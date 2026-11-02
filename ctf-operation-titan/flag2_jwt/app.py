from flask import Flask, request, jsonify
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
# Generate RSA keypair on boot
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
pem_pub = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
pem_priv = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()).decode()

FLAG = "CTF{jwt_4lg_c0nfus10n_byp4ss}"

@app.route('/')
def index():
    return "API Online. Get public key at /pub. Access /flag with admin JWT."

@app.route('/pub')
def pub():
    return pem_pub, 200, {'Content-Type': 'text/plain'}

@app.route('/flag')
def flag():
    token = request.headers.get('Authorization')
    if not token: return "Missing token", 401
    try:
        # VULNERABILITY: Accepts both RS256 and HS256, uses the public key string for verification in both cases!
        # If attacker sends HS256 signed with the PEM string, it works.
        data = jwt.decode(token, pem_pub, algorithms=["RS256", "HS256"])
        if data.get('role') == 'admin':
            return FLAG
        return "Not admin"
    except Exception as e:
        return str(e), 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
