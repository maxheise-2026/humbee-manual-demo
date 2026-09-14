"""Baut aus content/ das Druckhandbuch.

Schritt 1  content/  ->  build/print/   (Quarto-Buchprojekt, les- und prüfbar)
Schritt 2  build/print/  ->  dist/humbee-handbuch-<version>.pdf

Aufruf:
    python scripts/build_print.py                  # Engine aus manual.yml
    python scripts/build_print.py --engine pandoc  # ohne Quarto-Installation
    python scripts/build_print.py --no-render      # nur build/print/ erzeugen
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date

import yaml

from common import (BUILD, DIST, ROOT, demote_headings, discover, load_config,
                    rewrite_images, rewrite_links, strip_conditionals)

OUT = BUILD / "print"


def slug(s: str) -> str:
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "ae"), ("Ö", "oe"),
                 ("Ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def tex_escape(s: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}")):
        s = s.replace(a, b)
    return s


def seite_aufbereiten(p, by_relpath, cfg, level: int) -> str:
    """Eine Handbuchseite in einen Abschnitt des Buches verwandeln."""
    body = strip_conditionals(p.body, "print")
    body = rewrite_links(p, body, "print", by_relpath, cfg)
    body = rewrite_images(body, "print")
    body = demote_headings(body, level - 1) if level > 1 else body
    # Anker an die oberste Überschrift der Seite, damit Querverweise landen.
    anker = "{#sec-" + p.id + ("" if not p.meta.get("unnumbered") else " .unnumbered") + "}"
    body = re.sub(r"^(#{1,6} .+?)\s*$", r"\1 " + anker, body.strip(), count=1, flags=re.MULTILINE)
    return body.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["quarto", "pandoc"])
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    engine = args.engine or cfg["print"].get("engine", "quarto")
    m, pr = cfg["manual"], cfg["print"]

    pages, chapters = discover()
    by_relpath = {str(p.rel).replace("\\", "/"): p for p in pages}

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    DIST.mkdir(exist_ok=True)

    # --- Bilder flach kopieren ---------------------------------------------
    for p in pages:
        if p.wanted_for("print"):
            for bild in p.images():
                ziel = OUT / "assets" / bild.name
                if not ziel.exists():
                    shutil.copy2(bild, ziel)

    # --- Metadaten als LaTeX-Makros ----------------------------------------
    datum = date.today().strftime("%d.%m.%Y")
    meta_tex = "\n".join([
        r"\usepackage{fontspec}",
        f"\\setmainfont{{{pr['schrift']}}}",
        f"\\setsansfont{{{pr['schrift']}}}",
        f"\\setmonofont{{{pr['schrift_mono']}}}[Scale=0.92]",
        f"\\newcommand{{\\manualtitel}}{{{tex_escape(m['title'])}}}",
        f"\\newcommand{{\\manualuntertitel}}{{{tex_escape(m['subtitle'])}}}",
        f"\\newcommand{{\\manualversion}}{{Version {tex_escape(str(m['version']))}}}",
        f"\\newcommand{{\\manualdatum}}{{{datum}}}",
        f"\\newcommand{{\\manualherausgeber}}{{{tex_escape(m['publisher'])}}}",
        f"\\newcommand{{\\manualhinweis}}{{{tex_escape(m['stand_hinweis'])}}}",
        f"\\AtBeginDocument{{\\hypersetup{{pdftitle={{{m['title']} {m['version']}}},"
        f"pdfauthor={{{m['publisher']}}}}}}}",
    ]) + "\n"
    (OUT / "meta.tex").write_text(meta_tex, encoding="utf-8")
    for t in ("kopf.tex", "deckblatt.tex"):
        shutil.copy2(ROOT / "templates" / t, OUT / t)

    # --- Vorspann (Seiten direkt in content/) -------------------------------
    vorspann = [p for p in pages if p.chapter is None and p.wanted_for("print")]
    index = ["---", "title: \"Vorspann\"", "---", ""]
    teile_dateien: list[str] = []
    if vorspann:
        stueck = ["\n".join(seite_aufbereiten(p, by_relpath, cfg, 1) for p in vorspann)]
        (OUT / "index.qmd").write_text("\n".join(stueck) + "\n", encoding="utf-8")
        teile_dateien.append("index.qmd")
    else:
        (OUT / "index.qmd").write_text(f"# Über dieses Handbuch {{.unnumbered}}\n\n"
                                       f"{m['title']}, Version {m['version']}.\n", encoding="utf-8")
        teile_dateien.append("index.qmd")

    # --- je Kapitel eine Datei ----------------------------------------------
    for ch in chapters:
        drin = [p for p in ch.pages if p.wanted_for("print")]
        if not drin:
            continue
        stueck = [f"# {ch.title}\n"]
        if ch.intro.strip():
            stueck.append(ch.intro.strip() + "\n")
        for p in drin:
            stueck.append(seite_aufbereiten(p, by_relpath, cfg, 2))
        datei = f"{ch.order:03d}-{slug(ch.title)}.qmd"
        (OUT / datei).write_text("\n".join(stueck) + "\n", encoding="utf-8")
        teile_dateien.append(datei)

    # --- _quarto.yml ---------------------------------------------------------
    quarto = {
        "project": {"type": "book", "output-dir": "../../dist"},
        "book": {
            "title": m["title"],
            "subtitle": m["subtitle"],
            "author": m["publisher"],
            "date": datum,
            "chapters": teile_dateien,
        },
        "lang": m["language"],
        "format": {
            "pdf": {
                "documentclass": "scrbook",
                "papersize": pr["paper"],
                "toc": True,
                "toc-depth": pr["toc_depth"],
                "lof": True,
                "number-sections": True,
                "colorlinks": True,
                "fig-cap-location": "bottom",
                "geometry": ["top=28mm", "bottom=26mm", "inner=30mm", "outer=24mm"],
                "include-in-header": ["meta.tex", "kopf.tex"],
                "include-before-body": ["deckblatt.tex"],
                "pdf-engine": "xelatex",
                "output-file": f"humbee-handbuch-{m['version']}",
            }
        },
    }
    (OUT / "_quarto.yml").write_text(
        yaml.safe_dump(quarto, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # --- eine Gesamtdatei für den pandoc-Fallback ---------------------------
    gesamt = "\n\n".join((OUT / d).read_text(encoding="utf-8") for d in teile_dateien)
    gesamt = re.sub(r"^---\n.*?\n---\n", "", gesamt, flags=re.DOTALL)
    (OUT / "handbuch.md").write_text(gesamt, encoding="utf-8")

    print(f"build/print/: {len(teile_dateien)} Dateien, "
          f"{len([p for p in pages if p.wanted_for('print')])} Handbuchseiten, "
          f"{len(list((OUT / 'assets').glob('*')))} Bilder")

    if args.no_render:
        return 0

    ziel_pdf = DIST / f"humbee-handbuch-{m['version']}.pdf"
    if engine == "quarto":
        if not shutil.which("quarto"):
            print("Quarto ist nicht installiert - weiche auf pandoc aus "
                  "(https://quarto.org/docs/get-started/ für die Installation).")
            engine = "pandoc"
        else:
            r = subprocess.run(["quarto", "render", ".", "--to", "pdf"], cwd=OUT)
            return 0 if r.returncode == 0 else r.returncode

    befehl = [
        "pandoc", "handbuch.md", "-o", str(ziel_pdf),
        "--from", "markdown+implicit_figures+pipe_tables+fenced_divs",
        "--pdf-engine", "xelatex",
        "--top-level-division=chapter",
        "--toc", f"--toc-depth={pr['toc_depth']}",
        "--number-sections",
        "--include-in-header", "meta.tex",
        "--include-in-header", "kopf.tex",
        "--include-before-body", "deckblatt.tex",
        "-V", "documentclass=scrbook",
        "-V", f"papersize={pr['paper']}",
        "-V", "geometry:top=28mm,bottom=26mm,inner=30mm,outer=24mm",
        "-V", f"lang={m['language']}",
        "-V", "linkcolor=humbeeBlau",
        "-M", "lof=true",
    ]
    r = subprocess.run(befehl, cwd=OUT)
    if r.returncode == 0:
        print(f"PDF erzeugt: dist/{ziel_pdf.name} "
              f"({ziel_pdf.stat().st_size / 1024:.0f} kB)")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
