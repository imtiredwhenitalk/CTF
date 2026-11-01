#!/bin/bash
echo "========================================="
echo "   Initiating Operation: Binance Heist   "
echo "========================================="

if ! command -v docker &> /dev/null; then
    echo "[!] Docker не знайдено. Встановіть docker."
    exit 1
fi

echo "[*] Підняття серверів..."
docker compose up -d --build

echo "========================================="
echo "[+] Сюжетний інтерфейс (Початок гри): http://localhost:8080"
echo "[+] API Криптобіржі (Таргет): http://localhost:5000"
echo "========================================="
