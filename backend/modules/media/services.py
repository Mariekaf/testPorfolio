import copy
from datetime import timedelta
import secrets
from threading import BoundedSemaphore
from django.db import transaction,connection,DatabaseError
from django.db.models import Q,Sum
from django.utils import timezone
from modules.accounts.models import Account
from modules.accounts.services import authorized_accounts,ensure_personal_account
from modules.portfolios.services import PortfolioProblem
from modules.templates.models import ReadyPortfolioDesign,ReadyDesignRevision
from .models import Asset
from .processing import process_image,MAX_FILES
from .storage import get_storage

MAX_ASSETS=200
MAX_ACCOUNT_BYTES=200*1024*1024
RETENTION_DAYS=7
DECODE_SLOTS=BoundedSemaphore(2)

def tag(asset):return f'"asset:{asset.pk}:{asset.version}"'

def metadata(asset):
    return {key:str(getattr(asset,key)) if key=='id' else getattr(asset,key) for key in
        ('id','original_name','content_type','width','height','thumbnail_width','thumbnail_height','size','thumbnail_size','status','version')} | {
        'created_at':asset.created_at.isoformat(),'etag':tag(asset),
        'thumbnail_url':f'/api/v1/media/assets/{asset.pk}/thumbnail',
        'file_url':f'/api/v1/media/assets/{asset.pk}/file'}


def references(document):
    slots=document['content']['slots'];result=[]
    for name in ('brand_logo','hero_portrait'):
        if slots[name]['value'] is not None:result.append(slots[name]['value'])
    result.extend(p['cover'] for p in slots['selected_projects']['items'] if p['cover'] is not None)
    return result


def files_ready(asset,storage=None):
    if asset.status!='ready' or not asset.rights_confirmed:return False
    try:
        storage=storage or get_storage()
        for variant,digest,size in [('full',asset.digest,asset.size),('thumbnail',asset.thumbnail_digest,asset.thumbnail_size)]:
            with storage.open(asset.storage_key,variant,digest,size):pass
        return True
    except OSError:return False


def resolve(account_id,document):
    ids={r['asset_id'] for r in references(document)}
    assets={str(a.pk):a for a in Asset.objects.filter(account_id=account_id,id__in=ids,status='ready')}
    result={}
    for identity in sorted(ids):
        asset=assets.get(identity)
        if asset and files_ready(asset):
            result[identity]={'state':'ready','asset_id':identity,'width':asset.width,'height':asset.height,
                'src':f'/api/v1/media/assets/{identity}/file'}
        else:result[identity]={'state':'missing'}
    return result


def validate_references(account_id,document):
    # Same Account lock as deletion and upload: deletion cannot win after validation.
    Account.objects.select_for_update().get(pk=account_id)
    facts=resolve(account_id,document)
    if any(value['state']!='ready' for value in facts.values()):
        raise PortfolioProblem('media_unavailable','Une image est indisponible ou non autorisée. Choisissez une image de votre bibliothèque ou retirez la référence.',400)


def is_used(asset):
    identity=str(asset.pk)
    query=(Q(document__content__slots__brand_logo__value__asset_id=identity) |
        Q(document__content__slots__hero_portrait__value__asset_id=identity) |
        Q(document__content__slots__selected_projects__items__contains=[{'cover':{'asset_id':identity}}]))
    return (ReadyPortfolioDesign.objects.filter(portfolio__account_id=asset.account_id).filter(query).exists() or
        ReadyDesignRevision.objects.filter(design__portfolio__account_id=asset.account_id).filter(query).exists())


def import_images(user,uploads):
    if not 1<=len(uploads)<=MAX_FILES:
        raise PortfolioProblem('too_many_files','Sélectionnez de 1 à 4 images.',400)
    if not DECODE_SLOTS.acquire(blocking=False):
        raise PortfolioProblem('media_busy','Deux imports sont déjà en préparation. Réessayez dans un instant.',503)
    try:processed=[process_image(upload) for upload in uploads]
    finally:DECODE_SLOTS.release()
    storage=get_storage();keys=[]
    try:
        with transaction.atomic():
            account=ensure_personal_account(user)
            existing=Asset.objects.filter(account=account).exclude(status='purged')
            used=existing.aggregate(full=Sum('size'),thumb=Sum('thumbnail_size'))
            total=(used['full'] or 0)+(used['thumb'] or 0)+sum(p['size']+p['thumbnail_size'] for p in processed)
            if existing.count()+len(processed)>MAX_ASSETS or total>MAX_ACCOUNT_BYTES:
                raise PortfolioProblem('quota_exceeded','Votre bibliothèque est limitée à 200 images et 200 Mio. Les fichiers supprimés en rétention restent comptabilisés.',409)
            result=[]
            for image in processed:
                key=secrets.token_hex(32)
                with connection.cursor() as cursor:cursor.execute('SELECT pg_advisory_xact_lock(%s,%s)',[17001,int(key[:8],16)&0x7fffffff])
                storage.write(key,image['full'],image['thumbnail']);keys.append(key)
                fields={k:v for k,v in image.items() if k not in ('full','thumbnail')}
                result.append(Asset.objects.create(account=account,storage_key=key,rights_confirmed=True,**fields))
        return result
    except BaseException:
        for key in keys:
            # A lost COMMIT acknowledgement is ambiguous: never remove bytes for
            # a potentially committed row. Reconciliation can safely decide later.
            try:
                if Asset.objects.filter(storage_key=key).exists():continue
            except DatabaseError:continue
            try:storage.delete(key)
            except OSError:pass  # Explicit orphan reconciliation handles interrupted cleanup.
        raise


def delete_asset(user,asset_id,if_match):
    with transaction.atomic():
        asset=Asset.objects.filter(pk=asset_id,account_id__in=authorized_accounts(user).values('id'),status='ready').first()
        if not asset:raise PortfolioProblem('not_found','Image introuvable.',404)
        Account.objects.select_for_update().get(pk=asset.account_id)
        asset=Asset.objects.select_for_update().get(pk=asset.pk)
        if asset.status!='ready':raise PortfolioProblem('not_found','Image introuvable.',404)
        if if_match is None:raise PortfolioProblem('precondition_required','Actualisez la bibliothèque avant suppression.',428)
        if if_match!=tag(asset):raise PortfolioProblem('version_conflict','Cette image a changé. Actualisez la bibliothèque.',412)
        if is_used(asset):
            raise PortfolioProblem('asset_in_use','Cette image est utilisée par un portfolio ou une révision et ne peut pas être supprimée.',409)
        asset.status='deleted';asset.deleted_at=timezone.now();asset.version+=1
        asset.save(update_fields=['status','deleted_at','version'])


def purge_asset(asset_id,execute=False):
    with transaction.atomic():
        asset=Asset.objects.get(pk=asset_id)
        Account.objects.select_for_update().get(pk=asset.account_id)
        asset=Asset.objects.select_for_update().get(pk=asset_id)
        if asset.status!='deleted' or asset.deleted_at>timezone.now()-timedelta(days=RETENTION_DAYS) or is_used(asset):return False
        if execute:
            get_storage().delete(asset.storage_key)
            asset.status='purged';asset.purged_at=timezone.now();asset.storage_key=None
            asset.original_name='';asset.width=asset.height=asset.thumbnail_width=asset.thumbnail_height=0
            asset.size=asset.thumbnail_size=0;asset.digest=asset.thumbnail_digest='';asset.version+=1
            asset.save()
        return True
