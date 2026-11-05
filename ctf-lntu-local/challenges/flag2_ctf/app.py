from flask import Flask, render_template_string, request, render_template
app = Flask(__name__)
FLAG = "CTF{v0lyn_g4s_sst1_3xpl01t_2026}"
@app.route('/')
def index(): return render_template('index.html')
@app.route('/request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        name, account, note = request.form.get('name', ''), request.form.get('account', ''), request.form.get('note', '')
        template = f'<!DOCTYPE html><html><head><link rel="stylesheet" href="/static/style.css"></head><body><div class="container"><h1>Заяву №{account} прийнято!</h1><p>Шановний <b>{name}</b>, ваша примітка:</p><div class="card">{note}</div><a href="/">Назад</a></div></body></html>'
        return render_template_string(template)
    return render_template('request.html')
@app.route('/admin')
def admin(): return render_template('admin.html', flag=FLAG)
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
