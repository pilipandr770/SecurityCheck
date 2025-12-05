# Руководство по установке SecurityCheck

## Требования

- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (опционально, для frontend разработки)
- Stripe аккаунт для приёма платежей
- API ключи для внешних сервисов

## Шаг 1: Клонирование и подготовка окружения

```bash
# Клонировать репозиторий
git clone <repository-url>
cd security-check

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## Шаг 2: Настройка PostgreSQL

```sql
-- Создать базу данных
CREATE DATABASE security_check_db;

-- Создать пользователя (опционально)
CREATE USER security_check_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE security_check_db TO security_check_user;
```

## Шаг 3: Настройка переменных окружения

Скопируйте файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

Заполните следующие переменные в `.env`:

### Основные настройки Flask
```env
FLASK_APP=backend/app.py
FLASK_ENV=development
SECRET_KEY=<генерируйте случайный ключ>
```

### База данных PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost:5432/security_check_db
POSTGRES_USER=security_check_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=security_check_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Stripe (платежи)
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs из Stripe Dashboard
STRIPE_STARTER_MONTHLY_PRICE_ID=price_...
STRIPE_STARTER_YEARLY_PRICE_ID=price_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
```

### OpenAI / Anthropic (AI объяснения)
```env
# Выберите один:
AI_PROVIDER=openai  # или anthropic
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Внешние API для проверки безопасности
```env
VIRUSTOTAL_API_KEY=<ваш ключ>
GOOGLE_SAFE_BROWSING_KEY=<ваш ключ>
IPQUALITYSCORE_API_KEY=<ваш ключ>  # опционально
```

## Шаг 4: Получение API ключей

### VirusTotal API
1. Зарегистрируйтесь на https://www.virustotal.com/
2. Перейдите в профиль → API Key
3. Скопируйте ключ в `.env`

### Google Safe Browsing API
1. Перейдите в Google Cloud Console
2. Создайте проект
3. Включите Safe Browsing API
4. Создайте API ключ
5. Скопируйте ключ в `.env`

### Stripe
1. Зарегистрируйтесь на https://stripe.com/
2. Перейдите в Dashboard → Developers → API Keys
3. Скопируйте Test keys в `.env`
4. Создайте Products и Price IDs:
   - Starter Monthly (€5/месяц)
   - Starter Yearly (€50/год)
   - Pro Monthly (€15/месяц)
   - Pro Yearly (€150/год)
5. Настройте Webhook endpoint для `/api/stripe/webhook`

### OpenAI API
1. Зарегистрируйтесь на https://platform.openai.com/
2. Перейдите в API Keys
3. Создайте новый ключ
4. Скопируйте ключ в `.env`

## Шаг 5: Инициализация базы данных

```python
# Откройте Python shell
python

# Выполните:
from backend.app import create_app
from backend.database import init_db

app = create_app()
with app.app_context():
    init_db()
    print("База данных инициализирована!")
```

Или используйте Flask CLI:

```bash
flask shell

>>> from backend.database import init_db
>>> init_db()
>>> exit()
```

## Шаг 6: Запуск приложения

### Режим разработки

```bash
# Метод 1: Напрямую через Python
cd backend
python run.py

# Метод 2: Через Flask CLI
export FLASK_APP=backend/app.py  # Linux/Mac
set FLASK_APP=backend/app.py     # Windows
flask run --debug

# Приложение будет доступно на http://localhost:5000
```

### Режим production (с Gunicorn)

```bash
# Установить Gunicorn (уже в requirements.txt)
pip install gunicorn

# Запустить с 4 воркерами
gunicorn -w 4 -b 0.0.0.0:8000 "backend.app:create_app()"
```

## Шаг 7: Проверка установки

1. Откройте браузер и перейдите на http://localhost:5000
2. Зарегистрируйте тестовый аккаунт
3. Попробуйте выполнить тестовое сканирование

### Проверка health endpoint

```bash
curl http://localhost:5000/api/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Шаг 8: Настройка Nginx (опционально для production)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/security-check/frontend/static;
        expires 30d;
    }
}
```

## Troubleshooting

### Ошибка подключения к PostgreSQL

```bash
# Проверить статус PostgreSQL
sudo systemctl status postgresql  # Linux
pg_ctl status  # Windows

# Перезапустить PostgreSQL
sudo systemctl restart postgresql  # Linux
pg_ctl restart  # Windows
```

### Ошибка импорта модулей

```bash
# Убедитесь что виртуальное окружение активно
which python  # должен показать путь в venv

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Ошибки API ключей

```bash
# Проверьте что .env файл загружен
python -c "import os; print(os.getenv('VIRUSTOTAL_API_KEY'))"

# Должен вывести ваш ключ, а не None
```

### Порт уже занят

```bash
# Найти процесс на порту 5000
# Linux/Mac:
lsof -i :5000
# Windows:
netstat -ano | findstr :5000

# Убить процесс
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

## Следующие шаги

- Прочитайте [USER_GUIDE.md](USER_GUIDE.md) для инструкций пользователя
- Прочитайте [API.md](API.md) для документации API
- Прочитайте [DEPLOYMENT.md](DEPLOYMENT.md) для деплоя на production

## Полезные команды

```bash
# Проверить версию Python
python --version

# Проверить установленные пакеты
pip list

# Обновить requirements.txt
pip freeze > requirements.txt

# Создать миграцию БД (если используете Alembic)
flask db migrate -m "описание"
flask db upgrade

# Запустить тесты
pytest tests/

# Проверить код на ошибки
flake8 backend/
pylint backend/
```

## Контакты и поддержка

Если возникли проблемы:
1. Проверьте секцию Troubleshooting
2. Посмотрите логи в `backend/logs/`
3. Создайте issue в GitHub

---

**Автор:** SecurityCheck Team  
**Лицензия:** MIT  
**Версия:** 1.0.0
