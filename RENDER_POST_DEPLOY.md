# Post-Deployment Setup für Render.com

## ✅ Was gerade passiert ist

Die Build-Fehler wurden behoben:
- ✅ Python auf 3.11.9 aktualisiert (stabil)
- ✅ lxml auf 5.3.0 aktualisiert (kompatibel)
- ✅ Build-Script vereinfacht
- ✅ Änderungen auf GitHub gepusht

## 🔄 Nächste Schritte

### 1. Render automatisch neu deployen lassen (2-3 Minuten)

Render sollte automatisch den neuen Commit erkennen und neu bauen. Wenn nicht:
- Gehe zu Render Dashboard → Dein Web Service
- Klicke "Manual Deploy" → "Deploy latest commit"

### 2. Nach erfolgreichem Build: Datenbank initialisieren

Sobald der Build erfolgreich ist, **musst du die Datenbank-Tabellen erstellen**:

```bash
# In Render Dashboard → Web Service → Shell (oben rechts)
cd backend
python -c "from app import app, db; with app.app_context(): db.create_all()"
```

### 3. Admin-Account erstellen

```bash
# In Render Shell
cd backend
python create_admin.py admin@securitycheck.de SecurePassword123!
```

### 4. Environment Variables überprüfen

Stelle sicher, dass alle diese Variablen in Render gesetzt sind:

**PFLICHT:**
```
SECRET_KEY=<generiere einen zufälligen String>
FLASK_ENV=production
DEBUG=False
DATABASE_URL=<automatisch von Render gesetzt>

# Stripe (von Dashboard holen)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_MONTHLY_PRICE_ID=price_...
STRIPE_STARTER_YEARLY_PRICE_ID=price_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...

# Security APIs
VIRUSTOTAL_API_KEY=...
GOOGLE_SAFE_BROWSING_KEY=...
```

**OPTIONAL (für AI-Features):**
```
OPENAI_API_KEY=sk-proj-...
```

### 5. Stripe Webhook URL aktualisieren

Nach dem Deployment:
1. Gehe zu Stripe Dashboard → Developers → Webhooks
2. Bearbeite deinen Webhook
3. Setze URL auf: `https://<deine-app>.onrender.com/webhook/stripe`
4. Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`

### 6. Testen

1. **Registrierung testen:** `https://<deine-app>.onrender.com/register`
2. **Login testen:** Login mit neuem Account
3. **Preise ansehen:** `/pricing` - sollten Stripe-Buttons zeigen
4. **Free Scan testen:** Versuche einen Website-Scan (10 pro Tag limit)

## 🐛 Falls Fehler auftreten

### Error: "No module named 'flask'"
→ Warte bis der Build komplett fertig ist (5-10 Minuten)

### Error: "relation 'user' does not exist"
→ Du hast vergessen die Datenbank zu initialisieren (Schritt 2 oben)

### 500 Error beim Öffnen der Seite
→ Prüfe Render Logs: Dashboard → Logs → letzte Fehler ansehen

### Stripe funktioniert nicht
→ Prüfe dass alle STRIPE_* Environment Variables gesetzt sind

## 📊 Erwartete Kosten

- **Web Service (Starter):** $7/Monat
- **PostgreSQL (Starter):** $7/Monat
- **Total:** $14/Monat

Für mehr Traffic:
- **Web Service (Standard):** $25/Monat (empfohlen für Production)
- **PostgreSQL (Standard):** $20/Monat

## 📞 Support

Bei Problemen:
- **Email:** andrii.it.info@gmail.com
- **Tel:** +49 160 95030120
- **GitHub Issues:** https://github.com/pilipandr770/SecurityCheck/issues

---

## ⚡ Quick Command Reference

```bash
# Database initialisieren
cd backend && python -c "from app import app, db; with app.app_context(): db.create_all()"

# Admin erstellen
cd backend && python create_admin.py admin@test.de Password123!

# Logs ansehen (in Render Dashboard)
# Dashboard → Dein Service → Logs

# Shell öffnen (in Render Dashboard)  
# Dashboard → Dein Service → Shell (oben rechts)

# Neu deployen
# Dashboard → Manual Deploy → Deploy latest commit
```

## ✅ Checklist

Nach dem Deployment abhaken:

- [ ] Build erfolgreich (grüner Status in Render)
- [ ] Datenbank initialisiert (`db.create_all()` ausgeführt)
- [ ] Admin-Account erstellt
- [ ] Alle Environment Variables gesetzt
- [ ] Stripe Webhook URL aktualisiert
- [ ] Registrierung funktioniert
- [ ] Login funktioniert
- [ ] Pricing-Seite zeigt Stripe-Buttons
- [ ] Free Scan funktioniert
- [ ] Logs zeigen keine kritischen Fehler

**Geschätzte Zeit:** 15-20 Minuten

Good luck! 🚀
