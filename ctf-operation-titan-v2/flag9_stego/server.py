import functools, html, os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, "titan.css"), encoding="utf-8").read()
LOGO = ('<svg viewBox="0 0 32 32" fill="none"><path d="M16 2 28 9v14L16 30 4 23V9z" stroke="#86b4d8" stroke-width="2"/>'
        '<path d="M10 12h12M16 12v11" stroke="#ff7a3d" stroke-width="2.4" stroke-linecap="square"/></svg>')

PAGE = f'''<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Archive Node · Operation Titan</title>
<style>{CSS}</style></head><body>
<header class="topbar"><div class="in"><a class="brand" href="/">{LOGO}<span>Operation Titan</span></a>
<span class="node"><span class="dot"></span>titan-node-09 · archive</span></div></header>
<main class="wrap">
<section class="hero"><span class="tag">09 · Forensics</span><h1>Titan Archive Node</h1>
<p>Сховище зашифрованих активів. Один файл виглядає надто великим для свого вмісту.</p></section>
<div class="grid">
 <div class="card"><div class="hd">Актив<span class="sub">image.png</span></div><div class="bd">
   <img class="px" src="image.png" alt="encrypted asset preview">
   <div class="row" style="margin-top:1rem"><a class="btn primary" href="image.png" download>Завантажити актив</a></div></div></div>
 <div class="card"><div class="hd">Нотатка архіваріуса</div><div class="bd">
   <div class="alert info">Пароль до вкладення: <code>titan</code></div>
   <p class="muted">Зображення — лише контейнер. Подивіться, що лежить після його кінця.</p></div></div>
</div></main></body></html>'''.encode("utf-8")


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


# only /app/public is exposed (secret.txt / server.py / titan.css are not reachable)
handler = functools.partial(Handler, directory='/app/public')
ThreadingHTTPServer(('', 80), handler).serve_forever()
