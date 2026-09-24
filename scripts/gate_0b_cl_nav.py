"""Gate 0b for UCO and SCO: rebuild each day's NAV from CL settlements under the funds' benchmark (AITODO 1d).

SPEC -- written 2026-09-24 before any replicated NAV was computed, and frozen from then on. The NG
version (`scripts/gate_0b_ng_nav.py`) is reused function for function; only the index differs.

THE GATE (deposit §P3.1 line 191): per fund, |iNAV at settlement - official NAV[t]| <= 5 bp on
>= 95% of days. UCO: L = +2. SCO: L = -2. ER 0.95%. Window: NAV dates 2017-05-22 → 2023-12-29.
Every panel goes through `load_panel(reserved_from="2024-01-01")`.

THE MODEL is Gate 0b's own:
    iNAV_t = NAV_{t-1} (1 + L (I_t/I_{t-1} - 1)) + NAV_{t-1} D (y/360 - ER/365)
I is recomputed from NYMEX CL settlements (`fut_settle_strip`, plus the two EIA-recovered days in
`data/ledger_settle_holes_2020.csv`). The benchmark follows the 10-K for 2020
(0001193125-21-049128):
  * ERA A, NAV dates through 2020-09-16: the Bloomberg WTI Crude Oil Subindex. BCOM §2.8's formula
    with Table 9's WTI row (Mar Mar May May Jul Jul Sep Sep Nov Nov Jan Jan). This is the same
    construction that passed for NG.
  * ERA B, from 2020-09-17 (the first NAV struck on the new benchmark; the 9/17 return uses era B):
    the Bloomberg Commodity Balanced WTI Crude Oil Index, three schedules, each rolled by §2.8's
    formula on its own roll days:
      - monthly: in month m, lead = delivery month m+2 and next = m+3, rolled every month;
      - June: rolls in March of year Y, from June Y to June Y+1; otherwise holds its June;
      - December: rolls in September of year Y, from Dec Y to Dec Y+1; otherwise holds its December.
    Component values drift with prices. The index's daily return is the value-weighted mean of the
    component returns. "The Benchmark weights are equally reset semi-annually in the months of
    March and September on close of the first business day": at the close of BD1 in March and
    September each component is set to one third. The first reset used is 2020-09-01.
  * Business days: CL settlement days, minus holiday republications (every CL settlement equal to
    the previous day's). That rule was found in NG's Gate 0b and is declared here in advance.
  * The roll schedule S0 and the ten declared alternatives are NG's, applied to every component at
    once.

DAY CLASSES (reported; the verdict is over ALL days):
  * roll_window (BD 4-12) and s0_roll (BD 6-10), as NG;
  * annual_roll: era B, March or September, BD 4-12, when a second schedule rolls as well;
  * reset_day: era B, BD1 of March or September;
  * transition: 2020-04-01 → 2020-09-16. The benchmark was still era A, but on 2020-06-30 the funds
    held three months (`data/ledger_cl_held_months_check.json`). A departure is expected here;
  * switch_day: 2020-09-17;
  * swap_held: UCO on every day (it held swaps at every quarter-end); SCO through 2020-Q3. The swaps
    pay the same benchmark, so the NAV still follows I. This class says where that assumption
    carries the result;
  * calendar and split, as NG.

VERDICT: PASS per fund if the share within 5 bp over all window days is >= 0.95. The share
excluding the transition class is reported beside it, never in its place.

THE ROLL DAYS: proven for a fund if the roll_window share within 5 bp is >= 0.95 under S0. The
best of the eleven schedules on roll_window days is reported.

CONTROLS THAT MUST FIRE (each raises if it does not): (a) NG's Table 13 check; (b) flipping L's
sign passes < 0.5; (c) a one-day lag passes < 0.5; (d) on era-B days, the era-A index (the plain
subindex, as if there had been no switch) must pass strictly fewer days than the Balanced index,
so the switch is detectable.

RESOLUTION (added 2026-09-24, after the investigation): Bloomberg's own BCBCLI methodology, fetched
on the principal's instruction, states the roll as BD2-3 at 50% a day, applied with yesterday's
weights. That is exactly the candidate the post-hoc search picked. The script asserts the match
and reports the Gate re-scored under the DOCUMENTED rule, over all days and with the transition
excluded. The pre-registered verdict above is left as it was.

WHAT THIS DOES NOT TOUCH: it reads UCO/SCO NAVs and CL settlements before 2024-01-01, computes
no strategy return and no settlement-window statistic, and writes `data/ledger_gate_0b_cl.json`.

    uv run python scripts/gate_0b_cl_nav.py            # write the JSON
    uv run python scripts/gate_0b_cl_nav.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_gate_0b_cl.json"
HOLES = REPO / "data" / "ledger_settle_holes_2020.csv"
SWITCH = "2020-09-17"
TRANSITION = ("2020-04-01", "2020-09-16")
FUNDS = {"UCO": 2, "SCO": -2}
SCO_SWAPS_THROUGH = "2020-09-30"
RE_CL = re.compile(r"^CL([FGHJKMNQUVXZ])(\d{1,2})$")
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
DESIGNATED = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7, 7: 9, 8: 9, 9: 11, 10: 11, 11: 13, 12: 13}

Key = tuple[int, int]


class GateError(RuntimeError):
    pass


def _gate0b() -> Any:
    spec = importlib.util.spec_from_file_location("gate_0b_ng_nav", REPO / "scripts" / "gate_0b_ng_nav.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules["gate_0b_ng_nav"] = m
    spec.loader.exec_module(m)
    return m


G = _gate0b()


def _ym_cl(contract: str, session: str) -> Key | None:
    m = RE_CL.match(contract)
    if not m:
        return None
    return G._ym("NG" + contract[2:], session)  # type: ignore[no-any-return]


def _add(y: int, m: int) -> Key:
    return (y + (m - 1) // 12, (m - 1) % 12 + 1)


def load() -> tuple[Any, dict[str, dict[Key, float]], dict[str, Any]]:
    nav_p = G.load_panel("fund_nav_daily", reserved_from=G.RESERVED_FROM, usecols=["date", "fund", "nav"])
    nav = nav_p.frame
    nav = nav[nav["fund"].isin(list(FUNDS))].copy()
    nav["date"] = nav["date"].astype(str)
    st_p = G.load_panel("fut_settle_strip", reserved_from=G.RESERVED_FROM, usecols=["root", "contract", "ref", "settle"])
    st = st_p.frame
    st = st[st["root"] == "CL"]
    settles: dict[str, dict[Key, float]] = {}

    def put(c: str, ref: str, px: float) -> None:
        ym = _ym_cl(c, ref)
        if ym is None:
            raise GateError(f"unparsed CL contract {c!r} on {ref}")
        day = settles.setdefault(ref, {})
        if ym in day and day[ym] != px:
            raise GateError(f"two settlements for CL {ym} on {ref}")
        day[ym] = px

    for c, ref, px in zip(st["contract"].astype(str), st["ref"].astype(str), st["settle"].astype(float)):
        put(c, ref, px)
    strip_days = set(settles)
    with HOLES.open(encoding="utf-8", newline="") as fh:
        n_fill = 0
        for r in csv.DictReader(fh):
            if r["root"] == "CL":
                if r["ref"] in strip_days:
                    raise GateError(f"hole day {r['ref']} already has CL settlements")
                put(r["contract"], r["ref"], float(r["settle"]))
                n_fill += 1
    if any(d >= G.RESERVED_FROM for d in settles) or (nav["date"] >= G.RESERVED_FROM).any():
        raise GateError("a row on or after the seal is in memory")
    reads = {"fund_nav_daily": {"sha256": nav_p.sha256, **nav_p.record},
             "fut_settle_strip": {"sha256": st_p.sha256, **st_p.record}, "holes_filled_cl_rows": n_fill}
    return nav, settles, reads


# ------------------------------------------------------------------ the two benchmarks
def era_a_contracts(day: str) -> tuple[Key, Key]:
    y, m = int(day[:4]), int(day[5:7])

    def des(yy: int, mm: int) -> Key:
        c = DESIGNATED[mm]
        return (yy + 1, c - 12) if c > 12 else (yy, c)

    return des(y, m), (des(y + 1, 1) if m == 12 else des(y, m + 1))


def era_b_components(day: str) -> list[tuple[Key, Key]]:
    """(lead, next) for the monthly, June and December schedules in `day`'s month."""
    y, m = int(day[:4]), int(day[5:7])
    monthly = (_add(y, m + 2), _add(y, m + 3))
    if m == 3:
        june = ((y, 6), (y + 1, 6))
    else:
        j = (y + 1, 6) if m > 3 else (y, 6)
        june = (j, j)
    if m == 9:
        dec = ((y, 12), (y + 1, 12))
    else:
        dd = (y + 1, 12) if m > 9 else (y, 12)
        dec = (dd, dd)
    return [monthly, june, dec]


def _ratio(s_d: dict[Key, float], s_p: dict[Key, float], lead: Key, nxt: Key, b: float) -> float:
    if lead == nxt or b == 0.0:
        return s_d[lead] / s_p[lead]
    if b == 1.0:
        return s_d[nxt] / s_p[nxt]
    return ((1 - b) * s_d[lead] + b * s_d[nxt]) / ((1 - b) * s_p[lead] + b * s_p[nxt])


def index_returns(days: list[str], bd: dict[str, int], settles: dict[str, dict[Key, float]],
                  sched: Any, *, force_era_a: bool = False, sched_b: Any = None) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    v = [1 / 3, 1 / 3, 1 / 3]
    started = False
    for p, d in zip(days, days[1:]):
        k = bd[d]
        b = sched(k) if (sched_b is None or d < "2020-09-01") else sched_b(k)
        if force_era_a or d < SWITCH:
            lead, nxt = era_a_contracts(d)
            try:
                out[d] = _ratio(settles[d], settles[p], lead, nxt, b)
            except KeyError:
                out[d] = None
        if force_era_a or d < "2020-09-01":
            continue
        # era B components run from the 2020-09-01 reset so the weights at the switch are the index's own
        comps = era_b_components(d)
        try:
            r = [_ratio(settles[d], settles[p], lead, nxt, b) for lead, nxt in comps]
        except KeyError:
            if d >= SWITCH:
                out[d] = None
            continue
        if started:
            tot = sum(v)
            rb = sum(vi * ri for vi, ri in zip(v, r)) / tot
            v = [vi * ri for vi, ri in zip(v, r)]
            if d >= SWITCH:
                out[d] = rb
        if k == 1 and d[5:7] in ("03", "09"):
            tot = sum(v)
            v = [tot / 3] * 3
            started = True
    return out


# ------------------------------------------------------------------ classes and evaluation
def classify(rows: list[dict[str, Any]], fund: str, split_days: set[str]) -> None:
    for r in rows:
        ks, d = r["bd"], str(r["date"])
        era_b = d >= SWITCH
        r["roll_window"] = any(4 <= k <= 12 for k in ks)
        r["s0_roll"] = any(6 <= k <= 10 for k in ks)
        r["annual_roll"] = era_b and d[5:7] in ("03", "09") and any(4 <= k <= 12 for k in ks)
        r["reset_day"] = era_b and d[5:7] in ("03", "09") and 1 in ks
        r["transition"] = TRANSITION[0] <= d <= TRANSITION[1]
        r["switch_day"] = d == SWITCH
        r["swap_held"] = fund == "UCO" or d <= SCO_SWAPS_THROUGH
        r["calendar"] = r["n_bdays"] != 1
        r["split"] = d in split_days
        r["missing"] = r["err_bp"] is None


CLASSES = ("roll_window", "s0_roll", "annual_roll", "reset_day", "transition", "switch_day", "swap_held", "calendar", "split")


def evaluate(nav: Any, fund: str, L: int, days: list[str], bd: dict[str, int], settles: dict[str, dict[Key, float]],
             rates: dict[str, float], split_days: set[str]) -> dict[str, Any]:
    R = {name: index_returns(days, bd, settles, f) for name, f in G.SCHEDULES.items()}
    rows = G.replicate(nav, fund, L, days, bd, R[G.PRIMARY], rates)
    classify(rows, fund, split_days)
    f: dict[str, Any] = {"verdict": G.summary(rows),
                         "excluding_transition": G.summary([r for r in rows if not r["transition"]])}
    f["classes"] = {c: G.summary([r for r in rows if r[c]]) for c in CLASSES}
    f["classes"]["not_roll_window"] = G.summary([r for r in rows if not r["roll_window"]])
    f["classes"]["era_a"] = G.summary([r for r in rows if str(r["date"]) < SWITCH and not r["transition"]])
    f["classes"]["era_b"] = G.summary([r for r in rows if str(r["date"]) >= SWITCH])
    f["roll_days_proven"] = bool(f["classes"]["roll_window"]["pass"])
    sch = {}
    for name in G.SCHEDULES:
        rr = G.replicate(nav, fund, L, days, bd, R[name], rates)
        classify(rr, fund, split_days)
        sch[name] = {"all": G.summary(rr), "roll_window": G.summary([r for r in rr if r["roll_window"]])}
    f["schedules"] = sch
    best = min(sch, key=lambda n: sch[n]["roll_window"]["mean_abs_bp"])
    f["best_schedule_on_roll_window"] = best
    f["best_is_s0"] = best == G.PRIMARY
    f["by_year"] = {y: G.summary([r for r in rows if str(r["date"])[:4] == y]) for y in sorted({str(r["date"])[:4] for r in rows})}
    f["by_business_day"] = {str(k): G.summary(sub) for k in range(1, 24)
                            if (sub := [r for r in rows if r["n_bdays"] == 1 and r["bd"] == [k]])}
    # controls
    wrong = G.summary(G.replicate(nav, fund, -L, days, bd, R[G.PRIMARY], rates))
    lagged = G.summary(G.replicate(nav, fund, L, days, bd, R[G.PRIMARY], rates, lag_index=True))
    if wrong["share"] >= 0.5 or lagged["share"] >= 0.5:
        raise GateError(f"control (b)/(c) failed for {fund}: sign-flip {wrong['share']}, lag {lagged['share']}")
    ra = index_returns(days, bd, settles, G.s0, force_era_a=True)
    rows_a = [r for r in G.replicate(nav, fund, L, days, bd, ra, rates) if str(r["date"]) >= SWITCH]
    era_a_on_b = G.summary(rows_a)
    if era_a_on_b["within_5bp"] >= f["classes"]["era_b"]["within_5bp"]:
        raise GateError(f"control (d) failed for {fund}: the plain subindex fits era B as well as the Balanced index")
    f["controls"] = {"b_sign_flipped": wrong, "c_index_lagged_one_day": lagged, "d_era_a_index_on_era_b_days": era_a_on_b}
    f["failing_days"] = [{"date": r["date"], "bd": r["bd"],
                          "err_bp": None if r["err_bp"] is None else round(float(r["err_bp"]), 3),
                          "tags": [c for c in CLASSES if r[c]] + (["missing"] if r["missing"] else [])}
                         for r in rows if r["err_bp"] is None or abs(float(r["err_bp"])) > G.BP_TOL]
    return f


#: POST HOC (after the first run, 2026-09-24). The pre-registered verdict stands (FAIL for both). The first
#: run's era-B failures clustered on BD3-9 of every month, not only in the annual-roll months, so
#: the Balanced era's roll window was searched over the candidates below, all of them listed.
INVESTIGATION = (
    "POST HOC. Era A (the WTI Subindex, S0) passed 99.9%/99.4% and needed nothing. On era-B days (from "
    "2020-09-17) S0 passed only 88.9%/88.5%, and the failures sat on BD3-9 of EVERY month, so the "
    "Balanced index's roll window, applied to all three schedules, was searched. The candidates: "
    "5-day windows starting BD1-8; 1-day rolls taking effect at BD1-5; 2- and 3-day windows starting "
    "BD2-4; and S0. That is 20 schedules. They are scored on era-B days only, and all are listed in "
    "`investigation.candidates`. The winner is then combined with S0 for era A, and the whole "
    "window re-scored. This is a search, so it is reported beside the verdict and never replaces "
    "it. Confirmation belongs to the index's own methodology document (BCBCLI), which is not on disk."
)


#: The index's own rule, read AFTER the investigation on the principal's instruction (2026-09-24).
DOC_URL = "https://data.bloomberglp.com/professional/sites/10/Bloomberg-Commodity-Balanced-WTI-Crude-Oil-Index-Methodology.pdf"
DOC_PATH = REPO / "data" / "raw" / "bloomberg" / "Bloomberg-Commodity-Balanced-WTI-Crude-Oil-Index-Methodology.pdf"
DOC_SHA256 = "7b6afea7533df1ccaa6fa13930f1650c1b0384b5c358408ef4306bf3563c9bc6"
DOC_RULE = (
    "BCBCLI methodology (published 6/23/2020), Section 1: 'All commodities will roll on the second and the "
    "third Business Day of each calendar month.' Section 3: 'starting on the second business day rolling "
    "over the two Business Days of each month, at 50% each Business Day'. The Daily Excess Return uses "
    "YESTERDAY's roll weights (the WAV and PWAV definitions, and Table 4), so the return on BD3 is "
    "50/50 and from BD4 it is all Next Contract. That is the candidate '2-day, weights from BD3'. "
    "Table 3's calendar matches the three schedules modelled here, and a 'Business Day' is any day "
    "NYMEX is open."
)
DOC_SCHEDULE = "2-day, weights from BD3"


def _window(first: int, n: int) -> Any:
    return lambda k: min(max((k - first + 1) / n, 0.0), 1.0)


def _candidates() -> dict[str, Any]:
    c: dict[str, Any] = {"S0 (declared)": G.s0}
    for first in range(1, 9):
        c[f"5-day, weights from BD{first}"] = _window(first, 5)
    for first in range(1, 6):
        c[f"1-day, weights from BD{first}"] = _window(first, 1)
    for first in range(2, 5):
        c[f"2-day, weights from BD{first}"] = _window(first, 2)
        c[f"3-day, weights from BD{first}"] = _window(first, 3)
    return c


def investigate(nav: Any, fund: str, L: int, days: list[str], bd: dict[str, int],
                settles: dict[str, dict[Key, float]], rates: dict[str, float], split_days: set[str]) -> dict[str, Any]:
    cand = {}
    for name, f in _candidates().items():
        R = index_returns(days, bd, settles, G.s0, sched_b=f)
        rows = [r for r in G.replicate(nav, fund, L, days, bd, R, rates) if str(r["date"]) >= SWITCH]
        cand[name] = G.summary(rows)
    best = max(cand, key=lambda n: (cand[n]["share"], -cand[n]["mean_abs_bp"]))
    R = index_returns(days, bd, settles, G.s0, sched_b=_candidates()[best])
    rows = G.replicate(nav, fund, L, days, bd, R, rates)
    classify(rows, fund, split_days)
    return {
        "candidates_era_b": cand, "best_era_b": best,
        "whole_window_with_best": G.summary(rows),
        "whole_window_with_best_excluding_transition": G.summary([r for r in rows if not r["transition"]]),
        "roll_window_with_best_excluding_transition": G.summary([r for r in rows if r["roll_window"] and not r["transition"]]),
        "failing_days_excluding_transition": [
            {"date": r["date"], "bd": r["bd"], "err_bp": None if r["err_bp"] is None else round(float(r["err_bp"]), 3)}
            for r in rows if not r["transition"] and (r["err_bp"] is None or abs(float(r["err_bp"])) > G.BP_TOL)],
    }


def build() -> dict[str, Any]:
    worst13 = G.table13_check()
    nav, settles, reads = load()
    copies = G.copy_days(settles)
    settles = {d: v for d, v in settles.items() if d not in set(copies)}
    days, bd = G.business_days(settles)
    rates = G.load_rates()
    splits: dict[str, set[str]] = {f: set() for f in FUNDS}
    with G.SPLITS.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["Symbol"] in FUNDS:
                mm, dd, yy = r["Date of Split"].split("/")
                splits[r["Symbol"]].add(f"{yy}-{mm}-{dd}")
    doc: dict[str, Any] = {
        "spec": "settlement-ledger AITODO 1d / deposit Gate 0b: UCO and SCO NAV rebuilt from CL settlements under the "
                "WTI Subindex (to 2020-09-16) and the Balanced WTI Index (from 2020-09-17); see the script docstring",
        "gate": f"per fund, |iNAV - NAV| <= {G.BP_TOL} bp on >= {G.SHARE_MIN:.0%} of days (deposit line 191)",
        "window": [G.FIRST, G.LAST], "reserved_from": G.RESERVED_FROM, "reads": reads,
        "controls": {"a_table13_worst_miss": worst13},
        "holiday_republications_dropped": [d for d in copies if G.FIRST <= d <= G.LAST],
        "deviations": ["the first run raised on its own guard: a recovered hole row was compared against "
                       "days already holding recovered rows; it now compares against the strip's days only",
                       "the post-hoc 'investigation' block per fund; the verdict is unchanged"],
        "funds": {},
    }
    win = [d for d in days if G.FIRST <= d <= G.LAST]
    for fund, L in FUNDS.items():
        navd = set(nav[nav["fund"] == fund]["date"])
        g = nav[(nav["fund"] == fund) & (nav["date"] >= G.FIRST) & (nav["date"] <= G.LAST)]
        f: dict[str, Any] = {"L": L, "calendar_check": {"nav_days_without_cl_settlement": sorted(d for d in g["date"] if d not in bd),
                                        "cl_settlement_days_without_nav": sorted(d for d in win if d not in navd)}}
        f.update(evaluate(nav, fund, L, days, bd, settles, rates, splits[fund]))
        f["investigation"] = investigate(nav, fund, L, days, bd, settles, rates, splits[fund])
        if f["investigation"]["best_era_b"] != DOC_SCHEDULE:
            raise GateError(f"{fund}: the search picked {f['investigation']['best_era_b']!r}, "
                            f"but the index's methodology states {DOC_SCHEDULE!r}")
        iv = f["investigation"]
        f["resolution_by_documented_rule"] = {
            "schedule": DOC_SCHEDULE,
            "all_days": iv["whole_window_with_best"],
            "excluding_transition": iv["whole_window_with_best_excluding_transition"],
            "roll_window_excluding_transition": iv["roll_window_with_best_excluding_transition"],
            "pass_excluding_transition": bool(iv["whole_window_with_best_excluding_transition"]["pass"]),
            "note": "the transition (2020-04-01 → 2020-09-16) is a departure by the FUNDS from their benchmark; "
                    "no index rule describes those days and the ledger cannot use them for CL",
        }
        doc["funds"][fund] = f
    doc["investigation_rule"] = INVESTIGATION
    with open(DOC_PATH, "rb") as fh:
        import hashlib
        got = hashlib.sha256(fh.read()).hexdigest()
    if got != DOC_SHA256:
        raise GateError(f"{DOC_PATH.name} sha256 {got} != recorded {DOC_SHA256}")
    doc["documented_rule"] = {"url": DOC_URL, "sha256": DOC_SHA256, "cached_at": "data/raw/bloomberg/ (gitignored)",
                              "rule": DOC_RULE, "search_winner_equals_documented_rule": True}
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise GateError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for fund, f in doc["funds"].items():
        v, x = f["verdict"], f["excluding_transition"]
        print(f"{fund}: {v['within_5bp']}/{v['days']} = {v['share']:.4f} -> {'PASS' if v['pass'] else 'FAIL'}"
              f" (median {v.get('median_abs_bp')} bp); excluding transition {x['share']:.4f}")
        for c, s in f["classes"].items():
            print(f"   {c:16s} {s['within_5bp']:5d}/{s['days']:5d} = {s['share']:.4f}  mean|err| {s.get('mean_abs_bp')}")
        print(f"   best schedule on roll-window days: {f['best_schedule_on_roll_window']}")
        print(f"   controls: sign {f['controls']['b_sign_flipped']['share']}, lag {f['controls']['c_index_lagged_one_day']['share']},"
              f" era-A index on era-B days {f['controls']['d_era_a_index_on_era_b_days']['share']}")
        iv = f["investigation"]
        print(f"   INVESTIGATION (post hoc): best era-B window {iv['best_era_b']} -> era B {iv['candidates_era_b'][iv['best_era_b']]['share']:.4f};"
              f" whole window {iv['whole_window_with_best']['share']:.4f};"
              f" excluding transition {iv['whole_window_with_best_excluding_transition']['share']:.4f};"
              f" roll window ex-transition {iv['roll_window_with_best_excluding_transition']['share']:.4f}")
        rz = f["resolution_by_documented_rule"]
        print(f"   DOCUMENTED RULE ({rz['schedule']}): all days {rz['all_days']['share']:.4f};"
              f" excluding transition {rz['excluding_transition']['share']:.4f} -> {'PASS' if rz['pass_excluding_transition'] else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
