import struct, zlib

def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

# minimal valid 64x64 grey PNG
w = h = 64
raw = b"".join(b"\x00" + bytes([40 + (x + y) % 60 for x in range(w)]) for y in range(h))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw))
       + chunk(b"IEND", b""))

with open("image.png", "wb") as f:
    f.write(png + open("secret.zip", "rb").read())   # ZIP appended after IEND
