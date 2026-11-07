from flask import Flask, request
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from titan_ui import page

app = Flask(__name__)

FLAG_FILE_PATH = "/etc/secret_flag_1337.txt"
WATERMARK_URL = os.environ.get("TITAN_WATERMARK_URL", "http://watermark:5060").rstrip("/")
CHALLENGE_ID = os.environ.get("TITAN_CHALLENGE_ID", "lfi_challenge")

BODY = '''
<div class="card"><div class="hd">Перегляд документа<span class="sub">GET /?file=</span></div><div class="bd">
  <div class="row" style="margin-bottom:1rem">
    <a class="btn" href="/?file=welcome.txt">Відкрити welcome.txt</a>
  </div>
  <pre class="code plain">{{ content }}</pre>
</div></div>
'''


def view(content):
    return page(BODY, title="Docs", heading="Document Server", tag="10 · LFI",
                node="titan-node-10 · docs", lead="Внутрішнє сховище документів Titan.", content=content)


def flag_for_client(client_ip: str) -> str:
    """Ask the internal watermark service for this VPN address's flag.

    The HMAC secret is deliberately not present in this container: the LFI
    challenge is vulnerable to RCE, so a locally stored key could be stolen.
    """
    query = urllib.parse.urlencode({"ip": client_ip, "challenge": CHALLENGE_ID})
    url = f"{WATERMARK_URL}/flag?{query}"
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("ok") and payload.get("flag"):
            return payload["flag"]
        return "Flag service returned an unexpected response."
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("message") or payload.get("error") or "access denied"
        except Exception:
            message = f"HTTP {exc.code}"
        return f"{message}\n\nАдреса запиту: {client_ip}"
    except Exception as exc:  # noqa: BLE001
        return f"Flag service is unavailable: {exc}"


@app.route('/')
def index():
    file = request.args.get('file', '')
    if not file:
        return view("Select a file to read.")
    if '..' in file:
        return view("Hacking Attempt Detected!")

    # The target file is virtual: its content is generated for the VPN
    # address that made the request.  Resolve variants such as /etc/./file
    # or /etc//file to the same virtual target.
    if os.path.realpath(file) == FLAG_FILE_PATH:
        client_ip = request.remote_addr or "unknown"
        return view(flag_for_client(client_ip))

    target = os.path.join('/app/files', file)
    try:
        with open(target, 'r') as handle:
            return view(handle.read())
    except Exception:
        return view("File not found.")


if __name__ == '__main__':
    os.makedirs('/app/files', exist_ok=True)
    with open('/app/files/welcome.txt', 'w') as handle:
        handle.write("Titan Document Server V3. All files are stored securely.")
    app.run(host='0.0.0.0', port=5000)
