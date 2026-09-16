"""D244 — the book on crypto.

    S1  position = +1 if hist_L > 0 AND md_L <= 0
    S2  UPTREND := g_lo > 0 AND g_hi > 0; enter at onset, exit at age 63 or state end
    C   S1 + S2 on one shared pool at 100% capital

Only the book. Zero fresh looks, no rule proposed, no rule changed.

THE ONE THING THAT CANNOT BE FROZEN IS CALENDAR MEANING. Bar counts are frozen,
but 252 bars is ONE YEAR on ETFs and 0.69 YEARS on a 365-day crypto calendar. The
book specifies BARS, so bars is what runs -- D221 established the indicator is
scale-free in bar counts. A calendar-matched 365/91 variant is NOT run here; if
this fails, that is a separate pre-registration and not a rescue.

THREE OVERRIDES, and each one is a place a study like this goes wrong:
  * FEE_BPS = 10 per side, `run_assembled_strategy`'s committed crypto constant,
    against the ETF book's derived ~1.6bp -- SIX TIMES the friction.
  * PPY = 365, because crypto trades 24/7.
  * a 34-coin panel intersected from 2018-01-01, chosen BY DATE (the earliest
    start retaining a majority of the 63) and never by performance.

The overrides are asserted to be OFF outside the crypto run. One that silently
persisted would corrupt every later study on the equity fixtures.

STAGE: an ASSET-CLASS holdout, NOT a time holdout. Crypto 2020-2025 overlaps the
ETF training window; D243 remains the only time-independent evidence.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import math
import sys
import time
from collections import defaultdict
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


E = _load("d243_extended", "run_book_extended.py")
B, U, X, L, S, J = E.B, E.U, E.X, E.L, E.S, E.J

SUMMARY = REPO / "data" / "book_crypto_summary.json"
RESULTS = REPO / "docs" / "results" / "BOOK_CRYPTO_RESULTS.md"
SRC = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
FIXTURE = REPO / "data" / "fixtures" / "crypto_book_2018_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_book_2018_raw_events.json"

SEED, N_SIMS = X.SEED, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL

PPY_CRYPTO = 365.0                 # D17's rule on crypto's 365-day calendar
FEE_BPS = 10.0                     # run_assembled_strategy's committed constant
START = "2018-01-01"               # the earliest start retaining a majority of 63
CELL_ORDER = ("S1", "S2", "C")
ARMS = ("S1", "S2")


def build_panel_fixture() -> dict:
    """The 34-coin intersection. Chosen BY DATE, never by performance.

    `load_panel` refuses a panel whose symbols have different bar counts, and the
    source fixture is deliberately NOT inner-joined (so no coin is truncated to
    another's inception). The intersection is taken here instead."""
    rows = defaultdict(dict)
    with gzip.open(SRC, "rt") as f:
        for r in csv.DictReader(f):
            if r["timestamp"][:10] >= START:
                rows[r["symbol"]][r["timestamp"][:10]] = r
    first = {s: min(v) for s, v in rows.items()}
    keep = sorted(s for s in rows if first[s] <= START[:4] + "-01-31")
    grid = sorted(set.intersection(*(set(rows[s]) for s in keep)))

    def write(dates):
        with gzip.open(FIXTURE, "wt", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
            for s in keep:
                for d in dates:
                    r = rows[s][d]
                    w.writerow([f"{d}T00:00:00", s, r["open"], r["high"], r["low"],
                                r["close"], r["volume"]])

    # ITERATE TO A FIXED POINT. `clean` drops bars per symbol -- non-finite OHLC,
    # low above high, non-positive volume, spikes -- so a raw date intersection
    # does NOT survive loading with equal bar counts, and `load_panel` refuses a
    # ragged panel. Removing a bar can also change whether its neighbours are
    # cleaned, so one pass is not guaranteed; this loops until stable.
    saved = L.FIXTURE
    try:
        L.FIXTURE = FIXTURE
        for _ in range(6):
            write(grid)
            cleaned, _ = L.clean(L.load_fixture_csv(FIXTURE))
            survive = set.intersection(
                *(set(tb.timestamp.isoformat()[:10] for tb in cleaned[s]) for s in keep))
            nxt = sorted(d for d in grid if d in survive)
            if len(nxt) == len(grid):
                break
            grid = nxt
        else:                                    # pragma: no cover - would mean churn
            raise SystemExit("the cleaned grid did not converge")
        write(grid)
    finally:
        L.FIXTURE = saved
    # Spot crypto has no dividends or splits, so the sidecar is empty BY
    # CONSTRUCTION (D108) rather than by omission.
    EVENTS.write_text(json.dumps({"dividends": {s: [] for s in keep},
                                  "splits": {s: [] for s in keep}},
                                 indent=1, sort_keys=True), encoding="utf-8")
    return {"symbols": keep, "bars": len(grid), "first": grid[0], "last": grid[-1]}


def books_on_crypto():
    """Load with the crypto overrides in place, then put them back.

    THE OVERRIDES ARE THE RISK. `PPY` and `cost_fraction` live on shared modules;
    one left switched on would silently corrupt every later equity study. They are
    restored in a `finally` and asserted afterwards."""
    saved = (L.PPY, X.PPY, U.PPY, E.PPY, L.FIXTURE, L.EVENTS)
    try:
        L.PPY = X.PPY = U.PPY = E.PPY = PPY_CRYPTO
        X.RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY_CRYPTO
        L.FIXTURE, L.EVENTS = FIXTURE, EVENTS
        panel, cleaned = L.load_panel()
        # the ETF commission schedule is meaningless here -- replace it outright
        panel = type(panel)(
            symbols=panel.symbols, closes=panel.closes, log_returns=panel.log_returns,
            cost_fraction=np.full(len(panel.symbols), FEE_BPS / 1e4),
            dates=panel.dates, total_log_returns=panel.total_log_returns,
        )
        start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
        md, hs, ok = S.base_masks(panel, cleaned, start)
        s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
        up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
        s2, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
        granted, _ = B.allocate({"S1": s1, "A2": s2}, start, 1.0, {"S1": 0.0, "A2": 0.0})
        c = granted["S1"] + granted["A2"]
        ones = np.ones_like(s1)
        ones[:, :start] = 0.0
        return panel, start, {"S1": s1, "S2": s2, "C": c}, ones
    finally:
        L.PPY, X.PPY, U.PPY, E.PPY, L.FIXTURE, L.EVENTS = saved
        X.RF_PER_BAR = math.log1p(RF_ANNUAL) / L.PPY


def build() -> dict:
    t0 = time.time()
    meta = build_panel_fixture()

    # The overrides must be live only inside the crypto block. Score there.
    saved_ppy = X.PPY
    panel, start, books, ones = books_on_crypto()
    X.PPY = PPY_CRYPTO
    X.RF_PER_BAR = math.log1p(RF_ANNUAL) / PPY_CRYPTO
    try:
        cells = {k: X.score(panel, books[k], start) for k in CELL_ORDER}
        bh = X.score(panel, ones, start)
        # BTC alone needs its OWN panel. Zeroing 34 of 35 rows leaves
        # `portfolio_log_returns` dividing by 35, so it would score BTC at 1/35
        # weight -- the same defect `subset_panel` was written for in D239.
        btc = None
        if "BTC-USD" in panel.symbols:
            i = panel.symbols.index("BTC-USD")
            solo_panel = type(panel)(
                symbols=(panel.symbols[i],), closes=panel.closes[[i]],
                log_returns=panel.log_returns[[i]],
                cost_fraction=panel.cost_fraction[[i]], dates=panel.dates,
                total_log_returns=panel.total_log_returns[[i]],
            )
            held = np.zeros((1, panel.closes.shape[1]))
            held[0, start:] = 1.0
            btc = X.score(solo_panel, held, start)

        def ex_of(pos):
            tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
            return X.excess_of(tot, pos, start)

        r = {k: ex_of(books[k]) for k in CELL_ORDER}
        r["BH"] = ex_of(ones)

        nl = X.rotation_nulls(panel, {k: books[k] for k in CELL_ORDER}, start)
        nulls = {}
        for k, draws in nl["draws"].items():
            a = cells[k]["excess_sharpe"]
            nulls[k] = {"p50": float(np.percentile(draws, 50)),
                        "p95": float(np.percentile(draws, 95)),
                        "percentile_of_actual": float((draws < a).mean() * 100.0),
                        "money_percentile_of_actual": float(
                            (nl["money"][k] < cells[k]["total_return"]).mean() * 100.0),
                        "vol_ratio": float(cells[k]["vol"] / np.percentile(nl["vol"][k], 50)),
                        "clears_X2": bool(a > float(np.percentile(draws, 95)))}

        def _sh(v):
            sd = float(np.std(v, ddof=1))
            return float(np.mean(v) / sd * math.sqrt(PPY_CRYPTO)) if sd > 0 else 0.0

        nlen = len(r["S1"])
        nblk = math.ceil(nlen / J.BLOCK)
        rb = np.random.default_rng(SEED)
        idxs = [(rb.integers(0, nlen - J.BLOCK + 1, size=nblk)[:, None]
                 + np.arange(J.BLOCK)[None, :]).ravel()[:nlen] for _ in range(J.N_BOOT)]
        boot = {}
        for k in CELL_ORDER:
            own = np.array([_sh(r[k][i]) for i in idxs])
            dbh = np.array([_sh(r[k][i]) - _sh(r["BH"][i]) for i in idxs])
            boot[k] = {"p05": float(np.percentile(own, 5)),
                       "p95": float(np.percentile(own, 95)),
                       "clears_X3": bool(np.percentile(own, 5) > 0.0),
                       "delta_bh": _sh(r[k]) - _sh(r["BH"]),
                       "delta_bh_p05": float(np.percentile(dbh, 5)),
                       "delta_bh_excludes_zero": bool(np.percentile(dbh, 5) > 0.0)}

        # breakeven cost: the per-side bps at which each arm's excess return hits zero
        breakeven = {}
        for k in CELL_ORDER:
            tot = X.signed_log_returns(panel, books[k], total_return=True)[start:]
            gross_turn = float(np.abs(np.diff(books[k], axis=1, prepend=0.0))[:, start:].sum())
            n_bars = len(tot)
            paid = -math.log1p(-FEE_BPS / 1e4) * gross_turn / len(panel.symbols)
            long_f = cells[k]["exposure_gross"]
            net_excess = float(np.sum(tot)) - long_f * X.RF_PER_BAR * n_bars
            per_unit = gross_turn / len(panel.symbols)
            breakeven[k] = (1e4 * (1 - math.exp(-(net_excess + paid) / per_unit))
                            if per_unit > 0 else None)

        verdict = {}
        for k in ARMS:
            d = cells[k]["excess_sharpe"] - bh["excess_sharpe"]
            verdict[k] = {"delta_vs_bh": d,
                          "clears_X1": bool(cells[k]["excess_sharpe"] > 0 and d > 0),
                          "clears_X2": nulls[k]["clears_X2"],
                          "clears_X3": boot[k]["clears_X3"]}
            verdict[k]["clears_all"] = bool(verdict[k]["clears_X1"] and verdict[k]["clears_X2"]
                                            and verdict[k]["clears_X3"])
        rho = float(np.corrcoef(r["S1"], r["S2"])[0, 1])
        years = (len(panel.dates) - start) / PPY_CRYPTO
        dep = {k: float(np.expm1(np.log1p(cells[k]["cagr"])
                                 + math.log1p(RF_ANNUAL) * (1 - cells[k]["exposure_gross"])))
               for k in CELL_ORDER}
    finally:
        X.PPY = saved_ppy
        X.RF_PER_BAR = math.log1p(RF_ANNUAL) / L.PPY

    # the overrides must be OFF again
    assert X.PPY == L.PPY == 252, "a crypto override leaked into the shared modules"

    both = (verdict["S1"]["clears_X1"] and verdict["S1"]["clears_X2"],
            verdict["S2"]["clears_X1"] and verdict["S2"]["clears_X2"])
    reading = {
        (True, True): "BOTH RULES TRAVEL TO A DIFFERENT ASSET CLASS. They are about price "
                      "behaviour, not about US equity ETFs.",
        (True, False): "S1 TRAVELS; S2 DOES NOT. The reversal thesis generalises and the "
                       "continuation one is equity-specific.",
        (False, True): "S2 TRAVELS; S1 DOES NOT. After D243 that is two failures for S1 in a "
                       "row, on the asset class most suited to it.",
        (False, False): "NEITHER RULE TRAVELS. Both are about US equity ETFs.",
    }[both]

    return {
        "produced": "D244", "stage": "ASSET-CLASS holdout -- not a time holdout",
        "seed": SEED, "n_sims": N_SIMS, "ppy": PPY_CRYPTO, "fee_bps": FEE_BPS,
        "universe": meta, "n_symbols": len(panel.symbols),
        "live_bars": len(panel.dates) - start, "live_years": years,
        "first_live": panel.dates[start][:10], "last_bar": panel.dates[-1][:10],
        "cells": cells, "buy_and_hold": bh, "btc_only": btc,
        "nulls": nulls, "bootstrap": boot, "verdict": verdict,
        "breakeven_bps": breakeven, "rho_S1_S2": rho, "deployable_return": dep,
        "reading": reading, "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, n, v, bt = p["cells"], p["nulls"], p["verdict"], p["bootstrap"]
    bh, dep, u = p["buy_and_hold"], p["deployable_return"], p["universe"]
    o = ["# D244 — the book on crypto\n"]
    o.append("**AN ASSET-CLASS HOLDOUT — not a time holdout.** Crypto 2020–2025 overlaps the "
             "ETF training window; D243 remains the only time-independent evidence.\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} coins x {p['live_bars']:,} live bars "
        f"({p['live_years']:.1f}y at PPY {p['ppy']:.0f}), {p['first_live']} .. {p['last_bar']}. "
        f"Costs **{p['fee_bps']:.0f} bp/side** against the ETF book's ~1.6. "
        f"Only the book — zero fresh looks.*\n"
    )
    o.append(
        f"**Universe chosen by date, never by performance:** every coin with history from "
        f"{u['first']}, being the earliest start that retains a majority of the 63. "
        f"**Not survivorship-cleaned** — it holds LUNC, USTC and FTT.\n"
    )
    o.append("## The book on crypto\n")
    o.append("| | exposure | excess Sharpe | Δ vs B&H | CAGR | deployable | vol | max DD | "
             "Calmar | E |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = c[k]
        d = x["excess_sharpe"] - bh["excess_sharpe"]
        o.append(
            f"| **{k}** | {x['exposure_gross']:.1%} | **{x['excess_sharpe']:+.3f}** | "
            f"{d:+.3f} | {x['cagr'] * 100:.2f}% | **{dep[k] * 100:.2f}%** | "
            f"{x['vol'] * 100:.1f}% | {x['max_drawdown'] * 100:+.2f}% | "
            f"{x['cagr'] / abs(x['max_drawdown']):.3f} | "
            f"{'✓' if x['clears_E'] else '✗'} ({x['min_entries_per_symbol']}) |")
    o.append(
        f"| *B&H, equal-weighted* | *100.0%* | *{bh['excess_sharpe']:+.3f}* | — | "
        f"*{bh['cagr'] * 100:.2f}%* | *{bh['cagr'] * 100:.2f}%* | *{bh['vol'] * 100:.1f}%* | "
        f"*{bh['max_drawdown'] * 100:+.2f}%* | "
        f"*{bh['cagr'] / abs(bh['max_drawdown']):.3f}* | — |")
    if p["btc_only"]:
        b = p["btc_only"]
        o.append(
            f"| *BTC alone* | *100.0%* | *{b['excess_sharpe']:+.3f}* | — | "
            f"*{b['cagr'] * 100:.2f}%* | *{b['cagr'] * 100:.2f}%* | *{b['vol'] * 100:.1f}%* | "
            f"*{b['max_drawdown'] * 100:+.2f}%* | "
            f"*{b['cagr'] / abs(b['max_drawdown']):.3f}* | — |")
    o.append("")

    o.append("## The hurdles\n")
    o.append("| | X1 beats B&H | X2 rotation null | pctile | money pct | X3 boot p05 | "
             "**all** |")
    o.append("|---|:--:|:--:|---:|---:|---:|:--:|")
    for k in ARMS:
        q, nn = v[k], n[k]
        o.append(
            f"| **{k}** | {'✓' if q['clears_X1'] else '✗'} | "
            f"{'✓' if q['clears_X2'] else '✗'} | **{nn['percentile_of_actual']:.1f}th** | "
            f"{nn['money_percentile_of_actual']:.1f}th | "
            f"{bt[k]['p05']:+.3f} {'✓' if q['clears_X3'] else '✗'} | "
            f"**{'✓' if q['clears_all'] else '✗'}** |")
    o.append(
        f"| *C* | — | {'✓' if n['C']['clears_X2'] else '✗'} | "
        f"*{n['C']['percentile_of_actual']:.1f}th* | "
        f"*{n['C']['money_percentile_of_actual']:.1f}th* | "
        f"*{bt['C']['p05']:+.3f}* | — |")
    o.append("")

    o.append("## Costs — the thing most likely to have killed it\n")
    o.append("| | charged | **breakeven** | headroom |")
    o.append("|---|---:|---:|---:|")
    fee = p["fee_bps"]
    for k in CELL_ORDER:
        be = p["breakeven_bps"][k]
        head = f"{be / fee:.2f}x" if be is not None and fee else "—"
        o.append(f"| **{k}** | {fee:.0f} bp | "
                 f"**{f'{be:.1f} bp' if be is not None else '—'}** | {head} |")
    o.append("")
    o.append("*Breakeven is the per-side cost at which the arm's excess return reaches zero. "
             "Below 10 bp means costs alone sink it.*\n")
    o.append(f"**ρ between S1 and S2 on crypto: `{p['rho_S1_S2']:+.4f}`** "
             f"(ETFs: +0.159, +0.175, +0.123).\n")
    o.append("## The reading, as declared in advance\n")
    o.append(f"> **{p['reading']}**\n")
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

    c, n, v, bt, dep = (payload["cells"], payload["nulls"], payload["verdict"],
                        payload["bootstrap"], payload["deployable_return"])
    print()
    print(f"{payload['n_symbols']} coins, {payload['live_bars']:,} live bars "
          f"({payload['live_years']:.1f}y), {payload['first_live']} .. {payload['last_bar']}, "
          f"{payload['fee_bps']:.0f}bp/side")
    print()
    print(f"{'':5s} {'expo':>7s} {'exSh':>8s} {'dBH':>8s} {'CAGR':>9s} {'deploy':>8s} "
          f"{'maxDD':>9s} {'pctile':>8s} {'p05':>8s}  X1 X2 X3")
    for k in CELL_ORDER:
        x = c[k]
        q = v.get(k)
        print(f"{k:5s} {x['exposure_gross']:7.1%} {x['excess_sharpe']:+8.3f} "
              f"{x['excess_sharpe'] - payload['buy_and_hold']['excess_sharpe']:+8.3f} "
              f"{x['cagr']:9.2%} {dep[k]:8.2%} {x['max_drawdown']:+9.2%} "
              f"{n[k]['percentile_of_actual']:7.1f}th {bt[k]['p05']:+8.3f}"
              + (f"  {'Y' if q['clears_X1'] else 'N'}  {'Y' if q['clears_X2'] else 'N'}  "
                 f"{'Y' if q['clears_X3'] else 'N'}" if q else ""))
    b = payload["buy_and_hold"]
    print(f"{'B&H':5s} {1.0:6.1%} {b['excess_sharpe']:+8.3f} {'—':>8s} {b['cagr']:9.2%} "
          f"{b['cagr']:8.2%} {b['max_drawdown']:+9.2%}")
    if payload["btc_only"]:
        t = payload["btc_only"]
        print(f"{'BTC':5s} {1.0:6.1%} {t['excess_sharpe']:+8.3f} {'—':>8s} {t['cagr']:9.2%} "
              f"{t['cagr']:8.2%} {t['max_drawdown']:+9.2%}")
    print()
    print("breakeven cost:", {k: (round(x, 1) if x is not None else None)
                              for k, x in payload["breakeven_bps"].items()}, "bp/side")
    print(f"rho(S1,S2) = {payload['rho_S1_S2']:+.4f}")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
