"""
API маршруты для проверки ссылок
"""

from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from database import db
from models import LinkCheck, ThreatLevel

link_checks_bp = Blueprint('link_checks', __name__)


@link_checks_bp.route('/check', methods=['POST'])
@login_required
def check_link():
    """Проверить ссылку на безопасность"""
    # Проверка лимитов
    from utils.limits import check_scan_limit
    
    limit_check = check_scan_limit(current_user, 'link_checks')
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
    
    try:
        from services.link_checker import LinkChecker
        from services.ai_explainer import AIExplainer
        import os
        
        # Передаём API ключи из environment
        checker = LinkChecker(
            vt_api_key=os.getenv('VIRUSTOTAL_API_KEY'),
            gsb_api_key=os.getenv('GOOGLE_SAFE_BROWSING_KEY')
        )
        ai = AIExplainer()
        
        # Выполняем проверку
        result = checker.run_full_check(url)
        
        # ЛОГИРОВАНИЕ результатов проверки
        current_app.logger.info(f"Link check result for {url}:")
        current_app.logger.info(f"  is_dangerous: {result.get('is_dangerous')}")
        current_app.logger.info(f"  is_suspicious: {result.get('is_suspicious')}")
        current_app.logger.info(f"  virustotal: {result.get('virustotal')}")
        current_app.logger.info(f"  ssl_valid: {result.get('ssl_valid')}")
        
        # Определяем уровень угрозы
        if result['is_dangerous']:
            threat_level = ThreatLevel.DANGER
        elif result['is_suspicious']:
            threat_level = ThreatLevel.WARNING
        else:
            threat_level = ThreatLevel.SAFE
        
        current_app.logger.info(f"  threat_level determined: {threat_level.value}")
        
        # Получаем AI объяснение
        ai_explanation = None
        try:
            ai_explanation = ai.explain_link_danger(url, result)
        except Exception as e:
            current_app.logger.error(f'AI explanation error: {e}')
        
        # Сохраняем результат
        link_check = LinkCheck(
            user_id=current_user.id,
            original_url=url,
            final_url=result.get('final_url', url),
            domain=domain,
            threat_level=threat_level,
            confidence=result.get('confidence', 0),
            virustotal_result=result.get('virustotal'),
            google_safebrowsing_result=result.get('google_safebrowsing'),
            urlhaus_result=result.get('urlhaus'),
            is_shortened=result.get('is_shortened', False),
            ssl_valid=result.get('ssl_valid'),
            domain_age_days=result.get('domain_age_days'),
            reasons=result.get('reasons', []),
            ai_explanation=ai_explanation
        )
        
        db.session.add(link_check)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'check': link_check.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Link check error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при проверке ссылки'
        }), 500


@link_checks_bp.route('/history')
@login_required
def get_history():
    """Получить историю проверок ссылок"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    checks = LinkCheck.query.filter_by(user_id=current_user.id)\
        .order_by(LinkCheck.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'checks': [c.to_dict() for c in checks.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': checks.total,
            'pages': checks.pages
        }
    })


@link_checks_bp.route('/<int:check_id>')
@login_required
def get_check(check_id):
    """Получить детали проверки ссылки"""
    check = LinkCheck.query.filter_by(
        id=check_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'check': check.to_dict()
    })
