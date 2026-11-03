import os, re, threading
import docker
from docker.errors import DockerException, NotFound
from flask import Flask, request, Response, render_template_string
from flask_cors import CORS

CONTAINER = os.environ.get("OPENVPN_CONTAINER", "openvpn")
USER_RE = re.compile(r"^[A-Za-z0-9_]{1,32}$")

app = Flask(__name__)
CORS(app)
lock = threading.Lock()          # easyrsa must not run twice at the same time

PAGE = """<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Titan VPN</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5" style="max-width:520px">
<div class="card bg-secondary text-light"><div class="card-header"><h4>Operation Titan — VPN</h4></div>
<div class="card-body">
<p>Введіть свій нікнейм (літери, цифри, _), щоб отримати файл <code>.ovpn</code>.</p>
<form method="GET" action="/api/vpn/download">
<input class="form-control mb-3" name="user" pattern="[A-Za-z0-9_]{1,32}" placeholder="nickname" required>
<button class="btn btn-warning" type="submit">Завантажити .ovpn</button>
</form></div></div></div></body></html>"""


def run(cmd, env=None):
    container = docker.from_env().containers.get(CONTAINER)
    code, out = container.exec_run(cmd, environment=env or {})
    return code, out.decode(errors="replace")


@app.route("/")
def index():
    return render_template_string(PAGE)


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
    app.run(host="10.10.10.10", port=5050)
