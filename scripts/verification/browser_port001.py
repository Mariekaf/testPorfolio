"""PORT-001 browser proof. Existing Playwright/Chromium required.
ONLY point at a disposable database; creates synthetic accounts and portfolios.
No credentials, cookies, reset links, API payloads or private configs printed.
"""
import argparse,json,re,secrets,platform
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect


def post(context,origin,path,data,method='POST',tag=None):
    csrf=context.request.get(origin+'/api/v1/auth/csrf').json()['csrf_token']
    headers={'X-CSRFToken':csrf}
    if tag:headers['If-Match']=tag
    return context.request.fetch(origin+path,method=method,data=data,headers=headers)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',required=True)
    parser.add_argument('--chromium',required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--disposable-database',action='store_true',required=True)
    args=parser.parse_args();origin=args.origin.rstrip('/')
    if urlsplit(origin).hostname not in ('localhost','127.0.0.1'):raise ValueError('Only local disposable instances permitted.')
    args.evidence.mkdir(parents=True,exist_ok=True);(args.evidence/'browser-results.json').unlink(missing_ok=True);proof=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        try:
            for width,height in [(1365,960),(390,844)]:
                context=browser.new_context(viewport={'width':width,'height':height},color_scheme='light',reduced_motion='reduce')
                page=context.new_page();errors=[]
                page.on('pageerror',lambda error:errors.append(type(error).__name__))
                page.goto(origin+'/dashboard');page.wait_for_url('**/login')
                email='synthetic-'+secrets.token_hex(5)+'@example.test';password=secrets.token_urlsafe(24)
                page.goto(origin+'/register')
                for label,value in [('Prénom','Synthetic'),('Nom','Designer'),('Adresse e-mail',email),('Mot de passe',password),('Confirmer le mot de passe',password)]:page.get_by_label(label,exact=True).fill(value)
                page.get_by_role('button',name='Créer mon compte').click();page.wait_for_url('**/login?reason=registered')
                page.get_by_label('Adresse e-mail',exact=True).fill(email);page.get_by_label('Mot de passe',exact=True).fill(password)
                page.get_by_role('button',name='Se connecter',exact=True).click();page.wait_for_url('**/dashboard')
                page.get_by_role('heading',name='Mes portfolios.').wait_for()
                page.get_by_role('heading',name='Votre prochain chapitre vous attend.').wait_for()
                page.screenshot(path=str(args.evidence/f'empty-{width}.png'),full_page=True)
                page.get_by_role('link',name='Créer un portfolio',exact=True).click()
                page.get_by_text('Utiliser un template',exact=True).wait_for()
                assert page.locator('.starting-option.unavailable').get_attribute('aria-disabled')=='true'
                page.get_by_role('button',name=re.compile('Portfolio vierge')).click()
                page.get_by_label('Nom du portfolio',exact=True).fill('Atelier UX')
                page.get_by_label('Description (facultative)',exact=True).fill('Recherche, conception et expériences numériques.')
                assert page.get_by_label('Identifiant du portfolio',exact=True).input_value()=='atelier-ux'
                page.get_by_role('button',name='Créer mon portfolio',exact=True).click()
                page.wait_for_url(re.compile(r'/portfolios/[0-9a-f-]+$'))
                primary_id=page.url.rsplit('/',1)[1]
                page.get_by_role('heading',name='Atelier UX',exact=True).wait_for()
                assert page.get_by_role('button',name=re.compile('Publication')).is_disabled()
                page.get_by_role('link',name='Paramètres',exact=True).click()
                page.get_by_label('Nom du portfolio',exact=True).fill('Atelier UX Études')
                page.get_by_label('Identifiant du portfolio',exact=True).fill('atelier-etudes')
                current=context.request.get(origin+'/api/v1/portfolios/'+primary_id).json()
                response=post(context,origin,'/api/v1/portfolios/'+primary_id,{'description':'Version concurrente synthétique'},'PATCH',current['etag'])
                assert response.status==200
                page.get_by_role('button',name='Enregistrer les modifications').click()
                page.get_by_role('alert').filter(has_text='Ce portfolio a changé').wait_for()
                page.get_by_role('button',name='Recharger la version actuelle').click()
                page.get_by_label('Description (facultative)',exact=True).fill('Études de cas et recherche UX.')
                page.get_by_label('Nom du portfolio',exact=True).fill('Atelier UX Études')
                page.get_by_label('Identifiant du portfolio',exact=True).fill('atelier-etudes')
                page.get_by_role('button',name='Enregistrer les modifications').click()
                page.get_by_role('status').filter(has_text='Modifications enregistrées').wait_for()
                saved=context.request.get(origin+'/api/v1/portfolios/'+primary_id).json()
                assert saved['id']==primary_id and saved['slug']=='atelier-etudes'
                # Explicit collision is surfaced at the corresponding input.
                page.goto(origin+'/portfolios/new');page.get_by_role('button',name=re.compile('Portfolio vierge')).click()
                page.get_by_label('Nom du portfolio',exact=True).fill('Autre intention')
                page.get_by_label('Identifiant du portfolio',exact=True).fill('atelier-etudes')
                page.get_by_role('button',name='Créer mon portfolio',exact=True).click()
                page.locator('#slug-error').filter(has_text='Choisissez un autre slug').wait_for()
                page.goto(origin+'/portfolios/'+primary_id)
                page.get_by_role('heading',name='Atelier UX Études',exact=True).wait_for()
                page.locator('.action-menu summary').click();page.get_by_role('button',name='Dupliquer',exact=True).click()
                page.wait_for_url(lambda url:bool(re.search(r'/portfolios/[0-9a-f-]+$',url)) and not url.endswith(primary_id))
                duplicate_id=page.url.rsplit('/',1)[1]
                page.get_by_role('heading',name='Atelier UX Études (copie)',exact=True).wait_for()
                page.locator('.action-menu summary').click();page.get_by_role('button',name='Archiver',exact=True).click()
                page.get_by_text('Ce portfolio est archivé.',exact=False).wait_for()
                page.goto(origin+'/dashboard');page.get_by_role('button',name=re.compile('^Archives')).click()
                card=page.locator('.portfolio-card').filter(has_text='Atelier UX Études (copie)');card.wait_for()
                card.get_by_role('link',name=re.compile('^Ouvrir ')).last.click()
                page.get_by_role('button',name='Restaurer le portfolio',exact=True).click()
                page.get_by_role('status').filter(has_text='Portfolio restauré').wait_for()
                page.locator('.action-menu summary').click();page.get_by_role('button',name='Supprimer',exact=True).click()
                dialog=page.get_by_role('dialog');dialog.wait_for()
                assert page.get_by_role('button',name='Annuler',exact=True).evaluate('(el)=>el===document.activeElement')
                page.keyboard.press('Shift+Tab');assert dialog.evaluate('(el)=>el.contains(document.activeElement)')
                page.keyboard.press('Escape');dialog.wait_for(state='hidden')
                assert context.request.get(origin+'/api/v1/portfolios/'+duplicate_id).status==200
                page.get_by_role('button',name='Supprimer',exact=True).click()
                page.get_by_role('button',name='Confirmer la suppression',exact=True).click()
                page.wait_for_url('**/dashboard')
                page.get_by_role('heading',name='Mes portfolios.').wait_for()
                assert context.request.get(origin+'/api/v1/portfolios/'+duplicate_id).status==404
                # Real synthetic rows for pagination: no fake counters or seeded UI statistics.
                for index in range(12):
                    r=post(context,origin,'/api/v1/portfolios',{'name':['Recherche produit','Interfaces et identités','Explorations visuelles'][index%3]+' '+str(index+1),'description':'Portfolio synthétique pour la vérification.'})
                    assert r.status==201
                page.reload();page.get_by_role('button',name='Suivant',exact=True).wait_for()
                expect(page.locator('.portfolio-card')).to_have_count(12)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(args.evidence/f'dashboard-light-{width}.png'),full_page=True)
                page.get_by_role('button',name='Suivant',exact=True).click()
                page.get_by_text('Page 2 sur 2',exact=True).wait_for();expect(page.locator('.portfolio-card')).to_have_count(1)
                page.get_by_role('button',name='Précédent',exact=True).click();page.get_by_text('Page 1 sur 2',exact=True).wait_for()
                page.get_by_role('button',name='Activer le mode sombre').click()
                assert page.evaluate('document.documentElement.dataset.studioTheme')=='dark'
                page.screenshot(path=str(args.evidence/f'dashboard-dark-{width}.png'),full_page=True)
                assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
                page.goto(origin+'/portfolios/'+primary_id)
                page.get_by_role('heading',name='Atelier UX Études',exact=True).wait_for()
                assert page.evaluate('document.documentElement.dataset.studioTheme')=='dark'
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(args.evidence/f'workspace-dark-{width}.png'),full_page=True)
                page.goto(origin+'/dashboard')
                page.route('**/api/v1/portfolios?*',lambda route:route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':{'message':'Erreur réseau synthétique.'}})))
                page.reload();page.get_by_role('alert').filter(has_text='Erreur réseau synthétique').wait_for()
                page.unroute('**/api/v1/portfolios?*');page.get_by_role('button',name='Recharger la version actuelle').click()
                page.locator('.portfolio-card').first.wait_for()
                other=browser.new_context();other_password=secrets.token_urlsafe(24);other_email='other-'+secrets.token_hex(5)+'@example.test'
                assert post(other,origin,'/api/v1/auth/register',{'email':other_email,'first_name':'Other','last_name':'Synthetic','password':other_password,'password_confirmation':other_password}).status==201
                assert post(other,origin,'/api/v1/auth/login',{'email':other_email,'password':other_password}).status==200
                assert other.request.get(origin+'/api/v1/portfolios/'+primary_id).status==404
                outsider=other.new_page();outsider.goto(origin+'/portfolios/'+primary_id)
                outsider.get_by_role('alert').filter(has_text='Portfolio introuvable').wait_for()
                assert 'Atelier UX Études' not in outsider.locator('body').inner_text()
                assert not errors,'Unexpected browser application error.'
                other.close();context.close()
                proof.append({'width':width,'height':height,'result':'passed','checks':['empty','blank creation','template unavailable','edit','slug collision','version conflict','duplicate','archive','restore','delete confirmation keyboard/escape','pagination','network error/retry','owner isolation','dark theme persistence','reduced motion','no horizontal overflow']})
                print(f'PASS PORT-001 {width}px: full management, concurrency conflict, owner isolation, pagination, keyboard dialog, dark mode and responsive checks.')
        finally:browser.close()
    (args.evidence/'browser-results.json').write_text(json.dumps({'synthetic_data_only':True,'platform':platform.system()+' Chromium','scenarios':proof},indent=2)+'\n')

if __name__=='__main__':main()
