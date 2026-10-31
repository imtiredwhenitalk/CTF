from flask import Flask, render_template_string, request, jsonify

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
    <p>Hint: Crack with John/Hashcat (krb5tgs / mode 13100). Flag is inside password.</p>
    {% endif %}
</body>
</html>
'''

HASH_FLAG = "$krb5tgs$23$*svc_backup$TITAN.LOCAL$MSSQLSvc/db.titan.local:1433*$CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}"

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML)

@app.route('/kerberoast', methods=['POST'])
def kerberoast():
    return render_template_string(HTML, ticket=HASH_FLAG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
