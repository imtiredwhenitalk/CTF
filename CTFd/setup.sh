#!/usr/bin/env bash
# Operation Titan — platform stack (CTFd + OpenVPN + watermark service).
#
#   ./setup.sh              start / update the platform
#   ./setup.sh --reset      wipe CTFd DB, VPN keys, watermark registry and rebuild
#   PUBLIC_IP=1.2.3.4 ./setup.sh
#
# Challenges are started separately from ../ctf-operation-titan-v2/setup.sh.
set -euo pipefail
cd "$(dirname "$0")"

VPN_SUBNET=10.8.0.0/24
CHALLENGE_NET=172.28.0.0/24

echo "========================================="
echo "   Operation Titan: platform"
echo "========================================="

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
D="$SUDO docker"

# --- address -------------------------------------------------------------
if [ -z "${PUBLIC_IP:-}" ] && [ -f .env ]; then
    PUBLIC_IP=$(grep -E '^PUBLIC_IP=' .env | tail -1 | cut -d= -f2- | tr -d '"' || true)
fi
PUBLIC_IP=${PUBLIC_IP:-10.10.15.124}
export PUBLIC_IP
echo "[+] IP сервера: $PUBLIC_IP   (інший: PUBLIC_IP=x.x.x.x ./setup.sh)"
if command -v ip >/dev/null 2>&1 && ! ip -4 addr show 2>/dev/null | grep -qw "$PUBLIC_IP"; then
    echo "[!] Увага: $PUBLIC_IP не знайдено на інтерфейсах цієї машини."
fi

# --- reset ---------------------------------------------------------------
if [ "${1:-}" = "--reset" ]; then
    echo "[*] Повне очищення платформи (CTFd DB + VPN + watermark)..."
    $DC down -v --remove-orphans || true
    rm -rf openvpn-data data logs
fi

# --- shared state --------------------------------------------------------
mkdir -p data logs openvpn-data/conf/ccd plugins
if [ ! -f data/watermark.key ]; then
    echo "[*] Генерую watermark-секрет..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import secrets; print(secrets.token_hex(32))' > data/watermark.key
    else
        openssl rand -hex 32 > data/watermark.key
    fi
fi
chmod 0644 data/watermark.key
[ -f data/user_registry.csv ] || : > data/user_registry.csv
chmod 0644 data/user_registry.csv
chmod 0777 logs
touch logs/flag_issuance.log
chmod 0666 logs/flag_issuance.log
# --- VPN portal team credentials ----------------------------------------
# Passwords are stored as PBKDF2 hashes.  Create/reset team accounts with:
#   sudo python3 vpn-portal/admin_teams.py add <team>
if [ ! -f data/team_credentials.json ]; then
    printf '{\n  "version": 1,\n  "teams": {}\n}\n' > data/team_credentials.json
fi
chmod 0600 data/team_credentials.json
if [ ! -f data/portal_secret.key ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import secrets; print(secrets.token_hex(32))' > data/portal_secret.key
    else
        openssl rand -hex 32 > data/portal_secret.key
    fi
fi
chmod 0600 data/portal_secret.key


# --- OpenVPN PKI ---------------------------------------------------------
if [ ! -f openvpn-data/conf/openvpn.conf ] || [ ! -f openvpn-data/conf/pki/ca.crt ]; then
    echo "[*] Ініціалізація OpenVPN (генерація DH може тривати кілька хвилин)..."
    rm -f openvpn-data/conf/openvpn.conf openvpn-data/conf/ovpn_env.sh
    mkdir -p openvpn-data/conf
    # -d: no redirect-gateway, -D/-b: don't touch client DNS, no -N: keep the
    # real 10.8.0.x source address (required for per-user flag watermarking).
    # topology subnet + a small dynamic pool leaves .10-.250 for fixed users.
    $D run --rm -v "$PWD/openvpn-data/conf:/etc/openvpn" kylemanna/openvpn \
        ovpn_genconfig -u "udp://$PUBLIC_IP:1194" -s "$VPN_SUBNET" -d -D -b \
        -e "topology subnet" \
        -e "ifconfig-pool 10.8.0.2 10.8.0.9" \
        -p "route 172.28.0.0 255.255.255.0"
    if [ ! -f openvpn-data/conf/pki/ca.crt ]; then
        $D run --rm -v "$PWD/openvpn-data/conf:/etc/openvpn" \
            -e EASYRSA_BATCH=1 -e EASYRSA_REQ_CN=Titan-CA kylemanna/openvpn ovpn_initpki nopass
    fi
fi

# Existing installations: make the config compatible with fixed IPs.
CONF=openvpn-data/conf/openvpn.conf
if [ -f "$CONF" ]; then
    grep -qE '^topology[[:space:]]+subnet' "$CONF" || echo "topology subnet" >> "$CONF"
    grep -qE '^ifconfig-pool[[:space:]]' "$CONF" || echo "ifconfig-pool 10.8.0.2 10.8.0.9" >> "$CONF"
    grep -qE '^client-config-dir[[:space:]]' "$CONF" || echo "client-config-dir /etc/openvpn/ccd" >> "$CONF"
fi
# OpenVPN 2.7: explicit ifconfig-pool requires nopool on the server line.
sed -i -E 's/^server([[:space:]]+[^[:space:]]+[[:space:]]+[^[:space:]]+)[[:space:]]*$/server\1 nopool/' "$CONF" 

mkdir -p openvpn-data/conf/ccd

if [ -f openvpn-data/conf/ovpn_env.sh ]; then
    sed -i 's/^declare -x OVPN_NAT=.*/declare -x OVPN_NAT=0/' openvpn-data/conf/ovpn_env.sh
    sed -i "s#^declare -x OVPN_SERVER_URL=.*#declare -x OVPN_SERVER_URL=udp://$PUBLIC_IP:1194#" openvpn-data/conf/ovpn_env.sh
fi

# OpenVPN 2.7 + DCO: compression is not allowed.  kylemanna's
# ovpn_genconfig writes "comp-lzo no" and push "comp-lzo no" when
# OVPN_COMP_LZO=0; strip both so modern clients can connect.
if [ -f "$CONF" ]; then
    sed -i -E '/^[[:space:]]*comp-lzo([[:space:]]|$)/d; /^[[:space:]]*compress([[:space:]]|$)/d; /^[[:space:]]*push[[:space:]]+"comp-lzo/d; /^[[:space:]]*push[[:space:]]+"compress/d' "$CONF"
fi
if [ -f openvpn-data/conf/ovpn_env.sh ]; then
    sed -i -E 's/^declare -x OVPN_COMP_LZO=.*/declare -x OVPN_COMP_LZO=""/' openvpn-data/conf/ovpn_env.sh
fi

# --- routing / firewall --------------------------------------------------
# VPN clients must be able to reach the challenge bridge and receive replies.
if [ "$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null || echo 0)" != "1" ]; then
    echo "[*] Вмикаю IPv4 forwarding..."
    $SUDO sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true
fi
# Return traffic from a challenge container (172.28.0.x) to a VPN client
# (10.8.0.x) arrives on the Docker bridge while the route back is via tun0.
# Strict reverse-path filtering would drop it; use loose mode.
if [ -w /proc/sys/net/ipv4/conf/all/rp_filter ] || $SUDO test -w /proc/sys/net/ipv4/conf/all/rp_filter; then
    $SUDO sysctl -w net.ipv4.conf.all.rp_filter=2 >/dev/null 2>&1 || true
    $SUDO sysctl -w net.ipv4.conf.default.rp_filter=2 >/dev/null 2>&1 || true
fi
if command -v iptables >/dev/null 2>&1; then
    CHAIN=FORWARD
    $SUDO iptables -L DOCKER-USER >/dev/null 2>&1 && CHAIN=DOCKER-USER
    $SUDO iptables -C "$CHAIN" -i tun0 -o br-+ -j ACCEPT 2>/dev/null || \
        $SUDO iptables -I "$CHAIN" -i tun0 -o br-+ -j ACCEPT 2>/dev/null || true
    $SUDO iptables -C "$CHAIN" -i br-+ -o tun0 -j ACCEPT 2>/dev/null || \
        $SUDO iptables -I "$CHAIN" -i br-+ -o tun0 -j ACCEPT 2>/dev/null || true
fi
if command -v ufw >/dev/null 2>&1 && $SUDO ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "[*] ufw активний, відкриваю порти CTF..."
    $SUDO ufw allow 8000/tcp >/dev/null 2>&1 || true
    $SUDO ufw allow 5050/tcp >/dev/null 2>&1 || true
    $SUDO ufw allow 8001:8012/tcp >/dev/null 2>&1 || true
    $SUDO ufw allow 1194/udp >/dev/null 2>&1 || true
    $SUDO ufw route allow from 10.8.0.0/24 to 172.28.0.0/24 >/dev/null 2>&1 || true
    $SUDO ufw route allow from 172.28.0.0/24 to 10.8.0.0/24 >/dev/null 2>&1 || true
fi

# --- start ---------------------------------------------------------------
echo "[*] Збірка та запуск платформи..."
$DC up -d --build --remove-orphans

# Re-apply OpenVPN config fixes to an already-running container.
$D restart openvpn >/dev/null 2>&1 || true

echo "========================================="
echo "[+] Платформа запущена."
echo "    CTFd:        http://$PUBLIC_IP:8000   (${ADMIN_NAME:-admin} / ${ADMIN_PASSWORD:-admin})"
echo "    VPN портал:  http://$PUBLIC_IP:5050"
echo "    Watermark:   внутрішній http://watermark:5060 (лише titan_internal)"
echo "    Команди:     sudo python3 vpn-portal/admin_teams.py add <team>"
echo "    Далі:        ../ctf-operation-titan-v2/setup.sh"
echo "========================================="
