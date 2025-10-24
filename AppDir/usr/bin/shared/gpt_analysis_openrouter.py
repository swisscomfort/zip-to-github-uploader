import os
import requests

def analyze_project_with_openrouter(prompt: str) -> str:
    """
    Sendet eine Projektanalyse-Anfrage an OpenRouter (z. B. Mistral).
    Erwartet Umgebungsvariablen OPENROUTER_API_KEY und OPENROUTER_MODEL in .env.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "mistral/mistral-7b-instruct:free")

    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY nicht gesetzt in .env")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        timeout=30
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
