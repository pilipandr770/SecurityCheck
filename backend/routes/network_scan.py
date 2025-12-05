"""
API маршруты для сетевого сканирования
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import ipaddress
import re

from database import db
from models import NetworkScan, ScanStatus, ThreatLevel

network_scan_bp = Blueprint('network_scan', __name__)


def is_valid_target(target):
    """Проверить валидность цели сканирования (IP или домен)"""
    # Проверяем IP адрес
    try:
        ipaddress.ip_address(target)
        return True, 'ip'
    except ValueError:
        pass
    
    # Проверяем домен
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, target):
        return True, 'domain'
    
    return False, None


def is_private_ip(ip_str):
    """Проверить является ли IP приватным"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False


@network_scan_bp.route('/start', methods=['POST'])
@login_required
def start_scan():
    """Запустить сетевое сканирование"""
    # Проверка лимитов
    can_scan, message = current_user.can_use_feature('network_scans')
    if not can_scan:
        return jsonify({
            'success': False,
            'error': message
        }), 429
    
    # Получаем данные из запроса
    data = request.get_json()
    
    if not data or 'target' not in data:
        return jsonify({
            'success': False,
            'error': 'Не указана цель сканирования'
        }), 400
    
    target = data['target'].strip()
    
    # Валидация цели
    is_valid, target_type = is_valid_target(target)
    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Неверный формат цели. Укажите IP адрес или домен'
        }), 400
    
    # Получаем опции сканирования
    scan_ports = data.get('scan_ports', True)
    scan_services = data.get('scan_services', True)
    custom_ports = data.get('custom_ports', None)  # Список портов или None для стандартных
    
    try:
        # Создаём запись в БД
        scan = NetworkScan(
            user_id=current_user.id,
            target=target,
            target_type=target_type,
            scan_ports=scan_ports,
            scan_services=scan_services,
            custom_ports=custom_ports,
            status=ScanStatus.PENDING
        )
        
        db.session.add(scan)
        db.session.commit()
        
        # Запускаем сканирование
        run_network_scan(scan.id)
        
        return jsonify({
            'success': True,
            'scan_id': scan.id,
            'message': 'Сетевое сканирование запущено'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Network scan start error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при запуске сканирования'
        }), 500


@network_scan_bp.route('/<int:scan_id>')
@login_required
def get_scan(scan_id):
    """Получить результаты сетевого сканирования"""
    scan = NetworkScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'scan': scan.to_dict()
    })


@network_scan_bp.route('/<int:scan_id>/status')
@login_required
def get_scan_status(scan_id):
    """Получить статус сканирования"""
    scan = NetworkScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'status': scan.status.value,
        'threat_level': scan.threat_level.value if scan.threat_level else None,
        'progress': scan.scan_progress
    })


@network_scan_bp.route('/history')
@login_required
def get_history():
    """Получить историю сетевых сканирований"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    scans = NetworkScan.query.filter_by(user_id=current_user.id)\
        .order_by(NetworkScan.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'scans': [s.to_dict() for s in scans.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': scans.total,
            'pages': scans.pages
        }
    })


@network_scan_bp.route('/<int:scan_id>', methods=['DELETE'])
@login_required
def delete_scan(scan_id):
    """Удалить результаты сканирования"""
    scan = NetworkScan.query.filter_by(
        id=scan_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Удаляем запись из БД
        db.session.delete(scan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Результаты сканирования удалены'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Scan delete error: {e}')
        return jsonify({
            'success': False,
            'error': 'Ошибка при удалении'
        }), 500


# ==================== ЛОГИКА СКАНИРОВАНИЯ ====================

def run_network_scan(scan_id):
    """
    Запустить сетевое сканирование
    """
    from services.network_scanner import NetworkScanner
    from services.ai_explainer import AIExplainer
    
    scan = NetworkScan.query.get(scan_id)
    if not scan:
        return
    
    try:
        scan.status = ScanStatus.RUNNING
        scan.scan_progress = 0
        db.session.commit()
        
        scanner = NetworkScanner()
        ai = AIExplainer()
        
        # Выполняем сканирование
        result = scanner.run_full_scan(
            target=scan.target,
            scan_ports=scan.scan_ports,
            scan_services=scan.scan_services,
            custom_ports=scan.custom_ports
        )
        
        # Обновляем запись
        scan.resolved_ip = result.get('resolved_ip')
        scan.open_ports = result.get('open_ports', [])
        scan.services_detected = result.get('services', {})
        scan.vulnerabilities = result.get('vulnerabilities', [])
        scan.os_detection = result.get('os_detection')
        scan.total_ports_scanned = result.get('total_ports_scanned', 0)
        scan.scan_duration = result.get('scan_duration', 0)
        scan.scan_progress = 100
        
        # Определяем уровень угрозы
        critical_count = len([v for v in scan.vulnerabilities if v.get('severity') == 'critical'])
        high_count = len([v for v in scan.vulnerabilities if v.get('severity') == 'high'])
        
        if critical_count > 0:
            scan.threat_level = ThreatLevel.DANGER
        elif high_count > 0 or len(scan.open_ports) > 20:
            scan.threat_level = ThreatLevel.WARNING
        else:
            scan.threat_level = ThreatLevel.SAFE
        
        # AI объяснение
        try:
            ai_result = ai.explain_network_scan(
                target=scan.target,
                scan_results=result
            )
            scan.ai_explanation = ai_result.get('explanation')
            scan.ai_recommendation = ai_result.get('recommendation')
        except Exception as e:
            current_app.logger.error(f'AI explanation error: {e}')
        
        # Завершаем
        scan.status = ScanStatus.COMPLETED
        scan.scanned_at = datetime.utcnow()
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f'Network scan error: {e}')
        scan.status = ScanStatus.FAILED
        scan.scan_progress = 0
        db.session.commit()
