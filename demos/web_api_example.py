#!/usr/bin/env python3
"""
Beispiel für Web-API Integration des Security-Validierungstools
Zeigt JSON-Responses für verschiedene Szenarien
"""

import json
import tempfile
import os
from security_validation import validate_file_upload, get_detailed_file_info


def create_api_response(file_path, upload_type="web_upload", user_id="web_user"):
    """Erstellt eine vollständige API-Response für Web-Interface"""

    try:
        # Detaillierte Validierung
        is_safe, detailed_info = validate_file_upload(
            file_path, upload_type=upload_type, user_id=user_id, detailed=True
        )

        # Zusätzliche Dateiinformationen
        file_info = get_detailed_file_info(file_path)

        # API Response zusammenstellen
        api_response = {
            "status": "success",
            "validation": {
                "is_safe": is_safe,
                "risk_level": detailed_info["risk_level"],
                "security_score": detailed_info.get("security_score", 0),
                "upload_allowed": is_safe,
            },
            "file": {
                "name": detailed_info["filename"],
                "size": file_info["file_size"],
                "size_formatted": file_info["file_size_formatted"],
                "category": file_info["file_category"],
                "is_binary": file_info["is_binary"],
                "estimated_upload_time": file_info["estimated_upload_time"],
            },
            "checks": detailed_info["checks"],
            "github": detailed_info.get("github_compatibility", {}),
            "issues": {
                "errors": detailed_info["errors"],
                "warnings": detailed_info["warnings"],
            },
            "recommendations": detailed_info["recommendations"],
            "metadata": {
                "upload_type": upload_type,
                "user_id": user_id,
                "timestamp": detailed_info["timestamp"],
                "api_version": "1.0",
            },
        }

        return api_response

    except Exception as e:
        return {
            "status": "error",
            "message": f"Validierung fehlgeschlagen: {str(e)}",
            "validation": {"is_safe": False, "upload_allowed": False},
            "metadata": {
                "timestamp": detailed_info.get("timestamp", ""),
                "api_version": "1.0",
            },
        }


def demo_web_api_responses():
    """Demonstriert verschiedene API-Responses"""

    print("🌐 WEB-API RESPONSES FÜR GITHUB UPLOAD VALIDATOR")
    print("=" * 70)
    print()

    # Erstelle Test-Dateien
    test_dir = tempfile.mkdtemp(prefix="api_demo_")

    scenarios = [
        {
            "name": "✅ Sichere Datei",
            "filename": "document.pdf",
            "content": b"%PDF-1.4\nSicheres PDF-Dokument",
            "description": "Normale, sichere Datei für GitHub Upload",
        },
        {
            "name": "❌ Verdächtiger Dateiname",
            "filename": "backdoor_script.txt",
            "content": b"Harmloser Inhalt",
            "description": "Datei mit verdächtigem Namen wird blockiert",
        },
        {
            "name": "⚠️  Große Datei",
            "filename": "large_file.txt",
            "content": b"X" * (30 * 1024 * 1024),  # 30 MB
            "description": "Datei überschreitet GitHub-Empfehlungen",
        },
        {
            "name": "🔒 Versteckte Executable",
            "filename": "document.exe.pdf",
            "content": b"Versteckte ausfuehrbare Datei",
            "description": "Doppelte Erweiterung wird erkannt",
        },
    ]

    for scenario in scenarios:
        print(f"📋 SZENARIO: {scenario['name']}")
        print(f"📄 Beschreibung: {scenario['description']}")
        print("-" * 70)

        # Erstelle Test-Datei
        filepath = os.path.join(test_dir, scenario["filename"])
        with open(filepath, "wb") as f:
            f.write(scenario["content"])

        # Generiere API Response
        api_response = create_api_response(filepath, "web_upload", "demo_user")

        # Zeige JSON Response
        print("🔧 JSON API RESPONSE:")
        print(json.dumps(api_response, indent=2, ensure_ascii=False))
        print()

        # Zeige Web-Interface Interpretation
        print("🌐 WEB-INTERFACE DARSTELLUNG:")
        validation = api_response.get("validation", {})

        if validation.get("is_safe", False):
            print("   🟢 Status: Upload erlaubt")
            print("   ✅ Button: 'Zu GitHub hochladen' (aktiv)")
        else:
            print("   🔴 Status: Upload blockiert")
            print("   ❌ Button: 'Upload nicht möglich' (deaktiviert)")

        score = validation.get("security_score", 0)
        print(f"   📊 Sicherheitsscore: {score}/100")

        # Zeige Benutzer-Feedback
        issues = api_response.get("issues", {})
        if issues.get("errors"):
            print("   🚨 Fehlermeldungen für Benutzer:")
            for error in issues["errors"]:
                print(f"      • {error}")

        if issues.get("warnings"):
            print("   ⚠️  Warnungen für Benutzer:")
            for warning in issues["warnings"]:
                print(f"      • {warning}")

        recommendations = api_response.get("recommendations", [])
        if recommendations:
            print("   💡 Empfehlungen für Benutzer:")
            for rec in recommendations[:3]:  # Zeige nur erste 3
                print(f"      • {rec}")

        print("\n" + "=" * 70 + "\n")


def create_frontend_javascript():
    """Erstellt JavaScript-Code für Frontend-Integration"""

    js_code = """
// JavaScript für Frontend-Integration des GitHub Upload Validators

class GitHubUploadValidator {
    constructor(apiEndpoint) {
        this.apiEndpoint = apiEndpoint;
    }
    
    async validateFile(file, uploadType = 'web_upload', userId = 'user') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('upload_type', uploadType);
        formData.append('user_id', userId);
        
        try {
            const response = await fetch(`${this.apiEndpoint}/validate`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            return this.processValidationResult(result);
            
        } catch (error) {
            return {
                status: 'error',
                message: 'Validierung fehlgeschlagen: ' + error.message,
                validation: { is_safe: false, upload_allowed: false }
            };
        }
    }
    
    processValidationResult(result) {
        // Aktualisiere UI basierend auf Validierungsergebnis
        this.updateUploadButton(result.validation.upload_allowed);
        this.updateSecurityScore(result.validation.security_score);
        this.showIssues(result.issues);
        this.showRecommendations(result.recommendations);
        this.updateGitHubCompatibility(result.github);
        
        return result;
    }
    
    updateUploadButton(uploadAllowed) {
        const button = document.getElementById('upload-button');
        if (uploadAllowed) {
            button.disabled = false;
            button.textContent = '🚀 Zu GitHub hochladen';
            button.className = 'btn btn-success';
        } else {
            button.disabled = true;
            button.textContent = '❌ Upload nicht möglich';
            button.className = 'btn btn-danger';
        }
    }
    
    updateSecurityScore(score) {
        const scoreElement = document.getElementById('security-score');
        const progressBar = document.getElementById('score-progress');
        
        scoreElement.textContent = `${score}/100`;
        progressBar.style.width = `${score}%`;
        
        // Farbe basierend auf Score
        if (score >= 80) {
            progressBar.className = 'progress-bar bg-success';
        } else if (score >= 60) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-danger';
        }
    }
    
    showIssues(issues) {
        const errorsDiv = document.getElementById('validation-errors');
        const warningsDiv = document.getElementById('validation-warnings');
        
        // Zeige Fehler
        if (issues.errors && issues.errors.length > 0) {
            errorsDiv.innerHTML = issues.errors.map(error => 
                `<div class="alert alert-danger">🚨 ${error}</div>`
            ).join('');
            errorsDiv.style.display = 'block';
        } else {
            errorsDiv.style.display = 'none';
        }
        
        // Zeige Warnungen
        if (issues.warnings && issues.warnings.length > 0) {
            warningsDiv.innerHTML = issues.warnings.map(warning => 
                `<div class="alert alert-warning">⚠️ ${warning}</div>`
            ).join('');
            warningsDiv.style.display = 'block';
        } else {
            warningsDiv.style.display = 'none';
        }
    }
    
    showRecommendations(recommendations) {
        const recDiv = document.getElementById('recommendations');
        
        if (recommendations && recommendations.length > 0) {
            recDiv.innerHTML = '<h5>💡 Empfehlungen:</h5>' + 
                recommendations.map(rec => `<li>${rec}</li>`).join('');
            recDiv.style.display = 'block';
        } else {
            recDiv.style.display = 'none';
        }
    }
    
    updateGitHubCompatibility(github) {
        const githubDiv = document.getElementById('github-compatibility');
        
        if (github) {
            const status = github.is_compatible ? '✅ Kompatibel' : '❌ Inkompatibel';
            githubDiv.innerHTML = `<strong>🐙 GitHub: ${status}</strong>`;
            
            if (github.warnings && github.warnings.length > 0) {
                githubDiv.innerHTML += '<br>' + github.warnings.map(w => 
                    `<small class="text-warning">⚠️ ${w}</small>`
                ).join('<br>');
            }
        }
    }
}

// Verwendung:
const validator = new GitHubUploadValidator('/api/security');

document.getElementById('file-input').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        const result = await validator.validateFile(file, 'web_upload', 'current_user');
        console.log('Validierungsergebnis:', result);
    }
});
"""

    return js_code


def main():
    """Hauptfunktion"""
    print("🌐 WEB-API INTEGRATION DEMO")
    print("Zeigt wie der Validator in Web-Interfaces integriert wird")
    print()

    choice = input(
        "Was möchten Sie sehen?\n1. API-Responses für verschiedene Szenarien\n2. Frontend JavaScript-Code\n3. Beides\nWahl [1-3]: "
    ).strip()

    if choice in ["1", "3"]:
        demo_web_api_responses()

    if choice in ["2", "3"]:
        print("💻 FRONTEND JAVASCRIPT-INTEGRATION")
        print("=" * 70)
        print(create_frontend_javascript())


if __name__ == "__main__":
    main()
