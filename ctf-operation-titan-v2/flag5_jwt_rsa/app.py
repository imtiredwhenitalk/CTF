from flask import Flask, request, jsonify
import jwt
from titan_ui import page
app = Flask(__name__)
JWT_SECRET = "123456"
n = 54173879
e = 65537
FLAG = "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"
encrypted_flag = [pow(ord(c), e, n) for c in FLAG]

BODY = '''
<div class="card"><div class="hd">Ваш токен сесії<span class="sub">role: guest</span></div><div class="bd">
  <div style="position:relative"><pre id="tok" class="code has-cp">{{ token }}</pre>
  <button class="btn sm cp" data-copy="tok">Копіювати</button></div>
  <p class="muted" style="margin-top:1rem">Надсилайте токен у заголовку <code>Authorization</code> на <code>/admin</code>.</p>
  <div class="alert warn">Гостьовий токен не дає доступу до виконавчих даних.</div>
</div></div>
'''

@app.route('/')
def index():
    token = jwt.encode({"role": "guest"}, JWT_SECRET, algorithm="HS256")
    return page(BODY, title="Executive Portal", heading="Executive Access", tag="05 · JWT + RSA",
                node="titan-node-05 · executive", lead="Закритий розділ для керівництва.", token=token)

@app.route('/admin')
def admin():
    token = request.headers.get('Authorization', '')
    try:
        if jwt.decode(token, JWT_SECRET, algorithms=["HS256"]).get("role") == "admin":
            return jsonify({"msg": "Welcome Admin!", "n": n, "e": e, "enc": encrypted_flag})
    except: pass
    return "Unauthorized", 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
