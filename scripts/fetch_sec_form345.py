"""SEC Insider Transactions Data Sets (Form 3/4/5), one zip per calendar quarter, 2006q1 .. 2026q1. D454's pull; spec 4ce4b86 committed
before this file. Fair access as D331: the repo's project User-Agent, <= 2 requests/s, cached under data/raw/edgar/form345/ (git-ignored),
resumable, a 404 recorded and never refetched. No statistic is computed here.

    uv run python -u scripts/fetch_sec_form345.py [--start 2006q1] [--end 2026q1]
"""
from __future__ import annotations
import argparse, io, json, time, zipfile
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "raw" / "edgar" / "form345"; MANIFEST = CACHE / "_manifest.json"
USER_AGENT = "BacktestFramework research script research@backtest-framework.org"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{q}_form345.zip"
MIN_INTERVAL = 0.5; TIMEOUT = 180; NEED = ("SUBMISSION.tsv", "REPORTINGOWNER.tsv", "NONDERIV_TRANS.tsv")


def quarters(start, end):
    y0, q0 = int(start[:4]), int(start[-1]); y1, q1 = int(end[:4]), int(end[-1]); out = []
    y, q = y0, q0
    while (y, q) <= (y1, q1):
        out.append(f"{y}q{q}"); q += 1
        if q == 5:
            y, q = y + 1, 1
    return out


def path_of(q):
    return CACHE / f"{q}_form345.zip"


def fetch(q, session, man):
    p = path_of(q)
    if p.exists():
        try:
            with zipfile.ZipFile(p) as z:
                names = set(z.namelist()); assert all(n in names for n in NEED)
            return "cached", p.stat().st_size
        except (zipfile.BadZipFile, AssertionError, OSError):
            p.unlink(missing_ok=True)
    if man.get(q, {}).get("status") == "404":
        return "404", 0
    backoff = 2.0
    for attempt in range(5):
        time.sleep(MIN_INTERVAL)
        try:
            r = session.get(URL.format(q=q), timeout=TIMEOUT)
        except requests.RequestException:
            time.sleep(backoff); backoff = min(backoff * 2, 60); continue
        if r.status_code == 200:
            try:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    names = set(z.namelist()); assert all(n in names for n in NEED)
            except (zipfile.BadZipFile, AssertionError):
                time.sleep(backoff); backoff = min(backoff * 2, 60); continue
            CACHE.mkdir(parents=True, exist_ok=True); p.write_bytes(r.content); return "ok", len(r.content)
        if r.status_code == 404:
            return "404", 0
        time.sleep(max(backoff, 10.0) if r.status_code in (403, 429) else backoff); backoff = min(backoff * 2, 60)
    return "giveup", 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--start", default="2006q1"); ap.add_argument("--end", default="2026q1"); a = ap.parse_args()
    qs = quarters(a.start, a.end); man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}; session = requests.Session(); session.headers.update(HEADERS)
    t0 = time.time(); counts = {}; total = 0
    for i, q in enumerate(qs):
        st, n = fetch(q, session, man); man[q] = {"status": st, "bytes": n, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}; counts[st] = counts.get(st, 0) + 1; total += n
        if (i + 1) % 10 == 0 or i + 1 == len(qs):
            CACHE.mkdir(parents=True, exist_ok=True); MANIFEST.write_text(json.dumps(man, indent=1)); print(f"[{i+1:3d}/{len(qs)}] {q} {counts}  {total/1e6:.0f} MB  {(time.time()-t0)/60:.1f} min", flush=True)
    print(f"done: {counts}; {total/1e6:.0f} MB; {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
