"""D778 Stage 0: the M2K closing-auction fade (D772's Lead 4) with a trend filter.
Spec: docs/decisions/D778-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-trend-filter.md.

    python scripts/stage0_d778_auction_fade_trend_filter.py --selftest
    python scripts/stage0_d778_auction_fade_trend_filter.py --run

The panel is D777's (stage0_d777_post_close_fade.panel: S+1 at most 4 calendar days on, the 18:04 -> 09:59 outcome,
the volatility scale); the rotation is D777's; the trade statistics are D775's. Bars are one-minute, stamped at the
bar's START, on each session's front. Sessions 2016-01-01 .. 2023-12-31 only (asserted).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as D775  # noqa: E402
import stage0_d777_post_close_fade as D7  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D778-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-trend-filter.md"
OUT = REPO / "data" / "stage0_d778_auction_fade_trend_filter.json"
BARS = sorted(set(D7.BARS) | {"15:49"})
PRIMARY = "RTY"
ORDER = ("RTY", "ES", "YM", "NQ")
Q, WIN, WIN_MIN, MA_N, RV_N, RV_MED, RV_LAG = 0.8, 250, 120, 200, 20, 250, 20
AUDIT_N, SEED, WORKERS = 40, 778, 4


class D778Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D778Error(msg)


# ================================================================================ data
def _load_file(args: tuple[str, tuple[str, ...]]) -> pd.DataFrame:
    fn, roots = args
    parts = []
    for ch in pd.read_csv(D7.FIX / fn, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[ch["root"].isin(roots) & (ch["session"] >= D7.START) & (ch["session"] < D7.SEAL) & ch["hhmm"].isin(BARS)]
        lag = (pd.to_datetime(ch["session"]) - pd.to_datetime(ch["et"].str[:10])).dt.days
        parts.append(ch[(lag >= 0) & (lag <= D7.MAX_GAP)])
    d = pd.concat(parts, ignore_index=True)
    need(bool((d["session"] < D7.SEAL).all()), "seal: a session on or after 2024-01-01")
    return d


def load_bars() -> pd.DataFrame:
    jobs: dict[str, list[str]] = {}
    for r, (fn, _, _) in D7.ROOTS.items():
        jobs.setdefault(fn, []).append(r)
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        frames = list(ex.map(_load_file, [(fn, tuple(rs)) for fn, rs in jobs.items()]))
    return pd.concat(frames, ignore_index=True)


# ================================================================================ the frame
def trend_state(p16: pd.Series, contract: pd.Series) -> pd.DataFrame:
    """The back-adjusted 16:00 index (returns zeroed across a change of front), its 200-session average (including
    S), DOWN, and F2's rising-volatility flag. Uses prices up to S only. A session with no 16:00 price adds 0; the next
    priced session's return runs from the last priced close (fixed after the first launch's lag audit, §0 of the
    result)."""
    have = p16.notna()
    prev_p = p16.where(have).ffill().shift(1)
    prev_k = contract.where(have).ffill().shift(1)
    r = np.log(p16 / prev_p)
    r = r.where(have & (contract == prev_k), 0.0).fillna(0.0)
    idx = r.cumsum()
    ma = idx.rolling(MA_N, min_periods=MA_N).mean()
    rv = r.rolling(RV_N, min_periods=RV_N).std()
    rv_med = rv.shift(1).rolling(RV_MED, min_periods=WIN_MIN).median()
    return pd.DataFrame({"r": r, "idx": idx, "ma": ma, "down": idx < ma, "has_trend": ma.notna(),
                         "rising_vol": (rv > rv_med) & (rv > rv.shift(RV_LAG))})


def frame(b: pd.DataFrame, root: str) -> pd.DataFrame:
    D = D7.panel(b, root)
    g = b[b["root"] == root]
    P = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index().reindex(D.index)
    K = g.groupby("session")["contract"].first().reindex(D.index)
    D["c"] = P["15:59"] - P["15:49"]
    D = D.join(trend_state(P["15:59"], K))
    absc = D["c"].abs().where(D["c"] != 0)
    D["cthr"] = absc.shift(1).rolling(WIN, min_periods=WIN_MIN).quantile(Q)
    D["cvalid"] = D["c"].notna() & (D["c"] != 0) & D["y"].notna() & D["cthr"].notna() & D["has_trend"]
    D["base"] = D["cvalid"] & (absc >= D["cthr"])
    D["side"] = -np.sign(D["c"])
    D["gross"] = D["side"] * D["y"]
    D["fall"] = D["c"] < 0
    D["removed"] = D["base"] & D["fall"] & D["down"]
    D["keep"] = D["base"] & ~D["removed"]
    D["removed2"] = D["base"] & D["fall"] & D["rising_vol"]
    D["keep2"] = D["base"] & ~D["removed2"]
    D["va"] = D["gross"] / D["sigma"]
    return D


# ================================================================================ nulls
def filter_null(D: pd.DataFrame) -> dict[str, Any]:
    """Delta = mean gross (filtered) - mean gross (base); the DOWN flag rotated circularly over the valid sessions."""
    V = D[D["cvalid"]]
    base = V["base"].to_numpy()
    fall = V["fall"].to_numpy()
    down = V["down"].to_numpy()
    g = V["gross"].to_numpy()
    mb = g[base].mean()
    n = len(V)
    deltas = np.empty(n)
    for k in range(n):
        keep = base & ~(fall & np.roll(down, k))
        deltas[k] = g[keep].mean() - mb
    obs = deltas[0]
    need(abs(obs - (D.loc[D["keep"], "gross"].mean() - D.loc[D["base"], "gross"].mean())) < 1e-9,
         "right quantity: the filter null's offset 0 != the observed improvement")
    d = deltas[1:]
    return {"delta": round(float(obs), 3), "p50": round(float(np.percentile(d, 50)), 3),
            "p95": round(float(np.percentile(d, 95)), 3), "rank": round(float((d < obs).mean()), 4), "n": int(len(d))}


# ================================================================================ statistics
def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def grp(T: pd.DataFrame, key: Any, cost: float) -> dict[str, Any]:
    return {str(k): {"n": int(len(g)), "mean_gross": round(g["gross"].mean(), 2), "mean_net": round(g["gross"].mean() - cost, 2),
                     "win": round(float((g["gross"] > 0).mean()), 3), "va": round(float(g["va"].mean()), 3),
                     "t": round(tstat(g["gross"]), 2)} for k, g in T.groupby(key)}


def book_of(D: pd.DataFrame, flag: str, cost: float) -> tuple[dict[str, Any], pd.Series]:
    Dk = D.copy()
    Dk["valid"], Dk["gate"] = Dk["cvalid"], Dk[flag]
    return D7.daily_book(Dk, cost)


def gates(D: pd.DataFrame, cost: float, workers: int) -> dict[str, Any]:
    T = D[D["keep"]]
    V = D[D["cvalid"]]
    out: dict[str, Any] = {"stats": D775.trade_stats(T["gross"], cost)}
    s = (V["side"] * V["keep"]).to_numpy(dtype=float)
    out["N_rotation"] = D7.rot_summary(s, V["y"].to_numpy(), workers)
    out["F_null"] = filter_null(D)
    R = D[D["removed"]]
    out["removed"] = {"n": int(len(R)), "mean_gross": round(float(R["gross"].mean()), 2) if len(R) else None,
                      "by_year": grp(R, R["year"], cost) if len(R) else {}}
    yr = grp(T, T["year"], cost)
    out["by_year"] = yr
    full = sorted(yr)[1:]
    need_years = math.ceil(0.75 * len(full))
    win_years = sum(yr[y]["win"] >= 0.5 for y in full)
    va_years = sum(yr[y]["va"] > 0 for y in full)
    hv = T.groupby(np.where(T["year"] <= "2019", "first", "second"))["va"].mean()
    y_i = win_years >= need_years
    y_ii = va_years >= need_years and hv.get("first", np.nan) >= 0.5 * hv.get("second", np.nan)
    net_by_year = {y: yr[y]["mean_net"] * yr[y]["n"] for y in yr}
    best2 = sorted(net_by_year, key=net_by_year.get)[-2:]
    ex_best2 = float((T.loc[~T["year"].isin(best2), "gross"] - cost).sum())
    ex22 = float(T.loc[T["year"] != "2022", "gross"].mean())
    k = max(1, int(round(0.01 * len(T))))
    trimmed = float(T["gross"].sort_values().iloc[k:-k].mean())
    st = out["stats"]
    g1 = st["mean_gross"] > 0 and st["t_gross"] >= 2
    n_ok = out["N_rotation"]["obs"] > out["N_rotation"]["p95"]
    f_ok = (out["removed"]["mean_gross"] is not None and out["removed"]["mean_gross"] < 0
            and out["F_null"]["delta"] > out["F_null"]["p95"])
    g2 = st["mean_net"] > 0 and st["t_net"] >= 2 and ex_best2 > 0 and ex22 >= 2 * cost and trimmed >= 2 * cost
    out["gates"] = {"G1": bool(g1), "N": bool(n_ok), "F": bool(f_ok),
                    "Y": {"pass": bool(y_i or y_ii), "full_years": full, "need": need_years, "i_win_years": int(win_years),
                          "ii_va_years": int(va_years), "va_first": round(float(hv.get("first", np.nan)), 3),
                          "va_second": round(float(hv.get("second", np.nan)), 3), "i": bool(y_i), "ii": bool(y_ii)},
                    "G2": {"pass": bool(g2), "best_two_years": best2, "net_ex_best2": round(ex_best2, 0),
                           "mean_gross_ex2022": round(ex22, 2), "trimmed_gross": round(trimmed, 2), "bar_2x": round(2 * cost, 2)}}
    out["reading"] = ("NO EFFECT" if not g1 else "NOT ABOVE NULL" if not n_ok else "FILTER ADDS NOTHING" if not f_ok else
                      "CONCENTRATED" if not (y_i or y_ii) else "NO PRIZE" if not g2 else "SUPPORTED")
    return out


def study(b: pd.DataFrame, root: str, workers: int = WORKERS, full: bool = True) -> dict[str, Any]:
    _, mult, cost = D7.ROOTS[root]
    D = frame(b, root)
    need(int(D["base"].sum()) == int(D["keep"].sum()) + int(D["removed"].sum()), "right quantity: base != kept + removed")
    need(int(D["removed"].sum()) > 0, "the filter removed nothing")
    out = gates(D, cost, workers)
    if not full:
        return out
    audit(b, root, D)
    B = D[D["base"]]
    out["base_book"] = {"stats": D775.trade_stats(B["gross"], cost), "by_year": grp(B, B["year"], cost),
                        "book": book_of(D, "base", cost)[0]}
    T2 = D[D["keep2"]]
    R2 = D[D["removed2"]]
    out["F2_rising_vol"] = {"stats": D775.trade_stats(T2["gross"], cost), "removed_n": int(len(R2)),
                            "removed_mean_gross": round(float(R2["gross"].mean()), 2) if len(R2) else None,
                            "book": book_of(D, "keep2", cost)[0]}
    T = D[D["keep"]]
    bk, daily = book_of(D, "keep", cost)
    out["book"] = bk
    out["sides_kept"] = grp(T, np.where(T["fall"], "fall (long)", "rise (short)"), cost)
    out["sides_base_by_period"] = {p: grp(g, np.where(g["fall"], "fall (long)", "rise (short)"), cost) for p, g in
                                   B.groupby(np.where(B.index < "2020-01-01", "2016-19", np.where(B.index < "2022-01-01",
                                             "2020-21", np.where(B.index < "2023-01-01", "2022", "2023"))))}
    out["abs_c_terciles"] = grp(T, pd.qcut(T["c"].abs().rank(method="first"), 3, labels=["low", "mid", "high"]), cost)
    out["regimes"] = grp(T, np.where(T.index < D7.REGIME_1, "a_before_2020-10-26", np.where(T.index <= D7.REGIME_2,
                                                                                            "b_to_2021-06-25", "c_after")), cost)
    drift = float(D.loc[D["cvalid"], "y"].mean())
    out["drift_adjusted"] = {"drift": round(drift, 2),
                             "fall_side_kept": round(float(T.loc[T["fall"], "gross"].mean() - drift), 2),
                             "rise_side": round(float(T.loc[~T["fall"], "gross"].mean() + drift), 2)}
    out["down_share_of_sessions"] = round(float(D.loc[D["cvalid"], "down"].mean()), 3)
    net = T["gross"] - cost
    out["top5"] = [[d, round(v, 2)] for d, v in net.nlargest(5).items()]
    out["bottom5"] = [[d, round(v, 2)] for d, v in net.nsmallest(5).items()]
    out["_daily"] = daily
    return out


# ================================================================================ audits
def sign_audit(mirror: float = 1.0) -> None:
    """In money: a closing fall (c < 0) followed by an overnight rise pays the long fade."""
    c, ent, ex = -5.0, 2000.0, 2010.0
    need((-np.sign(c) * mirror) * (ex - ent) * 5.0 > 0, "sign audit: a faded closing fall followed by a rise must pay")


def audit(b: pd.DataFrame, root: str, D: pd.DataFrame, n: int = AUDIT_N) -> None:
    """Second implementation: explicit loops over the raw rows for c, the trend state and the keep decision."""
    _, mult, _ = D7.ROOTS[root]
    raw = b[b["root"] == root].sort_values(["session", "hhmm"])
    close: dict[tuple[str, str], float] = {}
    front: dict[str, str] = {}
    for r in raw.itertuples(index=False):
        close[(r.session, r.hhmm)] = float(r.close)
        front.setdefault(r.session, r.contract)
    sess = list(D.index)
    idx, prev_p, prev_k, acc = {}, None, None, 0.0
    for s in sess:
        p = close.get((s, "15:59"))
        if p is not None and prev_p is not None and front.get(s) == prev_k:
            acc += math.log(p / prev_p)
        idx[s] = acc
        if p is not None:
            prev_p, prev_k = p, front.get(s)
    B = D[D["base"]]
    pick = B.index[np.random.default_rng(SEED).choice(len(B), size=min(n, len(B)), replace=False)]
    for s in pick:
        i = sess.index(s)
        c = close[(s, "15:59")] - close[(s, "15:49")]
        need(abs(c - float(D.at[s, "c"])) < 1e-9, f"lag audit: c differs on {s}")
        need(abs(idx[s] - float(D.at[s, "idx"])) < 1e-9, f"lag audit: the trend index differs on {s}")
        window = [idx[sess[j]] for j in range(i - MA_N + 1, i + 1)]
        down = idx[s] < sum(window) / len(window)
        keep = not (c < 0 and down)
        need(keep == bool(D.at[s, "keep"]), f"lag audit: the keep decision differs on {s}")
        s1 = D.at[s, "s1"]
        g = (-1.0 if c > 0 else 1.0) * (close[(s1, "09:59")] - close[(s1, "18:04")]) * mult
        need(abs(g - float(D.at[s, "gross"])) < 1e-6, f"lag audit: the fade differs on {s}")


# ================================================================================ run
def run() -> int:
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D778Error:
        pass
    else:
        raise D778Error("the sign audit did not raise on a mirrored book")
    b = load_bars()
    res: dict[str, Any] = {"spec": SPEC.name, "window": [D7.START, "2023-12-31"]}
    dailies = {}
    for root in ORDER:
        r = study(b, root)
        dailies[root] = r.pop("_daily")
        res[root] = r
        print(root, "| kept", r["stats"]["n"], "mean", r["stats"]["mean_gross"], "t", r["stats"]["t_gross"], "| base",
              r["base_book"]["stats"]["mean_gross"], "| removed", r["removed"]["n"], r["removed"]["mean_gross"], "| F", r["F_null"],
              "|", r["reading"], flush=True)
    res["GO"] = bool(res[PRIMARY]["reading"] == "SUPPORTED")
    # the component line
    rty = dailies[PRIMARY].groupby(level=0).sum()
    d775 = D7.d775_daily(b)
    nqD = D7.panel(b, "NQ")
    _, d777 = D7.daily_book(nqD, 4.07)
    comp = {"d775": round(float(pd.concat([rty, d775], axis=1).fillna(0).corr().iloc[0, 1]), 3),
            "d777_mnq": round(float(pd.concat([rty, d777.groupby(level=0).sum()], axis=1).fillna(0).corr().iloc[0, 1]), 3)}
    if D7.LINES.exists():
        lines = pd.read_csv(D7.LINES, index_col=0, encoding="utf-8")
        jj = lines.join(rty.rename("d778"), how="inner")
        comp.update({c: round(float(jj["d778"].corr(jj[c])), 3) for c in lines.columns})
    res["component_rho"] = comp
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("PRIMARY", res[PRIMARY]["reading"], "GO", res["GO"], f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def _synthetic(sessions: list[str], bear: tuple[int, int], rng: np.random.Generator, real_filter: bool = True) -> pd.DataFrame:
    """Sessions with a trending price level; the closing move c reverts overnight (fade pays), except fall-side moves
    on sessions whose level is below its own 200-session average (the generator's DOWN), which continue (fade loses).
    With real_filter False, nothing continues."""
    lv = [2000.0]
    for i in range(1, len(sessions)):
        lv.append(lv[-1] * math.exp(-0.004 if bear[0] <= i < bear[1] else 0.0006))
    loglv = np.log(np.array(lv))
    down_gen = [i >= MA_N - 1 and loglv[i] < loglv[i - MA_N + 1:i + 1].mean() for i in range(len(lv))]
    rows, prev = [], None
    for i, d in enumerate(sessions):
        level = lv[i]
        bars = {}
        p = level + rng.normal(0, 2)
        for h in BARS:
            p += rng.normal(0, 0.8)
            bars[h] = p
        bars["15:59"] = level * (1 + rng.normal(0, 1e-5))
        bars["15:49"] = bars["15:59"] - rng.normal(0, 3)
        if prev is not None:
            pc, prev_down = prev
            eff = -0.9 if (pc < 0 and prev_down and real_filter) else 0.9
            bars["09:59"] = bars["18:04"] - eff * pc + rng.normal(0, 0.5)
        prev = (bars["15:59"] - bars["15:49"], down_gen[i])
        for h in BARS:
            day = d if h < "18:00" else (pd.Timestamp(d) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            rows.append({"root": "RTY", "session": d, "et": f"{day} {h}", "hhmm": h, "contract": "RTYZ9", "close": round(bars[h], 2)})
    return pd.DataFrame(rows)


def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
    except D778Error:
        pass
    else:
        raise D778Error("the sign audit did not raise on a mirrored book")
    rng = np.random.default_rng(SEED)
    sessions = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", "2019-12-31")]
    # 1) a planted downtrend continuation on fall-side buys: the filter removes it and passes F
    b = _synthetic(sessions, (500, 700), rng)
    r = study(b, "RTY", workers=1, full=False)
    need(r["removed"]["mean_gross"] < 0 and r["gates"]["F"], f"planted downtrend: F should pass {r['F_null']} {r['removed']}")
    # 2) a filter that tracks nothing: no continuation anywhere, so the removed trades earn and F fails
    b0 = _synthetic(sessions, (500, 700), rng, real_filter=False)
    r0 = study(b0, "RTY", workers=1, full=False)
    need(not r0["gates"]["F"], f"a filter tracking nothing must fail F: {r0['F_null']} {r0['removed']}")
    # 3) the trend state uses no later price
    D = frame(b, "RTY")
    b2 = b.copy()
    late = sessions[800]
    b2.loc[(b2["session"] == late) & (b2["hhmm"] == "15:59"), "close"] *= 3
    D2 = frame(b2, "RTY")
    early = [s for s in sessions[:800] if s in D.index]
    need(D.loc[early, "down"].equals(D2.loc[early, "down"]), "the trend state used a later price")
    # 4) the second implementation agrees (including across sessions with a missing 16:00 bar), and raises on a broken
    #    decision
    audit(b, "RTY", D, n=50)
    bm = b[~((b["hhmm"] == "15:59") & b["session"].isin(sessions[300:900:37]))]
    audit(bm, "RTY", frame(bm, "RTY"), n=10_000)
    Dx = D.copy()
    s0 = Dx[Dx["removed"]].index[0]
    Dx.loc[s0, "keep"] = True
    try:
        audit(b, "RTY", Dx.loc[[s0] + [i for i in Dx.index if i != s0]].sort_index(), n=10_000)
    except D778Error:
        pass
    else:
        raise D778Error("the second implementation did not raise on a broken keep decision")
    # 5) chunk == whole for the rotation (tie-heavy)
    s = rng.integers(-1, 2, size=1201).astype(float)
    f = rng.integers(-3, 4, size=1201).astype(float)
    need(bool(np.array_equal(D7.rotation(s, f, 1), D7.rotation(s, f, 4))), "chunk != whole")
    # 6) the whole study end to end
    full = study(b, "RTY", workers=1, full=True)
    need(full["reading"] in {"NO EFFECT", "NOT ABOVE NULL", "FILTER ADDS NOTHING", "CONCENTRATED", "NO PRIZE", "SUPPORTED"},
         "the whole study")
    print("selftest OK: a planted downtrend continuation is removed and passes F; a filter tracking nothing fails F; the "
          "trend state uses no later price; the second implementation agrees and raises on a broken decision; "
          f"chunk == whole; the whole study runs (synthetic reading {full['reading']})")
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
