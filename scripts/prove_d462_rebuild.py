"""The joint run's guard on the D462 rebuild (JOINT_RUN_CHECKLIST V13): the ES/NQ/YM/RTY minute fixtures and the
session/roll tables must keep their in-sample rows (day <= 2023-12-29) byte for byte when D462 rebuilds them after the
pre-lapse top-up, or D716's, D737's and D734's in-sample known answers would refuse on the day.

    python scripts/prove_d462_rebuild.py --prove     # SYSTEM python: rebuild into temp/ (FIX and META redirected; the
                                                     #   real fixtures are never written) and compare with them
    python scripts/prove_d462_rebuild.py --record    # once: write data/d462_insample_text_sha256.json from the fixtures
    python scripts/prove_d462_rebuild.py --check     # after the real rebuild: the fixtures' in-sample text against it

Text hashes of the decompressed CSV (gzip headers carry a build time). Prints hashes and line counts only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
RECORD = REPO / "data" / "d462_insample_text_sha256.json"
TEMP_OUT = REPO / "temp" / "d462_rebuild_proof" / "out"
CUT = "2023-12-29"
FILES = ["fut_ES_rth_1m.csv.gz", "fut_NQ_rth_1m.csv.gz", "fut_YM_rth_1m.csv.gz", "fut_RTY_rth_1m.csv.gz",
         "fut_index_sessions.csv.gz", "fut_index_rolls.csv.gz"]


def text_sha(p: Path, cut: str | None = None) -> tuple[str, int]:
    """sha256 of the decompressed text: every line, or the header plus the rows dated <= cut. The minute files lead with
    the day; the session and roll tables lead with the root, then the day."""
    h = hashlib.sha256()
    n = 0
    with gzip.open(p, "rt", encoding="utf-8", newline="") as f:
        for i, line in enumerate(f):
            if cut is not None and i > 0:
                day = line[:10] if line[:2] == "20" else line.split(",", 2)[1]
                if day > cut:
                    continue
            h.update(line.encode("utf-8"))
            n += 1
    return h.hexdigest(), n


def prove() -> int:
    sys.path.insert(0, str(REPO / "scripts"))
    import build_fut_index_1m as M
    TEMP_OUT.mkdir(parents=True, exist_ok=True)
    M.FIX = TEMP_OUT
    M.META = TEMP_OUT / "fut_index_1m.meta.json"
    if M.fixture_path("NQ").parent != TEMP_OUT:
        raise SystemExit("the redirect failed; nothing was built")
    M.cmd_build(6)
    ok = True
    for name in FILES:
        fa, fb = text_sha(FIX / name), text_sha(TEMP_OUT / name)
        ca, cb = text_sha(FIX / name, CUT), text_sha(TEMP_OUT / name, CUT)
        ok &= ca == cb
        print(f"{name:28s} full {'IDENTICAL' if fa == fb else 'DIFFERS'} ({fa[1]} / {fb[1]} lines); <= {CUT} "
              f"{'IDENTICAL' if ca == cb else 'DIFFERS'} ({ca[1]} / {cb[1]})")
    print("PROOF:", "in-sample rows reproduce byte for byte" if ok else "AN IN-SAMPLE DIFFERENCE")
    return 0 if ok else 1


def record() -> int:
    if RECORD.exists():
        raise SystemExit(f"{RECORD.name} exists; it is written once")
    doc = {"cut": CUT, "what": "sha256 of the decompressed text: the header plus every row dated <= cut",
           "files": {name: dict(zip(("sha256", "lines"), text_sha(FIX / name, CUT))) for name in FILES}}
    RECORD.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, indent=1))
    return 0


def check() -> int:
    doc = json.loads(RECORD.read_text(encoding="utf-8"))
    bad = []
    for name, want in doc["files"].items():
        got = text_sha(FIX / name, doc["cut"])
        same = got[0] == want["sha256"] and got[1] == want["lines"]
        print(f"{name:28s} <= {doc['cut']} {'UNCHANGED' if same else 'CHANGED'} ({got[1]} lines)")
        if not same:
            bad.append(name)
    print("CHECK:", "the in-sample rows are unchanged" if not bad else f"CHANGED: {bad} -- stop before any vault step")
    return 0 if not bad else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prove", action="store_true")
    g.add_argument("--record", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(prove() if a.prove else record() if a.record else check())
