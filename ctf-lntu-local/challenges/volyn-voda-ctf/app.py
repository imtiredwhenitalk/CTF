from flask import Flask, request, jsonify, render_template_string
app = Flask(__name__)
USERS = {"1001": {"name": "Test"}, "1337": {"name": "Admin", "flag": "CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}"}}
HTML = '''<body><form action="/user"><input name="id"><button>Search</button></form> <pre>{{ data }}</pre></body>'''
@app.route('/')
def index(): return render_template_string(HTML)
@app.route('/user')
def get_user():
    user = USERS.get(request.args.get('id', ''))
    return render_template_string(HTML, data=jsonify(user).get_data(as_text=True) if user else "Not found")
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
