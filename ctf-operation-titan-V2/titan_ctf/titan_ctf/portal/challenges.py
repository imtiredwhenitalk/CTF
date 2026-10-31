"""Каталог завдань Operation Titan.

ВАЖЛИВО: цей файл містить прапори, тому він живе лише на сервері порталу
і ніколи не віддається користувачам.
`service`: {"kind": "http"|"nc", "port": N} - сервіс у docker-compose.
`files`: файли для скачування з папки portal/downloads (після ./setup.sh).
"""

CHALLENGES = [
    {
        "id": 1,
        "title": "Initial Footprint",
        "category": "Web",
        "points": 100,
        "description": "Державна система моніторингу «Титан» має публічну сторінку. "
                       "Розробники поспішали з релізом і могли залишити після себе зайве. "
                       "Знайдіть слід у кореневій директорії.",
        "hint": "Подивіться на вихідний код сторінки уважніше. Не все, що лишив розробник, видно у браузері.",
        "service": {"kind": "http", "port": 8081},
        "files": [],
        "flag": "CTF{w3lc0m3_t0_th3_tr1d3nt_n3tw0rk_2026}",
    },
    {
        "id": 2,
        "title": "Broken Session",
        "category": "Web / Crypto",
        "points": 200,
        "description": "Адмін-API «Титана» видає токени гостям. Прапор доступний лише ролі "
                       "internal_admin. Чи так надійно захищений підпис токена?",
        "hint": "Ключ підпису JWT - слабкий. Словник вам у допомогу.",
        "service": {"kind": "http", "port": 8082},
        "files": [],
        "flag": "CTF{jwt_s3cr3ts_sh0uld_n3v3r_b3_w34k}",
    },
    {
        "id": 3,
        "title": "Dark Config",
        "category": "Reverse",
        "points": 200,
        "description": "Перехоплено зашифрований конфіг продакшн-сервера та утиліту, якою його "
                       "завантажують. Розберіться з алгоритмом і дістаньте пароль.",
        "hint": "Два прості кроки, які виконуються у зворотному порядку.",
        "service": None,
        "files": ["config_loader.py", "production.conf.enc"],
        "flag": "CTF{gh1dr4_r3v3rs1ng_m4st3r_9921}",
    },
    {
        "id": 4,
        "title": "System Override",
        "category": "Pwn",
        "points": 300,
        "description": "Діагностичний сервіс приймає ваш «payload». Усередині є функція, "
                       "яка ніколи не викликається штатно. Змусьте її спрацювати.",
        "hint": "Класичне переповнення буфера на стеку. Знайдіть зміщення та адресу цільової функції.",
        "service": {"kind": "nc", "port": 1337},
        "files": [],
        "flag": "CTF{pwn_th3_s3rv3r_g3t_th3_r00t}",
    },
    {
        "id": 5,
        "title": "Domain Takeover",
        "category": "Active Directory",
        "points": 300,
        "description": "У консолі сервісу Kerberos можна запитати квиток для службового акаунта "
                       "svc_backup. Що ховається у відповіді?",
        "hint": "Формат хешу: krb5tgs, hashcat mode 13100. Придивіться до його структури.",
        "service": {"kind": "http", "port": 8085},
        "files": [],
        "flag": "CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}",
    },
    {
        "id": 6,
        "title": "Zero-Day Core",
        "category": "Kernel",
        "points": 500,
        "description": "Виявлено вразливий драйвер ядра SCADA-системи. Проаналізуйте його код "
                       "та дістаньте секрет, що зберігається в пам'яті ядра.",
        "hint": "Прочитайте вихідний код драйвера від початку до кінця, включно з коментарями.",
        "service": None,
        "files": ["scada_driver.c"],
        "flag": "CTF{0d4y_k3rn3l_m4st3r_ukr41n14n_cyb3r_f0rc3}",
    },
    {
        "id": 7,
        "title": "Leaked Directory",
        "category": "Web",
        "points": 150,
        "description": "Внутрішній довідник співробітників «Титан» має пошук за прізвищем. "
                       "Схоже, база даних відповідає більше, ніж слід.",
        "hint": "Спробуйте вставити в поле пошуку одинарну лапку і подивіться, що скаже БД.",
        "service": {"kind": "http", "port": 8087},
        "files": [],
        "flag": "CTF{un10n_s3l3ct_dr41ns_th3_v4ult_7731}",
    },
]

BY_ID = {c["id"]: c for c in CHALLENGES}
ALLOWED_FILES = {f for c in CHALLENGES for f in c["files"]}
