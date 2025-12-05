# 🚀 Деплой SecurityCheck на Render.com

## Пошаговая инструкция

### 1. Подготовка Stripe

1. Зайдите на https://dashboard.stripe.com
2. Переключитесь в **Live Mode**
3. Создайте продукты и цены:
   - **STARTER Monthly**: €9.99/месяц
   - **STARTER Yearly**: €99.90/год
   - **PRO Monthly**: €29.99/месяц
   - **PRO Yearly**: €299.90/год
4. Скопируйте Price IDs (price_xxxxx)
5. Получите API ключи:
   - **Publishable key**: `Settings → API keys → Publishable key`
   - **Secret key**: `Settings → API keys → Secret key`
6. Настройте Webhook:
   - `Developers → Webhooks → Add endpoint`
   - URL: `https://your-app.onrender.com/webhook/stripe`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`
   - Скопируйте **Webhook Secret** (whsec_xxxxx)

---

### 2. Создание проекта на Render.com

#### A. PostgreSQL Database

1. Зайдите на https://render.com
2. **New → PostgreSQL**
3. Настройки:
   - **Name**: `securitycheck-db`
   - **Database**: `security_check_db`
   - **User**: `securitycheck`
   - **Region**: Frankfurt (или ближайший)
   - **Plan**: Starter ($7/месяц)
4. Нажмите **Create Database**
5. **Скопируйте Internal Database URL** (будет использован в веб-сервисе)

#### B. Web Service

1. **New → Web Service**
2. **Connect Repository**: `https://github.com/pilipandr770/SecurityCheck.git`
3. Настройки:
   - **Name**: `securitycheck` (или ваше название)
   - **Region**: Frankfurt (EU Central)
   - **Branch**: `main`
   - **Root Directory**: оставьте пустым
   - **Runtime**: `Python 3`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: Starter ($7/месяц)

---

### 3. Настройка Environment Variables

В разделе **Environment** добавьте:

```bash
# Flask
SECRET_KEY=<сгенерируйте длинную случайную строку>
FLASK_ENV=production
DEBUG=False

# Database (из шага 2A)
DATABASE_URL=postgresql://securitycheck:password@host:5432/security_check_db

# Stripe (из шага 1)
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Stripe Price IDs (из шага 1)
STRIPE_PRICE_STARTER_MONTHLY=price_xxxxx
STRIPE_PRICE_STARTER_YEARLY=price_xxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxx
STRIPE_PRICE_PRO_YEARLY=price_xxxxx

# Email (опционально, Gmail App Password)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@securitycheck.de

# AI (опционально, для расширенных объяснений)
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# App Settings
APP_NAME=SecurityCheck
DOMAIN=securitycheck.onrender.com
```

**Как сгенерировать SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

---

### 4. Deploy!

1. Нажмите **Create Web Service**
2. Render автоматически:
   - Клонирует репозиторий
   - Установит зависимости
   - Создаст таблицы БД
   - Запустит приложение
3. Процесс займет 5-10 минут

---

### 5. Создание Admin-аккаунта

После успешного деплоя:

1. Зайдите в **Shell** вашего веб-сервиса на Render
2. Выполните команды:

```bash
cd backend
python create_admin.py admin@securitycheck.de your-secure-password
```

3. Запишите данные для входа!

---

### 6. Проверка работы

1. Откройте ваш сайт: `https://securitycheck.onrender.com`
2. Проверьте страницы:
   - `/` - Главная (должен редирект на `/login`)
   - `/register` - Регистрация
   - `/login` - Вход
   - `/pricing` - Тарифы
   - `/impressum` - Impressum
   - `/datenschutz` - Datenschutz
   - `/agb` - AGB

3. Войдите как admin и проверьте:
   - Dashboard работает
   - Можно создать скан
   - Admin-панель доступна

---

### 7. Настройка Stripe Webhook (финализация)

1. Вернитесь в Stripe Dashboard → Webhooks
2. Обновите URL endpoint на реальный:
   - Было: `https://your-app.onrender.com/webhook/stripe`
   - Стало: `https://securitycheck.onrender.com/webhook/stripe`
3. Протестируйте webhook (Send test webhook)

---

### 8. Настройка Custom Domain (опционально)

Если у вас есть домен:

1. В Render: **Settings → Custom Domain**
2. Добавьте ваш домен: `securitycheck.de`
3. Следуйте инструкциям Render для настройки DNS
4. Обновите переменную `DOMAIN` в Environment Variables
5. Обновите Stripe Webhook URL

---

## 🔧 Troubleshooting

### Ошибка при Build

Проверьте логи Build в Render. Частые проблемы:
- **Зависимости не установились**: Проверьте `requirements.txt`
- **База данных недоступна**: Убедитесь, что `DATABASE_URL` правильный

### Ошибка 500 на сайте

1. Откройте **Logs** в Render
2. Ищите строки с `ERROR`
3. Частые причины:
   - Неправильный `SECRET_KEY`
   - Неверный `DATABASE_URL`
   - Отсутствуют таблицы в БД

Решение:
```bash
# В Shell Render
cd backend
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Stripe не работает

1. Проверьте, что используете **Live Mode** ключи (начинаются с `pk_live_` и `sk_live_`)
2. Убедитесь, что Price IDs правильные
3. Проверьте Webhook URL и Secret

---

## 📊 Мониторинг

### Render Dashboard
- **Metrics**: CPU, Memory, Response Time
- **Logs**: Real-time логи приложения
- **Events**: История деплоев

### PostgreSQL
- **Metrics**: Connections, Queries, Storage
- Бекапы создаются автоматически

---

## 💰 Стоимость

### Минимальная конфигурация:
- **Web Service (Starter)**: $7/месяц
- **PostgreSQL (Starter)**: $7/месяц
- **Итого**: $14/месяц (~€13/месяц)

### Рекомендуемая (для production):
- **Web Service (Standard)**: $25/месяц
- **PostgreSQL (Standard)**: $20/месяц
- **Итого**: $45/месяц (~€42/месяц)

---

## 🎉 Готово!

Ваш SecurityCheck теперь доступен по адресу:
**https://securitycheck.onrender.com**

### Следующие шаги:

1. ✅ Создайте тестовый аккаунт
2. ✅ Протестируйте регистрацию → FREE план
3. ✅ Протестируйте upgrade FREE → STARTER (с тестовой картой Stripe)
4. ✅ Проверьте все сканеры работают
5. ✅ Настройте Google Analytics (опционально)
6. ✅ Настройте мониторинг (UptimeRobot, Pingdom)

---

**📧 Поддержка:** andrii.it.info@gmail.com  
**📱 Телефон:** +49 160 95030120  

© 2024 Andrii Pylypchuk
