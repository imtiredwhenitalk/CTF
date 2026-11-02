# LFSR Encryption
def lfsr(seed, taps, length):
    state = seed
    out = []
    for _ in range(length):
        out.append(state & 1)
        bit = 0
        for t in taps: bit ^= (state >> t) & 1
        state = (state >> 1) | (bit << 15)
    return out

def encrypt(text, seed):
    bits = lfsr(seed, [0, 2, 3, 5], len(text) * 8)
    res = []
    for i, char in enumerate(text):
        key_byte = int("".join(map(str, bits[i*8:(i+1)*8])), 2)
        res.append(chr(ord(char) ^ key_byte))
    return "".join(res)
