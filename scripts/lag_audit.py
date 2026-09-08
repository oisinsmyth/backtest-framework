"""The lag audit, as a thing you IMPORT rather than a thing you remember.

    uv run python scripts/lag_audit.py --selftest

    import lag_audit as LA                       # or LA = _load("lag_audit", "lag_audit.py")
    LA.assert_slot_lagged(base, score, n, pos)            # ranking books
    LA.assert_gate_lagged(gate, sc, base, finT, bars, gate_rows, rebuild)   # slot-book gates
    pos_mask = LA.lag1_mask(sig_mask); LA.assert_mask_is_lagged(pos_mask, sig_mask)  # event books
    LA.raises_on_broken(LA.assert_slot_lagged, base, score, n, BROKEN_pos)  # the negative control

WHY THIS FILE EXISTS, and it is not tidiness.

`scripts/d345_event_book.py:11` already states the contract in prose:

    "Inputs are (T, n) and ALREADY LAGGED: sig_*[t] and score_T[t] are what is known at the
     close of t-1."

D391's pre-registration section 7 already REQUIRED an [L] lag audit. Both existed, and D391's
runner still shipped without one: it carried [E], [POOL], [PIV] and [SC], booked the signal bar's
own open-to-close, and reported +43.02 where the honest number is +8.00. D279 lost ~93% of an
apparent edge to the same class of bug; D391 lost ~82% of one.

**A documented contract plus a written requirement was not enough.** Three near-identical copies of
the ranking audit exist (`run_overnight_short.py:454`, `run_unfiltered_ranking.py:93`,
`run_descending_ranking.py:134`) and two byte-identical copies of the gate wrapper
(`run_d348_score_rotation_null.py:266`, `run_d355_exit_swap.py:509`) -- and a defect appeared in the
one shape nobody had a copy of. `d296_criterion_matched_nulls.py:256` states the policy this file
implements: *"a lag audit rewritten here would be a second copy."*

THE THREE SHAPES, and they are genuinely different questions:

  SLOT / RANKING   a held set chosen by `top_n` from a score grid. The bug is ranking on
                   `score[:, t]` instead of `score[:, t-1]`. D279.
  GATE             a slot book's membership rebuilt from the raw score at t-lag, never through
                   the selection function. D338's shape, used by eight runners.
  EVENT            a boolean mask handed to `EB.simulate_event`, which treats the mask bar as the
                   bar the position OPENS ON. D359/D360/D361 are safe because their percentile
                   grids are lagged upstream; anything defined by bar t's own OHLC is not. D391.

WHAT THIS FILE DOES NOT DO. It does not prove a SCORE is causal -- that is the truncation audit
(`ragged_vol_scores.py:172`), which rebuilds from a panel truncated at T0 and requires the values
to match. A causal score can still be traded on the wrong bar, and a lagged position can still be
built from a score that read the future. **Both are needed and neither substitutes for the other.**
D391 passed [PIV] -- its pivot levels were provably causal -- and still booked the signal bar.

EQUIVALENCE. `assert_slot_lagged(..., descending=False)` is `run_descending_ranking.py:134`'s body,
which subsumes `run_overnight_short.py:454`'s: the original masks non-finite scores to `+inf` and
stable-argsorts, which orders the finite block ascending and leaves the non-finite block in panel
order -- exactly what the partitioned form builds. The self-test asserts that equivalence against
the original body inline, on a TIE-HEAVY input, per CLAUDE.md's rule for guarding a rewrite.
"""

from __future__ import annotations

import argparse

import numpy as np


# ---------------------------------------------------------------- shape 1: ranking
def assert_slot_lagged(base, score, n, pos, descending=False):
    """Re-derive the held set from `score[:, t-1]` and assert it matches `pos`.

    A SECOND IMPLEMENTATION, deliberately not a call into `top_n`: the point is to disagree with it
    if it is wrong, and a check that shares the code it checks cannot. Partitions the eligible
    indices into finite and non-finite scores, sorts the finite block by the RAW score in the
    stated direction, and appends the non-finite block in panel order.

    Returns the number of bars verified. Raises AssertionError on the first mismatch."""
    if np.any(base[:, 0] != 0.0):
        raise AssertionError("base column 0 is non-zero; hold_book did not lag")
    checked = 0
    for t in range(1, base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            want = q
        else:
            s = score[q, t - 1]                       # EXPLICITLY the prior bar
            fin = np.isfinite(s)
            key = -s[fin] if descending else s[fin]
            order = np.concatenate([q[fin][np.argsort(key, kind="stable")], q[~fin]])
            want = order[:n]
        got = np.flatnonzero(pos[:, t] != 0.0)
        if got.size != want.size or not np.array_equal(np.sort(got), np.sort(want)):
            raise AssertionError(
                f"{'desc' if descending else 'asc'} top{n} bar {t}: held set does not match "
                f"the rank of score[:, t-1]")
        checked += 1
    return checked


def held_rank_pctile(base, score, pos, shift):
    """Mean cross-sectional percentile of the HELD names in the bar's score.

    `shift=1` scores them on `score[:, t-1]` (all the book may see), `shift=0` on `score[:, t]`
    (the bar it earns). Percentile 0 is the LOWEST score: an ascending book sits near 0, a
    descending book near 1. **The D279 defect inverted exactly that**, which is why this is
    reported beside the assertion rather than instead of it -- it is the diagnostic that makes a
    passing audit legible."""
    acc = []
    for t in range(1, base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size < 2:
            continue
        h = np.flatnonzero(pos[:, t] != 0.0)
        if h.size == 0:
            continue
        s = np.where(np.isfinite(score[q, t - shift]), score[q, t - shift], np.inf)
        rank = np.empty(q.size, dtype=float)
        rank[np.argsort(s, kind="stable")] = np.arange(q.size)
        acc.append(rank[np.searchsorted(q, h)] / max(q.size - 1, 1))
    return float(np.concatenate(acc).mean()) if acc else float("nan")


# ------------------------------------------------------------------- shape 2: gate
def assert_gate_lagged(gate, score, base, finT, bars, gate_rows, rebuild, side=0):
    """The slot-book gate check, unified from two byte-identical copies
    (`run_d348_score_rotation_null.py:266`, `run_d355_exit_swap.py:509`).

    `gate_rows(gate, side, t)` and `rebuild(score, base, finT, t, lag)` are passed IN rather than
    imported, so this stays free of `run_d338`'s `N_BASE` and can serve a gate of any width.
    `rebuild` must never call the selection function -- that is the whole point.

    Returns the number of sampled bars on which the UNLAGGED rebuild DIFFERS. **A caller must
    assert that count is large**: if the unlagged rebuild agrees everywhere, the audit is passing
    because the score barely moves between bars, not because the book is lagged. Every existing
    call site pairs this with `assert n_unl > len(bars) // 2`."""
    n_unl = 0
    for t in bars:
        t = int(t)
        got = set(int(r) for r in gate_rows(gate, side, t))
        want = rebuild(score, base, finT, t, 1)
        if got != want:
            raise AssertionError(f"[L] bar {t}: gate != rebuild from score[:, t-1]")
        n_unl += rebuild(score, base, finT, t, 0) != got
    return n_unl


# ------------------------------------------------------------------ shape 3: event
def lag1_mask(m):
    """A SIGNAL mask shifted one bar forward, into a POSITION mask.

    `EB.simulate_event` treats the mask it is given as the bar the position OPENS ON and books
    that bar's open-to-close (`d345_event_book.py:11`, and the mechanics at `:96-115`). A signal
    computed from bar t's own OHLC must therefore be shifted before it is handed over.

    D359/D360/D361 do NOT need this: their masks are built from percentile grids already lagged to
    t-1 by `run_d350.lagged` / `run_d347.prep`'s closure, so the mask at bar t is known at the
    close of t-1 and opening at bar t's open is honest. **Use this when the event reads bar t
    itself.**"""
    out = np.zeros_like(m)
    out[1:] = m[:-1]
    return np.ascontiguousarray(out)


def assert_mask_is_lagged(pos, raw):
    """`pos` is exactly `raw` shifted one bar, and nothing opens on bar 0."""
    if not np.array_equal(pos[1:], raw[:-1]):
        raise AssertionError("[L] the position mask is not the signal mask shifted one bar")
    if pos[0].any():
        raise AssertionError("[L] a position opens on bar 0, where no signal can precede it")
    return int(pos.sum())


def pct_direct(col, i):
    """The cross-sectional percentile of row `i` in `col`, BY DIRECT COUNTING.

    No sort, no `percentile_grid` -- the average-rank definition written out, so it can disagree
    with the grid it checks. D347's `[E]` and D359's `assert_E` both use this shape; it is the
    primitive rather than the whole assertion, because the CONDITION is study-specific and a
    helper that pretended otherwise would be one nobody could call."""
    fin = np.isfinite(col)
    if not fin.any():
        return np.nan
    v = col[i]
    if not np.isfinite(v):
        return np.nan
    return (float((col[fin] < v).sum()) + 0.5 * float((col[fin] == v).sum())) / float(fin.sum()) * 100.0


def sample_events(mask, k, rng):
    """`k` random (t, i) pairs from a boolean event mask, for a per-event condition check."""
    t, i = np.nonzero(mask)
    if t.size == 0:
        return np.empty(0, int), np.empty(0, int)
    j = rng.choice(t.size, size=min(k, t.size), replace=False)
    return t[j], i[j]


# ------------------------------------------------------- the negative-control harness
def raises_on_broken(fn, *args, **kwargs):
    """Assert that `fn(*args)` RAISES AssertionError. Returns the message it raised.

    **CLAUDE.md: "A self-test that cannot fail is worse than none."** Every existing call site
    hand-rolls a `try/except AssertionError` block to prove this; making it one call is the only
    way the negative control stays as cheap as the assertion it guards -- and therefore the only
    way it keeps getting written."""
    try:
        fn(*args, **kwargs)
    except AssertionError as e:
        return str(e)
    raise AssertionError(
        f"THE AUDIT CANNOT FAIL: {getattr(fn, '__name__', fn)} accepted a deliberately broken "
        f"input. An assertion that never fires is worse than none.")


# ------------------------------------------------------------------------ self-test
def _original_ascending(base, score, n, pos):
    """`run_overnight_short.py:454`'s body verbatim, as the reference the unified form must equal."""
    if np.any(base[:, 0] != 0.0):
        raise AssertionError("base column 0 is non-zero; hold_book did not lag")
    checked = 0
    for t in range(1, base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            want = q
        else:
            s = score[q, t - 1]
            s = np.where(np.isfinite(s), s, np.inf)
            want = q[np.argsort(s, kind="stable")[:n]]
        got = np.flatnonzero(pos[:, t] != 0.0)
        if got.size != want.size or not np.array_equal(np.sort(got), np.sort(want)):
            raise AssertionError(f"top{n} bar {t}: mismatch")
        checked += 1
    return checked


def _top_n_like(base, score, n):
    """A minimal stand-in for `run_concentrated_short.top_n`: lag INSIDE, then rank."""
    lagged = np.full_like(score, np.nan)
    lagged[:, 1:] = score[:, :-1]
    pos = np.zeros_like(base)
    for t in range(base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            keep = q
        else:
            s = np.where(np.isfinite(lagged[q, t]), lagged[q, t], np.inf)
            keep = q[np.argsort(s, kind="stable")[:n]]
        pos[keep, t] = 1.0
    return pos


def selftest() -> int:
    print("LAG AUDIT SELF-TEST -- three shapes, and every assertion proved able to fail\n")
    rng = np.random.default_rng(20260908)
    n_names, T, N = 40, 120, 5

    # TIE-HEAVY on purpose: ties are where a rewrite disagrees with what it replaced.
    score = np.round(rng.normal(size=(n_names, T)), 1)
    score[rng.random((n_names, T)) < 0.10] = np.nan
    base = (rng.random((n_names, T)) < 0.5).astype(float)
    base[:, 0] = 0.0
    pos = _top_n_like(base, score, N)

    # --- shape 1 --------------------------------------------------------
    checked = assert_slot_lagged(base, score, N, pos)
    ref = _original_ascending(base, score, N, pos)
    assert checked == ref, f"[EQ] unified {checked} != original {ref}"
    print(f"    shape 1 RANKING: {checked} bars verified, and the unified body agrees with "
          f"`run_overnight_short.py:454`'s original on a tie-heavy input "
          f"({int(np.isnan(score).sum())} NaN, {len(np.unique(score[~np.isnan(score)]))} distinct)")

    broken = _top_n_like(base, np.roll(score, -1, axis=1), N)      # ranked on score[:, t]
    msg = raises_on_broken(assert_slot_lagged, base, score, N, broken)
    print(f"    [X] a book ranked on score[:, t] IS CAUGHT -- {msg[:58]}...")

    lag_p = held_rank_pctile(base, score, pos, 1)
    con_p = held_rank_pctile(base, score, pos, 0)
    assert lag_p < con_p, f"[D] ascending book should sit lower in the LAGGED distribution"
    print(f"    held-rank percentile: {lag_p:.3f} lagged vs {con_p:.3f} contemporaneous "
          f"-- an ascending book sits low in what it could see")

    desc_pos = _top_n_like(base, -score, N)
    assert assert_slot_lagged(base, -score, N, desc_pos) > 0
    raises_on_broken(assert_slot_lagged, base, score, N, desc_pos)
    print(f"    descending=False on a DESCENDING book IS CAUGHT (the direction flag is load-bearing)")

    # --- shape 2 --------------------------------------------------------
    finT = np.ones((T, n_names), bool)
    sc2 = np.round(rng.normal(size=(n_names, T)), 1)
    b2 = np.ones((n_names, T), bool)

    def rebuild(s, bs, fn, t, lag):
        v = np.where(bs[:, t], s[:, t - lag], np.nan)
        order = np.argsort(v, kind="stable")
        return set(int(r) for r in order[:N] if fn[t, r])

    gate = {t: rebuild(sc2, b2, finT, t, 1) for t in range(1, T)}
    n_unl = assert_gate_lagged(gate, sc2, b2, finT, range(1, T),
                               lambda g, side, t: g[t], rebuild)
    assert n_unl > (T - 1) // 2, f"[L] the unlagged rebuild agrees too often ({n_unl})"
    print(f"    shape 2 GATE: {T - 1} bars verified; the UNLAGGED rebuild differs on {n_unl} "
          f"of them, so the check is not passing on a stationary score")
    bad_gate = {t: rebuild(sc2, b2, finT, t, 0) for t in range(1, T)}
    raises_on_broken(assert_gate_lagged, bad_gate, sc2, b2, finT, range(1, T),
                     lambda g, side, t: g[t], rebuild)
    print(f"    [X] a gate rebuilt from score[:, t] IS CAUGHT")

    # --- shape 3 --------------------------------------------------------
    sig = np.zeros((T, n_names), bool)
    sig[rng.random((T, n_names)) < 0.05] = True
    posm = lag1_mask(sig)
    kept = assert_mask_is_lagged(posm, sig)
    print(f"    shape 3 EVENT: {kept:,} positions, each exactly one bar after its signal")
    raises_on_broken(assert_mask_is_lagged, sig, sig)
    print(f"    [X] handing the RAW signal mask to the kernel IS CAUGHT -- this is D391's defect")

    # Hand case: [1, 2, 2, NaN, 5]. The AVERAGE-RANK convention counts the value ITSELF among the
    # ties, which is D347's definition -- so the unique minimum is 0.5/4 = 12.5%, not 0, and the
    # tied pair is (1 below + 0.5 x 2 tied)/4 = 50%, not 37.5%. My first expectation here was
    # 37.5 and it was wrong; the convention is the repo's, not mine to round.
    col = np.array([1.0, 2.0, 2.0, np.nan, 5.0])
    assert abs(pct_direct(col, 0) - 12.5) < 1e-9, pct_direct(col, 0)
    assert abs(pct_direct(col, 1) - 50.0) < 1e-9, pct_direct(col, 1)
    assert np.isnan(pct_direct(col, 3)), "a NaN row has no percentile"
    print(f"    pct_direct on a hand case with a tie and a NaN: "
          f"{pct_direct(col, 0):.1f} / {pct_direct(col, 1):.1f} (average-rank, ties include self)")

    t_, i_ = sample_events(sig, 50, np.random.default_rng(1))
    assert t_.size == 50 and sig[t_, i_].all(), "[E] sample_events returned a non-event"
    print(f"    sample_events: 50 drawn, every one a true event cell")

    # --- and the harness itself must be able to fail ---------------------
    try:
        raises_on_broken(lambda: None)
    except AssertionError as e:
        assert "CANNOT FAIL" in str(e)
        print(f"    [X] raises_on_broken itself rejects a no-op that never raises")
    else:
        raise AssertionError("raises_on_broken accepted a function that cannot fail")

    print("\nSELF-TEST PASSED\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    raise SystemExit(selftest())
