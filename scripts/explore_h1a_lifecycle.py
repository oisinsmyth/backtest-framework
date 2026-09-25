"""EXPLORATORY diagnosis of D627's FAIL (option D, the principal, 2026-09-25). It uses only the in-sample D627 already
spent. It can ADMIT NOTHING and changes no verdict: D627 stands as FAIL on both roots.

THE VAULT DECISION RULE. It was written, and committed, BEFORE any number in this file was computed. The principal
chose option D on the understanding that the vault is spent only if a vault test could answer:
  * The candidate lines are, per root:
      (W) the window test with the life-cycle-corrected dependent;
      (T) abnormal TAS volume.
    Both are fitted with D627's regression here.
  * A line is eligible only if its exploratory β > 0.
  * Its vault power = Φ(E − 2), where E = 0.5 × t_explore × sqrt(n_vault / n_explore). The 0.5 is the shrinkage
    allowed for an effect selected after the fact; n_vault counts the business days 2025-03-03 → 2026-09-18.
  * **The vault is spent only on eligible lines with power ≥ 0.80**: at n_vault = 390 and n_explore ≈ 1,900, that needs
    t_explore ≈ 12.7 or more (t 3.9 gives 0.13; t 8 gives 0.42). The
    t_explore used is the HC1 t on the f_est reading, with year fixed effects. If no line qualifies, the settlement
    ledger goes to STOP → write-up (the deposit's rule after a Gate 1 failure), and the vault stays unread.

WHAT IS DIAGNOSED.
  1. The life-cycle drift (D627-RESULT §4.2). D627's A_t compared the held contracts with their own trailing 20-day
     mean. A held contract moving toward the front grows in volume, so that norm lags. The corrected norm compares
     each held contract c on day t with the PREVIOUS K = 6 delivery months of the same root, each on the day it
     stood at the same number of business days to its own expiry (DTE) as c does on t. At least 4 of the 6 must be
     observed. Those days are all earlier than t, so there is no look-ahead. The same correction applies to the
     pre-window control P, the placebo window, and TAS (on the TAS contract of the same month).
     - Expiry is the Gate 0b rule (`check_uscf_months_and_rolls.last_trade`), on the in-sample business-day calendar
       extended by plain weekdays after 2025-02-28 (a calendar, not data). The extension only affects DTE labels of
       deferred contracts, and it affects all of them the same way.
     - The check that the correction worked: the share of days with A* > 0 and the median of A* should sit near
       one half and zero.
  2. D627's regression on A* (window) and T* (TAS), with and without year fixed effects, plus the placebo on the
     corrected 11:50–12:20 volume and A9's rotation null. HC1 and Newey-West t are both reported.

Output: `data/ledger_h1a_exploratory.json`. `--check` recomputes it and compares byte for byte.

    uv run python -W error::RuntimeWarning scripts/explore_h1a_lifecycle.py [--check]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_h1a_exploratory.json"
K_PREV, K_MIN = 6, 4
SHRINK, POWER_MIN = 0.5, 0.80
VAULT = ("2025-03-03", "2026-09-18")
LETTER = "FGHJKMNQUVXZ"


class ExploreError(RuntimeError):
    pass


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


R = _load("run_h1a_stage_a")
U = _load("check_uscf_months_and_rolls")


def vault_n() -> int:
    """Business days in the vault by the US federal-holiday weekday calendar: a count of days, no data."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = USFederalHolidayCalendar().holidays(VAULT[0], VAULT[1])
    return int(len(pd.bdate_range(VAULT[0], VAULT[1], freq="C", holidays=hol)))


def power(t_explore: float, n_explore: int, n_v: int) -> float:
    e = SHRINK * t_explore * math.sqrt(n_v / n_explore)
    return 0.5 * (1 + math.erf((e - 2.0) / math.sqrt(2)))


def _key(ym: str) -> tuple[int, int]:
    return int(ym[:4]), int(ym[5:7])


def lifecycle_norm(root: str, col: str, frame: pd.DataFrame, bdays: list[str]) -> dict[tuple[str, str], float]:
    """(ym, day) -> the mean of `col` over the previous K_PREV delivery months, each on the day it stood at the same
    business-day DTE as ym on `day`. Every contract-day on the calendar is 0-filled where the contract has no row."""
    ext = bdays + [d.strftime("%Y-%m-%d") for d in pd.bdate_range(pd.Timestamp(bdays[-1]) + pd.Timedelta(days=1),
                                                                   "2032-12-31")]
    pos = {d: i for i, d in enumerate(ext)}
    piv = frame.pivot_table(index="day", columns="ym", values=col, aggfunc="sum").reindex(bdays).fillna(0.0)
    expiry_i: dict[str, int] = {}
    for ym in piv.columns:
        e = U.last_trade(root, _key(ym), ext)
        expiry_i[ym] = pos[e]
    # vol at (ym, dte)
    at: dict[tuple[str, int], float] = {}
    for ym in piv.columns:
        ei = expiry_i[ym]
        s = piv[ym]
        for d, v in zip(bdays, s.to_numpy()):
            dte = ei - pos[d]
            if dte >= 0:
                at[(ym, dte)] = float(v)
    out: dict[tuple[str, str], float] = {}
    for ym in piv.columns:
        y, m = _key(ym)
        prev = []
        for k in range(1, K_PREV + 1):
            t = y * 12 + (m - 1) - k
            prev.append(f"{t // 12:04d}-{t % 12 + 1:02d}")
        ei = expiry_i[ym]
        for d in bdays:
            dte = ei - pos[d]
            if dte < 0:
                continue
            vals = [at[(p, dte)] for p in prev if (p, dte) in at]
            if len(vals) >= K_MIN:
                out[(ym, d)] = float(np.mean(vals))
    return out


def corrected(root: str, col: str, frame: pd.DataFrame, bdays: list[str], days: list[str],
              helds: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """(Σ over H_t of col on t, Σ over H_t of the life-cycle norm): NaN where any held contract lacks a norm."""
    norm = lifecycle_norm(root, col, frame, bdays)
    piv = frame.pivot_table(index="day", columns="ym", values=col, aggfunc="sum").reindex(bdays).fillna(0.0)
    now, nm = [], []
    for d, h in zip(days, helds):
        keys = h.split(";")
        now.append(float(piv.loc[d].reindex(keys, fill_value=0.0).sum()))
        vals = [norm.get((k, d)) for k in keys]
        nm.append(float(sum(vals)) if all(v is not None for v in vals) else np.nan)  # type: ignore[arg-type]
    return np.array(now), np.array(nm)


def explore(root: str, n_v: int) -> dict[str, Any]:
    b = R.build(root, read_dependent=True)
    d = b["d"]
    cal = pd.read_csv(R.CAL, encoding="utf-8")
    bdays = list(cal[cal["root"] == root]["date"])
    p = pd.read_csv(R.PANEL, encoding="utf-8",
                    usecols=["root", "kind", "day", "ym", "vol_win", "vol_pre", "vol_plc", "vol_plc_pre", "tas_vol"])
    p = p[p["root"] == root]
    out, tas = p[p["kind"] == "outright"], p[p["kind"] == "tas"]
    days, helds = list(d["day"]), list(d["held"])
    for name, col, frame in (("Astar", "vol_win", out), ("Pstar", "vol_pre", out), ("Aplc", "vol_plc", out),
                             ("Pplc", "vol_plc_pre", out), ("Tstar", "tas_vol", tas)):
        now, nm = corrected(root, col, frame, bdays, days, helds)
        d[name] = now - nm
        if name == "Astar":
            d["Astar_ratio"] = now / nm
    ok = d[["Astar", "Pstar", "Aplc", "Pplc", "Tstar"]].notna().all(axis=1)
    d = d[ok].reset_index(drop=True)
    years = d["day"].str[:4].to_numpy()
    fe = [(years == y).astype(float) for y in np.unique(years)[1:]]

    def design(q: np.ndarray, absr: str, pre: str, with_fe: bool) -> np.ndarray:
        X = R.design_matrix(d, root, q, absr, pre)
        return np.column_stack([X] + fe) if with_fe else X

    q = d["absQ"].to_numpy(float)
    res: dict[str, Any] = {"n": int(len(d)), "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
                           "drift_check": {"D627_A_share_positive": float((b["d"]["A"] > 0).mean()),
                                           "Astar_share_positive": float((d["Astar"] > 0).mean()),
                                           "Astar_median": float(d["Astar"].median()),
                                           "Astar_ratio_median": float(d["Astar_ratio"].median()),
                                           "Tstar_share_positive": float((d["Tstar"] > 0).mean())}}
    lines: dict[str, Any] = {}
    for line, ycol, pre in (("W_window", "Astar", "Pstar"), ("T_tas", "Tstar", "Pstar")):
        y = d[ycol].to_numpy(float)
        f0 = R.fit(y, design(q, "absr", pre, False))
        f1 = R.fit(y, design(q, "absr", pre, True))
        ts = R.rotation(y, design(q, "absr", pre, False), years, np.random.default_rng(R.ROT_SEED))
        p50, p95, se = R.p95_with_se(ts, np.random.default_rng(R.ROT_SEED))
        t_ex = f1["t_hc1"]
        pw = power(t_ex, len(d), n_v) if f1["beta"] > 0 else 0.0
        lines[line] = {"pooled": f0, "year_fe": f1, "rotation": {"p50": p50, "p95": p95, "p95_se": se},
                       "eligible": bool(f1["beta"] > 0), "t_explore": t_ex,
                       "vault_power_at_half_effect": pw, "qualifies": bool(f1["beta"] > 0 and pw >= POWER_MIN)}
    yp = d["Aplc"].to_numpy(float)
    qp = d["absQ_plc"].to_numpy(float)
    okp = np.isfinite(qp) & d["plc_clean"].to_numpy(bool)
    lines["W_placebo"] = {"year_fe": R.fit(yp[okp], np.column_stack([R.design_matrix(d, root, qp, "absr_plc", "Pplc")]
                                                                   + fe)[okp])}
    res["lines"] = lines
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    n_v = vault_n()
    out: dict[str, Any] = {"label": "EXPLORATORY: spent in-sample, admits nothing, changes no verdict (D627 FAILS)",
                           "rule": {"shrink": SHRINK, "power_min": POWER_MIN, "vault": VAULT, "n_vault": n_v,
                                    "k_prev": K_PREV, "k_min": K_MIN}, "roots": {}}
    for root in ("CL", "NG"):
        out["roots"][root] = explore(root, n_v)
    q = [f"{r}:{ln}" for r, v in out["roots"].items() for ln, x in v["lines"].items() if x.get("qualifies")]
    out["decision"] = {"qualifying_lines": q,
                       "outcome": "spend the vault on the qualifying lines (a pre-registration first)" if q
                       else "STOP -> write-up; the vault stays unread"}
    text = json.dumps(out, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise ExploreError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for r, v in out["roots"].items():
        print(r, "n", v["n"], v["drift_check"])
        for ln, x in v["lines"].items():
            fe = x["year_fe"]
            extra = (f" | rot p95 {x['rotation']['p95']:.2f} | vault power {x['vault_power_at_half_effect']:.3f}"
                     f" qualifies {x['qualifies']}") if "rotation" in x else ""
            pooled = f"pooled b {x['pooled']['beta']:.4f} t {x['pooled']['t_hc1']:.2f} | " if "pooled" in x else ""
            print(f"  {ln:9s} {pooled}FE b {fe['beta']:.4f} t {fe['t_hc1']:.2f} NW {fe['t_nw5']:.2f}{extra}")
    print("decision:", out["decision"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
