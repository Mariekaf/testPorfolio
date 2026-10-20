"""MEDIA-001, synthetic data only, runs through the new-cluster runner."""
import copy
from io import BytesIO,StringIO
import os
from pathlib import Path
import secrets
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from datetime import timedelta
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import close_old_connections,transaction,IntegrityError,DatabaseError
from django.test import TestCase,TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from modules.accounts.services import ensure_personal_account
from modules.media.models import Asset
from modules.media.processing import process_image,MAX_FILE,MAX_BODY
from modules.media.services import import_images,delete_asset,tag,purge_asset,resolve
from modules.media.storage import PrivateLocalStorage
from modules.portfolios.services import PortfolioProblem
from modules.templates.models import ReadyDesignRevision
from tests.test_ready_instances import ReadyMixin,BASE
from tests.media_fixtures import image_upload

URL='/api/v1/media/assets'

class MediaMixin(ReadyMixin):
    def setUp(self):
        super().setUp()
        self.folder=tempfile.TemporaryDirectory(prefix='media_test_',dir=os.environ['SAAS_MEDIA_ROOT'])
        self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        (self.root/'.portfolio-media-v1').write_bytes(b'portfolio-media-v1\n')
        self.env=patch.dict(os.environ,{'SAAS_MEDIA_ROOT':str(self.root)})
        self.env.start();self.addCleanup(self.env.stop)

    def upload(self,files=None,rights='true',client=None):
        client=client or self.client
        token=client.get('/api/v1/auth/csrf').json()['csrf_token']
        return client.post(URL,{'files':files if files is not None else [image_upload(size=(120,160))],'rights':rights},format='multipart',HTTP_X_CSRFTOKEN=token)

    def asset(self):
        result=self.upload();self.assertEqual(result.status_code,201,result.data);return result.json()['results'][0]

    def bind(self,record,asset):
        data=self.content(record);data['content']['slots']['hero_portrait']['value']={'asset_id':asset['id'],'alt':'Portrait synthétique','decorative':False,'focal_point':{'x':.3,'y':.6}}
        return self.send(BASE+'/'+record['portfolio']['id'],data,'put',tag=record['etag'])

class MediaTests(MediaMixin,TestCase):
    def test_openapi_real_metadata_errors_and_resolution(self):
        import json
        from jsonschema import Draft202012Validator,FormatChecker
        from referencing import Registry,Resource
        from referencing.jsonschema import DRAFT202012
        root=Path(__file__).resolve().parents[2]/'contracts';spec=root/'api/media.v1.json'
        def retrieve(uri):
            path=Path.from_uri(uri).resolve();self.assertTrue(path.is_relative_to(root))
            return Resource.from_contents(json.loads(path.read_text(encoding='utf-8')),default_specification=DRAFT202012)
        def verify(result,route,method):
            pointer=route.replace('~','~0').replace('/','~1')
            schema={'$ref':spec.as_uri()+f'#/paths/{pointer}/{method}/responses/{result.status_code}/content/application~1json/schema'}
            Draft202012Validator(schema,registry=Registry(retrieve=retrieve),format_checker=FormatChecker()).validate(result.json())
            self.assertIn('no-store',result['Cache-Control'])
        uploaded=self.upload();verify(uploaded,URL,'post');item=uploaded.json()['results'][0]
        verify(self.client.get(URL),URL,'get');verify(self.client.get(URL+'/'+item['id']),URL+'/{id}','get')
        verify(self.send(URL+'/'+item['id'],{'confirm':True},'delete'),URL+'/{id}','delete')
        r=self.create();data=self.content(r)
        data['content']['slots']['hero_portrait']['value']={'asset_id':item['id'],'alt':'x','decorative':False,'focal_point':{'x':.5,'y':.5}}
        response=self.send(BASE+'/'+r['portfolio']['id']+'/media',{'content':data['content']})
        verify(response,BASE+'/{id}/media','post')
        self.assertEqual(response.json()['assets'][item['id']]['asset_id'],item['id'])

    def test_real_three_formats_reencoded_headers_and_private_metadata(self):
        uploads=[image_upload('photo.jpg','JPEG',size=(120,160)),image_upload(size=(120,160)),image_upload('figure.webp','WEBP',size=(120,160))]
        result=self.upload(uploads);self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(len(result.json()['results']),3)
        for item in result.json()['results']:
            self.assertNotIn('storage_key',item);self.assertNotIn(str(self.root),str(item));self.assertEqual(item['content_type'],'image/webp')
            for suffix in ('file','thumbnail'):
                response=self.client.get(URL+'/'+item['id']+'/'+suffix);self.assertEqual(response.status_code,200)
                raw=b''.join(response.streaming_content)
                with Image.open(BytesIO(raw)) as image:self.assertEqual(image.format,'WEBP');self.assertFalse(image.getexif())
                self.assertIn('private',response['Cache-Control']);self.assertIn('no-store',response['Cache-Control'])
                self.assertIn('Cookie',response['Vary']);self.assertEqual(response['X-Content-Type-Options'],'nosniff')
                self.assertEqual(response['Cross-Origin-Resource-Policy'],'same-origin')
                self.assertEqual(response['Content-Type'],'image/webp')
                self.assertNotIn(item['original_name'],response['Content-Disposition'])

    def test_exif_orientation_gps_comments_do_not_survive(self):
        exif=Image.Exif();exif[274]=6;exif[315]='Synthetic private author';exif[270]='Synthetic secret location'
        item=self.upload([image_upload('rotated.jpg','JPEG',size=(100,200),exif=exif)]).json()['results'][0]
        self.assertEqual((item['width'],item['height']),(200,100))
        raw=b''.join(self.client.get(item['file_url']).streaming_content)
        self.assertNotIn(b'Synthetic private',raw);self.assertNotIn(b'Synthetic secret',raw)
        with Image.open(BytesIO(raw)) as image:self.assertFalse(image.getexif());self.assertNotIn('icc_profile',image.info);self.assertNotIn('xmp',image.info)

    def test_alpha_and_thumbnail_dimensions_preserved(self):
        raw=BytesIO();image=Image.new('RGBA',(4000,2000),(60,100,80,0));image.save(raw,format='PNG')
        result=self.upload([SimpleUploadedFile('transparent.png',raw.getvalue(),'image/png')])
        self.assertEqual(result.status_code,201,result.data);item=result.json()['results'][0]
        self.assertEqual((item['width'],item['height']),(2560,1280))
        self.assertEqual((item['thumbnail_width'],item['thumbnail_height']),(400,200))
        with Image.open(BytesIO(b''.join(self.client.get(item['file_url']).streaming_content))) as normalized:
            self.assertEqual(normalized.getpixel((0,0))[3],0)

    def test_logo_and_cover_revisions_block_deletion(self):
        for role in ('brand_logo','selected_projects'):
            item=self.asset();r=self.create();data=self.content(r)
            reference={'asset_id':item['id'],'alt':'Synthétique','decorative':False,'focal_point':{'x':.5,'y':.5}}
            if role=='brand_logo':data['content']['slots'][role]['value']=reference
            else:data['content']['slots'][role]['items']=[{'id':str(uuid.uuid4()),'title':'Projet synthétique','summary':'','cover':reference,'target':None}]
            result=self.send(BASE+'/'+r['portfolio']['id'],data,'put',tag=r['etag']);self.assertEqual(result.status_code,200,result.data)
            self.assertEqual(self.send(URL+'/'+item['id'],{'confirm':True},'delete',tag=item['etag']).status_code,409)

    def test_private_storage_permissions_and_decode_capacity(self):
        marker=self.root/'.portfolio-media-v1';marker.unlink()
        try:
            with self.assertRaises(PortfolioProblem):PrivateLocalStorage()
        finally:marker.write_bytes(b'portfolio-media-v1\n')
        with patch.dict(os.environ,{'SAAS_MEDIA_ROOT':str(Path(__file__).resolve().parents[2])}):
            with self.assertRaises(PortfolioProblem):PrivateLocalStorage()
        if os.name!='nt':
            self.root.chmod(0o755)
            try:
                with self.assertRaises(PortfolioProblem):PrivateLocalStorage()
            finally:self.root.chmod(0o700)
        with patch('modules.media.services.DECODE_SLOTS.acquire',return_value=False):
            self.assertEqual(self.upload().status_code,503)
        self.assertFalse(Asset.objects.exists())

    def test_invalid_disguised_and_animated_files_atomic(self):
        vectors=[SimpleUploadedFile('x.svg',b'<svg onload="alert(1)"/>','image/svg+xml'),
            SimpleUploadedFile('x.png',b'<html>script</html>','image/png'),
            SimpleUploadedFile('x.exe',image_upload().read(),'image/png'),
            SimpleUploadedFile('x.png',b'\x89PNG\r\n\x1a\ncorrupt','image/png'),
            SimpleUploadedFile('x.png',image_upload().read(),'image/jpeg')]
        animated=BytesIO();Image.new('RGB',(16,16),'red').save(animated,format='WEBP',save_all=True,append_images=[Image.new('RGB',(16,16),'blue')],duration=10,loop=0)
        vectors.append(SimpleUploadedFile('animated.webp',animated.getvalue(),'image/webp'))
        for invalid in vectors:
            result=self.upload([image_upload(size=(120,160)),invalid]);self.assertEqual(result.status_code,400,result.data)
            self.assertFalse(Asset.objects.exists());self.assertEqual([p for p in self.root.iterdir() if p.is_dir()],[])

    def test_pixels_sides_and_decompression_bomb_refused(self):
        for size in [(8193,1),(5000,5000)]:
            result=self.upload([image_upload(size=size)]);self.assertEqual(result.status_code,400,result.data)
        # IHDR with a huge declared pixel count; no allocation/decompression is attempted.
        import struct,zlib
        raw=image_upload(size=(10,10)).read();header=struct.pack('>IIBBBBB',100000,100000,8,2,0,0,0)
        bomb=raw[:8]+struct.pack('>I',13)+b'IHDR'+header+struct.pack('>I',zlib.crc32(b'IHDR'+header))+raw[33:]
        self.assertEqual(self.upload([SimpleUploadedFile('bomb.png',bomb,'image/png')]).status_code,400)
        self.assertFalse(Asset.objects.exists())

    def test_file_count_body_size_and_other_api_limits(self):
        self.assertEqual(self.upload([image_upload(size=(16,16)) for _ in range(5)]).status_code,400)
        self.assertEqual(self.upload([SimpleUploadedFile('huge.png',b'x'*(MAX_FILE+1),'image/png')]).status_code,413)
        token=self.client.get('/api/v1/auth/csrf').json()['csrf_token']
        result=self.client.generic('POST',URL,b'x'*(MAX_BODY+1),content_type='multipart/form-data; boundary=x',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(result.status_code,413)
        self.assertFalse(Asset.objects.exists())
        result=self.client.post('/api/v1/auth/login',{'email':'x'*20000,'password':'x'},format='json',HTTP_X_CSRFTOKEN=token)
        self.assertIn(result.status_code,[400,413]);self.assertNotEqual(result.status_code,200)

    def test_csrf_anonymous_unknown_and_rights(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.get(URL).status_code,401)
        self.assertEqual(client.get(URL+'/'+str(uuid.uuid4())+'/file').status_code,401)
        self.assertEqual(self.client.post(URL,{'files':[image_upload()],'rights':'true'},format='multipart').status_code,403)
        self.assertEqual(self.upload(rights='false').status_code,400)
        self.assertEqual(self.client.get(URL+'/'+str(uuid.uuid4())).status_code,404)
        self.assertEqual(self.client.get(URL+'?page=../../').status_code,400)
        self.assertEqual(self.client.get(URL+'/../../.local').status_code,404)

    def test_other_account_cannot_get_list_resolve_save_delete(self):
        item=self.asset();record=self.create()
        other=get_user_model().objects.create_user(email='foreign-media@example.test',password=self.password);ensure_personal_account(other)
        client=APIClient(enforce_csrf_checks=True);self.send('/api/v1/auth/login',{'email':other.email,'password':self.password},client=client)
        self.assertEqual(client.get(URL).json()['count'],0)
        for suffix in ('','/file','/thumbnail'):self.assertEqual(client.get(URL+'/'+item['id']+suffix).status_code,404)
        self.assertEqual(self.send(URL+'/'+item['id'],{'confirm':True},'delete',tag=item['etag'],client=client).status_code,404)
        created=self.send(BASE,{'name':'Autre compte'},key=uuid.uuid4(),client=client).json()
        data=self.content(created);data['content']['slots']['hero_portrait']['value']={'asset_id':item['id'],'alt':'x','decorative':False,'focal_point':{'x':.5,'y':.5}}
        path=BASE+'/'+created['portfolio']['id']
        self.assertEqual(self.send(path,data,'put',tag=created['etag'],client=client).status_code,400)
        resolved=self.send(path+'/media',{'content':data['content']},client=client)
        self.assertEqual(resolved.json()['assets'][item['id']],{'state':'missing'})
        self.assertEqual(self.send(BASE+'/'+record['portfolio']['id']+'/media',{'content':record['snapshot']['content']},client=client).status_code,404)

    def test_missing_file_keeps_other_content_and_rejects_new_reference(self):
        item=self.asset();record=self.create();saved=self.bind(record,item);self.assertEqual(saved.status_code,200)
        asset=Asset.objects.get(pk=item['id']);(self.root/asset.storage_key/'full.webp').unlink()
        self.assertEqual(self.client.get(item['file_url']).status_code,404)
        r=saved.json();self.assertEqual(self.client.get(BASE+'/'+r['portfolio']['id']).json(),r)
        response=self.send(BASE+'/'+r['portfolio']['id']+'/media',{'content':r['snapshot']['content']})
        self.assertEqual(response.json()['assets'][item['id']]['state'],'missing')
        self.assertEqual(self.send(BASE+'/'+r['portfolio']['id'],self.content(r),'put',tag=r['etag']).status_code,400)
        data=self.content(r);data['content']['slots']['hero_portrait']['value']=None
        self.assertEqual(self.send(BASE+'/'+r['portfolio']['id'],data,'put',tag=r['etag']).status_code,200)

    def test_revisions_retain_used_file_after_slot_removed(self):
        item=self.asset();r=self.bind(self.create(),item).json();data=self.content(r);data['content']['slots']['hero_portrait']['value']=None
        removed=self.send(BASE+'/'+r['portfolio']['id'],data,'put',tag=r['etag']);self.assertEqual(removed.status_code,200)
        result=self.send(URL+'/'+item['id'],{'confirm':True},'delete',tag=item['etag']);self.assertEqual(result.status_code,409)
        self.assertEqual(result.json()['error']['code'],'asset_in_use')
        self.assertEqual(self.client.get(item['file_url']).status_code,200)
        self.assertEqual(ReadyDesignRevision.objects.count(),3)

    def test_delete_preconditions_retention_dry_run_and_purge(self):
        item=self.asset();asset=Asset.objects.get(pk=item['id']);key=asset.storage_key
        self.assertEqual(self.send(URL+'/'+item['id'],{'confirm':True},'delete').status_code,428)
        self.assertEqual(self.send(URL+'/'+item['id'],{'confirm':True},'delete',tag='stale').status_code,412)
        self.assertEqual(self.send(URL+'/'+item['id'],{'confirm':True},'delete',tag=item['etag']).status_code,204)
        self.assertTrue((self.root/key/'full.webp').exists());self.assertEqual(self.client.get(item['file_url']).status_code,404)
        self.assertFalse(purge_asset(item['id'],execute=True))
        Asset.objects.filter(pk=item['id']).update(deleted_at=timezone.now()-timedelta(days=8))
        out=StringIO();call_command('purge_assets',stdout=out);self.assertIn('Dry run',out.getvalue());self.assertTrue((self.root/key).exists())
        call_command('purge_assets',execute=True,stdout=StringIO());self.assertFalse((self.root/key).exists())
        asset.refresh_from_db();self.assertEqual(asset.status,'purged');self.assertIsNone(asset.storage_key);self.assertEqual(asset.original_name,'')

    def test_quota_and_disk_failure_cleanup_are_atomic(self):
        with patch('modules.media.services.MAX_ASSETS',1):
            self.asset();self.assertEqual(self.upload().status_code,409)
        count=Asset.objects.count();paths=set(self.root.iterdir())
        with patch('modules.media.storage.os.fsync',side_effect=OSError('synthetic disk failure')):
            self.assertEqual(self.upload().status_code,503)
        self.assertEqual(Asset.objects.count(),count);self.assertEqual(set(self.root.iterdir()),paths)
        with patch('modules.media.services.MAX_ACCOUNT_BYTES',1):self.assertEqual(self.upload().status_code,409)
        original=Asset.objects.create
        with patch.object(Asset.objects,'create',side_effect=RuntimeError('synthetic DB rollback')):
            with self.assertRaises(RuntimeError):import_images(self.user,[image_upload(size=(32,32))])
        self.assertEqual(set(self.root.iterdir()),paths)

    def test_uncertain_database_commit_preserves_bytes_for_reconciliation(self):
        original=Asset.objects.filter
        def filter_rows(*args,**kwargs):
            if set(kwargs)=={'storage_key'}:raise DatabaseError('synthetic verification outage')
            return original(*args,**kwargs)
        with patch.object(Asset.objects,'create',side_effect=RuntimeError('synthetic interrupted insert')):
            with patch.object(Asset.objects,'filter',side_effect=filter_rows):
                with self.assertRaises(RuntimeError):import_images(self.user,[image_upload(size=(32,32))])
        self.assertFalse(Asset.objects.exists())
        directories=[p for p in self.root.iterdir() if p.is_dir()]
        self.assertEqual(len(directories),1)
        self.assertTrue((directories[0]/'full.webp').exists())
        os.utime(directories[0],(0,0));call_command('reconcile_media',execute=True,stdout=StringIO())
        self.assertFalse(directories[0].exists())

    def test_path_and_hash_tampering_never_serve_arbitrary_binary(self):
        item=self.asset();asset=Asset.objects.get(pk=item['id'])
        with self.assertRaises(OSError):PrivateLocalStorage().open('../outside','full','x',1)
        (self.root/asset.storage_key/'full.webp').write_bytes(b'<script>bad</script>')
        self.assertEqual(self.client.get(item['file_url']).status_code,404)
        self.assertEqual(Asset.objects.get(pk=item['id']).status,'ready')
        if hasattr(os,'symlink'):
            target=self.root/'target';target.write_bytes(b'synthetic')
            path=self.root/asset.storage_key/'full.webp';path.unlink()
            try:path.symlink_to(target)
            except OSError:return  # Separate named symlink test below records an actual skip.
            self.assertEqual(self.client.get(item['file_url']).status_code,404)

    def test_symlink_storage_is_refused(self):
        target=self.root/'target';target.mkdir();path=self.root/'link'
        try:path.symlink_to(target,target_is_directory=True)
        except OSError:self.skipTest('Symlink creation unavailable in this environment.')
        with patch.dict(os.environ,{'SAAS_MEDIA_ROOT':str(path)}):
            with self.assertRaises(PortfolioProblem):PrivateLocalStorage()

    def test_library_pagination_and_no_metadata_leak(self):
        for i in range(13):import_images(self.user,[image_upload(f'synthetic-{i}.png',size=(24,24))])
        first=self.client.get(URL).json();second=self.client.get(URL+'?page=2').json()
        self.assertEqual((first['count'],len(first['results']),len(second['results'])),(13,12,1))
        self.assertFalse({a['id'] for a in first['results']}&{a['id'] for a in second['results']})
        text=str(first);self.assertNotIn('storage_key',text);self.assertNotIn('digest',text);self.assertNotIn(str(self.root),text)

    def test_orphan_reconciliation_safe_and_explicit(self):
        storage=PrivateLocalStorage();key=secrets.token_hex(32);storage.write(key,b'x',b'y');path=self.root/key
        os.utime(path,(0,0));out=StringIO();call_command('reconcile_media',stdout=out)
        self.assertIn('Dry run',out.getvalue());self.assertTrue(path.exists())
        call_command('reconcile_media',execute=True,stdout=StringIO());self.assertFalse(path.exists())
        self.assertTrue(self.root.exists())

    def test_migration_guard_existing_database_refused(self):
        import importlib
        from types import SimpleNamespace
        guard=importlib.import_module('modules.media.migrations.0001_initial').isolated_only
        with patch.dict(os.environ,{'SAAS_MEDIA001_ISOLATED_MIGRATIONS':'1'}):
            with self.assertRaises(RuntimeError):guard(None,SimpleNamespace(connection=SimpleNamespace(settings_dict={'NAME':'portfolio_real'})))

class MediaConcurrencyTests(MediaMixin,TransactionTestCase):
    def test_concurrent_quota_one_success_and_parallel_downloads(self):
        from threading import Barrier
        barrier=Barrier(2)
        def upload(index):
            close_old_connections()
            try:
                user=get_user_model().objects.get(pk=self.user.pk);barrier.wait(timeout=10)
                try:return str(import_images(user,[image_upload(f'parallel-{index}.png',size=(32,32))])[0].pk)
                except PortfolioProblem as e:return e.code
            finally:close_old_connections()
        with patch('modules.media.services.MAX_ASSETS',1):
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(upload,[1,2]))
        self.assertEqual(results.count('quota_exceeded'),1);self.assertEqual(Asset.objects.count(),1)
        asset=Asset.objects.get();cookies=copy.copy(self.client.cookies)
        def download(_):
            close_old_connections()
            try:
                client=APIClient();client.cookies=copy.copy(cookies)
                response=client.get(f'{URL}/{asset.pk}/file');data=b''.join(response.streaming_content)
                return response.status_code,data
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=4) as pool:reads=list(pool.map(download,range(8)))
        self.assertTrue(all(status==200 for status,_ in reads));self.assertTrue(all(raw==reads[0][1] for _,raw in reads))
