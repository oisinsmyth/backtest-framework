"""D751 Stage 0: the gold fix on MGC. Spec: docs/decisions/D751-STAGE-0-PRE-REG-the-gold-fix-on-mgc.md.

    python scripts/stage0_d751_gold_fix.py --selftest                       # SYSTEM interpreter (pyarrow)
    uv run --no-sync python scripts/stage0_d749_month_end_fix.py --other-lines temp/d751_other_lines.csv
    python scripts/stage0_d751_gold_fix.py --run --lines temp/d751_other_lines.csv

s = sign(gold's 09:30 -> fix-5 move), gated by |move| > the median of the previous 250 sessions' |move|. Leg A: s from
fix-5 to fix+5 (into the LBMA PM auction, 15:00 London = 10:00 ET, 11:00 in DST-mismatch weeks). Leg B: -s from fix+5
to fix+30. One MGC ($5.93; 2c $11.87). Controls: the enumerated sign rotation, an 11:30 ET placebo clock, the DST
control, the phone vs ICE eras. Nothing dated 2024-01-01 or later is read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d749_month_end_fix as F49  # noqa: E402  (D749's clock rules and helpers, read-only)

MAIN_DATA = F49.MAIN_DATA
SPEC = REPO / "docs" / "decisions" / "D751-STAGE-0-PRE-REG-the-gold-fix-on-mgc.md"
OUT = REPO / "data" / "stage0_d751_gold_fix.json"
SEAL, LO, HI = "2024-01-01", "2011-01-01", "2023-12-31"
BAR0, NBAR = 540, 420
OPEN_MIN = 570                       # 09:30 ET
PLACEBO_MIN = 690                    # 11:30 ET
OZ = 10.0                            # $ per $1/oz at one MGC
GATE_N, EDGE = 250, 20
ICE = "2015-03-20"
LONDON, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")


class D751Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D751Error(msg)


def fix_et(day: str) -> int:
    y, m, d = (int(x) for x in day.split("-"))
    t = dt.datetime(y, m, d, 15, 0, tzinfo=LONDON).astimezone(NY)
    return t.hour * 60 + t.minute


def fix_et_by_rule(day: str) -> int:
    return F49.fix_et_by_rule(day) - 60          # D749's rule gives 16:00 London; the gold auction is 15:00


def load_gc() -> dict[str, Any]:
    cols = ["root", "contract", "day", "bar", "open", "close", "same_front", "present"]
    b = pd.read_parquet(MAIN_DATA / "fixtures" / "fut_day1m.parquet", columns=cols,
                        filters=[("root", "==", "GC"), ("day", ">=", "2010-01-01"), ("day", "<", SEAL)])
    need(len(b) > 0 and (b["day"] < SEAL).all(), "seal: a GC bar on or after 2024-01-01")
    ok = b.groupby("day")[["same_front", "present"]].all()
    days = np.array(sorted(b["day"].unique()))
    Op = b.pivot(index="day", columns="bar", values="open").reindex(index=days, columns=range(NBAR)).to_numpy(float)
    Cl = b.pivot(index="day", columns="bar", values="close").reindex(index=days, columns=range(NBAR)).to_numpy(float)
    return {"days": days, "Op": Op, "Cf": pd.DataFrame(Cl).ffill(axis=1).to_numpy(float),
            "good": (ok["same_front"] & ok["present"]).reindex(days).to_numpy(bool)}


def price_at(X: dict[str, Any], i: int, minute: int) -> float:
    """The price AT `minute`: the open of the bar starting there, else the last close before it."""
    k = minute - BAR0
    if k < 1 or k >= NBAR:
        return float("nan")
    o = X["Op"][i, k]
    return float(o) if np.isfinite(o) else float(X["Cf"][i, k - 1])


def legs(X: dict[str, Any], i: int, fx: int, canary: bool = False) -> dict[str, float]:
    """Signal move (09:30 -> fx-5; the canary reads to fx-4) and the A, A15, B moves, all in $/oz."""
    p0, ps = price_at(X, i, OPEN_MIN), price_at(X, i, fx - 5 + (1 if canary else 0))
    return {"sig": ps - p0, "A": price_at(X, i, fx + 5) - price_at(X, i, fx - 5),
            "A15": price_at(X, i, fx + 5) - price_at(X, i, fx - 15), "B": price_at(X, i, fx + 30) - price_at(X, i, fx + 5)}


def gate(absmv: np.ndarray, leak: bool = False) -> np.ndarray:
    """True where |move| > the median of the previous GATE_N finite values (strictly earlier; `leak` includes the
    session's own, the canary); NaN-gate (False) during burn-in."""
    out = np.zeros(len(absmv), dtype=bool)
    burn = np.ones(len(absmv), dtype=bool)
    hist: list[float] = []
    for k, v in enumerate(absmv):
        if not np.isfinite(v):
            continue
        h = hist + [v] if leak else hist
        if len(h) >= GATE_N:
            out[k] = v > float(np.median(h[-GATE_N:]))
            burn[k] = False
        hist.append(v)
    return out & ~burn


# ================================================================================ statistics
def nw_t(x: np.ndarray, lag: int = 5) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    e = x - x.mean()
    s = float(e @ e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * float(e[k:] @ e[:-k]) / n
    se = math.sqrt(s / n)
    return float(x.mean() / se) if se > 0 else float("nan")


def book(g: np.ndarray, days: list[str], side: np.ndarray, cost: float) -> dict[str, Any]:
    n = g - cost
    k = len(n)
    yrs_span = (pd.Timestamp(HI) - pd.Timestamp(LO)).days / 365.25
    tpy = k / yrs_span
    srt = np.sort(n)
    cut = max(1, int(round(0.01 * k)))
    dn = math.sqrt(float(np.mean(np.minimum(n, 0) ** 2)))
    eq = np.cumsum(n)
    yrs = pd.Series(n, index=[d[:4] for d in days]).groupby(level=0).sum()
    s = pd.Series(n)
    w, l_ = n[n > 0], n[n <= 0]
    return {"trades": k, "trades_per_year": tpy, "mean_gross": float(g.mean()), "t_gross_nw": nw_t(g), "mean_net": float(n.mean()),
            "median_net": float(np.median(n)), "sharpe_net": float(n.mean() / n.std(ddof=1) * math.sqrt(tpy)),
            "sortino_net": float(n.mean() / dn * math.sqrt(tpy)) if dn > 0 else None,
            "sharpe_gross": float(g.mean() / g.std(ddof=1) * math.sqrt(tpy)),
            "max_dd": float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()), "total_net": float(n.sum()),
            "win_rate": float((n > 0).mean()), "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s.skew()), "kurtosis": float(s.kurt()), "mean_abs_gross": float(np.abs(g).mean()),
            "mean_abs_vs_2c": float(np.abs(g).mean() / (2 * cost)), "breakeven_cost": float(g.mean()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()),
            "long_mean_gross": float(g[side > 0].mean()) if (side > 0).any() else None, "long_n": int((side > 0).sum()),
            "short_mean_gross": float(g[side < 0].mean()) if (side < 0).any() else None, "short_n": int((side < 0).sum()),
            "years": {y: round(float(v), 2) for y, v in yrs.items()},
            "positive_years": f"{int((yrs > 0).sum())} of {len(yrs)}",
            "largest_year_share": float(yrs.max() / n.sum()) if n.sum() > 0 else None}


def cost_mgc() -> float:
    j = json.loads((MAIN_DATA / "futures_costs.json").read_text(encoding="utf-8"))
    m = j["roots"]["GC"]["micro"]
    c = float(m["commission_rt_usd"]["value"]) + float(m["crossing_ticks_rt"][m["default_line"]]["value"]) * float(m["tick_usd"])
    need(m["symbol"] == "MGC" and abs(c - 5.9335) < 0.001, f"the MGC cost line moved: {c}")
    return c


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def welch(a: np.ndarray, b: np.ndarray) -> float:
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


# ================================================================================ the run
def frame(X: dict[str, Any], clock: str) -> pd.DataFrame:
    rows = []
    for i, d in enumerate(X["days"]):
        if not (LO <= d <= HI) or not X["good"][i]:
            continue
        fx = fix_et(d) if clock == "fix" else PLACEBO_MIN
        lg = legs(X, i, fx)
        rows.append({"i": i, "day": d, "fx": fx, **lg, "sig_canary": legs(X, i, fx, canary=True)["sig"]})
    f = pd.DataFrame(rows)
    f["s"] = np.sign(f["sig"])
    f["gate"] = gate(np.abs(f["sig"].to_numpy(float)))
    f["gate_canary"] = gate(np.abs(f["sig"].to_numpy(float)), leak=True)
    return f


def run(lines: Path | None) -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D751 is run-once")
    t0 = time.time()
    sign_audit()
    cost = cost_mgc()
    X = load_gc()
    F = frame(X, "fix")
    Pf = frame(X, "placebo")
    for d in F["day"].iloc[::5]:
        need(fix_et(d) == fix_et_by_rule(d), f"clock: {d}")
    need((F["fx"] == 660).any(), "right quantity: no daylight-saving-mismatch session")
    need((F["s"] != np.sign(F["sig_canary"])).any(), "lag: the fix-4 canary changed no signal")
    need((F["gate"] != F["gate_canary"]).any(), "lag: the leaky-gate canary changed no gate")
    need(not (F["fx"] == PLACEBO_MIN).any(), "right quantity: the placebo clock equals the fix clock")
    res: dict[str, Any] = {"spec": SPEC.name, "window": [LO, HI], "seal": f"nothing on or after {SEAL}", "cost_usd": cost,
                           "two_c": 2 * cost, "sessions": int(len(F)), "gated_sessions": int(F["gate"].sum()),
                           "mismatch_sessions": int((F["fx"] == 660).sum()), "legs": {}}
    ps: dict[str, float] = {}
    for leg, sign in (("A", 1.0), ("B", -1.0)):
        for gated in (True, False):
            sel = F[(F["gate"] if gated else ~F["sig"].isna()) & np.isfinite(F[leg]) & (F["s"] != 0)].reset_index(drop=True)
            side = sign * sel["s"].to_numpy(float)
            mv = sel[leg].to_numpy(float) * OZ
            g = side * mv
            key = f"{leg}_{'gated' if gated else 'ungated'}"
            r: dict[str, Any] = {"book": book(g, sel["day"].tolist(), side, cost), "O1_mean_abs_move": float(np.abs(mv).mean()),
                                 "O3_quartiles": [float(np.quantile(np.abs(mv), q)) for q in (0.25, 0.5, 0.75)]}
            if gated:
                nul = np.array([float(np.mean(np.roll(side, k) * mv)) for k in range(EDGE, len(side) - EDGE)])
                r["N1_rotation"] = {"offsets": len(nul), "p50": float(np.median(nul)), "p95": float(np.percentile(nul, 95)),
                                    "p": float((nul >= g.mean()).mean())}
                ps[leg] = r["N1_rotation"]["p"]
                pl = Pf[Pf["gate"] & np.isfinite(Pf[leg]) & (Pf["s"] != 0)]
                gp = sign * pl["s"].to_numpy(float) * pl[leg].to_numpy(float) * OZ
                r["N2_placebo_1130"] = {"n": int(len(gp)), "mean_gross": float(gp.mean()), "t": nw_t(gp), "welch_t": welch(g, gp)}
                mm = sel["fx"].to_numpy() == 660
                at10 = []
                for _, row in sel[mm].iterrows():
                    lg10 = legs(X, int(row["i"]), 600)
                    at10.append(sign * np.sign(lg10["sig"]) * lg10[leg] * OZ)
                r["N3_dst"] = {"n": int(mm.sum()), "at_real_fix": float(g[mm].mean()) if mm.any() else None,
                               "at_10_00": float(np.nanmean(at10)) if at10 else None}
                ice = (sel["day"] >= ICE).to_numpy()
                r["eras"] = {"phone": {"n": int((~ice).sum()), "mean_gross": float(g[~ice].mean()), "t": nw_t(g[~ice])},
                             "ice": {"n": int(ice.sum()), "mean_gross": float(g[ice].mean()), "t": nw_t(g[ice])}}
                if lines is not None and lines.exists():
                    ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
                    ol.index = ol.index.astype(str)
                    alld = F["day"].tolist()
                    daily = pd.Series(g - cost, index=sel["day"].tolist()).reindex(alld, fill_value=0.0)
                    r["component_corr"] = {c: float(np.corrcoef(daily.to_numpy(), ol[c].reindex(alld).fillna(0).to_numpy())[0, 1])
                                           for c in ol.columns}
                if leg == "A":
                    sel15 = F[F["gate"] & np.isfinite(F["A15"]) & (F["s"] != 0)]
                    r["A15_sensitivity_mean_gross"] = float((sel15["s"] * sel15["A15"] * OZ).mean())
            res["legs"][key] = r
    hp = holm(ps)
    for leg in ("A", "B"):
        r = res["legs"][f"{leg}_gated"]
        e = r["book"]
        no_room = r["O1_mean_abs_move"] < 2 * cost
        flow = (e["mean_gross"] > 0 and e["t_gross_nw"] >= 2 and e["mean_gross"] > r["N1_rotation"]["p95"]
                and e["mean_gross"] > r["N2_placebo_1130"]["mean_gross"] and r["N2_placebo_1130"]["welch_t"] >= 1.64)
        go = (flow and not no_room and hp[leg] <= 0.05 and e["mean_net"] > 0 and int(e["positive_years"].split(" of ")[0]) >= 8
              and e["largest_year_share"] is not None and e["largest_year_share"] < 0.5 and r["eras"]["ice"]["mean_gross"] > 0)
        r["holm_p"] = hp[leg]
        r["readings"] = {"NO_ROOM": bool(no_room), "FLOW_PRESENT": bool(flow), "GO": bool(go),
                         "reading": "NO ROOM" if no_room else ("FLOW PRESENT" if flow else "NOTHING")}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for k, r in res["legs"].items():
        e = r["book"]
        print(f"[{k}] n {e['trades']}, gross {e['mean_gross']:+.2f} (t {e['t_gross_nw']:+.2f}), net {e['mean_net']:+.2f}, "
              f"mean|move| {r['O1_mean_abs_move']:.2f}" + (f", rot p50/p95 {r['N1_rotation']['p50']:+.2f}/{r['N1_rotation']['p95']:+.2f}, "
              f"placebo {r['N2_placebo_1130']['mean_gross']:+.2f}, reading {r['readings']['reading']}" if "N1_rotation" in r else ""))
    return 0


# ================================================================================ self-test
def sign_audit() -> None:
    X = {"Op": np.full((1, NBAR), 1900.0), "Cf": np.full((1, NBAR), 1900.0)}
    X["Op"][0, 61:], X["Cf"][0, 61:] = 1902.0, 1902.0           # +$2/oz from 10:01
    lg = legs(X, 0, 600)
    need(lg["A"] * OZ > 0 and +1 * lg["A"] * OZ > 0 and -1 * lg["A"] * OZ < 0, f"sign: a rise did not pay the long A leg ({lg})")


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D751Error as e:
        fails.append(str(e))
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2011-01-01", "2023-12-31")]
    bad = [d for d in days if fix_et(d) != fix_et_by_rule(d)]
    if bad:
        fails.append(f"clock: {len(bad)} days differ, e.g. {bad[:3]}")
    if fix_et("2019-10-31") != 660 or fix_et("2019-06-28") != 600:
        fails.append("clock: a known date is wrong")
    v = np.r_[np.arange(1, 300, dtype=float)]
    g1, g2 = gate(v), gate(v, leak=True)
    if g1[:GATE_N].any() or not g1[GATE_N:].all():
        fails.append("gate: a rising series must pass every post-burn-in session against the strictly earlier median")
    if (g1 == g2).all():
        fails.append("gate: the leaky canary changed nothing on a synthetic series")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money; the 15:00-London clock equals the statutory rule on every business day "
          "2011-2023 (11:00 ET in the mismatch week); the walk-forward gate uses strictly earlier sessions and its leaky "
          "canary differs")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run(a.lines)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
