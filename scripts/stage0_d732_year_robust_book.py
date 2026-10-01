"""D732 Stage 0: is there an ES/NQ book at one micro that does not rest on one year? As pre-registered in
docs/decisions/D732-STAGE-0-PRE-REG-a-book-that-does-not-rest-on-one-year.md (74f907a4).

    uv run python scripts/stage0_d732_year_robust_book.py --selftest
    uv run python scripts/stage0_d732_year_robust_book.py --run        # run-once: refuses if the output exists

The book B = A (the MACD arm) + F (NQ F2, D716 book B) + C (D680 compression C1), one MNQ each, daily net on the
ES/NQ calendar 2018-05-14 -> 2023-12-29. Beside: T1 / T1.5 (D727's follow book; CONTEXT ONLY, declined by the
principal as a strategy) and E (ES F2 at one MES, correlations only).
S1 per-series net, Sharpe/Sortino (daily, sqrt 252), max drawdown, by year, and D729's dollar/vol-unit report
(scale $2 x NQ prior front settle x sigma20); S2 the book's Sharpe with each year removed; S3 correlations by year.
GO iff the book's largest year is <= 50 % of its net in both units AND its Sharpe without that year is >= 0.5.
Writes data/stage0_d732_year_robust_book.json (aggregates only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation.concentration import year_concentration  # noqa: E402

LO, HI, SEAL = "2018-05-14", "2023-12-29", "2024-01-01"
OUT = REPO / "data" / "stage0_d732_year_robust_book.json"
D727_JSON = REPO / "data" / "stage0_d727_trend_curve.json"
BOOK = ("A", "F", "C")
CONTEXT = ("T1", "T1.5")
NQ_USD_PP = 2.0


class D732Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D732Error(msg)


def seal(days, what: str) -> None:
    d = np.asarray(days, dtype=str)
    need(not (d >= SEAL).any(), f"[SEAL] {what}: a session dated >= {SEAL}")


# ------------------------------------------------------------------------------------------------ inputs
def calendar() -> np.ndarray:
    import diag_d722_conditioners as DC
    p = DC.load_conditioners().reset_index()
    s = np.sort(p.loc[p["root"] == "NQ", "session"].to_numpy(str))
    s = s[(s >= LO) & (s <= HI)]
    seal(s, "calendar")
    return s


def trades_d722() -> dict[str, pd.DataFrame]:
    import diag_d722_lines as DL
    df = DL.load_lines()                          # re-validates every D722 known answer, A (K1) and F (L2) included
    out = {}
    for k, line in (("A", "K1"), ("F", "L2"), ("E", "L1")):
        x = df[df["line"] == line][["session", "net_usd"]].rename(columns={"net_usd": "net"})
        seal(x["session"], line)
        out[k] = x.reset_index(drop=True)
    return out


def trades_d680() -> tuple[pd.DataFrame, dict]:
    import vault_d680_nq_compression as V
    tr, _s, _R = V.in_sample()
    ka = V.known_answer(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(c1.sum()) == ka["trades"], "[D680] the C1 mask differs from its known answer")
    x = tr[c1]
    net = x["net"].to_numpy(float) / 1e4 * x["entry"].to_numpy(float) * NQ_USD_PP
    t = pd.DataFrame({"session": x["session"].astype(str).to_numpy(), "net": net})
    t = t[t["session"] <= HI].reset_index(drop=True)        # the cut, before anything is computed
    seal(t["session"], "D680 C1")
    return t, ka


def daily_d727() -> dict[str, pd.Series]:
    import diag_d727_overlap as O
    import stage0_d727_trend_curve as T
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    pn = T.load_root("NQ", REPO / "data")
    ob = T.objects(pn)
    known = json.loads(D727_JSON.read_text(encoding="utf-8"))
    nq = known["roots"]["NQ"] if "roots" in known else known["NQ"]
    out = {}
    for k, name in ((1.0, "T1"), (1.5, "T1.5")):
        s = O.first_crossing_daily(pn, ob, k, float(cl["usd_per_point"]), float(cl["cost"]))
        seal(s.index, name)
        kn = nq["books"]["first_crossing"][str(k)]
        tr = s[s != 0]
        need(len(tr) == kn["trades"] and abs(float(tr.mean()) - kn["mean_net"]) < 1e-9,
             f"[D727] k {k}: {len(tr)} trades, {float(tr.mean())} against {kn['trades']}, {kn['mean_net']}")
        out[name] = s
    return out


def to_daily(t: pd.DataFrame, cal: np.ndarray, name: str, one_per_session: bool) -> pd.Series:
    t = t[(t["session"] >= LO) & (t["session"] <= HI)]
    if one_per_session:
        need(not t["session"].duplicated().any(), f"[DAILY] {name}: two trades on one session")
    off = ~t["session"].isin(set(cal))
    need(not off.any(), f"[DAILY] {name}: a trade on a session off the calendar ({t.loc[off, 'session'].iloc[0] if off.any() else ''})")
    d = t.groupby("session")["net"].sum().reindex(cal).fillna(0.0)
    need(abs(float(d.sum()) - float(t["net"].sum())) <= 1e-9 * max(1.0, float(t["net"].abs().sum())),
         f"[DAILY] {name}: the daily sum differs from the trade total")
    return d


def nq_scale(cal: np.ndarray) -> np.ndarray:
    import report_d729_vol_unit_concentration as R
    t = R.scale_table("NQ")
    sig, p = R.lookup(t, cal)
    sc = NQ_USD_PP * p * sig
    need(np.isfinite(sc).all() and (sc > 0).all(), "[SCALE] a session without NQ's scale")
    return sc


# ------------------------------------------------------------------------------------------------ statistics
def sharpe(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x) / sd * math.sqrt(252)) if sd > 0 else float("nan")


def sortino(x: np.ndarray) -> float:
    dd = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(np.mean(x) / dd * math.sqrt(252)) if dd > 0 else float("nan")


def max_dd(x: np.ndarray) -> float:
    c = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(np.r_[0.0, c])[1:] - c))


def series_stats(d: pd.Series, scale: np.ndarray) -> dict:
    x = d.to_numpy(float)
    yrs = d.index.str[:4]
    by = {y: float(x[yrs == y].sum()) for y in sorted(set(yrs))}
    rep = year_concentration(d.index.to_numpy(str), x, scale)
    return {"total_net": float(x.sum()), "net_per_year": float(x.sum() / (len(x) / 252)), "trade_days": int((x != 0).sum()),
            "net_sharpe": sharpe(x), "net_sortino": sortino(x), "max_dd": max_dd(x), "by_year": by,
            "d729": {"label": rep["label"], "max_year_usd": rep["gross"]["max_year"], "max_share_usd": rep["gross"]["max_share"],
                     "max_year_vol": rep["vol_units"]["max_year"], "max_share_vol": rep["vol_units"]["max_share"],
                     "shares_usd": {y: v["share"] for y, v in rep["gross"]["by_year"].items()},
                     "shares_vol": {y: v["share"] for y, v in rep["vol_units"]["by_year"].items()},
                     "years_positive": rep["gross"]["years_positive"], "n_years": rep["gross"]["n_years"]}}


def loyo(d: pd.Series) -> dict:
    x, yrs = d.to_numpy(float), d.index.str[:4]
    return {y: {"sharpe_without": sharpe(x[yrs != y]), "net_without": float(x[yrs != y].sum())} for y in sorted(set(yrs))}


def corr_table(D: dict[str, pd.Series], names: tuple[str, ...]) -> dict:
    frame = pd.DataFrame({n: D[n] for n in names})
    out = {"pooled": {}, "by_year": {}}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out["pooled"][f"{a}-{b}"] = float(np.corrcoef(frame[a], frame[b])[0, 1])
            for y in sorted(set(frame.index.str[:4])):
                m = frame.index.str[:4] == y
                out["by_year"].setdefault(f"{a}-{b}", {})[y] = float(np.corrcoef(frame.loc[m, a], frame.loc[m, b])[0, 1])
    return out


def reading(max_share_usd, max_share_vol, sharpe_without_max, net_without_max) -> str:
    ok_share = (max_share_usd is not None and max_share_vol is not None and max_share_usd <= 0.5 and max_share_vol <= 0.5)
    if ok_share and sharpe_without_max >= 0.5:
        return "GO"
    if net_without_max > 0:
        return "PARTIAL"
    return "NO-GO"


def book_identity(parts: list[pd.Series], B: pd.Series) -> None:
    need(np.allclose(sum(p.to_numpy() for p in parts), B.to_numpy(), rtol=0, atol=1e-9), "[BOOK] B != the sum of its parts")
    X = np.column_stack([p.to_numpy() for p in parts])
    cov = np.cov(X, rowvar=False, ddof=1)
    need(math.isclose(float(np.var(B.to_numpy(), ddof=1)), float(cov.sum()), rel_tol=1e-9),
         "[BOOK] Var(B) != sum var + 2 sum cov")


# ------------------------------------------------------------------------------------------------ run
def study() -> dict:
    t0 = time.time()
    cal = calendar()
    tr = trades_d722()
    c, ka_c = trades_d680()
    t727 = daily_d727()
    D = {"A": to_daily(tr["A"], cal, "A", True), "F": to_daily(tr["F"], cal, "F", True),
         "C": to_daily(c, cal, "C", True), "E": to_daily(tr["E"], cal, "E", True)}
    for k, s in t727.items():
        s = s[(s.index >= LO) & (s.index <= HI)]
        off = ~s.index.isin(cal)
        need(not (off & (s != 0)).any(), f"[DAILY] {k}: a trade off the calendar")
        D[k] = s.reindex(cal).fillna(0.0)
    B = D["A"] + D["F"] + D["C"]
    book_identity([D[n] for n in BOOK], B)
    sc = nq_scale(cal)
    out = {"spec": "docs/decisions/D732-STAGE-0-PRE-REG-a-book-that-does-not-rest-on-one-year.md (74f907a4)",
           "calendar": {"sessions": int(len(cal)), "from": str(cal[0]), "to": str(cal[-1])},
           "known_answers": {"C_d680": ka_c}, "series": {}, "book": {}, "context_only": {}}
    for n in ("A", "F", "C", "E", "T1", "T1.5"):
        out["series"][n] = series_stats(D[n], sc)
    bs = series_stats(B, sc)
    lo = loyo(B)
    ymax = bs["d729"]["max_year_usd"]
    out["book"] = {"components": list(BOOK), **bs, "without_each_year": lo, "largest_year": ymax}
    if ymax is not None:
        out["book"]["reading"] = reading(bs["d729"]["max_share_usd"], bs["d729"]["max_share_vol"],
                                         lo[ymax]["sharpe_without"], lo[ymax]["net_without"])
    else:
        out["book"]["reading"] = "NO-GO"
    # fractional equal-risk variant (beside, not read): weights 1/sd, scaled to sum to 3
    w = np.array([1.0 / float(np.std(D[n], ddof=1)) for n in BOOK])
    w = 3 * w / w.sum()
    Bw = sum(wi * D[n] for wi, n in zip(w, BOOK))
    out["book"]["equal_risk_beside"] = {"weights": dict(zip(BOOK, map(float, w))), "net_sharpe": sharpe(Bw.to_numpy()),
                                        "net_sortino": sortino(Bw.to_numpy())}
    for k in CONTEXT:
        Bt = B + D[k]
        st = series_stats(Bt, sc)
        out["context_only"][f"book_plus_{k}"] = {"net_sharpe": st["net_sharpe"], "net_sortino": st["net_sortino"],
                                                 "max_dd": st["max_dd"], "d729": st["d729"], "without_each_year": loyo(Bt),
                                                 "note": "the principal declined D727's follow as a strategy; not read"}
    out["correlations"] = corr_table(D, ("A", "F", "C", "E", "T1", "T1.5"))
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run() -> int:
    need(not OUT.exists(), f"[RUN] {OUT.name} exists: --run is run-once")
    res = study()
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(jsonable(res), fh, indent=1)
        fh.write("\n")
    for n, s in list(res["series"].items()) + [("BOOK", res["book"])]:
        d = s["d729"]
        print(f"{n:5s} net ${s['total_net']:9.0f} ({s['net_per_year']:7.0f}/yr)  Sharpe {s['net_sharpe']:+.2f} "
              f"Sortino {s['net_sortino']:+.2f}  maxDD ${s['max_dd']:6.0f}  largest ${d['max_year_usd']} "
              f"{(d['max_share_usd'] or float('nan')):.0%} / vol {d['max_year_vol']} {(d['max_share_vol'] or float('nan')):.0%}  {d['label']}")
    b = res["book"]
    print("book without each year (Sharpe):", {y: round(v["sharpe_without"], 2) for y, v in b["without_each_year"].items()})
    print("READING:", b["reading"], "| equal-risk beside Sharpe", round(b["equal_risk_beside"]["net_sharpe"], 2))
    for k, v in res["context_only"].items():
        print(f"context {k}: Sharpe {v['net_sharpe']:+.2f}, {v['d729']['label']}")
    print("rho pooled:", {k: round(v, 2) for k, v in res["correlations"]["pooled"].items()})
    print(f"wrote {OUT.relative_to(REPO)} in {res['wall_s']} s")
    return 0


def selftest() -> int:
    t0 = time.time()
    fired = []

    def expect(fn, what):
        try:
            fn()
        except D732Error as e:
            print(f"  RAISES  {what}: {str(e)[:120]}")
            fired.append(what)
            return
        raise SystemExit(f"SELFTEST FAILED: did not raise: {what}")

    cal = np.array(["2019-01-02", "2019-01-03", "2019-01-04", "2020-01-02", "2020-01-03"])
    t = pd.DataFrame({"session": ["2019-01-02", "2019-01-04", "2020-01-03"], "net": [1.0, -2.0, 3.0]})
    d = to_daily(t, cal, "x", True)
    need(d.tolist() == [1.0, 0.0, -2.0, 0.0, 3.0], "[DAILY] zero-filling")
    print("  PASS    daily aggregation zero-fills and conserves the total")
    expect(lambda: to_daily(pd.concat([t, t.iloc[[0]]]), cal, "x", True), "daily: a duplicated trade", )
    expect(lambda: to_daily(pd.concat([t, pd.DataFrame({"session": ["2019-01-05"], "net": [1.0]})]), cal, "x", True),
           "daily: a trade off the calendar")
    expect(lambda: seal(["2023-12-29", "2024-01-02"], "x"), "seal: a planted 2024 session")
    a = pd.Series([1.0, -1.0, 2.0, 0.5, -0.5], index=cal)
    b = pd.Series([0.5, 0.5, -1.0, 1.0, 0.0], index=cal)
    book_identity([a, b], a + b)
    print("  PASS    book identity on a synthetic pair")
    expect(lambda: book_identity([a, b], a + 2 * b), "book: a part counted twice")
    cases = [((0.4, 0.45, 0.8, 10.0), "GO"), ((0.6, 0.45, 0.8, 10.0), "PARTIAL"), ((0.4, 0.55, 0.8, 10.0), "PARTIAL"),
             ((0.4, 0.45, 0.3, 10.0), "PARTIAL"), ((0.6, 0.6, -0.2, -5.0), "NO-GO"), ((None, None, 1.0, 10.0), "PARTIAL")]
    for args, want in cases:
        need(reading(*args) == want, f"[READING] {args} -> {reading(*args)} != {want}")
    print(f"  PASS    reading logic on {len(cases)} cases")
    expect(lambda: need(reading(0.5, 0.5, 0.5, 1.0) == "PARTIAL", "[READING] the boundaries are inclusive (GO at 50 % and 0.5)"),
           "reading: the 50 % / 0.5 boundaries")
    print("[real inputs: known answers, no statistic printed]")
    calr = calendar()
    tr = trades_d722()
    c, ka = trades_d680()
    t727 = daily_d727()
    print(f"  PASS    calendar {len(calr)} sessions; A {len(tr['A'])} F {len(tr['F'])} rows; C known answer {ka['trades']} C1, "
          f"{len(c)} to 2023-12-29; D727 k 1.0 and 1.5 reproduce their known answers")
    bad = c.copy()
    bad.loc[0, "session"] = "2024-01-03"
    expect(lambda: seal(bad["session"], "C"), "seal: a planted 2024 C1 trade")
    expect(lambda: need(abs(float(t727["T1"][t727["T1"] != 0].mean()) + 0.01 - 7.139523412161051) < 1e-9, "[D727] a perturbed mean"),
           "known answer: a perturbed D727 mean")
    sc = nq_scale(calr)
    print(f"  PASS    NQ scale defined on all {len(sc)} sessions")
    print(f"SELFTEST PASS: {len(fired)} canaries raised; {time.time() - t0:.1f} s")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
