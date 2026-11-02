from flask import Flask, request, render_template_string
import pickle, base64, hmac, hashlib
app = Flask(__name__)
SECRET = b"titan_weak_key_123"

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><title>Titan HR Portal</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>Employee Portal Sync</h4></div>
        <div class="card-body">
            <form method="POST" action="/upload">
                <div class="mb-3">
                    <label class="form-label">Signature (SHA256)</label>
                    <input type="text" class="form-control" name="sign" placeholder="HMAC signature">
                </div>
                <div class="mb-3">
                    <label class="form-label">Payload (Base64 Pickle)</label>
                    <input type="text" class="form-control" name="payload" placeholder="Base64 encoded data">
                </div>
                <button type="submit" class="btn btn-primary">Sync Profile</button>
            </form>
            <br>
            <a href="/source" class="text-info">View Sync Source Code</a>
        </div>
    </div>
</div></body></html>
'''
@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/source')
def source(): return open(__file__).read(), 200, {'Content-Type': 'text/plain'}

@app.route('/upload', methods=['POST'])
def upload():
    sign = request.form.get('sign', '')
    payload = request.form.get('payload', '')
    expected_sign = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    if sign != expected_sign: return "Invalid HMAC signature!"
    try:
        obj = pickle.loads(base64.b64decode(payload))
        return f"Hello, {obj.name}"
    except Exception as e: return f"Error: {e}"

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
