"""
API маршруты для анализа доменов
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import re

from database import db
from models import DomainIntel

domain_intel_bp = Blueprint('domain_intel', __name__)


def validate_domain(domain):
    """Валидация доменного имени"""
    # Убираем протокол если есть
    domain = re.sub(r'^https?://', '', domain)
    # Убираем путь если есть
    domain = domain.split('/')[0]
    # Убираем www
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Проверяем формат домена
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        return None
    
    return domain.lower()


@domain_intel_bp.route('/lookup', methods=['POST'])
@login_required
def lookup_domain():
    """Получить информацию о домене"""
    # Проверка лимитов
    from utils.limits import check_scan_limit
    
    limit_check = check_scan_limit(current_user, 'domain_lookups')
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
    if not data or not data.get('domain'):
        return jsonify({
            'success': False,
            'error': 'Домен обязателен'
        }), 400
    
    domain = validate_domain(data['domain'])
    if not domain:
        return jsonify({
            'success': False,
            'error': 'Некорректный формат домена'
        }), 400
    
    try:
        from services.domain_analyzer import DomainAnalyzer
        from services.ai_explainer import AIExplainer
        
        analyzer = DomainAnalyzer()
        ai = AIExplainer()
        
        # Выполняем анализ
        result = analyzer.run_full_analysis(domain)
        
        # Создаём запись в БД
        intel = DomainIntel(
            user_id=current_user.id,
            domain=domain,
            # WHOIS
            whois_registrar=result.get('whois', {}).get('registrar'),
            whois_registrant=result.get('whois', {}).get('registrant'),
            whois_created_date=result.get('whois', {}).get('created_date'),
            whois_expiry_date=result.get('whois', {}).get('expiry_date'),
            whois_updated_date=result.get('whois', {}).get('updated_date'),
            whois_nameservers=result.get('whois', {}).get('nameservers'),
            whois_raw=result.get('whois'),
            # DNS
            dns_a_records=result.get('dns', {}).get('A'),
            dns_aaaa_records=result.get('dns', {}).get('AAAA'),
            dns_mx_records=result.get('dns', {}).get('MX'),
            dns_txt_records=result.get('dns', {}).get('TXT'),
            dns_ns_records=result.get('dns', {}).get('NS'),
            # Email security
            has_spf=result.get('email_security', {}).get('has_spf'),
            has_dkim=result.get('email_security', {}).get('has_dkim'),
            has_dmarc=result.get('email_security', {}).get('has_dmarc'),
            email_security_score=result.get('email_security', {}).get('score'),
            # Reputation
            domain_age_days=result.get('domain_age_days'),
            reputation_score=result.get('reputation_score'),
            ip_reputation=result.get('ip_reputation'),
            # Wayback
            wayback_snapshots=result.get('wayback', {}).get('snapshots'),
            wayback_first_capture=result.get('wayback', {}).get('first_capture'),
            wayback_last_capture=result.get('wayback', {}).get('last_capture')
        )
        
        # AI резюме
        try:
            ai_summary = ai.generate_domain_summary(domain, result)
            intel.ai_summary = ai_summary
        except Exception as e:
            current_app.logger.error(f'AI summary error: {e}')
        
        db.session.add(intel)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'intel': intel.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Domain lookup error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при анализе домена'
        }), 500


@domain_intel_bp.route('/<int:intel_id>')
@login_required
def get_intel(intel_id):
    """Получить информацию о домене по ID"""
    intel = DomainIntel.query.filter_by(
        id=intel_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'intel': intel.to_dict()
    })


@domain_intel_bp.route('/<int:intel_id>/dns-records')
@login_required
def get_dns_records(intel_id):
    """Получить DNS записи домена"""
    intel = DomainIntel.query.filter_by(
        id=intel_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'dns': {
            'A': intel.dns_a_records,
            'AAAA': intel.dns_aaaa_records,
            'MX': intel.dns_mx_records,
            'TXT': intel.dns_txt_records,
            'NS': intel.dns_ns_records
        }
    })


@domain_intel_bp.route('/history')
@login_required
def get_history():
    """Получить историю анализов доменов"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    intel_list = DomainIntel.query.filter_by(user_id=current_user.id)\
        .order_by(DomainIntel.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'intel': [i.to_dict() for i in intel_list.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': intel_list.total,
            'pages': intel_list.pages
        }
    })
