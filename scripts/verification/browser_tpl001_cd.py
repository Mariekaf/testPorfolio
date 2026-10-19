"""C+D verification, not phase E. No credentials/cookies are written to evidence."""
import argparse,json,re,secrets
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
parser=argparse.ArgumentParser(description='C+D full browser proof; synthetic database ONLY. Creates synthetic users and portfolios.')
parser.add_argument('--origin',required=True);parser.add_argument('--evidence',type=Path,required=True)
parser.add_argument('--chromium',required=True);parser.add_argument('--disposable-database',action='store_true',required=True)
args=parser.parse_args();origin=args.origin.rstrip('/');url=urlsplit(origin)
if url.scheme!='http' or url.hostname not in ['localhost','127.0.0.1'] or url.username or url.password or url.path or url.query or url.fragment:raise ValueError('Local disposable instance required.')
out=args.evidence;out.mkdir(parents=True,exist_ok=True);(out/'browser-results.json').unlink(missing_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
 email='cd-'+secrets.token_hex(5)+'@example.test';password=secrets.token_urlsafe(24)
 def post(path,data,method='POST',tag=None):
  token=context.request.get(origin+'/api/v1/auth/csrf').json()['csrf_token'];headers={'X-CSRFToken':token,'Origin':origin}
  if tag:headers['If-Match']=tag
  return context.request.fetch(origin+path,method=method,data=data,headers=headers)
 assert post('/api/v1/auth/register',{'email':email,'first_name':'Profil','last_name':'Synthétique','password':password,'password_confirmation':password}).status==201
 assert post('/api/v1/auth/login',{'email':email,'password':password}).status==200
 page=context.new_page();creation_requests=[];page.on('request',lambda request:creation_requests.append(request.url) if request.method=='POST' and request.url.endswith('/api/v1/portfolios/from-template') else None);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));results=[]
 for template in ['minimal','editorial']:
  page.goto(origin+'/templates');page.get_by_role('heading',name='Deux regards sur votre travail.').wait_for()
  if template=='minimal':page.screenshot(path=str(out/'library-desktop.png'),full_page=True)
  card=page.locator('article').filter(has=page.get_by_role('heading',name=template.title(),exact=True)).first
  card.get_by_role('link',name='Utiliser ce template',exact=True).click()
  page.get_by_label('Nom du portfolio',exact=True).fill('Atelier '+template.title())
  before=len(creation_requests)
  page.get_by_role('button',name='Créer et personnaliser').dblclick()
  page.wait_for_url(re.compile(r'/portfolios/[0-9a-f-]+/edit$'));item_id=page.url.split('/')[-2]
  assert len(creation_requests)==before+1
  page.get_by_label('Titre principal',exact=True).fill('Mon regard '+template)
  page.once('dialog',lambda d:d.dismiss());page.get_by_role('link',name='← Vue d’ensemble',exact=True).click()
  assert page.url.endswith('/edit')
  page.once('dialog',lambda d:d.dismiss());page.evaluate('history.back()')
  page.wait_for_timeout(250)
  assert page.url.endswith('/edit')
  page.get_by_label('Sous-titre',exact=True).fill('Recherche, design et expériences utiles.')
  page.get_by_label('Libellé du CTA',exact=True).fill('Voir les projets')
  page.get_by_role('button',name='Compétences',exact=True).click();page.get_by_role('button',name='Ajouter une compétence',exact=True).click()
  page.get_by_label('Compétence 1',exact=True).fill('Recherche UX')
  page.get_by_role('button',name='Contact',exact=True).click()
  page.get_by_label('Titre du contact',exact=True).fill('Échangeons ensemble')
  page.get_by_label('Texte du contact',exact=True).fill('Une idée à explorer ?')
  page.get_by_label('Adresse e-mail de contact',exact=True).fill('contact@example.test')
  page.get_by_role('button',name='Projets',exact=True).click();page.get_by_role('button',name='Ajouter un projet',exact=True).click()
  page.get_by_label('Titre du projet 1',exact=True).fill('Étude de cas personnelle')
  page.get_by_label('Résumé du projet 1',exact=True).fill('Des entretiens au prototype testé.')
  page.get_by_label('Lien du projet 1',exact=True).fill('http://example.test/case')
  page.get_by_role('button',name='Enregistrer',exact=True).click();page.get_by_role('alert').filter(has_text='Vérifiez').wait_for()
  page.get_by_label('Lien du projet 1',exact=True).fill('https://example.test/case')
  page.get_by_role('button',name='Descendre' if template=='minimal' else 'Monter',exact=True).click()
  page.get_by_label('Espacement',exact=True).select_option('airy')
  page.get_by_role('button',name='À propos',exact=True).click()
  page.get_by_label('Titre de présentation',exact=True).fill('Ma démarche')
  page.get_by_label('Description de présentation',exact=True).fill('Écouter, prototyper et tester.')
  page.get_by_label('Afficher cette section',exact=True).uncheck()
  page.get_by_role('button',name='Enregistrer',exact=True).click();page.get_by_role('status').filter(has_text='Modifications enregistrées').wait_for()
  page.reload();page.get_by_label('Titre principal',exact=True).wait_for();assert page.get_by_label('Titre principal',exact=True).input_value()=='Mon regard '+template
  assert page.get_by_test_id('instance-preview').locator('[data-section="about"]').count()==0
  assert page.get_by_test_id('instance-preview').get_by_text('Étude de cas personnelle',exact=True).count()>=1
  current=context.request.get(origin+f'/api/v1/portfolios/{item_id}/design').json()
  assert next(s for s in current['snapshot']['content']['sections'] if s['type']=='contact')['data']['email']=='contact@example.test'
  assert next(s for s in current['snapshot']['content']['sections'] if s['type']=='skills')['data']['items']==['Recherche UX']
  assert current['snapshot']['customization']['section_order'][1]=='about'
  page.get_by_label('Titre principal',exact=True).fill('Brouillon en conflit '+template)
  remote=current['snapshot'];remote['content']['sections'][0]['data']['subtitle']='Version distante'
  assert post(f'/api/v1/portfolios/{item_id}/design',{k:remote[k] for k in ['content','customization']},'PUT',current['etag']).status==200
  page.get_by_role('button',name='Enregistrer',exact=True).click();page.get_by_role('alert').filter(has_text='Ce portfolio a changé').wait_for()
  assert page.get_by_label('Titre principal',exact=True).input_value()=='Brouillon en conflit '+template
  page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Recharger la version enregistrée',exact=True).click()
  page.get_by_label('Titre principal',exact=True).wait_for();assert page.get_by_label('Titre principal',exact=True).input_value()=='Mon regard '+template
  page.screenshot(path=str(out/f'editor-{template}-desktop.png'),full_page=True)
  page.set_viewport_size({'width':900,'height':1000});assert page.locator('body').evaluate('(el)=>el.scrollWidth<=window.innerWidth')
  page.screenshot(path=str(out/f'editor-{template}-tablet.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='Mobile',exact=True).click()
  assert page.locator('body').evaluate('(el)=>el.scrollWidth<=window.innerWidth')
  page.screenshot(path=str(out/f'editor-{template}-mobile.png'),full_page=True)
  page.set_viewport_size({'width':1440,'height':1000})
  page.get_by_role('button',name='Activer le mode sombre',exact=True).click();page.screenshot(path=str(out/f'editor-{template}-dark.png'),full_page=True)
  page.get_by_role('button',name='Activer le mode clair',exact=True).click()
  # The normal dashboard keeps all PORT actions, and duplicate copies its design.
  item=context.request.get(origin+f'/api/v1/portfolios/{item_id}').json()
  duplicate=post(f'/api/v1/portfolios/{item_id}/duplicate',{},tag=item['etag']);assert duplicate.status==201
  dup=duplicate.json();dd=context.request.get(origin+f"/api/v1/portfolios/{dup['id']}/design").json()
  dd['snapshot']['content']['sections'][0]['data']['title']='Copie indépendante'
  assert post(f"/api/v1/portfolios/{dup['id']}/design",{k:dd['snapshot'][k] for k in ['content','customization']},'PUT',dd['etag']).status==200
  assert context.request.get(origin+f'/api/v1/portfolios/{item_id}/design').json()['snapshot']['content']['sections'][0]['data']['title']=='Mon regard '+template
  archive=post(f'/api/v1/portfolios/{item_id}/archive',{},tag=item['etag']).json();assert archive['management_state']=='archived'
  restored=post(f'/api/v1/portfolios/{item_id}/restore',{},tag=archive['etag']).json();assert restored['management_state']=='active'
  assert post('/api/v1/auth/logout',{}).status==200
  assert post('/api/v1/auth/login',{'email':email,'password':password}).status==200
  page.goto(origin+f'/portfolios/{item_id}/edit');page.get_by_label('Titre principal',exact=True).wait_for()
  assert page.get_by_label('Titre principal',exact=True).input_value()=='Mon regard '+template
  results.append({'template':template,'double_click_single_request':True,'unsaved_link_and_back_guard':True,'created_saved_reloaded':True,'reconnected':True,'validation_400':True,'conflict_412_keeps_local':True,'duplicate_independent':True,'archive_restore':True,'mobile_no_overflow':True})
 assert not errors,errors
 page.goto(origin+'/dashboard');page.get_by_role('heading',name=re.compile('Mes portfolios')).wait_for();page.screenshot(path=str(out/'dashboard-templates.png'),full_page=True)
 (out/'browser-results.json').write_text(json.dumps({'platform':'Linux Chromium','results':results,'page_errors':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('PASS: create, personalize, save, reload and reconnect from both templates; conflicts, duplication and responsive checked.')
 browser.close()
