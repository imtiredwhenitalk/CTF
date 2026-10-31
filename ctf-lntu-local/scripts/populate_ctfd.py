#!/usr/bin/env python3
import argparse
import requests

CHALLENGES = [
    {
        "name": "01. ВолиньГаз - Витік та Шаблони",
        "category": "Web / SSTI",
        "description": "Портал ВолиньГаз має внутрішню вразливість обробки шаблонів за заявами споживачів. (http://localhost:8081)",
        "value": 500,
        "type": "dynamic",
        "state": "visible"
    },
    {
        "name": "02. ВолиньВода - Прихований обліковий запис",
        "category": "Web / IDOR & LFI",
        "description": "Перевірте систему обліку показників ВолиньВода та знайдіть адмінські дані. (http://localhost:8082)",
        "value": 500,
        "type": "dynamic",
        "state": "visible"
    },
    {
        "name": "03. LNTU Cyber Blog - XSS Challenge",
        "category": "Web / XSS",
        "description": "Опублікуйте статтю в блозі та викрадіть Cookie адміністратора, який періодично переглядає пости. (http://localhost:8083)",
        "value": 500,
        "type": "dynamic",
        "state": "visible"
    },
    {
        "name": "04. Магазин Затвор - SQL Injection",
        "category": "Web / SQLi",
        "description": "Знайдіть способи обходу фільтрації в пошуку магазину «Затвор». (http://localhost:8084)",
        "value": 500,
        "type": "dynamic",
        "state": "visible"
    },
    {
        "name": "05. LNTU Binary - Stack Overflow",
        "category": "PWN",
        "description": "Переповніть буфер сервісу діагностики систем ЛНТУ та отримайте виконання коду. (nc localhost 1337)",
        "value": 500,
        "type": "dynamic",
        "state": "visible"
    }
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    headers = {
        "Authorization": f"Token {args.token}",
        "Content-Type": "application/json"
    }

    for chal in CHALLENGES:
        r = requests.post(f"{args.url.rstrip('/')}/api/v1/challenges", json=chal, headers=headers)
        if r.status_code == 200:
            print(f"[+] Додано таск: {chal['name']}")
        else:
            print(f"[-] Помилка при додаванні {chal['name']}: {r.text}")

if __name__ == "__main__":
    main()
