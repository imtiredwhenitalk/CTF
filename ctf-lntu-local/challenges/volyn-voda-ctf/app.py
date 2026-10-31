from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

USERS = {
    "1001": {"name": "Петро Ковальчук", "address": "вул. Лесі Українки 12, Луцьк", "status": "Оплачено"},
    "1002": {"name": "Олена Мельник", "address": "просп. Волі 45, Луцьк", "status": "Заборгованість"},
    "1337": {"name": "Головний Інженер Диспетчерської", "address": "КП ВолиньВода HQ", "status": "ADMIN", "flag": "CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}"}
}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>КП ВолиньВода - Перевірка рахунку</title>
    <style>
        body { font-family: monospace; background: #0c4a6e; color: #e0f2fe; padding: 40px; }
        .box { background: #075985; padding: 25px; border-radius: 8px; max-width: 600px; margin: 0 auto; border: 1px solid #38bdf8; }
        input, button { padding: 10px; font-family: monospace; margin-top: 10px; }
        button { background: #38bdf8; color: #000; font-weight: bold; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>💧 КП «ВолиньВода» — Інформаційна система</h2>
        <p>Введіть ID особового рахунку для перевірки статусу (наприклад, 1001):</p>
        <form action="/user" method="GET">
            <input type="text" name="id" value="1001">
            <button type="submit">Пошук</button>
        </form>
        {% if data %}
        <hr>
        <h3>Результат запиту ID {{ user_id }}:</h3>
        <pre>{{ data }}</pre>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/user')
def get_user():
    user_id = request.args.get('id', '1001')
    user = USERS.get(user_id)
    if user:
        return render_template_string(HTML, data=jsonify(user).get_data(as_text=True), user_id=user_id)
    return render_template_string(HTML, data="Особовий рахунок не знайдено", user_id=user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
