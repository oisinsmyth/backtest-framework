"""D779 Stage 0: the M2K closing-auction fade (D772's Lead 4) with a rates filter.
Spec: docs/decisions/D779-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-rates-filter.md.

    python scripts/stage0_d779_auction_fade_rates_filter.py --selftest
    python scripts/stage0_d779_auction_fade_rates_filter.py --run

The equity frame is D778's (stage0_d778_auction_fade_trend_filter.frame: D777's panel, c, the q80 gate, the side, the
200-session warm-up), so the base book is D778's base book exactly (asserted against its JSON). The rates state is
ZN's 09:30 -> 16:00 move on the session's ET day, from fut_day1m (bar 29's close is the 09:30 price, bar 419's the
16:00 price; both on one contract). Sessions 2016-01-01 .. 2023-12-31 only (asserted, equity and ZN).
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
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as D775  # noqa: E402
import stage0_d777_post_close_fade as D7  # noqa: E402
import stage0_d778_auction_fade_trend_filter as D8  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D779-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-rates-filter.md"
OUT = REPO / "data" / "stage0_d779_auction_fade_rates_filter.json"
D778_JSON = REPO / "data" / "stage0_d778_auction_fade_trend_filter.json"
DAY1M = D7.MAIN / "data" / "fixtures" / "fut_day1m.parquet"
PRIMARY, ORDER = "RTY", ("RTY", "ES", "YM", "NQ")
# ZN windows (bar index from 09:00 ET, start-stamped; a bar's close is the price one minute later)
WINDOWS = {"w0930": (29, 419), "w1500": (359, 419), "w1550": (409, 419)}
MAIN_W = "w0930"
EX_YEAR = "2022"
AUDIT_N, SEED, WORKERS = 40, 779, 4


class D779Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D779Error(msg)


# ================================================================================ data
def load_zn(path: Path = DAY1M) -> pd.DataFrame:
    bars = sorted({b for w in WINDOWS.values() for b in w})
    f = ((ds.field("root") == "ZN") & (ds.field("day") >= D7.START) & (ds.field("day") < D7.SEAL)
         & ds.field("bar").isin(bars))
    z = ds.dataset(str(path)).to_table(filter=f, columns=["day", "bar", "contract", "close"]).to_pandas()
    need(len(z) > 0 and bool((z["day"] < D7.SEAL).all()) and bool((z["day"] >= D7.START).all()),
         "seal: a ZN day outside 2016-01-01 .. 2023-12-31")
    need(not z.duplicated(["day", "bar"]).any(), "ZN: a duplicated (day, bar)")
    return z


def zn_state(z: pd.DataFrame) -> pd.DataFrame:
    """Per ET day and window: has (both bars present on one contract) and fell (close(b) - close(a) < 0, given has)."""
    P = z.pivot(index="day", columns="bar", values="close")
    K = z.pivot(index="day", columns="bar", values="contract")
    out = {}
    for w, (a, b) in WINDOWS.items():
        pa, pb = P.get(a), P.get(b)
        has = pa.notna() & pb.notna() & (K[a] == K[b])
        out[f"has_{w}"] = has
        out[f"fell_{w}"] = has & ((pb - pa) < 0)
    return pd.DataFrame(out)


# ================================================================================ the frame
def frame(b: pd.DataFrame, z: pd.DataFrame, root: str) -> pd.DataFrame:
    D = D8.frame(b, root)
    Z = zn_state(z)
    D = D.drop(columns=["removed", "keep", "removed2", "keep2"])       # D778's trend filter, not used here
    S = Z.reindex(D.index)
    for w in WINDOWS:
        D[f"has_{w}"] = S[f"has_{w}"].fillna(False).astype(bool)
        D[f"fell_{w}"] = S[f"fell_{w}"].fillna(False).astype(bool)    # no reading -> the trade is kept
        D[f"removed_{w}"] = D["base"] & D["fall"] & D[f"fell_{w}"]
        D[f"keep_{w}"] = D["base"] & ~D[f"removed_{w}"]
    D["zfell"], D["removed"], D["keep"] = D[f"fell_{MAIN_W}"], D[f"removed_{MAIN_W}"], D[f"keep_{MAIN_W}"]
    return D


# ================================================================================ nulls
def filter_null(D: pd.DataFrame, flag: str = "zfell") -> dict[str, Any]:
    """Delta = mean gross (filtered) - mean gross (base); the flag rotated circularly over the valid sessions, every
    offset (missing readings travel with the flag series as not-fell)."""
    V = D[D["cvalid"]]
    base, fall, fl = V["base"].to_numpy(), V["fall"].to_numpy(), V[flag].to_numpy()
    g = V["gross"].to_numpy()
    mb = g[base].mean()
    n = len(V)
    deltas = np.empty(n)
    for k in range(n):
        deltas[k] = g[base & ~(fall & np.roll(fl, k))].mean() - mb
    obs = deltas[0]
    keep = D["base"] & ~(D["fall"] & D[flag])
    need(abs(obs - (D.loc[keep, "gross"].mean() - D.loc[D["base"], "gross"].mean())) < 1e-9,
         "right quantity: the filter null's offset 0 != the observed improvement")
    d = deltas[1:]
    return {"delta": round(float(obs), 3), "p50": round(float(np.percentile(d, 50)), 3),
            "p95": round(float(np.percentile(d, 95)), 3), "rank": round(float((d < obs).mean()), 4), "n": int(len(d))}


# ================================================================================ statistics
def gates(D: pd.DataFrame, cost: float, workers: int) -> dict[str, Any]:
    T = D[D["keep"]]
    V = D[D["cvalid"]]
    out: dict[str, Any] = {"stats": D775.trade_stats(T["gross"], cost)}
    s = (V["side"] * V["keep"]).to_numpy(dtype=float)
    out["N_rotation"] = D7.rot_summary(s, V["y"].to_numpy(), workers)
    out["F_null"] = filter_null(D)
    R = D[D["removed"]]
    out["removed"] = {"n": int(len(R)), "mean_gross": round(float(R["gross"].mean()), 2) if len(R) else None,
                      "by_year": D8.grp(R, R["year"], cost) if len(R) else {}}
    R_out = R[R["year"] != EX_YEAR]
    K_out = D[D["keep"] & D["fall"] & (D["year"] != EX_YEAR)]
    fc_removed = float(R_out["gross"].mean()) if len(R_out) else float("nan")
    fc_kept = float(K_out["gross"].mean()) if len(K_out) else float("nan")
    out["F_c"] = {"removed_ex2022": {"n": int(len(R_out)), "mean_gross": round(fc_removed, 2)},
                  "kept_fall_ex2022": {"n": int(len(K_out)), "mean_gross": round(fc_kept, 2)}}
    yr = D8.grp(T, T["year"], cost)
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
    ex22 = float(T.loc[T["year"] != EX_YEAR, "gross"].mean())
    k = max(1, int(round(0.01 * len(T))))
    trimmed = float(T["gross"].sort_values().iloc[k:-k].mean())
    st = out["stats"]
    g1 = st["mean_gross"] > 0 and st["t_gross"] >= 2
    n_ok = out["N_rotation"]["obs"] > out["N_rotation"]["p95"]
    fa = out["removed"]["mean_gross"] is not None and out["removed"]["mean_gross"] < 0
    fb = out["F_null"]["delta"] > out["F_null"]["p95"]
    fcc = bool(fc_removed < fc_kept)
    f_ok = fa and fb and fcc
    g2 = st["mean_net"] > 0 and st["t_net"] >= 2 and ex_best2 > 0 and ex22 >= 2 * cost and trimmed >= 2 * cost
    out["gates"] = {"G1": bool(g1), "N": bool(n_ok), "F": bool(f_ok), "F_a": bool(fa), "F_b": bool(fb), "F_c": fcc,
                    "Y": {"pass": bool(y_i or y_ii), "full_years": full, "need": need_years, "i_win_years": int(win_years),
                          "ii_va_years": int(va_years), "va_first": round(float(hv.get("first", np.nan)), 3),
                          "va_second": round(float(hv.get("second", np.nan)), 3), "i": bool(y_i), "ii": bool(y_ii)},
                    "G2": {"pass": bool(g2), "best_two_years": best2, "net_ex_best2": round(ex_best2, 0),
                           "mean_gross_ex2022": round(ex22, 2), "trimmed_gross": round(trimmed, 2), "bar_2x": round(2 * cost, 2)}}
    out["reading"] = ("NO EFFECT" if not g1 else "NOT ABOVE NULL" if not n_ok else "FILTER ADDS NOTHING" if not f_ok else
                      "CONCENTRATED" if not (y_i or y_ii) else "NO PRIZE" if not g2 else "SUPPORTED")
    return out


def study(b: pd.DataFrame, z: pd.DataFrame, root: str, workers: int = WORKERS, full: bool = True,
          ref: dict[str, Any] | None = None) -> dict[str, Any]:
    _, mult, cost = D7.ROOTS[root]
    D = frame(b, z, root)
    need(int(D["base"].sum()) == int(D["keep"].sum()) + int(D["removed"].sum()), "right quantity: base != kept + removed")
    need(int(D["removed"].sum()) > 0, "the filter removed nothing")
    B = D[D["base"]]
    if ref is not None:                                                 # the base book is D778's, exactly
        need(int(len(B)) == ref["n"] and round(float(B["gross"].mean()), 2) == ref["mean_gross"],
             f"right quantity: {root}'s base book ({len(B)}, {B['gross'].mean():.2f}) is not D778's ({ref})")
    out = gates(D, cost, workers)
    need(out["stats"]["n"] != len(B), "right quantity: the filtered book equals the base")
    if not full:
        return out
    audit(b, z, root, D)
    out["base_book"] = {"stats": D775.trade_stats(B["gross"], cost), "by_year": D8.grp(B, B["year"], cost),
                        "book": D8.book_of(D, "base", cost)[0]}
    T = D[D["keep"]]
    bk, daily = D8.book_of(D, "keep", cost)
    out["book"] = bk
    out["other_windows"] = {}
    for w in WINDOWS:
        if w == MAIN_W:
            continue
        Tw, Rw = D[D[f"keep_{w}"]], D[D[f"removed_{w}"]]
        out["other_windows"][w] = {"stats": D775.trade_stats(Tw["gross"], cost), "removed_n": int(len(Rw)),
                                   "removed_mean_gross": round(float(Rw["gross"].mean()), 2) if len(Rw) else None,
                                   "removed_by_year": D8.grp(Rw, Rw["year"], cost) if len(Rw) else {},
                                   "F_null": filter_null(D, f"fell_{w}"), "book": D8.book_of(D, f"keep_{w}", cost)[0]}
    BF = B[B["fall"]]
    out["fall_buys_removed_share_by_year"] = {y: round(float(g["zfell"].mean()), 3) for y, g in BF.groupby("year")}
    out["zfell_share_of_sessions_by_year"] = {y: round(float(g["zfell"].mean()), 3)
                                              for y, g in D[D["cvalid"]].groupby("year")}
    out["zn_reading_share"] = round(float(D.loc[D["cvalid"], f"has_{MAIN_W}"].mean()), 4)
    out["fall_buys_by_zfell_by_year"] = {
        y: {("zfell" if z else "other"): {"n": int(len(h)), "mean_gross": round(float(h["gross"].mean()), 2)}
            for z, h in g.groupby("zfell")} for y, g in BF.groupby("year")}
    out["sides_kept"] = D8.grp(T, np.where(T["fall"], "fall (long)", "rise (short)"), cost)
    out["abs_c_terciles"] = D8.grp(T, pd.qcut(T["c"].abs().rank(method="first"), 3, labels=["low", "mid", "high"]), cost)
    out["regimes"] = D8.grp(T, np.where(T.index < D7.REGIME_1, "a_before_2020-10-26", np.where(T.index <= D7.REGIME_2,
                                                                                              "b_to_2021-06-25", "c_after")), cost)
    drift = float(D.loc[D["cvalid"], "y"].mean())
    out["drift_adjusted"] = {"drift": round(drift, 2),
                             "fall_side_kept": round(float(T.loc[T["fall"], "gross"].mean() - drift), 2),
                             "rise_side": round(float(T.loc[~T["fall"], "gross"].mean() + drift), 2)}
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


def audit(b: pd.DataFrame, z: pd.DataFrame, root: str, D: pd.DataFrame, n: int = AUDIT_N) -> None:
    """Second implementation: explicit loops over the raw equity and ZN rows for c, ZFELL, the keep decision and the
    fade. It never calls frame() or zn_state()."""
    _, mult, _ = D7.ROOTS[root]
    close: dict[tuple[str, str], float] = {}
    for r in b[b["root"] == root].itertuples(index=False):
        close[(r.session, r.hhmm)] = float(r.close)
    zc: dict[tuple[str, int], tuple[float, str]] = {}
    for r in z.itertuples(index=False):
        zc[(r.day, int(r.bar))] = (float(r.close), r.contract)
    a0, a1 = WINDOWS[MAIN_W]
    B = D[D["base"]]
    pick = B.index[np.random.default_rng(SEED).choice(len(B), size=min(n, len(B)), replace=False)]
    for s in pick:
        c = close[(s, "15:59")] - close[(s, "15:49")]
        need(abs(c - float(D.at[s, "c"])) < 1e-9, f"lag audit: c differs on {s}")
        o, e = zc.get((s, a0)), zc.get((s, a1))
        fell = o is not None and e is not None and o[1] == e[1] and e[0] - o[0] < 0
        need(fell == bool(D.at[s, "zfell"]), f"lag audit: ZFELL differs on {s}")
        keep = not (c < 0 and fell)
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
    except D779Error:
        pass
    else:
        raise D779Error("the sign audit did not raise on a mirrored book")
    ref = json.loads(D778_JSON.read_text(encoding="utf-8"))
    z = load_zn()
    b = D8.load_bars()
    res: dict[str, Any] = {"spec": SPEC.name, "window": [D7.START, "2023-12-31"], "zn_days": int(z["day"].nunique())}
    dailies = {}
    for root in ORDER:
        rs = ref[root]["base_book"]["stats"]
        r = study(b, z, root, ref={"n": rs["n"], "mean_gross": rs["mean_gross"]})
        dailies[root] = r.pop("_daily")
        res[root] = r
        print(root, "| kept", r["stats"]["n"], "mean", r["stats"]["mean_gross"], "t", r["stats"]["t_gross"], "| base",
              r["base_book"]["stats"]["mean_gross"], "| removed", r["removed"]["n"], r["removed"]["mean_gross"],
              "| F", r["F_null"], r["F_c"], "|", r["reading"], flush=True)
    res["GO"] = bool(res[PRIMARY]["reading"] == "SUPPORTED")
    rty = dailies[PRIMARY].groupby(level=0).sum()
    d775 = D7.d775_daily(b)
    _, d777 = D7.daily_book(D7.panel(b, "NQ"), 4.07)
    comp = {"d775": round(float(pd.concat([rty, d775], axis=1).fillna(0).corr().iloc[0, 1]), 3),
            "d777_mnq": round(float(pd.concat([rty, d777.groupby(level=0).sum()], axis=1).fillna(0).corr().iloc[0, 1]), 3)}
    if D7.LINES.exists():
        lines = pd.read_csv(D7.LINES, index_col=0, encoding="utf-8")
        jj = lines.join(rty.rename("d779"), how="inner")
        comp.update({c: round(float(jj["d779"].corr(jj[c])), 3) for c in lines.columns})
    res["component_rho"] = comp
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("PRIMARY", res[PRIMARY]["reading"], "GO", res["GO"], f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def _synthetic(sessions: list[str], rng: np.random.Generator, planted: bool = True,
               only_year: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Equity sessions whose closing move c reverts overnight (the fade pays), except fall-side moves on sessions
    whose synthetic ZN fell 09:30 -> 16:00, which continue (the fade loses). With planted False nothing continues;
    with only_year set, the continuation is planted in that year only. ZN has a gap of missing bars and a few contract
    changes inside a day (no reading)."""
    eq, zn, prev = [], [], None
    level = 2000.0
    zp = 120.0
    for i, d in enumerate(sessions):
        level *= math.exp(rng.normal(0.0003, 0.01))
        bars = {}
        p = level + rng.normal(0, 2)
        for h in BARS_EQ:
            p += rng.normal(0, 0.8)
            bars[h] = p
        bars["15:59"] = level
        bars["15:49"] = level - rng.normal(0, 3)
        z0 = zp + rng.normal(0, 0.05)
        z1 = z0 + rng.choice([-1, 1]) * rng.integers(1, 20) / 64
        zp = z1
        k0 = k1 = "ZNH9"
        if i % 97 == 5:
            k1 = "ZNM9"                                                 # a contract change inside the day: no reading
        if not (300 <= i < 305):                                        # a ZN gap: no reading, the trade is kept
            zn += [{"day": d, "bar": 29, "contract": k0, "close": z0}, {"day": d, "bar": 419, "contract": k1, "close": z1},
                   {"day": d, "bar": 359, "contract": k1, "close": (z0 + z1) / 2},
                   {"day": d, "bar": 409, "contract": k1, "close": z1 + rng.choice([-1, 0, 1]) / 64}]
        fell_today = (not (300 <= i < 305)) and k0 == k1 and z1 < z0
        if prev is not None:
            pc, prev_fell = prev
            if only_year is None:
                eff = -0.9 if (pc < 0 and prev_fell and planted) else 0.9
            elif pc < 0 and prev_fell:                                  # a strong continuation in that year only;
                eff = -5.0 if sessions[i - 1][:4] == only_year else 1.2  # elsewhere ZFELL drops revert MORE
            else:
                eff = 0.9
            bars["09:59"] = bars["18:04"] - eff * pc + rng.normal(0, 0.5)
        prev = (bars["15:59"] - bars["15:49"], fell_today)
        for h in BARS_EQ:
            day = d if h < "18:00" else (pd.Timestamp(d) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            eq.append({"root": "RTY", "session": d, "et": f"{day} {h}", "hhmm": h, "contract": "RTYZ9", "close": round(bars[h], 2)})
    return pd.DataFrame(eq), pd.DataFrame(zn)


BARS_EQ = D8.BARS


def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
    except D779Error:
        pass
    else:
        raise D779Error("the sign audit did not raise on a mirrored book")
    rng = np.random.default_rng(SEED)
    sessions = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", "2019-12-31")]
    # 1) a planted continuation on fall-side buys on ZFELL days: removed, and F passes (a, b and c)
    b, z = _synthetic(sessions, rng)
    r = study(b, z, "RTY", workers=1, full=False)
    need(r["removed"]["mean_gross"] < 0 and r["gates"]["F"], f"planted: F should pass {r['F_null']} {r['F_c']} {r['removed']}")
    # 2) a flag that tracks nothing: no continuation anywhere, so the removed trades earn and F fails
    b0, z0 = _synthetic(sessions, rng, planted=False)
    r0 = study(b0, z0, "RTY", workers=1, full=False)
    need(not r0["gates"]["F"], f"a flag tracking nothing must fail F: {r0['F_null']} {r0['F_c']} {r0['removed']}")
    # 2b) a continuation planted in 2022 only: F(a) and F(b) pass, and F(c) -- the other years -- must fail it
    s22 = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2019-01-02", "2023-12-29")]
    b22, z22 = _synthetic(s22, rng, only_year=EX_YEAR)
    r22 = study(b22, z22, "RTY", workers=1, full=False)
    need(r22["gates"]["F_a"] and r22["gates"]["F_b"] and not r22["gates"]["F_c"] and not r22["gates"]["F"],
         f"a 2022-only continuation must pass F(a), F(b) and fail F(c): {r22['F_null']} {r22['F_c']} {r22['removed']}")
    # 3) no reading keeps the trade; ZFELL is per session and reads no other day's price
    D = frame(b, z, "RTY")
    gap = [s for s in sessions[300:305] if s in D.index]
    need(len(gap) > 0 and not D.loc[gap, "zfell"].any() and not D.loc[gap, "removed"].any(), "a missing ZN reading removed a trade")
    swap = [s for i, s in enumerate(sessions) if i % 97 == 5 and s in D.index]
    need(len(swap) > 0 and not D.loc[swap, "zfell"].any(), "a ZN reading across two contracts was used")
    z2 = z.copy()
    late = sessions[800]
    z2.loc[(z2["day"] == late) & (z2["bar"] == 419), "close"] += 5.0
    D2 = frame(b, z2, "RTY")
    others = [s for s in D.index if s != late]
    need(D.loc[others, "zfell"].equals(D2.loc[others, "zfell"]), "ZFELL read another day's ZN price")
    # 4) the second implementation agrees, and raises on a broken decision
    audit(b, z, "RTY", D, n=10_000)
    Dx = D.copy()
    s0 = Dx[Dx["removed"]].index[0]
    Dx.loc[s0, "keep"] = True
    try:
        audit(b, z, "RTY", Dx, n=10_000)
    except D779Error:
        pass
    else:
        raise D779Error("the second implementation did not raise on a broken keep decision")
    Dz = D.copy()
    s1 = Dz[Dz["base"] & ~Dz["zfell"] & Dz[f"has_{MAIN_W}"]].index[0]
    Dz.loc[s1, "zfell"] = True
    try:
        audit(b, z, "RTY", Dz, n=10_000)
    except D779Error:
        pass
    else:
        raise D779Error("the second implementation did not raise on a broken ZFELL")
    # 5) chunk == whole for the rotation (tie-heavy)
    s = rng.integers(-1, 2, size=1201).astype(float)
    f = rng.integers(-3, 4, size=1201).astype(float)
    need(bool(np.array_equal(D7.rotation(s, f, 1), D7.rotation(s, f, 4))), "chunk != whole")
    # 6) the right-quantity guard on the base book fires
    try:
        study(b, z, "RTY", workers=1, full=False, ref={"n": -1, "mean_gross": 0.0})
    except D779Error:
        pass
    else:
        raise D779Error("the base-book reproduction guard did not fire")
    # 7) the whole study end to end
    full = study(b, z, "RTY", workers=1, full=True)
    need(full["reading"] in {"NO EFFECT", "NOT ABOVE NULL", "FILTER ADDS NOTHING", "CONCENTRATED", "NO PRIZE", "SUPPORTED"},
         "the whole study")
    print("selftest OK: a planted ZFELL continuation is removed and passes F; a flag tracking nothing fails F; a "
          "2022-only continuation passes F(a) and F(b) and fails F(c); a missing "
          "or two-contract ZN reading keeps the trade; ZFELL reads no other day; the second implementation agrees and "
          "raises on a broken keep and a broken ZFELL; chunk == whole; the base-book guard fires; the whole study runs "
          f"(synthetic reading {full['reading']})")
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
