"""C1 STAGE 0 -- do BREADTH and DISPERSION forecast anything, before any gate is designed?

    uv run python scripts/c1_gate_stage0.py --selftest
    uv run python scripts/c1_gate_stage0.py

DESCRIPTIVE. No cell is scored, no book is built, no trade is simulated. It reads
forward returns -- a premise check must -- but it reads them as a COHORT DRIFT,
never as a strategy's P&L, exactly as D361's Stage 0 did.

WHY IT RUNS BEFORE ANY DESIGN. The principal's requirement is a FLAT-BY-DEFAULT
sleeve. D358 measured that a cross-sectional trigger cannot deliver one: a fresh
entry into the bottom 2% of ~1,000 names fires 5.2 times a bar, so a 40-bar hold
is 120 open positions on the average bar. Rarity says WHICH NAMES; it cannot say
WHEN. Flatness is a TIME-SERIES GATE, so under
docs/research/the-signal-hunt-part2.md section 2 a gate stops being one candidate
among eight and becomes a precondition for the other seven.

D361 rule 1, and the standing memory rule, both say the same thing: **a gate's
premise is the block correlation of its LEVEL with the target over the next
horizon, measured BEFORE the design is written. A split by era or year is not a
state.** This file measures that premise for the two states section 4.7 names and
nothing else.

THE TWO NEW STATES, declared before the run. Both are computed from the panel the
programme already owns, over the ELIGIBLE names only (D351), from the cross
section at t-1:

    BREADTH[t]     share of eligible names whose close at t-1 is above their OWN
                   trailing 50-bar mean, counted in each name's OWN bars
    DISPERSION[t]  the inter-quartile range, across eligible names at t-1, of the
                   21-bar return

Both are UNDEFINED on a bar carrying fewer than MIN_NAMES eligible names with a
finite value -- D373's `pct` convention, applied to a market-level statistic.

THE THRESHOLDS ARE DECLARED AND ARE NOT THE POINT. The premise is the LEVEL's
block correlation; the on/off drift split is reported beside it at a threshold
fixed before the run: BREADTH on when it is below 0.50 (fewer than half the
universe above its own mean -- a natural midpoint, not a fitted one) and
DISPERSION on when it is above its own TRAILING 252-bar median (causal: the value
at t reads dispersion strictly before t). No threshold here is searched, and if
this record ever becomes a gate the threshold is a design decision that must be
made in its own pre-registration.

G1 AND G2 ARE RECOMPUTED HERE AS THE REFERENCE FRAME, and that is what makes the
new numbers readable: a correlation of -0.2 means nothing until it sits beside
the two states this programme already measured. [REG] asserts that this file's
INDEPENDENT block-correlation implementation reproduces D361's published
G1/bottom_10 numbers -- corr, block count and shuffle p95 -- from
data/d361_stage0.json, to 0.0, before any new gate is read.

THREE TARGETS, not one. D361 correlated its gate against the loser cohort because
that was its hypothesis. These gates are meant to serve EVERY candidate in the
record, so the level is correlated against the forward-20 hedged drift of the
loser cohort (comparable to D361), the WINNER cohort (where A1 and D373 live) and
all eligible names (the base rate).

ASSERTIONS
  [REG] the block correlation reproduces D361's published G1 and G2 numbers
        exactly, from their own artifact and their own recorded shuffle seed.
  [L]   the level at t is unchanged when every bar from t onward is deleted --
        a causality audit by a SECOND implementation that rebuilds the level from
        a truncated panel and never calls the vectorised one.
  [E]   breadth and dispersion are computed over ELIGIBLE names only, and the
        count entering each bar is reported (D351).
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on a level that reads bar t. A self-test that cannot
        fail is worse than none.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "c1_gate_stage0.json"
D361_JSON = REPO / "data" / "d361_stage0.json"

MA_BARS = 50            # breadth: each name against its OWN trailing 50-bar mean
RET_BARS = 21           # dispersion: the cross-sectional IQR of the 21-bar return
MED_BARS = 252          # dispersion's threshold: its own trailing median, causal
MIN_NAMES = 50          # a bar with fewer eligible finite names carries no state
BREADTH_ON = 0.50       # declared, not fitted
TARGETS = ("bottom_10", "top_10", "elig_all")
SEED = 20260907


# ------------------------------------------------------- the two new state levels
def above_own_mean(closes_nT, live_nT, w=MA_BARS):
    """(n, T) bool-as-float: is the close above the name's OWN trailing w-bar mean?

    NaN before the name's own w-th bar. Computed on each symbol's OWN bars and
    scattered back, `signals_ragged`'s rule -- a contiguous slice would misalign
    every value after an internal hole. The mean is a direct windowed sum, not a
    difference of cumulative sums: A1's Stage 0 caught that reordering breaking an
    invariant at 3e-12 and the lesson transfers unchanged."""
    n, T = closes_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size < w:
            continue
        c = closes_nT[i, at]
        mean = np.lib.stride_tricks.sliding_window_view(c, w).mean(axis=-1)   # ends at own bar w-1 ..
        out[i, at[w - 1:]] = (c[w - 1:] > mean).astype(float)
    return out


def trailing_return(closes_nT, live_nT, w=RET_BARS):
    """(n, T) the w-bar return on the name's OWN bars, NaN before its own w-th bar."""
    n, T = closes_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size <= w:
            continue
        c = closes_nT[i, at]
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i, at[w:]] = np.where(c[:-w] > 0, c[w:] / c[:-w] - 1.0, np.nan)
    return out


def cross_state(grid_nT, eligT_Tn, how):
    """The market-level state from the cross section, per bar: (value, count).

    `grid_nT` is (n, T); `eligT_Tn` is (T, n). The value at column t is computed
    from column t and is LAGGED by the caller -- keeping the lag in one place is
    the whole of D279's lesson (a lagged position built from an unlagged ranking
    is still look-ahead, and the base being correctly lagged is what hides it)."""
    n, T = grid_nT.shape
    val = np.full(T, np.nan)
    cnt = np.zeros(T, dtype=int)
    for t in range(T):
        v = grid_nT[eligT_Tn[t], t]
        v = v[np.isfinite(v)]
        cnt[t] = v.size
        if v.size < MIN_NAMES:
            continue
        val[t] = v.mean() if how == "mean" else float(np.subtract(*np.percentile(v, [75, 25])))
    return val, cnt


def state_pack(name, raw, cnt, T, dates, years, gate_rule):
    """A D361 `gate_pack`-shaped dict from a raw per-bar statistic.

    THE LAG LIVES HERE AND NOWHERE ELSE: level[t] = raw[t-1]. Every consumer takes
    `level` and `gate`, so no downstream code can forget it."""
    level = np.full(T, np.nan)
    level[1:] = raw[:-1]
    ok = np.isfinite(level)
    assert ok.any(), f"{name}: never defined"
    d0 = int(np.flatnonzero(ok)[0])
    # the state must be defined CONTIGUOUSLY from d0; a hole would silently change
    # the block grid and make the correlation a different object than D361's
    assert ok[d0:].all(), f"{name}: undefined bars after d0 ({int((~ok[d0:]).sum())})"
    gate = np.zeros(T, bool)
    gate[d0:] = gate_rule(level[d0:])
    defined = np.zeros(T, bool)
    defined[d0:] = True
    eps = V61.episodes_of(gate)
    return dict(name=name, w=None, d0=d0, Td=int(T - d0), gate=gate, defined=defined, level=level,
                on=int(gate.sum()), on_share=float(gate[defined].mean()), episodes=eps,
                runs=[e - s + 1 for s, e in eps], names_per_bar=cnt,
                dates=[(dates[s], dates[e]) for s, e in eps],
                years=[sorted(set(int(y) for y in np.asarray(years)[s:e + 1])) for s, e in eps])


def trailing_median_rule(level, w=MED_BARS):
    """DISPERSION is 'on' when it exceeds its OWN trailing w-bar median -- causal:
    the comparison at t reads only bars strictly before t. Undefined (False) until
    w prior values exist, which costs the first w bars of the state and no more."""
    m = np.full(level.size, np.nan)
    if level.size > w:
        W = np.lib.stride_tricks.sliding_window_view(level[:-1], w)          # ends at t-1
        m[w:] = np.median(W, axis=-1)
    return np.where(np.isfinite(m), level > m, False)


# --------------------------------------------------------------- the block premise
def block_corr(level, group_Tn, F, d0, T, seed, horizon):
    """D361's premise statistic, INDEPENDENTLY implemented so [REG] means something.

    x = the state's level at the start of each non-overlapping `horizon`-bar block
    from d0; y = the mean forward-`horizon` hedged drift over the group's names at
    that block start. Blocks with no group name are skipped and counted."""
    xs, ys, empty = [], [], 0
    for b in range(d0, T - horizon + 1, horizon):
        row = group_Tn[b]
        if not row.any():
            empty += 1
            continue
        xs.append(level[b])
        ys.append(float(F[b][row].mean()))
    x, y = np.array(xs), np.array(ys)
    nb = x.size
    assert nb >= 10 and np.isfinite(x).all() and np.isfinite(y).all(), \
        f"[D] too few blocks ({nb}) or an undefined block level"
    r = float(np.corrcoef(x, y)[0, 1])
    rng = np.random.default_rng(seed)
    r_sh = float(np.corrcoef(x[rng.permutation(nb)], y)[0, 1])
    se = 1.0 / np.sqrt(nb - 1.0)
    more = np.array([np.corrcoef(x[rng.permutation(nb)], y)[0, 1] for _ in range(999)])
    return dict(n_blocks=nb, empty_blocks=empty, horizon=horizon, corr=r, corr_shuffled=r_sh,
                se=se, z_shuffled=r_sh / se, shuffle_seed=list(seed) if isinstance(seed, list) else seed,
                shuffle_p50=float(np.median(more)), shuffle_p95=float(np.quantile(np.abs(more), .95)),
                x_mean=float(x.mean()), y_mean_bp=float(y.mean()) * 1e4,
                decisive=bool(abs(r) > float(np.quantile(np.abs(more), .95))))


# ---------------------------------------------------------------------- self-test
def selftest() -> int:
    print("C1 STAGE 0 SELF-TEST -- the lag, the windows, and a break that must be caught\n")
    T = 40
    raw = np.arange(T, dtype=float)
    years = [2020] * T
    dates = [f"2020-01-{i + 1:02d}" for i in range(T)]
    cnt = np.full(T, 100)
    gp = state_pack("PROBE", raw, cnt, T, dates, years, lambda lv: lv > 20.0)
    assert gp["level"][5] == raw[4], "[L] level[t] must be raw[t-1]"
    assert np.isnan(gp["level"][0]), "[L] level[0] must be undefined"
    print(f"    [L] level[t] == raw[t-1] on all {T - 1} lagged bars; level[0] undefined")

    # [X] a level that reads bar t must be CAUGHT by the same check
    bad = np.full(T, np.nan)
    bad[:] = raw                                                    # unlagged
    raised = False
    try:
        assert bad[5] == raw[4], "unlagged level must not pass the lag audit"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- an unlagged level passed the lag audit"
    print(f"    [X] an UNLAGGED level reads {bad[5]:.0f} where {raw[4]:.0f} is required and IS CAUGHT")

    # own-bar windows on a holed name
    live = np.ones((1, 60), dtype=bool)
    live[0, 10:20] = False
    c = np.full((1, 60), np.nan)
    at = np.flatnonzero(live[0])
    c[0, at] = np.linspace(10.0, 60.0, at.size)
    # THE WINDOW MUST STRADDLE THE HOLE OR THE CHECK IS VACUOUS. The first version
    # used w=5 on a hole at columns 10..19 and printed "column 4, not column 4":
    # the warm-up ended before the hole began, so it proved nothing. w=12 puts the
    # first defined bar past the hole, where a column-counted window would differ.
    w_ = 12
    assert at[w_ - 1] != w_ - 1, "[W] the probe window does not straddle the hole"
    am = above_own_mean(c, live, w=w_)
    assert np.isnan(am[0, at[:w_ - 1]]).all() and np.isfinite(am[0, at[w_ - 1]]), \
        "[W] the trailing mean is being counted in columns, not in the name's own bars"
    assert np.isnan(am[0, w_ - 1]), "[W] a column-counted window would have defined this bar"
    assert (am[0, at[w_ - 1:]] == 1.0).all(), "a rising series is above its own trailing mean"
    print(f"    [W] holed name: first defined bar is its OWN {w_}th -- column {at[w_ - 1]}, "
          f"NOT column {w_ - 1} (which is undefined, as a column-counted window would not be)")
    tr = trailing_return(c, live, w=w_)
    assert np.isnan(tr[0, at[:w_]]).all() and np.isfinite(tr[0, at[w_]]), "[W] trailing_return warm-up"
    assert np.isnan(tr[0, w_]), "[W] trailing_return is counting columns"
    print(f"    [W] trailing_return warm-up counted in own bars too -- column {at[w_]}, not {w_}")

    # the causal trailing median never reads its own bar
    lv = np.arange(300, dtype=float)
    g = trailing_median_rule(lv, w=10)
    assert not g[:10].any(), "the trailing median must be undefined for its first w bars"
    assert g[10:].all(), "a rising series is above its own trailing median everywhere after warm-up"
    lv2 = lv.copy()
    lv2[200:] = -1.0                                                # the future turns down
    g2 = trailing_median_rule(lv2, w=10)
    assert np.array_equal(g[:200], g2[:200]), "[L] the trailing median read the future"
    print("    [L] trailing median: changing every bar from 200 onward leaves bars 0..199 identical")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    selftest()

    t0 = time.time()
    P = PREP.prep(need_grids=False)
    T, n = P["T"], P["n"]
    elig = np.asarray(P["elig"])                                    # (T, n)
    eligT = elig.T                                                  # (n, T)
    closes = np.ascontiguousarray(np.asarray(P["CLOSE"]).T)
    dates, years = P["dates"], P["years"]
    H = V61.HORIZON
    print(f"  prep in {time.time() - t0:.0f}s | {n} names x {T} bars | horizon {H}", flush=True)

    F = V61.forward20(P)
    groups = V61.stage0_groups(P)
    print(f"  forward-{H} hedged drift grid and the three target groups built "
          f"({', '.join(f'{k} {int(v.sum()):,}' for k, v in groups.items())})", flush=True)

    # ---- [REG] reproduce D361's published premise with THIS file's own block code
    d361 = json.loads(D361_JSON.read_text())
    reg = {}
    for g in ("G1", "G2"):
        gp = V61.gate_pack(P, g)
        pub = d361["gates"][g]["block"]
        got = block_corr(gp["level"], groups["bottom_10"], F, gp["d0"], T, pub["shuffle_seed"], H)
        for k in ("n_blocks", "empty_blocks", "corr", "corr_shuffled", "shuffle_p50", "shuffle_p95"):
            assert (got[k] == pub[k]) if isinstance(pub[k], int) else abs(got[k] - pub[k]) < 1e-12, \
                f"[REG] {g}.{k}: {got[k]!r} != D361's {pub[k]!r}"
        reg[g] = {"published_corr": pub["corr"], "recomputed_corr": got["corr"],
                  "n_blocks": got["n_blocks"], "shuffle_p95": got["shuffle_p95"]}
        print(f"    [REG] {g}: this file's block correlation reproduces D361's published "
              f"{pub['corr']:+.5f} on {pub['n_blocks']} blocks to 0.0", flush=True)

    # ---- the two new states -------------------------------------------------
    t = time.time()
    am = above_own_mean(closes, P["live"])
    br_raw, br_cnt = cross_state(am, elig, "mean")
    tr = trailing_return(closes, P["live"])
    dp_raw, dp_cnt = cross_state(tr, elig, "iqr")
    print(f"  breadth and dispersion built in {time.time() - t:.0f}s", flush=True)

    PACKS = {"G1": V61.gate_pack(P, "G1"), "G2": V61.gate_pack(P, "G2"),
             "BREADTH": state_pack("BREADTH", br_raw, br_cnt, T, dates, years,
                                   lambda lv: lv < BREADTH_ON),
             "DISPERSION": state_pack("DISPERSION", dp_raw, dp_cnt, T, dates, years,
                                      trailing_median_rule)}

    # ---- [E] how many eligible names carry each state ----------------------
    e_rep = {}
    for name, cnt in (("BREADTH", br_cnt), ("DISPERSION", dp_cnt)):
        gp = PACKS[name]
        c = cnt[gp["defined"]]
        e_rep[name] = {"min": int(c.min()), "median": float(np.median(c)), "max": int(c.max()),
                       "bars_below_min_names": int((cnt < MIN_NAMES).sum())}
        print(f"    [E] {name}: eligible names per defined bar min {c.min()}, median "
              f"{np.median(c):.0f}, max {c.max()}; {int((cnt < MIN_NAMES).sum()):,} bars carried "
              f"fewer than {MIN_NAMES} and are undefined", flush=True)

    # ---- [L] causality, by a second implementation that truncates the panel --
    rng = np.random.default_rng(SEED)
    for name, grid, how in (("BREADTH", am, "mean"), ("DISPERSION", tr, "iqr")):
        gp = PACKS[name]
        probe = rng.choice(np.flatnonzero(gp["defined"])[10:], size=6, replace=False)
        for tb in probe:
            cl2 = closes.copy()
            lv2 = P["live"].copy()
            cl2[:, tb:] = np.nan                                    # delete bar tb onward
            lv2[:, tb:] = False
            g2 = above_own_mean(cl2, lv2) if name == "BREADTH" else trailing_return(cl2, lv2)
            raw2, _ = cross_state(g2, elig & (np.arange(T) < tb)[:, None], how)
            got, want = raw2[tb - 1], (br_raw if name == "BREADTH" else dp_raw)[tb - 1]
            assert (np.isnan(got) and np.isnan(want)) or got == want, \
                f"[L] {name}: level at {tb} changed when the future was deleted ({got} != {want})"
        print(f"    [L] {name}: level unchanged on {probe.size} sampled bars when every bar from "
              f"t onward is deleted -- rebuilt by a second path, not the vectorised one", flush=True)

    # ---- the premise, per state, per target --------------------------------
    res = {}
    for name, gp in PACKS.items():
        gate, d = gp["gate"], gp["defined"]
        on, off = (gate & d)[:, None], (~gate & d)[:, None]
        drift = {}
        for g, m in groups.items():
            drift[g] = {lab: V61.cond_drift(F, m & cm)
                        for lab, cm in (("on", on), ("off", off), ("all", d[:, None]))}
        blocks = {g: block_corr(gp["level"], groups[g], F, gp["d0"], T, [SEED, 0, i], H)
                  for i, g in enumerate(TARGETS)}
        res[name] = dict(drift=drift, blocks=blocks, on_share=gp["on_share"], on=gp["on"],
                         Td=gp["Td"], d0=gp["d0"], d0_date=dates[gp["d0"]],
                         episodes=len(gp["episodes"]),
                         run_median=float(np.median(gp["runs"])) if gp["runs"] else None,
                         run_max=max(gp["runs"]) if gp["runs"] else None)

    # ---- ADDED AFTER SEEING THE BLOCK TABLE, AND DISCLOSED AS SUCH ----------
    # Two states can both be decisive and be the SAME state wearing two names --
    # the defect section 3a of the record names, and the question D362 left unrun
    # ("which of the two is the state variable"). Without this the block table
    # cannot be read: a decisive DISPERSION is either a new gate or G1 restated.
    # Spearman on the LEVELS over the bars where both are defined; ON-SHARE
    # overlap (Jaccard) on the booleans beside it, because two levels can rank
    # alike and still gate different bars.
    keys = list(PACKS)
    both = np.ones(T, bool)
    for k in keys:
        both &= PACKS[k]["defined"] & np.isfinite(PACKS[k]["level"])
    rk = {k: np.argsort(np.argsort(PACKS[k]["level"][both])) / max(1, int(both.sum()) - 1) for k in keys}
    Lm = np.corrcoef(np.vstack([rk[k] for k in keys]))
    Jm = np.zeros((len(keys), len(keys)))
    for i, ka in enumerate(keys):
        for j, kb in enumerate(keys):
            a_, b_ = PACKS[ka]["gate"] & both, PACKS[kb]["gate"] & both
            u = (a_ | b_).sum()
            Jm[i, j] = float((a_ & b_).sum() / u) if u else np.nan
    overlap = {"bars": int(both.sum()), "states": keys,
               "level_spearman": Lm.tolist(), "gate_jaccard": Jm.tolist(),
               "disclosed": "computed AFTER the block table was read, to decide whether a "
                            "decisive state is a NEW state or an incumbent restated"}

    # ---- [P] PERSIST BEFORE RENDERING --------------------------------------
    payload = {
        "purpose": "C1 Stage 0: the PREMISE of two candidate market states, measured before any "
                   "gate is designed (D361 rule 1). Descriptive; no cell scored, no book built.",
        "bar_committed_in": "docs/research/the-signal-hunt-part2.md sections 4.7 and 8, commit "
                            "ed967bd, before this runner existed (R8)",
        "states": {"BREADTH": f"share of eligible names with close[t-1] above their own trailing "
                              f"{MA_BARS}-bar mean; gate on below {BREADTH_ON}",
                   "DISPERSION": f"cross-sectional IQR of the {RET_BARS}-bar return at t-1; gate on "
                                 f"above its own trailing {MED_BARS}-bar median (causal)",
                   "G1": "D361: 63-bar trailing compounded return of the floored market < 0",
                   "G2": "D361: index[t-1] < mean(index[t-200..t-1])"},
        "horizon": H, "min_names": MIN_NAMES, "targets": list(TARGETS), "seed": SEED,
        "regression_against_d361": reg, "eligible_names_per_bar": e_rep, "result": res,
        "state_overlap": overlap,
    }
    OUT.write_text(json.dumps(V61.clean(payload) if hasattr(V61, "clean") else payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render -------------------------------------------------------------
    print(f"\nTHE PREMISE -- block correlation of the state's LEVEL at the start of each "
          f"non-overlapping {H}-bar block against that group's mean forward-{H} hedged drift.")
    print("A state that forecasts has |corr| above its own shuffled |r| p95. 'decisive' is that test.\n")
    print(f"  {'state':<11s} {'target':<11s} {'blocks':>7s} {'corr':>8s} {'shuf p95':>9s} "
          f"{'y mean bp':>10s}  decisive")
    for name in PACKS:
        for g in TARGETS:
            b = res[name]["blocks"][g]
            print(f"  {name:<11s} {g:<11s} {b['n_blocks']:>7d} {b['corr']:>+8.3f} "
                  f"{b['shuffle_p95']:>9.3f} {b['y_mean_bp']:>10.1f}  "
                  f"{'YES' if b['decisive'] else 'no'}")

    print(f"\nTHE CONDITIONAL DRIFT beside it -- forward-{H} hedged drift, bp per name-bar, "
          f"at the declared threshold (reported, NOT the premise test)\n")
    print(f"  {'state':<11s} {'on%':>6s} {'eps':>5s} {'runmed':>7s} | "
          + " | ".join(f"{g} on/off" for g in TARGETS))
    for name in PACKS:
        r = res[name]
        cells = []
        for g in TARGETS:
            d_ = r["drift"][g]
            cells.append(f"{(d_['on']['bp'] or float('nan')):+7.1f}/{(d_['off']['bp'] or float('nan')):+7.1f}")
        print(f"  {name:<11s} {100 * r['on_share']:>5.1f}% {r['episodes']:>5d} "
              f"{(r['run_median'] or 0):>7.1f} | " + " | ".join(cells))

    print(f"\nARE THESE FOUR STATES DISTINCT? Spearman of the LEVELS over the {overlap['bars']:,} "
          f"bars where all four are defined,\nwith the share of gated bars they agree on (Jaccard) "
          f"beside it. COMPUTED AFTER the block table was read, and disclosed.\n")
    print("  " + " " * 12 + " ".join(f"{k[:10]:>11s}" for k in keys) + "   |  Jaccard of the ON bars")
    for i, k in enumerate(keys):
        print(f"  {k:<12s}" + " ".join(f"{Lm[i, j]:>11.3f}" for j in range(len(keys)))
              + "   |  " + " ".join(f"{Jm[i, j]:>5.2f}" for j in range(len(keys))))

    print("\n  Read the LEFT table, not the right one. The conditional split is what an era or "
          "year split also produces;")
    print("  the block correlation against its own shuffle is what separates a STATE from a "
          "coincidence (D361 rule 1).")
    print("\nThis measurement admits nothing and designs nothing. A decisive premise makes a state "
          "worth GATING WITH; it is not a signal (R15).")
    return 0


PREP = _load("d348p", "d348_prep.py")
V61 = _load("d361r", "run_d361_regime_gated_short.py")
V59 = V61.V59

if __name__ == "__main__":
    raise SystemExit(main())
