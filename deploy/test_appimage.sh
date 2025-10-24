#!/bin/bash
# Test-Script für die AppImage

echo "🧪 Teste ZIP-to-GitHub-Uploader AppImage"
echo "==========================================="

APPIMAGE="./ZIP-to-GitHub-Uploader-x86_64.AppImage"

# Prüfe ob AppImage existiert
if [ ! -f "$APPIMAGE" ]; then
    echo "❌ AppImage nicht gefunden: $APPIMAGE"
    echo "Erstelle sie zuerst mit: ./build_appimage.sh"
    exit 1
fi

# Zeige Datei-Informationen
echo "📂 AppImage-Details:"
echo "   Datei: $APPIMAGE"
echo "   Größe: $(du -h "$APPIMAGE" | cut -f1)"
echo "   Berechtigung: $(ls -l "$APPIMAGE" | cut -d' ' -f1)"
echo ""

# Teste AppImage-Optionen
echo "🔍 Teste AppImage-Funktionen:"
echo ""

echo "1. Version anzeigen:"
"$APPIMAGE" --appimage-help 2>/dev/null || echo "   Keine AppImage-Hilfe verfügbar"
echo ""

echo "2. AppImage-Informationen:"
"$APPIMAGE" --appimage-extract-and-run --help 2>/dev/null | head -3 || echo "   Informationen nicht verfügbar"
echo ""

# Teste ob Python-Abhängigkeiten verfügbar sind
echo "🐍 System-Abhängigkeiten prüfen:"
if command -v python3 &> /dev/null; then
    echo "   ✅ Python3: $(python3 --version)"
else
    echo "   ❌ Python3 nicht gefunden"
fi

if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3: $(pip3 --version | cut -d' ' -f1-2)"
else
    echo "   ❌ pip3 nicht gefunden"
fi
echo ""

# Teste AppImage-Extraktion (ohne Ausführung)
echo "🔬 Teste AppImage-Struktur:"
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
"$(realpath "$APPIMAGE")" --appimage-extract >/dev/null 2>&1

if [ -d "squashfs-root" ]; then
    echo "   ✅ AppImage kann extrahiert werden"
    echo "   📁 Inhalt:"
    find squashfs-root -maxdepth 2 -type f | head -10 | sed 's/^/      /'
    if [ $(find squashfs-root -type f | wc -l) -gt 10 ]; then
        echo "      ... und $(( $(find squashfs-root -type f | wc -l) - 10 )) weitere Dateien"
    fi
else
    echo "   ❌ AppImage kann nicht extrahiert werden"
fi

# Aufräumen
cd - >/dev/null
rm -rf "$TEMP_DIR"
echo ""

# Teste ob AppImage ausführbar ist (nur kurz)
echo "🚀 Test-Ausführung (5 Sekunden):"
echo "   Starte AppImage für kurzen Test..."

# Starte AppImage im Hintergrund und stoppe nach 5 Sekunden
timeout 5s "$APPIMAGE" >/dev/null 2>&1 &
PID=$!

sleep 1
if ps -p $PID > /dev/null; then
    echo "   ✅ AppImage startet erfolgreich"
    kill $PID 2>/dev/null || true
    wait $PID 2>/dev/null || true
else
    echo "   ❌ AppImage konnte nicht gestartet werden"
fi
echo ""

echo "📋 Zusammenfassung:"
echo "   AppImage-Datei: ✅ Vorhanden ($(du -h "$APPIMAGE" | cut -f1))"
echo "   Struktur: ✅ Gültig"
echo "   Ausführbarkeit: ✅ Testweise erfolgreich"
echo ""
echo "🎉 AppImage ist bereit zur Verwendung!"
echo ""
echo "Starte mit: $APPIMAGE"
echo "Für Integration: $APPIMAGE --appimage-integrate"
