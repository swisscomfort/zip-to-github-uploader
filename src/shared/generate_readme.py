def generate_readme(file_list):
    """
    Generiert eine README.md basierend auf den Dateien im Projekt.
    Erkennt automatisch Projekttypen und erstellt eine passende Struktur.
    """
    # Projekttyp erkennen
    project_type = "Unbekannt"
    languages = []
    
    if any(f.endswith(".py") for f in file_list):
        languages.append("Python")
    if any(f.endswith(".js") or f.endswith(".jsx") for f in file_list):
        languages.append("JavaScript")
    if any(f.endswith(".html") for f in file_list):
        languages.append("HTML")
    if any(f.endswith(".css") for f in file_list):
        languages.append("CSS")
    if any(f.endswith(".java") for f in file_list):
        languages.append("Java")
    if any(f.endswith(".php") for f in file_list):
        languages.append("PHP")
    
    # Frameworks erkennen
    frameworks = []
    if "package.json" in file_list:
        frameworks.append("Node.js")
    if "requirements.txt" in file_list:
        frameworks.append("Python-Paket")
    if "manage.py" in file_list and any("django" in f.lower() for f in file_list):
        frameworks.append("Django")
    if "app.py" in file_list and any("flask" in f.lower() for f in file_list):
        frameworks.append("Flask")
    if "pom.xml" in file_list:
        frameworks.append("Maven")
    if "build.gradle" in file_list:
        frameworks.append("Gradle")
    if "composer.json" in file_list:
        frameworks.append("PHP/Composer")
    
    # Projekttyp bestimmen
    if "index.html" in file_list and "style.css" in file_list:
        project_type = "Webseite"
    elif "package.json" in file_list and "react" in str(file_list).lower():
        project_type = "React-Anwendung"
    elif "package.json" in file_list and "vue" in str(file_list).lower():
        project_type = "Vue.js-Anwendung"
    elif "package.json" in file_list and "angular" in str(file_list).lower():
        project_type = "Angular-Anwendung"
    elif "requirements.txt" in file_list and "flask" in str(file_list).lower():
        project_type = "Flask-Anwendung"
    elif "requirements.txt" in file_list and "django" in str(file_list).lower():
        project_type = "Django-Anwendung"
    elif "docker-compose.yml" in file_list or "Dockerfile" in file_list:
        project_type = "Docker-Projekt"
    elif len(languages) > 0:
        project_type = f"{', '.join(languages)}-Projekt"
    
    # README erstellen
    lines = [f"# {project_type}"]
    
    # Beschreibung
    lines.append("\n## Beschreibung")
    lines.append("Dieses Projekt wurde automatisch mit dem ZIP-to-GitHub Uploader erstellt.")
    
    if frameworks:
        lines.append(f"\nDieses Projekt verwendet: {', '.join(frameworks)}")
    
    # Dateien auflisten
    lines.append("\n## Projektstruktur")
    lines.append("```")
    
    # Zeige maximal 20 Dateien
    for f in sorted(file_list)[:20]:
        lines.append(f"- {f}")
    
    if len(file_list) > 20:
        lines.append(f"... und {len(file_list) - 20} weitere Dateien")
    
    lines.append("```")
    
    # Installation
    if "requirements.txt" in file_list:
        lines.append("\n## Installation")
        lines.append("```bash")
        lines.append("pip install -r requirements.txt")
        lines.append("```")
    elif "package.json" in file_list:
        lines.append("\n## Installation")
        lines.append("```bash")
        lines.append("npm install")
        lines.append("```")
    
    # Ausführung
    if "package.json" in file_list:
        lines.append("\n## Ausführung")
        lines.append("```bash")
        lines.append("npm start")
        lines.append("```")
    elif any(f.endswith(".py") for f in file_list):
        main_file = next((f for f in file_list if f == "app.py" or f == "main.py"), None)
        if main_file:
            lines.append("\n## Ausführung")
            lines.append("```bash")
            lines.append(f"python {main_file}")
            lines.append("```")
    
    return "\n".join(lines)
