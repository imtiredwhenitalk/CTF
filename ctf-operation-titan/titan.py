#!/usr/bin/env python3
"""Cross-platform Operation Titan launcher."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def docker_command() -> list[str]:
    docker = shutil.which("docker")
    if not docker:
        raise SystemExit("Docker is not installed or is not available on PATH.")
    result = subprocess.run(
        [docker, "compose", "version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit("Docker Compose v2 is required (try: docker compose version).")
    return [docker, "compose"]

def compose_args(args: argparse.Namespace) -> list[str]:
    command = docker_command()
    if args.vpn:
        command.extend(["--profile", "vpn"])
    return command

def run(args: argparse.Namespace, *compose_options: str) -> int:
    command = compose_args(args) + list(compose_options)
    print("$ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Operation Titan CTF.")
    parser.add_argument("--vpn", action="store_true", help="Include the optional OpenVPN services.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("config", help="Validate the Compose configuration.")
    subparsers.add_parser("up", help="Build and start all services.")
    subparsers.add_parser("flag1", help="Build and start challenge 01 only.")
    subparsers.add_parser("down", help="Stop services without deleting the database.")
    subparsers.add_parser("reset", help="Stop services and delete database volumes.")
    subparsers.add_parser("status", help="Show service status.")
    logs = subparsers.add_parser("logs", help="Follow service logs.")
    logs.add_argument("service", nargs="?", help="Optional service name.")

    args = parser.parse_args()
    if args.action == "config":
        return run(args, "config", "--quiet")
    if args.action == "up":
        return run(args, "up", "-d", "--build", "--remove-orphans")
    if args.action == "flag1":
        result = run(args, "up", "-d", "--build", "flag1_git")
        if result == 0:
            print("Challenge 01: http://localhost:8001", flush=True)
        return result
    if args.action == "down":
        return run(args, "down", "--remove-orphans")
    if args.action == "reset":
        confirmation = input("Delete the CTF database volume? [y/N] ").strip().lower()
        if confirmation != "y":
            print("Reset cancelled.")
            return 0
        return run(args, "down", "-v", "--remove-orphans")
    if args.action == "status":
        return run(args, "ps")
    log_args = ["logs", "-f"]
    if args.service:
        log_args.append(args.service)
    return run(args, *log_args)

if __name__ == "__main__":
    sys.exit(main())