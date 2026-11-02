#!/bin/bash
echo "========================================="
echo "   Operation Titan: Final Deployment     "
echo "========================================="
if ! command -v docker &> /dev/null; then
    echo "[!] Docker не знайдено. Встановлюю..."
    curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && rm get-docker.sh
fi

PUBLIC_IP=$(curl -s ifconfig.me || echo "127.0.0.1")
echo "[+] IP для VPN: $PUBLIC_IP"

if [ ! -f "./openvpn-data/conf/openvpn.conf" ]; then
    echo "[*] Ініціалізація OpenVPN..."
    mkdir -p ./openvpn-data/conf
    docker run -v $(pwd)/openvpn-data/conf:/etc/openvpn --rm kylemanna/openvpn ovpn_genconfig -u udp://$PUBLIC_IP:1194 -n 10.8.0.0/24 -N
    docker run -v $(pwd)/openvpn-data/conf:/etc/openvpn -e EASYRSA_BATCH=1 --rm kylemanna/openvpn ovpn_initpki nopass
fi

echo "[*] Очищення старих контейнерів та запуск (Це займе кілька хвилин)..."
docker compose down -v
docker compose up -d --build

echo "========================================="
echo "[+] Все успішно запущено!"
echo "[+] CTFd: http://localhost:8000 (Авто-налаштування займе ще ~30 секунд)"
echo "[+] Адмін CTFd: admin / admin"
echo "[+] VPN Портал: http://localhost:5050"
echo "========================================="
