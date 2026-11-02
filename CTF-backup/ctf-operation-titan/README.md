# All-Ukrainian CTF: Operation Titan (ОПЕРАЦІЯ: ТИТАН)

Готовий до розгортання архів інфраструктури All-Ukrainian CTF з 6 прапорами за принципом прогресивної складності.

## 🚀 Швидкий старт

### 1. Вимоги
- Linux (Ubuntu 22.04 LTS / Debian 12 recommended)
- Docker & Docker Compose (v2.20+)
- Python 3.10+ (`pip install requests`)

### 2. Запуск інфраструктури
```bash
# Дати права на виконання скрипту
chmod +x setup.sh

# Запустити всі сервіси CTF та CTFd платформу
./setup.sh
```

Після запуску:
- **CTFd Платформа:** http://localhost:8000
- **Flag 1 (Web Recon):** http://localhost:8081
- **Flag 2 (JWT API):** http://localhost:8082
- **Flag 3 (Crypto/Reverse):** у папці `challenges/flag3_crypto_rev/`
- **Flag 4 (PWN Sandbox):** `nc localhost 1337`
- **Flag 5 (AD / Kerberos Sim):** http://localhost:8085
- **Flag 6 (SCADA / Kernel):** у папці `challenges/flag6_kernel_scada/`

---

## Прапори та відповіді (для організаторів)

1. `CTF{w3lc0m3_t0_th3_tr1d3nt_n3tw0rk_2026}`
2. `CTF{jwt_s3cr3ts_sh0uld_n3v3r_b3_w34k}`
3. `CTF{gh1dr4_r3v3rs1ng_m4st3r_9921}`
4. `CTF{pwn_th3_s3rv3r_g3t_th3_r00t}`
5. `CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}`
6. `CTF{0d4y_k3rn3l_m4st3r_ukr41n14n_cyb3r_f0rc3}`

---

## Автоматичне імпортування тасків у CTFd
Після реєстрації первинного адміна в CTFd (http://localhost:8000) виконайте:
```bash
python3 scripts/populate_ctfd.py --url http://localhost:8000 --token <YOUR_CTFD_API_TOKEN>
```
