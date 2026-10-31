#!/bin/bash
echo "========================================="
echo "   LNTU Local CTF Deployment Script      "
echo "========================================="

if ! command -v docker &> /dev/null; then
    echo "[!] Docker не знайдено! Встановіть Docker та спробуйте знову."
    exit 1
fi

echo "[*] Збірка та запуск Docker контейнерів..."
docker compose up -d --build

echo ""
echo "[+] Успішно запущено!"
echo "[+] CTFd доступний за адресою: http://localhost:8000"
echo "[+] Деталі запуску та порти дивіться у README.md"
