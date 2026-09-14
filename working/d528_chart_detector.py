"""Ten candle charts of the causal detector and every one of its outputs, at s=3.

    python working/d528_chart_detector.py

The ten cases are the DECILES of realised P&L across all admitted excursions, so they span the
detector's performance from worst to best rather than being ten cherry-picked wins.

CANDLES ARE BUILT FROM THE 1-MINUTE MID, aggregated to the detector's own bar size, so the chart
shows exactly what the detector sees and no trade prices are mixed in. The detector SAMPLES the
mid every s minutes, so each candle is the OHLC of the s minutes BEGINNING at that sample and the
sample is the candle's OPEN.

Every detector output is drawn:
  history A [0,10) and history B [10,20)   shaded, each with its own fitted line -- the A1 test
  the LEVEL                                fitted on history B, EXTRAPOLATED forward
  +/- 2 sigma                              the excursion threshold
  +/- 3 sigma                              the extend/stop threshold
  the trade window [20,31)                 shaded, where an excursion may start
  the tracking window                      shaded lighter
  entry, exit, and the hold                marked and joined
  and the numbers                          sigma in ticks, slope, hold, realised P&L in ticks
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.patches import Rectangle             # noqa: E402

sys.path.insert(0, "scripts")
import d528_mean_reversion_oracle as Q               # noqa: E402

S = 3
X, TAU = 2.0, 20
H = Q.H_EST
TRADE, HIST = 11, 2 * Q.H_EST
SPAN = HIST + TRADE + TAU
OUT = "working/d528_detector_charts.png"

C_UP, C_DN = "#1a7f5a", "#b3402f"
C_LVL, C_ENV, C_EXT, C_FIT = "#2b5d9e", "#8a6bbf", "#b3402f", "#c98a1e"
SH = {"A": "#f1f0ea", "B": "#e4e9f3", "T": "#ecf3ea", "K": "#f8f8f5"}


def fit(seg):
    n = len(seg)
    t = np.arange(n, dtype=np.float64)
    tc = t - t.mean()
    b = float((tc * (seg - seg.mean())).sum() / (tc * tc).sum())
    a = float(seg.mean() - b * t.mean())
    r = seg - (a + b * t)
    return b, a, float(r.std(ddof=1))


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
cases = []

for r in roots:
    g = d[d["root"] == r]
    tick = sp[r]["tick_price_units"]
    bar = g["bar"].to_numpy()
    mid = g["mid"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    for a_, b_ in zip(np.concatenate(([0], cut)), np.concatenate((cut, [len(g)]))):
        bb, mm = bar[a_:b_], mid[a_:b_]
        brk = np.flatnonzero(np.diff(bb) != 1)
        st = np.concatenate(([0], brk + 1))
        spp = np.concatenate((brk + 1, [len(bb)]))
        i = int(np.argmax(spp - st))
        run, run_b0 = mm[st[i]:spp[i]], int(bb[st[i]])
        npts = len(run) // S
        j = 0
        while j + HIST + TRADE <= npts:
            idx = np.arange(j, min(j + SPAN, npts)) * S
            path = run[idx]
            if len(path) < HIST + TRADE:
                break
            b1, a1, s1 = fit(path[:H])
            b2, a2, s2 = fit(path[H:HIST])
            pooled = float(np.sqrt(0.5 * (s1 ** 2 + s2 ** 2)))
            med = float(np.median(np.abs(np.diff(path[H:HIST]))) / tick)
            if not (pooled > 0 and abs(b1 - b2) * H <= 0.5 * pooled and med >= Q.MIN_TICKS):
                j += TRADE
                continue
            t_ax = np.arange(len(path), dtype=np.float64) - H
            lvl = a2 + b2 * t_ax
            y = path - lvl
            thr, ext = X * s2, Q.EXT_MULT * X * s2
            j0 = -1
            for k in range(HIST, min(HIST + TRADE, len(path))):
                if abs(y[k]) >= thr:
                    j0 = k
                    break
            if j0 < 0:
                j += TRADE
                continue
            sgn = float(np.sign(y[j0]))
            seg = y[j0 + 1:min(j0 + 1 + TAU, len(path))] * sgn
            if len(seg) == 0:
                j += TRADE
                continue
            hr, he = np.flatnonzero(seg <= 0), np.flatnonzero(seg >= ext)
            i_r = hr[0] if len(hr) else 10 ** 9
            i_e = he[0] if len(he) else 10 ** 9
            ret = i_r < i_e
            dd = (min(i_r, i_e) if min(i_r, i_e) < 10 ** 9 else len(seg) - 1) + 1
            jx = min(j0 + dd, len(path) - 1)
            ohlc = np.array([[run[k], run[k:k + S].max(), run[k:k + S].min(),
                              run[min(k + S - 1, len(run) - 1)]] for k in idx])
            cases.append({"root": r, "day": str(day[a_]), "tick": tick, "path": path,
                          "ohlc": ohlc, "lvl": lvl, "sd": s2, "slope": b2, "b1": b1, "a1": a1,
                          "j0": j0, "jx": jx, "d": dd, "sgn": sgn,
                          "pnl": sgn * (y[j0] - y[jx] - b2 * dd) / tick,
                          "out": "RETURN" if ret else ("STOPPED" if i_e < 10 ** 9 else "TIMEOUT"),
                          "t0": run_b0 + j * S})
            j += TRADE

pn = np.array([c["pnl"] for c in cases])
order = np.argsort(pn)
qs = np.arange(0.05, 1.0, 0.1)
picks = [cases[order[int(q * (len(order) - 1))]] for q in qs]
print(f"{len(cases):,} admitted excursions at s={S} across {len(roots)} roots")
print(f"  mean {pn.mean():+.2f} ticks   median {np.median(pn):+.2f}   "
      f"RETURN {sum(c['out']=='RETURN' for c in cases)/len(cases):.1%}  "
      f"STOPPED {sum(c['out']=='STOPPED' for c in cases)/len(cases):.1%}  "
      f"TIMEOUT {sum(c['out']=='TIMEOUT' for c in cases)/len(cases):.1%}")
print("  deciles: " + "  ".join(f"p{int(q*100)} {c['pnl']:+.1f}" for q, c in zip(qs, picks)))

fig, axes = plt.subplots(10, 1, figsize=(15.5, 40.0))
fig.patch.set_facecolor("white")
for ax, q, c in zip(axes, qs, picks):
    n = len(c["path"])
    oh, lvl, sd = c["ohlc"], c["lvl"], c["sd"]
    for lo, hi, key, lab in ((0, H, "A", "history A"), (H, HIST, "B", "history B + level fit"),
                             (HIST, HIST + TRADE, "T", "trade window"),
                             (HIST + TRADE, n, "K", "tracking")):
        if hi > lo:
            ax.axvspan(lo - 0.5, min(hi, n) - 0.5, color=SH[key], zorder=0)
            ax.text((lo + min(hi, n) - 1) / 2, 0.025, lab,
                    transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                    fontsize=8, color="#57574f")
    xs = np.arange(n)
    ax.plot(xs, lvl, color=C_LVL, lw=2.0, zorder=3, label="level (extrapolated)")
    for m, ls, col, lab in ((X, ":", C_ENV, "±2σ entry"), (X * Q.EXT_MULT, "--", C_EXT, "±3σ stop")):
        ax.plot(xs, lvl + m * sd, ls=ls, color=col, lw=1.2, zorder=3, label=lab)
        ax.plot(xs, lvl - m * sd, ls=ls, color=col, lw=1.2, zorder=3)
    ax.plot(np.arange(H), c["a1"] + c["b1"] * np.arange(H), ls="--", color=C_FIT, lw=1.8,
            zorder=4, label="half-window fits (A1 slope test)")
    ax.plot(np.arange(H, HIST), lvl[H:HIST], color=C_FIT, lw=2.4, zorder=4)
    for i in range(n):
        o, h_, l_, cl = oh[i]
        col = C_UP if cl >= o else C_DN
        ax.plot([i, i], [l_, h_], color=col, lw=0.9, zorder=2)
        ax.add_patch(Rectangle((i - 0.31, min(o, cl)), 0.62, max(abs(cl - o), 1e-9),
                               facecolor=col, edgecolor=col, zorder=2))
    j0, jx = c["j0"], c["jx"]
    oc = {"RETURN": C_UP, "STOPPED": C_DN, "TIMEOUT": "#6b6b64"}[c["out"]]
    ax.plot([j0], [c["path"][j0]], "o", ms=11, mfc="none", mec="black", mew=2.2, zorder=6)
    ax.plot([jx], [c["path"][jx]], "s", ms=12, color=oc, mec="white", mew=1.8, zorder=7)
    ax.axvline(jx, color=oc, lw=1.0, alpha=0.45, zorder=1)
    ax.plot([j0, jx], [c["path"][j0], c["path"][jx]], ls=":", color="black", lw=1.2, zorder=5)
    ax.set_xlim(-1, n)
    ax.set_title(f"p{int(q*100)}   {c['root']}  {c['day']}   {c['out']}   "
                 f"P&L {c['pnl']:+.1f} ticks   σ {sd/c['tick']:.1f} tk   "
                 f"slope {c['slope']/c['tick']:+.2f} tk/bar   held {c['d']} bars = {c['d']*S}m",
                 fontsize=11, loc="left", pad=10, color=oc if c["out"] != "TIMEOUT" else "#1a1a18")
    ax.set_ylabel(f"{c['root']} mid", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", color="#e8e6e0", lw=0.6)
    ax.set_axisbelow(True)
    if ax is axes[0]:
        ax.legend(fontsize=8, loc="upper left", framealpha=0.92, ncols=2)
axes[-1].set_xlabel(f"detector bar ({S}-minute mid candles)", fontsize=9)
fig.suptitle(f"The causal mean-reversion detector, ten deciles of its own realised P&L   "
             f"(s={S}m, {len(cases):,} admitted excursions, mean {pn.mean():+.2f} / "
             f"median {np.median(pn):+.2f} ticks)", fontsize=13, y=0.999)
fig.tight_layout(rect=(0, 0, 1, 0.995))
fig.savefig(OUT, dpi=110, facecolor="white")
print(f"wrote {OUT}")
