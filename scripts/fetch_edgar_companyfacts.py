"""SEC XBRL companyfacts, one document per CIK, for every CIK the fixture's D331 resolution names. D444's pull; spec f0d97af
committed before this file. Fair access as D331: the repo's project User-Agent, <= MAX_RPS requests/s across THREADS workers, gzip
cache under data/raw/edgar/companyfacts/CIK##########.json.gz (git-ignored), 404 recorded in the manifest and never refetched,
40 consecutive failures abort. No statistic is computed here.

    uv run python -u scripts/fetch_edgar_companyfacts.py [--limit N] [--threads 4]
"""
from __future__ import annotations
import argparse, gzip, json, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
DEALS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_deals.json"
CACHE = REPO / "data" / "raw" / "edgar" / "companyfacts"; MANIFEST = CACHE / "_manifest.json"
USER_AGENT = "BacktestFramework research script research@backtest-framework.org"       # D331's project contact; SEC fair-access policy
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
MAX_RPS = 8.0; THREADS = 4; TIMEOUT = 90; MAX_CONSECUTIVE = 40


class Pacer:
    def __init__(self, rps):
        self.min_interval = 1.0 / rps; self.lock = threading.Lock(); self.next_slot = 0.0
    def wait(self):
        with self.lock:
            t = max(time.monotonic(), self.next_slot); self.next_slot = t + self.min_interval
        d = t - time.monotonic()
        if d > 0:
            time.sleep(d)


def ciks_needed():
    res = json.loads(DEALS.read_text())["resolution"]; out = {}
    for sym, r in res.items():
        for c in r.get("ciks") or ([{"cik": r["cik"]}] if r.get("cik") else []):
            out.setdefault(c["cik"], set()).add(sym)
    return {k: sorted(v) for k, v in out.items()}


def path_of(cik):
    return CACHE / f"CIK{cik}.json.gz"


def fetch_one(cik, session, pacer, state):
    p = path_of(cik)
    if p.exists():
        return "cached"
    if state["abort"]:
        return "aborted"
    backoff = 1.0
    for attempt in range(6):
        pacer.wait()
        try:
            r = session.get(URL.format(cik=cik), timeout=TIMEOUT)
        except requests.RequestException as e:
            time.sleep(backoff); backoff = min(backoff * 2, 60); continue
        if r.status_code == 200:
            try:
                j = r.json(); assert "facts" in j
            except Exception:
                time.sleep(backoff); backoff = min(backoff * 2, 60); continue
            CACHE.mkdir(parents=True, exist_ok=True)
            with gzip.open(p, "wt", encoding="utf-8") as fh:
                json.dump(j, fh)
            with state["lock"]:
                state["consecutive"] = 0
            return "ok"
        if r.status_code == 404:
            return "404"
        with state["lock"]:
            state["consecutive"] += 1
            if state["consecutive"] >= MAX_CONSECUTIVE:
                state["abort"] = True; return "aborted"
        time.sleep(max(backoff, 10.0) if r.status_code in (403, 429) else backoff); backoff = min(backoff * 2, 60)
    return "giveup"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=None); ap.add_argument("--threads", type=int, default=THREADS); a = ap.parse_args()
    need = ciks_needed(); ciks = sorted(need)[: a.limit] if a.limit else sorted(need)
    man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    todo = [c for c in ciks if not path_of(c).exists() and man.get(c, {}).get("status") != "404"]
    print(f"{len(need)} CIKs for {sum(len(v) for v in need.values())} symbol-links; {len(ciks) - len(todo)} cached or 404; fetching {len(todo)} at <= {MAX_RPS} rps on {a.threads} threads", flush=True)
    session = requests.Session(); session.headers.update(HEADERS); pacer = Pacer(MAX_RPS); state = dict(lock=threading.Lock(), consecutive=0, abort=False)
    t0 = time.time(); counts = {}; done = 0
    def work(cik):
        st = fetch_one(cik, session, pacer, state); return cik, st
    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        for cik, st in ex.map(work, todo):
            man[cik] = {"status": st, "symbols": need[cik], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}; counts[st] = counts.get(st, 0) + 1; done += 1
            if done % 100 == 0 or done == len(todo):
                CACHE.mkdir(parents=True, exist_ok=True); MANIFEST.write_text(json.dumps(man, indent=0))
                print(f"[{done:4d}/{len(todo)}] {counts}  {(time.time()-t0)/60:.1f} min", flush=True)
    for c in ciks:
        if path_of(c).exists() and c not in man:
            man[c] = {"status": "ok", "symbols": need[c], "at": "cached"}
    CACHE.mkdir(parents=True, exist_ok=True); MANIFEST.write_text(json.dumps(man, indent=0))
    print(f"done: {counts}; abort={state['abort']}; {(time.time()-t0)/60:.1f} min; cache {sum(p.stat().st_size for p in CACHE.glob('*.json.gz'))/1e6:.0f} MB")


if __name__ == "__main__":
    main()
