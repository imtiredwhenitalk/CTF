"""Python-версія завдання Flag 2 для локального запуску без Node.js/Docker.
Поведінка та відповіді ідентичні app.js (HS256, слабкий секрет)."""
import datetime

import jwt
from flask import Flask, jsonify, request

app = Flask(__name__)

JWT_SECRET = 'secret123'  # Weak secret for CTF


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Titan Admin API",
        "auth_endpoint": "POST /login (guest/guest)",
        "flag_endpoint": "GET /admin/flag (Requires role: internal_admin)",
    })


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if data.get('username') == 'guest' and data.get('password') == 'guest':
        token = jwt.encode(
            {'username': 'guest', 'role': 'guest',
             'iat': datetime.datetime.now(datetime.timezone.utc),
             'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
            JWT_SECRET, algorithm='HS256')
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/admin/flag', methods=['GET'])
def admin_flag():
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"error": "No token provided"}), 401
    parts = auth.split(' ')
    token = parts[1] if len(parts) > 1 else ''
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return jsonify({"error": "Invalid token"}), 400
    if decoded.get('role') == 'internal_admin':
        return jsonify({"flag": "CTF{jwt_s3cr3ts_sh0uld_n3v3r_b3_w34k}"})
    return jsonify({"error": "Forbidden. Requires role: internal_admin"}), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
