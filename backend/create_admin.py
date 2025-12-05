"""
Скрипт для создания администратора с безлимитным планом
"""

import sys
from werkzeug.security import generate_password_hash
from database import db, init_db
from models import User, SubscriptionPlan

def create_admin(email, password, name="Admin"):
    """Создать администратора"""
    
    # Инициализация БД
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Проверяем существует ли уже админ
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"⚠️  Пользователь с email {email} уже существует!")
            response = input("Обновить план на PRO? (y/n): ")
            if response.lower() == 'y':
                existing_user.subscription_plan = SubscriptionPlan.PRO
                db.session.commit()
                print(f"✅ План пользователя {email} обновлен на PRO (безлимит)")
                return
            else:
                print("❌ Отменено")
                return
        
        # Создаём нового админа
        admin = User(
            email=email,
            full_name=name,
            password_hash=generate_password_hash(password),
            subscription_plan=SubscriptionPlan.PRO,  # PRO план = безлимит
            is_admin=True,
            is_active=True,
            email_verified=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"""
✅ Администратор успешно создан!

📧 Email: {email}
👤 Имя: {admin.full_name}
🔐 Password: {password}
💎 План: PRO (безлимит)
🛡️  Админ: Да

🎯 Возможности:
   • Безлимитные веб-сканирования
   • Безлимитные проверки ссылок
   • Безлимитные загрузки файлов (до 50 MB)
   • Безлимитные проверки доменов
   • Полный доступ ко всем функциям

🚀 Войдите на http://localhost:5000/login
        """)

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════╗
║   SecurityCheck - Создание Админа     ║
╚═══════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else 'admin123'
        name = sys.argv[3] if len(sys.argv) > 3 else 'Admin'
    else:
        email = input("📧 Введите email админа: ").strip()
        if not email:
            email = "admin@securitycheck.com"
        
        password = input("🔐 Введите пароль (Enter для 'admin123'): ").strip()
        if not password:
            password = "admin123"
    
    try:
        create_admin(email, password)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
