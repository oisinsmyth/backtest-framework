"""D666 Stage 0: the re-break of yesterday's range, per root (ES, NQ). Written after D666's design (0bfd9e7), committed
before its one run.

    uv run python scripts/stage0_d666_rebreak.py --selftest
    uv run python scripts/stage0_d666_rebreak.py --dry-run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
    uv run python scripts/stage0_d666_rebreak.py --run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

In-sample 2016-01-04 -> 2025-02-28 through the sealed loader; Sierra TICK read only before 2025-03-01; SqueezeMetrics
GEX from the row dated before each session (credited; licence-guarded output: statistics only).

SETUP (long; short mirrored): L = the prior RTH high, A = D644's atr20. Arm on a bar trading above L; the pullback is a
later bar whose low touches L (minute tau); a buy stop at L + 0.25 A is live from the bar after tau to tau + 60, fill at
max(stop, the bar's open) + 1 tick; expiry resets the side; the first entry of the day, either side; none after 15:29.
EXITS, checked from the bar after the entry bar, the stop before the target inside a bar, stop fills minus 1 tick:
E1 target entry +/- P with the stop at L, else 15:59's close; E2 the stop at L, else 15:59; E3 the close of the bar
starting 60 minutes after the entry bar, no stop; E4 initial stop L, trailing 0.25 A behind the best price, never loosening.
GATE 1 (mechanism): unfiltered gross per trade > 0, Holm across 8; beats the plain break (a stop at L + 0.25 A from
09:30, no pullback) by Welch t >= 2; above the random-entry null's p95 (1,000 draws of a uniform minute in the setup's own
hour, same side, the real trade's stop distance) by more than 2 SE; positive without Feb-Apr 2020.
GATE 2 (tradeability, on Gate-1 cells): projected gross = pi_hat x P >= 2 x cost, pi_hat the mean of gross / P over
EARLIER trades of the same root and exit (burn-in 40; at least 30 filtered trades); filtered net > 0, Holm; ex-COVID > 0.
SECONDARY: size = 1 + aligned (gap > 0.1 A, A7 > 0, TICK z > 0.5); the fade veto (p_FADE >= its prior-252 80th pct, fade
against the trade) sets size 0. Writes data/stage0_d666_rebreak.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402

OUT = REPO / "data" / "stage0_d666_rebreak.json"
TICK = 0.25
K_ATR, WINDOW, LAST_ENTRY, CLOSE_BAR = 0.25, 60, 15 * 60 + 29, 15 * 60 + 59
TRAIL_K, BURN_IN, MIN_FILTERED, EP_K = 0.25, 40, 30, 2.0
N_NULL, SEED = 1000, 666
CHECKPOINTS = ("09:45", "10:00", "10:30", "11:00")
COVID = ("2020-02-01", "2020-04-30")
EXITS = ("E1", "E2", "E3", "E4")


class D666Error(RuntimeError):
    pass


def hm(s: str) -> int:
    return int(s[:2]) * 60 + int(s[3:])


# ================================================================================ the setup
def scan(bb: dict, Lh: float, Ll: float, A: float, window: int = WINDOW) -> dict[str, Any] | None:
    """The first re-break entry of the day: {D, i, tau, stop, entry, L, same_bar_skips}. Reads bars only up to the
    entry bar. `window` is the minutes after the touch within which the stop must fill."""
    m, o, h, l = bb["m"], bb["o"], bb["h"], bb["l"]
    st = {1: 0, -1: 0}
    tau = {1: -1, -1: -1}
    tau_i = {1: -1, -1: -1}
    same_bar = 0
    first_touch = None  # the day's first retest, whether or not it re-breaks: the random-entry null's population
    for i in range(len(m)):
        if m[i] > LAST_ENTRY:
            break
        for D, L in ((1, Lh), (-1, Ll)):
            stop = L + D * K_ATR * A
            if st[D] == 2:
                if m[i] - tau[D] > window:
                    st[D] = 0
                elif i > tau_i[D] and ((D > 0 and h[i] >= stop) or (D < 0 and l[i] <= stop)):
                    fill = (max(stop, o[i]) + TICK) if D > 0 else (min(stop, o[i]) - TICK)
                    return {"D": D, "i": i, "tau": tau[D], "stop": stop, "entry": float(fill), "L": L,
                            "same_bar_skips": same_bar, "first_touch": first_touch}
            if st[D] == 1 and ((D > 0 and l[i] <= L) or (D < 0 and h[i] >= L)):
                st[D], tau[D], tau_i[D] = 2, int(m[i]), i
                if first_touch is None:
                    first_touch = {"D": D, "tau": int(m[i]), "tau_i": i, "L": L}
                if (D > 0 and h[i] >= stop) or (D < 0 and l[i] <= stop):
                    same_bar += 1
            if st[D] == 0 and ((D > 0 and h[i] > L) or (D < 0 and l[i] < L)):
                st[D] = 1
    return None if first_touch is None else {"i": None, "first_touch": first_touch, "same_bar_skips": same_bar}


def scan_second_path(bb: dict, Lh: float, Ll: float, A: float) -> dict[str, Any] | None:
    """The lag audit's second implementation: event indices found with array operations, never calling scan()."""
    m, o, h, l = bb["m"], bb["o"], bb["h"], bb["l"]
    live = m <= LAST_ENTRY
    best = None
    for D, L in ((1, Lh), (-1, Ll)):
        beyond = (h > L) if D > 0 else (l < L)
        touch = (l <= L) if D > 0 else (h >= L)
        stop = L + D * K_ATR * A
        trig = (h >= stop) if D > 0 else (l <= stop)
        start = 0
        while True:
            a_ = np.flatnonzero(beyond[start:] & live[start:])
            if not len(a_):
                break
            ia = start + a_[0]
            t_ = np.flatnonzero(touch[ia + 1:] & live[ia + 1:])
            if not len(t_):
                break
            it = ia + 1 + t_[0]
            cand = np.flatnonzero(trig[it + 1:] & live[it + 1:] & (m[it + 1:] - m[it] <= WINDOW))
            gone = np.flatnonzero(m[it + 1:] - m[it] > WINDOW)
            if len(cand) and (not len(gone) or cand[0] < gone[0]):
                ie = it + 1 + cand[0]
                if best is None or ie < best[1]:
                    best = (D, ie, float((max(stop, o[ie]) + TICK) if D > 0 else (min(stop, o[ie]) - TICK)))
                break
            if not len(gone):
                break
            start = it + 1 + gone[0]  # expired: arm again from the first bar past the window
    return None if best is None else {"D": best[0], "i": int(best[1]), "entry": best[2]}


def plain_break(bb: dict, Lh: float, Ll: float, A: float) -> dict[str, Any] | None:
    """C1: a stop at L +/- 0.25 A live from 09:30, no pullback; the first fill of the day, either side."""
    m, o, h, l = bb["m"], bb["o"], bb["h"], bb["l"]
    for i in range(len(m)):
        if m[i] > LAST_ENTRY:
            return None
        for D, L in ((1, Lh), (-1, Ll)):
            stop = L + D * K_ATR * A
            if (D > 0 and h[i] >= stop) or (D < 0 and l[i] <= stop):
                return {"D": D, "i": i, "entry": float((max(stop, o[i]) + TICK) if D > 0 else (min(stop, o[i]) - TICK)),
                        "L": L, "stop": stop}
    return None


# ================================================================================ exits
def exit_trade(bb: dict, i: int, D: int, entry: float, stop_lvl: float, A: float, P_pts: float, kind: str,
               loosen: bool = False) -> tuple[float, str]:
    """(exit price, reason) for exit `kind` of a trade entered during bar i. `loosen` is the trailing-stop canary."""
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    if kind == "E3":
        j = np.flatnonzero(m <= m[i] + 60)
        return float(c[j[-1]]), "time"
    stop = stop_lvl
    target = entry + D * P_pts if kind == "E1" else None
    best = entry
    for k in range(i + 1, len(m)):
        if m[k] > CLOSE_BAR:
            break
        hit = (l[k] <= stop) if D > 0 else (h[k] >= stop)
        if hit:
            through = (o[k] <= stop) if D > 0 else (o[k] >= stop)
            px = (o[k] if through else stop) - D * TICK
            return float(px), "stop"
        if target is not None and ((D > 0 and h[k] >= target) or (D < 0 and l[k] <= target)):
            return float(target), "target"
        if kind == "E4":
            best = max(best, h[k]) if D > 0 else min(best, l[k])
            if loosen:  # the canary: a stop that trails the CURRENT price follows the market back down
                stop = c[k] - D * TRAIL_K * A
            else:
                new = best - D * TRAIL_K * A
                stop = max(stop, new) if D > 0 else min(stop, new)
    j = np.flatnonzero(m <= CLOSE_BAR)
    return float(c[j[-1]]), "close"


def trail_audit(fn: Callable = exit_trade) -> None:
    """The trailing stop never loosens: a rise then a fall back to (but not through) the initial stop must exit at
    the trailed stop, above the initial one."""
    m = np.arange(hm("10:00"), hm("12:00"))
    c = np.r_[np.linspace(100, 102, 30), np.linspace(102, 100.3, 90)]
    bb = {"m": m, "o": c, "h": c + 0.05, "l": c - 0.05, "c": c}
    px, why = fn(bb, 0, 1, 100.0, 100.0 - 0.5, 1.0, 5.0, "E4")
    if not (why == "stop" and px > 100.0):
        raise D666Error(f"trailing: the stop did not hold its gains ({px}, {why})")


# ================================================================================ per-root build
def cost_bp(R: Any, r: str, entry: float) -> float:
    return R.COST_USD[r] / R.USD_PER_POINT[r] / entry * 1e4


def root_trades(args: tuple) -> dict[str, Any]:
    """One root, in its own process: the re-break and plain-break trades with all four exits, and the random-entry
    table (every minute of the setup's hour, all four exits) for the null."""
    r, frame, bars_r, R_costs, P_col = args
    COST_USD, USD_PT = R_costs
    rows, plain, null_tab = [], [], []
    for s, d in frame.iterrows():
        bb = bars_r.get(s)
        if bb is None:
            continue
        Lh, Ll, A = float(d["prior_high"]), float(d["prior_low"]), float(d["atr20"])
        sc = scan(bb, Lh, Ll, A)
        e = sc if sc is not None and sc.get("i") is not None else None
        sig_left = lambda i_: float(d["sig20"]) * math.sqrt(max(CLOSE_BAR + 1 - int(bb["m"][i_]), 1) / 390)  # noqa: E731
        if sc is not None and sc["first_touch"] is not None:
            # the random-entry null (C2): EVERY day's first retest, whether or not it re-broke -- conditioning on
            # the re-break would hand the null the future. A uniform minute in (tau, tau + 60], entered at that bar's
            # close + 1 tick, the setup's own side, the stop 0.25 A + 1 tick away, the same projection.
            ft = sc["first_touch"]
            dist = K_ATR * A + TICK
            cand = []
            for k in np.flatnonzero((bb["m"] > ft["tau"]) & (bb["m"] <= ft["tau"] + WINDOW) & (bb["m"] <= LAST_ENTRY)):
                ent = float(bb["c"][k]) + ft["D"] * TICK
                Pk = ent * sig_left(k) * float(d[P_col]) / 1e4
                cand.append([ft["D"] * (exit_trade(bb, int(k), ft["D"], ent, ent - ft["D"] * dist, A, Pk, x)[0] / ent - 1) * 1e4
                             for x in EXITS])
            if cand:
                null_tab.append(np.array(cand))
        if e is not None:
            P_bp = sig_left(e["i"]) * float(d[P_col])
            P_pts = e["entry"] * P_bp / 1e4
            rec = {"session": s, "D": e["D"], "minute": int(bb["m"][e["i"]]), "tau": e["tau"], "entry": e["entry"],
                   "L": e["L"], "P_bp": P_bp, "same_bar_skips": e["same_bar_skips"],
                   "cost_bp": COST_USD / USD_PT / e["entry"] * 1e4}
            for x in EXITS:
                px, why = exit_trade(bb, e["i"], e["D"], e["entry"], e["L"], A, P_pts, x)
                rec[f"{x}_gross"] = e["D"] * (px / e["entry"] - 1) * 1e4
                rec[f"{x}_why"] = why
            rows.append(rec)
        p = plain_break(bb, Lh, Ll, A)
        if p is not None:
            P_pts = p["entry"] * sig_left(p["i"]) * float(d[P_col]) / 1e4
            prec = {"session": s, "D": p["D"]}
            for x in EXITS:
                px, _ = exit_trade(bb, p["i"], p["D"], p["entry"], p["L"], A, P_pts, x)
                prec[f"{x}_gross"] = p["D"] * (px / p["entry"] - 1) * 1e4
            plain.append(prec)
    return {"root": r, "rows": rows, "plain": plain, "null_tab": null_tab}


def mean_t(x: np.ndarray, R: Any) -> tuple[float, float, float]:
    x = np.asarray(x, float)
    t, se = R.nw_t(x)
    return float(x.mean()), float(t), float(se)


def four_groups(tr: pd.DataFrame, gross: pd.Series, net: pd.Series, per_year: float, R: Any, r: str) -> dict[str, Any]:
    v = np.sort(net.to_numpy(float))
    k = max(1, int(round(0.01 * len(v))))
    w, lo = v[v > 0], v[v <= 0]
    cum = np.cumsum(net.to_numpy(float))
    sh = float(net.mean() / net.std(ddof=1) * math.sqrt(per_year)) if net.std(ddof=1) > 0 else float("nan")
    dd = math.sqrt(float(np.mean(np.minimum(net.to_numpy(float), 0) ** 2)))
    top = tr.loc[net.abs().idxmax()]
    return {"trades": int(len(net)), "gross_mean": float(gross.mean()), "net_mean": float(net.mean()),
            "net_median": float(np.median(v)), "win": float((v > 0).mean()),
            "payoff": float(w.mean() / -lo.mean()) if len(w) and len(lo) and lo.mean() < 0 else float("nan"),
            "skew": float(stats.skew(v)), "kurtosis": float(stats.kurtosis(v)),
            "ex_top1pct": float(v[:-k].mean()), "ex_bottom1pct": float(v[k:].mean()), "trimmed": float(v[k:-k].mean()),
            "sharpe_net_ann": sh, "sortino_net_ann": float(net.mean() / dd * math.sqrt(per_year)) if dd > 0 else float("nan"),
            "sharpe_gross_ann": float(gross.mean() / gross.std(ddof=1) * math.sqrt(per_year)),
            "max_dd_bp": float((np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum).max()),
            "breakeven_cost_bp": float(gross.mean()), "cost_bp_mean": float(tr["cost_bp"].mean()),
            "top_trade": {"session": str(top["session"]), "D": int(top["D"]), "net_bp": float(net.loc[top.name])}}


def build(data_root: Path, dry: bool) -> dict[str, Any]:
    t_start = time.time()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(data_root, dry)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    rng = np.random.default_rng(SEED)
    if dry:
        gex = pd.Series(rng.normal(3e9, 4e9, 3000), index=pd.bdate_range("2014-01-01", periods=3000).strftime("%Y-%m-%d"))
    else:
        dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
        gex = dix[dix["date"] < T.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    frames = {}
    for r in ("ES", "NQ"):
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        g_own = Gd[r].reindex(d.index)
        short = (d["gd_spx"] < 0) if r == "ES" else (g_own < 0)
        d["m_gamma"] = np.where(short.fillna(False), 1.5, 1.0)
        frames[r] = d
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars},
             (R.COST_USD[r], R.USD_PER_POINT[r]), "m_gamma") for r in ("ES", "NQ")]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(root_trades, jobs)}
    fan_s = time.time() - t0
    # the second path for the setup, on every session of both roots
    for r in ("ES", "NQ"):
        by = {x["session"]: x for x in got[r]["rows"]}
        for s, d in frames[r].iterrows():
            if (r, s) not in bars:
                continue
            e2 = scan_second_path(bars[(r, s)], float(d["prior_high"]), float(d["prior_low"]), float(d["atr20"]))
            e1 = by.get(s)
            if (e1 is None) != (e2 is None) or (e1 and (e1["D"] != e2["D"] or abs(e1["entry"] - e2["entry"]) > 1e-9)):
                raise D666Error(f"lag: the setup's second path disagrees on {r} {s}")
    # confluences and the fade veto
    conf = confluences(data_root, dry, b, tabs, frames, got, R)
    out: dict[str, Any] = {"spec": "D666 (0bfd9e7)", "dry_run": dry, "credit": "dealer gamma (GEX): SqueezeMetrics",
                           "cells": {}, "roots": {}}
    p1 = {}
    for r in ("ES", "NQ"):
        tr = pd.DataFrame(got[r]["rows"])
        pl = pd.DataFrame(got[r]["plain"])
        years = len(frames[r]) / 252
        per_year = len(tr) / years
        out["roots"][r] = {"sessions": int(len(frames[r])), "rebreaks": int(len(tr)), "per_year": per_year,
                           "plain_breaks": int(len(pl)), "same_bar_touch_and_trigger_skipped": int(tr["same_bar_skips"].sum()),
                           "long": int((tr["D"] > 0).sum()), "short": int((tr["D"] < 0).sum())}
        idx = tr["session"]
        exc = ~idx.between(*COVID)
        null_tab = got[r]["null_tab"]
        for j, x in enumerate(EXITS):
            g = tr[f"{x}_gross"]
            net = g - tr["cost_bp"]
            gm, gt, gse = mean_t(g.to_numpy(), R)
            p1[f"{r}_{x}"] = float(stats.norm.sf(gt))
            # C1: the plain break, gross
            pg = pl[f"{x}_gross"].to_numpy(float)
            diff = gm - pg.mean()
            welch = diff / math.sqrt(g.var(ddof=1) / len(g) + pg.var(ddof=1) / len(pg))
            # C2: the random-entry null, gross mean per draw
            draws = np.empty(N_NULL)
            for kd in range(N_NULL):
                draws[kd] = np.nanmean([nt[rng.integers(0, len(nt)), j] for nt in null_tab])
            q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(500)]
            # Gate 2: the expected-profit filter, walk-forward pass-through
            ratio = (g / tr["P_bp"]).to_numpy(float)
            pi_hat = np.r_[np.nan, np.cumsum(ratio)[:-1] / np.arange(1, len(ratio))]
            proj = pi_hat * tr["P_bp"].to_numpy(float)
            after = np.arange(len(tr)) >= BURN_IN
            take = after & (proj >= EP_K * tr["cost_bp"].to_numpy(float))
            fnet = net.to_numpy(float)[take]
            f_ex = net[take & exc.to_numpy()].to_numpy(float)
            fm, ft, _ = mean_t(fnet, R) if len(fnet) > 2 else (float("nan"),) * 3
            se_v = gse * math.sqrt(len(tr) / (per_year * 390 / 252))
            out["cells"][f"{r}_{x}"] = {
                "gate1": {"gross_mean": gm, "t_hac": gt, "p_one_sided": p1[f"{r}_{x}"], "mde80": (1.959964 + 0.841621) * gse,
                          "vs_plain": {"plain_gross_mean": float(pg.mean()), "plain_n": int(len(pg)), "diff": diff, "welch_t": welch},
                          "random_null": {"p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)),
                                          "p95_se": float(np.std(q95, ddof=1)), "rank": float((draws < gm).mean())},
                          "ex_covid_gross": float(g[exc].mean()),
                          "vault_power": float(stats.norm.sf(1.959964 - gm / se_v)) if se_v > 0 else float("nan")},
                "gate2": {"filtered_trades": int(take.sum()), "pass_rate_after_burnin": float(take[after].mean()) if after.any() else float("nan"),
                          "filtered_net_mean": fm, "filtered_t": ft, "filtered_ex_covid": float(np.mean(f_ex)) if len(f_ex) else float("nan"),
                          "pi_hat_final": float(pi_hat[-1]) if len(pi_hat) else float("nan"),
                          "removed_net_mean": float(net.to_numpy(float)[after & ~take].mean()) if (after & ~take).any() else float("nan")},
                "four_groups": four_groups(tr, g, net, per_year, R, r),
                "splits": {"long_gross": float(g[tr["D"] > 0].mean()), "short_gross": float(g[tr["D"] < 0].mean()),
                           "pre_0dte_gross": float(g[idx < "2022-05-16"].mean()), "post_0dte_gross": float(g[idx >= "2022-05-16"].mean()),
                           "by_year_gross": {y: float(g[idx.str.startswith(y)].mean()) for y in sorted({s[:4] for s in idx})},
                           "exit_reasons": tr[f"{x}_why"].value_counts().to_dict()},
                "secondary": conf.get(f"{r}_{x}", {})}
    # verdicts: Gate 1 Holm across the 8; Gate 2 Holm across the Gate-1 passes
    h1 = T.holm(p1)
    g1 = {}
    for k, c in out["cells"].items():
        a = c["gate1"]
        g1[k] = {"gross_positive_holm": bool(a["gross_mean"] > 0 and h1[k] < 0.05),
                 "beats_plain": bool(a["vs_plain"]["diff"] > 0 and a["vs_plain"]["welch_t"] >= 2),
                 "above_random_p95": bool(a["gross_mean"] - a["random_null"]["p95"] > 2 * a["random_null"]["p95_se"]),
                 "positive_ex_covid": bool(a["ex_covid_gross"] > 0)}
        c["gate1"]["holm_p"] = h1[k]
        c["gate1"]["checks"] = g1[k]
    passed1 = [k for k in g1 if all(g1[k].values())]
    p2 = {k: float(stats.norm.sf(out["cells"][k]["gate2"]["filtered_t"])) for k in passed1
          if np.isfinite(out["cells"][k]["gate2"]["filtered_t"])}
    h2 = T.holm(p2) if p2 else {}
    for k, c in out["cells"].items():
        g2 = c["gate2"]
        ok2 = bool(k in h2 and g2["filtered_trades"] >= MIN_FILTERED and g2["filtered_net_mean"] > 0 and h2[k] < 0.05
                   and g2["filtered_ex_covid"] > 0)
        c["verdict"] = ("SUPPORTED" if k in passed1 and ok2 else "MECHANISM ONLY" if k in passed1 else "NOT SUPPORTED")
        if k in passed1 and g2["filtered_trades"] < MIN_FILTERED:
            c["verdict"] = "MECHANISM ONLY (Gate 2 UNRESOLVED: too few filtered trades)"
    out["verdict_by_root"] = {r: sorted({c["verdict"] for k, c in out["cells"].items() if k.startswith(r)}) for r in ("ES", "NQ")}
    cells = out["cells"]
    out["predictions"] = {
        "1_both_roots_not_supported_at_gate1": not passed1,
        "2_rebreak_minus_plain_within_2bp": all(abs(c["gate1"]["vs_plain"]["diff"]) <= 2 for c in cells.values()),
        "3_no_exit_beats_E3_by_its_se": all(cells[f"{r}_{x}"]["gate1"]["gross_mean"] - cells[f"{r}_E3"]["gate1"]["gross_mean"]
                                             <= cells[f"{r}_E3"]["gate1"]["mde80"] / 2.8 for r in ("ES", "NQ") for x in EXITS),
        "4_sizing_slope_inside_noise": all(abs(c["secondary"].get("slope_t_on_count", 0.0)) < 2 for c in cells.values()),
        "5_vault_power_below_half": all(c["gate1"]["vault_power"] < 0.5 for c in cells.values()),
        "6_pi_hat_near_zero": all(abs(c["gate2"]["pi_hat_final"]) <= 0.1 for c in cells.values())}
    out["speed"] = {"fanout_wall_s": round(fan_s, 1)}
    out["runtime_min"] = round((time.time() - t_start) / 60, 2)
    T.licence_guard(out)
    return out


def confluences(data_root: Path, dry: bool, b: pd.DataFrame, tabs: dict, frames: dict, got: dict, R: Any) -> dict:
    """The secondary layer: size = 1 + aligned (gap, A7, TICK); the fade veto sets size 0. Per root and exit."""
    rng = np.random.default_rng(SEED + 1)
    a7 = None if dry else pd.read_csv(REPO / "data" / "opening" / "a7.csv", encoding="utf-8", dtype={"session": str})
    if a7 is not None:
        a7 = a7[a7["session"] < T.RESERVED_FROM]
    # D645's walk-forward p_FADE at each checkpoint, pooled fit as registered
    cal = sorted({s for r in R.ROOTS for s in tabs[r].index if tabs[r].loc[s, "usable"] and s >= "2016-01-04"})
    pf = {}
    for t in CHECKPOINTS:
        P = R.walk_forward(R.dataset(tabs, t, t), list(R.S_A), cal)
        pf[t] = P.set_index(["root", "session"])["p_FADE"]
    ex = {}
    if not dry:
        with ProcessPoolExecutor(max_workers=2) as pool:
            ex = dict(pool.map(T.extract_job, [(T.SHOCK_SYMS[r]["tick"], str(T.SC_DATA / f"{T.SHOCK_SYMS[r]['tick']}.scid"))
                                               for r in ("ES", "NQ")]))
        for e_ in ex.values():
            T.assert_sealed(e_)
    out = {}
    for r in ("ES", "NQ"):
        tr = pd.DataFrame(got[r]["rows"]).set_index("session")
        d = frames[r].reindex(tr.index)
        gap_al = (tr["D"] * (d["open"] / d["prior_close"] - 1) * 100 > 0.10 * d["atr20"] / d["prior_close"] * 100)
        a7_al = pd.Series(False, index=tr.index)
        if a7 is not None:
            ar = a7[a7["root"] == r].set_index("session")
            for s, rec in tr.iterrows():
                cps = [t for t in CHECKPOINTS if hm(t) <= rec["minute"]]
                if cps and s in ar.index and np.isfinite(ar.at[s, f"a7_{cps[-1]}"]):
                    a7_al[s] = bool(rec["D"] * ar.at[s, f"a7_{cps[-1]}"] > 0)
        tick_al = pd.Series(False, index=tr.index)
        if ex:
            sym = T.SHOCK_SYMS[r]["tick"]
            gt = {"tick": T.gate_f(ex[sym], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
            rows = pd.DataFrame({"D": tr["D"], "eb": tr["minute"]})
            sh = T.shocks(rows, "09:30", ex[sym], None, None, gt)
            tick_al = (sh["s_tick"] > 0.5).fillna(False)
        count = gap_al.astype(int) + a7_al.astype(int) + tick_al.astype(int)
        veto = pd.Series(False, index=tr.index)
        for t in CHECKPOINTS:
            ser = pf[t].xs(r, level="root").sort_index()
            thr = ser.shift(1).rolling(252, min_periods=60).quantile(0.8)
            for s, rec in tr.iterrows():
                cps = [c for c in CHECKPOINTS if hm(c) <= rec["minute"]]
                if cps and cps[-1] == t and s in ser.index and np.isfinite(thr.get(s, np.nan)):
                    fade_dir = -np.sign(d.at[s, "open"] - d.at[s, "prior_close"])
                    veto[s] = bool(ser[s] >= thr[s] and fade_dir == -rec["D"])
        size = np.where(veto, 0, 1 + count)
        for x in EXITS:
            net = tr[f"{x}_gross"] - tr["cost_bp"]
            usd = net / 1e4 * tr["entry"] * R.USD_PER_POINT[r]
            flat_sh = float(usd.mean() / usd.std(ddof=1)) if usd.std(ddof=1) > 0 else float("nan")
            sized = usd * size
            sz_sh = float(sized.mean() / sized.std(ddof=1)) if sized.std(ddof=1) > 0 else float("nan")
            f = S.hac(net.to_numpy(float), count.to_numpy(float)[:, None])
            kept, vet = net[~veto], net[veto]
            out[f"{r}_{x}"] = {"aligned_share": {"gap": float(gap_al.mean()), "a7": float(a7_al.mean()), "tick": float(tick_al.mean())},
                               "per_trade_sharpe_flat": flat_sh, "per_trade_sharpe_sized": sz_sh,
                               "slope_net_on_count": float(f.params[1]), "slope_t_on_count": float(f.tvalues[1]),
                               "vetoed": int(veto.sum()), "vetoed_net_mean": float(vet.mean()) if len(vet) else float("nan"),
                               "kept_net_mean": float(kept.mean()),
                               "veto_diff_t": float((vet.mean() - kept.mean()) / math.sqrt(vet.var(ddof=1) / len(vet) + kept.var(ddof=1) / len(kept)))
                               if len(vet) > 2 else float("nan")}
    del rng
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D666Error:
            fired.append(name)
            return
        raise SystemExit(f"SELFTEST FAILED: {name} did not raise")

    m = np.arange(hm("09:30"), hm("16:00"))
    # a long re-break: up through 100 (L), back to 100 at 10:20, up through 100.5 (L + 0.25 x 2) at 10:40
    c = np.interp(m, [hm("09:30"), hm("10:00"), hm("10:20"), hm("10:40"), hm("16:00")], [99.5, 100.4, 100.0, 100.6, 101.5])
    bb = {"m": m, "o": c, "h": c + 0.02, "l": c - 0.02, "c": c}
    e = scan(bb, 100.0, 90.0, 2.0)
    e2 = scan_second_path(bb, 100.0, 90.0, 2.0)
    if e is None or e.get("i") is None or e2 is None or e["D"] != 1 or e["i"] != e2["i"]:
        raise SystemExit(f"SELFTEST FAILED: the setup or its second path ({e}, {e2})")
    # the window: the same path, but the re-break 61 minutes after the touch, must not trade; a canary window accepts it
    c61 = np.interp(m, [hm("09:30"), hm("10:00"), hm("10:20"), hm("11:21"), hm("16:00")], [99.5, 100.4, 100.0, 100.49, 101.5])
    c61[m > hm("11:21")] = np.linspace(100.51, 101.5, int((m > hm("11:21")).sum()))
    b61 = {"m": m, "o": c61, "h": c61 + 0.0, "l": c61 - 0.0, "c": c61}

    def window_audit(win: int) -> None:
        got = scan(b61, 100.0, 90.0, 2.0, window=win)
        if got is not None and got.get("i") is not None and b61["m"][got["i"]] - got["tau"] > WINDOW:
            raise D666Error("window: a fill beyond tau + 60 was traded")
    window_audit(WINDOW)
    must_raise("window-61", lambda: window_audit(120))
    # sign and money: a long that rises pays; a stop exit loses at least the stop distance plus slippage
    px, why = exit_trade(bb, e["i"], 1, e["entry"], e["L"], 2.0, 5.0, "E2")
    if not (why in ("close", "stop") and (why != "close" or px > e["entry"])):
        raise SystemExit("SELFTEST FAILED: a rising long did not pay")
    cd = np.r_[np.full(10, 101.0), np.linspace(101.0, 98.0, 50)]
    md = np.arange(hm("10:00"), hm("10:00") + 60)
    bd = {"m": md, "o": cd, "h": cd + 0.01, "l": cd - 0.01, "c": cd}
    pxs, whys = exit_trade(bd, 0, 1, 101.0, 100.0, 2.0, 50.0, "E2")
    if not (whys == "stop" and pxs <= 100.0 - TICK + 1e-9):
        raise SystemExit(f"SELFTEST FAILED: a stop exit did not lose the stop distance plus slippage ({pxs}, {whys})")
    # fills: a bar opening through the stop fills at its open
    cg = np.r_[np.full(5, 101.0), np.full(5, 99.0)]
    mg = np.arange(hm("10:00"), hm("10:10"))
    bg = {"m": mg, "o": cg, "h": cg, "l": cg, "c": cg}
    pxg, _ = exit_trade(bg, 0, 1, 101.0, 100.0, 2.0, 50.0, "E2")
    if abs(pxg - (99.0 - TICK)) > 1e-9:
        raise SystemExit(f"SELFTEST FAILED: a gap through the stop did not fill at the open ({pxg})")
    # the trailing stop never loosens
    trail_audit()
    must_raise("trail-loosens", lambda: trail_audit(lambda *a, **k: exit_trade(*a, **k, loosen=True)))
    # right quantity: E3 differs from E2 on the rising path
    if exit_trade(bb, e["i"], 1, e["entry"], e["L"], 2.0, 5.0, "E3")[0] == exit_trade(bb, e["i"], 1, e["entry"], e["L"], 2.0, 5.0, "E2")[0]:
        raise SystemExit("SELFTEST FAILED: E3 equals E2")
    # lag canaries on the walk-forward pass-through: including the trade's own outcome must differ
    ratio = np.array([1.0, -1.0, 2.0, 0.5])

    def pi_audit(inclusive: bool) -> None:
        ok = np.r_[np.nan, np.cumsum(ratio)[:-1] / np.arange(1, len(ratio))]
        cand = np.cumsum(ratio) / np.arange(1, len(ratio) + 1) if inclusive else ok
        if not np.allclose(cand[1:], ok[1:], equal_nan=True):
            raise D666Error("lag: the pass-through uses the trade's own outcome")
    pi_audit(False)
    must_raise("pi-includes-own", lambda: pi_audit(True))

    # the checkpoint rule for A7 and p_FADE: a checkpoint after the entry is a leak
    def cp_audit(entry_minute: int, chosen: str) -> None:
        if hm(chosen) > entry_minute:
            raise D666Error("lag: a checkpoint after the entry")
    cp_audit(hm("10:40"), [t for t in CHECKPOINTS if hm(t) <= hm("10:40")][-1])
    must_raise("checkpoint-after-entry", lambda: cp_audit(hm("10:40"), "11:00"))

    # the gap canary: a gap measured to the entry price differs from the open's
    def gap_audit(price_used: float, open_: float) -> None:
        if price_used != open_:
            raise D666Error("lag: the gap is measured to a later price")
    gap_audit(99.5, 99.5)
    must_raise("gap-to-entry", lambda: gap_audit(e["entry"], 99.5))
    # the licence guard
    T.licence_guard({"x": [1, 2]})
    try:
        T.licence_guard({"g": list(range(100))})
        raise SystemExit("SELFTEST FAILED: the licence guard")
    except T.D663Error:
        fired.append("licence")
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the clean cases pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run and OUT.exists():
        raise SystemExit("D666 Stage 0 runs once: its output exists")
    doc = build(a.data_root, dry=a.dry_run)
    if a.run:
        OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for k, c in doc["cells"].items():
        g1 = c["gate1"]
        print(f"{'DRY ' if a.dry_run else ''}{k}: {c['verdict']:<14} gross {g1['gross_mean']:+7.2f} (t {g1['t_hac']:+.2f}, "
              f"Holm {g1['holm_p']:.3f}) vs plain {g1['vs_plain']['diff']:+.2f} (t {g1['vs_plain']['welch_t']:+.2f}) "
              f"random p95 {g1['random_null']['p95']:+.2f}; filtered net {c['gate2']['filtered_net_mean']:+.2f} "
              f"(n {c['gate2']['filtered_trades']})")
    print(json.dumps(doc["roots"]), f"{doc['runtime_min']} min; {'written' if a.run else 'nothing written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
