"""TPL-001.F real browser proof. Run ONLY through the new native-cluster runner."""
import argparse
import json
import os
import re
from pathlib import Path
import secrets
import uuid
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
origin=os.environ['SAAS_TEST_ORIGIN'];url=urlsplit(origin)
if url.scheme!='http' or url.hostname!='127.0.0.1' or url.path or url.username or url.password:
    raise ValueError('Loopback origin required')
config=json.loads(Path(os.environ['SAAS_CONFIG_FILE']).read_text(encoding='utf-8'))
if config['database_mode']!='native' or not config['database']['name'].startswith('e04_') or os.environ.get('SAAS_MEDIA001_ISOLATED_MIGRATIONS')!='1':
    raise ValueError('Use the new isolated native-cluster runner only')
args.output.mkdir(exist_ok=True,parents=True)
results=[]
with sync_playwright() as engine:
    browser=engine.chromium.launch(executable_path=os.environ.get('SAAS_TEST_CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();errors=[];writes=[];reads=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:(writes if request.method=='PUT' else reads).append(request.url) if request.method in ('GET','PUT') and ('/design' in request.url or '/ready-portfolios/' in request.url) else None)
    def send(ctx,path,data=None,method='POST',tag=None,key=None):
        token=ctx.request.get(origin+'/api/v1/auth/csrf').json()['csrf_token']
        headers={'X-CSRFToken':token,'Origin':origin}
        if tag:headers['If-Match']=tag
        if key:headers['Idempotency-Key']=str(key)
        return ctx.request.fetch(origin+'/api/v1/'+path,method=method,data=data,headers=headers)
    def account(ctx):
        password=secrets.token_urlsafe(32);email='tpl-f-'+uuid.uuid4().hex[:10]+'@example.test'
        assert send(ctx,'auth/register',{'email':email,'first_name':'Profil','last_name':'Synthétique','password':password,'password_confirmation':password}).status==201
        assert send(ctx,'auth/login',{'email':email,'password':password}).status==200
    def nav(label):
        page.get_by_role('navigation',name='Espace portfolio',exact=True).get_by_role('link',name=label,exact=True).click()
        expect(page.get_by_role('navigation',name='Espace portfolio',exact=True).get_by_role('link',name=label,exact=True)).to_have_attribute('aria-current','page')
    account(context)
    page.goto(origin+'/dashboard');expect(page.get_by_role('heading',name='Votre prochain chapitre vous attend.')).to_be_visible()
    created=[]
    for template in ('minimal','editorial','creative-editorial'):
        if template=='creative-editorial':
            response=send(context,'ready-portfolios',{'name':'Recette '+template},key=uuid.uuid4())
            assert response.status==201
            item=response.json()['portfolio'];route='ready';endpoint='ready-portfolios/'+item['id']
        else:
            response=send(context,'portfolios/from-template',{'name':'Recette '+template,'template_id':template,'template_version':'1.0.0'},key=uuid.uuid4())
            assert response.status==201
            item=response.json();route='edit';endpoint='portfolios/'+item['id']+'/design'
        created.append(item)
        path='/portfolios/'+item['id'];editor=origin+path+'/'+route
        page.goto(origin+path);nav('Projets')
        page.wait_for_url(editor+'?panel=projects')
        if page.get_by_label('Titre du projet 1',exact=True).count()==0:
            page.get_by_role('button',name='Ajouter un projet',exact=True).click()
        count=page.get_by_label(re.compile(r'^Titre du projet [0-9]+$')).count()
        page.get_by_role('button',name='Ajouter un projet',exact=True).click()
        page.get_by_label(f'Titre du projet {count+1}',exact=True).fill('Projet temporaire synthétique')
        page.get_by_role('button',name=f'Retirer le projet {count+1}',exact=True).click()
        expect(page.get_by_label(f'Titre du projet {count+1}',exact=True)).to_have_count(0)
        expect(page.get_by_role('button',name='Monter',exact=True)).to_have_count(0)
        title='Projet conservé '+template
        page.get_by_label('Titre du projet 1',exact=True).fill(title)
        cover=None
        if template=='creative-editorial':
            token=context.request.get(origin+'/api/v1/auth/csrf').json()['csrf_token']
            source=Path(__file__).resolve().parents[2]/'docs/media001/evidence/couverture-synthetique.png'
            uploaded=context.request.post(origin+'/api/v1/media/assets',headers={'X-CSRFToken':token,'Origin':origin},multipart={'rights':'true','files':{'name':'navigation-couverture.png','mimeType':'image/png','buffer':source.read_bytes()}})
            assert uploaded.status==201
            cover=uploaded.json()['results'][0]
            page.get_by_role('button',name='Choisir dans ma bibliothèque — couverture 1',exact=True).click()
            page.get_by_role('dialog',name='Choisir une image pour couverture 1',exact=True).get_by_role('button',name='Choisir navigation-couverture.png',exact=True).click()
            page.get_by_label('Texte alternatif Couverture 1',exact=True).fill('Couverture synthétique conservée')
            crop=page.get_by_label('Cadrage Couverture 1 horizontal',exact=True)
            crop.focus();crop.press('ArrowRight');crop.press('ArrowRight')
            crop_value=crop.input_value()
        before_put=len(writes);before_get=len(reads)
        nav('Apparence')
        if template=='creative-editorial':
            page.get_by_label('Palette',exact=True).select_option('paper-cobalt')
            page.get_by_label('Couleur text',exact=True).fill('#F5F4EE')
            expect(page.get_by_role('button',name='Enregistrer',exact=True)).to_be_disabled()
            page.get_by_label('Couleur text',exact=True).fill('#102A43')
        else:
            expect(page.get_by_label('Palette',exact=True)).to_have_count(0)
            page.get_by_label('Espacement',exact=True).select_option('airy')
        nav('Sections')
        if template!='creative-editorial':
            expect(page.get_by_label('Afficher cette section',exact=False)).to_be_disabled()
            sections_nav=page.get_by_role('navigation',name='Sections du portfolio',exact=True)
            sections_nav.get_by_role('button',name='À propos',exact=True).click()
            toggle=page.get_by_label('Afficher cette section',exact=False)
            toggle.uncheck();toggle.check()
            move=page.get_by_role('button',name='Monter',exact=True)
            if not move.is_enabled():move=page.get_by_role('button',name='Descendre',exact=True)
            expect(move).to_be_enabled();move.click()
            sections_nav.get_by_role('button',name='Introduction',exact=True).click()
        else:
            expect(page.get_by_role('button',name='Monter',exact=True)).to_have_count(0)
        page.get_by_label('Titre principal',exact=True).fill('Hero conservé '+template)
        nav('Projets');expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        page.go_back();expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Hero conservé '+template)
        page.go_forward();expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        if cover:
            expect(page.get_by_label('Texte alternatif Couverture 1',exact=True)).to_have_value('Couverture synthétique conservée')
            expect(page.get_by_label('Cadrage Couverture 1 horizontal',exact=True)).to_have_value(crop_value)
        assert len(writes)==before_put,'Panel navigation must not PUT'
        assert len(reads)==before_get,'Panel navigation must not reload the snapshot'
        # Cancelling both an explicit exit and logout keeps the live draft.
        page.once('dialog',lambda dialog:dialog.dismiss());navlink=page.get_by_role('navigation',name='Espace portfolio').get_by_role('link',name='Vue d’ensemble',exact=True)
        navlink.click();expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        page.once('dialog',lambda dialog:dialog.dismiss());page.get_by_role('button',name='Se déconnecter',exact=True).click()
        expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        with page.expect_response(lambda response:response.request.method=='PUT' and response.url==origin+'/api/v1/'+endpoint) as saved:
            page.get_by_role('button',name='Enregistrer',exact=True).click()
        assert saved.value.status==200
        assert set(saved.value.request.post_data_json)=={'content','customization'}
        assert saved.value.request.headers.get('if-match')
        page.reload();expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        if cover:
            stored=context.request.get(origin+'/api/v1/'+endpoint).json()['snapshot']['content']['slots']['selected_projects']['items'][0]['cover']
            assert stored['asset_id']==cover['id'] and stored['alt']=='Couverture synthétique conservée'
            assert abs(stored['focal_point']['x']-float(crop_value))<.0001
            image=page.locator('[data-testid="ready-preview"]').get_by_role('img',name='Couverture synthétique conservée',exact=True)
            image.scroll_into_view_if_needed()
            page.wait_for_function('(src)=>Array.from(document.images).some(i=>i.getAttribute("src")===src&&i.complete&&i.naturalWidth>0)',arg=cover['file_url'])
        nav('Sections');expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Hero conservé '+template)
        nav('Apparence')
        if template=='creative-editorial':expect(page.get_by_label('Palette',exact=True)).to_have_value('paper-cobalt')
        else:expect(page.get_by_label('Espacement',exact=True)).to_have_value('airy')
        nav('Projets')
        for width,label in ((1440,'desktop'),(768,'tablet'),(390,'mobile'),(320,'small')):
            page.set_viewport_size({'width':width,'height':1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(template,width,'overflow')
            page.screenshot(path=str(args.output/f'{template}-{label}.png'),full_page=True)
        page.set_viewport_size({'width':1440,'height':1000})
        # Layout equivalent of 200% browser zoom on a 1440px display: CSS viewport
        # 720px, DPR 2. CSS zoom alone would not trigger media queries.
        zoom=context.browser.new_context(storage_state=context.storage_state(),viewport={'width':720,'height':500},device_scale_factor=2)
        zoom_page=zoom.new_page();zoom_page.goto(editor+'?panel=projects')
        expect(zoom_page.get_by_label('Titre du projet 1',exact=True)).to_have_value(title)
        assert zoom_page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
        zoom_page.screenshot(path=str(args.output/f'{template}-zoom200-equivalent.png'),full_page=True)
        zoom.close()
        # Keyboard activation and focus transfer; forced-colors/reduced-motion.
        page.emulate_media(forced_colors='active',reduced_motion='reduce')
        link=page.get_by_role('navigation',name='Espace portfolio').get_by_role('link',name='Apparence',exact=True)
        link.focus();link.press('Enter');expect(page.locator('[data-editor-panel-heading]:visible')).to_be_focused()
        page.screenshot(path=str(args.output/f'{template}-forced-colors.png'),full_page=True)
        page.emulate_media(forced_colors='none',reduced_motion='no-preference')
        # Real stale ETag: another request saves the server copy while draft stays dirty.
        nav('Projets');page.get_by_label('Titre du projet 1',exact=True).fill('Saisie locale après conflit')
        current=context.request.get(origin+'/api/v1/'+endpoint).json()
        assert send(context,endpoint,{k:current['snapshot'][k] for k in ('content','customization')},'PUT',current['etag']).status==200
        with page.expect_response(lambda r:r.request.method=='PUT' and r.url==origin+'/api/v1/'+endpoint) as conflict:
            page.get_by_role('button',name='Enregistrer',exact=True).click()
        assert conflict.value.status==412
        expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value('Saisie locale après conflit')
        nav('Sections');nav('Projets');expect(page.get_by_label('Titre du projet 1',exact=True)).to_have_value('Saisie locale après conflit')
        expect(page.get_by_role('button',name='Enregistrer',exact=True)).to_be_disabled()
        page.once('dialog',lambda d:d.accept());page.reload()
        # Archive via the real API: views remain available, all writes disabled.
        meta=context.request.get(origin+'/api/v1/portfolios/'+item['id']).json()
        assert send(context,'portfolios/'+item['id']+'/archive',{},tag=meta['etag']).status==200
        page.reload();nav('Projets');expect(page.get_by_role('button',name='Enregistrer',exact=True)).to_be_disabled()
        expect(page.get_by_label('Titre du projet 1',exact=True)).to_be_disabled()
        results.append({'template':template,'navigation_without_put_or_reload':True,'draft_history':True,'exit_guards':True,'project_add_remove':True,'template_section_restrictions':True,'save_reopen':True,'etag_conflict':True,'archive_read_only':True,'keyboard_focus':True,'widths':[1440,768,390,320]})
    for history_mode in ('native','fallback'):
        # Exercise both native Navigation API and the popstate fallback, with cancelled exit.
        fallback_item=send(context,'portfolios/from-template',{'name':'Navigation '+history_mode+' synthétique','template_id':'minimal','template_version':'1.0.0'},key=uuid.uuid4()).json()
        fallback=browser.new_context(storage_state=context.storage_state(),viewport={'width':1100,'height':900})
        if history_mode=='fallback':fallback.add_init_script("Object.defineProperty(window,'navigation',{value:undefined,configurable:true})")
        fp=fallback.new_page();fp.goto(origin+'/dashboard')
        card=fp.locator('article').filter(has=fp.get_by_role('heading',name='Navigation '+history_mode+' synthétique',exact=True))
        card.locator('a.open-link').click();expect(fp.get_by_label('Titre principal',exact=True)).to_be_visible()
        fnav=fp.get_by_role('navigation',name='Espace portfolio')
        # Panel changes while clean must not put a boundary between later edits.
        fnav.get_by_role('link',name='Apparence',exact=True).click()
        fnav.get_by_role('link',name='Sections',exact=True).click()
        fp.get_by_label('Titre principal',exact=True).fill('Brouillon historique conservé')
        fnav.get_by_role('link',name='Apparence',exact=True).click()
        fnav.get_by_role('link',name='Sections',exact=True).click()
        fp.go_back();expect(fnav.get_by_role('link',name='Apparence',exact=True)).to_have_attribute('aria-current','page')
        fp.go_back();expect(fp.get_by_label('Titre principal',exact=True)).to_have_value('Brouillon historique conservé')
        fp.go_back();expect(fnav.get_by_role('link',name='Apparence',exact=True)).to_have_attribute('aria-current','page')
        fp.go_back();expect(fp.get_by_label('Titre principal',exact=True)).to_have_value('Brouillon historique conservé')
        exit_dialogs=[]
        def stay(dialog):
            exit_dialogs.append(dialog.type);dialog.dismiss()
        fp.on('dialog',stay)
        try:
            with fp.expect_event('dialog',timeout=5000):
                fp.evaluate('history.back()')
            expect(fp.get_by_label('Titre principal',exact=True)).to_have_value('Brouillon historique conservé')
            expect(fp).to_have_url(origin+'/portfolios/'+fallback_item['id']+'/edit')
        except Exception:
            (args.output/('lifecycle-'+history_mode+'.json')).write_text(json.dumps({'url':fp.url,'events':fp.evaluate('window.__eventTrace'),'dialogs':exit_dialogs},ensure_ascii=False,indent=2),encoding='utf-8')
            raise
        assert exit_dialogs
        fp.wait_for_function("history.state?.portfolioEditor?.kind==='live'")
        fp.remove_listener('dialog',stay)
        def discard(dialog):dialog.accept()
        fp.on('dialog',discard)
        with fp.expect_event('dialog'):
            fp.evaluate('history.back()')
        expect(fp).to_have_url(origin+'/dashboard')
        server_copy=context.request.get(origin+'/api/v1/portfolios/'+fallback_item['id']+'/design').json()['snapshot']
        assert next(section for section in server_copy['content']['sections'] if section['type']=='hero')['data']['title']!='Brouillon historique conservé'
        fp.remove_listener('dialog',discard)
        fp.go_forward();expect(fp.get_by_label('Titre principal',exact=True)).to_be_visible()
        fp.get_by_label('Titre principal',exact=True).fill('Nouvelle saisie après retour')
        fp.on('dialog',stay)
        with fp.expect_event('dialog'):
            fp.evaluate('history.back()')
        expect(fp.get_by_label('Titre principal',exact=True)).to_have_value('Nouvelle saisie après retour')
        fp.wait_for_function("history.state?.portfolioEditor?.kind==='live'")
        fp.remove_listener('dialog',stay)
        fallback.close()
    # Blank portfolio: no invented editor or mutation path.
    blank=send(context,'portfolios',{'name':'Portfolio vierge synthétique'}).json()
    page.goto(origin+'/portfolios/'+blank['id'])
    expect(page.get_by_text('Aucun template associé.',exact=False)).to_be_visible()
    expect(page.get_by_role('navigation',name='Espace portfolio').get_by_role('link',name='Projets',exact=True)).to_have_count(0)
    # Unknown template version is a response fixture, never a database mutation.
    record=created[0];metadata=context.request.get(origin+'/api/v1/portfolios/'+record['id']).json()
    metadata['source_template_version']='9.0.0'
    pattern='**/api/v1/portfolios/'+record['id']
    page.route(pattern,lambda route:route.fulfill(status=200,json=metadata))
    page.goto(origin+'/portfolios/'+record['id']);expect(page.get_by_text('Cette version ne dispose pas',exact=False)).to_be_visible()
    expect(page.get_by_role('navigation',name='Espace portfolio').get_by_role('link',name='Projets',exact=True)).to_have_count(0)
    page.unroute(pattern)
    # Simulate the real schema negotiation error without activating v2 flags.
    design_pattern='**/api/v1/portfolios/'+record['id']+'/design'
    page.route(design_pattern,lambda route:route.fulfill(status=406,json={'error':{'code':'design_schema_not_acceptable','message':'Ce client ne prend pas en charge la version du design.'}}))
    page.goto(origin+'/portfolios/'+record['id']+'/edit');expect(page.get_by_role('alert').filter(has_text='version du design')).to_be_visible()
    page.unroute(design_pattern)
    page.route(design_pattern,lambda route:route.fulfill(status=503,json={'error':{'message':'Indisponible'}}))
    page.goto(origin+'/portfolios/'+record['id'])
    expect(page.get_by_role('button',name='Réessayer l’éditeur',exact=True)).to_be_visible()
    page.unroute(design_pattern)
    page.get_by_role('button',name='Réessayer l’éditeur',exact=True).click()
    expect(page.get_by_role('navigation',name='Espace portfolio').get_by_role('link',name='Projets',exact=True)).to_be_visible()
    # Deleted and foreign portfolios: actual server refusals, not client fixtures.
    assert send(context,'portfolios/'+blank['id'],{'confirm':True},'DELETE',blank['etag']).status==204
    page.goto(origin+'/portfolios/'+blank['id']);expect(page.get_by_role('alert').filter(has_text='introuvable')).to_be_visible()
    foreign=browser.new_context();account(foreign)
    other=foreign.new_page();other.goto(origin+'/portfolios/'+created[0]['id']+'/edit')
    expect(other.get_by_role('alert').filter(has_text='introuvable')).to_be_visible()
    assert foreign.request.get(origin+'/api/v1/portfolios/'+created[0]['id']).status==404
    foreign.close()
    # Revoked session uses the existing AUTH redirects (elapsed expiry tested by Django).
    assert send(context,'auth/logout',{}).status==200
    page.goto(origin+'/dashboard');expect(page).to_have_url(origin+'/login')
    assert not errors,errors
    (args.output/'navigation-results.json').write_text(json.dumps({'groups':results,'forward_return_reprotects_draft':True,'history_exit_accepted_no_autosave':True,'native_history_exit_guard':True,'history_without_navigation_api':True,'zoom_equivalent_css720_dpr2':True,'blank':True,'unknown_version_fixture':True,'v2_406_fixture':True,'capability_probe_503_retry_fixture':True,'media_reference_alt_crop_persisted':True,'deleted_actual':True,'foreign_actual':True,'revoked_session':True,'page_errors':errors,'windows_native_executed':os.name=='nt'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    context.close();browser.close()
