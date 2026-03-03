# Cron Jobs Documentation Generator

Ein Ansible-basiertes System zur automatischen Dokumentation von Cronjobs auf mehreren Servern mit Python-basierter Markdown-Verarbeitung.

## Features

✅ Automatische Erfassung von Cronjobs von mehreren Servern
✅ Markdown-Dokumentation mit strukturiertem Format
✅ Statische Bereiche können manuell gepflegt werden (werden nicht überschrieben)
✅ Automatische Zeitstempel bei jeder Aktualisierung
✅ Unterstützung für User-Crontabs, System-Crontabs und /etc/cron.d Dateien

## Struktur

```
.
├── collect_crons.yml          # Task-Datei für Cronjob-Erfassung
├── generate_cron_docs.yml     # Main-Playbook (orchestriert alles)
├── process_crons.py           # Python-Skript für Markdown-Verarbeitung
├── inventory.ini              # Ansible-Inventory (Server-Liste)
└── docs/                       # Generierte Dokumentation (wird erstellt)
    └── <hostname>_crons.md
```

## Installation

### Anforderungen

- Ansible 2.9+
- Python 3.6+
- SSH-Zugang zu den Zielservern
- Sudo-Ausnahme für `crontab -l` und `/etc/crontab` Lesezugriff

### Setup

1. Repository klonen/aktualisieren:
```bash
cd /workspaces/kalle-ansible
```

2. Inventory-Datei anpassen (`inventory.ini`):
```ini
[webservers]
web-01 ansible_host=192.168.1.10 ansible_user=deploy
web-02 ansible_host=192.168.1.11 ansible_user=deploy
```

3. SSH-Zugang testen:
```bash
ansible all -i inventory.ini -m ping
```

## Verwendung

### Dokumentation generieren

```bash
ansible-playbook generate_cron_docs.yml -i inventory.ini
```

Dies erzeugt Markdown-Dateien im `docs/` Verzeichnis:
- `web-01_crons.md`
- `web-02_crons.md`
- usw.

### Output-Format

Jede generierte Markdown-Datei hat eines dieser Formats:

```markdown
# Cron Jobs Documentation - web-01

_Last updated: 2024-03-03 14:30:00_

[STATIC_START]
## Beschreibung (manuell hinzugefügt)
Dieser Server ist für XYZ verantwortlich.

Wichtige Informationen:
- Backup täglich um 2 Uhr
- Wartung jeden Sonntag
[STATIC_END]

## User Crontab

\`\`\`cron
0 2 * * * /usr/local/bin/backup.sh
\`\`\`

## System Crontab

\`\`\`cron
SHELL=/bin/bash
0 0 * * * root /opt/scripts/maintenance.sh
\`\`\`

## Cron.d Files

\`\`\`cron
=== /etc/cron.d/sysstat ===
*/10 * * * * root /usr/lib64/sa/sa1 1 1
\`\`\`
```

## Statische Bereiche schützen

Die Markdown-Dateien können einen statischen Bereich enthalten, der bei jeder Aktualisierung erhalten bleibt. Dieser wird mit speziellen Markern gekennzeichnet:

```markdown
[STATIC_START]
Hier können Sie manuell weitere Informationen hinzufügen.
Diese Zeilen werden bei der nächsten Aktualisierung nicht überschrieben.
[STATIC_END]
```

**Wie es funktioniert:**

1. Das Python-Skript `process_crons.py` liest die existierende Markdown-Datei
2. Es extrahiert den Text zwischen `[STATIC_START]` und `[STATIC_END]`
3. Die Cronjobs werden neu eingefügt
4. Der statische Bereich wird am Ende wieder eingefügt

## Python-Skript Details

### CronMarkdownProcessor Klasse

```python
processor = CronMarkdownProcessor("path/to/output.md")

# Statischen Bereich extrahieren
static = processor.extract_static_section()

# Markdown generieren und speichern
processor.update_markdown({
    "hostname": "web-01",
    "user_crontab": "0 2 * * * /backup.sh",
    "system_crontab": "...",
    "cron_d_files": "..."
})
```

## Erweiterte Konfiguration

### Custom Output-Verzeichnis

In `generate_cron_docs.yml` anpassen:

```yaml
vars:
  docs_path: "/path/to/custom/docs"
```

### Nur bestimmte Server aktualisieren

```bash
ansible-playbook generate_cron_docs.yml -i inventory.ini -l webservers
```

### Mit Verbose-Output

```bash
ansible-playbook generate_cron_docs.yml -i inventory.ini -vv
```

## Fehlerbehandlung

| Problem | Lösung |
|---------|--------|
| SSH-Verbindung fehlgeschlagen | Inventory-Host überprüfen, SSH-Schlüssel testen |
| "Permission denied" für /etc/crontab | Ansible-Benutzer benötigt Sudo-Zugang |
| Python-Fehler beim Skript | Python 3.6+ auf localhost überprüfen |
| Markdown sieht seltsam aus | Encoding-Probleme - UTF-8 überprüfen |

## Todos & Verbesserungen

- [ ] Filtering von Cronjobs nach Muster
- [ ] HTML-Report-Generierung
- [ ] Benachrichtigungen bei Cronjob-Änderungen
- [ ] Versionskontrolle der Dokumentation
- [ ] Integration mit Git (Auto-Commit)

## Lizenz

MIT