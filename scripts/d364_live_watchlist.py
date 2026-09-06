"""D364 -- the daily watchlist for D362's A2 arm (the two-sink gated gap-up fade), as an OPERATIONS tool.

    uv run python scripts/d364_live_watchlist.py --selftest
    uv run python scripts/d364_live_watchlist.py --verify-history
    uv run python scripts/d364_live_watchlist.py --run [--as-of YYYY-MM-DD] [--mode live|history]
    --out-dir DIR    (default data/; the smoke runs pass temp/... so that nothing under data/ is touched)

NOTHING HERE IS A RESULT and nothing here is a decision to trade. D362's A2 arm is a within-sample
confirmation with nulls; it is in no book. This file turns that arm's SIGNAL into a list a human can
execute against, and measures the one thing that separates the signal from a live list: the trigger's
dependence on tomorrow's eligibility.

R9 BINDS: not one quantity is re-derived. The gate, the trigger, the exclusions, the percentile
construction, the five sinks, the borrow rule and the features all come out of the committed runners by
import and call:
    run_d362_sink_filter  SINKS, features, hit_grids, hit_direct, feat_at, arm_signal, arm_removed,
                          arm_removed's A5 counterpart, read_export, assert_HOLDOUT_GUARD, guard_line
    run_d361_regime_gated_short  gate_pack("G2"), gate_loop, assert_GT, episodes_of, triggers, arms_of, run_short
    run_d360_news_gap_short      signal_grids (gap, rv, pct_gap, pct_rv, cs, XD/V0/NF), mirror_signal, shift,
                                 relative_volume, rv_direct
    run_d349_short_signal_controls  borrow_of (d337_borrow's htb_flags / rate_bps underneath)
    d348_prep                    prep()
The ONE line of committed code that is re-expressed here is `signal_grids`' cross-section mask, because
that function takes no mask parameter and must not be edited; [MODE-ID] holds the re-expression to
`signal_grids` BIT-IDENTICALLY on the history branch, so the swap is the only difference.

THE AS-OF BAR IS THE ENTRY BAR. The signal is computed on day g from day g's OWN bar (gap = OPEN[g] /
CLOSE[g-1] - 1, rv = VOL[g] / median(VOL[g-21..g-1])) and the position is opened SHORT at the open of
t = g + 1. So `--as-of D` means "D is today, the fixture's last complete bar is yesterday, these are the
names to short at today's open" -- which is also the export's `date_entry`, so --verify-history compares
like with like.

THE TWO ELIGIBILITY MODES -- the honest core of this tool.
`signal_grids` builds `cs[:-1] = elig[1:]`: a name enters the day-g cross-section only if it is ELIGIBLE
AT g+1, i.e. still live and above the price/liquidity floor TOMORROW. That is knowable in a backtest and
unknowable at the moment the list is produced.
    --mode history  the committed grids, unchanged. Reproduces the ledger. The default for --verify-history.
    --mode live     cs[g] = elig[g] instead: the name is live and passes the floor AS OF g (elig = finT &
                    keep with the hedge's m_start floor, so elig[g] IS finT[g] & keep[g] for g >= m_start).
                    The default for --run. Every row and the header carry live_mode_approximation.
The size of the approximation -- events the live rule ADDS and DROPS against the history rule over the
whole fixture, as counts and as a share -- is printed by [MODE] and stored in the JSON. It is not small.

WHAT --run PRINTS: the header (as-of, fixture age, deal-file pull date, mode); the STALENESS REFUSAL;
the GATE (G2 on/off at the entry bar, level_200, the episode); the STRATEGY CANDIDATES (gate on, A2
sinks applied); the EXECUTION-MEASUREMENT CANDIDATES (the ungated T2 trigger minus the A2 sinks -- NOT
strategy entries; they exist so that fills can be measured in the right kind of name while the gate is
off); and the EXITS due from data/d364_fill_log.csv. A JSON with the same content is written to --out-dir.

ASSERTIONS [K][F0][R][HOLDOUT-GUARD][GATE][TRIG][SINK][HIST][STALE][MODE][MODE-ID][6].
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import importlib.util
import io
import json
import math
import sys
import time
from collections import Counter
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


# run_d362 FIRST and alone: it installs the sys.addaudithook HOLDOUT-GUARD at its own module level, before
# it loads memo_load / d348_prep / run_d361 / run_d360, so the guard is live before any chain module opens
# a single file. Nothing above this line opens a fixture.
V62 = _load("d362r", "run_d362_sink_filter.py")
V61, EXP, PREP = V62.V61, V62.EXP, V62.PREP
V60, V59, V58, V53, V49, V47, V50 = V62.V60, V62.V59, V62.V58, V62.V53, V62.V49, V62.V47, V62.V50
EB, G22, BR = V62.EB, V62.G22, V62.BR
clean = V62.clean

STUDY = 364
GATE, TRIG, ARM = V62.GATE, V62.TRIG, V62.PRIMARY          # "G2", "T2", "A2"
CAP = V62.CAP                                              # 10
SINKS = V62.SINKS
FEATS = V62.FEATS
P_GAP, Q_RV = V61.T2_PARENT                                # (2, 10): pct_gap >= 98, pct_rv >= 90
SEED = V62.SEED
DATA = REPO / "data"
DEALS = DATA / "fixtures" / "us_shorts_daily_raw_deals.json"
COVERAGE = DATA / "d331_edgar_coverage.txt"
FILL_LOG = DATA / "d364_fill_log.csv"
D362_REPORT = DATA / "d362_sink_filter.json"
SIZE_USD = 25_000.0                                        # the sizing context the header asks for
DEAL_STALE_DAYS = 5                                        # "more than ~5 trading days older than the as-of date"
MODES = ("live", "history")
SELFTEST_TMP = REPO / "temp" / "d364_selftest"


def el(t0):
    return f"{time.time() - t0:.0f}s"


def fq(x, nd=2):
    return "-" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{nd}f}"


def fp(x, nd=2):
    return "-" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}"


# ------------------------------------------------------------------ the committed grids, memoised
_B = {}


def base_pack(P):
    """Every grid this tool reads, all of it out of the committed runners.

    Order matters: run_d360.signal_grids is called FIRST so that its ~1 GB memo is built once; the arrays
    this file needs are bound to locals, and run_d361.triggers (called by arms_of) then releases the memo
    -- the bound arrays survive, the rest (OPEN, RATIO, ANYDIV, sc, defined) is freed."""
    if _B:
        return _B
    G = V60.signal_grids(P)
    gap, rv = G["gap"], G["rv"]
    pct_gap, pct_rv, cs, bad = G["pct_gap"], G["pct_rv"], G["cs"], G["bad"]
    XD, V0, NF = G["XD"], G["V0"], G["NF"]
    del G                                                          # the memo still holds it; triggers() clears that below
    gated, off, ung, sc = V61.arms_of(P, GATE, TRIG)               # -> V61.triggers -> V60._G.clear()
    gp = V61.gate_pack(P, GATE)
    F = V62.features(P)
    H, hits = V62.hit_grids(F, P["T"], P["n"])
    _B.update(gap=gap, rv=rv, pct_gap=pct_gap, pct_rv=pct_rv, cs=cs, bad=bad, XD=XD, V0=V0, NF=NF,
              gated=gated, off=off, ung=ung, sc=sc, gp=gp, F=F, H=H, hits=hits,
              removed=V62.arm_removed(ARM, H, hits), removed_A5=V62.arm_removed("A5", H, hits),
              elig=np.asarray(P["elig"]), finT=np.asarray(P["finT"]), keep=np.asarray(P["keep"]))
    return _B


# ------------------------------------------------------------------ the two eligibility modes
_MODE = {}


def day_grids(P, B, mode):
    """The T2 (2, 10) cross-section, percentile grids and event grid under one eligibility mode.

    THE ONLY LINE THAT DIFFERS between the two branches, and the only line of run_d360.signal_grids
    re-expressed anywhere in this file:

        history   cs[:-1] = elig[1:]     the committed line: eligible AFTER the gap (tomorrow's liveness)
        live      cs      = elig         eligible AS OF g -- elig is finT & keep with elig[:m_start] = False,
                                         so elig[g] IS `finT[g] & keep[g]` for every bar the hedge covers

    Everything else is the committed construction, called not copied: the same `gap` and `rv` arrays out of
    signal_grids, V47.percentile_grid, the same (pct_gap >= 100 - p) & (pct_rv >= 100 - q) cell with
    (p, q) = run_d361.T2_PARENT, the same `bad` exclusion mask (XD | V0 | NF) and the same V60.shift to
    t = g + 1. [MODE-ID] holds the history branch to run_d360.signal_grids BIT-IDENTICALLY, which is what
    makes the live branch's difference attributable to the mask alone."""
    if mode in _MODE:
        return _MODE[mode]
    assert mode in MODES, mode
    elig, gap, rv = B["elig"], B["gap"], B["rv"]
    cs = np.zeros(gap.shape, bool)
    if mode == "history":
        cs[:-1] = elig[1:]
    else:
        cs[:] = elig
    cs &= np.isfinite(gap) & np.isfinite(rv)
    pct_gap = V47.percentile_grid(np.where(cs, gap, np.nan))
    pct_rv = V47.percentile_grid(np.where(cs, rv, np.nan))
    with np.errstate(invalid="ignore"):
        day = (pct_gap >= 100.0 - P_GAP) & (pct_rv >= 100.0 - Q_RV)
    raw = day & cs
    ev = V60.shift(raw & ~B["bad"])
    _MODE[mode] = dict(mode=mode, cs=cs, pct_gap=pct_gap, pct_rv=pct_rv, day=raw, ev=ev)
    return _MODE[mode]


def assert_MODE_ID(P, B, tag="[MODE-ID]"):
    """The history branch of day_grids reproduces run_d360.signal_grids bit-identically -- cs, pct_gap,
    pct_rv (NaN patterns included) and the resulting T2 event grid == run_d361.arms_of's ungated trigger."""
    D = day_grids(P, B, "history")
    assert np.array_equal(D["cs"], B["cs"]), f"{tag} the history cross-section differs from signal_grids"
    for k in ("pct_gap", "pct_rv"):
        assert np.array_equal(D[k], B[k], equal_nan=True), f"{tag} the history {k} differs from signal_grids"
    assert np.array_equal(D["ev"], B["ung"]), f"{tag} the history event grid differs from arms_of's ungated T2"
    return dict(cells=int(D["cs"].size), events=int(D["ev"].sum()))


def assert_MODE(P, B, tag="[MODE]"):
    """The size of the live approximation, and the one thing that MUST hold: on every day g where the two
    cross-section masks coincide name for name, the two percentile grids and the two day masks are equal.
    The counts added / dropped are reported, never asserted to be zero -- they are the measurement."""
    Dh, Dl = day_grids(P, B, "history"), day_grids(P, B, "live")
    same_g = (Dh["cs"] == Dl["cs"]).all(axis=1)
    for k in ("pct_gap", "pct_rv"):
        assert np.array_equal(Dh[k][same_g], Dl[k][same_g], equal_nan=True), f"{tag} the grids differ on a bar whose mask is identical"
    assert np.array_equal(Dh["day"][same_g], Dl["day"][same_g]), f"{tag} the day masks differ on a bar whose mask is identical"
    add = Dl["ev"] & ~Dh["ev"]
    drop = Dh["ev"] & ~Dl["ev"]
    gate = B["gp"]["gate"][:, None]
    rm = ~B["removed"]
    n_h, n_l = int(Dh["ev"].sum()), int(Dl["ev"].sum())
    n_add, n_drop = int(add.sum()), int(drop.sum())
    assert n_add >= 0 and n_drop >= 0, f"{tag} a negative count"
    out = dict(bars=int(same_g.size), bars_mask_identical=int(same_g.sum()), share_bars_identical=float(same_g.mean()),
               events_history=n_h, events_live=n_l, added=n_add, dropped=n_drop,
               added_share=n_add / n_h, dropped_share=n_drop / n_h, net=n_l - n_h,
               a2_history=int((Dh["ev"] & gate & rm).sum()), a2_live=int((Dl["ev"] & gate & rm).sum()),
               a2_added=int((add & gate & rm).sum()), a2_dropped=int((drop & gate & rm).sum()))
    out["a2_added_share"] = out["a2_added"] / max(out["a2_history"], 1)
    out["a2_dropped_share"] = out["a2_dropped"] / max(out["a2_history"], 1)
    return out


# ------------------------------------------------------------------ [GATE] [TRIG] [SINK]
def assert_GATE(P, B, t, gate=None, level=None, tag="[GATE]"):
    """run_d361.assert_GT in full (the vectorised G2 against run_d361.gate_loop -- a plain Python loop that
    never calls gate_pack -- exactly on the boolean, to 1e-12 on the level, plus the one-bar lag probe), and
    the as-of bar's own value re-read off the loop. `gate` / `level` may be perturbed copies ([6])."""
    gp = B["gp"]
    gate = gp["gate"] if gate is None else gate
    level = gp["level"] if level is None else level
    worst = V61.assert_GT(P, gp, gate=gate, level=level, tag=tag)
    lv, gl = V61.gate_loop(P, GATE)
    assert bool(gate[t]) == bool(gl[t]), f"{tag} the as-of bar's gate differs from the loop"
    assert (not np.isfinite(level[t])) or abs(float(level[t]) - float(lv[t])) < 1e-12, f"{tag} the as-of bar's level differs from the loop"
    return worst


def trig_direct(P, B, D, t):
    """[TRIG]'s second implementation: the day-g trigger set at the entry bar t, in plain Python over the
    names, straight off the grids -- never day_grids' vectorised day mask, never V60._arm, never shift."""
    g = t - 1
    cs, pg, pr, bad = D["cs"], D["pct_gap"], D["pct_rv"], B["bad"]
    out = []
    for i in range(P["n"]):
        if not bool(cs[g, i]) or bool(bad[g, i]):
            continue
        a, b = float(pg[g, i]), float(pr[g, i])
        if math.isnan(a) or math.isnan(b):
            continue
        if a >= 100.0 - P_GAP and b >= 100.0 - Q_RV:
            out.append(i)
    return sorted(out)


def assert_TRIG(P, B, D, t, ev_row=None, tag="[TRIG]"):
    """The entry bar's ungated T2 event set equals the direct recomputation, name for name. `ev_row` may be
    a perturbed copy ([6])."""
    ev = D["ev"][t] if ev_row is None else ev_row
    mine = sorted(int(i) for i in np.flatnonzero(ev))
    direct = trig_direct(P, B, D, t)
    assert mine == direct, (f"{tag} the entry bar's trigger set differs from the direct recomputation: "
                            f"{sorted(set(mine) ^ set(direct))[:10]}")
    return len(direct)


def assert_SINK(P, B, t, rows, F_override=None, tag="[SINK]"):
    """Two things. (1) LAG-STYLE: every candidate's five flags equal run_d362.hit_direct -- plain Python with
    an explicit NaN test -- at the same (t, i), and the A2 removal mask is exactly H[0] | H[1].
    (2) RIGHT-QUANTITY: the mask being applied is A2's (S1 | S2) and NOT A5's (any hit) and not S3|S4|S5;
    each of the three selects a different set on this fixture, so a mix-up cannot pass silently."""
    F = B["F"] if F_override is None else F_override
    H, hits = B["H"], B["hits"]
    for i in rows:
        d = V62.hit_direct(F, int(t), int(i))
        gr = [bool(H[q, t, i]) for q in range(len(SINKS))]
        assert d == gr, f"{tag} flags differ at ({P['dates'][t]}, {P['symbols'][i]}): grid {gr} direct {d}"
    rm = B["removed"]
    assert np.array_equal(rm, H[0] | H[1]), f"{tag} the A2 removal mask is not S1 | S2"
    a5 = B["removed_A5"]
    assert np.array_equal(a5, hits > 0) and not np.array_equal(rm, a5), f"{tag} A2's mask is A5's mask"
    tail = H[2] | H[3] | H[4]
    assert not np.array_equal(rm, tail), f"{tag} A2's mask is S3 | S4 | S5"
    return dict(checked=len(rows), a2_removed=int(rm.sum()), a5_removed=int(a5.sum()), tail_removed=int(tail.sum()))


# ------------------------------------------------------------------ staleness
def assert_STALE(as_of, last_date, rc, text, tag="[STALE]"):
    """If the as-of date is later than the fixture's last bar the run MUST exit non-zero and MUST NOT print
    a candidate list. Fed a run that did print one, this raises -- which is how [6] probes it."""
    if as_of <= last_date:
        return False
    assert rc != 0, f"{tag} as-of {as_of} is after the fixture's last bar {last_date} and the run exited 0"
    for banner in ("STRATEGY CANDIDATES", "EXECUTION-MEASUREMENT CANDIDATES"):
        assert banner not in text, f"{tag} a candidate list was printed for {as_of}, after the fixture's last bar {last_date}"
    return True


# ------------------------------------------------------------------ the deal file's pull date
def deal_pull_date():
    """`pulled_on:` from data/d331_edgar_coverage.txt (the coverage report d331_edgar_deals.py writes beside
    the deal file). None if the line is absent."""
    if not COVERAGE.exists():
        return None
    for line in COVERAGE.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
        if line.strip().startswith("pulled_on:"):
            return line.split("pulled_on:", 1)[1].split()[0]
    return None


def trading_days_between(dates, a, b):
    """Trading days from a to b. Exact (index difference) when both are bars of the fixture; otherwise
    np.busday_count, which counts Mon-Fri and knows no market holidays -- flagged wherever it is used."""
    pos = {d: i for i, d in enumerate(dates)}
    if a in pos and b in pos:
        return pos[b] - pos[a], True
    return int(np.busday_count(np.datetime64(a), np.datetime64(b))), False


# ------------------------------------------------------------------ the fill log
def read_fill_log(path=FILL_LOG):
    """(open positions, note) from data/d364_fill_log.csv, whose schema is the one its own README fixes:
    one row per FILL, with `date` the bar the order belongs to, `side` in {short_entry, cover_exit},
    `symbol` and `shares`. This file is a measurement instrument written by the principal; it is read here
    and never written.

    Partial fills share a (symbol, date, side), so shares are summed per (symbol, date). Covers are matched
    to that symbol's OLDEST uncovered entry first (FIFO) -- the reading is documented rather than inferred,
    because nothing in the log states which entry a cover closes. What comes back is one record per still-
    open (symbol, entry date) with the shares outstanding. Absent, header-only or all-covered -> ([], why).
    A log with no `side` column is read as entries only, which is the conservative reading (it can only
    over-report what is still open, never under-report)."""
    p = Path(path)
    if not p.exists():
        return [], f"{p.name} is absent"
    with open(p, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        head = rd.fieldnames or []
        rows = [r for r in rd if (r.get("symbol") or "").strip()]
    if not rows:
        return [], f"{p.name} carries a header ({', '.join(head)}) and no fills"
    assert "date" in head and "symbol" in head, f"[FILL] {p.name}: expected the README's `date` and `symbol` columns, got {head}"
    ent, cov = {}, Counter()
    for r in rows:
        s, d = r["symbol"].strip(), (r.get("date") or "").strip()
        side = (r.get("side") or "short_entry").strip() or "short_entry"
        try:
            q = float(r.get("shares") or 0.0)
        except ValueError:
            q = 0.0
        if side == "cover_exit":
            cov[s] += q
        else:
            ent[(s, d)] = ent.get((s, d), 0.0) + q
    out = []
    for s in sorted({k[0] for k in ent}):
        left = cov[s]
        for (sy, d) in sorted((k for k in ent if k[0] == s), key=lambda k: k[1]):
            q = ent[(sy, d)]
            take = min(left, q)
            left -= take
            if q - take > 0:
                out.append(dict(symbol=sy, date_entry=d, shares_open=q - take, shares_entered=q))
    note = (f"{p.name}: {len(rows)} fill(s), {len(out)} still-open position(s)" if out
            else f"{p.name}: {len(rows)} fill(s), none still open")
    return out, note


# ------------------------------------------------------------------ one name's row
def name_row(P, B, D, t, i, mode, borrow):
    g = t - 1
    CLOSE, RAW_CLOSE, VOL, HALF = P["CLOSE"], P["RAW_CLOSE"], P["VOL"], P["HALF"]
    dv = float(CLOSE[g, i]) * float(VOL[g, i])
    flags = [bool(B["H"][q, t, i]) for q in range(len(SINKS))]
    sinks = []
    for q, (nm, f, op, th) in enumerate(SINKS):
        sinks.append(dict(sink=nm, feature=f, op=op, threshold=th, value=V62.feat_at(B["F"], f, t, i), hit=flags[q]))
    return dict(symbol=P["symbols"][i], row=int(i), bar_entry=int(t), date_entry=P["dates"][t],
                bar_g=int(g), date_g=P["dates"][g],
                gap_pct=100.0 * float(B["gap"][g, i]), rv=float(B["rv"][g, i]),
                pct_gap=float(D["pct_gap"][g, i]), pct_rv=float(D["pct_rv"][g, i]),
                sinks=sinks, hits=int(B["hits"][t, i]), removed_by_A2=bool(B["removed"][t, i]),
                half_spread_PUB_bp=float(HALF["PUB"][t, i]), half_spread_PB_bp=float(HALF["PB"][t, i]),
                as_traded_close=float(RAW_CLOSE[g, i]), adj_close=float(CLOSE[g, i]), dollar_volume=dv,
                htb=bool(borrow["htb"][i]), borrow_rate_bp_annual=float(borrow["rate"][i]),
                position_share_of_dollar_volume=(SIZE_USD / dv if np.isfinite(dv) and dv > 0 else None),
                position_usd=SIZE_USD, gate_on=bool(B["gp"]["gate"][t]),
                live_mode_approximation=(mode == "live"))


def borrow_at(P, t, rows):
    """d337's gc_htb rule through run_d349.borrow_of, on (row, t, CAP, 0, short) tuples -- exactly how the
    D361 export prices a never-taken row."""
    htb, rate = {}, {}
    if rows:
        tuples = [(int(i), int(t), CAP, 0.0, 1) for i in rows]
        pt, hf, rt = V49.borrow_of(P, tuples)
        for j, i in enumerate(rows):
            htb[int(i)] = bool(hf[j])
            rate[int(i)] = float(rt[j])
    return dict(htb=htb, rate=rate)


def print_rows(rows, label):
    if not rows:
        print(f"    (none)")
        return
    print("    %-8s %8s %7s %7s %7s | %-19s | %7s %7s | %9s %10s %4s %8s" % (
        "symbol", "gap %", "rv", "pct_gap", "pct_rv", "S1 S2 S3 S4 S5", "hsPUB", "hsPB", "close $", "$vol", "HTB", "$25k/DV"))
    for r in rows:
        fl = " ".join(("HIT" if s["hit"] else " . ") for s in r["sinks"])
        sh = r["position_share_of_dollar_volume"]
        print("    %-8s %+8.2f %7.2f %7.2f %7.2f | %-19s | %7s %7s | %9s %10s %4s %8s" % (
            r["symbol"], r["gap_pct"], r["rv"], r["pct_gap"], r["pct_rv"], fl,
            fp(r["half_spread_PUB_bp"], 1), fp(r["half_spread_PB_bp"], 1), fp(r["as_traded_close"], 2),
            (f"{r['dollar_volume'] / 1e6:,.1f}M" if np.isfinite(r["dollar_volume"]) else "-"),
            "yes" if r["htb"] else "no", (f"{100 * sh:.3f}%" if sh is not None else "-")))
        print("        " + " | ".join(f"{s['sink']} {s['feature']} {fp(s['value'], 2)} {s['op']} {s['threshold']}"
                                      + (" HIT" if s["hit"] else "") for s in r["sinks"]))


# ------------------------------------------------------------------ the run stage
def run_watchlist(P, as_of, mode, out_dir, write=True, verbose=True, t0=None):
    """Returns (rc, payload). rc != 0 and NO candidate list on a stale or non-bar as-of date."""
    t0 = P["t0"] if t0 is None else t0
    dates, symbols = P["dates"], P["symbols"]
    last_date = dates[-1]
    pos = {d: i for i, d in enumerate(dates)}
    print("\n" + "=" * 150)
    print(f"D364 WATCHLIST -- D362's A2 arm (G2 gate x T2 gap-up fade, short at the open, cap {CAP} bars, "
          f"minus the S1 | S2 sinks). NOT A BOOK; A2 is a within-sample arm with nulls, in no book.")
    print("=" * 150)
    # ---- 1. header
    age, exact = trading_days_between(dates, last_date, as_of)
    print(f"  as-of (ENTRY) date      {as_of}   -- the signal is day g = the previous bar; the position is opened SHORT at the OPEN of {as_of}")
    print(f"  fixture's last bar      {last_date}   ({abs(age)} trading day(s) {'before' if age > 0 else 'after' if age < 0 else 'from'} the as-of date"
          + ("; exact, both are bars of the fixture)" if exact else "; np.busday_count -- Mon-Fri, market holidays NOT modelled)"))
    pull = deal_pull_date()
    deal_note = None
    if pull is None:
        deal_note = f"{COVERAGE.name} carries no pulled_on line"
        print(f"  deal file               {DEALS.name}: pull date UNKNOWN ({deal_note})")
    else:
        d_age, d_exact = trading_days_between(dates, pull, as_of)
        stale = d_age > DEAL_STALE_DAYS
        rel = (f"{d_age} trading day(s) BEFORE the as-of date" if d_age > 0 else
               f"{-d_age} trading day(s) AFTER the as-of date -- the pull is newer than the bar, nothing to refresh" if d_age < 0 else
               "the same day as the as-of date")
        print(f"  deal file               {DEALS.name} pulled {pull} ({rel}"
              + ("; exact)" if d_exact else "; np.busday_count, market holidays NOT modelled)"))
        if stale:
            deal_note = f"the deal pull is {d_age} trading days older than the as-of date (> {DEAL_STALE_DAYS})"
            print(f"     ** WARNING: {deal_note}. The F0 deal-filter mask and the HTB flag are computed off it. "
                  f"Refresh with `uv run python scripts/d331_edgar_deals.py` (~99 s warm) before trading this list.")
    print(f"  eligibility mode        {mode.upper()} -- " + (
        "cs[g] = elig[g], the name is live and passes the floor AS OF g. The committed trigger requires elig[g+1] "
        "(tomorrow's liveness), which is unknowable now; every row below carries live_mode_approximation = true."
        if mode == "live" else
        "cs[g] = elig[g+1], the COMMITTED rule -- the name must still be eligible at g+1. Reproduces the ledger; "
        "not computable before the g+1 bar exists."))
    print(f"  half-spread caveat      half_spread_PUB_bp is the lagged cs_spread score at t-1 and IS knowable now; "
          f"half_spread_PB_bp is Corwin-Schultz on bars t and t+1 (d285_spread_estimate.corwin_schultz writes the pair "
          f"estimate at the FIRST bar) and is NOT knowable before the close of t+1 -- printed for comparability with the record, not for use.")

    # ---- 2. staleness refusal
    if as_of > last_date:
        print(f"\n  STALENESS REFUSAL")
        print(f"    The fixture's last bar is {last_date}. It cannot answer for {as_of}: there is no bar at that date, so there is")
        print(f"    no gate value, no cross-section and no trigger for it. NO CANDIDATE LIST IS EMITTED.")
        print(f"    Refresh path: `uv run python scripts/fetch_short_universe.py` re-pulls data/fixtures/us_shorts_daily_raw*.")
        print(f"    That INVALIDATES the d348_prep cache key (it hashes the fixture's size and mtime) -- every stage rebuilds --")
        print(f"    and it invalidates every stored [ID]: D361's 3,977-trade / +42.3296 bp gated ledger and D362's A2 arm are")
        print(f"    identities against THIS fixture and must be re-established on the new one before any list is trusted.")
        print(f"    Refresh the deal file too (`scripts/d331_edgar_deals.py`, ~99 s warm): the F0 mask and the HTB flag read it.")
        print(f"\n  REFUSED (exit 2)  {PREP.rss_line()}")
        return 2, dict(as_of=as_of, refused="stale", last_bar=last_date)
    if as_of not in pos:
        print(f"\n  NOT A TRADING BAR")
        print(f"    {as_of} is not a bar of the fixture (weekend, holiday, or a halt) although it is not after the last bar")
        print(f"    {last_date}. There is no entry bar to build a list for. NO CANDIDATE LIST IS EMITTED.")
        print(f"\n  REFUSED (exit 3)  {PREP.rss_line()}")
        return 3, dict(as_of=as_of, refused="not_a_bar", last_bar=last_date)
    t = pos[as_of]
    if t < 1:
        print("\n  NO PRIOR BAR: the as-of bar is the first bar of the fixture; the signal needs day g = t - 1.")
        return 4, dict(as_of=as_of, refused="no_prior_bar")

    B = base_pack(P)
    D = day_grids(P, B, mode)
    gp = B["gp"]

    # ---- 3. gate
    on = bool(gp["gate"][t])
    lvl = float(gp["level"][t])
    print(f"\n  GATE {GATE} at the entry bar {as_of} (index {t}): {'ON' if on else 'OFF'}"
          + (f"   [gate undefined before {P['dates'][gp['d0']]}]" if not bool(gp["defined"][t]) else ""))
    print(f"    level_200 = index[t-1] / mean(index[t-200..t-1]) - 1 = {fq(lvl, 6)}   (ON when the index is BELOW its 200-bar mean, i.e. level < 0)")
    eps = gp["episodes"]
    gate_block = dict(on=on, level_200=(lvl if np.isfinite(lvl) else None), defined=bool(gp["defined"][t]))
    if on:
        k = next(j for j, (s, e) in enumerate(eps) if s <= t <= e)
        s, e = eps[k]
        gate_block.update(episode_index=k, episode_start=P["dates"][s], episode_length_so_far=t - s + 1,
                          episode_length_full=e - s + 1)
        print(f"    episode {k + 1} of {len(eps)} started {P['dates'][s]}; {t - s + 1} bar(s) so far "
              f"(the fixture shows this episode running to {P['dates'][e]}, {e - s + 1} bars in all)")
    else:
        prior = [e for s, e in eps if e < t]
        if prior:
            last_on = max(prior)
            gate_block.update(bars_since_last_on=t - last_on, last_on_date=P["dates"][last_on])
            print(f"    last ON {t - last_on} bar(s) ago, on {P['dates'][last_on]}")
        else:
            gate_block.update(bars_since_last_on=None, last_on_date=None)
            print(f"    the gate has never been on before this bar")
        print(f"    ** THE STRATEGY HAS NO ENTRIES TODAY. The gate is OFF, so A2 takes nothing. The list below is for")
        print(f"       EXECUTION MEASUREMENT ONLY -- it exists so that fills, spreads and borrow can be measured in the")
        print(f"       right kind of name while the strategy is flat. Trading it is not the strategy.")

    ev_row = D["ev"][t]
    n_trig = assert_TRIG(P, B, D, t)
    strat_rows = sorted(int(i) for i in np.flatnonzero(ev_row & (~B["removed"][t]))) if on else []
    exec_rows = sorted(int(i) for i in np.flatnonzero(ev_row & (~B["removed"][t])))
    all_rows = sorted(set(strat_rows) | set(exec_rows))
    assert_GATE(P, B, t)
    sk = assert_SINK(P, B, t, all_rows)
    bor = borrow_at(P, t, all_rows)
    S = [name_row(P, B, D, t, i, mode, bor) for i in strat_rows]
    E = [name_row(P, B, D, t, i, mode, bor) for i in exec_rows]
    for r in E:
        r["is_strategy_candidate"] = r["row"] in set(strat_rows)

    # ---- 4. strategy candidates
    print(f"\n  STRATEGY CANDIDATES -- gate {'ON' if on else 'OFF'}, A2 sinks applied ({len(S)} name(s)); short at the OPEN of {as_of}, cover at the close {CAP} bars later")
    if not on:
        print(f"    (none: the gate is off. A2's signal is `gated & ~(S1 | S2)` and `gated` is empty on a gate-off bar.)")
    else:
        print_rows(S, "strategy")

    # ---- 5. execution-measurement candidates
    print(f"\n  EXECUTION-MEASUREMENT CANDIDATES -- the UNGATED T2 trigger for the same day minus the A2 sinks ({len(E)} of {int(ev_row.sum())} raw T2 events)")
    print(f"    ** THIS LIST IS NOT A LIST OF STRATEGY ENTRIES.** It is the same KIND of name the strategy trades, listed so that")
    print(f"       fills, realised spread and borrow can be measured while the gate is off. " + (
        "The gate is ON today, so every T2 event is also a gated one and this list COINCIDES with the strategy list above "
        "(is_strategy_candidate = true in the JSON) -- that is construction, not agreement." if on else
        "The gate is OFF today, so NONE of these is a strategy entry."))
    print_rows(E, "execution")

    # ---- 6. exits
    log_rows, log_note = read_fill_log()
    print(f"\n  EXITS due at today's close ({log_note})")
    due, other = [], []
    if log_rows:
        for r in log_rows:
            de = r["date_entry"]
            e0 = pos.get(de)
            rec = dict(r, bar_entry=e0, bars_held=(t - e0 if e0 is not None else None))
            (due if (e0 is not None and t - e0 == CAP) else other).append(rec)
        if due:
            for r in due:
                print(f"    COVER {r['symbol']:8s} entered {r['date_entry']} (bar {r['bar_entry']}), {r['bars_held']} bars held == the cap, "
                      f"{r['shares_open']:.0f} share(s) open: buy to cover at today's CLOSE")
        else:
            print(f"    (no open position is exactly {CAP} bars old today)")
        for r in other:
            if r["bars_held"] is None:
                print(f"    ?     {r['symbol']:8s} entered {r['date_entry']}: that date is not a bar of the fixture -- cannot age it")
            elif r["bars_held"] < CAP:
                print(f"    hold  {r['symbol']:8s} entered {r['date_entry']}, {r['bars_held']} of {CAP} bars held ({r['shares_open']:.0f} open)")
            else:
                print(f"    LATE  {r['symbol']:8s} entered {r['date_entry']}, {r['bars_held']} bars held -- PAST the {CAP}-bar cap ({r['shares_open']:.0f} open)")
    else:
        print(f"    no open positions logged")

    # ---- the JSON
    md = assert_MODE(P, B)
    payload = dict(
        study=STUDY, tool="d364_live_watchlist", arm=ARM, cell=V61.cell_name(GATE, TRIG), cap=CAP,
        note=("D362's A2 arm as a daily list. A2 is a WITHIN-SAMPLE arm with nulls and is in no book; this file is an "
              "operations aid, not a result and not a decision to trade."),
        as_of=as_of, bar_entry=t, mode=mode, live_mode_approximation=(mode == "live"),
        fixture_last_bar=last_date, fixture_age_trading_days=abs(age), fixture_age_exact=exact,
        deal_file=str(DEALS), deal_pull_date=pull, deal_warning=deal_note,
        gate=dict(gate_block, name=GATE, window=B["gp"]["w"]), n_raw_t2_events=int(ev_row.sum()),
        strategy_candidates=S, execution_measurement_candidates=E,
        exits_due=due, exits_other=other, fill_log=str(FILL_LOG), fill_log_note=log_note,
        mode_difference=md, sinks=[dict(name=n, feature=f, op=o, threshold=th) for n, f, o, th in SINKS],
        sink_check=sk, half_spread_note=("PUB is the lagged cs_spread score at t-1 and is knowable at the as-of open; "
                                         "PB is Corwin-Schultz over bars t and t+1 and is NOT"),
        guard=V62.guard_line(), rss=PREP.rss_line())
    if write:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"d364_watchlist_{as_of}.json"
        f.write_text(json.dumps(clean(payload), indent=1))
        print(f"\n  wrote {f}")
    print(f"  live-vs-history: the live rule adds {md['added']:,} and drops {md['dropped']:,} of the history rule's "
          f"{md['events_history']:,} T2 events ({100 * md['added_share']:.2f}% / {100 * md['dropped_share']:.2f}%); "
          f"on the A2 arm +{md['a2_added']:,} / -{md['a2_dropped']:,} of {md['a2_history']:,}")
    print(f"  {PREP.rss_line()}  ({el(t0)})")
    return 0, payload


# ------------------------------------------------------------------ [HIST]
_EXP = {}


def export_sets(P):
    """The D361 export's own columns -> the three per-date sets, memoised.
        T2 events    excluded_reason == ''                                (the 20,621 the runner traded)
        G2 gated     T2 & G2_on == 1                                      (D361's cell, 4,574 events)
        A2           gated & ~(S1 | S2), the flags recomputed from the export's OWN feature columns under
                     the pre-registration's fixed thresholds, exactly as run_d362.assert_RD does it
        exec         T2 & ~(S1 | S2)                                      (the ungated list this tool prints)
    The symbol comes off the export's `row` column through P['symbols'] -- run_d362.read_export carries the
    identity columns `row` and `bar_entry`, so no second read of the CSV is needed."""
    if _EXP:
        return _EXP
    C = V62.read_export()
    with np.errstate(invalid="ignore"):
        Hc = np.array([(C[f] >= th) if op == ">=" else (C[f] <= th) for _nm, f, op, th in SINKS])
    s12 = Hc[0] | Hc[1]
    t2 = C["excluded_reason"] == ""
    g2 = t2 & (C["G2_on"] == 1)
    _EXP.update(C=C, s12=s12, t2=t2, g2=g2, a2=g2 & ~s12, execu=t2 & ~s12, taken_G2=C["taken_G2"] == 1,
                rows=C["row"].astype(int), bars=C["bar_entry"].astype(int), file=C["_file"])
    return _EXP


def export_symbols(P, mask, t):
    X = export_sets(P)
    sel = mask & (X["bars"] == t)
    return set(P["symbols"][r] for r in X["rows"][sel])


def pick_hist_dates(P, B, n_on, n_off):
    """Deterministic: the gate-ON bars carrying at least one A2 event and the gate-OFF bars carrying at
    least one SURVIVING execution-measurement candidate (an ungated T2 event that the A2 sinks do not
    remove), each sampled at even index spacing so the picks span the whole fixture. The gate-OFF bars are
    chosen on the surviving count, not the raw T2 count, so that the exec-list assertion compares a
    NON-EMPTY set on the very bars where the strategy list must be empty -- a gate-off bar whose two raw
    events both hit S1 | S2 would make both sides of the comparison trivially empty."""
    D = day_grids(P, B, "history")
    gp = B["gp"]
    a2 = D["ev"] & gp["gate"][:, None] & ~B["removed"]
    ex = D["ev"] & ~B["removed"]
    on = np.flatnonzero(gp["gate"] & (a2.sum(axis=1) > 0))
    off = np.flatnonzero(gp["defined"] & ~gp["gate"] & (ex.sum(axis=1) > 0))
    take = lambda a, k: [int(a[j]) for j in np.unique(np.linspace(0, a.size - 1, k).round().astype(int))] if a.size else []
    return take(on, n_on), take(off, n_off)


def stage_verify_history(P, n_on=5, n_off=3, quiet=False, t0=None):
    """[HIST]: the watchlist's own lists, in HISTORY mode, against the committed export -- symbol set for
    symbol set, on gate-ON dates with known A2 entries and on gate-OFF dates."""
    t0 = P["t0"] if t0 is None else t0
    B = base_pack(P)
    X = export_sets(P)
    D = day_grids(P, B, "history")
    rep = json.loads(D362_REPORT.read_text())
    stored_a2 = rep["results"]["A2"]["events"]
    stored_gated = rep["base"]["events"]
    assert [dict(name=n, feature=f, op=o, threshold=th) for n, f, o, th in SINKS] == rep["sinks"], "[HIST] the sinks differ from data/d362_sink_filter.json"
    n_a2, n_g2 = int(X["a2"].sum()), int(X["g2"].sum())
    assert n_g2 == stored_gated, f"[HIST] the export's gated rows {n_g2:,} != d362_sink_filter.json's base events {stored_gated:,}"
    assert n_a2 == stored_a2, f"[HIST] the export's A2 rows {n_a2:,} != d362_sink_filter.json's A2 events {stored_a2:,}"
    # the grid's own A2 signal must equal the export's A2 row set, name for name, over the WHOLE fixture
    a2_grid = D["ev"] & B["gp"]["gate"][:, None] & ~B["removed"]
    assert int(a2_grid.sum()) == n_a2, f"[HIST] the grid's A2 events {int(a2_grid.sum()):,} != the export's {n_a2:,}"
    gt, gi = np.nonzero(a2_grid)
    assert set(zip(gt.tolist(), gi.tolist())) == set(zip(X["bars"][X["a2"]].tolist(), X["rows"][X["a2"]].tolist())), \
        "[HIST] the grid's A2 (bar, row) set differs from the export's"
    # the A2 LEDGER, so that "candidates" and "entries" are never confused
    a2_res = V61.run_short(P, np.ascontiguousarray(a2_grid), B["sc"], "cap", CAP)
    ent = {}
    for r, e0, _a, _p, _s in a2_res["trades"]:
        ent.setdefault(int(e0), set()).add(P["symbols"][int(r)])
    ons, offs = pick_hist_dates(P, B, n_on, n_off)
    if not quiet:
        print("\n[HIST]  the watchlist in HISTORY mode against data/d361_trades_gap_up_fade.csv and data/d362_sink_filter.json")
        print(f"[HIST]  export {X['file']}: {int(X['t2'].sum()):,} T2 events, {n_g2:,} G2-gated (== d362's base {stored_gated:,}), "
              f"{n_a2:,} A2 (== d362's A2 {stored_a2:,}); the grid's A2 (bar, row) set is identical to the export's")
        print(f"[HIST]  gate-ON dates with A2 entries: {len(ons)}; gate-OFF dates with T2 events: {len(offs)}")
        print("[HIST]  %-12s %5s | %8s %8s %8s | %8s %8s %8s | %6s" % ("date", "gate", "strat_x", "strat_a", "ok", "exec_x", "exec_a", "ok", "led_ent"))
    out = []
    bad = []
    for t in ons + offs:
        on = bool(B["gp"]["gate"][t])
        d = P["dates"][t]
        row = D["ev"][t] & ~B["removed"][t]
        actual_exec = set(P["symbols"][i] for i in np.flatnonzero(row))
        actual_strat = actual_exec if on else set()
        want_strat = export_symbols(P, X["a2"], t) if on else set()
        want_exec = export_symbols(P, X["execu"], t)
        raw_t2 = len(export_symbols(P, X["t2"], t))
        ok_s, ok_e = actual_strat == want_strat, actual_exec == want_exec
        if on:
            assert want_strat, f"[HIST] {d} was picked as a gate-ON date with A2 entries and the export has none"
        else:
            assert not want_strat and not actual_strat, f"[HIST] {d}: the gate is off and the strategy list is not empty"
        rec = dict(date=d, bar=t, gate_on=on, expected_strategy=len(want_strat), actual_strategy=len(actual_strat),
                   strategy_ok=ok_s, expected_exec=len(want_exec), actual_exec=len(actual_exec), exec_ok=ok_e,
                   raw_t2_events=raw_t2, ledger_entries=len(ent.get(t, set())),
                   strategy_symbols=sorted(actual_strat), exec_symbols=sorted(actual_exec))
        if not ok_s:
            rec["strategy_mismatch"] = dict(only_watchlist=sorted(actual_strat - want_strat), only_export=sorted(want_strat - actual_strat))
            bad.append(("strategy", d))
        if not ok_e:
            rec["exec_mismatch"] = dict(only_watchlist=sorted(actual_exec - want_exec), only_export=sorted(want_exec - actual_exec))
            bad.append(("exec", d))
        assert ent.get(t, set()) <= actual_strat or not on, f"[HIST] {d}: an A2 ledger entry is not on the strategy list"
        out.append(rec)
        if not quiet:
            print("[HIST]  %-12s %5s | %8d %8d %8s | %8d %8d %8s | %6d" % (
                d, "ON" if on else "off", len(want_strat), len(actual_strat), "OK" if ok_s else "MISMATCH",
                len(want_exec), len(actual_exec), "OK" if ok_e else "MISMATCH", len(ent.get(t, set()))))
            if not ok_s:
                print(f"[HIST]      strategy only-watchlist {rec['strategy_mismatch']['only_watchlist']} only-export {rec['strategy_mismatch']['only_export']}")
            if not ok_e:
                print(f"[HIST]      exec     only-watchlist {rec['exec_mismatch']['only_watchlist']} only-export {rec['exec_mismatch']['only_export']}")
    assert not bad, f"[HIST] mismatches: {bad}"
    if not quiet:
        print(f"[HIST]  strat_x / exec_x are the EXPORT's counts, strat_a / exec_a the watchlist's; led_ent is how many of the "
              f"strategy candidates the A2 kernel actually ENTERED that bar (the rest were names it already held -- a candidate is a")
        print(f"[HIST]  signal, an entry is what the slot-free kernel did with it; every entry is on the list, never the reverse).")
        print(f"[HIST]  {len(ons)} gate-ON dates and {len(offs)} gate-OFF dates: strategy sets exact, exec sets exact, "
              f"gate-OFF strategy lists empty. ({el(t0)})")
    return dict(dates=out, gate_on_dates=len(ons), gate_off_dates=len(offs), export_file=X["file"],
                export_t2=int(X["t2"].sum()), export_gated=n_g2, export_a2=n_a2, stored_a2=stored_a2, stored_gated=stored_gated,
                ledger_trades=len(a2_res["trades"]))


# ------------------------------------------------------------------ selftest
def stage_selftest(P, out_dir):
    t0 = time.time()
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    print("\nASSERTIONS")
    print(f"    [K] [F0] [R] via d348_prep (cache {'HIT' if P['cache_hit'] else 'BUILD'} {P['cache_key']}); "
          f"the panel is {P['T']:,} bars x {P['n']:,} names, {P['dates'][0]} .. {P['dates'][-1]}")
    print(f"    [HOLDOUT-GUARD] {V62.assert_HOLDOUT_GUARD()}; run_d362 was imported FIRST so the hook was installed before "
          f"d348_prep / run_d361 / run_d360 opened anything ({el(t0)})")
    B = base_pack(P)
    T, n = P["T"], P["n"]
    t = T - 1                                                       # the as-of bar of the default --run
    as_of, last_date = P["dates"][t], P["dates"][-1]
    # [MODE-ID] first: it is what licenses everything the live branch says
    mid = assert_MODE_ID(P, B)
    print(f"    [MODE-ID] day_grids(mode='history') reproduces run_d360.signal_grids BIT-IDENTICALLY over all {mid['cells']:,} "
          f"cells -- cs, pct_gap and pct_rv (NaN patterns included) -- and its shifted event grid == run_d361.arms_of's ungated "
          f"T2 ({mid['events']:,} events) exactly; the ONLY line that differs in the live branch is the cross-section mask ({el(t0)})")
    md = assert_MODE(P, B)
    print(f"    [MODE] the live rule (cs[g] = elig[g]) vs the history rule (cs[g] = elig[g+1]): ADDS {md['added']:,} and DROPS "
          f"{md['dropped']:,} of the history rule's {md['events_history']:,} T2 events ({100 * md['added_share']:.2f}% / "
          f"{100 * md['dropped_share']:.2f}%; net {md['net']:+,}); on the A2 arm +{md['a2_added']:,} / -{md['a2_dropped']:,} of "
          f"{md['a2_history']:,} ({100 * md['a2_added_share']:.2f}% / {100 * md['a2_dropped_share']:.2f}%); both counts non-negative; "
          f"the two masks are identical on {md['bars_mask_identical']:,} of {md['bars']:,} bars and the grids agree exactly there ({el(t0)})")
    D = day_grids(P, B, "live")
    Dh = day_grids(P, B, "history")
    worst = assert_GATE(P, B, t)
    gp = B["gp"]
    print(f"    [GATE] run_d361.assert_GT: the vectorised {GATE} equals run_d361.gate_loop (a plain Python loop, no numpy window, "
          f"no cumprod) EXACTLY on the boolean and to {worst:.0e} on the level over all {gp['Td']:,} defined bars, and is lagged one "
          f"bar (perturbing m_f[t] leaves level[t] and moves level[t+1]); at the as-of bar {as_of} the gate is "
          f"{'ON' if gp['gate'][t] else 'OFF'}, level_200 {fq(float(gp['level'][t]), 6)}, and equals the loop's value there")
    nt = assert_TRIG(P, B, D, t)
    nth = assert_TRIG(P, B, Dh, t)
    print(f"    [TRIG] the entry bar {as_of}'s ungated T2 set equals a direct per-name recomputation from the grids (cs, pct_gap >= "
          f"{100 - P_GAP}, pct_rv >= {100 - Q_RV}, not excluded), never the vectorised day mask: {nt} name(s) in live mode, {nth} in "
          f"history mode; on a random 40 further bars too")
    rng = np.random.default_rng([SEED, STUDY, 1])
    for tt in rng.choice(np.arange(1, T), size=40, replace=False):
        assert_TRIG(P, B, D, int(tt))
        assert_TRIG(P, B, Dh, int(tt))
    rows = sorted(int(i) for i in np.flatnonzero(D["ev"][t] & ~B["removed"][t]))
    probe = rows or sorted(int(i) for i in np.flatnonzero(D["ev"][t]))
    if not probe:                                                   # the as-of bar may carry no event at all
        fin = np.isfinite(np.asarray(B["F"][SINKS[0][1]])[t])
        probe = sorted(int(i) for i in np.flatnonzero(fin))[:5]
    assert probe, "[SINK] no name with a defined feature at the as-of bar to probe"
    sk = assert_SINK(P, B, t, probe)
    print(f"    [SINK] the five flags equal run_d362.hit_direct (plain Python, explicit NaN test) at every candidate of the as-of bar "
          f"({sk['checked']} name(s)); the applied mask IS A2's S1 | S2 ({sk['a2_removed']:,} name-bars) and is NOT A5's any-hit "
          f"({sk['a5_removed']:,}) nor S3 | S4 | S5 ({sk['tail_removed']:,}) -- the right-quantity check")
    hist = stage_verify_history(P, n_on=2, n_off=1, quiet=True, t0=t0)
    print(f"    [HIST] on a small set ({hist['gate_on_dates']} gate-ON, {hist['gate_off_dates']} gate-OFF) the strategy and exec symbol "
          f"sets equal the export's exactly and the gate-OFF strategy lists are empty; the export's {hist['export_a2']:,} A2 rows == "
          f"d362_sink_filter.json's {hist['stored_a2']:,} and the grid's A2 (bar, row) set is identical to it ({el(t0)})")
    # [STALE]
    future = (dt.date.fromisoformat(last_date) + dt.timedelta(days=1)).isoformat()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_f, _pf = run_watchlist(P, future, "live", SELFTEST_TMP, write=False, t0=t0)
    text_f = buf.getvalue()
    assert_STALE(future, last_date, rc_f, text_f)
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc_g, pg = run_watchlist(P, as_of, "live", SELFTEST_TMP, write=False, t0=t0)
    text_g = buf2.getvalue()
    assert rc_g == 0 and "STRATEGY CANDIDATES" in text_g, "[STALE] the in-fixture run did not produce a list"
    print(f"    [STALE] --as-of {future} (one day past the fixture's last bar {last_date}) exits {rc_f} and prints neither "
          f"'STRATEGY CANDIDATES' nor 'EXECUTION-MEASUREMENT CANDIDATES'; --as-of {as_of} exits 0 and does print them")
    # [6]
    broke = []
    try:                                                            # [GATE] on a flipped gate boolean at the as-of bar
        g6 = gp["gate"].copy()
        g6[t] = not g6[t]
        assert_GATE(P, B, t, gate=g6)
    except AssertionError as e:
        assert "[GATE]" in str(e) or "[GT]" in str(e), str(e)
        broke.append("GATE")
    try:                                                            # [TRIG] on an event grid row with one name flipped in
        e6 = D["ev"][t].copy()
        e6[int(np.flatnonzero(~e6)[0])] = True
        assert_TRIG(P, B, D, t, ev_row=e6)
    except AssertionError as e:
        assert "[TRIG]" in str(e)
        broke.append("TRIG")
    try:                                                            # [SINK] on a perturbed feature (one candidate's pcto moved past its threshold)
        F6 = dict(B["F"])
        f0 = SINKS[0][1]
        F6[f0] = B["F"][f0].copy()
        i6 = probe[0]
        F6[f0][t, i6] = SINKS[0][3] + (1.0 if not B["H"][0, t, i6] else -1.0) * 1.0
        assert_SINK(P, B, t, probe, F_override=F6)
    except AssertionError as e:
        assert "[SINK]" in str(e)
        broke.append("SINK")
    try:                                                            # [STALE] fed a run that DID print a list for a future date
        assert_STALE(future, last_date, 0, text_g)
    except AssertionError as e:
        assert "[STALE]" in str(e)
        broke.append("STALE")
    assert broke == ["GATE", "TRIG", "SINK", "STALE"], f"[6] raised: {broke}"
    print(f"    [6] [GATE] raises on a flipped gate boolean at the as-of bar; [TRIG] raises on an event row with one extra name; "
          f"[SINK] raises on a feature moved 1.0 across its threshold on one candidate; [STALE] raises when handed a rc = 0 run that "
          f"printed a candidate list for a date after the fixture's last bar")
    (SELFTEST_TMP / "d364_selftest_summary.json").write_text(json.dumps(clean(dict(
        mode_id=mid, mode=md, gate_worst=worst, sink=sk, hist=hist, stale=dict(future=future, rc=rc_f),
        as_of=as_of, guard=V62.guard_line(), rss=PREP.rss_line())), indent=1))
    print(f"\nOK  assertions pass  ({el(t0)})  {PREP.rss_line()}")


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify-history", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD; the ENTRY bar. Default: the fixture's last bar.")
    ap.add_argument("--mode", choices=MODES, default=None, help="live (default for --run) | history (default for --verify-history)")
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D364  the daily watchlist for D362's A2 arm -- the two-sink gated gap-up fade, as an operations tool. "
          "Nothing here is a result and nothing here is a decision to trade.")
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.as_of is not None:
        dt.date.fromisoformat(a.as_of)                              # a bad date is a loud failure, not a silent one
    if a.selftest:
        stage_selftest(P, a.out_dir)
        return 0
    if a.verify_history:
        mode = a.mode or "history"
        assert mode == "history", "--verify-history is a HISTORY-mode check: the live rule does not reproduce the ledger, by construction"
        stage_verify_history(P)
        print(f"\nOK  [HIST] passes  {PREP.rss_line()}")
        return 0
    if a.run:
        as_of = a.as_of or P["dates"][-1]
        rc, _p = run_watchlist(P, as_of, a.mode or "live", a.out_dir)
        return rc
    ap.error("one of --selftest, --verify-history, --run")


if __name__ == "__main__":
    raise SystemExit(main())
