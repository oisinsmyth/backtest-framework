"""D787 DIAG: signal strength against its own gate across the six books (descriptive; no filter, no gate).
Spec: docs/decisions/D787-DIAG-PRE-REG-signal-strength-against-its-own-gate.md.

    uv run --no-sync python scripts/diag_d787_signal_strength.py --selftest
    uv run --no-sync python scripts/diag_d787_signal_strength.py --run

Each book's trades and trigger magnitude m come from its own code (as D786), each known answer reproduced:
D737 |Z| at the trigger minute (D735's spread/trigger via D737's cell, on D746's text-restricted rth bars), NQ F2 tc,
C1 -ctier (forward_f2_c1_ledgers), D776 |x| (D775's classify), L4 |c| (D778's frame), NG |I| (D723's in_sample).
Strength = m's percentile among the book's own EARLIER trades (expanding, >= 30). Window 2016-2023.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import diag_d786_abstention_oracle as A  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D787-DIAG-PRE-REG-signal-strength-against-its-own-gate.md"
OUT = REPO / "data" / "diag_d787_signal_strength.json"
BOOKS = A.BOOKS
MIN_PRIOR, AUDIT_N, SEED = 30, 20, 787
YEAR_MAX = 0.60


class D787Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D787Error(msg)


# ================================================================================ the books with their magnitudes
def load() -> dict[str, pd.DataFrame]:
    """{book: DataFrame(index=session, gross, net, m[, early])}, each known answer reproduced."""
    import forward_f2_c1_ledgers as FW
    import stage0_d727_trend_curve as T
    import stage0_d746_intraday_fades as S746
    import stage0_d775_cpi_nfp_fade as S775
    import stage0_d778_auction_fade_trend_filter as D8
    import vault_d723_ng_stage_a as V723
    import vault_d737_nq_leads_the_dow as V737
    out: dict[str, pd.DataFrame] = {}
    nq, ym, es = S746.rth("NQ"), S746.rth("YM"), S746.rth("ES")
    c = V737.cell(T.panel_from_raw("NQ", nq), T.panel_from_raw("YM", ym))
    d, m0 = c["d"], c["m0"]
    days = np.asarray(c["days"]).astype(str)[d]
    z = np.abs(c["sp"]["Z"][d, m0[d]])
    need(bool((z >= 1.0 - 1e-12).all()), "D737: a trigger below its gate |Z| >= 1")
    cst = V737.cost()
    x = pd.DataFrame({"gross": c["g"], "net": c["g"] - cst, "m": z, "early": -m0[d].astype(float)}, index=days)
    out["D737"] = x[x.index >= S746.LO]
    _VD, M = FW.f2_modules()
    f2 = FW.f2_rows(FW.L_from_bars(M, "NQ", nq[nq["day"] <= M.IN_END]), FW.L_from_bars(M, "ES", es[es["day"] <= M.IN_END]), S746.LO)
    t = f2[f2["status"] == "trade"].set_index("session")
    out["NQ_F2"] = pd.DataFrame({"gross": t["gross_usd"].astype(float), "net": t["net_usd"].astype(float), "m": t["tc"].astype(float)})
    b = FW.g0_bars(S775.FIX / "fut_opening_globex_1m.csv.gz", "2024-01-01")
    c1 = FW.c1_rows(b, FW.g0_use(S775.MAIN / "data", "2024-01-01"), "2016-01-04")
    t = c1[c1["status"] == "trade"].set_index("session")
    need(bool((t["ctier"].astype(float) < 1 / 3).all()), "C1: a trade at or above its gate ctier < 1/3")
    out["C1"] = pd.DataFrame({"gross": t["gross_usd"].astype(float), "net": t["net_usd"].astype(float), "m": -t["ctier"].astype(float)})
    bn = S775._load_file((S775.ROOTS["NQ"][0], ("NQ",)))
    U, _ = S775.classify(S775.sessions(bn, "NQ"), S775.release_days())
    R = U[U["is_rel"]]
    out["D776"] = pd.DataFrame({"gross": R["gross"], "net": R["gross"] - S775.ROOTS["NQ"][2], "m": R["x"].abs()})
    D = D8.frame(D8._load_file(("fut_opening_globex_1m_ym_rty.csv.gz", ("RTY",))), "RTY")
    B = D[D["base"]]
    need(bool((B["c"].abs() >= B["cthr"]).all()), "L4: a trade below its gate |c| >= q80")
    out["L4"] = pd.DataFrame({"gross": B["gross"], "net": B["gross"] - 3.76, "m": B["c"].abs()})
    tab, _ = V723.in_sample()
    V723.check_known(V723.answer(tab))
    tt = tab[tab["traded"]].set_index("day")
    g = V723.mng_gross(tt["g"].to_numpy(float))
    cng = float(V723._R().MNG_COST)
    out["NG"] = pd.DataFrame({"gross": g, "net": g - cng, "m": tt["absI_usd"].to_numpy(float)}, index=tt.index)
    for k, n in A.KNOWN.items():
        need(len(out[k]) == n, f"{k}: {len(out[k])} trades, not the known {n}")
    need(round(float(out["D776"]["gross"].mean()), 2) == 34.88 and round(float(out["L4"]["gross"].mean()), 2) == 15.84,
         "D776's or L4's mean gross is not reproduced")
    for k in BOOKS:
        y = out[k]
        y.index = y.index.astype(str)
        y = y[(y.index >= A.LO) & (y.index <= A.HI)].sort_index()
        need(len(y) > 0 and y.index.is_unique and y["m"].notna().all(), f"{k}: empty, duplicated or missing magnitudes")
        out[k] = y
    return out


# ================================================================================ strength and profiles
def strength(m: np.ndarray, min_prior: int = MIN_PRIOR) -> np.ndarray:
    """The percentile of m_i among m_0..m_{i-1} (ties count half); NaN before min_prior earlier trades."""
    out = np.full(len(m), np.nan)
    for i in range(min_prior, len(m)):
        prior = m[:i]
        out[i] = float(((prior < m[i]).sum() + 0.5 * (prior == m[i]).sum()) / i)
    return out


def split(y: pd.DataFrame, col: str = "strength") -> dict[str, Any]:
    z = y[y[col].notna()]
    s, w = z.loc[z[col] >= 0.5, "net"], z.loc[z[col] < 0.5, "net"]
    sp = float(s.mean() - w.mean()) if len(s) and len(w) else float("nan")
    se = math.sqrt(s.var(ddof=1) / len(s) + w.var(ddof=1) / len(w)) if len(s) > 1 and len(w) > 1 else float("nan")
    return {"strong": A.grp(s), "weak": A.grp(w), "spread": round(sp, 2), "spread_se": round(se, 2) if se == se else None,
            "z": round(sp / se, 2) if se == se and se > 0 else None}


def book_profile(y: pd.DataFrame, volpct: pd.Series) -> dict[str, Any]:
    z = y[y["strength"].notna()].copy()
    ex = z[~z["year"].isin(["2020", "2022"])]
    terc = pd.qcut(z["strength"].rank(method="first"), 3, labels=["low", "mid", "high"])
    weak = z[z["strength"] < 0.5]
    wy = weak["year"].value_counts(normalize=True).sort_index().round(3).to_dict()
    vp = volpct.reindex(z.index)
    return {"trades_scored": int(len(z)), "terciles": {k: A.grp(z.loc[terc == k, "net"]) for k in ("low", "mid", "high")},
            "strong_vs_weak": split(z), "strong_vs_weak_ex_2020_2022": split(ex),
            "weak_half_by_year": wy, "weak_half_max_year_share": max(wy.values()) if wy else None,
            "corr_strength_nq_volpct": round(float(z["strength"].corr(vp)), 3) if vp.notna().sum() > 10 else None}


def candidate(prof: dict[str, dict[str, Any]]) -> dict[str, Any]:
    over = [b for b in BOOKS if (prof[b]["strong_vs_weak"]["z"] or 0) > 2]
    sign_all = [b for b in BOOKS if (prof[b]["strong_vs_weak"]["spread"] or 0) > 0]
    sign_ex = [b for b in BOOKS if (prof[b]["strong_vs_weak_ex_2020_2022"]["spread"] or 0) > 0]
    cal = [b for b in BOOKS if (prof[b]["weak_half_max_year_share"] or 0) > YEAR_MAX]
    ok = len(over) >= 2 and len(sign_all) >= 5 and len(sign_ex) >= 5 and not cal
    return {"books_over_2se": over, "positive_spread": sign_all, "positive_spread_ex_2020_2022": sign_ex,
            "books_failing_the_calendar_check": cal, "candidate": bool(ok)}


# ================================================================================ audits
def audit(y: pd.DataFrame, book: str, n: int = AUDIT_N) -> None:
    rng = np.random.default_rng(SEED)
    m = y["m"].to_numpy(float)
    for i in rng.choice(len(y), size=min(n, len(y)), replace=False):
        if i < MIN_PRIOR:
            need(np.isnan(y["strength"].iloc[i]), f"strength audit ({book}): a value before {MIN_PRIOR} earlier trades")
            continue
        below = sum(1.0 for j in range(i) if m[j] < m[i]) + 0.5 * sum(1.0 for j in range(i) if m[j] == m[i])
        need(abs(below / i - y["strength"].iloc[i]) < 1e-12, f"strength audit ({book}): trade {i} differs")


# ================================================================================ run
def run() -> int:
    t0 = time.time()
    books = load()
    stq = A.state_frame(A.daily_closes("NQ"), A.MULT["NQ"])
    res: dict[str, Any] = {"spec": SPEC.name, "window": [A.LO, A.HI], "books": {}}
    for b in BOOKS:
        y = books[b].copy()
        y["strength"] = strength(y["m"].to_numpy(float))
        y["year"] = y.index.str[:4]
        audit(y, b)
        vol = A.at_lag(stq, y.index, A.LAG[b])["volpct"]
        res["books"][b] = {"type": A.TYPE[b], "trades": int(len(y)), **book_profile(y, vol)}
        if b == "D737":
            ye = y.copy()
            ye["strength"] = strength(ye["early"].to_numpy(float))
            res["books"][b]["earliness"] = book_profile(ye, vol)
        p = res["books"][b]
        print(f"{b:6s} | strong {p['strong_vs_weak']['strong']['mean_net']} weak {p['strong_vs_weak']['weak']['mean_net']} "
              f"spread {p['strong_vs_weak']['spread']} z {p['strong_vs_weak']['z']} | ex20/22 {p['strong_vs_weak_ex_2020_2022']['spread']} "
              f"z {p['strong_vs_weak_ex_2020_2022']['z']} | weak max-year {p['weak_half_max_year_share']} | corr vol {p['corr_strength_nq_volpct']}",
              flush=True)
    res["cross_book"] = {b: {"spread": res["books"][b]["strong_vs_weak"]["spread"], "z": res["books"][b]["strong_vs_weak"]["z"],
                             "spread_ex": res["books"][b]["strong_vs_weak_ex_2020_2022"]["spread"],
                             "z_ex": res["books"][b]["strong_vs_weak_ex_2020_2022"]["z"]} for b in BOOKS}
    res["candidate"] = candidate(res["books"])
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("candidate:", res["candidate"], f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def selftest() -> int:
    rng = np.random.default_rng(SEED)
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", "2023-12-29")][::4]
    vol = pd.Series(rng.uniform(0, 1, len(days)), index=days)
    # 1) a planted effect: net rises with m in every book -> a candidate
    prof = {}
    for b in BOOKS:
        m = rng.uniform(0, 1, len(days))
        y = pd.DataFrame({"m": m, "net": 30 * (m - 0.5) + rng.normal(0, 5, len(days))}, index=days)
        y["strength"], y["year"] = strength(m), y.index.str[:4]
        audit(y, b)
        prof[b] = book_profile(y, vol)
    need(candidate(prof)["candidate"], f"a planted strength effect was not found: {candidate(prof)}")
    # 2) shuffled outcomes: not a candidate
    for b in BOOKS:
        m = rng.uniform(0, 1, len(days))
        y = pd.DataFrame({"m": m, "net": rng.normal(0, 5, len(days))}, index=days)
        y["strength"], y["year"] = strength(m), y.index.str[:4]
        prof[b] = book_profile(y, vol)
    need(not candidate(prof)["candidate"], "noise was reported as a candidate")
    # 3) the audit raises on a strength that includes the current trade
    m = rng.uniform(0, 1, 200)
    y = pd.DataFrame({"m": m, "strength": [np.nan] * MIN_PRIOR + [float((m[: i + 1] <= m[i]).mean()) for i in range(MIN_PRIOR, 200)]},
                     index=[f"2017-01-{1 + i % 28:02d}" for i in range(200)])
    try:
        audit(y, "selftest", n=200)
    except D787Error:
        pass
    else:
        raise D787Error("the strength audit did not raise on a strength that includes the current trade")
    # 4) a calendar-concentrated weak half fails the calendar check (strengths assigned directly: the weak half sits
    #    in 2016; expanding percentiles re-centre over time, so this is the check's own test, not strength()'s)
    for b in BOOKS:
        yrs = pd.Index(days).str[:4]
        s = np.where(yrs == "2016", rng.uniform(0, 0.5, len(days)), rng.uniform(0.5, 1, len(days)))
        y = pd.DataFrame({"m": s, "strength": s, "net": 30 * (s - 0.5) + rng.normal(0, 5, len(days))}, index=days)
        y["year"] = y.index.str[:4]
        prof[b] = book_profile(y, vol)
    need(not candidate(prof)["candidate"] and candidate(prof)["books_failing_the_calendar_check"],
         "a calendar-concentrated weak half passed the calendar check")
    print("selftest OK: a planted strength effect is a candidate; noise is not; the strength audit raises on a strength "
          "that includes the current trade; a calendar-concentrated weak half fails the calendar check")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
