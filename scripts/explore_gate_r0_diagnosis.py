"""POST HOC, after D634's one run (data/index_reweight/gate_r0.json, verdict UNRESOLVED (proxy)). Admits nothing and
changes no verdict. It decomposes the misses the way D634 s.4 asks for UNRESOLVED:

1. The monthly misses of each fund pair (+2x and -2x on one subindex). Write e_long and e_short for the two funds'
   monthly errors (reconstructed minus fund-implied). An accrual the NAV model misses (interest, fees, swap
   financing) has the same sign in both funds' NAVs, so after dividing by +-L it enters with OPPOSITE signs; an error
   in the rebuilt subindex enters both with the SAME sign. So (e_long + e_short)/2 is the rebuild's part and
   (e_short - e_long)/2 the proxy's. Months holding the 2020 strip holes (2020-02-27, 2020-06-30) are shown apart.
2. The aggregate (UCD/CMD, 2016): the daily index-level error regressed on each component's daily return, to name
   the component whose weight or price is off.

    uv run python scripts/explore_gate_r0_diagnosis.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "index_reweight" / "gate_r0_posthoc.json"
HOLE_MONTHS = {"2020-02", "2020-03", "2020-06", "2020-07"}
PAIRS = {"Natural Gas": ("BOIL", "KOLD"), "WTI Crude Oil": ("UCO", "SCO"), "Gold": ("UGL", "GLL"),
         "Silver": ("AGQ", "ZSL"), "BCOM": ("UCD", "CMD")}


def _load() -> object:
    s = importlib.util.spec_from_file_location("run_gate_r0", REPO / "scripts" / "run_gate_r0.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules["run_gate_r0"] = m
    s.loader.exec_module(m)
    return m


def monthly_errors(G, nav, L, bdays, bd, R, rates, first, last) -> dict[str, float]:  # type: ignore[no-untyped-def]
    rows = G.replicate(nav, L, bdays, bd, R, rates, first, last)
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["date"][:7], []).append(r)
    out = {}
    for m, rs in by.items():
        if any(r["ratio"] is None for r in rs):
            continue
        rec = float(np.prod([r["ratio"] for r in rs])) - 1
        imp = float(np.prod([1 + ((r["nav1"] - r["acc"]) / r["nav0"] - 1) / L for r in rs])) - 1
        out[m] = (rec - imp) * 1e4
    return out


def main() -> int:
    G = _load()
    reads: dict = {}
    cip = G.cips()
    cme, _ = G.load_cme(reads)
    prices = {**cme, **G.load_ice(reads), **G.load_lme(reads)}
    bdays, bd, det = G.calendar(prices, cip)
    bdays = [d for d in bdays if d >= "2015-01-01"]
    comps = sorted({c for y in cip for c, w in cip[y].items() if w > 0})
    rws = {c: G.roll_weights(c, prices, bdays, bd) for c in comps}
    R = {c: G.sub_index_returns(c, prices, bdays, bd, rws[c])[0] for c in comps}
    cim = G.cims(prices, cip, det)
    Ragg = G.aggregate_returns(prices, cip, cim, bdays, bd, det, rws)
    navs = G.load_navs({})
    rates = G.load_rates()
    doc: dict = {"record": "POST HOC on D634's one run; admits nothing", "pairs": {}}
    for comp, (fl, fs) in PAIRS.items():
        Rs = Ragg if comp == "BCOM" else R[comp]
        _, _, first, last = G.FUNDS[fl]
        el = monthly_errors(G, navs[fl], G.FUNDS[fl][0], bdays, bd, Rs, rates, first, last)
        es = monthly_errors(G, navs[fs], G.FUNDS[fs][0], bdays, bd, Rs, rates, first, last)
        ms = sorted(set(el) & set(es))
        rebuild = {m: (el[m] + es[m]) / 2 for m in ms}
        proxy = {m: (es[m] - el[m]) / 2 for m in ms}
        clean = [m for m in ms if m not in HOLE_MONTHS]

        def stats(d: dict[str, float], keys: list[str]) -> dict:
            a = np.array([d[k] for k in keys])
            return {"months": len(a), "median_abs_bp": round(float(np.median(np.abs(a))), 3),
                    "mean_bp": round(float(a.mean()), 3), "share_within_5bp": round(float((np.abs(a) <= 5).mean()), 4)}

        doc["pairs"][comp] = {
            "funds": [fl, fs],
            "long_fund_all_months": stats(el, ms), "short_fund_all_months": stats(es, ms),
            "long_fund_without_hole_months": stats(el, clean), "short_fund_without_hole_months": stats(es, clean),
            "rebuild_part_without_hole_months": stats(rebuild, clean),
            "proxy_part_without_hole_months": stats(proxy, clean),
            "hole_months": {m: {"long": round(el[m], 2), "short": round(es[m], 2)} for m in ms if m in HOLE_MONTHS},
        }
    # the aggregate: which component's return explains the daily index-level error?
    fl, fs = PAIRS["BCOM"]
    rows_l = G.replicate(navs[fl], 2, bdays, bd, Ragg, rates, "2016-01-05", "2016-08-25")
    rows_s = G.replicate(navs[fs], -2, bdays, bd, Ragg, rates, "2016-01-05", "2016-08-25")
    dates, err = [], []
    for a, b in zip(rows_l, rows_s):
        if a["ratio"] is None or b["ratio"] is None or len(a["bd"]) != 1 or a["date"] != b["date"]:
            continue
        il = ((a["nav1"] - a["acc"]) / a["nav0"] - 1) / 2
        ish = ((b["nav1"] - b["acc"]) / b["nav0"] - 1) / -2
        dates.append(a["date"])
        err.append((a["ratio"] - 1) - (il + ish) / 2)  # the rebuild's part, index level
    X = np.array([[(R[c].get(d) or 1.0) - 1 for c in comps if cim[2016].get(c)] for d in dates])
    names = [c for c in comps if cim[2016].get(c)]
    y = np.array(err)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    doc["aggregate_2016"] = {
        "days": len(y), "median_abs_error_bp": round(float(np.median(np.abs(y))) * 1e4, 3),
        "r2_on_component_returns": round(float(1 - ((y - fit) ** 2).sum() / ((y - y.mean()) ** 2).sum()), 4),
        "implied_weight_error_by_component": {n: round(float(b), 5) for n, b in
                                              sorted(zip(names, beta), key=lambda t: -abs(t[1]))},
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
