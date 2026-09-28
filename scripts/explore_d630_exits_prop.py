"""POST HOC, on D630's spent in-sample: do the stop, target and trailing-stop exits make the FULL NG contract survive the
prop-account lifecycle? (The principal, 2026-09-28.) Exploratory: it admits nothing and changes no verdict.

    uv run python scripts/explore_d630_exits_prop.py [--paths 3000] [--workers 8]   # -> data/ledger_d630_exits_prop.json

THE TRADES: D630's 1,028, with each exit rule of `explore_d630_exits_micro.exit_money` (stop / target at k x |I|,
the ratcheting trailing stop). Each day's path for the account is (low, high, end) in full-contract dollars from the
fill to the exit bar:
- bars before the exit bar contribute both extremes;
- the exit bar: a stop exit books the stop and clips the adverse side there (the account is flat beyond it) but keeps
  the bar's favourable extreme (it may have come first, and it raises an intraday trailing drawdown's high-water mark);
  a target exit books the target and clips the favourable side there but keeps the bar's adverse extreme;
- a time exit: every bar to 14:29, exactly as `explore_d630_prop_lifecycle.trade_paths`.

THE ACCOUNT: `explore_d630_prop_lifecycle`'s machinery unchanged (D440's simulate_provider over D386's fourteen plans,
D493's `cell` and `provider_measured`, its cost convention and bar: V > 2 SE, P3 worst day >= -2%, life >= 3 years),
full NG only, n = 1, 2, 3, 5, all years and without 2022.

KNOWN ANSWERS (raise): the time exit's paths equal `explore_d630_prop_lifecycle.trade_paths` on every day; every
variant's end equals `explore_d630_exits_micro.exit_money` on every trade; the lifecycle's P1 gate passes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "ledger_d630_exits_prop.json"
EXITS = {"time exit only (D630 primary)": (None, None, False), "stop 1x": (1.0, None, False),
         "target 1x": (None, 1.0, False), "stop 1x + target 1x (book frame)": (1.0, 1.0, False),
         "trailing stop 1x": (1.0, None, True), "trailing stop 1x + target 1x": (1.0, 1.0, True),
         "stop 2x": (2.0, None, False), "trailing stop 2x": (2.0, None, True)}


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


X = _load("explore_d630_exits_micro", "explore_d630_exits_micro.py")  # repoints D630's inputs to the main checkout
R = X.R
L = _load("explore_d630_prop_lifecycle", "explore_d630_prop_lifecycle.py")


class PropExitError(RuntimeError):
    pass


def path(dr: float, fill: float, exit_px: float, absI: float, mins: np.ndarray, hi: np.ndarray, lo: np.ndarray,
         t0: str, ks: float | None, kt: float | None, trail: bool) -> tuple[float, float, float]:
    """(end, mae, mfe) in full-contract gross dollars, with the exit rule of exit_money."""
    stop = fill - dr * ks * absI if ks is not None else None
    tgt = fill + dr * kt * absI if kt is not None else None
    best_px = fill
    first = R.add_min(t0, 2)
    worst, best = 0.0, 0.0
    end = None
    for m, h, lw in zip(mins, hi, lo):
        if m < first or m >= R.EXIT_END:
            continue
        adv, fav = (lw, h) if dr > 0 else (h, lw)
        hit_s = stop is not None and ((lw <= stop) if dr > 0 else (h >= stop))
        hit_t = tgt is not None and m < R.W_START and ((h >= tgt) if dr > 0 else (lw <= tgt))
        if hit_s:
            end = R.money(dr, fill, stop)
            worst, best = min(worst, end), max(best, R.money(dr, fill, fav))
            break
        if hit_t:
            end = R.money(dr, fill, tgt)
            worst, best = min(worst, R.money(dr, fill, adv)), max(best, end)
            break
        worst, best = min(worst, R.money(dr, fill, adv)), max(best, R.money(dr, fill, fav))
        if trail and stop is not None:
            best_px = max(best_px, h) if dr > 0 else min(best_px, lw)
            stop = max(stop, best_px - ks * absI) if dr > 0 else min(stop, best_px + ks * absI)
    if end is None:
        end = R.money(dr, fill, exit_px)
    return end, min(worst, 0.0, end), max(best, 0.0, end)


def frames() -> dict[str, pd.DataFrame]:
    d, rows = X.trades()
    base = L.trade_paths()
    tr = d["traded"].to_numpy() & np.isfinite(R.signed(d))
    out = {}
    for name, (ks, kt, trail) in EXITS.items():
        g, mae, mfe = np.zeros(len(d)), np.zeros(len(d)), np.zeros(len(d))
        for r in rows:
            e, a, b = path(r["dir"], r["fill"], r["exit"], r["absI"], r["mins"], r["hi"], r["lo"], r["t0"], ks, kt, trail)
            ref = X.exit_money(r["dir"], r["fill"], r["exit"], r["absI"], r["mins"], r["hi"], r["lo"], r["t0"], ks, kt,
                               trail=trail)[0]
            if e != ref:
                raise PropExitError(f"known answer: {name} {r['day']} end {e} against exit_money's {ref}")
            g[r["i"]], mae[r["i"]], mfe[r["i"]] = e, a, b
        t = pd.DataFrame({"day": d["day"].to_numpy(), "traded": tr, "g": g, "mae": mae, "mfe": mfe})
        if ks is None and kt is None:
            for c in ("traded", "g", "mae", "mfe"):
                if not np.array_equal(t[c].to_numpy(), base[c].to_numpy()):
                    raise PropExitError(f"known answer: the time exit's {c} differs from the lifecycle study's paths")
        out[name] = t
    return out


def job(args: tuple[str, str, pd.DataFrame, int]) -> list[dict[str, Any]]:
    name, variant, t, n_paths = args
    D93 = L._load("run_d493", "run_d493_account_size.py")
    D40 = L._load("d440l", "d440_lifecycle.py")
    res = []
    for n in L.NS:
        h = L.days_for(t, "full", n, variant)
        sd = float(h["d_end"].std(ddof=1))
        years = h["day"].str[:4].nunique()
        cum = np.cumsum(h["d_end"].to_numpy())
        for p in D40.D386.PLANS:
            prov, npth = D93.provider_measured(h, n_paths)
            c = D93.cell(D40, p, h, prov, npth, n_paths, sd)
            c.update(exit=name, variant=variant, n=n, plan=f"{p.firm} {p.size // 1000}k", dd_fund=p.dd_fund,
                     P3_breaches_per_year=c["P3_days_below_2pct"] / years,
                     worst_day_low_usd=float(h["d_low"].min()),
                     max_dd_closed_usd=float((cum - np.maximum.accumulate(cum)).min()))
            res.append(c)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=3000)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()
    D40 = L._load("d440l", "d440_lifecycle.py")
    fails = D40.p1_gate(verbose=False)
    if fails:
        raise PropExitError(f"[P1] {fails}")
    fr = frames()
    print(f"known answers hold: the time exit equals the lifecycle study's paths; every end equals exit_money "
          f"({time.time() - t0:.0f} s)", flush=True)
    jobs = [(name, v, fr[name], a.paths) for name in EXITS for v in L.VARIANTS]
    cells: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for part in ex.map(job, jobs):
            cells.extend(part)
    df = pd.DataFrame(cells)
    summary = {}
    for name, t in fr.items():
        tr = t["traded"].to_numpy()
        low = np.where(tr, t["mae"] - R.COST, 0.0)
        end = np.where(tr, t["g"] - R.COST, 0.0)
        summary[name] = {"mean_net_trade": float(end[tr].mean()), "daily_sd": float(end.std(ddof=1)),
                         "worst_day_low": float(low.min()), "p1_day_low": float(np.quantile(low[tr], 0.01)),
                         "days_low_below_1000": int((low < -1000).sum()), "days_low_below_2000": int((low < -2000).sum())}
    doc = {"record": "POST HOC on D630's spent in-sample; admits nothing", "exits": {k: list(v) for k, v in EXITS.items()},
           "bar": L._load("run_d493", "run_d493_account_size.py").BAR, "paths_summary_full_one_contract": summary,
           "cells": df.to_dict("records"), "clearing": df[df["clears"]].to_dict("records"),
           "wall_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("\nFull NG, one contract: the day's path")
    print(pd.DataFrame(summary).T.round(1).to_string())
    for variant in L.VARIANTS:
        print(f"\n[{variant}] cells clearing (V > 2 SE, P3 worst >= -2%, life >= 3 y) by exit and n:")
        g = df[df["variant"] == variant]
        print(g.pivot_table(index="exit", columns="n", values="clears", aggfunc="sum").to_string())
        print(f"\n[{variant}] n = 1: pass rate / breach rate / life (y) / V +- SE / P3 worst % by plan and exit")
        one = g[g["n"] == 1].copy()
        one["cell"] = one.apply(lambda r: f"{r['p_pass']:.2f}/{r['p_breached']:.2f}/{(r['life_years'] or 0):.1f}/"
                                          f"{r['V']:+.0f}+-{r['V_se']:.0f}/{r['P3_worst_pct']:.1f}", axis=1)
        with pd.option_context("display.width", 300, "display.max_colwidth", 40):
            print(one.pivot(index="plan", columns="exit", values="cell").to_string())
    print(f"\n{int(df['clears'].sum())} of {len(df)} cells clear; wrote {OUT.relative_to(REPO)} in {doc['wall_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
