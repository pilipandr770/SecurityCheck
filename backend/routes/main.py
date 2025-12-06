from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/impressum')
def impressum():
    """Impressum (Impressum)"""
    return render_template('impressum.html')

@main_bp.route('/datenschutz')
def datenschutz():
    """Datenschutzerklärung (Privacy Policy)"""
    return render_template('datenschutz.html')

@main_bp.route('/agb')
def agb():
    """Allgemeine Geschäftsbedingungen (Terms of Service)"""
    return render_template('agb.html')

@main_bp.route('/portfolio')
def portfolio():
    """Портфолио защищенных проектов"""
    return render_template('portfolio.html')

@main_bp.route('/contact')
def contact():
    """Контактная страница"""
    return render_template('contact.html')
