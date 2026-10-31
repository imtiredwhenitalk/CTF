import os
from flask import Flask, Response, abort, request, render_template_string

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.environ.get("DOCS_DIR", os.path.join(BASE, "docs"))

HTML = '''
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>ТИТАН ЕНЕРГО - Портал документації</title>
    <style>
        body { font-family: monospace; background: #0f172a; color: #38bdf8; padding: 40px; }
        .card { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 8px; }
        a { color: #7dd3fc; }
    </style>
</head>
<body>
    <div class="card">
        <h1>[+] ПОРТАЛ ТЕХНІЧНОЇ ДОКУМЕНТАЦІЇ "ТИТАН"</h1>
        <p>Доступні документи:</p>
        <ul>
            {% for d in docs %}<li><a href="/view?file={{ d }}">{{ d }}</a></li>{% endfor %}
        </ul>
        <!-- DEV NOTE: чутливі файли лежать поруч з docs/, у каталозі secret/. Захист від ../ уже додано. -->
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    docs = sorted(os.listdir(DOCS_DIR))
    return render_template_string(HTML, docs=docs)


@app.route('/view')
def view():
    name = request.args.get('file', '')
    # Vulnerable: "захист" видаляє ../ лише за один прохід
    name = name.replace("../", "")
    name = name.lstrip("/")
    path = os.path.join(DOCS_DIR, name)
    try:
        with open(path, "r", errors="ignore") as f:
            return Response(f.read(), mimetype="text/plain; charset=utf-8")
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
