# Інструкція з розгортання та керування CTF

## 1. Вимоги
Ubuntu 22.04+ / Debian 12 / Kali / WSL2, `docker` + `docker compose` (встановлюються через `./ctf.sh setup`), `python3`.
Для таску 3 образ збирається на базі Playwright (~1.5 ГБ) — перша збірка триває кілька хвилин.

## 2. Команди
| Дія | Команда |
|-----|---------|
| Перший запуск | `./ctf.sh setup` |
| Додати таски в CTFd | `./ctf.sh populate <TOKEN>` |
| Перевірка всіх тасків | `./ctf.sh check` |
| Стан / логи | `./ctf.sh status` · `./ctf.sh logs flag3_ctf` |
| Перезапуск одного таска | `./ctf.sh restart flag3_ctf` |
| Після правок коду таска | `./ctf.sh rebuild flag3_ctf` |
| Зупинка | `./ctf.sh down` |
| Повне видалення з даними | `./ctf.sh clean` |

Порти: CTFd `8000`, таски `8081–8095` (таск N → `8080+N`), OpenVPN `1194/udp`.
Якщо сервер за файрволом — відкрийте ці порти.

## 3. Токен для populate
CTFd → Admin Panel → Settings → Access Tokens → Generate → скопіюйте токен.

## 4. VPN для гравців
```bash
./ctf.sh vpn-init   # один раз: генерація PKI
./ctf.sh vpn-up     # старт контейнера openvpn
```
Сторінку з кнопкою завантаження .ovpn створюйте як раніше: Admin Panel → Pages → New Page (Route: `vpn`, редактор у режимі HTML).
У коді сторінки замініть `localhost` в `downloadUrl` на IP сервера, де працює ваш VPN-API (порт 5050).
Контейнер у compose називається `openvpn` (як очікує VPN-API при `docker exec`). Якщо OpenVPN у вас вже працює окремо — `vpn-up` не запускайте.
