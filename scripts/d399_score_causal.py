"""Score a construction against the CAUSAL ground truth -- the forward-only replay.

    uv run python scripts/d399_score_causal.py [--branch E] [--min-piv 3] [--h-annual 4] [--all]

GROUND TRUTH: `data/d399_live_ground_truth.json`. 25 trendlines the principal drew while stepping
GME bar by bar with no way forward, so nothing in it saw the future. A causal construction is
scored against it with NO oracle caveat -- the first time that has been true here.

WHY A NEW SCORE. The hindsight scorer was `AGREEMENT * RECALL**0.25` over bars where BOTH sides
were on, and it had three failures the causal set lets us fix:

  1. IT NEVER PENALISED A FALSE POSITIVE. Claiming a trend where the principal saw none cost
     nothing, which is why branches B, C and D scored well while declaring a trend on all 260
     bars. The causal set labels EVERY bar he stepped through -- a slope or N/A -- so a false
     positive is now a measurable error rather than an unscored region.
  2. FRAGMENTING WAS FREE, because per-bar agreement cannot tell one 46-bar line from five 9-bar
     ones. That criticism has now partly dissolved anyway: drawn live his median trend lives
     SEVEN bars, so the constructions' 8-9 bar segments were never the defect they looked like.
  3. A TIME ROTATION OF THE FITTED GRADIENTS SCORED 0.29 AT THE MEDIAN against the incumbent's
     0.236 -- the metric was satisfied by the slope MARGINAL rather than by placement. So this
     scorer carries its own exact rotation null and reports the excess, not the raw number.

THE SCORE

    per bar t that the principal SAW, per side:
        TP  both call a trend      -> quality_t = max(0, 1 - |g_fit - g_true| / max(|g_true|, DELTA))
        TN  both call no trend     -> correct, and counted in precision/recall only
        FP  construction says trend, he says N/A
        FN  he says trend, construction says N/A

    QUALITY = mean(quality_t) over TP bars          how right are the slopes it does give
    P       = TP / (TP + FP)                        how often a claimed trend is real
    R       = TP / (TP + FN)                        how much of his trend it finds
    F_0.5   = 1.25 * P * R / (0.25 * P + R)         recall weighted a QUARTER of precision
    SCORE   = QUALITY * F_0.5

F_0.5 is the principal's rule -- less coverage should cost only a little -- expressed so that it
cannot be gamed the way a bare exponent could: `never a trend` gives TP = 0 and scores ZERO
rather than winning on true negatives, and `always a trend` is capped by precision.

Scores nothing else. Admits nothing (R15).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
GT = REPO / "data" / "d399_live_ground_truth.json"
OUT = REPO / "data" / "d399_causal_scores.json"
BETA2 = 0.25          # beta = 0.5: recall counts a quarter of precision


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def score_side(g_fit, g_true, seen, delta):
    """The score and every part of it, for one side."""
    f_on = np.isfinite(g_fit) & seen
    t_on = np.isfinite(g_true) & seen
    TP = int((f_on & t_on).sum())
    FP = int((f_on & ~t_on).sum())
    FN = int((~f_on & t_on).sum())
    TN = int((~f_on & ~t_on & seen).sum())
    if TP == 0:
        return dict(TP=0, FP=FP, FN=FN, TN=TN, precision=0.0, recall=0.0,
                    f_beta=0.0, quality=None, score=0.0)
    both = f_on & t_on
    gt = g_true[both]
    rel = np.abs(g_fit[both] - gt) / np.maximum(np.abs(gt), delta)
    quality = float(np.clip(1.0 - rel, 0.0, None).mean())
    P = TP / (TP + FP) if (TP + FP) else 0.0
    R = TP / (TP + FN) if (TP + FN) else 0.0
    F = ((1 + BETA2) * P * R / (BETA2 * P + R)) if (P + R) > 0 else 0.0
    return dict(TP=TP, FP=FP, FN=FN, TN=TN, precision=round(P, 4), recall=round(R, 4),
                f_beta=round(F, 4), quality=round(quality, 4), score=round(quality * F, 4))


def rotation_null(g_fit, g_true, seen, delta, lo, hi):
    """Exact null: rotate the FITTED series through every offset inside the seen window.

    Enumerated, so the p95 carries no sampling error (CLAUDE.md's escape, D361's ROT). Rotating
    destroys placement and keeps the marginal, which is exactly the failure mode the hindsight
    scorer had -- so if a construction cannot beat its own rotation, it is not placing anything."""
    idx = np.arange(lo, hi + 1)
    base = g_fit[idx]
    m = idx.size
    out = []
    for k in range(1, m):
        rot = np.full_like(g_fit, np.nan)
        rot[idx] = np.roll(base, k)
        out.append(score_side(rot, g_true, seen, delta)["score"])
    a = np.asarray(out, float)
    return dict(draws=int(a.size), p50=round(float(np.median(a)), 4),
                p95=round(float(np.quantile(a, .95)), 4), max=round(float(a.max()), 4))


def build(name, cfg, DR, UO, PV, m, lo_px, hi_px, ps):
    """Every construction reachable from this repo, behind one signature."""
    h = DR.h_of_annual(cfg.get("h_annual", 4.0))
    mp = cfg.get("min_piv", 3)
    out = {}
    for kind, sign, px in (("support", -1, lo_px), ("resistance", +1, hi_px)):
        idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        lp = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
        if name == "E":
            G, _L, _a, _w = DR.segment_windows(idx, lp, np.log(px), m, UO.K, h, sign,
                                               min_piv=mp, max_window=UO.WINDOW)
        elif name in ("B", "C", "D"):
            g_fix, c_fix = UO.rolling_fit(m, idx, lp, UO.K)
            cnt, _sp = DR.pivot_support(m, idx, UO.K, UO.WINDOW)
            ok = cnt >= mp
            if name == "B":
                G, _L, _a, _p, _g = DR.ratchet_corrected(g_fix, c_fix, np.log(px), h, sign, ok)
            else:
                RT = DR.ratchet_reset if name == "D" else DR.ratchet_tight
                G, _L, _a, _p, _g = RT(g_fix, np.log(px), h, sign, UO.WINDOW, ok)
        elif name == "segmentation":
            SEG = _load("d399seg", "d399_alt_segment.py")
            ev = SEG.sliding_events(idx, lp, UO.K, "abs", 0.08, 0.0, 3)
            G, _S = SEG.broadcast(ev, m, 5, True, DR.DELTA)
        elif name == "two-pivot":
            PP = _load("d399pp", "d399_alt_pivotpair.py")
            dat = PP.load_data(UO.K)
            cells = PP.run_cell(dat, "b_far", 0.0, 42, True, UO.K, {})
            G, _L2, _x, _y = cells[kind]
            G = PP.apply_min_run(PP.apply_delta(G, DR.DELTA), DR.MIN_RUN)
        else:
            raise SystemExit(f"unknown construction {name}")
        out[kind] = G
    return out


CONSTRUCTIONS = [("B", {}), ("C", {}), ("D", {}), ("E", {}),
                 ("segmentation", {}), ("two-pivot", {})]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default=None)
    ap.add_argument("--min-piv", type=int, default=3)
    ap.add_argument("--h-annual", type=float, default=4.0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-null", action="store_true")
    a = ap.parse_args()

    DR = _load("d399draw", "d399_draw_construction.py")
    UO = _load("d240", "run_uptrend_onset.py")
    RP = _load("rp", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV

    gt = json.loads(GT.read_text())
    start, n, seen_to = int(gt["start_bar"]), int(gt["n"]), int(gt["seen_through"])
    first_seen = min(L["drawn_at"] for L in gt["lines"])
    seen = np.zeros(n, bool)
    seen[first_seen:seen_to + 1] = True
    g_true = {k: np.array([np.nan if v is None else v for v in gt[f"g_{k}"]], float)
              for k in ("support", "resistance")}

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[gt["symbol"]]
    m = len(bars)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    ps = PV(bars, UO.K)

    todo = CONSTRUCTIONS if (a.all or not a.branch) else [(a.branch, {})]
    print(f"\n  CAUSAL ground truth: {gt['symbol']} bars {first_seen}-{seen_to}, "
          f"{len(gt['lines'])} lines, median life {gt['median_live_bars']:.0f} bars")
    print(f"  he called NO TREND on {gt['bars_no_trend']} of {seen.sum()} bars seen "
          f"({100 * gt['bars_no_trend'] / seen.sum():.0f}%)\n")
    print(f"  {'construction':>14s} {'side':>11s} {'TP':>5s} {'FP':>5s} {'FN':>5s} "
          f"{'prec':>6s} {'rec':>6s} {'F.5':>6s} {'qual':>6s} {'SCORE':>7s}")

    res = dict(ground_truth=str(GT.relative_to(REPO)), symbol=gt["symbol"],
               first_seen=first_seen, seen_through=seen_to, beta=0.5,
               note="Causal: the drawn lines never saw the future, so there is no oracle caveat.",
               constructions={})
    for name, cfg in todo:
        cfg = dict(cfg, min_piv=a.min_piv, h_annual=a.h_annual)
        G = build(name, cfg, DR, UO, PV, m, lo, hi, ps)
        cell, scores = {}, []
        for kind in ("support", "resistance"):
            gf = G[kind][start:start + n]
            s = score_side(gf, g_true[kind], seen, DR.DELTA)
            cell[kind] = s
            scores.append(s["score"])
            print(f"  {name:>14s} {kind:>11s} {s['TP']:>5d} {s['FP']:>5d} {s['FN']:>5d} "
                  f"{s['precision']:>6.3f} {s['recall']:>6.3f} {s['f_beta']:>6.3f} "
                  f"{(s['quality'] or 0):>6.3f} {s['score']:>7.3f}")
        tot = float(np.mean(scores))
        cell["SCORE"] = round(tot, 4)
        if not a.no_null:
            nl = {}
            for kind in ("support", "resistance"):
                gf = G[kind][start:start + n]
                nl[kind] = rotation_null(gf, g_true[kind], seen, DR.DELTA, first_seen, seen_to)
            p95 = float(np.mean([nl[k]["p95"] for k in nl]))
            p50 = float(np.mean([nl[k]["p50"] for k in nl]))
            cell["null"] = nl
            cell["null_p50"] = round(p50, 4)
            cell["null_p95"] = round(p95, 4)
            cell["clears_null"] = bool(tot > p95)
            cell["excess"] = round((tot - p50) / (p95 - p50), 3) if p95 > p50 else None
            print(f"  {'':>14s} {'OVERALL':>11s} {'':>5s} {'':>5s} {'':>5s} {'':>6s} {'':>6s} "
                  f"{'':>6s} {'':>6s} {tot:>7.3f}   null p50 {p50:.3f} p95 {p95:.3f} -> "
                  f"{'CLEARS' if tot > p95 else 'inside'}")
        else:
            print(f"  {'':>14s} {'OVERALL':>11s} {'':>5s} {'':>5s} {'':>5s} {'':>6s} {'':>6s} "
                  f"{'':>6s} {'':>6s} {tot:>7.3f}")
        res["constructions"][name] = cell
        print()

    OUT.write_text(json.dumps(res, indent=1))
    print(f"  [P] {OUT.relative_to(REPO)} written")
    print("\nNothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
