"""
Скрипт для массового перевода HTML-файлов с русского на немецкий
"""

import os
import re
from pathlib import Path

# Словарь переводов (основные фразы)
TRANSLATIONS = {
    # Заголовки и названия
    'Панель управления': 'Dashboard',
    'Добро пожаловать': 'Willkommen',
    'Ваш тариф': 'Ihr Tarif',
    
    # Сканирование
    'Проверки безопасности сайтов': 'Website-Sicherheitsprüfungen',
    'Сканирование Wi-Fi сети': 'WiFi-Netzwerk-Scan',
    'Проверка безопасности сайта': 'Website-Sicherheitsprüfung',
    'Сканер Wi-Fi сети': 'WiFi-Netzwerk-Scanner',
    '📡 Сканирование WiFi': 'WiFi-Scan',
    
    # Статус и действия
    'Доступно сегодня': 'Heute verfügbar',
    'Основные функции': 'Hauptfunktionen',
    'Полный аудит уязвимостей': 'Vollständiges Schwachstellen-Audit',
    'Узнайте какие устройства подключены': 'Erfahren Sie, welche Geräte verbunden sind',
    
    # Список устройств
    'Телефоны': 'Smartphones',
    'Компьютеры': 'Computer',
    'Роутеры': 'Router',
    'Камеры': 'Kameras',
    'Неизвестные': 'Unbekannt',
    
    # Графики
    'Активность за последние 7 дней': 'Aktivität der letzten 7 Tage',
    'Распределение проверок': 'Scan-Verteilung',
    'Проверки сайтов': 'Website-Scans',
    
    # Таблица
    'Последние проверки': 'Letzte Scans',
    'Посмотреть все': 'Alle ansehen',
    'Тип': 'Typ',
    'Цель': 'Ziel',
    'Статус': 'Status',
    'Оценка': 'Bewertung',
    'Дата': 'Datum',
    'Действия': 'Aktionen',
    'Завершено': 'Abgeschlossen',
    'Обработка': 'In Bearbeitung',
    'Ошибка': 'Fehler',
    'Просмотр': 'Ansehen',
    
    # Пусто
    'Пока нет выполненных проверок': 'Noch keine Scans durchgeführt',
    'Начните с проверки вашего первого сайта': 'Starten Sie mit der Prüfung Ihrer ersten Website',
    
    # Тарифы
    'Улучшите тариф': 'Plan upgraden',
    'для получения больше проверок': 'um mehr Scans zu erhalten',
    'Посмотреть тарифы': 'Tarife ansehen',
    
    # Общее
    'ГЛАВНАЯ ФУНКЦИЯ': 'HAUPTFUNKTION',
    'ДОПОЛНИТЕЛЬНО': 'ZUSÄTZLICH',
    
    # Тарифы (pricing.html)
    'Выберите подходящий тариф': 'Wählen Sie den passenden Tarif',
    'Проверяйте безопасность своих сайтов': 'Überprüfen Sie die Sicherheit Ihrer Websites',
    'Помочь найти уязвимости': 'Helfen Sie, Schwachstellen zu finden',
    'Ежемесячно': 'Monatlich',
    'Ежегодно': 'Jährlich',
    'Скидка 17%': '17% Rabatt',
    
    'Навсегда бесплатно': 'Für immer kostenlos',
    'проверок сайтов в месяц': 'Website-Scans pro Monat',
    'проверок ссылок в месяц': 'Link-Checks pro Monat',
    'WiFi-сканирований в месяц': 'WiFi-Scans pro Monat',
    'проверок доменов в месяц': 'Domain-Prüfungen pro Monat',
    'Базовый отчет о безопасности': 'Basis-Sicherheitsbericht',
    'История проверок': 'Scan-Verlauf',
    'дней': 'Tage',
    'PDF-экспорт отчетов': 'PDF-Export von Berichten',
    'Email-уведомления': 'E-Mail-Benachrichtigungen',
    'Текущий план': 'Aktueller Plan',
    'Перейти на Free': 'Zu Free wechseln',
    
    'Популярный': 'Beliebt',
    'в месяц': 'pro Monat',
    'в год': 'pro Jahr',
    '∞ Безлимитные': '∞ Unbegrenzt',
    'Безлимитные': 'Unbegrenzt',
    'Безлимитная': 'Unbegrenzter',
    'Безлимитно': 'Unbegrenzt',
    'Расширенный отчет с рекомендациями': 'Erweiterter Bericht mit Empfehlungen',
    'Email-уведомления об угрозах': 'E-Mail-Benachrichtigungen bei Bedrohungen',
    'API доступ': 'API-Zugriff',
    'Перейти на Starter': 'Zu Starter wechseln',
    'Понизить до Starter': 'Zu Starter downgraden',
    
    'Лучший выбор для бизнеса': 'Beste Wahl für Unternehmen',
    'Всё из плана Starter': 'Alles aus dem Starter-Plan',
    'Безлимитная история проверок': 'Unbegrenzter Scan-Verlauf',
    'API доступ для интеграций': 'API-Zugriff für Integrationen',
    'White-label отчеты': 'White-Label-Berichte',
    'Консультация эксперта': 'Experten-Beratung',
    'час/месяц': 'Stunde/Monat',
    'Анализ архитектуры безопасности': 'Sicherheitsarchitektur-Analyse',
    'Рекомендации по защите': 'Schutzempfehlungen',
    'Приоритетная поддержка': 'Prioritäts-Support',
    'Перейти на Pro': 'Zu Pro upgraden',
    
    # Сравнение
    'Сравнение тарифов': 'Tarif-Vergleich',
    'Функция': 'Funktion',
    'Сканирование сайтов': 'Website-Scans',
    'Проверка ссылок': 'Link-Checks',
    'Анализ файлов': 'Datei-Analyse',
    'Проверка доменов': 'Domain-Prüfungen',
    'Максимальный размер файла': 'Maximale Dateigröße',
    'AI объяснения': 'KI-Erklärungen',
    'Приоритет': 'Priorität',
    'Поддержка': 'Support',
    'Форум': 'Forum',
    'Email': 'E-Mail',
    
    # FAQ
    'Частые вопросы': 'Häufig gestellte Fragen',
    'Можно ли отменить подписку?': 'Kann ich das Abonnement kündigen?',
    'Да, вы можете отменить подписку в любой момент': 'Ja, Sie können das Abonnement jederzeit kündigen',
    'После отмены вы сохраните доступ до конца оплаченного периода': 'Nach der Kündigung behalten Sie den Zugriff bis zum Ende des bezahlten Zeitraums',
    'Какие методы оплаты принимаются?': 'Welche Zahlungsmethoden werden akzeptiert?',
    'Мы принимаем все основные кредитные карты': 'Wir akzeptieren alle gängigen Kreditkarten',
    'через безопасный платежный шлюз Stripe': 'über das sichere Zahlungsgateway Stripe',
    'Можно ли изменить план?': 'Kann ich den Plan ändern?',
    'Да, вы можете повышать или понижать план в любое время': 'Ja, Sie können Ihren Plan jederzeit upgraden oder downgraden',
    'При повышении будет пропорциональная оплата': 'Bei einem Upgrade erfolgt eine anteilige Abrechnung',
    'Есть ли возврат средств?': 'Gibt es eine Geld-zurück-Garantie?',
    'Да, мы предлагаем 14-дневную гарантию возврата': 'Ja, wir bieten eine 14-tägige Geld-zurück-Garantie',
    'без вопросов': 'ohne Fragen',
}


def translate_file(file_path):
    """Переводит один HTML-файл"""
    print(f"Обрабатываю: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Применяем переводы
    for russian, german in sorted(TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        content = content.replace(russian, german)
    
    # Сохраняем только если были изменения
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Переведен: {file_path}")
        return True
    else:
        print(f"○ Без изменений: {file_path}")
        return False


def main():
    """Основная функция"""
    templates_dir = Path(__file__).parent / 'templates'
    
    if not templates_dir.exists():
        print(f"Директория не найдена: {templates_dir}")
        return
    
    # Список файлов для перевода
    files_to_translate = [
        'dashboard.html',
        'pricing.html',
        'settings.html',
        'web_scan.html',
        'link_check.html',
        'wifi_scan.html',
        'domain_lookup.html',
        'network_scan.html',
        'portfolio.html',
        'history.html',
    ]
    
    translated_count = 0
    
    for filename in files_to_translate:
        file_path = templates_dir / filename
        if file_path.exists():
            if translate_file(file_path):
                translated_count += 1
        else:
            print(f"✗ Не найден: {file_path}")
    
    print(f"\n✓ Переведено файлов: {translated_count}/{len(files_to_translate)}")


if __name__ == '__main__':
    main()
