"""Fetch the USD/CNY central parity (the 09:15 Beijing fix) and the Fed H.10 noon New York USD/CNY rate (FRED DEXCHUS),
2015-06-01 -> 2023-12-31, into data/raw/cny_fix/ (gitignored); build_cny_fix.py turns them into fixtures.

Approved by the principal 2026-10-02 ("Yes, download both"). Honest client (a plain identifying User-Agent, no browser
spoofing), one request at a time with a pause, and NO retry on any refusal: a 403/412/429 stops the run. Nothing dated
after 2023-12-31 is requested (the held slice and the vault stay unread).

Sources:
  SAFE   https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do  (State Administration of Foreign Exchange; the central
         parity table, CNY per 100 units, data from CFETS; one query per calendar year, the page's 366-day cap)
  FRED   https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS
CFETS's own history endpoint (chinamoney.com.cn ... CcprHisNew) answered this script with HTTP 403 on 2026-10-02; by rule
it was not retried and no other client was tried. SAFE publishes the same series.
Run (system python): python scripts/fetch_cny_fix.py
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "cny_fix"
UA = "Backtest-Framework research script (python urllib; one-off historical fetch)"
SAFE = "https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS&cosd=2015-06-01&coed=2023-12-31"
PAUSE = 5.0


def fetch(url: str, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"refused: HTTP {e.code} on {url} (no retry, by rule)")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    fred = RAW / "fred_dexchus_2015_2023.csv"
    if not fred.exists():
        fred.write_bytes(fetch(FRED))
        print(f"FRED DEXCHUS: {len(fred.read_bytes())} bytes", flush=True)
        time.sleep(PAUSE)
    for year in range(2015, 2024):
        out = RAW / f"safe_central_parity_{year}.html"
        if out.exists():
            continue
        start = "2015-06-01" if year == 2015 else f"{year}-01-01"
        form = urllib.parse.urlencode({"startDate": start, "endDate": f"{year}-12-31", "queryYN": "true"}).encode()
        body = fetch(SAFE, data=form)
        out.write_bytes(body)
        print(f"SAFE {year}: {len(body)} bytes", flush=True)
        time.sleep(PAUSE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
