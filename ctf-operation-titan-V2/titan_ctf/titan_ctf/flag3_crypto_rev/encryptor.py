#!/usr/bin/env python3
KEY = b"TITAN2026"

def encrypt(data: bytes) -> bytes:
    reversed_data = data[::-1]
    return bytes([b ^ KEY[i % len(KEY)] for i, b in enumerate(reversed_data)])

config_content = b"""
[SERVER]
host = 10.100.0.15
ssh_user = app_user
ssh_key_pass = CTF{gh1dr4_r3v3rs1ng_m4st3r_9921}
"""

with open("production.conf.enc", "wb") as f:
    f.write(encrypt(config_content))

print("[+] Generated production.conf.enc")
