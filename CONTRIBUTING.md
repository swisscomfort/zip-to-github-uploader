# Contributing Guide

Vielen Dank, dass du ZIP-to-GitHub-Uploader verbessern möchtest! 🎉

## 📋 Vor dem Start

1. **Fork** das Repository
2. **Clone** dein Fork lokal
3. **Erstelle** einen neuen Branch: `git checkout -b feature/deine-feature`

## 🚀 Development Setup

```bash
# 1. Repository klonen
git clone https://github.com/DEIN_GITHUB/zip-to-github-uploader.git
cd zip-to-github-uploader

# 2. Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Für Development

# 4. Starte die App
streamlit run src/streamlit_app.py
```

## 📝 Code-Style

Wir folgen [PEP 8](https://pep8.org/):

```bash
# Formatierung prüfen
pylint src/
black --check src/

# Auto-Format
black src/
```

## 🧪 Tests

```bash
# Alle Tests ausführen
pytest tests/

# Mit Coverage
pytest --cov=src tests/

# Specific Test
pytest tests/test_security_validation.py -v
```

## 🔍 Commit-Konventionen

Nutze **Conventional Commits**:

```
feat: neue Feature beschreiben
fix: Bugfix beschreiben
docs: Dokumentation aktualisieren
test: Tests hinzufügen
refactor: Code umstrukturieren
chore: Build, Dependencies etc.
```

Beispiele:
```
feat: Batch-Upload mit Fortschrittsanzeige
fix: GitHub-Token-Validierung bei leeren Token
docs: API-Dokumentation erweitern
```

## 📤 Pull Requests

1. **Pushe** deinen Branch zu deinem Fork
2. **Öffne** einen PR gegen `main`
3. **Beschreibe** klar, was deine Änderung tut
4. **Verlinke** verwandte Issues (`Fixes #123`)
5. **Warte** auf Review

### PR-Vorlage

```markdown
## Beschreibung
Was macht dieser PR?

## Type of Change
- [ ] Bug-Fix
- [ ] Neue Feature
- [ ] Breaking Change
- [ ] Dokumentation

## Testing
Wie wurde das getestet?

## Checkliste
- [ ] Code folgt dem Style Guide
- [ ] Neue Tests hinzugefügt
- [ ] Dokumentation aktualisiert
- [ ] Keine neuen Warnings
```

## 🎯 Bereiche zur Mitwirkung

### Code
- 🐛 Bug-Fixes
- ✨ Neue Features
- ⚡ Performance-Optimierung
- ♻️ Code-Refactoring

### Dokumentation
- 📖 README verbessern
- 🎓 Tutorials schreiben
- 🔍 Typos fixen

### Testing
- ✅ Unit-Tests erweitern
- 🧪 Integration-Tests
- 🔒 Security-Tests

### Lokalisierung
- 🌍 Neue Sprachen hinzufügen
- 🗣️ Übersetzungen verbessern

## 💡 Ideen & Suggestions

1. **Öffne eine Discussion** unter "Discussions"
2. **Oder ein Issue** mit Label `enhancement`
3. **Beschreibe** die Use-Case detailliert

## 📦 Release-Prozess

Maintainer aktualisieren die Version nach:
- `X.Y.Z` → Major.Minor.Patch (Semantic Versioning)
- Updates in `CHANGELOG.md`
- GitHub Release mit Release Notes

## 🤝 Verhaltensrichtlinien

- ✅ Sei respektvoll gegenüber anderen
- ✅ Feedback ist konstruktiv gemeint
- ✅ Melde keine Äußerungen von Anderen
- ❌ Keine Diskriminierung oder Missbrauch
- ❌ Keine kommerziellen Spam

Wir halten uns an den [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/).

## ❓ Fragen?

- 💬 Schreib eine GitHub Discussion
- 📧 Kontaktiere den Maintainer
- 📚 Schau in die `docs/` für mehr Info

Danke für deine Mitwirkung! 🙏
