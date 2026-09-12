"""D492 -- D490's range-reversion rule with an RSI confirmation (Wilder RSI(14) on continuous five-minute RTH closes; long <= 30, short
>= 70). Cell A = D490's rule + the confirmation (primary); cell B = the confirmation in place of the volume spike. Spec committed in
b512918 BEFORE this file. Reuses D490's simulator, exit table, nulls and summaries unchanged.

    uv run python -u scripts/run_d492_rsi_filter.py --dev
    uv run python -u scripts/run_d492_rsi_filter.py --validate --filter-declared     # only if the development artefact shows the bar cleared for a cell
    uv run python -u scripts/run_d492_rsi_filter.py --selftest
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
D90 = _load("d490r", "run_d490_range_reversion.py"); D66 = D90.D66
RSI_N, RSI_LO, RSI_HI = 14, 30.0, 70.0; SEED = 492
ENDS = np.array([59, 119, 179, 239, 299, 359, 389])      # ADDENDUM: HOURLY RTH buckets (10:29 .. 15:29, and the 15:59 half-bucket); 14 buckets ~ two sessions


# ------------------------------------------------------------------------------------------ RSI on continuous five-minute closes
def wilder_rsi(x, n=RSI_N):
    """Wilder's RSI on a 1-d series of closes (NaN-free): the first average is the simple mean of the first n changes, then alpha = 1/n."""
    x = np.asarray(x, float); d = np.diff(x); up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0); out = np.full(x.size, np.nan)
    if d.size < n:
        return out
    au = up[:n].mean(); ad = dn[:n].mean(); out[n] = 100.0 - 100.0 / (1.0 + au / ad) if ad > 0 else 100.0
    for t in range(n, d.size):
        au = (au * (n - 1) + up[t]) / n; ad = (ad * (n - 1) + dn[t]) / n; out[t + 1] = 100.0 - 100.0 / (1.0 + au / ad) if ad > 0 else 100.0
    return out


def rsi_by_day(d):
    """(n_days x 7) RSI at each hourly bucket end (ENDS), from one continuous series across the loaded sessions in day order (missing
    buckets skipped in the series, NaN in the table)."""
    C = d["C"]; closes = C[:, ENDS]; flat = closes.ravel(); ok = np.isfinite(flat)
    r = np.full(flat.size, np.nan); r[ok] = wilder_rsi(flat[ok]); return r.reshape(closes.shape)


def rsi_at_bar(R_day, e):
    """The RSI of the last COMPLETED bucket at or before bar e."""
    b = int(np.searchsorted(ENDS, e, side="right")) - 1
    return R_day[b] if b >= 0 else np.nan


def triggers_rsi(d, i, side, Hy, Ly, med, R_day, use_spike):
    O, Hh, Ll, C = D90.series(d, i, side); rng_ = Hy - Ly
    if not (rng_ > 0) or (use_spike and np.isnan(med).all()):
        return -1
    for e in range(D90.FIRST_BAR, D90.NBAR - 1):
        c = d["C"][i][e]; P = (c - Ly) / rng_; cond = (P <= D90.LO_P) if side == 1 else (P >= D90.HI_P)
        if not cond:
            continue
        if use_spike:
            v = d["V"][i][e]; m = med[e]
            if not (np.isfinite(m) and m > 0 and v >= D90.SPIKE * m):
                continue
        r = rsi_at_bar(R_day, e)
        if not np.isfinite(r):
            continue
        if (side == 1 and r <= RSI_LO) or (side == -1 and r >= RSI_HI):
            return e
    return -1


def run_rule_rsi(d, mult, R, use_spike, trail=True, offset=1):
    rows = []
    for i in np.flatnonzero(d["trade"]):
        Hy, Ly = D90.day_range(d, i, offset); med = D90.normaliser(d["V"], i)
        if not np.isfinite(Hy):
            continue
        Hr, Lr = D90.day_range(d, i, 1)
        for side in (1, -1):
            e = triggers_rsi(d, i, side, Hy, Ly, med, R[i], use_spike)
            if e < 0:
                continue
            p, jx, typ, mae, mfe, ent, ex = D90.simulate(d, i, side, e, Hy, Ly, trail); c = d["C"][i][e]; P = (c - Lr) / (Hr - Lr) if Hr > Lr else np.nan; m = med[e]
            rows.append(dict(day=d["days"][i], side=side, e=int(e), entry_hhmm=d["hh"][e + 1], exit_hhmm=d["hh"][jx], exit=typ, minutes=int(jx - e), pnl_pts=float(p), gross_usd=float(p * mult), net_usd=float(p * mult - D90.COST), mae_usd=float(mae * mult), mfe_usd=float(mfe * mult),
                             P_at_trigger=float(P), spike=float(d["V"][i][e] / m) if np.isfinite(m) and m > 0 else float("nan"), rsi=float(rsi_at_bar(R[i], e)), open_in_range=bool(Lr <= d["O"][i][0] <= Hr), before_11=bool(d["hh"][e] < "11:00"), entry_bp=float(p / abs(ent) * 1e4)))
    return pd.DataFrame(rows)


def score_cell(d, mult, R, use_spike, cal, label, rng, log=print):
    tr = run_rule_rsi(d, mult, R, use_spike); ab = run_rule_rsi(d, mult, R, use_spike, trail=False); log(f"  {label}: the rule"); S = D90.summarise(tr, cal, mult, label, log); log(f"  {label}: no trailing stop"); A = D90.summarise(ab, cal, mult, label + "-notrail", log)
    if len(tr) < 10:
        return dict(rule=S, ablation=A, trades=int(len(tr)), bar=False), tr
    sp = D90.splits(tr, log); n1 = []
    for off in D90.N1_OFFSETS:
        w = run_rule_rsi(d, mult, R, use_spike, offset=off)
        if len(w) >= 10:
            n1.append(dict(offset=off, trades=int(len(w)), gross_mean=float(w["gross_usd"].mean())))
    n1g = np.array([x["gross_mean"] for x in n1]); n2, tabs = D90.n2_random_entries(d, mult, tr, rng); se95 = D90.p95_se(n2)
    assert all(abs(tabs[(r.day, r.side)][r.e] * mult - r.gross_usd) < 1e-6 for r in tr.itertuples()), "table/scalar disagreement"
    P = S["pooled"]; bar = bool(P["gross_mean"] > np.quantile(n1g, .95) and P["gross_mean"] > np.quantile(n2, .95) + 2 * se95 and P["net_sharpe"] > 0.3)
    log(f"  {label}: N1 wrong-range p50 ${np.median(n1g):+.2f} p95 ${np.quantile(n1g, .95):+.2f}   N2 random entries p50 ${np.median(n2):+.2f} p95 ${np.quantile(n2, .95):+.2f} +- {se95:.2f}   THE BAR: {'CLEARED' if bar else 'not cleared'} (gross ${P['gross_mean']:+.2f}, net Sharpe {P['net_sharpe']:+.2f})")
    return dict(rule=S, ablation=A, splits=sp, N1=dict(offsets=n1, p50=float(np.median(n1g)), p95=float(np.quantile(n1g, .95))), N2=dict(p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95), bar=bar), tr


def run_slice(mode, log=print):
    lo, hi = D90.SLICES[mode]; t0 = time.time(); log(f"D492 -- D490's rule with the RSI confirmation, {mode} {lo}..{hi}\n      spec committed in b512918 BEFORE this ran"); res = {}
    for root in D90.ROOTS:
        d = D90.load_root(root, lo, hi); R = rsi_by_day(d); mult = D90.MULT[root]; cal = pd.Index(d["days"][d["trade"]]); log(f"\n{root}: {int(d['trade'].sum())} full sessions"); res[root] = {}
        for cell, use_spike in (("A", True), ("B", False)):
            out, tr = score_cell(d, mult, R, use_spike, cal, f"cell {cell}", np.random.default_rng(SEED + (cell == "B")), log); res[root][cell] = out; tr.to_csv(REPO / "data" / f"d492_trades_{mode}_{root}_{cell}.csv.gz", index=False, compression="gzip")
    log(f"\n{(time.time()-t0)/60:.1f} min"); return res


def predictions(res, log=print):
    E = res["ES"]; A = E["A"]; B = E["B"]; Ar = A["rule"]; Br = B["rule"]; d90 = json.loads((REPO / "data" / "d490_range_reversion_dev.json").read_text())["ES"]["rule"]
    log("\nPREDICTIONS (development, ES)")
    log(f"  X-a RSI removes 50-70% of D490's trades (long 491 -> 150-250)                 : long {Ar.get('long', {}).get('trades', 0)} (-{100*(1-Ar.get('long', {}).get('trades', 0)/d90['long']['trades']):.0f}%), pooled {Ar.get('pooled', {}).get('trades', 0)} vs {d90['pooled']['trades']}")
    log(f"  X-b sign unchanged: A long -$6..+$2, short -$6..0, net Sharpe -0.8..0            : long ${Ar.get('long', {}).get('gross_mean', float('nan')):+.2f}, short ${Ar.get('short', {}).get('gross_mean', float('nan')):+.2f}, Sharpe {Ar.get('pooled', {}).get('net_sharpe', float('nan')):+.2f}")
    log(f"  X-c B better than A by $2-6, not above N1 p95, Sharpe -0.4..+0.2               : B ${Br.get('pooled', {}).get('gross_mean', float('nan')):+.2f} vs A ${Ar.get('pooled', {}).get('gross_mean', float('nan')):+.2f}; N1 p95 ${B.get('N1', {}).get('p95', float('nan')):+.2f}; Sharpe {Br.get('pooled', {}).get('net_sharpe', float('nan')):+.2f}")
    log(f"  X-d bar not cleared; no validation read                                          : A {'CLEARED' if A['bar'] else 'not cleared'}, B {'CLEARED' if B['bar'] else 'not cleared'}")


def main_mode(mode, flag):
    if mode == "validate":
        if not flag:
            print("REFUSED: --validate touches 2021-2023; re-run with --filter-declared."); return 2
        dev = json.loads((REPO / "data" / "d492_rsi_filter_dev.json").read_text()); cleared = [(r, c) for r in dev for c in ("A", "B") if dev[r][c].get("bar")]
        if not cleared:
            print("REFUSED: the development artefact shows no cell cleared the bar; D492 declared the validation read only for a cell that did."); return 3
        print(f"cells that cleared in development: {cleared}")
    res = run_slice(mode)
    if mode == "dev":
        predictions(res)
    (REPO / "data" / f"d492_rsi_filter_{mode}.json").write_text(json.dumps(res, indent=1, default=float)); print(f"wrote data/d492_rsi_filter_{mode}.json"); return 0


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) Wilder RSI matches a pandas EWM reference after the seed; a monotone rise reads 100, a monotone fall 0")
    rng = np.random.default_rng(1); x = 100 + np.cumsum(rng.normal(0, 1, 300)); r = wilder_rsi(x); d = pd.Series(np.diff(x)); up = d.clip(lower=0); dn = (-d).clip(lower=0)
    au = up.ewm(alpha=1 / RSI_N, adjust=False).mean(); ad = dn.ewm(alpha=1 / RSI_N, adjust=False).mean()          # same recursion once seeded; compare far from the seed
    ref = 100 - 100 / (1 + au / ad); assert abs(r[250] - ref.iloc[249]) < 0.5 and abs(r[299] - ref.iloc[298]) < 0.5, (r[250], ref.iloc[249])
    assert wilder_rsi(np.arange(40.0))[-1] == 100.0 and wilder_rsi(np.arange(40.0)[::-1])[-1] == 0.0 and np.isnan(wilder_rsi(x)[:RSI_N]).all()
    print(f"  ok: RSI at t=250 {r[250]:.2f} vs reference {ref.iloc[249]:.2f}; first {RSI_N} NaN")
    print("== (b) the hourly bucket map: bar 59 -> bucket 0, bar 60 -> 0, bar 119 -> 1, bar 389 -> 6; bar 58 undefined")
    R = np.arange(7.0); assert rsi_at_bar(R, 59) == 0 and rsi_at_bar(R, 60) == 0 and rsi_at_bar(R, 119) == 1 and rsi_at_bar(R, 389) == 6 and np.isnan(rsi_at_bar(R, 58)); print("  ok")
    print("== (c) on a synthetic day the long fires only when the hourly RSI is oversold: a flat day at the bottom of the range after rising days (RSI mid) is refused; a fall into it after falling days (RSI low) is taken; cell B ignores the spike")
    n = D90.NBAR; vol = np.full(n, 100.0); vol[380:] = 500.0
    cases = (("refused", np.linspace(90, 110, n), np.full(n, 90.5)), ("taken", np.full(n, 100.0), np.linspace(105, 90.5, n)))      # (prior days' path, today's path): rising days then a flat day at the range bottom -> RSI mid; flat days then a fall to far below the range (P < 0 counts) -> RSI low
    for expect, prev, path in cases:
        d = D90.make_d([prev] * 21 + [path], [np.full(n, 100.0)] * 21 + [vol], None); d["trade"][:] = False; d["trade"][-1] = True; d["days"] = np.array([f"2018-{1 + k // 28:02d}-{1 + k % 28:02d}" for k in range(22)])
        Rt = rsi_by_day(d); i = 21; Hy, Ly = D90.day_range(d, i, 1); med = D90.normaliser(d["V"], i); e = triggers_rsi(d, i, 1, Hy, Ly, med, Rt[i], True); eb = triggers_rsi(d, i, 1, Hy, Ly, med, Rt[i], False); e90 = D90.triggers(d, i, 1, Hy, Ly, med)
        r_at = rsi_at_bar(Rt[i], e90) if e90 >= 0 else float("nan")
        if expect == "refused":
            assert e90 >= 0 and e < 0 and eb < 0, (e90, e, eb, r_at)
        else:
            assert e90 >= 0 and e == e90 and eb <= e90 and eb >= 0, (e90, e, eb, r_at)
        print(f"  ok: {expect}: D490 trigger {e90}, RSI there {r_at:.1f}, cell A {e}, cell B {eb}")
    print("== (d) the validation guard refuses without the flag and without a cleared cell")
    assert main_mode("validate", False) == 2; print("  ok")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--dev", action="store_true"); g.add_argument("--validate", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--filter-declared", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.dev:
        sys.exit(main_mode("dev", True))
    else:
        sys.exit(main_mode("validate", a.filter_declared))
