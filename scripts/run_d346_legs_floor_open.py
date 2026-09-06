"""D346 -- the 46 legs under the floor and the open fill: does any long leg survive honest scoring?

    uv run python scripts/run_d346_legs_floor_open.py --selftest
    uv run python scripts/run_d346_legs_floor_open.py

D335's per-leg table under keep_v2 and the next-open fill, at k=20 (the D335
comparison) and k=40 (the operating point). Every one of the 46 dimensionless
signals as a symmetric book at depth 2 with D303's target and the F0 deal filter;
variant (slot-capped, bp/bar) and invariant (per leg, per trade); PUB and PB.
No nulls per leg -- the counts are the finding.

ASSERTIONS [K][F0][R][P][1][C][S][L][6] -- pre-reg section 4.
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


V44 = _load("d344r", "run_d344_hold_length.py")      # main guarded; every alias
V35, V31, PA, V9 = V44.V35, V44.V31, V44.PA, V44.V9
V6, Y, W, D, M, SP, R, X = V44.V6, V44.Y, V44.W, V44.D, V44.M, V44.SP, V44.R, V44.X
G22, BR, V38, CEN, UF, FL = V44.G22, V44.BR, V44.V38, V44.CEN, V44.UF, V44.FL

DEPTH = 2
KS = (20, 40)
CONVS = ("PB", "PUB")
EXCLUDED = V9.EXCLUDED
OUT = REPO / "data" / "d346_legs_floor_open.json"
D335_JSON = REPO / "data" / "d335_legs_under_filter.json"
D343_JSON = REPO / "data" / "d343_relisting_clause.json"
D344_JSON = REPO / "data" / "d344_hold_length.json"
EVENT_CANDIDATES = ("rsi", "retrace_leg", "rev_5")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D346  the 46 legs under the floor and the open fill")

    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists() and cache.stat().st_mtime > rp.stat().st_mtime, "[K]"
    assert str(np.load(cache, allow_pickle=False)["key"]) == R.BC.cache_key(M.B.FIXTURE), "[K] key"
    print("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")

    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
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
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    G4 = {cv: (HALF[cv], CLOSE, DV, finT) for cv in CONVS}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    d335 = json.loads(D335_JSON.read_text())
    d343 = json.loads(D343_JSON.read_text())
    d344 = json.loads(D344_JSON.read_text())
    print(f"  panel {finT.shape} ({el()})")

    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == V35.EXPECT_APPLIED and abs(pct - V35.EXPECT_PCT) < 0.02, f"[F0] {n_ok} / {pct:.3f}%"
    print(f"    [F0] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")
    RAW = UF.raw_price_factor(panel, ev)
    assert np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)), "[R] factor"
    RAW_CLOSE = CLOSE * RAW
    keep = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    assert abs(share - float(d343["floor"]["v2_share_live_fail"])) < 1e-9, "[R] keep_v2 share != D343"
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor; keep_v2 fails {100 * share:.4f}% of live name-bars == D343")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]

    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert sorted(pool) == sorted(d335["pool"]) and len(pool) == 46, "[P] the pool is not D335's 46"
    print(f"    [P] POOL: exactly D335's 46 dimensionless signals; {sorted(EXCLUDED)} excluded")

    def raw_px_median(res):
        v = np.array([RAW_CLOSE[e0 - 1, row] for row, e0, _a, _p, _s in res["trades"] if e0 > 0])
        return float(np.nanmedian(v)) if v.size else np.nan

    def run_cell(sig, k):
        sc = UF.apply_floor_replace(np.where(excl, np.nan, z[sig]), keep)
        rankT = Y.rank_single({sig: sc}, base, sig, n, T)
        gate = Y.gate_from(rankT, finT)
        W.BASE_HOLD = k
        res_v = W.simulate(A2, gate, DEPTH, True, slots=True, fill="open")
        res_i = W.simulate(A2, gate, DEPTH, True, slots=False, fill="open")
        out = {"variant": {}, "invariant": {}, "legs": {}, "raw_px": {}}
        for cv in CONVS:
            try:
                c = G22.costed(res_v, G4[cv])
                out["variant"][cv] = dict(net_bp_bar=c["net_bp"], gross_bp_bar=c["gross_bp"], sharpe_net=c["sharpe_net"],
                                          maxdd_bp=c["maxdd_bp"], held_half=c["held_half_spread"], held_price=c["held_price"])
            except ZeroDivisionError:
                out["variant"][cv] = "degenerate"
            legs = V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt)
            out["legs"][cv] = {str(s): legs[s] for s in (0, 1)}
            out["invariant"][cv] = (V9.invariant_legcost(res_i, legs) if all(legs[s] for s in (0, 1)) else "degenerate")
        for s in (0, 1):
            trs = [t for t in res_i["trades"] if t[4] == s]
            v = np.array([RAW_CLOSE[e0 - 1, row] for row, e0, _a, _p, _s in trs if e0 > 0])
            out["raw_px"][str(s)] = float(np.nanmedian(v)) if v.size else None
        return out, res_v, res_i

    # ---- identities first ---------------------------------------------------------------------
    print("\nASSERTIONS")
    worst = 0.0
    ID = {}
    for sig, k, ref, lab in (("rsi", 20, d343["cells"]["RSI/v2"], "D343 RSI/v2"), ("retrace_leg", 20, d343["cells"]["RL/v2"], "D343 RL/v2"),
                             ("rsi", 40, d344["cells"]["40"], "D344 k=40")):
        cell, res_v, res_i = run_cell(sig, k)
        ID[sig, k] = (cell, res_v, res_i)
        for cv in CONVS:
            worst = max(worst, abs(cell["variant"][cv]["net_bp_bar"] - ref["costed"][cv]["net_bp"]),
                        abs(cell["variant"][cv]["sharpe_net"] - ref["costed"][cv]["sharpe_net"]),
                        abs(cell["invariant"][cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: rsi and retrace_leg at k=20 reproduce D343, rsi at k=40 reproduces D344, to {worst:.1e} -- "
          f"variant net and Sharpe, invariant per trade, both conventions")
    # [C] on the identity cells
    for (sig, k), (cell, _v, _i) in ID.items():
        for cv in CONVS:
            for s in (0, 1):
                L = cell["legs"][cv][str(s)]
                assert L and abs(L["two_c"] - 2.0 * L["half_bp"]) < 1e-12, f"[C] {sig} {k} {cv} {s}"
    print("    [C] per-leg 2c is 2 x that leg's held median half-spread on every leg of the identity cells")
    # [S] on rsi k=20 invariant
    tr = ID["rsi", 20][2]["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    print(f"    [S] SIGN IN MONEY: every rsi k=20 invariant trade equals the open-fill recomputation to {worst_s:.1e}")
    # [6]
    broke = False
    try:
        bad = dict(ID["rsi", 20][0]["legs"]["PUB"]["0"])
        bad["net"] += 50.0
        assert abs(bad["net"] - d343["cells"]["RSI/v2"]["legs"]["PUB"]["0"]["net"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and the check raises on a leg handed free money")
    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- the table --------------------------------------------------------------------------------
    TABLE = {k: {} for k in KS}
    degenerate = {k: [] for k in KS}
    ts = time.time()
    for k in KS:
        for j, s in enumerate(pool):
            if (s, k) in ID:
                TABLE[k][s] = ID[s, k][0]
            else:
                TABLE[k][s], _v, _i = run_cell(s, k)
            for cv in CONVS:
                for side in (0, 1):
                    L = TABLE[k][s]["legs"][cv][str(side)]
                    if L is None or not L.get("trades"):
                        degenerate[k].append((s, cv, side))
                    elif L["half_bp"] == 0.0:
                        degenerate[k].append((s, cv, side))
            if (j + 1) % 10 == 0:
                print(f"  k={k}: {j + 1}/46 ({time.time() - ts:.0f}s)", flush=True)
    print(f"  92 symmetric books, both lenses ({el()})")
    # [L]
    for k in KS:
        for s in pool:
            for cv in CONVS:
                for side in (0, 1):
                    L = TABLE[k][s]["legs"][cv][str(side)]
                    if L and L.get("trades") and L["half_bp"] > 0:
                        assert abs(L["two_c"] - 2.0 * L["half_bp"]) < 1e-12, f"[C] {s} {k} {cv} {side}"
    print(f"    [L] every book has both legs; degenerate (zero held half-spread or no trades): k=20 {len(degenerate[20])}, k=40 {len(degenerate[40])} "
          f"-- recorded, not dropped; [C] holds on every costable leg")

    # ---- ranking and counts -----------------------------------------------------------------------------
    def leg_rows(k, cv, side):
        rows = []
        for s in pool:
            L = TABLE[k][s]["legs"][cv][str(side)]
            if L and L.get("trades") and L["half_bp"] > 0:
                rows.append((L["net"], s, L))
        return sorted(rows, key=lambda r: -r[0])

    def variant_rows(k, cv):
        rows = []
        for s in pool:
            v = TABLE[k][s]["variant"][cv]
            if v != "degenerate":
                rows.append((v["net_bp_bar"], s, v))
        return sorted(rows, key=lambda r: -r[0])

    SUMMARY = {}
    print("\n" + "=" * 110)
    for k in KS:
        for side, nm in ((0, "LONG"), (1, "SHORT")):
            rows = leg_rows(k, "PUB", side)
            nets = np.array([r[0] for r in rows])
            pos_n = int((nets > 0).sum())
            SUMMARY[f"k{k}/{nm}"] = dict(n=len(rows), positive=pos_n, p50=float(np.median(nets)), p95=float(np.quantile(nets, .95)),
                                        p05=float(np.quantile(nets, .05)), top=[(r[1], r[0]) for r in rows[:6]], bottom=[(r[1], r[0]) for r in rows[-3:]])
            print(f"  k={k} {nm} legs, PUB net per trade: {pos_n} of {len(rows)} positive; p50 {np.median(nets):+.1f}, p95 {np.quantile(nets, .95):+.1f}, "
                  f"p05 {np.quantile(nets, .05):+.1f}")
            print("    top: " + ", ".join(f"{s} {v:+.1f}" for v, s, _ in rows[:6]))
            print("    bottom: " + ", ".join(f"{s} {v:+.1f}" for v, s, _ in rows[-3:]))
        vr = variant_rows(k, "PUB")
        vn = np.array([r[0] for r in vr])
        SUMMARY[f"k{k}/VARIANT"] = dict(n=len(vr), positive=int((vn > 0).sum()), top=[(r[1], r[0], r[2]["sharpe_net"]) for r in vr[:8]])
        print(f"  k={k} VARIANT books, PUB net bp/bar: {int((vn > 0).sum())} of {len(vr)} positive; top: " +
              ", ".join(f"{s} {v:+.2f} (Sharpe {c['sharpe_net']:+.3f})" for v, s, c in vr[:8]))

    # the D335 comparison at k=20 (D335 was k=20, F0, close fill, no floor)
    comp = []
    for s in pool:
        L_new = TABLE[20][s]["legs"]["PUB"]["0"]
        L_old = d335["table"].get(s, {}).get("legs", {}).get("PUB", {}).get("0")
        if L_new and L_old and L_new.get("trades") and L_old.get("trades"):
            comp.append((s, L_old["net"], L_new["net"], L_old.get("price"), TABLE[20][s]["raw_px"]["0"]))
    improved = sum(1 for c in comp if c[2] > c[1])
    print(f"\n  D335 -> D346 at k=20, long legs PUB per trade: {improved} of {len(comp)} improved; median change "
          f"{np.median([c[2] - c[1] for c in comp]):+.1f} bp")
    big = sorted(comp, key=lambda c: c[2] - c[1])
    print("    largest falls: " + ", ".join(f"{c[0]} {c[1]:+.0f}->{c[2]:+.0f}" for c in big[:5]))
    print("    largest rises: " + ", ".join(f"{c[0]} {c[1]:+.0f}->{c[2]:+.0f}" for c in big[-5:]))
    raw_px_long = np.array([TABLE[20][s]["raw_px"]["0"] for s in pool if TABLE[20][s]["raw_px"]["0"] is not None])
    print(f"  median held as-traded price, long legs k=20: ${np.median(raw_px_long):.2f} (D335's top legs were at $6-$28 adjusted)")

    # the three event candidates
    print("\n  the three event candidates' long legs, PUB per trade:")
    for s in EVENT_CANDIDATES:
        for k in KS:
            L = TABLE[k][s]["legs"]["PUB"]["0"]
            print(f"    {s:12s} k={k}: net {L['net']:+.1f} on gross {L['gross']:+.1f} (t {L['t']:+.2f}, {L['trades']} trades, half {L['half_bp']:.1f} bp)")

    # ---- predictions ----------------------------------------------------------------------------------------
    q = {}
    q["Q1"] = bool(SUMMARY["k20/LONG"]["positive"] < 3)
    q["Q2"] = bool(all(TABLE[20][s]["legs"]["PUB"]["0"]["net"] <= 0 for s in EVENT_CANDIDATES))
    q["Q3"] = bool(SUMMARY["k40/LONG"]["positive"] < 3)
    q["Q4"] = bool(SUMMARY["k20/SHORT"]["positive"] < 3)
    q["Q5"] = bool(improved < 23)
    best_v = SUMMARY["k20/VARIANT"]["top"][0][0]
    q["Q6"] = bool(best_v == "rsi" and SUMMARY["k20/VARIANT"]["positive"] < 5)
    q["Q7"] = bool(np.median(raw_px_long) > 20.0)
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) < 3 of 46 long legs positive at k=20: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- {SUMMARY['k20/LONG']['positive']}: "
          + ", ".join(f"{s} {v:+.1f}" for s, v in SUMMARY["k20/LONG"]["top"] if v > 0))
    print(f"  Q2 none of rsi/retrace_leg/rev_5 long legs positive at k=20: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'}")
    print(f"  Q3 (against) < 3 positive long legs at k=40: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- {SUMMARY['k40/LONG']['positive']}: "
          + ", ".join(f"{s} {v:+.1f}" for s, v in SUMMARY["k40/LONG"]["top"] if v > 0))
    print(f"  Q4 < 3 short legs positive at k=20: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- {SUMMARY['k20/SHORT']['positive']}: "
          + ", ".join(f"{s} {v:+.1f}" for s, v in SUMMARY["k20/SHORT"]["top"] if v > 0))
    print(f"  Q5 < 23 long legs improved vs D335: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- {improved} of {len(comp)}")
    print(f"  Q6 (against) rsi is the best variant book and < 5 positive: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- best {best_v}, "
          f"{SUMMARY['k20/VARIANT']['positive']} positive")
    print(f"  Q7 median held as-traded price of long legs > $20: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- ${np.median(raw_px_long):.2f}")

    def clean(o):
        if isinstance(o, dict):
            return {"/".join(k) if isinstance(k, tuple) else str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    out = dict(note="D346: the 46 dimensionless signals as symmetric F0 books at depth 2 under keep_v2 and the open fill, k=20 and k=40, "
                    "both lenses, PUB and PB. Variant bp/bar and invariant per trade never compared. Nothing promoted.",
               pool=pool, excluded=sorted(EXCLUDED), table={str(k): TABLE[k] for k in KS}, degenerate={str(k): degenerate[k] for k in KS},
               summary=SUMMARY, d335_comparison=dict(rows=comp, improved=improved, n=len(comp)),
               median_raw_px_long_k20=float(np.median(raw_px_long)), predictions=q, identity_worst=worst)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
