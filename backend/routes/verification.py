"""
API для верификации владения доменом
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database import db
from models import DomainVerification
from services.domain_verifier import DomainVerifier


verification_bp = Blueprint('verification', __name__)


@verification_bp.route('/request', methods=['POST'])
@login_required
def request_verification():
    """Запросить верификацию домена"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL обязателен'}), 400
        
        # Извлечь домен
        domain = DomainVerifier.extract_domain(url)
        
        if not domain:
            return jsonify({'error': 'Некорректный URL'}), 400
        
        # Проверить существующую верификацию
        existing = DomainVerification.query.filter_by(
            user_id=current_user.id,
            domain=domain
        ).first()
        
        # Если есть активная верификация - вернуть её
        if existing and existing.is_active:
            return jsonify({
                'message': 'Домен уже верифицирован',
                'verification': existing.to_dict(),
                'instructions': DomainVerifier.get_verification_instructions(domain, existing.verification_code)
            }), 200
        
        # Если есть неактивная - удалить
        if existing:
            db.session.delete(existing)
        
        # Создать новую верификацию
        verification_code = DomainVerifier.generate_verification_code(domain, current_user.id)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        verification = DomainVerification(
            user_id=current_user.id,
            domain=domain,
            url=url,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        db.session.add(verification)
        db.session.commit()
        
        # Получить инструкции
        instructions = DomainVerifier.get_verification_instructions(domain, verification_code)
        
        return jsonify({
            'message': 'Код верификации создан',
            'verification': verification.to_dict(),
            'instructions': instructions
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@verification_bp.route('/verify', methods=['POST'])
@login_required
def verify_domain():
    """Проверить верификацию домена"""
    try:
        data = request.get_json()
        verification_id = data.get('verification_id')
        
        if not verification_id:
            return jsonify({'error': 'ID верификации обязателен'}), 400
        
        # Получить верификацию
        verification = DomainVerification.query.filter_by(
            id=verification_id,
            user_id=current_user.id
        ).first()
        
        if not verification:
            return jsonify({'error': 'Верификация не найдена'}), 404
        
        # Проверить срок
        if verification.is_expired:
            return jsonify({'error': 'Срок верификации истёк. Запросите новый код'}), 400
        
        # Если уже верифицирован
        if verification.is_verified:
            return jsonify({
                'message': 'Домен уже верифицирован',
                'verification': verification.to_dict()
            }), 200
        
        # Обновить попытки
        verification.attempts += 1
        verification.last_attempt_at = datetime.utcnow()
        
        # Проверить верификацию
        success, message, method = DomainVerifier.verify_domain(
            verification.url,
            verification.verification_code,
            timeout=10
        )
        
        if success:
            verification.is_verified = True
            verification.verification_method = method
            verification.verified_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': message,
                'verification': verification.to_dict()
            }), 200
        else:
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': message,
                'verification': verification.to_dict()
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@verification_bp.route('/check/<domain>', methods=['GET'])
@login_required
def check_verification_status(domain):
    """Проверить статус верификации домена"""
    try:
        # Админы всегда считаются верифицированными
        if current_user.is_admin:
            return jsonify({
                'is_verified': True,
                'is_admin': True,
                'message': 'Администратор - верификация не требуется'
            }), 200
        
        # Извлечь домен из URL если передан
        domain = DomainVerifier.extract_domain(domain)
        
        verification = DomainVerification.query.filter_by(
            user_id=current_user.id,
            domain=domain
        ).first()
        
        if not verification:
            return jsonify({
                'is_verified': False,
                'message': 'Верификация не запрошена'
            }), 200
        
        return jsonify({
            'is_verified': verification.is_active,
            'verification': verification.to_dict() if verification else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@verification_bp.route('/list', methods=['GET'])
@login_required
def list_verifications():
    """Список всех верификаций пользователя"""
    try:
        verifications = DomainVerification.query.filter_by(
            user_id=current_user.id
        ).order_by(DomainVerification.created_at.desc()).all()
        
        return jsonify({
            'verifications': [v.to_dict() for v in verifications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


@verification_bp.route('/<int:verification_id>', methods=['DELETE'])
@login_required
def delete_verification(verification_id):
    """Удалить верификацию"""
    try:
        verification = DomainVerification.query.filter_by(
            id=verification_id,
            user_id=current_user.id
        ).first()
        
        if not verification:
            return jsonify({'error': 'Верификация не найдена'}), 404
        
        db.session.delete(verification)
        db.session.commit()
        
        return jsonify({'message': 'Верификация удалена'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500
