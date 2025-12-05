"""
Скрипт для создания администратора
"""

import sys
from app import create_app
from database import db
from models import User, SubscriptionPlan

def create_admin(email, password):
    """Создать администратора"""
    app = create_app()
    
    with app.app_context():
        # Проверяем существует ли пользователь
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            # Если существует - делаем админом
            existing_user.is_admin = True
            existing_user.subscription_plan = SubscriptionPlan.PRO
            db.session.commit()
            print(f'✅ Пользователь {email} теперь администратор')
        else:
            # Создаём нового админа
            admin = User(
                email=email,
                is_admin=True,
                is_active=True,
                subscription_plan=SubscriptionPlan.PRO
            )
            admin.set_password(password)
            
            db.session.add(admin)
            db.session.commit()
            print(f'✅ Администратор {email} создан')
            print(f'   Пароль: {password}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Использование: python make_admin.py <email> <password>')
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    create_admin(email, password)
