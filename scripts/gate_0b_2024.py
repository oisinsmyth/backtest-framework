"""Gate 0b extended to 2024-01 → 2025-02 for BOIL, KOLD, UCO and SCO (AITODO 1f, amendment A6).

SPEC -- written 2026-09-24, after the principal chose the deposit's vault as the seal (A6: the
ledger's in-sample runs to 2025-02-28), and before any NAV or settlement dated 2024-01-01 or later
was read by this study. Frozen from then on.

WHY. Gate 0b was run on 2017-05-22 → 2023-12-29 (`gate_0b_ng_nav.py`, `gate_0b_cl_nav.py`). A6 adds
fourteen months to the in-sample, and the gate must hold on them too (deposit line 191). These
months are also a clean test of the rules those two runs ESTABLISHED, two of which were found
after the fact:
  * the business-day calendar drops holiday republications (found in NG's first run, declared in
    advance for CL);
  * UCO/SCO's Balanced WTI index rolls 50/50 at the BD2-3 closes (found by search in CL's run, then
    confirmed by Bloomberg's BCBCLI methodology).
Neither rule has been scored on a day after 2023-12-29. This run scores them there, unchanged.

WINDOW AND READS. NAV dates 2024-01-02 → 2025-02-28. Every panel goes through `load_panel(...,
reserved_from="2025-03-01")`, so no row inside the vault is in memory. The index is computed from
the full settlement history before the cut, because the Balanced index carries its component
weights from its 2020-09-01 reset. Only the NAV days in the window are scored.

THE GATE: per fund, |iNAV - NAV| <= 5 bp on >= 95% of window days, with missing days counted as
failures. iNAV is Gate 0b's own formula and inputs (L, ER 0.95%, the OECD USD 3-month rate at
month m-2, D calendar days), exactly as in the two earlier scripts, whose functions are reused.

THE RULES SCORED (primary, one per root, declared here):
  * NG (BOIL L=+2, KOLD L=-2): the Bloomberg Natural Gas Subindex, BCOM §2.8 schedule S0 (the funds
    trade at the BD5-9 closes), on the calendar WITHOUT holiday republications.
  * CL (UCO L=+2, SCO L=-2): the Balanced WTI index (the monthly, June and December schedules,
    reset to thirds at the close of BD1 in March and September), rolled by the DOCUMENTED rule,
    "2-day, weights from BD3", on the calendar without republications.

REPORTED BESIDE, never in place of the verdict:
  * NG on the calendar WITH republications (the 2017-2023 pre-registered calendar);
  * NG: all eleven declared schedules on roll-window days (BD4-12), best by mean |err|;
  * CL: the twenty candidate windows of CL's investigation, on all window days, best by pass share;
    and CL under S0 (the 2017-2023 pre-registered schedule);
  * day classes and failing days with their tags, by the earlier scripts' rules.
The predictions, written here before the run: NG's best schedule is S0; CL's best candidate is the
documented rule.

CONTROLS THAT MUST FIRE (each raises): (a) BCOM Table 13 reproduced; (b) flipping L's sign passes
< 0.5; (c) a one-day index lag passes < 0.5; (d, CL) the plain WTI subindex (era A's index, as if
there had been no switch) passes strictly fewer window days than the Balanced index.

WHAT THIS DOES NOT TOUCH: it reads BOIL/KOLD/UCO/SCO NAVs, NG/CL settlements and the OECD rate,
all dated before 2025-03-01. It computes no strategy return and no settlement-window price or
flow statistic, so none of H1-H15 is read. It writes `data/ledger_gate_0b_2024.json`.

    uv run python scripts/gate_0b_2024.py            # write the JSON
    uv run python scripts/gate_0b_2024.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_gate_0b_2024.json"
RESERVED_FROM = "2025-03-01"
FIRST, LAST = "2024-01-02", "2025-02-28"
#: Changes made after the first run. None so far.
DEVIATIONS: list[str] = []


class Gate2024Error(RuntimeError):
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


C = _load_mod("gate_0b_cl_nav", "scripts/gate_0b_cl_nav.py")
G = C.G
# A6: this study's cut and window. The two earlier scripts read these module constants at call time.
G.RESERVED_FROM, G.FIRST, G.LAST = RESERVED_FROM, FIRST, LAST


def _failing(rows: list[dict[str, Any]], tags: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"date": r["date"], "bd": r["bd"], "err_bp": None if r["err_bp"] is None else round(float(r["err_bp"]), 3),
             "tags": [t for t in tags if r.get(t)] + (["missing"] if r["err_bp"] is None else [])}
            for r in rows if r["err_bp"] is None or abs(float(r["err_bp"])) > G.BP_TOL]


def ng() -> dict[str, Any]:
    nav, settles, reads = G.load_inputs()
    rates = G.load_rates()
    copies = G.copy_days(settles)
    clean = {d: v for d, v in settles.items() if d not in set(copies)}
    days, bd = G.business_days(clean)
    raw_days, raw_bd = G.business_days(settles)
    sp, swapq = G.splits(), G.swap_held_quarters()
    out: dict[str, Any] = {"reads": reads, "holiday_republications_dropped": [d for d in copies if FIRST <= d <= LAST],
                           "funds": {}}
    for fund, L in G.FUNDS.items():
        split_days = {d for d, _k, _r in sp[fund]}
        g = nav[(nav["fund"] == fund) & (nav["date"] >= FIRST) & (nav["date"] <= LAST)]
        navd = set(nav[nav["fund"] == fund]["date"])
        f: dict[str, Any] = {"L": L, "calendar_check": {
            "nav_days_without_ng_settlement": sorted(d for d in g["date"] if d not in bd),
            "ng_settlement_days_without_nav": sorted(d for d in days if FIRST <= d <= LAST and d not in navd)},
            "rounding_floor": G.rounding_floor(nav, fund, sp[fund])}
        f.update(G.evaluate(nav, fund, L, clean, days, bd, rates, split_days, swapq, full=True))
        f["beside_calendar_with_republications"] = G.evaluate(nav, fund, L, settles, raw_days, raw_bd, rates,
                                                              split_days, swapq, full=False)["verdict"]
        f["prediction_best_schedule_is_s0"] = f["best_is_s0"]
        out["funds"][fund] = f
    return out


def cl() -> dict[str, Any]:
    nav, settles, reads = C.load()
    rates = G.load_rates()
    copies = G.copy_days(settles)
    settles = {d: v for d, v in settles.items() if d not in set(copies)}
    days, bd = G.business_days(settles)
    splits: dict[str, set[str]] = {f: set() for f in C.FUNDS}
    with G.SPLITS.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["Symbol"] in C.FUNDS:
                mm, dd, yy = r["Date of Split"].split("/")
                splits[r["Symbol"]].add(f"{yy}-{mm}-{dd}")
    cands = C._candidates()
    doc_sched = cands[C.DOC_SCHEDULE]
    out: dict[str, Any] = {"reads": reads, "holiday_republications_dropped": [d for d in copies if FIRST <= d <= LAST],
                           "documented_schedule": C.DOC_SCHEDULE, "funds": {}}
    tags = ("roll_window", "annual_roll", "reset_day", "calendar", "split", "swap_held")
    for fund, L in C.FUNDS.items():
        R = C.index_returns(days, bd, settles, G.s0, sched_b=doc_sched)
        rows = G.replicate(nav, fund, L, days, bd, R, rates)
        C.classify(rows, fund, splits[fund])
        g = nav[(nav["fund"] == fund) & (nav["date"] >= FIRST) & (nav["date"] <= LAST)]
        navd = set(nav[nav["fund"] == fund]["date"])
        f: dict[str, Any] = {"L": L, "calendar_check": {
            "nav_days_without_cl_settlement": sorted(d for d in g["date"] if d not in bd),
            "cl_settlement_days_without_nav": sorted(d for d in days if FIRST <= d <= LAST and d not in navd)}}
        f["verdict"] = G.summary(rows)
        f["classes"] = {c: G.summary([r for r in rows if r[c]]) for c in ("roll_window", "annual_roll", "reset_day",
                                                                          "calendar", "split")}
        f["classes"]["not_roll_window"] = G.summary([r for r in rows if not r["roll_window"]])
        f["by_business_day"] = {str(k): G.summary(sub) for k in range(1, 24)
                                if (sub := [r for r in rows if r["n_bdays"] == 1 and r["bd"] == [k]])}
        f["failing_days"] = _failing(rows, tags)
        cand = {}
        for name, sch in cands.items():
            rr = G.replicate(nav, fund, L, days, bd, C.index_returns(days, bd, settles, G.s0, sched_b=sch), rates)
            cand[name] = G.summary(rr)
        best = max(cand, key=lambda n: (cand[n]["share"], -cand[n]["mean_abs_bp"], n))
        f["candidates"] = cand
        f["best_candidate"] = best
        f["prediction_best_is_documented"] = best == C.DOC_SCHEDULE
        f["beside_s0_preregistered_2017"] = cand["S0 (declared)"]
        wrong = G.summary(G.replicate(nav, fund, -L, days, bd, R, rates))
        lagged = G.summary(G.replicate(nav, fund, L, days, bd, R, rates, lag_index=True))
        plain = G.summary(G.replicate(nav, fund, L, days, bd, C.index_returns(days, bd, settles, G.s0, force_era_a=True), rates))
        if wrong["share"] >= 0.5 or lagged["share"] >= 0.5:
            raise Gate2024Error(f"control (b)/(c) failed for {fund}: sign-flip {wrong['share']}, lag {lagged['share']}")
        if plain["within_5bp"] >= f["verdict"]["within_5bp"]:
            raise Gate2024Error(f"control (d) failed for {fund}: the plain subindex fits as well as the Balanced index")
        f["controls"] = {"b_sign_flipped": wrong, "c_index_lagged_one_day": lagged, "d_plain_wti_subindex": plain}
        out["funds"][fund] = f
    return out


def build() -> dict[str, Any]:
    worst13 = G.table13_check()
    doc: dict[str, Any] = {
        "spec": "settlement-ledger AITODO 1f / amendment A6: Gate 0b on 2024-01 → 2025-02 under the rules the "
                "2017-2023 runs established; see the script docstring",
        "gate": f"per fund, |iNAV - NAV| <= {G.BP_TOL} bp on >= {G.SHARE_MIN:.0%} of days (deposit line 191)",
        "window": [FIRST, LAST], "reserved_from": RESERVED_FROM, "deviations": DEVIATIONS,
        "controls": {"a_table13_worst_miss": worst13},
        "NG": ng(), "CL": cl(),
    }
    doc["verdicts"] = {fund: {"pass": bool(f["verdict"]["pass"]), "share": f["verdict"]["share"]}
                       for root in ("NG", "CL") for fund, f in doc[root]["funds"].items()}
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise Gate2024Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for root in ("NG", "CL"):
        for fund, f in doc[root]["funds"].items():
            v = f["verdict"]
            print(f"{fund}: {v['within_5bp']}/{v['days']} = {v['share']:.4f} -> {'PASS' if v['pass'] else 'FAIL'}"
                  f"  median {v.get('median_abs_bp')} bp, max {v.get('max_abs_bp')}, missing {v['missing']}")
            for c, s in f["classes"].items():
                print(f"   {c:16s} {s['within_5bp']:4d}/{s['days']:4d} = {s['share']:.4f}  mean|err| {s.get('mean_abs_bp')}")
            if root == "NG":
                print(f"   best schedule {f['best_schedule_on_roll_window']} (S0 predicted: {f['best_is_s0']});"
                      f" with republications {f['beside_calendar_with_republications']['share']}")
            else:
                print(f"   best candidate {f['best_candidate']} (documented predicted: {f['prediction_best_is_documented']});"
                      f" S0 {f['beside_s0_preregistered_2017']['share']}")
            print(f"   failing: {[(x['date'], x['err_bp'], x['tags']) for x in f['failing_days']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
