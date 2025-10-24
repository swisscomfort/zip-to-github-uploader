import streamlit as st
import zipfile
import tempfile
import os
import sys
import requests
import time
import json
from datetime import datetime, timedelta
import pandas as pd
import altair as alt

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uploader_utils import create_repo_and_push
from dotenv import load_dotenv
from shared.generate_readme import generate_readme
from shared.gpt_analysis_github_copilot import analyze_project_with_github_copilot

# .env laden
load_dotenv()

# Voreinstellungen
default_token = os.getenv("GITHUB_TOKEN")
default_user = os.getenv("GITHUB_USERNAME")
default_copilot_key = os.getenv("GITHUB_COPILOT_TOKEN")

# Streamlit Konfiguration
st.set_page_config(page_title="ZIP → GitHub Uploader", layout="centered")

# Seitenleiste mit Navigation
st.sidebar.title("📦 ZIP to GitHub")
page = st.sidebar.radio("Navigation", ["Einzelupload", "Batch-Upload", "Dashboard"])


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

    with st.expander("ℹ Hilfe anzeigen"):
        st.markdown(
            """
        Dieses Tool erlaubt dir:
        - Eine ZIP-Datei hochzuladen (z. B. ein exportiertes Projekt)
        - Automatisch ein GitHub-Repository zu erstellen (privat)
        - Die Projektdateien dorthin zu pushen (inkl. README, Code etc.)
        - Optional: Projektbeschreibung & Tags mit KI (OpenRouter)
        """
        )

    # Eingabefelder
    github_token = st.text_input(
        "🔑 GitHub Token", type="password", value=default_token
    )
    github_user = st.text_input("👤 GitHub Benutzername", value=default_user)
    repo_name = st.text_input("📘 Name des neuen GitHub-Repos")

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

    uploaded_zip = st.file_uploader("Wähle eine ZIP-Datei", type="zip")

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

                        # Repository erstellen
                        status_text.text("🔗 Erstelle GitHub-Repository...")
                        progress_bar.progress(0.7)

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

                        progress_bar.progress(1.0)
                        status_text.text("✅ Fertig!")
                        st.success("✅ Projekt erfolgreich hochgeladen!")
                        st.markdown(f"### [Repository auf GitHub öffnen]({repo_url})")

                except Exception as e:
                    st.error(f"❌ Fehler: {e}")
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
    st.info("Batch-Upload Funktion wird bald verfügbar sein.")
