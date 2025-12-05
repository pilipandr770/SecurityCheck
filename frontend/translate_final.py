"""
Финальный скрипт для перевода оставшихся русских фраз
"""

import os
from pathlib import Path

# Финальные переводы
FINAL_TRANSLATIONS = {
    # Base.html
    'Комплексная проверка безопасности сайтов и файлов для бизнеса': 'Umfassende Sicherheitsprüfung von Websites und Dateien für Unternehmen',
    'Проверка безопасности': 'Sicherheitsprüfung',
    'Навигация': 'Navigation',
    'Панель управления': 'Dashboard',
    'Проверка сайта': 'Website-Prüfung',
    'Проверка ссылок': 'Link-Check',
    'WiFi сканер': 'WiFi-Scanner',
    'Админ-панель': 'Admin-Panel',
    'Тарифы': 'Tarife',
    'Настройки': 'Einstellungen',
    
    # WiFi scan
    'Найдите все устройства, подключенные к вашей Wi-Fi сети': 'Finden Sie alle Geräte, die mit Ihrem WiFi-Netzwerk verbunden sind',
    'Сканирование локальной сети': 'Lokales Netzwerk scannen',
    'Будут найдены все устройства подключенные к вашему роутеру': 'Alle mit Ihrem Router verbundenen Geräte werden gefunden',
    'Начать сканирование': 'Scan starten',
    'Прогресс': 'Fortschritt',
    'Сканирование...': 'Scannen...',
    'Сканирование завершено': 'Scan abgeschlossen',
    'Найдено устройств': 'Gefundene Geräte',
    'Обработка результатов': 'Ergebnisse werden verarbeitet',
    'Загрузка результатов': 'Ergebnisse werden geladen',
    
    # Web scan
    'Введите URL сайта': 'Geben Sie die Website-URL ein',
    'Запустить проверку': 'Prüfung starten',
    'Проверка безопасности сайта': 'Website-Sicherheitsprüfung',
    'Анализируем сайт': 'Website wird analysiert',
    'Проверяем SSL сертификат': 'SSL-Zertifikat wird geprüft',
    'Анализируем заголовки': 'Header werden analysiert',
    'Сканируем порты': 'Ports werden gescannt',
    'Проверяем уязвимости': 'Schwachstellen werden geprüft',
    'Создаем отчет': 'Bericht wird erstellt',
    
    # Link check
    'Проверка ссылки на фишинг': 'Link auf Phishing prüfen',
    'Введите ссылку': 'Link eingeben',
    'Проверить ссылку': 'Link prüfen',
    'Ссылка безопасна': 'Link ist sicher',
    'Опасная ссылка': 'Gefährlicher Link',
    'Подозрительная ссылка': 'Verdächtiger Link',
    
    # Domain lookup
    'Анализ домена': 'Domain-Analyse',
    'Введите домен': 'Domain eingeben',
    'Проверить домен': 'Domain prüfen',
    'Информация о домене': 'Domain-Informationen',
    'Регистратор': 'Registrar',
    'Дата регистрации': 'Registrierungsdatum',
    'Дата истечения': 'Ablaufdatum',
    
    # History
    'История проверок': 'Scan-Verlauf',
    'Удалить эту запись': 'Diesen Eintrag löschen',
    'Экспортировать': 'Exportieren',
    'Фильтровать': 'Filtern',
    'Все типы': 'Alle Typen',
    'За всё время': 'Gesamter Zeitraum',
    'За неделю': 'Letzte Woche',
    'За месяц': 'Letzter Monat',
    
    # Settings
    'Личная информация': 'Persönliche Informationen',
    'Полное имя': 'Vollständiger Name',
    'Название компании': 'Firmenname',
    'Номер телефона': 'Telefonnummer',
    'Текущий пароль': 'Aktuelles Passwort',
    'Новый пароль': 'Neues Passwort',
    'Подтвердите пароль': 'Passwort bestätigen',
    'Изменить пароль': 'Passwort ändern',
    'Удалить аккаунт': 'Konto löschen',
    'Использование ресурсов': 'Ressourcennutzung',
    'Осталось': 'Verbleibend',
    
    # Portfolio
    'Наши проекты': 'Unsere Projekte',
    'Обычный сайт': 'Normale Website',
    'Защищенный сайт': 'Geschützte Website',
    'Уязвимости найдены': 'Schwachstellen gefunden',
    'Защита на высшем уровне': 'Höchstes Schutzniveau',
    'Хотите защищенный сайт': 'Möchten Sie eine geschützte Website',
    'Заказать разработку': 'Entwicklung bestellen',
    'Получить консультацию': 'Beratung erhalten',
    'Отправить заявку': 'Anfrage senden',
    'Имя': 'Name',
    'Телефон': 'Telefon',
    'Тип проекта': 'Projekttyp',
    'Описание проекта': 'Projektbeschreibung',
    
    # Network scan
    'Сканирование сети': 'Netzwerk-Scan',
    'Найденные устройства': 'Gefundene Geräte',
    'MAC адрес': 'MAC-Adresse',
    'IP адрес': 'IP-Adresse',
    'Производитель': 'Hersteller',
    'Тип устройства': 'Gerätetyp',
    'Неизвестное устройство': 'Unbekanntes Gerät',
    'Открытые порты': 'Offene Ports',
}


def translate_file(file_path):
    """Переводит один файл"""
    print(f"Обрабатываю: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Применяем переводы
    for russian, german in sorted(FINAL_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
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
    
    # Все HTML файлы рекурсивно
    all_files = list(templates_dir.rglob('*.html'))
    
    translated_count = 0
    
    for file_path in all_files:
        if translate_file(file_path):
            translated_count += 1
    
    print(f"\n✓ Переведено файлов: {translated_count}/{len(all_files)}")


if __name__ == '__main__':
    main()
