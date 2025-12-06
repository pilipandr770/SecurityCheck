"""
AI объяснения результатов
Использует OpenAI или Anthropic для генерации понятных объяснений
"""

import os
from typing import Dict, List
from .vulnerability_knowledge import VulnerabilityKnowledge


class AIExplainer:
    """AI ассистент для объяснения результатов сканирования"""
    
    def __init__(self, provider=None, api_key=None):
        """
        Инициализация
        
        Args:
            provider: 'openai' или 'anthropic'
            api_key: API ключ
        """
        self.provider = provider or os.environ.get('AI_PROVIDER', 'anthropic')
        
        if self.provider == 'openai':
            self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        else:
            self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    
    def generate_scan_summary(self, results: List[Dict], domain: str, language: str = 'de') -> Dict:
        """
        Сгенерировать резюме сканирования
        
        Args:
            results: Список результатов сканирования
            domain: Домен
            language: Язык ('de' или 'ru')
            
        Returns:
            dict: Резюме и рекомендации
        """
        if not self.api_key:
            return self._generate_simple_summary(results, domain)
        
        # Группируем результаты по severity
        critical = [r for r in results if r.get('severity') == 'critical']
        high = [r for r in results if r.get('severity') == 'high']
        medium = [r for r in results if r.get('severity') == 'medium']
        
        if language == 'de':
            prompt = f"""Du bist ein Cybersicherheitsexperte. Erkläre die Scan-Ergebnisse der Website {domain} in einfacher Sprache für einen Geschäftsinhaber (keine technische Person).

Gefundene Probleme:
- Kritisch: {len(critical)}
- Hoch: {len(high)}
- Mittel: {len(medium)}

Problemdetails:
"""
        else:
            prompt = f"""Ты - эксперт по кибербезопасности. Объясни результаты сканирования сайта {domain} простым языком для владельца бизнеса (не технического специалиста).

Найдено проблем:
- Критических: {len(critical)}
- Высоких: {len(high)}
- Средних: {len(medium)}

Детали проблем:
"""
        
        # Добавляем топ-5 самых серьёзных проблем
        top_issues = critical[:3] + high[:2]
        for issue in top_issues:
            prompt += f"\n- {issue.get('title')}: {issue.get('description', '')}"
        
        if language == 'de':
            prompt += "\n\nSchreibe eine kurze Zusammenfassung (2-3 Sätze) auf Deutsch über den Sicherheitszustand der Website und gib 3-5 konkrete Empfehlungen, was zuerst behoben werden sollte."
        else:
            prompt += "\n\nНапиши краткое резюме (2-3 предложения) на русском языке о состоянии безопасности сайта и дай 3-5 конкретных рекомендаций что нужно исправить в первую очередь."
        
        try:
            if self.provider == 'openai':
                response = self._call_openai(prompt, language)
            else:
                response = self._call_anthropic(prompt)
            
            # Парсим ответ
            parts = response.split('\n\n')
            summary = parts[0] if parts else response
            recommendations = '\n'.join(parts[1:]) if len(parts) > 1 else ''
            
            return {
                'summary': summary,
                'recommendations': recommendations
            }
        
        except Exception as e:
            return self._generate_simple_summary(results, domain, language)
    
    def explain_vulnerability(self, vuln_type: str, details: str, severity: str, language: str = 'ru', verified: bool = False) -> Dict:
        """
        Объяснить уязвимость простым языком используя базу знаний
        
        Args:
            vuln_type: Тип уязвимости
            details: Детали
            severity: Уровень критичности
            language: Язык ('ru' или 'de')
            verified: Верифицирован ли пользователь
            
        Returns:
            dict: Объяснение с видео и инструкциями
        """
        # Сначала пробуем найти в базе знаний
        vuln_info = VulnerabilityKnowledge.get_vulnerability_info(vuln_type, language, verified)
        
        if vuln_info:
            # У нас есть готовое объяснение!
            return vuln_info
        
        # Если нет в базе - используем AI или простое объяснение
        if not self.api_key:
            solution_text = 'Wir empfehlen, einen Sicherheitsspezialisten zu konsultieren.' if language == 'de' else 'Рекомендуется обратиться к специалисту по безопасности.'
            return {
                'type': vuln_type,
                'name': vuln_type.replace('_', ' ').title(),
                'severity': severity,
                'explanation': self._simple_explanation(vuln_type, severity, language),
                'solution': solution_text,
                'video': None
            }
        
        if language == 'de':
            prompt = f"""Erkläre einem Kleinunternehmer (kein Techniker) in einfacher Sprache, was "{vuln_type}" ist.

Details: {details}

Gefahrenstufe: {severity}

Schreibe auf Deutsch:
1. Was ist das? (1-2 Sätze)
2. Warum ist es gefährlich für das Geschäft? (1-2 Sätze)
3. Wie kann man es beheben? (konkrete Schritte)

Verwende einfache Wörter, vermeide technischen Jargon."""
        else:
            prompt = f"""Объясни простым языком владельцу малого бизнеса (не технарю) что такое "{vuln_type}".

Детали: {details}

Уровень опасности: {severity}

Напиши на русском языке:
1. Что это такое (1-2 предложения)
2. Чем это опасно для бизнеса (1-2 предложения)
3. Как это исправить (конкретные шаги)

Используй простые слова, избегай технического жаргона."""
        
        try:
            if self.provider == 'openai':
                explanation_text = self._call_openai(prompt, language)
            else:
                explanation_text = self._call_anthropic(prompt)
            
            solution_text = 'Siehe Erklärung oben' if language == 'de' else 'См. объяснение выше'
            return {
                'type': vuln_type,
                'name': vuln_type.replace('_', ' ').title(),
                'severity': severity,
                'explanation': explanation_text,
                'solution': solution_text,
                'video': None
            }
        except Exception:
            solution_text = 'Wir empfehlen, einen Sicherheitsspezialisten zu konsultieren.' if language == 'de' else 'Рекомендуется обратиться к специалисту.'
            return {
                'type': vuln_type,
                'name': vuln_type.replace('_', ' ').title(),
                'severity': severity,
                'explanation': self._simple_explanation(vuln_type, severity, language),
                'solution': solution_text,
                'video': None
            }
    
    def explain_file_threat(self, filename: str, analysis_result: Dict, language: str = 'de') -> Dict:
        """
        Объяснить угрозу в файле
        
        Args:
            filename: Имя файла
            analysis_result: Результаты анализа
            language: Язык ('de' или 'ru')
            
        Returns:
            dict: Объяснение и рекомендация
        """
        is_dangerous = analysis_result.get('is_dangerous', False)
        is_suspicious = analysis_result.get('is_suspicious', False)
        issues = analysis_result.get('issues', [])
        
        if not self.api_key or not (is_dangerous or is_suspicious):
            if is_dangerous:
                return {
                    'explanation': f'Файл {filename} содержит вредоносное ПО и опасен для вашего компьютера.',
                    'recommendation': 'НЕ ОТКРЫВАЙТЕ этот файл. Немедленно удалите его.'
                }
            elif is_suspicious:
                return {
                    'explanation': f'Файл {filename} имеет подозрительные характеристики.',
                    'recommendation': 'Будьте осторожны. Не открывайте файл если вы не уверены в его происхождении.'
                }
            else:
                return {
                    'explanation': f'Файл {filename} выглядит безопасным.',
                    'recommendation': 'Проверки не выявили очевидных угроз, но всегда будьте осторожны с незнакомыми файлами.'
                }
        
        if language == 'de':
            prompt = f"""Die Datei "{filename}" wurde auf Viren und Bedrohungen analysiert.

Ergebnisse:
- Gefährlich: {'Ja' if is_dangerous else 'Nein'}
- Verdächtig: {'Ja' if is_suspicious else 'Nein'}

Gefundene Probleme:
{chr(10).join([f'- {issue}' for issue in issues])}

Erkläre dem Geschäftsinhaber auf einfachem Deutsch:
1. Ist diese Datei sicher? (2-3 Sätze)
2. Sollte man sie öffnen? (klare Empfehlung)"""
        else:
            prompt = f"""Файл "{filename}" был проанализирован на вирусы и угрозы.

Результаты:
- Опасный: {'Да' if is_dangerous else 'Нет'}
- Подозрительный: {'Да' if is_suspicious else 'Нет'}

Обнаруженные проблемы:
{chr(10).join([f'- {issue}' for issue in issues])}

Объясни владельцу бизнеса на простом русском языке:
1. Безопасен ли этот файл (2-3 предложения)
2. Стоит ли его открывать (чёткая рекомендация)"""
        
        try:
            if self.provider == 'openai':
                response = self._call_openai(prompt, language)
            else:
                response = self._call_anthropic(prompt)
            
            parts = response.split('\n\n')
            explanation = parts[0] if parts else response
            recommendation = parts[1] if len(parts) > 1 else 'Будьте осторожны с этим файлом.'
            
            return {
                'explanation': explanation,
                'recommendation': recommendation
            }
        
        except Exception:
            return {
                'explanation': f'Анализ файла {filename} выявил {"серьёзные проблемы" if is_dangerous else "подозрительные признаки" if is_suspicious else "отсутствие явных угроз"}.',
                'recommendation': 'Не открывайте файл.' if is_dangerous else 'Будьте осторожны.' if is_suspicious else 'Файл выглядит безопасным.'
            }
    
    def explain_link_danger(self, url: str, check_result: Dict, language: str = 'de') -> str:
        """
        Объяснить опасность ссылки
        
        Args:
            url: URL
            check_result: Результаты проверки
            language: Язык ('de' или 'ru')
            
        Returns:
            str: Объяснение
        """
        is_dangerous = check_result.get('is_dangerous', False)
        is_suspicious = check_result.get('is_suspicious', False)
        reasons = check_result.get('reasons', [])
        
        if not self.api_key:
            if is_dangerous:
                return f'Ссылка {url} опасна! Не переходите по ней. Причины: {", ".join(reasons)}'
            elif is_suspicious:
                return f'Ссылка {url} подозрительна. Будьте осторожны. Причины: {", ".join(reasons)}'
            else:
                return f'Ссылка {url} выглядит безопасной.'
        
        if language == 'de':
            prompt = f"""Der Link wurde analysiert: {url}

Überprüfungsergebnisse:
- Gefährlich: {'Ja' if is_dangerous else 'Nein'}
- Verdächtig: {'Ja' if is_suspicious else 'Nein'}

Gründe:
{chr(10).join([f'- {reason}' for reason in reasons])}

Erkläre dem Geschäftsinhaber auf einfachem Deutsch:
1. Ist dieser Link sicher? (2-3 Sätze)
2. Kann man darauf klicken? (klare Antwort)
3. Welche Risiken gibt es beim Klicken?"""
        else:
            prompt = f"""Проанализирована ссылка: {url}

Результаты проверки:
- Опасная: {'Да' if is_dangerous else 'Нет'}
- Подозрительная: {'Да' if is_suspicious else 'Нет'}

Причины:
{chr(10).join([f'- {reason}' for reason in reasons])}

Объясни на простом русском языке владельцу бизнеса:
1. Безопасна ли эта ссылка (2-3 предложения)
2. Можно ли по ней переходить (чёткий ответ)
3. Какие риски если перейти"""
        
        try:
            if self.provider == 'openai':
                return self._call_openai(prompt, language)
            else:
                return self._call_anthropic(prompt)
        except Exception:
            status = 'опасна' if is_dangerous else 'подозрительна' if is_suspicious else 'безопасна'
            return f'Ссылка {status}. {" ".join(reasons[:2])}'
    
    def generate_domain_summary(self, domain: str, intel: Dict, language: str = 'de') -> str:
        """
        Сгенерировать резюме по домену
        
        Args:
            domain: Домен
            intel: Информация о домене
            language: Язык ('de' или 'ru')
            
        Returns:
            str: Резюме
        """
        age_days = intel.get('domain_age_days')
        reputation = intel.get('reputation_score')
        email_sec = intel.get('email_security', {})
        
        if not self.api_key:
            return f'Домен {domain} зарегистрирован {age_days} дней назад. Репутация: {reputation}/100. Email безопасность: {email_sec.get("score", 0)}/100.'
        
        if language == 'de':
            prompt = f"""Die Domain wurde analysiert: {domain}

Informationen:
- Alter: {age_days} Tage
- Reputation: {reputation}/100
- E-Mail-Sicherheit (SPF/DKIM/DMARC): {email_sec.get('score', 0)}/100
- SPF: {'Ja' if email_sec.get('has_spf') else 'Nein'}
- DMARC: {'Ja' if email_sec.get('has_dmarc') else 'Nein'}

Schreibe eine kurze Zusammenfassung (3-4 Sätze) auf Deutsch über die Zuverlässigkeit dieser Domain für einen Geschäftsinhaber."""
        else:
            prompt = f"""Проанализирован домен: {domain}

Информация:
- Возраст: {age_days} дней
- Репутация: {reputation}/100
- Email безопасность (SPF/DKIM/DMARC): {email_sec.get('score', 0)}/100
- SPF: {'Да' if email_sec.get('has_spf') else 'Нет'}
- DMARC: {'Да' if email_sec.get('has_dmarc') else 'Нет'}

Напиши краткое резюме (3-4 предложения) на русском языке о надёжности этого домена для владельца бизнеса."""
        
        try:
            if self.provider == 'openai':
                return self._call_openai(prompt, language)
            else:
                return self._call_anthropic(prompt)
        except Exception:
            return f'Домен {domain} имеет репутацию {reputation}/100 баллов и возраст {age_days} дней.'
    
    def explain_network_scan(self, target: str, scan_results: Dict) -> Dict:
        """
        Сгенерировать объяснение по результатам сетевого сканирования
        
        Args:
            target: Цель сканирования (IP или домен)
            scan_results: Результаты сканирования
            
        Returns:
            Dict: С ключами explanation и recommendation
        """
        open_ports = scan_results.get('open_ports', [])
        vulnerabilities = scan_results.get('vulnerabilities', [])
        os = scan_results.get('os_detection', 'Неизвестно')
        
        if not self.api_key:
            return {
                'explanation': f'Найдено {len(open_ports)} открытых портов. Обнаружено уязвимостей: {len(vulnerabilities)}.',
                'recommendation': 'Рекомендуется закрыть неиспользуемые порты и обновить ПО.'
            }
        
        # Формируем список портов
        ports_list = ', '.join([f"{p['port']} ({p['service']})" for p in open_ports[:10]])
        if len(open_ports) > 10:
            ports_list += f' и ещё {len(open_ports) - 10} портов'
        
        # Формируем список уязвимостей
        vuln_list = []
        for v in vulnerabilities:
            vuln_list.append(f"- {v.get('service')} ({v.get('severity')}): {v.get('description')}")
        vuln_text = '\n'.join(vuln_list[:5])
        
        prompt = f"""Выполнено сетевое сканирование цели: {target}

Результаты:
- Открыто портов: {len(open_ports)}
- Список портов: {ports_list}
- Определённая ОС: {os}
- Найдено уязвимостей: {len(vulnerabilities)}

Обнаруженные уязвимости:
{vuln_text if vuln_text else 'Критических уязвимостей не обнаружено'}

Объясни владельцу бизнеса (не техническому специалисту):
1. Насколько безопасна эта конфигурация (2-3 предложения)
2. Какие риски существуют
3. Дай 3-5 конкретных рекомендаций что нужно исправить в первую очередь"""
        
        try:
            if self.provider == 'openai':
                result = self._call_openai(prompt)
            else:
                result = self._call_anthropic(prompt)
            
            # Разделяем на объяснение и рекомендации
            parts = result.split('\n\n')
            if len(parts) >= 2:
                explanation = parts[0]
                recommendation = '\n\n'.join(parts[1:])
            else:
                explanation = result
                recommendation = 'Проконсультируйтесь со специалистом по безопасности.'
            
            return {
                'explanation': explanation,
                'recommendation': recommendation
            }
        except Exception as e:
            logger.error(f'AI explanation error: {e}')
            return {
                'explanation': f'Найдено {len(open_ports)} открытых портов и {len(vulnerabilities)} уязвимостей.',
                'recommendation': 'Рекомендуется провести аудит безопасности.'
            }
    
    def _call_openai(self, prompt: str, language: str = 'de') -> str:
        """Вызов OpenAI API"""
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_key)
        
        system_message = "Du bist ein Cybersicherheitsexperte, der komplexe Dinge in einfacher Sprache für Geschäftsinhaber erklärt." if language == 'de' else "Ты - эксперт по кибербезопасности, который объясняет сложные вещи простым языком для владельцев бизнеса."
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Вызов Anthropic API"""
        from anthropic import Anthropic
        
        client = Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    def _generate_simple_summary(self, results: List[Dict], domain: str, language: str = 'de') -> Dict:
        """Простое резюме без AI"""
        critical = sum(1 for r in results if r.get('severity') == 'critical')
        high = sum(1 for r in results if r.get('severity') == 'high')
        medium = sum(1 for r in results if r.get('severity') == 'medium')
        
        if language == 'de':
            if critical > 0:
                summary = f'Schwerwiegende Sicherheitsprobleme auf der Website {domain} gefunden. Sofortiges Handeln erforderlich!'
            elif high > 0:
                summary = f'Auf der Website {domain} wurden wichtige Sicherheitsprobleme gefunden, die behoben werden müssen.'
            elif medium > 0:
                summary = f'Die Website {domain} hat mehrere Sicherheitsprobleme mittlerer Wichtigkeit.'
            else:
                summary = f'Die Website {domain} hat grundlegenden Schutz, aber es gibt Verbesserungsmöglichkeiten.'
            
            recommendations = 'Wir empfehlen, einen Sicherheitsspezialisten zu konsultieren, um die gefundenen Probleme zu beheben.'
        else:
            if critical > 0:
                summary = f'Обнаружены серьёзные проблемы безопасности на сайте {domain}. Требуется немедленное вмешательство!'
            elif high > 0:
                summary = f'На сайте {domain} найдены важные проблемы безопасности, которые нужно исправить.'
            elif medium > 0:
                summary = f'Сайт {domain} имеет несколько проблем безопасности средней важности.'
            else:
                summary = f'Сайт {domain} имеет базовую защиту, но есть возможности для улучшения.'
            
            recommendations = 'Рекомендуем обратиться к специалисту по безопасности для устранения найденных проблем.'
        
        return {'summary': summary, 'recommendations': recommendations}
    
    def _simple_explanation(self, vuln_type: str, severity: str, language: str = 'de') -> str:
        """Простое объяснение без AI"""
        if language == 'de':
            explanations = {
                'ssl': 'Probleme mit dem SSL-Zertifikat können es Angreifern ermöglichen, Benutzerdaten abzufangen.',
                'headers': 'Fehlende Sicherheitsheader machen die Website anfällig für verschiedene Angriffe.',
                'forms': 'Unsichere Datei-Upload-Formulare können das Hochladen von Malware auf den Server ermöglichen.',
                'cookies': 'Unsichere Cookies können von Angreifern gestohlen werden.',
                'html': 'Sicherheitsproblem gefunden, das behoben werden muss.'
            }
        else:
            explanations = {
                'ssl': 'Проблемы с SSL сертификатом могут позволить злоумышленникам перехватывать данные пользователей.',
                'headers': 'Отсутствующие заголовки безопасности делают сайт уязвимым для различных атак.',
                'forms': 'Небезопасные формы загрузки файлов могут позволить загрузку вредоносного ПО на сервер.',
                'cookies': 'Небезопасные cookies могут быть украдены злоумышленниками.',
                'html': 'Обнаружена проблема безопасности, которую нужно исправить.'
            }
        
        default_msg = 'Sicherheitsproblem gefunden, das behoben werden muss.' if language == 'de' else 'Обнаружена проблема безопасности, которую нужно исправить.'
        return explanations.get(vuln_type, default_msg)
    
    def explain_wifi_scan(self, scan_results: Dict) -> Dict:
        """
        Объяснение результатов сканирования Wi-Fi сети
        
        Args:
            scan_results: Результаты сканирования сети
            
        Returns:
            dict: Объяснение и рекомендации
        """
        total_devices = scan_results.get('total_devices', 0)
        devices = scan_results.get('devices', [])
        network = scan_results.get('network', 'N/A')
        local_ip = scan_results.get('local_ip', 'N/A')
        
        # Группируем устройства по типу
        device_types = {}
        vendors = {}
        for device in devices:
            dtype = device.get('device_type', 'Неизвестное')
            vendor = device.get('vendor', 'Unknown')
            device_types[dtype] = device_types.get(dtype, 0) + 1
            if vendor != 'Unknown':
                vendors[vendor] = vendors.get(vendor, 0) + 1
        
        # Формируем промпт для AI
        prompt = f"""Ты - эксперт по сетевой безопасности. Объясни владельцу бизнеса результаты сканирования его Wi-Fi сети простым языком.

Результаты сканирования:
- Сеть: {network}
- Ваш IP: {local_ip}
- Всего устройств: {total_devices}

Найденные устройства:
"""
        for dtype, count in device_types.items():
            prompt += f"- {dtype}: {count} шт.\n"
        
        if vendors:
            prompt += f"\nПроизводители:\n"
            for vendor, count in vendors.items():
                prompt += f"- {vendor}: {count} шт.\n"
        
        prompt += f"""
Объясни владельцу:
1. Нормально ли такое количество устройств для домашней/офисной сети? (2-3 предложения)
2. Есть ли потенциальные риски безопасности?
3. Дай 3-5 конкретных рекомендаций по безопасности Wi-Fi сети

Говори простым языком, без технических терминов. Раздели ответ на две части: ОБЪЯСНЕНИЕ и РЕКОМЕНДАЦИИ."""
        
        try:
            if not self.api_key:
                # Простой ответ без AI
                explanation = f"""В вашей сети найдено {total_devices} подключенных устройств. 
Это {'нормально' if total_devices <= 15 else 'много'} для {'домашней' if total_devices <= 10 else 'офисной'} сети.
Регулярно проверяйте список подключенных устройств - все они должны быть вам знакомы."""
                
                recommendations = """1. Используйте сложный пароль Wi-Fi (минимум 12 символов)
2. Включите шифрование WPA3 или хотя бы WPA2
3. Отключите WPS на роутере
4. Регулярно обновляйте прошивку роутера
5. Создайте отдельную гостевую сеть для посетителей"""
                
                return {
                    'explanation': explanation,
                    'recommendation': recommendations
                }
            
            # Вызываем AI
            if self.provider == 'openai':
                full_response = self._call_openai(prompt)
            else:
                full_response = self._call_anthropic(prompt)
            
            # Разделяем на объяснение и рекомендации
            parts = full_response.split('РЕКОМЕНДАЦИИ')
            if len(parts) == 2:
                explanation = parts[0].replace('ОБЪЯСНЕНИЕ:', '').strip()
                recommendations = parts[1].strip()
            else:
                # Если не получилось разделить, пробуем по другому
                lines = full_response.split('\n')
                explanation_lines = []
                recommendation_lines = []
                in_recommendations = False
                
                for line in lines:
                    if 'рекоменд' in line.lower() or line.strip().startswith(('1.', '2.', '3.')):
                        in_recommendations = True
                    
                    if in_recommendations:
                        recommendation_lines.append(line)
                    else:
                        explanation_lines.append(line)
                
                explanation = '\n'.join(explanation_lines).strip()
                recommendations = '\n'.join(recommendation_lines).strip()
            
            return {
                'explanation': explanation or f"Найдено {total_devices} устройств в сети",
                'recommendation': recommendations or "Регулярно проверяйте подключенные устройства"
            }
            
        except Exception as e:
            # Fallback на простой ответ
            return {
                'explanation': f"В вашей сети найдено {total_devices} подключенных устройств",
                'recommendation': "Используйте сложный пароль и регулярно проверяйте подключенные устройства"
            }
