# LNTU Local Cyber Range (Університетський CTF ЛНТУ)

Готовий до локального розгортання CTF для студентів та заходів ЛНТУ.

## 🚀 Швидкий запуск
```bash
chmod +x setup.sh
./setup.sh
```

Після запуску сервіси будуть доступні за адресами:
- **CTFd Платформа:** http://localhost:8000
- **Таск 1 (ВолиньГаз CTF - SSTI/Auth):** http://localhost:8081
- **Таск 2 (ВолиньВода CTF - IDOR/LFI):** http://localhost:8082
- **Таск 3 (XSS Blog CTF - Stored XSS + Bot):** http://localhost:8083
- **Таск 4 (Затвор CTF - SQL Injection/Bypass):** http://localhost:8084
- **Таск 5 (Buffer Overflow PWN):** `nc localhost 1337`

---

## 🚩 Прапори для перевірки
1. `CTF{v0lyn_g4s_sst1_3xpl01t_2026}`
2. `CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}`
3. `CTF{xss_st0r3d_4dm1n_c00k13_st34l}`
4. `CTF{z4tv0r_sqli_byp4ss_m4st3r}`
5. `CTF{pwn_lntu_st4ck_0v3rfl0w_r00t}`

---

## ⚙️ Автоматичний імпорт у CTFd
1. Зареєструйте акаунт адміна на `http://localhost:8000`.
2. В налаштуваннях профілю (Settings -> Access Tokens) згенеруйте API Token.
3. Виконайте автоматичний імпорт завдань:
```bash
python3 scripts/populate_ctfd.py --url http://localhost:8000 --token <YOUR_TOKEN>
```
