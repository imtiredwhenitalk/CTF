# Інструкція з розгортання та керування CTF

## 1. Системні вимоги
- ОС: Ubuntu 22.04 LTS / Debian 12 / Kali Linux / WSL2
- Пакети: `docker`, `docker-compose-v2`, `python3`

## 2. Команди керування
- **Запуск усіх сервісів:** `./setup.sh`
- **Зупинка:** `docker compose down`
- **Перезапуск конкретного завдання:** `docker compose restart volyngas_ctf`
- **Перегляд логів:** `docker compose logs -f`
