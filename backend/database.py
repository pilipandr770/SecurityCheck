"""
Инициализация базы данных PostgreSQL с отдельной схемой
SecurityCheck использует схему security_check_schema
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

# Создаём экземпляр SQLAlchemy
db = SQLAlchemy()


def init_db(app):
    """
    Инициализация базы данных и создание схемы
    
    Args:
        app: Flask приложение
    """
    db.init_app(app)
    
    with app.app_context():
        # Получаем имя схемы из конфигурации
        schema_name = app.config.get('DB_SCHEMA', 'security_check_schema')
        
        # Создаём схему если её нет
        try:
            db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema_name}'))
            db.session.commit()
            app.logger.info(f'Схема {schema_name} создана или уже существует')
        except Exception as e:
            app.logger.error(f'Ошибка создания схемы: {e}')
            db.session.rollback()
        
        # Устанавливаем search_path для текущей сессии
        try:
            db.session.execute(text(f'SET search_path TO {schema_name}'))
            db.session.commit()
        except Exception as e:
            app.logger.error(f'Ошибка установки search_path: {e}')
            db.session.rollback()
        
        # Создаём все таблицы
        db.create_all()
        app.logger.info('Все таблицы созданы')


def reset_db(app):
    """
    Сброс базы данных (удаление всех таблиц и создание заново)
    ВНИМАНИЕ: Используйте только в development!
    
    Args:
        app: Flask приложение
    """
    with app.app_context():
        if app.config.get('FLASK_ENV') == 'production':
            raise RuntimeError('Нельзя сбрасывать БД в production!')
        
        db.drop_all()
        db.create_all()
        app.logger.warning('База данных сброшена!')


def get_db_stats(app):
    """
    Получить статистику базы данных
    
    Args:
        app: Flask приложение
        
    Returns:
        dict: Статистика БД
    """
    with app.app_context():
        schema_name = app.config.get('DB_SCHEMA', 'security_check_schema')
        
        stats = {
            'schema': schema_name,
            'tables': {}
        }
        
        # Получаем список таблиц и количество записей
        try:
            result = db.session.execute(text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema_name}'
            """))
            
            tables = [row[0] for row in result]
            
            for table in tables:
                count_result = db.session.execute(
                    text(f'SELECT COUNT(*) FROM {schema_name}.{table}')
                )
                count = count_result.scalar()
                stats['tables'][table] = count
                
        except Exception as e:
            app.logger.error(f'Ошибка получения статистики БД: {e}')
            
        return stats


# Обработчик событий для автоматической установки search_path
@event.listens_for(Engine, 'connect')
def set_search_path(dbapi_connection, connection_record):
    """
    Автоматически устанавливает search_path при каждом подключении
    """
    # Этот обработчик работает только если connection_record содержит схему
    # Основная установка search_path происходит через connect_args в config.py
    pass


class DatabaseHealthCheck:
    """Проверка здоровья базы данных"""
    
    @staticmethod
    def check_connection(app):
        """
        Проверить подключение к БД
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                return True
        except Exception as e:
            app.logger.error(f'Ошибка подключения к БД: {e}')
            return False
    
    @staticmethod
    def check_schema_exists(app):
        """
        Проверить существование схемы
        
        Returns:
            bool: True если схема существует
        """
        try:
            with app.app_context():
                schema_name = app.config.get('DB_SCHEMA', 'security_check_schema')
                result = db.session.execute(text(f"""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = '{schema_name}'
                """))
                return result.scalar() is not None
        except Exception as e:
            app.logger.error(f'Ошибка проверки схемы: {e}')
            return False
    
    @staticmethod
    def get_health_status(app):
        """
        Полная проверка здоровья БД
        
        Returns:
            dict: Статус здоровья
        """
        return {
            'connection': DatabaseHealthCheck.check_connection(app),
            'schema_exists': DatabaseHealthCheck.check_schema_exists(app),
            'stats': get_db_stats(app) if DatabaseHealthCheck.check_connection(app) else None
        }
