"""Build data/fixtures/gld_holdings_daily.csv from SPDR's official GLD historical archive (D773).

Source: https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en (linked from
spdrgoldshares.com/usa/gld/ as the historical-archive download; served as US_GLD_Archive_EN.xlsx), fetched once on
2026-10-02 with an honest client on the principal's word ("Yes, download"). The older address
spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv now serves a 120-page PDF, kept as
data/raw/gld/served_instead_of_csv.pdf and not used.

Rows dated on or after 2024-01-01 are dropped as the FIRST step, before any value is parsed or printed; the fixture
holds 2015-06-01 -> 2023-12-29.
Run (system python, needs openpyxl): python scripts/build_gld_holdings.py
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "gld" / "US_GLD_Archive_EN.xlsx"
OUT = REPO / "data" / "fixtures" / "gld_holdings_daily.csv"
META = REPO / "data" / "fixtures" / "gld_holdings_daily.meta.json"
FIRST, SEAL = dt.date(2015, 6, 1), dt.date(2024, 1, 1)
SHEET = "US GLD Historical Archive"
COLS = {"Date": "date", "Closing Price": "close_usd", "Ounces of Gold per Share": "oz_per_share",
        "NAV/Share at 10:30am NYT": "nav_per_share_1030",
        "Premium/Discount of GLD Mid Point vs Indicative Value of GLD at 4:15pm NYT": "premium_pct",
        "Daily Share Volume": "share_volume", "Total Ounces of Gold in the Trust": "total_oz", "Tonnes of Gold": "tonnes",
        "Total Net Asset Value in the Trust": "nav_total_usd"}


class BuildError(RuntimeError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise BuildError(msg)


def build() -> int:
    wb = openpyxl.load_workbook(RAW, read_only=True, data_only=True)
    need(SHEET in wb.sheetnames, f"sheet {SHEET!r} not found: {wb.sheetnames}")
    rows = list(wb[SHEET].iter_rows(values_only=True))
    head = [str(c).strip() if c is not None else "" for c in rows[0]]
    idx = {}
    for name, key in COLS.items():
        hit = [i for i, h in enumerate(head) if h.startswith(name[:28])]
        need(len(hit) == 1, f"column {name!r}: {len(hit)} matches in {head}")
        idx[key] = hit[0]
    kept, n_late, n_early = [], 0, 0
    for r in rows[1:]:
        raw_d = r[idx["date"]]
        if raw_d is None or str(raw_d).strip() == "":
            continue
        d = raw_d.date() if isinstance(raw_d, dt.datetime) else datetime.strptime(str(raw_d).strip(), "%d-%b-%Y").date()
        if d >= SEAL:                      # dropped first, unread
            n_late += 1
            continue
        if d < FIRST:
            n_early += 1
            continue
        rec, notes = {"date": d.isoformat()}, set()
        for k, i in idx.items():
            if k != "date":
                v = r[i]
                try:
                    rec[k] = float(str(v).replace(",", "").replace("%", "")) if v not in (None, "") else ""
                except ValueError:
                    rec[k] = ""
                    notes.add(str(v).strip())
        rec["note"] = ";".join(sorted(notes))
        kept.append(rec)
    kept.sort(key=lambda x: x["date"])
    need(len({x["date"] for x in kept}) == len(kept), "duplicate dates")
    need(kept[0]["date"] <= "2015-06-02" and kept[-1]["date"] >= "2023-12-28", f"coverage {kept[0]['date']} -> {kept[-1]['date']}")
    ton = [float(x["tonnes"]) for x in kept if x["tonnes"] != ""]
    need(min(ton) > 500 and max(ton) < 1500, f"tonnes out of the 500-1500 band: {min(ton)}..{max(ton)}")
    out = io.StringIO(newline="")
    w = csv.DictWriter(out, fieldnames=["date"] + [k for k in idx if k != "date"] + ["note"], lineterminator="\n")
    w.writeheader()
    w.writerows(kept)
    OUT.write_text(out.getvalue(), encoding="utf-8", newline="\n")
    meta = {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "builder": "scripts/build_gld_holdings.py",
            "source": "https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en (US_GLD_Archive_EN.xlsx)",
            "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(), "rows": len(kept), "first": kept[0]["date"],
            "last": kept[-1]["date"], "dropped_2024_or_later_unread": n_late, "dropped_before_2015_06": n_early,
            "columns": {k: head[i] for k, i in idx.items()},
            "what_bites": ["tonnes / total_oz are the trust's holdings as of each date; the daily change is net creations "
                           "minus redemptions (and the small daily sponsor-fee accrual on ounces per share)",
                           "the publication time of a date's holdings is not stated in the file; a study must lag it a full "
                           "day before trading on it", "blank cells are holidays or missing values"]}
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(kept)} rows {kept[0]['date']} -> {kept[-1]['date']}; dropped {n_late} rows dated 2024+ unread, "
          f"{n_early} before 2015-06; tonnes {min(ton):.1f}..{max(ton):.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
