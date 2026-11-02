#!/usr/bin/env python3
# Custom encryption algorithm used to encrypt internal config
import sys

KEY = b"TITAN2026"

def xor_cipher(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def encrypt(data: bytes) -> bytes:
    # Reverse string + XOR
    reversed_data = data[::-1]
    return xor_cipher(reversed_data, KEY)

def decrypt(data: bytes) -> bytes:
    # XOR + Reverse string
    xored = xor_cipher(data, KEY)
    return xored[::-1]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 config_loader.py <production.conf.enc>")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as f:
        enc_data = f.read()
    
    print("[+] Decrypting configuration...")
    decrypted = decrypt(enc_data)
    print(decrypted.decode(errors='ignore'))
