#!/usr/bin/env python3
"""
Live Demo des Security-Validierungstools
Interaktive Kommandozeilen-Demo mit Echtzeit-Feedback
"""

import os
import tempfile
import zipfile
import time
from datetime import datetime
from security_validation import (
    validate_file_upload,
    validate_zip_file,
    create_security_validator,
    UPLOAD_LIMITS,
    ALLOWED_EXTENSIONS,
    upload_tracker
)

class LiveDemo:
    def __init__(self):
        self.stats = {
            'total_uploads': 0,
            'safe_uploads': 0,
            'blocked_uploads': 0,
            'start_time': datetime.now()
        }
        self.validators = {
            'web': create_security_validator('web_upload'),
            'api': create_security_validator('api_upload'),
            'admin': create_security_validator('admin_upload')
        }
        
    def print_header(self):
        """Druckt den Demo-Header"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("🔒" + "="*60 + "🔒")
        print("    SECURITY VALIDATION TOOL - LIVE DEMO")
        print("🔒" + "="*60 + "🔒")
        print()
        
    def print_stats(self):
        """Zeigt aktuelle Statistiken"""
        runtime = datetime.now() - self.stats['start_time']
        print(f"📊 STATISTIKEN (Laufzeit: {runtime.seconds}s)")
        print("-" * 40)
        print(f"   Gesamt Uploads: {self.stats['total_uploads']}")
        print(f"   ✅ Sichere Dateien: {self.stats['safe_uploads']}")
        print(f"   ❌ Blockierte Dateien: {self.stats['blocked_uploads']}")
        if self.stats['total_uploads'] > 0:
            success_rate = (self.stats['safe_uploads'] / self.stats['total_uploads']) * 100
            print(f"   📈 Erfolgsrate: {success_rate:.1f}%")
        print()
        
    def print_limits(self):
        """Zeigt Upload-Limits"""
        print("📋 UPLOAD-LIMITS")
        print("-" * 40)
        for upload_type, limits in UPLOAD_LIMITS.items():
            print(f"   {upload_type.upper()}:")
            print(f"     • Max. Dateigröße: {limits['max_file_size']/1024/1024:.0f} MB")
            print(f"     • Max. ZIP-Größe: {limits['max_zip_size']/1024/1024:.0f} MB")
        print()
        
    def create_test_files(self):
        """Erstellt Test-Dateien für die Demo"""
        print("🧪 Erstelle Test-Dateien...")
        
        test_dir = tempfile.mkdtemp(prefix="live_demo_")
        
        # Sichere Test-Dateien
        safe_files = {
            'dokument.pdf': b'%PDF-1.4\nSicheres PDF-Dokument',
            'bild.jpg': b'\xff\xd8\xff\xe0JFIF\x00\x01' + b'\x00' * 100,
            'text.txt': b'Dies ist eine sichere Textdatei.',
            'script.py': b'print("Hello World")\n# Sicherer Python Code'
        }
        
        # Unsichere Test-Dateien
        unsafe_files = {
            'backdoor.txt': b'Diese Datei hat einen verdaechtigen Namen',
            'malware.exe.txt': b'Versteckte Executable-Erweiterung',
            'traversal.txt': b'Directory Traversal Versuch'
        }
        
        created_files = {'safe': {}, 'unsafe': {}}
        
        # Erstelle sichere Dateien
        for filename, content in safe_files.items():
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(content)
            created_files['safe'][filename] = filepath
            
        # Erstelle unsichere Dateien
        for filename, content in unsafe_files.items():
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(content)
            created_files['unsafe'][filename] = filepath
        
        # Erstelle Test-ZIPs
        safe_zip = os.path.join(test_dir, 'sicher.zip')
        with zipfile.ZipFile(safe_zip, 'w') as zf:
            for filename, content in safe_files.items():
                zf.writestr(filename, content)
        created_files['safe']['sicher.zip'] = safe_zip
        
        unsafe_zip = os.path.join(test_dir, 'unsicher.zip')
        with zipfile.ZipFile(unsafe_zip, 'w') as zf:
            zf.writestr('normal.txt', b'Normaler Inhalt')
            zf.writestr('../../../etc/passwd', b'Directory Traversal in ZIP')
        created_files['unsafe']['unsicher.zip'] = unsafe_zip
        
        print(f"✅ Test-Dateien erstellt in: {test_dir}")
        print()
        
        return test_dir, created_files
        
    def validate_file_live(self, filepath, upload_type='web', user_id='demo_user'):
        """Validiert eine Datei mit Live-Feedback"""
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        
        print(f"🔍 VALIDIERE: {filename}")
        print("-" * 50)
        print(f"   📄 Datei: {filename}")
        print(f"   📏 Größe: {file_size/1024:.1f} KB")
        print(f"   🔧 Upload-Typ: {upload_type}")
        print(f"   👤 User: {user_id}")
        print()
        
        # Simuliere Validierungsschritte
        steps = [
            "Prüfe Dateiname...",
            "Analysiere MIME-Type...",
            "Scanne Dateiinhalt...",
            "Prüfe Größenlimits...",
            "Validiere Sicherheit..."
        ]
        
        for step in steps:
            print(f"   ⏳ {step}")
            time.sleep(0.3)  # Simuliere Verarbeitungszeit
        
        print()
        
        # Führe echte Validierung durch
        start_time = time.time()
        validator = self.validators[upload_type]
        is_safe, message = validator(filepath, user_id)
        validation_time = (time.time() - start_time) * 1000
        
        # Update Statistiken
        self.stats['total_uploads'] += 1
        if is_safe:
            self.stats['safe_uploads'] += 1
        else:
            self.stats['blocked_uploads'] += 1
        
        # Zeige Ergebnis
        status = "✅ SICHER" if is_safe else "❌ UNSICHER"
        color = "\033[92m" if is_safe else "\033[91m"  # Grün/Rot
        reset = "\033[0m"
        
        print(f"   {color}{status}{reset}")
        print(f"   📝 Details: {message}")
        print(f"   ⏱️  Validierungszeit: {validation_time:.1f}ms")
        print()
        
        return is_safe, message
        
    def demo_batch_validation(self, test_files):
        """Demonstriert Batch-Validierung"""
        print("🚀 BATCH-VALIDIERUNG")
        print("="*50)
        
        all_files = {**test_files['safe'], **test_files['unsafe']}
        
        for filename, filepath in all_files.items():
            self.validate_file_live(filepath, 'web', 'batch_user')
            
            # Kurze Pause zwischen Dateien
            print("   " + "-"*30)
            time.sleep(1)
            
    def demo_upload_types(self, test_file):
        """Demonstriert verschiedene Upload-Typen"""
        print("🔧 UPLOAD-TYPEN VERGLEICH")
        print("="*50)
        
        upload_types = ['web', 'api', 'admin']
        
        for upload_type in upload_types:
            print(f"\n🔹 {upload_type.upper()}-UPLOAD:")
            limits = UPLOAD_LIMITS[f'{upload_type}_upload']
            print(f"   Max. Größe: {limits['max_file_size']/1024/1024:.0f} MB")
            
            self.validate_file_live(test_file, upload_type, f'{upload_type}_user')
            time.sleep(0.5)
            
    def demo_rate_limiting(self, test_file):
        """Demonstriert Rate Limiting"""
        print("🚦 RATE LIMITING DEMO")
        print("="*50)
        
        user_id = "rate_test_user"
        
        print(f"👤 Teste Rate Limiting für User: {user_id}")
        print("   Limit: 50 Uploads/Stunde")
        print()
        
        for i in range(5):
            print(f"🔄 Upload {i+1}/5:")
            self.validate_file_live(test_file, 'web', user_id)
            
            # Zeige Rate Limit Status
            uploads = upload_tracker.get(user_id, [])
            print(f"   📊 Aktuelle Uploads: {len(uploads)}/50")
            print()
            time.sleep(0.5)
            
    def interactive_mode(self, test_files):
        """Interaktiver Modus"""
        while True:
            self.print_header()
            self.print_stats()
            
            print("🎮 INTERAKTIVER MODUS")
            print("="*50)
            print("1. 📄 Einzelne Datei testen")
            print("2. 🚀 Batch-Validierung")
            print("3. 🔧 Upload-Typen vergleichen")
            print("4. 🚦 Rate Limiting testen")
            print("5. 📋 Limits anzeigen")
            print("6. 🧪 Neue Test-Dateien erstellen")
            print("0. ❌ Beenden")
            print()
            
            choice = input("Wählen Sie eine Option (0-6): ").strip()
            
            if choice == '0':
                print("\n👋 Demo beendet. Auf Wiedersehen!")
                break
            elif choice == '1':
                self.single_file_test(test_files)
            elif choice == '2':
                self.demo_batch_validation(test_files)
            elif choice == '3':
                test_file = list(test_files['safe'].values())[0]
                self.demo_upload_types(test_file)
            elif choice == '4':
                test_file = list(test_files['safe'].values())[0]
                self.demo_rate_limiting(test_file)
            elif choice == '5':
                self.print_limits()
            elif choice == '6':
                test_dir, test_files = self.create_test_files()
            else:
                print("❌ Ungültige Auswahl!")
                
            input("\n⏎ Drücken Sie Enter um fortzufahren...")
            
    def single_file_test(self, test_files):
        """Einzelne Datei testen"""
        print("\n📄 EINZELNE DATEI TESTEN")
        print("-"*30)
        
        all_files = {**test_files['safe'], **test_files['unsafe']}
        
        print("Verfügbare Test-Dateien:")
        for i, filename in enumerate(all_files.keys(), 1):
            safety = "✅" if filename in test_files['safe'] else "❌"
            print(f"   {i}. {safety} {filename}")
        
        try:
            choice = int(input("\nWählen Sie eine Datei (Nummer): ")) - 1
            filenames = list(all_files.keys())
            
            if 0 <= choice < len(filenames):
                filename = filenames[choice]
                filepath = all_files[filename]
                
                upload_type = input("Upload-Typ (web/api/admin) [web]: ").strip() or 'web'
                user_id = input("User ID [demo_user]: ").strip() or 'demo_user'
                
                print()
                self.validate_file_live(filepath, upload_type, user_id)
            else:
                print("❌ Ungültige Auswahl!")
                
        except ValueError:
            print("❌ Bitte geben Sie eine gültige Nummer ein!")

def main():
    """Hauptfunktion"""
    demo = LiveDemo()
    
    try:
        demo.print_header()
        print("🚀 Willkommen zur Live-Demo des Security-Validierungstools!")
        print()
        print("Diese Demo zeigt Ihnen:")
        print("   • Echtzeit-Dateivalidierung")
        print("   • Verschiedene Upload-Typen")
        print("   • Rate Limiting")
        print("   • Sicherheitsfeatures")
        print()
        
        # Erstelle Test-Dateien
        test_dir, test_files = demo.create_test_files()
        
        input("⏎ Drücken Sie Enter um zu starten...")
        
        # Starte interaktiven Modus
        demo.interactive_mode(test_files)
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo durch Benutzer beendet.")
    except Exception as e:
        print(f"\n❌ Fehler in der Demo: {e}")

if __name__ == "__main__":
    main()
