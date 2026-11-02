#!/bin/bash
echo "========================================="
echo "   Operation Titan CTF Deployment        "
echo "========================================="

if ! command -v docker &> /dev/null
then
    echo "[!] Docker не знайдено. Встановіть docker та docker-compose."
    exit 1
fi

echo "[*] Збірка та запуск Docker-контейнерів..."
docker compose up -d --build

echo ""
echo "[+] Успішно запущено!"
echo "[+] Платформа CTFd доступна за адресою: http://localhost:8000"
echo "[+] Ознайомтеся з README.md для налаштування завдань."
