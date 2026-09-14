# Arbeitsanweisung für Claude Code in diesem Repo

Dieses Repo ist die einzige Quelle für zwei Auslieferungen:

* **LLM-Wiki** – `build/wiki/` geht an den Ingest-Agenten. Leser ist ein KI-Chat,
  der einzelne Abschnitte als Treffer ausliefert.
* **Druckhandbuch** – `build/print/` wird zu `dist/humbee-handbuch-<version>.pdf`.
  Leser ist ein Mensch, der linear liest.

Geschrieben wird **ausschließlich in `content/`**. Alles unter `build/` und `dist/`
ist generiert und wird nie von Hand bearbeitet.

## Ablauf für jede Änderung

1. Neuen Branch anlegen (`doku/<thema>`). Nie direkt auf `main` arbeiten.
2. Seite(n) in `content/` anlegen oder ändern.
3. `python scripts/validate.py` ausführen und alle Fehler beheben.
4. Committen, Pull Request öffnen. Erst der Merge löst Ingest und PDF aus.

## Aufbau einer Seite

Jede Datei beginnt mit vollständigem Frontmatter:

```yaml
---
id: vorgang-anlegen          # klein, mit Bindestrichen, EINDEUTIG und UNVERÄNDERLICH
title: Vorgang anlegen       # identisch mit der H1
summary: Ein bis zwei Sätze, worum es geht. Erscheint in der Trefferliste des KI-Chats.
version: "2026.9"
updated: 2026-09-14
status: entwurf              # entwurf | review | freigegeben
tags: [vorgang, anlegen]
audience: [anwender]         # anwender | administrator | support
wiki: true                   # soll ins LLM-Wiki
print: true                  # soll ins Druckhandbuch
---
```

**Die `id` ist der Schlüssel im LLM-Wiki.** Wird sie geändert, löscht der Ingest-Agent
die alte Seite und legt eine neue an – Verweise und Bewertungen gehen verloren.
Also: Titel gerne ändern, `id` nie.

Nur Seiten mit `status: freigegeben` werden gebaut und ausgeliefert.

## Schreibregeln

* Sie-Form, sachlich, kurze Sätze. Handlungsanweisungen im Imperativ.
* Genau eine H1 pro Datei, danach H2 für Abschnitte, H3 für Unterschritte.
  Keine Ebene überspringen.
* **Jeder H2-Abschnitt muss allein verständlich sein.** Er landet als eigener
  Chunk im Wiki. Verboten sind deshalb „wie oben beschrieben", „im vorherigen
  Kapitel", „siehe unten". Stattdessen den Sachverhalt benennen oder verlinken.
* Schaltflächen und Menüpunkte **fett**, Tastenkürzel als `Code`, Feldnamen fett.
* Keine Zeitangaben wie „neu ab Version X" im Fließtext – das veraltet.
* Zeilen auf etwa 95 Zeichen umbrechen, damit Diffs lesbar bleiben.

## Bilder

```markdown
![Ein vollständiger Satz, der beschreibt, was auf dem Bild zu sehen ist.](../assets/img/datei.png){width=75%}
```

* Ablage immer unter `content/assets/img/`, Dateiname sprechend und klein.
* Die Bildunterschrift ist Pflicht und muss aussagekräftig sein: Im Druck ist sie
  die Abbildungsbeschriftung, im Wiki oft die einzige Beschreibung des Bildinhalts.
* `{width=…}` steuert nur den Druck und wird für das Wiki entfernt.

## Zielgruppen-Unterschiede

Passagen, die nur in einem Medium sinnvoll sind, werden markiert statt doppelt gepflegt:

```markdown
::: {.print-only}
Erscheint nur im PDF – z.B. Überleitungen, Verweise auf Anlagen, Lesehinweise.
:::

::: {.wiki-only}
Erscheint nur im Wiki – z.B. eine Kurzantwort direkt am Anfang eines Abschnitts.
:::
```

Ganze Seiten steuert man über `wiki: false` bzw. `print: false`.

## Querverweise

Immer als relativer Link auf die andere `.md`-Datei:

```markdown
Siehe [Vorgang anlegen](../020-vorgaenge/010-vorgang-anlegen.md).
```

Die Builds setzen das ziel­gerecht um (Wiki-ID bzw. PDF-Sprungmarke). Verweise auf
Kapitelnummern („siehe Kapitel 4.2") sind verboten – sie gibt es im Wiki nicht.

## Reihenfolge und Kapitel

Die Reihenfolge ergibt sich aus den Zahlenpräfixen von Ordnern und Dateien
(`020-vorgaenge/010-vorgang-anlegen.md`). In Zehnerschritten nummerieren, damit
später etwas dazwischen passt. Kapitelname und Kapiteleinleitung stehen in
`_kapitel.yml` des jeweiligen Ordners; die Einleitung erscheint nur im PDF.

## Was NICHT zu tun ist

* Nichts unter `build/`, `dist/` oder `state/` von Hand ändern.
  `state/ingest-manifest.json` ist das Gedächtnis der Auslieferung – wird nur von
  der Action geschrieben.
* Keine Seite löschen, ohne zu bedenken, dass der Ingest-Agent sie dann aus dem
  Wiki entfernt. Soll sie nur aus dem Druck verschwinden: `print: false`.
* Keine Screenshots direkt in Markdown einbetten (base64), keine externen Bild-URLs.
