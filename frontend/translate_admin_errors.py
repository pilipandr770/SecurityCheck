"""
Расширенный скрипт перевода для админских и error-страниц
"""

import os
from pathlib import Path

# Дополнительные переводы для админки и ошибок
ADMIN_TRANSLATIONS = {
    # Админка
    'Админ-панель': 'Admin-Panel',
    'Управление системой и пользователями': 'System- und Benutzerverwaltung',
    'Всего пользователей': 'Benutzer gesamt',
    'Активных': 'Aktiv',
    'Всего сканов': 'Scans gesamt',
    'За последние 30 дней': 'Letzte 30 Tage',
    'Опасные находки': 'Gefährliche Funde',
    'Опасных ссылок': 'Gefährliche Links',
    'Доход (месяц)': 'Einnahmen (Monat)',
    'в год': 'pro Jahr',
    
    'Пользователи по тарифам': 'Benutzer nach Tarifen',
    'Типы сканов': 'Scan-Typen',
    'Последние регистрации': 'Letzte Registrierungen',
    'Все пользователи': 'Alle Benutzer',
    
    'Веб-сканы': 'Web-Scans',
    'Количество сканов': 'Anzahl der Scans',
    'Домены': 'Domains',
    
    # Управление пользователями
    'Управление пользователями': 'Benutzerverwaltung',
    'Пользователи': 'Benutzer',
    'Фильтры и поиск': 'Filter und Suche',
    'Поиск': 'Suche',
    'Email, имя или фамилия': 'E-Mail, Vor- oder Nachname',
    'Тариф': 'Tarif',
    'Все тарифы': 'Alle Tarife',
    'Искать': 'Suchen',
    
    'Список пользователей': 'Benutzerliste',
    'Имя': 'Name',
    'Регистрация': 'Registrierung',
    'Активность': 'Aktivität',
    'Не входил': 'Nicht angemeldet',
    'Активен': 'Aktiv',
    'Заблокирован': 'Gesperrt',
    
    'Просмотр': 'Ansehen',
    'Удалить': 'Löschen',
    
    'Ошибка при обновлении тарифа': 'Fehler beim Aktualisieren des Tarifs',
    'Ошибка при обновлении статуса': 'Fehler beim Aktualisieren des Status',
    'Ошибка при удалении пользователя': 'Fehler beim Löschen des Benutzers',
    'Удалить пользователя': 'Benutzer löschen',
    'ВСЕ его данные будут удалены безвозвратно': 'ALLE seine Daten werden unwiderruflich gelöscht',
    
    # Страницы ошибок
    'Страница не найдена': 'Seite nicht gefunden',
    'Извините, запрашиваемая страница не существует': 'Entschuldigung, die angeforderte Seite existiert nicht',
    'Возможно, она была удалена или вы ввели неверный адрес': 'Möglicherweise wurde sie gelöscht oder Sie haben eine falsche Adresse eingegeben',
    'На главную': 'Zur Startseite',
    'Назад': 'Zurück',
    
    'Доступ запрещен': 'Zugriff verweigert',
    'У вас нет прав': 'Sie haben keine Berechtigung',
    'для доступа к этой странице': 'für den Zugriff auf diese Seite',
    'Свяжитесь с администратором': 'Kontaktieren Sie den Administrator',
    
    'Ошибка сервера': 'Server-Fehler',
    'Что-то пошло не так': 'Etwas ist schief gelaufen',
    'Мы уже работаем над исправлением': 'Wir arbeiten bereits an der Behebung',
    'Попробуйте обновить страницу': 'Versuchen Sie, die Seite neu zu laden',
    
    'Неверный запрос': 'Ungültige Anfrage',
    'Сервер не может обработать запрос': 'Der Server kann die Anfrage nicht verarbeiten',
    'Проверьте правильность данных': 'Überprüfen Sie die Richtigkeit der Daten',
}


def translate_file(file_path):
    """Переводит один файл"""
    print(f"Обрабатываю: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Применяем переводы
    for russian, german in sorted(ADMIN_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
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
    
    files_to_translate = [
        'admin/dashboard.html',
        'admin/users.html',
        'errors/400.html',
        'errors/403.html',
        'errors/404.html',
        'errors/500.html',
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
