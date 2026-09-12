"""D457 -- the 8-K item atlas with returns: 17 cells x {all, pure} x both sides through the D345 kernel at cap 10, the state-matched
control (C1) and the exact rotation of each cell's calendar (C2) on every cell. Spec committed in 0aad00a BEFORE this file. In-sample
2010-2023; the 2024-2026 slice stays unread; no holdout.

    uv run python -u scripts/run_d457_8k_atlas.py --run [--quick]
    uv run python -u scripts/run_d457_8k_atlas.py --selftest

Lenses: per trade = hedged pnl per trade (bp); book = the DEPLOYED mean of book_dep_x over bars on which the cell holds anything, with a
monthly block-bootstrap SE over those bars. The kernel is symmetric under 'cap' exits (short gross == -long gross, asserted), so C1 is
drawn on the long side and read two-sided; a cell's favoured side is the sign of (long gross - C1 median).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R46 = _load("d446", "run_d446_issuance_book.py"); R56 = _load("d456", "run_d456_8k_atlas_stage0.py")
EVENTS = R56.EVENTS; OUT = REPO / "data" / "d457_8k_atlas.json"; START, END = "2010-01-01", R56.END
CELLS = ("1.01", "1.02", "2.01", "2.02", "2.03", "2.05", "2.06", "3.01", "3.02", "3.03", "4.01", "5.02", "5.03", "5.07", "8.01"); SUB300 = ("2.04", "4.02")
CAP, CAP2, NEAR = 10, 3, 5; N_DRAW_ALL, N_DRAW_PURE, ROT_STEP, SEED = 100, 50, 21, 457; CAPTURE, CHASE_BP = 0.66, 9.0
EXPECTED_C1, EXPECTED_BOTH = 17 * 2 * 0.025, 17 * 2 * 0.025 * 0.05


# ------------------------------------------------------------------------------------------ events -> masks
def load_events(dates, symbols, elig, T):
    fix = pd.to_datetime(dates); sym_i = {s: i for i, s in enumerate(symbols)}
    df = pd.read_csv(EVENTS, dtype={"symbol": str, "filing": str, "items": str, "accession": str}); df["items"] = df["items"].fillna("")
    df = df[(~df["unread"].astype(bool)) & (df["filing"] >= START) & (df["filing"] <= END)].copy()
    df["t_av"] = np.searchsorted(fix, pd.to_datetime(df["filing"]), side="right"); df = df[df["t_av"] < T]; df["j"] = df["symbol"].map(sym_i); df = df[df["j"].notna()]; df["j"] = df["j"].astype(int)
    assert all(dates[t] > f for t, f in zip(df["t_av"], df["filing"])), "[F] an availability bar on or before its filing date"
    df["elig"] = [bool(elig[t, j]) for t, j in zip(df["t_av"], df["j"])]; df = df[df["elig"]]
    parsed = df["items"].map(R56.parse_items); df["modern"] = [m for m, _ in parsed]; df["pure"] = df["modern"].map(lambda m: [x for x in m if x != "9.01"]).map(lambda m: m[0] if len(m) == 1 else "")
    return df


def mask_of(sub, T, N):
    m = np.zeros((T, N), bool); m[sub["t_av"].to_numpy(), sub["j"].to_numpy()] = True; return m


def dilate(m, k):
    out = m.copy()
    for s in range(1, k + 1):
        out[s:] |= m[:-s]; out[:-s] |= m[s:]
    return out


# ------------------------------------------------------------------------------------------ lenses
def deployed(r, dates, R37):
    x = np.asarray(r["book_dep_x"], float); held = np.isfinite(x)
    if held.sum() < 5:
        return dict(mean=float("nan"), se=float("nan"), bars=int(held.sum()))
    se, m = R37.block_boot(x[held] * 1e4, dates[held]); return dict(mean=m, se=se, bars=int(held.sum()))


def real_cell(V59, R37, P, elig, mask, cap, dates, SC):
    out = {}
    for name, side in (("long", 0), ("short", 1)):
        r = R46.simulate(V59, P, mask, SC, cap, side, None); tb = V59.trade_block(P, r, elig, side, False); pnl = V59.V47.pnl_bp(r); dep = deployed(r, dates, R37)
        out[name] = dict(trades=tb["trades"], gross=tb["mean_bp"], median=tb["median_bp"], se=float(pnl.std(ddof=1) / np.sqrt(pnl.size)) if pnl.size > 1 else float("nan"), two_c=tb["two_c"]["PUB"], borrow=tb.get("borrow", {}).get("mean_bp", 0.0) if side == 1 else 0.0,
                         dep_mean=dep["mean"], dep_se=dep["se"], dep_bars=dep["bars"]); out[name]["r"] = r
    assert abs(out["long"]["gross"] + out["short"]["gross"]) < 1e-6, "[SYM] the kernel is not symmetric under the cap exit"
    return out


# ------------------------------------------------------------------------------------------ the study
def run(quick=False):
    t0 = time.time(); print("D457 -- the 8-K item atlas with returns: 17 cells, both sides, cap 10, C1 and C2 on every cell\n      the bar was committed in 0aad00a BEFORE this ran; 2010-2023; the 2024-2026 slice unread; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py"); R37 = _load("d437", "run_d437_stage1.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]).copy(); dates = np.array([str(x)[:10] for x in P["dates"]]); symbols = list(P["symbols"])
    t_end = int(np.searchsorted(dates, END, side="right")); elig[t_end:] = False; SC = np.full((T, N), 50.0)
    idx = A92.eligible_index(elig); mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, SC, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", SC); assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    df = load_events(dates, symbols, elig, T); any8k = mask_of(df, T, N); pool = elig & ~dilate(any8k, NEAR); cells_sh = [R46.shift(c, elig) for c in R46.cells_of(A92, P, elig)]
    print(f"  [K] kernel probe;  [F] availability strictly after filing;  {len(df):,} eligible 8-K filings 2010-2023;  C1 pool excludes any name with an 8-K within +-{NEAR} bars")
    n_all, n_pure, step = (10, 5, 42) if quick else (N_DRAW_ALL, N_DRAW_PURE, ROT_STEP); rng = np.random.default_rng(SEED); offs = list(range(step, T - step, step))
    res = dict(spec="0aad00a", n_filings=int(len(df)), cells={}, family={}, quick=quick); t1 = time.time()
    for it in CELLS + SUB300:
        for ver in ("all", "pure"):
            sub = df[df["modern"].map(lambda m, it=it: it in m)] if ver == "all" else df[df["pure"] == it]
            if len(sub) < 30:
                res["cells"][f"{it}|{ver}"] = dict(n_filings=int(len(sub)), skipped=True); continue
            mask = mask_of(sub, T, N); real = real_cell(V59, R37, P, elig, mask, CAP, dates, SC); r3 = real_cell(V59, R37, P, elig, mask, CAP2, dates, SC)
            # C1 on the long side, read two-sided
            ev = R46.entry_mask(real["long"]["r"], T, N); gs = []
            for d in range(n_all if ver == "all" else n_pure):
                rr = R46.simulate(V59, P, R46.c1_mask(R37, rng, ev, cells_sh, pool), SC, CAP, 0, None); gs.append(float(V59.V47.pnl_bp(rr).mean()))
            gs = np.array(gs); q = np.quantile(gs, [.025, .5, .975]); sd = float(gs.std(ddof=1)); mc = sd / np.sqrt(gs.size); x = real["long"]["gross"]
            fav = "long" if x >= q[1] else "short"; clears1 = bool(x > q[2] + 2 * mc) if fav == "long" else bool(x < q[0] - 2 * mc); z = (x - q[1]) / sd if sd > 0 else float("nan")
            c = dict(n_filings=int(len(sub)), trades=real["long"]["trades"], gross_long=x, median_long=real["long"]["median"], se_trade=real["long"]["se"], favoured=fav, gross_fav=abs(x) if fav == "short" else x,
                     two_c=real[fav]["two_c"], borrow=real[fav]["borrow"], net_crossed=real[fav]["gross"] - real[fav]["two_c"] - real[fav]["borrow"], net_passive=real[fav]["gross"] - real[fav]["two_c"] * (1 - CAPTURE) - CHASE_BP - real[fav]["borrow"],
                     dep_long=real["long"]["dep_mean"], dep_se=real["long"]["dep_se"], dep_bars=real["long"]["dep_bars"], cap3_gross_long=r3["long"]["gross"], cap3_dep_long=r3["long"]["dep_mean"],
                     C1=dict(n=int(gs.size), p025=float(q[0]), p50=float(q[1]), p975=float(q[2]), sd=sd, mc_se=float(mc), z=float(z), clears=clears1))
            # C2 on 'all': the calendar rolled, exact on the grid, deployed mean on the long side
            if ver == "all":
                rot = []
                for k in offs:
                    rr = R46.simulate(V59, P, np.roll(mask, k, axis=0) & elig, SC, CAP, 0, None); rot.append(deployed(rr, dates, R37)["mean"])
                rot = np.array(rot); rot = rot[np.isfinite(rot)]; q2 = np.quantile(rot, [.025, .5, .975]); dl = real["long"]["dep_mean"]
                clears2 = bool(dl > q2[2]) if fav == "long" else bool(dl < q2[0]); c["C2"] = dict(n=int(rot.size), p025=float(q2[0]), p50=float(q2[1]), p975=float(q2[2]), clears=clears2); c["clears_both"] = bool(clears1 and clears2 and it in CELLS)
            res["cells"][f"{it}|{ver}"] = c
            print(f"  {it} {ver:4s} n {c['n_filings']:6,} tr {c['trades']:6,} | long {x:+7.1f} (med {c['median_long']:+6.1f})  C1 [{q[0]:+6.1f}, {q[1]:+6.1f}, {q[2]:+6.1f}] z {z:+.2f} {'C1' if clears1 else '--'} | fav {fav:5s} 2c {c['two_c']:5.1f} net {c['net_crossed']:+6.1f} | dep {dl if ver == 'all' else c['dep_long']:+6.2f}/bar +- {c['dep_se']:.2f}"
                  + (f"  C2 [{q2[0]:+5.2f}, {q2[1]:+5.2f}, {q2[2]:+5.2f}] {'C2' if clears2 else '--'}  {'*** CLEARS BOTH' if c['clears_both'] else ''}" if ver == "all" else "") + f"   ({(time.time()-t1)/60:.1f} min)", flush=True)
    A = {k: v for k, v in res["cells"].items() if k.endswith("|all") and not v.get("skipped")}; n_c1 = sum(v["C1"]["clears"] for k, v in A.items() if k.split("|")[0] in CELLS); n_both = sum(v.get("clears_both", False) for v in A.values())
    both = [k.split("|")[0] + ":" + v["favoured"] for k, v in A.items() if v.get("clears_both")]; c1only = [k.split("|")[0] + ":" + v["favoured"] for k, v in A.items() if v["C1"]["clears"] and k.split("|")[0] in CELLS]
    res["family"] = dict(n_cells=len(CELLS), clears_C1=n_c1, clears_both=n_both, expected_C1_by_chance=EXPECTED_C1, expected_both_by_chance=EXPECTED_BOTH, cleared=both, cleared_C1=c1only)
    print(f"\nTHE FAMILY: {n_c1} of 17 cells clear C1 (chance {EXPECTED_C1:.2f}); {n_both} clear BOTH (chance {EXPECTED_BOTH:.2f}): {both}\n  C1 clears: {c1only}")
    g = lambda it, k: A.get(f"{it}|all", {}).get(k, float("nan")); gf = lambda it: A.get(f"{it}|all", {}).get("gross_fav", float("nan"))
    print("\nPREDICTIONS\n" + f"  X-a 2-4 cells clear both, all short, from 2.06/3.01/4.01/3.02/2.05; no long clears : {n_both} -> {both}\n"
          + f"  X-b short gross cap10: 2.06 +60..+200, 3.01 +80..+250, 4.01 +40..+150, 3.02 +40..+120; C1 p50 within +-15 : 2.06 {-g('2.06','gross_long'):+.0f}  3.01 {-g('3.01','gross_long'):+.0f}  4.01 {-g('4.01','gross_long'):+.0f}  3.02 {-g('3.02','gross_long'):+.0f};  max |C1 p50| {max(abs(v['C1']['p50']) for v in A.values()):.0f}\n"
          + f"  X-c 2.02 |g| < 20; 5.02 -10..-40; 8.01/1.01/5.07/5.03 |g| < 15; 2.01 0..+30; 1.02 -20..-80 : 2.02 {g('2.02','gross_long'):+.0f}  5.02 {g('5.02','gross_long'):+.0f}  8.01 {g('8.01','gross_long'):+.0f}  1.01 {g('1.01','gross_long'):+.0f}  5.07 {g('5.07','gross_long'):+.0f}  5.03 {g('5.03','gross_long'):+.0f}  2.01 {g('2.01','gross_long'):+.0f}  2.03 {g('2.03','gross_long'):+.0f}  1.02 {g('1.02','gross_long'):+.0f}\n"
          + f"  X-d C2 p50 within +-0.5 on every cell                                        : max |C2 p50| {max(abs(v['C2']['p50']) for v in A.values() if 'C2' in v):.2f}\n"
          + f"  X-e cleared cells: 2c 80-130, net crossed > 0 on at most two, passive > 0 on all : " + "; ".join(f"{k.split('|')[0]} 2c {v['two_c']:.0f} net {v['net_crossed']:+.0f} passive {v['net_passive']:+.0f}" for k, v in A.items() if v.get("clears_both")) + "\n"
          + f"  X-f cap3 >= 60% of cap10 on cleared; pure 2.06 / 2.05 stronger than all          : " + "; ".join(f"{k.split('|')[0]} cap3 {v['cap3_gross_long']:+.0f} vs cap10 {v['gross_long']:+.0f}" for k, v in A.items() if v.get("clears_both")) + f";  2.06 pure {res['cells'].get('2.06|pure', {}).get('gross_long', float('nan')):+.0f} vs all {g('2.06','gross_long'):+.0f}; 2.05 pure {res['cells'].get('2.05|pure', {}).get('gross_long', float('nan')):+.0f} vs all {g('2.05','gross_long'):+.0f}")
    for v in res["cells"].values():
        v.pop("r", None)
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (2010-2023 only; the 2024-2026 slice unread; no holdout)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) deployed mean on a toy result; dilation; the pure flag")
    dates = np.array([str(d.date()) for d in pd.bdate_range("2015-01-01", "2015-12-31")]); x = np.full(dates.size, np.nan); x[10:20] = 0.001; x[100:105] = -0.002
    R37 = _load("d437", "run_d437_stage1.py"); d = deployed({"book_dep_x": x}, dates, R37); assert d["bars"] == 15 and abs(d["mean"] - (10 * 10 - 5 * 20) / 15) < 1e-9
    m = np.zeros((30, 2), bool); m[5, 0] = True; assert dilate(m, 2)[3:8, 0].all() and dilate(m, 2).sum() == 5
    print(f"  deployed mean {d['mean']:+.3f} bp over 15 held bars; dilation ok")
    print("== (b) the real events: [F]; the kernel's short == -long on one small cell [SYM]; the C1 pool excludes every 8-K name")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py"); P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]).copy(); dates = np.array([str(x)[:10] for x in P["dates"]]); symbols = list(P["symbols"])
    t_end = int(np.searchsorted(dates, END, side="right")); elig[t_end:] = False; df = load_events(dates, symbols, elig, T); SC = np.full((T, N), 50.0)
    sub = df[df["modern"].map(lambda m: "2.06" in m)]; real = real_cell(V59, R37, P, elig, mask_of(sub, T, N), CAP, dates, SC)
    any8k = mask_of(df, T, N); pool = elig & ~dilate(any8k, NEAR); assert not (pool & any8k).any()
    print(f"  {len(df):,} eligible filings; 2.06 all: {real['long']['trades']} trades, long {real['long']['gross']:+.1f} == -short {real['short']['gross']:+.1f}; pool excludes 8-K names")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.run:
        run(a.quick)
    else:
        cmd_selftest()
