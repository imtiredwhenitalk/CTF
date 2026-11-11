# Operation Titan — platform stack

Ця папка містить **платформу**: CTFd, базу даних, Redis, OpenVPN, VPN-портал,
внутрішній watermark-сервіс, CTFd-плагін для водяних прапорів, інструменти
адміністратора та writeups.

Самі завдання лежать окремо в [`../ctf-operation-titan-v2`](../ctf-operation-titan-v2).
Такий поділ дозволяє оновлювати платформу, не перебудовуючи 12 контейнерів
завдань, і навпаки.

## Швидкий старт

Рекомендований спосіб — із папки завдань, бо вона піднімає обидва стеки:

```bash
cd ../ctf-operation-titan-v2
chmod +x setup.sh
./setup.sh --reset      # перший запуск (створює PKI, БД, мережі, секрет)
./setup.sh              # звичайний запуск
```

Лише платформа:

```bash
cd CTFd
chmod +x setup.sh
./setup.sh --reset
```

Після старту:

| Сервіс | Адреса |
|---|---|
| CTFd | `http://<PUBLIC_IP>:8000` |
| VPN-портал | `http://<PUBLIC_IP>:5050` |
| OpenVPN | `udp/<PUBLIC_IP>:1194` |
| Watermark | `http://watermark:5060` — лише всередині `titan_internal` |

`PUBLIC_IP` задається у `.env` (за замовчуванням `10.10.15.124`). Його також
можна передати явно:

```bash
PUBLIC_IP=203.0.113.10 ./setup.sh --reset
```

Пароль адміністратора CTFd береться з `ADMIN_PASSWORD` (за замовчуванням
`admin`). Після першого налаштування CTFd змінити пароль можна через
`ADMIN_PASSWORD=... ./setup.sh --reset` (це очистить БД) або через адмінку CTFd.

## Архітектура

```text
                 Internet / LAN
                       |
          +------------+-------------+
          |                          |
   UDP 1194 (OpenVPN)          TCP 8000/5050/8001-8012
          |                          |
   +------+------+            +------+-------+
   |  openvpn    |            |  vpn_portal  |
   | host netns  |            |  172.28.0.3  |
   +------+------+            +------+-------+
          |                          |
          |  titan_net 172.28.0.0/24 |
          +------------+-------------+
                       |
        +--------------+--------------+
        |              |              |
   CTFd 172.28.0.10  challenges   db/cache
        |
        | titan_internal (internal, not routed to VPN)
        |
   watermark 172.28.0.x  <-- LFI challenge calls /flag
```

- `titan_net` — спільна мережа платформи й завдань, `172.28.0.0/24`.
  Фіксовані адреси завдань `.11`–`.22`; динамічний пул Docker — `.128/25`.
- `titan_internal` — приватна мережа без доступу з VPN. У ній живуть
  `watermark`, CTFd і LFI-завдання. Секрет watermark недоступний гравцям.
- OpenVPN працює в `network_mode: host`, тому VPN-клієнти бачать реальні
  адреси `10.8.0.x`, а не NAT-адресу контейнера.

## VPN: одна команда — одна адреса

1. Капітан відкриває VPN-портал і вводить **назву команди** та **пароль**,
   який видав організатор. Назва команди має збігатися з ім'ям користувача
   в CTFd — за ним watermark-плагін перевіряє прапор.
2. `vpn-portal` резервує адресу `10.8.0.10`–`10.8.0.250`, створює клієнтський
   сертифікат і пише:
   - `openvpn-data/conf/ccd/<common-name>` з `ifconfig-push <ip> 255.255.255.0`;
   - `data/user_registry.csv` з `team,common_name,vpn_ip`.
3. OpenVPN читає CCD і видає клієнту саме цю адресу.
4. Повторний вхід повертає той самий профіль та IP.
5. Паролі зберігаються як PBKDF2-хеші в `data/team_credentials.json`;
   самі паролі видає `vpn-portal/admin_teams.py` (див. «Адміністрування»).

У `openvpn.conf`:

```text
server 10.8.0.0 255.255.255.0 nopool
topology subnet
ifconfig-pool 10.8.0.2 10.8.0.9
client-config-dir /etc/openvpn/ccd
push "route 172.28.0.0 255.255.255.0"
```

Динамічний пул `.2`–`.9` залишено для службових підключень; постійні гравці
отримують `.10`–`.250`. `OVPN_NAT=0`: NAT вимкнено навмисно, інакше всі гравці
виглядали б як одна адреса. `nopool` обов'язковий у OpenVPN 2.7, коли
`ifconfig-pool` задано явно.

### OpenVPN 2.7 / DCO

OpenVPN 2.7 з data-channel offloading не приймає compression. `setup.sh`
після генерації видаляє `comp-lzo` та `push "comp-lzo..."` з `openvpn.conf`;
інакше клієнт падає з:

```text
Compression or compression stub framing is not allowed since data-channel offloading is enabled
```

Якщо ви завантажували профіль раніше, видаліть старий `.ovpn` і завантажте новий.

### Маршрутизація без NAT

`CTFd/setup.sh`:

- вмикає `net.ipv4.ip_forward=1`;
- ставить `rp_filter=2` (loose), щоб зворотний трафік із Docker-bridge до
  `10.8.0.x` не відкидався;
- додає в `DOCKER-USER`/`FORWARD` правила `tun0 ↔ br-+`;
- відкриває порти в `ufw`, якщо він активний.

Без цих кроків VPN-клієнт підключиться, але сайти завдань не відкриються.
Скрипт запускайте з `sudo` або з користувача, який має доступ до Docker і
iptables.

## Watermark: унікальний прапор для профілю

- `watermark/watermark.py` — HMAC-логіка. Ідентифікатор — `vpn_ip:challenge_id`.
- `watermark/server.py` — внутрішній сервіс:
  - `GET /flag?ip=...&challenge=lfi_challenge` — видати прапор для VPN-IP;
  - `GET /verify?nickname=...&flag=...` — перевірити для CTFd;
  - `GET /trace?flag=...` — знайти власника витоку;
  - `POST /cheat` — записати спробу надіслати чужий прапор.
- Секрет: `data/watermark.key` (створюється `setup.sh`).
- Журнал: `logs/flag_issuance.log` (`FLAG_ISSUED`, `FLAG_REFUSED`,
  `CHEAT_DETECTED`).

LFI-завдання **не містить** секрету. Воно викликає `http://watermark:5060/flag`
і передає адресу, з якої прийшов запит. Навіть якщо гравець використає RCE,
секрет не лежить у контейнері завдання.

CTFd-плагін `plugins/watermarked/__init__.py` реєструє тип прапора
`watermarked`. Для завдання 10 у БД зберігається прапор із `type=watermarked`
і `data=lfi_challenge`; сам прапор не зберігається. Під час сабміту CTFd
питає watermark-сервіс, чи збігається прапор із профілем поточної команди
(CTFd `user.name`).

## Адміністрування

### Команди та паролі VPN

```bash
cd CTFd

# Створити команду і отримати згенерований пароль
sudo python3 vpn-portal/admin_teams.py add team-alpha

# Створити багато команд і зберегти паролі для роздачі капітанам
sudo python3 vpn-portal/admin_teams.py bulk team-alpha team-beta team-gamma \
  --output data/team_passwords.csv

# Створити паролі для команд, які вже є в user_registry.csv (міграція)
sudo python3 vpn-portal/admin_teams.py import-registry \
  --output data/team_passwords.csv

# Скинути пароль / показати список / видалити пароль
sudo python3 vpn-portal/admin_teams.py set team-alpha
sudo python3 vpn-portal/admin_teams.py list
sudo python3 vpn-portal/admin_teams.py remove team-alpha
```

`data/team_credentials.json` містить лише PBKDF2-хеші (режим `0600`).
Портал також приймає HTTP Basic для API:

```bash
curl -u 'team-alpha:ПАРОЛЬ' http://10.10.15.124:5050/api/vpn/info
curl -u 'team-alpha:ПАРОЛЬ' -o team-alpha.ovpn \
  http://10.10.15.124:5050/api/vpn/download
```

Видаліть `data/team_passwords.csv` після роздачі паролів.

### Watermark та логи

```bash
# Хто яку VPN-адресу отримав
python3 logger/logger.py registry

# Перевірити прапор для команди
python3 logger/logger.py verify shadow_hunter42 'CTF{...}'

# Знайти, кому належить злитий прапор
python3 logger/logger.py trace 'CTF{...}'

# Останні події
python3 logger/logger.py tail 50

# Логи контейнерів
docker compose logs -f ctfd_setup
docker compose logs -f watermark
docker compose logs -f openvpn
```

Для `logger.py` потрібен доступ до `data/watermark.key`; запускайте його на
сервері з папки `CTFd` або через `logger/dockerfile`.

## Скидання

```bash
# Повне очищення платформи: CTFd DB, PKI, реєстр, логи (завдання теж зупиняються)
cd ../ctf-operation-titan-v2
./setup.sh --reset
```

`--reset` видаляє `openvpn-data`, `data`, `logs` і Docker-томи БД. Це знищує
акаунти CTFd, розв'язки, VPN-сертифікати та watermark-секрет. Використовуйте
лише для чистого перезапуску.

## Діагностика

| Симптом | Що перевірити |
|---|---|
| CTFd не стартує | `docker compose logs ctfd db`; healthcheck БД |
| Завдання не з'явилися | `docker compose logs ctfd_setup`; плагін `watermarked` змонтований |
| `watermarked` не завантажився | шлях `./plugins/watermarked` і `docker compose restart ctfd` |
| VPN підключається, сайти не відкриваються | `ip_forward`, `rp_filter`, правила `tun0 ↔ br-+`, `ufw` |
| LFI каже «немає VPN-профілю» | профіль отримано для тієї самої назви команди? IP у `data/user_registry.csv`? |
| Прапор не приймається | назва команди в CTFd і на порталі збігається? профіль отримано до сабміту? |
| `easyrsa failed` | контейнер `openvpn` запущений? `docker compose logs openvpn` |
| OpenVPN: `Compression ... not allowed` | `grep -nE 'comp-lzo\|compress' openvpn-data/conf/openvpn.conf` має бути порожнім; перезапустіть `openvpn` |
| Портал: «Невірна назва команди або пароль» | `sudo python3 vpn-portal/admin_teams.py list`; скиньте пароль через `set` |

## Вимоги

- Linux-сервер із Docker і Compose v2.
- `/dev/net/tun` і можливість `NET_ADMIN` (для OpenVPN).
- Вільні порти: `1194/udp`, `8000/tcp`, `5050/tcp`, `8001–8012/tcp`.
- Стабільна `PUBLIC_IP` у `.env` (краще зарезервувати на DHCP).
- Для маршрутизації без NAT — `iptables`/`ufw` і root-доступ під час `setup.sh`.

## Безпека

- Не публікуйте `data/watermark.key`, `data/team_credentials.json`,
  `data/team_passwords.csv` і `logs/flag_issuance.log`.
- `titan_internal` навмисно `internal: true`; не підключайте до неї VPN.
- `docker.sock` змонтований у VPN-портал: портал має доступ до Docker. Це
  потрібно для `easyrsa`/`ovpn_getclient`; не виставляйте портал у публічний
  інтернет без додаткового захисту.
- Для продакшену змініть `SECRET_KEY`, пароль CTFd, пароль БД і
  `ADMIN_PASSWORD`.
