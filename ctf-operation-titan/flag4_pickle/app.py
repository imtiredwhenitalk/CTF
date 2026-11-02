from flask import Flask, request, render_template_string
import pickle, base64, hmac, hashlib
app = Flask(__name__)
SECRET = b"titan_weak_key_123"

HTML = '''
<h2>Titan HR Portal</h2><form method="POST" action="/upload">
  Signature (SHA256): <input type="text" name="sign"><br>
  Payload (Base64): <input type="text" name="payload"><br><input type="submit">
</form><a href="/source">Source</a>
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
