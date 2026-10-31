import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE products (id INTEGER, name TEXT, description TEXT, price REAL)')
    c.execute('CREATE TABLE secrets (id INTEGER, flag TEXT)')
    
    c.execute("INSERT INTO products VALUES (1, 'Затвор механічний Z-100', 'Промисловий клапан високого тиску', 1500.0)")
    c.execute("INSERT INTO products VALUES (2, 'Дросель регулюючий D-50', 'Автоматичний регулятор потоку', 2300.0)")
    c.execute("INSERT INTO secrets VALUES (1, 'CTF{z4tv0r_sqli_byp4ss_m4st3r}')")
    conn.commit()
    return conn

conn = init_db()

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Магазин Затвор - Пошук обладнання</title>
    <style>
        body { font-family: monospace; background: #09090b; color: #22c55e; padding: 40px; }
        .box { max-width: 700px; margin: auto; background: #18181b; padding: 30px; border: 1px solid #22c55e; border-radius: 6px; }
        input, button { padding: 10px; font-family: monospace; background: #000; color: #22c55e; border: 1px solid #22c55e; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #22c55e; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🛠️ ТОВ «Затвор-СпецМаш» — Пошуковий Каталог</h2>
        <form method="GET" action="/search">
            <input type="text" name="q" placeholder="Назва товару..." style="width: 70%;">
            <button type="submit">Шукати</button>
        </form>
        {% if results %}
        <table>
            <tr><th>ID</th><th>Назва</th><th>Опис</th><th>Ціна</th></tr>
            {% for r in results %}
            <tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td><td>{{ r[3] }}</td></tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    c = conn.cursor()
    # Vulnerable SQL Injection
    raw_sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    try:
        c.execute(raw_sql)
        results = c.fetchall()
    except Exception as e:
        results = [(0, "Error", str(e), 0)]
    return render_template_string(HTML, results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
