"""D624: can one-second bars stand in for aggressor-signed flow in the settlement ledger's Stage A?

The spec is `docs/decisions/D624-PRE-REG-validating-estimated-signed-flow-for-stage-A.md`, committed alone in
`6e1bfa4` before this file existed. This runner implements it and nothing else. Section numbers below are the
record's.

    python scripts/validate_flow_estimate.py --siblings    # §4: K1, the selection, the agreement check, C1 and C2 on HO/RB
    python scripts/validate_flow_estimate.py --gate        # §5: K1 and the NG/CL gate, once, after the top-up
    python scripts/validate_flow_estimate.py --check       # rebuild every phase on disk; compare byte for byte

It uses the SYSTEM interpreter (databento). It reads only Databento files under data/raw/databento/, named by the
job records `data/ledger_sibling_pull_jobs.json` (siblings) and `data/ledger_free_pull_jobs.json` plus
`data/ledger_topup_pull_jobs.json` (the gate). No NG or CL row dated 2025-03-01 → 2026-09-18 is read; the guard
raises on one.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
OUT = REPO / "data" / "ledger_flow_estimate_validation.json"
SIB_JOBS = REPO / "data" / "ledger_sibling_pull_jobs.json"
FREE_JOBS = REPO / "data" / "ledger_free_pull_jobs.json"
TOPUP_JOBS = REPO / "data" / "ledger_topup_pull_jobs.json"
ET = "America/New_York"
VAULT = ("2025-03-01", "2026-09-18")
FIRST_HALF = ("2025-09-25", "2026-02-27")
SECOND_HALF = ("2026-03-02", "2026-09-18")
W0, W1 = "14:28:00", "14:30:00"
STATE_FROM = "09:00:00"
SIGMA_FROM = "13:58:00"
PRE_FROM, TAUS = "13:30:00", ("13:50:00", "14:00:00", "14:10:00")
MIN_TRUE_TRADES = 20
BAR, NEAR_MISS, MIN_SESSIONS = 0.8, 0.70, 15
TIE = 0.005
SEED = 624
ORDER = ("E1", "E2", "E3")
LETTER = "FGHJKMNQUVXZ"
RE_OUT = re.compile(r"^(HO|RB|CL|NG)([FGHJKMNQUVXZ])(\d{1,2})$")
RE_TAS = re.compile(r"^(CLT|NGT)([FGHJKMNQUVXZ])(\d{1,2})$")
#: Changes made after the first run.
DEVIATIONS: list[str] = [
    "K1 raised on the first sibling run: bar volume matched trade volume on 98.32% of 252,270 window seconds, with "
    "window totals 1,271,123 against 1,271,121. The diagnosis, on one day and without computing any correlation: "
    "Databento builds ohlcv-1s bars on ts_recv (the bars' ts_event column is the bucket start in RECEIVE time), while "
    "trades had been bucketed on the exchange's ts_event. Those clocks differ by milliseconds, so trades near a "
    "second's edge fell into the neighbouring bar. On 2025-10-01 the match is 99.26% on ts_event and 100% on ts_recv. "
    "Trades, and so the truth, are now bucketed and windowed on ts_recv, the same clock as the bars. The K1 "
    "threshold (99.9%) is unchanged. D624 did not name the timestamp. A crash in `load` before any statistic "
    "(`.dt` missing on a date conversion) is also fixed.",
    "The second sibling run's numbers are VOID. `truth` subtracted sell size from buy size on Databento's UNSIGNED "
    "`size` (uint32), so every session with net selling wrapped to about +4.3e9, and numpy warned of the overflow. "
    "The correlations it printed (first-half mean r: E1 -0.20, E2 -0.22, E3 -0.19; second-half E3 r: HO 0.04, RB 0.13) "
    "were computed against a corrupted truth, and they are recorded here only so the void run is not hidden. The "
    "sums are now cast to int64 before subtracting, and the selftest has a net-selling case on uint32 sizes that "
    "must return -1. The selection and agreement are recomputed from scratch on the corrected truth. The void "
    "numbers are NOT uninformative. The wrapped truth is about 4.3e9 exactly on net-selling sessions, so each "
    "estimator's correlation with it measures, roughly, how often it had the day's sign right, and that ranking "
    "(E2 best) was seen before the corrected run. The selection rule is mechanical (the highest first-half mean r, "
    "within 0.005 the simpler wins) and was fixed in D624 before either run, so that exposure cannot move the "
    "choice. It is disclosed here all the same.",
]


class D624Error(RuntimeError):
    pass


# ------------------------------------------------------------------ loading
def _files(job_record: Path, label: str) -> list[Path]:
    rec = json.loads(job_record.read_text(encoding="utf-8"))
    job = next(j for j in rec["jobs"] if j["label"] == label)
    folder = RAW / job["job"]["id"]
    files = sorted(folder.glob("*.dbn.zst"))
    if not files:
        raise D624Error(f"no files for {label} in {folder}")
    return files


def load(files: list[Path], pattern: re.Pattern[str], t_from: str, t_to: str) -> pd.DataFrame:
    """Rows whose symbol matches `pattern` and whose ET clock time is in [t_from, t_to), with ET date and time."""
    import databento as db
    parts = []
    for f in files:
        store = db.DBNStore.from_file(f)
        for chunk in store.to_df(map_symbols=True, count=2_000_000):
            chunk = chunk[chunk["symbol"].astype(str).str.match(pattern)]
            if chunk.empty:
                continue
            # Databento builds ohlcv-1s on ts_recv (the bars' index), so trades are bucketed on ts_recv too (DEVIATIONS)
            ts = chunk["ts_recv"] if "ts_recv" in chunk.columns else chunk.index.to_series()
            et = pd.DatetimeIndex(ts).tz_convert(ET)
            clock = et.strftime("%H:%M:%S")
            keep = (clock >= t_from) & (clock < t_to)
            if not keep.any():
                continue
            c = chunk.loc[keep].copy()
            c["et"] = et[keep]
            c["day"] = c["et"].dt.strftime("%Y-%m-%d")
            c["clock"] = clock[keep]
            c["sec"] = c["et"].dt.floor("s")
            parts.append(c)
    if not parts:
        raise D624Error(f"no rows for {pattern.pattern} in {[f.name for f in files]}")
    return pd.concat(parts).reset_index(drop=True)


def vault_guard(df: pd.DataFrame, roots: tuple[str, ...]) -> None:
    hit = df[df["symbol"].str[:2].isin(roots) & (df["day"] >= VAULT[0]) & (df["day"] <= VAULT[1])]
    if len(hit):
        raise D624Error(f"{len(hit)} {roots} rows inside the vault {VAULT} are in memory")


# ------------------------------------------------------------------ the estimators (§3)
def _phi(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def estimate(bars: pd.DataFrame, which: str) -> tuple[pd.Series, bool]:
    """Signed volume per bar for ONE contract-day's bars in time order, and whether E3 fell back to E1."""
    c = bars["close"].to_numpy(float)
    o = bars["open"].to_numpy(float)
    v = bars["volume"].to_numpy(float)
    dc = np.diff(c, prepend=np.nan)
    # E1: the sign of the last non-zero close change, carried; 0 before the first change
    tick = pd.Series(np.sign(dc)).replace(0.0, np.nan).ffill().fillna(0.0).to_numpy()
    fallback = False
    if which == "E1":
        s = tick
    elif which == "E2":
        s = np.where(c > o, 1.0, np.where(c < o, -1.0, tick))
    elif which == "E3":
        clock = bars["clock"].to_numpy()
        d_ref = dc[(clock >= SIGMA_FROM) & (clock < W0)]
        d_ref = d_ref[~np.isnan(d_ref)]
        sigma = float(np.std(d_ref)) if len(d_ref) >= 30 else 0.0
        if sigma == 0.0:
            s, fallback = tick, True
        else:
            s = 2.0 * _phi(np.nan_to_num(dc / sigma, nan=0.0)) - 1.0
    else:
        raise D624Error(which)
    return pd.Series(s * v, index=bars.index), fallback


def truth(trades: pd.DataFrame) -> float:
    """Buy-aggressor minus sell-aggressor size. Databento's `size` is UNSIGNED, so the sums are cast first."""
    side = trades["side"].astype(str)
    size = trades["size"].astype("int64")
    return float(int(size[side == "B"].sum()) - int(size[side == "A"].sum()))


# ------------------------------------------------------------------ K1, the known answer (§6)
def k1(bars: pd.DataFrame, trades: pd.DataFrame) -> dict[str, Any]:
    b = bars[(bars["clock"] >= W0) & (bars["clock"] < W1)].groupby(["symbol", "sec"])["volume"].sum()
    t = trades[(trades["clock"] >= W0) & (trades["clock"] < W1)].groupby(["symbol", "sec"])["size"].sum()
    j = pd.concat([b.rename("bar"), t.rename("trade")], axis=1).fillna(0)
    ok = float((j["bar"] == j["trade"]).mean())
    out = {"window_seconds": int(len(j)), "share_equal": round(ok, 6),
           "bar_volume": int(j["bar"].sum()), "trade_volume": int(j["trade"].sum())}
    if ok < 0.999:
        raise D624Error(f"K1 failed: bar volume equals trade volume on only {ok:.4%} of window seconds {out}")
    return out


# ------------------------------------------------------------------ per-session series
def _ym(sym: str, day: str) -> tuple[int, int]:
    m = RE_OUT.match(sym) or RE_TAS.match(sym)
    assert m is not None, sym
    mon, y = LETTER.index(m.group(2)) + 1, m.group(3)
    if len(y) == 2:
        return (2000 + int(y), mon)
    sy, sm = int(day[:4]), int(day[5:7])
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and cand * 12 + mon >= sy * 12 + sm - 1:
            return (cand, mon)
    raise D624Error(f"cannot date {sym} on {day}")


def traded_contract_rule(root: str, day: str) -> tuple[int, int]:
    """§2 for NG and CL: the index month with the largest weight at the start of the window."""
    y, m = int(day[:4]), int(day[5:7])
    d = dt.date.fromisoformat(day)
    k = sum(1 for i in range(1, d.day + 1) if dt.date(y, m, i).weekday() < 5)  # no NYMEX holiday in the gate span
    add = lambda yy, mm: (yy + (mm - 1) // 12, (mm - 1) % 12 + 1)  # noqa: E731
    if root == "NG":
        des = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7, 7: 9, 8: 9, 9: 11, 10: 11, 11: 13, 12: 13}
        lead = add(y, des[m])
        nm = add(y, m + 1)
        nxt = add(nm[0], des[nm[1]])
        w_next = min(max((k - 5) / 5.0, 0.0), 1.0)
        return nxt if w_next > 0.5 else lead
    rolled = 0.0 if k <= 2 else (0.5 if k == 3 else 1.0)  # after the BD2 and BD3 closes
    w: dict[tuple[int, int], float] = {}
    w[add(y, m + 2)] = w.get(add(y, m + 2), 0.0) + (1 - rolled) / 3
    w[add(y, m + 3)] = w.get(add(y, m + 3), 0.0) + rolled / 3
    june = (y, 6) if m < 3 or (m == 3 and rolled < 1) else (y + 1, 6)
    dec = (y, 12) if m < 9 or (m == 9 and rolled < 1) else (y + 1, 12)
    for c in (june, dec):
        w[c] = w.get(c, 0.0) + 1 / 3
    top = max(w.values())
    best = [c for c, x in w.items() if abs(x - top) < 1e-12]
    monthly = add(y, m + 2) if rolled < 0.5 else add(y, m + 3)
    return monthly if (len(best) > 1 and monthly in best) else min(best)


def sessions(bars: pd.DataFrame, trades: pd.DataFrame, root: str, contract_rule: str) -> pd.DataFrame:
    """One row per usable session: the contract, true and estimated window flow, and the reported extras."""
    rows = []
    bars_r = bars[bars["symbol"].str[:2] == root]
    trades_r = trades[trades["symbol"].str[:2] == root]
    for day, bd in bars_r.groupby("day"):
        td = trades_r[trades_r["day"] == day]
        win_b = bd[(bd["clock"] >= W0) & (bd["clock"] < W1)]
        if win_b.empty:
            continue
        if contract_rule == "most_active":
            sym = str(win_b.groupby("symbol")["volume"].sum().idxmax())
        else:
            want = traded_contract_rule(root, str(day))
            cand = [s for s in win_b["symbol"].unique() if _ym(str(s), str(day)) == want]
            if not cand:
                continue
            sym = str(cand[0])
        tw = td[(td["symbol"] == sym) & (td["clock"] >= W0) & (td["clock"] < W1)]
        if len(tw) < MIN_TRUE_TRADES:
            rows.append({"day": day, "symbol": sym, "excluded": f"{len(tw)} true trades in the window"})
            continue
        b = bd[bd["symbol"] == sym].sort_values("sec")
        row: dict[str, Any] = {"day": day, "symbol": sym, "true_window": truth(tw),
                               "n_share": round(float(tw.loc[tw["side"].astype(str) == "N", "size"].sum() / tw["size"].sum()), 4)}
        inwin = (b["clock"] >= W0) & (b["clock"] < W1)
        for e in ORDER:
            sv, fb = estimate(b, e)
            if e == "E3":
                row["E3_fallback"] = fb
            row[f"{e}_window"] = float(sv[inwin].sum())
            for tau in TAUS:
                pre = (b["clock"] >= PRE_FROM) & (b["clock"] < tau)
                row[f"{e}_pre_{tau[:5]}"] = float(sv[pre].sum())
            # all outright months summed
            tot = 0.0
            for s2, b2 in bd.groupby("symbol"):
                b2 = b2.sort_values("sec")
                sv2, _fb = estimate(b2, e)
                tot += float(sv2[(b2["clock"] >= W0) & (b2["clock"] < W1)].sum())
            row[f"{e}_all_outrights"] = tot
            # volume-weighted classification accuracy in the window
            sec_sign = pd.Series(np.sign(sv[inwin].to_numpy()), index=b.loc[inwin, "sec"].to_numpy())
            tt = tw[tw["side"].astype(str).isin(["B", "A"])]
            tsign = np.where(tt["side"].astype(str) == "B", 1.0, -1.0)
            match = tsign == sec_sign.reindex(tt["sec"].to_numpy()).fillna(0).to_numpy()
            row[f"{e}_accuracy"] = round(float((tt["size"].to_numpy() * match).sum() / tt["size"].sum()), 4)
        for tau in TAUS:
            pre_t = td[(td["symbol"] == sym) & (td["clock"] >= PRE_FROM) & (td["clock"] < tau)]
            row[f"true_pre_{tau[:5]}"] = truth(pre_t)
        row["true_all_outrights"] = truth(td[(td["clock"] >= W0) & (td["clock"] < W1)])
        rows.append(row)
    return pd.DataFrame(rows)


def corr(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    n = int(len(x))
    if n < 4:
        return {"n": n, "r": None}
    r = float(np.corrcoef(x, y)[0, 1])
    z, h = math.atanh(max(min(r, 0.999999), -0.999999)), 1.645 / math.sqrt(n - 3)
    rs = float(pd.Series(x).rank().corr(pd.Series(y).rank()))
    return {"n": n, "r": round(r, 4), "ci90": [round(math.tanh(z - h), 4), round(math.tanh(z + h), 4)],
            "spearman": round(rs, 4)}


def _usable(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["excluded"].isna()] if "excluded" in df.columns else df


def describe(df: pd.DataFrame, e: str) -> dict[str, Any]:
    u = _usable(df)
    out = {"window": corr(u[f"{e}_window"], u["true_window"]),
           "all_outrights": corr(u[f"{e}_all_outrights"], u["true_all_outrights"]),
           "pre_window": {tau[:5]: corr(u[f"{e}_pre_{tau[:5]}"], u[f"true_pre_{tau[:5]}"]) for tau in TAUS},
           "accuracy_mean": round(float(u[f"{e}_accuracy"].mean()), 4) if len(u) else None}
    if len(u) >= 4:
        slope, icpt = np.polyfit(u[f"{e}_window"], u["true_window"], 1)
        resid = u["true_window"] - (slope * u[f"{e}_window"] + icpt)
        out["band_truth_on_estimate"] = {"slope": round(float(slope), 4), "intercept": round(float(icpt), 2),
                                         "residual_sd": round(float(resid.std(ddof=2)), 2)}
    return out


# ------------------------------------------------------------------ phases
def siblings() -> dict[str, Any]:
    tr = load(_files(SIB_JOBS, "siblings-trades"), RE_OUT, PRE_FROM, W1)
    ba = load(_files(SIB_JOBS, "siblings-ohlcv1s"), RE_OUT, STATE_FROM, W1)
    if set(tr["symbol"].str[:2]) - {"HO", "RB"} or set(ba["symbol"].str[:2]) - {"HO", "RB"}:
        raise D624Error("a non-sibling root is in the sibling files")
    out: dict[str, Any] = {"k1": k1(ba, tr), "roots": {}}
    per: dict[str, pd.DataFrame] = {}
    for root in ("HO", "RB"):
        per[root] = sessions(ba, tr, root, "most_active")
        per[root]["excluded"] = per[root].get("excluded")
    halves = {h: {root: per[root][(per[root]["day"] >= a) & (per[root]["day"] <= b)] for root in per}
              for h, (a, b) in (("first", FIRST_HALF), ("second", SECOND_HALF))}
    sel = {e: {root: corr(_usable(halves["first"][root])[f"{e}_window"], _usable(halves["first"][root])["true_window"])
               for root in per} for e in ORDER}
    mean_r = {e: float(np.mean([sel[e][r]["r"] for r in per])) for e in ORDER}
    top = max(mean_r.values())
    chosen = next(e for e in ORDER if mean_r[e] >= top - TIE)
    agree = {root: describe(halves["second"][root], chosen) for root in per}
    agrees = all(agree[r]["window"]["r"] is not None and agree[r]["window"]["r"] >= BAR for r in per)
    # controls on the second half, chosen estimator
    rng = np.random.default_rng(SEED)
    controls: dict[str, Any] = {}
    for root in per:
        u = _usable(halves["second"][root]).reset_index(drop=True)
        shifted = corr(u[f"{chosen}_window"].iloc[:-1].reset_index(drop=True), u["true_window"].iloc[1:].reset_index(drop=True))
        rnd = u[f"{chosen}_window"].abs() * rng.choice([-1.0, 1.0], size=len(u))
        rand = corr(rnd, u["true_window"])
        if shifted["r"] is None or abs(shifted["r"]) >= 0.5:
            raise D624Error(f"C1 failed on {root}: day-shifted r = {shifted['r']}")
        if rand["r"] is None or abs(rand["r"]) >= 0.3:
            raise D624Error(f"C2 failed on {root}: random-sign r = {rand['r']}")
        controls[root] = {"c1_day_shift": shifted, "c2_random_sign": rand}
    out.update({
        "selection_first_half": {"per_estimator": sel, "mean_r": {e: round(v, 4) for e, v in mean_r.items()},
                                 "chosen": chosen},
        "agreement_second_half": agree, "siblings_agree": bool(agrees), "controls": controls,
        "sessions": {root: {"usable": int(len(_usable(per[root]))),
                            "excluded": per[root][per[root]["excluded"].notna()][["day", "excluded"]].to_dict("records")}
                     for root in per},
        "all_estimators_second_half_for_the_record": {e: {r: describe(halves["second"][r], e)["window"] for r in per}
                                                      for e in ORDER},
    })
    return out


def gate() -> dict[str, Any]:
    if not TOPUP_JOBS.exists():
        raise D624Error(f"{TOPUP_JOBS.name} is absent: the gate is read once, after the top-up (§5)")
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    sib = doc.get("siblings")
    if not sib:
        raise D624Error("the sibling phase must run first (§4)")
    chosen = sib["selection_first_half"]["chosen"]
    tr = pd.concat([load(_files(FREE_JOBS, "trades-post-vault"), RE_OUT, PRE_FROM, W1),
                    load(_files(TOPUP_JOBS, "topup-trades"), RE_OUT, PRE_FROM, W1)])
    ba = load(_files(TOPUP_JOBS, "topup-ohlcv1s"), RE_OUT, STATE_FROM, W1)
    vault_guard(tr, ("CL", "NG"))
    vault_guard(ba, ("CL", "NG"))
    out: dict[str, Any] = {"estimator": chosen, "k1": k1(ba, tr), "roots": {}}
    for root in ("CL", "NG"):
        df = sessions(ba, tr, root, "rule")
        d = describe(df, chosen)
        r, n = d["window"]["r"], d["window"]["n"]
        if n < MIN_SESSIONS or r is None:
            verdict = "UNRESOLVED (fewer than 15 usable sessions)"
        elif not sib["siblings_agree"]:
            verdict = "NOT ON THE ESTIMATE (siblings did not agree)"
        elif r >= BAR:
            verdict = "PASS"
        elif r >= NEAR_MISS:
            verdict = "UNRESOLVED (near miss)"
        else:
            verdict = "FAIL"
        out["roots"][root] = {"verdict": verdict, **d, "sessions": df.to_dict("records")}
    out["tas_reported_not_gated"] = tas_report(
        _files(FREE_JOBS, "trades-post-vault") + _files(TOPUP_JOBS, "topup-trades"),
        _files(TOPUP_JOBS, "topup-ohlcv1s"), chosen)
    return out


def tas_report(files_tr: list[Path], files_bar: list[Path], chosen: str) -> dict[str, Any]:
    """§7: daily signed TAS volume, session open (18:00 ET the evening before) to 14:30 ET; all TAS months summed."""
    def span(files: list[Path]) -> pd.DataFrame:
        eve = load(files, RE_TAS, "18:00:00", "24:00:00")
        eve["day"] = (pd.to_datetime(eve["day"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        return pd.concat([eve, load(files, RE_TAS, "00:00:00", W1)])
    tr, ba = span(files_tr), span(files_bar)
    vault_guard(tr.assign(symbol=tr["symbol"].str[:2]), ("CL", "NG"))
    out: dict[str, Any] = {}
    for root in ("CLT", "NGT"):
        rows = []
        for day, bd in ba[ba["symbol"].str[:3] == root].groupby("day"):
            td = tr[(tr["symbol"].str[:3] == root) & (tr["day"] == day)]
            if len(td) < MIN_TRUE_TRADES:
                continue
            est = 0.0
            for _s, b2 in bd.groupby("symbol"):
                sv, _fb = estimate(b2.sort_values("sec"), chosen)
                est += float(sv.sum())
            rows.append({"day": day, "true": truth(td), "est": est})
        df = pd.DataFrame(rows)
        out[root] = corr(df["est"], df["true"]) if len(df) else {"n": 0, "r": None}
    return out


def selftest() -> None:
    """K1 must raise on misaligned bars; the estimators must give known answers on a synthetic path."""
    secs = pd.date_range("2026-01-05 14:28:00", periods=4, freq="s", tz=ET)
    bars = pd.DataFrame({"symbol": "HOF6", "sec": secs, "clock": secs.strftime("%H:%M:%S"),
                         "open": [2.0, 2.0, 2.02, 2.01], "close": [2.0, 2.01, 2.02, 2.01], "volume": [5, 3, 2, 4]})
    trades = pd.DataFrame({"symbol": "HOF6", "sec": secs, "clock": secs.strftime("%H:%M:%S"),
                           "size": [5, 3, 2, 4], "side": ["N", "B", "B", "A"]})
    k1(bars, trades)
    try:
        k1(bars.assign(sec=bars["sec"] + pd.Timedelta(seconds=1)), trades)
    except D624Error:
        pass
    else:
        raise D624Error("selftest: K1 did not fire on bars shifted by one second")
    e1, _ = estimate(bars, "E1")
    if e1.tolist() != [0.0, 3.0, 2.0, -4.0]:
        raise D624Error(f"selftest: E1 gave {e1.tolist()}")
    e2, _ = estimate(bars, "E2")
    if e2.tolist() != [0.0, 3.0, 2.0, -4.0]:
        raise D624Error(f"selftest: E2 gave {e2.tolist()}")
    if truth(trades) != 1.0:
        raise D624Error("selftest: truth must drop N and net B minus A (3 + 2 - 4 = 1)")
    sold = trades.assign(side=["N", "A", "A", "B"], size=np.array([5, 3, 2, 4], dtype=np.uint32))
    if truth(sold) != -1.0:
        raise D624Error(f"selftest: truth on UNSIGNED sizes with net selling gave {truth(sold)}, not -1")
    if traded_contract_rule("CL", "2026-10-01") != (2026, 12) or traded_contract_rule("NG", "2026-09-22") != (2026, 11):
        raise D624Error("selftest: the traded-contract rule is wrong on its worked cases")
    print("[selftest] K1 fires on a one-second shift; E1/E2/truth give their known answers; contract rule holds")


def build(phase: str) -> dict[str, Any]:
    return siblings() if phase == "siblings" else gate()


def _dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--siblings", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    doc: dict[str, Any] = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "spec": "D624; docs/decisions/D624-PRE-REG-validating-estimated-signed-flow-for-stage-A.md (6e1bfa4)",
        "deviations": DEVIATIONS}
    if a.check:
        rebuilt = dict(doc)
        for ph in ("siblings", "gate"):
            if ph in doc:
                rebuilt[ph] = build(ph)
        if _dump(rebuilt) != OUT.read_text(encoding="utf-8"):
            raise D624Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    phase = "siblings" if a.siblings else "gate" if a.gate else None
    if phase is None:
        ap.print_help()
        return 2
    doc[phase] = build(phase)
    doc["deviations"] = DEVIATIONS
    OUT.write_text(_dump(doc), encoding="utf-8", newline="\n")
    p = doc[phase]
    if phase == "siblings":
        print("K1", p["k1"])
        print("selection (first half) mean r:", p["selection_first_half"]["mean_r"], "-> chosen", p["selection_first_half"]["chosen"])
        for r, d in p["agreement_second_half"].items():
            print(f"  {r} second half: window {d['window']}  accuracy {d['accuracy_mean']}")
        print("siblings agree:", p["siblings_agree"], "| controls:",
              {r: (c['c1_day_shift']['r'], c['c2_random_sign']['r']) for r, c in p["controls"].items()})
    else:
        for r, d in p["roots"].items():
            print(r, d["verdict"], d["window"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
