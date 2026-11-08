import base64
import codecs
import os
from flask import Flask
from ui import page, setup

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "SIGINT-клуб ЛНТУ", "#f472b6"
NAV = (("/", "Перехоплення"),)
FLAG = "CTF{l4y3r3d_3nc0d1ng_1s_n0t_3ncrypt10n}"
# прапор → ROT13 → Base64 → HEX
CIPHER = base64.b64encode(codecs.encode(FLAG, "rot13").encode()).hex()


@app.get("/")
def index():
    body = f"""<h1>Перехоплене повідомлення</h1>
    <p class="lead">Радіоклуб перехопив повідомлення. Відправник «захистив» його кількома шарами кодування.</p>
    <div class="card accent"><label>Перехоплено 2026-10-21 · канал 7</label><pre>{CIPHER}</pre></div>
    <div class="alert warn">Відомо: у повідомленні використано <b>HEX</b>, <b>Base64</b> та <b>ROT13</b> — порядок невідомий.
    Відповідь має формат <code>CTF{{...}}</code>.</div>
    <p class="muted">Сирий текст: <a href="/message.txt">/message.txt</a></p>"""
    return page("Перехоплення", body, BRAND, ACCENT, NAV)


@app.get("/message.txt")
def raw():
    return CIPHER + "\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
