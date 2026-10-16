"""Optional browser reference checks, only against a synthetic temporary dataset.

Requires an existing Playwright installation and Chromium. Does not install either.
Usage: python -B scripts/verification/browser_base001.py --chromium /path/to/chromium
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/base001'


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def passed(case, message):
    print(case + ' PASS - ' + message, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium', required=True)
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix='base001-') as folder:
        temporary = Path(folder)
        data = temporary / 'data'
        data.mkdir()
        shutil.copyfile(FIXTURE / 'legacy-content.json', data / 'content.json')
        shutil.copytree(FIXTURE / 'uploads', data / 'uploads')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        origin = 'http://127.0.0.1:' + str(port)
        process = subprocess.Popen(
            [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'server.py'), '--host', '127.0.0.1', '--port', str(port)],
            cwd=ROOT, env={**os.environ, 'PORTFOLIO_DATA_DIR': str(data), 'PYTHONDONTWRITEBYTECODE': '1'},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(origin + '/api/content', timeout=1):
                        break
                except OSError:
                    if process.poll() is not None:
                        raise RuntimeError('Temporary server exited')
                    time.sleep(.05)
            else:
                raise RuntimeError('Temporary server did not become ready')
            # Only the ephemeral server's own generated credential, never a user file.
            password = (data / 'initial-password.txt').read_text(encoding='utf-8')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.chromium)
                try:
                    studio_context = browser.new_context(viewport={'width': 1440, 'height': 1000})
                    guest_context = browser.new_context(viewport={'width': 1440, 'height': 1000})
                    page, public = studio_context.new_page(), guest_context.new_page()
                    errors = []
                    studio_context.on('page', lambda p: p.on('pageerror', lambda e: errors.append(str(e))))
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    public.on('pageerror', lambda e: errors.append(str(e)))
                    public.goto(origin)
                    public.locator('.project').first.wait_for()
                    check(public.locator('.project').count() == 2, 'Draft appears publicly')
                    check(public.locator('.project h3').all_text_contents() == ['Projet alpha', 'Projet gamma'], 'Public order')
                    check(public.locator('.portrait').get_attribute('alt') == 'Carré vert synthétique', 'Portrait alt')
                    check(public.locator('#apropos').inner_text().find('Échantillon éditorial fictif.') >= 0, 'About')
                    check(public.locator('a[href="mailto:studio@example.test"]').count() == 1, 'Contact')
                    passed('B01', 'Accueil, portrait, ordre public, a propos et contact synthetiques')
                    public.locator('.project').first.click()
                    public.locator('.case-block').first.wait_for()
                    public.reload()
                    public.locator('.case-block').first.wait_for()
                    check(public.locator('.case-block').count() == 2, 'Sections')
                    check('<script>exemple</script>' in public.locator('.case-body').first.inner_text(), 'Literal text')
                    check('東京' in public.locator('.case-body').first.inner_text(), 'Unicode')
                    check(public.locator('.case-facts').inner_text().find('Conception') >= 0, 'Metadata')
                    check(public.locator('.case-links a').get_attribute('href') == 'https://example.test/prototype/alpha', 'Project link')
                    check(public.locator('.case-block img').get_attribute('alt') == 'Carré vert synthétique', 'Section alt')
                    check(public.locator('.next-project').get_attribute('href') == '/projet/gamma', 'Next project')
                    response = public.goto(origin + '/projet/inexistant')
                    public.get_by_role('heading', name='Projet introuvable', exact=True).wait_for()
                    check(response.status == 200, 'Legacy missing-project HTTP behavior changed')
                    passed('B02', 'Page dediee rechargeable, sections Unicode, liens et introuvable HTTP 200 observe')
                    page.goto(origin + '/admin')
                    page.get_by_label('Mot de passe').fill(password)
                    page.get_by_role('button', name='Entrer dans mon studio').click()
                    page.get_by_role('heading', name='Mes projets', exact=True).wait_for()
                    check(page.locator('.project-row').count() == 3, 'Admin projects')
                    passed('B03', 'Connexion via identifiant ephemere, liste privee complete')

                    def save():
                        page.get_by_role('button', name='Enregistrer', exact=True).click()
                        page.get_by_text('Tout est enregistré', exact=True).wait_for()

                    page.get_by_role('button', name='+ Nouveau projet', exact=True).click()
                    page.get_by_label('Titre du projet', exact=True).fill('Projet delta')
                    page.get_by_label('Adresse de la page').fill('delta')
                    page.get_by_label('Description courte').fill('Résumé delta synthétique')
                    with page.expect_file_chooser() as chooser:
                        page.get_by_role('button', name='Importer une image', exact=True).first.click()
                    chooser.value.set_files(str(FIXTURE / 'uploads/11111111111111111111111111111111.png'))
                    page.locator('.image-preview').first.wait_for()
                    page.get_by_label('Description de l’image (accessibilité)').first.fill('Couverture synthétique delta')
                    save()
                    public.goto(origin)
                    public.locator('.project').first.wait_for()
                    check(public.locator('.project').count() == 2, 'New draft leaked')
                    page.get_by_label('Publier ce projet').check()
                    save()
                    public.goto(origin + '/projet/delta')
                    public.get_by_role('heading', name='Projet delta', exact=True).wait_for()
                    check(public.locator('.case-cover').get_attribute('alt') == 'Couverture synthétique delta', 'Uploaded cover')
                    page.get_by_label('Description courte').fill('Résumé modifié immédiatement')
                    save()
                    public.reload()
                    public.get_by_text('Résumé modifié immédiatement', exact=True).wait_for()
                    passed('B04', 'Creation, image, brouillon et publication immediate historique apres sauvegarde')
                    page.get_by_role('button', name='+ Ajouter une section', exact=True).click()
                    page.get_by_label('Titre de section', exact=True).last.fill('Section ajoutée')
                    page.get_by_label('Votre récit', exact=True).last.fill('Récit ajouté')
                    page.get_by_role('button', name='Monter la section 6', exact=True).click()
                    check(page.get_by_label('Titre de section', exact=True).nth(4).input_value() == 'Section ajoutée', 'Section order')
                    page.once('dialog', lambda d: d.accept())
                    page.locator('.section-block').last.get_by_role('button', name='Supprimer', exact=True).click()
                    page.get_by_role('button', name='+ Ajouter un lien', exact=True).click()
                    page.get_by_label('Libellé', exact=True).fill('Prototype delta')
                    page.get_by_label('Lien', exact=True).fill('https://example.test/delta')
                    save()
                    public.reload()
                    public.get_by_role('link', name='Prototype delta').wait_for()
                    page.locator('.link-row').get_by_role('button', name='Retirer', exact=True).click()
                    page.locator('.image-actions').first.get_by_role('button', name='Retirer', exact=True).click()
                    save()
                    public.reload()
                    check(public.locator('.case-cover').count() == 0, 'Cover reference not removed')
                    passed('B05', 'Sections ajoutees/reordonnees/supprimees, liens et retrait de couverture')
                    page.get_by_role('button', name='Dupliquer', exact=True).click()
                    check(not page.get_by_label('Publier ce projet').is_checked(), 'Copy published')
                    check(page.get_by_label('Adresse de la page').input_value() != 'delta', 'Copy slug')
                    save()
                    page.once('dialog', lambda d: d.accept())
                    page.get_by_role('button', name='Supprimer le projet', exact=True).click()
                    save()
                    check(page.locator('.project-row').count() == 4, 'Copy deletion')
                    page.get_by_role('button', name='Descendre Projet alpha', exact=True).click()
                    save()
                    check(page.locator('.row-content h3').all_text_contents()[:2] == ['Projet beta', 'Projet alpha'], 'Project reorder')
                    passed('B06', 'Duplication privee, suppression et ordre des projets')
                    public.goto(origin + '/?preview=1')
                    public.get_by_text('Connectez-vous au back-office pour voir cet aperçu.', exact=True).wait_for()
                    preview = studio_context.new_page()
                    preview.goto(origin + '/?preview=1')
                    preview.locator('.project').first.wait_for()
                    check(preview.locator('.project').count() == 4, 'Private preview incomplete')
                    preview.locator('.project').first.click()
                    preview.get_by_role('heading', name='Projet beta', exact=True).wait_for()
                    check('preview=1' in preview.url, 'Private preview navigation')
                    preview.close()
                    passed('B07', 'Apercu refuse invite, brouillon visible en session et navigation privee')
                    page.get_by_role('button', name='Mon contenu').click()
                    page.get_by_label('Présentation courte', exact=True).fill('Présentation synthétique modifiée')
                    page.get_by_label('Adresse e-mail', exact=True).fill('contact@example.test')
                    save()
                    public.goto(origin)
                    public.get_by_text('Présentation synthétique modifiée', exact=True).wait_for()
                    check(public.locator('a[href="mailto:contact@example.test"]').count() == 1, 'Updated contact')
                    social = public.locator('.socials a')
                    check(social.get_attribute('rel') == 'noopener noreferrer', 'External link protection')
                    page.get_by_label('Adresse e-mail', exact=True).fill('')
                    save()
                    public.reload()
                    public.locator('.project').first.wait_for()
                    check(public.locator('a[href^="mailto:"]').count() == 0, 'Empty contact visible')
                    passed('B08', 'Edition profil/contact, liens proteges et masquage sans email')
                    page.get_by_role('button', name='Apparence').click()
                    color = page.get_by_label('Accent', exact=True)
                    color.fill('#334455')
                    check(page.locator('#theme-preview').evaluate('(n)=>n.style.getPropertyValue("--sample-accent")') == '#334455', 'Palette preview')
                    for label, value in [('Style des titres','serif'),('Coins des visuels','round'),('Espacement','compact'),('Grille des projets','one')]:
                        page.get_by_label(label).select_option(value)
                    save()
                    public.reload()
                    public.locator('.project').first.wait_for()
                    for key, value in [('font','serif'),('radius','round'),('density','compact'),('columns','one')]:
                        check(public.locator('body').get_attribute('data-'+key) == value, 'Theme option '+key)
                    check(public.locator('html').evaluate('(n)=>n.style.getPropertyValue("--green")') == '#334455', 'Public accent')
                    passed('B09', 'Palette apercue et theme public: serif, arrondi, compact, une colonne')
                    page.get_by_role('button', name='Mon contenu').click()
                    page.get_by_label('Texte du pied de page', exact=True).fill('Modification non enregistrée synthétique')
                    page.get_by_role('button', name='Sauvegardes').click()
                    with page.expect_download() as download:
                        page.get_by_role('button', name='Exporter le contenu JSON', exact=True).click()
                    export_path = temporary / 'export.json'
                    download.value.save_as(export_path)
                    check(json.loads(export_path.read_text(encoding='utf-8'))['site']['footer'] == 'Modification non enregistrée synthétique', 'JSON memory export')
                    with page.expect_download() as download:
                        page.get_by_role('button', name='Télécharger contenu + images', exact=True).click()
                    archive_path = temporary / 'backup.zip'
                    download.value.save_as(archive_path)
                    with zipfile.ZipFile(archive_path) as archive:
                        check(json.loads(archive.read('content.json'))['site']['footer'] != 'Modification non enregistrée synthétique', 'ZIP must use disk')
                        check('uploads/33333333333333333333333333333333.png' in archive.namelist(), 'Orphan lost')
                        check('auth.json' not in archive.namelist() and 'initial-password.txt' not in archive.namelist(), 'Credential in export')
                    page.once('dialog', lambda d: d.dismiss())
                    page.locator('#import-picker').set_input_files(str(FIXTURE / 'legacy-content.json'))
                    page.get_by_role('button', name='Mon contenu').click()
                    check(page.get_by_label('Texte du pied de page', exact=True).input_value() == 'Modification non enregistrée synthétique', 'Cancelled import changed memory')
                    page.get_by_role('button', name='Sauvegardes').click()
                    page.once('dialog', lambda d: d.accept())
                    page.locator('#import-picker').set_input_files(str(FIXTURE / 'legacy-content.json'))
                    page.get_by_role('button', name='Mes projets').click()
                    check(page.locator('.project-row').count() == 3, 'Confirmed import did not replace memory')
                    public.reload()
                    public.locator('.project').first.wait_for()
                    check(public.locator('.project').count() == 3, 'Import applied before save')
                    save()
                    public.reload()
                    public.locator('.project').first.wait_for()
                    check(public.locator('.project').count() == 2, 'Saved import absent')
                    passed('B10', 'Exports memoire/disque, medias orphelins conserves, import annule/confirme puis sauvegarde')
                    page.get_by_role('button', name='Mon contenu').click()
                    page.get_by_label('Texte du pied de page', exact=True).fill('Modification non sauvegardée')
                    page.get_by_text('Modifications non enregistrées', exact=True).wait_for()
                    unload_dialogs = []
                    def accept_unload(dialog):
                        unload_dialogs.append(dialog.type)
                        dialog.accept()
                    page.once('dialog', accept_unload)
                    page.reload()
                    page.get_by_role('heading', name='Mes projets', exact=True).wait_for()
                    check(unload_dialogs == ['beforeunload'], 'Missing unsaved changes guard')
                    passed('B11', 'Indicateur dirty et avertissement beforeunload')
                    # Finish dirty editing safely, then inspect the mobile viewport.
                    save()
                    page.set_viewport_size({'width': 390, 'height': 844})
                    check(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Admin mobile overflow')
                    page.get_by_role('button', name='Mes projets').click()
                    page.get_by_role('button', name='Modifier ↗').first.click()
                    check(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Project editor mobile overflow')
                    public.set_viewport_size({'width': 390, 'height': 844})
                    public.goto(origin)
                    public.locator('.project').first.wait_for()
                    check(public.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Public mobile overflow')
                    page.get_by_role('button', name='Se déconnecter').click()
                    page.get_by_role('heading', name='Bienvenue au studio.', exact=True).wait_for()
                    check(not errors, 'Browser JavaScript errors')
                    passed('B12', 'Viewport mobile public/admin/editeur et deconnexion sans erreur JavaScript')
                finally:
                    browser.close()
        finally:
            process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=5)
            if process.poll() is None:
                process.kill()
                process.wait()
    print('12 browser scenarios passed; synthetic data only; no runtime user files accessed.')


if __name__ == '__main__':
    main()
