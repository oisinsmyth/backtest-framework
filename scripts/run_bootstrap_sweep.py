"""D230 — every delta this programme reported, through the test it said it ran.

D217 and D218 both write hurdle A as ">= +0.10 Sharpe, above the paired
bootstrap's p95" and NEITHER RUNNER EVER COMPUTED THE SECOND LEG. D229 built the
bootstrap and found D218's headline fails it. This sweeps all 24 ladder deltas.

SPENDS NO LOOKS. No new strategy configuration is evaluated -- every cell here is
already in the ledger from D217, D218 or D229. A confidence interval around a
published estimate conditions on nothing new.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = _load("d217_ladder", "run_macd_ladder.py")
I = _load("d218_impulse", "run_impulse_macd.py")
J = _load("d229_jerk", "run_jerk_rung.py")

SUMMARY = REPO / "data" / "bootstrap_sweep_summary.json"
RESULTS = REPO / "BOOTSTRAP_SWEEP_RESULTS.md"

DELTA_HURDLE = L.DELTA_HURDLE  # +0.10
REPRO_TOL = 1e-9

BOOKS = (("long_short", True), ("long_flat", False))
GATES = (("none", False), ("200ma", True))

# Every delta the programme has reported, with the artifact field each point
# estimate must reproduce. The field names are the audit: if a name here does not
# exist in the committed summary, the delta being swept is not the delta that was
# reported and the sweep says so rather than quietly scoring something else.
DELTAS = (
    ("D217", "R1 - R2", "signal_line", "zero_line", "signal_minus_zero"),
    ("D217", "R2 - R3", "zero_line", "momentum", "zero_minus_momentum"),
    ("D218", "I1 - I2", "I1_signal", "I2_band", "signal_minus_band"),
    ("D218", "I2 - I3", "I2_band", "I3_no_deadzone", "band_minus_no_deadzone"),
    ("D218", "I1 - C", "I1_signal", "C_macd_signal", "impulse_minus_control"),
    ("D229", "I0 - I1", "I0_jerk", "I1_signal", None),
)


def _series(panel, position: np.ndarray, start: int) -> np.ndarray:
    """The price-only, rf=0 return series -- D217's and D218's reporting basis.

    Deltas are audited on the basis they were REPORTED on. Auditing them on a
    better basis would answer a question nobody asked and would not tell us
    whether the stated hurdle was met."""
    return L.portfolio_log_returns(panel, position)[start:]


def collect(panel, cleaned) -> dict:
    """One return series per (study, rung, book, gate), each at its OWN start."""
    start_217 = L.ladder_start(M.DEFAULT_FAST, M.DEFAULT_SLOW, M.DEFAULT_SIGNAL)
    start_218 = I.ladder_start()
    out: dict[tuple, np.ndarray] = {}
    starts = {"D217": start_217, "D218": start_218, "D229": start_218}

    for book, long_short in BOOKS:
        for gate, gated in GATES:
            for rung in L.RUNGS:
                pos = L.arm_positions(
                    panel, cleaned, rung,
                    M.DEFAULT_FAST, M.DEFAULT_SLOW, M.DEFAULT_SIGNAL,
                    long_short=long_short, gated=gated, start=start_217,
                )
                out[("D217", rung, book, gate)] = _series(panel, pos, start_217)
            for rung in I.RUNGS:
                pos = I.arm_positions(
                    panel, cleaned, rung,
                    long_short=long_short, gated=gated, start=start_218,
                )
                out[("D218", rung, book, gate)] = _series(panel, pos, start_218)
            for rung in ("I0_jerk", "I1_signal"):
                pos = J.arm_positions(
                    panel, cleaned, rung,
                    long_short=long_short, gated=gated, start=start_218,
                )
                out[("D229", rung, book, gate)] = _series(panel, pos, start_218)
    return out, starts


def committed_point(study: str, field: str | None, book: str, gate: str) -> float | None:
    """The value the committed artifact reports, or None where none was published."""
    if field is None:
        p = json.loads((REPO / "data" / "jerk_rung_summary.json").read_text(encoding="utf-8"))
        return float(p["deltas"][f"{book}|{gate}"]["I0_minus_I1"])
    src = "macd_ladder_summary.json" if study == "D217" else "impulse_macd_summary.json"
    p = json.loads((REPO / "data" / src).read_text(encoding="utf-8"))
    for row in p["deltas"]:
        if row["book"] == book and row["gate"] == gate:
            return float(row[field])
    return None


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    series, starts = collect(panel, cleaned)

    rows = []
    repro_failures = []
    for study, label, rung_a, rung_b, field in DELTAS:
        for book, _ in BOOKS:
            for gate, _ in GATES:
                a = series[(study, rung_a, book, gate)]
                b = series[(study, rung_b, book, gate)]
                point = L.sharpe_of(a) - L.sharpe_of(b)

                # THE REPRODUCTION GATE. An audit that cannot reproduce the number
                # it is auditing has found something worse than imprecision.
                published = committed_point(study, field, book, gate)
                drift = None if published is None else abs(point - published)
                if drift is not None and drift > REPRO_TOL:
                    repro_failures.append(
                        {"study": study, "delta": label, "book": book, "gate": gate,
                         "recomputed": point, "published": published, "drift": drift}
                    )

                boot = J.paired_block_bootstrap(a, b)
                rows.append({
                    "study": study,
                    "delta": label,
                    "book": book,
                    "gate": gate,
                    "point": point,
                    "published": published,
                    "reproduction_drift": drift,
                    "p05": boot["p05"],
                    "p50": boot["p50"],
                    "p95": boot["p95"],
                    "sd": boot["sd"],
                    "interval_width": boot["p95"] - boot["p05"],
                    "as_scored": point >= DELTA_HURDLE,
                    "as_claimed": point >= DELTA_HURDLE and boot["p05"] > DELTA_HURDLE,
                    "straddles_zero": boot["p05"] < 0.0 < boot["p95"],
                })

    scored = sum(r["as_scored"] for r in rows)
    claimed = sum(r["as_claimed"] for r in rows)
    return {
        "produced": "D230",
        "seed": J.SEED,
        "n_boot": J.N_BOOT,
        "block": J.BLOCK,
        "delta_hurdle": DELTA_HURDLE,
        "starts": starts,
        "live_bars": {k: int(len(series[("D217", "zero_line", "long_flat", "none")]))
                      if k == "D217" else
                      int(len(series[("D218", "I2_band", "long_flat", "none")]))
                      for k in ("D217", "D218")},
        "rows": rows,
        "n_deltas": len(rows),
        "n_as_scored": scored,
        "n_as_claimed": claimed,
        "n_changed_verdict": scored - claimed,
        "n_straddling_zero": sum(r["straddles_zero"] for r in rows),
        "reproduction_failures": repro_failures,
        "reproduction_clean": not repro_failures,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = []
    o.append("# D230 — the bootstrap sweep\n")
    o.append(
        f"*`scripts/run_bootstrap_sweep.py`, seed {p['seed']}, {p['n_boot']:,} replications "
        f"at block {p['block']}, {p['elapsed_seconds']}s. D217 arms start at bar "
        f"{p['starts']['D217']:,}, D218 and D229 at {p['starts']['D218']:,}.*\n"
    )
    o.append(
        f"**{p['n_as_scored']} of {p['n_deltas']} deltas cleared the hurdle as the runners "
        f"scored it. {p['n_as_claimed']} clear it as the records claimed it. "
        f"{p['n_changed_verdict']} change verdict.**\n"
    )
    if p["reproduction_clean"]:
        o.append(
            "*Reproduction gate: every point estimate matches its committed artifact to "
            "1e-9.*\n"
        )
    else:
        o.append(
            f"***REPRODUCTION GATE FAILED** on {len(p['reproduction_failures'])} deltas — "
            f"see below. The bootstrap results are not the headline of this study.*\n"
        )
    o.append("## Every delta\n")
    o.append("| study | delta | book | gate | point | p05 | p95 | width | as scored | as claimed |")
    o.append("|---|---|---|---|---:|---:|---:|---:|:--:|:--:|")
    for r in p["rows"]:
        o.append(
            f"| {r['study']} | `{r['delta']}` | {r['book']} | {r['gate']} | "
            f"**{r['point']:+.3f}** | {r['p05']:+.3f} | {r['p95']:+.3f} | "
            f"{r['interval_width']:.3f} | "
            f"{'PASS' if r['as_scored'] else '—'} | "
            f"{'PASS' if r['as_claimed'] else '**FAIL**'} |"
        )
    o.append("")
    o.append(
        f"**{p['n_straddling_zero']} of {p['n_deltas']} intervals contain zero.**\n"
    )
    if not p["reproduction_clean"]:
        o.append("## Reproduction failures\n")
        o.append("| study | delta | book | gate | recomputed | published | drift |")
        o.append("|---|---|---|---|---:|---:|---:|")
        for f in p["reproduction_failures"]:
            o.append(
                f"| {f['study']} | `{f['delta']}` | {f['book']} | {f['gate']} | "
                f"{f['recomputed']:+.6f} | {f['published']:+.6f} | {f['drift']:.2e} |"
            )
        o.append("")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")

    RESULTS.write_text(render(payload), encoding="utf-8")
    print(f"deltas swept        {payload['n_deltas']}")
    print(f"reproduction        {'CLEAN' if payload['reproduction_clean'] else 'FAILED'}")
    print(f"clear as SCORED     {payload['n_as_scored']}")
    print(f"clear as CLAIMED    {payload['n_as_claimed']}")
    print(f"change verdict      {payload['n_changed_verdict']}")
    print(f"intervals inc. zero {payload['n_straddling_zero']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
