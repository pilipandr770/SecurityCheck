# ✅ SecurityCheck - Чеклист деплоя на Render

## 📋 Быстрый старт (15 минут)

### 1. Stripe Setup (5 мин)
- [ ] Зайти на https://dashboard.stripe.com
- [ ] Переключиться в **Live Mode**
- [ ] Создать 4 продукта/цены:
  - [ ] STARTER Monthly (€9.99)
  - [ ] STARTER Yearly (€99.90)
  - [ ] PRO Monthly (€29.99)
  - [ ] PRO Yearly (€299.90)
- [ ] Скопировать Price IDs: `price_xxxxx`
- [ ] Скопировать API keys: `pk_live_xxxxx` и `sk_live_xxxxx`
- [ ] Создать Webhook → Events: checkout.session.completed, invoice.payment_succeeded, customer.subscription.deleted
- [ ] Скопировать Webhook Secret: `whsec_xxxxx`

---

### 2. Render.com Setup (5 мин)

#### PostgreSQL
- [ ] New → PostgreSQL
- [ ] Name: `securitycheck-db`
- [ ] Region: **Frankfurt**
- [ ] Plan: Starter ($7/мес)
- [ ] Create Database
- [ ] Скопировать **Internal Database URL**

#### Web Service
- [ ] New → Web Service
- [ ] Repository: `https://github.com/pilipandr770/SecurityCheck.git`
- [ ] Name: `securitycheck`
- [ ] Region: **Frankfurt**
- [ ] Branch: `main`
- [ ] Build Command: `chmod +x build.sh && ./build.sh`
- [ ] Start Command: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- [ ] Plan: Starter ($7/мес)

---

### 3. Environment Variables (3 мин)

Скопируйте и заполните:

```bash
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production
DEBUG=False
DATABASE_URL=<из PostgreSQL Internal URL>
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_STARTER_MONTHLY=price_xxxxx
STRIPE_PRICE_STARTER_YEARLY=price_xxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxx
STRIPE_PRICE_PRO_YEARLY=price_xxxxx
APP_NAME=SecurityCheck
DOMAIN=<your-app>.onrender.com
```

Опционально (Email):
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=<app-password>
```

---

### 4. Deploy (2 мин)
- [ ] Нажать **Create Web Service**
- [ ] Дождаться завершения деплоя (5-10 мин)
- [ ] Проверить логи на ошибки

---

### 5. Post-Deploy (5 мин)

#### Создать Admin
В Shell Render:
```bash
cd backend
python create_admin.py admin@securitycheck.de YourPassword123
```

#### Обновить Stripe Webhook
- [ ] Stripe Dashboard → Webhooks
- [ ] Изменить URL: `https://<your-app>.onrender.com/webhook/stripe`
- [ ] Test webhook

#### Проверить сайт
- [ ] https://<your-app>.onrender.com/login
- [ ] https://<your-app>.onrender.com/register
- [ ] https://<your-app>.onrender.com/pricing
- [ ] https://<your-app>.onrender.com/impressum
- [ ] Войти как admin → Dashboard
- [ ] Создать тестовый скан

---

## 🎯 Готово!

Ваш SecurityCheck запущен на:
**https://<your-app>.onrender.com**

### Тестовая карта Stripe:
- **Номер**: 4242 4242 4242 4242
- **Дата**: 12/34
- **CVC**: 123
- **ZIP**: 12345

---

## 🚨 Если что-то не работает

### Build Failed
```bash
# Проверьте requirements.txt
# Проверьте build.sh имеет права на выполнение
```

### Database Error
```bash
# В Shell Render:
cd backend
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### 500 Error
```bash
# Проверьте Logs в Render
# Убедитесь SECRET_KEY и DATABASE_URL правильные
```

---

**📧 Контакт:** andrii.it.info@gmail.com  
**📱 Телефон:** +49 160 95030120

Стоимость: **$14/месяц** (Web + Database)
