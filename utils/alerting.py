from typing import Dict, List, Optional, Callable
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class AlertThreshold:
    """Configuration for alert thresholds."""
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # seconds to maintain threshold before alerting
    cooldown: int  # seconds to wait before sending another alert

@dataclass
class AlertConfig:
    """Configuration for alert destinations."""
    email: Optional[Dict] = None  # {smtp_server, port, username, password, recipients}
    webhook: Optional[str] = None
    slack: Optional[str] = None  # Slack webhook URL

class SystemAlertManager:
    """Manages system-level alerts based on metric thresholds."""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_history: List[Dict] = []
        
        # Initialize default thresholds
        self.add_threshold(AlertThreshold(
            metric="cpu_usage",
            threshold=90.0,
            operator=">=",
            duration=300,  # 5 minutes
            cooldown=3600  # 1 hour
        ))
        
        self.add_threshold(AlertThreshold(
            metric="memory_usage",
            threshold=85.0,
            operator=">=",
            duration=300,
            cooldown=3600
        ))
        
        self.add_threshold(AlertThreshold(
            metric="disk_usage",
            threshold=90.0,
            operator=">=",
            duration=300,
            cooldown=3600
        ))
    
    def add_threshold(self, threshold: AlertThreshold):
        """Add a new alert threshold."""
        self.thresholds[threshold.metric] = threshold
    
    def check_metric(self, metric: str, value: float) -> bool:
        """Check if a metric value triggers an alert."""
        if metric not in self.thresholds:
            return False
            
        threshold = self.thresholds[metric]
        now = datetime.now()
        
        # Check cooldown
        if metric in self.last_alert_time:
            if (now - self.last_alert_time[metric]).total_seconds() < threshold.cooldown:
                return False
        
        # Check threshold
        if threshold.operator == ">":
            triggered = value > threshold.threshold
        elif threshold.operator == ">=":
            triggered = value >= threshold.threshold
        elif threshold.operator == "<":
            triggered = value < threshold.threshold
        elif threshold.operator == "<=":
            triggered = value <= threshold.threshold
        elif threshold.operator == "==":
            triggered = value == threshold.threshold
        else:
            return False
            
        if triggered:
            self.last_alert_time[metric] = now
            self._send_alert(metric, value, threshold)
            return True
            
        return False
    
    def _send_alert(self, metric: str, value: float, threshold: AlertThreshold):
        """Send alerts through configured channels."""
        message = f"ALERT: {metric} is {value} (threshold: {threshold.operator} {threshold.threshold})"
        
        # Record in history
        alert_record = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "value": value,
            "threshold": threshold.threshold,
            "operator": threshold.operator
        }
        self.alert_history.append(alert_record)
        
        # Send email
        if self.config.email:
            self._send_email_alert(message)
        
        # Send webhook
        if self.config.webhook:
            self._send_webhook_alert(message)
        
        # Send Slack
        if self.config.slack:
            self._send_slack_alert(message)
    
    def _send_email_alert(self, message: str):
        """Send alert via email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email['username']
            msg['To'] = ", ".join(self.config.email['recipients'])
            msg['Subject'] = "System Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.config.email['smtp_server'], self.config.email['port']) as server:
                server.starttls()
                server.login(self.config.email['username'], self.config.email['password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, message: str):
        """Send alert via webhook."""
        try:
            requests.post(self.config.webhook, json={"message": message})
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
    
    def _send_slack_alert(self, message: str):
        """Send alert via Slack."""
        try:
            payload = {"text": message}
            requests.post(self.config.slack, json=payload)
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get recent alert history."""
        return self.alert_history[-limit:]

# Global alert manager instance
alert_manager: Optional[SystemAlertManager] = None

def init_alerting(config: AlertConfig) -> SystemAlertManager:
    """Initialize the system alert manager."""
    global alert_manager
    if alert_manager is None:
        alert_manager = SystemAlertManager(config)
    return alert_manager

def get_alert_manager() -> SystemAlertManager:
    """Get the global alert manager instance."""
    if alert_manager is None:
        raise RuntimeError("Alerting not initialized. Call init_alerting first.")
    return alert_manager 