import hmac
import os
import secrets
import sqlite3
import time
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from challenges import ALLOWED_FILES, BY_ID, CHALLENGES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "data", "ctf.db"))
DOWNLOADS = os.path.join(BASE_DIR, "downloads")
# Хост, який бачать учасники (для посилань на сервіси завдань)
PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "localhost")
CTF_NAME = os.environ.get("CTF_NAME", "Operation Titan CTF")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Простий ліміт спроб відправки прапорів: {user_id: [timestamps]}
ATTEMPTS = {}
MAX_ATTEMPTS, WINDOW = 8, 60


# ---------- БД ----------
def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        pw_hash TEXT NOT NULL,
        created INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS solves (
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        solved_at INTEGER NOT NULL,
        PRIMARY KEY (user_id, challenge_id)
    );
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER NOT NULL,
        correct INTEGER NOT NULL,
        ts INTEGER NOT NULL
    );
    """)
    db.commit()


with app.app_context():
    init_db()


# ---------- Допоміжне ----------
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token
app.jinja_env.globals["ctf_name"] = CTF_NAME


@app.before_request
def load_user_and_check_csrf():
    g.user = None
    uid = session.get("uid")
    if uid:
        g.user = get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if request.method == "POST":
        sent = request.form.get("csrf", "")
        if not hmac.compare_digest(sent, session.get("csrf", "")):
            abort(400, "Невірний CSRF-токен")


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not g.user:
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapper


def solved_ids(user_id):
    rows = get_db().execute("SELECT challenge_id FROM solves WHERE user_id=?", (user_id,))
    return {r["challenge_id"] for r in rows}


def service_url(ch):
    s = ch.get("service")
    if not s:
        return None
    if s["kind"] == "http":
        return f"http://{PUBLIC_HOST}:{s['port']}"
    return f"nc {PUBLIC_HOST} {s['port']}"


def public_challenge(ch):
    """Копія без прапора."""
    d = {k: v for k, v in ch.items() if k != "flag"}
    d["url"] = service_url(ch)
    return d


# ---------- Маршрути ----------
@app.route("/")
def index():
    return render_template("index.html", total=sum(c["points"] for c in CHALLENGES),
                           count=len(CHALLENGES))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not (3 <= len(username) <= 24) or not username.replace("_", "").replace("-", "").isalnum():
            flash("Нікнейм: 3-24 символи, літери/цифри/_/-.", "err")
        elif len(password) < 6:
            flash("Пароль має містити щонайменше 6 символів.", "err")
        else:
            try:
                db = get_db()
                cur = db.execute("INSERT INTO users (username, pw_hash, created) VALUES (?,?,?)",
                                 (username, generate_password_hash(password), int(time.time())))
                db.commit()
                session.clear()
                session["uid"] = cur.lastrowid
                return redirect(url_for("challenges"))
            except sqlite3.IntegrityError:
                flash("Такий нікнейм уже зайнятий.", "err")
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        row = get_db().execute("SELECT * FROM users WHERE username=?",
                               (request.form.get("username", "").strip(),)).fetchone()
        if row and check_password_hash(row["pw_hash"], request.form.get("password", "")):
            session.clear()
            session["uid"] = row["id"]
            return redirect(url_for("challenges"))
        flash("Невірний нікнейм або пароль.", "err")
    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/challenges")
@login_required
def challenges():
    done = solved_ids(g.user["id"])
    items = [public_challenge(c) for c in CHALLENGES]
    return render_template("challenges.html", items=items, done=done)


@app.route("/submit/<int:cid>", methods=["POST"])
@login_required
def submit(cid):
    ch = BY_ID.get(cid)
    if not ch:
        abort(404)
    uid = g.user["id"]
    now = time.time()
    recent = [t for t in ATTEMPTS.get(uid, []) if now - t < WINDOW]
    if len(recent) >= MAX_ATTEMPTS:
        flash(f"Забагато спроб. Зачекайте {WINDOW} с.", "err")
        return redirect(url_for("challenges"))
    ATTEMPTS[uid] = recent + [now]

    guess = request.form.get("flag", "").strip()
    ok = hmac.compare_digest(guess.encode(), ch["flag"].encode())
    db = get_db()
    db.execute("INSERT INTO submissions (user_id, challenge_id, correct, ts) VALUES (?,?,?,?)",
               (uid, cid, int(ok), int(now)))
    if ok:
        if cid in solved_ids(uid):
            flash("Це завдання вже зараховане.", "info")
        else:
            db.execute("INSERT INTO solves (user_id, challenge_id, solved_at) VALUES (?,?,?)",
                       (uid, cid, int(now)))
            flash(f"Вірно! +{ch['points']} балів за «{ch['title']}».", "ok")
    else:
        flash("Невірний прапор.", "err")
    db.commit()
    return redirect(url_for("challenges"))


@app.route("/download/<path:name>")
@login_required
def download(name):
    if name not in ALLOWED_FILES:
        abort(404)
    return send_from_directory(DOWNLOADS, name, as_attachment=True)


@app.route("/scoreboard")
def scoreboard():
    points = {c["id"]: c["points"] for c in CHALLENGES}
    db = get_db()
    users = db.execute("SELECT id, username FROM users").fetchall()
    solves = db.execute("SELECT user_id, challenge_id, solved_at FROM solves").fetchall()
    table = {u["id"]: {"name": u["username"], "score": 0, "last": 0, "n": 0} for u in users}
    for s in solves:
        row = table[s["user_id"]]
        row["score"] += points.get(s["challenge_id"], 0)
        row["n"] += 1
        row["last"] = max(row["last"], s["solved_at"])
    ranked = sorted(table.values(), key=lambda r: (-r["score"], r["last"]))
    return render_template("scoreboard.html", ranked=ranked)


@app.errorhandler(400)
@app.errorhandler(404)
def err(e):
    return render_template("error.html", e=e), e.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
