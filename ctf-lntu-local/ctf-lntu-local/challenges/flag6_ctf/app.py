import os
from flask import Flask, send_from_directory
from ui import page, setup

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Autumn Archive", "#f59e0b"
NAV = (("/", "Архів"),)


@app.get("/")
def index():
    body = """<h1>Autumn Archive · загублений польовий звіт</h1>
    <p class="lead">Волонтер публікував польові нотатки під публічним псевдонімом <b>autumn_fox</b>.</p>
    <div class="card accent">
      <p>Оригінальний допис видалено, але відновлений артефакт з камери ще доступний:</p>
      <p><a class="btn" href="/evidence.png">⬇ evidence.png</a></p>
    </div>
    <h2>Що відомо</h2>
    <table><tr><th>Зачіпка</th><th>Значення</th></tr>
    <tr><td>Псевдонім</td><td><code>autumn_fox</code></td></tr>
    <tr><td>Дата зйомки</td><td><code>2026-10-17</code></td></tr>
    <tr><td>Джерело</td><td><code>field-camera-2026-10-17</code></td></tr></table>
    <p class="muted">Дослідіть метадані файлу та дані, що йдуть <i>після</i> завершення зображення.</p>"""
    return page("Архів", body, BRAND, ACCENT, NAV)


@app.get("/evidence.png")
def evidence():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "evidence.png", mimetype="image/png")


@app.get("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /internal/\n", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
