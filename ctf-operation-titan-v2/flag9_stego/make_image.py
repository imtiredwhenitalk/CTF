import os
import struct
import zlib


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


def make_png():
    # minimal valid 64x64 grey PNG
    w = h = 64
    raw = b"".join(b"\x00" + bytes([40 + (x + y) % 60 for x in range(w)]) for y in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def write_container(path, archive):
    with open(path, "wb") as f:
        f.write(make_png() + open(archive, "rb").read())   # ZIP appended after IEND


os.makedirs("public", exist_ok=True)
write_container("public/image.png", "secret.zip")

# TRAP / RED HERRING: archived image with an old, non-scoring flag.
write_container("public/image_old.png", "secret_old.zip")

with open("public/notes.txt", "w", encoding="utf-8") as f:
    f.write(
        "Titan Archive Node - migration notes\n"
        "=====================================\n"
        "image.png     - current asset container (password: titan)\n"
        "image_old.png - 2021 archive copy (password: titan)\n\n"
        "The 2021 archive was already reviewed by the audit team. Its recovered\n"
        "flag (CTF{st3g0_l3g4cy_4rch1v3_fl4g}) is retained for reference only and\n"
        "was rotated out of the scoreboard.\n"
    )
