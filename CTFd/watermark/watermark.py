"""Operation Titan — per-user flag watermarking.

The same module is used by the internal flag service (``server.py``) and by
the offline administration tool (``logger/logger.py``).  It is deliberately
NOT copied into any vulnerable challenge container: the HMAC secret must not
be reachable through LFI/RCE.

Registry format (written by vpn-portal/vpn_api.py)::

    nickname,common_name,vpn_ip
    shadow_hunter42,ctfd_shadow_hunter42_1a2b3c4d,10.8.0.10

Flags look like::

    CTF{lf1_t0_rc3_p01s0n1ng_pr0_<first 8 hex chars of HMAC>}

The identifier that is signed is the VPN address plus the challenge id, so a
flag is valid only for the VPN profile it was issued to.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import ipaddress
import os
import secrets
import threading
import time
from typing import Iterable

DEFAULT_CHALLENGE_ID = os.environ.get("TITAN_CHALLENGE_ID", "lfi_challenge")
FLAG_PREFIX = "CTF{lf1_t0_rc3_p01s0n1ng_pr0_"
FLAG_SUFFIX = "}"

DATA_DIR = os.environ.get("TITAN_DATA_DIR", "/data")
REGISTRY_PATH = os.environ.get("TITAN_REGISTRY", os.path.join(DATA_DIR, "user_registry.csv"))
SECRET_FILE = os.environ.get("TITAN_WATERMARK_SECRET_FILE", os.path.join(DATA_DIR, "watermark.key"))
LOG_PATH = os.environ.get("TITAN_LOG_PATH", "/logs/flag_issuance.log")

_lock = threading.Lock()
_secret_cache: bytes | None = None


def _read_secret() -> bytes:
    """Load the HMAC key from the environment or the shared key file.

    The internal service is allowed to create the key on first start; every
    other consumer only ever reads it.  Creating it with O_EXCL makes a race
    between two service replicas harmless.
    """
    global _secret_cache
    if _secret_cache is not None:
        return _secret_cache

    env_secret = os.environ.get("TITAN_WATERMARK_SECRET")
    if env_secret:
        _secret_cache = env_secret.encode("utf-8")
        return _secret_cache

    try:
        with open(SECRET_FILE, "rb") as handle:
            value = handle.read().strip()
        if value:
            _secret_cache = value
            return _secret_cache
    except FileNotFoundError:
        pass

    # Generate a key once.  ``os.open(..., O_CREAT | O_EXCL)`` guarantees
    # that concurrent starts do not end up with two different keys.
    os.makedirs(os.path.dirname(SECRET_FILE) or ".", exist_ok=True)
    value = secrets.token_hex(32).encode("ascii")
    try:
        fd = os.open(SECRET_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        with open(SECRET_FILE, "rb") as handle:
            value = handle.read().strip()
    else:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value + b"\n")
    _secret_cache = value
    return value


def generate_token(identifier: str, challenge_id: str | None = None) -> str:
    challenge = challenge_id or DEFAULT_CHALLENGE_ID
    message = f"{identifier}:{challenge}".encode("utf-8")
    return hmac.new(_read_secret(), message, hashlib.sha256).hexdigest()[:8]


def generate_flag(identifier: str, challenge_id: str | None = None) -> str:
    return f"{FLAG_PREFIX}{generate_token(identifier, challenge_id)}{FLAG_SUFFIX}"


def load_registry() -> dict[str, str]:
    """Return ``{vpn_ip: nickname}`` from the CSV written by the VPN portal."""
    mapping: dict[str, str] = {}
    try:
        with open(REGISTRY_PATH, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or row[0].strip().startswith("#"):
                    continue
                if row[0].strip().lower() == "nickname":  # optional header
                    continue
                if len(row) < 3:
                    continue
                nickname, _cn, vpn_ip = (cell.strip() for cell in row[:3])
                if not nickname or not vpn_ip:
                    continue
                try:
                    ipaddress.ip_address(vpn_ip)
                except ValueError:
                    continue
                mapping[vpn_ip] = nickname
    except FileNotFoundError:
        pass
    return mapping


def nickname_for_ip(client_ip: str) -> str | None:
    return load_registry().get(client_ip)


def ip_for_nickname(nickname: str) -> str | None:
    for vpn_ip, name in load_registry().items():
        if name == nickname:
            return vpn_ip
    return None


def get_flag_for_ip(client_ip: str, challenge_id: str | None = None) -> str:
    return generate_flag(client_ip, challenge_id)


def verify_flag(nickname: str, submitted_flag: str, challenge_id: str | None = None) -> bool:
    vpn_ip = ip_for_nickname(nickname)
    if vpn_ip is None:
        return False
    expected = generate_flag(vpn_ip, challenge_id)
    return hmac.compare_digest(submitted_flag.strip(), expected)


def trace_flag(
    submitted_flag: str,
    challenge_id: str | None = None,
    extra_ips: Iterable[str] = (),
) -> dict[str, str] | None:
    """Find which registry entry owns a leaked flag.

    ``extra_ips`` is used by the administration tool to also check addresses
    that were not written to the registry (for example a restored backup).
    """
    submitted = submitted_flag.strip()
    seen: set[str] = set()
    for vpn_ip, nickname in load_registry().items():
        seen.add(vpn_ip)
        if hmac.compare_digest(submitted, generate_flag(vpn_ip, challenge_id)):
            return {"nickname": nickname, "ip": vpn_ip}
    for vpn_ip in extra_ips:
        if vpn_ip in seen:
            continue
        try:
            ipaddress.ip_address(vpn_ip)
        except ValueError:
            continue
        if hmac.compare_digest(submitted, generate_flag(vpn_ip, challenge_id)):
            return {"nickname": "UNKNOWN_IP", "ip": vpn_ip}
    return None


def log_event(event: str, **fields: object) -> None:
    """Append one structured line to the issuance log (best effort)."""
    def clean(value: object) -> str:
        return str(value).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")

    keys = " ".join(f"{key}={clean(value)}" for key, value in fields.items())
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {event} {keys}\n"
    with _lock:
        try:
            os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            # The service must keep issuing flags even if the log volume is
            # read-only; the container's stdout still receives the message.
            print(line, end="", flush=True)
