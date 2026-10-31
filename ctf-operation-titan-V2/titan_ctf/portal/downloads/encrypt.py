#!/usr/bin/env python3
# Titan Secure Courier - шифрування службових повідомлень (RSA)
# Ця програма зашифрувала повідомлення, яке перехопили в мережі.
import random

E = 3  # "швидке" шифрування


def is_prime(n, rounds=40):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def gen_prime(bits):
    while True:
        p = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        # p - 1 не повинно ділитися на E, інакше E не буде оберненим
        if (p - 1) % E != 0 and is_prime(p):
            return p


if __name__ == "__main__":
    flag = open("flag.txt", "rb").read().strip()
    p, q = gen_prime(1024), gen_prime(1024)
    n = p * q
    m = int.from_bytes(flag, "big")
    c = pow(m, E, n)
    with open("output.txt", "w") as f:
        f.write(f"n = {n}\ne = {E}\nc = {c}\n")
    print("[+] Generated output.txt")
