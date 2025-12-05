"""
Конфигурация приложения SecurityCheck
Поддержка development и production окружений
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Базовая конфигурация"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - использует DATABASE_URL из .env или собирает из компонентов
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Используем полный URL из .env (например, Render.com)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Или собираем из отдельных компонентов
        DB_USER = os.environ.get('POSTGRES_USER', 'postgres')
        DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
        DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        DB_PORT = os.environ.get('POSTGRES_PORT', '5432')
        DB_NAME = os.environ.get('POSTGRES_DB', 'security_check_db')
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    
    DB_SCHEMA = os.environ.get('POSTGRES_SCHEMA', 'security_check_schema')
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'options': f'-c search_path={DB_SCHEMA}'
        }
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Stripe
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    # AI Provider
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'anthropic')  # 'openai' или 'anthropic'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # Security APIs
    VIRUSTOTAL_API_KEY = os.environ.get('VIRUSTOTAL_API_KEY', '')
    GOOGLE_SAFEBROWSING_KEY = os.environ.get('GOOGLE_SAFEBROWSING_KEY', '')
    IPQUALITYSCORE_KEY = os.environ.get('IPQUALITYSCORE_KEY', '')
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 524288000))  # 500MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = set(
        os.environ.get('ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,zip,txt,jpg,png').split(',')
    )
    
    # Scanning
    MAX_SCAN_TIMEOUT = int(os.environ.get('MAX_SCAN_TIMEOUT', 30))
    
    # Rate Limits (запросов в день)
    RATE_LIMITS = {
        'free': {
            'web_scans': 10,
            'link_checks': 20,
            'network_scans': 5,
            'domain_lookups': 10,
            'file_uploads': 5,
            'max_file_size_mb': 10,
            'history_days': 7
        },
        'starter': {
            'web_scans': -1,  # unlimited
            'link_checks': -1,
            'network_scans': 50,
            'domain_lookups': -1,
            'file_uploads': 5,
            'max_file_size_mb': 50,
            'history_days': 30
        },
        'pro': {
            'web_scans': -1,
            'link_checks': -1,
            'network_scans': -1,
            'domain_lookups': -1,
            'file_uploads': -1,
            'max_file_size_mb': 500,
            'history_days': -1  # unlimited
        }
    }
    
    # Subscription Prices (в центах)
    SUBSCRIPTION_PRICES = {
        'starter': {
            'monthly': 500,  # €5
            'yearly': 5000   # €50 (2 месяца бесплатно)
        },
        'pro': {
            'monthly': 1500,  # €15
            'yearly': 15000   # €150 (2 месяца бесплатно)
        }
    }
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    
    # В разработке используем менее строгие настройки cookie
    SESSION_COOKIE_SECURE = False
    
    # SQLite для локальной разработки (если PostgreSQL недоступен)
    # Раскомментируйте если нужно:
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///security_check_dev.db'
    # SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    """Конфигурация для production (Render.com)"""
    
    DEBUG = False
    FLASK_ENV = 'production'
    
    # В production обязательно используем безопасные настройки
    SESSION_COOKIE_SECURE = True
    
    # Render.com предоставляет DATABASE_URL
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Render использует postgres://, но SQLAlchemy требует postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        return super().SQLALCHEMY_DATABASE_URI


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    
    TESTING = True
    DEBUG = True
    
    # Используем отдельную тестовую БД
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Отключаем CSRF для тестов
    WTF_CSRF_ENABLED = False
    
    # Отключаем rate limits для тестов
    RATE_LIMITS = {
        'free': {
            'web_scans': -1,
            'link_checks': -1,
            'domain_lookups': -1,
            'file_uploads': -1,
            'max_file_size_mb': 500,
            'history_days': -1
        }
    }


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Получить конфигурацию на основе FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
