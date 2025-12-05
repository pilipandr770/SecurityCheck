"""
Скрипт для очистки зависших сканирований
"""
from app import app
from models import db, NetworkScan, ScanStatus

with app.app_context():
    # Находим все незавершенные сканирования
    pending_scans = NetworkScan.query.filter(
        NetworkScan.status.in_([ScanStatus.PENDING, ScanStatus.RUNNING])
    ).all()
    
    print(f"Найдено {len(pending_scans)} незавершенных сканирований")
    
    # Помечаем как failed
    for scan in pending_scans:
        scan.status = ScanStatus.FAILED
        scan.ai_explanation = "Сканирование было прервано"
        print(f"Scan #{scan.id} помечен как failed")
    
    db.session.commit()
    print("Готово!")
