import sqlite3
from flask import Flask, request, render_template_string
app = Flask(__name__)
def init_db():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE products (id INTEGER, name TEXT)')
    conn.execute("INSERT INTO products VALUES (1, 'Zatvor')")
    conn.execute('CREATE TABLE secrets (id INTEGER, flag TEXT)')
    conn.execute("INSERT INTO secrets VALUES (1, 'CTF{z4tv0r_sqli_byp4ss_m4st3r}')")
    conn.commit()
    return conn
conn = init_db()
@app.route('/')
def search():
    query = request.args.get('q', '')
    try: results = conn.execute(f"SELECT * FROM products WHERE name LIKE '%{query}%'").fetchall()
    except Exception as e: results = [(0, str(e))]
    return str(results)
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
