# 05. JWT & RSA (300 балів) — розв'язок

Прапор: `CTF{jwt_cr4ck3d_rs4_f4ct0r3d}`

## Крок 1. Слабкий секрет JWT

Головна сторінка віддає гостьовий токен, підписаний `HS256`. Секрет —
`123456`, його можна підібрати словником:

```bash
hashcat -m 16500 guest.jwt /usr/share/wordlists/rockyou.txt
```

або вручну:

```python
import jwt
print(jwt.decode(guest_token, "123456", algorithms=["HS256"]))
```

Після цього генеруємо адмін-токен:

```python
import jwt, requests
BASE = "http://10.10.15.124:8005"          # через VPN: http://172.28.0.15:5000
admin = jwt.encode({"role": "admin"}, "123456", algorithm="HS256")
r = requests.get(f"{BASE}/admin", headers={"Authorization": admin})
print(r.json())
```

`/admin` повертає `n`, `e` та список `enc` — по одному RSA-блокові на символ прапора.

## Крок 2. Факторизація RSA

`n = 54173879` — лише 26 біт, тому факторизується миттєво:

```text
n = 54173879 = 6841 * 7919
phi = (6841 - 1) * (7919 - 1)
d = e^(-1) mod phi = 379313
```

## Крок 3. Розшифрування

Кожен символ шифрувався окремо: `enc[i] = ord(char)^e mod n`. Тому:

```python
import requests, jwt

BASE = "http://10.10.15.124:8005"
admin = jwt.encode({"role": "admin"}, "123456", algorithm="HS256")
data = requests.get(f"{BASE}/admin", headers={"Authorization": admin}).json()

n, e, enc = data["n"], data["e"], data["enc"]
p, q = 6841, 7919
d = pow(e, -1, (p - 1) * (q - 1))
flag = "".join(chr(pow(c, d, n)) for c in enc)
print(flag)
```

## Прапор

```text
CTF{jwt_cr4ck3d_rs4_f4ct0r3d}
```
