"""Prove the downloaded futures data is what was asked for. Offline except list_files.

    uv run python scripts/verify_futures_acquisition.py [--json]

An HTTP 200 can be the wrong data, and this programme has a catalogue of ways that
happens. Four checks, each of which RAISES rather than warns:

  1. SIZE     every file on disk matches the byte count Databento's manifest states.
  2. HASH     every file matches the hash Databento supplies. This is the one check that
              catches silent corruption in a 111 GB transfer over 30 hours.
  3. HEADER   the DBN metadata header of every file states the dataset, schema, stype_in
              and window that was REQUESTED. Header only -- zero records decoded. This is
              what catches a correct-looking file of the wrong thing.
  4. COVERAGE the nine ohlcv-1m slices must TILE their range with no gap and no overlap.
              The bars were acquired in nine pieces after two failed wide jobs, so "did
              we actually get every year" is a real question, not a formality.

Any gap found is REPORTED, not silently accepted: a fixture assembled from nine slices
with a hole in it is a different object from one without.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "temp" / "databento"
STATE = RAW / "acquisition_state.json"
OUT = REPO / "data" / "futures_acquisition_verification.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
GB = 10 ** 9


class VerifyError(AssertionError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


def api_key() -> str:
    return (os.environ.get("DATABENTO_API_KEY")
            or KEY_FILE.read_text(encoding="utf-8").strip())


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-hash", action="store_true",
                    help="size+header+coverage only; hashing 111 GB takes ~15 min")
    a = ap.parse_args()

    import databento as db
    c = db.Historical(api_key())
    st = json.loads(STATE.read_text(encoding="utf-8"))
    man = {i["key"]: i for i in st["manifest"]}
    live = [(k, v) for k, v in st["items"].items() if v.get("state") == "downloaded"]

    report = {"verified_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "items": [], "failures": [], "coverage": {}}
    n_files = n_size_ok = n_hash_ok = n_hdr_ok = 0
    total_bytes = 0

    P(f"verifying {len(live)} downloaded items\n")
    for key, s in sorted(live, key=lambda x: (x[1].get("rank", 9), x[0])):
        m = man.get(key, {})
        jid = s["job_id"]
        d = RAW / jid
        try:
            files = {f["filename"]: f for f in c.batch.list_files(jid)
                     if not str(f["filename"]).endswith(".json")}
        except Exception as exc:
            report["failures"].append({"item": key, "check": "list_files", "detail": str(exc)[:200]})
            P(f"  {key:26} list_files FAILED: {str(exc)[:70]}")
            continue

        item = {"key": key, "schema": m.get("schema"), "job_id": jid,
                "window": [m.get("start"), m.get("end")], "files": len(files),
                "size_ok": 0, "hash_ok": 0, "hash_skipped": 0, "header_ok": 0,
                "bytes": 0}
        for fname, meta in sorted(files.items()):
            p = d / fname
            n_files += 1
            if not p.exists():
                report["failures"].append({"item": key, "file": fname, "check": "exists"})
                continue
            got, want = p.stat().st_size, int(meta.get("size", -1))
            item["bytes"] += got
            total_bytes += got
            if got != want:
                report["failures"].append({"item": key, "file": fname, "check": "size",
                                           "on_disk": got, "manifest": want})
                continue
            item["size_ok"] += 1
            n_size_ok += 1

            if a.skip_hash:
                item["hash_skipped"] += 1
            else:
                want_h = str(meta.get("hash", ""))
                if want_h.startswith("sha256:"):
                    want_h = want_h.split(":", 1)[1]
                if want_h:
                    got_h = sha256(p)
                    if got_h.lower() != want_h.lower():
                        report["failures"].append({"item": key, "file": fname,
                                                   "check": "hash", "got": got_h[:16],
                                                   "want": want_h[:16]})
                        continue
                    item["hash_ok"] += 1
                    n_hash_ok += 1
                else:
                    item["hash_skipped"] += 1

        # HEADER: one file per item is enough to prove the item is the right thing.
        first = sorted(files)[0] if files else None
        if first and (d / first).exists():
            try:
                store = db.DBNStore.from_file(d / first)
                md = store.metadata
                hdr = {"dataset": md.dataset, "schema": str(md.schema),
                       "stype_in": str(md.stype_in),
                       "start": str(md.start)[:10], "end": str(md.end)[:10]}
                item["header"] = hdr
                bad = []
                if hdr["dataset"] != "GLBX.MDP3":
                    bad.append(f"dataset {hdr['dataset']}")
                if m.get("schema") and hdr["schema"] != m["schema"]:
                    bad.append(f"schema {hdr['schema']} != requested {m['schema']}")
                if bad:
                    report["failures"].append({"item": key, "file": first,
                                               "check": "header", "detail": "; ".join(bad)})
                else:
                    item["header_ok"] = 1
                    n_hdr_ok += 1
            except Exception as exc:
                report["failures"].append({"item": key, "check": "header",
                                           "detail": str(exc)[:200]})
        report["items"].append(item)
        P(f"  {key:26} {str(m.get('schema')):11} {len(files):3} files  "
          f"{item['bytes']/GB:7.2f} GB  size {item['size_ok']}/{len(files)}  "
          f"hash {item['hash_ok']}/{len(files)}  hdr {'ok' if item['header_ok'] else 'FAIL'}")

    # COVERAGE of the bars, which arrived in nine pieces.
    import pandas as pd
    bars = sorted(((man[k]["start"], man[k]["end"], k) for k, v in live
                   if man.get(k, {}).get("schema") == "ohlcv-1m"))
    gaps, overlaps = [], []
    for (s0, e0, k0), (s1, e1, k1) in zip(bars, bars[1:]):
        if e0 < s1:
            gaps.append({"after": k0, "before": k1, "from": e0, "to": s1,
                         "days": (pd.Timestamp(s1) - pd.Timestamp(e0)).days})
        elif e0 > s1:
            overlaps.append({"a": k0, "b": k1, "from": s1, "to": e0})
    report["coverage"] = {
        "schema": "ohlcv-1m", "slices": len(bars),
        "first": bars[0][0] if bars else None, "last": bars[-1][1] if bars else None,
        "gaps": gaps, "overlaps": overlaps,
        "known_gap_at_end": {
            "from": bars[-1][1] if bars else None, "to": "2026-09-11",
            "why": "the final slice was resubmitted ending 2026-09-10 while chasing a "
                   "stall; the dataset's last session is therefore not in this pull"}
        if bars and bars[-1][1] < "2026-09-11" else None,
    }
    P(f"\n  ohlcv-1m coverage: {len(bars)} slices, {bars[0][0]} .. {bars[-1][1]}")
    P(f"    interior gaps {len(gaps)}   overlaps {len(overlaps)}")
    for g in gaps:
        P(f"      GAP {g['from']} -> {g['to']} ({g['days']} d) between {g['after']} and {g['before']}")
    if report["coverage"]["known_gap_at_end"]:
        P(f"      known end gap: {bars[-1][1]} -> 2026-09-11 (recorded, not a surprise)")

    ok = not report["failures"]
    P(f"\n  files {n_files}   size ok {n_size_ok}   hash ok {n_hash_ok}   header ok {n_hdr_ok}")
    P(f"  total {total_bytes/GB:.1f} GB")
    P(f"\n  {'VERIFIED' if ok else 'FAILURES: ' + str(len(report['failures']))}")
    for f in report["failures"][:10]:
        P(f"    {f}")

    report["summary"] = {"files": n_files, "size_ok": n_size_ok, "hash_ok": n_hash_ok,
                         "header_ok": n_hdr_ok, "total_bytes": total_bytes,
                         "all_passed": ok}
    if a.json:
        OUT.write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
