"""Operation Titan VPN portal.

The portal authenticates a *team name* and a password that the organisers hand
to team captains.  On success it issues one client certificate per team,
reserves a fixed VPN address and writes both:

* ``/openvpn/ccd/<common-name>`` — OpenVPN ``ifconfig-push`` directive;
* ``/data/user_registry.csv`` — team → VPN IP mapping used by the watermark
  service and the CTFd plugin.

A fixed address is what makes per-team flag watermarking possible: the LFI
challenge sees the real ``10.8.0.x`` source address (the OpenVPN server must
run without NAT for the lab network).

Credentials live in ``/data/team_credentials.json`` and are managed with
``admin_teams.py`` (see README).  The CTFd username must match the team name,
because the watermark plugin verifies flags for the logged-in CTFd user.
"""
from __future__ import annotations

import csv
import fcntl
import hashlib
import ipaddress
import os
import re
import secrets
import threading
import time
from datetime import timedelta

import docker
import team_auth
from docker.errors import DockerException, NotFound
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from titan_ui import page

CONTAINER = os.environ.get("OPENVPN_CONTAINER", "openvpn")
OPENVPN_DIR = os.environ.get("TITAN_OPENVPN_DIR", "/openvpn")
DATA_DIR = os.environ.get("TITAN_DATA_DIR", "/data")
REGISTRY_PATH = os.environ.get("TITAN_REGISTRY", os.path.join(DATA_DIR, "user_registry.csv"))
CREDENTIALS_PATH = os.environ.get(
    "TITAN_CREDENTIALS", os.path.join(DATA_DIR, "team_credentials.json")
)
PORTAL_SECRET_FILE = os.environ.get(
    "TITAN_PORTAL_SECRET_FILE", os.path.join(DATA_DIR, "portal_secret.key")
)
LOCK_PATH = os.path.join(DATA_DIR, ".registry.lock")
CCD_DIR = os.path.join(OPENVPN_DIR, "ccd")

VPN_NETWORK = ipaddress.ip_network("10.8.0.0/24")
VPN_FIRST = 10
VPN_LAST = 250

FAIL_WINDOW = 300.0
MAX_FAILURES = 10


def _load_portal_secret() -> str:
    env_secret = os.environ.get("TITAN_PORTAL_SECRET")
    if env_secret:
        return env_secret

    try:
        with open(PORTAL_SECRET_FILE, "r", encoding="utf-8") as handle:
            value = handle.read().strip()
        if value:
            return value
    except FileNotFoundError:
        pass
    except OSError:
        return secrets.token_hex(32)

    value = secrets.token_hex(32)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        fd = os.open(PORTAL_SECRET_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            with open(PORTAL_SECRET_FILE, "r", encoding="utf-8") as handle:
                stored = handle.read().strip()
            if stored:
                return stored
        except OSError:
            pass
    except OSError:
        # A read-only data volume should not prevent the portal from booting;
        # sessions will simply not survive a restart.
        return value
    else:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value + "\n")
    return value


app = Flask(__name__)
app.secret_key = _load_portal_secret()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

_lock = threading.Lock()
_fail_lock = threading.Lock()
_failures: dict[str, list[float]] = {}

TASKS = [
    ("01", "SSTI Comms Console", "http://172.28.0.11:5000"),
    ("02", "JWT Alg Confusion", "http://172.28.0.12:5000"),
    ("03", "LFSR Reversing", "http://172.28.0.13"),
    ("04", "Pickle & HMAC", "http://172.28.0.14:5000"),
    ("05", "JWT & RSA", "http://172.28.0.15:5000"),
    ("06", "AES ECB Oracle", "http://172.28.0.16:5000"),
    ("07", "Blind SQLi WAF", "http://172.28.0.17:5000"),
    ("08", "RSA Wiener's Attack", "http://172.28.0.18"),
    ("09", "Hidden Archive", "http://172.28.0.19"),
    ("10", "LFI to RCE", "http://172.28.0.20:5000"),
    ("11", "Binance API Heist", "http://172.28.0.21"),
    ("12", "Token Forge", "http://172.28.0.22:5000"),
]

TASKS_CARD = """
<div class="card"><div class="hd">Адреси завдань у VPN</div><div class="bd">
<table class="t"><tr><th>#</th><th>Завдання</th><th>Адреса</th></tr>
{% for n, name, url in tasks %}<tr><td class="mono">{{ n }}</td><td>{{ name }}</td><td><code>{{ url }}</code></td></tr>{% endfor %}
</table>
<div class="alert warn" style="margin-top:1rem">Прапор завдання <b>10. LFI to RCE</b> прив'язаний до VPN-адреси команди. Якщо відкривати завдання напряму через <code>:8010</code>, прапор не пройде перевірку в CTFd.</div>
</div></div>
"""

LOGIN = """
<div class="grid">
<div class="card"><div class="hd">Вхід для команди<span class="sub">VPN · captain</span></div><div class="bd">
  {% if error %}<div class="alert bad">{{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <div class="field"><label for="team">Назва команди</label>
      <input id="team" class="input" name="team" maxlength="128" placeholder="team-name" autocomplete="username" required autofocus></div>
    <div class="field"><label for="password">Пароль</label>
      <input id="password" class="input" name="password" type="password" maxlength="256" placeholder="password" autocomplete="current-password" required></div>
    <button class="btn primary" type="submit">Увійти</button>
  </form>
  <div class="alert info">Назва команди — це ім'я користувача в CTFd. Пароль видає організатор.</div>
</div></div>
<div class="card"><div class="hd">Як підключитися</div><div class="bd">
  <p class="muted">1. Увійдіть і завантажте <code>team.ovpn</code>.<br>
  2. Linux/macOS: <code>sudo openvpn --config team.ovpn</code><br>
  3. Windows: імпортуйте файл у OpenVPN GUI та натисніть Connect.</p>
  <p class="muted">Через VPN маршрутизується лише мережа завдань <code>172.28.0.0/24</code>, решта трафіку йде як звичайно.</p>
</div></div>
</div>
""" + TASKS_CARD

DASHBOARD = """
<div class="card"><div class="hd">Команда<span class="sub">{{ team }}</span></div><div class="bd">
  <dl class="kv">
    <dt>Команда</dt><dd>{{ team }}</dd>
    {% if entry %}
    <dt>VPN-адреса</dt><dd><code>{{ entry.vpn_ip }}</code></dd>
    <dt>Сертифікат</dt><dd class="mono">{{ entry.cn }}</dd>
    {% else %}
    <dt>VPN-адреса</dt><dd class="muted">ще не видана</dd>
    {% endif %}
  </dl>
  <div class="row" style="margin-top:1rem">
    <a class="btn primary" href="/issue">Отримати / оновити профіль</a>
    {% if entry %}<a class="btn" href="/api/vpn/download">Завантажити .ovpn</a>{% endif %}
    <form method="POST" action="/logout" style="margin:0"><button class="btn" type="submit">Вийти</button></form>
  </div>
  <div class="alert info" style="margin-top:1rem">Ваша VPN-адреса — <code>{{ entry.vpn_ip if entry else "10.8.0.x" }}</code>. Саме до неї буде прив'язаний прапор завдання 10.</div>
</div></div>
""" + TASKS_CARD

RESULT = """
<div class="card"><div class="hd">Профіль готовий<span class="sub">OpenVPN · UDP 1194</span></div><div class="bd">
  <dl class="kv">
    <dt>Команда</dt><dd>{{ team }}</dd>
    <dt>VPN-адреса</dt><dd><code>{{ entry.vpn_ip }}</code></dd>
    <dt>Сертифікат</dt><dd class="mono">{{ entry.cn }}</dd>
  </dl>
  <div class="row" style="margin-top:1rem">
    <a class="btn primary" href="/api/vpn/download">Завантажити .ovpn</a>
    <a class="btn" href="/">Назад</a>
  </div>
  <div class="alert info" style="margin-top:1rem">Ваша VPN-адреса — <code>{{ entry.vpn_ip }}</code>. Саме до неї буде прив'язаний прапор завдання 10.</div>
</div></div>
""" + TASKS_CARD

ERROR = """
<div class="card"><div class="hd">{{ error_heading }}</div><div class="bd">
  <div class="alert bad">{{ error }}</div>
  <div class="row" style="margin-top:1rem"><a class="btn" href="/">Назад</a></div>
</div></div>
"""


def run(cmd, env=None):
    container = docker.from_env().containers.get(CONTAINER)
    code, out = container.exec_run(cmd, environment=env or {})
    return code, out.decode(errors="replace")


def safe_cn(team: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", team)[:24] or "team"
    digest = hashlib.sha1(team.encode("utf-8")).hexdigest()[:8]
    return f"ctfd_{safe}_{digest}"


def load_registry() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    try:
        with open(REGISTRY_PATH, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or row[0].strip().startswith("#"):
                    continue
                if row[0].strip().lower() in {"team", "nickname"}:
                    continue
                if len(row) < 3:
                    continue
                team, cn, vpn_ip = (cell.strip() for cell in row[:3])
                if team and cn and vpn_ip:
                    entries.append({"team": team, "cn": cn, "vpn_ip": vpn_ip})
    except FileNotFoundError:
        pass
    return entries


def save_registry(entries: list[dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(REGISTRY_PATH) or ".", exist_ok=True)
    temporary = f"{REGISTRY_PATH}.tmp"
    with open(temporary, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for entry in entries:
            writer.writerow([entry["team"], entry["cn"], entry["vpn_ip"]])
    os.replace(temporary, REGISTRY_PATH)


def registry_entry(team: str) -> dict[str, str] | None:
    return next((item for item in load_registry() if item["team"] == team), None)


def write_ccd(cn: str, vpn_ip: str) -> None:
    os.makedirs(CCD_DIR, exist_ok=True)
    temporary = os.path.join(CCD_DIR, f".{cn}.tmp")
    with open(temporary, "w", encoding="ascii") as handle:
        handle.write(f"ifconfig-push {vpn_ip} 255.255.255.0\n")
    # OpenVPN drops privileges to `nobody` before reading CCD files.
    os.chmod(temporary, 0o644)
    os.replace(temporary, os.path.join(CCD_DIR, cn))


def next_free_ip(entries: list[dict[str, str]]) -> str:
    used = {entry["vpn_ip"] for entry in entries}
    for last_octet in range(VPN_FIRST, VPN_LAST + 1):
        candidate = str(VPN_NETWORK.network_address + last_octet)
        if candidate not in used:
            return candidate
    raise RuntimeError("VPN address pool is exhausted (10.8.0.10–10.8.0.250)")


def ensure_profile(team: str) -> dict[str, str]:
    """Return the existing profile or create cert + CCD + registry entry."""
    team = team_auth.validate_team(team)

    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock, open(LOCK_PATH, "a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        entries = load_registry()
        entry = next((item for item in entries if item["team"] == team), None)

        if entry is None:
            entry = {
                "team": team,
                "cn": safe_cn(team),
                "vpn_ip": next_free_ip(entries),
            }

        # The certificate may be missing after a partial reset; rebuild it
        # with the same common name so the reserved VPN address stays valid.
        code, _ = run(["test", "-f", f"/etc/openvpn/pki/issued/{entry['cn']}.crt"])
        if code != 0:
            code, out = run(
                ["easyrsa", "build-client-full", entry["cn"], "nopass"],
                {"EASYRSA_BATCH": "1"},
            )
            if code != 0:
                raise RuntimeError(f"easyrsa failed:\n{out}")

        write_ccd(entry["cn"], entry["vpn_ip"])
        if not any(item["team"] == team for item in entries):
            entries.append(entry)
            save_registry(entries)
        return entry


def build_profile(cn: str) -> str:
    code, conf = run(["ovpn_getclient", cn])
    if code != 0 or "client" not in conf:
        raise RuntimeError(f"ovpn_getclient failed:\n{conf}")
    return conf


# --- authentication -------------------------------------------------------


def _client_key() -> str:
    # The portal is published directly, so do not trust X-Forwarded-For:
    # it would let a client bypass the per-IP failure limit.
    return request.remote_addr or "unknown"


def _too_many_failures(key: str) -> bool:
    now = time.monotonic()
    with _fail_lock:
        attempts = [stamp for stamp in _failures.get(key, ()) if now - stamp < FAIL_WINDOW]
        if attempts:
            _failures[key] = attempts
        else:
            _failures.pop(key, None)
        return len(attempts) >= MAX_FAILURES


def _record_failure(key: str) -> None:
    with _fail_lock:
        _failures.setdefault(key, []).append(time.monotonic())


def _clear_failures(key: str) -> None:
    with _fail_lock:
        _failures.pop(key, None)


def _session_team() -> str | None:
    team = session.get("team")
    if not team:
        return None
    try:
        team = team_auth.validate_team(team)
    except ValueError:
        session.clear()
        return None
    payload = team_auth.load(CREDENTIALS_PATH)
    if team not in payload["teams"]:
        session.clear()
        return None
    return team


def _basic_team() -> str | None:
    auth = request.authorization
    if (
        not auth
        or (auth.type or "").lower() != "basic"
        or not auth.username
        or auth.password is None
    ):
        return None
    try:
        team = team_auth.validate_team(auth.username)
    except ValueError:
        return None
    payload = team_auth.load(CREDENTIALS_PATH)
    return team if team_auth.authenticate(payload, team, auth.password) else None


def current_team() -> str | None:
    team = _session_team()
    if team:
        return team
    return _basic_team()


def unauthorized():
    response = jsonify(
        ok=False,
        error="authentication_required",
        message="Потрібна назва команди та пароль.",
    )
    response.status_code = 401
    response.headers["WWW-Authenticate"] = 'Basic realm="titan-vpn", charset="UTF-8"'
    return response


def render_login(error: str = "", status: int = 200):
    return (
        page(
            LOGIN,
            title="VPN",
            heading="Доступ до лабораторної мережі",
            tag="VPN · Portal",
            node="titan-vpn · portal",
            lead="Увійдіть назвою команди та паролем, який видав організатор.",
            error=error,
            tasks=TASKS,
        ),
        status,
    )


def render_error(message: str, status: int, heading: str = "Помилка"):
    return (
        page(
            ERROR,
            title="VPN",
            heading=heading,
            tag="VPN · Portal",
            node="titan-vpn · portal",
            error_heading=heading,
            error=message,
            tasks=TASKS,
        ),
        status,
    )


# --- routes ---------------------------------------------------------------


@app.route("/")
def index():
    try:
        team = current_team()
    except team_auth.CredentialError as exc:
        return render_login(f"Сховище паролів недоступне: {exc}", 503)

    if not team:
        return render_login()

    try:
        entry = registry_entry(team)
    except OSError:
        entry = None

    return page(
        DASHBOARD,
        title="VPN",
        heading="Профіль команди",
        tag="VPN · Portal",
        node="titan-vpn · portal",
        lead="Отримайте .ovpn із постійною VPN-адресою, щоб дістатися до завдань.",
        team=team,
        entry=entry,
        tasks=TASKS,
    )


@app.route("/health")
def health():
    return "ok"


@app.post("/login")
def login():
    key = _client_key()
    if _too_many_failures(key):
        return render_login("Забагато невдалих спроб. Спробуйте пізніше.", 429)

    team = (request.form.get("team") or "").strip()
    password = request.form.get("password") or ""
    if not team or not password:
        _record_failure(key)
        return render_login("Введіть назву команди та пароль.", 400)

    try:
        payload = team_auth.load(CREDENTIALS_PATH)
    except team_auth.CredentialError as exc:
        return render_login(f"Сховище паролів недоступне: {exc}", 503)

    if not team_auth.authenticate(payload, team, password):
        _record_failure(key)
        return render_login("Невірна назва команди або пароль.", 401)

    _clear_failures(key)
    session.clear()
    session["team"] = team_auth.validate_team(team)
    session.permanent = True
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/issue")
def issue():
    try:
        team = current_team()
    except team_auth.CredentialError as exc:
        return render_error(f"Сховище паролів недоступне: {exc}", 503)

    if not team:
        return redirect(url_for("index"))

    try:
        entry = ensure_profile(team)
    except ValueError as exc:
        return render_error(str(exc), 400, "Не вдалося створити профіль")
    except (RuntimeError, NotFound, DockerException) as exc:
        return render_error(f"OpenVPN недоступний:\n{exc}", 503, "OpenVPN недоступний")

    return page(
        RESULT,
        title="VPN",
        heading="Профіль готовий",
        tag="VPN · Portal",
        node="titan-vpn · portal",
        team=team,
        entry=entry,
        tasks=TASKS,
    )


@app.route("/api/vpn/info")
def vpn_info():
    try:
        team = current_team()
    except team_auth.CredentialError as exc:
        return jsonify(ok=False, error="credential_store_unavailable", message=str(exc)), 503

    if not team:
        return unauthorized()

    try:
        entry = ensure_profile(team)
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400
    except (RuntimeError, NotFound, DockerException) as exc:
        return jsonify(ok=False, error=str(exc)), 503

    return jsonify(
        ok=True,
        team=team,
        cn=entry["cn"],
        vpn_ip=entry["vpn_ip"],
        profile_url="/api/vpn/download",
    )


@app.route("/api/vpn/download")
def download():
    try:
        team = current_team()
    except team_auth.CredentialError as exc:
        return str(exc), 503

    if not team:
        return unauthorized()

    try:
        entry = ensure_profile(team)
        conf = build_profile(entry["cn"])
    except ValueError as exc:
        return str(exc), 400
    except (RuntimeError, NotFound, DockerException) as exc:
        return f"Failed to build profile:\n{exc}", 503

    filename = re.sub(r"[^A-Za-z0-9_.-]", "_", team).strip("._") or "team"
    filename = f"{filename[:64]}.ovpn"
    return Response(
        conf,
        mimetype="application/x-openvpn-profile",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
