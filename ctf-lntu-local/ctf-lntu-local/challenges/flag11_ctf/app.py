import os
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "ВолиньОбленерго", "#facc15"
NAV = (("/", "Головна"), ("/admin/login", "Вхід для персоналу"))
FLAG = "CTF{r0b0ts_txt_l34ks_b4ckups}"
BACKUP = """# site_config.old — резервна копія конфігурації (НЕ ВИДАЛЯТИ ПЕРЕД МІГРАЦІЄЮ)
db_host=10.0.5.12
db_name=oblenergo
admin_user=svc_admin
admin_pass=Ob1energo#2026
"""


@app.get("/")
def index():
    body = """<h1>ВолиньОбленерго</h1><p class="lead">Графіки відключень, оплата та звернення абонентів.</p>
    <div class="grid"><div class="card"><h3>⚡ Графіки відключень</h3><p class="muted">Оновлюються щодня о 18:00.</p></div>
    <div class="card"><h3>💳 Оплата</h3><p class="muted">Онлайн-оплата тимчасово недоступна.</p></div>
    <div class="card"><h3>📞 Контакти</h3><p class="muted">Гаряча лінія: 0 800 000 000</p></div></div>"""
    return page("Головна", body, BRAND, ACCENT, NAV)


@app.get("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin/\nDisallow: /backup/\n", 200, {"Content-Type": "text/plain"}


@app.get("/backup/")
def backup_index():
    body = """<h1>Index of /backup/</h1><table><tr><th>Ім'я</th><th>Розмір</th></tr>
    <tr><td><a href="/backup/site_config.old">site_config.old</a></td><td>162 B</td></tr></table>"""
    return page("Index of /backup/", body, BRAND, ACCENT, NAV)


@app.get("/backup/site_config.old")
def backup_file():
    return BACKUP, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    msg = ""
    if request.method == "POST":
        if request.form.get("username") == "svc_admin" and request.form.get("password") == "Ob1energo#2026":
            return page("Панель", f'<h1>Панель адміністратора</h1><div class="alert ok">Вхід виконано.</div><div class="flagbox">{esc(FLAG)}</div>', BRAND, ACCENT, NAV)
        msg = '<div class="alert bad">Невірні облікові дані.</div>'
    body = f"""<h1>Вхід для персоналу</h1>{msg}<form method="POST" class="card accent" style="max-width:420px">
    <label>Логін</label><input name="username" required><label>Пароль</label>
    <input name="password" type="password" required><button>Увійти</button></form>"""
    return page("Вхід", body, BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
