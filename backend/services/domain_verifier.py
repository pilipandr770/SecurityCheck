"""
Сервис верификации владения доменом
Проверяет подтверждение через verification.txt или meta tag
"""

import requests
import hashlib
import secrets
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Tuple, Optional


class DomainVerifier:
    """Верификатор владения доменом"""
    
    VERIFICATION_PREFIX = 'securitycheck-verification-'
    VERIFICATION_META_NAME = 'securitycheck-site-verification'
    
    @staticmethod
    def generate_verification_code(domain: str, user_id: int) -> str:
        """
        Генерирует уникальный код верификации для домена
        
        Args:
            domain: Доменное имя
            user_id: ID пользователя
            
        Returns:
            str: Код верификации
        """
        # Уникальный код на основе домена, пользователя и случайной соли
        salt = secrets.token_hex(16)
        raw = f"{domain}:{user_id}:{salt}"
        code = hashlib.sha256(raw.encode()).hexdigest()[:32]
        return f"{DomainVerifier.VERIFICATION_PREFIX}{code}"
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Извлекает доменное имя из URL
        
        Args:
            url: Полный URL
            
        Returns:
            str: Доменное имя
        """
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Убрать www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.lower()
    
    @staticmethod
    def verify_txt_file(url: str, verification_code: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Проверяет наличие verification.txt файла с кодом
        
        Args:
            url: URL сайта
            verification_code: Ожидаемый код верификации
            timeout: Таймаут запроса
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Попробуем оба варианта: с префиксом и без
            verification_urls = [
                f"{base_url}/{verification_code}.txt",
                f"{base_url}/securitycheck-verification.txt"
            ]
            
            for verification_url in verification_urls:
                try:
                    response = requests.get(
                        verification_url,
                        timeout=timeout,
                        allow_redirects=True,
                        headers={'User-Agent': 'SecurityCheck-Verifier/1.0'}
                    )
                    
                    if response.status_code == 200:
                        content = response.text.strip()
                        
                        # Проверить, содержит ли файл код
                        if verification_code in content:
                            return True, f"✅ Верификация успешна через {verification_url}"
                        
                except requests.RequestException:
                    continue
            
            return False, "❌ Файл верификации не найден. Загрузите файл в корень сайта."
            
        except Exception as e:
            return False, f"❌ Ошибка проверки: {str(e)}"
    
    @staticmethod
    def verify_meta_tag(url: str, verification_code: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Проверяет наличие meta тега с кодом верификации
        
        Args:
            url: URL сайта
            verification_code: Ожидаемый код верификации
            timeout: Таймаут запроса
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={'User-Agent': 'SecurityCheck-Verifier/1.0'}
            )
            
            if response.status_code != 200:
                return False, f"❌ Сайт недоступен (статус {response.status_code})"
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем meta тег
            meta_tag = soup.find('meta', attrs={'name': DomainVerifier.VERIFICATION_META_NAME})
            
            if not meta_tag:
                return False, "❌ Meta тег верификации не найден в <head>"
            
            content = meta_tag.get('content', '')
            
            if verification_code in content:
                return True, "✅ Верификация успешна через meta тег"
            else:
                return False, "❌ Код верификации в meta теге не совпадает"
                
        except requests.RequestException as e:
            return False, f"❌ Ошибка подключения: {str(e)}"
        except Exception as e:
            return False, f"❌ Ошибка парсинга: {str(e)}"
    
    @staticmethod
    def verify_domain(url: str, verification_code: str, timeout: int = 10) -> Tuple[bool, str, Optional[str]]:
        """
        Проверяет верификацию домена (пробует оба метода)
        
        Args:
            url: URL сайта
            verification_code: Код верификации
            timeout: Таймаут запроса
            
        Returns:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, метод верификации)
        """
        # Сначала пробуем TXT файл (быстрее)
        success, message = DomainVerifier.verify_txt_file(url, verification_code, timeout)
        if success:
            return True, message, 'txt_file'
        
        txt_error = message
        
        # Затем пробуем meta тег
        success, message = DomainVerifier.verify_meta_tag(url, verification_code, timeout)
        if success:
            return True, message, 'meta_tag'
        
        # Оба метода не сработали
        combined_message = f"Не удалось верифицировать:\n\n📄 Файл: {txt_error}\n🏷️ Meta: {message}"
        return False, combined_message, None
    
    @staticmethod
    def get_verification_instructions(domain: str, verification_code: str) -> dict:
        """
        Возвращает инструкции по верификации
        
        Args:
            domain: Домен
            verification_code: Код верификации
            
        Returns:
            dict: Инструкции для обоих методов
        """
        return {
            'code': verification_code,
            'domain': domain,
            'methods': {
                'txt_file': {
                    'name': 'Файл верификации',
                    'difficulty': 'easy',
                    'steps': [
                        f"1. Создайте файл: {verification_code}.txt",
                        f"2. Содержимое файла: {verification_code}",
                        f"3. Загрузите в корень сайта: https://{domain}/{verification_code}.txt",
                        "4. Проверьте доступность файла в браузере",
                        "5. Нажмите 'Проверить верификацию'"
                    ],
                    'alternative': f"Или создайте файл securitycheck-verification.txt с содержимым: {verification_code}"
                },
                'meta_tag': {
                    'name': 'HTML Meta тег',
                    'difficulty': 'medium',
                    'steps': [
                        "1. Откройте главную страницу сайта для редактирования",
                        "2. Найдите секцию <head>",
                        f"3. Добавьте мета тег: <meta name=\"securitycheck-site-verification\" content=\"{verification_code}\">",
                        "4. Сохраните изменения",
                        "5. Нажмите 'Проверить верификацию'"
                    ]
                }
            },
            'expiration': '30 дней',
            'note': 'После успешной верификации вы получите полный отчёт с инструкциями по проверке уязвимостей'
        }
