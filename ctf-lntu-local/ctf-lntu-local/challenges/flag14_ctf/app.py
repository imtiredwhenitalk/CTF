import os
from flask import Flask, send_from_directory
from ui import page, setup

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Фотоархів ЛНТУ", "#fb7185"
NAV = (("/", "Фото"),)


@app.get("/")
def index():
    body = """<h1>Фотоархів · осінь 2026</h1>
    <p class="lead">Фото кампусу з осінньої фотосесії. Здається, куратор архіву залишив у файлі щось зайве…</p>
    <div class="card accent center"><img src="/photo.png" alt="осінь" style="max-width:100%;border-radius:10px">
    <p><a class="btn" href="/photo.png" download>⬇ Завантажити оригінал</a></p></div>
    <p class="muted">Підказка: іноді дані ховають у наймолодших бітах пікселів. Спробуйте <code>zsteg</code>, StegSolve або Python + Pillow.</p>"""
    return page("Фото", body, BRAND, ACCENT, NAV)


@app.get("/photo.png")
def photo():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "photo.png", mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
