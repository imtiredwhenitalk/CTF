import os
import jwt
from flask import Flask, jsonify, request
from ui import page, setup

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "Бібліотека ЛНТУ API", "#2dd4bf"
NAV = (("/", "Консоль API"),)
FLAG = "CTF{jwt_w34k_s3cr3t_cr4ck3d}"
SECRET = "lntu2026"  # навмисно слабкий секрет: «назва університету + рік»
USERS = {"reader": "reader123"}

JS = """
<script>
const out = document.getElementById('out');
async function call(url, opts){
  const r = await fetch(url, opts); const t = await r.text();
  out.textContent = r.status + ' ' + url + '\\n' + t; return t;
}
async function login(){
  const t = await call('/api/login', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({username: document.getElementById('u').value, password: document.getElementById('p').value})});
  try { document.getElementById('tok').value = JSON.parse(t).token || ''; } catch(e){}
}
function withToken(url){ call(url, {headers:{'Authorization':'Bearer ' + document.getElementById('tok').value}}); }
</script>"""


@app.get("/")
def index():
    body = f"""<h1>Бібліотека ЛНТУ · REST API</h1>
    <p class="lead">Консоль розробника. Токени JWT (HS256) видаються після входу.</p>
    <div class="card accent"><div class="row">
      <div><label>Логін</label><input id="u" value="reader"></div>
      <div><label>Пароль</label><input id="p" value="reader123"></div>
      <button onclick="login()">Отримати токен</button></div>
    <label>JWT-токен</label><textarea id="tok" placeholder="токен з'явиться тут"></textarea>
    <button onclick="withToken('/api/me')">GET /api/me</button>
    <button onclick="withToken('/api/admin/flag')" style="background:#f87171">GET /api/admin/flag</button></div>
    <h2>Відповідь</h2><pre id="out">—</pre>
    <p class="muted">Політика безпеки: секрет підпису = назва університету (малими літерами) + рік поточного семестру.</p>{JS}"""
    return page("Консоль API", body, BRAND, ACCENT, NAV)


@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    if USERS.get(d.get("username")) != d.get("password"):
        return jsonify(error="invalid credentials"), 401
    return jsonify(token=jwt.encode({"sub": d["username"], "role": "reader"}, SECRET, algorithm="HS256"))


def claims():
    h = request.headers.get("Authorization", "")
    if not h.startswith("Bearer "):
        return None
    try:
        return jwt.decode(h[7:], SECRET, algorithms=["HS256"])
    except Exception:
        return None


@app.get("/api/me")
def me():
    c = claims()
    return (jsonify(c), 200) if c else (jsonify(error="unauthorized"), 401)


@app.get("/api/admin/flag")
def admin_flag():
    c = claims()
    if not c:
        return jsonify(error="unauthorized"), 401
    if c.get("role") != "admin":
        return jsonify(error="admin role required", your_role=c.get("role")), 403
    return jsonify(flag=FLAG)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
