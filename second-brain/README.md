# Second Brain (Jarvis)

Dein persönliches Notiz- und Steuerungssystem. Du schreibst hier rein, "Jarvis"
(Claude in der Rolle aus `CLAUDE.md` im Repo-Root) liest es bei jeder Session
und hilft dir, den Überblick über Projekte und Ideen zu behalten.

- **`inbox.md`** – Schnelle Notizen, Ideen, Fragen, Aufgaben. Einfach
  reinschreiben (z.B. `- [ ] Frage: ...`), Claude verarbeitet die Einträge
  in der nächsten Session und hakt sie ab.
- **`projects.md`** – Übersicht über alle Projekte mit Status und nächsten
  Schritten.
- **`ideas.md`** – Ideen-Backlog, grob kategorisiert.
- **`journal.md`** – Verlauf wichtiger Entscheidungen und Gespräche, mit Datum.

## Automatisierung (optional, nächster Schritt)

Damit die Inbox auch ohne manuell gestartete Session abgearbeitet wird, kann
in Claude Code on the web ein **Trigger** (zeitgesteuerte Session, z.B.
täglich) eingerichtet werden, der diesen Workflow anstößt. Das wird über die
Claude Code Web-Oberfläche konfiguriert (nicht über dieses Repo) – siehe
https://code.claude.com/docs/en/claude-code-on-the-web.
