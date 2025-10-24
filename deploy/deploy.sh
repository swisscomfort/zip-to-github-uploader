#!/usr/bin/env bash

# 🚀 deploy.sh – Automatischer Upload & KI-Analyse für ZIP-Projekte
# Verwendung: ./deploy.sh <Projekt-ZIP-Datei>
# Voraussetzungen:
# - .env mit GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_COPILOT_TOKEN vorhanden

set -euo pipefail
export $(grep -v '^#' .env | xargs)

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-zip>"
  exit 1
fi

ZIP_PATH="$1"
WORKDIR=$(mktemp -d)

echo "📦 Entpacke ZIP: $ZIP_PATH"
cp "$ZIP_PATH" "$WORKDIR/upload.zip"
unzip -q "$WORKDIR/upload.zip" -d "$WORKDIR"

# Bestimme Projektverzeichnis
CONTENT_DIRS=( $(find "$WORKDIR" -maxdepth 1 -type d ! -path "$WORKDIR") )
PROJECT_DIR=${CONTENT_DIRS[0]:-$WORKDIR}

echo "📁 Projektverzeichnis: $PROJECT_DIR"

# Generiere README
echo "📝 README automatisch erstellen"

python3 - "$PROJECT_DIR" <<EOF
from shared.generate_readme import generate_readme
import os, sys
project_dir = sys.argv[1]
files = os.listdir(project_dir)
content = generate_readme(files)
with open(os.path.join(project_dir, "README_auto.md"), "w") as f:
    f.write(content)
EOF

# Optional KI-Analyse
if [ -n "${GITHUB_COPILOT_TOKEN:-}" ]; then
  echo "🤖 Starte KI-Analyse (GitHub Copilot)"
  python3 - "$PROJECT_DIR" <<EOF
from shared.gpt_analysis_github_copilot import analyze_project_with_github_copilot
import os, sys
project_dir = sys.argv[1]
prompt = open(os.path.join(project_dir, "README_auto.md")).read()
result = analyze_project_with_github_copilot(prompt)
with open(os.path.join(project_dir, "README_ki.md"), 'w') as f:
    f.write(result)
EOF
else
  echo "⚠ Kein GITHUB_COPILOT_TOKEN gesetzt: KI-Analyse übersprungen"
fi

# Repository-Namen basierend auf ZIP
REPO_NAME=$(basename "$ZIP_PATH" .zip)

echo "🔗 Erstelle GitHub-Repo: $REPO_NAME"
python3 - <<EOF
from uploader_utils import create_repo_and_push
import os
url = create_repo_and_push(
    os.getenv('GITHUB_TOKEN'),
    os.getenv('GITHUB_USERNAME'),
    "$REPO_NAME",
    "$PROJECT_DIR"
)
print("✅ Repo erstellt:", url)
EOF

# Aufräumen
echo "🧹 Aufräumen"
rm -rf "$WORKDIR"

echo "🎉 Fertig!"
