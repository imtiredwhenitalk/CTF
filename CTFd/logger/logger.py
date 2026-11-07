#!/usr/bin/env python3
"""Operation Titan — admin helper for watermarked flags.

Run it on the server (or build the logger container) to verify a submitted
flag or find who leaked one.

Examples::

    python3 logger.py registry
    python3 logger.py verify shadow_hunter42 'CTF{lf1_t0_rc3_p01s0n1ng_pr0_1a2b3c4d}'
    python3 logger.py trace 'CTF{lf1_t0_rc3_p01s0n1ng_pr0_1a2b3c4d}'
    python3 logger.py tail 50

Environment overrides (defaults point at the CTFd folder):
    TITAN_DATA_DIR, TITAN_REGISTRY, TITAN_WATERMARK_SECRET_FILE,
    TITAN_LOG_PATH, TITAN_CHALLENGE_ID
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "watermark"))

os.environ.setdefault("TITAN_DATA_DIR", str(BASE / "data"))
os.environ.setdefault("TITAN_REGISTRY", str(BASE / "data" / "user_registry.csv"))
os.environ.setdefault(
    "TITAN_WATERMARK_SECRET_FILE", str(BASE / "data" / "watermark.key")
)
os.environ.setdefault("TITAN_LOG_PATH", str(BASE / "logs" / "flag_issuance.log"))

import watermark  # noqa: E402  (path configured above)


def cmd_registry(_args) -> int:
    registry = watermark.load_registry()
    if not registry:
        print("Registry is empty. Ask players to download a VPN profile first.")
        return 0
    print(f"{'VPN IP':<16} nickname")
    for vpn_ip, nickname in sorted(
        registry.items(), key=lambda item: tuple(int(part) for part in item[0].split("."))
    ):
        print(f"{vpn_ip:<16} {nickname}")
    return 0


def cmd_verify(args) -> int:
    valid = watermark.verify_flag(args.nickname, args.flag, args.challenge)
    print("VALID" if valid else "INVALID")
    if not valid:
        match = watermark.trace_flag(args.flag, args.challenge)
        if match:
            print(f"Flag belongs to: {match['nickname']} ({match['ip']})")
    return 0 if valid else 1


def cmd_trace(args) -> int:
    extra = (f"10.8.0.{last}" for last in range(10, 251))
    match = watermark.trace_flag(args.flag, args.challenge, extra_ips=extra)
    if not match:
        print("No matching registry entry.")
        return 1
    print(f"Flag belongs to: {match['nickname']} (VPN IP {match['ip']})")
    return 0


def cmd_tail(args) -> int:
    path = Path(watermark.LOG_PATH)
    if not path.exists():
        print(f"Log does not exist yet: {path}")
        return 1
    with path.open(encoding="utf-8", errors="replace") as handle:
        lines = handle.readlines()
    for line in lines[-args.lines :]:
        print(line, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Operation Titan watermark helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("registry", help="show nickname → VPN IP mapping")

    verify = sub.add_parser("verify", help="check a flag for a nickname")
    verify.add_argument("nickname")
    verify.add_argument("flag")
    verify.add_argument("--challenge", default=watermark.DEFAULT_CHALLENGE_ID)

    trace = sub.add_parser("trace", help="find the owner of a leaked flag")
    trace.add_argument("flag")
    trace.add_argument("--challenge", default=watermark.DEFAULT_CHALLENGE_ID)

    tail = sub.add_parser("tail", help="show the last log lines")
    tail.add_argument("lines", nargs="?", type=int, default=30)

    args = parser.parse_args()
    return {
        "registry": cmd_registry,
        "verify": cmd_verify,
        "trace": cmd_trace,
        "tail": cmd_tail,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
