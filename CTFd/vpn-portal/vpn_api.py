"""Operation Titan VPN portal.

The portal issues one client certificate per CTFd nickname, reserves a fixed
VPN address for that nickname and writes both:

* ``/openvpn/ccd/<common-name>`` — OpenVPN ``ifconfig-push`` directive;
* ``/data/user_registry.csv`` — nickname → VPN IP mapping used by the
  watermark service and the CTFd plugin.

A fixed address is what makes per-user flag watermarking possible: the LFI
challenge sees the real ``10.8.0.x`` source address (the OpenVPN server must
run without NAT for the lab network).
"""
from __future__ import annotations

import csv
import fcntl
import hashlib
import ipaddress
import os
import re
import threading

import docker
from docker.errors import DockerException, NotFound
from flask import Flask, Response, jsonify, request
from titan_ui import page

CONTAINER = os.environ.get("OPENVPN_CONTAINER", "openvpn")
OPENVPN_DIR = os.environ.get("TITAN_OPENVPN_DIR", "/openvpn")
DATA_DIR = os.environ.get("TITAN_DATA_DIR", "/data")
REGISTRY_PATH = os.environ.get("TITAN_REGISTRY", os.path.join(DATA_DIR, "user_registry.csv"))
LOCK_PATH = os.path.join(DATA_DIR, ".registry.lock")
CCD_DIR = os.path.join(OPENVPN_DIR, "ccd")

VPN_NETWORK = ipaddress.ip_network("10.8.0.0/24")
VPN_FIRST = 10
VPN_LAST = 250

USER_RE = re.compile(r"^[^\x00-\x1f\x7f/\\]{1,128}$")
app = Flask(__name__)
_lock = threading.Lock()

PAGE = """
<div class="grid">
<div class="card"><div class="hd">Отримати профіль<span class="sub">OpenVPN · UDP 1194</span></div><div class="bd">
  <form method="GET" action="/issue">
    <div class="field"><label for="user">Нікнейм (той самий, що в CTFd; до 128 символів)</label>
      <input id="user" class="input" name="user" maxlength="128" placeholder="nickname" autocomplete="off" required></div>
    <button class="btn primary" type="submit">Отримати профіль</button>
  </form>
  <div class="alert info">Один нікнейм — один сертифікат і одна постійна VPN-адреса. Повторний запит поверне той самий профіль.</div>
</div></div>
<div class="card"><div class="hd">Як підключитися</div><div class="bd">
  <p class="muted">1. Завантажте <code>nickname.ovpn</code>.<br>
  2. Linux/macOS: <code>sudo openvpn --config nickname.ovpn</code><br>
  3. Windows: імпортуйте файл у OpenVPN GUI та натисніть Connect.</p>
  <p class="muted">Через VPN маршрутизується лише мережа завдань <code>172.28.0.0/24</code>, решта трафіку йде як звичайно.</p>
</div></div>
</div>
<div class="card"><div class="hd">Адреси завдань у VPN</div><div class="bd">
<table class="t"><tr><th>#</th><th>Завдання</th><th>Адреса</th></tr>
{% for n, name, url in tasks %}<tr><td class="mono">{{ n }}</td><td>{{ name }}</td><td><code>{{ url }}</code></td></tr>{% endfor %}
</table>
<div class="alert warn" style="margin-top:1rem">Прапор завдання <b>10. LFI to RCE</b> прив'язаний до вашої VPN-адреси. Якщо відкривати завдання напряму через <code>:8010</code>, прапор не пройде перевірку в CTFd.</div>
</div></div>
"""

RESULT = """
<div class="card"><div class="hd">Профіль готовий<span class="sub">OpenVPN · UDP 1194</span></div><div class="bd">
  <dl class="kv">
    <dt>Нікнейм</dt><dd>{{ nickname }}</dd>
    <dt>VPN-адреса</dt><dd><code>{{ vpn_ip }}</code></dd>
    <dt>Сертифікат</dt><dd class="mono">{{ cn }}</dd>
  </dl>
  <div class="row" style="margin-top:1rem">
    <a class="btn primary" href="/api/vpn/download?user={{ nickname|urlencode }}">Завантажити .ovpn</a>
    <a class="btn" href="/">Назад</a>
  </div>
  <div class="alert info" style="margin-top:1rem">Ваша VPN-адреса — <code>{{ vpn_ip }}</code>. Саме до неї буде прив'язаний прапор завдання 10.</div>
</div></div>
"""

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


def run(cmd, env=None):
    container = docker.from_env().containers.get(CONTAINER)
    code, out = container.exec_run(cmd, environment=env or {})
    return code, out.decode(errors="replace")


def safe_cn(nickname: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", nickname)[:24] or "user"
    digest = hashlib.sha1(nickname.encode("utf-8")).hexdigest()[:8]
    return f"ctfd_{safe}_{digest}"


def load_registry() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    try:
        with open(REGISTRY_PATH, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or row[0].strip().startswith("#"):
                    continue
                if row[0].strip().lower() == "nickname":
                    continue
                if len(row) < 3:
                    continue
                nickname, cn, vpn_ip = (cell.strip() for cell in row[:3])
                if nickname and cn and vpn_ip:
                    entries.append({"nickname": nickname, "cn": cn, "vpn_ip": vpn_ip})
    except FileNotFoundError:
        pass
    return entries


def save_registry(entries: list[dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(REGISTRY_PATH) or ".", exist_ok=True)
    temporary = f"{REGISTRY_PATH}.tmp"
    with open(temporary, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for entry in entries:
            writer.writerow([entry["nickname"], entry["cn"], entry["vpn_ip"]])
    os.replace(temporary, REGISTRY_PATH)


def write_ccd(cn: str, vpn_ip: str) -> None:
    os.makedirs(CCD_DIR, exist_ok=True)
    temporary = os.path.join(CCD_DIR, f".{cn}.tmp")
    with open(temporary, "w", encoding="ascii") as handle:
        handle.write(f"ifconfig-push {vpn_ip} 255.255.255.0\n")
    os.replace(temporary, os.path.join(CCD_DIR, cn))


def next_free_ip(entries: list[dict[str, str]]) -> str:
    used = {entry["vpn_ip"] for entry in entries}
    for last_octet in range(VPN_FIRST, VPN_LAST + 1):
        candidate = str(VPN_NETWORK.network_address + last_octet)
        if candidate not in used:
            return candidate
    raise RuntimeError("VPN address pool is exhausted (10.8.0.10–10.8.0.250)")


def ensure_profile(nickname: str) -> dict[str, str]:
    """Return the existing profile or create cert + CCD + registry entry."""
    if not USER_RE.match(nickname):
        raise ValueError("Invalid nickname (1–128 characters; '/' and '\\' are not allowed)")

    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock, open(LOCK_PATH, "a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        entries = load_registry()
        entry = next((item for item in entries if item["nickname"] == nickname), None)

        if entry is None:
            entry = {
                "nickname": nickname,
                "cn": safe_cn(nickname),
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
        if not any(item["nickname"] == nickname for item in entries):
            entries.append(entry)
            save_registry(entries)
        return entry


def build_profile(cn: str) -> str:
    code, conf = run(["ovpn_getclient", cn])
    if code != 0 or "client" not in conf:
        raise RuntimeError(f"ovpn_getclient failed:\n{conf}")
    return conf


@app.route("/")
def index():
    return page(
        PAGE,
        title="VPN",
        heading="Доступ до лабораторної мережі",
        tag="VPN · Portal",
        node="titan-vpn · portal",
        lead="Отримайте особистий .ovpn із постійною VPN-адресою, щоб дістатися до завдань.",
        tasks=TASKS,
    )


@app.route("/health")
def health():
    return "ok"


@app.route("/issue")
def issue():
    nickname = (request.args.get("user") or "").strip()
    try:
        entry = ensure_profile(nickname)
    except ValueError as exc:
        return page(
            '<div class="card"><div class="hd">Помилка</div><div class="bd">'
            f'<div class="alert bad">{{{{ error }}}}</div><a class="btn" href="/">Назад</a>'
            "</div></div>",
            title="VPN",
            heading="Не вдалося створити профіль",
            tag="VPN · Portal",
            node="titan-vpn · portal",
            error=str(exc),
        ), 400
    except (RuntimeError, NotFound, DockerException) as exc:
        return page(
            '<div class="card"><div class="hd">Помилка</div><div class="bd">'
            f'<div class="alert bad">{{{{ error }}}}</div><a class="btn" href="/">Назад</a>'
            "</div></div>",
            title="VPN",
            heading="OpenVPN недоступний",
            tag="VPN · Portal",
            node="titan-vpn · portal",
            error=str(exc),
        ), 503

    return page(
        RESULT,
        title="VPN",
        heading="Профіль готовий",
        tag="VPN · Portal",
        node="titan-vpn · portal",
        nickname=entry["nickname"],
        vpn_ip=entry["vpn_ip"],
        cn=entry["cn"],
        tasks=TASKS,
    )


@app.route("/api/vpn/info")
def vpn_info():
    nickname = (request.args.get("user") or "").strip()
    try:
        entry = ensure_profile(nickname)
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400
    except (RuntimeError, NotFound, DockerException) as exc:
        return jsonify(ok=False, error=str(exc)), 503
    return jsonify(
        ok=True,
        nickname=entry["nickname"],
        cn=entry["cn"],
        vpn_ip=entry["vpn_ip"],
        profile_url=f"/api/vpn/download?user={nickname}",
    )


@app.route("/api/vpn/download")
def download():
    nickname = (request.args.get("user") or "").strip()
    try:
        entry = ensure_profile(nickname)
        conf = build_profile(entry["cn"])
    except ValueError as exc:
        return str(exc), 400
    except (RuntimeError, NotFound, DockerException) as exc:
        return f"Failed to build profile:\n{exc}", 503

    filename = re.sub(r"[^A-Za-z0-9_.-]", "_", nickname).strip("._") or "profile"
    filename = f"{filename[:64]}.ovpn"
    return Response(
        conf,
        mimetype="application/x-openvpn-profile",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
