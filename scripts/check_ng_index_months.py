"""Check that BOIL and KOLD held exactly the Bloomberg Natural Gas Subindex's contract months.

The settlement ledger maps each fund's rebalance flow to the contract months it holds (deposit §3.1,
"Flow is mapped to the contract months actually held"). No free daily holdings history exists
(AITODO item 1), so the held months must come from the index the funds track, and that is only
acceptable if the funds provably held exactly those months. This script is that proof, on every day
the funds' own published holdings can be read.

THE RULE, from the Bloomberg Commodity Index Methodology (Table 9, "Bloomberg Commodity Index
Contract Calendar", and §2.8), https://assets.bbhub.io/professional/sites/10/BCOM-Methodology.pdf:

  * natural gas's designated contract for each calendar month is
        Jan Mar · Feb Mar · Mar May · Apr May · May Jul · Jun Jul ·
        Jul Sep · Aug Sep · Sep Nov · Oct Nov · Nov Jan(+1) · Dec Jan(+1);
  * in month m the index holds month m's designated contract (the Lead Future) until the Roll
    Period, shifts 20% a day into month m+1's (the Next Future) over Business Days 6–10, and holds
    that for the rest of the month.

So on any day after Business Day 10 — every quarter-end, and both daily tables below — the index
holds exactly month m+1's designated contract. The prediction is written before anything is read.

EVIDENCE, the funds' own published holdings:
  * every BOIL and KOLD quarter-end in `data/fixtures/fund_holdings_quarterly.csv.gz` (D620,
    parsed from the audited schedules of investments), 2017-Q1 → the latest;
  * ProShares' daily holdings for 2026-09-18 (D619's recorded page) and 2026-09-23 (the
    all-funds file the principal supplied, `data/raw/proshares_daily_holdings/2026-09-23.csv`).

CONTROL that must fire: the same comparison against the table shifted by one month must FAIL.

    uv run python scripts/check_ng_index_months.py            # write the JSON
    uv run python scripts/check_ng_index_months.py --check    # rebuild and compare byte for byte
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
HOLDINGS = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
DAILY_0923 = REPO / "data" / "raw" / "proshares_daily_holdings" / "2026-09-23.csv"
OUT = REPO / "data" / "ledger_ng_held_months_check.json"
FUNDS = ("BOIL", "KOLD")
FIRST = "2017-03-31"
MON = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
       "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}

#: BCOM Table 9, natural gas: calendar month -> designated contract month (13 = January next year).
DESIGNATED = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7, 7: 9, 8: 9, 9: 11, 10: 11, 11: 13, 12: 13}


class MonthsError(RuntimeError):
    pass


def held_after_roll(day: str, table: dict[int, int] = DESIGNATED) -> str:
    """The contract (YYYY-MM) the index holds on `day`, which must fall after Business Day 10."""
    y, m = int(day[:4]), int(day[5:7])
    nm_y, nm = (y + 1, 1) if m == 12 else (y, m + 1)  # month m+1
    c = table[nm]
    cy, cm = (nm_y + 1, c - 12) if c > 12 else (nm_y, c)
    return f"{cy:04d}-{cm:02d}"


def _after_bd10(day: str) -> bool:
    d = pd.Timestamp(day)
    bdays = pd.bdate_range(d.replace(day=1), d)  # weekdays only: a lower bound on BD count is enough
    return len(bdays) > 12  # > 12 weekdays covers BD10 even with two holidays in the month


def evidence() -> list[dict[str, object]]:
    h = pd.read_csv(HOLDINGS, encoding="utf-8", dtype=str)
    f = h[h.fund.isin(FUNDS) & (h.kind == "futures") & (h.period_end >= FIRST)]
    rows: list[dict[str, object]] = []
    for (fund, pe), g in f.groupby(["fund", "period_end"]):
        months = sorted(set(g.contract_month.dropna()))
        rows.append({"fund": fund, "day": pe, "source": "D620 quarter-end (SEC schedule of investments)",
                     "held_months": months})
    # 2026-09-18: D619's recorded fund pages, via the D620 fixture's live-page gate would be circular;
    # read the recorded HTML table directly.
    rec_dir = REPO / "data" / "raw" / "recorder" / "proshares_holdings"
    for fund in FUNDS:
        pages = sorted(rec_dir.glob(f"{fund}__*.html")) if rec_dir.exists() else []
        if pages:
            import re
            raw = pages[-1].read_text(encoding="utf-8", errors="replace")
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).upper()  # tags sit between label and date
            ms = sorted({f"20{yy}-{MON[mon]:02d}" for mon, yy in re.findall(r"NATURAL GAS FUTR ([A-Z]{3})(\d{2})", txt)})
            asof = re.search(r"HOLDINGS AS OF (\d{1,2})/(\d{1,2})/(\d{4})", txt)
            if asof and ms:
                day = f"{asof.group(3)}-{int(asof.group(1)):02d}-{int(asof.group(2)):02d}"
                rows.append({"fund": fund, "day": day, "source": f"D619 recorded page {pages[-1].name}", "held_months": ms})
    if DAILY_0923.exists():
        with DAILY_0923.open(encoding="utf-8", newline="") as fh:
            lines = list(csv.reader(fh))
        for fund in FUNDS:
            ms = sorted({f"20{r[4].split()[-1][3:]}-{MON[r[4].split()[-1][:3].upper()]:02d}"
                         for r in lines[4:] if r and r[0] == fund and r[4].upper().startswith("NATURAL GAS FUTR")})
            if ms:
                rows.append({"fund": fund, "day": "2026-09-23", "source": "ProShares all-funds holdings file (principal, 2026-09-24)",
                             "held_months": ms})
    return sorted(rows, key=lambda r: (r["fund"], r["day"]))  # type: ignore[arg-type,return-value]


def compare(rows: list[dict[str, object]], table: dict[int, int]) -> tuple[int, list[dict[str, object]]]:
    bad = []
    for r in rows:
        day = str(r["day"])
        if not _after_bd10(day):
            raise MonthsError(f"{r['fund']} {day} may fall inside a roll window; the rule does not apply")
        want = held_after_roll(day, table)
        if r["held_months"] != [want]:
            bad.append({**r, "predicted": want})
    return len(rows) - len(bad), bad


def build() -> dict[str, object]:
    rows = evidence()
    if len(rows) < 30:
        raise MonthsError(f"only {len(rows)} evidence days found; the D620 fixture should give ~70")
    ok, bad = compare(rows, DESIGNATED)
    shifted = {m: DESIGNATED[m % 12 + 1] for m in DESIGNATED}  # the table moved one month early
    ok_s, _bad_s = compare(rows, shifted)
    if ok_s == len(rows):
        raise MonthsError("control failed: a table shifted by one month also matched every day")
    for r in rows:
        r["predicted"] = held_after_roll(str(r["day"]))
        r["match"] = r["held_months"] == [r["predicted"]]
    return {
        "spec": "settlement-ledger AITODO item 1: BOIL/KOLD held months vs the Bloomberg Natural Gas Subindex calendar",
        "rule_source": "https://assets.bbhub.io/professional/sites/10/BCOM-Methodology.pdf, Table 9 and Section 2.8",
        "designated_ng": {str(k): v for k, v in DESIGNATED.items()},
        "rule": "after Business Day 10 of month m the index holds month m+1's designated contract; 13 = January next year",
        "evidence_days": len(rows),
        "matched": ok,
        "mismatched": bad,
        "control": {"shifted_table_matches": ok_s, "of": len(rows), "must_be_below_all": True},
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise MonthsError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"evidence days {doc['evidence_days']}; matched {doc['matched']}; mismatched {len(doc['mismatched'])}")  # type: ignore[arg-type]
    for b in doc["mismatched"]:  # type: ignore[attr-defined]
        print("  MISMATCH", b)
    c = doc["control"]
    print(f"control: the one-month-shifted table matches {c['shifted_table_matches']} of {c['of']} (must be below all)")  # type: ignore[index]
    return 0 if not doc["mismatched"] else 1


if __name__ == "__main__":
    sys.exit(main())
