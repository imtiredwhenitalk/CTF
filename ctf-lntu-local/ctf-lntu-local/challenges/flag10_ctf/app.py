import os
import subprocess
from pathlib import Path
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "LNTU NOC", "#4ade80"
NAV = (("/", "Діагностика"),)
FLAG = "CTF{c0mm4nd_1nj3ct10n_p1p3_th3_fl4g}"
try:
    Path(os.environ.get("FLAG_FILE", "/flag.txt")).write_text(FLAG + "\n")
except OSError as e:
    print("[warn] не вдалося записати прапор:", e, flush=True)
BLACKLIST = [";", "&", "`", "\n", "\r"]


@app.get("/")
def index():
    host = request.args.get("host", "")
    result = ""
    if host:
        if any(b in host for b in BLACKLIST):
            result = '<div class="alert bad">Заборонені символи у адресі вузла.</div>'
        else:
            # навмисна вразливість: shell=True та неповний фільтр
            p = subprocess.run(f"ping -c 1 -W 1 {host}", shell=True, capture_output=True, text=True, timeout=10)
            result = f"<h2>Результат</h2><pre>{esc(p.stdout + p.stderr)}</pre>"
    body = f"""<h1>Мережева діагностика</h1>
    <p class="lead">Інструмент персоналу NOC: перевірка доступності вузла (ping).</p>
    <form class="card accent"><div class="row"><div><label>IP-адреса або домен</label>
    <input name="host" value="{esc(host)}" placeholder="8.8.8.8"></div><button>Ping</button></div></form>{result}"""
    return page("Діагностика", body, BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
