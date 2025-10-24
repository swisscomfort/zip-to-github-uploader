import streamlit as st
import zipfile
import tempfile
import os
import sys
import time
import pandas as pd
from datetime import datetime

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
st.set_page_config(page_title="Batch ZIP → GitHub Uploader", layout="wide")
st.title("📦 Batch ZIP to GitHub Repo – Massenupload")

# Eingabefelder
github_token = st.text_input("🔑 GitHub Token", type="password", value=default_token)
github_user = st.text_input("👤 GitHub Benutzername", value=default_user)

# Repository-Einstellungen
st.subheader("📋 Repository-Einstellungen")
col1, col2 = st.columns(2)
with col1:
    repo_private = st.checkbox("🔒 Private Repositories", value=True)
    auto_init = st.checkbox("📄 README automatisch erstellen", value=True)
with col2:
    add_license = st.selectbox("📜 Lizenz hinzufügen", 
                              ["Keine", "MIT", "Apache-2.0", "GPL-3.0"])
    add_gitignore = st.selectbox("🚫 .gitignore Template", 
                                ["Keine", "Python", "Node", "Java"])

# Batch-Upload
uploaded_files = st.file_uploader("Mehrere ZIP-Dateien auswählen", 
                                 type="zip", accept_multiple_files=True)

if uploaded_files and github_token and github_user:
    # Vorschau der zu erstellenden Repositories
    st.subheader("🔍 Repository-Vorschau")
    
    preview_data = []
    for i, file in enumerate(uploaded_files):
        repo_name = file.name.replace(".zip", "").replace(" ", "-")
        preview_data.append({
            "Nr.": i+1,
            "ZIP-Datei": file.name,
            "Repository-Name": repo_name,
            "Status": "Ausstehend"
        })
    
    preview_df = pd.DataFrame(preview_data)
    st.dataframe(preview_df)
    
    if st.button("🚀 Alle Projekte hochladen"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        for i, file in enumerate(uploaded_files):
            repo_name = file.name.replace(".zip", "").replace(" ", "-")
            status_text.text(f"Verarbeite {file.name} ({i+1}/{len(uploaded_files)})...")
            
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # ZIP speichern und entpacken
                    zip_path = os.path.join(tmpdir, file.name)
                    with open(zip_path, "wb") as f:
                        f.write(file.read())
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                    
                    # Projektverzeichnis ermitteln
                    entries = os.listdir(tmpdir)
                    dirs = [d for d in entries if os.path.isdir(os.path.join(tmpdir, d)) and d != "__MACOSX"]
                    project_dir = os.path.join(tmpdir, dirs[0]) if dirs else tmpdir
                    
                    # README generieren
                    if auto_init:
                        generated = generate_readme(os.listdir(project_dir))
                        with open(os.path.join(project_dir, "README.md"), "w") as f:
                            f.write(generated)
                    
                    # Repository erstellen und pushen
                    repo_url = create_repo_and_push(
                        github_token, github_user, repo_name, project_dir,
                        private=repo_private,
                        license_template=None if add_license == "Keine" else add_license,
                        gitignore_template=None if add_gitignore == "Keine" else add_gitignore
                    )
                    
                    results.append({
                        "Nr.": i+1,
                        "ZIP-Datei": file.name,
                        "Repository-Name": repo_name,
                        "Repository-URL": repo_url,
                        "Status": "Erfolgreich",
                        "Zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except Exception as e:
                results.append({
                    "Nr.": i+1,
                    "ZIP-Datei": file.name,
                    "Repository-Name": repo_name,
                    "Repository-URL": "",
                    "Status": f"Fehler: {str(e)}",
                    "Zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
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
            mime="text/csv"
        )
else:
    st.info("Bitte lade ZIP-Dateien hoch und gib deine GitHub-Zugangsdaten ein.")