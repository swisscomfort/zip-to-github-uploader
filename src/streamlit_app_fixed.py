import streamlit as st
import zipfile
import tempfile
import os
import sys
import requests
import time
import json
import subprocess
import re
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
from uploader_utils import create_repo_and_push
from dotenv import load_dotenv
from shared.generate_readme import generate_readme
from shared.gpt_analysis_github_copilot import analyze_project_with_github_copilot


def detect_security_issues(project_dir):
    """Prüft auf häufige Sicherheitsprobleme"""
    issues = []

    # Suche nach potenziellen Geheimnissen
    sensitive_patterns = [
        r"api[_-]key\s*=\s*['\"]\w+['\"]",
        r"password\s*=\s*['\"]\w+['\"]",
        r"secret\s*=\s*['\"]\w+['\"]",
        r"token\s*=\s*['\"]\w+['\"]",
    ]

    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith((".py", ".js", ".env", ".config")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        for pattern in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append(
                                    {
                                        "type": "security",
                                        "file": file,
                                        "message": "Mögliche hartcodierte Geheimnisse gefunden",
                                    }
                                )
                except Exception:
                    pass

    return issues


def analyze_code_quality(project_dir, project_type):
    """Analysiert die Codequalität"""
    results = {"issues": [], "metrics": {}}

    if project_type["type"] == "python":
        # Prüfe mit pylint
        try:
            cmd = f"cd {project_dir} && pylint --output-format=json *.py"
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if proc.returncode != 0:
                results["issues"].extend(json.loads(proc.stdout))
        except Exception:
            pass

        # Berechne Metriken
        try:
            import radon.complexity as cc

            for file in project_type["files"]:
                with open(os.path.join(project_dir, file), "r") as f:
                    code = f.read()
                    complexity = cc.cc_visit(code)
                    avg_complexity = (
                        sum(item.complexity for item in complexity) / len(complexity)
                        if complexity
                        else 0
                    )
                    results["metrics"][file] = {"complexity": avg_complexity}
        except Exception:
            pass

    elif project_type["type"] == "node":
        # Prüfe mit ESLint
        try:
            cmd = f"cd {project_dir} && npx eslint --format json *.js"
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if proc.returncode != 0:
                results["issues"].extend(json.loads(proc.stdout))
        except Exception:
            pass

    return results


def detect_project_type(project_dir):
    """Erkennt den Projekttyp und gibt Konfiguration zurück"""
    files = os.listdir(project_dir)

    # Python-Projekt
    if any(f.endswith(".py") for f in files):
        return {
            "type": "python",
            "files": [f for f in files if f.endswith(".py")],
            "config": ("requirements.txt" if "requirements.txt" in files else None),
            "test_cmd": (
                "python -m pytest"
                if any(f.startswith("test_") for f in files)
                else None
            ),
            "build_system": (
                "setuptools"
                if "setup.py" in files
                else ("poetry" if "pyproject.toml" in files else None)
            ),
        }

    # Node.js Projekt
    if "package.json" in files:
        return {
            "type": "node",
            "files": ["package.json"] + [f for f in files if f.endswith(".js")],
            "config": "package.json",
            "test_cmd": ("npm test" if any("test" in f for f in files) else None),
            "build_system": (
                "npm"
                if "package-lock.json" in files
                else ("yarn" if "yarn.lock" in files else None)
            ),
        }

    # Java Projekt
    if any(f.endswith(".java") for f in files):
        return {
            "type": "java",
            "files": [f for f in files if f.endswith(".java")],
            "config": (
                "pom.xml"
                if "pom.xml" in files
                else ("build.gradle" if "build.gradle" in files else None)
            ),
            "test_cmd": (
                "mvn test"
                if "pom.xml" in files
                else ("gradle test" if "build.gradle" in files else None)
            ),
            "build_system": (
                "maven"
                if "pom.xml" in files
                else ("gradle" if "build.gradle" in files else None)
            ),
        }

    # Go Projekt
    if any(f.endswith(".go") for f in files):
        return {
            "type": "go",
            "files": [f for f in files if f.endswith(".go")],
            "config": "go.mod" if "go.mod" in files else None,
            "test_cmd": "go test ./...",
            "build_system": "go",
        }

    # Rust Projekt
    if "Cargo.toml" in files:
        return {
            "type": "rust",
            "files": [f for f in files if f.endswith(".rs")],
            "config": "Cargo.toml",
            "test_cmd": "cargo test",
            "build_system": "cargo",
        }

    return None


def validate_project(project_dir, project_type):
    """Validiert ein Projekt und führt Tests aus"""
    results = {"valid": True, "messages": [], "test_results": None}

    if project_type["type"] == "python":
        # Prüfe Python-Abhängigkeiten
        if project_type["config"]:
            try:
                req_file = os.path.join(project_dir, "requirements.txt")
                with open(req_file, "r") as f:
                    requirements = f.read().splitlines()
                msg = f"✅ {len(requirements)} Python-Abhängigkeiten gefunden"
                results["messages"].append(msg)
            except Exception as e:
                results["messages"].append("⚠️ Fehler: requirements.txt")
                results["valid"] = False

        # Führe Python-Tests aus
        if project_type["test_cmd"]:
            try:
                cmd = f"cd {project_dir} && {project_type['test_cmd']}"
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                results["test_results"] = proc.stdout + proc.stderr

                if proc.returncode != 0:
                    results["valid"] = False
                    results["messages"].append("❌ Tests fehlgeschlagen")
                else:
                    results["messages"].append("✅ Tests erfolgreich")
            except Exception as e:
                msg = f"⚠️ Test-Fehler: {str(e)}"
                results["messages"].append(msg)
                results["valid"] = False

    elif project_type["type"] == "node":
        # Prüfe Node.js-Abhängigkeiten
        try:
            pkg_file = os.path.join(project_dir, "package.json")
            with open(pkg_file, "r") as f:
                package = json.load(f)
                deps = len(package.get("dependencies", {}))
                dev_deps = len(package.get("devDependencies", {}))
                total = deps + dev_deps
                msg = f"✅ {total} Node.js-Abhängigkeiten gefunden"
                results["messages"].append(msg)
        except Exception as e:
            results["messages"].append("⚠️ Fehler: package.json")
            results["valid"] = False

        # Führe Node.js-Tests aus
        if project_type["test_cmd"]:
            try:
                cmd = f"cd {project_dir} && {project_type['test_cmd']}"
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                results["test_results"] = proc.stdout + proc.stderr

                if (
                    "npm ERR!" in proc.stderr
                    or "FAIL" in proc.stderr
                    or proc.returncode != 0
                ):
                    results["valid"] = False
                    results["messages"].append("❌ Tests fehlgeschlagen")
                else:
                    results["messages"].append("✅ Tests erfolgreich")
            except Exception as e:
                msg = f"⚠️ Test-Fehler: {str(e)}"
                results["messages"].append(msg)
                results["valid"] = False

    return results


def analyze_git_error(error_message):
    """Analysiert Git-Fehlermeldungen und gibt Lösungsvorschläge zurück"""
    solutions = []
    error_str = str(error_message)

    if "fatal: remote origin already exists" in error_str:
        solutions.append(
            {
                "problem": "Das Remote-Repository 'origin' existiert bereits",
                "solution": "Repository zurücksetzen und neu initialisieren",
                "action": "git_reset",
            }
        )
    elif "Permission denied (publickey)" in error_str:
        solutions.append(
            {
                "problem": "SSH-Authentifizierungsfehler",
                "solution": "HTTPS-URL verwenden statt SSH",
                "action": "use_https",
            }
        )
    elif "fatal: Authentication failed" in error_str:
        solutions.append(
            {
                "problem": "GitHub Token Authentifizierungsfehler",
                "solution": "Token überprüfen (benötigt 'repo' Scope)",
                "action": "check_token",
            }
        )
    elif (
        "rejected] main -> main (fetch first)" in error_str
        or "non-zero exit status 1" in error_str
    ):
        solutions.append(
            {
                "problem": "Push wurde abgelehnt - Remote-Repository Konflikt",
                "solution": "Repository mit force-push synchronisieren",
                "action": "force_push",
            }
        )
    elif "git push" in error_str:
        solutions.append(
            {
                "problem": "Allgemeiner Git-Push Fehler",
                "solution": "Repository-Zustand zurücksetzen und neu versuchen",
                "action": "git_reset",
            }
        )

    return solutions


def validate_github_token(token):
    """Überprüft die Gültigkeit und Berechtigungen eines GitHub-Tokens"""
    if not token:
        return False, "Kein Token angegeben"

    headers = {"Authorization": f"token {token}"}
    try:
        # Überprüfe Token-Gültigkeit
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            return False, f"Token ungültig (Status: {response.status_code})"

        # Überprüfe Token-Berechtigungen
        scopes_response = requests.get(
            "https://api.github.com/rate_limit",
            headers=headers,
            timeout=10,
        )

        if "repo" not in scopes_response.headers.get("X-OAuth-Scopes", ""):
            return False, "Token benötigt 'repo' Berechtigung"

        return True, "Token gültig"

    except requests.exceptions.RequestException as e:
        return False, f"Verbindungsfehler: {str(e)}"


def check_rate_limits(token):
    """Überprüft GitHub API Rate Limits"""
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(
            "https://api.github.com/rate_limit",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            limits = response.json()
            core = limits["resources"]["core"]
            remaining = core["remaining"]
            reset_time = datetime.fromtimestamp(core["reset"])

            if remaining < 10:
                return (
                    False,
                    f"Rate Limit fast erreicht. Reset um {reset_time.strftime('%H:%M')}",
                )

        return True, f"Rate Limit OK ({remaining} verbleibend)"

    except Exception as e:
        return False, f"Fehler beim Prüfen der Rate Limits: {str(e)}"


def sanitize_repo_name(name):
    """Bereinigt und validiert Repository-Namen"""
    import re

    if not name:
        return False, "Kein Repository-Name angegeben"

    # Entferne unerlaubte Zeichen
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", name)

    # Prüfe Länge
    if len(sanitized) > 100:
        return False, "Repository-Name zu lang (max. 100 Zeichen)"

    # Prüfe auf gültige Zeichen am Anfang/Ende
    if not re.match(r"^[a-zA-Z0-9].*[a-zA-Z0-9]$", sanitized):
        return False, "Repository-Name muss mit Buchstaben/Zahlen beginnen und enden"

    return True, sanitized


# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env laden
load_dotenv()

# Voreinstellungen
default_token = os.getenv("GITHUB_TOKEN")
default_user = os.getenv("GITHUB_USERNAME")
default_copilot_key = os.getenv("GITHUB_COPILOT_TOKEN")

# Streamlit Konfiguration
st.set_page_config(page_title="ZIP → GitHub Uploader", layout="centered")

# Initialisiere Session State für Tipps wenn nicht vorhanden
if "tip_index" not in st.session_state:
    st.session_state.tip_index = 0

# Seitenleiste mit Navigation
st.sidebar.title("📦 ZIP to GitHub")
navigation = ["Einzelupload", "Batch-Upload", "Dashboard", "📚 Lern & Hilfe"]
page = st.sidebar.radio("Navigation", navigation)

# Hilfe-Button in der Sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("❓ Schnellhilfe"):
        st.info(
            """
        **Schnellstart:**
        1. Wähle deine ZIP-Datei
        2. Gib GitHub-Token ein
        3. Wähle Repository-Name
        4. Klicke auf Upload
        """
        )


def load_repositories(github_token, github_user):
    """Lädt Repositories über die GitHub API"""
    if not github_token or not github_user:
        st.warning("⚠️ Bitte gib GitHub-Token und Benutzername ein.")
        return None

    headers = {"Authorization": f"token {github_token}"}

    # Teste zuerst die Token-Gültigkeit
    try:
        auth_test = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )
        if auth_test.status_code != 200:
            st.error(f"❌ Token ungültig! Status: {auth_test.status_code}")
            return None

        auth_user = auth_test.json()
        st.success(f"✅ Token gültig für Benutzer: {auth_user['login']}")

        # Verwende die authentifizierte API um auch private Repos zu sehen
        response = requests.get(
            "https://api.github.com/user/repos?per_page=100&sort=updated",
            headers=headers,
            timeout=10,
        )

        st.write(f"**Debug Info:** Status Code: {response.status_code}")

        if response.status_code == 200:
            repos = response.json()
            st.success(f"✅ {len(repos)} Repositories gefunden")

            # Filter nur die Repos des gewünschten Users
            user_repos = [
                repo for repo in repos if repo["owner"]["login"] == github_user
            ]
            st.info(f"📊 Davon {len(user_repos)} Repositories von {github_user}")

            return user_repos
        else:
            st.error(f"❌ Fehler beim Laden: {response.status_code}")
            try:
                error_data = response.json()
                st.write(f"**Fehlerdetails:** {error_data.get('message', 'Unbekannt')}")
            except Exception:
                st.write(f"**Antworttext:** {response.text[:200]}...")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Netzwerkfehler: {e}")
        return None


if page == "Einzelupload":
    st.title("📦 ZIP to GitHub Repo – Upload & Deploy")

    # KI-Analyse Optionen
    with st.expander("🧠 KI-Analyse Optionen", expanded=True):
        st.markdown(
            """
        ### Verfügbare KI-Analysen:
        - 🔍 Code-Muster Erkennung
        - 📊 Abhängigkeitsanalyse
        - 📝 Automatische Dokumentation
        - 🏗️ Projektstrukturanalyse
        """
        )

        ai_code_patterns = st.checkbox("Code-Muster analysieren", value=True)
        ai_dependencies = st.checkbox("Abhängigkeiten prüfen", value=True)
        ai_documentation = st.checkbox("Dokumentation generieren", value=True)
        ai_structure = st.checkbox("Projektstruktur analysieren", value=True)

    # Sicherheitshinweise
    with st.expander("🔒 Sicherheitshinweise", expanded=True):
        st.markdown(
            """
        ### Wichtige Sicherheitshinweise:
        - Verwenden Sie einen GitHub Token mit minimalen Berechtigungen
        - Aktivieren Sie 2FA für Ihren GitHub-Account
        - Überprüfen Sie den Code vor dem Upload
        - Vermeiden Sie das Hochladen sensibler Daten
        """
        )

    # Eingabefelder mit Validierung
    github_token = st.text_input(
        "🔑 GitHub Token", type="password", value=default_token
    )
    if github_token:
        token_valid, token_msg = validate_github_token(github_token)
        if not token_valid:
            st.error(f"⚠️ {token_msg}")
        else:
            st.success("✅ Token gültig")

        # Zeige Rate Limit Status
        rate_ok, rate_msg = check_rate_limits(github_token)
        if not rate_ok:
            st.warning(f"⚠️ {rate_msg}")

    github_user = st.text_input("👤 GitHub Benutzername", value=default_user)

    # ZIP-Datei Upload zuerst, um automatischen Repository-Namen zu generieren
    uploaded_zip = st.file_uploader("Wähle eine ZIP-Datei", type="zip")

    # Zeige Beispiel für automatische Namensgenierung
    if not uploaded_zip:
        st.info(
            "💡 **Tipp:** Der Repository-Name wird automatisch aus dem ZIP-Dateinamen generiert!"
        )
        st.markdown(
            """
        **Beispiele:**
        - `mein-projekt.zip` → Repository: `mein-projekt`
        - `WebApp_v1.2.zip` → Repository: `webapp-v1-2`
        - `My Cool App.zip` → Repository: `my-cool-app`
        """
        )

    # Automatischer Repository-Name basierend auf ZIP-Datei
    auto_repo_name = ""
    if uploaded_zip:
        # Entferne Dateiendung und bereinige den Namen
        zip_filename = uploaded_zip.name
        auto_repo_name = os.path.splitext(zip_filename)[0]  # Entfernt .zip
        # Bereinige Zeichen
        auto_repo_name = re.sub(r"[^a-zA-Z0-9._-]", "-", auto_repo_name)
        # Kleinbuchstaben für Konsistenz
        auto_repo_name = auto_repo_name.lower()

        st.success(f"📁 ZIP-Datei geladen: `{zip_filename}`")
        st.info(f"🏷️ Automatisch generierter Repository-Name: `{auto_repo_name}`")

    repo_name = st.text_input(
        "📘 Name des neuen GitHub-Repos",
        value=auto_repo_name,
        help="Der Name wird automatisch aus dem ZIP-Dateinamen generiert",
    )

    if repo_name:
        name_valid, name_msg = sanitize_repo_name(repo_name)
        if not name_valid:
            st.error(f"⚠️ {name_msg}")
        elif name_msg != repo_name:
            st.warning(f"Repository-Name wurde bereinigt zu: {name_msg}")
            repo_name = name_msg

    # Repository-Einstellungen
    st.subheader("📋 Repository-Einstellungen")
    col1, col2 = st.columns(2)
    with col1:
        repo_private = st.checkbox("🔒 Privates Repository", value=True)
        auto_init = st.checkbox("📄 README automatisch erstellen", value=True)
    with col2:
        add_license = st.selectbox(
            "📜 Lizenz hinzufügen", ["Keine", "MIT", "Apache-2.0", "GPL-3.0"]
        )
        add_gitignore = st.selectbox(
            "🚫 .gitignore Template", ["Keine", "Python", "Node", "Java"]
        )

    run_ai = False
    if default_copilot_key:
        run_ai = st.checkbox("🧠 Projekt automatisch analysieren (GitHub Copilot)")
    else:
        st.warning("⚠ Kein GITHUB_COPILOT_TOKEN gefunden. Analyse-Funktion deaktiviert.")

    # Haupt-Workflow
    if uploaded_zip and github_token and repo_name and github_user:
        if st.button("🚀 Projekt hochladen und GitHub-Repo erstellen"):
            with st.spinner("Wird verarbeitet..."):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Repository erstellen und pushen
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # ZIP entpacken
                        status_text.text("📦 Entpacke ZIP-Datei...")
                        progress_bar.progress(0.2)

                        zip_path = os.path.join(tmpdir, "upload.zip")
                        with open(zip_path, "wb") as f:
                            f.write(uploaded_zip.read())

                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(tmpdir)

                        # Projektverzeichnis ermitteln
                        entries = os.listdir(tmpdir)
                        dirs = [
                            d
                            for d in entries
                            if os.path.isdir(os.path.join(tmpdir, d))
                            and d != "__MACOSX"
                        ]
                        project_dir = os.path.join(tmpdir, dirs[0]) if dirs else tmpdir

                        # README generieren
                        if auto_init:
                            status_text.text("📝 Generiere README...")
                            progress_bar.progress(0.4)
                            generated = generate_readme(os.listdir(project_dir))
                            with open(os.path.join(project_dir, "README.md"), "w") as f:
                                f.write(generated)

                        # Projekt validieren
                        status_text.text("🔍 Analysiere Projekt...")
                        progress_bar.progress(0.6)

                        project_type = detect_project_type(project_dir)
                        can_proceed = True

                        if project_type:
                            proj_type = project_type["type"].upper()
                            status_text.text(f"✨ {proj_type}-Projekt erkannt")

                            validation = validate_project(project_dir, project_type)

                            # Zeige Validierungsergebnisse
                            with st.expander("🔍 Analyse", expanded=True):
                                for msg in validation["messages"]:
                                    st.write(msg)
                                if validation["test_results"]:
                                    st.code(validation["test_results"])

                            if not validation["valid"]:
                                proceed = st.button("⚠️ Trotz Fehler fortfahren")
                                if proceed:
                                    st.warning("Upload trotz Warnungen")
                                else:
                                    st.error("❌ Bitte Probleme beheben")
                                    can_proceed = False
                        else:
                            st.info("ℹ️ Typ nicht erkannt - Skip Validierung")

                        if not can_proceed:
                            st.stop()

                        # Repository erstellen
                        status_text.text("🔗 Erstelle GitHub-Repository...")
                        progress_bar.progress(0.8)

                        repo_url = create_repo_and_push(
                            github_token,
                            github_user,
                            repo_name,
                            project_dir,
                            private=repo_private,
                            license_template=(
                                None if add_license == "Keine" else add_license
                            ),
                            gitignore_template=(
                                None if add_gitignore == "Keine" else add_gitignore
                            ),
                            auto_init=auto_init,
                        )

                        progress_bar.progress(0.9)

                        # AppImage Build Option
                        if project_type and project_type["type"] == "python":
                            status_text.text("🎁 Erstelle AppImage...")
                            if st.checkbox("AppImage erstellen"):
                                with st.spinner("Erstelle AppImage..."):
                                    app_name = repo_name.lower().replace(" ", "-")
                                    build_result = build_appimage(project_dir, app_name)

                                    if build_result["success"]:
                                        st.success(build_result["message"])

                                        # AppImage zu GitHub Release hochladen
                                        try:
                                            headers = {
                                                "Authorization": f"token {github_token}",
                                                "Accept": "application/vnd.github.v3+json",
                                            }

                                            # Erstelle Release
                                            release_data = {
                                                "tag_name": "v1.0.0",
                                                "name": f"{repo_name} v1.0.0",
                                                "body": "Erste AppImage Version",
                                                "draft": False,
                                                "prerelease": False,
                                            }

                                            release_url = f"https://api.github.com/repos/{github_user}/{repo_name}/releases"
                                            release_response = requests.post(
                                                release_url,
                                                headers=headers,
                                                json=release_data,
                                            )

                                            if release_response.status_code == 201:
                                                release_info = release_response.json()

                                                # Lade AppImage hoch
                                                with open(
                                                    build_result["appimage_path"], "rb"
                                                ) as f:
                                                    files = {"file": f}
                                                    upload_url = release_info[
                                                        "upload_url"
                                                    ].replace(
                                                        "{?name,label}",
                                                        f"?name={os.path.basename(build_result['appimage_path'])}",
                                                    )
                                                    upload_response = requests.post(
                                                        upload_url,
                                                        headers={
                                                            "Authorization": f"token {github_token}",
                                                            "Content-Type": "application/x-executable",
                                                        },
                                                        data=f.read(),
                                                    )

                                                    if (
                                                        upload_response.status_code
                                                        == 201
                                                    ):
                                                        st.success(
                                                            "✅ AppImage erfolgreich hochgeladen!"
                                                        )
                                                        download_url = (
                                                            upload_response.json()[
                                                                "browser_download_url"
                                                            ]
                                                        )
                                                        st.markdown(
                                                            f"### [AppImage herunterladen]({download_url})"
                                                        )
                                                    else:
                                                        st.error(
                                                            "❌ Fehler beim Hochladen des AppImage"
                                                        )
                                            else:
                                                st.error(
                                                    "❌ Fehler beim Erstellen des Release"
                                                )
                                        except Exception as e:
                                            st.error(f"❌ Fehler beim Upload: {str(e)}")
                                    else:
                                        st.error(f"❌ {build_result['message']}")

                        progress_bar.progress(1.0)
                        status_text.text("✅ Fertig!")
                        st.success("✅ Projekt erfolgreich hochgeladen!")
                        st.markdown(f"### [Repository auf GitHub öffnen]({repo_url})")

                except Exception as e:
                    st.error(f"❌ Fehler: {e}")
                    error_message = str(e)

                    # Git-Fehleranalyse - prüfe spezifisch auf Git-Probleme
                    if any(
                        keyword in error_message.lower()
                        for keyword in ["git", "push", "repository", "remote"]
                    ):
                        solutions = analyze_git_error(error_message)

                        if solutions:
                            st.warning("🔧 Mögliche Lösungen gefunden:")
                            for i, solution in enumerate(solutions):
                                st.info(f"**Problem:** {solution['problem']}")
                                st.info(f"**Lösung:** {solution['solution']}")

                                if solution["action"] == "git_reset":
                                    if st.button(
                                        f"🔄 Repository zurücksetzen #{i+1}",
                                        key=f"reset_{i}",
                                    ):
                                        with st.spinner(
                                            "Repository wird zurückgesetzt..."
                                        ):
                                            try:
                                                # Versuche erneut mit bereinigtem Repository
                                                repo_url = create_repo_and_push(
                                                    github_token,
                                                    github_user,
                                                    repo_name + "-fixed",  # Neuer Name
                                                    project_dir,
                                                    private=repo_private,
                                                    license_template=(
                                                        None
                                                        if add_license == "Keine"
                                                        else add_license
                                                    ),
                                                    gitignore_template=(
                                                        None
                                                        if add_gitignore == "Keine"
                                                        else add_gitignore
                                                    ),
                                                    auto_init=False,  # Kein auto_init um Konflikte zu vermeiden
                                                )
                                                st.success(
                                                    "✅ Repository erfolgreich erstellt!"
                                                )
                                                st.markdown(
                                                    f"### [Repository auf GitHub öffnen]({repo_url})"
                                                )
                                            except Exception as reset_error:
                                                st.error(
                                                    f"❌ Fehler beim Neuversuch: {reset_error}"
                                                )

                                elif solution["action"] == "force_push":
                                    st.warning(
                                        "⚠️ Das Force-Push Feature ist automatisch in der neuen Version integriert."
                                    )
                                    if st.button(
                                        f"🔄 Mit verbesserter Methode versuchen #{i+1}",
                                        key=f"improved_{i}",
                                    ):
                                        with st.spinner(
                                            "Verwende verbesserte Upload-Methode..."
                                        ):
                                            try:
                                                # Versuche mit auto_init=False
                                                repo_url = create_repo_and_push(
                                                    github_token,
                                                    github_user,
                                                    repo_name + "-v2",
                                                    project_dir,
                                                    private=repo_private,
                                                    license_template=(
                                                        None
                                                        if add_license == "Keine"
                                                        else add_license
                                                    ),
                                                    gitignore_template=(
                                                        None
                                                        if add_gitignore == "Keine"
                                                        else add_gitignore
                                                    ),
                                                    auto_init=False,  # Das ist der Trick!
                                                )
                                                st.success(
                                                    "✅ Upload mit verbesserter Methode erfolgreich!"
                                                )
                                                st.markdown(
                                                    f"### [Repository auf GitHub öffnen]({repo_url})"
                                                )
                                            except Exception as improved_error:
                                                st.error(
                                                    f"❌ Fehler bei verbesserter Methode: {improved_error}"
                                                )
                        else:
                            st.warning(
                                "❓ Keine automatische Lösung verfügbar. Mögliche Ursachen:"
                            )
                            st.markdown(
                                """
                            - **GitHub Token:** Überprüfen Sie die Berechtigung ('repo' Scope erforderlich)
                            - **Repository-Name:** Möglicherweise bereits verwendet oder ungültig
                            - **Netzwerk:** Verbindungsprobleme zu GitHub
                            - **Git-Konfiguration:** Lokale Git-Einstellungen
                            
                            **Lösungsvorschläge:**
                            1. Verwenden Sie einen anderen Repository-Namen
                            2. Überprüfen Sie Ihre Internet-Verbindung
                            3. Erneuern Sie Ihren GitHub Token
                            4. Versuchen Sie es in einigen Minuten erneut
                            """
                            )
                    else:
                        st.warning(
                            "❓ Allgemeiner Fehler - Bitte überprüfen Sie Ihre Eingaben und versuchen Sie es erneut."
                        )
    else:
        st.info("Bitte lade eine ZIP-Datei hoch und gib deine GitHub-Zugangsdaten ein.")

elif page == "Dashboard":
    st.title("📊 GitHub Uploader Dashboard")

    # GitHub-Zugangsdaten für Dashboard-Funktionen
    with st.expander("🔑 GitHub-Zugangsdaten", expanded=False):
        github_token = st.text_input(
            "🔑 GitHub Token",
            type="password",
            value=default_token,
            key="dashboard_token",
        )
        github_user = st.text_input(
            "👤 GitHub Benutzername", value=default_user, key="dashboard_user"
        )

    # Tabs für verschiedene Ansichten
    tab1, tab2 = st.tabs(["📈 Übersicht", "🔍 Repository-Liste"])

    with tab1:
        st.header("📈 Dashboard-Übersicht")

        # Upload-Historie laden
        history_file = "upload_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)

                # Statistiken berechnen
                total_repos = len(history)
                recent_repos = sum(
                    1
                    for item in history
                    if datetime.fromisoformat(item["timestamp"])
                    > datetime.now() - timedelta(days=7)
                )
                success_rate = (
                    (
                        sum(1 for item in history if item["status"] == "success")
                        / total_repos
                    )
                    if total_repos > 0
                    else 0
                )

                # Statistik-Karten
                col1, col2, col3 = st.columns(3)
                col1.metric("Gesamt-Repositories", total_repos)
                col2.metric("Letzte 7 Tage", recent_repos)
                col3.metric("Erfolgsrate", f"{success_rate:.1%}")

            except Exception as e:
                st.error(f"Fehler beim Laden der Upload-Historie: {e}")
        else:
            st.info(
                "Keine Upload-Historie gefunden. Erstelle zuerst einige Repositories."
            )

    with tab2:
        st.header("🔍 Repository-Liste")

        if st.button("🔄 Repositories laden"):
            repos = load_repositories(github_token, github_user)

            if repos:
                # Daten für Tabelle vorbereiten
                repo_data = []
                for repo in repos:
                    repo_data.append(
                        {
                            "Name": repo["name"],
                            "Beschreibung": repo["description"] or "",
                            "Erstellt am": repo["created_at"],
                            "Sprache": repo["language"] or "Unbekannt",
                            "Sichtbarkeit": (
                                "Privat" if repo["private"] else "Öffentlich"
                            ),
                            "URL": repo["html_url"],
                        }
                    )

                # Tabelle anzeigen
                if repo_data:
                    df = pd.DataFrame(repo_data)
                    st.dataframe(df)

                    # Sprachverteilung
                    st.subheader("Sprachverteilung")
                    if "Sprache" in df.columns and len(df) > 0:
                        lang_counts = df["Sprache"].value_counts()
                        if len(lang_counts) > 0:
                            st.bar_chart(lang_counts)
                        else:
                            st.info("Keine Sprachdaten verfügbar.")
                    else:
                        st.info("Keine Sprachdaten verfügbar.")
                else:
                    st.info("Keine Repository-Daten gefunden.")

elif page == "Batch-Upload":
    st.title("📦 Batch ZIP to GitHub Repo – Massenupload")

    with st.expander("ℹ️ Batch-Upload Hilfe"):
        st.markdown(
            """
        ### Batch-Upload erlaubt dir:
        - Mehrere ZIP-Dateien gleichzeitig hochzuladen
        - Gemeinsame Einstellungen für alle Repositories
        - Fortschrittsüberwachung für alle Uploads
        
        ### Tipps:
        - Nutze konsistente Namensgebung
        - Überprüfe die Einstellungen vor dem Upload
        - Behalte den Status im Auge
        """
        )

    # Gemeinsame Einstellungen
    st.subheader("🔧 Gemeinsame Einstellungen")
    col1, col2 = st.columns(2)
    with col1:
        batch_private = st.checkbox("🔒 Private Repositories", value=True)
        batch_auto_init = st.checkbox("📄 READMEs erstellen", value=True)
    with col2:
        batch_license = st.selectbox(
            "📜 Standard-Lizenz", ["Keine", "MIT", "Apache-2.0", "GPL-3.0"]
        )
        batch_gitignore = st.selectbox(
            "🚫 Standard .gitignore", ["Keine", "Python", "Node", "Java"]
        )

    # GitHub-Zugangsdaten
    st.subheader("🔑 GitHub-Zugangsdaten")
    batch_token = st.text_input("GitHub Token", type="password", value=default_token)
    batch_user = st.text_input("GitHub Benutzername", value=default_user)

    # ZIP-Datei Upload
    st.subheader("📁 Projekt-Dateien")
    uploaded_files = st.file_uploader(
        "Wähle ZIP-Dateien", type="zip", accept_multiple_files=True
    )

    if uploaded_files and batch_token and batch_user:
        # Projektliste anzeigen
        st.subheader("📋 Upload-Liste")
        projects = []
        for zip_file in uploaded_files:
            # Automatischer Repository-Name aus ZIP-Dateiname
            auto_name = os.path.splitext(zip_file.name)[0]  # Entfernt .zip
            auto_name = re.sub(r"[^a-zA-Z0-9._-]", "-", auto_name)  # Bereinigt
            auto_name = auto_name.lower()  # Kleinbuchstaben

            repo_name = st.text_input(
                f"Repository-Name für {zip_file.name}",
                value=auto_name,
                key=f"batch_repo_{zip_file.name}",
            )
            projects.append({"zip": zip_file, "name": repo_name})

        # Upload starten
        if st.button("🚀 Alle Projekte hochladen"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, project in enumerate(projects):
                status_text.text(
                    f"Verarbeite {project['name']} ({i+1}/{len(projects)})..."
                )

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # ZIP entpacken
                        zip_path = os.path.join(tmpdir, "upload.zip")
                        with open(zip_path, "wb") as f:
                            f.write(project["zip"].read())

                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(tmpdir)

                        # Projektverzeichnis ermitteln
                        entries = os.listdir(tmpdir)
                        dirs = [
                            d
                            for d in entries
                            if os.path.isdir(os.path.join(tmpdir, d))
                            and d != "__MACOSX"
                        ]
                        project_dir = os.path.join(tmpdir, dirs[0]) if dirs else tmpdir

                        # Repository erstellen und pushen
                        repo_url = create_repo_and_push(
                            batch_token,
                            batch_user,
                            project["name"],
                            project_dir,
                            private=batch_private,
                            license_template=(
                                None if batch_license == "Keine" else batch_license
                            ),
                            gitignore_template=(
                                None if batch_gitignore == "Keine" else batch_gitignore
                            ),
                            auto_init=batch_auto_init,
                        )

                        st.success(
                            f"✅ {project['name']} erfolgreich erstellt: [Öffnen]({repo_url})"
                        )

                except Exception as e:
                    st.error(f"❌ Fehler bei {project['name']}: {str(e)}")

                progress_bar.progress((i + 1) / len(projects))

            status_text.text("✅ Batch-Upload abgeschlossen!")
            progress_bar.progress(1.0)
    else:
        st.info("Bitte lade ZIP-Dateien hoch und gib deine GitHub-Zugangsdaten ein.")

elif page == "📚 Lern & Hilfe":
    show_learning_content()


def handle_git_error(
    error_message,
    project_dir,
    github_token,
    github_user,
    repo_name,
    repo_private,
    add_license,
    add_gitignore,
    auto_init,
):
    """Behandelt Git-Fehler und bietet Lösungsmöglichkeiten an"""
    solutions = analyze_git_error(error_message)

    if solutions:
        st.warning("🔧 Mögliche Lösungen gefunden:")
        for solution in solutions:
            st.info(f"Problem: {solution['problem']}")
            st.info(f"Lösung: {solution['solution']}")

            if solution["action"] == "git_reset":
                btn_text = "🔄 Repository zurücksetzen"
                if st.button(btn_text):
                    with st.spinner("Reset läuft..."):
                        try:
                            # Git-Repository neu initialisieren
                            cmd = f"cd {project_dir} && rm -rf .git"
                            cmd += " && git init"
                            os.system(cmd)

                            # Repository neu erstellen
                            repo_url = create_repo_and_push(
                                github_token,
                                github_user,
                                repo_name,
                                project_dir,
                                private=repo_private,
                                license_template=(
                                    None if add_license == "Keine" else add_license
                                ),
                                gitignore_template=(
                                    None if add_gitignore == "Keine" else add_gitignore
                                ),
                                auto_init=auto_init,
                            )
                            msg = "✅ Repository erfolgreich zurückgesetzt!"
                            st.success(msg)

                            link = "### [Repository auf GitHub öffnen]"
                            link += f"({repo_url})"
                            st.markdown(link)
                        except Exception as reset_error:
                            err = "❌ Fehler beim Reset: "
                            err += str(reset_error)
                            st.error(err)

            elif solution["action"] == "force_push":
                if st.button("⚠️ Force-Push"):
                    with st.spinner("Force-Push läuft..."):
                        try:
                            cmd = f"cd {project_dir}"
                            cmd += " && git push -f origin main"
                            os.system(cmd)
                            st.success("✅ Force-Push erfolgt!")
                        except Exception as force_error:
                            err = "❌ Force-Push Fehler: "
                            err += str(force_error)
                            st.error(err)
    else:
        msg = "❓ Keine automatische Lösung. Bitte überprüfen:"
        st.warning(msg)
        st.markdown(
            """
        - GitHub Token Berechtigungen
        - Repository-Name (Verfügbarkeit)
        - Netzwerkverbindung
        - GitHub API Status
        """
        )


def show_learning_content():
    """Zeigt Lerninhalte und Hilfe an"""
    st.title("📚 Lern & Hilfe")

    # Git & GitHub Grundlagen
    with st.expander("🌱 Git & GitHub Grundlagen", expanded=True):
        st.markdown(
            """
        ### Was ist Git?
        Git ist ein **Versionskontrollsystem**, das dir hilft:
        - Änderungen an deinem Code zu verfolgen
        - Mit anderen zusammenzuarbeiten
        - Frühere Versionen wiederherzustellen

        ### Was ist GitHub?
        GitHub ist eine **Online-Plattform**, die:
        - Deine Git-Repositories hostet
        - Zusammenarbeit ermöglicht
        - Issues, Pull Requests und mehr bietet
        """
        )

    # Repository-Einstellungen erklärt
    with st.expander("🔧 Repository-Einstellungen erklärt"):
        st.markdown(
            """
        ### Repository-Einstellungen
        1. **Privates Repository**:
           - Nur du und eingeladene Personen können es sehen
           - Gut für persönliche oder sensible Projekte

        2. **README automatisch erstellen**:
           - README.md ist die "Visitenkarte" deines Projekts
           - Beschreibt, was dein Projekt macht
           - Erklärt, wie man es nutzt

        3. **Lizenz**:
           - MIT: Sehr permissiv, erlaubt fast alles
           - Apache: Gut für größere Projekte
           - GPL: Erzwingt Open-Source

        4. **.gitignore**:
           - Verhindert, dass bestimmte Dateien hochgeladen werden
           - Wichtig für temporäre Dateien und Geheimnisse
        """
        )

    # Best Practices
    with st.expander("✨ Best Practices"):
        st.markdown(
            """
        ### Repository Best Practices

        1. **Gute README schreiben**
           - Projektbeschreibung
           - Installation & Nutzung
           - Beispiele

        2. **Saubere Struktur**
           - Logische Ordnerstruktur
           - Wichtige Dateien im Wurzelverzeichnis
           - Dokumentation in `docs/`

        3. **Sicherheit**
           - Keine Passwörter committen
           - .env Dateien in .gitignore
           - Sichere Abhängigkeiten
        """
        )

    # Häufige Probleme
    with st.expander("❓ Häufige Probleme & Lösungen"):
        st.markdown(
            """
        ### Typische Probleme

        1. **Push wird abgelehnt**
           - Repository existiert bereits
           - Keine Schreibrechte
           - Konflikte mit Remote

        2. **Authentifizierung schlägt fehl**
           - Token abgelaufen
           - Falsche Berechtigungen
           - Token nicht korrekt kopiert

        3. **Tests schlagen fehl**
           - Abhängigkeiten fehlen
           - Falsches Python/Node.js Version
           - Fehler im Code
        """
        )

    # Interaktive Tipps
    with st.expander("💡 Hilfreiche Tipps"):
        tip_index = st.session_state.get("tip_index", 0)
        tips = [
            "Committe regelmäßig kleine Änderungen statt selten große",
            "Nutze aussagekräftige Commit-Nachrichten",
            "Teste dein Projekt lokal bevor du pushst",
            "Halte deine Abhängigkeiten aktuell",
            "Dokumentiere während der Entwicklung",
            "Nutze Branches für neue Features",
            "Mache Backups wichtiger Daten",
            "Überprüfe die GitHub Actions Status",
        ]

        st.info(f"**Tipp des Tages:** {tips[tip_index]}")
        if st.button("🎲 Neuer Tipp"):
            st.session_state.tip_index = (tip_index + 1) % len(tips)
            st.experimental_rerun()


def build_appimage(project_dir, app_name):
    """Erstellt ein AppImage aus dem Projekt"""
    results = {"success": False, "message": "", "appimage_path": None}

    try:
        # Erstelle AppDir Struktur
        app_dir = os.path.join(project_dir, "AppDir")
        os.makedirs(app_dir, exist_ok=True)
        os.makedirs(os.path.join(app_dir, "usr/bin"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "usr/share/applications"), exist_ok=True)
        os.makedirs(
            os.path.join(app_dir, "usr/share/icons/hicolor/256x256/apps"), exist_ok=True
        )

        # Kopiere Projektdateien
        os.system(f"cp -r {project_dir}/* {app_dir}/usr/bin/")

        # Erstelle .desktop Datei
        desktop_file = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec=python3 usr/bin/main.py
Icon={app_name}
Categories=Development;
"""
        with open(os.path.join(app_dir, f"{app_name}.desktop"), "w") as f:
            f.write(desktop_file)

        # Kopiere .desktop Datei
        os.system(f"cp {app_dir}/{app_name}.desktop {app_dir}/usr/share/applications/")

        # Erstelle AppRun Datei
        apprun_content = """#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${HERE}/usr/sbin/:${HERE}/usr/games/:${HERE}/bin/:${HERE}/sbin/${PATH:+:$PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/:${HERE}/usr/lib/i386-linux-gnu/:${HERE}/usr/lib/x86_64-linux-gnu/:${HERE}/usr/lib32/:${HERE}/usr/lib64/:${HERE}/lib/:${HERE}/lib/i386-linux-gnu/:${HERE}/lib/x86_64-linux-gnu/:${HERE}/lib32/:${HERE}/lib64/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="${HERE}/usr/bin/${PYTHONPATH:+:$PYTHONPATH}"
export XDG_DATA_DIRS="${HERE}/usr/share/${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
EXEC=$(grep -e '^Exec=.*' "${HERE}"/*.desktop | head -n 1 | cut -d "=" -f 2 | cut -d " " -f 1)
exec "${EXEC}" "$@"
"""
        with open(os.path.join(app_dir, "AppRun"), "w") as f:
            f.write(apprun_content)
        os.system(f"chmod +x {app_dir}/AppRun")

        # Erstelle ein Standard-Icon wenn keins existiert
        if not os.path.exists(
            os.path.join(
                app_dir, "usr/share/icons/hicolor/256x256/apps", f"{app_name}.png"
            )
        ):
            # Hier könnte man ein Standard-Icon erstellen
            pass

        # Hole appimagetool wenn nicht vorhanden
        if not os.path.exists("./appimagetool-x86_64.AppImage"):
            os.system(
                "wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
            )
            os.system("chmod +x appimagetool-x86_64.AppImage")

        # Erstelle AppImage
        output_name = f"{app_name}-x86_64.AppImage"
        os.system(f"./appimagetool-x86_64.AppImage {app_dir} {output_name}")

        if os.path.exists(output_name):
            results["success"] = True
            results["message"] = "AppImage erfolgreich erstellt!"
            results["appimage_path"] = os.path.abspath(output_name)
        else:
            results["message"] = "Fehler beim Erstellen des AppImage"

    except Exception as e:
        results["message"] = f"Fehler: {str(e)}"

    return results


def analyze_code_patterns(project_dir):
    """Analysiert Codemuster und gibt Verbesserungsvorschläge"""
    patterns = {
        "hardcoded_config": r"(?:API_KEY|PASSWORD|SECRET)\s*=\s*['\"][^'\"]+['\"]",
        "large_functions": r"def\s+\w+\s*\([^)]*\):\s*(?:[^}]*?(?:\n\s*[^\n}]+){20,})",
        "complex_conditions": r"if\s+[^:]+(?:and|or)[^:]+(?:and|or)[^:]+:",
        "duplicate_code": r"(.{100,}?).*\1",
    }

    results = []

    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith((".py", ".js", ".java")):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()

                        for pattern_name, pattern in patterns.items():
                            matches = re.finditer(pattern, content, re.MULTILINE)
                            for match in matches:
                                results.append(
                                    {
                                        "file": file,
                                        "pattern": pattern_name,
                                        "line": content.count("\n", 0, match.start())
                                        + 1,
                                        "suggestion": get_improvement_suggestion(
                                            pattern_name
                                        ),
                                    }
                                )
                except Exception:
                    pass

    return results


def get_improvement_suggestion(pattern_name):
    """Gibt Verbesserungsvorschläge für erkannte Muster"""
    suggestions = {
        "hardcoded_config": "Verwende Umgebungsvariablen oder sichere Konfigurationsdateien",
        "large_functions": "Teile die Funktion in kleinere, wiederverwendbare Funktionen auf",
        "complex_conditions": "Vereinfache die Bedingungen oder nutze Hilfsfunktionen",
        "duplicate_code": "Erstelle eine gemeinsame Funktion für den wiederholten Code",
    }
    return suggestions.get(
        pattern_name, "Überprüfe den Code auf mögliche Verbesserungen"
    )


def analyze_dependencies(project_dir):
    """Analysiert Projektabhängigkeiten auf Sicherheit und Updates"""
    results = {"vulnerabilities": [], "outdated": [], "recommendations": []}

    try:
        if os.path.exists(os.path.join(project_dir, "requirements.txt")):
            # Python Projekt
            with open(os.path.join(project_dir, "requirements.txt"), "r") as f:
                requirements = f.read().splitlines()

            for req in requirements:
                # Prüfe auf bekannte Sicherheitslücken (simuliert)
                if "django<2.0" in req or "requests<2.20" in req:
                    results["vulnerabilities"].append(
                        {
                            "package": req,
                            "severity": "high",
                            "description": "Bekannte Sicherheitslücke",
                        }
                    )

                # Empfehlungen für bessere Alternativen
                if "urllib3" in req:
                    results["recommendations"].append(
                        {
                            "current": req,
                            "suggestion": "requests",
                            "reason": "Einfachere API und bessere Sicherheit",
                        }
                    )

        elif os.path.exists(os.path.join(project_dir, "package.json")):
            # Node.js Projekt
            with open(os.path.join(project_dir, "package.json"), "r") as f:
                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

            for pkg, version in dependencies.items():
                if version.startswith("^"):
                    results["recommendations"].append(
                        {
                            "package": pkg,
                            "current": version,
                            "suggestion": "Fixiere Version für bessere Reproduzierbarkeit",
                        }
                    )

    except Exception:
        pass

    return results


def generate_documentation(project_dir):
    """Generiert automatisch Dokumentation für das Projekt"""
    docs = {
        "overview": "",
        "setup": "",
        "api": [],
        "examples": [],
    }

    try:
        # Projektübersicht
        readme_path = os.path.join(project_dir, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                content = f.read()
                docs["overview"] = content

        # Setup-Anleitung
        setup_steps = []
        if os.path.exists(os.path.join(project_dir, "requirements.txt")):
            setup_steps.extend(
                [
                    "1. Python-Umgebung erstellen: `python -m venv venv`",
                    "2. Umgebung aktivieren: `source venv/bin/activate`",
                    "3. Abhängigkeiten installieren: `pip install -r requirements.txt`",
                ]
            )
        elif os.path.exists(os.path.join(project_dir, "package.json")):
            setup_steps.extend(
                [
                    "1. Node.js installieren",
                    "2. Abhängigkeiten installieren: `npm install`",
                    "3. Entwicklungsserver starten: `npm run dev`",
                ]
            )
        docs["setup"] = "\n".join(setup_steps)

        # API-Dokumentation aus Docstrings
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), "r") as f:
                            content = f.read()
                            # Suche nach Funktionsdefinitionen mit Docstrings
                            matches = re.finditer(
                                r'def\s+(\w+)\s*\([^)]*\):\s*"""([^"]*)"""', content
                            )
                            for match in matches:
                                docs["api"].append(
                                    {
                                        "function": match.group(1),
                                        "description": match.group(2).strip(),
                                    }
                                )
                    except Exception:
                        pass

        # Beispiele aus Testdateien
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), "r") as f:
                            content = f.read()
                            # Extrahiere Testfälle als Beispiele
                            matches = re.finditer(r"def\s+test_(\w+)", content)
                            for match in matches:
                                docs["examples"].append(
                                    {
                                        "name": match.group(1).replace("_", " "),
                                        "code": extract_test_code(
                                            content, match.start()
                                        ),
                                    }
                                )
                    except Exception:
                        pass

    except Exception:
        pass

    return docs


def extract_test_code(content, start_pos):
    """Extrahiert den relevanten Testcode"""
    # Finde Ende der Testfunktion
    lines = content[start_pos:].split("\n")
    test_code = []
    indent = None

    for line in lines:
        if indent is None and line.strip():
            indent = len(line) - len(line.lstrip())
            test_code.append(line.strip())
        elif indent is not None:
            if not line.strip() or line.startswith(" " * indent):
                test_code.append(line.strip())
            else:
                break

    return "\n".join(test_code)


def analyze_project_structure(project_dir):
    """Analysiert die Projektstruktur und gibt Empfehlungen"""
    results = {
        "structure": [],
        "recommendations": [],
        "best_practices": [],
    }

    try:
        # Analysiere Verzeichnisstruktur
        for root, dirs, files in os.walk(project_dir):
            rel_path = os.path.relpath(root, project_dir)
            if rel_path == ".":
                # Hauptverzeichnis
                if not any(d in dirs for d in ["src", "tests", "docs"]):
                    results["recommendations"].append(
                        "Erwäge die Standardordner 'src', 'tests' und 'docs' anzulegen"
                    )

            # Prüfe auf versteckte Dateien
            hidden_files = [
                f
                for f in files
                if f.startswith(".") and f not in [".gitignore", ".env.example"]
            ]
            if hidden_files:
                results["recommendations"].append(
                    f"Überprüfe versteckte Dateien in {rel_path}: {', '.join(hidden_files)}"
                )

        # Prüfe Best Practices
        common_files = {
            "README.md": "Projektdokumentation",
            ".gitignore": "Git-Ignore Datei",
            "requirements.txt": "Python Abhängigkeiten",
            "setup.py": "Python Paket-Setup",
            "package.json": "Node.js Paket-Info",
            "Dockerfile": "Container-Definition",
            "LICENSE": "Lizenzinformation",
        }

        for file, description in common_files.items():
            if not os.path.exists(os.path.join(project_dir, file)):
                results["best_practices"].append(
                    f"Erwäge das Hinzufügen einer {file} Datei für {description}"
                )

        # Spezielle Projekttyp-Empfehlungen
        if os.path.exists(os.path.join(project_dir, "requirements.txt")):
            results["best_practices"].extend(
                [
                    "Nutze virtual environments für Python-Projekte",
                    "Erwäge die Verwendung von pytest für Tests",
                    "Füge type hints zu Python-Funktionen hinzu",
                ]
            )

        elif os.path.exists(os.path.join(project_dir, "package.json")):
            results["best_practices"].extend(
                [
                    "Nutze ESLint für JavaScript/TypeScript",
                    "Konfiguriere Prettier für Codeformatierung",
                    "Erwäge Jest für Tests",
                ]
            )

    except Exception as e:
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    # Starte die Streamlit-App mit:
    # Linux/Mac: streamlit run streamlit_app_fixed.py
    # Windows:   python -m streamlit run streamlit_app_fixed.py
    pass
