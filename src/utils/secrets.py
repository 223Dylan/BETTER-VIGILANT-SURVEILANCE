"""
Secrets management module for handling sensitive information.
"""
import os
from typing import Optional
from dotenv import load_dotenv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SecretsManager:
    """Manages application secrets and sensitive information."""
    
    def __init__(self):
        """Initialize the secrets manager."""
        load_dotenv()
        self._secrets = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from environment variables."""
        self._secrets = {
            'API_KEY_ADMIN': os.getenv('API_KEY_ADMIN'),
            'API_KEY_USER': os.getenv('API_KEY_USER'),
            'API_KEY_VIEWER': os.getenv('API_KEY_VIEWER'),
            'REDIS_URL': os.getenv('REDIS_URL'),
            'ELASTICSEARCH_URL': os.getenv('ELASTICSEARCH_URL'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'SMTP_SERVER': os.getenv('SMTP_SERVER'),
            'SMTP_PORT': os.getenv('SMTP_PORT'),
            'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
            'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
            'ALERT_EMAIL_RECIPIENTS': os.getenv('ALERT_EMAIL_RECIPIENTS'),
            'WEBHOOK_URL': os.getenv('WEBHOOK_URL'),
            'SLACK_WEBHOOK': os.getenv('SLACK_WEBHOOK')
        }

    def get(self, key, default=None):
        """Get a secret value by key."""
        return self._secrets.get(key, default)
    
    def get_all(self):
        """Get all secrets."""
        return self._secrets.copy()

    def validate_secrets(self) -> bool:
        """Validate that all required secrets are present"""
        # Core required secrets
        required_secrets = [
            'API_KEY_ADMIN', 
            'API_KEY_USER', 
            'API_KEY_VIEWER', 
            'REDIS_URL', 
            'ELASTICSEARCH_URL', 
            'LOG_LEVEL'
        ]
        
        # Optional secrets (for alerting)
        optional_secrets = [
            'SMTP_SERVER',
            'SMTP_PORT',
            'SMTP_USERNAME',
            'SMTP_PASSWORD',
            'ALERT_EMAIL_RECIPIENTS',
            'WEBHOOK_URL',
            'SLACK_WEBHOOK'
        ]
        
        # Check required secrets
        missing_required = [secret for secret in required_secrets if not self._secrets.get(secret)]
        if missing_required:
            logger.error(f"Missing required secrets: {', '.join(missing_required)}")
            return False
            
        # Log missing optional secrets
        missing_optional = [secret for secret in optional_secrets if not self._secrets.get(secret)]
        if missing_optional:
            logger.info(f"Optional secrets not configured: {', '.join(missing_optional)}")
            
        return True

# Create a singleton instance
secrets_manager = SecretsManager() 