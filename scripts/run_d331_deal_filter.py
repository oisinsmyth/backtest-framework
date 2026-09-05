"""D331 -- the deal filter: an EVENT-driven exclusion for pinned takeover targets.

    uv run python scripts/run_d331_deal_filter.py

PRE-REGISTERED AT `56863e3`, committed before this file existed (R8).

THE SAME TEST AS D330 B WITH A BETTER INSTRUMENT. D330 B's tape filter caught
71% of the pinned trades and removed 39% of the survivors. Here the instrument
is SEC EDGAR: a name is excluded from the SCORE for 189 bars after a qualifying
filing, or until it dies, so the removed name is replaced by the next rank.
Three filing definitions, predictions on F1:

    F0  target-specific   DEFM14A PREM14A SC 14D9 SC TO-T SC TO-C
    F1  primary           F0 + 8-K with Item 1.01 and merger/tender/acquisition language
    F2  broad             F1 + 425 (acquirer-dominated; role not recorded)

CAUSALITY. A filing dated d maps to the first fixture bar on or after d, is
known at that bar's close, and applies to the score from that bar; R.ranked
lags once, so the first bar it can affect is the next. [K] is a truncation
audit on the mask, [D] counts every filing that could not be applied.

PART A validates against D330 A's look-ahead labels (catch rate, survivor
removal, lead time) and touches no book. PART B runs the books under BOTH
spread conventions -- PB, the per-bar median used since D318, and PUB, the
published trailing mean D332 made the default -- on both lenses.
"""

from __future__ import annotations

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


PA = _load("d330a", "run_d330a_pinned_decomposition.py")
V9 = PA.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
G22 = V6.G22

K0, KS = 20, (10, 20, 40)
WINDOW = 189                                # bars of exclusion after a filing
LOOKBACK = 63                               # bars before entry a filing must sit in, for Part A
F0_FORMS = {"DEFM14A", "PREM14A", "SC 14D9", "SC TO-T", "SC TO-C"}
DEALS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_deals.json"
OUT = REPO / "data" / "d331_deal_filter.json"


def filing_bars(deals, symbols, dates, first_live, last_live, forms_ok):
    """Per row, the sorted fixture bars of qualifying filings, plus drop counts.

    A filing maps to the first bar on or after its date. Filings after the
    name's last live bar, before its first, or after the fixture end are
    DROPPED and counted, never applied.
    """
    idx = {s: i for i, s in enumerate(symbols)}
    darr = np.array(dates)
    bars = {i: [] for i in range(len(symbols))}
    drops = {"after_death": 0, "before_first": 0, "after_fixture": 0, "unknown_symbol": 0}
    n_ok = 0
    for s, fl in deals.items():
        i = idx.get(s)
        if i is None:
            drops["unknown_symbol"] += sum(1 for f in fl if forms_ok(f))
            continue
        for f in fl:
            if not forms_ok(f):
                continue
            b = int(np.searchsorted(darr, f["date"]))
            if b >= len(dates):
                drops["after_fixture"] += 1
            elif b > last_live[i]:
                drops["after_death"] += 1
            elif b < first_live[i]:
                drops["before_first"] += 1
            else:
                bars[i].append(b); n_ok += 1
    return {i: np.array(sorted(set(v)), int) for i, v in bars.items()}, drops, n_ok


def exclusion_mask(fbars, n, T, last_live):
    """(n, T) bool: excluded from bar b for WINDOW bars or until the last live bar."""
    m = np.zeros((n, T), bool)
    for i, bs in fbars.items():
        for b in bs:
            e = min(b + WINDOW, last_live[i] + 1)
            m[i, b:e] = True
    return m


def main() -> int:
    t0 = time.time()
    print("D331  the deal filter")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    RANGE = np.ascontiguousarray(((g["high"] - g["low"]) / g["close"]).T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    DV = X.roll_mean_T(CLOSE * VOL)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan); HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    d332 = json.loads((REPO / "data" / "d332_spread_convention.json").read_text())
    dj = json.loads(DEALS.read_text())
    deals, resol = dj["deals"], dj["resolution"]
    resolved = {s for s, r in resol.items() if r.get("confidence") in ("high", "low")}
    print(f"  panel {finT.shape}; deals file pulled {dj.get('pulled_on')}, {len(deals)} symbols, "
          f"{len(resolved)} resolved ({time.time() - t0:.0f}s)")

    is8k = lambda f: f["form"] == "8-K" and "1.01" in str(f.get("items", "")) and f.get("matched_queries")
    FORMS = {"F0": lambda f: f["form"] in F0_FORMS,
             "F1": lambda f: f["form"] in F0_FORMS or is8k(f),
             "F2": lambda f: f["form"] in F0_FORMS or is8k(f) or f["form"] == "425"}
    fb, drops, nok, excl = {}, {}, {}, {}
    for k, fn in FORMS.items():
        fb[k], drops[k], nok[k] = filing_bars(deals, panel.symbols, panel.dates, first_live, last_live, fn)
        excl[k] = exclusion_mask(fb[k], n, T, last_live)
        print(f"  {k}: {nok[k]:,} filings applied, {sum(len(v) for v in fb[k].values()):,} distinct name-bars; "
              f"drops {drops[k]}; excluded name-bars {int((excl[k] & finT.T).sum()):,} "
              f"({100 * (excl[k] & finT.T).sum() / finT.sum():.2f}% of live)")

    def filt(sig, k):
        return np.where(excl[k], np.nan, z[sig])
    rk = {"S": Y.rank_single(z, base, "skew_63", n, T), "H": Y.rank_single(z, base, "hist_L", n, T)}
    for k in FORMS:
        rk[f"S_{k}"] = Y.rank_single({"skew_63": filt("skew_63", k)}, base, "skew_63", n, T)
    RK = {"S": rk["S"], "H": rk["H"], "LW": V9.legwise(rk["H"], rk["S"]),
          "S_F1": rk["S_F1"], "LW_F1": V9.legwise(rk["H"], rk["S_F1"]),
          "S_F0": rk["S_F0"], "S_F2": rk["S_F2"]}

    def run_cell(rankT, k, H):
        W.BASE_HOLD = k
        gate = Y.gate_from(rankT, finT)
        out = {}
        res_v = W.simulate(A, gate, 2, True, slots=True)
        try:
            c = G22.costed(res_v, (H, CLOSE, DV, finT))
            g1 = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)
            out["variant"] = dict(net_bp_bar=g1["net_bp_bar"], gross_bp_bar=g1["gross_bp_bar"],
                                  sharpe_net=g1["sharpe_net"], maxdd_bp=g1["maxdd_bp"],
                                  round_trip=c["round_trip"], held_half=c["held_half_spread"])
        except ZeroDivisionError:
            out["variant"] = "degenerate"
        res_i = W.simulate(A, gate, 2, True, slots=False)
        legs = V9.per_leg(res_i, H, CLOSE, r1T, mkt)
        out["invariant"] = V9.invariant_legcost(res_i, legs) if all(legs[s] for s in (0, 1)) else "degenerate"
        out["legs"] = {str(s): legs[s] for s in (0, 1)}
        return out, res_v, res_i

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # K. causality -- truncation audit on the F1 mask
    T0 = T // 2
    cut = {s: [f for f in fl if np.searchsorted(np.array(panel.dates), f["date"]) <= T0] for s, fl in deals.items()}
    fb_cut, _, _ = filing_bars(cut, panel.symbols, panel.dates, first_live, last_live, FORMS["F1"])
    m_cut = exclusion_mask(fb_cut, n, T, last_live)
    assert np.array_equal(excl["F1"][:, :T0 + 1], m_cut[:, :T0 + 1]), "[K] the mask before T0 changed"
    print(f"    [K] CAUSALITY: deleting every filing dated after T0={T0} leaves the exclusion mask "
          f"bit-identical through T0")
    # D. date mapping
    for k in FORMS:
        for i, bs in fb[k].items():
            assert (bs >= first_live[i]).all() and (bs <= last_live[i]).all() and (bs < T).all()
    print(f"    [D] DATE MAPPING: every applied filing sits in [first, last] live bar of its name; "
          f"dropped (F1): {drops['F1']}")
    # W. the window
    for i, bs in fb["F1"].items():
        row = excl["F1"][i]
        if row.any():
            assert int(np.flatnonzero(row)[-1]) <= min(int(bs.max()) + WINDOW - 1, last_live[i])
            assert not row[last_live[i] + 1:].any()
    print(f"    [W] WINDOW: no exclusion runs past {WINDOW} bars from its filing or past the name's last live bar")
    # I. labels reproduce D330 A
    _, resS_v, resS_i = run_cell(RK["S"], K0, HALF_PB)
    lab = PA.label_trades(resS_i["trades"], r1T, RANGE, HALF_PB, last_live, T)
    short_idx = [j for j, t in enumerate(resS_i["trades"]) if t[4] == 1]
    lab_s = lab[short_idx]
    n_dies = int(lab_s[:, 2].sum()); n_pin = int((lab_s[:, 6] == 1).sum()); n_col = int((lab_s[:, 6] == 2).sum())
    assert (len(short_idx), n_dies, n_pin, n_col) == (1024, 297, 212, 0), (len(short_idx), n_dies, n_pin, n_col)
    print("    [I] LABELS: skew_63's short leg reproduces D330 A -- 1,024 trades, 297 dying, 212 pinned, 0 collapses")
    # 1. identity with D332
    cell = {}
    worst = 0.0
    for nm in ("S", "H", "LW"):
        for cv in ("PB", "PUB"):
            cell[(nm, cv, K0)], _, _ = run_cell(RK[nm], K0, HALF[cv])
            c2 = d332["cells"][f"{nm}/{cv}"]
            worst = max(worst, abs(cell[(nm, cv, K0)]["invariant"]["net_per_trade"] - c2["invariant"]["net_per_trade"]),
                        abs(cell[(nm, cv, K0)]["variant"]["sharpe_net"] - c2["variant"]["sharpe_net"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: the unfiltered arms reproduce D332's PB and PUB cells to {worst:.1e}")
    # F. the filter fires; L. leg independence; R. refill
    for cv in ("PB", "PUB"):
        cell[("S_F1", cv, K0)], _, rSf = run_cell(RK["S_F1"], K0, HALF[cv])
        cell[("LW_F1", cv, K0)], vLWf, iLWf = run_cell(RK["LW_F1"], K0, HALF[cv])
        _, vH, iH = run_cell(RK["H"], K0, HALF[cv])
        assert not V9.same_side(rSf, resS_i, 1), "[F] S_F1 == S on the short leg"
        for a_, b_, side in ((iLWf, iH, 0), (vLWf, vH, 0)):
            assert V9.same_side(a_, b_, side), "[L] LW_F1 long != H long"
        assert V9.same_side(iLWf, rSf, 1), "[L] LW_F1 short != S_F1 short"
    assert excl["F1"].sum() > 0
    print("    [F] the filter FIRES: S_F1 differs from S on the short leg")
    print("    [L] LEG INDEPENDENCE: LW_F1's long ledger is H's, its short ledger is S_F1's, both lenses")
    rS, rSf1 = rk["S"][1], rk["S_F1"][1]
    removed_bars = refilled = 0
    for t in range(1, T):
        i0 = np.flatnonzero(rS[t] == 0)
        if i0.size == 0:
            continue
        i0 = int(i0[0])
        if excl["F1"][i0, t - 1]:
            removed_bars += 1
            j0 = np.flatnonzero(rSf1[t] == 0)
            assert j0.size == 1 and int(j0[0]) != i0, f"[R] no refill at bar {t}"
            refilled += 1
    assert removed_bars > 0 and refilled == removed_bars
    print(f"    [R] REFILL: at all {removed_bars} bars where the rank-0 short name is excluded, a different name holds rank 0")
    # 6. raises
    broke = False
    try:
        bad = dict(cell[("LW_F1", "PUB", K0)]["invariant"]); bad["net_per_trade"] += 50.0
        assert abs(bad["net_per_trade"] - cell[("LW_F1", "PUB", K0)]["invariant"]["net_per_trade"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke
    print("    [6] and the check raises on a book handed free money")

    # ---- Part A: validation against the labels --------------------------
    print("\nPART A -- skew_63's short leg, k=20: does a filing sit in [entry-63, entry]?")
    tr = [resS_i["trades"][j] for j in short_idx]
    pinned = [(t, l) for t, l in zip(tr, lab_s) if l[6] == 1]
    alive = [(t, l) for t, l in zip(tr, lab_s) if l[2] == 0]
    partA = {}
    print("  %-4s %10s %14s %14s %10s %12s" % ("def", "caught", "caught|resolv", "survivor rem", "n resolv", "lead (med)"))
    for k in FORMS:
        def hit(t):
            bs = fb[k].get(t[0], np.array([], int))
            w = bs[(bs <= t[1]) & (bs >= t[1] - LOOKBACK)]
            return w
        c_all = np.array([hit(t).size > 0 for t, _ in pinned])
        res_m = np.array([panel.symbols[t[0]] in resolved for t, _ in pinned])
        c_res = c_all[res_m].mean() if res_m.any() else np.nan
        rem = np.array([hit(t).size > 0 for t, _ in alive]).mean()
        leads = [t[1] - hit(t).min() for t, _ in pinned if hit(t).size]
        partA[k] = dict(caught=float(c_all.mean()), caught_resolved=float(c_res), n_resolved=int(res_m.sum()),
                        n_pinned=len(pinned), survivor_removed=float(rem), n_alive=len(alive),
                        lead_median=float(np.median(leads)) if leads else np.nan)
        print("  %-4s %9.1f%% %13.1f%% %13.1f%% %10d %12s"
              % (k, 100 * c_all.mean(), 100 * c_res, 100 * rem, int(res_m.sum()),
                 ("%.0f bars" % np.median(leads)) if leads else "-"))
    # long-leg removal under F1 (Q8): trades in S's long leg whose name is excluded at entry-1
    long_tr = [t for t in resS_i["trades"] if t[4] == 0]
    rem_long = float(np.mean([excl["F1"][t[0], max(t[1] - 1, 0)] for t in long_tr]))
    print(f"  F1 on skew_63's LONG leg: {100 * rem_long:.2f}% of its {len(long_tr)} trades excluded at entry")

    # ---- Part B: the books ----------------------------------------------
    ts = time.time()
    for nm in ("S", "S_F1", "H", "LW", "LW_F1"):
        for k in KS:
            for cv in ("PB", "PUB"):
                if (nm, cv, k) not in cell:
                    cell[(nm, cv, k)], _, _ = run_cell(RK[nm], k, HALF[cv])
    for nm in ("S_F0", "S_F2"):
        for cv in ("PB", "PUB"):
            cell[(nm, cv, K0)], _, _ = run_cell(RK[nm], K0, HALF[cv])
    print(f"\n  Part B cells ({time.time() - ts:.0f}s)")
    it = lambda c: c["invariant"]["net_per_trade"] if c["invariant"] != "degenerate" else np.nan
    vb = lambda c: c["variant"]["net_bp_bar"] if c["variant"] != "degenerate" else np.nan
    sh = lambda c: c["variant"]["sharpe_net"] if c["variant"] != "degenerate" else np.nan
    sl = lambda c, s: c["legs"][str(s)]
    print("\nPART B -- invariant net per trade | variant net bp/bar (Sharpe)     PB  ||  PUB")
    print("  %-7s %3s | %8s %8s %8s | %8s %8s %8s || %8s %8s | %8s %8s"
          % ("arm", "k", "net/trd", "S-leg", "S half", "bp/bar", "Sharpe", "maxDD", "net/trd", "S-leg", "bp/bar", "Sharpe"))
    for nm in ("S", "S_F1", "S_F0", "S_F2", "H", "LW", "LW_F1"):
        for k in KS:
            if (nm, "PB", k) not in cell:
                continue
            a, b = cell[(nm, "PB", k)], cell[(nm, "PUB", k)]
            print("  %-7s %3d | %+8.2f %+8.1f %8.1f | %+8.2f %+8.3f %8.0f || %+8.2f %+8.1f | %+8.2f %+8.3f"
                  % (nm, k, it(a), sl(a, 1)["net"], sl(a, 1)["half_bp"], vb(a), sh(a),
                     a["variant"]["maxdd_bp"] if a["variant"] != "degenerate" else np.nan,
                     it(b), sl(b, 1)["net"], vb(b), sh(b)))

    # trimmed-both mean of the short leg, from the ledgers
    def trim_short(rankT):
        W.BASE_HOLD = K0
        res = W.simulate(A, Y.gate_from(rankT, finT), 2, True, slots=False)
        p = np.sort(np.array([t[3] for t in res["trades"] if t[4] == 1]) * 1e4)
        c1 = max(1, len(p) // 100)
        return float(p[c1:-c1].mean())
    tr_S, tr_F1 = trim_short(RK["S"]), trim_short(RK["S_F1"])

    # ---- predictions -------------------------------------------------------
    a1 = partA["F1"]
    q1 = a1["caught"] > 0.75 and a1["caught_resolved"] > 0.85 and a1["survivor_removed"] < 0.10
    q2 = (sl(cell[("S_F1", "PB", K0)], 1)["half_bp"] >= 8.5 and sl(cell[("S_F1", "PUB", K0)], 1)["half_bp"] >= 20.0)
    q3 = abs(tr_F1 - tr_S) < 10.0
    q4 = sl(cell[("S_F1", "PUB", K0)], 1)["net"] > sl(cell[("S", "PUB", K0)], 1)["net"]
    q5 = it(cell[("LW_F1", "PUB", K0)]) > max(it(cell[("S_F1", "PUB", K0)]), it(cell[("H", "PUB", K0)]))
    q6 = partA["F0"]["caught"] < 0.50
    q7 = (partA["F2"]["survivor_removed"] > 3 * max(partA["F1"]["survivor_removed"], 1e-9)
          and partA["F2"]["caught"] - partA["F1"]["caught"] < 0.05)
    q8 = rem_long < 0.02
    q9 = a1["lead_median"] > 5
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 F1 catches >75% of pinned (>85% among resolved) and removes <10% of survivors  [load-bearing]", q1),
                   ("Q2 filtered short-leg half-spread: PB >= 8.5, PUB >= 20", q2),
                   ("Q3 trimmed-both mean of the short leg moves < 10 bp", q3),
                   ("Q4 under PUB, S_F1's short leg nets more per trade than S's", q4),
                   ("Q5 LW_F1 still beats both parents per trade under PUB  [load-bearing]", q5),
                   ("Q6 F0 (target forms only) catches < 50%  [against F0]", q6),
                   ("Q7 F2 (adding 425) removes >3x the survivors of F1 for <5 pts more catch  [against F2]", q7),
                   ("Q8 F1 removes <2% of skew_63's LONG-leg trades", q8),
                   ("Q9 median lead from filing to entry > 5 bars", q9)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    F1: caught {100 * a1['caught']:.1f}% ({100 * a1['caught_resolved']:.1f}% of {a1['n_resolved']} resolved), "
          f"survivors removed {100 * a1['survivor_removed']:.1f}%, lead {a1['lead_median']:.0f} bars, long-leg removed {100 * rem_long:.2f}%")
    print(f"    short leg trimmed-both: {tr_S:+.1f} -> {tr_F1:+.1f};  S short net PUB {sl(cell[('S', 'PUB', K0)], 1)['net']:+.1f} -> "
          f"{sl(cell[('S_F1', 'PUB', K0)], 1)['net']:+.1f};  half PB {sl(cell[('S_F1', 'PB', K0)], 1)['half_bp']:.1f} PUB {sl(cell[('S_F1', 'PUB', K0)], 1)['half_bp']:.1f}")
    print(f"    LW_F1 PUB per trade {it(cell[('LW_F1', 'PUB', K0)]):+.2f} vs S_F1 {it(cell[('S_F1', 'PUB', K0)]):+.2f}, H {it(cell[('H', 'PUB', K0)]):+.2f};  "
          f"LW_F1 PB {it(cell[('LW_F1', 'PB', K0)]):+.2f}")

    OUT.write_text(json.dumps(dict(
        note="D331: event-driven deal exclusion on the score. PB/PUB spread conventions; variant bp/bar, "
             "invariant per trade, never compared (FINDINGS 10). Part A labels are look-ahead, used only to validate.",
        deals_pulled_on=dj.get("pulled_on"), window_bars=WINDOW, lookback_bars=LOOKBACK,
        forms={"F0": sorted(F0_FORMS), "F1": "F0 + 8-K item 1.01 merger language", "F2": "F1 + 425"},
        applied=nok, drops=drops,
        excluded_live_frac={k: float((excl[k] & finT.T).sum() / finT.sum()) for k in FORMS},
        partA=partA, long_leg_removed=rem_long, trimmed_short={"S": tr_S, "S_F1": tr_F1},
        cells={f"{a}/{b}/k{k}": c for (a, b, k), c in cell.items()},
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5),
                         Q6=bool(q6), Q7=bool(q7), Q8=bool(q8), Q9=bool(q9))), indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
