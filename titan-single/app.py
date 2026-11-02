"""Operation Titan - ONE vulnerable-by-design CTF site (platform + 10 challenges).
FOR TRAINING ONLY. Do not expose to the internet."""
import os, re, json, time, base64, hmac, hashlib, pickle, sqlite3, secrets, subprocess, threading
from functools import wraps
import jwt
from flask import (Flask, request, session, redirect, url_for, jsonify, make_response,
                   send_from_directory, abort, render_template, flash)
from jinja2 import DictLoader
from markupsafe import Markup, escape
from werkzeug.security import generate_password_hash, check_password_hash
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
os.makedirs(DATA, exist_ok=True)
FLAG4_FILE = os.environ.get("FLAG4_FILE", "/tmp/titan_flag4.txt")
FLAG10_FILE = os.environ.get("FLAG10_FILE", "/etc/secret_flag_1337.txt")

CHALS = {
 1: ("Git Leak & XOR", "Crypto/Web", 100, "CTF{g1t_l34k_4nd_x0r_m4st3r}", "Ми забули прибрати службові файли. Знайди те, що видалили."),
 2: ("JWT Alg Confusion", "Web", 200, "CTF{jwt_4lg_c0nfus10n_byp4ss}", "Шлюз довіряє заголовку токена. Стань адміном."),
 3: ("LFSR Reversing", "Crypto", 200, "CTF{lfsr_1s_n0t_s3cur3_3n0ugh}", "«Незламний» потоковий шифр. Відновити флаг із flag.enc."),
 4: ("Pickle & HMAC", "Web/Pwn", 300, "CTF{d3s3r14l1z4t10n_hm4c_byp4ss}", "Портал синхронізації довіряє підписаним об'єктам. Флаг у файлі " + FLAG4_FILE),
 5: ("JWT & RSA", "Crypto", 300, "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}", "Зламай сесію, потім розшифруй адмінський флаг."),
 6: ("AES ECB Block", "Crypto", 300, "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}", "Зроби так, щоб термінал побачив role=admin."),
 7: ("Blind SQLi WAF", "Web", 400, "CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}", "Суворий WAF. Тільки blind boolean."),
 8: ("RSA Wiener's Attack", "Crypto", 400, "CTF{w13n3r_4tt4ck_d_1s_t00_sm4ll}", "Приватна експонента d підозріло мала."),
 9: ("Hidden Archive", "Forensics", 300, "CTF{st3g0_4nd_43s_1s_fun}", "Зображення ховає архів. Дістань і розшифруй."),
 10: ("LFI", "Web", 300, "CTF{lf1_t0_rc3_p01s0n1ng_pr0}", "Сервер документів читає файли. Секрет лежить у /etc/secret_flag_1337.txt"),
}
def flag_of(i): return CHALS[i][3]

# ---------------- app + layout ----------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change_me_titan_secret")
BASE_HTML = """<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} · Operation Titan</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><nav class="navbar navbar-dark bg-black"><div class="container">
<a class="navbar-brand" href="/">🛡️ Operation Titan</a>
<div><a class="btn btn-sm btn-outline-light" href="/challenges">Завдання</a>
<a class="btn btn-sm btn-outline-light" href="/scoreboard">Скорборд</a>
{% if session.get('user') %}<span class="mx-2">{{ session['user'] }}</span><a class="btn btn-sm btn-outline-warning" href="/logout">Вийти</a>
{% else %}<a class="btn btn-sm btn-warning" href="/login">Вхід</a>{% endif %}</div></div></nav>
<div class="container mt-4">{% with m = get_flashed_messages() %}{% for x in m %}<div class="alert alert-info">{{ x }}</div>{% endfor %}{% endwith %}
<div class="card bg-secondary text-light"><div class="card-header"><h4>{{ title }}</h4></div><div class="card-body">{{ body }}</div></div></div></body></html>"""
app.jinja_loader = DictLoader({"base.html": BASE_HTML})

def page(title, body, status=200):
    return render_template("base.html", title=title, body=Markup(body)), status

# ---------------- platform db ----------------
DB = os.path.join(DATA, "platform.db")
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
with db() as c:
    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE, pw TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS solves(user_id INT, chal INT, ts REAL, UNIQUE(user_id,chal))")

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("uid"): return redirect("/login")
        return f(*a, **k)
    return w

@app.route("/")
def index():
    return page("Operation Titan", """<p class="lead">Навчальний CTF в одному сайті: 10 завдань із різними вразливостями.</p>
<p>Зареєструйся, відкривай завдання, знаходь флаги формату <code>CTF{...}</code> і здавай їх на сторінці завдань.</p>
<a class="btn btn-warning" href="/challenges">До завдань</a>""")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        n, p = request.form.get("name", ""), request.form.get("password", "")
        if not re.fullmatch(r"\w{3,24}", n) or len(p) < 4:
            flash("Нік: 3-24 символи (літери/цифри/_), пароль: від 4 символів"); return redirect("/register")
        try:
            with db() as c: c.execute("INSERT INTO users(name,pw) VALUES(?,?)", (n, generate_password_hash(p)))
        except sqlite3.IntegrityError:
            flash("Такий нік уже є"); return redirect("/register")
        flash("Готово, увійди"); return redirect("/login")
    return page("Реєстрація", AUTH_FORM.format(action="/register", btn="Зареєструватись"))

AUTH_FORM = """<form method="POST" action="{action}"><input class="form-control mb-2" name="name" placeholder="нік" required>
<input class="form-control mb-2" type="password" name="password" placeholder="пароль" required>
<button class="btn btn-warning">{btn}</button></form><p class="mt-3"><a class="text-info" href="/register">Реєстрація</a> · <a class="text-info" href="/login">Вхід</a></p>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with db() as c: u = c.execute("SELECT * FROM users WHERE name=?", (request.form.get("name", ""),)).fetchone()
        if u and check_password_hash(u["pw"], request.form.get("password", "")):
            session["uid"], session["user"] = u["id"], u["name"]; return redirect("/challenges")
        flash("Невірний нік або пароль"); return redirect("/login")
    return page("Вхід", AUTH_FORM.format(action="/login", btn="Увійти"))

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/challenges")
def challenges():
    solved = set()
    if session.get("uid"):
        with db() as c: solved = {r["chal"] for r in c.execute("SELECT chal FROM solves WHERE user_id=?", (session["uid"],))}
    rows = ""
    for i, (t, cat, pts, _, d) in CHALS.items():
        ok = "✅" if i in solved else ""
        rows += f"""<div class="card bg-dark mb-3"><div class="card-body"><h5>{i:02d}. {escape(t)} {ok}
<span class="badge bg-info text-dark">{escape(cat)}</span> <span class="badge bg-warning text-dark">{pts}</span></h5>
<p>{escape(d)}</p><a class="btn btn-sm btn-outline-info" href="/c/{i}/">Відкрити</a>
<form class="d-inline-flex ms-2" method="POST" action="/submit"><input type="hidden" name="chal" value="{i}">
<input class="form-control form-control-sm" name="flag" placeholder="CTF{{...}}" style="width:260px"> 
<button class="btn btn-sm btn-warning ms-1">Здати</button></form></div></div>"""
    return page("Завдання", rows)

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    try: i = int(request.form.get("chal", 0)); assert i in CHALS
    except Exception: abort(400)
    if hmac.compare_digest(request.form.get("flag", "").strip().encode(), flag_of(i).encode()):
        with db() as c: c.execute("INSERT OR IGNORE INTO solves VALUES(?,?,?)", (session["uid"], i, time.time()))
        flash(f"✅ Правильно! +{CHALS[i][2]}")
    else: flash("❌ Невірний флаг")
    return redirect("/challenges")

@app.route("/scoreboard")
def scoreboard():
    with db() as c: rs = c.execute("SELECT u.name, s.chal, s.ts FROM solves s JOIN users u ON u.id=s.user_id").fetchall()
    sc = {}
    for r in rs:
        a = sc.setdefault(r["name"], [0, 0.0, 0]); a[0] += CHALS[r["chal"]][2]; a[1] = max(a[1], r["ts"]); a[2] += 1
    top = sorted(sc.items(), key=lambda kv: (-kv[1][0], kv[1][1]))
    body = "<table class='table table-dark'><tr><th>#</th><th>Гравець</th><th>Очки</th><th>Задач</th></tr>"
    for rank, (n, (p, _, k)) in enumerate(top, 1): body += f"<tr><td>{rank}</td><td>{escape(n)}</td><td>{p}</td><td>{k}</td></tr>"
    return page("Скорборд", body + "</table>")

# =============== 1. Git leak ===============
C1 = os.path.join(DATA, "c1_site")
def build_c1():
    if os.path.isdir(os.path.join(C1, ".git")): return
    os.makedirs(C1, exist_ok=True)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=Admin", "-c", "user.email=admin@titan", *a], cwd=C1, check=True, capture_output=True)
    g("init", "-q")
    open(os.path.join(C1, "index.html"), "w").write("<h1>Titan Secure Node v1.0</h1><p>We are developing our new encryption module.</p><p>Source code management is strictly monitored.</p>")
    open(os.path.join(C1, "crypto.py"), "w").write("def encrypt(text): return ''.join([chr(ord(c)^42) for c in text])\n")
    g("add", "index.html", "crypto.py"); g("commit", "-q", "-m", "Initial commit")
    open(os.path.join(C1, "flag.enc"), "wb").write(bytes(ord(ch) ^ 42 for ch in flag_of(1)))
    g("add", "flag.enc"); g("commit", "-q", "-m", "Added encrypted flag")
    os.remove(os.path.join(C1, "crypto.py")); g("add", "-A"); g("commit", "-q", "-m", "Removed crypto.py")
    g("update-server-info")
build_c1()

@app.route("/c/1/")
def c1_index():
    return page("01. Titan Secure Node", "<p class='lead'>We are developing our new encryption module.</p><div class='alert alert-info'>Notice: Source code management is strictly monitored.</div>")
@app.route("/c/1/<path:p>")
def c1_files(p): return send_from_directory(C1, p)   # also serves .git/ (intentional leak)

# =============== 2. JWT alg confusion ===============
_k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM_PUB = _k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
def b64d(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def verify2(token):
    h, p, s = token.split(".")
    alg = json.loads(b64d(h)).get("alg")
    if alg == "HS256":   # VULNERABLE: key taken from header alg, public key reused as HMAC secret
        exp = hmac.new(PEM_PUB.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(exp, b64d(s)): raise ValueError("bad signature")
        return json.loads(b64d(p))
    if alg == "RS256": return jwt.decode(token, PEM_PUB, algorithms=["RS256"])
    raise ValueError("unsupported alg")
@app.route("/c/2/")
def c2_index():
    return page("02. API Gateway v2", "<p>Access requires a valid JWT.</p><ul><li><a class='text-info' href='/c/2/pub'>Public key</a></li><li><a class='text-info' href='/c/2/flag'>Admin panel</a> (Authorization header, raw token)</li></ul>")
@app.route("/c/2/pub")
def c2_pub(): return PEM_PUB, 200, {"Content-Type": "text/plain"}
@app.route("/c/2/flag")
def c2_flag():
    t = request.headers.get("Authorization")
    if not t: return jsonify(error="Missing Authorization header"), 401
    try:
        if verify2(t).get("role") == "admin": return flag_of(2)
        return jsonify(error="Role must be 'admin'"), 403
    except Exception as e: return str(e), 401

# =============== 3. LFSR ===============
def lfsr(seed, taps, n):
    st, out = seed, []
    for _ in range(n):
        out.append(st & 1); b = 0
        for t in taps: b ^= (st >> t) & 1
        st = (st >> 1) | (b << 15)
    return out
def l_enc(data, seed):
    bits = lfsr(seed, [0, 2, 3, 5], len(data) * 8)
    return bytes(x ^ int("".join(map(str, bits[i*8:(i+1)*8])), 2) for i, x in enumerate(data))
C3_SRC = '''# Titan custom LFSR stream cipher (16-bit state)
def lfsr(seed, taps, length):
    state = seed
    out = []
    for _ in range(length):
        out.append(state & 1)
        bit = 0
        for t in taps:
            bit ^= (state >> t) & 1
        state = (state >> 1) | (bit << 15)
    return out

def encrypt(data: bytes, seed: int) -> bytes:
    bits = lfsr(seed, [0, 2, 3, 5], len(data) * 8)
    res = bytearray()
    for i, byte in enumerate(data):
        key_byte = int("".join(map(str, bits[i * 8:(i + 1) * 8])), 2)
        res.append(byte ^ key_byte)
    return bytes(res)
# flag.enc = encrypt(flag.encode(), SECRET_SEED)   # 16-bit secret seed
'''
C3_ENC = l_enc(flag_of(3).encode(), secrets.randbelow(65535) + 1)
@app.route("/c/3/")
def c3_index():
    return page("03. Titan Custom Stream Cipher", "<p>We developed an unbreakable LFSR-based stream cipher.</p><a class='btn btn-outline-light' href='/c/3/encrypt.py'>encrypt.py</a> <a class='btn btn-outline-warning' href='/c/3/flag.enc'>flag.enc</a>")
@app.route("/c/3/encrypt.py")
def c3_src(): return C3_SRC, 200, {"Content-Type": "text/plain"}
@app.route("/c/3/flag.enc")
def c3_enc(): return C3_ENC, 200, {"Content-Type": "application/octet-stream", "Content-Disposition": "attachment; filename=flag.enc"}

# =============== 4. Pickle + weak HMAC ===============
SECRET4 = b"titan_weak_key_123"
try: open(FLAG4_FILE, "w").write(flag_of(4) + "\n")
except OSError: pass
C4_SRC = '''SECRET = b"titan_weak_key_123"

@app.route('/c/4/upload', methods=['POST'])
def upload():
    sign = request.form.get('sign', '')
    payload = request.form.get('payload', '')
    expected = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if sign != expected: return "Invalid HMAC signature!"
    obj = pickle.loads(base64.b64decode(payload))
    return f"Hello, {obj.name}"
'''
@app.route("/c/4/")
def c4_index():
    return page("04. Employee Portal Sync", """<form method="POST" action="/c/4/upload"><input class="form-control mb-2" name="sign" placeholder="HMAC-SHA256 signature">
<input class="form-control mb-2" name="payload" placeholder="Base64 pickle"><button class="btn btn-primary">Sync Profile</button></form>
<br><a class="text-info" href="/c/4/source">Sync source</a>""")
@app.route("/c/4/source")
def c4_source(): return C4_SRC, 200, {"Content-Type": "text/plain"}
@app.route("/c/4/upload", methods=["POST"])
def c4_upload():
    sign, payload = request.form.get("sign", ""), request.form.get("payload", "")
    if sign != hmac.new(SECRET4, payload.encode(), hashlib.sha256).hexdigest(): return "Invalid HMAC signature!"
    try: return f"Hello, {pickle.loads(base64.b64decode(payload)).name}"     # VULNERABLE deserialization
    except Exception as e: return f"Error: {e}"

# =============== 5. JWT weak secret + small RSA ===============
JWT5, N5, E5 = "123456", 54173879, 65537
ENC5 = [pow(ord(c), E5, N5) for c in flag_of(5)]
@app.route("/c/5/")
def c5_index():
    tok = jwt.encode({"role": "guest"}, JWT5, algorithm="HS256")
    return page("05. Executive Access", f"<p>Your session token:</p><pre class='bg-dark p-3 text-success'>{escape(tok)}</pre><p>Send it in the Authorization header to <code>/c/5/admin</code></p>")
@app.route("/c/5/admin")
def c5_admin():
    try:
        if jwt.decode(request.headers.get("Authorization", ""), JWT5, algorithms=["HS256"]).get("role") == "admin":
            return jsonify(msg="Welcome Admin!", n=N5, e=E5, enc=ENC5)
    except Exception: pass
    return "Unauthorized", 401

# =============== 6. AES-ECB cookie ===============
KEY6 = os.urandom(16)
def enc6(u): return base64.b64encode(AES.new(KEY6, AES.MODE_ECB).encrypt(pad(f"user={u};role=guest".encode(), 16))).decode()
def dec6(c):
    try: return unpad(AES.new(KEY6, AES.MODE_ECB).decrypt(base64.b64decode(c)), 16).decode()
    except Exception: return ""
def c6_page(msg=""):
    m = f"<div class='alert alert-info'>{escape(msg)}</div>" if msg else ""
    return page("06. SCADA Maintenance Terminal", m + """<form method="POST" action="/c/6/login"><input class="form-control mb-2" name="username" placeholder="Operator name">
<button class="btn btn-warning">Generate Session</button></form><br><a class="text-info" href="/c/6/source">Terminal source</a>""")
C6_SRC = '''def encrypt_cookie(username):
    cipher = AES.new(KEY, AES.MODE_ECB)
    return b64(cipher.encrypt(pad(f"user={username};role=guest".encode(), 16)))

# login: username = username.replace(';','').replace('=','')
# index: if "role=admin" in decrypt(cookie): print(FLAG)
'''
@app.route("/c/6/")
def c6_index():
    ck = request.cookies.get("auth")
    if ck:
        d = dec6(ck)
        if "role=admin" in d: return page("06. SCADA", f"<h3>SCADA Overridden!</h3><code>{flag_of(6)}</code>")
        return c6_page(f"Active session: {d}")
    return c6_page()
@app.route("/c/6/login", methods=["POST"])
def c6_login():
    r = make_response(c6_page("Session generated. Check your cookies."))
    r.set_cookie("auth", enc6(request.form.get("username", "").replace(";", "").replace("=", "")), path="/c/6")
    return r
@app.route("/c/6/source")
def c6_source(): return C6_SRC, 200, {"Content-Type": "text/plain"}

# =============== 7. Blind SQLi + WAF ===============
_c7 = sqlite3.connect(":memory:", check_same_thread=False)
_c7.execute("CREATE TABLE users(id INTEGER, username TEXT, password TEXT)")
_c7.execute("INSERT INTO users VALUES(1,'admin',?)", (flag_of(7),))
L7 = threading.Lock()
@app.route("/c/7/")
def c7_index():
    uid = request.args.get("id", "")
    res = ""
    if uid:
        if re.search(r"[\s=><]|\b(union|or|and)\b", uid, re.I): res = "WAF Blocked: Malicious input detected!"
        else:
            try:
                with L7: r = _c7.execute(f"SELECT username FROM users WHERE id = {uid}").fetchone()   # VULNERABLE
                res = "User exists in directory." if r else "User not found."
            except Exception: res = "Database Error."
    return page("07. Staff Lookup", f"""<form method="GET"><input class="form-control" name="id" placeholder="Staff ID (e.g. 1)">
<button class="btn btn-primary mt-2">Search</button></form><div class="mt-3 text-warning">{escape(res)}</div>""")

# =============== 8. Wiener ===============
C8 = json.load(open(os.path.join(BASE, "assets", "c8.json")))
@app.route("/c/8/")
def c8_index():
    s = "".join(f"<p style='word-break:break-all'><strong>{k}:</strong> {C8[k]}</p>" for k in "NeC")
    return page("08. Intercepted RSA Transmission", s + "<div class='alert alert-info'>Intel: the private exponent 'd' is suspiciously small.</div>")

# =============== 9. Stego ===============
@app.route("/c/9/")
def c9_index():
    return page("09. Titan Archive Node", "<a class='btn btn-primary' href='/c/9/image.png'>Download Encrypted Asset</a><p class='mt-3 text-muted'>Password hint: titan</p>")
@app.route("/c/9/image.png")
def c9_img(): return send_from_directory(os.path.join(BASE, "assets"), "image.png")

# =============== 10. LFI ===============
C10 = os.path.join(DATA, "c10_files"); os.makedirs(C10, exist_ok=True)
open(os.path.join(C10, "welcome.txt"), "w").write("Titan Document Server V3. All files are stored securely.")
try: open(FLAG10_FILE, "w").write(flag_of(10) + "\n")
except OSError: pass
@app.route("/c/10/")
def c10_index():
    f, content = request.args.get("file", ""), "Select a file to read."
    if f:
        if ".." in f: content = "Hacking Attempt Detected!"
        else:
            try: content = open(os.path.join(C10, f)).read()      # VULNERABLE: absolute path overrides base dir
            except Exception: content = "File not found."
    return page("10. Document Server", f"<a class='btn btn-info' href='/c/10/?file=welcome.txt'>Load Welcome Doc</a><hr><pre class='bg-dark p-3 text-light'>{escape(content)}</pre>")

@app.route("/health")
def health(): return "ok"
