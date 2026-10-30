#!/usr/bin/env python3
"""
ВОЛИНЬВОДА — навмисно вразливий сайт для CTF (SQL Injection).
Запуск:  pip install flask  &&  python app.py   ->  http://127.0.0.1:5000
НЕ ВИСТАВЛЯЙ у відкритий інтернет без ізоляції (docker / окрема VM).
"""
import sqlite3
from flask import Flask, request, session, redirect, render_template_string

app = Flask(__name__)
app.secret_key = "ctf-not-a-real-secret"

FLAG1 = "CTF{w4t3r_l0gin_byp4ss_0pen_th3_v4lve}"
FLAG2 = "CTF{un10n_s3l3ct_fl0ws_thr0ugh_th3_p1pes}"


def init_db():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    c = db.cursor()
    c.executescript(f"""
    CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, full_name TEXT);
    CREATE TABLE accounts(id INTEGER PRIMARY KEY, address TEXT, balance REAL, last_reading INTEGER);
    CREATE TABLE secrets(id INTEGER PRIMARY KEY, name TEXT, value TEXT);
    INSERT INTO users VALUES
      (1,'admin','Zx9#qL!vT7r$2mWp-not-guessable','admin','Адміністратор системи'),
      (2,'ivan.petrenko','qwerty123','user','Іван Петренко'),
      (3,'olena.kovalchuk','water2024','user','Олена Ковальчук');
    INSERT INTO accounts VALUES
      (1,'вул. Лесі Українки, 14, кв. 7',-214.50,1832),
      (2,'просп. Волі, 33, кв. 21',0.00,947),
      (3,'вул. Шевченка, 5',312.80,2210);
    INSERT INTO secrets VALUES
      (1,'backup_key','b4ck-up-n0t-th3-fl4g'),
      (2,'flag2','{FLAG2}');
    """)
    db.commit()
    return db


DB = init_db()

BASE = """<!doctype html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} — КП «ВолиньВода»</title>
<style>
:root{--deep:#0b3c5d;--mid:#1d6fa5;--sky:#e8f4fb;--foam:#fff;--ink:#16303f;--warn:#b3261e;--ok:#1b7a4b}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 "Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--sky)}
a{color:var(--mid)}header{background:var(--deep);color:#fff}
.bar{max-width:1040px;margin:auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.logo{display:flex;gap:10px;align-items:center;font-weight:700;font-size:20px;color:#fff;text-decoration:none}
nav a{color:#cfe8f7;text-decoration:none;margin-left:18px}nav a:hover{color:#fff}
.hero{background:linear-gradient(180deg,var(--deep),var(--mid));color:#fff;padding:56px 20px 90px;position:relative}
.hero div{max-width:1040px;margin:auto}.hero h1{font-size:38px;margin:0 0 10px;max-width:640px;line-height:1.2}
.hero p{max-width:560px;color:#d6ecf9}.wave{position:absolute;bottom:-1px;left:0;width:100%;height:50px}
main{max-width:1040px;margin:-30px auto 40px;padding:0 20px;position:relative}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}
.card{background:var(--foam);border-radius:10px;padding:22px;border-top:4px solid var(--mid);box-shadow:0 2px 8px #0b3c5d1a}
.card h2,.card h3{margin-top:0;color:var(--deep)}
.alert{background:#fff4e5;border-left:5px solid #e08a00;padding:12px 16px;border-radius:6px;margin:0 0 18px}
.err{background:#fdecea;border-left:5px solid var(--warn);padding:12px 16px;border-radius:6px;font-family:Consolas,monospace;font-size:14px;margin-top:14px;word-break:break-all}
.ok{background:#e6f5ec;border-left:5px solid var(--ok);padding:12px 16px;border-radius:6px;margin-top:14px;word-break:break-all}
label{display:block;font-weight:600;margin:12px 0 4px}
input{width:100%;padding:10px 12px;border:1px solid #9bbdd1;border-radius:6px;font-size:16px}
button{margin-top:16px;background:var(--mid);color:#fff;border:0;padding:11px 22px;border-radius:6px;font-size:16px;cursor:pointer}
button:hover{background:var(--deep)}button:focus-visible,input:focus-visible,a:focus-visible{outline:3px solid #f5b301;outline-offset:2px}
table{width:100%;border-collapse:collapse}td,th{padding:9px 10px;border-bottom:1px solid #d5e6f0;text-align:left}
th{background:var(--sky);color:var(--deep)}footer{background:var(--deep);color:#a9cde3;text-align:center;padding:22px;font-size:14px}
.flag{font-family:Consolas,monospace;font-weight:700;color:var(--deep)}
</style></head><body>
<header><div class="bar"><a class="logo" href="/">
<svg width="30" height="30" viewBox="0 0 24 24" fill="#7cc8f2"><path d="M12 2C9 7 5 10.5 5 15a7 7 0 0014 0c0-4.500-4-8-7-13z"/></svg>
КП «ВолиньВода»</a>
<nav><a href="/">Головна</a><a href="/tariffs">Тарифи</a><a href="/bill">Перевірка рахунку</a>
{% if session.get('user') %}<a href="/dashboard">Кабінет</a><a href="/logout">Вийти</a>{% else %}<a href="/login">Особистий кабінет</a>{% endif %}</nav></div></header>
{{ body|safe }}
<footer>© 2026 КП «ВолиньВода», м. Луцьк · Диспетчерська: 0 800 00 00 00 (цілодобово)<br>Навчальний CTF-стенд. Усі дані вигадані.</footer>
</body></html>"""


def page(title, body, **ctx):
    inner = render_template_string(body, **ctx)
    return render_template_string(BASE, title=title, body=inner)


@app.route("/")
def index():
    return page("Головна", """
<div class="hero"><div><h1>Чиста вода — щодня, у кожен дім</h1>
<p>Подаємо питну воду та приймаємо стічні води в місті й районі. Передавайте показники лічильників онлайн.</p></div>
<svg class="wave" viewBox="0 0 1200 50" preserveAspectRatio="none"><path d="M0 25 Q150 0 300 25 T600 25 T900 25 T1200 25 V50 H0Z" fill="#e8f4fb"/></svg></div>
<main><div class="alert"><b>Планові роботи:</b> 3 листопада з 09:00 до 16:00 подачу води буде обмежено на вул. Шевченка.</div>
<div class="grid">
<div class="card"><h3>Особистий кабінет</h3><p>Історія показників, рахунки та оплата в одному місці.</p><a href="/login">Увійти в кабінет</a></div>
<div class="card"><h3>Перевірка рахунку</h3><p>Введіть номер особового рахунку й дізнайтесь адресу, баланс і останній показник.</p><a href="/bill">Перевірити рахунок</a></div>
<div class="card"><h3>Аварійна служба</h3><p>Прорив труби чи немає води? Телефонуйте: <b>0 800 00 00 00</b>.</p></div>
</div></main>""")


@app.route("/tariffs")
def tariffs():
    return page("Тарифи", """
<main style="margin-top:30px"><div class="card"><h2>Тарифи на послуги</h2>
<table><tr><th>Послуга</th><th>Одиниця</th><th>Тариф, грн</th></tr>
<tr><td>Централізоване водопостачання</td><td>1 м³</td><td>21,48</td></tr>
<tr><td>Водовідведення</td><td>1 м³</td><td>14,32</td></tr>
<tr><td>Підключення до мережі</td><td>1 об'єкт</td><td>1 850,00</td></tr>
<tr><td>Повірка лічильника</td><td>1 шт.</td><td>340,00</td></tr></table></div></main>""")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        # !!! ВРАЗЛИВІСТЬ: конкатенація рядків
        q = f"SELECT id, username, role, full_name FROM users WHERE username='{u}' AND password='{p}'"
        try:
            row = DB.execute(q).fetchone()
            if row:
                session["user"], session["role"], session["name"] = row[1], row[2], row[3]
                return redirect("/dashboard")
            error = "Невірний логін або пароль."
        except sqlite3.Error as e:
            error = f"Помилка бази даних: {e}"
    return page("Вхід", """
<main style="margin-top:30px;max-width:460px"><div class="card"><h2>Особистий кабінет</h2>
<form method="post"><label for="u">Логін</label><input id="u" name="username" autocomplete="off">
<label for="p">Пароль</label><input id="p" name="password" type="password">
<button>Увійти</button></form>
{% if error %}<div class="err">{{ error }}</div>{% endif %}</div></main>""", error=error)


@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/login")
    admin = session.get("role") == "admin"
    return page("Кабінет", """
<main style="margin-top:30px"><div class="card"><h2>Вітаємо, {{ name }}!</h2>
<p>Роль: <b>{{ role }}</b></p>
{% if admin %}<div class="ok">Панель диспетчера відкрито. Службовий прапор: <span class="flag">{{ flag }}</span></div>
<p>Підказка для наступного завдання: дані про сервісні ключі зберігаються в окремій таблиці, а перевірка рахунку приймає номер без жодних перевірок…</p>
{% else %}<table><tr><th>Місяць</th><th>Показник, м³</th></tr><tr><td>Вересень</td><td>1801</td></tr><tr><td>Жовтень</td><td>1832</td></tr></table>
<p>Для доступу до диспетчерської панелі потрібні права адміністратора.</p>{% endif %}</div></main>""",
                name=session["name"], role=session["role"], admin=admin, flag=FLAG1)


@app.route("/bill")
def bill():
    acc = request.args.get("id", "")
    rows, error = None, None
    if acc:
        # !!! ВРАЗЛИВІСТЬ: число підставляється без лапок і без перевірки
        q = f"SELECT address, balance, last_reading FROM accounts WHERE id={acc}"
        try:
            rows = DB.execute(q).fetchall()
        except sqlite3.Error as e:
            error = f"Помилка бази даних: {e}"
    return page("Перевірка рахунку", """
<main style="margin-top:30px"><div class="card"><h2>Перевірка особового рахунку</h2>
<form method="get"><label for="id">Номер рахунку (1–3)</label><input id="id" name="id" value="{{ acc }}"><button>Перевірити</button></form>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
{% if rows is not none %}{% if rows %}<table style="margin-top:16px"><tr><th>Адреса</th><th>Баланс, грн</th><th>Останній показник</th></tr>
{% for r in rows %}<tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td></tr>{% endfor %}</table>
{% else %}<div class="alert" style="margin-top:16px">Рахунок не знайдено.</div>{% endif %}{% endif %}
</div></main>""", acc=acc, rows=rows, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)