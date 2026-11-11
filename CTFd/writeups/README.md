# Operation Titan — Writeups

Розв'язки до всіх 12 завдань. Кожен файл містить стислий опис вразливості, повний
експлойт/скрипт і прапор.

| # | Завдання | Категорія | Балів | Writeup |
|---|---|---|---|---|
| 01 | SSTI Comms Console | Web | 100 | [01_ssti.md](01_ssti.md) |
| 02 | JWT Alg Confusion | Web | 200 | [02_jwt.md](02_jwt.md) |
| 03 | LFSR Reversing | Crypto | 200 | [03_lfsr.md](03_lfsr.md) |
| 04 | Pickle & HMAC | Web/Pwn | 300 | [04_pickle.md](04_pickle.md) |
| 05 | JWT & RSA | Crypto | 300 | [05_jwt_rsa.md](05_jwt_rsa.md) |
| 06 | AES ECB Oracle | Crypto | 500 | [06_ecb.md](06_ecb.md) |
| 07 | Blind SQLi WAF | Web | 400 | [07_sqli.md](07_sqli.md) |
| 08 | RSA Wiener's Attack | Crypto | 400 | [08_wiener.md](08_wiener.md) |
| 09 | Hidden Archive | Forensics | 300 | [09_stego.md](09_stego.md) |
| 10 | LFI to RCE | Web | 300 | [10_lfi.md](10_lfi.md) |
| 11 | Binance API Heist | Web | 500 | [../../ctf-operation-titan-v2/flag11_binance/writeup.md](../../ctf-operation-titan-v2/flag11_binance/writeup.md) |
| 12 | Token Forge | Web | 300 | [12_token_forge.md](12_token_forge.md) |

Адреси взяті з `ctf-operation-titan-v2/docker-compose.yml`:

- напряму: `http://10.10.15.124:8001` … `:8012` (порти як у compose);
- через VPN: `172.28.0.11` … `172.28.0.22`; завдання 03, 08, 09, 11 слухають порт `80`,
  решта — `5000`.

Завдання **10. LFI to RCE** має динамічний прапор, прив'язаний до VPN-адреси
гравця. Перед розв'язком отримайте `.ovpn` на VPN-порталі під тією самою
назвою команди, що й у CTFd. Прямий доступ через `:8010` поверне повідомлення без прапора, який
зарахує CTFd.

Усі скрипти нижче використовують `requests`; для криптозадач додатково потрібен
`pycryptodome` лише там, де це явно вказано.
