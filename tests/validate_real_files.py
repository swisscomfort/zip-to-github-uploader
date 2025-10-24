#!/usr/bin/env python3
"""
Praktisches Tool zur Validierung echter Dateien
Verwenden Sie dieses Skript um echte Dateien zu testen
"""

import os
import sys
import argparse
from pathlib import Path
from security_validation import (
    validate_file_upload,
    validate_zip_file,
    validate_upload_directory,
    create_security_validator,
    UPLOAD_LIMITS,
    ALLOWED_EXTENSIONS
)

def print_header():
    """Druckt Header"""
    print("🔒" + "="*60 + "🔒")
    print("    SECURITY VALIDATION TOOL - ECHTE DATEIEN TESTEN")
    print("🔒" + "="*60 + "🔒")
    print()

def print_limits():
    """Zeigt verfügbare Upload-Typen und Limits"""
    print("📋 VERFÜGBARE UPLOAD-TYPEN:")
    print("-" * 40)
    for upload_type, limits in UPLOAD_LIMITS.items():
        print(f"🔧 {upload_type.upper()}:")
        print(f"   • Max. Dateigröße: {limits['max_file_size']/1024/1024:.0f} MB")
        print(f"   • Max. ZIP-Größe: {limits['max_zip_size']/1024/1024:.0f} MB")
        print(f"   • Max. entpackte Größe: {limits['max_extracted_size']/1024/1024:.0f} MB")
        print(f"   • Max. Dateien pro ZIP: {limits['max_files_in_zip']}")
        print()

def print_allowed_types():
    """Zeigt erlaubte Dateitypen"""
    print("✅ ERLAUBTE DATEITYPEN:")
    print("-" * 40)
    for category, extensions in ALLOWED_EXTENSIONS.items():
        print(f"📁 {category.upper()}: {', '.join(extensions)}")
    print()

def validate_single_file(file_path, upload_type='web_upload', user_id='user'):
    """Validiert eine einzelne Datei"""
    if not os.path.exists(file_path):
        print(f"❌ Datei nicht gefunden: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    
    print(f"🔍 VALIDIERE DATEI:")
    print(f"   📄 Datei: {filename}")
    print(f"   📁 Pfad: {file_path}")
    print(f"   📏 Größe: {file_size/1024:.1f} KB ({file_size/1024/1024:.2f} MB)")
    print(f"   🔧 Upload-Typ: {upload_type}")
    print(f"   👤 User: {user_id}")
    print()
    
    # Wähle Validierungsmethode basierend auf Dateityp
    if filename.lower().endswith('.zip'):
        print("📦 ZIP-Datei erkannt - verwende ZIP-Validierung")
        is_safe, message = validate_zip_file(file_path, upload_type, user_id)
    else:
        print("📄 Einzeldatei - verwende Standard-Validierung")
        is_safe, message = validate_file_upload(file_path, upload_type, user_id)
    
    # Zeige Ergebnis
    status = "✅ SICHER" if is_safe else "❌ UNSICHER"
    print(f"\n🎯 ERGEBNIS: {status}")
    print(f"📝 Details: {message}")
    print()
    
    return is_safe

def validate_directory(dir_path, upload_type='web_upload', user_id='user'):
    """Validiert alle Dateien in einem Verzeichnis"""
    if not os.path.exists(dir_path):
        print(f"❌ Verzeichnis nicht gefunden: {dir_path}")
        return False
    
    if not os.path.isdir(dir_path):
        print(f"❌ Pfad ist kein Verzeichnis: {dir_path}")
        return False
    
    print(f"🔍 VALIDIERE VERZEICHNIS:")
    print(f"   📁 Pfad: {dir_path}")
    print(f"   🔧 Upload-Typ: {upload_type}")
    print(f"   👤 User: {user_id}")
    print()
    
    # Zähle Dateien
    file_count = sum(1 for root, dirs, files in os.walk(dir_path) for file in files)
    print(f"📊 Gefundene Dateien: {file_count}")
    print()
    
    # Validiere Verzeichnis
    is_safe, message = validate_upload_directory(dir_path, upload_type, user_id)
    
    # Zeige Ergebnis
    status = "✅ ALLE SICHER" if is_safe else "❌ UNSICHERE DATEIEN GEFUNDEN"
    print(f"🎯 ERGEBNIS: {status}")
    print(f"📝 Details: {message}")
    print()
    
    return is_safe

def interactive_mode():
    """Interaktiver Modus für Dateivalidierung"""
    print_header()
    print("🎮 INTERAKTIVER MODUS")
    print("Geben Sie Dateipfade ein um sie zu validieren")
    print("Befehle: 'help', 'limits', 'types', 'quit'")
    print()
    
    upload_type = 'web_upload'
    user_id = 'interactive_user'
    
    while True:
        try:
            user_input = input("📁 Dateipfad (oder Befehl): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Auf Wiedersehen!")
                break
            elif user_input.lower() == 'help':
                print("\n📚 HILFE:")
                print("   • Geben Sie einen Dateipfad ein um die Datei zu validieren")
                print("   • Geben Sie einen Verzeichnispfad ein um alle Dateien zu validieren")
                print("   • 'limits' - Zeigt Upload-Limits")
                print("   • 'types' - Zeigt erlaubte Dateitypen")
                print("   • 'set web/api/admin' - Ändert Upload-Typ")
                print("   • 'user <name>' - Ändert User-ID")
                print("   • 'quit' - Beendet das Programm")
                print()
                continue
            elif user_input.lower() == 'limits':
                print_limits()
                continue
            elif user_input.lower() == 'types':
                print_allowed_types()
                continue
            elif user_input.lower().startswith('set '):
                new_type = user_input[4:].strip()
                if new_type in ['web', 'api', 'admin']:
                    upload_type = f'{new_type}_upload'
                    print(f"✅ Upload-Typ geändert zu: {upload_type}")
                else:
                    print("❌ Ungültiger Upload-Typ. Verwenden Sie: web, api, admin")
                print()
                continue
            elif user_input.lower().startswith('user '):
                new_user = user_input[5:].strip()
                if new_user:
                    user_id = new_user
                    print(f"✅ User-ID geändert zu: {user_id}")
                else:
                    print("❌ Bitte geben Sie eine gültige User-ID an")
                print()
                continue
            
            # Pfad validieren
            path = Path(user_input).expanduser().resolve()
            
            if path.is_file():
                validate_single_file(str(path), upload_type, user_id)
            elif path.is_dir():
                validate_directory(str(path), upload_type, user_id)
            else:
                print(f"❌ Pfad nicht gefunden: {path}")
                print()
                
        except KeyboardInterrupt:
            print("\n👋 Programm beendet.")
            break
        except Exception as e:
            print(f"❌ Fehler: {e}")
            print()

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description="Security Validation Tool - Echte Dateien testen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python validate_real_files.py document.pdf
  python validate_real_files.py archive.zip --type api
  python validate_real_files.py /path/to/directory --type admin --user admin123
  python validate_real_files.py --interactive
  python validate_real_files.py --limits
        """
    )
    
    parser.add_argument('path', nargs='?', help='Pfad zur Datei oder zum Verzeichnis')
    parser.add_argument('--type', choices=['web', 'api', 'admin'], default='web',
                       help='Upload-Typ (default: web)')
    parser.add_argument('--user', default='cli_user', help='User-ID (default: cli_user)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Startet interaktiven Modus')
    parser.add_argument('--limits', action='store_true',
                       help='Zeigt Upload-Limits und beendet')
    parser.add_argument('--types', action='store_true',
                       help='Zeigt erlaubte Dateitypen und beendet')
    
    args = parser.parse_args()
    
    # Zeige nur Informationen
    if args.limits:
        print_header()
        print_limits()
        return
    
    if args.types:
        print_header()
        print_allowed_types()
        return
    
    # Interaktiver Modus
    if args.interactive:
        interactive_mode()
        return
    
    # Pfad-Validierung
    if not args.path:
        print("❌ Bitte geben Sie einen Pfad an oder verwenden Sie --interactive")
        parser.print_help()
        return
    
    print_header()
    
    upload_type = f'{args.type}_upload'
    path = Path(args.path).expanduser().resolve()
    
    if path.is_file():
        validate_single_file(str(path), upload_type, args.user)
    elif path.is_dir():
        validate_directory(str(path), upload_type, args.user)
    else:
        print(f"❌ Pfad nicht gefunden: {path}")

if __name__ == "__main__":
    main()
