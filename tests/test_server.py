import base64
import http.cookiejar
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('portfolio', ROOT/'server.py')
portfolio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portfolio)

class PortfolioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os, socket
        cls.tmp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.tmp.name)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
        cls.base='http://127.0.0.1:'+str(port)
        cls.process=subprocess.Popen(['python3',str(ROOT/'server.py'),'--host','127.0.0.1','--port',str(port)],env={**os.environ,'PORTFOLIO_DATA_DIR':cls.tmp.name},stdout=subprocess.DEVNULL)
        for _ in range(100):
            try:
                urllib.request.urlopen(cls.base+'/api/content',timeout=1).close()
                break
            except OSError:time.sleep(.05)
        else:raise RuntimeError('Server did not start')
        cls.password=(cls.data/'initial-password.txt').read_text()

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate();cls.process.wait();cls.tmp.cleanup()

    def setUp(self):
        self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf=''

    def request(self,path,value=None,raw=False,csrf=True):
        headers={}
        if value is not None:
            headers['Content-Type']='application/octet-stream' if raw else 'application/json'
        if self.csrf and csrf:headers['X-CSRF-Token']=self.csrf
        req=urllib.request.Request(self.base+path,data=value if raw else json.dumps(value).encode() if value is not None else None,headers=headers)
        try:r=self.client.open(req)
        except urllib.error.HTTPError as e:r=e
        body=r.read()
        return r.status,json.loads(body) if r.headers['Content-Type'].startswith('application/json') else body

    def login(self):
        status,result=self.request('/api/login',{'password':self.password})
        self.assertEqual(status,200);self.csrf=result['csrf']

    def test_auth_csrf_and_private_files(self):
        self.assertEqual(self.request('/api/admin/content')[0],401)
        self.assertEqual(self.request('/api/admin/backup')[0],401)
        self.assertEqual(self.request('/.local/auth.json')[0],404)
        self.assertEqual(self.request('/api/login',{'password':'wrong'})[0],401)
        self.login()
        _,content=self.request('/api/admin/content')
        self.assertEqual(self.request('/api/admin/content',content,csrf=False)[0],403)
        self.assertEqual(self.request('/api/logout',{})[0],200)
        self.assertEqual(self.request('/api/admin/content')[0],401)

    def test_persistence_drafts_and_revision_conflicts(self):
        self.login();_,content=self.request('/api/admin/content')
        project=json.loads(json.dumps(content['projects'][0]))
        project.update(id='test-draft',slug='test-draft',title='Projet privé',published=False)
        content['projects'].append(project)
        status,saved=self.request('/api/admin/content',content)
        self.assertEqual(status,200)
        _,public=self.request('/api/content')
        self.assertNotIn('test-draft',[p['id'] for p in public['projects']])
        self.assertIn('test-draft',[p['id'] for p in json.loads((self.data/'content.json').read_text())['projects']])
        self.assertEqual(self.request('/api/admin/content',content)[0],409)
        saved['projects'][-1]['published']=True
        self.assertEqual(self.request('/api/admin/content',saved)[0],200)
        _,public=self.request('/api/content')
        self.assertIn('test-draft',[p['id'] for p in public['projects']])
        # Restart the actual server to prove data and authentication persist.
        self.process.terminate();self.process.wait()
        import os
        port=self.base.rsplit(':',1)[1]
        type(self).process=subprocess.Popen(['python3',str(ROOT/'server.py'),'--host','127.0.0.1','--port',port],env={**os.environ,'PORTFOLIO_DATA_DIR':str(self.data)},stdout=subprocess.DEVNULL)
        for _ in range(100):
            try:
                status,public=self.request('/api/content')
                break
            except OSError:time.sleep(.05)
        self.assertIn('test-draft',[p['id'] for p in public['projects']])
        self.assertEqual(self.request('/api/admin/content')[0],401)
        self.login()
        self.assertEqual(self.request('/api/admin/content')[0],200)

    def test_images_backup_and_link_validation(self):
        self.login()
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZ1cAAAAASUVORK5CYII=')
        status,result=self.request('/api/admin/upload',png,raw=True)
        self.assertEqual(status,201)
        self.assertEqual(self.request(result['url'])[1],png)
        self.assertEqual(self.request('/api/admin/upload',b'<svg></svg>',raw=True)[0],400)
        status,archive=self.request('/api/admin/backup')
        self.assertEqual(status,200)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            self.assertIn('content.json',z.namelist())
            self.assertIn(result['url'].lstrip('/'),z.namelist())
            self.assertNotIn('auth.json',z.namelist())
        _,content=self.request('/api/admin/content')
        content['site']['socials']=[{'label':'malicious','url':'javascript:alert(1)'}]
        self.assertEqual(self.request('/api/admin/content',content)[0],400)
        content['site']['socials']=[]
        content['projects'][1]['slug']=content['projects'][0]['slug']
        self.assertEqual(self.request('/api/admin/content',content)[0],400)

if __name__=='__main__':unittest.main()
