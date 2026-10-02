"""D764 Stage 0: the CME bitcoin expiry window (prop book), as pre-registered in
docs/decisions/D764-STAGE-0-PRE-REG-the-bitcoin-expiry-window.md (00b6509d).

    uv run --no-sync python scripts/stage0_d764_btc_expiry_window.py --selftest
    uv run --no-sync python scripts/stage0_d764_btc_expiry_window.py --run     # once; writes data/stage0_d764_btc_expiry_window.json

BTC front bars from fut_btc_1m (UTC bar starts), 2017-12-18 -> 2023-12-29. On the last Friday of the month (CME
expiry; CF Bitcoin Reference Rate computed 15:00-16:00 London), x = P(16:00 London) - P(15:00), y = P(17:00) - P(16:00);
P(t) = the close of the last bar starting before t, ineligible if that bar started more than 10 minutes before t.
E1: delta = rho(x, y | expiry) - rho(x, y | other Fridays) against the full exact rotation of the label; E2: the fade's
gross >= $4.31 (one MBT) at t >= 2. In-sample only. Ranks, rotation and reporting helpers from D763's runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d763_expiry_open as D3  # noqa: E402  (rank_avg, spearman, delta, rotation, dist, sharpe_sortino, clean)

SPEC = REPO / "docs" / "decisions" / "D764-STAGE-0-PRE-REG-the-bitcoin-expiry-window.md"
OUT = REPO / "data" / "stage0_d764_btc_expiry_window.json"
FIX = REPO / "data" / "fixtures" / "fut_btc_1m.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
FIRST, SEAL = "2017-12-18", "2024-01-01"
LON, ET = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")
STALE = 10                                                      # minutes
SUBST = {"2018-03-30": "2018-03-29", "2020-12-25": "2020-12-24"}
MBT_START = "2021-05-03"
T_MIN = 2.0


class D764Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D764Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seal_check(df: pd.DataFrame) -> None:
    need(not (df["day"] >= SEAL).any(), "the seal: a row on or after 2024-01-01")


# ================================================================================ calendar and clock
def last_friday(y: int, m: int) -> pd.Timestamp:
    nxt = pd.Timestamp(year=y + (m == 12), month=m % 12 + 1, day=1)
    d = nxt - pd.Timedelta(days=1)
    return d - pd.Timedelta(days=(d.weekday() - 4) % 7)


def expiry_days() -> list[str]:
    out = []
    for y in range(2018, 2024):
        for m in range(1, 13):
            d = last_friday(y, m).strftime("%Y-%m-%d")
            out.append(SUBST.get(d, d))
    return out


def check_calendar(E: list[str]) -> None:
    need(len(E) == 72 and len(set(E)) == 72, f"calendar: {len(E)} expiry days")
    for e in E:
        wd = pd.Timestamp(e).weekday()
        need(wd == 4 or e in SUBST.values(), f"calendar: {e} is not a Friday nor a declared substitute")
    for must in ("2018-01-26", "2018-03-29", "2020-12-24"):
        need(must in E, f"calendar: {must} missing")


def utc_min(day: str, hh: int, mm: int = 0) -> int:
    """Minutes since the epoch (UTC) of hh:mm London on day."""
    d = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), hh, mm, tzinfo=LON).astimezone(timezone.utc)
    return int(d.timestamp() // 60)


# ================================================================================ data
def load() -> pd.DataFrame:
    parts = []
    for ch in pd.read_csv(FIX, usecols=["root", "day", "ts_utc", "contract", "close", "volume"], dtype={"day": str, "ts_utc": str, "contract": str},
                          chunksize=500_000, encoding="utf-8"):
        ch = ch[(ch["root"] == "BTC") & (ch["day"] < SEAL) & (ch["day"] >= FIRST)]
        if len(ch):
            parts.append(ch)
    b = pd.concat(parts, ignore_index=True)
    seal_check(b)
    b["tm"] = (pd.to_datetime(b["ts_utc"], utc=True).astype("int64") // 60_000_000_000).astype(np.int64)
    return b.sort_values(["day", "tm"]).reset_index(drop=True)


def price_at(tm: np.ndarray, cl: np.ndarray, t: int, at_or_before: bool = False) -> float:
    """Close of the last bar starting before t (or at t, the deliberate break), NaN if stale."""
    i = int(np.searchsorted(tm, t, side="right" if at_or_before else "left")) - 1
    if i < 0 or t - tm[i] > STALE:
        return float("nan")
    return float(cl[i])


def sessions(b: pd.DataFrame, days: list[str], at_or_before: bool = False) -> pd.DataFrame:
    rows = []
    g = {d: s for d, s in b.groupby("day")}
    for d in days:
        s = g.get(d)
        if s is None:
            continue
        tm, cl, vol = s["tm"].to_numpy(), s["close"].to_numpy(float), s["volume"].to_numpy(float)
        t0, t1, t2 = utc_min(d, 15), utc_min(d, 16), utc_min(d, 17)
        p = {k: price_at(tm, cl, t, at_or_before) for k, t in (("p0", t0), ("p1", t1), ("p2", t2), ("p3", t1 + 120), ("pm", t0 - 60))}
        wv = float(vol[(tm >= t0) & (tm < t1)].sum())
        rows.append(dict(day=d, contract=s["contract"].iloc[0], window_volume=wv, **p))
    f = pd.DataFrame(rows)
    f["x"], f["y"], f["y2"], f["pre"] = f["p1"] - f["p0"], f["p2"] - f["p1"], f["p3"] - f["p1"], f["p0"] - f["pm"]
    return f


def lag_audit(b: pd.DataFrame, f: pd.DataFrame, sample: list[int]) -> None:
    g = {d: s for d, s in b.groupby("day")}
    for i in sample:
        r = f.iloc[i]
        s = g[r["day"]]
        for key, t in (("p0", utc_min(r["day"], 15)), ("p1", utc_min(r["day"], 16)), ("p2", utc_min(r["day"], 17))):
            best = None
            for tm_, c_ in zip(s["tm"].tolist(), s["close"].tolist()):
                if tm_ < t and (best is None or tm_ >= best[0]):
                    best = (tm_, c_)
            want = float("nan") if best is None or t - best[0] > STALE else float(best[1])
            got = float(r[key])
            need((math.isnan(want) and math.isnan(got)) or math.isclose(want, got, rel_tol=0, abs_tol=1e-9),
                 f"lag: {key} at {r['day']}: {want} vs {got}")


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    E = expiry_days()
    check_calendar(E)
    b = load()
    all_days = sorted(b["day"].unique())
    fridays = [d for d in all_days if pd.Timestamp(d).weekday() == 4]
    units = sorted(set(fridays) | (set(E) & set(all_days)))
    f = sessions(b, units)
    f["E"] = f["day"].isin(E)
    ok = f[["x", "y"]].notna().all(1)
    rng = np.random.default_rng(764)
    ie = np.flatnonzero(f["E"].to_numpy() & ok.to_numpy())
    samp = list(rng.choice(ie, size=min(20, ie.size), replace=False)) + list(rng.choice(np.arange(len(f)), size=20, replace=False))
    lag_audit(b, f, [int(i) for i in samp])
    g = f[ok].reset_index(drop=True)
    lab = g["E"].to_numpy()
    x, y = g["x"].to_numpy(float), g["y"].to_numpy(float)
    rot = D3.rotation(x, y, lab)
    need(math.isclose(rot["offset0"], rot["delta"], rel_tol=0, abs_tol=1e-15), "rotation offset 0 != observed")
    # two-sided rank of delta (reported)
    null = np.array([D3.delta(x, y, np.roll(lab, k)) for k in range(1, lab.size)])
    rot["rank"] = float((null < rot["delta"]).mean())
    c = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]["BTC"]["micro"]
    cost = float(c["commission_rt_usd"]["value"] + c["crossing_ticks_rt"][c["default_line"]]["value"] * c["tick_usd"])
    upp, tick = float(c["usd_per_point"]), float(c["tick_usd"])
    side = -np.sign(x)
    gross = side * y * upp
    tk, tc = lab & (side != 0), (~lab) & (side != 0)
    gE, gC = D3.dist(gross[tk]), D3.dist(gross[tc])
    welch = (gE["mean"] - gC["mean"]) / math.sqrt(gE["sd"] ** 2 / gE["n"] + gC["sd"] ** 2 / gC["n"])
    e1 = bool(rot["delta"] < 0 and rot["delta"] < rot["p05"])
    e2 = bool(gE["mean"] >= cost and gE["t"] >= T_MIN)
    reading = "NO EFFECT" if not e1 else ("PREMISE HOLDS" if e2 else "EFFECT, NO PRIZE")
    tr = pd.DataFrame({"day": g["day"][tk].to_numpy(), "side": side[tk], "gross": gross[tk], "net": gross[tk] - cost})
    cal = np.array(all_days)
    dn = tr.groupby("day")["net"].sum().reindex(cal, fill_value=0.0).to_numpy()
    dg = tr.groupby("day")["gross"].sum().reindex(cal, fill_value=0.0).to_numpy()
    eq = np.cumsum(dn)
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    rho_b = {}
    for nm, gb in bk.groupby("book"):
        sb = gb.groupby("session")["net"].sum()
        span = cal[(cal >= max(min(cal), min(sb.index))) & (cal <= min(max(cal), max(sb.index)))]
        s1 = pd.Series(dn, index=cal).reindex(span).to_numpy()
        rho_b[nm] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if span.size > 30 and s1.std() > 0 else None
    top = tr.sort_values("net", ascending=False)
    yrs = g["day"].str[:4].to_numpy()
    mbt = (g["day"] >= MBT_START).to_numpy()
    ok2 = g["y2"].notna().to_numpy()
    okp = g["pre"].notna().to_numpy()
    res = {"record": "D764 (00b6509d)", "reading": reading,
           "sessions": {"btc_sessions": len(all_days), "units": len(units), "eligible": int(len(g)), "E_eligible": int(lab.sum()),
                        "E_missing_or_stale": sorted(set(E) - set(g.loc[g["E"], "day"])), "C_eligible": int((~lab).sum())},
           "E1": dict(rot, **{"pass": e1}),
           "E2": {"trades": int(tk.sum()), "gross": gE, "net": D3.dist(gross[tk] - cost), "cost": cost, "pass": e2,
                  "control_fridays_gross": gC, "welch_t_E_minus_C": welch, "net_plus_one_tick": D3.dist(gross[tk] - cost - tick),
                  "daily_net_sharpe_sortino": D3.sharpe_sortino(dn), "daily_gross_sharpe_sortino": D3.sharpe_sortino(dg),
                  "max_dd_usd": float((np.maximum.accumulate(eq) - eq).max()),
                  "by_year": {k: {"n": int(len(v)), "net": float(v["net"].sum())} for k, v in tr.assign(yr=tr["day"].str[:4]).groupby("yr")},
                  "long_short": {("long" if k > 0 else "short"): D3.dist(v["net"]) for k, v in tr.groupby("side")},
                  "top5": top.head(5)[["day", "net"]].to_dict("records"), "bottom5": top.tail(5)[["day", "net"]].to_dict("records"),
                  "rho_books": rho_b},
           "reported": {"mean_x_usd_E": float(x[lab].mean() * upp), "mean_x_usd_C": float(x[~lab].mean() * upp),
                        "t_mean_x_E": D3.dist(x[lab] * upp)["t"], "mean_abs_x_usd_E": float(np.abs(x[lab]).mean() * upp),
                        "mean_abs_x_usd_C": float(np.abs(x[~lab]).mean() * upp), "mean_abs_y_usd_E": float(np.abs(y[lab]).mean() * upp),
                        "mean_abs_y_usd_C": float(np.abs(y[~lab]).mean() * upp),
                        "window_volume_median_E": float(g.loc[lab, "window_volume"].median()),
                        "window_volume_median_C": float(g.loc[~lab, "window_volume"].median()),
                        "rho_x_y2_E": D3.spearman(x[lab & ok2], g["y2"].to_numpy(float)[lab & ok2]),
                        "rho_x_y2_C": D3.spearman(x[~lab & ok2], g["y2"].to_numpy(float)[~lab & ok2]),
                        "rho_pre_x_E": D3.spearman(g["pre"].to_numpy(float)[lab & okp], x[lab & okp]),
                        "rho_pre_x_C": D3.spearman(g["pre"].to_numpy(float)[~lab & okp], x[~lab & okp]),
                        "mbt_era": {"rho_E": D3.spearman(x[lab & mbt], y[lab & mbt]), "rho_C": D3.spearman(x[~lab & mbt], y[~lab & mbt]),
                                    "n_E": int((lab & mbt).sum()), "fade_gross_E": D3.dist(gross[tk & mbt])},
                        "rho_E_by_year": {yr: D3.spearman(x[lab & (yrs == yr)], y[lab & (yrs == yr)]) for yr in sorted(set(yrs))}},
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(D3.clean(res), fh, indent=1, default=str)
        fh.write("\n")
    e = res["E1"]
    print(f"[D764] {reading}: rho_E {e['rho_E']:+.3f} (n {e['n_E']}) rho_C {e['rho_C']:+.3f} (n {e['n_C']}); delta {e['delta']:+.3f} "
          f"(p05 {e['p05']:+.3f} p50 {e['p50']:+.3f} p95 {e['p95']:+.3f}; p {e['p_one_sided']:.3f}; rank {e['rank']:.3f})")
    print(f"  E2 n {res['E2']['trades']} gross {gE['mean']:+.2f} (t {gE['t']:.2f}, med {gE['median']:+.2f}) vs cost {cost:.2f}; "
          f"control gross {gC['mean']:+.2f}; Welch {welch:+.2f}")
    print(f"  sessions {res['sessions']}")
    print(f"  reported {json.dumps(D3.clean({k: v for k, v in res['reported'].items() if k != 'rho_E_by_year'}))}")
    print(f"[D764] wall {res['wall_s']} s")
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    E = expiry_days()
    try:
        check_calendar(E)
    except D764Error as e:
        fails.append(f"calendar raised: {e}")
    try:
        check_calendar([d for d in E if d != "2018-03-29"] + ["2018-03-30"])
        fails.append("calendar did not raise on an unsubstituted Good Friday")
    except D764Error:
        pass
    # the clock: 15:00 London is 15:00 UTC in January, 14:00 UTC in July, and 11:00 ET in a mismatch week
    def hhmm_utc(day, hh):
        return datetime.fromtimestamp(utc_min(day, hh) * 60, tz=timezone.utc)
    if hhmm_utc("2019-01-25", 15).hour != 15 or hhmm_utc("2019-07-26", 15).hour != 14 or \
            hhmm_utc("2018-03-23", 15).astimezone(ET).hour != 11 or hhmm_utc("2019-07-26", 15).astimezone(ET).hour != 10:
        fails.append("clock")
    # the lag audit on synthetic raw rows: passes on the truth; the at-t bar (the break) must raise
    day = "2019-07-26"
    t1 = utc_min(day, 16)
    tm = np.arange(utc_min(day, 13), utc_min(day, 19), dtype=np.int64)
    rng = np.random.default_rng(1)
    cl = 10000 + np.cumsum(rng.normal(0, 5, tm.size))
    b = pd.DataFrame({"day": day, "tm": tm, "close": cl, "volume": 1.0, "contract": "BTCQ9"})
    f = sessions(b, [day])
    try:
        lag_audit(b, f, [0])
    except D764Error as e:
        fails.append(f"lag audit raised on the truth: {e}")
    try:
        lag_audit(b, sessions(b, [day], at_or_before=True), [0])
        fails.append("lag audit did not raise on the at-t bar")
    except D764Error:
        pass
    # staleness: remove the bars in the 15 minutes before t1, and P(t1) must be NaN
    b2 = b[(b["tm"] < t1 - 15) | (b["tm"] >= t1)]
    if not math.isnan(sessions(b2, [day])["p1"].iloc[0]):
        fails.append("staleness guard")
    # sign in money
    if float(-np.sign(10.0) * (-20.0) * 0.1) != 2.0:
        fails.append("sign in money")
    # the seal
    try:
        seal_check(pd.DataFrame({"day": ["2024-01-05"]}))
        fails.append("seal did not raise")
    except D764Error:
        pass
    # synthetic on the real label pattern (last Fridays among Fridays): planted reversal passes; noise fails ~95 %
    fr = sorted({d.strftime("%Y-%m-%d") for d in pd.date_range("2018-01-05", "2023-12-29", freq="W-FRI")} | set(E))
    lab = np.isin(fr, E)
    n = lab.size
    xs = rng.normal(size=n)
    ys = np.where(lab, -0.6 * xs, 0.0) + rng.normal(size=n)
    rt = D3.rotation(xs, ys, lab)
    if not rt["delta"] < rt["p05"]:
        fails.append("planted reversal did not pass E1")
    nf = 0
    for s in range(100):
        r2 = np.random.default_rng(200 + s)
        rr = D3.rotation(r2.normal(size=n), r2.normal(size=n), lab)
        nf += int(not rr["delta"] < rr["p05"])
    print(f"  noise fails E1 {nf} / 100")
    if not 88 <= nf <= 100:
        fails.append(f"noise fails E1 {nf}/100")
    for f_ in fails:
        print(f"[SELFTEST FAIL] {f_}")
    print(f"[D764] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
