"""D766 Stage 0: crowded leverage and the MBT day (prop book), as pre-registered in
docs/decisions/D766-STAGE-0-PRE-REG-crowded-leverage-and-the-mbt-day.md.

    uv run --no-sync python scripts/stage0_d766_crowded_leverage.py --selftest
    uv run --no-sync python scripts/stage0_d766_crowded_leverage.py --run     # once; writes data/stage0_d766_crowded_leverage.json

F_d = the mean of Binance BTCUSDT funding settled at 16:00 UTC on d-1, 00:00 and 08:00 UTC on d. L: F_d above the prior
250 sessions' 90th percentile; S: below the 10th. r_d = P(16:00 ET) - P(09:30 ET) on CME BTC (fut_btc_1m), $ per MBT.
G1: the contrarian mean against the exact rotation of the L/S flags; G2: gross >= $4.31 at NW(5) t >= 2; G3 episodes.
In-sample only (<= 2023-12-29). Ranks/reporting helpers from D763; the clock and minute conversion from D764.
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
import stage0_d763_expiry_open as D3  # noqa: E402  (dist, sharpe_sortino, clean)
import stage0_d764_btc_expiry_window as D4  # noqa: E402  (to_minutes, STALE)

SPEC = REPO / "docs" / "decisions" / "D766-STAGE-0-PRE-REG-crowded-leverage-and-the-mbt-day.md"
OUT = REPO / "data" / "stage0_d766_crowded_leverage.json"
FUND = REPO / "data" / "fixtures" / "perp_funding.csv"
OI = REPO / "data" / "fixtures" / "perp_open_interest_daily.csv"
BTC = REPO / "data" / "fixtures" / "fut_btc_1m.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
SEAL = "2024-01-01"
ET = ZoneInfo("America/New_York")
WF, QHI, QLO, GAP, MIN_EPIS, T_MIN = 250, 90.0, 10.0, 5, 8, 2.0


class D766Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D766Error(msg)


def seal(dates: pd.Series, what: str) -> None:
    """Called on every input after its text cut; the self-test proves it raises on a 2024 row."""
    need(not (dates.astype(str) >= SEAL).any(), f"the seal: a {what} row on or after 2024-01-01")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ the signal
def load_funding(venue: str, symbol: str, f: pd.DataFrame | None = None) -> pd.Series:
    if f is None:
        f = pd.read_csv(FUND, usecols=["venue", "symbol", "settlement_utc", "funding_rate"], dtype={"settlement_utc": str}, encoding="utf-8")
    f = f[(f["venue"] == venue) & (f["symbol"] == symbol) & (f["settlement_utc"] < SEAL)]
    seal(f["settlement_utc"], "funding")
    ts = pd.to_datetime(f["settlement_utc"], utc=True).dt.floor("min")
    s = pd.Series(f["funding_rate"].to_numpy(float), index=ts)
    return s[~s.index.duplicated()].sort_index()


def f_of_day(fund: pd.Series, day: str, include_16_today: bool = False) -> float:
    """Mean of the funding settled at 16:00 UTC on d-1, 00:00 and 08:00 UTC on d (the break adds 16:00 UTC on d)."""
    d = pd.Timestamp(str(day), tz="UTC")
    keys = [d - pd.Timedelta(hours=8), d, d + pd.Timedelta(hours=8)] + ([d + pd.Timedelta(hours=16)] if include_16_today else [])
    v = [fund.get(k, np.nan) for k in keys]
    return float(np.mean(v)) if all(np.isfinite(v)) else float("nan")


def flags(F: np.ndarray, wf: int = WF) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """c = -1 (crowded long, L), +1 (crowded short, S), 0 otherwise; NaN thresholds before the burn-in."""
    n = F.size
    hi, lo = np.full(n, np.nan), np.full(n, np.nan)
    for i in range(wf, n):
        w = F[i - wf:i]
        w = w[np.isfinite(w)]
        if w.size >= wf * 0.9:
            hi[i], lo[i] = np.percentile(w, QHI), np.percentile(w, QLO)
    c = np.where(F > hi, -1, np.where(F < lo, 1, 0))
    c = np.where(np.isfinite(hi) & np.isfinite(F), c, 0)
    return c.astype(int), hi, lo


# ================================================================================ the outcome
def et_min(day: str, hh: int, mm: int) -> int:
    d = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), hh, mm, tzinfo=ET).astimezone(timezone.utc)
    return int(d.timestamp() // 60)


def load_btc() -> pd.DataFrame:
    parts = []
    for ch in pd.read_csv(BTC, usecols=["root", "day", "ts_utc", "close"], dtype={"day": str, "ts_utc": str}, chunksize=500_000, encoding="utf-8"):
        ch = ch[(ch["root"] == "BTC") & (ch["day"] < SEAL) & (ch["day"] >= "2019-09-01")]
        if len(ch):
            parts.append(ch)
    b = pd.concat(parts, ignore_index=True)
    seal(b["day"], "btc")
    b["tm"] = D4.to_minutes(b["ts_utc"])
    return b.sort_values(["day", "tm"]).reset_index(drop=True)


def day_moves(b: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for d, s in b.groupby("day"):
        if pd.Timestamp(d).weekday() > 4:
            continue
        tm, cl = s["tm"].to_numpy(), s["close"].to_numpy(float)
        p = []
        for t in (et_min(d, 9, 30), et_min(d, 16, 0)):
            i = int(np.searchsorted(tm, t, side="left")) - 1
            p.append(float(cl[i]) if i >= 0 and t - tm[i] <= D4.STALE else float("nan"))
        rows.append((d, p[0], p[1]))
    f = pd.DataFrame(rows, columns=["day", "p0930", "p1600"])
    f["r_pts"] = f["p1600"] - f["p0930"]
    return f


# ================================================================================ statistics
def contrarian_mean(c: np.ndarray, r: np.ndarray) -> float:
    m = c != 0
    return float((c[m] * r[m]).mean()) if m.any() else float("nan")


def rotation(c: np.ndarray, r: np.ndarray) -> dict:
    obs = contrarian_mean(c, r)
    null = np.array([contrarian_mean(np.roll(c, k), r) for k in range(1, c.size)])
    null = null[np.isfinite(null)]
    return {"A": obs, "offset0": contrarian_mean(np.roll(c, 0), r), "offsets": int(null.size),
            "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)),
            "p_one_sided": float((1 + (null >= obs).sum()) / (1 + null.size))}


def nw_t(x: np.ndarray, lags: int = 5) -> float:
    x = np.asarray(x, float)
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * float((e[L:] * e[:-L]).sum())
    return float(x.mean() / math.sqrt(s / n / n)) if s > 0 else float("nan")


def episodes(c: np.ndarray, gap: int = GAP) -> list[tuple[int, int, int]]:
    """Maximal runs of the same nonzero side with gaps of at most `gap` sessions: (side, first index, last index)."""
    out, cur = [], None
    for i, v in enumerate(c):
        if v == 0:
            continue
        if cur is not None and v == cur[0] and i - cur[2] <= gap + 1:
            cur = (cur[0], cur[1], i)
        else:
            if cur is not None:
                out.append(cur)
            cur = (int(v), i, i)
    if cur is not None:
        out.append(cur)
    return out


# ================================================================================ lag audit
def lag_audit(fund: pd.Series, days, F, c, sample, include_16_today: bool = False) -> None:
    raw = {k: v for k, v in fund.items()}
    for i in sample:
        d = days[i]
        base = pd.Timestamp(str(d), tz="UTC")
        ks = [base - pd.Timedelta(hours=8), base, base + pd.Timedelta(hours=8)] + ([base + pd.Timedelta(hours=16)] if include_16_today else [])
        need(all(k <= base + pd.Timedelta(hours=8) for k in ks), f"lag: a settlement after 08:00 UTC on {d}")
        vals = [raw.get(k) for k in ks]
        f = float("nan") if any(v is None for v in vals) else sum(vals) / len(vals)
        need((math.isnan(f) and math.isnan(F[i])) or math.isclose(f, F[i], rel_tol=1e-12), f"lag: F at {d}")
        if i >= WF:
            prev = sorted(x for x in F[i - WF:i] if math.isfinite(x))
            if len(prev) >= WF * 0.9:
                def pct(q):
                    h = (len(prev) - 1) * q / 100
                    lo_ = int(math.floor(h))
                    return prev[lo_] + (h - lo_) * (prev[min(lo_ + 1, len(prev) - 1)] - prev[lo_])
                want = -1 if F[i] > pct(QHI) else (1 if F[i] < pct(QLO) else 0)
                need(want == c[i], f"lag: flag at {d}")


# ================================================================================ the run
def evaluate(fund: pd.Series, mv: pd.DataFrame, upp: float, cost: float) -> dict:
    days = mv["day"].to_numpy(str)
    F = np.array([f_of_day(fund, d) for d in days])
    ok = np.isfinite(F) & mv["r_pts"].notna().to_numpy()
    days, F = days[ok], F[ok]
    r = mv["r_pts"].to_numpy(float)[ok] * upp
    c, hi, lo = flags(F)
    live = np.isfinite(hi)
    days, F, r, c = days[live], F[live], r[live], c[live]
    rot = rotation(c, r)
    need(math.isclose(rot["offset0"], rot["A"], rel_tol=0, abs_tol=1e-12), "rotation offset 0 != observed")
    m = c != 0
    g = c[m] * r[m]
    gd = D3.dist(g)
    t_nw = nw_t(g)
    ep = episodes(c)
    net = g - cost
    tr = pd.DataFrame({"day": days[m], "side": c[m], "gross": g, "net": net})
    tr["year"] = tr["day"].str[:4]
    ep_net = []
    for side, a, b_ in ep:
        sel = (days[m] >= days[a]) & (days[m] <= days[b_])
        ep_net.append(float(net[sel].sum()))
    tot = float(net.sum())
    g3 = bool(len(ep) >= MIN_EPIS and float(net[tr["year"] != "2021"].sum()) > 0 and float(net[tr["year"] != "2022"].sum()) > 0
              and tot > 0 and max(ep_net) / tot <= 0.5)
    absr = np.abs(r)
    size = {"mean_abs_crowded": float(absr[m].mean()), "mean_abs_other": float(absr[~m].mean()),
            "ratio": float(absr[m].mean() / absr[~m].mean())}
    sn = np.array([absr[np.roll(c, k) != 0].mean() / absr[np.roll(c, k) == 0].mean() for k in range(1, c.size)])
    size.update({"null_p50": float(np.percentile(sn, 50)), "null_p95": float(np.percentile(sn, 95)), "rank": float((sn < size["ratio"]).mean())})
    return {"days": days, "F": F, "r": r, "c": c, "rot": rot, "gross": gd, "t_nw": t_nw, "episodes": ep, "episode_net": ep_net,
            "tr": tr, "g3": g3, "size": size, "n": int(days.size), "n_L": int((c == -1).sum()), "n_S": int((c == 1).sum())}


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    fraw = pd.read_csv(FUND, usecols=["venue", "symbol", "settlement_utc", "funding_rate"], dtype={"settlement_utc": str}, encoding="utf-8")
    fraw = fraw[fraw["settlement_utc"] < SEAL]
    fund = load_funding("binance", "BTCUSDT", fraw)
    b = load_btc()
    mv = day_moves(b)
    cc = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]["BTC"]["micro"]
    cost = float(cc["commission_rt_usd"]["value"] + cc["crossing_ticks_rt"][cc["default_line"]]["value"] * cc["tick_usd"])
    upp, tick = float(cc["usd_per_point"]), float(cc["tick_usd"])
    ev = evaluate(fund, mv, upp, cost)
    rng = np.random.default_rng(766)
    samp = [int(i) for i in rng.choice(np.arange(ev["n"]), size=40, replace=False)]
    # the lag audit runs on the full eligible F series so its walk-forward window matches the flags
    lag_audit(fund, ev["days"], ev["F"], ev["c"], [i for i in samp if i >= WF] + [i for i in samp if i < WF])
    rot, gd = ev["rot"], ev["gross"]
    g1 = bool(rot["A"] > 0 and rot["A"] > rot["p95"])
    g2 = bool(gd["mean"] >= cost and ev["t_nw"] >= T_MIN)
    g3 = ev["g3"]
    reading = "NO DIRECTION" if not g1 else ("DIRECTION, NO PRIZE" if not g2 else ("EPISODIC" if not g3 else "PREMISE HOLDS"))
    tr = ev["tr"]
    cal = ev["days"]
    dn = tr.set_index("day")["net"].reindex(cal, fill_value=0.0).to_numpy()
    dg = tr.set_index("day")["gross"].reindex(cal, fill_value=0.0).to_numpy()
    eq = np.cumsum(dn)
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    rho_b = {}
    for nm, gb in bk.groupby("book"):
        sb = gb.groupby("session")["net"].sum()
        span = cal[(cal >= max(min(cal), min(sb.index))) & (cal <= min(max(cal), max(sb.index)))]
        s1 = pd.Series(dn, index=cal).reindex(span).to_numpy()
        rho_b[nm] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if span.size > 30 and s1.std() > 0 else None
    # reported: L and S apart, quintile tails, open interest, the Bybit inverse long sample
    c, r = ev["c"], ev["r"]
    sides = {"L_short": D3.dist(-r[c == -1]), "S_long": D3.dist(r[c == 1])}
    F = ev["F"]
    hi20 = np.array([np.percentile(F[max(0, i - WF):i], 80) if i >= WF else np.nan for i in range(F.size)])
    lo20 = np.array([np.percentile(F[max(0, i - WF):i], 20) if i >= WF else np.nan for i in range(F.size)])
    cq = np.where(F > hi20, -1, np.where(F < lo20, 1, 0))
    oi = pd.read_csv(OI, dtype={"day_utc": str}, encoding="utf-8")
    oi = oi[(oi["venue"] == "bybit_linear") & (oi["symbol"] == "BTCUSDT") & (oi["day_utc"] < SEAL)]
    oi = oi.assign(day=oi["day_utc"].str[:10]).set_index("day")["open_interest_contracts"].sort_index()
    doi = oi.diff()
    rising = np.array([bool(doi.get(d, np.nan) > 0) if np.isfinite(doi.get(d, np.nan)) else False for d in cal])
    has_oi = np.array([np.isfinite(doi.get(d, np.nan)) for d in cal])
    Lm = c == -1
    oi_rep = {"L_rising_oi": D3.dist(-r[Lm & rising & has_oi]), "L_flat_or_falling_oi": D3.dist(-r[Lm & ~rising & has_oi])}
    fund_b = load_funding("bybit_inverse", "BTCUSD", fraw)
    evb = evaluate(fund_b, mv, upp, cost)
    res = {"record": "D766", "reading": reading,
           "sessions": {"eligible_after_burn_in": ev["n"], "L": ev["n_L"], "S": ev["n_S"], "first": str(cal[0]), "last": str(cal[-1])},
           "G1": dict(rot, **{"pass": g1}),
           "G2": {"trades": int((c != 0).sum()), "gross": gd, "t_nw": ev["t_nw"], "cost": cost, "pass": g2},
           "G3": {"episodes": len(ev["episodes"]), "episode_list": [{"side": "L" if s == -1 else "S", "from": str(cal[a]), "to": str(cal[b_]),
                                                                    "days": int((c[a:b_ + 1] == s).sum()), "net": nt}
                                                                   for (s, a, b_), nt in zip(ev["episodes"], ev["episode_net"])],
                  "net_ex_2021": float(tr.loc[tr["year"] != "2021", "net"].sum()), "net_ex_2022": float(tr.loc[tr["year"] != "2022", "net"].sum()),
                  "pass": g3},
           "trade": {"net": D3.dist(tr["net"]), "net_plus_one_tick": D3.dist(tr["net"] - tick),
                     "daily_net_sharpe_sortino": D3.sharpe_sortino(dn), "daily_gross_sharpe_sortino": D3.sharpe_sortino(dg),
                     "max_dd_usd": float((np.maximum.accumulate(eq) - eq).max()), "total_net": float(tr["net"].sum()),
                     "by_year": {k: {"n": int(len(v)), "net": float(v["net"].sum())} for k, v in tr.groupby("year")},
                     "top5": tr.sort_values("net", ascending=False).head(5)[["day", "side", "net"]].to_dict("records"),
                     "bottom5": tr.sort_values("net").head(5)[["day", "side", "net"]].to_dict("records"), "rho_books": rho_b},
           "reported": {"size": ev["size"], "sides": sides, "quintile_contrarian": D3.dist(cq[cq != 0] * r[cq != 0]),
                        "open_interest": oi_rep,
                        "bybit_inverse": {"n": evb["n"], "L": evb["n_L"], "S": evb["n_S"], "A": evb["rot"]["A"], "p95": evb["rot"]["p95"],
                                          "p": evb["rot"]["p_one_sided"], "gross": evb["gross"], "t_nw": evb["t_nw"], "episodes": len(evb["episodes"]),
                                          "first": str(evb["days"][0])}},
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(D3.clean(res), fh, indent=1, default=str)
        fh.write("\n")
    print(f"[D766] {reading}: n {ev['n']} (L {ev['n_L']}, S {ev['n_S']}); A {rot['A']:+.2f} (p05 {rot['p05']:+.2f} p50 {rot['p50']:+.2f} "
          f"p95 {rot['p95']:+.2f}; p {rot['p_one_sided']:.3f})")
    print(f"  G2 gross {gd['mean']:+.2f} (NW t {ev['t_nw']:.2f}, med {gd['median']:+.2f}) vs {cost:.2f}; G3 episodes {len(ev['episodes'])}, pass {g3}")
    print(f"  size {ev['size']}")
    print(f"  sides {json.dumps(D3.clean({k: {kk: v.get(kk) for kk in ('n', 'mean', 't', 'median')} for k, v in sides.items()}))}")
    print(f"  bybit inverse {json.dumps(D3.clean({k: v for k, v in res['reported']['bybit_inverse'].items() if k != 'gross'}))}")
    print(f"[D766] wall {res['wall_s']} s")
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    rng = np.random.default_rng(7)
    # the clock
    if datetime.fromtimestamp(et_min("2021-01-15", 9, 30) * 60, tz=timezone.utc).hour != 14 or \
            datetime.fromtimestamp(et_min("2021-07-15", 9, 30) * 60, tz=timezone.utc).hour != 13:
        fails.append("clock")
    # synthetic funding: every 8 h for 400 days
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2020-01-06", periods=400)]
    idx = pd.date_range("2020-01-04", periods=2000, freq="8h", tz="UTC")
    fund = pd.Series(rng.normal(1e-4, 2e-4, idx.size), index=idx)
    F = np.array([f_of_day(fund, d) for d in days])
    c, hi, lo = flags(F)
    try:
        lag_audit(fund, np.array(days), F, c, list(range(250, 290)))
    except D766Error as e:
        fails.append(f"lag audit raised on the truth: {e}")
    try:
        lag_audit(fund, np.array(days), F, c, [260], include_16_today=True)
        fails.append("lag audit did not raise on the same-day 16:00 settlement")
    except D766Error:
        pass
    # sign in money: short on a crowded-long day pays when the price falls
    if contrarian_mean(np.array([-1]), np.array([-30.0])) != 30.0:
        fails.append("sign in money")
    # the seal
    try:
        seal(pd.Series(["2023-12-29", "2024-01-02T00:00:00Z"]), "test")
        fails.append("seal did not raise")
    except D766Error:
        pass
    # episodes
    if [(s, a, b) for s, a, b in episodes(np.array([0, -1, -1, 0, 0, -1, 0, 0, 0, 0, 0, 0, 1, 1]))] != [(-1, 1, 5), (1, 12, 13)]:
        fails.append("episodes")
    # synthetic G1: planted contrarian passes; noise fails ~95 %; an AR(1) signal against independent returns fails ~95 %
    n = 900
    cpl = rng.choice([-1, 0, 0, 0, 0, 1], n)
    rpl = 0.8 * cpl * 50 + rng.normal(0, 100, n)          # L (c = -1) days fall, S days rise: the contrarian side pays
    rp = rotation(cpl, rpl)
    if not rp["A"] > rp["p95"]:
        fails.append("planted contrarian did not pass G1")
    nf = na = 0
    for s in range(100):
        r2 = np.random.default_rng(300 + s)
        cn = r2.choice([-1, 0, 0, 0, 0, 1], n)
        rn = r2.normal(0, 100, n)
        rr = rotation(cn, rn)
        nf += int(not rr["A"] > rr["p95"])
        z = np.zeros(n)
        e = r2.normal(size=n)
        for i in range(1, n):
            z[i] = 0.98 * z[i - 1] + e[i]
        ca = np.where(z > np.percentile(z, 90), -1, np.where(z < np.percentile(z, 10), 1, 0))
        ra = rotation(ca, r2.normal(0, 100, n))
        na += int(not ra["A"] > ra["p95"])
    print(f"  noise fails G1 {nf} / 100; persistent AR(1) signal fails G1 {na} / 100")
    if not 88 <= nf <= 100:
        fails.append(f"noise fails G1 {nf}/100")
    if not 85 <= na <= 100:
        fails.append(f"AR(1) fails G1 {na}/100")
    for f_ in fails:
        print(f"[SELFTEST FAIL] {f_}")
    print(f"[D766] selftest: {'FAIL' if fails else 'all passed'}")
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
