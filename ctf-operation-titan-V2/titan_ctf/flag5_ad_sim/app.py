import hashlib
import itertools

from flask import Flask, render_template_string

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head><title>Titan Active Directory Simulator</title></head>
<body style="font-family: monospace; background: #111; color: #0f0; padding: 20px;">
    <h2>[+] Active Directory Kerberos Service Console</h2>
    <p>Target Service: svc_backup@TITAN.LOCAL</p>
    <form method="POST" action="/kerberoast">
        <label>Request TGS Ticket for SPN:</label><br><br>
        <input type="text" name="spn" value="MSSQLSvc/db.titan.local:1433" style="width: 300px;">
        <button type="submit">Request Ticket</button>
    </form>
    {% if ticket %}
    <h3>[+] TGS-REP Hash Received:</h3>
    <textarea rows="4" cols="80">{{ ticket }}</textarea>
    <p>Hint: це навчальна імітація, не справжній krb5tgs-формат John/Hashcat.
       Частина після останньої <code>*</code> - це пароль службового акаунта,
       зашифрований XOR-ключем, що залежить від SPN і realm вище.</p>
    {% endif %}
</body>
</html>
'''

SPN = "MSSQLSvc/db.titan.local:1433"
REALM = "TITAN.LOCAL"
ACCOUNT = "svc_backup"
PASSWORD = "CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}"


def derive_key():
    # Ключ XOR залежить лише від даних, які й так видно на сторінці (SPN + realm)
    return hashlib.sha256(f"{SPN}${REALM}".encode()).digest()


def encrypted_password_hex():
    key = derive_key()
    enc = bytes(b ^ k for b, k in zip(PASSWORD.encode(), itertools.cycle(key)))
    return enc.hex()


@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML)


@app.route('/kerberoast', methods=['POST'])
def kerberoast():
    ticket = f"$krb5tgs$23$*{ACCOUNT}${REALM}${SPN}*${encrypted_password_hex()}"
    return render_template_string(HTML, ticket=ticket)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
