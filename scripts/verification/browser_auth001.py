"""Optional AUTH-001 browser check. Requires existing Playwright + Chromium.

Use ONLY a disposable AUTH-001 database and a dedicated private mailbox.
This creates synthetic accounts. No credentials, reset links or page dumps printed.
"""
import argparse
from pathlib import Path
import secrets
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',required=True)
    parser.add_argument('--mailbox',required=True,type=Path)
    parser.add_argument('--chromium',required=True)
    parser.add_argument('--disposable-database',action='store_true',required=True)
    args=parser.parse_args()
    origin=args.origin.rstrip('/')
    if urlsplit(origin).hostname not in ('127.0.0.1','localhost'):
        raise ValueError('Only a local disposable instance is permitted.')
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        try:
            for width,height in [(1280,900),(390,844)]:
                context=browser.new_context(viewport={'width':width,'height':height})
                page=context.new_page()
                requests=[]
                page.on('request',lambda request:requests.append(request.url))
                page.goto(origin+'/dashboard');page.wait_for_url('**/login')
                email='synthetic-'+secrets.token_hex(5)+'@example.test'
                password=secrets.token_urlsafe(24)
                page.goto(origin+'/register')
                page.get_by_label('Prénom',exact=True).fill('Synthetic')
                page.get_by_label('Nom',exact=True).fill('Tester')
                page.get_by_label('Adresse e-mail',exact=True).fill(email)
                page.get_by_label('Mot de passe',exact=True).fill(password)
                page.get_by_label('Confirmer le mot de passe',exact=True).fill(password)
                page.get_by_role('button',name='Créer mon compte').click()
                page.wait_for_url('**/login?reason=registered')
                page.get_by_label('Adresse e-mail',exact=True).fill(email)
                page.get_by_label('Mot de passe',exact=True).fill(password)
                page.get_by_role('button',name='Se connecter',exact=True).click()
                page.wait_for_url('**/dashboard')
                page.get_by_role('heading',name='Bienvenue, Synthetic.').wait_for()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                session=context.cookies()
                cookie=next(c for c in session if c['name']=='portfolio_saas_session')
                assert cookie['httpOnly'] and cookie['sameSite']=='Strict'
                assert page.evaluate('localStorage.length')==0
                assert page.request.get(origin+'/api/v1/auth/me').status==200
                page.get_by_role('button',name='Se déconnecter').click()
                page.wait_for_url('**/login')
                assert page.request.get(origin+'/api/v1/auth/me').status==401
                page.goto(origin+'/forgot-password')
                page.get_by_label('Adresse e-mail',exact=True).fill(email)
                before=set(args.mailbox.glob('*.log'))
                page.get_by_role('button',name='Recevoir un lien').click()
                page.get_by_role('status').filter(has_text='Si un compte correspond').wait_for()
                files=set(args.mailbox.glob('*.log'))-before
                assert len(files)==1
                # Email text is decoded privately; never output the reset link.
                from email import policy
                from email.parser import BytesParser
                message=BytesParser(policy=policy.default).parsebytes(next(iter(files)).read_bytes())
                body=message.get_payload(decode=True).decode(message.get_content_charset() or 'utf-8')
                link=next(line for line in body.splitlines() if line.startswith(origin+'/reset-password#'))
                assert urlsplit(link).query==''
                page.goto(link)
                page.get_by_label('Mot de passe',exact=True).wait_for()
                page.wait_for_function('location.hash === ""')
                new_password=secrets.token_urlsafe(24)
                page.get_by_label('Mot de passe',exact=True).fill(new_password)
                page.get_by_label('Confirmer le mot de passe',exact=True).fill(new_password)
                page.get_by_role('button',name='Enregistrer le mot de passe').click()
                page.wait_for_url('**/login?reason=reset')
                page.get_by_label('Adresse e-mail',exact=True).fill(email)
                page.get_by_label('Mot de passe',exact=True).fill(new_password)
                page.get_by_role('button',name='Se connecter',exact=True).click()
                page.wait_for_url('**/dashboard')
                page.get_by_role('heading',name='Bienvenue, Synthetic.').wait_for()
                page.goto(link)
                page.get_by_label('Mot de passe',exact=True).fill(password)
                page.get_by_label('Confirmer le mot de passe',exact=True).fill(password)
                page.get_by_role('button',name='Enregistrer le mot de passe').click()
                page.get_by_role('status').filter(has_text='Ce lien est invalide').wait_for()
                # Tokens must stay out of all HTTP request URLs.
                from urllib.parse import parse_qs
                token=parse_qs(urlsplit(link).fragment)['token'][0]
                assert all(token not in url for url in requests)
                page.goto(origin+'/dashboard')
                page.get_by_role('heading',name='Bienvenue, Synthetic.').wait_for()
                peer=context.new_page();peer.goto(origin+'/dashboard')
                peer.get_by_role('heading',name='Bienvenue, Synthetic.').wait_for()
                page.get_by_role('button',name='Se déconnecter').click()
                page.wait_for_url('**/login')
                peer.wait_for_url('**/login?reason=expired')
                context.close()
                print(f'PASS {width}px: private-route, registration, login, logout, local-mail reset, reused-link rejection, cookie flags, no localStorage, responsive layout, cross-tab logout, reset token absent from HTTP URLs.')
        finally:
            browser.close()

if __name__=='__main__':
    main()
