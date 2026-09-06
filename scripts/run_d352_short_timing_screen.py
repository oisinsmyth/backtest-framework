"""D352 -- a short-timing screen at the extreme the slot book trades: 139 declared short events, each scored
against its own names at random ELIGIBLE times.

    uv run python scripts/run_d352_short_timing_screen.py --selftest
    uv run python scripts/run_d352_short_timing_screen.py --screen [--workers 6]           stage 1: the grid, every member
    uv run python scripts/run_d352_short_timing_screen.py --kernel SIG/SHAPE --draws N --part p   stage 2: A' and B under the kernel
    uv run python scripts/run_d352_short_timing_screen.py --report                        stage 2: the kernel record + Q1..Q8

The family: the 46 dimensionless scores of D346's pool (D350's pool, the same file), floored (keep_v2), deal-
filtered (F0), on the warm base, lagged one bar, ranked cross-sectionally among floored live names (average rank
on ties, >= 50 finite names). Three SHORT event shapes on the percentile p -- S2 (p >= 98, prev < 98), S5 (95),
S10 (90; D349's shape) -- plus the rsi turn (rsi < 70, prev >= 70, on the raw lagged rsi). 46 x 3 + 1 = 139.
S10 on on_share, skew_63, close_in_range, rsi and the turn are D349's event matrices exactly ([G49]).

Stage 1 scores every member on the cached forward-40 hedged-excess grid F with the SHORT sign: E_s = mean of -F
over the member's event cells, every event counted. Control A' (D351): each name's events rolled in time within
its ELIGIBLE bars, offsets independent per name, the sparse gather of D350. Control B: each event's name
replaced by a random name in the same rsi bucket that day, the pool confined to eligible names WITH a defined
rsi percentile (D349 section 6: an undefined percentile digitises into the top bucket, where short events live).
1,000 draws each. Multiplicity: per-member p; BH at q = 0.10 over the 139; the family-wise grid-max under one
shared offset vector; M_eff by Li-Ji and Cheverud-Nyholt from the members' daily mean(-F) series.

Stage 2 runs D345's kernel fed (zeros, hi) with the RAW percentile as its score (invalidation exit: pct <= 50;
same-bar entries most extreme first) on the survivors of the declared gate: A' (within elig, the D351
assertions) and B (defined-percentile pool) at 100 draws, C (1,000 sign flips), the mirror (the LONG of the same
event), PUB/PB net per trade with and without D337's GC/HTB borrow and the breakeven half-spread, the four groups
per trade with the top trade named, the splits, and the rsi-bucket interaction on the SHORT base rate.

Everything shared is imported, not copied: d348_prep (the cached prep; loaded FIRST so memo_load is installed),
run_d350_long_timing_screen (grid machinery, controls, multiplicity, four groups), run_d349_short_signal_controls
(the short-side conventions: run_short, run_mirror, borrow_of, check_borrow, event_buckets, event_accounting).

ASSERTIONS [K][F0][R][F][G49][E][SP][A'][B][O][S][SB][M][BH][X][6] -- pre-reg section 6.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import multiprocessing as mp
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


PREP = _load("d348p", "d348_prep.py")                       # FIRST: installs memo_load; executes D347's alias chain once
V50 = _load("d350r", "run_d350_long_timing_screen.py")      # its own _load("d348p") is memoised to PREP
V49 = _load("d349r", "run_d349_short_signal_controls.py")   # likewise
V47 = PREP.V47
EB, BR, FL, UF = PREP.EB, PREP.BR, PREP.FL, PREP.UF

CAP, SEED, RSI_HI, BUCKET_EDGES, CONVS = V47.CAP, V47.SEED, V47.RSI_HI, V47.BUCKET_EDGES, V47.CONVS
STUDY = 352
SHAPES = ("S2", "S5", "S10")
THR = {"S2": 98.0, "S5": 95.0, "S10": 90.0}
TURN = "rsi/turn"
DRAWS, BLOCK = V50.DRAWS, V50.BLOCK
GATE_P, GATE_MIN_EVENTS, GATE_TOP, FALLBACK_TOP, BH_Q = V50.GATE_P, V50.GATE_MIN_EVENTS, V50.GATE_TOP, V50.FALLBACK_TOP, V50.BH_Q
D349_SCORES = ("on_share", "skew_63", "close_in_range", "rsi")
D349_OF = {"on_share/S10": "on_share", "skew_63/S10": "skew_63", "close_in_range/S10": "close_in_range", "rsi/S10": "rsi_decile",
           TURN: "rsi_turn"}
D349_COUNTS = {"on_share/S10": 22_646, "skew_63/S10": 8_985, "close_in_range/S10": 168_180, "rsi/S10": 45_290, TURN: 32_917}
TOP_BUCKET = V49.TOP_BUCKET                                 # 9: (98, 100] of the rsi percentile at t-1
PER_SHARE, BORROW_SCHEME = V49.PER_SHARE, V49.BORROW_SCHEME
SCREEN_OUT = REPO / "data" / "d352_screen.json"
CTRL = REPO / "data" / "d352_ctrl_{member}_p{part}.json"
OUT = REPO / "data" / "d352_short_timing_screen.json"

# D350's machinery, reused not copied
lagged, sparse_events, Rotator, control_A, control_B, BucketPools = (V50.lagged, V50.sparse_events, V50.Rotator, V50.control_A,
                                                                    V50.control_B, V50.BucketPools)
member_stats, overlap_share, bh_reject, m_eff_of, pairwise_corr, assert_M = (V50.member_stats, V50.overlap_share, V50.bh_reject,
                                                                            V50.m_eff_of, V50.pairwise_corr, V50.assert_M)
daily_series, oracle_events, noise_events, assert_oracle, p_A_of = (V50.daily_series, V50.oracle_events, V50.noise_events,
                                                                   V50.assert_oracle, V50.p_A_of)
four_groups, gate_pass, z_key, load_pool, clean = V50.four_groups, V50.gate_pass, V50.z_key, V50.load_pool, V50.clean
_nanmean_rows = V50._nanmean_rows


# ------------------------------------------------------------------ the family
def members_of(pool):
    return [f"{s}/{k}" for s in pool for k in SHAPES] + [TURN]


def member_index(pool, member):
    if member == TURN:
        return len(pool) * len(SHAPES)
    sig, k = member.split("/")
    return pool.index(sig) * len(SHAPES) + SHAPES.index(k)


def _prev(p):
    prev = np.full_like(p, np.nan)
    prev[1:] = p[:-1]
    return prev


def short_masks(p, elig, thr):
    """The SHORT event: a fresh entry into the top (100 - thr)% -- pct[t] >= thr and pct[t-1] < thr -- on eligible bars.
    thr = 90 is D349's `hi` verbatim."""
    prev = _prev(p)
    with np.errstate(invalid="ignore"):
        return (p >= thr) & (prev < thr) & elig


def turn_mask(r, elig):
    """D349's rsi turn verbatim: the raw lagged rsi crossing back down through 70."""
    prev = _prev(r)
    with np.errstate(invalid="ignore"):
        return (r < RSI_HI) & (prev >= RSI_HI) & elig


def score_events(P, sig, elig):
    """One score -> its members' sparse events (three shapes; rsi also carries the turn). The grids are built, used, dropped."""
    LAG = lagged(P, sig)
    pct = V47.percentile_grid(LAG)
    out = {f"{sig}/{k}": sparse_events(short_masks(pct, elig, THR[k])) for k in SHAPES}
    if sig == "rsi":
        out[TURN] = sparse_events(turn_mask(LAG, elig))
    return out


def member_dense(P, member, elig):
    """(hi, score): the short event grid and the score the kernel reads -- the RAW lagged percentile (the raw lagged rsi for the
    turn), so the invalidation exit is `score <= 50` and same-bar entries are ordered most extreme first (D349's convention)."""
    sig, shape = member.split("/")
    LAG = lagged(P, sig)
    if member == TURN:
        return np.ascontiguousarray(turn_mask(LAG, elig)), np.ascontiguousarray(LAG)
    pct = V47.percentile_grid(LAG)
    return np.ascontiguousarray(short_masks(pct, elig, THR[shape])), pct


# ------------------------------------------------------------------ the floor, the short statistic, the pools
def floor_sets(P):
    elig = np.array(P["elig"])
    bucket = np.array(P["bucket_rsi"])
    rsi_ok = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    elig_b = elig & rsi_ok                                       # D349's elig_b: control B's pool and the bucket base rates
    P["rsi_pct_ok"], P["elig_b"] = rsi_ok, elig_b                # what V49.event_buckets / control_b_defined read
    return elig, elig_b, rsi_ok, bucket


def setup(P):
    Fs = -np.asarray(P["F"])                                     # the SHORT statistic: -(forward-40 hedged excess)
    elig, elig_b, rsi_ok, bucket = floor_sets(P)
    assert Fs.shape == elig.shape == bucket.shape == (P["T"], P["n"])
    rot = Rotator(elig)                                          # A': within the ELIGIBLE bars (D351)
    pools_b = BucketPools(elig_b, bucket)
    return Fs, elig, elig_b, rsi_ok, bucket, rot, pools_b


def pools_for(t, i, Fs, pools_b, elig_b, rsi_ok, bucket):
    """Control B's pool for one member: the defined-percentile pool, and the count of the member's finite-F events whose OWN rsi
    percentile is undefined. Such an event digitises to bucket 9; V50.control_B requires every event name in its (day, bucket) pool
    and then REMOVES the group's event names before drawing -- so adding those event cells to the pool leaves every replacement a
    defined-percentile name, exactly as D349's kernel control B. D349 found none on its five members."""
    fin = np.isfinite(Fs[t, i]) if t.size else np.zeros(0, bool)
    n_undef = int((~rsi_ok[t[fin], i[fin]]).sum()) if t.size else 0
    if not n_undef:
        return pools_b, 0
    ev = np.zeros(elig_b.shape, bool)
    ev[t[fin], i[fin]] = True
    return BucketPools(elig_b | ev, bucket), n_undef


def short_member_stats(name, t, i, Fs, rot, pools_b, elig_b, rsi_ok, bucket, rng_A, rng_B, half, draws=DRAWS):
    """D350's member_stats on the SHORT statistic with control B's pool confined to defined-percentile names."""
    t, i = np.asarray(t, np.int32), np.asarray(i, np.int32)
    pools, n_undef = pools_for(t, i, Fs, pools_b, elig_b, rsi_ok, bucket)
    d, kp = member_stats(name, t, i, Fs, rot, pools, bucket, rng_A, rng_B, half, draws=draws)
    d["n_undefined_rsi_pct"] = n_undef
    return d, kp


# ------------------------------------------------------------------ the kernel's controls
def assert_on_floor(ss, hi, elig):
    assert not (ss & ~elig).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(ss.sum(axis=0), hi.sum(axis=0)), "[A'] per-name event count changed"


def aprime_draw(P, hi, sc, elig, rng):
    """A' (D351): the per-name rotation of the short events and their score within `elig`, with the two D351 assertions."""
    sl, ss, sc_ = EB.rotate_signals(np.zeros_like(hi), hi, sc, elig, rng)
    assert not sl.any(), "[A'] a long appeared in the rotation"
    assert_on_floor(ss, hi, elig)
    return ss, sc_


def control_b_kernel(P, hi, elig_b, rng):
    """D349's control_b_defined: D347's same-day same-bucket replacement drawn from names WITH a defined rsi percentile."""
    return V47.control_b_signal(dict(P, elig=elig_b), hi, rng)


def top_vs_rest(inter):
    """Q7: the top bucket's interaction minus the MOST NEGATIVE of the rest (< 0 iff the top bucket is the most negative)."""
    if TOP_BUCKET not in inter:
        return None
    rest = [v["interaction"] for b, v in inter.items() if b != TOP_BUCKET]
    return inter[TOP_BUCKET]["interaction"] - min(rest) if rest else None


def peak_rss_mb():
    try:
        import psutil
        mi = psutil.Process().memory_info()
        return float((getattr(mi, "peak_wset", None) or mi.rss) / 2 ** 20)
    except Exception:
        return None


# ------------------------------------------------------------------ the per-score job (process pool: the controls are GIL-bound)
_W = {}


def _init_worker():
    """Each process does its own cache-HIT prep (quietly) and builds the shared grid objects once."""
    with contextlib.redirect_stdout(io.StringIO()):
        P = PREP.prep(need_grids=True, verbose=False)
        Fs, elig, elig_b, rsi_ok, bucket, rot, pools_b = setup(P)
        _W.update(P=P, Fs=Fs, elig=elig, elig_b=elig_b, rsi_ok=rsi_ok, bucket=bucket, rot=rot, pools_b=pools_b, pool=load_pool(P))


def _score_job(args):
    """One score -> its members' rows and kept event arrays (3 shapes; rsi also the turn). Seeded per member."""
    sig, draws, half = args
    if not _W:
        _init_worker()
    P, Fs, elig, elig_b, rsi_ok, bucket, rot, pools_b, pool = (_W[k] for k in ("P", "Fs", "elig", "elig_b", "rsi_ok", "bucket", "rot",
                                                                              "pools_b", "pool"))
    ev = score_events(P, sig, elig)
    out = []
    for member, (t, i) in ev.items():
        mi = member_index(pool, member)
        d, kp = short_member_stats(member, t, i, Fs, rot, pools_b, elig_b, rsi_ok, bucket, np.random.default_rng([SEED, STUDY, 1, mi]),
                                   np.random.default_rng([SEED, STUDY, 2, mi]), half, draws=draws)
        out.append((member, d, kp))
    return out, peak_rss_mb()


# ------------------------------------------------------------------ stage 0: the assertions
def _direct_pct(v, i):
    fin = np.isfinite(v)
    if not fin[i]:
        return np.nan
    return (float((v[fin] < v[i]).sum()) + 0.5 * float((v[fin] == v[i]).sum())) / fin.sum() * 100.0


def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    T, n, r1T, finT, ocT, m_f, m_f_oc = P["T"], P["n"], P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"]
    half = T // 2
    pool = load_pool(P)
    members = members_of(pool)
    assert len(members) == 139 and len(set(members)) == 139 and member_index(pool, TURN) == 138
    assert [member_index(pool, m) for m in members] == list(range(139))
    print(f"    family: {len(pool)} scores x {len(SHAPES)} shapes + the rsi turn = {len(members)} members; thresholds "
          + ", ".join(f"{k} >= {THR[k]:.0f}" for k in SHAPES) + f"; turn rsi < {RSI_HI:.0f}")
    Fs, elig, elig_b, rsi_ok, bucket, rot, pools_b = setup(P)
    assert np.array_equal(bucket, V47.bucket_of(P["PCT"]["rsi"])), "bucket_rsi != bucket_of(PCT['rsi'])"
    n_undef_elig = int((elig & ~rsi_ok).sum())
    print(f"    the floor: {int(elig.sum()):,} eligible name-bars, {n_undef_elig:,} of them with an undefined rsi percentile (excluded from "
          f"control B's pool and the bucket base rates); the statistic is -F, finite on {int(np.isfinite(Fs).sum()):,} cells")
    rng = np.random.default_rng(STUDY)
    # [F] the SHORT grid -F equals a direct per-cell recomputation with the short sign (D349's loop)
    cells = np.argwhere(np.isfinite(Fs) & elig)
    sample = cells[rng.choice(len(cells), size=3000, replace=False)]
    worst_f = 0.0
    for t, i in sample:
        v = r1T[t:t + CAP, i].copy()
        mm = m_f[t:t + CAP].copy()
        v[0], mm[0] = ocT[t, i], m_f_oc[t]
        okk = finT[t:t + CAP, i] & np.isfinite(v) & np.isfinite(mm)
        okk[0] = True
        direct = -float(np.sum(np.where(okk, v - mm, 0.0)))
        worst_f = max(worst_f, abs(direct - Fs[t, i]))
    assert worst_f < 1e-9, f"[F] {worst_f:.2e}"
    print(f"    [F] the short forward-40 grid -F equals a direct per-cell recomputation with the short sign on 3,000 sampled cells to {worst_f:.1e}")
    # [G49] S10 on D349's four decile scores and the turn equal D349's event matrices exactly, with D349's counts
    V49.add_short_events(P)
    assert np.array_equal(P["elig_b"], elig_b) and np.array_equal(P["rsi_pct_ok"], rsi_ok), "[G49] elig_b != D349's"
    grids, masks = {}, {}
    for sig in D349_SCORES:
        LAG = lagged(P, sig)
        assert np.array_equal(LAG, P["LAG49"][sig], equal_nan=True), f"[G49] lagged {sig} != D349"
        pct = V47.percentile_grid(LAG)
        assert np.array_equal(pct, P["PCT49"][sig], equal_nan=True), f"[G49] percentile {sig} != D349"
        grids[sig] = (LAG, pct)
        for k in SHAPES:
            masks[f"{sig}/{k}"] = short_masks(pct, elig, THR[k])
    masks[TURN] = turn_mask(grids["rsi"][0], elig)
    for member, d349 in D349_OF.items():
        hi49, sc49 = P["EVENTS49"][d349]
        assert np.array_equal(masks[member], hi49), f"[G49] {member} != D349 events_for({d349})"
        sig = member.split("/")[0]
        sc_mine = grids[sig][0] if member == TURN else grids[sig][1]
        assert np.array_equal(sc_mine, sc49, equal_nan=True), f"[G49] {member} kernel score != D349's"
        cnt = int(masks[member].sum())
        assert cnt == D349_COUNTS[member], f"[G49] {member}: {cnt:,} events != D349's {D349_COUNTS[member]:,}"
        print(f"    [G49] {member:18s}: lagged score, percentile grid, event matrix and kernel score equal D349's events_for({d349}) "
              f"exactly -- {cnt:,} events (pre-reg check: {D349_COUNTS[member]:,})")
    ev = {m: sparse_events(mk) for m, mk in masks.items()}
    # [E] 300 sampled events per member of the four D349 scores: the definition by direct count at t-1, fresh at t-2, unlagged fails
    n_e = 0
    for member, (t_ev, i_ev) in ev.items():
        sig, k = member.split("/")
        LAG, pct = grids[sig]
        pick = rng.choice(t_ev.size, size=min(300, t_ev.size), replace=False)
        n_unl = 0
        for t, i in zip(t_ev[pick], i_ev[pick]):
            assert elig[t, i], f"[E] {member} ({t},{i}) not eligible"
            if member == TURN:
                assert LAG[t, i] < RSI_HI and LAG[t - 1, i] >= RSI_HI, f"[E] {member} ({t},{i})"
                s_t = LAG[t + 1, i] if t + 1 < T else np.nan                    # the rsi AT t: unlagged
                unl = s_t == s_t and s_t < RSI_HI and LAG[t, i] >= RSI_HI
            else:
                thr = THR[k]
                pd = _direct_pct(LAG[t], i)
                pp = _direct_pct(LAG[t - 1], i)
                assert pd >= thr - 1e-9 and (pp == pp and pp < thr), f"[E] {member} ({t},{i}) direct {pd:.3f} prev {pp:.3f}"
                p_t = pct[t + 1, i] if t + 1 < T else np.nan                    # the percentile of the score AT t: unlagged
                unl = p_t == p_t and p_t >= thr and pct[t, i] < thr
            n_unl += not unl
        assert n_unl == pick.size, f"[E] {member}: the unlagged condition holds on {pick.size - n_unl} sampled events"
        n_e += pick.size
    print(f"    [E] {n_e} sampled events ({len(ev)} members x 300) satisfy their shape on the raw lagged score by direct count at t-1 and t-2, "
          f"are eligible, and every one fails the unlagged condition ({el()})")
    del grids
    # [SP] sparse gather == dense rotation within eligible bars, 20 draws x 5 members + a tie-heavy synthetic grid; [A'] alongside
    five = ("on_share/S2", "skew_63/S5", "close_in_range/S10", "rsi/S2", TURN)
    rng_sp = np.random.default_rng([SEED, STUDY, 7])
    worst = 0.0
    for m in five:
        t_ev, i_ev = ev[m]
        worst = max(worst, V50.assert_sparse_equals_dense(t_ev, i_ev, Fs, rot, elig, rng_sp, 20, V50.dense_rotate_within_elig, m))
    Ts, ns = 90, 7
    rs = np.random.default_rng(3527)
    el_s = rs.random((Ts, ns)) > 0.3
    el_s[:6] = False
    el_s[:, 6] = False                                             # a name with no eligible bars
    el_s[40:, 5] = False
    F_s = -rs.integers(-2, 3, size=(Ts, ns)).astype(float)        # tie-heavy: five distinct values, short sign
    F_s[-3:] = np.nan
    ev_s = el_s & (rs.random((Ts, ns)) < 0.3)
    ts_, is_ = sparse_events(ev_s)
    V50.assert_sparse_equals_dense(ts_, is_, F_s, Rotator(el_s), el_s, rs, 20, V50.dense_rotate_within_elig, "synthetic")
    print(f"    [SP] the sparse control-A' gather equals the dense per-name roll within ELIGIBLE bars: identical cell sets and means on "
          f"20 draws x 5 members (statistic vs dense mean within {worst:.1e}) and on a tie-heavy {Ts}x{ns} synthetic grid")
    print(f"    [A'] every name's event count is preserved and every rotated cell is eligible on every one of those draws (rotated index arrays)")
    # [B] date and bucket kept; the pool contains only eligible names with a defined percentile; changed wherever the pool allows
    rng_b = np.random.default_rng([SEED, STUDY, 8])
    for m in five:
        t_ev, i_ev = ev[m]
        fin = np.isfinite(Fs[t_ev, i_ev])
        t_ev, i_ev = t_ev[fin], i_ev[fin]
        pools_m, n_undef = pools_for(t_ev, i_ev, Fs, pools_b, elig_b, rsi_ok, bucket)
        b = control_B(t_ev, i_ev, Fs, pools_m, bucket, rng_b, draws=3, block=3, return_last=True)
        L = b["last"]
        assert np.array_equal(np.sort(L["t"]), np.sort(t_ev)), f"[B] {m} dates"
        assert np.array_equal(bucket[L["t"], L["i_new"]], bucket[L["t"], L["i_orig"]]), f"[B] {m} bucket"
        assert rsi_ok[L["t"], L["i_new"]].all() and elig[L["t"], L["i_new"]].all(), f"[B] {m} a replacement is off the defined-percentile pool"
        changed = float((L["i_new"] != L["i_orig"]).mean())
        kept = b["n_kept"] / t_ev.size
        assert (L["i_new"][L["sample"]] != L["i_orig"][L["sample"]]).all(), f"[B] {m} a sampled event kept its name"
        assert abs(changed + kept - 1.0) < 1e-12, f"[B] {m} changed {changed:.4f} + kept {kept:.4f} != 1"
        assert changed > 0.99 or kept > 0.0, f"[B] {m} name changed on {100 * changed:.2f}%"
        comp = L["gid"].astype(np.int64) * n + L["i_new"]
        assert np.unique(comp[L["sample"]]).size == int(L["sample"].sum()), f"[B] {m} duplicate within a (day, bucket) group"
        assert not (np.isin(L["t"] * n + L["i_new"], t_ev.astype(np.int64) * n + i_ev)[L["sample"]]).any(), f"[B] {m} replacement is an event name"
        print(f"    [B] {m:18s}: every event keeps its date and rsi bucket; every replacement is eligible with a defined rsi percentile; name "
              f"changed on {100 * changed:.2f}% ({b['n_kept']} = {100 * kept:.2f}% kept for want of pool, the declared fallback); distinct per "
              f"day and bucket and never an event name; {n_undef} events with an undefined rsi percentile")
    # [O] the hurdle has teeth on -F: the oracle clears A' at p < 0.001; noise does not (<= 3 of 20 seeds below 0.05)
    rng_o = np.random.default_rng([SEED, STUDY, 9])
    t_or, i_or = oracle_events(Fs, elig, rng_o)
    p_or, E_or, A_or = assert_oracle(t_or, i_or, Fs, rot, rng_o)
    p_noise = []
    for s in range(20):
        r = np.random.default_rng([SEED, STUDY, 10, s])
        t_n, i_n = noise_events(Fs, elig, r)
        p_noise.append(p_A_of(t_n, i_n, Fs, rot, r)[0])
    n_low = int(sum(p < 0.05 for p in p_noise))
    assert n_low <= 3, f"[O] noise below 0.05 on {n_low} of 20 seeds"
    print(f"    [O] the oracle ({t_or.size:,} events in each name's own top decile of -F) clears A' at p = {p_or:.4f} (E {E_or * 1e4:+.0f} bp vs A' max "
          f"{A_or.max() * 1e4:+.0f}); the noise series is below 0.05 on {n_low} of 20 seeds (p50 of its p_A {np.median(p_noise):.2f}) ({el()})")
    # [S] sign in money on on_share/S2 SHORT events, cap exit: pnl == -(open-fill hedged excess); a riser pays negatively
    hi, sc = member_dense(P, "on_share/S2", elig)
    assert np.array_equal(hi, masks["on_share/S2"])
    res = V49.run_short(P, hi, sc, "cap")
    tr = res["trades"]
    assert all(t[4] == 1 for t in tr), "[S] a long in the short ledger"
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    ex = np.array([float((ocT[e0, row] - m_f_oc[e0]) + np.nansum(r1T[e0 + 1:e0 + age, row] - m_f[e0 + 1:e0 + age]))
                   for row, e0, age, _p, _s in tr])
    assert (pnl[ex > 0] < 0).all() and (pnl[ex < 0] > 0).all(), "[S] short sign"
    assert float(np.abs(pnl + ex).max()) < 1e-9, "[S] pnl != -(excess)"                 # the nansum form (D349's tolerance)
    acc = V49.event_accounting(P, hi, res)
    print(f"    [S] SIGN IN MONEY: every on_share/S2 cap-exit SHORT trade equals -(open-fill hedged excess against the floored market) to "
          f"{worst_s:.1e}; a name that rises against the market pays negatively, one that falls pays positively ({len(tr):,} trades; "
          f"{int((ex > 0).sum()):,} rose, {int((ex < 0).sum()):,} fell)")
    print(f"    check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + "
          f"{acc['unpriced']:,} unpriced; trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    # [SB] the borrow on 200 sampled trades
    pt, htb, rate = V49.borrow_of(P, tr)
    idx_sb, worst_b = V49.check_borrow(P, tr, pt, htb, rng, k=200)
    assert (rate[htb] == BR.HTB_BPS).all() and (rate[~htb] == BR.GC_BPS).all(), "[SB] rates"
    print(f"    [SB] BORROW: on {len(idx_sb)} sampled short trades the per-trade borrow equals the rule x bars held / 252 to {worst_b:.1e}, and "
          f"every HTB flag agrees with the F0-window / ${BR.PX_HTB:.0f} rule; HTB on {int(htb.sum())} of {len(tr):,}; mean borrow {pt.mean():.2f} bp per trade")
    # [A'] under the kernel: the D351 assertions on one draw, no NaN; [B] under the kernel keeps date and bucket, defined-percentile names
    rng_k = np.random.default_rng([SEED, STUDY, 11])
    ss, sc_ = aprime_draw(P, hi, sc, elig, rng_k)
    pa = V47.pnl_bp(V49.run_short(P, ss, sc_, "cap"))
    assert np.isfinite(pa).all(), "[A'] NaN P&L in a rotated draw"
    sB = control_b_kernel(P, hi, elig_b, rng_k)
    assert np.array_equal(sB.sum(axis=1), hi.sum(axis=1)), "[B] kernel: dates changed"
    assert sorted(bucket[hi].tolist()) == sorted(bucket[sB].tolist()), "[B] kernel: bucket multiset changed"
    assert rsi_ok[sB].all() and elig[sB].all(), "[B] kernel: a replacement is off the defined-percentile pool"
    assert (sB & hi).sum() <= 0.05 * hi.sum(), "[B] kernel: too many names unchanged"
    print(f"    [A'] under the kernel: one draw of on_share/S2 keeps every name's event count, every rotated event is eligible, no NaN "
          f"({pa.size:,} trades, mean {pa.mean():+.1f} bp); [B] under the kernel keeps every date and bucket, every replacement eligible with a "
          f"defined percentile ({int((sB & hi).sum())} of {int(hi.sum()):,} unchanged by chance) ({el()})")
    # [M] on synthetic series, 139 wide; [BH] textbook rejections (D350's checks at this family's width)
    rs = np.random.default_rng(35211)
    S = rs.normal(size=(139, 400))
    S[rs.random(S.shape) < 0.3] = np.nan
    C, n_bad = pairwise_corr(S)
    liji, nyh, _, liji_abs = assert_M(C, "synthetic")
    assert abs(m_eff_of(np.eye(139))[0] - 139) < 1e-9 and abs(m_eff_of(np.eye(139))[1] - 139) < 1e-9, "[M] identity"
    l1, n1, _, l1_abs = m_eff_of(np.ones((139, 139)))
    assert 1.0 - 1e-9 <= l1_abs <= 2.0 + 1e-6 and abs(n1 - 1.0) < 1e-6, f"[M] rank-one {l1_abs} / {n1}"
    print(f"    [M] pairwise-complete correlation: symmetric, unit diagonal; M_eff on 139 independent synthetic series Li-Ji {liji:.1f} "
          f"(|lambda| {liji_abs:.1f}) CN {nyh:.1f}; identity -> 139.0 / 139.0; rank-one -> |lambda| Li-Ji {l1_abs:.1f} / CN {n1:.1f} (verbatim Li-Ji {l1:.0f})")
    r1 = bh_reject([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.07, 0.4], 0.05)
    assert r1.tolist() == [True, True, False, False, False, False, False, False], f"[BH] {r1}"
    assert bh_reject([0.04, 0.041, 0.042], 0.10).all(), "[BH] step-up"
    assert bh_reject([0.001, 0.02, 0.021, 0.5], 0.10).tolist() == [True, True, True, False], "[BH]"
    assert not bh_reject([0.2, 0.5, 0.9], 0.10).any(), "[BH] none"
    print("    [BH] Benjamini-Hochberg recovers the textbook rejections: 2 of 8 at q=.05; the step-up rejects all of [.04,.041,.042] at q=.10; "
          "3 of 4 on [.001,.02,.021,.5]; none on [.2,.5,.9]")
    # [6] the checks fail when they should
    broke = 0
    try:                                                            # [S] on a short ledger handed +50 bp
        assert np.abs(FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc) - (pnl + 50e-4)).max() < 1e-12
    except AssertionError:
        broke += 1
    try:                                                            # [A'] on D347's rotation within finT
        _sl, ss_f, _sc = V47.rotate_confined(P, np.zeros_like(hi), hi, sc, np.random.default_rng(5))
        assert_on_floor(ss_f, hi, elig)
    except AssertionError as e:
        assert "off the floor" in str(e) or "count" in str(e)
        broke += 1
    try:                                                            # [O] on noise in the oracle's place
        r = np.random.default_rng([SEED, STUDY, 10, 0])
        t_n, i_n = noise_events(Fs, elig, r)
        assert_oracle(t_n, i_n, Fs, rot, r)
    except AssertionError:
        broke += 1
    assert broke == 3, f"[6] {broke} of 3 raised"
    print("    [6] [S] raises on a short ledger handed +50 bp; [A'] raises on a draw rotated within finT; [O] raises when the oracle is replaced by noise")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


# ------------------------------------------------------------------ stage 1: the grid
def stage_screen(P, scores=None, out=SCREEN_OUT, draws=DRAWS, workers=6):
    t_start = time.time()
    el = lambda: f"{time.time() - t_start:.0f}s"
    T, n = P["T"], P["n"]
    half = T // 2
    pool = load_pool(P)
    dev = scores is not None
    scores = scores or pool
    members = [f"{s}/{k}" for s in scores for k in SHAPES] + ([TURN] if "rsi" in scores else [])
    Fs, elig, elig_b, rsi_ok, bucket, rot, pools_b = setup(P)
    print(f"\nSTAGE 1 -- the grid: {len(members)} SHORT members, {draws} draws per control; -F finite on {int(np.isfinite(Fs).sum()):,} cells, "
          f"eligible {int(elig.sum()):,}, with a defined rsi percentile {int(elig_b.sum()):,}; era midpoint bar {half} ({P['dates'][half]})")
    jobs = [(s, draws, half) for s in scores]
    rss = []
    if workers > 1:
        with mp.get_context("spawn").Pool(workers, initializer=_init_worker) as pl:
            results = pl.map(_score_job, jobs, chunksize=1)
    else:
        _W.update(P=P, Fs=Fs, elig=elig, elig_b=elig_b, rsi_ok=rsi_ok, bucket=bucket, rot=rot, pools_b=pools_b, pool=pool)
        results = [_score_job(j) for j in jobs]
    res = {}
    for rows_, peak in results:
        rss.append(peak)
        for member, d, kp in rows_:
            res[member] = (d, kp)
    rows = [res[m][0] for m in members]
    keep = {m: res[m][1] for m in members}
    rss_ok = [r for r in rss if r is not None]
    n_undef = int(sum(d.get("n_undefined_rsi_pct", 0) for d in rows))
    print(f"  events and controls A' and B done for {len(members)} members on {workers} worker{'s' if workers > 1 else ''} ({el()}); "
          f"degenerate: {sum(1 for d in rows if d.get('degenerate'))}; events with an undefined rsi percentile: {n_undef}; "
          + (f"peak working set per worker process: max {max(rss_ok):,.0f} MB, median {np.median(rss_ok):,.0f} MB" if rss_ok else "peak RSS unavailable"))
    # the family-wise grid-max under ONE shared offset vector per draw
    live = [m for m in members if keep[m] is not None and keep[m]["A_sd"] > 0]
    rng_g = np.random.default_rng([SEED, STUDY, 3])
    maxz, done = [], 0
    while done < draws:
        B = min(50, draws - done)
        off = rot.draw_offsets(rng_g, B)
        Z = np.full((B, len(live)), -np.inf)
        for j, m in enumerate(live):
            km = keep[m]
            Er = _nanmean_rows(Fs[rot.rotate(km["t"], km["i"], off), km["i"][None, :]])
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
    # M_eff from the daily mean(-F) event series
    S = np.full((len(members), T), np.nan)
    for j, m in enumerate(members):
        if keep[m] is not None:
            S[j] = daily_series(keep[m]["t"], keep[m]["Fe"], T)
    C, n_bad = pairwise_corr(S)
    liji, nyh, eig, liji_abs = assert_M(C, "family")
    iu = np.triu_indices(len(members), 1)
    n_neg = int((eig < -1e-9).sum())
    print(f"    [M] correlation of {len(members)} daily mean(-F) series: symmetric, unit diagonal; {n_bad} pairs with < 10 common days set to 0; "
          f"pairwise median {np.median(C[iu]):+.3f} max {C[iu].max():+.3f}; M_eff Li-Ji {liji:.1f}, Cheverud-Nyholt {nyh:.1f} (nominal {len(members)}); "
          f"{n_neg} negative eigenvalues (min {eig.min():+.3f}); Li-Ji on |lambda| {liji_abs:.1f}")
    # BH and the gate
    pA = np.array([d["p_A"] for d in rows])
    rej = bh_reject(pA, BH_Q)
    for d, r in zip(rows, rej):
        d["bh_reject"] = bool(r)
        d["gate_pass"] = gate_pass(d)
    passers = [d for d in ranked if d["gate_pass"]][:GATE_TOP]
    fallback = not passers
    survivors = [d["member"] for d in (passers if passers else [d for d in ranked if not d.get("degenerate")][:FALLBACK_TOP])]
    n_p05 = int((pA <= GATE_P).sum())
    d349 = {m: next(j for j, d in enumerate(ranked) if d["member"] == m) + 1 for m in D349_OF if m in members}
    check = {m: (res[m][0]["n_events_raw"] == D349_COUNTS[m]) for m in D349_OF if m in members}
    assert all(check.values()), f"[G49] event counts differ from D349's: {[(m, res[m][0]['n_events_raw']) for m, ok in check.items() if not ok]}"
    # ---- print ----
    print("\n" + "=" * 150)
    print("THE GRID -- -(forward-40 hedged excess) per SHORT event (bp), every event counted; A' = own names at random ELIGIBLE times, "
          "B = same day same rsi bucket, defined-percentile pool")
    print("=" * 150)
    print("  %4s %-20s %6s %5s %5s %7s %7s %7s %7s %6s %6s %6s %7s %7s %6s %4s" % (
        "rank", "member", "n", "names", "ovl%", "E", "A' p50", "A' p95", "TV", "z_A", "p_A", "p_B", "TV e1", "TV e2", "top1%", "gate"))
    show = list(range(min(20, len(ranked)))) + sorted(r - 1 for r in d349.values() if r > 20)
    for j in show:
        d = ranked[j]
        if d.get("degenerate"):
            print("  %4d %-20s %6d  degenerate" % (j + 1, d["member"], d["n_events"]))
            continue
        print("  %4d %-20s %6d %5d %5.1f %+7.1f %+7.1f %+7.1f %+7.1f %+6.2f %6.3f %6.3f %+7.1f %+7.1f %6s %4s" % (
            j + 1, d["member"], d["n_events"], d["n_names"], 100 * d["overlap_share"], d["E_bp"], d["A_p50_bp"], d["A_p95_bp"], d["TV_bp"],
            z_key(d), d["p_A"], d["p_B"], d["TV_era1_bp"] or 0, d["TV_era2_bp"] or 0,
            ("%.0f%%" % (100 * d["top1pct_share"])) if d["top1pct_share"] is not None else "-", "PASS" if d["gate_pass"] else ""))
    print(f"\n  D349's members rank: " + ", ".join(f"{m} #{r}" for m, r in d349.items()))
    print(f"  members with p_A <= 0.05: {n_p05} of {len(members)}; BH at q={BH_Q} rejects {int(rej.sum())}"
          + (": " + ", ".join(d["member"] for d in ranked if d["bh_reject"]) if rej.any() else ""))
    print(f"  M_eff Li-Ji {liji:.1f} / Cheverud-Nyholt {nyh:.1f}; false discovery alone at 0.05 gives {0.05 * liji:.1f} / {0.05 * nyh:.1f}")
    print(f"  grid-max p for {best['member']}: {p_max:.3f} ({n_ge} of {draws} shared-offset draws reach its z_A)")
    print(f"  GATE (p_A <= .05, p_B <= .05, TV > 0 both eras, n >= 2000; top {GATE_TOP} by z_A): "
          + (f"{len(passers)} pass -> {survivors}" if passers else f"NONE pass -> fallback top {FALLBACK_TOP} by z_A {survivors}"))
    by_shape = {k: [d for d in rows if d["shape"] == k and not d.get("degenerate")] for k in SHAPES + ("turn",)}
    print("  by shape: " + "; ".join(f"{k} n={len(v)} p_A<=.05 on {sum(1 for d in v if d['p_A'] <= GATE_P)}, A' p50 median "
                                     f"{np.median([d['A_p50_bp'] for d in v]):+.1f}, TV median {np.median([d['TV_bp'] for d in v]):+.1f}"
                                     for k, v in by_shape.items() if v))
    q = grid_predictions(rows, liji, nyh)
    print("\nPRELIMINARY (grid-only) PREDICTIONS -- Q1, Q4, Q5, Q7 need the kernel (--report); Q8 here is the grid's A'")
    print_grid_predictions(q, rows, liji, nyh)
    out_d = dict(note="D352 stage 1: the grid. 139 SHORT members = 46 scores x {S2, S5, S10} + the rsi turn, scored as mean(-F) over the "
                      "event cells against control A' (own names at random ELIGIBLE times; D351's domain) and control B (same day, same rsi "
                      "bucket, another name from the defined-percentile pool). Every event counted (the kernel drops overlaps: overlap_share). "
                      "Nothing is a book.",
                 pool=pool, shapes=SHAPES, thresholds=THR, turn=TURN, draws=draws, cap=CAP, era_midpoint_bar=half,
                 era_midpoint_date=P["dates"][half], n_eligible=int(elig.sum()), n_eligible_defined_pct=int(elig_b.sum()),
                 members=rows, ranked=[d["member"] for d in ranked],
                 gate=dict(p=GATE_P, min_events=GATE_MIN_EVENTS, top=GATE_TOP, n_pass=len(passers), survivors=survivors, fallback=fallback),
                 n_pA_le_05=n_p05, bh=dict(q=BH_Q, n_reject=int(rej.sum()), rejected=[d["member"] for d in ranked if d["bh_reject"]]),
                 m_eff=dict(li_ji=liji, cheverud_nyholt=nyh, li_ji_abs_lambda=liji_abs, eigen_top5=[float(e) for e in eig[:5]],
                            eigen_min=float(eig.min()), n_negative_eigen=n_neg, pairs_zeroed=n_bad,
                            corr_median=float(np.median(C[iu])), corr_max=float(C[iu].max())),
                 grid_max=dict(draws=draws, best_member=best["member"], best_z=best.get("z_A"), p_max=p_max, n_draws_ge_best=n_ge,
                               max_z_p50=float(np.median(maxz)), max_z_p95=float(np.quantile(maxz, .95)), max_z_max=float(maxz.max())),
                 d349_ranks=d349, d349_count_check=check, n_undefined_rsi_pct_events=n_undef, predictions_grid=q,
                 workers=workers, peak_rss_mb_per_worker=rss_ok, elapsed_s=time.time() - t_start, dev=dev)
    out.write_text(json.dumps(clean(out_d), indent=1))
    print(f"\nwrote {out.relative_to(REPO)}  (screen {el()}; total {time.time() - P['t0']:.0f}s)")
    return out_d


def grid_predictions(rows, liji, nyh):
    by = {d["member"]: d for d in rows}
    live = lambda m: m in by and not by[m].get("degenerate")
    q = {}
    q["Q2_by_score"] = {s: bool(live(f"{s}/S2") and live(f"{s}/S10") and by[f"{s}/S2"]["p_A"] <= GATE_P and by[f"{s}/S10"]["p_A"] > GATE_P)
                        for s in ("on_share", "skew_63")}
    q["Q2"] = bool(all(q["Q2_by_score"].values()))
    n_p05 = int(sum(1 for d in rows if d["p_A"] <= GATE_P))
    q["Q3"] = bool(n_p05 > 0.05 * liji + 2)
    q["Q3_cheverud_nyholt"] = bool(n_p05 > 0.05 * nyh + 2)
    s2 = [d for d in rows if d["shape"] == "S2" and not d.get("degenerate")]
    q["Q6"] = bool(s2) and all(d["A_p50_bp"] < 0 for d in s2)
    q["Q8_grid"] = bool(live(TURN) and by[TURN]["E_bp"] <= by[TURN]["A_p95_bp"])
    return q


def print_grid_predictions(q, rows, liji, nyh):
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    by = {d["member"]: d for d in rows}
    f = lambda m: f"{m} p_A {by[m]['p_A']:.3f}" if m in by and not by[m].get("degenerate") else f"{m} absent"
    n_p05 = int(sum(1 for d in rows if d["p_A"] <= GATE_P))
    s2 = [d for d in rows if d["shape"] == "S2" and not d.get("degenerate")]
    print(f"  Q2 on_share and skew_63: S2 at p_A <= .05 and S10 not: {v(q['Q2'])} -- "
          + "; ".join(f"{s} {v(q['Q2_by_score'][s])} ({f(s + '/S2')}, {f(s + '/S10')})" for s in q["Q2_by_score"]))
    print(f"  Q3 members at p_A <= .05 exceed 0.05 x M_eff + 2: {v(q['Q3'])} -- {n_p05} vs {0.05 * liji + 2:.1f} (Li-Ji); "
          f"{v(q['Q3_cheverud_nyholt'])} vs {0.05 * nyh + 2:.1f} (Cheverud-Nyholt)")
    print(f"  Q6 A' centred below zero for every S2 member: {v(q['Q6'])} -- {sum(1 for d in s2 if d['A_p50_bp'] < 0)} of {len(s2)} below zero"
          + (f"; A' p50 range {min(d['A_p50_bp'] for d in s2):+.1f} to {max(d['A_p50_bp'] for d in s2):+.1f}" if s2 else ""))
    t = by.get(TURN)
    print(f"  Q8 the rsi turn inside A' p95 (grid): {v(q['Q8_grid'])} -- " + (f"E {t['E_bp']:+.1f} vs A' p95 {t['A_p95_bp']:+.1f} (p_A {t['p_A']:.3f})"
                                                                            if t and not t.get("degenerate") else "turn absent"))


# ------------------------------------------------------------------ stage 2: the kernel
def ctrl_path(member, part):
    return Path(str(CTRL).format(member=member.replace("/", "-"), part=part))


def stage_kernel(P, member, draws, part):
    pool = load_pool(P)
    assert member in members_of(pool), member
    mi = member_index(pool, member)
    elig, elig_b, rsi_ok, bucket = floor_sets(P)
    hi, sc = member_dense(P, member, elig)
    zeros = np.zeros_like(hi)
    res = V47.run_events(P, zeros, hi, sc, "cap")
    obs = float(V47.pnl_bp(res).mean())
    print(f"\n  {member} part {part}: {int(hi.sum()):,} short events -> {len(res['trades']):,} trades; observed mean hedged excess, SHORT, cap exit {obs:+.2f} bp")
    rngA = np.random.default_rng([SEED, STUDY, 4, mi, part])
    rngB = np.random.default_rng([SEED, STUDY, 5, mi, part])
    A_, B_ = [], []
    ts = time.time()
    for d in range(draws):
        ss, sc_ = aprime_draw(P, hi, sc, elig, rngA)                    # A' ONLY: within elig, the D351 assertions (no finT rotation)
        pa = V47.pnl_bp(V47.run_events(P, zeros, ss, sc_, "cap"))
        assert np.isfinite(pa).all(), "[A'] NaN in a rotated draw"
        A_.append(float(pa.mean()))
        sB = control_b_kernel(P, hi, elig_b, rngB)
        B_.append(float(V47.pnl_bp(V47.run_events(P, zeros, sB, sc, "cap")).mean()))
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {member}: {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.1f}s per draw)", flush=True)
    out = dict(member=member, draws=draws, part=part, observed=obs, trades=len(res["trades"]), events=int(hi.sum()), control_A=A_, control_B=B_,
               note="control_A is A' (D351): the rotation within the ELIGIBLE bars; control_B draws from the defined-percentile pool")
    f = ctrl_path(member, part)
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A' p50 {np.median(A_):+.2f} p95 {np.quantile(A_, .95):+.2f}; B p50 {np.median(B_):+.2f} p95 {np.quantile(B_, .95):+.2f} "
          f"({time.time() - P['t0']:.0f}s)")


def trade_stats(P, tr, pnl, elig, half, down, is_short):
    r1T, m_f, ocT, m_f_oc, beta, HALF, CLOSE, years = P["r1T"], P["m_f"], P["ocT"], P["m_f_oc"], P["beta"], P["HALF"], P["CLOSE"], P["years"]
    pb = V47.pnl_beta_adjusted(tr, r1T, m_f, ocT, m_f_oc, beta) * 1e4
    yrs = np.array([years[t[1]] for t in tr])
    eras = np.array([t[1] < half for t in tr])
    c2 = {cv: V47.two_c(tr, HALF[cv], CLOSE) for cv in CONVS}
    in_down = np.isin(yrs, list(down))
    mean = float(pnl.mean())
    d_ = dict(trades=len(tr), mean_bp=mean, median_bp=float(np.median(pnl)), t=float(mean / (pnl.std(ddof=1) / np.sqrt(pnl.size))),
              share_pos=float((pnl > 0).mean()), hold_mean=float(np.mean([t[2] for t in tr])),
              beta_adj_mean_bp=float(np.nanmean(pb)), beta_median=float(np.nanmedian([beta[t[1], t[0]] for t in tr])),
              two_c={cv: c2[cv][0] for cv in CONVS}, net_per_trade={cv: mean - c2[cv][0] for cv in CONVS},
              held_half={cv: c2[cv][1] for cv in CONVS}, held_price=c2["PUB"][2],
              down_years_mean_bp=(float(pnl[in_down].mean()) if in_down.any() else None), down_years_n=int(in_down.sum()),
              era1_mean_bp=float(pnl[eras].mean()) if eras.any() else None, era2_mean_bp=float(pnl[~eras].mean()) if (~eras).any() else None,
              by_year={int(y): float(pnl[yrs == y].mean()) for y in np.unique(yrs)}, four_groups=four_groups(tr, pnl, P, elig))
    if is_short:
        pt, htb, _rate = V49.borrow_of(P, tr)
        bm = float(pt.mean())
        comm = 2.0 * PER_SHARE / c2["PUB"][2] * 1e4                       # the commission half of 2c, bp per trade
        d_["borrow"] = dict(scheme=BORROW_SCHEME, mean_bp=bm, median_bp=float(np.median(pt)), htb_share=float(htb.mean()), gc_bps=BR.GC_BPS,
                            htb_bps=BR.HTB_BPS)
        d_["net_per_trade_borrow"] = {cv: mean - c2[cv][0] - bm for cv in CONVS}
        d_["breakeven_half_spread_bp_side"] = (mean - bm - comm) / 2.0
    return d_


def stage_report(P):
    assert SCREEN_OUT.exists(), "run --screen first"
    screen = json.loads(SCREEN_OUT.read_text())
    survivors, fallback = screen["gate"]["survivors"], screen["gate"]["fallback"]
    by_member = {d["member"]: d for d in screen["members"]}
    T = P["T"]
    half = T // 2
    down = set(P["down_years"])
    elig, elig_b, rsi_ok, bucket = floor_sets(P)
    Fs = -np.asarray(P["F"])
    Fm = elig_b & np.isfinite(Fs)                                          # base rates confined to defined-percentile name-bars
    E_all = float(np.nanmean(Fs[Fm])) * 1e4
    E_b = {b: (float(np.nanmean(Fs[Fm & (bucket == b)])) * 1e4 if (Fm & (bucket == b)).any() else np.nan) for b in range(10)}
    print(f"\nSTAGE 2 -- the kernel on {'the gate survivors' if not fallback else 'the FALLBACK top 3 by z_A (nothing passed the gate)'}: {survivors}")
    print(f"  SHORT BASE RATES: -(forward-40 hedged excess), eligible name-bars with a defined rsi percentile {E_all:+.1f} bp; by rsi bucket: "
          + " ".join(f"b{b}:{E_b[b]:+.0f}" for b in range(10)))
    REPORT, CHECK = {}, {}
    rngC = np.random.default_rng([SEED, STUDY, 6])
    for member in survivors:
        hi, sc = member_dense(P, member, elig)
        R_ = {}
        for lens in ("short", "mirror"):
            for exit_ in ("cap", "invalidation"):
                res = V49.run_short(P, hi, sc, exit_) if lens == "short" else V49.run_mirror(P, hi, sc, exit_)
                tr = res["trades"]
                assert all(t[4] == (1 if lens == "short" else 0) for t in tr), f"{member} {lens}: wrong side in the ledger"
                pnl = V47.pnl_bp(res)
                d_ = trade_stats(P, tr, pnl, elig, half, down, lens == "short")
                d_["events"] = int(hi.sum())
                if lens == "short" and exit_ == "cap":
                    CHECK[member] = V49.event_accounting(P, hi, res)
                    b_ev = V49.event_buckets(P, tr)                           # -1 where the rsi percentile is undefined
                    Es = float(pnl.mean())
                    inter = {}
                    for b in range(10):
                        mb = b_ev == b
                        if mb.any():
                            Esb = float(pnl[mb].mean())
                            inter[b] = dict(n=int(mb.sum()), E_sb=Esb, E_b=E_b[b], interaction=Esb - E_b[b] - Es + E_all)
                    groups = [b for b in range(-1, 10) if (b_ev == b).any()]
                    assert sum(int((b_ev == b).sum()) for b in groups) == pnl.size, f"[X] {member} buckets do not partition the trades"
                    tot = sum((b_ev == b).sum() * (pnl[b_ev == b].mean() - Es) for b in groups)
                    assert abs(tot) < 1e-9 * max(1.0, float(np.abs(pnl).sum())), f"[X] {member} {tot}"
                    print(f"    [X] {member}: the buckets partition the {len(tr):,} trades ({int((b_ev < 0).sum())} with an undefined rsi percentile, "
                          f"excluded and counted) and sum_b n_b (E_sb - E_s) = {tot:.2e}")
                    d_["interaction"] = inter
                    d_["events_undefined_rsi_bucket"] = int((b_ev < 0).sum())
                    d_["top_vs_rest"] = top_vs_rest(inter)
                    signs = rngC.choice([-1.0, 1.0], size=(1000, pnl.size))
                    cC = (signs * pnl[None, :]).mean(axis=1)
                    d_["control_C"] = dict(p50=float(np.median(cC)), p95=float(np.quantile(cC, .95)), max=float(cC.max()), draws=1000,
                                           above=bool(Es > np.quantile(cC, .95)))
                R_[f"{lens}/{exit_}"] = d_
        parts = sorted(REPO.glob(f"data/d352_ctrl_{member.replace('/', '-')}_p*.json"))
        if parts:
            cs_ = [json.loads(p.read_text()) for p in parts]
            obs = R_["short/cap"]["mean_bp"]
            for c in cs_:
                assert abs(c["observed"] - obs) < 1e-9, f"observed differs between stages for {member}"
                assert c["trades"] == R_["short/cap"]["trades"], f"trade count differs between stages for {member}"
            A_ = np.concatenate([np.array(c["control_A"]) for c in cs_])
            B_ = np.concatenate([np.array(c["control_B"]) for c in cs_])
            R_["controls"] = dict(draws=int(sum(c["draws"] for c in cs_)), parts=[p.name for p in parts],
                                  A=dict(p50=float(np.median(A_)), p95=float(np.quantile(A_, .95)), max=float(A_.max()),
                                         distinct=int(len(set(A_.tolist()))), above=bool(obs > np.quantile(A_, .95))),
                                  B=dict(p50=float(np.median(B_)), p95=float(np.quantile(B_, .95)), max=float(B_.max()),
                                         distinct=int(len(set(B_.tolist()))), above=bool(obs > np.quantile(B_, .95))),
                                  timing_value=float(obs - np.median(A_)))
        R_["grid"] = by_member[member]
        REPORT[member] = R_

    # ---- print ----
    print("\n" + "=" * 140)
    print("THE SURVIVORS UNDER THE KERNEL -- every event taken, next-open fill, hedged against the floored market; bp per trade (mirror = the LONG of the same event)")
    print("=" * 140)
    print("  %-18s %-6s %-12s %7s %6s %8s %8s %6s %7s %8s %9s %9s %9s %8s %9s" % ("member", "side", "exit", "events", "n", "mean", "median", "t", "hold",
                                                                                "beta-adj", "net PUB", "net PB", "PUB+brw", "down-yr", "eras"))
    for member in survivors:
        for key, d_ in REPORT[member].items():
            if key in ("controls", "grid"):
                continue
            lens, exit_ = key.split("/")
            print("  %-18s %-6s %-12s %7d %6d %+8.1f %+8.1f %+6.2f %7.1f %+8.1f %+9.1f %+9.1f %9s %8s %9s" % (
                member, lens, exit_, d_["events"], d_["trades"], d_["mean_bp"], d_["median_bp"], d_["t"], d_["hold_mean"], d_["beta_adj_mean_bp"],
                d_["net_per_trade"]["PUB"], d_["net_per_trade"]["PB"],
                ("%+.1f" % d_["net_per_trade_borrow"]["PUB"]) if "net_per_trade_borrow" in d_ else "-",
                ("%+.0f" % d_["down_years_mean_bp"]) if d_["down_years_mean_bp"] is not None else "-",
                "%+.0f/%+.0f" % (d_["era1_mean_bp"] or 0, d_["era2_mean_bp"] or 0)))
    print(f"\n  down-years (floored market negative): {P['down_years']}")
    print("\n  CHECK (short, cap exit): events = entries + on names already held + unpriced; trades = entries - open at the end")
    for member in survivors:
        c = CHECK[member]
        print(f"  {member:18s} events {c['events']:7,} = {c['entries']:7,} + {c['already_held']:6,} + {c['unpriced']:3,}; trades {c['trades']:6,} = "
              f"{c['entries']:6,} - {c['open_at_end']}")
    print("\n  CONTROLS on the short cap-exit statistic (mean hedged excess, bp) -- grid (stage 1) beside kernel (stage 2); A' within elig:")
    print("  %-18s %8s %8s %6s | %8s %8s %8s %4s %6s | %8s %8s %8s %4s %6s | %8s %8s %6s | %8s" % (
        "member", "grid E", "grid TV", "p_A", "A' p50", "A' p95", "A' max", "dist", "above", "B p50", "B p95", "B max", "dist", "above",
        "C p95", "C max", "above", "timing'"))
    for member in survivors:
        R_, g = REPORT[member], REPORT[member]["grid"]
        c, cc = R_.get("controls"), R_["short/cap"]["control_C"]
        if c:
            print("  %-18s %+8.1f %+8.1f %6.3f | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %6s | %+8.2f" % (
                member, g["E_bp"], g["TV_bp"], g["p_A"], c["A"]["p50"], c["A"]["p95"], c["A"]["max"], c["A"]["distinct"], "yes" if c["A"]["above"] else "NO",
                c["B"]["p50"], c["B"]["p95"], c["B"]["max"], c["B"]["distinct"], "yes" if c["B"]["above"] else "NO",
                cc["p95"], cc["max"], "yes" if cc["above"] else "NO", c["timing_value"]))
        else:
            print(f"  {member:18s} {g['E_bp']:+8.1f} {g['TV_bp']:+8.1f} {g['p_A']:6.3f} | kernel controls A'/B not run (--kernel); C p95 {cc['p95']:+.2f} "
                  f"max {cc['max']:+.2f} {'yes' if cc['above'] else 'NO'}")
    print("\n  FOUR GROUPS per trade (short, cap exit):")
    for member in survivors:
        g4 = REPORT[member]["short/cap"]["four_groups"]
        tt = g4["top_trade"]
        print(f"  {member}: n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% payoff "
              f"{g4['payoff'] if g4['payoff'] is None else round(g4['payoff'], 2)} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}")
        print(f"      trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f}  ex-bottom {g4['mean_ex_bottom_bp']:+.1f}  trimmed {g4['mean_trimmed_bp']:+.1f}")
        print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
              + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
              + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}")
        print(f"      TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} (DV pct "
              f"{tt['dv_percentile_at_entry'] if tt['dv_percentile_at_entry'] is None else round(tt['dv_percentile_at_entry'], 1)}), held {tt['hold']} bars, "
              f"{tt['pnl_bp']:+.0f} bp = {('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
        sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
        r = lambda x: "-" if x is None else round(x, 1)
        print(f"      splits: dead {sd_['dead_n']} {r(sd_['dead_mean_bp'])} / alive {sd_['alive_n']} {r(sd_['alive_mean_bp'])}; price <= ${sp_['median_price']:.2f} "
              f"{sp_['low_n']} {r(sp_['low_mean_bp'])} / above {sp_['high_n']} {r(sp_['high_mean_bp'])}")
    print("\n  INTERACTION with the rsi ranking (short, cap exit, short base rate): bucket | n | E[member,bucket] | E[bucket] | interaction")
    for member in survivors:
        d_ = REPORT[member]["short/cap"]
        tv = d_["top_vs_rest"]
        print(f"  {member}: " + " ".join(f"b{b}[{v['n']}] {v['E_sb']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(d_["interaction"].items()))
              + f" | undefined {d_['events_undefined_rsi_bucket']} | " + (f"top - min(rest) {tv:+.1f}" if tv is not None else "no top-bucket events"))
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")
    print("\n  NET per trade, SHORT: mean - 2c (PB / PUB) - borrow (gc_htb: GC %.0f, HTB %.0f bp/yr)" % (BR.GC_BPS, BR.HTB_BPS))
    print("  %-18s %-12s %8s %7s %7s %7s %6s | %8s %8s | %8s %8s | %8s" % ("member", "exit", "mean", "2c PB", "2c PUB", "borrow", "HTB%",
                                                                         "net PB", "net PUB", "PB+brw", "PUB+brw", "be hs/s"))
    for member in survivors:
        for exit_ in ("cap", "invalidation"):
            d_ = REPORT[member][f"short/{exit_}"]
            print("  %-18s %-12s %+8.1f %7.1f %7.1f %7.1f %6.1f | %+8.1f %+8.1f | %+8.1f %+8.1f | %8.1f" % (
                member, exit_, d_["mean_bp"], d_["two_c"]["PB"], d_["two_c"]["PUB"], d_["borrow"]["mean_bp"], 100 * d_["borrow"]["htb_share"],
                d_["net_per_trade"]["PB"], d_["net_per_trade"]["PUB"], d_["net_per_trade_borrow"]["PB"], d_["net_per_trade_borrow"]["PUB"],
                d_["breakeven_half_spread_bp_side"]))
    print("  be hs/s: the held median half-spread (bp per side) at which net after commission and borrow is zero")

    # ---- predictions ----
    def above_all(member):
        R_ = REPORT[member]
        c = R_.get("controls")
        return bool(c and c["A"]["above"] and c["B"]["above"] and R_["short/cap"]["control_C"]["above"])

    kernel_surv = [m for m in survivors if above_all(m)]
    gate_kernel = [m for m in kernel_surv if not fallback]
    gate_kernel_s2 = [m for m in gate_kernel if m.split("/")[1] == "S2"]
    missing = [m for m in survivors if "controls" not in REPORT[m]]
    print("\n  A' (within elig), B (defined-percentile pool) and C under the kernel, cap exit, bp per trade:")
    for m in survivors:
        c = REPORT[m].get("controls")
        obs = REPORT[m]["short/cap"]["mean_bp"]
        cc = REPORT[m]["short/cap"]["control_C"]
        print(f"    {m:18s} observed {obs:+7.1f} | " + (f"A' p50 {c['A']['p50']:+7.1f} p95 {c['A']['p95']:+7.1f} above {'yes' if c['A']['above'] else 'NO '} | "
                                                       f"B p50 {c['B']['p50']:+7.1f} p95 {c['B']['p95']:+7.1f} above {'yes' if c['B']['above'] else 'NO '} | "
                                                       if c else "A'/B not run | ")
              + f"C p95 {cc['p95']:+6.1f} above {'yes' if cc['above'] else 'NO '}")
    print(f"  above A', B and C: {kernel_surv}; of them S2 gate passers: {gate_kernel_s2}")
    q = grid_predictions(screen["members"], screen["m_eff"]["li_ji"], screen["m_eff"]["cheverud_nyholt"])
    q["Q1"] = bool(len(gate_kernel_s2) > 0)
    q["Q1_any_shape"] = bool(len(gate_kernel) > 0)
    q["Q4"] = bool(any(REPORT[m][f"short/{e}"]["net_per_trade_borrow"]["PUB"] > 0 for m in survivors for e in ("cap", "invalidation")))
    q["Q5"] = bool(survivors) and all(REPORT[m]["mirror/cap"]["mean_bp"] < 0 for m in survivors)
    q["Q7"] = bool(survivors) and all((REPORT[m]["short/cap"]["top_vs_rest"] if REPORT[m]["short/cap"]["top_vs_rest"] is not None else 1e9) < 0
                                      for m in survivors)
    if TURN in REPORT and "controls" in REPORT[TURN]:
        q["Q8"] = bool(not REPORT[TURN]["controls"]["A"]["above"])
        q["Q8_source"] = "kernel"
    else:
        q["Q8"] = q["Q8_grid"]
        q["Q8_source"] = "grid"
    q["check_d349_counts"] = bool(all(screen["d349_count_check"].values()))
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) an S2 member is above p95 of A', B and C under the kernel: {v(q['Q1'])} -- "
          f"{'fallback members only (nothing passed the gate)' if fallback else 'gate survivors ' + str(survivors)}; above all three: {kernel_surv}"
          + (f"; kernel controls A'/B missing for {missing}" if missing else "") + f"; any shape above all three (not the prediction): {v(q['Q1_any_shape'])}")
    print_grid_predictions(q, screen["members"], screen["m_eff"]["li_ji"], screen["m_eff"]["cheverud_nyholt"])
    print(f"  Q4 (against) a survivor nets > 0 per trade after the PUB round trip and the borrow, either exit: {v(q['Q4'])} -- "
          + ", ".join(f"{m} {REPORT[m]['short/cap']['net_per_trade_borrow']['PUB']:+.1f}/{REPORT[m]['short/invalidation']['net_per_trade_borrow']['PUB']:+.1f}"
                      for m in survivors))
    print(f"  Q5 every survivor's mirror (the long of the same event) < 0: {v(q['Q5'])} -- "
          + ", ".join(f"{m} {REPORT[m]['mirror/cap']['mean_bp']:+.1f}" for m in survivors))
    print(f"  Q7 every survivor's interaction most negative in the top rsi bucket (98,100]: {v(q['Q7'])} -- "
          + ", ".join(f"{m} top - min(rest) {REPORT[m]['short/cap']['top_vs_rest']:+.1f}" if REPORT[m]["short/cap"]["top_vs_rest"] is not None
                      else f"{m} no top-bucket events" for m in survivors))
    print(f"  Q8 the rsi turn inside A' p95 ({q['Q8_source']}): {v(q['Q8'])}")
    print(f"  check: S10 on D349's four scores and the turn reproduce D349's event counts: {v(q['check_d349_counts'])}")
    out = dict(note="D352: a short-timing screen. Stage 1 (the grid, data/d352_screen.json) scored 139 SHORT members on -F against their own "
                    "names at random ELIGIBLE times (A') and the defined-percentile same-bucket control (B); stage 2 ran D345's kernel fed "
                    "(zeros, hi) with the raw percentile on the survivors. Every event taken; nothing is a book; nothing promoted.",
               survivors=survivors, fallback=fallback, kernel_survivors=kernel_surv, gate_and_kernel_survivors=gate_kernel,
               gate_and_kernel_survivors_S2=gate_kernel_s2, cap=CAP, thresholds=THR, bucket_edges=BUCKET_EDGES,
               short_base_rate_all_bp=E_all, short_base_rate_by_bucket_bp=E_b, down_years=P["down_years"], floored_market_by_year=P["yr_ret"],
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), check=CHECK, report=REPORT,
               screen=dict(m_eff=screen["m_eff"], bh=screen["bh"], grid_max=screen["grid_max"], gate=screen["gate"], n_pA_le_05=screen["n_pA_le_05"],
                           d349_ranks=screen["d349_ranks"], d349_count_check=screen["d349_count_check"]),
               predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--scores", help="dev only: comma-separated subset of scores for --screen; writes to temp/, not data/")
    ap.add_argument("--workers", type=int, default=6, help="--screen: processes for the per-score controls (1 = in-process)")
    ap.add_argument("--kernel", metavar="MEMBER", help="e.g. on_share/S2 or rsi/turn")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print("D352  a short-timing screen at the extreme the slot book trades -- 139 declared short events against their own names at random eligible times")
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
            stage_screen(P, scores=a.scores.split(","), out=REPO / "temp" / "d352_screen_dev.json", workers=a.workers)
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
