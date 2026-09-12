"""D439 -- passive-fill capture on the 15m fixtures. Spec docs/decisions/D439-passive-fill-capture-on-the-15m-fixtures.md
(committed BEFORE this file, R8). A MEASUREMENT; 2024-01-01 onward is RESERVED and never read.

    uv run python -u scripts/run_d439_fill_capture.py --run
"""
from __future__ import annotations
import argparse, gzip, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
FIX = [REPO / "data/fixtures" / f for f in ("cohort3_intraday_15m_raw.csv.gz", "cohort4_intraday_15m_raw.csv.gz", "single_name_intraday_15m_raw.csv.gz")]
START, END = "2018-01-02", "2023-12-31"
CACHE = REPO / "temp" / "d439_15m_days.npz"
OUT = REPO / "data" / "d439_fill_capture.json"
DELTAS = (0.0, 5e-4, 1e-3)           # touch, through-5bp, through-10bp
FWD = 20; N_ROT = 200; SEED = 439


def load_days():
    """Per name-day: open, first-30-minute low/high (bars 09:30 and 09:45), close, volume; every bar past END cut and asserted."""
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True); return {k: z[k] for k in z.files}
    rows = {}
    for p in FIX:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            hdr = next(fh).strip().split(","); assert hdr == ["timestamp", "symbol", "open", "high", "low", "close", "volume"], hdr
            for line in fh:
                q = line.rstrip("\n").split(","); ts = q[0]
                if ts[:10] > END or ts[:10] < START:
                    continue
                rows.setdefault(q[1], []).append((ts, float(q[2]), float(q[3]), float(q[4]), float(q[5]), float(q[6])))
    sym, date, o, l30, h30, c, vol, nb, p30 = [], [], [], [], [], [], [], [], []
    for s, v in rows.items():
        v.sort(key=lambda r: r[0]); days = {}
        for r in v: days.setdefault(r[0][:10], []).append(r)
        for d, bars in days.items():
            if bars[0][0][11:16] != "09:30":
                continue                                    # [SESSION] a day without its opening bar is not a session
            first2 = bars[:2]
            sym.append(s); date.append(d); o.append(bars[0][1]); l30.append(min(b[3] for b in first2)); h30.append(max(b[2] for b in first2)); c.append(bars[-1][4]); vol.append(sum(b[5] for b in bars)); nb.append(len(bars))
            p30.append(first2[-1][4])                       # the price at the end of the passive window (the 09:45 bar's close)
    out = dict(sym=np.array(sym), date=np.array(date), o=np.array(o), l30=np.array(l30), h30=np.array(h30), c=np.array(c), vol=np.array(vol), nbars=np.array(nb), p30=np.array(p30))
    assert (out["date"] <= END).all() and (out["date"] >= START).all(), "[RESERVED] a bar outside the mining window"
    CACHE.parent.mkdir(parents=True, exist_ok=True); np.savez_compressed(CACHE, **out); return out


def fills(o, l30, h30, limit, delta):
    buy = l30 <= limit * (1 - delta); sell = h30 >= limit * (1 + delta); return buy, sell


def adverse(ret_signed, filled):
    """Mean subsequent return on filled days minus unfilled, signed AGAINST the order (positive = a cost)."""
    return float(ret_signed[~filled].mean() - ret_signed[filled].mean()) if filled.any() and (~filled).any() else float("nan")


def assert_SIGN():
    # day 0 gaps DOWN and never trades above the open; day 1 gaps UP and never trades below it
    o = np.array([100.0, 100.0]); l30 = np.array([99.0, 100.0]); h30 = np.array([100.0, 101.0])
    b, s = fills(o, l30, h30, o, 5e-4)
    assert b[0] and not s[0], "[SIGN] a day that gaps down through the open must fill the buy and not the sell"
    assert not b[1] and s[1], "[SIGN] a day that gaps up must fill the sell and not the buy"
    r = np.array([-0.01, +0.01]); fb = np.array([True, False])
    assert adverse(r, fb) > 0, "[SIGN] a buy that fills into a falling price must read as a POSITIVE adverse selection (a cost)"
    fired = False
    try:
        assert adverse(-r, fb) > 0, "flipped"
    except AssertionError:
        fired = True
    assert fired, "[X] THE SELF-TEST CANNOT FAIL -- a flipped sign passed"


def run():
    t0 = time.time(); assert_SIGN(); print("D439 -- passive-fill capture on the 15m fixtures\n      spec committed in 7dceb57 BEFORE this ran; 2024+ RESERVED and not read\n  [SIGN] fills and the adverse-selection sign convention behave, and the check fires when flipped")
    D = load_days(); sym, date, o, l30, h30, c, vol, p30 = D["sym"], D["date"], D["o"], D["l30"], D["h30"], D["c"], D["vol"], D["p30"]
    names = sorted(set(sym.tolist())); print(f"  [RESERVED] {len(date):,} name-days on {len(names)} names, {min(date.tolist())} .. {max(date.tolist())}; every bar past {END} cut")
    # daily PUB half-spread from the atlas panel, matched by symbol and date
    PREP = _load("d348p", "d348_prep.py"); P = PREP.prep(need_grids=False, verbose=False)
    HS = np.asarray(P["HALF"]["PUB"], float) / 1e4          # the grid is in bp (D303); back to a fraction, printed in bp below
    psym = {s: i for i, s in enumerate(P["symbols"])}; pdate = {str(d)[:10]: t for t, d in enumerate(P["dates"])}
    hs = np.full(len(date), np.nan); missing = sorted(s for s in names if s not in psym)
    for k in range(len(date)):
        i = psym.get(sym[k]); t = pdate.get(date[k])
        if i is not None and t is not None: hs[k] = HS[t, i]
    print(f"  half-spread PUB attached from the atlas panel; names not in the panel (dropped): {missing if missing else 'none'}; name-days with hs: {int(np.isfinite(hs).sum()):,}")
    # per name: prior close, forward 20-session close, trailing-20 mean volume (shifted), all within name
    prev_c = np.full(len(date), np.nan); fwd_c = np.full(len(date), np.nan); adv20 = np.full(len(date), np.nan)
    order = np.lexsort((date, sym))
    for s in names:
        idx = order[sym[order] == s]
        cs, vs = c[idx], vol[idx]
        prev_c[idx[1:]] = cs[:-1]; fwd_c[idx[:-FWD]] = cs[FWD:]
        for j in range(20, idx.size): adv20[idx[j]] = vs[j - 20:j].mean()
    ok = np.isfinite(hs) & np.isfinite(prev_c) & np.isfinite(fwd_c) & (o > 0)
    shock = ok & np.isfinite(adv20) & (vol >= 3 * adv20)
    ret_oc = np.log(c / o); ret_20 = np.log(fwd_c / o)
    hs_ter = np.nanquantile(hs[ok], [1 / 3, 2 / 3])
    print(f"  usable name-days {int(ok.sum()):,};  volume-shock days (>= 3x trailing-20) {int(shock.sum()):,};  hs terciles at {1e4*hs_ter[0]:.1f} / {1e4*hs_ter[1]:.1f} bp/side (median {1e4*np.nanmedian(hs[ok]):.1f})", flush=True)
    res = dict(n=int(ok.sum()), n_shock=int(shock.sum()), names=len(names), missing=missing, hs_median_bp=float(1e4 * np.nanmedian(hs[ok])), hs_terciles_bp=[float(1e4 * x) for x in hs_ter], cells={})
    sets = [("all", ok), ("hs narrow", ok & (hs <= hs_ter[0])), ("hs mid", ok & (hs > hs_ter[0]) & (hs <= hs_ter[1])), ("hs wide", ok & (hs > hs_ter[1])), ("shock days", shock)]
    rng = np.random.default_rng(SEED)
    chase30 = np.log(p30 / o)                                 # the move from the open to the end of the passive window
    print(f"\n{'set':12s} {'limit':6s} {'rule':10s} {'n':>7s} {'fill%':>6s} {'hs bp':>6s} {'gross cap':>9s} {'chase|unf':>9s} {'NET cap bp':>10s} {'net/hs':>7s}   {'fill-info same-day':>18s} {'20-sess':>8s}   {'rotation p05..p95 of fill-info':>30s}")
    for sl, sm in sets:
        for ll, lim in (("open", o), ("prevC", prev_c)):
            for dl, delta in zip(("touch", "through5", "through10"), DELTAS):
                b, s = fills(o, l30, h30, lim, delta)
                for side, f, sign in (("buy", b, +1.0), ("sell", s, -1.0)):
                    m = sm & np.isfinite(lim); ff = f[m]; if_ = ff.mean()
                    hsb = float(1e4 * hs[m].mean()); gross = hsb * if_
                    # the CHASE: on unfilled days the passive trader enters at P30 + hs; the cost is the signed move O -> P30 against the order
                    unf = ~ff; chase = float(1e4 * (sign * chase30[m][unf]).mean()) if unf.any() else 0.0
                    net = gross - (1 - if_) * chase; frac = net / hsb if hsb > 0 else float("nan")
                    as_oc = 1e4 * adverse(sign * ret_oc[m], ff); as_20 = 1e4 * adverse(sign * ret_20[m], ff)
                    # rotation null: within name, roll the filled flag by a random offset
                    rot = []
                    if sl == "all" and ll == "open":
                        sub_sym, sub_r = sym[m], sign * ret_oc[m]
                        for d in range(N_ROT):
                            fr = ff.copy()
                            for nm_ in names:
                                jj = np.flatnonzero(sub_sym == nm_)
                                if jj.size > 1: fr[jj] = np.roll(ff[jj], int(rng.integers(1, jj.size)))
                            rot.append(1e4 * adverse(sub_r, fr))
                    key = f"{sl}|{ll}|{dl}|{side}"
                    res["cells"][key] = dict(n=int(m.sum()), fill=float(if_), hs_bp=hsb, gross_capture_bp=float(gross), chase_unfilled_bp=chase, net_capture_bp=float(net), net_over_hs=float(frac),
                                             fill_info_oc_bp=float(as_oc), fill_info_20_bp=float(as_20), rot_p95=float(np.quantile(rot, .95)) if rot else None, rot_p05=float(np.quantile(rot, .05)) if rot else None)
                    if side == "buy" or sl == "all":
                        r_ = f"{np.quantile(rot,.05):+5.2f} .. {np.quantile(rot,.95):+5.2f}" if rot else ""
                        print(f"{sl:12s} {ll:6s} {dl+'/'+side:10s} {int(m.sum()):7,} {100*if_:6.1f} {hsb:6.1f} {gross:9.2f} {chase:+9.2f} {net:+10.2f} {frac:+7.2f}   {as_oc:+18.2f} {as_20:+8.2f}   {r_:>30s}", flush=True)
        print()
    a = res["cells"]
    print("PREDICTIONS")
    print(f"  X-a buy-at-open fill: touch 50-60, through5 35-45, through10 25-35 : {100*a['all|open|touch|buy']['fill']:.1f} / {100*a['all|open|through5|buy']['fill']:.1f} / {100*a['all|open|through10|buy']['fill']:.1f}")
    print(f"  X-b hs median 3-12 bp/side, top tercile 15-40                      : median {res['hs_median_bp']:.1f}; terciles {res['hs_terciles_bp'][0]:.1f} / {res['hs_terciles_bp'][1]:.1f}")
    print(f"  X-c (ADDENDUM) chase on unfilled days, through5 buy, +15..+40 bp   : {a['all|open|through5|buy']['chase_unfilled_bp']:+.2f}  (fill information same-day {a['all|open|through5|buy']['fill_info_oc_bp']:+.2f}, 20-sess {a['all|open|through5|buy']['fill_info_20_bp']:+.2f})")
    print(f"  X-d (ADDENDUM) net capture 0.5-0.8 of hs (through5, all); lower on shock days : all {a['all|open|through5|buy']['net_over_hs']:+.2f}; shock {a['shock days|open|through5|buy']['net_over_hs']:+.2f}")
    print(f"  X-e net/hs largest in the wide tercile, 0.3-0.5                    : narrow {a['hs narrow|open|through5|buy']['net_over_hs']:+.2f}  mid {a['hs mid|open|through5|buy']['net_over_hs']:+.2f}  wide {a['hs wide|open|through5|buy']['net_over_hs']:+.2f}")
    print(f"  X-f rotation p95 of AS within +-2 bp                              : {a['all|open|through5|buy']['rot_p05']:+.2f} .. {a['all|open|through5|buy']['rot_p95']:+.2f}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {time.time()-t0:.0f}s   (2024+ not read; no strategy scored)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.run:
        run()
