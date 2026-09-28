"""Phase 2 of the opening agent-state model: the pre-open agent pressures A1-A6 per (market, session), raw and
standardised (OPENING_AGENT_STATE_PREREG.md s.4; OA-A6, OA-A7 ruled 2026-09-28). A7 waits for the Sierra tick pull
and its check against the exchange flag (OA-A3).

    uv run python scripts/build_opening_agents.py [--data-root DIR]     # the venv (scipy); -> data/opening/agents.csv

Every value at session t uses information available by 09:29 ET on t (A6: 09:31), through
`backtest_framework.opening.agents` (deposit tests 4-11). Inputs:
- this checkout's bar fixture `fut_opening_globex_1m.csv.gz` (D644): A1, A5, A6's futures prints, the RTH summary;
- `--data-root` (the gitignored inputs; a worktree passes the main checkout's `data/`):
  - `fixtures/fut_settle_strip.csv.gz` + `fixtures/fut_index_sessions.csv.gz`: A2/A3's front settlement, ratio
    back-adjusted at D462's rolls (OA-A7.1);
  - `raw/alphavantage/1min/{SPY,QQQ}`: A6;
  - `fixtures/fut_es_options_eod.csv.gz` + `fixtures/cme_session_calendar.csv.gz`: A4 on ES (NQ has no options fixture
    yet, so its A4 is NaN and S-H waits for it);
- `data/calendar/events.csv` (D585): CPI and EMPSIT days for A5.
Nothing on or after 2025-03-01 is read (A10): every frame is cut by `filter_before` and checked by
`assert_none_at_or_after`. Output rows run 2015-09-01 -> 2025-02-28; the z-scores need 60 prior sessions (OA-A7.3).
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.opening import agents as A  # noqa: E402
from backtest_framework.opening.labels import atr_prior  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

_s = importlib.util.spec_from_file_location("opening_gate0", REPO / "scripts" / "opening_gate0.py")
assert _s is not None and _s.loader is not None
G0 = importlib.util.module_from_spec(_s)
sys.modules["opening_gate0"] = G0
_s.loader.exec_module(G0)

OUT = REPO / "data" / "opening" / "agents.csv"
RESERVED_FROM, FIRST = "2025-03-01", "2015-09-01"
ROOTS = ("ES", "NQ")
ETF = {"ES": "SPY", "NQ": "QQQ"}
MONEYNESS_MAX = 0.30  # D581
CHUNK = 2_000_000


def cut(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = filter_before(df, col, RESERVED_FROM)
    assert_none_at_or_after(df, col, RESERVED_FROM)
    return df


def settlement_series(root: str, data_root: Path) -> pd.Series:
    """The front contract's settlement per D462 session, ratio back-adjusted at every roll (OA-A7.1)."""
    ses = pd.read_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
    ses = cut(ses[ses["root"] == root][["day", "contract"]].sort_values("day"), "day")
    st = pd.read_csv(data_root / "fixtures" / "fut_settle_strip.csv.gz", encoding="utf-8", dtype={"ref": str},
                     usecols=["root", "contract", "ref", "settle"])
    st = cut(st[st["root"] == root], "ref")
    st = st[st["settle"] != 0]  # D526: an exact 0.0 is a missing-value sentinel
    px = st.set_index(["ref", "contract"])["settle"]
    front = ses["contract"].to_numpy()
    days = ses["day"].to_numpy()
    s = np.array([px.get((d, c), np.nan) for d, c in zip(days, front)], dtype=float)
    k = np.ones(len(s))
    for t in range(1, len(s)):
        if front[t] != front[t - 1]:
            old = px.get((days[t], front[t - 1]), np.nan)
            k[t] = s[t] / old if np.isfinite(old) and old > 0 else np.nan
    if np.isnan(k).any():
        raise SystemExit(f"{root}: a roll day without both contracts' settlements: {days[np.isnan(k)][:5]}")
    return pd.Series(A.ratio_adjust(s, k), index=days)


def etf_frame(sym: str, data_root: Path, months: list[str]) -> pd.DataFrame:
    recs = []
    for m in months:
        p = data_root / "raw" / "alphavantage" / "1min" / sym / f"{m}.json.gz"
        if not p.exists():  # the fetch starts 2015-10 (OA-A4); 2015-09 is warm-up only, and A6 is NaN there
            if m >= "2015-10":
                raise SystemExit(f"missing ETF slice {p}")
            continue
        payload = json.load(gzip.open(p, "rt", encoding="utf-8"))
        ser = next(v for k, v in payload.items() if k.lower().startswith("time series"))
        recs.extend((k[:10], k[11:16], float(v["2. high"]), float(v["3. low"]), float(v["4. close"]))
                    for k, v in ser.items())
    e = cut(pd.DataFrame(recs, columns=["day", "hhmm", "high", "low", "close"]), "day")
    rth = e[(e["hhmm"] >= "09:30") & (e["hhmm"] <= "15:59")].sort_values(["day", "hhmm"])
    g = rth.groupby("day")
    d = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last()})
    d["atr20"] = atr_prior(d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy())
    d["c0930"] = rth[rth["hhmm"] == "09:30"].set_index("day")["close"].reindex(d.index)
    d["c1559"] = rth[rth["hhmm"] == "15:59"].set_index("day")["close"].reindex(d.index)
    return d


def dealer_gamma_es(data_root: Path, sessions: list[str]) -> pd.Series:
    """G per ES session (s.4 A4 under OA-A7.4): OI as of the prior close, vol implied from the prior settlement,
    gamma at the underlying's prior settlement, over options expiring after 09:30 on the session."""
    cols = ["session", "right", "strike", "expiry_date", "expiry_hhmm", "underlying", "oi", "settle"]
    want = set(sessions)
    parts = []
    for ch in pd.read_csv(data_root / "fixtures" / "fut_es_options_eod.csv.gz", encoding="utf-8", usecols=cols,
                          chunksize=CHUNK, dtype={"session": str, "expiry_date": str, "expiry_hhmm": str,
                                                  "underlying": str, "right": str}):
        ch = cut(ch, "session")
        parts.append(ch[ch["session"].isin(want) & (ch["oi"] > 0) & ch["settle"].notna() & (ch["settle"] > 0)])
    o = pd.concat(parts, ignore_index=True)
    cal = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str},
                      usecols=["root", "day", "is_trading"])
    tdays = np.array(sorted(cal.loc[(cal["root"] == "ES") & cal["is_trading"].astype(bool), "day"]))
    pos = {d: i for i, d in enumerate(tdays)}
    last = tdays[-1]

    def n_sessions(frm: np.ndarray, to: np.ndarray) -> np.ndarray:
        i0 = np.searchsorted(tdays, frm)
        i1 = np.searchsorted(tdays, to)
        beyond = to > last
        extra = np.where(beyond, np.busday_count(np.full(len(to), last, dtype="datetime64[D]"),
                                                 np.where(beyond, to, last).astype("datetime64[D]")), 0)
        return np.where(beyond, len(tdays) - 1 + extra, i1) - i0

    prev = {d: tdays[pos[d] - 1] for d in sessions if d in pos and pos[d] > 0}
    st = pd.read_csv(data_root / "fixtures" / "fut_settle_strip.csv.gz", encoding="utf-8", dtype={"ref": str},
                     usecols=["root", "contract", "ref", "settle"])
    st = cut(st[(st["root"] == "ES") & (st["settle"] != 0)], "ref")
    o["prev"] = o["session"].map(prev)
    o = o.merge(st.rename(columns={"ref": "prev", "contract": "underlying", "settle": "F"})[["prev", "underlying", "F"]],
                on=["prev", "underlying"], how="inner")
    n_ahead = n_sessions(o["session"].to_numpy(), o["expiry_date"].to_numpy())
    alive = (n_ahead > 0) | ((n_ahead == 0) & (o["expiry_hhmm"].to_numpy() > "09:30"))
    K, F = o["strike"].to_numpy(float), o["F"].to_numpy(float)
    keep = alive & (np.abs(K / F - 1) < MONEYNESS_MAX)
    o = o[keep].reset_index(drop=True)
    tau = (n_ahead[keep] + 1) / A.SESSIONS_PER_YEAR  # from the prior settlement through the expiry session (D581)
    is_call = (o["right"] == "C").to_numpy()
    K, F, px, oi = (o[c].to_numpy(float) for c in ("strike", "F", "settle", "oi"))
    signed = np.zeros(len(o))
    for i in range(0, len(o), CHUNK):
        sl = slice(i, i + CHUNK)
        iv = A.implied_vol(px[sl], F[sl], K[sl], tau[sl], is_call[sl])
        g = A.b76_gamma(F[sl], K[sl], iv, tau[sl]) * oi[sl]
        signed[sl] = np.where(np.isfinite(g), np.where(is_call[sl], g, -g), 0.0)
    return pd.Series(signed).groupby(o["session"].to_numpy()).sum().reindex(sessions)


def build(data_root: Path) -> pd.DataFrame:
    b = G0.load_bars()
    ev = pd.read_csv(REPO / "data" / "calendar" / "events.csv", encoding="utf-8")
    rel_days = set(ev.loc[ev["event"].isin(["CPI", "EMPSIT"]), "datetime_et"].str[:10])
    out = []
    for r in ROOTS:
        d = G0.daily_frame(b, r)  # every fixture session, in order; OA-A6's RTH summary
        sessions = list(d.index)
        x = b[b["root"] == r]
        piv = x[x["hhmm"].isin(["08:28", "09:24", "09:30", "15:59"])].pivot_table(
            index="session", columns="hhmm", values="close", aggfunc="first").reindex(sessions)
        # A1
        p1 = A.a1_stop(d["open"], d["high"].shift(1), d["low"].shift(1), d["atr20"])
        # A2, A3 on the adjusted settlement series (standardised over the long series, then mapped)
        sser = settlement_series(r, data_root)
        target, p2_all = A.on_finite(A.a2_trend, sser.to_numpy())  # sessions with a settlement only
        _, p3_all = A.on_finite(A.a3_voltarget, sser.to_numpy())
        z2_all, z3_all = A.on_finite(A.standardise, p2_all)[0], A.on_finite(A.standardise, p3_all)[0]
        m2 = pd.DataFrame({"P2": p2_all, "P3": p3_all, "z2": z2_all, "z3": z3_all}, index=sser.index)
        m2 = m2.reindex(sessions)
        # A4 (ES only)
        if r == "ES":
            G = dealer_gamma_es(data_root, sessions).to_numpy(float)
        else:
            G = np.full(len(sessions), np.nan)
        p4 = A.a4_pressure(G, d["open"], d["prior_close"])
        # A5
        r5 = (piv["09:24"] / piv["08:28"] - 1).to_numpy(float)
        p5 = A.a5_macro(r5, np.array([s in rel_days for s in sessions]))
        # A6
        months = sorted({s[:7] for s in sessions})
        e = etf_frame(ETF[r], data_root, months).reindex(sessions)
        rho = A.fair_ratio_prior((piv["15:59"] / e["c1559"]).to_numpy(float))
        p6 = A.a6_basis(piv["09:30"].to_numpy(float), e["c0930"].to_numpy(float), rho, e["atr20"].to_numpy(float))
        f = pd.DataFrame({"root": r, "session": sessions, "P1": p1, "P2": m2["P2"].to_numpy(), "P3": m2["P3"].to_numpy(),
                          "P4": p4, "P5": p5, "P6": p6, "G_es": G, "release": [s in rel_days for s in sessions]})
        f["z1"] = A.standardise(f["P1"].to_numpy())
        f["z2"], f["z3"] = m2["z2"].to_numpy(), m2["z3"].to_numpy()
        for k in ("4", "5", "6"):
            f["z" + k] = A.standardise(f["P" + k].to_numpy())
        out.append(f)
    res = pd.concat(out, ignore_index=True)
    return res[(res["session"] >= FIRST) & (res["session"] < RESERVED_FROM)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    t0 = time.time()
    res = build(a.data_root)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n", float_format="%.8g")
    ins = res[res["session"] >= "2016-01-04"]
    print(f"wrote {OUT.name}: {len(res):,} rows in {(time.time() - t0) / 60:.1f} min")
    print("finite share from 2016-01-04:")
    print(ins.groupby("root")[[f"z{k}" for k in range(1, 7)]].agg(lambda s: round(float(np.isfinite(s).mean()), 3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
