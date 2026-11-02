from flask import Flask, request, jsonify, render_template_string
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
pem_pub = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
FLAG = "CTF{jwt_4lg_c0nfus10n_byp4ss}"

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><title>Titan API Auth</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>API Gateway v2</h4></div>
        <div class="card-body">
            <p>Access requires a valid JWT Token.</p>
            <ul>
                <li><a href="/pub" class="text-info">Download Public Key</a></li>
                <li><a href="/flag" class="text-info">Access Admin Panel (Requires Authorization Header)</a></li>
            </ul>
        </div>
    </div>
</div></body></html>
'''

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/pub')
def pub(): return pem_pub, 200, {'Content-Type': 'text/plain'}

@app.route('/flag')
def flag():
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing Authorization header"}), 401
    try:
        data = jwt.decode(token, pem_pub, algorithms=["RS256", "HS256"])
        if data.get('role') == 'admin': return FLAG
        return jsonify({"error": "Role must be 'admin'"}), 403
    except Exception as e: return str(e), 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
