# Writeup: Flag 5 - Domain Takeover

1. Відкрити `http://localhost:8085`.
2. Запитати TGS-квиток для сервісного акаунта `svc_backup`.
3. Витягти Kerberoast hash (`$krb5tgs$23$...`).
4. Проаналізувати структуру хешу та отримати прапор: `CTF{4ct1v3_d1r3ct0ry_c0mpr0m1s3d_k3rb3r0s}`.
