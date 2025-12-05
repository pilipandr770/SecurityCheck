"""
API эндпоинт для получения информации об использовании лимитов
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from utils.limits import get_usage_statistics, get_plan_limits, has_feature

usage_bp = Blueprint('usage', __name__)


@usage_bp.route('/stats')
@login_required
def get_usage_stats():
    """Получить статистику использования пользователем"""
    stats = get_usage_statistics(current_user)
    limits = get_plan_limits(current_user.subscription_plan)
    
    return jsonify({
        'success': True,
        'plan': current_user.subscription_plan.value,
        'usage': stats,
        'limits': limits,
        'features': {
            'pdf_export': has_feature(current_user, 'pdf_export'),
            'api_access': has_feature(current_user, 'api_access'),
            'email_alerts': has_feature(current_user, 'email_alerts'),
            'priority_support': has_feature(current_user, 'priority_support')
        }
    })
