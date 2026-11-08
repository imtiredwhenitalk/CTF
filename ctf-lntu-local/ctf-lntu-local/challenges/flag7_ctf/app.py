import base64
import json
import os
from flask import Flask, request, redirect, make_response
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Деканат ЛНТУ", "#60a5fa"
NAV = (("/", "Вхід"), ("/dashboard", "Кабінет"), ("/admin", "Адмін-панель"))
FLAG = "CTF{c00k13_r0l3_t4mp3r1ng_l4nds_4dm1n}"
USERS = {"student": "student123"}


def b64e(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")


def b64d(s):
    return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))


def current():
    raw = request.cookies.get("session_data")
    if not raw:
        return None
    try:
        return b64d(raw)  # навмисна вразливість: кука не підписана
    except Exception:
        return None


@app.route("/", methods=["GET", "POST"])
def login():
    err = ""
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        if USERS.get(u) == p:
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie("session_data", b64e({"user": u, "role": "student"}))
            return resp
        err = '<div class="alert bad">Невірний логін або пароль.</div>'
    body = f"""<h1>Кабінет студента</h1><p class="lead">Оцінки, розклад та заяви до деканату.</p>{err}
    <form method="POST" class="card accent" style="max-width:420px">
      <label>Логін</label><input name="username" required>
      <label>Пароль</label><input name="password" type="password" required>
      <button>Увійти</button></form>
    <p class="muted">Демо-доступ для перегляду: <code>student</code> / <code>student123</code></p>"""
    return page("Вхід", body, BRAND, ACCENT, NAV)


@app.get("/dashboard")
def dashboard():
    s = current()
    if not s:
        return redirect("/")
    body = f"""<h1>Вітаємо, {esc(s.get('user'))}!</h1>
    <div class="grid"><div class="card"><h3>Роль</h3><span class="badge">{esc(s.get('role'))}</span></div>
    <div class="card"><h3>Середній бал</h3><p>4.6</p></div><div class="card"><h3>Заяви</h3><p>Активних: 0</p></div></div>"""
    return page("Кабінет", body, BRAND, ACCENT, NAV)


@app.get("/admin")
def admin():
    s = current()
    if not s:
        return redirect("/")
    if s.get("role") != "admin":
        return page("Заборонено", '<h1>403</h1><div class="alert bad">Ця сторінка лише для адміністраторів деканату.</div>', BRAND, ACCENT, NAV), 403
    return page("Адмін", f'<h1>Адмін-панель</h1><div class="alert ok">Доступ підтверджено.</div><div class="flagbox">{esc(FLAG)}</div>', BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
