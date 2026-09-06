"""D353 -- rev_5 entering the bottom decile: the full record on the event lens, and the slot-capped event book hedged.

    uv run python scripts/run_d353_rev5_record.py --selftest
    uv run python scripts/run_d353_rev5_record.py --controls --draws 100 --part 1          A' and B, part >= 1 (part 0 is D350's file)
    uv run python scripts/run_d353_rev5_record.py --variant --draws 100 --part 0 [--k 2|4] the slot-capped event book + A' null per K
    uv run python scripts/run_d353_rev5_record.py --report

Pre-registration: docs/decisions/D353-rev-5-entering-the-bottom-decile-the-full-record.md

The event is D350's rev_5/E1 member exactly (member_dense: floored, deal-filtered, warm-based, lagged, cross-sectional
percentile; pct <= 10 and prev > 10 on eligible bars): 72,677 events, 27,316 cap-exit trades, observed +43.4 bp.

Invariant lens: every event taken, D347's kernel, arms (long, mirror) x (cap, invalidation, target), both hedges, PUB/PB
per trade, the splits, the four groups, the rsi-bucket interaction; controls A' (per-name time rotation within elig,
D351), B (same day, same rsi bucket, a random name from the defined-percentile pool), C (random direction, 1,000).
Part 0 of A' and B is D350's stored file (control_A_elig, control_B); part 1 adds 100 draws here.

Variant lens: EB.simulate_event(n_max=K) for K in (2, 4), cap and invalidation exits, ONE-SIDED (long only), scored on
the HEDGED capital series the additive kernel option returns (book_dep_x, book_tot_x): G22.costed on the deployed base
(as the slot books are scored), EB.costed_event's total arithmetic (entries / bars / U) on the total base -- G22.costed's
turnover is entries / mean-held / bars, the deployed basis, so it is not applied to the total series. Null: A' re-simulated
at the same K.  D346's rev_5 slot-book cell is printed beside it: the ranking construction on the same score, never on the
same statistic.

ASSERTIONS [K][F0][R][F][G][ID][KX][HX][A'][B][C][P][S][X][V][6] -- pre-reg section 6.
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
V50 = _load("d350r", "run_d350_long_timing_screen.py")      # its own _load("d348p") is memoised to PREP
V47 = PREP.V47
EB, G22, FL = PREP.EB, PREP.G22, PREP.FL
SEED, CAP, X_TARGET = V47.SEED, V47.CAP, V47.X_TARGET
CONVS = V47.CONVS
STUDY = 353
MEMBER = "rev_5/E1"
D350_EVENTS, D350_TRADES = 72_677, 27_316
EXITS = ("cap", "invalidation", "target")
KS = (2, 4)
U_SLOTS = 4
D350_P0 = REPO / "data" / "d350_ctrl_rev_5-E1_p0.json"
D347_HIST_P0 = REPO / "data" / "d347_ctrl_hist_L_p0.json"
D346_JSON = REPO / "data" / "d346_legs_floor_open.json"
D350_SCREEN = REPO / "data" / "d350_screen.json"
CTRL = REPO / "data" / "d353_ctrl_p{part}.json"
VAR = REPO / "data" / "d353_variant_k{K}_p{part}.json"
OUT = REPO / "data" / "d353_rev5_record.json"
clean = V50.clean


# ------------------------------------------------------------------ the event and the kernel
def event(P):
    elig = np.array(P["elig"])
    lo, hi, sc = V50.member_dense(P, MEMBER, elig)
    return lo, hi, sc, elig


def run(P, sl, ss, sc, exit_):
    return V47.run_events(P, sl, ss, sc, exit_)


def pnl_bp(res):
    return V47.pnl_bp(res)


def zeros(x):
    return np.zeros_like(x)


def aprime_draw(lo, hi, sc, elig, rng):
    """A' (D351): per-name time rotation within elig; D351's two assertions."""
    sl, ss, sc_ = EB.rotate_signals(lo, hi, sc, elig, rng)
    assert not (sl & ~elig).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(sl.sum(axis=0), lo.sum(axis=0)), "[A'] per-name event count changed"
    return sl, ss, sc_


def b_pool_P(P, elig):
    """Control B's pool: eligible names with a DEFINED rsi percentile (D352's [B]; np.digitize puts NaN in bucket 9)."""
    return dict(P, elig=elig & np.isfinite(np.asarray(P["PCT"]["rsi"])))


def b_shortfall(PB, lo):
    """Events the pool cannot replace, counted the declared way: per (day, bucket), max(0, events - pool)."""
    bucket, el = PB["bucket_rsi"], PB["elig"]
    short = 0
    for t in np.flatnonzero(lo.any(axis=1)):
        ev = np.flatnonzero(lo[t])
        pool = np.flatnonzero(el[t] & ~lo[t])
        b_ev, b_pool = bucket[t, ev], bucket[t, pool]
        for b in np.unique(b_ev):
            short += max(0, int((b_ev == b).sum()) - int((b_pool == b).sum()))
    return short


def recompute_trade(P, row, e0, age, side):
    """D351's: the open-fill hedged excess of one trade against the floored market, independently of the kernel."""
    ocT, mkt_oc, r1T, m_f = P["ocT"], P["m_f_oc"], P["r1T"], P["m_f"]
    ex = ocT[e0, row] - mkt_oc[e0]
    for j in range(1, age):
        v = r1T[e0 + j, row]
        if np.isfinite(v):
            ex += v - m_f[e0 + j]
    return ex if side == 0 else -ex


def assert_S(P, tr, rng, k=300, tol=1e-9, tag="[S]"):
    """Sign in money: k sampled trades equal the open-fill recomputation; favourable paths pay positively (long) /
    a name that rises against the market pays negatively (short)."""
    pick = rng.choice(len(tr), size=min(k, len(tr)), replace=False)
    worst, n_fav = 0.0, 0
    for p in pick:
        row, e0, age, pnl, sd = tr[p]
        rec = recompute_trade(P, row, e0, age, sd)
        worst = max(worst, abs(pnl - rec))
        ex = rec if sd == 0 else -rec                           # the name's own hedged excess, side-free
        if ex > 0:
            assert (pnl > 0) if sd == 0 else (pnl < 0), f"{tag} a favourable path pays the wrong way (side {sd})"
            n_fav += 1
        elif ex < 0:
            assert (pnl < 0) if sd == 0 else (pnl > 0), f"{tag} an adverse path pays the wrong way (side {sd})"
    assert worst < tol, f"{tag} {worst:.2e}"
    return worst, int(pick.size), n_fav


# ------------------------------------------------------------------ the hedged series: [HX]
def hx_rebuild(res, P):
    """Per-bar hedged sum rebuilt from the ledger: (row, e0, age, pnl, side) -> sgn * (v - m) on bars e0 .. e0 + age - 1,
    the entry bar on ocT / m_f_oc, later bars on r1T / m_f. Returns (rebuilt sum, rebuilt position count)."""
    r1T, ocT, m_f, m_oc = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"]
    T = res["held"].size
    reb, cnt = np.zeros(T), np.zeros(T, np.int64)
    for row, e0, age, _p, side in res["trades"]:
        sgn = 1.0 if side == 0 else -1.0
        v = np.array(r1T[e0:e0 + age, row], dtype=float)
        mm = np.array(m_f[e0:e0 + age], dtype=float)
        v[0], mm[0] = ocT[e0, row], m_oc[e0]
        reb[e0:e0 + age] += sgn * (v - mm)
        cnt[e0:e0 + age] += 1
    return reb, cnt


def assert_HX(res, P, key="book_dep_x", tol=1e-12):
    """The deployed series times positions held equals the ledger summed per bar on every bar the ledger covers. Positions
    still open at the last bar are in the series and not in the ledger; they are held contiguously from entry to T-1, so
    the uncovered bars must be exactly the tail [first uncovered, T) -- asserted, counted, excluded."""
    reb, cnt = hx_rebuild(res, P)
    held = res["held"].astype(np.int64)
    T = held.size
    assert (cnt <= held).all(), "[HX] the ledger claims a position the book never held"
    covered = cnt == held
    unc = np.flatnonzero(~covered)
    if unc.size:
        assert np.array_equal(unc, np.arange(unc[0], T)), "[HX] uncovered bars are not the open tail"
    with np.errstate(invalid="ignore"):
        signed = np.where(held > 0, np.nan_to_num(np.asarray(res[key], float)) * held, 0.0)
    assert np.isfinite(reb).all(), "[HX] a rebuilt bar is not finite"
    worst = float(np.abs(signed[covered] - reb[covered]).max())
    assert worst < tol, f"[HX] {key}: series x held != ledger per bar: {worst:.2e}"
    pnl_sum = float(sum(t[3] for t in res["trades"]))
    assert abs(float(reb.sum()) - pnl_sum) < 1e-9, "[HX] the per-bar rebuild does not sum to the ledger"
    return dict(worst=worst, covered=int(covered.sum()), uncovered=int(unc.size), open_at_end=int(held[-1] - cnt[-1]),
                first_uncovered=int(unc[0]) if unc.size else None)


def assert_series_defs(res):
    """book_dep_x and book_tot_x are the declared functions of signed_x (exact)."""
    sx, held, U = res["signed_x"], res["held"], float(res["U"])
    assert np.array_equal(res["book_dep_x"], np.where(held > 0, sx / np.maximum(held, 1), np.nan), equal_nan=True), "[HX] book_dep_x definition"
    assert np.array_equal(res["book_tot_x"], np.where(res["defined"], sx / U, np.nan), equal_nan=True), "[HX] book_tot_x definition"


# ------------------------------------------------------------------ the invariant lens: per-arm statistics (D350's block)
def arm_stats(P, tr, pnl, elig, E_b=None, E_all=None, rngC=None, with_interaction=False):
    r1T, ocT, m_f, m_f_oc, beta = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["beta"]
    HALF, CLOSE, years, T = P["HALF"], P["CLOSE"], P["years"], P["T"]
    bucket_rsi = np.asarray(P["bucket_rsi"])
    down = set(P["down_years"])
    half = T // 2
    pb = V47.pnl_beta_adjusted(tr, r1T, m_f, ocT, m_f_oc, beta) * 1e4
    yrs = np.array([years[t[1]] for t in tr])
    eras = np.array([t[1] < half for t in tr])
    c2 = {cv: V47.two_c(tr, HALF[cv], CLOSE) for cv in CONVS}
    px = c2["PUB"][2]
    mean = float(pnl.mean())
    hold = float(np.mean([t[2] for t in tr]))
    d_ = dict(trades=len(tr), mean_bp=mean, median_bp=float(np.median(pnl)),
              t=float(mean / (pnl.std(ddof=1) / np.sqrt(pnl.size))), share_pos=float((pnl > 0).mean()), hold_mean=hold,
              mean_per_bar_held_bp=mean / hold,
              beta_adj_mean_bp=float(np.nanmean(pb)), beta_median=float(np.nanmedian([beta[t[1], t[0]] for t in tr])),
              two_c={cv: c2[cv][0] for cv in CONVS}, net_per_trade={cv: mean - c2[cv][0] for cv in CONVS},
              held_half={cv: c2[cv][1] for cv in CONVS}, held_price=px,
              # 2c = 2 hs + 2 x 0.005 / px x 1e4 per side-pair, so the half-spread at which the mean nets zero:
              breakeven_half_spread_bp_side=(mean - 2.0 * 0.005 / px * 1e4) / 2.0,
              down_years_mean_bp=(float(pnl[np.isin(yrs, list(down))].mean()) if np.isin(yrs, list(down)).any() else None),
              down_years_n=int(np.isin(yrs, list(down)).sum()),
              era1_mean_bp=float(pnl[eras].mean()) if eras.any() else None, era2_mean_bp=float(pnl[~eras].mean()) if (~eras).any() else None,
              era1_n=int(eras.sum()), era2_n=int((~eras).sum()),
              by_year={int(y): float(pnl[yrs == y].mean()) for y in np.unique(yrs)},
              four_groups=V50.four_groups(tr, pnl, P, elig))
    if with_interaction:
        b_ev = np.array([bucket_rsi[t[1], t[0]] for t in tr])
        inter, tot = {}, 0.0
        for b in range(10):
            mb = b_ev == b
            if mb.any():
                Esb = float(pnl[mb].mean())
                inter[b] = dict(n=int(mb.sum()), E_sb=Esb, E_b=E_b[b], interaction=Esb - E_b[b] - mean + E_all)
                tot += mb.sum() * (Esb - mean)
        assert abs(tot) < 1e-9 * max(1.0, float(np.abs(pnl).sum())), f"[X] {tot}"
        assert sum(v["n"] for v in inter.values()) == len(tr), "[X] the buckets do not partition the trades"
        d_["interaction"] = inter
        d_["interaction_identity"] = float(tot)
        signs = rngC.choice([-1.0, 1.0], size=(1000, pnl.size))
        cC = (signs * pnl[None, :]).mean(axis=1)
        d_["control_C"] = dict(p50=float(np.median(cC)), p95=float(np.quantile(cC, .95)), max=float(cC.max()), draws=1000,
                               above=bool(mean > np.quantile(cC, .95)))
    return d_


def base_rates(P, elig):
    F = P["F"]
    bucket_rsi = np.asarray(P["bucket_rsi"])
    Fm = elig & np.isfinite(F)
    E_all = float(np.nanmean(F[Fm])) * 1e4
    E_b = {}
    for b in range(10):
        mb = Fm & (bucket_rsi == b)
        E_b[b] = float(np.nanmean(F[mb])) * 1e4 if mb.any() else np.nan
    return E_all, E_b


# ------------------------------------------------------------------ the variant lens: the slot-capped event book, hedged
def simulate_variant(P, sl, ss, sc, exit_, K):
    return EB.simulate_event(P["A3"], sl, ss, sc, exit=exit_, cap=CAP, n_max=K, x_target=X_TARGET, U=U_SLOTS, hedged_series=True)


def score_variant(res, P, K):
    """G22.costed on the hedged DEPLOYED series (the slot books' scoring), EB.costed_event's TOTAL arithmetic on the hedged
    total series; the two deployed costings are asserted equal."""
    defined, dep_mask, held = res["defined"], res["mask_dep"], res["held"]
    ent, skipped = int(res["ent"].sum()), int(res["skipped"].sum())
    assert int(res["cnt0"].max()) <= K and int(res["cnt1"].max()) == 0, f"[V] holds {int(res['cnt0'].max())} > K={K}"
    assert ent == len(res["trades"]) + int(held[-1]), "[V] entries != closed trades + open at the end"
    pnl = pnl_bp(res)
    out = dict(K=K, exit=res["exit"], trades=len(res["trades"]), entries=ent, skipped=skipped,
               skipped_share=skipped / max(ent + skipped, 1), max_positions=int(res["cnt0"].max()),
               exposure=float(dep_mask[defined].mean()), mean_positions=float(held[defined].mean()),
               mean_positions_deployed=float(held[dep_mask].mean()), bars_defined=int(defined.sum()), bars_deployed=int(dep_mask.sum()),
               trade_mean_bp=float(pnl.mean()), trade_median_bp=float(np.median(pnl)), hold_mean=float(np.mean([t[2] for t in res["trades"]])),
               open_at_end=int(held[-1]))
    hres = dict(res, book_dep=res["book_dep_x"], book_tot=res["book_tot_x"])
    for cv in CONVS:
        dep = G22.costed(dict(res, book=res["book_dep_x"], mask=dep_mask), P["G4"][cv])
        ce = EB.costed_event(hres, P["HALF"][cv], P["CLOSE"], P["DV"])
        for k in ("gross_bp", "net_bp", "vol_bp", "sharpe_gross", "sharpe_net", "maxdd_bp", "turnover", "cost_bp"):
            assert abs(dep[k] - ce["deployed"][k]) < 1e-9, f"G22.costed and costed_event disagree on deployed {k}"
        out[cv] = dict(deployed=dep, total=ce["total"], two_c_bp=ce["two_c_bp"], held_half_spread=ce["held_half_spread"],
                       held_price=ce["held_price"], trade_net_mean_bp=ce["trade_net_mean_bp"])
    return out


def null_stats(res, P):
    """Per A' draw: gross bp/bar, PUB net bp/bar and PUB net Sharpe on the hedged DEPLOYED base (+ PB net, total gross beside)."""
    dep = {cv: G22.costed(dict(res, book=res["book_dep_x"], mask=res["mask_dep"]), P["G4"][cv]) for cv in CONVS}
    bt = res["book_tot_x"][res["defined"]]
    return dict(gross_bp=dep["PUB"]["gross_bp"], net_PUB=dep["PUB"]["net_bp"], sharpe_net_PUB=dep["PUB"]["sharpe_net"],
                net_PB=dep["PB"]["net_bp"], gross_tot_bp=float(bt.mean()) * 1e4, trades=len(res["trades"]))


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    T, n, r1T, finT, ocT, m_f, m_f_oc = P["T"], P["n"], P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"]
    rng = np.random.default_rng([SEED, STUDY, 0])
    # [F] the forward grid equals a direct per-cell recomputation (D350's loop)
    F = P["F"]
    elig = np.array(P["elig"])
    cells = np.argwhere(np.isfinite(F) & elig)
    sample = cells[rng.choice(len(cells), size=3000, replace=False)]
    worst_f = 0.0
    for t, i in sample:
        v = np.array(r1T[t:t + CAP, i], float)
        mm = np.array(m_f[t:t + CAP], float)
        v[0], mm[0] = ocT[t, i], m_f_oc[t]
        okk = finT[t:t + CAP, i] & np.isfinite(v) & np.isfinite(mm)
        okk[0] = True
        worst_f = max(worst_f, abs(float(np.sum(np.where(okk, v - mm, 0.0))) - F[t, i]))
    assert worst_f < 1e-9, f"[F] {worst_f:.2e}"
    print(f"    [F] the forward-40 grid equals a direct per-cell recomputation on 3,000 sampled cells to {worst_f:.1e}")
    # [G] the event matrix equals D350's rev_5/E1 member exactly
    lo, hi, sc, elig = event(P)
    assert int(lo.sum()) == D350_EVENTS, f"[G] {int(lo.sum())} events"
    sp = V50.score_events(P, "rev_5", elig)["E1"]                               # D350's sparse path, independently
    t_d, i_d = np.nonzero(lo)
    assert np.array_equal(sp[0], t_d) and np.array_equal(sp[1], i_d), "[G] dense member != D350's sparse events"
    pct = V47.percentile_grid(V50.lagged(P, "rev_5"))
    assert np.array_equal(sc, pct, equal_nan=True) and sc is not pct, "[G] the kernel's score is not the percentile grid"
    prev = np.full_like(pct, np.nan)
    prev[1:] = pct[:-1]
    with np.errstate(invalid="ignore"):
        lo2 = (pct <= V47.DECILE) & (prev > V47.DECILE) & elig                    # D347's `lo`, verbatim
        hi2 = (pct >= 100.0 - V47.DECILE) & (prev < 100.0 - V47.DECILE) & elig
    assert np.array_equal(lo, lo2) and np.array_equal(hi, hi2), "[G] member != D347's event rule"
    p0 = json.loads(D350_P0.read_text())
    assert p0["events"] == D350_EVENTS and p0["member"] == MEMBER, "[G] D350's stored file"
    del pct, prev, lo2, hi2
    print(f"    [G] {MEMBER}: {int(lo.sum()):,} events == D350's member (dense == D350's sparse score_events; == D347's rule on the percentile "
          f"grid; == the stored file's {p0['events']:,}); mirror {int(hi.sum()):,} ({el()})")
    # [ID] the kernel reproduces D350's trades and observed
    res = run(P, lo, zeros(lo), sc, "cap")
    pnl = pnl_bp(res)
    obs = float(pnl.mean())
    assert len(res["trades"]) == D350_TRADES and p0["trades"] == D350_TRADES, f"[ID] {len(res['trades'])} trades"
    assert abs(obs - p0["observed"]) < 1e-9, f"[ID] observed {obs} vs stored {p0['observed']}"
    print(f"    [ID] the kernel reproduces D350's {len(res['trades']):,} cap-exit trades and observed {obs:+.4f} bp (stored {p0['observed']:+.4f}, "
          f"diff {abs(obs - p0['observed']):.1e}) ({el()})")
    # [KX] the additive option: (a) D347's hist_L control-A part 0, first 3 draws, by its own code path and seed
    cs = json.loads(D347_HIST_P0.read_text())
    loH, hiH, scH = P["EVENTS"]["hist_L"]
    loH, hiH, scH = np.asarray(loH), np.asarray(hiH), np.asarray(scH)
    resH = run(P, loH, zeros(loH), scH, "cap")
    obsH = float(pnl_bp(resH).mean())
    assert obsH == cs["observed"] and len(resH["trades"]) == cs["trades"], f"[KX] hist_L observed {obsH} vs {cs['observed']}"
    rngH = np.random.default_rng([SEED, 347, 1, V47.SIGNALS.index("hist_L"), 0])
    worst_a = 0.0
    for d in range(3):
        sl_, ss_, sc_ = V47.rotate_confined(P, loH, hiH, scH, rngH)
        m = float(pnl_bp(run(P, sl_, zeros(loH), sc_, "cap")).mean())
        worst_a = max(worst_a, abs(m - cs["control_A"][d]))
    assert worst_a == 0.0, f"[KX] (a) D347 hist_L control A not reproduced to 0.0: {worst_a:.2e}"
    # (b) D350's rev_5/E1 kernel stage: observed and trade count to 0.0
    assert obs == p0["observed"] and len(res["trades"]) == p0["trades"], f"[KX] (b) rev_5 observed {obs!r} vs stored {p0['observed']!r}"
    # (c) with and without the option: every common key equal, the trades list equal
    def kx_compare(n_max, exit_):
        a = EB.simulate_event(P["A3"], lo, zeros(lo), sc, exit=exit_, cap=CAP, n_max=n_max, x_target=X_TARGET, U=U_SLOTS)
        b = EB.simulate_event(P["A3"], lo, zeros(lo), sc, exit=exit_, cap=CAP, n_max=n_max, x_target=X_TARGET, U=U_SLOTS, hedged_series=True)
        assert set(b) - set(a) == {"signed_x", "book_dep_x", "book_tot_x"}, f"[KX] added keys {set(b) - set(a)}"
        assert set(a) <= set(b)
        for k in a:
            if isinstance(a[k], np.ndarray):
                assert a[k].dtype == b[k].dtype and np.array_equal(a[k], b[k], equal_nan=(a[k].dtype.kind == "f")), f"[KX] {k} differs"
            elif k == "trades":
                assert a[k] == b[k], "[KX] trades differ"
            else:
                assert a[k] == b[k], f"[KX] {k} differs"
        assert not np.array_equal(a["book_dep"], b["book_dep_x"], equal_nan=True), "[KX] the hedged series equals the raw one"
        return a, b
    kx_compare(None, "cap")
    _ra, rb2 = kx_compare(2, "cap")
    print(f"    [KX] with the hedged-series option: (a) D347's hist_L control-A part 0 first 3 draws reproduce from its seed by its own code path "
          f"to {worst_a:.1e} (observed {obsH:+.4f} == stored); (b) D350's rev_5/E1 observed and {len(res['trades']):,} trades equal the stored "
          f"file to 0.0; (c) simulate_event with and without hedged_series=True on rev_5 (n_max None and 2, cap): every common key "
          f"array_equal (NaN-equal), trades lists equal; the option adds signed_x/book_dep_x/book_tot_x only ({el()})")
    # [HX] the hedged series reconcile to the ledger per bar, K=2 and K=4 on both exits, and on the invariant run
    lines = []
    for K in KS:
        for exit_ in ("cap", "invalidation"):
            rv = simulate_variant(P, lo, zeros(lo), sc, exit_, K)
            assert_series_defs(rv)
            h = assert_HX(rv, P)
            lines.append(f"K={K}/{exit_} {h['worst']:.1e} ({h['covered']:,} bars covered, tail of {h['uncovered']} excluded, "
                         f"{h['open_at_end']} open at the end)")
    rinv = EB.simulate_event(P["A3"], lo, zeros(lo), sc, exit="cap", cap=CAP, n_max=None, x_target=X_TARGET, U=U_SLOTS, hedged_series=True)
    assert_series_defs(rinv)
    hinv = assert_HX(rinv, P)
    print(f"    [HX] book_dep_x x n_held equals the ledger's sgn(v - m) summed per bar to 1e-12 on every covered bar, and book_tot_x = signed_x / U "
          f"exactly: " + "; ".join(lines) + f"; invariant cap {hinv['worst']:.1e} ({hinv['uncovered']} tail bars excluded); the per-bar rebuild "
          f"sums to the ledger to 1e-9 ({el()})")
    # [A'] and [S] on an A' ledger; [V] on the variant
    rngA = np.random.default_rng([SEED, STUDY, 1, 0])
    for d in range(2):
        sl, ss, sc_ = aprime_draw(lo, hi, sc, elig, rngA)
        rA = run(P, sl, zeros(lo), sc_, "cap")
        pa = pnl_bp(rA)
        assert np.isfinite(pa).all(), "[A'] NaN P&L"
    print(f"    [A'] 2 draws keep every name's event count, every rotated event is eligible, no NaN; {len(rA['trades']):,} trades, "
          f"mean {pa.mean():+.2f} bp (observed {obs:+.2f}) ({el()})")
    worst_s, n_s, n_fav = assert_S(P, rA["trades"], np.random.default_rng([SEED, STUDY, 2]))
    resM = run(P, zeros(hi), hi, sc, "cap")
    worst_m, n_m, n_fav_m = assert_S(P, resM["trades"], np.random.default_rng([SEED, STUDY, 2, 1]))
    print(f"    [S] SIGN IN MONEY: {n_s} sampled A' trades equal the open-fill recomputation against the floored market to {worst_s:.1e}; "
          f"favourable paths pay positively ({n_fav} of {n_s}); on the mirror ledger ({len(resM['trades']):,} short trades) {n_m} sampled equal "
          f"-(excess) to {worst_m:.1e} and a name rising against the market pays negatively")
    # [B]
    PB = b_pool_P(P, elig)
    rngB = np.random.default_rng([SEED, STUDY, 2, 0])
    sigB = V47.control_b_signal(PB, lo, rngB)
    bucket = np.asarray(P["bucket_rsi"])
    assert np.array_equal(sigB.sum(axis=1), lo.sum(axis=1)), "[B] dates changed"
    assert sorted(bucket[lo].tolist()) == sorted(bucket[sigB].tolist()), "[B] bucket multiset changed"
    pct_ok = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    assert not (sigB & ~lo & ~pct_ok).any(), "[B] a replacement has no defined rsi percentile"
    assert not (sigB & ~lo & ~elig).any(), "[B] a replacement is ineligible"
    kept = int((sigB & lo).sum())
    short = b_shortfall(PB, lo)
    assert kept == short, f"[B] kept {kept} != pool shortfall {short}"
    rB = run(P, sigB, zeros(lo), sc, "cap")
    pB = pnl_bp(rB)
    assert np.isfinite(pB).all(), "[B] NaN P&L"
    print(f"    [B] every event keeps its date and rsi bucket; replacements are eligible names with a DEFINED rsi percentile and never an event "
          f"name; the name changes on {100 * (1 - kept / lo.sum()):.2f}% ({kept} kept = the pool shortfall, counted); {len(rB['trades']):,} trades, "
          f"mean {pB.mean():+.2f} ({el()})")
    # [C]
    signs = rng.choice([-1.0, 1.0], size=(1000, pnl.size))
    cm = (signs * pnl[None, :]).mean(axis=1)
    se = cm.std(ddof=1) / np.sqrt(cm.size)
    assert abs(cm.mean()) < 2 * se + 1e-9, "[C]"
    print(f"    [C] control C: mean {cm.mean():+.3f} bp, within 2 standard errors ({se:.3f}) of zero; p95 {np.quantile(cm, .95):+.2f}")
    # [P] part 0 is D350's stored file
    assert abs(p0["observed"] - obs) < 1e-9 and p0["draws"] == 100 and len(p0["control_A_elig"]) == 100 and len(p0["control_B"]) == 100, "[P]"
    p1s = sorted(REPO.glob("data/d353_ctrl_p*.json"))
    for f in p1s:
        c = json.loads(f.read_text())
        assert abs(c["observed"] - obs) < 1e-9 and c["part"] != 0, f"[P] {f.name}"
    print(f"    [P] part 0 = D350's stored file: observed {p0['observed']:+.4f} equals the re-simulated to 1e-9; 100 A' (control_A_elig) and 100 B "
          f"draws" + (f"; {len(p1s)} D353 part file(s) also match" if p1s else "; no D353 part file yet"))
    # [X]
    E_all, E_b = base_rates(P, elig)
    d_ = arm_stats(P, res["trades"], pnl, elig, E_b, E_all, np.random.default_rng([SEED, STUDY, 4]), with_interaction=True)
    print(f"    [X] the rsi buckets partition the {len(res['trades']):,} trades and sum_b n_b (E_sb - E_s) = {d_['interaction_identity']:.2e}")
    # [V]
    for K in KS:
        rv = simulate_variant(P, lo, zeros(lo), sc, "cap", K)
        sv = score_variant(rv, P, K)
        print(f"    [V] K={K}: the book holds at most {sv['max_positions']} per bar (<= K), never a short; entries {sv['entries']:,} = "
              f"{sv['trades']:,} closed + {sv['open_at_end']} open; {sv['skipped']:,} over-cap events skipped and counted "
              f"({100 * sv['skipped_share']:.1f}% of signals); G22.costed and costed_event agree on the deployed base to 1e-9")
    # [6]
    broke = 0
    try:
        assert_HX(rb2, P, key="book_dep")                      # the market term left in
    except AssertionError as e:
        assert "[HX]" in str(e)
        broke += 1
    try:
        tr50 = [(row, e0, age, pnl_ + 50e-4, sd) for row, e0, age, pnl_, sd in rA["trades"]]
        assert_S(P, tr50, np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke += 1
    assert broke == 2, f"[6] {broke} of 2 raised"
    print("    [6] [HX] raises when fed the unhedged deployed series (the market term left in); [S] raises on a ledger handed +50 bp")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_controls(P, draws, part):
    assert part != 0, "part 0 is D350's stored file (data/d350_ctrl_rev_5-E1_p0.json); use --part >= 1"
    lo, hi, sc, elig = event(P)
    res = run(P, lo, zeros(lo), sc, "cap")
    obs = float(pnl_bp(res).mean())
    assert len(res["trades"]) == D350_TRADES, "[ID]"
    p0 = json.loads(D350_P0.read_text())
    assert abs(obs - p0["observed"]) < 1e-9, "[P] observed differs from D350's stored file"
    print(f"\n  {MEMBER} part {part}: {int(lo.sum()):,} events -> {len(res['trades']):,} trades; observed {obs:+.2f} bp ([ID] == D350; [P] == stored)")
    PB = b_pool_P(P, elig)
    rngA = np.random.default_rng([SEED, STUDY, 1, part])
    rngB = np.random.default_rng([SEED, STUDY, 2, part])
    A_, B_, tA, tB = [], [], 0.0, 0.0
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        sl, ss, sc_ = aprime_draw(lo, hi, sc, elig, rngA)
        pa = pnl_bp(run(P, sl, zeros(lo), sc_, "cap"))
        assert np.isfinite(pa).all(), "[A'] NaN in a rotated draw"
        A_.append(float(pa.mean()))
        t2 = time.time()
        sB = V47.control_b_signal(PB, lo, rngB)
        pb = pnl_bp(run(P, sB, zeros(lo), sc, "cap"))
        assert np.isfinite(pb).all(), "[B] NaN in a draw"
        B_.append(float(pb.mean()))
        tA += t2 - t1
        tB += time.time() - t2
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - ts:.0f}s; A' {tA / (d + 1):.1f} s/draw, B {tB / (d + 1):.1f} s/draw)", flush=True)
    out = dict(member=MEMBER, draws=draws, part=part, observed=obs, trades=len(res["trades"]), events=int(lo.sum()),
               control_A_elig=A_, control_B=B_, seeds=dict(A=[SEED, STUDY, 1, part], B=[SEED, STUDY, 2, part]),
               B_pool="elig & isfinite(PCT rsi)", seconds_per_draw=dict(A=tA / draws, B=tB / draws))
    f = Path(str(CTRL).format(part=part))
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A' p50 {np.median(A_):+.2f} p95 {np.quantile(A_, .95):+.2f}; B p50 {np.median(B_):+.2f} p95 "
          f"{np.quantile(B_, .95):+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_variant(P, draws, part, ks):
    lo, hi, sc, elig = event(P)
    assert int(lo.sum()) == D350_EVENTS, "[G]"
    for K in ks:
        observed = {}
        for exit_ in ("cap", "invalidation"):
            rv = simulate_variant(P, lo, zeros(lo), sc, exit_, K)
            assert_series_defs(rv)
            h = assert_HX(rv, P)
            sv = score_variant(rv, P, K)
            sv["hx"] = h
            observed[exit_] = sv
            print(f"\n  K={K} {exit_:12s}: trades {sv['trades']:,} (mean/trade {sv['trade_mean_bp']:+.1f}), exposure {100 * sv['exposure']:.0f}%, "
                  f"positions {sv['mean_positions']:.2f}, skipped {100 * sv['skipped_share']:.0f}%; DEPLOYED hedged gross {sv['PUB']['deployed']['gross_bp']:+.2f} "
                  f"net PUB {sv['PUB']['deployed']['net_bp']:+.2f} PB {sv['PB']['deployed']['net_bp']:+.2f} bp/bar; TOTAL gross "
                  f"{sv['PUB']['total']['gross_bp']:+.2f} net PUB {sv['PUB']['total']['net_bp']:+.2f}; [HX] {h['worst']:.1e}; [V] max {sv['max_positions']}")
        rng = np.random.default_rng([SEED, STUDY, 3, K, part])
        null = {e: [] for e in ("cap", "invalidation")}
        ts = time.time()
        for d in range(draws):
            sl, ss, sc_ = aprime_draw(lo, hi, sc, elig, rng)
            for exit_ in ("cap", "invalidation"):
                rn = simulate_variant(P, sl, zeros(lo), sc_, exit_, K)
                assert int(rn["cnt0"].max()) <= K, "[V] null"
                assert np.isfinite(rn["book_dep_x"][rn["mask_dep"]]).all(), "[A'] NaN in a null series"
                null[exit_].append(null_stats(rn, P))
            if (d + 1) % 10 == 0 or d + 1 == draws:
                print(f"    K={K}: {d + 1}/{draws} ({time.time() - ts:.0f}s; {(time.time() - ts) / (d + 1):.1f} s/draw, both exits)", flush=True)
        out = dict(member=MEMBER, K=K, draws=draws, part=part, seed=[SEED, STUDY, 3, K, part], observed=observed,
                   null={e: {k: [x[k] for x in null[e]] for k in null[e][0]} for e in null} if draws else {},
                   seconds_per_draw=(time.time() - ts) / max(draws, 1))
        f = Path(str(VAR).format(K=K, part=part))
        f.write_text(json.dumps(clean(out)))
        if draws:
            g = np.array(out["null"]["cap"]["gross_bp"])
            print(f"  wrote {f.name}: cap-exit null gross p50 {np.median(g):+.2f} p95 {np.quantile(g, .95):+.2f} vs observed "
                  f"{observed['cap']['PUB']['deployed']['gross_bp']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def _dist(x, obs):
    x = np.asarray(x, float)
    return dict(p50=float(np.median(x)), p95=float(np.quantile(x, .95)), max=float(x.max()), draws=int(x.size),
                distinct=int(len(set(x.tolist()))), above=bool(obs > np.quantile(x, .95)))


def stage_report(P):
    lo, hi, sc, elig = event(P)
    assert int(lo.sum()) == D350_EVENTS, "[G]"
    E_all, E_b = base_rates(P, elig)
    rngC = np.random.default_rng([SEED, STUDY, 4])
    ARMS = {}
    for lens, sl, ss in (("long", lo, zeros(lo)), ("mirror", zeros(hi), hi)):
        for exit_ in EXITS:
            res = run(P, sl, ss, sc, exit_)
            pnl = pnl_bp(res)
            d_ = arm_stats(P, res["trades"], pnl, elig, E_b, E_all, rngC, with_interaction=(lens == "long" and exit_ == "cap"))
            d_["events"] = int(sl.sum() + ss.sum())
            ARMS[f"{lens}/{exit_}"] = d_
            if lens == "long" and exit_ == "cap":
                assert len(res["trades"]) == D350_TRADES, "[ID]"
                print(f"    [X] the rsi buckets partition the {len(res['trades']):,} trades and sum_b n_b (E_sb - E_s) = {d_['interaction_identity']:.2e}")
    obs = ARMS["long/cap"]["mean_bp"]
    # controls: part 0 = D350's file, parts >= 1 = this study's
    p0 = json.loads(D350_P0.read_text())
    assert abs(p0["observed"] - obs) < 1e-9 and p0["trades"] == D350_TRADES, "[P] D350's stored observed differs from the re-simulated"
    A_, B_, parts = [np.array(p0["control_A_elig"])], [np.array(p0["control_B"])], [dict(file=D350_P0.name, part=0, draws=p0["draws"], B_pool="elig")]
    for f in sorted(REPO.glob("data/d353_ctrl_p*.json")):
        c = json.loads(f.read_text())
        assert abs(c["observed"] - obs) < 1e-9, f"[P] {f.name} observed differs from the re-simulated"
        assert c["part"] != 0
        A_.append(np.array(c["control_A_elig"]))
        B_.append(np.array(c["control_B"]))
        parts.append(dict(file=f.name, part=c["part"], draws=c["draws"], B_pool=c.get("B_pool")))
    A_, B_ = np.concatenate(A_), np.concatenate(B_)
    print(f"    [P] part 0 is D350's stored file (observed {p0['observed']:+.4f} == re-simulated {obs:+.4f}); parts: "
          + ", ".join(f"{p['file']} ({p['draws']} draws)" for p in parts))
    CTRLS = dict(draws=int(A_.size), parts=parts, A_prime=_dist(A_, obs), B=_dist(B_, obs), C=ARMS["long/cap"]["control_C"],
                 B_pool_note="part 0 (D350) drew B from elig; parts >= 1 from elig & isfinite(PCT rsi) (D352's [B])")
    # variant files
    VARIANT = {}
    for K in KS:
        fs = sorted(REPO.glob(f"data/d353_variant_k{K}_p*.json"))
        if not fs:
            continue
        ds = [json.loads(f.read_text()) for f in fs]
        v = dict(observed=ds[0]["observed"], files=[f.name for f in fs], null={})
        with_null = [d for d in ds if d["null"]]
        for e in ("cap", "invalidation"):
            o = ds[0]["observed"][e]
            nl = {k: np.concatenate([np.array(d["null"][e][k]) for d in with_null]) for k in with_null[0]["null"][e]} if with_null else None
            if nl is not None:
                v["null"][e] = dict(gross_bp=_dist(nl["gross_bp"], o["PUB"]["deployed"]["gross_bp"]),
                                    net_PUB=_dist(nl["net_PUB"], o["PUB"]["deployed"]["net_bp"]),
                                    sharpe_net_PUB=_dist(nl["sharpe_net_PUB"], o["PUB"]["deployed"]["sharpe_net"]),
                                    net_PB=_dist(nl["net_PB"], o["PB"]["deployed"]["net_bp"]),
                                    gross_tot_bp=_dist(nl["gross_tot_bp"], o["PUB"]["total"]["gross_bp"]))
        VARIANT[K] = v
    d346 = json.loads(D346_JSON.read_text())
    D346 = {k: dict(PUB_net_bp_bar=d346["table"][k]["rev_5"]["variant"]["PUB"]["net_bp_bar"], PB_net_bp_bar=d346["table"][k]["rev_5"]["variant"]["PB"]["net_bp_bar"],
                    gross_bp_bar=d346["table"][k]["rev_5"]["variant"]["PUB"]["gross_bp_bar"]) for k in ("20", "40")}
    m_eff = json.loads(D350_SCREEN.read_text())["m_eff"] if D350_SCREEN.exists() else None

    # ---- print ----
    print("\n" + "=" * 132)
    print(f"THE INVARIANT LENS -- {MEMBER}: every event taken, next-open fill, hedged against the floored market; bp per TRADE")
    print("=" * 132)
    print("  %-6s %-12s %6s %6s %8s %8s %6s %6s %7s %8s %9s %9s %7s %8s %9s" % ("side", "exit", "events", "n", "mean", "median", "t", "pos%", "hold", "bp/bar",
                                                                            "beta-adj", "net PUB", "net PB", "be hs", "eras"))
    for key, d_ in ARMS.items():
        lens, exit_ = key.split("/")
        print("  %-6s %-12s %6d %6d %+8.1f %+8.1f %+6.2f %6.1f %7.1f %+8.2f %+9.1f %+9.1f %+7.1f %8.1f %9s" % (
            lens, exit_, d_["events"], d_["trades"], d_["mean_bp"], d_["median_bp"], d_["t"], 100 * d_["share_pos"], d_["hold_mean"],
            d_["mean_per_bar_held_bp"], d_["beta_adj_mean_bp"], d_["net_per_trade"]["PUB"], d_["net_per_trade"]["PB"], d_["breakeven_half_spread_bp_side"],
            "%+.0f/%+.0f" % (d_["era1_mean_bp"] or 0, d_["era2_mean_bp"] or 0)))
    print(f"  2c (PUB / PB) on the cap exit: {ARMS['long/cap']['two_c']['PUB']:.1f} / {ARMS['long/cap']['two_c']['PB']:.1f} bp at held median half-spread "
          f"{ARMS['long/cap']['held_half']['PUB']:.1f} / {ARMS['long/cap']['held_half']['PB']:.1f}, held price ${ARMS['long/cap']['held_price']:.2f}; "
          f"'be hs' = the half-spread (bp/side) at which the mean nets zero")
    print(f"  down-years {P['down_years']}: long/cap {ARMS['long/cap']['down_years_mean_bp']:+.1f} (n {ARMS['long/cap']['down_years_n']}); by year: "
          + " ".join(f"{y}:{v:+.0f}" for y, v in sorted(ARMS["long/cap"]["by_year"].items())))
    print(f"\n  CONTROLS on the long cap-exit statistic (mean hedged excess, bp): observed {obs:+.2f}")
    print("  %-10s %6s %8s %8s %8s %6s %6s" % ("control", "draws", "p50", "p95", "max", "dist", "above"))
    for nm, c in (("A'", CTRLS["A_prime"]), ("B", CTRLS["B"]), ("C", CTRLS["C"])):
        print("  %-10s %6d %+8.2f %+8.2f %+8.2f %6s %6s" % (nm, c["draws"], c["p50"], c["p95"], c["max"], c.get("distinct", "-"), "yes" if c["above"] else "NO"))
    print(f"  {CTRLS['B_pool_note']}; multiplicity: 138 nominal" + (f", M_eff Li-Ji {m_eff['li_ji']:.0f} / CN {m_eff['cheverud_nyholt']:.0f} (D350)" if m_eff else ""))
    for key in ("long/cap", "long/invalidation"):
        g4 = ARMS[key]["four_groups"]
        tt = g4["top_trade"]
        print(f"\n  FOUR GROUPS per trade ({key}): n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
              f"payoff {round(g4['payoff'], 2) if g4['payoff'] is not None else '-'} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}")
        print(f"      trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f}  ex-bottom {g4['mean_ex_bottom_bp']:+.1f}  trimmed {g4['mean_trimmed_bp']:+.1f}")
        print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
              + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
              + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}")
        print(f"      TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} (DV pct "
              f"{round(tt['dv_percentile_at_entry'], 1) if tt['dv_percentile_at_entry'] is not None else '-'}), held {tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = "
              f"{('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
        sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
        print(f"      splits: dead {sd_['dead_n']} {round(sd_['dead_mean_bp'], 1) if sd_['dead_mean_bp'] is not None else '-'} / alive {sd_['alive_n']} "
              f"{round(sd_['alive_mean_bp'], 1) if sd_['alive_mean_bp'] is not None else '-'}; price <= ${sp_['median_price']:.2f} {sp_['low_n']} "
              f"{round(sp_['low_mean_bp'], 1) if sp_['low_mean_bp'] is not None else '-'} / above {sp_['high_n']} "
              f"{round(sp_['high_mean_bp'], 1) if sp_['high_mean_bp'] is not None else '-'}")
    inter = ARMS["long/cap"]["interaction"]
    print("\n  INTERACTION with the rsi ranking (long, cap exit): bucket[n] E[member,bucket]/E[bucket]/interaction")
    print("  " + " ".join(f"b{b}[{v['n']}] {v['E_sb']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(inter.items())))
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1; "
          f"base rate all floored name-bars {E_all:+.1f}")

    print("\n" + "=" * 132)
    print("THE VARIANT LENS -- the slot-capped event book (long only), HEDGED capital series; bp per BAR -- never compared to the per-trade lens")
    print("=" * 132)
    if VARIANT:
        print("  %-3s %-12s %6s %5s %5s %5s | %7s %7s %7s %7s %7s %8s | %7s %7s %6s | %7s %7s %6s" % (
            "K", "exit", "n", "exp%", "pos", "skip%", "gross", "netPUB", "netPB", "vol", "Sh net", "maxdd", "A' p50", "A' p95", "above", "nPUB50", "nPUB95", "above"))
        for K, v in VARIANT.items():
            for e in ("cap", "invalidation"):
                o = v["observed"][e]
                dp, dpb = o["PUB"]["deployed"], o["PB"]["deployed"]
                nl = v["null"].get(e)
                print("  %-3d %-12s %6d %5.0f %5.2f %5.0f | %+7.2f %+7.2f %+7.2f %7.1f %+7.3f %8.0f | %s" % (
                    K, e, o["trades"], 100 * o["exposure"], o["mean_positions"], 100 * o["skipped_share"], dp["gross_bp"], dp["net_bp"], dpb["net_bp"],
                    dp["vol_bp"], dp["sharpe_net"], dp["maxdd_bp"],
                    ("%+7.2f %+7.2f %6s | %+7.2f %+7.2f %6s" % (nl["gross_bp"]["p50"], nl["gross_bp"]["p95"], "yes" if nl["gross_bp"]["above"] else "NO",
                                                              nl["net_PUB"]["p50"], nl["net_PUB"]["p95"], "yes" if nl["net_PUB"]["above"] else "NO")) if nl else "null not run"))
            for e in ("cap", "invalidation"):
                o = v["observed"][e]
                print(f"      K={K} {e}: TOTAL base (per U=4 slots, defined bars) gross {o['PUB']['total']['gross_bp']:+.2f} net PUB {o['PUB']['total']['net_bp']:+.2f} "
                      f"PB {o['PB']['total']['net_bp']:+.2f} Sharpe net PUB {o['PUB']['total']['sharpe_net']:+.3f}; deployed Sharpe gross {o['PUB']['deployed']['sharpe_gross']:+.3f}; "
                      f"turnover {o['PUB']['deployed']['turnover']:.4f}, entries {o['entries']:,}, held half-spread PUB {o['PUB']['held_half_spread']:.1f} PB {o['PB']['held_half_spread']:.1f}"
                      + (f"; null Sharpe net PUB p95 {v['null'][e]['sharpe_net_PUB']['p95']:+.3f}, distinct {v['null'][e]['gross_bp']['distinct']} of {v['null'][e]['gross_bp']['draws']}" if v["null"].get(e) else ""))
    else:
        print("  variant stage not run (--variant)")
    print(f"  D346's rev_5 SLOT-BOOK cell (rank < 2 both sides, F0, keep_v2, open fill) PUB net bp/bar: k=20 {D346['20']['PUB_net_bp_bar']:+.2f}, k=40 "
          f"{D346['40']['PUB_net_bp_bar']:+.2f} -- the ranking construction on the same score, never on the same statistic")

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    L = ARMS["long/cap"]
    q = {}
    q["Q1"] = bool(CTRLS["A_prime"]["above"] and CTRLS["B"]["above"] and CTRLS["C"]["above"])
    q["Q2"] = bool(all(ARMS[f"long/{e}"]["net_per_trade"]["PUB"] < 0 for e in EXITS) and L["net_per_trade"]["PB"] > 0)
    inv = ARMS["long/invalidation"]
    q["Q3"] = bool(inv["mean_bp"] < L["mean_bp"] and inv["mean_per_bar_held_bp"] > L["mean_per_bar_held_bp"])
    k2 = VARIANT.get(2)
    n2 = k2["null"].get("cap") if k2 else None
    q["Q4a"] = bool(n2 and n2["gross_bp"]["above"])
    q["Q4b"] = bool(k2 and k2["observed"]["cap"]["PUB"]["deployed"]["net_bp"] > 0)
    g4 = L["four_groups"]
    q["Q5"] = bool(abs(g4["mean_trimmed_bp"] - g4["mean_bp"]) <= 10.0 and (g4["top_trade"]["share_of_pnl"] or 0) < 0.03)
    q["Q6"] = bool((L["era1_mean_bp"] or 0) > 0)

    def inter_mean(buckets):
        sel = [inter[b] for b in buckets if b in inter]
        return (sum(v["n"] * v["interaction"] for v in sel) / sum(v["n"] for v in sel)) if sel else None
    ib, ia = inter_mean((0, 1, 2)), inter_mean((6, 7, 8, 9))
    q["Q7"] = bool(ib is not None and ia is not None and ib < 0 and ia > 0)
    q["Q8"] = bool(abs(L["beta_adj_mean_bp"] - L["mean_bp"]) <= 0.15 * abs(L["mean_bp"]))
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) above p95 of A', B and C on the cap exit: {v_(q['Q1'])} -- observed {obs:+.2f} vs A' p95 {CTRLS['A_prime']['p95']:+.2f}, "
          f"B p95 {CTRLS['B']['p95']:+.2f}, C p95 {CTRLS['C']['p95']:+.2f} at {CTRLS['draws']} A'/B draws" + ("" if CTRLS["draws"] >= 200 else " (pre-reg: 200; part 1 not yet run)"))
    print(f"  Q2 nets negative under PUB on every exit and positive under PB on the cap: {v_(q['Q2'])} -- PUB " +
          ", ".join(f"{e} {ARMS[f'long/{e}']['net_per_trade']['PUB']:+.1f}" for e in EXITS) + f"; PB cap {L['net_per_trade']['PB']:+.1f}")
    print(f"  Q3 invalidation's mean per trade below the cap's and its mean per bar held above: {v_(q['Q3'])} -- per trade {inv['mean_bp']:+.1f} vs {L['mean_bp']:+.1f}; "
          f"per bar held {inv['mean_per_bar_held_bp']:+.2f} vs {L['mean_per_bar_held_bp']:+.2f} (holds {inv['hold_mean']:.1f} vs {L['hold_mean']:.1f})")
    if k2:
        o2 = k2["observed"]["cap"]["PUB"]["deployed"]
        print(f"  Q4a the K=2 hedged deployed series above A' p95 on gross bp/bar (cap exit): {v_(q['Q4a'])} -- gross {o2['gross_bp']:+.2f} vs A' p95 "
              + (f"{n2['gross_bp']['p95']:+.2f} (p50 {n2['gross_bp']['p50']:+.2f}, {n2['gross_bp']['draws']} draws)" if n2 else "null not run"))
        print(f"  Q4b (against) the K=2 hedged deployed series nets > 0 bp/bar under PUB: {v_(q['Q4b'])} -- net PUB {o2['net_bp']:+.2f} (cost {o2['cost_bp']:.2f} on turnover "
              f"{o2['turnover']:.4f}); PB {k2['observed']['cap']['PB']['deployed']['net_bp']:+.2f}")
    else:
        print("  Q4a / Q4b: variant stage at K=2 not run -- FALSIFIED by absence (not evaluated)")
    print(f"  Q5 symmetric 1% trim within 10 bp of the mean and the top trade < 3% of P&L: {v_(q['Q5'])} -- trimmed {g4['mean_trimmed_bp']:+.1f} vs mean {g4['mean_bp']:+.1f}; "
          f"top trade {g4['top_trade']['symbol']} {100 * (g4['top_trade']['share_of_pnl'] or 0):.1f}%")
    print(f"  Q6 (against) era 1 positive on the cap exit: {v_(q['Q6'])} -- era1 {L['era1_mean_bp']:+.1f} (n {L['era1_n']}) / era2 {L['era2_mean_bp']:+.1f} (n {L['era2_n']})")
    print(f"  Q7 interaction negative in the bottom rsi decile and positive above the 75th percentile: {v_(q['Q7'])} -- bottom (b0-2) "
          f"{ib if ib is None else round(ib, 1)}, above 75 (b6-9) {ia if ia is None else round(ia, 1)}")
    print(f"  Q8 beta-adjusted excess within 15% of equal-weight: {v_(q['Q8'])} -- {L['mean_bp']:+.1f} -> {L['beta_adj_mean_bp']:+.1f} "
          f"({100 * abs(L['beta_adj_mean_bp'] - L['mean_bp']) / abs(L['mean_bp']):.1f}%; median beta {L['beta_median']:.2f})")
    out = dict(note="D353: rev_5/E1 (D350's survivor) on the invariant event lens with every exit, both hedges, A'/B/C at up to 200 draws and the four "
                    "groups; and the slot-capped one-sided event book on a HEDGED capital series (the additive kernel option) against A' at the same K. "
                    "Per-trade and per-bar statistics are never compared. Nothing is a book; nothing promoted.",
               member=MEMBER, events=int(lo.sum()), cap=CAP, x_target=X_TARGET, U=U_SLOTS, ks=list(KS), base_rate_all_bp=E_all, base_rate_by_bucket_bp=E_b,
               down_years=P["down_years"], floored_market_by_year=P["yr_ret"], arms=ARMS, controls=CTRLS, variant=VARIANT, d346_rev5_slot_book=D346,
               m_eff_d350=m_eff, predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--variant", action="store_true")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--k", type=int, choices=KS, help="--variant: one K only (default both)")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print(f"D353  {MEMBER} entering the bottom decile -- the full record, and the slot-capped event book hedged")
    P = PREP.prep(need_grids=a.selftest or a.report)
    if a.selftest:
        stage_selftest(P)
    elif a.controls:
        stage_controls(P, a.draws, a.part)
    elif a.variant:
        stage_variant(P, a.draws, a.part, (a.k,) if a.k else KS)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --controls, --variant, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
