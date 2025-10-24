#!/bin/bash
# Release-Script für ZIP-to-GitHub-Uploader AppImage

set -e

VERSION=${1:-"1.0.0"}
echo "🚀 Erstelle Release v$VERSION für ZIP-to-GitHub-Uploader"
echo "========================================================"

# Prüfe ob alle nötigen Dateien vorhanden sind
REQUIRED_FILES=(
    "streamlit_app_fixed.py"
    "uploader_utils.py"
    "requirements.txt"
    "build_appimage.sh"
    "README_AppImage.md"
)

echo "📋 Prüfe erforderliche Dateien..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Fehlende Datei: $file"
        exit 1
    else
        echo "   ✅ $file"
    fi
done
echo ""

# Bereinige vorherige Builds
echo "🧹 Bereinige vorherige Builds..."
rm -rf AppDir
rm -f ZIP-to-GitHub-Uploader-*.AppImage
rm -f appimagetool-*.AppImage
echo ""

# Erstelle AppImage
echo "🔨 Erstelle AppImage..."
./build_appimage.sh

if [ ! -f "ZIP-to-GitHub-Uploader-x86_64.AppImage" ]; then
    echo "❌ AppImage-Erstellung fehlgeschlagen"
    exit 1
fi

# Benenne AppImage mit Version um
RELEASE_NAME="ZIP-to-GitHub-Uploader-v$VERSION-x86_64.AppImage"
mv "ZIP-to-GitHub-Uploader-x86_64.AppImage" "$RELEASE_NAME"

echo ""
echo "✅ Release erfolgreich erstellt!"
echo ""
echo "📦 Release-Informationen:"
echo "   Version: v$VERSION"
echo "   Datei: $RELEASE_NAME"
echo "   Größe: $(du -h "$RELEASE_NAME" | cut -f1)"
echo "   Erstellt: $(date)"
echo ""

# Erstelle Checksumme
echo "🔐 Erstelle Checksumme..."
sha256sum "$RELEASE_NAME" > "$RELEASE_NAME.sha256"
echo "   SHA256: $(cat "$RELEASE_NAME.sha256")"
echo ""

# Teste AppImage
echo "🧪 Teste AppImage..."
./test_appimage.sh > test_results.log 2>&1

if grep -q "AppImage ist bereit zur Verwendung" test_results.log; then
    echo "   ✅ Tests erfolgreich"
else
    echo "   ⚠️  Tests mit Warnungen (siehe test_results.log)"
fi
echo ""

# Erstelle Release-Notizen
cat > "RELEASE_NOTES_v$VERSION.md" << EOF
# ZIP-to-GitHub-Uploader v$VERSION

## 🎉 Neue AppImage-Version

Diese portable Linux-Anwendung ermöglicht es, ZIP-Dateien direkt zu GitHub-Repositories hochzuladen.

### 📦 Download

- **AppImage**: [\`$RELEASE_NAME\`]($RELEASE_NAME)
- **Checksumme**: [\`$RELEASE_NAME.sha256\`]($RELEASE_NAME.sha256)

### 🚀 Verwendung

\`\`\`bash
# AppImage herunterladen und ausführbar machen
chmod +x $RELEASE_NAME

# Starten
./$RELEASE_NAME
\`\`\`

### ✨ Features

- 📦 ZIP-Dateien zu GitHub-Repositories hochladen
- 🔒 Unterstützung für private Repositories
- 📊 Dashboard mit Repository-Übersicht
- 🧠 Optional: KI-gestützte Projektanalyse
- 🖥️ Web-basierte Benutzeroberfläche (Streamlit)
- 🐧 Portable AppImage für alle Linux-Distributionen

### 📋 Systemanforderungen

- Linux x86_64
- Python 3.8+
- pip3
- Internetverbindung

### 🔧 Technische Details

- **Größe**: $(du -h "$RELEASE_NAME" | cut -f1)
- **Format**: AppImage
- **Architektur**: x86_64
- **Erstellt**: $(date)

### 📚 Dokumentation

Siehe [README_AppImage.md](README_AppImage.md) für detaillierte Anweisungen.

### 🐛 Bug Reports

Bei Problemen bitte ein Issue erstellen mit:
- Linux-Distribution und -Version
- Python-Version (\`python3 --version\`)
- Fehlermeldung oder Verhalten
EOF

echo "📝 Release-Notizen erstellt: RELEASE_NOTES_v$VERSION.md"
echo ""

# Erstelle Release-Archiv (optional)
echo "📁 Erstelle Release-Archiv..."
tar -czf "ZIP-to-GitHub-Uploader-v$VERSION-release.tar.gz" \
    "$RELEASE_NAME" \
    "$RELEASE_NAME.sha256" \
    "RELEASE_NOTES_v$VERSION.md" \
    "README_AppImage.md"

echo "   ✅ Archiv: ZIP-to-GitHub-Uploader-v$VERSION-release.tar.gz"
echo ""

echo "🎯 Release v$VERSION ist bereit!"
echo ""
echo "📋 Nächste Schritte:"
echo "   1. Teste die AppImage: ./$RELEASE_NAME"
echo "   2. Upload zu GitHub Releases"
echo "   3. Teile die Release-Notizen"
echo ""
echo "🔗 GitHub Release Command:"
echo "   gh release create v$VERSION \\"
echo "     $RELEASE_NAME \\"
echo "     $RELEASE_NAME.sha256 \\"
echo "     RELEASE_NOTES_v$VERSION.md \\"
echo "     --title \"ZIP-to-GitHub-Uploader v$VERSION\" \\"
echo "     --notes-file RELEASE_NOTES_v$VERSION.md"
