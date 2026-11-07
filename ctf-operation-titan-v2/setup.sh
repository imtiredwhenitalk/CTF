#!/usr/bin/env bash
# Operation Titan — full deployment.
#
#   ./setup.sh              start/update platform (../CTFd) + challenges
#   ./setup.sh --reset      wipe CTFd DB, VPN keys, watermark registry and rebuild
#   PUBLIC_IP=1.2.3.4 ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

PLATFORM_DIR="../CTFd"

echo "========================================="
echo "   Operation Titan: deployment"
echo "========================================="

if [ ! -f "$PLATFORM_DIR/docker-compose.yml" ] || [ ! -f "$PLATFORM_DIR/setup.sh" ]; then
    echo "[-] Не знайдено платформу в $PLATFORM_DIR (docker-compose.yml + setup.sh)"
    exit 1
fi

# --- Docker --------------------------------------------------------------
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

# --- address -------------------------------------------------------------
if [ -z "${PUBLIC_IP:-}" ] && [ -f "$PLATFORM_DIR/.env" ]; then
    PUBLIC_IP=$(grep -E '^PUBLIC_IP=' "$PLATFORM_DIR/.env" | tail -1 | cut -d= -f2- | tr -d '"' || true)
fi
PUBLIC_IP=${PUBLIC_IP:-10.10.15.124}
export PUBLIC_IP

# --- reset ---------------------------------------------------------------
if [ "${1:-}" = "--reset" ]; then
    echo "[*] Зупиняю завдання та звільняю мережі..."
    $DC down -v --remove-orphans || true
fi

# --- platform first (creates titan_net + titan_internal) -----------------
if [ "${1:-}" = "--reset" ]; then
    bash "$PLATFORM_DIR/setup.sh" --reset
else
    bash "$PLATFORM_DIR/setup.sh"
fi

# --- shared UI -> each challenge build context --------------------------
bash tools/sync_ui.sh

# --- firewall for challenge ports ---------------------------------------
if command -v ufw >/dev/null 2>&1 && $SUDO ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "[*] ufw активний, відкриваю порти завдань..."
    $SUDO ufw allow 8001:8012/tcp >/dev/null 2>&1 || true
fi

# --- challenges ----------------------------------------------------------
echo "[*] Збірка та запуск завдань..."
$DC up -d --build --remove-orphans

echo "========================================="
echo "[+] Все запущено."
echo "    CTFd:        http://$PUBLIC_IP:8000   (${ADMIN_NAME:-admin} / ${ADMIN_PASSWORD:-admin})"
echo "    VPN портал:  http://$PUBLIC_IP:5050"
echo "    Завдання:    http://$PUBLIC_IP:8001 ... :8012"
echo "    Через VPN:   172.28.0.11 ... 172.28.0.22"
echo "    Watermark:   ../CTFd/logs/flag_issuance.log"
echo "========================================="
