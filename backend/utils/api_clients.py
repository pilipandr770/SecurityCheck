"""
API клиенты для внешних сервисов
"""

import os
import requests
from typing import Dict, Any, Optional


class VirusTotalClient:
    """Клиент для VirusTotal API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = 'https://www.virustotal.com/api/v3'
        self.headers = {'x-apikey': self.api_key}
    
    def scan_url(self, url: str) -> Dict[str, Any]:
        """Сканировать URL"""
        endpoint = f'{self.base_url}/urls/{url}'
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def scan_file_hash(self, file_hash: str) -> Dict[str, Any]:
        """Проверить файл по хешу"""
        endpoint = f'{self.base_url}/files/{file_hash}'
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Загрузить файл на сканирование"""
        endpoint = f'{self.base_url}/files'
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(endpoint, headers=self.headers, files=files, timeout=60)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {'error': str(e)}


class GoogleSafeBrowsingClient:
    """Клиент для Google Safe Browsing API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_SAFE_BROWSING_KEY')
        self.base_url = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
    
    def check_url(self, url: str) -> Dict[str, Any]:
        """Проверить URL на угрозы"""
        payload = {
            'client': {
                'clientId': 'SecurityCheck',
                'clientVersion': '1.0'
            },
            'threatInfo': {
                'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE'],
                'platformTypes': ['ANY_PLATFORM'],
                'threatEntryTypes': ['URL'],
                'threatEntries': [{'url': url}]
            }
        }
        
        try:
            response = requests.post(
                f'{self.base_url}?key={self.api_key}',
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}


class URLhausClient:
    """Клиент для URLhaus API"""
    
    def __init__(self):
        self.base_url = 'https://urlhaus-api.abuse.ch/v1'
    
    def check_url(self, url: str) -> Dict[str, Any]:
        """Проверить URL в базе URLhaus"""
        endpoint = f'{self.base_url}/url/'
        
        try:
            response = requests.post(endpoint, data={'url': url}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}


class IPQualityScoreClient:
    """Клиент для IPQualityScore API (опционально)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('IPQUALITYSCORE_API_KEY')
        self.base_url = 'https://www.ipqualityscore.com/api/json/ip'
    
    def check_ip(self, ip_address: str) -> Dict[str, Any]:
        """Проверить репутацию IP"""
        if not self.api_key:
            return {'error': 'API key not configured'}
        
        endpoint = f'{self.base_url}/{self.api_key}/{ip_address}'
        
        try:
            response = requests.get(endpoint, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}


class WaybackMachineClient:
    """Клиент для Wayback Machine API"""
    
    def __init__(self):
        self.base_url = 'https://archive.org/wayback/available'
    
    def get_snapshots(self, url: str) -> Dict[str, Any]:
        """Получить снимки сайта из архива"""
        try:
            response = requests.get(self.base_url, params={'url': url}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
