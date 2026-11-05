#!/bin/bash
echo "========================================="
echo "   LNTU Local CTF + OpenVPN Deployment   "
echo "========================================="

# 1. Перевірка та встановлення Docker та Python3, якщо їх немає
if ! command -v docker &> /dev/null; then
    echo "[*] Docker не знайдено. Встановлюю Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v python3 &> /dev/null; then
    echo "[*] Python3 не знайдено. Встановлюю Python3..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-requests
fi

# 2. Отримання публічного IP (або використання localhost для тесту)
PUBLIC_IP=$(curl -s ifconfig.me)
if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP="127.0.0.1"
fi
echo "[+] Буде використано IP для VPN: $PUBLIC_IP"

# 3. Ініціалізація OpenVPN конфігів (тільки якщо ще не створено)
if [ ! -f "./openvpn-data/conf/openvpn.conf" ]; then
    echo "[*] Ініціалізація бази OpenVPN (PKI)..."
    mkdir -p ./openvpn-data/conf
    docker run -v $(pwd)/openvpn-data/conf:/etc/openvpn --rm kylemanna/openvpn ovpn_genconfig -u udp://$PUBLIC_IP:1194 -n 10.8.0.0/24 -N
    
    # Автоматичне створення сертифікатів без пароля (EASYRSA_BATCH=1)
    echo "[*] Генерація сертифікатів CA (Це може зайняти хвилину)..."
    docker run -v $(pwd)/openvpn-data/conf:/etc/openvpn -e EASYRSA_BATCH=1 --rm kylemanna/openvpn ovpn_initpki nopass
fi

# 4. Збірка та запуск усіх контейнерів
echo "[*] Збірка та запуск інфраструктури..."
docker compose up -d --build

# 5. Очікування підняття CTFd
echo "[*] Очікуємо 10 секунд для запуску бази CTFd..."
sleep 10

echo "========================================="
echo "[+] Успішно запущено!"
echo "[+] CTFd доступний: http://localhost:8000"
echo "[+] VPN API Портал: http://localhost:5050"
echo "[!] Не забудьте створити сторінку завантаження VPN у CTFd (код у README.md)"
echo "========================================="
