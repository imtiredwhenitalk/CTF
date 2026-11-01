import subprocess
import re
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def sanitize_username(username):
    if re.match(r"^[a-zA-Z0-9_]+$", username):
        return username
    return None

@app.route('/api/vpn/download', methods=['GET'])
def get_vpn_config():
    raw_user = request.args.get('user')
    if not raw_user:
        return "Missing user parameter", 400

    username = sanitize_username(raw_user)
    if not username:
        return "Invalid username format. Use only letters, numbers, and underscores.", 400

    container_name = "openvpn"

    # 1. Перевіряємо, чи є вже такий клієнт в OpenVPN
    check_cmd = f"docker exec {container_name} grep -q {username} /etc/openvpn/pki/index.txt"
    client_exists = subprocess.run(check_cmd, shell=True).returncode == 0

    if not client_exists:
        # 2. Генеруємо нового клієнта без пароля
        gen_cmd = f"docker exec -e EASYRSA_BATCH=1 {container_name} easyrsa build-client-full {username} nopass"
        res = subprocess.run(gen_cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return f"Error generating client certificate: {res.stderr}", 500

    # 3. Витягуємо готовий .ovpn файл
    get_cmd = f"docker exec {container_name} ovpn_getclient {username}"
    result = subprocess.run(get_cmd, shell=True, capture_output=True, text=True)

    if "BEGIN CERTIFICATE" not in result.stdout:
        return "Error extracting VPN config file.", 500

    return Response(
        result.stdout,
        mimetype="application/x-openvpn-profile",
        headers={"Content-Disposition": f"attachment;filename={username}_lntu.ovpn"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
