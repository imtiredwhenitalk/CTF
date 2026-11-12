from flask import Flask, request, jsonify
import jwt
from titan_ui import page
app = Flask(__name__)
JWT_SECRET = "123456"
n = 54173879
e = 65537
FLAG = "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"
encrypted_flag = [pow(ord(c), e, n) for c in FLAG]

# ---------------------------------------------------------------------------
# TRAP / RED HERRING. Pre-rotation archive values. Decrypting these gives a
# retired flag that the scoreboard rejects; the live payload is above.
# ---------------------------------------------------------------------------
LEGACY_FLAG = "CTF{rs4_l3g4cy_k3y_r0t4t3d}"
LEGACY_N = 1000036000099
LEGACY_E = 65537
LEGACY_ENC = [494595306700, 220091654224, 712350340228, 401545281796, 567093028755,
              652289077990, 41181925686, 696115105548, 66430751771, 799592089105,
              747272319801, 41181925686, 961574227611, 123230991267, 696115105548,
              139508643943, 799592089105, 123230991267, 696115105548, 567093028755,
              977768124177, 273294389345, 41181925686, 273294389345, 799592089105,
              154827252436, 330073803953]

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
            return jsonify({
                "msg": "Welcome Admin!",
                "n": n,
                "e": e,
                "enc": encrypted_flag,
                # Archived pre-rotation package. Decoys are not scored.
                "legacy": {"n": LEGACY_N, "e": LEGACY_E, "enc": LEGACY_ENC},
            })
    except: pass
    return "Unauthorized", 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
