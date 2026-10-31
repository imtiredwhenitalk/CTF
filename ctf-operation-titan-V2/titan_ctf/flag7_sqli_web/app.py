import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>ТИТАН ЕНЕРГО - Довідник співробітників</title>
    <style>
        body { font-family: monospace; background: #0f172a; color: #38bdf8; padding: 40px; }
        .card { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 8px; }
        input { background: #0f172a; color: #38bdf8; border: 1px solid #334155; padding: 6px; width: 300px; }
        button { background: #334155; color: #38bdf8; border: none; padding: 7px 14px; cursor: pointer; }
        td, th { border-bottom: 1px solid #334155; padding: 6px 14px; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <h1>[+] ВНУТРІШНІЙ ДОВІДНИК "ТИТАН"</h1>
        <p>Пошук співробітника за прізвищем:</p>
        <form method="GET" action="/search">
            <input type="text" name="q" value="{{ q }}" placeholder="Напр. Коваленко">
            <button type="submit">Знайти</button>
        </form>
        {% if error %}<p style="color:#f87171;">[!] Помилка БД: {{ error }}</p>{% endif %}
        {% if rows is not none %}
        <table>
            <tr><th>ID</th><th>Прізвище</th><th>Відділ</th></tr>
            {% for r in rows %}<tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td></tr>{% endfor %}
        </table>
        {% endif %}
        <!-- DEV NOTE: TODO перенести таблицю vault в окрему БД перед релізом -->
    </div>
</body>
</html>
'''


def init_db():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    c = db.cursor()
    c.execute("CREATE TABLE employees (id INTEGER, name TEXT, department TEXT)")
    c.executemany("INSERT INTO employees VALUES (?, ?, ?)", [
        (1, "Коваленко", "Диспетчерська"),
        (2, "Шевченко", "ІТ-безпека"),
        (3, "Бондаренко", "Підстанція №4"),
        (4, "Мельник", "Бухгалтерія"),
    ])
    c.execute("CREATE TABLE vault (id INTEGER, title TEXT, secret TEXT)")
    c.execute("INSERT INTO vault VALUES (1, 'backup_token', 'CTF{un10n_s3l3ct_dr41ns_th3_v4ult_7731}')")
    db.commit()
    return db


DB = init_db()


@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML, q="", rows=None, error=None)


@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q', '')
    # Vulnerable: string concatenation instead of parameterized query
    query = "SELECT id, name, department FROM employees WHERE name LIKE '%" + q + "%'"
    try:
        rows = DB.execute(query).fetchall()
        return render_template_string(HTML, q=q, rows=rows, error=None)
    except Exception as e:
        return render_template_string(HTML, q=q, rows=None, error=str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
