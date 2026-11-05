from flask import Flask, request, render_template_string, make_response
app = Flask(__name__)
posts = [{"title": "Hello", "content": "Welcome"}]
HTML = '''<body>{% for p in posts %}<div>{{ p.content | safe }}</div>{% endfor %}</body>'''
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': posts.append({"title": request.form.get('title'), "content": request.form.get('content')})
    resp = make_response(render_template_string(HTML, posts=posts))
    resp.set_cookie('admin_session', 'CTF{xss_st0r3d_4dm1n_c00k13_st34l}')
    return resp
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
