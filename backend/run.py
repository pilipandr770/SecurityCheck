"""
Точка входа для запуска Flask приложения
"""

import os
from app import create_app

# Создаём приложение
app = create_app()

if __name__ == '__main__':
    # Получаем порт из переменной окружения (для Render.com)
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем приложение
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('FLASK_ENV') == 'development'
    )
