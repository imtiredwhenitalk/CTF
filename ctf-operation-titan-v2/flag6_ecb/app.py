from flask import Flask, request, make_response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, os
from titan_ui import page

app = Flask(__name__)
KEY = os.urandom(16)
FLAG = "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}"

def encrypt_cookie(username):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(f"user={username};role=guest".encode(), 16))).decode()

def decrypt_cookie(cookie):
    try: return unpad(AES.new(KEY, AES.MODE_ECB).decrypt(base64.b64decode(cookie)), 16).decode()
    except: return ""

BODY = '''
<div class="card"><div class="hd">Сесія оператора<span class="sub">cookie: auth</span></div><div class="bd">
  {% if msg %}<div class="alert info">{{ msg }}</div>{% endif %}
  <form method="POST" action="/login">
    <div class="field"><label for="u">Ім'я оператора</label>
      <input id="u" class="input" type="text" name="username" autocomplete="off" placeholder="operator"></div>
    <div class="row"><button class="btn primary" type="submit">Створити сесію</button>
      <a href="/source">Код терміналу</a></div>
  </form>
</div></div>
'''
WIN = '''
<div class="card"><div class="hd">Доступ підтверджено</div><div class="bd">
  <div class="alert ok"><b>SCADA Overridden!</b> <code>{{ flag }}</code></div>
</div></div>
'''

def render(msg=""):
    return page(BODY, title="SCADA", heading="SCADA Maintenance Terminal", tag="06 · AES-ECB",
                node="titan-node-06 · scada", lead="Сесія зберігається в зашифрованому cookie.", msg=msg)

@app.route('/')
def index():
    cookie = request.cookies.get('auth')
    msg = ""
    if cookie:
        data = decrypt_cookie(cookie)
        if "role=admin" in data:
            return page(WIN, title="SCADA", heading="SCADA Maintenance Terminal", tag="06 · AES-ECB",
                        node="titan-node-06 · scada", flag=FLAG)
        msg = f"Active session: {data}"
    return render(msg)

@app.route('/login', methods=['POST'])
def login():
    resp = make_response(render("Session generated. Check your cookies."))
    resp.set_cookie('auth', encrypt_cookie(request.form.get('username', '').replace(';','').replace('=','')))
    return resp

@app.route('/source')
def source(): return open(__file__).read(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
