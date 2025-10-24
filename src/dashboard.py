import streamlit as st
import pandas as pd
import json
import os
import requests
import matplotlib.pyplot as plt
import altair as alt
from datetime import datetime, timedelta

# Streamlit Konfiguration
st.set_page_config(page_title="GitHub Uploader Dashboard", layout="wide")
st.title("📊 GitHub Uploader Dashboard")

# .env laden
from dotenv import load_dotenv
load_dotenv()

# Voreinstellungen
default_token = os.getenv("GITHUB_TOKEN")
default_user = os.getenv("GITHUB_USERNAME")

# Seitenleiste für Authentifizierung
with st.sidebar:
    st.header("🔐 Authentifizierung")
    github_token = st.text_input("GitHub Token", type="password", value=default_token)
    github_user = st.text_input("GitHub Benutzername", value=default_user)
    
    if github_token and github_user:
        st.success("✅ Authentifizierung bereit")
    else:
        st.warning("⚠️ Bitte GitHub-Zugangsdaten eingeben")

# Hauptbereich
if github_token and github_user:
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Übersicht", "🔍 Repository-Liste", "📜 Upload-Historie", "⚙️ Verwaltung"])
    
    with tab1:
        st.header("📈 Dashboard-Übersicht")
        
        # Upload-Historie laden
        history_file = "upload_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                # Statistiken berechnen
                total_repos = len(history)
                recent_repos = sum(1 for item in history if datetime.fromisoformat(item['timestamp']) > datetime.now() - timedelta(days=7))
                success_rate = sum(1 for item in history if item['status'] == 'success') / total_repos if total_repos > 0 else 0
                
                # Statistik-Karten
                col1, col2, col3 = st.columns(3)
                col1.metric("Gesamt-Repositories", total_repos)
                col2.metric("Letzte 7 Tage", recent_repos)
                col3.metric("Erfolgsrate", f"{success_rate:.1%}")
                
                # Zeitverlauf-Diagramm
                st.subheader("Repository-Erstellungen im Zeitverlauf")
                
                # Daten für Chart vorbereiten
                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                daily_counts = df.groupby('date').size().reset_index(name='count')
                
                # Altair Chart
                chart = alt.Chart(daily_counts).mark_line(point=True).encode(
                    x='date:T',
                    y='count:Q',
                    tooltip=['date:T', 'count:Q']
                ).properties(height=300)
                
                st.altair_chart(chart, use_container_width=True)
                
            except Exception as e:
                st.error(f"Fehler beim Laden der Upload-Historie: {e}")
        else:
            st.info("Keine Upload-Historie gefunden. Erstelle zuerst einige Repositories.")
    
    with tab2:
        st.header("🔍 Repository-Liste")
        
        if st.button("🔄 Repositories laden"):
            with st.spinner("Lade Repositories..."):
                headers = {"Authorization": f"token {github_token}"}
                response = requests.get(f"https://api.github.com/users/{github_user}/repos?per_page=100", headers=headers)
                
                if response.status_code == 200:
                    repos = response.json()
                    
                    # Daten für Tabelle vorbereiten
                    repo_data = []
                    for repo in repos:
                        repo_data.append({
                            "Name": repo['name'],
                            "Beschreibung": repo['description'] or "",
                            "Erstellt am": repo['created_at'],
                            "Sprache": repo['language'] or "Unbekannt",
                            "Sichtbarkeit": "Privat" if repo['private'] else "Öffentlich",
                            "URL": repo['html_url']
                        })
                    
                    # Tabelle anzeigen
                    df = pd.DataFrame(repo_data)
                    st.dataframe(df)
                    
                    # Sprachverteilung
                    st.subheader("Sprachverteilung")
                    lang_counts = df['Sprache'].value_counts()
                    st.bar_chart(lang_counts)
                    
                else:
                    st.error(f"Fehler beim Laden der Repositories: {response.status_code}")
    
    with tab3:
        st.header("📜 Upload-Historie")
        
        # Upload-Historie laden
        history_file = "upload_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                # Daten für Tabelle vorbereiten
                df = pd.DataFrame(history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
                
                # Tabelle anzeigen
                st.dataframe(df)
                
                # CSV-Export
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Historie als CSV herunterladen",
                    data=csv,
                    file_name=f"upload_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"Fehler beim Laden der Upload-Historie: {e}")
        else:
            st.info("Keine Upload-Historie gefunden. Erstelle zuerst einige Repositories.")
    
    with tab4:
        st.header("⚙️ Repository-Verwaltung")
        
        # Repository auswählen
        repo_name = st.text_input("Repository-Name zum Verwalten")
        
        if repo_name and st.button("🔍 Repository-Details laden"):
            headers = {"Authorization": f"token {github_token}"}
            response = requests.get(f"https://api.github.com/repos/{github_user}/{repo_name}", headers=headers)
            
            if response.status_code == 200:
                repo = response.json()
                
                st.subheader(f"Details für {repo['name']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Beschreibung:** {repo['description'] or 'Keine'}")
                    st.write(f"**Erstellt am:** {repo['created_at']}")
                    st.write(f"**Sprache:** {repo['language'] or 'Unbekannt'}")
                    st.write(f"**Sichtbarkeit:** {'Privat' if repo['private'] else 'Öffentlich'}")
                
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
                        new_private = not repo['private']
                        update_response = requests.patch(
                            f"https://api.github.com/repos/{github_user}/{repo_name}",
                            headers=headers,
                            json={"private": new_private}
                        )
                        
                        if update_response.status_code == 200:
                            st.success(f"Sichtbarkeit geändert zu: {'Privat' if new_private else 'Öffentlich'}")
                        else:
                            st.error(f"Fehler beim Ändern der Sichtbarkeit: {update_response.status_code}")
                
                with col2:
                    if st.button("🗑️ Repository löschen", help="Achtung: Diese Aktion kann nicht rückgängig gemacht werden!"):
                        confirm = st.text_input("Zum Bestätigen Repository-Namen eingeben")
                        
                        if confirm == repo_name:
                            delete_response = requests.delete(
                                f"https://api.github.com/repos/{github_user}/{repo_name}",
                                headers=headers
                            )
                            
                            if delete_response.status_code == 204:
                                st.success(f"Repository {repo_name} erfolgreich gelöscht!")
                            else:
                                st.error(f"Fehler beim Löschen des Repositories: {delete_response.status_code}")
            else:
                st.error(f"Repository nicht gefunden: {response.status_code}")
else:
    st.warning("Bitte gib deine GitHub-Zugangsdaten in der Seitenleiste ein.")