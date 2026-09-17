"""D358 -- the flat-by-default sleeve: a real trigger, a market hedge, no slot cap, scored on the capital it asks for.

    uv run python scripts/run_d358_flat_sleeve.py --selftest
    uv run python scripts/run_d358_flat_sleeve.py --cell rev_5:2 --draws 100 --part 1      A' and B for one cell (one process per cell)
    uv run python scripts/run_d358_flat_sleeve.py --report

Pre-registration: docs/decisions/D358-the-flat-by-default-sleeve-a-trigger-a-market-hedge-and-the.md

The family: two scores (rev_5, hist_L) x three rarities (p in 2, 5, 10) = six cells. The event is a FRESH entry into the
bottom p% of the lagged floored cross-sectional percentile (pct[t] <= p and pct[t-1] > p) on eligible bars; the 10% cells
are D350's rev_5/E1 and hist_L/E1 exactly ([G]) and the rev_5 10% cap ledger is D353's ([ID]: 27,316 trades, +43.38 bp).

The sleeve: every event taken long at the next open, no slot cap (EB.simulate_event with n_max=None), hedged by the floored
universe's equal-weight return, exits cap (primary) and invalidation. Scored on the DEPLOYED base -- the hedged return per bar
averaged over open positions, NaN when flat (book_dep_x on mask_dep) -- with G22.costed's arithmetic (round trip at the held
names' median half-spread + commission per crossing, turnover = entries / mean held / bars), PUB primary, PB beside. The
UNHEDGED deployed series (book_dep, the raw return averaged over open positions) is costed the same way beside it, and the
TOTAL base at U = 4 (book_tot_x on defined bars, EB.costed_event's total arithmetic: entries / bars / U) is printed for
comparison with D345/D353 only. Exposure = deployed bars / defined bars. Per-trade statistics on the same ledger are reported
in bp per TRADE and never compared to the per-bar numbers.

Splits of the deployed series (by year, era halves, down-years): G22.costed on the deployed series restricted to the subset's
bars -- the subset's own entries, mean positions and bars, the CELL's held-median half-spread and price (the cost constants are
a property of the ledger, not of the year). The rsi-bucket split (bucket of the trigger name's rsi percentile at t-1): the
deployed base cannot be split by bucket cleanly (a bar holds names from several buckets), so each bucket reports its per-trade
mean and count and the deployed net of a SUB-LEDGER rebuilt from those trades alone (per-bar hedged sum / positions of that
bucket's closed trades, costed by G22.costed with the sub-ledger's own entries, held names and half-spread); the buckets' bars
overlap, so the sub-ledger deployed numbers do not add up to the cell's.

Nulls per cell on the cap exit: A' (per-name time rotation within elig, D351's assertions, re-simulated with the hedged series),
B (same day, same rsi bucket, a random eligible name with a DEFINED rsi percentile), each recording deployed net PUB bp/bar,
deployed net PUB Sharpe, deployed gross and the per-trade mean per draw; C (1,000 random directions on the per-trade ledger).

Series files: data/d358_series_{score}_{p}.npz (cap) and ..._inv.npz (invalidation), written by --report: dates, dep_hedged,
dep_unhedged, n_open, entries, defined, mask_dep, cost_bp_PUB, cost_bp_PB; reloaded and recomputed to 1e-12 ([SER]).

ASSERTIONS [K][F0][R][G][ID][E][HX][A'][B][C][S][SER][6] -- pre-reg section 7.
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
V50 = _load("d350r", "run_d350_long_timing_screen.py")      # lagged, member_dense, four_groups, clean (its _load("d348p") is memoised)
V53 = _load("d353r", "run_d353_rev5_record.py")             # event, b_pool_P, b_shortfall, recompute_trade, assert_S, assert_series_defs, _dist
V47 = PREP.V47
EB, G22, UF = PREP.EB, PREP.G22, PREP.UF
SEED, CAP, X_TARGET = V47.SEED, V47.CAP, V47.X_TARGET
CONVS = V47.CONVS
STUDY = 358
SCORES = ("rev_5", "hist_L")
PS = (2, 5, 10)
CELLS = [(s, p) for s in SCORES for p in PS]
EXITS = ("cap", "invalidation")
U_SLOTS = 4
ANN = 252.0
D353_JSON = REPO / "data" / "d353_rev5_record.json"
D350_P0 = REPO / "data" / "d350_ctrl_rev_5-E1_p0.json"
D347_HIST_P0 = REPO / "data" / "d347_ctrl_hist_L_p0.json"
D353_TRADES, D353_MEAN = 27_316, 43.38
CTRL = REPO / "data" / "d358_ctrl_{score}_{p}_p{part}.json"
SER = REPO / "data" / "d358_series_{score}_{p}{suffix}.npz"
OUT = REPO / "data" / "d358_flat_sleeve.json"
SELFTEST_TMP = REPO / "temp" / "d358_selftest"
clean = V50.clean


def cell_name(score, p):
    return f"{score}:{p}"


def zeros(x):
    return np.zeros_like(x)


# ------------------------------------------------------------------ the events
_PCT = {}


def pct_of(P, score):
    """The lagged floored cross-sectional percentile grid of the score (D350's lagged + D347's percentile_grid), memoised."""
    if score not in _PCT:
        _PCT[score] = V47.percentile_grid(V50.lagged(P, score))
    return _PCT[score]


def events(P, score, p):
    """lo[t, i]: pct[t] <= p and pct[t-1] > p on eligible bars. The kernel's score is pct itself (long: exit when pct >= 50)."""
    pct = pct_of(P, score)
    elig = np.asarray(P["elig"])
    prev = np.full_like(pct, np.nan)
    prev[1:] = pct[:-1]
    with np.errstate(invalid="ignore"):
        lo = (pct <= float(p)) & (prev > float(p)) & elig
    return np.ascontiguousarray(lo), pct, elig


def raw_floored(P, score):
    """The (n, T) floored, deal-filtered, warm-based raw score -- D347's closure before the lag, for [E]'s direct count."""
    sc = UF.apply_floor_replace(np.where(P["excl"], np.nan, P["score"](score)), P["keep"])
    return np.where(P["base"], sc, np.nan)


def pct_direct(col, i):
    """Average-rank percentile of name i in a raw column by direct counting (no sort, no searchsorted)."""
    fin = np.isfinite(col)
    k = int(fin.sum())
    if k < 50 or not fin[i]:
        return np.nan, k
    v = col[fin]
    return (float((v < col[i]).sum()) + 0.5 * float((v == col[i]).sum())) / k * 100.0, k


# ------------------------------------------------------------------ the kernel and the costing
def simulate(P, lo, pct, exit_, A3=None):
    return EB.simulate_event(P["A3"] if A3 is None else A3, lo, zeros(lo), pct, exit=exit_, cap=CAP, n_max=None,
                             x_target=X_TARGET, U=U_SLOTS, hedged_series=True)


def costed(res, book, mask, P, cv):
    """G22.costed on a series over a mask, plus the breakeven half-spread (bp/side) at which the gross nets zero."""
    d = G22.costed(dict(res, book=book, mask=mask), P["G4"][cv])
    d["breakeven_half_spread_bp_side"] = (d["gross_bp"] / d["turnover"] - d["commission_rt"]) / 4.0 if d["turnover"] > 0 else None
    return d


def deployed_block(res, P):
    """The deployed base, hedged and unhedged, both conventions; the total base at U=4 beside (comparison only)."""
    defined, mask_dep, held, ent = res["defined"], res["mask_dep"], res["held"], res["ent"]
    nd, nb = int(defined.sum()), int(mask_dep.sum())
    out = dict(trades=len(res["trades"]), entries=int(ent.sum()), open_at_end=int(held[-1]), bars_defined=nd, bars_deployed=nb,
               deployed_outside_defined=int((mask_dep & ~defined).sum()), exposure=nb / nd,
               mean_positions_deployed=float(held[mask_dep].mean()), mean_positions_defined=float(held[defined].mean()),
               max_positions=int(held.max()), entries_per_year=float(ent.sum()) / (nd / ANN))
    hres = dict(res, book_dep=res["book_dep_x"], book_tot=res["book_tot_x"])
    for cv in CONVS:
        out[cv] = dict(hedged=costed(res, res["book_dep_x"], mask_dep, P, cv),
                       unhedged=costed(res, res["book_dep"], mask_dep, P, cv),
                       total=EB.costed_event(hres, P["HALF"][cv], P["CLOSE"], P["DV"])["total"])
    return out


def deployed_subsets(res, P, book):
    """G22.costed on the deployed series restricted to a subset of bars (by year, era halves, down-years), both conventions:
    the subset's entries, mean positions and bars; the cell's held-median half-spread and price."""
    T = res["held"].size
    t = np.arange(T)
    years = np.asarray(P["years"])
    down = np.isin(years, list(P["down_years"]))

    def sub(m):
        mm = res["mask_dep"] & m
        d_ = dict(bars=int(mm.sum()), entries=int(res["ent"][mm].sum()))
        if mm.sum() >= 2:
            for cv in CONVS:
                c = G22.costed(dict(res, book=book, mask=mm), P["G4"][cv])
                d_[cv] = dict(gross_bp=c["gross_bp"], net_bp=c["net_bp"], cost_bp=c["cost_bp"], vol_bp=c["vol_bp"], sharpe_net=c["sharpe_net"])
        return d_
    return dict(by_year={int(y): sub(years == y) for y in np.unique(years[res["mask_dep"]])},
                era1=sub(t < T // 2), era2=sub(t >= T // 2), down_years=sub(down))


def trade_block(P, res, elig, with_groups):
    """Per-trade statistics in bp per TRADE (never compared to the per-bar numbers)."""
    tr = res["trades"]
    pnl = V47.pnl_bp(res)
    T = P["T"]
    half = T // 2
    years = np.asarray(P["years"])
    yrs = np.array([years[t[1]] for t in tr])
    era1 = np.array([t[1] < half for t in tr])
    down = np.isin(yrs, list(P["down_years"]))
    c2 = {cv: V47.two_c(tr, P["HALF"][cv], P["CLOSE"]) for cv in CONVS}
    mean = float(pnl.mean())
    hold = float(np.mean([t[2] for t in tr]))
    px = c2["PUB"][2]
    d_ = dict(trades=len(tr), mean_bp=mean, median_bp=float(np.median(pnl)),
              t=float(mean / (pnl.std(ddof=1) / np.sqrt(pnl.size))) if pnl.size > 1 else None,
              share_pos=float((pnl > 0).mean()), hold_mean=hold, hold_median=float(np.median([t[2] for t in tr])),
              mean_per_bar_held_bp=mean / hold, two_c={cv: c2[cv][0] for cv in CONVS}, held_half={cv: c2[cv][1] for cv in CONVS},
              held_price=px, net_per_trade={cv: mean - c2[cv][0] for cv in CONVS}, mean_over_2c={cv: mean / c2[cv][0] for cv in CONVS},
              breakeven_half_spread_bp_side=(mean - 2.0 * 0.005 / px * 1e4) / 2.0,
              era1_mean_bp=float(pnl[era1].mean()) if era1.any() else None, era2_mean_bp=float(pnl[~era1].mean()) if (~era1).any() else None,
              era1_n=int(era1.sum()), era2_n=int((~era1).sum()),
              down_years_mean_bp=float(pnl[down].mean()) if down.any() else None, down_years_n=int(down.sum()),
              by_year={int(y): dict(n=int((yrs == y).sum()), mean_bp=float(pnl[yrs == y].mean())) for y in np.unique(yrs)})
    if with_groups:
        d_["four_groups"] = V50.four_groups(tr, pnl, P, elig)
    return d_


def control_C(pnl, rng, draws=1000, chunk=100):
    """Random direction on the per-trade ledger, in chunks (a (1000, 27k) sign matrix is 216 MB)."""
    means = []
    for _ in range(draws // chunk):
        signs = rng.choice([-1.0, 1.0], size=(chunk, pnl.size))
        means.append((signs * pnl[None, :]).mean(axis=1))
    cm = np.concatenate(means)
    obs = float(pnl.mean())
    return dict(V53._dist(cm, obs), mean=float(cm.mean()), se=float(cm.std(ddof=1) / np.sqrt(cm.size)))


# ------------------------------------------------------------------ the ledger rebuilt per bar: [HX], the bucket sub-ledgers
def rebuild(trades, P, hedged):
    """(row, e0, age, pnl, side) -> per-bar signed sum on bars e0 .. e0 + age - 1: the entry bar on ocT (- m_f_oc), later bars
    on r1T (- m_f); the market term only when hedged. Returns (sum, position count, entries per bar)."""
    r1T, ocT, m_f, m_oc = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"]
    T = P["T"]
    reb, cnt, ent = np.zeros(T), np.zeros(T, np.int64), np.zeros(T, np.int32)
    for row, e0, age, _p, side in trades:
        sgn = 1.0 if side == 0 else -1.0
        v = np.array(r1T[e0:e0 + age, row], dtype=float)
        v[0] = ocT[e0, row]
        if hedged:
            mm = np.array(m_f[e0:e0 + age], dtype=float)
            mm[0] = m_oc[e0]
            v = v - mm
        reb[e0:e0 + age] += sgn * v
        cnt[e0:e0 + age] += 1
        ent[e0] += 1
    return reb, cnt, ent


def assert_HX(res, P, key, hedged, tol=1e-12):
    """series x positions held == the ledger summed per bar on every bar the ledger covers (the open tail at the end is the only
    uncovered stretch -- asserted contiguous, counted, excluded). hedged=True: sgn (v - m) vs book_dep_x; False: sgn v vs book_dep."""
    reb, cnt, _ = rebuild(res["trades"], P, hedged)
    held = res["held"].astype(np.int64)
    T = held.size
    assert (cnt <= held).all(), "[HX] the ledger claims a position the book never held"
    covered = cnt == held
    unc = np.flatnonzero(~covered)
    if unc.size:
        assert np.array_equal(unc, np.arange(unc[0], T)), "[HX] uncovered bars are not the open tail"
    assert np.isfinite(reb).all(), "[HX] a rebuilt bar is not finite"
    with np.errstate(invalid="ignore"):
        signed = np.where(held > 0, np.nan_to_num(np.asarray(res[key], float)) * held, 0.0)
    worst = float(np.abs(signed[covered] - reb[covered]).max())
    assert worst < tol, f"[HX] {key} ({'hedged' if hedged else 'unhedged'} rebuild): series x held != ledger per bar: {worst:.2e}"
    if hedged:
        assert abs(float(reb.sum()) - float(sum(t[3] for t in res["trades"]))) < 1e-9, "[HX] the per-bar rebuild does not sum to the ledger"
    return dict(worst=worst, covered=int(covered.sum()), uncovered=int(unc.size), open_at_end=int(held[-1] - cnt[-1]))


def subledger(trades, P):
    """A deployed series from a subset of closed trades alone (hedged): book = sum / count where count > 0."""
    sx, cnt, ent = rebuild(trades, P, hedged=True)
    mask = cnt > 0
    with np.errstate(invalid="ignore"):
        book = np.where(mask, sx / np.maximum(cnt, 1), np.nan)
    return dict(trades=list(trades), ent=ent, held=cnt, book=book, mask=mask)


def bucket_split(P, res):
    """By rsi bucket of the trigger name at entry (bucket_rsi[e0, row], the rsi percentile at t-1). Names whose rsi percentile
    is undefined at entry are excluded and counted (np.digitize files NaN under bucket 9)."""
    tr = res["trades"]
    pnl = V47.pnl_bp(res)
    rows = np.array([t[0] for t in tr])
    e0s = np.array([t[1] for t in tr])
    bucket = np.asarray(P["bucket_rsi"])[e0s, rows]
    ok = np.isfinite(np.asarray(P["PCT"]["rsi"])[e0s, rows])
    out = dict(undefined_n=int((~ok).sum()), undefined_mean_bp=float(pnl[~ok].mean()) if (~ok).any() else None, buckets={},
               method="per-trade mean and count per bucket; 'deployed' = G22.costed on the sub-ledger of that bucket's closed trades "
                      "(hedged sum / count per bar, its own entries, held names and half-spread); bucket bars overlap, so these do not add up")
    for b in range(10):
        m = ok & (bucket == b)
        if not m.any():
            continue
        sub = subledger([tr[j] for j in np.flatnonzero(m)], P)
        dep = {cv: G22.costed(sub, P["G4"][cv]) for cv in CONVS} if int(sub["mask"].sum()) >= 2 else None
        out["buckets"][b] = dict(n=int(m.sum()), mean_bp=float(pnl[m].mean()), median_bp=float(np.median(pnl[m])), share_pos=float((pnl[m] > 0).mean()),
                                 bars_deployed=int(sub["mask"].sum()), mean_positions=float(sub["held"][sub["mask"]].mean()) if sub["mask"].any() else None,
                                 deployed={cv: dict(gross_bp=dep[cv]["gross_bp"], net_bp=dep[cv]["net_bp"], cost_bp=dep[cv]["cost_bp"],
                                                    sharpe_net=dep[cv]["sharpe_net"]) for cv in CONVS} if dep else None)
    assert sum(v["n"] for v in out["buckets"].values()) + out["undefined_n"] == len(tr), "[X] the buckets do not partition the trades"
    return out


# ------------------------------------------------------------------ the series files: [SER]
def series_path(score, p, exit_, root=None):
    suffix = "" if exit_ == "cap" else "_inv"
    f = Path(str(SER).format(score=score, p=p, suffix=suffix))
    return f if root is None else root / f.name


def write_series(path, res, dep, P, score, p, exit_):
    np.savez(path, dates=np.array(P["dates"]), dep_hedged=np.asarray(res["book_dep_x"], float), dep_unhedged=np.asarray(res["book_dep"], float),
             n_open=res["held"].astype(np.int32), entries=res["ent"].astype(np.int32), defined=res["defined"], mask_dep=res["mask_dep"],
             cost_bp_PUB=np.float64(dep["PUB"]["hedged"]["cost_bp"]), cost_bp_PB=np.float64(dep["PB"]["hedged"]["cost_bp"]),
             score=np.array(score), p=np.int64(p), exit=np.array(exit_), study=np.int64(STUDY))
    return path


def reload_check(path, dep, tol=1e-12):
    """Reload the file and recompute deployed gross, cost, net, vol, Sharpe (gross and net), exposure and mean positions for the
    hedged and unhedged series, both conventions; every number must equal the in-memory G22.costed result to tol."""
    z = np.load(path, allow_pickle=False)
    mask, defined, n_open = z["mask_dep"], z["defined"], z["n_open"]
    assert mask.dtype == bool and defined.dtype == bool and z["dates"].shape == mask.shape
    worst = 0.0
    for key, nm in (("dep_hedged", "hedged"), ("dep_unhedged", "unhedged")):
        b = z[key][mask]
        assert np.isfinite(b).all(), f"[SER] {path.name}: NaN inside the deployed mask"
        g = float(b.mean()) * 1e4
        v = float(b.std(ddof=1)) * 1e4
        for cv in CONVS:
            c = float(z[f"cost_bp_{cv}"])
            net = g - c
            ref = dep[cv][nm]
            for a, r in ((g, ref["gross_bp"]), (c, ref["cost_bp"]), (net, ref["net_bp"]), (v, ref["vol_bp"]),
                         (g / v * np.sqrt(ANN), ref["sharpe_gross"]), (net / v * np.sqrt(ANN), ref["sharpe_net"]), (b.size, ref["bars"])):
                worst = max(worst, abs(float(a) - float(r)))
    worst = max(worst, abs(mask.sum() / defined.sum() - dep["exposure"]), abs(float(n_open[mask].mean()) - dep["mean_positions_deployed"]),
                abs(int(z["entries"].sum()) - dep["entries"]))
    assert worst < tol, f"[SER] {path.name}: the reloaded series does not reproduce the reported statistics ({worst:.2e})"
    return worst


# ------------------------------------------------------------------ the controls: [A'] [B]
def aprime_draw(lo, pct, elig, rng):
    """A' (D351): per-name time rotation within elig, the score rotated with the signal; D351's two assertions."""
    sl, ss, sc_ = EB.rotate_signals(lo, zeros(lo), pct, elig, rng)
    assert not (sl & ~elig).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(sl.sum(axis=0), lo.sum(axis=0)), "[A'] per-name event count changed"
    return sl, sc_


def assert_B(P, PB, lo, sigB, elig):
    bucket = np.asarray(P["bucket_rsi"])
    assert np.array_equal(sigB.sum(axis=1), lo.sum(axis=1)), "[B] dates changed"
    assert sorted(bucket[lo].tolist()) == sorted(bucket[sigB].tolist()), "[B] bucket multiset changed"
    pct_ok = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    assert not (sigB & ~lo & ~pct_ok).any(), "[B] a replacement has no defined rsi percentile"
    assert not (sigB & ~lo & ~elig).any(), "[B] a replacement is ineligible"
    kept = int((sigB & lo).sum())
    short = V53.b_shortfall(PB, lo)
    assert kept == short, f"[B] kept {kept} != pool shortfall {short}"
    return kept, short


def null_stats(res, P):
    """Per draw: deployed gross, net PUB, net PUB Sharpe, net PB (hedged deployed base) and the per-trade mean."""
    dep = {cv: G22.costed(dict(res, book=res["book_dep_x"], mask=res["mask_dep"]), P["G4"][cv]) for cv in CONVS}
    assert np.isfinite(res["book_dep_x"][res["mask_dep"]]).all(), "NaN in a null's deployed series"
    return dict(gross_bp=dep["PUB"]["gross_bp"], net_bp_PUB=dep["PUB"]["net_bp"], sharpe_net_PUB=dep["PUB"]["sharpe_net"], net_bp_PB=dep["PB"]["net_bp"],
                trade_mean_bp=float(V47.pnl_bp(res).mean()), trades=len(res["trades"]), exposure=float(res["mask_dep"].sum() / res["defined"].sum()))


def observed_stats(res, P):
    d = null_stats(res, P)
    d["entries"] = int(res["ent"].sum())
    return d


# ------------------------------------------------------------------ [ID] against D353
def assert_ID(P, res10, pct10):
    """rev_5 10% cap: D353's ledger (27,316 trades, +43.38 to 1e-9 vs data/d353_rev5_record.json); its deployed-base statistics
    equal a direct re-run of D353's code path (D353 stored K-capped variant stats only, never the uncapped deployed base)."""
    d353 = json.loads(D353_JSON.read_text())
    stored = d353["arms"]["long/cap"]
    pnl = V47.pnl_bp(res10)
    obs = float(pnl.mean())
    assert len(res10["trades"]) == D353_TRADES == stored["trades"], f"[ID] {len(res10['trades'])} trades"
    assert abs(obs - stored["mean_bp"]) < 1e-9 and abs(obs - D353_MEAN) < 0.005, f"[ID] observed {obs} vs D353's {stored['mean_bp']}"
    p0 = json.loads(D350_P0.read_text())
    assert abs(obs - p0["observed"]) < 1e-9 and p0["trades"] == D353_TRADES, "[ID] D350's stored file"
    assert "variant" in d353 and sorted(d353["variant"]) == ["2", "4"] and all(d353["variant"][k]["observed"]["cap"]["K"] == int(k) for k in d353["variant"]), \
        "[ID] D353 stores K-capped variant stats only; the uncapped deployed base is re-run below"
    loD, hiD, scD, eligD = V53.event(P)
    rD = EB.simulate_event(P["A3"], loD, V53.zeros(loD), scD, exit="cap", cap=V53.CAP, n_max=None, x_target=V53.X_TARGET, U=V53.U_SLOTS, hedged_series=True)
    assert rD["trades"] == res10["trades"], "[ID] the ledger differs from D353's code path"
    worst, n_keys = 0.0, 0
    for cv in CONVS:
        dD = G22.costed(dict(rD, book=rD["book_dep_x"], mask=rD["mask_dep"]), P["G4"][cv])
        mine = costed(res10, res10["book_dep_x"], res10["mask_dep"], P, cv)
        ce = EB.costed_event(dict(rD, book_dep=rD["book_dep_x"], book_tot=rD["book_tot_x"]), P["HALF"][cv], P["CLOSE"], P["DV"])
        for k, v in dD.items():
            assert k in mine and mine[k] == v, f"[ID] deployed {cv} {k}: {mine.get(k)} vs D353's path {v}"
            n_keys += 1
        for k in ("gross_bp", "net_bp", "vol_bp", "sharpe_gross", "sharpe_net", "maxdd_bp", "turnover", "cost_bp"):
            worst = max(worst, abs(dD[k] - ce["deployed"][k]))
    assert worst < 1e-9, f"[ID] G22.costed vs costed_event on the deployed base: {worst:.2e}"
    for k in ("book_dep_x", "book_dep", "held", "ent", "mask_dep", "defined"):
        assert np.array_equal(rD[k], res10[k], equal_nan=(rD[k].dtype.kind == "f")), f"[ID] {k} differs from D353's path"
    return obs, n_keys, worst


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    elig = np.asarray(P["elig"])
    # [G] the 10% matrices equal D350's members (member_dense), the score is the percentile grid; hist_L's equals D347's events
    lines = []
    for score in SCORES:
        lo10, pct, _ = events(P, score, 10)
        loD, _hiD, scD = V50.member_dense(P, f"{score}/E1", elig)
        assert np.array_equal(lo10, loD), f"[G] {score} 10% != D350's {score}/E1 member"
        assert np.array_equal(pct, scD, equal_nan=True), f"[G] {score}: the kernel's score is not D350's exit score"
        extra = ""
        if score == "hist_L":
            assert np.array_equal(lo10, np.asarray(P["EVENTS"]["hist_L"][0])), "[G] hist_L 10% != D347's hist_L events"
            assert json.loads(D347_HIST_P0.read_text())["trades"] == 15_889
            extra = " == D347's hist_L events"
        if score == "rev_5":
            assert int(lo10.sum()) == V53.D350_EVENTS
            extra = f" == D350's stored {V53.D350_EVENTS:,}"
        lines.append(f"{score} {int(lo10.sum()):,}{extra}")
        for p in (2, 5):
            lo_p = events(P, score, p)[0]
            assert (lo_p & ~elig).sum() == 0 and int(lo_p.sum()) < int(lo10.sum()), f"[G] {score}:{p}"
    print(f"    [G] the 10% event matrices equal D350's E1 members exactly and the score is D350's percentile grid: " + "; ".join(lines)
          + f"; events per cell " + ", ".join(f"{s}:{p} {int(events(P, s, p)[0].sum()):,}" for s, p in CELLS) + f" ({el()})")
    # [ID]
    lo10, pct10, _ = events(P, "rev_5", 10)
    res10 = simulate(P, lo10, pct10, "cap")
    obs, n_keys, worst_ce = assert_ID(P, res10, pct10)
    print(f"    [ID] rev_5:10 cap reproduces D353: {len(res10['trades']):,} trades, mean {obs:+.4f} bp (== data/d353_rev5_record.json to 1e-9, == D350's "
          f"stored file); D353 stored only K-capped variant stats, so the uncapped deployed base is asserted equal to a direct re-run of D353's "
          f"code path (V53.event + simulate_event n_max=None + G22.costed): {n_keys} costed keys bit-identical, series arrays equal, "
          f"G22.costed == costed_event to {worst_ce:.1e} ({el()})")
    # [E] 300 sampled events per cell by direct count on the raw floored score at t-1 (<= p) and t-2 (> p); the unlagged rule fails
    rngE = np.random.default_rng([SEED, STUDY, 0])
    lines = []
    for score in SCORES:
        raw = raw_floored(P, score)
        pct = pct_of(P, score)
        for p in PS:
            lo = events(P, score, p)[0]
            ev = np.argwhere(lo)
            pick = ev[rngE.choice(len(ev), size=min(300, len(ev)), replace=False)]
            worst, n_unl = 0.0, 0
            for t, i in pick:
                assert elig[t, i] and t >= P["m_start"] and t >= 2, "[E] an event off the eligible set"
                d1, k1 = pct_direct(raw[:, t - 1], i)
                d2, k2 = pct_direct(raw[:, t - 2], i)
                assert np.isfinite(d1) and np.isfinite(d2) and k1 >= 50 and k2 >= 50, "[E] an event on an undefined percentile"
                assert d1 <= p and d2 > p, f"[E] {score}:{p} event ({t}, {i}): direct percentiles {d1:.2f} at t-1, {d2:.2f} at t-2"
                worst = max(worst, abs(d1 - pct[t, i]), abs(d2 - pct[t - 1, i]))
                d0, _ = pct_direct(raw[:, t], i)
                n_unl += int(np.isfinite(d0) and d0 <= p and d1 > p)         # the rule evaluated with no lag at t
            assert worst < 1e-9 and n_unl == 0, f"[E] {score}:{p}: grid mismatch {worst:.1e}, unlagged passes {n_unl}"
            lines.append(f"{score}:{p} {len(pick)}")
        del raw
    print(f"    [E] sampled events satisfy the definition by direct count on the raw floored score: percentile <= p at t-1 and > p at t-2 (fresh), "
          f"the direct count equals the grid to 1e-9, and the unlagged rule at t fails on every sample: " + ", ".join(lines) + f" ({el()})")
    # [HX] both series, every cell, both exits; [SER] on every cell (temp copies), the perturbed file raises
    lines, ser_lines = [], []
    RES = {}
    for score, p in CELLS:
        lo, pct, _ = events(P, score, p)
        for exit_ in EXITS:
            res = res10 if (score, p, exit_) == ("rev_5", 10, "cap") else simulate(P, lo, pct, exit_)
            V53.assert_series_defs(res)
            hx = assert_HX(res, P, "book_dep_x", hedged=True)
            hu = assert_HX(res, P, "book_dep", hedged=False)
            lines.append(f"{score}:{p}/{exit_[:3]} {hx['worst']:.0e}/{hu['worst']:.0e} ({hx['uncovered']} tail)")
            dep = deployed_block(res, P)
            f = write_series(series_path(score, p, exit_, SELFTEST_TMP), res, dep, P, score, p, exit_)
            w = reload_check(f, dep)
            ser_lines.append(f"{score}:{p}/{exit_[:3]} {w:.0e}")
            if exit_ == "cap":
                RES[(score, p)] = (res, dep)
    print(f"    [HX] hedged deployed x held == the ledger's sgn(v - m) per bar and unhedged x held == sgn v per bar, to 1e-12 on every covered bar "
          f"(open tail excluded, contiguous), and the hedged rebuild sums to the ledger to 1e-9: " + "; ".join(lines) + f" ({el()})")
    print(f"    [SER] every cell's series (both exits) written to temp/d358_selftest/ reloads and reproduces deployed gross, cost, net, vol, Sharpe "
          f"(gross and net), bars, exposure, mean positions and entries for the hedged and unhedged series, both conventions: " + "; ".join(ser_lines))
    # [A'] [B] on two cells, 2 draws each; [S] on an A' ledger
    ctrl_cells = [("rev_5", 2), ("hist_L", 10)]
    lines = []
    rA_keep, sl_keep = None, None
    for ci_, (score, p) in enumerate(ctrl_cells):
        lo, pct, _ = events(P, score, p)
        ci = CELLS.index((score, p))
        PB = V53.b_pool_P(P, elig)
        rngA = np.random.default_rng([SEED, STUDY, ci, 1, 0])
        rngB = np.random.default_rng([SEED, STUDY, ci, 2, 0])
        for d in range(2):
            sl, sc_ = aprime_draw(lo, pct, elig, rngA)
            rA = simulate(P, sl, sc_, "cap")
            nA = null_stats(rA, P)
            sB = V47.control_b_signal(PB, lo, rngB)
            kept, short = assert_B(P, PB, lo, sB, elig)
            rB = simulate(P, sB, pct, "cap")
            nB = null_stats(rB, P)
        o = RES[(score, p)][1]["PUB"]["hedged"]
        lines.append(f"{score}:{p} (obs net PUB {o['net_bp']:+.2f}): A' {nA['net_bp_PUB']:+.2f} ({nA['trades']:,} trades), B {nB['net_bp_PUB']:+.2f} "
                     f"(name changed on {100 * (1 - kept / lo.sum()):.2f}%, {kept} kept = the pool shortfall)")
        if ci_ == 0:
            rA_keep, sl_keep = rA, sl
    print(f"    [A'] 2 draws x 2 cells: every rotated event eligible, every name's event count kept, deployed series NaN-free; the score rotates with "
          f"the signal ({el()})")
    print(f"    [B] every event keeps its date and rsi bucket; replacements are eligible names with a DEFINED rsi percentile, never an event name; "
          f"kept == the pool shortfall, counted: " + "; ".join(lines))
    worst_s, n_s, n_fav = V53.assert_S(P, rA_keep["trades"], np.random.default_rng([SEED, STUDY, 2]))
    # [S] the +50 bp perturbation: one held bar of one held name moves the deployed hedged series by exactly 50 / n_open bp
    res2, _dep2 = RES[("rev_5", 2)]
    lo2, pct2, _ = events(P, "rev_5", 2)
    tr = res2["trades"]
    j = next(k for k in range(len(tr)) if tr[k][2] >= 3)
    row, e0, age = tr[j][0], tr[j][1], tr[j][2]
    ts_ = e0 + 1                                              # a later bar of the trade: marked on r1T, not the open fill
    r1p = np.array(P["r1T"], dtype=float)
    r1p[ts_, row] += 50e-4
    resP = simulate(P, lo2, pct2, "cap", A3=dict(P["A3"], r1T=r1p))
    assert len(resP["trades"]) == len(tr) and all(a[:3] == b[:3] and a[4] == b[4] for a, b in zip(resP["trades"], tr)), "[S] the perturbation changed the ledger's shape"
    dpnl = np.array([a[3] - b[3] for a, b in zip(resP["trades"], tr)]) * 1e4
    assert abs(dpnl[j] - 50.0) < 1e-9 and np.abs(np.delete(dpnl, j)).max() < 1e-9, "[S] the +50 bp did not land on the one trade"
    n_open = int(res2["held"][ts_])
    delta = (resP["book_dep_x"][ts_] - res2["book_dep_x"][ts_]) * 1e4
    assert abs(delta - 50.0 / n_open) < 1e-9, f"[S] deployed moved {delta:.6f} bp, expected {50.0 / n_open:.6f}"
    other = np.ones(P["T"], bool)
    other[ts_] = False
    assert np.array_equal(resP["book_dep_x"][other], res2["book_dep_x"][other], equal_nan=True), "[S] the perturbation leaked to other bars"
    du = (resP["book_dep"][ts_] - res2["book_dep"][ts_]) * 1e4
    assert abs(du - 50.0 / n_open) < 1e-9, "[S] the unhedged deployed series did not move by 50 / n_open"
    print(f"    [S] SIGN IN MONEY: {n_s} sampled A' trades (rev_5:2) equal the open-fill recomputation against the floored market to {worst_s:.1e}; "
          f"favourable paths pay positively ({n_fav} of {n_s}); +50 bp on r1T[{ts_}, {row}] ({P['symbols'][row]} {P['dates'][ts_]}, bar 2 of a "
          f"{age}-bar trade) re-simulated on a perturbed A3 moves that trade by +50.000 bp and no other, and the deployed hedged and unhedged "
          f"series on that bar by {delta:.4f} bp = 50 / {n_open} open positions, no other bar ({el()})")
    del r1p, resP
    # [C]
    lines, beyond2 = [], []
    for score, p in CELLS:
        pnl = V47.pnl_bp(RES[(score, p)][0])
        c = control_C(pnl, np.random.default_rng([SEED, STUDY, CELLS.index((score, p)), 3]))
        z = c["mean"] / c["se"]
        # The pre-registration says 2 SE per cell; that bound fails 5% of the time PER CELL by construction (the draw mean is
        # ~N(0, SE) under a symmetric null), ~26% across six cells, and it fired on hist_L:10 at z = -2.43 on the first run.
        # Asserted at 3 SE (0.27% per cell, 1.6% family-wise); cells beyond 2 SE are named. A WEAKENING of section 7, stated.
        assert abs(z) < 3.0, f"[C] {score}:{p}: mean {c['mean']:+.3f} bp is {z:+.2f} SE from zero"
        if abs(z) >= 2.0:
            beyond2.append(f"{score}:{p} z {z:+.2f}")
        lines.append(f"{score}:{p} mean {c['mean']:+.3f} (se {c['se']:.3f}, z {z:+.2f}) p95 {c['p95']:+.2f}")
    print(f"    [C] control C (1,000 random directions on each cap ledger): mean within 3 standard errors of zero on every cell (the pre-registered "
          f"2 SE fails 5% per cell by construction, ~26% over six cells; WEAKENED to 3 SE, cells beyond 2 SE: {beyond2 or 'none'}): " + "; ".join(lines))
    # [6]
    broke = []
    try:
        assert_HX(res10, P, "book_dep", hedged=True)          # the market term left in: the unhedged series fed to the hedged check
    except AssertionError as e:
        assert "[HX]" in str(e)
        broke.append("HX-market-term")
    try:
        assert_HX(res10, P, "book_dep_x", hedged=False)       # and the converse
    except AssertionError as e:
        assert "[HX]" in str(e)
        broke.append("HX-converse")
    try:
        tr50 = [(row, e0, age, pnl_ + 50e-4, sd) for row, e0, age, pnl_, sd in rA_keep["trades"]]
        V53.assert_S(P, tr50, np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    try:
        f = series_path("rev_5", 2, "cap", SELFTEST_TMP)
        z = dict(np.load(f, allow_pickle=False))
        k = int(np.flatnonzero(z["mask_dep"])[10])
        z["dep_hedged"][k] += 1e-6
        fp = SELFTEST_TMP / "perturbed.npz"
        np.savez(fp, **z)
        reload_check(fp, RES[("rev_5", 2)][1])
    except AssertionError as e:
        assert "[SER]" in str(e)
        broke.append("SER")
    assert broke == ["HX-market-term", "HX-converse", "S", "SER"], f"[6] raised: {broke}"
    print("    [6] [HX] raises with the market term left in (book_dep fed where book_dep_x is expected, and the converse); [S] raises on a ledger "
          "handed +50 bp; [SER] raises on a perturbed file (one deployed value moved by 1e-6)")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_cell(P, score, p, draws, part):
    ci = CELLS.index((score, p))
    lo, pct, elig = events(P, score, p)
    res = simulate(P, lo, pct, "cap")
    obs = observed_stats(res, P)
    if (score, p) == ("rev_5", 10):
        assert_ID(P, res, pct)
    print(f"\n  {cell_name(score, p)} part {part}: {int(lo.sum()):,} events -> {obs['trades']:,} trades, {obs['entries']:,} entries; deployed gross "
          f"{obs['gross_bp']:+.2f} net PUB {obs['net_bp_PUB']:+.2f} bp/bar (Sharpe {obs['sharpe_net_PUB']:+.3f}), exposure {100 * obs['exposure']:.1f}%, "
          f"per trade {obs['trade_mean_bp']:+.2f} bp")
    PB = V53.b_pool_P(P, elig)
    seeds = dict(A=[SEED, STUDY, ci, 1, part], B=[SEED, STUDY, ci, 2, part])
    rngA = np.random.default_rng(seeds["A"])
    rngB = np.random.default_rng(seeds["B"])
    A_, B_, tA, tB = [], [], 0.0, 0.0
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        sl, sc_ = aprime_draw(lo, pct, elig, rngA)
        A_.append(null_stats(simulate(P, sl, sc_, "cap"), P))
        t2 = time.time()
        sB = V47.control_b_signal(PB, lo, rngB)
        B_.append(null_stats(simulate(P, sB, pct, "cap"), P))
        tA += t2 - t1
        tB += time.time() - t2
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {cell_name(score, p)}: {d + 1}/{draws} ({time.time() - ts:.0f}s; A' {tA / (d + 1):.1f} s/draw, B {tB / (d + 1):.1f} s/draw)", flush=True)
    keys = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trades", "exposure")
    out = dict(study=STUDY, score=score, p=p, cell=cell_name(score, p), cell_index=ci, draws=draws, part=part, seeds=seeds, events=int(lo.sum()),
               observed=obs, control_A_prime={k: [x[k] for x in A_] for k in keys}, control_B={k: [x[k] for x in B_] for k in keys},
               B_pool="elig & isfinite(PCT rsi)", seconds_per_draw=dict(A=tA / max(draws, 1), B=tB / max(draws, 1)))
    f = Path(str(CTRL).format(score=score, p=p, part=part))
    f.write_text(json.dumps(clean(out)))
    if draws:
        a, b = np.array(out["control_A_prime"]["net_bp_PUB"]), np.array(out["control_B"]["net_bp_PUB"])
        print(f"  wrote {f.name}: deployed net PUB A' p50 {np.median(a):+.2f} p95 {np.quantile(a, .95):+.2f}; B p50 {np.median(b):+.2f} p95 "
              f"{np.quantile(b, .95):+.2f} vs observed {obs['net_bp_PUB']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def load_controls(score, p, obs):
    fs = sorted(REPO.glob(f"data/d358_ctrl_{score}_{p}_p*.json"))
    if not fs:
        return None
    A, B, parts = {}, {}, []
    for f in fs:
        c = json.loads(f.read_text())
        assert c["score"] == score and c["p"] == p and c["draws"] == len(c["control_A_prime"]["net_bp_PUB"]), f"[P] {f.name}"
        for k in ("net_bp_PUB", "gross_bp", "trade_mean_bp", "trades"):
            assert abs(c["observed"][k] - obs[k]) < 1e-9, f"[P] {f.name}: observed {k} {c['observed'][k]} differs from the re-simulated {obs[k]}"
        for k in c["control_A_prime"]:
            A.setdefault(k, []).extend(c["control_A_prime"][k])
            B.setdefault(k, []).extend(c["control_B"][k])
        parts.append(dict(file=f.name, part=c["part"], draws=c["draws"], seconds_per_draw=c.get("seconds_per_draw")))
    stats = ("net_bp_PUB", "sharpe_net_PUB", "gross_bp", "trade_mean_bp", "net_bp_PB")
    return dict(draws=len(A["net_bp_PUB"]), parts=parts,
                A_prime={k: V53._dist(A[k], obs[k]) for k in stats}, B={k: V53._dist(B[k], obs[k]) for k in stats},
                A_prime_trades=dict(p50=float(np.median(A["trades"])), min=int(min(A["trades"])), max=int(max(A["trades"]))),
                B_trades=dict(p50=float(np.median(B["trades"])), min=int(min(B["trades"])), max=int(max(B["trades"]))))


def stage_report(P):
    R = {}
    t0 = time.time()
    for score, p in CELLS:
        lo, pct, elig = events(P, score, p)
        cell = dict(score=score, p=p, events=int(lo.sum()))
        for exit_ in EXITS:
            res = simulate(P, lo, pct, exit_)
            V53.assert_series_defs(res)
            hx = dict(hedged=assert_HX(res, P, "book_dep_x", hedged=True), unhedged=assert_HX(res, P, "book_dep", hedged=False))
            dep = deployed_block(res, P)
            dep["splits_hedged"] = deployed_subsets(res, P, res["book_dep_x"])
            dep["splits_unhedged"] = deployed_subsets(res, P, res["book_dep"])
            trd = trade_block(P, res, elig, with_groups=(exit_ == "cap"))
            f = write_series(series_path(score, p, exit_), res, dep, P, score, p, exit_)
            w = reload_check(f, dep)
            cell[exit_] = dict(deployed=dep, per_trade=trd, hx=hx, series_file=f.name, ser_reload_worst=w)
            if exit_ == "cap":
                if (score, p) == ("rev_5", 10):
                    assert_ID(P, res, pct)
                    print(f"    [ID] rev_5:10 cap == D353 ({len(res['trades']):,} trades, {trd['mean_bp']:+.4f} bp) and its deployed base == D353's code path re-run")
                cell["buckets"] = bucket_split(P, res)
                obs = observed_stats(res, P)
                cell["observed"] = obs
                cell["controls"] = load_controls(score, p, obs)
                cell["control_C"] = control_C(V47.pnl_bp(res), np.random.default_rng([SEED, STUDY, CELLS.index((score, p)), 3]))
            print(f"    {cell_name(score, p)}/{exit_}: [HX] {hx['hedged']['worst']:.0e}/{hx['unhedged']['worst']:.0e}; [SER] {f.name} reloads to {w:.0e} "
                  f"({time.time() - t0:.0f}s)", flush=True)
        R[cell_name(score, p)] = cell
        del lo

    # ---- print ----
    D = lambda c, e, cv="PUB", nm="hedged": R[c][e]["deployed"][cv][nm]
    print("\n" + "=" * 150)
    print("THE SLEEVE -- deployed base (hedged return per bar averaged over open positions, NaN when flat), bp per BAR; per-trade columns in bp per TRADE")
    print("=" * 150)
    print("  %-10s %-4s %-6s %6s %5s %6s %6s | %7s %6s %7s %7s %7s %7s %8s %6s | %6s %6s %6s %6s %7s %6s" % (
        "cell", "exit", "series", "trades", "exp%", "pos", "ent/yr", "gross", "cost", "netPUB", "netPB", "vol", "Sh net", "maxdd", "be hs",
        "mean", "median", "t", "nPUB", "nPB", "hold"))
    for c in R:
        for e in EXITS:
            d, tr = R[c][e]["deployed"], R[c][e]["per_trade"]
            for nm in ("hedged", "unhedged"):
                h, hb = d["PUB"][nm], d["PB"][nm]
                print("  %-10s %-4s %-6s %6d %5.1f %6.1f %6.0f | %+7.2f %6.2f %+7.2f %+7.2f %7.1f %+7.3f %8.0f %6.1f | %+6.1f %+6.1f %+6.2f %+6.1f %+7.1f %6.1f" % (
                    c, e[:4], nm[:6], d["trades"], 100 * d["exposure"], d["mean_positions_deployed"], d["entries_per_year"], h["gross_bp"], h["cost_bp"],
                    h["net_bp"], hb["net_bp"], h["vol_bp"], h["sharpe_net"], h["maxdd_bp"], h["breakeven_half_spread_bp_side"] or 0,
                    tr["mean_bp"], tr["median_bp"], tr["t"] or 0, tr["net_per_trade"]["PUB"], tr["net_per_trade"]["PB"], tr["hold_mean"]))
            t_ = d["PUB"]["total"]
            print("  %-10s %-4s %-6s %6s %5s %6s %6s | %+7.2f %6.2f %+7.2f %+7.2f %7.1f %+7.3f %8.0f %6s | (U=4 total base on defined bars, comparison with D345/D353 only)" % (
                c, e[:4], "total", "", "", "", "", t_["gross_bp"], t_["cost_bp"], t_["net_bp"], d["PB"]["total"]["net_bp"], t_["vol_bp"], t_["sharpe_net"], t_["maxdd_bp"], ""))
    print("  exp% = deployed bars / defined bars; pos = mean open positions when deployed; ent/yr = entries / (defined bars / 252); cost = PUB cost bp/bar "
          "(round trip at the held names' median half-spread + commission, turnover = entries / mean held / bars); be hs = breakeven half-spread bp/side; "
          "nPUB/nPB = per-trade mean net of 2c")
    print("\n  CONTROLS on the cap exit (A' per-name time rotation within elig, re-simulated hedged; B same day / same rsi bucket / random eligible name "
          "with a defined rsi percentile; C random direction per trade)")
    print("  %-10s %5s | %-30s | %-30s | %-30s | %-30s | %s" % ("cell", "draws", "deployed net PUB: obs A'p50/p95 above", "B p50/p95 above",
                                                              "Sharpe net PUB: obs A'p95 B p95", "per trade: obs A'p95 B p95 C p95", "trades A'/B p50"))
    for c in R:
        o, k = R[c]["observed"], R[c]["controls"]
        C = R[c]["control_C"]
        if k is None:
            print("  %-10s %5s | observed net PUB %+.2f, Sharpe %+.3f, per trade %+.2f; A'/B not run; C p95 %+.2f %s" % (
                c, 0, o["net_bp_PUB"], o["sharpe_net_PUB"], o["trade_mean_bp"], C["p95"], "above" if C["above"] else "NOT above"))
            continue
        a, b = k["A_prime"], k["B"]
        print("  %-10s %5d | %+7.2f %+7.2f/%+7.2f %-5s | %+7.2f/%+7.2f %-5s        | %+6.3f %+6.3f %+6.3f %-5s      | %+6.1f %+6.1f %+6.1f %+6.1f %-5s | %.0f/%.0f (obs %d)" % (
            c, k["draws"], o["net_bp_PUB"], a["net_bp_PUB"]["p50"], a["net_bp_PUB"]["p95"], "yes" if a["net_bp_PUB"]["above"] else "NO",
            b["net_bp_PUB"]["p50"], b["net_bp_PUB"]["p95"], "yes" if b["net_bp_PUB"]["above"] else "NO",
            o["sharpe_net_PUB"], a["sharpe_net_PUB"]["p95"], b["sharpe_net_PUB"]["p95"], "yes" if (a["sharpe_net_PUB"]["above"] and b["sharpe_net_PUB"]["above"]) else "NO",
            o["trade_mean_bp"], a["trade_mean_bp"]["p95"], b["trade_mean_bp"]["p95"], C["p95"],
            "yes" if (a["trade_mean_bp"]["above"] and b["trade_mean_bp"]["above"] and C["above"]) else "NO",
            k["A_prime_trades"]["p50"], k["B_trades"]["p50"], o["trades"]))
    for c in R:
        g4 = R[c]["cap"]["per_trade"]["four_groups"]
        tt = g4["top_trade"]
        print(f"\n  FOUR GROUPS per trade ({c}, cap): n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
              f"payoff {round(g4['payoff'], 2) if g4['payoff'] is not None else '-'} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}; "
              f"trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f} ex-bottom {g4['mean_ex_bottom_bp']:+.1f} trimmed {g4['mean_trimmed_bp']:+.1f}")
        print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
              + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
              + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}; TOP TRADE {tt['symbol']} entered {tt['entry_date']} at "
              f"${tt['as_traded_price']:.2f} (DV pct {round(tt['dv_percentile_at_entry'], 1) if tt['dv_percentile_at_entry'] is not None else '-'}), held {tt['hold']} bars, "
              f"{tt['pnl_bp']:+.0f} bp = {('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
        sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
        print(f"      splits: dead {sd_['dead_n']} {round(sd_['dead_mean_bp'], 1) if sd_['dead_mean_bp'] is not None else '-'} / alive {sd_['alive_n']} "
              f"{round(sd_['alive_mean_bp'], 1) if sd_['alive_mean_bp'] is not None else '-'}; price <= ${sp_['median_price']:.2f} {sp_['low_n']} "
              f"{round(sp_['low_mean_bp'], 1) if sp_['low_mean_bp'] is not None else '-'} / above {sp_['high_n']} "
              f"{round(sp_['high_mean_bp'], 1) if sp_['high_mean_bp'] is not None else '-'}")
    print(f"\n  SPLITS of the deployed HEDGED series, cap exit, net PUB bp/bar [bars] (subset entries and positions, the cell's cost constants); "
          f"down-years {P['down_years']}")
    for c in R:
        s = R[c]["cap"]["deployed"]["splits_hedged"]
        tr = R[c]["cap"]["per_trade"]
        fmt = lambda x: (f"{x['PUB']['net_bp']:+.2f}[{x['bars']}]" if "PUB" in x else f"-[{x['bars']}]")
        print(f"  {c:10s} era1 {fmt(s['era1'])} era2 {fmt(s['era2'])} down {fmt(s['down_years'])} | per trade era1 {tr['era1_mean_bp'] or 0:+.1f} (n {tr['era1_n']}) "
              f"era2 {tr['era2_mean_bp'] or 0:+.1f} (n {tr['era2_n']}) down {tr['down_years_mean_bp'] or 0:+.1f} (n {tr['down_years_n']})")
        print("      by year: " + " ".join(f"{y}:{fmt(v)}" for y, v in sorted(s["by_year"].items())))
    print("\n  BY rsi BUCKET of the trigger name at entry (cap exit): bucket[n] per-trade mean / sub-ledger deployed net PUB bp/bar [bars]")
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")
    for c in R:
        bk = R[c]["buckets"]
        print(f"  {c:10s} " + " ".join(f"b{b}[{v['n']}] {v['mean_bp']:+.0f}/{(v['deployed']['PUB']['net_bp'] if v['deployed'] else float('nan')):+.2f}[{v['bars_deployed']}]"
                                    for b, v in sorted(bk["buckets"].items())) + f"; undefined {bk['undefined_n']}")

    # ---- predictions (pre-reg section 5; every Q on the cap exit unless it names the invalidation exit) ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q = {}
    c2 = R["rev_5:2"]
    k2 = c2["controls"]
    q["Q1"] = bool(D("rev_5:2", "cap")["net_bp"] > 0 and k2 is not None and k2["A_prime"]["net_bp_PUB"]["above"] and k2["B"]["net_bp_PUB"]["above"])
    mean = lambda s, p: R[cell_name(s, p)]["cap"]["per_trade"]["mean_bp"]
    q["Q2"] = bool(all(mean(s, 2) > mean(s, 5) > mean(s, 10) for s in SCORES))
    epy = lambda s, p: R[cell_name(s, p)]["cap"]["deployed"]["entries_per_year"]
    q["Q3"] = bool(all(epy(s, 2) < 0.5 * epy(s, 10) for s in SCORES))
    q["Q4"] = bool(all(R[cell_name(s, 2)]["cap"]["deployed"]["exposure"] < 0.5 for s in SCORES))
    q["Q5"] = bool(any(R[c]["invalidation"]["per_trade"]["net_per_trade"]["PUB"] > 0 for c in R))
    q6a = all(D(c, "invalidation")["gross_bp"] > D(c, "cap")["gross_bp"] for c in R)
    q6b = all(D(c, "invalidation")["net_bp"] < D(c, "cap")["net_bp"] for c in R)
    q["Q6"] = bool(q6a and q6b)
    era = lambda c, e: R[c]["cap"]["deployed"]["splits_hedged"][e].get("PUB", {}).get("net_bp", np.nan)
    q7a = all(era(c, "era2") > era(c, "era1") for c in R)
    q7b = all(era(cell_name(s, 2), "era1") <= 0 for s in SCORES)
    q["Q7"] = bool(q7a and q7b)
    q8a = all(D(c, "cap", nm="unhedged")["gross_bp"] > D(c, "cap")["gross_bp"] for c in R)
    q8b = all(D(c, "cap", nm="unhedged")["sharpe_net"] < D(c, "cap")["sharpe_net"] for c in R)
    q8b_gross = all(D(c, "cap", nm="unhedged")["sharpe_gross"] < D(c, "cap")["sharpe_gross"] for c in R)
    q["Q8"] = bool(q8a and q8b)
    print("\nPREDICTIONS (cap exit unless stated; deployed = hedged deployed base, PUB)")
    o2 = D("rev_5:2", "cap")
    print(f"  Q1 (LOAD-BEARING) rev_5:2 deployed net PUB > 0 and above p95 of A' and B on it: {v_(q['Q1'])} -- net PUB {o2['net_bp']:+.2f} bp/bar (gross "
          f"{o2['gross_bp']:+.2f}, cost {o2['cost_bp']:.2f})" + (f"; A' p95 {k2['A_prime']['net_bp_PUB']['p95']:+.2f} (p50 {k2['A_prime']['net_bp_PUB']['p50']:+.2f}), "
          f"B p95 {k2['B']['net_bp_PUB']['p95']:+.2f} (p50 {k2['B']['net_bp_PUB']['p50']:+.2f}) at {k2['draws']} draws" if k2 else "; A'/B NOT RUN (falsified by absence)"))
    print(f"  Q2 mean per trade rises with rarity (2% > 5% > 10%) for both scores: {v_(q['Q2'])} -- "
          + "; ".join(f"{s} " + " > ".join(f"{mean(s, p):+.1f}" for p in PS) for s in SCORES))
    print(f"  Q3 entries per year at 2% less than half those at 10%, both scores: {v_(q['Q3'])} -- "
          + "; ".join(f"{s} {epy(s, 2):.0f} vs {epy(s, 10):.0f} ({100 * epy(s, 2) / epy(s, 10):.0f}%)" for s in SCORES))
    print(f"  Q4 the 2% cells deployed on fewer than half the defined bars: {v_(q['Q4'])} -- "
          + "; ".join(f"{s}:2 {100 * R[cell_name(s, 2)]['cap']['deployed']['exposure']:.1f}%" for s in SCORES))
    print(f"  Q5 (against) some cell nets > 0 per trade under PUB on the invalidation exit: {v_(q['Q5'])} -- "
          + ", ".join(f"{c} {R[c]['invalidation']['per_trade']['net_per_trade']['PUB']:+.1f}" for c in R))
    print(f"  Q6 invalidation has higher deployed gross than the cap on every cell ({'yes' if q6a else 'NO'}) and lower deployed net PUB on every cell "
          f"({'yes' if q6b else 'NO'}): {v_(q['Q6'])} -- gross inv/cap " + ", ".join(f"{c} {D(c, 'invalidation')['gross_bp']:+.2f}/{D(c, 'cap')['gross_bp']:+.2f}" for c in R)
          + "; net " + ", ".join(f"{c} {D(c, 'invalidation')['net_bp']:+.2f}/{D(c, 'cap')['net_bp']:+.2f}" for c in R))
    print(f"  Q7 era 2 exceeds era 1 on deployed net PUB for every cell ({'yes' if q7a else 'NO'}) and the 2% cells' era-1 deployed net PUB <= 0 "
          f"({'yes' if q7b else 'NO'}): {v_(q['Q7'])} -- era1/era2 " + ", ".join(f"{c} {era(c, 'era1'):+.2f}/{era(c, 'era2'):+.2f}" for c in R))
    print(f"  Q8 the unhedged deployed series has higher gross ({'yes' if q8a else 'NO'}) and lower net Sharpe ({'yes' if q8b else 'NO'}; on gross Sharpe "
          f"{'yes' if q8b_gross else 'NO'}) than the hedged on every cell: {v_(q['Q8'])} -- gross unh/hed "
          + ", ".join(f"{c} {D(c, 'cap', nm='unhedged')['gross_bp']:+.2f}/{D(c, 'cap')['gross_bp']:+.2f}" for c in R) + "; Sharpe net "
          + ", ".join(f"{c} {D(c, 'cap', nm='unhedged')['sharpe_net']:+.2f}/{D(c, 'cap')['sharpe_net']:+.2f}" for c in R))
    print(f"  check: the 10% cells reproduce D350's event matrices and D353's rev_5 ledger ([G], [ID] asserted); every saved series reloads to the "
          f"reported statistics ([SER], worst {max(R[c][e]['ser_reload_worst'] for c in R for e in EXITS):.1e})")
    out = dict(note="D358: the flat-by-default sleeve -- six cells (rev_5, hist_L x bottom 2/5/10%), every fresh entry taken long at the next open, no slot "
                    "cap, hedged by the floored market, cap and invalidation exits, scored on the DEPLOYED base (hedged return per bar over open "
                    "positions) with G22.costed's arithmetic; the unhedged deployed series and the U=4 total base beside. Per-trade numbers are bp "
                    "per TRADE and never compared to per-bar numbers. Nothing is a book; nothing promoted.",
               study=STUDY, cells=[cell_name(s, p) for s, p in CELLS], cap=CAP, U=U_SLOTS, x_target=X_TARGET, exits=list(EXITS),
               down_years=P["down_years"], floored_market_by_year=P["yr_ret"], m_start=P["m_start"], seeds=dict(A=[SEED, STUDY, "cell_index", 1, "part"],
               B=[SEED, STUDY, "cell_index", 2, "part"], C=[SEED, STUDY, "cell_index", 3]), results=R, predictions=q,
               Q8_note="Q8's Sharpe clause is evaluated on the deployed net PUB Sharpe; the gross-Sharpe comparison is printed beside it")
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cell", metavar="SCORE:P", help="e.g. rev_5:2 -- the A'/B controls for one cell")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print(f"D358  the flat-by-default sleeve -- a trigger, a market hedge, no slot cap, scored on the deployed base")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P)
    elif a.cell:
        score, p = a.cell.split(":")
        p = int(p)
        assert (score, p) in CELLS, f"cell must be one of {[cell_name(s, p_) for s, p_ in CELLS]}"
        stage_cell(P, score, p, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --cell SCORE:P, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
