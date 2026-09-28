"""POST HOC, on D630's spent in-sample: the NG settlement trade's stop and early-profit exits, singled out and combined,
at the micro size (MNG). Exploratory: it admits nothing, changes no verdict, and a cell chosen from its grid would be
chosen after seeing results (the principal asked for the grid, 2026-09-28).

    uv run python scripts/explore_d630_exits_micro.py --run    # the venv (statsmodels) -> data/ledger_d630_exits_micro.json

THE TRADES are D630's own (`run_h2_ng_stage_a.build`): the 1,028 traded days, the fill at the close of bar t0+1, the
structural exit at the close of the 14:29 bar. THE EXITS are D630 §7.4's book frame generalised to a multiple k of the
day's predicted impact |I| (in price):
- stop at k_s x |I| adverse, on any bar from t0+2 to 14:29, filled AT the stop price (a sensitivity adds one tick);
- early profit at k_t x |I| favourable, on bars before W_start (14:28), filled AT the target price on a touch (a
  sensitivity needs one tick through it);
- both in one bar: the stop (D630's rule).
k_s, k_t in {none, 0.5, 1, 1.5, 2}: 25 cells, among them the primary (none, none) and D630's book frame (1, 1).
THE RATCHETING TRAILING STOP (the principal, 2026-09-28): the same k_s, but the stop follows the best extreme reached at
k_s x |I| and never moves back (`exit_money`, trail=True; `audit_trail` proves it on a buy, its mirror-image sell, and
a bar that must not tighten its own stop): 20 more cells, k_s in {0.5, 1, 1.5, 2} x k_t as above.

MONEY: the stop and target are price levels, so MNG's gross is exactly 1/10 of the full contract's (1,000 against
10,000 MMBtu), and its cost is D630's $5 a round trip ($3 + $1 + $1 slippage) against the full contract's $26. Daily
series run over all 1,936 in-sample days with zeros on untraded days, as D630's component line does.

KNOWN ANSWERS (raise): (none, none) reproduces D630's primary money on every trade and its MNG line (net Sharpe 0.4387);
(1, 1) reproduces D630's book frame on every trade ($57.61, t 6.35). The sign audit is D630's money audit.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "ledger_d630_exits_micro.json"
PUBLISHED = REPO / "data" / "ledger_h2_ng_stage_a.json"
KS = (None, 0.5, 1.0, 1.5, 2.0)
TICK = 0.001
HEADLINE = {"time exit only (D630 primary)": (None, None, False), "stop 1x only": (1.0, None, False),
            "target 1x only": (None, 1.0, False), "stop 1x + target 1x (D630 book frame)": (1.0, 1.0, False),
            "trailing stop 1x only": (1.0, None, True), "trailing stop 1x + target 1x": (1.0, 1.0, True)}


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


R = _load("run_h2_ng_stage_a")
H = sys.modules["run_h1a_stage_a"]
DATA = _main_checkout(REPO) / "data"  # the gitignored inputs live in the main checkout when this runs in a worktree
for mod, names in ((R, ("FLOW", "BARS", "PANEL")), (H, ("FLOW", "PANEL", "FSHARE"))):
    for n in names:
        p = getattr(mod, n)
        if not p.exists():
            setattr(mod, n, DATA / p.name)
RATIO = R.MNG_MULT / R.MULT


class ExitError(RuntimeError):
    pass


def exit_money(dr: float, fill: float, exit_px: float, absI: float, mins: np.ndarray, hi: np.ndarray, lo: np.ndarray,
               t0: str, ks: float | None, kt: float | None, stop_slip: int = 0, through: int = 0,
               trail: bool = False) -> tuple[float, str, int]:
    """Full-contract gross dollars, the exit reason, and minutes from t0 to the exit.

    trail=True makes the stop a RATCHETING TRAILING stop: it starts at ks x |I| adverse from the fill, then sits
    ks x |I| behind the best extreme reached (the high for a buy, the low for a sell) and never moves back. Each bar is
    tested against the stop as it stood BEFORE that bar, and only then does the bar's extreme move it: a bar's own high
    never tightens a stop that the same bar's low then hits (bar data cannot say which came first)."""
    stop = fill - dr * ks * absI if ks is not None else None
    tgt = fill + dr * kt * absI if kt is not None else None
    best = fill
    first = R.add_min(t0, 2)
    t0m = int(t0[:2]) * 60 + int(t0[3:])
    for m, h, lw in zip(mins, hi, lo):
        if m < first or m >= R.EXIT_END:
            continue
        hit_s = stop is not None and ((lw <= stop) if dr > 0 else (h >= stop))
        hit_t = (tgt is not None and m < R.W_START
                 and ((h >= tgt + through * TICK) if dr > 0 else (lw <= tgt - through * TICK)))
        if hit_s or hit_t:
            held = int(m[:2]) * 60 + int(m[3:]) - t0m
            if hit_s:
                return R.money(dr, fill, stop - dr * stop_slip * TICK), ("trail" if trail else "stop"), held
            return R.money(dr, fill, tgt), "target", held
        if trail and stop is not None:
            best = max(best, h) if dr > 0 else min(best, lw)
            stop = max(stop, best - ks * absI) if dr > 0 else min(stop, best + ks * absI)
    return R.money(dr, fill, exit_px), "time", int(R.EXIT_END[:2]) * 60 + int(R.EXIT_END[3:]) - t0m


def audit_trail() -> None:
    """A buy at 10.000 with |I| 0.010 and k 1: the market rises to 10.030 then falls. The fixed stop (9.990) is never
    hit; the trailing stop ratchets to 10.020 and exits there (+$200 full size), never back down; a bar whose high and
    low both breach does not tighten its own stop."""
    mins = np.array(["13:52", "13:53", "13:54", "13:55"], dtype=object)
    hi = np.array([10.010, 10.030, 10.025, 10.015])
    lo = np.array([10.000, 10.020, 10.019, 10.005])
    fixed = exit_money(1.0, 10.0, 10.005, 0.010, mins, hi, lo, "13:50", 1.0, None)
    trail = exit_money(1.0, 10.0, 10.005, 0.010, mins, hi, lo, "13:50", 1.0, None, trail=True)
    if fixed[1] != "time" or not math.isclose(fixed[0], 50.0):
        raise ExitError(f"trail audit: the fixed stop {fixed}")
    if trail[1] != "trail" or not math.isclose(trail[0], 200.0, abs_tol=1e-6) or trail[2] != 4:
        raise ExitError(f"trail audit: the trailing stop {trail}")
    sell = exit_money(-1.0, 10.0, 9.995, 0.010, mins, 20.0 - lo, 20.0 - hi, "13:50", 1.0, None, trail=True)
    if sell[1] != "trail" or not math.isclose(sell[0], 200.0, abs_tol=1e-6) or sell[2] != 4:
        raise ExitError(f"trail audit: the sell side (the mirror image) {sell}")
    one = exit_money(1.0, 10.0, 10.0, 0.010, np.array(["13:52"], dtype=object), np.array([10.050]),
                     np.array([10.030]), "13:50", 1.0, None, trail=True)
    if one[1] != "time":
        raise ExitError(f"trail audit: a bar tightened its own stop {one}")


def trades() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    b = R.build(read_returns=True)
    d = b["d"]
    g = R.signed(d)
    ok = d["traded"].to_numpy() & np.isfinite(g)
    bars = pd.read_csv(R.BARS, encoding="utf-8", usecols=["day", "ym", "minute", "high", "low", "close"])
    if (bars["day"] >= R.CUT).any():
        raise ExitError("a bar on or after the cut is in memory")
    groups = {k: (x["minute"].to_numpy(), x["close"].to_numpy(), x["high"].to_numpy(), x["low"].to_numpy())
              for k, x in bars.sort_values(["day", "ym", "minute"]).groupby(["day", "ym"], sort=False)}
    px = pd.read_csv(R.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "px_1350"])
    px = px[(px["root"] == "NG") & (px["kind"] == "outright")].set_index(["day", "ym"])["px_1350"]
    empty = (np.array([], dtype=object),) + (np.array([]),) * 3
    rows = []
    for i, r in enumerate(d.itertuples(index=False)):
        if not ok[i]:
            continue
        mins, cl, hi, lo = groups.get((r.day, r.traded_ym), empty)
        s1350 = float(px.get((r.day, r.traded_ym), np.nan))
        fill = R.asof(mins, cl, R.fill_end(r.tau), s1350)
        rows.append({"i": i, "day": r.day, "dir": r.dir, "t0": r.tau, "absI": r.absI_px, "fill": fill,
                     "exit": R.asof(mins, cl, R.EXIT_END, s1350), "mins": mins, "hi": hi, "lo": lo,
                     "g_primary": float(g[i]), "g_book": float(d["g_book"].iloc[i])})
    return d, rows


def cell(d: pd.DataFrame, rows: list[dict[str, Any]], ks: float | None, kt: float | None, stop_slip: int = 0,
         through: int = 0, detail: bool = False, trail: bool = False) -> dict[str, Any]:
    C = sys.modules.get("backtest_framework.validation.component_series") or R._load_cs()
    res = [exit_money(r["dir"], r["fill"], r["exit"], r["absI"], r["mins"], r["hi"], r["lo"], r["t0"], ks, kt,
                      stop_slip, through, trail) for r in rows]
    gf = np.array([x[0] for x in res])
    why = np.array([x[1] for x in res])
    held = np.array([x[2] for x in res], dtype=float)
    idx = np.array([r["i"] for r in rows])
    years = np.array([r["day"][:4] for r in rows])
    out: dict[str, Any] = {"stop_k": ks, "target_k": kt, "trailing": trail, "n": int(len(gf)),
                           "share_stopped": float(np.isin(why, ["stop", "trail"]).mean()), "share_target": float((why == "target").mean()),
                           "mean_minutes_held": float(held.mean())}
    for size, scale, cost in (("full", 1.0, R.COST), ("micro", RATIO, R.MNG_COST)):
        g = gf * scale
        dg = np.zeros(len(d))
        dg[idx] = g
        dn = np.zeros(len(d))
        dn[idx] = g - cost
        cum = np.cumsum(dn)
        se = float(g.std(ddof=1) / math.sqrt(len(g)))
        blk = {"mean_gross": float(g.mean()), "mean_net": float(g.mean() - cost), "t_gross": float(g.mean() / se),
               "sharpe_gross": C.sharpe(dg), "sortino_gross": C.sortino(dg), "sharpe_net": C.sharpe(dn),
               "sortino_net": C.sortino(dn), "hit_rate_net": float((g - cost > 0).mean()),
               "total_net_usd": float(dn.sum()), "max_drawdown_usd_net": float((cum - np.maximum.accumulate(cum)).min()),
               "breakeven_cost_usd_rt": float(g.mean())}
        x22 = years != "2022"
        dn22 = dn.copy()
        dn22[idx[~x22]] = 0.0
        keep = np.ones(len(d), bool)
        keep[idx[~x22]] = False  # 2022's days leave the calendar, not just its trades
        blk["without_2022"] = {"n": int(x22.sum()), "mean_net": float(g[x22].mean() - cost),
                               "sharpe_net": C.sharpe(dn[keep]), "sortino_net": C.sortino(dn[keep])}
        if detail:
            net = np.sort(g - cost)
            k = max(1, int(math.ceil(0.01 * len(net))))
            s = pd.Series(net)
            blk["distribution_net"] = {
                "mean": float(net.mean()), "median": float(np.median(net)), "win_rate": float((net > 0).mean()),
                "payoff": float(net[net > 0].mean() / -net[net < 0].mean()), "skew": float(s.skew()),
                "kurtosis_excess": float(s.kurt()), "mean_ex_top_1pct": float(net[:-k].mean()),
                "mean_ex_bottom_1pct": float(net[k:].mean()), "mean_trimmed_both": float(net[k:-k].mean())}
            blk["by_year_mean_net"] = {y: {"n": int((years == y).sum()), "mean_net": float(g[years == y].mean() - cost)}
                                       for y in sorted(set(years))}
            blk["skew_daily_net"] = float(pd.Series(dn).skew())
        out[size] = blk
    out["_gross_full"] = gf
    return out


def run() -> dict[str, Any]:
    t = time.time()
    R.audit_money()
    audit_trail()
    d, rows = trades()
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))["NG"]
    base = cell(d, rows, None, None)
    book = cell(d, rows, 1.0, 1.0)
    gp = np.array([r["g_primary"] for r in rows])
    gb = np.array([r["g_book"] for r in rows])
    if not np.array_equal(base["_gross_full"], gp):
        raise ExitError("known answer: (none, none) does not rebuild D630's primary money on every trade")
    if not np.array_equal(book["_gross_full"], gb):
        raise ExitError("known answer: (1, 1) does not rebuild D630's book frame on every trade")
    if not math.isclose(base["micro"]["sharpe_net"], pub["component_mng"]["sharpe_net"], rel_tol=0, abs_tol=1e-12):
        raise ExitError(f"known answer: MNG net Sharpe {base['micro']['sharpe_net']} vs D630's "
                        f"{pub['component_mng']['sharpe_net']}")
    if not math.isclose(book["full"]["mean_gross"], pub["book_frame"]["mean"], rel_tol=0, abs_tol=1e-9):
        raise ExitError("known answer: the book frame's mean")
    if np.array_equal(base["_gross_full"], book["_gross_full"]):
        raise ExitError("right-quantity: the exits changed nothing")
    grid = []
    for trail in (False, True):
        for ks in KS:
            if trail and ks is None:
                continue
            for kt in KS:
                c = cell(d, rows, ks, kt, trail=trail)
                c.pop("_gross_full")
                grid.append(c)
    headline = {}
    for name, (ks, kt, trail) in HEADLINE.items():
        c = cell(d, rows, ks, kt, detail=True, trail=trail)
        c.pop("_gross_full")
        c["sensitivity"] = {}
        if ks is not None:
            s = cell(d, rows, ks, kt, stop_slip=1, trail=trail)
            c["sensitivity"]["stop_fills_one_tick_worse"] = {k: s["micro"][k] for k in ("mean_net", "sharpe_net", "sortino_net")}
        if kt is not None:
            s = cell(d, rows, ks, kt, through=1, trail=trail)
            c["sensitivity"]["target_needs_one_tick_through"] = {k: s["micro"][k] for k in ("mean_net", "sharpe_net", "sortino_net")}
        headline[name] = c
    doc = {"spec": "POST HOC on D630's spent in-sample (the principal, 2026-09-28): stops and early-profit exits at "
                   "k x |I|, singled out and combined, at MNG size. Admits nothing.",
           "known_answers": "primary and book frame rebuilt on every trade; MNG net Sharpe matches D630 exactly",
           "costs_usd_round_trip": {"full": R.COST, "micro": R.MNG_COST}, "tick": TICK,
           "headline": headline, "grid": grid, "runtime_min": round((time.time() - t) / 60, 2)}
    OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if not a.run:
        ap.print_help()
        return 1
    doc = run()
    for name, c in doc["headline"].items():
        m, f = c["micro"], c["full"]
        print(f"{name:42s} MNG gross {m['mean_gross']:6.2f} net {m['mean_net']:6.2f} Sh {m['sharpe_net']:5.2f} "
              f"So {m['sortino_net']:5.2f} | full net {f['mean_net']:6.1f} Sh {f['sharpe_net']:5.2f} | stop "
              f"{c['share_stopped']:.2f} tgt {c['share_target']:.2f} hold {c['mean_minutes_held']:.0f}m | ex-2022 MNG "
              f"net {m['without_2022']['mean_net']:5.2f} Sh {m['without_2022']['sharpe_net']:5.2f} | {c['sensitivity']}")
    for trail in (False, True):
        for key, lab in (("sharpe_net", "net Sharpe"), ("mean_net", "net $ a trade")):
            print(f"\nMNG {lab}, {'TRAILING' if trail else 'FIXED'} stop (rows stop k, cols target k):")
            tab = pd.DataFrame([(str(c["stop_k"]), str(c["target_k"]), c["micro"][key]) for c in doc["grid"]
                                if c["trailing"] == trail], columns=["stop", "target", "v"])
            print(tab.pivot(index="stop", columns="target", values="v").round(2).to_string())
    print(f"\nwrote {OUT.relative_to(REPO)} in {doc['runtime_min']} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
