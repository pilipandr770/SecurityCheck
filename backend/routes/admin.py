"""
Админ-панель
"""

from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from database import db
from models import User, WebScan, LinkCheck, NetworkScan, DomainIntel, SubscriptionPlan, ThreatLevel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Anmeldung erforderlich', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Zugriff verweigert. Admin-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def index():
    """Главная страница админ-панели"""
    
    # Статистика пользователей
    total_users = User.query.count()
    free_users = User.query.filter_by(subscription_plan=SubscriptionPlan.FREE).count()
    starter_users = User.query.filter_by(subscription_plan=SubscriptionPlan.STARTER).count()
    pro_users = User.query.filter_by(subscription_plan=SubscriptionPlan.PRO).count()
    
    # Статистика сканов за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    web_scans_count = WebScan.query.filter(WebScan.created_at >= thirty_days_ago).count()
    link_checks_count = LinkCheck.query.filter(LinkCheck.created_at >= thirty_days_ago).count()
    network_scans_count = NetworkScan.query.filter(NetworkScan.created_at >= thirty_days_ago).count()
    domain_checks_count = DomainIntel.query.filter(DomainIntel.created_at >= thirty_days_ago).count()
    
    # Опасные находки
    dangerous_links = LinkCheck.query.filter(
        LinkCheck.threat_level == ThreatLevel.DANGER,
        LinkCheck.created_at >= thirty_days_ago
    ).count()
    
    # Последние регистрации
    recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
    
    # Активные пользователи (сканы за последние 7 дней)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_user_ids = set()
    
    for scan in WebScan.query.filter(WebScan.created_at >= week_ago).all():
        active_user_ids.add(scan.user_id)
    for check in LinkCheck.query.filter(LinkCheck.created_at >= week_ago).all():
        active_user_ids.add(check.user_id)
    
    active_users_count = len(active_user_ids)
    
    # Доход (примерная оценка)
    monthly_revenue = (starter_users * 5) + (pro_users * 15)
    
    stats = {
        'users': {
            'total': total_users,
            'free': free_users,
            'starter': starter_users,
            'pro': pro_users,
            'active': active_users_count
        },
        'scans': {
            'web': web_scans_count,
            'links': link_checks_count,
            'network': network_scans_count,
            'domains': domain_checks_count,
            'total': web_scans_count + link_checks_count + network_scans_count + domain_checks_count
        },
        'threats': {
            'dangerous_links': dangerous_links
        },
        'revenue': {
            'monthly': monthly_revenue,
            'yearly': monthly_revenue * 12
        }
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Список всех пользователей"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Фильтры
    search = request.args.get('search', '')
    plan = request.args.get('plan', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    if plan:
        query = query.filter_by(subscription_plan=SubscriptionPlan(plan))
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, plan=plan)


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Детальная информация о пользователе"""
    user = User.query.get_or_404(user_id)
    
    # Статистика пользователя
    web_scans = WebScan.query.filter_by(user_id=user_id).count()
    link_checks = LinkCheck.query.filter_by(user_id=user_id).count()
    network_scans = NetworkScan.query.filter_by(user_id=user_id).count()
    domain_checks = DomainIntel.query.filter_by(user_id=user_id).count()
    
    # Последняя активность
    last_web_scan = WebScan.query.filter_by(user_id=user_id).order_by(desc(WebScan.created_at)).first()
    last_link_check = LinkCheck.query.filter_by(user_id=user_id).order_by(desc(LinkCheck.created_at)).first()
    
    stats = {
        'web_scans': web_scans,
        'link_checks': link_checks,
        'network_scans': network_scans,
        'domain_checks': domain_checks,
        'total': web_scans + link_checks + network_scans + domain_checks,
        'last_web_scan': last_web_scan,
        'last_link_check': last_link_check
    }
    
    return render_template('admin/user_detail.html', user=user, stats=stats)


@admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    """Обновление данных пользователя"""
    user = User.query.get_or_404(user_id)
    
    data = request.get_json()
    
    if 'subscription_plan' in data:
        try:
            user.subscription_plan = SubscriptionPlan(data['subscription_plan'])
            db.session.commit()
            return jsonify({'success': True, 'message': 'Тариф обновлён'})
        except ValueError:
            return jsonify({'success': False, 'error': 'Некорректный тариф'}), 400
    
    if 'is_active' in data:
        user.is_active = data['is_active']
        db.session.commit()
        action = 'активирован' if user.is_active else 'заблокирован'
        return jsonify({'success': True, 'message': f'Пользователь {action}'})
    
    return jsonify({'success': False, 'error': 'Некорректные данные'}), 400


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Удаление пользователя"""
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Нельзя удалить себя'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # Удаляем все данные пользователя
    WebScan.query.filter_by(user_id=user_id).delete()
    LinkCheck.query.filter_by(user_id=user_id).delete()
    NetworkScan.query.filter_by(user_id=user_id).delete()
    DomainIntel.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Пользователь удалён'})


@admin_bp.route('/scans')
@login_required
@admin_required
def scans():
    """История всех сканов"""
    scan_type = request.args.get('type', 'web')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    if scan_type == 'web':
        scans = WebScan.query.order_by(desc(WebScan.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    elif scan_type == 'links':
        scans = LinkCheck.query.order_by(desc(LinkCheck.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    elif scan_type == 'network':
        scans = NetworkScan.query.order_by(desc(NetworkScan.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        scans = DomainIntel.query.order_by(desc(DomainIntel.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    return render_template('admin/scans.html', scans=scans, scan_type=scan_type)


@admin_bp.route('/stats/api')
@login_required
@admin_required
def stats_api():
    """API для графиков статистики"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Регистрации по дням
    registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= start_date).group_by(func.date(User.created_at)).all()
    
    # Сканы по дням
    scans = db.session.query(
        func.date(WebScan.created_at).label('date'),
        func.count(WebScan.id).label('count')
    ).filter(WebScan.created_at >= start_date).group_by(func.date(WebScan.created_at)).all()
    
    return jsonify({
        'registrations': [{'date': str(r.date), 'count': r.count} for r in registrations],
        'scans': [{'date': str(s.date), 'count': s.count} for s in scans]
    })
