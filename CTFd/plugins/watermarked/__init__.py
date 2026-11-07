"""CTFd custom flag type: per-user watermarked flags.

The flag itself is never stored in the CTFd database.  Instead, CTFd asks the
internal flag service (see ``CTFd/watermark/server.py``) whether the submitted
value matches the VPN profile of the currently logged-in user.

The service also records every leaked-flag attempt in
``logs/flag_issuance.log`` so organisers can trace who leaked a flag.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from flask import current_app

from CTFd.plugins.flags import FLAG_CLASSES, BaseFlag
from CTFd.utils.user import get_current_user

WATERMARK_URL = os.environ.get("TITAN_WATERMARK_URL", "http://watermark:5060").rstrip("/")
DEFAULT_CHALLENGE = os.environ.get("TITAN_CHALLENGE_ID", "lfi_challenge")
TIMEOUT = float(os.environ.get("TITAN_WATERMARK_TIMEOUT", "3"))


def _call(path: str, params: dict[str, str] | None = None, body: dict | None = None) -> dict | None:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{WATERMARK_URL}{path}{query}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - never break flag submission
        try:
            current_app.logger.warning("watermark service unavailable: %s", exc)
        except Exception:  # noqa: BLE001
            pass
        return None


def _challenge_id(chal_key_obj) -> str:
    data = (getattr(chal_key_obj, "data", "") or "").strip()
    return data or DEFAULT_CHALLENGE


class WatermarkedFlag(BaseFlag):
    name = "watermarked"
    templates: dict = {}

    @staticmethod
    def compare(chal_key_obj, provided):
        user = get_current_user()
        if user is None:
            return False

        nickname = (user.name or "").strip()
        if not nickname:
            return False

        challenge = _challenge_id(chal_key_obj)
        payload = _call("/verify", {"nickname": nickname, "flag": provided, "challenge": challenge})
        if payload is None:
            return False
        if payload.get("valid") is True:
            return True

        # Wrong flag: ask the service who the leaked flag belongs to and let
        # it write a CHEAT_DETECTED line into the central log.
        _call(
            "/cheat",
            body={
                "submitted_by": nickname,
                "flag": provided,
                "challenge": challenge,
            },
        )
        return False


def load(app):
    FLAG_CLASSES[WatermarkedFlag.name] = WatermarkedFlag
    app.logger.info("Loaded watermarked flag type (service: %s)", WATERMARK_URL)
