from flask import Flask, request, make_response, render_template_string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64, os

app = Flask(__name__)
KEY = os.urandom(16)
FLAG = "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}"

def encrypt_cookie(username):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(f"user={username};role=guest".encode(), 16))).decode()

def decrypt_cookie(cookie):
    try: return unpad(AES.new(KEY, AES.MODE_ECB).decrypt(base64.b64decode(cookie)), 16).decode()
    except: return ""

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><title>SCADA Control</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>SCADA Maintenance Terminal</h4></div>
        <div class="card-body">
            {% if msg %}
                <div class="alert alert-info">{{ msg }}</div>
            {% endif %}
            <form method="POST" action="/login">
                <div class="mb-3">
                    <label>Operator Name</label>
                    <input type="text" class="form-control" name="username">
                </div>
                <button type="submit" class="btn btn-warning">Generate Session</button>
            </form>
            <br><a href="/source" class="text-info">Terminal Source Code</a>
        </div>
    </div>
</div></body></html>
'''

@app.route('/')
def index():
    cookie = request.cookies.get('auth')
    msg = ""
    if cookie:
        data = decrypt_cookie(cookie)
        if "role=admin" in data: return f"SCADA Overridden! {FLAG}"
        msg = f"Active session: {data}"
    return render_template_string(HTML, msg=msg)

@app.route('/login', methods=['POST'])
def login():
    resp = make_response(render_template_string(HTML, msg="Session generated. Check your cookies."))
    resp.set_cookie('auth', encrypt_cookie(request.form.get('username', '').replace(';','').replace('=','')))
    return resp

@app.route('/source')
def source(): return open(__file__).read(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
