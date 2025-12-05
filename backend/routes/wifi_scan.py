"""
API для сканирования Wi-Fi сети
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, NetworkScan
from services.wifi_scanner import WiFiScanner
from services.ai_explainer import AIExplainer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

wifi_scan_bp = Blueprint('wifi_scan', __name__)


@wifi_scan_bp.route('/start', methods=['POST'])
@login_required
def start_wifi_scan():
    """Запускает сканирование Wi-Fi сети"""
    try:
        logger.info("Starting WiFi scan request")
        
        # Проверяем лимиты
        can_scan, message = current_user.can_use_feature('network_scans')
        logger.info(f"Can scan: {can_scan}, message: {message}")
        
        if not can_scan:
            return jsonify({
                'success': False,
                'error': message
            }), 403
        
        # Создаём запись в БД
        from models import ScanStatus
        scan = NetworkScan(
            user_id=current_user.id,
            target='local_network',
            target_type='network',
            status=ScanStatus.PENDING,
            scan_progress=0,
            scan_ports=True,
            scan_services=True
        )
        logger.info("NetworkScan object created")
        
        db.session.add(scan)
        db.session.commit()
        logger.info(f"Scan saved to DB with ID: {scan.id}")
        
        # Запускаем сканирование в фоне
        from threading import Thread
        from flask import current_app
        thread = Thread(target=run_wifi_scan, args=(scan.id, current_app._get_current_object()))
        thread.daemon = True
        thread.start()
        logger.info("Background thread started")
        
        return jsonify({
            'success': True,
            'scan_id': scan.id,
            'message': 'Сканирование Wi-Fi сети запущено'
        })
        
    except Exception as e:
        logger.error(f"Ошибка запуска сканирования: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_wifi_scan(scan_id: int, app):
    """Выполняет сканирование WiFi"""
    from models import ScanStatus, ThreatLevel
    
    with app.app_context():
        try:
            scan = NetworkScan.query.get(scan_id)
            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return
            
            # Обновляем статус
            scan.status = ScanStatus.RUNNING
            scan.scan_progress = 10
            db.session.commit()
            
            # Создаём сканер
            scanner = WiFiScanner(timeout=1.0, max_workers=50)
            
            # Функция обновления прогресса
            def update_progress(progress):
                scan.scan_progress = min(progress, 95)
                db.session.commit()
            
            # Запускаем сканирование
            results = scanner.scan_network(progress_callback=update_progress)
            
            if not results['success']:
                scan.status = ScanStatus.FAILED
                scan.ai_explanation = results.get('error', 'Ошибка сканирования')
                db.session.commit()
                return
            
            # Сохраняем результаты
            scan.resolved_ip = results['local_ip']
            scan.total_ports_scanned = results['total_devices']
            scan.scan_duration = results['scan_duration']
            
            # Форматируем устройства
            devices_list = []
            for device in results['devices']:
                devices_list.append({
                    'ip': device['ip'],
                    'mac': device['mac'],
                    'hostname': device['hostname'],
                    'device_type': device['device_type'],
                    'vendor': device['vendor'],
                    'icon': device['icon'],
                    'open_ports': device['open_ports']
                })
            
            scan.open_ports = devices_list  # Сохраняем устройства в поле open_ports (JSON)
            
            # Определяем уровень угрозы
            total_devices = len(devices_list)
            scan.services_detected = {'network': results['network'], 'total': total_devices}
            
            if total_devices <= 5:
                scan.threat_level = ThreatLevel.SAFE
            elif total_devices <= 15:
                scan.threat_level = ThreatLevel.WARNING
            else:
                scan.threat_level = ThreatLevel.DANGER
            
            # AI объяснение
            try:
                ai = AIExplainer()
                explanation_result = ai.explain_wifi_scan(results)
                scan.ai_explanation = explanation_result.get('explanation', '')
                scan.ai_recommendation = explanation_result.get('recommendation', '')
            except Exception as e:
                logger.error(f"AI explanation error: {e}")
                scan.ai_explanation = f"Найдено {total_devices} устройств в сети"
                scan.ai_recommendation = "Регулярно проверяйте подключенные устройства"
            
            # Завершаем
            scan.status = ScanStatus.COMPLETED
            scan.scan_progress = 100
            scan.scanned_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"WiFi scan {scan_id} completed: {total_devices} devices found")
            
        except Exception as e:
            logger.error(f"WiFi scan error: {e}", exc_info=True)
            scan.status = ScanStatus.FAILED
            scan.ai_explanation = f"Ошибка сканирования: {str(e)}"
            db.session.commit()


@wifi_scan_bp.route('/<int:scan_id>', methods=['GET'])
@login_required
def get_scan(scan_id):
    """Получает результаты сканирования"""
    try:
        scan = NetworkScan.query.get(scan_id)
        
        if not scan:
            return jsonify({
                'success': False,
                'error': 'Сканирование не найдено'
            }), 404
        
        if scan.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Доступ запрещён'
            }), 403
        
        return jsonify({
            'success': True,
            'scan': scan.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения сканирования: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения данных'
        }), 500


@wifi_scan_bp.route('/<int:scan_id>/status', methods=['GET'])
@login_required
def get_scan_status(scan_id):
    """Получает статус сканирования"""
    try:
        scan = NetworkScan.query.get(scan_id)
        
        if not scan or scan.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Сканирование не найдено'
            }), 404
        
        return jsonify({
            'success': True,
            'status': scan.status.value if scan.status else 'pending',
            'progress': scan.scan_progress
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения статуса'
        }), 500


@wifi_scan_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """Получает историю сканирований"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        scans = NetworkScan.query\
            .filter_by(user_id=current_user.id)\
            .order_by(NetworkScan.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'scans': [scan.to_dict() for scan in scans.items],
            'total': scans.total,
            'pages': scans.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения истории'
        }), 500


@wifi_scan_bp.route('/<int:scan_id>', methods=['DELETE'])
@login_required
def delete_scan(scan_id):
    """Удаляет сканирование"""
    try:
        scan = NetworkScan.query.get(scan_id)
        
        if not scan:
            return jsonify({
                'success': False,
                'error': 'Сканирование не найдено'
            }), 404
        
        if scan.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Доступ запрещён'
            }), 403
        
        db.session.delete(scan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Сканирование удалено'
        })
        
    except Exception as e:
        logger.error(f"Ошибка удаления сканирования: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка удаления'
        }), 500
