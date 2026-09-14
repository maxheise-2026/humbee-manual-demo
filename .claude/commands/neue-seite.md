---
description: Legt eine neue Handbuchseite mit korrektem Frontmatter an
argument-hint: <Thema> [Kapitel]
---

Lege eine neue Handbuchseite zum Thema **$ARGUMENTS** an.

Vorgehen:

1. Sieh dir `content/` an und wähle das passende Kapitel. Falls keines passt,
   schlage ein neues Kapitel vor und frage nach, bevor du es anlegst.
2. Bestimme den Dateinamen: nächstes freies Zehnerpräfix im Kapitelordner,
   danach ein sprechender Slug (`030-frist-verlaengern.md`).
3. Schreibe die Seite nach den Regeln in `CLAUDE.md`. Achte besonders auf:
   - vollständiges Frontmatter, `status: entwurf`
   - stabile, eindeutige `id`
   - jeder H2-Abschnitt für sich verständlich
   - keine Verweise auf Kapitelnummern
4. Wo ein Screenshot nötig wäre, setze einen Platzhalter-Kommentar
   `<!-- TODO Screenshot: was zu sehen sein soll -->` statt eines erfundenen Bildpfads.
5. Führe anschließend `python scripts/validate.py` aus und behebe alle Fehler.
6. Fasse am Ende in drei Zeilen zusammen: Datei, ID, was noch fehlt (Screenshots,
   fachliche Prüfung), damit der Status auf `freigegeben` gesetzt werden kann.
