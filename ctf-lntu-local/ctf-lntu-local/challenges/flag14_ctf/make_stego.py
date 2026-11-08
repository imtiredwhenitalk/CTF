"""Генерує photo.png: прапор прихований у наймолодших бітах червоного каналу (LSB, MSB-first, порядок рядків)."""
import math
import random
from pathlib import Path
from PIL import Image

FLAG = b"CTF{lsb_st3g0_h1d1ng_1n_pl41n_s1ght}\x00"
W, H = 480, 320
random.seed(2026)

img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    for x in range(W):
        t = y / H
        r = int(240 - 80 * t + 12 * math.sin(x / 31))
        g = int(150 - 70 * t + 10 * math.sin(x / 23 + y / 40))
        b = int(60 + 40 * t + random.randint(-4, 4))
        px[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

bits = [(byte >> i) & 1 for byte in FLAG for i in range(7, -1, -1)]
for n, bit in enumerate(bits):
    x, y = n % W, n // W
    r, g, b = px[x, y]
    px[x, y] = ((r & ~1) | bit, g, b)

img.save(Path(__file__).parent / "photo.png")
print("photo.png створено")
