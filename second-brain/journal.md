# Journal

## 2026-06-15

- Second-Brain-Struktur angelegt: `CLAUDE.md` (Rolle & Workflow für Claude) +
  `second-brain/` (inbox, projects, ideas, journal).
- HTML-Linting (`htmlhint`) als Basis-Tooling für die Website eingerichtet.
- Second Brain Assistent als "Jarvis" benannt.
- Recherche: Claude Code (CLI/Web) hat keine native Sprachausgabe; der
  Cloud-Container hat keine Port-Weiterleitung nach außen (lokaler
  `python3 -m http.server` ist für den Nutzer nicht erreichbar).
- Entscheidung: Audio-Ausgabe zuerst über eine neue "Jarvis"-Seite mit
  Browser-eigener Web Speech API angehen (läuft im Nutzer-Browser, keine
  Infrastruktur nötig). Video-Ausgabe (Idee verworfen) und Playwright/Test-Setup
  vorerst zurückgestellt.
- `jarvis.html` umgesetzt: zeigt Inbox/Projekte/Ideen aus `second-brain/` und
  liest sie per Web Speech API (Deutsch) vor. HTML-Lint ok.
- "Mit Jarvis sprechen" (Claude Mobile App, Voice Mode) vorbereitet:
  `second-brain/jarvis-claude-projekt.md` enthält fertige Custom Instructions
  + Setup-Anleitung. Anlegen des Claude.ai-Projekts muss Komplexchef selbst
  übernehmen (kein Account-Zugriff für Claude Code).
- Mail-Anbindung recherchiert: claude.ai Projects bieten offiziellen
  Gmail-Connector (lesen/durchsuchen/Entwürfe, kein Versand) – Anleitung als
  Schritt 3b in `jarvis-claude-projekt.md` ergänzt. Mail-Zugriff *in
  Claude-Code-Sessions* (dieses Repo) braucht eigenen Gmail-MCP-Server mit
  OAuth – bewusst NICHT in diesem öffentlichen Repo eingerichtet
  (Zugangsdaten-Sicherheit). Als offene Idee vermerkt, Use-Case noch zu
  klären.
- Klarstellung: In dieser Session besteht KEIN Zugriff auf
  ferienhaus19@gmail.com oder komplexchef@gmail.com – nichts wurde an den
  echten Postfächern verändert. Stattdessen Briefing
  `second-brain/mail-organisation.md` erstellt: Phase 1 = ferienhaus19@gmail.com
  (Kategorien: Buchungen, Gäste-Kommunikation, Finanzen, Sonstiges), Phase 2 =
  komplexchef@gmail.com (Briefing folgt später). Gmail-Connector ist noch
  nicht verbunden – das ist der nächste Schritt vor jeder Mail-Aktion.
