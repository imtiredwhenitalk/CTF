#!/usr/bin/env bash
# Operation Titan deployment.   ./setup.sh [--reset]
#   --reset  wipe CTFd database, VPN keys and rebuild everything from scratch
#   PUBLIC_IP=1.2.3.4 ./setup.sh   force the address written into .ovpn files
set -euo pipefail
cd "$(dirname "$0")"

SUBNET_ADDR=172.28.0.0
SUBNET_MASK=255.255.255.0

echo "========================================="
echo "   Operation Titan: Deployment"
echo "========================================="

# --- Docker ---
if ! command -v docker >/dev/null 2>&1; then
    echo "[!] Docker не знайдено. Встановлюю..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && { sudo apt-get install -y docker.io docker-compose-v2 || sudo apt-get install -y docker.io docker-compose; }
    else
        curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && rm -f get-docker.sh
    fi
    sudo systemctl enable --now docker 2>/dev/null || true
fi

SUDO=""
if ! docker info >/dev/null 2>&1; then SUDO="sudo -E"; fi
if $SUDO docker compose version >/dev/null 2>&1; then
    DC="$SUDO docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DC="$SUDO docker-compose"
else
    echo "[-] Не знайдено 'docker compose' / 'docker-compose'"; exit 1
fi
D="$SUDO docker"

# --- reset ---
if [ "${1:-}" = "--reset" ]; then
    echo "[*] Повне очищення (CTFd DB + VPN ключі)..."
    $DC down -v --remove-orphans || true
    if [ -d openvpn-data ]; then
        $D run --rm -v "$PWD/openvpn-data:/d" alpine sh -c 'rm -rf /d/* /d/.[!.]*' 2>/dev/null || sudo rm -rf openvpn-data
        rm -rf openvpn-data 2>/dev/null || sudo rm -rf openvpn-data
    fi
fi

# --- address written into client profiles / CTFd descriptions ---
# priority: env PUBLIC_IP  >  .env  >  10.10.15.124 (ens18 цього сервера)
if [ -z "${PUBLIC_IP:-}" ] && [ -f .env ]; then
    PUBLIC_IP=$(grep -E '^PUBLIC_IP=' .env | tail -1 | cut -d= -f2- | tr -d '"' || true)
fi
PUBLIC_IP=${PUBLIC_IP:-10.10.15.124}
export PUBLIC_IP
echo "[+] IP сервера: $PUBLIC_IP   (інший: PUBLIC_IP=x.x.x.x ./setup.sh)"
if command -v ip >/dev/null 2>&1 && ! ip -4 addr show 2>/dev/null | grep -qw "$PUBLIC_IP"; then
    echo "[!] Увага: $PUBLIC_IP не знайдено на інтерфейсах цієї машини. Адреса в DHCP могла змінитися (перевірте 'ip a')."
fi

# --- shared UI -> each service build context ---
bash tools/sync_ui.sh

# --- firewall (ufw є в системі; відкриваємо тільки потрібні порти) ---
if command -v ufw >/dev/null 2>&1 && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "[*] ufw активний, відкриваю порти CTF..."
    sudo ufw allow 8000/tcp >/dev/null; sudo ufw allow 5050/tcp >/dev/null
    sudo ufw allow 8001:8010/tcp >/dev/null; sudo ufw allow 1194/udp >/dev/null
fi

# --- OpenVPN PKI ---
if [ ! -f "./openvpn-data/conf/openvpn.conf" ]; then
    echo "[*] Ініціалізація OpenVPN (генерація DH може тривати кілька хвилин)..."
    mkdir -p openvpn-data/conf
    # -s VPN subnet, -N NAT, -d no redirect-gateway (only lab traffic goes via VPN),
    # -D/-b don't touch client DNS, -p push route to the CTF docker network
    $D run --rm -v "$PWD/openvpn-data/conf:/etc/openvpn" kylemanna/openvpn \
        ovpn_genconfig -u "udp://$PUBLIC_IP:1194" -s 10.8.0.0/24 -N -d -D -b \
        -p "route $SUBNET_ADDR $SUBNET_MASK"
    $D run --rm -v "$PWD/openvpn-data/conf:/etc/openvpn" \
        -e EASYRSA_BATCH=1 -e EASYRSA_REQ_CN=Titan-CA kylemanna/openvpn ovpn_initpki nopass
fi

# якщо PKI вже є, але IP змінився - оновлюємо адресу в клієнтських профілях (ключі лишаються)
if [ -f ./openvpn-data/conf/ovpn_env.sh ] && ! grep -q "OVPN_SERVER_URL=udp://$PUBLIC_IP:1194" ./openvpn-data/conf/ovpn_env.sh; then
    echo "[*] Оновлюю адресу VPN у профілях на $PUBLIC_IP"
    $D run --rm -v "$PWD/openvpn-data/conf:/d" alpine sed -i "s#OVPN_SERVER_URL=udp://[^ ]*#OVPN_SERVER_URL=udp://$PUBLIC_IP:1194#" /d/ovpn_env.sh
fi

echo "[*] Збірка та запуск (кілька хвилин)..."
$DC up -d --build --remove-orphans

echo "========================================="
echo "[+] Запущено. CTFd налаштується автоматично за ~1 хв."
echo "    Прогрес:  $DC logs -f ctfd_setup"
echo "    CTFd:       http://$PUBLIC_IP:8000   (${ADMIN_NAME:-admin} / ${ADMIN_PASSWORD:-admin})"
echo "    VPN портал: http://$PUBLIC_IP:5050"
echo "    Завдання напряму: http://$PUBLIC_IP:8001 ... :8010"
echo "    Через VPN: 172.28.0.11 ... 172.28.0.20"
echo "========================================="
