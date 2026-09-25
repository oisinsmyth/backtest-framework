"""Stage A's predictor inputs: P1, the leveraged funds' rebalance, at each evaluation time, per NYMEX business day for
CL and NG, 2017-05-22 → 2025-02-28 (settlement ledger A8, H1a's |Q_rem|; deposit §4 lines 143–160).

It builds inputs and computes no statistic: no volume is read, and nothing is regressed.

WHAT IS COMPUTED. For fund f with leverage L on business day t, at time τ:
    r(t, τ)   = the held return from the prior settlement to τ (line 146), on the fund's HELD contracts
    Q1_f(t, τ) = AUM_f[t-1] x L(L-1) x r(t, τ) x f_fut[t-1] / (multiplier x P_held(t, τ))   (line 156)
At Stage A, Q_rem is P1 alone (A8: K = 0, p = 0). UNG and USO have L = +1 and so no P1 (unit test 2); only
BOIL/KOLD (NG) and UCO/SCO (CL) enter.

THE HELD CONTRACTS are the index's, as Gate 0b proved them. No holdings are re-derived here; the functions are
imported from the Gate 0b scripts.
  * NG, BOIL and KOLD: the BCOM Natural Gas subindex under S0 (`gate_0b_ng_nav.contracts_for`, `s0`). On business
    day d the index holds (1-b) units of the lead contract and b of the next, with b = s0(BD of d).
  * CL era A (to 2020-09-16), UCO and SCO: the BCOM WTI subindex under S0 (`gate_0b_cl_nav.era_a_contracts`).
  * CL era B (from 2020-09-17): the Balanced WTI index. It has three components: monthly, June and December
    (`era_b_components`). Each component rolls on the documented "2-day, weights from BD3" schedule
    (`gate_0b_cl_nav._window(3, 2)`). The value weights v drift with prices and are reset to one third at the
    BD1 close in March and September, tracked from the 2020-09-01 reset exactly as `gate_0b_cl_nav.index_returns`
    tracks them.
  * KNOWN ANSWER (raises): at τ = the settlement, this file's day-level ratio must equal the Gate 0b functions'
    own `index_returns` bit for bit on every business day. The single-component Q must equal the ledger's
    `q1_rebalance` bit for bit.

THE CONTRACT SPLIT. The fund's rebalance notional is split across components by value weight at τ, and within a
component by quantity: (1-b) of the units in the lead and b in the next. `held` lists every held contract, and the
contracts file gives each one's share of the units. P_held is the reciprocal of contracts per dollar, so
Q = notional / (multiplier x P_held) holds exactly on every era. The principal decided on 2026-09-25 that H1a's
dependent is the window volume summed over the held contracts. The largest-share contract is `traded_ym`, reported
beside it.

THE FUTURES SHARE. Q is linear in f per fund, so each fund's Q at f = 1 (`q1_*`) is stored. The runner then forms any
reading, and A4's imputation draws, exactly. Stored: f_est (A4's primary), f_pit, f_lo and f_hi (A3's readings),
and σ_q (A4 under A6). σ_q = h/1.645 on an estimated day, h on a DISFAVOURED quarter and 0 on a proven day, with
h = 0.162 (`ledger_fut_share_summary_a6.json`). The totals are q_est, q_pit, q_lo and q_hi.

THE GATE, §7.2, at every τ: |I| ≥ 3 x RT_cost AND SNR ≥ 1.5. Each piece:
  * I = 0.7 x σ_d x sqrt(|Q_rem| / V_d) x P_held (§5.3). Q_rem = q_est: at Stage A, P1 alone.
  * σ_d: the sample std of the held index's daily return, R_d - 1, over business days t-20 .. t-1.
  * V_d: the sum over the held contracts of each one's mean whole-session volume (`vol_ses`) over t-20 .. t-1.
  * SNR = |Q_rem| / σ_Q, where σ_Q² is the sum over the two funds of A5's var_Q1:
        (c x f_est)² σ_rem² + (c x r)² σ_q²,   with c = the contracts per unit return at f = 1.
    σ_rem is the sample std, over t-20 .. t-1 (at least 15 valid days), of the held return from τ to the settlement,
    R_d / (1 + r(τ)) - 1.
  * RT_cost: full-size CL and NG (the principal, 2026-09-25), on the repo's default cost line
    (`futures_costs.json`). CL uses d508_exec: $6 + 1.546 ticks x $10 = $21.46. NG uses the one-tick convention:
    $6 + $10 = $16. Both crossings were measured 2025-09 → 2026-09 and applied to older, cheaper years: optimistic,
    as the table itself says.
The earliest-pass τ* (§7.1) is the first of 13:50, 14:00 and 14:10 that passes, else 14:10 (A8: H1a scores every
day). It is defined only on days where all three are evaluable. `gate_pass` is -1 where it is not (warm-up, or a
stale leg).

PRICES AT τ are the window panel's as-of prices (`data/ledger_window_volume_daily.csv.gz`, px_HHMM): the last
one-second close at or before τ, from 09:30 ET. A held contract with no trade since 09:30 has no price at τ. Its
component return is then taken as 0 (P_held = the prior settlement), and the row is flagged `stale`. The
count is reported.

INPUTS, all read below the cut 2025-03-01 (A6):
  * settlements: `check_uscf_months_and_rolls.settlements`. These are Gate 0b's loaders (fut_settle_strip
    through `load_panel`), with holiday republications dropped and the 2020 holes EIA-filled. That is the
    same business-day calendar as `build_ledger_calendar.py`.
  * AUM[t-1]: `fund_nav_daily` through `load_panel(reserved_from="2025-03-01")`, at the fund's latest NAV date
    strictly before t.
  * f_fut[t-1]: `data/ledger_fut_share_daily_a6.csv.gz`, the latest row strictly before t (its NAV date must equal
    AUM's). All four readings are carried, with f_est primary (A4). Note that f_est is interpolated between
    published quarter-ends, so it is not point-in-time. That is A3/A4's design, and f_pit is the point-in-time
    reading beside it.
  * the window panel's `vol_ses` for V_d, `data/ledger_fut_share_summary_a6.json` for h and the DISFAVOURED
    quarters, and `data/futures_costs.json` for RT_cost.

Outputs:
  * `data/ledger_predicted_flow_daily.csv.gz` (gitignored): one row per (root, day, τ).
  * `data/ledger_predicted_flow_contracts.csv.gz` (gitignored): one row per (root, day, τ, held contract).
  * `data/ledger_predicted_flow_summary.json` (tracked).
`--check` rebuilds all three and compares them byte for byte.

    uv run python scripts/build_predicted_flow_panel.py [--check]
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import hashlib
import importlib.util
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_framework.data.panels import load_panel
from backtest_framework.ledger.flows import held_return, q1_notional, q1_rebalance

REPO = Path(__file__).resolve().parents[1]
OUT_DAY = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
OUT_CON = REPO / "data" / "ledger_predicted_flow_contracts.csv.gz"
OUT_SUM = REPO / "data" / "ledger_predicted_flow_summary.json"
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
FSHARE = REPO / "data" / "ledger_fut_share_daily_a6.csv.gz"
FSUM = REPO / "data" / "ledger_fut_share_summary_a6.json"
COSTS = REPO / "data" / "futures_costs.json"
Y, K_COST, SNR_MIN = 0.7, 3.0, 1.5  # §5.3 (decision D6) and §7.2
N_TRAIL, N_REM_MIN = 20, 15  # §5.3's 20-day windows; σ_remaining needs 15 of its 20 days (declared here)
CANDIDATES = ("13:50", "14:00", "14:10")  # §7.1
CUT, FIRST, LAST = "2025-03-01", "2017-05-22", "2025-02-28"
SWITCH = "2020-09-17"
TAUS = ("11:30", "13:50", "14:00", "14:10", "14:28")  # 11:30 is H1a's time placebo; 14:28 is W_start
FUNDS = {"NG": {"BOIL": 2, "KOLD": -2}, "CL": {"UCO": 2, "SCO": -2}}
MULT = {"NG": 10_000.0, "CL": 1_000.0}
Key = tuple[int, int]


class FlowPanelError(RuntimeError):
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


U = _load("check_uscf_months_and_rolls")
U.G.RESERVED_FROM = CUT  # A6. Both copies of gate_0b_ng_nav must carry the cut (build_ledger_calendar.py's note)
U.GCL.G.RESERVED_FROM = CUT
G, GCL = U.G, U.GCL
B_SCHED = GCL._window(3, 2)  # era B's documented "2-day, weights from BD3"


def _ym_str(k: Key) -> str:
    return f"{k[0]:04d}-{k[1]:02d}"


def legs(lead: Key, nxt: Key, b: float) -> list[tuple[Key, float]]:
    """A component's contracts and their quantities per unit, as `gate_0b_cl_nav._ratio` prices it."""
    if lead == nxt or b == 0.0:
        return [(lead, 1.0)]
    if b == 1.0:
        return [(nxt, 1.0)]
    return [(lead, 1.0 - b), (nxt, b)]


# ------------------------------------------------------------------ holdings
def holdings(root: str, days: list[str], bd: dict[str, int]) -> dict[str, list[tuple[float, Key, Key, float]]]:
    """day -> [(value weight carried from the prior close, lead, next, b)] per component, for the day's holdings."""
    out: dict[str, list[tuple[float, Key, Key, float]]] = {}
    v = [1 / 3, 1 / 3, 1 / 3]
    started = False
    for p, d in zip(days, days[1:]):
        k = bd[d]
        if root == "NG":
            lead, nxt = G.contracts_for(d)
            out[d] = [(1.0, lead, nxt, G.s0(k))]
            continue
        b = G.s0(k) if d < "2020-09-01" else B_SCHED(k)
        if d < SWITCH:
            lead, nxt = GCL.era_a_contracts(d)
            out[d] = [(1.0, lead, nxt, b)]
        if d < "2020-09-01":
            continue
        comps = GCL.era_b_components(d)
        st_d, st_p = SETTLES[root].get(d, {}), SETTLES[root].get(p, {})
        try:
            r = [GCL._ratio(st_d, st_p, lead, nxt, b) for lead, nxt in comps]
        except KeyError:
            if d >= SWITCH:
                raise FlowPanelError(f"CL era B: a component settlement is missing on {d} or {p}")
            continue
        if started:
            if d >= SWITCH:
                out[d] = [(vi, lead, nxt, b) for vi, (lead, nxt) in zip(v, comps)]  # unnormalised, as the gate keeps v
            v = [vi * ri for vi, ri in zip(v, r)]
        if k == 1 and d[5:7] in ("03", "09"):
            tot = sum(v)
            v = [tot / 3] * 3
            started = True
    return out


def known_answer(root: str, days: list[str], bd: dict[str, int],
                 hold: dict[str, list[tuple[float, Key, Key, float]]]) -> dict[str, float]:
    """At the settlement, the holdings' ratio must equal Gate 0b's own index_returns, bit for bit. Returns the
    settlement-to-settlement ratio R_d of every checked day (σ_d's input)."""
    st = SETTLES[root]
    if root == "NG":
        ref = G.index_returns(days, bd, st, G.s0)
    else:
        ref = GCL.index_returns(days, bd, st, G.s0, sched_b=B_SCHED)
    out: dict[str, float] = {}
    for p, d in zip(days, days[1:]):
        if d not in hold or ref.get(d) is None:
            continue
        comps = hold[d]
        if root == "NG":
            # gate_0b_ng_nav.index_returns' own arithmetic. It does NOT short-circuit lead == next (Table 9 names
            # November for both September and October), where (1-b)x + bx differs from x by an ULP.
            (_w, lead, nxt, b), = comps
            s_d, s_p = st[d], st[p]
            if b == 0.0:
                rs = [s_d[lead] / s_p[lead]]
            elif b == 1.0:
                rs = [s_d[nxt] / s_p[nxt]]
            else:
                rs = [((1 - b) * s_d[lead] + b * s_d[nxt]) / ((1 - b) * s_p[lead] + b * s_p[nxt])]
        else:
            rs = [GCL._ratio(st[d], st[p], lead, nxt, b) for _w, lead, nxt, b in comps]
        if len(comps) == 1:
            mine = rs[0]
        else:
            tot = sum(w for w, *_ in comps)  # gate_0b_cl_nav's own association: sum(v_i r_i) / sum(v)
            mine = sum(w * r for (w, *_), r in zip(comps, rs)) / tot
        if mine != ref[d]:
            raise FlowPanelError(f"{root} {d}: holdings ratio {mine!r} != Gate 0b index_returns {ref[d]!r}")
        out[d] = mine
    return out


# ------------------------------------------------------------------ inputs
SETTLES: dict[str, dict[str, dict[Key, float]]] = {}


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    for root in ("CL", "NG"):
        st = U.settlements(root)
        if any(d >= CUT for d in st):
            raise FlowPanelError(f"{root}: a settlement dated on or after {CUT} is in memory")
        SETTLES[root] = st
    nav_p = load_panel("fund_nav_daily", reserved_from=CUT, usecols=["date", "fund", "aum"])
    nav = nav_p.frame
    nav = nav[nav["fund"].isin(["BOIL", "KOLD", "UCO", "SCO"])].copy()
    nav["date"] = nav["date"].astype(str)
    fs = pd.read_csv(FSHARE, encoding="utf-8", usecols=["fund", "date", "f_est", "f_pit", "f_lo", "f_hi", "method"])
    fs = fs[fs["fund"].isin(["BOIL", "KOLD", "UCO", "SCO"])]
    px = pd.read_csv(PANEL, encoding="utf-8",
                     usecols=["root", "kind", "day", "ym", "vol_ses"] + [f"px_{t.replace(':', '')}" for t in TAUS])
    px = px[px["kind"] == "outright"].drop(columns="kind")
    for name, df, col in (("fund_nav_daily", nav, "date"), ("fut_share", fs, "date"), ("window panel", px, "day")):
        if (df[col] >= CUT).any():
            raise FlowPanelError(f"{name}: a row on or after {CUT} is in memory")
    reads = {"fund_nav_daily": {"sha256": nav_p.sha256, **nav_p.record},
             "fut_share_a6": {"sha256": hashlib.sha256(FSHARE.read_bytes()).hexdigest()},
             "fut_share_summary_a6": {"sha256": hashlib.sha256(FSUM.read_bytes()).hexdigest()},
             "window_panel": {"sha256": hashlib.sha256(PANEL.read_bytes()).hexdigest()},
             "futures_costs": {"sha256": hashlib.sha256(COSTS.read_bytes()).hexdigest()}}
    return nav, fs, px, reads


def sigma_q_table() -> tuple[float, dict[str, set[str]]]:
    """A4 under A6: h = the pooled p90, and the per-fund DISFAVOURED quarters (σ_q = h there, h/1.645 elsewhere)."""
    s = json.loads(FSUM.read_text(encoding="utf-8"))
    return float(s["h_pooled_p90"]), {f: set(v["post_hoc_disfavoured_quarters"]) for f, v in s["funds"].items()}


def rt_cost() -> dict[str, dict[str, Any]]:
    """The repo's default cost line per full-size root (futures_costs.json `default_line`), in USD and price units."""
    c = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]
    out: dict[str, dict[str, Any]] = {}
    for root in ("CL", "NG"):
        f = c[root]["full"]
        line = f["default_line"]
        usd = float(f["commission_rt_usd"]["value"]) + float(f["crossing_ticks_rt"][line]["value"]) * float(f["tick_usd"])
        if float(f["usd_per_point"]) != MULT[root]:
            raise FlowPanelError(f"{root}: cost table multiplier {f['usd_per_point']} != {MULT[root]}")
        out[root] = {"line": line, "usd": usd, "price_units": usd / MULT[root]}
    return out


def _quarter(day: str) -> str:
    return f"{day[:4]}-Q{(int(day[5:7]) - 1) // 3 + 1}"


# ------------------------------------------------------------------ build
def build() -> tuple[bytes, bytes, str]:
    nav, fs, px, reads = load_inputs()
    h, disfav = sigma_q_table()
    costs = rt_cost()
    aum = {f: (list(g["date"]), list(g["aum"].astype(float))) for f, g in nav.sort_values("date").groupby("fund")}
    fmap: dict[str, tuple[list[str], list[tuple[float, float, float, float, str]]]] = {}
    for f, g in fs.sort_values("date").groupby("fund"):
        fmap[f] = (list(g["date"]), list(zip(g["f_est"].astype(float), g["f_pit"].astype(float), g["f_lo"].astype(float),
                                             g["f_hi"].astype(float), g["method"].astype(str))))
    pxmap = {(r, d, ym): row for r, d, ym, _v, *row in px.itertuples(index=False, name=None)}
    recs: list[dict[str, Any]] = []
    con_rows: list[str] = ["root,day,tau,ym,px_tau,settle_prev,stale,units_share"]
    summary: dict[str, Any] = {"cut": CUT, "window": [FIRST, LAST], "taus": list(TAUS), "reads": reads, "roots": {},
                               "a4_h": h, "a4_disfavoured": {f: sorted(v) for f, v in disfav.items()},
                               "rt_cost": costs, "gate": {"Y": Y, "k_cost": K_COST, "snr_min": SNR_MIN,
                                                          "window": N_TRAIL, "sigma_rem_min_obs": N_REM_MIN}}
    ratios: dict[str, dict[str, float]] = {}
    held_of: dict[str, dict[str, list[str]]] = {}
    for root in ("CL", "NG"):
        st = SETTLES[root]
        days = sorted(st)
        if days[-1] < LAST:
            raise FlowPanelError(f"{root}: business days end {days[-1]}, short of {LAST}: a stale cut")
        bd: dict[str, int] = {}
        cnt: dict[str, int] = {}
        for d in days:
            cnt[d[:7]] = cnt.get(d[:7], 0) + 1
            bd[d] = cnt[d[:7]]
        hold = holdings(root, days, bd)
        ratios[root] = known_answer(root, days, bd, hold)
        held_of[root] = {}
        funds = list(FUNDS[root].items())
        mult = MULT[root]
        n_single_checked = n_stale = n_missing = 0
        skipped_no_f: list[str] = []
        for p, d in zip(days, days[1:]):
            if not (FIRST <= d <= LAST):
                continue
            comps = hold[d]
            held_of[root][d] = sorted({_ym_str(ym) for _w, lead, nxt, b in comps for ym, _q in legs(lead, nxt, b)})
            fund_in: list[dict[str, Any]] = []
            for f, L in funds:
                dates, vals = aum[f]
                i = bisect.bisect_left(dates, d) - 1
                if i < 0:
                    raise FlowPanelError(f"{f}: no NAV before {d}")
                fdates, fvals = fmap[f]
                j = bisect.bisect_left(fdates, d) - 1  # f_fut[t-1]: the latest value strictly before t
                if j < 0:
                    break  # the f_fut file starts 2017-05-22, so its first day has no f[t-1]; counted, not filled
                if fdates[j] != dates[i]:
                    raise FlowPanelError(f"{f} {d}: f_fut dated {fdates[j]} but AUM dated {dates[i]}")
                fe, fp, flo, fhi, method = fvals[j]
                sq = 0.0 if method == "proven" else (h if _quarter(fdates[j]) in disfav[f] else h / 1.645)
                fund_in.append({"fund": f, "L": L, "aum": vals[i], "navdate": dates[i], "f_est": fe, "f_pit": fp,
                                "f_lo": flo, "f_hi": fhi, "sigma_q": sq})
            if len(fund_in) < len(funds):
                skipped_no_f.append(d)
                continue
            for tau in TAUS:
                col = TAUS.index(tau)
                parts: list[tuple[float, Key, Key, float, float, float]] = []
                missing = stale = 0
                for w, lead, nxt, b in comps:
                    u_tau = u_prev = 0.0
                    for ym, q in legs(lead, nxt, b):
                        s = st[p][ym]
                        row = pxmap.get((root, d, _ym_str(ym)))
                        pt = float("nan") if row is None else row[col]
                        if row is None:  # the contract has no bar in any span that day (e.g. 2020-02-28, a vendor gap)
                            missing += 1
                        if not np.isfinite(pt):
                            stale += 1
                            pt = s
                        u_tau += q * pt
                        u_prev += q * s
                    parts.append((w, lead, nxt, b, u_tau, u_prev))
                # value weights at tau, then the day's held return
                vsum = sum(pt[0] for pt in parts)
                grown = [w / vsum * (u_tau / u_prev) for w, _l, _n, _b, u_tau, u_prev in parts]
                r = sum(grown) - 1.0 if len(parts) > 1 else held_return(parts[0][4], parts[0][5])
                wt = [g / sum(grown) for g in grown]
                # contracts per USD of notional, split across the held contracts; P_held is its reciprocal
                per_usd: dict[Key, float] = {}
                for (_w, lead, nxt, b, u_tau, _up), wi in zip(parts, wt):
                    for ym, q in legs(lead, nxt, b):
                        per_usd[ym] = per_usd.get(ym, 0.0) + wi / (mult * u_tau) * q
                k_usd = sum(per_usd.values())
                p_held = 1.0 / (mult * k_usd)
                rec: dict[str, Any] = {"root": root, "day": d, "prev": p, "tau": tau, "r_held": r,
                                       "R_day": ratios[root][d], "p_held": p_held, "n_comp": len(parts),
                                       "n_stale": stale, "price_missing": missing}
                for side, fi in (("long", [x for x in fund_in if x["L"] > 0][0]),
                                 ("inverse", [x for x in fund_in if x["L"] < 0][0])):
                    q1 = q1_notional(fi["aum"], fi["L"], r, 1.0) * k_usd
                    if len(parts) == 1:
                        ref = q1_rebalance(fi["aum"], fi["L"], r, 1.0, mult, parts[0][4])
                        if not math.isclose(q1, ref, rel_tol=1e-12, abs_tol=1e-9):
                            raise FlowPanelError(f"{root} {d} {tau} {fi['fund']}: Q {q1!r} != q1_rebalance {ref!r}")
                        n_single_checked += 1
                    if r != 0 and np.sign(q1) != np.sign(r):  # sign audit: L(L-1) > 0, so BOTH funds buy on r > 0
                        raise FlowPanelError(f"{root} {d} {tau} {fi['fund']}: Q {q1!r} against r {r!r}")
                    rec.update({f"{k}_{side}": fi[k] for k in ("aum", "navdate", "f_est", "f_pit", "f_lo", "f_hi",
                                                               "sigma_q")})
                    rec[f"c_{side}"] = fi["aum"] * fi["L"] * (fi["L"] - 1) * k_usd  # contracts per unit return, f = 1
                    rec[f"q1_{side}"] = q1
                for rd in ("est", "pit", "lo", "hi"):
                    rec[f"q_{rd}"] = rec[f"f_{rd}_long"] * rec["q1_long"] + rec[f"f_{rd}_inverse"] * rec["q1_inverse"]
                traded = max(per_usd, key=lambda k: per_usd[k])
                rec["traded_ym"], rec["traded_share"] = _ym_str(traded), per_usd[traded] / k_usd
                rec["held"] = ";".join(held_of[root][d])
                recs.append(rec)
                n_stale += stale
                n_missing += missing
                for ym in sorted(per_usd):
                    row = pxmap.get((root, d, _ym_str(ym)))
                    pt = float("nan") if row is None else row[col]
                    con_rows.append(f"{root},{d},{tau},{_ym_str(ym)},{pt!r},{st[p][ym]!r},{int(not np.isfinite(pt))},"
                                    f"{per_usd[ym] / k_usd!r}")
        summary["roots"][root] = {"business_days": sum(1 for d in days if FIRST <= d <= LAST),
                                  "known_answer_days": len(ratios[root]), "days_without_f_prev": skipped_no_f,
                                  "single_component_q_checked": n_single_checked,
                                  "stale_legs": n_stale, "legs_without_any_bar_that_day": n_missing,
                                  "funds": {f: L for f, L in funds}}
    df = gate(pd.DataFrame(recs), px, ratios, costs, summary)
    cols = ["root", "day", "prev", "tau", "r_held", "R_day", "p_held", "n_comp", "n_stale", "price_missing", "held",
            "traded_ym", "traded_share", "q_est", "q_pit", "q_lo", "q_hi"] + \
        [f"{k}_{s}" for s in ("long", "inverse") for k in ("aum", "navdate", "c", "q1", "f_est", "f_pit", "f_lo",
                                                            "f_hi", "sigma_q")] + \
        ["sigma_d", "sigma_rem_ret", "V_d", "sigma_Q", "snr", "I", "rt_cost", "gate_pass", "is_tau_star", "signal_day"]
    buf = io.StringIO()
    df[cols].to_csv(buf, index=False, lineterminator="\n", float_format="%.17g", encoding="utf-8")
    return _gz(buf.getvalue()), _gz("\n".join(con_rows) + "\n"), json.dumps(summary, indent=1, sort_keys=True) + "\n"


def gate(df: pd.DataFrame, px: pd.DataFrame, ratios: dict[str, dict[str, float]], costs: dict[str, dict[str, Any]],
         summary: dict[str, Any]) -> pd.DataFrame:
    """§7.2 at every τ, and the earliest-pass τ* per day (§7.1: 13:50, else 14:00, else 14:10; 14:10 on a day with
    no signal, A8). Every window is the N_TRAIL business days BEFORE t."""
    out = []
    for root, g in df.groupby("root", sort=True):
        days = sorted(ratios[root])  # every business day since 2010 with a checked ratio
        R = pd.Series({d: ratios[root][d] - 1.0 for d in days})
        sig_d = R.rolling(N_TRAIL, min_periods=N_TRAIL).std(ddof=1).shift(1)  # σ_d: days t-20 .. t-1
        # V_d: the mean whole-session volume of each held contract over t-20 .. t-1 (no row that day = 0 traded)
        v = px[px["root"] == root].pivot_table(index="day", columns="ym", values="vol_ses", aggfunc="sum")
        bdays = [d for d in days if d >= v.index.min()]
        v = v.reindex(bdays).fillna(0.0)
        vbar = v.rolling(N_TRAIL, min_periods=N_TRAIL).mean().shift(1)
        parts = []
        for tau, gt in g.groupby("tau", sort=True):
            gt = gt.sort_values("day").copy()
            ok = gt["n_stale"] == 0
            rem = pd.Series(np.where(ok, gt["R_day"] / (1.0 + gt["r_held"]) - 1.0, np.nan), index=gt["day"].to_numpy())
            rem = rem.reindex(bdays)
            s_rem = rem.rolling(N_TRAIL, min_periods=N_REM_MIN).std(ddof=1).shift(1)
            gt["sigma_d"] = sig_d.reindex(gt["day"]).to_numpy()
            gt["sigma_rem_ret"] = s_rem.reindex(gt["day"]).to_numpy()
            vd = []
            for d, h in zip(gt["day"], gt["held"]):
                if d not in vbar.index:
                    vd.append(np.nan)
                    continue
                # a held contract with no bar in the whole panel traded 0; NaN only in the 20-day warm-up
                x = vbar.loc[d].reindex(h.split(";"), fill_value=0.0)
                vd.append(float(x.sum()) if x.notna().all() else np.nan)
            gt["V_d"] = vd
            var = np.zeros(len(gt))
            for s in ("long", "inverse"):
                var = var + (gt[f"c_{s}"] * gt[f"f_est_{s}"]) ** 2 * gt["sigma_rem_ret"] ** 2 \
                    + (gt[f"c_{s}"] * gt["r_held"]) ** 2 * gt[f"sigma_q_{s}"] ** 2  # A5
            gt["sigma_Q"] = np.sqrt(var)
            gt["snr"] = gt["q_est"].abs() / gt["sigma_Q"]
            gt["I"] = Y * gt["sigma_d"] * np.sqrt(gt["q_est"].abs() / gt["V_d"]) * gt["p_held"] * np.sign(gt["q_est"])
            gt["rt_cost"] = costs[root]["price_units"]
            ready = gt[["sigma_d", "sigma_rem_ret", "V_d"]].notna().all(axis=1) & (gt["n_stale"] == 0)
            passed = ready & (gt["I"].abs() >= K_COST * gt["rt_cost"]) & (gt["snr"] >= SNR_MIN)
            gt["gate_pass"] = np.where(ready, passed.astype(int), -1)  # -1: the gate cannot be evaluated
            parts.append(gt)
        gg = pd.concat(parts)
        # τ*: the first of 13:50/14:00/14:10 that passes, else 14:10; only where all three are evaluable
        cand = gg[gg["tau"].isin(CANDIDATES)].pivot(index="day", columns="tau", values="gate_pass")
        evaluable = (cand[list(CANDIDATES)] >= 0).all(axis=1)
        star = {}
        for d, row in cand[evaluable].iterrows():
            first = next((t for t in CANDIDATES if row[t] == 1), None)
            star[d] = (first or CANDIDATES[-1], int(first is not None))
        gg["is_tau_star"] = [int(d in star and star[d][0] == t) for d, t in zip(gg["day"], gg["tau"])]
        gg["signal_day"] = [star[d][1] if d in star else -1 for d in gg["day"]]
        n_ev = len(star)
        n_sig = sum(v[1] for v in star.values())
        by_tau = {t: sum(1 for v in star.values() if v[0] == t and v[1] == 1) for t in CANDIDATES}
        summary["roots"][root]["tau_star"] = {"evaluable_days": n_ev, "signal_days": n_sig,
                                              "first_pass_at": by_tau, "no_signal_days_scored_at_14:10": n_ev - n_sig}
        out.append(gg)
    return pd.concat(out).sort_values(["root", "day", "tau"]).reset_index(drop=True)


def _gz(text: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as z:
        z.write(text.encode("utf-8"))
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    day_b, con_b, summ = build()
    if a.check:
        for path, new in ((OUT_DAY, day_b), (OUT_CON, con_b)):
            if path.read_bytes() != new:
                raise FlowPanelError(f"{path.name} does not reproduce")
        if OUT_SUM.read_text(encoding="utf-8") != summ:
            raise FlowPanelError(f"{OUT_SUM.name} does not reproduce")
        print("[check] all three outputs reproduce byte for byte")
        return 0
    OUT_DAY.write_bytes(day_b)
    OUT_CON.write_bytes(con_b)
    OUT_SUM.write_text(summ, encoding="utf-8", newline="\n")
    print(summ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
