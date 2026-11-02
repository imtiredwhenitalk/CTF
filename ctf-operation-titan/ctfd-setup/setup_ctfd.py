import re
import time

import requests

CTFD_URL = "http://ctfd:8000"
session = requests.Session()

def get_nonce(html):
    # Оновлений парсер, який працює з новими версіями CTFd (одинарні та подвійні лапки)
    match = re.search(r"""csrfNonce["']?\s*:\s*["']([^"']+)["']""", html, re.IGNORECASE)
    if match: return match.group(1)
    match = re.search(r'name="nonce"\s+value="([^"]+)"', html)
    if match: return match.group(1)
    return None

def wait_for_ctfd():
    print("[*] Waiting for CTFd to boot...")
    for _ in range(40):
        try:
            r = session.get(f"{CTFD_URL}/setup", timeout=15)
            if r.status_code == 200:
                print("[+] CTFd is up!")
                return r.text
        except requests.exceptions.RequestException as exc:
            print(f"[-] CTFd is not ready yet: {exc}")
        time.sleep(3)
    raise Exception("CTFd timeout")

def do_setup(html):
    nonce = get_nonce(html)
    if not nonce:
        print("[-] Already setup or nonce not found")
        return False
    
    setup_data = {
        "ctf_name": "Operation Titan",
        "name": "admin",
        "email": "admin@titan.local",
        "password": "admin",
        "user_mode": "users",
        "challenge_visibility": "public",
        "account_visibility": "public",
        "score_visibility": "public",
        "registration_visibility": "public",
        "verify_emails": "false",
        "ctf_theme": "core",
        "nonce": nonce
    }
    r = session.post(f"{CTFD_URL}/setup", data=setup_data, timeout=15)
    print(f"Setup response: {r.status_code}")
    return r.status_code in (200, 302)

def main():
    html = wait_for_ctfd()
    if do_setup(html):
        print("[*] Generating API Token...")
        # Login
        login_page = session.get(f"{CTFD_URL}/login").text
        nonce = get_nonce(login_page)
        login = session.post(
            f"{CTFD_URL}/login",
            data={"name": "admin", "password": "admin", "nonce": nonce},
            timeout=15,
        )
        if login.status_code not in (200, 302):
            print(f"[-] CTFd login failed: {login.status_code} {login.text}")
            return
        
        # Get Token
        token_page = session.get(f"{CTFD_URL}/settings/tokens").text
        nonce = get_nonce(token_page)
        if not nonce:
            print("[-] Could not find the token page CSRF nonce.")
            return
        r = session.post(
            f"{CTFD_URL}/api/v1/tokens",
            json={"expiration": ""},
            headers={"CSRF-Token": nonce},
            timeout=15,
        )
        
        if r.status_code != 200:
            print(f"[-] Failed to generate token: {r.text}")
            return
            
        token = r.json()["data"]["value"]
        
        chals = [
            ("01. Encrypted Operations Archive", "Crypto/Web", "Find the hidden archive, reconstruct its password from distributed logs, and decrypt the telemetry. (http://localhost:8001)", 100, "CTF{0ps_arch1ve_bur13d}"),
            ("02. JWT Alg Confusion", "Web", "Exploit JWT algorithm confusion (RS256 to HS256). (http://localhost:8002)", 200, "CTF{jwt_4lg_c0nfus10n_byp4ss}"),
            ("03. LFSR Reversing", "Crypto", "Custom stream cipher. Can you reverse it? (http://localhost:8003)", 200, "CTF{lfsr_1s_n0t_s3cur3_3n0ugh}"),
            ("04. Pickle & HMAC", "Web/Pwn", "Bypass weak HMAC to deserialize a payload. (http://localhost:8004)", 300, "CTF{d3s3r14l1z4t10n_hm4c_byp4ss}"),
            ("05. JWT & RSA", "Crypto", "Factorize RSA to decrypt the admin flag. (http://localhost:8005)", 300, "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"),
            ("06. AES ECB Block", "Crypto", "Manipulate the ECB blocks to become admin. (http://localhost:8006)", 300, "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}"),
            ("07. Blind SQLi WAF", "Web", "Strict WAF. Use blind boolean SQL injection. (http://localhost:8007)", 400, "CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}"),
            ("08. RSA Wiener's Attack", "Crypto", "The private key 'd' is too small. (http://localhost:8008)", 400, "CTF{w13n3r_4tt4ck_d_1s_t00_sm4ll}"),
            ("09. AES Steganography", "Forensics", "The image hides a secret ZIP. Extract and decrypt. (http://localhost:8009)", 300, "CTF{st3g0_4nd_43s_1s_fun}"),
            ("10. LFI to RCE", "Web", "Exploit Local File Inclusion to read the secret. (http://localhost:8010)", 300, "CTF{lf1_t0_rc3_p01s0n1ng_pr0}")
        ]
        
        headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
        for name, cat, desc, pts, flag in chals:
            c_data = {"name": name, "category": cat, "description": desc, "value": pts, "type": "standard", "state": "visible"}
            r = session.post(
                f"{CTFD_URL}/api/v1/challenges",
                json=c_data,
                headers=headers,
                timeout=15,
            )
            if r.status_code == 200:
                c_id = r.json()["data"]["id"]
                session.post(
                    f"{CTFD_URL}/api/v1/flags",
                    json={"challenge_id": c_id, "content": flag, "type": "static"},
                    headers=headers,
                    timeout=15,
                )
                print(f"[+] Created: {name}")
            else:
                print(f"[-] Failed to create {name}: {r.status_code} {r.text}")
        print("[+] All challenges provisioned!")

if __name__ == '__main__':
    main()
