#!/bin/sh
# Builds the web root: the final site files + a believable .git history.
# Usage: build_repo.sh <site-dir> <history-dir> <out-dir>
set -eu
SITE=$(cd "$1" && pwd); HIST=$(cd "$2" && pwd)
mkdir -p "$3"; OUT=$(cd "$3" && pwd)
FLAG='CTF{g1t_l34k_4nd_x0r_m4st3r}'
REAL_KEY='T1t4n-V4ult!'

find "$OUT" -mindepth 1 -delete; cd "$OUT"
git init -q
git symbolic-ref HEAD refs/heads/main
git config core.fileMode false

commit() {  # name email date message
    GIT_AUTHOR_NAME="$1" GIT_AUTHOR_EMAIL="$2" GIT_COMMITTER_NAME="$1" GIT_COMMITTER_EMAIL="$2" \
    GIT_AUTHOR_DATE="$3" GIT_COMMITTER_DATE="$3" git commit -q -m "$4"
}
A="Alina Koval";      AM="alina@titan.local"
M="Marko Dyachenko";  MM="marko@titan.local"

# 1. landing page
cp "$SITE/titan.css" "$SITE/404.html" .
cp "$HIST/index.v1.html" index.html
git add -A
commit "$A" "$AM" "2026-09-14T10:12:00+03:00" "Initial commit: landing page"

# 2. vault module, placeholder key
mkdir vault
cat > vault/xor_vault.py <<'PY'
"""Titan vault: repeating-key XOR with hex armour."""
from itertools import cycle


def encrypt(plaintext: bytes, key: bytes) -> str:
    return bytes(p ^ k for p, k in zip(plaintext, cycle(key))).hex()


def decrypt(hexdata: str, key: bytes) -> bytes:
    return bytes(c ^ k for c, k in zip(bytes.fromhex(hexdata.strip()), cycle(key)))
PY
cat > vault/config.py <<'PY'
# TODO: set a real key before using the vault
VAULT_KEY = "changeme"
PY
git add -A
commit "$M" "$MM" "2026-09-21T16:40:00+03:00" "Add XOR vault module (WIP)"

# 3. real key + encrypted payload
cat > vault/config.py <<PY
# key rotated, do not share
VAULT_KEY = "$REAL_KEY"
PY
python3 - "$FLAG" "$REAL_KEY" > vault/launch_codes.enc <<'PY'
import sys
from itertools import cycle
pt, key = sys.argv[1].encode(), sys.argv[2].encode()
print(bytes(p ^ k for p, k in zip(pt, cycle(key))).hex())
PY
git add -A
commit "$M" "$MM" "2026-09-28T18:05:00+03:00" "Rotate vault key, encrypt launch codes"

# 4. stop committing secrets
cat > vault/config.py <<'PY'
import os

# the key lives in the environment of the vault host, never in git
VAULT_KEY = os.environ["VAULT_KEY"]
PY
cp "$SITE/README.md" README.md
git add -A
commit "$A" "$AM" "2026-10-02T09:30:00+03:00" "Security: read key from env instead of the repo"

# 5. clean the public tree, ship the final landing page
git rm -q vault/launch_codes.enc
cp "$SITE/index.html" index.html
git add -A
commit "$A" "$AM" "2026-10-05T11:00:00+03:00" "Remove vault artifacts from the public node"

rm -f .git/hooks/*.sample .git/description
git update-server-info
chmod -R a+rX .
git log --oneline
