"""
Маршруты Dashboard
Главная страница после входа, статистика, история
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, current_app, request
from flask_login import login_required, current_user
from sqlalchemy import func

from database import db
from models import WebScan, LinkCheck, NetworkScan, DomainIntel, ScanStatus

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Главная страница Dashboard"""
    # Получаем статистику для текущего пользователя
    stats = get_user_stats(current_user.id)
    
    # Получаем последние сканирования
    recent_scans = get_recent_scans(current_user.id, limit=5)
    
    # Получаем лимиты пользователя
    limits = get_user_limits(current_user)
    
    # Получаем данные для графиков
    activity_data = get_activity_chart_data(current_user.id)
    distribution_data = get_distribution_chart_data(current_user.id)
    
    return render_template('dashboard.html',
                           stats=stats,
                           recent_scans=recent_scans,
                           limits=limits,
                           activity_data=activity_data,
                           distribution_data=distribution_data)


@dashboard_bp.route('/dashboard/stats')
@login_required
def get_stats():
    """API: Получить статистику пользователя"""
    stats = get_user_stats(current_user.id)
    return jsonify({
        'success': True,
        'stats': stats
    })


@dashboard_bp.route('/dashboard/recent-scans')
@login_required
def get_recent():
    """API: Получить последние сканирования"""
    limit = min(int(request.args.get('limit', 10)), 50)
    recent = get_recent_scans(current_user.id, limit=limit)
    return jsonify({
        'success': True,
        'scans': recent
    })


@dashboard_bp.route('/dashboard/history')
@login_required
def get_history():
    """API: Получить историю всех проверок"""
    page = int(request.args.get('page', 1))
    scan_type = request.args.get('type', 'all')
    period = request.args.get('period', '7')
    status = request.args.get('status', 'all')
    limit = 20
    
    # Фильтр по периоду
    if period != 'all':
        days = int(period)
        date_from = datetime.now() - timedelta(days=days)
    else:
        date_from = None
    
    items = []
    
    # Web scans
    if scan_type in ['all', 'web_scan']:
        query = WebScan.query.filter_by(user_id=current_user.id)
        if date_from:
            query = query.filter(WebScan.created_at >= date_from)
        if status != 'all':
            query = query.filter(WebScan.status == ScanStatus[status])
        
        for scan in query.order_by(WebScan.created_at.desc()).all():
            items.append({
                'type': 'web_scan',
                'id': scan.id,
                'target': scan.target_domain,
                'status': scan.status.value,
                'result': scan.security_score,
                'created_at': scan.created_at.isoformat()
            })
    
    # Link checks
    if scan_type in ['all', 'link_check']:
        query = LinkCheck.query.filter_by(user_id=current_user.id)
        if date_from:
            query = query.filter(LinkCheck.created_at >= date_from)
        
        for check in query.order_by(LinkCheck.created_at.desc()).all():
            items.append({
                'type': 'link_check',
                'id': check.id,
                'target': check.domain,
                'status': 'completed',
                'result': check.threat_level.value if check.threat_level else 'unknown',
                'created_at': check.created_at.isoformat()
            })
    
    # Domain intel
    if scan_type in ['all', 'domain_intel']:
        query = DomainIntel.query.filter_by(user_id=current_user.id)
        if date_from:
            query = query.filter(DomainIntel.created_at >= date_from)
        
        for intel in query.order_by(DomainIntel.created_at.desc()).all():
            items.append({
                'type': 'domain_intel',
                'id': intel.id,
                'target': intel.domain,
                'status': 'completed',
                'result': intel.reputation_score,
                'created_at': intel.created_at.isoformat()
            })
    
    # Сортировка и пагинация
    items.sort(key=lambda x: x['created_at'], reverse=True)
    
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    paginated_items = items[start:end]
    
    # Статистика
    statistics = {
        'total': total,
        'today': len([i for i in items if datetime.fromisoformat(i['created_at']).date() == datetime.now().date()]),
        'safe': len([i for i in items if i.get('result') in ['safe', 'clean'] or (isinstance(i.get('result'), (int, float)) and i['result'] >= 80)]),
        'threats': len([i for i in items if i.get('result') in ['malicious', 'suspicious', 'phishing'] or (isinstance(i.get('result'), (int, float)) and i['result'] < 60)])
    }
    
    return jsonify({
        'success': True,
        'items': paginated_items,
        'statistics': statistics,
        'page': page,
        'total_pages': (total + limit - 1) // limit,
        'total': total
    })


@dashboard_bp.route('/dashboard/limits')
@login_required
def get_limits():
    """API: Получить лимиты пользователя"""
    limits = get_user_limits(current_user)
    return jsonify({
        'success': True,
        'limits': limits
    })


# ==================== СТРАНИЦЫ ФУНКЦИЙ ====================

@dashboard_bp.route('/scan/website')
@login_required
def web_scan_page():
    """Страница сканирования веб-сайта"""
    can_scan, message = current_user.can_use_feature('web_scans')
    limits = get_user_limits(current_user)
    return render_template('web_scan.html', can_scan=can_scan, limit_message=message, limits=limits)


@dashboard_bp.route('/check/link')
@login_required
def link_check_page():
    """Страница проверки ссылки"""
    can_check, message = current_user.can_use_feature('link_checks')
    limits = get_user_limits(current_user)
    return render_template('link_check.html', can_check=can_check, limit_message=message, limits=limits)


@dashboard_bp.route('/scan/network')
@dashboard_bp.route('/scan/wifi')  # Алиас для WiFi сканера
@login_required
def network_scan_page():
    """Страница сканирования WiFi сети"""
    can_scan, message = current_user.can_use_feature('network_scans')
    limits = get_user_limits(current_user)
    return render_template('wifi_scan.html', can_scan=can_scan, limit_message=message, limits=limits)

# Регистрируем алиас для url_for
dashboard_bp.add_url_rule('/scan/wifi', 'wifi_scan_page', network_scan_page)


@dashboard_bp.route('/lookup/domain')
@login_required
def domain_lookup_page():
    """Страница проверки домена"""
    can_lookup, message = current_user.can_use_feature('domain_lookups')
    limits = get_user_limits(current_user)
    return render_template('domain_lookup.html', can_lookup=can_lookup, limit_message=message, limits=limits)


@dashboard_bp.route('/history')
@login_required
def history_page():
    """Страница истории сканирований"""
    return render_template('history.html')


@dashboard_bp.route('/pricing')
def pricing_page():
    """Страница с ценами и тарифами"""
    return render_template('pricing.html')


@dashboard_bp.route('/settings')
@login_required
def settings_page():
    """Страница настроек пользователя"""
    return render_template('settings.html')


@dashboard_bp.route('/results/<scan_type>/<int:scan_id>')
@login_required
def results_page(scan_type, scan_id):
    """Страница результатов сканирования"""
    # Проверяем тип сканирования и получаем данные
    scan = None
    
    if scan_type == 'web':
        scan = WebScan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    elif scan_type == 'link':
        scan = LinkCheck.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    elif scan_type == 'domain':
        scan = DomainIntel.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    else:
        abort(404)
    
    return render_template('results.html', scan_type=scan_type, scan=scan)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_user_stats(user_id):
    """
    Получить статистику пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Статистика
    """
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    week_ago = today_start - timedelta(days=7)
    month_ago = today_start - timedelta(days=30)
    
    # Подсчёт сканирований
    stats = {
        'total': {
            'web_scans': WebScan.query.filter_by(user_id=user_id).count(),
            'link_checks': LinkCheck.query.filter_by(user_id=user_id).count(),
            'network_scans': NetworkScan.query.filter_by(user_id=user_id).count(),
            'domain_lookups': DomainIntel.query.filter_by(user_id=user_id).count()
        },
        'today': {
            'web_scans': WebScan.query.filter(
                WebScan.user_id == user_id,
                WebScan.created_at >= today_start
            ).count(),
            'link_checks': LinkCheck.query.filter(
                LinkCheck.user_id == user_id,
                LinkCheck.created_at >= today_start
            ).count(),
            'network_scans': NetworkScan.query.filter(
                NetworkScan.user_id == user_id,
                NetworkScan.created_at >= today_start
            ).count(),
            'domain_lookups': DomainIntel.query.filter(
                DomainIntel.user_id == user_id,
                DomainIntel.created_at >= today_start
            ).count()
        },
        'this_week': {
            'web_scans': WebScan.query.filter(
                WebScan.user_id == user_id,
                WebScan.created_at >= week_ago
            ).count()
        },
        'this_month': {
            'web_scans': WebScan.query.filter(
                WebScan.user_id == user_id,
                WebScan.created_at >= month_ago
            ).count()
        }
    }
    
    # Средний Security Score
    avg_score = db.session.query(func.avg(WebScan.security_score)).filter(
        WebScan.user_id == user_id,
        WebScan.security_score.isnot(None)
    ).scalar()
    stats['average_security_score'] = round(avg_score) if avg_score else None
    
    # Количество критических проблем
    critical_count = db.session.query(func.sum(WebScan.critical_issues)).filter(
        WebScan.user_id == user_id
    ).scalar()
    stats['total_critical_issues'] = critical_count or 0
    
    return stats


def get_recent_scans(user_id, limit=10):
    """
    Получить последние сканирования всех типов
    
    Args:
        user_id: ID пользователя
        limit: Максимальное количество
        
    Returns:
        list: Последние сканирования
    """
    recent = []
    
    # Web scans
    web_scans = WebScan.query.filter_by(user_id=user_id)\
        .order_by(WebScan.created_at.desc())\
        .limit(limit).all()
    for scan in web_scans:
        recent.append({
            'type': 'web',
            'id': scan.id,
            'title': scan.target_domain,
            'status': scan.status.value,
            'score': scan.security_score,
            'created_at': scan.created_at,
            'view_url': f'/scan/website?id={scan.id}'
        })
    
    # Link checks
    link_checks = LinkCheck.query.filter_by(user_id=user_id)\
        .order_by(LinkCheck.created_at.desc())\
        .limit(limit).all()
    for check in link_checks:
        recent.append({
            'type': 'link',
            'id': check.id,
            'title': check.domain,
            'status': check.threat_level.value,
            'created_at': check.created_at,
            'view_url': f'/check/link?id={check.id}'
        })
    
    # Network scans
    network_scans = NetworkScan.query.filter_by(user_id=user_id)\
        .order_by(NetworkScan.created_at.desc())\
        .limit(limit).all()
    for scan in network_scans:
        recent.append({
            'type': 'network',
            'id': scan.id,
            'title': scan.target,
            'status': scan.threat_level.value if scan.threat_level else 'pending',
            'created_at': scan.created_at,
            'view_url': f'/scan/network?id={scan.id}'
        })
    
    # Domain intel
    domain_intel = DomainIntel.query.filter_by(user_id=user_id)\
        .order_by(DomainIntel.created_at.desc())\
        .limit(limit).all()
    for intel in domain_intel:
        recent.append({
            'type': 'domain',
            'id': intel.id,
            'title': intel.domain,
            'score': intel.reputation_score,
            'created_at': intel.created_at,
            'view_url': f'/lookup/domain?id={intel.id}'
        })
    
    # Сортируем по дате и берём первые N
    recent.sort(key=lambda x: x['created_at'], reverse=True)
    return recent[:limit]


def get_user_limits(user):
    """
    Получить информацию о лимитах пользователя
    
    Args:
        user: Объект пользователя
        
    Returns:
        dict: Информация о лимитах
    """
    features = ['web_scans', 'link_checks', 'network_scans', 'domain_lookups']
    limits = {}
    
    for feature in features:
        limit = user.get_daily_limit(feature)
        usage = user.get_usage_today(feature)
        can_use, message = user.can_use_feature(feature)
        
        limits[feature] = {
            'limit': limit,
            'usage': usage,
            'remaining': max(0, limit - usage) if limit > 0 else (-1 if limit == -1 else 0),
            'can_use': can_use,
            'message': message,
            'unlimited': limit == -1
        }
        
        # Добавляем formatted версии для шаблонов
        feature_name = feature.replace('_', '_')
        limits[f'{feature_name}_total'] = 'Безлимит' if limit == -1 else str(limit)
        limits[f'{feature_name}_remaining'] = 'Безлимит' if limit == -1 else str(max(0, limit - usage))
    
    return limits


def get_activity_chart_data(user_id):
    """
    Получить данные для графика активности (последние 7 дней)
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Данные для графика активности
    """
    today = datetime.utcnow().date()
    labels = []
    web_scans_data = []
    link_checks_data = []
    file_analyses_data = []
    domain_lookups_data = []
    
    # Генерируем данные за последние 7 дней
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        labels.append(day.strftime('%d.%m'))
        
        # Подсчёт сканирований за день
        web_count = WebScan.query.filter(
            WebScan.user_id == user_id,
            WebScan.created_at >= day_start,
            WebScan.created_at <= day_end
        ).count()
        web_scans_data.append(web_count)
        
        link_count = LinkCheck.query.filter(
            LinkCheck.user_id == user_id,
            LinkCheck.created_at >= day_start,
            LinkCheck.created_at <= day_end
        ).count()
        link_checks_data.append(link_count)
        
        domain_count = DomainIntel.query.filter(
            DomainIntel.user_id == user_id,
            DomainIntel.created_at >= day_start,
            DomainIntel.created_at <= day_end
        ).count()
        domain_lookups_data.append(domain_count)
    
    return {
        'labels': labels,
        'web_scans': web_scans_data,
        'link_checks': link_checks_data,
        'domain_lookups': domain_lookups_data
    }


def get_distribution_chart_data(user_id):
    """
    Получить данные для графика распределения типов сканирований
    
    Args:
        user_id: ID пользователя
        
    Returns:
        dict: Данные для графика распределения
    """
    web_count = WebScan.query.filter_by(user_id=user_id).count()
    link_count = LinkCheck.query.filter_by(user_id=user_id).count()
    network_count = NetworkScan.query.filter_by(user_id=user_id).count()
    domain_count = DomainIntel.query.filter_by(user_id=user_id).count()
    
    return {
        'labels': ['Сайты', 'Ссылки', 'Сеть', 'Домены'],
        'data': [web_count, link_count, network_count, domain_count]
    }


# Импортируем request для API endpoints
from flask import request, abort
