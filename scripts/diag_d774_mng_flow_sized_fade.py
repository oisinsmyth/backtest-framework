"""D774 DIAG (POST HOC, on D630's spent NG in-sample, 2017-05 .. 2023-12): D772's Fable R1, the MNG post-settlement fade
sized by the leveraged funds' predicted flow |I|, rebuilt independently of the agents' scripts. Two questions from the
principal (2026-10-02): is it similar to the vault's lines, and how does it do without 2022 (by year, on win rate and a
volatility-adjusted return)?

    python scripts/diag_d774_mng_flow_sized_fade.py        # SYSTEM interpreter is fine (pandas, numpy only)

Legs, on NG 1-minute bars (bar-START stamped, so "the close of bar hh:mm" is the price at hh:mm + 1 minute):
- H2, the vault's NG trade (slot 3, D723; slot 8, D649 on MNG): on D630 signal days, side = sign(q_est) at t0
  (is_tau_star), entry the close of bar t0+1, exit the close of the 14:29 bar. Checked against
  data/ledger_d630_by_year.json (counts and mean gross per year).
- R1, the fade: side = -sign(q_est at 13:50), entry the close of the 14:29 bar (D630's W_end close), exit the close of
  the 15:29 bar. The agents' cell entered at the 14:28 bar; that variant is reported.
- Gates, prior days only: T = |I| (13:50) in its walk-forward top third (prior 250 days, at least 120); V = the
  trailing-20 sd of the R1 response, in $ per MNG, >= $30.
Money: MNG $1,000 per $1/MMBtu; $4 a round trip (and $5). Full NG is 10x.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")      # data/raw-side fixtures live in the main checkout
FLOW = MAIN / "data" / "ledger_predicted_flow_daily.csv.gz"
BARS = MAIN / "data" / "fixtures" / "fut_opening_globex_1m_cl_ng_gc_si.csv.gz"
D630_BY_YEAR = REPO / "data" / "ledger_d630_by_year.json"
LINES = REPO / "temp" / "d755_other_lines.csv"                       # D770's daily lines of D737's twin, NQ F2, C1
OUT = REPO / "data" / "diag_d774_mng_flow_sized_fade.json"
SEAL = "2024-01-01"
MNG, COST, COST_HI, GATE_SD = 1000.0, 4.0, 5.0, 30.0


def plus1(hm: str) -> str:
    h, m = map(int, hm.split(":"))
    m += 1
    return f"{h + m // 60:02d}:{m % 60:02d}"


def build() -> pd.DataFrame:
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[(f["root"] == "NG") & (f["day"] < SEAL)]
    assert f["day"].max() < SEAL, "seal"
    f1350 = f[f["tau"] == "13:50"].set_index("day")
    star = f[f["is_tau_star"] == 1].drop_duplicates("day").set_index("day")
    parts = []
    for ch in pd.read_csv(BARS, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == "NG") & (ch["session"] >= "2017-01-01") & (ch["session"] < SEAL)
                & (ch["hhmm"] >= "13:45") & (ch["hhmm"] <= "15:30")]
        parts.append(ch[ch["et"].str[:10] == ch["session"]])
    b = pd.concat(parts)
    assert b["session"].max() < SEAL, "seal"
    px = b.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    one = b.groupby("session")["contract"].nunique() == 1

    def bar(day: str, hm: str) -> float:
        return float(px.at[day, hm]) if hm in px.columns and pd.notna(px.at[day, hm]) else float("nan")

    rows = []
    for day in sorted(set(f1350.index) & set(px.index)):
        if not bool(one.get(day, False)):
            continue
        d = np.sign(f1350.at[day, "q_est"])
        if not np.isfinite(d) or d == 0:
            continue
        p1428, p1429, p1529 = bar(day, "14:28"), bar(day, "14:29"), bar(day, "15:29")
        rec = {"day": day, "absI": abs(float(f1350.at[day, "I"])), "dir": d,
               "signal": int(f1350.at[day, "signal_day"] == 1),
               "r1": -d * (p1529 - p1429) * MNG, "r1_1428": -d * (p1529 - p1428) * MNG, "h2": float("nan")}
        if day in star.index:
            rec["h2"] = np.sign(star.at[day, "q_est"]) * (p1429 - bar(day, plus1(star.at[day, "tau"]))) * MNG
        rows.append(rec)
    D = pd.DataFrame(rows).dropna(subset=["r1"]).sort_values("day").reset_index(drop=True)
    D["year"] = D["day"].str[:4]
    # gates from prior days only
    D["thr"] = D["absI"].shift(1).rolling(250, min_periods=120).quantile(2 / 3)
    D["T"] = D["absI"] >= D["thr"]
    D["sd20"] = D["r1"].shift(1).rolling(20, min_periods=15).std()
    D["V"] = D["sd20"] >= GATE_SD
    D["vadj"] = D["r1"] / D["sd20"]
    return D


def lag_audit(D: pd.DataFrame) -> None:
    """Second implementation of both gates with explicit loops over earlier rows only."""
    a, r = D["absI"].to_numpy(), D["r1"].to_numpy()
    for i in range(0, len(D), 37):
        prior = a[max(0, i - 250):i]
        thr = float(np.quantile(prior, 2 / 3)) if len(prior) >= 120 else float("nan")
        assert (a[i] >= thr) == bool(D["T"].iat[i]) or not np.isfinite(thr), f"lag audit: T at row {i}"
        pr = r[max(0, i - 20):i]
        sd = float(np.std(pr, ddof=1)) if len(pr) >= 15 else float("nan")
        same = (np.isnan(sd) and np.isnan(D["sd20"].iat[i])) or abs(sd - D["sd20"].iat[i]) < 1e-9
        assert same, f"lag audit: sd20 at row {i}"


def sign_audit() -> None:
    """In money: funds predicted to BUY into the window (q_est > 0), price then FALLS after 14:29 -> the fade pays."""
    d, p1429, p1529 = 1.0, 3.000, 2.990
    assert abs(-d * (p1529 - p1429) * MNG - 10.0) < 1e-6, "sign audit"
    assert -(-d) * (p1529 - p1429) * MNG < 0, "sign audit: the mirrored side must lose"


def summ(g: pd.DataFrame) -> dict[str, Any]:
    x = g["r1"]
    n = len(x)
    if n < 3:
        return {"n": n, "mean": round(float(x.mean()), 2) if n else None}
    v = g["vadj"].dropna()
    return {"n": n, "mean": round(x.mean(), 2), "median": round(x.median(), 2), "win": round(float((x > 0).mean()), 3),
            "t": round(x.mean() / x.std(ddof=1) * math.sqrt(n), 2), "net4": round(x.mean() - COST, 2),
            "net5": round(x.mean() - COST_HI, 2), "vadj_mean": round(v.mean(), 3),
            "vadj_t": round(v.mean() / v.std(ddof=1) * math.sqrt(len(v)), 2) if len(v) > 2 else None}


def book(g: pd.DataFrame, span: pd.Series) -> dict[str, Any]:
    """The four reporting groups for a traded cell at one MNG, $4: daily series over every flow day in the span."""
    net = g["r1"] - COST
    days = span[(span >= g["day"].min()) & (span <= g["day"].max())]
    s = pd.Series(0.0, index=days.to_numpy())
    s.loc[g["day"].to_numpy()] = net.to_numpy()
    s_g = pd.Series(0.0, index=days.to_numpy())
    s_g.loc[g["day"].to_numpy()] = g["r1"].to_numpy()
    down = s[s < 0]
    eq = s.cumsum()
    k = max(1, int(round(0.01 * len(net))))
    srt = net.sort_values()
    wins, losses = net[net > 0], net[net < 0]
    top = g.assign(net=net).nlargest(5, "net")[["day", "net"]]
    return {"sharpe_net": round(s.mean() / s.std() * math.sqrt(252), 2),
            "sortino_net": round(s.mean() / math.sqrt((down ** 2).sum() / len(s)) * math.sqrt(252), 2),
            "sharpe_gross": round(s_g.mean() / s_g.std() * math.sqrt(252), 2),
            "max_drawdown": round(float((eq.cummax() - eq).max()), 0), "total_net": round(float(net.sum()), 0),
            "exposure_days_share": round(len(g) / len(days), 3), "mean_abs_gross": round(g["r1"].abs().mean(), 2),
            "breakeven_cost": round(g["r1"].mean(), 2), "skew": round(float(net.skew()), 2),
            "kurtosis": round(float(net.kurt()), 2),
            "payoff": round(wins.mean() / -losses.mean(), 2) if len(losses) else None,
            "mean_ex_top1pct": round(srt.iloc[:-k].mean(), 2), "mean_ex_bottom1pct": round(srt.iloc[k:].mean(), 2),
            "mean_trimmed": round(srt.iloc[k:-k].mean(), 2),
            "top5": [[r.day, round(r.net, 2)] for r in top.itertuples()],
            "top5_share_of_net": round(float(top["net"].sum() / net.sum()), 2) if net.sum() else None}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    sign_audit()
    D = build()
    lag_audit(D)
    with open(D630_BY_YEAR, encoding="utf-8") as fh:
        ref = {r["year"]: r for r in json.load(fh)["by_year"]}
    val = {}
    for y, g in D[D["signal"] == 1].groupby("year"):
        h = g["h2"].dropna() * 10
        if y in ref:
            val[y] = {"n_here": len(h), "n_d630": ref[y]["trades"], "gross_here_full": round(h.mean(), 2),
                      "gross_d630_full": round(ref[y]["mean_gross"], 2)}
    span = D["day"]
    cells = {"A all days": D, "B D630 signal days": D[D["signal"] == 1], "C top third |I|": D[D["T"]],
             "D top third and sd20 >= $30 (R1)": D[D["T"] & D["V"]]}
    out: dict[str, Any] = {"spec": "D774 DIAG (POST HOC)", "window": [D["day"].min(), D["day"].max()],
                           "validation_h2_vs_d630": val, "cells": {}}
    for name, g in cells.items():
        by = {y: summ(gg) for y, gg in g.groupby("year")}
        out["cells"][name] = {"all": summ(g), "ex2022": summ(g[g["year"] != "2022"]),
                              "ex2020_2022": summ(g[~g["year"].isin(["2020", "2022"])]),
                              "entry_1428_mean": round(g["r1_1428"].mean(), 2), "by_year": by}
    R = D[D["T"] & D["V"]]
    out["book_R1"] = {"all": book(R, span), "ex2022": book(R[R["year"] != "2022"], span[span.str[:4] != "2022"])}
    both = D[(D["signal"] == 1) & D["h2"].notna()]
    Rh = R[R["h2"].notna()]
    sim: dict[str, Any] = {"R1_trades": len(R), "R1_on_H2_signal_days": int((R["signal"] == 1).sum()),
                           "rho_r1_h2_signal_days": round(float(np.corrcoef(both["r1"], both["h2"])[0, 1]), 3),
                           "rho_r1_h2_on_R1_days": round(float(np.corrcoef(Rh["r1"], Rh["h2"])[0, 1]), 3)}
    if LINES.exists():
        lines = pd.read_csv(LINES, index_col=0, encoding="utf-8")
        daily = pd.Series(0.0, index=D["day"].to_numpy())
        daily.loc[R["day"].to_numpy()] = R["r1"].to_numpy()
        j = lines.join(daily.rename("r1"), how="inner")
        sim["rho_daily_with_index_lines"] = {c: round(float(j["r1"].corr(j[c])), 3) for c in lines.columns}
        sim["days_joined"] = len(j)
    out["similarity"] = sim
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"validation": val, "book_R1": out["book_R1"], "similarity": sim}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
