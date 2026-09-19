"""THE CHASE: does the volume gate help because it is a CHANGE rather than a LEVEL?

D531 found the principal's gate ADDING +0.38 points of hit rate where D506's activity filter COST
-2.09. Two things differ between them, and only one is interesting:

    D506 (LEVEL)    is TODAY unusually active?      score = sqrt(range/med20 x volume/med20)
                                                    in play = score >= trailing 250-session p90
    PRINCIPAL (CHANGE)  has activity been RISING?   gate  = log(EMA_10(V) / SMA_50(V)) > 0

D526 established that on a daily clock a LEVEL collapses to a regime variable -- CL's curve had
0 of 8 years containing both states -- while the CHANGE has real within-period variation, 8 of 8.
So this is not a variant of D506's filter; it may be the repair D526 named.

THE COMPARISON IS LIKE FOR LIKE BY CONSTRUCTION: both gates read the SAME input (the night session's
volume, known before 09:00), on the same roots, the same signals and the same window. Only the
functional form differs.

Statistic: D506's accuracy term, `p(gated) - p(rest)` in POINTS, so it is directly comparable to its
published -2.09. Null: permute the gate mask across sessions, preserving the number gated -- the
question is whether THIS selection picks better sessions than an arbitrary one of the same size.

NO P&L, no cost, nothing admitted (R15). In sample 2016-01-04..2023-12-29; the 2024+ slice unread.

    python working/chase_volume_gate_level_vs_change.py
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import activity_filter as AF  # noqa: E402

# The D467 SESSIONS fixture, not the breadth one: activity_filter is built for it, and the breadth
# fixture carries ~17% NaN night-range rows on ES, which makes every 20-session rolling median NaN
# and collapses the LEVEL score to nothing (score finite 0 of 2,453). Measured, not assumed.
FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
LO, HI = "2016-01-04", "2023-12-29"
ROOTS = ["ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E"]      # D467/D506/D515's eight
EMA_N, SMA_N = 10, 50
N_DRAWS = 2000
SEED = 20260914


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


D506B = _load("d506c", "d506_macd_breadth.py")


def ema(x, n):
    a = 2.0 / (n + 1.0)
    out = np.empty(len(x)); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def gates(night_vol, score, thr):
    """Two gates from the SAME night input. Both causal: night data is complete before 09:00."""
    level = AF.in_play(score, thr)                                  # D506's: is today unusually active
    lv = np.log(np.where(night_vol > 0, night_vol, np.nan))
    change = np.full(len(lv), False)
    fin = np.isfinite(lv)
    if fin.sum() > SMA_N:
        z = lv[fin]
        e = ema(z, EMA_N)
        s = pd.Series(z).rolling(SMA_N, min_periods=SMA_N).mean().to_numpy()
        ch = np.full(len(lv), np.nan); ch[fin] = e - s
        change = ch > 0                                             # the principal's: is it RISING
    return level, change


def acc_term(hit, mask, rng):
    """p(gated) - p(rest) in points, and the permutation null that preserves the number gated."""
    m = np.asarray(mask, bool) & np.isfinite(hit)
    ok = np.isfinite(hit)
    if m.sum() < 60 or (ok & ~m).sum() < 60:
        return None
    obs = 100 * (hit[m].mean() - hit[ok & ~m].mean())
    h = hit[ok]; k = int(m[ok].sum()); n = len(h)
    draws = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        idx = rng.permutation(n)
        sel = idx[:k]
        draws[i] = 100 * (h[sel].mean() - h[idx[k:]].mean())
    return dict(obs=float(obs), n_gated=int(m.sum()), n_rest=int((ok & ~m).sum()),
                p50=float(np.median(draws)), p95=float(np.quantile(draws, 95 / 100)),
                share_ge=float(np.mean(draws >= obs)))


def main():
    rng = np.random.default_rng(SEED)
    B = pd.read_csv(FIX, dtype={"root": str, "day": str, "contract": str})
    B = B[(B["day"] >= LO) & (B["day"] <= HI)]
    assert B["day"].max() <= HI, "[WINDOW] reserved slice read"
    d_all = pd.read_csv(D506B.FIX)
    import json
    meta = json.loads(D506B.META.read_text(encoding="utf-8"))
    specs = meta["specs"]

    print(f"THE VOLUME GATE: LEVEL (D506) vs CHANGE (the principal's), same night-volume input")
    print(f"statistic = p(gated) - p(rest) in points. D506's published accuracy term: -2.09\n")
    print(f"  {'root':<5}{'signal':<8}{'gate':<8}{'n gated':>9}{'n rest':>8}{'acc pts':>10}"
          f"{'null p95':>10}{'share>=':>9}")
    rows = []
    for r in ROOTS:
        t = B[B["root"] == r].sort_values("day").reset_index(drop=True)
        t = t[t["same_front"].astype(str).str.lower().isin(("true", "1"))].reset_index(drop=True)
        if len(t) < 400:
            continue
        score, thr, level_mask, rngd, nvol = AF.from_session_table(t)
        level, change = gates(nvol, score, thr)

        day_ret = np.log(t["h15_c"].to_numpy(float) / t["h09_o"].to_numpy(float))
        sig = {}
        sig["drift"] = np.where(np.isfinite(day_ret), 1.0, np.nan)          # long the day session
        try:
            b = D506B.build_root(d_all, r, specs[r]["day_window"])
            A = b["AGREE"]; first = D506B.seg_index(specs[r]["day_window"][0])
            dirn = np.sign(np.nan_to_num(A[:, first], nan=0.0))
            # JOIN BY DAY, never by position: build_root reads the breadth fixture and this table is
            # the sessions fixture, and their session lists are not the same object.
            m_ = pd.Series(dirn, index=np.asarray(b["days"], dtype=str))
            aligned = m_.reindex(t["day"].to_numpy()).to_numpy(float)
            sig["macd"] = np.where((aligned == 0) | ~np.isfinite(aligned), np.nan, aligned)
        except Exception as e:                                             # noqa: BLE001
            print(f"  {r}: MACD signal unavailable ({type(e).__name__}); drift only")
        for sname, s in sig.items():
            hit = np.where(np.isfinite(s) & np.isfinite(day_ret), (np.sign(day_ret) == np.sign(s)).astype(float), np.nan)
            for gname, gmask in (("level", level), ("change", change)):
                res = acc_term(hit, gmask, rng)
                if res is None:
                    continue
                rows.append(dict(root=r, signal=sname, gate=gname, **res))
                print(f"  {r:<5}{sname:<8}{gname:<8}{res['n_gated']:>9,}{res['n_rest']:>8,}"
                      f"{res['obs']:>+10.2f}{res['p95']:>+10.2f}{100*res['share_ge']:>8.1f}%")
    D = pd.DataFrame(rows)
    print("\n" + "=" * 86)
    for g, x in D.groupby("gate"):
        pos = int((x["obs"] > 0).sum())
        clears = int((x["obs"] > x["p95"]).sum())
        print(f"  {g.upper():<7} mean accuracy term {x['obs'].mean():+.2f} points   "
              f"positive in {pos} of {len(x)}   clears its own null in {clears} of {len(x)}")
    lv = D[D.gate == "level"]["obs"].mean(); ch = D[D.gate == "change"]["obs"].mean()
    print(f"\n  D506 published the LEVEL gate's accuracy term as -2.09 points; here it reads {lv:+.2f}")
    print(f"  the CHANGE gate reads {ch:+.2f} -- a difference of {ch-lv:+.2f} points of hit rate")
    print("=" * 86)
    D.to_csv(REPO / "working" / "chase_volume_gate_level_vs_change.csv", index=False)


if __name__ == "__main__":
    main()
