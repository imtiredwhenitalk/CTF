from flask import Flask, request
import pickle, base64, hmac, hashlib
from titan_ui import page
app = Flask(__name__)
SECRET = b"titan_weak_key_123"

# ---------------------------------------------------------------------------
# TRAP / RED HERRING. These values belong to the retired 2021 mobile client and
# to the migration test mirror; they are not the live scoring flag.
# ---------------------------------------------------------------------------
LEGACY_SECRET = b"titan_legacy_key_2021"
LEGACY_FLAG = "CTF{p1ckl3_l3g4cy_m1rr0r_fl4g}"
# The old mirror was /app/flag.txt. The live flag was moved to /flag.txt.

BODY = '''
<div class="card"><div class="hd">Синхронізація профілю<span class="sub">POST /upload</span></div><div class="bd">
  <form method="POST" action="/upload">
    <div class="field"><label for="sign">Підпис (HMAC-SHA256)</label>
      <input id="sign" class="input" type="text" name="sign" placeholder="hex-підпис payload" autocomplete="off"></div>
    <div class="field"><label for="payload">Payload (Base64 Pickle)</label>
      <input id="payload" class="input" type="text" name="payload" placeholder="base64-дані профілю" autocomplete="off"></div>
    <div class="row"><button class="btn primary" type="submit">Синхронізувати</button>
      <a href="/source">Переглянути код синхронізації</a></div>
  </form>
</div></div>
'''
RESULT = '''
<div class="card"><div class="hd">Результат</div><div class="bd">
  <div class="alert {{ kind }}">{{ msg }}</div>
  <a class="btn" href="/">Назад</a>
</div></div>
'''

def view(msg, kind="info", status=200):
    return page(RESULT, title="HR Portal", heading="Employee Portal Sync", tag="04 · Pickle",
                node="titan-node-04 · hr-portal", msg=msg, kind=kind), status

@app.route('/')
def index():
    return page(BODY, title="HR Portal", heading="Employee Portal Sync", tag="04 · Pickle", node="titan-node-04 · hr-portal",
                lead="Профілі співробітників передаються серіалізованим об'єктом із підписом.")

@app.route('/source')
def source(): return open(__file__).read(), 200, {'Content-Type': 'text/plain'}

@app.route('/upload', methods=['POST'])
def upload():
    sign = request.form.get('sign', '')
    payload = request.form.get('payload', '')
    expected_sign = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if sign != expected_sign: return view("Invalid HMAC signature!", "bad")
    try:
        obj = pickle.loads(base64.b64decode(payload))
        return view(f"Hello, {obj.name}", "ok")
    except Exception as e: return view(f"Error: {e}", "bad")

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
