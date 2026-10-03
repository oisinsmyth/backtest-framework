"""D786 DIAG: the abstention oracle across six books (descriptive; no filter, no gate).
Spec: docs/decisions/D786-DIAG-PRE-REG-the-abstention-oracle-across-six-books.md.

    uv run --no-sync python scripts/diag_d786_abstention_oracle.py --selftest
    uv run --no-sync python scripts/diag_d786_abstention_oracle.py --run

The books come from their own code, each known answer reproduced first:
- D737, NQ F2, C1: the row functions D746/D747's `other_lines()` call (the recorder's d737_rows over D746's
  text-restricted rth bars; forward_f2_c1_ledgers' f2_rows and c1_rows over bars bounded at 2024-01-01);
- D776: D775's classify(sessions()); L4: D778's frame, base book; NG: D723's in_sample() (D630's frame), one MNG.

The states (A own payoff vs cost; B self-referential; C mechanism-typed; D shared NQ and own-root volatility and trend)
use only data strictly before each trade's entry session: closes through S-1 for the books that enter during S, and
through S for L4 (whose entry is S's evening, inside session S+1). Window 2016-01-01 .. 2023-12-31 for every book.
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

SPEC = REPO / "docs" / "decisions" / "D786-DIAG-PRE-REG-the-abstention-oracle-across-six-books.md"
OUT = REPO / "data" / "diag_d786_abstention_oracle.json"
LO, HI = "2016-01-01", "2023-12-31"
BOOKS = ("D737", "NQ_F2", "C1", "D776", "L4", "NG")
TYPE = {"D737": "continuation", "NQ_F2": "continuation", "C1": "continuation", "D776": "reversion", "L4": "reversion",
        "NG": "flow"}
ROOT = {"D737": "NQ", "NQ_F2": "NQ", "C1": "NQ", "D776": "NQ", "L4": "RTY", "NG": "NG"}
LAG = {b: (0 if b == "L4" else 1) for b in BOOKS}           # sessions the state's last close sits before S
MULT = {"NQ": 2.0, "RTY": 5.0, "NG": 1000.0}                   # $ per point at the book's micro
KNOWN = {"D737": 1699, "NQ_F2": 274, "C1": 328, "D776": 186, "L4": 280}
SIG_N, RV_N, PCT_N, PCT_MIN = 20, 20, 250, 120
BETA_MIN, TRAIL_N, TRAIL_MIN = 30, 20, 10
AUDIT_N, SEED = 20, 786
STATES = {"A_proj_over_cost": "tercile", "A_proj_ge_2c": "binary", "B_trail20_net": "tercile", "B_trail20_pos": "binary",
          "D_nq_volpct": "tercile", "D_nq_down": "binary", "D_own_volpct": "tercile", "D_own_down": "binary"}


class D786Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D786Error(msg)


# ================================================================================ the books
def load_books() -> tuple[dict[str, pd.DataFrame], dict[str, float]]:
    """{book: DataFrame(index=session, gross, net)} and each book's round trip, each known answer reproduced."""
    import forward_f2_c1_ledgers as FW
    import record_forward_nq_lines as REC
    import stage0_d746_intraday_fades as S746
    import stage0_d775_cpi_nfp_fade as S775
    import stage0_d778_auction_fade_trend_filter as D8
    import vault_d723_ng_stage_a as V723
    out: dict[str, pd.DataFrame] = {}
    cost: dict[str, float] = {}
    nq, ym, es = S746.rth("NQ"), S746.rth("YM"), S746.rth("ES")
    rows, _ = REC.d737_rows(nq, ym, S746.LO)
    t = rows[rows["status"] == "trade"].set_index("day")
    out["D737"] = pd.DataFrame({"gross": t["gross_usd"].astype(float), "net": t["net_usd"].astype(float)})
    _VD, M = FW.f2_modules()
    f2 = FW.f2_rows(FW.L_from_bars(M, "NQ", nq[nq["day"] <= M.IN_END]), FW.L_from_bars(M, "ES", es[es["day"] <= M.IN_END]), S746.LO)
    t = f2[f2["status"] == "trade"].set_index("session")
    out["NQ_F2"] = pd.DataFrame({"gross": t["gross_usd"].astype(float), "net": t["net_usd"].astype(float)})
    b = FW.g0_bars(S775.FIX / "fut_opening_globex_1m.csv.gz", "2024-01-01")
    c1 = FW.c1_rows(b, FW.g0_use(S775.MAIN / "data", "2024-01-01"), "2016-01-04")
    t = c1[c1["status"] == "trade"].set_index("session")
    out["C1"] = pd.DataFrame({"gross": t["gross_usd"].astype(float), "net": t["net_usd"].astype(float)})
    bn = S775._load_file((S775.ROOTS["NQ"][0], ("NQ",)))
    U, _ = S775.classify(S775.sessions(bn, "NQ"), S775.release_days())
    R = U[U["is_rel"]]
    cost["D776"] = S775.ROOTS["NQ"][2]
    out["D776"] = pd.DataFrame({"gross": R["gross"], "net": R["gross"] - cost["D776"]})
    D = D8.frame(D8._load_file(("fut_opening_globex_1m_ym_rty.csv.gz", ("RTY",))), "RTY")
    B = D[D["base"]]
    cost["L4"] = 3.76
    out["L4"] = pd.DataFrame({"gross": B["gross"], "net": B["gross"] - cost["L4"]})
    tab, _ = V723.in_sample()
    V723.check_known(V723.answer(tab))
    tt = tab[tab["traded"]].set_index("day")
    g = V723.mng_gross(tt["g"].to_numpy(float))
    cost["NG"] = float(V723._R().MNG_COST)
    out["NG"] = pd.DataFrame({"gross": g, "net": g - cost["NG"]}, index=tt.index)
    for k in ("D737", "NQ_F2", "C1"):
        c = (out[k]["gross"] - out[k]["net"]).round(4).unique()   # 4 dp: D737's differs in the 6th (float noise)
        need(len(c) == 1, f"{k}: more than one cost per trade: {c[:5]}")
        cost[k] = float(c[0])
    for k, n in KNOWN.items():
        need(len(out[k]) == n, f"{k}: {len(out[k])} trades, not the known {n}")
    need(round(float(out["D776"]["gross"].mean()), 2) == 34.88 and round(float(out["L4"]["gross"].mean()), 2) == 15.84,
         "D776's or L4's mean gross is not reproduced")
    for k in BOOKS:
        x = out[k]
        x.index = x.index.astype(str)
        out[k] = x[(x.index >= LO) & (x.index <= HI)].sort_index()
        need(len(out[k]) > 0 and out[k].index.is_unique, f"{k}: empty or duplicated sessions")
    return out, cost


# ================================================================================ the roots' daily closes and states
def daily_closes(root: str) -> pd.DataFrame:
    """The session's last bar at or before 16:59 on its own date, on the session's front (the opening fixtures)."""
    import stage0_d777_post_close_fade as D7
    fn = {"NQ": "fut_opening_globex_1m.csv.gz", "RTY": "fut_opening_globex_1m_ym_rty.csv.gz",
          "NG": "fut_opening_globex_1m_cl_ng_gc_si.csv.gz"}[root]
    parts = []
    for ch in pd.read_csv(D7.FIX / fn, encoding="utf-8", chunksize=2_000_000, dtype={"session": str, "et": str, "hhmm": str,
                                                                                     "contract": str},
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == root) & (ch["session"] >= "2014-06-01") & (ch["session"] <= HI) & (ch["hhmm"] <= "16:59")]
        parts.append(ch[ch["et"].str[:10] == ch["session"]])
    d = pd.concat(parts, ignore_index=True)
    need(bool((d["session"] <= HI).all()), f"seal: a {root} session after {HI}")
    d = d.sort_values(["session", "hhmm"])
    last = d.groupby("session").tail(1).set_index("session")
    return last[["contract", "close"]].sort_index()


def state_frame(c: pd.DataFrame, mult: float) -> pd.DataFrame:
    """Per session S, values computed from closes up to AND INCLUDING S (callers shift by the book's lag)."""
    import stage0_d778_auction_fade_trend_filter as D8
    same = c["contract"] == c["contract"].shift(1)
    dpx = (c["close"] - c["close"].shift(1)).where(same)
    lr = np.log(c["close"] / c["close"].shift(1)).where(same)
    rv = lr.rolling(RV_N, min_periods=RV_N - 5).std()
    pct = rv.rolling(PCT_N, min_periods=PCT_MIN).apply(lambda w: float((w[:-1] < w[-1]).mean()), raw=True)
    ts = D8.trend_state(c["close"], c["contract"])
    return pd.DataFrame({"sigma_usd": (dpx * mult).rolling(SIG_N, min_periods=SIG_N - 5).std(), "volpct": pct,
                         "down": ts["down"].where(ts["has_trend"])}, index=c.index)


def at_lag(st: pd.DataFrame, sessions: pd.Index, lag: int) -> pd.DataFrame:
    """The state known before each session's entry: the row `lag` sessions before it in the root's own calendar."""
    sh = st.shift(lag)
    return sh.reindex(sessions)


def beta_proj(g: np.ndarray, s: np.ndarray) -> np.ndarray:
    """proj_i = beta_{<i} x sigma_i, beta the through-origin slope of gross on sigma over earlier trades (>= BETA_MIN)."""
    out = np.full(len(g), np.nan)
    num = den = 0.0
    n = 0
    for i in range(len(g)):
        if n >= BETA_MIN and np.isfinite(s[i]) and den > 0:
            out[i] = num / den * s[i]
        if np.isfinite(s[i]) and np.isfinite(g[i]):
            num += g[i] * s[i]
            den += s[i] ** 2
            n += 1
    return out


def book_states(x: pd.DataFrame, book: str, cost: float, st_own: pd.DataFrame, st_nq: pd.DataFrame) -> pd.DataFrame:
    y = x.copy()
    lag = LAG[book]
    o = at_lag(st_own, y.index, lag)
    q = at_lag(st_nq, y.index, lag)
    y["sigma_usd"] = o["sigma_usd"]
    y["proj"] = beta_proj(y["gross"].to_numpy(float), y["sigma_usd"].to_numpy(float))
    y["A_proj_over_cost"] = y["proj"] / cost
    y["A_proj_ge_2c"] = (y["proj"] >= 2 * cost).where(y["proj"].notna())
    tr = y["net"].shift(1).rolling(TRAIL_N, min_periods=TRAIL_MIN).mean()
    y["B_trail20_net"] = tr
    y["B_trail20_pos"] = (tr > 0).where(tr.notna())
    y["D_nq_volpct"], y["D_nq_down"] = q["volpct"], q["down"]
    y["D_own_volpct"], y["D_own_down"] = o["volpct"], o["down"]
    y["year"] = y.index.str[:4]
    return y


# ================================================================================ profiles
def grp(v: pd.Series) -> dict[str, Any]:
    n = len(v)
    se = float(v.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    return {"n": int(n), "mean_net": round(float(v.mean()), 2) if n else None, "se": round(se, 2) if n > 1 else None,
            "win": round(float((v > 0).mean()), 3) if n else None, "total": round(float(v.sum()), 0),
            "losers": int((v < 0).sum())}


def profile(y: pd.DataFrame, col: str, kind: str) -> dict[str, Any]:
    z = y[y[col].notna()]
    if len(z) < 9:
        return {"n": int(len(z)), "spread": None}
    if kind == "tercile":
        lab = pd.qcut(z[col].rank(method="first"), 3, labels=["low", "mid", "high"])
        cells = {k: grp(z.loc[lab == k, "net"]) for k in ("low", "mid", "high")}
        hi, lo = z.loc[lab == "high", "net"], z.loc[lab == "low", "net"]
    else:
        f = z[col].astype(bool)
        cells = {"true": grp(z.loc[f, "net"]), "false": grp(z.loc[~f, "net"])}
        hi, lo = z.loc[f, "net"], z.loc[~f, "net"]
    losers = int((z["net"] < 0).sum())
    for k in cells:
        cells[k]["share_of_losers"] = round(cells[k]["losers"] / losers, 3) if losers else None
    sp = float(hi.mean() - lo.mean()) if len(hi) and len(lo) else float("nan")
    se = float(math.sqrt(hi.var(ddof=1) / len(hi) + lo.var(ddof=1) / len(lo))) if len(hi) > 1 and len(lo) > 1 else float("nan")
    return {"n": int(len(z)), "cells": cells, "spread": round(sp, 2), "spread_se": round(se, 2),
            "spread_over_se": round(sp / se, 2) if se and np.isfinite(se) and se > 0 else None}


def oracle(y: pd.DataFrame, cost: float, sessions_in_window: int) -> dict[str, Any]:
    net = y["net"]
    by = net.groupby(y["year"]).agg(["count", "sum", "mean"]).round(2)
    tot = float(net.sum())
    best2 = list(by["sum"].sort_values().index[-2:])
    return {"trades": int(len(y)), "cost": cost, "market_time_share": round(len(y) / sessions_in_window, 3),
            "mean_gross": round(float(y["gross"].mean()), 2), "mean_net": round(float(net.mean()), 2),
            "t_net": round(float(net.mean() / net.std(ddof=1) * math.sqrt(len(net))), 2), "total_net": round(tot, 0),
            "net_without_best_two_years": round(float(net[~y["year"].isin(best2)].sum()), 0), "best_two_years": best2,
            "share_2020": round(float(net[y["year"] == "2020"].sum()) / tot, 3) if tot else None,
            "share_2022": round(float(net[y["year"] == "2022"].sum()) / tot, 3) if tot else None,
            "oracle_take_winners_total": round(float(net[net > 0].sum()), 0),
            "oracle_take_winners_trades": int((net > 0).sum()),
            "worst_decile_share_of_gross_loss": round(float(net[net <= net.quantile(0.1)].sum() / net[net < 0].sum()), 3),
            "by_year": {k: [int(r["count"]), float(r["sum"]), float(r["mean"])] for k, r in by.iterrows()}}


def _sign(v: Any) -> int | None:
    return None if v is None or not np.isfinite(v) else int(np.sign(v))


def candidates(prof: dict[str, dict[str, Any]], prof_ex: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for s in STATES:
        hits = []
        for b in BOOKS:
            p, q = prof[b][s], prof_ex[b][s]
            z = p.get("spread_over_se")
            if z is not None and np.isfinite(z) and abs(z) > 2 and _sign(q.get("spread")) is not None \
                    and _sign(q["spread"]) == _sign(p["spread"]):
                hits.append(b)
        out[s] = {"books_over_2se_same_sign_ex2020_22": hits, "candidate": len(hits) >= 2,
                  "signs": {b: _sign(prof[b][s].get("spread")) for b in BOOKS}}
    return out


# ================================================================================ audits
def audit(y: pd.DataFrame, book: str, closes: pd.DataFrame, cost: float, n: int = AUDIT_N) -> None:
    """The state on sampled trades, recomputed from closes TRUNCATED at the state's last session; beta by explicit loop."""
    rng = np.random.default_rng(SEED)
    ok = y[y["sigma_usd"].notna()]
    for s in ok.index[rng.choice(len(ok), size=min(n, len(ok)), replace=False)]:
        pos = closes.index.get_loc(s) if s in closes.index else closes.index.searchsorted(s)
        cut = closes.iloc[: pos + 1 - LAG[book]]
        st = state_frame(cut, MULT[ROOT[book]]).iloc[-1]
        need(abs(st["sigma_usd"] - y.at[s, "sigma_usd"]) < 1e-6, f"lag audit ({book} {s}): sigma from truncated closes differs")
    g, sg = y["gross"].to_numpy(float), y["sigma_usd"].to_numpy(float)
    for i in rng.choice(len(y), size=min(n, len(y)), replace=False):
        prior = [(g[j], sg[j]) for j in range(i) if np.isfinite(sg[j]) and np.isfinite(g[j])]
        if len(prior) < BETA_MIN or not np.isfinite(sg[i]):
            need(not np.isfinite(y["proj"].iloc[i]), f"beta audit ({book}): a projection before {BETA_MIN} earlier trades")
            continue
        beta = sum(a * b for a, b in prior) / sum(b * b for _, b in prior)
        need(abs(beta * sg[i] - y["proj"].iloc[i]) < 1e-6, f"beta audit ({book}): the projection differs")


# ================================================================================ run
def run() -> int:
    t0 = time.time()
    books, cost = load_books()
    closes = {r: daily_closes(r) for r in ("NQ", "RTY", "NG")}
    stf = {r: state_frame(c, MULT[r]) for r, c in closes.items()}
    res: dict[str, Any] = {"spec": SPEC.name, "window": [LO, HI], "books": {}, "profiles": {}, "profiles_ex_2020_2022": {}}
    ys = {}
    for b in BOOKS:
        y = book_states(books[b], b, cost[b], stf[ROOT[b]], stf["NQ"])
        audit(y, b, closes[ROOT[b]], cost[b])
        ys[b] = y
        sess = closes[ROOT[b]]
        n_sess = int(((sess.index >= LO) & (sess.index <= HI)).sum())
        res["books"][b] = {"type": TYPE[b], "root": ROOT[b], **oracle(y, cost[b], n_sess)}
        res["profiles"][b] = {s: profile(y, s, k) for s, k in STATES.items()}
        yx = y[~y["year"].isin(["2020", "2022"])]
        res["profiles_ex_2020_2022"][b] = {s: profile(yx, s, k) for s, k in STATES.items()}
        print(b, res["books"][b]["trades"], "trades, mean net", res["books"][b]["mean_net"], "| spreads/SE",
              {s: res["profiles"][b][s].get("spread_over_se") for s in STATES}, flush=True)
    res["cross_book"] = {s: {b: {"spread": res["profiles"][b][s].get("spread"), "spread_over_se": res["profiles"][b][s].get("spread_over_se"),
                                 "spread_ex2020_22": res["profiles_ex_2020_2022"][b][s].get("spread")} for b in BOOKS}
                         for s in STATES}
    res["candidates"] = candidates(res["profiles"], res["profiles_ex_2020_2022"])
    res["mechanism_typed_signs"] = {s: {t: [res["candidates"][s]["signs"][b] for b in BOOKS if TYPE[b] == t]
                                        for t in ("continuation", "reversion", "flow")} for s in STATES}
    res["d649_note"] = "NG's projected-profit line (D649, slot 8) is family A on D630's trades: its own projection rule"
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("candidates:", {s: v["books_over_2se_same_sign_ex2020_22"] for s, v in res["candidates"].items()},
          f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def selftest() -> int:
    rng = np.random.default_rng(SEED)
    sess = pd.Index([d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", "2019-12-31")])
    closes = pd.DataFrame({"contract": "NQH6", "close": 5000 * np.exp(np.cumsum(rng.normal(0, 0.01, len(sess))))}, index=sess)
    st = state_frame(closes, 2.0)
    # 1) a planted state: net depends on the lagged volatility percentile -> the profile finds it in two books
    tr = sess[300::3]
    vol = at_lag(st, tr, 1)["volpct"].to_numpy()
    profs, profs_ex = {}, {}
    for b in BOOKS:
        noise = rng.normal(0, 5, len(tr))
        net = np.where(np.isfinite(vol), 40 * (vol - 0.5), 0) + noise
        x = pd.DataFrame({"gross": net + 4.0, "net": net}, index=tr)
        y = book_states(x, b if b != "L4" else "D737", 4.0, st, st)
        profs[b] = {s: profile(y, s, k) for s, k in STATES.items()}
        profs_ex[b] = {s: profile(y[~y["year"].isin(["2020", "2022"])], s, k) for s, k in STATES.items()}
    c = candidates(profs, profs_ex)
    need(c["D_nq_volpct"]["candidate"], f"the planted state was not found: {c['D_nq_volpct']}")
    # 2) a shuffled outcome: no state is a candidate
    for b in BOOKS:
        x = pd.DataFrame({"gross": rng.normal(0, 5, len(tr)) + 4.0}, index=tr)
        x["net"] = x["gross"] - 4.0
        y = book_states(x, "D737", 4.0, st, st)
        profs[b] = {s: profile(y, s, k) for s, k in STATES.items()}
        profs_ex[b] = {s: profile(y[~y["year"].isin(["2020", "2022"])], s, k) for s, k in STATES.items()}
    c0 = candidates(profs, profs_ex)
    need(sum(v["candidate"] for v in c0.values()) <= 1, f"noise produced candidates: {[s for s, v in c0.items() if v['candidate']]}")
    # 3) the truncation audit passes on the honest state and raises on one that reads the entry day
    x = pd.DataFrame({"gross": rng.normal(5, 5, len(tr)), "net": rng.normal(1, 5, len(tr))}, index=tr)
    y = book_states(x, "D737", 4.0, st, st)
    audit(y, "D737", closes, 4.0)
    bad = y.copy()
    bad["sigma_usd"] = at_lag(st, tr, 0)["sigma_usd"]                # reads the entry day
    try:
        audit(bad, "D737", closes, 4.0)
    except D786Error:
        pass
    else:
        raise D786Error("the truncation audit did not raise on a state that reads the entry day")
    # 4) beta uses earlier trades only
    g = np.array([1.0] * 40 + [100.0])
    s = np.ones(41)
    p = beta_proj(g, s)
    need(np.isnan(p[:BETA_MIN]).all() and abs(p[-1] - 1.0) < 1e-12, "beta_proj used the current or later trades")
    print("selftest OK: a planted state is found as a candidate; shuffled outcomes give at most one spurious candidate; "
          "the truncation audit passes the honest state and raises on one that reads the entry day; beta uses earlier "
          "trades only")
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
