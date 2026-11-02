#!/usr/bin/env python3
import argparse
import requests

CHALLENGES = [
    {
        "name": "01. Initial Footprint",
        "category": "Web / OSINT",
        "description": "Знайдіть витік первинної інформації на веб-сайті об'єкта ТИТАН (http://localhost:8081).",
        "value": 500,
        "type": "standard",
        "state": "visible"
    },
    {
        "name": "02. Broken Session",
        "category": "Web / Auth",
        "description": "Отримайте доступ до адміністративної панелі API (http://localhost:8082).",
        "value": 500,
        "type": "standard",
        "state": "visible"
    },
    {
        "name": "03. Dark Config",
        "category": "Crypto / Reverse",
        "description": "Розшифруйте конфігураційний файл `production.conf.enc` у папці challenges/flag3_crypto_rev/.",
        "value": 500,
        "type": "standard",
        "state": "visible"
    },
    {
        "name": "04. System Override",
        "category": "PWN",
        "description": "Проведіть атаку на сервіс діагностики (nc localhost 1337).",
        "value": 500,
        "type": "standard",
        "state": "visible"
    },
    {
        "name": "05. Domain Takeover",
        "category": "Active Directory",
        "description": "Здійсніть атаку Kerberoasting на консолі (http://localhost:8085).",
        "value": 500,
        "type": "standard",
        "state": "visible"
    },
    {
        "name": "06. Zero-Day Core",
        "category": "Kernel / SCADA",
        "description": "Дослідіть драйвер ядра `scada_driver.c` та витягніть секретний прапор.",
        "value": 500,
        "type": "standard",
        "state": "visible"
    }
]

def main():
    parser = argparse.ArgumentParser(description="Populate CTFd with challenges")
    parser.add_argument("--url", required=True, help="CTFd URL (e.g. http://localhost:8000)")
    parser.add_argument("--token", required=True, help="CTFd Admin API Token")
    args = parser.parse_args()

    headers = {
        "Authorization": f"Token {args.token}",
        "Content-Type": "application/json"
    }

    print("[*] Додавання тасків до CTFd...")
    for chal in CHALLENGES:
        res = requests.post(f"{args.url.rstrip('/')}/api/v1/challenges", json=chal, headers=headers)
        if res.status_code == 200:
            print(f"[+] Створено таск: {chal['name']}")
        else:
            print(f"[-] Помилка під час створення {chal['name']}: {res.text}")

if __name__ == "__main__":
    main()
