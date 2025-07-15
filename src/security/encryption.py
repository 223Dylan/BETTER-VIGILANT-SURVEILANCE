import base64
import hashlib
import hmac
import json
import os
from base64 import b64encode, urlsafe_b64encode
from datetime import datetime
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()


class EncryptionManager:
    def __init__(self):
        self.symmetric_key = os.getenv("ENCRYPTION_KEY")
        if not self.symmetric_key:
            # Generate a new key if none exists
            self.symmetric_key = urlsafe_b64encode(os.urandom(32)).decode()
            logger.warning("No encryption key found in environment. Generated new key.")

        # Ensure key is properly formatted
        try:
            # If key is not base64 encoded, encode it
            if not self.symmetric_key.endswith("="):
                self.symmetric_key = urlsafe_b64encode(
                    self.symmetric_key.encode()
                ).decode()

            # Initialize Fernet with the properly formatted key
            self.fernet = Fernet(self.symmetric_key.encode())
            logger.info("Encryption manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise

        # Asymmetric keys for request signing
        self.private_key_path = os.getenv("PRIVATE_KEY_PATH", "keys/private_key.pem")
        self.public_key_path = os.getenv("PUBLIC_KEY_PATH", "keys/public_key.pem")

        # Ensure key directory exists
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)

        # Load or generate asymmetric keys
        if not (
            os.path.exists(self.private_key_path)
            and os.path.exists(self.public_key_path)
        ):
            self._generate_asymmetric_keys()
        else:
            self._load_asymmetric_keys()

    def _generate_asymmetric_keys(self):
        """Generate new RSA key pair."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Save private key
        with open(self.private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Save public key
        with open(self.public_key_path, "wb") as f:
            f.write(
                private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

        self.private_key = private_key
        self.public_key = private_key.public_key()

    def _load_asymmetric_keys(self):
        """Load existing RSA key pair."""
        # Load private key
        with open(self.private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )

        # Load public key
        with open(self.public_key_path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt data using symmetric encryption."""
        json_data = json.dumps(data)
        return self.fernet.encrypt(json_data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt data using symmetric encryption."""
        decrypted_data = self.fernet.decrypt(encrypted_data.encode())
        return json.loads(decrypted_data.decode())

    def sign_request(
        self, data: Dict[str, Any], timestamp: Optional[str] = None
    ) -> str:
        """Sign request data using RSA private key."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        # Add timestamp to data
        data["timestamp"] = timestamp

        # Convert data to string
        data_str = json.dumps(data, sort_keys=True)

        # Sign the data
        signature = self.private_key.sign(
            data_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return base64.b64encode(signature).decode()

    def verify_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """Verify request signature using RSA public key."""
        try:
            # Convert data to string
            data_str = json.dumps(data, sort_keys=True)

            # Verify the signature
            self.public_key.verify(
                base64.b64decode(signature),
                data_str.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    def generate_hmac(self, data: Dict[str, Any], secret: str) -> str:
        """Generate HMAC for request validation."""
        data_str = json.dumps(data, sort_keys=True)
        return hmac.new(secret.encode(), data_str.encode(), hashlib.sha256).hexdigest()


# Create singleton instance
encryption_manager = EncryptionManager()
