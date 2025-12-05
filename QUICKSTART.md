# SecurityCheck - Quick Start Guide

## 🚀 Быстрый старт (5 минут)

### Предварительные требования
- Python 3.9+
- PostgreSQL 13+
- Git

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd security-check

# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Активировать (Linux/Mac)
source venv/bin/activate

# Установить зависимости
pip install -r backend/requirements.txt
```

### 2. Создать базу данных PostgreSQL

```sql
CREATE DATABASE security_check_db;
```

### 3. Настроить .env файл

```bash
# Скопировать пример
cp backend/.env.example backend/.env

# Отредактировать backend/.env
# Минимум нужно:
DATABASE_URL=postgresql://user:password@localhost:5432/security_check_db
SECRET_KEY=your-secret-key-here
VIRUSTOTAL_API_KEY=your-key
OPENAI_API_KEY=your-key
STRIPE_SECRET_KEY=your-key
```

### 4. Инициализировать базу данных

```bash
cd backend
python init_db.py init
```

Создайте тестового пользователя когда спросит (y)

### 5. Запустить приложение

```bash
python run.py
```

Откройте браузер: **http://localhost:5000**

## 🎯 Тест функциональности

1. **Регистрация**: Создайте аккаунт или войдите как admin@test.com / admin123
2. **Проверка сайта**: Зайдите в "Проверка сайта" и введите https://example.com
3. **Проверка ссылки**: Протестируйте любую ссылку
4. **Загрузка файла**: Загрузите тестовый PDF файл
5. **Проверка домена**: Введите example.com

## 📋 Получение API ключей

### VirusTotal (обязательно)
1. https://www.virustotal.com/gui/join-us
2. Профиль → API Key
3. Копировать в .env

### OpenAI (обязательно для AI объяснений)
1. https://platform.openai.com/signup
2. API Keys → Create new secret key
3. Копировать в .env

### Stripe (для платежей)
1. https://dashboard.stripe.com/register
2. Developers → API Keys → Test mode
3. Копировать Secret key в .env

### Google Safe Browsing (опционально)
1. https://console.cloud.google.com/
2. Создать проект
3. Enable Safe Browsing API
4. Create credentials → API key

## 🔧 Структура проекта

```
security-check/
├── backend/
│   ├── routes/          # API endpoints
│   ├── services/        # Бизнес-логика
│   ├── models.py        # SQLAlchemy модели
│   ├── database.py      # Подключение к БД
│   ├── config.py        # Конфигурация
│   ├── app.py           # Flask app factory
│   ├── run.py           # Точка входа
│   └── init_db.py       # Скрипт инициализации БД
├── frontend/
│   ├── templates/       # HTML шаблоны
│   └── static/
│       ├── css/         # Стили
│       └── js/          # JavaScript
├── tests/               # Юнит-тесты
├── docs/                # Документация
├── .gitignore
├── README.md
└── SETUP.md            # Полная инструкция
```

## 🐛 Troubleshooting

### Ошибка: "No module named 'flask'"
```bash
pip install -r backend/requirements.txt
```

### Ошибка: "Could not connect to database"
```bash
# Проверить PostgreSQL
# Windows:
pg_ctl status

# Проверить .env:
DATABASE_URL=postgresql://user:password@localhost:5432/security_check_db
```

### Ошибка: "API key not found"
```bash
# Проверить .env файл
cat backend/.env | grep API_KEY
```

### Порт 5000 занят
```bash
# Изменить порт в backend/run.py
app.run(host='0.0.0.0', port=8000, debug=True)
```

## 📚 Дополнительная документация

- **[SETUP.md](SETUP.md)** - Подробная инструкция по установке
- **[API.md](docs/API.md)** - Документация API
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - Руководство пользователя
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Деплой на production

## 🎓 Примеры использования

### Проверка сайта через API

```bash
curl -X POST http://localhost:5000/api/web-scans/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Проверка ссылки через API

```bash
curl -X POST http://localhost:5000/api/link-checks/check \
  -H "Content-Type: application/json" \
  -d '{"url": "https://suspicious-link.com"}'
```

## 💡 Полезные команды

```bash
# Проверить статус БД
cd backend
python init_db.py check

# Сбросить БД (удалит все данные!)
python init_db.py reset

# Запустить тесты
pytest tests/

# Проверить код
flake8 backend/

# Production сервер
gunicorn -w 4 -b 0.0.0.0:8000 "backend.app:create_app()"
```

## 🔐 Тарифные планы

| Тариф | Цена | Лимиты |
|-------|------|--------|
| Free | €0/месяц | 10 проверок сайтов/день, 20 ссылок, 5 файлов, 5 доменов |
| Starter | €5/месяц | 100 проверок сайтов/день, 200 ссылок, 50 файлов, 50 доменов |
| Pro | €15/месяц | Безлимит |

## 📞 Поддержка

- 📧 Email: support@securitycheck.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: /docs

---

**Версия:** 1.0.0  
**Лицензия:** MIT  
**Автор:** SecurityCheck Team
