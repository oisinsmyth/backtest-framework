"""D758 Stage 0: the CME bitcoin weekend gap on MBT. Spec: docs/decisions/D758-STAGE-0-PRE-REG-the-cme-bitcoin-weekend-gap.md.

    python scripts/stage0_d758_btc_weekend_gap.py --selftest      # SYSTEM interpreter (pyarrow for the calm gate)
    python scripts/stage0_d758_btc_weekend_gap.py --run --lines temp/d755_other_lines.csv

G = P(Sun 18:05 ET) - F (Friday's last traded price, same contract); fade s = -sign(G) from the first bar at or after
18:06 to P(Mon 09:30 ET), one MBT ($4.31; 2c $8.62). Touch test: the Monday path trades at F (fill) or at R + G (the
mirror). Controls: the enumerated sign rotation and Mon-Thu reopens after the daily halt. Nothing dated 2024-01-01 or
later is read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
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
import forward_f2_c1_ledgers as FW  # noqa: E402
from stage0_d755_ecb_press_conference import book, tstat, welch  # noqa: E402

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SPEC = REPO / "docs" / "decisions" / "D758-STAGE-0-PRE-REG-the-cme-bitcoin-weekend-gap.md"
FIX = MAIN_DATA / "fixtures" / "fut_btc_1m.csv.gz"
OUT = REPO / "data" / "stage0_d758_btc_weekend_gap.json"
SEAL, LO = "2024-01-01", "2018-01-01"
USD_PER_PT = 0.1                                     # MBT: 0.1 bitcoin
COST = 3.0 + 2.6161168726417716 * 0.5                # d508_exec, $4.31
MBT_LIST = "2021-05-03"
NY = ZoneInfo("America/New_York")
EPOCH = dt.datetime(1970, 1, 1)


class D758Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D758Error(msg)


# ================================================================================ the clock
def et_minutes(ts_utc: pd.Series) -> np.ndarray:
    """ET wall-clock minutes since 1970-01-01 00:00 (naive), by zoneinfo."""
    t = pd.to_datetime(ts_utc, utc=True).dt.tz_convert(NY).dt.tz_localize(None)
    return ((t - pd.Timestamp(EPOCH)) // pd.Timedelta(minutes=1)).to_numpy(np.int64)


def _nth_sunday(y: int, m: int, n: int) -> dt.date:
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def et_minutes_by_rule(ts_utc: pd.Series) -> np.ndarray:
    """Second implementation: US DST from the 2nd Sunday of March 07:00 UTC to the 1st Sunday of November 06:00 UTC."""
    t = pd.to_datetime(ts_utc, utc=True).dt.tz_localize(None)
    yrs = sorted(set(t.dt.year))
    start = {y: pd.Timestamp(_nth_sunday(y, 3, 2)) + pd.Timedelta(hours=7) for y in yrs}
    end = {y: pd.Timestamp(_nth_sunday(y, 11, 1)) + pd.Timedelta(hours=6) for y in yrs}
    s = t.dt.year.map(start)
    e = t.dt.year.map(end)
    off = np.where((t >= s) & (t < e), -4, -5)
    loc = t + pd.to_timedelta(off, unit="h")
    return ((loc - pd.Timestamp(EPOCH)) // pd.Timedelta(minutes=1)).to_numpy(np.int64)


def wall(day: str, hhmm: str, days_back: int = 0) -> int:
    d = dt.date.fromisoformat(day) - dt.timedelta(days=days_back)
    h, m = (int(x) for x in hhmm.split(":"))
    return int((dt.datetime(d.year, d.month, d.day, h, m) - EPOCH).total_seconds() // 60)


# ================================================================================ data
def load() -> dict[str, Any]:
    b = pd.read_csv(io.BytesIO(FW.restrict_text(FIX, 1, SEAL)), dtype={"day": str}, encoding="utf-8")
    b = b[(b["root"] == "BTC") & (b["day"] < SEAL)].copy()
    need(bool((pd.to_datetime(b["ts_utc"], utc=True) < pd.Timestamp(SEAL, tz="UTC")).all()), "seal: a bar on or after 2024")
    b["m"] = et_minutes(b["ts_utc"])
    rule = et_minutes_by_rule(b["ts_utc"])
    need(bool((b["m"].to_numpy() == rule).all()), f"clock: zoneinfo and the statutory rule disagree on {int((b['m'].to_numpy() != rule).sum())} bars")
    b = b.sort_values(["day", "m"]).reset_index(drop=True)
    days = b["day"].to_numpy()
    cut = np.flatnonzero(np.r_[True, days[1:] != days[:-1], True])
    sess = {days[cut[i]]: (int(cut[i]), int(cut[i + 1])) for i in range(len(cut) - 1)}
    return {"m": b["m"].to_numpy(np.int64), "o": b["open"].to_numpy(float), "h": b["high"].to_numpy(float),
            "l": b["low"].to_numpy(float), "c": b["close"].to_numpy(float), "k": b["contract"].to_numpy(),
            "days": sorted(sess), "sess": sess}


def px_before(X: dict[str, Any], a: int, z: int, t: int) -> float:
    """P(t): the close of the last bar in [a, z) starting before t (nan if none)."""
    j = int(np.searchsorted(X["m"][a:z], t, side="left")) - 1
    return float(X["c"][a + j]) if j >= 0 else float("nan")


def first_at(X: dict[str, Any], a: int, z: int, t: int) -> int:
    """Index of the first bar in [a, z) starting at or after t (-1 if none)."""
    j = int(np.searchsorted(X["m"][a:z], t, side="left"))
    return a + j if a + j < z else -1


# ================================================================================ one reopen
def reopen_trade(X: dict[str, Any], p: str, d: str, open_back: int, canary: bool = False) -> dict[str, Any] | None:
    """p = the previous session, d = the reopening session whose nominal open is 18:00 ET `open_back` days before d."""
    a0, z0 = X["sess"][p]
    a, z = X["sess"][d]
    F = float(X["c"][z0 - 1])
    t_open = wall(d, "18:00", open_back)
    R = px_before(X, a, z, t_open + (6 if canary else 5))
    if not np.isfinite(R) or X["k"][z0 - 1] != X["k"][a]:
        return {"excluded": "roll" if X["k"][z0 - 1] != X["k"][a] else "no bar in the first five minutes"}
    G = R - F
    if G == 0:
        return {"excluded": "zero gap"}
    s = -float(np.sign(G))
    t930, t1600 = wall(d, "09:30"), wall(d, "16:00")
    e = first_at(X, a, z, t_open + 6)
    if e < 0 or X["m"][e] >= t930:
        return {"excluded": "no bar between 18:06 and 09:30"}
    x930, x1600 = px_before(X, a, z, t930), px_before(X, a, z, t1600)
    k930 = int(np.searchsorted(X["m"][a:z], t930, side="left")) + a    # bars [e, k930) start before 09:30
    hi, lo = float(X["h"][e:k930].max()), float(X["l"][e:k930].min())
    mirror = R + G
    fill_touch = (lo <= F) if G > 0 else (hi >= F)
    mirror_touch = (hi >= mirror) if G > 0 else (lo <= mirror)
    entry = float(X["o"][e])
    # the folklore's own trade: exit at F if touched (a resting limit), else 09:30
    tgt = (F - entry) * s if fill_touch else (x930 - entry) * s
    # the day-session version: the gap still open at 09:30, faded 09:31 -> 16:00
    g2 = x930 - F
    e2 = first_at(X, a, z, wall(d, "09:31"))
    day_move = (x1600 - float(X["o"][e2])) * -np.sign(g2) if (e2 >= 0 and X["m"][e2] < t1600 and g2 != 0) else float("nan")
    fri_range = float(X["h"][a0:z0].max() - X["l"][a0:z0].min())
    return {"day": d, "G": G * USD_PER_PT, "G_range": abs(G) / fri_range if fri_range > 0 else float("nan"), "s": s,
            "entry_late_min": int(X["m"][e] - (t_open + 6)), "move930": (x930 - entry) * USD_PER_PT,
            "move1600": (x1600 - entry) * USD_PER_PT, "fill": bool(fill_touch), "mirror": bool(mirror_touch),
            "target": tgt * USD_PER_PT, "day_session": day_move * USD_PER_PT,
            "first_bar_late_min": int(X["m"][a] - t_open)}


def classify(X: dict[str, Any]) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, int]], list[tuple[str, str]]]:
    """Weekend events (Mon trade date, previous = the Friday), placebos (previous = the day before, Tue-Fri), holiday reopens."""
    wk, plc, hol = [], [], []
    days = X["days"]
    for p, d in zip(days[:-1], days[1:]):
        if d < LO:
            continue
        dd, pp = dt.date.fromisoformat(d), dt.date.fromisoformat(p)
        if dd.weekday() == 0 and (dd - pp).days == 3:
            wk.append((p, d, 1))
        elif dd.weekday() in (1, 2, 3, 4) and (dd - pp).days == 1:
            plc.append((p, d, 1))
        else:
            hol.append((p, d))
    return wk, plc, hol


def sign_test(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return float("nan")
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


# ================================================================================ the run
def run(lines: Path | None) -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D758 is run-once")
    t0 = time.time()
    sign_audit()
    X = load()
    wk, plc, hol = classify(X)
    ev, excl = [], {}
    for p, d, back in wk:
        r = reopen_trade(X, p, d, back)
        if "excluded" in r:
            excl[r["excluded"]] = excl.get(r["excluded"], 0) + 1
            continue
        r["s_canary"] = (reopen_trade(X, p, d, back, canary=True) or {}).get("s", np.nan)
        ev.append(r)
    E = pd.DataFrame(ev)
    need(len(E) + sum(excl.values()) == len(wk), "right quantity: the events used plus excluded differ from the weekends read")
    need(bool((E["s"] != E["s_canary"]).any()), "lag: the 18:05-bar canary changed no sign")
    need(bool((E["entry_late_min"] >= 0).all()), "lag: an entry before 18:06")
    pl = [r for r in (reopen_trade(X, p, d, b) for p, d, b in plc) if "excluded" not in r]
    P = pd.DataFrame(pl)
    need(not set(P["day"]) & set(E["day"]), "right quantity: a placebo is a weekend event")
    g = (E["s"] * E["move930"]).to_numpy(float)
    gp = (P["s"] * P["move930"]).to_numpy(float)
    per_year = len(E) / 6.0
    s_arr, mv = E["s"].to_numpy(float), E["move930"].to_numpy(float)
    nul = np.array([float(np.mean(np.roll(s_arr, k) * mv)) for k in range(1, len(E))])
    b_fill = int((E["fill"] & ~E["mirror"]).sum())
    c_mirror = int((~E["fill"] & E["mirror"]).sum())
    pb, pc = int((P["fill"] & ~P["mirror"]).sum()), int((~P["fill"] & P["mirror"]).sum())
    absG = E["G"].abs().to_numpy(float)
    terc = pd.qcut(absG, 3, labels=["small", "mid", "large"])
    mbt = (E["day"] >= MBT_LIST).to_numpy()
    res: dict[str, Any] = {
        "spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "cost": COST, "two_c": 2 * COST,
        "weekends_read": len(wk), "events_scored": int(len(E)), "excluded": excl, "placebo_reopens": int(len(P)),
        "holiday_reopens": len(hol),
        "first_bar_late_min_median": float(E["first_bar_late_min"].median()),
        "first_bar_at_1800_share": float((E["first_bar_late_min"] == 0).mean()),
        "entry_late_min_median": float(E["entry_late_min"].median()),
        "O1_mean_abs_move_weekend": float(np.abs(mv).mean()), "O1_mean_abs_move_placebo": float(P["move930"].abs().mean()),
        "O1_welch_abs": welch(np.abs(mv), P["move930"].abs().to_numpy(float)),
        "O2_mean_abs_gap_usd": float(absG.mean()), "O2_mean_abs_gap_usd_placebo": float(P["G"].abs().mean()),
        "O2_gap_over_friday_range_median": float(E["G_range"].median()),
        "O2_gap_over_prev_range_median_placebo": float(P["G_range"].median()),
        "P": book(g, E["day"].tolist(), COST, per_year),
        "P_net_at_1p5x": float((g - 1.5 * COST).mean()), "P_net_at_2x": float((g - 2 * COST).mean()),
        "N1_rotation": {"offsets": int(len(nul)), "p05": float(np.percentile(nul, 5)), "p50": float(np.median(nul)),
                        "p95": float(np.percentile(nul, 95)), "p_up": float((nul >= g.mean()).mean())},
        "N2_placebo": {"n": int(len(gp)), "mean_gross": float(gp.mean()), "t": tstat(gp), "welch_t": welch(g, gp)},
        "touch": {"fill_rate": float(E["fill"].mean()), "mirror_rate": float(E["mirror"].mean()),
                  "fill_only": b_fill, "mirror_only": c_mirror, "sign_test_p": sign_test(b_fill, c_mirror),
                  "placebo_fill_rate": float(P["fill"].mean()), "placebo_mirror_rate": float(P["mirror"].mean()),
                  "placebo_fill_only": pb, "placebo_mirror_only": pc,
                  "difference": float(E["fill"].mean() - E["mirror"].mean()),
                  "placebo_difference": float(P["fill"].mean() - P["mirror"].mean())},
        "exit_1600": {"mean_gross": float((E["s"] * E["move1600"]).mean()), "t": tstat((E["s"] * E["move1600"]).to_numpy(float))},
        "target_trade": {"mean_gross": float(E["target"].mean()), "t": tstat(E["target"].to_numpy(float)),
                         "win_rate": float((E["target"] > 0).mean()), "median": float(E["target"].median())},
        "day_session": {"n": int(E["day_session"].notna().sum()), "mean_gross": float(E["day_session"].mean()),
                        "t": tstat(E["day_session"].to_numpy(float))},
        "gap_terciles": {str(k): {"n": int((terc == k).sum()), "mean_gross": float(g[np.asarray(terc == k)].mean()),
                                  "fill_rate": float(E["fill"][np.asarray(terc == k)].mean()),
                                  "mirror_rate": float(E["mirror"][np.asarray(terc == k)].mean())}
                         for k in ["small", "mid", "large"]},
        "eras": {"pre_mbt": {"n": int((~mbt).sum()), "mean_gross": float(g[~mbt].mean()), "t": tstat(g[~mbt])},
                 "mbt": {"n": int(mbt.sum()), "mean_gross": float(g[mbt].mean()), "t": tstat(g[mbt])}},
    }
    # holiday reopens, reported only
    hr = [r for r in (reopen_trade(X, p, d, 1) for p, d in hol) if r and "excluded" not in r]   # opens 18:00 the day before
    res["holiday_reopens_scored"] = {"n": len(hr), "mean_gross": float(np.mean([r["s"] * r["move930"] for r in hr])) if hr else None}
    # the calm split (D754's walk-forward gate on the Monday trade date), reported
    import stage0_d754_calm_bull as S754
    pct = S754.wf_pct(S754.rv20(S754.daily_close("NQ")))
    cp = pct.reindex(E["day"]).to_numpy(float)
    calm, other = np.isfinite(cp) & (cp < 1 / 3), np.isfinite(cp) & (cp >= 1 / 3)
    res["calm_split"] = {"calm": {"n": int(calm.sum()), "mean_gross": float(g[calm].mean()) if calm.any() else None,
                                  "mean_abs": float(np.abs(mv[calm]).mean()) if calm.any() else None},
                         "other": {"n": int(other.sum()), "mean_gross": float(g[other].mean()) if other.any() else None,
                                   "mean_abs": float(np.abs(mv[other]).mean()) if other.any() else None},
                         "ungated": int((~np.isfinite(cp)).sum())}
    if lines is not None and lines.exists():
        ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
        ol.index = ol.index.astype(str)
        alld = sorted(set(ol.index) | {d for d in E["day"] if ol.index.min() <= d <= ol.index.max()})
        tr = pd.Series(g - COST, index=E["day"].tolist())
        res["component_corr"] = {c: float(np.corrcoef(tr.reindex(alld, fill_value=0.0), ol[c].reindex(alld).fillna(0.0))[0, 1]) for c in ol.columns}
        res["component_corr_span"] = [ol.index.min(), ol.index.max(), int(tr.index.isin(alld).sum())]
    srt = E.assign(g=g).sort_values("g")
    res["largest_trades"] = {"losers": srt.head(3)[["day", "G", "g"]].round(2).to_dict("records"),
                             "winners": srt.tail(3)[["day", "G", "g"]].round(2).to_dict("records")}
    e = res["P"]
    no_room = res["O1_mean_abs_move_weekend"] < 2 * COST
    tch = res["touch"]
    fill = (e["mean_gross"] > 0 and e["t_gross"] >= 2 and e["mean_gross"] > res["N1_rotation"]["p95"]
            and res["N2_placebo"]["welch_t"] >= 1.64 and b_fill > c_mirror and tch["sign_test_p"] < 0.05)
    cont = (e["mean_gross"] < 0 and e["t_gross"] <= -2 and e["mean_gross"] < res["N1_rotation"]["p05"]
            and res["N2_placebo"]["welch_t"] <= -1.64 and c_mirror > b_fill and tch["sign_test_p"] < 0.05)
    if fill or cont:
        side = 1.0 if fill else -1.0
        net_side = side * g - COST
        yrs = pd.Series(net_side, index=[d[:4] for d in E["day"]]).groupby(level=0).sum()
        go = (not no_room and net_side.mean() > 0 and int((yrs > 0).sum()) >= 4 and yrs.sum() > 0
              and yrs.max() / yrs.sum() < 0.5 and float((side * g[mbt]).mean()) > 0)
    else:
        go = False
    res["readings"] = {"NO_ROOM": bool(no_room), "NOT_SPECIAL": bool(res["O1_welch_abs"] < 2), "FILL": bool(fill),
                       "CONTINUATION": bool(cont), "GO": bool(go),
                       "reading": "NO ROOM" if no_room else ("FILL" if fill else ("CONTINUATION" if cont else "NOTHING"))}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("readings", "events_scored", "excluded", "O1_mean_abs_move_weekend",
                                          "O1_mean_abs_move_placebo", "touch", "N1_rotation", "N2_placebo", "eras")},
                     indent=1, default=float))
    print(json.dumps({k: res["P"][k] for k in ("trades", "mean_gross", "t_gross", "mean_net", "positive_years")}, indent=1))
    return 0


# ================================================================================ self-test
def _synthetic(up: float) -> dict[str, Any]:
    """Friday session at 100, a Sunday reopen at 100 - 10*up (a down-gap for up=+1), then a rise to 100 - 5*up."""
    fri = [wall("2020-01-03", "16:58"), wall("2020-01-03", "16:59")]
    sun = [wall("2020-01-06", "18:00", 1) + i for i in range(10)] + [wall("2020-01-06", "09:00")]
    m = np.array(fri + sun, np.int64)
    c = np.array([100.0, 100.0] + [100 - 10 * up] * 10 + [100 - 5 * up])
    k = np.array(["BTCF0"] * len(m))
    return {"m": m, "o": c.copy(), "h": c.copy(), "l": c.copy(), "c": c, "k": k, "days": ["2020-01-03", "2020-01-06"],
            "sess": {"2020-01-03": (0, 2), "2020-01-06": (2, len(m))}}


def sign_audit(up: float = 1.0) -> None:
    r = reopen_trade(_synthetic(up), "2020-01-03", "2020-01-06", 1)
    need(r is not None and "excluded" not in r, f"sign: the synthetic weekend was excluded ({r})")
    need(r["s"] > 0, "sign: a down-gap did not give a long fade")
    need(r["s"] * r["move930"] > 0, f"sign: a rise after a down-gap did not pay the fade ({r})")
    need(r["fill"] is False and r["mirror"] is False, "touch: a half-fill touched a level")


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D758Error as e:
        fails.append(str(e))
    try:
        sign_audit(up=-1.0)
        fails.append("sign: the audit did not raise on a mirrored (broken) book")
    except D758Error:
        pass
    # touch: a full fill touches F and not the mirror
    X = _synthetic(1.0)
    X["c"][-1] = X["h"][-1] = X["o"][-1] = X["l"][-1] = 100.0
    r = reopen_trade(X, "2020-01-03", "2020-01-06", 1)
    if not (r["fill"] and not r["mirror"]):
        fails.append(f"touch: a full fill was not read as a fill ({r})")
    ts = pd.Series(pd.date_range("2018-01-01", "2023-12-31 23:00", freq="37min", tz="UTC").strftime("%Y-%m-%dT%H:%M"))
    if not (et_minutes(ts) == et_minutes_by_rule(ts)).all():
        fails.append("clock: zoneinfo and the statutory rule disagree")
    if sign_test(10, 0) > 0.002 or abs(sign_test(5, 5) - 1.0) > 1e-12:
        fails.append("sign test: a known answer is wrong")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money (a down-gap fades long and a rise pays; it raises on a mirrored book); "
          "the touch test reads a half-fill as neither and a full fill as a fill; the UTC -> ET clock equals the "
          "statutory rule on 2018-2023; the exact sign test's known answers")
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
