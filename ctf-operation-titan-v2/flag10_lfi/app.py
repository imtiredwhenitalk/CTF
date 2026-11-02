from flask import Flask, request, render_template_string
import os
app = Flask(__name__)

HTML = '''
<!DOCTYPE html><html lang="en"><head><title>Titan Docs</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-light"><div class="container mt-5">
    <div class="card bg-secondary text-light">
        <div class="card-header"><h4>Document Server</h4></div>
        <div class="card-body">
            <a href="/?file=welcome.txt" class="btn btn-info">Load Welcome Doc</a>
            <hr>
            <pre class="bg-dark p-3 text-light">{{ content }}</pre>
        </div>
    </div>
</div></body></html>
'''

@app.route('/')
def index():
    file = request.args.get('file', '')
    if not file: return render_template_string(HTML, content="Select a file to read.")
    if '..' in file: return render_template_string(HTML, content="Hacking Attempt Detected!")
    
    target = os.path.join('/app/files', file)
    try:
        with open(target, 'r') as f: return render_template_string(HTML, content=f.read())
    except: return render_template_string(HTML, content="File not found.")

if __name__ == '__main__': 
    os.makedirs('/app/files', exist_ok=True)
    with open('/app/files/welcome.txt', 'w') as f: f.write("Titan Document Server V3. All files are stored securely.")
    app.run(host='0.0.0.0', port=5000)
