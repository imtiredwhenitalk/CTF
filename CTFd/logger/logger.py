from flask import Flask, request
import datetime

app = Flask(__name__)

@app.route('/log', methods=['GET', 'POST'])
def log_request():
    data = request.all_data if request.data else request.args
    log_entry = f"[{datetime.datetime.now()}] IP: {request.remote_addr} | Data: {data}\n"
    
    with open("/logger/logs/ctf_activity.log", "a") as f:
        f.write(log_entry)
        
    return "Logged", 200

if __name__ == '__main__':
    app.run(host='10.10.15.124', port=5000)
