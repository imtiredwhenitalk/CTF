from http.server import SimpleHTTPRequestHandler, HTTPServer
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Target 9</h1><a href='image.png'>Download Image</a> (Hint: use binwalk/unzip. Password is 'titan')")
        else: super().do_GET()
HTTPServer(('', 80), Handler).serve_forever()
