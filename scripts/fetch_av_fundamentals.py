"""Alpha Vantage BALANCE_SHEET + CASH_FLOW (quarterly) for every name in a fixture. D443's pull; the spec (0fa0d5c) was committed
before this file, and no statistic is computed here. Paced at the key's 66/min, cached, resumable; the key is read from ALPHAVANTAGE_API_KEY or
~/.config/alphavantage/key and is NEVER printed or logged. Raw JSON under data/raw/alphavantage/fundamentals/<SYM>_{bs,cf}.json.gz
(git-ignored, D191: cache the raw, commit the derived). A response carrying "Error Message" / "Note" / "Information" or no
quarterlyReports key is recorded in the manifest and NOT cached, so it is re-requested next run.

    uv run python -u scripts/fetch_av_fundamentals.py --fixture us_shorts_daily_raw [--limit N]
"""
from __future__ import annotations
import argparse, gzip, http.client, json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request

REPO = pathlib.Path(__file__).resolve().parents[1]
API = "https://www.alphavantage.co/query"
KEY_FILE = pathlib.Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage" / "fundamentals"
MANIFEST = CACHE / "_manifest.json"
FUNCS = {"bs": "BALANCE_SHEET", "cf": "CASH_FLOW"}
MIN_INTERVAL = 60.0 / 66.0; TIMEOUT = 60; RETRIES = 3


def api_key():
    k = os.environ.get("ALPHAVANTAGE_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}.")


_last = [0.0]
def _pace():
    gap = time.monotonic() - _last[0]
    if gap < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - gap)
    _last[0] = time.monotonic()


def path_of(symbol, kind):
    return CACHE / f"{symbol}_{kind}.json.gz"


def load_cached(symbol, kind):
    p = path_of(symbol, kind)
    if not p.exists():
        return None
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, EOFError, json.JSONDecodeError):
        p.unlink(missing_ok=True); return None


def fetch(symbol, kind, key):
    """(status, n_quarterly). Cached and resumable; a cached file is never re-requested; an error response is never cached."""
    d = load_cached(symbol, kind)
    if d is not None:
        return "cached", len(d.get("quarterlyReports") or [])
    url = f"{API}?{urllib.parse.urlencode({'function': FUNCS[kind], 'symbol': symbol, 'apikey': key})}"
    for attempt in range(RETRIES):
        _pace()
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
                payload = json.loads(r.read().decode("utf-8", errors="replace"))
            break
        except (urllib.error.URLError, OSError, http.client.HTTPException, TimeoutError, json.JSONDecodeError) as e:
            if attempt == RETRIES - 1:
                return f"error: {type(e).__name__}", 0
            time.sleep(2.0 * (attempt + 1))
    for flag in ("Error Message", "Note", "Information"):
        if flag in payload:
            return flag, 0
    if payload == {}:
        return "empty", 0                                   # AV's answer for an unknown symbol: {}
    rows = payload.get("quarterlyReports")
    if not isinstance(rows, list):
        return "no quarterlyReports", 0
    CACHE.mkdir(parents=True, exist_ok=True)
    with gzip.open(path_of(symbol, kind), "wt", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return "ok", len(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fixture", default="us_shorts_daily_raw"); ap.add_argument("--limit", type=int, default=None); a = ap.parse_args()
    meta = json.loads((REPO / "data" / "fixtures" / f"{a.fixture}.meta.json").read_text()); syms = sorted(meta["symbols"]); syms = syms[:a.limit] if a.limit else syms
    key = api_key(); t0 = time.time(); man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    counts = {}; n_req = 0
    for i, s in enumerate(syms):
        for kind in FUNCS:
            st, n = fetch(s, kind, key); man[f"{s}_{kind}"] = {"status": st, "n_quarterly": n, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            counts[st.split(":")[0]] = counts.get(st.split(":")[0], 0) + 1; n_req += st != "cached"
        if (i + 1) % 50 == 0 or i + 1 == len(syms):
            CACHE.mkdir(parents=True, exist_ok=True); MANIFEST.write_text(json.dumps(man, indent=0))
            print(f"[{i+1:4d}/{len(syms)}] {s:6s} requests {n_req}  {counts}  {(time.time()-t0)/60:.1f} min", flush=True)
    print(f"done: {counts} in {(time.time()-t0)/60:.1f} min; manifest {MANIFEST.relative_to(REPO)}")


if __name__ == "__main__":
    main()
