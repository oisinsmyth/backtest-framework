"""D351 -- control A must rotate within the floored universe: an erratum study on D347 and D349.

    uv run python scripts/run_d351_control_a_on_the_floor.py --selftest
    uv run python scripts/run_d351_control_a_on_the_floor.py --rerun d347:hist_L --draws 100
    uv run python scripts/run_d351_control_a_on_the_floor.py --rerun d349:on_share --draws 100
    uv run python scripts/run_d351_control_a_on_the_floor.py --report

Pre-registration: docs/decisions/D351-control-A-must-rotate-within-the-floored-universe-an-erratum-study-on-D347-and-D349.md

D347's and D349's control A rolled each name's EVENTS within finT -- every priced bar -- while the observed events are
confined to elig = finT & keep_v2 (after the hedge is defined). A rotated event can therefore land on a bar the strategy is
forbidden to trade (as-traded close < $5, dollar volume below the cut, or no dollar-volume estimate yet), and the kernel
trades it because it checks finT and not keep. Those bars are the illiquid tail D339 removed, and their forward hedged
excess averages +65 bp against +1.7 on the eligible universe.

A' rotates within elig. Everything else -- kernel, cap exit, hedge, sides -- is D347's and D349's. [R47]/[R49] first
reproduce the studies' stored control-A draws from their own seeds by their own code path, so the defect is shown in the
code that ran, not in a re-implementation.
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


PREP = _load("d348p", "d348_prep.py")                       # memo_load installed here; the chain executes once
V47 = PREP.V47
V49 = _load("d349r", "run_d349_short_signal_controls.py")   # its own _load("d348p") is memoised to PREP
EB = PREP.EB
SEED = V47.SEED
CAP = V47.CAP
OUT = REPO / "data" / "d351_control_a_on_the_floor.json"
APRIME = REPO / "data" / "d351_aprime_{study}_{sig}.json"
STUDIES = {"d347": ("long", V47.SIGNALS, 347), "d349": ("short", V49.SIGNALS, V49.STUDY)}


# ------------------------------------------------------------------ the objects
def prep(need_grids=True):
    P = V49.prep(need_grids=need_grids)          # D347's dict + D349's short events (EVENTS49)
    P["elig_np"] = np.asarray(P["elig"])
    P["finT_np"] = np.asarray(P["finT"])
    return P


def events(P, study, sig):
    """(lo, hi, sc, side): the event matrices and the score the kernel reads, on the study's side."""
    if study == "d347":
        lo, hi, sc = P["EVENTS"][sig]
        return np.asarray(lo), np.asarray(hi), np.asarray(sc), 0
    hi, sc = P["EVENTS49"][sig]
    return np.zeros_like(hi), np.asarray(hi), np.asarray(sc), 1


def run(P, lo, hi, sc, side):
    return V47.run_events(P, lo, np.zeros_like(hi), sc, "cap") if side == 0 else V47.run_events(P, np.zeros_like(lo), hi, sc, "cap")


def stored_ctrl(study, sig):
    """The study's own control files (all parts), concatenated."""
    parts = sorted(REPO.glob(f"data/{study}_ctrl_{sig}_p*.json"))
    assert parts, f"no stored control file for {study}:{sig}"
    cs = [json.loads(p.read_text()) for p in parts]
    return cs, np.concatenate([np.array(c["control_A"]) for c in cs]), np.concatenate([np.array(c["control_B"]) for c in cs])


def study_json(study):
    f = REPO / "data" / ("d347_long_signal_controls.json" if study == "d347" else "d349_short_signal_controls.json")
    return json.loads(f.read_text())


def rng_for(study, sig, part=0):
    side, sigs, code = STUDIES[study]
    return np.random.default_rng([SEED, code, 1, sigs.index(sig), part])


def finT_draw(P, lo, hi, sc, side, rng):
    """One draw of the study's OWN control A: D347's rotate_confined (within finT), the side's events."""
    if side == 0:
        return V47.rotate_confined(P, lo, hi, sc, rng)
    return V47.rotate_confined(P, np.zeros_like(hi), hi, sc, rng)


def aprime_draw(P, lo, hi, sc, side, rng):
    """A': the same rotation within elig."""
    sl, ss, sc_ = EB.rotate_signals(lo, hi, sc, P["elig_np"], rng)
    ev = sl if side == 0 else ss
    src = lo if side == 0 else hi
    assert not (ev & ~P["elig_np"]).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(ev.sum(axis=0), src.sum(axis=0)), "[A'] per-name event count changed"
    return sl, ss, sc_


def off_floor(P, ev):
    """Share of rotated events off the floor, and the mean forward hedged excess of those landings, two ways."""
    elig, F = P["elig_np"], np.asarray(P["F"])
    dense_off = ev & ~elig
    t, i = np.nonzero(ev)
    sparse_share = float((~elig[t, i]).mean()) if t.size else 0.0
    dense_share = float(dense_off.sum() / ev.sum()) if ev.sum() else 0.0
    assert abs(sparse_share - dense_share) < 1e-12, "[OFF] dense and sparse off-floor shares differ"
    vals = F[dense_off]
    on = F[ev & elig]
    return dense_share, float(np.nanmean(vals) * 1e4) if vals.size else np.nan, float(np.nanmean(on) * 1e4) if on.size else np.nan


def pnl_bp(res):
    return V47.pnl_bp(res)


def recompute_trade(P, row, e0, age, side):
    """The open-fill hedged excess of one trade against the floored market, independently of the kernel."""
    ocT, mkt_oc, r1T, m_f = np.asarray(P["ocT"]), np.asarray(P["m_f_oc"]), np.asarray(P["r1T"]), np.asarray(P["m_f"])
    ex = ocT[e0, row] - mkt_oc[e0]
    for j in range(1, age):
        v = r1T[e0 + j, row]
        if np.isfinite(v):
            ex += v - m_f[e0 + j]
    return ex if side == 0 else -ex


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    F = np.asarray(P["F"])
    fin_ok = P["finT_np"] & np.isfinite(F)
    m_on, m_off = float(np.nanmean(F[P["elig_np"] & np.isfinite(F)]) * 1e4), float(np.nanmean(F[fin_ok & ~P["elig_np"]]) * 1e4)
    print(f"    the grid: mean forward-40 hedged excess on eligible name-bars {m_on:+.1f} bp; on priced-but-ineligible {m_off:+.1f} bp; "
          f"{float((fin_ok & ~P['elig_np']).sum() / fin_ok.sum()):.1%} of priced bars are ineligible")
    for study, sig, k in (("d347", "hist_L", 3), ("d349", "on_share", 3)):
        lo, hi, sc, side = events(P, study, sig)
        cs, A_stored, _ = stored_ctrl(study, sig)
        rng = rng_for(study, sig, 0)
        worst = 0.0
        shares, offs = [], []
        for d in range(k):
            sl, ss, sc_ = finT_draw(P, lo, hi, sc, side, rng)
            m = float(pnl_bp(run(P, sl, ss, sc_, side)).mean())
            worst = max(worst, abs(m - cs[0]["control_A"][d]))
            sh, off_m, on_m = off_floor(P, sl if side == 0 else ss)
            shares.append(sh); offs.append(off_m)
        assert worst < 1e-9, f"[R{study[1:]}] stored control A not reproduced: {worst:.2e}"
        print(f"    [R{study[1:]}] {study}:{sig}: the first {k} stored control-A draws reproduce from the study's seed by its own code path to {worst:.1e}; "
              f"{np.mean(shares):.1%} of the rotated events landed OFF the floor, where forward excess averages {np.mean(offs):+.1f} bp")
        # [OFF] direct recomputation of the grid at 200 sampled landing cells
        sl, ss, sc_ = finT_draw(P, lo, hi, sc, side, np.random.default_rng([SEED, 351, 9]))
        ev = (sl if side == 0 else ss) & ~P["elig_np"]
        t, i = np.nonzero(ev)
        pick = np.random.default_rng(1).choice(t.size, size=min(200, t.size), replace=False)
        r1T, m_f, ocT, m_oc, finT = np.asarray(P["r1T"]), np.asarray(P["m_f"]), np.asarray(P["ocT"]), np.asarray(P["m_f_oc"]), P["finT_np"]
        worst_f = 0.0
        for p in pick:
            tt, ii = int(t[p]), int(i[p])
            if not np.isfinite(F[tt, ii]):
                continue
            direct = ocT[tt, ii] - m_oc[tt]
            for j in range(1, CAP):
                if finT[tt + j, ii] and np.isfinite(r1T[tt + j, ii]) and np.isfinite(m_f[tt + j]):
                    direct += r1T[tt + j, ii] - m_f[tt + j]
            worst_f = max(worst_f, abs(direct - F[tt, ii]))
        assert worst_f < 1e-12, f"[OFF] grid != direct at a landing cell: {worst_f:.2e}"
        print(f"    [OFF] dense and sparse off-floor shares agree; the grid equals a direct recomputation at {len(pick)} off-floor landing cells to {worst_f:.1e}")
        # [A'] and [S]
        rng2 = np.random.default_rng([SEED, 351, 1, 0])
        for d in range(2):
            sl, ss, sc_ = aprime_draw(P, lo, hi, sc, side, rng2)
            res = run(P, sl, ss, sc_, side)
            pa = pnl_bp(res)
            assert np.isfinite(pa).all(), "[A'] NaN P&L"
        tr = res["trades"]
        pick = np.random.default_rng(2).choice(len(tr), size=min(300, len(tr)), replace=False)
        worst_s = 0.0
        for p in pick:
            row, e0, age, pnl, sd = tr[p]
            worst_s = max(worst_s, abs(pnl - recompute_trade(P, row, e0, age, sd)))
            assert sd == side
        pa = pnl_bp(res)
        print(f"    [A'] {study}:{sig}: 2 draws keep every name's event count, every rotated event is eligible, no NaN; "
              f"{len(tr):,} trades; [S] 300 sampled trades equal the open-fill recomputation against the floored market to {worst_s:.1e} "
              f"({'long' if side == 0 else 'short'} sign)")
        assert worst_s < 1e-9, "[S] sign in money"
    # [6]
    lo, hi, sc, side = events(P, "d347", "hist_L")
    sl, ss, sc_ = finT_draw(P, lo, hi, sc, side, np.random.default_rng(5))
    try:
        assert not (sl & ~P["elig_np"]).any(), "[A'] a rotated event landed off the floor"
        raise SystemExit("[6] FAILED: [A'] did not raise on a finT-rotated draw")
    except AssertionError as e:
        assert "off the floor" in str(e)
    print("    [6] [A'] raises on a draw rotated within finT (some landing is off the floor)")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


def stage_rerun(P, study, sig, draws):
    lo, hi, sc, side = events(P, study, sig)
    res = run(P, lo, hi, sc, side)
    obs = float(pnl_bp(res).mean())
    cs, A_stored, B_stored = stored_ctrl(study, sig)
    assert abs(cs[0]["observed"] - obs) < 1e-9, "observed differs from the study's stored observed"
    print(f"\n  {study}:{sig} ({'long' if side == 0 else 'short'}): observed {obs:+.2f} bp on {len(res['trades']):,} trades; "
          f"stored control A (finT) p50 {np.median(A_stored):+.2f} p95 {np.quantile(A_stored, .95):+.2f} over {A_stored.size} draws")
    # reproduce the first 5 stored draws and measure their off-floor landings
    rng = rng_for(study, sig, 0)
    worst, shares, offs, ons = 0.0, [], [], []
    for d in range(5):
        sl, ss, sc_ = finT_draw(P, lo, hi, sc, side, rng)
        m = float(pnl_bp(run(P, sl, ss, sc_, side)).mean())
        worst = max(worst, abs(m - cs[0]["control_A"][d]))
        sh, off_m, on_m = off_floor(P, sl if side == 0 else ss)
        shares.append(sh); offs.append(off_m); ons.append(on_m)
    assert worst < 1e-9, f"[R] stored control A not reproduced: {worst:.2e}"
    print(f"    [R] 5 stored draws reproduced to {worst:.1e}; off-floor landings {np.mean(shares):.1%}, their mean forward excess {np.mean(offs):+.1f} bp "
          f"(on-floor landings {np.mean(ons):+.1f})")
    rng2 = np.random.default_rng([SEED, 351, 1, STUDIES[study][1].index(sig), 0])
    A2 = []
    ts = time.time()
    for d in range(draws):
        sl, ss, sc_ = aprime_draw(P, lo, hi, sc, side, rng2)
        pa = pnl_bp(run(P, sl, ss, sc_, side))
        assert np.isfinite(pa).all(), "[A'] NaN in a rotated draw"
        A2.append(float(pa.mean()))
        if (d + 1) % 25 == 0 or d + 1 == draws:
            print(f"    {sig}: {d + 1}/{draws} ({time.time() - ts:.0f}s)", flush=True)
    A2 = np.array(A2)
    out = dict(study=study, signal=sig, side=side, draws=draws, observed=obs, trades=len(res["trades"]), control_A_prime=A2.tolist(),
               stored_A=dict(p50=float(np.median(A_stored)), p95=float(np.quantile(A_stored, .95)), max=float(A_stored.max()), draws=int(A_stored.size)),
               stored_B=dict(p50=float(np.median(B_stored)), p95=float(np.quantile(B_stored, .95)), max=float(B_stored.max())),
               repro_worst=worst, off_floor_share=float(np.mean(shares)), off_floor_meanF_bp=float(np.mean(offs)), on_floor_meanF_bp=float(np.mean(ons)))
    f = Path(str(APRIME).format(study=study, sig=sig))
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A' p50 {np.median(A2):+.2f} p95 {np.quantile(A2, .95):+.2f} max {A2.max():+.2f}; observed above A' p95: "
          f"{obs > np.quantile(A2, .95)}; timing' {obs - np.median(A2):+.2f} ({time.time() - P['t0']:.0f}s)")


def stage_report(P):
    rows = {}
    for study, (side, sigs, code) in STUDIES.items():
        J = study_json(study)
        for sig in sigs:
            f = Path(str(APRIME).format(study=study, sig=sig))
            if not f.exists():
                print(f"  {study}:{sig}: A' not run")
                continue
            d = json.loads(f.read_text())
            A2 = np.array(d["control_A_prime"])
            R = J["report"][sig]
            arm = R.get("long/cap") if study == "d347" else R.get("short/cap")
            c = R["controls"]
            rows[f"{study}:{sig}"] = dict(
                study=study, signal=sig, side=side, observed=d["observed"], trades=d["trades"],
                A_stored=d["stored_A"], A_prime=dict(p50=float(np.median(A2)), p95=float(np.quantile(A2, .95)), max=float(A2.max()), draws=int(A2.size),
                                                     distinct=int(len(set(A2.tolist()))), above=bool(d["observed"] > np.quantile(A2, .95))),
                above_A_stored=bool(c["A"]["above"]), above_B=bool(c["B"]["above"]), above_C=bool(arm["control_C"]["above"]),
                timing_stored=d["observed"] - d["stored_A"]["p50"], timing_prime=d["observed"] - float(np.median(A2)),
                off_floor_share=d["off_floor_share"], off_floor_meanF_bp=d["off_floor_meanF_bp"], on_floor_meanF_bp=d["on_floor_meanF_bp"],
                repro_worst=d["repro_worst"])
    print("\n" + "=" * 150)
    print("CONTROL A AS RUN (within finT) vs A' (within the floored universe); kernel, cap exit, mean hedged excess bp per trade")
    print("=" * 150)
    print("  %-22s %5s %8s | %8s %8s %6s | %8s %8s %8s %6s | %8s %8s | %7s %8s | %s" % (
        "signal", "side", "observed", "A p50", "A p95", "above", "A' p50", "A' p95", "A' max", "above", "timing", "timing'", "off-fl%", "off F bp", "B / C above"))
    for k, r in rows.items():
        print("  %-22s %5s %+8.1f | %+8.1f %+8.1f %6s | %+8.1f %+8.1f %+8.1f %6s | %+8.1f %+8.1f | %6.1f%% %+8.1f | %s / %s" % (
            k, r["side"], r["observed"], r["A_stored"]["p50"], r["A_stored"]["p95"], "yes" if r["above_A_stored"] else "NO",
            r["A_prime"]["p50"], r["A_prime"]["p95"], r["A_prime"]["max"], "yes" if r["A_prime"]["above"] else "NO",
            r["timing_stored"], r["timing_prime"], 100 * r["off_floor_share"], r["off_floor_meanF_bp"],
            "yes" if r["above_B"] else "NO", "yes" if r["above_C"] else "NO"))
    # predictions
    g = lambda s, sig: rows.get(f"{s}:{sig}")
    longs = [g("d347", s) for s in V47.SIGNALS if g("d347", s)]
    shorts = [g("d349", s) for s in V49.SIGNALS if g("d349", s)]
    q = {}
    hl, r21 = g("d347", "hist_L"), g("d347", "rev_21")
    q["Q1"] = bool(hl and r21 and hl["A_prime"]["above"] and r21["A_prime"]["above"])
    q["Q2"] = bool(rows and all(r["repro_worst"] < 1e-9 and r["off_floor_share"] > 0.08 and r["off_floor_meanF_bp"] > 40 for r in rows.values()))
    q["Q3"] = bool(hl and abs(hl["A_prime"]["p50"] - 25.0) <= 10.0)
    q["Q4"] = bool(shorts and all(abs(r["timing_prime"]) < 0.5 * abs(r["timing_stored"]) or r["timing_prime"] < 0 for r in shorts)
                   and sum(1 for r in shorts if not r["A_prime"]["above"]) >= 2)
    q["Q5"] = bool(shorts and all(r["observed"] < 0 and not r["above_C"] for r in shorts))
    q["Q6"] = bool(longs and any(r["A_prime"]["p50"] > 40 for r in longs))
    q["Q7"] = bool(all(g("d347", s) and not g("d347", s)["A_prime"]["above"] for s in ("rsi_turn", "rsi_decile")))
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) hist_L and rev_21 long events above A' p95: {v(q['Q1'])} -- " +
          ", ".join(f"{r['signal']} {r['observed']:+.1f} vs A' p95 {r['A_prime']['p95']:+.1f}" for r in longs))
    print(f"  Q2 stored A reproduced; off-floor share > 8% and off-floor mean F > +40 for every signal: {v(q['Q2'])} -- " +
          ", ".join(f"{k} {100 * r['off_floor_share']:.1f}% / {r['off_floor_meanF_bp']:+.0f}" for k, r in rows.items()))
    print(f"  Q3 A' for hist_L within +-10 of the grid's +25: {v(q['Q3'])} -- A' p50 {hl['A_prime']['p50']:+.1f}" if hl else "  Q3: hist_L not run")
    print(f"  Q4 shorts' timing shrinks by more than half and >= 2 fall inside A' p95: {v(q['Q4'])} -- " +
          ", ".join(f"{r['signal']} {r['timing_stored']:+.0f} -> {r['timing_prime']:+.0f} ({'inside' if not r['A_prime']['above'] else 'above'})" for r in shorts))
    print(f"  Q5 D349's verdict stands (every short negative in mean and inside C): {v(q['Q5'])}")
    print(f"  Q6 (against) some long signal's A' still centred above +40: {v(q['Q6'])} -- " + ", ".join(f"{r['signal']} {r['A_prime']['p50']:+.1f}" for r in longs))
    print(f"  Q7 the two rsi references inside A' p95: {v(q['Q7'])}")
    OUT.write_text(json.dumps(dict(note="D351: control A' rotates within the floored universe; A as run rotated within finT (D347/D349's defect)",
                                   rows=rows, predictions=q), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rerun", metavar="STUDY:SIG", help="d347:hist_L or d349:on_share")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print("D351  control A must rotate within the floored universe -- an erratum study on D347 and D349")
    P = prep(need_grids=True)
    if a.selftest:
        stage_selftest(P)
    elif a.rerun:
        study, sig = a.rerun.split(":")
        assert study in STUDIES and sig in STUDIES[study][1], a.rerun
        stage_rerun(P, study, sig, a.draws)
    elif a.report:
        stage_report(P)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
