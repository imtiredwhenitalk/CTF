import os
from flask import Flask, request, render_template_string
from ui import page, setup

app = Flask(__name__)
app.config["SECRET_FLAG"] = "CTF{v0lyn_g4s_sst1_3xpl01t_2026}"
setup(app)

BRAND, ACCENT = "ВолиньГаз", "#fb923c"
NAV = (("/", "Головна"), ("/request", "Подати заяву"), ("/status", "Стан мережі"), ("/admin", "Кабінет оператора"))


@app.get("/")
def index():
    body = """
    <h1>ВолиньГаз · онлайн-кабінет абонента</h1>
    <p class="lead">Передавайте показники лічильника, подавайте заяви на підключення та відстежуйте їх статус.</p>
    <div class="grid">
      <div class="card accent"><h3>🔥 Подати заяву</h3><p class="muted">Підключення, переоформлення, звірка показників.</p><a class="btn" href="/request">Створити заяву</a></div>
      <div class="card"><h3>📡 Стан мережі</h3><p class="muted">Планові роботи та аварійні відключення.</p><a href="/status">Переглянути</a></div>
      <div class="card"><h3>🔒 Кабінет оператора</h3><p class="muted">Лише для працівників ВолиньГаз.</p><a href="/admin">Увійти</a></div>
    </div>"""
    return page("Головна", body, BRAND, ACCENT, NAV)


@app.get("/status")
def status():
    body = """<h1>Стан мережі</h1><table><tr><th>Район</th><th>Статус</th></tr>
    <tr><td>Луцьк, центр</td><td><span class="badge ok">працює</span></td></tr>
    <tr><td>Ківерці</td><td><span class="badge ok">працює</span></td></tr>
    <tr><td>Нововолинськ</td><td><span class="badge bad">планові роботи</span></td></tr></table>"""
    return page("Стан мережі", body, BRAND, ACCENT, NAV)


@app.route("/request", methods=["GET", "POST"])
def submit_request():
    if request.method == "POST":
        name = request.form.get("name", "")
        account = request.form.get("account", "")
        note = request.form.get("note", "")
        # УВАГА (навмисна вразливість): дані користувача підставляються прямо в шаблон
        body = (
            f'<h1>Заяву №{account} прийнято</h1>'
            f'<p class="lead">Шановний(-а) <b>{name}</b>, ваша примітка збережена:</p>'
            f'<div class="card accent">{note}</div>'
            '<p><a class="btn" href="/">На головну</a></p>'
        )
        return render_template_string(page("Заяву прийнято", body, BRAND, ACCENT, NAV))
    body = """<h1>Нова заява</h1><p class="lead">Заповніть форму — оператор зв'яжеться з вами протягом доби.</p>
    <form method="POST" class="card">
      <label>Ім'я та прізвище</label><input name="name" required>
      <label>Особовий рахунок</label><input name="account" required>
      <label>Примітка</label><textarea name="note"></textarea>
      <button>Надіслати</button></form>"""
    return page("Нова заява", body, BRAND, ACCENT, NAV)


@app.get("/admin")
def admin():
    body = """<h1>Кабінет оператора</h1><div class="alert bad">403 · Доступ дозволено лише з внутрішньої мережі ВолиньГаз.
    Секрет змінної оточення <code>SECRET_FLAG</code> тут не відображається.</div>"""
    return page("Доступ заборонено", body, BRAND, ACCENT, NAV), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
