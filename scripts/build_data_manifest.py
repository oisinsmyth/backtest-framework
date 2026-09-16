"""The manifest that replaces the bulk data in git: one line per untracked panel.

    python scripts/build_data_manifest.py --build     # writes data/data_manifest.json
    python scripts/build_data_manifest.py --verify    # re-hashes on-disk files against it
    python scripts/build_data_manifest.py --status

WHY THIS EXISTS
---------------
`data/fixtures/*.csv.gz` and friends were committed on purpose, not by accident: D70/D24 wanted a
snapshot whose CHANGE IS A VISIBLE DIFF rather than a silent re-fetch, and the cheapest way to get
that property is to put the bytes in git. It worked -- and it cost 844 MB across 115 files, in a
repository whose source is 21k lines.

The 2026-09-15 repack drops those bytes from the index and keeps the property. For every file it
stops tracking, this manifest records:

  * **`sha256`** -- so a changed panel is still a visible diff. The diff moves from the blob to
    this file, which is the point: one line changing in a tracked JSON is MORE readable than a
    46 MB gzip blob that no reviewer opens.
  * **`git_blob`** -- the blob id the file had at the last commit that tracked it. History is not
    rewritten, so every byte is still there:

        git cat-file blob <git_blob> > data/fixtures/<name>

    That is the recovery path, and it is why the repack is not a deletion.
  * **`bytes`**, and whether the `.meta.json` / `_events.json` sidecar (which STAYS tracked, being
    small and being the provenance record) is present beside it.

WHAT IT DOES NOT DO
-------------------
It does not fetch. A file listed here and missing from disk is missing -- the manifest says what
it should be, not where to buy it. The fetchers named in each sidecar's `meta.json` are the
re-acquisition path, and for the vendor data `docs/data-available.md` is the index.

**Nothing here reads a price.** If a function in this file parses a bar, it is a bug.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "data_manifest.json"

# The formats the repack stops tracking. Plain .csv and .json stay in git: the largest tracked
# .csv under data/ is 0.6 MB and the JSONs are the artifacts decision records quote -- evidence,
# not panels (CLAUDE.md: "a file a record quotes is evidence: it belongs in data/").
BULK_SUFFIXES = (".csv.gz", ".parquet", ".npz", ".zip")

SIDECAR_SUFFIXES = (".meta.json", "_events.json")


def is_bulk(path: Path) -> bool:
    name = path.name
    return any(name.endswith(s) for s in BULK_SUFFIXES)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blobs() -> dict[str, str]:
    """`path -> blob id` for everything the index still holds.

    Run BEFORE the `git rm --cached`, the ids are live; run after, this returns nothing for the
    repacked files and the manifest keeps whatever it already recorded. Losing an id silently is
    the one failure that would make the recovery path above a lie, so a rebuild never overwrites
    a known blob id with a blank.
    """
    out = subprocess.run(
        ["git", "ls-files", "-s", "data"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    blobs: dict[str, str] = {}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 2:
            blobs[path] = parts[1]
    return blobs


def scan(previous: dict) -> dict:
    blobs = git_blobs()
    prev_files = {f["path"]: f for f in previous.get("files", [])}

    files = []
    for path in sorted((REPO / "data").rglob("*")):
        if not path.is_file() or not is_bulk(path):
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith("data/raw/") or rel.startswith("data/snapshots/"):
            continue  # the vendor cache, never tracked, indexed by docs/data-available.md

        stem = path.name
        for suffix in BULK_SUFFIXES:
            stem = stem[: -len(suffix)] if stem.endswith(suffix) else stem
        sidecars = sorted(
            p.relative_to(REPO).as_posix()
            for s in SIDECAR_SUFFIXES
            for p in [path.parent / f"{stem}{s}"]
            if p.exists()
        )

        blob = blobs.get(rel) or prev_files.get(rel, {}).get("git_blob")
        files.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256_of(path),
                "git_blob": blob,
                "sidecars": sidecars,
            }
        )

    return {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # The note is read by a human opening the manifest, so it has to be true of EVERY entry
        # below it, not of most of them. Until 2026-09-16 it said flatly that these panels were
        # "dropped from the index", which D538 made false for two of the 118: the two smallest
        # crypto panels (0.2 MB and 6.7 MB) are tracked again by an explicit `.gitignore`
        # negation, because between them they unblock 73 of a clone's skips for under 5% of the
        # index. They stay listed here deliberately -- `scan()` selects by SUFFIX and has no
        # tracked/untracked filter, `cmd_verify()` below hashes the disk and never consults git,
        # and `git_blobs()` records the LIVE blob id for a tracked file rather than a stale
        # historical one. So a tracked panel gets a stronger check here, not a redundant one.
        # (tests/conftest.py builds its panel-skip allowlist from these basenames; a tracked
        # panel in that set is inert while the file is present, and is the right behaviour if it
        # ever is not.)
        "note": (
            "Every bulk panel under data/, listed by suffix and regardless of whether git tracks "
            "it. Most were dropped from the index on 2026-09-15 (D536) and are recoverable from "
            "history: `git cat-file blob <git_blob> > <path>` -- history is not rewritten. A few "
            "small ones are tracked again by an explicit .gitignore negation (D538, 2026-09-16) "
            "and are simply present in a clone. --verify re-hashes what is on disk either way."
        ),
        "suffixes": list(BULK_SUFFIXES),
        "total_bytes": sum(f["bytes"] for f in files),
        "count": len(files),
        "files": files,
    }


def load() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def cmd_build() -> int:
    manifest = scan(load())
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    missing_blob = [f["path"] for f in manifest["files"] if not f["git_blob"]]
    print(
        f"{manifest['count']} files, {manifest['total_bytes'] / 1048576:.1f} MB -> "
        f"{MANIFEST.relative_to(REPO).as_posix()}"
    )
    if missing_blob:
        print(f"  no blob id for {len(missing_blob)} file(s) -- never committed:")
        for p in missing_blob[:10]:
            print(f"    {p}")
    return 0


def cmd_verify() -> int:
    manifest = load()
    if not manifest:
        print("no manifest -- run --build first")
        return 1

    missing, changed = [], []
    for entry in manifest["files"]:
        path = REPO / entry["path"]
        if not path.exists():
            missing.append(entry["path"])
        elif sha256_of(path) != entry["sha256"]:
            changed.append(entry["path"])

    print(f"{len(manifest['files'])} listed, {len(missing)} missing, {len(changed)} changed")
    for p in missing:
        print(f"  MISSING  {p}")
    for p in changed:
        print(f"  CHANGED  {p}")
    # A changed panel is a study whose numbers may have moved underneath it. That is the exact
    # event D70 committed the bytes to make visible, so it is an error, not a warning.
    return 1 if changed else 0


def cmd_status() -> int:
    manifest = load()
    if not manifest:
        print("no manifest")
        return 1
    on_disk = sum(1 for f in manifest["files"] if (REPO / f["path"]).exists())
    print(f"built_at     {manifest['built_at']}")
    print(f"listed       {manifest['count']} files, {manifest['total_bytes'] / 1048576:.1f} MB")
    print(f"on disk      {on_disk}")
    print(f"recoverable  {sum(1 for f in manifest['files'] if f['git_blob'])} have a blob id")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.build:
        return cmd_build()
    if args.verify:
        return cmd_verify()
    if args.status:
        return cmd_status()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
