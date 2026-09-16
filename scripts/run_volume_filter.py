"""D220 — can volume tell Impulse MACD which of its trades are the bad ones?

    uv run python scripts/run_volume_filter.py
    uv run python scripts/run_volume_filter.py --report-only

Offline, deterministic, seeded. `docs/decisions/D220-the-volume-filter-on-impulse-macd.md`
was written and committed BEFORE this file existed.

WHAT IS BEING TESTED
--------------------
Not "does volume work". Whether a volume condition **specified in advance** removes
trades that go on to LOSE at a higher rate than it removes trades that go on to WIN.
That is a trade-level claim, and the portfolio numbers are consequences of it. A
filter can raise Sharpe purely by removing exposure from a book whose marginal
exposure is unprofitable, and that is not selectivity — so the null is matched on
trade COUNT, which is exactly what a filter does.

THE TWO BOUNDS
--------------
ORACLE removes the worst k% of trades by REALISED PnL. It is look-ahead by
construction, is never a strategy, and carries the word ORACLE in every table it
appears in. D181 is the standing distinction: the look-ahead guard binds strategies,
not analytics, and this is an analytic upper bound.

RANDOM removes the same COUNT at random. Any real filter must land above it.

    capture = (filter - random_median) / (oracle - random_median)

WHY THIS SCRIPT IMPORTS THE OTHER TWO RUNNERS
---------------------------------------------
The panel, cost derivation, portfolio arithmetic, nulls and DSR machinery are
REUSED, NOT RESTATED (D212). Volume is loaded SEPARATELY rather than by changing
`load_panel`, so no previously published number can move — the pre-registration
makes that a stop condition, and `test_volume_filter.py` pins it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.csv_fixture import (  # noqa: E402
    load_fixture_csv_with_volumes,
)
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


L = _load("run_macd_ladder", "run_macd_ladder.py")
I = _load("run_impulse_macd", "run_impulse_macd.py")  # noqa: E741

SUMMARY = REPO / "data" / "volume_filter_summary.json"
RESULTS = REPO / "docs" / "results" / "MACD_RESULTS.md"

PPY = L.PPY
SEED = 0
N_SIMS = 400
NULL_PERCENTILE = 95.0

PARENT_RUNG = "I1_signal"
WINDOWS = (20, 50)
CONDITIONS = ("V1_confirmation", "V2_contrarian", "V3_rising")
BOOKS = (False, True)  # long_flat, long_short

FRESH_LOOKS = len(CONDITIONS) * len(WINDOWS) * len(BOOKS)  # 12
INHERITED_LOOKS = 62  # D217's 42 + D218's 20
MARGINAL_HURDLE = 0.05  # D219 P4
MIN_ENTRIES_PER_ETF = 30  # D216 WP2 census gate
ORACLE_GRID = (0.10, 0.20, 0.30, 0.50)


# --------------------------------------------------------------------------
# Volume, loaded WITHOUT touching load_panel
# --------------------------------------------------------------------------


def volume_matrix(panel, cleaned: dict) -> np.ndarray:
    """(n, T) volumes aligned to the CLEANED bar grid, by timestamp.

    `load_fixture_csv` delegates to `load_fixture_csv_with_volumes` and throws the
    volumes away, so re-reading here returns the identical bars — the price path
    cannot move. `clean()` may drop bars, so the join is on timestamp rather than
    on position, and every cleaned bar must find a volume or this raises."""
    raw_bars, raw_vols = load_fixture_csv_with_volumes(L.FIXTURE)
    rows = []
    for sym in panel.symbols:
        by_ts = {
            tb.timestamp: v for tb, v in zip(raw_bars[sym], raw_vols[sym], strict=True)
        }
        series = []
        for tb in cleaned[sym]:
            v = by_ts.get(tb.timestamp)
            if v is None or not math.isfinite(v):
                raise ValueError(f"{sym}: no finite volume for bar {tb.timestamp}")
            series.append(float(v))
        rows.append(series)
    return np.asarray(rows, dtype=float)


def trailing_mean(values: np.ndarray, window: int) -> np.ndarray:
    """Mean of the `window` bars ENDING AT t inclusive. NaN before it exists."""
    out = np.full(values.shape, np.nan, dtype=float)
    if values.shape[1] < window:
        return out
    csum = np.cumsum(values, axis=1)
    out[:, window - 1] = csum[:, window - 1] / window
    out[:, window:] = (csum[:, window:] - csum[:, :-window]) / window
    return out


def entry_allowed(volumes: np.ndarray, condition: str, window: int) -> np.ndarray:
    """(n, T) boolean: may a trade whose position FIRST EXISTS at t be opened?

    THE INFORMATION BOUNDARY. With `lag=1` the position held through bar t was
    decided from bar t-1's close, so the newest volume legitimately available to
    that decision is `volume[t-1]`. Everything here is therefore read at t-1, and
    `test_the_filter_reads_no_bar_later_than_the_decision_bar` pins it."""
    ma = trailing_mean(volumes, window)
    prev_v = np.full(volumes.shape, np.nan)
    prev_v[:, 1:] = volumes[:, :-1]
    prev_ma = np.full(volumes.shape, np.nan)
    prev_ma[:, 1:] = ma[:, :-1]
    if condition == "V1_confirmation":
        ok = prev_v > prev_ma
    elif condition == "V2_contrarian":
        ok = prev_v < prev_ma
    elif condition == "V3_rising":
        prev_ma2 = np.full(volumes.shape, np.nan)
        prev_ma2[:, 2:] = ma[:, :-2]
        ok = prev_ma > prev_ma2
    else:  # pragma: no cover - guarded by CONDITIONS
        raise ValueError(condition)
    return np.where(np.isnan(prev_ma), False, ok)


# --------------------------------------------------------------------------
# Trades
# --------------------------------------------------------------------------


def extract_trades(panel, position: np.ndarray, start: int) -> list[dict]:
    """One record per maximal run of non-zero exposure in one symbol.

    PnL is the dividend-adjusted log return over the run at the held size, less
    two sides of cost — the same per-side convention `portfolio_log_returns`
    charges (D212), written per trade."""
    ret = panel.total_log_returns
    trades = []
    for i in range(position.shape[0]):
        live = position[i, start:]
        t = 0
        while t < len(live):
            if live[t] == 0.0:
                t += 1
                continue
            j = t
            while j < len(live) and live[j] != 0.0:
                j += 1
            a, b = start + t, start + j
            pnl = float(np.sum(ret[i, a:b] * live[t]))
            pnl += 2.0 * float(np.log1p(-panel.cost_fraction[i]))
            trades.append(
                {"row": i, "entry": a, "exit": b, "size": float(live[t]), "pnl": pnl}
            )
            t = j
    return trades


def book_from_trades(shape, trades: list[dict], keep: np.ndarray) -> np.ndarray:
    out = np.zeros(shape, dtype=float)
    for k, tr in enumerate(trades):
        if keep[k]:
            out[tr["row"], tr["entry"] : tr["exit"]] = tr["size"]
    return out


def census(trades: list[dict], n_symbols: int) -> dict:
    pnl = np.array([t["pnl"] for t in trades], dtype=float)
    wins = pnl > 0
    per_symbol = np.bincount(
        [t["row"] for t in trades], minlength=n_symbols
    ).astype(float)
    return {
        "n_trades": len(trades),
        "win_rate": float(wins.mean()) if len(pnl) else 0.0,
        "mean_win": float(np.expm1(pnl[wins].mean())) if wins.any() else 0.0,
        "mean_loss": float(np.expm1(pnl[~wins].mean())) if (~wins).any() else 0.0,
        "median_hold_bars": float(np.median([t["exit"] - t["entry"] for t in trades]))
        if trades
        else 0.0,
        "min_entries_per_etf": float(per_symbol.min()),
        "median_entries_per_etf": float(np.median(per_symbol)),
    }


# --------------------------------------------------------------------------
# The bounds
# --------------------------------------------------------------------------


def score(panel, position: np.ndarray, start: int) -> tuple[float, float]:
    s = L.portfolio_log_returns(panel, position, total_return=True)[start:]
    return L.sharpe_of(s), L.total_return_of(s)


def oracle_at(panel, trades, shape, start, n_remove: int) -> tuple[float, float]:
    """ORACLE — look-ahead by construction. A BOUND, NEVER A STRATEGY (D181)."""
    keep = np.ones(len(trades), dtype=bool)
    if n_remove > 0:
        worst = np.argsort([t["pnl"] for t in trades])[:n_remove]
        keep[worst] = False
    return score(panel, book_from_trades(shape, trades, keep), start)


def random_matched(
    panel, trades, shape, start, n_remove: int, n_sims: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """The null for a selectivity claim: remove the same COUNT at random, so a
    delta over it cannot be explained by simply having traded less."""
    rng = np.random.default_rng(seed)
    sh = np.empty(n_sims)
    tot = np.empty(n_sims)
    for s in range(n_sims):
        keep = np.ones(len(trades), dtype=bool)
        if n_remove > 0:
            keep[rng.choice(len(trades), n_remove, replace=False)] = False
        sh[s], tot[s] = score(panel, book_from_trades(shape, trades, keep), start)
    return sh, tot


def label_permutation_p(pnl: np.ndarray, removed: np.ndarray, seed: int) -> dict:
    """Is the removed set's mean PnL below the kept set's by more than chance?

    Permutes the REMOVED/KEPT labels, holding the trade population and the removal
    count fixed. Directly tests selectivity without going through the portfolio."""
    n_rm = int(removed.sum())
    if n_rm == 0 or n_rm == len(pnl):
        return {"observed_gap": 0.0, "percentile": float("nan"), "n_removed": n_rm}
    observed = float(pnl[~removed].mean() - pnl[removed].mean())
    rng = np.random.default_rng(seed)
    draws = np.empty(2000)
    idx = np.arange(len(pnl))
    for s in range(2000):
        rm = rng.choice(idx, n_rm, replace=False)
        mask = np.zeros(len(pnl), dtype=bool)
        mask[rm] = True
        draws[s] = pnl[~mask].mean() - pnl[mask].mean()
    return {
        "observed_gap": observed,
        "percentile": float((draws < observed).mean() * 100.0),
        "n_removed": n_rm,
    }


def capture(value: float, random_median: float, oracle: float) -> float:
    span = oracle - random_median
    return float((value - random_median) / span) if abs(span) > 1e-12 else 0.0


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


def run_cells(panel, bars, volumes, start: int) -> tuple[list[dict], dict]:
    shape = panel.log_returns.shape
    parents, parent_trades, parent_scores = {}, {}, {}
    for long_short in BOOKS:
        p = I.arm_positions(
            panel, bars, PARENT_RUNG, long_short=long_short, gated=False,
            start=start, lag=1,
        )
        parents[long_short] = p
        parent_trades[long_short] = extract_trades(panel, p, start)
        parent_scores[long_short] = score(panel, p, start)

    bh = L.buy_and_hold(panel, start)
    bh_stream = L.portfolio_log_returns(
        panel, np.where(np.arange(shape[1]) >= start, 1.0, 0.0)[None, :].repeat(shape[0], 0),
        total_return=True,
    )[start:]

    cells = []
    for long_short in BOOKS:
        parent = parents[long_short]
        trades = parent_trades[long_short]
        pnl = np.array([t["pnl"] for t in trades], dtype=float)
        p_sh, p_tot = parent_scores[long_short]
        for cond in CONDITIONS:
            for window in WINDOWS:
                ok = entry_allowed(volumes, cond, window)
                keep = np.array([bool(ok[t["row"], t["entry"]]) for t in trades])
                n_remove = int((~keep).sum())
                book = book_from_trades(shape, trades, keep)
                f_sh, f_tot = score(panel, book, start)

                o_sh, o_tot = oracle_at(panel, trades, shape, start, n_remove)
                r_sh, r_tot = random_matched(
                    panel, trades, shape, start, n_remove, N_SIMS, SEED
                )
                perm = label_permutation_p(pnl, ~keep, SEED)

                kept_trades = [t for t, k in zip(trades, keep) if k]
                cen = census(kept_trades, shape[0])
                fs = L.portfolio_log_returns(panel, book, total_return=True)[start:]

                # D219 in-portfolio: marginal contribution against the DECLARED
                # incumbent (buy-and-hold), plus correlation with the parent arm.
                combo = (fs + bh_stream) / 2.0
                p_stream = L.portfolio_log_returns(panel, parent, total_return=True)[start:]
                cells.append(
                    {
                        "condition": cond,
                        "window": window,
                        "book": "long_short" if long_short else "long_flat",
                        "cell": f"{cond}/{window}/{'long_short' if long_short else 'long_flat'}",
                        "sharpe": f_sh,
                        "total_return_with_dividends": f_tot,
                        "exposure": float(np.mean(np.abs(book[:, start:]))),
                        "parent_sharpe": p_sh,
                        "parent_total_return": p_tot,
                        "trades_removed": n_remove,
                        "trades_kept": int(keep.sum()),
                        "removal_fraction": float(n_remove / max(len(trades), 1)),
                        "oracle_sharpe": o_sh,
                        "oracle_total_return": o_tot,
                        "random_sharpe_p50": float(np.percentile(r_sh, 50)),
                        "random_sharpe_p95": float(np.percentile(r_sh, NULL_PERCENTILE)),
                        "random_total_p50": float(np.percentile(r_tot, 50)),
                        "random_total_p95": float(np.percentile(r_tot, NULL_PERCENTILE)),
                        "sharpe_percentile_in_random": L.percentile_of(f_sh, r_sh),
                        "total_percentile_in_random": L.percentile_of(f_tot, r_tot),
                        "capture_sharpe": capture(f_sh, float(np.percentile(r_sh, 50)), o_sh),
                        "capture_total": capture(f_tot, float(np.percentile(r_tot, 50)), o_tot),
                        "permutation": perm,
                        "census": cen,
                        "corr_with_parent": float(np.corrcoef(fs, p_stream)[0, 1]),
                        "corr_with_buy_and_hold": float(np.corrcoef(fs, bh_stream)[0, 1]),
                        "marginal_contribution_vs_bh": float(
                            L.sharpe_of(combo) - L.sharpe_of(bh_stream)
                        ),
                        "sharpe_first_half": L.sharpe_of(fs[: L._half_index(panel, start) - start]),
                        "sharpe_second_half": L.sharpe_of(fs[L._half_index(panel, start) - start :]),
                    }
                )

    parent_block = {
        "rung": PARENT_RUNG,
        "books": {
            ("long_short" if ls else "long_flat"): {
                "sharpe": parent_scores[ls][0],
                "total_return_with_dividends": parent_scores[ls][1],
                "census": census(parent_trades[ls], shape[0]),
                "oracle_grid": [
                    {
                        "remove_fraction": f,
                        "sharpe": oracle_at(
                            panel, parent_trades[ls], shape, start,
                            int(round(f * len(parent_trades[ls]))),
                        )[0],
                        "total_return": oracle_at(
                            panel, parent_trades[ls], shape, start,
                            int(round(f * len(parent_trades[ls]))),
                        )[1],
                    }
                    for f in ORACLE_GRID
                ],
            }
            for ls in BOOKS
        },
        "buy_and_hold": bh,
    }
    return cells, parent_block


def multiplicity(cells: list[dict], prior: dict) -> dict:
    per_period = [c["sharpe"] / math.sqrt(PPY) for c in cells]
    var_trials = float(np.var(per_period, ddof=1))
    counts = {
        "fresh_d220_only": FRESH_LOOKS,
        "with_inherited": FRESH_LOOKS + INHERITED_LOOKS,
        "combined_with_disclosed": FRESH_LOOKS
        + INHERITED_LOOKS
        + prior["distinct_configs"]
        + L.DISCLOSED_PRIOR_LOOKS,
    }
    floors = {}
    for name, n in counts.items():
        sr0 = expected_max_sharpe(n, var_trials)
        floors[name] = {
            "n_trials": int(n),
            "expected_max_sharpe_per_period": sr0,
            "expected_max_sharpe_annualised": sr0 * math.sqrt(PPY),
        }
    return {
        "var_trials_per_period": var_trials,
        "raw_row_ceiling": prior["raw_rows"],
        "counts": floors,
        "verdict_count": "combined_with_disclosed",
        "units_contract": "D98: metric, sr and t are all per-period",
    }


def verdict(cells: list[dict], parent: dict, mult: dict) -> dict:
    floor = mult["counts"][mult["verdict_count"]]["expected_max_sharpe_annualised"]
    bh = parent["buy_and_hold"]
    rows = []
    for c in cells:
        beats_random = (
            c["sharpe_percentile_in_random"] >= NULL_PERCENTILE
            and c["total_percentile_in_random"] >= NULL_PERCENTILE
        )
        perm_ok = c["permutation"]["percentile"] >= NULL_PERCENTILE
        h = bool(beats_random and perm_ok)
        powered = c["census"]["min_entries_per_etf"] >= MIN_ENTRIES_PER_ETF
        if c["book"] == "long_flat":
            d = (
                c["sharpe"] > bh["sharpe_total_return"]
                and c["total_return_with_dividends"] > bh["total_return_with_dividends"]
            )
        else:
            d = c["sharpe"] > 0.0
        rows.append(
            {
                "cell": c["cell"],
                "H_selectivity": h,
                "H_beats_random_both": bool(beats_random),
                "H_permutation": bool(perm_ok),
                "D_benchmark": bool(d),
                "E_powered": bool(powered),
                "F_same_sign_halves": bool(
                    (c["sharpe_first_half"] > 0) == (c["sharpe_second_half"] > 0)
                ),
                "G_clears_floor": bool(c["sharpe"] > floor),
                "P4_marginal": bool(c["marginal_contribution_vs_bh"] >= MARGINAL_HURDLE),
                "beats_parent_sharpe": bool(c["sharpe"] > c["parent_sharpe"]),
                "beats_parent_money": bool(
                    c["total_return_with_dividends"] > c["parent_total_return"]
                ),
            }
        )
    survivors = [
        r["cell"]
        for r in rows
        if r["H_selectivity"] and r["D_benchmark"] and r["E_powered"]
        and r["F_same_sign_halves"] and r["G_clears_floor"]
    ]
    return {
        "floor_annualised": floor,
        "buy_and_hold_sharpe": bh["sharpe_total_return"],
        "buy_and_hold_total_return_with_dividends": bh["total_return_with_dividends"],
        "rows": rows,
        "survivors": survivors,
        "n_clearing_H": sum(1 for r in rows if r["H_selectivity"]),
        "n_clearing_P4": sum(1 for r in rows if r["P4_marginal"]),
    }


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def render(p: dict) -> str:
    v, m = p["verdict"], p["multiplicity"]
    par = p["parent"]
    lf = par["books"]["long_flat"]
    out: list[str] = []
    w = out.append
    w("## D220 — a volume filter on Impulse MACD: can it tell the bad trades from the good?")
    w("")
    w(f"**Produced:** {p['produced']} · **Reproduce:** `uv run python scripts/run_volume_filter.py`")
    w("(offline, deterministic, seed 0) · Decision record:")
    w("[`D220`](../decisions/D220-the-volume-filter-on-impulse-macd.md) · Artifact:")
    w("`data/volume_filter_summary.json`")
    w("")
    w("### The parent, and the space a filter has to work in")
    w("")
    c = lf["census"]
    w(f"`{PARENT_RUNG}` long-flat: **{c['n_trades']:,} trades**, win rate "
      f"**{_pct(c['win_rate'])}**, mean win {_pct(c['mean_win'])} against mean loss "
      f"{_pct(c['mean_loss'])}. **A majority of this arm's trades lose** — it earns on the "
      f"payoff ratio, not the hit rate, so there is a real population of bad trades to remove.")
    w("")
    w("| remove | ORACLE Sharpe | ORACLE total | — the ceiling for ANY filter |")
    w("|---:|---:|---:|---|")
    for g in lf["oracle_grid"]:
        w(f"| {g['remove_fraction'] * 100:.0f}% | {g['sharpe']:+.3f} | "
          f"{_pct(g['total_return'])} | look-ahead, never a strategy |")
    w("")
    w(f"Unfiltered parent: **{lf['sharpe']:+.3f}** Sharpe, "
      f"**{_pct(lf['total_return_with_dividends'])}** total.")
    w("")
    w("### The filters")
    w("")
    w("| cell | removed | Sharpe | total | capture Sh | capture $ | pct in random (Sh / $) | perm |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for cell in p["cells"]:
        w(f"| {cell['cell']} | {cell['trades_removed']:,} "
          f"({cell['removal_fraction'] * 100:.0f}%) | {cell['sharpe']:+.3f} | "
          f"{_pct(cell['total_return_with_dividends'])} | "
          f"{cell['capture_sharpe'] * 100:+.0f}% | {cell['capture_total'] * 100:+.0f}% | "
          f"{cell['sharpe_percentile_in_random']:.0f} / "
          f"{cell['total_percentile_in_random']:.0f} | "
          f"{cell['permutation']['percentile']:.0f} |")
    w("")
    w("`capture` is the fraction of the ORACLE-minus-RANDOM space the filter took, at its")
    w("own removal count. `pct in random` is where it sits inside the matched-count null;")
    w("hurdle H needs **95 on both** plus 95 on the label permutation.")
    w("")
    w("### Verdict")
    w("")
    w("| cell | H | D | E | F | G | P4 | > parent Sh | > parent $ |")
    w("|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for r in v["rows"]:
        def mark(x: bool) -> str:
            return "yes" if x else "no"
        w(f"| {r['cell']} | {mark(r['H_selectivity'])} | {mark(r['D_benchmark'])} | "
          f"{mark(r['E_powered'])} | {mark(r['F_same_sign_halves'])} | "
          f"{mark(r['G_clears_floor'])} | {mark(r['P4_marginal'])} | "
          f"{mark(r['beats_parent_sharpe'])} | {mark(r['beats_parent_money'])} |")
    w("")
    w(f"**{v['n_clearing_H']} of {len(v['rows'])} cells clear hurdle H "
      f"(selectivity). {v['n_clearing_P4']} clear P4. "
      f"{len(v['survivors'])} clear every hurdle.**")
    w("")
    w("### Multiplicity")
    w("")
    w("| count | N | noise floor |")
    w("|---|---:|---:|")
    for name, f in m["counts"].items():
        w(f"| {name} | {f['n_trials']:,} | {f['expected_max_sharpe_annualised']:+.3f} |")
    w("")
    w(f"Verdict floor **{v['floor_annualised']:+.3f}**. Raw row ceiling "
      f"{m['raw_row_ceiling']:,}, which is not an N.")
    w("")
    w("### The disclosure that belongs beside the verdict, not in a footnote")
    w("")
    w("**ETF volume is a weak instrument.** ETF liquidity comes from the")
    w("creation/redemption mechanism and the underlying basket, so on-exchange volume is a")
    w("poor proxy for interest — a quiet tape can simply mean the authorised participants")
    w("did not need to trade. A negative result here is **weaker evidence against volume as")
    w("a concept** than the same result would be on single names or crypto.")
    w("")
    return "\n".join(out) + "\n"


def append_section(text: str) -> None:
    """Splice the D220 section in, IDEMPOTENTLY.

    D217 published a page that `--report-only` could not reproduce byte-for-byte,
    and the first version of this function had the same defect in a different
    place: the insert path and the replace path emitted a different number of
    blank lines before the parking lot. Any existing D220 section is therefore
    stripped first so both paths run the SAME insertion, and
    `test_report_only_reproduces_the_page_byte_for_byte` pins it."""
    page = RESULTS.read_text(encoding="utf-8")
    anchor = "### Parking lot"
    marker = "## D220 —"
    if marker in page:
        head, rest = page.split(marker, 1)
        tail = anchor + rest.split(anchor, 1)[1] if anchor in rest else ""
        page = head.rstrip("\n") + ("\n\n" + tail if tail else "\n")
    if anchor in page:
        head, tail = page.split(anchor, 1)
        RESULTS.write_text(
            head.rstrip("\n") + "\n\n" + text + "\n" + anchor + tail, encoding="utf-8"
        )
    else:
        RESULTS.write_text(page.rstrip("\n") + "\n\n" + text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    if not args.report_only:
        t0 = time.time()
        panel, cleaned = L.load_panel()
        volumes = volume_matrix(panel, cleaned)
        start = I.ladder_start()
        cells, parent = run_cells(panel, cleaned, volumes, start)
        prior = L.prior_etf_trials()
        mult = multiplicity(cells, prior)
        payload = {
            "produced": time.strftime("%Y-%m-%d"),
            "common_start": start,
            "n_bars_live": len(panel.dates) - start,
            "span": [panel.dates[start], panel.dates[-1]],
            "parent": parent,
            "cells": cells,
            "multiplicity": mult,
            "verdict": verdict(cells, parent, mult),
            "fresh_looks": FRESH_LOOKS,
            "seed": SEED,
            "n_sims": N_SIMS,
        }
        SUMMARY.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SUMMARY.name} in {time.time() - t0:.1f}s")

    # ALWAYS render from the re-read artifact, never from memory: sort_keys
    # reorders dicts on round-trip, and D217 published a page that --report-only
    # could not reproduce because of exactly that.
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    append_section(render(payload))
    v = payload["verdict"]
    print(
        f"H cleared by {v['n_clearing_H']}/{len(v['rows'])}; "
        f"survivors {len(v['survivors'])}; floor {v['floor_annualised']:+.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
