"""E0703 local synthetic visual/keyboard checks, no app/auth/database."""
import argparse
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from serve_ready_e0703 import server_for
from browser_hero_e05 import contrast


def wait_images(page):
    for _ in range(100):
        if page.locator('img').evaluate_all('(images)=>images.every(i=>i.complete && i.naturalWidth>0)'):
            return
        page.wait_for_timeout(50)
    raise AssertionError('Controlled local images did not load.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--chromium', required=True)
    args = parser.parse_args()
    args.evidence.mkdir(exist_ok=False)
    results = []
    geometry = {}
    with server_for(args.html) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=args.chromium, headless=True)
                page = browser.new_page(reduced_motion='reduce')
                errors, requests = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: requests.append(r.url))
                for case in ('studio-a', 'studio-b', 'paper-serif', 'empty-draft'):
                    for width in (320, 375, 640, 768, 1024, 1440):
                        page.set_viewport_size({'width': width, 'height': 960})
                        page.goto(origin+'/'+case+'.html')
                        page.locator('h1').wait_for(state='visible')
                        page.locator('.portfolio').evaluate("e=>e.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                        wait_images(page)
                        assert page.locator('h1').count() == 1
                        sections = page.locator('[data-ready-section]').evaluate_all('(es)=>es.map(e=>e.dataset.readySection)')
                        assert sections == (['navigation','hero','about','projects','contact','footer'] if case != 'empty-draft' else ['navigation','hero','footer'])
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), (case, width, 'overflow')
                        assert page.locator('img').count() == (5 if case != 'empty-draft' else 0)
                        assert not page.locator('img:not([alt]),img[alt=""]').count()
                        metrics = page.evaluate('''() => {
                          const root=document.querySelector('.portfolio'),cs=getComputedStyle(root),rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number);
                          const get=s=>{const e=root.querySelector(s);if(!e)return null;const c=getComputedStyle(e);return {color:rgb(c.color),background:rgb(c.backgroundColor)};};
                          return {text:rgb(cs.color),background:rgb(cs.backgroundColor),button:get('.button'),contact:get('.contactLink'),contactSurface:get('.contact'),
                            surface:cs.getPropertyValue('--ce-surface').trim(),
                            grid:root.querySelector('.projectGrid')?getComputedStyle(root.querySelector('.projectGrid')).gridTemplateColumns:null,
                            portraitRatio:getComputedStyle(root.querySelector('.heroPortrait')).aspectRatio,
                            font:getComputedStyle(root.querySelector('h1')).fontFamily,
                            animation:getComputedStyle(root.querySelector('h1')).animationName};
                        }''')
                        assert contrast(metrics['text'], metrics['background']) >= 4.5
                        if metrics['button']:
                            assert contrast(metrics['button']['color'], metrics['button']['background']) >= 4.5
                        if metrics['contact']:
                            assert contrast(metrics['contact']['color'], metrics['contactSurface']['background']) >= 4.5
                        assert metrics['animation'] == 'none'
                        assert metrics['portraitRatio'] == ('1 / 1' if width < 640 else '4 / 5')
                        if case != 'empty-draft':
                            geometry[(case, width)] = (metrics['grid'], metrics['portraitRatio'], metrics['font'])
                            # Navigation and structure suitable for assistive technology, not a screen-reader certification.
                            assert page.locator('nav[aria-label]').count() == 1
                            assert page.locator('h2').count() == 3
                            assert page.locator('h3').count() == 3
                        links = page.locator('a')
                        for index in range(links.count()):
                            page.keyboard.press('Tab')
                            assert links.nth(index).evaluate('(e)=>e===document.activeElement'), (case, width, index)
                            assert links.nth(index).evaluate('(e)=>getComputedStyle(e).outlineStyle') != 'none'
                        # Link d'évitement and actual internal target focus.
                        page.goto(origin+'/'+case+'.html')
                        page.keyboard.press('Tab')
                        page.keyboard.press('Enter')
                        assert page.locator('[data-ready-section="hero"]').evaluate('(e)=>e===document.activeElement')
                        page.evaluate('document.activeElement.blur();scrollTo(0,0)')
                        page.locator('.portfolio').evaluate("e=>e.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                        wait_images(page)
                        if width in (375, 768, 1440):
                            page.screenshot(path=str(args.evidence/f'{case}-{width}.png'), full_page=True)
                        # Fixed legal maximum lengths, plus layout zoom. No document contract is changed.
                        page.evaluate('''() => {
                          document.querySelector('h1').textContent='W'.repeat(160);
                          const subtitle=document.querySelector('.heroSubtitle');if(subtitle)subtitle.textContent='Description '.repeat(30).slice(0,300);
                          document.querySelectorAll('h2').forEach(e=>e.textContent='W'.repeat(120));
                          document.querySelectorAll('h3').forEach(e=>{const target=e.querySelector('a')??e;target.firstChild.textContent='W'.repeat(120);});
                          document.querySelectorAll('.actionLabel').forEach(e=>e.textContent='W'.repeat(60));
                          document.querySelectorAll('.projectMeta p').forEach(e=>e.textContent='W'.repeat(300));
                          document.querySelectorAll('.aboutBody p').forEach(e=>e.textContent='W'.repeat(1000));
                          document.querySelector('.identity span:last-child').textContent='W'.repeat(80);
                          const footer=document.querySelector('.footer p');if(footer)footer.textContent='W'.repeat(160);
                          document.body.style.zoom='2';
                        }''')
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), (case, width, 'zoom/long')
                        results.append({'case': case, 'width': width, 'keyboard': 'passed', 'contrast': 'passed', 'zoom_200_and_long_text': 'passed', 'sections': sections})
                    page.emulate_media(forced_colors='active')
                    page.goto(origin+'/'+case+'.html')
                    page.keyboard.press('Tab')
                    assert page.locator('a').first.evaluate('(e)=>e===document.activeElement')
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    page.emulate_media(forced_colors='none')
                for width in (320, 375, 640, 768, 1024, 1440):
                    assert geometry[('studio-a',width)] == geometry[('studio-b',width)], (width, 'composition changed')
                assert not errors, errors
                assert all(urlsplit(u).netloc == urlsplit(origin).netloc for u in requests), requests
                browser.close()
        finally:
            server.shutdown()
    (args.evidence/'browser-results.json').write_text(json.dumps({'checks':results,'composition_substitution':'six width comparisons passed','forced_colors':'4 passed','page_errors':errors,'remote_requests':0,'screenshots':12,'limitations':['Linux Chromium only, Windows/Safari/Firefox unrun.','Semantic structure and alt tested, no real screen-reader session.','200% CSS zoom; OS display scaling not tested.']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('24 viewport cases, 24 zoom/text cases, 4 forced-colors cases, 6 content-substitution comparisons, 12 screenshots: passed.')


if __name__ == '__main__':
    main()
