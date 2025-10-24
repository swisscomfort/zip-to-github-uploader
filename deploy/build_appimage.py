#!/usr/bin/env python3
"""
Script zum Erstellen einer AppImage für den ZIP-to-GitHub-Uploader
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def create_appimage():
    """Erstellt eine AppImage für die Streamlit-Anwendung"""

    # Arbeitsverzeichnis
    work_dir = Path.cwd()
    app_dir = work_dir / "AppDir"

    print("🚀 Erstelle AppImage für ZIP-to-GitHub-Uploader...")

    # 1. AppDir-Struktur erstellen
    print("📁 Erstelle AppDir-Struktur...")
    if app_dir.exists():
        shutil.rmtree(app_dir)

    app_dir.mkdir()
    (app_dir / "usr" / "bin").mkdir(parents=True)
    (app_dir / "usr" / "share" / "applications").mkdir(parents=True)
    (app_dir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(
        parents=True
    )

    # 2. Python-Anwendung kopieren
    print("📦 Kopiere Anwendungsdateien...")
    app_files = ["streamlit_app_fixed.py", "uploader_utils.py", "requirements.txt"]

    for file in app_files:
        if Path(file).exists():
            shutil.copy2(file, app_dir / "usr" / "bin")

    # Shared-Verzeichnis kopieren
    if Path("shared").exists():
        shutil.copytree("shared", app_dir / "usr" / "bin" / "shared")

    # 3. AppRun-Script erstellen
    print("⚙️ Erstelle AppRun-Script...")
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/bin:${PYTHONPATH}"

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "Python3 ist nicht installiert. Bitte installiere Python3."
    exit 1
fi

# Prüfe ob pip verfügbar ist
if ! command -v pip3 &> /dev/null; then
    echo "pip3 ist nicht installiert. Bitte installiere pip3."
    exit 1
fi

# Installiere benötigte Pakete (falls nicht vorhanden)
pip3 install --user streamlit requests python-dotenv pandas altair > /dev/null 2>&1

# Starte die Anwendung
cd "${HERE}/usr/bin"
python3 -m streamlit run streamlit_app_fixed.py --server.headless=true --server.port=8504 --browser.gatherUsageStats=false
"""

    with open(app_dir / "AppRun", "w") as f:
        f.write(apprun_content)

    os.chmod(app_dir / "AppRun", 0o755)

    # 4. Desktop-Datei erstellen
    print("🖥️ Erstelle Desktop-Datei...")
    desktop_content = """[Desktop Entry]
Name=ZIP to GitHub Uploader
Comment=Upload ZIP files to GitHub repositories
Exec=AppRun
Icon=zip-github-uploader
Type=Application
Categories=Development;Utility;
Terminal=false
StartupNotify=true
"""

    with open(app_dir / "zip-github-uploader.desktop", "w") as f:
        f.write(desktop_content)

    shutil.copy2(
        app_dir / "zip-github-uploader.desktop",
        app_dir / "usr" / "share" / "applications",
    )

    # 5. Icon erstellen (einfaches SVG)
    print("🎨 Erstelle Icon...")
    icon_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#24292e"/>
  <circle cx="128" cy="80" r="30" fill="#ffffff"/>
  <rect x="78" y="120" width="100" height="80" rx="10" fill="#0366d6"/>
  <text x="128" y="150" text-anchor="middle" fill="white" font-family="Arial" font-size="12">ZIP</text>
  <text x="128" y="170" text-anchor="middle" fill="white" font-family="Arial" font-size="12">→</text>
  <text x="128" y="190" text-anchor="middle" fill="white" font-family="Arial" font-size="12">GitHub</text>
</svg>"""

    icon_path = app_dir / "zip-github-uploader.svg"
    with open(icon_path, "w") as f:
        f.write(icon_content)

    # Icon auch in den richtigen Ordner kopieren
    shutil.copy2(
        icon_path,
        app_dir
        / "usr"
        / "share"
        / "icons"
        / "hicolor"
        / "256x256"
        / "apps"
        / "zip-github-uploader.svg",
    )

    # 6. AppImage erstellen
    print("🔨 Erstelle AppImage...")

    # appimagetool herunterladen falls nicht vorhanden
    appimagetool_path = work_dir / "appimagetool-x86_64.AppImage"
    if not appimagetool_path.exists():
        print("📥 Lade appimagetool herunter...")
        try:
            subprocess.run(
                [
                    "wget",
                    "-O",
                    str(appimagetool_path),
                    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
                ],
                check=True,
            )
            os.chmod(appimagetool_path, 0o755)
        except subprocess.CalledProcessError:
            print("❌ Fehler beim Herunterladen von appimagetool")
            return False

    # AppImage erstellen
    output_name = "ZIP-to-GitHub-Uploader-x86_64.AppImage"
    try:
        subprocess.run([str(appimagetool_path), str(app_dir), output_name], check=True)

        print(f"✅ AppImage erfolgreich erstellt: {output_name}")
        print(f"📂 Größe: {os.path.getsize(output_name) / 1024 / 1024:.1f} MB")

        # Ausführbar machen
        os.chmod(output_name, 0o755)

        print("\n🎉 Fertig! Du kannst die AppImage jetzt ausführen:")
        print(f"   ./{output_name}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Erstellen der AppImage: {e}")
        return False


def install_dependencies():
    """Installiert benötigte Abhängigkeiten"""
    print("📦 Installiere Abhängigkeiten...")

    try:
        # Prüfe ob wget installiert ist
        subprocess.run(["which", "wget"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ wget ist nicht installiert. Bitte installiere es:")
        print("   sudo apt install wget  # Ubuntu/Debian")
        print("   sudo dnf install wget  # Fedora")
        return False

    return True


if __name__ == "__main__":
    print("🔧 ZIP-to-GitHub-Uploader AppImage Builder")
    print("=" * 50)

    if not install_dependencies():
        sys.exit(1)

    if create_appimage():
        print("\n✅ AppImage wurde erfolgreich erstellt!")
        print("\nNützliche Befehle:")
        print("  ./ZIP-to-GitHub-Uploader-x86_64.AppImage  # Starten")
        print("  ./ZIP-to-GitHub-Uploader-x86_64.AppImage --help  # Hilfe")
    else:
        print("\n❌ Fehler beim Erstellen der AppImage")
        sys.exit(1)
