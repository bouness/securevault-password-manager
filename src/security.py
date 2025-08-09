import base64
import secrets
import string

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityManager:
    @staticmethod
    def generate_salt() -> bytes:
        """Generate a cryptographically secure random salt"""
        return secrets.token_bytes(16)

    @staticmethod
    def generate_key_from_password(password: str, salt: bytes) -> bytes:
        """Generate encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt_data(data: str, key: bytes) -> bytes:
        """Encrypt data using Fernet"""
        f = Fernet(key)
        return f.encrypt(data.encode())

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
        """Decrypt data using Fernet"""
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()

    @staticmethod
    def generate_password(
        length: int = 16,
        use_symbols: bool = True,
        use_numbers: bool = True,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
    ) -> str:
        """Generate secure random password"""
        charset = ""
        if use_lowercase:
            charset += string.ascii_lowercase
        if use_uppercase:
            charset += string.ascii_uppercase
        if use_numbers:
            charset += string.digits
        if use_symbols:
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not charset:
            charset = string.ascii_letters + string.digits

        password = "".join(secrets.choice(charset) for _ in range(length))
        return password
