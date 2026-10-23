"""Synthetic full Studio journey, called only by the verified disposable runner."""
import argparse
import json
import os
from pathlib import Path
import secrets
import time
import urllib.request
import uuid
from playwright.sync_api import sync_playwright, expect


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if os.environ.get('SAAS_E0704_ISOLATED_MIGRATIONS')!='1':
        raise RuntimeError('Use run_e0704_isolated.py --browser; existing environments are forbidden.')
    # Inherited config is owned by the new-cluster runner, not a default local config.
    config=Path(os.environ['SAAS_CONFIG_FILE'])
    if not config.parent.name.startswith('tpl001_e0704_'):
        raise RuntimeError('Unexpected synthetic configuration.')
    origin=os.environ['SAAS_TEST_ORIGIN']
    for _ in range(120):
        try:
            with urllib.request.urlopen(origin+'/login',timeout=2) as result:
                if result.status==200:break
        except Exception:time.sleep(.5)
    else:raise RuntimeError('Studio did not become ready.')
    email='synthetic-'+uuid.uuid4().hex[:8]+'@example.test';password=secrets.token_urlsafe(32)
    results=[];errors=[]
    with sync_playwright() as p:
        executable=os.environ.get('SAAS_TEST_CHROMIUM') or ('/usr/bin/chromium' if os.name!='nt' else None)
        browser=p.chromium.launch(executable_path=executable,headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(origin+'/portfolios/ready');expect(page).to_have_url(origin+'/login')
        results.append('anonymous private route redirects')
        page.goto(origin+'/register');page.get_by_label('Prénom',exact=True).fill('Synthétique');page.get_by_label('Nom',exact=True).fill('Recette')
        page.get_by_label('Adresse e-mail',exact=True).fill(email);page.get_by_label('Mot de passe',exact=True).fill(password);page.get_by_label('Confirmer le mot de passe',exact=True).fill(password)
        page.get_by_role('button',name='Créer mon compte',exact=True).click();page.wait_for_url('**/login?reason=registered')
        page.get_by_label('Adresse e-mail',exact=True).fill(email);page.get_by_label('Mot de passe',exact=True).fill(password);page.get_by_role('button',name='Se connecter',exact=True).click();page.wait_for_url('**/dashboard')
        page.get_by_role('link',name='Choisir Creative Editorial').click();expect(page.get_by_role('button',name='Créer mon portfolio privé')).to_be_visible()
        page.screenshot(path=str(args.output/'selection-desktop.png'),full_page=True)
        page.get_by_label('Nom du portfolio',exact=True).fill('Portfolio synthétique E0704');page.get_by_role('button',name='Créer mon portfolio privé').click();page.wait_for_url('**/portfolios/*/ready')
        url=page.url;expect(page.get_by_role('heading',name='Portfolio synthétique E0704',exact=True)).to_be_visible()
        results.append('real registration login private selection creation')
        def open_section(name):
            details=page.locator('details').filter(has=page.locator('summary',has_text=name)).first
            details.evaluate('e=>e.open=true')
        open_section('Identité et navigation');page.get_by_label('Nom affiché',exact=True).fill('Camille — démonstration synthétique')
        page.get_by_label('Titre principal',exact=True).fill('Concevoir des expériences utiles.')
        page.get_by_label('Sous-titre',exact=True).fill('Portfolio UX/UI de recette : aucun contenu réel.')
        open_section('Présentation');page.get_by_label('Titre de présentation',exact=True).fill('Une approche attentive')
        page.get_by_role('button',name='Ajouter un paragraphe',exact=True).click();page.get_by_label('Texte paragraphe 1 fragment 1',exact=True).fill('Recherche, prototypes et interfaces accessibles. Texte synthétique.')
        page.get_by_label('Gras',exact=True).check()
        open_section('Projets');page.get_by_label('Titre des projets',exact=True).fill('Projets de démonstration')
        page.get_by_role('button',name='Ajouter un projet',exact=True).click();page.get_by_label('Titre du projet 1',exact=True).fill('Projet de test indépendant')
        page.get_by_label('Résumé du projet 1',exact=True).fill('Une étude fictive pour vérifier la sauvegarde et la reprise.')
        page.get_by_label('Type Projet 1',exact=True).select_option('external');page.get_by_label('URL HTTPS Projet 1',exact=True).fill('https://example.invalid/project')
        open_section('Contact');page.get_by_label('Titre du contact',exact=True).fill('Discutons de votre projet')
        page.get_by_label('Type Lien de contact',exact=True).select_option('email');page.get_by_label('Adresse e-mail Lien de contact',exact=True).fill('contact@example.test')
        page.get_by_role('button',name='Ajouter un réseau',exact=True).click();page.get_by_label('Libellé réseau 1',exact=True).fill('Mon laboratoire');page.get_by_label('URL HTTPS réseau 1',exact=True).fill('https://example.invalid/lab')
        open_section('Pied de page');page.get_by_label('Note de pied de page',exact=True).fill('Recette synthétique · non publié')
        open_section('Apparence autorisée');page.get_by_label('Palette',exact=True).select_option('paper-cobalt');page.get_by_label('Police',exact=True).select_option('system-serif')
        open_section('Identité et navigation')
        page.get_by_role('button',name='Référencer logo',exact=True).click()
        page.get_by_label('UUID Logo',exact=True).fill(str(uuid.uuid4()))
        page.get_by_label('Texte alternatif Logo',exact=True).fill('Logo synthétique non résolu')
        page.get_by_label('Libellé Bouton du Hero',exact=True).fill('Découvrir mes travaux')
        page.get_by_label('Type Bouton du Hero',exact=True).select_option('section')
        page.get_by_label('Section Bouton du Hero',exact=True).select_option('projects')
        preview=page.get_by_test_id('ready-preview');expect(preview.get_by_role('heading',name='Concevoir des expériences utiles.',exact=True)).to_be_visible()
        expect(preview.get_by_text('Camille — démonstration synthétique',exact=True)).to_be_visible()
        # No real media service: persist reference without granting access or loading image.
        open_section('Hero');page.get_by_role('button',name='Référencer portrait',exact=True).click()
        page.get_by_label('UUID Portrait',exact=True).fill(str(uuid.uuid4()));page.get_by_label('Texte alternatif Portrait',exact=True).fill('Référence synthétique non résolue')
        expect(preview.locator('img')).to_have_count(0)
        results.append('structured text rich project link social media style editing and real renderer')
        print('Structured editing completed.',flush=True)
        # Validation errors preserve values and prevent save.
        page.get_by_label('Couleur text',exact=True).fill('#FFFFFF')
        expect(page.get_by_role('button',name='Enregistrer',exact=True)).to_be_disabled()
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir des expériences utiles.')
        page.get_by_role('button',name='Réinitialiser l’apparence',exact=True).click()
        page.get_by_label('Palette',exact=True).select_option('paper-cobalt');page.get_by_label('Police',exact=True).select_option('system-serif')
        # Intentional network failure must preserve draft and allow retry.
        page.route('**/api/v1/ready-portfolios/*',lambda route:route.abort() if route.request.method=='PUT' else route.continue_())
        page.get_by_role('button',name='Enregistrer',exact=True).click()
        expect(page.locator('[role=alert]').filter(has_text='Connexion impossible.')).to_have_count(1)
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir des expériences utiles.')
        page.unroute('**/api/v1/ready-portfolios/*')
        page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_role('status')).to_contain_text('Modifications enregistrées')
        results.append('validation and network failure retain input retry saves')
        print('Validation and network retry completed.',flush=True)
        # Leave and resume through real dashboard/overview routing.
        page.get_by_role('link',name='← Mes portfolios',exact=True).click();page.wait_for_url('**/dashboard')
        page.get_by_role('link',name='Portfolio synthétique E0704',exact=True).click();page.wait_for_url(url.removesuffix('/ready'))
        page.get_by_role('link',name='Modifier le portfolio',exact=True).click();page.wait_for_url(url)
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir des expériences utiles.')
        expect(preview.get_by_text('Projet de test indépendant',exact=True)).to_be_visible()
        results.append('save leave dashboard overview resume persisted content')
        print('Leave and resume completed.',flush=True)
        # Independent editor same ETag -> one save, one explicit conflict, no overwrite.
        second=context.new_page();second.goto(url);expect(second.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir des expériences utiles.')
        page.get_by_label('Titre principal',exact=True).fill('Brouillon local conservé')
        second.get_by_label('Titre principal',exact=True).fill('Version concurrente enregistrée');second.get_by_role('button',name='Enregistrer',exact=True).click();expect(second.get_by_role('status')).to_contain_text('Modifications enregistrées')
        page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_role('alert').filter(has_text='Ce portfolio a changé.')).to_be_visible()
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Brouillon local conservé')
        page.once('dialog',lambda d:d.dismiss());page.get_by_role('link',name='← Mes portfolios',exact=True).click();expect(page).to_have_url(url)
        page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Recharger le brouillon enregistré',exact=True).click()
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Version concurrente enregistrée');second.close()
        results.append('concurrent ETag conflict and unsaved navigation guard explicit reload')
        print('Concurrency and navigation completed.',flush=True)
        # Real Studio and portfolio captures in desktop and mobile, no second renderer.
        page.locator('details').evaluate_all("es=>es.forEach(e=>e.open=e.querySelector('summary').textContent==='Hero')")
        for width,label in [(1440,'desktop'),(375,'mobile')]:
            page.set_viewport_size({'width':width,'height':1000})
            page.get_by_role('button',name='Mobile' if width==375 else 'Desktop',exact=True).click()
            expect(preview.get_by_role('heading',name='Version concurrente enregistrée',exact=True)).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'Studio overflow'
            assert preview.evaluate('e=>e.scrollWidth<=e.clientWidth+1'),'Preview overflow'
            page.screenshot(path=str(args.output/f'studio-{label}.png'),full_page=True)
            preview.screenshot(path=str(args.output/f'portfolio-{label}.png'))
        results.append('desktop mobile Studio and actual portfolio screenshots no overflow')
        page.get_by_role('button',name='Se déconnecter',exact=True).click();page.wait_for_url('**/login')
        page.goto(url);expect(page).to_have_url(origin+'/login')
        results.append('logout private route closed')
        assert not errors,errors
        (args.output/'browser-results.json').write_text(json.dumps({'checks':results,'page_errors':errors,'screenshots':5,'synthetic_only':True,'windows_executed':False,'screen_reader_executed':False},indent=2)+'\n',encoding='utf-8')
        browser.close()
    print('E0704 synthetic authenticated browser journey passed; 5 screenshots, no existing DB.')

if __name__=='__main__':main()
