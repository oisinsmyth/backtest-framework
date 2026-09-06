"""D362 -- the sink filter on the gated gap-up fade: five losing conditions found in the D361 trade export, applied to the SIGNAL and
re-simulated (A2: events hitting S1 or S2 removed; A5: any hit removed; W: every position sized 0.5^hits), the row-drop version beside
each, and the filter's own nulls (DROP: the same number of gated events removed at random; FROT: each name's hit flags rotated in time
across its own gated events) beside the gate rotation, A' within the gate and C. Within-sample with nulls, not out-of-sample.

    uv run python scripts/run_d362_sink_filter.py --selftest
    uv run python scripts/run_d362_sink_filter.py --arm A2 --draws 100 --draws-rot 200 --part 0     the nulls for one arm (A2 | A5 | W)
    uv run python scripts/run_d362_sink_filter.py --report
    --out-dir DIR    (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)
    --draws N        the A'-within-gate draws (pre-reg 100); --draws-rot R the DROP, FROT and gate-rotation draws (pre-reg 200; default N)

Pre-registration: docs/decisions/D362-the-sink-filter-on-the-gated-gap-up-fade.md (38d7a74)

THE BASE is D361's G2 x T2 cell exactly (run_d361.arms_of, run_short at cap 10; [ID] to 1e-9 against data/d361_regime_gated_short.json).

THE FEATURES at (bar_entry, row) are the D361 export's definitions, imported and not re-derived: pcto_<score> = d361_export_trades.own_lagged
(the score floored, deal-filtered, LAGGED one bar, under the score's OWN warm-up) through V47.percentile_grid -- the export's pcto_ builder
line for line; mkt_vol_20 = sd (ddof = 1) of m_f over bars t-20 .. t-1 in bp, NaN where t - 20 < m_start -- the export computes it inline
in build() (not as a function), so the expression is REPEATED here verbatim and [FEAT] holds it to the export's CSV column exactly.
[FEAT] checks EVERY gated event against data/d361_trades_gap_up_fade.csv (the mining fixture's export), not only the 300 sampled.

THE SINKS (thresholds fixed in the pre-registration, section 1; a NaN never hits):
    S1 pcto_mass_imbalance >= 86.84   S2 mkt_vol_20 <= 99.03   S3 pcto_beta_63 >= 87.22   S4 pcto_mass_here <= 18.77   S5 pcto_gk_minus_cc <= 6.38
hit_k[t, i] is computed on EVERY (t, i) of the panel (the features exist everywhere), so a flag is defined for every T2 event, gated or
not, and for every bar a rotated event can land on. hits = sum_k hit_k (0..5).

THE ARMS (arm_index A2 0, A5 1, W 2 -- the pre-registration's seed slot, fixed here):
    A2  signal = gated & ~(hit_1 | hit_2)             re-simulated through run_short at cap 10 (the PRIMARY arm)
    A5  signal = gated & ~(hits > 0)
    W   signal = gated; the position opened on event (t, i) carries weight w = 0.5^hits[t, i]; the ledger is the BASE ledger trade for
        trade (the kernel is equal-weight and untouched) and the weights are read off the (t, i) of each trade. The deployed base is the
        weighted hedged return per bar sum_i w_i sgn (v_i - m) / sum_i w_i over the open positions (rebuild_w, the entry bar on ocT - m_f_oc,
        later bars on r1T - m_f); the per-trade statistic is the return per unit of capital sum w pnl / sum w with capital used = sum w / n;
        its t = mean_w / se_w, se_w = sqrt(sum w^2 (x - mean_w)^2) / sum w.
    Row-drop beside each: the same flags applied to the BASE ledger's rows without re-simulation (for W the row-drop IS the arm: the
    signal is unchanged, so the difference is 0 by construction and printed as such).

W's COST: G22.costed's arithmetic on the weighted series with turnover = (sum of w over entries) / mean over deployed bars of (sum of w over
open positions) / bars -- entries weighted by w, held = sum w over open positions. G22.costed itself truncates entries with int(), so the
weighted version is written here (costed_w) and asserted equal to G22.costed key for key with every weight 1 ([W]).

THE NULLS on the primary arm (seeds [SEED, 362, arm_index, null_index, part]; null_index DROP 1, FROT 2, gate rotation 3, A' 4, C 5):
    DROP  (200) a uniformly random subset of the gated events of the SAME SIZE as the observed removal (|hit_1 | hit_2| among the gated
          events) removed from the signal, re-simulated. [DROP]: the exact count every draw; never the observed set.
    FROT  (200) per name, its 5-column hit matrix over its gated events (in time order) circularly rotated by one offset drawn uniformly
          in [1, k-1]; a name with ONE gated event keeps its flags (there is nothing to rotate; counted and reported). Where the rotated
          arm flag (hit_1 | hit_2 for A2; hits > 0 for A5) equals the observed vector on a name whose observed vector is not constant (a
          periodic vector), the offset is REDRAWN (offset 1 always changes a non-constant vector, so this terminates; redraws counted).
          [FROT]: every name's per-sink hit counts kept; the arm flag vector never the observed one on a non-constant name.
    ROT   (200) D361's gate rotation (offsets without replacement over the defined bars, [ROT] with the circular run multiset), re-ANDed
          with the FILTERED ungated trigger: the flags are those computed on the OBSERVED bars (the name's own state and the market's
          20-bar vol at the event bar) and only the gate is rotated. For W the unfiltered trigger, re-weighted by the flags at the bar.
    A'    (100) D361's A' within the gate (EB.rotate_signals on elig & gate) on the filtered signal; for W on the unfiltered signal with
          the weight read at the landing bar.
    C     (1,000) random directions on the arm's ledger (for W: sum w s x / sum w).
    For A5 DROP and FROT are run too (cheap); for W they are skipped (its filter is a weight) and the file says so.

Everything shared is imported: run_d361 (gate_pack, triggers, arms_of, run_short, rotate_gate, assert_ROT, rot_offsets, aprime_gate_draw,
the blocks), d361_export_trades (own_lagged), and through them run_d360 / run_d359 / run_d358 / run_d353 / run_d350 / run_d349 / d348_prep.

HOLDOUT GUARD: a sys.addaudithook on every file `open` in the process, installed before the first module of the chain executes: a path
containing 'holdout' (anywhere; stricter than the task's data/fixtures) is REFUSED before the file is touched, and every open under
data/fixtures is counted by basename. [HOLDOUT-GUARD] prints them and probes the hook with a non-existent holdout path.

ASSERTIONS [K][F0][R][HOLDOUT-GUARD][ID][FEAT][HIT][RD][W][DROP][FROT][ROT][A'][C][S][HX][6] -- pre-reg section 6.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# ------------------------------------------------------------------ the holdout guard: before ANY module of the chain executes
_OPENED = dict(n=0, fixtures=Counter(), refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    s = os.fspath(p)
    low = s.replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[HOLDOUT-GUARD] refused to open {s}")
    if "data/fixtures/" in low:
        _OPENED["fixtures"][low.rsplit("/", 1)[-1]] += 1


sys.addaudithook(_audit)

sys.path.insert(0, str(REPO / "scripts"))
import memo_load                                   # noqa: E402  -- installed HERE so that this file's own first _load (run_d361) is memoised and the
memo_load.install()                                # export's _load("d361r") binds the same object (d348_prep installs it too; install() is idempotent)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V61 = _load("d361r", "run_d361_regime_gated_short.py")       # loads d348_prep FIRST (memo_load installed there), then run_d360, run_d359
EXP = _load("d361x", "d361_export_trades.py")               # the feature definitions; its own _load("d361r") is memoised to the same object
assert EXP.V61 is V61, "run_d361 loaded twice (memo_load not installed?)"
PREP, V60, V59, V58, V53, V49, V47, V50 = V61.PREP, V61.V60, V61.V59, V61.V58, V61.V53, V61.V49, V61.V47, V61.V50
EB, G22, BR = V61.EB, V61.G22, V61.BR
SEED, X_TARGET, CONVS = V61.SEED, V61.X_TARGET, V61.CONVS
STUDY = 362
GATE, TRIG = "G2", "T2"
CAP = 10
PER_SHARE, BORROW_SCHEME = V61.PER_SHARE, V61.BORROW_SCHEME
SINKS = (("S1", "pcto_mass_imbalance", ">=", 86.84), ("S2", "mkt_vol_20", "<=", 99.03), ("S3", "pcto_beta_63", ">=", 87.22),
         ("S4", "pcto_mass_here", "<=", 18.77), ("S5", "pcto_gk_minus_cc", "<=", 6.38))
FEATS = tuple(s[1] for s in SINKS)
ARMS = ("A2", "A5", "W")
ARM_INDEX = dict(A2=0, A5=1, W=2)
NULL = dict(DROP=1, FROT=2, ROT=3, A=4, C=5)
PRIMARY = "A2"
DATA = REPO / "data"
D361_REPORT = DATA / "d361_regime_gated_short.json"
EXPORT_CSV, EXPORT_GZ = DATA / "d361_trades_gap_up_fade.csv", DATA / "d361_trades_gap_up_fade.csv.gz"
SELFTEST_TMP = REPO / "temp" / "d362_selftest"
PREREG = dict(base_trades=3_977, base_mean_bp=42.3296, rd_A5_era2_trades=1_221, rd_A5_era2_mean_bp=91.5, unf_trimmed_bp=35.0, unf_era2_bp=55.0,
              unf_exposure=0.28, q10_bp=10.0)
run_short, simulate = V61.run_short, V61.simulate
deployed_block, trade_block = V61.deployed_block, V61.trade_block
assert_S_short, perturb_test = V61.assert_S_short, V61.perturb_test
deployed_subsets, assert_HX, control_C, null_stats, observed_stats = V61.deployed_subsets, V61.assert_HX, V61.control_C, V61.null_stats, V61.observed_stats
assert_C = V61.assert_C
clean = V61.clean
KEYS = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trades", "exposure")


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, ctrl=str(d / "d362_ctrl_{arm}_p{part}.json"), report=d / "d362_sink_filter.json")


def fq(x, nd=2):
    return "-" if x is None else f"{x:+.{nd}f}"


def guard_line():
    fx = _OPENED["fixtures"]
    return (f"{_OPENED['n']:,} file opens audited in this process, {sum(fx.values())} under data/fixtures ({', '.join(f'{k} x{v}' for k, v in sorted(fx.items()))}); "
            f"none containing 'holdout' opened ({_OPENED['refused']} refused: the probe)")


def assert_HOLDOUT_GUARD():
    """The hook is installed and fires: a NON-EXISTENT path with 'holdout' in its name is refused before the filesystem is touched;
    no opened fixture basename contains 'holdout'."""
    probe = DATA / "fixtures" / "holdout_probe_that_does_not_exist.txt"
    assert not probe.exists()
    raised = False
    try:
        open(probe, "r")
    except RuntimeError as e:
        raised = "[HOLDOUT-GUARD]" in str(e)
    except OSError:
        raised = False
    assert raised, "[HOLDOUT-GUARD] the audit hook did not refuse a holdout path"
    assert not any("holdout" in k for k in _OPENED["fixtures"]), "[HOLDOUT-GUARD] a holdout fixture was opened"
    return guard_line()


# ------------------------------------------------------------------ the base
_BASE = {}


def base(P):
    """gated / ungated T2 event grids, the kernel score, elig, the G2 gate pack, the gated events in (t, i) row-major order. Memoised."""
    if _BASE:
        return _BASE
    gated, _off, ung, sc = V61.arms_of(P, GATE, TRIG)
    elig = V61.triggers(P)[TRIG][2]
    gp = V61.gate_pack(P, GATE)
    ev_t, ev_i = np.nonzero(gated)
    _BASE.update(gated=gated, ung=ung, sc=sc, elig=elig, gp=gp, ev_t=ev_t, ev_i=ev_i)
    return _BASE


def assert_ID(P, res, tol=1e-9, tag="[ID]"):
    """The unfiltered gated ledger == D361's stored G2:T2 gated cap-10 per_trade (trades, mean, median, held half-spread PUB) and its
    observed deployed gross / net PUB / net PB, each to tol; the trade count is the pre-registration's 3,977."""
    d = json.loads(D361_REPORT.read_text())["results"][V61.cell_name(GATE, TRIG)]
    p, o = d["gated"]["cap10"]["per_trade"], d["observed"]
    pnl = V47.pnl_bp(res)
    m = float(pnl.mean())
    assert all(t[4] == 1 for t in res["trades"]), f"{tag} a long in the short ledger"
    assert len(res["trades"]) == p["trades"] == PREREG["base_trades"], f"{tag} {len(res['trades']):,} trades != D361's stored {p['trades']:,}"
    assert abs(m - p["mean_bp"]) < tol, f"{tag} mean {m:.10f} != D361's stored {p['mean_bp']:.10f}"
    assert abs(float(np.median(pnl)) - p["median_bp"]) < tol, f"{tag} median"
    hs = V47.two_c(res["trades"], P["HALF"]["PUB"], P["CLOSE"])[1]
    assert abs(hs - p["held_half"]["PUB"]) < tol, f"{tag} held half-spread PUB"
    ob = observed_stats(res, P)
    for k in ("gross_bp", "net_bp_PUB", "net_bp_PB", "trades", "entries", "exposure"):
        assert abs(ob[k] - o[k]) < tol, f"{tag} observed {k} {ob[k]} != D361's {o[k]}"
    assert abs(m - PREREG["base_mean_bp"]) < 5e-5, f"{tag} the pre-registration's rounded +{PREREG['base_mean_bp']} differs from the stored value"
    return dict(trades=len(res["trades"]), mean_bp=m, stored_mean_bp=p["mean_bp"], median_bp=float(np.median(pnl)), held_half_PUB=hs, observed=ob,
                stored_observed=o)


# ------------------------------------------------------------------ the features (the export's definitions)
_FEAT = {}


def mkt_vol_20_series(P):
    """The export's mkt_vol_20, verbatim (d361_export_trades.build: for each entry bar e with e - 20 >= m_start, float(np.std(m_f[e-20:e],
    ddof=1)) * 1e4; NaN otherwise), as a (T,) series."""
    m_f = np.asarray(P["m_f"], float)
    T, m0 = P["T"], P["m_start"]
    mv = np.full(T, np.nan)
    for e in range(T):
        if e - 20 >= m0:
            w = m_f[e - 20:e]
            mv[e] = float(np.std(w, ddof=1)) * 1e4
    return mv


def features(P):
    """{feature: (T, n) grid | (T,) series}: pcto_<score> = V47.percentile_grid(EXP.own_lagged(P, raw, score)) -- the export's builder;
    mkt_vol_20 the series above. Memoised (~52 MB per grid)."""
    if _FEAT:
        return _FEAT
    for f in FEATS:
        if f == "mkt_vol_20":
            _FEAT[f] = mkt_vol_20_series(P)
            continue
        s = f[len("pcto_"):]
        raw = np.asarray(P["score"](s), float)
        own = EXP.own_lagged(P, raw, s)
        _FEAT[f] = V47.percentile_grid(own)
        del raw, own
    return _FEAT


def feat_at(F, f, t, i):
    v = F[f]
    return float(v[t]) if v.ndim == 1 else float(v[t, i])


def hit_grids(F, T, n):
    """H[k] (T, n) bool: the k-th sink's condition on its feature, NaN never hits; hits = sum_k H[k] (int8)."""
    H = np.zeros((len(SINKS), T, n), bool)
    with np.errstate(invalid="ignore"):
        for k, (_nm, f, op, th) in enumerate(SINKS):
            v = F[f]
            if v.ndim == 1:
                v = v[:, None]
            H[k] = (v >= th) if op == ">=" else (v <= th)
    return H, H.sum(axis=0).astype(np.int8)


def hit_direct(F, t, i):
    """[HIT]'s second implementation: the five flags at (t, i) in plain Python with an explicit NaN test."""
    out = []
    for _nm, f, op, th in SINKS:
        v = feat_at(F, f, t, i)
        out.append(False if math.isnan(v) else (v >= th if op == ">=" else v <= th))
    return out


def arm_removed(arm, H, hits):
    """The (T, n) mask of what the arm REMOVES from the signal (W removes nothing)."""
    if arm == "A2":
        return H[0] | H[1]
    if arm == "A5":
        return hits > 0
    return np.zeros_like(hits, dtype=bool)


def arm_flag(arm, Hev):
    """The arm's flag per event from an (N, 5) hit matrix."""
    return (Hev[:, 0] | Hev[:, 1]) if arm == "A2" else Hev.any(axis=1)


def arm_signal(arm, sig, H, hits):
    return np.ascontiguousarray(sig & ~arm_removed(arm, H, hits))


def weight_grid(hits):
    return 0.5 ** hits.astype(float)


# ------------------------------------------------------------------ the export CSV: [FEAT] [HIT] [RD]
_CSV = {}
EXPORT_COLS = FEATS + ("pnl_cap10_bp_G2", "era", "row", "bar_entry", "excluded_reason", "G2_on", "taken_G2")


def read_export(cols=EXPORT_COLS):
    """The needed columns of data/d361_trades_gap_up_fade.csv (or the .csv.gz) as float arrays ('' -> NaN) plus the (row, bar_entry) index. Read once."""
    if _CSV:
        return _CSV["C"]
    src = EXPORT_CSV if EXPORT_CSV.exists() else EXPORT_GZ
    f = open(src, encoding="utf-8", newline="") if src.suffix == ".csv" else gzip.open(src, "rt", encoding="utf-8", newline="")
    with f:
        r = csv.reader(f)
        head = next(r)
        need = list(EXPORT_COLS)
        ci = [head.index(c) for c in need]
        raw = [[x[j] for j in ci] for x in r]
    out = {}
    for j, c in enumerate(need):
        if c == "excluded_reason":
            out[c] = np.array([x[j] for x in raw], dtype=object)
        else:
            out[c] = np.array([float(x[j]) if x[j] != "" else np.nan for x in raw])
    out["_index"] = {(int(r_), int(e)): k for k, (r_, e) in enumerate(zip(out["row"], out["bar_entry"]))}
    out["_file"] = src.name
    _CSV["C"] = out
    return out


def assert_FEAT(P, F, B, rng, k=300, F_override=None, tag="[FEAT]"):
    """The five features at (bar_entry, row) equal the export's CSV columns EXACTLY (NaN patterns equal) on k sampled gated events AND on
    every gated event; the export's G2_on & not-excluded rows are exactly the gated events."""
    C = read_export()
    F = F if F_override is None else F_override
    ev_t, ev_i = B["ev_t"], B["ev_i"]
    idx = C["_index"]
    pos = np.array([idx[(int(i), int(t))] for t, i in zip(ev_t, ev_i)])
    on = (C["G2_on"] == 1) & (C["excluded_reason"] == "")
    assert int(on.sum()) == ev_t.size and on[pos].all(), f"{tag} the export's gated rows ({int(on.sum())}) are not the {ev_t.size} gated events"
    samp = rng.choice(ev_t.size, size=min(k, ev_t.size), replace=False)
    n_nan = Counter()
    for j in range(ev_t.size):
        t, i, p = int(ev_t[j]), int(ev_i[j]), int(pos[j])
        for f in FEATS:
            a, b = feat_at(F, f, t, i), float(C[f][p])
            same = (math.isnan(a) and math.isnan(b)) or a == b
            assert same, f"{tag} {f} at ({P['dates'][t]}, {P['symbols'][i]}): runner {a!r} != export {b!r}"
            if math.isnan(a):
                n_nan[f] += 1
    return dict(events=int(ev_t.size), sampled=int(samp.size), nan_counts=dict(n_nan), file=C["_file"])


def assert_HIT(P, F, H, hits, B, res, rng, k=300, tag="[HIT]"):
    """The grid flags equal hit_direct (plain Python, explicit NaN test) on k sampled gated events and on every event; hits == the sum;
    the per-sink hit counts on the BASE ledger equal those computed from the export's own columns on its taken_G2 rows, flag for flag."""
    ev_t, ev_i = B["ev_t"], B["ev_i"]
    for j in range(ev_t.size):
        t, i = int(ev_t[j]), int(ev_i[j])
        d = hit_direct(F, t, i)
        g = [bool(H[q, t, i]) for q in range(len(SINKS))]
        assert d == g, f"{tag} flags differ at ({P['dates'][t]}, {P['symbols'][i]}): grid {g} direct {d}"
        assert int(hits[t, i]) == sum(d), f"{tag} hits != the sum"
    C = read_export()
    idx = C["_index"]
    tr = res["trades"]
    pos = np.array([idx[(int(r), int(e0))] for r, e0, _a, _p, _s in tr])
    assert (C["taken_G2"][pos] == 1).all() and int((C["taken_G2"] == 1).sum()) == len(tr), f"{tag} the export's taken_G2 rows are not the ledger"
    counts, csv_counts = [], []
    with np.errstate(invalid="ignore"):
        for q, (_nm, f, op, th) in enumerate(SINKS):
            mine = np.array([bool(H[q, e0, r]) for r, e0, _a, _p, _s in tr])
            v = C[f][pos]
            theirs = (v >= th) if op == ">=" else (v <= th)
            assert np.array_equal(mine, theirs), f"{tag} {f}: the ledger's flags differ from the export's columns on {int((mine != theirs).sum())} trades"
            counts.append(int(mine.sum()))
            csv_counts.append(int(theirs.sum()))
    return dict(events=int(ev_t.size), ledger_hit_counts=counts, export_hit_counts=csv_counts)


def rowdrop_trades(arm, trades, H, hits):
    rm = arm_removed(arm, H, hits)
    return [t for t in trades if not rm[t[1], t[0]]]


def assert_RD(P, res, H, hits, tol=1e-9, tag="[RD]"):
    """The row-drop A5 restricted to era 2 (e0 >= T // 2) reproduces the export analysis's cross-era number -- 1,221 trades, +91.5 (the
    pre-reg, to 0.05) -- and, to tol, the same statistic recomputed from the export's own columns (pnl_cap10_bp_G2 and the five features
    under the fixed thresholds on taken_G2 rows); the row-drop A2 / A5 on the whole sample likewise."""
    C = read_export()
    T = P["T"]
    tk = C["taken_G2"] == 1
    pnl_c = C["pnl_cap10_bp_G2"]
    with np.errstate(invalid="ignore"):
        Hc = np.array([(C[f] >= th) if op == ">=" else (C[f] <= th) for _nm, f, op, th in SINKS])
    a2c, a5c = tk & ~(Hc[0] | Hc[1]), tk & ~Hc.any(axis=0)
    e2c = C["era"] == 2
    out = {}
    for arm, cm in (("A2", a2c), ("A5", a5c)):
        sub = rowdrop_trades(arm, res["trades"], H, hits)
        pnl = pnl_bp_of(sub)
        mine = (len(sub), float(pnl.mean()))
        theirs = (int(cm.sum()), float(pnl_c[cm].mean()))
        assert mine[0] == theirs[0] and abs(mine[1] - theirs[1]) < tol, f"{tag} row-drop {arm}: {mine} != the export's {theirs}"
        e2 = np.array([t[1] >= T // 2 for t in sub])
        mine2 = (int(e2.sum()), float(pnl[e2].mean()))
        theirs2 = (int((cm & e2c).sum()), float(pnl_c[cm & e2c].mean()))
        assert mine2[0] == theirs2[0] and abs(mine2[1] - theirs2[1]) < tol, f"{tag} row-drop {arm} era 2: {mine2} != the export's {theirs2}"
        out[arm] = dict(trades=mine[0], mean_bp=mine[1], era2_trades=mine2[0], era2_mean_bp=mine2[1], export_trades=theirs[0], export_mean_bp=theirs[1],
                        export_era2_trades=theirs2[0], export_era2_mean_bp=theirs2[1])
    a5 = out["A5"]
    assert a5["era2_trades"] == PREREG["rd_A5_era2_trades"] and abs(a5["era2_mean_bp"] - PREREG["rd_A5_era2_mean_bp"]) < 0.05, \
        f"{tag} row-drop A5 era 2 {a5['era2_trades']} / {a5['era2_mean_bp']:.4f} != the pre-registration's {PREREG['rd_A5_era2_trades']} / +{PREREG['rd_A5_era2_mean_bp']}"
    return out


# ------------------------------------------------------------------ W: the weighted series, statistics and cost
def pnl_bp_of(trades):
    return np.array([t[3] for t in trades]) * 1e4


def weights_of(trades, wgrid):
    return np.array([float(wgrid[e0, row]) for row, e0, _a, _p, _s in trades])


def rebuild_w(trades, P, wgrid):
    """(row, e0, age, pnl, side) -> per bar: sum_i w_i sgn (v_i - m) over the open positions (the entry bar on ocT - m_f_oc, later bars on
    r1T - m_f), sum_i w_i, and the weighted entries. With every weight 1 this is V58.rebuild(hedged=True)."""
    r1T, ocT, m_f, m_oc = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"]
    T = P["T"]
    reb, cw, ew = np.zeros(T), np.zeros(T), np.zeros(T)
    for row, e0, age, _p, side in trades:
        sgn = 1.0 if side == 0 else -1.0
        w = float(wgrid[e0, row])
        v = np.array(r1T[e0:e0 + age, row], dtype=float)
        mm = np.array(m_f[e0:e0 + age], dtype=float)
        v[0], mm[0] = ocT[e0, row], m_oc[e0]
        reb[e0:e0 + age] += w * (sgn * (v - mm))
        cw[e0:e0 + age] += w
        ew[e0] += w
    return reb, cw, ew


def weighted_loop(trades, P, wgrid):
    """[HX]'s second implementation for W: a bar loop over a set of open positions (the kernel's shape), never rebuild_w's slice adds."""
    r1T, ocT, m_f, m_oc = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"]
    T = P["T"]
    starts = {}
    for row, e0, age, _p, side in trades:
        starts.setdefault(e0, []).append((row, e0, e0 + age, 1.0 if side == 0 else -1.0, float(wgrid[e0, row])))
    open_, sx, cw = [], np.zeros(T), np.zeros(T)
    for t in range(T):
        open_ = [o for o in open_ if o[2] > t] + starts.get(t, [])
        s = c = 0.0
        for row, e0, _end, sgn, w in open_:
            v, m_ = (float(ocT[t, row]), float(m_oc[t])) if t == e0 else (float(r1T[t, row]), float(m_f[t]))
            s += w * sgn * (v - m_)
            c += w
        sx[t], cw[t] = s, c
    return sx, cw


def series_w(trades, P, wgrid):
    """dict(book, mask, held_w, ent_w, signed): the weighted deployed series and its bases."""
    reb, cw, ew = rebuild_w(trades, P, wgrid)
    mask = cw > 0
    with np.errstate(invalid="ignore"):
        book = np.where(mask, reb / np.where(mask, cw, 1.0), np.nan)
    return dict(book=book, mask=mask, held_w=cw, ent_w=ew, signed=reb)


def costed_w(trades, S, P, cv, crossings=4.0):
    """G22.costed's arithmetic on the weighted series: turnover = sum ent_w / mean held_w / bars; hs / px the held-median half-spread
    and price of the names held (G22's X.held_median on the ledger); the breakeven half-spread as run_d358.costed."""
    HALF, CLOSE, DV, _ = P["G4"][cv]
    ok = S["mask"]
    b = S["book"][ok]
    bars = b.size
    e = float(S["ent_w"][ok].sum())
    held = float(S["held_w"][ok].mean())
    r_ = dict(trades=trades)
    hs, px, dv = G22.X.held_median(r_, HALF), G22.X.held_median(r_, CLOSE), G22.X.held_median(r_, DV)
    rt = 4.0 * hs
    rtc = crossings * G22.PER_SHARE / px * 1e4 if px > 0 else np.nan
    turn = e / held / bars
    g = float(b.mean()) * 1e4
    v = float(b.std(ddof=1)) * 1e4
    net = g - (rt + rtc) * turn
    eq = np.cumsum(b)
    d = dict(gross_bp=g, vol_bp=v, net_bp=net, sharpe_gross=g / v * np.sqrt(G22.ANN) if v > 0 else 0.0, sharpe_net=net / v * np.sqrt(G22.ANN) if v > 0 else 0.0,
             round_trip=rt, commission_rt=rtc, cost_bp=(rt + rtc) * turn, turnover=turn, held_per_bar=held, fill=held / (2.0 * G22.DEPTH),
             held_half_spread=hs, held_price=px, held_dv=dv, maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4, entries=e, bars=bars,
             trades=len(trades))
    d["breakeven_half_spread_bp_side"] = (g / turn - rtc) / 4.0 if turn > 0 else None
    return d


def deployed_block_w(res, P, wgrid):
    """W's deployed block: the weighted hedged series, both conventions, 4 and 2 crossings; exposure on the kernel's defined bars."""
    S = series_w(res["trades"], P, wgrid)
    defined, held = res["defined"], res["held"]
    nd, nb = int(defined.sum()), int(S["mask"].sum())
    assert np.array_equal(S["mask"], res["mask_dep"]) or int(res["held"][-1]) > 0, "[W] the weighted mask differs from the kernel's deployed mask"
    out = dict(trades=len(res["trades"]), entries=int(res["ent"].sum()), entries_w=float(S["ent_w"].sum()), open_at_end=int(held[-1]), bars_defined=nd,
               bars_deployed=nb, exposure=nb / nd, mean_positions_deployed=float(held[S["mask"]].mean()), mean_capital_deployed=float(S["held_w"][S["mask"]].mean()),
               max_positions=int(held.max()), entries_per_year=float(res["ent"].sum()) / (nd / G22.ANN),
               turnover_definition="sum of w over entries / mean over deployed bars of (sum of w over open positions) / bars")
    for cv in CONVS:
        h = costed_w(res["trades"], S, P, cv)
        out[cv] = dict(hedged=h, hedged_2x=V59.two_crossing(h))
    out["_series"] = S
    return out


def trade_block_w(P, trades, w):
    """W's per-trade block: the return per unit of capital sum w pnl / sum w, its t (se = sqrt(sum w^2 (x - m)^2) / sum w), capital used
    sum w / n, the weighted hold, 2c on the same held names, the weighted borrow, net and breakeven, the weighted era / year splits."""
    pnl = pnl_bp_of(trades)
    W = float(w.sum())
    m = float((w * pnl).sum() / W)
    se = float(np.sqrt(((w ** 2) * (pnl - m) ** 2).sum()) / W)
    ages = np.array([t[2] for t in trades], float)
    T = P["T"]
    years = np.asarray(P["years"])
    yrs = np.array([years[t[1]] for t in trades])
    era1 = np.array([t[1] < T // 2 for t in trades])
    down = np.isin(yrs, list(P["down_years"]))
    c2 = {cv: V47.two_c(trades, P["HALF"][cv], P["CLOSE"]) for cv in CONVS}
    px = c2["PUB"][2]
    comm = 2.0 * PER_SHARE / px * 1e4
    pt, htb, _rate = V49.borrow_of(P, trades)
    bm = float((w * pt).sum() / W)
    wm = lambda mk: float((w[mk] * pnl[mk]).sum() / w[mk].sum()) if mk.any() else None
    return dict(side="short", weighted=True, trades=len(trades), mean_bp=m, se_bp=se, t=m / se if se > 0 else None, unweighted_mean_bp=float(pnl.mean()),
                median_bp=float(np.median(pnl)), capital_used=W / len(trades), sum_w=W, hold_mean=float((w * ages).sum() / W), hold_median=float(np.median(ages)),
                two_c={cv: c2[cv][0] for cv in CONVS}, held_half={cv: c2[cv][1] for cv in CONVS}, held_price=px, commission_bp=comm,
                borrow=dict(scheme=BORROW_SCHEME, mean_bp=bm, htb_share=float((w * htb).sum() / W), htb_n=int(htb.sum()), unweighted_mean_bp=float(pt.mean())),
                net_per_trade={cv: m - c2[cv][0] for cv in CONVS}, net_per_trade_borrow={cv: m - c2[cv][0] - bm for cv in CONVS},
                breakeven_half_spread_bp_side=(m - bm - comm) / 2.0, era1_mean_bp=wm(era1), era2_mean_bp=wm(~era1), era1_n=int(era1.sum()), era2_n=int((~era1).sum()),
                era1_capital=float(w[era1].mean()) if era1.any() else None, era2_capital=float(w[~era1].mean()) if (~era1).any() else None,
                down_years_mean_bp=wm(down), down_years_n=int(down.sum()),
                by_year={int(y): dict(n=int((yrs == y).sum()), mean_bp=wm(yrs == y), capital=float(w[yrs == y].mean())) for y in np.unique(yrs)},
                weight_distribution={str(k): int(v) for k, v in sorted(Counter(np.round(np.log2(1.0 / w)).astype(int).tolist()).items())})


def stats_w(res, P, wgrid):
    """Per draw for W: the weighted per-trade mean, trades, capital, and the weighted deployed gross / net PUB / Sharpe / net PB / exposure."""
    tr = res["trades"]
    w = weights_of(tr, wgrid)
    pnl = pnl_bp_of(tr)
    S = series_w(tr, P, wgrid)
    assert np.isfinite(S["book"][S["mask"]]).all(), "NaN in a weighted deployed series"
    dep = {cv: costed_w(tr, S, P, cv) for cv in CONVS}
    return dict(gross_bp=dep["PUB"]["gross_bp"], net_bp_PUB=dep["PUB"]["net_bp"], sharpe_net_PUB=dep["PUB"]["sharpe_net"], net_bp_PB=dep["PB"]["net_bp"],
                trade_mean_bp=float((w * pnl).sum() / w.sum()), trades=len(tr), exposure=float(S["mask"].sum() / res["defined"].sum()),
                capital=float(w.mean()), unweighted_trade_mean_bp=float(pnl.mean()))


def control_C_w(pnl, w, rng, draws=1000, chunk=100):
    """Random direction on the weighted ledger: sum w s x / sum w per draw."""
    means = []
    for _ in range(draws // chunk):
        signs = rng.choice([-1.0, 1.0], size=(chunk, pnl.size))
        means.append((signs * (w * pnl)[None, :]).sum(axis=1) / w.sum())
    cm = np.concatenate(means)
    obs = float((w * pnl).sum() / w.sum())
    return dict(V53._dist(cm, obs), mean=float(cm.mean()), se=float(cm.std(ddof=1) / np.sqrt(cm.size)))


def assert_W(P, res, wgrid, hits, tol=1e-12, tag="[W]"):
    """Every trade's weight is 0.5^hits at its (e0, row) exactly; with every weight 1 the weighted rebuild equals V58.rebuild exactly and
    the kernel's hedged deployed series (book_dep_x) to tol on every covered bar, and costed_w equals G22.costed key for key on the same
    series; with the arm's weights the weighted series x sum w equals the bar-loop second implementation to tol and sums to sum w pnl
    to 1e-9; sum w pnl / sum w equals a plain-Python loop over hits; capital used == sum w / n."""
    tr = res["trades"]
    w = weights_of(tr, wgrid)
    for j, (row, e0, _a, _p, _s) in enumerate(tr):
        assert w[j] == 0.5 ** int(hits[e0, row]), f"{tag} trade {j} ({P['symbols'][row]} {P['dates'][e0]}): weight {w[j]!r} != 0.5^{int(hits[e0, row])}"
    ones = np.ones_like(wgrid)
    reb1, cw1, ew1 = rebuild_w(tr, P, ones)
    reb0, cnt0, ent0 = V58.rebuild(tr, P, hedged=True)
    assert np.array_equal(reb1, reb0) and np.array_equal(cw1, cnt0.astype(float)) and np.array_equal(ew1, ent0.astype(float)), f"{tag} unit weights != V58.rebuild"
    held = res["held"].astype(np.int64)
    covered = cnt0 == held
    S1 = series_w(tr, P, ones)
    bd = np.asarray(res["book_dep_x"], float)
    worst1 = float(np.abs(np.nan_to_num(S1["book"][covered]) - np.nan_to_num(bd[covered])).max())
    assert worst1 < tol, f"{tag} the unit-weight series differs from the kernel's book_dep_x ({worst1:.2e})"
    assert np.array_equal(S1["mask"][covered], res["mask_dep"][covered]), f"{tag} the unit-weight mask differs from the kernel's"
    for cv in CONVS:                                                  # the same series into both: the ARITHMETIC is what is compared
        mine = costed_w(tr, S1, P, cv)
        ref = G22.costed(dict(trades=tr, book=S1["book"], mask=S1["mask"], ent=ent0, held=cnt0), P["G4"][cv])
        for k in ref:
            assert mine[k] == ref[k], f"{tag} costed_w[{k}] {mine[k]} != G22.costed {ref[k]} with unit weights ({cv})"
    S = series_w(tr, P, wgrid)
    sx, cw = weighted_loop(tr, P, wgrid)
    worst2 = float(np.abs(np.nan_to_num(S["book"] * S["held_w"]) - sx).max())
    assert worst2 < tol and float(np.abs(S["held_w"] - cw).max()) < tol, f"{tag} the weighted series x sum w differs from the bar loop ({worst2:.2e})"
    pnl = pnl_bp_of(tr)
    assert abs(float(S["signed"].sum()) * 1e4 - float((w * pnl).sum())) < 1e-9, f"{tag} the weighted rebuild does not sum to sum w pnl"
    num = den = 0.0
    for (row, e0, _a, p, _s) in tr:
        wi = 0.5 ** int(hits[e0, row])
        num += wi * p * 1e4
        den += wi
    m_direct = num / den
    m = float((w * pnl).sum() / w.sum())
    assert abs(m - m_direct) < 1e-9, f"{tag} sum w pnl / sum w {m:.10f} != the direct loop {m_direct:.10f}"
    cap = float(w.sum() / len(tr))
    assert abs(cap - float(w.mean())) < 1e-15 and abs(cap - den / len(tr)) < 1e-12, f"{tag} capital used != sum w / n"
    return dict(worst_unit=worst1, worst_loop=worst2, mean_w_bp=m, capital=cap, sum_w=float(w.sum()), n=len(tr))


# ------------------------------------------------------------------ the filter nulls: DROP and FROT
def event_hits(H, B):
    """(N, 5) bool: the sinks' flags on the gated events in (t, i) order."""
    return np.stack([H[k][B["ev_t"], B["ev_i"]] for k in range(len(SINKS))], axis=1)


def drop_draw(B, n_rm, rng):
    """The gated signal with n_rm uniformly random gated events removed; returns (signal, the removed event indices)."""
    pick = np.sort(rng.choice(B["ev_t"].size, size=n_rm, replace=False))
    sig = B["gated"].copy()
    sig[B["ev_t"][pick], B["ev_i"][pick]] = False
    return np.ascontiguousarray(sig), pick


def assert_DROP(B, sig, pick, n_rm, obs_pick, tag="[DROP]"):
    """Exactly n_rm gated events removed, nothing added, and the removed set is never the observed one."""
    assert pick.size == n_rm and len(set(pick.tolist())) == n_rm, f"{tag} {pick.size} removed != {n_rm}"
    assert int(B["gated"].sum()) - int(sig.sum()) == n_rm and not (sig & ~B["gated"]).any(), f"{tag} the draw did not remove exactly {n_rm} gated events"
    assert not np.array_equal(pick, obs_pick), f"{tag} the removed set is the observed one"
    return int(sig.sum())


def name_groups(B):
    """{name: the indices of its gated events in time order} (the events are row-major, so per name they are already in t order)."""
    g = {}
    for j, i in enumerate(B["ev_i"]):
        g.setdefault(int(i), []).append(j)
    return {i: np.array(v) for i, v in sorted(g.items())}


def frot_draw(Hev, groups, arm, rng, max_redraw=64):
    """Each name's (k, 5) hit matrix circularly rotated by one offset in [1, k-1]; a name with one event keeps its flags; a rotation that
    leaves the ARM flag equal to a non-constant observed vector is redrawn. Returns (rotated (N, 5), offsets per name, redraws)."""
    Hr = Hev.copy()
    offs, redraw = {}, 0
    for i, idx in groups.items():
        k = idx.size
        if k < 2:
            continue
        blk = Hev[idx]
        f_obs = arm_flag(arm, blk)
        const = f_obs.all() or not f_obs.any()
        for _ in range(max_redraw):
            off = int(rng.integers(1, k))
            rolled = np.roll(blk, off, axis=0)
            if const or not np.array_equal(arm_flag(arm, rolled), f_obs):
                break
            redraw += 1
        else:
            raise AssertionError(f"[FROT] no changing offset found for name {i} after {max_redraw} redraws")
        Hr[idx] = rolled
        offs[i] = off
    return Hr, offs, redraw


def frot_signal(B, Hr, arm):
    f = arm_flag(arm, Hr)
    sig = B["gated"].copy()
    sig[B["ev_t"][f], B["ev_i"][f]] = False
    return np.ascontiguousarray(sig)


def assert_FROT(Hev, Hr, groups, arm, sig, B, n_rm, tag="[FROT]"):
    """Every name's per-sink hit counts kept; on every name with >= 2 events whose observed arm flag is not constant the rotated arm flag
    vector differs from the observed; single-event names keep their flags exactly; the total removal equals the observed count."""
    n_single = n_multi = n_nonconst = 0
    for i, idx in groups.items():
        assert np.array_equal(Hev[idx].sum(axis=0), Hr[idx].sum(axis=0)), f"{tag} name {i}: a per-sink hit count changed"
        if idx.size < 2:
            n_single += 1
            assert np.array_equal(Hev[idx], Hr[idx]), f"{tag} a single-event name's flags changed"
            continue
        n_multi += 1
        fo, fr = arm_flag(arm, Hev[idx]), arm_flag(arm, Hr[idx])
        assert int(fo.sum()) == int(fr.sum()), f"{tag} name {i}: the arm flag count changed"
        if fo.any() and not fo.all():
            n_nonconst += 1
            assert not np.array_equal(fo, fr), f"{tag} name {i}: the rotated arm flag vector is the observed one"
    assert int(B["gated"].sum()) - int(sig.sum()) == n_rm, f"{tag} the rotated filter removes {int(B['gated'].sum()) - int(sig.sum())} != {n_rm}"
    assert not np.array_equal(arm_flag(arm, Hr), arm_flag(arm, Hev)), f"{tag} the rotated flags equal the observed flags on every event"
    return dict(names=len(groups), single=n_single, multi=n_multi, nonconst=n_nonconst)


# ------------------------------------------------------------------ the arms in the report
def arm_report(P, arm, sig, B, H, hits, wgrid, with_groups=True):
    """One arm re-simulated: the deployed block, the per-trade block (W weighted), [HX], the accounting; the row-drop beside."""
    sc, elig, gp = B["sc"], B["elig"], B["gp"]
    res = run_short(P, sig, sc, "cap", CAP)
    V53.assert_series_defs(res)
    hx = dict(hedged=assert_HX(res, P, "book_dep_x", hedged=True), unhedged=assert_HX(res, P, "book_dep", hedged=False))
    out = dict(arm=arm, events=int(sig.sum()), events_removed=int(B["gated"].sum() - sig.sum()), hx=hx, accounting=V49.event_accounting(P, sig, res, cap=CAP), res=res)
    out["gate"] = V61.gate_exposure(res, gp)
    if arm == "W":
        w = weights_of(res["trades"], wgrid)
        out["deployed"] = deployed_block_w(res, P, wgrid)
        out["deployed_unweighted"] = deployed_block(res, P)
        out["per_trade"] = trade_block_w(P, res["trades"], w)
        out["per_trade_unweighted"] = trade_block(P, res, elig, 1, with_groups)
        out["rowdrop"] = dict(per_trade=trade_block_w(P, res["trades"], w), note="W's row-drop is the arm itself: the signal is unchanged; difference 0 by construction")
        out["hx"]["weighted"] = assert_W(P, res, wgrid, hits)
    else:
        out["deployed"] = deployed_block(res, P)
        out["deployed"]["splits_hedged"] = deployed_subsets(res, P, res["book_dep_x"])
        out["per_trade"] = trade_block(P, res, elig, 1, with_groups)
    return out


def rowdrop_report(P, arm, base_res, H, hits, elig, with_groups=False):
    sub = rowdrop_trades(arm, base_res["trades"], H, hits)
    return dict(per_trade=trade_block(P, dict(trades=sub), elig, 1, with_groups), trades=len(sub), dropped=len(base_res["trades"]) - len(sub))


def sink_table(H, hits, B, res, wgrid):
    """Per sink: the threshold, gated events hit, NaN events, hits on the BASE ledger, hit mean and non-hit mean; the hits distribution."""
    tr = res["trades"]
    pnl = pnl_bp_of(tr)
    out = {}
    for q, (nm, f, op, th) in enumerate(SINKS):
        ev = H[q][B["ev_t"], B["ev_i"]]
        m = np.array([bool(H[q, e0, r]) for r, e0, _a, _p, _s in tr])
        out[nm] = dict(feature=f, op=op, threshold=th, events_hit=int(ev.sum()), ledger_hit=int(m.sum()), ledger_hit_mean_bp=float(pnl[m].mean()) if m.any() else None,
                       ledger_nonhit_mean_bp=float(pnl[~m].mean()) if (~m).any() else None, ledger_hit_share=float(m.mean()))
    hv = np.array([int(hits[e0, r]) for r, e0, _a, _p, _s in tr])
    out["hits"] = dict(ledger_distribution={str(k): int((hv == k).sum()) for k in range(6)}, ledger_mean_by_hits={str(k): float(pnl[hv == k].mean()) for k in range(6) if (hv == k).any()},
                       events_distribution={str(k): int(v) for k, v in sorted(Counter(hits[B["ev_t"], B["ev_i"]].tolist()).items())},
                       weight_mean_ledger=float(weights_of(tr, wgrid).mean()))
    return out


def drop_res(d):
    if isinstance(d, dict):
        d.pop("res", None)
        d.pop("_series", None)
        for v in d.values():
            drop_res(v)


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    print(f"    [K] [F0] [R] via d348_prep (cache {'HIT' if P['cache_hit'] else 'BUILD'} {P['cache_key']}); the kernel is D345's (EB.simulate_event), the fill the next open")
    B = base(P)
    T, n = P["T"], P["n"]
    print(f"    [HOLDOUT-GUARD] {assert_HOLDOUT_GUARD()}; a non-existent 'holdout' probe path was refused by the hook before the filesystem was touched ({el()})")
    # [ID]
    res = run_short(P, B["gated"], B["sc"], "cap", CAP)
    idd = assert_ID(P, res)
    print(f"    [ID] the unfiltered gated ledger == D361's G2:T2 gated cap 10: {idd['trades']:,} trades, mean {idd['mean_bp']:+.6f} == stored {idd['stored_mean_bp']:+.6f} to 1e-9 "
          f"(median, held half-spread PUB {idd['held_half_PUB']:.3f}, deployed gross {idd['observed']['gross_bp']:+.4f} / net PUB {idd['observed']['net_bp_PUB']:+.4f} / "
          f"exposure {100 * idd['observed']['exposure']:.2f}% also to 1e-9); the pre-registration's +{PREREG['base_mean_bp']} within 5e-5 ({el()})")
    # [FEAT]
    F = features(P)
    fe = assert_FEAT(P, F, B, np.random.default_rng([SEED, STUDY, 99]))
    print(f"    [FEAT] the five features at (bar_entry, row) -- pcto_ via EXP.own_lagged + V47.percentile_grid, mkt_vol_20 the export's expression -- equal {fe['file']}'s "
          f"columns EXACTLY (NaN patterns included) on {fe['sampled']} sampled gated events and on ALL {fe['events']:,}; the export's G2_on & not-excluded rows are exactly "
          f"the gated events; NaN on the events: " + ", ".join(f"{k} {v}" for k, v in fe["nan_counts"].items()) + f" ({el()})")
    # [HIT]
    H, hits = hit_grids(F, T, n)
    wgrid = weight_grid(hits)
    ht = assert_HIT(P, F, H, hits, B, res, np.random.default_rng([SEED, STUDY, 98]))
    print(f"    [HIT] the grid flags (NaN never hits) equal a plain-Python recomputation with an explicit NaN test on all {ht['events']:,} gated events and hits == their "
          f"sum; on the base ledger the per-sink hit counts {ht['ledger_hit_counts']} equal those from the export's own columns {ht['export_hit_counts']} flag for flag ({el()})")
    # [RD]
    rd = assert_RD(P, res, H, hits)
    print(f"    [RD] row-drop A5 on era 2: {rd['A5']['era2_trades']:,} trades, mean {rd['A5']['era2_mean_bp']:+.4f} == the export analysis's (1,221, +91.5) and == the same "
          f"statistic recomputed from the export's columns to 1e-9; whole sample row-drop A2 {rd['A2']['trades']:,} {rd['A2']['mean_bp']:+.4f}, A5 {rd['A5']['trades']:,} "
          f"{rd['A5']['mean_bp']:+.4f}, each == the export's to 1e-9 ({el()})")
    # [W]
    wv = assert_W(P, res, wgrid, hits)
    print(f"    [W] every trade's weight == 0.5^hits at its (e0, row); with every weight 1 the weighted rebuild == V58.rebuild exactly and == the kernel's book_dep_x to {wv['worst_unit']:.0e}, and costed_w == G22.costed key "
          f"for key on both conventions; with the arm's weights the series x sum w == a bar-loop second implementation to {wv['worst_loop']:.0e} and sums to sum w pnl; "
          f"sum w pnl / sum w = {wv['mean_w_bp']:+.4f} == a plain-Python loop to 1e-9; capital used {wv['capital']:.4f} == sum w / n ({wv['sum_w']:.1f} / {wv['n']:,}) ({el()})")
    # the arms
    ARM_RES = {}
    for arm in ARMS:
        sig = arm_signal(arm, B["gated"], H, hits)
        ARM_RES[arm] = arm_report(P, arm, sig, B, H, hits, wgrid, with_groups=False)
    a2, a5, w_ = (ARM_RES[a] for a in ARMS)
    assert [t[:3] for t in w_["res"]["trades"]] == [t[:3] for t in res["trades"]], "[W] W's ledger is not the base ledger"
    assert all(t[2] <= CAP and t[4] == 1 for a in ARMS for t in ARM_RES[a]["res"]["trades"]), "[K] a long or an over-cap hold"
    for a in ("A2", "A5"):
        rm_a = arm_removed(a, H, hits)
        assert all(B["gp"]["gate"][t[1]] and not rm_a[t[1], t[0]] for t in ARM_RES[a]["res"]["trades"]), f"[K] {a}: a trade on a removed or gate-off event"
    print(f"    check: base {int(B['gated'].sum()):,} gated events -> {len(res['trades']):,} trades {float(pnl_bp_of(res['trades']).mean()):+.2f}; A2 {a2['events']:,} events "
          f"({a2['events_removed']:,} removed) -> {a2['per_trade']['trades']:,} trades {a2['per_trade']['mean_bp']:+.2f} (t {a2['per_trade']['t']:+.2f}); A5 {a5['events']:,} "
          f"({a5['events_removed']:,} removed) -> {a5['per_trade']['trades']:,} {a5['per_trade']['mean_bp']:+.2f}; W {w_['per_trade']['trades']:,} trades, per unit capital "
          f"{w_['per_trade']['mean_bp']:+.2f} (t {w_['per_trade']['t']:+.2f}, capital {w_['per_trade']['capital_used']:.3f}); every A2 / A5 trade on a kept, gate-on event")
    # [HX]
    print("    [HX] hedged deployed x held == the ledger's sgn(v - m) per bar and unhedged x held == sgn v, to 1e-12 on every covered bar; " + "; ".join(
        f"{a} {ARM_RES[a]['hx']['hedged']['worst']:.0e}/{ARM_RES[a]['hx']['unhedged']['worst']:.0e} ({ARM_RES[a]['hx']['hedged']['uncovered']} tail)" for a in ARMS)
        + f"; W's weighted series against the weighted bar loop {w_['hx']['weighted']['worst_loop']:.0e} ({el()})")
    # [DROP] [FROT] on 5 draws (A2)
    ai = ARM_INDEX[PRIMARY]
    Hev = event_hits(H, B)
    f_obs = arm_flag(PRIMARY, Hev)
    obs_pick = np.flatnonzero(f_obs)
    n_rm = int(f_obs.sum())
    rngD = np.random.default_rng([SEED, STUDY, ai, NULL["DROP"], 0])
    D_ = []
    for d in range(5):
        sigD, pick = drop_draw(B, n_rm, rngD)
        assert_DROP(B, sigD, pick, n_rm, obs_pick)
        D_.append(null_stats(run_short(P, sigD, B["sc"], "cap", CAP), P))
    groups = name_groups(B)
    rngF = np.random.default_rng([SEED, STUDY, ai, NULL["FROT"], 0])
    F_, fi = [], []
    for d in range(5):
        Hr, offs, redraw = frot_draw(Hev, groups, PRIMARY, rngF)
        sigF = frot_signal(B, Hr, PRIMARY)
        fi.append(dict(assert_FROT(Hev, Hr, groups, PRIMARY, sigF, B, n_rm), redraws=redraw))
        F_.append(null_stats(run_short(P, sigF, B["sc"], "cap", CAP), P))
    fm = lambda xs, key, f: ", ".join(format(x[key], f) for x in xs)
    single_ev = sum(1 for idx in groups.values() if idx.size < 2)
    print(f"    [DROP] 5 draws: exactly {n_rm:,} of the {int(B['gated'].sum()):,} gated events removed at random (the observed |S1|S2| count), never the observed set; per "
          f"trade {fm(D_, 'trade_mean_bp', '+.2f')} bp ({fm(D_, 'trades', ',')} trades) vs A2 {a2['per_trade']['mean_bp']:+.2f}")
    print(f"    [FROT] 5 draws: every name's per-sink hit counts kept, the A2 flag vector never the observed one on the {fi[0]['nonconst']} names with a non-constant flag "
          f"(of {fi[0]['multi']} with >= 2 events; {fi[0]['single']} single-event names of {fi[0]['names']} keep their flag -- {100 * fi[0]['single'] / fi[0]['names']:.1f}% of names, "
          f"{single_ev:,} events); redraws on periodic vectors {[x['redraws'] for x in fi]}; per trade {fm(F_, 'trade_mean_bp', '+.2f')} bp ({fm(F_, 'trades', ',')} trades) ({el()})")
    # [ROT] on 5 draws
    gp = B["gp"]
    ung_f = arm_signal(PRIMARY, B["ung"], H, hits)
    rngR = np.random.default_rng([SEED, STUDY, ai, NULL["ROT"], 0])
    offs = V61.rot_offsets(gp, 5, rngR)
    R_, rot_info = [], []
    for k in offs:
        rot = V61.rotate_gate(gp, k)
        rot_info.append(V61.assert_ROT(gp, rot, k))
        R_.append(null_stats(run_short(P, np.ascontiguousarray(ung_f & rot[:, None]), B["sc"], "cap", CAP), P))
    print(f"    [ROT] 5 rotations of {GATE} (offsets {[int(k) for k in offs]}, distinct, in [1, {gp['Td'] - 1}]) re-ANDed with the FILTERED ungated trigger ({int(ung_f.sum()):,} of "
          f"{int(B['ung'].sum()):,} T2 events; the flags computed on the observed bars, only the gate rotated): on-share and the circular run multiset kept exactly, never the "
          f"observed gate; wrap split in {sum(r['wrap_split'] for r in rot_info)} of 5; per trade {fm(R_, 'trade_mean_bp', '+.2f')} bp ({fm(R_, 'trades', ',')} trades) ({el()})")
    # [A'] 2 draws
    rngA = np.random.default_rng([SEED, STUDY, ai, NULL["A"], 0])
    A_ = []
    rA_keep = None
    sigA2 = arm_signal(PRIMARY, B["gated"], H, hits)
    for d in range(2):
        ss, sc_ = V61.aprime_gate_draw(sigA2, B["sc"], B["elig"], gp["gate"], rngA)
        rA = run_short(P, ss, sc_, "cap", CAP)
        A_.append(null_stats(rA, P))
        if d == 0:
            rA_keep = rA
    print(f"    [A'] 2 draws within the gate on the A2 signal: every rotated event on an eligible gate-on bar, every name's event count kept, no long, the score rotated with "
          f"the signal; per trade {fm(A_, 'trade_mean_bp', '+.2f')} bp ({fm(A_, 'trades', ',')} trades) vs A2 {a2['per_trade']['mean_bp']:+.2f}")
    # [C]
    pnlA2 = pnl_bp_of(a2["res"]["trades"])
    cC = control_C(pnlA2, np.random.default_rng([SEED, STUDY, ai, NULL["C"]]))
    z = assert_C(cC)
    print(f"    [C] 1,000 random directions on the A2 ledger: mean {cC['mean']:+.3f} bp (se {cC['se']:.3f}, z {z:+.2f}) within 3 SE of zero; p50 {cC['p50']:+.2f} p95 "
          f"{cC['p95']:+.2f} max {cC['max']:+.2f}; observed {pnlA2.mean():+.2f} {'above' if cC['above'] else 'NOT above'} p95")
    # [S]
    worst_s, n_s, n_fell, n_rose, worst_m = assert_S_short(P, rA_keep["trades"], np.random.default_rng([SEED, STUDY, 2]))
    pert = perturb_test(P, sigA2, B["sc"], 1, a2["res"], -1.0)
    print(f"    [S] SIGN IN MONEY on the SHORT: {n_s} sampled A' trades equal the open-fill recomputation against the floored market to {worst_s:.1f} (bit-identical); a "
          f"short on a name that fell pays positively ({n_fell} fell, {n_rose} rose); the long of the same path pays the opposite to {worst_m:.1f}; +50 bp on "
          f"r1T[{pert['bar']}, {pert['row']}] ({pert['symbol']} {pert['date']}, bar 2 of a {pert['age']}-bar A2 short) moves that trade by {pert['dpnl']:+.3f} bp and no "
          f"other, the deployed series by {pert['delta']:.4f} = -50 / {pert['n_open']} open on that bar only ({el()})")
    # [6]
    broke = []
    try:                                                              # [ID] on a perturbed ledger (+1 bp on one trade)
        r6 = dict(res, trades=[(r, e, a, p + (1e-4 if j == 0 else 0.0), sd) for j, (r, e, a, p, sd) in enumerate(res["trades"])])
        assert_ID(P, r6)
    except AssertionError as e:
        assert "[ID]" in str(e)
        broke.append("ID")
    try:                                                              # [FEAT] on a perturbed feature (one gated event's pcto moved by 1e-6)
        F6 = dict(F)
        F6[FEATS[0]] = F[FEATS[0]].copy()
        j = next(j for j in range(B["ev_t"].size) if np.isfinite(F[FEATS[0]][B["ev_t"][j], B["ev_i"][j]]))
        F6[FEATS[0]][B["ev_t"][j], B["ev_i"][j]] += 1e-6
        assert_FEAT(P, F, B, np.random.default_rng(6), F_override=F6)
    except AssertionError as e:
        assert "[FEAT]" in str(e)
        broke.append("FEAT")
    try:                                                              # [DROP] on a wrong count (one event more)
        sig6, pick6 = drop_draw(B, n_rm + 1, np.random.default_rng(6))
        assert_DROP(B, sig6, pick6, n_rm, obs_pick)
    except AssertionError as e:
        assert "[DROP]" in str(e)
        broke.append("DROP")
    try:                                                              # [W] on a perturbed weight (one trade's weight x (1 + 1e-6))
        w6 = wgrid.copy()
        r0, e0 = res["trades"][0][0], res["trades"][0][1]
        w6[e0, r0] *= 1.0 + 1e-6
        assert_W(P, res, w6, hits)
    except AssertionError as e:
        assert "[W]" in str(e)
        broke.append("W")
    try:                                                              # [S] on a sign-flipped ledger
        assert_S_short(P, [(r, e, a, -p, sd) for r, e, a, p, sd in rA_keep["trades"]], np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    assert broke == ["ID", "FEAT", "DROP", "W", "S"], f"[6] raised: {broke}"
    print("    [6] [ID] raises on a perturbed ledger (+1 bp on one trade); [FEAT] raises on a perturbed feature (1e-6 on one event's pcto); [DROP] raises on a wrong count "
          "(one event more); [W] raises on a perturbed weight (one trade's weight x (1 + 1e-6): no longer 0.5^hits); [S] raises on a sign-flipped ledger")
    summ = dict(ID=idd, FEAT=fe, HIT=ht, RD=rd, W=wv, C=cC, drop=D_, frot=F_, frot_info=fi, rot=R_, rot_info=rot_info, aprime=A_, guard=guard_line(),
                arms={a: dict(events=ARM_RES[a]["events"], removed=ARM_RES[a]["events_removed"], trades=ARM_RES[a]["per_trade"]["trades"], mean_bp=ARM_RES[a]["per_trade"]["mean_bp"],
                              t=ARM_RES[a]["per_trade"]["t"]) for a in ARMS})
    (SELFTEST_TMP / "selftest_summary.json").write_text(json.dumps(clean(summ), indent=1))
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_arm(P, arm, draws, draws_rot, part, paths):
    ai = ARM_INDEX[arm]
    B = base(P)
    T, n = P["T"], P["n"]
    res0 = run_short(P, B["gated"], B["sc"], "cap", CAP)
    assert_ID(P, res0)
    F = features(P)
    fe = assert_FEAT(P, F, B, np.random.default_rng([SEED, STUDY, 99]))
    H, hits = hit_grids(F, T, n)
    assert_HIT(P, F, H, hits, B, res0, np.random.default_rng([SEED, STUDY, 98]))
    wgrid = weight_grid(hits)
    sig = arm_signal(arm, B["gated"], H, hits)
    res = run_short(P, sig, B["sc"], "cap", CAP)
    st = stats_w if arm == "W" else null_stats
    obs = st(res, P, wgrid) if arm == "W" else observed_stats(res, P)
    gp, sc, elig = B["gp"], B["sc"], B["elig"]
    print(f"\n  arm {arm} part {part}: {int(sig.sum()):,} events (of {int(B['gated'].sum()):,} gated; {int(B['gated'].sum() - sig.sum()):,} removed) -> {obs['trades']:,} trades; "
          f"per trade {obs['trade_mean_bp']:+.2f} bp{' per unit capital' if arm == 'W' else ''}; deployed gross {obs['gross_bp']:+.2f} net PUB {obs['net_bp_PUB']:+.2f} bp/bar; "
          f"exposure {100 * obs['exposure']:.1f}%  [FEAT] ok on {fe['events']:,} events")
    seeds = {k: [SEED, STUDY, ai, NULL[k], part] for k in ("DROP", "FROT", "ROT", "A")}
    rngD, rngF, rngR, rngA = (np.random.default_rng(seeds[k]) for k in ("DROP", "FROT", "ROT", "A"))
    stat = (lambda r: stats_w(r, P, wgrid)) if arm == "W" else (lambda r: null_stats(r, P))
    keys = KEYS + (("capital", "unweighted_trade_mean_bp") if arm == "W" else ())
    tm = dict(DROP=0.0, FROT=0.0, ROT=0.0, A=0.0)
    D_, F_, fi, n_rm, single = [], [], [], None, None
    if arm != "W":
        Hev = event_hits(H, B)
        f_obs = arm_flag(arm, Hev)
        obs_pick = np.flatnonzero(f_obs)
        n_rm = int(f_obs.sum())
        groups = name_groups(B)
        single = dict(names=len(groups), single_event_names=sum(1 for v in groups.values() if v.size < 2),
                      single_event_removed=int(sum(f_obs[v].sum() for v in groups.values() if v.size < 2)))
        ts = time.time()
        for d in range(draws_rot):
            t1 = time.time()
            sigD, pick = drop_draw(B, n_rm, rngD)
            assert_DROP(B, sigD, pick, n_rm, obs_pick)
            D_.append(stat(run_short(P, sigD, sc, "cap", CAP)))
            t2 = time.time()
            Hr, offs, redraw = frot_draw(Hev, groups, arm, rngF)
            sigF = frot_signal(B, Hr, arm)
            fi.append(dict(assert_FROT(Hev, Hr, groups, arm, sigF, B, n_rm), redraws=redraw))
            F_.append(stat(run_short(P, sigF, sc, "cap", CAP)))
            tm["DROP"] += t2 - t1
            tm["FROT"] += time.time() - t2
            if (d + 1) % 20 == 0 or d + 1 == draws_rot:
                print(f"    {arm}: DROP/FROT {d + 1}/{draws_rot} ({time.time() - ts:.0f}s; DROP {tm['DROP'] / (d + 1):.2f} s/draw, FROT {tm['FROT'] / (d + 1):.2f})", flush=True)
    # the gate rotation on the filtered (W: unfiltered, re-weighted) ungated trigger
    ung_f = arm_signal(arm, B["ung"], H, hits)
    offs = V61.rot_offsets(gp, draws_rot, rngR)
    R_, rot_info = [], []
    ts = time.time()
    for d, k in enumerate(offs):
        t1 = time.time()
        rot = V61.rotate_gate(gp, k)
        rot_info.append(V61.assert_ROT(gp, rot, k))
        R_.append(stat(run_short(P, np.ascontiguousarray(ung_f & rot[:, None]), sc, "cap", CAP)))
        tm["ROT"] += time.time() - t1
        if (d + 1) % 20 == 0 or d + 1 == draws_rot:
            print(f"    {arm}: rotation {d + 1}/{draws_rot} ({time.time() - ts:.0f}s; {tm['ROT'] / (d + 1):.2f} s/draw)", flush=True)
    A_ = []
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        ss, sc_ = V61.aprime_gate_draw(sig, sc, elig, gp["gate"], rngA)
        A_.append(stat(run_short(P, ss, sc_, "cap", CAP)))
        tm["A"] += time.time() - t1
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {arm}: A' {d + 1}/{draws} ({time.time() - ts:.0f}s; {tm['A'] / (d + 1):.2f} s/draw)", flush=True)
    col = lambda xs: {k: [x[k] for x in xs] for k in keys} if xs else {k: [] for k in keys}
    out = dict(study=STUDY, arm=arm, arm_index=ai, cell=V61.cell_name(GATE, TRIG), exit=f"cap{CAP}", draws=draws, draws_rot=draws_rot, part=part, seeds=seeds,
               events=int(sig.sum()), events_gated=int(B["gated"].sum()), events_removed=int(B["gated"].sum() - sig.sum()), events_ungated=int(B["ung"].sum()),
               events_ungated_filtered=int(ung_f.sum()), observed=obs, n_removed_observed=n_rm, single_event=single,
               control_DROP=col(D_), control_FROT=col(F_), frot_redraws=[x["redraws"] for x in fi], frot_nonconst_names=(fi[0]["nonconst"] if fi else None),
               control_ROT=col(R_), rot_offsets=[int(k) for k in offs], rot_wrap_split=[r["wrap_split"] for r in rot_info], rot_linear_kept=[r["linear_kept"] for r in rot_info],
               control_A_prime=col(A_),
               notes=dict(DROP="a uniformly random subset of the gated events of the observed removal's size, removed from the signal, re-simulated" if arm != "W" else "skipped: W's filter is a weight",
                          FROT="per name, the 5-column hit matrix over its gated events rotated by one offset in [1, k-1]; single-event names keep their flags; periodic vectors redrawn" if arm != "W" else "skipped: W's filter is a weight",
                          ROT="D361's gate rotation re-ANDed with the filtered ungated trigger; the flags are those of the observed bars, only the gate is rotated" + (" (W: unfiltered, re-weighted at the bar)" if arm == "W" else ""),
                          A="D361's A' within the gate (elig & gate) on the arm's signal" + (" (W: the unfiltered gated signal, the weight read at the landing bar)" if arm == "W" else ""),
                          W_statistic="trade_mean_bp is sum w pnl / sum w (return per unit capital); gross / net are the weighted deployed series costed with weighted turnover" if arm == "W" else None),
               seconds_per_draw=dict(DROP=tm["DROP"] / max(draws_rot, 1) if arm != "W" else None, FROT=tm["FROT"] / max(draws_rot, 1) if arm != "W" else None,
                                     ROT=tm["ROT"] / max(draws_rot, 1), A=tm["A"] / max(draws, 1)), rss=PREP.rss_line(), guard=guard_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(arm=arm, part=part))
    f.write_text(json.dumps(clean(out)))
    msg = f"  wrote {f}: per trade"
    for nm, xs in (("DROP", D_), ("FROT", F_), ("ROT", R_), ("A'", A_)):
        if xs:
            r = np.array([x["trade_mean_bp"] for x in xs])
            msg += f" {nm} p50 {np.median(r):+.2f} p95 {np.quantile(r, .95):+.2f};"
    print(msg + f" vs observed {obs['trade_mean_bp']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def load_controls(paths, arm, obs):
    fs = sorted(paths["dir"].glob(f"d362_ctrl_{arm}_p*.json"))
    if not fs:
        return None
    C = dict(DROP={}, FROT={}, ROT={}, A_prime={})
    parts, offs, splits, lin, redraws = [], [], [], [], []
    for f in fs:
        d = json.loads(f.read_text())
        assert d["arm"] == arm and d["draws"] == len(d["control_A_prime"]["trade_mean_bp"]) and d["draws_rot"] == len(d["control_ROT"]["trade_mean_bp"]), f"[P] {f.name}"
        for k in ("net_bp_PUB", "gross_bp", "trade_mean_bp", "trades"):
            assert abs(d["observed"][k] - obs[k]) < 1e-9, f"[P] {f.name}: observed {k} {d['observed'][k]} differs from the re-simulated {obs[k]}"
        for nm, key in (("DROP", "control_DROP"), ("FROT", "control_FROT"), ("ROT", "control_ROT"), ("A_prime", "control_A_prime")):
            for k in d[key]:
                C[nm].setdefault(k, []).extend(d[key][k])
        offs.extend(d["rot_offsets"])
        splits.extend(d["rot_wrap_split"])
        lin.extend(d["rot_linear_kept"])
        redraws.extend(d.get("frot_redraws") or [])
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], draws_rot=d["draws_rot"], seconds_per_draw=d.get("seconds_per_draw"), rss=d.get("rss")))
    assert len(set(offs)) == len(offs), f"[ROT] {len(offs) - len(set(offs))} repeated offsets across parts"
    stats = ("trade_mean_bp", "net_bp_PUB", "sharpe_net_PUB", "gross_bp", "net_bp_PB")
    tdist = lambda x: dict(p50=float(np.median(x)), min=int(min(x)), max=int(max(x))) if x else None
    out = dict(parts=parts, draws=len(C["A_prime"]["trade_mean_bp"]), draws_rot=len(C["ROT"]["trade_mean_bp"]), draws_drop=len(C["DROP"].get("trade_mean_bp", [])),
               draws_frot=len(C["FROT"].get("trade_mean_bp", [])), rot_offsets_distinct=len(set(offs)), rot_wrap_splits=int(sum(splits)), rot_linear_kept=int(sum(lin)),
               frot_redraws_total=int(sum(redraws)), n_removed_observed=d["n_removed_observed"], single_event=d["single_event"], notes=d["notes"])
    for nm in C:
        if C[nm].get("trade_mean_bp"):
            out[nm] = {k: V53._dist(C[nm][k], obs[k]) for k in stats}
            out[nm]["trades"] = tdist(C[nm]["trades"])
        else:
            out[nm] = None
    return out


def stage_report(P, paths):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    B = base(P)
    T, n = P["T"], P["n"]
    res0 = run_short(P, B["gated"], B["sc"], "cap", CAP)
    idd = assert_ID(P, res0)
    F = features(P)
    fe = assert_FEAT(P, F, B, np.random.default_rng([SEED, STUDY, 99]))
    H, hits = hit_grids(F, T, n)
    ht = assert_HIT(P, F, H, hits, B, res0, np.random.default_rng([SEED, STUDY, 98]))
    rd = assert_RD(P, res0, H, hits)
    wgrid = weight_grid(hits)
    print(f"    [HOLDOUT-GUARD] {assert_HOLDOUT_GUARD()}")
    print(f"    [ID] base == D361's G2:T2 ({idd['trades']:,}, {idd['mean_bp']:+.4f}) to 1e-9; [FEAT] {fe['events']:,} events == the export's columns; [HIT] ledger hit counts "
          f"{ht['ledger_hit_counts']} == the export's; [RD] row-drop A5 era 2 {rd['A5']['era2_trades']:,} / {rd['A5']['era2_mean_bp']:+.2f} ({el()})")
    BASE = dict(events=int(B["gated"].sum()), res=res0)
    V53.assert_series_defs(res0)
    BASE["hx"] = dict(hedged=assert_HX(res0, P, "book_dep_x", hedged=True), unhedged=assert_HX(res0, P, "book_dep", hedged=False))
    BASE["deployed"] = deployed_block(res0, P)
    BASE["deployed"]["splits_hedged"] = deployed_subsets(res0, P, res0["book_dep_x"])
    BASE["per_trade"] = trade_block(P, res0, B["elig"], 1, True)
    BASE["gate"] = V61.gate_exposure(res0, B["gp"])
    BASE["accounting"] = V49.event_accounting(P, B["gated"], res0, cap=CAP)
    R = {}
    for arm in ARMS:
        sig = arm_signal(arm, B["gated"], H, hits)
        a = arm_report(P, arm, sig, B, H, hits, wgrid, with_groups=True)
        if arm != "W":
            a["rowdrop"] = rowdrop_report(P, arm, res0, H, hits, B["elig"], with_groups=(arm == PRIMARY))
            a["rowdrop"]["diff_resim_minus_rowdrop_bp"] = a["per_trade"]["mean_bp"] - a["rowdrop"]["per_trade"]["mean_bp"]
        else:
            a["rowdrop"]["diff_resim_minus_rowdrop_bp"] = 0.0
        a["observed"] = stats_w(a["res"], P, wgrid) if arm == "W" else observed_stats(a["res"], P)
        a["controls"] = load_controls(paths, arm, a["observed"])
        pnl = pnl_bp_of(a["res"]["trades"])
        rngC = np.random.default_rng([SEED, STUDY, ARM_INDEX[arm], NULL["C"]])
        a["control_C"] = control_C_w(pnl, weights_of(a["res"]["trades"], wgrid), rngC) if arm == "W" else control_C(pnl, rngC)
        R[arm] = a
        print(f"    {arm}: [HX] {a['hx']['hedged']['worst']:.0e}/{a['hx']['unhedged']['worst']:.0e}; {a['events']:,} events ({a['events_removed']:,} removed) -> "
              f"{a['per_trade']['trades']:,} trades; controls {'loaded' if a['controls'] else 'NOT RUN'} ({el()})", flush=True)
    SK = sink_table(H, hits, B, res0, wgrid)
    wv = R["W"]["hx"]["weighted"]

    # ---- print ----
    print("\n" + "=" * 170)
    print("THE SINK FILTER on D361's gated gap-up fade (G2 x T2, short at the next open, cap 10, hedged by the floored market); bp per TRADE. re-sim = the filter applied "
          "to the SIGNAL and re-simulated; row-drop = the same flags on D361's ledger rows. W: per unit of CAPITAL (sum w pnl / sum w), weights 0.5^hits")
    print("=" * 170)
    print("  %-5s %-8s %7s %6s %7s %7s %6s %5s | %6s %6s %6s %6s %5s | %7s %7s | %7s | %7s %7s %6s" % (
        "arm", "version", "events", "n", "mean", "median", "t", "hold", "2c PUB", "2c PB", "hs PUB", "borrow", "HTB%", "netPUB", "netPB", "be hs/s", "era1", "era2", "down"))

    def row(label, ver, ev, d):
        b, nb = d["borrow"], d["net_per_trade_borrow"]
        print("  %-5s %-8s %7s %6d %+7.1f %+7.1f %+6.2f %5.1f | %6.1f %6.1f %6.1f %6.1f %5.2f | %+7.1f %+7.1f | %7.1f | %+7.1f %+7.1f %6s" % (
            label, ver, f"{ev:,}" if ev is not None else "-", d["trades"], d["mean_bp"], d["median_bp"], d["t"] or 0, d["hold_mean"], d["two_c"]["PUB"], d["two_c"]["PB"],
            d["held_half"]["PUB"], b["mean_bp"], 100 * b["htb_share"], nb["PUB"], nb["PB"], d["breakeven_half_spread_bp_side"], d["era1_mean_bp"] or 0, d["era2_mean_bp"] or 0,
            ("%+.0f" % d["down_years_mean_bp"]) if d["down_years_mean_bp"] is not None else "-"))
    row("base", "D361", BASE["events"], BASE["per_trade"])
    for arm in ARMS:
        row(arm + (" *" if arm == PRIMARY else ""), "re-sim", R[arm]["events"], R[arm]["per_trade"])
        row(arm, "row-drop", None, R[arm]["rowdrop"]["per_trade"])
    print("  hs PUB = the held names' median PUB half-spread at entry on THIS ledger (bp/side); netPUB/netPB = mean - 2c - borrow; be hs/s = the held half-spread at which "
          "the net after commission and borrow is zero; W's median is the unweighted median, its hold / borrow / era splits capital-weighted")
    w_ = R["W"]["per_trade"]
    print(f"  W: capital used {w_['capital_used']:.4f} of the base's (sum w {w_['sum_w']:.1f} over {w_['trades']:,} trades); unweighted mean {w_['unweighted_mean_bp']:+.2f}; "
          f"se {w_['se_bp']:.2f}; weight distribution (hits: trades) " + ", ".join(f"{k}: {v}" for k, v in w_["weight_distribution"].items()))
    for arm in ("A2", "A5"):
        d = R[arm]["rowdrop"]
        print(f"  {arm}: re-simulated {R[arm]['per_trade']['trades']:,} trades {R[arm]['per_trade']['mean_bp']:+.2f} vs row-drop {d['trades']:,} {d['per_trade']['mean_bp']:+.2f}: "
              f"difference {d['diff_resim_minus_rowdrop_bp']:+.2f} bp (Q10); row-drop era 2 {d['per_trade']['era2_mean_bp']:+.2f} [{d['per_trade']['era2_n']:,}]")
    print("\n  THE SINKS on the base ledger (D361's 3,977): threshold, gated events hit [NaN never hits], trades hit, hit mean / non-hit mean bp per trade")
    for nm, f, op, th in SINKS:
        s = SK[nm]
        print(f"  {nm} {f:22s} {op} {th:6.2f}: events {s['events_hit']:5,} (NaN {fe['nan_counts'].get(f, 0):4,}); ledger {s['ledger_hit']:5,} ({100 * s['ledger_hit_share']:.1f}%) "
              f"hit {fq(s['ledger_hit_mean_bp'], 1)} / non-hit {fq(s['ledger_nonhit_mean_bp'], 1)}")
    hd = SK["hits"]
    print("  hits on the ledger: " + ", ".join(f"{k}: {v} ({fq(hd['ledger_mean_by_hits'].get(k), 0)})" for k, v in hd["ledger_distribution"].items()) + f"; mean weight {hd['weight_mean_ledger']:.3f}")
    print("\n  DEPLOYED BASE (hedged, bp per BAR), the 4-crossing line (G22.costed) and the 2-crossing line; exp% = share of the kernel's defined bars with a position; "
          "W = the CAPITAL-weighted series (sum w (v - m) / sum w), turnover on the weighted entries")
    print("  %-5s %-8s %5s %6s %6s | %7s %6s %7s %7s %7s | %6s %7s %7s | %7s %6s" % ("arm", "version", "exp%", "pos", "ent/yr", "gross", "cost4", "net4PUB", "net4PB", "Sh4PUB",
                                                                                   "cost2", "net2PUB", "net2PB", "Sh2PUB", "be4 hs"))

    def drow(label, ver, d):
        h, hb, h2, hb2 = d["PUB"]["hedged"], d["PB"]["hedged"], d["PUB"]["hedged_2x"], d["PB"]["hedged_2x"]
        pos = d.get("mean_capital_deployed", d["mean_positions_deployed"])
        print("  %-5s %-8s %5.1f %6.1f %6.0f | %+7.2f %6.2f %+7.2f %+7.2f %+7.3f | %6.2f %+7.2f %+7.2f | %+7.3f %6.1f" % (
            label, ver, 100 * d["exposure"], pos, d["entries_per_year"], h["gross_bp"], h["cost_bp"], h["net_bp"], hb["net_bp"], h["sharpe_net"], h2["cost_bp"], h2["net_bp"],
            hb2["net_bp"], h2["sharpe_net"], h["breakeven_half_spread_bp_side"] or 0))
    drow("base", "D361", BASE["deployed"])
    for arm in ARMS:
        drow(arm, "re-sim", R[arm]["deployed"])
    drow("W", "unwtd", R["W"]["deployed_unweighted"])
    print(f"  W: pos = mean capital (sum w) over the deployed bars; exposure equal to the base's by construction (the same positions, weighted)")
    print("\n  CONTROLS per arm, bp per trade (W per unit capital): DROP = the same number of gated events removed at random; FROT = each name's hit flags rotated in time; "
          "ROT = the gate rotated, re-ANDed with the filtered trigger; A' = per-name rotation within elig & gate; C = random direction")
    print("  %-4s %8s | %7s %7s %5s | %7s %7s %5s | %7s %7s %5s | %7s %7s %5s | %7s %7s %5s | %s" % ("arm", "observed", "DROP50", "DROP95", "above", "FROT50", "FROT95", "above",
                                                                                                      "ROT50", "ROT95", "above", "A'50", "A'95", "above", "C50", "C95", "above",
                                                                                                      "deployed net PUB: obs / ROT p95 / A' p95"))
    for arm in ARMS:
        o, k, C = R[arm]["observed"], R[arm]["controls"], R[arm]["control_C"]
        cells = []
        for nm in ("DROP", "FROT", "ROT", "A_prime"):
            x = k[nm] if k else None
            if x:
                cells.append("%+7.2f %+7.2f %5s" % (x["trade_mean_bp"]["p50"], x["trade_mean_bp"]["p95"], "yes" if x["trade_mean_bp"]["above"] else "NO"))
            else:
                cells.append("%-21s" % ("      skipped" if (k and arm == "W" and nm in ("DROP", "FROT")) else "      NOT RUN"))
        dep = f"{o['net_bp_PUB']:+.2f} / {k['ROT']['net_bp_PUB']['p95']:+.2f} / {k['A_prime']['net_bp_PUB']['p95']:+.2f}" if k else f"{o['net_bp_PUB']:+.2f} / - / -"
        print("  %-4s %+8.2f | %s | %s | %s | %s | %+7.2f %+7.2f %5s | %s" % (arm, o["trade_mean_bp"], *cells, C["p50"], C["p95"], "yes" if C["above"] else "NO", dep))
        if k:
            print(f"        draws DROP {k['draws_drop']} FROT {k['draws_frot']} ROT {k['draws_rot']} ({k['rot_offsets_distinct']} distinct offsets, wrap split in {k['rot_wrap_splits']}) A' {k['draws']}; "
                  + (f"removed {k['n_removed_observed']:,} events; single-event names {k['single_event']['single_event_names']:,} of {k['single_event']['names']:,} carrying "
                     f"{k['single_event']['single_event_removed']:,} of the removed; FROT redraws {k['frot_redraws_total']}; " if k["single_event"] else "")
                  + f"trades p50: DROP {k['DROP']['trades']['p50'] if k['DROP'] else '-'} FROT {k['FROT']['trades']['p50'] if k['FROT'] else '-'} ROT {k['ROT']['trades']['p50']:.0f} A' {k['A_prime']['trades']['p50']:.0f} vs observed {o['trades']:,}")
    g4 = R[PRIMARY]["per_trade"]["four_groups"]
    tt = g4["top_trade"]
    print(f"\n  FOUR GROUPS per trade (A2 re-simulated, cap 10, short): n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
          f"payoff {round(g4['payoff'], 2) if g4['payoff'] is not None else '-'} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}; "
          f"trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f} ex-bottom {g4['mean_ex_bottom_bp']:+.1f} trimmed {g4['mean_trimmed_bp']:+.1f}")
    print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
          + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
          + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}; TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} "
          f"(DV pct {round(tt['dv_percentile_at_entry'], 1) if tt['dv_percentile_at_entry'] is not None else '-'}), held {tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = "
          f"{('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
    sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
    r_ = lambda x: "-" if x is None else round(x, 1)
    print(f"      splits: dead {sd_['dead_n']} {r_(sd_['dead_mean_bp'])} / alive {sd_['alive_n']} {r_(sd_['alive_mean_bp'])}; price <= ${sp_['median_price']:.2f} "
          f"{sp_['low_n']} {r_(sp_['low_mean_bp'])} / above {sp_['high_n']} {r_(sp_['high_mean_bp'])}")
    g0 = BASE["per_trade"]["four_groups"]
    print(f"      base for comparison: trimmed {g0['mean_trimmed_bp']:+.1f} ex-top {g0['mean_ex_top_bp']:+.1f} ex-bottom {g0['mean_ex_bottom_bp']:+.1f}; names to half {g0['names_to_half_pnl']}; "
          f"top trade {g0['top_trade']['symbol']} {g0['top_trade']['entry_date']} {g0['top_trade']['pnl_bp']:+.0f} bp ({100 * g0['top_trade']['share_of_pnl']:.1f}%)")
    acc = R[PRIMARY]["accounting"]
    print(f"      check: A2 {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; trades "
          f"{acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    print(f"\n  SPLITS per trade era1 / era2 / down-years [n] (W capital-weighted); down-years {P['down_years']}")
    for label, d in (("base", BASE["per_trade"]),) + tuple((a, R[a]["per_trade"]) for a in ARMS):
        print(f"  {label:5s} era1 {d['era1_mean_bp'] or 0:+.1f} [{d['era1_n']}] era2 {d['era2_mean_bp'] or 0:+.1f} [{d['era2_n']}] down {d['down_years_mean_bp'] or 0:+.1f} [{d['down_years_n']}]"
              + " | by year: " + " ".join(f"{y}:{v['mean_bp']:+.0f}[{v['n']}]" for y, v in sorted(d["by_year"].items())))

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q = {}
    p2, p5, pw, pb = R["A2"]["per_trade"], R["A5"]["per_trade"], R["W"]["per_trade"], BASE["per_trade"]
    k2, C2 = R["A2"]["controls"], R["A2"]["control_C"]
    ab = lambda nm: bool(k2 is not None and k2[nm] is not None and k2[nm]["trade_mean_bp"]["above"])
    q["Q1"] = bool(p2["mean_bp"] > pb["mean_bp"] and ab("DROP") and ab("FROT"))
    q["Q2"] = bool(ab("ROT") and ab("A_prime"))
    q["Q3"] = bool(p5["mean_bp"] > p2["mean_bp"])
    q["Q4"] = bool(p5["trades"] < 0.5 * pb["trades"] and p2["trades"] > 0.5 * pb["trades"])
    q["Q5"] = bool(p2["net_per_trade_borrow"]["PUB"] > 0)
    q["Q6"] = bool(pw["t"] is not None and p2["t"] is not None and pw["t"] > p2["t"])
    q["Q7"] = bool(g4["mean_trimmed_bp"] > g0["mean_trimmed_bp"])
    q["Q8"] = bool(p2["era2_mean_bp"] > pb["era2_mean_bp"])
    q["Q9"] = bool(R["A2"]["deployed"]["exposure"] < BASE["deployed"]["exposure"])
    q["Q10"] = bool(abs(R["A2"]["rowdrop"]["diff_resim_minus_rowdrop_bp"]) <= PREREG["q10_bp"])
    q["check"] = bool(idd["trades"] == PREREG["base_trades"] and rd["A5"]["era2_trades"] == PREREG["rd_A5_era2_trades"] and fe["events"] == BASE["events"])
    print(f"\nPREDICTIONS (A2 re-simulated, cap 10, short, bp per trade unless stated; the signal criterion is GROSS, R15; within-sample with nulls, not out-of-sample)")
    print(f"  Q1 (LOAD-BEARING) A2's gross mean per trade exceeds the unfiltered and is above the p95 of DROP and of FROT: {v_(q['Q1'])} -- A2 {p2['mean_bp']:+.2f} "
          f"({p2['trades']:,}) vs unfiltered {pb['mean_bp']:+.2f} ({pb['trades']:,})"
          + (f"; DROP p95 {k2['DROP']['trade_mean_bp']['p95']:+.2f} (p50 {k2['DROP']['trade_mean_bp']['p50']:+.2f}) at {k2['draws_drop']} draws, FROT p95 "
             f"{k2['FROT']['trade_mean_bp']['p95']:+.2f} (p50 {k2['FROT']['trade_mean_bp']['p50']:+.2f}) at {k2['draws_frot']}" if k2 else "; DROP / FROT NOT RUN (falsified by absence)"))
    print(f"  Q2 A2 above the p95 of the gate rotation and of A' within the gate: {v_(q['Q2'])}"
          + (f" -- ROT p95 {k2['ROT']['trade_mean_bp']['p95']:+.2f} (p50 {k2['ROT']['trade_mean_bp']['p50']:+.2f}) at {k2['draws_rot']}, A' p95 {k2['A_prime']['trade_mean_bp']['p95']:+.2f} "
             f"(p50 {k2['A_prime']['trade_mean_bp']['p50']:+.2f}) at {k2['draws']}" if k2 else " -- ROT / A' NOT RUN (falsified by absence)") + f"; C p95 {C2['p95']:+.2f} (p50 {C2['p50']:+.2f})")
    print(f"  Q3 A5's gross mean exceeds A2's: {v_(q['Q3'])} -- A5 {p5['mean_bp']:+.2f} ({p5['trades']:,}) vs A2 {p2['mean_bp']:+.2f}")
    print(f"  Q4 A5 keeps fewer than half the unfiltered trades, A2 more than half: {v_(q['Q4'])} -- A5 {p5['trades']:,} / A2 {p2['trades']:,} of {pb['trades']:,} "
          f"({100 * p5['trades'] / pb['trades']:.1f}% / {100 * p2['trades'] / pb['trades']:.1f}%)")
    print(f"  Q5 (against) A2 nets > 0 per trade after the PUB 2c and borrow: {v_(q['Q5'])} -- {p2['mean_bp']:+.2f} - 2c PUB {p2['two_c']['PUB']:.2f} - borrow {p2['borrow']['mean_bp']:.2f} "
          f"= {p2['net_per_trade_borrow']['PUB']:+.2f} (PB {p2['net_per_trade_borrow']['PB']:+.2f}); be hs/s {p2['breakeven_half_spread_bp_side']:.1f}")
    print(f"  Q6 W's t on return per unit capital exceeds A2's t: {v_(q['Q6'])} -- W t {pw['t']:+.2f} ({pw['mean_bp']:+.2f} / se {pw['se_bp']:.2f}, capital {pw['capital_used']:.3f}) vs "
          f"A2 t {p2['t']:+.2f} ({p2['mean_bp']:+.2f} on {p2['trades']:,}); base t {pb['t']:+.2f}")
    print(f"  Q7 A2's symmetric 1% trimmed mean exceeds the unfiltered trimmed mean (+35): {v_(q['Q7'])} -- A2 trimmed {g4['mean_trimmed_bp']:+.2f} (k {g4['trim_k']}) vs base "
          f"{g0['mean_trimmed_bp']:+.2f} (k {g0['trim_k']}; the pre-reg's +{PREREG['unf_trimmed_bp']:.0f})")
    print(f"  Q8 A2's era-2 mean exceeds the unfiltered era-2 mean (+55): {v_(q['Q8'])} -- A2 era 2 {p2['era2_mean_bp']:+.2f} [{p2['era2_n']:,}] vs base {pb['era2_mean_bp']:+.2f} "
          f"[{pb['era2_n']:,}]; era 1 {p2['era1_mean_bp']:+.2f} vs {pb['era1_mean_bp']:+.2f}")
    print(f"  Q9 A2's exposure below the unfiltered 28% of defined bars: {v_(q['Q9'])} -- {100 * R['A2']['deployed']['exposure']:.2f}% vs {100 * BASE['deployed']['exposure']:.2f}% of "
          f"{BASE['deployed']['bars_defined']:,} defined bars")
    print(f"  Q10 the re-simulated A2 mean within 10 bp of the row-drop A2 mean: {v_(q['Q10'])} -- re-sim {p2['mean_bp']:+.2f} ({p2['trades']:,}) vs row-drop "
          f"{R['A2']['rowdrop']['per_trade']['mean_bp']:+.2f} ({R['A2']['rowdrop']['trades']:,}): {R['A2']['rowdrop']['diff_resim_minus_rowdrop_bp']:+.2f} bp")
    print(f"  check: the unfiltered ledger reproduces D361 ({idd['trades']:,}, {idd['mean_bp']:+.4f}) to 1e-9; the row-drop A5 on era 2 reproduces the export analysis "
          f"({rd['A5']['era2_trades']:,}, {rd['A5']['era2_mean_bp']:+.2f}) to 1e-9 against the export's columns; the five features equal the export's columns on all "
          f"{fe['events']:,} gated events: {v_(q['check'])}")
    for a in ARMS:
        drop_res(R[a])
    drop_res(BASE)
    out = dict(note="D362: the sink filter on the gated gap-up fade -- five entry-time conditions from the D361 export (thresholds fit on era 1, fixed in the pre-reg) applied "
                    "to the SIGNAL and re-simulated (A2 primary, A5, W sized 0.5^hits), the row-drop beside; DROP and FROT (the filter's nulls), the gate rotation, A' within "
                    "the gate and C; cost beside, deciding nothing (R15). Within-sample confirmation with nulls; the features were selected from ~40 on this sample. "
                    "Per-trade numbers are bp per TRADE (W per unit capital) and never compared to per-bar numbers. Nothing is a book; nothing promoted.",
               study=STUDY, cell=V61.cell_name(GATE, TRIG), cap=CAP, arms=list(ARMS), arm_index=ARM_INDEX, primary=PRIMARY, null_index=NULL,
               sinks=[dict(name=nm, feature=f, op=op, threshold=th) for nm, f, op, th in SINKS], sink_table=SK,
               features=dict(pcto="d361_export_trades.own_lagged (floored, deal-filtered, lagged one bar, the score's own warm-up) through V47.percentile_grid",
                             mkt_vol_20="sd (ddof = 1) of m_f over bars t-20..t-1 in bp, NaN where t-20 < m_start (the export's expression, repeated verbatim)",
                             nan="a NaN never hits", nan_counts_on_events=fe["nan_counts"], export_file=fe["file"]),
               W=dict(weight="0.5^hits at the event bar, attached to the position the kernel takes (equal-weight kernel untouched)",
                      deployed="sum_i w_i sgn (v_i - m) / sum_i w_i over open positions per bar; turnover = sum w over entries / mean sum w over open positions / bars",
                      per_trade="sum w pnl / sum w; t = mean / se, se = sqrt(sum w^2 (x - m)^2) / sum w; capital used = sum w / n", assert_W=wv),
               seeds=dict(DROP=[SEED, STUDY, "arm_index", NULL["DROP"], "part"], FROT=[SEED, STUDY, "arm_index", NULL["FROT"], "part"], ROT=[SEED, STUDY, "arm_index", NULL["ROT"], "part"],
                          A=[SEED, STUDY, "arm_index", NULL["A"], "part"], C=[SEED, STUDY, "arm_index", NULL["C"]]),
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), down_years=P["down_years"], floored_market_by_year=P["yr_ret"],
               ID=idd, FEAT=fe, HIT=ht, RD=rd, guard=guard_line(), base=BASE, results=R, predictions=q, prereg=PREREG)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['report']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--arm", choices=ARMS, help="the nulls for one arm: DROP / FROT (A2, A5), the gate rotation and A' (all)")
    ap.add_argument("--draws", type=int, default=100, help="A'-within-gate draws (pre-reg 100)")
    ap.add_argument("--draws-rot", type=int, default=None, help="DROP, FROT and gate-rotation draws (pre-reg 200; default --draws)")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; the smoke runs pass a temp/ directory)")
    a = ap.parse_args()
    print("D362  the sink filter on the gated gap-up fade -- five conditions from the trade export as a filter and as a sizer, re-simulated with their own nulls")
    paths = out_paths(a.out_dir)
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.arm:
        stage_arm(P, a.arm, a.draws, a.draws if a.draws_rot is None else a.draws_rot, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --arm A2|A5|W, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
