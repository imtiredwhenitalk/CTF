from flask import Flask, request, make_response
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

@app.route('/')
def index():
    cookie = request.cookies.get('auth')
    if cookie:
        data = decrypt_cookie(cookie)
        if "role=admin" in data: return f"SCADA Overridden! {FLAG}"
        return f"Logged in as: {data}"
    return '''<form method="POST" action="/login">User: <input name="username"><input type="submit"></form><a href="/source">Source</a>'''

@app.route('/login', methods=['POST'])
def login():
    resp = make_response("Logged in. <a href='/'>Back</a>")
    resp.set_cookie('auth', encrypt_cookie(request.form.get('username', '').replace(';','').replace('=','')))
    return resp

@app.route('/source')
def source(): return open(__file__).read(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
