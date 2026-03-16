import os
from cryptography.fernet import Fernet
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KEY_FILE = BASE_DIR / "secret.key"


def get_master_key() -> bytes:

    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)

    with open(KEY_FILE, "rb") as f:
        return f.read()
    
cipher_suite = Fernet(get_master_key())

def encrypt_data(plain_text: str) -> str:
    if not plain_text: return ""
    encrypted_bytes = cipher_suite.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_data(cipher_text: str) -> str:
    if not cipher_text: return ""
    decrypted_bytes = cipher_suite.decrypt(cipher_text.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')
