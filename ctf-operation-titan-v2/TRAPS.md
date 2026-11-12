# Operation Titan — пастки та фальшиві прапори (для організаторів)

Цей файл **не** віддається жодним контейнером. Усі `CTF{...}` нижче — декої,
їх **не можна** додавати в CTFd. Реальні прапори залишилися без змін і лежать
у `ctfd-setup/setup_ctfd.py` та відповідних Dockerfile.

## 01 · SSTI Comms Console
- `/backup` і `/app/backup/legacy.conf` → `CTF{sst1_l3g4cy_c0ns0l3_fl4g}`.
- `/app/flag.txt` → `CTF{sst1_0ld_c0py_fl4g}`.
- Додано WAF: блокує `flag`, `os`, `popen`, `system`, `subprocess`, `lipsum`,
  `cycler`. Робочий обхід — у `writeups/01_ssti.md`.
- Реальний прапор: `/flag.txt` (без змін).

## 02 · JWT Alg Confusion
- `/old_pub` — інший публічний ключ, підпис ним не проходить.
- `/dev/token` — готовий admin-токен на staging-секреті, не проходить; у JSON є
  фальшивий `legacy_flag` → `CTF{jwt_hs256_st4g1ng_byp4ss}`.
- `/robots.txt` показує обидві пастки.
- Реальний прапор: `CTF{jwt_4lg_c0nfus10n_byp4ss}`.

## 03 · LFSR Reversing
- `flag_backup.enc` → `CTF{lfsr_b4ckup_k3y_r0t4t3d}` (інший seed).
- Підказка про seed `4660` — фальшива.
- Реальний прапор: `flag.enc`, seed 47011.

## 04 · Pickle & HMAC
- `LEGACY_SECRET = b"titan_legacy_key_2021"` — підпис із ним не проходить.
- `/app/flag.txt` → `CTF{p1ckl3_l3g4cy_m1rr0r_fl4g}`.
- Реальний прапор: `/flag.txt`.

## 05 · JWT & RSA
- Поле `legacy` у `/admin` → `CTF{rs4_l3g4cy_k3y_r0t4t3d}`.
- Реальні поля: `n`, `e`, `enc` верхнього рівня.

## 06 · AES ECB Oracle
- `/legacy` + `/unlock_legacy` з публічним токеном →
  `CTF{3cb_l3g4cy_v4ult_r0t4t3d}`.
- Реальний токен генерується при старті й відкривається лише через `/unlock`.

## 07 · Blind SQLi WAF
- `users.id=2` (`admin_legacy`) → `CTF{bl1nd_sqli_l3g4cy_us3r}`.
- `legacy_users` → `CTF{bl1nd_sqli_l3g4cy_t4bl3}`.
- `audit_notes` → `CTF{bl1nd_sqli_aud1t_n0t3}`.
- Реальний прапор: пароль `admin` у `users.id=1`.

## 08 · RSA Wiener
- `intercept_backup.txt` → `CTF{w13n3r_b4ckup_p4ck3t_r0t4t3d}`.
- У `intercept.txt` підказано фальшивий `d = 123496108`.
- Реальні значення: `N`, `e`, `C` з `intercept.txt`.

## 09 · Hidden Archive
- `image_old.png` + `notes.txt` → `CTF{st3g0_l3g4cy_4rch1v3_fl4g}`.
- Реальний ZIP дописаний до `image.png`, пароль `titan`.

## 10 · LFI
- `/etc/secret_flag_1337.txt` → `CTF{lf1_l3g4cy_p4th_r0t4t3d}`.
- `/app/files/flag.txt` → `CTF{lf1_b4ckup_m1rr0r_fl4g}`.
- `/app/files/backup/flag.bak` → `CTF{lf1_b4ckup_d1r3ct0ry_fl4g}`.
- Реальний прапор: `/var/lib/titan/secure/.flag`, шлях є в `ops_note.txt`.

## 11 · Binance API Heist
- `BACKUP_KEY` у HTML + `/api/v3/internal/legacy` +
  `/api/v3/wallet/withdraw_legacy` →
  `CTF{b1n4nc3_l3g4cy_d3bug_fl4g}`.
- Реальний ланцюжок: `DEBUG_KEY` → `BNC-ADM-88912-SECRET` →
  `/api/v3/wallet/withdraw`.

## Швидка перевірка

```bash
# усі реальні прапори (не змінювалися)
grep -o 'CTF{[^}]*}' ctfd-setup/setup_ctfd.py

# усі декої, які не повинні потрапити в CTFd
grep -rho 'CTF{[^}]*}' flag*/ | sort -u
```
