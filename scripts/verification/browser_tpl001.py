"""Read-only TPL-001.B browser evidence; creates one synthetic AUTH user.

Use a disposable SaaS database only. No migrations, portfolio writes or media.
Credentials/cookies are generated in memory and never written to evidence.
"""
import argparse
import json
import secrets
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',required=True)
    parser.add_argument('--chromium',required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--disposable-database',action='store_true',required=True)
    args=parser.parse_args();origin=args.origin.rstrip('/')
    url=urlsplit(origin)
    if url.scheme!='http' or url.hostname not in ['127.0.0.1','localhost'] or url.path:
        raise ValueError('Local disposable instance required.')
    args.evidence.mkdir(parents=True,exist_ok=True)
    password=secrets.token_urlsafe(30)
    email='tpl-preview-'+secrets.token_hex(6)+'@example.test'
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        try:
            anonymous=browser.new_context()
            page=anonymous.new_page();page.goto(origin+'/templates/minimal/1.0.0');page.wait_for_url('**/login')
            assert anonymous.request.get(origin+'/api/v1/templates').status==401
            anonymous.close()
            context=browser.new_context(viewport={'width':1365,'height':1000},color_scheme='light',reduced_motion='reduce')
            def post(path,data):
                token=context.request.get(origin+'/api/v1/auth/csrf').json()['csrf_token']
                return context.request.post(origin+path,data=data,headers={'X-CSRFToken':token,'Origin':origin})
            assert post('/api/v1/auth/register',{'email':email,'first_name':'Profil','last_name':'Synthétique','password':password,'password_confirmation':password}).status==201
            assert post('/api/v1/auth/login',{'email':email,'password':password}).status==200
            initial=context.request.get(origin+'/api/v1/portfolios').json()['count']
            assert post('/api/v1/templates',{}).status==405
            assert context.request.post(origin+'/api/v1/templates',data={}).status==403
            page=context.new_page();errors=[];remote=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda req:remote.append(req.url) if not req.url.startswith(origin+'/') else None)
            for width in [1365,390]:
                page.set_viewport_size({'width':width,'height':1000 if width>600 else 844})
                page.goto(origin+'/templates');page.get_by_role('heading',name='Deux regards sur votre travail.').wait_for()
                for name,layout in [('minimal','minimal-stack'),('editorial','editorial-grid')]:
                    page.goto(origin+f'/templates/{name}/1.0.0')
                    frame=page.get_by_test_id('template-frame');frame.locator(f'[data-layout="{layout}"]').wait_for()
                    assert frame.locator('[data-section]').count()==5
                    assert frame.locator('[data-section="projects"] article').count()==3
                    assert frame.get_by_text('Contenus et projets fictifs').is_visible()
                    assert page.locator('body').evaluate('(el)=>el.scrollWidth<=window.innerWidth')
                    assert frame.evaluate('(el)=>el.scrollWidth<=el.clientWidth+2')
                    assert not page.get_by_role('button',name='Créer',exact=True).count()
                    page.get_by_role('button',name='Mobile',exact=True).click()
                    assert page.get_by_role('button',name='Mobile',exact=True).get_attribute('aria-pressed')=='true'
                    assert frame.bounding_box()['width']<=390
                    assert frame.locator('[data-section="projects"] article').first.bounding_box()['width']>200
                    page.get_by_role('button',name='Desktop',exact=True).focus();page.keyboard.press('Space')
                    assert page.get_by_role('button',name='Desktop',exact=True).get_attribute('aria-pressed')=='true'
                    if width==1365:
                        page.get_by_role('button',name='Mobile',exact=True).click()
                        frame.screenshot(path=str(args.evidence/f'{name}-container-mobile.png'))
                        page.get_by_role('button',name='Desktop',exact=True).click()
                        assert frame.bounding_box()['width']>900
                    frame.screenshot(path=str(args.evidence/f'{name}-{width}.png'))
                    results.append({'template':name,'viewport':width,'layout':layout,'sections':5,'projects':3,'overflow':False,'shared_renderer':True})
            assert context.request.get(origin+'/api/v1/portfolios').json()['count']==initial
            assert not errors,errors
            assert not remote,'Unexpected external resource request'
            assert context.request.get(origin+'/api/v1/templates/minimal/versions/999.0.0').status==404
            page.goto(origin+'/templates/minimal/999.0.0');page.get_by_role('heading',name='404',exact=True).wait_for()
            assert post('/api/v1/auth/logout',{}).status==200
            page.goto(origin+'/templates');page.wait_for_url('**/login')
            assert context.request.get(origin+'/api/v1/templates').status==401
            context.close()
            (args.evidence/'browser-results.json').write_text(json.dumps({'platform':'Linux Chromium','synthetic_only':True,'results':results,'anonymous_redirect':True,'write_denied':True,'csrf_preserved':True,'logout_guard':True,'no_portfolio_created':True,'external_requests':0,'page_errors':0},ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
            print('PASS: both templates desktop/mobile; shared renderer, session/CSRF, read-only, no overflow/external request.')
        finally:browser.close()

if __name__=='__main__':main()
