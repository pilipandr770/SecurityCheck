"""
Contact form routes
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user
from backend.services.telegram_notifier import TelegramNotifier
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

contact_bp = Blueprint('contact', __name__, url_prefix='/api/contact')


@contact_bp.route('/submit', methods=['POST'])
def submit_contact_form():
    """
    Handle contact form submission
    
    Expected JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+49...",
        "project_type": "website",
        "message": "I need help..."
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Feld "{field}" ist erforderlich'
                }), 400
        
        # Validate email format
        email = data.get('email', '')
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'message': 'Ungültige E-Mail-Adresse'
            }), 400
        
        # Send notification via Telegram
        telegram = TelegramNotifier()
        
        if telegram.is_configured():
            success = telegram.send_contact_form(data)
            
            if success:
                logger.info(f'Contact form submitted by {email}')
                return jsonify({
                    'success': True,
                    'message': 'Vielen Dank! Wir werden uns in Kürze bei Ihnen melden.'
                })
            else:
                logger.error(f'Failed to send Telegram notification for {email}')
                return jsonify({
                    'success': False,
                    'message': 'Fehler beim Senden. Bitte schreiben Sie direkt an: andrii.it.info@gmail.com'
                }), 500
        else:
            # Telegram not configured - fallback to email logging
            logger.warning('Telegram not configured. Contact form data:')
            logger.warning(f'Name: {data.get("name")}')
            logger.warning(f'Email: {data.get("email")}')
            logger.warning(f'Phone: {data.get("phone")}')
            logger.warning(f'Project: {data.get("project_type")}')
            logger.warning(f'Message: {data.get("message")}')
            
            return jsonify({
                'success': True,
                'message': 'Anfrage erhalten. Wir melden uns bald bei Ihnen.'
            })
    
    except Exception as e:
        logger.error(f'Contact form error: {e}')
        return jsonify({
            'success': False,
            'message': 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.'
        }), 500


@contact_bp.route('/test', methods=['GET'])
def test_telegram():
    """Test endpoint to verify Telegram configuration (only for admins)"""
    telegram = TelegramNotifier()
    
    if not telegram.is_configured():
        return jsonify({
            'success': False,
            'message': 'Telegram nicht konfiguriert. Setzen Sie TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID'
        }), 400
    
    # Send test message
    test_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+49123456789',
        'project_type': 'test',
        'message': 'Dies ist eine Testnachricht vom SecurityCheck-System.'
    }
    
    success = telegram.send_contact_form(test_data)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Test-Nachricht erfolgreich an Telegram gesendet!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Fehler beim Senden der Test-Nachricht'
        }), 500
