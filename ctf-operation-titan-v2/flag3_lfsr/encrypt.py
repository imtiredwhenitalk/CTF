# Titan custom LFSR stream cipher (16-bit state)
def lfsr(seed, taps, length):
    state = seed
    out = []
    for _ in range(length):
        out.append(state & 1)
        bit = 0
        for t in taps:
            bit ^= (state >> t) & 1
        state = (state >> 1) | (bit << 15)
    return out

def encrypt(data: bytes, seed: int) -> bytes:
    bits = lfsr(seed, [0, 2, 3, 5], len(data) * 8)
    res = bytearray()
    for i, byte in enumerate(data):
        key_byte = int("".join(map(str, bits[i * 8:(i + 1) * 8])), 2)
        res.append(byte ^ key_byte)
    return bytes(res)

# flag.enc = encrypt(flag.encode(), SECRET_SEED)   # 16-bit secret seed
