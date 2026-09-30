"""D711 addendum (post hoc, the principal: "I would like the extremes striped out for the decision time comparison and
the other comparisons to the other roots. I would also like to have a statistical breakdown of where the trades overlap
between NQ and ES and where they disagree?"). Descriptive only, on D711's already-read in-sample data (to 2023-12-29);
nothing gates, nothing is fitted.

    uv run python scripts/diag_d711_trims_and_overlap.py --selftest
    uv run python scripts/diag_d711_trims_and_overlap.py --run

1. TRIMS. For every A1 clock and every A2 root: the F2-rule book with the extremes removed -- symmetric trims of 1 / 2.5 /
   5 / 10 % of trades from BOTH tails (by net), the 5 % winsorised mean, ex-top-5 and ex-bottom-5 trades, and the median
   -- in dollars net and in z (gross / the line's take-everything sd, D711's unit). The take-everything line is trimmed
   the same way, so the filter's lift is shown under each trim; A1's pooled placebo is trimmed as a pool.
2. OVERLAP. ES F2 against NQ F2 at 15:30 on their common sessions: both take / ES only / NQ only / neither; direction
   agreement; each side's P&L in each cell; what the other root's unfiltered trade earned on the days only one took;
   the one-MES + one-MNQ book against each alone; by year.
Writes data/diag_d711_trims_and_overlap.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage1_d711_f2_mechanism as M  # noqa: E402

D = M.D
OUT = REPO / "data" / "diag_d711_trims_and_overlap.json"
D711_JSON = REPO / "data" / "stage1_d711_f2_mechanism.json"
TRIMS = (0.01, 0.025, 0.05, 0.10)
CLOCKS = M.PLACEBO + (M.SHOULDER, M.ANCHOR)


class DiagError(RuntimeError):
    pass


# ================================================================================ trims
def trim_idx(net: np.ndarray, p: float) -> np.ndarray:
    """Indices kept after removing floor(p * n) trades from EACH tail by net, in the book's time order."""
    n = len(net)
    k = int(math.floor(p * n))
    order = np.argsort(net, kind="stable")
    keep = np.ones(n, bool)
    if k > 0:
        keep[order[:k]] = False
        keep[order[-k:]] = False
    return keep


def winsor_mean(x: np.ndarray, p: float) -> float:
    lo, hi = np.quantile(x, p), np.quantile(x, 1 - p)
    return float(np.clip(x, lo, hi).mean())


def trims(net: np.ndarray, z: np.ndarray) -> dict[str, Any]:
    """Trimmed / winsorised / ex-top / ex-bottom statistics; the trims rank on net, and z is cut on the same trades."""
    out: dict[str, Any] = {"n": int(len(net)), "full": {"mean_net": float(net.mean()), "mean_z": float(z.mean()),
                                                      "t_hac": D.nw_t(net)[0]},
                           "median": {"net": float(np.median(net)), "z": float(np.median(z))}}
    for p in TRIMS:
        k = trim_idx(net, p)
        out[f"trim_{p * 100:g}pct_each_tail"] = {"kept": int(k.sum()), "mean_net": float(net[k].mean()),
                                                 "mean_z": float(z[k].mean()), "t_hac": D.nw_t(net[k])[0]}
    out["winsorised_5pct"] = {"mean_net": winsor_mean(net, 0.05), "mean_z": winsor_mean(z, 0.05)}
    o = np.argsort(net, kind="stable")
    out["ex_top5"] = {"mean_net": float(net[o[:-5]].mean()), "mean_z": float(z[o[:-5]].mean())}
    out["ex_bottom5"] = {"mean_net": float(net[o[5:]].mean()), "mean_z": float(z[o[5:]].mean())}
    out["top5_share_of_total_net"] = float(np.sort(net)[-5:].sum() / net.sum()) if net.sum() > 0 else None
    return out


def line_trims(X: pd.DataFrame, F: dict[str, np.ndarray], lo: str) -> dict[str, Any]:
    sess = X.index.to_numpy(str)
    span = F["window"] & (sess >= lo)
    g = X["gross"].to_numpy(float)
    cost = X.attrs["cost"]
    s_T = float(g[span].std(ddof=1))
    take = F["take"] & span
    filt = trims(g[take] - cost, g[take] / s_T)
    allb = trims(g[span] - cost, g[span] / s_T)
    lift = {}
    for key in [f"trim_{p * 100:g}pct_each_tail" for p in TRIMS]:
        lift[key] = filt[key]["mean_z"] - allb[key]["mean_z"]
    lift["full"] = filt["full"]["mean_z"] - allb["full"]["mean_z"]
    lift["median"] = filt["median"]["z"] - allb["median"]["z"]
    return {"trades": int(take.sum()), "s_T": s_T, "filtered": filt, "take_everything": allb, "lift_z": lift,
            "_z": g[take] / s_T, "_sess": sess[take]}


def pooled_trims(parts: list[dict[str, Any]], g_f2: dict[str, Any]) -> dict[str, Any]:
    z = np.concatenate([p["_z"] for p in parts])
    s = np.concatenate([p["_sess"] for p in parts])
    out = {"n": int(len(z))}
    t, se = M.clustered_t(z, s)
    out["full"] = {"G_P": float(z.mean()), "se": se, "t": t, "vs_F2": g_f2["full"]["mean_z"]}
    for p in TRIMS:
        k = trim_idx(z, p)
        t, se = M.clustered_t(z[k], s[k])
        key = f"trim_{p * 100:g}pct_each_tail"
        out[key] = {"G_P": float(z[k].mean()), "se": se, "t": t, "vs_F2": g_f2[key]["mean_z"],
                    "ratio_to_F2": float(z[k].mean() / g_f2[key]["mean_z"]) if g_f2[key]["mean_z"] else None}
    out["median"] = {"G_P": float(np.median(z)), "vs_F2": g_f2["median"]["z"]}
    return out


# ================================================================================ overlap
def daily_book(x: pd.Series) -> dict[str, float]:
    x = x.astype(float)
    dn = math.sqrt(float(np.mean(np.minimum(x.to_numpy(), 0) ** 2)))
    eq = x.cumsum().to_numpy()
    return {"total_net": float(x.sum()), "sharpe_daily": float(x.mean() / x.std(ddof=1) * math.sqrt(252)),
            "sortino_daily": float(x.mean() / dn * math.sqrt(252)) if dn > 0 else float("nan"),
            "max_drawdown_usd": float(np.max(np.maximum.accumulate(eq) - eq))}


def cell(es_net: np.ndarray | None, nq_net: np.ndarray | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for nm, x in (("ES", es_net), ("NQ", nq_net)):
        if x is None or len(x) == 0:
            continue
        out[nm] = {"n": int(len(x)), "mean_net": float(x.mean()), "median_net": float(np.median(x)),
                   "hit": float((x > 0).mean()), "total_net": float(x.sum()),
                   "t_hac": D.nw_t(x)[0] if len(x) > 10 else None}
    return out


def overlap(Xe: pd.DataFrame, Fe: dict[str, np.ndarray], Xn: pd.DataFrame, Fn: dict[str, np.ndarray]) -> dict[str, Any]:
    E_ = pd.DataFrame({"take": Fe["take"] & Fe["window"], "win": Fe["window"], "side": Xe["side"].to_numpy(float),
                       "gross": Xe["gross"].to_numpy(float), "tc": Fe["tc"]}, index=Xe.index)
    N_ = pd.DataFrame({"take": Fn["take"] & Fn["window"], "win": Fn["window"], "side": Xn["side"].to_numpy(float),
                       "gross": Xn["gross"].to_numpy(float), "tc": Fn["tc"]}, index=Xn.index)
    common = E_.index[E_["win"]].intersection(N_.index[N_["win"]])
    e, n = E_.loc[common], N_.loc[common]
    ce, cn = Xe.attrs["cost"], Xn.attrs["cost"]
    et, nt = e["take"].to_numpy(bool), n["take"].to_numpy(bool)
    same = (e["side"].to_numpy() == n["side"].to_numpy())
    es_net, nq_net = e["gross"].to_numpy() - ce, n["gross"].to_numpy() - cn
    both, eo, no, nei = et & nt, et & ~nt, ~et & nt, ~et & ~nt
    yrs = np.array([s[:4] for s in common])
    res: dict[str, Any] = {
        "common_sessions": int(len(common)), "span": [str(common[0]), str(common[-1])],
        "counts": {"both": int(both.sum()), "ES_only": int(eo.sum()), "NQ_only": int(no.sum()), "neither": int(nei.sum())},
        "jaccard": float(both.sum() / (et | nt).sum()),
        "p_NQ_takes_given_ES_takes": float(both.sum() / et.sum()), "p_ES_takes_given_NQ_takes": float(both.sum() / nt.sum()),
        "phi_take_flags": float(np.corrcoef(et.astype(float), nt.astype(float))[0, 1]),
        "direction_agreement": {"all_common_sessions": float(same.mean()), "when_both_take": float(same[both].mean()),
                                "when_ES_only": float(same[eo].mean()), "when_NQ_only": float(same[no].mean())},
        "tier_of_the_root_that_did_not_take": {
            "NQ_tc_on_ES_only_days": {"median": float(np.nanmedian(n["tc"].to_numpy()[eo])),
                                      "share_at_or_above_0.6": float(np.nanmean(n["tc"].to_numpy()[eo] >= 0.6))},
            "ES_tc_on_NQ_only_days": {"median": float(np.nanmedian(e["tc"].to_numpy()[no])),
                                      "share_at_or_above_0.6": float(np.nanmean(e["tc"].to_numpy()[no] >= 0.6))}},
        "cells": {
            "both_take_same_direction": cell(es_net[both & same], nq_net[both & same]),
            "both_take_opposite_direction": cell(es_net[both & ~same], nq_net[both & ~same]),
            "ES_only": {"ES_taken": cell(es_net[eo], None)["ES"], "NQ_unfiltered_same_days": cell(None, nq_net[eo])["NQ"]},
            "NQ_only": {"NQ_taken": cell(None, nq_net[no])["NQ"], "ES_unfiltered_same_days": cell(es_net[no], None)["ES"]},
            "neither_unfiltered": cell(es_net[nei], nq_net[nei])},
        "rho_gross_when_both_take": float(np.corrcoef(e["gross"].to_numpy()[both], n["gross"].to_numpy()[both])[0, 1]),
        "rho_gross_all_common": float(np.corrcoef(e["gross"].to_numpy(), n["gross"].to_numpy())[0, 1])}
    # where each book's profit comes from
    res["share_of_ES_F2_net_from_both_days"] = float(es_net[both].sum() / es_net[et].sum())
    res["share_of_NQ_F2_net_from_both_days"] = float(nq_net[both].sum() / nq_net[nt].sum())
    # the difference between the overlap and the rest, per root (Welch, descriptive)
    for nm, x, tk in (("ES", es_net, et), ("NQ", nq_net, nt)):
        a, b = x[both], x[tk & ~both]
        w = stats.ttest_ind(a, b, equal_var=False)
        res[f"{nm}_both_minus_alone"] = {"both_mean": float(a.mean()), "alone_mean": float(b.mean()),
                                          "diff": float(a.mean() - b.mean()), "welch_t": float(w.statistic)}
    # the books, one contract each, on the common sessions
    es_d = pd.Series(np.where(et, es_net, 0.0), index=common)
    nq_d = pd.Series(np.where(nt, nq_net, 0.0), index=common)
    res["books_on_common_sessions"] = {"ES_F2_1MES": daily_book(es_d), "NQ_F2_1MNQ": daily_book(nq_d),
                                       "both_1MES_plus_1MNQ": daily_book(es_d + nq_d),
                                       "rho_daily_net": float(np.corrcoef(es_d, nq_d)[0, 1])}
    # by year
    by = {}
    for y in sorted(set(yrs)):
        m = yrs == y
        by[y] = {"both": int((both & m).sum()), "ES_only": int((eo & m).sum()), "NQ_only": int((no & m).sum()),
                 "both_same_dir_ES_net": float(es_net[both & same & m].mean()) if (both & same & m).any() else None,
                 "both_same_dir_NQ_net": float(nq_net[both & same & m].mean()) if (both & same & m).any() else None,
                 "ES_only_net": float(es_net[eo & m].mean()) if (eo & m).any() else None,
                 "NQ_only_net": float(nq_net[no & m].mean()) if (no & m).any() else None}
    res["by_year"] = by
    return res


# ================================================================================ run
def run() -> dict[str, Any]:
    t0 = time.time()
    j = json.loads(D711_JSON.read_text(encoding="utf-8"))
    lo = j["A1"]["common_start"]
    Les = M.load_root("ES")
    ef = {T: M.clock_frame(Les, T) for T in CLOCKS}
    fe = {T: M.f2_on(X) for T, X in ef.items()}
    M.es_known_answer(ef[M.ANCHOR])
    a1 = {T: line_trims(ef[T], fe[T], lo) for T in CLOCKS}
    for T in CLOCKS:  # the known answer: D711's recorded lines, exactly
        rec = j["A1"]["clocks"][T]["filtered"]
        if a1[T]["trades"] != rec["trades"] or abs(a1[T]["filtered"]["full"]["mean_z"] - rec["mean_z"]) > 1e-12:
            raise DiagError(f"A1 {T} does not reproduce D711's line")
    pooled = pooled_trims([a1[T] for T in M.PLACEBO], a1[M.ANCHOR]["filtered"])
    if abs(pooled["full"]["G_P"] - j["A1"]["pooled_placebo"]["G_P"]) > 1e-12:
        raise DiagError("A1's pooled placebo does not reproduce D711's")
    rf = {r: M.clock_frame(M.load_root(r), M.ANCHOR) for r in M.A2_ROOTS}
    ff = {r: M.f2_on(X) for r, X in rf.items()}
    a2 = {"ES": line_trims(ef[M.ANCHOR], fe[M.ANCHOR], "2016-01-01")}
    for r in M.A2_ROOTS:
        a2[r] = line_trims(rf[r], ff[r], "2016-01-01")
        if a2[r]["trades"] != j["A2"]["roots"][r]["trades"]:
            raise DiagError(f"A2 {r} does not reproduce D711's trade count")
    ov = overlap(ef[M.ANCHOR], fe[M.ANCHOR], rf["NQ"], ff["NQ"])
    strip = lambda d: {k: v for k, v in d.items() if not k.startswith("_")}  # noqa: E731
    return {"spec": "D711 addendum, post hoc and descriptive (the principal's request, 2026-09-30)",
            "A1_clocks": {T: strip(v) for T, v in a1.items()}, "A1_pooled_placebo": pooled,
            "A2_roots_at_1530": {r: strip(v) for r, v in a2.items()}, "overlap_ES_NQ": ov,
            "runtime_min": round((time.time() - t0) / 60, 2)}


def selftest() -> int:
    x = np.array([5.0, -100.0, 1.0, 2.0, 3.0, 200.0, 4.0, 0.0, -1.0, 6.0])
    k = trim_idx(x, 0.1)
    if sorted(x[k].tolist()) != [-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
        raise SystemExit(f"selftest: the 10 % trim kept {sorted(x[k].tolist())}")
    if trim_idx(x, 0.01).sum() != 10:
        raise SystemExit("selftest: a 1 % trim of 10 trades should drop nothing")
    w = winsor_mean(np.arange(101.0), 0.05)
    if not math.isclose(w, 50.0):
        raise SystemExit("selftest: a symmetric winsorisation moved the centre")
    t = trims(x, x / 10)
    if not (t["ex_top5"]["mean_net"] < t["full"]["mean_net"] < t["ex_bottom5"]["mean_net"]):
        raise SystemExit("selftest: ex-top / ex-bottom are the wrong way round")
    print("selftest OK: the trims drop the named tails from both ends, a 1 % trim of 10 drops none, the winsorised "
          "centre holds, ex-top < full < ex-bottom on a two-tailed book.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    out = run()
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pooled": out["A1_pooled_placebo"], "overlap_counts": out["overlap_ES_NQ"]["counts"],
                      "runtime_min": out["runtime_min"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
