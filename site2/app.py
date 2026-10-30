from flask import Flask, render_template, request, session, redirect, render_template_string

import os 
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "ctf-not-a-real-secret"

FLAG = "CTF{CaN_U_F1ND_Th3_Fl4g?}"

def init_db():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    c = db.cursor()
    c.executescript(f"""
    CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, full_name TEXT);
    CREATE TABLE accounts(id INTEGER PRIMARY KEY, address TEXT, balance REAL, last_reading INTEGER);
    CREATE TABLE secrets(id INTEGER PRIMARY KEY, name TEXT, value TEXT);
    INSERT INTO users VALUES
      (1,'admin','Zx9#qL!vT7r$2mWp-not-guessable','admin','Адміністратор системи'),
      (2,'ivan.petrenko','qwerty123','user','Іван Петренко'),
      (3,'olena.kovalchuk','water2024','user','Олена Ковальчук');
    INSERT INTO accounts VALUES
      (1,'вул. Лесі Українки, 14, кв. 7',-214.50,1832),
      (2,'просп. Волі, 33, кв. 21',0.00,947),
      (3,'вул. Шевченка, 5',312.80,2210);
    """)
    db.commit()
    return db

DB = init_db()

@app.route('/')
def home():
    return render_template(BASE_DIR + '/templates/main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        with DB as c:
            user = c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
            user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
    return render_template(BASE_DIR + '/templates/login.html')

