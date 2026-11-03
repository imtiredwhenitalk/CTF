import html
import os
import re
import sys
import time

import requests

CTFD_URL = os.environ.get("CTFD_URL", "http://ctfd:8000").rstrip("/")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@titan.local")
SERVER_HOST = os.environ.get("SERVER_HOST", "10.10.15.124")
TIMEOUT = 30

s = requests.Session()
s.headers.update({"User-Agent": "operation-titan-ctfd-setup/2"})

NONCE_PATTERNS = [
    r'name=["\']nonce["\'][^>]*?value=["\']([^"\']+)["\']',
    r'value=["\']([^"\']+)["\'][^>]*?name=["\']nonce["\']',
    r"""csrfNonce["']?\s*[:=]\s*["']([A-Za-z0-9]+)["']""",
]


def get_nonce(page):
    for pattern in NONCE_PATTERNS:
        match = re.search(pattern, page, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_setup_page(page):
    return 'id="setup-form"' in page or 'action="/setup"' in page


def html_snippet(page, limit=600):
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


# (name, category, points, flag, vpn_ip, internal_port, host_port, description)
CHALLENGES = [
    ("01. SSTI Comms Console", "Web", 100, "CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}", "172.28.0.11", 5000, 8001,
     "Консоль зв'язку Titan рендерить позивні операторів через шаблонізатор. Дістаньтеся внутрішнього прапора."),
    ("02. JWT Alg Confusion", "Web", 200, "CTF{jwt_4lg_c0nfus10n_byp4ss}", "172.28.0.12", 5000, 8002,
     "Exploit JWT algorithm confusion (RS256 to HS256)."),
    ("03. LFSR Reversing", "Crypto", 200, "CTF{lfsr_1s_n0t_s3cur3_3n0ugh}", "172.28.0.13", 80, 8003,
     "Custom stream cipher. Can you reverse it?"),
    ("04. Pickle & HMAC", "Web/Pwn", 300, "CTF{d3s3r14l1z4t10n_hm4c_byp4ss}", "172.28.0.14", 5000, 8004,
     "Bypass weak HMAC to deserialize a payload."),
    ("05. JWT & RSA", "Crypto", 300, "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}", "172.28.0.15", 5000, 8005,
     "Crack the token, then factorize RSA to decrypt the admin flag."),
    ("06. AES ECB Block", "Crypto", 300, "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}", "172.28.0.16", 5000, 8006,
     "Manipulate the ECB blocks to become admin."),
    ("07. Blind SQLi WAF", "Web", 400, "CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}", "172.28.0.17", 5000, 8007,
     "Strict WAF. Use blind boolean SQL injection."),
    ("08. RSA Wiener's Attack", "Crypto", 400, "CTF{w13n3r_4tt4ck_d_1s_t00_sm4ll}", "172.28.0.18", 80, 8008,
     "The private key 'd' is too small."),
    ("09. Hidden Archive", "Forensics", 300, "CTF{st3g0_4nd_43s_1s_fun}", "172.28.0.19", 80, 8009,
     "The image hides a secret ZIP. Extract and decrypt."),
    ("10. LFI to RCE", "Web", 300, "CTF{lf1_t0_rc3_p01s0n1ng_pr0}", "172.28.0.20", 5000, 8010,
     "Exploit Local File Inclusion to read the secret."),
]

# Old names that must disappear when a challenge is replaced.
OBSOLETE_CHALLENGES = {
    "01. Git Leak & XOR",
    "Git Leak & XOR",
}


def wait_for_ctfd():
    print("[*] Waiting for CTFd to boot...", flush=True)
    for _ in range(150):
        try:
            response = s.get(f"{CTFD_URL}/setup", timeout=10)
            if response.status_code == 200:
                print(f"[+] CTFd is up ({response.url})", flush=True)
                return response
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    sys.exit("[-] CTFd timeout")


def do_setup(response):
    if not is_setup_page(response.text):
        print("[=] CTFd is already set up, skipping initial setup", flush=True)
        return

    nonce = get_nonce(response.text)
    if not nonce:
        sys.exit("[-] Cannot find setup nonce")

    data = {
        "ctf_name": "Operation Titan",
        "ctf_description": "Operation Titan CTF",
        "user_mode": "users",
        "challenge_visibility": "public",
        "account_visibility": "public",
        "score_visibility": "public",
        "registration_visibility": "public",
        "verify_emails": "false",
        "team_size": "",
        "name": ADMIN_NAME,
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "ctf_theme": "core",
        "theme_color": "",
        "start": "",
        "end": "",
        "social_shares": "false",
        "nonce": nonce,
    }

    for attempt in range(1, 4):
        try:
            result = s.post(f"{CTFD_URL}/setup", data=data, timeout=60)
        except requests.exceptions.RequestException as exc:
            print(f"[!] Setup request failed ({exc}); retry {attempt}/3", flush=True)
            time.sleep(3)
            continue

        if result.status_code == 200 and not is_setup_page(result.text):
            print(f"[+] Setup submitted (HTTP {result.status_code})", flush=True)
            return

        # CTFd re-renders the setup form with validation errors (HTTP 200).
        # Refresh the nonce in case the session was rotated before retrying.
        fresh = get_nonce(result.text)
        if fresh:
            data["nonce"] = fresh
        print(f"[!] Setup attempt {attempt}/3 failed (HTTP {result.status_code}): "
              f"{html_snippet(result.text)}", flush=True)
        time.sleep(3)

    sys.exit("[-] CTFd setup failed")


def check_admin():
    """Return True when the session is authenticated as an admin.

    CTFd's /api/v1/users/me no longer exposes a ``type`` field, so verify
    admin access against an admin-only page instead (a normal user is
    redirected to /login).
    """
    try:
        response = s.get(f"{CTFD_URL}/api/v1/users/me", timeout=TIMEOUT)
        if response.status_code != 200:
            return False
        payload = response.json()
        if not payload.get("success") or not payload.get("data", {}).get("id"):
            return False

        admin_page = s.get(f"{CTFD_URL}/admin/challenges", timeout=TIMEOUT)
        return admin_page.status_code == 200 and "/admin/" in admin_page.url
    except (requests.exceptions.RequestException, ValueError):
        return False


def login():
    for attempt in range(1, 6):
        if check_admin():
            print("[+] Logged in as admin", flush=True)
            return

        try:
            page = s.get(f"{CTFD_URL}/login", timeout=TIMEOUT).text
        except requests.exceptions.RequestException as exc:
            print(f"[!] Login page failed ({exc}); retry {attempt}/5", flush=True)
            time.sleep(3)
            continue

        nonce = get_nonce(page)
        if not nonce:
            print(f"[!] Cannot find login nonce; retry {attempt}/5", flush=True)
            time.sleep(3)
            continue

        try:
            s.post(
                f"{CTFD_URL}/login",
                data={"name": ADMIN_NAME, "password": ADMIN_PASSWORD, "nonce": nonce},
                timeout=TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            print(f"[!] Login request failed ({exc}); retry {attempt}/5", flush=True)
            time.sleep(3)
            continue

        if check_admin():
            print("[+] Logged in as admin", flush=True)
            return
        time.sleep(2)

    sys.exit("[-] Admin login failed (wrong ADMIN_PASSWORD or stale database? "
             "Try: docker compose down -v)")


def get_csrf():
    try:
        page = s.get(f"{CTFD_URL}/admin/challenges", timeout=TIMEOUT).text
    except requests.exceptions.RequestException as exc:
        sys.exit(f"[-] Cannot load admin page: {exc}")
    nonce = get_nonce(page)
    if not nonce:
        sys.exit("[-] Cannot find CSRF nonce on admin page")
    return nonce


def api(method, path, **kwargs):
    response = s.request(
        method,
        f"{CTFD_URL}{path}",
        headers={"CSRF-Token": CSRF, "Content-Type": "application/json"},
        timeout=TIMEOUT,
        **kwargs,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    return response, payload


def api_ok(response, payload):
    return response.ok and payload.get("success") is True


def list_challenges():
    response, payload = api("GET", "/api/v1/challenges?view=admin")
    if not api_ok(response, payload):
        sys.exit(f"[-] Cannot list challenges: HTTP {response.status_code} {response.text[:200]}")
    return {challenge["name"]: challenge["id"] for challenge in payload.get("data", [])}


def delete_obsolete(existing):
    failures = 0
    for name in sorted(OBSOLETE_CHALLENGES):
        challenge_id = existing.pop(name, None)
        if challenge_id is None:
            continue
        response, payload = api("DELETE", f"/api/v1/challenges/{challenge_id}")
        if api_ok(response, payload):
            print(f"[+] Removed obsolete challenge: {name}", flush=True)
        else:
            print(f"[-] Could not remove obsolete challenge '{name}': "
                  f"HTTP {response.status_code} {response.text[:200]}", flush=True)
            failures += 1
    return failures


def ensure_flag(challenge_id, flag):
    response, payload = api("GET", f"/api/v1/challenges/{challenge_id}/flags")
    if not api_ok(response, payload):
        return False, f"HTTP {response.status_code} {response.text[:200]}"

    flags = payload.get("data", [])
    flag_data = {
        "challenge_id": challenge_id,
        "content": flag,
        "type": "static",
        "data": "",
    }
    if flags:
        flag_id = flags[0]["id"]
        response, payload = api("PATCH", f"/api/v1/flags/{flag_id}",
                                json={"content": flag, "type": "static", "data": ""})
    else:
        response, payload = api("POST", "/api/v1/flags", json=flag_data)

    if not api_ok(response, payload):
        return False, f"HTTP {response.status_code} {response.text[:200]}"
    return True, ""


def main():
    global CSRF

    do_setup(wait_for_ctfd())
    login()
    CSRF = get_csrf()

    existing = list_challenges()
    errors = delete_obsolete(existing)

    for name, category, points, flag, vpn_ip, internal_port, host_port, text in CHALLENGES:
        description = (
            f"{text}\n\n"
            f"**VPN:** http://{vpn_ip}{'' if internal_port == 80 else f':{internal_port}'}  \n"
            f"**Direct:** http://{SERVER_HOST}:{host_port}"
        )
        challenge_data = {
            "name": name,
            "category": category,
            "description": description,
            "value": points,
            "type": "standard",
            "state": "visible",
        }

        challenge_id = existing.get(name)
        if challenge_id is None:
            response, payload = api("POST", "/api/v1/challenges", json=challenge_data)
            if not api_ok(response, payload):
                print(f"[-] Challenge '{name}' failed: "
                      f"HTTP {response.status_code} {response.text[:200]}", flush=True)
                errors += 1
                continue
            challenge_id = payload["data"]["id"]
            action = "Created"
        else:
            response, payload = api("PATCH", f"/api/v1/challenges/{challenge_id}",
                                    json=challenge_data)
            if not api_ok(response, payload):
                print(f"[-] Challenge '{name}' update failed: "
                      f"HTTP {response.status_code} {response.text[:200]}", flush=True)
                errors += 1
                continue
            action = "Updated"

        ok, error = ensure_flag(challenge_id, flag)
        if not ok:
            print(f"[-] Flag for '{name}' failed: {error}", flush=True)
            errors += 1
            continue

        print(f"[+] {action}: {name}", flush=True)

    errors += verify_provisioning()

    if errors:
        sys.exit(f"[-] Finished with {errors} error(s)")
    print("[+] All challenges provisioned and verified!", flush=True)


def verify_provisioning():
    """Read everything back so a silent API failure cannot leave an empty CTFd."""
    existing = list_challenges()
    errors = 0
    for name, _category, _points, flag, _vpn_ip, _internal_port, _host_port, _text in CHALLENGES:
        challenge_id = existing.get(name)
        if challenge_id is None:
            print(f"[-] Verification failed: challenge '{name}' is missing", flush=True)
            errors += 1
            continue

        response, payload = api("GET", f"/api/v1/challenges/{challenge_id}/flags")
        contents = {item.get("content") for item in payload.get("data", [])}
        if not api_ok(response, payload) or flag not in contents:
            print(f"[-] Verification failed: flag for '{name}' is missing", flush=True)
            errors += 1

    if errors == 0:
        print(f"[+] Verified {len(CHALLENGES)} challenges and their flags", flush=True)
    return errors


if __name__ == "__main__":
    CSRF = ""
    main()
