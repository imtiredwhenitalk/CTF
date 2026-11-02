"""Build the static operations archive used by challenge 01."""

from pathlib import Path
import base64
import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


ROOT = Path(__file__).resolve().parent
PASSWORD = "polar-night-07"
PLAINTEXT = """TITAN OPERATIONS ARCHIVE
Classification: internal
Incident: ORBITAL-07

The emergency access token was rotated after the night-shift handover.
Do not publish this value in the public status feed.

Recovery token: CTF{0ps_arch1ve_bur13d}
"""


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def encrypt_archive(content: str) -> bytes:
    salt = b"TitanArchiveSalt"
    key_material = hashlib.pbkdf2_hmac(
        "sha256", PASSWORD.encode("utf-8"), salt, 200_000, 48
    )
    key, iv = key_material[:32], key_material[32:]
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(content.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return b"TITAN-ARCHIVE-1\n" + base64.b64encode(salt + ciphertext)


def main() -> None:
    write("robots.txt", "User-agent: *\nDisallow: /archive/\nDisallow: /telemetry/\n")
    write(
        "status/health.log",
        "[2024-11-07T01:14:22Z] archive worker: healthy\n"
        "[2024-11-07T01:15:01Z] key rotation: first recovery fragment = polar\n",
    )
    write(
        "archive/manifest.json",
        '{\n  "service": "ops-archive",\n  "format": "titan aes-cbc envelope",\n'
        '  "retention": "90d",\n  "rotation-note": "second fragment: night"\n}\n',
    )
    write(
        "telemetry/legacy/rotation.log",
        "NOTICE: deprecated telemetry channel retained for incident response.\n"
        "operator suffix fragment: 07\n",
    )
    write(
        "archive/readme.txt",
        "Archived records are encrypted at rest. The public status feed contains "
        "no incident data.\n",
    )
    encrypted = ROOT / "archive" / "2024" / "quarterly" / "telemetry.enc"
    encrypted.parent.mkdir(parents=True, exist_ok=True)
    encrypted.write_bytes(encrypt_archive(PLAINTEXT))


if __name__ == "__main__":
    main()
