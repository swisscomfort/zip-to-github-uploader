import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def send_slack_notification(repo_name, repo_url, success=True):
    """
    Sendet eine Benachrichtigung an Slack über einen neuen Repository-Upload.
    Erfordert SLACK_WEBHOOK_URL in .env
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    
    status = "erfolgreich" if success else "fehlgeschlagen"
    color = "#36a64f" if success else "#ff0000"
    
    payload = {
        "attachments": [
            {
                "fallback": f"Repository-Upload {status}: {repo_name}",
                "color": color,
                "title": f"Repository-Upload {status}",
                "title_link": repo_url,
                "fields": [
                    {
                        "title": "Repository",
                        "value": repo_name,
                        "short": True
                    },
                    {
                        "title": "Status",
                        "value": status.capitalize(),
                        "short": True
                    }
                ],
                "footer": "ZIP to GitHub Uploader",
                "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception:
        return False

def send_discord_notification(repo_name, repo_url, success=True):
    """
    Sendet eine Benachrichtigung an Discord über einen neuen Repository-Upload.
    Erfordert DISCORD_WEBHOOK_URL in .env
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False
    
    status = "erfolgreich" if success else "fehlgeschlagen"
    color = 3066993 if success else 15158332  # Grün oder Rot
    
    payload = {
        "embeds": [
            {
                "title": f"Repository-Upload {status}",
                "description": f"Repository: [{repo_name}]({repo_url})",
                "color": color,
                "footer": {
                    "text": "ZIP to GitHub Uploader"
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception:
        return False

def send_email_notification(repo_name, repo_url, recipient_email, success=True):
    """
    Sendet eine E-Mail-Benachrichtigung über einen neuen Repository-Upload.
    Erfordert SMTP-Konfiguration in .env
    """
    # Diese Funktion würde SMTP verwenden, um E-Mails zu senden
    # Für die Implementierung wäre ein E-Mail-Service wie SendGrid oder SMTP-Bibliothek nötig
    pass

def notify_all(repo_name, repo_url, success=True):
    """
    Sendet Benachrichtigungen an alle konfigurierten Kanäle.
    """
    results = {}
    
    # Slack
    slack_result = send_slack_notification(repo_name, repo_url, success)
    results["slack"] = slack_result
    
    # Discord
    discord_result = send_discord_notification(repo_name, repo_url, success)
    results["discord"] = discord_result
    
    # E-Mail (falls konfiguriert)
    email = os.getenv("NOTIFICATION_EMAIL")
    if email:
        email_result = send_email_notification(repo_name, repo_url, email, success)
        results["email"] = email_result
    
    return results