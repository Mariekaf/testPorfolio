"""E0703 pure fixture/SSR and preview isolation tests. No Django or DB."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from modules.templates.hero_contracts import ROOT
from modules.templates.ready_registry import ReadyRegistry

FIXTURES=json.loads((ROOT/'contracts/fixtures/ready-rendering/demonstration.v1.json').read_text(encoding='utf-8'))


def render(cases):
    run=subprocess.run(['node',str(ROOT/'scripts/verification/ready-rendering-driver.mjs')],input=json.dumps(cases,ensure_ascii=False),encoding='utf-8',capture_output=True,check=True,cwd=ROOT,timeout=30)
    return json.loads(run.stdout)


class ReadyRenderingTests(unittest.TestCase):
    def test_both_datasets_validate_and_actual_react_bindings_match(self):
        validator=ReadyRegistry().validator();before=copy.deepcopy(FIXTURES)
        for case in FIXTURES['cases']:validator.validate(case['document'])
        output=render(FIXTURES['cases'])
        self.assertNotEqual(output[0],output[1])
        for case,html in zip(FIXTURES['cases'],output):
            self.assertIn(case['document']['content']['slots']['identity_name']['value'],html)
            self.assertIn('data-ready-section="projects"',html)
            self.assertEqual(html.count('<h1 '),1)
            self.assertIn('Démonstration synthétique',html)
        self.assertEqual(FIXTURES,before)
        a,b=FIXTURES['cases'];self.assertEqual(a['document']['composition'],b['document']['composition'])
        for name,value in a['document']['content']['slots'].items():self.assertNotEqual(value,b['document']['content']['slots'][name],name)

    def test_original_local_svg_hashes_and_closed_vocabulary(self):
        directory=ROOT/'contracts/fixtures/ready-rendering/assets'
        manifest=json.loads((directory/'index.v1.json').read_text(encoding='utf-8'))
        allowed={'svg','rect','circle','path','ellipse','g'}
        for source in manifest['sources']:
            raw=(directory/source['file']).read_bytes()
            self.assertEqual(len(raw),source['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),source['sha256'])
            xml=ET.fromstring(raw)
            for element in xml.iter():
                self.assertIn(element.tag.rsplit('}',1)[-1],allowed)
                self.assertFalse(any(key.lower().startswith('on') or key.lower().endswith('href') for key in element.attrib))
        self.assertIn('CC0',(directory/'LICENSE.txt').read_text(encoding='utf-8'))

    def test_export_and_loopback_server_cannot_serve_repository_or_arbitrary_files(self):
        spec=importlib.util.spec_from_file_location('ready_preview_server',ROOT/'scripts/verification/serve_ready_e0703.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='ready-render-e0703-') as directory:
            target=Path(directory)/'preview'
            run=subprocess.run(['node',str(ROOT/'scripts/verification/render_ready_e0703.mjs'),str(target)],capture_output=True,encoding='utf-8',check=True,cwd=ROOT,timeout=30)
            self.assertIn('Four isolated previews',run.stdout)
            with module.server_for(target) as server:
                threading.Thread(target=server.serve_forever,daemon=True).start()
                origin=f'http://127.0.0.1:{server.server_port}'
                try:
                    with urllib.request.urlopen(origin+'/studio-a.html',timeout=5) as response:
                        self.assertEqual(response.status,200)
                        self.assertIn("default-src 'none'",response.headers['Content-Security-Policy'])
                        self.assertIn('no-store',response.headers['Cache-Control'])
                    for path in ('/.local/auth.json','/manifest.json','/__ready_assets/%2e%2e%2fsecret.svg','/../server.py'):
                        with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(origin+path,timeout=5)
                        self.assertEqual(caught.exception.code,404)
                finally:server.shutdown()
            with self.assertRaises(AssertionError):module.server_for(ROOT)
