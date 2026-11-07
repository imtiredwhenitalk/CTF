# Operation Titan — challenge stack

Тут живуть **лише контейнери завдань**. Платформа (CTFd, OpenVPN, VPN-портал,
watermark-сервіс, БД) — у [`../CTFd`](../CTFd).

Стек підключається до зовнішніх мереж `titan_net` і `titan_internal`, які
створює платформа. Тому спочатку запускається `../CTFd/setup.sh`, а потім цей
compose. Обгортка `./setup.sh` робить обидва кроки.

## Запуск

```bash
chmod +x setup.sh
./setup.sh --reset      # перший запуск / повне очищення
./setup.sh              # звичайний запуск
```

Скрипт:

1. запускає платформу з `../CTFd` (створює `titan_net`, `titan_internal`, PKI,
   БД, CTFd, VPN-портал, watermark);
2. синхронізує спільний дизайн у папки завдань (`tools/sync_ui.sh`);
3. збирає та запускає 12 контейнерів завдань.

Якщо платформа вже працює, а треба лише оновити завдання:

```bash
docker compose up -d --build --remove-orphans
```

## Адреси

| # | Завдання | Напряму | Через VPN |
|---|---|---|---|
| 01 | SSTI Comms Console | `:8001` | `172.28.0.11:5000` |
| 02 | JWT Alg Confusion | `:8002` | `172.28.0.12:5000` |
| 03 | LFSR Reversing | `:8003` | `172.28.0.13:80` |
| 04 | Pickle & HMAC | `:8004` | `172.28.0.14:5000` |
| 05 | JWT & RSA | `:8005` | `172.28.0.15:5000` |
| 06 | AES ECB Oracle | `:8006` | `172.28.0.16:5000` |
| 07 | Blind SQLi WAF | `:8007` | `172.28.0.17:5000` |
| 08 | RSA Wiener's Attack | `:8008` | `172.28.0.18:80` |
| 09 | Hidden Archive | `:8009` | `172.28.0.19:80` |
| 10 | LFI to RCE | `:8010` | `172.28.0.20:5000` |
| 11 | Binance API Heist | `:8011` | `172.28.0.21:80` |
| 12 | Token Forge | `:8012` | `172.28.0.22:5000` |

`PUBLIC_IP` береться з `../CTFd/.env` (за замовчуванням `10.10.15.124`) і
використовується в описах завдань CTFd.

## Завдання 10 і VPN

Прапор **10. LFI to RCE** динамічний і прив'язаний до VPN-адреси. Щоб отримати
прапор, який зарахує CTFd:

1. Зареєструйтеся в CTFd під ніком `nickname`.
2. Відкрийте VPN-портал `http://<PUBLIC_IP>:5050`.
3. Введіть **той самий** нік і завантажте `.ovpn`.
4. Підключіться до VPN і відкривайте завдання за адресою `172.28.0.20:5000`.

Прямий доступ через `:8010` покаже повідомлення, що для адреси немає
VPN-профілю. Це очікувано: watermark-сервіс видає прапор лише для
зареєстрованих VPN-адрес.

## Завдання 12

`flag12_tokengate` — Flask-сайт із реєстрацією, тестовим логіном
`test` / `test123`, підміною ролі в токені та зашифрованим журналом аудиту.
Стан користувачів зберігається в Docker-томі `tokengate_data`. Повне очищення
тому: `docker compose down -v`.

Розв'язок: [`../CTFd/writeups/12_token_forge.md`](../CTFd/writeups/12_token_forge.md).

## Дизайн

Усі сайти використовують офлайн-дизайн Titan:

- джерело: `shared/titan_ui.py`, `shared/titan.css`;
- копіювання: `tools/sync_ui.sh` (запускається з `./setup.sh`);
- після зміни дизайну: `bash tools/sync_ui.sh`, потім перезберіть завдання.

`sync_ui.sh` також оновлює копію дизайну для VPN-порталу в `../CTFd/vpn-portal`.

## Writeups

- 01–10 і 12: [`../CTFd/writeups`](../CTFd/writeups);
- 11: [`flag11_binance/writeup.md`](flag11_binance/writeup.md).

## Діагностика

| Симптом | Що перевірити |
|---|---|
| `external network titan_net not found` | спочатку запустіть `../CTFd/setup.sh` |
| Завдання не стартує | `docker compose logs <service>` |
| Порт зайнятий | `docker compose down --remove-orphans`, перевірте `:8001–:8012` |
| Сайт без стилів | `bash tools/sync_ui.sh`, перезберіть контейнер |
| 10 не дає прапор | VPN-профіль під тим самим ніком; `ip a` показує `10.8.0.x` |
| 12 не зберігає реєстрацію | том `tokengate_data`; `docker compose logs flag12_tokengate` |

## Склад

```
ctf-operation-titan-v2/
├── docker-compose.yml      # 12 завдань + зовнішні мережі
├── setup.sh                # платформа + завдання
├── tools/sync_ui.sh
├── shared/                 # єдиний дизайн
├── flag1_ssti/ ... flag11_binance/
└── flag12_tokengate/       # нове завдання
```

Платформа: [`../CTFd/README.md`](../CTFd/README.md).
