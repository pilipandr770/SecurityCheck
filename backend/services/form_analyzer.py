"""
Анализатор безопасности форм загрузки файлов
Поиск форм, проверка валидации, тестирование защиты
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class FormSecurityAnalyzer:
    """Анализатор безопасности форм загрузки файлов"""
    
    def __init__(self):
        self.results = []
    
    def analyze_page(self, html_content, base_url):
        """
        Анализировать страницу на наличие форм загрузки
        
        Args:
            html_content: HTML содержимое страницы
            base_url: Базовый URL для построения полных путей
            
        Returns:
            list: Список результатов анализа
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Находим все формы с полями загрузки файлов
            upload_forms = self.find_upload_forms(soup, base_url)
            
            if not upload_forms:
                results.append({
                    'category': 'forms',
                    'title': 'Формы загрузки не найдены',
                    'description': 'На странице нет форм для загрузки файлов',
                    'severity': 'info',
                    'raw_data': {'forms_found': 0}
                })
                return results
            
            # Анализируем каждую форму
            for form_data in upload_forms:
                # Проверяем JavaScript валидацию
                js_validation = self.analyze_js_validation(html_content, form_data)
                
                # Создаём результат для формы
                severity = self.determine_severity(form_data, js_validation)
                
                results.append({
                    'category': 'forms',
                    'title': f'Найдена форма загрузки файлов',
                    'description': self.generate_description(form_data, js_validation),
                    'severity': severity,
                    'evidence': f'Action: {form_data["action"]}, Method: {form_data["method"]}',
                    'raw_data': {
                        'form': form_data,
                        'js_validation': js_validation
                    }
                })
            
        except Exception as e:
            results.append({
                'category': 'forms',
                'title': 'Ошибка анализа форм',
                'description': f'Не удалось проанализировать формы: {str(e)}',
                'severity': 'low',
                'raw_data': {'error': str(e)}
            })
        
        return results
    
    def find_upload_forms(self, soup, base_url):
        """
        Найти все формы с полями загрузки файлов
        
        Args:
            soup: BeautifulSoup объект
            base_url: Базовый URL
            
        Returns:
            list: Список найденных форм
        """
        upload_forms = []
        
        forms = soup.find_all('form')
        
        for form in forms:
            # Ищем input type="file"
            file_inputs = form.find_all('input', {'type': 'file'})
            
            if file_inputs:
                form_data = {
                    'action': urljoin(base_url, form.get('action', '')),
                    'method': form.get('method', 'get').upper(),
                    'enctype': form.get('enctype', ''),
                    'file_inputs': [],
                    'has_proper_enctype': False
                }
                
                # Проверяем enctype
                if form_data['enctype'] == 'multipart/form-data':
                    form_data['has_proper_enctype'] = True
                
                # Собираем информацию о полях загрузки
                for file_input in file_inputs:
                    input_data = {
                        'name': file_input.get('name', 'unnamed'),
                        'accept': file_input.get('accept', ''),
                        'multiple': file_input.has_attr('multiple'),
                        'required': file_input.has_attr('required')
                    }
                    form_data['file_inputs'].append(input_data)
                
                upload_forms.append(form_data)
        
        return upload_forms
    
    def analyze_js_validation(self, html_content, form_data):
        """
        Анализ JavaScript валидации файлов
        
        Args:
            html_content: HTML содержимое
            form_data: Данные формы
            
        Returns:
            dict: Информация о валидации
        """
        validation_info = {
            'has_validation': False,
            'checks_extension': False,
            'checks_mime_type': False,
            'checks_file_size': False,
            'allowed_extensions': [],
            'max_file_size': None,
            'validation_level': 'NONE'
        }
        
        try:
            # Ищем JavaScript код валидации файлов
            # Паттерны для поиска валидации
            
            # Проверка расширения
            extension_patterns = [
                r'\.split\(["\']\.["\']\)\.pop\(\)',
                r'\.toLowerCase\(\)\.match\(',
                r'allowedExtensions\s*=\s*\[(.*?)\]',
                r'\.endsWith\(["\']\.([a-z]+)["\']\)',
                r'accept\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in extension_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    validation_info['checks_extension'] = True
                    validation_info['has_validation'] = True
                    
                    # Пытаемся извлечь разрешённые расширения
                    match = re.search(r'allowedExtensions\s*=\s*\[(.*?)\]', html_content)
                    if match:
                        extensions = re.findall(r'["\']([a-z0-9]+)["\']', match.group(1))
                        validation_info['allowed_extensions'] = extensions
                    break
            
            # Проверка MIME type
            mime_patterns = [
                r'\.type\s*[!=]=',
                r'allowedMimeTypes',
                r'file\.type\.match\(',
                r'application/|image/|video/|audio/'
            ]
            
            for pattern in mime_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    validation_info['checks_mime_type'] = True
                    validation_info['has_validation'] = True
                    break
            
            # Проверка размера файла
            size_patterns = [
                r'\.size\s*>',
                r'maxFileSize',
                r'file\.size\s*[<>]=?\s*(\d+)',
                r'1024\s*\*\s*1024'  # MB в байтах
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    validation_info['checks_file_size'] = True
                    validation_info['has_validation'] = True
                    
                    # Пытаемся извлечь максимальный размер
                    size_match = re.search(r'(\d+)\s*\*\s*1024\s*\*\s*1024', html_content)
                    if size_match:
                        validation_info['max_file_size'] = int(size_match.group(1))
                    break
            
            # Определяем уровень валидации
            if validation_info['checks_extension'] and validation_info['checks_mime_type'] and validation_info['checks_file_size']:
                validation_info['validation_level'] = 'HIGH'
            elif validation_info['checks_extension'] and (validation_info['checks_mime_type'] or validation_info['checks_file_size']):
                validation_info['validation_level'] = 'MEDIUM'
            elif validation_info['has_validation']:
                validation_info['validation_level'] = 'LOW'
            
        except Exception:
            pass
        
        return validation_info
    
    def check_upload_directory_security(self, base_url, form_action):
        """
        Проверка безопасности директории загрузки (ОПАСНО - реальные запросы!)
        Эта функция выполняет реальные тесты и должна использоваться осторожно
        
        Args:
            base_url: Базовый URL сайта
            form_action: Action URL формы
            
        Returns:
            dict: Результаты проверки
        """
        # В MVP версии эту функцию лучше НЕ вызывать автоматически
        # Она может быть опасной и нарушать законы о несанкционированном доступе
        
        return {
            'status': 'NOT_TESTED',
            'message': 'Активное тестирование отключено в целях безопасности',
            'recommendations': [
                'Убедитесь что загруженные файлы не могут быть выполнены',
                'Используйте .htaccess для запрета выполнения скриптов',
                'Храните загруженные файлы вне веб-корня',
                'Проверяйте MIME type на сервере, не доверяйте клиенту'
            ]
        }
    
    def determine_severity(self, form_data, js_validation):
        """
        Определить уровень критичности для формы
        
        Args:
            form_data: Данные формы
            js_validation: Информация о валидации
            
        Returns:
            str: Уровень критичности
        """
        # Критично если:
        # - Нет enctype multipart/form-data
        # - Используется GET метод для загрузки
        if not form_data['has_proper_enctype']:
            return 'high'
        
        if form_data['method'] == 'GET':
            return 'high'
        
        # Высокий риск если нет валидации
        if js_validation['validation_level'] == 'NONE':
            return 'high'
        
        # Средний риск если слабая валидация
        if js_validation['validation_level'] == 'LOW':
            return 'medium'
        
        # Низкий риск если есть хорошая валидация
        if js_validation['validation_level'] in ['MEDIUM', 'HIGH']:
            return 'low'
        
        return 'medium'
    
    def generate_description(self, form_data, js_validation):
        """
        Сгенерировать описание для результата
        
        Args:
            form_data: Данные формы
            js_validation: Информация о валидации
            
        Returns:
            str: Описание
        """
        issues = []
        
        if not form_data['has_proper_enctype']:
            issues.append('отсутствует enctype="multipart/form-data"')
        
        if form_data['method'] == 'GET':
            issues.append('используется GET метод (должен быть POST)')
        
        if js_validation['validation_level'] == 'NONE':
            issues.append('отсутствует JavaScript валидация файлов')
        elif js_validation['validation_level'] == 'LOW':
            issues.append('слабая JavaScript валидация')
        
        if not js_validation['checks_extension']:
            issues.append('не проверяется расширение файла')
        
        if not js_validation['checks_mime_type']:
            issues.append('не проверяется MIME type')
        
        if not js_validation['checks_file_size']:
            issues.append('не проверяется размер файла')
        
        if issues:
            return f'Форма загрузки файлов имеет проблемы: {"; ".join(issues)}'
        else:
            return 'Форма загрузки файлов имеет базовую защиту на клиенте'
