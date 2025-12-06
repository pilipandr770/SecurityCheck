"""
API маршруты для управления подписками
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from database import db
from models import SubscriptionPlan

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/plans')
def get_plans():
    """Получить список тарифных планов"""
    plans = [
        {
            'id': 'free',
            'name': 'Free',
            'price': 0,
            'currency': 'EUR',
            'billing': 'monthly',
            'description': 'Базовый план для знакомства с сервисом',
            'features': [
                '10 проверок сайтов в месяц',
                '50 проверок ссылок в месяц',
                '5 проверок доменов в месяц',
                'Базовый отчет о безопасности',
                'История проверок (7 дней)',
                'Поддержка через email'
            ],
            'cta': 'Начать бесплатно',
            'popular': False
        },
        {
            'id': 'starter',
            'name': 'Starter',
            'price': 9.99,
            'currency': 'EUR',
            'billing': 'monthly',
            'yearly_price': 99.90,
            'description': 'Для постоянного мониторинга безопасности',
            'features': [
                '✅ Безлимитные проверки сайтов',
                '✅ Безлимитные проверки ссылок',
                '✅ Безлимитные проверки доменов',
                '✅ Расширенный отчет с рекомендациями',
                '✅ История проверок (90 дней)',
                '✅ Email-уведомления об угрозах',
                '✅ PDF-экспорт отчетов',
                '✅ Приоритетная поддержка'
            ],
            'cta': 'Выбрать Starter',
            'popular': True
        },
        {
            'id': 'pro',
            'name': 'Pro + Development',
            'price': 29.99,
            'currency': 'EUR',
            'billing': 'monthly',
            'yearly_price': 299.90,
            'description': 'Комплексная безопасность + консультации',
            'features': [
                '🚀 Всё из плана Starter',
                '🚀 Безлимитная история проверок',
                '🚀 API доступ для интеграций',
                '🚀 White-label отчеты',
                '🚀 Консультация эксперта (1 час/месяц)',
                '🚀 Анализ архитектуры безопасности',
                '🚀 Рекомендации по защите',
                '🚀 Приоритетная поддержка 24/7'
            ],
            'cta': 'Выбрать Pro',
            'popular': False,
            'highlight': 'Лучший выбор для бизнеса'
        }
    ]
    
    return jsonify({
        'success': True,
        'plans': plans
    })


@subscription_bp.route('/current')
@login_required
def get_current():
    """Получить текущую подписку пользователя"""
    return jsonify({
        'success': True,
        'subscription': {
            'plan': current_user.subscription_plan.value,
            'plan_name': current_user.plan_name,
            'is_active': current_user.is_subscription_active,
            'expires': current_user.subscription_expires.isoformat() if current_user.subscription_expires else None,
            'stripe_subscription_id': current_user.stripe_subscription_id
        }
    })


@subscription_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Обновить подписку (создать Stripe Checkout сессию)"""
    data = request.get_json()
    plan = data.get('plan')
    billing = data.get('billing', 'monthly')  # monthly or yearly
    
    if plan not in ['starter', 'pro']:
        return jsonify({
            'success': False,
            'error': 'Недопустимый план'
        }), 400
    
    try:
        from services.stripe_handler import StripeHandler
        
        handler = StripeHandler()
        
        # Создаём или получаем Stripe Customer
        if not current_user.stripe_customer_id:
            customer = handler.create_customer(
                email=current_user.email,
                name=current_user.full_name or current_user.company_name
            )
            current_user.stripe_customer_id = customer['id']
            db.session.commit()
        
        # Создаём Checkout сессию
        session = handler.create_checkout_session(
            customer_id=current_user.stripe_customer_id,
            plan=plan,
            billing=billing,
            success_url=f"{request.host_url}dashboard?payment=success",
            cancel_url=f"{request.host_url}pricing?payment=cancelled"
        )
        
        return jsonify({
            'success': True,
            'checkout_url': session['url']
        })
        
    except Exception as e:
        current_app.logger.error(f'Stripe upgrade error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при создании платёжной сессии'
        }), 500


@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Отменить подписку"""
    if not current_user.stripe_subscription_id:
        return jsonify({
            'success': False,
            'error': 'Активная подписка не найдена'
        }), 400
    
    try:
        from services.stripe_handler import StripeHandler
        
        handler = StripeHandler()
        
        # Отменяем подписку в Stripe (в конце периода)
        handler.cancel_subscription(
            current_user.stripe_subscription_id,
            at_period_end=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Подписка будет отменена в конце текущего периода'
        })
        
    except Exception as e:
        current_app.logger.error(f'Stripe cancel error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при отмене подписки'
        }), 500


@subscription_bp.route('/portal')
@login_required
def customer_portal():
    """Получить ссылку на Stripe Customer Portal"""
    if not current_user.stripe_customer_id:
        return jsonify({
            'success': False,
            'error': 'Stripe аккаунт не найден'
        }), 400
    
    try:
        from services.stripe_handler import StripeHandler
        
        handler = StripeHandler()
        
        session = handler.create_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url=f"{request.host_url}settings"
        )
        
        return jsonify({
            'success': True,
            'portal_url': session['url']
        })
        
    except Exception as e:
        current_app.logger.error(f'Stripe portal error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при создании сессии портала'
        }), 500
