#!/usr/bin/env python3
"""Локальний запуск Operation Titan CTF без Docker (Windows / Linux / macOS).

Потрібні лише Python 3.8+ (і, за бажанням, git). Використання:
    python run_local.py
Зупинити всі сервіси: Ctrl+C.

Що запускається: портал (8080) та завдання 1, 2, 5, 7, 10.
Завдання 3, 6, 8, 9 - це файли, їх віддає портал.
Завдання 4 (Pwn) потребує Linux-бінарника, тому без Docker/WSL недоступне.
"""
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORTAL = ROOT / "portal"
DL = PORTAL / "downloads"

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def say(msg):
    print(msg, flush=True)


def ensure_deps():
    missing = []
    for mod, pkg in (("flask", "flask"), ("jwt", "pyjwt")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        say(f"[*] Встановлюю залежності: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])


def load_env():
    """Читає .env; якщо файлу немає - створює з випадковим SECRET_KEY."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        env_file.write_text(f"SECRET_KEY={secrets.token_hex(32)}\nPUBLIC_HOST=localhost\n", encoding="utf-8")
        say("[*] Створено .env з випадковим SECRET_KEY")
    values = {}
    for ln in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split("=", 1)
            values[k.strip()] = v.strip()
    return values


def flags():
    sys.path.insert(0, str(PORTAL))
    import challenges
    return {c["id"]: c["flag"] for c in challenges.CHALLENGES}


def run_py(script, cwd):
    subprocess.check_call([sys.executable, script], cwd=cwd, env=ENV)


def prepare(fl):
    DL.mkdir(parents=True, exist_ok=True)

    # Flag 1: репозиторій .git всередині app/ (прапор у .git/config)
    app1 = ROOT / "flag1_git_leak" / "app"
    if not (app1 / ".git" / "config").exists():
        say("[*] Flag 1: створюю .git")
        shutil.rmtree(app1 / ".git", ignore_errors=True)
        if shutil.which("git"):
            def git(*a):
                subprocess.check_call(["git", *a], cwd=app1, stdout=subprocess.DEVNULL)
            git("init", "-q")
            git("config", "user.email", "dev@titan.local")
            git("config", "user.name", "titan-dev")
            git("add", "index.html")
            git("commit", "-q", "-m", "initial monitoring page")
            git("config", "titan.note", "backup-token")
            git("config", "titan.flag", fl[1])
        else:
            say("    git не знайдено - створюю мінімальний .git вручну")
            g = app1 / ".git"
            (g / "objects").mkdir(parents=True)
            (g / "refs").mkdir()
            (g / "HEAD").write_text("ref: refs/heads/master\n")
            (g / "config").write_text(
                "[core]\n\trepositoryformatversion = 0\n\tfilemode = false\n\tbare = false\n"
                f"[titan]\n\tnote = backup-token\n\tflag = {fl[1]}\n")

    # Flag 3: production.conf.enc
    d3 = ROOT / "flag3_crypto_rev"
    if not (DL / "production.conf.enc").exists():
        say("[*] Flag 3: генерую production.conf.enc")
        run_py("encryptor.py", d3)
        shutil.copy(d3 / "production.conf.enc", DL)
        shutil.copy(d3 / "config_loader.py", DL)

    # Flag 6: файл драйвера
    shutil.copy(ROOT / "flag6_kernel_scada" / "scada_driver.c", DL)

    # Flag 8: RSA (генерується один раз, щоб n і c не змінювались між запусками)
    d8 = ROOT / "flag8_crypto_rsa"
    if not (DL / "output.txt").exists():
        say("[*] Flag 8: генерую RSA-завдання")
        (d8 / "flag.txt").write_text(fl[8])
        try:
            run_py("encrypt.py", d8)
        finally:
            (d8 / "flag.txt").unlink(missing_ok=True)
        shutil.copy(d8 / "output.txt", DL)
        shutil.copy(d8 / "encrypt.py", DL)

    # Flag 9: access.log
    d9 = ROOT / "flag9_forensics"
    if not (DL / "access.log").exists():
        say("[*] Flag 9: генерую access.log")
        (d9 / "flag.txt").write_text(fl[9])
        try:
            run_py("gen_logs.py", d9)
        finally:
            (d9 / "flag.txt").unlink(missing_ok=True)
        shutil.copy(d9 / "access.log", DL)


def flask_proc(directory, port, module="app", extra_env=None):
    code = (f"import sys; sys.path.insert(0, r'{directory}'); import {module} as m; "
            f"m.app.run(host='0.0.0.0', port={port}, threaded=True)")
    env = dict(ENV, **(extra_env or {}))
    return subprocess.Popen([sys.executable, "-c", code], cwd=directory, env=env)


def main():
    ensure_deps()
    env_vals = load_env()
    fl = flags()
    prepare(fl)

    procs = []
    services = []

    def add(name, port, proc, url=None):
        procs.append((name, proc))
        services.append((name, url or f"http://localhost:{port}"))

    add("Портал", 8080, flask_proc(PORTAL, 8080, extra_env={
        "SECRET_KEY": env_vals.get("SECRET_KEY", secrets.token_hex(32)),
        "PUBLIC_HOST": env_vals.get("PUBLIC_HOST", "localhost"),
    }))
    add("Flag 1", 8081, subprocess.Popen(
        [sys.executable, "-m", "http.server", "8081", "--bind", "0.0.0.0",
         "--directory", str(ROOT / "flag1_git_leak" / "app")],
        env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    add("Flag 2", 8082, flask_proc(ROOT / "flag2_jwt_api", 8082, module="app_local"))
    add("Flag 5", 8085, flask_proc(ROOT / "flag5_ad_sim", 8085))
    add("Flag 7", 8087, flask_proc(ROOT / "flag7_sqli_web", 8087))
    add("Flag 10", 8090, flask_proc(ROOT / "flag10_lfi", 8090))

    time.sleep(2)
    say("\n[+] Operation Titan CTF запущено:")
    for name, url in services:
        say(f"    {name:8} {url}")
    say("    Flag 3, 6, 8, 9 - файли на порталі; Flag 4 (Pwn) без Docker/WSL недоступне")
    say("\nCtrl+C - зупинити все\n")

    try:
        while True:
            time.sleep(2)
            for name, p in procs:
                if p.poll() is not None:
                    say(f"[!] {name} завершився з кодом {p.returncode}")
                    procs[:] = [(n, q) for n, q in procs if q is not p]
                    break
            if not procs:
                break
    except KeyboardInterrupt:
        pass
    finally:
        say("\n[*] Зупиняю сервіси...")
        for _, p in procs:
            p.terminate()
        for _, p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
