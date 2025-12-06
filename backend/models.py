"""
SQLAlchemy модели для SecurityCheck
Все таблицы создаются в схеме security_check_schema
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum
import enum

from database import db


# ==================== ENUMS ====================

class SubscriptionPlan(enum.Enum):
    """Тарифные планы"""
    FREE = 'free'
    STARTER = 'starter'
    PRO = 'pro'


class ScanStatus(enum.Enum):
    """Статус сканирования"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class SeverityLevel(enum.Enum):
    """Уровни критичности"""
    INFO = 'info'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class ThreatLevel(enum.Enum):
    """Уровни угрозы"""
    SAFE = 'safe'
    WARNING = 'warning'
    DANGER = 'danger'


# ==================== USER MODEL ====================

class User(UserMixin, db.Model):
    """Модель пользователя"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Профиль
    company_name = db.Column(db.String(255), nullable=True)
    full_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    
    # Подписка
    subscription_plan = db.Column(
        db.Enum(SubscriptionPlan), 
        default=SubscriptionPlan.FREE, 
        nullable=False
    )
    subscription_expires = db.Column(db.DateTime, nullable=True)
    
    # Stripe
    stripe_customer_id = db.Column(db.String(255), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    
    # Метаданные
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Связи
    web_scans = db.relationship('WebScan', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    link_checks = db.relationship('LinkCheck', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    domain_intel = db.relationship('DomainIntel', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Установить пароль"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_subscription_active(self):
        """Проверить активна ли подписка"""
        if self.subscription_plan == SubscriptionPlan.FREE:
            return True
        if not self.subscription_expires:
            return False
        return self.subscription_expires > datetime.utcnow()
    
    @property
    def plan_name(self):
        """Получить название плана"""
        return self.subscription_plan.value.capitalize()
    
    def get_daily_limit(self, feature):
        """
        Получить дневной лимит для функции
        
        Args:
            feature: название функции (web_scans, link_checks, etc.)
            
        Returns:
            int: лимит (-1 = безлимит, 0 = недоступно)
        """
        from config import Config
        plan = self.subscription_plan.value
        limits = Config.RATE_LIMITS.get(plan, Config.RATE_LIMITS['free'])
        return limits.get(feature, 0)
    
    def get_usage_today(self, feature):
        """
        Получить использование за сегодня
        
        Args:
            feature: название функции
            
        Returns:
            int: количество использований сегодня
        """
        from datetime import datetime
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        if feature == 'web_scans':
            from models import WebScan
            return db.session.query(WebScan).filter(
                WebScan.user_id == self.id,
                WebScan.created_at >= today_start
            ).count()
        elif feature == 'link_checks':
            from models import LinkCheck
            return db.session.query(LinkCheck).filter(
                LinkCheck.user_id == self.id,
                LinkCheck.created_at >= today_start
            ).count()
        elif feature == 'network_scans':
            from models import NetworkScan
            return db.session.query(NetworkScan).filter(
                NetworkScan.user_id == self.id,
                NetworkScan.created_at >= today_start
            ).count()
        elif feature == 'domain_lookups':
            from models import DomainIntel
            return db.session.query(DomainIntel).filter(
                DomainIntel.user_id == self.id,
                DomainIntel.created_at >= today_start
            ).count()
        return 0
    
    def can_use_feature(self, feature):
        """
        Проверить может ли пользователь использовать функцию
        
        Args:
            feature: название функции
            
        Returns:
            tuple: (bool, str) - можно ли использовать и причина
        """
        limit = self.get_daily_limit(feature)
        
        if limit == 0:
            return False, f'Функция недоступна для плана {self.plan_name}'
        
        if limit == -1:
            return True, 'Безлимитно'
        
        usage = self.get_usage_today(feature)
        if usage >= limit:
            return False, f'Достигнут дневной лимит ({usage}/{limit})'
        
        return True, f'Осталось {limit - usage} из {limit}'
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'full_name': self.full_name,
            'subscription_plan': self.subscription_plan.value,
            'subscription_expires': self.subscription_expires.isoformat() if self.subscription_expires else None,
            'is_subscription_active': self.is_subscription_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


# ==================== WEB SCAN MODELS ====================

class WebScan(db.Model):
    """Модель сканирования веб-сайта"""
    
    __tablename__ = 'web_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Информация о цели
    target_url = db.Column(db.String(2048), nullable=False)
    target_domain = db.Column(db.String(255), nullable=False, index=True)
    
    # Верификация владения
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_id = db.Column(db.Integer, db.ForeignKey('domain_verifications.id'), nullable=True)
    
    # Статус сканирования
    status = db.Column(db.Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    progress = db.Column(db.Integer, default=0)  # 0-100
    
    # Результаты
    security_score = db.Column(db.Integer, nullable=True)  # 0-100
    total_issues = db.Column(db.Integer, default=0)
    critical_issues = db.Column(db.Integer, default=0)
    high_issues = db.Column(db.Integer, default=0)
    medium_issues = db.Column(db.Integer, default=0)
    low_issues = db.Column(db.Integer, default=0)
    
    # AI объяснение
    ai_summary = db.Column(db.Text, nullable=True)
    ai_recommendations = db.Column(db.Text, nullable=True)
    
    # Метаданные
    scan_duration = db.Column(db.Float, nullable=True)  # в секундах
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Связи
    results = db.relationship('ScanResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_security_score(self):
        """Рассчитать Security Score на основе найденных проблем"""
        if self.total_issues == 0:
            self.security_score = 100
            return
        
        # Веса для разных уровней критичности
        weights = {
            'critical': 25,
            'high': 15,
            'medium': 10,
            'low': 5
        }
        
        penalty = (
            self.critical_issues * weights['critical'] +
            self.high_issues * weights['high'] +
            self.medium_issues * weights['medium'] +
            self.low_issues * weights['low']
        )
        
        self.security_score = max(0, 100 - penalty)
    
    def to_dict(self, include_results=False):
        """Преобразовать в словарь для API"""
        # Calculate category scores based on results
        ssl_score = 100
        headers_score = 100
        html_score = 100
        
        if include_results or self.results.count() > 0:
            results_list = self.results.all() if not include_results else self.results.all()
            
            for result in results_list:
                # Category score penalties
                penalty = 0
                if result.severity == SeverityLevel.CRITICAL:
                    penalty = 40
                elif result.severity == SeverityLevel.HIGH:
                    penalty = 25
                elif result.severity == SeverityLevel.MEDIUM:
                    penalty = 15
                elif result.severity == SeverityLevel.LOW:
                    penalty = 5
                
                # Apply penalty to correct category
                if result.category == 'ssl':
                    ssl_score = max(0, ssl_score - penalty)
                elif result.category == 'headers':
                    headers_score = max(0, headers_score - penalty)
                elif result.category in ['html', 'forms', 'cookies']:
                    html_score = max(0, html_score - penalty)
        
        data = {
            'id': self.id,
            'target_url': self.target_url,
            'target_domain': self.target_domain,
            'is_verified': self.is_verified,
            'status': self.status.value,
            'progress': self.progress,
            'security_score': self.security_score,
            'ssl_score': ssl_score,
            'headers_score': headers_score,
            'html_score': html_score,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'high_issues': self.high_issues,
            'medium_issues': self.medium_issues,
            'low_issues': self.low_issues,
            'ai_summary': self.ai_summary,
            'ai_recommendations': self.ai_recommendations,
            'scan_duration': self.scan_duration,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_results:
            data['results'] = [r.to_dict() for r in self.results.all()]
        
        return data
    
    def __repr__(self):
        return f'<WebScan {self.target_url}>'


class ScanResult(db.Model):
    """Модель результата сканирования"""
    
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('web_scans.id'), nullable=False, index=True)
    
    # Информация о проблеме
    category = db.Column(db.String(100), nullable=False)  # ssl, headers, html, etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Критичность
    severity = db.Column(db.Enum(SeverityLevel), nullable=False)
    
    # Технические детали
    raw_data = db.Column(db.JSON, nullable=True)
    evidence = db.Column(db.Text, nullable=True)
    
    # AI объяснение
    ai_explanation = db.Column(db.Text, nullable=True)
    ai_fix = db.Column(db.Text, nullable=True)
    
    # Информация из базы знаний (видео, стоимость ущерба, решения)
    vulnerability_info = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'raw_data': self.raw_data,
            'evidence': self.evidence,
            'ai_explanation': self.ai_explanation,
            'ai_fix': self.ai_fix,
            'vulnerability_info': self.vulnerability_info,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ScanResult {self.title}>'


# ==================== LINK CHECK MODEL ====================

class LinkCheck(db.Model):
    """Модель проверки ссылки"""
    
    __tablename__ = 'link_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Информация о ссылке
    original_url = db.Column(db.String(2048), nullable=False)
    final_url = db.Column(db.String(2048), nullable=True)  # После редиректов
    domain = db.Column(db.String(255), nullable=False, index=True)
    
    # Результаты
    threat_level = db.Column(db.Enum(ThreatLevel), nullable=False)
    confidence = db.Column(db.Integer, default=0)  # 0-100
    
    # Детали проверок
    virustotal_result = db.Column(db.JSON, nullable=True)
    google_safebrowsing_result = db.Column(db.JSON, nullable=True)
    urlhaus_result = db.Column(db.JSON, nullable=True)
    
    # Дополнительная информация
    is_shortened = db.Column(db.Boolean, default=False)
    ssl_valid = db.Column(db.Boolean, nullable=True)
    domain_age_days = db.Column(db.Integer, nullable=True)
    
    # Причины предупреждения
    reasons = db.Column(db.JSON, nullable=True)  # Список причин
    
    # AI объяснение
    ai_explanation = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        # Обработка результатов VirusTotal
        virustotal_score = None  # None если нет данных, 0 если проверено и чисто
        if self.virustotal_result and isinstance(self.virustotal_result, dict):
            if 'error' not in self.virustotal_result and 'status' not in self.virustotal_result:
                # Есть результаты сканирования
                virustotal_score = self.virustotal_result.get('malicious', 0)
            elif self.virustotal_result.get('status') == 'queued':
                # Отправлено на сканирование - это не угроза
                virustotal_score = 0
        
        # Обработка результатов Google Safe Browsing
        safe_browsing_threats = []
        if self.google_safebrowsing_result and isinstance(self.google_safebrowsing_result, dict):
            if self.google_safebrowsing_result.get('is_dangerous'):
                threat_type = self.google_safebrowsing_result.get('threat_type', 'UNKNOWN')
                safe_browsing_threats.append(threat_type)
        
        # Обработка результатов URLhaus
        urlhaus_status = None
        if self.urlhaus_result and isinstance(self.urlhaus_result, dict):
            if self.urlhaus_result.get('is_malicious'):
                urlhaus_status = 'online'
            else:
                urlhaus_status = 'clean'
        
        # Форматирование возраста домена
        domain_age = None
        if self.domain_age_days is not None:
            if self.domain_age_days < 365:
                domain_age = f'{self.domain_age_days} дней'
            else:
                years = self.domain_age_days // 365
                domain_age = f'{years} лет' if years > 1 else f'{years} год'
        
        return {
            'id': self.id,
            'original_url': self.original_url,
            'final_url': self.final_url,
            'domain': self.domain,
            'threat_level': self.threat_level.value,
            'confidence_score': self.confidence,
            'is_shortened': self.is_shortened,
            'ssl_valid': self.ssl_valid,
            'domain_age': domain_age,
            'reasons': self.reasons or [],
            'ai_explanation': self.ai_explanation,
            'virustotal_score': virustotal_score,
            'safe_browsing_threats': safe_browsing_threats,
            'urlhaus_status': urlhaus_status,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<LinkCheck {self.original_url}>'


# ==================== FILE ANALYSIS MODEL ====================

# ==================== NETWORK SCAN MODEL ====================

class NetworkScan(db.Model):
    """Модель сетевого сканирования"""
    
    __tablename__ = 'network_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Цель сканирования
    target = db.Column(db.String(255), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False)  # 'ip' или 'domain'
    resolved_ip = db.Column(db.String(45), nullable=True)  # IPv4/IPv6
    
    # Параметры сканирования
    scan_ports = db.Column(db.Boolean, default=True)
    scan_services = db.Column(db.Boolean, default=True)
    custom_ports = db.Column(db.JSON, nullable=True)  # Пользовательский список портов
    
    # Статус
    status = db.Column(db.Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    scan_progress = db.Column(db.Integer, default=0)  # 0-100%
    
    # Результаты
    threat_level = db.Column(db.Enum(ThreatLevel), nullable=True)
    open_ports = db.Column(db.JSON, nullable=True)  # Список открытых портов
    services_detected = db.Column(db.JSON, nullable=True)  # Обнаруженные сервисы
    vulnerabilities = db.Column(db.JSON, nullable=True)  # Найденные уязвимости
    os_detection = db.Column(db.String(100), nullable=True)  # Определение ОС
    
    # Статистика
    total_ports_scanned = db.Column(db.Integer, default=0)
    scan_duration = db.Column(db.Float, nullable=True)  # в секундах
    
    # AI объяснение
    ai_explanation = db.Column(db.Text, nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    scanned_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'target': self.target,
            'target_type': self.target_type,
            'resolved_ip': self.resolved_ip,
            'status': self.status.value,
            'scan_progress': self.scan_progress,
            'threat_level': self.threat_level.value if self.threat_level else None,
            'open_ports': self.open_ports or [],
            'services_detected': self.services_detected or {},
            'vulnerabilities': self.vulnerabilities or [],
            'os_detection': self.os_detection,
            'total_ports_scanned': self.total_ports_scanned,
            'scan_duration': self.scan_duration,
            'ai_explanation': self.ai_explanation,
            'ai_recommendation': self.ai_recommendation,
            'created_at': self.created_at.isoformat(),
            'scanned_at': self.scanned_at.isoformat() if self.scanned_at else None
        }
    
    def __repr__(self):
        return f'<NetworkScan {self.target}>'


# ==================== DOMAIN INTEL MODEL ====================

class DomainIntel(db.Model):
    """Модель информации о домене"""
    
    __tablename__ = 'domain_intel'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Информация о домене
    domain = db.Column(db.String(255), nullable=False, index=True)
    
    # WHOIS данные
    whois_registrar = db.Column(db.String(255), nullable=True)
    whois_registrant = db.Column(db.String(255), nullable=True)
    whois_created_date = db.Column(db.DateTime, nullable=True)
    whois_expiry_date = db.Column(db.DateTime, nullable=True)
    whois_updated_date = db.Column(db.DateTime, nullable=True)
    whois_nameservers = db.Column(db.JSON, nullable=True)
    whois_raw = db.Column(db.JSON, nullable=True)
    
    # DNS записи
    dns_a_records = db.Column(db.JSON, nullable=True)
    dns_aaaa_records = db.Column(db.JSON, nullable=True)
    dns_mx_records = db.Column(db.JSON, nullable=True)
    dns_txt_records = db.Column(db.JSON, nullable=True)
    dns_ns_records = db.Column(db.JSON, nullable=True)
    
    # Email безопасность
    has_spf = db.Column(db.Boolean, nullable=True)
    has_dkim = db.Column(db.Boolean, nullable=True)
    has_dmarc = db.Column(db.Boolean, nullable=True)
    email_security_score = db.Column(db.Integer, nullable=True)  # 0-100
    
    # Репутация
    domain_age_days = db.Column(db.Integer, nullable=True)
    reputation_score = db.Column(db.Integer, nullable=True)  # 0-100
    ip_reputation = db.Column(db.JSON, nullable=True)
    
    # Wayback Machine
    wayback_snapshots = db.Column(db.Integer, nullable=True)
    wayback_first_capture = db.Column(db.DateTime, nullable=True)
    wayback_last_capture = db.Column(db.DateTime, nullable=True)
    
    # AI объяснение
    ai_summary = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'domain': self.domain,
            'whois': {
                'registrar': self.whois_registrar,
                'registrant': self.whois_registrant,
                'created_date': self.whois_created_date.isoformat() if self.whois_created_date else None,
                'expiry_date': self.whois_expiry_date.isoformat() if self.whois_expiry_date else None,
                'nameservers': self.whois_nameservers
            },
            'dns': {
                'a_records': self.dns_a_records,
                'mx_records': self.dns_mx_records,
                'txt_records': self.dns_txt_records,
                'ns_records': self.dns_ns_records
            },
            'email_security': {
                'has_spf': self.has_spf,
                'has_dkim': self.has_dkim,
                'has_dmarc': self.has_dmarc,
                'score': self.email_security_score
            },
            'domain_age_days': self.domain_age_days,
            'reputation_score': self.reputation_score,
            'wayback': {
                'snapshots': self.wayback_snapshots,
                'first_capture': self.wayback_first_capture.isoformat() if self.wayback_first_capture else None,
                'last_capture': self.wayback_last_capture.isoformat() if self.wayback_last_capture else None
            },
            'ai_summary': self.ai_summary,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<DomainIntel {self.domain}>'


# ==================== STRIPE EVENT MODEL ====================

class StripeEvent(db.Model):
    """Модель события Stripe"""
    
    __tablename__ = 'stripe_events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Идентификаторы Stripe
    stripe_event_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = db.Column(db.String(255), nullable=True, index=True)
    
    # Информация о событии
    event_type = db.Column(db.String(100), nullable=False)  # customer.subscription.created, etc.
    event_data = db.Column(db.JSON, nullable=True)
    
    # Статус обработки
    processed = db.Column(db.Boolean, default=False, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<StripeEvent {self.stripe_event_id}>'


# ==================== DOMAIN VERIFICATION ====================

class DomainVerification(db.Model):
    """Модель верификации владения доменом"""
    
    __tablename__ = 'domain_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Информация о домене
    domain = db.Column(db.String(255), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False)
    
    # Верификация
    verification_code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_method = db.Column(db.String(50), nullable=True)  # txt_file, meta_tag
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Срок действия
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Метаданные
    attempts = db.Column(db.Integer, default=0, nullable=False)
    last_attempt_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('domain_verifications', lazy='dynamic'))
    
    @property
    def is_expired(self):
        """Проверить истёк ли срок"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self):
        """Проверить активна ли верификация"""
        return self.is_verified and not self.is_expired
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'domain': self.domain,
            'url': self.url,
            'verification_code': self.verification_code,
            'is_verified': self.is_verified,
            'verification_method': self.verification_method,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'expires_at': self.expires_at.isoformat(),
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<DomainVerification {self.domain} verified={self.is_verified}>'


# ==================== ДОПОЛНИТЕЛЬНЫЕ ИНДЕКСЫ ====================

# Создаём составные индексы для часто используемых запросов
db.Index('idx_web_scans_user_date', WebScan.user_id, WebScan.created_at.desc())
db.Index('idx_link_checks_user_date', LinkCheck.user_id, LinkCheck.created_at.desc())
db.Index('idx_domain_intel_user_date', DomainIntel.user_id, DomainIntel.created_at.desc())
db.Index('idx_domain_verifications_user_domain', DomainVerification.user_id, DomainVerification.domain)
