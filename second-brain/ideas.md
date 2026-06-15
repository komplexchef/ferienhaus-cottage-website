# Ideen-Backlog

## Jarvis: Audio-/Video-Ausgabe (in Arbeit, 2026-06-15)

Ziel: Mündliche Kommunikation mit Jarvis / Second Brain ermöglichen.

- [x] **Vorlese-Funktion (Quick Win):** `jarvis.html` zeigt Inbox, Projekte und
  Ideen aus `second-brain/` an und liest sie per Browser-eigener Web Speech
  API (`speechSynthesis`, Deutsch) vor – pro Karte einzeln oder "Alles
  vorlesen". Läuft komplett im Browser des Nutzers, keine
  Server-/Container-Probleme wie bei `python3 -m http.server`.
- [ ] **Mobile Eingabe für Inbox:** `second-brain/inbox.md` per GitHub-App auf
  dem Handy bearbeiten (Diktierfunktion der Tastatur) oder GitHub Issues als
  Inbox nutzen – einfacher unterwegs als direktes Datei-Editieren.
- [ ] **"Mit Jarvis sprechen" via Claude Mobile App:** Eigenes Claude.ai-Projekt
  mit Jarvis-Persona (aus `CLAUDE.md`) + Second-Brain-Inhalten als
  Projektwissen einrichten; Voice Mode der Claude-App für Gespräche nutzen,
  Ergebnisse danach manuell/per nächster Session ins Repo zurückspielen.

## Zurückgestellt

- Playwright/Test-Setup (`pip install -r requirements.txt`,
  `playwright install chromium`, `config.json`) – nicht Teil dieses Projekts,
  zurückgestellt bis konkreter Bedarf besteht.
