"""D675 Stage 1 -- D484's log MACD edge decomposed exactly (design: docs/decisions/D675-STAGE-1-DESIGN-...).

    uv run python scripts/d675_macd_kernel_decomposition.py --selftest
    uv run python scripts/d675_macd_kernel_decomposition.py --run --data-root "<main checkout>/data"

The 12/26/9 histogram is a linear filter of past log returns along the chain of valid bars:
hist_t = sum_k w_k r_{t-k}, with sum(w) = 0 (+ on lags 0-13, - on 14+). L1 = hist/v splits D484's edge
exactly into lag regions and source buckets (source side) and time subsets (time side). S = sign(hist) is
D484's traded signal; it is reproduced bit for bit (G0) and split on the time side only.

The null is an exact session rotation: the forward return, with its time subset, is rotated against the
component by 23*j bars for every j from 5 to n-5 sessions. The observed value is offset 0 of the same
GEMM over the same doubled array, so observed and null cannot differ by a rounding path.

Reads only D484's window (2016-01-04 -> 2023-12-29). SqueezeMetrics GEX (ES only) is used as a split;
only aggregates are written (docs/research/licences/squeezemetrics-dix-gex.md).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d675_macd_kernel_decomposition.json"
D484_JSON = REPO / "data" / "d484_offdiagonal_and_macd.json"
SPECS = REPO / "data" / "futures_contract_specs.json"

_spec = importlib.util.spec_from_file_location("d484", REPO / "scripts" / "d484_offdiagonal_and_macd.py")
d484 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d484)          # module body defines only; main() is __main__-guarded

ROOTS = d484.ROOTS
HOLDS = d484.HOLDS
NSEG = len(d484.SEGMENTS)               # 23
K = 2000                                # kernel truncation; |w_1999| < 1e-60
V_N = 120                               # §2: v = sqrt(EMA_120(r^2)), declared, not tuned
VS_FAST, VS_SLOW = 23, 230              # §3 vol state
VOL_LOOKBACK, VOL_HIGH = 20, 1.5        # §3 source volume
PURGE_SESSIONS = 5                      # §5
TOL_ID = 1e-10                          # §2 identity, relative

REGIONS = {"CONT": (0, 13), "REV1": (14, 39), "REV2": (40, 78), "TAIL": (79, K - 1), "REV": (14, K - 1)}
SEG_HOURS = [int(s[1:]) for s in d484.SEGMENTS]


def clock_of_hour(h: int) -> str:
    if h >= 18 or h <= 2:
        return "ASIA"
    if 3 <= h <= 8:
        return "EUROPE"
    if h in (9, 10):
        return "US_OPEN"
    if h in (11, 12, 13):
        return "US_MID"
    return "US_CLOSE"


CLOCK_NAMES = ("ASIA", "EUROPE", "US_OPEN", "US_MID", "US_CLOSE")
SEG_CLOCK = np.array([CLOCK_NAMES.index(clock_of_hour(h)) for h in SEG_HOURS])
SIZES = ("SMALL", "MID", "LARGE")
VOLS = ("HIGH", "NORMAL")
SIGNS = ("UP", "DOWN")
SESS = ("SAME", "CROSS")
YEARS = tuple(range(2016, 2024))
VSTATE = ("RISING", "FALLING")
GAMMA = ("SHORT", "LONG")
LIQUID = {"6E": ("EUROPE", "US_OPEN", "US_MID")}
LIQUID_DEFAULT = ("US_OPEN", "US_MID", "US_CLOSE")
FIX_WINDOW = {"ES": "US_CLOSE", "NQ": "US_CLOSE", "YM": "US_CLOSE", "ZN": "US_CLOSE", "ZB": "US_CLOSE",
              "CL": "US_CLOSE", "GC": "US_MID", "6E": "US_MID"}
STRESS_YEARS = (2018, 2020, 2022)


class GateError(AssertionError):
    """An audit refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- the kernel (§2)

def kernel(n: int = K) -> np.ndarray:
    """w_k: the 12/26/9 histogram's weight on r_{t-k}, EMA initialised at the first value."""
    a12, a26, a9 = 2 / 13, 2 / 27, 2 / 10
    j = np.arange(n)
    wm = (1 - a26) ** (j + 1) - (1 - a12) ** (j + 1)
    return wm - np.convolve(a9 * (1 - a9) ** j, wm)[:n]


W = kernel()


def region_kernel(name: str, sq: bool = False) -> np.ndarray:
    lo, hi = REGIONS[name]
    w = np.zeros(K)
    w[lo:hi + 1] = W[lo:hi + 1]
    return w * w if sq else w


def causal_conv(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """z_t = sum_k w_k x_{t-k}, k < len(w). Output t reads x[0..t] only."""
    return np.convolve(x, w)[:len(x)]


def paired_conv(x: np.ndarray, w: np.ndarray, sess: np.ndarray, same: bool) -> np.ndarray:
    """Like causal_conv, keeping only pairs whose source bar is (not) in t's session."""
    z = np.zeros(len(x))
    lo = int(np.flatnonzero(w)[0])
    hi = int(np.flatnonzero(w)[-1])
    for k in range(lo, hi + 1):
        if k == 0:
            if same:
                z += w[0] * x
            continue
        if k >= len(x):
            break
        m = (sess[k:] == sess[:-k]) if same else (sess[k:] != sess[:-k])
        z[k:] += w[k] * (x[:-k] * m)
    return z


# ---------------------------------------------------------------- audits (§8)

def audit_lag(build, r: np.ndarray, t0: int) -> None:
    """The component at t <= t0 must not move when every return after t0 is altered."""
    z0 = build(r)
    r2 = r.copy()
    r2[t0 + 1:] = r2[t0 + 1:] * -3.0 + 0.01
    z1 = build(r2)
    if not np.array_equal(z0[:t0 + 1], z1[:t0 + 1]):
        raise GateError("[LAG] a component at or before t0 moved when later returns changed")


def audit_second_path(r: np.ndarray, z: np.ndarray, ts) -> None:
    """Rebuild z_t from the chain up to t alone, without the convolution."""
    scale = float(np.sqrt(np.mean(z * z))) or 1.0
    for t in ts:
        k = np.arange(min(t + 1, K))
        direct = float(np.dot(W[k], r[t - k]))
        if abs(direct - z[t]) > 1e-11 * scale:
            raise GateError(f"[LAG] second path disagrees at t={t}: {direct} vs {z[t]}")


def audit_sign(contrib) -> None:
    """A positive component paired with a favourable (positive) move must pay positively."""
    z = np.array([1.0, 2.0, 0.5])
    f = np.array([0.01, 0.02, 0.005])
    if not contrib(z, f) > 0 or not contrib(z, -f) < 0:
        raise GateError("[SIGN] a favourable move did not pay positively")


def audit_partition(cells: dict, total: float, label: str) -> None:
    s = float(sum(cells.values()))
    scale = float(sum(abs(v) for v in cells.values())) + abs(total)
    if abs(s - total) > TOL_ID * max(scale, 1e-300):
        raise GateError(f"[IDENTITY] {label}: cells sum {s!r} != total {total!r}")


def audit_right_quantity(lo_next: np.ndarray, lc_now: np.ndarray) -> float:
    """The forward return starts at the open of t+1. It must differ from a close-of-t entry."""
    m = np.isfinite(lo_next) & np.isfinite(lc_now)
    share = float(np.mean(lo_next[m] != lc_now[m]))
    if share == 0.0:
        raise GateError("[RIGHT QUANTITY] open of t+1 equals close of t on every bar")
    return share


def audit_reproduction(cells_now: list, committed: list, p1_now: float, p1_committed: float) -> None:
    key = lambda x: (x["root"], x["H"])
    a = {key(x): x["edge_sigma"] for x in cells_now}
    b = {key(x): x["edge_sigma"] for x in committed}
    if set(a) != set(b):
        raise GateError(f"[G0] cell sets differ: {sorted(set(a) ^ set(b))}")
    bad = [k for k in a if a[k] != b[k]]
    if bad:
        raise GateError(f"[G0] {len(bad)} B2 cells differ from D484's JSON, e.g. {bad[0]}: "
                        f"{a[bad[0]]!r} vs {b[bad[0]]!r}")
    if p1_now != p1_committed:
        raise GateError(f"[G0] P1 pooled {p1_now!r} != committed {p1_committed!r}")


def contrib_sum(z, f):
    return float(np.dot(z, f))


# ---------------------------------------------------------------- data

def load_root(root, d_all, meta, gex):
    """Everything the decomposition needs for one root, on D484's series."""
    import pandas as pd
    s = d484.series_for(root, d_all, meta)
    # the same rows series_for used, for volume, days and years
    start = max(d484.IN_SAMPLE[0], meta["usable_start"][root])
    d = d_all[(d_all["root"] == root) & d_all["same_front"]]
    d = d[d["day"].between(start, d484.IN_SAMPLE[1])].sort_values("day", kind="stable")
    C_ = np.stack([d[f"{g}_c"].to_numpy(float) for g in d484.SEGMENTS], axis=1).ravel()
    fin = np.isfinite(s["log_close"])
    if len(C_) != len(fin) or not np.array_equal(np.log(C_[fin]), s["log_close"][fin]):
        raise GateError(f"[DATA] {root}: rebuilt rows disagree with series_for")
    nsess = len(d)
    V = d[[f"{g}_v" for g in d484.SEGMENTS]].astype(float)
    med = V.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).median().shift(1)
    ratio = (V / med).to_numpy().ravel()
    hi_vol = np.where(np.isfinite(ratio), ratio >= VOL_HIGH, False)
    days = d["day"].to_numpy()
    year = np.repeat(np.array([int(x[:4]) for x in days]), NSEG)
    sess_id = np.repeat(np.arange(nsess), NSEG)
    seg = np.tile(np.arange(NSEG), nsess)
    gam = None
    if gex is not None:
        gd = gex["date"].to_numpy()
        gv = gex["gex"].to_numpy(float)
        pos = np.searchsorted(gd, days, side="left") - 1          # last row strictly before the day
        g_sess = np.where(pos >= 0, gv[np.clip(pos, 0, None)], np.nan)
        gam = np.repeat(g_sess, NSEG)
    return {"s": s, "nsess": nsess, "hi_vol": hi_vol, "year": year, "sess": sess_id, "seg": seg,
            "gamma": gam, "days": days}


def ema_np(x: np.ndarray, n: int) -> np.ndarray:
    return d484.ema(x, n)


# ---------------------------------------------------------------- one root

def decompose_root(root, R, verbose=True):
    t_start = time.perf_counter()
    s = R["s"]
    lc, lo_ = s["log_close"], s["log_open"]
    N = len(lc)
    ok = np.isfinite(lc)
    idx = np.flatnonzero(ok)
    c = lc[ok]
    r = np.diff(c, prepend=c[0])                                  # r_0 = 0: EMA initialised at p_0
    n = len(c)

    hist = d484.macd_hist(lc)                                     # D484's own function
    hist_chain = causal_conv(r, W)
    scale_h = float(np.nanstd(hist))
    id_err = float(np.max(np.abs(hist_chain - hist[ok]))) / scale_h
    if id_err > 1e-9:
        raise GateError(f"[IDENTITY] {root}: kernel sum differs from macd_hist by {id_err:.2e} sd")
    # §8.1 on the real chain: causality of each construction, and a second path that never convolves
    t0 = n // 2
    audit_lag(lambda x: causal_conv(x, region_kernel("CONT")), r, t0)
    audit_lag(lambda x: paired_conv(x, region_kernel("REV"), R["sess"][idx], True), r, t0)
    audit_second_path(r, hist_chain, [14, 79, t0, n - 1] + list(range(1000, n, 7919)))

    v = np.sqrt(ema_np(r * r, V_N))
    v_prev = np.concatenate([[np.nan], v[:-1]])
    with np.errstate(divide="ignore", invalid="ignore"):
        size_z = np.where(v_prev > 0, np.abs(r) / v_prev, np.where(r != 0, np.inf, 0.0))
    size_b = np.where(size_z < 1, 0, np.where(size_z < 2, 1, 2))
    vol_b = np.where(R["hi_vol"][idx], 0, 1)
    sign_b = np.where(r > 0, 0, np.where(r < 0, 1, -1))
    clk_b = SEG_CLOCK[R["seg"][idx]]
    sess_c = R["sess"][idx]
    vs_rise = np.sqrt(ema_np(r * r, VS_FAST)) > np.sqrt(ema_np(r * r, VS_SLOW))

    # ---- source-side components along the chain, divided by v_t
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_v = np.where(v > 0, 1.0 / v, 0.0)
    comps, varc = {}, {}
    comps["L1"] = hist_chain * inv_v
    for reg in ("CONT", "REV1", "REV2", "TAIL", "REV"):
        comps[reg] = causal_conv(r, region_kernel(reg)) * inv_v
        varc[reg] = causal_conv(r * r, region_kernel(reg, sq=True)) * inv_v * inv_v
    for reg in ("CONT", "REV"):
        wk, wk2 = region_kernel(reg), region_kernel(reg, sq=True)
        for i, g in enumerate(CLOCK_NAMES):
            b = (clk_b == i).astype(float)
            comps[f"{reg}|src:{g}"] = causal_conv(r * b, wk) * inv_v
            varc[f"{reg}|src:{g}"] = causal_conv(r * r * b, wk2) * inv_v * inv_v
        for i, g in enumerate(SIZES):
            b = (size_b == i).astype(float)
            comps[f"{reg}|size:{g}"] = causal_conv(r * b, wk) * inv_v
            varc[f"{reg}|size:{g}"] = causal_conv(r * r * b, wk2) * inv_v * inv_v
        for i, g in enumerate(VOLS):
            b = (vol_b == i).astype(float)
            comps[f"{reg}|vol:{g}"] = causal_conv(r * b, wk) * inv_v
            varc[f"{reg}|vol:{g}"] = causal_conv(r * r * b, wk2) * inv_v * inv_v
        for i, g in enumerate(SIGNS):
            b = (sign_b == i).astype(float)
            comps[f"{reg}|sign:{g}"] = causal_conv(r * b, wk) * inv_v
            varc[f"{reg}|sign:{g}"] = causal_conv(r * r * b, wk2) * inv_v * inv_v
        for g, same in (("SAME", True), ("CROSS", False)):
            comps[f"{reg}|sess:{g}"] = paired_conv(r, wk, sess_c, same) * inv_v
            varc[f"{reg}|sess:{g}"] = paired_conv(r * r, wk2, sess_c, same) * inv_v * inv_v

    # series-level identities (before any forward return is touched)
    rms_l1 = float(np.sqrt(np.mean(comps["L1"] ** 2)))
    def series_close(parts, total, label):
        e = float(np.max(np.abs(sum(comps[p] for p in parts) - comps[total]))) / rms_l1
        if e > TOL_ID:
            raise GateError(f"[IDENTITY] {root} {label}: series partition off by {e:.2e} rms")
    series_close(["CONT", "REV1", "REV2", "TAIL"], "L1", "regions")
    series_close(["REV1", "REV2", "TAIL"], "REV", "REV")
    for reg in ("CONT", "REV"):
        for fam, names in (("src", CLOCK_NAMES), ("size", SIZES), ("vol", VOLS), ("sign", SIGNS),
                           ("sess", SESS)):
            series_close([f"{reg}|{fam}:{g}" for g in names], reg, f"{reg} {fam}")

    # ---- map to the uncompressed index, with the signal-side mask
    sigmask = s["pure"] & ok & np.isfinite(hist) & (hist != 0)
    v_unc = np.full(N, np.nan)
    v_unc[idx] = v
    if not np.all(v_unc[sigmask] > 0):
        raise GateError(f"[DATA] {root}: v is not positive on a signal bar")
    names = ["S", "L1", "CONT", "REV1", "REV2", "TAIL", "REV"] + \
        [k for k in comps if "|" in k]
    Z = np.zeros((len(names), N))
    Z[0] = np.where(sigmask, np.sign(np.nan_to_num(hist)), 0.0)
    for i, nm in enumerate(names[1:], start=1):
        row = np.zeros(N)
        row[idx] = comps[nm]
        Z[i] = np.where(sigmask, row, 0.0)
    Vn = [nm for nm in names if nm in varc]
    VZ = np.zeros((len(Vn), N))
    for i, nm in enumerate(Vn):
        row = np.zeros(N)
        row[idx] = varc[nm]
        VZ[i] = np.where(sigmask, row, 0.0)

    # ---- time-side subsets at t
    rise_unc = np.zeros(N, dtype=bool)
    rise_unc[idx] = vs_rise
    nxt_clock = SEG_CLOCK[(R["seg"] + 1) % NSEG]
    subsets = {"ALL": np.ones(N, dtype=bool)}
    for i, g in enumerate(CLOCK_NAMES):
        subsets[f"tgt:{g}"] = nxt_clock == i
    for y in YEARS:
        subsets[f"year:{y}"] = R["year"] == y
    subsets["vs:RISING"] = rise_unc
    subsets["vs:FALLING"] = ~rise_unc
    gamma_na = None
    if R["gamma"] is not None:
        g = R["gamma"]
        subsets["gamma:SHORT"] = np.isfinite(g) & (g < 0)
        subsets["gamma:LONG"] = np.isfinite(g) & (g >= 0)
        gamma_na = int(np.sum(sigmask & ~np.isfinite(g)))
    snames = list(subsets)

    # ---- forward returns (D484's), constants and the target stack
    fwd, consts, T = {}, {}, []
    rq_share = None
    for H in HOLDS:
        f = np.full(N, np.nan)
        f[:N - H] = lc[H:] - lo_[1:N - H + 1]
        fwd[H] = f
        fvalid = np.isfinite(f)
        valid = sigmask & fvalid
        nH = int(valid.sum())
        sd = float(f[valid].std(ddof=1))
        rms = float(np.sqrt(np.mean(Z[1][valid] ** 2)))
        consts[H] = {"N": nH, "sigma": sd, "rms_L1": rms,
                     "N_sub": {k: int((valid & m).sum()) for k, m in subsets.items()}}
        F = np.where(fvalid, f, 0.0)
        for k in snames:
            T.append(F * subsets[k])
        if H == 1:
            lo_next = np.full(N, np.nan)
            lo_next[:-1] = lo_[1:]
            rq_share = audit_right_quantity(lo_next[sigmask], lc[sigmask])
    T = np.array(T)
    M = len(snames)

    # ---- null: every session offset, one GEMM each over a slice of the doubled target array
    T2 = np.concatenate([T, T], axis=1)
    js = [0] + list(range(PURGE_SESSIONS, R["nsess"] - PURGE_SESSIONS + 1))
    raw = np.empty((len(js), len(names), T.shape[0]))
    for a, j in enumerate(js):
        o = NSEG * j
        raw[a] = Z @ T2[:, N - o:2 * N - o].T
    t_null = time.perf_counter()

    # scale: value = raw / (N sigma) [/ rms for the L1-type rows]; then the H-mean
    is_l1 = np.array([nm != "S" for nm in names])
    val = np.empty_like(raw)
    for h, H in enumerate(HOLDS):
        cs = consts[H]
        den = cs["N"] * cs["sigma"]
        sl = slice(h * M, (h + 1) * M)
        val[:, :, sl] = raw[:, :, sl] / den
        val[:, is_l1, sl] /= cs["rms_L1"]
    hmean = val.reshape(len(js), len(names), len(HOLDS), M).mean(axis=2)
    obs_h = val[0].reshape(len(names), len(HOLDS), M)
    obs = hmean[0]
    nul = hmean[1:]

    # variance sums per bucket (H-mean over each hold's valid mask), for intensities
    Vsum = {}
    for i, nm in enumerate(Vn):
        acc = []
        for H in HOLDS:
            valid = sigmask & np.isfinite(fwd[H])
            acc.append(float(VZ[i][valid].sum()) / consts[H]["rms_L1"] ** 2 / consts[H]["N"])
        Vsum[nm] = float(np.mean(acc))

    # ---- identities at the cell level, per hold and on the H-mean
    ni = {nm: i for i, nm in enumerate(names)}
    si = {k: i for i, k in enumerate(snames)}
    for h, H in enumerate(HOLDS):
        o = obs_h[:, h, :]
        A = si["ALL"]
        audit_partition({x: o[ni[x], A] for x in ("CONT", "REV1", "REV2", "TAIL")}, o[ni["L1"], A],
                        f"{root} H={H} regions")
        for reg in ("CONT", "REV"):
            for fam, nm_ in (("src", CLOCK_NAMES), ("size", SIZES), ("vol", VOLS), ("sign", SIGNS),
                             ("sess", SESS)):
                audit_partition({g: o[ni[f"{reg}|{fam}:{g}"], A] for g in nm_}, o[ni[reg], A],
                                f"{root} H={H} {reg} {fam}")
        for row in ("S", "L1", "CONT", "REV"):
            audit_partition({g: o[ni[row], si[f"tgt:{g}"]] for g in CLOCK_NAMES}, o[ni[row], A],
                            f"{root} H={H} {row} target clock")
            audit_partition({y: o[ni[row], si[f"year:{y}"]] for y in YEARS}, o[ni[row], A],
                            f"{root} H={H} {row} years")
            audit_partition({g: o[ni[row], si[f"vs:{g}"]] for g in VSTATE}, o[ni[row], A],
                            f"{root} H={H} {row} vol state")
        # the GEMM's S x ALL cell against D484's own edge_sigma (a rounding-path check only)
        e484 = d484.edge_sigma(np.where(s["pure"], np.sign(hist), np.nan), fwd[H])
        if abs(o[ni["S"], A] - e484) > 1e-12 * max(abs(e484), 1e-300):
            raise GateError(f"[G0] {root} H={H}: GEMM S {o[ni['S'], A]!r} vs edge_sigma {e484!r}")

    # ---- L0, the forward-window roll, B1/B2 agreement, ticks
    e_l0 = {}
    roll = {}
    con = s["contract"]
    for H in HOLDS:
        valid = sigmask & np.isfinite(fwd[H])
        e_l0[H] = float(np.mean(hist[valid] * fwd[H][valid]) / consts[H]["sigma"]
                        / np.sqrt(np.mean(hist[valid] ** 2)))
        cross = np.zeros(N, dtype=bool)
        cross[:N - H] = con[H:] != con[:N - H]
        cr = valid & cross
        roll[H] = {"bars": int(cr.sum()),
                   "L1_contribution": float(np.dot(Z[1][cr], fwd[H][cr]) / consts[H]["N"]
                                            / consts[H]["sigma"] / consts[H]["rms_L1"])}
    b1h, md = d484.impulse_macd(s["log_high"], s["log_low"], lc)
    b1 = np.where(md == 0.0, 0.0, np.sign(b1h))
    both = s["pure"] & np.isfinite(b1) & (b1 != 0) & np.isfinite(hist) & (hist != 0)
    agree = float(np.mean(np.sign(hist[both]) == b1[both]))

    # ---- null summaries
    def band(ci, mi):
        x = nul[:, ci, mi]
        o_ = obs[ci, mi]
        return {"value": float(o_), "p50": float(np.quantile(x, .5)), "p95": float(np.quantile(x, .95)),
                "pct": float(np.mean(x <= o_)), "n_offsets": int(len(x))}

    cells = {}
    for nm in names:
        cells[nm] = {}
        for k in snames:
            b = band(ni[nm], si[k])
            b["per_hold"] = {str(H): float(obs_h[ni[nm], h, si[k]]) for h, H in enumerate(HOLDS)}
            cells[nm][k] = b
    frac_sub = {k: float(np.mean([consts[H]["N_sub"][k] / consts[H]["N"] for H in HOLDS])) for k in snames}

    if verbose:
        P(f"  {root}: {n:,} chain bars, {R['nsess']:,} sessions, {len(js) - 1:,} null offsets, "
          f"identity {id_err:.1e} sd, null {t_null - t_start:.1f}s")
    return {"names": names, "subsets": snames, "cells": cells, "Vsum": Vsum, "frac_sub": frac_sub,
            "consts": {str(H): {k: v for k, v in consts[H].items()} for H in HOLDS},
            "E_L0": {str(H): e_l0[H] for H in HOLDS}, "forward_window_roll": roll,
            "b1_b2_sign_agreement": agree, "right_quantity_share_open_ne_close": rq_share,
            "identity_max_sd": id_err, "gamma_na_signal_bars": gamma_na, "n_chain": n,
            "n_sessions": R["nsess"], "fwd_sigma_log": {str(H): consts[H]["sigma"] for H in HOLDS},
            "median_price": float(np.nanmedian(np.exp(lc)))}


# ---------------------------------------------------------------- reading the fingerprints (§4)

def read_root(root, D):
    c = D["cells"]
    v = lambda row, sub="ALL": c[row][sub]["value"]
    p95 = lambda row: c[row]["ALL"]["p95"]
    fs = D["frac_sub"]
    V = D["Vsum"]
    E = v("L1")
    ES = v("S")
    per_var = lambda row: v(row) / V[row] if V.get(row) else float("nan")
    per_bar = lambda row, sub: v(row, sub) / fs[sub] if fs[sub] > 0 else float("nan")
    out = {"E_S": ES, "E_L1": E, "E_L1_positive": bool(E > 0)}
    # guard
    subs13 = [f"tgt:{g}" for g in CLOCK_NAMES] + [f"year:{y}" for y in YEARS]
    xs = np.array([v("S", k) for k in subs13])
    ys = np.array([v("L1", k) for k in subs13])
    rho = float(np.corrcoef(xs, ys)[0, 1])
    out["G_S1"] = bool(np.sign(ES) == np.sign(E))
    out["G_S2_pearson"] = rho
    out["representative"] = bool(out["G_S1"] and rho >= 0.5)
    share = lambda row: v(row) / E if E != 0 else float("nan")
    out["shares"] = {k: share(k) for k in ("CONT", "REV1", "REV2", "TAIL", "REV")}
    # F1
    f1 = {"a": v("REV") > 0.5 * E and v("REV") > p95("REV"),
          "b": per_var("REV|vol:HIGH") > per_var("REV"),
          "c": per_var("REV|size:LARGE") > per_var("REV"),
          "d": v("REV|sign:UP") > 0 and v("REV|sign:DOWN") > 0}
    # F2
    liq = LIQUID.get(root, LIQUID_DEFAULT)
    liq_c = sum(v("CONT", f"tgt:{g}") for g in liq)
    liq_f = sum(fs[f"tgt:{g}"] for g in liq)
    f2 = {"a": v("CONT") > 0.5 * E and v("CONT") > p95("CONT"),
          "b": per_var("CONT|sess:SAME") > per_var("CONT|sess:CROSS"),
          "c": liq_c / liq_f > v("CONT")}
    # F3
    stress = sum(v("CONT", f"year:{y}") for y in STRESS_YEARS)
    f3 = {"a": v("CONT") > p95("CONT"),
          "b": per_bar("CONT", "vs:RISING") > per_bar("CONT", "vs:FALLING"),
          "c": per_var("CONT|sign:DOWN") > per_var("CONT|sign:UP"),
          "d": v("CONT") > 0 and stress / v("CONT") > 0.5}
    # F4: needs source clock x target clock
    abroad = sum(v(f"CONT|src:{s_}", f"tgt:{t_}") for s_ in ("ASIA", "EUROPE")
                 for t_ in ("US_OPEN", "US_MID", "US_CLOSE"))
    f4 = {"a": v("CONT") > p95("CONT"), "b": v("CONT") > 0 and abroad / v("CONT") > 0.5}
    fp = {"F1": f1, "F2": f2, "F3": f3, "F4": f4}
    if "gamma:SHORT" in c["L1"]:
        fp["F5"] = {"a": per_bar("CONT", "gamma:SHORT") > per_bar("CONT", "gamma:LONG"),
                    "b": per_bar("REV", "gamma:LONG") > per_bar("REV", "gamma:SHORT")}
    win = FIX_WINDOW[root]
    fp["F6"] = {"a": E > 0 and per_bar("L1", f"tgt:{win}") >= 2 * E}
    out["fingerprints"] = {k: {kk: bool(vv) for kk, vv in d.items()} for k, d in fp.items()}
    out["fits"] = {k: all(d.values()) for k, d in fp.items()}
    out["numbers"] = {
        "REV_share": share("REV"), "CONT_share": share("CONT"),
        "REV_p95": p95("REV"), "CONT_p95": p95("CONT"), "REV_pct": c["REV"]["ALL"]["pct"],
        "CONT_pct": c["CONT"]["ALL"]["pct"], "L1_pct": c["L1"]["ALL"]["pct"], "S_pct": c["S"]["ALL"]["pct"],
        "REV_I_HIGH": per_var("REV|vol:HIGH") / per_var("REV") if per_var("REV") else float("nan"),
        "REV_I_LARGE": per_var("REV|size:LARGE") / per_var("REV") if per_var("REV") else float("nan"),
        "REV_UP": v("REV|sign:UP"), "REV_DOWN": v("REV|sign:DOWN"),
        "CONT_same_per_var": per_var("CONT|sess:SAME"), "CONT_cross_per_var": per_var("CONT|sess:CROSS"),
        "CONT_liquid_per_bar": liq_c / liq_f, "CONT_rising_per_bar": per_bar("CONT", "vs:RISING"),
        "CONT_falling_per_bar": per_bar("CONT", "vs:FALLING"),
        "CONT_stress_year_share": stress / v("CONT") if v("CONT") else float("nan"),
        "CONT_abroad_to_us_share": abroad / v("CONT") if v("CONT") else float("nan"),
        "fix_window": win, "fix_per_bar_over_E": per_bar("L1", f"tgt:{win}") / E if E else float("nan"),
    }
    return out


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    rng = np.random.default_rng(675)
    n = 5000
    r = rng.standard_normal(n) * 0.001
    r[0] = 0.0
    sess = np.repeat(np.arange(n // 23 + 1), 23)[:n]

    # kernel shape and the identity against D484's macd_hist on a synthetic chain
    assert np.all(W[:14] > 0) and np.all(W[14:] < 0), "kernel sign structure"
    assert abs(W.sum()) < 1e-12, "kernel sums to zero"
    p = np.cumsum(r) + 4.0
    h = d484.macd_hist(p)
    z = causal_conv(r, W)
    assert np.max(np.abs(z - h)) < 1e-14, "kernel identity"
    P("  kernel: + on 0-13, - on 14+, sum 0; identity with macd_hist holds")

    # lag audit: passes on the real construction, raises on a look-ahead one
    audit_lag(lambda x: causal_conv(x, W), r, 2500)
    audit_lag(lambda x: paired_conv(x, region_kernel("REV"), sess, True), r, 2500)
    try:
        audit_lag(lambda x: np.roll(causal_conv(x, W), -1), r, 2500)
        raise SystemExit("lag audit FAILED to fire on a look-ahead component")
    except GateError:
        pass
    audit_second_path(r, z, [0, 1, 13, 14, 500, 4999])
    try:
        audit_second_path(r, np.roll(z, -1), [500, 1000])
        raise SystemExit("second path FAILED to fire on a shifted component")
    except GateError:
        pass
    P("  lag audit fires on look-ahead; second path fires on a shift")

    # sign audit
    audit_sign(contrib_sum)
    try:
        audit_sign(lambda a, b: -contrib_sum(a, b))
        raise SystemExit("sign audit FAILED to fire on an inverted contribution")
    except GateError:
        pass
    P("  sign audit fires on an inverted sign")

    # partition audit: sessions split exactly; a dropped cell raises
    wr = region_kernel("REV")
    tot = causal_conv(r, wr)
    sm, cr = paired_conv(r, wr, sess, True), paired_conv(r, wr, sess, False)
    assert np.max(np.abs(sm + cr - tot)) < 1e-15, "same + cross = region"
    audit_partition({"a": 1.0, "b": 2.0}, 3.0, "ok")
    try:
        audit_partition({"a": 1.0}, 3.0, "dropped cell")
        raise SystemExit("identity audit FAILED to fire on a dropped cell")
    except GateError:
        pass
    P("  identity audit fires on a dropped cell")

    # right quantity
    lo_next = p[1:] + rng.standard_normal(n - 1) * 1e-4
    audit_right_quantity(lo_next, p[:-1])
    try:
        audit_right_quantity(p[:-1].copy(), p[:-1])
        raise SystemExit("right-quantity audit FAILED to fire on a close-of-t entry")
    except GateError:
        pass
    P("  right-quantity audit fires on a close-of-t entry")

    # reproduction audit on the committed JSON, and on a perturbed copy
    j = json.loads(D484_JSON.read_text(encoding="utf-8"))
    b2 = [x for x in j["cells"] if x["family"] == "B2"]
    audit_reproduction(b2, b2, j["parts"]["B2"]["P1_pooled"], j["parts"]["B2"]["P1_pooled"])
    bad = [dict(x) for x in b2]
    bad[5]["edge_sigma"] = np.nextafter(bad[5]["edge_sigma"], 1.0)
    try:
        audit_reproduction(bad, b2, j["parts"]["B2"]["P1_pooled"], j["parts"]["B2"]["P1_pooled"])
        raise SystemExit("reproduction audit FAILED to fire on a one-ULP change")
    except GateError:
        pass
    P("  reproduction audit fires on a one-ULP change")

    # rotation by slicing the doubled array equals np.roll
    A = rng.standard_normal((3, 46))
    A2 = np.concatenate([A, A], axis=1)
    for o in (0, 23, 46 - 23):
        assert np.array_equal(A2[:, 46 - o:92 - o], np.roll(A, o, axis=1)), "doubled-array rotation"
    P("  doubled-array slice equals np.roll at every tested offset")
    P("SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------- run

def do_run(data_root: Path) -> int:
    import pandas as pd
    t0 = time.perf_counter()
    fix = data_root / "fixtures" / "fut_sessions_hourly.csv.gz"
    meta = json.loads((data_root / "fixtures" / "fut_sessions_hourly.meta.json").read_text(encoding="utf-8"))
    d_all = pd.read_csv(fix)
    gex = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"])
    gex = gex.sort_values("date", kind="stable").reset_index(drop=True)

    # G0: D484's B2 cells, bit for bit, with D484's own functions
    committed = json.loads(D484_JSON.read_text(encoding="utf-8"))
    b2c = [x for x in committed["cells"] if x["family"] == "B2"]
    now = []
    Rs = {}
    for root in ROOTS:
        Rs[root] = load_root(root, d_all, meta, gex if root == "ES" else None)
        s = Rs[root]["s"]
        sg = np.where(s["pure"], np.sign(d484.macd_hist(s["log_close"])), np.nan)
        N = len(s["log_close"])
        for H in HOLDS:
            f = np.full(N, np.nan)
            f[:N - H] = s["log_close"][H:] - s["log_open"][1:N - H + 1]
            now.append({"root": root, "H": H, "edge_sigma": d484.edge_sigma(sg, f)})
    p1 = float(np.nanmean(np.array([x["edge_sigma"] for x in now], dtype=float)))
    audit_reproduction(now, b2c, p1, committed["parts"]["B2"]["P1_pooled"])
    P(f"G0: all {len(now)} B2 cells and P1 pooled ({p1!r}) reproduce D484 bit for bit "
      f"({time.perf_counter() - t0:.1f}s)")

    res, reads = {}, {}
    for root in ROOTS:
        res[root] = decompose_root(root, Rs[root])
        reads[root] = read_root(root, res[root])

    # ---- report
    P("\n=== The edge, per root (mean over H = 1, 2, 3, 5; sigma units) ===")
    P(f"  {'root':>4} {'E_S':>9} {'E_L1':>9} {'rho S,L1':>9} {'repr':>5} {'CONT':>9} {'REV1':>9} "
      f"{'REV2':>9} {'TAIL':>9} {'REV share':>10}")
    for root in ROOTS:
        x, c = reads[root], res[root]["cells"]
        P(f"  {root:>4} {x['E_S']:>+9.5f} {x['E_L1']:>+9.5f} {x['G_S2_pearson']:>9.2f} "
          f"{'yes' if x['representative'] else 'NO':>5} " +
          " ".join(f"{c[k]['ALL']['value']:>+9.5f}" for k in ("CONT", "REV1", "REV2", "TAIL")) +
          f" {x['shares']['REV']:>10.2f}")
    P("\n=== Null (exact session rotation), mean over H: value / p50 / p95 / percentile ===")
    for root in ROOTS:
        c = res[root]["cells"]
        P(f"  {root:>4} " + "  ".join(
            f"{k} {c[k]['ALL']['value']:+.5f}/{c[k]['ALL']['p50']:+.5f}/{c[k]['ALL']['p95']:+.5f}/"
            f"{c[k]['ALL']['pct']:.3f}" for k in ("S", "L1", "CONT", "REV")))
    P("\n=== Fingerprints (a mechanism fits when all its letters hold) ===")
    for root in ROOTS:
        fp = reads[root]["fingerprints"]
        P(f"  {root:>4} " + "  ".join(
            f"{m}:{''.join(k if ok_ else '.' for k, ok_ in d.items())}{'*' if all(d.values()) else ''}"
            for m, d in fp.items()))

    # ---- predictions (§6)
    pr = {}
    pr["1_G0"] = True
    pr["2_identity"] = True          # every audit_partition above raised on failure
    pr["3_L1_represents_S_on_7"] = sum(reads[r]["representative"] for r in ROOTS) >= 7
    pr["4_REV_majority_on_5"] = sum(reads[r]["shares"]["REV"] > 0.5 for r in ROOTS) >= 5
    pr["5_TAIL_under_10pc_everywhere"] = all(
        abs(res[r]["cells"]["TAIL"]["ALL"]["value"]) < 0.1 * abs(reads[r]["E_L1"]) for r in ROOTS)
    f1n = sum(reads[r]["fits"]["F1"] for r in ROOTS)
    f4n = sum(reads[r]["fits"]["F4"] for r in ROOTS)
    pr["6_F1_on_3_and_F4_on_at_most_2"] = f1n >= 3 and f4n <= 2
    P("\n=== Predictions (D675 §6) ===")
    for k, v_ in pr.items():
        P(f"  {k:<34} {'HELD' if v_ else 'BROKEN'}")
    P(f"  (F1 fits {f1n} roots; F4 fits {f4n})")

    # ---- ticks: D484 §2's conversion, S's gross per trade, and the CONT/REV shares of E_L1
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    ticks = {}
    for root in ROOTS:
        if root not in spec or "tick_points" not in spec[root]:
            continue
        tp = spec[root]["tick_points"]
        lvl = res[root]["median_price"]
        per_h = {}
        for H in HOLDS:
            sig_ticks = res[root]["fwd_sigma_log"][str(H)] * lvl / tp
            e = res[root]["cells"]["S"]["ALL"]["per_hold"][str(H)]
            per_h[str(H)] = {"sigma_ticks": sig_ticks, "gross_ticks": e * sig_ticks}
        ticks[root] = per_h

    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "design": "docs/decisions/D675-STAGE-1-DESIGN-the-log-macd-edge-decomposed-exactly.md",
           "window": list(d484.IN_SAMPLE), "roots": list(ROOTS), "holds": list(HOLDS),
           "kernel": {"positive_lags": "0-13", "negative_lags": "14+", "truncation": K,
                      "abs_weight_beyond_78": float(np.abs(W[79:]).sum() / np.abs(W).sum())},
           "G0": {"cells": len(now), "P1_pooled": p1, "bit_identical": True},
           "reads": reads, "decomposition": res, "predictions": pr, "ticks_S_gross": ticks,
           "wall_seconds": time.perf_counter() - t0}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    P(f"\nwrote {OUT.relative_to(REPO)}  ({time.perf_counter() - t0:.0f}s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return do_self_test()
    if a.run:
        do_self_test()
        return do_run(a.data_root)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
