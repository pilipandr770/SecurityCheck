"""
Скрипт инициализации базы данных SecurityCheck
Создаёт схему и все необходимые таблицы
"""

import sys
import os

# Добавить backend в путь
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import init_db, get_db_stats
from models import User, WebScan, ScanResult, LinkCheck, DomainIntel, StripeEvent


def initialize_database():
    """Инициализировать базу данных"""
    print("🚀 Инициализация базы данных SecurityCheck...")
    print("-" * 50)
    
    # create_app() уже вызывает init_db() внутри init_extensions()
    app = create_app()
    
    with app.app_context():
        try:
            # Схема и таблицы уже созданы в create_app()
            print("✅ Схема security_check_schema создана!")
            
            # Проверить созданные таблицы
            print("\n📊 Проверка таблиц...")
            stats = get_db_stats(app)
            
            if stats and 'tables' in stats:
                tables = stats['tables']
                print(f"✅ Найдено таблиц: {len(tables)}")
                for table_name, row_count in tables.items():
                    print(f"   - {table_name}: {row_count} записей")
            
            # Создать тестового пользователя (опционально)
            create_test = input("\n❓ Создать тестового пользователя? (y/n): ").lower()
            
            if create_test == 'y':
                from werkzeug.security import generate_password_hash
                
                test_email = input("Email (по умолчанию admin@test.com): ").strip() or "admin@test.com"
                test_password = input("Пароль (по умолчанию admin123): ").strip() or "admin123"
                
                # Проверить существование пользователя
                existing_user = User.query.filter_by(email=test_email).first()
                
                if existing_user:
                    print(f"⚠️  Пользователь {test_email} уже существует")
                else:
                    test_user = User(
                        email=test_email,
                        password_hash=generate_password_hash(test_password),
                        subscription_tier='free'
                    )
                    
                    from database import db
                    db.session.add(test_user)
                    db.session.commit()
                    
                    print(f"✅ Тестовый пользователь создан:")
                    print(f"   Email: {test_email}")
                    print(f"   Пароль: {test_password}")
            
            print("\n" + "=" * 50)
            print("🎉 Инициализация завершена успешно!")
            print("=" * 50)
            print("\nТеперь вы можете запустить приложение:")
            print("  python run.py")
            print("\nИли через Flask CLI:")
            print("  flask run")
            
        except Exception as e:
            print(f"\n❌ Ошибка инициализации: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def reset_database():
    """Сброс базы данных (удалить все данные)"""
    confirm = input("⚠️  ВНИМАНИЕ! Это удалит все данные. Продолжить? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Отменено")
        return
    
    print("🗑️  Сброс базы данных...")
    
    app = create_app()
    
    with app.app_context():
        try:
            from database import reset_db
            reset_db()
            print("✅ База данных сброшена")
            
            # Пересоздать схему
            print("📦 Создание новой схемы...")
            init_db()
            print("✅ Схема создана")
            
        except Exception as e:
            print(f"❌ Ошибка сброса: {str(e)}")
            sys.exit(1)


def check_database():
    """Проверить состояние базы данных"""
    print("🔍 Проверка базы данных...")
    print("-" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Проверить подключение
            from database import db
            db.session.execute('SELECT 1')
            print("✅ Подключение к базе данных успешно")
            
            # Получить статистику
            stats = get_db_stats()
            
            if stats:
                print("\n📊 Статистика таблиц:")
                for table_name, row_count in stats.items():
                    print(f"   {table_name}: {row_count} записей")
            
            # Проверить пользователей
            users_count = User.query.count()
            print(f"\n👥 Зарегистрировано пользователей: {users_count}")
            
            if users_count > 0:
                print("\nПоследние 5 пользователей:")
                recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
                for user in recent_users:
                    print(f"   - {user.email} ({user.subscription_tier}) - {user.created_at}")
            
        except Exception as e:
            print(f"❌ Ошибка проверки: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    print("=" * 50)
    print("SecurityCheck - Управление базой данных")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            initialize_database()
        elif command == 'reset':
            reset_database()
        elif command == 'check':
            check_database()
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("\nДоступные команды:")
            print("  python init_db.py init   - Инициализировать БД")
            print("  python init_db.py reset  - Сбросить БД")
            print("  python init_db.py check  - Проверить БД")
    else:
        # Интерактивный режим
        print("\nВыберите действие:")
        print("1. Инициализировать базу данных")
        print("2. Сбросить базу данных")
        print("3. Проверить базу данных")
        print("4. Выход")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == '1':
            initialize_database()
        elif choice == '2':
            reset_database()
        elif choice == '3':
            check_database()
        elif choice == '4':
            print("👋 До свидания!")
        else:
            print("❌ Неверный выбор")
