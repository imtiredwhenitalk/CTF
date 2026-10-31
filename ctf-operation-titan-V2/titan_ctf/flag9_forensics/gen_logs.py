#!/usr/bin/env python3
"""Генератор access.log для завдання Ghost Logs (організаторський скрипт).
Фіксований seed: файл завжди однаковий. Прапор читається з flag.txt."""
import base64
import datetime
import random

random.seed(4417)
FLAG = open("flag.txt").read().strip()

ATTACKER = "185.220.101.47"
USERS = [f"10.100.0.{i}" for i in range(20, 48)]
PAGES = ["/", "/index.html", "/status", "/api/metrics", "/api/stations", "/static/app.js",
         "/static/style.css", "/login", "/dashboard", "/api/grid/load", "/favicon.ico"]
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 Safari/605.1.15",
]
ATTACK_UA = "python-requests/2.31.0"
SCAN_PATHS = ["/admin", "/.env", "/backup.zip", "/phpmyadmin/", "/wp-login.php", "/.git/config",
              "/server-status", "/config.php", "/api/v1/users", "/console"]
SQLI = ["/api/stations?id=1'", "/api/stations?id=1+OR+1=1--",
        "/api/stations?id=1+UNION+SELECT+null,null--",
        "/api/stations?id=1+UNION+SELECT+username,password+FROM+admins--"]

start = datetime.datetime(2026, 10, 30, 8, 0, 0)
events = []  # (time, line)


def line(t, ip, method, path, status, size, ua):
    ts = t.strftime("%d/%b/%Y:%H:%M:%S +0200")
    return f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {size} "-" "{ua}"'


# Звичайний трафік
t = start
for _ in range(900):
    t += datetime.timedelta(seconds=random.randint(5, 90))
    p = random.choice(PAGES)
    events.append((t, line(t, random.choice(USERS), "GET", p,
                           random.choices([200, 304, 404], [88, 8, 4])[0],
                           random.randint(300, 9000), random.choice(UAS))))
end = t

# Хибний слід: легітимний користувач експортує звіт (base64, але не прапор)
decoy = base64.b64encode(b"report_2026_q3.csv").decode()
td = start + datetime.timedelta(hours=3, minutes=12)
events.append((td, line(td, "10.100.0.31", "GET", f"/api/export?chunk=1&d={decoy}", 200, 512, UAS[0])))

# Атакувальник
ta = start + datetime.timedelta(hours=6)
for p in SCAN_PATHS:
    ta += datetime.timedelta(seconds=random.randint(1, 3))
    events.append((ta, line(ta, ATTACKER, "GET", p, random.choice([403, 404]), 162, ATTACK_UA)))
for p in SQLI:
    ta += datetime.timedelta(seconds=random.randint(2, 6))
    events.append((ta, line(ta, ATTACKER, "GET", p, 200 if "UNION" in p else 500, random.randint(300, 900), ATTACK_UA)))

# Ексфільтрація: прапор розбито на 3 частини, кожна у base64; chunk=N задає порядок
parts = [FLAG[i:i + 16] for i in range(0, len(FLAG), 16)]
order = list(range(len(parts)))
random.shuffle(order)  # у логу вони йдуть не по порядку
for idx in order:
    ta += datetime.timedelta(seconds=random.randint(20, 120))
    enc = base64.urlsafe_b64encode(parts[idx].encode()).decode().rstrip("=")
    events.append((ta, line(ta, ATTACKER, "GET", f"/api/export?chunk={idx + 1}&d={enc}", 200, 64, ATTACK_UA)))

events.sort(key=lambda e: e[0])
with open("access.log", "w") as f:
    f.write("\n".join(l for _, l in events) + "\n")
print(f"[+] Generated access.log ({len(events)} lines, {len(parts)} chunks)")
