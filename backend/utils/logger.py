"""
Централизованное логирование
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(app=None, log_level=None):
    """
    Настроить логгер приложения
    
    Args:
        app: Flask app
        log_level: Уровень логирования
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    if log_level is None:
        log_level = logging.INFO
    
    # Создать директорию для логов
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Хендлер для файла (ротация при 10MB, 5 backup файлов)
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    if app:
        # Настроить логгер Flask
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(log_level)
        return app.logger
    else:
        # Создать standalone логгер
        logger = logging.getLogger('security_check')
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(log_level)
        return logger


def log_security_event(user_id, event_type, details):
    """
    Логировать событие безопасности
    
    Args:
        user_id: ID пользователя
        event_type: Тип события (login, scan, upload, etc)
        details: Детали события
    """
    logger = logging.getLogger('security_check')
    logger.info(f'SECURITY_EVENT | User: {user_id} | Type: {event_type} | Details: {details}')


def log_api_call(service_name, endpoint, status_code, response_time):
    """
    Логировать вызов внешнего API
    
    Args:
        service_name: Название сервиса (VirusTotal, Stripe, etc)
        endpoint: Endpoint
        status_code: HTTP статус
        response_time: Время ответа в секундах
    """
    logger = logging.getLogger('security_check')
    logger.info(f'API_CALL | Service: {service_name} | Endpoint: {endpoint} | Status: {status_code} | Time: {response_time:.2f}s')


def log_error(error, context=None):
    """
    Логировать ошибку с контекстом
    
    Args:
        error: Объект исключения
        context: Дополнительный контекст
    """
    logger = logging.getLogger('security_check')
    
    error_msg = f'ERROR | {type(error).__name__}: {str(error)}'
    if context:
        error_msg += f' | Context: {context}'
    
    logger.error(error_msg, exc_info=True)


def log_scan_start(user_id, scan_type, target):
    """
    Логировать начало сканирования
    
    Args:
        user_id: ID пользователя
        scan_type: Тип сканирования
        target: Цель (URL, file, domain)
    """
    logger = logging.getLogger('security_check')
    logger.info(f'SCAN_START | User: {user_id} | Type: {scan_type} | Target: {target}')


def log_scan_complete(user_id, scan_type, target, duration, findings):
    """
    Логировать завершение сканирования
    
    Args:
        user_id: ID пользователя
        scan_type: Тип сканирования
        target: Цель
        duration: Длительность в секундах
        findings: Количество найденных проблем
    """
    logger = logging.getLogger('security_check')
    logger.info(f'SCAN_COMPLETE | User: {user_id} | Type: {scan_type} | Target: {target} | Duration: {duration:.2f}s | Findings: {findings}')
