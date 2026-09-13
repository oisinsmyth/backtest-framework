"""D523 STAGE 0 -- is the trending exception a detectable STATE, and is it commoner than chance?

    python scripts/d523_oracle_stage0.py --self-test      # 16 checks, seconds
    python scripts/d523_oracle_stage0.py --profile        # one root, timing, before any fan-out
    python scripts/d523_oracle_stage0.py --run            # the two premise gates

Spec: docs/decisions/D523-the-oracle-label-is-the-trending-exception-a-detectable-state-and-can-a-
causal-statistic-see-it-coming.md, committed de26b79 BEFORE this file existed (R8).

WHAT THIS COMPUTES, and nothing else.  No P&L, no cost, no position (R15).

  eff   = |sum(r)| / sum(|r|)  over H contiguous 5-minute log returns inside ONE session.
  z     = the observed eff's MID-P PERCENTILE inside that block's own sign-shuffle distribution,
          holding |r| identically fixed.  Exactly uniform under sign exchangeability, so it needs
          no random-walk constant -- which is the point, because D471's `C` is 1 only for Gaussian
          steps and measured 1.17-1.21 on ES, making a raw efficiency benchmark unusable.
  GATE 0a  split-half reliability of mean z across odd- vs even-indexed blocks of a root-session.
           Zero if trendiness is an independent coin flip per block.
  GATE 0b  exception rate minus mean(b0) at H=8, in percentage points.

THREE EXACTNESS DECISIONS, each of which a shortcut would have broken.

  1. eff_obs IS READ OUT OF THE ENUMERATION, not recomputed.  `sum(r)` and `S[k] @ |r|` are the
     same number in real arithmetic and NOT bit-identical in floating point (different summation
     order), so a `vals == eff_obs` tie count would be wrong in its last bits -- and the mid-p
     definition depends on that exact tie count.  The observed sign pattern is encoded to its row
     index instead, so eff_obs is bit-identically one of the atoms.
  2. THE MID-RANK IS AN INTEGER and is carried as one: `2*count(<) + count(=)` is in [1, 2^H - 1],
     so z = that / 2^H exactly, with no float accumulation anywhere.  At H=8 it fits uint8.
  3. TIES AMONG ATOMS ARE COMMON AND ARE NOT A NUISANCE.  A 5-minute ZT bar moves 0 or 1 tick, so
     many |r| coincide and so do many atoms.  q95 and b0 are therefore taken as ORDER STATISTICS
     of the enumerated vector, which handles ties correctly by construction; nothing assumes the
     atoms are distinct.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_day5m.parquet"
META = REPO / "data" / "fixtures" / "fut_day5m.meta.json"
OUT = REPO / "data" / "d523_oracle_stage0.json"

IS_END = "2023-12-29"          # in sample; 2024+ is RESERVED and NOT READ
HORIZONS = (3, 4, 6, 8, 12, 16, 20)
PRIMARY_H = 8
EXACT_MAX_H = 12               # enumerate at or below this; sample above
N_SAMPLED = 8192               # sign vectors, for H > EXACT_MAX_H
MIN_BLOCKS_0A = 4              # a split-half needs >= 2 blocks a side
N_NULL = 1000
N_BOOT = 2000
SEED = 523


class GateError(RuntimeError):
    pass


def P(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------------------------
# the statistic
# ---------------------------------------------------------------------------------------------
def eff(r: np.ndarray) -> float:
    """|net| / |path|.  1 a straight line, 0 a round trip, sign-blind, in [0, 1]."""
    d = np.abs(r).sum()
    if d == 0:
        raise GateError("[EFF] a block whose path length is zero has no efficiency")
    return abs(r.sum()) / d


def sign_matrix(H: int) -> np.ndarray:
    """The 2^(H-1) flip-classes of {-1,+1}^H, first column pinned to +1.

    eff(s) == eff(-s), so half the group is redundant; pinning s_0 = +1 picks one
    representative of each class exactly once."""
    k = np.arange(2 ** (H - 1), dtype=np.int64)
    bits = ((k[:, None] >> np.arange(H - 1)[None, :]) & 1).astype(np.int8)
    return np.hstack([np.ones((len(k), 1), np.int8), np.where(bits == 1, 1, -1)])


def observed_row(r: np.ndarray) -> np.ndarray:
    """Row index of each column of `r` (H x n) in `sign_matrix(H)`.

    A zero return contributes 0 to eff whichever sign it is given, so it is assigned +1."""
    H = r.shape[0]
    s = np.where(r >= 0, 1, -1).astype(np.int8)
    s = s * s[0]                                     # normalise the first sign to +1
    bits = (s[1:] == 1).astype(np.int64)
    return (bits * (1 << np.arange(H - 1, dtype=np.int64))[:, None]).sum(0)


def _midranks(vals: np.ndarray) -> np.ndarray:
    """`2*count(below) + count(equal)` for every entry, per column, fully vectorised.

    An element in the sorted tie group spanning [s, e) has `count(below) = s` and
    `count(equal) = e - s`, so its mid-rank numerator is `s + e`.  Found by accumulating the
    group boundaries along the sorted axis -- no per-column Python loop, no searchsorted."""
    m = vals.shape[0]
    order = np.argsort(vals, axis=0, kind="stable")
    sv = np.take_along_axis(vals, order, axis=0)
    idx = np.arange(m, dtype=np.int64)[:, None]
    new = np.empty(sv.shape, bool)
    new[0, :] = True
    new[1:, :] = sv[1:, :] != sv[:-1, :]
    gstart = np.maximum.accumulate(np.where(new, idx, 0), axis=0)
    nxt = np.empty(sv.shape, bool)
    nxt[:-1, :] = new[1:, :]
    nxt[-1, :] = True
    gend = np.minimum.accumulate(np.where(nxt, idx + 1, m)[::-1], axis=0)[::-1]
    out = np.empty(vals.shape, np.int64)
    np.put_along_axis(out, order, gstart + gend, axis=0)
    return out


def block_labels(r: np.ndarray, rng: np.random.Generator | None = None,
                 want_ranks: bool | None = None) -> dict:
    """z, eff_obs, q95, b0 (and optionally every atom's mid-rank) for blocks `r`, shape (H, n).

    Mid-ranks are INTEGERS over a denominator of 2^H (or 2*N_SAMPLED when sampled), so z is
    exact with no float accumulation.  `ranks_all` is what a Stage-0a null draw reads; it is
    m x n, so it is kept only where m is small (H <= 8) and the null is drawn uniformly above
    that, where the atom granularity is <= 1/2048 and the coarsening is immaterial."""
    H, n = r.shape
    a = np.abs(r)
    path = a.sum(0)
    if (path == 0).any():
        raise GateError("[EFF] zero-path blocks must be dropped before labelling")

    exact = H <= EXACT_MAX_H
    if exact:
        S = sign_matrix(H)
        idx = observed_row(r)
        m = S.shape[0]
    else:
        if rng is None:
            raise GateError("[SAMPLE] a sampled horizon needs an rng")
        S = np.where(rng.integers(0, 2, (N_SAMPLED, H)) == 1, 1, -1).astype(np.int8)
        S[:, 0] = 1
        idx = None
        m = N_SAMPLED

    keep_ranks = (m <= 128) if want_ranks is None else want_ranks
    dt = np.uint8 if 2 * m - 1 <= 255 else np.uint16
    Sf = S.astype(np.float64)
    chunk = max(256, 4_000_000 // m)        # ~4M cells a chunk, so peak memory is flat in m
    z_num = np.empty(n, np.int64)
    q95 = np.empty(n)
    b0 = np.empty(n)
    eff_obs = np.empty(n)
    ranks_all = np.empty((m, n), dt) if keep_ranks else None
    k95 = int(np.ceil(0.95 * m))            # 1-indexed order statistic

    for lo in range(0, n, chunk):
        hi = min(lo + chunk, n)
        w = np.arange(hi - lo)
        vals = np.abs(Sf @ a[:, lo:hi]) / path[lo:hi]
        # ONE order statistic, not a full sort: partition is O(m), sort is O(m log m), and
        # only the k95-th element is ever read.
        q = np.partition(vals, k95 - 1, axis=0)[k95 - 1]
        q95[lo:hi] = q
        b0[lo:hi] = (vals > q).sum(0) / m
        # eff_obs is READ OUT of the enumeration where the null is exact, so the tie count
        # in the mid-p rank is exact rather than one-ULP fragile.
        e = (vals[idx[lo:hi], w] if exact
             else np.abs(r[:, lo:hi].sum(0)) / path[lo:hi])
        eff_obs[lo:hi] = e
        if keep_ranks:
            # the FULL mid-rank table, needed only because a Stage-0a null draw reads an
            # arbitrary atom's rank.  This is the one place an argsort is unavoidable.
            mr = _midranks(vals)
            ranks_all[:, lo:hi] = mr.astype(dt)
            z_num[lo:hi] = mr[idx[lo:hi], w]
        else:
            # only the OBSERVED row's rank is wanted, which is two O(m) comparisons
            z_num[lo:hi] = 2 * (vals < e[None, :]).sum(0) + (vals == e[None, :]).sum(0)

    return {"z": z_num / (2 * m), "z_num": z_num, "denom": 2 * m, "eff": eff_obs,
            "q95": q95, "b0": b0, "m": m, "exact": exact, "ranks_all": ranks_all,
            "exception": eff_obs > q95}


def b0_theoretical(H: int) -> float:
    """Exact null tail probability for generic (untied) |r|: the reason H=3 and H=4 are refused."""
    m = 2 ** (H - 1)
    return (m - int(np.ceil(0.95 * m))) / m


# ---------------------------------------------------------------------------------------------
# ranking and correlation, without scipy
# ---------------------------------------------------------------------------------------------
def rankdata_ref(x: np.ndarray) -> np.ndarray:
    """Average ranks, ties shared -- the reference, a plain loop. scipy is not installed here."""
    n = len(x)
    o = np.argsort(x, kind="stable")
    xs = x[o]
    r = np.empty(n, np.float64)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[j + 1] == xs[i]:
            j += 1
        r[o[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return r


def rankdata(x: np.ndarray) -> np.ndarray:
    """Average ranks, ties shared, with NO Python loop. Ranks along the LAST axis.

    THE MEASURED BOTTLENECK, not a guessed one.  The reference above walks the tie groups in
    Python, so one call over 84,000 sessions is ~84,000 interpreter iterations -- and the
    Stage-0a null calls it twice per draw, 1,000 draws a horizon.  A tie group spanning
    sorted positions [s, e) has average 1-indexed rank (s + e + 1)/2, and both boundaries come
    from accumulating the group edges, exactly as `_midranks` does.  Working along the last
    axis lets a whole BATCH of null draws be ranked in one call.  Asserted bit-identical to
    the reference on tie-heavy input in the self-test."""
    n = x.shape[-1]
    o = np.argsort(x, axis=-1, kind="stable")
    xs = np.take_along_axis(x, o, axis=-1)
    idx = np.arange(n, dtype=np.int64)
    new = np.empty(xs.shape, bool)
    new[..., 0] = True
    new[..., 1:] = xs[..., 1:] != xs[..., :-1]
    gstart = np.maximum.accumulate(np.where(new, idx, 0), axis=-1)
    nxt = np.empty(xs.shape, bool)
    nxt[..., :-1] = new[..., 1:]
    nxt[..., -1] = True
    gend = np.minimum.accumulate(np.where(nxt, idx + 1, n)[..., ::-1], axis=-1)[..., ::-1]
    r = np.empty(x.shape, np.float64)
    np.put_along_axis(r, o, (gstart + gend + 1) * 0.5, axis=-1)
    return r


def pearson(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Pearson along the LAST axis; scalar in, scalar out."""
    x = x - x.mean(axis=-1, keepdims=True)
    y = y - y.mean(axis=-1, keepdims=True)
    d = np.sqrt((x * x).sum(-1) * (y * y).sum(-1))
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(d > 0, (x * y).sum(-1) / d, np.nan)
    return out if out.ndim else float(out)


def spearman(x: np.ndarray, y: np.ndarray):
    return pearson(rankdata(x), rankdata(y))


# ---------------------------------------------------------------------------------------------
# the split-half plan: computed ONCE, so a batch of null draws is a handful of array calls
# ---------------------------------------------------------------------------------------------
def halfsum_plan(sid: np.ndarray, ordinal: np.ndarray) -> dict:
    """Reorder + reduceat boundaries for per-session odd/even means.

    `split_half` costs four bincounts a call, and the Stage-0a null needs it 1,000 times.
    The grouping never changes between draws -- only the z values do -- so the ordering and
    the group boundaries are hoisted here and every draw becomes one `add.reduceat` that
    vectorises over the batch axis.  Hoisted, not reordered: the sums are over the same
    members in the same sorted order as before."""
    parity = (ordinal % 2).astype(np.int64)
    ns = int(sid.max()) + 1
    key = sid * 2 + parity
    order = np.argsort(key, kind="stable")
    ks = key[order]
    new = np.empty(len(ks), bool)
    new[0] = True
    new[1:] = ks[1:] != ks[:-1]
    starts = np.flatnonzero(new)
    counts = np.diff(np.append(starts, len(ks))).astype(np.float64)
    gkey = ks[starts]
    gsid, gpar = gkey // 2, gkey % 2
    grp = np.full((ns, 2), -1, np.int64)
    grp[gsid, gpar] = np.arange(len(starts))
    tot = np.bincount(gsid, weights=counts, minlength=ns)
    ok = (tot >= MIN_BLOCKS_0A) & (grp[:, 0] >= 0) & (grp[:, 1] >= 0)
    return {"order": order, "starts": starts, "counts": counts,
            "ei": grp[ok, 0], "oi": grp[ok, 1], "n_sessions": int(ok.sum())}


def half_means(z: np.ndarray, plan: dict) -> tuple[np.ndarray, np.ndarray]:
    """Per-session even/odd mean z. `z` may be 1-D or (batch, n_blocks)."""
    m = np.add.reduceat(z[..., plan["order"]], plan["starts"], axis=-1) / plan["counts"]
    return m[..., plan["ei"]], m[..., plan["oi"]]


def reliability(z: np.ndarray, plan: dict):
    e, o = half_means(z, plan)
    return spearman(e, o)


# ---------------------------------------------------------------------------------------------
# the panel
# ---------------------------------------------------------------------------------------------
def eligible() -> tuple[pd.DataFrame, dict]:
    """The fixture, cut to the pre-registered universe and window."""
    meta = json.loads(META.read_text(encoding="utf-8"))
    cov = meta["coverage"]["per_root"]
    clean = {r: c["first_clean_year"] for r, c in cov.items()
             if c["first_clean_year"] is not None}
    d = pd.read_parquet(FIX, columns=["root", "day", "bar", "close", "same_front", "present"])
    n0 = len(d)
    d = d[d["root"].isin(clean)]
    d["yr"] = d["day"].str[:4].astype(int)
    d = d[d["yr"] >= d["root"].map(clean)]
    d = d[d["present"]]
    d = d[d["same_front"]]
    d = d[d["day"] <= IS_END]
    d = d.sort_values(["root", "day", "bar"], kind="stable").reset_index(drop=True)
    info = {"rows_fixture": int(n0), "rows_eligible": int(len(d)),
            "roots": sorted(clean), "excluded_roots": sorted(set(cov) - set(clean)),
            "first_clean_year": clean,
            "sessions": int(d.groupby(["root", "day"]).ngroups),
            "span": [str(d["day"].min()), str(d["day"].max())]}
    return d, info


def runs_of(bars: np.ndarray) -> list[tuple[int, int]]:
    """[(start, stop)) index ranges of CONSECUTIVE bar slots."""
    brk = np.flatnonzero(np.diff(bars) != 1)
    starts = np.concatenate(([0], brk + 1))
    stops = np.concatenate((brk + 1, [len(bars)]))
    return list(zip(starts.tolist(), stops.tolist()))


def blocks_for_root(g: pd.DataFrame, H: int) -> tuple:
    """Non-overlapping forward blocks of H close-to-close log returns inside one session.

    Returns (R of shape (H, n_blocks), session_id, block ordinal within session, first bar).
    A run of L bars yields L-1 returns and (L-1)//H blocks; blocks never straddle a gap or a
    session boundary.  `bar0` is the bar index of the block's FIRST CLOSE, so the block reads
    bars `bar0 .. bar0+H` inclusive and a caller can verify contiguity independently."""
    cols, sid, ordinal, bar0 = [], [], [], []
    bars = g["bar"].to_numpy()
    close = g["close"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    # session boundaries
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    seg_bounds = list(zip(np.concatenate(([0], cut)).tolist(),
                          np.concatenate((cut, [len(g)])).tolist()))
    for s_i, (s0, s1) in enumerate(seg_bounds):
        b = bars[s0:s1]
        c = close[s0:s1]
        k = 0
        for (r0, r1) in runs_of(b):
            if r1 - r0 < H + 1:                  # H returns need H+1 closes
                continue
            lr = np.diff(np.log(c[r0:r1]))       # length (r1-r0-1)
            nb = len(lr) // H
            if nb == 0:
                continue
            cols.append(lr[:nb * H].reshape(nb, H).T)
            sid.append(np.full(nb, s_i, np.int64))
            ordinal.append(np.arange(k, k + nb, dtype=np.int64))
            bar0.append(b[r0] + H * np.arange(nb, dtype=np.int64))
            k += nb
    if not cols:
        z = np.zeros(0, np.int64)
        return np.zeros((H, 0)), z, z, z
    return (np.hstack(cols), np.concatenate(sid), np.concatenate(ordinal),
            np.concatenate(bar0))


# ---------------------------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------------------------
def split_half(z: np.ndarray, sid: np.ndarray, ordinal: np.ndarray) -> tuple:
    """Mean z over even- and odd-indexed blocks of each session, for sessions with >= MIN blocks."""
    ns = int(sid.max()) + 1 if len(sid) else 0
    cnt = np.bincount(sid, minlength=ns)
    ev = ordinal % 2 == 0
    se = np.bincount(sid[ev], weights=z[ev], minlength=ns)
    ne = np.bincount(sid[ev], minlength=ns)
    so = np.bincount(sid[~ev], weights=z[~ev], minlength=ns)
    no = np.bincount(sid[~ev], minlength=ns)
    ok = (cnt >= MIN_BLOCKS_0A) & (ne > 0) & (no > 0)
    return se[ok] / ne[ok], so[ok] / no[ok], int(ok.sum())


def session_bootstrap_excess(exc: np.ndarray, b0: np.ndarray, sid: np.ndarray,
                             rng: np.random.Generator, n_boot: int) -> np.ndarray:
    """Bootstrap of (mean exception - mean b0) resampling ROOT-SESSIONS, not blocks.

    RETURNED IN PERCENTAGE POINTS, the same unit as the statistic it is the SE of.  The first
    version returned a fraction while the statistic was scaled by 100, so the reported SE was
    100x too small and the gate compared pp against a fraction."""
    ns = int(sid.max()) + 1
    n_s = np.bincount(sid, minlength=ns).astype(np.float64)
    e_s = np.bincount(sid, weights=exc.astype(np.float64), minlength=ns)
    b_s = np.bincount(sid, weights=b0, minlength=ns)
    # BATCHED: one gather of (chunk, ns) instead of n_boot scalar passes. The draw sequence
    # is unchanged -- rng.integers is called with the same total count in the same order --
    # only the reduction is vectorised.
    out = np.empty(n_boot)
    step = max(1, 8_000_000 // max(ns, 1))
    for lo in range(0, n_boot, step):
        k = min(step, n_boot - lo)
        d = rng.integers(0, ns, (k, ns))
        out[lo:lo + k] = 100.0 * (e_s[d].sum(1) - b_s[d].sum(1)) / n_s[d].sum(1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--profile", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.profile:
        return profile()
    if a.run:
        return run()
    ap.print_help()
    return 1


def profile() -> int:
    P("  profiling ONE root before any fan-out (measure the worker, then decide)")
    d, info = eligible()
    g = d[d["root"] == "ES"]
    for H in (8, 12):
        t0 = time.time()
        R, sid, ordn, _ = blocks_for_root(g, H)
        t1 = time.time()
        keep = np.abs(R).sum(0) > 0
        lab = block_labels(R[:, keep], rng=np.random.default_rng(SEED))
        t2 = time.time()
        P(f"    ES H={H:>2}  {R.shape[1]:>7,} blocks  build {t1-t0:5.1f}s  label {t2-t1:5.1f}s"
          f"  -> 35 roots approx {(t2-t0)*35/60:4.1f} min")
    return 0


def run() -> int:
    rng = np.random.default_rng(SEED)
    P("D523 STAGE 0 -- the two premise gates")
    d, info = eligible()
    P(f"  eligible: {info['rows_eligible']:,} bars of {info['rows_fixture']:,}, "
      f"{len(info['roots'])} roots, {info['sessions']:,} root-sessions, "
      f"{info['span'][0]} .. {info['span'][1]}")
    P(f"  excluded roots: {info['excluded_roots']}   window ends {IS_END} (2024+ NOT READ)")

    # HOISTED: the horizon loop used `d[d.root == r]`, a full-column scan of 6.7M rows, 35
    # times per horizon = 245 scans. Split once.
    by_root = {r: g for r, g in d.groupby("root", sort=True)}
    del d

    res = {"spec": "D523 pre-reg de26b79", "universe": info, "gates": {}, "ladder": {}}
    roots = info["roots"]

    for H in HORIZONS:
        t0 = time.time()
        zs, excs, b0s, sids, ords, per_root, ranks = [], [], [], [], [], {}, []
        off = 0
        for r in roots:
            R, sid, ordn, _ = blocks_for_root(by_root[r], H)
            if R.shape[1] == 0:
                continue
            # session ids are offset by the root's FULL session count, taken BEFORE the
            # zero-path filter -- otherwise dropping the last session's blocks would shorten
            # the offset and the next root's ids would collide with this one's.
            n_sess_root = int(sid.max()) + 1
            keep = np.abs(R).sum(0) > 0
            n_zero = int((~keep).sum())
            R, sid, ordn = R[:, keep], sid[keep], ordn[keep]
            if R.shape[1] == 0:
                off += n_sess_root
                continue
            lab = block_labels(R, rng=rng)
            zs.append(lab["z"])
            excs.append(lab["exception"])
            b0s.append(lab["b0"])
            sids.append(sid + off)
            ords.append(ordn)
            if lab["ranks_all"] is not None:
                ranks.append(lab["ranks_all"])
            off += n_sess_root
            pl = halfsum_plan(sid, ordn)
            per_root[r] = {
                "blocks": int(R.shape[1]), "zero_path_blocks_dropped": n_zero,
                "sessions_0a": pl["n_sessions"],
                "mean_z": float(lab["z"].mean()),
                "exception_rate": float(lab["exception"].mean()),
                "b0_mean": float(lab["b0"].mean()),
                "excess_pp": float(100 * (lab["exception"].mean() - lab["b0"].mean())),
                "reliability": (float(reliability(lab["z"], pl))
                                if pl["n_sessions"] > 30 else None)}
        t_label = time.time() - t0

        z = np.concatenate(zs)
        exc = np.concatenate(excs)
        b0 = np.concatenate(b0s)
        sid = np.concatenate(sids)
        ordn = np.concatenate(ords)
        m = 2 ** (H - 1) if H <= EXACT_MAX_H else N_SAMPLED
        plan = halfsum_plan(sid, ordn)
        ns = plan["n_sessions"]

        # ---- 0b: the excess, in PERCENTAGE POINTS and so is its SE ------------------------
        excess = 100 * (exc.mean() - b0.mean())
        bse = session_bootstrap_excess(exc, b0, sid, rng, N_BOOT) if H >= 6 else None
        ex_se = float(np.std(bse, ddof=1)) if bse is not None else None

        # ---- 0a: split-half reliability --------------------------------------------------
        rel = float(reliability(z, plan))
        # NULL: replace each block's observed atom by a uniformly drawn one. BATCHED -- the
        # grouping is fixed across draws, so a chunk of draws is one reduceat and one
        # batched rank, instead of 1,000 scalar passes over 84,000 sessions.
        RA = np.hstack(ranks) if ranks else None
        nb = len(z)
        null = np.empty(N_NULL)
        batch = max(1, 6_000_000 // max(nb, 1))
        cols = np.arange(nb)
        for lo in range(0, N_NULL, batch):
            k = min(batch, N_NULL - lo)
            if RA is not None:
                kk = rng.integers(0, m, (k, nb))
                zn = RA[kk, cols].astype(np.float64) / (2 * m)
            else:
                zn = rng.random((k, nb))   # z is uniform to within 1/m; m >= 32,768 here
            null[lo:lo + k] = np.atleast_1d(reliability(zn, plan))
        # bootstrap SE of the null p95 ITSELF (D373: a sample p95 is biased toward the centre)
        bi = rng.integers(0, N_NULL, (200, N_NULL))
        p95 = float(np.percentile(null, 95))
        p95_se = float(np.std(np.percentile(null[bi], 95, axis=1), ddof=1))
        # and the observed reliability's own SE, resampling SESSIONS
        rel_se = None
        if ns > 30:
            e, o = half_means(z, plan)
            dd = rng.integers(0, ns, (500, ns))
            rel_se = float(np.std(spearman(e[dd], o[dd]), ddof=1))

        row = {"H": H, "atoms": m, "exact_null": H <= EXACT_MAX_H,
               "blocks": int(nb), "sessions_0a": ns,
               "mean_z": float(z.mean()),
               "b0_theoretical": b0_theoretical(H) if H <= EXACT_MAX_H else None,
               "b0_measured": float(b0.mean()),
               "exception_rate": float(exc.mean()),
               "excess_pp": float(excess), "excess_se_pp": ex_se,
               "reliability": rel, "reliability_se": rel_se,
               "null_p50": float(np.percentile(null, 50)), "null_p95": p95,
               "null_p95_se": p95_se,
               "seconds": {"label": round(t_label, 1), "total": round(time.time() - t0, 1)},
               "per_root": per_root}
        res["ladder"][str(H)] = row
        P(f"\n  H={H:>2}  {nb:>8,} blocks  {ns:>7,} sessions  "
          f"label {t_label:5.1f}s  total {time.time()-t0:5.1f}s   mean z {z.mean():.4f}")
        if H >= 6:
            P(f"        0b  exception {exc.mean()*100:6.3f}%  b0 {b0.mean()*100:6.3f}%"
              f"  EXCESS {excess:+7.3f} pp  +/- {ex_se:.3f}")
        else:
            P(f"        0b  NOT DEFINED (b0 = 0 exactly; the threshold is eff = 1)")
        P(f"        0a  reliability {rel:+.4f}"
          f"{'' if rel_se is None else f' +/- {rel_se:.4f}'}"
          f"   null p50 {np.percentile(null,50):+.4f}  p95 {p95:+.4f} +/- {p95_se:.4f}")

    # ---- the pre-registered gates, at the pre-registered horizon ------------------------
    pr = res["ladder"][str(PRIMARY_H)]
    ex, exse = pr["excess_pp"], pr["excess_se_pp"]
    rel, p95, p95se = pr["reliability"], pr["null_p95"], pr["null_p95_se"]
    if ex is None or exse is None:
        raise GateError("[GATE] the primary horizon has no defined excess")
    g0b = "PASS" if ex > 2 * exse else ("UNRESOLVED" if ex > 0 else "FAIL")
    marg = rel - p95
    g0a = ("UNRESOLVED" if abs(marg) <= 2 * p95se
           else ("PASS" if marg > 2 * p95se else "FAIL"))
    res["gates"] = {
        "primary_H": PRIMARY_H,
        "gate_0a": {"statistic": "split-half Spearman of mean z, odd vs even blocks",
                    "value": rel, "se": pr["reliability_se"],
                    "null_p95": p95, "null_p95_se": p95se,
                    "margin": marg, "verdict": g0a},
        "gate_0b": {"statistic": "exception rate - mean(b0), percentage points",
                    "value": ex, "se": exse, "verdict": g0b},
        "stop_rule": "both fail -> the line closes on its premise; Stages 1-2 are not run",
        "outcome": ("LINE CLOSED ON PREMISE" if g0a == "FAIL" and g0b == "FAIL"
                    else "PROCEED TO STAGE 1")}
    P(f"\n  GATE 0a  {rel:+.4f} vs null p95 {p95:+.4f} (SE {p95se:.4f})  -> {g0a}")
    P(f"  GATE 0b  {ex:+.3f} pp (SE {exse:.3f})                       -> {g0b}")
    P(f"  OUTCOME  {res['gates']['outcome']}")
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------------------------------------
def self_test() -> int:
    fails = []

    def chk(name, ok, note=""):
        P(f"    [{'PASS' if ok else 'FAIL'}] {name:<66} {note}")
        if not ok:
            fails.append(name)

    # 1 -- eff on paths whose answer is known by hand (D471's set, reused)
    chk("eff: a straight line is 1", eff(np.array([1.0, 1, 1, 1])) == 1.0)
    chk("eff: a round trip is 0", eff(np.array([1.0, -1, 1, -1])) == 0.0)
    chk("eff: out-and-two-thirds-back is 0.2",
        abs(eff(np.array([3.0, -2.0])) - 0.2) < 1e-15, f"{eff(np.array([3.0,-2.0])):.6f}")
    r = np.array([0.3, -0.1, 0.2, -0.4])
    chk("eff: sign-blind", eff(r) == eff(-r))
    chk("eff: in [0,1] on 10,000 random paths",
        all(0 <= eff(x) <= 1 for x in np.random.default_rng(0).normal(size=(10_000, 6))))
    try:
        eff(np.zeros(4)); zok = False
    except GateError:
        zok = True
    chk("[X] eff RAISES on a zero-path block instead of dividing by zero", zok)

    # 2 -- the enumeration is the whole group
    import itertools
    for H in (3, 4, 6, 8):
        S = sign_matrix(H)
        brute = {tuple(s if s[0] == 1 else tuple(-np.array(s)))
                 for s in itertools.product((-1, 1), repeat=H)}
        got = {tuple(row) for row in S}
        ok = len(S) == 2 ** (H - 1) and got == brute
        chk(f"enumeration H={H}: {2**(H-1)} rows and equals brute force deduped by flip", ok)
    a = np.abs(np.random.default_rng(1).normal(size=8))
    S = sign_matrix(8)
    v1 = np.abs(S @ a) / a.sum()
    v2 = np.abs((-S) @ a) / a.sum()
    chk("eff(s) == eff(-s) for every enumerated row, bit-identically", np.array_equal(v1, v2))

    # 3 -- observed_row finds the actual pattern, so eff_obs IS an atom
    rng = np.random.default_rng(2)
    R = rng.normal(size=(8, 500))
    idx = observed_row(R)
    S = sign_matrix(8)
    A = np.abs(R)
    vals = np.abs(S.astype(float) @ A) / A.sum(0)
    e_from_atom = vals[idx, np.arange(500)]
    e_direct = np.abs(R.sum(0)) / A.sum(0)
    chk("observed_row: eff read from the enumeration matches the direct sum to 1e-12",
        np.allclose(e_from_atom, e_direct, atol=1e-12),
        f"max diff {np.abs(e_from_atom - e_direct).max():.2e}")
    # THE INVARIANT the mid-p count needs is that eff_obs is bit-identically one of the atoms.
    # Reading it out of the enumeration guarantees that by construction; recomputing it does
    # not, and the [X] below shows what one ULP does to the statistic.
    chk("eff_obs is bit-identically a member of its own atom set (the mid-p count depends on it)",
        bool((vals == e_from_atom[None, :]).any(0).all()))
    # toward +inf, not toward 1.0: nextafter(1.0, 1.0) is a NO-OP, and ~4 of 500 random
    # 8-return blocks are all-same-sign with eff exactly 1.0, which left their ties intact
    nudged = np.nextafter(e_from_atom, np.inf)
    eq_ok = (vals == e_from_atom[None, :]).sum(0)
    eq_nudge = (vals == nudged[None, :]).sum(0)
    chk("[X] ONE ULP up destroys every tie, so the mid-p rank would be wrong",
        eq_ok.min() >= 1 and eq_nudge.max() == 0,
        f"ties {eq_ok.min()}-{eq_ok.max()} become {eq_nudge.max()}")

    # 4 -- z is uniform under the null, and the exception rate equals mean(b0)
    n = 40_000
    mag = np.abs(np.random.default_rng(3).normal(size=(8, n))) + 0.01
    s = np.where(np.random.default_rng(4).integers(0, 2, (8, n)) == 1, 1, -1)
    lab = block_labels(mag * s)
    mz = lab["z"].mean()
    chk("z: mean is 0.5 on an iid-random-sign series", abs(mz - 0.5) < 0.005, f"{mz:.4f}")
    er, bm = lab["exception"].mean(), lab["b0"].mean()
    chk("z: exception rate equals mean(b0) under the null",
        abs(er - bm) < 0.004, f"{er:.4f} vs {bm:.4f}")
    trend = np.abs(mag)                      # all-positive: maximally trending
    labt = block_labels(trend)
    chk("[X] the SAME check FAILS on a deliberately trending series",
        abs(labt["z"].mean() - 0.5) > 0.4 and labt["exception"].mean() > 0.9,
        f"mean z {labt['z'].mean():.4f}, exception {labt['exception'].mean():.3f}")

    # 5 -- b0 is exact, bounded, and DEGENERATE at H=3 and H=4
    for H in (3, 4):
        aa = np.abs(np.random.default_rng(5).normal(size=(H, 200))) + 0.01
        L = block_labels(aa * np.where(np.random.default_rng(6).integers(0, 2, (H, 200)) == 1, 1, -1))
        chk(f"b0 is EXACTLY 0 at H={H} and q95 == 1.0 -- the exception cannot fire",
            L["b0"].max() == 0.0 and np.allclose(L["q95"], 1.0)
            and b0_theoretical(H) == 0.0, f"b0max {L['b0'].max()}, q95 {L['q95'][0]:.4f}")
    for H in (6, 8, 12):
        chk(f"b0 theoretical at H={H} is {b0_theoretical(H):.4f} and <= 0.05",
            b0_theoretical(H) <= 0.05 and b0_theoretical(H) > 0)

    # 6 -- ties: the vectorised path equals a reference loop on TIE-HEAVY input
    tie = np.tile(np.array([1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0])[:, None], (1, 300))
    tie = tie * np.where(np.random.default_rng(7).integers(0, 2, (8, 300)) == 1, 1, -1)
    L = block_labels(tie)
    S = sign_matrix(8)
    ref_z, ref_b0, ref_q, ref_e = [], [], [], []
    for j in range(300):
        aa = np.abs(tie[:, j])
        v = np.abs(S @ aa) / aa.sum()
        sv = np.sort(v)
        q = sv[int(np.ceil(0.95 * 128)) - 1]
        e = v[observed_row(tie[:, j:j + 1])[0]]
        ref_z.append((2 * (v < e).sum() + (v == e).sum()) / 256)
        ref_b0.append((v > q).sum() / 128)
        ref_q.append(q)
        ref_e.append(e)
    chk("[OPT] vectorised labels equal a reference loop EXACTLY on tie-heavy |r|",
        np.array_equal(L["z"], np.array(ref_z)) and np.array_equal(L["b0"], np.array(ref_b0))
        and np.array_equal(L["q95"], np.array(ref_q))
        and np.array_equal(L["eff"], np.array(ref_e)),
        f"{len(set(np.abs(tie[:,0])))} distinct |r| values")
    chk("ties really are present in that input (the check could otherwise not bite)",
        len(np.unique(np.abs(S @ np.abs(tie[:, 0])))) < 128,
        f"{len(np.unique(np.abs(S @ np.abs(tie[:,0]))))} distinct atoms of 128")

    # 7 -- ranks_all is the mid-rank of every atom
    chk("ranks_all[k] is the mid-rank of atom k, and the observed row reproduces z",
        np.array_equal(L["ranks_all"][observed_row(tie), np.arange(300)] / 256.0, L["z"]))

    # 8 -- blocks: contiguous, non-overlapping, inside one session
    g = pd.DataFrame({"root": "T", "day": ["d1"] * 20 + ["d2"] * 20,
                      "bar": list(range(20)) + list(range(20)),
                      "close": np.arange(1, 41, dtype=float)})
    R, sid, ordn, bar0 = blocks_for_root(g, 4)
    chk("blocks: a 20-bar session gives (20-1)//4 = 4 blocks, per session",
        R.shape[1] == 8 and list(np.bincount(sid)) == [4, 4], f"{R.shape[1]} blocks")
    chk("blocks: ordinals restart at 0 each session",
        list(ordn) == [0, 1, 2, 3, 0, 1, 2, 3])
    chk("blocks: non-overlapping -- consecutive blocks start exactly H bars apart",
        list(bar0) == [0, 4, 8, 12, 0, 4, 8, 12], f"{list(bar0)}")
    # A HOLE: bars 9 and 10 of d1 removed.  The BLOCK COUNT is a useless discriminator here --
    # 20 bars give 19//4 = 4 blocks and two 9-bar runs give 2+2 = 4, the SAME number.  What has
    # to be checked is that no block's bar span crosses the hole.
    holed = g[~((g["day"] == "d1") & (g["bar"].isin([9, 10])))]
    Rh, sidh, _, bh = blocks_for_root(holed, 4)
    present = set(holed[holed["day"] == "d1"]["bar"].tolist())
    spans = [set(range(int(b), int(b) + 5)) for b, s in zip(bh, sidh) if s == 0]
    chk("blocks: no block STRADDLES a hole -- every bar it reads is present",
        all(sp <= present for sp in spans) and len(spans) == 4,
        f"{len(spans)} d1 blocks, spans {[sorted(s)[0] for s in spans]}")
    chk("[X] and the block count alone could NOT have caught it",
        Rh.shape[1] == R.shape[1] == 8, f"{Rh.shape[1]} == {R.shape[1]}")
    chk("blocks: H returns need H+1 closes, so a 4-bar run yields no H=4 block",
        blocks_for_root(g[g["bar"] < 4], 4)[0].shape[1] == 0)

    # 9 -- rankdata and spearman, hand-checked
    chk("rankdata: ties share the average rank",
        list(rankdata(np.array([10.0, 20, 20, 30]))) == [1.0, 2.5, 2.5, 4.0])
    # [OPT] the three rewrites that made the run tractable, each against what it replaced,
    # on TIE-HEAVY input -- ties are where a vectorised rewrite disagrees.
    tiey = np.random.default_rng(11).integers(0, 5, 4000).astype(np.float64)
    chk("[OPT] vectorised rankdata equals the reference loop EXACTLY on tie-heavy input",
        np.array_equal(rankdata(tiey), rankdata_ref(tiey)),
        f"{len(np.unique(tiey))} distinct values in 4,000")
    batch = np.random.default_rng(12).integers(0, 5, (7, 4000)).astype(np.float64)
    chk("[OPT] batched rankdata equals row-by-row EXACTLY",
        np.array_equal(rankdata(batch),
                       np.vstack([rankdata_ref(row) for row in batch])))
    chk("[OPT] batched spearman equals the scalar call EXACTLY",
        np.array_equal(spearman(batch, batch[::-1]),
                       np.array([pearson(rankdata_ref(a_), rankdata_ref(b_))
                                 for a_, b_ in zip(batch, batch[::-1])])))
    # half_means (reduceat, hoisted plan) vs split_half (four bincounts, per call)
    rg = np.random.default_rng(13)
    sid_t = np.repeat(np.arange(400), 6)
    ord_t = np.tile(np.arange(6), 400)
    drop = rg.random(len(sid_t)) < 0.15          # ragged sessions, some falling under the min
    sid_t, ord_t = sid_t[~drop], ord_t[~drop]
    z_t = rg.random(len(sid_t))
    pl = halfsum_plan(sid_t, ord_t)
    e_ref, o_ref, ns_ref = split_half(z_t, sid_t, ord_t)
    e_fast, o_fast = half_means(z_t, pl)
    # add.reduceat over the reordered array and bincount over the original DO NOT sum in the
    # same order, so they differ by ~1 ULP on ~8% of sessions.  Reordering a float sum is
    # exactly what the house rule forbids, so the rewrite is held to the invariant that
    # actually decides the statistic: SPEARMAN READS ONLY RANKS.  The bound is derived --
    # a k-term sum carries at most (k-1) roundings and the mean divides by k, so the relative
    # error is at most k*eps -- not guessed.
    kmax = int(np.bincount(sid_t).max())
    bound = kmax * np.finfo(np.float64).eps
    chk("half_means agrees with split_half to the DERIVED float bound k*eps",
        pl["n_sessions"] == ns_ref
        and np.abs(e_fast - e_ref).max() <= bound
        and np.abs(o_fast - o_ref).max() <= bound,
        f"{ns_ref} sessions, max diff {np.abs(e_fast-e_ref).max():.2e} vs bound {bound:.2e}")
    chk("[OPT] and the RANKS are bit-identical, so the reported Spearman is unchanged",
        np.array_equal(rankdata(e_fast), rankdata(e_ref))
        and np.array_equal(rankdata(o_fast), rankdata(o_ref))
        and spearman(e_fast, o_fast) == spearman(e_ref, o_ref),
        f"rho {spearman(e_fast, o_fast):+.12f}")
    swap = e_ref.copy()
    lo_i, hi_i = np.argsort(swap)[:2]
    swap[lo_i], swap[hi_i] = swap[hi_i], swap[lo_i]
    chk("[X] and that rank check FIRES when two sessions actually swap places",
        not np.array_equal(rankdata(swap), rankdata(e_ref)))
    chk("[OPT] and half_means vectorises over a batch identically",
        np.array_equal(half_means(np.vstack([z_t, z_t[::-1]]), pl)[0],
                       np.vstack([half_means(z_t, pl)[0], half_means(z_t[::-1], pl)[0]])))

    # the excess bootstrap is in PERCENTAGE POINTS, the same unit as the statistic
    exc_t = (rg.random(len(sid_t)) < 0.20)
    b0_t = np.full(len(sid_t), 0.05)
    bs = session_bootstrap_excess(exc_t, b0_t, sid_t, rg, 400)
    point = 100 * (exc_t.mean() - b0_t.mean())
    chk("the excess bootstrap is centred on the point estimate IN PP, not a fraction",
        abs(bs.mean() - point) < 1.0 and abs(point) > 5,
        f"point {point:+.2f} pp, bootstrap mean {bs.mean():+.2f} pp, SE {bs.std(ddof=1):.3f}")
    chk("spearman: a monotone map gives exactly 1",
        abs(spearman(np.array([1.0, 2, 3, 4]), np.array([1.0, 4, 9, 16])) - 1.0) < 1e-12)
    chk("spearman: a reversed map gives exactly -1",
        abs(spearman(np.array([1.0, 2, 3, 4]), np.array([4.0, 3, 2, 1])) + 1.0) < 1e-12)

    # 10 -- split_half honours the minimum block count
    z = np.array([0.1, 0.9, 0.2, 0.8, 0.5, 0.5])
    sid = np.array([0, 0, 0, 0, 1, 1])
    ordn = np.array([0, 1, 2, 3, 0, 1])
    e, o, ns = split_half(z, sid, ordn)
    chk("split_half: a session with 2 blocks is excluded at MIN_BLOCKS_0A=4",
        ns == 1 and abs(e[0] - 0.15) < 1e-12 and abs(o[0] - 0.85) < 1e-12,
        f"{ns} session kept, even {e[0]:.3f} odd {o[0]:.3f}")

    # 11 -- the runner computes the PRE-REGISTERED statistic
    chk("the declared primary horizon is H=8 and the declared window ends 2023-12-29",
        PRIMARY_H == 8 and IS_END == "2023-12-29")
    chk("the declared horizons match the pre-registration",
        HORIZONS == (3, 4, 6, 8, 12, 16, 20))

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
