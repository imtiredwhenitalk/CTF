from flask import Flask, request, jsonify, render_template_string
import jwt
app = Flask(__name__)
JWT_SECRET = "123456" 
n = 54173879  
e = 65537
FLAG = "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"
encrypted_flag = [pow(ord(c), e, n) for c in FLAG]

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><title>Titan Executive Portal</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>Executive Access</h4></div>
        <div class="card-body">
            <p>Your current session token:</p>
            <pre class="bg-dark p-3 text-success rounded">{{ token }}</pre>
            <p>Send this token in the Authorization header to <code>/admin</code></p>
        </div>
    </div>
</div></body></html>
'''

@app.route('/')
def index():
    token = jwt.encode({"role": "guest"}, JWT_SECRET, algorithm="HS256")
    return render_template_string(HTML, token=token)

@app.route('/admin')
def admin():
    token = request.headers.get('Authorization', '')
    try:
        if jwt.decode(token, JWT_SECRET, algorithms=["HS256"]).get("role") == "admin":
            return jsonify({"msg": "Welcome Admin!", "n": n, "e": e, "enc": encrypted_flag})
    except: pass
    return "Unauthorized", 401

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
