"""
Прямое добавление полей в базу данных
"""

import sys
from app import create_app
from database import db
from sqlalchemy import text

def add_verification_columns():
    """Добавить поля верификации в web_scans"""
    app = create_app()
    
    with app.app_context():
        print("Добавление полей верификации...")
        
        try:
            # Добавить is_verified
            db.session.execute(text("""
                ALTER TABLE web_scans 
                ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL
            """))
            db.session.commit()
            print("✅ Добавлено поле is_verified")
        except Exception as e:
            print(f"⚠️  is_verified: {e}")
            db.session.rollback()
        
        try:
            # Добавить verification_id
            db.session.execute(text("""
                ALTER TABLE web_scans 
                ADD COLUMN verification_id INTEGER
            """))
            db.session.commit()
            print("✅ Добавлено поле verification_id")
        except Exception as e:
            print(f"⚠️  verification_id: {e}")
            db.session.rollback()
        
        try:
            # Добавить foreign key
            db.session.execute(text("""
                ALTER TABLE web_scans 
                ADD CONSTRAINT fk_web_scans_verification 
                FOREIGN KEY (verification_id) 
                REFERENCES domain_verifications(id) 
                ON DELETE SET NULL
            """))
            db.session.commit()
            print("✅ Добавлен foreign key")
        except Exception as e:
            print(f"⚠️  foreign key: {e}")
            db.session.rollback()
        
        print("\n✅ Миграция завершена!")

if __name__ == '__main__':
    add_verification_columns()
