# kalle-ansible

Ansible-basiertes Tooling zur automatischen Generierung von Cronjob-Dokumentation im Markdown-Format.

---

## Übersicht

```
kalle-ansible/
├── inventory/
│   └── hosts.ini.example     ← Beispiel-Inventory (nach hosts.ini kopieren)
├── playbooks/
│   └── cron_docs.yml         ← Ansible-Playbook (Verbindung + Datensammlung)
├── scripts/
│   └── generate_cron_docs.py ← Python-Skript (Markdown-Generierung)
├── docs/
│   └── <hostname>_crons.md   ← Generierte Dokumentationsdateien
└── README.md
```

---

## Funktionsweise

```
┌─────────────────────────────────────────────────────────────────┐
│  Ansible-Playbook (cron_docs.yml)                               │
│                                                                  │
│  1. Verbindet sich zu allen Hosts im Inventory                  │
│  2. Liest aus (remote):                                         │
│     - Root-Crontab (crontab -l)                                 │
│     - Alle Benutzer-Crontabs                                    │
│     - /etc/crontab                                              │
│     - /etc/cron.d/* (Dateiinhalte)                              │
│     - /etc/cron.{hourly,daily,weekly,monthly}/ (Skript-Listen)  │
│  3. Speichert Daten als JSON-Zwischendatei (lokal, /tmp)        │
│  4. Ruft Python-Skript pro Server auf                           │
│  5. Räumt JSON-Zwischendatei auf                                │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Python-Skript (generate_cron_docs.py)                          │
│                                                                  │
│  1. Liest JSON-Eingabe                                          │
│  2. Prüft, ob docs/<hostname>_crons.md bereits existiert        │
│     - Ja  → Statische Sektion (<!-- STATIC_START/END -->) lesen │
│     - Nein → Standard-Platzhalter verwenden                     │
│  3. Generiert Auto-Sektion (<!-- AUTO_GENERATED_START/END -->)  │
│  4. Schreibt: Auto-Sektion + Statische Sektion in Datei         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Aufbau der generierten Markdown-Datei

```markdown
<!-- AUTO_GENERATED_START -->

# Cronjob-Dokumentation: server01

> Automatisch generiert am 2024-01-15 10:30:00
> Änderungen in diesem Bereich werden beim nächsten Playbook-Lauf überschrieben.

---

## Root Crontab (`crontab -l`)

| Zeitplan      | Befehl                       | Beschreibung    |
|---------------|------------------------------|-----------------|
| `0 2 * * *`   | `/usr/local/bin/backup.sh`   | Nightly backup  |

## /etc/crontab

...

<!-- AUTO_GENERATED_END -->


<!-- STATIC_START -->

## Notizen

> Dieser Bereich wird **nicht** automatisch überschrieben.
> Hier können manuelle Anmerkungen, Kontakte oder Hinweise eingetragen werden.

<!-- STATIC_END -->
```

**Wichtig:** Nur der Block zwischen `<!-- STATIC_START -->` und `<!-- STATIC_END -->` bleibt bei jedem Lauf erhalten. Alles außerhalb der statischen Sektion wird überschrieben.

---

## Voraussetzungen

- Python 3.10+ (auf dem Ansible-Control-Node)
- Ansible 2.12+
- SSH-Zugang zu den Ziel-Servern
- `sudo`-Rechte auf den Ziel-Servern (für Benutzer-Crontabs)

---

## Einrichtung

```bash
# 1. Inventory anlegen
cp inventory/hosts.ini.example inventory/hosts.ini
# Datei editieren und eigene Server eintragen

# 2. SSH-Verbindung testen
ansible -i inventory/hosts.ini all -m ping

# 3. Playbook ausführen
ansible-playbook -i inventory/hosts.ini playbooks/cron_docs.yml
```

Die generierten Markdown-Dateien befinden sich anschließend unter `docs/`.

---

## Optionen

Variablen können per `-e` überschrieben werden:

```bash
# Anderes Ausgabeverzeichnis
ansible-playbook -i inventory/hosts.ini playbooks/cron_docs.yml \
  -e "docs_output_dir=/pfad/zum/wiki"

# Nur bestimmte Hosts
ansible-playbook -i inventory/hosts.ini playbooks/cron_docs.yml \
  --limit webserver
```

---

## Statische Sektion bearbeiten

Nach dem ersten Lauf enthält die generierte Datei einen Platzhalter für Notizen:

```markdown
<!-- STATIC_START -->

## Notizen

> Dieser Bereich wird **nicht** automatisch überschrieben.

<!-- STATIC_END -->
```

Dieser Bereich kann frei befüllt werden – Ansprechpartner, Abhängigkeiten, Hinweise zur Deaktivierung, etc. Er wird beim nächsten Playbook-Lauf **nicht** überschrieben.
