from flask import Flask, request
import sqlite3, re, threading
from titan_ui import page
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.execute('CREATE TABLE users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}')")
    # TRAP / RED HERRING: rows below are archived from the 2022 directory.
    # They are not the live password and are not accepted by the scoreboard.
    conn.execute("INSERT INTO users VALUES (2, 'admin_legacy', 'CTF{bl1nd_sqli_l3g4cy_us3r}')")
    conn.execute('CREATE TABLE legacy_users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT INTO legacy_users VALUES (1, 'admin', 'CTF{bl1nd_sqli_l3g4cy_t4bl3}')")
    conn.execute('CREATE TABLE audit_notes (id INTEGER, note TEXT)')
    conn.execute("INSERT INTO audit_notes VALUES (1, 'flag archived after rotation: CTF{bl1nd_sqli_aud1t_n0t3}')")
    return conn
db = init_db()
lock = threading.Lock()

BODY = '''
<div class="card"><div class="hd">Пошук за ID<span class="sub">GET /?id=</span></div><div class="bd">
  <form method="GET">
    <div class="field"><label for="id">ID співробітника</label>
      <input id="id" class="input" type="text" name="id" placeholder="наприклад, 1" autocomplete="off" value="{{ q }}"></div>
    <button class="btn primary" type="submit">Знайти</button>
  </form>
  {% if result %}<div class="alert {{ kind }}">{{ result }}</div>{% endif %}
  <p class="muted" style="margin-top:1rem">Під час міграції старі записи збережено в
  таблицях <code>legacy_users</code> та <code>audit_notes</code>.</p>
</div></div>
'''

def view(result="", kind="info", q=""):
    return page(BODY, title="Staff Directory", heading="Staff Lookup", tag="07 · Blind SQLi",
                node="titan-node-07 · directory", lead="Внутрішній довідник співробітників.", result=result, kind=kind, q=q)

@app.route('/')
def index():
    uid = request.args.get('id', '')
    if not uid: return view()

    # Strict WAF
    if re.search(r"[\s=><]|\b(union|or|and)\b", uid, re.IGNORECASE):
        return view("WAF Blocked: Malicious input detected!", "bad", uid)
    try:
        with lock:
            res = db.execute(f"SELECT username FROM users WHERE id = {uid}").fetchone()
        if res: return view("User exists in directory.", "ok", uid)
        return view("User not found.", "warn", uid)
    except: return view("Database Error.", "bad", uid)

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
