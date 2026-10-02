"""Fetch SHFE daily per-contract quotes (2016-2023) and, for candidate big-move days only, the per-contract daily limit
file, into data/raw/shfe_daily/ (gitignored). For the limit-lock spillover line (principal-approved 2026-10-02: "Yes,
download").

  quotes  https://www.shfe.com.cn/data/tradedata/future/dailydata/kx{YYYYMMDD}.dat          (one per trading day; 404 = no
          trading that day, which is NOT a refusal)
  limits  https://www.shfe.com.cn/data/busiparamdata/future/ContractDailyTradeArgument{YYYYMMDD}.dat   (UPPER_VALUE /
          LOWER_VALUE, the limit in force ON that trading day; fetched only where a target metal's contract moved >= 3.5%
          from its prior settlement with volume >= 100)

Honest client (a plain identifying User-Agent, no browser spoofing), one request every 2 seconds, resumable (existing
files are skipped). A 403/412/429 or any 5xx stops the run at once (no retry); a network timeout is retried once after
30 s, then stops. Nothing dated after 2023-12-31 is requested.
Run (system python, background): python scripts/fetch_shfe_daily.py
"""
from __future__ import annotations

import datetime as dt
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "shfe_daily"
UA = "Backtest-Framework research script (python urllib; research-readonly)"
KX = "https://www.shfe.com.cn/data/tradedata/future/dailydata/kx{d}.dat"
ARG = "https://www.shfe.com.cn/data/busiparamdata/future/ContractDailyTradeArgument{d}.dat"
FIRST, LAST = dt.date(2016, 1, 1), dt.date(2023, 12, 31)
PAUSE = 2.0
TARGETS = ("cu", "au", "ag", "al", "zn", "ni")
MOVE, MIN_VOL = 0.035, 100


def get(url: str) -> bytes | None:
    """Bytes, or None on 404. Stops the run on a refusal or a server error."""
    for attempt in (1, 2):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise SystemExit(f"stopped: HTTP {e.code} on {url} (refusal or server error; no retry, by rule)")
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            if attempt == 2:
                raise SystemExit(f"stopped: {e} on {url} after one retry")
            time.sleep(30)
    return None


def candidates(path: Path) -> bool:
    rows = json.loads(path.read_bytes().decode("utf-8")).get("o_curinstrument", [])
    for r in rows:
        pid = str(r.get("PRODUCTID", "")).strip().split("_")[0]
        if pid not in TARGETS or not str(r.get("DELIVERYMONTH", "")).strip().isdigit():
            continue
        try:
            pre, close, vol = float(r["PRESETTLEMENTPRICE"]), float(r["CLOSEPRICE"]), float(r["VOLUME"])
        except (KeyError, TypeError, ValueError):
            continue
        if pre > 0 and vol >= MIN_VOL and abs(close - pre) / pre >= MOVE:
            return True
    return False


def main() -> int:
    (RAW / "kx").mkdir(parents=True, exist_ok=True)
    (RAW / "arg").mkdir(parents=True, exist_ok=True)
    nontrading = RAW / "nontrading_days.txt"
    seen_nt = set(nontrading.read_text(encoding="utf-8").split()) if nontrading.exists() else set()
    d, n_new, n_nt = FIRST, 0, 0
    while d <= LAST:
        tag = d.strftime("%Y%m%d")
        out = RAW / "kx" / f"kx{tag}.dat"
        if d.weekday() < 5 and not out.exists() and tag not in seen_nt:
            body = get(KX.format(d=tag))
            if body is None:
                seen_nt.add(tag)
                with open(nontrading, "a", encoding="utf-8") as fh:
                    fh.write(tag + "\n")
                n_nt += 1
            else:
                out.write_bytes(body)
                n_new += 1
            time.sleep(PAUSE)
            if (n_new + n_nt) % 100 == 0:
                print(f"{tag}: {n_new} quote files, {n_nt} non-trading days so far", flush=True)
        d += dt.timedelta(days=1)
    print(f"quotes done: {len(list((RAW / 'kx').glob('kx*.dat')))} files; {len(seen_nt)} non-trading weekdays", flush=True)
    cands = [p for p in sorted((RAW / "kx").glob("kx*.dat")) if candidates(p)]
    print(f"candidate big-move days: {len(cands)}", flush=True)
    for p in cands:
        tag = p.stem[2:]
        out = RAW / "arg" / f"ContractDailyTradeArgument{tag}.dat"
        if out.exists():
            continue
        body = get(ARG.format(d=tag))
        if body is not None:
            out.write_bytes(body)
        time.sleep(PAUSE)
    print(f"limit files: {len(list((RAW / 'arg').glob('*.dat')))}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
