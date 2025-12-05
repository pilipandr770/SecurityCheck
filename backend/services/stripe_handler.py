"""
Обработчик Stripe платежей
Создание подписок, управление платежами
"""

import stripe
import os
from datetime import datetime


class StripeHandler:
    """Обработчик Stripe API"""
    
    def __init__(self, api_key=None):
        """
        Инициализация
        
        Args:
            api_key: Stripe Secret Key
        """
        self.api_key = api_key or os.environ.get('STRIPE_SECRET_KEY')
        stripe.api_key = self.api_key
    
    def create_customer(self, email: str, name: str = None, metadata: dict = None):
        """
        Создать Stripe Customer
        
        Args:
            email: Email пользователя
            name: Имя пользователя
            metadata: Дополнительные метаданные
            
        Returns:
            dict: Customer объект
        """
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
        
        return {
            'id': customer.id,
            'email': customer.email,
            'name': customer.name
        }
    
    def create_checkout_session(self, customer_id: str, plan: str, billing: str,
                                success_url: str, cancel_url: str):
        """
        Создать Checkout Session для подписки
        
        Args:
            customer_id: ID Stripe Customer
            plan: Название плана (starter, pro)
            billing: Тип биллинга (monthly, yearly)
            success_url: URL после успешной оплаты
            cancel_url: URL при отмене
            
        Returns:
            dict: Checkout Session
        """
        # Price IDs должны быть созданы в Stripe Dashboard
        # Здесь используются примеры, замените на реальные
        price_ids = {
            'starter_monthly': os.environ.get('STRIPE_STARTER_MONTHLY_PRICE_ID', 'price_starter_monthly'),
            'starter_yearly': os.environ.get('STRIPE_STARTER_YEARLY_PRICE_ID', 'price_starter_yearly'),
            'pro_monthly': os.environ.get('STRIPE_PRO_MONTHLY_PRICE_ID', 'price_pro_monthly'),
            'pro_yearly': os.environ.get('STRIPE_PRO_YEARLY_PRICE_ID', 'price_pro_yearly')
        }
        
        price_id = price_ids.get(f'{plan}_{billing}')
        
        if not price_id:
            raise ValueError(f'Invalid plan or billing: {plan}/{billing}')
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'plan': plan,
                'billing': billing
            }
        )
        
        return {
            'id': session.id,
            'url': session.url
        }
    
    def create_portal_session(self, customer_id: str, return_url: str):
        """
        Создать Customer Portal Session
        
        Args:
            customer_id: ID Stripe Customer
            return_url: URL для возврата
            
        Returns:
            dict: Portal Session
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        
        return {
            'id': session.id,
            'url': session.url
        }
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True):
        """
        Отменить подписку
        
        Args:
            subscription_id: ID подписки
            at_period_end: Отменить в конце периода или сразу
            
        Returns:
            dict: Subscription объект
        """
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.cancel(subscription_id)
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'cancel_at_period_end': subscription.cancel_at_period_end
        }
    
    def get_subscription(self, subscription_id: str):
        """
        Получить информацию о подписке
        
        Args:
            subscription_id: ID подписки
            
        Returns:
            dict: Информация о подписке
        """
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'plan': subscription.items.data[0].price.id if subscription.items.data else None
        }
    
    def get_customer_subscriptions(self, customer_id: str):
        """
        Получить все подписки клиента
        
        Args:
            customer_id: ID Stripe Customer
            
        Returns:
            list: Список подписок
        """
        subscriptions = stripe.Subscription.list(customer=customer_id)
        
        return [{
            'id': sub.id,
            'status': sub.status,
            'current_period_end': datetime.fromtimestamp(sub.current_period_end)
        } for sub in subscriptions.data]
