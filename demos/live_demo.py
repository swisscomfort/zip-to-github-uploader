#!/usr/bin/env python3
"""
Live Demo des Security-Validierungstools
Web-Interface mit Flask für Echtzeit-Tests
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import tempfile
import zipfile
from datetime import datetime
from security_validation import (
    validate_file_upload,
    validate_zip_file,
    create_security_validator,
    UPLOAD_LIMITS,
    ALLOWED_EXTENSIONS,
    upload_tracker
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Erstelle Validatoren
web_validator = create_security_validator('web_upload')
api_validator = create_security_validator('api_upload')
admin_validator = create_security_validator('admin_upload')

# Statistiken
stats = {
    'total_uploads': 0,
    'safe_uploads': 0,
    'blocked_uploads': 0,
    'last_uploads': []
}

@app.route('/')
def index():
    """Hauptseite mit Upload-Interface"""
    return render_template('index.html', 
                         upload_limits=UPLOAD_LIMITS,
                         allowed_extensions=ALLOWED_EXTENSIONS,
                         stats=stats)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Datei-Upload und Validierung"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
        
        file = request.files['file']
        upload_type = request.form.get('upload_type', 'web_upload')
        user_id = request.form.get('user_id', 'demo_user')
        
        if file.filename == '':
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
        
        # Speichere temporär
        temp_dir = tempfile.mkdtemp(prefix="live_demo_")
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Wähle Validator basierend auf Upload-Typ
        validators = {
            'web_upload': web_validator,
            'api_upload': api_validator,
            'admin_upload': admin_validator
        }
        
        validator = validators.get(upload_type, web_validator)
        
        # Validiere Datei
        start_time = datetime.now()
        is_safe, message = validator(temp_path, user_id)
        validation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Sammle Datei-Informationen
        file_size = os.path.getsize(temp_path)
        file_info = {
            'filename': file.filename,
            'size': file_size,
            'size_mb': round(file_size / 1024 / 1024, 2),
            'upload_type': upload_type,
            'user_id': user_id,
            'is_safe': is_safe,
            'message': message,
            'validation_time_ms': round(validation_time, 2),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        # Update Statistiken
        stats['total_uploads'] += 1
        if is_safe:
            stats['safe_uploads'] += 1
        else:
            stats['blocked_uploads'] += 1
        
        stats['last_uploads'].insert(0, file_info)
        if len(stats['last_uploads']) > 10:
            stats['last_uploads'] = stats['last_uploads'][:10]
        
        # Aufräumen
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        return jsonify({
            'status': 'success' if is_safe else 'blocked',
            'file_info': file_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Upload: {str(e)}'}), 500

@app.route('/stats')
def get_stats():
    """API für aktuelle Statistiken"""
    return jsonify(stats)

@app.route('/rate_limit_status/<user_id>')
def rate_limit_status(user_id):
    """Zeigt Rate Limit Status für einen User"""
    uploads = upload_tracker.get(user_id, [])
    now = datetime.now()
    
    # Zähle Uploads der letzten Stunde
    hour_ago = now.replace(minute=now.minute-60) if now.minute >= 60 else now.replace(hour=now.hour-1, minute=now.minute+60-60)
    uploads_last_hour = sum(1 for timestamp in uploads if timestamp > hour_ago)
    
    return jsonify({
        'user_id': user_id,
        'uploads_last_hour': uploads_last_hour,
        'max_per_hour': 50,
        'remaining': max(0, 50 - uploads_last_hour)
    })

@app.route('/create_test_files')
def create_test_files():
    """Erstellt Test-Dateien zum Download"""
    test_dir = tempfile.mkdtemp(prefix="test_files_")
    
    # Sichere Test-Dateien
    safe_files = {
        'sicher.txt': b'Dies ist eine sichere Textdatei.',
        'dokument.pdf': b'%PDF-1.4\nSicheres PDF-Dokument',
        'bild.jpg': b'\xff\xd8\xff\xe0JFIF\x00\x01' + b'\x00' * 100,
        'script.py': b'print("Hello World")\n# Sicherer Python Code'
    }
    
    # Unsichere Test-Dateien
    unsafe_files = {
        'backdoor.txt': b'Diese Datei hat einen verdaechtigen Namen',
        'datei.exe.txt': b'Versteckte Executable-Erweiterung',
        'traversal_.._.._etc_passwd': b'Directory Traversal Versuch'
    }
    
    # Erstelle sichere ZIP
    safe_zip = os.path.join(test_dir, 'sicher.zip')
    with zipfile.ZipFile(safe_zip, 'w') as zf:
        for filename, content in safe_files.items():
            zf.writestr(filename, content)
    
    # Erstelle unsichere ZIP
    unsafe_zip = os.path.join(test_dir, 'unsicher.zip')
    with zipfile.ZipFile(unsafe_zip, 'w') as zf:
        zf.writestr('normal.txt', b'Normaler Inhalt')
        zf.writestr('../../../etc/passwd', b'Directory Traversal in ZIP')
    
    all_files = {**safe_files, **unsafe_files}
    all_files['sicher.zip'] = b'ZIP-Archiv mit sicheren Dateien'
    all_files['unsicher.zip'] = b'ZIP-Archiv mit Directory Traversal'
    
    # Erstelle alle Dateien
    created_files = []
    for filename, content in all_files.items():
        if not filename.endswith('.zip'):
            filepath = os.path.join(test_dir, filename.replace('_', ''))
            with open(filepath, 'wb') as f:
                f.write(content)
            created_files.append(filename.replace('_', ''))
    
    created_files.extend(['sicher.zip', 'unsicher.zip'])
    
    return jsonify({
        'test_dir': test_dir,
        'files': created_files,
        'message': 'Test-Dateien erstellt. Verwenden Sie diese für Live-Tests!'
    })

if __name__ == '__main__':
    # Erstelle Template-Verzeichnis falls nicht vorhanden
    os.makedirs('templates', exist_ok=True)
    
    # Erstelle HTML-Template
    html_template = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 Security Validation Tool - Live Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .upload-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; }
        .results-section { background: #f1f8e9; padding: 20px; border-radius: 8px; }
        .upload-form { display: grid; gap: 15px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { font-weight: bold; margin-bottom: 5px; }
        .form-group input, .form-group select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .upload-btn { background: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .upload-btn:hover { background: #45a049; }
        .result { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .result.safe { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .result.unsafe { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .recent-uploads { max-height: 300px; overflow-y: auto; }
        .upload-item { background: white; margin: 5px 0; padding: 10px; border-radius: 4px; border-left: 4px solid #ddd; }
        .upload-item.safe { border-left-color: #28a745; }
        .upload-item.unsafe { border-left-color: #dc3545; }
        .limits-info { background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .test-files-btn { background: #17a2b8; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Security Validation Tool</h1>
            <h2>Live Demo - Testen Sie Dateien in Echtzeit!</h2>
        </div>
        
        <div class="limits-info">
            <h3>📋 Upload-Limits:</h3>
            <p><strong>Web:</strong> 25MB | <strong>API:</strong> 100MB | <strong>Admin:</strong> 500MB</p>
            <button class="test-files-btn" onclick="createTestFiles()">🧪 Test-Dateien erstellen</button>
        </div>
        
        <div class="upload-section">
            <h3>📤 Datei hochladen und validieren</h3>
            <form class="upload-form" id="uploadForm">
                <div class="form-group">
                    <label for="file">Datei auswählen:</label>
                    <input type="file" id="file" name="file" required>
                </div>
                <div class="form-group">
                    <label for="upload_type">Upload-Typ:</label>
                    <select id="upload_type" name="upload_type">
                        <option value="web_upload">Web Upload (25MB)</option>
                        <option value="api_upload">API Upload (100MB)</option>
                        <option value="admin_upload">Admin Upload (500MB)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="user_id">User ID:</label>
                    <input type="text" id="user_id" name="user_id" value="demo_user" required>
                </div>
                <button type="submit" class="upload-btn">🔍 Datei validieren</button>
            </form>
        </div>
        
        <div class="stats-section">
            <div class="stat-card">
                <h3>📊 Statistiken</h3>
                <div id="stats">
                    <p>Gesamt: <span id="total">0</span></p>
                    <p>✅ Sicher: <span id="safe">0</span></p>
                    <p>❌ Blockiert: <span id="blocked">0</span></p>
                </div>
            </div>
            <div class="stat-card">
                <h3>🚦 Rate Limiting</h3>
                <div id="rateLimit">
                    <p>User: <span id="currentUser">demo_user</span></p>
                    <p>Uploads/Stunde: <span id="hourlyUploads">0</span>/50</p>
                    <p>Verbleibend: <span id="remaining">50</span></p>
                </div>
            </div>
        </div>
        
        <div class="results-section">
            <h3>📋 Letzte Validierungen</h3>
            <div id="results" class="recent-uploads">
                <p>Noch keine Uploads...</p>
            </div>
        </div>
    </div>
    
    <script>
        // Upload-Formular Handler
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const uploadBtn = document.querySelector('.upload-btn');
            
            uploadBtn.textContent = '⏳ Validiere...';
            uploadBtn.disabled = true;
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayResult(result);
                updateStats();
                updateRateLimit();
                
            } catch (error) {
                displayResult({error: 'Fehler beim Upload: ' + error.message});
            }
            
            uploadBtn.textContent = '🔍 Datei validieren';
            uploadBtn.disabled = false;
        });
        
        // Ergebnis anzeigen
        function displayResult(result) {
            const resultsDiv = document.getElementById('results');
            
            if (result.error) {
                resultsDiv.innerHTML = `<div class="result unsafe">❌ Fehler: ${result.error}</div>` + resultsDiv.innerHTML;
                return;
            }
            
            const fileInfo = result.file_info;
            const statusClass = fileInfo.is_safe ? 'safe' : 'unsafe';
            const statusIcon = fileInfo.is_safe ? '✅' : '❌';
            
            const resultHTML = `
                <div class="upload-item ${statusClass}">
                    <strong>${statusIcon} ${fileInfo.filename}</strong> (${fileInfo.size_mb} MB)
                    <br>📝 ${fileInfo.message}
                    <br>⏱️ ${fileInfo.validation_time_ms}ms | 👤 ${fileInfo.user_id} | 🔧 ${fileInfo.upload_type}
                    <br>🕐 ${fileInfo.timestamp}
                </div>
            `;
            
            resultsDiv.innerHTML = resultHTML + resultsDiv.innerHTML;
        }
        
        // Statistiken aktualisieren
        async function updateStats() {
            try {
                const response = await fetch('/stats');
                const stats = await response.json();
                
                document.getElementById('total').textContent = stats.total_uploads;
                document.getElementById('safe').textContent = stats.safe_uploads;
                document.getElementById('blocked').textContent = stats.blocked_uploads;
            } catch (error) {
                console.error('Fehler beim Laden der Statistiken:', error);
            }
        }
        
        // Rate Limit Status aktualisieren
        async function updateRateLimit() {
            const userId = document.getElementById('user_id').value;
            try {
                const response = await fetch(`/rate_limit_status/${userId}`);
                const rateLimit = await response.json();
                
                document.getElementById('currentUser').textContent = rateLimit.user_id;
                document.getElementById('hourlyUploads').textContent = rateLimit.uploads_last_hour;
                document.getElementById('remaining').textContent = rateLimit.remaining;
            } catch (error) {
                console.error('Fehler beim Laden des Rate Limits:', error);
            }
        }
        
        // Test-Dateien erstellen
        async function createTestFiles() {
            try {
                const response = await fetch('/create_test_files');
                const result = await response.json();
                alert(`✅ ${result.message}\\n\\nTest-Verzeichnis: ${result.test_dir}\\n\\nDateien: ${result.files.join(', ')}`);
            } catch (error) {
                alert('❌ Fehler beim Erstellen der Test-Dateien: ' + error.message);
            }
        }
        
        // Automatische Updates
        setInterval(updateStats, 5000);
        setInterval(updateRateLimit, 10000);
        
        // Initial laden
        updateStats();
        updateRateLimit();
    </script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("🚀 Starte Live Demo des Security-Validierungstools...")
    print("📱 Öffnen Sie http://localhost:5000 in Ihrem Browser")
    print("🔒 Testen Sie verschiedene Dateien und sehen Sie die Validierung in Echtzeit!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
