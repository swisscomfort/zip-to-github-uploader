#!/usr/bin/env python3
"""
Demo-Skript für das Security-Validierungstool
Zeigt praktische Anwendungsbeispiele
"""

import os
import tempfile
import zipfile
from security_validation import (
    validate_file_upload,
    validate_zip_file,
    create_security_validator,
    UPLOAD_LIMITS,
    ALLOWED_EXTENSIONS
)

def print_header(title):
    """Druckt einen formatierten Header"""
    print(f"\n{'='*60}")
    print(f"🔒 {title}")
    print('='*60)

def print_limits():
    """Zeigt die konfigurierten Limits an"""
    print_header("Konfigurierte Upload-Limits")
    
    for upload_type, limits in UPLOAD_LIMITS.items():
        print(f"\n📋 {upload_type.upper()}:")
        print(f"  • Max. Dateigröße: {limits['max_file_size']/1024/1024:.1f} MB")
        print(f"  • Max. ZIP-Größe: {limits['max_zip_size']/1024/1024:.1f} MB")
        print(f"  • Max. entpackte Größe: {limits['max_extracted_size']/1024/1024:.1f} MB")
        print(f"  • Max. Dateien pro ZIP: {limits['max_files_in_zip']}")

def print_allowed_types():
    """Zeigt die erlaubten Dateitypen an"""
    print_header("Erlaubte Dateitypen (Whitelist)")
    
    for category, extensions in ALLOWED_EXTENSIONS.items():
        print(f"\n📁 {category.upper()}:")
        print(f"  {', '.join(extensions)}")

def demo_basic_validation():
    """Demonstriert grundlegende Dateivalidierung"""
    print_header("Demo: Grundlegende Dateivalidierung")
    
    # Erstelle temporäre Test-Dateien
    test_dir = tempfile.mkdtemp(prefix="demo_")
    
    test_cases = [
        ("sicher.txt", b"Dies ist eine sichere Textdatei.", True),
        ("dokument.pdf", b"%PDF-1.4\nSicheres PDF", True),
        ("bild.jpg", b"\xff\xd8\xff\xe0JFIF\x00\x01", True),
        ("script.py", b"print('Hello World')", True),
        ("verdaechtig_backdoor.txt", b"Harmloser Inhalt", False),  # Verdächtiger Name
        ("datei.exe.txt", b"Versteckte Executable", False),  # Doppelte Erweiterung
    ]
    
    print(f"📁 Test-Verzeichnis: {test_dir}")
    
    for filename, content, expected_safe in test_cases:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        
        is_safe, message = validate_file_upload(filepath, 'web_upload', 'demo_user')
        status = "✅ SICHER" if is_safe else "❌ UNSICHER"
        expected = "✅" if expected_safe else "❌"
        
        print(f"{expected} {status} {filename}")
        print(f"    → {message}")

def demo_zip_validation():
    """Demonstriert ZIP-Validierung"""
    print_header("Demo: ZIP-Validierung")
    
    test_dir = tempfile.mkdtemp(prefix="demo_zip_")
    
    # Erstelle sichere ZIP
    safe_zip = os.path.join(test_dir, "sicher.zip")
    with zipfile.ZipFile(safe_zip, 'w') as zf:
        zf.writestr("dokument.txt", "Sicherer Inhalt")
        zf.writestr("bild.jpg", b"\xff\xd8\xff\xe0JFIF")
        zf.writestr("ordner/datei.py", "print('Hello')")
    
    # Erstelle unsichere ZIP mit Directory Traversal
    unsafe_zip = os.path.join(test_dir, "unsicher.zip")
    with zipfile.ZipFile(unsafe_zip, 'w') as zf:
        zf.writestr("normal.txt", "Normaler Inhalt")
        zf.writestr("../../../etc/passwd", "root:x:0:0")  # Directory Traversal
    
    test_zips = [
        (safe_zip, "Sichere ZIP-Datei"),
        (unsafe_zip, "Unsichere ZIP-Datei (Directory Traversal)")
    ]
    
    for zip_path, description in test_zips:
        print(f"\n📦 {description}:")
        is_safe, message = validate_zip_file(zip_path, 'web_upload', 'demo_user')
        status = "✅ SICHER" if is_safe else "❌ UNSICHER"
        print(f"   {status} {message}")

def demo_upload_types():
    """Demonstriert verschiedene Upload-Typen"""
    print_header("Demo: Verschiedene Upload-Typen")
    
    # Erstelle eine größere Test-Datei (30 MB simuliert)
    test_dir = tempfile.mkdtemp(prefix="demo_types_")
    large_file = os.path.join(test_dir, "grosse_datei.txt")
    
    # Simuliere 30 MB Datei (nur für Demo - erstelle kleinere Datei)
    with open(large_file, 'w') as f:
        f.write("Simulierte große Datei\n" * 1000)
    
    # Teste verschiedene Upload-Typen
    upload_types = ['web_upload', 'api_upload', 'admin_upload']
    
    for upload_type in upload_types:
        print(f"\n🔧 Upload-Typ: {upload_type}")
        limits = UPLOAD_LIMITS[upload_type]
        print(f"   Max. Größe: {limits['max_file_size']/1024/1024:.1f} MB")
        
        is_safe, message = validate_file_upload(large_file, upload_type, 'demo_user')
        status = "✅ ERLAUBT" if is_safe else "❌ ABGELEHNT"
        print(f"   {status} {message}")

def demo_validator_factory():
    """Demonstriert die Validator-Factory"""
    print_header("Demo: Validator Factory Pattern")
    
    # Erstelle verschiedene Validatoren
    web_validator = create_security_validator('web_upload')
    api_validator = create_security_validator('api_upload')
    admin_validator = create_security_validator('admin_upload')
    
    print("🏭 Validator-Factory erstellt verschiedene Validatoren:")
    print("   • Web-Validator (strenge Limits)")
    print("   • API-Validator (moderate Limits)")
    print("   • Admin-Validator (großzügige Limits)")
    
    # Teste mit einer Beispieldatei
    test_dir = tempfile.mkdtemp(prefix="demo_factory_")
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("Test-Inhalt")
    
    validators = [
        (web_validator, "Web-Validator"),
        (api_validator, "API-Validator"),
        (admin_validator, "Admin-Validator")
    ]
    
    print(f"\n📄 Test-Datei: {os.path.basename(test_file)}")
    for validator, name in validators:
        is_safe, message = validator(test_file, 'demo_user')
        status = "✅ OK" if is_safe else "❌ FEHLER"
        print(f"   {status} {name}: {message}")

def demo_rate_limiting():
    """Demonstriert Rate Limiting"""
    print_header("Demo: Rate Limiting")
    
    print("🚦 Rate Limiting schützt vor Spam und Missbrauch:")
    print("   • Max. 50 Uploads pro Stunde")
    print("   • Max. 200 Uploads pro Tag")
    
    # Simuliere mehrere Uploads
    test_dir = tempfile.mkdtemp(prefix="demo_rate_")
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("Test für Rate Limiting")
    
    user_id = "demo_rate_user"
    
    print(f"\n👤 Simuliere Uploads für User: {user_id}")
    for i in range(5):
        is_safe, message = validate_file_upload(test_file, 'web_upload', user_id)
        status = "✅ ERLAUBT" if is_safe else "❌ BLOCKIERT"
        print(f"   Upload {i+1}: {status}")

def main():
    """Hauptfunktion für alle Demos"""
    print("🔒 Security Validation Tool - Demo")
    print("Demonstriert die Funktionen des verbesserten Security-Tools")
    
    try:
        print_limits()
        print_allowed_types()
        demo_basic_validation()
        demo_zip_validation()
        demo_upload_types()
        demo_validator_factory()
        demo_rate_limiting()
        
        print_header("Demo abgeschlossen")
        print("✨ Das Security-Validierungstool bietet umfassenden Schutz:")
        print("   • Whitelist-basierte Dateityp-Validierung")
        print("   • Directory Traversal Schutz")
        print("   • ZIP-Bomb Schutz")
        print("   • Rate Limiting")
        print("   • Flexible Upload-Limits")
        print("   • MIME-Type Validierung")
        print("   • Verdächtige Muster-Erkennung")
        
    except Exception as e:
        print(f"❌ Fehler in der Demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
