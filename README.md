# 🚀 ZIP → GitHub Repo Uploader

> Ein intelligentes, professionelles Werkzeug zur Automatisierung von ZIP-Projekt-Uploads in GitHub-Repositories.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Release](https://img.shields.io/github/v/release/swisscomfort/zip-to-github-uploader?style=flat)](https://github.com/swisscomfort/zip-to-github-uploader/releases)
[![GitHub Stars](https://img.shields.io/github/stars/swisscomfort/zip-to-github-uploader?style=flat)](https://github.com/swisscomfort/zip-to-github-uploader)
[![GitHub Issues](https://img.shields.io/github/issues/swisscomfort/zip-to-github-uploader?style=flat)](https://github.com/swisscomfort/zip-to-github-uploader/issues)
[![Streamlit App](https://img.shields.io/badge/Streamlit-v1.28+-FF4B4B?style=flat)](https://streamlit.io)
[![Build Status](https://img.shields.io/github/actions/workflow/status/swisscomfort/zip-to-github-uploader/tests.yml?style=flat)](https://github.com/swisscomfort/zip-to-github-uploader/actions)

---

## 🎯 Funktionen

## 📋 Inhaltsverzeichnis

- 📦 Lade ZIP-Dateien direkt über die Oberfläche hoch

- [Features](#-features)- 🧠 Die App entpackt, initialisiert Git, committet und pusht dein Projekt

- [Installation](#-installation)- 🌐 Erstellt automatisch ein neues **öffentliches Repository auf GitHub**

- [Schnellstart](#-schnellstart)- ⚙️ Nutzt GitHub API (via Token) und subprocess für Git-Aktionen

- [Verwendung](#-verwendung)- 🧱 Ideal zur Massenverarbeitung von ZIP-Projekten (z. B. von Exporten, Prototypen, Bot-Projekten)

- [Architektur](#-architektur)

- [Sicherheit](#-sicherheit)---

- [Contributing](#-contributing)

- [Lizenz](#-lizenz)## 🧪 Demo in Aktion



---> Ein ZIP hochladen. Projektname & Token eingeben. **Zack, online.**



## ✨ Features---



### Core-Features## 🛠️ Voraussetzungen

- 📦 **ZIP-Upload & Extraktion** – Hochladen von ZIP-Dateien mit automatischer Entpackung

- 🤖 **GitHub API Integration** – Erstelle automatisch neue öffentliche/private Repositories- Python 3.8+

- 🔐 **Token-basierte Auth** – Sichere Authentifizierung mit GitHub Personal Access Tokens- Git (im Systempfad)

- 🧬 **Git-Push Automatisierung** – Automatischer Commit und Push von Projektdateien- [GitHub Token](https://github.com/settings/tokens) mit `repo`-Rechten

- 📊 **Batch-Processing** – Verarbeite mehrere ZIP-Dateien gleichzeitig

- 🔒 **Sicherheitsvalidierung** – Umfassende Dateiprüfung mit Whitelist-AnsatzInstallieren:

```bash

### Erweiterte Featurespip install -r requirements.txt

- 🤖 **AI-Analyse** – Projektbeschreibung & Tags mit GitHub Copilot Integration```

- 📋 **Auto-README** – Intelligente README-Generierung basierend auf Projekttyp

- 🔔 **Webhooks** – Benachrichtigungen via Slack, Discord oder EmailStarten:

- 📊 **Dashboard** – Upload-Historie und Statistiken```bash

- 🐧 **AppImage** – Portable Linux-Distributionstreamlit run streamlit_app.py

- 📈 **Rate-Limiting** – Schutz vor Missbrauch mit konfigurierbaren Limits```



------



## 📦 Installation## 📁 Projektstruktur



### Voraussetzungen```text

zip-uploader/

- **Python 3.8 oder neuer**├── streamlit_app.py            ← Hauptanwendung (Streamlit GUI)

- **Git** (im Systempfad installiert)├── uploader_utils.py           ← GitHub- & Git-Integration

- **GitHub Personal Access Token** ([Token erstellen](https://github.com/settings/tokens))├── requirements.txt            ← Python-Abhängigkeiten

├── README.md                   ← Diese Datei

### Setup```



```bash---

# Virtuelle Umgebung erstellen

python3 -m venv venv## 🧑‍💻 Vorlage von

source venv/bin/activate  # Linux/macOS

**swisscomfort** – entwickelt im Rahmen des `app-dev-starter`-Setups  

# Dependencies installieren👀 [Besuche mein GitHub-Profil](https://github.com/swisscomfort)
pip install -r requirements.txt

# Konfiguriere .env (siehe unten)
cp .env.example .env  # Bearbeite mit deinen Credentials
```

---

## 🚀 Schnellstart

### 1. Umgebungsvariablen konfigurieren

Erstelle eine `.env`-Datei:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_USERNAME=your_github_username
GITHUB_COPILOT_TOKEN=ghp_your_token_optional
```

### 2. App starten

```bash
streamlit run src/streamlit_app.py
```

### 3. ZIP hochladen & Repository erstellen

- Wähle ZIP-Datei
- Gib Details ein
- Klick Upload
- Fertig! 🎉

---

## 💻 Verwendung

### Web-Interface

**Einzelupload:**
```bash
streamlit run src/streamlit_app.py
```

**Batch-Upload:**
```bash
streamlit run src/batch_uploader.py
```

**Dashboard:**
```bash
streamlit run src/dashboard.py
```

### Python-API

```python
from src.uploader_utils import create_repo_and_push

result = create_repo_and_push(
    github_token="ghp_xxx",
    github_user="username",
    repo_name="my-project",
    local_path="/path/to/project",
    private=False,
    license_template="MIT"
)
```

---

## 🏗️ Architektur

```
src/
├── streamlit_app.py         # GUI
├── batch_uploader.py        # Batch-Processing
├── dashboard.py             # Analytics
├── uploader_utils.py        # GitHub API
├── security_validation.py   # File Validation
├── webhook_integration.py   # Notifications
└── shared/                  # Utilities
```

---

## 🔐 Sicherheit

✅ Whitelist-Ansatz
✅ MIME-Type-Validierung
✅ Rate-Limiting
✅ Input-Sanitization
✅ Minimale Token-Berechtigungen

Siehe [SECURITY.md](./SECURITY.md) für Details.

---

## 🤝 Contributing

Siehe [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## �‍💻 Über den Autor

**swisscomfort** – Full-Stack Developer & Open Source Enthusiast

- 🌐 GitHub: [@swisscomfort](https://github.com/swisscomfort)
- 💼 Portfolio: Spezialisiert auf Python, Web Development & DevOps
- 🚀 Projekte: Automatisierung, Cloud-native Applications, Developer Tools

---

## �📄 Lizenz

MIT License – Siehe [LICENSE](./LICENSE)

Made with ❤️ by [swisscomfort](https://github.com/swisscomfort)
