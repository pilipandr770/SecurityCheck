"""
Утилиты для проверки лимитов тарифных планов
"""

from datetime import datetime, timedelta
from models import SubscriptionPlan, User, WebScan, LinkCheck, DomainIntel
from database import db
from sqlalchemy import func


# Лимиты для тарифных планов
PLAN_LIMITS = {
    'free': {
        'web_scans_per_month': 10,
        'link_checks_per_month': 50,
        'wifi_scans_per_month': 5,
        'domain_lookups_per_month': 5,
        'history_days': 7,
        'pdf_export': False,
        'api_access': False,
        'email_alerts': False,
        'priority_support': False
    },
    'starter': {
        'web_scans_per_month': -1,  # -1 = unlimited
        'link_checks_per_month': -1,
        'wifi_scans_per_month': -1,
        'domain_lookups_per_month': -1,
        'history_days': 90,
        'pdf_export': True,
        'api_access': False,
        'email_alerts': True,
        'priority_support': False
    },
    'pro': {
        'web_scans_per_month': -1,
        'link_checks_per_month': -1,
        'wifi_scans_per_month': -1,
        'domain_lookups_per_month': -1,
        'history_days': -1,  # -1 = unlimited
        'pdf_export': True,
        'api_access': True,
        'email_alerts': True,
        'priority_support': True
    }
}


def get_plan_limits(plan: SubscriptionPlan) -> dict:
    """
    Получить лимиты для тарифного плана
    
    Args:
        plan: Тарифный план (enum)
        
    Returns:
        dict: Словарь с лимитами
    """
    plan_value = plan.value if isinstance(plan, SubscriptionPlan) else plan
    return PLAN_LIMITS.get(plan_value, PLAN_LIMITS['free'])


def check_scan_limit(user: User, scan_type: str) -> dict:
    """
    Проверить, может ли пользователь выполнить сканирование
    
    Args:
        user: Пользователь
        scan_type: Тип сканирования ('web_scans', 'link_checks', 'wifi_scans', 'domain_lookups')
        
    Returns:
        dict: {
            'allowed': bool,
            'reason': str (если not allowed),
            'used': int,
            'limit': int,
            'remaining': int
        }
    """
    limits = get_plan_limits(user.subscription_plan)
    limit_key = f"{scan_type}_per_month"
    
    # Получаем лимит для данного типа сканирования
    limit = limits.get(limit_key, 0)
    
    # Если лимит = -1, это безлимит
    if limit == -1:
        return {
            'allowed': True,
            'used': 0,
            'limit': -1,
            'remaining': -1
        }
    
    # Считаем использование за текущий месяц
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if scan_type == 'web_scans':
        used = WebScan.query.filter(
            WebScan.user_id == user.id,
            WebScan.created_at >= start_of_month
        ).count()
    elif scan_type == 'link_checks':
        used = LinkCheck.query.filter(
            LinkCheck.user_id == user.id,
            LinkCheck.created_at >= start_of_month
        ).count()
    elif scan_type == 'domain_lookups':
        used = DomainIntel.query.filter(
            DomainIntel.user_id == user.id,
            DomainIntel.created_at >= start_of_month
        ).count()
    elif scan_type == 'wifi_scans':
        # Для WiFi-сканов пока нет отдельной таблицы, используем WebScan как заглушку
        # TODO: Создать таблицу для WiFi сканирований
        used = 0
    else:
        used = 0
    
    remaining = max(0, limit - used)
    allowed = used < limit
    
    result = {
        'allowed': allowed,
        'used': used,
        'limit': limit,
        'remaining': remaining
    }
    
    if not allowed:
        result['reason'] = f'Limit von {limit} Scans pro Monat erreicht. Upgraden Sie Ihren Tarif, um fortzufahren.'
    
    return result


def get_usage_statistics(user: User) -> dict:
    """
    Получить статистику использования для пользователя
    
    Args:
        user: Пользователь
        
    Returns:
        dict: Статистика по всем типам сканирований
    """
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    web_scans_count = WebScan.query.filter(
        WebScan.user_id == user.id,
        WebScan.created_at >= start_of_month
    ).count()
    
    link_checks_count = LinkCheck.query.filter(
        LinkCheck.user_id == user.id,
        LinkCheck.created_at >= start_of_month
    ).count()
    
    domain_lookups_count = DomainIntel.query.filter(
        DomainIntel.user_id == user.id,
        DomainIntel.created_at >= start_of_month
    ).count()
    
    limits = get_plan_limits(user.subscription_plan)
    
    return {
        'web_scans': {
            'used': web_scans_count,
            'limit': limits['web_scans_per_month'],
            'remaining': -1 if limits['web_scans_per_month'] == -1 else max(0, limits['web_scans_per_month'] - web_scans_count)
        },
        'link_checks': {
            'used': link_checks_count,
            'limit': limits['link_checks_per_month'],
            'remaining': -1 if limits['link_checks_per_month'] == -1 else max(0, limits['link_checks_per_month'] - link_checks_count)
        },
        'domain_lookups': {
            'used': domain_lookups_count,
            'limit': limits['domain_lookups_per_month'],
            'remaining': -1 if limits['domain_lookups_per_month'] == -1 else max(0, limits['domain_lookups_per_month'] - domain_lookups_count)
        },
        'wifi_scans': {
            'used': 0,
            'limit': limits['wifi_scans_per_month'],
            'remaining': limits['wifi_scans_per_month']
        }
    }


def has_feature(user: User, feature: str) -> bool:
    """
    Проверить, доступна ли функция для тарифа пользователя
    
    Args:
        user: Пользователь
        feature: Название функции ('pdf_export', 'api_access', 'email_alerts', 'priority_support')
        
    Returns:
        bool: True если доступна
    """
    limits = get_plan_limits(user.subscription_plan)
    return limits.get(feature, False)
