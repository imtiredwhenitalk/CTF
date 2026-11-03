from flask import Flask, request
import os
from titan_ui import page
app = Flask(__name__)

BODY = '''
<div class="card"><div class="hd">Перегляд документа<span class="sub">GET /?file=</span></div><div class="bd">
  <div class="row" style="margin-bottom:1rem">
    <a class="btn" href="/?file=welcome.txt">Відкрити welcome.txt</a>
  </div>
  <pre class="code plain">{{ content }}</pre>
</div></div>
'''

def view(content):
    return page(BODY, title="Docs", heading="Document Server", tag="10 · LFI",
                node="titan-node-10 · docs", lead="Внутрішнє сховище документів Titan.", content=content)

@app.route('/')
def index():
    file = request.args.get('file', '')
    if not file: return view("Select a file to read.")
    if '..' in file: return view("Hacking Attempt Detected!")

    target = os.path.join('/app/files', file)
    try:
        with open(target, 'r') as f: return view(f.read())
    except: return view("File not found.")

if __name__ == '__main__':
    os.makedirs('/app/files', exist_ok=True)
    with open('/app/files/welcome.txt', 'w') as f: f.write("Titan Document Server V3. All files are stored securely.")
    app.run(host='0.0.0.0', port=5000)
