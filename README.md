# 🛡️ CTF Cyber Range & Challenge Collection

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![CTFd](https://img.shields.io/badge/CTFd-Platform-ff4d00?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

Готовий до автоматичного розгортання комплекс кіберзмагань (Cyber Range) та інфраструктура CTF. Набір містить розгорнуту платформу **CTFd** та серію повністю ізольованих у **Docker-контейнерах** завдань із різним рівнем складності (від Web Recon до Kernel UAF та PWN).

Проєкт адаптований як для проведення локальних університетських заходів (LNTU CTF), так і для проведення масштабних змагань із розгортанням у VPN (WireGuard / OpenVPN / Tailscale).

## Operation Titan v2

Активна інфраструктура розділена на два стеки:

| Папка | Що всередині |
|---|---|
| [`CTFd/`](CTFd/README.md) | CTFd 3.8.9, MariaDB, Redis, OpenVPN, VPN-портал із постійними IP, внутрішній watermark-сервіс, CTFd-плагін `watermarked`, logger, writeups |
| [`ctf-operation-titan-v2/`](ctf-operation-titan-v2/README.md) | 12 контейнерів завдань, спільний дизайн Titan, обгортка розгортання |

Швидкий старт:

```bash
cd ctf-operation-titan-v2
chmod +x setup.sh
./setup.sh --reset
```

Після старту: CTFd — `http://<PUBLIC_IP>:8000`, VPN-портал — `:5050`,
завдання — `:8001`…`:8012` напряму або `172.28.0.11`…`172.28.0.22` через VPN.

Ключові особливості:

- один нік у CTFd → один сертифікат → одна постійна VPN-адреса `10.8.0.x`;
- прапор завдання **10. LFI to RCE** генерується окремо для кожної VPN-адреси;
- HMAC-секрет і журнал видачі живуть у внутрішньому `watermark`-сервісі й не
  потрапляють у вразливий LFI-контейнер;
- нове завдання **12. Token Forge** — реєстрація, тестовий логін, підміна ролі
  в підписаному токені та AES-зашифрований журнал аудиту з прапором.

Деталі: [`CTFd/README.md`](CTFd/README.md), [`ctf-operation-titan-v2/README.md`](ctf-operation-titan-v2/README.md).
