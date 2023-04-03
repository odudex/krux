import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import base64
from kivy.storage.jsonstore import JsonStore

STORE_FILE_PATH = "../seeds.json"

class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
    
class StoredSeeds:
    def __init__(self) -> None:
        self.encrypted_store = JsonStore(STORE_FILE_PATH)

    def list_fingerprints(self):
        fingerprints = []
        for fingerprint in self.encrypted_store:
            fingerprints.append(fingerprint)
        return fingerprints
    
    def decrypt(self, key, fingerprint):
        decryptor = AESCipher(key)
        try:
            load = self.encrypted_store.get(fingerprint)['load']
            words = decryptor.decrypt(load)
        except:
            return None
        return words
    def sotore_encrypted(self, key, fingerprint, seed):
        encryptor = AESCipher(key)
        encrypted = encryptor.encrypt(seed).decode('utf-8')
        self.encrypted_store = JsonStore(STORE_FILE_PATH)
        self.encrypted_store.put(fingerprint, load=encrypted)

    def del_seed(self, fingerprint):
        self.encrypted_store.delete(fingerprint)


