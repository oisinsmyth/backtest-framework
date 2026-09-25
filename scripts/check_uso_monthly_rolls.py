"""USO's roll days, 2017-02 -> 2020-03, from its month-end NAV (settlement-ledger gap G19).

SPEC -- written 2026-09-25 on the principal's brief, before any USO monthly NAV return was compared
with any benchmark return, and frozen from then on. Its sha256 is SPEC_SHA256 below; the script
refuses to run if this text changes.

THE QUESTION. Did USO roll its CL position on its documented four-day schedule (25% a day, over the
four business days after D0 = E - 14 calendar days, E the near contract's last trading day) in the
months 2017-02 -> 2020-03? `check_uscf_months_and_rolls.py` proves the rule only for 2020 (USCF's
official calendar starts then) and could not identify it from market closes (its Part 2). This is
the USO twin of `check_ung_monthly_rolls.py`, which identified UNG's 2017-2019 schedule from
month-end NAV.

THE TEST WINDOW. USO months 2017-02 -> 2020-03 (38 months): every month whose two month-ends are in
`data/fund_facts/uscf_monthly_statements.csv` and fall before the first allocation change in
`data/fund_facts/uso_allocation_notices.csv` (effective 2020-04-17). The window is derived from those
two files, and the script raises unless it equals the declared one.

THE RETURN. PRIMARY, declared in advance (the UNG check's post-hoc lesson: the printed NAV per share
is rounded to the cent, about +/-4 bp an endpoint at $12 and +/-12 bp at $4.24): the EXACT NAV per
share, total net assets (`nav_usd`) / shares outstanding (`shares`), so
r_nav = (NPS_m * k_m) / NPS_{m-1} - 1. The same test on the PRINTED NAV per share (`nav_per_share`)
is reported beside it, never in its place; the verdict reads only the primary.

SPLITS. None in the window. USO's 1-for-8 reverse split falls in 2020-04 (k = 1/8 on the panel's
basis: April's statement is post-split, March's is not). It is declared and asserted anyway, as
UNG's is: an undeclared month-on-month ratio outside (0.4, 2.5) raises, and a declared split that is
not visible in the raw NAV per share raises.

THE BENCHMARK, per schedule s: r_s = the compounded CL benchmark return over the CL business days
after the last business day of m-1 through the last business day of m, built by
`check_uscf_months_and_rolls` (`settlements("CL")`, `roll_calendar("CL", ...)` with CL's last-trade
rule, `bench_returns`, `weight_fn`). The eleven schedules are its `SCHEDULES`, applied to CL: the
documented one; that four-day window shifted by -3, -2, -1, +1, +2, +3 business days; single-day
rolls at the close of D0+0, D0+1, D0+2, D0+3.

THE ACCRUAL. accrual_m = y * days_m / 360, y the OECD USD 3-month rate at month m-2 (Gate 0b's rule,
as UNG's), days_m the calendar days between the two month-ends.

THE ERROR. err_s,m = r_nav - r_s - accrual_m - c_s, where c_s is the median of (r_nav - r_s -
accrual_m) over the window's months: one constant per schedule, so none is favoured. It absorbs the
expense ratio and brokerage, which the panel does not carry.

IDENTIFIED iff the documented schedule has the lowest mean |err| over the window AND, month by month,
beats the best alternative (the lowest mean |err| among the other ten) in a one-sided sign test at
p < 0.05. Ties (|err| equal to within 0.001 bp) count for neither side.

CONTROLS that must fire, in the USO window: (a) the documented schedule on the WRONG contract pair
(next -> the month after) must score a higher mean |err| than the documented schedule on the right
pair; (b) the documented schedule scored against the PREVIOUS month's r_nav must score a higher mean
|err|. The verdict is PROVEN only if the documented schedule is IDENTIFIED and both controls fire;
IDENTIFIED with a control that does not fire is VOID; anything else is NOT IDENTIFIED.

THE KNOWN ANSWER, which must pass before any USO verdict is written. USO's only official-calendar
months before its change are 2020-01..03, too few, so the SAME functions run on UNG (root NG) over
2020-01 -> 2022-12, where USCF's calendar proves the documented schedule. On the primary return the
documented schedule must be IDENTIFIED and both controls must fire, or the script RAISES: monthly NAV
would then have no power, and no USO verdict is written. The re-run must also reproduce, value for
value, the known-answer numbers already in `data/ledger_ung_monthly_rolls_check.json` (printed ->
its `windows.known_answer`; exact -> its `post_hoc_exact_nav_per_share.known_answer`), or it raises:
the shared code must be the code that produced that ledger.

REPORTED ONLY: USO's rolls in 2020-01..03 against USCF's official calendar
(`data/raw/uscf/uscf-rolldates-commodities-2020.csv`): Roll Begin = D0 and Roll End = the third
business day after D0.

WHAT THIS DOES NOT TOUCH. The settlement strips are read through
`load_panel(reserved_from="2024-01-01")` (inside `check_uscf_months_and_rolls.settlements`). The
monthly statement panel, the allocation notices and the OECD rates are not catalogued panels, so they
are read directly and cut and asserted before 2024-01-01. It computes no strategy return and writes
only `data/ledger_uso_monthly_rolls_check.json`.

    uv run python -W error::RuntimeWarning scripts/check_uso_monthly_rolls.py              # write the JSON
    uv run python -W error::RuntimeWarning scripts/check_uso_monthly_rolls.py --check      # rebuild, compare byte for byte
    uv run python -W error::RuntimeWarning scripts/check_uso_monthly_rolls.py --selftest   # every gate raises on a break
"""
from __future__ import annotations

import argparse
import bisect
import copy
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_uso_monthly_rolls_check.json"
PANEL = REPO / "data" / "fund_facts" / "uscf_monthly_statements.csv"
NOTICES = REPO / "data" / "fund_facts" / "uso_allocation_notices.csv"
UNG_LEDGER = REPO / "data" / "ledger_ung_monthly_rolls_check.json"
RESERVED_FROM = "2024-01-01"
FUNDS: dict[str, dict[str, Any]] = {
    "USO": {"root": "CL", "split_k": {"2020-04": 0.125}},
    #: UNG's own declaration (check_ung_monthly_rolls.SPLIT_K, with its deviation)
    "UNG": {"root": "NG", "split_k": {"2017-12": 0.25, "2023-12": 0.25}},
}
USO_WINDOW = ("2017-02", "2020-03")
UNG_KNOWN_ANSWER = ("2020-01", "2022-12")
OFFICIAL_MONTHS = ("2020-01", "2020-03")
TIE_BP = 0.001
SPEC_SHA256 = "18f9e8558338d466effb29a204f2235a0d6be885514b8dde20d680ef750ffd90"
#: Spec sha256 18f9e855..., computed 2026-09-25T07:58Z, before the first run. Changes made after the first run:
DEVIATIONS: list[str] = []

Bench = dict[str, float | None]


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


# ------------------------------------------------------------------ gates on the spec and the inputs
def spec_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_spec(text: str | None) -> str:
    h = spec_sha256(text or "")
    if h != SPEC_SHA256:
        raise MonthlyRollError(f"the spec docstring hashes to {h}, not the frozen {SPEC_SHA256}")
    return h


def statement_rows(fund: str, extra: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    with PANEL.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["fund"] == fund and r["month_end"] < RESERVED_FROM]
    rows += extra or []
    if any(r["month_end"] >= RESERVED_FROM for r in rows):
        raise MonthlyRollError("a statement on or after the seal is in memory")
    return rows


def month_ends(rows: list[dict[str, str]], exact: bool) -> dict[str, float]:
    """NAV per share: exact (total NAV / shares) or as printed (to the cent)."""
    return {r["month_end"][:7]: (int(r["nav_usd"]) / int(r["shares"]) if exact else float(r["nav_per_share"]))
            for r in rows}


def nav_returns(nps: dict[str, float], split_k: dict[str, float]) -> dict[str, float]:
    out = {}
    months = sorted(nps)
    for a, b in zip(months, months[1:]):
        if G._month_minus(b, 1) != a:
            raise MonthlyRollError(f"panel gap between {a} and {b}")
        ratio = nps[b] * split_k.get(b, 1.0) / nps[a]
        if not 0.4 < ratio < 2.5:
            raise MonthlyRollError(f"{b}: month return {ratio - 1:+.3f} looks like an undeclared split")
        out[b] = ratio - 1
    for b in split_k:  # a declared split must be one: unadjusted, the ratio is far outside the bound
        a = G._month_minus(b, 1)
        if 0.4 < nps[b] / nps[a] < 2.5:
            raise MonthlyRollError(f"{b}: the declared split is not visible in the raw NAV per share")
    return out


def allocation_change() -> str:
    """The first effective date whose allocation differs from the documented (first) row's."""
    with NOTICES.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return min(r["effective"] for r in rows[1:] if r["allocation"] != rows[0]["allocation"])


def derive_window(rows: list[dict[str, str]], change: str, declared: tuple[str, str]) -> tuple[str, str]:
    end = {r["month_end"][:7]: r["month_end"] for r in rows}
    months = [m for m in sorted(end) if G._month_minus(m, 1) in end
              and end[G._month_minus(m, 1)] < change and end[m] < change]
    derived = (months[0], months[-1])
    if derived != declared or len(months) != len(set(months)):
        raise MonthlyRollError(f"the window derived from the panel and the notices is {derived}, "
                               f"not the declared {declared}")
    return derived


# ------------------------------------------------------------------ the scoring (UNG's, generalised)
def last_bday(bdays: list[str], ym: str) -> str:
    i = bisect.bisect_left(bdays, G._month_minus(ym, -1) + "-01")
    return bdays[i - 1]


def month_bench(bdays: list[str], R: Bench, ym: str) -> float | None:
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


def score(months: list[str], rnav: dict[str, float], bench: Bench,
          acc: dict[str, float]) -> tuple[dict[str, float], dict[str, Any]]:
    raw: dict[str, float] = {}
    for m in months:
        b = bench.get(m)
        if b is not None:
            raw[m] = rnav[m] - b - acc[m]
    if len(raw) != len(months):
        raise MonthlyRollError(f"benchmark missing for {sorted(set(months) - set(raw))}")
    c = float(np.median(list(raw.values())))
    err = {m: (v - c) * 1e4 for m, v in raw.items()}
    ae = [abs(v) for v in err.values()]
    return err, {"months": len(err), "constant_bp_per_month": round(c * 1e4, 4),
                 "mean_abs_err_bp": round(float(np.mean(ae)), 4), "median_abs_err_bp": round(float(np.median(ae)), 4)}


def window(lo: str, hi: str, rnav: dict[str, float], benches: dict[str, Bench], wrong: Bench,
           acc: dict[str, float]) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
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
    out = {"months": [months[0], months[-1], len(months)], "schedules": res, "best": best,
           "best_alternative": best_alt, "documented_is_best": best == "documented",
           "sign_test_vs_best_alternative": {"months_won": wins, "months_lost": losses, "p_one_sided": round(p, 6)},
           "identified": bool(best == "documented" and p < 0.05), "controls": controls,
           "documented_monthly_err_bp": {m: round(v, 3) for m, v in errs["documented"].items()}}
    return out, errs


def controls_fire(res: dict[str, Any]) -> bool:
    return bool(res["controls"]["wrong_pair_fires"] and res["controls"]["previous_month_fires"])


# ------------------------------------------------------------------ the known answer's two gates
def known_answer_gate(res: dict[str, Any]) -> None:
    if not res["identified"]:
        raise MonthlyRollError(f"KNOWN ANSWER FAILED: the documented schedule is not identified on UNG "
                               f"{res['months']} (best {res['best']}, sign {res['sign_test_vs_best_alternative']});"
                               " monthly NAV has no power and no USO verdict is written")
    if not controls_fire(res):
        raise MonthlyRollError(f"KNOWN ANSWER FAILED: a control did not fire on UNG: {res['controls']}")


def _json(x: Any) -> Any:
    return json.loads(json.dumps(x, sort_keys=True))


def reproduce_gate(printed: dict[str, Any], exact: dict[str, Any], ledger: dict[str, Any]) -> None:
    want_p = ledger["windows"]["known_answer"]
    want_x = ledger["post_hoc_exact_nav_per_share"]["known_answer"]
    got_x = {k: v for k, v in exact.items() if k != "documented_monthly_err_bp"}
    for label, got, want in (("printed", printed, want_p), ("exact", got_x, want_x)):
        if _json(got) != want:
            diff = sorted(k for k in set(want) | set(_json(got)) if _json(got).get(k) != want.get(k))
            raise MonthlyRollError(f"the UNG re-run ({label}) does not reproduce "
                                   f"{UNG_LEDGER.name}'s known-answer numbers; keys differing: {diff}")


def right_quantity_gate(primary: dict[str, float], printed: dict[str, float], months: list[str]) -> int:
    n = sum(primary[m] != printed[m] for m in months)
    if n == 0:
        raise MonthlyRollError("the primary (exact) returns equal the printed ones in every month; "
                               "the scored quantity is not the declared one")
    return n


# ------------------------------------------------------------------ inputs per fund
def fund_inputs(fund: str) -> dict[str, Any]:
    root = FUNDS[fund]["root"]
    st = U.settlements(root)
    bdays = sorted(st)
    U._BDAYS = bdays
    rolls = U.roll_calendar(root, bdays)
    rows = statement_rows(fund)
    rx = nav_returns(month_ends(rows, exact=True), FUNDS[fund]["split_k"])
    rp = nav_returns(month_ends(rows, exact=False), FUNDS[fund]["split_k"])
    if sorted(rx) != sorted(rp):
        raise MonthlyRollError(f"{fund}: exact and printed return months differ")
    months = sorted(rx)
    benches: dict[str, Bench] = {}
    for name, (kind, param) in U.SCHEDULES.items():
        R = U.bench_returns(bdays, st, rolls, U.weight_fn(kind, param))
        benches[name] = {m: month_bench(bdays, R, m) for m in months}
    Rw = U.bench_returns(bdays, st, rolls, U.weight_fn("doc", 0), wrong_pair=True)
    wrong = {m: month_bench(bdays, Rw, m) for m in months}
    rates = G.load_rates()
    acc = {m: accrual(rates, m) for m in months}
    return {"root": root, "bdays": bdays, "rolls": rolls, "rows": rows, "exact": rx, "printed": rp,
            "benches": benches, "wrong": wrong, "acc": acc}


def official_2020(bdays: list[str], rolls: list[dict[str, Any]]) -> dict[str, Any]:
    lo, hi = OFFICIAL_MONTHS
    rows = set()
    with (U.ROLLCAL / "uscf-rolldates-commodities-2020.csv").open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.reader(fh):
            if len(r) >= 3 and r[0] == "USO":
                rows.add((U._d(r[1]), U._d(r[2])))
    out = []
    for begin, end in sorted(rows):
        if not lo <= begin[:7] <= hi:
            continue
        hit = [x for x in rolls if x["D0"][:7] == begin[:7]]
        pred = [hit[0]["D0"], bdays[hit[0]["i0"] + 3]] if hit else None
        out.append({"month": begin[:7], "official": [begin, end], "predicted": pred, "match": [begin, end] == pred})
    return {"reported_only": True, "months": len(out), "matched": sum(o["match"] for o in out), "rows": out}


def _file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ build
def build() -> dict[str, Any]:
    spec_h = check_spec(__doc__)
    # THE KNOWN ANSWER FIRST: the same functions on UNG 2020-2022
    ung = fund_inputs("UNG")
    klo, khi = UNG_KNOWN_ANSWER
    ka_x, _ = window(klo, khi, ung["exact"], ung["benches"], ung["wrong"], ung["acc"])
    ka_p, _ = window(klo, khi, ung["printed"], ung["benches"], ung["wrong"], ung["acc"])
    known_answer_gate(ka_x)
    reproduce_gate(ka_p, ka_x, json.loads(UNG_LEDGER.read_text(encoding="utf-8")))

    # THE TEST: USO 2017-02 -> 2020-03
    uso = fund_inputs("USO")
    change = allocation_change()
    lo, hi = derive_window(uso["rows"], change, USO_WINDOW)
    months = [m for m in sorted(uso["exact"]) if lo <= m <= hi]
    n_diff = right_quantity_gate(uso["exact"], uso["printed"], months)
    te, errs = window(lo, hi, uso["exact"], uso["benches"], uso["wrong"], uso["acc"])
    tp, _ = window(lo, hi, uso["printed"], uso["benches"], uso["wrong"], uso["acc"])
    te["best_alternative_monthly_err_bp"] = {m: round(v, 3) for m, v in errs[te["best_alternative"]].items()}
    if te["identified"] and controls_fire(te):
        verdict = (f"PROVEN {lo} -> {hi}: USO's documented four-day roll is identified from its month-end "
                   "NAV (exact NAV / shares), and both controls fire")
    elif te["identified"]:
        verdict = f"VOID {lo} -> {hi}: identified, but a control did not fire: {te['controls']}"
    else:
        verdict = (f"NOT IDENTIFIED {lo} -> {hi}, although the same code identifies UNG's documented "
                   f"schedule over {klo} -> {khi}")
    return {
        "spec": "settlement-ledger gap G19: USO's 2017-02 -> 2020-03 roll days from its month-end NAV; "
                "see the script docstring",
        "spec_sha256": spec_h, "reserved_from": RESERVED_FROM, "deviations": DEVIATIONS,
        "inputs_sha256": {"uscf_monthly_statements.csv": _file_sha(PANEL),
                          "uso_allocation_notices.csv": _file_sha(NOTICES),
                          UNG_LEDGER.name: _file_sha(UNG_LEDGER)},
        "known_answer_ung": {"root": "NG", "window": [klo, khi], "primary_exact_nav_per_share": ka_x,
                             "printed_nav_per_share": {k: v for k, v in ka_p.items() if k != "documented_monthly_err_bp"},
                             "identified_and_controls_fire": True,
                             "reproduces_ung_ledger_known_answer": True},
        "uso": {"root": "CL", "allocation_change_effective": change, "window": [lo, hi],
                "months_where_exact_and_printed_returns_differ": n_diff,
                "primary_exact_nav_per_share": te,
                "printed_nav_per_share": {k: v for k, v in tp.items() if k != "documented_monthly_err_bp"},
                "official_calendar_2020_01_03": official_2020(uso["bdays"], uso["rolls"])},
        "verdict": verdict,
    }


# ------------------------------------------------------------------ selftest: every gate raises on a break
def _expect_raise(label: str, fn: Any) -> str:
    try:
        fn()
    except MonthlyRollError as e:
        return f"[selftest] {label}: raised ({str(e)[:90]})"
    raise AssertionError(f"selftest: the gate '{label}' did not raise on its deliberate break")


def selftest() -> int:
    doc = build()  # the clean case: every gate passes on the real inputs
    print(f"[selftest] clean build passes; verdict: {doc['verdict'][:60]}...")
    ung = fund_inputs("UNG")
    uso = fund_inputs("USO")
    klo, khi = UNG_KNOWN_ANSWER
    lines = [
        _expect_raise("spec hash", lambda: check_spec((__doc__ or "") + " ")),
        _expect_raise("seal", lambda: statement_rows("USO", [{**uso["rows"][-1], "month_end": "2024-01-31"}])),
        _expect_raise("undeclared split", lambda: nav_returns(month_ends(uso["rows"], True), {})),
        _expect_raise("declared split not visible",
                      lambda: nav_returns(month_ends(uso["rows"], True), {"2020-04": 0.125, "2019-06": 0.5})),
        _expect_raise("panel gap", lambda: nav_returns(
            {m: v for m, v in month_ends(uso["rows"], True).items() if m != "2018-05"}, {"2020-04": 0.125})),
        _expect_raise("benchmark missing", lambda: score(
            ["2018-05"], uso["exact"], {"2018-05": None}, uso["acc"])),
        _expect_raise("window derivation", lambda: derive_window(uso["rows"], allocation_change(), ("2017-02", "2020-04"))),
        _expect_raise("right quantity", lambda: right_quantity_gate(uso["printed"], uso["printed"], sorted(uso["printed"]))),
    ]
    # the known-answer gate: swap the documented and the +3-shifted benchmarks, so the label is wrong
    swapped = dict(ung["benches"])
    swapped["documented"], swapped["documented shifted +3"] = swapped["documented shifted +3"], swapped["documented"]
    bad, _ = window(klo, khi, ung["exact"], swapped, ung["wrong"], ung["acc"])
    lines.append(_expect_raise("known answer not identified", lambda: known_answer_gate(bad)))
    # the control gate: the wrong pair replaced by the documented pair cannot score higher
    nof, _ = window(klo, khi, ung["exact"], ung["benches"], ung["benches"]["documented"], ung["acc"])
    lines.append(_expect_raise("known-answer control did not fire", lambda: known_answer_gate(nof)))
    # the reproduction gate: perturb one value in the ledger read
    ka_x, _ = window(klo, khi, ung["exact"], ung["benches"], ung["wrong"], ung["acc"])
    ka_p, _ = window(klo, khi, ung["printed"], ung["benches"], ung["wrong"], ung["acc"])
    led = json.loads(UNG_LEDGER.read_text(encoding="utf-8"))
    reproduce_gate(ka_p, ka_x, led)
    led2 = copy.deepcopy(led)
    led2["post_hoc_exact_nav_per_share"]["known_answer"]["schedules"]["documented"]["mean_abs_err_bp"] += 1e-4
    lines.append(_expect_raise("UNG ledger reproduction", lambda: reproduce_gate(ka_p, ka_x, led2)))
    # --check: a changed byte must fail
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    _compare(text, text)
    lines.append(_expect_raise("--check byte for byte", lambda: _compare(text[:-1] + " \n", text)))
    print("\n".join(lines))
    print(f"[selftest] {len(lines)} gates raise on their breaks; the clean case passes")
    return 0


def _compare(new: str, old: str) -> None:
    if new != old:
        raise MonthlyRollError(f"{OUT.name} does not reproduce")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        _compare(text, OUT.read_text(encoding="utf-8"))
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    ka = doc["known_answer_ung"]["primary_exact_nav_per_share"]
    print(f"KNOWN ANSWER UNG {ka['months']}: identified {ka['identified']}; sign {ka['sign_test_vs_best_alternative']}; "
          f"controls {ka['controls']}")
    u = doc["uso"]
    for label in ("primary_exact_nav_per_share", "printed_nav_per_share"):
        r = u[label]
        print(f"USO {label} {r['months']}: best {r['best']}; identified {r['identified']}; "
              f"sign {r['sign_test_vs_best_alternative']}; controls {r['controls']}")
        for n, s in sorted(r["schedules"].items(), key=lambda kv: kv[1]["mean_abs_err_bp"]):
            print(f"   {n:32s} mean|err| {s['mean_abs_err_bp']:8.3f} bp  median {s['median_abs_err_bp']:7.3f}"
                  f"  c {s['constant_bp_per_month']:7.2f}")
    oc = u["official_calendar_2020_01_03"]
    print(f"USO official calendar 2020-01..03 (reported only): {oc['matched']}/{oc['months']}")
    print("VERDICT:", doc["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
