"""Gemeinsame Bausteine für alle Builds.

Eine Quelle (content/), zwei Ziele:
  build/wiki/   -> Paket für den Ingest-Agenten des LLM-Wikis
  build/print/  -> Quarto-Projekt, aus dem das PDF entsteht
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ASSETS = CONTENT / "assets"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
STATE = ROOT / "state"

PFLICHTFELDER = ["id", "title", "summary", "version", "updated", "status", "tags", "audience"]
ERLAUBTE_STATUS = {"entwurf", "review", "freigegeben"}

RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_COND_OPEN = re.compile(r"^:{3,}\s*\{?\s*\.(print-only|wiki-only)\s*\}?\s*$")
RE_COND_CLOSE = re.compile(r"^:{3,}\s*$")
RE_MD_LINK = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+?\.md)(#[^)]*)?\)")
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(\s+\"[^\"]*\")?\)(\{[^}]*\})?")


# ---------------------------------------------------------------- Konfiguration
def load_config() -> dict:
    return yaml.safe_load((ROOT / "manual.yml").read_text(encoding="utf-8"))


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "arbeitskopie"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ Datenmodell
@dataclass
class Page:
    path: Path                 # absoluter Pfad
    rel: Path                  # relativ zu content/
    meta: dict
    body: str                  # Markdown ohne Frontmatter
    chapter: "Chapter | None"
    order: tuple

    @property
    def id(self) -> str:
        return self.meta["id"]

    @property
    def title(self) -> str:
        return self.meta["title"]

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "entwurf")).lower()

    def wanted_for(self, target: str) -> bool:
        """target: 'wiki' | 'print'"""
        if self.status != "freigegeben":
            return False
        return bool(self.meta.get(target, True))

    def images(self) -> list[Path]:
        out = []
        for m in RE_IMAGE.finditer(self.body):
            src = m.group(2)
            if src.startswith(("http://", "https://", "data:")):
                continue
            out.append((self.path.parent / src).resolve())
        return out


@dataclass
class Chapter:
    dir: Path
    title: str
    order: int
    intro: str = ""
    unnumbered: bool = False
    pages: list[Page] = field(default_factory=list)


def _prefix(name: str) -> int:
    m = re.match(r"^(\d+)[-_]", name)
    return int(m.group(1)) if m else 9999


def parse_page(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    m = RE_FRONTMATTER.match(raw)
    if not m:
        return {}, raw
    return yaml.safe_load(m.group(1)) or {}, raw[m.end():]


def discover() -> tuple[list[Page], list[Chapter]]:
    """Liest content/ ein. Reihenfolge ergibt sich aus den Zahlenpräfixen von
    Ordner- und Dateinamen; 'order' im Frontmatter überschreibt das."""
    chapters: list[Chapter] = []
    pages: list[Page] = []

    # Seiten direkt in content/ (Vorwort, Impressum ...) - vor allen Kapiteln
    for f in sorted(CONTENT.glob("*.md")):
        meta, body = parse_page(f)
        p = Page(f, f.relative_to(CONTENT), meta, body, None,
                 (0, meta.get("order", _prefix(f.name))))
        pages.append(p)

    for d in sorted(x for x in CONTENT.iterdir() if x.is_dir() and x.name != "assets"):
        kfile = d / "_kapitel.yml"
        kmeta = yaml.safe_load(kfile.read_text(encoding="utf-8")) if kfile.exists() else {}
        ch = Chapter(d, kmeta.get("title", d.name), int(kmeta.get("order", _prefix(d.name))),
                     kmeta.get("intro", "") or "", bool(kmeta.get("unnumbered", False)))
        for f in sorted(d.glob("*.md")):
            meta, body = parse_page(f)
            p = Page(f, f.relative_to(CONTENT), meta, body, ch,
                     (ch.order, meta.get("order", _prefix(f.name))))
            ch.pages.append(p)
            pages.append(p)
        chapters.append(ch)

    chapters.sort(key=lambda c: c.order)
    for c in chapters:
        c.pages.sort(key=lambda p: p.order)
    pages.sort(key=lambda p: p.order)
    return pages, chapters


# ------------------------------------------------------------- Transformationen
def strip_conditionals(body: str, target: str) -> str:
    """Entfernt ::: {.wiki-only} / ::: {.print-only} Blöcke des jeweils
    anderen Ziels und löst die Markierung des eigenen Ziels auf."""
    keep = f"{target}-only"
    out, skipping, unwrapping = [], False, False
    for line in body.splitlines():
        if skipping or unwrapping:
            if RE_COND_CLOSE.match(line):
                skipping = unwrapping = False
                continue
            if skipping:
                continue
            out.append(line)
            continue
        m = RE_COND_OPEN.match(line)
        if m:
            if m.group(1) == keep:
                unwrapping = True
            else:
                skipping = True
            continue
        out.append(line)
    return "\n".join(out)


def rewrite_links(page: Page, body: str, target: str, by_relpath: dict[str, Page],
                  cfg: dict) -> str:
    """Interne .md-Verweise in ein Ziel umschreiben, das im jeweiligen Medium
    funktioniert. Unaufgelöste Verweise bleiben als Klartext stehen."""
    def repl(m):
        text, href = m.group(1), m.group(2)
        tgt = (page.path.parent / href).resolve()
        try:
            key = str(tgt.relative_to(CONTENT)).replace("\\", "/")
        except ValueError:
            return m.group(0)
        dest = by_relpath.get(key)
        if dest is None:
            return text
        if target == "wiki":
            return f"[{text}]({cfg['wiki']['id_prefix']}{dest.id})"
        return f"[{text}](#sec-{dest.id})"
    return RE_MD_LINK.sub(repl, body)


def rewrite_images(body: str, target: str) -> str:
    """Bilder liegen im Build flach unter assets/. Attribute ({width=...})
    bleiben für den Druck erhalten und fallen im Wiki weg."""
    def repl(m):
        alt, src, title, attrs = m.group(1), m.group(2), m.group(3) or "", m.group(4) or ""
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        new = f"assets/{Path(src).name}"
        if target == "wiki":
            return f"![{alt}]({new}{title})"
        return f"![{alt}]({new}{title}){attrs}"
    return RE_IMAGE.sub(repl, body)


def demote_headings(body: str, levels: int = 1) -> str:
    """H1 -> H2 usw., damit mehrere Seiten zu einem Kapitel zusammenwachsen."""
    out = []
    fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{1,5} ", line):
            line = "#" * levels + line
        out.append(line)
    return "\n".join(out)
