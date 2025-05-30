from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import logging
from typing import Optional

logger = logging.getLogger("encryption_service")

class EncryptionService:
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY.encode() if settings.ENCRYPTION_KEY else Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def encrypt_message(self, message: str) -> str:
        """Encrypt a message using Fernet symmetric encryption."""
        try:
            encrypted_data = self.cipher_suite.encrypt(message.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting message: {str(e)}")
            raise

    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt a message using Fernet symmetric encryption."""
        try:
            encrypted_data = base64.b64decode(encrypted_message.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting message: {str(e)}")
            raise

# Create a singleton instance
encryption_service = EncryptionService() 