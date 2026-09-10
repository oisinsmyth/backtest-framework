"""D415 -- daily zone, 15-minute CONFIRMATION entry. Bar committed in dfb9c39 BEFORE this ran.

    uv run python scripts/run_d415_15m_confirmation.py --run

Path-invariant. Same 3,023 paired events as D414 -- read from D414's committed artifact, not
rebuilt, so the two records are provably one population read twice. Does NOT test the signal.

THE TRAP THE DESIGN REMOVES (record section 2). A confirmation rule is a filter as well as a
timing: the events that never confirm are the ones where price kept going, so the confirmed subset
is positively selected by construction. Two controls, and a rule must beat both:
  ctrl  the TIME-MATCHED unconditional entry at bar j+k, k = the rule's own median lag, same events
        -> rule - ctrl is the information in the PATTERN beyond the information in WAITING
  drop  the daily-close strategy's own 5-day return on the events the rule DECLINED

THE RULES (demand; supply is the mirror), scanned from the bar AFTER the first-touch bar j:
  R1  up-bar      first bar with close > open          PRIMARY -- one comparison, no knob
  R2  higher low  first bar with low  > previous low   shape
  R3  re-cross    first bar with close > hi_u          shape
Entry at the confirming bar's close. Exit at the close of t+5, held fixed for every arm, so every
delta is entry-only and already net of matched costs (every arm crosses the spread at a bar close).

THE BAR on R1 pooled: G1 fires on >= 30%; T1 delta > 0 by 2 paired SE; T2 info > 0 by 2 paired SE;
T3 the dropped trades' daily return is NOT higher than the kept trades' by more than 2 SE. All three.
Cell 2 is the declared SECONDARY: same three tests, cannot clear on its own.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d414", REPO / "scripts" / "run_d414_15m_entry.py")
F = importlib.util.module_from_spec(_s)
sys.modules["d414"] = F
_s.loader.exec_module(F)                      # the [SPLIT] holdout guard comes with it

D414_ART = REPO / "data" / "d414_15m_entry.json"
OUT = REPO / "data" / "d415_15m_confirmation.json"
D414_N = 3023
MIN_FIRE = 0.30
RULES = ("R1", "R2", "R3")
PRIMARY = "R1"


def confirm(o, h, l, c, j, side, lo, hi):
    """Index of the confirming bar for each rule, or -1. Scan starts at j+1. Mirror for supply."""
    n = c.size
    out = dict(R1=-1, R2=-1, R3=-1)
    for m in range(j + 1, n):
        if side > 0:
            r1 = c[m] > o[m]
            r2 = l[m] > l[m - 1]
            r3 = c[m] > hi
        else:
            r1 = c[m] < o[m]
            r2 = h[m] < h[m - 1]
            r3 = c[m] < lo
        if out["R1"] < 0 and r1:
            out["R1"] = m
        if out["R2"] < 0 and r2:
            out["R2"] = m
        if out["R3"] < 0 and r3:
            out["R3"] = m
        if min(out.values()) >= 0:
            break
    return out


def assert_SIGN():
    """[SIGN] a confirmed entry BELOW the daily close on a demand zone must give a POSITIVE delta,
    and the supply mirror must too. In money, in the declared direction."""
    for side, p_entry, close in ((+1, 99.0, 101.0), (-1, 101.0, 99.0)):
        d = side * (np.log(close) - np.log(p_entry))
        assert d > 0, f"[SIGN] side {side}: {d:+.4f}"
    # and the scanner itself, on a synthetic session: touch at bar 2, first up-bar at bar 4
    o = np.array([100, 99, 98, 97.5, 97.0, 97.6, 98.2])
    c = np.array([99, 98, 97.5, 97.0, 97.4, 98.2, 98.0])
    l = np.array([98.5, 97.5, 97.0, 96.8, 96.9, 97.4, 97.8])
    h = np.array([100.2, 99.1, 98.1, 97.6, 97.5, 98.3, 98.4])
    r = confirm(o, h, l, c, j=2, side=+1, lo=96.0, hi=97.9)
    assert r["R1"] == 4, f"[SIGN] R1 scanner found bar {r['R1']}, expected 4"
    assert r["R2"] == 4, f"[SIGN] R2 scanner found bar {r['R2']}, expected 4"
    assert r["R3"] == 5, f"[SIGN] R3 scanner found bar {r['R3']}, expected 5"
    return True


def stat(x, label):
    x = np.asarray(x, float)
    if x.size < 2:
        return dict(label=label, n=int(x.size))
    se = x.std(ddof=1) / np.sqrt(x.size)
    return dict(label=label, n=int(x.size), mean=float(1e4 * x.mean()), se=float(1e4 * se),
                t=float(x.mean() / se) if se > 0 else float("nan"),
                median=float(1e4 * np.median(x)), win=float(100 * (x > 0).mean()))


def show(s):
    if "mean" not in s:
        print(f"  {s['label']:40s} n {s['n']:5,}   (too few)")
        return
    print(f"  {s['label']:40s} n {s['n']:5,}   mean {s['mean']:+8.2f} +-{s['se']:5.2f} bp"
          f"   {s['t']:+5.1f} SE   median {s['median']:+7.2f}   >0 {s['win']:.1f}%")


def diff_stat(a, b, label):
    """Unpaired difference of means, a - b, with its SE."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size < 2 or b.size < 2:
        return dict(label=label, n_a=int(a.size), n_b=int(b.size))
    d = a.mean() - b.mean()
    se = float(np.hypot(a.std(ddof=1) / np.sqrt(a.size), b.std(ddof=1) / np.sqrt(b.size)))
    return dict(label=label, n_a=int(a.size), n_b=int(b.size), diff=float(1e4 * d),
                se=float(1e4 * se), t=float(d / se) if se > 0 else float("nan"))


def run():
    t0 = time.time()
    print("D415  daily zone, 15-minute CONFIRMATION -- the filter and the timing, separated")
    print("      the bar was committed in dfb9c39 BEFORE this ran\n")
    assert_SIGN()

    art = json.loads(D414_ART.read_text(encoding="utf-8"))
    ev = art["events"]
    assert len(ev) == D414_N, f"[P2] D414's event set is {D414_N}; artifact carries {len(ev)}"
    assert all(e["date"] <= F.END for e in ev), "[RESERVED] an event past the mining window"
    print(f"  P2  D414's {len(ev):,} paired events reproduced from the committed artifact; "
          f"cell 2 {sum(e['cell2'] for e in ev):,}")

    intr = F.load_15m(verbose=False)
    for s in intr:
        keep = intr[s]["date"] <= F.END
        for k in ("ts", "date", "o", "h", "l", "c"):
            intr[s][k] = intr[s][k][keep]
    sidx = {s: F.session_index(intr[s]) for s in intr}
    print(f"  [RESERVED] every 15m bar past {F.END} cut before scanning")

    # ---- scan
    rows = []
    for e in ev:
        s, d, j, side = e["sym"], e["date"], e["bar"], e["side"]
        a, b = sidx[s][d]
        o, h, l, c = (intr[s][x][a:b] for x in ("o", "h", "l", "c"))
        n = c.size
        assert abs(c[-1] - e["close"]) / e["close"] < 1e-9, \
            f"[ALIGN] {s} {d}: session last close {c[-1]} != D414's close {e['close']}"
        conf = confirm(o, h, l, c, j, side, e["lo"], e["hi"])
        row = dict(sym=s, date=d, j=j, n=n, side=side, cell2=e["cell2"], r_daily=e["r_daily"],
                   close=e["close"])
        for R in RULES:
            m = conf[R]
            row[R] = m
            row[f"{R}_lag"] = (m - j) if m >= 0 else None
            row[f"{R}_p"] = float(c[m]) if m >= 0 else None
            row[f"{R}_trivial"] = bool(m == n - 1) if m >= 0 else None
        row["bars"] = [float(x) for x in c]          # closes, for the time-matched control
        rows.append(row)
    N = len(rows)
    side_arr = np.array([r["side"] for r in rows])
    close_arr = np.array([r["close"] for r in rows])
    c2 = np.array([r["cell2"] for r in rows])
    rd = np.array([r["r_daily"] for r in rows])
    j_arr = np.array([r["j"] for r in rows])
    n_arr = np.array([r["n"] for r in rows])

    res = dict(rules={})
    print(f"\n  --- P1: fire rate, lag, trivial share, and k, per rule ---")
    K = {}
    for R in RULES:
        m = np.array([r[R] for r in rows])
        fired = m >= 0
        lag = np.array([r[f"{R}_lag"] for r in rows if r[R] >= 0])
        triv = np.array([r[f"{R}_trivial"] for r in rows if r[R] >= 0])
        K[R] = int(round(float(np.median(lag)))) if lag.size else None
        res["rules"][R] = dict(fire=float(fired.mean()), n_fired=int(fired.sum()),
                               lag_p10=float(np.quantile(lag, .1)), lag_p50=float(np.median(lag)),
                               lag_p90=float(np.quantile(lag, .9)), trivial=float(triv.mean()),
                               k=K[R], fire_cell2=float(fired[c2].mean()),
                               fire_not_cell2=float(fired[~c2].mean()))
        q = res["rules"][R]
        print(f"  {R}  fires {100*q['fire']:.1f}%  (n {q['n_fired']:,})   lag p10/50/90 "
              f"{q['lag_p10']:.0f}/{q['lag_p50']:.0f}/{q['lag_p90']:.0f} bars   "
              f"trivial (last bar) {100*q['trivial']:.1f}%   k={q['k']}")
    print(f"\n  --- P3: fire rate inside cell 2 vs outside ---")
    for R in RULES:
        q = res["rules"][R]
        print(f"  {R}  cell 2 {100*q['fire_cell2']:.1f}%   not cell 2 {100*q['fire_not_cell2']:.1f}%")

    # ---- P4: look at the object
    e = next(r for r in rows if r["cell2"] and r["R1"] >= 0 and r["R1_lag"] >= 2)
    print(f"\n  P4  {e['sym']} {e['date']}  side {e['side']:+d}  touch bar {e['j']}  "
          f"R1 at bar {e['R1']} (lag {e['R1_lag']}) entry {e['R1_p']:.2f}   "
          f"ctrl bar {min(e['j']+K['R1'], e['n']-1)} entry {e['bars'][min(e['j']+K['R1'], e['n']-1)]:.2f}"
          f"   close {e['close']:.2f}   R2 bar {e['R2']}  R3 bar {e['R3']}")

    # ---- the quantities, per rule
    S = {}
    print(f"\n  --- THE PAIRED DELTAS (record section 3) ---")
    for R in RULES:
        m = np.array([r[R] for r in rows])
        fired = m >= 0
        pR = np.array([r[f"{R}_p"] if r[R] >= 0 else np.nan for r in rows])
        delta = side_arr * (np.log(close_arr) - np.log(pR))
        k = K[R]
        ctrl_bar = j_arr + k
        ctrl_ok = fired & (ctrl_bar <= n_arr - 1)
        p_ctrl = np.array([r["bars"][min(r["j"] + k, r["n"] - 1)] for r in rows])
        d_ctrl = side_arr * (np.log(close_arr) - np.log(p_ctrl))
        info = delta - d_ctrl
        S[R] = dict(
            delta=stat(delta[fired], f"{R} delta vs daily close (confirmed)"),
            ctrl=stat(d_ctrl[ctrl_ok], f"{R} time-matched ctrl at j+{k} (same)"),
            info=stat(info[ctrl_ok], f"{R} info = rule - ctrl"),
            ctrl_excluded=int((fired & ~ctrl_ok).sum()),
            kept_daily=stat(rd[fired], f"{R} daily-close return, KEPT events"),
            dropped_daily=stat(rd[~fired], f"{R} daily-close return, DROPPED events"),
            drop_minus_kept=diff_stat(rd[~fired], rd[fired], f"{R} dropped - kept"),
            cell2=dict(
                delta=stat(delta[fired & c2], f"{R} cell 2  delta"),
                ctrl=stat(d_ctrl[ctrl_ok & c2], f"{R} cell 2  ctrl"),
                info=stat(info[ctrl_ok & c2], f"{R} cell 2  info"),
                kept_daily=stat(rd[fired & c2], f"{R} cell 2  daily, kept"),
                dropped_daily=stat(rd[~fired & c2], f"{R} cell 2  daily, dropped"),
                drop_minus_kept=diff_stat(rd[~fired & c2], rd[fired & c2], f"{R} cell 2  dropped - kept")))
        tag = "PRIMARY" if R == PRIMARY else "shape"
        print(f"\n  [{R}  {tag}]   control excluded where j+k runs past the session: {S[R]['ctrl_excluded']}")
        for key in ("delta", "ctrl", "info", "kept_daily", "dropped_daily"):
            show(S[R][key])
        dk = S[R]["drop_minus_kept"]
        if "diff" in dk:
            print(f"  {dk['label']:40s} {dk['diff']:+8.2f} +-{dk['se']:5.2f} bp   {dk['t']:+5.1f} SE")

    print(f"\n  --- the cell-2 stratum, declared SECONDARY, cannot clear (record section 5a) ---")
    for R in RULES:
        print(f"  [{R}]")
        for key in ("delta", "ctrl", "info", "kept_daily", "dropped_daily"):
            show(S[R]["cell2"][key])
        dk = S[R]["cell2"]["drop_minus_kept"]
        if "diff" in dk:
            print(f"  {dk['label']:40s} {dk['diff']:+8.2f} +-{dk['se']:5.2f} bp   {dk['t']:+5.1f} SE")
    print(f"\n  for reference, D414 in cell 2: first-touch MARKET delta -35.08 +-7.20 (-4.9 SE)")

    # ---- the bar, R1 pooled
    P = S[PRIMARY]
    G1 = bool(res["rules"][PRIMARY]["fire"] >= MIN_FIRE)
    T1 = bool(G1 and P["delta"].get("t", -9) > 2.0)
    T2 = bool(G1 and P["info"].get("t", -9) > 2.0)
    T3 = bool(G1 and not (P["drop_minus_kept"].get("t", 9) > 2.0))
    print(f"\n  --- THE BAR (committed dfb9c39), R1 pooled ---")
    print(f"    G1 R1 fires on >= {100*MIN_FIRE:.0f}%              : {G1}   ({100*res['rules'][PRIMARY]['fire']:.1f}%)")
    print(f"    T1 delta > 0 by 2 paired SE          : {T1}   ({P['delta'].get('mean', float('nan')):+.2f} bp, {P['delta'].get('t', float('nan')):+.1f} SE)")
    print(f"    T2 info  > 0 by 2 paired SE          : {T2}   ({P['info'].get('mean', float('nan')):+.2f} bp, {P['info'].get('t', float('nan')):+.1f} SE)")
    print(f"    T3 dropped not better than kept      : {T3}   (dropped - kept {P['drop_minus_kept'].get('diff', float('nan')):+.2f} bp, {P['drop_minus_kept'].get('t', float('nan')):+.1f} SE)")
    Q = S[PRIMARY]["cell2"]
    s1 = bool(Q["delta"].get("t", -9) > 2.0); s2 = bool(Q["info"].get("t", -9) > 2.0)
    s3 = bool(not (Q["drop_minus_kept"].get("t", 9) > 2.0))
    print(f"    secondary, cell 2 (cannot clear)     : T1 {s1}  T2 {s2}  T3 {s3}")
    clears = bool(G1 and T1 and T2 and T3)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}   secondary cell 2: "
          f"{'all three' if (s1 and s2 and s3) else 'not all three'}")

    for r in rows:
        r.pop("bars")
    OUT.write_text(json.dumps(dict(
        source=str(D414_ART.relative_to(REPO)), n=N, k=K, stage0=res,
        bar=dict(G1=G1, T1=T1, T2=T2, T3=T3, clears=clears),
        secondary_cell2=dict(T1=s1, T2=s2, T3=s3), stats=S, events=rows),
        indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
