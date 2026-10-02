"""Build the yuan fixtures from data/raw/cny_fix/ (fetched by scripts/fetch_cny_fix.py):

  data/fixtures/cny_central_parity.csv   the daily central parity (the 09:15 Beijing fix) from SAFE's table, 2015-06-01 ->
                                         2023-12-31: date, usdcny_fix (CNY per USD), and every other currency column as
                                         SAFE quotes it (header kept verbatim in the meta; most are CNY per 100 units,
                                         a few Asian/emerging currencies are units per 100 CNY)
  data/fixtures/fred_dexchus.csv         the Fed H.10 noon New York USD/CNY rate (FRED DEXCHUS): date, usdcny_noon_ny;
                                         holidays (FRED '.' or blank) dropped

Run (system python): python scripts/build_cny_fix.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "cny_fix"
OUT_FIX = REPO / "data" / "fixtures" / "cny_central_parity.csv"
OUT_FRED = REPO / "data" / "fixtures" / "fred_dexchus.csv"
META = REPO / "data" / "fixtures" / "cny_fix.meta.json"
LAST = "2023-12-31"
CODES = {"美元": "USD", "欧元": "EUR", "日元": "JPY", "港元": "HKD", "英镑": "GBP", "澳元": "AUD", "新西兰元": "NZD",
         "新加坡元": "SGD", "瑞士法郎": "CHF", "加元": "CAD", "加拿大元": "CAD", "林吉特": "MYR", "卢布": "RUB", "兰特": "ZAR",
         "韩元": "KRW", "迪拉姆": "AED", "里亚尔": "SAR", "福林": "HUF", "兹罗提": "PLN", "丹麦克朗": "DKK", "瑞典克朗": "SEK",
         "挪威克朗": "NOK", "里拉": "TRY", "比索": "MXN", "泰铢": "THB", "澳门元": "MOP"}


class BuildError(RuntimeError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise BuildError(msg)


def cells(row: str) -> list[str]:
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<!--.*?-->|<[^>]+>", "", c, flags=re.S))).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)]


def parse_safe(path: Path) -> tuple[list[str], list[list[str]]]:
    t = path.read_bytes().decode("utf-8")
    m = re.search(r'<table[^>]*id="InfoTable"[^>]*>(.*?)</table>', t, flags=re.S)
    need(m is not None, f"{path.name}: no InfoTable")
    rows = [cells(r) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), flags=re.S)]
    head = rows[0]
    need(head[0] == "日期" and head[1] == "美元", f"{path.name}: unexpected header {head[:3]}")
    body = [r for r in rows[1:] if r and re.match(r"^\d{4}-\d\d-\d\d$", r[0])]
    need(all(len(r) == len(head) for r in body), f"{path.name}: ragged rows")
    return head, body


def build() -> int:
    head0, allrows = None, {}
    files = sorted(RAW.glob("safe_central_parity_*.html"))
    need(len(files) == 9, f"expected 9 yearly SAFE files, found {len(files)}")
    for f in files:
        head, body = parse_safe(f)
        if head0 is None:
            head0 = head
        need(head == head0, f"{f.name}: header differs from the first year's")
        for r in body:
            need(r[0] not in allrows or allrows[r[0]] == r, f"duplicate date with different values: {r[0]}")
            allrows[r[0]] = r
    dates = sorted(allrows)
    need(dates[0] == "2015-06-01" and dates[-1] <= LAST, f"coverage {dates[0]} -> {dates[-1]}")
    need(allrows["2015-06-01"][1] == "612.07", "check: SAFE USD on 2015-06-01 should be 612.07 (CFETS 6.1207)")
    codes = [CODES.get(h, "X" + str(i)) for i, h in enumerate(head0[1:], 1)]
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["date", "usdcny_fix"] + [f"safe_{c}" for c in codes])
    for d in dates:
        r = allrows[d]
        usd = float(r[1]) / 100.0
        need(5.5 < usd < 7.5, f"{d}: USD/CNY fix {usd} out of range")
        w.writerow([d, f"{usd:.4f}"] + r[1:])
    OUT_FIX.write_text(out.getvalue(), encoding="utf-8", newline="\n")
    fred_raw = (RAW / "fred_dexchus_2015_2023.csv").read_text(encoding="utf-8").splitlines()
    need(fred_raw[0].strip() == "observation_date,DEXCHUS", f"FRED header {fred_raw[0]!r}")
    fr = [ln.split(",") for ln in fred_raw[1:] if ln.strip()]
    kept = [(d, v) for d, v in fr if v not in ("", ".")]
    need(all(d <= LAST for d, _ in kept), "FRED row after 2023-12-31")
    need(all(5.5 < float(v) < 7.5 for _, v in kept), "FRED value out of range")
    OUT_FRED.write_text("date,usdcny_noon_ny\n" + "".join(f"{d},{v}\n" for d, v in kept), encoding="utf-8", newline="\n")
    per_year = {y: sum(1 for d in dates if d[:4] == y) for y in sorted({d[:4] for d in dates})}
    meta = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "builder": "scripts/build_cny_fix.py",
        "fetcher": "scripts/fetch_cny_fix.py (principal-approved 2026-10-02; honest client; CFETS's own endpoint refused with 403 "
                   "and was not retried, SAFE publishes the same series)",
        "central_parity": {"source": "SAFE https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do (data from CFETS)",
                           "rows": len(dates), "first": dates[0], "last": dates[-1], "rows_per_year": per_year,
                           "header_verbatim": head0, "codes": codes,
                           "quote_convention": "SAFE quotes most currencies as CNY per 100 units (USD 612.07 = 6.1207); "
                                               "usdcny_fix = USD/100. Check any other column's convention before use.",
                           "check": "2015-06-01 USD 612.07 equals the CFETS history endpoint's 6.1207 (scouted)",
                           "release_time": "09:15 Beijing (20:15 ET in EDT, 21:15 ET in EST) on CFETS business days"},
        "fred_dexchus": {"source": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS", "rows": len(kept),
                         "dropped_holidays": len(fr) - len(kept), "first": kept[0][0], "last": kept[-1][0],
                         "what_it_is": "Federal Reserve H.10 noon buying rate in New York (about 00:00-01:00 Beijing the next "
                                       "calendar day); onshore vs offshore basis not stated by the source"},
        "raw_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(RAW.iterdir())},
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"central parity: {len(dates)} days {dates[0]} -> {dates[-1]} {per_year}; FRED: {len(kept)} days "
          f"({len(fr) - len(kept)} holidays dropped); codes {codes}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
