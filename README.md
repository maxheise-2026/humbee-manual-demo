# humbee Handbuch – Demo-Repo

Eine Quelle, zwei Auslieferungen:

```
content/  ──▶ build/wiki/   ──▶ Ingest-Agent des LLM-Wikis   (KI-Chat)
          └─▶ build/print/  ──▶ dist/humbee-handbuch-X.pdf   (Druckhandbuch)
```

`content/` ist die einzige Stelle, an der geschrieben wird. Alles unter `build/`
und `dist/` ist generiert und steht in `.gitignore`.

## Schnellstart

```bash
pip install -r requirements.txt

python scripts/validate.py          # Inhalte prüfen
python scripts/build_wiki.py        # Ingest-Paket + Änderungsliste bauen
python scripts/push_ingest.py --dry-run
python scripts/build_print.py       # PDF nach dist/
```

In VS Code liegen dieselben Schritte als Tasks (`Strg`+`Shift`+`B` baut das PDF).

### Was installiert sein muss

| Zweck | Werkzeug | Pflicht |
|---|---|---|
| Skripte | Python 3.11+ mit `PyYAML`, `requests` | ja |
| PDF | [Quarto](https://quarto.org/docs/get-started/) + LaTeX (TinyTeX) | empfohlen |
| PDF ohne Quarto | Pandoc + XeLaTeX, Aufruf mit `--engine pandoc` | Alternative |

Ohne Quarto fällt `build_print.py` automatisch auf Pandoc zurück. Das Layout ist
in beiden Fällen dasselbe, weil beide `templates/kopf.tex` und
`templates/deckblatt.tex` verwenden.

## Verzeichnisse

| Pfad | Inhalt |
|---|---|
| `content/` | Die Handbuchseiten. Reihenfolge über Zahlenpräfixe. |
| `content/<kapitel>/_kapitel.yml` | Kapitelname, Reihenfolge, Einleitung (nur Druck) |
| `content/assets/img/` | Screenshots |
| `templates/` | LaTeX-Layout des PDFs – hier wird das Corporate Design gepflegt |
| `scripts/` | Prüfung und beide Builds |
| `state/ingest-manifest.json` | Zuletzt an das Wiki ausgelieferter Stand. **Nur die Action schreibt hier.** |
| `.github/workflows/` | Prüfung bei PR, Auslieferung nach Merge |

## Wie eine Änderung durchläuft

1. Branch `doku/<thema>` anlegen, Seiten in `content/` bearbeiten.
2. `validate.py` grün bekommen, committen, Pull Request öffnen.
3. Die Action **Handbuch prüfen** baut ein Vorschau-PDF und hängt es als Artefakt
   an den PR. Der Review sieht damit genau das, was freigegeben wird.
4. Nach dem Merge läuft **Handbuch freigeben**:
   - meldet neue, geänderte und gelöschte Seiten beim Ingest-Agenten,
   - schreibt `state/ingest-manifest.json` fort,
   - baut das PDF und legt es als Artefakt ab.
5. Ein Tag `v2026.9` erzeugt zusätzlich ein GitHub-Release mit dem PDF als Anhang.

Damit Schritt 4 wirklich erst nach dem Review passiert, muss `main` geschützt sein:
**Settings → Branches → Add rule** für `main` mit *Require a pull request before
merging* (mindestens 1 Approval) und *Require status checks to pass* → `pruefen`.

## Schnittstelle zum Ingest-Agenten

`build_wiki.py` erzeugt `build/wiki/changes.json` – das Delta gegen den zuletzt
ausgelieferten Stand. `push_ingest.py` schickt je Änderung einen POST als
`multipart/form-data` an `$HUMBEE_INGEST_ENDPOINT`:

| Teil | Inhalt |
|---|---|
| `payload` | JSON mit `action` (`upsert`/`delete`), `id`, `source`, `title`, `summary`, `tags`, `updated`, `commit`, `assets` |
| `document` | die Markdown-Datei der Seite |
| `asset` | je ein Screenshot (mehrfach) |

Header `Idempotency-Key: <commit>:<seiten-id>` – derselbe Commit darf nie
Dubletten erzeugen. Die Seiten-ID ist stabil und trägt das Präfix aus `manual.yml`,
damit der Agent erkennt, welche Seiten aus diesem Repo stammen und welche er
löschen darf.

Der genaue Vertrag steht im Kopf von `scripts/push_ingest.py`. Weicht euer Agent
davon ab, ist das die einzige Datei, die angepasst werden muss.

## Was `validate.py` prüft

Eindeutige und stabil formatierte IDs, vollständiges Frontmatter, genau eine H1,
keine Überschriftensprünge, existierende Bilder mit brauchbarer Bildunterschrift,
interne Verweise, ausgeglichene `:::`-Blöcke, verwaiste Bilder – und es warnt bei
Formulierungen wie „wie oben beschrieben", die im Wiki-Chunk ihren Bezug verlieren.

## Demo-Hinweise

* Die Screenshots sind Platzhalter aus `scripts/_demo_screenshots.py`. Im echten
  Repo werden sie durch echte Aufnahmen ersetzt und das Skript gelöscht.
* `content/020-vorgaenge/030-vorgang-serienbearbeitung.md` steht auf
  `status: entwurf` und zeigt, dass Entwürfe nirgends ausgeliefert werden.
* `content/030-dokumente/020-upload-fehler.md` hat `print: false`,
  `content/vorwort.md` hat `wiki: false` – so werden Zielgruppen getrennt, ohne
  Inhalte doppelt zu pflegen.
