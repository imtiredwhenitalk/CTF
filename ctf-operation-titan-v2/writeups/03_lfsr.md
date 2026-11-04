# 03. LFSR Reversing (200 балів) — розв'язок

Прапор: `CTF{lfsr_1s_n0t_s3cur3_3n0ugh}`

## Вразливість

Шифр — потоковий LFSR із 16-бітним станом. Ключовий потік повністю визначається
початковим `seed`, а простір seed-ів — лише `2^16 = 65536` значень. Перебираємо всі
seed-и, розшифровуємо `flag.enc` і шукаємо результат у форматі `CTF{...}`.

Файли `encrypt.py` та `flag.enc` доступні з веб-сторінки завдання.

## Експлойт

```python
from pathlib import Path

def lfsr(seed, taps, length):
    state = seed
    out = []
    for _ in range(length):
        out.append(state & 1)
        bit = 0
        for t in taps:
            bit ^= (state >> t) & 1
        state = (state >> 1) | (bit << 15)
    return out

def decrypt(data: bytes, seed: int) -> bytes:
    bits = lfsr(seed, [0, 2, 3, 5], len(data) * 8)
    res = bytearray()
    for i, byte in enumerate(data):
        key_byte = int("".join(map(str, bits[i * 8:(i + 1) * 8])), 2)
        res.append(byte ^ key_byte)
    return bytes(res)

data = Path("flag.enc").read_bytes()
for seed in range(65536):
    plain = decrypt(data, seed)
    if plain.startswith(b"CTF{") and plain.endswith(b"}"):
        print(seed, plain.decode())
```

Результат:

```text
47011 CTF{lfsr_1s_n0t_s3cur3_3n0ugh}
```

## Прапор

```text
CTF{lfsr_1s_n0t_s3cur3_3n0ugh}
```
