"""D528 DESIGN -- the ORACLE AS A DETECTOR: is this window driven by CHOP or by DRIFT, and how
reliably does price traverse the range?

    python working/d528_chop_oracle_design.py

THE PRINCIPAL'S REFRAMING, which replaces the scaling-exponent approach entirely:

  "establish the maximum/most accurate detector we can make with foresight... what are we
   detecting, we want to know in what periods does ranging chop drive price more than say drift
   or momentum... That's more of a yes or no question, then magnitude comes from a combination of
   how often the chop does one cycle (like a sin wave) around some mean and with what reliability
   does the price travel the full width of the range (probably the more important metric). We do
   all this while taking into account minor drift."

WHY THIS IS THE RIGHT OBJECT AND A HURST EXPONENT WAS NOT.

  1. It is a CLASSIFICATION with a magnitude, not a population parameter. A Hurst exponent of
     0.539 is a statement about 244 sessions; this is a statement about ONE window.
  2. THE TRAVERSE RELIABILITY IS THE TRADE. "Does price cross the full width of the range" is
     literally the win rate of a range trade with a target at the far side -- so the oracle's
     magnitude is already in the units a construction needs, rather than needing translation.
  3. It handles drift EXPLICITLY by detrending first, so chop and drift are separated instead of
     being conflated into one exponent.
  4. It is coarse and robust, which is what a LABEL needs.  D526 s8 measured that the scaling
     exponent has no reliable session-to-session variation, so nothing could predict it.  A
     binary state has a chance of varying in a way something can see.

THE FOUR QUANTITIES, per window:

    drift_share   |b*N| / (|b*N| + W)          how much of the movement is the trend, in [0,1]
    cycles        alternating band crossings / 2, on the DETRENDED series
    traverse      completed traverses / (completed + breakouts)   <- the principal's key metric
    width_sigma   W / (sigma*sqrt(N))          is the range wide or narrow for the volatility

THE TRAP THIS DESIGN HAS TO AVOID, and it is the reason the bands are QUANTILES and not extremes:
if the range is the window's realised high and low, then price touched both BY DEFINITION and the
traverse reliability is 1 by construction -- a self-fulfilling label.  Bands are set from interior
quantiles of the detrended residual so a traverse is a real event that can fail, and the synthetic
checks below confirm a random walk does NOT score 1.

No return is read as P&L, no cost, no position.  This validates a LABEL.
"""
import sys
import numpy as np

sys.path.insert(0, "scripts")
import d523_oracle_stage0 as M     # noqa: E402

RNG = np.random.default_rng(528)

Q_LO, Q_HI = 0.10, 0.90      # the range is an interior width, NOT the realised extremes
H_BAND = 0.35                # an edge is this fraction of W from the centre
B_BREAK = 0.85               # beyond this fraction of W from the centre is a BREAKOUT


def P(*a):
    print(*a, flush=True)


def detrend(p: np.ndarray) -> tuple[np.ndarray, float]:
    """Remove the linear drift. Returns (residual, slope per bar)."""
    n = len(p)
    t = np.arange(n, dtype=np.float64)
    tc = t - t.mean()
    b = float((tc * (p - p.mean())).sum() / (tc * tc).sum())
    return p - (b * tc + p.mean()), b


def oracle(p: np.ndarray) -> dict:
    """THE ORACLE LABEL for one window of prices `p` (length N+1). Uses the whole window --
    that is the point of an oracle -- but every quantity is a property of the PATH, not of a
    fitted model."""
    n = len(p) - 1
    y, b = detrend(p)
    mid = float(np.median(y))
    lo, hi = np.quantile(y, [Q_LO, Q_HI])
    W = float(hi - lo)
    if W <= 0:
        return {"degenerate": True}
    up, dn = mid + H_BAND * W, mid - H_BAND * W
    bo_up, bo_dn = mid + B_BREAK * W, mid - B_BREAK * W

    # --- band state machine: the cycle count AND the traverse outcomes come from one pass -----
    state = 0
    cross = 0                     # completed traverses: an edge reached from the OTHER edge
    breaks = 0                    # attempts that broke out instead
    armed = 0                     # the edge we are travelling FROM (0 = none yet)
    for v in y:
        if armed == -1:                     # travelling up from the lower edge
            if v >= up:
                cross += 1
                armed = 1
                state = 1
                continue
            if v <= bo_dn:
                breaks += 1
                armed = 0
                continue
        elif armed == 1:                    # travelling down from the upper edge
            if v <= dn:
                cross += 1
                armed = -1
                state = -1
                continue
            if v >= bo_up:
                breaks += 1
                armed = 0
                continue
        if armed == 0:
            if v >= up:
                armed, state = 1, 1
            elif v <= dn:
                armed, state = -1, -1
    attempts = cross + breaks
    traverse = cross / attempts if attempts else np.nan
    cycles = cross / 2.0

    sig = float(np.std(np.diff(p), ddof=1))
    drift_abs = abs(b) * n
    return {"degenerate": False,
            "drift_per_bar": b, "drift_abs": drift_abs, "W": W,
            "drift_share": drift_abs / (drift_abs + W) if (drift_abs + W) > 0 else np.nan,
            "cycles": cycles, "traverse": traverse, "attempts": attempts,
            "breaks": breaks,
            "width_sigma": W / (sig * np.sqrt(n)) if sig > 0 else np.nan,
            "net_over_W": abs(p[-1] - p[0]) / W}


def summarise(paths: np.ndarray) -> dict:
    """paths: (N+1, n). Mean of each oracle field over the columns."""
    out = [oracle(paths[:, j]) for j in range(paths.shape[1])]
    good = [o for o in out if not o["degenerate"]]
    keys = ("drift_share", "cycles", "traverse", "attempts", "width_sigma", "net_over_W")
    r = {k: float(np.nanmean([o[k] for o in good])) for k in keys}
    r["n"] = len(good)
    r["traverse_sd"] = float(np.nanstd([o["traverse"] for o in good], ddof=1))
    r["cycles_sd"] = float(np.nanstd([o["cycles"] for o in good], ddof=1))
    return r


# =============================================================================================
N = 72
NP = 4000
P("=" * 104)
P("1  KNOWN-ANSWER CASES -- the oracle must separate chop from drift, and a random walk must")
P("   sit BETWEEN them rather than at either extreme")
P("=" * 104)
t = np.arange(N + 1, dtype=np.float64)

cases = {}
# pure chop: a sine wave, 3 full cycles, tiny noise
cases["pure chop, 3 sine cycles"] = (
    np.sin(2 * np.pi * 3 * t / N)[:, None] + 0.02 * RNG.normal(size=(N + 1, NP)))
cases["pure chop, 1 sine cycle"] = (
    np.sin(2 * np.pi * 1 * t / N)[:, None] + 0.02 * RNG.normal(size=(N + 1, NP)))
# pure drift: a straight line, tiny noise
cases["pure drift, straight line"] = (
    (t / N)[:, None] * 2.0 + 0.02 * RNG.normal(size=(N + 1, NP)))
# random walk
cases["random walk"] = np.vstack([np.zeros((1, NP)), RNG.normal(size=(N, NP)).cumsum(0)])
# chop WITH drift -- the principal's "minor drift" case
cases["chop + minor drift"] = (
    np.sin(2 * np.pi * 3 * t / N)[:, None] + (t / N)[:, None] * 1.0
    + 0.02 * RNG.normal(size=(N + 1, NP)))
cases["chop + major drift"] = (
    np.sin(2 * np.pi * 3 * t / N)[:, None] + (t / N)[:, None] * 6.0
    + 0.02 * RNG.normal(size=(N + 1, NP)))
# a single trend leg then chop
half = N // 2
leg = np.concatenate([np.linspace(0, 2, half + 1), np.full(N - half, 2.0)])
cases["one leg then flat"] = leg[:, None] + 0.05 * RNG.normal(size=(N + 1, NP))

P("")
P("   case                          drift_share  cycles (sd)   TRAVERSE (sd)  attempts  "
  "width/sigma  net/W")
for name, pp in cases.items():
    r = summarise(pp)
    P(f"   {name:<28}    {r['drift_share']:.3f}     {r['cycles']:.2f} ({r['cycles_sd']:.2f})"
      f"   {r['traverse']:.3f} ({r['traverse_sd']:.3f})    {r['attempts']:.2f}"
      f"      {r['width_sigma']:.2f}     {r['net_over_W']:.2f}")

P("")
P("   THE DEGENERACY CHECK, which is why the bands are QUANTILES and not the realised extremes:")
rw = summarise(cases["random walk"])
P(f"   a random walk scores traverse {rw['traverse']:.3f}, NOT 1.000 -- so the label is not")
P(f"   self-fulfilling, and pure chop ({summarise(cases['pure chop, 3 sine cycles'])['traverse']:.3f})")
P(f"   is separated from pure drift ({summarise(cases['pure drift, straight line'])['traverse']:.3f}).")

# =============================================================================================
P("")
P("=" * 104)
P("2  DOES THE TRAVERSE RELIABILITY TRACK WHAT A RANGE TRADE WOULD EARN?")
P("=" * 104)
P("   A range trade buys the lower edge and targets the upper. Its win rate IS the traverse")
P("   reliability, and its payoff is the full width against a breakout stop. So:")
P("")
P("   traverse   implied payoff at target=W*0.7, stop=W*0.5   expectancy in units of W")
for tv in (0.30, 0.40, 0.50, 0.60, 0.70, 0.80):
    tgt, stp = 0.70, 0.50
    exp = tv * tgt - (1 - tv) * stp
    P(f"     {tv:.2f}         win {tv:.0%} x {tgt:.2f}W, lose {1-tv:.0%} x {stp:.2f}W"
      f"           {exp:+.3f} W   {'PROFITABLE' if exp > 0 else ''}")
P("")
P(f"   BREAKEVEN traverse reliability at that geometry is {0.50/(0.70+0.50):.3f}.")
P("   THAT is the number the oracle has to beat for a window to be worth trading as a range,")
P("   and it is why the principal called it the more important metric: it is a WIN RATE.")

# =============================================================================================
P("")
P("=" * 104)
P("3  ON REAL DATA: the label's DISTRIBUTION, and -- the question the last oracle failed --")
P("   DOES IT VARY AND PERSIST?")
P("=" * 104)
import pandas as pd
import d526_mid_vs_trade_scaling as Q     # noqa: E402

d = pd.read_parquet("data/fixtures/fut_day5m.parquet",
                    columns=["root", "day", "bar", "close", "present", "same_front"])
d = d[d["present"]]
d = d[d["same_front"]]
d = d[d["day"] <= "2023-12-29"]

P("")
P("   root   sessions   traverse  (sd)   cycles  drift_share   share of sessions with")
P("                      mean            mean     mean         traverse > breakeven 0.417")
rows = {}
for r in ("ES", "NQ", "YM", "RTY", "GC", "ZN", "ZB", "6E", "CL", "HO"):
    g = d[d["root"] == r].sort_values(["day", "bar"], kind="stable")
    R, days = Q.session_matrix(g, "close")
    if R.shape[1] < 500:
        continue
    pxs = np.vstack([np.zeros((1, R.shape[1])), R.cumsum(0)])     # log-price paths
    labs = [oracle(pxs[:, j]) for j in range(pxs.shape[1])]
    tv = np.array([o["traverse"] if not o["degenerate"] else np.nan for o in labs])
    cy = np.array([o["cycles"] if not o["degenerate"] else np.nan for o in labs])
    ds = np.array([o["drift_share"] if not o["degenerate"] else np.nan for o in labs])
    rows[r] = (tv, cy, ds, days)
    P(f"   {r:>4}   {R.shape[1]:>8,}    {np.nanmean(tv):.3f} ({np.nanstd(tv, ddof=1):.3f})"
      f"   {np.nanmean(cy):.2f}     {np.nanmean(ds):.3f}        "
      f"{np.nanmean(tv > 0.417):.1%}")

P("")
P("   AND THE RELIABILITY OF THE LABEL ITSELF -- corr(window W, next window W), within root,")
P("   non-overlapping. This is where the scaling exponent died (all cells noise, D526 s8).")
P("")
P("   root    " + "  ".join(f"W={w:<4}" for w in (1, 5, 10, 20, 60)))
for r, (tv, cy, ds, days) in rows.items():
    cells = []
    for W in (1, 5, 10, 20, 60):
        s = tv[np.isfinite(tv)]
        nb = len(s) // W
        if nb < 10:
            cells.append("  --  ")
            continue
        blk = s[:nb * W].reshape(nb, W).mean(1)
        a, b = blk[:-1][::2], blk[1:][::2]
        cells.append(f"{M.pearson(a, b):+.3f}" if len(a) > 5 else "  --  ")
    P(f"   {r:>4}    " + "  ".join(cells))
P("")
P("   pairs at each W (ES): " + "  ".join(
    f"W={W}:{len(tv[np.isfinite(tv)])//W//2}" for W in (1, 5, 10, 20, 60)))
P("   SE of a correlation at n pairs is 1/sqrt(n-1); judge every cell against it.")
