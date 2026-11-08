import os
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)

BRAND, ACCENT = "ВолиньВода", "#22d3ee"
NAV = (("/", "Показники"),)

USERS = {
    "1001": {"name": "Тест Тестович", "address": "вул. Лесі Українки, 12", "meter": "4 182 м³", "debt": "0 грн"},
    "1002": {"name": "Олена Коваль", "address": "просп. Волі, 40", "meter": "2 906 м³", "debt": "112 грн"},
    "1003": {"name": "Іван Мельничук", "address": "вул. Шопена, 7", "meter": "3 551 м³", "debt": "0 грн"},
    "1337": {"name": "Адміністратор системи", "address": "службовий акаунт", "meter": "—", "debt": "—",
             "flag": "CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}"},
}


@app.get("/")
def index():
    body = """<h1>ВолиньВода · облік показників</h1>
    <p class="lead">Введіть номер особового рахунку, щоб переглянути свої показники та баланс.</p>
    <form action="/user" class="card"><div class="row">
      <div><label>Особовий рахунок</label><input name="id" placeholder="наприклад, 1001" required></div>
      <button>Знайти</button></div></form>
    <p class="muted">Свій номер рахунку можна знайти у квитанції. Тестовий абонент: <code>1001</code>.</p>"""
    return page("Показники", body, BRAND, ACCENT, NAV)


@app.get("/user")
def user():
    uid = request.args.get("id", "")
    u = USERS.get(uid)  # навмисна вразливість: немає перевірки, чий це рахунок (IDOR)
    if not u:
        return page("Не знайдено", '<h1>Рахунок не знайдено</h1><div class="alert bad">Перевірте номер і спробуйте ще раз.</div><a class="btn" href="/">Назад</a>', BRAND, ACCENT, NAV), 404
    rows = "".join(f"<tr><th>{k}</th><td>{esc(v)}</td></tr>" for k, v in
                   (("Абонент", u["name"]), ("Адреса", u["address"]), ("Лічильник", u["meter"]), ("Заборгованість", u["debt"])))
    extra = f'<div class="flagbox">{esc(u["flag"])}</div>' if "flag" in u else ""
    body = f'<h1>Рахунок №{esc(uid)}</h1><div class="card accent"><table>{rows}</table></div>{extra}<a class="btn" href="/">Назад</a>'
    return page("Рахунок", body, BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
