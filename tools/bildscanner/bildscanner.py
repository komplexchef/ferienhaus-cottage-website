#!/usr/bin/env python3
"""Bildscanner – erkennt, was auf Bildern ist, woher sie kommen und wohin sie gehören.

Quellen:  lokaler Ordner  oder  Dropbox-Ordner (z. B. "/Kamera-Uploads")
Analyse:  Claude (Bildinhalt) + EXIF/Dateiname/Dropbox-Metadaten (Herkunft)
Ergebnis: Bericht (HTML, JSON, CSV), Rechnungsliste (CSV) und – nur mit --anwenden –
          Verschieben/Umbenennen in die vorgeschlagene Ordnerstruktur.

Beispiele:
    python bildscanner.py lokal ~/Bilder/Unsortiert
    python bildscanner.py dropbox "/Kamera-Uploads"
    python bildscanner.py dropbox "/Kamera-Uploads" --anwenden --ziel "/Sortiert"
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from PIL import ExifTags, Image, ImageOps

try:  # iPhone-Fotos (HEIC) – optional
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

MODEL = "claude-opus-5-5"
BILD_ENDUNGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
MAX_KANTE = 1568  # längste Bildkante, die an Claude geht (spart Tokens, reicht für Belege)

KATEGORIEN = {
    "rechnung": "Rechnung / Quittung / Kassenbon / Beleg",
    "dokument": "Sonstiges Dokument (Brief, Vertrag, Formular, Ausweis, Notiz)",
    "urlaubsfoto": "Urlaubs- oder Reisefoto (Landschaft, Sehenswürdigkeit, Strand, Stadt)",
    "personen": "Foto mit Personen im Mittelpunkt (Familie, Freunde, Feier)",
    "ferienhaus": "Foto vom Ferienhaus / Cottage (Zimmer, Einrichtung, Garten, Außenansicht)",
    "hintergrund": "Hintergrundbild / Wallpaper / dekoratives Motiv ohne persönlichen Bezug",
    "screenshot": "Screenshot von Handy oder Computer",
    "grafik": "Grafik, Logo, Meme, Illustration, Design-Entwurf",
    "sonstiges": "Passt in keine andere Kategorie",
}

# Zielordner je Kategorie. Platzhalter: {jahr} {monat} {ort}
STANDARD_ZIELE = {
    "rechnung": "Rechnungen/{jahr}/{monat}",
    "dokument": "Dokumente/{jahr}",
    "urlaubsfoto": "Fotos/Urlaub/{jahr} {ort}",
    "personen": "Fotos/Personen/{jahr}",
    "ferienhaus": "Ferienhaus/Fotos",
    "hintergrund": "Hintergruende",
    "screenshot": "Screenshots/{jahr}",
    "grafik": "Grafiken",
    "sonstiges": "Unsortiert",
}

SYSTEM_PROMPT = f"""Du sortierst die Bildersammlung einer Privatperson, die nebenbei ein Ferienhaus vermietet.
Ordne jedes Bild genau einer Kategorie zu:
{chr(10).join(f"- {k}: {v}" for k, v in KATEGORIEN.items())}

Du bekommst zusätzlich technische Hinweise (Dateiname, EXIF-Kamera, Aufnahmedatum, GPS), die helfen
können, die Herkunft zu bestimmen (Handykamera, Screenshot, WhatsApp, Scan, Download aus dem Netz).
Wenn Bildinhalt und Hinweise sich widersprechen, gewichte den Bildinhalt.

Bei Rechnungen/Belegen lies Aussteller, Datum (YYYY-MM-DD), Gesamtbetrag, Währung und
Rechnungsnummer ab – nur was wirklich lesbar ist, sonst null. Rate keine Beträge.
Der Dateiname-Vorschlag ist kurz, ohne Endung, nur a-z 0-9 und Bindestriche,
beginnend mit dem Datum falls bekannt (z. B. 2026-07-14-baumarkt-rechnung).
Nächste Schritte: 1–3 konkrete, kurze Handlungsempfehlungen auf Deutsch
(z. B. "An Steuerberater weiterleiten", "Für Website-Galerie geeignet", "Duplikat prüfen").
Alle Texte auf Deutsch."""

_NULLABLE_STR = {"type": ["string", "null"]}
ANTWORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "kategorie", "sicherheit", "beschreibung", "herkunft", "ort", "datum",
        "dateiname_vorschlag", "tags", "naechste_schritte", "rechnung",
    ],
    "properties": {
        "kategorie": {"type": "string", "enum": list(KATEGORIEN)},
        "sicherheit": {"type": "string", "enum": ["hoch", "mittel", "niedrig"]},
        "beschreibung": {"type": "string"},
        "herkunft": {
            "type": "string",
            "enum": ["handykamera", "kamera", "screenshot", "messenger", "scan", "download", "unbekannt"],
        },
        "ort": _NULLABLE_STR,
        "datum": _NULLABLE_STR,
        "dateiname_vorschlag": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "naechste_schritte": {"type": "array", "items": {"type": "string"}},
        "rechnung": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["aussteller", "datum", "betrag", "waehrung", "rechnungsnummer"],
                    "properties": {
                        "aussteller": _NULLABLE_STR,
                        "datum": _NULLABLE_STR,
                        "betrag": {"type": ["number", "null"]},
                        "waehrung": _NULLABLE_STR,
                        "rechnungsnummer": _NULLABLE_STR,
                    },
                },
            ]
        },
    },
}


# --------------------------------------------------------------------------- Datenmodell

@dataclass
class Bildquelle:
    """Ein zu scannendes Bild – egal ob lokal oder aus der Dropbox."""

    pfad: str  # lokaler Pfad oder Dropbox-Pfad
    name: str
    daten: bytes
    quelle: str  # "lokal" | "dropbox"
    geaendert: str | None = None


@dataclass
class Ergebnis:
    pfad: str
    name: str
    quelle: str
    sha256: str
    technik: dict
    analyse: dict | None = None
    zielpfad: str | None = None
    fehler: str | None = None
    verschoben: bool = False
    vorschau: str | None = field(default=None, repr=False)  # kleines JPEG als data-URI für den Bericht


# --------------------------------------------------------------------------- Herkunft (ohne KI)

_NAMENSMUSTER = [
    (re.compile(r"^(screenshot|bildschirmfoto|screen shot)", re.I), "screenshot"),
    (re.compile(r"^IMG-\d{8}-WA\d+", re.I), "messenger"),  # WhatsApp
    (re.compile(r"(whatsapp|telegram|signal)", re.I), "messenger"),
    (re.compile(r"^(scan|scanned|dokument|document)", re.I), "scan"),
    (re.compile(r"^(IMG_|PXL_|DSC|DCIM|\d{8}_\d{6}|\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2})", re.I), "kamera"),
]
_EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}


def _gps_zu_grad(wert, ref) -> float | None:
    try:
        g, m, s = (float(x) for x in wert)
        grad = g + m / 60 + s / 3600
        return round(-grad if ref in ("S", "W") else grad, 6)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def technische_herkunft(bild: Image.Image, name: str, geaendert: str | None) -> dict:
    """Liest EXIF und Dateinamen aus – liefert Fakten, die Claude als Hinweise bekommt."""
    info: dict = {"dateiname_hinweis": None, "kamera": None, "aufgenommen": None, "gps": None,
                  "software": None, "groesse": f"{bild.width}x{bild.height}", "geaendert": geaendert}
    for muster, art in _NAMENSMUSTER:
        if muster.search(name):
            info["dateiname_hinweis"] = art
            break

    exif = bild.getexif()
    if exif:
        marke = str(exif.get(_EXIF_TAGS["Make"], "")).strip()
        modell = str(exif.get(_EXIF_TAGS["Model"], "")).strip()
        info["kamera"] = " ".join(x for x in (marke, modell) if x) or None
        info["software"] = str(exif.get(_EXIF_TAGS["Software"], "")).strip() or None
        detail = exif.get_ifd(ExifTags.IFD.Exif)
        zeit = detail.get(_EXIF_TAGS["DateTimeOriginal"]) or exif.get(_EXIF_TAGS["DateTime"])
        if zeit:
            try:
                info["aufgenommen"] = datetime.strptime(str(zeit), "%Y:%m:%d %H:%M:%S").isoformat()
            except ValueError:
                pass
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
        if gps and 2 in gps and 4 in gps:
            lat, lon = _gps_zu_grad(gps[2], gps.get(1)), _gps_zu_grad(gps[4], gps.get(3))
            if lat is not None and lon is not None:
                info["gps"] = {"lat": lat, "lon": lon}
    return info


# --------------------------------------------------------------------------- Bildaufbereitung

def bild_vorbereiten(daten: bytes) -> tuple[Image.Image, bytes, str]:
    """Öffnet das Bild, dreht es richtig, verkleinert es und liefert (Original, JPEG für Claude, Vorschau-URI)."""
    original = Image.open(io.BytesIO(daten))
    original.load()
    bild = ImageOps.exif_transpose(original).convert("RGB")
    bild.thumbnail((MAX_KANTE, MAX_KANTE))
    puffer = io.BytesIO()
    bild.save(puffer, "JPEG", quality=85)

    klein = bild.copy()
    klein.thumbnail((240, 240))
    vorschau = io.BytesIO()
    klein.save(vorschau, "JPEG", quality=70)
    uri = "data:image/jpeg;base64," + base64.b64encode(vorschau.getvalue()).decode()
    return original, puffer.getvalue(), uri


# --------------------------------------------------------------------------- Claude

class Klassifizierer:
    """Direkt bei Anthropic (Standard) oder über ein lokales Gateway wie OmniRoute.

    Gateway-Modus: Die Anfrage bleibt im Anthropic-Messages-Format (das spricht OmniRoute),
    verzichtet aber auf Anthropic-spezifische Extras (Beta-Fallbacks, JSON-Schema-Zwang,
    Thinking), weil dahinter auch andere Modelle antworten können. Das JSON wird
    dann per Anweisung angefordert und tolerant ausgelesen.
    """

    def __init__(self, effort: str = "low", gateway: str | None = None, modell: str | None = None):
        import anthropic

        self.effort = effort
        self.gateway = gateway
        if gateway:
            schluessel = os.environ.get("OMNIROUTE_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            if not schluessel:
                sys.exit("OmniRoute-Schlüssel fehlt: OMNIROUTE_API_KEY setzen "
                         "(Dashboard → Endpoints). Siehe README.md.")
            # Kein /v1 anhängen – das SDK ergänzt /v1/messages selbst.
            self.client = anthropic.Anthropic(base_url=gateway.rstrip("/").removesuffix("/v1"),
                                              auth_token=schluessel)
            self.modell = modell or "auto"
        else:
            self.client = anthropic.Anthropic()
            self.modell = modell or MODEL

    def analysiere(self, jpeg: bytes, name: str, technik: dict) -> dict:
        hinweise = json.dumps({"dateiname": name, **technik}, ensure_ascii=False)
        inhalt = [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.standard_b64encode(jpeg).decode()}},
            {"type": "text", "text": f"Technische Hinweise: {hinweise}\n\nOrdne dieses Bild ein."},
        ]
        if self.gateway:
            return self._ueber_gateway(inhalt)

        antwort = self.client.beta.messages.create(
            model=self.modell,
            max_tokens=4096,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": ANTWORT_SCHEMA},
            },
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": inhalt}],
        )
        if antwort.stop_reason == "refusal":
            raise RuntimeError("Claude hat die Analyse dieses Bildes abgelehnt.")
        if antwort.stop_reason == "max_tokens":
            raise RuntimeError("Antwort wurde abgeschnitten (max_tokens).")
        text = "".join(b.text for b in antwort.content if b.type == "text")
        return json.loads(text)

    def _ueber_gateway(self, inhalt: list) -> dict:
        system = (SYSTEM_PROMPT + "\n\nAntworte ausschließlich mit einem JSON-Objekt, ohne Erklärtext "
                  "und ohne Markdown, nach diesem JSON-Schema:\n" + json.dumps(ANTWORT_SCHEMA, ensure_ascii=False))
        antwort = self.client.messages.create(
            model=self.modell,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": inhalt}],
        )
        if antwort.stop_reason == "refusal":
            raise RuntimeError("Das Modell hat die Analyse dieses Bildes abgelehnt.")
        text = "".join(getattr(b, "text", "") for b in antwort.content)
        daten = _json_aus_text(text)
        daten["_modell"] = getattr(antwort, "model", self.modell)  # welches Modell wirklich geantwortet hat
        return _normalisieren(daten)


def _json_aus_text(text: str) -> dict:
    """Holt das erste JSON-Objekt aus einer Antwort – auch wenn ein Modell Text oder ```-Blöcke drumherum schreibt."""
    start = text.find("{")
    if start < 0:
        raise RuntimeError(f"Keine JSON-Antwort erhalten: {text[:200]!r}")
    try:
        daten, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as fehler:
        raise RuntimeError(f"Antwort ist kein gültiges JSON ({fehler}): {text[start:start + 200]!r}") from None
    if not isinstance(daten, dict):
        raise RuntimeError("Antwort ist kein JSON-Objekt.")
    return daten


def _normalisieren(d: dict) -> dict:
    """Bringt Antworten anderer Modelle in die erwartete Form (fehlende Felder, falsche Werte)."""
    d["kategorie"] = str(d.get("kategorie") or "").strip().lower()
    d["sicherheit"] = str(d.get("sicherheit") or "").strip().lower()
    if d["kategorie"] not in KATEGORIEN:
        d["kategorie"] = "sonstiges"
    if d.get("sicherheit") not in ("hoch", "mittel", "niedrig"):
        d["sicherheit"] = "niedrig"
    for feld in ("beschreibung", "dateiname_vorschlag"):
        d[feld] = str(d.get(feld) or "")
    d.setdefault("herkunft", "unbekannt")
    for feld in ("ort", "datum"):
        d.setdefault(feld, None)
    for feld in ("tags", "naechste_schritte"):
        d[feld] = [str(x) for x in d.get(feld) or [] if x]
    r = d.get("rechnung")
    if isinstance(r, dict):
        try:
            r["betrag"] = None if r.get("betrag") in (None, "") else float(str(r["betrag"]).replace(",", "."))
        except ValueError:
            r["betrag"] = None
    else:
        d["rechnung"] = None
    return d


# --------------------------------------------------------------------------- Quellen

def lokale_bilder(ordner: Path) -> Iterator[Bildquelle]:
    for pfad in sorted(ordner.rglob("*")):
        if pfad.is_file() and pfad.suffix.lower() in BILD_ENDUNGEN:
            geaendert = datetime.fromtimestamp(pfad.stat().st_mtime).isoformat(timespec="seconds")
            yield Bildquelle(str(pfad), pfad.name, pfad.read_bytes(), "lokal", geaendert)


def dropbox_client():
    import dropbox

    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    refresh = os.environ.get("DROPBOX_REFRESH_TOKEN")
    app_key = os.environ.get("DROPBOX_APP_KEY")
    if refresh and app_key:
        return dropbox.Dropbox(oauth2_refresh_token=refresh, app_key=app_key,
                               app_secret=os.environ.get("DROPBOX_APP_SECRET"))
    if token:
        return dropbox.Dropbox(token)
    sys.exit("Dropbox-Zugang fehlt: DROPBOX_ACCESS_TOKEN setzen "
             "(oder DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY). Siehe README.md.")


def dropbox_bilder(dbx, ordner: str, rekursiv: bool = True) -> Iterator[Bildquelle]:
    import dropbox

    ordner = "" if ordner in ("", "/") else ordner
    res = dbx.files_list_folder(ordner, recursive=rekursiv)
    while True:
        for eintrag in res.entries:
            if isinstance(eintrag, dropbox.files.FileMetadata) and \
                    Path(eintrag.name).suffix.lower() in BILD_ENDUNGEN:
                _, antwort = dbx.files_download(eintrag.path_lower)
                yield Bildquelle(eintrag.path_display, eintrag.name, antwort.content, "dropbox",
                                 eintrag.client_modified.isoformat())
        if not res.has_more:
            break
        res = dbx.files_list_folder_continue(res.cursor)


# --------------------------------------------------------------------------- Zielpfad

def _saeubern(text: str) -> str:
    text = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9-]+", "-", text)).strip("-")


def zielpfad(ergebnis: Ergebnis, ziele: dict, basis: str) -> str:
    a = ergebnis.analyse
    datum = (a.get("rechnung") or {}).get("datum") or a.get("datum") or ergebnis.technik.get("aufgenommen") \
        or ergebnis.technik.get("geaendert") or ""
    treffer = re.match(r"(\d{4})-(\d{2})", datum)
    jahr, monat = (treffer.group(1), treffer.group(2)) if treffer else ("ohne-Datum", "")
    ordner = ziele.get(a["kategorie"], ziele["sonstiges"]).format(jahr=jahr, monat=monat, ort=a.get("ort") or "")
    ordner = "/".join(teil.strip() for teil in ordner.split("/") if teil.strip())
    endung = Path(ergebnis.name).suffix.lower()
    dateiname = (_saeubern(a.get("dateiname_vorschlag") or "") or Path(ergebnis.name).stem) + endung
    return f"{basis.rstrip('/')}/{ordner}/{dateiname}"


# --------------------------------------------------------------------------- Cache

class Cache:
    """Merkt sich Analysen pro Dateiinhalt (SHA-256), damit nichts doppelt bezahlt wird."""

    def __init__(self, pfad: Path):
        self.pfad = pfad
        self.daten = json.loads(pfad.read_text()) if pfad.exists() else {}

    def get(self, sha: str) -> dict | None:
        return self.daten.get(sha)

    def set(self, sha: str, analyse: dict) -> None:
        self.daten[sha] = analyse
        self.pfad.write_text(json.dumps(self.daten, ensure_ascii=False, indent=1))


# --------------------------------------------------------------------------- Berichte

def berichte_schreiben(ergebnisse: list[Ergebnis], ausgabe: Path, titel: str) -> None:
    ausgabe.mkdir(parents=True, exist_ok=True)
    (ausgabe / "ergebnisse.json").write_text(json.dumps(
        [{k: v for k, v in asdict(e).items() if k != "vorschau"} for e in ergebnisse],
        ensure_ascii=False, indent=2))

    with open(ausgabe / "ergebnisse.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Datei", "Kategorie", "Sicherheit", "Herkunft", "Datum", "Ort", "Beschreibung",
                    "Zielpfad", "Nächste Schritte", "Modell", "Fehler"])
        for e in ergebnisse:
            a = e.analyse or {}
            w.writerow([e.pfad, a.get("kategorie"), a.get("sicherheit"), a.get("herkunft"), a.get("datum"),
                        a.get("ort"), a.get("beschreibung"), e.zielpfad,
                        " | ".join(a.get("naechste_schritte", [])), a.get("_modell"), e.fehler])

    rechnungen = [e for e in ergebnisse if e.analyse and e.analyse.get("rechnung")]
    with open(ausgabe / "rechnungen.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Datum", "Aussteller", "Betrag", "Währung", "Rechnungsnummer", "Datei"])
        for e in sorted(rechnungen, key=lambda e: e.analyse["rechnung"].get("datum") or ""):
            r = e.analyse["rechnung"]
            betrag = "" if r.get("betrag") is None else f"{r['betrag']:.2f}".replace(".", ",")
            w.writerow([r.get("datum"), r.get("aussteller"), betrag, r.get("waehrung"),
                        r.get("rechnungsnummer"), e.zielpfad if e.verschoben else e.pfad])

    (ausgabe / "bericht.html").write_text(_html_bericht(ergebnisse, titel), encoding="utf-8")


def _anzeige_kategorie(e: Ergebnis) -> str:
    if e.analyse:
        return e.analyse["kategorie"]
    return "duplikat" if (e.fehler or "").startswith("Duplikat") else "fehler"


def _html_bericht(ergebnisse: list[Ergebnis], titel: str) -> str:
    esc = lambda x: html.escape(str(x)) if x not in (None, "") else "–"  # noqa: E731
    zaehler: dict[str, int] = {}
    for e in ergebnisse:
        k = _anzeige_kategorie(e)
        zaehler[k] = zaehler.get(k, 0) + 1
    chips = "".join(f'<button class="chip" data-k="{esc(k)}">{esc(k)} <b>{n}</b></button>'
                    for k, n in sorted(zaehler.items(), key=lambda x: -x[1]))
    karten = []
    for e in ergebnisse:
        a = e.analyse or {}
        r = a.get("rechnung")
        rechnung = ""
        if r:
            betrag = "–" if r.get("betrag") is None else f"{r['betrag']:.2f} {r.get('waehrung') or ''}"
            rechnung = (f'<p class="re">🧾 {esc(r.get("aussteller"))} · {esc(r.get("datum"))} · '
                        f'<b>{esc(betrag)}</b> · Nr. {esc(r.get("rechnungsnummer"))}</p>')
        schritte = "".join(f"<li>{esc(s)}</li>" for s in a.get("naechste_schritte", []))
        tech = e.technik
        herkunft = ", ".join(x for x in (a.get("herkunft"), tech.get("kamera"),
                                         (tech.get("aufgenommen") or "")[:10]) if x)
        gps = tech.get("gps")
        karte = (f' · <a href="https://www.openstreetmap.org/?mlat={gps["lat"]}&mlon={gps["lon"]}&zoom=14" '
                 f'target="_blank">📍 Karte</a>') if gps else ""
        status = "✅ verschoben" if e.verschoben else "Vorschlag"
        karten.append(f"""
<article class="karte" data-k="{esc(_anzeige_kategorie(e))}">
  {'<img src="' + e.vorschau + '" alt="">' if e.vorschau else '<div class="leer">?</div>'}
  <div class="info">
    <div class="kopf"><span class="kat">{esc(_anzeige_kategorie(e))}</span>
      <span class="sich s-{esc(a.get('sicherheit'))}">{esc(a.get('sicherheit'))}</span></div>
    <p class="name" title="{esc(e.pfad)}">{esc(e.name)}</p>
    <p>{esc(a.get('beschreibung') or e.fehler)}</p>
    {rechnung}
    <p class="klein"><b>Woher:</b> {esc(herkunft)}{karte}{(' · ' + esc(a['ort'])) if a.get('ort') else ''}</p>
    <p class="klein"><b>Wohin</b> ({status}): <code>{esc(e.zielpfad)}</code></p>
    {'<ul>' + schritte + '</ul>' if schritte else ''}
    {'<p class="modell">Modell: ' + esc(a['_modell']) + '</p>' if a.get('_modell') else ''}
  </div>
</article>""")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(titel)}</title>
<style>
:root{{--bg:#f6f4ef;--karte:#fff;--text:#1f2328;--leise:#6b6f76;--akzent:#2f6f5e;--rand:#e3e0d8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181b;--karte:#1f2226;--text:#e8e6e1;--leise:#9aa0a6;--akzent:#6cc3a8;--rand:#30343a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,sans-serif;padding:24px 16px}}
h1{{margin:0 0 4px;font-size:1.5rem}}.meta{{color:var(--leise);margin:0 0 16px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}}
.chip{{border:1px solid var(--rand);background:var(--karte);color:var(--text);border-radius:999px;padding:6px 12px;cursor:pointer;font:inherit}}
.chip.an{{background:var(--akzent);color:#fff;border-color:var(--akzent)}}
.raster{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:16px}}
.karte{{background:var(--karte);border:1px solid var(--rand);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}}
.karte img,.leer{{width:100%;height:190px;object-fit:cover;background:var(--rand);display:grid;place-items:center}}
.info{{padding:12px 14px}}.info p{{margin:4px 0}}.kopf{{display:flex;justify-content:space-between}}
.kat{{font-weight:700;color:var(--akzent);text-transform:uppercase;font-size:.8rem;letter-spacing:.05em}}
.sich{{font-size:.75rem;color:var(--leise)}}.s-niedrig{{color:#c0392b}}
.name{{font-size:.8rem;color:var(--leise);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.klein{{font-size:.85rem}}code{{font-size:.8rem;word-break:break-all}}.re{{background:var(--bg);padding:6px 8px;border-radius:6px}}
.modell{{font-size:.75rem;color:var(--leise);margin-top:8px}}
ul{{margin:6px 0 0;padding-left:18px;font-size:.85rem}}a{{color:var(--akzent)}}
</style></head><body>
<h1>{esc(titel)}</h1><p class="meta">{len(ergebnisse)} Bilder · erstellt {datetime.now():%d.%m.%Y %H:%M}</p>
<div class="chips"><button class="chip an" data-k="*">alle <b>{len(ergebnisse)}</b></button>{chips}</div>
<main class="raster">{''.join(karten)}</main>
<script>
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{{
  document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('an',x===c));
  document.querySelectorAll('.karte').forEach(k=>k.style.display=(c.dataset.k==='*'||k.dataset.k===c.dataset.k)?'':'none');
}});
</script></body></html>"""


# --------------------------------------------------------------------------- Ablauf

def _freier_lokaler_pfad(ziel: Path) -> Path:
    kandidat, n = ziel, 2
    while kandidat.exists():
        kandidat = ziel.with_name(f"{ziel.stem}-{n}{ziel.suffix}")
        n += 1
    return kandidat


def verschieben(e: Ergebnis, dbx) -> None:
    if e.quelle == "lokal":
        ziel = _freier_lokaler_pfad(Path(e.zielpfad))
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(e.pfad, ziel)
        e.zielpfad = str(ziel)
    else:
        erg = dbx.files_move_v2(e.pfad, e.zielpfad, autorename=True)
        e.zielpfad = erg.metadata.path_display
    e.verschoben = True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bilder scannen, einordnen und sortieren (lokal oder Dropbox).")
    p.add_argument("quelle", choices=["lokal", "dropbox"], help="Woher die Bilder kommen")
    p.add_argument("ordner", help='Lokaler Ordner oder Dropbox-Pfad, z. B. "/Kamera-Uploads"')
    p.add_argument("--ziel", help="Basisordner für die Sortierung (Standard: <ordner>/Sortiert)")
    p.add_argument("--anwenden", action="store_true",
                   help="Dateien wirklich verschieben/umbenennen (ohne: nur Bericht)")
    p.add_argument("--nicht-rekursiv", action="store_true", help="Unterordner nicht durchsuchen")
    p.add_argument("--max", type=int, default=0, help="Höchstens so viele Bilder scannen (0 = alle)")
    p.add_argument("--ziele", type=Path, help="JSON-Datei mit eigenen Zielordnern je Kategorie")
    p.add_argument("--ausgabe", type=Path, default=Path("bildscanner-bericht"), help="Ordner für Berichte")
    p.add_argument("--gateway", default=os.environ.get("OMNIROUTE_URL"),
                   help="Über ein lokales Gateway statt direkt bei Anthropic, z. B. http://localhost:20128 "
                        "(OmniRoute). Alternativ Umgebungsvariable OMNIROUTE_URL.")
    p.add_argument("--modell", help='Modell-ID (Standard: claude-opus-5-5 direkt, "auto" über Gateway)')
    p.add_argument("--effort", default="low", choices=["low", "medium", "high"],
                   help="Wie gründlich Claude nachdenkt (low reicht meistens)")
    args = p.parse_args(argv)

    ziele = dict(STANDARD_ZIELE)
    if args.ziele:
        ziele.update(json.loads(args.ziele.read_text()))
    basis = args.ziel or f"{args.ordner.rstrip('/')}/Sortiert"

    dbx = None
    if args.quelle == "dropbox":
        dbx = dropbox_client()
        bilder = dropbox_bilder(dbx, args.ordner, rekursiv=not args.nicht_rekursiv)
    else:
        ordner = Path(args.ordner).expanduser().resolve()
        if not ordner.is_dir():
            sys.exit(f"Ordner nicht gefunden: {ordner}")
        basis = str(Path(basis).expanduser().resolve())
        bilder = lokale_bilder(ordner)

    args.ausgabe.mkdir(parents=True, exist_ok=True)
    cache = Cache(args.ausgabe / "cache.json")
    klassifizierer = Klassifizierer(args.effort, args.gateway, args.modell)
    ergebnisse: list[Ergebnis] = []
    gesehen: dict[str, str] = {}

    for nr, b in enumerate(bilder, 1):
        # Bereits einsortierte Bilder (unterhalb des Zielordners) überspringen
        if b.pfad.lower().startswith(basis.lower().rstrip("/") + "/"):
            continue
        if args.max and len(ergebnisse) >= args.max:
            break
        sha = hashlib.sha256(b.daten).hexdigest()
        print(f"[{nr}] {b.pfad} … ", end="", flush=True)
        try:
            original, jpeg, vorschau = bild_vorbereiten(b.daten)
            e = Ergebnis(b.pfad, b.name, b.quelle, sha, technische_herkunft(original, b.name, b.geaendert),
                         vorschau=vorschau)
        except Exception as fehler:  # kaputte oder nicht lesbare Datei
            ergebnisse.append(Ergebnis(b.pfad, b.name, b.quelle, sha, {}, fehler=f"Nicht lesbar: {fehler}"))
            print("nicht lesbar")
            continue

        if sha in gesehen:
            e.fehler = f"Duplikat von {gesehen[sha]}"
            ergebnisse.append(e)
            print("Duplikat")
            continue
        gesehen[sha] = b.pfad

        try:
            e.analyse = cache.get(sha) or klassifizierer.analysiere(jpeg, b.name, e.technik)
            cache.set(sha, e.analyse)
            e.zielpfad = zielpfad(e, ziele, basis)
            if args.anwenden:
                verschieben(e, dbx)
            print(f"{e.analyse['kategorie']} → {e.zielpfad}")
        except Exception as fehler:
            e.fehler = str(fehler)
            print(f"Fehler: {fehler}")
        ergebnisse.append(e)

    if not ergebnisse:
        print("Keine Bilder gefunden.")
        return 0
    berichte_schreiben(ergebnisse, args.ausgabe, f"Bildscanner – {args.quelle}: {args.ordner}")
    print(f"\nFertig: {len(ergebnisse)} Bilder. Bericht: {args.ausgabe / 'bericht.html'}")
    if not args.anwenden:
        print("Es wurde nichts verschoben. Mit --anwenden werden die Vorschläge umgesetzt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
