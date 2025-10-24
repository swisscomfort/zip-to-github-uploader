#!/usr/bin/env python3
"""
Test-Skript für das Security-Validierungstool
"""

import os
import tempfile
import zipfile
from security_validation import (
    validate_file_upload,
    validate_zip_file,
    is_safe_filename,
    is_safe_path,
    get_file_category,
    check_rate_limit,
    create_security_validator,
    UPLOAD_LIMITS,
    ALLOWED_EXTENSIONS
)

def create_test_files():
    """Erstellt Test-Dateien für die Validierung"""
    test_dir = tempfile.mkdtemp(prefix="security_test_")
    print(f"Test-Verzeichnis: {test_dir}")
    
    # Sichere Test-Dateien
    safe_files = {
        "test.txt": b"Dies ist eine sichere Textdatei.",
        "image.jpg": b"\xff\xd8\xff\xe0" + b"JFIF" + b"\x00" * 100,  # JPEG Header
        "document.pdf": b"%PDF-1.4" + b"\x00" * 100,  # PDF Header
        "code.py": b"print('Hello World')\n# Sicherer Python Code",
    }
    
    # Unsichere Test-Dateien
    unsafe_files = {
        "malware.exe": b"MZ" + b"\x00" * 100,  # Windows PE Header
        "script.js": b"eval('malicious code');",
        "backdoor.txt": b"This file contains backdoor",
        "traversal../../../etc/passwd": b"root:x:0:0:root:/root:/bin/bash",
    }
    
    created_files = {"safe": {}, "unsafe": {}}
    
    # Erstelle sichere Dateien
    for filename, content in safe_files.items():
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        created_files["safe"][filename] = filepath
    
    # Erstelle unsichere Dateien
    for filename, content in unsafe_files.items():
        # Sichere Dateinamen für das Dateisystem
        safe_filename = filename.replace("../", "_").replace("/", "_")
        filepath = os.path.join(test_dir, safe_filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        created_files["unsafe"][filename] = filepath
    
    return test_dir, created_files

def create_test_zip(test_dir, files_dict):
    """Erstellt Test-ZIP-Dateien"""
    zip_files = {}
    
    # Sichere ZIP
    safe_zip = os.path.join(test_dir, "safe_archive.zip")
    with zipfile.ZipFile(safe_zip, 'w') as zf:
        for filename, filepath in files_dict["safe"].items():
            zf.write(filepath, filename)
    zip_files["safe"] = safe_zip
    
    # Unsichere ZIP mit Directory Traversal
    unsafe_zip = os.path.join(test_dir, "unsafe_archive.zip")
    with zipfile.ZipFile(unsafe_zip, 'w') as zf:
        # Normale Datei
        zf.write(list(files_dict["safe"].values())[0], "normal.txt")
        # Directory Traversal Versuch
        zf.write(list(files_dict["safe"].values())[0], "../../../etc/passwd")
    zip_files["unsafe"] = unsafe_zip
    
    return zip_files

def test_filename_validation():
    """Testet die Dateinamen-Validierung"""
    print("\n=== Test: Dateinamen-Validierung ===")
    
    test_cases = [
        # (filename, expected_safe, description)
        ("document.pdf", True, "Normale PDF-Datei"),
        ("image.jpg", True, "Normale JPEG-Datei"),
        ("script.py", True, "Python-Datei"),
        ("malware.exe", False, "Executable-Datei"),
        ("file.exe.txt", False, "Versteckte Executable"),
        ("../../../etc/passwd", False, "Directory Traversal"),
        ("backdoor_script.py", False, "Verdächtiger Name"),
        ("normal<script>.html", False, "Gefährliche Zeichen"),
    ]
    
    for filename, expected_safe, description in test_cases:
        is_safe, message = is_safe_filename(filename)
        status = "✅ PASS" if (is_safe == expected_safe) else "❌ FAIL"
        print(f"{status} {description}: {filename}")
        if not is_safe:
            print(f"    Grund: {message}")

def test_file_category():
    """Testet die Dateikategorie-Erkennung"""
    print("\n=== Test: Dateikategorie-Erkennung ===")
    
    test_cases = [
        ("document.pdf", "document"),
        ("image.jpg", "image"),
        ("script.py", "code"),
        ("archive.zip", "archive"),
        ("music.mp3", "audio"),
        ("video.mp4", "video"),
        ("malware.exe", None),  # Nicht erlaubt
    ]
    
    for filename, expected_category in test_cases:
        category = get_file_category(filename)
        status = "✅ PASS" if (category == expected_category) else "❌ FAIL"
        print(f"{status} {filename} -> {category} (erwartet: {expected_category})")

def test_rate_limiting():
    """Testet das Rate Limiting"""
    print("\n=== Test: Rate Limiting ===")
    
    user_id = "test_user_123"
    
    # Erste Uploads sollten OK sein
    for i in range(3):
        is_ok, message = check_rate_limit(user_id)
        print(f"Upload {i+1}: {'✅ OK' if is_ok else '❌ BLOCKED'} - {message}")
    
    print(f"Rate Limit Status für {user_id} getestet")

def test_file_validation(test_files):
    """Testet die Datei-Validierung"""
    print("\n=== Test: Datei-Validierung ===")
    
    # Teste verschiedene Upload-Typen
    upload_types = ["web_upload", "api_upload", "admin_upload"]
    
    for upload_type in upload_types:
        print(f"\n--- Upload-Typ: {upload_type} ---")
        limits = UPLOAD_LIMITS[upload_type]
        print(f"Max. Dateigröße: {limits['max_file_size']/1024/1024:.1f} MB")
        
        # Teste sichere Dateien
        for filename, filepath in test_files["safe"].items():
            is_safe, message = validate_file_upload(filepath, upload_type, "test_user")
            status = "✅ SAFE" if is_safe else "❌ UNSAFE"
            print(f"  {status} {filename}: {message}")

def test_zip_validation(zip_files):
    """Testet die ZIP-Validierung"""
    print("\n=== Test: ZIP-Validierung ===")
    
    for zip_type, zip_path in zip_files.items():
        print(f"\n--- {zip_type.upper()} ZIP ---")
        is_safe, message = validate_zip_file(zip_path, "web_upload", "test_user")
        status = "✅ SAFE" if is_safe else "❌ UNSAFE"
        print(f"{status} {os.path.basename(zip_path)}: {message}")

def test_validator_factory():
    """Testet die Validator-Factory"""
    print("\n=== Test: Validator Factory ===")
    
    # Erstelle verschiedene Validatoren
    web_validator = create_security_validator('web_upload')
    api_validator = create_security_validator('api_upload')
    
    print("✅ Web-Validator erstellt")
    print("✅ API-Validator erstellt")
    print("Factory-Pattern funktioniert")

def main():
    """Hauptfunktion für alle Tests"""
    print("🔒 Security Validation Tool - Test Suite")
    print("=" * 50)
    
    try:
        # Erstelle Test-Dateien
        test_dir, test_files = create_test_files()
        zip_files = create_test_zip(test_dir, test_files)
        
        # Führe Tests durch
        test_filename_validation()
        test_file_category()
        test_rate_limiting()
        test_file_validation(test_files)
        test_zip_validation(zip_files)
        test_validator_factory()
        
        print("\n" + "=" * 50)
        print("🎉 Alle Tests abgeschlossen!")
        print(f"📁 Test-Dateien in: {test_dir}")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
