"""D361 EXPORT -- every T2 event of the G2:T2 cell (D360's gap-up fade entered SHORT, gated by the index below its 200-bar mean), one row
per event, with the gate, the trigger, the name's lagged state, every score percentile in the cache, the borrow, the kernel's outcome in
three runs (ungated / G2-gated / G1-gated, cap 10), the forward path from the entry open, and the hindsight status -- a DATA ARTEFACT for
the principal's own analysis. Nothing here is a result.

    uv run python scripts/d361_export_trades.py                 writes data/d361_trades_gap_up_fade.{csv,dict.json,README.md}
    uv run python scripts/d361_export_trades.py --out-dir DIR   elsewhere (smoke)

Everything is imported from the committed runners, never re-derived: run_d361 (gate_pack, gate_loop, triggers, arms_of, run_short),
run_d360 (signal_grids: OPEN, gap, rv, the percentile grids, the exclusions; rv_direct), run_d359 (grids), run_d358 (pct_of, pct_direct),
run_d350 (lagged), run_d349 (borrow_of), d345_event_book (the kernel, through run_short), d348_prep (P).

ROWS: every RAW T2 candidate on day g (pct_gap >= 98 & pct_rv >= 90 on the cross-section cs = eligible at g+1 with a finite gap and rv):
24,750 = the 24,736 events D361 traded + the 14 D360 excluded on an ex-distribution day ([XD]; none on [V0]/[NF]). The excluded rows are
kept with `excluded_reason` set; they are in no arm and no run. Sorted by (bar_g, row).

SIGN: pnl > 0 means the SHORT made money. pnl = -sum over held bars of (v - m): the entry bar on (ocT - m_f_oc), later bars on (r1T - m_f),
the kernel's own accumulation order (bit-identical, [PATH]).

THREE RUNS, one kernel: the ungated T2 ledger (20,621 trades), the G2-gated (3,977; the cell) and the G1-gated (beside). Which events are
SKIPPED ('held': the name already carries a position) differs between the runs because the books differ -- the gate removes positions,
so a name free in the gated run can be held in the ungated one and vice versa. A trade's hold and P&L depend only on (row, e0): identical
in every run that takes it (asserted).

TWO PERCENTILES PER SCORE. `pct_<score>` is run_d358.pct_of: the score behind the programme's SHARED base (P['base'] = the cache's `warm`
& live, i.e. signals_ragged's need = max(impulse_warm_up_bars 1,000, warm_up_bars 393, U.WINDOW 252) of the name's OWN bars) -- so every
score is NaN for a name's first 1,000 bars whatever its own window, and 42% of rows carry no pct_ at all (100% in 2010-2013). `pcto_<score>`
is the SAME construction without P['base']: the score's own NaN pattern, as its builder wrote it, governs (own_warm_declared: read from the
family modules' constants, verified against the cache by [WARM]). The cross-section is larger, so the values differ; the record's studies
use pct_ and the two are not interchangeable for reproducing one. hist_L / md are the one family whose builder used the shared warm (the
Impulse IIR burn-in), so their pcto_ equals their pct_ (asserted).

ASSERTIONS (every one prints; any failure aborts before anything is written under --out-dir):
  [N] [XD] [GATE] [LEDGER] [REPLAY] [PATH] [LAG] [WARM] [OWN-LAG] [OWN-SUB] [SB] [FIX] [SAME] [6]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import importlib.util
import io
import json
import math
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


V61 = _load("d361r", "run_d361_regime_gated_short.py")       # loads d348_prep FIRST (memo_load installed there), then run_d360, run_d359
PREP, V60, V59, V58, V49, V47, V50 = V61.PREP, V61.V60, V61.V59, V61.V58, V61.V49, V61.V47, V61.V50
EB, BR = V61.EB, V61.BR
UF = PREP.UF                                                 # d339_universe_floor: apply_floor_replace (the floor as pct_of applies it)
BC = PREP.R.BC                                               # d290_build_cache: the family modules (B, PS, RF, PR, VS, SS, AN, ST), AXES, AXIS_OF
IMPULSE = ("hist_L", "md")                                   # the one family whose builder used the SHARED warm (signals_ragged's need)
SEED, STUDY = V61.SEED, V61.STUDY
CAP = 10
HORIZON = 20
P_GAP, Q_RV = V61.T2_PARENT                                  # (2, 10): pct_gap >= 98, pct_rv >= 90
DATA = REPO / "data"
REPORT = DATA / "d361_regime_gated_short.json"
META = DATA / "fixtures" / "us_shorts_daily_raw.meta.json"
FIXTURE = V60.FIXTURE
STEM = "d361_trades_gap_up_fade"
RUNS = ("ungated", "G2", "G1")
NON_SCORES = ("key", "warm")                                 # the npz members that are not scores


def el(t0):
    return f"{time.time() - t0:.0f}s"


# ------------------------------------------------------------------ the would-be hold: a second implementation that never calls the kernel
def hold_of(finT, T, last_live, e0, row, cap=CAP):
    """(hold, exit_reason, in_ledger) for a position opened at e0 on row under D345's cap exit: marked on e0 .. while priced, at most cap
    bars; it exits at bar x = e0 + hold (the first bar it is not marked) -- by the cap (hold == cap), or because bar x is unpriced
    ('delist' if x is after the name's last live bar, 'hole' if the name is priced again later). If x >= T the kernel never closes it:
    'open_at_end', absent from the ledger. Returns hold 0 / 'unpriced' if e0 itself is unpriced (the kernel cannot enter it)."""
    if not finT[e0, row]:
        return 0, "unpriced", False
    j = e0 + 1
    stop = min(e0 + cap, T)
    while j < stop and finT[j, row]:
        j += 1
    hold = j - e0
    if j >= T:
        return hold, "open_at_end", False
    if hold == cap:
        return hold, "cap", True
    return hold, ("delist" if j > last_live[row] else "hole"), True


def replay(ev_t, ev_row, in_arm, holds, finT, n):
    """The arm's events in (t, row) order through the kernel's rule without the kernel: taken iff priced at t and the name carries no
    position (a position opened at e0 with hold h frees the name from bar e0 + h). Returns (taken, reason)."""
    free_from = np.zeros(n, int)
    N = ev_t.size
    taken = np.zeros(N, bool)
    reason = np.array([""] * N, dtype=object)
    for i in range(N):
        if not in_arm[i]:
            continue
        t, r = int(ev_t[i]), int(ev_row[i])
        if not finT[t, r]:
            reason[i] = "unpriced"
        elif t < free_from[r]:
            reason[i] = "held"
        else:
            taken[i] = True
            free_from[r] = t + holds[i]
    return taken, reason


# ------------------------------------------------------------------ the fixture, streamed once for the bars the rows need
def stream_bars(want):
    """{(symbol, date): (open, high, low, close, volume)} for the wanted keys, read from the raw fixture by the strings alone."""
    out = {}
    with gzip.open(FIXTURE, "rt") as f:
        r = csv.reader(f)
        head = next(r)
        c = {k: head.index(k) for k in ("timestamp", "symbol", "open", "high", "low", "close", "volume")}
        for row in r:
            k = (row[c["symbol"]], row[c["timestamp"]][:10])
            if k in want:
                assert k not in out, f"[FIX] duplicate raw bar {k}"
                out[k] = tuple(float(row[c[x]]) for x in ("open", "high", "low", "close", "volume"))
    return out


# ------------------------------------------------------------------ the dictionary
def fmt(x):
    if isinstance(x, (float, np.floating)):
        return "" if not np.isfinite(x) else repr(float(x))
    if isinstance(x, (bool, np.bool_)):
        return "1" if x else "0"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return "" if x is None else str(x)


# ------------------------------------------------------------------ the scores' OWN warm-up (pcto_): declared by the builders, verified against the cache
def own_warm_declared():
    """Per score: the builder's own warm-up as the first admissible OWN-BAR index (0-based: how many of the name's live bars must precede
    the value), the module that wrote the cache grid, and the rule -- read from the family modules' constants, never typed here. A score's
    builder may withhold a value LATER than this by its own rule (no level yet, a zero-range bar, |gap| below 50 bp): that is the score's
    NaN pattern, not a warm-up, and pcto_ carries it as pct_ does."""
    B, PS, RF, PR, VS, SS, AN, ST = BC.B, BC.PS, BC.RF, BC.PR, BC.VS, BC.SS, BC.AN, BC.ST
    need = max(B.M.impulse_warm_up_bars(), B.M.warm_up_bars(), B.U.WINDOW)
    prof = PR.VolumeProfileSensor(PR.LOOKBACK_BARS, PR.BUCKET_ATR, PR.VOLUME_UNITS, atr_window=PR.ATR_WINDOW).warm_up_bars() + 1
    W = {}

    def add(s, bars, module, rule):
        W[s] = dict(axis=BC.AXIS_OF[s], module=module, warm_bars=int(bars), rule=rule)

    for s in IMPULSE:
        add(s, need, "run_book_single_names.signals_ragged (run_activation_threshold.log_parts)",
            f"the family's SHARED need = max(M.impulse_warm_up_bars() {B.M.impulse_warm_up_bars()}, M.warm_up_bars() {B.M.warm_up_bars()}, U.WINDOW "
            f"{B.U.WINDOW}) own bars, written as the cache's `warm` member (warm[i, at[need:]]); the raw grid seeds earlier (the zlema / SMA seed, "
            "an unburned IIR) but the family declares the burn-in, so pcto_ is masked at need and equals pct_")
    for s, b in PS.WARM_UP_BARS.items():
        add(s, b, "ragged_price_scores.price_scores", "WARM_UP_BARS[score] (the score's own seed + IIR burn-in), warm[k][i, at[need:]]; the cache is "
            "already NaN before it (np.where(pwarm, price, nan) in d290_build_cache)")
    for s in RF.INTRABAR_SCORES:
        add(s, 1 if s == "gap_frac" else 0, "ragged_features.intrabar_scores", "per-bar shape, no window" + ("; needs the previous live close"
            if s == "gap_frac" else "") + "; NaN on a zero-range or malformed bar")
    for s in RF.VOL_SCORES:
        add(s, RF.LOOKBACK_SESSIONS + (RF.TREND_BARS - 1 if s == "vol_trend" else 0), "ragged_features.volume_scores",
            f"the {RF.LOOKBACK_SESSIONS} PRIOR own sessions (j < LOOKBACK_SESSIONS: continue)" +
            (f", then {RF.TREND_BARS} finite rel_vol bars" if s == "vol_trend" else ""))
    for s in PR.PROFILE_SCORES:
        add(s, prof, "ragged_profile.build_profile_scores", f"VolumeProfileSensor(lookback {PR.LOOKBACK_BARS}, atr_window {PR.ATR_WINDOW}).warm_up_bars() "
            f"+ 1 = {prof}; NaN where no HVN / LVN level exists")
    trail = (f"ragged_vol_scores._trail over the name's OWN bars: a w-bar window ending at the bar, NaN-padded before it, needs ceil(MIN_FRAC x w) "
             f"finite values (MIN_FRAC {VS.MIN_FRAC}) -- first at own bar w-1; a return-based window then holds w-1 returns (bar 0 has no prior close), "
             "the same partial-window rule pct_ carries across internal holes")
    for s, w in (("atr_norm", VS.ATR_BARS), ("cs_spread", VS.CS_BARS), ("rvol21", VS.RVOL_BARS), ("vol_ratio", VS.SLOW_BARS), ("range_over_atr", VS.ATR_BARS)):
        add(s, w - 1, "ragged_vol_scores.vol_level_scores", f"w = {w}; " + trail)
    for s in SS.SESSION_SCORES:
        add(s, SS.WINDOW - 1, "ragged_session_scores.session_scores", f"w = WINDOW {SS.WINDOW}; " + trail + "; overnight legs only on consecutive own bars")
    for s, w in (("max_ret_21", AN.MAX_BARS), ("ivol_21", AN.IVOL_BARS), ("beta_63", AN.BETA_BARS), ("rev_5", AN.REV_FAST), ("rev_21", AN.REV_SLOW),
                 ("mom_252_21", AN.MOM_LONG), ("skew_63", AN.SKEW_BARS), ("amihud_21", AN.AMIHUD_BARS), ("dist_52w_high", AN.HIGH_BARS)):
        add(s, w - 1, "ragged_anomaly_scores.anomaly_scores", f"w = {w}; " + trail)
    add("price_log", 0, "ragged_anomaly_scores.anomaly_scores", "log of the as-traded close, per bar")
    for s in ("fvg_dist", "fvg_signed"):
        add(s, ST.ATR_BARS - 1, "ragged_structure_scores.structure_scores", f"the price ATR (w = {ST.ATR_BARS}; " + trail + ") AND a live fair-value gap "
            f"at most {ST.FRESH_BARS} bars old -- the first gap forms per name, later than the ATR")
    add("struct_trend", 0, "ragged_structure_scores.structure_scores", "market_structure's trend state, defined from bar 0")
    add("retrace_leg", ST.ATR_BARS - 1, "ragged_structure_scores.structure_scores", f"the price ATR (w = {ST.ATR_BARS}) AND confirmed pivots (K = {ST.K}) "
        f"within {ST.FRESH_BARS} bars with a leg > 0.5 ATR -- later than the ATR per name")
    add("choch_dist", ST.ATR_BARS - 1, "ragged_structure_scores.structure_scores", f"the price ATR (w = {ST.ATR_BARS}) AND a live change-of-character level "
        f"within {ST.FRESH_BARS} bars -- the first CHoCH forms per name, later than the ATR (the earliest name at own bar 15)")
    for s in ("park_vol_21", "gk_minus_cc"):
        add(s, ST.VOL_BARS - 1, "ragged_structure_scores.structure_scores", f"w = VOL_BARS {ST.VOL_BARS}; " + trail)
    add("gap_reversal", 1, "ragged_structure_scores.structure_scores", "consecutive own bars with |open / prev close - 1| > 50 bp: the first such gap per name")
    return W


def own_lagged(P, raw, s):
    """run_d350.lagged WITHOUT the shared base: floored, deal-filtered, lagged one bar -> (T, n). The score's own NaN pattern governs; the
    Impulse family (hist_L, md) keeps P['base'], which IS its builder's declared warm."""
    sc = UF.apply_floor_replace(np.where(P["excl"], np.nan, raw), P["keep"])
    if s in IMPULSE:
        sc = np.where(P["base"], sc, np.nan)
    out = np.full((P["T"], P["n"]), np.nan)
    out[1:] = sc[:, :-1].T
    return out


def own_subset_check(pct, pcto, s):
    """[OWN-SUB]: wherever pct_<s> is finite pcto_<s> is finite. Returns (n_pct, n_pcto, n_both, mean |diff| on both, share of both with |diff| > 5)."""
    fp, fo = np.isfinite(pct), np.isfinite(pcto)
    bad = int((fp & ~fo).sum())
    assert bad == 0, f"[OWN-SUB] pcto_{s} is NaN on {bad} rows where pct_{s} is finite"
    both = fp & fo
    d = np.abs(pct[both] - pcto[both])
    return int(fp.sum()), int(fo.sum()), int(both.sum()), (float(d.mean()) if both.any() else 0.0), (float((d > 5.0).mean()) if both.any() else 0.0)


def assert_same_as_committed(C, old_cols, N):
    """[SAME]: every pre-existing column, formatted as the writer formats it, equals the committed file cell for cell (git show HEAD:...csv.gz);
    the header of the committed file is exactly old_cols. The new columns are appended after them, so the written file is the committed one
    with columns added at the end of every line."""
    rel = f"data/{STEM}.csv.gz"
    out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(REPO), capture_output=True)
    assert out.returncode == 0, f"[SAME] git show HEAD:{rel} failed: {out.stderr.decode(errors='replace')[:300]}"
    rows = list(csv.reader(io.StringIO(gzip.decompress(out.stdout).decode("utf-8"))))
    head, body = rows[0], rows[1:]
    assert head == old_cols, f"[SAME] the committed header differs from the pre-existing columns: {[c for c in head if c not in old_cols]} / {[c for c in old_cols if c not in head]}"
    assert len(body) == N, f"[SAME] committed rows {len(body)} != {N}"
    n_cells = 0
    for j, c in enumerate(old_cols):
        mine = [fmt(x) for x in C[c]]
        theirs = [r[j] for r in body]
        if mine != theirs:
            k = next(i for i in range(N) if mine[i] != theirs[i])
            raise AssertionError(f"[SAME] column {c} differs from the committed file at row {k}: {mine[k]!r} vs {theirs[k]!r}")
        n_cells += N
    return len(old_cols), n_cells, len(out.stdout)


def build(P, out_dir, t0):
    T, n = P["T"], P["n"]
    finT, r1T, ocT = np.asarray(P["finT"]), np.asarray(P["r1T"]), np.asarray(P["ocT"])
    m_f, m_f_oc = np.asarray(P["m_f"], float), np.asarray(P["m_f_oc"], float)
    CLOSE, RAW_CLOSE, RAW, VOL, DV = P["CLOSE"], P["RAW_CLOSE"], P["RAW"], P["VOL"], P["DV"]
    HALF, elig, excl, last_live = P["HALF"], np.asarray(P["elig"]), np.asarray(P["excl"]), np.asarray(P["last_live"])
    dates, symbols, years = P["dates"], P["symbols"], np.asarray(P["years"])
    rep = json.loads(REPORT.read_text())
    cell = rep["results"]["G2:T2"]
    stored = dict(events_gated=cell["events"]["gated"], events_ung=cell["events"]["ungated"], events_G1=rep["G"]["cells"]["G1:T2"]["gated"],
                  raw=rep["G"]["T2"]["counts"]["raw"], excluded=rep["G"]["T2"]["counts"]["excluded"],
                  g2=cell["gated"]["cap10"]["per_trade"], g2_acc=cell["gated"]["cap10"]["accounting"],
                  ung=rep["ungated"]["T2"]["cap10"]["per_trade"], ung_acc=rep["ungated"]["T2"]["cap10"]["accounting"],
                  g1=rep["results"]["G1:T2"]["gated"]["cap10"]["per_trade"], g1_acc=rep["results"]["G1:T2"]["gated"]["cap10"]["accounting"])

    # ---- the raw T2 candidates on day g (D360's grids; memoised, released by V61.triggers below)
    G = V60.signal_grids(P)
    with np.errstate(invalid="ignore"):
        day = (G["pct_gap"] >= 100.0 - P_GAP) & (G["pct_rv"] >= 100.0 - Q_RV)
    raw = day & G["cs"]
    gs, rows = np.nonzero(raw)                                    # row-major: sorted by (g, row)
    N = gs.size
    es = gs + 1
    assert es.max() < T
    idx = {(int(r), int(e)): j for j, (r, e) in enumerate(zip(rows, es))}
    assert len(idx) == N, "[N] a (row, bar_entry) repeated"
    C = {}                                                        # the columns, in dictionary order
    xd, v0, nf = G["XD"][gs, rows], G["V0"][gs, rows], G["NF"][gs, rows]
    bad = G["bad"][gs, rows]
    excluded_reason = np.array(["+".join(k for k, f in (("xd", a), ("v0", b), ("nf", c)) if f) for a, b, c in zip(xd, v0, nf)], dtype=object)
    assert np.array_equal(bad, excluded_reason != ""), "[XD] the exclusion flags disagree with bad"
    gap, rv, pct_gap, pct_rv = (G[k][gs, rows].astype(float) for k in ("gap", "rv", "pct_gap", "pct_rv"))
    OPEN_g, OPEN_e = G["OPEN"][gs, rows].astype(float), G["OPEN"][es, rows].astype(float)
    CLOSE_gm1 = np.asarray(CLOSE)[gs - 1, rows].astype(float)
    kernel_score = G["sc"][es, rows].astype(float)
    sh2, c2 = V60.mirror_signal(P, P_GAP, Q_RV)
    assert c2["raw"] == N == stored["raw"] and c2["excluded"] == int(bad.sum()) == stored["excluded"] and c2["events"] == N - int(bad.sum()) == stored["events_ung"], \
        f"[N] raw {N} excluded {int(bad.sum())} vs mirror_signal {c2} / stored {stored}"
    assert np.array_equal(sh2[es, rows], ~bad) and int(sh2.sum()) == N - int(bad.sum()), "[N] the mirror event grid is not the raw candidates less the excluded"
    del G, day, raw
    S = V61.triggers(P)                                           # asserts [XD] [V0] against D360's grids, releases D360's memo (~1 GB)
    sig_u, sc, elig_t, cnt = S["T2"]
    assert np.array_equal(sig_u, sh2) and np.array_equal(elig_t, elig), "[N] triggers' T2 != the mirror grid"
    del sh2
    print(f"    [N] {N:,} rows = {N - int(bad.sum()):,} T2 events + {int(bad.sum())} excluded (D360's [XD]/[V0]/[NF] on day g; stored raw {stored['raw']:,}, "
          f"excluded {stored['excluded']}, events {stored['events_ung']:,}); sorted by (bar_g, row) ({el(t0)})")

    # ---- identity
    C["symbol"] = [symbols[r] for r in rows]
    C["row"] = rows
    C["bar_g"] = gs
    C["date_g"] = [dates[g] for g in gs]
    C["bar_entry"] = es
    C["date_entry"] = [dates[e] for e in es]
    C["year"] = years[es]
    C["era"] = np.where(es < T // 2, 1, 2)
    C["down_year"] = np.isin(years[es], list(P["down_years"])).astype(int)
    C["weekday_entry"] = np.array([dt.date.fromisoformat(dates[e]).weekday() for e in es])
    C["excluded_reason"] = excluded_reason

    # ---- the gates at bar_entry
    gp = {g: V61.gate_pack(P, g) for g in ("G1", "G2")}
    worst_gt = {g: V61.assert_GT(P, gp[g]) for g in gp}
    ep = {}
    for g in gp:
        eid, elen = np.full(T, -1), np.zeros(T, int)
        for i, (s, e) in enumerate(gp[g]["episodes"]):
            eid[s:e + 1], elen[s:e + 1] = i, e - s + 1
        ep[g] = (eid, elen)
    C["G1_on"] = gp["G1"]["gate"][es].astype(int)
    C["G1_defined"] = gp["G1"]["defined"][es].astype(int)
    C["level_63"] = gp["G1"]["level"][es]
    C["episode_id_G1"] = ep["G1"][0][es]
    C["episode_len_G1"] = ep["G1"][1][es]
    C["G2_on"] = gp["G2"]["gate"][es].astype(int)
    C["G2_defined"] = gp["G2"]["defined"][es].astype(int)
    C["level_200"] = gp["G2"]["level"][es]
    C["episode_id_G2"] = ep["G2"][0][es]
    C["episode_len_G2"] = ep["G2"][1][es]
    m0 = P["m_start"]
    mr, mv = np.full(N, np.nan), np.full(N, np.nan)
    for i, e in enumerate(es):
        if e - 20 >= m0:
            w = m_f[e - 20:e]
            mr[i] = float(np.prod(1.0 + w) - 1.0)
            mv[i] = float(np.std(w, ddof=1)) * 1e4
    C["mkt_ret_20"], C["mkt_vol_20"] = mr, mv
    # [GATE]: the runner's gate at bar_entry equals the plain-loop gate (gate_loop, no numpy window) on every row; counts == stored
    ok = ~bad
    for g, key in (("G1", "events_G1"), ("G2", "events_gated")):
        _lv, gl = V61.gate_loop(P, g)
        assert np.array_equal(gl[es], C[f"{g}_on"].astype(bool)), f"[GATE] {g}_on != gate_loop at bar_entry"
        assert int(C[f"{g}_on"][ok].sum()) == stored[key], f"[GATE] {g}_on rows {int(C[f'{g}_on'][ok].sum())} != stored gated events {stored[key]}"
    print(f"    [GATE] G1_on / G2_on at bar_entry equal the vectorised gate (loop to {worst_gt['G1']:.0e} / {worst_gt['G2']:.0e} on the level, exactly on the "
          f"boolean) and gate_loop on every row; G2_on on {int(C['G2_on'][ok].sum()):,} of the {int(ok.sum()):,} events == stored gated {stored['events_gated']:,}; "
          f"G1_on {int(C['G1_on'][ok].sum()):,} == {stored['events_G1']:,}; on the excluded rows G2_on {int(C['G2_on'][bad].sum())}, G1_on {int(C['G1_on'][bad].sum())} ({el(t0)})")

    # ---- the trigger on day g
    C["gap"], C["pct_gap"], C["rv"], C["pct_rv"] = gap, pct_gap, rv, pct_rv
    C["kernel_score"] = kernel_score
    C["ret_g_cc"] = r1T[gs, rows].astype(float)
    C["ret_g_oc"] = ocT[gs, rows].astype(float)
    C["vol_g"] = np.asarray(VOL)[gs, rows].astype(float)
    C["dollar_vol_g"] = np.asarray(CLOSE)[gs, rows].astype(float) * C["vol_g"]
    # the fixture's own bars for g-1, g, g+1: high/low for the range, open/close as the independent read behind [FIX]
    want = set()
    for g, r in zip(gs, rows):
        s = symbols[r]
        want.update(((s, dates[g - 1]), (s, dates[g]), (s, dates[g + 1])))
    bars = stream_bars(want)
    hi = np.array([bars[(symbols[r], dates[g])][1] for g, r in zip(gs, rows)])
    lo = np.array([bars[(symbols[r], dates[g])][2] for g, r in zip(gs, rows)])
    op = np.array([bars[(symbols[r], dates[g])][0] for g, r in zip(gs, rows)])
    cl = np.array([bars[(symbols[r], dates[g])][3] for g, r in zip(gs, rows)])
    vo = np.array([bars[(symbols[r], dates[g])][4] for g, r in zip(gs, rows)])
    # `_b=bars` BINDS THE DICT AT DEFINITION rather than closing over the name, which is
    # `del`eted at the end of this block. Behaviour is identical today -- both calls are two
    # lines below and the object is the same -- but a call added after the `del` would have
    # raised `NameError: cannot access free variable 'bars'` rather than working (D543).
    at_bar = lambda g, r, j, _b=bars: _b[(symbols[r], dates[g])][j] if (symbols[r], dates[g]) in _b else np.nan
    cl_prev = np.array([at_bar(g - 1, r, 3) for g, r in zip(gs, rows)])
    op_e = np.array([at_bar(g + 1, r, 0) for g, r in zip(gs, rows)])
    assert np.array_equal(op, OPEN_g) and np.array_equal(cl, np.asarray(CLOSE)[gs, rows]) and np.array_equal(vo, C["vol_g"]), "[FIX] the fixture's open/close/volume on day g != the grids"
    assert np.array_equal(cl_prev, CLOSE_gm1, equal_nan=True) and np.array_equal(op_e, OPEN_e, equal_nan=True), "[FIX] the fixture's close(g-1) / open(g+1) != the grids"
    with np.errstate(invalid="ignore", divide="ignore"):
        C["range_g"] = (hi - lo) / op
        C["close_loc_g"] = np.where(hi > lo, (cl - lo) / (hi - lo), np.nan)
    n_bad_hl = int(((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl))).sum())
    print(f"    [FIX] {len(bars):,} raw bars streamed from {FIXTURE.name} for days g-1, g, g+1 of every row: open/close/volume on g, close on g-1 and open on g+1 "
          f"equal the prep's CLOSE / VOL and D360's OPEN grid bit-identically on all {N:,} rows; high/low read for range_g ({n_bad_hl} bars with high < max(o, c) "
          f"or low > min(o, c), kept as read) ({el(t0)})")
    del bars, want

    # ---- the name's state at bar_entry (t-1 information)
    C["price_close_g"] = np.asarray(RAW_CLOSE)[gs, rows].astype(float)
    C["price_adj_close_g"] = np.asarray(CLOSE)[gs, rows].astype(float)
    C["price_open_entry"] = OPEN_e * np.asarray(RAW)[es, rows]
    C["price_adj_open_entry"] = OPEN_e
    C["dv_63_lagged"] = np.asarray(DV)[es, rows].astype(float)
    dvp = np.full(N, np.nan)
    for e in np.unique(es):
        m = es == e
        dv = np.asarray(DV[e], float)
        okd = elig[e] & np.isfinite(dv)
        if okd.any():
            for i in np.flatnonzero(m):
                x = dv[rows[i]]
                dvp[i] = float((dv[okd] < x).mean() * 100.0) if np.isfinite(x) else np.nan
    C["dv_pct"] = dvp
    C["half_spread_PUB_bp"] = np.asarray(HALF["PUB"])[es, rows].astype(float)
    C["half_spread_PB_bp"] = np.asarray(HALF["PB"])[es, rows].astype(float)
    C["f0_window_at_entry"] = excl[rows, es - 1].astype(int)
    C["rsi_bucket"] = np.where(P["rsi_pct_ok"][es, rows], np.asarray(P["bucket_rsi"])[es, rows], -1).astype(int)
    C["elig_entry"] = elig[es, rows].astype(int)
    # every score in the cache: the lagged floored cross-sectional percentile at bar_entry (run_d358.pct_of), [LAG]-checked by pct_direct
    scores = [k for k in P["z"].files if k not in NON_SCORES]
    rng = np.random.default_rng([SEED, STUDY, 99])
    samp = rng.choice(np.flatnonzero(ok), size=300, replace=False)
    worst_lag = 0
    # the scores' OWN warm-up (pcto_): the builders' declarations, and the cache's first finite own bar per name to check them against
    WD = own_warm_declared()
    assert set(WD) == set(scores), f"[WARM] declared {sorted(set(WD) ^ set(scores))}"
    live = np.asarray(P["live"])                                  # (n, T)
    base = np.asarray(P["base"])                                  # (n, T): the cache's warm & live
    keep = np.asarray(P["keep"])                                  # (T, n)
    own_idx = np.cumsum(live, axis=1) - 1                         # own-bar index at every column (valid where live)
    nbars = live.sum(axis=1)
    samp_names = np.random.default_rng([SEED, STUDY, 98]).choice(np.flatnonzero(nbars >= 1100), size=20, replace=False)
    assert (own_idx[base].min() if base.any() else -1) == WD["hist_L"]["warm_bars"] and not (base & ~live).any(), "[WARM] P['base'] is not own bar >= need"
    C2 = {}                                                       # the pcto_ columns, appended after everything else
    OW = {}                                                       # the per-score table for the dictionary
    for s in scores:
        pct = V58.pct_of(P, s)
        col = pct[es, rows].astype(float)
        L = V50.lagged(P, s)
        for i in samp:
            d, _k = V58.pct_direct(L[es[i]], int(rows[i]))
            same = (math.isnan(d) and math.isnan(col[i])) or d == col[i]
            assert same, f"[LAG] pct_{s} at row {i} ({symbols[rows[i]]} {dates[es[i]]}): column {col[i]} != pct_direct {d}"
        C[f"pct_{s}"] = col
        V58._PCT.pop(s, None)
        del pct, L
        # ---- [WARM]: the raw cache grid's first finite OWN bar per name against the builder's declared warm-up
        raw = np.asarray(P["score"](s), float)                    # (n, T), the cache member as written
        fin = np.isfinite(raw)
        assert not (fin & ~live).any(), f"[WARM] {s} finite off a live bar"
        has = fin.any(axis=1)
        fo = np.where(has, own_idx[np.arange(n), np.argmax(fin, axis=1)], -1)
        decl = WD[s]["warm_bars"]
        early = int((fo[has] < decl).sum())
        if s in IMPULSE:                                          # the primitive's seed precedes the family's declared burn-in: masked at need
            assert early == int(has.sum()) and fo[has].min() < decl, f"[WARM] {s}: expected every name's seed before need {decl}, got min {fo[has].min()}"
            masked_at = decl
        else:
            assert early == 0, f"[WARM] {s}: {early} names carry a value before the declared warm-up {decl} own bars (min {fo[has].min()})"
            masked_at = None
        sample20 = [int(x) for x in fo[samp_names]]
        # ---- pcto_: the same percentile without P['base']
        own = own_lagged(P, raw, s)
        pcto = V47.percentile_grid(own)
        colo = pcto[es, rows].astype(float)
        del own, pcto
        # [OWN-LAG]: a direct recomputation on the sampled rows -- the column at es-1 built from the raw member, the exclusions, the floor (and
        # for the Impulse family the shared base), then pct_direct's counting; never own_lagged
        for i in samp:
            e, r = int(es[i]), int(rows[i])
            colr = raw[:, e - 1].copy()
            colr[excl[:, e - 1]] = np.nan
            colr[~keep[e - 1]] = np.nan
            if s in IMPULSE:
                colr[~base[:, e - 1]] = np.nan
            d, _k = V58.pct_direct(colr, r)
            same = (math.isnan(d) and math.isnan(colo[i])) or d == colo[i]
            assert same, f"[OWN-LAG] pcto_{s} at row {i} ({symbols[r]} {dates[e]}): column {colo[i]} != direct {d}"
        if s in IMPULSE:
            assert np.array_equal(col, colo, equal_nan=True), f"[OWN-SUB] pcto_{s} != pct_{s} although the family's own warm is the shared one"
        n_p, n_o, n_b, mad, gt5 = own_subset_check(col, colo, s)
        C2[f"pcto_{s}"] = colo
        OW[s] = dict(axis=WD[s]["axis"], module=WD[s]["module"], warm_bars_declared=decl, rule=WD[s]["rule"],
                     first_finite_own_bar=dict(min_over_names=int(fo[has].min()), names_with_a_value=int(has.sum()), sample20=sample20,
                                               sample20_all_equal_declared=bool(all(x == decl for x in sample20))),
                     masked_at_own_bar=masked_at, rows_pct=n_p, rows_pcto=n_o, cov_pct=n_p / N, cov_pcto=n_o / N, rows_both=n_b,
                     mean_abs_diff_both=mad, share_both_diff_gt_5=gt5)
        del raw, fin
    n_eq = sum(1 for s in scores if OW[s]["first_finite_own_bar"]["min_over_names"] == OW[s]["warm_bars_declared"])
    later = [s for s in scores if s not in IMPULSE and OW[s]["first_finite_own_bar"]["min_over_names"] > OW[s]["warm_bars_declared"]]
    s20 = sum(1 for s in scores if OW[s]["first_finite_own_bar"]["sample20_all_equal_declared"])
    print(f"    [WARM] per score, the cache's first finite OWN bar per name (own_idx = cumsum(live) - 1, so a hole does not count) vs the builder's declared "
          f"warm-up (own_warm_declared, from the family modules' constants): NO name carries a value before its declared warm-up on any of the {len(scores) - len(IMPULSE)} "
          f"non-Impulse scores; the minimum over names EQUALS the declared value on {n_eq} of {len(scores)} scores and is later on {later} (the builder's own "
          f"value rule, not a warm-up); on 20 sampled names (>= 1,100 bars) every name's first finite bar equals the declared value on {s20} scores. "
          f"{'/'.join(IMPULSE)}: the raw grid seeds at own bar {OW['hist_L']['first_finite_own_bar']['min_over_names']} / {OW['md']['first_finite_own_bar']['min_over_names']} "
          f"(the zlema / SMA seed of an IIR the family declares burned in at {WD['hist_L']['warm_bars']}): masked at {WD['hist_L']['warm_bars']} = P['base'], so pcto_ == pct_ ({el(t0)})")
    worst_mad = max(scores, key=lambda s: OW[s]["mean_abs_diff_both"])
    worst_gt5 = max(scores, key=lambda s: OW[s]["share_both_diff_gt_5"])
    tot_p, tot_o = sum(OW[s]["rows_pct"] for s in scores), sum(OW[s]["rows_pcto"] for s in scores)
    print(f"    [OWN-LAG] {len(scores)} pcto_<score> columns (the same percentile WITHOUT the shared base) equal a direct recomputation from the raw cache member at "
          f"bar_entry - 1 (exclusions, floor, pct_direct's counting; the Impulse family also the shared base) EXACTLY on the same 300 sampled rows for every score ({el(t0)})")
    print(f"    [OWN-SUB] wherever pct_<score> is finite pcto_<score> is finite, all {len(scores)} scores; pct_ finite on {tot_p:,} score-rows, pcto_ on {tot_o:,} "
          f"({tot_o / tot_p:.3f}x); where both are finite the mean |pcto - pct| is {np.mean([OW[s]['mean_abs_diff_both'] for s in scores]):.3f} points (worst {worst_mad} "
          f"{OW[worst_mad]['mean_abs_diff_both']:.3f}) and {np.mean([OW[s]['share_both_diff_gt_5'] for s in scores]):.2%} of rows differ by > 5 points (worst {worst_gt5} "
          f"{OW[worst_gt5]['share_both_diff_gt_5']:.2%}); {'/'.join(IMPULSE)} identical to pct_ ({el(t0)})")
    # gap / rv on the sampled rows against D360's direct forms (rv_direct: a per-name window loop; the gap: OPEN[g] / CLOSE[g-1] - 1 on the same grids)
    VOLa = np.asarray(VOL)
    for i in samp:
        g, r = int(gs[i]), int(rows[i])
        rd = V60.rv_direct(VOLa, g, r)
        assert rd == rv[i], f"[LAG] rv at row {i}: {rv[i]} != rv_direct {rd}"
        gd = OPEN_g[i] / CLOSE_gm1[i] - 1.0
        assert gd == gap[i], f"[LAG] gap at row {i}: {gap[i]} != direct {gd}"
    print(f"    [LAG] {len(scores)} pct_<score> columns (run_d358.pct_of at (bar_entry, row): the score floored, deal-filtered, warm-based, LAGGED one bar, "
          f"average-rank percentile among finite names, NaN under 50 names or where the name is undefined) equal pct_direct on a fresh V50.lagged column on 300 "
          f"sampled rows EXACTLY for every score; gap == OPEN[g]/CLOSE[g-1] - 1 and rv == rv_direct exactly on the same rows ({el(t0)})")

    # ---- the three runs through the kernel, and the kernel-free replay
    gated2, _off2, ung, sc2 = V61.arms_of(P, "G2", "T2")
    gated1 = V61.arms_of(P, "G1", "T2")[0]
    assert np.array_equal(ung, sig_u) and sc2 is sc
    arm = dict(ungated=~bad, G2=~bad & C["G2_on"].astype(bool), G1=~bad & C["G1_on"].astype(bool))
    sigs = dict(ungated=ung, G2=gated2, G1=gated1)
    for k in RUNS:
        assert int(sigs[k].sum()) == int(arm[k].sum()) and np.array_equal(sigs[k][es, rows], arm[k]), f"[N] the {k} arm's events != the rows' flags"
    holds = np.zeros(N, int)
    exit_reason = np.array([""] * N, dtype=object)
    in_ledger = np.zeros(N, bool)
    for i in range(N):
        holds[i], exit_reason[i], in_ledger[i] = hold_of(finT, T, last_live, int(es[i]), int(rows[i]))
    C["hold_cap10"] = holds
    C["exit_reason_cap10"] = exit_reason
    RES = {}
    pnl_of = {}
    for k in RUNS:
        res = V61.run_short(P, sigs[k], sc, "cap", CAP)
        RES[k] = res
        taken, reason = replay(es, rows, arm[k], holds, finT, n)
        reason[~arm[k] & bad] = "excluded"
        reason[~arm[k] & ~bad] = "gate_off"
        tr = res["trades"]
        assert all(t[4] == 1 for t in tr), f"[REPLAY] a long in the {k} ledger"
        led = {(t[0], t[1]): (t[2], t[3]) for t in tr}
        assert len(led) == len(tr), f"[REPLAY] {k}: a (row, e0) repeated in the ledger"
        mine = {(int(rows[i]), int(es[i])): int(holds[i]) for i in np.flatnonzero(taken & in_ledger)}
        assert set(mine) == set(led), f"[REPLAY] {k}: the replay's taken-and-closed set differs from the kernel's ledger on {len(set(mine) ^ set(led))} trades"
        assert all(led[key][0] == h for key, h in mine.items()), f"[REPLAY] {k}: a hold differs from the kernel's age"
        n_open_end = int((taken & ~in_ledger).sum())
        assert int(taken.sum()) == int(res["ent"].sum()) and n_open_end == int(res["held"][-1]), \
            f"[REPLAY] {k}: taken {int(taken.sum())} vs entries {int(res['ent'].sum())}; open at end {n_open_end} vs {int(res['held'][-1])}"
        pnl = np.full(N, np.nan)
        for i in np.flatnonzero(taken & in_ledger):
            key = (int(rows[i]), int(es[i]))
            pnl[i] = led[key][1] * 1e4
            if key in pnl_of:
                assert pnl_of[key] == pnl[i], f"[REPLAY] {key}: P&L differs between runs"
            pnl_of[key] = pnl[i]
        C[f"taken_{k}"] = taken.astype(int)
        C[f"skip_reason_{k}"] = reason
        C[f"pnl_cap10_bp_{k}"] = pnl
        C[f"n_open_at_entry_{k}"] = (res["held"][es] - res["ent"][es]).astype(int)
        C[f"n_entries_bar_{k}"] = res["ent"][es].astype(int)
        acc = {"ungated": stored["ung_acc"], "G2": stored["g2_acc"], "G1": stored["g1_acc"]}[k]
        assert int(taken.sum()) == acc["entries"] and len(tr) == acc["trades"] and n_open_end == acc["open_at_end"] and int((reason == "held").sum()) == acc["already_held"], \
            f"[LEDGER] {k}: entries {int(taken.sum())} trades {len(tr)} open {n_open_end} held {int((reason == 'held').sum())} vs stored {acc}"
        print(f"    [REPLAY] {k}: {int(arm[k].sum()):,} events -> {int(taken.sum()):,} entries (a kernel-free replay on the hold rule) == the kernel's {int(res['ent'].sum()):,}; "
              f"{int((reason == 'held').sum()):,} skipped on a name already held, {int((reason == 'unpriced').sum())} unpriced; {len(tr):,} closed trades match the ledger "
              f"(row, e0, age) for (row, e0, age); {n_open_end} open at the end == held[-1]; stored accounting {acc} ({el(t0)})")
    # [LEDGER] against the stored file
    for k, st, want_n, want_m in (("G2", stored["g2"], 3977, None), ("ungated", stored["ung"], 20621, 14.7555), ("G1", stored["g1"], None, None)):
        pnl = C[f"pnl_cap10_bp_{k}"]
        m = np.isfinite(pnl)
        mean = float(pnl[m].mean())
        assert int(m.sum()) == st["trades"] and (want_n is None or want_n == st["trades"]), f"[LEDGER] {k}: {int(m.sum())} vs stored {st['trades']}"
        assert abs(mean - st["mean_bp"]) < 1e-9, f"[LEDGER] {k}: mean {mean:.12f} != stored {st['mean_bp']:.12f}"
        assert abs(float(np.median(pnl[m])) - st["median_bp"]) < 1e-9, f"[LEDGER] {k}: median"
        assert want_m is None or abs(mean - want_m) < 5e-5
        kern = float(V47.pnl_bp(RES[k]).mean())
        assert abs(kern - mean) < 1e-9
        print(f"    [LEDGER] {k}: {int(m.sum()):,} rows with pnl_cap10_bp_{k}, mean {mean:+.10f} bp == stored {st['mean_bp']:+.10f} (median {float(np.median(pnl[m])):+.6f} == "
              f"stored {st['median_bp']:+.6f}) to 1e-9, and == the re-run kernel's ledger trade for trade")
    C["pnl_cap10_bp"] = np.array([pnl_of.get((int(r), int(e)), np.nan) for r, e in zip(rows, es)])
    taken_any = (C["taken_ungated"] | C["taken_G2"] | C["taken_G1"]).astype(bool)

    # ---- borrow (D337's gc_htb through V49.borrow_of): actual hold where taken in any run, the rule at 10 bars otherwise
    age_b = np.where(taken_any, holds, CAP)
    tuples = [(int(r), int(e), int(a), 0.0, 1) for r, e, a in zip(rows, es, age_b)]
    pt, htb, rate = V49.borrow_of(P, tuples)
    C["htb"] = htb.astype(int)
    C["borrow_rate_bp_annual"] = rate
    C["borrow_bp_cap10"] = pt
    for k in ("G2", "ungated"):
        tr = RES[k]["trades"]
        pt_k, htb_k, _ = V49.borrow_of(P, tr)
        worst = max(abs(pt[idx[(t[0], t[1])]] - pt_k[j]) for j, t in enumerate(tr))
        assert worst == 0.0 and all(htb[idx[(t[0], t[1])]] == htb_k[j] for j, t in enumerate(tr)), f"[SB] {k}: borrow / HTB differ from borrow_of on the ledger ({worst:.2e})"
    print(f"    [SB] borrow_bp_cap10 == V49.borrow_of on the G2 and ungated ledgers exactly (rate x hold / 252; HTB = F0 window at e0-1 or as-traded close < ${BR.PX_HTB:.0f}); "
          f"HTB on {int(htb.sum()):,} of {N:,} rows; never-taken rows priced at {CAP} bars ({el(t0)})")

    # ---- the forward path from the entry open, k = 1..20
    H, U, M = (np.full((N, HORIZON), np.nan) for _ in range(3))
    n_path = np.zeros(N, int)
    for i in range(N):
        e, r = int(es[i]), int(rows[i])
        k = 0
        while k < HORIZON and e + k < T and finT[e + k, r]:
            if k == 0:
                v, mm = float(ocT[e, r]), float(m_f_oc[e])
            else:
                v, mm = float(r1T[e + k, r]), float(m_f[e + k])
            U[i, k], M[i, k], H[i, k] = v, mm, v - mm
            k += 1
        n_path[i] = k
    negH = -H                                                     # the short's sign, per bar
    with np.errstate(invalid="ignore"):
        cum = np.nancumsum(negH, axis=1)                          # sequential adds in k, as the kernel's st[1] += -(v - m)
    cum[~np.isfinite(negH).cumprod(axis=1).astype(bool)] = np.nan
    for k in range(HORIZON):
        C[f"h_{k + 1}"] = H[:, k] * 1e4
    for k in range(HORIZON):
        C[f"u_{k + 1}"] = U[:, k] * 1e4
    for k in range(HORIZON):
        C[f"m_{k + 1}"] = M[:, k] * 1e4
    C["n_path"] = n_path
    at = lambda i, k: cum[i, k - 1] * 1e4 if k >= 1 else np.nan
    C["pnl_path10_bp"] = np.array([at(i, min(CAP, n_path[i])) for i in range(N)])
    C["pnl_path20_bp"] = np.array([at(i, min(HORIZON, n_path[i])) for i in range(N)])
    C["mfe10_bp"] = np.array([np.nanmax(cum[i, :min(CAP, n_path[i])]) * 1e4 if n_path[i] else np.nan for i in range(N)])
    C["mae10_bp"] = np.array([np.nanmin(cum[i, :min(CAP, n_path[i])]) * 1e4 if n_path[i] else np.nan for i in range(N)])
    # [PATH]: for every closed trade in every run, the path summed over its actual hold equals the kernel's P&L
    worst_p, n_p = 0.0, 0
    for k in RUNS:
        for r, e0, age, pnl, _s in RES[k]["trades"]:
            i = idx[(r, e0)]
            assert n_path[i] >= age, f"[PATH] {k}: the path is shorter than the hold on row {i}"
            d = abs(at(i, age) - pnl * 1e4)
            worst_p = max(worst_p, d)
            n_p += 1
            assert d < 1e-9, f"[PATH] {k} row {i} ({symbols[r]} {dates[e0]}): path {at(i, age):.12f} != kernel {pnl * 1e4:.12f}"
    assert all(n_path[i] >= holds[i] for i in range(N))
    print(f"    [PATH] on all {n_p:,} closed trades of the three runs, -(h_1 + .. + h_hold) equals the kernel's P&L to {worst_p:.1e} (the same per-bar terms in the same "
          f"order: the entry bar on ocT - m_f_oc, later bars on r1T - m_f); positive = the short made money; n_path >= hold_cap10 on every row ({el(t0)})")

    # ---- hindsight
    meta = json.loads(META.read_text())["symbols"]
    C["status_meta"] = [meta[symbols[r]]["status"] for r in rows]
    C["delist_date"] = [meta[symbols[r]]["delistingDate"] or "" for r in rows]
    C["last_live_date"] = [dates[last_live[r]] for r in rows]
    C["bars_to_last_live"] = last_live[rows] - es

    # ---- [XD] [N]
    for k in RUNS:
        assert not C[f"taken_{k}"][bad].any() and (C[f"skip_reason_{k}"][bad] == "excluded").all(), f"[XD] an excluded row taken / unlabelled in {k}"
    assert int(bad.sum()) == stored["excluded"] == 14 and (excluded_reason[bad] == "xd").all()
    assert N == stored["raw"] == 24_750 and N - int(bad.sum()) == 24_736
    print(f"    [XD] the {int(bad.sum())} excluded rows all carry excluded_reason 'xd' (an ex-distribution of >= 1% of the prior close on day g), are in no arm and "
          f"taken in no run; every other row has excluded_reason ''")
    print(f"    [N] {N:,} rows: {N - int(bad.sum()):,} events + {int(bad.sum())} excluded; taken ungated {int(C['taken_ungated'].sum()):,}, G2 {int(C['taken_G2'].sum()):,}, "
          f"G1 {int(C['taken_G1'].sum()):,}; taken in any run {int(taken_any.sum()):,}")

    # ---- [6]: the checks raise on a broken artefact
    broke = []
    try:
        j = int(np.flatnonzero(np.isfinite(C["pnl_cap10_bp_G2"]))[0])
        tr0 = RES["G2"]["trades"]
        r0, e0, a0, p0, s0 = tr0[0]
        assert abs(at(idx[(r0, e0)], a0) - (p0 + 1e-8) * 1e4) < 1e-9, "[PATH] perturbed"
    except AssertionError as ex:
        assert "[PATH]" in str(ex)
        broke.append("PATH")
    try:
        g2 = C["G2_on"].copy()
        g2[int(np.flatnonzero(ok)[0])] ^= 1
        assert int(g2[ok].sum()) == stored["events_gated"], "[GATE] perturbed"
    except AssertionError as ex:
        assert "[GATE]" in str(ex)
        broke.append("GATE")
    try:
        _t, _r = replay(es, rows, arm["G2"], np.where(holds > 0, 1, 0), finT, n)     # a one-bar hold frees every name at once: no 'held' skip survives
        assert int(_t.sum()) == int(RES["G2"]["ent"].sum()), "[REPLAY] perturbed"
    except AssertionError as ex:
        assert "[REPLAY]" in str(ex)
        broke.append("REPLAY")
    try:
        po = C2["pcto_rsi"].copy()
        po[int(np.flatnonzero(np.isfinite(C["pct_rsi"]))[0])] = np.nan                  # one own-percentile removed where the shared one exists
        own_subset_check(C["pct_rsi"], po, "rsi")
    except AssertionError as ex:
        assert "[OWN-SUB]" in str(ex)
        broke.append("OWN-SUB")
    assert broke == ["PATH", "GATE", "REPLAY", "OWN-SUB"], broke
    print("    [6] [PATH] raises on a P&L moved by 1e-4 bp; [GATE] raises on one G2_on flag flipped; [REPLAY] raises on a one-bar hold rule (every 'held' skip vanishes); "
          "[OWN-SUB] raises on one pcto_rsi value blanked where pct_rsi is finite")
    C.update(C2)                                                  # the pcto_ columns, after every pre-existing column
    return C, scores, dict(N=N, n_excluded=int(bad.sum()), taken={k: int(C[f"taken_{k}"].sum()) for k in RUNS}, worst_path=worst_p, n_path_checked=n_p,
                           stored=dict(g2_mean=stored["g2"]["mean_bp"], g2_trades=stored["g2"]["trades"], ung_mean=stored["ung"]["mean_bp"], ung_trades=stored["ung"]["trades"]),
                           own_warm=OW)


# ------------------------------------------------------------------ the dictionary
def dictionary(scores):
    """[(column, definition, measured_at, hindsight)] in the CSV's column order. measured_at: 'g' (the gap day; known at the close of g,
    before the entry at the open of g+1), 't-1' (information to the close of bar_entry - 1, the kernel's lag), 'entry' (bar_entry, a
    label), 'path' (forward from the entry open: an OUTCOME), 'hindsight' (the span end)."""
    D = []
    add = lambda c, d, at, h=False: D.append(dict(column=c, definition=d, measured_at=at, hindsight=bool(h)))
    add("symbol", "ticker (P['symbols'][row])", "entry")
    add("row", "the panel column index of the name", "entry")
    add("bar_g", "the gap day's bar index g", "g")
    add("date_g", "the gap day (YYYY-MM-DD)", "g")
    add("bar_entry", "the event / entry bar index t = g + 1; the fill is the OPEN of this bar (D340)", "entry")
    add("date_entry", "the entry bar's date", "entry")
    add("year", "calendar year of bar_entry", "entry")
    add("era", "1 if bar_entry < T // 2 else 2 (the runners' era split; T = 4187)", "entry")
    add("down_year", "1 if year in the floored market's down-years (2015, 2018, 2022)", "entry")
    add("weekday_entry", "weekday of date_entry, 0 = Monday .. 4 = Friday", "entry")
    add("excluded_reason", "'' for a T2 event; 'xd' / 'v0' / 'nf' (joined by +) for a raw candidate D360 excluded on day g: ex-distribution >= 1% of the prior close / "
        "zero volume / no prior close. Excluded rows are in no arm and no run", "g")
    add("G1_on", "1 if G1 is on at bar_entry: the floored market's trailing 63-bar COMPOUNDED return over bars t-63..t-1 < 0 (run_d361.gate_pack); 0 where off or undefined", "t-1")
    add("G1_defined", "1 if bar_entry >= m_start + 63 (the window fits)", "t-1")
    add("level_63", "prod(1 + m_f[t-63..t-1]) - 1, the G1 level; NaN where undefined", "t-1")
    add("episode_id_G1", "index (0-based, in time order) of the G1 on-episode containing bar_entry; -1 if off", "t-1")
    add("episode_len_G1", "bars in that episode (0 if off). NOTE the episode's END is hindsight; its start and id are not", "t-1", True)
    add("G2_on", "1 if G2 is on at bar_entry: index[t-1] < mean(index[t-200..t-1]) with index = cumprod(1 + m_f) from m_start; the cell's gate", "t-1")
    add("G2_defined", "1 if bar_entry >= m_start + 200", "t-1")
    add("level_200", "index[t-1] / mean(index[t-200..t-1]) - 1, the G2 level; NaN where undefined", "t-1")
    add("episode_id_G2", "index of the G2 on-episode containing bar_entry; -1 if off", "t-1")
    add("episode_len_G2", "bars in that G2 episode (0 if off); the episode's end is hindsight", "t-1", True)
    add("mkt_ret_20", "prod(1 + m_f[t-20..t-1]) - 1: the floored market's trailing 20-bar compounded return (fraction); NaN where the window precedes m_start", "t-1")
    add("mkt_vol_20", "sd (ddof = 1) of m_f over bars t-20..t-1, in bp", "t-1")
    add("gap", "OPEN[g] / CLOSE[g-1] - 1 (split-adjusted frame, the fixture's; run_d360.signal_grids)", "g")
    add("pct_gap", "average-rank percentile of gap among the day-g cross-section cs (eligible at g+1, finite gap and rv); the trigger needs >= 98", "g")
    add("rv", "VOL[g] / median(VOL[g-21..g-1]) (run_d360.relative_volume); NaN unless all 21 prior volumes are finite and the median > 0", "g")
    add("pct_rv", "percentile of rv on the same cross-section; the trigger needs >= 90", "g")
    add("kernel_score", "100 - pct_gap, the score the kernel orders entries by at bar_entry (highest first, ties by row descending)", "t-1")
    add("ret_g_cc", "r1T[g]: the name's close(g-1) -> close(g) simple TOTAL return (fraction)", "g")
    add("ret_g_oc", "ocT[g]: the name's open(g) -> close(g) return on the gap day (fraction): did the gap extend or fade intraday", "g")
    add("vol_g", "shares traded on day g (the fixture's volume)", "g")
    add("dollar_vol_g", "CLOSE[g] x VOL[g] (split-adjusted close x volume, DV's construction), dollars", "g")
    add("range_g", "(high - low) / open on day g, from the raw fixture's bars (streamed; open/close asserted equal to the grids)", "g")
    add("close_loc_g", "(close - low) / (high - low) on day g; NaN when high == low", "g")
    add("price_close_g", "the AS-TRADED close on day g (RAW_CLOSE = CLOSE x the split factor)", "g")
    add("price_adj_close_g", "CLOSE[g], split-adjusted", "g")
    add("price_open_entry", "the as-traded open of bar_entry (the fill price): OPEN[t] x RAW[t]", "entry")
    add("price_adj_open_entry", "OPEN[t], split-adjusted", "entry")
    add("dv_63_lagged", "P['DV'][t]: trailing 63-bar mean of CLOSE x VOL, lagged one bar (dollars)", "t-1")
    add("dv_pct", "share (x100) of eligible names at bar_entry with finite DV whose DV[t] is strictly below this name's -- the record's four_groups convention "
        "(P['DV'] at e0 among elig[e0]); DV is itself lagged", "t-1")
    add("half_spread_PUB_bp", "P['HALF']['PUB'][t, row]: the public-quote half-spread estimate at bar_entry (bp/side), what the ledger's 2c PUB uses", "t-1")
    add("half_spread_PB_bp", "P['HALF']['PB'][t, row]: the Corwin-Schultz half-spread (bp/side), the 2c PB input", "t-1")
    add("f0_window_at_entry", "1 if the name is inside a D331 deal-filing (F0) exclusion window at t-1 (P['excl'][row, t-1]); the HTB rule's first leg", "t-1")
    add("rsi_bucket", "P['bucket_rsi'][t, row]: bucket 0..9 of the lagged rsi percentile (edges 0,2,5,10,25,50,75,90,95,98,100); -1 where undefined", "t-1")
    add("elig_entry", "1 if the name is eligible at bar_entry (priced, floored, deal-filtered; always 1 here)", "t-1")
    for s in scores:
        add(f"pct_{s}", f"run_d358.pct_of(P, '{s}')[t, row]: the '{s}' score's floored, deal-filtered, warm-based value LAGGED one bar, as an average-rank "
            "percentile (0..100) among finite names at bar_entry; NaN if undefined or fewer than 50 names", "t-1")
    add("hold_cap10", "bars the kernel marks a position opened at bar_entry: cap 10, or fewer if an unpriced bar / the panel end comes first (the same in every "
        "run that takes the event; asserted against the kernel's age on every closed trade). The would-be hold on skipped rows", "path")
    add("exit_reason_cap10", "'cap' (held 10 bars), 'delist' (exit on the first unpriced bar, after the name's last live bar), 'hole' (an unpriced bar with "
        "later bars priced), 'open_at_end' (still open at the panel end: NOT in the ledger, pnl_cap10_bp NaN), 'unpriced' (bar_entry unpriced; never here)", "path")
    for k in RUNS:
        lab = {"ungated": "the UNGATED T2 run (every event)", "G2": "the G2-GATED run (the cell: events with G2_on)", "G1": "the G1-GATED run (events with G1_on)"}[k]
        add(f"taken_{k}", f"1 if the kernel opened a position on this event in {lab}, cap 10, no slot cap", "entry")
        add(f"skip_reason_{k}", f"why not taken in {lab}: 'held' (the name already carries a position in THAT run's book), 'unpriced', 'gate_off' (not in the arm), "
            "'excluded'; '' if taken", "entry")
        add(f"pnl_cap10_bp_{k}", f"the closed trade's hedged P&L in bp in {lab}: -sum over the held bars of (v - m), positive = the short made money; "
            "NaN if not taken or open at the end", "path")
        add(f"n_open_at_entry_{k}", f"positions in {lab}'s book carried into bar_entry after that bar's exits, before its entries (held[t] - ent[t])", "entry")
        add(f"n_entries_bar_{k}", f"entries the kernel made on bar_entry in {lab} (this one included if taken)", "entry")
    add("pnl_cap10_bp", "the kernel's P&L (bp) where the event was taken and closed in ANY run (identical across runs); NaN otherwise", "path")
    add("htb", "1 if hard-to-borrow under D337's rule: an F0 window at t-1 or an as-traded close < $5 at bar_entry", "t-1")
    add("borrow_rate_bp_annual", "50 bp (GC) or 500 bp (HTB), the gc_htb scheme", "t-1")
    add("borrow_bp_cap10", "borrow charged per trade, bp = rate x hold / 252, with hold = hold_cap10 where the event was taken in any run and 10 otherwise", "path")
    for k in range(1, HORIZON + 1):
        add(f"h_{k}", f"hedged per-bar return in bp on forward bar {k} from the entry open: k=1 is ocT[t] - m_f_oc[t] (open -> close of the entry bar against the "
            "floored market's open-to-close); k>=2 is r1T[t+k-1] - m_f[t+k-1]. The SHORT earns -h_k. NaN beyond the last consecutively priced bar or the panel end", "path")
    for k in range(1, HORIZON + 1):
        add(f"u_{k}", f"the name's own (unhedged) return on forward bar {k}, bp: ocT[t] for k=1, r1T[t+k-1] for k>=2", "path")
    for k in range(1, HORIZON + 1):
        add(f"m_{k}", f"the floored market's return on forward bar {k}, bp: m_f_oc[t] for k=1, m_f[t+k-1] for k>=2", "path")
    add("n_path", "priced forward bars available, 1..20: the count of consecutive bars from bar_entry with finT True (the kernel's truncation), capped at 20", "path")
    add("pnl_path10_bp", "-(h_1 + .. + h_K) with K = min(10, n_path): the short's cumulative hedged P&L over the cap-10 hold, bp (equals pnl_cap10_bp where closed)", "path")
    add("pnl_path20_bp", "the same over K = min(20, n_path)", "path")
    add("mfe10_bp", "max over k = 1..min(10, n_path) of the short's cumulative hedged P&L -(h_1 + .. + h_k), bp (the best close-to-close mark; 0 is NOT included)", "path")
    add("mae10_bp", "min over the same k of the cumulative short P&L, bp (the worst mark)", "path")
    add("status_meta", "the fixture meta's status: delisted / collapsed (final close >= 90% below its in-span peak) / survived", "hindsight", True)
    add("delist_date", "the meta's delistingDate ('' if none)", "hindsight", True)
    add("last_live_date", "the date of the name's last priced bar in the panel", "hindsight", True)
    add("bars_to_last_live", "last_live[row] - bar_entry: bars from the entry to the name's last priced bar", "hindsight", True)
    for s in scores:
        add(f"pcto_{s}", f"as pct_{s} but WITHOUT the programme's shared 1,000-bar base (P['base']): the '{s}' score floored, deal-filtered, LAGGED one bar, as an "
            "average-rank percentile among the names finite at bar_entry under the score's OWN warm-up (own_warm in the dictionary; " +
            ("identical to pct_ -- the Impulse family's own warm IS the shared one" if s in IMPULSE else
             "a larger cross-section, so the value differs from pct_ where both are finite") + "). NaN under 50 names or where the name is undefined. "
            "The record's studies use pct_; the two are not interchangeable for reproducing one", "t-1")
    return D


def write_outputs(C, D, out_dir, info, t0):
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [d["column"] for d in D]
    assert cols == list(C.keys()), f"dictionary / column order differ: {[c for c in cols if c not in C]} {[c for c in C if c not in cols]}"
    N = info["N"]
    for c in cols:
        assert len(C[c]) == N, f"{c}: {len(C[c])} != {N}"
    f_csv = out_dir / f"{STEM}.csv"
    with open(f_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        arrs = [C[c] for c in cols]
        for i in range(N):
            w.writerow([fmt(a[i]) for a in arrs])
    f_dict = out_dir / f"{STEM}.dict.json"
    f_dict.write_text(json.dumps(dict(
        file=f_csv.name, rows=N, n_columns=len(cols), study=STUDY, cell="G2:T2", kernel="d345_event_book.simulate_event via run_d359.run_short (cap 10, no slot cap, hedged by the floored market)",
        sign="pnl > 0: the SHORT made money. pnl = -sum over held bars of (v - m); the entry bar on ocT - m_f_oc, later bars on r1T - m_f",
        row="one raw T2 candidate (pct_gap >= 98 & pct_rv >= 90 on day g, eligible at g+1); 24,736 events + 14 excluded ([XD])",
        runs="ungated / G2 / G1: the same kernel on the whole trigger, on the G2-gated arm, on the G1-gated arm; skips differ because the books differ",
        measured_at=dict(g="the gap day, known at its close", **{"t-1": "information to the close of bar_entry - 1 (the kernel's lag)"},
                         entry="a label of bar_entry", path="an OUTCOME from the entry open", hindsight="the span end"),
        floats="written with Python repr (round-trip exact); '' is NaN; flags are 0/1",
        stored_reference=info["stored"], taken=info["taken"], path_check=dict(trades=info["n_path_checked"], worst_bp=info["worst_path"]),
        own_warm=dict(
            what="per score: the builder's own warm-up (warm_bars_declared = the first admissible OWN-BAR index, 0-based, counted in the name's live bars), "
                 "the module that wrote the cache grid, the rule, the cache's first finite own bar per name ([WARM]: min over names, a 20-name sample), where "
                 "pcto_ is masked (the Impulse family only, at the shared need), and the row coverage of pct_<score> vs pcto_<score> with the value gap where both "
                 "are finite. pct_ sits behind P['base'] = own bar >= 1,000 (signals_ragged's need) for every score; pcto_ does not",
            scores=info["own_warm"]),
        columns=D), indent=1))
    f_md = out_dir / f"{STEM}.README.md"
    f_md.write_text("\n".join([
        f"# {STEM}",
        "",
        f"One row per raw T2 candidate of D361's cell G2:T2 -- D360's gap-up fade (a gap in the top 2% of day g on top-decile relative volume, eligible at g+1) entered SHORT at the open of g+1: {N:,} rows = 24,736 events + 14 excluded on an ex-distribution day (`excluded_reason`, in no run). Sorted by (bar_g, row). Built by `scripts/d361_export_trades.py` from the committed runners (run_d361 / run_d360 / run_d359 / d348_prep) and D345's kernel; every column is asserted ([N] [XD] [GATE] [LEDGER] [REPLAY] [PATH] [LAG] [WARM] [OWN-LAG] [OWN-SUB] [SB] [FIX] [SAME] [6]).",
        "",
        "**Sign.** Positive P&L means the short made money: `pnl_cap10_bp_*` = -(sum over the held bars of v - m), the entry bar on ocT - m_f_oc, later bars on r1T - m_f, in bp; `h_k` is the hedged per-bar return the short earns *minus* (-h_k), `u_k` the name's own, `m_k` the floored market's. `pnl_path10_bp` is the same sum over min(10, n_path) bars and equals the kernel's P&L on every closed trade to 1e-9.",
        "",
        "**Lagged vs hindsight.** `measured_at` in the dictionary: `g` = known at the close of the gap day (gap, rv, their percentiles, ret_g_*, range_g, prices on g); `t-1` = information to the close of bar_entry - 1 (both gates and their levels, mkt_ret_20 / mkt_vol_20, dv_pct, the half-spreads, f0_window, rsi_bucket, every `pct_<score>`, htb); `entry` = a label of the entry bar (dates, era, the taken flags and book counts); `path` = an OUTCOME from the entry open (h/u/m_k, n_path, pnl_*, mfe/mae, hold, exit_reason, borrow at the actual hold); `hindsight` = status_meta, delist_date, last_live_date, bars_to_last_live, and the episode LENGTHS (an episode's end is not known while it runs). The `hindsight` flag in the dictionary marks them.",
        "",
        "**Three runs, one kernel.** `taken_ungated` / `taken_G2` / `taken_G1` are the same cap-10 kernel on the whole trigger, on the G2-gated arm and on the G1-gated arm. The runs SKIP different events (`skip_reason_* = held`): an event is skipped when its name already carries a position in THAT run's book, and the books differ because the gate removes positions -- so a name free in the gated run can be held in the ungated one and vice versa. A trade's hold and P&L depend only on (row, bar_entry) and are identical across the runs that take it; `pnl_cap10_bp` collects it. `n_open_at_entry_*` is the book carried into the entry bar (after exits, before entries).",
        "",
        f"**Reference.** The G2-gated ledger: {info['stored']['g2_trades']:,} trades, mean {info['stored']['g2_mean']:+.4f} bp; the ungated: {info['stored']['ung_trades']:,}, {info['stored']['ung_mean']:+.4f} (data/d361_regime_gated_short.json, reproduced to 1e-9). Gross, hedged, before the 2c and borrow. Nothing here is a result; the 14 excluded rows and the never-taken rows are data, not trades.",
        "",
        f"**Two percentiles per score: `pct_` and `pcto_`.** `pct_<score>` is run_d358.pct_of, the percentile the record's studies use: the score behind the programme's SHARED base (P['base'] = the cache's `warm` & live, i.e. signals_ragged's need = max(impulse_warm_up_bars 1,000, warm_up_bars 393, U.WINDOW 252) of the name's OWN bars), so every score is NaN for a name's first 1,000 live bars whatever its own window -- {info['pct_nan_rows']:,} of the {N:,} rows ({info['pct_nan_rows'] / N:.1%}) carry no `pct_` at all (every row of 2010-2013). `pcto_<score>` is the same construction (floor, deal filter, one-bar lag, average-rank percentile among >= 50 finite names) WITHOUT that base: the score's own warm-up, as its builder wrote it, governs (`own_warm` in the dictionary gives each score's declared warm-up in own bars, the module, and the coverage before / after; [WARM] verified the cache's first finite bar against the declaration on every name). The cross-section is larger, so where both are finite the values DIFFER (mean gap {info['mad_mean']:.2f} points, {info['gt5_mean']:.1%} of rows by more than 5); `hist_L` / `md` are the one family whose builder used the shared warm, and their `pcto_` equals their `pct_`. The two are not interchangeable for reproducing a study: a study quoting pct_ ranks are reproduced from `pct_`, and a result on `pcto_` is a result on a different (earlier, larger) cross-section.",
        "",
        "Floats are Python repr (round-trip exact); empty = NaN; flags 0/1. Dictionary: `" + f_dict.name + "`.",
        "",
    ]))
    return f_csv, f_dict, f_md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    t0 = time.time()
    print("D361 EXPORT  every T2 event of G2:T2, one row each, with the gate, trigger, state, scores, borrow, three kernel runs, the forward path and the hindsight status")
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    print("\nASSERTIONS")
    C, scores, info = build(P, Path(a.out_dir), t0)
    D = dictionary(scores)
    cols = [d["column"] for d in D]
    old_cols = [c for c in cols if not c.startswith("pcto_")]
    assert cols[:len(old_cols)] == old_cols, "the pcto_ columns are not all at the end"
    n_old, n_cells, gz_bytes = assert_same_as_committed(C, old_cols, info["N"])
    print(f"    [SAME] all {n_old} pre-existing columns equal the committed file (git show HEAD:data/{STEM}.csv.gz, {gz_bytes / 2**20:.1f} MB) cell for cell on all "
          f"{info['N']:,} rows ({n_cells:,} cells, the writer's own formatting on both sides; the header identical); the {len(cols) - n_old} pcto_ columns are appended "
          f"after them ({el(t0)})")
    OW = info["own_warm"]
    pct_cols = np.array([C[f"pct_{s}"] for s in scores])
    info["pct_nan_rows"] = int((~np.isfinite(pct_cols)).all(axis=0).sum())
    info["mad_mean"] = float(np.mean([OW[s]["mean_abs_diff_both"] for s in scores]))
    info["gt5_mean"] = float(np.mean([OW[s]["share_both_diff_gt_5"] for s in scores]))
    del pct_cols
    f_csv, f_dict, f_md = write_outputs(C, D, Path(a.out_dir), info, t0)
    print(f"\nOK  every assertion passed; wrote {f_csv} ({f_csv.stat().st_size / 2**20:.1f} MB), {f_dict.name}, {f_md.name}  ({el(t0)})  {PREP.rss_line()}")
    print(f"\nROWS {info['N']:,}; taken " + ", ".join(f"{k} {v:,}" for k, v in info["taken"].items()) + f"; columns {len(D)} ({len(old_cols)} pre-existing + {len(cols) - len(old_cols)} pcto_)")
    print(f"\nOWN WARM-UP (per score: the builder's declared warm-up in OWN bars [the cache's first finite own bar: min over names / 20-name sample all equal], "
          f"module; rows with pct_ -> rows with pcto_ of {info['N']:,}; mean |pcto - pct| where both finite, share > 5 points)")
    print(f"  {'score':16s} {'ax':2s} {'decl':>5s} {'min':>5s} {'s20':>3s} {'mask':>5s}  {'pct rows':>9s} {'%':>6s}  {'pcto rows':>9s} {'%':>6s}  {'mad':>6s} {'>5':>6s}  module")
    for s in scores:
        o = OW[s]
        ff = o["first_finite_own_bar"]
        print(f"  {s:16s} {o['axis']:2s} {o['warm_bars_declared']:5d} {ff['min_over_names']:5d} {'yes' if ff['sample20_all_equal_declared'] else 'no':>3s} "
              f"{(str(o['masked_at_own_bar']) if o['masked_at_own_bar'] is not None else '-'):>5s}  {o['rows_pct']:9,d} {o['cov_pct']:6.1%}  {o['rows_pcto']:9,d} {o['cov_pcto']:6.1%}  "
              f"{o['mean_abs_diff_both']:6.2f} {o['share_both_diff_gt_5']:6.1%}  {o['module']}")
    print(f"  rows with NO pct_ on any score: {info['pct_nan_rows']:,} ({info['pct_nan_rows'] / info['N']:.1%}); rows with no pcto_ on any score: "
          f"{int((~np.isfinite(np.array([C[f'pcto_{s}'] for s in scores]))).all(axis=0).sum()):,}")
    print("\nCOVERAGE BY YEAR (rows with a finite value / rows in the year)")
    yrs = np.asarray(C["year"])
    show_c = ["pct_rsi", "pcto_rsi", "pct_rev_5", "pcto_rev_5", "pct_mom_252_21", "pcto_mom_252_21", "pct_hist_L", "pcto_hist_L"]
    print("  year   rows  " + "  ".join(f"{c:>15s}" for c in show_c))
    for y in np.unique(yrs):
        m = yrs == y
        print(f"  {y}  {int(m.sum()):5d}  " + "  ".join(f"{int(np.isfinite(C[c][m]).sum()):6d} {np.isfinite(C[c][m]).mean():7.1%}" for c in show_c))
    print("\nDICTIONARY (column: definition [measured_at, hindsight?])")
    for d in D:
        print(f"  {d['column']:28s} {d['definition']} [{d['measured_at']}{', HINDSIGHT' if d['hindsight'] else ''}]")
    show = ["symbol", "date_entry", "gap", "pct_gap", "rv", "G2_on", "level_200", "taken_ungated", "taken_G2", "skip_reason_G2", "pnl_cap10_bp", "hold_cap10",
            "exit_reason_cap10", "pnl_path10_bp", "mfe10_bp", "mae10_bp", "htb", "status_meta"]
    print("\nHEAD (5 rows, a handful of columns)")
    print("  " + " | ".join(show))
    for i in range(5):
        print("  " + " | ".join(fmt(C[c][i])[:12] for c in show))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
