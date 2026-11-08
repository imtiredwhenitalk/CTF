import struct
import zlib
from pathlib import Path


FLAG = b"CTF{autumn_fox_metadata_tells_the_story}"


def chunk(name, data):
    return (
        struct.pack(">I", len(data))
        + name
        + data
        + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    )


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
png += chunk(b"tEXt", b"Author\x00autumn_fox")
png += chunk(b"tEXt", b"Comment\x00Recovered from the LNTU autumn archive")
png += chunk(b"tEXt", b"Source\x00field-camera-2026-10-17")
png += chunk(b"IDAT", zlib.compress(b"\x00\x8c\x65\x3a"))
png += chunk(b"IEND", b"")
png += b"\n-- forensic recovery note --\n" + FLAG + b"\n"

with (Path(__file__).parent / "evidence.png").open("wb") as file:
    file.write(png)
