"""
Проверка ссылок на безопасность
Интеграция с VirusTotal, Google Safe Browsing, URLhaus
"""

import requests
import dns.resolver
from urllib.parse import urlparse
from datetime import datetime, timedelta
import whois


class LinkChecker:
    """Проверка ссылок на вредоносность и фишинг"""
    
    def __init__(self, vt_api_key=None, gsb_api_key=None):
        """
        Инициализация
        
        Args:
            vt_api_key: VirusTotal API ключ
            gsb_api_key: Google Safe Browsing API ключ
        """
        self.vt_api_key = vt_api_key
        self.gsb_api_key = gsb_api_key
        self.shortened_domains = [
            'bit.ly', 'tinyurl.com', 'ow.ly', 'goo.gl', 't.co',
            'short.link', 'cutt.ly', 'rebrandly.com'
        ]
    
    def run_full_check(self, url):
        """
        Полная проверка URL
        
        Args:
            url: URL для проверки
            
        Returns:
            dict: Результаты проверки
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        results = {
            'original_url': url,
            'final_url': url,
            'domain': domain,
            'is_shortened': self.is_shortened_url(domain),
            'is_dangerous': False,
            'is_suspicious': False,
            'confidence': 0,
            'reasons': []
        }
        
        # Разворачиваем сокращённый URL
        if results['is_shortened']:
            try:
                final_url = self.expand_shortened_url(url)
                results['final_url'] = final_url
                results['reasons'].append('Сокращённый URL развёрнут')
                parsed = urlparse(final_url)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                results['domain'] = domain
            except Exception:
                results['reasons'].append('Не удалось развернуть сокращённый URL')
        
        # Проверка через VirusTotal
        if self.vt_api_key:
            vt_result = self.check_virustotal(results['final_url'])
            results['virustotal'] = vt_result
            
            # ЛОГИРОВАНИЕ для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"VirusTotal result for {results['final_url']}: {vt_result}")
            
            if vt_result.get('malicious', 0) > 0:
                results['is_dangerous'] = True
                results['reasons'].append(f'VirusTotal: {vt_result["malicious"]} антивирусов обнаружили угрозу')
            elif vt_result.get('suspicious', 0) > 0:
                results['is_suspicious'] = True
                results['reasons'].append(f'VirusTotal: {vt_result["suspicious"]} антивирусов отметили как подозрительное')
        
        # Проверка через Google Safe Browsing
        if self.gsb_api_key:
            gsb_result = self.check_google_safe_browsing(results['final_url'])
            results['google_safebrowsing'] = gsb_result
            
            if gsb_result.get('is_dangerous'):
                results['is_dangerous'] = True
                results['reasons'].append(f'Google Safe Browsing: {gsb_result["threat_type"]}')
        
        # Проверка через URLhaus
        urlhaus_result = self.check_urlhaus(results['final_url'])
        results['urlhaus'] = urlhaus_result
        
        if urlhaus_result.get('is_malicious'):
            results['is_dangerous'] = True
            results['reasons'].append('URLhaus: URL в базе вредоносных')
        
        # Проверка SSL
        ssl_valid = self.check_ssl_validity(results['final_url'])
        results['ssl_valid'] = ssl_valid
        
        # Помечаем как подозрительное ТОЛЬКО если SSL явно невалидный (ssl.SSLError)
        # None означает что не смогли проверить - это НЕ проблема безопасности
        if ssl_valid is False and parsed.scheme == 'https':
            results['is_suspicious'] = True
            results['reasons'].append('SSL сертификат недействителен или истёк')
        
        # Возраст домена
        domain_age = self.get_domain_age(domain)
        results['domain_age_days'] = domain_age
        
        if domain_age is not None and domain_age < 30:
            results['is_suspicious'] = True
            results['reasons'].append(f'Новый домен (возраст: {domain_age} дней)')
        
        # Расчёт уверенности
        results['confidence'] = self.calculate_confidence(results)
        
        return results
    
    def is_shortened_url(self, domain):
        """Проверить является ли URL сокращённым"""
        return any(shortened in domain for shortened in self.shortened_domains)
    
    def expand_shortened_url(self, url):
        """Развернуть сокращённый URL"""
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.url
        except Exception:
            return url
    
    def check_virustotal(self, url):
        """
        Проверка через VirusTotal API
        
        Returns:
            dict: Результаты проверки
        """
        if not self.vt_api_key:
            return {'error': 'API key not provided'}
        
        try:
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            
            headers = {'x-apikey': self.vt_api_key}
            response = requests.get(
                f'https://www.virustotal.com/api/v3/urls/{url_id}',
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'harmless': stats.get('harmless', 0),
                    'undetected': stats.get('undetected', 0),
                    'total': sum(stats.values())
                }
            elif response.status_code == 404:
                # URL не найден в базе, отправляем на сканирование
                return self.submit_url_to_virustotal(url)
            
        except Exception as e:
            return {'error': str(e)}
        
        return {'error': 'Unknown error'}
    
    def submit_url_to_virustotal(self, url):
        """Отправить URL на сканирование в VirusTotal"""
        try:
            headers = {'x-apikey': self.vt_api_key}
            data = {'url': url}
            
            response = requests.post(
                'https://www.virustotal.com/api/v3/urls',
                headers=headers,
                data=data,
                timeout=15
            )
            
            if response.status_code == 200:
                return {
                    'status': 'queued',
                    'message': 'URL отправлен на сканирование',
                    'malicious': 0,
                    'suspicious': 0
                }
        except Exception:
            pass
        
        return {'error': 'Failed to submit'}
    
    def check_google_safe_browsing(self, url):
        """
        Проверка через Google Safe Browsing API
        
        Returns:
            dict: Результаты проверки
        """
        if not self.gsb_api_key:
            return {'error': 'API key not provided'}
        
        try:
            api_url = f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.gsb_api_key}'
            
            payload = {
                'client': {
                    'clientId': 'securitycheck',
                    'clientVersion': '1.0.0'
                },
                'threatInfo': {
                    'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE', 'POTENTIALLY_HARMFUL_APPLICATION'],
                    'platformTypes': ['ANY_PLATFORM'],
                    'threatEntryTypes': ['URL'],
                    'threatEntries': [{'url': url}]
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                if matches:
                    threat_type = matches[0].get('threatType', 'UNKNOWN')
                    return {
                        'is_dangerous': True,
                        'threat_type': threat_type,
                        'platform': matches[0].get('platformType', 'UNKNOWN')
                    }
                else:
                    return {'is_dangerous': False}
        
        except Exception as e:
            return {'error': str(e)}
        
        return {'is_dangerous': False}
    
    def check_urlhaus(self, url):
        """
        Проверка через URLhaus API (бесплатный)
        
        Returns:
            dict: Результаты проверки
        """
        try:
            response = requests.post(
                'https://urlhaus-api.abuse.ch/v1/url/',
                data={'url': url},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('query_status') == 'ok':
                    return {
                        'is_malicious': True,
                        'threat': data.get('threat', 'unknown'),
                        'tags': data.get('tags', []),
                        'status': data.get('url_status', 'unknown')
                    }
                else:
                    return {'is_malicious': False}
        
        except Exception:
            pass
        
        return {'is_malicious': False}
    
    def check_ssl_validity(self, url):
        """Проверить валидность SSL сертификата"""
        parsed = urlparse(url)
        
        if parsed.scheme != 'https':
            return None  # Не HTTPS - не проверяем
        
        try:
            import ssl
            import socket
            
            # Убираем порт если есть
            hostname = parsed.netloc
            if ':' in hostname:
                hostname = hostname.split(':')[0]
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Проверяем что сертификат не истёк
                    cert = ssock.getpeercert()
                    return True
        except ssl.SSLError as e:
            # Реальная проблема с SSL сертификатом
            return False
        except (socket.timeout, socket.error, ConnectionRefusedError):
            # Проблема с соединением - не значит что SSL плохой
            # Домен может быть за CDN/firewall
            return None
        except Exception:
            # Неизвестная ошибка - лучше не пугать пользователя
            return None
    
    def get_domain_age(self, domain):
        """Получить возраст домена в днях"""
        try:
            w = whois.whois(domain)
            
            if w.creation_date:
                if isinstance(w.creation_date, list):
                    creation_date = w.creation_date[0]
                else:
                    creation_date = w.creation_date
                
                if isinstance(creation_date, datetime):
                    age = (datetime.now() - creation_date).days
                    return age
        except Exception:
            pass
        
        return None
    
    def calculate_confidence(self, results):
        """
        Рассчитать уверенность в результатах (0-100)
        
        Args:
            results: Результаты проверки
            
        Returns:
            int: Процент уверенности
        """
        confidence = 50  # Базовая уверенность
        
        # Увеличиваем если есть результаты от надёжных источников
        if results.get('virustotal'):
            if 'error' not in results['virustotal']:
                confidence += 20
        
        if results.get('google_safebrowsing'):
            if 'error' not in results['google_safebrowsing']:
                confidence += 20
        
        if results.get('urlhaus'):
            confidence += 10
        
        # Уменьшаем если не все проверки доступны
        if not self.vt_api_key:
            confidence -= 15
        
        if not self.gsb_api_key:
            confidence -= 15
        
        return max(0, min(100, confidence))
