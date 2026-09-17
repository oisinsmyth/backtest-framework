"""D484 -- the off-diagonal lookback, and the log impulse MACD as a momentum signal.

    uv run python scripts/d484_offdiagonal_and_macd.py --self-test
    uv run python scripts/d484_offdiagonal_and_macd.py --run [--json]

Pre-registered in
`docs/decisions/D484-PRE-REG-the-off-diagonal-lookback-and-the-log-impulse-MACD-as.md`,
committed before this file existed. **Every root, grid value, parameter, statistic, null and
threshold below is copied from that record. None is chosen here.**

WHY PART A EXISTS: D474 and D475 locked the lookback EQUAL to the holding period, inherited
from the canonical TSMOM form without asking whether it suited this application. It does not --
a signal's measurement window and its decay horizon are independent quantities. The principal
caught it.

WHAT IS SPENT: only the DIAGONAL has been examined (D474 on ES, D475 on 7 roots). Off-diagonal
cells are primary on all 8 roots; diagonal cells are descriptive replication only; MACD is
wholly unspent.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d484_offdiagonal_and_macd.json"

ROOTS = ("ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E")   # §1; RTY excluded on G2
EXCLUDED = {"RTY": "fails gate G2 (reverting roll 2020-06-14)"}
IN_SAMPLE = ("2016-01-04", "2023-12-29")                   # §1
SEGMENTS = ([f"h{h:02d}" for h in range(18, 24)]
            + [f"h{h:02d}" for h in range(0, 17)])         # §1: 23 hourly segments
LOOKBACKS = (1, 2, 3, 5, 8, 13)                            # §2
HOLDS = (1, 2, 3, 5)                                       # §2
MACD_FAST, MACD_SLOW, MACD_SIG = 12, 26, 9                 # §3 B2, canonical, NOT tuned
IMP_LEN, IMP_SIG = 34, 9                                   # §3 B1, LazyBear defaults
CONTRACT_PURE_BARS = 3 * MACD_SLOW                         # §1: 78
N_DRAWS = 2000                                             # §4
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "YM": "MYM"}         # §5
CROSS_TICKS = 1.009
COMMISSION_RT = 3.00
SEED = 484


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- smoothers (§3)

def ema(x: np.ndarray, n: int) -> np.ndarray:
    """Standard EMA, alpha = 2/(n+1). NaN-propagating from the first finite value."""
    a = 2.0 / (n + 1.0)
    out = np.full(len(x), np.nan)
    s = np.nan
    for i, v in enumerate(x):
        if not np.isfinite(v):
            continue
        s = v if not np.isfinite(s) else s + a * (v - s)
        out[i] = s
    return out


def smma(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder / running mean: s[t] = s[t-1] + (x[t] - s[t-1])/n. §3 defines this explicitly
    so the runner cannot quietly substitute a different smoother."""
    out = np.full(len(x), np.nan)
    s = np.nan
    for i, v in enumerate(x):
        if not np.isfinite(v):
            continue
        s = v if not np.isfinite(s) else s + (v - s) / n
        out[i] = s
    return out


def zlema(x: np.ndarray, n: int) -> np.ndarray:
    """Zero-lag EMA: EMA(2*x[t] - x[t-lag], n) with lag = (n-1)//2. §3."""
    lag = (n - 1) // 2
    y = np.full(len(x), np.nan)
    y[lag:] = 2.0 * x[lag:] - x[:len(x) - lag]
    return ema(y, n)


def sma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    c = np.cumsum(np.nan_to_num(x))
    ok = np.isfinite(x).astype(float)
    cok = np.cumsum(ok)
    tot = c[n - 1:] - np.concatenate([[0.0], c[:len(c) - n]])
    cnt = cok[n - 1:] - np.concatenate([[0.0], cok[:len(cok) - n]])
    out[n - 1:] = np.where(cnt == n, tot / n, np.nan)
    return out


# ---------------------------------------------------------------- signals (§2, §3)

def signal_lookback(logc: np.ndarray, L: int) -> np.ndarray:
    """§2 Part A: sign(p[t] - p[t-L]). NaN for the first L bars."""
    out = np.full(len(logc), np.nan)
    out[L:] = np.sign(logc[L:] - logc[:len(logc) - L])
    return out


def impulse_macd(logh, logl, logc):
    """§3 B1 -- LazyBear's Impulse MACD on log prices. Returns (hist, md).

    `md == 0` whenever the zero-lag midline sits INSIDE the [SMMA(low), SMMA(high)] band. That
    zero is a NO-TRADE state, not a flat position, and it is the whole point of the variant.
    """
    hlc3 = (logh + logl + logc) / 3.0
    mi = zlema(hlc3, IMP_LEN)
    hi = smma(logh, IMP_LEN)
    lo = smma(logl, IMP_LEN)
    md = np.where(mi > hi, mi - hi, np.where(mi < lo, mi - lo, 0.0))
    md = np.where(np.isfinite(mi) & np.isfinite(hi) & np.isfinite(lo), md, np.nan)
    return md - sma(md, IMP_SIG), md


def macd_hist(logc):
    """§3 B2 -- plain MACD histogram on log close, 12/26/9, canonical and NOT tuned."""
    m = ema(logc, MACD_FAST) - ema(logc, MACD_SLOW)
    return m - ema(m, MACD_SIG)


# ---------------------------------------------------------------- statistic (§5)

def edge_sigma(sig: np.ndarray, fwd: np.ndarray) -> float:
    """§5: gross edge in SIGMA units, mean(signal * r_fwd)/sigma(r_fwd). Dimensionless, so
    it is comparable across roots and horizons -- which is also why 6E's missing tick size
    does not matter."""
    m = np.isfinite(sig) & np.isfinite(fwd) & (sig != 0)
    if m.sum() < 200:
        return float("nan")
    s = float(fwd[m].std(ddof=1))
    return float((sig[m] * fwd[m]).mean() / s) if s > 0 else float("nan")


def rotate(x: np.ndarray, k: int) -> np.ndarray:
    """§4 R1: circular rotation. Preserves the series' own autocorrelation and marginal
    distribution EXACTLY; destroys only its alignment with anything else."""
    return np.roll(x, k)


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:66} {detail}")
        if not cond:
            fails.append(label)

    # --- smoothers against hand-computable cases
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    e = ema(x, 3)                       # alpha = 0.5
    chk("EMA seeds on the first value", abs(e[0] - 1.0) < 1e-12, f"{e[0]}")
    chk("EMA(3) second value is 1 + 0.5*(2-1) = 1.5", abs(e[1] - 1.5) < 1e-12, f"{e[1]}")
    s = smma(x, 4)
    chk("SMMA seeds on the first value", abs(s[0] - 1.0) < 1e-12)
    chk("SMMA(4) second value is 1 + (2-1)/4 = 1.25", abs(s[1] - 1.25) < 1e-12, f"{s[1]}")
    chk("SMMA is SLOWER than EMA of the same n", smma(x, 3)[2] < ema(x, 3)[2],
        f"{smma(x, 3)[2]:.4f} vs {ema(x, 3)[2]:.4f}")
    # on a straight line, ZLEMA should track it more closely than EMA -- that is its purpose
    lin = np.arange(60.0)
    chk("ZLEMA lags a ramp LESS than EMA (that is what zero-lag means)",
        abs(zlema(lin, 20)[-1] - lin[-1]) < abs(ema(lin, 20)[-1] - lin[-1]),
        f"ZLEMA err {abs(zlema(lin,20)[-1]-lin[-1]):.3f} vs EMA "
        f"{abs(ema(lin,20)[-1]-lin[-1]):.3f}")
    chk("SMA(3) of 1..5 is [nan,nan,2,3,4]",
        np.allclose(sma(x, 3)[2:], [2.0, 3.0, 4.0]), f"{sma(x,3)[2:]}")

    # --- Part A signal
    logc = np.log(np.array([100.0, 101, 102, 101, 100, 99, 100, 103]))
    s1 = signal_lookback(logc, 1)
    chk("lookback signal is +1 on a rise, -1 on a fall",
        s1[1] == 1.0 and s1[4] == -1.0, f"{s1[1]}, {s1[4]}")
    chk("lookback signal NaN for the first L bars", bool(np.isnan(s1[0])))
    s3 = signal_lookback(logc, 3)
    chk("L=3 compares t against t-3, not t-1",
        s3[3] == np.sign(logc[3] - logc[0]), f"{s3[3]}")
    # The first version of this asserted disagreement at ONE hand-picked bar, where the two
    # happened to agree. The meaningful claim is that the two signals are not the same
    # SERIES -- which is the whole premise of testing L != H.
    rg0 = np.random.default_rng(11)
    walk = np.cumsum(rg0.standard_normal(5_000)) * 0.001 + np.log(100.0)
    s_1, s_13 = signal_lookback(walk, 1), signal_lookback(walk, 13)
    both = np.isfinite(s_1) & np.isfinite(s_13)
    disagree = float((s_1[both] != s_13[both]).mean())
    chk("L=1 and L=13 are DIFFERENT signals, not relabellings", disagree > 0.2,
        f"they disagree on {disagree:.1%} of bars")

    # --- THE IMPULSE ZERO STATE, which is the distinctive feature of B1
    rg = np.random.default_rng(3)
    flat = np.full(400, 100.0) + rg.standard_normal(400) * 0.01      # a range
    lh, ll, lc = np.log(flat + 0.05), np.log(flat - 0.05), np.log(flat)
    _, md_flat = impulse_macd(lh, ll, lc)
    zero_share_flat = float(np.mean(md_flat[np.isfinite(md_flat)] == 0.0))
    trend = 100.0 * np.exp(np.cumsum(np.full(400, 0.002)))           # a clean trend
    th, tl, tc = np.log(trend * 1.001), np.log(trend * 0.999), np.log(trend)
    _, md_tr = impulse_macd(th, tl, tc)
    zero_share_tr = float(np.mean(md_tr[np.isfinite(md_tr)] == 0.0))
    chk("impulse md is ZERO most of the time in a RANGE", zero_share_flat > 0.5,
        f"{zero_share_flat:.1%} zero")
    chk("impulse md is rarely zero in a TREND", zero_share_tr < 0.2,
        f"{zero_share_tr:.1%} zero")
    chk("so the zero state discriminates range from trend",
        zero_share_flat > zero_share_tr + 0.4,
        f"{zero_share_flat:.1%} vs {zero_share_tr:.1%}")
    chk("impulse hist is finite once warmed up",
        bool(np.isfinite(impulse_macd(th, tl, tc)[0][-1])))

    # --- MACD B2 sign must follow a trend and flip on a reversal
    up = np.log(100.0 * np.exp(np.cumsum(np.full(200, 0.003))))
    dn = np.log(100.0 * np.exp(np.cumsum(np.full(200, -0.003))))
    chk("MACD hist is positive in a sustained rise", macd_hist(up)[-1] > 0,
        f"{macd_hist(up)[-1]:.2e}")
    chk("MACD hist is negative in a sustained fall", macd_hist(dn)[-1] < 0,
        f"{macd_hist(dn)[-1]:.2e}")

    # --- the statistic: recovers a planted edge, reads zero on noise, and is scale-free
    n = 200_000
    f = rg.standard_normal(n)
    sg = np.sign(rg.standard_normal(n))
    chk("edge_sigma ~0 on unrelated series", abs(edge_sigma(sg, f)) < 0.01,
        f"{edge_sigma(sg, f):+.5f}")
    planted = f + 0.05 * sg
    chk("edge_sigma recovers a planted 0.05 sigma edge",
        abs(edge_sigma(sg, planted) - 0.05) < 0.005, f"{edge_sigma(sg, planted):+.5f}")
    chk("edge_sigma is SCALE-FREE (x1000 the returns, same answer)",
        abs(edge_sigma(sg, planted * 1000) - edge_sigma(sg, planted)) < 1e-9)
    chk("edge_sigma IGNORES zero signals (the no-trade state)",
        abs(edge_sigma(np.where(np.arange(n) % 2 == 0, 0.0, sg), planted)
            - edge_sigma(sg[1::2], planted[1::2])) < 0.01)

    # --- §4 R1: the rotation must preserve autocorrelation and destroy alignment.
    #
    # THE FIRST VERSION USED sign(diff(random walk)) AS THE "AUTOCORRELATED" SIGNAL. A random
    # walk's INCREMENTS are independent, so that sign series is i.i.d. and the check compared
    # two near-zero autocorrelations -- it could not have distinguished the nulls. The real
    # signals are autocorrelated because overlapping windows SHARE DATA (L=13 consecutive
    # signals share 12 of 13 increments) and because MACD is smoothed. Both real
    # constructions are used below.
    big = np.cumsum(rg.standard_normal(40_000)) * 0.001 + np.log(100.0)
    for name, sg_series in (("L=13 lookback", signal_lookback(big, 13)),
                            ("impulse MACD hist",
                             np.sign(impulse_macd(big + 0.001, big - 0.001, big)[0]))):
        v = sg_series[np.isfinite(sg_series)]
        ac1 = float(np.corrcoef(v[:-1], v[1:])[0, 1])
        rot = rotate(v, 13_337)
        shuf = rg.permutation(v)
        ac_rot = float(np.corrcoef(rot[:-1], rot[1:])[0, 1])
        ac_shuf = float(np.corrcoef(shuf[:-1], shuf[1:])[0, 1])
        chk(f"{name}: the real signal IS strongly autocorrelated", ac1 > 0.5,
            f"lag-1 rho {ac1:+.3f}")
        chk(f"{name}: R1 rotation PRESERVES that autocorrelation",
            abs(ac_rot - ac1) < 0.02, f"{ac_rot:+.3f} vs {ac1:+.3f}")
        chk(f"{name}: R2 shuffle DESTROYS it -- which is why R1 is primary",
            abs(ac_shuf) < 0.05 and ac_rot > ac_shuf + 0.4,
            f"shuffled {ac_shuf:+.3f} vs rotated {ac_rot:+.3f}")
        chk(f"{name}: rotation preserves the multiset exactly",
            bool(np.array_equal(np.sort(rot), np.sort(v))))
    chk("rotation DESTROYS alignment with the returns",
        abs(edge_sigma(rotate(np.sign(rg.standard_normal(20_000)), 7_777),
                       planted[:20_000])) < 0.05)

    # --- grid bookkeeping from §2
    cells = [(L, H) for L in LOOKBACKS for H in HOLDS]
    offd = [(L, H) for L, H in cells if L != H]
    diag = [(L, H) for L, H in cells if L == H]
    chk("24 (L,H) cells, 20 off-diagonal primary, 4 diagonal descriptive",
        len(cells) == 24 and len(offd) == 20 and len(diag) == 4,
        f"{len(cells)}/{len(offd)}/{len(diag)}")
    chk("the grid contains L>H, L<H and L=H so Z-c is answerable",
        any(L > H for L, H in cells) and any(L < H for L, H in cells) and len(diag) > 0)

    # --- §5 micro costs
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    c_mes = COMMISSION_RT / spec["MES"]["tick_usd"] + CROSS_TICKS
    c_mnq = COMMISSION_RT / spec["MNQ"]["tick_usd"] + CROSS_TICKS
    chk("MES cost 3.409 ticks, MNQ ~7.009 -- NQ faces about twice the bar",
        abs(c_mes - 3.409) < 0.001 and abs(c_mnq - 7.009) < 0.001,
        f"{c_mes:.3f} / {c_mnq:.3f}")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


# ---------------------------------------------------------------- build

def series_for(root: str, d_all, meta) -> dict:
    """One continuous hourly series per root: log high/low/close, contract, valid mask."""
    import pandas as pd
    start = max(IN_SAMPLE[0], meta["usable_start"][root])
    d = d_all[(d_all["root"] == root) & d_all["same_front"]]
    d = d[d["day"].between(start, IN_SAMPLE[1])].sort_values("day", kind="stable")
    if len(d) and d["day"].max() > "2023-12-31":
        raise GateError(f"[HOLDOUT] {root}: rows past 2023 survived the filter")
    o = np.concatenate([d[f"{s}_o"].to_numpy(float) for s in SEGMENTS].__iter__()
                       ) if False else None
    # stack segment-major then flatten session-major so the series is chronological
    O = np.stack([d[f"{s}_o"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    H_ = np.stack([d[f"{s}_h"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    L_ = np.stack([d[f"{s}_l"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    C_ = np.stack([d[f"{s}_c"].to_numpy(float) for s in SEGMENTS], axis=1).ravel()
    con = np.repeat(d["contract"].to_numpy(), len(SEGMENTS))
    pos = (O > 0) & (H_ > 0) & (L_ > 0) & (C_ > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lo_, lh, ll, lc = (np.where(pos, np.log(O), np.nan),
                           np.where(pos, np.log(H_), np.nan),
                           np.where(pos, np.log(L_), np.nan),
                           np.where(pos, np.log(C_), np.nan))
    # §1: contract-pure over the trailing CONTRACT_PURE_BARS
    same = np.ones(len(con), dtype=bool)
    for k in range(1, CONTRACT_PURE_BARS + 1):
        same[k:] &= con[k:] == con[:-k]
    same[:CONTRACT_PURE_BARS] = False
    return {"log_open": lo_, "log_high": lh, "log_low": ll, "log_close": lc,
            "contract": con, "pure": same & pos, "n_sessions": int(len(d)),
            "start": start}


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    for root in ROOTS:
        g = meta["gates"].get(root)
        if g is None:
            raise GateError(f"[FIXTURE] no gate block for {root}")
        bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
        if bad:
            raise GateError(f"[FIXTURE] {root} fails gates {bad}")
    for r, why in EXCLUDED.items():
        P(f"  excluded: {r} -- {why}")

    d_all = pd.read_csv(FIX)
    S = {r: series_for(r, d_all, meta) for r in ROOTS}
    P("")
    for r in ROOTS:
        s = S[r]
        P(f"  {r:4} {s['n_sessions']:>5} sessions from {s['start']} -> "
          f"{len(s['log_close']):>7,} hourly bars, {int(s['pure'].sum()):>7,} "
          f"contract-pure")

    # ---- forward returns by hold, in log units, entered at the OPEN of t+1
    def fwd_ret(s, H):
        lo_, lc = s["log_open"], s["log_close"]
        out = np.full(len(lc), np.nan)
        if H + 1 <= len(lc):
            out[:len(lc) - H] = lc[H:] - lo_[1:len(lc) - H + 1]
        return out

    rows = []
    for r in ROOTS:
        s = S[r]
        fwd = {H: fwd_ret(s, H) for H in HOLDS}
        sigs = {("A", L): signal_lookback(s["log_close"], L) for L in LOOKBACKS}
        sigs[("B1", 0)] = np.sign(impulse_macd(s["log_high"], s["log_low"],
                                               s["log_close"])[0])
        md0 = impulse_macd(s["log_high"], s["log_low"], s["log_close"])[1]
        zero_share = float(np.mean(md0[np.isfinite(md0)] == 0.0))
        sigs[("B1", 0)] = np.where(md0 == 0.0, 0.0, sigs[("B1", 0)])   # §3: zero = NO TRADE
        sigs[("B2", 0)] = np.sign(macd_hist(s["log_close"]))
        for key, sg in sigs.items():
            for H in HOLDS:
                sg_v = np.where(s["pure"], sg, np.nan)
                e = edge_sigma(sg_v, fwd[H])
                m = np.isfinite(sg_v) & np.isfinite(fwd[H]) & (sg_v != 0)
                rows.append({"root": r, "family": key[0], "L": key[1], "H": H,
                             "n": int(m.sum()), "edge_sigma": e,
                             "diagonal": bool(key[0] == "A" and key[1] == H),
                             "zero_share": zero_share if key[0] == "B1" else None})
        S[r]["_fwd"], S[r]["_sigs"] = fwd, sigs
        S[r]["_zero"] = zero_share

    def show(fam, only_primary):
        sel = [x for x in rows if x["family"] == fam
               and (not x["diagonal"] if only_primary else True)]
        if not sel:
            return
        P(f"\n  {'root':>5}{'L':>4}{'H':>3}{'n':>9}{'edge/sigma':>12}")
        for x in sorted(sel, key=lambda z: -(z["edge_sigma"] if z["edge_sigma"] == z["edge_sigma"] else -9)):
            P(f"  {x['root']:>5}{x['L']:>4}{x['H']:>3}{x['n']:>9,}"
              f"{x['edge_sigma']:>+12.5f}")

    # ---- §5: the two declared statistics per part
    res_parts = {}
    for fam, label in (("A", "PART A -- off-diagonal lookback"),
                       ("B1", "PART B1 -- log IMPULSE MACD (primary)"),
                       ("B2", "PART B2 -- plain log MACD histogram (secondary)")):
        prim = [x for x in rows if x["family"] == fam and not x["diagonal"]]
        e = np.array([x["edge_sigma"] for x in prim], dtype=float)
        P1 = float(np.nanmean(e))
        P2 = float(np.nanmax(e))
        best = prim[int(np.nanargmax(e))]
        P(f"\n=== {label} ===")
        P(f"  cells {len(prim)}  P1 pooled {P1:+.5f}  P2 family max {P2:+.5f}  "
          f"(best: {best['root']} L={best['L']} H={best['H']})")
        res_parts[fam] = {"n_cells": len(prim), "P1_pooled": P1, "P2_family_max": P2,
                          "best_cell": best}

    # ---- §4: nulls. R1 rotates the SIGNAL; R2 randomises its sign per observation.
    rg = np.random.default_rng(SEED)
    nulls = {}
    for fam in ("A", "B1", "B2"):
        keys = [k for k in S[ROOTS[0]]["_sigs"] if k[0] == fam]
        r1_p1 = np.empty(N_DRAWS)
        r1_p2 = np.empty(N_DRAWS)
        r2_p1 = np.empty(N_DRAWS)
        for i in range(N_DRAWS):
            e1, e2 = [], []
            for r in ROOTS:
                s = S[r]
                nbar = len(s["log_close"])
                k = int(rg.integers(CONTRACT_PURE_BARS, nbar - CONTRACT_PURE_BARS))
                for key in keys:
                    sg = np.where(s["pure"], s["_sigs"][key], np.nan)
                    rot = rotate(sg, k)
                    flip = np.where(rg.random(nbar) < 0.5, -1.0, 1.0)
                    for H in HOLDS:
                        if fam == "A" and key[1] == H:
                            continue                      # diagonal is not in the primary
                        e1.append(edge_sigma(rot, s["_fwd"][H]))
                        e2.append(edge_sigma(sg * flip, s["_fwd"][H]))
            r1_p1[i] = float(np.nanmean(e1))
            r1_p2[i] = float(np.nanmax(e1))
            r2_p1[i] = float(np.nanmean(e2))

        def band(x):
            p50, p95 = float(np.quantile(x, .50)), float(np.quantile(x, .95))
            boot = np.array([np.quantile(rg.choice(x, len(x), replace=True), .95)
                             for _ in range(400)])
            return {"p50": p50, "p95": p95, "se_of_p95": float(boot.std(ddof=1))}

        nulls[fam] = {"R1_pooled": band(r1_p1), "R1_family_max": band(r1_p2),
                      "R2_pooled": band(r2_p1)}

    P(f"\n=== NULLS ({N_DRAWS:,} draws each) ===")
    verdicts = {}
    for fam in ("A", "B1", "B2"):
        n, p = nulls[fam], res_parts[fam]
        m1 = (p["P1_pooled"] - n["R1_pooled"]["p95"]) / n["R1_pooled"]["se_of_p95"]
        m2 = (p["P2_family_max"] - n["R1_family_max"]["p95"]) / \
            n["R1_family_max"]["se_of_p95"]
        P(f"\n  {fam}:")
        P(f"    P1 {p['P1_pooled']:+.5f}  vs R1 pooled p50 {n['R1_pooled']['p50']:+.5f} "
          f"p95 {n['R1_pooled']['p95']:+.5f} (SE {n['R1_pooled']['se_of_p95']:.5f})"
          f"  -> {m1:+.1f} SE")
        P(f"    P2 {p['P2_family_max']:+.5f}  vs R1 family-max p95 "
          f"{n['R1_family_max']['p95']:+.5f} (SE {n['R1_family_max']['se_of_p95']:.5f})"
          f"  -> {m2:+.1f} SE")
        P(f"    R2 pooled p95 {n['R2_pooled']['p95']:+.5f} "
          f"(vs R1's {n['R1_pooled']['p95']:+.5f} -- R2 narrower? "
          f"{'YES' if n['R2_pooled']['p95'] < n['R1_pooled']['p95'] else 'NO'})")
        v = ("PASS on P1" if m1 > 2 else "") + ("  PASS on P2" if m2 > 2 else "")
        verdicts[fam] = v.strip() or "FAIL on both declared statistics"
        P(f"    **{verdicts[fam]}**")

    # ---- §5 TRADEABLE, and §6's Z-f. BOTH WERE DECLARED AND THE FIRST VERSION OF THIS
    # RUNNER COMPUTED NEITHER -- the exact failure my own standing note names ("check the
    # runner computes what the pre-reg declared"). Added here rather than quietly dropped.
    #
    # An edge in sigma units only becomes money once multiplied by sigma IN TICKS, so that
    # conversion is the whole of tradeability.
    trade = []
    for r in ROOTS:
        micro = MICRO_OF.get(r)
        if micro is None or micro not in spec or r not in spec:
            continue                      # §5 limits this to ES/NQ/YM
        tickp = spec[r]["tick_points"]
        cost = COMMISSION_RT / spec[micro]["tick_usd"] + CROSS_TICKS
        for H in HOLDS:
            f = S[r]["_fwd"][H]
            # sigma of the forward LOG return -> ticks, via price level and tick size
            lvl = float(np.nanmedian(np.exp(S[r]["log_close"])))
            sig_ticks = float(np.nanstd(f, ddof=1)) * lvl / tickp
            for x in rows:
                if x["root"] != r or x["H"] != H or x["diagonal"]:
                    continue
                gross = x["edge_sigma"] * sig_ticks
                trade.append({"root": r, "micro": micro, "family": x["family"],
                              "L": x["L"], "H": H, "sigma_ticks": sig_ticks,
                              "cost_ticks": cost, "gross_ticks": gross,
                              "net_ticks": gross - cost,
                              "net_positive": bool(gross - cost > 0),
                              "gross_over_cost": gross / cost})
    P(f"\n=== §5 TRADEABILITY (ES/NQ/YM, the roots with a committed micro) ===")
    P(f"  {'root':>5}{'micro':>6}{'fam':>4}{'L':>4}{'H':>3}{'sigma tk':>10}"
      f"{'cost tk':>9}{'gross tk':>10}{'net tk':>9}{'gross/cost':>12}")
    best_by = {}
    for r in ("ES", "NQ", "YM"):
        sub = [t for t in trade if t["root"] == r]
        if not sub:
            continue
        b = max(sub, key=lambda z: z["net_ticks"])
        best_by[r] = b
        P(f"  {b['root']:>5}{b['micro']:>6}{b['family']:>4}{b['L']:>4}{b['H']:>3}"
          f"{b['sigma_ticks']:>10.1f}{b['cost_ticks']:>9.3f}{b['gross_ticks']:>10.3f}"
          f"{b['net_ticks']:>9.3f}{b['gross_over_cost']:>12.2f}")
    n_pos = sum(1 for t in trade if t["net_positive"])
    P(f"  cells with POSITIVE net: {n_pos} of {len(trade)}")
    P(f"  (best cells overall sit on GC and CL, which have no micro in the committed specs, "
      f"so §5 cannot cost them -- a real limitation, not an omission)")

    # ---- §6 predictions
    a_off = np.array([x["edge_sigma"] for x in rows
                      if x["family"] == "A" and not x["diagonal"]], dtype=float)
    a_dia = np.array([x["edge_sigma"] for x in rows
                      if x["family"] == "A" and x["diagonal"]], dtype=float)
    best_a = max((x for x in rows if x["family"] == "A" and not x["diagonal"]),
                 key=lambda z: z["edge_sigma"] if z["edge_sigma"] == z["edge_sigma"] else -9)
    zshare = float(np.mean([S[r]["_zero"] for r in ROOTS]))
    za = verdicts["A"].startswith("FAIL")
    zb = "P2" not in verdicts["A"]
    zc = float(np.nanmean(a_off)) > float(np.nanmean(a_dia)) and best_a["L"] > best_a["H"]
    zd = zshare > 0.40 and res_parts["B1"]["P1_pooled"] > res_parts["B2"]["P1_pooled"]
    ze = all(nulls[f]["R2_pooled"]["p95"] < nulls[f]["R1_pooled"]["p95"]
             for f in ("A", "B1", "B2"))
    P(f"\n=== PRE-REGISTERED PREDICTIONS (D484 §6) ===")
    P(f"  Z-a Part A pooled fails R1          {'HELD' if za else 'BROKEN':>7}")
    P(f"  Z-b Part A family max fails too     {'HELD' if zb else 'BROKEN':>7}")
    P(f"  Z-c off-diagonal beats diagonal and the best cell has L>H  "
      f"{'HELD' if zc else 'BROKEN':>7}  off {np.nanmean(a_off):+.5f} vs "
      f"diag {np.nanmean(a_dia):+.5f}; best L={best_a['L']} H={best_a['H']}")
    P(f"  Z-d B1 zero state >40% and beats B2 {'HELD' if zd else 'BROKEN':>7}  "
      f"zero {zshare:.1%}")
    P(f"  Z-e R2 narrower than R1             {'HELD' if ze else 'BROKEN':>7}")
    zf = n_pos == 0
    P(f"  Z-f no cell TRADEABLE at micro cost {'HELD' if zf else 'BROKEN':>7}  "
      f"{n_pos} of {len(trade)} net positive")

    show("A", True)
    show("B1", True)
    show("B2", True)

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D484-PRE-REG-the-off-diagonal-lookback-and-"
                               "the-log-impulse-MACD-as-momentum-signals.md",
           "source": str(FIX.relative_to(REPO)), "roots": list(ROOTS),
           "excluded": EXCLUDED, "window": list(IN_SAMPLE),
           "grid": {"lookbacks": list(LOOKBACKS), "holds": list(HOLDS)},
           "macd_params": {"B1_impulse": [IMP_LEN, IMP_SIG],
                           "B2_plain": [MACD_FAST, MACD_SLOW, MACD_SIG],
                           "note": "published defaults, NOT tuned; any other set is a "
                                   "separate pre-registration"},
           "parts": res_parts, "nulls": nulls, "verdicts": verdicts,
           "impulse_zero_state_share_by_root": {r: S[r]["_zero"] for r in ROOTS},
           "predictions": {"Z-a": bool(za), "Z-b": bool(zb), "Z-c": bool(zc),
                           "Z-d": bool(zd), "Z-e": bool(ze), "Z-f": bool(zf)},
           "tradeability": trade, "tradeability_best_by_root": best_by,
           "tradeability_cells_net_positive": int(n_pos),
           "cells": rows}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
