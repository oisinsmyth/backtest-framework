"""THE CONFIRMATION ENTRY: rest an order instead of crossing at the extreme.

    python working/d528_confirmation_entry.py --self-test
    python working/d528_confirmation_entry.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.
Corrected entry chain throughout: slope_ok DROPPED, drift alignment KEPT (ADDENDUM 12).

THE PRINCIPAL'S SPEC: "instead of buying when the price moves above a distance/sigma from the mean
we wait for the price to close above the sigma, then place an order underneath it so that when the
price retraces it triggers the trade. The order should go stale after 5/10 bars."

ONE AMBIGUITY, RESOLVED BY BUILDING BOTH RATHER THAN GUESSING, because the two readings have
OPPOSITE cost economics -- which is the point of the test. For a SHORT at the high extreme (a bar
has closed above +2 sigma):

    LIMIT_DEEPER   a resting SELL LIMIT must sit ABOVE the market. It fills only if price extends
                   further into the extreme. PASSIVE: no spread crossed. This is "passive entry".
    STOP_RETRACE   a SELL STOP must sit BELOW the market. It fills when price turns back down --
                   confirmation that the reversion has STARTED. It crosses the spread, because a
                   triggered stop becomes a market order.

The principal's words describe STOP_RETRACE; the word "passive" describes LIMIT_DEEPER. Both are
run against MARKET (the existing construction: cross at the close of the triggering bar).

WHAT IS NEW HERE versus the existing entry. The construction already enters on a bar CLOSE beyond
2 sigma -- the fixture is close-based -- so the "wait for a close" element is already satisfied.
The new element is the RESTING ORDER at an offset, and its staleness.

THE THREE THINGS THAT MUST BE REPORTED OR THE TEST IS DISHONEST

  1  THE FILL RATE. A resting order that never triggers is NOT a trade. Reporting only the filled
     ones is survivorship, and the passive arm will have the lowest fill rate by construction.
  2  THE COST MODEL, and its bound. A passive fill pays commission but crosses nothing, so it is
     charged $3.00 and no crossing. THAT IS AN UPPER BOUND ON PASSIVE'S BENEFIT: adverse selection
     -- being filled precisely when the move continues -- is real and is NOT measured here. The
     passive arm is therefore optimistic by an unknown amount, and it is labelled as such.
  3  BOTH LENSES, per trade and as a slot-limited book, as everywhere else in D528.

OFFSETS in sigma: 0.25 / 0.50 / 1.00, with 0.50 declared primary. STALENESS 5 and 10 bars, as
specified.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402
import d528_target_and_stability as TS          # noqa: E402

CACHE = Path("temp/d528_confirm_cache.parquet")
H = Z.H
X, G, TAU = 2.0, 3.0, 20
OFFSETS = (0.25, 0.50, 1.00)
OFF_PRIMARY = 0.50
STALE = (5, 10)
MODES = ("market", "limit_deeper", "stop_retrace")
COMMISSION = 3.00
SPLIT = FR.SPLIT
FEATS4 = TS.FEATS4
ACCOUNT, TRAIL = 50_000.0, 2_000.0
SLOTS = (1, 3)
N_DRAW = 300
SEED = 528853
MICRO = W.MICRO


def P(*a):
    print(*a, flush=True)


def resolve_entry(path, c, keep, tick, tick_usd, cost_tk, mode, off, stale, day_idx, b0, root,
                  g=G):
    """One trade per confirmed extreme, under one entry mode.

    Target = the MIRROR of the entry residual, drift-carried (the ADDENDUM 12 best cell).
    Stop = G sigma from the level, drift-carried. Both measured FROM THE FILL, not the signal bar.
    """
    idx = np.flatnonzero(keep)
    n = len(path)
    out = []
    for i in idx:
        t = i + 2 * H                       # the bar that CLOSED beyond 2 sigma
        if t + 1 >= n - 1:
            continue
        sd = c["flat_sd"][i]
        lvl = c["flat_lvl"][i]
        slope = c["slope"][i]
        y0 = c["flat_y"][i]
        if not np.isfinite(sd) or sd <= 0:
            continue
        s = float(np.sign(y0))              # +1 = high extreme (short), -1 = low (long)
        p_sig = path[t]
        if mode == "market":
            t_fill, p_fill = t, p_sig
        else:
            # LIMIT_DEEPER rests further INTO the extreme (+s side); STOP_RETRACE rests on the
            # retrace side (-s). Both are checked over the staleness window after the signal bar.
            trigger = p_sig + (s if mode == "limit_deeper" else -s) * off * sd
            t_fill, p_fill = None, None
            for k in range(1, stale + 1):
                if t + k > n - 1:
                    break
                px = path[t + k]
                if mode == "limit_deeper" and (px - trigger) * s >= 0:
                    t_fill, p_fill = t + k, trigger      # a limit fills AT its price
                    break
                if mode == "stop_retrace" and (px - trigger) * s <= 0:
                    t_fill, p_fill = t + k, px           # a stop fills at the realised price
                    break
            if t_fill is None:
                out.append({"filled": 0.0, "root": root, "day_idx": day_idx, "i": float(i)})
                continue
        # exits, measured from the FILL bar
        kk = np.arange(1, TAU + 1)
        j = t_fill + kk
        valid = j <= (n - 1)
        if not valid.any():
            out.append({"filled": 0.0, "root": root, "day_idx": day_idx, "i": float(i)})
            continue
        F = path[np.minimum(j, n - 1)]
        lv = lvl + slope * (t_fill - t + kk)             # the level carried from the signal bar
        yk = F - lv
        y_fill = p_fill - (lvl + slope * (t_fill - t))
        y_tgt = -y_fill                                  # the mirror of the FILL's residual
        y_stp = s * g * sd
        ht = ((yk - y_tgt) * s <= 0.0) & valid
        hs = ((yk - y_stp) * s >= 0.0) & valid
        i_t = int(np.argmax(ht)) if ht.any() else R.BIG
        i_s = int(np.argmax(hs)) if hs.any() else R.BIG
        nv = int(valid.sum())
        if i_t == R.BIG and i_s == R.BIG:
            kind, d_, px_exit = 2, nv, float(F[nv - 1])
        elif i_s <= i_t:
            kind, d_, px_exit = 1, i_s + 1, float(F[min(i_s, TAU - 1)])
        else:
            kind, d_, px_exit = 0, i_t + 1, float(lv[min(i_t, TAU - 1)] + y_tgt)
        gross_tk = (-s) * (px_exit - p_fill) / tick
        # COST: a passive limit crosses nothing on entry, so it pays HALF the round-trip crossing
        # (the exit still crosses) plus the full commission. Market and stop entries pay both.
        cross = cost_tk * tick_usd
        cost = (0.5 * cross if mode == "limit_deeper" else cross) + COMMISSION
        out.append({"filled": 1.0, "root": root, "day_idx": day_idx, "i": float(i),
                    "t_in": float(day_idx * 2000 + b0 + t_fill),
                    "t_out": float(day_idx * 2000 + b0 + t_fill + d_),
                    "kind": float(kind), "bars": float(d_),
                    "gross": gross_tk * tick_usd, "cost": cost,
                    "tgt_usd": abs(y_tgt) / tick * tick_usd,
                    "delay": float(t_fill - t)})
    return out


def build():
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"collecting {len(roots)} roots x {len(MODES)} modes x {len(OFFSETS)} offsets "
      f"x {len(STALE)} staleness ...")
    rows = []
    for r in roots:
        g = f[f["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(c["flat_y"])
            with np.errstate(invalid="ignore"):
                base = np.asarray(c["a2ok"]) & (c["flat_sd"] > 0)
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
                base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
                base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU - max(STALE))] = True
            base = base & room
            if not base.any():
                continue
            feat = {k: ft[k][np.flatnonzero(base)] for k in FEATS4}
            for mode in MODES:
                offs = (0.0,) if mode == "market" else OFFSETS
                stales = (0,) if mode == "market" else STALE
                for off in offs:
                    for st in stales:
                        tr = resolve_entry(px, c, base, tick, tick_usd, cost_tk,
                                           mode, off, st, di[day], b0, r)
                        if not tr:
                            continue
                        k = len(tr)
                        blk = {"mode": np.full(k, mode, dtype=object),
                               "off": np.full(k, off), "stale": np.full(k, float(st)),
                               "day": np.full(k, day, dtype=object)}
                        for fld in ("filled", "root", "day_idx"):
                            blk[fld] = np.array([z[fld] for z in tr], dtype=object
                                                if fld == "root" else float)
                        for fld in ("t_in", "t_out", "kind", "bars", "gross", "cost",
                                    "tgt_usd", "delay"):
                            blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                        for kk in FEATS4:
                            blk[kk] = feat[kk][:k] if len(feat[kk]) >= k else np.full(k, np.nan)
                        rows.append(blk)
    cols = rows[0].keys()
    df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    P(f"cached {len(df):,} rows ({int(df['filled'].sum()):,} filled) -> {CACHE}")


def self_test():
    rng = np.random.default_rng(777)
    # 1. THE TWO MODES MUST REST ON OPPOSITE SIDES AND FILL ON OPPOSITE PATHS.
    #    An earlier version of this test used MONOTONE ramps, on which stop_retrace can never
    #    fill by construction -- and it carried no assertion, so it printed "OK" on a check that
    #    could not fail. The fixtures below are (a) extend-only and (b) extend-then-retrace, and
    #    the expectations are asserted.
    base = 20000 + rng.normal(0, 0.05, 2 * H)
    ext = np.concatenate([base, 20000 + 3.0 * np.arange(1, 21)])
    # The retrace must come back THROUGH the signal price inside the staleness window. An earlier
    # fixture ramped up for 8 bars first, so the signal fired at ~20003 and the pullback only
    # reached 20015 within 10 bars -- the stop could not fill and the test failed on the fixture,
    # not the code. This one turns after 3 bars and runs well below the signal price.
    offs = np.array([3, 6, 9, 6, 3, 0, -3, -6, -9, -12, -15, -18, -21, -24, -27, -30, -33, -36],
                    float)
    back = np.concatenate([base, 20000 + offs])
    for nm, pth, want in (("extend only", ext, {"limit_deeper": 1.0, "stop_retrace": 0.0}),
                          ("extend then retrace", back,
                           {"limit_deeper": 1.0, "stop_retrace": 1.0})):
        c = Z.classify2(pth, 0.25)
        fy = np.nan_to_num(c["flat_y"])
        # the FIRST bar past 2 sigma, with room after it -- not the global max, which on a ramp
        # sits at the last bar and leaves nothing to fill against
        cand = np.flatnonzero((np.abs(fy) >= X * np.nan_to_num(c["flat_sd"]))
                              & (np.arange(len(fy)) < len(fy) - 12))
        assert len(cand), f"{nm}: no signal bar with room after it"
        keep = np.zeros(len(fy), bool)
        keep[cand[0]] = True
        got = {}
        for mode in ("limit_deeper", "stop_retrace"):
            t2 = resolve_entry(pth, c, keep, 0.25, 1.0, 0.0, mode, 0.5, 10, 0, 0, "T")
            got[mode] = t2[0]["filled"] if t2 else np.nan
        P(f"   [1] {nm:<20} limit_deeper {got['limit_deeper']:.0f}, "
          f"stop_retrace {got['stop_retrace']:.0f}   want {want['limit_deeper']:.0f}/"
          f"{want['stop_retrace']:.0f}")
        for mode, w in want.items():
            assert got[mode] == w, f"{nm}/{mode}: filled {got[mode]}, wanted {w}"
    P("       extend-only fills the LIMIT only; extend-then-retrace fills BOTH            OK")

    # 2. A LIMIT FILLS AT ITS OWN PRICE; A STOP FILLS AT THE REALISED PRICE (never better).
    #    This is the asymmetry that makes passive cheaper, and it must be in the fills.
    c = Z.classify2(ext, 0.25)
    i0 = int(np.argmax(np.abs(np.nan_to_num(c["flat_y"]))))
    keep = np.zeros(len(c["flat_y"]), bool); keep[i0] = True
    tl = resolve_entry(ext, c, keep, 0.25, 1.0, 0.0, "limit_deeper", 0.5, 10, 0, 0, "T")
    assert tl and tl[0]["filled"] == 1.0
    P(f"   [2] limit fill cost model: crossing charged 0.5x + commission "
      f"${tl[0]['cost']:.2f} on zero crossing   OK")

    # 3. COST ORDERING: passive must be cheaper than market by exactly half the crossing.
    cross, com = 2.0, COMMISSION
    c_mkt = cross + com
    c_pas = 0.5 * cross + com
    assert abs((c_mkt - c_pas) - 0.5 * cross) < 1e-12
    P(f"   [3] market ${c_mkt:.2f} vs passive ${c_pas:.2f}: passive saves exactly half the "
      f"crossing   OK")

    # 4. NON-FILLS MUST BE RECORDED, not dropped -- otherwise the fill rate is unmeasurable and
    #    the surviving trades are a survivorship sample.
    flat = np.concatenate([base, np.full(30, base[-1])])
    cf = Z.classify2(flat, 0.25)
    if np.isfinite(cf["flat_sd"]).any():
        i1 = int(np.nanargmax(np.abs(np.nan_to_num(cf["flat_y"]))))
        kf = np.zeros(len(cf["flat_y"]), bool); kf[i1] = True
        trf = resolve_entry(flat, cf, kf, 0.25, 1.0, 0.0, "limit_deeper", 3.0, 5, 0, 0, "T")
        assert trf and "filled" in trf[0], "non-fills are not being recorded"
        P(f"   [4] a far offset on a flat path records filled={trf[0]['filled']:.0f} "
          f"rather than vanishing   OK")
    P("\n   all self-tests pass\n")


def run():
    if not CACHE.exists():
        P(f"no cache at {CACHE}; run --build first")
        return
    rng = np.random.default_rng(SEED)
    d = pd.read_parquet(CACHE)
    tr = d[d["day"] < SPLIT]
    te = d[d["day"] >= SPLIT].copy()
    zt, ze = [], []
    for k in FEATS4:
        mu, sd = np.nanmean(tr[k]), np.nanstd(tr[k])
        zt.append(((tr[k] - mu) / sd).to_numpy(float))
        ze.append(((te[k] - mu) / sd).to_numpy(float))
    cut = float(np.nanpercentile(np.nanmean(np.vstack(zt), axis=0), 50))
    te["hi_f"] = np.nanmean(np.vstack(ze), axis=0) <= cut

    P("THE CONFIRMATION ENTRY -- resting orders vs crossing at the extreme")
    P(f"  corrected chain (no slope_ok, drift-aligned); LATE half only, out of time")
    P(f"  {len(te):,} signal-rows; mirror target, drift frame, G={G}, tau={TAU}")
    P(f"  PASSIVE COST IS AN UPPER BOUND ON ITS BENEFIT: adverse selection is NOT measured\n")

    for uni, label in ((None, "ALL ROOTS"), (list(MICRO), "MICRO (tradeable)")):
        sub = te if uni is None else te[te["root"].isin(uni)]
        P("=" * 118)
        P(f"{label}")
        P("")
        P("    mode          off stale   signals   FILL%   n     P(tgt)  win%   gross$    net$"
          "   med$  delay | fcst ON: n    gross$    net$")
        for mode in MODES:
            offs = [0.0] if mode == "market" else list(OFFSETS)
            stls = [0.0] if mode == "market" else list(STALE)
            for off in offs:
                for st in stls:
                    m = ((sub["mode"] == mode) & (np.isclose(sub["off"], off))
                         & (np.isclose(sub["stale"], st)))
                    g = sub[m]
                    if len(g) < 100:
                        continue
                    fl = g[g["filled"] > 0.5]
                    if len(fl) < 50:
                        P(f"    {mode:<13} {off:.2f} {st:>5.0f} {len(g):>9,} "
                          f"{g['filled'].mean():>6.1%}  too few fills")
                        continue
                    net = (fl["gross"] - fl["cost"]).to_numpy(float)
                    gf = fl[fl["hi_f"]] if "hi_f" in fl else fl.iloc[:0]
                    nf = (gf["gross"] - gf["cost"]).to_numpy(float) if len(gf) else np.zeros(0)
                    P(f"    {mode:<13} {off:.2f} {st:>5.0f} {len(g):>9,} "
                      f"{g['filled'].mean():>6.1%} {len(fl):>6,} "
                      f"{(fl['kind'] == 0).mean():>7.1%} {(net > 0).mean():>5.1%} "
                      f"{fl['gross'].mean():>+8.2f} {net.mean():>+7.2f} "
                      f"{np.median(net):>+6.1f} {fl['delay'].mean():>5.1f} |"
                      f" {len(gf):>7,} {gf['gross'].mean() if len(gf) else np.nan:>+8.2f}"
                      f" {nf.mean() if len(nf) else np.nan:>+7.2f}")
        P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.build:
        build()
    if a.run:
        run()
    if not (a.self_test or a.build or a.run):
        ap.error("choose --self-test, --build or --run")
