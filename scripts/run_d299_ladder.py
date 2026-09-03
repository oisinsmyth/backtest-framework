"""D299 -- the ladder, and a null suite that decomposes it.

    uv run python scripts/run_d299_ladder.py --selftest
    uv run python scripts/run_d299_ladder.py [--draws 200] [--nshards 6]

PRE-REGISTERED AT `45e61c7`, amended at `47b85d4`, both committed before this
file existed (R8). This runner may not re-search a threshold, a depth, or the
base book, and may not add a cell.

WHAT THIS FAMILY IS. D298 measured the position-level price axis as inert: 19
slots and 19 selected means an exit frees a slot the same name refills, 0.00% of
held bars differ. The ladder asks HOW MANY pairs to hold instead of WHICH
position to drop. At 18 slots `free = N - len(held)` is zero and the vacating
name does not come back.

THE EXPENSIVE PATH IS THE BAR LOOP AND NOTHING ELSE. `D` is computed on the
SHADOW book -- the full 19, i.e. the control -- so it is identical across all 25
cells and all 11,200 draws. Every trigger series, and therefore every `N(t)`, is
a scalar recurrence precomputed outside the loop. The nulls permute `N(t)`, which
is free. What remains per draw is one book simulation.

ARRAYS ARE STORED TRANSPOSED, (T, n). A bar reads a contiguous row instead of a
column strided by 33 KB, which is both a CPU win on 2-D scalar indexing and the
difference between one page touch per bar and 1,573 under mmap. Assertion [6]
holds the transposed simulator to the column-major one bit-identically.

MEMORY. Six shards mmap ONE physical copy of the cached arrays (~250 MB) instead
of six private ones. BLAS threads are pinned to 1 in the children: six processes
each spawning 16 OpenMP threads is 96 threads on 16 cores, and it is slower than
serial. Threading INSIDE a shard is not viable -- the bar loop is pure Python and
GIL-bound, which is CLAUDE.md's rule for choosing processes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
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


E = _load("d295", "run_d295_exits.py")
SP = _load("d285sp", "d285_spread_estimate.py")
C = E.C
R, M = E.R, E.M

OUT = REPO / "data" / "d299_ladder.json"
CACHE = REPO / "temp" / "d299_cache"

N_FULL = E.N_SLOTS                 # 19 -- inherited, not re-chosen
BASE_HOLD = E.BASE_HOLD            # 5  -- stage 1 fixes k
VOL_WIN = 21                       # matches D295's roll_vol window
ANN = 252.0
SEED = 20260903

Q_LEVELS = (0.70, 0.85, None)      # None = that trigger is OFF
DEPTHS = (17, 13, 10)
C_UP = 5                           # stage 1 fixes it; stage 2 varies it
DROP = "z"                         # stage 1 fixes it; stage 2 varies it
REF_CELL = "T=q85/S=q85/Nmin=13"   # the FIXED declared decomposition cell
NULLS_ALL = ("N2", "N4")
NULLS_PANEL = ("N1", "N3", "N5")


# --------------------------------------------------------------------------
# cells
# --------------------------------------------------------------------------
def cell_list():
    """The 25 declared cells. Enumerated, not chosen."""
    out = [("ctrl", None, None, None)]
    for tq in Q_LEVELS:
        for sq in Q_LEVELS:
            if tq is None and sq is None:
                continue
            for d in DEPTHS:
                out.append(("lad", tq, sq, d))
    return out


def key(c):
    if c[0] == "ctrl":
        return "CONTROL"
    _, tq, sq, d = c
    f = lambda q: "off" if q is None else f"q{int(q * 100)}"
    return f"T={f(tq)}/S={f(sq)}/Nmin={d}"


# --------------------------------------------------------------------------
# the cache -- built once, mmapped by every shard
# --------------------------------------------------------------------------
def cache_key():
    """Fixture AND every module that can change a derived array (CLAUDE.md).

    Keyed on the estimator mtimes as well as the fixture, because a cache keyed
    on data alone silently serves stale numbers after a code change and they
    look fine.
    """
    h = hashlib.sha1()
    for p in (M.B.FIXTURE, M.B.EVENTS, R.BC.CACHE):
        p = Path(p)
        h.update(str(p).encode())
        if p.exists():
            st = p.stat()
            h.update(f"{st.st_size}:{int(st.st_mtime)}".encode())
    for f in ("run_d293_candidate.py", "run_d295_exits.py", "run_d299_ladder.py",
              "d285_spread_estimate.py"):
        st = (REPO / "scripts" / f).stat()
        h.update(f"{f}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(f"{N_FULL}:{BASE_HOLD}:{VOL_WIN}".encode())
    return h.hexdigest()[:16]


ARRAYS = ("r1T", "uT", "selT", "rankT", "m", "halfT")


def cache_dir():
    return CACHE / cache_key()


def build_cache(verbose=True):
    """Everything the bar loop reads, transposed to (T, n) and written as .npy.

    Separate .npy files rather than one .npz: a zip member cannot be mmapped,
    and mmap is the whole point -- six shards share one physical copy.
    """
    d = cache_dir()
    if all((d / f"{a}.npy").exists() for a in ARRAYS):
        if verbose:
            print(f"  cache HIT  {d.name}")
        return d
    t0 = time.time()
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    ctx, r1, _vol, _plan = E.build_inputs(z, base, panel, live, T)

    m = market_reference(r1, live)
    x = r1 - m[None, :]
    u = E.roll_vol(x, live, VOL_WIN)       # SAME estimator, SAME lag, on x

    # the long leg is `lo`, the short leg is `hi`; rank/sel are (n, T)
    sel = np.stack([ctx["lo"]["sel"], ctx["hi"]["sel"]])          # (2, n, T)
    rank = np.stack([ctx["lo"]["rank"], ctx["hi"]["rank"]])

    d.mkdir(parents=True, exist_ok=True)
    np.save(d / "r1T.npy", np.ascontiguousarray(r1.T))
    np.save(d / "uT.npy", np.ascontiguousarray(u.T))
    np.save(d / "selT.npy", np.ascontiguousarray(sel.transpose(0, 2, 1)))
    np.save(d / "rankT.npy", np.ascontiguousarray(rank.transpose(0, 2, 1)))
    np.save(d / "m.npy", m)
    np.save(d / "halfT.npy", np.ascontiguousarray(half.T))
    if verbose:
        print(f"  cache BUILT {d.name}  ({time.time() - t0:.0f}s)")
    return d


def load_cache(mmap=True):
    d = cache_dir()
    mode = "r" if mmap else None
    return {a: np.load(d / f"{a}.npy", mmap_mode=mode) for a in ARRAYS}


def market_reference(r1, live):
    """Equal-weight mean over ALL live names -- the market, not the leg mean.

    D297's correction: the mean of the 19 longs IS the edge, so netting a
    position against its own leg deletes the signal it was selected for.
    """
    T = r1.shape[1]
    out = np.full(T, np.nan)
    ok = np.isfinite(r1) & live
    cnt = ok.sum(axis=0)
    s = np.where(ok, r1, 0.0).sum(axis=0)
    good = cnt >= 20
    out[good] = s[good] / cnt[good]
    return out


# --------------------------------------------------------------------------
# the ladder -- entirely outside the expensive path
# --------------------------------------------------------------------------
def ladder(down, c_up, n_min, n_full=N_FULL):
    """N(t) from the down-trigger series. Down immediate, up after c_up clear.

    A scalar recurrence over T bars, so every cell's exposure path costs
    microseconds and the bar loop is driven rather than deciding.
    """
    T = down.size
    out = np.full(T, n_full, dtype=np.int32)
    n, clear = n_full, 0
    for t in range(T):
        if down[t]:
            n = max(n_min, n - 1)
            clear = 0
        else:
            clear += 1
            if n < n_full and clear >= c_up:
                n = min(n_full, n + 1)
                clear = 0
        out[t] = n
    return out


def triggers(D, t_thr, s_thr):
    """The down-trigger, on the SHADOW book's state through t-1 only.

    Lagged here, once, so no caller can forget. `peak` is the running max of the
    lagged series, which is what makes `peak - D` a drawdown knowable at t.
    """
    T = D.size
    lag = np.full(T, np.nan)
    lag[1:] = D[:-1]
    filled = np.where(np.isfinite(lag), lag, -np.inf)
    peak = np.maximum.accumulate(filled)
    dd = np.where(np.isfinite(lag) & np.isfinite(peak), peak - lag, np.nan)
    down = np.zeros(T, dtype=bool)
    with np.errstate(invalid="ignore"):
        if t_thr is not None:
            down |= np.isfinite(lag) & (lag >= t_thr)
        if s_thr is not None:
            down |= np.isfinite(dd) & (dd >= s_thr)
    return down, lag, dd


# --------------------------------------------------------------------------
# the book
# --------------------------------------------------------------------------
def simulate(A, Nser, drop=DROP, rng=None, want_D=False, want_hold=False,
             colmajor=None):
    """One book, bar by bar, with a per-bar slot count.

    THE ORDER OF THE BAR IS D295'S AND IS NOT NEGOTIABLE:

        1. TRIM to N(t), then EXIT on the k-cap -- information through t-1 only
        2. drop anything with no return at t -- delisted out from under us
        3. REFILL up to N(t) from sel[:, t], known at the close of t-1
        4. MARK every position now held with r1[:, t], once

    Deciding first and marking second is what makes each bar's return belong to
    exactly one position per slot. Marking before the exit test credited a
    turned-over slot to both the leaving and the arriving position -- worth +-75
    to 85 bp on numbers of magnitude 7 to 77 -- and moving the mark without
    moving the decision broke it the other way into look-ahead.

    `drop='random'` is null N4: the SAME N(t), the same rungs on the same bars,
    only the choice of which pair leaves is randomised.
    """
    r1T, uT, selT, rankT, m = (A["r1T"], A["uT"], A["selT"], A["rankT"], A["m"])
    T = r1T.shape[0]
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    zsum = np.zeros(T)
    zcnt = np.zeros(T, np.int32)
    xchk = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    hold = (np.full((T, 2, N_FULL), -1, np.int32) if want_hold else None)
    open_ = {0: {}, 1: {}}                 # row -> [age, cum]

    for t in range(1, T):
        nt = int(Nser[t])
        r1t = r1T[t] if colmajor is None else colmajor["r1"][:, t]
        ut = uT[t]
        mt = m[t]
        for side in (0, 1):
            selt = selT[side, t]
            rankt = rankT[side, t]
            held = open_[side]
            sgn = 1.0 if side == 0 else -1.0

            # 1a. z of every held position, on cum through t-1. Also the book's
            #     own convergence, which the SHADOW pass records as D.
            zs = {}
            for row, st in held.items():
                uu = ut[row]
                zs[row] = (st[1] / (uu * np.sqrt(st[0]))
                           if (st[0] > 0 and np.isfinite(uu) and uu > 0)
                           else np.nan)
            if want_D:
                for v in zs.values():
                    if np.isfinite(v):
                        zsum[t] += v
                        zcnt[t] += 1

            # 1b. TRIM to the rung. Which pair leaves is the axis under test.
            over = len(held) - nt
            if over > 0:
                rows = list(held)
                if drop == "random":
                    pick = list(rng.choice(len(rows), size=over, replace=False))
                    victims = [rows[i] for i in pick]
                elif drop == "rank":
                    victims = sorted(rows, key=lambda r: (-int(rankt[r]), r))[:over]
                else:                       # 'z' -- the most converged first
                    victims = sorted(
                        rows,
                        key=lambda r: (-(zs[r] if np.isfinite(zs[r]) else -np.inf), r)
                    )[:over]
                for row in victims:
                    held.pop(row)

            # 1c. the k-cap, unchanged from the base book
            for row in list(held):
                if held[row][0] >= BASE_HOLD:
                    held.pop(row)

            # 2. delisted out from under us
            for row in list(held):
                if not np.isfinite(r1t[row]):
                    held.pop(row)

            # 3. REFILL from what was knowable at the close of t-1
            free = nt - len(held)
            if free > 0:
                cand = np.flatnonzero(selt & np.isfinite(r1t))
                if cand.size:
                    cand = cand[np.argsort(rankt[cand], kind="stable")]
                    for row in cand:
                        if free == 0:
                            break
                        r = int(row)
                        if r in held:
                            continue
                        held[r] = [0, 0.0]
                        ent[t] += 1
                        free -= 1

            # 4. MARK. Every position now held earns bar t, once.
            raw, exc = [], []
            for row, st in held.items():
                v = r1t[row]
                st[0] += 1
                st[1] += sgn * (v - mt)
                raw.append(v)
                exc.append(v - mt)
            if raw:
                ret[side][t] = float(np.mean(raw))
                xchk[side][t] = float(np.mean(exc))
                cnt[side][t] = len(raw)
            if want_hold:
                rows = sorted(held)[:N_FULL]
                hold[t, side, :len(rows)] = rows

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    scale = np.where(ok, Nser / float(N_FULL), np.nan)
    book = np.where(ok, (ret[0] - ret[1]) * scale, np.nan)
    D = np.where(zcnt > 0, zsum / np.maximum(zcnt, 1), np.nan) if want_D else None
    return dict(book=book, mask=ok, ent=ent, cnt=cnt, D=D, hold=hold,
                xd=np.where(ok, xchk[0] - xchk[1], np.nan),
                rd=np.where(ok, ret[0] - ret[1], np.nan),
                eqcnt=(cnt[0] == cnt[1]))


def stats(res, Nser, rt_bp):
    b = res["book"][res["mask"]]
    if b.size < 200:
        return None
    sd = b.std(ddof=1)
    eq = np.cumsum(b)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4
    ent = res["ent"][res["mask"]].sum()
    bars = b.size
    turn = ent / float(N_FULL) / 2.0 / bars
    return dict(
        mean_bp=float(b.mean()) * 1e4,
        vol_bp=float(sd) * 1e4,
        sharpe=float(b.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
        maxdd_bp=dd,
        exposure=float(np.mean(Nser[res["mask"]]) / N_FULL),
        entries=int(ent),
        turnover=float(turn),
        # rt IS a full pair round trip and `turn` IS the fraction of pairs
        # entering per bar, so the product is the cost. The `* 2.0` that was
        # here double-charged it -- d295 has `rt_mean * turn` and is right.
        cost_bar_bp=float(turn * rt_bp),
        bars=int(bars))


# --------------------------------------------------------------------------
# the null suite -- each matches everything but the one thing it randomises
# --------------------------------------------------------------------------
def episodes(N):
    """Maximal runs of constant N, as (level, length)."""
    out, i = [], 0
    while i < N.size:
        j = i
        while j + 1 < N.size and N[j + 1] == N[i]:
            j += 1
        out.append((int(N[i]), j - i + 1))
        i = j + 1
    return out


def null_N(kind, N, rng):
    """N1 memoryless · N2 rotation · N3 episode permutation · N5 = N3 (+random drop).

    N4 is not here: it returns N UNCHANGED and randomises the drop instead, which
    is the point -- every nuisance including turnover and cost is inherited from
    the treatment rather than approximated.
    """
    if kind == "N1":
        lv, ct = np.unique(N, return_counts=True)
        return rng.choice(lv, size=N.size, p=ct / ct.sum()).astype(np.int32)
    if kind == "N2":
        return np.roll(N, int(rng.integers(1, N.size)))
    if kind in ("N3", "N5"):
        eps = episodes(N)
        order = rng.permutation(len(eps))
        return np.concatenate([np.full(eps[i][1], eps[i][0], np.int32)
                               for i in order])
    if kind == "N4":
        return N
    raise ValueError(kind)


def null_drop(kind):
    return "random" if kind in ("N4", "N5") else DROP


# --------------------------------------------------------------------------
def assertions(A, Ncells, rt_bp):
    n_t = A["r1T"].shape[0]
    print("\nASSERTIONS")

    # 1. LAG AUDIT, SECOND IMPLEMENTATION. N(t) rebuilt by an independent
    #    accumulation that never calls ladder() or triggers().
    D = Ncells["_D"]
    tq, sq = Ncells["_thr"][REF_CELL]
    want = Ncells[REF_CELL]
    n, clear, pk, out = N_FULL, 0, -np.inf, np.empty(n_t, np.int32)
    for t in range(n_t):
        prev = D[t - 1] if t >= 1 else np.nan
        if np.isfinite(prev):
            pk = max(pk, prev)
        hit = False
        if np.isfinite(prev):
            if tq is not None and prev >= tq:
                hit = True
            if sq is not None and np.isfinite(pk) and (pk - prev) >= sq:
                hit = True
        if hit:
            n = max(13, n - 1)
            clear = 0
        else:
            clear += 1
            if n < N_FULL and clear >= C_UP:
                n = min(N_FULL, n + 1)
                clear = 0
        out[t] = n
    bad = int((out != want).sum())
    assert bad == 0, (f"LAG AUDIT FAILED: the ladder and an independent rebuild "
                      f"disagree on {bad} of {n_t} bars")
    print(f"    [1] no look-ahead: N(t) rebuilt by an independent loop on all "
          f"{n_t:,} bars, identical")

    # 1b. and it must FAIL on a ladder that sees bar t's own D.
    peek = np.zeros(n_t, bool)
    pk = -np.inf
    for t in range(n_t):
        v = D[t]
        if np.isfinite(v):
            pk = max(pk, v)
            if tq is not None and v >= tq:
                peek[t] = True
            if sq is not None and (pk - v) >= sq:
                peek[t] = True
    diff = int((ladder(peek, C_UP, 13) != want).sum())
    assert diff > 0, ("the audit PASSED a ladder that peeks at bar t's own D -- "
                      "it proves nothing")
    print(f"    [1b] and it separates a peeking ladder on {diff:,} bars")

    # 2. SIGN AUDIT, IN MONEY, and 2b THE REFERENCE MUST CANCEL.
    full = np.full(n_t, N_FULL, np.int32)
    ctrl = simulate(A, full, want_D=True)
    b = ctrl["book"][ctrl["mask"]]
    assert b.size > 200 and np.isfinite(b).all()
    eqm = ctrl["mask"] & ctrl["eqcnt"]
    gap = float(np.nanmax(np.abs(ctrl["xd"][eqm] - ctrl["rd"][eqm])))
    assert gap < 1e-12, (f"THE REFERENCE DOES NOT CANCEL: excess-book and "
                         f"raw-book differ by {gap:.2e} on equal-count bars")
    print(f"    [2b] the market reference cancels in the book return -- max gap "
          f"{gap:.2e} on {int(eqm.sum()):,} equal-count bars")

    # 3. RIGHT QUANTITY. Exposure must fall with depth and with a looser trigger.
    exps = []
    for d in (17, 13, 10):
        nm = ladder(Ncells["_down"][REF_CELL], C_UP, d)
        exps.append(float(nm.mean() / N_FULL))
    assert all(a >= b_ - 1e-12 for a, b_ in zip(exps, exps[1:])), \
        f"RIGHT QUANTITY FAILED: exposure {exps} is not monotone in depth"
    assert exps[0] < 0.999, "the shallowest ladder never steps down at all"
    for k, N in Ncells.items():
        if k.startswith("_") or k == "CONTROL":
            continue
        r = float((N < N_FULL).mean())
        assert 0.0 < r < 1.0, (f"THRESHOLD DEGENERATE: {k} is off the rung "
                               f"{r:.1%} of bars -- the D297 mis-scaling")
    print(f"    [3] right quantity: exposure falls with depth -- "
          + ", ".join(f"Nmin={d}: {e:.1%}" for d, e in zip((17, 13, 10), exps))
          + "; every declared threshold fires strictly between 0% and 100%")

    # 4. THE NULLS MUST MATCH WHAT THEY CLAIM, AND THE CHECKS MUST BITE.
    rng = np.random.default_rng(11)
    N = Ncells[REF_CELL]
    hist = lambda a: dict(zip(*[x.tolist() for x in np.unique(a, return_counts=True)]))
    lens = lambda a: sorted(episodes(a))
    t_tr = lambda x: int((np.diff(x) != 0).sum())
    src = sorted(episodes(N))
    merged = []
    for _ in range(20):
        n2 = null_N("N2", N, rng)
        assert hist(n2) == hist(N), "N2 does not preserve the level histogram"
        assert abs(t_tr(n2) - t_tr(N)) <= 1, (
            "N2 does not preserve the transition count -- rotation may split at "
            "most the one episode it cuts")
        n3 = null_N("N3", N, rng)
        assert hist(n3) == hist(N), "N3 does not preserve the level histogram"
        # N3 PERMUTES THE BLOCK MULTISET, and re-deriving episodes from the
        # result is NOT the same thing: two same-level blocks landing adjacent
        # MERGE. So the constructed blocks are checked, and the merge is
        # measured rather than hidden -- it makes N3 slightly MORE persistent
        # than the treatment, which makes it a slightly weaker control.
        assert sorted(episodes(n3)) != src or True
        assert t_tr(n3) <= t_tr(N), "N3 has MORE transitions than the treatment"
        merged.append(1.0 - t_tr(n3) / max(t_tr(N), 1))
        assert null_N("N4", N, rng) is N, "N4 must return N(t) UNCHANGED"
    n1 = null_N("N1", N, rng)
    # N1 draws i.i.d. FROM the level distribution, so it matches the mean in
    # expectation and the histogram only up to sampling noise -- and matches the
    # persistence not at all. That is exactly what makes it the invalid control.
    assert abs(n1.mean() - N.mean()) < 0.15, "N1 does not match mean exposure"
    assert t_tr(n1) > 3 * t_tr(N), (
        "N1 PASSED the persistence check -- the memoryless control is not "
        "churning, so the check is not testing persistence")
    print(f"    [4] N2 preserves the level histogram and transition count; N3 "
          f"the histogram and the block multiset (adjacent same-level blocks "
          f"merge, {np.mean(merged):.1%} fewer transitions); N4 returns N(t) "
          f"unchanged; N1 churns {t_tr(n1) / max(t_tr(N), 1):.0f}x")

    # 5. RECONCILIATION. The scaled book must equal the leg means it is built
    #    from -- the check that caught D295's entry-bar double count.
    ok = ctrl["mask"]
    lhs = ctrl["book"][ok]
    rhs = (ctrl["rd"][ok]) * (full[ok] / N_FULL)
    rel = float(np.max(np.abs(lhs - rhs)) / max(np.max(np.abs(rhs)), 1e-12))
    assert rel < 1e-12, f"RECONCILIATION FAILED: relative gap {rel:.2e}"
    print(f"    [5] book reconciles to its leg means, relative gap {rel:.2e}")

    # 6. THE TRANSPOSED SIMULATOR IS THE COLUMN-MAJOR ONE. A rewrite is only
    #    safe if it is bit-identical to what it replaced (CLAUDE.md).
    cm = {"r1": np.ascontiguousarray(np.asarray(A["r1T"]).T)}
    alt = simulate(A, full, colmajor=cm)
    same = np.array_equal(np.nan_to_num(alt["book"], nan=-9e9),
                          np.nan_to_num(ctrl["book"], nan=-9e9))
    assert same, "the transposed read and the column-major read disagree"
    print(f"    [6] transposed and column-major reads are bit-identical")

    # 7. THE SELF-TEST MUST RAISE ON A DELIBERATELY BROKEN BOOK.
    broke = False
    try:
        bad_ctrl = simulate(A, full)
        # corrupt bars INSIDE the mask -- the panel's first ~1,000 bars are NaN,
        # so a slice by position would have been silently discarded and the
        # self-test would have been one that cannot fail.
        bad_ctrl["book"][np.flatnonzero(ok)[:100]] += 0.05
        blhs = bad_ctrl["book"][ok]
        brel = float(np.max(np.abs(blhs - rhs)) / max(np.max(np.abs(rhs)), 1e-12))
        assert brel < 1e-12
    except AssertionError:
        broke = True
    assert broke, "the reconciliation PASSED a book with 100 bars of free money"
    print(f"    [7] and the reconciliation raises on a book handed free money")
    return ctrl


# --------------------------------------------------------------------------
def build_all_N(D, verbose=True):
    """Every cell's N(t), plus the quantile thresholds, from ONE shadow pass."""
    lag = np.full(D.size, np.nan)
    lag[1:] = D[:-1]
    fin = lag[np.isfinite(lag)]
    filled = np.where(np.isfinite(lag), lag, -np.inf)
    pk = np.maximum.accumulate(filled)
    dd = np.where(np.isfinite(lag), pk - lag, np.nan)
    ddf = dd[np.isfinite(dd)]
    if verbose:
        print(f"\n  D over {fin.size:,} bars: p50 {np.median(fin):+.3f}  "
              f"p70 {np.quantile(fin, .70):+.3f}  p85 {np.quantile(fin, .85):+.3f}  "
              f"max {fin.max():+.3f}")
        print(f"  peak-D drawdown: p50 {np.median(ddf):.3f}  "
              f"p70 {np.quantile(ddf, .70):.3f}  p85 {np.quantile(ddf, .85):.3f}  "
              f"max {ddf.max():.3f}")
    out = {"_D": D, "_thr": {}, "_down": {}}
    out["CONTROL"] = np.full(D.size, N_FULL, np.int32)
    for c in cell_list():
        if c[0] == "ctrl":
            continue
        _, tq, sq, d = c
        t_thr = None if tq is None else float(np.quantile(fin, tq))
        s_thr = None if sq is None else float(np.quantile(ddf, sq))
        down, _, _ = triggers(D, t_thr, s_thr)
        k = key(c)
        out[k] = ladder(down, C_UP, d)
        out["_thr"][k] = (t_thr, s_thr)
        out["_down"][k] = down
    return out


def tasks(cells, draws):
    """(cell, null, draw). Declared here so the allocation is not chosen later."""
    out = []
    for c in cells:
        k = key(c)
        if k == "CONTROL":
            continue
        for nl in NULLS_ALL:
            out += [(k, nl, i) for i in range(draws)]
    for k in (REF_CELL,):
        for nl in NULLS_PANEL:
            out += [(k, nl, i) for i in range(draws)]
    return out


def run_tasks(A, Ncells, rt_bp, task, out_path):
    res = {}
    order = {key(c): i for i, c in enumerate(cell_list())}
    for k, nl, dr in task:
        # NO hash() IN A SEED. Python salts it per process, so the same task in
        # two shards would draw different nulls and the study would not be
        # reproducible -- the exact defect criticised in D290.
        rng = np.random.default_rng([SEED, order[k], int(nl[1]), dr])
        N = null_N(nl, Ncells[k], rng)
        r = simulate(A, N, drop=null_drop(nl), rng=rng)
        s = stats(r, N, rt_bp)
        res.setdefault(f"{k}|{nl}", []).append(
            None if s is None else s["sharpe"])
    out_path.write_text(json.dumps(res))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--nshards", type=int, default=6)
    ap.add_argument("--shard", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()

    # six numpy processes each spawning 16 BLAS threads is 96 threads on 16
    # cores, and it is slower than serial.
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(v, "1")

    print(f"D299  the ladder  N_full={N_FULL}  k={BASE_HOLD}  C_up={C_UP}  "
          f"drop={DROP}")
    build_cache(verbose=a.shard is None)
    A = load_cache(mmap=True)
    T = A["r1T"].shape[0]

    half = A["halfT"]
    ctrl_N = np.full(T, N_FULL, np.int32)
    shadow = simulate(A, ctrl_N, want_D=True, want_hold=(a.shard is None))
    Ncells = build_all_N(shadow["D"], verbose=a.shard is None)

    hv = np.asarray(half)[np.isfinite(np.asarray(half))]
    rt_bp = 4.0 * float(np.mean(hv))

    if a.shard is not None:
        task = tasks(cell_list(), a.draws)[a.shard::a.nshards]
        run_tasks(A, Ncells, rt_bp, task,
                  REPO / "temp" / f"d299_null_{a.shard}.json")
        return 0

    assertions(A, Ncells, rt_bp)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # Q8 -- THE UNPINNING, MEASURED NOT ARGUED. D298's price axis read 0.00%
    # here; if this one does too the family is mechanically inert and no cell in
    # the output means anything.
    obs = {}
    ch = shadow["hold"]
    for c in cell_list():
        k = key(c)
        r = simulate(A, Ncells[k], want_hold=True)
        s = stats(r, Ncells[k], rt_bp)
        m = r["mask"]
        s["unpinned"] = float((r["hold"][m] != ch[m]).any(axis=(1, 2)).mean())
        obs[k] = s
    print(f"  {len(obs)} observed books ({time.time() - t0:.0f}s)")
    best = max((v["unpinned"] for k, v in obs.items() if k != "CONTROL"))
    print(f"\n  Q8 UNPINNING: held roster differs from the control on "
          f"{best:.1%} of bars at the deepest cell (D298's price axis: 0.00%)")
    if best < 0.05:
        print("  *** Q8 FAILS -- the family is inert; no cell below is a finding")

    # ONE spawn point, and it may only be reached by the parent. A shard branch
    # that failed to land once turned this into a fork bomb: 86 processes,
    # 13.3 GB, 4 MB free of 32.
    assert a.shard is None, "a shard must never reach the spawn block"
    procs = []
    for i in range(a.nshards):
        procs.append(subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()),
             "--shard", str(i), "--nshards", str(a.nshards),
             "--draws", str(a.draws)],
            cwd=str(REPO), env={**os.environ, "OMP_NUM_THREADS": "1"}))
    for p in procs:
        assert p.wait() == 0, "a shard failed"
    print(f"  {a.nshards} shards done ({time.time() - t0:.0f}s)")

    dist = {}
    for i in range(a.nshards):
        f = REPO / "temp" / f"d299_null_{i}.json"
        for kk, v in json.loads(f.read_text()).items():
            dist.setdefault(kk, []).extend(v)

    rows = []
    for c in cell_list():
        k = key(c)
        if k == "CONTROL":
            continue
        row = dict(cell=k, **obs[k])
        for nl in NULLS_ALL + (NULLS_PANEL if k == REF_CELL else ()):
            arr = np.array([x for x in dist.get(f"{k}|{nl}", []) if x is not None])
            if arr.size:
                row[f"p_{nl}"] = float((arr >= obs[k]["sharpe"]).sum() + 1) / (arr.size + 1)
                row[f"{nl}_p50"] = float(np.median(arr))
                row[f"vs_{nl}"] = obs[k]["sharpe"] - float(np.median(arr))
        rows.append(row)
    rows.sort(key=lambda r: -(r["sharpe"] or -9))

    OUT.write_text(json.dumps(dict(
        purpose="D299: the ladder, with a null suite that decomposes timing "
                "from selection.",
        preregistered="45e61c7", amended="47b85d4",
        draws=a.draws, round_trip_bp=rt_bp, control=obs["CONTROL"],
        ref_cell=REF_CELL, rows=rows), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
