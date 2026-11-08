import os
from pathlib import Path
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Е-Архів ЛНТУ", "#c084fc"
NAV = (("/", "Документи"),)
FLAG = "CTF{p4th_tr4v3rs4l_n0t_s0_s4f3}"
DOCS = Path(__file__).resolve().parent / "docs"
FLAG_FILE = Path(os.environ.get("FLAG_FILE", "/etc/lntu/flag.txt"))
try:
    FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
    FLAG_FILE.write_text(FLAG + "\n")
except OSError as e:
    print("[warn] не вдалося записати прапор:", e, flush=True)


@app.get("/")
def index():
    items = "".join(f'<tr><td>📄 {f.name}</td><td><a href="/view?file={f.name}">Відкрити</a></td></tr>'
                    for f in sorted(DOCS.glob("*.txt")))
    body = f"""<h1>Електронний архів документів</h1>
    <p class="lead">Публічні документи кафедри. Файли відкриваються у браузері.</p>
    <table><tr><th>Файл</th><th></th></tr>{items}</table>"""
    return page("Документи", body, BRAND, ACCENT, NAV)


@app.get("/view")
def view():
    name = request.args.get("file", "")
    name = name.replace("../", "")  # «захист» від обходу каталогів — спрацьовує лише один раз
    try:
        text = open(os.path.join(DOCS, name), encoding="utf-8", errors="replace").read()
    except Exception:
        return page("Помилка", '<h1>Файл не знайдено</h1><div class="alert bad">Такого документа немає в архіві.</div><a class="btn" href="/">Назад</a>', BRAND, ACCENT, NAV), 404
    return page("Перегляд", f'<h1>{esc(name)}</h1><pre>{esc(text)}</pre><a class="btn" href="/">Назад</a>', BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
