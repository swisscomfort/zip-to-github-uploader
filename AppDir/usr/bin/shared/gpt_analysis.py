from openai import OpenAI

def analyze_code_structure(file_list, api_key):
    prompt = f"""
Ich bin eine KI. Bitte beschreibe dieses Projekt basierend auf diesen Dateien:
{file_list}

Antworte mit:
1. Kurzbeschreibung in 1–2 Sätzen
2. Eine Liste mit max. 6 passenden Tags
"""
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist ein hilfsbereiter Projektanalyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=300
    )

    return response.choices[0].message.content
