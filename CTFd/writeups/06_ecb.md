# 06. AES ECB Oracle (500 балів) — розв'язок

Прапор: `CTF{3cb_byt3_4t_4_t1m3_w1th_r4nd0m_pr3f1x}`

> Завдання перероблено: старий варіант віддавав прапор через `/source` і розв'язувався
> одним запитом. Тепер прапора в коді немає — його віддає `/unlock` лише за правильним
> секретним токеном.

## Що робить сервіс

`/api/encrypt?data=...` повертає Base64 від:

```text
AES-ECB( PREFIX || data || "|vault=" || TOKEN )
```

- `PREFIX` — випадкові `0..15` байт, згенеровані при старті процесу (довжина невідома,
  але фіксована);
- `TOKEN` — `secrets.token_hex(16)`, тобто 32 hex-символи, генеруються при старті;
- `KEY` — випадковий AES-ключ, теж лише в пам'яті.

Прапор лежить у `/flag.txt` і повертається тільки після правильного токена. Отже,
потрібно відновити `TOKEN` із шифртексту.

## Ідея атаки

AES-ECB детермінований: однакові 16-байтові блоки відкритого тексту дають однакові
блоки шифртексту. Це дозволяє робити byte-at-a-time атаку.

Нехай `S = "|vault=" + TOKEN`, `N = len(S) = 39`. Для кожного байта `S[j]`:

1. Подаємо на вхід стільки `A`, щоб `S[j]` став **останнім байтом** блоку. Тоді блок
   має вигляд `known15 || S[j]`, де `known15` — 15 уже відомих байтів:
   `(b"A"*15 + S[:j])[-15:]`.
2. Будуємо словник: для кожного кандидата `g` шифруємо
   `A*(...) || known15 || g` і беремо блок, який містить `known15 || g`.
3. Порівнюємо цільовий блок зі словником — збіг дає `S[j]`.

Випадковий `PREFIX` ускладнює вирівнювання, але не ламає атаку: його довжина всього
`0..15`, тож її можна перебрати. Вміст префікса не важливий — ECB залежить лише від
вмісту блоків.

### Вирівнювання

Нехай `p` — довжина префікса (`0..15`), `b = (-p) mod 16`. Після `p + b` байтів
починається межа блоку. Перший повністю контрольований блок `A` має індекс
`i = ceil(p/16)` (для `0 < p < 16` це `1`, для `p = 0` — `0`).

Для байта `S[j]` надсилаємо:

```text
data = b"A" * (b + 16*K + ((15 - j) mod 16)),   K = 2
```

Тоді `S[j]` потрапляє в блок з індексом `i + K + j // 16`.

Словник для кандидата `g`:

```text
data = b"A" * (b + 16*K) + known15 + bytes([g])
```

Блок з індексом `i + K` містить `known15 || g`. Оскільки формат суфікса відомий,
для перших 7 байтів (`|vault=`) кандидат один, а далі перебираємо лише hex-алфавіт.

## Повний експлойт

```python
import base64, requests

BASE = "http://10.10.15.124:8006"          # через VPN: http://172.28.0.16:5000
N = 39                                     # len("|vault=") + 32 hex
KNOWN = b"|vault="
HEX = b"0123456789abcdef"

def encrypt(data: bytes) -> bytes:
    r = requests.get(f"{BASE}/api/encrypt", params={"data": data.decode("ascii")})
    r.raise_for_status()
    return base64.b64decode(r.json()["ciphertext"])

def blocks(ct: bytes):
    return [ct[i:i + 16] for i in range(0, len(ct), 16)]

K = 2
for pcand in range(16):
    b = (-pcand) % 16
    i = 0 if pcand == 0 else 1
    recovered = b""
    ok = True

    for j in range(N):
        known15 = (b"A" * 15 + recovered)[-15:]

        length = b + 16 * K + ((15 - j) % 16)
        target = blocks(encrypt(b"A" * length))[i + K + j // 16]

        candidates = KNOWN[j:j + 1] if j < len(KNOWN) else HEX
        for guess in candidates:
            probe = encrypt(b"A" * (b + 16 * K) + known15 + bytes([guess]))
            if blocks(probe)[i + K] == target:
                recovered += bytes([guess])
                break
        else:
            ok = False
            break

    if ok and recovered.startswith(KNOWN):
        token = recovered[len(KNOWN):].decode()
        print("prefix length:", pcand, "token:", token)
        print(requests.get(f"{BASE}/unlock", params={"token": token}).text)
        break
```

Скрипт робить кілька тисяч запитів (перебір 16 варіантів довжини префікса + словник
по 16 hex-символах), після чого відкриває сховище.

Приклад результату:

```text
prefix length: 7 token: 1f0c...e9a2
... SCADA Overridden! CTF{3cb_byt3_4t_4_t1m3_w1th_r4nd0m_pr3f1x} ...
```

## Прапор

```text
CTF{3cb_byt3_4t_4_t1m3_w1th_r4nd0m_pr3f1x}
```
