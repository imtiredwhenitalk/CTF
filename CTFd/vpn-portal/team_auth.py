"""Team credential storage for the Operation Titan VPN portal.

The portal authenticates a *team name* and a password.  Passwords are never
stored in plaintext: each record contains a per-team salt, the PBKDF2
iteration count and the resulting PBKDF2-HMAC-SHA256 digest.

The format is deliberately dependency-free so the same module can be imported
by the portal container and by the host-side administration CLI:

    {
      "version": 1,
      "teams": {
        "team-name": {
          "algorithm": "pbkdf2_sha256",
          "iterations": 260000,
          "salt": "<hex>",
          "hash": "<hex>",
          "created": "2026-11-11T08:00:00Z",
          "updated": "2026-11-11T08:00:00Z"
        }
      }
    }
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any

DEFAULT_ITERATIONS = 260_000
MIN_PASSWORD_LENGTH = 8
PASSWORD_ALPHABET = string.ascii_letters + string.digits + "-_"

# Team names become part of a file name in the OpenVPN CCD directory, so path
# separators and control characters are rejected.  Everything else (including
# spaces and non-Latin characters) is allowed; ``safe_cn`` hashes the name.
TEAM_RE = re.compile(r"^[^\x00-\x1f\x7f/\\]{1,128}$")

# Fixed salt used to spend roughly the same time on unknown team names as on
# known ones (reduces user enumeration through response timing).
_DUMMY_SALT = bytes.fromhex("4f7065726174696f6e20546974616e21")


class CredentialError(RuntimeError):
    """The credential file exists but cannot be used."""


def validate_team(team: str) -> str:
    value = (team or "").strip()
    if not TEAM_RE.match(value):
        raise ValueError(
            "Назва команди має містити 1–128 символів; "
            "символи керування, '/' та '\\' заборонені."
        )
    return value


def generate_password(length: int = 20) -> str:
    length = max(int(length), 12)
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty() -> dict[str, Any]:
    return {"version": 1, "teams": {}}


def load(path: str) -> dict[str, Any]:
    """Read the credential file.  A missing file means "no teams yet"."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return _empty()
    except json.JSONDecodeError as exc:
        raise CredentialError(f"Пошкоджений файл паролів {path}: {exc}") from exc
    except OSError as exc:
        raise CredentialError(f"Не вдалося прочитати {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise CredentialError(f"Файл паролів {path} має містити JSON-об'єкт")
    teams = payload.get("teams", {})
    if not isinstance(teams, dict):
        raise CredentialError(f"Поле 'teams' у {path} має бути об'єктом")
    payload["teams"] = teams
    payload.setdefault("version", 1)
    return payload


def save(path: str, payload: dict[str, Any]) -> None:
    """Atomically write the credential file with mode 0600."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    temporary = f"{path}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def hash_password(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, Any]:
    salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", str(password).encode("utf-8"), salt, int(iterations)
    )
    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": int(iterations),
        "salt": salt.hex(),
        "hash": digest.hex(),
    }


def verify_password(record: Any, password: str) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        algorithm = str(record.get("algorithm", "pbkdf2_sha256"))
        iterations = int(record.get("iterations", DEFAULT_ITERATIONS))
        salt = bytes.fromhex(str(record["salt"]))
        expected = bytes.fromhex(str(record["hash"]))
    except (KeyError, TypeError, ValueError):
        return False

    if algorithm != "pbkdf2_sha256" or not salt or not expected:
        return False
    # Reject absurd values that could be used for a CPU denial of service.
    if iterations < 10_000 or iterations > 2_000_000:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256", str(password).encode("utf-8"), salt, iterations, dklen=len(expected)
    )
    return hmac.compare_digest(digest, expected)


def authenticate(payload: dict[str, Any], team: str, password: str) -> bool:
    """Check a team password; invalid team names simply fail."""
    try:
        team = validate_team(team)
    except ValueError:
        return False

    record = payload.get("teams", {}).get(team)
    if not isinstance(record, dict):
        # Spend comparable time on unknown teams.  The digest is discarded.
        hashlib.pbkdf2_hmac(
            "sha256", str(password).encode("utf-8"), _DUMMY_SALT, DEFAULT_ITERATIONS
        )
        return False
    return verify_password(record, password)


def create_team(
    payload: dict[str, Any],
    team: str,
    password: str,
    *,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, Any]:
    team = validate_team(team)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Пароль має містити щонайменше {MIN_PASSWORD_LENGTH} символів."
        )
    now = _utcnow()
    record = hash_password(password, iterations=iterations)
    record["created"] = now
    record["updated"] = now
    payload.setdefault("teams", {})[team] = record
    return record


def set_team_password(
    payload: dict[str, Any],
    team: str,
    password: str,
    *,
    iterations: int = DEFAULT_ITERATIONS,
) -> dict[str, Any]:
    team = validate_team(team)
    teams = payload.setdefault("teams", {})
    previous = teams.get(team) if isinstance(teams.get(team), dict) else {}
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Пароль має містити щонайменше {MIN_PASSWORD_LENGTH} символів."
        )
    record = hash_password(password, iterations=iterations)
    record["created"] = previous.get("created") or _utcnow()
    record["updated"] = _utcnow()
    teams[team] = record
    return record


def remove_team(payload: dict[str, Any], team: str) -> bool:
    team = validate_team(team)
    return payload.setdefault("teams", {}).pop(team, None) is not None
