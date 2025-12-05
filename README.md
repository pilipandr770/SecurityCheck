# SecurityCheck - Sicherheitsprüfung für Websites

🇩🇪 **Deutsche Version** | Professional Security Auditing Platform

SecurityCheck ist eine umfassende Sicherheitsprüfungsplattform für Websites, entwickelt für den deutschen Markt.

## ✨ Features

### 🔍 Website-Sicherheitsprüfung
- SSL/TLS-Zertifikatsanalyse
- Sicherheits-Header-Prüfung
- XSS & CSRF Schwachstellen-Scan
- Port-Scanning
- Vollständiger Sicherheitsbericht

### 🔗 Link-Checker
- Phishing-Erkennung
- Malware-Prüfung
- URL-Reputationsanalyse

### 📡 WiFi & Network Scanner
- Netzwerkgeräte-Erkennung
- Offene Ports-Analyse
- Sicherheitsempfehlungen

### 🌐 Domain-Intelligence
- WHOIS-Informationen
- DNS-Einträge
- Domain-Historie
- Reputationsprüfung

## 💰 Tarife

- **FREE**: €0/Monat - 10 Scans/Monat
- **STARTER**: €9.99/Monat - Unbegrenzte Scans
- **PRO**: €29.99/Monat - Alles + API + Beratung

## 🚀 Deployment auf Render.com

### Umgebungsvariablen

```bash
SECRET_KEY=your-secret-key
FLASK_ENV=production
DATABASE_URL=postgresql://...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

### Setup

1. Repository verbinden: `https://github.com/pilipandr770/SecurityCheck.git`
2. Build Command: `./build.sh`
3. Start Command: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
4. PostgreSQL-Datenbank hinzufügen
5. Umgebungsvariablen konfigurieren

## 📦 Lokale Installation

```bash
git clone https://github.com/pilipandr770/SecurityCheck.git
cd SecurityCheck
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cd backend
python run.py
```

## 📞 Kontakt

**Andrii Pylypchuk**  
📧 andrii.it.info@gmail.com  
📱 +49 160 95030120  
📍 Frankfurt am Main, Deutschland

---

© 2024 Andrii Pylypchuk. Made with ❤️ in Frankfurt.
