"""
Маршруты аутентификации
Регистрация, вход, выход пользователей
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import re

from database import db
from models import User

auth_bp = Blueprint('auth', __name__)


# ==================== ВАЛИДАЦИЯ ====================

def validate_email(email):
    """Валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Passwort-Validierung
    Mindestens 8 Zeichen, mindestens ein Buchstabe und eine Ziffer
    """
    if len(password) < 8:
        return False, 'Passwort muss mindestens 8 Zeichen lang sein'
    if not re.search(r'[A-Za-z]', password):
        return False, 'Passwort muss mindestens einen Buchstaben enthalten'
    if not re.search(r'\d', password):
        return False, 'Passwort muss mindestens eine Ziffer enthalten'
    return True, 'OK'


# ==================== СТРАНИЦЫ ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница и обработка регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        company_name = request.form.get('company_name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        
        # Валидация
        errors = []
        
        if not email:
            errors.append('Email обязателен')
        elif not validate_email(email):
            errors.append('Некорректный формат email')
        elif User.query.filter_by(email=email).first():
            errors.append('Этот email уже зарегистрирован')
        
        if not password:
            errors.append('Пароль обязателен')
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)
        
        if password != password_confirm:
            errors.append('Passwörter stimmen nicht überein')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', 
                                   email=email, 
                                   company_name=company_name,
                                   full_name=full_name)
        
        # Создание пользователя
        try:
            user = User(
                email=email,
                company_name=company_name if company_name else None,
                full_name=full_name if full_name else None
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Fehler bei der Registrierung. Bitte versuchen Sie es erneut.', 'danger')
            return render_template('register.html', 
                                   email=email, 
                                   company_name=company_name,
                                   full_name=full_name)
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница и обработка входа"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        if not email or not password:
            flash('Bitte geben Sie E-Mail und Passwort ein', 'danger')
            return render_template('login.html', email=email)
        
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Ungültige E-Mail oder Passwort', 'danger')
            return render_template('login.html', email=email)
        
        if not user.is_active:
            flash('Ihr Konto ist gesperrt', 'danger')
            return render_template('login.html', email=email)
        
        # Вход успешен
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash(f'Willkommen, {user.full_name or user.email}!', 'success')
        
        # Редирект на запрошенную страницу или dashboard
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Sie haben sich abgemeldet', 'info')
    return redirect(url_for('auth.login'))


# ==================== API ENDPOINTS ====================

@auth_bp.route('/auth/user')
@login_required
def get_current_user():
    """Получить информацию о текущем пользователе"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })


@auth_bp.route('/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """Смена пароля"""
    data = request.get_json() or request.form
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Проверка текущего пароля
    if not current_user.check_password(current_password):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Aktuelles Passwort ist falsch'}), 400
        flash('Aktuelles Passwort ist falsch', 'danger')
        return redirect(url_for('dashboard.settings'))
    
    # Валидация нового пароля
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        if request.is_json:
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('dashboard.settings'))
    
    if new_password != confirm_password:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Passwörter stimmen nicht überein'}), 400
        flash('Passwörter stimmen nicht überein', 'danger')
        return redirect(url_for('dashboard.settings'))
    
    # Смена пароля
    try:
        current_user.set_password(new_password)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Passwort erfolgreich geändert'})
        flash('Passwort erfolgreich geändert', 'success')
        return redirect(url_for('dashboard.settings'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Fehler beim Ändern des Passworts'}), 500
        flash('Fehler beim Ändern des Passworts', 'danger')
        return redirect(url_for('dashboard.settings'))


@auth_bp.route('/auth/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Обновление профиля"""
    data = request.get_json() or request.form
    
    full_name = data.get('full_name', '').strip()
    company_name = data.get('company_name', '').strip()
    phone = data.get('phone', '').strip()
    
    try:
        current_user.full_name = full_name if full_name else None
        current_user.company_name = company_name if company_name else None
        current_user.phone = phone if phone else None
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Profil aktualisiert', 'user': current_user.to_dict()})
        flash('Profil aktualisiert', 'success')
        return redirect(url_for('dashboard.settings'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Fehler beim Aktualisieren des Profils'}), 500
        flash('Fehler beim Aktualisieren des Profils', 'danger')
        return redirect(url_for('dashboard.settings'))


# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

@auth_bp.before_app_request
def update_last_seen():
    """Обновление времени последней активности"""
    if current_user.is_authenticated:
        # Обновляем не чаще раза в минуту для производительности
        pass
