# Operation Titan: Ultimate Edition 🛡️

Повна інфраструктура з 10 ускладненими завданнями, вбудованим OpenVPN та **автоматично налаштованим CTFd**.

## 🚀 Що всередині:
- **10 Хардкорних завдань:** Усі переведені на Python/Web/Crypto, жодного C-коду. Додано LFI, WAF SQLi, RSA Wiener's Attack, LFSR, Stego, JWT Alg Confusion.
- **CTFd Auto-Setup:** Платформа сама ініціалізується, створює адміна (`admin:admin`) і автоматично завантажує всі 10 тасків із їхніми прапорами та описами!
- **VPN з коробки:** OpenVPN генерує сертифікати і підіймається автоматично.

## 🛠 Запуск
```bash
chmod +x setup.sh
./setup.sh
```
Після старту:
- **CTFd:** `http://localhost:8000` (Вже налаштовано! Логін `admin`, пароль `admin`)
- **VPN Портал:** `http://localhost:5050`
