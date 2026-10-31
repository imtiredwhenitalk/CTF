from flask import Flask, request, render_template_string, redirect, url_for, make_response

app = Flask(__name__)

posts = [
    {"id": 1, "title": "Ласкаво просимо до Блогу Кібербезпеки ЛНТУ", "content": "Тут студенти та викладачі публікують актуальні новини та звіти."}
]

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ЛНТУ Cyber Blog</title>
    <style>
        body { font-family: Arial, sans-serif; background: #18181b; color: #f4f4f5; padding: 30px; }
        .container { max-width: 800px; margin: auto; }
        .post { background: #27272a; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #3f3f46; }
        h1 { color: #a855f7; }
        input, textarea, button { width: 100%; padding: 10px; margin-top: 10px; background: #09090b; color: #fff; border: 1px solid #3f3f46; border-radius: 4px; }
        button { background: #a855f7; color: #fff; font-weight: bold; cursor: pointer; border: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ LNTU Cyber Security Blog</h1>
        <a href="/new" style="color: #c084fc;">+ Написати новий пост</a>
        <hr style="border-color: #3f3f46; margin: 20px 0;">
        {% for p in posts %}
        <div class="post">
            <h2>{{ p.title }}</h2>
            <!-- Vulnerable: raw unsafe HTML rendering -->
            <div>{{ p.content | safe }}</div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

NEW_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Створити пост</title>
    <style>
        body { font-family: Arial, sans-serif; background: #18181b; color: #f4f4f5; padding: 30px; }
        .container { max-width: 600px; margin: auto; background: #27272a; padding: 25px; border-radius: 8px; }
        input, textarea, button { width: 100%; padding: 10px; margin-top: 10px; background: #09090b; color: #fff; border: 1px solid #3f3f46; }
        button { background: #a855f7; color: #fff; font-weight: bold; cursor: pointer; border: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Новий пост у Блог</h2>
        <form method="POST">
            <label>Заголовок:</label>
            <input type="text" name="title" required>
            <label>Вміст (HTML підтримується):</label>
            <textarea name="content" rows="6" required></textarea>
            <button type="submit">Опублікувати</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    resp = make_response(render_template_string(HTML, posts=posts))
    # Admin cookie contains the flag
    resp.set_cookie('admin_session', 'CTF{xss_st0r3d_4dm1n_c00k13_st34l}')
    return resp

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        posts.append({"id": len(posts)+1, "title": title, "content": content})
        return redirect(url_for('index'))
    return render_template_string(NEW_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
