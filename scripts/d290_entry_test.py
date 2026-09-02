"""Is the one-bar edge the ENTRY PRINT, or real fast information?

    uv run python scripts/d290_entry_test.py [--workers 6]

THE SKIP TEST COULD NOT ANSWER THIS, and saying so is the point. Skipping a bar
removes the bid-ask bounce AND any genuinely fast signal at the same time, so
"edge dies at skip 1" is consistent with both. The principal caught that.

THREE CUTS, EACH ANSWERING SOMETHING THE OTHERS CANNOT.

1. OVERNIGHT vs INTRADAY. You form the position at close[t-1] and the signal IS
   a property of that print. If the edge is bounce, the next print (open[t])
   averages half a spread away, so the artifact is realised ENTIRELY in the
   close->open segment and the open->close segment is clean.
   NOT DECISIVE ALONE: real overnight news lands in the same segment.

2. OPEN ENTRY. Same signal, same one-bar horizon, but enter at open[t] rather
   than at close[t-1]. Removes the print that generated the signal while keeping
   the information fresh. Practical rather than diagnostic: it says whether the
   edge is CAPTURABLE, not what it is.

3. LIQUIDITY TERCILES -- THE DECISIVE ONE. Bounce magnitude is PROPORTIONAL TO
   THE SPREAD; information is not. Split the universe by each name's own trailing
   Corwin-Schultz half-spread, rebuild the book inside each tercile, and compare.
   If edge_wide / edge_tight tracks spread_wide / spread_tight, it is bounce. If
   the edge is flat across terciles, it is not.

EVERYTHING HERE IS PRICE-ONLY AND INTERNALLY CONSISTENT. D290's `fwd` uses total
log returns (dividends included); this file builds overnight and intraday from
the OHLC grid so that `overnight + intraday == the price return EXACTLY`, which
is asserted rather than assumed. Over one bar the dividend difference is
negligible and applies to both legs.

AN OVERNIGHT ACROSS AN INTERNAL HOLE IS NOT AN OVERNIGHT. 134 of 1,573 names
carry halts or provider holes where the previous OWN bar is weeks earlier. Those
cells are dropped, exactly as `ragged_session_scores` does.

Hoisted the same way as `d290_skip_all`: one column sort per (candidate,
universe), one leg build per N. Threads, because argsort and bincount release
the GIL and six of them share one 2.69 GB cache.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
SP = _load("d285sp", "d285_spread_estimate.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
B, C, FN = M.B, M.C, M.FN

OUT = REPO / "data" / "d290_entry_test.json"
D290 = json.loads((REPO / "data" / "d290_stage1.json").read_text())
NS = tuple(D290["n_levels"])
KS = tuple(D290["horizons"])


def segments(g, live, panel):
    """Overnight, intraday and their composition, price-only and adjacent-only."""
    O, Cl = g["open"], g["close"]
    n, T = Cl.shape
    on = np.full((n, T), np.nan)
    idr = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size < 2:
            continue
        o, c = O[i, at], Cl[i, at]
        prev = np.concatenate([[np.nan], c[:-1]])
        adj = np.zeros(at.size, dtype=bool)
        adj[1:] = np.diff(at) == 1          # a gap across a hole is not a night
        with np.errstate(invalid="ignore", divide="ignore"):
            on[i, at] = np.where(adj & (prev > 0) & (o > 0), np.log(o / prev), np.nan)
            idr[i, at] = np.where((o > 0) & (c > 0), np.log(c / o), np.nan)
    return on, idr


def cum(logs, live, ks):
    """expm1 of the forward cumulative sum, per horizon. Same shape as M.forward_returns."""
    T = live.shape[1]
    out, acc, ok = {}, np.zeros_like(logs), live.copy()
    for k in range(1, max(ks) + 1):
        acc[:, :T - k + 1] += logs[:, k - 1:]
        ok[:, :T - k + 1] &= live[:, k - 1:]
        if k in ks:
            out[k] = np.where(ok, np.expm1(acc), np.nan).astype(np.float32)
    return out


def open_entry(on, idr, live, ks):
    """open[t] -> close[t+k-1]: the total path MINUS the first overnight leg.

    Built by subtracting the entry night from the price path rather than by a
    second accumulation, so it cannot drift from the close-entry series.
    """
    tot = on + idr
    T = live.shape[1]
    out, acc, ok = {}, np.zeros_like(tot), live.copy()
    for k in range(1, max(ks) + 1):
        acc[:, :T - k + 1] += tot[:, k - 1:]
        ok[:, :T - k + 1] &= live[:, k - 1:]
        if k in ks:
            out[k] = np.where(ok, np.expm1(acc - on), np.nan).astype(np.float32)
    return out


def book(score, base, N, T):
    order, cnt = M.rank_columns(score, base)
    ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
    return np.nonzero(ev_lo), np.nonzero(ev_hi)


def stat(f, lo_idx, hi_idx, T):
    """ALL THREE CONSTRUCTIONS, not just the spread.

    A first version returned `lo - hi` only, so there was no capturability
    diagnostic for the long or short book -- and the short book is the personal
    track's actual objective. `short` is sign-flipped so positive always means
    the construction MADE money, matching D290.
    """
    slo, clo = M.bar_sums(f, lo_idx[0], lo_idx[1], T)
    shi, chi = M.bar_sums(f, hi_idx[0], hi_idx[1], T)
    m = (clo > 0) & (chi > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    lo, hi = slo[m] / clo[m], shi[m] / chi[m]
    out = {}
    for name, d in (("long", lo), ("short", -hi), ("spread", lo - hi)):
        sd = d.std(ddof=1)
        out[name] = (float(d.mean() * 1e4),
                     float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else 0.0)
    return out


def one(score, base, terc, grids, T):
    """All three cuts for one candidate."""
    fwd_c, fwd_o, on1, id1, tot1 = grids
    res = {}
    peak = None
    for N in NS:
        lo, hi = book(score, base, N, T)
        res[str(N)] = {
            "overnight_k1": stat(on1, lo, hi, T),
            "intraday_k1": stat(id1, lo, hi, T),
            "total_k1": stat(tot1, lo, hi, T),
            "close_entry": {str(k): stat(fwd_c[k], lo, hi, T) for k in KS},
            "open_entry": {str(k): stat(fwd_o[k], lo, hi, T) for k in KS},
        }
    # liquidity terciles, at k=1 only -- the decisive cut
    tq = {}
    for name, mask in terc.items():
        b = base & mask
        row = {}
        for N in NS:
            if int(b.sum()) < 1000:
                continue
            lo, hi = book(score, b, N, T)
            row[str(N)] = stat(tot1, lo, hi, T)
        tq[name] = row
    res["terciles_k1"] = tq
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    t0 = time.time()
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(B.FIXTURE), "CACHE IS STALE -- rebuild"
    panel, cleaned = M.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    base = z["warm"] & live
    T = live.shape[1]
    g = P1.build_grids(panel, cleaned)
    print(f"loaded in {time.time() - t0:.0f}s", flush=True)

    on, idr = segments(g, live, panel)
    tot = on + idr
    # ASSERTED, NOT ASSUMED: the two segments compose to the price return.
    px = np.full_like(tot, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        px[:, 1:] = np.log(g["close"][:, 1:] / g["close"][:, :-1])
    m = np.isfinite(tot) & np.isfinite(px) & live
    err = float(np.abs(tot[m] - px[m]).max())
    print(f"  overnight + intraday == price return on {int(m.sum()):,} cells, "
          f"max |delta| {err:.2e}")
    assert err < 1e-9, "the session decomposition does not compose"

    fwd_c = cum(tot, live, KS)
    fwd_o = open_entry(on, idr, live, KS)
    on1 = np.where(np.isfinite(on), np.expm1(on), np.nan).astype(np.float32)
    id1 = np.where(np.isfinite(idr), np.expm1(idr), np.nan).astype(np.float32)
    tot1 = fwd_c[1]

    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    # per-bar cross-sectional terciles, so the split is not a time effect
    terc = {}
    q = np.full(half.shape, np.nan)
    for t in range(T):
        v = np.where(base[:, t], half[:, t], np.nan)
        f = np.isfinite(v)
        if f.sum() < 30:
            continue
        r = np.argsort(np.argsort(v[f]))
        q[f, t] = r / max(r.max(), 1)
    terc = {"tight": base & (q < 1 / 3), "mid": base & (q >= 1 / 3) & (q < 2 / 3),
            "wide": base & (q >= 2 / 3)}
    for k, v in terc.items():
        sp = half[v & np.isfinite(half)]
        print(f"  {k:6s} tercile: {int(v.sum()):>9,} cells, "
              f"mean half-spread {sp.mean():6.1f} bp/side")
    ratios = {k: float(half[v & np.isfinite(half)].mean()) for k, v in terc.items()}
    print(f"  SPREAD RATIO wide/tight = {ratios['wide'] / ratios['tight']:.2f}x "
          f"-- a pure bounce edge should scale by this")

    cands = list(BC.CANDIDATES)
    grids = (fwd_c, fwd_o, on1, id1, tot1)
    print(f"\n  {len(cands)} candidates x {len(NS)} N | {a.workers} threads",
          flush=True)
    res = FN.parallel_map(lambda c, s: one(s, base, terc, grids, T),
                          [(c, z[c]) for c in cands],
                          workers=a.workers, progress=True)

    json.dump({"purpose": "Is the one-bar edge the entry print or real fast "
                          "information? Overnight/intraday split, open entry, and "
                          "liquidity terciles -- the last is decisive for bounce.",
               "spread_ratio_wide_over_tight": ratios["wide"] / ratios["tight"],
               "tercile_half_spread_bp": ratios, "n_levels": list(NS),
               "horizons": list(KS), "results": res,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
