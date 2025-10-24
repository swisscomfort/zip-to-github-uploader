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

if page == "Einzelupload":
    st.title("📦 ZIP to GitHub Repo – Upload & Deploy")

    with st.expander("ℹ Hilfe anzeigen"):
        st.markdown(
            """
        Dieses Tool erlaubt dir:

        - Eine ZIP-Datei hochzuladen (z. B. ein exportiertes Projekt)
        - Automatisch ein GitHub-Repository zu erstellen (privat)
        - Die Projektdateien dorthin zu pushen (inkl. README, Code etc.)
        - Optional: Projektbeschreibung & Tags mit KI (GitHub Copilot)

        Voraussetzungen:
        - Ein GitHub-Token mit `repo`-Rechten ([Token erstellen](https://github.com/settings/tokens))
        - Dein GitHub-Benutzername
        - Optional: `.env` mit `GITHUB_TOKEN`, `GITHUB_USERNAME`, `GITHUB_COPILOT_TOKEN`

        Ergebnis:
        - Ein vollwertiges Repository unter deinem Account
        - Bei Analyse-Aktivierung: Beschreibung & Tags via KI
        """
        )

    # Eingabefelder
    github_token = st.text_input(
        "🔑 GitHub Token", type="password", value=default_token
    )
    github_user = st.text_input("👤 GitHub Benutzername", value=default_user)
    repo_name = st.text_input(
        "📘 Name des neuen GitHub-Repos",
        help="Der Name des zu erstellenden Repositories auf GitHub",
    )

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
        # ZIP-Vorschau
        with st.expander("🔍 ZIP-Inhalt Vorschau"):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "upload.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.read())

                # ZIP zurücksetzen für späteren Gebrauch
                uploaded_zip.seek(0)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    file_list = zip_ref.namelist()

                    # Zeige die ersten 20 Dateien
                    st.write(f"ZIP enthält {len(file_list)} Dateien:")
                    for file in file_list[:20]:
                        st.write(f"- {file}")

                    if len(file_list) > 20:
                        st.write(f"... und {len(file_list) - 20} weitere Dateien")

        if st.button("🚀 Projekt hochladen und GitHub-Repo erstellen"):
            with st.spinner("Wird verarbeitet..."):
                try:
                    # Fortschrittsanzeige
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Schritt 1: ZIP entpacken
                    status_text.text("📦 Entpacke ZIP-Datei...")
                    progress_bar.progress(0.1)
                    time.sleep(0.5)

                    with tempfile.TemporaryDirectory() as tmpdir:
                        # ZIP speichern und entpacken
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

                        # Schritt 2: README-Generierung
                        status_text.text("📝 Generiere README...")
                        progress_bar.progress(0.3)
                        time.sleep(0.5)

                        readme_exists = "README.md" in os.listdir(project_dir)
                        if readme_exists:
                            readme_option = st.radio(
                                "Im ZIP ist bereits eine README.md enthalten. Was tun?",
                                (
                                    "Beibehalten",
                                    "Überschreiben",
                                    "Neue Datei erstellen (README_auto.md)",
                                ),
                            )
                        else:
                            readme_option = "Überschreiben"

                        generated = generate_readme(os.listdir(project_dir))
                        if readme_option == "Überschreiben":
                            with open(os.path.join(project_dir, "README.md"), "w") as f:
                                f.write(generated)
                        elif readme_option.startswith("Neue Datei"):
                            with open(
                                os.path.join(project_dir, "README_auto.md"), "w"
                            ) as f:
                                f.write(generated)

                        # Schritt 3: KI-Analyse
                        if run_ai:
                            status_text.text("🧠 Führe KI-Analyse durch...")
                            progress_bar.progress(0.5)
                            try:
                                prompt = f"Bitte beschreibe dieses Projekt und gib passende Tags an:\n{generated}"
                                result = analyze_project_with_github_copilot(prompt)

                                # Speichere KI-Analyse
                                with open(
                                    os.path.join(project_dir, "README_KI.md"), "w"
                                ) as f:
                                    f.write(result)

                                st.text_area(
                                    "💡 KI-Beschreibung & Tags", result, height=200
                                )
                            except Exception as ai_error:
                                st.error(f"❌ Analyse-Fehler: {ai_error}")

                        # Schritt 4: Repository erstellen
                        status_text.text("🔗 Erstelle GitHub-Repository...")
                        progress_bar.progress(0.7)

                        try:
                            # Repository erstellen und pushen
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

                            # Schritt 5: Abschluss
                            progress_bar.progress(1.0)
                            status_text.text("✅ Fertig!")

                            # Erfolgsanzeige
                            st.success(f"✅ Projekt erfolgreich hochgeladen!")
                            st.markdown(
                                f"### [Repository auf GitHub öffnen]({repo_url})"
                            )

                            # Teste ob das Repo wirklich existiert
                            test_response = requests.get(
                                f"https://api.github.com/repos/{github_user}/{repo_name}",
                                headers={"Authorization": f"token {github_token}"},
                            )
                            if test_response.status_code == 200:
                                repo_data = test_response.json()
                                st.write(f"**Repository-Name:** {repo_data['name']}")
                                st.write(
                                    f"**Sichtbarkeit:** {'Privat' if repo_data['private'] else 'Öffentlich'}"
                                )
                                st.write(f"**Erstellt am:** {repo_data['created_at']}")

                        except Exception as repo_error:
                            st.error(f"❌ Fehler beim Repository-Upload: {repo_error}")
                            st.info("💡 Mögliche Lösungen:")
                            st.write("- Prüfe GitHub-Token und Berechtigung")
                            st.write("- Verwende einen anderen Repository-Namen")
                            st.write(
                                "- Der Name wird automatisch angepasst falls er bereits existiert"
                            )

                except Exception as e:
                    st.error(f"❌ Fehler: {e}")
                    st.info("💡 Mögliche Lösungen:")
                    st.write("- Prüfe GitHub-Token und Berechtigung")
                    st.write("- Verwende einen anderen Repository-Namen")
                    st.write("- Stelle sicher, dass der Name noch nicht existiert")
    else:
        st.info("Bitte lade eine ZIP-Datei hoch und gib deine GitHub-Zugangsdaten ein.")

elif page == "Batch-Upload":
    # Batch-Upload-Seite
    st.title("📦 Batch ZIP to GitHub Repo – Massenupload")

    # Eingabefelder
    github_token = st.text_input(
        "🔑 GitHub Token", type="password", value=default_token
    )
    github_user = st.text_input("👤 GitHub Benutzername", value=default_user)

    # Repository-Einstellungen
    st.subheader("📋 Repository-Einstellungen")
    col1, col2 = st.columns(2)
    with col1:
        repo_private = st.checkbox("🔒 Private Repositories", value=True)
        auto_init = st.checkbox("📄 README automatisch erstellen", value=True)
    with col2:
        add_license = st.selectbox(
            "📜 Lizenz hinzufügen", ["Keine", "MIT", "Apache-2.0", "GPL-3.0"]
        )
        add_gitignore = st.selectbox(
            "🚫 .gitignore Template", ["Keine", "Python", "Node", "Java"]
        )

    # Batch-Upload
    uploaded_files = st.file_uploader(
        "Mehrere ZIP-Dateien auswählen", type="zip", accept_multiple_files=True
    )

    if uploaded_files and github_token and github_user:
        # Vorschau der zu erstellenden Repositories
        st.subheader("🔍 Repository-Vorschau")

        preview_data = []
        for i, file in enumerate(uploaded_files):
            repo_name = file.name.replace(".zip", "").replace(" ", "-")
            preview_data.append(
                {
                    "Nr.": i + 1,
                    "ZIP-Datei": file.name,
                    "Repository-Name": repo_name,
                    "Status": "Ausstehend",
                }
            )

        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df)

        if st.button("🚀 Alle Projekte hochladen"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []

            for i, file in enumerate(uploaded_files):
                repo_name = file.name.replace(".zip", "").replace(" ", "-")
                status_text.text(
                    f"Verarbeite {file.name} ({i+1}/{len(uploaded_files)})..."
                )

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # ZIP speichern und entpacken
                        zip_path = os.path.join(tmpdir, file.name)
                        with open(zip_path, "wb") as f:
                            f.write(file.read())

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
                            generated = generate_readme(os.listdir(project_dir))
                            with open(os.path.join(project_dir, "README.md"), "w") as f:
                                f.write(generated)

                        # Repository erstellen und pushen
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
                        )

                        results.append(
                            {
                                "Nr.": i + 1,
                                "ZIP-Datei": file.name,
                                "Repository-Name": repo_name,
                                "Repository-URL": repo_url,
                                "Status": "Erfolgreich",
                                "Zeitstempel": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        )

                except Exception as e:
                    results.append(
                        {
                            "Nr.": i + 1,
                            "ZIP-Datei": file.name,
                            "Repository-Name": repo_name,
                            "Repository-URL": "",
                            "Status": f"Fehler: {str(e)}",
                            "Zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                # Fortschritt aktualisieren
                progress_bar.progress((i + 1) / len(uploaded_files))

            # Ergebnisse anzeigen
            status_text.text("✅ Alle Uploads abgeschlossen!")
            results_df = pd.DataFrame(results)
            st.subheader("📊 Upload-Ergebnisse")
            st.dataframe(results_df)

            # CSV-Export
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Ergebnisse als CSV herunterladen",
                data=csv,
                file_name=f"batch_upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    else:
        st.info("Bitte lade ZIP-Dateien hoch und gib deine GitHub-Zugangsdaten ein.")

elif page == "Dashboard":
    # Dashboard-Seite
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
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Übersicht", "🔍 Repository-Liste", "📜 Upload-Historie", "⚙️ Verwaltung"]
    )

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
                    sum(1 for item in history if item["status"] == "success")
                    / total_repos
                    if total_repos > 0
                    else 0
                )

                # Statistik-Karten
                col1, col2, col3 = st.columns(3)
                col1.metric("Gesamt-Repositories", total_repos)
                col2.metric("Letzte 7 Tage", recent_repos)
                col3.metric("Erfolgsrate", f"{success_rate:.1%}")

                # Zeitverlauf-Diagramm
                st.subheader("Repository-Erstellungen im Zeitverlauf")

                # Daten für Chart vorbereiten
                df = pd.DataFrame(history)
                df["date"] = pd.to_datetime(df["timestamp"]).dt.date
                daily_counts = df.groupby("date").size().reset_index(name="count")

                # Altair Chart
                chart = (
                    alt.Chart(daily_counts)
                    .mark_line(point=True)
                    .encode(x="date:T", y="count:Q", tooltip=["date:T", "count:Q"])
                    .properties(height=300)
                )

                st.altair_chart(chart, use_container_width=True)

            except Exception as e:
                st.error(f"Fehler beim Laden der Upload-Historie: {e}")
        else:
            st.info(
                "Keine Upload-Historie gefunden. Erstelle zuerst einige Repositories."
            )

    with tab2:
        st.header("🔍 Repository-Liste")
        
        # Token-Validierung
        if not github_token or not github_user:
            st.warning("⚠️ Bitte gib GitHub-Token und Benutzername ein.")
        else:
            if st.button("🔄 Repositories laden"):
                with st.spinner("Lade Repositories..."):
                    headers = {"Authorization": f"token {github_token}"}
                    
                    # Teste zuerst die Token-Gültigkeit
                    auth_test = requests.get("https://api.github.com/user", headers=headers)
                    if auth_test.status_code != 200:
                        st.error(f"❌ Token ungültig! Status: {auth_test.status_code}")
                    else:
                        auth_user = auth_test.json()
                        st.success(f"✅ Token gültig für Benutzer: {auth_user['login']}")
                        
                        # Verwende die authentifizierte API um auch private Repos zu sehen
                        response = requests.get(
                            "https://api.github.com/user/repos?per_page=100&sort=updated",
                            headers=headers,
                        )
                        
                        st.write(f"**Debug Info:** Status Code: {response.status_code}")
                        
                        if response.status_code == 200:
                            repos = response.json()
                            st.success(f"✅ {len(repos)} Repositories gefunden")
                            
                            # Filter nur die Repos des gewünschten Users (falls Token Zugriff auf andere Orgs hat)
                            user_repos = [repo for repo in repos if repo["owner"]["login"] == github_user]
                            st.info(f"📊 Davon {len(user_repos)} Repositories von {github_user}")

                    # Daten für Tabelle vorbereiten (verwende gefilterte user_repos)
                    repo_data = []
                    for repo in user_repos:
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

                        # Sprachverteilung nur anzeigen wenn Daten vorhanden
                        st.subheader("Sprachverteilung")
                        try:
                            if "Sprache" in df.columns and len(df) > 0:
                                lang_counts = df["Sprache"].value_counts()
                                if len(lang_counts) > 0:
                                    st.bar_chart(lang_counts)
                                else:
                                    st.info("Keine Sprachdaten verfügbar.")
                            else:
                                st.info("Keine Sprachdaten verfügbar.")
                        except Exception as e:
                            st.warning(f"Fehler bei der Sprachverteilung: {e}")
                            st.info("Sprachverteilung konnte nicht angezeigt werden.")
                    else:
                        st.info("Keine Repository-Daten gefunden.")

                else:
                    st.error(f"❌ Fehler beim Laden der Repositories: {response.status_code}")
                    
                    # Zeige detaillierte Fehlerinformationen
                    try:
                        error_data = response.json()
                        st.write(f"**Fehlerdetails:** {error_data.get('message', 'Unbekannter Fehler')}")
                    except:
                        st.write(f"**Antworttext:** {response.text[:200]}...")
                    
                    st.info("💡 Mögliche Lösungen:")
                    st.write("- Prüfe ob das GitHub-Token gültig ist")
                    st.write("- Stelle sicher, dass das Token 'repo' Berechtigung hat")
                    st.write("- Prüfe ob der Benutzername korrekt ist")

    with tab3:
        st.header("📜 Upload-Historie")

        # Upload-Historie laden
        history_file = "upload_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)

                # Daten für Tabelle vorbereiten
                df = pd.DataFrame(history)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp", ascending=False)

                # Tabelle anzeigen
                st.dataframe(df)

                # CSV-Export
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Historie als CSV herunterladen",
                    data=csv,
                    file_name=f"upload_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"Fehler beim Laden der Upload-Historie: {e}")
        else:
            st.info(
                "Keine Upload-Historie gefunden. Erstelle zuerst einige Repositories."
            )

    with tab4:
        st.header("⚙️ Repository-Verwaltung")

        # Repository auswählen
        repo_name = st.text_input("Repository-Name zum Verwalten")

        if repo_name and st.button("🔍 Repository-Details laden"):
            headers = {"Authorization": f"token {github_token}"}
            response = requests.get(
                f"https://api.github.com/repos/{github_user}/{repo_name}",
                headers=headers,
            )

            if response.status_code == 200:
                repo = response.json()

                st.subheader(f"Details für {repo['name']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Beschreibung:** {repo['description'] or 'Keine'}")
                    st.write(f"**Erstellt am:** {repo['created_at']}")
                    st.write(f"**Sprache:** {repo['language'] or 'Unbekannt'}")
                    st.write(
                        f"**Sichtbarkeit:** {'Privat' if repo['private'] else 'Öffentlich'}"
                    )

                with col2:
                    st.write(f"**URL:** {repo['html_url']}")
                    st.write(f"**Forks:** {repo['forks_count']}")
                    st.write(f"**Stars:** {repo['stargazers_count']}")
                    st.write(f"**Offene Issues:** {repo['open_issues_count']}")

                # Repository-Aktionen
                st.subheader("Aktionen")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Sichtbarkeit ändern"):
                        new_private = not repo["private"]
                        update_response = requests.patch(
                            f"https://api.github.com/repos/{github_user}/{repo_name}",
                            headers=headers,
                            json={"private": new_private},
                        )

                        if update_response.status_code == 200:
                            st.success(
                                f"Sichtbarkeit geändert zu: {'Privat' if new_private else 'Öffentlich'}"
                            )
                        else:
                            st.error(
                                f"Fehler beim Ändern der Sichtbarkeit: {update_response.status_code}"
                            )

                with col2:
                    if st.button(
                        "🗑️ Repository löschen",
                        help="Achtung: Diese Aktion kann nicht rückgängig gemacht werden!",
                    ):
                        confirm = st.text_input(
                            "Zum Bestätigen Repository-Namen eingeben"
                        )

                        if confirm == repo_name:
                            delete_response = requests.delete(
                                f"https://api.github.com/repos/{github_user}/{repo_name}",
                                headers=headers,
                            )

                            if delete_response.status_code == 204:
                                st.success(
                                    f"Repository {repo_name} erfolgreich gelöscht!"
                                )
                            else:
                                st.error(
                                    f"Fehler beim Löschen des Repositories: {delete_response.status_code}"
                                )
            else:
                st.error(f"Repository nicht gefunden: {response.status_code}")
