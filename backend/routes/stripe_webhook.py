"""
Stripe Webhook обработчик
Обрабатывает события от Stripe (платежи, подписки)
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from database import db
from models import User, StripeEvent, SubscriptionPlan

stripe_webhook_bp = Blueprint('stripe_webhook', __name__)


@stripe_webhook_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Обработать webhook от Stripe"""
    import stripe
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        current_app.logger.error('Invalid Stripe payload')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        current_app.logger.error('Invalid Stripe signature')
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Проверяем не обрабатывали ли уже это событие
    existing = StripeEvent.query.filter_by(stripe_event_id=event['id']).first()
    if existing:
        return jsonify({'status': 'already processed'}), 200
    
    # Сохраняем событие
    stripe_event = StripeEvent(
        stripe_event_id=event['id'],
        event_type=event['type'],
        event_data=event['data'],
        stripe_customer_id=event['data']['object'].get('customer')
    )
    db.session.add(stripe_event)
    
    try:
        # Обрабатываем разные типы событий
        if event['type'] == 'customer.subscription.created':
            handle_subscription_created(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        
        elif event['type'] == 'checkout.session.completed':
            handle_checkout_completed(event['data']['object'])
        
        stripe_event.processed = True
        stripe_event.processed_at = datetime.utcnow()
        
    except Exception as e:
        current_app.logger.error(f'Webhook processing error: {e}')
        stripe_event.error_message = str(e)
    
    db.session.commit()
    
    return jsonify({'status': 'success'}), 200


def handle_subscription_created(subscription):
    """Обработка создания подписки"""
    customer_id = subscription.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if not user:
        current_app.logger.warning(f'User not found for customer {customer_id}')
        return
    
    # Определяем план по price_id
    plan = get_plan_from_subscription(subscription)
    
    user.subscription_plan = plan
    user.stripe_subscription_id = subscription['id']
    
    # Устанавливаем дату окончания
    if subscription.get('current_period_end'):
        user.subscription_expires = datetime.fromtimestamp(
            subscription['current_period_end']
        )
    
    current_app.logger.info(f'Subscription created for user {user.id}: {plan.value}')


def handle_subscription_updated(subscription):
    """Обработка обновления подписки"""
    customer_id = subscription.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if not user:
        return
    
    # Обновляем план
    plan = get_plan_from_subscription(subscription)
    user.subscription_plan = plan
    
    # Обновляем дату окончания
    if subscription.get('current_period_end'):
        user.subscription_expires = datetime.fromtimestamp(
            subscription['current_period_end']
        )
    
    # Проверяем статус
    if subscription.get('cancel_at_period_end'):
        current_app.logger.info(f'Subscription will be cancelled for user {user.id}')


def handle_subscription_deleted(subscription):
    """Обработка удаления подписки"""
    customer_id = subscription.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if not user:
        return
    
    user.subscription_plan = SubscriptionPlan.FREE
    user.stripe_subscription_id = None
    user.subscription_expires = None
    
    current_app.logger.info(f'Subscription cancelled for user {user.id}')


def handle_payment_succeeded(invoice):
    """Обработка успешного платежа"""
    customer_id = invoice.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        current_app.logger.info(f'Payment succeeded for user {user.id}')


def handle_payment_failed(invoice):
    """Обработка неудачного платежа"""
    customer_id = invoice.get('customer')
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        current_app.logger.warning(f'Payment failed for user {user.id}')
        # TODO: Отправить email пользователю


def handle_checkout_completed(session):
    """Обработка завершения Checkout сессии"""
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if customer_id and subscription_id:
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.stripe_subscription_id = subscription_id
            current_app.logger.info(f'Checkout completed for user {user.id}')


def get_plan_from_subscription(subscription):
    """
    Определить план по данным подписки Stripe
    """
    # Получаем price_id из items
    items = subscription.get('items', {}).get('data', [])
    if not items:
        return SubscriptionPlan.FREE
    
    price_id = items[0].get('price', {}).get('id', '')
    
    # Здесь должно быть сопоставление price_id с планами
    # В реальном проекте нужно хранить эти ID в конфиге
    
    # По умолчанию смотрим на сумму
    amount = items[0].get('price', {}).get('unit_amount', 0)
    
    if amount >= 1500:  # €15
        return SubscriptionPlan.PRO
    elif amount >= 500:  # €5
        return SubscriptionPlan.STARTER
    else:
        return SubscriptionPlan.FREE
