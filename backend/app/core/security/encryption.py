import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class EncryptionService:
    def __init__(self):
        # In a real scenario, this key MUST be securely stored in the .env file.
        # It must be a valid Fernet key (32 url-safe base64-encoded bytes).
        self.master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not self.master_key:
            # Generate a new key if not present (only for first time setup)
            self.master_key = Fernet.generate_key().decode()
            print(f"WARNING: No MASTER_ENCRYPTION_KEY found in .env. Generated a new one: {self.master_key}")
            # In a real app, this should automatically be written to .env via config_updater
            
        self.cipher_suite = Fernet(self.master_key.encode())

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        return self.cipher_suite.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            return self.cipher_suite.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            print(f"Decryption failed: {e}")
            return ""

# Singleton instance
encryption_service = EncryptionService()
