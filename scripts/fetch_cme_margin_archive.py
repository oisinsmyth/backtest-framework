"""Fetch CME's margin histories and clearing advisories from the Internet Archive (D657 A1).

cmegroup.com refuses automated clients, so nothing here touches it. The Internet Archive's CDX index lists which
of CME's files it holds and when each was captured; this script reads that index, picks the LATEST capture of each
file, and downloads the raw capture (`/web/{timestamp}id_/{url}`), sequentially and at least ``--delay`` seconds
apart, backing off on 429/503.

    python scripts/fetch_cme_margin_archive.py --dry-run
    python scripts/fetch_cme_margin_archive.py --only history
    python scripts/fetch_cme_margin_archive.py --only advisories

Targets:
    history     CME's per-product margin histories (`clearing/risk-management/files/{code}_...`) for the 33 D657
                roots' clearing codes, "prior to 2009" files excluded;
    advisories  clearing advisories `Chadv{10..16}-{nnn}.pdf` (notice dates only).

Everything lands in the MAIN checkout's gitignored raw cache, ``data/raw/cme_margins/{history,advisories}/``, named
``{original file stem}__{capture timestamp}{ext}``; the CDX responses are saved beside them, and every attempt is
appended to ``fetch_log.jsonl`` (URL, capture timestamp, HTTP status, bytes, sha256, a magic-byte check). A file
already on disk is skipped, so a run can be resumed. A capture whose first bytes are not a PDF or a zip (the archive
sometimes stores an error page) is logged as ``bad_magic`` and not saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CDX = "https://web.archive.org/cdx/search/cdx"
UA = "BacktestFramework-research/1.0 (D657; polite sequential fetch)"
# the D657 roots' CME clearing codes (docs/decisions/D657-...: 33 breadth roots with a margin history)
CODES = {"06", "07", "11", "17", "21", "25", "26", "48", "AD", "BP", "BTC", "C", "CD", "CL", "EC", "GC",
         "HG", "HO", "JY", "LN", "ND", "NG", "NK", "PL", "RB", "S", "SF", "SI", "SP", "SR3", "TN", "UBE", "W"}
HIST_PREFIX = "cmegroup.com/clearing/risk-management/files/"
ADV_PREFIX = "cmegroup.com/tools-information/lookups/advisories/clearing/files/Chadv"
ADV_RE = re.compile(r"Chadv(1[0-6])-(\d{1,3})\.pdf$", re.I)
MAGIC = {".pdf": b"%PDF", ".zip": b"PK"}


def main_checkout() -> Path:
    here = Path(__file__).resolve().parent.parent
    for p in [here, *here.parents]:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
    return here


ROOT = main_checkout() / "data" / "raw" / "cme_margins"


def get(url: str, tries: int = 6) -> tuple[int, bytes]:
    wait = 30.0
    for k in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and k < tries - 1:
                print(f"  {e.code}; backing off {wait:.0f}s", flush=True)
                time.sleep(wait)
                wait = min(wait * 2, 600)
                continue
            return e.code, b""
        except (urllib.error.URLError, TimeoutError) as e:
            if k < tries - 1:
                print(f"  {type(e).__name__}; backing off {wait:.0f}s", flush=True)
                time.sleep(wait)
                wait = min(wait * 2, 600)
                continue
            return 0, b""
    return 0, b""


def cdx(prefix: str, save_as: str) -> list[list[str]]:
    q = (f"{CDX}?url={prefix}&matchType=prefix&output=json&fl=original,timestamp,statuscode,length"
         f"&filter=statuscode:200&limit=200000")
    status, body = get(q)
    if status != 200:
        raise SystemExit(f"CDX query failed ({status}) for {prefix}")
    (ROOT / save_as).write_bytes(body)
    return json.loads(body)[1:]


def latest(rows: list[list[str]], keep) -> dict[str, tuple[str, str, int]]:
    """file name -> (timestamp, original url, length) of its latest capture, for names ``keep`` accepts."""
    out: dict[str, tuple[str, str, int]] = {}
    for original, ts, _sc, ln in rows:
        name = original.split("?")[0].rsplit("/", 1)[-1]
        if not keep(name):
            continue
        key = name.lower()
        if key not in out or ts > out[key][0]:
            out[key] = (ts, original, int(ln) if ln.isdigit() else 0)
    return out


def keep_history(name: str) -> bool:
    m = re.match(r"([A-Za-z0-9]+)[-_]", name)
    low = name.lower()
    return bool(m) and m.group(1).upper() in CODES and "prior" not in low and "pror" not in low \
        and low.endswith((".pdf", ".zip"))


def keep_advisory(name: str) -> bool:
    return bool(ADV_RE.search(name))


def fetch(kind: str, picks: dict[str, tuple[str, str, int]], delay: float) -> None:
    dst_dir = ROOT / kind
    dst_dir.mkdir(parents=True, exist_ok=True)
    log = ROOT / "fetch_log.jsonl"
    done = saved = bad = 0
    t0 = time.time()
    for key in sorted(picks):
        ts, original, _ln = picks[key]
        name = original.split("?")[0].rsplit("/", 1)[-1]
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
        dst = dst_dir / f"{stem}__{ts}{ext}"
        done += 1
        if dst.exists() and dst.stat().st_size > 0:
            continue
        url = f"https://web.archive.org/web/{ts}id_/{original}"
        status, body = get(url)
        ok = status == 200 and body.startswith(MAGIC.get(ext, b""))
        rec = {"kind": kind, "file": dst.name, "original": original, "capture": ts, "url": url,
               "status": status, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest() if body else None,
               "result": "saved" if ok else ("bad_magic" if status == 200 else "failed"),
               "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec) + "\n")
        if ok:
            tmp = dst.with_suffix(dst.suffix + ".part")
            tmp.write_bytes(body)
            tmp.replace(dst)
            saved += 1
        else:
            bad += 1
        if done % 25 == 0:
            el = time.time() - t0
            print(f"[{kind}] {done}/{len(picks)} saved {saved} bad {bad} ({el / 60:.1f} min)", flush=True)
        time.sleep(delay)
    print(f"[{kind}] done: {done} considered, {saved} saved this run, {bad} not saved", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["history", "advisories"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delay", type=float, default=2.0)
    a = ap.parse_args()
    if a.delay < 1.5:
        raise SystemExit("--delay below 1.5 s is not allowed (D657 A1)")
    ROOT.mkdir(parents=True, exist_ok=True)
    kinds = [a.only] if a.only else ["history", "advisories"]
    plan = {}
    if "history" in kinds:
        plan["history"] = latest(cdx(HIST_PREFIX, "cdx_history.json"), keep_history)
        time.sleep(a.delay)
    if "advisories" in kinds:
        plan["advisories"] = latest(cdx(ADV_PREFIX, "cdx_advisories.json"), keep_advisory)
    for kind, picks in plan.items():
        mb = sum(v[2] for v in picks.values()) / 1e6
        print(f"[{kind}] {len(picks)} files, ~{mb:.1f} MB (CDX lengths), into {ROOT / kind}", flush=True)
    if a.dry_run:
        return
    for kind, picks in plan.items():
        fetch(kind, picks, a.delay)


if __name__ == "__main__":
    main()
