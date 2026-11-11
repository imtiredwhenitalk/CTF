#!/usr/bin/env python3
"""Administration CLI for Operation Titan VPN team accounts.

Examples (run from the ``CTFd`` directory):

    # Create one team and print a generated password
    sudo python3 vpn-portal/admin_teams.py add team-alpha

    # Create many teams at once and save the plaintext list for distribution
    sudo python3 vpn-portal/admin_teams.py bulk team-alpha team-beta team-gamma \
        --output data/team_passwords.csv

    # Create passwords for every existing registry entry (migration)
    sudo python3 vpn-portal/admin_teams.py import-registry \
        --output data/team_passwords.csv

    # Reset a captain's password
    sudo python3 vpn-portal/admin_teams.py set team-alpha

    # Show teams and their VPN addresses
    sudo python3 vpn-portal/admin_teams.py list

The plaintext output file is written with mode 0600.  Hand it to captains and
delete it afterwards; the portal only stores PBKDF2 hashes.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import getpass
import hashlib
import os
import re
import secrets
import sys
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import team_auth  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.environ.get(
    "TITAN_DATA_DIR", os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data"))
)


class CliError(RuntimeError):
    pass


@contextmanager
def locked(credentials_path: str):
    lock_path = f"{credentials_path}.lock"
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def load_credentials(path: str) -> dict:
    return team_auth.load(path)


def save_credentials(path: str, payload: dict) -> None:
    team_auth.save(path, payload)


def read_registry(path: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or row[0].strip().startswith("#"):
                    continue
                if row[0].strip().lower() in {"team", "nickname"}:
                    continue
                if len(row) < 3:
                    continue
                team, cn, vpn_ip = (cell.strip() for cell in row[:3])
                if team and cn and vpn_ip:
                    entries.append({"team": team, "cn": cn, "vpn_ip": vpn_ip})
    except FileNotFoundError:
        pass
    return entries


def safe_cn(team: str) -> str:
    """Keep this in sync with ``safe_cn`` in vpn_api.py."""
    safe = re.sub(r"[^A-Za-z0-9_]", "_", team)[:24] or "team"
    digest = hashlib.sha1(team.encode("utf-8")).hexdigest()[:8]
    return f"ctfd_{safe}_{digest}"


def write_output(path: str | None, rows: list[tuple[str, str]]) -> None:
    """Merge ``team,password`` rows into a 0600 CSV (last value wins)."""
    if not path or not rows:
        return
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    existing: dict[str, str] = {}
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or len(row) < 2:
                    continue
                team = row[0].strip()
                if not team or team.lower() in {"team", "nickname"}:
                    continue
                existing[team] = row[1].strip()
    except FileNotFoundError:
        pass

    for team, password in rows:
        existing[team] = password

    temporary = f"{path}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["team", "password"])
            for team, password in existing.items():
                writer.writerow([team, password])
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def report(rows: list[tuple[str, str]], output: str | None) -> None:
    if not rows:
        print("[=] Нових команд не створено.")
        return
    print()
    print("team\tpassword")
    for team, password in rows:
        print(f"{team}\t{password}")
    print()
    if output:
        write_output(output, rows)
        print(f"[+] Паролі дописано у {os.path.abspath(output)} (chmod 600).")
        print("[!] Передайте файл капітанам і видаліть його після роздачі.")
    else:
        print("[!] Збережіть пароли зараз: у файлі зберігаються лише хеші.")


def add_team(
    payload: dict,
    team: str,
    password: str | None,
    *,
    force: bool,
    iterations: int,
) -> tuple[str, str] | None:
    team = team_auth.validate_team(team)
    existing = team in payload.get("teams", {})
    if existing and not force:
        print(f"[=] Команда '{team}' вже має пароль; пропускаю (--force для скидання).")
        return None

    password = password or team_auth.generate_password()
    if existing:
        team_auth.set_team_password(payload, team, password, iterations=iterations)
        print(f"[+] Пароль команди '{team}' скинуто.")
    else:
        team_auth.create_team(payload, team, password, iterations=iterations)
        print(f"[+] Створено команду '{team}'.")
    return team, password


def cmd_add(args, credentials: str, registry: str) -> int:
    with locked(credentials):
        payload = load_credentials(credentials)
        result = add_team(
            payload,
            args.team,
            args.password,
            force=args.force,
            iterations=args.iterations,
        )
        if result:
            save_credentials(credentials, payload)
            report([result], args.output)
    return 0


def collect_teams(args) -> list[str]:
    teams: list[str] = []
    for item in args.teams:
        teams.extend(part.strip() for part in item.split(",") if part.strip())
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.split("#", 1)[0].strip()
                if line:
                    teams.append(line)
    seen: set[str] = set()
    unique: list[str] = []
    for team in teams:
        if team not in seen:
            seen.add(team)
            unique.append(team)
    return unique


def cmd_bulk(args, credentials: str, registry: str) -> int:
    teams = collect_teams(args)
    if not teams:
        raise CliError("Не вказано жодної назви команди (аргументи або --file).")

    rows: list[tuple[str, str]] = []
    with locked(credentials):
        payload = load_credentials(credentials)
        for team in teams:
            result = add_team(
                payload,
                team,
                None,
                force=args.force,
                iterations=args.iterations,
            )
            if result:
                rows.append(result)
        if rows:
            save_credentials(credentials, payload)
    report(rows, args.output)
    return 0


def cmd_import_registry(args, credentials: str, registry: str) -> int:
    registry_entries = read_registry(registry)
    if not registry_entries:
        print(f"[=] Реєстр {registry} порожній або не існує.")
        return 0

    rows: list[tuple[str, str]] = []
    with locked(credentials):
        payload = load_credentials(credentials)
        for entry in registry_entries:
            team = entry["team"]
            if team in payload.get("teams", {}) and not args.force:
                continue
            result = add_team(
                payload,
                team,
                None,
                force=args.force,
                iterations=args.iterations,
            )
            if result:
                rows.append(result)
        if rows:
            save_credentials(credentials, payload)
    report(rows, args.output)
    return 0


def cmd_set(args, credentials: str, registry: str) -> int:
    team = team_auth.validate_team(args.team)
    if args.generate:
        password = team_auth.generate_password()
        generated = True
    elif args.password:
        password = args.password
        generated = False
    else:
        password = getpass.getpass(f"Новий пароль для '{team}': ")
        confirmation = getpass.getpass("Повторіть пароль: ")
        if password != confirmation:
            raise CliError("Паролі не збігаються.")
        generated = False

    with locked(credentials):
        payload = load_credentials(credentials)
        if team not in payload.get("teams", {}):
            raise CliError(
                f"Команда '{team}' не має пароля. Створіть її командою add."
            )
        team_auth.set_team_password(payload, team, password, iterations=args.iterations)
        save_credentials(credentials, payload)

    print(f"[+] Пароль команди '{team}' оновлено.")
    if generated:
        report([(team, password)], args.output)
    return 0


def cmd_remove(args, credentials: str, registry: str) -> int:
    team = team_auth.validate_team(args.team)
    with locked(credentials):
        payload = load_credentials(credentials)
        if team not in payload.get("teams", {}):
            raise CliError(f"Команда '{team}' не знайдена.")
        if not args.yes:
            answer = input(f"Видалити пароль команди '{team}'? [y/N] ").strip().lower()
            if answer not in {"y", "yes", "т", "так"}:
                print("[=] Скасовано.")
                return 1
        team_auth.remove_team(payload, team)
        save_credentials(credentials, payload)

    print(f"[+] Пароль команди '{team}' видалено.")
    cn = safe_cn(team)
    print(
        f"[!] VPN-сертифікат {cn} і CCD-файл залишилися. Щоб повністю "
        "відкликати доступ, виконайте на сервері:"
    )
    print(f"    sudo docker exec openvpn ovpn_revokeclient {cn} remove")
    print(
        "    Потім видаліть CTFd/openvpn-data/conf/ccd/"
        f"{cn} і рядок команди з CTFd/data/user_registry.csv."
    )
    return 0


def cmd_list(args, credentials: str, registry: str) -> int:
    payload = load_credentials(credentials)
    registered = {entry["team"]: entry for entry in read_registry(registry)}
    teams = sorted(set(payload.get("teams", {})) | set(registered))
    if not teams:
        print("[=] Ще немає жодної команди.")
        return 0

    print(f"{'TEAM':32} {'VPN IP':15} {'CERT':28} STATUS")
    print("-" * 100)
    for team in teams:
        entry = registered.get(team, {})
        if team in payload.get("teams", {}):
            status = "ok"
        else:
            status = "немає пароля (import-registry)"
        print(
            f"{team[:32]:32} {entry.get('vpn_ip', '-'):15} "
            f"{entry.get('cn', '-'):28} {status}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Керування командами та паролями VPN-порталу Operation Titan."
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"каталог даних (за замовчуванням {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--credentials",
        default=None,
        help="шлях до team_credentials.json (за замовчуванням <data-dir>/team_credentials.json)",
    )
    parser.add_argument(
        "--registry",
        default=None,
        help="шлях до user_registry.csv (за замовчуванням <data-dir>/user_registry.csv)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=team_auth.DEFAULT_ITERATIONS,
        help=f"PBKDF2 iterations (за замовчуванням {team_auth.DEFAULT_ITERATIONS})",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="створити команду і згенерувати пароль")
    add.add_argument("team")
    add.add_argument("--password", help="задати пароль вручну (мінімум 8 символів)")
    add.add_argument("--force", action="store_true", help="скинути пароль, якщо команда існує")
    add.add_argument("--output", help="дописати team,password у файл (chmod 600)")

    bulk = sub.add_parser("bulk", help="створити багато команд одним запуском")
    bulk.add_argument("teams", nargs="*", help="назви команд (можна через кому)")
    bulk.add_argument("--file", help="файл зі списком команд, по одній на рядок")
    bulk.add_argument("--force", action="store_true", help="скинути паролі існуючих команд")
    bulk.add_argument("--output", help="дописати team,password у файл (chmod 600)")

    set_cmd = sub.add_parser("set", help="змінити пароль команди")
    set_cmd.add_argument("team")
    set_cmd.add_argument("password", nargs="?", help="новий пароль (інакше буде запит)")
    set_cmd.add_argument("--generate", action="store_true", help="згенерувати новий пароль")
    set_cmd.add_argument("--output", help="дописати team,password у файл (chmod 600)")

    remove = sub.add_parser("remove", help="видалити пароль команди")
    remove.add_argument("team")
    remove.add_argument("--yes", action="store_true", help="без підтвердження")

    import_registry = sub.add_parser(
        "import-registry", help="створити паролі для всіх команд із user_registry.csv"
    )
    import_registry.add_argument("--force", action="store_true", help="скинути паролі")
    import_registry.add_argument("--output", help="дописати team,password у файл (chmod 600)")

    sub.add_parser("list", help="показати команди, VPN-адреси та стан паролів")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    credentials = args.credentials or os.path.join(args.data_dir, "team_credentials.json")
    registry = args.registry or os.path.join(args.data_dir, "user_registry.csv")

    handlers = {
        "add": cmd_add,
        "bulk": cmd_bulk,
        "set": cmd_set,
        "remove": cmd_remove,
        "import-registry": cmd_import_registry,
        "list": cmd_list,
    }
    handler = handlers[args.command]
    try:
        return handler(args, credentials, registry)
    except (CliError, ValueError, team_auth.CredentialError, OSError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
