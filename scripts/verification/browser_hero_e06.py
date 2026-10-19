"""Browser checks on static E06 references. No network API, credentials or database.
Requires test-only Playwright and a locally installed Chromium executable.
"""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright


def contrast(a, b):
    def luminance(rgb):
        channels = [v / 255 for v in rgb]
        return sum(w * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
                   for w, v in zip((.2126, .7152, .0722), channels))
    x, y = sorted((luminance(a), luminance(b)))
    return (y + .05) / (x + .05)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--chromium', required=True)
    args = parser.parse_args()
    args.evidence.mkdir(exist_ok=False)
    results = []
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(args.html.resolve())))
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium, headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 960}, reduced_motion='reduce')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        for layout in ('asymmetric', 'product-showcase', 'bento-grid'):
            for width in (320, 375, 640, 768, 1024, 1440):
                page.set_viewport_size({'width': width, 'height': 960})
                page.goto(origin + '/' + layout + '.html')
                page.locator('h1').wait_for(state='visible')
                metrics = page.evaluate('''() => {
                  const hero=document.querySelector('[data-hero-layout]'),copy=hero.querySelector('.copy'),h1=hero.querySelector('h1'),cta=hero.querySelector('a');
                  const rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number);
                  const cs=getComputedStyle(copy),as=getComputedStyle(cta);
                  return {overflow:document.documentElement.scrollWidth>innerWidth,
                    text:rgb(cs.color),surface:rgb(cs.backgroundColor),accent:rgb(as.backgroundColor),link:rgb(as.color),
                    alpha:cs.backgroundColor,align:cs.textAlign,weight:getComputedStyle(h1).fontWeight,
                    heading:h1.getBoundingClientRect().width,animation:getComputedStyle(h1).animationName,
                    columns:getComputedStyle(hero.querySelector('.frame')).gridTemplateColumns};
                }''')
                assert not metrics['overflow'], (layout, width, metrics)
                assert contrast(metrics['text'], metrics['surface']) >= 4.5
                assert contrast(metrics['link'], metrics['accent']) >= 4.5
                assert metrics['animation'] == 'none'
                assert metrics['align'] == ('center' if width < 640 or (width >= 1024 and layout == 'centered') else 'left')
                assert metrics['heading'] > 0
                geometry = page.evaluate("""() => {
                  const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
                  const id=document.querySelector('[data-hero-layout]').dataset.heroLayout;
                  return {copy:rect('.copy'),parts:id==='asymmetric'?[rect('.offsetArt')]:id==='product-showcase'?[rect('.productPanel')]:Array.from(document.querySelectorAll('.bentoTile')).map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};})};
                }""")
                assert all(part['height'] > 0 for part in geometry['parts'])
                if width >= 640:
                    assert geometry['parts'][0]['x'] > geometry['copy']['x']
                    if layout == 'asymmetric':
                        assert geometry['copy']['y'] > geometry['parts'][0]['y']
                    if layout == 'product-showcase':
                        assert abs((geometry['copy']['y'] + geometry['copy']['height']/2) -
                                   (geometry['parts'][0]['y'] + geometry['parts'][0]['height']/2)) < 2
                    if layout == 'bento-grid':
                        assert geometry['parts'][1]['y'] > geometry['parts'][0]['y']
                else:
                    assert geometry['parts'][0]['y'] >= geometry['copy']['y'] + geometry['copy']['height']

                page.keyboard.press('Tab')
                assert page.locator('a').evaluate('(e)=>e===document.activeElement')
                assert page.locator('a').evaluate('(e)=>getComputedStyle(e).outlineStyle') != 'none'
                page.keyboard.press('Enter')
                assert page.evaluate('location.hash') == '#projects'
                assert page.locator('#projects').evaluate('(e)=>e===document.activeElement')
                page.evaluate('document.activeElement.blur();scrollTo(0,0)')
                if width in (375, 768, 1440):
                    page.screenshot(path=str(args.evidence / f'{layout}-{width}.png'), full_page=True)
                # Maximum accepted content lengths and doubled layout zoom.
                page.evaluate('''() => {
                  document.querySelector('h1').textContent='W'.repeat(160);
                  document.querySelector('.subtitle').textContent='Texte '.repeat(84).slice(0,500);
                  document.querySelector('.ctaLabel').textContent='W'.repeat(60);
                  document.body.style.zoom='2';
                }''')
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), (layout, width, 'long content + 200% zoom')
                results.append({'layout': layout, 'width': width, 'text_contrast': round(contrast(metrics['text'], metrics['surface']), 3),
                                'cta_contrast': round(contrast(metrics['link'], metrics['accent']), 3),
                                'keyboard': 'passed', 'long_content_200_percent_zoom': 'passed', 'alignment': metrics['align']})
            page.emulate_media(forced_colors='active')
            page.goto(origin + '/' + layout + '.html')
            page.keyboard.press('Tab')
            assert page.locator('a').evaluate('(e)=>e===document.activeElement')
            page.emulate_media(forced_colors='none')
        assert not errors, errors
        browser.close()
    server.shutdown()
    server.server_close()
    (args.evidence / 'browser-results.json').write_text(json.dumps({'browser': 'Chromium', 'results': results,
        'screenshots': 9, 'forced_colors': '3 passed', 'page_errors': errors,
        'limitations': ['Linux Chromium only; no Windows, Safari, Firefox or screen-reader certification.',
                        'CSS zoom exercised; operating-system display scaling not tested.']}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('18 viewport checks; 18 long-content/200% zoom checks; 3 forced-colors checks; 9 screenshots. Passed.')


if __name__ == '__main__':
    main()
