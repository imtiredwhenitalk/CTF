# Writeup: Flag 5 - Domain Takeover

1. Відкрити `http://localhost:8085`.
2. Запитати TGS-квиток для сервісного акаунта `svc_backup` (SPN `MSSQLSvc/db.titan.local:1433`, realm `TITAN.LOCAL`).
3. У відповіді прийде рядок виду `$krb5tgs$23$*svc_backup$TITAN.LOCAL$MSSQLSvc/db.titan.local:1433*$<hex>`.
   Це навчальна імітація, не справжній формат John/Hashcat (mode 13100 тут не підійде) - частина після
   останнього `*$` (тобто сам `<hex>`) є паролем службового акаунта, зашифрованим XOR-ключем, похідним
   від SPN і realm, які видно прямо на сторінці.
4. Порахувати ключ: `key = sha256(f"{spn}${realm}".encode()).digest()`, де
   `spn = "MSSQLSvc/db.titan.local:1433"`, `realm = "TITAN.LOCAL"`.
5. Розшифрувати hex-блок циклічним XOR із цим ключем:

```python
import hashlib, itertools

spn = "MSSQLSvc/db.titan.local:1433"
realm = "TITAN.LOCAL"
hexblob = "..."  # усе, що йде після останнього *$ у відповіді сервера

key = hashlib.sha256(f"{spn}${realm}".encode()).digest()
enc = bytes.fromhex(hexblob)
flag = bytes(b ^ k for b, k in zip(enc, itertools.cycle(key))).decode()
print(flag)
```

6. Отримати прапор: `CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}`.
