"""Stage A's calendar flags, per NYMEX business day for CL and NG, 2017-05-22 → 2025-02-28 (settlement ledger A8, H1a's
controls; deposit §3.5).

It builds flags and computes no statistic. Every rule is one that item 1 proved or documented; the source is named
per flag:
  * `bd`, `bd_in_month`: business days are the root's settlement days minus holiday republications, plus the two
    EIA-filled 2020 holes (`check_uscf_months_and_rolls.settlements`, the Gate 0b calendar).
  * `index_roll_close`: the funds' index moves weight at this session's close.
      - NG, the BCOM Natural Gas subindex: BD5–9 closes (Gate 0b NG, S0).
      - CL, era A (to 2020-09-16), the WTI subindex: BD5–9 closes.
      - CL, era B (from 2020-09-17), the Balanced WTI index: BD2–3 closes (Bloomberg's BCBCLI methodology;
        Gate 0b CL).
  * `index_annual_roll`: CL era B, the March and September BD2–3 closes, when the June and December components
    roll too.
  * `index_reset`: CL era B, the BD1 close in March and September.
  * `cl_transition`: 2020-04-01 → 2020-09-16, excluded for CL under A1.
  * `fund_roll`: UNG (on NG) and USO (on CL) trade at this session's close.
      - From 2020: USCF's official roll calendar (`data/raw/uscf/uscf-rolldates-commodities-YYYY.csv`), every
        business day from Roll Begin to Roll End inclusive.
      - Before 2020: the documented rule, D0 → D0+3 with D0 = E − 14 calendar days. It is proven for both funds
        (`ledger_ung_monthly_rolls_check.json`, `ledger_uso_monthly_rolls_check.json`).
  * `expiry`: the near contract's last trading day (the D526/Gate 0b rules in `check_uscf_months_and_rolls`).
  * `ng_spot_last3`: NG's last three trading days of the spot month, whose settlement follows its own procedure
    (`data/settlement_windows.csv`).
  * `eia_report`: an EIA Weekly Petroleum Status Report (CL) or Natural Gas Storage Report (NG) was released that
    ET date (`data/calendar/events.csv`).

Reads go through `load_panel(reserved_from="2025-03-01")` (A6). Output: `data/ledger_calendar_flags.csv`
(tracked, small). `--check` rebuilds and compares byte for byte.

    uv run python scripts/build_ledger_calendar.py [--check]
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_calendar_flags.csv"
EVENTS = REPO / "data" / "calendar" / "events.csv"
ROLLCAL = REPO / "data" / "raw" / "uscf"
CUT, FIRST, LAST = "2025-03-01", "2017-05-22", "2025-02-28"
SWITCH, TRANSITION = "2020-09-17", ("2020-04-01", "2020-09-16")
FUND_OF = {"NG": "UNG", "CL": "USO"}
EIA_OF = {"NG": "EIA_NGSR", "CL": "EIA_WPSR"}


class CalendarError(RuntimeError):
    pass


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


U = _load("check_uscf_months_and_rolls")
U.G.RESERVED_FROM = CUT  # A6: the Gate 0b loaders read it at call time
# gate_0b_cl_nav imports its OWN copy of gate_0b_ng_nav, and CL's loader reads that copy's cut. Setting only U.G
# left CL silently at the 2024-01-01 cut on the first run (1,665 CL days against 1,957 NG).
U.GCL.G.RESERVED_FROM = CUT


def official_roll_days(fund: str, bdays: list[str]) -> set[str]:
    out: set[str] = set()
    for y in range(2020, int(LAST[:4]) + 1):
        with (ROLLCAL / f"uscf-rolldates-commodities-{y}.csv").open(encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) >= 3 and r[0] == fund:
                    a, b = U._d(r[1]), U._d(r[2])
                    out.update(d for d in bdays if a <= d <= b)
    return out


def eia_days(event: str) -> set[str]:
    with EVENTS.open(encoding="utf-8", newline="") as fh:
        return {r["datetime_et"][:10] for r in csv.DictReader(fh) if r["event"] == event}


def build() -> str:
    rows = ["root,date,bd,bd_in_month,index_roll_close,index_annual_roll,index_reset,cl_transition,fund_roll,"
            "expiry,ng_spot_last3,eia_report"]
    for root in ("CL", "NG"):
        st = U.settlements(root)
        bdays = sorted(st)
        if any(d >= CUT for d in bdays):
            raise CalendarError(f"{root}: a settlement dated on or after {CUT} is in memory")
        if bdays[-1] < "2025-02-28":
            raise CalendarError(f"{root}: business days end {bdays[-1]}, short of the in-sample end: a stale cut")
        U._BDAYS = bdays
        rolls = U.roll_calendar(root, bdays)
        expiries = {r["E"] for r in rolls}
        last3 = set()
        if root == "NG":
            for r in rolls:
                i = bdays.index(r["E"])
                last3.update(bdays[max(0, i - 2): i + 1])
        pre2020 = set()
        for r in rolls:
            if r["D0"] < "2020-01-01":
                pre2020.update(bdays[r["i0"]: r["i0"] + 4])
        fund_roll = pre2020 | official_roll_days(FUND_OF[root], bdays)
        eia = eia_days(EIA_OF[root])
        count: dict[str, int] = {}
        per_month: dict[str, int] = {}
        for d in bdays:
            per_month[d[:7]] = per_month.get(d[:7], 0) + 1
        for d in bdays:
            count[d[:7]] = count.get(d[:7], 0) + 1
            if not (FIRST <= d <= LAST):
                continue
            k = count[d[:7]]
            era_b = root == "CL" and d >= SWITCH
            roll = (2 <= k <= 3) if era_b else (5 <= k <= 9)
            annual = era_b and d[5:7] in ("03", "09") and 2 <= k <= 3
            reset = era_b and d[5:7] in ("03", "09") and k == 1
            trans = root == "CL" and TRANSITION[0] <= d <= TRANSITION[1]
            vals = [roll, annual, reset, trans, d in fund_roll, d in expiries, d in last3, d in eia]
            rows.append(f"{root},{d},{k},{per_month[d[:7]]}," + ",".join("1" if v else "0" for v in vals))
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = build()
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise CalendarError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    rd = list(csv.DictReader(io.StringIO(text)))
    for root in ("CL", "NG"):
        r = [x for x in rd if x["root"] == root]
        print(root, len(r), "days;", {c: sum(int(x[c]) for x in r) for c in
                                      ("index_roll_close", "index_annual_roll", "index_reset", "cl_transition",
                                       "fund_roll", "expiry", "ng_spot_last3", "eia_report")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
