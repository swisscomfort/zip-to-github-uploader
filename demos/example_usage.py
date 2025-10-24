#!/usr/bin/env python3
"""
Beispiel für die praktische Nutzung des Security-Validierungstools
"""

from security_validation import (
    validate_file_upload,
    validate_zip_file,
    create_security_validator
)

def example_web_upload(file_path, user_id):
    """Beispiel für Web-Upload-Validierung"""
    print(f"🌐 Web-Upload Validierung für: {file_path}")
    
    is_safe, message = validate_file_upload(
        file_path=file_path,
        upload_type='web_upload',
        user_id=user_id
    )
    
    if is_safe:
        print(f"✅ Upload erlaubt: {message}")
        return True
    else:
        print(f"❌ Upload abgelehnt: {message}")
        return False

def example_api_upload(file_path, user_id):
    """Beispiel für API-Upload-Validierung"""
    print(f"🔌 API-Upload Validierung für: {file_path}")
    
    is_safe, message = validate_file_upload(
        file_path=file_path,
        upload_type='api_upload',
        user_id=user_id
    )
    
    if is_safe:
        print(f"✅ API-Upload erlaubt: {message}")
        return True
    else:
        print(f"❌ API-Upload abgelehnt: {message}")
        return False

def example_zip_validation(zip_path, user_id):
    """Beispiel für ZIP-Validierung"""
    print(f"📦 ZIP-Validierung für: {zip_path}")
    
    is_safe, message = validate_zip_file(
        zip_path=zip_path,
        upload_type='web_upload',
        user_id=user_id
    )
    
    if is_safe:
        print(f"✅ ZIP-Upload erlaubt: {message}")
        return True
    else:
        print(f"❌ ZIP-Upload abgelehnt: {message}")
        return False

def example_validator_factory():
    """Beispiel für die Verwendung der Validator-Factory"""
    print("🏭 Validator-Factory Beispiel")
    
    # Erstelle verschiedene Validatoren
    web_validator = create_security_validator('web_upload')
    api_validator = create_security_validator('api_upload')
    admin_validator = create_security_validator('admin_upload')
    
    # Beispiel-Datei (würde in der Praxis vom User hochgeladen)
    example_file = "/tmp/example.txt"
    
    # Erstelle Beispiel-Datei
    try:
        with open(example_file, 'w') as f:
            f.write("Beispiel-Inhalt für Validierung")
        
        print(f"📄 Teste Datei: {example_file}")
        
        # Teste mit verschiedenen Validatoren
        validators = [
            (web_validator, "Web-Validator"),
            (api_validator, "API-Validator"),
            (admin_validator, "Admin-Validator")
        ]
        
        for validator, name in validators:
            is_safe, message = validator(example_file, 'example_user')
            status = "✅ ERLAUBT" if is_safe else "❌ ABGELEHNT"
            print(f"   {status} {name}: {message}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

def flask_integration_example():
    """Beispiel für Flask-Integration"""
    print("\n🌶️  Flask-Integration Beispiel:")
    
    flask_code = '''
from flask import Flask, request, jsonify
from security_validation import create_security_validator

app = Flask(__name__)
web_validator = create_security_validator('web_upload')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Keine Datei'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id', 'anonymous')
    
    # Speichere temporär
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    # Validiere Sicherheit
    is_safe, message = web_validator(temp_path, user_id)
    
    if is_safe:
        # Verarbeite sichere Datei
        return jsonify({'status': 'success', 'message': message})
    else:
        # Lösche unsichere Datei
        os.remove(temp_path)
        return jsonify({'error': message}), 400
'''
    
    print(flask_code)

def django_integration_example():
    """Beispiel für Django-Integration"""
    print("\n🎸 Django-Integration Beispiel:")
    
    django_code = '''
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from security_validation import validate_file_upload

@csrf_exempt
def upload_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        
        # Speichere temporär
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Validiere
        is_safe, message = validate_file_upload(
            temp_path, 
            'web_upload', 
            str(user_id)
        )
        
        if is_safe:
            # Verarbeite sichere Datei
            return JsonResponse({'status': 'success', 'message': message})
        else:
            # Lösche unsichere Datei
            os.remove(temp_path)
            return JsonResponse({'error': message}, status=400)
    
    return JsonResponse({'error': 'Keine Datei'}, status=400)
'''
    
    print(django_code)

def main():
    """Hauptfunktion mit Beispielen"""
    print("🔒 Security Validation Tool - Praktische Beispiele")
    print("=" * 60)
    
    # Beispiele für verschiedene Anwendungsfälle
    print("\n📚 Grundlegende Verwendung:")
    print("=" * 30)
    
    # Diese würden in der Praxis echte Dateipfade sein
    example_files = [
        "/tmp/document.pdf",
        "/tmp/image.jpg", 
        "/tmp/archive.zip"
    ]
    
    # Erstelle Beispiel-Dateien
    for file_path in example_files:
        try:
            with open(file_path, 'w') as f:
                f.write("Beispiel-Inhalt")
        except:
            pass
    
    # Teste verschiedene Validierungsarten
    for file_path in example_files:
        if file_path.endswith('.zip'):
            example_zip_validation(file_path, 'user123')
        else:
            example_web_upload(file_path, 'user123')
        print()
    
    # Validator Factory Beispiel
    example_validator_factory()
    
    # Framework-Integration Beispiele
    flask_integration_example()
    django_integration_example()
    
    print("\n" + "=" * 60)
    print("✨ Weitere Anwendungsmöglichkeiten:")
    print("   • REST API Endpoints")
    print("   • File Upload Services")
    print("   • Content Management Systeme")
    print("   • Cloud Storage Gateways")
    print("   • Backup-Validierung")
    print("   • Email-Anhang-Prüfung")

if __name__ == "__main__":
    main()
