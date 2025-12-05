"""
Анализатор доменов
WHOIS, DNS, репутация, история
"""

import dns.resolver
import whois
import requests
from datetime import datetime
from urllib.parse import urlparse


class DomainAnalyzer:
    """Анализатор доменов и DNS"""
    
    def __init__(self, ipqs_api_key=None):
        """
        Инициализация
        
        Args:
            ipqs_api_key: IPQualityScore API ключ
        """
        self.ipqs_api_key = ipqs_api_key
    
    def run_full_analysis(self, domain):
        """
        Полный анализ домена
        
        Args:
            domain: Доменное имя
            
        Returns:
            dict: Результаты анализа
        """
        results = {
            'domain': domain,
            'whois': self.get_whois_info(domain),
            'dns': self.get_dns_records(domain),
            'email_security': self.check_email_security(domain),
            'wayback': self.get_wayback_history(domain),
            'reputation_score': None,
            'domain_age_days': None
        }
        
        # Возраст домена
        if results['whois'].get('created_date'):
            created = results['whois']['created_date']
            if isinstance(created, datetime):
                results['domain_age_days'] = (datetime.now() - created).days
        
        # Репутация IP
        if results['dns'].get('A'):
            ip = results['dns']['A'][0] if results['dns']['A'] else None
            if ip:
                results['ip_reputation'] = self.get_ip_reputation(ip)
                
                # Общая репутация на основе разных факторов
                results['reputation_score'] = self.calculate_reputation_score(results)
        
        return results
    
    def get_whois_info(self, domain):
        """
        Получить WHOIS информацию
        
        Args:
            domain: Доменное имя
            
        Returns:
            dict: WHOIS данные
        """
        info = {}
        
        try:
            w = whois.whois(domain)
            
            # Регистратор
            info['registrar'] = w.registrar if hasattr(w, 'registrar') else None
            
            # Владелец (может быть скрыт)
            info['registrant'] = w.name if hasattr(w, 'name') else None
            
            # Даты
            if hasattr(w, 'creation_date'):
                creation = w.creation_date
                if isinstance(creation, list):
                    creation = creation[0]
                info['created_date'] = creation
            
            if hasattr(w, 'expiration_date'):
                expiry = w.expiration_date
                if isinstance(expiry, list):
                    expiry = expiry[0]
                info['expiry_date'] = expiry
            
            if hasattr(w, 'updated_date'):
                updated = w.updated_date
                if isinstance(updated, list):
                    updated = updated[0]
                info['updated_date'] = updated
            
            # Nameservers
            if hasattr(w, 'name_servers'):
                ns = w.name_servers
                if ns:
                    info['nameservers'] = [str(n).lower() for n in ns] if isinstance(ns, list) else [str(ns).lower()]
        
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def get_dns_records(self, domain):
        """
        Получить DNS записи
        
        Args:
            domain: Доменное имя
            
        Returns:
            dict: DNS записи
        """
        records = {
            'A': [],
            'AAAA': [],
            'MX': [],
            'TXT': [],
            'NS': [],
            'CNAME': []
        }
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME']
        
        for record_type in record_types:
            try:
                answers = resolver.resolve(domain, record_type)
                
                for rdata in answers:
                    if record_type == 'MX':
                        records[record_type].append({
                            'priority': rdata.preference,
                            'exchange': str(rdata.exchange)
                        })
                    elif record_type == 'TXT':
                        records[record_type].append(str(rdata).strip('"'))
                    else:
                        records[record_type].append(str(rdata))
            
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                pass
            except Exception:
                pass
        
        return records
    
    def check_email_security(self, domain):
        """
        Проверка безопасности email (SPF, DKIM, DMARC)
        
        Args:
            domain: Доменное имя
            
        Returns:
            dict: Статус email безопасности
        """
        security = {
            'has_spf': False,
            'has_dkim': False,
            'has_dmarc': False,
            'spf_record': None,
            'dmarc_record': None,
            'score': 0
        }
        
        try:
            # Проверка SPF
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            
            txt_records = resolver.resolve(domain, 'TXT')
            for rdata in txt_records:
                txt = str(rdata).strip('"')
                if txt.startswith('v=spf1'):
                    security['has_spf'] = True
                    security['spf_record'] = txt
                    security['score'] += 35
                    break
            
            # Проверка DMARC
            try:
                dmarc_records = resolver.resolve(f'_dmarc.{domain}', 'TXT')
                for rdata in dmarc_records:
                    txt = str(rdata).strip('"')
                    if txt.startswith('v=DMARC1'):
                        security['has_dmarc'] = True
                        security['dmarc_record'] = txt
                        security['score'] += 35
                        break
            except Exception:
                pass
            
            # Проверка DKIM (сложнее, так как нужен селектор)
            # Проверяем распространённые селекторы
            common_selectors = ['default', 'google', 'k1', 's1', 'mail', 'smtp']
            for selector in common_selectors:
                try:
                    dkim_query = f'{selector}._domainkey.{domain}'
                    dkim_records = resolver.resolve(dkim_query, 'TXT')
                    if dkim_records:
                        security['has_dkim'] = True
                        security['score'] += 30
                        break
                except Exception:
                    continue
        
        except Exception:
            pass
        
        return security
    
    def get_wayback_history(self, domain):
        """
        Получить историю с Wayback Machine
        
        Args:
            domain: Доменное имя
            
        Returns:
            dict: История снимков
        """
        history = {
            'snapshots': 0,
            'first_capture': None,
            'last_capture': None
        }
        
        try:
            url = f'http://archive.org/wayback/available?url={domain}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('archived_snapshots'):
                    closest = data['archived_snapshots'].get('closest', {})
                    
                    if closest.get('available'):
                        # Для получения количества снимков нужен другой API endpoint
                        # Упрощённая версия
                        timestamp = closest.get('timestamp')
                        if timestamp:
                            # Формат: YYYYMMDDhhmmss
                            year = int(timestamp[:4])
                            month = int(timestamp[4:6])
                            day = int(timestamp[6:8])
                            history['first_capture'] = datetime(year, month, day)
                            history['last_capture'] = datetime(year, month, day)
                            history['snapshots'] = 1  # Упрощение
        
        except Exception:
            pass
        
        return history
    
    def get_ip_reputation(self, ip):
        """
        Получить репутацию IP адреса
        
        Args:
            ip: IP адрес
            
        Returns:
            dict: Информация о репутации
        """
        reputation = {
            'ip': ip,
            'is_vpn': False,
            'is_proxy': False,
            'is_datacenter': False,
            'country': None,
            'fraud_score': 0
        }
        
        if not self.ipqs_api_key:
            # Используем бесплатный сервис ip-api.com
            try:
                response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    reputation['country'] = data.get('country')
                    reputation['isp'] = data.get('isp')
                    
                    # Простая эвристика
                    isp = data.get('isp', '').lower()
                    if any(keyword in isp for keyword in ['datacenter', 'hosting', 'server', 'cloud']):
                        reputation['is_datacenter'] = True
            except Exception:
                pass
        else:
            # IPQualityScore API
            try:
                url = f'https://ipqualityscore.com/api/json/ip/{self.ipqs_api_key}/{ip}'
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    reputation['fraud_score'] = data.get('fraud_score', 0)
                    reputation['is_vpn'] = data.get('vpn', False)
                    reputation['is_proxy'] = data.get('proxy', False)
                    reputation['country'] = data.get('country_code')
                    reputation['isp'] = data.get('ISP')
            except Exception:
                pass
        
        return reputation
    
    def calculate_reputation_score(self, results):
        """
        Рассчитать общую репутацию домена (0-100)
        
        Args:
            results: Результаты анализа
            
        Returns:
            int: Репутация (100 = отлично, 0 = плохо)
        """
        score = 50  # Базовый балл
        
        # Возраст домена
        age = results.get('domain_age_days')
        if age:
            if age > 365:
                score += 20
            elif age > 180:
                score += 10
            elif age < 30:
                score -= 20
        
        # Email безопасность
        email_sec = results.get('email_security', {})
        score += email_sec.get('score', 0) // 5  # Макс +20
        
        # IP репутация
        ip_rep = results.get('ip_reputation', {})
        if ip_rep.get('fraud_score', 0) > 75:
            score -= 30
        elif ip_rep.get('fraud_score', 0) > 50:
            score -= 15
        
        if ip_rep.get('is_vpn') or ip_rep.get('is_proxy'):
            score -= 10
        
        # История Wayback
        wayback = results.get('wayback', {})
        if wayback.get('snapshots', 0) > 0:
            score += 5
        
        return max(0, min(100, score))
