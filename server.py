#!/usr/bin/env python3
"""Dependency-free portfolio CMS. Run: python3 server.py."""
import argparse
import getpass
import io
import zipfile
import hashlib
import hmac
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('PORTFOLIO_DATA_DIR', ROOT / '.local')).resolve()
LOCK = threading.Lock()
SESSIONS = {}
ATTEMPTS = {}
MAX_BODY = 12 * 1024 * 1024
STATIC = {'index.html', 'style.css', 'script.js', 'admin.html', 'admin.css', 'admin.js'}

def password_record(password):
    salt = secrets.token_hex(16)
    return {'salt': salt, 'hash': hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()}

def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.chmod(0o600)
    temp.replace(path)

def initialize():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    (DATA / 'uploads').mkdir(exist_ok=True)
    if not (DATA / 'content.json').exists():
        write_json(DATA / 'content.json', json.loads((ROOT / 'content.example.json').read_text()))
    if not (DATA / 'auth.json').exists():
        password = secrets.token_urlsafe(24)
        write_json(DATA / 'auth.json', password_record(password))
        path = DATA / 'initial-password.txt'
        path.write_text(password, encoding='utf-8')
        path.chmod(0o600)

def text(value, limit=20000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError('Texte invalide ou trop long.')
    return value

def url(value, image=False):
    value = text(value, 2000).strip()
    if not value:
        return ''
    if image and re.fullmatch(r'/uploads/[a-f0-9]{32}\.(png|jpg|webp|gif)', value):
        return value
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('Utilisez un lien complet https:// ou http://.')
    return value

def validate(value):
    if not isinstance(value, dict) or not isinstance(value.get('site'), dict) or not isinstance(value.get('projects'), list):
        raise ValueError('Format de sauvegarde invalide.')
    site = value['site']
    fields = ['name','job','location','availability','heroTitle','heroDescription','projectsTitle','projectsIntro','aboutTitle','aboutIntro','aboutText','skills','contactTitle','contactText','email','footer','photoAlt']
    clean = {key: text(site.get(key, ''), 5000) for key in fields}
    if not clean['name'].strip():
        raise ValueError('Le nom est obligatoire.')
    if clean['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', clean['email']):
        raise ValueError('Adresse e-mail invalide.')
    clean['photo'] = url(site.get('photo', ''), True)
    clean['socials'] = []
    for link in site.get('socials', [])[:10]:
        clean['socials'].append({'label': text(link.get('label',''), 100), 'url': url(link.get('url',''))})
    theme = site.get('theme', {})
    clean['theme'] = {}
    for field in ['background','text','accent','surface']:
        color = theme.get(field, '')
        if not isinstance(color, str) or not re.fullmatch(r'#[a-fA-F0-9]{6}', color):
            raise ValueError('Couleur invalide.')
        clean['theme'][field] = color
    for field, choices in [('font',['sans','serif']),('radius',['square','soft','round']),('density',['compact','airy']),('columns',['one','two'])]:
        if theme.get(field) not in choices:
            raise ValueError('Option de thème invalide.')
        clean['theme'][field] = theme[field]
    projects = []
    ids, slugs = set(), set()
    if len(value['projects']) > 100:
        raise ValueError('Maximum 100 projets.')
    for project in value['projects']:
        entry = {k:text(project.get(k,''), 20000) for k in ['id','slug','title','category','summary','role','duration','year','tools','coverAlt']}
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', entry['id']) or entry['id'] in ids:
            raise ValueError('Identifiant de projet invalide ou dupliqué.')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', entry['slug']) or len(entry['slug']) > 100 or entry['slug'] in slugs:
            raise ValueError('Chaque adresse de projet doit être unique, en minuscules et avec des tirets.')
        if not entry['title'].strip():
            raise ValueError('Chaque projet doit avoir un titre.')
        ids.add(entry['id']); slugs.add(entry['slug'])
        entry['published'] = project.get('published') is True
        entry['cover'] = url(project.get('cover',''), True)
        entry['color'] = project.get('color', '#e6e9df')
        if not re.fullmatch(r'#[a-fA-F0-9]{6}', entry['color']):
            raise ValueError('Couleur de projet invalide.')
        entry['links'] = [{'label':text(x.get('label',''),100), 'url':url(x.get('url',''))} for x in project.get('links',[])[:10]]
        entry['sections'] = []
        for block in project.get('sections', [])[:60]:
            entry['sections'].append({'title':text(block.get('title',''),200), 'body':text(block.get('body','')), 'image':url(block.get('image',''),True), 'alt':text(block.get('alt',''),500), 'caption':text(block.get('caption',''),1000)})
        projects.append(entry)
    return {'site':clean, 'projects':projects}

class Handler(BaseHTTPRequestHandler):
    server_version = 'Portfolio'
    def log_message(self, fmt, *args):
        # Never log credentials, request bodies or URL query strings.
        print('%s %s' % (self.command, self.path.split('?')[0]), flush=True)

    def respond(self, status, body, mime='application/json; charset=utf-8', extra=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: http:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        for key, val in (extra or {}).items():
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(body)

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie',''))
            session = SESSIONS.get(cookie['portfolio_session'].value)
            if session and session['expires'] > time.time():
                return session
        except (KeyError, ValueError):
            pass
        return None

    def same_origin(self):
        origin = self.headers.get('Origin')
        return not origin or urlsplit(origin).netloc == self.headers.get('Host')

    def read_body(self):
        length = int(self.headers.get('Content-Length','0'))
        if length < 0 or length > MAX_BODY:
            raise ValueError('Fichier trop volumineux (maximum 12 Mo).')
        return self.rfile.read(length)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/api/content':
            content = json.loads((DATA/'content.json').read_text())
            content['projects'] = [p for p in content['projects'] if p['published']]
            return self.respond(200, content)
        if path == '/api/admin/session':
            session = self.session()
            return self.respond(200 if session else 401, {'csrf':session['csrf']} if session else {'error':'Connexion requise.'})
        if path == '/api/admin/backup':
            if not self.session():
                return self.respond(401, {'error':'Connexion requise.'})
            buffer = io.BytesIO()
            with LOCK, zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.write(DATA/'content.json', 'content.json')
                for asset in (DATA/'uploads').iterdir():
                    if asset.is_file():
                        archive.write(asset, 'uploads/'+asset.name)
            return self.respond(200, buffer.getvalue(), 'application/zip', {'Content-Disposition':'attachment; filename=portfolio-sauvegarde.zip'})
        if path == '/api/admin/content':
            if not self.session():
                return self.respond(401, {'error':'Connexion requise.'})
            return self.respond(200, json.loads((DATA/'content.json').read_text()))
        if path.startswith('/uploads/'):
            name = path.removeprefix('/uploads/')
            if not re.fullmatch(r'[a-f0-9]{32}\.(png|jpg|webp|gif)', name):
                return self.respond(404, {'error':'Image introuvable.'})
            file = DATA/'uploads'/name
        else:
            name = 'admin.html' if path in ('/admin','/admin/') else 'index.html' if path=='/' or re.fullmatch(r'/projet/[a-z0-9-]+/?',path) else path.lstrip('/')
            if name not in STATIC:
                return self.respond(404, {'error':'Page introuvable.'})
            file = ROOT/name
        if not file.is_file():
            return self.respond(404, {'error':'Fichier introuvable.'})
        return self.respond(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'application/octet-stream')

    def do_POST(self):
        try:
            path = urlsplit(self.path).path
            if not self.same_origin():
                return self.respond(403, {'error':'Origine non autorisée.'})
            if path == '/api/login':
                key = self.client_address[0]
                recent = [t for t in ATTEMPTS.get(key,[]) if t > time.time()-300]
                ATTEMPTS[key] = recent
                if len(recent) >= 10:
                    return self.respond(429, {'error':'Trop de tentatives. Réessayez dans 5 minutes.'})
                password = json.loads(self.read_body()).get('password','')
                record = json.loads((DATA/'auth.json').read_text())
                valid = isinstance(password,str) and len(password)<=500 and hmac.compare_digest(hashlib.scrypt(password.encode(),salt=bytes.fromhex(record['salt']),n=16384,r=8,p=1).hex(),record['hash'])
                if not valid:
                    recent.append(time.time())
                    return self.respond(401, {'error':'Mot de passe incorrect.'})
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                for old_token in list(SESSIONS):
                    if SESSIONS[old_token]['expires'] <= time.time():
                        SESSIONS.pop(old_token,None)
                SESSIONS[token] = {'expires':time.time()+8*3600,'csrf':csrf}
                ATTEMPTS.pop(key,None)
                return self.respond(200, {'csrf':csrf}, extra={'Set-Cookie':f'portfolio_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if os.environ.get('PORTFOLIO_HTTPS')=='1' else '')})
            session = self.session()
            if not session:
                return self.respond(401, {'error':'Connexion requise.'})
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),session['csrf']):
                return self.respond(403, {'error':'Session invalide. Reconnectez-vous.'})
            if path == '/api/logout':
                cookie = SimpleCookie(self.headers.get('Cookie',''))
                SESSIONS.pop(cookie['portfolio_session'].value,None)
                return self.respond(200, {'ok':True}, extra={'Set-Cookie':'portfolio_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            if path == '/api/admin/content':
                value = json.loads(self.read_body())
                clean = validate(value)
                with LOCK:
                    old = json.loads((DATA/'content.json').read_text())
                    if value.get('revision') != old.get('revision'):
                        return self.respond(409, {'error':'Le contenu a changé dans une autre session. Exportez vos modifications puis rechargez avant de sauvegarder.'})
                    clean['revision'] = old.get('revision',0)+1
                    write_json(DATA/'content.backup.json',old)
                    write_json(DATA/'content.json',clean)
                return self.respond(200, clean)
            if path == '/api/admin/upload':
                raw = self.read_body()
                if raw.startswith(b'\x89PNG\r\n\x1a\n'): ext='png'
                elif raw.startswith(b'\xff\xd8\xff'): ext='jpg'
                elif raw[:6] in (b'GIF87a',b'GIF89a'): ext='gif'
                elif raw.startswith(b'RIFF') and raw[8:12]==b'WEBP': ext='webp'
                else: raise ValueError('Formats acceptés : PNG, JPEG, WebP ou GIF. Les SVG ne sont pas acceptés.')
                name = secrets.token_hex(16)+'.'+ext
                (DATA/'uploads'/name).write_bytes(raw)
                return self.respond(201, {'url':'/uploads/'+name})
            return self.respond(404, {'error':'Action introuvable.'})
        except (ValueError, TypeError, AttributeError, KeyError) as error:
            return self.respond(400, {'error':str(error) or 'Données invalides.'})
        except Exception:
            return self.respond(500, {'error':'Erreur de sauvegarde. Réessayez et vérifiez le serveur.'})

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--host',default='0.0.0.0')
    parser.add_argument('--set-password',action='store_true')
    args=parser.parse_args()
    initialize()
    if args.set_password:
        password=getpass.getpass('Nouveau mot de passe administrateur (12 caractères minimum) : ')
        if len(password)<12: parser.error('12 caractères minimum requis.')
        if password!=getpass.getpass('Confirmez le mot de passe : '): parser.error('Les mots de passe ne correspondent pas.')
        write_json(DATA/'auth.json',password_record(password))
        (DATA/'initial-password.txt').unlink(missing_ok=True)
        print('Mot de passe enregistré. Redémarrez le serveur pour fermer les anciennes sessions.')
    else:
        print(f'Portfolio démarré sur le port {args.port}. Administration : /admin',flush=True)
        ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
