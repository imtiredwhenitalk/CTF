#!/bin/bash
# ctf.sh — єдина точка керування LNTU CTF (CTFd + 15 тасків + опційно OpenVPN)
set -euo pipefail
cd "$(dirname "$0")"

DC="docker compose"
CTFD_URL="${CTFD_URL:-http://localhost:8000}"

detect_ip() {
  # IP, який побачать гравці: перший не-loopback адрес хоста
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1 || true
}
HOST_IP="${CTF_HOST:-$(detect_ip)}"; HOST_IP="${HOST_IP:-localhost}"

need_docker() {
  if ! command -v docker >/dev/null; then
    echo "[*] Docker не знайдено — встановлюю..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER" || true
    echo "[!] Перелогіньтесь (або виконайте 'newgrp docker') і запустіть команду ще раз."; exit 1
  fi
  $DC version >/dev/null 2>&1 || { echo "[-] Потрібен плагін 'docker compose' (docker-compose-v2)"; exit 1; }
}

usage() {
  cat <<U
Використання: ./ctf.sh <команда> [аргументи]

  setup                  перший запуск: перевірка Docker, збірка й запуск усього
  up                     зібрати та запустити CTFd + усі таски
  down                   зупинити все (дані CTFd зберігаються)
  restart [сервіс]       перезапустити все або один сервіс (напр. flag3_ctf)
  rebuild <сервіс>       перебудувати та перезапустити один таск
  status                 стан контейнерів
  logs [сервіс]          логи (Ctrl+C — вихід)
  populate <TOKEN>       додати всі 15 тасків із прапорами та підказками в CTFd
  check                  самоперевірка: проходить усі таски як гравець
  vpn-init               ініціалізація OpenVPN PKI (один раз)
  vpn-up                 запустити OpenVPN-контейнер
  clean                  ВИДАЛИТИ все разом з даними CTFd (запитає підтвердження)

Змінні: CTF_HOST=<IP для гравців> (зараз: $HOST_IP), CTFD_URL=$CTFD_URL
U
}

wait_http() { # url, секунд
  for _ in $(seq 1 "$2"); do curl -fs -o /dev/null "$1" && return 0; sleep 1; done; return 1
}

cmd="${1:-help}"; shift || true
case "$cmd" in
  setup)
    need_docker
    command -v python3 >/dev/null || sudo apt-get install -y python3
    command -v curl >/dev/null || sudo apt-get install -y curl
    $DC up -d --build
    echo "[*] Чекаю на CTFd..."
    wait_http "$CTFD_URL" 120 && echo "[+] CTFd відповідає" || echo "[!] CTFd ще стартує — перевірте './ctf.sh logs ctfd'"
    echo
    echo "================================================================"
    echo " CTFd:        http://$HOST_IP:8000  (перший вхід — майстер налаштування)"
    echo " Таски:       http://$HOST_IP:8081 … http://$HOST_IP:8095"
    echo " Далі:        1) створіть адміна в CTFd"
    echo "              2) Admin → Settings → Access Tokens → згенеруйте токен"
    echo "              3) ./ctf.sh populate <TOKEN>"
    echo "              4) ./ctf.sh check"
    echo "================================================================"
    ;;
  up)       need_docker; $DC up -d --build ;;
  down)     need_docker; $DC --profile vpn down ;;
  restart)  need_docker; $DC restart "$@" ;;
  rebuild)  need_docker; [ $# -ge 1 ] || { echo "вкажіть сервіс, напр. flag3_ctf"; exit 1; }; $DC up -d --build "$@" ;;
  status)   need_docker; $DC --profile vpn ps ;;
  logs)     need_docker; $DC logs -f --tail=100 "$@" ;;
  populate)
    [ $# -ge 1 ] || { echo "Використання: ./ctf.sh populate <TOKEN>"; exit 1; }
    python3 scripts/populate_ctfd.py --url "$CTFD_URL" --token "$1" --host "$HOST_IP" ;;
  check)    python3 scripts/check_challenges.py --host "${1:-$HOST_IP}" ;;
  vpn-init)
    need_docker
    PUBLIC_IP="${CTF_HOST:-$(curl -fs --max-time 5 ifconfig.me || true)}"; PUBLIC_IP="${PUBLIC_IP:-$HOST_IP}"
    if [ -f openvpn-data/conf/openvpn.conf ]; then echo "[=] PKI вже ініціалізовано"; exit 0; fi
    mkdir -p openvpn-data/conf
    docker run -v "$PWD/openvpn-data/conf:/etc/openvpn" --rm kylemanna/openvpn ovpn_genconfig -u "udp://$PUBLIC_IP:1194" -n 10.8.0.0/24 -N
    docker run -v "$PWD/openvpn-data/conf:/etc/openvpn" -e EASYRSA_BATCH=1 --rm kylemanna/openvpn ovpn_initpki nopass
    echo "[+] Готово. Запуск: ./ctf.sh vpn-up" ;;
  vpn-up)   need_docker; $DC --profile vpn up -d openvpn ;;
  clean)
    read -r -p "Це видалить усі контейнери та дані CTFd (users, solves). Введіть YES: " a
    [ "$a" = "YES" ] && $DC --profile vpn down -v --remove-orphans || echo "Скасовано" ;;
  *) usage ;;
esac
