"""LME official cash-settlement and 3-month prices for aluminium, zinc, nickel and lead, from Westmetall's free
yearly tables (the principal, 2026-09-27: "Yes to both"). They stand in for BCOM's LME designated contracts in the
index-reweight drift (amendment IR-A4): LME is 9.4-10.7% of BCOM, and Sierra Chart does not carry it.

One page per metal and year, 2015-2026: 48 GETs, one a second, with a plain browser user agent. The pages are cached
in data/raw/index_reweight/westmetall/ and never re-fetched. The parse writes
data/index_reweight/lme_westmetall_daily.csv.gz (date, metal, cash_usd_t, three_month_usd_t). Rows dated
2025-03-01 or later are written and never read before the joint vault run (A10).

    python scripts/fetch_westmetall_lme.py --fetch --parse
"""
from __future__ import annotations

import argparse
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "index_reweight" / "westmetall"
OUT = REPO / "data" / "index_reweight" / "lme_westmetall_daily.csv.gz"
URL = "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_{m}_cash&year={y}"
METALS = {"Al": "aluminium", "Zn": "zinc", "Ni": "nickel", "Pb": "lead"}
# D636 s.1 (the principal, 2026-09-27): LME copper for GSCI's weights, written to its own file so the BCOM file
# Gate R0 hashed stays byte-identical
COPPER = {"Cu": "copper"}
OUT_CU = REPO / "data" / "index_reweight" / "lme_copper_westmetall_daily.csv.gz"
YEARS = range(2015, 2027)
UA = "Mozilla/5.0 (research data fetch)"
ROW = re.compile(r"<tr>\s*<td >(\d\d\. \w+ \d{4})</td>\s*<td >([\d,.\-]*)</td>\s*<td >([\d,.\-]*)</td>")


def fetch(metals: dict[str, str] = METALS) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for m in metals:
        for y in YEARS:
            p = RAW / f"LME_{m}_{y}.html"
            if p.exists() and p.stat().st_size > 1000:
                continue
            req = urllib.request.Request(URL.format(m=m, y=y), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status != 200:
                    raise RuntimeError(f"{m} {y}: HTTP {r.status}")
                p.write_bytes(r.read())
            time.sleep(1.0)
    print(f"cached {len(list(RAW.glob('*.html')))} pages")


def num(s: str) -> float:
    s = s.replace(",", "").strip()
    return float(s) if s and s != "-" else float("nan")


def parse(metals: dict[str, str] = METALS, out: Path = OUT) -> pd.DataFrame:
    rows = []
    for m, name in metals.items():
        for y in YEARS:
            t = (RAW / f"LME_{m}_{y}.html").read_text(encoding="utf-8", errors="replace")
            got = ROW.findall(t)
            if not got:
                raise RuntimeError(f"{m} {y}: no rows parsed")
            for d, cash, three in got:
                day = pd.to_datetime(d, format="%d. %B %Y")
                if day.year != y:
                    raise RuntimeError(f"{m} {y}: a row dated {d} is on the wrong year's page")
                rows.append((day.strftime("%Y-%m-%d"), name, num(cash), num(three)))
    df = pd.DataFrame(rows, columns=["date", "metal", "cash_usd_t", "three_month_usd_t"])
    df = df.sort_values(["metal", "date"]).reset_index(drop=True)
    if df.duplicated(["metal", "date"]).any():
        raise RuntimeError("a (metal, date) appears twice")
    df.to_csv(out, index=False, encoding="utf-8", lineterminator="\n",
              compression={"method": "gzip", "mtime": 0})
    for name, g in df.groupby("metal"):
        print(f"  {name}: {len(g)} days {g['date'].iloc[0]} -> {g['date'].iloc[-1]}, "
              f"missing cash {int(g['cash_usd_t'].isna().sum())}, missing 3M {int(g['three_month_usd_t'].isna().sum())}")
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--parse", action="store_true")
    ap.add_argument("--copper", action="store_true", help="LME copper for GSCI (D636 s.1), into its own file")
    a = ap.parse_args()
    metals, out = (COPPER, OUT_CU) if a.copper else (METALS, OUT)
    if a.fetch:
        fetch(metals)
    if a.parse:
        parse(metals, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
