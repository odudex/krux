# The MIT License (MIT)

# Copyright (c) 2021-2023 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import hashlib
from Crypto.Cipher import AES
import base64
from embit.wordlists.bip39 import WORDLIST
from kivy.storage.jsonstore import JsonStore
from .krux_settings import Settings, PBKDF2_HMAC_ECB, PBKDF2_HMAC_CBC, AES_BLOCK_SIZE


STORE_FILE_PATH = "../seeds.json"

VERSION_MODE = {
    "AES-ECB": AES.MODE_ECB,
    "AES-CBC": AES.MODE_CBC,
    PBKDF2_HMAC_ECB: AES.MODE_ECB,
    PBKDF2_HMAC_CBC: AES.MODE_CBC,
}

VERSION_NUMBER = {
    "AES-ECB": PBKDF2_HMAC_ECB,
    "AES-CBC": PBKDF2_HMAC_CBC,
}



class AESCipher(object):
    """Helper for AES encrypt/decrypt"""

    def __init__(self, key, salt, iterations):
        self.key = hashlib.pbkdf2_hmac(
            "sha256", key.encode(), salt.encode(), iterations
        )

    def encrypt(self, raw, mode=AES.MODE_ECB, iv=None):
        """Encrypt using AES MODE_ECB and return the value encoded as base64"""
        data_bytes = raw.encode("latin-1") if isinstance(raw, str) else raw
        if iv:
            encryptor = AES.new(self.key, mode, iv)
            data_bytes = iv + data_bytes
        else:
            encryptor = AES.new(self.key, mode)
        encrypted = encryptor.encrypt(
            data_bytes + b"\x00" * ((16 - (len(data_bytes) % 16)) % 16)
        )
        return base64.b64encode(encrypted)

    def decrypt(self, encrypted, mode, iv=None):
        """Decrypt a base64 using AES MODE_ECB and return the value decoded as string"""
        if iv:
            decryptor = AES.new(self.key, mode, iv)
        else:
            decryptor = AES.new(self.key, mode)
        load = decryptor.decrypt(encrypted).decode("utf-8")
        return load.replace("\x00", "")

    def decrypt_bytes(self, encrypted, mode, i_vector=None):
        """Decrypt and return value as bytes"""
        if i_vector:
            decryptor = AES.new(self.key, mode, i_vector)
        else:
            decryptor = AES.new(self.key, mode)
        return decryptor.decrypt(encrypted)


class MnemonicStorage:
    """Handler of stored encrypted seeds"""

    def __init__(self) -> None:
        self.stored = JsonStore(STORE_FILE_PATH)
        self.stored_sd = {}
        self.has_sd_card = False


    def list_mnemonics(self, sd_card=False):
        """List all seeds stored on a file"""
        mnemonic_ids = []
        source = self.stored_sd if sd_card else self.stored
        for mnemonic_id in source:
            mnemonic_ids.append(mnemonic_id)
        return mnemonic_ids

    def decrypt(self, key, mnemonic_id, sd_card=False):
        """Decrypt a selected encrypted mnemonic from a file"""
        try:
            encrypted_data = self.stored.get(mnemonic_id)["data"]
            iterations = self.stored.get(mnemonic_id)["key_iterations"]
            version = self.stored.get(mnemonic_id)["version"]
        except:
            return None
        data = base64.b64decode(encrypted_data)
        mode = VERSION_MODE[version]
        if mode == AES.MODE_ECB:
            encrypted_mnemonic = data
            iv = None
        else:
            encrypted_mnemonic = data[AES_BLOCK_SIZE:]
            iv = data[:AES_BLOCK_SIZE]
        decryptor = AESCipher(key, mnemonic_id, iterations)
        words = decryptor.decrypt(encrypted_mnemonic, mode, iv)
        return words

    def store_encrypted(self, key, mnemonic_id, mnemonic, sd_card=False, iv=None):
        """Saves the encrypted mnemonic on a file"""
        encryptor = AESCipher(key, mnemonic_id, Settings().encryption.pbkdf2_iterations)
        mode = VERSION_MODE[Settings().encryption.version]
        encrypted = encryptor.encrypt(mnemonic, mode, iv).decode("utf-8")
        mnemonics = {}
        success = True
        self.stored.put(mnemonic_id, data = encrypted)
        self.stored[mnemonic_id]["version"] = VERSION_NUMBER[Settings().encryption.version]
        self.stored[mnemonic_id]["key_iterations"] = Settings().encryption.pbkdf2_iterations
        self.stored[mnemonic_id] = self.stored[mnemonic_id]

        return success

    def del_mnemonic(self, mnemonic_id, sd_card=False):
        """Remove an entry from encrypted mnemonics file"""
        self.stored.delete(mnemonic_id)


class EncryptedQRCode:
    """Creates and decrypts encrypted mnemonic QR codes"""

    def __init__(self) -> None:
        self.mnemonic_id = None
        self.version = VERSION_NUMBER[Settings().encryption.version]
        self.iterations = Settings().encryption.pbkdf2_iterations
        self.encrypted_data = None

    def create(self, key, mnemonic_id, mnemonic, i_vector=None):
        """Joins necessary data and creates encrypted mnemonic QR codes"""
        name_lenght = len(mnemonic_id.encode())
        version = VERSION_NUMBER[Settings().encryption.version]
        key_iterations = Settings().encryption.pbkdf2_iterations
        qr_code_data = name_lenght.to_bytes(1, "big")
        qr_code_data += mnemonic_id.encode()
        qr_code_data += version.to_bytes(1, "big")
        qr_code_data += (key_iterations // 10000).to_bytes(3, "big")
        encryptor = AESCipher(key, mnemonic_id, Settings().encryption.pbkdf2_iterations)
        mode = VERSION_MODE[Settings().encryption.version]
        words = mnemonic.split(" ")
        checksum_bits = 8 if len(words) == 24 else 4
        indexes = [WORDLIST.index(word) for word in words]
        bitstring = "".join(["{:0>11}".format(bin(index)[2:]) for index in indexes])[
            :-checksum_bits
        ]
        bytes_to_encrypt = int(bitstring, 2).to_bytes((len(bitstring) + 7) // 8, "big")
        bytes_to_encrypt += hashlib.sha256(bytes_to_encrypt).digest()[:16]
        base64_encrypted = encryptor.encrypt(bytes_to_encrypt, mode, i_vector)
        bytes_encrypted = base64.b64decode(base64_encrypted)
        qr_code_data += bytes_encrypted
        return qr_code_data

    def public_data(self, data):
        """Parse and returns encrypted mnemonic QR codes public data"""
        mnemonic_info = "Encrypted QR Code:\n"
        try:
            id_lenght = int.from_bytes(data[:1], "big")
            self.mnemonic_id = data[1 : id_lenght + 1].decode("utf-8")
            mnemonic_info += "ID: " + self.mnemonic_id + "\n"
            self.version = int.from_bytes(data[id_lenght + 1 : id_lenght + 2], "big")
            version_name = [k for k, v in VERSION_NUMBER.items() if v == self.version][
                0
            ]
            mnemonic_info += "Version: " + version_name + "\n"
            self.iterations = int.from_bytes(data[id_lenght + 2 : id_lenght + 5], "big")
            self.iterations *= 10000
            mnemonic_info += "Key iter.: " + str(self.iterations)
        except:
            return None
        extra_bytes = id_lenght + 5  # 1(id lenght byte) + 1(version) + 3(iterations)
        if self.version == 1:
            extra_bytes += 16  # Initial Vector size
        extra_bytes += 16  # Encrypted QR checksum is always 16 bytes
        len_mnemonic_bytes = len(data) - extra_bytes
        if len_mnemonic_bytes not in (16, 32):
            return None
        self.encrypted_data = data[id_lenght + 5 :]
        return mnemonic_info

    def decrypt(self, key):
        """Decrypts encrypted mnemonic QR codes"""
        mode = VERSION_MODE[self.version]
        if mode == AES.MODE_ECB:
            encrypted_mnemonic_data = self.encrypted_data
            i_vector = None
        else:
            encrypted_mnemonic_data = self.encrypted_data[AES_BLOCK_SIZE:]
            i_vector = self.encrypted_data[:AES_BLOCK_SIZE]
        decryptor = AESCipher(key, self.mnemonic_id, self.iterations)
        decrypted_data = decryptor.decrypt_bytes(
            encrypted_mnemonic_data, mode, i_vector
        )
        mnemonic_data = decrypted_data[:-AES_BLOCK_SIZE]
        checksum = decrypted_data[-AES_BLOCK_SIZE:]
        # Data validation:
        if hashlib.sha256(mnemonic_data).digest()[:16] != checksum:
            return None
        return mnemonic_data
