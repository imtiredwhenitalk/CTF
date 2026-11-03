from flask import Flask, request, jsonify
import jwt, hmac, hashlib, base64, json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from titan_ui import page

app = Flask(__name__)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
pem_pub = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
FLAG = "CTF{jwt_4lg_c0nfus10n_byp4ss}"

BODY = '''
<div class="card"><div class="hd">Доступ до API<span class="sub">GET /flag</span></div><div class="bd">
  <p>Адмін-панель приймає лише валідний JWT у заголовку <code>Authorization</code>. Токени підписує сервіс автентифікації Titan; публічний ключ відкритий.</p>
  <div class="row" style="margin-top:1rem">
    <a class="btn" href="/pub">Завантажити публічний ключ</a>
    <a class="btn primary" href="/flag">Відкрити адмін-панель</a>
  </div>
</div></div>
<div class="card"><div class="hd">Приклад запиту</div><div class="bd">
<pre class="code plain">curl -H "Authorization: &lt;token&gt;" http://&lt;host&gt;/flag</pre>
<div class="alert info">Вимога до токена: у claims має бути <code>role: admin</code>.</div>
</div></div>
'''

def b64d(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))

def verify_token(token):
    # VULNERABLE BY DESIGN: algorithm is taken from the token header and the same
    # public key is used both as RSA key (RS256) and as HMAC secret (HS256).
    # (Modern PyJWT refuses this, so HS256 is verified manually.)
    h_b64, p_b64, s_b64 = token.split('.')
    alg = json.loads(b64d(h_b64)).get('alg')
    if alg == 'HS256':
        expected = hmac.new(pem_pub.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, b64d(s_b64)):
            raise ValueError("Signature verification failed")
        return json.loads(b64d(p_b64))
    if alg == 'RS256':
        return jwt.decode(token, pem_pub, algorithms=["RS256"])
    raise ValueError("Unsupported algorithm")

@app.route('/')
def index():
    return page(BODY, title="API Gateway", heading="API Gateway v2", tag="02 · JWT", node="titan-node-02 · api-gateway",
                lead="Єдина точка входу до внутрішніх сервісів.")

@app.route('/pub')
def pub(): return pem_pub, 200, {'Content-Type': 'text/plain'}

@app.route('/flag')
def flag():
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing Authorization header"}), 401
    try:
        data = verify_token(token)
        if data.get('role') == 'admin': return FLAG
        return jsonify({"error": "Role must be 'admin'"}), 403
    except Exception as e: return str(e), 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
