"""WHY D523 Stage 0 saw no trends: four candidate defects, measured rather than argued.

    python working/d523_diagnose_why.py

The principal's objection: trending markets demonstrably exist, therefore the detection is wrong.
This script tests four specific ways it could be wrong, in the runner's own quantities.

  A  DRIFT vs NOISE.  A trend is a small drift against per-bar noise.  Does a REALISTIC trend
     even register as trending at H=8, or does it read as mean-reverting?
  B  THE RETRACEMENT PROBLEM.  eff demands near-monotonicity.  D471 measured that a real move
     retraces ~45-50% before paying.  What does eff say about such a path?
  C  THE HORIZON CAP.  Stage 0's ladder stopped at H=20 because a NON-OVERLAPPING PAIR needs
     2H <= 84 -- but that constraint binds STAGE 1, not Stage 0b, which needs one block.
  D  BID-ASK BOUNCE.  The numerator |sum r| TELESCOPES the bounce away; the denominator
     sum|r| ACCUMULATES it.  So eff is biased DOWN by an amount that scales with tick/vol,
     and the sign shuffle cannot correct it because it conditions on the inflated |r|.
"""
import sys
import numpy as np

sys.path.insert(0, "scripts")
import d523_oracle_stage0 as M     # noqa: E402

RNG = np.random.default_rng(20260913)


def P(*a):
    print(*a, flush=True)


def z_of(R: np.ndarray, n_draw: int = 4096) -> np.ndarray:
    """Mid-p percentile of eff inside each column's sign-shuffle set (sampled, any H)."""
    H, n = R.shape
    a = np.abs(R)
    path = a.sum(0)
    S = np.where(RNG.integers(0, 2, (n_draw, H)) == 1, 1, -1).astype(np.float64)
    S[:, 0] = 1.0
    out = np.empty(n)
    step = max(1, 2_000_000 // n_draw)
    for lo in range(0, n, step):
        hi = min(lo + step, n)
        vals = np.abs(S @ a[:, lo:hi]) / path[lo:hi]
        e = np.abs(R[:, lo:hi].sum(0)) / path[lo:hi]
        out[lo:hi] = (2 * (vals < e).sum(0) + (vals == e).sum(0)) / (2 * n_draw)
    return out


# =============================================================================================
P("=" * 94)
P("A  DRIFT vs NOISE -- what does a REAL trend score, at each horizon?")
P("=" * 94)
P("   A market that moves X% over one 84-bar session, with 5-minute sigma of 0.05%,")
P("   has per-bar drift mu = X/84.  Simulated, 20,000 blocks a cell.")
P("")
P("   mu/sigma  daily move    H=8      H=20     H=42     H=83    <- mean z (0.5 = no signal)")
SIG = 0.0005
for mo in (0.0, 0.005, 0.01, 0.02, 0.04):
    mu = mo / 84.0
    cells = []
    for H in (8, 20, 42, 83):
        R = RNG.normal(mu, SIG, (H, 20_000))
        cells.append(z_of(R).mean())
    P(f"   {mu/SIG:8.3f}  {mo*100:7.1f}%   " + "  ".join(f"{c:7.4f}" for c in cells))
P("")
P("   READ THE TOP-LEFT AGAINST THE BOTTOM-RIGHT. That is the defect: a genuine trend is")
P("   INVISIBLE at the horizons Stage 0 swept, and obvious only at the session scale.")

# =============================================================================================
P("")
P("=" * 94)
P("B  THE RETRACEMENT PROBLEM -- eff demands monotonicity; real moves retrace ~50% (D471)")
P("=" * 94)
paths = {
    "straight line, 8 up":            np.array([1.0] * 8),
    "trend, 25% retrace (+3,-1)x4":   np.array([3.0, -1, 3, -1, 3, -1, 3, -1]),
    "trend, 50% retrace (+2,-1)x4":   np.array([2.0, -1, 2, -1, 2, -1, 2, -1]),
    "trend, one big leg then chop":   np.array([6.0, 1, -1, 1, -1, 1, -1, 1]),
    "pure chop (+1,-1)x4":            np.array([1.0, -1, 1, -1, 1, -1, 1, -1]),
}
P("   path                              net   pathlen    eff      z      verdict")
for name, p in paths.items():
    e = M.eff(p)
    zz = z_of(p[:, None])[0]
    v = ("TRENDING" if zz > 0.95 else "ordinary" if zz > 0.2 else "REVERTING")
    P(f"   {name:<32} {p.sum():+5.0f}   {np.abs(p).sum():7.0f}   {e:.3f}  {zz:.3f}   {v}")
P("")
P("   D471 measured adverse/|move| = 0.45-0.50 in EVERY cell: a winning move goes about half")
P("   its size against you first. THAT path is the '50% retrace' row -- and eff calls it")
P("   ordinary, because the sign shuffle can rearrange the same magnitudes into a straight line.")

# =============================================================================================
P("")
P("=" * 94)
P("C + D  ON THE REAL FIXTURE: the horizon cap, and bounce vs tick coarseness")
P("=" * 94)
d, info = M.eligible()
by_root = {r: g for r, g in d.groupby("root", sort=True)}
del d

P("")
P("C  Stage 0b's ladder, EXTENDED past the cap that only Stage 1 needed")
P("   H     blocks    mean z    exception   b0      excess pp")
rows = {}
for H in (8, 20, 42, 83):
    zs, excs, b0s = [], [], []
    for r in info["roots"]:
        R, sid, ordn, _ = M.blocks_for_root(by_root[r], H)
        if R.shape[1] == 0:
            continue
        keep = np.abs(R).sum(0) > 0
        R = R[:, keep]
        if R.shape[1] == 0:
            continue
        a = np.abs(R)
        path = a.sum(0)
        n_draw = 4096
        S = np.where(RNG.integers(0, 2, (n_draw, H)) == 1, 1, -1).astype(np.float64)
        S[:, 0] = 1.0
        k95 = int(np.ceil(0.95 * n_draw))
        zz = np.empty(R.shape[1])
        ex = np.empty(R.shape[1], bool)
        bb = np.empty(R.shape[1])
        step = max(1, 2_000_000 // n_draw)
        for lo in range(0, R.shape[1], step):
            hi = min(lo + step, R.shape[1])
            vals = np.abs(S @ a[:, lo:hi]) / path[lo:hi]
            e = np.abs(R[:, lo:hi].sum(0)) / path[lo:hi]
            q = np.partition(vals, k95 - 1, axis=0)[k95 - 1]
            zz[lo:hi] = (2 * (vals < e).sum(0) + (vals == e).sum(0)) / (2 * n_draw)
            ex[lo:hi] = e > q
            bb[lo:hi] = (vals > q).sum(0) / n_draw
        zs.append(zz); excs.append(ex); b0s.append(bb)
    z = np.concatenate(zs); ex = np.concatenate(excs); b0 = np.concatenate(b0s)
    rows[H] = (len(z), z.mean(), ex.mean(), b0.mean(), 100 * (ex.mean() - b0.mean()))
    P(f"  {H:>3}  {len(z):>9,}   {z.mean():.4f}    {ex.mean()*100:6.3f}%  {b0.mean()*100:6.3f}%"
      f"   {100*(ex.mean()-b0.mean()):+8.3f}")

# ---------------------------------------------------------------------------------------------
P("")
P("D  Bounce: is mean z ordered by TICK COARSENESS? (bounce inflates sum|r|, not |sum r|)")
P("   per root: median |5-min return| in TICKS, against that root's mean z at H=8")
import json
bmeta = json.loads((M.REPO / "data" / "fixtures" /
                    "fut_breadth_hourly.meta.json").read_text(encoding="utf-8"))
specs = bmeta["specs"]
st = json.loads((M.REPO / "data" / "d523_oracle_stage0.json").read_text(encoding="utf-8"))
mz8 = {k: v["mean_z"] for k, v in st["ladder"]["8"]["per_root"].items()}

tab = []
for r in info["roots"]:
    g = by_root[r]
    tick = specs.get(r, {}).get("tick_price_units")
    if tick is None:
        continue
    c = g["close"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    bar = g["bar"].to_numpy()
    ok = (day[1:] == day[:-1]) & (np.diff(bar) == 1)
    dr = np.abs(np.diff(c))[ok]
    dr = dr[dr > 0]
    if len(dr) < 1000:
        continue
    tab.append((r, float(np.median(dr) / tick), mz8[r]))

tab.sort(key=lambda t: t[1])
P("   root   median |r| in ticks   mean z")
for r, t, m in tab:
    P(f"   {r:>4}   {t:>18.2f}   {m:.4f}")
tk = np.array([t for _, t, _ in tab])
mv = np.array([m for _, _, m in tab])
P("")
P(f"   Spearman( median |r| in ticks , mean z ) = {M.spearman(tk, mv):+.4f}   on {len(tab)} roots")
P("   A POSITIVE rank correlation is the bounce signature: the coarser a root's tick relative")
P("   to its 5-minute move, the further its efficiency falls below the exchangeable value.")
P("")
P("   And the roots whose moves are LARGEST in ticks -- where bounce matters least:")
for r, t, m in tab[-6:]:
    P(f"      {r:>4}  {t:>6.2f} ticks   mean z {m:.4f}")
