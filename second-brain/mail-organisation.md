# E-Mail-Organisation – Briefing für Jarvis

Ziel: Postfächer sortieren, nach Priorität sichten, aufräumen, Struktur
schaffen und bei wichtigen Mails Antwort-Entwürfe vorbereiten.

**Reihenfolge:**
1. `ferienhaus19@gmail.com` (Geschäftspostfach Ferienhaus) – zuerst
2. `komplexchef@gmail.com` (persönlich) – danach, eigenes Briefing folgt

**Voraussetzung (noch offen):** Gmail-Connector im claude.ai-Projekt "Jarvis"
für `ferienhaus19@gmail.com` verbinden (siehe `jarvis-claude-projekt.md`,
Schritt 3b). Vorher kann Jarvis das Postfach nicht sehen.

**Wichtige Einschränkung des Gmail-Connectors:** lesend + Entwürfe – Jarvis
kann Mails durchsuchen/zusammenfassen und Antwort-Entwürfe vorschlagen, aber
**keine Mails versenden, löschen, verschieben oder labeln**. "Aufräumen" und
"Struktur reinbringen" heißt also zunächst: Jarvis liefert eine sortierte
Übersicht + Vorschläge (Labels, Prioritäten, Filter-Regeln) – das Anwenden
(Labels anlegen, Mails zuordnen/archivieren) macht Komplexchef selbst, ggf.
mit von Jarvis vorformulierten Gmail-Filterregeln.

---

## Phase 1: ferienhaus19@gmail.com

### Vorgeschlagene Kategorien/Labels

| Label | Inhalt | Priorität |
|---|---|---|
| 📅 Buchungen | Anfragen, Bestätigungen, Stornierungen (Booking.com, Airbnb, direkt) | Hoch – zeitkritisch |
| 💬 Gäste-Kommunikation | Fragen vor/während/nach dem Aufenthalt, Bewertungen | Hoch – zeitkritisch |
| 💰 Finanzen | Plattform-Abrechnungen, Rechnungen, Belege, Steuerrelevantes | Mittel |
| 🗂️ Sonstiges | Wartung/Handwerker, Newsletter, Werbung, Spam | Niedrig – aufräumen/archivieren |

### Ablauf für Jarvis (sobald Connector verbunden)

1. **Sichtung:** Postfach durchsuchen, Mails den 4 Kategorien zuordnen
   (Vorschlag, keine Aktion).
2. **Prioritätenliste:** Offene/unbeantwortete Mails aus "Buchungen" und
   "Gäste-Kommunikation" als Liste ausgeben (Absender, Datum, Kurzfassung,
   was zu tun ist).
3. **Entwürfe:** Für die wichtigsten offenen Mails Antwort-Entwürfe
   vorbereiten (zur Freigabe durch Komplexchef, kein automatischer Versand).
4. **Aufräum-Vorschlag:** Für "Sonstiges" (Newsletter/Werbung) Vorschlag
   für Filterregeln (z.B. "automatisch archivieren/labeln") liefern.
5. **Daten extrahieren:** Relevante Buchungsdetails (Zeiträume, Gästezahl,
   besondere Wünsche) strukturiert sammeln – z.B. in einer neuen
   `second-brain/buchungen.md` oder direkt in `projects.md`, je nach Menge.

---

## Phase 2: komplexchef@gmail.com

Eigenes Briefing nötig, sobald Phase 1 läuft – persönliches Postfach hat
andere Kategorien (z.B. privat, andere Projekte, Finanzen, Newsletter).
Wird mit Komplexchef abgestimmt, sobald es so weit ist.

---

## Nächster konkreter Schritt

Gmail-Connector für `ferienhaus19@gmail.com` im claude.ai-Projekt "Jarvis"
verbinden (siehe `jarvis-claude-projekt.md`, Schritt 3b). Danach: Jarvis
(im claude.ai-Projekt, per Chat oder Voice Mode) bitten, dieses Briefing
("second-brain/mail-organisation.md", Phase 1) auszuführen.
