"""
Скрипт для перевода интерфейса с русского на немецкий
"""

# Словарь переводов
TRANSLATIONS = {
    # Общие
    'Войти': 'Anmelden',
    'Вход': 'Anmeldung',
    'Выход': 'Abmelden',
    'Регистрация': 'Registrierung',
    'Зарегистрироваться': 'Registrieren',
    'Настройки': 'Einstellungen',
    'Тарифы': 'Tarife',
    'Профиль': 'Profil',
    'Подписка': 'Abonnement',
    'Безопасность': 'Sicherheit',
    'Использование': 'Nutzung',
    'Статистика': 'Statistik',
    
    # Действия
    'Сохранить': 'Speichern',
    'Отменить': 'Abbrechen',
    'Удалить': 'Löschen',
    'Изменить': 'Ändern',
    'Обновить': 'Aktualisieren',
    'Загрузить': 'Laden',
    'Скачать': 'Herunterladen',
    'Экспортировать': 'Exportieren',
    'Поиск': 'Suche',
    'Фильтр': 'Filter',
    
    # Формы
    'Email': 'E-Mail',
    'Пароль': 'Passwort',
    'Имя': 'Name',
    'Фамилия': 'Nachname',
    'Компания': 'Unternehmen',
    'Телефон': 'Telefon',
    'Адрес': 'Adresse',
    'Город': 'Stadt',
    'Страна': 'Land',
    'Комментарий': 'Kommentar',
    'Сообщение': 'Nachricht',
    
    # Сканирование
    'Проверка сайтов': 'Website-Scan',
    'Проверка ссылок': 'Link-Check',
    'WiFi сканер': 'WiFi-Scanner',
    'WiFi Сканер': 'WiFi-Scanner',
    'Проверка домена': 'Domain-Prüfung',
    'Анализ домена': 'Domain-Analyse',
    'Сканирование': 'Scannen',
    'Запустить сканирование': 'Scan starten',
    'Начать проверку': 'Prüfung starten',
    'Результаты': 'Ergebnisse',
    'История': 'Verlauf',
    
    # Безопасность
    'Уязвимости': 'Sicherheitslücken',
    'Угрозы': 'Bedrohungen',
    'Безопасно': 'Sicher',
    'Опасно': 'Gefährlich',
    'Предупреждение': 'Warnung',
    'Критичный': 'Kritisch',
    'Высокий': 'Hoch',
    'Средний': 'Mittel',
    'Низкий': 'Niedrig',
    'SSL сертификат': 'SSL-Zertifikat',
    'Защищено': 'Geschützt',
    
    # Тарифы и подписка
    'Бесплатно': 'Kostenlos',
    'в месяц': 'pro Monat',
    'в год': 'pro Jahr',
    'Безлимитно': 'Unbegrenzt',
    'Лимит': 'Limit',
    'Текущий план': 'Aktueller Plan',
    'Перейти на': 'Wechseln zu',
    'Улучшить тариф': 'Plan upgraden',
    'Отменить подписку': 'Abonnement kündigen',
    
    # Сообщения
    'Спасибо': 'Danke',
    'Ошибка': 'Fehler',
    'Успешно': 'Erfolgreich',
    'Внимание': 'Achtung',
    'Информация': 'Information',
    'Загрузка': 'Lädt',
    'Подождите': 'Bitte warten',
    
    # Навигация
    'Главная': 'Startseite',
    'Дашборд': 'Dashboard',
    'Возможности': 'Funktionen',
    'Функции': 'Funktionen',
    'Поддержка': 'Support',
    'Документация': 'Dokumentation',
    'Контакты': 'Kontakt',
    'О нас': 'Über uns',
    
    # Время
    'Сегодня': 'Heute',
    'Вчера': 'Gestern',
    'Неделя': 'Woche',
    'Месяц': 'Monat',
    'Год': 'Jahr',
    'день': 'Tag',
    'дней': 'Tage',
    'часов': 'Stunden',
    'минут': 'Minuten',
    
    # Юридическое
    'Все права защищены': 'Alle Rechte vorbehalten',
    'Политика конфиденциальности': 'Datenschutzerklärung',
    'Условия использования': 'Nutzungsbedingungen',
    'Юридическая информация': 'Rechtliches',
    
    # Админ
    'Админ-панель': 'Admin-Panel',
    'Пользователи': 'Benutzer',
    'Администратор': 'Administrator',
    'Управление': 'Verwaltung',
    'Статистика использования': 'Nutzungsstatistik',
    
    # Портфолио
    'Наши проекты': 'Unsere Projekte',
    'Посмотреть': 'Ansehen',
    'Подробнее': 'Mehr erfahren',
    'Получить консультацию': 'Beratung erhalten',
    'Связаться с нами': 'Kontaktieren Sie uns',
    
    # Фразы
    'Простая и надёжная проверка безопасности для вашего бизнеса': 'Einfache und zuverlässige Sicherheitsprüfung für Ihr Unternehmen',
    'Войдите чтобы начать проверку безопасности': 'Melden Sie sich an, um mit der Sicherheitsprüfung zu beginnen',
    'Нет аккаунта?': 'Kein Konto?',
    'Забыли пароль?': 'Passwort vergessen?',
    'Запомнить меня': 'Angemeldet bleiben',
    'Введите пароль': 'Passwort eingeben',
    'Введите URL': 'URL eingeben',
    'Заполните все поля': 'Bitte füllen Sie alle Felder aus',
    'Почему SecurityCheck?': 'Warum SecurityCheck?',
    'Хотите защитить свой сайт?': 'Möchten Sie Ihre Website schützen?',
    'Обнаружены уязвимости?': 'Sicherheitslücken gefunden?',
}

print("Словарь переводов создан!")
print(f"Всего переводов: {len(TRANSLATIONS)}")
