"""Meldet die Änderungen aus build/wiki/changes.json beim Ingest-Agenten an.

Aufruf:
    python scripts/push_ingest.py --dry-run     # zeigt nur, was gesendet würde
    python scripts/push_ingest.py               # sendet wirklich

Erwartete Umgebungsvariablen (Namen stehen in manual.yml):
    HUMBEE_INGEST_ENDPOINT   z.B. https://wiki.intern/api/ingest
    HUMBEE_INGEST_TOKEN      Bearer-Token

Vertrag mit dem Agenten
-----------------------
Je Änderung ein POST als multipart/form-data:

    payload   JSON - Metadaten (siehe unten)
    document  die Markdown-Datei              (nur bei action=upsert)
    asset[]   die zugehörigen Bilddateien     (nur bei action=upsert)

payload = {
  "action": "upsert" | "delete",
  "source": "humbee-manual",          # damit der Agent weiß, welche Seiten aus
  "id": "humbee-manual/vorgang-anlegen",  # diesem Repo stammen und er sie ersetzen
  "title": ..., "summary": ..., "tags": [...],  # bzw. löschen darf
  "manual_version": "2026.9", "updated": "2026-09-14",
  "commit": "<git sha>",
  "assets": [{"filename": ..., "sha256": ...}]
}

Header  Idempotency-Key: <commit>:<id>
        -> ein erneut gesendeter Commit darf nichts duplizieren.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

import requests

from common import BUILD, STATE, load_config

OUT = BUILD / "wiki"
TIMEOUT = 60
VERSUCHE = 3


def main() -> int:
    dry = "--dry-run" in sys.argv
    cfg = load_config()

    changes_datei = OUT / "changes.json"
    if not changes_datei.exists():
        print("FEHLER: build/wiki/changes.json fehlt - erst scripts/build_wiki.py ausführen")
        return 1
    changes = json.loads(changes_datei.read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))

    if not changes["changes"]:
        print("Keine Änderungen - nichts zu senden.")
        return 0

    endpoint = os.environ.get(cfg["wiki"]["endpoint_env"], "")
    token = os.environ.get(cfg["wiki"]["token_env"], "")
    if not dry and not endpoint:
        print(f"FEHLER: {cfg['wiki']['endpoint_env']} ist nicht gesetzt")
        return 1

    protokoll = []
    for c in changes["changes"]:
        payload = {
            "action": c["action"],
            "source": changes["source"],
            "id": c.get("wiki_id") or (cfg["wiki"]["id_prefix"] + c["id"]),
            "commit": changes["commit"],
            "manual_version": manifest["manual_version"],
            "title": c.get("title"),
            "summary": c.get("summary"),
            "tags": c.get("tags", []),
            "updated": c.get("updated"),
            "source_path": c.get("source_path"),
            "assets": [{"filename": a["path"].split("/")[-1], "sha256": a["sha256"]}
                       for a in c.get("assets", [])],
        }
        kopf = {"Idempotency-Key": f"{changes['commit']}:{c['id']}"}
        if token:
            kopf["Authorization"] = f"Bearer {token}"

        if dry:
            n = len(payload["assets"])
            print(f"  {c['action']:<7} {payload['id']:<38} "
                  f"{'+ ' + str(n) + ' Bild(er)' if n else ''}")
            protokoll.append(payload)
            continue

        dateien = []
        try:
            if c["action"] == "upsert":
                dateien.append(("document", ((OUT / c["file"]).name,
                                             (OUT / c["file"]).open("rb"), "text/markdown")))
                for a in c.get("assets", []):
                    pfad = OUT / a["path"]
                    dateien.append(("asset", (pfad.name, pfad.open("rb"), "image/png")))
            dateien.append(("payload", (None, json.dumps(payload, ensure_ascii=False),
                                        "application/json")))

            for versuch in range(1, VERSUCHE + 1):
                try:
                    r = requests.post(endpoint, files=dateien, headers=kopf, timeout=TIMEOUT)
                    if r.status_code < 300:
                        print(f"  OK      {payload['id']} ({r.status_code})")
                        protokoll.append(payload)
                        break
                    if r.status_code < 500:
                        print(f"  FEHLER  {payload['id']} -> {r.status_code} {r.text[:200]}")
                        return 1
                    raise requests.RequestException(f"{r.status_code}")
                except requests.RequestException as e:
                    if versuch == VERSUCHE:
                        print(f"  FEHLER  {payload['id']} nach {VERSUCHE} Versuchen: {e}")
                        return 1
                    time.sleep(2 ** versuch)
        finally:
            for _, teil in dateien:
                if isinstance(teil, tuple) and hasattr(teil[1], "close"):
                    teil[1].close()

    if dry:
        ziel = OUT / "ingest-payload.json"
        ziel.write_text(json.dumps(protokoll, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"\nProbelauf: {len(protokoll)} Anfragen, nichts gesendet.")
        print(f"Vorschau der Payloads: {ziel.relative_to(ziel.parents[2])}")
        return 0

    # Erst wenn ALLES durch ist, wird der neue Soll-Zustand festgeschrieben.
    # Diese Datei wird committet - sie ist das Gedächtnis für das nächste Delta.
    STATE.mkdir(exist_ok=True)
    shutil.copy2(OUT / "manifest.json", STATE / "ingest-manifest.json")
    print(f"\n{len(protokoll)} Änderungen übertragen, state/ingest-manifest.json aktualisiert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
