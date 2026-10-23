"""Full private media journey, only against the verified temporary MEDIA001 environment."""
from io import BytesIO
import argparse
import json
import os
from pathlib import Path
import secrets
import time
import urllib.request
import uuid
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright,expect


def create_fixtures(directory):
    portrait=Image.new('RGB',(900,1125),'#d6e99c');draw=ImageDraw.Draw(portrait)
    draw.rounded_rectangle((120,600,800,1300),radius=220,fill='#275247')
    draw.ellipse((230,170,690,730),fill='#dfb797');draw.pieslice((200,90,720,670),180,360,fill='#162d29')
    draw.ellipse((340,400,365,425),fill='#162d29');draw.ellipse((540,400,565,425),fill='#162d29')
    draw.arc((340,450,560,610),10,170,fill='#6f4638',width=10)
    portrait.save(directory/'portrait-synthetique.png')
    cover=Image.new('RGB',(1200,800),'#efc9a9');draw=ImageDraw.Draw(cover)
    draw.rounded_rectangle((90,80,1110,720),radius=25,fill='#253e39')
    draw.rectangle((130,130,1070,220),fill='#f7f4eb');draw.rectangle((130,260,730,660),fill='#d6e99c')
    draw.ellipse((250,310,620,610),fill='#547d6a');draw.rectangle((770,260,1070,450),fill='#dbad8c');draw.rectangle((770,490,1070,660),fill='#f7f4eb')
    cover.save(directory/'couverture-synthetique.png')
    logo=Image.new('RGBA',(128,128),(0,0,0,0));draw=ImageDraw.Draw(logo)
    draw.ellipse((8,8,120,120),fill='#275247');draw.rectangle((42,28,86,100),fill='#d6e99c')
    logo.save(directory/'logo-synthetique.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if os.environ.get('SAAS_MEDIA001_ISOLATED_MIGRATIONS')!='1' or not Path(os.environ['SAAS_CONFIG_FILE']).parent.name.startswith('media001_'):
        raise RuntimeError('Verified MEDIA001 disposable runner required.')
    origin=os.environ['SAAS_TEST_ORIGIN'];create_fixtures(args.output)
    for _ in range(100):
        try:
            with urllib.request.urlopen(origin+'/login',timeout=2) as response:
                if response.status==200:break
        except OSError:time.sleep(.3)
    else:raise RuntimeError('Synthetic Studio unavailable.')
    checks=[];errors=[]
    with sync_playwright() as p:
        executable=os.environ.get('SAAS_TEST_CHROMIUM') or ('/usr/bin/chromium' if os.name!='nt' else None)
        browser=p.chromium.launch(executable_path=executable,headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        def register_login(page,email,password):
            page.goto(origin+'/register');page.get_by_label('Prénom',exact=True).fill('Recette');page.get_by_label('Nom',exact=True).fill('Synthétique')
            page.get_by_label('Adresse e-mail',exact=True).fill(email);page.get_by_label('Mot de passe',exact=True).fill(password);page.get_by_label('Confirmer le mot de passe',exact=True).fill(password)
            page.get_by_role('button',name='Créer mon compte',exact=True).click();page.wait_for_url('**/login?reason=registered')
            login(page,email,password)
        def login(page,email,password):
            page.goto(origin+'/login');page.get_by_label('Adresse e-mail',exact=True).fill(email);page.get_by_label('Mot de passe',exact=True).fill(password)
            page.get_by_role('button',name='Se connecter',exact=True).click();page.wait_for_url('**/dashboard')
        email='media-'+uuid.uuid4().hex[:10]+'@example.test';password=secrets.token_urlsafe(32)
        page.goto(origin+'/portfolios/media');expect(page).to_have_url(origin+'/login')
        register_login(page,email,password)
        page.get_by_role('link',name='Choisir Creative Editorial',exact=True).click();page.get_by_label('Nom du portfolio',exact=True).fill('Portfolio média synthétique')
        page.get_by_role('button',name='Créer mon portfolio privé',exact=True).click();page.wait_for_url('**/portfolios/*/ready');url=page.url
        expect(page.get_by_label('Titre principal',exact=True)).to_be_visible();page.get_by_label('Titre principal',exact=True).fill('Concevoir avec attention.')
        page.get_by_label('Sous-titre',exact=True).fill('Contenus et illustrations synthétiques pour la recette MEDIA-001.')
        def section(name):page.locator('details').filter(has=page.locator('summary',has_text=name)).first.evaluate('e=>e.open=true')
        section('Identité et navigation');page.get_by_label('Nom affiché',exact=True).fill('Noa · démonstration synthétique')
        page.get_by_role('button',name='Choisir dans ma bibliothèque — portrait',exact=True).click()
        dialog=page.get_by_role('dialog',name='Choisir une image pour portrait',exact=True)
        expect(dialog.get_by_text('Aucune image pour le moment.',exact=False)).to_be_visible()
        dialog.get_by_label('Images à importer',exact=True).set_input_files([str(args.output/f) for f in ('portrait-synthetique.png','couverture-synthetique.png','logo-synthetique.png')])
        dialog.get_by_label('Je dispose des droits nécessaires pour utiliser ces images.',exact=True).check()
        dialog.get_by_role('button',name='Importer une image',exact=True).click()
        expect(dialog.get_by_role('button',name='Choisir portrait-synthetique.png',exact=True)).to_be_visible()
        for width,label in [(1440,'desktop'),(375,'mobile')]:
            page.set_viewport_size({'width':width,'height':1000})
            expect(dialog.locator('img')).to_have_count(3)
            for img in dialog.locator('img').all():expect(img).to_be_visible();assert img.evaluate('e=>e.complete&&e.naturalWidth>0')
            dialog.screenshot(path=str(args.output/f'library-{label}.png'))
        page.set_viewport_size({'width':1440,'height':1000})
        dialog.get_by_role('button',name='Choisir portrait-synthetique.png',exact=True).click()
        page.get_by_label('Texte alternatif Portrait',exact=True).fill('Portrait illustré synthétique, fond vert')
        crop=page.get_by_label('Cadrage Portrait horizontal',exact=True);crop.focus();crop.press('End');crop.press('ArrowLeft')
        page.get_by_label('Cadrage Portrait vertical',exact=True).focus();page.get_by_label('Cadrage Portrait vertical',exact=True).press('Home');page.get_by_label('Cadrage Portrait vertical',exact=True).press('ArrowRight')
        page.get_by_role('button',name='Choisir dans ma bibliothèque — logo',exact=True).click()
        page.get_by_role('dialog').get_by_role('button',name='Choisir logo-synthetique.png',exact=True).click()
        section('Présentation');page.get_by_label('Titre de présentation',exact=True).fill('Du sens dans les détails')
        page.get_by_role('button',name='Ajouter un paragraphe',exact=True).click();page.get_by_label('Texte paragraphe 1 fragment 1',exact=True).fill('Recherche, exploration et interfaces utiles. Texte fictif de recette.')
        section('Projets');page.get_by_label('Titre des projets',exact=True).fill('Une exploration visuelle')
        page.get_by_role('button',name='Ajouter un projet',exact=True).click();page.get_by_label('Titre du projet 1',exact=True).fill('Projet synthétique / interface')
        page.get_by_label('Résumé du projet 1',exact=True).fill('Une couverture importée depuis la bibliothèque privée.')
        page.get_by_role('button',name='Choisir dans ma bibliothèque — couverture 1',exact=True).click()
        page.get_by_role('dialog').get_by_role('button',name='Choisir couverture-synthetique.png',exact=True).click()
        page.get_by_label('Texte alternatif Couverture 1',exact=True).fill('Interface géométrique synthétique')
        section('Contact');page.get_by_label('Titre du contact',exact=True).fill('Échangeons des idées')
        page.get_by_label('Type Lien de contact',exact=True).select_option('email');page.get_by_label('Adresse e-mail Lien de contact',exact=True).fill('synthetic@example.test')
        preview=page.get_by_test_id('ready-preview')
        def images_loaded():
            expect(preview.locator('img')).to_have_count(3)
            for image in preview.locator('img').all():image.scroll_into_view_if_needed()
            for _ in range(100):
                if preview.locator('img').evaluate_all('es=>es.every(e=>e.complete&&e.naturalWidth>0)'):return
                page.wait_for_timeout(50)
            raise AssertionError('Actual private images did not load.')
        images_loaded();portrait=preview.get_by_alt_text('Portrait illustré synthétique, fond vert',exact=True)
        expect(portrait).to_have_css('object-position','99% 1%')
        assert '/api/v1/media/assets/' in portrait.get_attribute('src')
        portrait_url=portrait.get_attribute('src');assert page.get_by_label('UUID Portrait',exact=True).count()==0
        page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_role('status').filter(has_text='Modifications enregistrées')).to_be_visible()
        checks.append('private import three real images, selection in all three slots, real pixels, alt/crop, save')
        print('Import, association and rendering passed.',flush=True)
        # Leave, logout, login, reopen: persisted refs and binaries survive all steps.
        page.get_by_role('link',name='← Mes portfolios',exact=True).click();page.wait_for_url('**/dashboard')
        page.get_by_role('button',name='Se déconnecter',exact=True).click();page.wait_for_url('**/login')
        unauthorized=context.request.get(origin+portrait_url);assert unauthorized.status==401
        login(page,email,password);page.goto(url);expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir avec attention.')
        images_loaded();expect(preview.get_by_alt_text('Portrait illustré synthétique, fond vert',exact=True)).to_have_css('object-position','99% 1%')
        checks.append('leave logout login reopen private binaries and crop persist; anonymous binary denied')
        page.route('**'+portrait_url,lambda route:route.fulfill(status=404,body=''))
        page.reload();expect(preview.get_by_role('img',name='Image indisponible',exact=True)).to_be_visible()
        expect(page.get_by_label('Titre principal',exact=True)).to_have_value('Concevoir avec attention.')
        page.unroute('**'+portrait_url);page.reload();images_loaded()
        checks.append('binary failure placeholder preserves content and recovers after reopen')
        # Capture the actual renderer within the Studio, never a replacement image/layout.
        page.locator('details').evaluate_all("es=>es.forEach(e=>e.open=e.querySelector('summary').textContent==='Hero')")
        for width,label in [(1440,'desktop'),(375,'mobile')]:
            page.set_viewport_size({'width':width,'height':1000});page.get_by_role('button',name='Mobile' if width==375 else 'Desktop',exact=True).click()
            images_loaded();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(args.output/f'editor-{label}.png'),full_page=True)
            preview.screenshot(path=str(args.output/f'portfolio-{label}.png'))
        page.set_viewport_size({'width':1440,'height':1000})
        # Errors are readable and modal focus/escape are native + explicit.
        page.get_by_role('button',name='Remplacer portrait',exact=True).click();dialog=page.get_by_role('dialog')
        dialog.get_by_label('Images à importer',exact=True).set_input_files({'name':'invalid.svg','mimeType':'image/svg+xml','buffer':b'<svg><script>bad</script></svg>'})
        dialog.get_by_label('Je dispose des droits nécessaires pour utiliser ces images.',exact=True).check();dialog.get_by_role('button',name='Importer une image',exact=True).click()
        expect(dialog.get_by_role('alert')).to_contain_text('Image refusée')
        dialog.screenshot(path=str(args.output/'library-error.png'))
        page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
        expect(page.get_by_role('button',name='Remplacer portrait',exact=True)).to_be_focused()
        # Remove then replace a reference; other slots remain intact, revisions retain file.
        page.get_by_role('button',name='Retirer portrait',exact=True).click();expect(preview.locator('img')).to_have_count(2)
        expect(preview.get_by_text('Projet synthétique / interface',exact=True)).to_be_visible()
        page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_role('status').filter(has_text='Modifications enregistrées')).to_be_visible()
        page.get_by_role('button',name='Choisir dans ma bibliothèque — portrait',exact=True).click();dialog=page.get_by_role('dialog')
        page.once('dialog',lambda d:d.accept());dialog.get_by_role('button',name='Supprimer portrait-synthetique.png',exact=True).click()
        expect(dialog.get_by_role('alert')).to_contain_text('révision')
        dialog.get_by_role('button',name='Choisir portrait-synthetique.png',exact=True).click();images_loaded()
        page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_role('status').filter(has_text='Modifications enregistrées')).to_be_visible()
        checks.append('invalid SVG rejected, keyboard modal escape focus, remove/replace preserves other slots, revision deletion refused')
        # >10 Mio multipart through the real Next rewrite, no global API limit relaxation.
        page.get_by_role('button',name='Remplacer portrait',exact=True).click();dialog=page.get_by_role('dialog')
        encoded=BytesIO();Image.new('RGB',(120,160),'#275247').save(encoded,format='JPEG')
        padded=encoded.getvalue()+b'\x00'*(6*1024*1024-len(encoded.getvalue()))
        dialog.get_by_label('Images à importer',exact=True).set_input_files([
            {'name':'grand-synthetique-1.jpg','mimeType':'image/jpeg','buffer':padded},
            {'name':'grand-synthetique-2.jpg','mimeType':'image/jpeg','buffer':padded}])
        dialog.get_by_label('Je dispose des droits nécessaires pour utiliser ces images.',exact=True).check()
        dialog.get_by_role('button',name='Importer une image',exact=True).click()
        expect(dialog.get_by_role('button',name='Choisir grand-synthetique-1.jpg',exact=True)).to_be_visible()
        page.once('dialog',lambda d:d.accept());dialog.get_by_role('button',name='Supprimer grand-synthetique-1.jpg',exact=True).click()
        expect(dialog.get_by_role('button',name='Choisir grand-synthetique-1.jpg',exact=True)).to_have_count(0)
        dialog.get_by_role('button',name='Fermer la bibliothèque',exact=True).click();images_loaded()
        checks.append('12 Mio real proxied multipart import succeeds and unused asset deletion follows retention policy')
        # Other account cannot read binary nor metadata, despite knowing exact UUID.
        foreign=browser.new_context();other=foreign.new_page();register_login(other,'foreign-'+uuid.uuid4().hex[:10]+'@example.test',secrets.token_urlsafe(32))
        assert foreign.request.get(origin+portrait_url).status==404
        assert foreign.request.get(origin+portrait_url.removesuffix('/file')).status==404
        assert foreign.request.get(origin+'/api/v1/media/assets').json()['count']==0
        foreign.close();checks.append('authenticated second tenant cannot read known asset or metadata or list it')
        assert not errors,errors
        (args.output/'browser-results.json').write_text(json.dumps({'checks':checks,'screenshots':7,'page_errors':errors,'synthetic_only':True,'windows_executed':False,'screen_reader_executed':False},indent=2)+'\n',encoding='utf-8')
        browser.close()
    print('MEDIA001 full private authenticated journey passed; 7 screenshots.',flush=True)

if __name__=='__main__':main()
