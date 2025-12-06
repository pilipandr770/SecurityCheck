"""
API маршруты для сканирования веб-сайтов
"""

from datetime import datetime
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from database import db
from models import WebScan, ScanResult, ScanStatus, SeverityLevel

web_scans_bp = Blueprint('web_scans', __name__)


@web_scans_bp.route('/start', methods=['POST'])
@login_required
def start_scan():
    """Запустить сканирование веб-сайта"""
    # Проверка лимитов
    from utils.limits import check_scan_limit
    
    limit_check = check_scan_limit(current_user, 'web_scans')
    if not limit_check['allowed']:
        return jsonify({
            'success': False,
            'error': limit_check.get('reason', 'Лимит превышен'),
            'usage': {
                'used': limit_check['used'],
                'limit': limit_check['limit'],
                'remaining': limit_check['remaining']
            }
        }), 429
    
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({
            'success': False,
            'error': 'URL обязателен'
        }), 400
    
    url = data['url'].strip()
    
    # Валидация URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        
        if not parsed.netloc:
            raise ValueError('Invalid URL')
            
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
            
    except Exception:
        return jsonify({
            'success': False,
            'error': 'Некорректный URL'
        }), 400
    
    # Создаём запись о сканировании
    try:
        scan = WebScan(
            user_id=current_user.id,
            target_url=url,
            target_domain=domain,
            status=ScanStatus.PENDING
        )
        db.session.add(scan)
        db.session.commit()
        
        # TODO: Запустить асинхронное сканирование
        # Пока запускаем синхронно (для MVP)
        run_scan(scan.id)
        
        return jsonify({
            'success': True,
            'scan_id': scan.id,
            'message': 'Сканирование запущено'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error starting scan: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при запуске сканирования'
        }), 500


@web_scans_bp.route('/<int:scan_id>')
@login_required
def get_scan(scan_id):
    """Получить результаты сканирования"""
    scan = WebScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'scan': scan.to_dict(include_results=True)
    })


@web_scans_bp.route('/<int:scan_id>/status')
@login_required
def get_scan_status(scan_id):
    """Получить статус сканирования"""
    scan = WebScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'status': scan.status.value,
        'progress': scan.progress
    })


@web_scans_bp.route('/<int:scan_id>/forms')
@login_required
def get_scan_forms(scan_id):
    """Получить найденные формы загрузки"""
    scan = WebScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Ищем результаты категории 'forms'
    form_results = ScanResult.query.filter_by(
        scan_id=scan_id,
        category='forms'
    ).all()
    
    return jsonify({
        'success': True,
        'forms': [r.to_dict() for r in form_results]
    })


@web_scans_bp.route('/history')
@login_required
def get_history():
    """Получить историю сканирований"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    scans = WebScan.query.filter_by(user_id=current_user.id)\
        .order_by(WebScan.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'scans': [s.to_dict() for s in scans.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': scans.total,
            'pages': scans.pages
        }
    })


@web_scans_bp.route('/<int:scan_id>', methods=['DELETE'])
@login_required
def delete_scan(scan_id):
    """Удалить результаты сканирования"""
    scan = WebScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        db.session.delete(scan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Сканирование удалено'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting scan: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при удалении'
        }), 500


# ==================== ЛОГИКА СКАНИРОВАНИЯ ====================

def map_vulnerability_type(result):
    """
    Маппинг результата сканирования к типу уязвимости из базы знаний
    
    Args:
        result: Dict с результатом сканирования
        
    Returns:
        str: Тип уязвимости для VulnerabilityKnowledge или None
    """
    category = result.get('category', '')
    title = result.get('title', '').lower()
    description = result.get('description', '').lower()
    severity = result.get('severity', '')
    
    current_app.logger.info(f'Mapping vulnerability: category={category}, title={title[:50]}, severity={severity}')
    
    # XSS уязвимости (проверяем первыми, так как это часто в headers)
    if 'content-security-policy' in title or 'csp' in title:
        current_app.logger.info('-> Mapped to XSS (CSP missing)')
        return 'xss'
    
    if 'x-xss-protection' in title:
        current_app.logger.info('-> Mapped to XSS Protection header (treating as separate from CSP)')
        # X-XSS-Protection это legacy заголовок, низкий приоритет - не показываем отдельно
        return None  # Пусть AI обработает или пропустим
    
    # HSTS
    if 'hsts' in title or 'strict-transport-security' in title:
        current_app.logger.info('-> Mapped to missing_hsts')
        return 'missing_hsts'
    
    # Clickjacking
    if 'x-frame-options' in title or 'clickjacking' in title or 'frame' in title:
        current_app.logger.info('-> Mapped to clickjacking')
        return 'clickjacking'
    
    # MIME Sniffing
    if 'x-content-type-options' in title or 'mime' in title:
        current_app.logger.info('-> Mapped to mime_sniffing')
        return 'mime_sniffing'
    
    # Information Disclosure
    if 'раскрытие информации' in title or 'server' in description.lower() and 'раскрывает' in description:
        current_app.logger.info('-> Mapped to info_disclosure')
        return 'info_disclosure'
    
    # SSL/TLS проблемы
    if category == 'ssl':
        # Любая проблема с SSL - показываем информацию о missing_ssl
        if severity in ['high', 'critical'] or 'истёк' in title or 'не используется' in title or 'отсутствует' in title:
            current_app.logger.info('-> Mapped to missing_ssl')
            return 'missing_ssl'
    
    # Insecure cookies
    if category == 'cookies' and severity in ['medium', 'high', 'critical']:
        if 'secure' in title or 'httponly' in title or 'samesite' in title:
            current_app.logger.info('-> Mapped to insecure cookies (treating as XSS risk)')
            return 'xss'  # Небезопасные куки могут привести к XSS атакам
    
    # CSRF уязвимости
    if 'csrf' in title or 'csrf' in description:
        current_app.logger.info('-> Mapped to CSRF')
        return 'csrf'
    
    # SQL Injection
    if 'sql' in title or 'injection' in description:
        current_app.logger.info('-> Mapped to SQL Injection')
        return 'sql_injection'
    
    # Weak password policy
    if 'password' in title or 'парол' in title:
        current_app.logger.info('-> Mapped to weak_password_policy')
        return 'weak_password_policy'
    
    current_app.logger.info('-> No mapping found, will use AI')
    return None


def run_scan(scan_id):
    """
    Запустить сканирование (синхронно для MVP)
    В production использовать Celery или аналог
    """
    from services.web_scanner import WebScanner
    from services.form_analyzer import FormSecurityAnalyzer
    from services.ai_explainer import AIExplainer
    from services.vulnerability_knowledge import VulnerabilityKnowledge
    
    scan = WebScan.query.get(scan_id)
    if not scan:
        return
    
    try:
        scan.status = ScanStatus.RUNNING
        scan.progress = 0
        db.session.commit()
        
        start_time = datetime.utcnow()
        
        # Инициализируем сканер
        scanner = WebScanner(scan.target_url)
        form_analyzer = FormSecurityAnalyzer()
        ai = AIExplainer()
        
        # Проверяем верификацию
        is_verified = scan.is_verified or False
        
        # Выполняем проверки
        results = []
        
        # SSL проверка (10%)
        scan.progress = 10
        db.session.commit()
        ssl_results = scanner.check_ssl_certificate()
        results.extend(ssl_results)
        
        # Заголовки безопасности (30%)
        scan.progress = 30
        db.session.commit()
        header_results = scanner.check_security_headers()
        results.extend(header_results)
        
        # HTML анализ (50%)
        scan.progress = 50
        db.session.commit()
        html_results = scanner.check_html_issues()
        results.extend(html_results)
        
        # Поиск форм загрузки (70%)
        scan.progress = 70
        db.session.commit()
        html_content = scanner.get_page_content()
        if html_content:
            form_results = form_analyzer.analyze_page(html_content, scan.target_url)
            results.extend(form_results)
        
        # Cookies (80%)
        scan.progress = 80
        db.session.commit()
        cookie_results = scanner.check_cookies()
        results.extend(cookie_results)
        
        # HTTP методы (90%)
        scan.progress = 90
        db.session.commit()
        http_results = scanner.check_http_methods()
        results.extend(http_results)
        
        # Сохраняем результаты
        critical = high = medium = low = 0
        
        for result in results:
            severity = SeverityLevel(result['severity'])
            
            # Определяем тип уязвимости
            vuln_type = map_vulnerability_type(result)
            
            # Если не смогли определить автоматически, используем category
            if not vuln_type:
                vuln_type = result.get('category')
            
            # Получаем дополнительную информацию из базы знаний
            vuln_info = None
            
            try:
                vuln_info = VulnerabilityKnowledge.get_vulnerability_info(
                    vuln_type, 
                    language='de',
                    verified=is_verified
                )
                if vuln_info:
                    current_app.logger.info(f'✅ Got vulnerability info from knowledge base for {vuln_type}')
                    current_app.logger.info(f'   Video: {vuln_info.get("video", {}).get("youtube_id", "NO VIDEO")}')
                else:
                    current_app.logger.info(f'❌ No vulnerability info in knowledge base for {vuln_type}')
            except Exception as e:
                current_app.logger.warning(f'Could not get vulnerability info for {vuln_type}: {e}')
            
            # Если нет в базе знаний, пробуем AI объяснение
            ai_explanation = result.get('ai_explanation')
            if not vuln_info and not ai_explanation:
                try:
                    vuln_explain = ai.explain_vulnerability(
                        vuln_type,
                        result.get('description', ''),
                        result['severity'],
                        language='de',
                        verified=is_verified
                    )
                    if isinstance(vuln_explain, dict):
                        vuln_info = vuln_explain
                    else:
                        ai_explanation = vuln_explain
                except Exception as e:
                    current_app.logger.warning(f'AI explanation error: {e}')
            
            scan_result = ScanResult(
                scan_id=scan.id,
                category=result['category'],
                title=result['title'],
                description=result.get('description'),
                severity=severity,
                raw_data=result.get('raw_data'),
                evidence=result.get('evidence'),
                ai_explanation=ai_explanation,
                ai_fix=result.get('ai_fix'),
                vulnerability_info=vuln_info  # Добавляем информацию из базы знаний
            )
            db.session.add(scan_result)
            
            # Подсчёт по severity
            if severity == SeverityLevel.CRITICAL:
                critical += 1
            elif severity == SeverityLevel.HIGH:
                high += 1
            elif severity == SeverityLevel.MEDIUM:
                medium += 1
            elif severity == SeverityLevel.LOW:
                low += 1
        
        # Обновляем статистику
        scan.total_issues = len(results)
        scan.critical_issues = critical
        scan.high_issues = high
        scan.medium_issues = medium
        scan.low_issues = low
        
        # Рассчитываем Security Score
        scan.calculate_security_score()
        
        # Генерируем AI резюме
        try:
            summary = ai.generate_scan_summary(results, scan.target_domain, language='de')
            scan.ai_summary = summary.get('summary')
            scan.ai_recommendations = summary.get('recommendations')
        except Exception as e:
            current_app.logger.error(f'AI summary error: {e}')
        
        # Завершаем
        end_time = datetime.utcnow()
        scan.scan_duration = (end_time - start_time).total_seconds()
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = end_time
        scan.progress = 100
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f'Scan error for {scan_id}: {e}')
        scan.status = ScanStatus.FAILED
        db.session.commit()
