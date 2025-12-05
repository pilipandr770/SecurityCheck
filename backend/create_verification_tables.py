"""
Создать таблицы для системы верификации
"""

import sys
from app import create_app
from database import db

def create_verification_tables():
    """Создать таблицы для верификации"""
    app = create_app()
    
    with app.app_context():
        print("Создание таблиц...")
        
        # Создать все таблицы (в т.ч. domain_verifications)
        db.create_all()
        
        # Добавить поля в web_scans если их нет
        try:
            db.session.execute("""
                ALTER TABLE web_scans 
                ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL
            """)
            db.session.commit()
            print("✅ Добавлено поле is_verified в web_scans")
        except Exception as e:
            print(f"⚠️ Поле is_verified уже существует или ошибка: {e}")
            db.session.rollback()
        
        try:
            db.session.execute("""
                ALTER TABLE web_scans 
                ADD COLUMN IF NOT EXISTS verification_id INTEGER REFERENCES domain_verifications(id) ON DELETE SET NULL
            """)
            db.session.commit()
            print("✅ Добавлено поле verification_id в web_scans")
        except Exception as e:
            print(f"⚠️ Поле verification_id уже существует или ошибка: {e}")
            db.session.rollback()
        
        print("\n✅ Миграция завершена!")

if __name__ == '__main__':
    create_verification_tables()
