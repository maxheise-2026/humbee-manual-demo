"""Baut das Ingest-Paket für das LLM-Wiki.

Ergebnis in build/wiki/:
    pages/<id>.md      eine flache Datei je Handbuchseite, Bilder verlinkt
    assets/            alle verwendeten Screenshots
    manifest.json      Soll-Zustand dieser Quelle (alle Seiten mit Prüfsumme)
    changes.json       Delta gegen state/ingest-manifest.json (neu/geändert/gelöscht)

Chunking macht der Ingest-Agent. Dieses Skript liefert ihm saubere,
in sich verständliche Seiten mit stabilen IDs - mehr nicht.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone

import yaml

from common import (BUILD, ROOT, STATE, discover, git_commit, load_config,
                    rewrite_images, rewrite_links, sha256, strip_conditionals)

OUT = BUILD / "wiki"


def main() -> int:
    cfg = load_config()
    pages, _ = discover()
    by_relpath = {str(p.rel).replace("\\", "/"): p for p in pages}

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "pages").mkdir(parents=True)
    (OUT / "assets").mkdir(parents=True)

    commit = git_commit()
    manifest = {
        "source": cfg["wiki"]["source"],
        "id_prefix": cfg["wiki"]["id_prefix"],
        "manual_version": cfg["manual"]["version"],
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pages": {},
    }

    for p in pages:
        if not p.wanted_for("wiki"):
            continue

        body = strip_conditionals(p.body, "wiki")
        body = rewrite_links(p, body, "wiki", by_relpath, cfg)
        body = rewrite_images(body, "wiki")

        assets = []
        for bild in p.images():
            ziel = OUT / "assets" / bild.name
            if not ziel.exists():
                shutil.copy2(bild, ziel)
            assets.append({"path": f"assets/{bild.name}",
                           "sha256": sha256(bild.read_bytes())})

        # Frontmatter für den Ingest-Agenten: nur was er wirklich braucht.
        fm = {
            "id": cfg["wiki"]["id_prefix"] + p.id,
            "title": p.title,
            "summary": p.meta["summary"],
            "tags": p.meta.get("tags", []),
            "audience": p.meta.get("audience", []),
            "manual_version": cfg["manual"]["version"],
            "updated": str(p.meta["updated"]),
            "source": cfg["wiki"]["source"],
            "source_path": f"content/{p.rel.as_posix()}",
            "source_commit": commit,
        }
        text = ("---\n"
                + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
                + "---\n\n" + body.strip() + "\n")

        datei = OUT / "pages" / f"{p.id}.md"
        datei.write_text(text, encoding="utf-8")

        manifest["pages"][p.id] = {
            "wiki_id": fm["id"],
            "title": p.title,
            "summary": p.meta["summary"],
            "tags": p.meta.get("tags", []),
            "updated": str(p.meta["updated"]),
            "file": f"pages/{p.id}.md",
            "source_path": fm["source_path"],
            "sha256": sha256(text.encode("utf-8")),
            "assets": assets,
        }

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # --- Delta gegen den zuletzt ausgelieferten Stand ------------------------
    vorher_datei = STATE / "ingest-manifest.json"
    vorher = json.loads(vorher_datei.read_text(encoding="utf-8")) if vorher_datei.exists() else {"pages": {}}
    alt, neu = vorher.get("pages", {}), manifest["pages"]

    changes = []
    for pid, info in neu.items():
        if pid not in alt:
            changes.append({"action": "upsert", "reason": "neu", "id": pid, **info})
        elif alt[pid].get("sha256") != info["sha256"] or alt[pid].get("assets") != info["assets"]:
            changes.append({"action": "upsert", "reason": "geändert", "id": pid, **info})
    for pid, info in alt.items():
        if pid not in neu:
            changes.append({"action": "delete", "reason": "entfernt oder zurückgezogen",
                            "id": pid, "wiki_id": info.get("wiki_id"),
                            "title": info.get("title")})

    (OUT / "changes.json").write_text(json.dumps({
        "source": manifest["source"],
        "commit": commit,
        "based_on_commit": vorher.get("commit"),
        "generated_at": manifest["generated_at"],
        "changes": changes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"build/wiki/: {len(manifest['pages'])} Seiten, "
          f"{len(list((OUT / 'assets').glob('*')))} Bilder")
    if changes:
        for c in changes:
            print(f"  {c['action']:<7} {c['id']:<28} ({c['reason']})")
    else:
        print("  keine Änderungen gegenüber dem ausgelieferten Stand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
