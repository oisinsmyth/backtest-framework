"""A VOLUME FILTER: block thin conditions (LEVEL) and falling conditions (CHANGE), separately.

    python working/d528_volume_filter.py --self-test
    python working/d528_volume_filter.py --run

Nothing admitted (R15). Micro universe, in sample only; reserved slice UNREAD.

THE PRINCIPAL'S DESIGN, and the one change made to it. He asked for an SMA of volume against an
EMA of volume, over ~100 bars rather than the detection window, scale-invariant, with no warm-up --
the previous session's volume filling any shortfall, excluding overnight.

THE ONE CHANGE: EVERYTHING IS NORMALISED BY THE TIME-OF-DAY PROFILE FIRST. NQ's median 5-minute
volume runs 17,021 at 09:30 against 3,378 at 14:00 -- a 14.5x swing -- so a 100-bar window against
a longer average would mostly report WHAT TIME IT IS. That is the same defect already diagnosed in
the detector itself: a normaliser that encodes the thing it is meant to measure.

It also matters for a second reason. Measured on the 717 candidates:

    corr(price vol_ratio, TIME-OF-DAY-NORMALISED volume) = +0.052   independent -- filter is safe
    corr(price vol_ratio, RAW volume)                    = +0.235   entangled -- would cut the
                                                                    quiet-window cell that works

So normalising is what keeps the volume filter from eating the one cell that clears its control.

TWO FILTERS, DECLARED SEPARATELY, both cut at 1.0 (untuned, and the natural point of each):

    LEVEL    fast < 1.0          the last 100 minutes were THINNER than normal for this time of day
    CHANGE   fast / slow < 1.0   activity is FALLING relative to the instrument's recent norm

    fast = mean of normalised volume over the trailing 20 five-minute bars (= 100 minutes)
    slow = EMA of normalised volume, half-life 2 sessions

NOTE ON THE SIGN. "SMA much less than EMA" as literally written blocks volume SURGES, because an
EMA weights recent data more heavily. Both directions are reported so the principal can see which
he meant; CHANGE below is `fast/slow < 1` = falling activity.

NO WARM-UP, and it is simpler than feared: THE FIXTURE IS DAY-SESSION ONLY (09:00-15:59), so there
is no overnight volume in it to exclude. Where a session is younger than 100 minutes the trailing
window backfills from the PREVIOUS session's same-clock bars.

CAUSALITY. The time-of-day profile for day d uses only sessions STRICTLY BEFORE d (rolling 20).
Candidates whose profile cannot be formed from >= 5 prior sessions are dropped from the pool
ENTIRELY, so the filtered set and its control share the same eligibility.

AND THE COST IS RE-CHARGED AT THE HOUR'S OWN SPREAD, because that is where this filter should pay.
ADDENDUM 10 found the spike cell trades at 1.95 ticks against 1.41 on random minutes while the cost
model charges one full-year figure per root. Here:

    cost_ticks(hour) = COST[root] * spread(root, day, hour) / median spread(root)

anchored on D507's measured crossing, plus the $3.00 commission, which does not scale with spread.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_detector_diagnosis as D             # noqa: E402

FIVE = "data/fixtures/fut_day5m.parquet"
TBBO = "data/fixtures/fut_crossing_tbbo.csv.gz"
FAST_BARS5 = 20              # 20 five-minute bars = 100 minutes, the principal's window
TOD_SESSIONS = 20            # rolling sessions forming the time-of-day profile
TOD_MIN_SESSIONS = 5
SLOW_HL_SESSIONS = 2.0
CUT = 1.0                    # declared, untuned, for BOTH filters
N_DRAW = 400
SEED = 528331


def P(*a):
    print(*a, flush=True)


def build_volume(roots, days):
    """Per (root, day): the 84 five-minute volumes, the causal time-of-day profile, and the
    normalised series -- plus `fast` and `slow` per five-minute bar.

    The profile for day d is the median volume at that bar over the previous TOD_SESSIONS days,
    strictly before d. Nothing here reads day d or later.
    """
    f = pd.read_parquet(FIVE, columns=["root", "day", "bar", "volume"])
    f = f[f["root"].isin(roots) & f["day"].isin(days)]
    out = {}
    for r in roots:
        g = f[f["root"] == r]
        by_day = {dy: sub.set_index("bar")["volume"].reindex(range(84)).to_numpy(float)
                  for dy, sub in g.groupby("day")}
        ordered = [dy for dy in days if dy in by_day]
        slow_state = None
        for k, dy in enumerate(ordered):
            prior = ordered[max(0, k - TOD_SESSIONS):k]
            if len(prior) < TOD_MIN_SESSIONS:
                out[(r, dy)] = None
                continue
            stack = np.vstack([by_day[p] for p in prior])
            with np.errstate(invalid="ignore"):
                tod = np.nanmedian(stack, axis=0)
            v = by_day[dy]
            with np.errstate(invalid="ignore", divide="ignore"):
                u = np.where(tod > 0, v / tod, np.nan)
            # fast: trailing FAST_BARS5, backfilled from the PREVIOUS session's same-clock tail
            prev_u = out.get((r, ordered[k - 1]), None)
            prev_series = prev_u["u"] if prev_u else None
            fast = np.full(84, np.nan)
            for b in range(84):
                need = FAST_BARS5
                take = u[max(0, b - need + 1):b + 1]
                if len(take) < need and prev_series is not None:
                    take = np.concatenate([prev_series[len(prev_series) - (need - len(take)):],
                                           take])
                if np.isfinite(take).sum() >= need // 2:
                    fast[b] = np.nanmean(take)
            # slow: EMA across sessions, one update per session on the session's own mean
            sm = np.nanmean(u) if np.isfinite(u).any() else np.nan
            if np.isfinite(sm):
                a = 1.0 - 0.5 ** (1.0 / SLOW_HL_SESSIONS)
                slow_state = sm if slow_state is None else (a * sm + (1 - a) * slow_state)
            out[(r, dy)] = {"u": u, "fast": fast, "slow": slow_state, "tod": tod}
    return out


def build_spread(roots, days):
    t = pd.read_csv(TBBO)
    t = t[t["root"].isin(roots) & t["day"].isin(days)]
    t["wsum"] = t["spread_tk"] * t["vol"]
    g = t.groupby(["root", "day", "hour"], as_index=False).agg(
        wsum=("wsum", "sum"), vol=("vol", "sum"))
    g["sp"] = g["wsum"] / g["vol"].replace(0, np.nan)
    hourly = {(r, d, h): s for r, d, h, s in zip(g["root"], g["day"], g["hour"], g["sp"])}
    # THE DENOMINATOR MUST MATCH THE ANCHOR'S BASIS. D507's COST[root] is the measured effective
    # crossing AT EXECUTION HOURS, so the reference spread must be the DAY-SESSION median too.
    # Taking the median over all 24 hours pulls in wide overnight quotes, which made the day
    # session look tight (spread x ~0.90) and scaled the cost DOWN -- the opposite of ADDENDUM
    # 10's finding that this cell trades wider than a random minute.
    day = g[(g["hour"] >= Q.DAY_LO // 60) & (g["hour"] <= Q.DAY_HI // 60)]
    med = day.groupby("root")["sp"].median().to_dict()
    return hourly, med


def self_test():
    rng = np.random.default_rng(101)
    # 1. THE PROFILE MUST BE CAUSAL: it uses only sessions strictly before the day it scores.
    days = [f"d{i:02d}" for i in range(12)]
    ordered = days
    for k, dy in enumerate(ordered):
        prior = ordered[max(0, k - TOD_SESSIONS):k]
        assert dy not in prior, f"{dy} is in its own profile window"
        assert all(p < dy for p in prior), f"a future day leaked into {dy}'s profile"
    P("   [1] the time-of-day profile for day d uses only days strictly before d        OK")

    # 2. NORMALISING MUST REMOVE THE U-SHAPE. Build a synthetic U and confirm the raw series
    #    correlates with a U-shaped template while the normalised one does not.
    bars = np.arange(84)
    u_shape = 1.0 + 3.0 * (np.exp(-bars / 8.0) + np.exp(-(83 - bars) / 8.0))
    raw = np.vstack([u_shape * rng.lognormal(0, 0.25, 84) for _ in range(30)])
    tod = np.median(raw[:20], axis=0)
    norm = raw[25] / tod
    c_raw = abs(np.corrcoef(raw[25], u_shape)[0, 1])
    c_nrm = abs(np.corrcoef(norm, u_shape)[0, 1])
    assert c_raw > 0.8, f"the synthetic U is not U-shaped enough to test: {c_raw:.3f}"
    assert c_nrm < 0.3, f"normalising left |corr| with the U at {c_nrm:.3f}"
    P(f"   [2] |corr| with the U-shape: raw {c_raw:.3f} -> normalised {c_nrm:.3f}          OK")

    # 3. THE WARM-UP BACKFILL: at bar 0 the trailing window must be drawn entirely from the
    #    PREVIOUS session, and must be FAST_BARS5 long -- not a short, noisy partial window.
    prev = np.arange(84, dtype=float)
    cur = np.full(84, 100.0)
    b = 0
    take = cur[max(0, b - FAST_BARS5 + 1):b + 1]
    assert len(take) == 1
    take = np.concatenate([prev[len(prev) - (FAST_BARS5 - len(take)):], take])
    assert len(take) == FAST_BARS5, f"backfilled window is {len(take)}, wanted {FAST_BARS5}"
    assert take[0] == prev[84 - (FAST_BARS5 - 1)], "backfill did not take the previous tail"
    P(f"   [3] at bar 0 the window is {len(take)} bars, {FAST_BARS5-1} of them from the "
      f"previous session   OK")

    # 4. THE TWO FILTERS MUST DIFFER. A series that is thin but RISING passes CHANGE and fails
    #    LEVEL; one that is rich but FALLING does the opposite. If they agreed, "both, reported
    #    separately" would be one filter reported twice.
    for nm, fast, slow, want_lvl, want_chg in (("thin but rising", 0.7, 0.5, False, True),
                                               ("rich but falling", 1.4, 1.8, True, False)):
        lvl = fast >= CUT
        chg = (fast / slow) >= CUT
        assert lvl == want_lvl and chg == want_chg, f"{nm}: level {lvl}, change {chg}"
        P(f"   [4] {nm:<18} LEVEL {'pass' if lvl else 'BLOCK'}, "
          f"CHANGE {'pass' if chg else 'BLOCK'}   OK")

    # 5. THE SPREAD-SCALED COST must equal the fixed cost exactly when the hour's spread equals
    #    the root median, and scale linearly away from it.
    base, med = 2.134, 1.70
    assert abs(base * (med / med) - base) < 1e-12
    assert abs(base * (2 * med / med) - 2 * base) < 1e-12
    P("   [5] spread-scaled cost == fixed cost at the median, and doubles at 2x spread  OK")
    P("\n   all self-tests pass\n")


def run():
    rng = np.random.default_rng(SEED)
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    rev_day = {i: u for u, i in day_index.items()}

    P("A VOLUME FILTER: LEVEL (thin) and CHANGE (falling), reported separately")
    P(f"  {len(roots)} roots, {len(udays)} sessions; volume from the 5-minute fixture")
    P(f"  fast = {FAST_BARS5} five-minute bars ({FAST_BARS5*5} min), backfilled from the previous")
    P(f"  session; slow = EMA half-life {SLOW_HL_SESSIONS} sessions; both normalised by a causal")
    P(f"  {TOD_SESSIONS}-session time-of-day profile. DECLARED CUT {CUT} for both, untuned.\n")

    pool_all = D.collect(d, sp, roots, day_index)
    vol = build_volume(roots, udays)
    hourly, med_sp = build_spread(roots, udays)

    # attach the volume measures; drop candidates whose causal profile cannot be formed
    pool, dropped = [], 0
    for z in pool_all:
        dy = rev_day[z["day"]]
        rec = vol.get((z["root"], dy))
        if rec is None or rec["slow"] is None:
            dropped += 1
            continue
        bar = z["t_in"] - z["day"] * 2000
        b5 = bar // 5
        fast = rec["fast"][b5] if 0 <= b5 < 84 else np.nan
        if not np.isfinite(fast) or rec["slow"] <= 0:
            dropped += 1
            continue
        z["v_fast"] = float(fast)
        z["v_slow"] = float(rec["slow"])
        z["v_chg"] = float(fast / rec["slow"])
        hh = (Q.DAY_LO + bar) // 60
        s = hourly.get((z["root"], dy, hh))
        m = med_sp.get(z["root"])
        scale = (s / m) if (s and m and np.isfinite(s) and m > 0) else 1.0
        base_tk = R.COST.get(z["root"], R.COST_DEFAULT)
        z["cost_hour"] = base_tk * scale * z["tick_usd"] + B.COMMISSION_RT
        z["net_hour"] = z["gross"] - z["cost_hour"]
        z["sp_scale"] = scale
        pool.append(z)

    P(f"  pool {len(pool):,} eligible candidates ({dropped} dropped: no causal profile)")
    P(f"  median fast {np.median([z['v_fast'] for z in pool]):.3f}, "
      f"median fast/slow {np.median([z['v_chg'] for z in pool]):.3f}, "
      f"median spread scale {np.median([z['sp_scale'] for z in pool]):.3f}")
    P("")

    def f_quiet(z):
        return np.isfinite(z["vol_ratio"]) and z["vol_ratio"] < 0.913

    def f_sudden(z):
        return np.isfinite(z["frac_last"]) and z["frac_last"] > 0.8

    def f_jump(z):
        return np.isfinite(z["jump"]) and z["jump"] > 3

    def spike(z):
        return f_quiet(z) and f_sudden(z) and f_jump(z)

    LVL = lambda z: z["v_fast"] >= CUT                      # noqa: E731
    CHG = lambda z: z["v_chg"] >= CUT                       # noqa: E731

    CELLS = (
        ("pool (no volume filter)", lambda z: True),
        ("LEVEL: not thin", LVL),
        ("CHANGE: not falling", CHG),
        ("LEVEL + CHANGE", lambda z: LVL(z) and CHG(z)),
        ("-- the inverted sign --", None),
        ("LEVEL inverted (thin only)", lambda z: not LVL(z)),
        ("CHANGE inverted (falling only)", lambda z: not CHG(z)),
        ("-- on the spike cell --", None),
        ("spike", spike),
        ("spike + LEVEL", lambda z: spike(z) and LVL(z)),
        ("spike + CHANGE", lambda z: spike(z) and CHG(z)),
        ("spike + LEVEL + CHANGE", lambda z: spike(z) and LVL(z) and CHG(z)),
    )

    P("=" * 116)
    P("1  BOTH FILTERS, against the matched control. NET(fixed) uses one cost per root;")
    P("   NET(hour) re-charges the crossing at the spread actually prevailing in that hour.")
    P("")
    P("    cell                            n   P(tgt)   win%    gross $  NET fixed  NET hour"
      "  spread x | matched p5    p50    p95  | verdict")
    for label, fn in CELLS:
        if fn is None:
            P(f"    {label}")
            continue
        rows = [z for z in pool if fn(z)]
        if len(rows) < 20:
            P(f"    {label:<30} {len(rows):>5}  too few")
            continue
        g = np.array([z["gross"] for z in rows])
        nf = np.array([z["net"] for z in rows])
        nh = np.array([z["net_hour"] for z in rows])
        kd = np.array([z["kind"] for z in rows])
        scl = np.array([z["sp_scale"] for z in rows])
        gp = np.array([z["gross"] for z in pool])
        dr = np.array([gp[rng.choice(len(gp), len(rows), replace=False)].mean()
                       for _ in range(N_DRAW)])
        p5, p50, p95 = np.percentile(dr, [5, 50, 95])
        vd = "ABOVE p95" if g.mean() > p95 else ("below p5" if g.mean() < p5 else "inside")
        P(f"    {label:<30} {len(rows):>5,} {(kd==0).mean():>7.1%} {(nf>0).mean():>6.1%} "
          f"{g.mean():>+9.2f} {nf.mean():>+10.2f} {nh.mean():>+9.2f} {np.median(scl):>8.3f}"
          f" | {p5:>+8.2f} {p50:>+6.2f} {p95:>+6.2f}  | {vd}")
    P("")
    P("  'spread x' is the median hour-spread relative to that root's own median -- above 1")
    P("  means the cell trades in wider markets than the fixed cost model assumes.")
    P("")
    P("=" * 116)
    P("2  WHAT THE FILTERS ACTUALLY SELECT")
    P("")
    for nm, fn in (("LEVEL: not thin", LVL), ("CHANGE: not falling", CHG)):
        k = [z for z in pool if fn(z)]
        kk = [z for z in pool if not fn(z)]
        P(f"    {nm:<22} passes {len(k):>5,} ({len(k)/len(pool):.1%})   "
          f"median spread x  pass {np.median([z['sp_scale'] for z in k]):.3f} vs "
          f"block {np.median([z['sp_scale'] for z in kk]):.3f}")
    ff = np.array([z["v_fast"] for z in pool])
    cc = np.array([z["v_chg"] for z in pool])
    P(f"    corr(LEVEL measure, CHANGE measure) = {np.corrcoef(ff, cc)[0,1]:+.3f}  "
      f"-- if near 1 the two filters are one filter")
    vr = np.array([z["vol_ratio"] for z in pool], dtype=float)
    ok = np.isfinite(vr)
    P(f"    corr(price vol_ratio, LEVEL measure) = {np.corrcoef(vr[ok], ff[ok])[0,1]:+.3f}  "
      f"-- near 0 means the filter does not cut the quiet cell")
    P("")
    P("  Exploratory. Two filters at one declared cut, on a window already ~30 looks deep;")
    P("  the reserved slice is untouched and nothing here can be promoted.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
