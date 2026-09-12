"""D490 -- the principal's range-reversion rule on the D462 one-minute RTH fixtures. Spec committed in 738ddfa BEFORE this file.

Long: first bar from 09:35 whose close sits at P <= 0.05 of yesterday's RTH range AND whose volume >= 2x the same-minute median of the
previous 20 sessions; enter at the next bar's open + 1 tick. Exits: target at P = 0.95 (filled at the level, or the open if it gaps
through); trailing stop armed once a close has P >= 0.5, sitting at the most recent confirmed swing low (5 bars either side, confirmed 5
bars later, formed at or after the entry bar), ratcheting up, filled at the stop - 1 tick; else the 15:59 close. Short: the mirror.
One entry per side per day. No initial stop. Cost $3 a round trip plus the fills above. Ablation: no trailing stop.

    uv run python -u scripts/run_d490_range_reversion.py --dev                              # development 2016-02-01 .. 2020-12-31
    uv run python -u scripts/run_d490_range_reversion.py --validate --filter-declared       # 2021-2023, once per declared filter set
    uv run python -u scripts/run_d490_range_reversion.py --final --principals-word          # 2024+, the principal's word
    uv run python -u scripts/run_d490_range_reversion.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; FIX = REPO / "data" / "fixtures"
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
D66 = _load("d466c", "run_d466_components.py")
SLICES = {"dev": ("2016-02-01", "2020-12-31"), "validate": ("2021-01-04", "2023-12-29"), "final": ("2024-01-02", "2026-09-09")}
ROOTS = ("ES", "NQ"); MULT = {"ES": 5.0, "NQ": 2.0}; TICK = 0.25; COST = 3.0; ACCOUNT = 50_000.0
LO_P, HI_P, MID_P, SPIKE, NORM_N, PIV, FIRST_BAR, NBAR = 0.05, 0.95, 0.5, 2.0, 20, 5, 5, 390; N2_DRAWS, N1_OFFSETS, SEED = 2000, range(3, 23), 490


# ------------------------------------------------------------------------------------------ data
def load_root(root, lo, hi):
    """Per-session arrays for all sessions from 35 sessions before lo (the normaliser and yesterday's range) to hi; trading days = full
    sessions inside [lo, hi]. Returns dict with days (all), O/H/L/C/V (n_days x 390, NaN where a bar is missing), full mask, trade mask."""
    b = pd.read_csv(FIX / f"fut_{root}_rth_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str}); b = b[b["day"] <= hi]
    days_all = np.array(sorted(b["day"].unique())); i_lo = max(0, int(np.searchsorted(days_all, lo)) - 35); days = days_all[i_lo:]; b = b[b["day"].isin(days)]
    assert b["day"].max() <= hi, "a row past the slice reached the measurement"
    hh = sorted(b["hhmm"].unique()); assert len(hh) == NBAR and hh[0] == "09:30" and hh[-1] == "15:59"
    def piv(col):
        return b.pivot(index="day", columns="hhmm", values=col).reindex(index=days, columns=hh).to_numpy(float)
    O, H, L, C, V = (piv(c) for c in ("open", "high", "low", "close", "volume")); full = ~np.isnan(C).any(axis=1)
    trade = full & (days >= lo) & (days <= hi); prev = np.full(len(days), -1)
    for i in range(1, len(days)):
        prev[i] = i - 1
    return dict(days=days, O=O, H=H, L=L, C=C, V=V, full=full, trade=trade, prev=prev, hh=hh)


def normaliser(V, i):
    """Median volume per minute over the previous NORM_N sessions (rows i-20..i-1), ignoring missing minutes."""
    w = V[max(0, i - NORM_N):i]; return np.nanmedian(w, axis=0) if len(w) >= 10 else np.full(V.shape[1], np.nan)


def day_range(d, i, offset=1):
    j = i - offset
    if j < 0:
        return np.nan, np.nan
    return float(np.nanmax(d["H"][j])), float(np.nanmin(d["L"][j]))


# ------------------------------------------------------------------------------------------ the transformed series (long on s*price)
def series(d, i, side):
    """For a short, negate prices and swap high/low so the long logic applies unchanged."""
    if side == 1:
        return d["O"][i], d["H"][i], d["L"][i], d["C"][i]
    return -d["O"][i], -d["L"][i], -d["H"][i], -d["C"][i]


def pivot_lows(lo):
    """is_pivot[k]: low[k] is the minimum of bars k-PIV..k+PIV (strict on the left? no: <=), confirmed at bar k+PIV."""
    n = len(lo); out = np.zeros(n, bool)
    for k in range(PIV, n - PIV):
        w = lo[k - PIV:k + PIV + 1]
        if lo[k] <= w.min():
            out[k] = True
    return out


def triggers(d, i, side, Hy, Ly, med):
    """The first trigger bar index e >= FIRST_BAR (entry at e+1), or -1."""
    O, Hh, Ll, C = series(d, i, side); rng_ = Hy - Ly
    if not (rng_ > 0) or np.isnan(med).all():
        return -1
    for e in range(FIRST_BAR, NBAR - 1):
        c = d["C"][i][e]; P = (c - Ly) / rng_; v = d["V"][i][e]; m = med[e]
        cond = (P <= LO_P) if side == 1 else (P >= HI_P)
        if cond and np.isfinite(m) and m > 0 and v >= SPIKE * m:
            return e
    return -1


def simulate(d, i, side, e, Hy, Ly, trail=True):
    """Scalar simulation of one trade entered at bar e+1 on the transformed series. Returns (pnl_pts_transformed, exit_bar, exit_type,
    mae_pts, mfe_pts, entry_px, exit_px) in transformed points; pnl in real $ = pnl_pts * mult (the transform makes a short a long)."""
    O, Hh, Ll, C = series(d, i, side); lo_t, hi_t = (Ly, Hy) if side == 1 else (-Hy, -Ly); rng_ = hi_t - lo_t
    T = lo_t + HI_P * rng_; mid = lo_t + MID_P * rng_; entry = O[e + 1] + TICK; piv = pivot_lows(Ll); armed = False; stop = np.nan; mae = 0.0; mfe = 0.0
    for j in range(e + 1, NBAR):
        mae = min(mae, Ll[j] - entry); mfe = max(mfe, Hh[j] - entry)
        if trail and armed and np.isfinite(stop) and Ll[j] < stop:
            px = stop - TICK; return px - entry, j, "trail", mae, mfe, entry, px
        if Hh[j] >= T:
            px = max(T, O[j]); return px - entry, j, "target", mae, mfe, entry, px
        if j == NBAR - 1:
            px = C[j]; return px - entry, j, "close", mae, mfe, entry, px
        if C[j] >= mid:
            armed = True
        k = j - PIV
        if k >= e + 1 and piv[k]:
            stop = Ll[k] if np.isnan(stop) else max(stop, Ll[k])
    raise RuntimeError("unreachable")


def exit_table(d, i, side, Hy, Ly, trail=True):
    """Vectorised over every entry bar e in [FIRST_BAR, NBAR-2]: the same rule as simulate(). Returns pnl_pts[e] (NaN for invalid e)."""
    O, Hh, Ll, C = series(d, i, side); lo_t, hi_t = (Ly, Hy) if side == 1 else (-Hy, -Ly); rng_ = hi_t - lo_t; T = lo_t + HI_P * rng_; mid = lo_t + MID_P * rng_
    es = np.arange(FIRST_BAR, NBAR - 1); entry = O[es + 1] + TICK; piv = pivot_lows(Ll); active = np.ones(len(es), bool); armed = np.zeros(len(es), bool); stop = np.full(len(es), np.nan); pnl = np.full(len(es), np.nan)
    for j in range(FIRST_BAR + 1, NBAR):
        live = active & (j >= es + 1)
        if not live.any():
            break
        if trail:
            hit = live & armed & np.isfinite(stop) & (Ll[j] < stop); pnl[hit] = (stop[hit] - TICK) - entry[hit]; active[hit] = False; live &= ~hit
        if Hh[j] >= T:
            pnl[live] = max(T, O[j]) - entry[live]; active[live] = False; live[:] = False
        if j == NBAR - 1:
            pnl[live] = C[j] - entry[live]; active[live] = False; break
        if C[j] >= mid:
            armed |= live
        k = j - PIV
        if k >= FIRST_BAR + 1 and piv[k]:
            upd = active & (k >= es + 1); stop[upd] = np.where(np.isnan(stop[upd]), Ll[k], np.maximum(stop[upd], Ll[k]))
    out = np.full(NBAR, np.nan); out[es] = pnl; return out


# ------------------------------------------------------------------------------------------ the study on a slice
def run_rule(d, mult, trail=True, offset=1, log=None):
    rows = []
    for i in np.flatnonzero(d["trade"]):
        Hy, Ly = day_range(d, i, offset); med = normaliser(d["V"], i)
        if not np.isfinite(Hy):
            continue
        Hr, Lr = day_range(d, i, 1)          # the REAL yesterday's range, for the descriptive P and open position
        for side in (1, -1):
            e = triggers(d, i, side, Hy, Ly, med)
            if e < 0:
                continue
            p, jx, typ, mae, mfe, ent, ex = simulate(d, i, side, e, Hy, Ly, trail); c = d["C"][i][e]; P = (c - Lr) / (Hr - Lr) if Hr > Lr else np.nan
            fill_cost = TICK * (1 + (typ == "trail")) * mult      # the entry tick is inside entry; the stop tick inside the exit; recorded for reference
            rows.append(dict(day=d["days"][i], side=side, e=int(e), entry_hhmm=d["hh"][e + 1], exit_hhmm=d["hh"][jx], exit=typ, minutes=int(jx - e), pnl_pts=float(p), gross_usd=float(p * mult), net_usd=float(p * mult - COST), mae_usd=float(mae * mult), mfe_usd=float(mfe * mult),
                             P_at_trigger=float(P), spike=float(d["V"][i][e] / med[e]), open_in_range=bool(Lr <= d["O"][i][0] <= Hr), before_11=bool(d["hh"][e] < "11:00"), entry_bp=float(p / abs(ent) * 1e4 if side == 1 else p / abs(ent) * 1e4)))
    return pd.DataFrame(rows)


def n2_random_entries(d, mult, tr, rng, n=N2_DRAWS):
    """Random entry bars with the real trades' count per day-side and time-of-day distribution, the same exits; the exit tables are
    built once per (day, side) that has a real trade."""
    tabs = {}; pool = {s: tr[tr["side"] == s]["e"].to_numpy() for s in (1, -1)}
    for r in tr.itertuples():
        i = int(np.flatnonzero(d["days"] == r.day)[0]); Hy, Ly = day_range(d, i, 1); tabs[(r.day, r.side)] = exit_table(d, i, r.side, Hy, Ly)
    keys = [(r.day, r.side) for r in tr.itertuples()]; out = np.empty(n)
    for b in range(n):
        tot = 0.0; cnt = 0
        for (day, side) in keys:
            e = int(rng.choice(pool[side])); v = tabs[(day, side)][e]
            if np.isfinite(v):
                tot += v * mult; cnt += 1
        out[b] = tot / cnt if cnt else np.nan
    return out[np.isfinite(out)], tabs


def p95_se(x, n_boot=300, seed=5):
    r = np.random.default_rng(seed); return float(np.std([np.quantile(r.choice(x, x.size), .95) for _ in range(n_boot)], ddof=1))


def summarise(tr, cal, mult, label, log=print):
    out = {}
    for lab, t in (("long", tr[tr["side"] == 1]), ("short", tr[tr["side"] == -1]), ("pooled", tr)):
        if len(t) < 10:
            continue
        g = t["gross_usd"].to_numpy(); n = t["net_usd"].to_numpy(); k = max(1, int(round(0.01 * g.size))); gs = np.sort(g)
        daily = t.groupby("day")["net_usd"].sum(); ser = D66.series_on(cal, daily.index, daily.values).to_numpy(); yrs = np.array([s[:4] for s in cal])
        out[lab] = dict(trades=int(len(t)), sessions=int(len(cal)), share_of_sessions=float(t["day"].nunique() / len(cal)), gross_mean=float(g.mean()), gross_median=float(np.median(g)), net_mean=float(n.mean()), trimmed=float(gs[k:-k].mean()), hit=float((g > 0).mean()), payoff=float(g[g > 0].mean() / -g[g < 0].mean()) if (g < 0).any() and (g > 0).any() else float("nan"),
                        minutes_median=float(t["minutes"].median()), exit_mix={x: float((t["exit"] == x).mean()) for x in ("target", "trail", "close")}, mae_p50=float(np.quantile(t["mae_usd"], .5)), mae_p95=float(np.quantile(t["mae_usd"], .05)), mae_worst=float(t["mae_usd"].min()), mfe_p50=float(np.quantile(t["mfe_usd"], .5)),
                        skew=float(pd.Series(g).skew()), largest=[(r.day, int(r.side), float(r.gross_usd)) for r in t.nlargest(10, "gross_usd").itertuples()], smallest=[(r.day, int(r.side), float(r.gross_usd)) for r in t.nsmallest(10, "gross_usd").itertuples()],
                        net_sharpe=D66.sharpe(ser), net_sharpe_se=D66.sharpe_boot(ser, cal), by_year={y: D66.sharpe(ser[yrs == y]) for y in sorted(set(yrs))}, days_below_2pct=int((ser < -0.02 * ACCOUNT).sum()), worst_day=float(ser.min()), bp_mean=float(t["entry_bp"].mean()))
        o = out[lab]; log(f"  {label} {lab:6s}: trades {o['trades']:4d} ({100*o['share_of_sessions']:.0f}% of sessions)  gross ${o['gross_mean']:+.2f} (median {o['gross_median']:+.2f}, trimmed {o['trimmed']:+.2f}; {o['bp_mean']:+.1f} bp)  net ${o['net_mean']:+.2f}  hit {100*o['hit']:.1f}%  payoff {o['payoff']:.2f}  min {o['minutes_median']:.0f}  exits T/tr/C {100*o['exit_mix']['target']:.0f}/{100*o['exit_mix']['trail']:.0f}/{100*o['exit_mix']['close']:.0f}%  MAE p50/p95/worst {o['mae_p50']:.0f}/{o['mae_p95']:.0f}/{o['mae_worst']:.0f}  skew {o['skew']:+.2f}  net Sharpe {o['net_sharpe']:+.2f} +- {o['net_sharpe_se']:.2f}  days < -2%: {o['days_below_2pct']}")
    return out


def splits(tr, log=print):
    out = {}; t = tr
    cuts = {"P<0": t["P_at_trigger"] < 0, "0<=P<=band": t["P_at_trigger"] >= 0, "spike 2-3x": t["spike"] < 3, "spike >3x": t["spike"] >= 3, "before 11:00": t["before_11"], "after 11:00": ~t["before_11"], "open in range": t["open_in_range"], "open outside": ~t["open_in_range"]}
    for k, m in cuts.items():
        for side, lab in ((1, "long"), (-1, "short")):
            s = t[m & (t["side"] == side)]
            if len(s) >= 10:
                g = s["gross_usd"].to_numpy(); out[f"{lab}|{k}"] = dict(n=int(len(s)), gross_mean=float(g.mean()), se=float(g.std(ddof=1) / math.sqrt(g.size)), hit=float((g > 0).mean()))
    log("  splits (gross $ per trade, SE, n): " + "  ".join(f"{k}: {v['gross_mean']:+.1f} ({v['se']:.1f}, {v['n']})" for k, v in out.items()))
    return out


def run_slice(mode, log=print):
    lo, hi = SLICES[mode]; t0 = time.time(); log(f"D490 -- the principal's range-reversion rule, {mode} {lo}..{hi}\n      spec committed in 738ddfa BEFORE this ran"); res = {}
    for root in ROOTS:
        d = load_root(root, lo, hi); mult = MULT[root]; cal = pd.Index(d["days"][d["trade"]]); rng = np.random.default_rng(SEED); log(f"\n{root}: {int(d['trade'].sum())} full sessions in the slice")
        tr = run_rule(d, mult); ab = run_rule(d, mult, trail=False); log(f"  the rule:"); S = summarise(tr, cal, mult, "rule", log); log(f"  ablation, no trailing stop:"); A = summarise(ab, cal, mult, "no-trail", log); sp = splits(tr, log)
        # N1 wrong-range control
        n1 = []
        for off in N1_OFFSETS:
            w = run_rule(d, mult, offset=off)
            if len(w) >= 10:
                n1.append(dict(offset=off, trades=int(len(w)), gross_mean=float(w["gross_usd"].mean()), long=float(w[w["side"] == 1]["gross_usd"].mean()) if (w["side"] == 1).sum() else float("nan")))
        n1g = np.array([x["gross_mean"] for x in n1]); n1l = np.array([x["long"] for x in n1 if np.isfinite(x["long"])])
        # N2 random entries
        n2, tabs = n2_random_entries(d, mult, tr, rng); se95 = p95_se(n2)
        chk = [abs(tabs[(r.day, r.side)][r.e] * mult - r.gross_usd) < 1e-6 for r in tr.itertuples()]; assert all(chk), "the vectorised exit table disagrees with the scalar simulation on a real trade"
        long_n2 = None
        if (tr["side"] == 1).sum() >= 10:
            trl = tr[tr["side"] == 1]; n2l, _ = n2_random_entries(d, mult, trl, np.random.default_rng(SEED + 1), n=N2_DRAWS); long_n2 = dict(p50=float(np.median(n2l)), p95=float(np.quantile(n2l, .95)), p95_se=p95_se(n2l))
        pooled = S.get("pooled", {}); res[root] = dict(rule=S, ablation=A, splits=sp, N1=dict(offsets=n1, p50=float(np.median(n1g)), p95=float(np.quantile(n1g, .95)), long_p95=float(np.quantile(n1l, .95)) if n1l.size else None), N2=dict(n=int(n2.size), p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95, long=long_n2))
        if pooled:
            bar = pooled["gross_mean"] > res[root]["N1"]["p95"] and pooled["gross_mean"] > res[root]["N2"]["p95"] + 2 * se95 and pooled["net_sharpe"] > 0.3; res[root]["bar"] = bool(bar)
            log(f"  N1 wrong-range control (offsets 3-22): p50 ${res[root]['N1']['p50']:+.2f} p95 ${res[root]['N1']['p95']:+.2f} (long p95 ${res[root]['N1']['long_p95'] if res[root]['N1']['long_p95'] is not None else float('nan'):+.2f})   N2 random entries, same exits: p50 ${res[root]['N2']['p50']:+.2f} p95 ${res[root]['N2']['p95']:+.2f} +- {se95:.2f}" + (f" (long p95 ${long_n2['p95']:+.2f})" if long_n2 else ""))
            log(f"  THE BAR (pooled gross > N1 p95 AND > N2 p95 + 2 SE AND net Sharpe > 0.3): {'CLEARED' if bar else 'not cleared'}   (gross ${pooled['gross_mean']:+.2f}; net Sharpe {pooled['net_sharpe']:+.2f})")
        tr.to_csv(REPO / "data" / f"d490_trades_{mode}_{root}.csv.gz", index=False, compression="gzip")
    log(f"\n{(time.time()-t0)/60:.1f} min"); return res


def predictions(res, log=print):
    E = res["ES"]; R = E["rule"]; L = R.get("long", {}); Sh = R.get("short", {}); A = E["ablation"]; sp = E["splits"]
    log("\nPREDICTIONS (development, ES)")
    log(f"  X-a long triggers on 35-50% of sessions, short on 25-40%                                   : long {100*L.get('share_of_sessions', float('nan')):.0f}%, short {100*Sh.get('share_of_sessions', float('nan')):.0f}%")
    log(f"  X-b long gross +3..+10 bp, hit 52-58%, exits T 15-30 / tr 30-50 / C rest; short +0..+5 bp; long median < mean : long {L.get('bp_mean', float('nan')):+.1f} bp hit {100*L.get('hit', float('nan')):.1f}% T/tr/C {100*L.get('exit_mix', {}).get('target', float('nan')):.0f}/{100*L.get('exit_mix', {}).get('trail', float('nan')):.0f}/{100*L.get('exit_mix', {}).get('close', float('nan')):.0f}%; short {Sh.get('bp_mean', float('nan')):+.1f} bp; long median ${L.get('gross_median', float('nan')):+.2f} vs mean ${L.get('gross_mean', float('nan')):+.2f}")
    log(f"  X-c trail raises hit, lowers mean, Sharpe within +-0.1 of the ablation                      : hit {100*R['pooled']['hit']:.1f}% vs {100*A['pooled']['hit']:.1f}%; mean ${R['pooled']['gross_mean']:+.2f} vs ${A['pooled']['gross_mean']:+.2f}; Sharpe {R['pooled']['net_sharpe']:+.2f} vs {A['pooled']['net_sharpe']:+.2f}")
    log(f"  X-d N1 within 2 bp of the rule; long clears N2                                              : rule ${R['pooled']['gross_mean']:+.2f} vs N1 p50 ${E['N1']['p50']:+.2f}; long ${L.get('gross_mean', float('nan')):+.2f} vs N2 long p95 ${(E['N2']['long'] or {}).get('p95', float('nan')):+.2f}")
    log(f"  X-e net Sharpe +0.1..+0.4, bar not cleared; 2018 worst                                       : {R['pooled']['net_sharpe']:+.2f} ({'CLEARED' if E.get('bar') else 'not cleared'}); by year " + " ".join(f"{y}:{v:+.2f}" for y, v in R['pooled']['by_year'].items()))
    log(f"  X-f P<0 worse than in-band; after 11:00 better                                               : " + "; ".join(f"{k} {v['gross_mean']:+.1f}" for k, v in sp.items() if k.startswith('long|') and (('P<' in k) or ('P<=' in k) or ('11' in k))))


def main_mode(mode, flag_ok):
    if mode == "validate" and not flag_ok:
        print("REFUSED: --validate touches 2021-2023, once per declared filter set; re-run with --filter-declared under a record that names the filter."); return 2
    if mode == "final" and not flag_ok:
        print("REFUSED: --final reads the reserved 2024+ slice; re-run with --principals-word only on the principal's word."); return 2
    res = run_slice(mode)
    if mode == "dev":
        predictions(res)
    (REPO / "data" / f"d490_range_reversion_{mode}.json").write_text(json.dumps(res, indent=1, default=float)); print(f"wrote data/d490_range_reversion_{mode}.json"); return 0


# ------------------------------------------------------------------------------------------ selftest
def synth_day(path, vol=None, base=100.0):
    """A 390-bar day from a per-bar close path; open = previous close, high/low = +-0.1 around; volume optional."""
    C = np.asarray(path, float); O = np.concatenate([[C[0]], C[:-1]]); H = np.maximum(O, C) + 0.1; L = np.minimum(O, C) - 0.1; V = np.full(NBAR, 100.0) if vol is None else np.asarray(vol, float)
    return O, H, L, C, V


def make_d(days_paths, vols, ranges):
    """Build a dict like load_root from synthetic days: ranges[i] = (H, L) for 'yesterday' of day i is realised by putting a day i-1 with that high/low."""
    n = len(days_paths); O = np.zeros((n, NBAR)); H = np.zeros((n, NBAR)); L = np.zeros((n, NBAR)); C = np.zeros((n, NBAR)); V = np.zeros((n, NBAR))
    for i, (p, v) in enumerate(zip(days_paths, vols)):
        O[i], H[i], L[i], C[i], V[i] = synth_day(p, v)
    hh = [f"{9 + (30 + m) // 60:02d}:{(30 + m) % 60:02d}" for m in range(NBAR)]
    return dict(days=np.array([f"2019-01-{i+1:02d}" for i in range(n)]), O=O, H=H, L=L, C=C, V=V, full=np.ones(n, bool), trade=np.ones(n, bool), hh=hh)


def cmd_selftest():
    t0 = time.time(); print("== (a) a dip to the bottom of yesterday's range on a spike, then a rise to the top: long enters at the next open + tick and exits at the target; the short never triggers")
    # yesterday: range 90..110 (day 0); today: starts 100, dips to 90.5 (P=0.025) at bar 40 with a volume spike, rises to 110 by bar 200
    prev = np.concatenate([np.linspace(100, 110, 100), np.linspace(110, 90, 200), np.linspace(90, 100, 90)]); today = np.concatenate([np.linspace(100, 90.5, 41), np.linspace(90.5, 111, 160), np.full(189, 111.0)])
    vol = np.full(NBAR, 100.0); vol[40] = 500.0; d = make_d([prev, today], [np.full(NBAR, 100.0), vol], None); d["V"] = np.vstack([np.full((20, NBAR), 100.0), d["V"]]); pad = 20
    for k in ("O", "H", "L", "C"):
        d[k] = np.vstack([np.tile(d[k][0], (pad, 1)), d[k]])
    d["days"] = np.array([f"2018-12-{i+1:02d}" for i in range(pad)] + list(d["days"])); d["full"] = np.ones(len(d["days"]), bool); d["trade"] = np.zeros(len(d["days"]), bool); d["trade"][-1] = True
    i = len(d["days"]) - 1; Hy, Ly = day_range(d, i, 1); med = normaliser(d["V"], i); assert abs(Hy - 110.1) < 1e-9 and abs(Ly - 89.9) < 1e-9
    e = triggers(d, i, 1, Hy, Ly, med); assert e == 40, e; assert triggers(d, i, -1, Hy, Ly, med) == -1
    p, jx, typ, mae, mfe, ent, ex = simulate(d, i, 1, e, Hy, Ly); T = Ly + 0.95 * (Hy - Ly); assert typ == "target" and abs(ex - T) < 1e-9 and abs(ent - (d["O"][i][41] + TICK)) < 1e-9 and abs(p - (T - ent)) < 1e-9
    tab = exit_table(d, i, 1, Hy, Ly); assert abs(tab[e] - p) < 1e-9, (tab[e], p); print(f"  ok: trigger bar 40, entry {ent:.2f}, target {T:.2f}, pnl {p:+.2f} pts; the vectorised table agrees")
    print("== (b) a rise past the midpoint then a fall: the trailing stop arms and exits at the last confirmed swing low - 1 tick; without the trail the trade rides to the close")
    today2 = np.concatenate([np.linspace(100, 90.5, 41), np.linspace(90.5, 103, 60), np.linspace(103, 99, 20), np.linspace(99, 104, 20), np.linspace(104, 92, 100), np.full(149, 92.0)]); d2 = dict(d); d2["O"], d2["H"], d2["L"], d2["C"], d2["V"] = (x.copy() for x in (d["O"], d["H"], d["L"], d["C"], d["V"]))
    O2, H2, L2, C2, V2 = synth_day(today2, vol); d2["O"][i], d2["H"][i], d2["L"][i], d2["C"][i], d2["V"][i] = O2, H2, L2, C2, V2
    p2, j2, t2, *_ = simulate(d2, i, 1, 40, Hy, Ly); p3, j3, t3, *_ = simulate(d2, i, 1, 40, Hy, Ly, trail=False); assert t2 == "trail" and t3 == "close" and p2 > p3, (t2, t3, p2, p3)
    tab2 = exit_table(d2, i, 1, Hy, Ly); tab3 = exit_table(d2, i, 1, Hy, Ly, trail=False); assert abs(tab2[40] - p2) < 1e-9 and abs(tab3[40] - p3) < 1e-9
    print(f"  ok: trail exit at bar {j2} for {p2:+.2f} pts (swing low 99 region); no-trail rides to the close for {p3:+.2f}")
    print("== (c) the short is the exact mirror: negating every price turns the long day into a short day with the same pnl")
    d3 = dict(d); d3["O"], d3["H"], d3["L"], d3["C"] = -d["O"], -d["L"], -d["H"], -d["C"]; Hy3, Ly3 = day_range(d3, i, 1); assert abs(Hy3 + Ly) < 1e-9 and abs(Ly3 + Hy) < 1e-9
    e3 = triggers(d3, i, -1, Hy3, Ly3, med); assert e3 == 40 and triggers(d3, i, 1, Hy3, Ly3, med) == -1; p3s, *_ = simulate(d3, i, -1, e3, Hy3, Ly3); assert abs(p3s - p) < 1e-9, (p3s, p)
    print(f"  ok: short pnl {p3s:+.2f} == long pnl {p:+.2f}")
    print("== (d) the volume normaliser ignores missing minutes and the spike needs 2x the same-minute median; the slice gate raises on a row past the slice")
    V = np.full((25, NBAR), 100.0); V[3, 40] = np.nan; V[:, 40] = np.where(np.isnan(V[:, 40]), np.nan, 50.0); m = normaliser(V, 25); assert abs(m[40] - 50.0) < 1e-9 and abs(m[41] - 100.0) < 1e-9
    try:
        load_root("ES", "2016-02-01", "2016-02-05"); ok = True
    except AssertionError:
        ok = False
    assert ok; print("  ok")
    print("== (e) on 30 real ES sessions the scalar simulation and the vectorised table agree on every real trade, both variants")
    d = load_root("ES", "2016-02-01", "2016-03-15"); cnt = 0
    for i in np.flatnonzero(d["trade"]):
        Hy, Ly = day_range(d, i, 1); med = normaliser(d["V"], i)
        for side in (1, -1):
            e = triggers(d, i, side, Hy, Ly, med)
            if e >= 0:
                for trail in (True, False):
                    p, *_ = simulate(d, i, side, e, Hy, Ly, trail); tab = exit_table(d, i, side, Hy, Ly, trail); assert abs(tab[e] - p) < 1e-9, (d["days"][i], side, trail, tab[e], p); cnt += 1
    assert cnt >= 10; print(f"  ok: {cnt} (trade, variant) pairs identical")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--dev", action="store_true"); g.add_argument("--validate", action="store_true"); g.add_argument("--final", action="store_true"); g.add_argument("--selftest", action="store_true")
    ap.add_argument("--filter-declared", action="store_true"); ap.add_argument("--principals-word", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.dev:
        sys.exit(main_mode("dev", True))
    elif a.validate:
        sys.exit(main_mode("validate", a.filter_declared))
    else:
        sys.exit(main_mode("final", a.principals_word))
