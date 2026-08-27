"""D228 — mining the mined fixture, with the selection bias MEASURED.

Eight declared candidates on D218's acceleration arm, scored against a
BEST-OF-SEARCH NULL: the identical search run over rotated filter signals, so
the floor is the distribution of "best candidate found when nothing works"
rather than an analytic bound whose `var_trials` is an input.

Offline, deterministic, seed 0. `--report-only` re-renders the page from the
committed artifact and must be byte-identical (the idempotency defect appeared
in D220 and again in D222).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402


def _load_ladder():
    """D218's runner, loaded as a module so its Panel/scoring is REUSED not restated.

    Same importlib pattern `run_impulse_macd._load_d217_runner` uses, and for the
    same reason: `@dataclass` resolves `__module__` through `sys.modules`."""
    path = REPO / "scripts" / "run_macd_ladder.py"
    spec = importlib.util.spec_from_file_location("d217_ladder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


L = _load_ladder()

SUMMARY = REPO / "data" / "filter_search_summary.json"
RESULTS = REPO / "FILTER_SEARCH_RESULTS.md"

PPY = L.PPY  # 252
SEED = 0
N_SIMS = 1000
LAG = 1

# rf, and it is charged on the EXPOSED FRACTION of a long-flat book (D228 Part 1).
RF_ANNUAL = 0.04
RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY

# Declared in D228. VOL_WINDOW and MA_WINDOW are named in the record; MEDIAN_WINDOW
# is NOT, and that gap is disclosed in the RESULT rather than quietly filled.
VOL_WINDOW = 63
MA_WINDOW = 200
MEDIAN_WINDOW = 252

# The closed list. Order is the declaration order and is not re-sorted by result.
GATES = ("G1", "G2")
SIZERS = ("S1", "S2", "S3", "S4", "S5")
OVERLAY = ("R1",)
CANDIDATES = GATES + SIZERS + OVERLAY

# R1 carries no filter signal to rotate — its signal IS the parent's flat mask —
# so it is reported but EXCLUDED from hurdle B. Disclosed, not hidden.
NULL_CANDIDATES = GATES + SIZERS

FRESH_LOOKS = 8
INHERITED_D218 = 62
DISCLOSED_PRIOR = 45_803


# --------------------------------------------------------------------------
# 1-D helpers. Written fresh because the repo's are Panel-shaped or Bar-shaped.
# --------------------------------------------------------------------------


def trailing_std(x: np.ndarray, window: int) -> np.ndarray:
    """Trailing sample sd along axis 1, NaN until `window` observations exist.

    Rolling sum-of-squares rather than a stride trick: at (57, 2500) the memory a
    strided view would materialise is not worth the two lines it saves."""
    n, t = x.shape
    out = np.full((n, t), np.nan)
    c1 = np.cumsum(x, axis=1)
    c2 = np.cumsum(x * x, axis=1)
    for i in range(window, t):
        s1 = c1[:, i] - c1[:, i - window]
        s2 = c2[:, i] - c2[:, i - window]
        var = (s2 - s1 * s1 / window) / (window - 1)
        out[:, i] = np.sqrt(np.maximum(var, 0.0))
    return out


def trailing_median(x: np.ndarray, window: int) -> np.ndarray:
    """Trailing median along axis 1, NaN until `window` non-NaN observations exist.

    STRICTLY TRAILING and that is the whole point: a median over the full span
    would be look-ahead, and this study's sizing candidates all normalise against
    'its own normal level'."""
    n, t = x.shape
    out = np.full((n, t), np.nan)
    for i in range(window, t):
        block = x[:, i - window : i]
        if np.isnan(block).all():
            continue
        out[:, i] = np.nanmedian(block, axis=1)
    return out


def trailing_mean(x: np.ndarray, window: int) -> np.ndarray:
    n, t = x.shape
    out = np.full((n, t), np.nan)
    c = np.cumsum(x, axis=1)
    for i in range(window, t):
        out[:, i] = (c[:, i] - c[:, i - window]) / window
    return out


def shift(x: np.ndarray, lag: int) -> np.ndarray:
    """Hold through bar t what was decided on t-lag. Same convention as
    `run_macd_ladder.arm_positions`, applied to the FILTER as well as the arm so
    the two cannot disagree about what was knowable when."""
    out = np.zeros_like(x)
    out[:, lag:] = x[:, :-lag]
    return out


# --------------------------------------------------------------------------
# The parent
# --------------------------------------------------------------------------


def parent_positions(cleaned: dict, symbols: tuple[str, ...], start: int) -> np.ndarray:
    """D218's I1 / long_flat / no gate, lag=1 — restated from `macd`, not re-derived."""
    rows = []
    for sym in symbols:
        series = M.impulse_macd_series(cleaned[sym])
        score = M.impulse_signal_score(series)
        decided = M.positions(score, start=start, long_short=False)
        rows.append(decided)
    return shift(np.asarray(rows, dtype=float), LAG)


def trade_spans(position: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Maximal runs of exposure, as (symbol_index, start_bar, end_bar_exclusive).

    Extracted ONCE. The parent never changes across candidates or across null
    replications, so every entry-gated book below is a scatter over these same
    spans with a different size vector — which is what makes 1,000 replications
    of an eight-candidate search tractable at all."""
    n, t = position.shape
    on = position > 0.0
    padded = np.zeros((n, t + 2), dtype=bool)
    padded[:, 1:-1] = on
    d = np.diff(padded.astype(np.int8), axis=1)
    sym_s, start = np.nonzero(d == 1)
    sym_e, end = np.nonzero(d == -1)
    assert np.array_equal(sym_s, sym_e), "run starts and ends must pair up"
    return sym_s, start, end


def book_from_spans(
    shape: tuple[int, int],
    sym: np.ndarray,
    start: np.ndarray,
    end: np.ndarray,
    size: np.ndarray,
) -> np.ndarray:
    """Scatter trade sizes into an (n, T) position matrix by delta-then-cumsum.

    `np.add.at` handles the (rare but real) case of two spans sharing a boundary
    bar without the second silently overwriting the first."""
    n, t = shape
    delta = np.zeros((n, t + 1))
    np.add.at(delta, (sym, start), size)
    np.add.at(delta, (sym, end), -size)
    return np.cumsum(delta, axis=1)[:, :t]


# --------------------------------------------------------------------------
# The eight candidates
# --------------------------------------------------------------------------


def candidate_signals(panel, cleaned: dict, start: int) -> dict[str, np.ndarray]:
    """One (n, T) signal per candidate, ALREADY LAG-SHIFTED.

    Gates are 0/1 and sizers are continuous in [0, 1] (S5 excepted, see below).
    Every one is normalised against a TRAILING statistic — never a full-span one —
    so none of them can see its own future."""
    n, t = panel.log_returns.shape

    # --- volatility, shared by G1 / S1 / S3 --------------------------------
    vol = trailing_std(panel.log_returns, VOL_WINDOW) * math.sqrt(PPY)
    own_med = trailing_median(vol, MEDIAN_WINDOW)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        # Every column before the vol window is all-NaN by construction; nanmedian
        # warns about it and the warning is noise, not news.
        warnings.simplefilter("ignore", RuntimeWarning)
        xsec_med = np.nanmedian(vol, axis=0)  # cross-sectional at each bar: trailing
    xsec = np.broadcast_to(xsec_med, (n, t))

    # --- the 200-day MA and its slope, shared by G2 / S4 -------------------
    closes = panel.closes
    ma = trailing_mean(closes, MA_WINDOW)
    slope = np.full((n, t), np.nan)
    slope[:, 1:] = ma[:, 1:] - ma[:, :-1]
    slope_sd = trailing_std(slope, MEDIAN_WINDOW)

    # --- |hist|, for S2 ----------------------------------------------------
    hist = np.asarray(
        [M.impulse_macd_series(cleaned[s]).histogram for s in panel.symbols], dtype=float
    )
    abs_hist = np.abs(hist)
    hist_med = trailing_median(abs_hist, MEDIAN_WINDOW)

    def ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.where(den > 0.0, num / den, np.nan)
        return np.clip(np.nan_to_num(r, nan=0.0), 0.0, 1.0)

    sig: dict[str, np.ndarray] = {}

    # G1 — enter only when trailing vol is below its own trailing median.
    sig["G1"] = np.where(np.isnan(own_med) | np.isnan(vol), 0.0, (vol < own_med) * 1.0)

    # G2 — enter only when the 200-day MA is rising.
    sig["G2"] = np.where(np.isnan(slope), 0.0, (slope > 0.0) * 1.0)

    # S1 — inverse-vol ACROSS instruments: the cross-sectional median is the target,
    # so a 40%-vol energy ETF takes a smaller slice than a 6%-vol bond fund. Derived
    # from the panel at each bar rather than chosen, which is why no TARGET_VOL
    # constant appears anywhere above.
    sig["S1"] = ratio(xsec, vol)

    # S2 — recover the magnitude the sign rule discards.
    sig["S2"] = ratio(abs_hist, hist_med)

    # S3 — G1's information, continuous. Same numerator and denominator as the gate;
    # the gate is the step function of this ratio at 1.0.
    sig["S3"] = ratio(own_med, vol)

    # S4 — G2's information, continuous. 0.5 at zero slope, so it is the smooth
    # analogue of a step at zero rather than a differently-centred rule.
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(slope_sd > 0.0, slope / slope_sd, np.nan)
    sig["S4"] = np.clip(np.nan_to_num(0.5 + 0.5 * z, nan=0.5), 0.0, 1.0)

    # S5 — cross-sectional rank of `hist`, renormalised to mean 1 across ALL 57
    # symbols (not only the held ones). The distinction matters and is NOT what the
    # pre-registration implied: because the parent holds roughly half the universe
    # at a time, normalising over all 57 leaves the held subset averaging ABOVE 1,
    # so S5 RAISES exposure rather than preserving it. Left as built rather than
    # corrected after the fact -- the best-of-search null scores whatever the search
    # actually is, and a candidate that shifts exposure is scored against rotations
    # of itself, which shift it identically. Disclosed in the RESULT.
    order = np.argsort(np.argsort(np.nan_to_num(hist, nan=-np.inf), axis=0), axis=0)
    rank = (order + 1.0) / n
    sig["S5"] = rank / np.maximum(rank.mean(axis=0, keepdims=True), 1e-12)

    return {k: shift(v, LAG) for k, v in sig.items()}


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def excess_sharpe(port: np.ndarray, exposure: np.ndarray) -> float:
    """Sharpe with rf charged on the EXPOSED FRACTION (D228 Part 1, fact 2).

    A long-flat arm holds CASH when flat and cash earns rf, so charging rf against
    the whole book understates it. `sharpe_of` is the rf=0 convention this repo
    reports elsewhere and is kept beside this, not replaced by it."""
    if len(port) < 3:
        return 0.0
    ex = port - exposure * RF_PER_BAR
    sd = float(np.std(ex, ddof=1))
    if sd <= 0.0:
        return 0.0
    return float(np.mean(ex)) / sd * math.sqrt(PPY)


def score(panel, position: np.ndarray, start: int) -> dict:
    live = slice(start, None)
    price = L.portfolio_log_returns(panel, position)[live]
    total = L.portfolio_log_returns(panel, position, total_return=True)[live]
    exposure = position[:, live].mean(axis=0)
    entries = int(np.sum(np.diff(position, axis=1, prepend=0.0)[:, live] > 0.0))
    per_symbol = np.sum(np.diff(position, axis=1, prepend=0.0)[:, live] > 0.0, axis=1)
    return {
        "sharpe_price": L.sharpe_of(price),
        "sharpe_total": L.sharpe_of(total),
        "excess_sharpe": excess_sharpe(total, exposure),
        "total_return": L.total_return_of(total),
        "total_return_price": L.total_return_of(price),
        "max_drawdown": L.max_drawdown_of(total),
        "cagr": float(np.expm1(np.sum(total) / (len(total) / PPY))),
        "exposure": float(exposure.mean()),
        "entries": entries,
        "min_entries_per_symbol": int(per_symbol.min()),
        "turnover_units": int(np.sum(np.diff(position, axis=1) != 0.0)),
    }


def apply_candidate(
    name: str,
    signal: np.ndarray,
    parent: np.ndarray,
    spans: tuple,
    panel,
) -> np.ndarray:
    """The position matrix for one candidate.

    THE TWO MODES ARE NOT INTERCHANGEABLE and the pairing depends on the choice:
    G1/G2 decide AT ENTRY and hold (D228 declares them "enter only when...", the
    D224 convention — exit is the parent's, never the filter's), so their
    continuous twins S3/S4 must also fix their size AT ENTRY or the pair is not
    matched on when the decision is made. S1/S2/S5 are ongoing sizing rules and
    apply every bar by design."""
    sym, start_b, end_b = spans
    if name in ("G1", "G2", "S3", "S4"):
        size = signal[sym, start_b]
        if name in GATES:
            size = (size > 0.0) * 1.0
        return book_from_spans(parent.shape, sym, start_b, end_b, size)
    if name == "R1":
        # The flat slice goes to IEF instead of cash. Each flat symbol contributes
        # 1/n of the book, and `portfolio_log_returns` means across rows, so the
        # row itself carries n * weight.
        out = parent.copy()
        ief = panel.symbols.index("IEF")
        out[ief] = out[ief] + (1.0 - parent).sum(axis=0)
        return out
    return parent * signal


def best_of_search_null(
    panel, parent: np.ndarray, spans: tuple, signals: dict, start: int, base: dict
) -> dict:
    """Hurdle B's floor, MEASURED.

    One offset vector per replication, REUSED ACROSS ALL CANDIDATES. That is the
    load-bearing detail: rotating each candidate independently would make the
    seven artificially independent, inflating the max and producing a floor that
    is wrong in the conservative direction. Correlated candidates must stay
    correlated, because the selection bias being measured IS a function of how
    correlated they are."""
    rng = np.random.default_rng(SEED)
    n, t = parent.shape
    span = t - start
    best_sh = np.empty(N_SIMS)
    best_mo = np.empty(N_SIMS)
    per_cand = {c: np.empty(N_SIMS) for c in NULL_CANDIDATES}
    for s in range(N_SIMS):
        offsets = rng.integers(1, span, size=n)
        sh, mo = [], []
        for name in NULL_CANDIDATES:
            rotated = np.empty_like(signals[name])
            for i in range(n):
                rotated[i] = np.roll(signals[name][i], int(offsets[i]))
            cell = score(panel, apply_candidate(name, rotated, parent, spans, panel), start)
            d_sh = cell["excess_sharpe"] - base["excess_sharpe"]
            d_mo = cell["total_return"] - base["total_return"]
            per_cand[name][s] = d_sh
            sh.append(d_sh)
            mo.append(d_mo)
        best_sh[s] = max(sh)
        best_mo[s] = max(mo)
    return {
        "n_sims": N_SIMS,
        "candidates_in_null": list(NULL_CANDIDATES),
        "best_sharpe_p50": float(np.percentile(best_sh, 50)),
        "best_sharpe_p95": float(np.percentile(best_sh, 95)),
        "best_money_p50": float(np.percentile(best_mo, 50)),
        "best_money_p95": float(np.percentile(best_mo, 95)),
        "single_candidate_p95": {
            c: float(np.percentile(per_cand[c], 95)) for c in NULL_CANDIDATES
        },
        "null_sharpe_sd": float(np.std(np.concatenate([per_cand[c] for c in NULL_CANDIDATES]), ddof=1)),
    }


# --------------------------------------------------------------------------


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    parent = parent_positions(cleaned, panel.symbols, start)
    spans = trade_spans(parent)
    signals = candidate_signals(panel, cleaned, start)

    base = score(panel, parent, start)
    bh = L.buy_and_hold(panel, start)
    bh_pos = np.ones_like(parent)
    bh_pos[:, :start] = 0.0  # exactly `buy_and_hold`'s cost path: one entry at start
    bh_excess = excess_sharpe(
        L.portfolio_log_returns(panel, bh_pos, total_return=True)[start:],
        np.ones(parent.shape[1] - start),
    )

    cells = {}
    for name in CANDIDATES:
        pos = apply_candidate(name, signals.get(name, parent), parent, spans, panel)
        c = score(panel, pos, start)
        c["delta_sharpe"] = c["excess_sharpe"] - base["excess_sharpe"]
        c["delta_money"] = c["total_return"] - base["total_return"]
        c["clears_P"] = c["delta_sharpe"] > 0.0 and c["delta_money"] > 0.0
        c["clears_E"] = c["entries"] >= 100 and c["min_entries_per_symbol"] >= 30
        cells[name] = c

    null = best_of_search_null(panel, parent, spans, signals, start, base)

    # D228 Part 1 claims the arm's money gap against buy-and-hold IS its exposure
    # gap. Eight candidates spanning 24%-100% exposure is a direct test of that
    # claim, and it costs no looks because it re-reads cells already scored.
    # ADDED AFTER A 5-SIM SMOKE RUN, when the pattern was visible in the table.
    dx = np.array([cells[c]["exposure"] - base["exposure"] for c in CANDIDATES])
    dm = np.array([cells[c]["delta_money"] for c in CANDIDATES])
    mechanism = {
        "exposure_vs_money_r": float(np.corrcoef(dx, dm)[0, 1]),
        "pp_money_per_pp_exposure": float(np.polyfit(dx, dm, 1)[0]),
        "note": "added post-smoke; descriptive, not a hurdle",
    }

    scored = [(cells[c]["delta_sharpe"], c) for c in NULL_CANDIDATES]
    best_name = max(scored)[1]
    best = cells[best_name]
    clears_B = (
        best["delta_sharpe"] > null["best_sharpe_p95"]
        and best["delta_money"] > null["best_money_p95"]
    )

    var_pp = float(null["null_sharpe_sd"] ** 2) / PPY
    floors = {
        "fresh": expected_max_sharpe(FRESH_LOOKS, var_pp) * math.sqrt(PPY),
        "with_inherited": expected_max_sharpe(FRESH_LOOKS + INHERITED_D218, var_pp) * math.sqrt(PPY),
        "verdict_count": expected_max_sharpe(FRESH_LOOKS + DISCLOSED_PRIOR, var_pp) * math.sqrt(PPY),
    }

    return {
        "produced": "D228",
        "seed": SEED,
        "n_sims": N_SIMS,
        "rf_annual": RF_ANNUAL,
        "periods_per_year": PPY,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "live_bars": len(panel.dates) - start,
        "windows": {"vol": VOL_WINDOW, "ma": MA_WINDOW, "median": MEDIAN_WINDOW},
        "parent": base,
        "buy_and_hold": dict(bh, excess_sharpe=bh_excess),
        "cells": cells,
        "null": null,
        "mechanism": mechanism,
        "best_candidate": best_name,
        "clears_B": bool(clears_B),
        "floors": floors,
        "ledger": {
            "fresh": FRESH_LOOKS,
            "with_inherited": FRESH_LOOKS + INHERITED_D218,
            "verdict_count": FRESH_LOOKS + DISCLOSED_PRIOR,
            "var_trials_per_period": var_pp,
        },
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def _pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def render(p: dict) -> str:
    b, bh, null = p["parent"], p["buy_and_hold"], p["null"]
    out = []
    out.append("# D228 — the filter search, with the selection bias measured\n")
    out.append(
        f"*Produced by `scripts/run_filter_search.py` (seed {p['seed']}, "
        f"{p['n_sims']:,} null replications, {p['elapsed_seconds']}s). "
        f"{p['first_live_date']} to {p['last_date']}, {p['live_bars']:,} live bars. "
        f"rf = {p['rf_annual']:.0%}, charged on the exposed fraction.*\n"
    )
    out.append("## The baseline\n")
    out.append("| book | excess Sharpe | Sharpe (rf=0) | CAGR | total | max DD | exposure |")
    out.append("|---|---:|---:|---:|---:|---:|---:|")
    out.append(
        f"| **parent (I1 accel)** | **{b['excess_sharpe']:+.3f}** | {b['sharpe_total']:+.3f} | "
        f"{b['cagr'] * 100:.2f}% | {_pct(b['total_return'])} | {_pct(b['max_drawdown'])} | "
        f"{b['exposure'] * 100:.1f}% |"
    )
    out.append(
        f"| buy and hold | {bh['excess_sharpe']:+.3f} | {bh['sharpe_total_return']:+.3f} | "
        f"{bh['cagr_with_dividends'] * 100:.2f}% | {_pct(bh['total_return_with_dividends'])} | "
        f"{_pct(bh['max_drawdown'])} | 100.0% |"
    )
    out.append("")
    out.append("## The eight candidates\n")
    out.append("| | excess Sharpe | delta | money | delta | exposure | entries | P | E |")
    out.append("|---|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for name in CANDIDATES:
        c = p["cells"][name]
        out.append(
            f"| **{name}** | {c['excess_sharpe']:+.3f} | {c['delta_sharpe']:+.3f} | "
            f"{_pct(c['total_return'])} | {c['delta_money'] * 100:+.2f} pp | "
            f"{c['exposure'] * 100:.1f}% | {c['entries']:,} | "
            f"{'PASS' if c['clears_P'] else ''} | {'PASS' if c['clears_E'] else ''} |"
        )
    out.append("")
    out.append("## Hurdle B — the best-of-search null\n")
    out.append(
        f"Seven candidates rotated together, {p['n_sims']:,} replications. "
        f"R1 is excluded: its signal is the parent's own flat mask, so there is "
        f"nothing to rotate.\n"
    )
    out.append("| | best real | null p50 | **null p95** | clears |")
    out.append("|---|---:|---:|---:|:--:|")
    best = p["cells"][p["best_candidate"]]
    out.append(
        f"| excess Sharpe | **{best['delta_sharpe']:+.3f}** | {null['best_sharpe_p50']:+.3f} | "
        f"**{null['best_sharpe_p95']:+.3f}** | "
        f"{'PASS' if best['delta_sharpe'] > null['best_sharpe_p95'] else 'FAIL'} |"
    )
    out.append(
        f"| money | **{best['delta_money'] * 100:+.2f} pp** | {null['best_money_p50'] * 100:+.2f} pp | "
        f"**{null['best_money_p95'] * 100:+.2f} pp** | "
        f"{'PASS' if best['delta_money'] > null['best_money_p95'] else 'FAIL'} |"
    )
    out.append("")
    out.append(
        f"**Best candidate: {p['best_candidate']}. "
        f"Hurdle B: {'CLEARS' if p['clears_B'] else 'FAILS'}.**\n"
    )
    out.append("### Selection bias, measured\n")
    out.append("| | p95 of delta |")
    out.append("|---|---:|")
    for c, v in null["single_candidate_p95"].items():
        out.append(f"| {c} alone | {v:+.3f} |")
    out.append(f"| **best of seven** | **{null['best_sharpe_p95']:+.3f}** |")
    out.append("")
    mech = p["mechanism"]
    lo = min(c["exposure"] for c in p["cells"].values()) * 100
    hi = max(c["exposure"] for c in p["cells"].values()) * 100
    out.append("## The mechanism, tested across the eight\n")
    out.append(
        f"D228 Part 1 claims the arm's money gap against buy-and-hold *is* its exposure "
        f"gap. Across candidates spanning {lo:.0f}% to {hi:.0f}% exposure, money delta "
        f"against exposure delta gives **r = {mech['exposure_vs_money_r']:+.3f}**, slope "
        f"**{mech['pp_money_per_pp_exposure']:.2f} pp of money per pp of exposure**.\n"
    )
    out.append("## The analytic floor, for comparison\n")
    out.append("| count | N | floor |")
    out.append("|---|---:|---:|")
    for k, n in (
        ("fresh", p["ledger"]["fresh"]),
        ("with_inherited", p["ledger"]["with_inherited"]),
        ("verdict_count", p["ledger"]["verdict_count"]),
    ):
        out.append(f"| {k} | {n:,} | {p['floors'][k]:+.3f} |")
    out.append("")
    return "\n".join(out) + "\n"


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
    print(f"parent excess Sharpe   {payload['parent']['excess_sharpe']:+.3f}")
    print(f"buy and hold           {payload['buy_and_hold']['excess_sharpe']:+.3f}")
    print(f"best candidate         {payload['best_candidate']}")
    print(f"  delta Sharpe         {payload['cells'][payload['best_candidate']]['delta_sharpe']:+.3f}")
    print(f"  null p95             {payload['null']['best_sharpe_p95']:+.3f}")
    print(f"HURDLE B               {'CLEARS' if payload['clears_B'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
