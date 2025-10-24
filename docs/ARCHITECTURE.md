# 🏗️ Architektur-Dokumentation

Technisches Design und Übersicht des ZIP-to-GitHub-Uploaders.

## 📐 System-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    Web-UI (Streamlit)                       │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │   Single     │    Batch     │  Dashboard   │            │
│  │   Upload     │   Upload     │              │            │
│  └──────────────┴──────────────┴──────────────┘            │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────────┐ ┌─▼────────────┐
│  Validation  │ │   Uploader   │ │   Utilities  │
│   Module     │ │   Module     │ │   & Shared   │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │
        │              │
        └──────────────┼──────────────┐
                       │              │
                 ┌─────▼────┐  ┌─────▼──────┐
                 │ GitHub   │  │   Git CLI  │
                 │   API    │  │            │
                 └──────────┘  └────────────┘
```

---

## 📦 Module & Verantwortlichkeiten

### 1. Core Module (`src/`)

#### **streamlit_app.py** (679 Zeilen)
**Zweck**: Haupt-Benutzeroberfläche
**Verantwortlichkeiten**:
- ZIP-Datei-Upload & Validierung
- Benutzereingaben (Repo-Name, GitHub-Token)
- Repository-Konfiguration (privat, mit License, .gitignore)
- Live-Feedback und Fehlerbehandlung
- Navigation zwischen Seiten

**Key Functions**:
- `detect_project_type()` – Projekttyp erkennen
- `validate_project()` – Projekt-Validierung
- `detect_security_issues()` – Sicherheitsprobleme finden
- `analyze_code_quality()` – Code-Qualität bewerten

---

#### **uploader_utils.py** (336 Zeilen)
**Zweck**: GitHub API und Git-Integration
**Verantwortlichkeiten**:
- Repository-Erstellung via GitHub API
- Git-Operationen (init, add, commit, push)
- Name-Konflikt-Vermeidung
- Upload-Historie speichern

**Key Functions**:
```python
create_repo_and_push(
    github_token,          # GitHub PAT
    github_user,           # Account-Name
    repo_name,             # Repository-Name
    local_path,            # Lokaler Projekt-Pfad
    private=True,          # Public/Private
    license_template=None, # MIT, Apache, etc.
    gitignore_template=None,
    auto_init=True         # Auto-Initialize
) -> str  # Repository-URL
```

**Git-Flow**:
1. Erstelle GitHub Repository via API
2. Klone via HTTPS (mit Token-Auth)
3. Kopiere Dateien in Repo-Verzeichnis
4. `git add .`
5. `git commit -m "Initial commit"`
6. `git push -u origin main`

---

#### **security_validation.py** (800+ Zeilen)
**Zweck**: Dateivalidierung und Sicherheitsprüfung
**Verantwortlichkeiten**:
- Whitelist-basierte Dateityp-Validierung
- MIME-Type-Prüfung
- Größen-Limits pro Upload-Typ
- Rate-Limiting pro IP/User
- Archive-Inspection

**Upload-Typen & Limits**:

| Typ | Max File | Max ZIP | Entpackt | Dateien |
|-----|----------|---------|----------|---------|
| web | 25 MB | 50 MB | 100 MB | 500 |
| api | 100 MB | 200 MB | 400 MB | 1000 |
| admin | 500 MB | 1 GB | 2 GB | 5000 |

**Rate-Limits**:
- 50 Uploads pro Stunde
- 200 Uploads pro Tag

**Validierungs-Chain**:
```
1. Filename-Check (gefährliche Zeichen?)
2. MIME-Type-Prüfung (magic bytes)
3. Größen-Prüfung
4. Archive-Exploration
   a. ZIP-Struktur valid?
   b. Jede Datei validieren
   c. Entpackte Größe prüfen
5. Rate-Limit-Check
```

---

#### **batch_uploader.py** (142 Zeilen)
**Zweck**: Massenverarbeitung mehrerer ZIPs
**Features**:
- Mehrere Dateien gleichzeitig
- Konfigurierbare Repository-Einstellungen
- Fortschrittsbar
- Fehlerbehandlung & Retry-Logik

---

#### **dashboard.py** (211 Zeilen)
**Zweck**: Monitoring und Analytics
**Features**:
- Upload-Statistiken
- Repository-Liste
- Upload-Historie
- Verwaltungs-Tools

---

### 2. Utility Module (`src/shared/`)

#### **generate_readme.py**
- Intelligente README-Generierung
- Projekttyp-Erkennung
- Framework-Detection

#### **gpt_analysis_github_copilot.py**
- GitHub Copilot API Integration
- Projekt-Analyse via GPT-4
- Tag & Description-Generierung

#### **gpt_analysis_github_copilot.py**
- GitHub Copilot API Integration
- Projekt-Analyse via GPT-4
- Tag & Description-Generierung

---

### 3. Tests (`tests/`)

#### **test_security_validation.py**
- Unit-Tests für Validierungsmodul
- Testfälle:
  - Filename-Validierung
  - File-Kategorie-Erkennung
  - Rate-Limiting
  - ZIP-Validierung

#### **validate_real_files.py**
- Interaktive Dateivalidierung
- CLI-Tool für manuelle Tests
- Detaillierte Berichte

---

## 🔄 Daten-Flows

### Upload-Flow

```
┌─────────────────────────────────┐
│   User wählt ZIP-Datei aus      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  ZIP-Datei wird validiert       │
│  - MIME-Type
│  - Größe
│  - Rate-Limit
└────────────┬────────────────────┘
             │
       ┌─────┴─────┐
       │ Valid?    │
       └─────┬─────┘
             │
        ┌────▼────┐
   No   │          │  Yes
  ┌─────▼─────┐    │
  │ Error      │    │
  │ Message    │    ▼
  └────────────┐  ┌──────────────────┐
               │  │ ZIP entpacken    │
               │  │ in temp dir      │
               │  └────────┬─────────┘
               │           │
               │           ▼
               │  ┌──────────────────────┐
               │  │ GitHub Repository    │
               │  │ erstellen (API)      │
               │  └────────┬─────────────┘
               │           │
               │           ▼
               │  ┌──────────────────────┐
               │  │ Dateien pushen via   │
               │  │ Git CLI              │
               │  └────────┬─────────────┘
               │           │
               │           ▼
               │  ┌──────────────────────┐
               │  │ History speichern    │
               │  │ Webhook senden       │
               │  └──────────────────────┘
               │
               ▼
        ┌────────────────┐
        │ Success/Error  │
        │ an UI          │
        └────────────────┘
```

### GitHub API Integration

**Endpoint**: `POST /user/repos`

```json
{
  "name": "my-awesome-project",
  "private": false,
  "description": "Automatisch erstellt",
  "auto_init": true,
  "license_template": "MIT",
  "gitignore_template": "Python"
}
```

**Response**:
- `clone_url` – HTTPS-Clone-URL
- `ssh_url` – SSH-Clone-URL
- `html_url` – GitHub-URL

---

## 🔐 Sicherheits-Architektur

### Defense Layers

```
1. Frontend-Validierung (Streamlit UI)
   ↓
2. MIME-Type-Prüfung (magic bytes)
   ↓
3. Whitelist-Validierung (erlaubte Dateitypen)
   ↓
4. Größen-Limits (pro Upload-Typ)
   ↓
5. Archive-Inspection (Inhalt prüfen)
   ↓
6. Rate-Limiting (IP/User-based)
   ↓
7. GitHub Token-Validierung
   ↓
8. Input-Sanitization (Dateinamen, Repo-Namen)
```

### Secret Management

```
.env (lokal, nicht versioniert)
  │
  ├─ GITHUB_TOKEN → GitHub API Auth
  ├─ GITHUB_USERNAME → Account Identification
  └─ OPENROUTER_API_KEY → AI-Features

Environment → Code lädt via dotenv
```

---

## 📊 Datenmodelle

### Upload-Objekt

```python
{
  "id": "uuid",
  "timestamp": "2025-10-24T12:34:56Z",
  "zip_filename": "my-project.zip",
  "repo_name": "my-project",
  "github_user": "username",
  "repo_url": "https://github.com/username/my-project",
  "status": "success",  # success, failed, pending
  "file_size": 1024000,
  "files_count": 25,
  "project_type": "python",
  "error_message": null,
  "duration_seconds": 12.5
}
```

### Validation-Report

```python
{
  "filename": "project.zip",
  "is_safe": True,
  "mime_type": "application/zip",
  "file_size": 1024000,
  "size_formatted": "1.0 MB",
  "file_category": "archive",
  "is_binary": True,
  "warnings": [],
  "risks": [],
  "timestamp": "2025-10-24T12:34:56Z"
}
```

---

## 🔄 Deployment-Architektur

### Streamlit Cloud
```
GitHub Repo
    ↓
Streamlit Cloud (auto-deploy on push)
    ↓
Öffentliche URL
```

### Docker
```
Dockerfile
    ↓
Docker Build
    ↓
Container Registry
    ↓
Deploy (Heroku, AWS, etc.)
```

### AppImage (Linux)
```
Python + Dependencies
    ↓
AppDir struktur
    ↓
appimagetool
    ↓
ZIP-to-GitHub-Uploader-x86_64.AppImage
```

---

## ⚡ Performance-Optimierungen

### Caching
- Upload-Historie in `upload_history.json`
- Projekt-Type-Detection gecacht
- Security-Validation Cache

### Parallel Processing
- Batch-Uploader verarbeitet ZIPs parallel
- Max 5 concurrent uploads (konfigurierbar)

### Rate-Limiting
- Verhindert API-Überlastung
- Per-User & Per-IP Limits
- Graceful degradation bei Limits

---

## 🔍 Fehlerbehandlung

### Error Categories

1. **Validation Errors**
   - Dateitype nicht erlaubt
   - Datei zu groß
   - Archive beschädigt

2. **GitHub API Errors**
   - Token ungültig
   - Repository existiert bereits
   - Quota überschritten

3. **Git Errors**
   - Push-Fehler
   - Branch-Konflikt
   - Auth-Fehler

4. **System Errors**
   - Disk-Space
   - Memory
   - Network

---

## 🚀 Erweiterungspunkte

Wo können neue Features hinzugefügt werden?

1. **Neue Upload-Quellen**
   - API Endpoint
   - Cloud Storage (AWS S3, Google Drive)
   - FTP/SFTP

2. **Neue Repository-Hosts**
   - GitLab
   - Gitea
   - Bitbucket

3. **Weitere AI-Integrationen**
   - GPT-4 / Claude
   - Lokale LLMs
   - Code-Analyse

4. **Enhanced Notifications**
   - SMS
   - Teams
   - Custom Webhooks

5. **Monitoring & Analytics**
   - Prometheus Metrics
   - Grafana Dashboards
   - Log Aggregation

---

## 📚 Dependencies

### Core
- `streamlit` – Web-Framework
- `requests` – HTTP Client
- `python-dotenv` – Environment Vars
- `python-magic` – MIME-Type Detection

### Optional
- `openrouter` – AI Integration
- `pytest` – Testing
- `black` – Code Formatting

---

## 🔄 Versionierung

Semantic Versioning (semver):
- `MAJOR` – Breaking Changes
- `MINOR` – New Features
- `PATCH` – Bug Fixes

Beispiel: `1.0.0` → `1.1.0` (neue Feature)
