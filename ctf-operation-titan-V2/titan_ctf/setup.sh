#!/usr/bin/env bash
# Підготовка артефактів завдань. Запускати один раз перед `docker compose up --build`.
set -euo pipefail
cd "$(dirname "$0")"

DL=portal/downloads
mkdir -p "$DL"

echo "[*] Flag 1: створюю git-репозиторій усередині app/ (.git буде доступний через nginx)"
rm -rf flag1_git_leak/app/.git
(
  cd flag1_git_leak/app
  git init -q
  git config user.email "dev@titan.local"
  git config user.name "titan-dev"
  git add index.html
  git commit -q -m "initial monitoring page"
  # Прапор лежить у .git/config
  git config titan.note "backup-token"
  git config titan.flag "CTF{w3lc0m3_t0_th3_tr1d3nt_n3tw0rk_2026}"
)

echo "[*] Flag 3: генерую production.conf.enc"
(cd flag3_crypto_rev && python3 encryptor.py)
cp flag3_crypto_rev/production.conf.enc flag3_crypto_rev/config_loader.py "$DL"/

echo "[*] Flag 6: копіюю драйвер для скачування"
cp flag6_kernel_scada/scada_driver.c "$DL"/

echo "[*] Flag 8: генерую RSA-завдання"
(
  cd flag8_crypto_rsa
  printf '%s' 'CTF{sm4ll_3xp0n3nt_n0_p4dd1ng_br0k3_rs4_5518}' > flag.txt
  python3 encrypt.py
  rm -f flag.txt
)
cp flag8_crypto_rsa/encrypt.py flag8_crypto_rsa/output.txt "$DL"/

if [ ! -f .env ]; then
  echo "[*] Створюю .env з випадковим SECRET_KEY"
  printf 'SECRET_KEY=%s\nPUBLIC_HOST=localhost\n' "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
fi

echo "[+] Готово. Далі: docker compose up --build -d"
echo "    Портал: http://localhost:8080"
