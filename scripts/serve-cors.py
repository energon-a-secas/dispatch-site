#!/usr/bin/env python3
"""Static file server with CORS for local hub ↔ feed testing.

The hub's corner popup (neorgon-site/js/dispatch-popup.js) fetches
data/posts.json cross-origin. GitHub Pages sends Access-Control-Allow-Origin
in production; plain http.server does not, so localhost needs this instead.
Same pattern as awesome-sites-site/scripts/serve-cors.py.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os

PORT = int(os.environ.get('PORT', '8873'))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Dev loop serves drafts and freshly edited modules; heuristic
        # caching of either turns every edit into a ghost hunt.
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


if __name__ == '__main__':
    # Loopback only: this server exposes data/drafts/, which is unapproved
    # and deliberately uncommitted. Binding 0.0.0.0 would hand every device
    # on the LAN the drafts plus a wildcard CORS header.
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'Serving {ROOT} → http://localhost:{PORT} (CORS enabled, loopback only)')
    server.serve_forever()
