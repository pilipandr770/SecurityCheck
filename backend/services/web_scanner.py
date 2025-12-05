"""
Сканер веб-сайтов
Проверка SSL, заголовков безопасности, HTML, cookies, HTTP методов
"""

import ssl
import socket
import requests
from urllib.parse import urlparse
from datetime import datetime
import OpenSSL
from bs4 import BeautifulSoup


class WebScanner:
    """Сканер безопасности веб-сайтов"""
    
    def __init__(self, url, timeout=30):
        """
        Инициализация сканера
        
        Args:
            url: URL для сканирования
            timeout: Таймаут запросов в секундах
        """
        self.url = url
        self.timeout = timeout
        self.parsed_url = urlparse(url)
        self.domain = self.parsed_url.netloc
        self.results = []
        self._html_content = None
        self._response = None
    
    def get_page_content(self):
        """Получить содержимое страницы"""
        if self._html_content is None:
            try:
                response = requests.get(self.url, timeout=self.timeout, allow_redirects=True)
                self._html_content = response.text
                self._response = response
            except Exception as e:
                self._html_content = ''
        return self._html_content
    
    def check_ssl_certificate(self):
        """Проверка SSL/TLS сертификата"""
        results = []
        
        if self.parsed_url.scheme != 'https':
            results.append({
                'category': 'ssl',
                'title': 'HTTPS не используется',
                'description': 'Сайт использует небезопасный HTTP протокол',
                'severity': 'high',
                'evidence': f'URL: {self.url}',
                'raw_data': {'protocol': 'http'}
            })
            return results
        
        try:
            # Получаем сертификат
            hostname = self.domain
            port = 443
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_bin = ssock.getpeercert(binary_form=True)
                    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)
                    
                    # Проверяем срок действия
                    expires = datetime.strptime(cert.get_notAfter().decode('utf-8'), '%Y%m%d%H%M%SZ')
                    days_until_expire = (expires - datetime.utcnow()).days
                    
                    if days_until_expire < 0:
                        results.append({
                            'category': 'ssl',
                            'title': 'SSL сертификат истёк',
                            'description': f'Сертификат истёк {abs(days_until_expire)} дней назад',
                            'severity': 'critical',
                            'evidence': f'Дата истечения: {expires}',
                            'raw_data': {'expires': expires.isoformat(), 'days': days_until_expire}
                        })
                    elif days_until_expire < 30:
                        results.append({
                            'category': 'ssl',
                            'title': 'SSL сертификат скоро истечёт',
                            'description': f'Сертификат истекает через {days_until_expire} дней',
                            'severity': 'medium',
                            'evidence': f'Дата истечения: {expires}',
                            'raw_data': {'expires': expires.isoformat(), 'days': days_until_expire}
                        })
                    # Не добавляем результат для валидного сертификата - это не уязвимость
                    # else:
                    #     pass  # Валидный сертификат - не показываем пользователю
                    
                    # Проверяем версию TLS
                    tls_version = ssock.version()
                    if tls_version in ['TLSv1', 'TLSv1.1', 'SSLv3', 'SSLv2']:
                        results.append({
                            'category': 'ssl',
                            'title': 'Устаревшая версия TLS/SSL',
                            'description': f'Используется {tls_version}. Рекомендуется TLSv1.2 или выше',
                            'severity': 'high',
                            'evidence': f'Версия: {tls_version}',
                            'raw_data': {'tls_version': tls_version}
                        })
                    
        except ssl.SSLError as e:
            results.append({
                'category': 'ssl',
                'title': 'Ошибка SSL сертификата',
                'description': f'Проблема с SSL: {str(e)}',
                'severity': 'critical',
                'evidence': str(e),
                'raw_data': {'error': str(e)}
            })
        except Exception as e:
            results.append({
                'category': 'ssl',
                'title': 'Не удалось проверить SSL',
                'description': f'Ошибка проверки: {str(e)}',
                'severity': 'medium',
                'raw_data': {'error': str(e)}
            })
        
        return results
    
    def check_security_headers(self):
        """Проверка заголовков безопасности"""
        results = []
        
        try:
            if self._response is None:
                self._response = requests.get(self.url, timeout=self.timeout, allow_redirects=True)
            
            headers = {k.lower(): v for k, v in self._response.headers.items()}
            
            # Strict-Transport-Security (HSTS)
            if 'strict-transport-security' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует HSTS заголовок',
                    'description': 'Strict-Transport-Security заголовок защищает от downgrade атак',
                    'severity': 'medium',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'Strict-Transport-Security', 'present': False}
                })
            
            # X-Content-Type-Options
            if 'x-content-type-options' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует X-Content-Type-Options',
                    'description': 'Этот заголовок защищает от MIME type sniffing',
                    'severity': 'medium',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'X-Content-Type-Options', 'present': False}
                })
            
            # X-Frame-Options
            if 'x-frame-options' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует X-Frame-Options',
                    'description': 'Этот заголовок защищает от clickjacking атак',
                    'severity': 'medium',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'X-Frame-Options', 'present': False}
                })
            
            # Content-Security-Policy
            if 'content-security-policy' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует Content-Security-Policy',
                    'description': 'CSP защищает от XSS и других инъекций кода',
                    'severity': 'high',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'Content-Security-Policy', 'present': False}
                })
            
            # X-XSS-Protection
            if 'x-xss-protection' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует X-XSS-Protection',
                    'description': 'Заголовок включает XSS фильтр браузера',
                    'severity': 'low',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'X-XSS-Protection', 'present': False}
                })
            
            # Permissions-Policy / Feature-Policy
            if 'permissions-policy' not in headers and 'feature-policy' not in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Отсутствует Permissions-Policy',
                    'description': 'Заголовок контролирует доступ к API браузера',
                    'severity': 'low',
                    'evidence': 'Заголовок не найден',
                    'raw_data': {'header': 'Permissions-Policy', 'present': False}
                })
            
            # Server header (information disclosure)
            if 'server' in headers:
                results.append({
                    'category': 'headers',
                    'title': 'Раскрытие информации о сервере',
                    'description': f'Server заголовок раскрывает информацию: {headers["server"]}',
                    'severity': 'low',
                    'evidence': f'Server: {headers["server"]}',
                    'raw_data': {'header': 'Server', 'value': headers['server']}
                })
            
        except Exception as e:
            results.append({
                'category': 'headers',
                'title': 'Не удалось проверить заголовки',
                'description': f'Ошибка: {str(e)}',
                'severity': 'low',
                'raw_data': {'error': str(e)}
            })
        
        return results
    
    def check_html_issues(self):
        """Анализ HTML на потенциальные проблемы"""
        results = []
        
        try:
            html = self.get_page_content()
            if not html:
                return results
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Inline скрипты (потенциальный XSS)
            inline_scripts = soup.find_all('script', src=False)
            if len(inline_scripts) > 5:
                results.append({
                    'category': 'html',
                    'title': 'Много inline скриптов',
                    'description': f'Найдено {len(inline_scripts)} inline скриптов. Рекомендуется использовать внешние файлы',
                    'severity': 'low',
                    'evidence': f'Количество: {len(inline_scripts)}',
                    'raw_data': {'count': len(inline_scripts)}
                })
            
            # Inline стили
            inline_styles = soup.find_all(style=True)
            if len(inline_styles) > 10:
                results.append({
                    'category': 'html',
                    'title': 'Много inline стилей',
                    'description': f'Найдено {len(inline_styles)} элементов с inline стилями',
                    'severity': 'info',
                    'raw_data': {'count': len(inline_styles)}
                })
            
            # Комментарии с потенциально чувствительной информацией
            comments = soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text)
            for comment in comments:
                comment_text = str(comment).lower()
                if any(keyword in comment_text for keyword in ['password', 'token', 'api', 'key', 'secret']):
                    results.append({
                        'category': 'html',
                        'title': 'Потенциально чувствительная информация в комментариях',
                        'description': 'Найдены комментарии с возможно чувствительными данными',
                        'severity': 'medium',
                        'evidence': 'Комментарий содержит ключевые слова',
                        'raw_data': {'comment': comment_text[:100]}
                    })
                    break
            
            # Устаревшие библиотеки
            scripts = soup.find_all('script', src=True)
            for script in scripts:
                src = script.get('src', '').lower()
                if 'jquery' in src:
                    # Пытаемся определить версию
                    if 'jquery-1.' in src or 'jquery/1.' in src:
                        results.append({
                            'category': 'html',
                            'title': 'Устаревшая версия jQuery',
                            'description': 'Используется jQuery 1.x с известными уязвимостями',
                            'severity': 'high',
                            'evidence': f'Скрипт: {src}',
                            'raw_data': {'src': src}
                        })
                    elif 'jquery-2.' in src or 'jquery/2.' in src:
                        results.append({
                            'category': 'html',
                            'title': 'Устаревшая версия jQuery',
                            'description': 'Используется jQuery 2.x, рекомендуется обновление',
                            'severity': 'medium',
                            'evidence': f'Скрипт: {src}',
                            'raw_data': {'src': src}
                        })
            
        except Exception as e:
            results.append({
                'category': 'html',
                'title': 'Не удалось проанализировать HTML',
                'description': f'Ошибка: {str(e)}',
                'severity': 'low',
                'raw_data': {'error': str(e)}
            })
        
        return results
    
    def check_cookies(self):
        """Анализ cookies на безопасность"""
        results = []
        
        try:
            if self._response is None:
                self._response = requests.get(self.url, timeout=self.timeout, allow_redirects=True)
            
            cookies = self._response.cookies
            
            for cookie in cookies:
                issues = []
                
                # Проверяем флаг Secure
                if not cookie.secure and self.parsed_url.scheme == 'https':
                    issues.append('отсутствует флаг Secure')
                
                # Проверяем флаг HttpOnly
                if not cookie.has_nonstandard_attr('HttpOnly'):
                    issues.append('отсутствует флаг HttpOnly')
                
                # Проверяем SameSite
                if not cookie.has_nonstandard_attr('SameSite'):
                    issues.append('отсутствует атрибут SameSite')
                
                if issues:
                    results.append({
                        'category': 'cookies',
                        'title': f'Небезопасная cookie: {cookie.name}',
                        'description': f'Cookie имеет проблемы: {", ".join(issues)}',
                        'severity': 'medium',
                        'evidence': f'Cookie: {cookie.name}',
                        'raw_data': {
                            'name': cookie.name,
                            'secure': cookie.secure,
                            'issues': issues
                        }
                    })
            
        except Exception as e:
            pass  # Cookies не критичны для сканирования
        
        return results
    
    def check_http_methods(self):
        """Проверка доступных HTTP методов"""
        results = []
        
        try:
            # Проверяем OPTIONS
            response = requests.options(self.url, timeout=10)
            allowed_methods = response.headers.get('Allow', '').upper()
            
            dangerous_methods = ['PUT', 'DELETE', 'TRACE', 'CONNECT']
            found_dangerous = [m for m in dangerous_methods if m in allowed_methods]
            
            if found_dangerous:
                results.append({
                    'category': 'http',
                    'title': 'Опасные HTTP методы включены',
                    'description': f'Доступны методы: {", ".join(found_dangerous)}',
                    'severity': 'high',
                    'evidence': f'Allow: {allowed_methods}',
                    'raw_data': {'methods': found_dangerous}
                })
            
        except Exception:
            pass  # Не все серверы отвечают на OPTIONS
        
        return results
    
    def run_full_scan(self):
        """Запустить полное сканирование"""
        all_results = []
        
        all_results.extend(self.check_ssl_certificate())
        all_results.extend(self.check_security_headers())
        all_results.extend(self.check_html_issues())
        all_results.extend(self.check_cookies())
        all_results.extend(self.check_http_methods())
        
        return all_results
