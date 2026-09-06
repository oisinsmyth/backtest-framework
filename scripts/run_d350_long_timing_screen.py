"""D350 -- a long-timing screen: 138 declared events, each scored against its own names at random times.

    uv run python scripts/run_d350_long_timing_screen.py --selftest
    uv run python scripts/run_d350_long_timing_screen.py --screen                       stage 1: the grid, every member
    uv run python scripts/run_d350_long_timing_screen.py --kernel SIG/Ek --draws N --part p   stage 2: D347's controls A and B
    uv run python scripts/run_d350_long_timing_screen.py --report                       stage 2: the kernel record + Q1..Q8

The family: the 46 dimensionless scores of D346's pool (the D290 51 less macd_line, macd_hist,
impulse_nodz, amihud_21, price_log), floored (keep_v2), deal-filtered (F0), on the warm base,
lagged one bar, ranked cross-sectionally among floored live names (average rank on ties, >= 50
finite names). Three long event shapes on the percentile p: E1 fresh entry into the bottom
decile (p <= 10, prev > 10); E2 fresh entry into the top decile (p >= 90, prev < 90); E3 the
recovery (p > 10, prev <= 10). hist_L/E1, rev_21/E1, rsi/E1 are D347's event sets exactly.

Stage 1 scores every member on the cached forward-40 hedged-excess grid F (D347's
forward_excess_grid): E_s = mean F over the member's event cells, every event counted. Control
A: each name's events rolled in time within its eligible bars, offsets independent per name,
a sparse gather of the rotated cells (guarded against the dense rotation). Control B: each
event's name replaced by a random floored live name in the same rsi bucket that day, distinct
per day and bucket where the pool allows. 1,000 draws each. Multiplicity: per-member p; BH at
q = 0.10 over the 138; the family-wise grid-max under one shared offset vector; M_eff by Li-Ji
and Cheverud-Nyholt from the members' daily mean-F event series.

Stage 2 runs D347's kernel (every event taken, next-open fill, hedged against the floored
market, cap and invalidation exits) on the survivors of the declared gate, with D347's
controls A, B (100 draws) and C (1,000), the mirror, PUB/PB net per trade, the four groups per
trade with the top trade named, the splits, and the rsi-bucket interaction.

ASSERTIONS [K][F0][R][F][G][SP][A][B][O][E][M][BH][X][6] -- pre-reg section 8.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import multiprocessing as mp
import sys
import threading
import time
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _wait_for_prep(max_wait_s=25 * 60, every_s=60):
    """The shared prep (scripts/d348_prep.py + temp/d348_prep/) is built by another study; wait for it."""
    f, d = REPO / "scripts" / "d348_prep.py", REPO / "temp" / "d348_prep"
    t0 = time.time()
    while not (f.exists() and d.exists()):
        if time.time() - t0 > max_wait_s:
            if not f.exists():
                raise SystemExit("scripts/d348_prep.py is absent after the wait; nothing to run against")
            print("  warning: temp/d348_prep/ absent after the wait -- prep() will BUILD its cache now", flush=True)
            break
        print(f"  waiting for scripts/d348_prep.py ({'present' if f.exists() else 'absent'}) and temp/d348_prep/ "
              f"({'present' if d.exists() else 'absent'}) ... {time.time() - t0:.0f}s", flush=True)
        time.sleep(every_s)


_wait_for_prep()
PREP = _load("d348p", "d348_prep.py")        # executes D347's alias chain ONCE; take every alias from here
V47 = PREP.V47
V45, PA, UF, FL, EB, W = PREP.V45, PREP.PA, PREP.UF, PREP.FL, PREP.EB, PREP.W

CAP, SEED = V47.CAP, V47.SEED
DECILE, BUCKET_EDGES = V47.DECILE, V47.BUCKET_EDGES
EXCLUDED = ("macd_line", "macd_hist", "impulse_nodz", "amihud_21", "price_log")
SHAPES = ("E1", "E2", "E3")
D347_MEMBERS = {"hist_L/E1": "hist_L", "rev_21/E1": "rev_21", "rsi/E1": "rsi_decile"}
D347_HIST_L_EVENTS = 23_491
REVERSAL = ("rsi", "rev_5", "rev_21", "hist_L", "md", "dist_52w_high", "mom_252_21")
DRAWS, BLOCK = 1000, 100
GATE_P, GATE_MIN_EVENTS, GATE_TOP, FALLBACK_TOP, BH_Q = 0.05, 2000, 5, 3, 0.10
CONVS = V47.CONVS
D346_JSON = REPO / "data" / "d346_legs_floor_open.json"
SCREEN_OUT = REPO / "data" / "d350_screen.json"
CTRL = REPO / "data" / "d350_ctrl_{member}_p{part}.json"
OUT = REPO / "data" / "d350_long_timing_screen.json"


# ------------------------------------------------------------------ the family
def load_pool(P):
    pool = list(json.loads(D346_JSON.read_text())["pool"])
    rule = [k for k in P["z"].files if k not in ("key", "warm") and k not in EXCLUDED]
    assert len(pool) == 46 and sorted(pool) == sorted(rule), f"pool {len(pool)} vs rule {len(rule)}: {sorted(set(pool) ^ set(rule))}"
    return pool


def members_of(pool):
    return [f"{s}/{k}" for s in pool for k in SHAPES]


def member_index(pool, member):
    sig, k = member.split("/")
    return pool.index(sig) * 3 + SHAPES.index(k)


_SCORE_LOCK = threading.Lock()


def lagged(P, sig):
    """D347's closure, line for line: floored, deal-filtered, warm-based, lagged one bar -> (T, n)."""
    with _SCORE_LOCK:                                 # one npz member read at a time (score_events runs in threads)
        raw = P["score"](sig)
    sc = UF.apply_floor_replace(np.where(P["excl"], np.nan, raw), P["keep"])
    sc = np.where(P["base"], sc, np.nan)
    out = np.full((P["T"], P["n"]), np.nan)
    out[1:] = sc[:, :-1].T
    return out


def shape_masks(p, elig):
    """The three long shapes on the percentile grid p, and their mirrors. E1's 'lo' is literally D347's."""
    prev = np.full_like(p, np.nan)
    prev[1:] = p[:-1]
    hi_edge = 100.0 - DECILE
    with np.errstate(invalid="ignore"):
        e1 = (p <= DECILE) & (prev > DECILE) & elig                 # D347: lo
        e2 = (p >= hi_edge) & (prev < hi_edge) & elig               # D347: hi (as a LONG event here)
        e3 = (p > DECILE) & (prev <= DECILE) & elig                 # the recovery
        e3m = (p < hi_edge) & (prev >= hi_edge) & elig              # E3's mirror: crossing down out of the top decile
    return {"E1": (e1, e2), "E2": (e2, e1), "E3": (e3, e3m)}       # shape -> (long event, its mirror)


def exit_score(pct, shape):
    """The score the kernel reads: entry order (most extreme first) and the invalidation exit (crossing 50 from the
    entry side). E2 enters the TOP decile, so its score is mirrored -- 100 - pct -- and 'pct >= 50' means the
    percentile has fallen back through the median."""
    return pct if shape in ("E1", "E3") else 100.0 - pct


def sparse_events(mask):
    t, i = np.nonzero(mask)
    return t.astype(np.int32), i.astype(np.int32)


def score_events(P, sig, elig):
    """One score -> its three members' sparse events. The (T, n) grids are built, used, and dropped."""
    pct = V47.percentile_grid(lagged(P, sig))
    masks = shape_masks(pct, elig)
    return {k: sparse_events(masks[k][0]) for k in SHAPES}


# ------------------------------------------------------------------ control A: the sparse rotation
class Rotator:
    """Per-name eligible-bar index. An event at position pos within its name's eligible bars moves to
    (pos + off) % L -- np.roll's convention, so the dense guard is np.roll on the eligible column."""

    def __init__(self, elig):
        T, n = elig.shape
        self.T, self.n = T, n
        cnt = elig.sum(axis=0).astype(np.int64)
        self.L = cnt
        self.start = np.concatenate([[0], np.cumsum(cnt)[:-1]]).astype(np.int64)
        i_c, t_c = np.nonzero(elig.T)                       # name-major, t ascending within a name
        self.at = t_c.astype(np.int32)
        self.pos = (np.cumsum(elig, axis=0, dtype=np.int32) - 1)

    def draw_offsets(self, rng, B):
        return rng.integers(0, np.maximum(self.L, 1), size=(B, self.n))

    def rotate(self, t, i, off):
        """(t, i) events, off (B, n) -> rotated bars (B, m); the name is unchanged."""
        p = self.pos[t, i].astype(np.int64)
        L, st = self.L[i], self.start[i]
        newpos = (p[None, :] + off[:, i]) % L[None, :]
        return self.at[st[None, :] + newpos]


def _nanmean_rows(X):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(X, axis=1)


def control_A(t, i, F, rot, rng, draws=DRAWS, block=BLOCK, half=None):
    """Mean F over the rotated cells, per draw; era statistics restricted to the ORIGINAL event's era."""
    A, A1, A2, n_nan = [], [], [], 0
    era1 = (t < half) if half is not None else None
    done = 0
    while done < draws:
        B = min(block, draws - done)
        off = rot.draw_offsets(rng, B)
        tr = rot.rotate(t, i, off)
        Fr = F[tr, i[None, :]]
        n_nan += int(np.isnan(Fr).sum())
        A.append(_nanmean_rows(Fr))
        if era1 is not None:
            A1.append(_nanmean_rows(Fr[:, era1]))
            A2.append(_nanmean_rows(Fr[:, ~era1]))
        done += B
    out = dict(A=np.concatenate(A), n_nan_cells=n_nan)
    if era1 is not None:
        out["A_era1"], out["A_era2"] = np.concatenate(A1), np.concatenate(A2)
    return out


def dense_rotate_within_elig(ev_dense, elig, off):
    """The guard: per name, np.roll of the event column restricted to the name's eligible bars."""
    out = np.zeros_like(ev_dense)
    for j in range(elig.shape[1]):
        idx = np.flatnonzero(elig[:, j])
        if idx.size:
            out[idx, j] = np.roll(ev_dense[idx, j], int(off[j]))
    return out


def dense_rotate_whole_grid(ev_dense, off):
    """A WRONG rotation -- the whole column rolled, ignoring eligibility; [6] must catch it."""
    out = np.zeros_like(ev_dense)
    for j in range(ev_dense.shape[1]):
        out[:, j] = np.roll(ev_dense[:, j], int(off[j]))
    return out


def assert_sparse_equals_dense(t, i, F, rot, elig, rng, draws, dense_fn, label):
    T, n = elig.shape
    ev_dense = np.zeros((T, n), bool)
    ev_dense[t, i] = True
    worst = 0.0
    for _ in range(draws):
        off = rot.draw_offsets(rng, 1)
        tr = rot.rotate(t, i, off)[0]
        sp = np.stack([tr, i], axis=1).astype(np.int64)
        sp = sp[np.lexsort((sp[:, 1], sp[:, 0]))]
        dn = np.argwhere(dense_fn(ev_dense, elig, off[0]))
        assert sp.shape == dn.shape and np.array_equal(sp, dn), f"[SP] {label}: rotated cell sets differ"
        m_sp = float(np.nanmean(F[sp[:, 0], sp[:, 1]]))
        m_dn = float(np.nanmean(F[dn[:, 0], dn[:, 1]]))
        assert (m_sp == m_dn) or (np.isnan(m_sp) and np.isnan(m_dn)), f"[SP] {label}: means differ"
        m_stat = float(np.nanmean(F[tr, i]))                       # the statistic as the screen computes it
        worst = max(worst, abs(m_stat - m_dn) if np.isfinite(m_stat) else 0.0)
        assert np.bincount(i, minlength=n).tolist() == np.bincount(sp[:, 1], minlength=n).tolist(), f"[A] {label}"
    return worst


# ------------------------------------------------------------------ control B: same day, same rsi bucket, another name
class BucketPools:
    """Per (day, bucket): the eligible names, as one flat array with start/count -- a draw is gathers only."""

    def __init__(self, elig, bucket):
        T, n = elig.shape
        self.T, self.n, self.nb = T, n, 10
        t_c, i_c = np.nonzero(elig)
        key = t_c.astype(np.int64) * self.nb + bucket[t_c, i_c].astype(np.int64)
        order = np.argsort(key, kind="stable")
        self.names = i_c[order].astype(np.int32)
        ks = key[order]
        keys = np.arange(T * self.nb)
        self.start = np.searchsorted(ks, keys, side="left").astype(np.int64)
        self.count = (np.searchsorted(ks, keys, side="right") - self.start).astype(np.int64)


def control_B(t, i, F, pools, bucket, rng, draws=DRAWS, block=BLOCK, return_last=False):
    """Each event's name replaced by a random eligible name in the same rsi bucket on the same day, distinct within
    the (day, bucket) group and never one of the group's own event names; where the pool is too small the excess
    events keep their original name (counted). Statistic: mean F over the replaced cells."""
    n, nb = pools.n, pools.nb
    m = t.size
    key = t.astype(np.int64) * nb + bucket[t, i].astype(np.int64)
    order = np.argsort(key, kind="stable")
    ks, ts, is_ = key[order], t[order].astype(np.int64), i[order].astype(np.int64)
    new = np.r_[True, ks[1:] != ks[:-1]]
    gid = np.cumsum(new) - 1                                    # (day, bucket) group of every event, contiguous
    G = int(gid[-1]) + 1 if m else 0
    gsize = np.bincount(gid, minlength=G)
    rank = np.arange(m) - np.flatnonzero(new)[gid]
    # the member-specific pools: every eligible name in the group's bucket that day, LESS the group's own event names
    ks_u = ks[new]
    cnt_u, st_u = pools.count[ks_u], pools.start[ks_u]
    tot = int(cnt_u.sum())
    rep_g = np.repeat(np.arange(G), cnt_u)
    within = np.arange(tot) - np.repeat(np.cumsum(cnt_u) - cnt_u, cnt_u)
    names_all = pools.names[st_u[rep_g] + within].astype(np.int64)
    ev_cell = np.sort(t.astype(np.int64) * n + i.astype(np.int64))
    cell = (ks_u // nb)[rep_g] * n + names_all
    j = np.searchsorted(ev_cell, cell).clip(max=ev_cell.size - 1)
    keep = ev_cell[j] != cell
    p_names, p_g = names_all[keep], rep_g[keep]
    p_cnt = np.bincount(p_g, minlength=G)
    p_st = np.cumsum(p_cnt) - p_cnt
    assert np.array_equal(p_cnt, cnt_u - gsize), "[B] a group's event names were not all found in its (day, bucket) pool"
    sample = rank < p_cnt[gid]                                  # the first k = min(events, pool) of each group are replaced
    n_kept = int((~sample).sum())
    s_idx = np.flatnonzero(sample)                              # sorted, group-contiguous
    ms = s_idx.size
    g_s = gid[s_idx]
    st_s, cnt_s = p_st[g_s], p_cnt[g_s]
    s_cnt = np.bincount(g_s, minlength=G)                       # sampled cells per group ...
    s_st = np.cumsum(s_cnt) - s_cnt                             # ... at columns s_st[g] .. s_st[g] + s_cnt[g] - 1
    multi_cols = np.flatnonzero(s_cnt[g_s] > 1)
    out, done, last = [], 0, None
    while done < draws:
        B = min(block, draws - done)
        samp = np.zeros((B, ms), np.int64)                      # the sampled events' replacement names
        todo = np.ones((B, ms), bool)
        for it in range(20_000):
            flat = np.flatnonzero(todo.ravel())
            if flat.size == 0:
                break
            d_f, col = flat // ms, flat % ms
            u = rng.random(flat.size)
            samp.ravel()[flat] = p_names[st_s[col] + (u * cnt_s[col]).astype(np.int64)]
            todo[:] = False
            # distinct within (draw, group): re-check every cell of every (draw, group) pair that was just redrawn
            if it == 0:
                act_d, act_c = np.repeat(np.arange(B), multi_cols.size), np.tile(multi_cols, B)
            else:
                g_f = g_s[col]
                mm = s_cnt[g_f] > 1
                if not mm.any():
                    continue
                pair = np.unique(d_f[mm] * G + g_f[mm])
                pd_, pg_ = pair // G, pair % G
                lens = s_cnt[pg_]
                act_d = np.repeat(pd_, lens)
                act_c = np.repeat(s_st[pg_], lens) + (np.arange(int(lens.sum())) - np.repeat(np.cumsum(lens) - lens, lens))
            if act_c.size == 0:
                continue
            comp = (act_d * G + g_s[act_c]) * n + samp[act_d, act_c]
            o = np.argsort(comp, kind="stable")
            cs = comp[o]
            dup = o[1:][cs[1:] == cs[:-1]]                      # the later element of every equal pair is redrawn
            todo[act_d[dup], act_c[dup]] = True
        else:
            raise AssertionError("[B] rejection sampling did not converge")
        name = np.tile(is_, (B, 1))                             # originals where the pool ran out (counted)
        name[:, s_idx] = samp
        Fb = F[ts[None, :], name]
        out.append(_nanmean_rows(Fb))
        if return_last:
            last = dict(t=ts, i_orig=is_, i_new=name[-1].copy(), gid=gid, sample=sample)
        done += B
    return dict(B=np.concatenate(out), n_kept=n_kept, last=last)


# ------------------------------------------------------------------ multiplicity
def bh_reject(p, q):
    p = np.asarray(p, float)
    m = p.size
    order = np.argsort(p, kind="stable")
    ps = p[order]
    ok = ps <= q * np.arange(1, m + 1) / m
    k = int(np.flatnonzero(ok).max()) + 1 if ok.any() else 0
    rej = np.zeros(m, bool)
    rej[order[:k]] = True
    return rej


def m_eff_of(C):
    """d321b's two estimators, formula for formula (liji, nyh). A pairwise-complete matrix can be indefinite, and
    d321b's Li-Ji term reads a negative eigenvalue e as e - floor(e); Li & Ji (2005) apply it to |e| -- that variant
    is returned fourth, as a diagnostic beside the verbatim one, with the eigenvalues."""
    n = C.shape[0]
    ev = np.linalg.eigvalsh(C)[::-1]
    liji = float(sum((1.0 if e >= 1 else 0.0) + min(1.0, max(0.0, e - np.floor(e))) for e in ev))     # d321b, verbatim
    nyh = float(1 + (n - 1) * (1 - np.var(ev, ddof=1) / n))                                             # d321b, verbatim
    liji_abs = float(sum((1.0 if a >= 1 else 0.0) + min(1.0, max(0.0, a - np.floor(a))) for a in np.abs(ev)))
    return liji, nyh, ev, liji_abs


def daily_series(t, F_ev, T):
    cnt = np.bincount(t, minlength=T).astype(float)
    s = np.bincount(t, weights=F_ev, minlength=T)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)


def pairwise_corr(S, min_overlap=10):
    """Pairwise-complete Pearson correlation of the rows of S (NaN = undefined day), symmetrised, unit diagonal;
    pairs with fewer than min_overlap common days (or zero variance) are set to 0."""
    Mk = np.isfinite(S).astype(float)
    X = np.where(np.isfinite(S), S, 0.0)
    N = Mk @ Mk.T
    Sx = X @ Mk.T                      # sum of x_i over days where j is defined
    Sxx = (X * X) @ Mk.T
    Sxy = X @ X.T
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = N * Sxy - Sx * Sx.T
        vx = N * Sxx - Sx * Sx
        C = cov / np.sqrt(vx * vx.T)
    bad = ~np.isfinite(C) | (N < min_overlap)
    C = np.where(bad, 0.0, C)
    C = 0.5 * (C + C.T)
    C = np.clip(C, -1.0, 1.0)
    np.fill_diagonal(C, 1.0)
    return C, int(bad[np.triu_indices(S.shape[0], 1)].sum())


def assert_M(C, tag=""):
    n = C.shape[0]
    assert np.array_equal(C, C.T) and np.allclose(np.diag(C), 1.0) and np.isfinite(C).all(), f"[M] {tag} matrix"
    liji, nyh, ev, liji_abs = m_eff_of(C)
    assert 1.0 <= liji <= n + 1e-9 and 1.0 <= nyh <= n + 1e-9, f"[M] {tag} M_eff {liji:.2f} / {nyh:.2f} outside [1, {n}]"
    return liji, nyh, ev, liji_abs


# ------------------------------------------------------------------ per-member statistics
def overlap_share(t, i):
    """Share of events that fall while the same name is already held by the kernel (a greedy 40-bar hold per name)."""
    if t.size == 0:
        return 0.0
    o = np.lexsort((t, i))
    ts, is_ = t[o], i[o]
    drop, last_i, last_t = 0, -1, -10 ** 9
    for a, b in zip(is_.tolist(), ts.tolist()):
        if a != last_i:
            last_i, last_t = a, b
            continue
        if b < last_t + CAP:
            drop += 1
        else:
            last_t = b
    return drop / t.size


def member_stats(name, t, i, F, rot, pools, bucket, rng_A, rng_B, half, draws=DRAWS):
    t, i = np.asarray(t, np.int32), np.asarray(i, np.int32)
    n_raw = int(t.size)
    Fe = F[t, i]
    fin = np.isfinite(Fe)
    n_nan = int((~fin).sum())
    t, i, Fe = t[fin], i[fin], Fe[fin]
    m = int(t.size)
    d = dict(member=name, sig=name.split("/")[0], shape=name.split("/")[1], n_events_raw=n_raw, n_events=m, n_nan_F=n_nan,
             n_names=int(np.unique(i).size), overlap_share=overlap_share(t, i))
    if m < 2:
        d.update(E_bp=None, z_A=None, p_A=1.0, p_B=1.0, TV_bp=None, TV_era1_bp=None, TV_era2_bp=None, degenerate=True)
        return d, None
    E = float(Fe.mean())
    era1 = t < half
    E1 = float(Fe[era1].mean()) if era1.any() else np.nan
    E2 = float(Fe[~era1].mean()) if (~era1).any() else np.nan
    a = control_A(t, i, F, rot, rng_A, draws=draws, half=half)
    A = a["A"]
    p50, sd = float(np.median(A)), float(A.std(ddof=1))
    b = control_B(t, i, F, pools, bucket, rng_B, draws=draws)
    Bd = b["B"]
    top_k = max(1, int(np.ceil(0.01 * m)))
    srt = np.sort(Fe)[::-1]
    tot = float(Fe.sum())
    d.update(E_bp=E * 1e4, E_era1_bp=E1 * 1e4, E_era2_bp=E2 * 1e4, n_era1=int(era1.sum()), n_era2=int((~era1).sum()),
             A_p50_bp=p50 * 1e4, A_p95_bp=float(np.quantile(A, .95)) * 1e4, A_sd_bp=sd * 1e4, A_max_bp=float(A.max()) * 1e4,
             A_nan_cells_per_draw=a["n_nan_cells"] / draws,
             TV_bp=(E - p50) * 1e4, z_A=((E - p50) / sd) if sd > 0 else None, p_A=float((1 + (A >= E).sum()) / (draws + 1)),
             B_p50_bp=float(np.median(Bd)) * 1e4, B_p95_bp=float(np.quantile(Bd, .95)) * 1e4, B_sd_bp=float(Bd.std(ddof=1)) * 1e4,
             p_B=float((1 + (Bd >= E).sum()) / (draws + 1)), B_kept_original=b["n_kept"],
             TV_era1_bp=(E1 - float(np.nanmedian(a["A_era1"]))) * 1e4 if np.isfinite(E1) else None,
             TV_era2_bp=(E2 - float(np.nanmedian(a["A_era2"]))) * 1e4 if np.isfinite(E2) else None,
             top1pct_share=(float(srt[:top_k].sum()) / tot) if tot > 0 else None, top1pct_mean_bp=float(srt[:top_k].mean()) * 1e4,
             sum_F_bp=tot * 1e4, draws=draws, degenerate=False)
    return d, dict(t=t, i=i, Fe=Fe, A_p50=p50, A_sd=sd)


def gate_pass(d):
    return bool(not d.get("degenerate") and d["p_A"] <= GATE_P and d["p_B"] <= GATE_P and (d["TV_era1_bp"] or 0) > 0
                and (d["TV_era2_bp"] or 0) > 0 and d["n_events"] >= GATE_MIN_EVENTS)


def z_key(d):
    return d["z_A"] if d.get("z_A") is not None and np.isfinite(d["z_A"]) else -np.inf


# ------------------------------------------------------------------ shared setup
def setup(P):
    F = np.array(P["F"])
    elig = np.array(P["elig"])
    bucket = np.array(P["bucket_rsi"])
    assert F.shape == elig.shape == bucket.shape == (P["T"], P["n"])
    rot = Rotator(elig)
    pools = BucketPools(elig, bucket)
    return F, elig, bucket, rot, pools


def oracle_events(F, elig, rng, k=20_000):
    """Events on the name-bars whose F is in the name's own top decile over its eligible bars, subsampled to k."""
    Fm = np.where(elig & np.isfinite(F), F, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        thr = np.nanpercentile(Fm, 90, axis=0)
    cells = np.argwhere(np.isfinite(Fm) & (Fm >= thr[None, :]))
    pick = cells[rng.choice(len(cells), size=min(k, len(cells)), replace=False)]
    return pick[:, 0].astype(np.int32), pick[:, 1].astype(np.int32)


def noise_events(F, elig, rng, k=20_000):
    cells = np.argwhere(elig & np.isfinite(F))
    pick = cells[rng.choice(len(cells), size=k, replace=False)]
    return pick[:, 0].astype(np.int32), pick[:, 1].astype(np.int32)


def p_A_of(t, i, F, rot, rng, draws=DRAWS):
    E = float(F[t, i].mean())
    A = control_A(t, i, F, rot, rng, draws=draws)["A"]
    return float((1 + (A >= E).sum()) / (draws + 1)), E, A


def assert_oracle(t, i, F, rot, rng):
    p, E, A = p_A_of(t, i, F, rot, rng)
    assert p < 0.001, f"[O] oracle p_A {p:.4f}"
    return p, E, A


# ------------------------------------------------------------------ the per-score job (process pool: the controls are GIL-bound)
_W = {}


def _init_worker():
    """Each process does its own cache-HIT prep (quietly) and builds the shared grid objects once."""
    with contextlib.redirect_stdout(io.StringIO()):
        P = PREP.prep(need_grids=True, verbose=False)
        F, elig, bucket, rot, pools = setup(P)
        _W.update(P=P, F=F, elig=elig, bucket=bucket, rot=rot, pools=pools, pool=load_pool(P))


def _score_job(args):
    """One score -> its three members' rows and kept event arrays. Seeded per member: identical under any scheduling."""
    sig, draws, half = args
    if not _W:
        _init_worker()
    P, F, elig, bucket, rot, pools, pool = (_W[k] for k in ("P", "F", "elig", "bucket", "rot", "pools", "pool"))
    ev = score_events(P, sig, elig)
    out = []
    for k in SHAPES:
        member = f"{sig}/{k}"
        mi = member_index(pool, member)
        d, kp = member_stats(member, ev[k][0], ev[k][1], F, rot, pools, bucket, np.random.default_rng([SEED, 350, 1, mi]),
                             np.random.default_rng([SEED, 350, 2, mi]), half, draws=draws)
        out.append((member, d, kp))
    return out


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    T, n, r1T, finT, ocT, m_f, m_f_oc = P["T"], P["n"], P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"]
    half = T // 2
    pool = load_pool(P)
    print(f"    family: {len(pool)} scores x {len(SHAPES)} shapes = {len(members_of(pool))} members; pool == every cache key less key/warm/{EXCLUDED}")
    F, elig, bucket, rot, pools = setup(P)
    assert np.array_equal(bucket, V47.bucket_of(P["PCT"]["rsi"])), "bucket_rsi != bucket_of(PCT['rsi'])"
    rng = np.random.default_rng(350)
    # [F] the grid equals a direct per-cell recomputation (D347's loop)
    cells = np.argwhere(np.isfinite(F) & elig)
    sample = cells[rng.choice(len(cells), size=3000, replace=False)]
    worst_f = 0.0
    for t, i in sample:
        v = r1T[t:t + CAP, i].copy()
        mm = m_f[t:t + CAP].copy()
        v[0], mm[0] = ocT[t, i], m_f_oc[t]
        okk = finT[t:t + CAP, i] & np.isfinite(v) & np.isfinite(mm)
        okk[0] = True
        direct = float(np.sum(np.where(okk, v - mm, 0.0)))
        worst_f = max(worst_f, abs(direct - F[t, i]))
    assert worst_f < 1e-9, f"[F] {worst_f:.2e}"
    print(f"    [F] the forward-40 grid equals a direct per-cell recomputation on 3,000 sampled cells to {worst_f:.1e}")
    # [G] the three D347 members reproduce D347's event matrices exactly; [E] on every shape of those scores
    grids, ev3 = {}, {}
    for member, d347 in D347_MEMBERS.items():
        sig = member.split("/")[0]
        LAG = lagged(P, sig)
        assert np.array_equal(LAG, P["LAG"][sig], equal_nan=True), f"[G] lagged {sig} != D347"
        pct = V47.percentile_grid(LAG)
        assert np.array_equal(pct, P["PCT"][sig], equal_nan=True), f"[G] percentile {sig} != D347"
        masks = shape_masks(pct, elig)
        e1 = masks["E1"][0]
        prev = np.full_like(pct, np.nan)
        prev[1:] = pct[:-1]
        with np.errstate(invalid="ignore"):
            lo_d347 = (pct <= V47.DECILE) & (prev > V47.DECILE) & elig       # D347's `lo`, verbatim
        assert np.array_equal(e1, lo_d347) and np.array_equal(e1, P["EVENTS"][d347][0]), f"[G] {member} != D347 events_for"
        assert np.array_equal(masks["E1"][1], P["EVENTS"][d347][1]), f"[G] {member} mirror != D347"
        if sig == "hist_L":
            assert int(e1.sum()) == D347_HIST_L_EVENTS, f"[G] hist_L events {int(e1.sum())}"
        grids[sig] = (LAG, pct)
        ev3[sig] = {k: sparse_events(masks[k][0]) for k in SHAPES}
        print(f"    [G] {member:10s}: lagged score, percentile grid and E1 matrix equal D347's events_for({d347}) exactly "
              f"({int(e1.sum()):,} events; mirror {int(masks['E1'][1].sum()):,})")
    n_e = 0
    for sig, (LAG, pct) in grids.items():
        for k in SHAPES:
            t_ev, i_ev = ev3[sig][k]
            pick = rng.choice(t_ev.size, size=min(300, t_ev.size), replace=False)
            n_unl = 0
            for t, i in zip(t_ev[pick], i_ev[pick]):
                v, v2 = LAG[t], LAG[t - 1]
                fin, fin2 = np.isfinite(v), np.isfinite(v2)
                pd = (float((v[fin] < v[i]).sum()) + 0.5 * float((v[fin] == v[i]).sum())) / fin.sum() * 100.0
                pp = ((float((v2[fin2] < v2[i]).sum()) + 0.5 * float((v2[fin2] == v2[i]).sum())) / fin2.sum() * 100.0) if fin2[i] else np.nan
                if k == "E1":
                    ok = pd <= DECILE + 1e-9 and (pp == pp and pp > DECILE)
                elif k == "E2":
                    ok = pd >= 100 - DECILE - 1e-9 and (pp == pp and pp < 100 - DECILE)
                else:
                    ok = pd > DECILE and (pp == pp and pp <= DECILE + 1e-9)
                assert ok, f"[E] {sig}/{k} ({t},{i}) direct {pd:.3f} prev {pp:.3f}"
                p_t = pct[t + 1, i] if t + 1 < T else np.nan               # the percentile of the score AT t: unlagged
                p_p = pct[t, i]
                if k == "E1":
                    unl = p_t == p_t and p_t <= DECILE and p_p > DECILE
                elif k == "E2":
                    unl = p_t == p_t and p_t >= 100 - DECILE and p_p < 100 - DECILE
                else:
                    unl = p_t == p_t and p_t > DECILE and p_p <= DECILE
                n_unl += not unl
            assert n_unl == pick.size, f"[E] {sig}/{k}: the unlagged condition holds on {pick.size - n_unl} sampled events"
            n_e += pick.size
    print(f"    [E] {n_e} sampled events ({len(grids)} scores x 3 shapes x 300) satisfy their shape on the raw lagged score by direct "
          f"count at t-1 and t-2, and every one fails the unlagged condition ({el()})")
    del grids
    # [SP] sparse gather == dense rotation-then-mask, 20 draws on 5 members, and on a tie-heavy synthetic grid; [A] alongside
    five = [("hist_L", "E1"), ("rev_21", "E1"), ("rsi", "E1"), ("rsi", "E3"), ("rev_21", "E2")]
    rng_sp = np.random.default_rng([SEED, 350, 7])
    worst = 0.0
    for sig, k in five:
        t_ev, i_ev = ev3[sig][k]
        worst = max(worst, assert_sparse_equals_dense(t_ev, i_ev, F, rot, elig, rng_sp, 20, dense_rotate_within_elig, f"{sig}/{k}"))
    Ts, ns = 90, 7
    rs = np.random.default_rng(3507)
    el_s = rs.random((Ts, ns)) > 0.3
    el_s[:6] = False
    el_s[:, 6] = False                                             # a name with no eligible bars
    el_s[40:, 5] = False
    F_s = rs.integers(-2, 3, size=(Ts, ns)).astype(float)         # tie-heavy: five distinct values
    F_s[-3:] = np.nan
    ev_s = el_s & (rs.random((Ts, ns)) < 0.3)
    ts_, is_ = sparse_events(ev_s)
    rot_s = Rotator(el_s)
    assert_sparse_equals_dense(ts_, is_, F_s, rot_s, el_s, rs, 20, dense_rotate_within_elig, "synthetic")
    print(f"    [SP] the sparse control-A gather equals the dense per-name roll within eligible bars: identical cell sets and means "
          f"on 20 draws x 5 members (statistic vs dense mean within {worst:.1e}) and on a tie-heavy {Ts}x{ns} synthetic grid")
    print(f"    [A] every name's event count is preserved under A on every one of those draws (rotated index arrays)")
    # [B] date and bucket preserved, name changed, distinct within (day, bucket) where the pool allows
    rng_b = np.random.default_rng([SEED, 350, 8])
    for sig, k in five:
        t_ev, i_ev = ev3[sig][k]
        fin = np.isfinite(F[t_ev, i_ev])
        t_ev, i_ev = t_ev[fin], i_ev[fin]
        b = control_B(t_ev, i_ev, F, pools, bucket, rng_b, draws=3, block=3, return_last=True)
        L = b["last"]
        assert np.array_equal(np.sort(L["t"]), np.sort(t_ev)), f"[B] {sig}/{k} dates"
        assert np.array_equal(bucket[L["t"], L["i_new"]], bucket[L["t"], L["i_orig"]]), f"[B] {sig}/{k} bucket"
        changed = float((L["i_new"] != L["i_orig"]).mean())
        kept = b["n_kept"] / t_ev.size
        # WEAKENED from "> 99% changed": rsi/E1's events sit in the smallest rsi buckets (bucket 0 is ~2% of names), so
        # the same-day same-bucket pool runs out on ~4% of them -- the declared fallback keeps the original, counted.
        # Asserted instead: every event the pool could replace WAS replaced, and the shortfall is exactly the kept count.
        assert (L["i_new"][L["sample"]] != L["i_orig"][L["sample"]]).all(), f"[B] {sig}/{k} a sampled event kept its name"
        assert abs(changed + kept - 1.0) < 1e-12, f"[B] {sig}/{k} changed {changed:.4f} + kept {kept:.4f} != 1"
        assert changed > 0.99 or kept > 0.0, f"[B] {sig}/{k} name changed on {100 * changed:.2f}%"
        comp = L["gid"].astype(np.int64) * n + L["i_new"]
        assert np.unique(comp[L["sample"]]).size == int(L["sample"].sum()), f"[B] {sig}/{k} duplicate within a (day, bucket) group"
        assert not (np.isin(L["t"] * n + L["i_new"], t_ev.astype(np.int64) * n + i_ev)[L["sample"]]).any(), f"[B] {sig}/{k} replacement is an event name"
        print(f"    [B] {sig}/{k:3s}: every event keeps its date and rsi bucket; name changed on {100 * changed:.2f}% "
              f"({b['n_kept']} = {100 * kept:.2f}% kept for want of pool, the declared fallback); replacements distinct per day and bucket "
              f"and never an event name")
    # [O] the hurdle has teeth: the oracle clears A at p < 0.001; noise does not (<= 3 of 20 seeds below 0.05)
    rng_o = np.random.default_rng([SEED, 350, 9])
    t_or, i_or = oracle_events(F, elig, rng_o)
    p_or, E_or, A_or = assert_oracle(t_or, i_or, F, rot, rng_o)
    p_noise = []
    for s in range(20):
        r = np.random.default_rng([SEED, 350, 10, s])
        t_n, i_n = noise_events(F, elig, r)
        p_noise.append(p_A_of(t_n, i_n, F, rot, r)[0])
    n_low = int(sum(p < 0.05 for p in p_noise))
    assert n_low <= 3, f"[O] noise below 0.05 on {n_low} of 20 seeds"
    print(f"    [O] the oracle ({t_or.size:,} top-decile-F events) clears control A at p = {p_or:.4f} (E {E_or * 1e4:+.0f} bp vs A max "
          f"{A_or.max() * 1e4:+.0f}); the noise series is below 0.05 on {n_low} of 20 seeds (p50 of its p_A {np.median(p_noise):.2f}) ({el()})")
    # [M] on synthetic series: identity -> M_eff = 138; identical rows -> 1; random -> in range and symmetric
    rs = np.random.default_rng(35011)
    S = rs.normal(size=(138, 400))
    S[rs.random(S.shape) < 0.3] = np.nan
    C, n_bad = pairwise_corr(S)
    liji, nyh, _, liji_abs = assert_M(C, "synthetic")
    C_id = np.eye(138)
    assert abs(m_eff_of(C_id)[0] - 138) < 1e-9 and abs(m_eff_of(C_id)[1] - 138) < 1e-9, "[M] identity"
    C_one = np.ones((138, 138))
    l1, n1, _, l1_abs = m_eff_of(C_one)
    # The rank-one matrix's 137 zero eigenvalues come out of eigvalsh as +-1e-15; d321b's verbatim term reads a NEGATIVE
    # one as e - floor(e) = 1 - 1e-15 (it gave 68.0 here), so the rank-one check is on Li & Ji's |lambda| form, which is
    # discontinuous at integers (137.999... reads as 1 + 0.999...) and so is allowed [1, 2]. The verbatim value is printed.
    assert 1.0 - 1e-9 <= l1_abs <= 2.0 + 1e-6 and abs(n1 - 1.0) < 1e-6, f"[M] rank-one {l1_abs} / {n1}"
    print(f"    [M] pairwise-complete correlation: symmetric, unit diagonal; M_eff on 138 independent synthetic series Li-Ji {liji:.1f} "
          f"(|lambda| variant {liji_abs:.1f}) CN {nyh:.1f}; identity -> 138.0 / 138.0; a rank-one matrix -> |lambda| Li-Ji {l1_abs:.1f} / "
          f"CN {n1:.1f} (d321b's verbatim Li-Ji reads its +-1e-15 eigenvalues as {l1:.0f}: negative eigenvalues inflate it; both are reported)")
    # [BH] textbook rejections on synthetic p-vectors
    p1 = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.07, 0.4]
    r1 = bh_reject(p1, 0.05)
    assert r1.tolist() == [True, True, False, False, False, False, False, False], f"[BH] {r1}"    # k/8*0.05: p(3)=.039 > .01875
    r2 = bh_reject([0.04, 0.041, 0.042], 0.10)
    assert r2.all(), "[BH] step-up: p(1) misses its bar but p(3) <= 0.10 rejects all three"
    r3 = bh_reject([0.001, 0.02, 0.021, 0.5], 0.10)
    assert r3.tolist() == [True, True, True, False], "[BH]"
    assert not bh_reject([0.2, 0.5, 0.9], 0.10).any(), "[BH] none"
    print("    [BH] Benjamini-Hochberg recovers the textbook rejections: 2 of 8 at q=.05 on [.001,.008,.039,.041,.042,.06,.07,.4]; "
          "the step-up rejects all of [.04,.041,.042] at q=.10; 3 of 4 on [.001,.02,.021,.5]; none on [.2,.5,.9]")
    # [6] the checks fail when they should
    broke = 0
    try:
        r = np.random.default_rng([SEED, 350, 10, 0])
        t_n, i_n = noise_events(F, elig, r)
        assert_oracle(t_n, i_n, F, rot, r)
    except AssertionError:
        broke += 1
    try:
        t_ev, i_ev = ev3["hist_L"]["E1"]
        assert_sparse_equals_dense(t_ev, i_ev, F, rot, elig, np.random.default_rng(1), 3, lambda e, _el, off: dense_rotate_whole_grid(e, off), "whole-grid")
    except AssertionError:
        broke += 1
    assert broke == 2, f"[6] {broke} of 2 raised"
    print("    [6] [O] raises when the oracle is replaced by noise; [SP] raises on a whole-grid roll that ignores eligibility")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


def stage_screen(P, scores=None, out=SCREEN_OUT, draws=DRAWS, workers=8):
    t_start = time.time()
    el = lambda: f"{time.time() - t_start:.0f}s"
    T, n = P["T"], P["n"]
    half = T // 2
    pool = load_pool(P)
    dev = scores is not None
    scores = scores or pool
    members = [f"{s}/{k}" for s in scores for k in SHAPES]
    F, elig, bucket, rot, pools = setup(P)
    print(f"\nSTAGE 1 -- the grid: {len(members)} members, {draws} draws per control; F finite on {int(np.isfinite(F).sum()):,} cells, "
          f"eligible {int(elig.sum()):,}; era midpoint bar {half} ({P['dates'][half]})")
    # phases 1-2: per score, the percentile grid (built, used for the three shapes, dropped) and each member's controls.
    # GIL-bound (many small numpy ops per draw), so processes, not threads; the result is seeded per member.
    jobs = [(s, draws, half) for s in scores]
    if workers > 1:
        with mp.get_context("spawn").Pool(workers, initializer=_init_worker) as pl:
            results = pl.map(_score_job, jobs, chunksize=1)
    else:
        _W.update(P=P, F=F, elig=elig, bucket=bucket, rot=rot, pools=pools, pool=pool)
        results = [_score_job(j) for j in jobs]
    res = {member: (d, kp) for r in results for member, d, kp in r}
    rows = [res[m][0] for m in members]
    keep = {m: res[m][1] for m in members}
    print(f"  events and controls A and B done for {len(members)} members on {workers} worker{'s' if workers > 1 else ''} ({el()}); "
          f"degenerate (fewer than 2 finite-F events): {sum(1 for d in rows if d.get('degenerate'))}")
    # phase 3: the family-wise grid-max under ONE shared offset vector per draw
    live = [m for m in members if keep[m] is not None and keep[m]["A_sd"] > 0]
    rng_g = np.random.default_rng([SEED, 350, 3])
    maxz, done = [], 0
    while done < draws:
        B = min(50, draws - done)
        off = rot.draw_offsets(rng_g, B)
        Z = np.full((B, len(live)), -np.inf)
        for j, m in enumerate(live):
            km = keep[m]
            Er = _nanmean_rows(F[rot.rotate(km["t"], km["i"], off), km["i"][None, :]])
            Z[:, j] = (Er - km["A_p50"]) / km["A_sd"]
        maxz.append(Z.max(axis=1))
        done += B
    maxz = np.concatenate(maxz)
    ranked = sorted(rows, key=z_key, reverse=True)
    best = ranked[0]
    n_ge = int((maxz >= best["z_A"]).sum()) if best.get("z_A") is not None else None
    p_max = (n_ge / draws) if n_ge is not None else None
    print(f"  grid-max: best member {best['member']} z_A {best['z_A']:+.2f}; max-z over the family per draw p50 {np.median(maxz):+.2f} "
          f"p95 {np.quantile(maxz, .95):+.2f} max {maxz.max():+.2f}; p_max {p_max:.3f} ({n_ge} of {draws} draws) ({el()})")
    # phase 4: M_eff from the daily mean-F event series
    S = np.full((len(members), T), np.nan)
    for j, m in enumerate(members):
        if keep[m] is not None:
            S[j] = daily_series(keep[m]["t"], keep[m]["Fe"], T)
    C, n_bad = pairwise_corr(S)
    liji, nyh, eig, liji_abs = assert_M(C, "family")
    iu = np.triu_indices(len(members), 1)
    n_neg = int((eig < -1e-9).sum())
    print(f"    [M] correlation of {len(members)} daily mean-F series: symmetric, unit diagonal; {n_bad} pairs with < 10 common days set to 0; "
          f"pairwise median {np.median(C[iu]):+.3f} max {C[iu].max():+.3f}; M_eff Li-Ji {liji:.1f}, Cheverud-Nyholt {nyh:.1f} (nominal {len(members)}); "
          f"{n_neg} negative eigenvalues (min {eig.min():+.3f}); Li-Ji on |lambda| {liji_abs:.1f}")
    # phase 5: BH and the gate
    pA = np.array([d["p_A"] for d in rows])
    rej = bh_reject(pA, BH_Q)
    for d, r in zip(rows, rej):
        d["bh_reject"] = bool(r)
        d["gate_pass"] = gate_pass(d)
    passers = [d for d in ranked if d["gate_pass"]][:GATE_TOP]
    fallback = not passers
    survivors = [d["member"] for d in (passers if passers else [d for d in ranked if not d.get("degenerate")][:FALLBACK_TOP])]
    n_p05 = int((pA <= GATE_P).sum())
    d347 = {m: next(j for j, d in enumerate(ranked) if d["member"] == m) + 1 for m in D347_MEMBERS if m in members}
    # ---- print ----
    print("\n" + "=" * 150)
    print(f"THE GRID -- forward-40 hedged excess per event (bp), every event counted; A = own names at random times, B = same day same rsi bucket")
    print("=" * 150)
    hdr = "  %4s %-20s %6s %5s %5s %7s %7s %7s %7s %6s %6s %6s %7s %7s %6s %4s" % (
        "rank", "member", "n", "names", "ovl%", "E", "A p50", "A p95", "TV", "z_A", "p_A", "p_B", "TV e1", "TV e2", "top1%", "gate")
    print(hdr)
    show = list(range(min(20, len(ranked)))) + [r - 1 for r in d347.values() if r > 20]
    for j in show:
        d = ranked[j]
        if d.get("degenerate"):
            print("  %4d %-20s %6d  degenerate" % (j + 1, d["member"], d["n_events"]))
            continue
        print("  %4d %-20s %6d %5d %5.1f %+7.1f %+7.1f %+7.1f %+7.1f %+6.2f %6.3f %6.3f %+7.1f %+7.1f %6s %4s" % (
            j + 1, d["member"], d["n_events"], d["n_names"], 100 * d["overlap_share"], d["E_bp"], d["A_p50_bp"], d["A_p95_bp"], d["TV_bp"],
            z_key(d), d["p_A"], d["p_B"], d["TV_era1_bp"] or 0, d["TV_era2_bp"] or 0,
            ("%.0f%%" % (100 * d["top1pct_share"])) if d["top1pct_share"] is not None else "-", "PASS" if d["gate_pass"] else ""))
    print(f"\n  D347's members rank: " + ", ".join(f"{m} #{r}" for m, r in d347.items()))
    print(f"  members with p_A <= 0.05: {n_p05} of {len(members)}; BH at q={BH_Q} rejects {int(rej.sum())}"
          + (": " + ", ".join(d["member"] for d in ranked if d["bh_reject"]) if rej.any() else ""))
    print(f"  M_eff Li-Ji {liji:.1f} / Cheverud-Nyholt {nyh:.1f}; false discovery alone at 0.05 gives {0.05 * liji:.1f} / {0.05 * nyh:.1f}")
    print(f"  grid-max p for {best['member']}: {p_max:.3f} ({n_ge} of {draws} shared-offset draws reach its z_A)")
    print(f"  GATE (p_A <= .05, p_B <= .05, TV > 0 both eras, n >= 2000; top {GATE_TOP} by z_A): "
          + (f"{len(passers)} pass -> {survivors}" if passers else f"NONE pass -> fallback top {FALLBACK_TOP} by z_A {survivors}"))
    q = grid_predictions(rows, liji, nyh, p_max, int(rej.sum()))
    print("\nPRELIMINARY (grid-only) PREDICTIONS -- Q1, Q7, Q8 need the kernel (--report)")
    print_grid_predictions(q, rows, liji, nyh, n_p05, p_max, int(rej.sum()))
    out_d = dict(note="D350 stage 1: the grid. 138 members = 46 scores x 3 shapes scored on the forward-40 hedged-excess grid against "
                      "control A (own names at random times, sparse rotation within eligible bars) and control B (same day, same rsi "
                      "bucket, another name). Every event counted (the kernel drops overlaps: overlap_share). Nothing is a book.",
                 pool=pool, shapes=SHAPES, excluded=EXCLUDED, draws=draws, cap=CAP, decile=DECILE, era_midpoint_bar=half,
                 era_midpoint_date=P["dates"][half], members=rows, ranked=[d["member"] for d in ranked],
                 gate=dict(p=GATE_P, min_events=GATE_MIN_EVENTS, top=GATE_TOP, n_pass=len(passers), survivors=survivors, fallback=fallback),
                 n_pA_le_05=n_p05, bh=dict(q=BH_Q, n_reject=int(rej.sum()), rejected=[d["member"] for d in ranked if d["bh_reject"]]),
                 m_eff=dict(li_ji=liji, cheverud_nyholt=nyh, li_ji_abs_lambda=liji_abs, eigen_top5=[float(e) for e in eig[:5]],
                            eigen_min=float(eig.min()), n_negative_eigen=n_neg, pairs_zeroed=n_bad,
                            corr_median=float(np.median(C[iu])), corr_max=float(C[iu].max())),
                 grid_max=dict(draws=draws, best_member=best["member"], best_z=best.get("z_A"), p_max=p_max, n_draws_ge_best=n_ge,
                               max_z_p50=float(np.median(maxz)), max_z_p95=float(np.quantile(maxz, .95)), max_z_max=float(maxz.max())),
                 d347_ranks=d347, predictions_grid=q, elapsed_s=time.time() - t_start, dev=dev)
    out.write_text(json.dumps(clean(out_d), indent=1))
    print(f"\nwrote {out.relative_to(REPO)}  (screen {el()}; total {time.time() - P['t0']:.0f}s)")
    return out_d


def grid_predictions(rows, liji, nyh, p_max, n_bh):
    pA = np.array([d["p_A"] for d in rows])
    n_p05 = int((pA <= GATE_P).sum())
    q = {}
    q["Q2"] = bool(n_p05 <= 0.05 * liji + 2)
    q["Q2_cheverud_nyholt"] = bool(n_p05 <= 0.05 * nyh + 2)
    q["Q3"] = not any((d.get("TV_bp") or 0) > 0 for d in rows if d["shape"] == "E1" and d["sig"] in REVERSAL)
    q["Q4"] = any((d.get("TV_bp") or 0) > 0 and d["p_A"] <= GATE_P for d in rows if d["shape"] == "E3")
    q["Q5"] = bool(p_max is not None and p_max > 0.05)
    q["Q6"] = bool(n_bh == 0)
    return q


def print_grid_predictions(q, rows, liji, nyh, n_p05, p_max, n_bh):
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    rev = [d for d in rows if d["shape"] == "E1" and d["sig"] in REVERSAL and not d.get("degenerate")]
    e3 = sorted([d for d in rows if d["shape"] == "E3" and not d.get("degenerate")], key=z_key, reverse=True)[:3]
    print(f"  Q2 members at p_A <= .05 within false discovery (<= 0.05 x M_eff + 2): {v(q['Q2'])} -- {n_p05} vs {0.05 * liji + 2:.1f} (Li-Ji)"
          f"; {v(q['Q2_cheverud_nyholt'])} vs {0.05 * nyh + 2:.1f} (Cheverud-Nyholt)")
    print(f"  Q3 no E1 member on a reversal score has TV > 0: {v(q['Q3'])} -- " + ", ".join(f"{d['member']} {d['TV_bp']:+.1f}" for d in rev))
    print(f"  Q4 some E3 member has TV > 0 at p_A <= .05: {v(q['Q4'])} -- best E3: " + ", ".join(f"{d['member']} TV {d['TV_bp']:+.1f} p {d['p_A']:.3f}" for d in e3))
    print(f"  Q5 the family-wise grid-max p of the best member > 0.05: {v(q['Q5'])} -- p_max {p_max:.3f}")
    print(f"  Q6 BH at q=0.10 over the family rejects zero: {v(q['Q6'])} -- rejects {n_bh}")


# ------------------------------------------------------------------ stage 2: the kernel
def member_dense(P, member, elig):
    sig, shape = member.split("/")
    pct = V47.percentile_grid(lagged(P, sig))
    lo, hi = shape_masks(pct, elig)[shape]
    return np.ascontiguousarray(lo), np.ascontiguousarray(hi), exit_score(pct, shape)


def ctrl_path(member, part):
    return Path(str(CTRL).format(member=member.replace("/", "-"), part=part))


def stage_kernel(P, member, draws, part):
    pool = load_pool(P)
    assert member in members_of(pool), member
    mi = member_index(pool, member)
    elig = np.array(P["elig"])
    lo, hi, sc = member_dense(P, member, elig)
    res = V47.run_events(P, lo, np.zeros_like(lo), sc, "cap")
    obs = float(V47.pnl_bp(res).mean())
    print(f"\n  {member} part {part}: {int(lo.sum()):,} events -> {len(res['trades']):,} trades; observed mean hedged excess (cap exit) {obs:+.2f} bp")
    rngA = np.random.default_rng([SEED, 350, 4, mi, part])
    rngB = np.random.default_rng([SEED, 350, 5, mi, part])
    rngA2 = np.random.default_rng([SEED, 350, 6, mi, part])
    A_, B_, A2_ = [], [], []
    ts = time.time()
    for d in range(draws):
        sl_, ss_, sc_ = V47.rotate_confined(P, lo, hi, sc, rngA)          # control A as pre-registered: D347's, within finT
        rA = V47.run_events(P, sl_, np.zeros_like(lo), sc_, "cap")
        pa = V47.pnl_bp(rA)
        assert np.isfinite(pa).all(), "[A] NaN in a rotated draw"
        A_.append(float(pa.mean()))
        # control A' (D351): the same rotation WITHIN THE FLOORED UNIVERSE -- every rotated event is a bar the strategy could trade.
        # D347's finT rotation lands ~13% of hist_L's events on sub-$5 / illiquid bars whose forward excess averages +65 bp.
        sl2, ss2, sc2 = PREP.EB.rotate_signals(lo, hi, sc, elig, rngA2)
        assert not (sl2 & ~elig).any(), "[A'] a rotated event landed off the floor"
        assert np.array_equal(sl2.sum(axis=0), lo.sum(axis=0)), "[A'] per-name event count changed"
        rA2 = V47.run_events(P, sl2, np.zeros_like(lo), sc2, "cap")
        pa2 = V47.pnl_bp(rA2)
        assert np.isfinite(pa2).all(), "[A'] NaN in a rotated draw"
        A2_.append(float(pa2.mean()))
        sB = V47.control_b_signal(P, lo, rngB)
        rB = V47.run_events(P, sB, np.zeros_like(lo), sc, "cap")
        B_.append(float(V47.pnl_bp(rB).mean()))
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {member}: {d + 1}/{draws} ({time.time() - ts:.0f}s)", flush=True)
    out = dict(member=member, draws=draws, part=part, observed=obs, trades=len(res["trades"]), events=int(lo.sum()), control_A=A_, control_B=B_,
               control_A_elig=A2_)
    f = ctrl_path(member, part)
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A p50 {np.median(A_):+.2f} p95 {np.quantile(A_, .95):+.2f}; A' (floored) p50 {np.median(A2_):+.2f} p95 "
          f"{np.quantile(A2_, .95):+.2f}; B p50 {np.median(B_):+.2f} p95 {np.quantile(B_, .95):+.2f} ({time.time() - P['t0']:.0f}s)")


def four_groups(tr, pnl, P, elig):
    """The four groups per trade (CLAUDE.md): distribution, both-tail trims, what the winners depend on, the top trade named."""
    m = pnl.size
    rows = np.array([t[0] for t in tr])
    e0s = np.array([t[1] for t in tr])
    ages = np.array([t[2] for t in tr])
    wins, loss = pnl[pnl > 0], pnl[pnl < 0]
    sd = pnl.std(ddof=1)
    z = (pnl - pnl.mean()) / sd if sd > 0 else np.zeros_like(pnl)
    k = max(1, int(np.floor(0.01 * m)))
    srt = np.sort(pnl)
    per_name = np.bincount(rows, weights=pnl, minlength=P["n"])
    tot = float(pnl.sum())
    desc = np.sort(per_name)[::-1]
    csum = np.cumsum(desc)
    names_half = int(np.searchsorted(csum, 0.5 * tot) + 1) if tot > 0 else None
    yrs = P["years"][e0s]
    by_year = {int(y): float(pnl[yrs == y].sum()) for y in np.unique(yrs)}
    j = int(np.argmax(pnl))
    row, e0 = int(rows[j]), int(e0s[j])
    dv = P["DV"][e0]
    ok = elig[e0] & np.isfinite(dv)
    dv_pct = float((dv[ok] < dv[row]).mean() * 100.0) if np.isfinite(dv[row]) and ok.any() else None
    price = P["RAW_CLOSE"][e0s, rows]
    dead = P["last_live"][rows] < P["T"] - 1
    med_px = float(np.nanmedian(price))
    lo_px = price <= med_px
    return dict(count=int(m), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)), win_rate=float((pnl > 0).mean()),
                payoff=(float(wins.mean() / -loss.mean()) if wins.size and loss.size else None), hold_mean=float(ages.mean()),
                hold_median=float(np.median(ages)), skew=float((z ** 3).mean()), kurtosis_excess=float((z ** 4).mean() - 3.0),
                trim_k=k, mean_ex_top_bp=float(srt[:-k].mean()), mean_ex_bottom_bp=float(srt[k:].mean()), mean_trimmed_bp=float(srt[k:-k].mean()),
                names_to_half_pnl=names_half, n_names=int((np.bincount(rows, minlength=P["n"]) > 0).sum()),
                top_name_share={str(kk): (float(desc[:kk].sum() / tot) if tot > 0 else None) for kk in (1, 5, 10)},
                profitable_years_share=float(np.mean([v > 0 for v in by_year.values()])), years=len(by_year),
                top_trade=dict(symbol=P["symbols"][row], entry_date=P["dates"][e0], as_traded_price=float(price[j]), hold=int(ages[j]),
                               pnl_bp=float(pnl[j]), share_of_pnl=(float(pnl[j] / tot) if tot > 0 else None), dv_percentile_at_entry=dv_pct),
                split_dead_alive=dict(dead_n=int(dead.sum()), dead_mean_bp=float(pnl[dead].mean()) if dead.any() else None,
                                      alive_n=int((~dead).sum()), alive_mean_bp=float(pnl[~dead].mean()) if (~dead).any() else None),
                split_price=dict(median_price=med_px, low_n=int(lo_px.sum()), low_mean_bp=float(pnl[lo_px].mean()) if lo_px.any() else None,
                                 high_n=int((~lo_px).sum()), high_mean_bp=float(pnl[~lo_px].mean()) if (~lo_px).any() else None))


def stage_report(P):
    assert SCREEN_OUT.exists(), "run --screen first"
    screen = json.loads(SCREEN_OUT.read_text())
    pool = load_pool(P)
    survivors, fallback = screen["gate"]["survivors"], screen["gate"]["fallback"]
    by_member = {d["member"]: d for d in screen["members"]}
    r1T, finT, ocT, m_f, m_f_oc, beta, F = P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"], P["beta"], P["F"]
    HALF, CLOSE, years, T = P["HALF"], P["CLOSE"], P["years"], P["T"]
    bucket_rsi = np.array(P["bucket_rsi"])
    elig = np.array(P["elig"])
    down = set(P["down_years"])
    half = T // 2
    Fm = elig & np.isfinite(F)
    E_all = float(np.nanmean(F[Fm])) * 1e4
    E_b = {}
    for b in range(10):
        mb = Fm & (bucket_rsi == b)
        E_b[b] = float(np.nanmean(F[mb])) * 1e4 if mb.any() else np.nan
    print(f"\nSTAGE 2 -- the kernel on {'the gate survivors' if not fallback else 'the FALLBACK top 3 by z_A (nothing passed the gate)'}: {survivors}")
    print(f"  BASE RATES: forward-40 hedged excess, all floored name-bars {E_all:+.1f} bp; by rsi bucket: " + " ".join(f"b{b}:{E_b[b]:+.0f}" for b in range(10)))
    REPORT = {}
    rngC = np.random.default_rng([SEED, 350, 6])
    for member in survivors:
        lo, hi, sc = member_dense(P, member, elig)
        R_ = {}
        for lens, sl, ss in (("long", lo, np.zeros_like(lo)), ("mirror", np.zeros_like(hi), hi)):
            for exit_ in ("cap", "invalidation"):
                res = V47.run_events(P, sl, ss, sc, exit_)
                tr = res["trades"]
                pnl = V47.pnl_bp(res)
                pb = V47.pnl_beta_adjusted(tr, r1T, m_f, ocT, m_f_oc, beta) * 1e4
                yrs = np.array([years[t[1]] for t in tr])
                eras = np.array([t[1] < half for t in tr])
                c2 = {cv: V47.two_c(tr, HALF[cv], CLOSE) for cv in CONVS}
                d_ = dict(events=int(sl.sum() + ss.sum()), trades=len(tr), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                          t=float(pnl.mean() / (pnl.std(ddof=1) / np.sqrt(pnl.size))), share_pos=float((pnl > 0).mean()),
                          hold_mean=float(np.mean([t[2] for t in tr])),
                          beta_adj_mean_bp=float(np.nanmean(pb)), beta_median=float(np.nanmedian([beta[t[1], t[0]] for t in tr])),
                          two_c={cv: c2[cv][0] for cv in CONVS}, net_per_trade={cv: float(pnl.mean()) - c2[cv][0] for cv in CONVS},
                          held_half={cv: c2[cv][1] for cv in CONVS}, held_price=c2["PUB"][2],
                          down_years_mean_bp=(float(pnl[np.isin(yrs, list(down))].mean()) if np.isin(yrs, list(down)).any() else None),
                          down_years_n=int(np.isin(yrs, list(down)).sum()),
                          era1_mean_bp=float(pnl[eras].mean()) if eras.any() else None, era2_mean_bp=float(pnl[~eras].mean()) if (~eras).any() else None,
                          by_year={int(y): float(pnl[yrs == y].mean()) for y in np.unique(yrs)},
                          four_groups=four_groups(tr, pnl, P, elig))
                if lens == "long" and exit_ == "cap":
                    b_ev = np.array([bucket_rsi[t[1], t[0]] for t in tr])
                    Es = float(pnl.mean())
                    inter = {}
                    tot = 0.0
                    for b in range(10):
                        mb = b_ev == b
                        if mb.any():
                            Esb = float(pnl[mb].mean())
                            inter[b] = dict(n=int(mb.sum()), E_sb=Esb, E_b=E_b[b], interaction=Esb - E_b[b] - Es + E_all)
                            tot += mb.sum() * (Esb - Es)
                    assert abs(tot) < 1e-9 * max(1.0, float(np.abs(pnl).sum())), f"[X] {member} {tot}"
                    assert sum(v["n"] for v in inter.values()) == len(tr), f"[X] {member} buckets do not partition the trades"
                    print(f"    [X] {member}: the buckets partition the {len(tr):,} trades and sum_b n_b (E_sb - E_s) = {tot:.2e}")
                    d_["interaction"] = inter
                    signs = rngC.choice([-1.0, 1.0], size=(1000, pnl.size))
                    cC = (signs * pnl[None, :]).mean(axis=1)
                    d_["control_C"] = dict(p50=float(np.median(cC)), p95=float(np.quantile(cC, .95)), max=float(cC.max()), draws=1000,
                                           above=bool(Es > np.quantile(cC, .95)))
                R_[f"{lens}/{exit_}"] = d_
        parts = sorted(REPO.glob(f"data/d350_ctrl_{member.replace('/', '-')}_p*.json"))
        if parts:
            cs_ = [json.loads(p.read_text()) for p in parts]
            obs = R_["long/cap"]["mean_bp"]
            for c in cs_:
                assert abs(c["observed"] - obs) < 1e-9, f"observed differs between stages for {member}"
            A_ = np.concatenate([np.array(c["control_A"]) for c in cs_])
            B_ = np.concatenate([np.array(c["control_B"]) for c in cs_])
            A2_ = np.concatenate([np.array(c["control_A_elig"]) for c in cs_ if "control_A_elig" in c]) if any("control_A_elig" in c for c in cs_) else None
            R_["controls"] = dict(draws=int(sum(c["draws"] for c in cs_)), parts=[p.name for p in parts],
                                  A=dict(p50=float(np.median(A_)), p95=float(np.quantile(A_, .95)), max=float(A_.max()),
                                         distinct=int(len(set(A_.tolist()))), above=bool(obs > np.quantile(A_, .95))),
                                  B=dict(p50=float(np.median(B_)), p95=float(np.quantile(B_, .95)), max=float(B_.max()),
                                         distinct=int(len(set(B_.tolist()))), above=bool(obs > np.quantile(B_, .95))))
            if A2_ is not None and A2_.size:
                R_["controls"]["A_elig"] = dict(p50=float(np.median(A2_)), p95=float(np.quantile(A2_, .95)), max=float(A2_.max()),
                                                distinct=int(len(set(A2_.tolist()))), above=bool(obs > np.quantile(A2_, .95)))
        R_["grid"] = by_member[member]
        REPORT[member] = R_

    # ---- print ----
    print("\n" + "=" * 130)
    print("THE SURVIVORS UNDER THE KERNEL -- every event taken, next-open fill, hedged against the floored market; bp per trade")
    print("=" * 130)
    print("  %-14s %-6s %-12s %6s %6s %8s %8s %6s %7s %8s %9s %9s %8s %9s" % ("member", "side", "exit", "events", "n", "mean", "median", "t", "hold",
                                                                          "beta-adj", "net PUB", "net PB", "down-yr", "eras"))
    for member in survivors:
        for key, d_ in REPORT[member].items():
            if key in ("controls", "grid"):
                continue
            lens, exit_ = key.split("/")
            print("  %-14s %-6s %-12s %6d %6d %+8.1f %+8.1f %+6.2f %7.1f %+8.1f %+9.1f %+9.1f %8s %9s" % (
                member, lens, exit_, d_["events"], d_["trades"], d_["mean_bp"], d_["median_bp"], d_["t"], d_["hold_mean"], d_["beta_adj_mean_bp"],
                d_["net_per_trade"]["PUB"], d_["net_per_trade"]["PB"],
                ("%+.0f" % d_["down_years_mean_bp"]) if d_["down_years_mean_bp"] is not None else "-",
                "%+.0f/%+.0f" % (d_["era1_mean_bp"] or 0, d_["era2_mean_bp"] or 0)))
    print(f"\n  down-years (floored market negative): {P['down_years']}")
    print("\n  CONTROLS on the long cap-exit statistic (mean hedged excess, bp) -- grid (stage 1) beside kernel (stage 2):")
    print("  %-14s %8s %8s %6s | %8s %8s %8s %4s %6s | %8s %8s %8s %4s %6s | %8s %8s %6s" % (
        "member", "grid E", "grid TV", "p_A", "A p50", "A p95", "A max", "dist", "above", "B p50", "B p95", "B max", "dist", "above", "C p95", "C max", "above"))
    for member in survivors:
        R_, g = REPORT[member], REPORT[member]["grid"]
        c, cc = R_.get("controls"), R_["long/cap"]["control_C"]
        if c:
            print("  %-14s %+8.1f %+8.1f %6.3f | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %6s" % (
                member, g["E_bp"], g["TV_bp"], g["p_A"], c["A"]["p50"], c["A"]["p95"], c["A"]["max"], c["A"]["distinct"], "yes" if c["A"]["above"] else "NO",
                c["B"]["p50"], c["B"]["p95"], c["B"]["max"], c["B"]["distinct"], "yes" if c["B"]["above"] else "NO",
                cc["p95"], cc["max"], "yes" if cc["above"] else "NO"))
        else:
            print(f"  {member:14s} {g['E_bp']:+8.1f} {g['TV_bp']:+8.1f} {g['p_A']:6.3f} | kernel controls A/B not run (--kernel); C p95 {cc['p95']:+.2f} "
                  f"{'yes' if cc['above'] else 'NO'}")
    print("\n  FOUR GROUPS per trade (long, cap exit):")
    for member in survivors:
        g4 = REPORT[member]["long/cap"]["four_groups"]
        tt = g4["top_trade"]
        print(f"  {member}: n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% payoff "
              f"{g4['payoff'] if g4['payoff'] is None else round(g4['payoff'], 2)} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}")
        print(f"      trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f}  ex-bottom {g4['mean_ex_bottom_bp']:+.1f}  trimmed {g4['mean_trimmed_bp']:+.1f}")
        print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
              + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
              + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}")
        print(f"      TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} (DV pct {tt['dv_percentile_at_entry'] if tt['dv_percentile_at_entry'] is None else round(tt['dv_percentile_at_entry'], 1)}), "
              f"held {tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = {('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
        sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
        print(f"      splits: dead {sd_['dead_n']} {sd_['dead_mean_bp'] if sd_['dead_mean_bp'] is None else round(sd_['dead_mean_bp'], 1)} / alive {sd_['alive_n']} "
              f"{sd_['alive_mean_bp'] if sd_['alive_mean_bp'] is None else round(sd_['alive_mean_bp'], 1)}; price <= ${sp_['median_price']:.2f} "
              f"{sp_['low_n']} {round(sp_['low_mean_bp'], 1) if sp_['low_mean_bp'] is not None else '-'} / above {sp_['high_n']} {round(sp_['high_mean_bp'], 1) if sp_['high_mean_bp'] is not None else '-'}")
    print("\n  INTERACTION with the rsi ranking (long, cap exit): bucket | n | E[member,bucket] | E[bucket] | interaction")
    for member in survivors:
        inter = REPORT[member]["long/cap"]["interaction"]
        print(f"  {member}: " + " ".join(f"b{b}[{v['n']}] {v['E_sb']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(inter.items())))
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")

    # ---- predictions ----
    def kernel_above_all(member):
        R_ = REPORT[member]
        c = R_.get("controls")
        return bool(c and c["A"]["above"] and c["B"]["above"] and R_["long/cap"]["control_C"]["above"])

    def inter_mean(member, buckets):
        inter = REPORT[member]["long/cap"]["interaction"]
        sel = [inter[b] for b in buckets if b in inter]
        return (sum(v["n"] * v["interaction"] for v in sel) / sum(v["n"] for v in sel)) if sel else None

    def kernel_above_all_elig(member):
        """Q1 under control A' (D351): the rotation within the floored universe, beside the pre-registered finT rotation."""
        R_ = REPORT[member]
        c = R_.get("controls")
        return bool(c and "A_elig" in c and c["A_elig"]["above"] and c["B"]["above"] and R_["long/cap"]["control_C"]["above"])

    kernel_surv = [m for m in survivors if kernel_above_all(m)]
    gate_kernel = [m for m in kernel_surv if not fallback]
    kernel_surv_elig = [m for m in survivors if kernel_above_all_elig(m)]
    print("\n  CONTROL A (pre-registered, D347's rotation within finT) beside A' (D351: within the floored universe), kernel, cap exit, bp per trade:")
    for m in survivors:
        c = REPORT[m].get("controls")
        if not c:
            print(f"    {m:18s} controls not run")
            continue
        obs = REPORT[m]["long/cap"]["mean_bp"]
        a2 = c.get("A_elig")
        print(f"    {m:18s} observed {obs:+7.1f} | A p50 {c['A']['p50']:+7.1f} p95 {c['A']['p95']:+7.1f} above {'yes' if c['A']['above'] else 'NO '} | "
              + (f"A' p50 {a2['p50']:+7.1f} p95 {a2['p95']:+7.1f} above {'yes' if a2['above'] else 'NO '} | " if a2 else "A' not run | ")
              + f"B p50 {c['B']['p50']:+7.1f} p95 {c['B']['p95']:+7.1f} above {'yes' if c['B']['above'] else 'NO '} | "
              f"C p95 {REPORT[m]['long/cap']['control_C']['p95']:+6.1f} above {'yes' if REPORT[m]['long/cap']['control_C']['above'] else 'NO '}")
    print(f"  above A, B and C: {kernel_surv}; above A', B and C: {kernel_surv_elig}")
    q = grid_predictions(screen["members"], screen["m_eff"]["li_ji"], screen["m_eff"]["cheverud_nyholt"], screen["grid_max"]["p_max"], screen["bh"]["n_reject"])
    q["Q1"] = bool(len(gate_kernel) > 0)
    q["Q7"] = bool(any((inter_mean(m, (4, 5)) or -1e9) > 0 and (inter_mean(m, (0, 1, 2)) or 1e9) < 0 for m in survivors))
    q["Q8"] = bool(any(REPORT[m]["long/invalidation"]["net_per_trade"]["PUB"] > 0 for m in survivors))
    n_p05 = screen["n_pA_le_05"]
    print("\nPREDICTIONS")
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print(f"  Q1 (LOAD-BEARING) a gate survivor is above p95 of A, B and C under the kernel: {v(q['Q1'])} -- "
          f"{'fallback members only (nothing passed the gate)' if fallback else 'gate survivors ' + str(survivors)}; above all three under the kernel: {kernel_surv}"
          + ("" if all("controls" in REPORT[m] for m in survivors) else "; kernel controls A/B missing for " + str([m for m in survivors if "controls" not in REPORT[m]])))
    print_grid_predictions(q, screen["members"], screen["m_eff"]["li_ji"], screen["m_eff"]["cheverud_nyholt"], n_p05, screen["grid_max"]["p_max"], screen["bh"]["n_reject"])
    print(f"  Q7 (against) a survivor's interaction is positive in the middle buckets (25-75) and negative in the bottom decile: {v(q['Q7'])} -- "
          + ", ".join(f"{m} mid {inter_mean(m, (4, 5)):+.1f} / bottom {inter_mean(m, (0, 1, 2)):+.1f}" for m in survivors
                      if inter_mean(m, (4, 5)) is not None and inter_mean(m, (0, 1, 2)) is not None))
    print(f"  Q8 (against) a survivor nets > 0 per trade after PUB under invalidation: {v(q['Q8'])} -- "
          + ", ".join(f"{m} {REPORT[m]['long/invalidation']['net_per_trade']['PUB']:+.1f}" for m in survivors))
    out = dict(note="D350: a long-timing screen. Stage 1 (the grid, data/d350_screen.json) scored 138 members against their own names at "
                    "random times; stage 2 ran D347's kernel on the survivors. Every event taken; nothing is a book; nothing promoted. "
                    "E2's kernel score is 100 - pct so the invalidation exit is the percentile crossing back through the median.",
               survivors=survivors, fallback=fallback, kernel_survivors=kernel_surv, gate_and_kernel_survivors=gate_kernel, kernel_survivors_elig=kernel_surv_elig, cap=CAP, decile=DECILE,
               bucket_edges=BUCKET_EDGES, base_rate_all_bp=E_all, base_rate_by_bucket_bp=E_b, down_years=P["down_years"],
               floored_market_by_year=P["yr_ret"], report=REPORT, screen=dict(m_eff=screen["m_eff"], bh=screen["bh"], grid_max=screen["grid_max"],
                                                                              gate=screen["gate"], n_pA_le_05=n_p05, d347_ranks=screen["d347_ranks"]),
               predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)")


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Path):
        return str(o)
    return o


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--scores", help="dev only: comma-separated subset of scores for --screen; writes to temp/, not data/")
    ap.add_argument("--workers", type=int, default=8, help="--screen: processes for the per-score controls (1 = in-process)")
    ap.add_argument("--kernel", metavar="MEMBER", help="e.g. hist_L/E1")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print("D350  a long-timing screen -- 138 declared events against their own names at random times")
    need = {"A3", "r1T", "finT", "ocT", "m_f", "m_f_oc", "keep", "elig", "base", "z", "n", "T", "HALF", "CLOSE", "RAW_CLOSE", "DV", "years",
            "down_years", "yr_ret", "LAG", "PCT", "EVENTS", "beta", "F", "bucket_rsi", "excl", "t0", "m_start", "score", "symbols", "dates", "last_live"}
    P = PREP.prep(need_grids=True)
    missing = sorted(need - set(P))
    assert not missing, f"d348_prep.prep() is missing keys: {missing}"
    if a.selftest:
        stage_selftest(P)
    elif a.screen:
        if a.scores:
            (REPO / "temp").mkdir(exist_ok=True)
            stage_screen(P, scores=a.scores.split(","), out=REPO / "temp" / "d350_screen_dev.json", workers=a.workers)
        else:
            stage_screen(P, workers=a.workers)
    elif a.kernel:
        stage_kernel(P, a.kernel, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --screen, --kernel MEMBER, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
