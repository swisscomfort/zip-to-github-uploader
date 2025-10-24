#!/usr/bin/env python3
"""
Demo für detaillierte Validierungsinformationen für Web-Interface
Zeigt alle Informationen, die vor einem GitHub Upload verfügbar sind
"""

import json
import tempfile
import os
from datetime import datetime
from security_validation import (
    validate_file_upload,
    get_detailed_file_info,
    format_file_size
)

def print_detailed_validation(file_path, upload_type='web_upload', user_id='web_user'):
    """Zeigt detaillierte Validierungsinformationen für Web-Interface"""
    
    print("🌐" + "="*70 + "🌐")
    print("    WEB-INTERFACE VALIDIERUNG - DETAILLIERTE INFORMATIONEN")
    print("🌐" + "="*70 + "🌐")
    print()
    
    # Hole detaillierte Validierungsinformationen
    is_safe, detailed_info = validate_file_upload(
        file_path, 
        upload_type=upload_type, 
        user_id=user_id, 
        detailed=True
    )
    
    # Hole zusätzliche Dateiinformationen
    file_info = get_detailed_file_info(file_path)
    
    # 1. DATEI-ÜBERSICHT
    print("📄 DATEI-ÜBERSICHT")
    print("-" * 50)
    print(f"   📁 Dateiname: {detailed_info['filename']}")
    print(f"   📏 Größe: {file_info['file_size_formatted']}")
    print(f"   📂 Kategorie: {file_info['file_category'] or 'Unbekannt'}")
    print(f"   🔧 Upload-Typ: {detailed_info['upload_type']}")
    print(f"   👤 Benutzer: {detailed_info['user_id']}")
    print(f"   ⏰ Validiert: {detailed_info['timestamp']}")
    print(f"   📊 Binärdatei: {'Ja' if file_info['is_binary'] else 'Nein'}")
    print(f"   ⏱️  Geschätzte Upload-Zeit: {file_info['estimated_upload_time']}")
    print()
    
    # 2. SICHERHEITSBEWERTUNG
    risk_colors = {
        'low': '🟢',
        'medium': '🟡', 
        'high': '🟠',
        'critical': '🔴'
    }
    
    risk_color = risk_colors.get(detailed_info['risk_level'], '⚪')
    security_score = detailed_info.get('security_score', 0)
    
    print("🛡️  SICHERHEITSBEWERTUNG")
    print("-" * 50)
    print(f"   🎯 Gesamtergebnis: {'✅ SICHER' if is_safe else '❌ UNSICHER'}")
    print(f"   {risk_color} Risiko-Level: {detailed_info['risk_level'].upper()}")
    print(f"   📊 Sicherheitsscore: {security_score}/100")
    
    # Score-Balken
    score_bar = "█" * (security_score // 5) + "░" * (20 - security_score // 5)
    print(f"   📈 [{score_bar}] {security_score}%")
    print()
    
    # 3. DETAILLIERTE PRÜFUNGEN
    print("🔍 DETAILLIERTE PRÜFUNGEN")
    print("-" * 50)
    
    for check_name, check_info in detailed_info['checks'].items():
        status = "✅ BESTANDEN" if check_info['passed'] else "❌ FEHLGESCHLAGEN"
        print(f"   {status} {check_name.replace('_', ' ').title()}")
        print(f"      📝 {check_info['message']}")
        if 'details' in check_info:
            print(f"      ℹ️  {check_info['details']}")
        print()
    
    # 4. GITHUB-KOMPATIBILITÄT
    if 'github_compatibility' in detailed_info:
        github_info = detailed_info['github_compatibility']
        print("🐙 GITHUB-KOMPATIBILITÄT")
        print("-" * 50)
        
        compat_status = "✅ KOMPATIBEL" if github_info['is_compatible'] else "❌ INKOMPATIBEL"
        print(f"   🎯 Status: {compat_status}")
        
        checks = [
            ('Dateigröße', github_info['file_size_ok']),
            ('Dateiname', github_info['filename_ok']),
            ('Encoding', github_info['encoding_ok'])
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        if github_info['warnings']:
            print("   ⚠️  Warnungen:")
            for warning in github_info['warnings']:
                print(f"      • {warning}")
        print()
    
    # 5. FEHLER UND WARNUNGEN
    if detailed_info['errors'] or detailed_info['warnings']:
        print("⚠️  PROBLEME GEFUNDEN")
        print("-" * 50)
        
        if detailed_info['errors']:
            print("   🚨 Fehler:")
            for error in detailed_info['errors']:
                print(f"      • {error}")
        
        if detailed_info['warnings']:
            print("   ⚠️  Warnungen:")
            for warning in detailed_info['warnings']:
                print(f"      • {warning}")
        print()
    
    # 6. EMPFEHLUNGEN
    if detailed_info['recommendations']:
        print("💡 EMPFEHLUNGEN")
        print("-" * 50)
        for i, recommendation in enumerate(detailed_info['recommendations'], 1):
            print(f"   {i}. {recommendation}")
        print()
    
    # 7. JSON-AUSGABE FÜR WEB-API
    print("🔧 JSON-AUSGABE FÜR WEB-API")
    print("-" * 50)
    
    # Kombiniere alle Informationen für API
    api_response = {
        'validation': detailed_info,
        'file_info': file_info,
        'timestamp': datetime.now().isoformat(),
        'api_version': '1.0'
    }
    
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    return is_safe, detailed_info

def demo_different_files():
    """Demonstriert verschiedene Dateitypen"""
    
    # Erstelle Test-Dateien
    test_dir = tempfile.mkdtemp(prefix="web_demo_")
    
    test_files = {
        'sicher.txt': b'Dies ist eine sichere Textdatei für GitHub.',
        'dokument.pdf': b'%PDF-1.4\nSicheres PDF-Dokument',
        'bild.jpg': b'\xff\xd8\xff\xe0JFIF\x00\x01' + b'\x00' * 100,
        'script.py': b'print("Hello GitHub")\n# Sicherer Python Code',
        'backdoor.txt': b'Diese Datei hat einen verdächtigen Namen',
        'große_datei.txt': b'X' * (30 * 1024 * 1024),  # 30 MB Datei
    }
    
    print("🧪 DEMO: VERSCHIEDENE DATEITYPEN FÜR WEB-INTERFACE")
    print("="*80)
    print()
    
    for filename, content in test_files.items():
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        
        print(f"📁 TESTE DATEI: {filename}")
        print("="*80)
        
        try:
            is_safe, detailed_info = print_detailed_validation(filepath, 'web_upload', 'demo_user')
            
            print(f"\n🎯 ZUSAMMENFASSUNG FÜR {filename}:")
            print(f"   Status: {'✅ Upload erlaubt' if is_safe else '❌ Upload blockiert'}")
            print(f"   Score: {detailed_info.get('security_score', 0)}/100")
            print(f"   Risiko: {detailed_info['risk_level']}")
            
        except Exception as e:
            print(f"❌ Fehler bei {filename}: {e}")
        
        print("\n" + "="*80 + "\n")
        
        # Kurze Pause zwischen Dateien
        input("⏎ Drücken Sie Enter für die nächste Datei...")

def main():
    """Hauptfunktion"""
    print("🌐 WEB-INTERFACE VALIDIERUNG DEMO")
    print("Zeigt detaillierte Informationen für GitHub Upload-Validierung")
    print()
    
    choice = input("Möchten Sie (1) eine eigene Datei testen oder (2) die Demo mit Beispieldateien? [1/2]: ").strip()
    
    if choice == '1':
        file_path = input("Geben Sie den Pfad zur Datei ein: ").strip()
        if os.path.exists(file_path):
            upload_type = input("Upload-Typ (web/api/admin) [web]: ").strip() or 'web'
            user_id = input("User-ID [web_user]: ").strip() or 'web_user'
            
            upload_type = f'{upload_type}_upload'
            print_detailed_validation(file_path, upload_type, user_id)
        else:
            print(f"❌ Datei nicht gefunden: {file_path}")
    
    elif choice == '2':
        demo_different_files()
    
    else:
        print("❌ Ungültige Auswahl")

if __name__ == "__main__":
    main()
