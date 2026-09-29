# Bildscanner

Scannt Bilder (lokal oder in der Dropbox), erkennt mit Claude, **was** drauf ist,
ermittelt, **woher** sie kommen, und schlägt vor, **wohin** sie gehören und **was als Nächstes** zu tun ist.

| Frage | Woher die Antwort kommt |
|---|---|
| **Was ist das?** | Claude schaut sich das Bild an: Rechnung, Dokument, Urlaubsfoto, Personen, Ferienhaus, Hintergrund, Screenshot, Grafik, Sonstiges |
| **Woher kommt es?** | EXIF (Kamera, Aufnahmedatum, GPS → Link zur Karte), Dateiname (`Screenshot_…`, WhatsApp `IMG-…-WA…`, `IMG_`/`PXL_` …) plus Claudes Einschätzung |
| **Wohin gehört es?** | Zielordner je Kategorie, z. B. `Rechnungen/2026/09/2026-09-03-baumarkt-rechnung.jpg` |
| **Wie geht's weiter?** | 1–3 Handlungsempfehlungen pro Bild; bei Rechnungen Aussteller, Datum, Betrag, Nummer → `rechnungen.csv` |

Duplikate (gleicher Inhalt) und kaputte Dateien werden erkannt. Bereits analysierte Bilder
landen in einem Cache, damit sie beim nächsten Lauf nichts mehr kosten.

## Einrichtung

```bash
cd tools/bildscanner
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # https://console.anthropic.com
```

### Dropbox-Zugang

1. Auf <https://www.dropbox.com/developers/apps> eine App anlegen („Scoped access“, „Full Dropbox“).
2. Unter *Permissions* anhaken: `files.metadata.read`, `files.content.read`, `files.content.write` → *Submit*.
3. Unter *Settings* → *Generated access token* → *Generate*, dann:

```bash
export DROPBOX_ACCESS_TOKEN=sl....
```

Dieser Token läuft nach ein paar Stunden ab. Für Dauerbetrieb stattdessen `DROPBOX_REFRESH_TOKEN`,
`DROPBOX_APP_KEY` und `DROPBOX_APP_SECRET` setzen.

## Benutzung

```bash
# 1) Nur anschauen – nichts wird verändert
python bildscanner.py dropbox "/Kamera-Uploads"
python bildscanner.py lokal ~/Bilder/Unsortiert

# Bericht öffnen: bildscanner-bericht/bericht.html

# 2) Vorschläge umsetzen (verschieben + umbenennen)
python bildscanner.py dropbox "/Kamera-Uploads" --anwenden --ziel "/Sortiert"
```

Wichtige Optionen:

| Option | Bedeutung |
|---|---|
| `--anwenden` | Dateien wirklich verschieben/umbenennen. Ohne diese Option wird **nur** ein Bericht erstellt. |
| `--ziel PFAD` | Basisordner der Sortierung (Standard: `<ordner>/Sortiert`). Bilder darunter werden beim Scannen übersprungen. |
| `--max N` | Nur die ersten N Bilder, gut zum Ausprobieren. |
| `--ziele datei.json` | Eigene Zielordner je Kategorie, siehe `ziele.beispiel.json`. Platzhalter: `{jahr}`, `{monat}`, `{ort}`. |
| `--nicht-rekursiv` | Unterordner nicht durchsuchen. |
| `--effort low/medium/high` | Wie gründlich Claude nachdenkt. `low` reicht meistens, `medium` hilft bei schwer lesbaren Belegen. |
| `--ausgabe ORDNER` | Wohin Berichte und Cache geschrieben werden. |

## Ausgabe

In `bildscanner-bericht/`:

- `bericht.html`: Übersicht mit Vorschaubildern, Filter nach Kategorie, Herkunft, Karte, Zielpfad und nächsten Schritten
- `ergebnisse.csv` / `ergebnisse.json`: alle Ergebnisse (CSV öffnet sich direkt in Excel)
- `rechnungen.csv`: alle erkannten Rechnungen mit Betrag, z. B. für den Steuerberater
- `cache.json`: bereits analysierte Bilder

## Kosten und Datenschutz

Jedes Bild wird verkleinert (max. 1568 px) an die Claude-API geschickt. Das kostet grob
1–2 Cent pro Bild (1.000 Bilder ≈ 10–20 €). Wiederholte Läufe nutzen den Cache.
Verschoben wird nur mit `--anwenden`. In der Dropbox wird bei Namensgleichheit automatisch umbenannt,
es wird nichts überschrieben oder gelöscht.
