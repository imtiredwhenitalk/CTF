#!/usr/bin/env python3
"""Наповнює CTFd усіма 15 тасками: умова, прапор (static), підказка. Лише стандартна бібліотека.
Повторний запуск безпечний: існуючі таски (за назвою) пропускаються."""
import argparse
import json
import sys
import urllib.error
import urllib.request

from challenges import CHALLENGES


def call(base, token, method, path, payload=None):
    req = urllib.request.Request(
        base.rstrip("/") + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[-] {method} {path}: HTTP {e.code} {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[-] Не вдалося підключитися до {base}: {e.reason}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://localhost:8000", help="адреса CTFd")
    ap.add_argument("--token", required=True, help="Admin Panel → Settings → Access Tokens")
    ap.add_argument("--host", default="localhost", help="IP/домен, який побачать гравці в умовах тасків")
    ap.add_argument("--hint-cost", type=int, default=50)
    a = ap.parse_args()

    existing = {c["name"] for c in call(a.url, a.token, "GET", "/api/v1/challenges?view=admin")["data"]}
    added = 0
    for c in CHALLENGES:
        if c["name"] in existing:
            print(f"[=] Вже існує: {c['name']}")
            continue
        desc = c["description"].format(host=a.host, port=c["port"]).replace("\n", "<br>")
        r = call(a.url, a.token, "POST", "/api/v1/challenges", dict(
            name=c["name"], category=c["category"], description=desc, value=c["value"],
            state="visible", type="standard"))
        cid = r["data"]["id"]
        call(a.url, a.token, "POST", "/api/v1/flags", dict(challenge_id=cid, content=c["flag"], type="static", data=""))
        call(a.url, a.token, "POST", "/api/v1/hints", dict(challenge_id=cid, content=c["hint"], cost=a.hint_cost))
        print(f"[+] {c['name']}  ({c['value']} балів, http://{a.host}:{c['port']})")
        added += 1
    print(f"Готово: додано {added}, усього тасків у списку {len(CHALLENGES)}.")


if __name__ == "__main__":
    sys.exit(main())
