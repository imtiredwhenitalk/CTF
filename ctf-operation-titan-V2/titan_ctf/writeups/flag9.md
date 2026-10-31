# Writeup: Flag 9 - Ghost Logs (Forensics)

1. Завантажити `access.log` (nginx, формат combined, ~900 рядків).
2. Знайти аномальну IP-адресу. За кількістю запитів вона не виділяється (зловмисник робить лише ~20), тому дивимось на User-Agent та коди відповідей. Більшість запитів - з `10.100.0.x` і браузерними User-Agent:
   `awk -F'"' '{print $6}' access.log | sort | uniq -c | sort -n` - рідкісний `python-requests/2.31.0`
   `grep python-requests access.log | head` - видно IP `185.220.101.47`: сканування (`/.env`, `/.git/config`...) з 403/404, SQL-ін'єкції (`UNION SELECT ... FROM admins`) і далі запити на `/api/export`.
3. Відфільтрувати експорт цієї IP:
   `grep 185.220.101.47 access.log | grep /api/export`
   Є три запити `chunk=1..3` з base64-параметром `d`. Запит від `10.100.0.31` з `report_2026_q3.csv` - хибний слід (легітимний користувач).
4. Запити в логу йдуть **не по порядку**, тому складати частини треба за номером `chunk`, а не за часом.
5. Декодувати кожну частину (base64url без `=`) і зібрати по порядку:

```bash
grep 185.220.101.47 access.log | grep -o 'chunk=[0-9]&d=[A-Za-z0-9_-]*' | sort | \
python3 -c "import sys,base64
for l in sys.stdin:
    d=l.strip().split('d=')[1]; print(base64.urlsafe_b64decode(d+'='*(-len(d)%4)).decode(), end='')"
```

6. Прапор: `CTF{l0g_f0r3ns1cs_f1nds_th3_gh0st_4417}`.
