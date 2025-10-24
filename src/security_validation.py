import os
import zipfile
import magic
import hashlib
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Konfigurierbare Limits je nach Anwendungsfall
UPLOAD_LIMITS = {
    "web_upload": {
        "max_file_size": 25 * 1024 * 1024,  # 25 MB für Web-Uploads
        "max_zip_size": 50 * 1024 * 1024,  # 50 MB für ZIP-Archive
        "max_extracted_size": 100 * 1024 * 1024,  # 100 MB entpackt
        "max_files_in_zip": 500,  # Max. 500 Dateien pro ZIP
    },
    "api_upload": {
        "max_file_size": 100 * 1024 * 1024,  # 100 MB für API
        "max_zip_size": 200 * 1024 * 1024,  # 200 MB für ZIP-Archive
        "max_extracted_size": 400 * 1024 * 1024,  # 400 MB entpackt
        "max_files_in_zip": 1000,  # Max. 1000 Dateien pro ZIP
    },
    "admin_upload": {
        "max_file_size": 500 * 1024 * 1024,  # 500 MB für Admins
        "max_zip_size": 1024 * 1024 * 1024,  # 1 GB für ZIP-Archive
        "max_extracted_size": 2048 * 1024 * 1024,  # 2 GB entpackt
        "max_files_in_zip": 5000,  # Max. 5000 Dateien pro ZIP
    },
}

# Dateityp-spezifische Limits
FILE_TYPE_LIMITS = {
    "image": 20 * 1024 * 1024,  # 20 MB für Bilder
    "document": 50 * 1024 * 1024,  # 50 MB für Dokumente
    "archive": 200 * 1024 * 1024,  # 200 MB für Archive
    "video": 1024 * 1024 * 1024,  # 1 GB für Videos
    "audio": 100 * 1024 * 1024,  # 100 MB für Audio
}

# Whitelist für erlaubte Dateierweiterungen (sicherer als Blacklist)
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "document": [
        ".pdf",
        ".txt",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
    ],
    "archive": [".zip", ".tar", ".gz", ".7z", ".rar"],
    "code": [".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".md"],
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac"],
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
}

# Whitelist für erlaubte MIME-Types
ALLOWED_MIME_TYPES = {
    "image": [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/svg+xml",
    ],
    "document": [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    "archive": [
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-7z-compressed",
    ],
    "code": [
        "text/plain",
        "text/html",
        "text/css",
        "application/json",
        "application/xml",
        "text/markdown",
        "text/x-python",
        "application/javascript",
        "text/javascript",
    ],
}

# Rate Limiting - Uploads pro IP/User
RATE_LIMITS = {"max_uploads_per_hour": 50, "max_uploads_per_day": 200}

# Globaler Speicher für Rate Limiting (in Produktion: Redis/Database verwenden)
upload_tracker = defaultdict(list)

# Blacklist für verdächtige Dateinamen (zusätzlich zur Whitelist)
SUSPICIOUS_PATTERNS = [
    r"backdoor",
    r"hack",
    r"exploit",
    r"trojan",
    r"virus",
    r"malware",
    r"ransom",
    r"keylog",
    r"rootkit",
    r"botnet",
    r"payload",
    r"shell",
    r"reverse",
]


def is_safe_path(filename):
    """Verhindert Directory Traversal Angriffe"""
    # Prüfe auf Directory Traversal Versuche
    if ".." in filename or filename.startswith("/") or ":" in filename:
        return False

    # Prüfe auf absolute Pfade und gefährliche Zeichen
    dangerous_chars = ["\\", "<", ">", "|", "*", "?", '"']
    if any(char in filename for char in dangerous_chars):
        return False

    return True


def get_file_category(filename, mime_type=None):
    """Bestimmt die Kategorie einer Datei basierend auf Erweiterung und MIME-Type"""
    filename_lower = filename.lower()

    for category, extensions in ALLOWED_EXTENSIONS.items():
        if any(filename_lower.endswith(ext) for ext in extensions):
            # Zusätzliche MIME-Type Validierung wenn verfügbar
            if mime_type and category in ALLOWED_MIME_TYPES:
                if mime_type not in ALLOWED_MIME_TYPES[category]:
                    return None  # MIME-Type stimmt nicht mit Erweiterung überein
            return category

    return None  # Dateitype nicht erlaubt


def is_safe_filename(filename, upload_type="web_upload"):
    """Prüft, ob ein Dateiname sicher ist (Whitelist-Ansatz)"""
    filename_lower = filename.lower()

    # Prüfe auf Directory Traversal
    if not is_safe_path(filename):
        return False, "Gefährlicher Pfad erkannt (Directory Traversal)"

    # Prüfe auf erlaubte Dateierweiterungen (Whitelist)
    file_category = get_file_category(filename)
    if not file_category:
        return False, "Dateityp nicht erlaubt"

    # Prüfe auf verdächtige Muster im Dateinamen
    if any(re.search(pattern, filename_lower) for pattern in SUSPICIOUS_PATTERNS):
        return False, "Verdächtiges Muster im Dateinamen erkannt"

    # Prüfe auf doppelte Erweiterungen (z.B. file.exe.txt)
    parts = filename_lower.split(".")
    if len(parts) > 2:
        # Prüfe ob eine der mittleren "Erweiterungen" gefährlich ist
        dangerous_exts = [
            ".exe",
            ".dll",
            ".bat",
            ".cmd",
            ".sh",
            ".com",
            ".scr",
            ".pif",
            ".vbs",
            ".ps1",
        ]
        for i in range(1, len(parts) - 1):
            if f".{parts[i]}" in dangerous_exts:
                return False, "Versteckte gefährliche Erweiterung erkannt"

    return True, "Dateiname ist sicher"


def check_rate_limit(user_id, upload_type="web_upload"):
    """Prüft Rate Limiting für Uploads"""
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    # Bereinige alte Einträge
    upload_tracker[user_id] = [
        timestamp for timestamp in upload_tracker[user_id] if timestamp > day_ago
    ]

    # Zähle Uploads der letzten Stunde und des letzten Tages
    uploads_last_hour = sum(
        1 for timestamp in upload_tracker[user_id] if timestamp > hour_ago
    )
    uploads_last_day = len(upload_tracker[user_id])

    # Prüfe Limits
    if uploads_last_hour >= RATE_LIMITS["max_uploads_per_hour"]:
        return (
            False,
            f"Rate Limit überschritten: {uploads_last_hour} Uploads in der letzten Stunde",
        )

    if uploads_last_day >= RATE_LIMITS["max_uploads_per_day"]:
        return (
            False,
            f"Rate Limit überschritten: {uploads_last_day} Uploads in den letzten 24 Stunden",
        )

    # Füge aktuellen Upload hinzu
    upload_tracker[user_id].append(now)

    return True, "Rate Limit OK"


def validate_zip_file(zip_path, upload_type="web_upload", user_id=None):
    """
    Validiert eine ZIP-Datei auf Sicherheitsrisiken.
    Gibt (is_valid, message) zurück.
    """
    # Hole die entsprechenden Limits für den Upload-Typ
    limits = UPLOAD_LIMITS.get(upload_type, UPLOAD_LIMITS["web_upload"])

    # Prüfe Rate Limiting wenn user_id gegeben
    if user_id:
        rate_ok, rate_msg = check_rate_limit(user_id, upload_type)
        if not rate_ok:
            return False, rate_msg

    # Prüfe ZIP-Dateigröße
    zip_size = os.path.getsize(zip_path)
    if zip_size > limits["max_zip_size"]:
        return (
            False,
            f"ZIP-Datei ist zu groß (max. {limits['max_zip_size']/1024/1024:.1f} MB)",
        )

    try:
        # Prüfe, ob es sich um eine gültige ZIP-Datei handelt
        if not zipfile.is_zipfile(zip_path):
            return False, "Keine gültige ZIP-Datei"

        # Öffne ZIP und prüfe Inhalt
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Prüfe auf zu viele Dateien
            file_count = len(zip_ref.namelist())
            if file_count > limits["max_files_in_zip"]:
                return (
                    False,
                    f"ZIP enthält zu viele Dateien (max. {limits['max_files_in_zip']})",
                )

            # Prüfe auf verdächtige Dateinamen und Directory Traversal
            total_size = 0
            for info in zip_ref.infolist():
                filename = info.filename

                # Prüfe Dateiname auf Sicherheit
                is_safe, safe_msg = is_safe_filename(filename, upload_type)
                if not is_safe:
                    return False, f"Unsichere Datei gefunden: {filename} - {safe_msg}"

                # Prüfe einzelne Dateigröße
                if info.file_size > limits["max_file_size"]:
                    return (
                        False,
                        f"Einzelne Datei zu groß: {filename} ({info.file_size/1024/1024:.1f} MB)",
                    )

                # Sammle Gesamtgröße für ZIP-Bomb-Schutz
                total_size += info.file_size

                # Prüfe auf ZIP-Bomb (entpackte Größe vs. komprimierte Größe)
                if total_size > limits["max_extracted_size"]:
                    return (
                        False,
                        f"Entpackte Größe überschreitet Limit ({total_size/1024/1024:.1f} MB > {limits['max_extracted_size']/1024/1024:.1f} MB)",
                    )

                # Zusätzlicher ZIP-Bomb-Schutz: Kompressionsverhältnis prüfen
                if info.compress_size > 0:
                    compression_ratio = info.file_size / info.compress_size
                    if (
                        compression_ratio > 100
                    ):  # Verdächtig hohes Kompressionsverhältnis
                        return (
                            False,
                            f"Verdächtig hohes Kompressionsverhältnis bei {filename} (ZIP-Bomb-Verdacht)",
                        )

        return (
            True,
            f"ZIP-Datei ist sicher ({file_count} Dateien, {total_size/1024/1024:.1f} MB entpackt)",
        )

    except Exception as e:
        return False, f"Fehler bei der Validierung: {str(e)}"


def scan_file_content(file_path, upload_type="web_upload"):
    """
    Scannt den Inhalt einer Datei auf verdächtige Muster.
    Verwendet Whitelist-Ansatz für MIME-Types.
    """
    try:
        # MIME-Type-Erkennung
        try:
            file_type = magic.from_file(file_path, mime=True)
        except Exception:
            # Fallback wenn python-magic nicht verfügbar ist
            import mimetypes

            file_type, _ = mimetypes.guess_type(file_path)
            if not file_type:
                file_type = "application/octet-stream"

        # Bestimme Dateikategorie basierend auf Dateiname
        filename = os.path.basename(file_path)
        file_category = get_file_category(filename, file_type)

        # Prüfe ob MIME-Type in der Whitelist ist
        if file_category and file_category in ALLOWED_MIME_TYPES:
            if file_type not in ALLOWED_MIME_TYPES[file_category]:
                return (
                    False,
                    f"MIME-Type {file_type} stimmt nicht mit Dateierweiterung überein",
                )
        else:
            return False, f"Unerlaubter MIME-Type: {file_type}"

        # Prüfe dateityp-spezifische Größenlimits
        file_size = os.path.getsize(file_path)
        if file_category in FILE_TYPE_LIMITS:
            if file_size > FILE_TYPE_LIMITS[file_category]:
                return (
                    False,
                    f"Datei überschreitet Limit für {file_category} ({file_size/1024/1024:.1f} MB)",
                )

        # Prüfe Datei-Hash gegen bekannte Malware-Hashes
        file_hash = calculate_file_hash(file_path)

        # In Produktion: Abfrage gegen Malware-Datenbank (VirusTotal API, etc.)
        known_malware_hashes = []  # Platzhalter für echte Malware-Hash-Datenbank

        if file_hash in known_malware_hashes:
            return False, "Datei entspricht bekannter Malware"

        # Erweiterte Heuristiken für verschiedene Dateitypen
        if file_category == "image":
            return validate_image_file(file_path)
        elif file_category == "document":
            return validate_document_file(file_path)
        elif file_category == "code":
            return validate_code_file(file_path)

        return True, f"Datei ist sicher ({file_type})"

    except Exception as e:
        return False, f"Fehler beim Scannen der Datei: {str(e)}"


def validate_image_file(file_path):
    """Spezielle Validierung für Bilddateien"""
    try:
        with open(file_path, "rb") as f:
            content = f.read(4096)  # Lese die ersten 4KB

            # Prüfe auf versteckte ausführbare Dateien in Bildern
            if content.startswith(b"MZ"):  # Windows PE Header
                return False, "Versteckte ausführbare Datei in Bild erkannt"

            # Prüfe auf verdächtige Skripte in SVG-Dateien
            if file_path.lower().endswith(".svg"):
                if b"<script" in content.lower() or b"javascript:" in content.lower():
                    return False, "Verdächtiger JavaScript-Code in SVG erkannt"

        return True, "Bilddatei ist sicher"
    except Exception as e:
        return False, f"Fehler bei Bildvalidierung: {str(e)}"


def validate_document_file(file_path):
    """Spezielle Validierung für Dokumentdateien"""
    try:
        with open(file_path, "rb") as f:
            content = f.read(8192)  # Lese die ersten 8KB

            # Prüfe auf Makros in Office-Dokumenten (einfache Heuristik)
            if any(
                keyword in content.lower()
                for keyword in [b"macro", b"vba", b"autoopen"]
            ):
                return False, "Verdächtige Makros in Dokument erkannt"

        return True, "Dokumentdatei ist sicher"
    except Exception as e:
        return False, f"Fehler bei Dokumentvalidierung: {str(e)}"


def validate_code_file(file_path):
    """Spezielle Validierung für Code-Dateien"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(10000)  # Lese die ersten 10KB

            # Prüfe auf verdächtige Code-Muster
            suspicious_patterns = [
                r"eval\s*\(",
                r"exec\s*\(",
                r"system\s*\(",
                r"shell_exec\s*\(",
                r"passthru\s*\(",
                r"base64_decode\s*\(",
                r"__import__\s*\(",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return False, f"Verdächtiges Code-Muster gefunden: {pattern}"

        return True, "Code-Datei ist sicher"
    except Exception as e:
        return False, f"Fehler bei Code-Validierung: {str(e)}"


def calculate_file_hash(file_path):
    """Berechnet den SHA-256 Hash einer Datei"""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Lese die Datei in Blöcken, um Speicherverbrauch zu minimieren
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)

    return sha256.hexdigest()


def validate_file_upload(
    file_path, upload_type="web_upload", user_id=None, detailed=False
):
    """
    Führt eine vollständige Sicherheitsvalidierung für eine hochgeladene Datei durch.
    Kombiniert Dateinamen-, Größen- und Inhaltsüberprüfung.

    Args:
        file_path: Pfad zur Datei
        upload_type: Art des Uploads (web_upload, api_upload, admin_upload)
        user_id: Benutzer-ID für Rate Limiting
        detailed: Wenn True, gibt detaillierte Informationen zurück

    Returns:
        Wenn detailed=False: (is_safe: bool, message: str)
        Wenn detailed=True: (is_safe: bool, detailed_info: dict)
    """
    # Hole die entsprechenden Limits für den Upload-Typ
    limits = UPLOAD_LIMITS.get(upload_type, UPLOAD_LIMITS["web_upload"])

    # Sammle detaillierte Informationen
    validation_info = {
        "filename": os.path.basename(file_path),
        "file_path": file_path,
        "file_size": os.path.getsize(file_path),
        "upload_type": upload_type,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "warnings": [],
        "errors": [],
        "is_safe": True,
        "risk_level": "low",  # low, medium, high, critical
        "recommendations": [],
    }

    # Prüfe Rate Limiting wenn user_id gegeben
    if user_id:
        rate_ok, rate_msg = check_rate_limit(user_id, upload_type)
        validation_info["checks"]["rate_limiting"] = {
            "passed": rate_ok,
            "message": rate_msg,
            "details": f"User {user_id} - {rate_msg}",
        }
        if not rate_ok:
            validation_info["is_safe"] = False
            validation_info["risk_level"] = "high"
            validation_info["errors"].append(f"Rate Limit: {rate_msg}")
            if not detailed:
                return False, rate_msg

    # Prüfe Dateiname
    filename = validation_info["filename"]
    is_safe, safe_msg = is_safe_filename(filename, upload_type)
    validation_info["checks"]["filename"] = {
        "passed": is_safe,
        "message": safe_msg,
        "details": f"Dateiname '{filename}' geprüft auf verdächtige Muster",
    }

    if not is_safe:
        validation_info["is_safe"] = False
        validation_info["risk_level"] = "high"
        validation_info["errors"].append(f"Unsicherer Dateiname: {safe_msg}")
        validation_info["recommendations"].append(
            "Benennen Sie die Datei um und entfernen Sie verdächtige Zeichen"
        )
        if not detailed:
            return False, f"Verdächtiger Dateiname: {filename} - {safe_msg}"

    # Prüfe Dateigröße basierend auf Upload-Typ
    file_size = validation_info["file_size"]
    size_check = file_size <= limits["max_file_size"]
    validation_info["checks"]["file_size"] = {
        "passed": size_check,
        "current_size_mb": round(file_size / 1024 / 1024, 2),
        "max_size_mb": round(limits["max_file_size"] / 1024 / 1024, 1),
        "message": f"Dateigröße: {file_size/1024/1024:.2f} MB (max. {limits['max_file_size']/1024/1024:.1f} MB)",
    }

    if not size_check:
        validation_info["is_safe"] = False
        validation_info["risk_level"] = "medium"
        validation_info["errors"].append(f"Datei zu groß: {file_size/1024/1024:.2f} MB")
        validation_info["recommendations"].append(
            f"Reduzieren Sie die Dateigröße auf unter {limits['max_file_size']/1024/1024:.1f} MB"
        )
        if not detailed:
            return (
                False,
                f"Datei ist zu groß (max. {limits['max_file_size']/1024/1024:.1f} MB)",
            )

    # Prüfe Dateiinhalt
    content_safe, content_msg = scan_file_content(file_path, upload_type)
    validation_info["checks"]["content_scan"] = {
        "passed": content_safe,
        "message": content_msg,
        "details": "MIME-Type und Inhaltsprüfung durchgeführt",
    }

    if not content_safe:
        validation_info["is_safe"] = False
        if "malware" in content_msg.lower() or "executable" in content_msg.lower():
            validation_info["risk_level"] = "critical"
        elif "verdächtig" in content_msg.lower():
            validation_info["risk_level"] = "high"
        else:
            validation_info["risk_level"] = "medium"
        validation_info["errors"].append(f"Inhaltsprüfung: {content_msg}")
        validation_info["recommendations"].append(
            "Überprüfen Sie den Dateiinhalt und entfernen Sie verdächtige Elemente"
        )
        if not detailed:
            return False, content_msg

    # Zusätzliche Informationen für Web-Interface
    if detailed:
        # Dateikategorie bestimmen
        file_category = get_file_category(filename)
        validation_info["file_category"] = file_category

        # GitHub-spezifische Prüfungen
        validation_info["github_compatibility"] = check_github_compatibility(
            file_path, filename
        )

        # Sicherheitsbewertung
        validation_info["security_score"] = calculate_security_score(validation_info)

        # Empfehlungen für sicheren Upload
        if validation_info["is_safe"]:
            validation_info["recommendations"].extend(
                [
                    "Datei ist sicher für GitHub Upload",
                    "Stellen Sie sicher, dass keine sensiblen Daten enthalten sind",
                    "Überprüfen Sie die Repository-Berechtigungen",
                ]
            )

    if detailed:
        return validation_info["is_safe"], validation_info
    else:
        return True, f"Datei ist sicher ({file_size/1024/1024:.1f} MB)"


def check_github_compatibility(file_path, filename):
    """Prüft GitHub-spezifische Kompatibilität"""
    compatibility = {
        "is_compatible": True,
        "warnings": [],
        "file_size_ok": True,
        "filename_ok": True,
        "encoding_ok": True,
        "line_endings_ok": True,
    }

    file_size = os.path.getsize(file_path)

    # GitHub Dateigrößenlimits
    if file_size > 100 * 1024 * 1024:  # 100 MB
        compatibility["is_compatible"] = False
        compatibility["file_size_ok"] = False
        compatibility["warnings"].append("Datei überschreitet GitHub's 100MB Limit")
    elif file_size > 25 * 1024 * 1024:  # 25 MB
        compatibility["warnings"].append(
            "Große Datei - GitHub empfiehlt Git LFS für Dateien >25MB"
        )

    # Problematische Dateinamen für GitHub
    problematic_chars = ["<", ">", ":", '"', "|", "?", "*"]
    if any(char in filename for char in problematic_chars):
        compatibility["filename_ok"] = False
        compatibility["warnings"].append(
            "Dateiname enthält für GitHub problematische Zeichen"
        )

    # Prüfe auf binäre vs. Text-Dateien
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(1024)  # Teste ersten KB
        compatibility["encoding_ok"] = True
    except UnicodeDecodeError:
        # Binärdatei - das ist OK
        compatibility["encoding_ok"] = True
    except Exception:
        compatibility["encoding_ok"] = False
        compatibility["warnings"].append("Encoding-Probleme erkannt")

    return compatibility


def calculate_security_score(validation_info):
    """Berechnet einen Sicherheitsscore von 0-100"""
    score = 100

    # Abzüge basierend auf Risiko-Level
    risk_penalties = {"low": 0, "medium": -20, "high": -50, "critical": -80}

    score += risk_penalties.get(validation_info["risk_level"], 0)

    # Abzüge für fehlgeschlagene Checks
    for check_name, check_info in validation_info["checks"].items():
        if not check_info.get("passed", True):
            if check_name == "rate_limiting":
                score -= 30
            elif check_name == "filename":
                score -= 25
            elif check_name == "file_size":
                score -= 15
            elif check_name == "content_scan":
                score -= 40

    # Bonus für bestandene Checks
    passed_checks = sum(
        1 for check in validation_info["checks"].values() if check.get("passed", False)
    )
    score += passed_checks * 2

    return max(0, min(100, score))


def get_detailed_file_info(file_path):
    """Sammelt detaillierte Dateiinformationen für Web-Interface"""
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    info = {
        "filename": filename,
        "file_size": file_size,
        "file_size_formatted": format_file_size(file_size),
        "file_extension": os.path.splitext(filename)[1].lower(),
        "file_category": get_file_category(filename),
        "created_time": os.path.getctime(file_path),
        "modified_time": os.path.getmtime(file_path),
        "is_binary": is_binary_file(file_path),
        "estimated_upload_time": estimate_upload_time(file_size),
    }

    return info


def format_file_size(size_bytes):
    """Formatiert Dateigröße human-readable"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def is_binary_file(file_path):
    """Prüft ob Datei binär ist"""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except:
        return True


def estimate_upload_time(file_size, connection_speed_mbps=10):
    """Schätzt Upload-Zeit basierend auf Dateigröße"""
    size_mb = file_size / (1024 * 1024)
    time_seconds = size_mb / connection_speed_mbps

    if time_seconds < 1:
        return "< 1 Sekunde"
    elif time_seconds < 60:
        return f"{time_seconds:.0f} Sekunden"
    else:
        minutes = time_seconds / 60
        return f"{minutes:.1f} Minuten"


def validate_upload_directory(directory_path, upload_type="web_upload", user_id=None):
    """
    Validiert alle Dateien in einem Verzeichnis.
    Nützlich nach dem Entpacken eines ZIP-Archivs.
    """
    results = []
    total_files = 0
    total_size = 0

    for root, _, files in os.walk(directory_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_size = os.path.getsize(file_path)
            total_files += 1
            total_size += file_size

            is_safe, message = validate_file_upload(file_path, upload_type, user_id)
            results.append(
                {
                    "file": file_path,
                    "is_safe": is_safe,
                    "message": message,
                    "size": file_size,
                }
            )

    # Prüfe, ob alle Dateien sicher sind
    all_safe = all(result["is_safe"] for result in results)

    if all_safe:
        return (
            True,
            f"Alle {total_files} Dateien sind sicher (Gesamt: {total_size/1024/1024:.1f} MB)",
        )
    else:
        # Finde die erste unsichere Datei
        unsafe_file = next(result for result in results if not result["is_safe"])
        return (
            False,
            f"Unsichere Datei gefunden: {unsafe_file['file']} - {unsafe_file['message']}",
        )


# Hilfsfunktion für einfache API-Nutzung
def create_security_validator(upload_type="web_upload"):
    """
    Factory-Funktion zur Erstellung eines konfigurierten Validators
    """

    def validator(file_path, user_id=None):
        if os.path.isfile(file_path):
            if file_path.lower().endswith(".zip"):
                return validate_zip_file(file_path, upload_type, user_id)
            else:
                return validate_file_upload(file_path, upload_type, user_id)
        elif os.path.isdir(file_path):
            return validate_upload_directory(file_path, upload_type, user_id)
        else:
            return False, "Pfad existiert nicht"

    return validator


# Beispiel für die Nutzung:
# web_validator = create_security_validator('web_upload')
# api_validator = create_security_validator('api_upload')
# admin_validator = create_security_validator('admin_upload')
#
# is_safe, message = web_validator('/path/to/file.zip', user_id='user123')
