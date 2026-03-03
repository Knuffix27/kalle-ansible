#!/usr/bin/env python3
"""
generate_cron_docs.py
=====================
Liest eine JSON-Datei mit Cron-Daten (gesammelt von Ansible) ein und
generiert eine Markdown-Dokumentationsdatei pro Server.

Aufbau der generierten Markdown-Datei:
  1. AUTO-GENERATED-Bereich  → wird bei jedem Lauf neu geschrieben
  2. STATIC-Bereich          → wird beim ersten Lauf angelegt und danach
                               NIEMALS überschrieben (kann manuell befüllt werden)

Verwendung:
  python3 generate_cron_docs.py --input /tmp/server1.json --output-dir ./docs
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Sektion-Marker
# ---------------------------------------------------------------------------

STATIC_START = "<!-- STATIC_START -->"
STATIC_END = "<!-- STATIC_END -->"
AUTO_START = "<!-- AUTO_GENERATED_START -->"
AUTO_END = "<!-- AUTO_GENERATED_END -->"

DEFAULT_STATIC_CONTENT = """\
{static_start}

## Notizen

> Dieser Bereich wird **nicht** automatisch überschrieben.
> Hier können manuelle Anmerkungen, Kontakte oder Hinweise eingetragen werden.

{static_end}
""".format(static_start=STATIC_START, static_end=STATIC_END)

# ---------------------------------------------------------------------------
# Hilfsfunktionen – Parsing
# ---------------------------------------------------------------------------

SPECIAL_SCHEDULES = {
    "@reboot": "Bei Systemstart",
    "@yearly": "Jährlich (1. Jan. 00:00)",
    "@annually": "Jährlich (1. Jan. 00:00)",
    "@monthly": "Monatlich (1. des Monats, 00:00)",
    "@weekly": "Wöchentlich (Sonntag, 00:00)",
    "@daily": "Täglich (00:00)",
    "@midnight": "Täglich Mitternacht",
    "@hourly": "Stündlich",
}


def format_schedule(schedule: str) -> str:
    """Gibt einen lesbaren Hinweis für @-Sonderzeitpläne zurück."""
    return SPECIAL_SCHEDULES.get(schedule.lower(), schedule)


def parse_crontab_lines(text: str, has_user_field: bool = False) -> dict:
    """
    Zerlegt einen Crontab-Text in strukturierte Daten.

    Rückgabe:
        {
            'env_vars': [{'key': str, 'value': str}, ...],
            'jobs':     [{'schedule': str, 'user': str|None, 'command': str, 'description': str}, ...]
        }
    """
    result: dict = {"env_vars": [], "jobs": []}

    if not text or not text.strip():
        return result

    pending_comments: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        # Leerzeile → ausstehende Kommentare verwerfen
        if not line:
            pending_comments = []
            continue

        # Kommentarzeile
        if line.lstrip().startswith("#"):
            comment = line.lstrip()[1:].strip()
            if comment:
                pending_comments.append(comment)
            continue

        # Umgebungsvariable (KEY=VALUE)
        env_match = re.match(r"^(\w+)\s*=\s*(.*)$", line)
        if env_match:
            result["env_vars"].append(
                {"key": env_match.group(1), "value": env_match.group(2).strip("'\"")}
            )
            pending_comments = []
            continue

        # Cron-Job-Zeile
        parts = line.split()
        description = " ".join(pending_comments)
        pending_comments = []

        if has_user_field:
            # Format: min hour dom mon dow USER command…
            if len(parts) >= 7:
                result["jobs"].append(
                    {
                        "schedule": " ".join(parts[:5]),
                        "user": parts[5],
                        "command": " ".join(parts[6:]),
                        "description": description,
                    }
                )
            # Format: @special USER command…
            elif len(parts) >= 3 and parts[0].startswith("@"):
                result["jobs"].append(
                    {
                        "schedule": parts[0],
                        "user": parts[1],
                        "command": " ".join(parts[2:]),
                        "description": description,
                    }
                )
        else:
            # Format: min hour dom mon dow command…
            if len(parts) >= 6:
                result["jobs"].append(
                    {
                        "schedule": " ".join(parts[:5]),
                        "user": None,
                        "command": " ".join(parts[5:]),
                        "description": description,
                    }
                )
            # Format: @special command…
            elif len(parts) >= 2 and parts[0].startswith("@"):
                result["jobs"].append(
                    {
                        "schedule": parts[0],
                        "user": None,
                        "command": " ".join(parts[1:]),
                        "description": description,
                    }
                )

    return result


def parse_user_crontabs(raw: str) -> list[dict]:
    """
    Verarbeitet die USER:name / END_USER formatierte Ausgabe des Ansible-Tasks.

    Rückgabe: [{'user': str, 'crontab': str}, ...]
    """
    users: list[dict] = []
    if not raw or not raw.strip():
        return users

    current_user: Optional[str] = None
    current_lines: list[str] = []

    for line in raw.splitlines():
        if line.startswith("USER:"):
            current_user = line[5:].strip()
            current_lines = []
        elif line == "END_USER":
            if current_user:
                users.append({"user": current_user, "crontab": "\n".join(current_lines)})
            current_user = None
            current_lines = []
        elif current_user is not None:
            current_lines.append(line)

    return users


# ---------------------------------------------------------------------------
# Hilfsfunktionen – Formatierung
# ---------------------------------------------------------------------------


def _escape_md(text: str) -> str:
    """Escaped das Pipe-Symbol für Markdown-Tabellen."""
    return text.replace("|", "\\|")


def jobs_to_markdown_table(jobs: list[dict], has_user_field: bool = False) -> str:
    """Wandelt eine Liste von Cron-Jobs in eine Markdown-Tabelle um."""
    if not jobs:
        return ""

    if has_user_field:
        lines = [
            "| Zeitplan | Benutzer | Befehl | Beschreibung |",
            "|----------|----------|--------|--------------|",
        ]
        for job in jobs:
            schedule = _escape_md(format_schedule(job["schedule"]))
            user = _escape_md(job.get("user") or "")
            command = _escape_md(job["command"])
            desc = _escape_md(job.get("description") or "")
            lines.append(f"| `{schedule}` | `{user}` | `{command}` | {desc} |")
    else:
        lines = [
            "| Zeitplan | Befehl | Beschreibung |",
            "|----------|--------|--------------|",
        ]
        for job in jobs:
            schedule = _escape_md(format_schedule(job["schedule"]))
            command = _escape_md(job["command"])
            desc = _escape_md(job.get("description") or "")
            lines.append(f"| `{schedule}` | `{command}` | {desc} |")

    return "\n".join(lines)


def format_crontab_section(
    title: str,
    text: str,
    has_user_field: bool = False,
    heading_level: int = 3,
) -> str:
    """
    Formatiert einen Crontab-Block als Markdown-Abschnitt.
    Gibt einen Leerstring zurück, wenn keine auswertbaren Einträge vorhanden sind.
    """
    if not text or not text.strip():
        return ""

    parsed = parse_crontab_lines(text, has_user_field=has_user_field)

    if not parsed["jobs"] and not parsed["env_vars"]:
        return ""

    prefix = "#" * heading_level
    md = f"\n{prefix} {title}\n\n"

    if parsed["env_vars"]:
        md += "**Umgebungsvariablen:**\n\n"
        for ev in parsed["env_vars"]:
            md += f"- `{ev['key']}={ev['value']}`\n"
        md += "\n"

    if parsed["jobs"]:
        table = jobs_to_markdown_table(parsed["jobs"], has_user_field=has_user_field)
        if table:
            md += table + "\n"

    return md


# ---------------------------------------------------------------------------
# Kern: Auto-Sektion generieren
# ---------------------------------------------------------------------------


def generate_auto_section(data: dict) -> str:
    """Erstellt den vollständigen automatisch generierten Markdown-Block."""
    hostname = data.get("hostname", "unknown")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = f"{AUTO_START}\n\n"
    md += f"# Cronjob-Dokumentation: {hostname}\n\n"
    md += (
        f"> **Automatisch generiert** am {now}  \n"
        f"> Änderungen in diesem Bereich werden beim nächsten Playbook-Lauf **überschrieben**.\n\n"
    )
    md += "---\n\n"

    has_content = False

    # Root-Crontab
    section = format_crontab_section(
        "Root Crontab (`crontab -l`)",
        data.get("root_crontab", ""),
        heading_level=2,
    )
    if section:
        md += section
        has_content = True

    # /etc/crontab (hat Benutzer-Feld)
    section = format_crontab_section(
        "/etc/crontab",
        data.get("etc_crontab", ""),
        has_user_field=True,
        heading_level=2,
    )
    if section:
        md += section
        has_content = True

    # Benutzer-Crontabs
    user_crontabs = parse_user_crontabs(data.get("user_crontabs_raw", ""))
    user_sections = ""
    for entry in user_crontabs:
        if entry["user"] == "root":
            # Root wurde bereits oben behandelt
            continue
        section = format_crontab_section(
            f"Crontab: `{entry['user']}`",
            entry["crontab"],
            heading_level=3,
        )
        if section:
            user_sections += section
            has_content = True

    if user_sections:
        md += "\n## Benutzer-Crontabs\n" + user_sections

    # /etc/cron.d/ Dateien (haben Benutzer-Feld)
    cron_d_files = data.get("cron_d_files", [])
    cron_d_sections = ""
    for cron_file in cron_d_files:
        filename = os.path.basename(cron_file.get("filename", "unknown"))
        section = format_crontab_section(
            f"`{filename}`",
            cron_file.get("content", ""),
            has_user_field=True,
            heading_level=3,
        )
        if section:
            cron_d_sections += section
            has_content = True

    if cron_d_sections:
        md += "\n## /etc/cron.d/\n" + cron_d_sections

    # Cron-Verzeichnisse (nur Skript-Namen)
    cron_dirs = [
        ("cron_hourly", "/etc/cron.hourly/"),
        ("cron_daily", "/etc/cron.daily/"),
        ("cron_weekly", "/etc/cron.weekly/"),
        ("cron_monthly", "/etc/cron.monthly/"),
    ]
    dir_md = ""
    for key, dirname in cron_dirs:
        scripts = [s for s in data.get(key, []) if s.strip()]
        if scripts:
            dir_md += f"\n### {dirname}\n\n"
            for script in sorted(scripts):
                dir_md += f"- `{script}`\n"
            dir_md += "\n"

    if dir_md:
        md += "\n## Cron-Verzeichnisse\n" + dir_md
        has_content = True

    if not has_content:
        md += "*Keine Cronjobs gefunden.*\n\n"

    md += f"\n{AUTO_END}\n"
    return md


# ---------------------------------------------------------------------------
# Statische Sektion lesen / verwalten
# ---------------------------------------------------------------------------


def read_static_section(filepath: str) -> Optional[str]:
    """
    Liest die statische Sektion aus einer bereits vorhandenen Markdown-Datei.
    Gibt None zurück, wenn die Datei nicht existiert oder keine statische Sektion hat.
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError as exc:
        print(f"Warnung: Datei konnte nicht gelesen werden ({filepath}): {exc}", file=sys.stderr)
        return None

    start_idx = content.find(STATIC_START)
    end_idx = content.find(STATIC_END)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return content[start_idx : end_idx + len(STATIC_END)]

    return None


# ---------------------------------------------------------------------------
# Einstiegspunkt: Dokumentation generieren
# ---------------------------------------------------------------------------


def generate_documentation(data: dict, output_dir: str) -> str:
    """
    Generiert die Markdown-Dokumentation für einen Server und schreibt sie heraus.

    Ablauf:
      1. Vorhandene statische Sektion lesen (oder Standardtext verwenden).
      2. Auto-Sektion neu generieren.
      3. Beide Sektionen zusammenführen und schreiben.

    Rückgabe: Pfad zur geschriebenen Datei.
    """
    hostname = data.get("hostname", "unknown")
    safe_hostname = re.sub(r"[^\w\-.]", "_", hostname)
    output_file = os.path.join(output_dir, f"{safe_hostname}_crons.md")

    # Statische Sektion erhalten oder Standardinhalt verwenden
    static_section = read_static_section(output_file)
    if static_section is None:
        static_section = DEFAULT_STATIC_CONTENT

    # Automatisch generierten Abschnitt erzeugen
    auto_section = generate_auto_section(data)

    # Datei zusammensetzen: Auto-Sektion oben, statische Sektion unten
    final_content = auto_section + "\n\n" + static_section + "\n"

    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(final_content)

    return output_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Markdown-Dokumentation für Server-Cronjobs generieren (Ansible-Output)."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        metavar="JSON_FILE",
        help="Pfad zur JSON-Eingabedatei (von Ansible erzeugt)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        required=True,
        metavar="DIR",
        help="Ausgabeverzeichnis für die Markdown-Dateien",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Fehler: Eingabedatei nicht gefunden: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Fehler beim Lesen der Eingabedatei: {exc}", file=sys.stderr)
        sys.exit(1)

    output_file = generate_documentation(data, args.output_dir)
    print(f"Dokumentation geschrieben: {output_file}")


if __name__ == "__main__":
    main()
