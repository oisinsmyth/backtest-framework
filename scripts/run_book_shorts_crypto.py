"""D253 — the short sides of S1 and S2, on crypto.

    S1_short  position = -1 if hist_L > 0 AND md_L <= 0          (D238's mirror)
    S2_short  DOWNTREND := g_lo < 0 AND g_hi < 0; enter at onset,
              exit at age 63 or when the state ends              (D240's mirror)
    C_short   both on one shared pool at 100% capital, FCFS

REGISTERED SEPARATELY FROM S3 AND ITS PROVENANCE IS IN D253'S OPENING SECTION.
D244 ran S1 LONG here and it landed at the 29.1st percentile of its own null, so
this is a complement. What makes it registrable is that the prediction came from
a structural hypothesis stated BEFORE the measurement, not from flipping a bad
result. D245's reserved cohort is NOT touched.

THE DRIFT CONFOUND IS THE WHOLE METHODOLOGICAL POINT. Crypto fell over this
sample, so a short earns by existing. The matched-count rotation null holds the
same exposure, turnover and holding periods on the WRONG bars, so it earns that
drift too -- ONLY THE EXCESS OVER THE NULL IS EVIDENCE. The raw return of a short
book on a falling universe is not a result and is not reported as one.

THREE OVERRIDES, each asserted OFF outside the crypto block. PPY=365, FEE_BPS=10
(the committed crypto constant, 6x the ETF book's ~1.6bp), and BORROW=10%/yr --
`run_short_mirror`'s 1.0% is an EQUITY borrow rate and is wrong here by an order
of magnitude. THE BORROW RATE IS A STATED ASSUMPTION, NOT A MEASUREMENT, so
`breakeven_borrow` is a headline number in every cell rather than a footnote.

R10 IS MANDATORY HERE. Crypto synchronises harder than equities, so names-held-at-
once is reported against a per-symbol-rotated book of identical exposure, and the
effective sample is reported instead of the pooled trade count.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
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

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = _load("d244_crypto", "run_book_crypto.py")
B, U, X, L, S, E = C.B, C.U, C.X, C.L, C.S, C.E

SUMMARY = REPO / "data" / "book_shorts_crypto_summary.json"
RESULTS = REPO / "BOOK_SHORTS_CRYPTO_RESULTS.md"

SEED, N_SIMS = X.SEED, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL
PPY_CRYPTO = C.PPY_CRYPTO                 # 365
FEE_BPS = C.FEE_BPS                       # 10 per side
BORROW_CRYPTO = 0.10                      # D253: a STATED ASSUMPTION, not a measurement
CELL_ORDER = ("S1_short", "S2_short", "C_short")


# --------------------------------------------------------------------------
# The books, with the overrides live only inside the block
# --------------------------------------------------------------------------


def books_on_crypto():
    """Load D244's frozen fixture with the crypto overrides, then put them back.

    THE OVERRIDES ARE THE RISK -- one left switched on silently corrupts every
    later equity study. Restored in a `finally` and asserted by the caller."""
    saved = (L.PPY, X.PPY, U.PPY, E.PPY, L.FIXTURE, L.EVENTS,
             X.RF_PER_BAR, X.BORROW_PER_BAR)
    try:
        L.PPY = X.PPY = U.PPY = E.PPY = PPY_CRYPTO
        X.RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY_CRYPTO
        X.BORROW_PER_BAR = math.log1p(BORROW_CRYPTO) / PPY_CRYPTO
        L.FIXTURE, L.EVENTS = C.FIXTURE, C.EVENTS
        panel, cleaned = L.load_panel()
        panel = type(panel)(
            symbols=panel.symbols, closes=panel.closes, log_returns=panel.log_returns,
            cost_fraction=np.full(len(panel.symbols), FEE_BPS / 1e4),
            dates=panel.dates, total_log_returns=panel.total_log_returns,
        )
        start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

        # S1's mirror -- the same mask, the opposite sign
        md, hs, ok = S.base_masks(panel, cleaned, start)
        s1_long = S.hold_book((hs > 0) & (md <= 0) & ok, start)
        s1 = -s1_long

        # S2's mirror. `U.signals` returns only the UP state, so both slopes are
        # recomputed from the tested primitive rather than changing a committed
        # signature three other runners depend on (D212).
        n, T = panel.closes.shape
        g_lo = np.full((n, T), np.nan)
        g_hi = np.full((n, T), np.nan)
        i_lo = np.full((n, T), np.nan)
        atr = np.full((n, T), np.nan)
        from backtest_framework.research.structure import pivots
        for i, sym in enumerate(panel.symbols):
            ps = pivots(cleaned[sym], U.K)
            li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
            hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
            g_lo[i], i_lo[i] = U.rolling_fit(
                T, li, np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([]), U.K)
            g_hi[i], _ = U.rolling_fit(
                T, hj, np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([]), U.K)
            atr[i] = U.atr_log(cleaned[sym], U.ATR_WINDOW)
        sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr))

        # the UP reconstruction is verified against the committed one, so the DOWN
        # mirror is known to be built from the same parts
        up = (g_lo > 0) & (g_hi > 0) & sok
        up[:, :start] = False
        up_ref, _, _, _ = U.signals(panel, cleaned, start)
        assert np.array_equal(up, up_ref), "UP reconstruction diverged from U.signals"

        down = (g_lo < 0) & (g_hi < 0) & sok
        down[:, :start] = False
        pos_down, _, _ = U.walk(panel, down, g_lo, i_lo, atr, start)
        s2 = -pos_down

        # FCFS on the MAGNITUDE -- capital use is by size, not sign -- then negated
        granted, _ = B.allocate({"S1": -s1, "A2": -s2}, start, 1.0, {"S1": 0.0, "A2": 0.0})
        c = -(granted["S1"] + granted["A2"])

        ones = np.ones_like(s1)
        ones[:, :start] = 0.0
        return panel, start, {"S1_short": s1, "S2_short": s2, "C_short": c}, ones
    finally:
        (L.PPY, X.PPY, U.PPY, E.PPY, L.FIXTURE, L.EVENTS,
         X.RF_PER_BAR, X.BORROW_PER_BAR) = saved


# --------------------------------------------------------------------------
# TWO SIZING MODELS, and the study is forced to report both
# --------------------------------------------------------------------------
#
# MODEL A -- `run_short_mirror.signed_log_returns`: every coin is its own 1x
#   sub-account. D238 put a guard in it that raises when `1 + pos*expm1(r) <= 0`,
#   i.e. when a short loses more than everything on a single bar.
#
#   THE GUARD FIRES HERE, AND THAT IS THE RESULT RATHER THAN A BUG.
#   BTG-USD returned +215.1% on 2025-06-13 while S1_short held it short. A
#   full-notional short of that bar ends at an equity multiple of -1.15.
#   S1_short and C_short are RUINED under model A. S2_short survives its worst
#   bar (+70.9%, STEEM-USD 2022-04-21) with 29% of capital left.
#
# MODEL B -- one pooled account, 1/n notional per coin. It survives, so the cells
#   can be scored at all. THIS IS A MODELLING CHOICE FORCED BY THE RUIN AND IT
#   FLATTERS THE ARMS: it assumes costless continuous rebalancing back to 1/n and
#   no margin call at any point inside a bar. Every scored number below is model B.
#
# The model-A ruin is reported beside them and is not superseded by them.


def pooled_returns(panel, position: np.ndarray, start: int) -> np.ndarray:
    """Per-bar SIMPLE return of one pooled account holding 1/n notional per name."""
    sm = np.expm1(panel.total_log_returns)
    turn = np.abs(np.diff(position, axis=1, prepend=0.0))
    gross = (position * sm).mean(axis=0)
    cost = (panel.cost_fraction[:, None] * turn).mean(axis=0)
    return (gross - cost)[start:]


def _legs(position: np.ndarray, start: int):
    live = position[:, start:]
    return (float(np.maximum(live, 0.0).mean()), float(np.maximum(-live, 0.0).mean()))


def pooled_score(panel, position: np.ndarray, start: int) -> dict:
    r = pooled_returns(panel, position, start)
    long_f, short_f = _legs(position, start)
    rf = math.expm1(math.log1p(RF_ANNUAL) / PPY_CRYPTO)
    bor = math.expm1(math.log1p(BORROW_CRYPTO) / PPY_CRYPTO)
    ex = r - long_f * rf - short_f * bor
    sd = float(np.std(ex, ddof=1))
    eq = np.cumprod(1.0 + r)
    yrs = len(r) / PPY_CRYPTO
    dd = eq / np.maximum.accumulate(eq) - 1.0
    active = (position != 0.0).astype(float)
    entries = np.sum(np.diff(active, axis=1, prepend=0.0)[:, start:] > 0.0, axis=1)
    be = None
    if short_f > 0.0:
        slack = (float(np.mean(r)) - long_f * rf) / short_f
        if slack > -1.0:
            be = float(np.expm1(math.log1p(slack) * PPY_CRYPTO))
    return {
        "excess_sharpe": (float(np.mean(ex)) / sd * math.sqrt(PPY_CRYPTO)) if sd > 0 else 0.0,
        "terminal_multiple": float(eq[-1]),
        "cagr": float(eq[-1] ** (1.0 / yrs) - 1.0),
        "total_return": float(eq[-1] - 1.0),
        "vol": float(np.std(r, ddof=1) * math.sqrt(PPY_CRYPTO)),
        "max_drawdown": float(dd.min()),
        "worst_bar": float(r.min()),
        "exposure_gross": long_f + short_f,
        "entries": int(entries.sum()),
        "min_entries_per_symbol": int(entries.min()),
        "turnover_units": float(np.abs(np.diff(position, axis=1)).sum()),
        "breakeven_borrow_annual": be,
        "clears_E": bool(entries.sum() >= 100 and entries.min() >= 30),
    }


def model_a_ruin(panel, position: np.ndarray, start: int) -> dict:
    """Does a FULL-NOTIONAL short of any one name lose more than everything?"""
    sm = np.expm1(panel.total_log_returns)[:, start:]
    live = position[:, start:]
    rise = np.where(live < 0, sm, -np.inf)
    w = float(rise.max())
    i, t = np.unravel_index(int(np.argmax(rise)), rise.shape)
    return {
        "worst_adverse_bar": w, "symbol": str(panel.symbols[i]),
        "date": str(panel.dates[start + t])[:10],
        "equity_multiple_at_1x": 1.0 - w, "ruined_at_1x": bool(w >= 1.0),
        "max_survivable_notional": float(1.0 / w) if w > 0 else None,
    }


def pooled_rotation_nulls(panel, positions: dict, start: int) -> dict:
    """Matched-count rotation null under model B. Same exposure, same turnover,
    same holding periods, WRONG BARS -- so it earns the universe's drift too,
    which is the only reason a short book on a falling universe can be judged."""
    rng = np.random.default_rng(SEED)
    names = list(positions)
    n = panel.closes.shape[0]
    per = {k: np.empty(N_SIMS) for k in names}
    money = {k: np.empty(N_SIMS) for k in names}
    for k in names:
        src = positions[k][:, start:]
        W = src.shape[1]
        rot = np.zeros_like(positions[k])
        for s in range(N_SIMS):
            off = rng.integers(0, W, size=n)
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(off[i]))
            sc = pooled_score(panel, rot, start)
            per[k][s] = sc["excess_sharpe"]
            money[k][s] = sc["total_return"]
    return {"n_sims": N_SIMS, "draws": per, "money": money}


# --------------------------------------------------------------------------
# R10 -- concurrency, actual against a per-symbol-rotated book
# --------------------------------------------------------------------------


def concurrency(position: np.ndarray, start: int, rng) -> dict:
    live = position[:, start:]
    held = (live != 0.0)
    n, T = held.shape
    rot = np.empty_like(held)
    for i in range(n):
        rot[i] = np.roll(held[i], int(rng.integers(0, T)))
    a, r = held.sum(axis=0), rot.sum(axis=0)
    line = max(n // 3, 1)
    return {
        "names": n, "line": line,
        "mean": float(a.mean()), "max": int(a.max()),
        "over_line": float(np.mean(a > line)),
        "rot_mean": float(r.mean()), "rot_max": int(r.max()),
        "rot_over_line": float(np.mean(r > line)),
        "sd_ratio": float(a.std() / r.std()) if r.std() > 0 else float("nan"),
    }


def effective_instruments(panel, start: int) -> float:
    r = panel.log_returns[:, start:]
    R = np.corrcoef(r)
    n = R.shape[0]
    return float(n * n / R.sum())


def universe_drift(panel, start: int) -> dict:
    """Named in D253 BEFORE the run: if the universe fell, a short earns by existing."""
    tot = panel.total_log_returns[:, start:]
    per = np.expm1(tot.mean(axis=1) * PPY_CRYPTO)
    return {
        "equal_weighted_cagr": float(np.expm1(tot.mean() * PPY_CRYPTO)),
        "median_symbol_cagr": float(np.median(per)),
        "symbols_that_fell": int((per < 0).sum()),
        "n_symbols": int(per.shape[0]),
    }


# --------------------------------------------------------------------------


def build() -> dict:
    t0 = time.time()
    saved_ppy, saved_rf, saved_bor = X.PPY, X.RF_PER_BAR, X.BORROW_PER_BAR
    panel, start, books, ones = books_on_crypto()

    # score inside the overrides
    X.PPY = PPY_CRYPTO
    X.RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY_CRYPTO
    X.BORROW_PER_BAR = math.log1p(BORROW_CRYPTO) / PPY_CRYPTO
    try:
        drift = universe_drift(panel, start)
        cells = {k: pooled_score(panel, v, start) for k, v in books.items()}
        cells["SHORT_ALL"] = pooled_score(panel, -ones, start)
        cells["B&H"] = pooled_score(panel, ones, start)
        ruin = {k: model_a_ruin(panel, v, start) for k, v in books.items()}
        nulls = pooled_rotation_nulls(panel, books, start)
        rng = np.random.default_rng(SEED)
        conc = {k: concurrency(v, start, rng) for k, v in books.items()}
        eff = effective_instruments(panel, start)
    finally:
        X.PPY, X.RF_PER_BAR, X.BORROW_PER_BAR = saved_ppy, saved_rf, saved_bor

    assert X.PPY == saved_ppy and X.BORROW_PER_BAR == saved_bor, "overrides leaked"
    assert L.FIXTURE != C.FIXTURE, "fixture override leaked"

    draws, money = nulls["draws"], nulls["money"]
    verdict = {}
    for k in CELL_ORDER:
        s_pct = float((np.asarray(draws[k]) < cells[k]["excess_sharpe"]).mean() * 100.0)
        m_pct = float((np.asarray(money[k]) < cells[k]["total_return"]).mean() * 100.0)
        verdict[k] = {
            "sharpe_pct": s_pct, "money_pct": m_pct,
            "clears_H": bool(s_pct >= 95.0 and m_pct >= 95.0),
            "null_sharpe_p95": float(np.percentile(draws[k], 95)),
            "null_money_p95": float(np.percentile(money[k], 95)),
        }
    best = np.max(np.vstack([np.asarray(draws[k]) for k in CELL_ORDER]), axis=0)
    best_floor = float(np.percentile(best, 95))

    n, T = panel.closes.shape
    payload = {
        "study": "D253", "seed": SEED, "n_sims": N_SIMS,
        "fixture": C.FIXTURE.name, "n_symbols": n, "bars": T, "start": start,
        "years": (T - start) / PPY_CRYPTO,
        "ppy": PPY_CRYPTO, "fee_bps": FEE_BPS,
        "borrow_annual_assumed": BORROW_CRYPTO, "rf_annual": RF_ANNUAL,
        "universe_drift": drift,
        "effective_instruments": eff,
        "cells": cells, "verdict": verdict, "concurrency": conc, "model_a_ruin": ruin,
        "best_of_floor_p95": best_floor,
        "any_clears_H": bool(any(verdict[k]["clears_H"] for k in CELL_ORDER)),
        "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    d, L_ = p["universe_drift"], []
    a = L_.append
    a("# D253 — the short sides of S1 and S2, on crypto\n")
    a(f"**Produced by** `scripts/run_book_shorts_crypto.py` · seed {p['seed']} · "
      f"{p['n_sims']:,} null draws · {p['seconds']:.1f}s\n")
    a(f"`{p['fixture']}` — **{p['n_symbols']} coins x {p['bars']:,} bars**, "
      f"{p['years']:.2f} live years from bar {p['start']:,}. "
      f"PPY {p['ppy']:.0f}, fees {p['fee_bps']:.0f} bp/side, "
      f"borrow **{p['borrow_annual_assumed']:.0%}/yr (assumed)**.\n")

    a("\n## The drift confound, measured before any cell is read\n")
    a(f"Equal-weighted universe CAGR **{d['equal_weighted_cagr']:+.2%}**, "
      f"median symbol **{d['median_symbol_cagr']:+.2%}**, "
      f"**{d['symbols_that_fell']} of {d['n_symbols']} coins fell**.\n")
    a("\n**A short book on a falling universe earns by existing.** The rotation null holds the "
      "same exposure, turnover and holding periods on the wrong bars, so it earns that drift too. "
      "**Only the excess over the null is evidence** — which is what hurdle H reads.\n")
    a(f"\n`SHORT_ALL` — short everything, always — is reported below as the drift benchmark: "
      f"**{p['cells']['SHORT_ALL']['cagr']:+.2%} CAGR**. A cell that does not clearly beat it "
      "has found nothing.\n")
    a(f"\nEffective independent instruments: **{p['effective_instruments']:.2f}** of "
      f"{p['n_symbols']}. Pooled trade counts are not sample sizes.\n")

    a("\n## Cells\n")
    a("| cell | exposure | CAGR | excess Sharpe | vol | max DD | entries | min/sym | "
      "breakeven borrow |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in list(CELL_ORDER) + ["SHORT_ALL", "B&H"]:
        c = p["cells"][k]
        be = c.get("breakeven_borrow_annual")
        a(f"| {'**'+k+'**' if k in CELL_ORDER else '*'+k+'*'} | "
          f"{c['exposure_gross']:.1%} | {c['cagr']:+.2%} | {c['excess_sharpe']:+.3f} | "
          f"{c['vol']:.1%} | {c['max_drawdown']:.2%} | {c['entries']:,} | "
          f"{c['min_entries_per_symbol']:,} | "
          f"{('%.1f%%' % (be*100)) if be is not None else '—'} |")

    a("\n## Hurdle H — the matched-count rotation null, BOTH legs\n")
    a("| cell | Sharpe pct | money pct | clears H |")
    a("|---|---:|---:|:--:|")
    for k in CELL_ORDER:
        v = p["verdict"][k]
        a(f"| {k} | {v['sharpe_pct']:.1f}th | {v['money_pct']:.1f}th | "
          f"{'**YES**' if v['clears_H'] else 'no'} |")
    a(f"\nBest-of-three floor (D228), p95: **{p['best_of_floor_p95']:+.3f}**.\n")

    a("\n## R10 — concurrency, actual against a per-symbol-rotated book\n")
    a("| cell | mean held | max | over ⅓ of universe | *rotated mean* | *rotated max* | "
      "*rotated over ⅓* | sd ratio |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        c = p["concurrency"][k]
        a(f"| {k} | {c['mean']:.1f} | **{c['max']}** of {c['names']} | {c['over_line']:.1%} | "
          f"*{c['rot_mean']:.1f}* | *{c['rot_max']}* | *{c['rot_over_line']:.1%}* | "
          f"{c['sd_ratio']:.2f}x |")

    a(f"\n## Verdict\n")
    a("**" + ("At least one cell clears H on both legs."
              if p["any_clears_H"] else
              "NO CELL CLEARS H ON BOTH LEGS. Per D253's stop, this is CLOSED — no fourth "
              "cell, no calendar-matched variant, no move to the 63-name universe as a rescue.")
      + "**\n")
    return "\n".join(L_) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    d = p["universe_drift"]
    print(f"universe CAGR {d['equal_weighted_cagr']:+.2%}, "
          f"{d['symbols_that_fell']}/{d['n_symbols']} coins fell; "
          f"SHORT_ALL {p['cells']['SHORT_ALL']['cagr']:+.2%}")
    for k in CELL_ORDER:
        c, v = p["cells"][k], p["verdict"][k]
        print(f"  {k:10} expo {c['exposure_gross']:5.1%}  CAGR {c['cagr']:+7.2%}  "
              f"exSharpe {c['excess_sharpe']:+6.3f}  "
              f"null {v['sharpe_pct']:5.1f}th/{v['money_pct']:5.1f}th  "
              f"{'CLEARS' if v['clears_H'] else 'no'}")
    print("ANY CELL CLEARS H:" , p["any_clears_H"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
