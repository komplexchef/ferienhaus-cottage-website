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
  Infrastruktur nötig). Video-Ausgabe und Playwright/Test-Setup vorerst
  zurückgestellt.
