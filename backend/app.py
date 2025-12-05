"""
Главное Flask приложение SecurityCheck
Инициализация всех компонентов и расширений
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import get_config
from database import db, init_db
from models import User


# Создаём экземпляры расширений
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=None):
    """
    Фабрика приложения Flask
    
    Args:
        config_class: Класс конфигурации (опционально)
        
    Returns:
        Flask: Настроенное Flask приложение
    """
    # Определяем пути к frontend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    template_dir = os.path.join(project_root, 'frontend', 'templates')
    static_dir = os.path.join(project_root, 'frontend', 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Загружаем конфигурацию
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Инициализируем расширения
    init_extensions(app)
    
    # Регистрируем blueprints
    register_blueprints(app)
    
    # Настраиваем логирование
    configure_logging(app)
    
    # Регистрируем обработчики ошибок
    register_error_handlers(app)
    
    # Создаём папки если их нет
    ensure_directories(app)
    
    return app


def init_extensions(app):
    """
    Инициализация Flask расширений
    
    Args:
        app: Flask приложение
    """
    # SQLAlchemy и инициализация БД
    init_db(app)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Загрузка пользователя по ID для Flask-Login"""
        return User.query.get(int(user_id))
    
    # CSRF Protection
    csrf.init_app(app)
    
    # Отключаем CSRF для API endpoints (они используют токены)
    @app.before_request
    def csrf_protect():
        pass  # CSRF проверяется автоматически для форм


def register_blueprints(app):
    """
    Регистрация всех blueprints (роутов)
    
    Args:
        app: Flask приложение
    """
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.web_scans import web_scans_bp
    from routes.link_checks import link_checks_bp
    from routes.wifi_scan import wifi_scan_bp
    from routes.domain_intel import domain_intel_bp
    from routes.subscription import subscription_bp
    from routes.stripe_webhook import stripe_webhook_bp
    from routes.verification import verification_bp
    from routes.usage import usage_bp
    
    # Регистрация blueprints
    app.register_blueprint(main_bp)  # Юридические страницы
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)  # Админ-панель
    
    # API blueprints (без CSRF для API endpoints)
    app.register_blueprint(web_scans_bp, url_prefix='/api/web-scans')
    app.register_blueprint(link_checks_bp, url_prefix='/api/link-checks')
    app.register_blueprint(wifi_scan_bp, url_prefix='/api/wifi-scans')
    app.register_blueprint(domain_intel_bp, url_prefix='/api/domain-intel')
    app.register_blueprint(verification_bp, url_prefix='/api/verification')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
    app.register_blueprint(usage_bp, url_prefix='/api/usage')
    
    # Отключаем CSRF для всех API blueprints
    csrf.exempt(web_scans_bp)
    csrf.exempt(link_checks_bp)
    csrf.exempt(wifi_scan_bp)
    csrf.exempt(domain_intel_bp)
    csrf.exempt(verification_bp)
    csrf.exempt(subscription_bp)
    csrf.exempt(usage_bp)
    
    # Stripe webhook (без CSRF)
    app.register_blueprint(stripe_webhook_bp, url_prefix='/stripe')
    csrf.exempt(stripe_webhook_bp)


def configure_logging(app):
    """
    Настройка логирования
    
    Args:
        app: Flask приложение
    """
    if not app.debug and not app.testing:
        # Создаём папку для логов
        log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Настраиваем файловый логгер
        file_handler = RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/app.log'),
            maxBytes=10240000,  # 10 MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('SecurityCheck startup')
    else:
        # В debug режиме выводим в консоль
        logging.basicConfig(level=logging.DEBUG)


def register_error_handlers(app):
    """
    Регистрация обработчиков ошибок
    
    Args:
        app: Flask приложение
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Обработка ошибки 400"""
        if request_wants_json():
            return jsonify({'error': 'Некорректный запрос', 'status': 400}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Обработка ошибки 401"""
        if request_wants_json():
            return jsonify({'error': 'Требуется авторизация', 'status': 401}), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Обработка ошибки 403"""
        if request_wants_json():
            return jsonify({'error': 'Доступ запрещён', 'status': 403}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Обработка ошибки 404"""
        if request_wants_json():
            return jsonify({'error': 'Страница не найдена', 'status': 404}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Обработка ошибки 429 (превышен лимит запросов)"""
        if request_wants_json():
            return jsonify({
                'error': 'Превышен лимит запросов. Попробуйте позже.',
                'status': 429
            }), 429
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Обработка ошибки 500"""
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        if request_wants_json():
            return jsonify({'error': 'Внутренняя ошибка сервера', 'status': 500}), 500
        return render_template('errors/500.html'), 500


def request_wants_json():
    """Проверить, ожидает ли клиент JSON ответ"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def ensure_directories(app):
    """
    Создание необходимых директорий
    
    Args:
        app: Flask приложение
    """
    directories = [
        app.config.get('UPLOAD_FOLDER', 'uploads'),
        os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            app.logger.info(f'Создана директория: {directory}')


# Контекстные процессоры для шаблонов
def register_template_context(app):
    """
    Регистрация контекстных процессоров для шаблонов
    
    Args:
        app: Flask приложение
    """
    
    @app.context_processor
    def utility_processor():
        """Добавление утилит в контекст шаблонов"""
        from datetime import datetime
        return {
            'now': datetime.utcnow(),
            'app_name': 'SecurityCheck',
            'app_version': '1.0.0'
        }


# Health check endpoint
def register_health_check(app):
    """
    Регистрация endpoint для проверки здоровья приложения
    
    Args:
        app: Flask приложение
    """
    
    @app.route('/health')
    def health_check():
        """Endpoint для проверки здоровья приложения (для Render.com)"""
        from .database import DatabaseHealthCheck
        
        health = DatabaseHealthCheck.get_health_status(app)
        
        status = 'healthy' if health['connection'] and health['schema_exists'] else 'unhealthy'
        status_code = 200 if status == 'healthy' else 503
        
        return jsonify({
            'status': status,
            'database': health
        }), status_code
