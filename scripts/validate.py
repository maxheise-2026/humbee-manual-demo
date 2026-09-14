"""Prüft content/ bevor irgendetwas gebaut oder verschickt wird.

Fehler (exit 1) blockieren den Build, Warnungen nicht.
Aufruf:  python scripts/validate.py [--strict]
"""
from __future__ import annotations

import re
import sys
from collections import Counter

from common import (CONTENT, ERLAUBTE_STATUS, PFLICHTFELDER, RE_IMAGE, RE_MD_LINK,
                    discover, load_config)

# Formulierungen, die beim Zerlegen in Chunks ihren Bezug verlieren
KONTEXTFALLEN = [
    r"\bwie (oben|bereits|zuvor) (beschrieben|erwähnt|gezeigt)\b",
    r"\bim (vorherigen|vorhergehenden|letzten|nächsten) (Kapitel|Abschnitt)\b",
    r"\bsiehe (oben|unten)\b",
    r"\bauf der (vorherigen|nächsten) Seite\b",
    r"\bin der Tabelle (oben|unten)\b",
]

fehler: list[str] = []
warnungen: list[str] = []


def f(page, msg):
    fehler.append(f"{page}: {msg}")


def w(page, msg):
    warnungen.append(f"{page}: {msg}")


def main() -> int:
    cfg = load_config()
    pages, chapters = discover()
    if not pages:
        print("FEHLER: keine Seiten in content/ gefunden")
        return 1

    by_relpath = {str(p.rel).replace("\\", "/"): p for p in pages}

    # --- IDs eindeutig? Die ID ist der Schlüssel im LLM-Wiki. ---------------
    for pid, n in Counter(p.meta.get("id") for p in pages).items():
        if pid and n > 1:
            fehler.append(f"ID '{pid}' wird {n}-mal verwendet - IDs müssen eindeutig und stabil sein")

    for p in pages:
        name = str(p.rel)

        for feld in PFLICHTFELDER:
            if not p.meta.get(feld):
                f(name, f"Pflichtfeld '{feld}' fehlt oder ist leer")

        pid = p.meta.get("id", "")
        if pid and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", pid):
            f(name, f"ID '{pid}' muss klein und mit Bindestrichen geschrieben sein")

        st = str(p.meta.get("status", "")).lower()
        if st and st not in ERLAUBTE_STATUS:
            f(name, f"Status '{st}' unbekannt (erlaubt: {', '.join(sorted(ERLAUBTE_STATUS))})")

        if not (p.meta.get("wiki", True) or p.meta.get("print", True)):
            w(name, "weder für Wiki noch für Druck vorgesehen - die Seite erscheint nirgends")

        summary = p.meta.get("summary", "")
        if summary and len(summary) > 300:
            w(name, f"summary ist {len(summary)} Zeichen lang - kürzer als 300 wirkt in der Trefferliste besser")

        # --- Überschriftenstruktur -----------------------------------------
        h1 = re.findall(r"^# (.+)$", p.body, re.MULTILINE)
        if len(h1) != 1:
            f(name, f"genau eine H1-Überschrift erwartet, gefunden: {len(h1)}")
        elif h1[0].strip() != str(p.meta.get("title", "")).strip():
            w(name, f"H1 '{h1[0].strip()}' weicht vom title im Frontmatter ab")

        vorher = 0
        for lvl_str, text in re.findall(r"^(#{1,6}) (.+)$", p.body, re.MULTILINE):
            lvl = len(lvl_str)
            if vorher and lvl > vorher + 1:
                w(name, f"Überschriftensprung H{vorher} -> H{lvl} bei '{text.strip()}'")
            vorher = lvl

        # --- Bilder ---------------------------------------------------------
        for m in RE_IMAGE.finditer(p.body):
            alt, src = m.group(1), m.group(2)
            if src.startswith(("http://", "https://", "data:")):
                w(name, f"externes Bild '{src}' - besser lokal ablegen, damit es im PDF sicher vorliegt")
                continue
            ziel = (p.path.parent / src).resolve()
            if not ziel.exists():
                f(name, f"Bild nicht gefunden: {src}")
            if len(alt.strip()) < 15:
                f(name, f"Bildunterschrift zu '{src}' fehlt oder ist zu kurz - "
                        f"sie ist im Wiki die einzige Beschreibung des Bildes")

        # --- interne Verweise ------------------------------------------------
        for m in RE_MD_LINK.finditer(p.body):
            ziel = (p.path.parent / m.group(2)).resolve()
            try:
                key = str(ziel.relative_to(CONTENT)).replace("\\", "/")
            except ValueError:
                f(name, f"Verweis zeigt aus content/ heraus: {m.group(2)}")
                continue
            if key not in by_relpath:
                f(name, f"Verweis zeigt ins Leere: {m.group(2)}")

        # --- Chunk-Tauglichkeit ---------------------------------------------
        if p.meta.get("wiki", True):
            for muster in KONTEXTFALLEN:
                for tr in re.finditer(muster, p.body, re.IGNORECASE):
                    w(name, f"'{tr.group(0)}' verliert im Wiki-Chunk seinen Bezug - "
                            f"Ziel ausschreiben oder verlinken")

        # --- bedingte Blöcke ausgeglichen? -----------------------------------
        auf = len(re.findall(r"^:{3,}\s*\{?\s*\.(print-only|wiki-only)", p.body, re.MULTILINE))
        zu = len(re.findall(r"^:{3,}\s*$", p.body, re.MULTILINE))
        if auf != zu:
            f(name, f"{auf} geöffnete, aber {zu} geschlossene ::: Blöcke")

    # --- verwaiste Bilder ---------------------------------------------------
    benutzt = {img for p in pages for img in p.images()}
    for bild in sorted((CONTENT / "assets" / "img").glob("*")):
        if bild.is_file() and bild.resolve() not in benutzt:
            warnungen.append(f"assets/img/{bild.name}: von keiner Seite verwendet")

    # --- Ausgabe ------------------------------------------------------------
    druck = [p for p in pages if p.wanted_for("print")]
    wiki = [p for p in pages if p.wanted_for("wiki")]
    print(f"content/: {len(pages)} Seiten in {len(chapters)} Kapiteln "
          f"-> {len(druck)} im PDF, {len(wiki)} im Wiki")

    for m in warnungen:
        print(f"  WARNUNG  {m}")
    for m in fehler:
        print(f"  FEHLER   {m}")

    if fehler:
        print(f"\n{len(fehler)} Fehler - Build abgebrochen.")
        return 1
    if warnungen and "--strict" in sys.argv:
        print(f"\n{len(warnungen)} Warnungen und --strict aktiv - Build abgebrochen.")
        return 1
    print(f"\nOK ({len(warnungen)} Warnungen).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
