import os, re, sys, time
import requests

CTFD_URL = os.environ.get("CTFD_URL", "http://ctfd:8000")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")

s = requests.Session()

NONCE_PATTERNS = [
    r'name="nonce"[^>]*?value="([^"]+)"',
    r'value="([^"]+)"[^>]*?name="nonce"',
    r"""csrfNonce['"]?\s*[:=]\s*['"]([A-Za-z0-9]+)['"]""",
]


def get_nonce(html):
    for pat in NONCE_PATTERNS:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


# (name, category, points, flag, vpn_ip, internal_port, host_port, description)
CHALLENGES = [
    ("01. Git Leak & XOR", "Crypto/Web", 100, "CTF{g1t_l34k_4nd_x0r_m4st3r}", "172.28.0.11", 80, 8001,
     "We leaked the source. Find the flag."),
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


def wait_for_ctfd():
    print("[*] Waiting for CTFd to boot...", flush=True)
    for _ in range(120):
        try:
            r = s.get(f"{CTFD_URL}/setup", timeout=10)
            if r.status_code == 200:
                print("[+] CTFd is up!", flush=True)
                return r
        except requests.exceptions.RequestException:
            pass
        time.sleep(3)
    sys.exit("[-] CTFd timeout")


def do_setup(r):
    nonce = get_nonce(r.text) if r.url.rstrip("/").endswith("/setup") else None
    if not nonce:
        print("[=] CTFd is already set up, skipping initial setup", flush=True)
        return
    data = {
        "ctf_name": "Operation Titan", "ctf_description": "Operation Titan CTF",
        "user_mode": "users", "challenge_visibility": "public", "account_visibility": "public",
        "score_visibility": "public", "registration_visibility": "public",
        "verify_emails": "false", "team_size": "", "name": ADMIN_NAME, "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD, "ctf_theme": "core", "theme_color": "",
        "start": "", "end": "", "nonce": nonce,
    }
    r = s.post(f"{CTFD_URL}/setup", data=data, timeout=60)
    print(f"[+] Setup submitted (HTTP {r.status_code})", flush=True)


def login():
    page = s.get(f"{CTFD_URL}/login", timeout=30).text
    nonce = get_nonce(page)
    if not nonce:
        sys.exit("[-] Cannot find login nonce")
    s.post(f"{CTFD_URL}/login", data={"name": ADMIN_NAME, "password": ADMIN_PASSWORD, "nonce": nonce},
           timeout=30)
    me = s.get(f"{CTFD_URL}/api/v1/users/me", timeout=30)
    try:
        ok = me.json()["data"]["type"] == "admin"
    except Exception:
        ok = False
    if not ok:
        sys.exit("[-] Admin login failed (wrong ADMIN_PASSWORD? old DB volume? run: docker compose down -v)")
    print("[+] Logged in as admin", flush=True)


def main():
    do_setup(wait_for_ctfd())
    login()

    csrf = get_nonce(s.get(f"{CTFD_URL}/admin/challenges", timeout=30).text)
    if not csrf:
        sys.exit("[-] Cannot find CSRF nonce on admin page")
    hdr = {"CSRF-Token": csrf, "Content-Type": "application/json"}

    existing = {c["name"] for c in s.get(f"{CTFD_URL}/api/v1/challenges", timeout=30).json().get("data", [])}
    errors = 0
    for name, cat, pts, flag, ip, iport, hport, text in CHALLENGES:
        if name in existing:
            print(f"[=] Exists: {name}", flush=True)
            continue
        desc = (f"{text}\n\n"
                f"**VPN:** http://{ip}{'' if iport == 80 else f':{iport}'}  \n"
                f"**Direct:** http://{SERVER_HOST}:{hport}")
        r = s.post(f"{CTFD_URL}/api/v1/challenges", headers=hdr, timeout=30, json={
            "name": name, "category": cat, "description": desc, "value": pts,
            "type": "standard", "state": "visible"})
        if r.status_code != 200 or not r.json().get("success"):
            print(f"[-] Challenge '{name}' failed: {r.status_code} {r.text[:200]}", flush=True)
            errors += 1
            continue
        cid = r.json()["data"]["id"]
        fr = s.post(f"{CTFD_URL}/api/v1/flags", headers=hdr, timeout=30,
                    json={"challenge_id": cid, "content": flag, "type": "static", "data": ""})
        if fr.status_code != 200 or not fr.json().get("success"):
            print(f"[-] Flag for '{name}' failed: {fr.status_code} {fr.text[:200]}", flush=True)
            errors += 1
            continue
        print(f"[+] Created: {name}", flush=True)

    if errors:
        sys.exit(f"[-] Finished with {errors} error(s)")
    print("[+] All challenges provisioned!", flush=True)


if __name__ == "__main__":
    main()
