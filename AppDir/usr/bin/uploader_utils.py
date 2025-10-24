import os
import subprocess
import requests
import logging
import json
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_repo_and_push(
    github_token: str,
    github_user: str,
    repo_name: str,
    local_path: str,
    private=True,
    license_template=None,
    gitignore_template=None,
    auto_init=True,
) -> str:
    """
    Erstellt ein neues GitHub-Repository per REST-API und pusht ein lokales Projektverzeichnis.
    """
    # GitHub-API-Aufruf
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Stelle sicher, dass der Repository-Name gültig und eindeutig ist
    repo_name = generate_unique_repo_name(github_token, github_user, repo_name)

    data = {
        "name": repo_name,
        "private": private,
        "description": "Automatisch erstellt mit ZIP-Uploader",
    }

    # Optionale Parameter hinzufügen
    if license_template and license_template != "Keine":
        data["license_template"] = license_template
    if gitignore_template and gitignore_template != "Keine":
        data["gitignore_template"] = gitignore_template
    if auto_init:
        data["auto_init"] = True

    logger.info(f"Erstelle Repository: {repo_name}")
    response = requests.post(
        "https://api.github.com/user/repos", headers=headers, json=data
    )

    if response.status_code != 201:
        error_details = response.json()
        error_message = error_details.get("message", "Unbekannter Fehler")
        errors = error_details.get("errors", [])

        if errors:
            error_info = f"{error_message}. Details: {', '.join([err.get('message', str(err)) for err in errors])}"
        else:
            error_info = error_message

        logger.error(f"GitHub API-Fehler ({response.status_code}): {error_info}")
        raise RuntimeError(f"GitHub API-Fehler ({response.status_code}): {error_info}")

    repo_data = response.json()
    clone_url = repo_data["clone_url"]
    auth_url = clone_url.replace("https://", f"https://{github_token}@")

    logger.info(f"Repository erfolgreich erstellt: {clone_url}")

    # Git-Initialisierung
    if not os.path.isdir(local_path):
        raise RuntimeError(f"Lokaler Pfad existiert nicht: {local_path}")

    # Erstelle .gitignore, falls nicht vorhanden
    gitignore_path = os.path.join(local_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write("# Automatisch generierte .gitignore\n")
            f.write("node_modules/\n.DS_Store\n*.log\n")

    # Git-Befehle mit Fehlerbehandlung
    try:
        # Initialisiere Git Repository
        subprocess.run(["git", "init"], cwd=local_path, check=True)

        # Prüfe ob main Branch bereits existiert
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "main"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # main Branch existiert bereits, wechsle zu ihm
                subprocess.run(["git", "checkout", "main"], cwd=local_path, check=True)
            else:
                # main Branch existiert nicht, erstelle ihn
                subprocess.run(
                    ["git", "checkout", "-b", "main"], cwd=local_path, check=True
                )
        except subprocess.CalledProcessError:
            # Falls es Probleme gibt, erstelle den Branch trotzdem
            try:
                subprocess.run(
                    ["git", "checkout", "-b", "main"], cwd=local_path, check=False
                )
            except:
                # Als letzte Option, verwende den aktuellen Branch
                pass

        # Füge alle Dateien hinzu, ignoriere Fehler bei einzelnen Dateien
        try:
            subprocess.run(["git", "add", "-f", "."], cwd=local_path, check=True)
        except subprocess.CalledProcessError:
            # Versuche es mit einer alternativen Methode, wenn der erste Versuch fehlschlägt
            logger.warning(
                "Standardmethode zum Hinzufügen von Dateien fehlgeschlagen, versuche alternative Methode..."
            )
            # Füge Dateien einzeln hinzu
            for root, _, files in os.walk(local_path):
                for file in files:
                    if not file.startswith(".git"):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, local_path)
                        try:
                            subprocess.run(
                                ["git", "add", "-f", rel_path], cwd=local_path
                            )
                        except Exception as e:
                            logger.warning(
                                f"Konnte Datei nicht hinzufügen: {rel_path}, Fehler: {str(e)}"
                            )

        subprocess.run(
            ["git", "commit", "-m", "🚀 Automatischer Upload via Streamlit"],
            cwd=local_path,
            check=True,
        )

        # Prüfe ob remote bereits existiert
        try:
            subprocess.run(
                ["git", "remote", "remove", "origin"], cwd=local_path, check=False
            )
        except:
            pass

        subprocess.run(
            ["git", "remote", "add", "origin", auth_url], cwd=local_path, check=True
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"], cwd=local_path, check=True
        )
        logger.info(f"Git-Push erfolgreich abgeschlossen")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git-Fehler: {str(e)}")
        raise RuntimeError(f"Git-Fehler: {str(e)}")

    # Upload-Historie speichern
    save_upload_history(repo_name, clone_url)

    return clone_url


def save_upload_history(repo_name, repo_url):
    """Speichert Upload-Historie in einer JSON-Datei"""
    history_file = "upload_history.json"
    history = []

    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            logger.warning(
                f"Fehler beim Lesen der Upload-Historie, erstelle neue Datei"
            )

    history.append(
        {
            "repo_name": repo_name,
            "repo_url": repo_url,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
        }
    )

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"Upload-Historie aktualisiert: {repo_name}")


def generate_unique_repo_name(
    github_token: str, github_user: str, base_name: str
) -> str:
    """
    Generiert einen eindeutigen Repository-Namen, falls der gewünschte bereits existiert.
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Bereinige den Basis-Namen
    base_name = base_name.strip().replace(" ", "-").replace("_", "-")
    # Entferne ungültige Zeichen
    import re

    base_name = re.sub(r"[^a-zA-Z0-9-.]", "", base_name)

    # Prüfe ob der Name bereits existiert
    response = requests.get(
        f"https://api.github.com/repos/{github_user}/{base_name}", headers=headers
    )

    if response.status_code == 404:
        # Repository existiert nicht, wir können den Namen verwenden
        return base_name

    # Repository existiert bereits, generiere einen neuen Namen
    import random
    import string

    for i in range(1, 100):  # Versuche bis zu 99 Varianten
        suffix = f"-{i}"
        test_name = base_name + suffix

        response = requests.get(
            f"https://api.github.com/repos/{github_user}/{test_name}", headers=headers
        )
        if response.status_code == 404:
            return test_name

    # Falls alle nummerierten Varianten belegt sind, füge zufällige Zeichen hinzu
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{base_name}-{random_suffix}"
