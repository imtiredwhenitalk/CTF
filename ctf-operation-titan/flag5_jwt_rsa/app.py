from flask import Flask, request, jsonify
import jwt
app = Flask(__name__)
JWT_SECRET = "123456" # Weak
n = 54173879  # 7919 * 6841
e = 65537
FLAG = "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"
encrypted_flag = [pow(ord(c), e, n) for c in FLAG]

@app.route('/')
def index():
    return jsonify({"token": jwt.encode({"role": "guest"}, JWT_SECRET, algorithm="HS256")})

@app.route('/admin')
def admin():
    token = request.headers.get('Authorization', '')
    try:
        if jwt.decode(token, JWT_SECRET, algorithms=["HS256"]).get("role") == "admin":
            return jsonify({"msg": "Welcome Admin!", "n": n, "e": e, "enc": encrypted_flag, "hint": "Factorize N to get p,q. Find d. Decrypt array."})
    except: pass
    return "Unauthorized", 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
