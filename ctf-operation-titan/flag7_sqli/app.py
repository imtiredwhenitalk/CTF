from flask import Flask, request
import sqlite3, re
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.execute('CREATE TABLE users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT INTO users VALUES (1, 'admin', 'CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}')")
    return conn
db = init_db()

@app.route('/')
def index():
    uid = request.args.get('id', '1')
    # WAF: block space, union, or, and, =, >
    if re.search(r"[\s=><]|union|or|and", uid, re.IGNORECASE):
        return "WAF Blocked!"
    try:
        # Vulnerable query
        res = db.execute(f"SELECT username FROM users WHERE id = {uid}").fetchone()
        return "User exists" if res else "User not found"
    except: return "Error"

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
