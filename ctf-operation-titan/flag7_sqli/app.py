from flask import Flask, request, render_template_string
import sqlite3, re
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.execute('CREATE TABLE users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}')")
    return conn
db = init_db()

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><title>Titan Staff Directory</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>Staff Lookup</h4></div>
        <div class="card-body">
            <form method="GET">
                <input type="text" class="form-control" name="id" placeholder="Enter Staff ID (e.g. 1)">
                <button type="submit" class="btn btn-primary mt-2">Search</button>
            </form>
            <div class="mt-3 text-warning">{{ result }}</div>
        </div>
    </div>
</div></body></html>
'''

@app.route('/')
def index():
    uid = request.args.get('id', '')
    if not uid: return render_template_string(HTML, result="")
    
    # Strict WAF
    if re.search(r"[\s=><]|union|or|and", uid, re.IGNORECASE):
        return render_template_string(HTML, result="WAF Blocked: Malicious input detected!")
    try:
        res = db.execute(f"SELECT username FROM users WHERE id = {uid}").fetchone()
        msg = "User exists in directory." if res else "User not found."
        return render_template_string(HTML, result=msg)
    except: return render_template_string(HTML, result="Database Error.")

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
