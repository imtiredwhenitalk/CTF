import subprocess, re
from flask import Flask, request, Response
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route('/api/vpn/download')
def get_vpn():
    user = request.args.get('user')
    if not user or not re.match(r"^[a-zA-Z0-9_]+$", user): return "Invalid user", 400
    if subprocess.run(f"docker exec openvpn grep -q {user} /etc/openvpn/pki/index.txt", shell=True).returncode != 0:
        subprocess.run(f"docker exec -e EASYRSA_BATCH=1 openvpn easyrsa build-client-full {user} nopass", shell=True)
    res = subprocess.run(f"docker exec openvpn ovpn_getclient {user}", shell=True, capture_output=True, text=True)
    return Response(res.stdout, mimetype="application/x-openvpn-profile", headers={"Content-Disposition": f"attachment;filename={user}.ovpn"})
if __name__ == '__main__': app.run(host='0.0.0.0', port=5050)
