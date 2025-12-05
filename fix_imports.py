"""
Скрипт для исправления относительных импортов на абсолютные
"""
import os
import re

def fix_imports_in_file(filepath):
    """Заменить относительные импорты на абсолютные"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменить ..database на database
    content = re.sub(r'from \.\.database import', 'from database import', content)
    
    # Заменить ..models на models
    content = re.sub(r'from \.\.models import', 'from models import', content)
    
    # Заменить ..config на config
    content = re.sub(r'from \.\.config import', 'from config import', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fixed: {filepath}")

# Исправить все файлы в routes
routes_dir = 'backend/routes'
for filename in os.listdir(routes_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        fix_imports_in_file(os.path.join(routes_dir, filename))

print("\nВсе импорты исправлены!")
