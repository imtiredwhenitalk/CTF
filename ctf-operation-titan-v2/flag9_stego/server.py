import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PAGE = b'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Titan Archive Node</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5 text-center">
<h1>Titan Archive Node</h1>
<a href="image.png" class="btn btn-primary mt-3">Download Encrypted Asset</a>
<p class="mt-3 text-muted">Password hint: titan</p>
</div></body></html>'''

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(PAGE)))
            self.end_headers()
            self.wfile.write(PAGE)
        else:
            super().do_GET()          # serves ONLY files from /app/public

# only /app/public is exposed (secret.txt / server.py are not reachable)
handler = functools.partial(Handler, directory='/app/public')
ThreadingHTTPServer(('', 80), handler).serve_forever()
