# Security Policy

## Sicherheitsmerkale

Dieses Projekt implementiert mehrere Sicherheitsebenen:

### 1. Dateivalidierung

- **Whitelist-Ansatz**: Nur genehmigte Dateitypen werden akzeptiert
- **MIME-Type-Überprüfung**: Validierung über `python-magic`
- **Größen-Limits**: Pro Upload-Typ konfigurierbare Limits
- **Archiv-Inspection**: Entpackte Dateien werden überprüft

### 2. Rate-Limiting

- **Pro Stunde**: Max. 50 Uploads pro IP/User
- **Pro Tag**: Max. 200 Uploads pro IP/User
- **Konfigurierbar**: Anpassbar je nach Deployment

### 3. GitHub-Sicherheit

- **Token-basierte Authentifizierung**: GitHub Personal Access Tokens
- **Minimal-Berechtigungen**: Nur `repo`-Scope erforderlich
- **Environment Variables**: Secrets in `.env`, nicht im Code

### 4. Input-Sanitization

- **Dateinamen**: Gefährliche Zeichen werden entfernt
- **Repository-Namen**: Validierung gegen GitHub-Konventionen
- **JSON-Input**: Strikte Validierung aller Eingaben

## Schwachstellen melden

Falls Sie eine Sicherheitslücke entdecken, **bitte nicht** öffentlich machen:

1. **Senden Sie eine E-Mail** an: <security@example.com> (ersetzen Sie mit echtem Kontakt)
2. **Beschreiben Sie** die Schwachstelle detailliert
3. **Warten Sie** auf eine Antwort (idealerweise in 48 Stunden)
4. **Aktualisieren Sie** nach dem Fix auf die neueste Version

## Bekannte Limitations

- **Große Archive**: Dateien > 1 GB benötigen erhöhte Timeouts
- **Rate-Limiting**: Kann bei Massenuploads problematisch sein
- **GitHub-API**: Unterliegt eigenen Rate-Limits von GitHub

## Security Best Practices

### Für Benutzer

1. ✅ Verwenden Sie einen separaten GitHub-Token (nicht den persönlichen Account-Token)
2. ✅ Aktivieren Sie 2FA auf Ihrem GitHub-Account
3. ✅ Speichern Sie Tokens nicht in Code oder Versionskontrolle
4. ✅ Überprüfen Sie regelmäßig die Berechtigungen Ihrer Tokens
5. ✅ Widerrufen Sie Tokens, wenn diese nicht mehr benötigt werden

### Für Contributor

1. ✅ Implementieren Sie Eingabe-Validierung für neue Features
2. ✅ Verwenden Sie Whitelists statt Blacklists
3. ✅ Scannen Sie auf bekannte CVEs (`pip-audit`)
4. ✅ Vermeiden Sie hardcodierte Secrets
5. ✅ Führen Sie Security-Tests lokal durch

## Compliance

- 🔒 Einhaltung von OWASP Top 10 Prinzipien
- 🛡️ Regelmäßige Dependency-Updates
- 📋 Audit-Logging für wichtige Operationen
