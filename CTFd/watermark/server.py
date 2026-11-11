"""Internal flag-issuance service for Operation Titan.

Only containers on the private ``titan_internal`` Docker network can reach
this API.  The LFI challenge calls ``/flag`` with the VPN client address it
observed, and CTFd calls ``/verify`` when a player submits a flag.  The HMAC
secret never leaves this container.
"""
from __future__ import annotations

import ipaddress
import os

from flask import Flask, jsonify, request

import watermark

app = Flask(__name__)
DEFAULT_CHALLENGE = os.environ.get("TITAN_CHALLENGE_ID", "lfi_challenge")


def _challenge(value: str | None) -> str:
    return (value or DEFAULT_CHALLENGE).strip()[:64]


def _client_ip(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


@app.get("/health")
def health():
    return "ok"


@app.get("/flag")
def issue_flag():
    client_ip = _client_ip(request.args.get("ip"))
    challenge = _challenge(request.args.get("challenge"))
    if client_ip is None:
        return jsonify(ok=False, error="bad_ip", message="Invalid client IP"), 400

    nickname = watermark.nickname_for_ip(client_ip)
    if nickname is None:
        watermark.log_event(
            "FLAG_REFUSED", ip=client_ip, challenge=challenge, reason="no_vpn_profile"
        )
        return (
            jsonify(
                ok=False,
                error="no_vpn_profile",
                message=(
                    "Для цієї адреси немає VPN-профілю. Спершу отримайте .ovpn "
                    "на VPN-порталі під тією самою назвою команди, що й у CTFd."
                ),
                ip=client_ip,
            ),
            403,
        )

    flag = watermark.generate_flag(client_ip, challenge)
    watermark.log_event(
        "FLAG_ISSUED", ip=client_ip, nickname=nickname, challenge=challenge, flag=flag
    )
    return jsonify(ok=True, flag=flag, nickname=nickname, ip=client_ip)


@app.get("/verify")
def verify():
    nickname = (request.args.get("nickname") or "").strip()
    submitted = (request.args.get("flag") or "").strip()
    challenge = _challenge(request.args.get("challenge"))
    if not nickname or not submitted:
        return jsonify(ok=False, error="missing_fields"), 400

    valid = watermark.verify_flag(nickname, submitted, challenge)
    return jsonify(ok=True, valid=valid, nickname=nickname, challenge=challenge)


@app.get("/trace")
def trace():
    submitted = (request.args.get("flag") or "").strip()
    challenge = _challenge(request.args.get("challenge"))
    if not submitted:
        return jsonify(ok=False, error="missing_flag"), 400
    match = watermark.trace_flag(submitted, challenge)
    return jsonify(ok=True, match=match)


@app.route("/cheat", methods=["GET", "POST"])
def cheat():
    payload = request.get_json(silent=True) or request.args
    submitted_by = str(payload.get("submitted_by", "UNKNOWN"))[:128]
    submitted = str(payload.get("flag", "")).strip()
    challenge = _challenge(payload.get("challenge"))
    match = watermark.trace_flag(submitted, challenge) if submitted else None
    watermark.log_event(
        "CHEAT_DETECTED",
        submitted_by=submitted_by,
        challenge=challenge,
        belongs_to=(f"{match['nickname']}@{match['ip']}" if match else "UNKNOWN"),
        flag=submitted,
    )
    return jsonify(ok=True, match=match)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5060)
