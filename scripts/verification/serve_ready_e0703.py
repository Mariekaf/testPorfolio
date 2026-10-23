"""Serve ONLY an exporter-created synthetic preview directory, on loopback."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path


def server_for(directory, port=0):
    original = Path(directory)
    assert not original.is_symlink(), 'Symlink preview root refused.'
    directory = original.resolve()
    allowed = {'index.html', 'studio-a.html', 'studio-b.html', 'empty-draft.html', 'paper-serif.html'}
    assert all((directory/name).is_file() for name in allowed), 'Use a fresh exported preview directory.'
    assert not directory.is_symlink() and not (directory/'.git').exists(), 'Repository serving is forbidden.'
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlsplit
            path = urlsplit(self.path).path
            valid = path in ('/', '/index.html', '/studio-a.html', '/studio-b.html', '/empty-draft.html', '/paper-serif.html') or path in {'/__ready_assets/'+name+'.svg' for name in ('portrait-a','portrait-b','project-a','project-b','project-c','project-d','logo-a','logo-b')}
            if not valid:
                self.send_error(404)
                return
            target = directory/('index.html' if path == '/' else path.lstrip('/'))
            if target.is_symlink() or target.parent.is_symlink() or not target.resolve().is_relative_to(directory):
                self.send_error(403)
                return
            super().do_GET()

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; object-src 'none'; form-action 'none'; frame-ancestors 'none'")
            super().end_headers()
    return ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(directory)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, default=3017)
    args = parser.parse_args()
    with server_for(args.directory, args.port) as server:
        print(f'Synthetic preview only: http://127.0.0.1:{server.server_port} — Ctrl+C to stop', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
