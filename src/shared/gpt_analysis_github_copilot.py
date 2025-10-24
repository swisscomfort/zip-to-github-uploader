import os
import requests

def analyze_project_with_github_copilot(prompt: str) -> str:
    """
    Sendet eine Projektanalyse-Anfrage an GitHub Copilot API.
    Erwartet Umgebungsvariable GITHUB_COPILOT_TOKEN in .env.
    
    GitHub Copilot nutzt das GPT-4 Modell für hochwertige Code-Analysen.
    """
    api_key = os.getenv("GITHUB_COPILOT_TOKEN")
    
    if not api_key:
        raise EnvironmentError(
            "GITHUB_COPILOT_TOKEN nicht gesetzt in .env. "
            "Registriere unter: https://github.com/copilot/chat"
        )

    response = requests.post(
        "https://api.github.com/copilot_internal/v2/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Code-Analyse-Assistent. Analysiere Projekte und gebe hilfreiche Zusammenfassungen."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        },
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"GitHub Copilot API-Fehler ({response.status_code}): "
            f"{response.json().get('message', 'Unbekannter Fehler')}"
        )
    
    return response.json()["choices"][0]["message"]["content"]
