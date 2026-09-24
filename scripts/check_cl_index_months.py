"""Check that UCO and SCO held exactly their benchmark's contract months (AITODO 1d).

SPEC -- written 2026-09-24 before any held month was compared, and frozen from then on.

THE BENCHMARKS, from ProShares Trust II's 10-K for 2020 (accession 0001193125-21-049128, recorded by
D620): "Prior to September 17, 2020, the benchmark ... was the Bloomberg WTI Crude Oil Subindex";
from that date it is the Bloomberg Commodity Balanced WTI Crude Oil Index (BCBCLI).

RULE A, through 2020-09-16: the WTI Crude Oil Subindex. BCOM Table 9's WTI row is Mar Mar May May
Jul Jul Sep Sep Nov Nov Jan Jan, the same as natural gas. After Business Day 10 of month m, the
index holds month m+1's designated contract. One month is held.

RULE B, from 2020-09-17: three equal schedules, quoted from the same 10-K. After the roll period in
month m (every quarter-end, and the daily tables, fall after BD10), the three are:
  * monthly: "rolls from the current futures contract ('Lead' ... expires one month out) into the
    following month's contract ('Next' ... expires two months out)". Having rolled in month m, it
    holds delivery month m+3.
  * June: "always designated to be in a June contract ... rolled in March". After March of year Y
    it holds June of Y+1.
  * December: "always designated to be in a December contract ... rolled in September". Before
    September of year Y it holds December of Y; after, December of Y+1.
  So exactly three distinct months are held.

TRANSITION, 2020-04-01 → 2020-09-16: the benchmark was still rule A. The 2020-06-30 schedules
already hold three months, so the fund departed from its benchmark before the switch. Those
quarter-ends are a class of their own. They are reported, never counted as a match, and never
counted as a rule failure.

EVIDENCE (holdings only; no price is read):
  * every UCO and SCO quarter-end in D620's `fund_holdings_quarterly`, 2017-03-31 → the latest,
    first publication only;
  * D619's recorded fund pages (2026-09-18);
  * ProShares' all-funds file for 2026-09-23.

CONTROLS THAT MUST FIRE: rule A shifted by one month, and rule B with the monthly schedule one
month early, must each fail to match every day of their own era.

    uv run python scripts/check_cl_index_months.py            # write the JSON
    uv run python scripts/check_cl_index_months.py --check    # rebuild and compare byte for byte
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
HOLDINGS = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
REC = REPO / "data" / "raw" / "recorder" / "proshares_holdings"
DAILY_0923 = REPO / "data" / "raw" / "proshares_daily_holdings" / "2026-09-23.csv"
OUT = REPO / "data" / "ledger_cl_held_months_check.json"
FUNDS = ("UCO", "SCO")
FIRST = "2017-03-31"
SWITCH = "2020-09-17"
TRANSITION = ("2020-04-01", "2020-09-16")
MON = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}
DESIGNATED = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7, 7: 9, 8: 9, 9: 11, 10: 11, 11: 13, 12: 13}


class MonthsError(RuntimeError):
    pass


def _ym(y: int, m: int) -> str:
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def rule_a(day: str, shift: int = 0) -> list[str]:
    y, m = int(day[:4]), int(day[5:7])
    nm_y, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    c = DESIGNATED[(nm - 1 + shift) % 12 + 1]
    return [_ym(nm_y, c)]


def rule_b(day: str, monthly_offset: int = 3) -> list[str]:
    y, m = int(day[:4]), int(day[5:7])
    monthly = _ym(y, m + monthly_offset)
    june = _ym(y + 1, 6) if m >= 3 else _ym(y, 6)
    dec = _ym(y + 1, 12) if m >= 9 else _ym(y, 12)
    return sorted({monthly, june, dec})


def _after_bd10(day: str) -> bool:
    d = pd.Timestamp(day)
    return len(pd.bdate_range(d.replace(day=1), d)) > 12


def evidence() -> list[dict[str, Any]]:
    h = pd.read_csv(HOLDINGS, encoding="utf-8", dtype=str)
    f = h[h.fund.isin(FUNDS) & (h.period_end >= FIRST)].sort_values(["period_end", "filed_date"])
    rows: list[dict[str, Any]] = []
    for (fund, pe), g in f.groupby(["fund", "period_end"]):
        first = g[g["source_accession"] == g["source_accession"].iloc[0]]
        fut = first[first["kind"] == "futures"]
        if fut.empty:
            continue
        rows.append({"fund": fund, "day": pe, "source": f"D620 quarter-end {first['source_accession'].iloc[0]}",
                     "held_months": sorted(set(fut["contract_month"].dropna()))})
    for fund in FUNDS:
        pages = sorted(REC.glob(f"{fund}__*.html")) if REC.exists() else []
        if pages:
            raw = pages[-1].read_text(encoding="utf-8", errors="replace")
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).upper()
            ms = sorted({f"20{yy}-{MON[mon]:02d}" for mon, yy in re.findall(r"WTI CRUDE FUTURE ([A-Z]{3})(\d{2})", txt)})
            asof = re.search(r"HOLDINGS AS OF (\d{1,2})/(\d{1,2})/(\d{4})", txt)
            if asof and ms:
                day = f"{asof.group(3)}-{int(asof.group(1)):02d}-{int(asof.group(2)):02d}"
                rows.append({"fund": fund, "day": day, "source": f"D619 recorded page {pages[-1].name}", "held_months": ms})
    if DAILY_0923.exists():
        with DAILY_0923.open(encoding="utf-8", newline="") as fh:
            lines = list(csv.reader(fh))
        for fund in FUNDS:
            ms = sorted({f"20{r[4].split()[-1][3:]}-{MON[r[4].split()[-1][:3].upper()]:02d}"
                         for r in lines[4:] if r and r[0] == fund and r[4].upper().startswith("WTI CRUDE FUTURE")})
            if ms:
                rows.append({"fund": fund, "day": "2026-09-23", "source": "ProShares all-funds holdings file (principal, 2026-09-24)",
                             "held_months": ms})
    return sorted(rows, key=lambda r: (r["fund"], r["day"]))


def predicted(day: str, a_shift: int = 0, b_offset: int = 3) -> list[str]:
    return rule_a(day, a_shift) if day < SWITCH else rule_b(day, b_offset)


def build() -> dict[str, Any]:
    rows = evidence()
    if len(rows) < 30:
        raise MonthsError(f"only {len(rows)} evidence days")
    for r in rows:
        if not _after_bd10(r["day"]):
            raise MonthsError(f"{r['fund']} {r['day']} may fall inside a roll window")
        r["era"] = "transition" if TRANSITION[0] <= r["day"] <= TRANSITION[1] else ("A" if r["day"] < SWITCH else "B")
        r["predicted"] = predicted(r["day"])
        r["match"] = r["held_months"] == r["predicted"]
    scored = [r for r in rows if r["era"] != "transition"]
    by_era = {e: {"days": sum(r["era"] == e for r in rows), "matched": sum(r["match"] for r in rows if r["era"] == e)}
              for e in ("A", "B", "transition")}
    ctl_a = sum(r["held_months"] == rule_a(r["day"], 1) for r in scored if r["era"] == "A")
    ctl_b = sum(r["held_months"] == rule_b(r["day"], 2) for r in scored if r["era"] == "B")
    if ctl_a == by_era["A"]["days"] or ctl_b == by_era["B"]["days"]:
        raise MonthsError(f"control failed: shifted rules match every day (A {ctl_a}, B {ctl_b})")
    return {
        "spec": "settlement-ledger AITODO 1d: UCO/SCO held months vs the WTI Subindex (to 2020-09-16) and the "
                "Balanced WTI Index (from 2020-09-17); see the script docstring",
        "switch": SWITCH, "transition": list(TRANSITION),
        "by_era": by_era,
        "mismatched": [r for r in scored if not r["match"]],
        "transition_rows": [r for r in rows if r["era"] == "transition"],
        "controls": {"rule_a_shifted_one_month_matches": ctl_a, "rule_b_monthly_one_early_matches": ctl_b},
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
    print(f"by era: {doc['by_era']}")
    print(f"controls: {doc['controls']}")
    for r in doc["mismatched"]:
        print("  MISMATCH", r["fund"], r["day"], r["held_months"], "predicted", r["predicted"], r["source"])
    for r in doc["transition_rows"]:
        print("  TRANSITION", r["fund"], r["day"], r["held_months"], "rule A says", r["predicted"])
    return 0 if not doc["mismatched"] else 1


if __name__ == "__main__":
    sys.exit(main())
