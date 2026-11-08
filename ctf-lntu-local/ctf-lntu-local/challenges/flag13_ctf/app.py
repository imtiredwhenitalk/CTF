import os
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Intranet ЛНТУ", "#818cf8"
NAV = (("/", "Портал"),)
FLAG = "CTF{h34d3rs_4r3_us3r_c0ntr0ll3d}"


def deny(title, text):
    return page("403", f'<h1>403 · {title}</h1><div class="alert bad">{text}</div>', BRAND, ACCENT, NAV), 403


@app.get("/")
def index():
    xff = request.headers.get("X-Forwarded-For", "")
    ua = request.headers.get("User-Agent", "")
    ref = request.headers.get("Referer", "")
    if not xff.strip().startswith("10."):
        return deny("Доступ лише з внутрішньої мережі",
                    f"Ваша адреса за версією балансувальника: <code>{esc(xff or request.remote_addr)}</code>. Дозволено лише підмережу <code>10.0.0.0/8</code>.")
    if "LNTU-Staff" not in ua:
        return deny("Непідтримуваний клієнт", "Портал відкривається лише у корпоративному браузері <code>LNTU-Staff</code>.")
    if not ref.startswith("http://intranet.lntu.local"):
        return deny("Невідоме джерело переходу", "Відкривайте сторінку лише з головного порталу <code>http://intranet.lntu.local</code>.")
    return page("Портал", f'<h1>Службовий портал</h1><div class="alert ok">Усі перевірки пройдено. Ласкаво просимо, співробітнику!</div><div class="flagbox">{esc(FLAG)}</div>', BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
