import requests, time, re

CTFD_URL = "http://ctfd:8000"
session = requests.Session()

def wait_for_ctfd():
    print("[*] Waiting for CTFd to boot...")
    for _ in range(60):
        try:
            r = session.get(f"{CTFD_URL}/setup")
            if r.status_code == 200:
                print("[+] CTFd is up!")
                return r.text
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    raise Exception("CTFd timeout")

def do_setup(html):
    nonce_match = re.search(r'"csrfNonce":\s*"([^"]+)"', html)
    if not nonce_match:
        print("Already setup or nonce not found")
        return False
    nonce = nonce_match.group(1)
    
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
    r = session.post(f"{CTFD_URL}/setup", data=setup_data)
    print(f"Setup response: {r.status_code}")
    return True

def create_challenge(token, name, category, desc, points, flag):
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    chal_data = {
        "name": name, "category": category, "description": desc,
        "value": points, "type": "standard", "state": "visible"
    }
    r = session.post(f"{CTFD_URL}/api/v1/challenges", json=chal_data, headers=headers)
    if r.status_code != 200: return
    chal_id = r.json()['data']['id']
    
    flag_data = {"challenge_id": chal_id, "content": flag, "type": "static"}
    session.post(f"{CTFD_URL}/api/v1/flags", json=flag_data, headers=headers)
    print(f"[+] Created: {name}")

def main():
    html = wait_for_ctfd()
    if do_setup(html):
        print("[*] Generating API Token...")
        # Login to be sure
        nonce_match = re.search(r'"csrfNonce":\s*"([^"]+)"', session.get(f"{CTFD_URL}/login").text)
        session.post(f"{CTFD_URL}/login", data={"name":"admin","password":"admin","nonce":nonce_match.group(1)})
        
        # Get Token
        nonce_match = re.search(r'"csrfNonce":\s*"([^"]+)"', session.get(f"{CTFD_URL}/settings/tokens").text)
        r = session.post(f"{CTFD_URL}/api/v1/tokens", json={"expiration":""}, headers={"CSRF-Token": nonce_match.group(1)})
        token = r.json()['data']['value']
        
        # Load Challenges
        chals = [
            ("01. Git Leak & XOR", "Crypto/Web", "We leaked the source. Find the flag. (http://localhost:8001)", 100, "CTF{g1t_l34k_4nd_x0r_m4st3r}"),
            ("02. JWT Alg Confusion", "Web", "Exploit JWT algorithm confusion (RS256 to HS256). (http://localhost:8002)", 200, "CTF{jwt_4lg_c0nfus10n_byp4ss}"),
            ("03. LFSR Reversing", "Crypto", "Custom stream cipher. Can you reverse it? (http://localhost:8003)", 200, "CTF{lfsr_1s_n0t_s3cur3_3n0ugh}"),
            ("04. Pickle & HMAC", "Web/Pwn", "Bypass weak HMAC to deserialize a payload. (http://localhost:8004)", 300, "CTF{d3s3r14l1z4t10n_hm4c_byp4ss}"),
            ("05. JWT & RSA", "Crypto", "Factorize RSA to decrypt the admin flag. (http://localhost:8005)", 300, "CTF{jwt_cr4ck3d_rs4_f4ct0r3d}"),
            ("06. AES ECB Block", "Crypto", "Manipulate the ECB blocks to become admin. (http://localhost:8006)", 300, "CTF{43s_3cb_bl0ck_m4n1pul4t10n_m4st3r}"),
            ("07. Blind SQLi WAF", "Web", "Strict WAF. Use blind boolean SQL injection. (http://localhost:8007)", 400, "CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}"),
            ("08. RSA Wiener's Attack", "Crypto", "The private key 'd' is too small. (http://localhost:8008)", 400, "CTF{w13n3r_4tt4ck_d_1s_t00_sm4ll}"),
            ("09. AES Steganography", "Forensics", "The image hides a secret ZIP. Extract and decrypt. (http://localhost:8009)", 300, "CTF{st3g0_4nd_43s_1s_fun}"),
            ("10. LFI to RCE", "Web", "Exploit Local File Inclusion to read the secret. (http://localhost:8010)", 300, "CTF{lf1_t0_rc3_p01s0n1ng_pr0}"),
        ]
        for c in chals:
            create_challenge(token, c[0], c[1], c[2], c[3], c[4])
        print("[+] All challenges provisioned!")

if __name__ == '__main__':
    main()
