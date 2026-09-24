"""UNG's roll days in 2017-2019, from its month-end NAV per share (AITODO 1e, the optional check).

SPEC -- written 2026-09-24, the principal's instruction ("run that optional check"), before any
monthly NAV return was compared with any benchmark return, and frozen from then on.

THE QUESTION. `check_uscf_months_and_rolls.py` proved UNG's roll days for 2020-2023 against USCF's
official roll calendar, and matched its held months at 27 of 27 quarter-ends. For 2017-2019 there
is no calendar, and Part 2 of that script could not identify the roll days from MARKET closes (the
4 p.m. close and the premium swamp a few basis points). The month-end NAV per share from UNG's Rule
4.22 statements (`data/fund_facts/uscf_monthly_statements.csv`, 84 month-ends, exact) is struck at
the settlement, so a month's NAV return carries the roll's timing without the premium.

THE TEST. For each month m with both month-ends in the panel:
  * r_nav = (NPS_m * k_m) / NPS_{m-1} - 1, where k_m is the reverse-split factor between the two
    statements (1 except UNG 2017-12, k = 1/4 on the panel's basis: the December 2017 statement is
    restated for the 1-for-4 split, and the panel's gate G2 lists it as the one exception).
  * r_s = the compounded benchmark return over the NG business days after the last business day of
    m-1 through the last business day of m, under schedule s. The eleven schedules are
    `check_uscf_months_and_rolls.SCHEDULES` (the documented four-day 25% roll from D0 = E - 14
    calendar days; that window shifted by -3..+3 business days; single-day rolls at the close of
    D0+0..D0+3), with its business days (holiday republications dropped, the 2020 holes filled).
  * accrual_m = y * days_m / 360, y the OECD USD 3-month rate at month m-2 (Gate 0b's rule),
    days_m the calendar days between the two month-ends.
  * err_s,m = r_nav - r_s - accrual_m - c_s, where c_s is the median of (r_nav - r_s - accrual_m)
    over the window's months for schedule s. c_s absorbs the expense ratio and brokerage, which the
    panel does not carry; each schedule gets its own constant, so none is favoured.

SCORING, per window: mean |err| over months. The documented schedule is IDENTIFIED if it has the
lowest mean |err| AND, month by month, beats the best alternative in more months than it loses (a
one-sided sign test, p < 0.05). Ties (equal |err| to 0.001 bp) count for neither.

WINDOWS.
  * KNOWN ANSWER, which must fire first: 2020-01 -> 2022-12 (36 months). The official calendar
    proves the documented schedule there, and UNG is proven futures-only through 2022-Q4. If the
    documented schedule is NOT identified here, monthly NAV has no power to identify roll days,
    and the 2017-2019 result is reported as "no power", not as a verdict.
  * TEST: 2017-02 -> 2019-12 (35 months, every month whose two month-ends are in the panel).
    UNG is proven futures-only throughout.
Controls that must fire (both windows): the documented schedule on the WRONG pair (next -> the
month after) must score a higher mean |err| than the documented pair; and the documented schedule
with r_nav taken from the PREVIOUS month must score a higher mean |err|.

WHAT THIS DOES NOT TOUCH: it reads the monthly statement panel, the NG settlement strip through
`load_panel(reserved_from="2024-01-01")`, the 2020 hole fill and the OECD rates, all before
2024-01-01. It computes no strategy return and no settlement-window statistic, and writes
`data/ledger_ung_monthly_rolls_check.json`.

    uv run python scripts/check_ung_monthly_rolls.py            # write the JSON
    uv run python scripts/check_ung_monthly_rolls.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_ung_monthly_rolls_check.json"
PANEL = REPO / "data" / "fund_facts" / "uscf_monthly_statements.csv"
RESERVED_FROM = "2024-01-01"
WINDOWS = {"known_answer": ("2020-01", "2022-12"), "test": ("2017-02", "2019-12")}
#: reverse splits between consecutive statements, on the panel's basis (its gate G2's exception list)
SPLIT_K = {"2017-12": 0.25, "2023-12": 0.25}
TIE_BP = 0.001
#: Changes made after the first run (spec sha256 3de5c0ab..., 2026-09-24T12:56Z). None touches a window.
DEVIATIONS = ["2023-12 added to SPLIT_K: the first run's split guard raised on UNG's December 2023 statement, "
              "restated for the 1-for-4 split of 2024-01 (the panel's G2 lists it). The month is outside both "
              "windows; the docstring named only 2017-12."]


class MonthlyRollError(RuntimeError):
    pass


def _load_mod(name: str, rel: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


U = _load_mod("check_uscf_months_and_rolls", "scripts/check_uscf_months_and_rolls.py")
G = U.G


def month_ends(exact: bool = False) -> dict[str, float]:
    """NAV per share as printed (to the cent), or with `exact` (post hoc) total NAV / shares."""
    with PANEL.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["fund"] == "UNG"]
    out = {r["month_end"][:7]: (int(r["nav_usd"]) / int(r["shares"]) if exact else float(r["nav_per_share"]))
           for r in rows}
    if any(m >= RESERVED_FROM[:7] for m in out):
        raise MonthlyRollError("a statement on or after the seal is in memory")
    return out


def nav_returns(nps: dict[str, float]) -> dict[str, float]:
    out = {}
    months = sorted(nps)
    for a, b in zip(months, months[1:]):
        if G._month_minus(b, 1) != a:
            raise MonthlyRollError(f"panel gap between {a} and {b}")
        ratio = nps[b] * SPLIT_K.get(b, 1.0) / nps[a]
        if not 0.4 < ratio < 2.5:
            raise MonthlyRollError(f"{b}: month return {ratio - 1:+.3f} looks like an undeclared split")
        out[b] = ratio - 1
    for b in SPLIT_K:  # a declared split must be one: unadjusted, the ratio is far outside the bound
        a = G._month_minus(b, 1)
        if 0.4 < nps[b] / nps[a] < 2.5:
            raise MonthlyRollError(f"{b}: the declared split is not visible in the raw NAV per share")
    return out


def last_bday(bdays: list[str], ym: str) -> str:
    i = bisect.bisect_left(bdays, G._month_minus(ym, -1) + "-01")
    return bdays[i - 1]


def month_bench(bdays: list[str], R: dict[str, float | None], ym: str) -> float | None:
    a, b = last_bday(bdays, G._month_minus(ym, 1)), last_bday(bdays, ym)
    rb = 1.0
    for d in bdays[bisect.bisect_right(bdays, a): bisect.bisect_right(bdays, b)]:
        v = R.get(d)
        if v is None:
            return None
        rb *= v
    return rb - 1


def accrual(rates: dict[str, float], ym: str) -> float:
    prev = G._month_minus(ym, 1)
    y0, m0 = int(prev[:4]), int(prev[5:7])
    y1, m1 = int(ym[:4]), int(ym[5:7])
    end0 = dt.date(y0 + m0 // 12, m0 % 12 + 1, 1) - dt.timedelta(days=1)
    end1 = dt.date(y1 + m1 // 12, m1 % 12 + 1, 1) - dt.timedelta(days=1)
    return float(rates[G._month_minus(ym, 2)] * (end1 - end0).days / 360.0)


def score(months: list[str], rnav: dict[str, float], bench: dict[str, float | None],
          acc: dict[str, float]) -> tuple[dict[str, float], dict[str, Any]]:
    raw = {m: rnav[m] - bench[m] - acc[m] for m in months if bench.get(m) is not None}  # type: ignore[operator]
    if len(raw) != len(months):
        raise MonthlyRollError(f"benchmark missing for {sorted(set(months) - set(raw))}")
    c = float(np.median(list(raw.values())))
    err = {m: (v - c) * 1e4 for m, v in raw.items()}
    ae = [abs(v) for v in err.values()]
    return err, {"months": len(err), "constant_bp_per_month": round(c * 1e4, 4),
                 "mean_abs_err_bp": round(float(np.mean(ae)), 4), "median_abs_err_bp": round(float(np.median(ae)), 4)}


def window(lo: str, hi: str, rnav: dict[str, float], benches: dict[str, dict[str, float | None]],
           wrong: dict[str, float | None], acc: dict[str, float]) -> dict[str, Any]:
    months = [m for m in sorted(rnav) if lo <= m <= hi]
    errs, res = {}, {}
    for name, bench in benches.items():
        errs[name], res[name] = score(months, rnav, bench, acc)
    best = min(res, key=lambda n: (res[n]["mean_abs_err_bp"], n))
    best_alt = min((n for n in res if n != "documented"), key=lambda n: (res[n]["mean_abs_err_bp"], n))
    wins = losses = 0
    for m in months:
        a, b = abs(errs["documented"][m]), abs(errs[best_alt][m])
        if abs(a - b) <= TIE_BP:
            continue
        wins += a < b
        losses += a > b
    n = wins + losses
    p = sum(math.comb(n, k) for k in range(wins, n + 1)) / 2 ** n if n else 1.0
    _e, wrong_pair = score(months, rnav, wrong, acc)
    prev_nav = {m: rnav[G._month_minus(m, 1)] for m in months if G._month_minus(m, 1) in rnav}
    lag_months = [m for m in months if m in prev_nav]
    _e2, lagged = score(lag_months, prev_nav, benches["documented"], acc)
    doc = res["documented"]["mean_abs_err_bp"]
    controls = {"wrong_pair_mean_abs_err_bp": wrong_pair["mean_abs_err_bp"],
                "previous_month_nav_mean_abs_err_bp": lagged["mean_abs_err_bp"],
                "wrong_pair_fires": wrong_pair["mean_abs_err_bp"] > doc,
                "previous_month_fires": lagged["mean_abs_err_bp"] > doc}
    return {"months": [months[0], months[-1], len(months)], "schedules": res, "best": best,
            "best_alternative": best_alt, "documented_is_best": best == "documented",
            "sign_test_vs_best_alternative": {"months_won": wins, "months_lost": losses, "p_one_sided": round(p, 6)},
            "identified": bool(best == "documented" and p < 0.05), "controls": controls,
            "documented_monthly_err_bp": {m: round(v, 3) for m, v in errs["documented"].items()}}


def build() -> dict[str, Any]:
    st = U.settlements("NG")
    bdays = sorted(st)
    U._BDAYS = bdays
    rolls = U.roll_calendar("NG", bdays)
    benches: dict[str, dict[str, float | None]] = {}
    rnav = nav_returns(month_ends())
    months = sorted(rnav)
    for name, (kind, param) in U.SCHEDULES.items():
        R = U.bench_returns(bdays, st, rolls, U.weight_fn(kind, param))
        benches[name] = {m: month_bench(bdays, R, m) for m in months}
    Rw = U.bench_returns(bdays, st, rolls, U.weight_fn("doc", 0), wrong_pair=True)
    wrong = {m: month_bench(bdays, Rw, m) for m in months}
    rates = G.load_rates()
    acc = {m: accrual(rates, m) for m in months}
    doc: dict[str, Any] = {"spec": "settlement-ledger AITODO 1e, optional: UNG's 2017-2019 roll days from its "
                                   "month-end NAV per share; see the script docstring",
                           "reserved_from": RESERVED_FROM, "deviations": DEVIATIONS, "windows": {}}
    for w, (lo, hi) in WINDOWS.items():
        doc["windows"][w] = window(lo, hi, rnav, benches, wrong, acc)
    ka, te = doc["windows"]["known_answer"], doc["windows"]["test"]
    fired = all(ka["controls"][k] for k in ("wrong_pair_fires", "previous_month_fires"))
    if not ka["identified"] or not fired:
        verdict = "NO POWER: the known-answer window does not identify the documented schedule"
    elif te["identified"]:
        verdict = "PROVEN 2017-2019: the documented schedule is identified from month-end NAV"
    else:
        verdict = "NOT IDENTIFIED 2017-2019, although the method identifies 2020-2022"
    doc["verdict"] = verdict
    # POST HOC, 2026-09-24, after the verdict: the printed NAV per share is rounded to the cent (about
    # +/-8 bp an endpoint at $6), so the same test on total NAV / shares. Reported beside, never in place.
    rx = nav_returns(month_ends(exact=True))
    doc["post_hoc_exact_nav_per_share"] = {
        w: {k: v for k, v in window(lo, hi, rx, benches, wrong, acc).items() if k != "documented_monthly_err_bp"}
        for w, (lo, hi) in WINDOWS.items()}
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise MonthlyRollError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for w, r in doc["windows"].items():
        print(f"{w} {r['months']}: best {r['best']}; identified {r['identified']}; "
              f"sign {r['sign_test_vs_best_alternative']}; controls {r['controls']}")
        for n, s in sorted(r["schedules"].items(), key=lambda kv: kv[1]["mean_abs_err_bp"]):
            print(f"   {n:32s} mean|err| {s['mean_abs_err_bp']:8.3f} bp  median {s['median_abs_err_bp']:7.3f}"
                  f"  c {s['constant_bp_per_month']:7.2f}")
    print("VERDICT:", doc["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
