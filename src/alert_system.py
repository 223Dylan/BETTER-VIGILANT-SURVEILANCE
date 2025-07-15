import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)


class AlertSystem:
    def __init__(self):
        self.alert_channels = {"email": self._send_email_alert, "log": self._log_alert}
        self.available_channels = self._initialize_channels()
        logger.info(
            f"Alert system initialized with available channels: {', '.join(self.available_channels)}"
        )

    def _initialize_channels(self) -> List[str]:
        """Initialize available alert channels."""
        available = ["log"]  # Log channel is always available

        # Check if email configuration exists
        if os.path.exists("config/email_config.json"):
            try:
                with open("config/email_config.json", "r") as f:
                    self.email_config = json.load(f)
                if all(
                    k in self.email_config
                    for k in ["smtp_server", "smtp_port", "username", "password"]
                ):
                    available.append("email")
            except Exception as e:
                logger.error(f"Failed to load email configuration: {str(e)}")

        return available

    def send_alert(
        self, message: str, level: str = "info", channels: Optional[List[str]] = None
    ) -> None:
        """Send an alert through specified channels."""
        if channels is None:
            channels = self.available_channels

        for channel in channels:
            if channel in self.alert_channels:
                try:
                    self.alert_channels[channel](message, level)
                except Exception as e:
                    logger.error(f"Failed to send alert through {channel}: {str(e)}")
            else:
                logger.warning(f"Alert channel {channel} not available")

    def _send_email_alert(self, message: str, level: str) -> None:
        """Send an email alert."""
        if "email" not in self.available_channels:
            logger.warning("Email alerts not configured")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["username"]
            msg["To"] = self.email_config["username"]  # Send to self for now
            msg["Subject"] = f"Alert: {level.upper()} - Shoplifting Detection System"

            body = f"""
            Alert Level: {level.upper()}
            Message: {message}
            
            This is an automated alert from the Shoplifting Detection System.
            """

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["username"], self.email_config["password"]
                )
                server.send_message(msg)

            logger.info(f"Email alert sent: {message}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")

    def _log_alert(self, message: str, level: str) -> None:
        """Log an alert message."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"ALERT: {message}")

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Alert system cleaned up")
