import os, re, threading
import docker
from docker.errors import DockerException, NotFound
from flask import Flask, request, Response
from titan_ui import page
from flask_cors import CORS

CONTAINER = os.environ.get("OPENVPN_CONTAINER", "openvpn")
USER_RE = re.compile(r"^[A-Za-z0-9_]{1,32}$")

app = Flask(__name__)
CORS(app)
lock = threading.Lock()          # easyrsa must not run twice at the same time

PAGE = """
<div class="grid">
<div class="card"><div class="hd">Отримати профіль<span class="sub">OpenVPN · UDP 1194</span></div><div class="bd">
  <form method="GET" action="/api/vpn/download">
    <div class="field"><label for="user">Нікнейм (літери, цифри, _; до 32 символів)</label>
      <input id="user" class="input" name="user" pattern="[A-Za-z0-9_]{1,32}" placeholder="nickname" autocomplete="off" required></div>
    <button class="btn primary" type="submit">Завантажити .ovpn</button>
  </form>
  <div class="alert info">Один нікнейм — один сертифікат. Повторний запит видасть той самий профіль.</div>
</div></div>
<div class="card"><div class="hd">Підключення</div><div class="bd">
  <pre class="code plain">sudo openvpn --config nickname.ovpn</pre>
  <p class="muted">Через VPN маршрутизується лише мережа завдань <code>172.28.0.0/24</code>; решта трафіку йде як зазвичай.</p>
</div></div>
</div>
<div class="card"><div class="hd">Адреси завдань у VPN</div><div class="bd">
<table class="t"><tr><th>#</th><th>Завдання</th><th>Адреса</th></tr>
{% for n, name, url in tasks %}<tr><td class="mono">{{ n }}</td><td>{{ name }}</td><td><code>{{ url }}</code></td></tr>{% endfor %}
</table></div></div>
"""

TASKS = [("01", "Git Leak & XOR", "http://172.28.0.11"), ("02", "JWT Alg Confusion", "http://172.28.0.12:5000"),
         ("03", "LFSR Reversing", "http://172.28.0.13"), ("04", "Pickle & HMAC", "http://172.28.0.14:5000"),
         ("05", "JWT & RSA", "http://172.28.0.15:5000"), ("06", "AES ECB Block", "http://172.28.0.16:5000"),
         ("07", "Blind SQLi WAF", "http://172.28.0.17:5000"), ("08", "RSA Wiener's Attack", "http://172.28.0.18"),
         ("09", "Hidden Archive", "http://172.28.0.19"), ("10", "LFI to RCE", "http://172.28.0.20:5000")]


def run(cmd, env=None):
    container = docker.from_env().containers.get(CONTAINER)
    code, out = container.exec_run(cmd, environment=env or {})
    return code, out.decode(errors="replace")


@app.route("/")
def index():
    return page(PAGE, title="VPN", heading="Доступ до лабораторної мережі", tag="VPN · Portal",
                node="titan-vpn · portal", lead="Отримайте особистий .ovpn, щоб дістатися до завдань.", tasks=TASKS)


@app.route("/health")
def health():
    return "ok"


@app.route("/api/vpn/download")
def get_vpn():
    user = request.args.get("user", "")
    if not USER_RE.match(user):
        return "Invalid user (use letters, digits, underscore; max 32)", 400
    try:
        with lock:
            code, _ = run(["test", "-f", f"/etc/openvpn/pki/issued/{user}.crt"])
            if code != 0:
                code, out = run(["easyrsa", "build-client-full", user, "nopass"],
                                {"EASYRSA_BATCH": "1"})
                if code != 0:
                    return f"Failed to create certificate:\n{out}", 500
            code, conf = run(["ovpn_getclient", user])
        if code != 0 or "client" not in conf:
            return f"Failed to build profile:\n{conf}", 500
    except NotFound:
        return f"Container '{CONTAINER}' is not running", 503
    except DockerException as e:
        return f"Docker error: {e}", 503
    return Response(conf, mimetype="application/x-openvpn-profile",
                    headers={"Content-Disposition": f"attachment; filename={user}.ovpn"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
