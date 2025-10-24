# ZIP-to-GitHub-Uploader AppImage

## 🚀 Was ist das?

Diese AppImage verpackt den ZIP-to-GitHub-Uploader als portable, ausführbare Datei für Linux-Systeme. Die AppImage enthält alle notwendigen Dateien und kann ohne Installation ausgeführt werden.

## 📦 AppImage erstellen

### Voraussetzungen

- Linux-System (Ubuntu, Fedora, openSUSE, etc.)
- Python 3.8+
- wget
- Internet-Verbindung

### Build-Prozess

1. **Einfacher Weg (Bash-Script):**
   ```bash
   ./build_appimage.sh
   ```

2. **Python-Script:**
   ```bash
   python3 build_appimage.py
   ```

### Was passiert beim Build?

1. **AppDir-Struktur erstellen**: Verzeichnisstruktur für die AppImage
2. **Dateien kopieren**: Alle Python-Dateien und Abhängigkeiten
3. **AppRun-Script**: Startet die Anwendung korrekt
4. **Desktop-Integration**: .desktop-Datei für Menü-Integration
5. **Icon erstellen**: SVG-Icon für die Anwendung
6. **AppImage packen**: Mit appimagetool zur finalen .AppImage

## 🎯 Verwendung der AppImage

### Starten
```bash
# AppImage ausführbar machen (falls nötig)
chmod +x ZIP-to-GitHub-Uploader-x86_64.AppImage

# Starten
./ZIP-to-GitHub-Uploader-x86_64.AppImage
```

### Was passiert beim Start?

1. **Abhängigkeiten prüfen**: Python3 und pip3 müssen installiert sein
2. **Pakete installieren**: Automatische Installation von Streamlit & Co.
3. **Server starten**: Streamlit-Server auf http://localhost:8504
4. **Browser öffnen**: Automatisches Öffnen der Web-Oberfläche

### Desktop-Integration

Die AppImage kann sich selbst ins System integrieren:

```bash
# Integration ins Anwendungsmenü
./ZIP-to-GitHub-Uploader-x86_64.AppImage --appimage-integrate

# Entfernen aus dem Menü
./ZIP-to-GitHub-Uploader-x86_64.AppImage --appimage-remove
```

## 🔧 Technische Details

### Verzeichnisstruktur der AppImage

```
AppDir/
├── AppRun                    # Haupt-Startup-Script
├── zip-github-uploader.desktop # Desktop-Datei
├── zip-github-uploader.svg   # Icon
└── usr/
    ├── bin/
    │   ├── streamlit_app_fixed.py
    │   ├── uploader_utils.py
    │   ├── requirements.txt
    │   └── shared/           # Shared-Module
    └── share/
        ├── applications/
        └── icons/
```

### Abhängigkeiten

Die AppImage benötigt folgende System-Abhängigkeiten:

- **Python 3.8+**: Grundlegende Laufzeitumgebung
- **pip3**: Für automatische Paket-Installation
- **Netzwerk**: Für GitHub-API und Paket-Downloads

### Automatisch installierte Python-Pakete

- `streamlit>=1.28.0`: Web-Framework
- `requests>=2.31.0`: HTTP-Client für GitHub-API
- `python-dotenv>=1.0.0`: Umgebungsvariablen
- `pandas>=2.0.0`: Datenverarbeitung
- `altair>=5.0.0`: Diagramme

## 🐛 Troubleshooting

### Häufige Probleme

1. **"Python3 ist nicht installiert"**
   ```bash
   # Ubuntu/Debian
   sudo apt install python3 python3-pip
   
   # Fedora
   sudo dnf install python3 python3-pip
   
   # openSUSE
   sudo zypper install python3 python3-pip
   ```

2. **"Permission denied"**
   ```bash
   chmod +x ZIP-to-GitHub-Uploader-x86_64.AppImage
   ```

3. **Port bereits belegt**
   - Die App verwendet Port 8504
   - Falls belegt, wird automatisch ein anderer Port gewählt

4. **Pakete können nicht installiert werden**
   ```bash
   # Aktualisiere pip
   python3 -m pip install --upgrade pip
   
   # Installiere manuell
   pip3 install --user streamlit requests python-dotenv pandas altair
   ```

### Debug-Modus

Für detaillierte Fehlersuche:

```bash
# Starte mit Debug-Output
APPIMAGE_DEBUG=1 ./ZIP-to-GitHub-Uploader-x86_64.AppImage
```

## 📊 Vorteile der AppImage

✅ **Portabel**: Läuft auf jedem Linux-System  
✅ **Keine Installation**: Direkt ausführbar  
✅ **Selbstständig**: Enthält alle Abhängigkeiten  
✅ **Sicher**: Läuft in isolierter Umgebung  
✅ **Desktop-Integration**: Kann ins Menü integriert werden  
✅ **Automatische Updates**: Kann Update-Mechanismus nutzen  

## 🚀 Verteilung

Die erstellte AppImage kann einfach verteilt werden:

- **GitHub Releases**: Als Download-Asset
- **Direkter Download**: Über HTTP-Server
- **USB-Stick**: Portable Nutzung
- **Package-Repositories**: Über AppImageHub

### Beispiel für GitHub Release

```bash
# Tag erstellen
git tag v1.0.0

# Release mit AppImage
gh release create v1.0.0 \
  ZIP-to-GitHub-Uploader-x86_64.AppImage \
  --title "ZIP to GitHub Uploader v1.0.0" \
  --notes "Erste AppImage-Version"
```

## 📝 Anpassungen

### Icon ändern

Bearbeite die SVG-Datei in `build_appimage.sh`:

```bash
# Eigenes Icon verwenden
cp my-custom-icon.svg "$APP_DIR/zip-github-uploader.svg"
```

### Zusätzliche Dateien

Füge weitere Dateien in den Build-Prozess ein:

```bash
# In build_appimage.sh
cp config.json "$APP_DIR/usr/bin/"
cp -r templates "$APP_DIR/usr/bin/"
```

### Port ändern

Ändere den Standard-Port in der AppRun-Datei:

```bash
# Statt Port 8504
--server.port=8505
```
