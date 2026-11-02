from flask import Flask, request, abort
import os
app = Flask(__name__)

@app.route('/')
def index():
    file = request.args.get('file', 'welcome.txt')
    # Filter '..' to prevent basic traversal, but we can bypass it!
    if '..' in file: return "Hacking Attempt Detected!"
    
    # Absolute paths are allowed by os.path.join if the second arg is absolute!
    target = os.path.join('/app/files', file)
    try:
        with open(target, 'r') as f: return f.read()
    except: return "File not found.", 404

if __name__ == '__main__': 
    os.makedirs('/app/files', exist_ok=True)
    with open('/app/files/welcome.txt', 'w') as f: f.write("Welcome to Titan Doc Server. Use ?file=welcome.txt")
    app.run(host='0.0.0.0', port=5000)
