"""D755 Stage 0: the ECB press-conference drift on M6E. Spec: docs/decisions/D755-STAGE-0-PRE-REG-the-ecb-press-conference-drift.md.

    python scripts/stage0_d755_ecb_press_conference.py --selftest            # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d755_ecb_press_conference.py --extract             # 6E minutes from the raw ohlcv-1m archive
    uv run --no-sync python scripts/stage0_d749_month_end_fix.py --other-lines temp/d755_other_lines.csv
    python scripts/stage0_d755_ecb_press_conference.py --run --lines temp/d755_other_lines.csv

J = P(T_p) - P(T_d), the statement's reaction up to the press conference; trade sign(J) from T_p+2 to T_p+60 on one
M6E ($4.38; 2c $8.76). Controls: the enumerated sign rotation, placebo Thursdays at the same Frankfurt clock, an FOMC
replication (reported). Times come from data/calendar/ecb_meetings.csv. Nothing dated 2024-01-01 or later is read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SPEC = REPO / "docs" / "decisions" / "D755-STAGE-0-PRE-REG-the-ecb-press-conference-drift.md"
CAL = REPO / "data" / "calendar" / "ecb_meetings.csv"
OUT = REPO / "data" / "stage0_d755_ecb_press_conference.json"
CACHE = REPO / "temp" / "d755_6e_1m.parquet"
SEAL, LO, HI = "2024-01-01", "2011-01-01", "2023-12-31"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
KEEP = [(360, 720), (810, 960)]            # ET minutes kept: 06:00-12:00 (ECB) and 13:30-16:00 (FOMC replication)
EUR, TICK = 12500.0, 0.0001
COST = 3.0 + 1.105885654136043 * 1.25      # d508_exec, $4.38
FRA, NY = ZoneInfo("Europe/Berlin"), ZoneInfo("America/New_York")
GATE_PIPS = 25
WORKERS = 8


class D755Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D755Error(msg)


# ================================================================================ the clock
def et_minute(day: str, hhmm: str) -> int:
    y, m, d = (int(x) for x in day.split("-"))
    h, mi = (int(x) for x in hhmm.split(":"))
    t = dt.datetime(y, m, d, h, mi, tzinfo=FRA).astimezone(NY)
    return t.hour * 60 + t.minute


def _nth_sunday(y: int, m: int, n: int) -> dt.date:
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_sunday(y: int, m: int) -> dt.date:
    d = (dt.date(y, m + 1, 1) - dt.timedelta(days=1)) if m < 12 else dt.date(y, 12, 31)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)


def et_minute_by_rule(day: str, hhmm: str) -> int:
    """Second implementation: EU summer time (last Sun Mar -> last Sun Oct), US DST (2nd Sun Mar -> 1st Sun Nov)."""
    d = dt.date.fromisoformat(day)
    eu = 2 if _last_sunday(d.year, 3) <= d < _last_sunday(d.year, 10) else 1
    us = -4 if _nth_sunday(d.year, 3, 2) <= d < _nth_sunday(d.year, 11, 1) else -5
    h, mi = (int(x) for x in hhmm.split(":"))
    return (h - eu + us) * 60 + mi


# ================================================================================ extraction (raw archive)
def _extract_file(path: str) -> pd.DataFrame | None:
    import databento as db
    sys.path.insert(0, str(REPO / "scripts"))
    import build_fut_breadth_hourly as BH
    store = db.DBNStore.from_file(path)
    w = BH.ids_of(store)
    if w is None:
        return None
    w = w[w["root"] == "6E"]
    if len(w) == 0:
        return None
    parts = []
    for arr in store.to_ndarray(count=BH.CHUNK):
        a = arr[np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32)) & (arr["ts_event"] < SEAL_NS)]
        if a.size == 0:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64),
                            "open": a["open"] * BH.PX, "high": a["high"] * BH.PX, "low": a["low"] * BH.PX,
                            "close": a["close"] * BH.PX, "volume": a["volume"].astype(np.int64)})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
        if len(j) == 0:
            continue
        need(not j.duplicated(["iid", "ts"]).any(), "a 6E bar claimed by more than one mapping window")
        ts = pd.to_datetime(j["ts"].to_numpy(), utc=True).tz_convert("America/New_York")
        minute = (ts.hour * 60 + ts.minute).to_numpy()
        keep = np.zeros(len(j), dtype=bool)
        for a0, a1 in KEEP:
            keep |= (minute >= a0) & (minute < a1)
        if not keep.any():
            continue
        parts.append(pd.DataFrame({"contract": j["contract"].to_numpy()[keep], "day": np.asarray(ts.strftime("%Y-%m-%d"))[keep],
                                   "minute": minute[keep].astype(np.int16), "open": j["open"].to_numpy()[keep],
                                   "close": j["close"].to_numpy()[keep], "volume": j["volume"].to_numpy()[keep]}))
    return pd.concat(parts, ignore_index=True) if parts else None


def extract() -> int:
    raw = sorted(p for d in sorted((MAIN_DATA / "raw" / "databento").glob("GLBX-*")) for p in d.glob("*.ohlcv-1m.dbn.zst"))
    print(f"{len(raw)} ohlcv-1m files", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(WORKERS) as ex:
        got = [g for g in ex.map(_extract_file, [str(p) for p in raw]) if g is not None]
    df = pd.concat(got, ignore_index=True)
    need((df["day"] < SEAL).all(), "seal: a 6E minute on or after 2024-01-01")
    # the front: fut_breadth_hourly's 6E contract per day, not re-elected
    import io
    sys.path.insert(0, str(REPO / "scripts"))
    import forward_f2_c1_ledgers as FW
    bh = pd.read_csv(io.BytesIO(FW.restrict_text(MAIN_DATA / "fixtures" / "fut_breadth_hourly.csv.gz", 1, SEAL)),
                     usecols=["root", "day", "contract"], dtype={"day": str})
    front = bh[bh["root"] == "6E"].set_index("day")["contract"]
    df = df[df["contract"].to_numpy() == front.reindex(df["day"]).to_numpy()]
    need(not df.duplicated(["day", "minute"]).any(), "duplicate front-contract minutes")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["day", "minute"]).to_parquet(CACHE, index=False)
    print(f"6E front minutes: {len(df):,} rows, {df['day'].nunique()} days, {df['day'].min()} -> {df['day'].max()}, "
          f"{(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


# ================================================================================ prices
def load_minutes() -> dict[str, Any]:
    df = pd.read_parquet(CACHE)
    need((df["day"] < SEAL).all(), "seal: the cache holds a minute on or after 2024-01-01")
    days = np.array(sorted(df["day"].unique()))
    cols = list(range(KEEP[0][0], KEEP[-1][1]))
    O = df.pivot(index="day", columns="minute", values="open").reindex(index=days, columns=cols).to_numpy(float)
    C = df.pivot(index="day", columns="minute", values="close").reindex(index=days, columns=cols).to_numpy(float)
    Cf = pd.DataFrame(C).ffill(axis=1).to_numpy(float)
    return {"days": days, "pos": {d: i for i, d in enumerate(days)}, "O": O, "Cf": Cf, "m0": KEEP[0][0]}


def price_at(X: dict[str, Any], i: int, minute: int) -> float:
    """The price AT `minute`: the close of the bar starting at minute - 1 (carried forward)."""
    k = minute - 1 - X["m0"]
    return float(X["Cf"][i, k]) if 0 <= k < X["Cf"].shape[1] else float("nan")


def open_at(X: dict[str, Any], i: int, minute: int) -> float:
    k = minute - X["m0"]
    if not 0 <= k < X["O"].shape[1]:
        return float("nan")
    o = X["O"][i, k]
    return float(o) if np.isfinite(o) else price_at(X, i, minute)


def event_trade(X: dict[str, Any], day: str, td: int, tp: int, canary: bool = False) -> dict[str, float] | None:
    i = X["pos"].get(day)
    if i is None:
        return None
    J = price_at(X, i, tp + (1 if canary else 0)) - price_at(X, i, td)
    if not np.isfinite(J) or J == 0:
        return None
    s = float(np.sign(J))
    e = open_at(X, i, tp + 2)
    x60, x30 = price_at(X, i, tp + 60), price_at(X, i, tp + 30)
    pre = price_at(X, i, tp) - open_at(X, i, td + 5)
    if not (np.isfinite(e) and np.isfinite(x60)):
        return None
    return {"J_pips": J / TICK, "s": s, "move60": (x60 - e) * EUR, "move30": (x30 - e) * EUR, "pre": pre * EUR}


# ================================================================================ statistics
def tstat(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def welch(a: np.ndarray, b: np.ndarray) -> float:
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


def book(g: np.ndarray, days: list[str], cost: float, per_year: float) -> dict[str, Any]:
    n = g - cost
    k = len(n)
    srt = np.sort(n)
    cut = max(1, int(round(0.01 * k)))
    dn = math.sqrt(float(np.mean(np.minimum(n, 0) ** 2)))
    eq = np.cumsum(n)
    yrs = pd.Series(n, index=[d[:4] for d in days]).groupby(level=0).sum()
    s = pd.Series(n)
    w, l_ = n[n > 0], n[n <= 0]
    return {"trades": k, "mean_gross": float(g.mean()), "t_gross": tstat(g), "mean_net": float(n.mean()),
            "median_net": float(np.median(n)), "sharpe_net": float(n.mean() / n.std(ddof=1) * math.sqrt(per_year)),
            "sortino_net": float(n.mean() / dn * math.sqrt(per_year)) if dn > 0 else None,
            "sharpe_gross": float(g.mean() / g.std(ddof=1) * math.sqrt(per_year)),
            "max_dd": float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()), "total_net": float(n.sum()),
            "win_rate": float((n > 0).mean()), "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s.skew()), "kurtosis": float(s.kurt()), "mean_abs_gross": float(np.abs(g).mean()),
            "mean_abs_vs_2c": float(np.abs(g).mean() / (2 * cost)), "breakeven_cost": float(g.mean()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()) if k > 2 * cut else None,
            "years": {y: round(float(v), 2) for y, v in yrs.items()}, "positive_years": f"{int((yrs > 0).sum())} of {len(yrs)}",
            "largest_year_share": float(yrs.max() / n.sum()) if n.sum() > 0 else None}


# ================================================================================ the run
def load_calendar() -> pd.DataFrame:
    import hashlib
    meta = json.loads(CAL.with_suffix(".meta.json").read_text(encoding="utf-8"))
    need(hashlib.sha256(CAL.read_bytes()).hexdigest() == meta["sha256"], "the ECB calendar differs from its committed hash")
    c = pd.read_csv(CAL, encoding="utf-8", dtype=str)
    c = c[(c["date"] >= LO) & (c["date"] <= HI)].reset_index(drop=True)
    need(len(c) > 50, f"the ECB calendar has only {len(c)} rows in the window")
    return c


def run(lines: Path | None) -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D755 is run-once")
    t0 = time.time()
    sign_audit()
    X = load_minutes()
    cal = load_calendar()
    rows, missing = [], []
    for _, r in cal.iterrows():
        d = r["date"]
        td, tp = et_minute(d, r["decision_release_time_cet"]), et_minute(d, r["press_conference_start_cet"])
        need(td == et_minute_by_rule(d, r["decision_release_time_cet"]) and tp == et_minute_by_rule(d, r["press_conference_start_cet"]),
             f"clock: {d}")
        t = event_trade(X, d, td, tp)
        if t is None:
            missing.append(d)
            continue
        rows.append({"day": d, "td": td, "tp": tp, "decision": r.get("decision", ""), **t,
                     "s_canary": (event_trade(X, d, td, tp, canary=True) or {"s": np.nan})["s"]})
    E = pd.DataFrame(rows)
    need(len(E) + len(missing) == len(cal), "right quantity: the calendar rows used differ from the rows read")
    need(bool((E["tp"] + 2 > E["tp"]).all() and (E["tp"] > E["td"]).all()), "lag: the entry is not after J's last bar")
    need((E["s"] != E["s_canary"]).any(), "lag: the T_p-bar canary changed no sign")
    # meetings in the weeks when Frankfurt and New York are 5 hours apart, not 6 (reported)
    mismatch = [d for d in E["day"] if et_minute(d, "12:00") != 360]
    ecb_days = set(cal["date"])
    # placebo Thursdays: the most recent meeting's Frankfurt clock
    cal_sorted = cal.sort_values("date")
    plc = []
    for d in map(str, X["days"]):
        if not (LO <= d <= HI) or d in ecb_days or pd.Timestamp(d).weekday() != 3:
            continue
        prev = cal_sorted[cal_sorted["date"] < d]
        if len(prev) == 0:
            continue
        rr = prev.iloc[-1]
        td, tp = et_minute(d, rr["decision_release_time_cet"]), et_minute(d, rr["press_conference_start_cet"])
        t = event_trade(X, d, td, tp)
        if t is not None:
            plc.append({"day": d, **t})
    Pdf = pd.DataFrame(plc)
    need(not set(Pdf["day"]) & ecb_days, "right quantity: a placebo day is an ECB day")
    g = (E["s"] * E["move60"]).to_numpy(float)
    gp = (Pdf["s"] * Pdf["move60"]).to_numpy(float)
    per_year = len(E) / 13.0
    s_arr, mv = E["s"].to_numpy(float), E["move60"].to_numpy(float)
    nul = np.array([float(np.mean(np.roll(s_arr, k) * mv)) for k in range(1, len(E))])
    gate = np.abs(E["J_pips"].to_numpy(float)) >= GATE_PIPS
    era = np.where(E["day"] < "2011-11-01", "trichet", np.where(E["day"] < "2019-11-01", "draghi", "lagarde"))
    res: dict[str, Any] = {
        "spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "cost": COST, "two_c": 2 * COST,
        "calendar_rows": int(len(cal)), "events_scored": int(len(E)), "events_without_bars": missing,
        "events_in_dst_mismatch_weeks": mismatch,
        "placebo_thursdays": int(len(Pdf)),
        "O1_mean_abs_move_ecb": float(np.abs(mv).mean()), "O1_mean_abs_move_placebo": float(np.abs(Pdf["move60"]).mean()),
        "O1_welch_abs": welch(np.abs(mv), np.abs(Pdf["move60"].to_numpy(float))),
        "O3_abs_quartiles": [float(np.quantile(np.abs(mv), q)) for q in (0.25, 0.5, 0.75)],
        "J_abs_pips_median": float(np.median(np.abs(E["J_pips"]))),
        "P": book(g, E["day"].tolist(), COST, per_year),
        "P_at_1p5x_cost": float((g - 1.5 * COST).mean()),
        "N1_rotation": {"offsets": int(len(nul)), "p05": float(np.percentile(nul, 5)), "p50": float(np.median(nul)),
                        "p95": float(np.percentile(nul, 95)), "p_up": float((nul >= g.mean()).mean())},
        "N2_placebo": {"n": int(len(gp)), "mean_gross": float(gp.mean()), "t": tstat(gp), "welch_t": welch(g, gp)},
        "gated_J25": {"n": int(gate.sum()), "mean_gross": float(g[gate].mean()) if gate.any() else None, "t": tstat(g[gate])},
        "exit_30": {"mean_gross": float((E["s"] * E["move30"]).mean()), "t": tstat((E["s"] * E["move30"]).to_numpy(float))},
        "E_pre": {"mean_gross": float((E["s"] * E["pre"]).mean()), "t": tstat((E["s"] * E["pre"]).to_numpy(float))},
        "eras": {e: {"n": int((era == e).sum()), "mean_gross": float(g[era == e].mean()) if (era == e).any() else None,
                     "t": tstat(g[era == e])} for e in ("trichet", "draghi", "lagarde")},
        "by_decision": {k: {"n": int((E["decision"] == k).sum()), "mean_gross": float(g[(E["decision"] == k).to_numpy()].mean())}
                        for k in sorted(set(E["decision"])) if (E["decision"] == k).sum() > 0},
    }
    # N3: the FOMC replication on M6E (2019-2023, every meeting had a press conference; reported only)
    ev = pd.read_csv(MAIN_DATA / "calendar" / "events.csv", encoding="utf-8")
    fom = ev[ev["event"] == "FOMC"].copy()
    fom["day"] = fom["datetime_et"].str[:10]
    fom = fom[(fom["day"] >= "2019-01-01") & (fom["day"] <= HI) & (fom["datetime_et"].str[11:16] == "14:00")]  # scheduled
    f_rows = []
    for _, r in fom.iterrows():
        hh, mm = int(r["datetime_et"][11:13]), int(r["datetime_et"][14:16])
        td = hh * 60 + mm
        t = event_trade(X, r["day"], td, td + 30)
        if t is not None:
            f_rows.append(t["s"] * t["move60"])
    res["N3_fomc_2019_2023"] = {"n": len(f_rows), "mean_gross": float(np.mean(f_rows)) if f_rows else None, "t": tstat(np.array(f_rows))}
    if lines is not None and lines.exists():
        ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
        ol.index = ol.index.astype(str)
        # over the other lines' own span only (they start 2016-02-24): ECB days before it would pair with false zeros
        alld = sorted(set(ol.index) | {d for d in E["day"] if ol.index.min() <= d <= ol.index.max()})
        tr = pd.Series(g - COST, index=E["day"].tolist())
        res["component_corr"] = {c: float(np.corrcoef(tr.reindex(alld, fill_value=0.0), ol[c].reindex(alld).fillna(0.0))[0, 1]) for c in ol.columns}
        res["component_corr_span"] = [ol.index.min(), ol.index.max(), int(tr.index.isin(alld).sum())]
    e = res["P"]
    no_room = res["O1_mean_abs_move_ecb"] < 2 * COST
    cont = (e["mean_gross"] > 0 and e["t_gross"] >= 2 and e["mean_gross"] > res["N1_rotation"]["p95"]
            and e["mean_gross"] > res["N2_placebo"]["mean_gross"] and res["N2_placebo"]["welch_t"] >= 1.64)
    rev = e["mean_gross"] < 0 and e["t_gross"] <= -2 and e["mean_gross"] < res["N1_rotation"]["p05"]
    go = (cont and not no_room and e["mean_net"] > 0 and int(e["positive_years"].split(" of ")[0]) >= 8
          and e["largest_year_share"] is not None and e["largest_year_share"] < 0.5 and (res["eras"]["lagarde"]["mean_gross"] or -1) > 0)
    res["readings"] = {"NO_ROOM": bool(no_room), "NOT_SPECIAL": bool(res["O1_welch_abs"] < 2), "CONTINUATION": bool(cont),
                       "REVERSAL": bool(rev), "GO": bool(go),
                       "reading": "NO ROOM" if no_room else ("CONTINUATION" if cont else ("REVERSAL" if rev else "NOTHING"))}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("readings", "events_scored", "O1_mean_abs_move_ecb", "O1_mean_abs_move_placebo",
                                          "N1_rotation", "N2_placebo", "eras", "N3_fomc_2019_2023")}, indent=1, default=float))
    print(json.dumps({k: res["P"][k] for k in ("trades", "mean_gross", "t_gross", "mean_net", "positive_years")}, indent=1))
    return 0


# ================================================================================ self-test
def sign_audit(up: float = 1.0) -> None:
    """A rising statement reaction must go long and a continued rise must pay it. `up` = -1 mirrors the path (the
    self-test's deliberately broken book, which must raise)."""
    X = {"pos": {"2020-01-02": 0}, "m0": 360, "O": np.full((1, 600), 1.1000), "Cf": np.full((1, 600), 1.1000)}
    X["O"][0, 120:], X["Cf"][0, 120:] = 1.1000 + up * 0.0005, 1.1000 + up * 0.0005   # the reaction at 08:00 ET
    t = event_trade(X, "2020-01-02", 465, 510)                     # T_d 07:45, T_p 08:30
    need(t is not None and t["s"] > 0, "sign: an up statement reaction did not give a long")
    X2 = {"pos": {"2020-01-02": 0}, "m0": 360, "O": np.full((1, 600), 1.1000), "Cf": np.full((1, 600), 1.1000)}
    X2["O"][0, 120:], X2["Cf"][0, 120:] = 1.1005, 1.1005
    X2["O"][0, 160:], X2["Cf"][0, 160:] = 1.1015, 1.1015           # a further rise from 08:40, inside the hold
    t2 = event_trade(X2, "2020-01-02", 465, 510)
    need(t2 is not None and t2["s"] * t2["move60"] > 0, f"sign: a continued rise did not pay the long ({t2})")


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D755Error as e:
        fails.append(str(e))
    try:
        sign_audit(up=-1.0)
        fails.append("sign: the audit did not raise on a mirrored (broken) book")
    except D755Error:
        pass
    days =[d.strftime("%Y-%m-%d") for d in pd.bdate_range(LO, HI)]
    bad = [d for d in days for hm in ("13:45", "14:15", "14:30", "14:45") if et_minute(d, hm) != et_minute_by_rule(d, hm)]
    if bad:
        fails.append(f"clock: {len(bad)} disagreements, e.g. {bad[:3]}")
    if et_minute("2019-10-24", "13:45") != 465 or et_minute("2019-03-07", "13:45") != 465 or et_minute("2015-03-20", "13:45") != 525:
        fails.append("clock: a known conversion is wrong")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money (an up statement reaction goes long and a continued rise pays); the "
          "Frankfurt -> New York clock equals the statutory-rule implementation on every business day 2011-2023")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.extract:
        return extract()
    if a.run:
        return run(a.lines)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
