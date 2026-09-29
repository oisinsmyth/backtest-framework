"""D687 DIAG -- why D685's month-end rebalancing mechanism fails (the principal: "Can you do a diagnostic on why the
underlying mechanism fails?"). Post hoc, in-sample only (2010-07 -> 2023-12, as D685 read it), no verdict.

    uv run python scripts/diag_d687_month_end_mechanism.py --data-root "<main checkout>/data"

Three facts from D685/D686 to explain: the edge FADES after 2018 (the sign book lost money in each of 2019-2022), the
BOND leg is flat (ZN beta -0.01), and the month-end move CONTINUES into the next month instead of reverting.

Candidate explanations and what each predicts (declared in this docstring before the run):
  A anticipation   : in the late era the negative slope moves EARLIER (days -9..-5 before the last day) while the
                     last-5-day window (-4..0) goes flat.
  B turn-of-month  : the late-era sign-book loss comes from its DRIFT part (mean position x mean return: mostly short
    offset           into a rising window) while the TIMING part (the covariance) keeps its sign; unconditional window
                     returns rise in the late era.
  C smaller flow   : the response per unit of RAW drift (bp per 0.01 of weight) falls, or |drift| falls, or the
                     stock-bond correlation turns positive (co-moving assets make small drifts).
  D information    : after month-end (days +1..+10, signal = the completed month's drift) the slope keeps the
                     window's sign in every era: continuation, not reversal.
  E bonds elsewhere: ZB (the long bond) responds where ZN does not (beta > 0: rebalancers buy duration).
  (not testable here: execution moving to cash equities / ETFs / swaps -- needs cash-index or ETF data.)

Eras (post hoc, from D685's per-year table): 2010-07..2015 (early), 2016..2018 (mid), 2019..2023 (late; the fade
years 2019-2022 plus 2023).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d687_month_end_diag.json"
ERAS = (("early 2010-15", 2010, 2015), ("mid 2016-18", 2016, 2018), ("late 2019-23", 2019, 2023))
R_LO, R_HI = -15, 10


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


B = _load("d685c", "stage0_d685_month_end_rebalancing.py")


def P(*a, **k):
    print(*a, **k, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    B.OTHER_ROOTS = ("ZB",)                                        # D685's loader, with ZB as the extra root
    D = B.load(a.data_root)
    days = D["days"]
    r = {k: D["R"][k][0] for k in ("ES", "ZN", "ZB")}
    r_es0 = np.where(np.isfinite(r["ES"]), r["ES"], 0.0)
    r_zn0 = np.where(np.isfinite(r["ZN"]), r["ZN"], 0.0)
    blocks_all = B.month_blocks(days)
    s = B.drift_signal(r_es0, r_zn0, blocks_all)
    bi = [i for i, b in enumerate(blocks_all) if B.FIRST_MONTH <= days[b[0]][:7] <= B.LAST_MONTH]

    # reproduction: D685's B1 and B2 from the same arrays
    T5 = np.array([blocks_all[i][len(blocks_all[i]) - 5:] for i in bi])
    d685 = json.loads((REPO / "data" / "d685_month_end_rebalancing.json").read_text(encoding="utf-8"))
    b2 = float(np.mean(-np.sign(s[T5 - B.LAG]) * r["ES"][T5] * 1e4))
    if b2 != d685["B2"]["value"]:
        raise SystemExit(f"[REPRO] B2 {b2!r} != D685's {d685['B2']['value']!r}")
    sd_s = float(np.std(s[T5 - B.LAG].ravel(), ddof=1))           # one global scale for bp per 1-SD, post hoc

    # event-time panel: relative day rr = -15..+10 around each month's last trading day T (rr = 0)
    rows = []
    for i in bi:
        b = blocks_all[i]
        T = b[-1]
        nxt = blocks_all[i + 1] if i + 1 < len(blocks_all) else None
        year = int(days[b[0]][:4])
        qe = int(days[b[0]][5:7]) % 3 == 0
        for rr in range(R_LO, R_HI + 1):
            if rr <= 0:
                o = T + rr
                if o - B.LAG < b[0]:
                    continue
            else:
                if nxt is None or rr > len(nxt) or days[nxt[0]] >= B.CUTOFF:
                    continue
                o = nxt[rr - 1]
            sig_i = min(o - B.LAG, T)                              # within-month lagged drift; after T, the month's final drift
            rows.append((year, rr, qe, s[sig_i], r["ES"][o] * 1e4, r["ZN"][o] * 1e4, r["ZB"][o] * 1e4))
    A = np.array(rows, dtype=float)
    yr, rel, qe, sig, y_es, y_zn, y_zb = A.T
    era_of = np.select([(yr >= a_) & (yr <= b_) for _, a_, b_ in ERAS], [0, 1, 2], default=-1)

    def slope(mask, y, x=None, per="sd"):
        x = sig if x is None else x
        m = mask & np.isfinite(y) & np.isfinite(x)
        if m.sum() < 30:
            return None
        xs = x[m] / (sd_s if per == "sd" else 0.01)
        return B.nw_slope(xs, y[m])

    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "post_hoc_in_sample": True, "reproduced_D685_B2": b2, "sd_s_global": sd_s, "eras": [e[0] for e in ERAS]}

    # A / D: the event-time profile of beta by era (bp per 1-SD of drift)
    prof = {}
    for e, (name, _, _) in enumerate(ERAS):
        prof[name] = {}
        for rr in range(R_LO, R_HI + 1):
            b_ = slope((era_of == e) & (rel == rr), y_es)
            prof[name][rr] = None if b_ is None else {"beta": b_["beta"], "t": b_["t"], "n": b_["n"]}
    blocks_r = {"anticipation -9..-5": (-9, -5), "window -4..0": (-4, 0), "post +1..+10": (1, 10),
                "early month-end -15..-10": (-15, -10)}
    pooled = {}
    for e, (name, _, _) in enumerate(ERAS + (("all", 0, 9999),)):
        pooled[name] = {}
        emask = np.ones(len(A), bool) if name == "all" else (era_of == e)
        for bn, (lo, hi) in blocks_r.items():
            b_ = slope(emask & (rel >= lo) & (rel <= hi), y_es)
            pooled[name][bn] = None if b_ is None else {"beta": b_["beta"], "t": b_["t"], "n": b_["n"]}
    out["A_D_profile_by_era"] = prof
    out["A_D_blocks_by_era"] = pooled

    # B: decomposition of the window sign book, drift part vs timing part; unconditional turn-of-month returns
    dec = {}
    tom = {}
    for e, (name, _, _) in enumerate(ERAS + (("all", 0, 9999),)):
        emask = np.ones(len(A), bool) if name == "all" else (era_of == e)
        w = emask & (rel >= -4) & (rel <= 0)
        pos = -np.sign(sig[w])
        yy = y_es[w]
        g = pos * yy
        drift = float(pos.mean() * yy.mean())
        timing = float(np.mean(pos * yy) - drift)                  # the population covariance, exactly
        dec[name] = {"sign_book_bp": float(g.mean()), "drift_part_bp": drift, "timing_part_bp": timing,
                     "mean_position": float(pos.mean()), "share_months_short": float(np.mean(pos < 0)),
                     "mean_window_return_bp": float(yy.mean()), "n": int(w.sum())}
        tom[name] = {}
        for rr in range(-5, 4):
            m_ = emask & (rel == rr)
            if m_.sum() >= 10:
                mm = B.nw_mean(y_es[m_], lag=1)
                tom[name][rr] = {"mean_bp": mm["mean"], "t": mm["t"], "n": mm["n"]}
    out["B_decomposition"] = dec
    out["B_turn_of_month_unconditional"] = tom

    # C: flow size -- |drift|, response per unit RAW drift, stock-bond correlation, and D686's impact factor by era
    flow = {}
    for e, (name, a_, b_) in enumerate(ERAS):
        w = (era_of == e) & (rel >= -4) & (rel <= 0)
        raw = slope(w, y_es, per="raw")
        dd = np.array([int(d[:4]) for d in days])
        dm = (dd >= a_) & (dd <= b_) & np.isfinite(r["ES"]) & np.isfinite(r["ZN"])
        corr = float(np.corrcoef(r["ES"][dm], r["ZN"][dm])[0, 1])
        flow[name] = {"mean_abs_drift": float(np.mean(np.abs(sig[w]))),
                      "beta_bp_per_0.01_raw_drift": None if raw is None else raw["beta"],
                      "t_raw": None if raw is None else raw["t"], "es_zn_daily_corr": corr}
    d686 = json.loads((REPO / "data" / "d686_month_end_variants.json").read_text(encoding="utf-8"))
    F = {int(k): v for k, v in d686["fade"]["F_by_year"].items()}
    for name, a_, b_ in ERAS:
        vals = [F[y] for y in F if a_ <= y <= b_]
        flow[name]["sqrt_law_impact_factor_mean"] = float(np.mean(vals)) if vals else None
    out["C_flow_size"] = flow

    # E: bonds -- ZN and ZB in the window, by era (a positive beta = bonds bought when equities are overweight)
    bonds = {}
    for e, (name, _, _) in enumerate(ERAS + (("all", 0, 9999),)):
        emask = np.ones(len(A), bool) if name == "all" else (era_of == e)
        w = emask & (rel >= -4) & (rel <= 0)
        bonds[name] = {}
        for lab, yv in (("ZN", y_zn), ("ZB", y_zb), ("ES_minus_ZB", y_es - y_zb)):
            b_ = slope(w, yv)
            bonds[name][lab] = None if b_ is None else {"beta": b_["beta"], "t": b_["t"], "n": b_["n"]}
    out["E_bonds"] = bonds

    # quarter-end months against the rest, by era (window)
    qe_tab = {}
    for e, (name, _, _) in enumerate(ERAS):
        qe_tab[name] = {}
        for lab, qm in (("quarter_end", qe == 1), ("other", qe == 0)):
            b_ = slope((era_of == e) & qm & (rel >= -4) & (rel <= 0), y_es)
            qe_tab[name][lab] = None if b_ is None else {"beta": b_["beta"], "t": b_["t"], "n": b_["n"]}
    out["quarter_end_by_era"] = qe_tab

    # report
    P(f"reproduced D685 B2 {b2:+.4f}; global sd of the lagged drift {sd_s:.4f}; panel rows {len(A)}")
    P("\n=== A/D: slope of ES on the drift, by block of relative days (bp per 1-SD; t) ===")
    for name, d_ in pooled.items():
        P(f"  {name:<14} " + "  ".join(f"{bn}: {v['beta']:+6.2f} ({v['t']:+.2f})" if v else f"{bn}: -" for bn, v in d_.items()))
    P("\n  profile (beta by relative day):")
    for name, d_ in prof.items():
        P(f"  {name:<14} " + " ".join(f"{rr}:{v['beta']:+.0f}" if v else f"{rr}:." for rr, v in d_.items()))
    P("\n=== B: the window sign book = drift part + timing part (bp per active day) ===")
    for name, d_ in dec.items():
        P(f"  {name:<14} book {d_['sign_book_bp']:+6.2f} = drift {d_['drift_part_bp']:+6.2f} + timing {d_['timing_part_bp']:+6.2f};"
          f" short {d_['share_months_short']:.2f} of days; mean window return {d_['mean_window_return_bp']:+.2f}")
    P("  unconditional ES return by relative day (bp):")
    for name, d_ in tom.items():
        P(f"  {name:<14} " + " ".join(f"{rr}:{v['mean_bp']:+.1f}({v['t']:+.1f})" for rr, v in d_.items()))
    P("\n=== C: flow size ===")
    for name, d_ in flow.items():
        P(f"  {name:<14} mean|drift| {d_['mean_abs_drift']:.4f}; beta per 0.01 raw drift {d_['beta_bp_per_0.01_raw_drift']:+.2f} "
          f"(t {d_['t_raw']:+.2f}); ES-ZN daily corr {d_['es_zn_daily_corr']:+.2f}; sqrt-law F {d_['sqrt_law_impact_factor_mean']:.2e}")
    P("\n=== E: bonds in the window (beta > 0 = bonds bought) ===")
    for name, d_ in bonds.items():
        P(f"  {name:<14} " + "  ".join(f"{k}: {v['beta']:+.2f} ({v['t']:+.2f})" for k, v in d_.items() if v))
    P("\n=== quarter-end vs other, window ===")
    for name, d_ in qe_tab.items():
        P(f"  {name:<14} " + "  ".join(f"{k}: {v['beta']:+.2f} ({v['t']:+.2f}, n {v['n']})" for k, v in d_.items() if v))
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
