import os
import sqlite3
from flask import Flask, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Затвор", "#f43f5e"
NAV = (("/", "Каталог"),)

conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.execute("CREATE TABLE products (id INTEGER, name TEXT, price INTEGER)")
conn.executemany("INSERT INTO products VALUES (?,?,?)", [
    (1, "Затвор ZT-1 (кріплення)", 450), (2, "Затвор ZT-2 (посилений)", 780),
    (3, "Пружина відкату", 120), (4, "Набір для чищення", 260)])
conn.execute("CREATE TABLE secrets (id INTEGER, flag TEXT)")
conn.execute("INSERT INTO secrets VALUES (1, 'CTF{z4tv0r_sqli_byp4ss_m4st3r}')")
conn.commit()


@app.get("/")
def search():
    q = request.args.get("q", "")
    msg, rows = "", ""
    if q:
        try:
            # навмисна вразливість: SQL-ін'єкція через конкатенацію
            res = conn.execute(f"SELECT id, name, price FROM products WHERE name LIKE '%{q}%'").fetchall()
            rows = "".join(f"<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td>{esc(r[2])} грн</td></tr>" for r in res)
            if not res:
                msg = '<div class="alert warn">Нічого не знайдено.</div>'
        except Exception as e:
            msg = f'<div class="alert bad">Помилка БД: <code>{esc(e)}</code></div>'
    else:
        res = conn.execute("SELECT id, name, price FROM products").fetchall()
        rows = "".join(f"<tr><td>{r[0]}</td><td>{esc(r[1])}</td><td>{r[2]} грн</td></tr>" for r in res)
    body = f"""<h1>Затвор · магазин комплектуючих</h1>
    <p class="lead">Пошук по каталогу. Усі товари — навчальні макети.</p>
    <form class="card"><div class="row"><div><label>Пошук</label><input name="q" value="{esc(q)}" placeholder="назва товару"></div><button>Шукати</button></div></form>
    {msg}<table><tr><th>ID</th><th>Назва</th><th>Ціна</th></tr>{rows}</table>"""
    return page("Каталог", body, BRAND, ACCENT, NAV)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
