from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64, hmac, os, secrets
from titan_ui import page

app = Flask(__name__)

# Per-instance secrets. The vault token is NOT in the source code: it is
# generated at startup and only ever leaves the process encrypted.
KEY = os.urandom(16)
PREFIX = os.urandom(secrets.randbelow(16))   # random 0..15 byte prefix, fixed per process
TOKEN = secrets.token_hex(16)                # 32 hex chars
SUFFIX = ("|vault=" + TOKEN).encode()

# ---------------------------------------------------------------------------
# TRAP / RED HERRING. The legacy vault was decommissioned and its token is
# public on purpose. It only opens an old flag that is not scored.
# ---------------------------------------------------------------------------
LEGACY_TOKEN = "d3adbeefcafebabe0123456789abcdef"
LEGACY_FLAG = "CTF{3cb_l3g4cy_v4ult_r0t4t3d}"

try:
    FLAG = os.environ.get("FLAG") or open("/flag.txt").read().strip()
except OSError:
    FLAG = ""

BODY = '''
<div class="card"><div class="hd">Шифрування аудит-банера<span class="sub">GET /api/encrypt?data=</span></div><div class="bd">
  <p>Кожен банер шифрується AES-ECB. Перед вашим текстом сервіс додає випадковий
  службовий префікс, а після нього — секретний токен сховища.</p>
  <form method="GET" action="/api/encrypt">
    <div class="field"><label for="data">Текст банера</label>
      <input id="data" class="input" name="data" value="status=nominal" autocomplete="off"></div>
    <button class="btn primary" type="submit">Зашифрувати</button>
  </form>
  {% if msg %}<div class="alert {{ kind }}">{{ msg }}</div>{% endif %}
</div></div>
<div class="card"><div class="hd">Розблокування сховища<span class="sub">GET /unlock?token=</span></div><div class="bd">
  <form method="GET" action="/unlock">
    <div class="field"><label for="token">Токен сховища</label>
      <input id="token" class="input" name="token" placeholder="32 hex-символи" autocomplete="off"></div>
    <button class="btn primary" type="submit">Відкрити</button>
  </form>
  <div class="alert warn">Токен ніколи не передається у відкритому вигляді. Він завжди дописується
  до відкритого тексту перед шифруванням.</div>
  <a class="btn" href="/source">Код терміналу</a>
  <a class="btn" href="/legacy">Старий термінал (legacy)</a>
</div></div>
'''

WIN = '''
<div class="card"><div class="hd">Сховище відкрито</div><div class="bd">
  <div class="alert ok"><b>SCADA Overridden!</b> <code>{{ flag }}</code></div>
</div></div>
'''


def render(msg="", kind="info"):
    return page(BODY, title="SCADA", heading="SCADA Maintenance Terminal", tag="06 · AES-ECB",
                node="titan-node-06 · scada",
                lead="Аудит-банер шифрується детермінованим AES-ECB із секретним суфіксом.",
                msg=msg, kind=kind)


def encrypt_banner(data):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(PREFIX + data + SUFFIX, 16))).decode()


@app.route('/')
def index():
    return render()


@app.route('/api/encrypt')
def encrypt():
    data = request.args.get('data', '').encode('utf-8')
    if len(data) > 256:
        return jsonify({"error": "data too long"}), 400
    return jsonify({"ciphertext": encrypt_banner(data)})


@app.route('/unlock')
def unlock():
    token = request.args.get('token', '')
    if token and hmac.compare_digest(token.encode('utf-8', 'ignore'), TOKEN.encode()):
        return page(WIN, title="SCADA", heading="SCADA Maintenance Terminal", tag="06 · AES-ECB",
                    node="titan-node-06 · scada", flag=FLAG)
    return render("Invalid vault token.", "bad")


@app.route('/legacy')
def legacy():
    return (
        "Legacy vault terminal (decommissioned).\n"
        "The old test token was left public for migration:\n"
        f"  {LEGACY_TOKEN}\n"
        f"Try /unlock_legacy?token={LEGACY_TOKEN}\n"
    ), 200, {'Content-Type': 'text/plain'}


@app.route('/unlock_legacy')
def unlock_legacy():
    token = request.args.get('token', '')
    if token and hmac.compare_digest(token.encode('utf-8', 'ignore'), LEGACY_TOKEN.encode()):
        return page(WIN, title="SCADA", heading="SCADA Maintenance Terminal (legacy)", tag="06 · AES-ECB",
                    node="titan-node-06 · scada", flag=LEGACY_FLAG)
    return render("Invalid legacy vault token.", "bad")


@app.route('/source')
def source():
    return open(__file__).read(), 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
