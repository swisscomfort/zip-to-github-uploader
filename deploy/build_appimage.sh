#!/bin/bash
# Vereinfachtes Build-Script für AppImage

set -e

echo "🚀 Erstelle AppImage für ZIP-to-GitHub-Uploader..."

# Prüfe Abhängigkeiten
if ! command -v wget &> /dev/null; then
    echo "❌ wget ist nicht installiert"
    echo "Installiere mit: sudo apt install wget"
    exit 1
fi

# Arbeitsverzeichnis
WORK_DIR=$(pwd)
APP_DIR="$WORK_DIR/AppDir"

# Bereinige vorherige Builds
rm -rf "$APP_DIR"
rm -f ZIP-to-GitHub-Uploader-*.AppImage

# Erstelle AppDir-Struktur
echo "📁 Erstelle AppDir-Struktur..."
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

# Kopiere Anwendungsdateien
echo "📦 Kopiere Anwendungsdateien..."
cp streamlit_app_fixed.py "$APP_DIR/usr/bin/"
cp uploader_utils.py "$APP_DIR/usr/bin/"
cp requirements.txt "$APP_DIR/usr/bin/"

# Kopiere shared-Verzeichnis falls vorhanden
if [ -d "shared" ]; then
    cp -r shared "$APP_DIR/usr/bin/"
fi

# Erstelle AppRun-Script
echo "⚙️ Erstelle AppRun-Script..."
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/bin:${PYTHONPATH}"

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    zenity --error --text="Python3 ist nicht installiert.\nBitte installiere Python3." 2>/dev/null || \
    echo "Python3 ist nicht installiert. Bitte installiere Python3."
    exit 1
fi

# Installiere benötigte Pakete
echo "Installiere Abhängigkeiten..."
pip3 install --user streamlit requests python-dotenv pandas altair > /tmp/pip_install.log 2>&1

# Starte die Anwendung
cd "${HERE}/usr/bin"

# Öffne Browser automatisch
sleep 2 && xdg-open "http://localhost:8504" &

# Starte Streamlit
python3 -m streamlit run streamlit_app_fixed.py \
    --server.headless=true \
    --server.port=8504 \
    --browser.gatherUsageStats=false \
    --server.address=0.0.0.0
EOF

chmod +x "$APP_DIR/AppRun"

# Erstelle Desktop-Datei
echo "🖥️ Erstelle Desktop-Datei..."
cat > "$APP_DIR/zip-github-uploader.desktop" << EOF
[Desktop Entry]
Name=ZIP to GitHub Uploader
Comment=Upload ZIP files to GitHub repositories
Exec=AppRun
Icon=zip-github-uploader
Type=Application
Categories=Development;Utility;Network;
Terminal=false
StartupNotify=true
EOF

cp "$APP_DIR/zip-github-uploader.desktop" "$APP_DIR/usr/share/applications/"

# Erstelle einfaches Icon
echo "🎨 Erstelle Icon..."
cat > "$APP_DIR/zip-github-uploader.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#24292e" rx="20"/>
  <rect x="40" y="60" width="80" height="60" fill="#0366d6" rx="8"/>
  <text x="80" y="100" text-anchor="middle" fill="white" font-family="Arial Black" font-size="16">ZIP</text>
  <path d="M130 85 L150 90 L130 95" stroke="white" stroke-width="3" fill="white"/>
  <circle cx="180" cy="90" r="25" fill="#ffffff"/>
  <path d="M165 90 L195 90 M180 75 L180 105" stroke="#24292e" stroke-width="3"/>
  <text x="128" y="140" text-anchor="middle" fill="white" font-family="Arial" font-size="14">GitHub</text>
  <text x="128" y="160" text-anchor="middle" fill="white" font-family="Arial" font-size="14">Uploader</text>
</svg>
EOF

cp "$APP_DIR/zip-github-uploader.svg" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/"

# Lade appimagetool herunter
APPIMAGETOOL="appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "📥 Lade appimagetool herunter..."
    wget -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# Erstelle AppImage
echo "🔨 Erstelle AppImage..."
OUTPUT_NAME="ZIP-to-GitHub-Uploader-x86_64.AppImage"

ARCH=x86_64 ./"$APPIMAGETOOL" "$APP_DIR" "$OUTPUT_NAME"

if [ -f "$OUTPUT_NAME" ]; then
    chmod +x "$OUTPUT_NAME"
    SIZE=$(du -h "$OUTPUT_NAME" | cut -f1)
    echo ""
    echo "✅ AppImage erfolgreich erstellt!"
    echo "📂 Datei: $OUTPUT_NAME"
    echo "📏 Größe: $SIZE"
    echo ""
    echo "🎉 Starte mit: ./$OUTPUT_NAME"
    echo ""
    echo "💡 Die App startet einen lokalen Server auf http://localhost:8504"
    echo "   und öffnet automatisch den Browser."
else
    echo "❌ Fehler beim Erstellen der AppImage"
    exit 1
fi
