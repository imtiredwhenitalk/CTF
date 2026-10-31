# Operation Titan CTF

Повний набір для проведення змагання: портал (реєстрація, завдання, прапори, скорборд) + 7 завдань у Docker.

## Структура

```
titan_ctf/
├── docker-compose.yml     # портал + сервіси завдань
├── setup.sh               # готує артефакти (git-репо, .enc-файл, завантаження, .env)
├── portal/                # Flask-портал (app.py, challenges.py з прапорами, templates, static)
├── flag1_git_leak/        # Web: витік .git
├── flag2_jwt_api/         # Web/Crypto: слабкий секрет JWT
├── flag3_crypto_rev/      # Reverse: reverse + XOR (файли видаються учасникам)
├── flag4_pwn/             # Pwn: переповнення буфера (gets)
├── flag5_ad_sim/          # AD: Kerberoast-симулятор
├── flag6_kernel_scada/    # Kernel: аналіз коду драйвера (файл видається)
├── flag7_sqli_web/        # Web: UNION SQL-ін'єкція
├── flag8_crypto_rsa/      # Crypto: RSA з e=3 без паддингу (файли видаються)
└── writeups/              # рішення (ТІЛЬКИ для організаторів)
```

## Запуск

```bash
./setup.sh                      # потрібні python3 і git
# за потреби відредагуйте .env: PUBLIC_HOST=<ваш IP/домен>
docker compose up --build -d
```

Портал: http://localhost:8080

| Завдання | Сервіс | Бали |
|---|---|---|
| 1 Initial Footprint | http://HOST:8081 | 100 |
| 2 Broken Session | http://HOST:8082 | 200 |
| 3 Dark Config | файли на порталі | 200 |
| 4 System Override | `nc HOST 1337` | 300 |
| 5 Domain Takeover | http://HOST:8085 | 300 |
| 6 Zero-Day Core | файл на порталі | 500 |
| 7 Leaked Directory | http://HOST:8087 | 150 |
| 8 Cube Courier | файли на порталі | 250 |

## Важливо

- Усі прапори лежать у `portal/challenges.py` і ніколи не віддаються клієнту. Для власного змагання змініть їх (а також у вихідниках завдань і writeups).
- Завдання 4 навмисно зібране без захисту стека (`-fno-stack-protector -z execstack`): запускайте лише в ізольованому середовищі, не відкривайте порти 1337/8081-8087 у публічний інтернет без потреби.
- Завдання 6 віддається як вихідний код: прапор лежить у коментарі, як і задумано в оригінальному writeup.
- Для змагання на кілька десятків людей достатньо одного хоста; БД порталу - SQLite у томі `portal_data`.
- Скинути результати: `docker compose down -v` (видалить том).
