"""D360 -- the news-gap short: a down-gap on abnormal volume in an ordinary name, entered short at the next open.

    uv run python scripts/run_d360_news_gap_short.py --selftest
    uv run python scripts/run_d360_news_gap_short.py --stage0                                   the premise: the event's own drift
    uv run python scripts/run_d360_news_gap_short.py --cell 2:10 --draws 100 --part 1           A' and B for one cell (one process per cell)
    uv run python scripts/run_d360_news_gap_short.py --report
    --out-dir DIR   (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)

Pre-registration: docs/decisions/D360-the-news-gap-short-a-down-gap-on-abnormal-volume-in-an-ordinary-name.md

The signal, on day g for every name with elig[g+1] (eligible AFTER the gap), from the panel's own split-adjusted bars:
    gap[g] = OPEN[g] / CLOSE[g-1] - 1          (the price gap; the fixture is split-adjusted and dividends sit in the same frame, meta D75)
    rv[g]  = VOL[g] / median(VOL[g-21 .. g-1])  (NaN unless all 21 prior volumes are finite and the median is > 0)
    the cross-section cs[g] = elig[g+1] & finite gap & finite rv; pct_gap and pct_rv = V47.percentile_grid over cs[g] (average rank
    on ties, undefined below 50 names; low pct_gap = the most negative gap, high pct_rv = the most volume)
    cell (p, q):     pct_gap <= p  &  pct_rv >= 100 - q      -> event at t = g + 1, SHORT at open(g+1), every event, no slot cap
    no-volume arm p: pct_gap <= p  &  pct_rv < 50            -> short, beside (disjoint from every cell)
    mirror (p, q):   pct_gap >= 100 - p  &  pct_rv >= 100 - q -> LONG, beside
    complement:      pct_gap > p   &  pct_rv >= 100 - q      -> with the cell it partitions the volume gap-downs VG_q ([G])
Exclusions on day g, applied to every arm and counted: an ex-distribution day (a dividend entry in the events file of at least 1% of
CLOSE[g-1], read straight from data/fixtures/*_events.json -- the loader keeps no amounts on the panel) [XD]; a zero-volume gap day or
a non-finite prior close [V0]. Cells (2,10) PRIMARY, (2,20), (5,10), (5,20). Exits: cap 10 (PRIMARY), cap 20, recovery (exit when the
close has retraced half the gap, capped at 20) -- the recovery exit runs THROUGH the kernel's invalidation mechanism on a per-name
score grid keyed on the name's most recent event (build_rec; a replay of the kernel's own skip / cap / delisting rules).
Hedged by the floored universe (A3: mkt = m_f). A name already held is skipped by the kernel and counted (event_accounting / replay).

Stage 0 (the premise): the mean hedged forward 10- and 20-bar return of the NAME from open(g+1) after the primary cell's events
(V47.forward_excess_grid h=10/20, a direct grid, not the ledger), beside the no-volume arm and the same names on random eligible days
(one A' draw); the short earns the negative.

Nulls on the primary exit per cell: A' (per-name rotation within elig), B (same day, same rsi bucket, random eligible name with a
defined rsi percentile), C (1,000 sign flips). Cost: 2c (V47.two_c) PUB and PB, D337's gc_htb borrow in the net, HTB share, the
breakeven half-spread after commission and borrow; the deployed base with the 4- and 2-crossing lines.

Everything shared is imported, not copied: d348_prep (FIRST), run_d359 (simulate / run_short / run_mirror, deployed_block with the
2-crossing line, trade_block with borrow and the four groups, aprime_draw, assert_S_short, perturb_test, bucket_interaction) and, via
it, run_d358 (events, simulate, assert_ID, assert_HX, control_C, null_stats, observed_stats, assert_B, deployed_subsets, pct_direct),
run_d353 (b_pool_P, assert_S, assert_series_defs, _dist), run_d349 (borrow_of, check_borrow, event_accounting), run_d350 (four_groups, clean).

ASSERTIONS [K][F0][R][GAP][E][XD][V0][G][R5][SB][S][A'][B][C][HX][REC][6] -- pre-reg section 8.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import warnings
import hashlib
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
V59 = _load("d359r", "run_d359_loser_rally_short.py")       # the short conventions (its own _loads are memoised)
V58, V53, V49, V50 = V59.V58, V59.V53, V59.V49, V59.V50
V47 = PREP.V47
EB, G22, BR, M = PREP.EB, PREP.G22, PREP.BR, PREP.M
SEED, X_TARGET = V47.SEED, V47.X_TARGET
CONVS = V47.CONVS
STUDY = 360
CELLS = [(2, 10), (2, 20), (5, 10), (5, 20)]                # index 0..3 fixes the RNG keys
PRIMARY = (2, 10)
EXITS = (("cap", 10), ("cap", 20), ("recovery", 20))
EXIT_NAME = {("cap", 10): "cap10", ("cap", 20): "cap20", ("recovery", 20): "rec20"}
PRIMARY_EXIT = "cap10"
REC_CAP = 20
VOL_WIN = 21
XD_MIN = 0.01
NOVOL_PCT = 50.0
ARM = dict(A=1, B=2, C=4)                                    # seed arms as D359: A' 1, B 2, C 4
PER_SHARE, BORROW_SCHEME = V49.PER_SHARE, V49.BORROW_SCHEME
D353_TRADES, D353_MEAN = 27_316, 43.3806
FIXTURE, EVENTS_FILE = Path(M.B.FIXTURE), Path(M.B.EVENTS)
DATA = REPO / "data"
SELFTEST_TMP = REPO / "temp" / "d360_selftest"
OPEN_CACHE = REPO / "temp" / "d360_prep"
OPEN_FILL_VERSION = "d360-open-v1"
run_short, run_mirror, simulate = V59.run_short, V59.run_mirror, V59.simulate
deployed_block, trade_block, aprime_draw = V59.deployed_block, V59.trade_block, V59.aprime_draw
assert_S_short, perturb_test, bucket_interaction = V59.assert_S_short, V59.perturb_test, V59.bucket_interaction
deployed_subsets, assert_HX, control_C, null_stats, observed_stats, assert_B = (V58.deployed_subsets, V58.assert_HX, V58.control_C,
                                                                                V58.null_stats, V58.observed_stats, V58.assert_B)
pct_direct = V58.pct_direct
clean = V50.clean


def cell_name(p, q):
    return f"{p}:{q}"


def fq(x, nd=2):
    """A signed number, or '-' for None."""
    return "-" if x is None else f"{x:+.{nd}f}"


def zeros(x):
    return np.zeros_like(x)


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, stage0=d / "d360_stage0.json", ctrl=str(d / "d360_ctrl_{p}_{q}_p{part}.json"), report=d / "d360_news_gap_short.json")


# ------------------------------------------------------------------ the panel's bars, streamed (P["panel"] is None on a cache HIT)
def stream_grids(symbols, dates):
    """OPEN and CLOSE (T, n) from the fixture's rows, placed by symbol and date exactly as ragged_panel.load_ragged places them
    (r['timestamp'][:10], float(r['open']), float(r['close'])) -- without materialising 4.1M bar objects. CLOSE is asserted
    bit-identical to the prep's CLOSE (panel.closes.T) before OPEN is trusted."""
    sym = {s: i for i, s in enumerate(symbols)}
    pos = {d: t for t, d in enumerate(dates)}
    T, n = len(dates), len(symbols)
    O, C = np.full((T, n), np.nan), np.full((T, n), np.nan)
    seen = 0
    with gzip.open(FIXTURE, "rt") as f:
        for r in csv.DictReader(f):
            i, t = sym.get(r["symbol"]), pos.get(r["timestamp"][:10])
            if i is None or t is None:
                continue
            assert not np.isfinite(C[t, i]), f"duplicate bar {r['symbol']} {r['timestamp'][:10]}"
            O[t, i], C[t, i] = float(r["open"]), float(r["close"])
            seen += 1
    return O, C, seen


def stream_lookup(want):
    """{(symbol, date): (open, close)} for the wanted keys, by the symbol and date strings alone (no grid index): the second,
    independent read of the raw bars for [GAP] and [REC]."""
    out = {}
    with gzip.open(FIXTURE, "rt") as f:
        for r in csv.DictReader(f):
            k = (r["symbol"], r["timestamp"][:10])
            if k in want:
                assert k not in out, f"duplicate raw bar {k}"
                out[k] = (float(r["open"]), float(r["close"]))
    return out


def open_cache_key(P):
    h = hashlib.sha1()
    for p in (FIXTURE, EVENTS_FILE):
        st = p.stat()
        h.update(f"{p}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(str(P["cache_key"]).encode())
    h.update(OPEN_FILL_VERSION.encode())
    return h.hexdigest()[:16]


def open_grid(P):
    """(T, n) split-adjusted open, NaN off live; cached in temp/d360_prep/ keyed on the fixture, the events file, the d348 cache key
    and the fill version. On a miss the streamed CLOSE must equal P['CLOSE'] bit-identically and OPEN must be finite and positive on
    exactly the live cells."""
    f = OPEN_CACHE / f"open_{open_cache_key(P)}.npy"
    if f.exists():
        O = np.load(f)
        print(f"    [K] d360 open grid cache HIT {f.name}")
    else:
        t0 = time.time()
        O, C, seen = stream_grids(P["symbols"], P["dates"])
        CLOSE, live = np.asarray(P["CLOSE"]), np.asarray(P["live"]).T
        assert np.array_equal(C, CLOSE, equal_nan=True), "[K] the streamed close grid != the prep's CLOSE (panel.closes.T)"
        assert seen == int(live.sum()) and np.array_equal(np.isfinite(O), live), "[K] the streamed bars do not cover exactly the live cells"
        assert (O[live] > 0).all(), "[K] a non-positive open on a live cell"
        OPEN_CACHE.mkdir(parents=True, exist_ok=True)
        np.save(f, O)
        print(f"    [K] d360 open grid BUILT from {FIXTURE.name} ({seen:,} bars, {time.time() - t0:.0f}s): streamed CLOSE == prep CLOSE bit-identically, "
              f"OPEN finite and > 0 on exactly the live cells; cached {f.name}")
    assert O.shape == (P["T"], P["n"])
    return O


# ------------------------------------------------------------------ the dividends (from the events file)
def parse_div(it):
    """The loader's two shapes: ['2016-11-08T00:00:00', 0.09] and {'date': ..., 'amount': ...}."""
    if isinstance(it, (list, tuple)):
        return str(it[0])[:10], float(it[1])
    d = str(it.get("date") or it.get("ex_date") or "")[:10]
    return d, float(it.get("amount", it.get("dividend", 0.0)) or 0.0)


def xd_grids(P):
    """XD[t, i]: an ex-distribution entry of at least XD_MIN x CLOSE[t-1, i] (both in the fixture's split-adjusted frame, meta D75);
    ANYDIV[t, i]: any positive entry placed on a live bar (the kernel's r1T is the TOTAL return, so the gap identity to r1T/ocT holds
    only off these). Amounts are re-read from the events file: ragged_panel applies them into total_log_returns and keeps no amounts."""
    ev = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    payload = ev.get("dividends", ev) if isinstance(ev, dict) else ev
    sym = {s: i for i, s in enumerate(P["symbols"])}
    pos = {d: t for t, d in enumerate(P["dates"])}
    CLOSE, live = np.asarray(P["CLOSE"]), np.asarray(P["live"]).T
    T, n = CLOSE.shape
    XD, ANY = np.zeros((T, n), bool), np.zeros((T, n), bool)
    RATIO = np.zeros((T, n))
    cnt = dict(entries=0, placed=0, no_prior_close=0, ge_1pct=0)
    for s, items in (payload.items() if isinstance(payload, dict) else []):
        i = sym.get(s)
        if i is None:
            continue
        for it in items:
            d, amt = parse_div(it)
            cnt["entries"] += 1
            t = pos.get(d)
            if t is None or amt <= 0.0 or not live[t, i]:
                continue
            ANY[t, i] = True
            cnt["placed"] += 1
            prev = CLOSE[t - 1, i] if t > 0 else np.nan
            if not (np.isfinite(prev) and prev > 0):
                cnt["no_prior_close"] += 1
                continue
            r = amt / prev
            RATIO[t, i] = max(RATIO[t, i], r)
            if r >= XD_MIN:
                XD[t, i] = True
    cnt["ge_1pct"] = int(XD.sum())
    return XD, ANY, RATIO, cnt


# ------------------------------------------------------------------ relative volume
def relative_volume(VOL, win=VOL_WIN, chunk=100):
    """rv[g, i] = VOL[g, i] / median(VOL[g-win .. g-1, i]); NaN unless all win prior volumes are finite (np.median of a window with a
    NaN is NaN) and the median is > 0. Column chunks keep the sliding-window sort under ~100 MB."""
    T, n = VOL.shape
    rv = np.full((T, n), np.nan)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        W = np.lib.stride_tricks.sliding_window_view(VOL[:, a:b], win, axis=0)     # W[k] covers bars k .. k+win-1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)                        # a window with a NaN yields NaN, as intended
            med = np.median(W, axis=-1)                                             # (T-win+1, b-a): med[k] = median(VOL[k:k+win])
        m = np.full((T, b - a), np.nan)
        m[win:] = med[:T - win]                                                     # m[g] = median(VOL[g-win:g])
        with np.errstate(invalid="ignore", divide="ignore"):
            r = VOL[:, a:b] / m
        r[~(m > 0)] = np.nan
        rv[:, a:b] = r
    return rv


def rv_direct(VOL, g, i, win=VOL_WIN):
    w = VOL[g - win:g, i]
    if g < win or not np.isfinite(w).all():
        return np.nan
    m = float(np.median(w))
    return VOL[g, i] / m if m > 0 else np.nan


# ------------------------------------------------------------------ the signal
_G = {}


def signal_grids(P):
    """Memoised: OPEN, gap, rv, the cross-section, the two percentile grids, the exclusions, the kernel's score (100 - pct_gap
    lagged one bar: the most negative gap has the highest score, so the short enters it first) and its defined bars."""
    if "g" in _G:
        return _G["g"]
    OPEN = open_grid(P)
    CLOSE, VOL, elig = np.asarray(P["CLOSE"]), np.asarray(P["VOL"]), np.asarray(P["elig"])
    T, n = CLOSE.shape
    gap = np.full((T, n), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        gap[1:] = OPEN[1:] / CLOSE[:-1] - 1.0
    gap[1:][~(CLOSE[:-1] > 0)] = np.nan
    rv = relative_volume(VOL)
    cs = np.zeros((T, n), bool)
    cs[:-1] = elig[1:]                                          # eligible AFTER the gap
    cs &= np.isfinite(gap) & np.isfinite(rv)
    pct_gap = V47.percentile_grid(np.where(cs, gap, np.nan))
    pct_rv = V47.percentile_grid(np.where(cs, rv, np.nan))
    XD, ANYDIV, RATIO, xd_counts = xd_grids(P)
    V0 = VOL == 0
    NF = np.ones((T, n), bool)
    NF[1:] = ~(np.isfinite(CLOSE[:-1]) & (CLOSE[:-1] > 0))
    bad = XD | V0 | NF
    sc = np.full((T, n), np.nan)
    sc[1:] = 100.0 - pct_gap[:-1]
    defined = EB.defined_bars(sc)
    _G["g"] = dict(OPEN=OPEN, CLOSE=CLOSE, VOL=VOL, gap=gap, rv=rv, cs=cs, pct_gap=pct_gap, pct_rv=pct_rv, XD=XD, ANYDIV=ANYDIV, RATIO=RATIO,
                   xd_counts=xd_counts, V0=V0, NF=NF, bad=bad, sc=sc, defined=defined, elig=elig)
    return _G["g"]


def shift(m):
    """A day-g mask -> the event mask at t = g + 1."""
    out = np.zeros_like(m)
    out[1:] = m[:-1]
    return np.ascontiguousarray(out)


def _arm(G, day_mask, label):
    """Apply the exclusions to a day-g candidate mask; return the event grid at g + 1 and the counts."""
    raw = day_mask & G["cs"]
    ev = shift(raw & ~G["bad"])
    counts = dict(arm=label, raw=int(raw.sum()), xd=int((raw & G["XD"]).sum()), v0=int((raw & G["V0"]).sum()), nf=int((raw & G["NF"]).sum()),
                  excluded=int((raw & G["bad"]).sum()), events=int(ev.sum()))
    return ev, counts


def cell_signal(P, p, q):
    G = signal_grids(P)
    with np.errstate(invalid="ignore"):
        return _arm(G, (G["pct_gap"] <= float(p)) & (G["pct_rv"] >= 100.0 - q), f"cell {cell_name(p, q)}")


def complement_signal(P, p, q):
    G = signal_grids(P)
    with np.errstate(invalid="ignore"):
        return _arm(G, (G["pct_gap"] > float(p)) & (G["pct_rv"] >= 100.0 - q), f"complement {cell_name(p, q)}")


def volume_gapdowns(P, q):
    G = signal_grids(P)
    with np.errstate(invalid="ignore"):
        return _arm(G, G["pct_rv"] >= 100.0 - q, f"VG_{q}")


def novol_signal(P, p):
    G = signal_grids(P)
    with np.errstate(invalid="ignore"):
        return _arm(G, (G["pct_gap"] <= float(p)) & (G["pct_rv"] < NOVOL_PCT), f"no-volume {p}")


def mirror_signal(P, p, q):
    G = signal_grids(P)
    with np.errstate(invalid="ignore"):
        return _arm(G, (G["pct_gap"] >= 100.0 - p) & (G["pct_rv"] >= 100.0 - q), f"mirror {cell_name(p, q)}")


# ------------------------------------------------------------------ the recovery exit through the kernel's invalidation mechanism
def build_rec(P, sig, side, cap=REC_CAP):
    """The per-name score grid for exit='invalidation': the kernel exits a short when score <= 50 and a long when score >= 50, on
    information through t-1 (score_T[t]). rec[t, i] carries the exit value iff the trade open on name i at bar t (keyed on the name's
    most recent TAKEN event g, entered at g+1) has close(t-1) past the half-gap level thr = open(g) + 0.5 (close(g-1) - open(g)) with
    t-1 > g+1 (the entry day's close does not count), the no-exit value elsewhere, NaN on bars where the study's cross-section is
    undefined. The walk replays the kernel's own rules -- exits before entries at a bar (re-entry on the exit bar allowed), a name
    already held skips the event, cap = age >= cap, a delisting pops the position -- so it also predicts every trade's age; the
    kernel's ledger is asserted equal to that prediction ([REC] replay identity) and 300 trades are checked against the raw closes."""
    G = signal_grids(P)
    OPEN, CLOSE, finT, defined = G["OPEN"], G["CLOSE"], np.asarray(P["finT"]), G["defined"]
    T, n = sig.shape
    no_exit, do_exit = (100.0, 0.0) if side == 1 else (0.0, 100.0)
    cond = (lambda c, thr: c >= thr) if side == 1 else (lambda c, thr: c <= thr)
    rec = np.full((T, n), no_exit)
    rec[~defined] = np.nan
    pred, acc = [], dict(events=int(sig.sum()), entries=0, already_held=0, unpriced=0, open_at_end=0, by_reason=dict(recovery=0, cap=0, delist=0))
    for i in np.flatnonzero(sig.any(axis=0)):
        exit_bar = -1
        for t in np.flatnonzero(sig[:, i]):
            t = int(t)
            if t < 1 or not finT[t, i]:
                acc["unpriced"] += 1
                continue
            if t < exit_bar:
                acc["already_held"] += 1
                continue
            g = t - 1
            thr = OPEN[g, i] + 0.5 * (CLOSE[g - 1, i] - OPEN[g, i])
            t_exit, reason = None, None
            for u in range(t, T):
                age = u - t
                if not finT[u, i]:
                    t_exit, reason = u, "delist"
                    break
                if age > 0:
                    if age >= cap:
                        t_exit, reason = u, "cap"
                        break
                    if u - 1 >= g + 2 and cond(CLOSE[u - 1, i], thr):
                        t_exit, reason = u, "recovery"
                        break
            acc["entries"] += 1
            if t_exit is None:
                acc["open_at_end"] += 1
                exit_bar = T
            else:
                pred.append((int(i), t, t_exit - t, reason))
                acc["by_reason"][reason] += 1
                exit_bar = t_exit
            for u in range(t + 1, min(exit_bar, T - 1) + 1):
                if u - 1 >= g + 2 and cond(CLOSE[u - 1, i], thr):
                    rec[u, i] = do_exit
    acc["trades"] = len(pred)
    assert acc["events"] == acc["entries"] + acc["already_held"] + acc["unpriced"], "[REC] replay: events != entries + already held + unpriced"
    assert acc["trades"] == acc["entries"] - acc["open_at_end"], "[REC] replay: trades != entries - open at end"
    return rec, pred, acc


def assert_rec_identity(res, pred, acc):
    """The kernel's recovery ledger equals the replay's prediction trade for trade (row, e0, age)."""
    got = sorted((int(r), int(e0), int(a)) for r, e0, a, _p, _s in res["trades"])
    want = sorted((r, e0, a) for r, e0, a, _reason in pred)
    assert int(res["ent"].sum()) == acc["entries"], f"[REC] kernel entries {int(res['ent'].sum())} != replay {acc['entries']}"
    assert got == want, "[REC] the kernel's recovery ledger differs from the replay (row, e0, age)"
    return len(got)


def assert_REC(P, trades, side, raw, cap=REC_CAP, tag="[REC]"):
    """Every given closed trade either hit the cap, was truncated by a delisting, or closed on the FIRST bar t' > g+1 whose close
    was past the half-gap level -- checked on the RAW bars (open(g), close(g-1) and the closes along the path from stream_lookup,
    keyed by symbol and date strings), independently of every grid."""
    finT, symbols, dates = np.asarray(P["finT"]), P["symbols"], P["dates"]
    cond = (lambda c, thr: c >= thr) if side == 1 else (lambda c, thr: c <= thr)
    n_cap = n_rec = n_del = 0
    for row, e0, age, _p, sd in trades:
        assert sd == side, f"{tag} a trade on the wrong side"
        s, g, last = symbols[row], e0 - 1, e0 + age - 1
        o_g, c_gm1 = raw[(s, dates[g])][0], raw[(s, dates[g - 1])][1]
        thr = o_g + 0.5 * (c_gm1 - o_g)
        first = next((u for u in range(g + 2, last + 1) if cond(raw[(s, dates[u])][1], thr)), None)
        delisted = e0 + age >= len(dates) or not finT[e0 + age, row]
        if age == cap:
            assert first is None or first == last, f"{tag} {s} {dates[e0]}: held to the cap past a retrace at bar {first}"
            n_cap += 1
        elif delisted:
            assert first is None or first == last, f"{tag} {s} {dates[e0]}: delisting-truncated past a retrace at bar {first}"
            n_del += 1
        else:
            assert first == last, f"{tag} {s} {dates[e0]}: closed after {age} bars but the half-gap condition first held at bar {first} (last held {last})"
            n_rec += 1
    return n_rec, n_cap, n_del


# ------------------------------------------------------------------ the kernel: exits by name
def run(P, sig, side, exit_name, rec=None):
    """The kernel on the study's score for the cap exits; the recovery exit is exit='invalidation' on the rec grid, cap 20."""
    G = signal_grids(P)
    if exit_name == "rec20":
        if rec is None:
            rec = build_rec(P, sig, side)[0]
        return simulate(P, sig, rec, "invalidation", REC_CAP, side)
    cap = {"cap10": 10, "cap20": 20}[exit_name]
    return simulate(P, sig, G["sc"], "cap", cap, side)


# ------------------------------------------------------------------ [GAP]
def gap_keys(P, events):
    dates, symbols = P["dates"], P["symbols"]
    keys = set()
    for t, i in events:
        keys.add((symbols[i], dates[t - 1]))
        keys.add((symbols[i], dates[t - 2]))
    return keys


def rec_keys(P, trades):
    dates, symbols = P["dates"], P["symbols"]
    keys = set()
    for row, e0, age, _p, _s in trades:
        for u in range(e0 - 2, min(e0 + age + 1, len(dates))):          # one bar past the exit: [6] perturbs a trade by +1 bar
            keys.add((symbols[row], dates[u]))
    return keys


def assert_GAP(P, G, events, raw, OPEN=None, tol=1e-12, tag="[GAP]"):
    """On the sampled events (t = g+1, i): the derived gap equals open(g) / close(g-1) - 1 from the raw bars to tol; rv equals a direct
    recomputation from VOL; the kernel identity (1 + r1T) / (1 + ocT) - 1 == gap off dividend days; the as-traded gap (x RAW) agrees
    off split days. OPEN may be a perturbed grid ([6])."""
    OPEN = G["OPEN"] if OPEN is None else OPEN
    CLOSE, VOL, r1T, ocT, RAW = G["CLOSE"], G["VOL"], np.asarray(P["r1T"]), np.asarray(P["ocT"]), np.asarray(P["RAW"])
    dates, symbols = P["dates"], P["symbols"]
    worst = worst_rv = worst_k = worst_raw = 0.0
    n_div = n_split = 0
    for t, i in events:
        g = t - 1
        s = symbols[i]
        o_g, c_prev = raw[(s, dates[g])][0], raw[(s, dates[g - 1])][1]
        derived = OPEN[g, i] / CLOSE[g - 1, i] - 1.0
        d = abs(derived - (o_g / c_prev - 1.0))
        worst = max(worst, d)
        assert d < tol, f"{tag} {s} {dates[g]}: derived gap {derived:.12f} vs raw bars {o_g / c_prev - 1.0:.12f} ({d:.1e})"
        assert G["gap"][g, i] == derived or OPEN is not G["OPEN"], f"{tag} the gap grid is not the derived gap"
        worst_rv = max(worst_rv, abs(G["rv"][g, i] - rv_direct(VOL, g, i)))
        if G["ANYDIV"][g, i]:
            n_div += 1
        else:
            worst_k = max(worst_k, abs((1.0 + r1T[g, i]) / (1.0 + ocT[g, i]) - 1.0 - derived))
        if RAW[g, i] != RAW[g - 1, i]:
            n_split += 1
        else:
            worst_raw = max(worst_raw, abs(OPEN[g, i] * RAW[g, i] / (CLOSE[g - 1, i] * RAW[g - 1, i]) - 1.0 - derived))
    assert worst_rv < tol, f"{tag} rv differs from the direct recomputation ({worst_rv:.1e})"
    assert worst_k < 1e-9, f"{tag} the kernel identity (1 + r1T) / (1 + ocT) - 1 differs from the gap off dividend days ({worst_k:.1e})"
    assert worst_raw < 1e-9, f"{tag} the as-traded gap differs from the adjusted gap off split days ({worst_raw:.1e})"
    return dict(n=len(events), worst=worst, worst_rv=worst_rv, worst_kernel=worst_k, worst_as_traded=worst_raw, dividend_days=n_div, split_days=n_split)


# ------------------------------------------------------------------ [E] [XD] [V0] [G]
def assert_E(P, rng, k=300):
    G = signal_grids(P)
    elig, cs, gap, rv = G["elig"], G["cs"], G["gap"], G["rv"]
    lines = []
    for p, q in CELLS:
        sh, _c = cell_signal(P, p, q)
        ev = np.argwhere(sh)
        pick = ev[rng.choice(len(ev), size=min(k, len(ev)), replace=False)]
        worst = 0.0
        for t, i in pick:
            g = t - 1
            assert elig[t, i] and t >= P["m_start"] and g >= 1, "[E] an event off the eligible set after the gap"
            col_g = np.where(cs[g], gap[g], np.nan)
            col_v = np.where(cs[g], rv[g], np.nan)
            dg, kg = pct_direct(col_g, i)
            dv, kv = pct_direct(col_v, i)
            assert kg == kv == int(cs[g].sum()) >= 50, "[E] the direct cross-section count differs or is undefined"
            assert np.isfinite(dg) and np.isfinite(dv) and dg <= p and dv >= 100.0 - q, f"[E] {cell_name(p, q)} event ({t}, {i}): gap pct {dg:.2f}, rv pct {dv:.2f} among {kg}"
            assert not G["bad"][g, i], "[E] an excluded day survived"
            worst = max(worst, abs(dg - G["pct_gap"][g, i]), abs(dv - G["pct_rv"][g, i]))
        assert worst < 1e-9, f"[E] {cell_name(p, q)}: grid mismatch {worst:.1e}"
        lines.append(f"{cell_name(p, q)} {len(pick)} ({worst:.0e})")
    return lines


def assert_XD(sig, XD, tag="[XD]"):
    """No surviving event (at t = g+1) sits on an ex-distribution day g."""
    n = int((sig & shift(XD)).sum())
    assert n == 0, f"{tag} {n} surviving events on an ex-distribution day"


def assert_V0(sig, V0, NF, tag="[V0]"):
    n0, nf = int((sig & shift(V0)).sum()), int((sig & shift(NF)).sum())
    assert n0 == 0 and nf == 0, f"{tag} {n0} surviving events on a zero-volume day, {nf} with a non-finite prior close"


def assert_G(P):
    """Every cell and its complement partition the volume gap-downs VG_q (disjoint, union equal); the no-volume arm is disjoint from
    every cell; the mirror is disjoint from every cell; the cells nest (2 in 5 at the same q, q=10 in q=20 at the same p)."""
    counts = {}
    sigs = {}
    for p, q in CELLS:
        sh, c = cell_signal(P, p, q)
        comp, cc = complement_signal(P, p, q)
        vg, cv = volume_gapdowns(P, q)
        assert not (sh & comp).any(), f"[G] cell {cell_name(p, q)} and its complement overlap"
        assert np.array_equal(sh | comp, vg), f"[G] cell u complement != the volume gap-downs at q={q}"
        mir, cm = mirror_signal(P, p, q)
        assert not (sh & mir).any(), f"[G] the mirror overlaps cell {cell_name(p, q)}"
        counts[cell_name(p, q)] = dict(cell=c, complement=cc, vg=cv, mirror=cm)
        sigs[(p, q)] = sh
    for p in (2, 5):
        nv, cn = novol_signal(P, p)
        for p_, q in CELLS:
            assert not (nv & sigs[(p_, q)]).any(), f"[G] the no-volume arm {p} overlaps cell {cell_name(p_, q)}"
        counts[f"novol {p}"] = cn
    for q in (10, 20):
        assert not (sigs[(2, q)] & ~sigs[(5, q)]).any(), f"[G] cell 2:{q} not inside 5:{q}"
    for p in (2, 5):
        assert not (sigs[(p, 10)] & ~sigs[(p, 20)]).any(), f"[G] cell {p}:10 not inside {p}:20"
    return counts


# ------------------------------------------------------------------ [R5] and Q7
def d353_ledger(P):
    """D353's rev_5 bottom-decile cap-40 long ledger by D358's path (V58.events + V58.simulate, CAP = 40)."""
    lo10, pct10, _ = V58.events(P, "rev_5", 10)
    return V58.simulate(P, lo10, pct10, "cap"), pct10


def assert_R5(P, res10, pct10, full=True):
    """The ledger equals D353's: 27,316 trades, mean +43.3806 bp to 1e-9 against data/d353_rev5_record.json; then D358's assert_ID
    (the deployed base against a re-run of D353's own code path)."""
    d353 = json.loads(V58.D353_JSON.read_text())["arms"]["long/cap"]
    pnl = V47.pnl_bp(res10)
    assert len(res10["trades"]) == D353_TRADES == d353["trades"], f"[R5] {len(res10['trades']):,} trades != D353's {D353_TRADES:,}"
    obs = float(pnl.mean())
    assert abs(obs - d353["mean_bp"]) < 1e-9, f"[R5] mean {obs:.10f} != D353's stored {d353['mean_bp']:.10f}"
    assert abs(obs - D353_MEAN) < 5e-5, f"[R5] mean {obs:.4f} != +{D353_MEAN}"
    assert all(t[4] == 0 and t[2] <= 40 for t in res10["trades"]), "[R5] a short or an over-cap hold in the long ledger"
    if full:
        V58.assert_ID(P, res10, pct10)
    return obs


def q7_split(P, res10):
    """For each D353 trade, whether its trigger bar g = e0 - 1 (the bar whose percentile fired the event) is a primary-cell gap day:
    pct_gap[g] <= 2 and pct_rv[g] >= 90 on that day (the elig[g+1] clause is moot: the trade entered). Covers every trade."""
    G = signal_grids(P)
    tr = res10["trades"]
    rows = np.array([t[0] for t in tr])
    gs = np.array([t[1] for t in tr]) - 1
    pnl = V47.pnl_bp(res10)
    p0, q0 = PRIMARY
    with np.errstate(invalid="ignore"):
        is_gap = (G["pct_gap"][gs, rows] <= float(p0)) & (G["pct_rv"][gs, rows] >= 100.0 - q0)
    undefined = ~np.isfinite(G["pct_gap"][gs, rows])
    assert int(is_gap.sum()) + int((~is_gap).sum()) == len(tr) == D353_TRADES, "[R5] the Q7 split does not cover every trade"
    mg = float(pnl[is_gap].mean()) if is_gap.any() else None
    mr = float(pnl[~is_gap].mean())
    return dict(trades=len(tr), gap_n=int(is_gap.sum()), gap_mean_bp=mg, gap_median_bp=float(np.median(pnl[is_gap])) if is_gap.any() else None,
                rest_n=int((~is_gap).sum()), rest_mean_bp=mr, diff_bp=(mg - mr) if mg is not None else None, undefined_pct_n=int(undefined.sum()),
                rule=f"trigger bar g = e0 - 1 with pct_gap[g] <= {p0} and pct_rv[g] >= {100 - q0}")


# ------------------------------------------------------------------ Stage 0
def stage0_compute(P):
    G = signal_grids(P)
    elig = G["elig"]
    p0, q0 = PRIMARY
    sh, c_sh = cell_signal(P, p0, q0)
    nv, c_nv = novol_signal(P, p0)
    seed = [SEED, STUDY, 0, 0]
    ss, _sc = aprime_draw(sh, G["sc"], elig, np.random.default_rng(seed))
    F = {h: V47.forward_excess_grid(P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["finT"], h=h) for h in (10, 20)}
    T = P["T"]
    half = T // 2
    t_ = np.arange(T)
    subsets = {"span": np.ones(T, bool), "era1": t_ < half, "era2": t_ >= half, "down_years": np.isin(np.asarray(P["years"]), list(P["down_years"]))}
    rows = {"primary_events": sh, "no_volume_arm": nv, "random_eligible_days": ss}
    table, worst = {}, 0.0
    for nm, m in rows.items():
        table[nm] = dict(events=int(m.sum()))
        for h in (10, 20):
            for s, tm in subsets.items():
                mm = m & tm[:, None] & np.isfinite(F[h])
                k = int(mm.sum())
                bp = float(F[h][mm].sum() / k) * 1e4 if k else None
                if k:
                    chk = float(np.nanmean(np.where(mm, F[h], np.nan))) * 1e4          # the second implementation
                    worst = max(worst, abs(chk - bp))
                table[nm][f"F{h}_{s}"] = dict(n=k, bp=bp, undefined=int((m & tm[:, None]).sum()) - k)
    assert worst < 1e-9, f"[D] Stage 0's masked mean differs from np.nanmean ({worst:.1e})"
    del F
    return table, worst, seed, dict(primary=c_sh, no_volume=c_nv)


def print_stage0(table):
    print("\n  STAGE 0 -- the premise: the event's own drift. Mean hedged forward return of the NAME from open(g+1) over 10 and 20 bars "
          "(V47.forward_excess_grid: ocT - m_f_oc on the entry bar, r1T - m_f after, truncated at delisting; a direct grid, not the ledger),")
    print("  bp per event [events]; the SHORT earns the negative. Events whose forward window is undefined (the last h bars) are dropped and counted.")
    cols = [f"F{h}_{s}" for h in (10, 20) for s in ("span", "era1", "era2", "down_years")]
    print("  %-24s " % "row" + " ".join("%18s" % c for c in cols))
    for nm, r in table.items():
        print("  %-24s " % f"{nm} [{r['events']:,}]" + " ".join(("%+7.1f [%8s]" % (r[c]["bp"], f"{r[c]['n']:,}")) if r[c]["bp"] is not None else "%18s" % "-" for c in cols))


def stage_stage0(P, paths):
    table, worst, seed, counts = stage0_compute(P)
    print(f"    check: Stage 0's masked mean equals an independent np.where + nanmean on every row x horizon x subset to {worst:.1e}")
    print_stage0(table)
    out = dict(study=STUDY, note="D360 Stage 0: the mean hedged forward 10/20-bar return of the name after the primary cell's events (long convention; the "
                                  "short earns the negative), beside the no-volume arm and the same names on random eligible days (one A' draw).",
               primary=cell_name(*PRIMARY), aprime_seed=seed, table=table, counts=counts, check_worst=worst, era_midpoint_bar=P["T"] // 2,
               era_midpoint_date=P["dates"][P["T"] // 2], down_years=P["down_years"])
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stage0"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['stage0']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


# ------------------------------------------------------------------ the arms in the report
def arm_report(P, sig, counts, side, elig, with_groups, exits):
    G = signal_grids(P)
    out = dict(counts=counts, events=int(sig.sum()))
    for e, cap in exits:
        nm = EXIT_NAME[(e, cap)]
        if nm == "rec20":
            rec, pred, acc = build_rec(P, sig, side)
            res = run(P, sig, side, nm, rec=rec)
            assert_rec_identity(res, pred, acc)
            acc = dict(acc, exit="recovery", replay_identity=True)
        else:
            res = run(P, sig, side, nm)
            acc = V49.event_accounting(P, sig, res, cap=cap)
        V53.assert_series_defs(res)
        hx = dict(hedged=assert_HX(res, P, "book_dep_x", hedged=True), unhedged=assert_HX(res, P, "book_dep", hedged=False))
        hod = int((res["held"] > 0)[~G["defined"]].sum())
        assert hod == 0, f"[HX] {hod} held bars outside the defined bars"
        assert np.array_equal(res["defined"], G["defined"]), f"[HX] {nm}: the kernel's defined bars differ from the study's"
        dep = deployed_block(res, P)
        dep["splits_hedged"] = deployed_subsets(res, P, res["book_dep_x"])
        trd = trade_block(P, res, elig, side, with_groups and nm == PRIMARY_EXIT)
        out[nm] = dict(deployed=dep, per_trade=trd, hx=hx, accounting=acc, res=res)
    return out


def drop_res(d):
    for k in list(d):
        if isinstance(d[k], dict) and "res" in d[k]:
            d[k].pop("res")


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    G = signal_grids(P)
    elig = G["elig"]
    p0, q0 = PRIMARY
    ci0 = CELLS.index(PRIMARY)
    xc = G["xd_counts"]
    print(f"    signal grids: {int(G['cs'].sum()):,} name-days in the cross-section (elig after the gap, finite gap and rv), defined bars {int(G['defined'].sum()):,} "
          f"of {P['T']:,} (undefined after m_start: {int((~G['defined'])[P['m_start']:].sum())}); dividends: {xc['entries']:,} entries, {xc['placed']:,} placed on "
          f"live bars, {xc['ge_1pct']:,} of at least {100 * XD_MIN:.0f}% of the prior close, {xc['no_prior_close']} without a prior close; zero-volume bars "
          f"{int(G['V0'][np.asarray(P['live']).T].sum()):,} ({el()})")
    # events, samples, the primary ledgers, one streaming pass of the raw bars
    sh, c_sh = cell_signal(P, p0, q0)
    union = np.zeros_like(sh)
    for p, q in CELLS:
        union |= cell_signal(P, p, q)[0] | mirror_signal(P, p, q)[0]
    for p in (2, 5):
        union |= novol_signal(P, p)[0]
    rngG = np.random.default_rng([SEED, STUDY, 1])
    ev_all = np.argwhere(union)
    pickG = [tuple(int(x) for x in e) for e in ev_all[rngG.choice(len(ev_all), size=min(300, len(ev_all)), replace=False)]]
    rec, pred, acc_rec = build_rec(P, sh, 1)
    RES = {"cap10": run(P, sh, 1, "cap10"), "cap20": run(P, sh, 1, "cap20"), "rec20": run(P, sh, 1, "rec20", rec=rec)}
    res = RES[PRIMARY_EXIT]
    tr = res["trades"]
    n_rec_id = assert_rec_identity(RES["rec20"], pred, acc_rec)
    rngR = np.random.default_rng([SEED, STUDY, 4])
    trR = RES["rec20"]["trades"]
    pickR = [trR[j] for j in rngR.choice(len(trR), size=min(300, len(trR)), replace=False)]
    want = gap_keys(P, pickG) | rec_keys(P, pickR)
    ts = time.time()
    raw = stream_lookup(want)
    assert len(raw) == len(want), f"[GAP] {len(want) - len(raw)} wanted raw bars not found in {FIXTURE.name}"
    t_stream = time.time() - ts
    # [GAP]
    gp = assert_GAP(P, G, pickG, raw)
    print(f"    [GAP] {gp['n']} sampled events (all cells, arms and mirrors): the derived gap OPEN[g] / CLOSE[g-1] - 1 equals open(g) / close(g-1) - 1 read "
          f"from the raw bars by symbol and date ({len(raw):,} bars, a second streaming pass, {t_stream:.0f}s) to {gp['worst']:.1e}; rv equals the direct "
          f"VOL[g] / median(VOL[g-21..g-1]) to {gp['worst_rv']:.1e}; the kernel identity (1 + r1T) / (1 + ocT) - 1 equals the gap to {gp['worst_kernel']:.1e} "
          f"off dividend days ({gp['dividend_days']} sampled events on a dividend day: r1T is the TOTAL return); the as-traded gap (x RAW) equals the "
          f"adjusted gap to {gp['worst_as_traded']:.1e} off split days ({gp['split_days']} on a split day) ({el()})")
    # [E]
    lines = assert_E(P, np.random.default_rng([SEED, STUDY, 0]))
    print(f"    [E] sampled events satisfy both conditions by direct count among the day's cross-section (elig at g+1, finite gap and rv; >= 50 names): "
          f"gap percentile <= p and rv percentile >= 100 - q, equal the grids to 1e-9, elig holds at g+1, no excluded day: " + ", ".join(lines) + f" ({el()})")
    # [XD] [V0]
    cnts = {}
    for p, q in CELLS:
        s_, c_ = cell_signal(P, p, q)
        assert_XD(s_, G["XD"])
        assert_V0(s_, G["V0"], G["NF"])
        cnts[c_["arm"]] = c_
        m_, cm = mirror_signal(P, p, q)
        assert_XD(m_, G["XD"])
        assert_V0(m_, G["V0"], G["NF"])
        cnts[cm["arm"]] = cm
    for p in (2, 5):
        n_, cn = novol_signal(P, p)
        assert_XD(n_, G["XD"])
        assert_V0(n_, G["V0"], G["NF"])
        cnts[cn["arm"]] = cn
    print(f"    [XD] [V0] no surviving event of any arm is on an ex-distribution day (>= {100 * XD_MIN:.0f}% of the prior close), a zero-volume day or a "
          f"non-finite prior close; excluded (xd / v0 / nf of raw): " + "; ".join(f"{k} {v['xd']}/{v['v0']}/{v['nf']} of {v['raw']:,} -> {v['events']:,}" for k, v in cnts.items()))
    # [G]
    g = assert_G(P)
    print(f"    [G] every cell and its complement partition the volume gap-downs at its q (disjoint, union equal); the no-volume arms are disjoint from every "
          f"cell; the mirrors are disjoint from the cells; the cells nest: " + ", ".join(f"{k} {v['cell']['events']:,} (complement {v['complement']['events']:,}, "
          f"VG {v['vg']['events']:,}, mirror {v['mirror']['events']:,})" for k, v in g.items() if "cell" in v) + f" ({el()})")
    # [R5]
    res10, pct10 = d353_ledger(P)
    obs53 = assert_R5(P, res10, pct10)
    q7 = q7_split(P, res10)
    print(f"    [R5] the rev_5 bottom-decile cap-40 long ledger reproduces D353: {len(res10['trades']):,} trades, mean {obs53:+.4f} bp (== data/d353_rev5_record.json "
          f"to 1e-9; D358's assert_ID against a re-run of D353's own code path passes); the Q7 split covers every trade: {q7['gap_n']:,} entered on a primary-cell "
          f"gap day ({fq(q7['gap_mean_bp'])} bp) vs {q7['rest_n']:,} ({q7['rest_mean_bp']:+.2f}) ({el()})")
    # the primary ledgers
    assert all(t[4] == 1 for t in tr) and all(t[2] <= 10 for t in tr), "[K] a long or an over-cap hold in the primary ledger"
    assert all(t[2] <= 20 for t in RES["rec20"]["trades"]) and all(t[2] <= 20 for t in RES["cap20"]["trades"]), "[K] a hold past 20 under cap 20 / recovery"
    acc = V49.event_accounting(P, sh, res, cap=10)
    print(f"    check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; "
          f"trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end (primary, cap 10); under recovery {acc_rec['entries']:,} entries, "
          f"{acc_rec['already_held']:,} already held, exits {acc_rec['by_reason']}")
    # [SB]
    rng = np.random.default_rng([SEED, STUDY, 5])
    pt, htb, rate = V49.borrow_of(P, tr)
    idx_sb, worst_b = V49.check_borrow(P, tr, pt, htb, rng, k=200)
    assert (rate[htb] == BR.HTB_BPS).all() and (rate[~htb] == BR.GC_BPS).all(), "[SB] rates"
    print(f"    [SB] BORROW: on {len(idx_sb)} sampled short trades the per-trade borrow equals the rule x bars held / 252 to {worst_b:.1e}, and every HTB "
          f"flag agrees with the F0-window / ${BR.PX_HTB:.0f} rule; HTB on {int(htb.sum())} of {len(tr):,} ({100 * htb.mean():.2f}%); mean borrow "
          f"{pt.mean():.2f} bp per trade")
    # [HX]
    lines = []
    for nm, r in RES.items():
        V53.assert_series_defs(r)
        hx = assert_HX(r, P, "book_dep_x", hedged=True)
        hu = assert_HX(r, P, "book_dep", hedged=False)
        hod = int((r["held"] > 0)[~G["defined"]].sum())
        assert hod == 0, f"[HX] {nm}: {hod} held bars outside the defined bars"
        assert np.array_equal(r["defined"], G["defined"]), f"[HX] {nm}: the kernel's defined bars differ from the study's"
        lines.append(f"{nm} {hx['worst']:.0e}/{hu['worst']:.0e} ({hx['uncovered']} tail)")
    print(f"    [HX] hedged deployed x held == the ledger's sgn(v - m) per bar and unhedged x held == sgn v per bar, to 1e-12 on every covered bar "
          f"(open tail excluded, contiguous), the hedged rebuild sums to the ledger to 1e-9, no held bar outside the defined bars; primary cell x three exits: "
          + "; ".join(lines) + f" ({el()})")
    # [REC]
    n_rec, n_cap, n_del = assert_REC(P, pickR, 1, raw)
    print(f"    [REC] the recovery ledger ({n_rec_id:,} trades) equals the replay of the kernel's rules trade for trade (row, e0, age); on {len(pickR)} sampled "
          f"closed trades, checked against the RAW closes: {n_rec} closed on the first bar t' > g+1 with close(t') >= open(g) + 0.5 (close(g-1) - open(g)), "
          f"{n_cap} hit the cap with no earlier retrace, {n_del} were truncated by a delisting ({el()})")
    # [A'] [B]
    PB = V53.b_pool_P(P, elig)
    rngA = np.random.default_rng([SEED, STUDY, ci0, ARM["A"], 0])
    rngB = np.random.default_rng([SEED, STUDY, ci0, ARM["B"], 0])
    obs = observed_stats(res, P)
    A_, B_ = [], []
    rA_keep = None
    for d in range(2):
        ss, sc_ = aprime_draw(sh, G["sc"], elig, rngA)
        rA = run_short(P, ss, sc_, "cap", 10)
        A_.append(null_stats(rA, P))
        sB = V47.control_b_signal(PB, sh, rngB)
        keptB, shortB = assert_B(P, PB, sh, sB, elig)
        B_.append(null_stats(run_short(P, sB, G["sc"], "cap", 10), P))
        if d == 0:
            rA_keep = rA
    fm = lambda xs, key, f: ", ".join(format(x[key], f) for x in xs)
    print(f"    [A'] 2 draws of {cell_name(p0, q0)}: every rotated event eligible, every name's event count kept, no long, the score rotated with the signal, "
          f"deployed series NaN-free; per trade {fm(A_, 'trade_mean_bp', '+.2f')} bp ({fm(A_, 'trades', ',')} trades) vs observed {obs['trade_mean_bp']:+.2f} ({el()})")
    print(f"    [B] every event keeps its date and rsi bucket; replacements are eligible names with a DEFINED rsi percentile, never an event name; "
          f"kept == the pool shortfall ({keptB} of {int(sh.sum()):,}); per trade {fm(B_, 'trade_mean_bp', '+.2f')} bp")
    # [S]
    worst_s, n_s, n_fell, n_rose, worst_m = assert_S_short(P, rA_keep["trades"], np.random.default_rng([SEED, STUDY, 2]))
    pert = perturb_test(P, sh, G["sc"], 1, res, -1.0)
    lo_m, _cm = mirror_signal(P, p0, q0)
    res_m = run(P, lo_m, 0, "cap10")
    assert all(t[4] == 0 for t in res_m["trades"]), "[S] a short in the mirror ledger"
    wm, nm_, n_fav_m = V53.assert_S(P, res_m["trades"], np.random.default_rng([SEED, STUDY, 3]), tol=1e-15)
    pert_m = perturb_test(P, lo_m, G["sc"], 0, res_m, +1.0)
    print(f"    [S] SIGN IN MONEY on the SHORT: {n_s} sampled A' trades equal the open-fill recomputation against the floored market to {worst_s:.1f} "
          f"(bit-identical); a short on a name that fell pays positively ({n_fell} fell, {n_rose} rose, of {n_s}); the LONG of the same path pays the "
          f"opposite amount to {worst_m:.1f}; +50 bp on r1T[{pert['bar']}, {pert['row']}] ({pert['symbol']} {pert['date']}, bar 2 of a {pert['age']}-bar "
          f"short) re-simulated on a perturbed A3 moves that trade by {pert['dpnl']:+.3f} bp and no other, and the deployed series by {pert['delta']:.4f} "
          f"= -50 / {pert['n_open']} open, no other bar; the mirror's {nm_} sampled LONG trades equal the recomputation to {wm:.1f} ({n_fav_m} favourable "
          f"paths pay positively) and +50 bp on {pert_m['symbol']} {pert_m['date']} moves its long by {pert_m['dpnl']:+.3f} ({el()})")
    # [C]
    pnl = V47.pnl_bp(res)
    cC = control_C(pnl, np.random.default_rng([SEED, STUDY, ci0, ARM["C"]]))
    z = assert_C(cC)
    print(f"    [C] control C (1,000 random directions on the primary cap-10 ledger): mean {cC['mean']:+.3f} bp (se {cC['se']:.3f}, z {z:+.2f}) within 3 SE "
          f"of zero (D358's stated weakening of 2 SE kept); p50 {cC['p50']:+.2f} p95 {cC['p95']:+.2f} max {cC['max']:+.2f}; observed {pnl.mean():+.2f} "
          f"{'above' if cC['above'] else 'NOT above'} p95")
    # [6]
    broke = []
    try:                                                              # [GAP] on a perturbed open
        O6 = G["OPEN"].copy()
        t6, i6 = pickG[0]
        O6[t6 - 1, i6] *= 1.0 + 1e-6
        assert_GAP(P, G, pickG, raw, OPEN=O6)
    except AssertionError as e:
        assert "[GAP]" in str(e)
        broke.append("GAP")
    try:                                                              # [S] on a sign-flipped ledger
        assert_S_short(P, [(r, e, a, -p, sd) for r, e, a, p, sd in rA_keep["trades"]], np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    try:                                                              # [XD] with an ex-distribution event admitted
        sh6 = sh.copy()
        cand = np.argwhere(G["XD"][:-1] & G["cs"][:-1])
        if len(cand) == 0:
            cand = np.argwhere(G["XD"][:-1])
        g6, i6 = cand[0]
        sh6[g6 + 1, i6] = True
        assert_XD(sh6, G["XD"])
    except AssertionError as e:
        assert "[XD]" in str(e)
        broke.append("XD")
    try:                                                              # [R5] on a perturbed ledger (+1 bp on one trade)
        r6 = dict(res10, trades=[(r, e, a, p + (1e-4 if j == 0 else 0.0), sd) for j, (r, e, a, p, sd) in enumerate(res10["trades"])])
        assert_R5(P, r6, pct10, full=False)
    except AssertionError as e:
        assert "[R5]" in str(e)
        broke.append("R5")
    try:                                                              # [REC] on a perturbed ledger (one recovery trade held a bar longer)
        j = next(k for k in range(len(pickR)) if pickR[k][2] < REC_CAP)
        r_, e_, a_, p_, s_ = pickR[j]
        assert_REC(P, [(r_, e_, a_ + 1, p_, s_)], 1, raw)
    except AssertionError as e:
        assert "[REC]" in str(e)
        broke.append("REC")
    try:                                                              # [C] can fail
        assert_C(dict(cC, mean=10.0 * cC["se"]))
    except AssertionError as e:
        assert "[C]" in str(e)
        broke.append("C")
    assert broke == ["GAP", "S", "XD", "R5", "REC", "C"], f"[6] raised: {broke}"
    print("    [6] [GAP] raises on a perturbed open (one sampled open x (1 + 1e-6)); [S] raises on a sign-flipped ledger; [XD] raises when an "
          "ex-distribution event is admitted; [R5] raises on a perturbed ledger (+1 bp on one trade); [REC] raises when a recovery trade is held one bar "
          "longer than the rule; [C] raises at 10 SE")
    (SELFTEST_TMP / "selftest_summary.json").write_text(json.dumps(clean(dict(G=g, counts=cnts, gap=gp, C=cC, observed=obs, q7=q7, accounting=acc,
                                                                                rec_accounting=acc_rec)), indent=1))
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def assert_C(cC):
    z = cC["mean"] / cC["se"]
    # D358's stated weakening kept (D359 did the same): the pre-registered band is 3 SE here (section 8), asserted at 3 SE; [6] checks it can fail.
    assert abs(z) < 3.0, f"[C] mean {cC['mean']:+.3f} bp is {z:+.2f} SE from zero"
    return z


def stage_cell(P, p, q, draws, part, paths):
    ci = CELLS.index((p, q))
    G = signal_grids(P)
    elig = G["elig"]
    sh, c_sh = cell_signal(P, p, q)
    res = run(P, sh, 1, "cap10")
    obs = observed_stats(res, P)
    print(f"\n  {cell_name(p, q)} part {part}: {int(sh.sum()):,} events ({c_sh['excluded']} excluded of {c_sh['raw']:,}) -> {obs['trades']:,} trades, {obs['entries']:,} "
          f"entries; per trade {obs['trade_mean_bp']:+.2f} bp; deployed gross {obs['gross_bp']:+.2f} net PUB {obs['net_bp_PUB']:+.2f} bp/bar (Sharpe "
          f"{obs['sharpe_net_PUB']:+.3f}), exposure {100 * obs['exposure']:.1f}%")
    PB = V53.b_pool_P(P, elig)
    seeds = dict(A=[SEED, STUDY, ci, ARM["A"], part], B=[SEED, STUDY, ci, ARM["B"], part])
    rngA, rngB = (np.random.default_rng(seeds[k]) for k in ("A", "B"))
    A_, B_, keptB = [], [], []
    tA = tB = 0.0
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        ss, sc_ = aprime_draw(sh, G["sc"], elig, rngA)
        A_.append(null_stats(run_short(P, ss, sc_, "cap", 10), P))
        t2 = time.time()
        sB = V47.control_b_signal(PB, sh, rngB)
        kb, _ = assert_B(P, PB, sh, sB, elig)
        keptB.append(kb)
        B_.append(null_stats(run_short(P, sB, G["sc"], "cap", 10), P))
        tA += t2 - t1
        tB += time.time() - t2
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {cell_name(p, q)}: {d + 1}/{draws} ({time.time() - ts:.0f}s; A' {tA / (d + 1):.1f} s/draw, B {tB / (d + 1):.1f})", flush=True)
    keys = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trades", "exposure")
    out = dict(study=STUDY, p=p, q=q, cell=cell_name(p, q), cell_index=ci, exit=PRIMARY_EXIT, draws=draws, part=part, seeds=seeds, events=int(sh.sum()),
               counts=c_sh, observed=obs, control_A_prime={k: [x[k] for x in A_] for k in keys}, control_B={k: [x[k] for x in B_] for k in keys},
               B_kept=keptB, B_pool="elig & isfinite(PCT rsi), same day, same rsi bucket", seconds_per_draw=dict(A=tA / max(draws, 1), B=tB / max(draws, 1)),
               rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(p=p, q=q, part=part))
    f.write_text(json.dumps(clean(out)))
    if draws:
        a, b = (np.array(out[k]["trade_mean_bp"]) for k in ("control_A_prime", "control_B"))
        print(f"  wrote {f}: per trade A' p50 {np.median(a):+.2f} p95 {np.quantile(a, .95):+.2f}; B p50 {np.median(b):+.2f} p95 {np.quantile(b, .95):+.2f} "
              f"vs observed {obs['trade_mean_bp']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def load_controls(paths, p, q, obs):
    fs = sorted(paths["dir"].glob(f"d360_ctrl_{p}_{q}_p*.json"))
    if not fs:
        return None
    A, B, parts = {}, {}, []
    for f in fs:
        d = json.loads(f.read_text())
        assert d["p"] == p and d["q"] == q and d["draws"] == len(d["control_A_prime"]["trade_mean_bp"]), f"[P] {f.name}"
        for k in ("net_bp_PUB", "gross_bp", "trade_mean_bp", "trades"):
            assert abs(d["observed"][k] - obs[k]) < 1e-9, f"[P] {f.name}: observed {k} {d['observed'][k]} differs from the re-simulated {obs[k]}"
        for k in d["control_A_prime"]:
            A.setdefault(k, []).extend(d["control_A_prime"][k])
            B.setdefault(k, []).extend(d["control_B"][k])
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], seconds_per_draw=d.get("seconds_per_draw"), B_kept=d.get("B_kept")))
    stats = ("trade_mean_bp", "net_bp_PUB", "sharpe_net_PUB", "gross_bp", "net_bp_PB")
    tdist = lambda x: dict(p50=float(np.median(x)), min=int(min(x)), max=int(max(x)))
    return dict(draws=len(A["trade_mean_bp"]), parts=parts, A_prime={k: V53._dist(A[k], obs[k]) for k in stats}, B={k: V53._dist(B[k], obs[k]) for k in stats},
                A_prime_trades=tdist(A["trades"]), B_trades=tdist(B["trades"]))


def stage_report(P, paths):
    R = {}
    t0 = time.time()
    G = signal_grids(P)
    elig = G["elig"]
    assert paths["stage0"].exists(), f"run --stage0 first ({paths['stage0']})"
    S0 = json.loads(paths["stage0"].read_text())["table"]
    # the check line's three parts: [GAP] on 300 sampled events against the raw bars, the exclusion counts, [R5] before Q7's split
    union = np.zeros((P["T"], P["n"]), bool)
    cnts = {}
    for p, q in CELLS:
        s_, c_ = cell_signal(P, p, q)
        m_, cm = mirror_signal(P, p, q)
        union |= s_ | m_
        cnts[c_["arm"]], cnts[cm["arm"]] = c_, cm
        assert_XD(s_, G["XD"]); assert_V0(s_, G["V0"], G["NF"]); assert_XD(m_, G["XD"]); assert_V0(m_, G["V0"], G["NF"])
    for p in (2, 5):
        n_, cn = novol_signal(P, p)
        union |= n_
        cnts[cn["arm"]] = cn
        assert_XD(n_, G["XD"]); assert_V0(n_, G["V0"], G["NF"])
    ev_all = np.argwhere(union)
    rngG = np.random.default_rng([SEED, STUDY, 1])
    pickG = [tuple(int(x) for x in e) for e in ev_all[rngG.choice(len(ev_all), size=min(300, len(ev_all)), replace=False)]]
    raw = stream_lookup(gap_keys(P, pickG))
    gp = assert_GAP(P, G, pickG, raw)
    print(f"    [GAP] {gp['n']} sampled events: derived gap == raw open / prior close to {gp['worst']:.1e}; rv to {gp['worst_rv']:.1e}; [XD] [V0] no survivor "
          f"violates ({time.time() - t0:.0f}s)")
    g = assert_G(P)
    res10, pct10 = d353_ledger(P)
    obs53 = assert_R5(P, res10, pct10)
    q7 = q7_split(P, res10)
    del res10
    print(f"    [R5] D353 reproduced ({D353_TRADES:,} trades, {obs53:+.4f} bp); Q7 split: gap-day entries {q7['gap_n']:,} vs rest {q7['rest_n']:,} ({time.time() - t0:.0f}s)")
    elig_b = elig & np.isfinite(np.asarray(P["PCT"]["rsi"]))
    F10 = V47.forward_excess_grid(P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["finT"], h=10)
    for p, q in CELLS:
        nm = cell_name(p, q)
        prim = (p, q) == PRIMARY
        sh, c_sh = cell_signal(P, p, q)
        cell = arm_report(P, sh, c_sh, 1, elig, with_groups=True, exits=EXITS)
        res = cell[PRIMARY_EXIT]["res"]
        cell["observed"] = observed_stats(res, P)
        cell["controls"] = load_controls(paths, p, q, cell["observed"])
        cell["control_C"] = control_C(V47.pnl_bp(res), np.random.default_rng([SEED, STUDY, CELLS.index((p, q)), ARM["C"]]))
        cell["interaction"] = bucket_interaction(P, res["trades"], V47.pnl_bp(res), F10, elig_b)
        drop_res(cell)
        beside = EXITS if prim else (("cap", 10),)
        nv, c_nv = novol_signal(P, p)
        arm = arm_report(P, nv, c_nv, 1, elig, with_groups=prim, exits=beside)
        mi, c_mi = mirror_signal(P, p, q)
        mirr = arm_report(P, mi, c_mi, 0, elig, with_groups=prim, exits=beside)
        drop_res(arm)
        drop_res(mirr)
        cell["no_volume"], cell["mirror"] = arm, mirr
        R[nm] = cell
        print(f"    {nm}: [HX] " + ", ".join(f"{e} {cell[e]['hx']['hedged']['worst']:.0e}/{cell[e]['hx']['unhedged']['worst']:.0e}" for e in EXIT_NAME.values())
              + f"; [REC] replay identity on {cell['rec20']['accounting']['trades']:,} trades; no-volume {arm['events']:,} events, mirror {mirr['events']:,} "
              f"({time.time() - t0:.0f}s)", flush=True)
    del F10

    # ---- print ----
    print("\n" + "=" * 160)
    print("THE NEWS-GAP SHORT -- every event taken short at the next open, no slot cap, hedged by the floored market; bp per TRADE (no-volume = the same gap "
          "with rv below the day's median, short; mirror = the volume gap UP, LONG)")
    print("=" * 160)
    print("  %-18s %-6s %7s %5s %6s %7s %7s %6s %5s | %6s %6s %6s %6s %5s | %7s %7s | %7s | %7s %7s %6s" % (
        "arm", "exit", "events", "excl", "n", "mean", "median", "t", "hold", "2c PUB", "2c PB", "hs PUB", "borrow", "HTB%", "netPUB", "netPB", "be hs/s",
        "era1", "era2", "down"))

    def row(label, ex, d, c):
        b = d.get("borrow")
        nb = d.get("net_per_trade_borrow", d["net_per_trade"])
        print("  %-18s %-6s %7s %5s %6d %+7.1f %+7.1f %+6.2f %5.1f | %6.1f %6.1f %6.1f %6s %5s | %+7.1f %+7.1f | %7.1f | %+7.1f %+7.1f %6s" % (
            label, ex, f"{c['events']:,}", c["excluded"], d["trades"], d["mean_bp"], d["median_bp"], d["t"] or 0, d["hold_mean"], d["two_c"]["PUB"], d["two_c"]["PB"],
            d["held_half"]["PUB"], ("%.1f" % b["mean_bp"]) if b else "-", ("%.2f" % (100 * b["htb_share"])) if b else "-", nb["PUB"], nb["PB"],
            d["breakeven_half_spread_bp_side"], d["era1_mean_bp"] or 0, d["era2_mean_bp"] or 0,
            ("%+.0f" % d["down_years_mean_bp"]) if d["down_years_mean_bp"] is not None else "-"))
    for nm in R:
        for e in EXIT_NAME.values():
            row(f"cell {nm}" + (" *" if nm == cell_name(*PRIMARY) and e == PRIMARY_EXIT else ""), e, R[nm][e]["per_trade"], R[nm]["counts"])
        for arm in ("no_volume", "mirror"):
            for e in EXIT_NAME.values():
                if e in R[nm][arm]:
                    row(f"  {arm} {nm}", e, R[nm][arm][e]["per_trade"], R[nm][arm]["counts"])
    print("  excl = events dropped on an ex-distribution / zero-volume / no-prior-close day; hs PUB = the held names' median PUB half-spread at entry (bp/side); "
          "netPUB/netPB = mean - 2c - borrow (short; the mirror's has no borrow); be hs/s = the held half-spread at which the net after commission and "
          "borrow is zero; era1/era2/down = mean per trade in the era halves and the down-years")
    print("\n  DEPLOYED BASE (hedged, bp per BAR), 4-crossing line (G22.costed, pre-registered for event books) and the 2-crossing line beside (cost / 2):")
    print("  %-18s %-6s %5s %5s %6s | %7s %6s %7s %7s %7s | %6s %7s %7s | %7s %6s" % ("arm", "exit", "exp%", "pos", "ent/yr", "gross", "cost4", "net4PUB", "net4PB",
                                                                                   "Sh4PUB", "cost2", "net2PUB", "net2PB", "Sh2PUB", "be4 hs"))
    for nm in R:
        for e in EXIT_NAME.values():
            d = R[nm][e]["deployed"]
            h, hb, h2, hb2 = d["PUB"]["hedged"], d["PB"]["hedged"], d["PUB"]["hedged_2x"], d["PB"]["hedged_2x"]
            print("  %-18s %-6s %5.1f %5.1f %6.0f | %+7.2f %6.2f %+7.2f %+7.2f %+7.3f | %6.2f %+7.2f %+7.2f | %+7.3f %6.1f" % (
                f"cell {nm}", e, 100 * d["exposure"], d["mean_positions_deployed"], d["entries_per_year"], h["gross_bp"], h["cost_bp"], h["net_bp"], hb["net_bp"],
                h["sharpe_net"], h2["cost_bp"], h2["net_bp"], hb2["net_bp"], h2["sharpe_net"], h["breakeven_half_spread_bp_side"] or 0))
    print("\n  CONTROLS on the primary exit (cap 10), per trade bp: A' per-name rotation within elig; B same day / same rsi bucket / defined-percentile pool; "
          "C random direction")
    print("  %-8s %5s %8s | %8s %8s %5s | %8s %8s %5s | %8s %8s %5s | %s" % ("cell", "draws", "observed", "A' p50", "A' p95", "above", "B p50", "B p95", "above",
                                                                          "C p50", "C p95", "above", "deployed net PUB: obs / A' p95 / B p95"))
    for nm in R:
        o, k, C = R[nm]["observed"], R[nm]["controls"], R[nm]["control_C"]
        if k is None:
            print("  %-8s %5s %+8.2f | %-37s | C %+8.2f %+8.2f %5s |" % (nm, "-", o["trade_mean_bp"], "A'/B NOT RUN", C["p50"], C["p95"], "yes" if C["above"] else "NO"))
            continue
        a, b = k["A_prime"]["trade_mean_bp"], k["B"]["trade_mean_bp"]
        print("  %-8s %5d %+8.2f | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+.2f / %+.2f / %+.2f" % (
            nm, k["draws"], o["trade_mean_bp"], a["p50"], a["p95"], "yes" if a["above"] else "NO", b["p50"], b["p95"], "yes" if b["above"] else "NO",
            C["p50"], C["p95"], "yes" if C["above"] else "NO", o["net_bp_PUB"], k["A_prime"]["net_bp_PUB"]["p95"], k["B"]["net_bp_PUB"]["p95"]))
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
    acc = R[pn][PRIMARY_EXIT]["accounting"]
    print(f"      check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; "
          f"trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    pr = R[pn][PRIMARY_EXIT]["per_trade"]
    for e in ("cap10", "cap20", "rec20"):
        d = R[pn][e]["per_trade"]
        b = d["borrow"]
        print(f"      primary {e}: n {d['trades']:,} mean {d['mean_bp']:+.2f} median {d['median_bp']:+.2f} t {d['t']:+.2f} hold {d['hold_mean']:.2f}; 2c PUB {d['two_c']['PUB']:.2f} "
              f"PB {d['two_c']['PB']:.2f}; held hs PUB {d['held_half']['PUB']:.2f} PB {d['held_half']['PB']:.2f} (price ${d['held_price']:.2f}); borrow {b['mean_bp']:.2f} bp "
              f"(HTB {100 * b['htb_share']:.2f}%, {b['htb_n']}); net after borrow PUB {d['net_per_trade_borrow']['PUB']:+.2f} PB {d['net_per_trade_borrow']['PB']:+.2f}; "
              f"be hs/s {d['breakeven_half_spread_bp_side']:.1f}")
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
    print("\n  STAGE 0 (data), the name's hedged forward return in bp per event (the short earns the negative):")
    print_stage0(S0)
    print(f"\n  Q7 SPLIT of D353's rev_5 bottom-decile cap-40 long ledger ({q7['trades']:,} trades; {q7['rule']}): entries on a primary-cell gap day "
          f"{q7['gap_n']:,} mean {fq(q7['gap_mean_bp'])} (median {fq(q7['gap_median_bp'])}) vs the rest {q7['rest_n']:,} mean {q7['rest_mean_bp']:+.2f}; "
          f"difference {fq(q7['diff_bp'])} bp; {q7['undefined_pct_n']} trades with an undefined gap percentile at the trigger bar")

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q = {}
    k = R[pn]["controls"]
    C = R[pn]["control_C"]
    q["Q1"] = bool(pr["mean_bp"] > 0 and k is not None and k["A_prime"]["trade_mean_bp"]["above"] and k["B"]["trade_mean_bp"]["above"] and C["above"])
    nv10 = R[pn]["no_volume"][PRIMARY_EXIT]["per_trade"]
    q["Q2"] = bool(nv10["mean_bp"] <= pr["mean_bp"] - 20.0)
    mir10 = R[pn]["mirror"][PRIMARY_EXIT]["per_trade"]
    q["Q3"] = bool(mir10["mean_bp"] > 0)
    q["Q4"] = bool(pr["net_per_trade_borrow"]["PUB"] > 0)
    q["Q5"] = bool(pr["held_half"]["PUB"] < 30.0)
    c20 = R[pn]["cap20"]["per_trade"]
    q["Q6"] = bool(c20["mean_bp"] > pr["mean_bp"])
    q["Q7"] = bool(q7["gap_mean_bp"] is not None and q7["gap_mean_bp"] <= q7["rest_mean_bp"] - 15.0)
    q["Q8"] = bool(pr["borrow"]["htb_share"] < 0.02 and pr["borrow"]["mean_bp"] < 3.0)
    q["Q9"] = bool(pr["era1_mean_bp"] is not None and pr["era2_mean_bp"] is not None and pr["era1_mean_bp"] > pr["era2_mean_bp"])
    q["check"] = bool(gp["worst"] < 1e-12 and all(v["excluded"] == v["raw"] - v["events"] for v in cnts.values()) and abs(obs53 - D353_MEAN) < 5e-5)
    print(f"\nPREDICTIONS (primary cell {pn}, cap 10, short, bp per trade unless stated)")
    print(f"  Q1 (LOAD-BEARING) mean per trade > 0 and above p95 of A', B and C: {v_(q['Q1'])} -- observed {pr['mean_bp']:+.2f} ({pr['trades']:,} trades)"
          + (f"; A' p95 {k['A_prime']['trade_mean_bp']['p95']:+.2f} (p50 {k['A_prime']['trade_mean_bp']['p50']:+.2f}), B p95 {k['B']['trade_mean_bp']['p95']:+.2f} "
             f"(p50 {k['B']['trade_mean_bp']['p50']:+.2f}) at {k['draws']} draws" if k else "; A'/B NOT RUN (falsified by absence)")
          + f"; C p95 {C['p95']:+.2f} (p50 {C['p50']:+.2f})")
    print(f"  Q2 the no-volume arm's mean at least 20 bp below the primary's: {v_(q['Q2'])} -- no-volume {nv10['mean_bp']:+.2f} ({nv10['trades']:,}) vs primary "
          f"{pr['mean_bp']:+.2f}, gap {pr['mean_bp'] - nv10['mean_bp']:+.2f}")
    print(f"  Q3 the mirror (volume gap up, long) has mean per trade > 0 at cap 10: {v_(q['Q3'])} -- {mir10['mean_bp']:+.2f} ({mir10['trades']:,} trades)")
    print(f"  Q4 (against) nets > 0 per trade after the PUB 2c and borrow, cap 10: {v_(q['Q4'])} -- mean {pr['mean_bp']:+.2f} - 2c PUB {pr['two_c']['PUB']:.2f} - borrow "
          f"{pr['borrow']['mean_bp']:.2f} = {pr['net_per_trade_borrow']['PUB']:+.2f} (PB {pr['net_per_trade_borrow']['PB']:+.2f}); be hs/s {pr['breakeven_half_spread_bp_side']:.1f}")
    print(f"  Q5 the held half-spread under PUB below 30 bp a side: {v_(q['Q5'])} -- {pr['held_half']['PUB']:.2f} bp/side (PB {pr['held_half']['PB']:.2f}; held price "
          f"${pr['held_price']:.2f})")
    print(f"  Q6 cap 20's mean per trade exceeds cap 10's: {v_(q['Q6'])} -- cap20 {c20['mean_bp']:+.2f} ({c20['trades']:,}, hold {c20['hold_mean']:.1f}) vs cap10 "
          f"{pr['mean_bp']:+.2f} (hold {pr['hold_mean']:.1f}); recovery {R[pn]['rec20']['per_trade']['mean_bp']:+.2f} (hold {R[pn]['rec20']['per_trade']['hold_mean']:.1f})")
    print(f"  Q7 D353's rev_5 entries whose trigger bar was a primary-cell gap day earn at least 15 bp less: {v_(q['Q7'])} -- gap-day {q7['gap_n']:,} "
          f"{fq(q7['gap_mean_bp'])} vs rest {q7['rest_n']:,} {q7['rest_mean_bp']:+.2f}, difference {fq(q7['diff_bp'])}")
    print(f"  Q8 HTB share below 2% and borrow below 3 bp a trade: {v_(q['Q8'])} -- HTB {100 * pr['borrow']['htb_share']:.2f}% ({pr['borrow']['htb_n']} of {pr['trades']:,}), "
          f"borrow {pr['borrow']['mean_bp']:.2f} bp")
    print(f"  Q9 era 1's mean per trade exceeds era 2's: {v_(q['Q9'])} -- era1 {pr['era1_mean_bp'] or 0:+.2f} [{pr['era1_n']}] vs era2 {pr['era2_mean_bp'] or 0:+.2f} [{pr['era2_n']}]")
    print(f"  check: the derived gap equals the raw bars' open / prior close on {gp['n']} sampled events to {gp['worst']:.1e}; the excluded ex-distribution and "
          f"zero-volume gaps are counted (primary: {cnts[f'cell {pn}']['xd']} xd, {cnts[f'cell {pn}']['v0']} v0, {cnts[f'cell {pn}']['nf']} nf of "
          f"{cnts[f'cell {pn}']['raw']:,}); the rev_5 ledger reproduces D353 ({D353_TRADES:,} trades, {obs53:+.4f}) before Q7's split: {v_(q['check'])}")
    out = dict(note="D360: the news-gap short -- a down-gap on abnormal volume in an ordinary name, four cells, three exits, every event taken short, hedged by "
                    "the floored market; the no-volume arm and the mirror beside; A', B, C on the primary exit; borrow in the net. Per-trade numbers are bp per "
                    "TRADE and never compared to per-bar numbers. Nothing is a book; nothing promoted.",
               study=STUDY, cells=[cell_name(p, q) for p, q in CELLS], primary=pn, primary_exit=PRIMARY_EXIT, exits=list(EXIT_NAME.values()),
               signal=dict(gap="OPEN[g] / CLOSE[g-1] - 1 on the split-adjusted panel bars", rv=f"VOL[g] / median(VOL[g-{VOL_WIN}..g-1])",
                           cross_section="elig[g+1] & finite gap & finite rv; V47.percentile_grid (average rank, undefined below 50 names)",
                           exclusions=f"ex-distribution day (events file amount >= {XD_MIN} x CLOSE[g-1]), zero volume, non-finite prior close",
                           kernel_score="100 - pct_gap lagged one bar (cap exits); the recovery grid for exit='invalidation' (rec20)",
                           already_held="skipped by the kernel and counted (event_accounting / the recovery replay)"),
               U=V59.U_SLOTS, x_target=X_TARGET, down_years=P["down_years"], floored_market_by_year=P["yr_ret"], m_start=P["m_start"],
               seeds=dict(A=[SEED, STUDY, "cell_index", ARM["A"], "part"], B=[SEED, STUDY, "cell_index", ARM["B"], "part"], C=[SEED, STUDY, "cell_index", ARM["C"]],
                          stage0_aprime=[SEED, STUDY, 0, 0]),
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), dividends=G["xd_counts"], G=g, counts=cnts, gap_check=gp,
               d353=dict(trades=D353_TRADES, mean_bp=obs53), q7=q7, stage0=S0, results=R, predictions=q)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['report']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--cell", metavar="P:Q", help="e.g. 2:10 -- the A'/B controls for one cell on the primary exit")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; the smoke runs pass a temp/ directory)")
    a = ap.parse_args()
    print("D360  the news-gap short -- a down-gap on abnormal volume in an ordinary name, entered short at the next open")
    paths = out_paths(a.out_dir)
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))                # what V49.event_buckets reads
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.stage0:
        stage_stage0(P, paths)
    elif a.cell:
        p, q = (int(x) for x in a.cell.split(":"))
        assert (p, q) in CELLS, f"cell must be one of {[cell_name(p_, q_) for p_, q_ in CELLS]}"
        stage_cell(P, p, q, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --stage0, --cell P:Q, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
