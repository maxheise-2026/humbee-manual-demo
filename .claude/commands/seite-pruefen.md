---
description: Prüft eine Handbuchseite auf Wiki- und Drucktauglichkeit
argument-hint: <Pfad zur .md-Datei>
---

Prüfe die Seite **$ARGUMENTS** kritisch. Ändere nichts, sondern liste Befunde auf.

Prüfe in dieser Reihenfolge:

1. **Frontmatter** – alle Pflichtfelder gesetzt, `summary` aussagekräftig und unter
   300 Zeichen, `tags` treffen die Begriffe, nach denen jemand suchen würde.
2. **Chunk-Tauglichkeit** – lies jeden H2-Abschnitt so, als wäre er der einzige
   Text, den ein KI-Chat als Treffer ausliefert. Fehlt Kontext? Gibt es Verweise,
   die ins Leere laufen? Benenne die betroffene Stelle wörtlich.
3. **Drucktauglichkeit** – ergibt die Seite im linearen Lesefluss Sinn? Fehlen
   Überleitungen, die als `::: {.print-only}` ergänzt werden sollten?
4. **Bilder** – hat jedes Bild eine Unterschrift, die den Inhalt wirklich
   beschreibt (nicht nur „Screenshot der Maske")?
5. **Sprache** – Sie-Form, Imperativ bei Handlungsanweisungen, einheitliche
   Fachbegriffe im Vergleich zu den übrigen Seiten in `content/`.

Gib das Ergebnis als kurze Liste aus, je Befund: Stelle, Problem, Vorschlag.
