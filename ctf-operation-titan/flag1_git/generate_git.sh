#!/bin/sh
git init
git config user.name "Admin"
git config user.email "admin@titan"
echo "def encrypt(text): return ''.join([chr(ord(c)^42) for c in text])" > crypto.py
git add index.html crypto.py
git commit -m "Initial commit"
echo "CTF{g1t_l34k_4nd_x0r_m4st3r}" | python3 -c "import sys; print(''.join([chr(ord(c)^42) for c in sys.stdin.read().strip()]))" > flag.enc
git add flag.enc
git commit -m "Added encrypted flag"
rm crypto.py
git add crypto.py
git commit -m "Removed crypto.py"
chmod -R 755 .git
