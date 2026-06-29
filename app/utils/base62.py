# Base62 encoding/decoding utilities
import string

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def encode(num: int) -> str:
    if num == 0:
        return BASE62_ALPHABET[0]

    base62 = []
    base = len(BASE62_ALPHABET)

    while num:
        num, rem = divmod(num, base)
        base62.append(BASE62_ALPHABET[rem])

    return ''.join(reversed(base62))


def decode(short_code: str) -> int:
    base = len(BASE62_ALPHABET)
    num = 0

    for char in short_code:
        num = num * base + BASE62_ALPHABET.index(char)

    return num