"""D471 -- the two things D469 left unmeasured: the spread where the moves are, and whether
path efficiency is a usable conditioner at all.

    uv run python scripts/d471_spread_and_path_efficiency.py --self-test
    uv run python scripts/d471_spread_and_path_efficiency.py --measure [--json]

**A MEASUREMENT, NOT A STUDY.** No signal, no entry rule, no edge, no Sharpe of any
construction. Nothing opened, closed or admitted (R15).

WHY
---
[D469](../docs/decisions/D469-RESULT-the-scalping-re-cost-the-spread-is-not-what-kills-it-a-fixed-commission-against-a-tenth-sized-tick-is.md)
put the MES breakeven accuracy at a 15-minute hold at **55.0%** by trading only the top
quintile of trailing volatility -- and flagged its own weakness in writing: *"the top
volatility quintile is exactly where fills are worst ... the conditioned rows are the most
optimistic cells in the table, not the safest."* D465's 97.6%-at-one-tick is **unconditional**.
So the first job here is to pay the spread that is actually quoted **in the bucket being
traded**, at **both** ends of the window, and recompute the bar.

The second job is the principal's question: **path efficiency.** For a window, efficiency is

    eff = |net displacement| / (total path length travelled)

in [0, 1]: 1 is a straight line, 0 is a round trip back to the start. It matters twice over.
**It separates a big move you can hold from a big move that shakes you out first**, which is
exactly the axis raw volatility cannot see -- high vol with low efficiency is chop.

**STAGE 0 COMES FIRST AND CAN KILL IT.** A conditioner is only usable if it **forecasts
itself**: the efficiency of the *next* window has to be predictable from the *previous* one.
That premise is measured here before anything is conditioned on it, and if the correlation is
~0 then path efficiency is a description of the past and not a signal, however good the story
is. Volatility passed this test in D469 at only rho = 0.232.

**RESOLUTION WARNING, and it is not a detail.** Path length is sampling-dependent -- for a
diffusion it diverges as the grid gets finer, so an efficiency NUMBER means nothing without
its grid. Everything here is on the same one-second grid, and only the RANKING across buckets
and the persistence correlation are claimed.

METHOD
------
**Non-overlapping** windows, unlike D469's overlapping pairs. Overlapping windows share
observations, so their statistics are correlated and an SE computed from them is a fiction.
Consecutive h-second blocks are independent, they give honest SEs, and they match the trading
model D469 priced (about 19 windows a day at 15 minutes).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
TICKS = REPO / "temp" / "d465_es_ticks_v2.npz"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d471_spread_and_path_efficiency.json"

PX_SCALE = 1e-9
TICK_PTS = 0.25
INT64_SENTINEL = 9223372036854775807      # DBN's absent-quote marker (D465's 875-tick bug)
COMMISSION_RT_MES = 3.00                  # D466's declared cost line
TICK_USD_MES = 1.25
HORIZONS = (300, 900)
NQ = 5                                    # quintiles


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- primitives

def path_efficiency(px: np.ndarray) -> float:
    """|net move| / total path length, in [0, 1]. 1 = straight line, 0 = round trip."""
    if len(px) < 2:
        return float("nan")
    length = float(np.abs(np.diff(px)).sum())
    if length <= 0:
        return float("nan")
    return abs(float(px[-1] - px[0])) / length


def blocks_of(sec: np.ndarray, h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Non-overlapping h-second blocks. Returns (block_id, start_idx, end_idx inclusive)."""
    bid = (sec - sec[0]) // h
    uniq, starts = np.unique(bid, return_index=True)
    ends = np.append(starts[1:], len(sec)) - 1
    return uniq, starts, ends


def breakeven_accuracy(cost_ticks: np.ndarray | float,
                       mean_abs_move_ticks: np.ndarray | float):
    """p to net zero on a +/-|M| outcome paying cost: p = (1 + cost/E|M|)/2."""
    return (1.0 + np.asarray(cost_ticks) / np.asarray(mean_abs_move_ticks)) / 2.0


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:58} {detail}")
        if not cond:
            fails.append(label)

    # --- path efficiency, on paths whose answer is known by hand
    chk("eff of a straight line = 1",
        abs(path_efficiency(np.array([1., 2., 3., 4.])) - 1.0) < 1e-12)
    chk("eff of an exact round trip = 0",
        abs(path_efficiency(np.array([1., 5., 1.])) - 0.0) < 1e-12)
    # 0 -> 3 -> 1 is a NET of 1 over a PATH of 3+2 = 5, so 0.2. I first wrote 1/3 here and
    # the check failed -- the arithmetic was wrong, not the function.
    chk("eff of out-and-two-thirds-back = 0.2",
        abs(path_efficiency(np.array([0., 3., 1.])) - 0.2) < 1e-12)
    chk("eff is sign-blind (a straight fall is also 1)",
        abs(path_efficiency(np.array([4., 3., 2., 1.])) - 1.0) < 1e-12)
    for p in (np.array([0., 1., -2., 5., 3.]), np.array([0., -1., -1., 2.])):
        e = path_efficiency(p)
        chk(f"eff in [0,1] for {list(p.astype(int))}", 0.0 <= e <= 1.0 + 1e-12, f"{e:.4f}")
    # RESOLUTION: the same underlying move sampled finer has a LONGER path, so lower
    # efficiency. This is why only rankings on one fixed grid are claimed.
    coarse = path_efficiency(np.array([0., 10.]))
    fine = path_efficiency(np.array([0., 3., 1., 6., 4., 10.]))
    chk("eff FALLS under finer sampling (resolution-dependent)", fine < coarse,
        f"coarse {coarse:.3f} vs fine {fine:.3f}")

    # --- the block machinery, against a hand-built case
    sec = np.array([0, 1, 2, 10, 11, 20, 21, 22], dtype=np.int64)
    uniq, st, en = blocks_of(sec, 10)
    chk("blocks: 3 blocks of width 10", len(uniq) == 3, f"{len(uniq)}")
    chk("blocks: starts", list(st) == [0, 3, 5], f"{list(st)}")
    chk("blocks: ends are INCLUSIVE and tile with no gap",
        list(en) == [2, 4, 7], f"{list(en)}")
    px = np.array([5., 7., 6., 1., 9., 2., 2., 2.])
    chk("reduceat block max matches a loop",
        list(np.maximum.reduceat(px, st)) == [7., 9., 2.])
    chk("reduceat block min matches a loop",
        list(np.minimum.reduceat(px, st)) == [5., 1., 2.])
    # path length by cumulative sum must equal the direct sum, per block
    cum = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(px)))])
    for k in range(len(st)):
        direct = float(np.abs(np.diff(px[st[k]:en[k] + 1])).sum())
        viacum = float(cum[en[k]] - cum[st[k]])
        chk(f"path length by cumsum == direct, block {k}", abs(direct - viacum) < 1e-12,
            f"{direct:.2f}")

    # --- adverse excursion from ENTRY (a fixed stop keys on this, not on a running peak)
    up = np.array([100., 101., 102., 103.])
    chk("a monotone rise has ZERO adverse excursion for a long",
        abs(float(up[0] - up.min())) < 1e-12)
    dip = np.array([100., 97., 99., 104.])
    chk("a long that dips 3 before paying 4 has adverse 3",
        abs(float(dip[0] - dip.min()) - 3.0) < 1e-12)
    chk("the SHORT side of the same path has adverse 4",
        abs(float(dip.max() - dip[0]) - 4.0) < 1e-12)

    # --- the sentinel filter, which is the bug that made D465 read 875-tick spreads
    bid = np.array([100, INT64_SENTINEL, 102, 0], dtype=np.int64)
    ask = np.array([101, 103, INT64_SENTINEL, 5], dtype=np.int64)
    ok = ((bid != INT64_SENTINEL) & (ask != INT64_SENTINEL) & (bid > 0) & (ask > 0)
          & (ask >= bid))
    chk("sentinel filter admits only the clean quote", list(ok) == [True, False, False, False],
        f"{list(ok)}")

    # --- the cost identity, and that a wider spread RAISES the bar
    lo = float(breakeven_accuracy(3.41, 22.83))
    hi = float(breakeven_accuracy(4.41, 22.83))
    chk("a wider spread raises breakeven accuracy", hi > lo,
        f"{lo:.3%} -> {hi:.3%} for one extra tick of cost")
    chk("a bigger move lowers it", breakeven_accuracy(3.41, 34.4) < lo,
        f"{float(breakeven_accuracy(3.41, 34.4)):.3%} at 34.4 ticks")
    chk("zero cost needs exactly 50%", abs(float(breakeven_accuracy(0.0, 10.0)) - .5) < 1e-15)

    # --- THE RANDOM-WALK BENCHMARK FOR EFFICIENCY, which is what makes the measured
    # numbers interpretable. For a driftless walk of n steps, E|net| = sigma*sqrt(2n/pi)
    # and E[path] = n*sigma*sqrt(2/pi), so efficiency -> 1/sqrt(n) EXACTLY. Without this
    # line "efficiency is 0.033" is an uninterpretable small number.
    rng = np.random.default_rng(4711)
    for n in (100, 900):
        effs = [path_efficiency(np.concatenate([[0.0], np.cumsum(rng.standard_normal(n))]))
                for _ in range(4000)]
        got, want = float(np.mean(effs)), 1.0 / np.sqrt(n)
        chk(f"simulated walk efficiency ~ 1/sqrt(n) at n={n}",
            abs(got - want) / want < 0.06, f"{got:.4f} vs 1/sqrt(n) {want:.4f}")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


# ---------------------------------------------------------------- measurement

def do_measure(as_json: bool) -> int:
    if not TICKS.exists():
        raise SystemExit(f"missing {TICKS}; run d465 --extract")
    z = np.load(TICKS)
    if "iid" not in z:
        raise GateError("[INPUT] cache carries no instrument_id -- this is the v1 cache "
                        "that pooled expiries; re-run d465 --extract")
    ts, iid = z["ts"], z["iid"]
    px = z["px"].astype(np.float64) * PX_SCALE
    bid, ask = z["bid"], z["ask"]

    # quote filter FIRST, and it is the same one D465 needed after reading 875-tick spreads
    good = ((px > 0) & (bid != INT64_SENTINEL) & (ask != INT64_SENTINEL)
            & (bid > 0) & (ask > 0) & (ask >= bid))
    dropped = int((~good).sum())
    ts, px, iid = ts[good], px[good], iid[good]
    half_tk = ((ask[good] - bid[good]).astype(np.float64) * PX_SCALE) / TICK_PTS / 2.0
    P(f"ES trades {len(px):,}  ({dropped:,} dropped on the quote filter)")

    sec = (ts // 1_000_000_000).astype(np.int64)
    # one expiry per second, or a cross-record measurement is reading the calendar basis
    _, f_ = np.unique(sec, return_index=True)
    i64 = iid.astype(np.int64)
    if int((np.maximum.reduceat(i64, f_) != np.minimum.reduceat(i64, f_)).sum()):
        raise GateError("[INPUT] a second carries two expiries")

    # collapse to the one-second grid: LAST trade in each second
    uniq_sec, first = np.unique(sec, return_index=True)
    last = np.append(first[1:], len(px)) - 1
    g_px, g_id, g_half = px[last], i64[last], half_tk[last]
    cum = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(g_px)))])
    P(f"one-second grid: {len(uniq_sec):,} seconds\n")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D471: the spread PAID in the bucket being traded, and whether path "
                      "efficiency forecasts itself well enough to be a conditioner. A "
                      "measurement -- no signal, no edge, no Sharpe, nothing admitted.",
           "source": "D465 v2 windowed ES front-month ticks, 2025-09-11..2026-09-10",
           "grid": "one-second last trade; non-overlapping windows",
           "resolution_warning": "path length and therefore efficiency are grid-dependent; "
                                 "only rankings on this one-second grid and the persistence "
                                 "correlation are claimed",
           "quote_records_dropped": dropped,
           "by_horizon": {}}

    for h in HORIZONS:
        lab = f"{h//60}m"
        uniq, st, en = blocks_of(uniq_sec, h)
        span = uniq_sec[en] - uniq_sec[st]
        npts = en - st + 1
        # A BLOCK MUST ACTUALLY SPAN ITS OWN WIDTH. The first run allowed span >= 0.5h and
        # the blocks averaged 534 seconds of trading against a 900-second width -- so it
        # measured ~9-minute moves and labelled them 15-minute ones, understating E|M| by
        # a third and inflating every breakeven. The tell was arithmetic that was there to
        # be done: 23,224 blocks x 900 s = 20.9M seconds against a 12.4M-second grid.
        valid = ((span >= 0.95 * h) & (npts >= 30)
                 & (np.maximum.reduceat(g_id, st) == np.minimum.reduceat(g_id, st)))
        # and its immediate predecessor must exist and be valid, to condition causally
        prev_ok = np.zeros(len(uniq), dtype=bool)
        has_prev = np.concatenate([[False], uniq[1:] == uniq[:-1] + 1])
        prev_ok[1:] = valid[:-1]
        use = valid & has_prev & prev_ok
        k = np.flatnonzero(use)
        if len(k) < 2000:
            P(f"{lab}: only {len(k)} usable blocks, skipped")
            continue

        entry, exitp = g_px[st[k]], g_px[en[k]]
        fwd_signed = (exitp - entry) / TICK_PTS
        fwd_abs = np.abs(fwd_signed)
        fwd_len = (cum[en[k]] - cum[st[k]]) / TICK_PTS
        fwd_eff = np.where(fwd_len > 0, fwd_abs / np.maximum(fwd_len, 1e-12), np.nan)
        # the PREVIOUS block, known in full at entry
        kp = k - 1
        prv_abs = np.abs(g_px[en[kp]] - g_px[st[kp]]) / TICK_PTS
        prv_len = (cum[en[kp]] - cum[st[kp]]) / TICK_PTS
        prv_eff = np.where(prv_len > 0, prv_abs / np.maximum(prv_len, 1e-12), np.nan)
        # adverse excursion from ENTRY, both sides
        blk_max = np.maximum.reduceat(g_px, st)[k]
        blk_min = np.minimum.reduceat(g_px, st)[k]
        adv_long = (entry - blk_min) / TICK_PTS
        adv_short = (blk_max - entry) / TICK_PTS
        # THE ADVERSE EXCURSION ON THE SIDE THAT WON. min(long, short) takes the gentler
        # side whichever way price went, which is not a trade anyone can place; the
        # question is "having called the direction right, how much pain came first".
        adv_correct = np.where(fwd_signed > 0, adv_long, adv_short)
        # the spread actually quoted at BOTH ends of the window
        cost_spread = g_half[st[k]] + g_half[en[k]]
        comm_tk = COMMISSION_RT_MES / TICK_USD_MES

        fin = np.isfinite(prv_eff) & np.isfinite(fwd_eff)

        # SESSION, because the overnight weighting is the whole gap with D469. D469 required
        # BOTH the entry second and the exit second to carry a trade, which silently drops
        # quiet overnight windows and activity-weights its sample; these blocks tile every
        # calendar block equally, dead Asian-hours blocks included. Neither is wrong -- they
        # answer different questions -- so the confound is removed by splitting rather than
        # by arguing about which mean is "the" mean.
        import pandas as pd
        et = pd.DatetimeIndex(pd.to_datetime(uniq_sec[st[k]], unit="s", utc=True)) \
            .tz_convert("America/New_York")
        et_min = et.hour.values * 60 + et.minute.values
        rth = (et_min >= 9 * 60 + 30) & (et_min < 16 * 60)
        P(f"=== {lab} holds, {len(k):,} non-overlapping windows "
          f"({fin.sum():,} with a finite efficiency pair; {int(rth.sum()):,} RTH) ===")

        # ---- STAGE 0: does either conditioner forecast ITSELF?
        r_vol = float(np.corrcoef(prv_abs[fin], fwd_abs[fin])[0, 1])
        r_eff = float(np.corrcoef(prv_eff[fin], fwd_eff[fin])[0, 1])
        r_cross = float(np.corrcoef(prv_eff[fin], fwd_abs[fin])[0, 1])
        n_f = int(fin.sum())
        se = 1.0 / np.sqrt(n_f)
        P(f"  STAGE 0, persistence on independent windows (SE ~ {se:.4f}):")
        P(f"    trailing |move|  -> forward |move|  rho {r_vol:+.3f}  "
          f"({abs(r_vol)/se:>5.1f} SE)")
        P(f"    trailing eff     -> forward eff     rho {r_eff:+.3f}  "
          f"({abs(r_eff)/se:>5.1f} SE)")
        P(f"    trailing eff     -> forward |move|  rho {r_cross:+.3f}  "
          f"({abs(r_cross)/se:>5.1f} SE)")

        # ---- the spread where the moves are, by trailing-volatility quintile
        def quintile_table(key: np.ndarray, keyname: str, mask: np.ndarray) -> list:
            kk = key[mask]
            edges = np.quantile(kk, np.linspace(0, 1, NQ + 1))
            out = []
            P(f"\n  by {keyname} quintile -- and the bar RE-COSTED on the spread each "
              f"bucket actually quotes:")
            P(f"  {'q':>3}{'n':>8}{'trail':>8}{'fwd|M|':>8}{'fwd eff':>9}{'rw eff':>8}"
              f"{'ratio':>7}{'spr(tk)':>9}{'cost':>7}{'p_be':>8}{'D469 p_be':>11}"
              f"{'adv/|M|':>9}")
            for q in range(NQ):
                m = mask.copy()
                sel = ((kk >= edges[q]) & (kk <= edges[q + 1])) if q == NQ - 1 else \
                      ((kk >= edges[q]) & (kk < edges[q + 1]))
                m[np.flatnonzero(mask)[~sel]] = False
                if m.sum() < 200:
                    continue
                e_abs = float(fwd_abs[m].mean())
                spr = float(cost_spread[m].mean())
                cost_true = spr + comm_tk
                cost_d469 = 1.009 + comm_tk          # D469's UNCONDITIONAL crossing
                p_true = float(breakeven_accuracy(cost_true, e_abs))
                p_d469 = float(breakeven_accuracy(cost_d469, e_abs))
                adv = float(adv_correct[m].mean())
                out.append({"quintile": q + 1, "n": int(m.sum()),
                            "trailing_mean": float(key[m].mean()),
                            "fwd_mean_abs_ticks": e_abs,
                            "fwd_mean_efficiency": float(np.nanmean(fwd_eff[m])),
                            "spread_both_ends_ticks": spr,
                            "cost_ticks_true": cost_true,
                            "breakeven_accuracy_true": p_true,
                            "breakeven_accuracy_at_d469_unconditional_spread": p_d469,
                            "mean_adverse_over_move": adv / e_abs})
                # THE BENCHMARK THAT MAKES AN EFFICIENCY NUMBER MEAN ANYTHING. A driftless
                # walk of n steps has efficiency 1/sqrt(n) exactly, so the ratio below is
                # the only scale-free reading: 1.00 means indistinguishable from a coin.
                steps = float((en[k][m] - st[k][m]).mean())
                rw = 1.0 / np.sqrt(max(steps, 1.0))
                eff_m = float(np.nanmean(fwd_eff[m]))
                out[-1]["random_walk_efficiency_1_over_sqrt_steps"] = float(rw)
                out[-1]["efficiency_over_random_walk"] = eff_m / rw
                P(f"  {q+1:>3}{m.sum():>8,}{key[m].mean():>8.1f}{e_abs:>8.1f}"
                  f"{eff_m:>9.3f}{rw:>8.3f}{eff_m/rw:>7.2f}{spr:>9.3f}{cost_true:>7.2f}"
                  f"{p_true:>8.1%}{p_d469:>11.1%}{adv/e_abs:>9.2f}")
            return out

        t_vol = quintile_table(prv_abs, "TRAILING |move|, ALL HOURS", fin.copy())
        t_vol_rth = quintile_table(prv_abs, "TRAILING |move|, RTH ONLY (09:30-16:00 ET)",
                                   fin & rth)
        t_eff = quintile_table(prv_eff, "TRAILING efficiency, ALL HOURS", fin.copy())

        # ---- the 2D cross: does efficiency add anything ON TOP of volatility?
        P(f"\n  top-volatility windows SPLIT by trailing efficiency "
          f"(does eff add to vol?):")
        hi_vol = fin & (prv_abs >= np.quantile(prv_abs[fin], 0.8))
        cross = []
        med_eff = float(np.median(prv_eff[hi_vol]))
        for tag, m in (("eff BELOW median", hi_vol & (prv_eff < med_eff)),
                       ("eff ABOVE median", hi_vol & (prv_eff >= med_eff))):
            if m.sum() < 200:
                continue
            e_abs = float(fwd_abs[m].mean())
            spr = float(cost_spread[m].mean())
            p_true = float(breakeven_accuracy(spr + comm_tk, e_abs))
            adv = float(adv_correct[m].mean())
            cross.append({"cell": tag, "n": int(m.sum()), "fwd_mean_abs_ticks": e_abs,
                          "fwd_mean_efficiency": float(np.nanmean(fwd_eff[m])),
                          "spread_both_ends_ticks": spr,
                          "breakeven_accuracy_true": p_true,
                          "mean_adverse_over_move": adv / e_abs})
            P(f"    {tag:20} n {m.sum():>7,}  fwd|M| {e_abs:>6.1f}  "
              f"fwd eff {np.nanmean(fwd_eff[m]):.3f}  spr {spr:.3f}  "
              f"p_be {p_true:>6.1%}  adv/|M| {adv/e_abs:.2f}")

        res["by_horizon"][h] = {
            "n_windows": int(len(k)), "n_finite_pairs": n_f,
            "persistence": {"trailing_abs_to_forward_abs": r_vol,
                            "trailing_eff_to_forward_eff": r_eff,
                            "trailing_eff_to_forward_abs": r_cross,
                            "se": float(se)},
            "commission_ticks": comm_tk,
            "by_trailing_volatility": t_vol,
            "by_trailing_volatility_RTH": t_vol_rth,
            "n_rth_windows": int(rth.sum()),
            "by_trailing_efficiency": t_eff,
            "top_vol_split_by_efficiency": cross,
        }
        P("")

    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"wrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.measure:
        return do_measure(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
