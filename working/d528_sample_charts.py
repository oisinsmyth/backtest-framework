"""TEN SAMPLE TRADES, SPREAD ACROSS THE P&L DISTRIBUTION, with every output drawn.

    python working/d528_sample_charts.py

The construction is the current one: micro universe, `traverse` classifier, entry at 2 sigma from
a FLAT-mean level, drift-aligned, target at the MIRROR of the entry, exits DRIFT-following,
stop at G = 3.0 sigma from the level, tau = 40.

The ten cases are the DECILES of realised net P&L, so they span the detector's whole range rather
than being ten chosen wins. Candles are the 1-minute mids the detector actually reads.

Everything the trade knows is drawn:
  history A [t-2H, t-H) and B [t-H, t)   shaded, each with its own line -- the stability test
  the flat-mean LEVEL                    and, where the frame is DRIFT, its forward path
  +/- 1.5 sigma                          the band whose full traversal the classifier requires
  the entry extreme                      +/- 2 sigma
  the TARGET                             the mirror of the entry, carried by the drift
  the STOP                               G = 3.0 sigma from the level, carried by the drift
  entry, exit, hold, and the numbers     sigma in ticks, slope, bars held, net $ and outcome
"""
from __future__ import annotations

import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.patches import Rectangle             # noqa: E402

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402

H = Z.H
X, G, TAU = 2.0, 3.0, 40
TARGET, FRAME = "reflect", "drift"
TRAV_K = 1.5
PRE, POST = 2 * H, 6           # bars of context drawn either side
OUT = "working/d528_sample_trades.png"

C_UP, C_DN = "#1a7f5a", "#b3402f"
C_LVL, C_BAND, C_TGT, C_STP, C_FIT = "#2b5d9e", "#8a6bbf", "#1a7f5a", "#b3402f", "#c98a1e"
SH = {"A": "#f1f0ea", "B": "#e4e9f3", "T": "#f8f8f5"}


def P(*a):
    print(*a, flush=True)


d = Q.load()
sp = Q.specs()
roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
udays = sorted(set(d["day"]))
day_index = {u: i for i, u in enumerate(udays)}
rev_day = {i: u for u, i in day_index.items()}

cases = []
for r in roots:
    gg = d[d["root"] == r]
    tick = sp[r]["tick_price_units"]
    tick_usd = sp[r]["tick_usd"]
    cost_tk = R.COST.get(r, R.COST_DEFAULT)
    for day, pth, b0 in B.sessions_with_bars(gg, 1):
        c = Z.classify2(pth, tick)
        if c is None:
            continue
        keep = Z.entry_mask(c, "flat", tick, cost_tk, "traverse")
        tr = O.resolve(pth, c, "flat", keep, tick, tick_usd, cost_tk, TARGET, FRAME, G, TAU,
                       day_index[day], b0, r)
        for z in tr:
            i = (z["t_in"] - day_index[day] * 2000) - b0        # path index of the entry
            cases.append({**z, "path": pth, "idx": i, "tick": tick, "b0": b0,
                          "sd": float(c["flat_sd"][i - 2 * H]),
                          "lvl": float(c["flat_lvl"][i - 2 * H]),
                          "slope": float(c["slope"][i - 2 * H]),
                          "y": float(c["flat_y"][i - 2 * H]),
                          "net": z["g_real_tk"] * tick_usd - z["cost_usd"]})

net = np.array([c["net"] for c in cases])
order = np.argsort(net)
qs = np.arange(0.05, 1.0, 0.1)
picks = [cases[order[int(q * (len(order) - 1))]] for q in qs]
P(f"{len(cases)} trades; deciles of net $: " +
  "  ".join(f"p{int(q*100)}={c['net']:+.1f}" for q, c in zip(qs, picks)))

fig, axes = plt.subplots(10, 1, figsize=(15.5, 40.0))
fig.patch.set_facecolor("white")
for ax, q, c in zip(axes, qs, picks):
    pth, i, tick, sd = c["path"], c["idx"], c["tick"], c["sd"]
    lo = max(i - PRE, 0)
    hi = min(i + c["bars"] + POST, len(pth))
    xs = np.arange(lo, hi)
    s = -1.0 if c["side"] < 0 else 1.0
    # the level and its forward path (the DRIFT frame carries it at `slope` per bar)
    k = xs - i
    lvl_line = c["lvl"] + c["slope"] * np.where(k > 0, k, 0)
    ax.plot(xs, lvl_line, color=C_LVL, lw=2.0, zorder=4, label="flat-mean level (carried)")
    for m, col, ls, lab in ((TRAV_K, C_BAND, ":", f"±{TRAV_K}σ traverse band"),
                            (X, "#8a8a82", "--", f"±{X}σ entry extreme")):
        ax.plot(xs, lvl_line + m * sd, ls=ls, color=col, lw=1.1, zorder=3, label=lab)
        ax.plot(xs, lvl_line - m * sd, ls=ls, color=col, lw=1.1, zorder=3)
    # target (mirror of the entry) and stop (G sigma), both carried by the drift
    ax.plot(xs, lvl_line - c["y"], color=C_TGT, lw=1.8, zorder=4, label="target = mirror of entry")
    ax.plot(xs, lvl_line + s * G * sd, color=C_STP, lw=1.8, ls="-.", zorder=4,
            label=f"stop = {G}σ from level")
    # history shading
    for a_, b_, key, lab in ((i - 2 * H, i - H, "A", "history A"), (i - H, i, "B", "history B"),
                             (i, i + c["bars"], "T", "the trade")):
        if b_ > a_ and b_ >= lo:
            ax.axvspan(max(a_, lo) - 0.5, min(b_, hi) - 0.5, color=SH[key], zorder=0)
            ax.text((max(a_, lo) + min(b_, hi) - 1) / 2, 0.02, lab,
                    transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                    fontsize=8, color="#57574f")
    # candles from the 1-minute mids: one bar per minute, so open == close; drawn as a step line
    ax.plot(xs, pth[lo:hi], color="#2b2b28", lw=1.0, zorder=2)
    for j in xs:
        col = C_UP if (j > lo and pth[j] >= pth[j - 1]) else C_DN
        ax.plot([j, j], [pth[j], pth[j]], marker="_", ms=5, color=col, zorder=2)
    jx = min(i + c["bars"], len(pth) - 1)
    oc = {0: C_UP, 1: C_DN, 2: "#6b6b64"}[c["kind"]]
    ax.plot([i], [pth[i]], "o", ms=11, mfc="none", mec="black", mew=2.2, zorder=6)
    ax.plot([jx], [pth[jx]], "s", ms=12, color=oc, mec="white", mew=1.8, zorder=7)
    ax.plot([i, jx], [pth[i], pth[jx]], ls=":", color="black", lw=1.2, zorder=5)
    ax.set_xlim(lo - 1, hi)
    nm = {0: "TARGET", 1: "STOP", 2: "TIMEOUT"}[c["kind"]]
    mm = Q.DAY_LO + c["b0"] + i
    ax.set_title(f"p{int(q*100)}   {c['root']}  {rev_day[c['day']]}  {mm//60:02d}:{mm%60:02d} ET"
                 f"   {'LONG' if c['side'] < 0 else 'SHORT'}   {nm}   net ${c['net']:+.2f}"
                 f"   σ {sd/tick:.1f} tk   slope {c['slope']/tick:+.2f} tk/bar"
                 f"   held {c['bars']} bars",
                 fontsize=11, loc="left", pad=10, color=oc if c["kind"] != 2 else "#1a1a18")
    ax.set_ylabel(f"{c['root']} mid", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", color="#e8e6e0", lw=0.6)
    ax.set_axisbelow(True)
    if ax is axes[0]:
        ax.legend(fontsize=8, loc="upper left", framealpha=0.92, ncols=3)
axes[-1].set_xlabel("minute of session", fontsize=9)
fig.suptitle(f"Ten sample trades across the P&L distribution   "
             f"(traverse classifier, mirror target, drift-following exits, G={G}, τ={TAU}; "
             f"{len(cases)} trades, mean ${net.mean():+.2f}, median ${np.median(net):+.2f})",
             fontsize=13, y=0.999)
fig.tight_layout(rect=(0, 0, 1, 0.995))
fig.savefig(OUT, dpi=110, facecolor="white")
P(f"wrote {OUT}")
