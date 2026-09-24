"""Gate 0b for BOIL and KOLD: rebuild each day's NAV from NG settlements and compare it with the official NAV.

SPEC -- written 2026-09-24 before any replicated NAV was computed, and frozen from then on. Anything
changed after the first run is listed in DEVIATIONS below and copied into the output.

WHY. The settlement ledger needs BOIL's and KOLD's contracts on every day (AITODO item 1). The held
MONTHS are proven (`data/ledger_ng_held_months_check.json`, 80 of 80 days), but every one of those
days is after the roll. Whether the funds trade on the index's roll days is not yet known, and the
fund filings do not say (`data/fund_facts/SOURCES.md` §4: "unknown for BOIL, KOLD, UCO and SCO").
The deposit's own Gate 0b settles it: if the NAV rebuilt under the index's rules matches the
official NAV on roll days as closely as on other days, the funds rolled with the index.

THE GATE (deposit, SETTLEMENT_FLOW_LEDGER_PREREG.md §P3.1 line 191, verbatim):
    "per fund, |iNAV at settlement − official NAV[t]| ≤ 5 bp on ≥ 95% of days."

FUNDS. BOIL L = +2 and KOLD L = −2 (deposit §3.1). ER = 0.95% a year, the management fee
(SOURCES.md §5, quoted from the 10-K). Brokerage commissions are not modelled.

WINDOW. NAV dates 2017-05-22 → 2023-12-29. 2017-05-22 is the first NAV date after the ledger's
sample start (2017-05-21, the GLBX MBO start). 2023-12-29 is the last NAV date before the repo's
2024-01-01 seal. Every panel is read through D609's `load_panel(..., reserved_from="2024-01-01")`,
so no row dated on or after the seal is ever in memory.

THE MODEL (deposit §P3.1 line 184, applied at the settlement):
    iNAV_t = NAV_{t-1} * (1 + L * (I_t / I_{t-1} - 1)) + NAV_{t-1} * D * (y / 360 - ER / 365)
  * D is the number of calendar days between the two NAV dates (fees and interest accrue daily).
  * I is the Bloomberg Natural Gas Subindex (excess return), recomputed from NYMEX NG settlements
    (`fut_settle_strip`). The formula is §2.8 of the BCOM methodology,
    https://assets.bbhub.io/professional/sites/10/BCOM-Methodology.pdf. On business day d of month
    m, with p the previous business day:
        R_d = ((1-b) P_L(d) + b P_N(d)) / ((1-b) P_L(p) + b P_N(p))
    L is month m's designated contract and N is month m+1's (Table 9: Mar Mar May May Jul Jul Sep Sep
    Nov Nov Jan Jan). b depends on the business-day number k of d in its month. Under the index's
    own schedule S0, b = 0 for k ≤ 5, then 0.2, 0.4, 0.6, 0.8 for k = 6..9, then 1 for k ≥ 10.
    Appendix C's Table 13 must be reproduced first; this is a known-answer check that raises.
    I_t / I_{t-1} is the product of R_d over the business days d in (t-1, t].
  * A business day is a day on which NG has a settlement in the strip. BCOM's definition is days
    when more than half the index weight is open; the two agree on US exchange days, and the
    calendar check below lists every day where the NAV calendar and the settlement calendar
    differ.
  * y is the OECD USD 3-month rate (`data/fixtures/oecd_ir3tib_monthly.csv`). Every day in month
    m uses the value dated m-2, the latest value certainly published by then (the fixture's
    `use` note). It is a proxy for the T-bill rate the deposit names; the sensitivities below
    bound what the choice can move.

WHAT S0'S FORMULA IMPLIES, stated before looking. S0 applies the weight for day k to both the
day-k and the day-(k-1) price. The portfolio it describes therefore trades 20% at each
settlement of business days 5 to 9, not 6 to 10. A fund that tracks the index exactly trades on
those closes.

DAY CLASSES. Each NAV day t is tagged from the business days in (t-1, t]:
  * roll_window: any of them has k in 4..12. That is every day on which some declared schedule
    below differs from another.
  * s0_roll: any of them has k in 6..10, the days on which S0's weights are between 0 and 1 or
    change.
  * january_cim: a January day with k in 6..9. WAV1 and WAV2 then use different CIMs (§2.7 and
    line 1065), and a single-commodity subindex's CIM ratio is not public, so the roll weight on
    those days is known only approximately.
  * calendar: (t-1, t] holds more than one business day, or none.
  * split: t is a split date in `data/fund_facts/proshares_splits.csv`.
  * swap_held (BOIL only): t falls in a quarter that `data/ledger_swap_free_quarters.json`
    marks SWAPS_HELD, which is 2023.
  * missing: a settlement the model needs is absent. The error is then None and the day
    COUNTS AS A FAILURE.

THE VERDICT (one per fund): PASS if, under S0 and over ALL window days, the share with
|err| ≤ 5 bp is at least 0.95, with missing days counted as failures. err is
(iNAV_t - NAV_t) / NAV_t in bp.

THE ROLL DAYS (the reason for this run). They are proven for a fund if, under S0, the share with
|err| ≤ 5 bp is at least 0.95 on the roll_window days as well. The alternative schedules, all
declared here, are scored on the roll_window days by pass share and mean |err|:
  * S0 shifted by s in {-2, -1, +1, +2} business days (trading at the closes of BD 3-7, 4-8,
    6-10 and 7-11);
  * single-day rolls at the close of BD j, for j in {5, ..., 10}.
The schedule with the lowest mean |err| on roll_window days is reported for each fund. If that
schedule is not S0, the finding is that the fund does not roll on the index's days. The finding
is not a pass under a schedule picked after the event.

CONTROLS THAT MUST FIRE (each raises if it does not):
  (a) Appendix C's Table 13 is reproduced to 0.001 index points on all 15 rows.
  (b) Flipping the sign of L gives a pass share below 0.5.
  (c) Pairing each NAV return with the PREVIOUS day's index return gives a pass share below 0.5.
  (d) The gate function returns FAIL on a synthetic series with 6% of days at 6 bp, and PASS on
      one with 4% (`--selftest`).

SENSITIVITIES, reported and never used for the verdict: y = 0; y from month m itself; a one-day
accrual (the deposit formula taken literally) in place of D calendar days; ER = 0. The NAV
rounding floor, from the published precision, is reported per fund.

WHAT THIS DOES NOT TOUCH. It reads BOIL/KOLD NAVs and NG settlements dated before 2024-01-01,
and the OECD rate. It computes no strategy return and no settlement-window price or flow
statistic, so none of H1-H15 is read. It writes one new file, `data/ledger_gate_0b_ng.json`.

DEVIATIONS (after the first run, 2026-09-24): listed in DEVIATIONS below. None touches the verdict.

    uv run python scripts/gate_0b_ng_nav.py              # write the JSON
    uv run python scripts/gate_0b_ng_nav.py --check      # rebuild, compare byte for byte
    uv run python scripts/gate_0b_ng_nav.py --selftest   # control (d)
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_framework.data.panels import load_panel

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_gate_0b_ng.json"
OECD = REPO / "data" / "fixtures" / "oecd_ir3tib_monthly.csv"
SPLITS = REPO / "data" / "fund_facts" / "proshares_splits.csv"
SWAPQ = REPO / "data" / "ledger_swap_free_quarters.json"
RESERVED_FROM = "2024-01-01"
FIRST, LAST = "2017-05-22", "2023-12-29"
FUNDS = {"BOIL": 2, "KOLD": -2}
ER = 0.0095
BP_TOL, SHARE_MIN = 5.0, 0.95
LETTER = "FGHJKMNQUVXZ"
MONTH = {c: i + 1 for i, c in enumerate(LETTER)}
RE_C = re.compile(r"^NG([FGHJKMNQUVXZ])(\d{1,2})$")

#: BCOM Table 9, natural gas: calendar month -> designated contract month (13 = January next year).
DESIGNATED = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7, 7: 9, 8: 9, 9: 11, 10: 11, 11: 13, 12: 13}

#: BCOM Appendix C, Table 13: (BD, WAV1, RW1, WAV2, RW2, BCOM), January 1997.
TABLE13 = [
    (1, 1196.764, 1, 1195.469, 0, 122.574), (2, 1196.121, 1, 1195.107, 0, 122.509),
    (3, 1214.668, 1, 1213.927, 0, 124.408), (4, 1214.314, 1, 1214.285, 0, 124.372),
    (5, 1220.453, 1, 1220.608, 0, 125.001), (6, 1218.382, 0.8, 1219.878, 0.2, 124.816),
    (7, 1216.373, 0.6, 1220.351, 0.4, 124.712), (8, 1207.51, 0.4, 1214.11, 0.6, 123.966),
    (9, 1209.179, 0.2, 1214.664, 0.8, 124.046), (10, 1226.924, 0, 1230.74, 1, 125.687),
    (11, 1212.804, 0, 1218.939, 1, 124.482), (12, 1206.098, 0, 1213.536, 1, 123.93),
    (13, 1194.815, 0, 1203.879, 1, 122.944), (14, 1197.584, 0, 1206.081, 1, 123.169),
    (15, 1197.393, 0, 1206.424, 1, 123.204),
]


#: Changes made after the first run (spec sha256 50a1df0b..., 2026-09-24T09:40Z). None touches the verdict.
DEVIATIONS = [
    "split class: the first run pooled BOIL's and KOLD's split dates into one set; it is now per fund (diagnostic only)",
    "rounding floor: the first run read decimals off the float's repr, which drops trailing zeros and "
    "reads scaled integers as exact; it now finds each row's published decimals (2-8) on the grid "
    "scaled by the later split factor, and raises on a row that sits on none (diagnostic only)",
    "added the 'investigation' block per fund (post hoc, see investigation_rule); the verdict is unchanged",
]

#: The post-hoc investigation of the failing days (deposit line 191: "Failures are investigated").
INVESTIGATION = (
    "POST HOC, written after the first run showed failures clustered on BD6-10 of April 2021 and April 2023. "
    "Those months contain Good Friday (2021-04-02, 2023-04-07), when the NYSE was closed and the strip "
    "nevertheless carries an NG settlement for every contract. Every one of them equals the previous day's, "
    "so these are holiday republications, not trading days. BCOM counts a Business Day only when more than "
    "half its weight is open for trading, so these days are not Business Days, and the pre-registered "
    "calendar (every day with an NG settlement) numbers the rest of the month one day late. The investigation "
    "drops every day on which EVERY NG settlement equals the previous day's (the rule is mechanical, and "
    "the full list across the strip is in holiday_republications_in_strip) and reruns S0 and the declared "
    "alternatives. It is reported beside the verdict and never replaces it."
)


class Gate0bError(RuntimeError):
    pass


# ---------------------------------------------------------------- schedules
Schedule = Callable[[int], float]


def s0(k: int) -> float:
    """BCOM §2.8: the weight on the Next Future on business day k."""
    return min(max((k - 5) / 5.0, 0.0), 1.0)


def shifted(s: int) -> Schedule:
    return lambda k: s0(k - s)


def single_day(j: int) -> Schedule:
    """All of the roll at the close of BD j, so from BD j+1 the index holds the Next Future."""
    return lambda k: 1.0 if k >= j + 1 else 0.0


SCHEDULES: dict[str, Schedule] = {"S0 (BCOM; trades BD5-9 closes)": s0}
for _s, _lab in ((-2, "BD3-7"), (-1, "BD4-8"), (1, "BD6-10"), (2, "BD7-11")):
    SCHEDULES[f"S0{_s:+d} (trades {_lab} closes)"] = shifted(_s)
for _j in range(5, 11):
    SCHEDULES[f"one day (trades BD{_j} close)"] = single_day(_j)
PRIMARY = "S0 (BCOM; trades BD5-9 closes)"


def table13_check() -> float:
    """Control (a): recompute BCOM from Table 13's WAVs with §2.8's formula; return the worst miss."""
    level, worst = TABLE13[0][5], 0.0
    for prev, cur in zip(TABLE13, TABLE13[1:]):
        k, w1, _rw1, w2, _rw2, published = cur
        b = s0(k)
        level = level * ((1 - b) * w1 + b * w2) / ((1 - b) * prev[1] + b * prev[3])
        worst = max(worst, abs(round(level, 3) - published))
    if worst > 0.001 + 1e-12:
        raise Gate0bError(f"control (a) failed: Table 13 not reproduced (worst miss {worst:.4f})")
    return worst


# ---------------------------------------------------------------- inputs
def _ym(contract: str, session: str) -> tuple[int, int] | None:
    """D526's rule (build_fut_settle_strip.ym): a one-digit year is the nearest delivery not more
    than one month behind the session; two digits are explicit."""
    m = RE_C.match(contract)
    if not m:
        return None
    mon, y = MONTH[m.group(1)], m.group(2)
    sy, sm = int(session[:4]), int(session[5:7])
    if len(y) == 2:
        return (2000 + int(y), mon)
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and (cand * 12 + mon) >= (sy * 12 + sm) - 1:
            return (cand, mon)
    return None


def load_inputs() -> tuple[pd.DataFrame, dict[str, dict[tuple[int, int], float]], dict[str, Any]]:
    nav_p = load_panel("fund_nav_daily", reserved_from=RESERVED_FROM, usecols=["date", "fund", "nav"])
    nav = nav_p.frame
    nav = nav[nav["fund"].isin(list(FUNDS))].copy()
    nav["date"] = nav["date"].astype(str)
    st_p = load_panel("fut_settle_strip", reserved_from=RESERVED_FROM, usecols=["root", "contract", "ref", "settle"])
    st = st_p.frame
    st = st[st["root"] == "NG"]
    settles: dict[str, dict[tuple[int, int], float]] = {}
    for c, ref, px in zip(st["contract"].astype(str), st["ref"].astype(str), st["settle"].astype(float)):
        ym = _ym(c, ref)
        if ym is None:
            raise Gate0bError(f"unparsed NG contract {c!r} on {ref}")
        day = settles.setdefault(ref, {})
        if ym in day and day[ym] != px:
            raise Gate0bError(f"two settlements for NG {ym} on {ref}")
        day[ym] = px
    for d in settles:
        if d >= RESERVED_FROM:
            raise Gate0bError(f"a settlement dated {d} is in memory")
    if (nav["date"] >= RESERVED_FROM).any():
        raise Gate0bError("a NAV row on or after the seal is in memory")
    reads = {"fund_nav_daily": {"sha256": nav_p.sha256, **nav_p.record},
             "fut_settle_strip": {"sha256": st_p.sha256, **st_p.record}}
    return nav, settles, reads


def load_rates() -> dict[str, float]:
    with OECD.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["currency"] == "USD" and r["period"] < RESERVED_FROM[:7]]
    return {r["period"]: float(r["rate_pct"]) / 100.0 for r in rows}


def _month_minus(ym: str, n: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) - n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def splits() -> dict[str, list[tuple[str, str, int]]]:
    """fund -> [(date, 'Reverse'|'Forward', ratio)] from ProShares' own split file."""
    out: dict[str, list[tuple[str, str, int]]] = {f: [] for f in FUNDS}
    with SPLITS.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["Symbol"] in FUNDS:
                mm, dd, yy = r["Date of Split"].split("/")
                out[r["Symbol"]].append((f"{yy}-{mm}-{dd}", r["Split Type"], int(r["Ratio"])))
    return out


def swap_held_quarters() -> set[str]:
    d = json.loads(SWAPQ.read_text(encoding="utf-8"))
    q = d["funds"]["BOIL"]["quarters"]
    return {k for k, v in q.items() if v["verdict"] == "SWAPS_HELD"}


# ---------------------------------------------------------------- the index
def contracts_for(day: str) -> tuple[tuple[int, int], tuple[int, int]]:
    y, m = int(day[:4]), int(day[5:7])

    def des(yy: int, mm: int) -> tuple[int, int]:
        c = DESIGNATED[mm]
        return (yy + 1, c - 12) if c > 12 else (yy, c)

    lead = des(y, m)
    nxt = des(y + 1, 1) if m == 12 else des(y, m + 1)
    return lead, nxt


def business_days(settles: dict[str, dict[tuple[int, int], float]]) -> tuple[list[str], dict[str, int]]:
    days = sorted(settles)
    bd: dict[str, int] = {}
    count: dict[str, int] = {}
    for d in days:
        count[d[:7]] = count.get(d[:7], 0) + 1
        bd[d] = count[d[:7]]
    return days, bd


def index_returns(days: list[str], bd: dict[str, int], settles: dict[str, dict[tuple[int, int], float]],
                  sched: Schedule) -> dict[str, float | None]:
    """R_d for every business day after the first; None where a needed settlement is absent."""
    out: dict[str, float | None] = {}
    for p, d in zip(days, days[1:]):
        lead, nxt = contracts_for(d)
        b = sched(bd[d])
        try:
            if b == 0.0:
                num, den = settles[d][lead], settles[p][lead]
            elif b == 1.0:
                num, den = settles[d][nxt], settles[p][nxt]
            else:
                num = (1 - b) * settles[d][lead] + b * settles[d][nxt]
                den = (1 - b) * settles[p][lead] + b * settles[p][nxt]
        except KeyError:
            out[d] = None
            continue
        out[d] = num / den
    return out


# ---------------------------------------------------------------- replication
def replicate(nav: pd.DataFrame, fund: str, L: int, days: list[str], bd: dict[str, int],
              R: dict[str, float | None], rates: dict[str, float], *, rate_lag: int = 2,
              accrual: str = "calendar", er: float = ER, lag_index: bool = False) -> list[dict[str, Any]]:
    g = nav[nav["fund"] == fund].sort_values("date")
    dates, navs = list(g["date"]), list(g["nav"].astype(float))
    rows: list[dict[str, Any]] = []
    for i in range(2, len(dates)):
        t0, t1 = dates[i - 1], dates[i]
        if not (FIRST <= t1 <= LAST):
            continue
        # the business days in (t0, t1]; control (c) takes the previous NAV interval's instead
        lo, hi = (dates[i - 2], t0) if lag_index else (t0, t1)
        in_gap = days[bisect.bisect_right(days, lo): bisect.bisect_right(days, hi)]
        ratio: float | None = 1.0
        for d in in_gap:
            r = R.get(d)
            if r is None or ratio is None:
                ratio = None
                break
            ratio *= r
        D = (pd.Timestamp(t1) - pd.Timestamp(t0)).days
        n = D if accrual == "calendar" else 1
        y = 0.0 if rate_lag < 0 else rates[_month_minus(t1[:7], rate_lag)]
        ks = [bd[d] for d in in_gap]
        row: dict[str, Any] = {"date": t1, "prev": t0, "bd": ks, "n_bdays": len(in_gap)}
        if ratio is None:
            row["err_bp"] = None
        else:
            inav = navs[i - 1] * (1 + L * (ratio - 1)) + navs[i - 1] * n * (y / 360 - er / 365)
            row["err_bp"] = (inav - navs[i]) / navs[i] * 1e4
        rows.append(row)
    return rows


def classify(rows: list[dict[str, Any]], fund: str, split_days: set[str], swapq: set[str]) -> None:
    for r in rows:
        ks = r["bd"]  # type: ignore[assignment]
        d = str(r["date"])
        q = f"{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}"
        r["roll_window"] = any(4 <= k <= 12 for k in ks)  # type: ignore[attr-defined]
        r["s0_roll"] = any(6 <= k <= 10 for k in ks)  # type: ignore[attr-defined]
        r["january_cim"] = d[5:7] == "01" and any(6 <= k <= 9 for k in ks)  # type: ignore[attr-defined]
        r["calendar"] = r["n_bdays"] != 1
        r["split"] = d in split_days
        r["swap_held"] = fund == "BOIL" and q in swapq
        r["missing"] = r["err_bp"] is None


def gate(errs: Sequence[float | None]) -> dict[str, Any]:
    n = len(errs)
    ok = sum(1 for e in errs if e is not None and abs(e) <= BP_TOL)
    share = ok / n if n else float("nan")
    return {"days": n, "within_5bp": ok, "share": round(share, 6), "pass": bool(n and share >= SHARE_MIN)}


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    e = [r["err_bp"] for r in rows]
    a = np.array([abs(x) for x in e if x is not None], dtype=float)  # type: ignore[arg-type]
    s = gate(e)  # type: ignore[arg-type]
    s["missing"] = sum(1 for x in e if x is None)
    if len(a):
        s.update({"mean_abs_bp": round(float(a.mean()), 4), "median_abs_bp": round(float(np.median(a)), 4),
                  "p95_abs_bp": round(float(np.quantile(a, 0.95)), 4), "max_abs_bp": round(float(a.max()), 4)})
    return s


def _sub(rows: list[dict[str, Any]], pred: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    return [r for r in rows if pred(r)]


def rounding_floor(nav: pd.DataFrame, fund: str, sp: list[tuple[str, str, int]]) -> dict[str, Any]:
    """The NAV rounding floor. The fixture is back-adjusted for every later split, so a NAV published
    to n decimals reads as a multiple of 10^-n x F(t), where F(t) is the product of the later split
    ratios (reverse multiplies, forward divides). Each row's n is the smallest in 2..8 that puts it
    on that grid, and the floor is half a unit on each of two NAVs, relative to NAV, in bp."""
    g = nav[(nav["fund"] == fund) & (nav["date"] >= FIRST) & (nav["date"] <= LAST)]
    bounds: list[float] = []
    decimals: dict[str, int] = {}
    for d, v in zip(g["date"], g["nav"].astype(float)):
        F = 1.0
        for sd, kind, ratio in sp:
            if sd > d:
                F *= ratio if kind == "Reverse" else 1.0 / ratio
        n = next((k for k in range(2, 9) if abs(v / (10.0 ** -k * F) - round(v / (10.0 ** -k * F)))
                  < 1e-6 * max(1.0, v / (10.0 ** -k * F))), None)
        decimals[str(n)] = decimals.get(str(n), 0) + 1
        if n is None:
            raise Gate0bError(f"{fund} {d}: NAV {v} is on no grid of 2-8 decimals x split factor {F}")
        bounds.append(2 * 0.5 * 10.0 ** -n * F / v * 1e4)
    return {"rows": len(bounds), "rows_by_published_decimals": dict(sorted(decimals.items())),
            "note": "the fewest decimals that fit, so a 4-decimal NAV ending in 0 or 00 counts as 3 or 2; "
                    "the ~1% and ~9% of rows at 2 and 3 are that arithmetic, and max_bound_bp is an upper bound",
            "median_bound_bp": round(float(np.median(bounds)), 5), "max_bound_bp": round(float(np.max(bounds)), 5)}


def copy_days(settles: dict[str, dict[tuple[int, int], float]]) -> list[str]:
    """Days on which EVERY NG settlement equals the previous day's: holiday republications."""
    days = sorted(settles)
    return [d for p, d in zip(days, days[1:]) if settles[d] == settles[p]]


# ---------------------------------------------------------------- build
def _failing(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"date": r["date"], "bd": r["bd"],
             "err_bp": None if r["err_bp"] is None else round(float(r["err_bp"]), 3),  # type: ignore[arg-type]
             "tags": [t for t in ("roll_window", "january_cim", "calendar", "split", "swap_held", "missing") if r[t]]}
            for r in rows if r["err_bp"] is None or abs(float(r["err_bp"])) > BP_TOL]  # type: ignore[arg-type]


def evaluate(nav: pd.DataFrame, fund: str, L: int, settles: dict[str, dict[tuple[int, int], float]],
             days: list[str], bd: dict[str, int], rates: dict[str, float], split_days: set[str],
             swapq: set[str], *, full: bool) -> dict[str, Any]:
    """Everything the spec reports for one fund on one business-day calendar."""
    R = {name: index_returns(days, bd, settles, f) for name, f in SCHEDULES.items()}
    rows = replicate(nav, fund, L, days, bd, R[PRIMARY], rates)
    classify(rows, fund, split_days, swapq)
    f: dict[str, Any] = {"verdict": summary(rows)}
    f["classes"] = {
        "not_roll_window": summary(_sub(rows, lambda r: not r["roll_window"])),
        "roll_window": summary(_sub(rows, lambda r: bool(r["roll_window"]))),
        "s0_roll": summary(_sub(rows, lambda r: bool(r["s0_roll"]))),
        "january_cim": summary(_sub(rows, lambda r: bool(r["january_cim"]))),
        "calendar": summary(_sub(rows, lambda r: bool(r["calendar"]))),
        "split": summary(_sub(rows, lambda r: bool(r["split"]))),
        "swap_held": summary(_sub(rows, lambda r: bool(r["swap_held"]))),
        "swap_free": summary(_sub(rows, lambda r: not r["swap_held"])),
    }
    f["roll_days_proven"] = bool(f["classes"]["roll_window"]["pass"])  # type: ignore[index]
    sch: dict[str, Any] = {}
    for name in SCHEDULES:
        rr = replicate(nav, fund, L, days, bd, R[name], rates)
        classify(rr, fund, split_days, swapq)
        sch[name] = {"all": summary(rr), "roll_window": summary(_sub(rr, lambda r: bool(r["roll_window"])))}
    f["schedules"] = sch
    best = min(sch, key=lambda n: sch[n]["roll_window"]["mean_abs_bp"])  # type: ignore[index]
    f["best_schedule_on_roll_window"] = best
    f["best_is_s0"] = best == PRIMARY
    f["failing_days"] = _failing(rows)
    if not full:
        return f

    by_bd: dict[str, Any] = {}
    for k in range(1, 24):
        sub = [r for r in rows if r["n_bdays"] == 1 and r["bd"] == [k]]
        if sub:
            by_bd[str(k)] = summary(sub)
    f["by_business_day"] = by_bd
    f["by_year"] = {y: summary([r for r in rows if str(r["date"])[:4] == y])
                    for y in sorted({str(r["date"])[:4] for r in rows})}
    sens = {
        "y=0": replicate(nav, fund, L, days, bd, R[PRIMARY], rates, rate_lag=-1),
        "y month m": replicate(nav, fund, L, days, bd, R[PRIMARY], rates, rate_lag=0),
        "one-day accrual": replicate(nav, fund, L, days, bd, R[PRIMARY], rates, accrual="one"),
        "ER=0": replicate(nav, fund, L, days, bd, R[PRIMARY], rates, er=0.0),
    }
    f["sensitivities"] = {k: summary(v) for k, v in sens.items()}
    wrong_sign = summary(replicate(nav, fund, -L, days, bd, R[PRIMARY], rates))
    lagged = summary(replicate(nav, fund, L, days, bd, R[PRIMARY], rates, lag_index=True))
    if float(wrong_sign["share"]) >= 0.5:  # type: ignore[arg-type]
        raise Gate0bError(f"control (b) failed for {fund}: sign-flipped L passes {wrong_sign['share']}")
    if float(lagged["share"]) >= 0.5:  # type: ignore[arg-type]
        raise Gate0bError(f"control (c) failed for {fund}: day-lagged index passes {lagged['share']}")
    f["controls"] = {"b_sign_flipped": wrong_sign, "c_index_lagged_one_day": lagged}
    return f


def build() -> dict[str, Any]:
    worst13 = table13_check()
    nav, settles, reads = load_inputs()
    rates = load_rates()
    days, bd = business_days(settles)
    sp, swapq = splits(), swap_held_quarters()
    win_days = [d for d in days if FIRST <= d <= LAST]

    # the investigation's calendar (post hoc): holiday republications are not business days
    copies = copy_days(settles)
    inv_settles = {d: v for d, v in settles.items() if d not in set(copies)}
    inv_days, inv_bd = business_days(inv_settles)

    doc: dict[str, Any] = {
        "spec": "settlement-ledger AITODO item 1 / deposit Gate 0b: BOIL and KOLD NAV rebuilt from NG settlements "
                "under the Bloomberg Natural Gas Subindex (BCOM §2.8, Table 9); see the script docstring",
        "gate": f"per fund, |iNAV - NAV| <= {BP_TOL} bp on >= {SHARE_MIN:.0%} of days (deposit line 191)",
        "window": [FIRST, LAST], "reserved_from": RESERVED_FROM, "reads": reads,
        "deviations": DEVIATIONS,
        "controls": {"a_table13_worst_miss": worst13},
        "investigation_rule": INVESTIGATION,
        "holiday_republications_in_strip": copies,
        "funds": {},
    }
    for fund, L in FUNDS.items():
        split_days = {d for d, _k, _r in sp[fund]}
        navd = set(nav[(nav["fund"] == fund)]["date"])
        g = nav[(nav["fund"] == fund) & (nav["date"] >= FIRST) & (nav["date"] <= LAST)]
        cal = {"nav_days_without_ng_settlement": sorted(d for d in g["date"] if d not in bd),
               "ng_settlement_days_without_nav": sorted(d for d in win_days if d not in navd)}
        f: dict[str, Any] = {"L": L, "calendar_check": cal, "rounding_floor": rounding_floor(nav, fund, sp[fund])}
        f.update(evaluate(nav, fund, L, settles, days, bd, rates, split_days, swapq, full=True))
        f["investigation"] = evaluate(nav, fund, L, inv_settles, inv_days, inv_bd, rates, split_days, swapq, full=False)
        doc["funds"][fund] = f  # type: ignore[index]
    return doc


def selftest() -> None:
    """Control (d): the gate function must fail at 6% of days over the bar and pass at 4%."""
    bad = [6.0] * 6 + [1.0] * 94
    good = [6.0] * 4 + [1.0] * 96
    if gate(bad)["pass"] or not gate(good)["pass"]:
        raise Gate0bError("control (d) failed: the gate function does not separate 94% from 96%")
    if gate([None] * 5 + [1.0] * 95)["pass"] is not True or gate([None] * 6 + [1.0] * 94)["pass"]:
        raise Gate0bError("control (d) failed: a missing day is not counted as a failure")
    table13_check()
    if not math.isclose(s0(6), 0.2) or s0(5) != 0.0 or s0(10) != 1.0 or shifted(1)(7) != s0(6):
        raise Gate0bError("schedule arithmetic wrong")
    print("[selftest] gate separates 94% from 96%; missing counts as failure; Table 13 reproduced")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise Gate0bError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for fund, f in doc["funds"].items():  # type: ignore[union-attr]
        v = f["verdict"]
        print(f"{fund}: {v['within_5bp']}/{v['days']} within 5 bp = {v['share']:.4f} -> {'PASS' if v['pass'] else 'FAIL'}"
              f"  (median |err| {v.get('median_abs_bp')} bp, missing {v['missing']})")
        for c, s in f["classes"].items():
            print(f"   {c:16s} {s['within_5bp']:5d}/{s['days']:5d} = {s['share']:.4f}  mean|err| {s.get('mean_abs_bp')}")
        print(f"   best schedule on roll-window days: {f['best_schedule_on_roll_window']}")
        iv = f["investigation"]
        print(f"   INVESTIGATION (post hoc, Good Fridays dropped): {iv['verdict']['within_5bp']}/{iv['verdict']['days']}"
              f" = {iv['verdict']['share']:.4f}; roll_window {iv['classes']['roll_window']['share']:.4f};"
              f" best {iv['best_schedule_on_roll_window']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
