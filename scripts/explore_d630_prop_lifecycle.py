"""POST HOC, on D630's spent in-sample: D630's NG settlement trade (Stage A) through the prop-account lifecycle.

It runs D493's machinery: D440's `simulate_provider` over D386's fourteen plans, and D493's `cell` and
`provider_measured`. The input is D630's own trade series, one full NG and one MNG, at n = 1, 2, 3 and 5 contracts.
Each day's path (low, high, end) comes from D630's own minute bars between the fill and the exit. Untraded days are
zero days, so an account lives through them. It admits nothing and changes no verdict.

Known answers (raise): the trade series reproduces D630's published gate mean and n, the full and MNG net Sharpes,
and every trade's money, exactly.

    python scripts/explore_d630_prop_lifecycle.py --selftest
    python scripts/explore_d630_prop_lifecycle.py --run
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
PUBLISHED = REPO / "data" / "ledger_h2_ng_stage_a.json"
OUT = REPO / "data" / "ledger_d630_prop_lifecycle.json"
NS = (1, 2, 3, 5)
VARIANTS = ("all years", "without 2022")


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


R = _load("run_h2_ng_stage_a", "run_h2_ng_stage_a.py")
CLASSES = {"full": dict(sym="NG", scale=1.0, cost=R.COST), "micro": dict(sym="MNG", scale=R.MNG_MULT / R.MULT,
                                                                          cost=R.MNG_COST)}


class LifecycleError(RuntimeError):
    pass


def trade_paths() -> pd.DataFrame:
    """One row per day (all 1,936): traded, gross money g, and the path's worst (mae) and best (mfe) marks in
    full-contract dollars from the fill to the exit, on D630's own bars."""
    b = R.build(read_returns=True)
    d = b["d"]
    g = R.signed(d)
    bars = pd.read_csv(R.BARS, encoding="utf-8", usecols=["day", "ym", "minute", "high", "low", "close"])
    if (bars["day"] >= R.CUT).any():
        raise LifecycleError("a bar on or after the cut is in memory")
    groups = {k: (x["minute"].to_numpy(), x["close"].to_numpy(), x["high"].to_numpy(), x["low"].to_numpy())
              for k, x in bars.sort_values(["day", "ym", "minute"]).groupby(["day", "ym"], sort=False)}
    px = pd.read_csv(R.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "px_1350"])
    px = px[(px["root"] == "NG") & (px["kind"] == "outright")].set_index(["day", "ym"])["px_1350"]
    tr = d["traded"].to_numpy() & np.isfinite(g)
    mae = np.zeros(len(d))
    mfe = np.zeros(len(d))
    for i, row in enumerate(d.itertuples(index=False)):
        if not tr[i]:
            continue
        mins, cl, hi, lo = groups.get((row.day, row.traded_ym), (np.array([], dtype=object),) + (np.array([]),) * 3)
        s1350 = float(px.get((row.day, row.traded_ym), np.nan))
        fill = R.asof(mins, cl, R.fill_end(row.tau), s1350)
        exit_px = R.asof(mins, cl, R.EXIT_END, s1350)
        end = R.money(row.dir, fill, exit_px)
        if end != g[i]:
            raise LifecycleError(f"known answer: {row.day} rebuilds {end} against D630's {g[i]}")
        held = (mins >= R.fill_end(row.tau)) & (mins < R.EXIT_END)
        if held.any():
            worst = lo[held].min() if row.dir > 0 else hi[held].max()
            best = hi[held].max() if row.dir > 0 else lo[held].min()
            mae[i] = min(R.money(row.dir, fill, worst), 0.0, end)
            mfe[i] = max(R.money(row.dir, fill, best), 0.0, end)
        else:
            mae[i], mfe[i] = min(0.0, end), max(0.0, end)
    return pd.DataFrame({"day": d["day"].to_numpy(), "traded": tr, "g": np.where(tr, g, 0.0), "mae": mae, "mfe": mfe})


def check_published(t: pd.DataFrame) -> None:
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))["NG"]
    C = R._load_cs()
    gt = t.loc[t["traded"], "g"].to_numpy()
    if int(t["traded"].sum()) != pub["gate"]["n"] or float(gt.mean()) != pub["gate"]["mean"]:
        raise LifecycleError(f"known answer: n {t['traded'].sum()} mean {gt.mean()} against D630's {pub['gate']}")
    ok = t["traded"].to_numpy()
    full = C.sharpe(np.where(ok, t["g"].to_numpy() - R.COST, 0.0))
    micro = C.sharpe(np.where(ok, t["g"].to_numpy() * R.MNG_MULT / R.MULT - R.MNG_COST, 0.0))
    if full != pub["performance"]["sharpe_net"] or micro != pub["component_mng"]["sharpe_net"]:
        raise LifecycleError(f"known answer: net Sharpe full {full} micro {micro} against D630's published")


def check_bounds(h: pd.DataFrame) -> None:
    if not ((h["d_low"] <= h["d_end"]).all() and (h["d_high"] >= 0).all() and (h["d_low"] <= 0).all()):
        raise LifecycleError("path bounds: low <= end, high >= 0 and low <= 0 on every day")


def days_for(t: pd.DataFrame, cls: str, n: int, variant: str) -> pd.DataFrame:
    """D493's convention: the cost is charged on the end and on the low; untraded days are zero."""
    c = CLASSES[cls]
    x = t if variant == "all years" else t[t["day"].str[:4] != "2022"]
    tr = x["traded"].to_numpy()
    end = np.where(tr, (x["g"].to_numpy() * c["scale"] - c["cost"]) * n, 0.0)
    low = np.where(tr, (x["mae"].to_numpy() * c["scale"] - c["cost"]) * n, 0.0)
    high = np.where(tr, x["mfe"].to_numpy() * c["scale"] * n, 0.0)
    h = pd.DataFrame({"day": x["day"].to_numpy(), "d_end": end, "d_low": np.minimum(low, end), "d_high": high})
    check_bounds(h)
    return h


def run(n_paths: int) -> dict[str, Any]:
    t0 = time.time()
    D93 = _load("run_d493", "run_d493_account_size.py")
    D40 = _load("d440l", "d440_lifecycle.py")
    fails = D40.p1_gate(verbose=False)
    if fails:
        raise LifecycleError(f"[P1] {fails}")
    t = trade_paths()
    check_published(t)
    print(f"known answers hold: n {int(t['traded'].sum())}, gate mean ${t.loc[t['traded'], 'g'].mean():.2f}, "
          f"published full and MNG net Sharpes reproduced exactly ({time.time() - t0:.0f} s)", flush=True)
    res: dict[str, Any] = {"record": "POST HOC on D630's spent in-sample; admits nothing", "cells": [],
                           "bar": D93.BAR, "horizon_days": D93.HORIZON_DAYS, "seed": D93.SEED}
    yr = {}
    for y, x in t.groupby(t["day"].str[:4]):
        dn = np.where(x["traded"], x["g"] - R.COST, 0.0)
        yr[y] = {"daily_sd_full_usd": float(np.std(dn, ddof=1)), "worst_day_low_full_usd":
                 float(np.where(x["traded"], x["mae"] - R.COST, 0.0).min()), "net_full_usd": float(dn.sum())}
    res["by_year_full_one_contract"] = yr
    for variant in VARIANTS:
        for cls in CLASSES:
            for n in NS:
                h = days_for(t, cls, n, variant)
                sd = float(h["d_end"].std(ddof=1))
                years = h["day"].str[:4].nunique()
                for p in D40.D386.PLANS:
                    prov, npth = D93.provider_measured(h, n_paths)
                    c = D93.cell(D40, p, h, prov, npth, n_paths, sd)
                    c.update(variant=variant, cls=cls, sym=CLASSES[cls]["sym"], n=n, plan=f"{p.firm} {p.size // 1000}k",
                             dd_fund=p.dd_fund, cost_usd=CLASSES[cls]["cost"] * n,
                             P3_breaches_per_year=c["P3_days_below_2pct"] / years,
                             max_dd_closed_usd=float((np.cumsum(h["d_end"]) - np.maximum.accumulate(
                                 np.cumsum(h["d_end"]))).min()))
                    res["cells"].append(c)
        print(f"  {variant}: {len(res['cells'])} cells ({time.time() - t0:.0f} s)", flush=True)
    df = pd.DataFrame(res["cells"])
    res["clearing"] = df[df["clears"]][["variant", "sym", "n", "plan", "V", "V_se", "p_pass", "life_years",
                                        "P3_worst_pct", "net_sharpe"]].to_dict("records")
    res["wall_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
    report(df, yr)
    print(f"wrote {OUT.relative_to(REPO)} in {res['wall_s']} s")
    return res


def report(df: pd.DataFrame, yr: dict[str, Any]) -> None:
    print("\nFull NG, one contract, by year: daily sd / worst intraday low / net")
    for y, v in yr.items():
        print(f"  {y}: sd ${v['daily_sd_full_usd']:,.0f}  worst low ${v['worst_day_low_full_usd']:,.0f}  "
              f"net ${v['net_full_usd']:,.0f}")
    cols = ["plan", "dd_fund", "p_pass", "p_breached", "life_years", "V", "V_se", "P3_worst_pct",
            "P3_breaches_per_year", "P5_years_over_40", "clears"]
    for variant in VARIANTS:
        for sym in ("NG", "MNG"):
            for n in NS:
                g = df[(df["variant"] == variant) & (df["sym"] == sym) & (df["n"] == n)]
                f = g.iloc[0]
                print(f"\n[{variant}] {sym} x{n}: net Sharpe {f['net_sharpe']:+.2f} +- {f['net_sharpe_se']:.2f}, "
                      f"mean ${f['mean_usd']:+.2f}/day, closed max DD ${f['max_dd_closed_usd']:,.0f}")
                with pd.option_context("display.width", 200, "display.max_columns", 20):
                    print(g[cols].round(3).to_string(index=False))


def selftest() -> int:
    t = pd.DataFrame({"day": ["2020-01-02", "2020-01-03", "2022-01-03"], "traded": [True, False, True],
                      "g": [100.0, 0.0, -50.0], "mae": [-40.0, 0.0, -80.0], "mfe": [120.0, 0.0, 10.0]})
    h = days_for(t, "full", 2, "all years")
    assert list(h["d_end"]) == [(100 - R.COST) * 2, 0.0, (-50 - R.COST) * 2], h
    assert list(h["d_low"]) == [(-40 - R.COST) * 2, 0.0, (-80 - R.COST) * 2], h
    m = days_for(t, "micro", 1, "all years")
    assert np.isclose(m["d_end"].iloc[0], 100 * 0.1 - R.MNG_COST), m
    assert len(days_for(t, "full", 1, "without 2022")) == 2
    bad = h.copy()
    bad.loc[0, "d_low"] = bad.loc[0, "d_end"] + 1.0
    try:
        check_bounds(bad)
    except LifecycleError:
        pass
    else:
        raise AssertionError("check_bounds did not raise on a low above the end")
    bad2 = h.copy()
    bad2.loc[0, "d_high"] = -1.0
    try:
        check_bounds(bad2)
    except LifecycleError:
        pass
    else:
        raise AssertionError("check_bounds did not raise on a negative high")
    print("selftest OK: cost on end and low, micro scale 0.1, the 2022 cut, and the bounds check raises when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--paths", type=int, default=3000)
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.run:
        run(a.paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
