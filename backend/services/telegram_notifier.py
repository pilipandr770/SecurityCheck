"""
Telegram notification service for contact form submissions
"""
import requests
import os
from typing import Dict
from flask import current_app


class TelegramNotifier:
    """Service to send notifications via Telegram bot"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    def send_contact_form(self, data: Dict) -> bool:
        """
        Send contact form submission to Telegram
        
        Args:
            data: Form data containing name, email, phone, project_type, message
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_configured():
            current_app.logger.warning('Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID')
            return False
        
        # Format message
        message = f"""
🔔 <b>Neue Kontaktanfrage</b>

👤 <b>Name:</b> {data.get('name', 'N/A')}
📧 <b>E-Mail:</b> {data.get('email', 'N/A')}
📞 <b>Telefon:</b> {data.get('phone', 'N/A')}
🎯 <b>Projekttyp:</b> {self._format_project_type(data.get('project_type', 'N/A'))}

💬 <b>Nachricht:</b>
{data.get('message', 'Keine Nachricht')}

⏰ Von: Portfolio-Seite
"""
        
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                current_app.logger.info(f'Telegram notification sent for {data.get("email")}')
                return True
            else:
                current_app.logger.error(f'Telegram API error: {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Failed to send Telegram notification: {e}')
            return False
    
    def send_scan_alert(self, domain: str, critical_issues: int, high_issues: int) -> bool:
        """
        Send security scan alert to Telegram
        
        Args:
            domain: Scanned domain
            critical_issues: Number of critical issues found
            high_issues: Number of high severity issues
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_configured():
            return False
        
        if critical_issues == 0 and high_issues == 0:
            return False  # Only send alerts for serious issues
        
        message = f"""
🚨 <b>Sicherheitswarnung</b>

🌐 <b>Domain:</b> {domain}
❌ <b>Kritische Probleme:</b> {critical_issues}
⚠️ <b>Hohe Probleme:</b> {high_issues}

➡️ Überprüfen Sie die Details im Dashboard
"""
        
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f'Failed to send scan alert: {e}')
            return False
    
    def _format_project_type(self, project_type: str) -> str:
        """Format project type to German"""
        types = {
            'website': 'Unternehmenswebsite',
            'ecommerce': 'Online-Shop',
            'webapp': 'Webanwendung',
            'audit': 'Sicherheitsaudit',
            'other': 'Sonstiges'
        }
        return types.get(project_type, project_type)
