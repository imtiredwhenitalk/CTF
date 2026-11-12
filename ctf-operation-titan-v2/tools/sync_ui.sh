#!/usr/bin/env bash
# Copies the shared design system into every service that uses it (each Docker build context is separate).
set -euo pipefail
cd "$(dirname "$0")/.."
for d in flag1_ssti flag2_jwt flag4_pickle flag5_jwt_rsa flag6_ecb flag7_sqli flag9_stego flag10_lfi vpn-portal; do
  cp shared/titan_ui.py shared/titan.css "$d"/
done
for d in flag3_lfsr flag8_wiener; do cp shared/titan.css "$d"/; done
echo "[+] UI synced"
