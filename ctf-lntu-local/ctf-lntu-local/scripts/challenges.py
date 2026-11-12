"""Єдине джерело правди: опис 15 тасків, прапори, порти, підказки, бали й порядок.
Використовується populate_ctfd.py (наповнення CTFd) та check_challenges.py (самоперевірка).

Порядок у списку = порядок показу в CTFd (position 01…15): спочатку найлегші.
Три рівні складності по 5 тасків: 15 / 20 / 25 балів (разом 300).
`n` — це номер сервісу flagN_ctf і порт BASE_PORT + n; він НЕ змінюється.
"""

BASE_PORT = 8080  # сервіс таска n слухає на BASE_PORT + n

DIFFICULTY_VALUES = {"easy": 15, "medium": 20, "hard": 25}
DIFFICULTY_LABELS = {"easy": "Легкий", "medium": "Середній", "hard": "Складний"}

# Список складено від найлегшого до найскладнішого.
CHALLENGES = [
    # ───────────────────────────── 15 балів ─────────────────────────────
    dict(n=11, difficulty="easy",
         title="ВолиньОбленерго — Забута резервна копія", category="Web / Recon",
         flag="CTF{r0b0ts_txt_l34ks_b4ckups}",
         description="Розробники залишили щось зайве на сайті. Знайдіть це та увійдіть у панель персоналу.\n\nhttp://{host}:{port}",
         hint="Із чого починається розвідка будь-якого сайту? /robots.txt."),
    dict(n=2, difficulty="easy",
         title="ВолиньВода — Чужий рахунок", category="Web / IDOR",
         flag="CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}",
         description="Система обліку ВолиньВода показує дані за номером рахунку. У системи є службовий акаунт — знайдіть його.\n\nhttp://{host}:{port}",
         hint="Тестовий рахунок має номер 1001. Службові номери часто «круглі» або «красиві»."),
    dict(n=5, difficulty="easy",
         title="LNTU Accounts — Витік токена", category="Web / Authentication",
         flag="CTF{r3s3t_t0k3n_1s_n0t_s3cr3t}",
         description="Сервіс відновлення доступу занадто багато розповідає. Скиньте пароль адміністратора.\n\nhttp://{host}:{port}",
         hint="Який користувач точно існує в будь-якій системі?"),
    dict(n=7, difficulty="easy",
         title="Деканат — Підміна ролі", category="Web / Cookies",
         flag="CTF{c00k13_r0l3_t4mp3r1ng_l4nds_4dm1n}",
         description="Кабінет студента довіряє даним, які зберігає у вашому браузері. Потрапте в адмін-панель деканату.\n\nhttp://{host}:{port}",
         hint="Увійдіть демо-акаунтом і уважно подивіться на значення куки. Це Base64?"),
    dict(n=12, difficulty="easy",
         title="SIGINT — Шари кодування", category="Crypto / Encoding",
         flag="CTF{l4y3r3d_3nc0d1ng_1s_n0t_3ncrypt10n}",
         description="Радіоклуб перехопив повідомлення. Воно закодоване кількома шарами. Розкодуйте.\n\nhttp://{host}:{port}",
         hint="CyberChef: From Hex → From Base64 → ROT13."),

    # ───────────────────────────── 20 балів ─────────────────────────────
    dict(n=13, difficulty="medium",
         title="Intranet — Свій серед своїх", category="Web / HTTP Headers",
         flag="CTF{h34d3rs_4r3_us3r_c0ntr0ll3d}",
         description="Службовий портал пускає лише «своїх». Зробіть так, щоб сервер повірив, що ви — співробітник у внутрішній мережі.\n\nhttp://{host}:{port}",
         hint="Читайте повідомлення про помилку 403 — кожне вказує на наступний заголовок (X-Forwarded-For, User-Agent, Referer)."),
    dict(n=9, difficulty="medium",
         title="Е-Архів — Вихід за межі каталогу", category="Web / LFI",
         flag="CTF{p4th_tr4v3rs4l_n0t_s0_s4f3}",
         description="Електронний архів відкриває документи за назвою файлу. Прапор лежить поза каталогом документів, у файлі /etc/lntu/flag.txt.\n\nhttp://{host}:{port}",
         hint="Фільтр видаляє `../` лише один раз. Що буде з `....//`?"),
    dict(n=6, difficulty="medium",
         title="Autumn Archive — Хвіст файлу", category="OSINT / Forensics",
         flag="CTF{autumn_fox_metadata_tells_the_story}",
         description="Допис волонтера autumn_fox видалили, але відновлений артефакт камери ще лежить в архіві. Дослідіть його повністю.\n\nhttp://{host}:{port}",
         hint="strings, exiftool та hex-редактор. Дані можуть бути після маркера IEND."),
    dict(n=4, difficulty="medium",
         title="Затвор — Пошук без меж", category="Web / SQLi",
         flag="CTF{z4tv0r_sqli_byp4ss_m4st3r}",
         description="У каталозі магазину «Затвор» пошук будує SQL-запит із вашого тексту. База містить таблицю, якої не видно в каталозі.\n\nhttp://{host}:{port}",
         hint="Запит повертає 3 колонки. `UNION SELECT` та `sqlite_master` допоможуть знайти таблицю."),
    dict(n=1, difficulty="medium",
         title="ВолиньГаз — Шаблони заяв", category="Web / SSTI",
         flag="CTF{v0lyn_g4s_sst1_3xpl01t_2026}",
         description="Портал ВолиньГаз приймає заяви від абонентів і показує підтвердження. Оператору довірили надто багато — "
                     "знайдіть спосіб прочитати секрет зі змінної конфігурації застосунку.\n\nhttp://{host}:{port}",
         hint="Що станеться, якщо в полі «Примітка» написати `{{7*7}}`?"),

    # ───────────────────────────── 25 балів ─────────────────────────────
    dict(n=10, difficulty="hard",
         title="LNTU NOC — Ping із сюрпризом", category="Web / Command Injection",
         flag="CTF{c0mm4nd_1nj3ct10n_p1p3_th3_fl4g}",
         description="Інструмент діагностики запускає ping у командному рядку. Прапор лежить у /flag.txt.\n\nhttp://{host}:{port}",
         hint="Крапку з комою та & заборонено. А що з `|` та `$( )`?"),
    dict(n=8, difficulty="hard",
         title="Бібліотека API — Слабкий секрет", category="Web / JWT",
         flag="CTF{jwt_w34k_s3cr3t_cr4ck3d}",
         description="REST API бібліотеки видає JWT-токени. Роль «reader» — не те, що вам потрібно. Підробіть токен адміністратора.\n\nhttp://{host}:{port}",
         hint="HS256 підписується секретом. hashcat -m 16500 або jwt_tool. Підказка про політику секрету — на головній сторінці."),
    dict(n=14, difficulty="hard",
         title="Фотоархів — Приховане в пікселях", category="Forensics / Stego",
         flag="CTF{lsb_st3g0_h1d1ng_1n_pl41n_s1ght}",
         description="На фото осені ховається повідомлення. Завантажте оригінал та витягніть його.\n\nhttp://{host}:{port}",
         hint="zsteg -a photo.png або Python + Pillow: LSB червоного каналу."),
    dict(n=3, difficulty="hard",
         title="LNTU Cyber Blog — Куки модератора", category="Web / XSS",
         flag="CTF{xss_st0r3d_4dm1n_c00k13_st34l}",
         description="Модератор блогу переглядає кожну нову статтю у своєму браузері з кукою <code>admin_session</code>. "
                     "Викрадіть її. Вбудований приймач: <code>/collect?d=…</code>, результат — на <code>/inbox</code>.\n\nhttp://{host}:{port}",
         hint="Тег `<script>` відфільтровано, але це не єдиний спосіб виконати JS. Подумайте про обробники подій (onerror, onload)."),
    dict(n=15, difficulty="hard",
         title="LinkPreview — Звернення всередину", category="Web / SSRF",
         flag="CTF{ssrf_1nt3rn4l_s3rv1c3_r34ch3d}",
         description="Сервіс прев'ю посилань завантажує будь-який URL. У внутрішній мережі живе служба метаданих, до якої ззовні не достукатися… напряму.\n\nhttp://{host}:{port}",
         hint="Фільтр блокує лише рядки localhost та 127.0.0.1. Є й інші способи записати loopback-адресу."),
]

# Похідні поля: порядок у CTFd, бали за рівнем, назва з номером, порт сервісу.
for _position, _c in enumerate(CHALLENGES, start=1):
    _c["position"] = _position
    _c["value"] = DIFFICULTY_VALUES[_c["difficulty"]]
    _c["difficulty_label"] = DIFFICULTY_LABELS[_c["difficulty"]]
    _c["name"] = f"{_position:02d}. {_c['title']}"
    _c["port"] = BASE_PORT + _c["n"]

# Захист від випадкового порушення структури «5 + 5 + 5».
_counts = {level: sum(c["difficulty"] == level for c in CHALLENGES) for level in DIFFICULTY_VALUES}
assert _counts == {"easy": 5, "medium": 5, "hard": 5}, _counts
assert len({c["n"] for c in CHALLENGES}) == len(CHALLENGES) == 15
