"""D359 -- the bear-market rally short: a fresh rev_5 spike INSIDE the loser cohort of mom_252_21, entered short.

    uv run python scripts/run_d359_loser_rally_short.py --selftest
    uv run python scripts/run_d359_loser_rally_short.py --stage0                                   the premise: the cohort's own drift
    uv run python scripts/run_d359_loser_rally_short.py --cell 10:90 --draws 100 --part 1          A', B and B_c for one cell (one process per cell)
    uv run python scripts/run_d359_loser_rally_short.py --report
    --out-dir DIR   (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)

Pre-registration: docs/decisions/D359-the-bear-market-rally-short-a-spike-inside-the-loser-cohort.md

The signal, on the lagged floored deal-filtered warm-based cross-sectional percentiles at t-1 (pct_mom of mom_252_21, high = winner;
pct_rev of rev_5), on eligible bars:
    cell (c, s):        pct_mom <= c  &  pct_rev >= s  &  pct_rev[t-1] < s        -> SHORT at the next open, every event, no slot cap
    complement (c, s):  pct_mom >  c  &  the same spike                             -> short, beside (cell u complement == the spike, disjoint)
    mirror (c, s):      pct_mom >= 100-c  &  pct_rev <= 100-s  &  pct_rev[t-1] > 100-s -> LONG, beside
Cells (10,90) PRIMARY, (10,95), (20,90), (20,95). Exits: cap 10 (PRIMARY), invalidation (pct_rev <= 50 for the short; the kernel's own
rule, side-aware) capped at 10 by the kernel's cap argument, cap 40 beside for D352. Hedged by the floored universe (A3: mkt = m_f).

Stage 0 (the premise): the mean next-bar hedged return r1T[t] - m_f[t] over eligible name-bars with pct_mom[t] <= c, its complement and
the top decile (pct_mom >= 90), in bp per bar, over the span, by era half, by year and the down-years; [D] against an independent
np.where + nanmean.

Nulls on the primary exit per cell: A' (per-name rotation within elig, the score rotated with the signal), B (same day, same rsi bucket,
random eligible name with a defined rsi percentile), B_c (same day, random eligible name in the SAME COHORT pct_mom <= c that is not an
event name; shortfall kept and counted), C (1,000 sign flips on the ledger). Per draw: trade mean, trades, deployed net PUB bp/bar and
Sharpe, gross (hedged deployed base, G22.costed as D358).

Cost per trade: 2c (V47.two_c) PUB and PB, D337's gc_htb borrow per trade (V49.borrow_of), the HTB share, net = mean - 2c - borrow, the
breakeven half-spread after commission and borrow. Deployed base beside: G22.costed's 4-crossing line and the 2-crossing line
(rt = 2 hs, rtc = 2 x commission: cost / 2 exactly, asserted).

Everything shared is imported, not copied: d348_prep (FIRST: installs memo_load), run_d350 (lagged, four_groups, clean), run_d353
(b_pool_P, b_shortfall, recompute_trade, assert_series_defs, _dist), run_d349 (borrow_of, check_borrow, event_buckets,
event_accounting), run_d358 (pct_of, raw_floored, pct_direct, costed, deployed_block, deployed_subsets, rebuild, assert_HX, subledger,
control_C, null_stats, observed_stats, assert_B).

ASSERTIONS [K][F0][R][G][E][D][SB][S][A'][B][B_c][C][HX][6] -- pre-reg section 8.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PREP = _load("d348p", "d348_prep.py")                       # installs memo_load; the alias chain executes once
V50 = _load("d350r", "run_d350_long_timing_screen.py")      # lagged, four_groups, clean (its _load("d348p") is memoised)
V53 = _load("d353r", "run_d353_rev5_record.py")             # b_pool_P, b_shortfall, recompute_trade, assert_series_defs, _dist
V49 = _load("d349r", "run_d349_short_signal_controls.py")   # the SHORT conventions: borrow_of, check_borrow, event_buckets, event_accounting
V58 = _load("d358r", "run_d358_flat_sleeve.py")             # the event / deployed-base helpers
V47 = PREP.V47
EB, G22, UF, BR = PREP.EB, PREP.G22, PREP.UF, PREP.BR
SEED, X_TARGET = V47.SEED, V47.X_TARGET
CONVS = V47.CONVS
STUDY = 359
MOM, REV = "mom_252_21", "rev_5"
CELLS = [(10, 90), (10, 95), (20, 90), (20, 95)]           # index 0..3 fixes the RNG keys
PRIMARY = (10, 90)
EXITS = (("cap", 10), ("invalidation", 10), ("cap", 40))
EXIT_NAME = {("cap", 10): "cap10", ("invalidation", 10): "inv10", ("cap", 40): "cap40"}
PRIMARY_EXIT = "cap10"
TOP_DECILE = 90.0
U_SLOTS = 4
ANN = 252.0
PER_SHARE, BORROW_SCHEME = V49.PER_SHARE, V49.BORROW_SCHEME
ARM = dict(A=1, B=2, Bc=3, C=4)                              # seed arms: A' 1, B 2, B_c 3 (as tasked); C takes 4 (D358 used 3 for C; B_c is new)
D352_SCREEN = REPO / "data" / "d352_screen.json"
D352_REPORT = REPO / "data" / "d352_short_timing_screen.json"
# D352 stored rev_5/S10 ONLY as a stage-1 grid row (it was not a gate survivor, so its kernel was never run): n_events_raw is the event
# count of the (., 90) spike with the cohort dropped; E_bp is mean(-F) over its events with finite F (F = the cached forward-40 hedged
# excess grid). The kernel cap-40 short mean is reproduced against a survivor D352 DID run (retrace_leg/S10), the same code path.
D352_REV5_S10 = dict(n_events_raw=73_109, n_events=71_982, n_nan_F=1_127, E_bp=-21.898981896631962)
D352_KERNEL_REF = "retrace_leg/S10"
DATA = REPO / "data"
SELFTEST_TMP = REPO / "temp" / "d359_selftest"
pct_of, raw_floored, pct_direct = V58.pct_of, V58.raw_floored, V58.pct_direct
costed, deployed_subsets, rebuild, assert_HX, subledger = V58.costed, V58.deployed_subsets, V58.rebuild, V58.assert_HX, V58.subledger
control_C, null_stats, observed_stats, assert_B = V58.control_C, V58.null_stats, V58.observed_stats, V58.assert_B
clean = V50.clean


def cell_name(c, s):
    return f"{c}:{s}"


def zeros(x):
    return np.zeros_like(x)


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, stage0=d / "d359_stage0.json", ctrl=str(d / "d359_ctrl_{c}_{s}_p{part}.json"), report=d / "d359_loser_rally_short.json")


# ------------------------------------------------------------------ the signal
_G = {}


def grids(P):
    """(pct_mom, pct_rev, prev_rev, elig): the two lagged floored percentile grids (the value at t uses information to t-1), the
    previous bar's pct_rev, the eligible set. Memoised."""
    if "g" not in _G:
        pct_mom = pct_of(P, MOM)
        pct_rev = pct_of(P, REV)
        prev = np.full_like(pct_rev, np.nan)
        prev[1:] = pct_rev[:-1]
        _G["g"] = (pct_mom, pct_rev, prev, np.asarray(P["elig"]))
    return _G["g"]


def spike(P, s):
    """The unconditioned fresh entry of rev_5 into the top (100 - s)%: pct_rev >= s and pct_rev[t-1] < s, eligible. D352's S10 at s = 90."""
    _pm, pct_rev, prev, elig = grids(P)
    with np.errstate(invalid="ignore"):
        return (pct_rev >= float(s)) & (prev < float(s)) & elig


def cohort(P, c):
    """The loser cohort on eligible bars: pct_mom <= c."""
    pct_mom, _pr, _pv, elig = grids(P)
    with np.errstate(invalid="ignore"):
        return (pct_mom <= float(c)) & elig


def cell_signal(P, c, s):
    """sh[t, i] for cell (c, s): the spike inside the cohort, entered SHORT."""
    return np.ascontiguousarray(spike(P, s) & cohort(P, c))


def complement_signal(P, c, s):
    """The same spike with pct_mom > c, short."""
    pct_mom = grids(P)[0]
    with np.errstate(invalid="ignore"):
        return np.ascontiguousarray(spike(P, s) & (pct_mom > float(c)))


def mirror_signal(P, c, s):
    """The winners' fresh dip: pct_mom >= 100 - c, pct_rev <= 100 - s and pct_rev[t-1] > 100 - s, eligible; entered LONG."""
    pct_mom, pct_rev, prev, elig = grids(P)
    with np.errstate(invalid="ignore"):
        return np.ascontiguousarray((pct_mom >= 100.0 - c) & (pct_rev <= 100.0 - s) & (prev > 100.0 - s) & elig)


def assert_partition(sh, comp, sp, tag="[G]"):
    """The cell and its complement partition the unconditioned spike."""
    assert not (sh & comp).any(), f"{tag} the cell and its complement overlap"
    assert np.array_equal(sh | comp, sp), f"{tag} cell u complement != the unconditioned spike"
    assert not (sh & ~sp).any() and not (comp & ~sp).any(), f"{tag} an event outside the spike"


# ------------------------------------------------------------------ the kernel
def simulate(P, sig, score, exit_, cap, side, A3=None):
    """D345's kernel, every event taken (n_max=None), hedged series on. side 1: fed (zeros, sig) -- the SHORT; side 0: (sig, zeros).
    The invalidation exit reads score_T side-aware: a short exits when score <= 50, a long when score >= 50 (EB.simulate_event step 1);
    `cap` bounds the hold under every exit (cap_hit = age >= cap is OR'd with the trigger), so invalidation capped at 10 is the kernel's
    own mechanism, never a truncated ledger."""
    z = zeros(sig)
    sl, ss = (z, sig) if side == 1 else (sig, z)
    return EB.simulate_event(P["A3"] if A3 is None else A3, sl, ss, score, exit=exit_, cap=cap, n_max=None, x_target=X_TARGET,
                             U=U_SLOTS, hedged_series=True)


def run_short(P, sh, sc, exit_, cap, A3=None):
    return simulate(P, sh, sc, exit_, cap, 1, A3)


def run_mirror(P, lo, sc, exit_, cap, A3=None):
    return simulate(P, lo, sc, exit_, cap, 0, A3)


def two_crossing(d):
    """The 2-crossing cost line beside G22.costed's 4-crossing line: rt = 2 hs and rtc = 2 x commission instead of 4 and 4, at the same
    turnover -- which is cost_bp / 2 exactly (asserted). Breakeven half-spread: gross / turnover - 2 x commission, over 2."""
    hs, px, turn, g, v = d["held_half_spread"], d["held_price"], d["turnover"], d["gross_bp"], d["vol_bp"]
    rtc2 = 2.0 * PER_SHARE / px * 1e4
    cost2 = (2.0 * hs + rtc2) * turn
    assert abs(cost2 - d["cost_bp"] / 2.0) < 1e-9, f"2-crossing cost {cost2} != cost_bp / 2 {d['cost_bp'] / 2.0}"
    net2 = g - cost2
    return dict(crossings=2, round_trip=2.0 * hs, commission_rt=rtc2, cost_bp=cost2, net_bp=net2,
                sharpe_net=net2 / v * np.sqrt(ANN) if v > 0 else 0.0,
                breakeven_half_spread_bp_side=(g / turn - rtc2) / 2.0 if turn > 0 else None)


def deployed_block(res, P):
    """D358's deployed block (hedged and unhedged, both conventions, 4 crossings; the U=4 total beside) plus the 2-crossing line."""
    out = V58.deployed_block(res, P)
    for cv in CONVS:
        out[cv]["hedged_2x"] = two_crossing(out[cv]["hedged"])
        out[cv]["unhedged_2x"] = two_crossing(out[cv]["unhedged"])
    return out


def trade_block(P, res, elig, side, with_groups):
    """Per-trade statistics in bp per TRADE (never compared to the per-bar numbers); for the short, D337's borrow in the net."""
    tr = res["trades"]
    assert tr and all(t[4] == side for t in tr), "trade_block: a trade on the wrong side"
    pnl = V47.pnl_bp(res)
    T = P["T"]
    half = T // 2
    years = np.asarray(P["years"])
    yrs = np.array([years[t[1]] for t in tr])
    era1 = np.array([t[1] < half for t in tr])
    down = np.isin(yrs, list(P["down_years"]))
    c2 = {cv: V47.two_c(tr, P["HALF"][cv], P["CLOSE"]) for cv in CONVS}
    mean = float(pnl.mean())
    ages = np.array([t[2] for t in tr], float)
    hold = float(ages.mean())
    px = c2["PUB"][2]
    comm = 2.0 * PER_SHARE / px * 1e4                                  # the commission half of 2c, bp per trade (D352's convention)
    d_ = dict(side="short" if side == 1 else "long", trades=len(tr), mean_bp=mean, median_bp=float(np.median(pnl)),
              t=float(mean / (pnl.std(ddof=1) / np.sqrt(pnl.size))) if pnl.size > 1 else None,
              share_pos=float((pnl > 0).mean()), hold_mean=hold, hold_median=float(np.median(ages)),
              mean_per_bar_held_bp=mean / hold, two_c={cv: c2[cv][0] for cv in CONVS}, held_half={cv: c2[cv][1] for cv in CONVS},
              held_price=px, commission_bp=comm, net_per_trade={cv: mean - c2[cv][0] for cv in CONVS},
              mean_over_2c={cv: mean / c2[cv][0] for cv in CONVS},
              era1_mean_bp=float(pnl[era1].mean()) if era1.any() else None, era2_mean_bp=float(pnl[~era1].mean()) if (~era1).any() else None,
              era1_n=int(era1.sum()), era2_n=int((~era1).sum()),
              down_years_mean_bp=float(pnl[down].mean()) if down.any() else None, down_years_n=int(down.sum()),
              by_year={int(y): dict(n=int((yrs == y).sum()), mean_bp=float(pnl[yrs == y].mean())) for y in np.unique(yrs)})
    if side == 1:
        pt, htb, _rate = V49.borrow_of(P, tr)
        bm = float(pt.mean())
        d_["borrow"] = dict(scheme=BORROW_SCHEME, mean_bp=bm, median_bp=float(np.median(pt)), htb_share=float(htb.mean()), htb_n=int(htb.sum()),
                            gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB)
        d_["net_per_trade_borrow"] = {cv: mean - c2[cv][0] - bm for cv in CONVS}
        d_["breakeven_half_spread_bp_side"] = (mean - bm - comm) / 2.0
    else:
        d_["breakeven_half_spread_bp_side"] = (mean - comm) / 2.0
    if with_groups:
        d_["four_groups"] = V50.four_groups(tr, pnl, P, elig)
    return d_


# ------------------------------------------------------------------ Stage 0: the premise
def stage0_masks(P):
    """ex[t, i] = r1T[t] - m_f[t] (close(t-1) -> close(t), hedged by the floored market that A3 hands the kernel as `mkt` and that
    D358's rebuild uses on every held bar after the entry bar); pct_mom[t] is lagged, so the pair is the NEXT-bar drift. P['mkt'] is
    the panel-wide market (D345's kernel input) and is not the hedge these trades are scored against. The base set is eligible
    name-bars with finite r1T and m_f."""
    pct_mom, _pr, _pv, elig = grids(P)
    r1T, m_f = np.asarray(P["r1T"]), np.asarray(P["m_f"])
    ok = elig & np.isfinite(r1T) & np.isfinite(m_f)[:, None]
    ex = r1T - m_f[:, None]
    groups = {"elig_all": ok}
    with np.errstate(invalid="ignore"):
        for c in (10, 20):
            groups[f"bottom_{c}"] = ok & (pct_mom <= float(c))
            groups[f"above_{c}"] = ok & (pct_mom > float(c))
        groups["top_10"] = ok & (pct_mom >= TOP_DECILE)
    return ex, groups


def stage0_subsets(P):
    T = P["T"]
    t = np.arange(T)
    years = np.asarray(P["years"])
    sub = {"span": np.ones(T, bool), "era1": t < T // 2, "era2": t >= T // 2, "down_years": np.isin(years, list(P["down_years"]))}
    for y in np.unique(years):
        sub[f"y{int(y)}"] = years == y
    return sub


def drift_table(ex, groups, subsets):
    """The main computation: masked sum / count, bp per bar, per group x subset, with counts."""
    out = {}
    for g, m in groups.items():
        out[g] = {}
        for s, tm in subsets.items():
            mm = m & tm[:, None]
            k = int(mm.sum())
            out[g][s] = dict(n=k, bp=float(ex[mm].sum() / k) * 1e4 if k else None)
    return out


def drift_independent(ex, mask):
    """[D]'s second implementation: np.where + nanmean, no masked gather, no bincount."""
    return float(np.nanmean(np.where(mask, ex, np.nan))) * 1e4


def assert_D(ex, groups, subsets, table, tol=1e-12):
    worst, n = 0.0, 0
    for g, m in groups.items():
        for s, tm in subsets.items():
            if table[g][s]["bp"] is None:
                continue
            d = drift_independent(ex, m & tm[:, None])
            worst = max(worst, abs(d - table[g][s]["bp"]))
            n += 1
            assert worst < tol, f"[D] {g}/{s}: independent {d} vs table {table[g][s]['bp']} ({worst:.2e})"
    return worst, n


def stage0_compute(P):
    ex, groups = stage0_masks(P)
    subsets = stage0_subsets(P)
    table = drift_table(ex, groups, subsets)
    worst, n = assert_D(ex, groups, subsets, table)
    return ex, groups, subsets, table, worst, n


def print_stage0(P, table):
    print("\n  STAGE 0 -- the premise: mean next-bar hedged return r1T[t] - m_f[t] on eligible name-bars, bp per bar [name-bars]")
    cols = ["span", "era1", "era2", "down_years"]
    print("  %-10s " % "group" + " ".join("%22s" % c for c in cols))
    for g in table:
        print("  %-10s " % g + " ".join("%+9.3f [%10s]" % (table[g][c]["bp"], f"{table[g][c]['n']:,}") if table[g][c]["bp"] is not None else "%22s" % "-" for c in cols))
    years = sorted(int(k[1:]) for k in table["elig_all"] if k.startswith("y"))
    fb = lambda g, y: ("%+.1f" % table[g][f"y{y}"]["bp"]) if table[g][f"y{y}"]["bp"] is not None else "-"
    print("  by year, bottom_10 / above_10 / top_10 [bottom_10 name-bars] (a year with no defined pct_mom prints '-'):")
    print("  " + " ".join(f"{y}:{fb('bottom_10', y)}/{fb('above_10', y)}/{fb('top_10', y)}[{table['bottom_10'][f'y{y}']['n']:,}]" for y in years))
    print(f"  down-years {P['down_years']}; era midpoint bar {P['T'] // 2} ({P['dates'][P['T'] // 2]})")


def stage_stage0(P, paths):
    _ex, _groups, _subsets, table, worst, n = stage0_compute(P)
    print(f"    [D] Stage 0's drift equals an independent np.where + nanmean on every group x subset ({n} cells) to {worst:.1e}")
    print_stage0(P, table)
    out = dict(study=STUDY, note="D359 Stage 0: the cohort's own next-bar drift. ex = r1T - m_f (the floored-market hedge the kernel uses); "
                                  "pct_mom lagged; groups on eligible name-bars with finite r1T and m_f. bp per bar; n = name-bars.",
               groups=list(table), subsets=["span", "era1", "era2", "down_years", "by year"], table=table, D_worst=worst, D_cells=n,
               down_years=P["down_years"], era_midpoint_bar=P["T"] // 2, era_midpoint_date=P["dates"][P["T"] // 2])
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stage0"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['stage0']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


# ------------------------------------------------------------------ the controls: [A'] [B] [B_c]
def aprime_draw(sh, sc, elig, rng):
    """A' (D351): per-name time rotation of the SHORT signal within elig, the score (pct_rev) rotated with it so the invalidation exit
    reads the rotated signal (irrelevant to the cap exit; kept consistent); D351's two assertions."""
    sl, ss, sc_ = EB.rotate_signals(zeros(sh), sh, sc, elig, rng)
    assert not sl.any(), "[A'] a long appeared in the rotation"
    assert not (ss & ~elig).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(ss.sum(axis=0), sh.sum(axis=0)), "[A'] per-name event count changed"
    return ss, sc_


def control_bc_signal(sh, coh, elig, rng):
    """B_c: each event (t, i) -> a random name j from {j : elig[t, j] & cohort[t, j] & ~sh[t, j]} that day, distinct within the day
    (B's convention); when the pool runs short the remaining events keep their name and are counted. Returns (signal, kept)."""
    out = zeros(sh)
    pool_all = elig & coh & ~sh
    kept = 0
    for t in np.flatnonzero(sh.any(axis=1)):
        ev = np.flatnonzero(sh[t])
        pool = np.flatnonzero(pool_all[t])
        k = min(ev.size, pool.size)
        if k:
            out[t, rng.choice(pool, size=k, replace=False)] = True
        if ev.size > k:
            out[t, ev[k:]] = True
            kept += ev.size - k
    return out, kept


def assert_Bc(sigBc, sh, coh, elig, kept):
    """[B_c]: dates kept, count kept; every replacement eligible, in the cohort that day, never an event name; kept == the shortfall."""
    assert np.array_equal(sigBc.sum(axis=1), sh.sum(axis=1)), "[B_c] dates changed"
    rep = sigBc & ~sh
    assert not (rep & ~elig).any(), "[B_c] a replacement is ineligible"
    assert not (rep & ~coh).any(), "[B_c] a replacement is outside the cohort that day"
    assert int((sigBc & sh).sum()) == kept, f"[B_c] kept {int((sigBc & sh).sum())} != counted shortfall {kept}"
    short = 0
    for t in np.flatnonzero(sh.any(axis=1)):
        short += max(0, int(sh[t].sum()) - int((elig[t] & coh[t] & ~sh[t]).sum()))
    assert short == kept, f"[B_c] shortfall recount {short} != kept {kept}"
    return int(rep.sum()), kept


# ------------------------------------------------------------------ [G] against D352
def assert_G(P, verbose=True):
    """Event counts per cell; each cell and its complement partition the spike; the (., 90) spike with the cohort dropped equals D352's
    rev_5/S10 stored row (event count, finite-F count, mean(-F) to 1e-9 -- the only quantities D352 stored for it); the kernel's cap-40
    short mean reproduces D352's stored kernel value on retrace_leg/S10 (a survivor it ran) to 1e-9."""
    pct_mom, pct_rev, prev, elig = grids(P)
    counts = {}
    for c, s in CELLS:
        sh, comp, sp = cell_signal(P, c, s), complement_signal(P, c, s), spike(P, s)
        assert_partition(sh, comp, sp)
        counts[cell_name(c, s)] = dict(cell=int(sh.sum()), complement=int(comp.sum()), spike=int(sp.sum()), mirror=int(mirror_signal(P, c, s).sum()))
    sp90 = spike(P, 90)
    st = json.loads(D352_SCREEN.read_text())
    row = next(m for m in st["members"] if m["member"] == "rev_5/S10")
    assert st["thresholds"]["S10"] == 90.0 and row["n_events_raw"] == D352_REV5_S10["n_events_raw"], "[G] D352's stored row"
    n_sp = int(sp90.sum())
    assert n_sp == row["n_events_raw"], f"[G] (., 90) spike {n_sp:,} != D352's rev_5/S10 {row['n_events_raw']:,}"
    F = P["F"]
    assert F is not None, "[G] needs the forward-40 grid (prep need_grids=True)"
    t_ev, i_ev = np.nonzero(sp90)
    Fe = (-np.asarray(F))[t_ev.astype(np.int32), i_ev.astype(np.int32)]           # D352's Fs = -F, gathered as V50.member_stats does
    fin = np.isfinite(Fe)
    E = float(Fe[fin].mean()) * 1e4
    assert int(fin.sum()) == row["n_events"] and int((~fin).sum()) == row["n_nan_F"], "[G] finite-F event counts differ from D352's row"
    assert abs(E - row["E_bp"]) < 1e-9 and abs(E - D352_REV5_S10["E_bp"]) < 1e-9, f"[G] grid statistic {E} vs D352's {row['E_bp']}"
    assert int(np.unique(i_ev[fin]).size) == row["n_names"], "[G] name count (over finite-F events, as member_stats) differs from D352's row"
    assert "rev_5/S10" not in st["gate"]["survivors"], "[G] rev_5/S10 was a D352 survivor after all -- use its kernel file"
    # the kernel identity on a survivor D352 ran: the same rule (pct >= 90, prev < 90, elig), the same kernel, cap 40, short
    rep = json.loads(D352_REPORT.read_text())
    ref = rep["report"][D352_KERNEL_REF]["short/cap"]
    ctrl = json.loads(next(DATA.glob(f"d352_ctrl_{D352_KERNEL_REF.replace('/', '-')}_p*.json")).read_text())
    pct_ref = V47.percentile_grid(V50.lagged(P, D352_KERNEL_REF.split("/")[0]))
    prev_ref = np.full_like(pct_ref, np.nan)
    prev_ref[1:] = pct_ref[:-1]
    with np.errstate(invalid="ignore"):
        hi_ref = np.ascontiguousarray((pct_ref >= 90.0) & (prev_ref < 90.0) & elig)
    assert int(hi_ref.sum()) == ctrl["events"] == ref["events"], f"[G] {D352_KERNEL_REF} events {int(hi_ref.sum())} vs stored {ctrl['events']}"
    r_ref = run_short(P, hi_ref, pct_ref, "cap", 40)
    m_ref = float(V47.pnl_bp(r_ref).mean())
    assert len(r_ref["trades"]) == ref["trades"] == ctrl["trades"], f"[G] {D352_KERNEL_REF} trades {len(r_ref['trades'])} vs {ref['trades']}"
    assert abs(m_ref - ref["mean_bp"]) < 1e-9 and abs(m_ref - ctrl["observed"]) < 1e-9, f"[G] {D352_KERNEL_REF} cap-40 mean {m_ref} vs stored {ref['mean_bp']}"
    del pct_ref, prev_ref, hi_ref, r_ref
    # the (., 90) spike's own cap-40 short mean: computed here, NOT stored by D352 (reported beside)
    r40 = run_short(P, np.ascontiguousarray(sp90), pct_rev, "cap", 40)
    m40 = float(V47.pnl_bp(r40).mean())
    out = dict(counts=counts, spike90_events=n_sp, d352_row=dict(n_events_raw=row["n_events_raw"], n_events=row["n_events"], n_nan_F=row["n_nan_F"],
               n_names=row["n_names"], E_bp=row["E_bp"]), grid_E_bp=E, spike90_cap40_short=dict(trades=len(r40["trades"]), mean_bp=m40),
               kernel_ref=dict(member=D352_KERNEL_REF, trades=ref["trades"], events=ctrl["events"], mean_bp=m_ref, stored_mean_bp=ref["mean_bp"]))
    if verbose:
        print(f"    [G] events per cell " + ", ".join(f"{k} {v['cell']:,} (complement {v['complement']:,}, mirror {v['mirror']:,})" for k, v in counts.items())
              + "; every cell and its complement partition the unconditioned spike (disjoint, union equal)")
        print(f"    [G] the (., 90) spike with the cohort dropped = {n_sp:,} events == D352's rev_5/S10 stored n_events_raw ({row['n_events_raw']:,}); "
              f"its grid statistic mean(-F) over the {row['n_events']:,} finite-F events {E:+.6f} bp == D352's stored E_bp to 1e-9 ({row['n_nan_F']} NaN-F, "
              f"{row['n_names']} names). D352 stored NO kernel number for rev_5/S10 (not a survivor); its cap-40 short mean here is {m40:+.4f} bp on "
              f"{len(r40['trades']):,} trades. The kernel identity is asserted on {D352_KERNEL_REF} (a survivor D352 ran): cap-40 short mean "
              f"{m_ref:+.6f} == stored {ref['mean_bp']:+.6f} to 1e-9 on {ref['trades']:,} trades, {ctrl['events']:,} events")
    return out


# ------------------------------------------------------------------ [E]
def assert_E(P, rng, k=300):
    """k sampled events per cell satisfy both conditions on the raw lagged scores by direct count at t-1 (percentile of the raw floored
    score column at t-1 == the grid at t), the spike is fresh (pct_rev at t-2 < s), and the unlagged rule (both percentiles at t, fresh
    against t-1) fails on every sample."""
    pct_mom, pct_rev, _prev, elig = grids(P)
    raw_m, raw_r = raw_floored(P, MOM), raw_floored(P, REV)
    lines = []
    for c, s in CELLS:
        sh = cell_signal(P, c, s)
        ev = np.argwhere(sh)
        pick = ev[rng.choice(len(ev), size=min(k, len(ev)), replace=False)]
        worst, n_unl = 0.0, 0
        for t, i in pick:
            assert elig[t, i] and t >= P["m_start"] and t >= 2, "[E] an event off the eligible set"
            dm1, km1 = pct_direct(raw_m[:, t - 1], i)
            dr1, kr1 = pct_direct(raw_r[:, t - 1], i)
            dr2, kr2 = pct_direct(raw_r[:, t - 2], i)
            assert all(np.isfinite(x) for x in (dm1, dr1, dr2)) and min(km1, kr1, kr2) >= 50, "[E] an event on an undefined percentile"
            assert dm1 <= c and dr1 >= s and dr2 < s, f"[E] {cell_name(c, s)} event ({t}, {i}): mom {dm1:.2f}, rev {dr1:.2f} at t-1, rev {dr2:.2f} at t-2"
            worst = max(worst, abs(dm1 - pct_mom[t, i]), abs(dr1 - pct_rev[t, i]), abs(dr2 - pct_rev[t - 1, i]))
            dm0, _ = pct_direct(raw_m[:, t], i)
            dr0, _ = pct_direct(raw_r[:, t], i)
            n_unl += int(np.isfinite(dm0) and np.isfinite(dr0) and dm0 <= c and dr0 >= s and dr1 < s)     # the rule with no lag, at t
        assert worst < 1e-9 and n_unl == 0, f"[E] {cell_name(c, s)}: grid mismatch {worst:.1e}, unlagged passes {n_unl}"
        lines.append(f"{cell_name(c, s)} {len(pick)} ({worst:.0e})")
    del raw_m, raw_r
    return lines


# ------------------------------------------------------------------ [S] sign in money on the short
def assert_S_short(P, tr, rng, k=300, tag="[S]"):
    """k sampled SHORT trades equal the open-fill recomputation against the floored market EXACTLY (the kernel accumulates
    -(v - m) per bar; the recomputation accumulates (v - m) and negates: bit-identical); a name that falls pays positively (counted),
    one that rises pays negatively; the LONG of the same path (side 0 recomputation) pays the opposite amount exactly."""
    pick = rng.choice(len(tr), size=min(k, len(tr)), replace=False)
    worst, n_fell, n_rose, worst_m = 0.0, 0, 0, 0.0
    for p in pick:
        row, e0, age, pnl, sd = tr[p]
        assert sd == 1, f"{tag} a long in the short ledger"
        rec = V53.recompute_trade(P, row, e0, age, 1)
        worst = max(worst, abs(pnl - rec))
        ex = -rec                                                     # the name's own hedged excess
        if ex < 0:
            assert pnl > 0, f"{tag} a short on a name that fell does not pay positively"
            n_fell += 1
        elif ex > 0:
            assert pnl < 0, f"{tag} a short on a name that rose does not pay negatively"
            n_rose += 1
        worst_m = max(worst_m, abs(V53.recompute_trade(P, row, e0, age, 0) + pnl))
    assert worst == 0.0, f"{tag} {worst:.2e} (not bit-identical)"
    assert worst_m == 0.0, f"{tag} the mirror's long on the same path does not pay the opposite amount ({worst_m:.2e})"
    return worst, int(pick.size), n_fell, n_rose, worst_m


def perturb_test(P, sig, sc, side, res, sign):
    """+50 bp on r1T at a later bar of one held trade, re-simulated on a perturbed A3: that trade moves by sign x 50.000 bp and no
    other; the deployed hedged and unhedged series move by sign x 50 / n_open on that bar and nowhere else."""
    tr = res["trades"]
    j = next(k for k in range(len(tr)) if tr[k][2] >= 3)
    row, e0, age = tr[j][0], tr[j][1], tr[j][2]
    ts_ = e0 + 1
    r1p = np.array(P["r1T"], dtype=float)
    r1p[ts_, row] += 50e-4
    resP = simulate(P, sig, sc, res["exit"], res["cap"], side, A3=dict(P["A3"], r1T=r1p))
    assert len(resP["trades"]) == len(tr) and all(a[:3] == b[:3] and a[4] == b[4] for a, b in zip(resP["trades"], tr)), "[S] the perturbation changed the ledger's shape"
    dpnl = np.array([a[3] - b[3] for a, b in zip(resP["trades"], tr)]) * 1e4
    assert abs(dpnl[j] - sign * 50.0) < 1e-9 and np.abs(np.delete(dpnl, j)).max() < 1e-9, f"[S] the +50 bp did not land on the one trade as {sign * 50:+.0f}"
    n_open = int(res["held"][ts_])
    delta = (resP["book_dep_x"][ts_] - res["book_dep_x"][ts_]) * 1e4
    du = (resP["book_dep"][ts_] - res["book_dep"][ts_]) * 1e4
    assert abs(delta - sign * 50.0 / n_open) < 1e-9 and abs(du - sign * 50.0 / n_open) < 1e-9, f"[S] deployed moved {delta:.6f}, expected {sign * 50.0 / n_open:.6f}"
    other = np.ones(P["T"], bool)
    other[ts_] = False
    assert np.array_equal(resP["book_dep_x"][other], res["book_dep_x"][other], equal_nan=True), "[S] the perturbation leaked to other bars"
    del r1p, resP
    return dict(trade=j, row=int(row), symbol=P["symbols"][row], date=P["dates"][ts_], bar=int(ts_), age=int(age), dpnl=float(dpnl[j]), n_open=n_open, delta=float(delta))


# ------------------------------------------------------------------ the rsi-bucket interaction
def bucket_interaction(P, tr, pnl, F10, elig_b):
    """D352's decomposition at the trade's own horizon: E_sb (the cell's mean in bucket b) - E_b (the SHORT forward-10 base rate of the
    bucket, -F10 over eligible name-bars with a defined rsi percentile) - E_s + E_all; [X]: the buckets partition the trades and
    sum_b n_b (E_sb - E_s) == 0. Undefined-percentile trades counted, excluded from the buckets."""
    bucket = np.asarray(P["bucket_rsi"])
    Fs = -F10
    Fm = elig_b & np.isfinite(Fs)
    E_all = float(np.nanmean(Fs[Fm])) * 1e4
    E_b = {b: (float(np.nanmean(Fs[Fm & (bucket == b)])) * 1e4 if (Fm & (bucket == b)).any() else np.nan) for b in range(10)}
    b_ev = V49.event_buckets(P, tr)
    Es = float(pnl.mean())
    inter = {}
    for b in range(10):
        mb = b_ev == b
        if mb.any():
            Esb = float(pnl[mb].mean())
            inter[b] = dict(n=int(mb.sum()), mean_bp=Esb, median_bp=float(np.median(pnl[mb])), share_pos=float((pnl[mb] > 0).mean()),
                            E_b=E_b[b], interaction=Esb - E_b[b] - Es + E_all)
    groups = [b for b in range(-1, 10) if (b_ev == b).any()]
    assert sum(int((b_ev == b).sum()) for b in groups) == pnl.size, "[X] the buckets do not partition the trades"
    tot = sum((b_ev == b).sum() * (pnl[b_ev == b].mean() - Es) for b in groups)
    assert abs(tot) < 1e-9 * max(1.0, float(np.abs(pnl).sum())), f"[X] {tot}"
    return dict(horizon=10, E_all=E_all, E_b=E_b, buckets=inter, undefined_n=int((b_ev < 0).sum()), identity=float(tot),
                method="E_sb - E_b - E_s + E_all with E_b the SHORT forward-10 base rate (-forward_excess_grid(h=10)) over eligible "
                       "name-bars with a defined rsi percentile; bucket = rsi percentile at t-1 of the trigger name at entry")


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    pct_mom, pct_rev, prev, elig = grids(P)
    c0, s0 = PRIMARY
    ci0 = CELLS.index(PRIMARY)
    # [G]
    g = assert_G(P)
    print(f"        ({el()})")
    # [E]
    lines = assert_E(P, np.random.default_rng([SEED, STUDY, 0]))
    print(f"    [E] sampled events satisfy the definition by direct count on the raw floored scores at t-1 (pct_mom <= c, pct_rev >= s), are fresh "
          f"(pct_rev at t-2 < s), equal the grids to 1e-9, and the unlagged rule at t fails on every sample: " + ", ".join(lines) + f" ({el()})")
    # [D]
    ex, groups, subsets, table, worst_d, n_d = stage0_compute(P)
    print(f"    [D] Stage 0's drift (masked sum / count) equals an independent np.where + nanmean on every group x subset ({n_d} cells) to {worst_d:.1e}")
    print_stage0(P, table)
    # the primary cell on the three exits
    sh = cell_signal(P, c0, s0)
    RES = {EXIT_NAME[(e, cap)]: run_short(P, sh, pct_rev, e, cap) for e, cap in EXITS}
    res = RES[PRIMARY_EXIT]
    tr = res["trades"]
    assert all(t[4] == 1 for t in tr) and all(t[2] <= 10 for t in tr), "[K] a long or an over-cap hold in the primary ledger"
    assert all(t[2] <= 10 for t in RES["inv10"]["trades"]), "[K] invalidation-10 held past the cap"
    acc = V49.event_accounting(P, sh, res, cap=10)
    print(f"    check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; "
          f"trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end (primary, cap 10)")
    # [SB]
    rng = np.random.default_rng([SEED, STUDY, 5])
    pt, htb, rate = V49.borrow_of(P, tr)
    idx_sb, worst_b = V49.check_borrow(P, tr, pt, htb, rng, k=200)
    assert (rate[htb] == BR.HTB_BPS).all() and (rate[~htb] == BR.GC_BPS).all(), "[SB] rates"
    print(f"    [SB] BORROW: on {len(idx_sb)} sampled short trades the per-trade borrow equals the rule x bars held / 252 to {worst_b:.1e}, and every HTB "
          f"flag agrees with the F0-window / ${BR.PX_HTB:.0f} rule; HTB on {int(htb.sum())} of {len(tr):,} ({100 * htb.mean():.1f}%); mean borrow "
          f"{pt.mean():.2f} bp per trade")
    # [HX] primary x three exits, hedged and unhedged
    lines = []
    for nm, r in RES.items():
        V53.assert_series_defs(r)
        hx = assert_HX(r, P, "book_dep_x", hedged=True)
        hu = assert_HX(r, P, "book_dep", hedged=False)
        lines.append(f"{nm} {hx['worst']:.0e}/{hu['worst']:.0e} ({hx['uncovered']} tail)")
    print(f"    [HX] hedged deployed x held == the ledger's sgn(v - m) per bar and unhedged x held == sgn v per bar, to 1e-12 on every covered bar "
          f"(open tail excluded, contiguous), the hedged rebuild sums to the ledger to 1e-9; primary cell x three exits: " + "; ".join(lines) + f" ({el()})")
    # [A'] [B] [B_c] on 2 draws of the primary cell
    coh = cohort(P, c0)
    PB = V53.b_pool_P(P, elig)
    rngA = np.random.default_rng([SEED, STUDY, ci0, ARM["A"], 0])
    rngB = np.random.default_rng([SEED, STUDY, ci0, ARM["B"], 0])
    rngC_ = np.random.default_rng([SEED, STUDY, ci0, ARM["Bc"], 0])
    obs = observed_stats(res, P)
    A_, B_, Bc_ = [], [], []
    rA_keep = sBc_keep = None
    for d in range(2):
        ss, sc_ = aprime_draw(sh, pct_rev, elig, rngA)
        rA = run_short(P, ss, sc_, "cap", 10)
        A_.append(null_stats(rA, P))
        sB = V47.control_b_signal(PB, sh, rngB)
        keptB, shortB = assert_B(P, PB, sh, sB, elig)
        B_.append(null_stats(run_short(P, sB, pct_rev, "cap", 10), P))
        sBc, keptC = control_bc_signal(sh, coh, elig, rngC_)
        n_rep, _ = assert_Bc(sBc, sh, coh, elig, keptC)
        Bc_.append(null_stats(run_short(P, sBc, pct_rev, "cap", 10), P))
        if d == 0:
            rA_keep, sBc_keep = rA, sBc
    fm = lambda xs, key, f: ", ".join(format(x[key], f) for x in xs)
    print(f"    [A'] 2 draws of {cell_name(c0, s0)}: every rotated event eligible, every name's event count kept, no long, the score rotated with the signal, "
          f"deployed series NaN-free; per trade {fm(A_, 'trade_mean_bp', '+.2f')} bp ({fm(A_, 'trades', ',')} trades) "
          f"vs observed {obs['trade_mean_bp']:+.2f} ({el()})")
    print(f"    [B] every event keeps its date and rsi bucket; replacements are eligible names with a DEFINED rsi percentile, never an event name; "
          f"kept == the pool shortfall ({keptB} of {int(sh.sum()):,}); per trade {fm(B_, 'trade_mean_bp', '+.2f')} bp")
    print(f"    [B_c] every replacement is eligible, in the cohort pct_mom <= {c0} that day and never an event name; dates and counts kept; kept == the "
          f"counted shortfall ({keptC} of {int(sh.sum()):,}, {n_rep:,} replaced); per trade {fm(Bc_, 'trade_mean_bp', '+.2f')} bp")
    # [S]
    worst_s, n_s, n_fell, n_rose, worst_m = assert_S_short(P, rA_keep["trades"], np.random.default_rng([SEED, STUDY, 2]))
    pert = perturb_test(P, sh, pct_rev, 1, res, -1.0)
    lo_m = mirror_signal(P, c0, s0)
    res_m = run_mirror(P, lo_m, pct_rev, "cap", 10)
    assert all(t[4] == 0 for t in res_m["trades"]), "[S] a short in the mirror ledger"
    wm, nm_, n_fav_m = V53.assert_S(P, res_m["trades"], np.random.default_rng([SEED, STUDY, 3]), tol=1e-15)
    pert_m = perturb_test(P, lo_m, pct_rev, 0, res_m, +1.0)
    print(f"    [S] SIGN IN MONEY on the SHORT: {n_s} sampled A' trades equal the open-fill recomputation against the floored market to {worst_s:.1f} "
          f"(bit-identical); a short on a name that fell pays positively ({n_fell} fell, {n_rose} rose, of {n_s}); the LONG of the same path pays the "
          f"opposite amount to {worst_m:.1f}; +50 bp on r1T[{pert['bar']}, {pert['row']}] ({pert['symbol']} {pert['date']}, bar 2 of a {pert['age']}-bar "
          f"short) re-simulated on a perturbed A3 moves that trade by {pert['dpnl']:+.3f} bp and no other, and the deployed series by {pert['delta']:.4f} "
          f"= -50 / {pert['n_open']} open, no other bar; the mirror's {nm_} sampled LONG trades equal the recomputation to {wm:.1f} ({n_fav_m} favourable "
          f"paths pay positively) and +50 bp on {pert_m['symbol']} {pert_m['date']} moves its long by {pert_m['dpnl']:+.3f} ({el()})")
    # [C] on the primary cell
    pnl = V47.pnl_bp(res)
    cC = control_C(pnl, np.random.default_rng([SEED, STUDY, ci0, ARM["C"]]))
    z = cC["mean"] / cC["se"]
    # D358's stated weakening kept: the pre-registered "within 3 SE" band (section 8 says 3 SE here) -- asserted at 3 SE, the can-fail check below.
    assert abs(z) < 3.0, f"[C] mean {cC['mean']:+.3f} bp is {z:+.2f} SE from zero"
    print(f"    [C] control C (1,000 random directions on the primary cap-10 ledger): mean {cC['mean']:+.3f} bp (se {cC['se']:.3f}, z {z:+.2f}) within 3 SE "
          f"of zero; p50 {cC['p50']:+.2f} p95 {cC['p95']:+.2f} max {cC['max']:+.2f}; observed {pnl.mean():+.2f} {'above' if cC['above'] else 'NOT above'} p95")
    # [6]
    broke = []
    try:                                                              # [S] on a sign-flipped ledger
        assert_S_short(P, [(r, e, a, -p, sd) for r, e, a, p, sd in rA_keep["trades"]], np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    try:                                                              # [G] with the cohort mask perturbed: one spike event moved out of the cell
        sh6 = sh.copy()
        t6, i6 = np.argwhere(sh6)[0]
        sh6[t6, i6] = False
        assert_partition(sh6, complement_signal(P, c0, s0), spike(P, s0))
    except AssertionError as e:
        assert "[G]" in str(e)
        broke.append("G-union")
    try:                                                              # [G] with the cohort mask perturbed the other way: a complement event admitted
        coh6 = coh.copy()
        t6, i6 = np.argwhere(complement_signal(P, c0, s0))[0]
        coh6[t6, i6] = True
        assert_partition(spike(P, s0) & coh6, complement_signal(P, c0, s0), spike(P, s0))
    except AssertionError as e:
        assert "[G]" in str(e)
        broke.append("G-overlap")
    try:                                                              # [B_c] with a replacement outside the cohort injected
        s6 = sBc_keep.copy()
        t6 = int(np.flatnonzero((s6 & ~sh).any(axis=1))[0])
        j_old = int(np.flatnonzero(s6[t6] & ~sh[t6])[0])
        j_new = int(np.flatnonzero(elig[t6] & ~coh[t6] & ~sh[t6] & ~s6[t6])[0])
        s6[t6, j_old] = False
        s6[t6, j_new] = True
        assert_Bc(s6, sh, coh, elig, int((sBc_keep & sh).sum()))
    except AssertionError as e:
        assert "[B_c]" in str(e)
        broke.append("Bc")
    try:                                                              # [D] on a perturbed mask
        g6 = {k: v for k, v in groups.items()}
        m6 = g6["bottom_10"].copy()
        t6, i6 = np.argwhere(m6)[0]
        m6[t6, i6] = False
        g6["bottom_10"] = m6
        assert_D(ex, g6, subsets, table)
    except AssertionError as e:
        assert "[D]" in str(e)
        broke.append("D")
    assert broke == ["S", "G-union", "G-overlap", "Bc", "D"], f"[6] raised: {broke}"
    print("    [6] [S] raises on a sign-flipped ledger; [G] raises with the cohort mask perturbed (a spike event dropped from the cell: union fails; a "
          "complement event admitted: overlap fails); [B_c] raises when a replacement outside the cohort is admitted; [D] raises on a perturbed mask")
    del ex
    (SELFTEST_TMP / "selftest_summary.json").write_text(json.dumps(clean(dict(G=g, C=cC, observed=obs, stage0=table)), indent=1))
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_cell(P, c, s, draws, part, paths):
    ci = CELLS.index((c, s))
    _pm, pct_rev, _pv, elig = grids(P)
    sh = cell_signal(P, c, s)
    coh = cohort(P, c)
    res = run_short(P, sh, pct_rev, "cap", 10)
    obs = observed_stats(res, P)
    print(f"\n  {cell_name(c, s)} part {part}: {int(sh.sum()):,} events -> {obs['trades']:,} trades, {obs['entries']:,} entries; per trade {obs['trade_mean_bp']:+.2f} bp; "
          f"deployed gross {obs['gross_bp']:+.2f} net PUB {obs['net_bp_PUB']:+.2f} bp/bar (Sharpe {obs['sharpe_net_PUB']:+.3f}), exposure {100 * obs['exposure']:.1f}%")
    PB = V53.b_pool_P(P, elig)
    seeds = dict(A=[SEED, STUDY, ci, ARM["A"], part], B=[SEED, STUDY, ci, ARM["B"], part], Bc=[SEED, STUDY, ci, ARM["Bc"], part])
    rngA, rngB, rngBc = (np.random.default_rng(seeds[k]) for k in ("A", "B", "Bc"))
    A_, B_, Bc_, keptB, keptBc = [], [], [], [], []
    tA = tB = tBc = 0.0
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        ss, sc_ = aprime_draw(sh, pct_rev, elig, rngA)
        A_.append(null_stats(run_short(P, ss, sc_, "cap", 10), P))
        t2 = time.time()
        sB = V47.control_b_signal(PB, sh, rngB)
        kb, _ = assert_B(P, PB, sh, sB, elig)
        keptB.append(kb)
        B_.append(null_stats(run_short(P, sB, pct_rev, "cap", 10), P))
        t3 = time.time()
        sBc, kc = control_bc_signal(sh, coh, elig, rngBc)
        assert_Bc(sBc, sh, coh, elig, kc)
        keptBc.append(kc)
        Bc_.append(null_stats(run_short(P, sBc, pct_rev, "cap", 10), P))
        tA += t2 - t1
        tB += t3 - t2
        tBc += time.time() - t3
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {cell_name(c, s)}: {d + 1}/{draws} ({time.time() - ts:.0f}s; A' {tA / (d + 1):.1f} s/draw, B {tB / (d + 1):.1f}, B_c {tBc / (d + 1):.1f})", flush=True)
    keys = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trades", "exposure")
    out = dict(study=STUDY, c=c, s=s, cell=cell_name(c, s), cell_index=ci, exit=PRIMARY_EXIT, draws=draws, part=part, seeds=seeds, events=int(sh.sum()),
               observed=obs, control_A_prime={k: [x[k] for x in A_] for k in keys}, control_B={k: [x[k] for x in B_] for k in keys},
               control_B_c={k: [x[k] for x in Bc_] for k in keys}, B_kept=keptB, B_c_kept=keptBc, B_pool="elig & isfinite(PCT rsi), same day, same rsi bucket",
               B_c_pool=f"elig & (pct_mom <= {c}) & ~sh, same day, distinct within the day", seconds_per_draw=dict(A=tA / max(draws, 1), B=tB / max(draws, 1), Bc=tBc / max(draws, 1)),
               rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(c=c, s=s, part=part))
    f.write_text(json.dumps(clean(out)))
    if draws:
        a, b, bc = (np.array(out[k]["trade_mean_bp"]) for k in ("control_A_prime", "control_B", "control_B_c"))
        print(f"  wrote {f}: per trade A' p50 {np.median(a):+.2f} p95 {np.quantile(a, .95):+.2f}; B p50 {np.median(b):+.2f} p95 {np.quantile(b, .95):+.2f}; "
              f"B_c p50 {np.median(bc):+.2f} p95 {np.quantile(bc, .95):+.2f} vs observed {obs['trade_mean_bp']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def load_controls(paths, c, s, obs):
    fs = sorted(paths["dir"].glob(f"d359_ctrl_{c}_{s}_p*.json"))
    if not fs:
        return None
    A, B, Bc, parts = {}, {}, {}, []
    for f in fs:
        d = json.loads(f.read_text())
        assert d["c"] == c and d["s"] == s and d["draws"] == len(d["control_A_prime"]["trade_mean_bp"]), f"[P] {f.name}"
        for k in ("net_bp_PUB", "gross_bp", "trade_mean_bp", "trades"):
            assert abs(d["observed"][k] - obs[k]) < 1e-9, f"[P] {f.name}: observed {k} {d['observed'][k]} differs from the re-simulated {obs[k]}"
        for k in d["control_A_prime"]:
            A.setdefault(k, []).extend(d["control_A_prime"][k])
            B.setdefault(k, []).extend(d["control_B"][k])
            Bc.setdefault(k, []).extend(d["control_B_c"][k])
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], seconds_per_draw=d.get("seconds_per_draw"), B_kept=d.get("B_kept"), B_c_kept=d.get("B_c_kept")))
    stats = ("trade_mean_bp", "net_bp_PUB", "sharpe_net_PUB", "gross_bp", "net_bp_PB")
    tdist = lambda x: dict(p50=float(np.median(x)), min=int(min(x)), max=int(max(x)))
    return dict(draws=len(A["trade_mean_bp"]), parts=parts,
                A_prime={k: V53._dist(A[k], obs[k]) for k in stats}, B={k: V53._dist(B[k], obs[k]) for k in stats}, B_c={k: V53._dist(Bc[k], obs[k]) for k in stats},
                A_prime_trades=tdist(A["trades"]), B_trades=tdist(B["trades"]), B_c_trades=tdist(Bc["trades"]))


def arm_report(P, sig, sc, side, elig, with_groups, exits=EXITS):
    out = dict(events=int(sig.sum()))
    for e, cap in exits:
        nm = EXIT_NAME[(e, cap)]
        res = simulate(P, sig, sc, e, cap, side)
        V53.assert_series_defs(res)
        hx = dict(hedged=assert_HX(res, P, "book_dep_x", hedged=True), unhedged=assert_HX(res, P, "book_dep", hedged=False))
        dep = deployed_block(res, P)
        dep["splits_hedged"] = deployed_subsets(res, P, res["book_dep_x"])
        trd = trade_block(P, res, elig, side, with_groups and nm == PRIMARY_EXIT)
        out[nm] = dict(deployed=dep, per_trade=trd, hx=hx, res=res)
    return out


def stage_report(P, paths):
    R = {}
    t0 = time.time()
    _pm, pct_rev, _pv, elig = grids(P)
    assert paths["stage0"].exists(), f"run --stage0 first ({paths['stage0']})"
    S0 = json.loads(paths["stage0"].read_text())["table"]
    g = assert_G(P, verbose=False)
    print(f"    [G] every cell and its complement partition the spike; the (., 90) spike == D352's rev_5/S10 row ({g['spike90_events']:,} events, grid statistic "
          f"{g['grid_E_bp']:+.4f} bp to 1e-9); the kernel reproduces D352's {D352_KERNEL_REF} cap-40 short mean {g['kernel_ref']['mean_bp']:+.4f} to 1e-9 "
          f"({time.time() - t0:.0f}s)")
    elig_b = elig & np.isfinite(np.asarray(P["PCT"]["rsi"]))
    F10 = V47.forward_excess_grid(P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["finT"], h=10)
    for c, s in CELLS:
        nm = cell_name(c, s)
        sh = cell_signal(P, c, s)
        cell = arm_report(P, sh, pct_rev, 1, elig, with_groups=True)
        prim = cell[PRIMARY_EXIT]
        res = prim.pop("res")
        for k in list(cell):
            if isinstance(cell[k], dict) and "res" in cell[k]:
                cell[k].pop("res")
        cell["accounting"] = V49.event_accounting(P, sh, res, cap=10)
        cell["observed"] = observed_stats(res, P)
        cell["controls"] = load_controls(paths, c, s, cell["observed"])
        cell["control_C"] = control_C(V47.pnl_bp(res), np.random.default_rng([SEED, STUDY, CELLS.index((c, s)), ARM["C"]]))
        cell["interaction"] = bucket_interaction(P, res["trades"], V47.pnl_bp(res), F10, elig_b)
        beside = [("cap", 10)] if (c, s) != PRIMARY else EXITS
        comp = arm_report(P, complement_signal(P, c, s), pct_rev, 1, elig, with_groups=((c, s) == PRIMARY), exits=beside)
        mirr = arm_report(P, mirror_signal(P, c, s), pct_rev, 0, elig, with_groups=((c, s) == PRIMARY), exits=beside)
        for d in (comp, mirr):
            for k in list(d):
                if isinstance(d[k], dict) and "res" in d[k]:
                    d[k].pop("res")
        cell["complement"], cell["mirror"] = comp, mirr
        R[nm] = cell
        print(f"    {nm}: [HX] " + ", ".join(f"{e} {cell[e]['hx']['hedged']['worst']:.0e}/{cell[e]['hx']['unhedged']['worst']:.0e}" for e in EXIT_NAME.values())
              + f"; complement {comp['events']:,} events, mirror {mirr['events']:,} ({time.time() - t0:.0f}s)", flush=True)
    del F10

    # ---- print ----
    print("\n" + "=" * 160)
    print("THE LOSER-COHORT RALLY SHORT -- every event taken short at the next open, no slot cap, hedged by the floored market; bp per TRADE (complement = the spike "
          "outside the cohort, short; mirror = the winners' fresh dip, LONG)")
    print("=" * 160)
    hdr = "  %-16s %-6s %7s %6s %7s %7s %6s %5s | %6s %6s %6s %5s | %7s %7s | %7s | %7s %7s %6s" % (
        "arm", "exit", "events", "n", "mean", "median", "t", "hold", "2c PUB", "2c PB", "borrow", "HTB%", "netPUB", "netPB", "be hs/s", "era1", "era2", "down")
    print(hdr)

    def row(label, ex, d):
        b = d.get("borrow")
        nb = d.get("net_per_trade_borrow", d["net_per_trade"])
        print("  %-16s %-6s %7s %6d %+7.1f %+7.1f %+6.2f %5.1f | %6.1f %6.1f %6s %5s | %+7.1f %+7.1f | %7.1f | %+7.1f %+7.1f %6s" % (
            label, ex, "", d["trades"], d["mean_bp"], d["median_bp"], d["t"] or 0, d["hold_mean"], d["two_c"]["PUB"], d["two_c"]["PB"],
            ("%.1f" % b["mean_bp"]) if b else "-", ("%.1f" % (100 * b["htb_share"])) if b else "-", nb["PUB"], nb["PB"], d["breakeven_half_spread_bp_side"],
            d["era1_mean_bp"] or 0, d["era2_mean_bp"] or 0, ("%+.0f" % d["down_years_mean_bp"]) if d["down_years_mean_bp"] is not None else "-"))
    for nm in R:
        for e in EXIT_NAME.values():
            row(f"cell {nm}" + (" *" if nm == cell_name(*PRIMARY) and e == PRIMARY_EXIT else ""), e, R[nm][e]["per_trade"])
        for arm in ("complement", "mirror"):
            for e in EXIT_NAME.values():
                if e in R[nm][arm]:
                    row(f"  {arm} {nm}", e, R[nm][arm][e]["per_trade"])
    print("  netPUB/netPB = mean - 2c - borrow (short; the mirror's has no borrow); be hs/s = the held median half-spread (bp/side) at which the net after "
          "commission and borrow is zero; era1/era2/down = mean per trade in the era halves and the down-years")
    print("\n  DEPLOYED BASE (hedged, bp per BAR), 4-crossing line (G22.costed, pre-registered for event books) and the 2-crossing line beside (cost / 2):")
    print("  %-16s %-6s %5s %5s %6s | %7s %6s %7s %7s %7s | %6s %7s %7s | %7s %6s" % ("arm", "exit", "exp%", "pos", "ent/yr", "gross", "cost4", "net4PUB", "net4PB",
                                                                                   "Sh4PUB", "cost2", "net2PUB", "net2PB", "Sh2PUB", "be4 hs"))
    for nm in R:
        for e in EXIT_NAME.values():
            d = R[nm][e]["deployed"]
            h, hb, h2, hb2 = d["PUB"]["hedged"], d["PB"]["hedged"], d["PUB"]["hedged_2x"], d["PB"]["hedged_2x"]
            print("  %-16s %-6s %5.1f %5.1f %6.0f | %+7.2f %6.2f %+7.2f %+7.2f %+7.3f | %6.2f %+7.2f %+7.2f | %+7.3f %6.1f" % (
                f"cell {nm}", e, 100 * d["exposure"], d["mean_positions_deployed"], d["entries_per_year"], h["gross_bp"], h["cost_bp"], h["net_bp"], hb["net_bp"],
                h["sharpe_net"], h2["cost_bp"], h2["net_bp"], hb2["net_bp"], h2["sharpe_net"], h["breakeven_half_spread_bp_side"] or 0))
    print("\n  CONTROLS on the primary exit (cap 10), per trade bp: A' per-name rotation within elig; B same day / same rsi bucket / defined-percentile pool; "
          "B_c same day / same cohort; C random direction")
    print("  %-8s %5s %8s | %8s %8s %5s | %8s %8s %5s | %8s %8s %5s | %8s %8s %5s | %s" % ("cell", "draws", "observed", "A' p50", "A' p95", "above", "B p50", "B p95", "above",
                                                                                          "B_c p50", "B_c p95", "above", "C p50", "C p95", "above", "deployed net PUB: obs / A' p95 / B_c p95"))
    for nm in R:
        o, k, C = R[nm]["observed"], R[nm]["controls"], R[nm]["control_C"]
        if k is None:
            print("  %-8s %5d %+8.2f | A'/B/B_c not run %s | C %+8.2f %+8.2f %5s |" % (nm, 0, o["trade_mean_bp"], " " * 50, C["p50"], C["p95"], "yes" if C["above"] else "NO"))
            continue
        a, b, bc = k["A_prime"]["trade_mean_bp"], k["B"]["trade_mean_bp"], k["B_c"]["trade_mean_bp"]
        print("  %-8s %5d %+8.2f | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+.2f / %+.2f / %+.2f" % (
            nm, k["draws"], o["trade_mean_bp"], a["p50"], a["p95"], "yes" if a["above"] else "NO", b["p50"], b["p95"], "yes" if b["above"] else "NO",
            bc["p50"], bc["p95"], "yes" if bc["above"] else "NO", C["p50"], C["p95"], "yes" if C["above"] else "NO",
            o["net_bp_PUB"], k["A_prime"]["net_bp_PUB"]["p95"], k["B_c"]["net_bp_PUB"]["p95"]))
    pn = cell_name(*PRIMARY)
    g4 = R[pn][PRIMARY_EXIT]["per_trade"]["four_groups"]
    tt = g4["top_trade"]
    print(f"\n  FOUR GROUPS per trade (primary {pn}, cap 10, short): n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
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
    acc = R[pn]["accounting"]
    print(f"      check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; "
          f"trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    print(f"\n  SPLITS (cap 10): per trade era1 / era2 / down-years [n], and the deployed hedged net PUB bp/bar [bars]; down-years {P['down_years']}")
    for nm in R:
        tr = R[nm][PRIMARY_EXIT]["per_trade"]
        s_ = R[nm][PRIMARY_EXIT]["deployed"]["splits_hedged"]
        fmt = lambda x: (f"{x['PUB']['net_bp']:+.2f}[{x['bars']}]" if "PUB" in x else f"-[{x['bars']}]")
        print(f"  {nm:8s} per trade era1 {tr['era1_mean_bp'] or 0:+.1f} [{tr['era1_n']}] era2 {tr['era2_mean_bp'] or 0:+.1f} [{tr['era2_n']}] down {tr['down_years_mean_bp'] or 0:+.1f} "
              f"[{tr['down_years_n']}] | deployed era1 {fmt(s_['era1'])} era2 {fmt(s_['era2'])} down {fmt(s_['down_years'])}")
        print("      by year (per trade mean [n]): " + " ".join(f"{y}:{v['mean_bp']:+.0f}[{v['n']}]" for y, v in sorted(tr["by_year"].items())))
    print("\n  INTERACTION with the rsi bucket of the trigger name at entry (cap 10): b[n] mean per trade / short forward-10 base rate / interaction "
          "(E_sb - E_b - E_s + E_all)")
    for nm in R:
        it = R[nm]["interaction"]
        print(f"  {nm:8s} E_all {it['E_all']:+.1f}: " + " ".join(f"b{b}[{v['n']}] {v['mean_bp']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(it["buckets"].items()))
              + f"; undefined {it['undefined_n']}")
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")
    print("\n  STAGE 0 (data): bottom_10 " + " ".join(f"{k} {S0['bottom_10'][k]['bp']:+.3f}" for k in ("span", "era1", "era2", "down_years"))
          + "; top_10 " + " ".join(f"{k} {S0['top_10'][k]['bp']:+.3f}" for k in ("span", "era1", "era2")) + " bp/bar")

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q = {}
    b10, top = S0["bottom_10"], S0["top_10"]
    q["Q0"] = bool(b10["span"]["bp"] < 0 and b10["era1"]["bp"] < 0 and b10["era2"]["bp"] < 0 and top["span"]["bp"] > 0)
    pr = R[pn][PRIMARY_EXIT]["per_trade"]
    k = R[pn]["controls"]
    C = R[pn]["control_C"]
    q["Q1"] = bool(pr["mean_bp"] > 0 and k is not None and k["A_prime"]["trade_mean_bp"]["above"] and k["B_c"]["trade_mean_bp"]["above"] and C["above"])
    q["Q2"] = bool(k is not None and k["A_prime"]["trade_mean_bp"]["p50"] <= 0)
    comp10 = R[pn]["complement"][PRIMARY_EXIT]["per_trade"]
    q["Q3"] = bool(comp10["mean_bp"] <= pr["mean_bp"] - 10.0)
    q["Q4"] = bool(pr["net_per_trade_borrow"]["PUB"] > 0)
    inv = R[pn]["inv10"]["per_trade"]
    q["Q5"] = bool(inv["mean_per_bar_held_bp"] > pr["mean_per_bar_held_bp"])
    mir10 = R[pn]["mirror"][PRIMARY_EXIT]["per_trade"]
    q["Q6"] = bool(mir10["mean_bp"] > 0)
    m_ = lambda c, s: R[cell_name(c, s)][PRIMARY_EXIT]["per_trade"]["mean_bp"]
    q["Q7"] = bool(all(m_(20, s) < m_(10, s) for s in (90, 95)))
    q["Q8"] = bool(pr["borrow"]["htb_share"] > 0.10)
    q["check_G"] = True
    print("\nPREDICTIONS (primary cell (10, 90), cap 10, short, bp per trade unless stated)")
    print(f"  Q0 (premise) bottom-decile hedged drift < 0 over the span and both eras, top decile > 0: {v_(q['Q0'])} -- bottom_10 span {b10['span']['bp']:+.3f} "
          f"era1 {b10['era1']['bp']:+.3f} era2 {b10['era2']['bp']:+.3f}; top_10 span {top['span']['bp']:+.3f} (era1 {top['era1']['bp']:+.3f} era2 {top['era2']['bp']:+.3f}) bp/bar")
    print(f"  Q1 (LOAD-BEARING) mean per trade > 0 and above p95 of A', B_c and C: {v_(q['Q1'])} -- observed {pr['mean_bp']:+.2f} ({pr['trades']:,} trades)"
          + (f"; A' p95 {k['A_prime']['trade_mean_bp']['p95']:+.2f} (p50 {k['A_prime']['trade_mean_bp']['p50']:+.2f}), B_c p95 {k['B_c']['trade_mean_bp']['p95']:+.2f} "
             f"(p50 {k['B_c']['trade_mean_bp']['p50']:+.2f}), B p95 {k['B']['trade_mean_bp']['p95']:+.2f} at {k['draws']} draws" if k else "; A'/B/B_c NOT RUN (falsified by absence)")
          + f"; C p95 {C['p95']:+.2f}")
    print(f"  Q2 A' centred at or below zero (p50 <= 0 in short P&L): {v_(q['Q2'])} -- " + (f"A' p50 {k['A_prime']['trade_mean_bp']['p50']:+.2f}" if k else "not run"))
    print(f"  Q3 the complement's mean at least 10 bp below the primary's: {v_(q['Q3'])} -- complement {comp10['mean_bp']:+.2f} ({comp10['trades']:,}) vs primary "
          f"{pr['mean_bp']:+.2f}, gap {pr['mean_bp'] - comp10['mean_bp']:+.2f}")
    print(f"  Q4 (against) nets > 0 per trade after the PUB 2c and borrow, cap 10: {v_(q['Q4'])} -- mean {pr['mean_bp']:+.2f} - 2c PUB {pr['two_c']['PUB']:.2f} - borrow "
          f"{pr['borrow']['mean_bp']:.2f} = {pr['net_per_trade_borrow']['PUB']:+.2f} (PB {pr['net_per_trade_borrow']['PB']:+.2f}); be hs/s {pr['breakeven_half_spread_bp_side']:.1f}")
    print(f"  Q5 invalidation-10's mean per bar held exceeds cap 10's: {v_(q['Q5'])} -- inv {inv['mean_per_bar_held_bp']:+.3f} ({inv['mean_bp']:+.2f} / {inv['hold_mean']:.2f} bars) "
          f"vs cap {pr['mean_per_bar_held_bp']:+.3f} ({pr['mean_bp']:+.2f} / {pr['hold_mean']:.2f})")
    print(f"  Q6 the mirror (winners' fresh dip, long) has mean per trade > 0: {v_(q['Q6'])} -- {mir10['mean_bp']:+.2f} ({mir10['trades']:,} trades)")
    print(f"  Q7 c = 20 earns less per trade than c = 10 at the same s: {v_(q['Q7'])} -- " + "; ".join(f"s={s}: {m_(20, s):+.2f} vs {m_(10, s):+.2f}" for s in (90, 95)))
    print(f"  Q8 HTB share of the primary cell's trades > 10%: {v_(q['Q8'])} -- {100 * pr['borrow']['htb_share']:.2f}% ({pr['borrow']['htb_n']:,} of {pr['trades']:,})")
    print(f"  check: with the cohort dropped the (., 90) events equal D352's rev_5/S10 row ({g['spike90_events']:,} events, grid statistic to 1e-9) and the kernel "
          f"reproduces D352's stored cap-40 short mean on {D352_KERNEL_REF} to 1e-9; D352 stored no kernel number for rev_5/S10 -- its cap-40 short mean here "
          f"{g['spike90_cap40_short']['mean_bp']:+.2f} bp on {g['spike90_cap40_short']['trades']:,} trades: {v_(q['check_G'])}")
    out = dict(note="D359: the bear-market rally short -- a fresh rev_5 spike inside the mom_252_21 loser cohort, four cells, three exits, every event taken short, "
                    "hedged by the floored market; complement and mirror beside; A', B, B_c, C on the primary exit; borrow in the net. Per-trade numbers are bp per "
                    "TRADE and never compared to per-bar numbers. Nothing is a book; nothing promoted.",
               study=STUDY, cells=[cell_name(c, s) for c, s in CELLS], primary=cell_name(*PRIMARY), primary_exit=PRIMARY_EXIT, exits=list(EXIT_NAME.values()),
               scores=dict(cohort=MOM, spike=REV), U=U_SLOTS, x_target=X_TARGET, down_years=P["down_years"], floored_market_by_year=P["yr_ret"], m_start=P["m_start"],
               seeds=dict(A=[SEED, STUDY, "cell_index", ARM["A"], "part"], B=[SEED, STUDY, "cell_index", ARM["B"], "part"], Bc=[SEED, STUDY, "cell_index", ARM["Bc"], "part"],
                          C=[SEED, STUDY, "cell_index", ARM["C"]]),
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), G=g, stage0=S0, results=R, predictions=q)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['report']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--cell", metavar="C:S", help="e.g. 10:90 -- the A'/B/B_c controls for one cell on the primary exit")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; the smoke runs pass a temp/ directory)")
    a = ap.parse_args()
    print("D359  the bear-market rally short -- a fresh rev_5 spike inside the mom_252_21 loser cohort, entered short")
    paths = out_paths(a.out_dir)
    # F (the cached forward-40 grid, mmapped) is read only by [G]'s grid-statistic check (selftest, report); the other stages run as D358 did.
    P = PREP.prep(need_grids=(a.selftest or a.report))
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))                # what V49.event_buckets reads (D352's floor_sets)
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.stage0:
        stage_stage0(P, paths)
    elif a.cell:
        c, s = (int(x) for x in a.cell.split(":"))
        assert (c, s) in CELLS, f"cell must be one of {[cell_name(c_, s_) for c_, s_ in CELLS]}"
        stage_cell(P, c, s, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --stage0, --cell C:S, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
