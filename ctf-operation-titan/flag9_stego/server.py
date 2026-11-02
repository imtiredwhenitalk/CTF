from http.server import SimpleHTTPRequestHandler, HTTPServer
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''
            <!DOCTYPE html><html lang="en"><head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
            <body class="bg-dark text-light"><div class="container mt-5 text-center">
            <h1>Titan Archive Node</h1>
            <a href="image.png" class="btn btn-primary mt-3">Download Encrypted Asset</a>
            <p class="mt-3 text-muted">Password hint: titan</p>
            </div></body></html>
            '''
            self.wfile.write(html.encode())
        else: super().do_GET()
HTTPServer(('', 80), Handler).serve_forever()
