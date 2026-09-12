"""D455 -- insider purchases stage 1: the event book through the D345 kernel with three controls. Spec committed in 398669b BEFORE this
file. In-sample on the mining fixture; no holdout.

    uv run python -u scripts/run_d455_insider_book.py --run [--quick]
    uv run python -u scripts/run_d455_insider_book.py --selftest

Primary set: purchase filings 2010-2023 with no 10% owner among the reporting owners, value >= $25k, name eligible at the availability
bar t_av (the first bar strictly after the filing date; the kernel fills at the open of t_av). Long, cap 63, every event, hedged.
Controls: C1 state-matched names (same price x vol x mom cell, same day, no purchase filing within +-5 bars); C2 the event calendar
rolled by a common offset on a 21-bar grid (exact); C3 each name's events rolled by its own random offset (D437's rotate).
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R46 = _load("d446", "run_d446_issuance_book.py")
EVENTS = REPO / "data" / "d454_insider_events.csv.gz"; OWNERS = REPO / "data" / "d454_insider_owner_rows.csv.gz"; OUT = REPO / "data" / "d455_insider_book.json"
START, END = "2010-01-01", "2023-12-29"; VALUE_FLOOR = 25_000.0; CAP = 63; CAPS_ROBUST = (21, 126); NEAR = 5; CLUSTER_CAP = 5
N_DRAW = 100; ROT_STEP = 21; SEED = 455; CAPTURE, CHASE_BP = 0.66, 9.0


# ------------------------------------------------------------------------------------------ events -> masks
def load_events(dates, symbols, elig, T):
    fix = pd.to_datetime(dates); sym_i = {s: i for i, s in enumerate(symbols)}
    ev = pd.read_csv(EVENTS, dtype={"symbol": str, "filing": str, "kind": str, "cik": str}); ev = ev[(ev["filing"] >= START) & (ev["filing"] <= END)].copy()
    ev["t_av"] = np.searchsorted(fix, pd.to_datetime(ev["filing"]), side="right"); ev = ev[ev["t_av"] < T]; ev["j"] = ev["symbol"].map(sym_i); ev = ev[ev["j"].notna()]; ev["j"] = ev["j"].astype(int)
    assert all(dates[t] > f for t, f in zip(ev["t_av"], ev["filing"])), "[F] an availability bar on or before its filing date"
    ev["elig"] = [bool(elig[t, j]) for t, j in zip(ev["t_av"], ev["j"])]
    for r in ("Director", "Officer", "TenPercentOwner", "Other"):
        ev[r] = ev[r].astype(bool)
    return ev


def cluster_flag(ev, dates, T):
    """Distinct NON-10%-owner buyers of the same name within +-NEAR bars of the event, capped at CLUSTER_CAP per name-day (family trusts)."""
    fix = pd.to_datetime(dates); o = pd.read_csv(OWNERS, dtype={"symbol": str, "RPTOWNERCIK": str, "kind": str, "filing": str}); o = o[(o["kind"] == "P") & (o["filing"] >= START) & (o["filing"] <= END)].copy()
    o["t_av"] = np.searchsorted(fix, pd.to_datetime(o["filing"]), side="right"); by = {}
    for s, g in o.groupby("symbol"):
        days = {}
        for t, ck in zip(g["t_av"], g["RPTOWNERCIK"]):
            days.setdefault(int(t), set()).add(ck)
        by[s] = {t: list(v)[:CLUSTER_CAP] for t, v in days.items()}
    out = np.zeros(len(ev), int)
    for i, (s, t) in enumerate(zip(ev["symbol"], ev["t_av"])):
        d = by.get(s, {}); owners = set()
        for tt in range(int(t) - NEAR, int(t) + NEAR + 1):
            owners.update(d.get(tt, []))
        out[i] = len(owners)
    return out


def mask_of(sub, T, N):
    m = np.zeros((T, N), bool); m[sub["t_av"].to_numpy(), sub["j"].to_numpy()] = True; return m


def dilate(m, k):
    out = m.copy()
    for s in range(1, k + 1):
        out[s:] |= m[:-s]; out[:-s] |= m[s:]
    return out


# ------------------------------------------------------------------------------------------ books
def side_block(V59, R38, P, elig, r, side, yr):
    tb = V59.trade_block(P, r, elig, side, False); db = V59.deployed_block(r, P); pnl = V59.V47.pnl_bp(r); borrow = tb.get("borrow", {}).get("mean_bp", 0.0) if side == 1 else 0.0
    turn = db["PUB"]["hedged"]["turnover"]; crossed = db["PUB"]["hedged_2x"]["cost_bp"] + borrow * turn; passive = db["PUB"]["hedged_2x"]["cost_bp"] * (1 - CAPTURE) + CHASE_BP * turn + borrow * turn
    return dict(trades=tb["trades"], gross=tb["mean_bp"], median=tb["median_bp"], se=float(pnl.std(ddof=1) / np.sqrt(pnl.size)) if pnl.size > 1 else float("nan"), two_c_PUB=tb["two_c"]["PUB"], borrow=borrow, net_PUB=tb["mean_bp"] - tb["two_c"]["PUB"] - borrow,
                hold=tb["hold_mean"], turnover=turn, cost_crossed_bar=crossed, cost_passive_bar=passive, conc=R38.conc(r, pnl, P, yr)), pnl


def run_set(V59, R38, R37, P, elig, mask, side, cap, dates, d0, t_end, yr, SC):
    r = R46.simulate(V59, P, mask, SC, cap, side, None); st, pnl = side_block(V59, R38, P, elig, r, side, yr); g = R46.book_series(r)
    bk = R46.book_stats(R37, g, dates, d0, st["cost_crossed_bar"], st["cost_passive_bar"], t_end)
    return r, st, bk, g


# ------------------------------------------------------------------------------------------ the study
def run(quick=False):
    t0 = time.time(); print("D455 STAGE 1 -- insider purchases: the event book, three controls\n      the bar was committed in 398669b BEFORE this ran; mining fixture only; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py"); R37 = _load("d437", "run_d437_stage1.py"); R38 = _load("d438", "run_d438_cost_axes.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]).copy(); dates = np.array([str(x)[:10] for x in P["dates"]]); symbols = list(P["symbols"]); yr = np.array([int(x[:4]) for x in dates])
    t_end = int(np.searchsorted(dates, END, side="right")); elig[t_end:] = False; SC = np.full((T, N), 50.0); R38.SC = SC
    idx = A92.eligible_index(elig); mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, SC, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", SC); assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    ev = load_events(dates, symbols, elig, T); ev["cluster_owners"] = cluster_flag(ev, dates, T)
    P_ = ev[(ev["kind"] == "P") & ev["elig"]]; prim = P_[(~P_["TenPercentOwner"]) & (P_["value"] >= VALUE_FLOOR)]; tenp = P_[P_["TenPercentOwner"] & (P_["value"] >= VALUE_FLOOR)]
    S_ = ev[(ev["kind"] == "S") & ev["elig"] & (~ev["TenPercentOwner"]) & (ev["value"] >= VALUE_FLOOR)]
    sets = {"primary": prim, "cluster": prim[prim["cluster_owners"] >= 2], "single": prim[prim["cluster_owners"] < 2], "officer_only": prim[prim["Officer"] & ~prim["Director"]], "director_only": prim[prim["Director"] & ~prim["Officer"]],
            "tenpct_owner": tenp}
    vt = prim["value"].quantile([1 / 3, 2 / 3]).to_numpy(); sets["value_lo"] = prim[prim["value"] <= vt[0]]; sets["value_hi"] = prim[prim["value"] > vt[1]]
    d0 = int(prim["t_av"].min()); n_ev = {k: int(len(v)) for k, v in sets.items()}
    print(f"  [K] kernel probe;  [F] every availability bar is after its filing;  purchase filings 2010-2023 on eligible names {len(P_):,} -> primary (no 10% owner, >= ${VALUE_FLOOR:,.0f}) {len(prim):,}; 10%-owner {len(tenp):,}; sales mirror {len(S_):,}; cluster {n_ev['cluster']:,} / single {n_ev['single']:,}; officer-only {n_ev['officer_only']:,} director-only {n_ev['director_only']:,}; value terciles at ${vt[0]:,.0f} / ${vt[1]:,.0f}")
    res = dict(spec="398669b", n_events=n_ev, d0=str(dates[d0]), end=END, sets={}, controls={}, robust={}, bar={}, quick=quick); n_draw = 10 if quick else N_DRAW; step = 42 if quick else ROT_STEP; rng = np.random.default_rng(SEED)

    # 1. the primary and the reported sets
    R = {}
    for k, sub in sets.items():
        r, st, bk, g = run_set(V59, R38, R37, P, elig, mask_of(sub, T, N), 0, CAP, dates, d0, t_end, yr, SC); R[k] = (r, g); st["book"] = bk; res["sets"][k] = st
        print(f"  {k:13s} n {st['trades']:6,}  per trade gross {st['gross']:+7.1f} +- {st['se']:5.1f}  median {st['median']:+7.1f}  2c {st['two_c_PUB']:5.1f}  net {st['net_PUB']:+7.1f}  |  book gross {bk['gross']:+.3f} +- {bk['se']:.3f}  crossed {st['cost_crossed_bar']:.3f}  net {bk['net_crossed']:+.3f} ({bk['net_crossed']/bk['se']:+.1f} SE)  passive net {bk['net_passive']:+.3f}  to-half {st['conc']['to_half']}  top1% {st['conc']['top1_share']:.0f}%")
    r, st, bk, g = run_set(V59, R38, R37, P, elig, mask_of(S_, T, N), 1, CAP, dates, d0, t_end, yr, SC); st["book"] = bk; res["sets"]["sales_short"] = st
    print(f"  {'sales_short':13s} n {st['trades']:6,}  per trade gross {st['gross']:+7.1f} +- {st['se']:5.1f}  median {st['median']:+7.1f}  2c {st['two_c_PUB']:5.1f}  borrow {st['borrow']:.1f}  net {st['net_PUB']:+7.1f}  |  book gross {bk['gross']:+.3f} +- {bk['se']:.3f}  net {bk['net_crossed']:+.3f}")
    pr = res["sets"]["primary"]; pb = pr["book"]; print(f"\n  PRIMARY book by year (net crossed): " + " ".join(f"{y}:{x:+.1f}" for y, x in pb["by_year"].items()) + f"\n  era1 {pb['era1']:+.3f} +- {pb['era1_se']:.3f}   era2 (from {pb['era2_start']}) {pb['era2']:+.3f} +- {pb['era2_se']:.3f}")
    for cap in CAPS_ROBUST:
        r, st, bk, g = run_set(V59, R38, R37, P, elig, mask_of(prim, T, N), 0, cap, dates, d0, t_end, yr, SC); res["robust"][f"cap{cap}"] = dict(trades=st["trades"], gross_trade=st["gross"], gross=bk["gross"], se=bk["se"], net_crossed=bk["net_crossed"])
        print(f"  cap {cap:3d}: per trade {st['gross']:+.1f}  book gross {bk['gross']:+.3f} +- {bk['se']:.3f}  net crossed {bk['net_crossed']:+.3f}")

    # 2. C1 -- state-matched names on the same day and cell, no purchase filing within +-5 bars
    print(f"\n  C1 state-matched ({n_draw} draws)", flush=True); t1 = time.time()
    cells = [R46.shift(c, elig) for c in R46.cells_of(A92, P, elig)]; near = dilate(mask_of(P_, T, N), NEAR); pool = elig & ~near
    ev_real = R46.entry_mask(R[("primary")][0], T, N); gs = []
    for d in range(n_draw):
        m = R46.c1_mask(R37, rng, ev_real, cells, pool); rr = R46.simulate(V59, P, m, SC, CAP, 0, None); gs.append(float(V59.V47.pnl_bp(rr).mean()))
    gs = np.array(gs); sd = float(gs.std(ddof=1)); real = pr["gross"]; c1d = dict(p50=float(np.median(gs)), p95=float(np.quantile(gs, .95)), se=sd / np.sqrt(n_draw), sd=sd, n_events=int(ev_real.sum()), increment=real - float(np.median(gs)), z_median=(real - float(np.median(gs))) / sd, z_p95=(real - float(np.quantile(gs, .95))) / sd)
    c1d["passes"] = bool(real > c1d["p95"] and (real - c1d["p95"]) >= 2 * c1d["se"]); res["controls"]["C1"] = c1d
    print(f"    real {real:+.1f}  C1 p50 {c1d['p50']:+.1f}  p95 {c1d['p95']:+.1f} +- {c1d['se']:.1f} (draw SD {sd:.0f}; real {c1d['z_median']:+.2f} SD above the median, {c1d['z_p95']:+.2f} beyond p95)  {'PASS' if c1d['passes'] else 'fail'}   ({(time.time()-t1)/60:.1f} min)", flush=True)

    # 3. C2 -- exact common rotation of the event calendar
    m0 = mask_of(prim, T, N); offs = list(range(step, T - step, step)); print(f"\n  C2 rotation: {len(offs)} offsets", flush=True); t1 = time.time(); rot = []
    for i, k in enumerate(offs):
        rr = R46.simulate(V59, P, np.roll(m0, k, axis=0) & elig, SC, CAP, 0, None); rot.append(float(R46.book_series(rr)[d0:t_end].mean()))
        if (i + 1) % 40 == 0:
            print(f"    {i+1}/{len(offs)}  {(time.time()-t1)/60:.1f} min", flush=True)
    rot = np.array(rot); c2 = dict(n=len(offs), p50=float(np.median(rot)), p95=float(np.quantile(rot, .95)), passes=bool(pb["gross"] > np.quantile(rot, .95)), draws=rot.tolist()); res["controls"]["C2"] = c2
    print(f"    real {pb['gross']:+.3f}  C2 p50 {c2['p50']:+.3f}  p95 {c2['p95']:+.3f} (exact on the grid)  {'PASS' if c2['passes'] else 'fail'}", flush=True)

    # 4. C3 -- name-preserving shuffle
    print(f"\n  C3 name-preserving shuffle ({n_draw} draws)", flush=True); t1 = time.time(); c3 = []
    for d in range(n_draw):
        rr = R46.simulate(V59, P, R37.rotate(rng, m0, elig), SC, CAP, 0, None); c3.append(float(R46.book_series(rr)[d0:t_end].mean()))
    c3 = np.array(c3); c3d = dict(n=n_draw, p50=float(np.median(c3)), p95=float(np.quantile(c3, .95)), se=float(c3.std(ddof=1) / np.sqrt(n_draw)), sd=float(c3.std(ddof=1))); c3d["passes"] = bool(pb["gross"] > c3d["p95"] and (pb["gross"] - c3d["p95"]) >= 2 * c3d["se"]); res["controls"]["C3"] = c3d
    print(f"    real {pb['gross']:+.3f}  C3 p50 {c3d['p50']:+.3f}  p95 {c3d['p95']:+.3f} +- {c3d['se']:.3f}  {'PASS' if c3d['passes'] else 'fail'}   ({(time.time()-t1)/60:.1f} min)", flush=True)

    # 5. the bar
    T1 = c1d["passes"]; T2 = bool(c2["passes"] and c3d["passes"]); T3 = bool(pb["net_crossed"] > 0 and pb["net_crossed"] / pb["se"] >= 2); T4 = bool(pb["era2"] > 0 and pb["era2"] / pb["era2_se"] >= 2)
    cc = pr["conc"]; T5 = bool((cc["to_half"] or 0) >= 20 and cc["top1_share"] <= 50); res["bar"] = dict(T1=T1, T2=T2, T3=T3, T4=T4, T5=T5, candidate=bool(T1 and T2 and T3 and T4 and T5))
    print(f"\nTHE BAR (primary set, cap {CAP}, crossed)\n  T1 per-trade gross > C1 p95 by 2 SE      : {T1}\n  T2 book gross > C2 p95 and > C3 p95 2SE   : {T2}   (C2 {c2['passes']}, C3 {c3d['passes']})\n  T3 book net crossed > 0 by 2 SE           : {T3}   ({pb['net_crossed']:+.3f} +- {pb['se']:.3f})\n  T4 era-2 net crossed > 0 by 2 SE          : {T4}   ({pb['era2']:+.3f} +- {pb['era2_se']:.3f})\n  T5 to-half >= 20, top 1% <= 50%            : {T5}   ({cc['to_half']}, {cc['top1_share']:.0f}%)\n  CANDIDATE: {res['bar']['candidate']}")
    S = res["sets"]
    print("\nPREDICTIONS\n" + f"  X-a gross +120..+260, median +40..+120; C1 p50 +20..+60; increment +80..+200 >= 2 SD : gross {pr['gross']:+.1f} median {pr['median']:+.1f}; C1 p50 {c1d['p50']:+.1f}; increment {c1d['increment']:+.1f} ({c1d['z_median']:+.1f} SD)\n"
          + f"  X-b book gross +2.0..+4.0, SE 0.8-1.2, crossed 1.2-2.2, net +0.3..+2.2, passive >= +1.5  : gross {pb['gross']:+.2f} +- {pb['se']:.2f}  crossed {pr['cost_crossed_bar']:.2f}  net {pb['net_crossed']:+.2f}  passive net {pb['net_passive']:+.2f}\n"
          + f"  X-c C2 p50 +0.5..+1.2, p95 +1.5..+2.5; C3 within 0.3 / 0.4 of C2                     : C2 {c2['p50']:+.2f} / {c2['p95']:+.2f};  C3 {c3d['p50']:+.2f} / {c3d['p95']:+.2f}\n"
          + f"  X-d cluster > single by +40..+100; officer > director +20..+60; value hi > lo +30..+80; 10% below primary; sales 0 +- 40 : cluster {S['cluster']['gross']:+.1f} vs single {S['single']['gross']:+.1f}; officer {S['officer_only']['gross']:+.1f} vs director {S['director_only']['gross']:+.1f}; value hi {S['value_hi']['gross']:+.1f} vs lo {S['value_lo']['gross']:+.1f}; 10% {S['tenpct_owner']['gross']:+.1f}; sales short {S['sales_short']['gross']:+.1f} +- {S['sales_short']['se']:.1f}\n"
          + f"  X-e cap 21 per bar >= cap 63; cap 126 below                                       : cap21 {res['robust']['cap21']['gross']:+.2f}  cap63 {pb['gross']:+.2f}  cap126 {res['robust']['cap126']['gross']:+.2f}\n"
          + f"  X-f era2 > 0 and < era1, T4 fails; to-half >= 40, top1% <= 40                    : era1 {pb['era1']:+.2f} era2 {pb['era2']:+.2f}; T4 {T4}; to-half {cc['to_half']} top1% {cc['top1_share']:.0f}%")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (mining fixture only; no holdout read)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) masks, dilation, cluster guard on a toy")
    T, N = 30, 3; sub = pd.DataFrame(dict(t_av=[5, 5, 20], j=[0, 1, 0])); m = mask_of(sub, T, N); assert m.sum() == 3 and m[5, 0] and m[5, 1] and m[20, 0]
    d = dilate(m, 2); assert d[3:8, 0].all() and not d[2, 0] and not d[8, 0] and d[18:23, 0].all() and d.sum() == 15
    print("  ok: 3 events, +-2 dilation covers 15 cells")
    print("== (b) the real events: [F] availability strictly after the filing; the primary filter; the cluster count caps family trusts at 5")
    PREP = _load("d348p", "d348_prep.py"); P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); dates = np.array([str(x)[:10] for x in P["dates"]]); symbols = list(P["symbols"])
    ev = load_events(dates, symbols, elig, T); cl = cluster_flag(ev, dates, T); isP = (ev["kind"] == "P").to_numpy(); assert cl.max() <= (2 * NEAR + 1) * CLUSTER_CAP and (cl[isP] >= 1).all() and (cl[~isP] >= 0).all()
    hy = ev[(ev["symbol"] == "HY") & (ev["kind"] == "P")]; assert hy.empty or cl[ev.index.get_indexer(hy.index)].max() <= 5 * (2 * NEAR + 1), "family-trust cap not applied"
    prim = ev[(ev["kind"] == "P") & ev["elig"] & ~ev["TenPercentOwner"] & (ev["value"] >= VALUE_FLOOR)]; assert (prim["value"] >= VALUE_FLOOR).all() and not prim["TenPercentOwner"].any()
    print(f"  {len(ev):,} filings 2010-2023 on fixture names; primary {len(prim):,}; max distinct-owner count within +-{NEAR} bars {cl.max()} (cap {CLUSTER_CAP}/name-day)")
    print("== (c) C2 at offset 0 is the real mask; C1 pool excludes every name with a purchase within +-5 bars")
    m0 = mask_of(prim, T, N); assert np.array_equal(np.roll(m0, 0, axis=0) & elig, m0 & elig); near = dilate(mask_of(ev[ev["kind"] == "P"], T, N), NEAR); pool = elig & ~near; assert not (pool & m0).any()
    print("  ok")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.run:
        run(a.quick)
    else:
        cmd_selftest()
