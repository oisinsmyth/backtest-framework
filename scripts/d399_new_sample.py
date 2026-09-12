"""D399 -- THE CONSTRUCTION ON NAMES AND DATES IT HAS NEVER SEEN.

    uv run python scripts/d399_new_sample.py --list             the draw only, no run
    uv run python scripts/d399_new_sample.py                    run the frozen cell, write charts
    uv run python scripts/d399_new_sample.py --compare          the frozen cell vs. extend-back

WHY. Everything in D399 so far is ONE name over ONE 260-bar window -- GME, bars 2429-2688 -- and
the construction was selected on it by eye across several hundred cells. Whatever it does here is
the first evidence that any of that survives contact with other data.

NO SCORE BY DEFAULT. Neither hand-drawn ground truth transfers -- the 25 lines and the 53 pivots
are GME's alone -- and the principal adjusts from what he sees. Forward return by state is still
computed and stored (a channel's claim is that direction persists while it holds, and that needs
no drawing to test), but it is printed only under --score.

THE SELECTION RULE, DECLARED HERE BEFORE ANY CHART IS DRAWN so the sample cannot be chosen to
flatter the construction:

  1. Universe: the same `us_shorts_daily_raw` ragged panel GME came from.
  2. GME is EXCLUDED outright.
  3. Every bar of the candidate window must pass D343's keep_v2 floor -- price >= $5 at t-1, dollar
     volume at or above the 28th percentile, DV finite.
  4. SPLIT GUARD. The daily fixture is NOT split-adjusted, and an unadjusted split manufactures a
     pivot, a body break and a channel inversion out of nothing. Any window containing a single-bar
     |log return| > SPLIT_LR is rejected, and the count is reported rather than hidden.
  5. The window is 260 bars, exactly GME's length.
  6. N_DRAW (name, start) pairs are drawn uniformly from every eligible pair with one seeded RNG.
     An explicit array seed -- never `hash()` on a str, which is salted per process (D392).

THE CELL, frozen, as chosen by the principal:
    k=1 tie-tolerant pivots | dg off | dh 30% | body break on | min_piv 4 | min_width 0
    break bar becomes a provisional pivot | intercept from body clearance | age decay 0.80

EXTEND-BACK (`--compare`) is the same cell with `carry` replaced by a TEST: when a new segment
first qualifies, the invalidated segment's pivots are walked newest-first and each is kept while
it still fits -- within the height deadband of the new line, and with a back-projection that
clears every body. See `recalc_pair.walk_back`.
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
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "d399_new_sample.json"
CHART = REPO / "temp" / "d399_new_sample_chart.json"
CMP_OUT = REPO / "data" / "d399_extend_compare.json"
CMP_CHART = REPO / "temp" / "d399_extend_chart.json"

SEED = 20260910
N_DRAW = 12
WIN = 260
SPLIT_LR = 0.40          # ~49% in one bar; a split, not a move
HORIZONS = (1, 5, 21)
EXCLUDE = ("GME",)

CELL = dict(k=1, dg=None, dh=30.0, use_body=True, min_piv=4, min_width=0.0,
            break_pivot=True, anchor_clear=True, decay_end=0.80, carry=3,
            extend_back=False,
            # THE REVIEW SWITCHES, at their defaults (see recalc_pair's docstring). Stated here
            # so the record shows them rather than inheriting them.
            height_mode="raw", syn_ttl=True)
# CARRY STAYS AT 3. The first version set it to 0 on the theory that the walk made it redundant,
# and coverage fell 69% -> 38% -- entirely the carry change, measured by running the four corners
# separately. Carry and the walk answer DIFFERENT invalidations: after a gradient or height drift
# the side goes dormant with no new information and needs `carry` points to re-qualify at all;
# after a BREAK there is new information and the walk decides how far back the new trend reaches.
# With both: coverage 73%, segments 14 -> 10, median life 15 -> 20, reach 16 -> 28 bars.
CELL_EXT = dict(CELL, carry=3, extend_back=True, back_tol=None, walk_chain="body_only",
                max_reach=130)
# THE ENVELOPE: one change from CELL_EXT -- the estimator. The line is the most-respected edge of
# the segment's pivots (gradient and level from the same two touched points) instead of a weighted
# regression. The clearance intercept and the age decay were repairs to the regression and do not
# apply; touch_tol is the width of a wick, and min_touch is the chartist's own criterion.
CELL_ENV = dict(CELL_EXT, fit_mode="envelope", anchor_clear=False, decay_end=1.0,
                touch_tol=0.025, min_touch=3)
# THE PRINCIPAL'S FINAL CONSTRUCTION, 2026-09-10, chosen by eye on the live page and handed over
# as its settings line, transcribed here field for field:
#   k=2 mp=2 maxp=0 carry=7 dh=20 dg=0 mw=10 body=on bdepth=2 bbars=2 syn=on anchor=quantile
#   aq=0.2 dmode=rank decay=0.76 height=anchored ttl=on walk=on btol=-1 chain=body_only
#   reach=130 stalew=35 staled=18 stalestat=mean fittol=16 pairbreak=on pairdraw=on fit=ols
#   ttol=0.37 mt=1
# (ttol and mt act only under the envelope or the respect age law; neither is in use here.)
CELL_FINAL = dict(
    k=2, min_piv=2, max_piv=None, carry=7, dh=20.0, dg=None, min_width=10.0, use_body=True,
    break_depth=2.0, break_bars=2, break_pivot=True, anchor_clear=True, anchor_mode="quantile",
    anchor_q=0.2, decay_mode="rank", decay_end=0.76, height_mode="anchored", syn_ttl=True,
    extend_back=True, back_tol=None, walk_chain="body_only", max_reach=130,
    stale_w=35, stale_d=18.0, stale_stat="mean", fit_tol=16.0, pair_break=True, pair_draw=True,
    fit_mode="ols", touch_tol=0.37, min_touch=1)
SETTINGS_LINE_FINAL = ("k=2 mp=2 maxp=0 carry=7 dh=20 dg=0 mw=10 body=on bdepth=2 bbars=2 syn=on "
                       "anchor=quantile aq=0.2 dmode=rank decay=0.76 height=anchored ttl=on walk=on "
                       "btol=-1 chain=body_only reach=130 stalew=35 staled=18 stalestat=mean "
                       "fittol=16 pairbreak=on pairdraw=on fit=ols ttol=0.37 mt=1")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def draw_sample(panel, cleaned, UF, n, seed=SEED, exclude=EXCLUDE):
    """The declared rule, applied. Returns the draw and the rejection counts. `exclude` is the
    names kept out -- GME by default; a second draw also keeps out the first draw's names."""
    cand, rej_split, rej_floor, rej_short = [], 0, 0, 0
    for s in panel.symbols:
        if s in exclude:
            continue
        bars = cleaned.get(s)
        if bars is None or len(bars) < WIN + 40:
            rej_short += 1
            continue
        cl = np.array([b.bar.close for b in bars], float)
        vol = np.array([b.bar.volume for b in bars], float)
        raw = np.array([getattr(b.bar, "raw_close", b.bar.close) for b in bars], float)
        with np.errstate(divide="ignore", invalid="ignore"):
            lr = np.diff(np.log(cl))
        dv = raw * vol
        ok_px = raw >= UF.PX_MIN
        thr = (np.nanpercentile(dv[np.isfinite(dv) & (dv > 0)], UF.DV_PCT)
               if np.isfinite(dv).any() else np.inf)
        ok = ok_px & np.isfinite(dv) & (dv >= thr)
        m = len(bars)
        for st in range(20, m - WIN):
            if not ok[st:st + WIN].all():
                rej_floor += 1
                continue
            if np.nanmax(np.abs(lr[st:st + WIN - 1])) > SPLIT_LR:
                rej_split += 1
                continue
            cand.append((s, st))
    if not cand:
        raise SystemExit("no eligible window -- the floor or the split guard is too tight")
    rng = np.random.default_rng([seed, n, WIN])
    pick = rng.choice(len(cand), size=min(n, len(cand)), replace=False)
    draw = [cand[int(i)] for i in sorted(pick)]
    return draw, dict(eligible=len(cand), rej_short=rej_short, rej_floor=rej_floor,
                      rej_split=rej_split)


def run_one(bars, st, cell, RC, DR, PVT):
    """The cell on one name. Returns (row, chart, fwd) with the invariants asserted."""
    m = len(bars)
    op = np.array([b.bar.open for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    with np.errstate(divide="ignore"):
        body_log = {"support": np.log(np.minimum(op, cl)),
                    "resistance": np.log(np.maximum(op, cl))}
        ext_log = {"support": np.log(lo), "resistance": np.log(hi)}
    ps = PVT(bars, cell["k"])
    piv = {}
    for kd, sg in (("support", -1), ("resistance", +1)):
        idx = np.array([p.index for p in ps if p.sign == sg], dtype=int)
        lp = np.log(np.array([p.price for p in ps if p.sign == sg], float))
        piv[kd] = (idx, lp)
    G, L, S, why = RC.recalc_pair(
        piv, cell["k"], body_log, m, carry=cell["carry"], min_piv=cell["min_piv"],
        max_dg=(RC.INF if cell["dg"] is None else DR.h_of_annual(cell["dg"])),
        max_dh=math.log1p(cell["dh"] / 100), use_body=cell["use_body"],
        min_width=math.log1p(cell["min_width"] / 100), delta=DR.DELTA, ext_log=ext_log,
        break_pivot=cell["break_pivot"], anchor_clear=cell["anchor_clear"],
        decay_end=cell["decay_end"], extend_back=cell["extend_back"],
        back_tol=(None if cell.get("back_tol") is None else math.log1p(cell["back_tol"] / 100)),
        fit_mode=cell.get("fit_mode", "ols"), touch_tol=cell.get("touch_tol", 0.025),
        min_touch=cell.get("min_touch", 3),
        height_mode=cell.get("height_mode", "raw"), walk_chain=cell.get("walk_chain", "body_only"),
        max_reach=cell.get("max_reach", 130), syn_ttl=cell.get("syn_ttl", True),
        stale_w=cell.get("stale_w"), stale_d=math.log1p(cell.get("stale_d", 5.0) / 100),
        stale_stat=cell.get("stale_stat", "mean"),
        fit_tol=(None if cell.get("fit_tol") is None else math.log1p(cell["fit_tol"] / 100)),
        pair_break=cell.get("pair_break", False), pair_draw=cell.get("pair_draw", False),
        anchor_mode=cell.get("anchor_mode"),
        break_depth=math.log1p(cell.get("break_depth", 0.0) / 100),
        break_bars=cell.get("break_bars", 1), max_piv=cell.get("max_piv"),
        decay_mode=cell.get("decay_mode", "span"), anchor_q=cell.get("anchor_q", 0.15),
        break_keep=cell.get("break_keep"))
    win = np.zeros(m, bool)
    win[st:st + WIN] = True
    btol = math.log1p(cell.get("break_depth", 0.0) / 100)
    RC.assert_no_inversion(L, win, math.log1p(cell["min_width"] / 100))
    RC.assert_respects_body(L, body_log, win, tol=btol)
    RC.assert_no_resurrection(G, L, S, body_log, tol=btol,
                              bars=cell.get("break_bars", 1))  # [Z], on the whole series

    cov, lives, thru, segs_out, reach = 0, [], 0, {}, []
    for kd in ("support", "resistance"):
        lv = L[kd][st:st + WIN]
        seg = S[kd][st:st + WIN]
        fin = np.isfinite(lv)
        cov += int(fin.sum())
        out_s, i = [], 0
        while i < WIN:
            if not (fin[i] and seg[i] >= 0):
                i += 1
                continue
            j = i
            while j + 1 < WIN and seg[j + 1] == seg[i] and fin[j + 1]:
                j += 1
            lives.append(j - i + 1)
            g = float(G[kd][st + i])
            c = float(lv[i]) - g * (i + st)
            aa = int(seg[i]) - st
            if np.isfinite(g) and np.isfinite(c):
                out_s.append(dict(s0=aa, t0=int(i), t1=int(j), g=g, c=c,
                                  anchored_before=bool(aa < i)))
                reach.append(i - aa)
            i = j + 1
        segs_out[kd] = out_s
        ref = body_log[kd][st:st + WIN]
        bad = (ref < lv - btol) if kd == "support" else (ref > lv + btol)
        thru += int((bad & fin).sum())

    # forward return by state, computed always, printed only on --score
    gS, gR = G["support"], G["resistance"]
    up = np.isfinite(gS) & np.isfinite(gR) & (gS > DR.DELTA) & (gR > DR.DELTA)
    dn = np.isfinite(gS) & np.isfinite(gR) & (gS < -DR.DELTA) & (gR < -DR.DELTA)
    with np.errstate(divide="ignore", invalid="ignore"):
        lc = np.log(cl)
    fwd = {}
    for hh in HORIZONS:
        f = np.full(m, np.nan)
        f[:m - hh] = lc[hh:] - lc[:m - hh]
        w = win & np.isfinite(f)
        fwd[hh] = dict(UP=f[w & up].tolist(), DOWN=f[w & dn].tolist(), ALL=f[w].tolist())

    # COUNTS INSIDE THE WINDOW, from the event list (D4). The whole-series totals are kept
    # beside them under `whole`, and each window count is asserted not to exceed its total.
    inwin = [e for e in why["events"] if st <= e[0] < st + WIN]

    def cnt(kind):
        return sum(1 for e in inwin if e[2] == kind)

    fired = {kk: cnt(kk) for kk in ("gradient", "height", "body", "inverted", "stale",
                                    "stale_abandoned", "stale_unconfirmed", "unfit", "pair",
                                    "body_poke")}
    whole = {kk: why[kk] for kk in ("gradient", "height", "body", "inverted", "syn_made",
                                    "syn_confirmed", "syn_dropped", "extended",
                                    "extended_pts", "max_reach_hit", "nan_fit", "stale",
                                    "stale_abandoned", "stale_unconfirmed", "unfit", "pair",
                                    "body_poke")}
    row = dict(coverage=cov, side_bars=2 * WIN, segments=len(lives),
               median_life=(float(np.median(lives)) if lives else None),
               median_reach=(float(np.median(reach)) if reach else None),
               max_reach=(int(max(reach)) if reach else None),
               through_body=thru, inverted=0,
               syn_made=cnt("syn_made"), syn_ratified=cnt("syn_confirmed"),
               syn_dropped=cnt("syn_dropped"),
               extended=cnt("extended"), extended_pts=cnt("extended_pt"),
               max_reach_hit=cnt("max_reach"), fired=fired, whole=whole)
    for kk, v in fired.items():
        assert v <= whole[kk], f"[D4] window {kk} {v} > whole-series {whole[kk]}"
    for kk, wk in (("syn_made", "syn_made"), ("syn_ratified", "syn_confirmed"),
                   ("syn_dropped", "syn_dropped"), ("extended", "extended"),
                   ("extended_pts", "extended_pts"), ("max_reach_hit", "max_reach_hit")):
        assert row[kk] <= whole[wk], f"[D4] window {kk} {row[kk]} > whole-series {whole[wk]}"
    chart = dict(dates=[str(b.timestamp)[:10] for b in bars[st:st + WIN]],
                 open=[float(v) for v in op[st:st + WIN]],
                 high=[float(v) for v in hi[st:st + WIN]],
                 low=[float(v) for v in lo[st:st + WIN]],
                 close=[float(v) for v in cl[st:st + WIN]],
                 segments=segs_out)
    return row, chart, fwd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="draw and print the sample, run nothing")
    ap.add_argument("--n", type=int, default=N_DRAW)
    ap.add_argument("--score", action="store_true", help="print forward return by state")
    ap.add_argument("--compare", action="store_true",
                    help="run two variants on every name, side by side")
    ap.add_argument("--compare-with", choices=("extend", "envelope"), default="extend",
                    help="extend: CELL vs CELL_EXT.  envelope: CELL_EXT vs CELL_ENV (one change: "
                         "the estimator)")
    a = ap.parse_args()

    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    print(f"\n  panel loaded in {time.time() - t0:.0f}s: {len(panel.symbols)} names")
    draw, rej = draw_sample(panel, cleaned, UF, a.n)
    print(f"  eligible (name, start) pairs: {rej['eligible']:,}")
    print(f"    rejected -- too few bars {rej['rej_short']} names | under the floor "
          f"{rej['rej_floor']:,} windows | split-sized jump {rej['rej_split']:,} windows")
    print(f"\n  THE DRAW (seed {SEED}, {a.n} of {rej['eligible']:,} eligible pairs)")
    for s, st in draw:
        b = cleaned[s]
        print(f"    {s:<8s} bars {st:>5d}-{st + WIN - 1:<5d}  "
              f"{str(b[st].timestamp)[:10]} -> {str(b[st + WIN - 1].timestamp)[:10]}")
    if a.list:
        return 0

    if a.compare_with == "envelope":
        base_cell, base_label = CELL_EXT, "regression, with the walk (current best)"
        second_cell, second_label = CELL_ENV, "envelope: the most-respected edge"
    else:
        base_cell, base_label = CELL, "carry = 3, as before"
        second_cell, second_label = CELL_EXT, "carry is a test: keep what still fits"
    cmp_chart = (CMP_CHART if a.compare_with == "extend"
                 else CMP_CHART.with_name("d399_envelope_chart.json"))
    cmp_out = (CMP_OUT if a.compare_with == "extend"
               else CMP_OUT.with_name("d399_envelope_compare.json"))
    variants = [("frozen", base_cell)] + ([("extend", second_cell)] if a.compare else [])
    results = {v: [] for v, _c in variants}
    charts = {v: [] for v, _c in variants}
    fwd_all = {v: {} for v, _c in variants}
    t1 = time.time()
    for s, st in draw:
        bars = cleaned[s]
        for v, cell in variants:
            row, ch, fwd = run_one(bars, st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st), date0=ch["dates"][0], date1=ch["dates"][-1])
            results[v].append(row)
            charts[v].append(dict(symbol=s, start_bar=int(st), n=WIN, **ch))
            for hh, dd in fwd.items():
                for nm, vals in dd.items():
                    fwd_all[v].setdefault(hh, {}).setdefault(nm, []).extend(vals)

    if not a.compare:
        print(f"\n  {'name':<8s} {'window':<24s} {'on':>7s} {'segs':>5s} {'life':>5s} "
              f"{'thru body':>10s} {'inverted':>9s} {'syn':>5s} {'rat':>4s} {'drop':>5s}"
              f"   (window counts)")
        for r in results["frozen"]:
            print(f"    {r['symbol']:<8s} {r['date0']} -> {r['date1']}  "
                  f"{r['coverage']:>4d}/{r['side_bars']:<4d} {r['segments']:>5d} "
                  f"{(r['median_life'] or 0):>5.0f} {r['through_body']:>10d} {0:>9d} "
                  f"{r['syn_made']:>5d} {r['syn_ratified']:>4d} {r['syn_dropped']:>5d}")
    else:
        print(f"\n  LEFT: {base_label}   |   RIGHT: {second_label}   -- same draw")
        print(f"  {'name':<8s} {'segs':>11s} {'life':>11s} {'reach':>11s} {'max':>9s} "
              f"{'extended':>9s} {'pts':>5s} {'cap':>4s}   (window counts)")
        print(f"  {'':<8s} {'L    R':>11s} {'L    R':>11s} {'L    R':>11s} {'L    R':>9s}")
        for rf, re in zip(results["frozen"], results["extend"]):
            print(f"    {rf['symbol']:<8s} {rf['segments']:>4d} {re['segments']:>5d}  "
                  f"{(rf['median_life'] or 0):>4.0f} {(re['median_life'] or 0):>5.0f}  "
                  f"{(rf['median_reach'] or 0):>4.0f} {(re['median_reach'] or 0):>5.0f}  "
                  f"{(rf['max_reach'] or 0):>4d} {(re['max_reach'] or 0):>4d} "
                  f"{re['extended']:>8d} {re['extended_pts']:>5d} {re['max_reach_hit']:>4d}")
        # D4: the two BA windows are different windows and must carry different window counts
        for v, _c in variants:
            ba = [r for r in results[v] if r["symbol"] == "BA"]
            if len(ba) == 2:
                keys = ("segments", "syn_made", "extended", "extended_pts", "fired")
                assert any(ba[0][kk] != ba[1][kk] for kk in keys), (
                    f"[D4] the two BA windows report identical counts under {v}: whole-series "
                    f"numbers are leaking into a per-window table")
        # which name did it change most? by how far the anchors moved back
        deltas = [((re["median_reach"] or 0) - (rf["median_reach"] or 0), rf["symbol"], i)
                  for i, (rf, re) in enumerate(zip(results["frozen"], results["extend"]))]
        deltas.sort(reverse=True)
        print(f"\n  reach = bars from a segment's first pivot to where it is first drawn; the walk "
              f"moves it back")
        print(f"  most changed: " + ", ".join(f"{s} (+{d:.0f})" for d, s, _i in deltas[:3]))
        top = deltas[0][2]
        cmp_chart.parent.mkdir(parents=True, exist_ok=True)
        cmp_chart.write_text(json.dumps(dict(
            cell=base_cell, second=second_cell, seed=SEED, window=WIN,
            pick=charts["frozen"][top]["symbol"],
            variants=[dict(key="frozen", label=base_label, charts=charts["frozen"]),
                      dict(key="extend", label=second_label, charts=charts["extend"])])))
        cmp_out.write_text(json.dumps(dict(
            what=f"D399: {second_label} vs {base_label} on the new sample", seed=SEED,
            base=base_cell, second=second_cell,
            most_changed=[dict(symbol=s, reach_delta=d) for d, s, _i in deltas],
            frozen=results["frozen"], extend=results["extend"]), indent=1))
        print(f"  [P] {cmp_out.relative_to(REPO)} and {cmp_chart.relative_to(REPO)} written")

    for v, _c in variants:
        rows = results[v]
        cov = np.array([r["coverage"] / r["side_bars"] for r in rows], float)
        life = np.array([r["median_life"] or np.nan for r in rows], float)
        print(f"\n  ACROSS THE {len(rows)} NAMES ({v}): coverage median {100 * np.median(cov):.0f}% "
              f"({100 * cov.min():.0f}-{100 * cov.max():.0f}) | segment life median "
              f"{np.nanmedian(life):.0f} bars | [R] and [C] asserted on all")

    if a.score:
        for v, _c in variants:
            print(f"\n  FORWARD RETURN BY STATE ({v}) -- gross, close-to-close, bp")
            for hh in HORIZONS:
                for nm in ("UP", "DOWN"):
                    x = np.asarray(fwd_all[v].get(hh, {}).get(nm, []), float)
                    if x.size:
                        print(f"    h={hh:>2d} {nm:<5s} n={x.size:>5d} mean {1e4 * x.mean():>7.1f} "
                              f"median {1e4 * np.median(x):>7.1f}")

    if not a.compare:
        OUT.write_text(json.dumps(dict(
            what="D399: the chosen cell on names and dates it has never seen", seed=SEED,
            window=WIN, split_lr=SPLIT_LR, excluded=list(EXCLUDE), cell=CELL,
            rejections=rej, names=results["frozen"]), indent=1))
        CHART.parent.mkdir(parents=True, exist_ok=True)
        CHART.write_text(json.dumps(dict(cell=CELL, seed=SEED, window=WIN,
                                         charts=charts["frozen"])))
        print(f"\n  [P] {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} written "
              f"({time.time() - t1:.0f}s to run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
