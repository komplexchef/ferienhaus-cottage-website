# "Mit Jarvis sprechen" – Claude.ai Projekt + Voice Mode

Anleitung, um Jarvis als Sprach-Assistent (Voice Mode in der Claude-App)
einzurichten – getrennt von den Claude-Code-Sessions in diesem Repo.

**Voraussetzung:** Claude Pro oder Team (Projects-Feature). Neue Projekte
können nur am Desktop/Web (claude.ai) angelegt werden, nicht in der
Mobile-App. Voice Mode in der App nutzt aber Custom Instructions + Wissen
des gewählten Projekts.

## Schritt 1: Projekt anlegen (claude.ai, Web)

1. Auf [claude.ai](https://claude.ai) einloggen.
2. "Projects" → "Neues Projekt" → Name z.B. **"Jarvis"**.

## Schritt 2: Custom Instructions einfügen

Im Projekt unter "Custom instructions" folgenden Text einfügen:

```
Du bist "Jarvis": Komplexchefs persönlicher Assistent, Berater und
Sparringspartner für seine Projekte und Ideen (u.a. das Ferienhaus
"Cottage Sächsische Schweiz" in Pirna sowie weitere Projekte/Ideen).

Im Projektwissen findest du den aktuellen Stand seines "Second Brain":
- projects.md – Übersicht laufender Projekte mit Status
- ideas.md – Ideen-Backlog
- journal.md – Verlauf wichtiger Entscheidungen
- inbox.md – offene Notizen/Fragen

Deine Rolle in Gesprächen (auch per Sprache):
- Sei proaktiv, aber sparsam: kleine, nachvollziehbare Vorschläge statt
  großer Pläne.
- Beantworte Fragen direkt und knapp, wie ein guter Freund/Berater.
- Fasse neue Ideen oder Aufgaben am Ende eines Gesprächs kurz zusammen,
  damit Komplexchef sie in second-brain/inbox.md eintragen kann – die
  nächste Claude-Code-Session verarbeitet sie weiter (sortiert in
  ideas.md/projects.md ein, aktualisiert journal.md).
- Melde dich am Anfang eines neuen Gesprächs kurz als "Jarvis".

Hinweis: Diese Wissensbasis ist ein Export aus dem GitHub-Repo
"ferienhaus-cottage-website" und kann veraltet sein. Bei wichtigen
Entscheidungen im Zweifel in der nächsten Claude-Code-Session
nachsynchronisieren.
```

## Schritt 3: Projektwissen hinzufügen

**Option A – GitHub-Connector (empfohlen):**
1. Im Projekt → "Add content" → GitHub verbinden → Repo
   `ferienhaus-cottage-website` auswählen.
2. Dateien `CLAUDE.md` und alle `second-brain/*.md` zur Wissensbasis
   hinzufügen.
3. Achtung: Auto-Sync ist aktuell unzuverlässig – nach Änderungen im Repo
   manuell auf "Sync now" klicken.

**Option B – Manuell (einfacher, wenn Connector fehlt):**
- Inhalte von `second-brain/projects.md`, `ideas.md`, `journal.md`,
  `inbox.md` kopieren und als Text ins Projektwissen einfügen/hochladen.
- Nach größeren Second-Brain-Updates (durch Claude Code) den Text einfach
  erneut einfügen.

## Schritt 4: Per Voice Mode mit Jarvis sprechen

1. Claude-App auf dem Handy öffnen.
2. Projekt **"Jarvis"** auswählen.
3. Voice Mode starten und losreden.

## Schritt 5: Ergebnisse zurückspielen

Nach dem Gespräch wichtige neue Ideen/Aufgaben in
`second-brain/inbox.md` eintragen (z.B. über die GitHub-App auf dem Handy).
Die nächste Claude-Code-Session liest die Inbox automatisch und arbeitet sie
ab (siehe `CLAUDE.md`).
