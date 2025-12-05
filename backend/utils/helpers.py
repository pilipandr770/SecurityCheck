"""
Вспомогательные функции
"""

from datetime import datetime, timedelta
from urllib.parse import urlparse
import re


def format_datetime(dt, format_string='%d.%m.%Y %H:%M'):
    """
    Форматировать datetime для отображения
    
    Args:
        dt: datetime объект
        format_string: Формат
        
    Returns:
        str: Отформатированная дата
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        return dt
    
    return dt.strftime(format_string)


def time_ago(dt):
    """
    Получить относительное время (например "2 часа назад")
    
    Args:
        dt: datetime объект
        
    Returns:
        str: Относительное время
    """
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'только что'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} {"минуту" if minutes == 1 else "минуты" if minutes < 5 else "минут"} назад'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} {"час" if hours == 1 else "часа" if hours < 5 else "часов"} назад'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} {"день" if days == 1 else "дня" if days < 5 else "дней"} назад'
    else:
        return format_datetime(dt, '%d.%m.%Y')


def format_file_size(size_bytes):
    """
    Форматировать размер файла
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Читаемый размер
    """
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    elif size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.1f} MB'
    else:
        return f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'


def sanitize_url(url):
    """
    Очистить и нормализовать URL
    
    Args:
        url: URL строка
        
    Returns:
        str: Очищенный URL
    """
    url = url.strip()
    
    # Добавляем схему если отсутствует
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Парсим и собираем обратно для нормализации
    try:
        parsed = urlparse(url)
        return parsed.geturl()
    except Exception:
        return url


def extract_domain(url):
    """
    Извлечь домен из URL
    
    Args:
        url: URL строка
        
    Returns:
        str: Домен
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Убираем www.
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        return url


def severity_to_badge_class(severity):
    """
    Конвертировать severity в CSS класс для badge
    
    Args:
        severity: Уровень критичности
        
    Returns:
        str: CSS класс
    """
    mapping = {
        'critical': 'badge-danger',
        'high': 'badge-danger',
        'medium': 'badge-warning',
        'low': 'badge-info',
        'info': 'badge-secondary'
    }
    return mapping.get(severity, 'badge-secondary')


def threat_level_to_badge_class(threat_level):
    """
    Конвертировать threat_level в CSS класс
    
    Args:
        threat_level: Уровень угрозы
        
    Returns:
        str: CSS класс
    """
    mapping = {
        'danger': 'badge-danger',
        'warning': 'badge-warning',
        'safe': 'badge-success'
    }
    return mapping.get(threat_level, 'badge-secondary')


def calculate_security_grade(score):
    """
    Рассчитать буквенную оценку безопасности
    
    Args:
        score: Оценка 0-100
        
    Returns:
        str: Буквенная оценка (A, B, C, D, F)
    """
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def truncate_text(text, length=100, suffix='...'):
    """
    Обрезать текст до указанной длины
    
    Args:
        text: Текст
        length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        str: Обрезанный текст
    """
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix


def is_valid_email(email):
    """
    Проверить валидность email
    
    Args:
        email: Email адрес
        
    Returns:
        bool: True если валидный
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_random_string(length=32):
    """
    Сгенерировать случайную строку
    
    Args:
        length: Длина строки
        
    Returns:
        str: Случайная строка
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password):
    """
    Хешировать пароль
    
    Args:
        password: Пароль
        
    Returns:
        str: Хеш
    """
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)


def check_password(password_hash, password):
    """
    Проверить пароль
    
    Args:
        password_hash: Хеш пароля
        password: Пароль для проверки
        
    Returns:
        bool: True если совпадает
    """
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)
