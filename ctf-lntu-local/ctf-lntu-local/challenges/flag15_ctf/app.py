import os
import threading
from urllib.parse import urlparse
import requests
from flask import Flask, request
from werkzeug.serving import make_server
from ui import page, setup, esc

FLAG = "CTF{ssrf_1nt3rn4l_s3rv1c3_r34ch3d}"
INTERNAL_PORT = int(os.environ.get("INTERNAL_PORT", 9000))

# ---- внутрішня служба метаданих (слухає лише 127.0.0.1) ----
internal = Flask("internal")


@internal.get("/")
def i_index():
    return "LNTU internal metadata service\nendpoints: /internal/flag\n", 200, {"Content-Type": "text/plain"}


@internal.get("/internal/flag")
def i_flag():
    return FLAG + "\n", 200, {"Content-Type": "text/plain"}


def run_internal():
    make_server("127.0.0.1", INTERNAL_PORT, internal, threaded=True).serve_forever()


# ---- публічний сайт ----
app = Flask(__name__)
setup(app)
BRAND, ACCENT = "LNTU LinkPreview", "#38bdf8"
NAV = (("/", "Прев'ю посилань"),)
BLOCKED_HOSTS = {"localhost", "127.0.0.1"}


@app.get("/")
def index():
    url = request.args.get("url", "")
    result = ""
    if url:
        u = urlparse(url)
        host = (u.hostname or "").lower()
        if u.scheme not in ("http", "https"):
            result = '<div class="alert bad">Дозволені лише http/https.</div>'
        elif host in BLOCKED_HOSTS:
            result = '<div class="alert bad">Доступ до внутрішніх адрес заборонено.</div>'
        else:
            try:  # навмисна вразливість: SSRF з поверхневим фільтром
                r = requests.get(url, timeout=4)
                result = f'<h2>Відповідь · HTTP {r.status_code}</h2><pre>{esc(r.text[:2000])}</pre>'
            except Exception as e:
                result = f'<div class="alert bad">Не вдалося завантажити: <code>{esc(type(e).__name__)}</code></div>'
    body = f"""<h1>Прев'ю посилань</h1>
    <p class="lead">Вставте URL — сервіс завантажить сторінку та покаже її вміст для попереднього перегляду.</p>
    <form class="card accent"><div class="row"><div><label>URL</label>
    <input name="url" value="{esc(url)}" placeholder="https://example.com"></div><button>Завантажити</button></div></form>
    <p class="muted">У внутрішній мережі працює служба метаданих на порту <code>{INTERNAL_PORT}</code> (шлях <code>/internal/flag</code>).</p>{result}"""
    return page("Прев'ю", body, BRAND, ACCENT, NAV)


if __name__ == "__main__":
    threading.Thread(target=run_internal, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
