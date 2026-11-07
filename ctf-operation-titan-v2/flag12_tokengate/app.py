"""Operation Titan — 12. Token Forge.

Vulnerability (by design): the session token signs only the numeric user id,
but the server trusts the ``role`` field from the token payload.  Change
``role`` to ``admin``, keep the original signature and the admin panel opens.

The admin panel serves an AES-256-CBC encrypted audit log.  The key is
SHA-256(session token) and the first 16 bytes of the file are the IV.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import threading
import time
from typing import Any

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, Response, make_response, redirect, request
from werkzeug.security import check_password_hash, generate_password_hash

from titan_ui import page

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("TOKENGATE_DATA_DIR", os.path.join(APP_DIR, "data"))
USERS_PATH = os.path.join(DATA_DIR, "users.json")
SIGNING_KEY = b"titan-token-forge-v2"
FLAG = "CTF{t0k3n_subst1tut10n_4nd_3ncrypt3d_l0gs}"
COOKIE = "session"

app = Flask(__name__)
_lock = threading.RLock()


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def sign_uid(uid: int) -> str:
    # The bug: the signature covers only the user id.  name/role are not
    # authenticated, so changing them keeps the token valid.
    return hmac.new(SIGNING_KEY, str(uid).encode("ascii"), hashlib.sha256).hexdigest()


def issue_token(user: dict[str, Any]) -> str:
    payload = {
        "uid": user["uid"],
        "name": user["name"],
        "role": user.get("role", "user"),
        "iat": int(time.time()),
    }
    body = b64u_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{body}.{sign_uid(user['uid'])}"


def read_token(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    try:
        payload = json.loads(b64u_decode(body))
        uid = int(payload["uid"])
    except (ValueError, KeyError, json.JSONDecodeError, TypeError, binascii.Error):
        return None
    if not hmac.compare_digest(signature, sign_uid(uid)):
        return None
    return payload


def current_user() -> dict[str, Any] | None:
    return read_token(request.cookies.get(COOKIE))


# ---------------------------------------------------------------------------
# Tiny user store
# ---------------------------------------------------------------------------
def _default_users() -> dict[str, dict[str, Any]]:
    return {
        "test": {
            "uid": 1,
            "name": "test",
            "role": "user",
            "password_hash": generate_password_hash("test123"),
        }
    }


def load_users() -> dict[str, dict[str, Any]]:
    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock:
        try:
            with open(USERS_PATH, encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and data:
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        users = _default_users()
        save_users(users)
        return users


def save_users(users: dict[str, dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    temporary = f"{USERS_PATH}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(users, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, USERS_PATH)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
LOGIN_PAGE = """
<div class="grid">
<div class="card"><div class="hd">Вхід<span class="sub">POST /login</span></div><div class="bd">
  <form method="POST" action="/login">
    <div class="field"><label for="name">Позивний</label>
      <input id="name" class="input" name="name" autocomplete="username" required></div>
    <div class="field"><label for="password">Пароль</label>
      <input id="password" class="input" type="password" name="password" autocomplete="current-password" required></div>
    <button class="btn primary" type="submit">Увійти</button>
  </form>
  <div class="alert info" style="margin-top:1rem">Тестовий оператор: <code>test</code> / <code>test123</code></div>
</div></div>
<div class="card"><div class="hd">Новий оператор</div><div class="bd">
  <form method="POST" action="/register">
    <div class="field"><label for="rname">Позивний (3–24, літери/цифри/_.-)</label>
      <input id="rname" class="input" name="name" pattern="[A-Za-z0-9_.-]{3,24}" required></div>
    <div class="field"><label for="rpassword">Пароль (мін. 6 символів)</label>
      <input id="rpassword" class="input" type="password" name="password" minlength="6" required></div>
    <button class="btn" type="submit">Зареєструватися</button>
  </form>
</div></div>
</div>
"""

DASHBOARD = """
<div class="card"><div class="hd">Сесія<span class="sub">role: {{ role }}</span></div><div class="bd">
  <dl class="kv">
    <dt>UID</dt><dd class="mono">{{ uid }}</dd>
    <dt>Позивний</dt><dd>{{ name }}</dd>
    <dt>Роль</dt><dd><code>{{ role }}</code></dd>
  </dl>
  <p class="muted" style="margin-top:1rem">Ваш підписаний токен (cookie <code>session</code>):</p>
  <pre class="code" id="token">{{ token }}</pre>
  <div class="row" style="margin-top:.75rem">
    <button class="btn sm" data-copy="token" type="button">Копіювати</button>
    <a class="btn" href="/logout">Вийти</a>
    {% if role == 'admin' %}<a class="btn primary" href="/admin">Адмін-панель</a>{% endif %}
  </div>
</div></div>
<div class="card"><div class="hd">Про токен</div><div class="bd">
  <p class="muted">Формат: <code>base64url(payload).HMAC-SHA256</code>. Підпис захищає токен від підміни.</p>
</div></div>
"""

ADMIN_PAGE = """
<div class="card"><div class="hd">Журнал аудиту<span class="sub">admin only</span></div><div class="bd">
  <p>Вітаємо в адмін-панелі. Журнал зберігається у зашифрованому вигляді.</p>
  <dl class="kv">
    <dt>Файл</dt><dd><code>audit.log.enc</code></dd>
    <dt>Шифрування</dt><dd>AES-256-CBC, PKCS#7</dd>
    <dt>Ключ</dt><dd><code>SHA-256(session token)</code> — 32 сирі байти</dd>
    <dt>IV</dt><dd>перші 16 байтів файлу</dd>
  </dl>
  <div class="row" style="margin-top:1rem">
    <a class="btn primary" href="/admin/audit.log.enc">Завантажити audit.log.enc</a>
    <a class="btn" href="/dashboard">Назад</a>
  </div>
  <div class="alert info" style="margin-top:1rem">
    Підказка: <code>key = sha256(token.encode()).digest()</code>, далі AES-CBC і зняти PKCS#7 padding.
    Ваш поточний токен показано на сторінці <a href="/dashboard">/dashboard</a>.
  </div>
</div></div>
"""


def render(body: str, *, title: str, heading: str, tag: str, lead: str = "", status: int = 200, **ctx):
    html = page(
        body,
        title=title,
        heading=heading,
        tag=tag,
        node="titan-node-12 · token-forge",
        lead=lead,
        **ctx,
    )
    return html, status


def set_session(response, token: str):
    response.set_cookie(COOKIE, token, httponly=True, samesite="Lax", max_age=86400)
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    user = current_user()
    if user:
        return redirect("/dashboard")
    return render(
        LOGIN_PAGE,
        title="Token Forge",
        heading="Token Forge",
        tag="12 · Web",
        lead="Внутрішній портал операторів Titan. Увійдіть або створіть обліковий запис.",
    )


@app.get("/health")
def health():
    return "ok"


@app.post("/login")
def login():
    name = (request.form.get("name") or "").strip()
    password = request.form.get("password") or ""
    users = load_users()
    user = users.get(name)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render(
            LOGIN_PAGE,
            title="Token Forge",
            heading="Вхід відхилено",
            tag="12 · Web",
            lead="Невірний позивний або пароль.",
            status=401,
        )
    response = make_response(redirect("/dashboard"))
    return set_session(response, issue_token(user))


@app.post("/register")
def register():
    name = (request.form.get("name") or "").strip()
    password = request.form.get("password") or ""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,24}", name):
        return render(
            LOGIN_PAGE,
            title="Token Forge",
            heading="Реєстрація",
            tag="12 · Web",
            lead="Позивний: 3–24 символи, літери/цифри/_.-",
            status=400,
        )
    if len(password) < 6:
        return render(
            LOGIN_PAGE,
            title="Token Forge",
            heading="Реєстрація",
            tag="12 · Web",
            lead="Пароль має містити щонайменше 6 символів.",
            status=400,
        )

    with _lock:
        users = load_users()
        if name in users:
            return render(
                LOGIN_PAGE,
                title="Token Forge",
                heading="Реєстрація",
                tag="12 · Web",
                lead="Такий позивний уже зайнятий.",
                status=409,
            )
        uid = max((int(item["uid"]) for item in users.values()), default=0) + 1
        users[name] = {
            "uid": uid,
            "name": name,
            "role": "user",
            "password_hash": generate_password_hash(password),
        }
        save_users(users)

    response = make_response(redirect("/dashboard"))
    return set_session(response, issue_token(users[name]))


@app.get("/dashboard")
def dashboard():
    user = current_user()
    if user is None:
        return redirect("/")
    token = request.cookies.get(COOKIE, "")
    return render(
        DASHBOARD,
        title="Token Forge",
        heading="Консоль оператора",
        tag="12 · Web",
        lead="Ваш підписаний токен сесії.",
        uid=user.get("uid"),
        name=user.get("name"),
        role=user.get("role"),
        token=token,
    )


@app.get("/admin")
def admin():
    user = current_user()
    if user is None:
        return redirect("/")
    if user.get("role") != "admin":
        return render(
            "<div class=\"card\"><div class=\"hd\">Доступ заборонено</div><div class=\"bd\">"
            "<div class=\"alert bad\">Потрібна роль <code>admin</code>.</div>"
            "<a class=\"btn\" href=\"/dashboard\">Назад</a></div></div>",
            title="Token Forge",
            heading="403",
            tag="12 · Web",
            status=403,
        )
    return render(
        ADMIN_PAGE,
        title="Token Forge",
        heading="Адмін-панель",
        tag="12 · Web",
        lead="Журнал аудиту доступний лише адміністраторам.",
    )


def audit_plaintext() -> bytes:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines = [
        f"[{now}] service=token-forge event=startup version=2.4",
        f"[{now}] auth user=test uid=1 result=ok",
        f"[{now}] warn signature_scope=uid token_v2=true",
        f"[{now}] auth user=test uid=1 role=admin result=ok",
        f"[{now}] audit export requested by=admin",
        f"[{now}] FLAG {FLAG}",
        f"[{now}] service=token-forge event=shutdown",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


@app.get("/admin/audit.log.enc")
def audit_log():
    user = current_user()
    if user is None or user.get("role") != "admin":
        return "Forbidden", 403

    token = request.cookies.get(COOKIE, "")
    key = hashlib.sha256(token.encode("utf-8")).digest()  # 32-byte AES key
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(audit_plaintext()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    payload = iv + ciphertext

    return Response(
        payload,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=audit.log.enc"},
    )


@app.get("/logout")
def logout():
    response = make_response(redirect("/"))
    response.delete_cookie(COOKIE)
    return response


if __name__ == "__main__":
    load_users()
    app.run(host="0.0.0.0", port=5000)
