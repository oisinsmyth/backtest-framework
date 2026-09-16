"""D229 — one more rung up the derivative ladder.

I2 = trend LEVEL (`md`), I1 = trend ACCELERATION (`hist`), I0 = JERK (`d hist`).
D217 and D218 established acceleration beats level, twice, on constructions
sharing no arithmetic. This asks whether the ladder keeps paying one step further.

The verdict is the PAIRED delta `I0 - I1`, not an absolute Sharpe: nested rungs
read the same series on the same bars, so almost all variance is common and the
difference is estimated far more precisely than either level.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load_ladder():
    path = REPO / "scripts" / "run_macd_ladder.py"
    spec = importlib.util.spec_from_file_location("d217_ladder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


L = _load_ladder()

SUMMARY = REPO / "data" / "jerk_rung_summary.json"
RESULTS = REPO / "docs" / "results" / "JERK_RUNG_RESULTS.md"

PPY = L.PPY
SEED = 0
LAG = 1
GATE_WINDOW = L.GATE_WINDOW
DELTA_HURDLE = L.DELTA_HURDLE  # +0.10, D217's

# D228's correction: rf on a long-flat book is charged on the EXPOSED FRACTION.
RF_ANNUAL = 0.04
RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY

# The paired block bootstrap. Block 21 is `block_shuffle_null`'s default and the
# repo's only precedent for a block length on daily bars.
N_BOOT = 1000
BLOCK = 21

RUNGS = ("I0_jerk", "I1_signal", "I2_band")

# Explicit page order. `json.dumps(sort_keys=True)` reorders the deltas dict on
# the round trip, so a render that iterated the dict produced a DIFFERENT ROW
# ORDER under --report-only than on the live run -- byte-identical in content
# and not in bytes. Same idempotency defect as D220 and D222.
CELL_ORDER = ("long_flat|none", "long_flat|200ma",
              "long_short|none", "long_short|200ma")
FRESH_LOOKS = 4  # I0 x 2 books x 2 gates. I1 and I2 are D218's, already counted.
INHERITED_D218 = 62
DISCLOSED_PRIOR = 45_803


def jerk_score(series) -> tuple[float, ...]:
    """RUNG I0 — the first difference of I1's histogram.

    NaN-safe at the first live bar and wherever the histogram itself is NaN: the
    difference of an unavailable value is unavailable, and `macd.positions` stands
    aside on NaN rather than guessing.

    TIES ARE FLAT and that policy is load-bearing here in a way it is not for a
    level rule. `md` is EXACTLY 0.0 inside the dead zone (a stated value, not a
    missing one), so a run of dead-zone bars gives `hist == 0.0` exactly and then
    `d hist == 0.0` exactly. D229 measured this at 3.10% of live bars before the
    record was written, and committed the flat policy in advance."""
    h = series.histogram
    out = [math.nan]
    for cur, prev in zip(h[1:], h[:-1]):
        out.append(math.nan if (cur != cur or prev != prev) else cur - prev)
    return tuple(out)


def arm_positions(
    panel, bars_by_symbol: dict, rung: str, *, long_short: bool, gated: bool, start: int
) -> np.ndarray:
    """Deliberately NOT a patch to `run_impulse_macd.arm_positions`.

    That function belongs to a committed study; adding a rung to its dispatch
    would edit D218's code after D218 reported. This duplicates four lines and
    reuses everything that matters (`impulse_macd_series`, `positions`,
    `trailing_ma`, the lag convention)."""
    rows = []
    for sym in panel.symbols:
        bars = bars_by_symbol[sym]
        series = M.impulse_macd_series(bars)
        score = {
            "I0_jerk": jerk_score,
            "I1_signal": M.impulse_signal_score,
            "I2_band": M.impulse_band_score,
        }[rung](series)
        gate = M.trailing_ma(bars, GATE_WINDOW) if gated else None
        closes = [b.bar.close for b in bars] if gated else None
        decided = M.positions(
            score, start=start, long_short=long_short, gate=gate, closes=closes
        )
        rows.append((0.0,) * LAG + decided[:-LAG])
    return np.asarray(rows, dtype=float)


def excess_sharpe(port: np.ndarray, exposure: np.ndarray) -> float:
    """rf charged on the exposed fraction (D228 Part 1)."""
    if len(port) < 3:
        return 0.0
    ex = port - exposure * RF_PER_BAR
    sd = float(np.std(ex, ddof=1))
    return 0.0 if sd <= 0.0 else float(np.mean(ex)) / sd * math.sqrt(PPY)


def score_cell(panel, gross_panel, position: np.ndarray, start: int) -> dict:
    live = slice(start, None)
    price = L.portfolio_log_returns(panel, position)[live]
    total = L.portfolio_log_returns(panel, position, total_return=True)[live]
    gross = L.portfolio_log_returns(gross_panel, position)[live]
    exposure = position[:, live].mean(axis=0)
    changes = np.diff(position, axis=1, prepend=0.0)[:, live]
    return {
        "sharpe": L.sharpe_of(price),  # price-only, rf=0 -- D218's basis
        "sharpe_gross": L.sharpe_of(gross),
        "sharpe_total_return": L.sharpe_of(total),
        "excess_sharpe": excess_sharpe(total, exposure),
        "total_return": L.total_return_of(price),
        "total_return_with_dividends": L.total_return_of(total),
        "max_drawdown": L.max_drawdown_of(total),
        "cagr_with_dividends": float(np.expm1(np.sum(total) / (len(total) / PPY))),
        "exposure": float(np.abs(position[:, live]).mean()),
        "entries": int(np.sum(changes > 0.0)),
        "min_entries_per_symbol": int(np.sum(changes > 0.0, axis=1).min()),
        "turnover_units": int(np.sum(np.diff(position, axis=1) != 0.0)),
    }


def paired_block_bootstrap(a: np.ndarray, b: np.ndarray) -> dict:
    """Hurdle A's missing leg, built because the repo has no paired bootstrap.

    D217 and D218 both state hurdle A as ">= +0.10 Sharpe, above the paired
    bootstrap's p95" and NEITHER RUNNER EVER CALLED ONE -- `ladder_deltas`
    compares the point estimate to +0.10 and stops. The cited
    `breakout_nulls.trade_bootstrap` is a single-arm terminal-wealth bootstrap
    over closed trades; it is not paired and could not have supplied that leg.

    The phrasing is also unachievable as literally written: a bootstrap of the
    observed data centres on the OBSERVED delta, so requiring the delta to exceed
    its own p95 is impossible by construction. Made precise in the STRICT
    direction -- a one-sided 95% lower confidence bound, `p05 > DELTA_HURDLE`.

    PAIRED means both rungs are recomputed on the IDENTICAL resampled dates. A
    bootstrap that drew separate dates per rung would destroy the common variance
    that makes a ladder delta worth measuring at all."""
    n = len(a)
    assert len(b) == n, "paired bootstrap needs two series on the same bars"
    rng = np.random.default_rng(SEED)
    n_blocks = math.ceil(n / BLOCK)
    root = math.sqrt(PPY)
    out = np.empty(N_BOOT)
    for s in range(N_BOOT):
        starts = rng.integers(0, n - BLOCK + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(BLOCK)[None, :]).ravel()[:n]
        xa, xb = a[idx], b[idx]
        sa = np.std(xa, ddof=1)
        sb = np.std(xb, ddof=1)
        out[s] = (
            (np.mean(xa) / sa if sa > 0 else 0.0) - (np.mean(xb) / sb if sb > 0 else 0.0)
        ) * root
    return {
        "n_boot": N_BOOT,
        "block": BLOCK,
        "p05": float(np.percentile(out, 5)),
        "p50": float(np.percentile(out, 50)),
        "p95": float(np.percentile(out, 95)),
        "mean": float(np.mean(out)),
        "sd": float(np.std(out, ddof=1)),
    }


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    gross_panel = dataclasses.replace(
        panel, cost_fraction=np.zeros_like(panel.cost_fraction)
    )
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    cells: dict[str, dict] = {}
    series_cache: dict[str, np.ndarray] = {}
    for rung in RUNGS:
        for book, long_short in (("long_flat", False), ("long_short", True)):
            for gate, gated in (("none", False), ("200ma", True)):
                key = f"{rung}|{book}|{gate}"
                pos = arm_positions(
                    panel, cleaned, rung, long_short=long_short, gated=gated, start=start
                )
                cells[key] = score_cell(panel, gross_panel, pos, start)
                series_cache[key] = L.portfolio_log_returns(panel, pos)[start:]

    bh = L.buy_and_hold(panel, start)
    ones = np.ones((len(panel.symbols), panel.closes.shape[1]))
    ones[:, :start] = 0.0
    bh["excess_sharpe"] = excess_sharpe(
        L.portfolio_log_returns(panel, ones, total_return=True)[start:],
        np.ones(panel.closes.shape[1] - start),
    )

    deltas = {}
    for book in ("long_flat", "long_short"):
        for gate in ("none", "200ma"):
            k0, k1, k2 = (f"{r}|{book}|{gate}" for r in RUNGS)
            d = {
                "book": book,
                "gate": gate,
                "I0_minus_I1": cells[k0]["sharpe"] - cells[k1]["sharpe"],
                "I0_minus_I1_gross": cells[k0]["sharpe_gross"] - cells[k1]["sharpe_gross"],
                "I0_minus_I1_excess": cells[k0]["excess_sharpe"] - cells[k1]["excess_sharpe"],
                "I0_minus_I2": cells[k0]["sharpe"] - cells[k2]["sharpe"],
                "I1_minus_I2": cells[k1]["sharpe"] - cells[k2]["sharpe"],
            }
            d["boot"] = paired_block_bootstrap(series_cache[k0], series_cache[k1])
            # D218's OWN headline delta, put through the bootstrap leg D218 stated
            # and never computed. ADDED AFTER D229's run.
            #
            # Defensible for the same reason D218's post-hoc hurdle G was: it can
            # only make a PARENT study look worse and cannot launder D229's own
            # failure. It also spends no new looks -- I1 and I2 are D218's cells,
            # already in the ledger -- and D229 is the record that discovered the
            # missing leg, so reporting what that leg says is an obligation rather
            # than an option.
            d["boot_I1_I2"] = paired_block_bootstrap(series_cache[k1], series_cache[k2])
            d["d218_clears_stated_A"] = (
                d["I1_minus_I2"] >= DELTA_HURDLE
                and d["boot_I1_I2"]["p05"] > DELTA_HURDLE
            )
            d["clears_A"] = (
                d["I0_minus_I1"] >= DELTA_HURDLE and d["boot"]["p05"] > DELTA_HURDLE
            )
            deltas[f"{book}|{gate}"] = d

    primary_key = "I0_jerk|long_flat|none"
    primary_delta = deltas["long_flat|none"]
    p = cells[primary_key]
    var_pp = float(primary_delta["boot"]["sd"] ** 2) / PPY

    return {
        "produced": "D229",
        "seed": SEED,
        "n_boot": N_BOOT,
        "block": BLOCK,
        "rf_annual": RF_ANNUAL,
        "periods_per_year": PPY,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": len(panel.dates) - start,
        "cells": cells,
        "deltas": deltas,
        "buy_and_hold": bh,
        "primary": {
            "cell": primary_key,
            "clears_A": bool(primary_delta["clears_A"]),
            "clears_D": bool(
                p["excess_sharpe"] > bh["excess_sharpe"]
                and p["total_return_with_dividends"] > bh["total_return_with_dividends"]
            ),
            "clears_E": bool(p["entries"] >= 100 and p["min_entries_per_symbol"] >= 30),
        },
        "ledger": {
            "fresh": FRESH_LOOKS,
            "with_inherited": FRESH_LOOKS + INHERITED_D218,
            "verdict_count": FRESH_LOOKS + DISCLOSED_PRIOR,
            "var_trials_per_period": var_pp,
            "floor_fresh": expected_max_sharpe(FRESH_LOOKS, var_pp) * math.sqrt(PPY),
            "floor_verdict": expected_max_sharpe(FRESH_LOOKS + DISCLOSED_PRIOR, var_pp)
            * math.sqrt(PPY),
        },
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def _pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def render(p: dict) -> str:
    o = []
    o.append("# D229 — one more rung up the derivative ladder\n")
    o.append(
        f"*`scripts/run_jerk_rung.py`, seed {p['seed']}, {p['n_boot']:,} bootstrap "
        f"replications at block {p['block']}, {p['elapsed_seconds']}s. "
        f"{p['first_live_date']} to {p['last_date']}, {p['live_bars']:,} live bars.*\n"
    )
    o.append("## The three rungs, long-flat, no gate\n")
    o.append("| rung | Sharpe (price) | gross | excess @rf=4% | money | CAGR | max DD | exposure | turnover |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    names = {"I0_jerk": "**I0 jerk**", "I1_signal": "I1 acceleration", "I2_band": "I2 level"}
    for r in RUNGS:
        c = p["cells"][f"{r}|long_flat|none"]
        o.append(
            f"| {names[r]} | {c['sharpe']:+.3f} | {c['sharpe_gross']:+.3f} | "
            f"{c['excess_sharpe']:+.3f} | {_pct(c['total_return_with_dividends'])} | "
            f"{c['cagr_with_dividends'] * 100:.2f}% | {_pct(c['max_drawdown'])} | "
            f"{c['exposure'] * 100:.1f}% | {c['turnover_units']:,} |"
        )
    bh = p["buy_and_hold"]
    o.append(
        f"| buy and hold | {bh['sharpe']:+.3f} | — | {bh['excess_sharpe']:+.3f} | "
        f"{_pct(bh['total_return_with_dividends'])} | {bh['cagr_with_dividends'] * 100:.2f}% | "
        f"{_pct(bh['max_drawdown'])} | 100.0% | — |"
    )
    o.append("")
    o.append("## Hurdle A — the paired delta\n")
    o.append("| book | gate | I0−I1 | gross | excess | boot p05 | boot p95 | clears A |")
    o.append("|---|---|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        d = p["deltas"][k]
        b = d["boot"]
        o.append(
            f"| {d['book']} | {d['gate']} | **{d['I0_minus_I1']:+.3f}** | "
            f"{d['I0_minus_I1_gross']:+.3f} | {d['I0_minus_I1_excess']:+.3f} | "
            f"{b['p05']:+.3f} | {b['p95']:+.3f} | "
            f"{'PASS' if d['clears_A'] else 'FAIL'} |"
        )
    o.append("")
    o.append(f"*Hurdle: point estimate ≥ {DELTA_HURDLE:+.2f} **and** bootstrap p05 > "
             f"{DELTA_HURDLE:+.2f}.*\n")
    o.append("## The ladder, for comparison with D218\n")
    o.append("| book | gate | I0−I1 | I1−I2 | I0−I2 |")
    o.append("|---|---|---:|---:|---:|")
    for k in CELL_ORDER:
        d = p["deltas"][k]
        o.append(
            f"| {d['book']} | {d['gate']} | {d['I0_minus_I1']:+.3f} | "
            f"{d['I1_minus_I2']:+.3f} | {d['I0_minus_I2']:+.3f} |"
        )
    o.append("")
    o.append("## D218's headline, through the bootstrap leg it stated and never ran\n")
    o.append("| book | gate | I1−I2 | boot p05 | clears the hurdle D218 wrote |")
    o.append("|---|---|---:|---:|:--:|")
    for k in CELL_ORDER:
        d = p["deltas"][k]
        o.append(
            f"| {d['book']} | {d['gate']} | **{d['I1_minus_I2']:+.3f}** | "
            f"{d['boot_I1_I2']['p05']:+.3f} | "
            f"{'PASS' if d['d218_clears_stated_A'] else '**FAIL**'} |"
        )
    o.append("")
    pr = p["primary"]
    o.append(
        f"**Primary cell `{pr['cell']}` — A: {'CLEARS' if pr['clears_A'] else 'FAILS'}, "
        f"D: {'CLEARS' if pr['clears_D'] else 'FAILS'}, "
        f"E: {'CLEARS' if pr['clears_E'] else 'FAILS'}.**\n"
    )
    lg = p["ledger"]
    o.append("## Ledger\n")
    o.append("| count | N | floor |")
    o.append("|---|---:|---:|")
    o.append(f"| fresh | {lg['fresh']:,} | {lg['floor_fresh']:+.3f} |")
    o.append(f"| + inherited | {lg['with_inherited']:,} | — |")
    o.append(f"| verdict count | {lg['verdict_count']:,} | {lg['floor_verdict']:+.3f} |")
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
    d = payload["deltas"]["long_flat|none"]
    print(f"I0 - I1  net    {d['I0_minus_I1']:+.3f}")
    print(f"I0 - I1  gross  {d['I0_minus_I1_gross']:+.3f}")
    print(f"I0 - I2         {d['I0_minus_I2']:+.3f}   (I1 - I2 = {d['I1_minus_I2']:+.3f})")
    print(f"bootstrap p05   {d['boot']['p05']:+.3f}   p50 {d['boot']['p50']:+.3f}")
    print(f"HURDLE A        {'CLEARS' if payload['primary']['clears_A'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
