import os, sqlite3, secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from jinja2 import Environment, StrictUndefined

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'local-ctf-only-change-me')
DB = Path(__file__).resolve().parent / 'instance' / 'volyngas.db'
DB.parent.mkdir(parents=True, exist_ok=True)
FLAG = os.environ.get('CTF_FLAG', 'CTF{template_preview_is_not_plain_text}')

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, name TEXT, phone TEXT, address TEXT, service TEXT, status TEXT)')
init_db()

@app.route('/')
def home(): return render_template('index.html')

@app.route('/request', methods=['GET', 'POST'])
def new_request():
    if request.method == 'POST':
        name = request.form.get('name','').strip()[:80]
        phone = request.form.get('phone','').strip()[:30]
        address = request.form.get('address','').strip()[:150]
        service = request.form.get('service','').strip()
        if not all([name, phone, address]) or service not in ('Діагностика','Технічне обслуговування','Консультація'):
            flash('Перевірте дані заявки.'); return redirect(url_for('new_request'))
        ident = secrets.token_hex(4).upper()
        with connect() as c:
            c.execute('INSERT INTO requests VALUES (?,?,?,?,?,?)', (ident,name,phone,address,service,'Прийнята'))
        return redirect(url_for('status', ident=ident))
    return render_template('request.html')

@app.route('/status/<ident>')
def status(ident):
    with connect() as c:
        item = c.execute('SELECT * FROM requests WHERE id=?', (ident,)).fetchone()
    if item is None: abort(404)
    return render_template('status.html', item=item)

@app.route('/preview', methods=['GET','POST'])
def preview():
    output = None
    content = 'Шановний абоненте! Ваша заявка прийнята.'
    if request.method == 'POST':
        content = request.form.get('message','')[:300]
        # INTENTIONAL CTF SSTI: untrusted user input is interpreted as Jinja template source.
        # The sandboxed, restricted environment only exposes a mock CTF object.
        env = Environment(undefined=StrictUndefined, autoescape=True)
        try:
            output = env.from_string(content).render(company='VolynGas Service', ctf={'flag': FLAG})
        except Exception:
            output = 'Помилка формування повідомлення'
    return render_template('preview.html', output=output, content=content)

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST' and request.form.get('pin') == os.environ.get('ADMIN_PIN','4826'):
        session['admin'] = True
    if not session.get('admin'):
        return render_template('admin.html', locked=True)
    with connect() as c:
        items = c.execute('SELECT * FROM requests ORDER BY rowid DESC').fetchall()
    return render_template('admin.html', locked=False, items=items)

@app.post('/admin/update/<ident>')
def update(ident):
    if not session.get('admin'): abort(403)
    status = request.form.get('status')
    if status not in ('Прийнята','В роботі','Виконана'): abort(400)
    with connect() as c:
        c.execute('UPDATE requests SET status=? WHERE id=?', (status, ident))
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
