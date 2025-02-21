import hashlib
from embit import bip32
from .baseconv import base_encode
from .wdt import wdt


# A deterministic PRNG based on SHA256(seed || counter)
class DeterministicPRNG:
    def __init__(self, seed: bytes):
        self.seed = seed
        self.counter = 0
        self.buffer = b""

    def __call__(self, n: int) -> bytes:
        while len(self.buffer) < n:
            counter_bytes = self.counter.to_bytes(4, "big")
            self.buffer += hashlib.sha256(self.seed + counter_bytes).digest()
            self.counter += 1
        result = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return result


class KruxPGP:
    """
    A class for generating PGP-compatible RSA keys from a BIP32 HDKey.
    """

    def public_encryption_key(self, key: bip32.HDKey):
        """
        Derive a PGP public encryption key from a BIP32 HDKey.
        """
        key_bits = 2048
        key_index = 0
        path_main = "m/83696968h/828365h/{}h/{}h".format(key_bits, key_index)
        path_encryption = path_main + "/0h"
        key_encryption = self.derive_rsa_key_from_hdkey(
            key.derive(path_encryption), key_bits
        )
        pubkey_encryption = self.encode_public_key(key_encryption)
        public_key = self.to_pem(pubkey_encryption, "PUBLIC KEY")
        print(public_key)
        print(self.to_pem(self.encode_private_key(key_encryption), "PRIVATE KEY"))
        return public_key

    def extended_gcd(self, a, b):
        old_r, r = a, b
        old_s, s = 1, 0
        old_t, t = 0, 1
        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s
            old_t, t = t, old_t - quotient * t
        return old_r, old_s, old_t

    def mod_inverse(self, a, m):
        g, x, y = self.extended_gcd(a, m)
        if g != 1:
            raise ValueError("Modular inverse does not exist")
        else:
            return x % m

    def is_prime(self, n, prng, rounds):
        if n <= 1:
            return False
        elif n <= 3:
            return True
        # Write n-1 as d * 2^s
        s = 0
        d = n - 1
        while d % 2 == 0:
            d //= 2
            s += 1
        # Perform Miller-Rabin tests
        for _ in range(rounds):
            byte_len = 0
            tmp = n
            while tmp:
                byte_len += 1
                tmp //= 256
            a_bytes = prng(byte_len)
            a = int.from_bytes(a_bytes, "big")
            a = 2 + (a % (n - 3))  # a is in [2, n-2]
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for __ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    def generate_prime(self, bits, prng, mr_rounds=20):
        # Generate initial candidate
        byte_length = (bits + 7) // 8
        candidate_bytes = prng(byte_length)
        candidate = int.from_bytes(candidate_bytes, "big")
        # Set highest bit and ensure oddness
        candidate |= (1 << (bits - 1)) | 1

        while True:
            wdt.feed()  # Keep watchdog timer alive
            # Test current candidate
            if self.is_prime(candidate, prng, mr_rounds):
                return candidate
            # Try next odd number
            candidate += 2
            # Regenerate if overflow beyond desired bit length
            # if candidate.bit_length() > bits:  # bit_length method not available in micropython
            #     candidate_bytes = prng(byte_length)
            #     candidate = int.from_bytes(candidate_bytes, "big")
            #     candidate |= (1 << (bits - 1)) | 1

    def generate_rsa_key(self, key_bits, prng):
        e = 65537
        key_bits
        while True:
            p = self.generate_prime(key_bits // 2, prng)
            q = self.generate_prime(key_bits // 2, prng)
            if p != q:
                break
        n = p * q
        phi = (p - 1) * (q - 1)
        d = self.mod_inverse(e, phi)
        dmp1 = d % (p - 1)
        dmq1 = d % (q - 1)
        iqmp = self.mod_inverse(q, p)
        return {
            "n": n,
            "e": e,
            "d": d,
            "p": p,
            "q": q,
            "dmp1": dmp1,
            "dmq1": dmq1,
            "iqmp": iqmp,
        }

    def encode_length(self, l):
        if l < 0x80:
            return bytes([l])
        else:
            temp = l
            result = bytearray()
            if temp == 0:
                result.append(0)
            else:
                while temp:
                    result = bytearray([temp & 0xFF]) + result
                    temp //= 256
            length_bytes = bytes(result)
            return bytes([0x80 | len(length_bytes)]) + length_bytes

    def encode_integer(self, x):
        if x == 0:
            return bytes([0x02, 0x01, 0x00])
        x_bytes_array = bytearray()
        tmp = x
        while tmp:
            x_bytes_array = bytearray([tmp & 0xFF]) + x_bytes_array
            tmp //= 256
        if not x_bytes_array:
            x_bytes_array.append(0)
        x_bytes = bytes(x_bytes_array)
        if x_bytes[0] & 0x80:
            x_bytes = bytes([0x00]) + x_bytes
        return bytes([0x02]) + self.encode_length(len(x_bytes)) + x_bytes

    def encode_private_key(self, rsa):
        version = self.encode_integer(0)
        components = [
            version,
            self.encode_integer(rsa["n"]),
            self.encode_integer(rsa["e"]),
            self.encode_integer(rsa["d"]),
            self.encode_integer(rsa["p"]),
            self.encode_integer(rsa["q"]),
            self.encode_integer(rsa["dmp1"]),
            self.encode_integer(rsa["dmq1"]),
            self.encode_integer(rsa["iqmp"]),
        ]
        content = b"".join(components)
        der = bytes([0x30]) + self.encode_length(len(content)) + content
        return der

    def encode_public_key(self, rsa):
        modulus = self.encode_integer(rsa["n"])
        exponent = self.encode_integer(rsa["e"])
        content = modulus + exponent
        der = bytes([0x30]) + self.encode_length(len(content)) + content
        return der

    def to_pem(self, der, name):
        b64 = base_encode(der, base=64).decode()
        pem = "-----BEGIN {}-----\n".format(name)
        pem += "\n".join([b64[i : i + 64] for i in range(0, len(b64), 64)])
        pem += "\n-----END {}-----\n".format(name)
        return pem

    def derive_rsa_key_from_hdkey(self, hdkey: bip32.HDKey, key_bits: int) -> dict:
        seed = hdkey.secret
        prng = DeterministicPRNG(seed)
        return self.generate_rsa_key(key_bits, prng)
