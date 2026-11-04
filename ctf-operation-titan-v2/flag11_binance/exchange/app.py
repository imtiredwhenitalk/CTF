import hashlib
import hmac

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Справжній ключ, з яким буде порівнюватись запит
API_KEY = "BNC-ADM-88912-SECRET"
WALLET_ID = "CW-BTC-994100"

# Прапор зашифровано: Base64( XOR(flag, "kopiko") )
ENCRYPTED_FLAG_B64 = "KDs2EgleBVseClgwA1sTAlgLNAxABQ8wHFscBVgbNBwEWQdcBRI="

HTML_INDEX = '''
<!DOCTYPE html>
<html>
<head>
    <title>Binance V3 API Gateway</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0b0e11; color: #eaecef; padding: 50px; text-align: center; }
        .box { background: #1e2329; padding: 40px; border-radius: 8px; display: inline-block; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        h1 { color: #fcd535; font-size: 2.5rem; margin-bottom: 10px; }
        p { color: #848e9c; font-size: 1.1rem; }
        .code { background: #000; padding: 15px; border-radius: 4px; font-family: monospace; color: #22c55e; text-align: left; margin-top: 20px; }
    </style>
    <!-- DEBUG_KEY: sLEdQ_xEehlbilF24xTA1as2Qnts26JjHaRS7F6csCQ= (Keep this safe, slurr!) -->
</head>
<body>
    <div class="box">
        <h1>B-Exchange API V3</h1>
        <p>System Status: ONLINE</p>
        <p>Market Data Gateway is active. Private routes require authentication.</p>
        <div class="code">
            > Endpoints available:<br>
            - GET /api/v3/ticker<br>
            - POST /api/v3/wallet/withdraw (Auth Required)
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_INDEX)

@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /api/v3/internal/debug\n"

@app.route('/api/v3/ticker')
def ticker():
    return jsonify({"symbol": "BTCUSDT", "price": "98450.00"})

@app.route('/api/v3/internal/debug')
def debug():
    # Vulnerability: Information Disclosure (Encrypted payload)
    return jsonify({
        "status": "debug_mode_enabled",
        "encryption": "Fernet (AES-128-CBC)",
        "encrypted_admin_key": "gAAAAABq57o2KZnSXrJWzvTjEdFZEyCJ8YvZKMRpFjiRZAoOnSUxVPO3mRCeUErYq_RqU87FVG72ddxGAt2vIzmjE1BKmmLayzOP5WQMB8tGCOvEyn_VOrI=",
        "target_cold_wallet": WALLET_ID,
        "hint": "Find the AES master key in the frontend, decrypt the admin_key, then sign the wallet ID before withdrawing."
    })

@app.route('/api/v3/wallet/withdraw', methods=['POST'])
def withdraw():
    provided_key = request.headers.get('X-API-Key')
    if not provided_key or provided_key != API_KEY:
        return jsonify({"error": "Unauthorized. Invalid or missing X-API-Key header."}), 401
    
    data = request.get_json(silent=True)
    if not data or data.get('wallet_id') != WALLET_ID:
        return jsonify({"error": "Invalid wallet ID specified."}), 400

    provided_signature = request.headers.get('X-API-Signature', '')
    expected_signature = hmac.new(
        API_KEY.encode(),
        WALLET_ID.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return jsonify({"error": "Invalid wallet authorization signature."}), 403

    return jsonify({
        "success": True,
        "message": "FUNDS TRANSFERRED SUCCESSFULLY.",
        "warning": "Payload encrypted to prevent interception.",
        "flag_algorithm": "Base64 -> XOR (key: kopiko)",
        "encrypted_flag": ENCRYPTED_FLAG_B64
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)