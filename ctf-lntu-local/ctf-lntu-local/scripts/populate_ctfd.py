#!/usr/bin/env python3
"""Наповнює CTFd усіма 15 тасками: умова, прапор (static), підказка, бали й порядок.
Лише стандартна бібліотека.

За замовчуванням працює як upsert: наявні таски (шукає за прапором або назвою)
оновлюються — назва з номером, бали 15/20/25, position 01…15, підказка.
Повторний запуск безпечний. Прапори та ID тасків не змінюються, тому розв'язки
гравців зберігаються.

Приклади:
    python3 populate_ctfd.py --token <TOKEN> --host 10.10.15.124
    python3 populate_ctfd.py --token <TOKEN> --create-only   # не оновлювати наявні
"""
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


def challenge_payload(c, host):
    return dict(
        name=c["name"],
        category=c["category"],
        description=c["description"].format(host=host, port=c["port"]).replace("\n", "<br>"),
        value=c["value"],
        position=c["position"],
        state="visible",
    )


def find_existing(c, existing, flag_by_challenge):
    """Шукає таск за прапором (найнадійніше), потім за фрагментом назви."""
    for ch in existing:
        flag = flag_by_challenge.get(ch["id"])
        if flag and flag.get("content") == c["flag"]:
            return ch, flag
    for ch in existing:
        if c["title"] in (ch.get("name") or ""):
            return ch, flag_by_challenge.get(ch["id"])
    return None, None


def sync_hint(base, token, challenge_id, hint, cost):
    hints = call(base, token, "GET", f"/api/v1/hints?challenge_id={challenge_id}")["data"]
    if hints:
        call(base, token, "PATCH", f"/api/v1/hints/{hints[0]['id']}",
             dict(content=hint, cost=cost))
    else:
        call(base, token, "POST", "/api/v1/hints",
             dict(challenge_id=challenge_id, content=hint, cost=cost))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000", help="адреса CTFd")
    ap.add_argument("--token", required=True, help="Admin Panel → Settings → Access Tokens")
    ap.add_argument("--host", default="localhost", help="IP/домен, який побачать гравці в умовах тасків")
    ap.add_argument("--hint-cost", type=int, default=5, help="вартість підказки в балах (типово 5)")
    ap.add_argument("--create-only", action="store_true",
                    help="не оновлювати наявні таски, лише додавати відсутні")
    a = ap.parse_args()

    existing = call(a.url, a.token, "GET", "/api/v1/challenges?view=admin")["data"]
    flags = call(a.url, a.token, "GET", "/api/v1/flags")["data"]
    flag_by_challenge = {f["challenge_id"]: f for f in flags}

    added = updated = 0
    for c in CHALLENGES:
        payload = challenge_payload(c, a.host)
        ch, flag = find_existing(c, existing, flag_by_challenge)

        if ch and a.create_only:
            print(f"[=] Вже існує: {c['name']}")
            continue

        if ch:
            cid = ch["id"]
            call(a.url, a.token, "PATCH", f"/api/v1/challenges/{cid}", payload)
            if flag:
                if flag.get("content") != c["flag"]:
                    call(a.url, a.token, "PATCH", f"/api/v1/flags/{flag['id']}",
                         dict(content=c["flag"]))
            else:
                call(a.url, a.token, "POST", "/api/v1/flags",
                     dict(challenge_id=cid, content=c["flag"], type="static", data=""))
            sync_hint(a.url, a.token, cid, c["hint"], a.hint_cost)
            print(f"[~] Оновлено: {c['name']}  ({c['value']} балів, position {c['position']:02d})")
            updated += 1
        else:
            r = call(a.url, a.token, "POST", "/api/v1/challenges",
                     dict(payload, type="standard"))
            cid = r["data"]["id"]
            call(a.url, a.token, "POST", "/api/v1/flags",
                 dict(challenge_id=cid, content=c["flag"], type="static", data=""))
            sync_hint(a.url, a.token, cid, c["hint"], a.hint_cost)
            print(f"[+] Додано: {c['name']}  ({c['value']} балів, position {c['position']:02d})")
            added += 1

    print(f"\nГотово: додано {added}, оновлено {updated}, усього тасків у списку {len(CHALLENGES)}.")
    print(f"Бали: 5×15 + 5×20 + 5×25 = {sum(c['value'] for c in CHALLENGES)}")

    # Показуємо фактичний порядок, який віддає CTFd гравцям.
    try:
        public = call(a.url, a.token, "GET", "/api/v1/challenges")["data"]
        print("\nПорядок у CTFd:")
        for c in public:
            print(f"  {c['name']}  —  {c['value']} балів")
    except SystemExit:
        pass


if __name__ == "__main__":
    sys.exit(main())
