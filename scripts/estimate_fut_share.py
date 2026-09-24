"""Estimate each fund's daily futures share f_fut, with a band, where the swap split is not proven (AITODO 1c, 1d, 1e).

SPEC -- written 2026-09-24 before any estimate was compared with anything, and frozen from then on.

WHY. The principal, 2026-09-24: an estimate is acceptable if it is directionally correct. The
predicted flow's SIGN never depends on f_fut in [0, 1]: L(L-1) is positive for L = +2 and for
L = -2, and f_fut only scales the size. So the estimate is about magnitude, and it carries a band.

KNOWN EXACTLY: total exposure = L x AUM every day (BOIL's 2023 swap quarter-ends reproduce it to
0.99999-1.0002); f_fut at every quarter-end (D620); each quarter's total swap gain or loss (the
statements of operations, `data/ledger_swap_free_quarters.json`, ProShares funds only).

PER FUND AND DAY, 2017-05-22 → 2023-12-29, one row with `method`:
  * `proven`: the quarter is FUTURES_ONLY_PROVEN (`ledger_swap_free_quarters.json`), so f = 1
    and the band is [1, 1]. That covers BOIL outside 2023, all of KOLD, and SCO from 2020-Q4.
  * `interpolated`: linear in calendar days between the two bounding quarter-end values a and b.
    The band is [min(a,b) - h, max(a,b) + h] clipped to [0, 1], where h is the pooled
    leave-one-out p90 defined below.
  * `carried`: after the last quarter-end filed before 2024-01-01, which is 2023-09-30. The
    2023-12-31 schedules were filed in 2024, past the seal, and are not read. f = the last value
    and the band is [f - h, f + h].
  * A quarter-end's value is its parsed f_fut. Where that is null (the USCF filings before ~2016
    printed no notional), a quarter-end with futures lines and NO swap line has f = 1 by
    definition.
  * UNG and USO quarters are never `proven`: their USCF statements of operations are not parsed
    yet (AITODO 1e). Days between two quarter-ends at 1.0 read `interpolated` with band
    [1 - h, 1]. [SUPERSEDED by POST HOC 1e below: the statements are parsed now.]

h: predict every quarter-end that has a swap line, or sits next to one, from the average of its
two neighbours. h is the p90 of |error| pooled across UCO, SCO, BOIL, UNG and USO, over
quarter-ends up to 2023-09-30. (Measured before this spec on the individual funds: p90
0.07-0.17.)

POINT-IN-TIME. The interpolation uses the NEXT quarter-end, which was published 40-90 days
later. The quantity estimated was itself public daily at the time (ProShares' daily-holdings
pages are archived from 2011), so the estimate targets information a participant had. But the
estimate is not point-in-time. `f_pit`, the value at the latest quarter-end FILED on or before
the day, is written beside it, and the mean |f_est - f_pit| is reported per fund.

THE CHECK: THE SWAP P&L (BOIL, UCO, SCO; each SWAPS_HELD quarter up to 2023-Q3). The implied
quarter P&L is
    implied = sum_d (1 - f_{d-1}) * L * AUM_{d-1} * R_d
where R_d, the index return, comes from the fund's own NAV:
    R_d = (NAV_d / NAV_{d-1} - 1 - D (y/360 - ER/365)) / L
(Gate 0b's accrual; the swap pays the same index). The reported P&L is realized plus the change
in unrealized. The mismatch gives a LOWER BOUND on the worst daily share error in the quarter:
    max_d |e_d| >= |reported - implied| / sum_d |L * AUM_{d-1} * R_d|.
  * If that bound exceeds h, the linear path is inconsistent with the audited P&L. For that
    quarter the estimate switches to the one-step path (a until day tau, b after) whose implied
    P&L is closest to the reported one, and the band widens to cover both paths.
  * Swap financing (a few bp a year) is not modelled; its size is reported beside each quarter.
UNG and USO get no P&L check yet, because the USCF statement parser does not exist. [SUPERSEDED:
see POST HOC 1e.]

POST HOC, 1e (2026-09-24): the USCF statements are now parsed (`prove_swap_free_quarters.py`).
  * UNG is futures-only PROVEN 2016-Q1 → 2022-Q4 and USO 2016-Q1 → 2021-Q4. Those days are
    `proven`.
  * USO 2022-Q1 held swaps only INSIDE the quarter: none at either quarter-end, yet $31.5M of swap
    P&L. Interpolating between two 1.0 anchors would call it all futures.
  * For a USCF quarter whose futures and swap P&L share a sign, F / (F + S) is the P&L-weighted
    average futures share (both legs earn the same returns). Where both anchors are 1.0, that
    ratio becomes the quarter's estimate (`pl_ratio_intra_quarter`, band [f - h, 1]).
  * Elsewhere it is reported against the linear path's mean f as the USCF version of the P&L
    check (`uscf_pl_ratio_checks`). Its caveat: USO's futures span several months while a swap
    may reference fewer, so the "same returns" premise holds only approximately.

POST HOC (after the first run, 2026-09-24; the estimate itself is unchanged). The lower bound
divides by the gross P&L of the whole book, so in a violent quarter it cannot fire. BOIL 2023-Q1
reported ~$0 of swap P&L against the linear path's -$37M, and the bound read 0.007. Each check
therefore also reports the constant shift c in f that would reproduce the reported P&L. A
quarter with |c| > h, or c undefined, is listed as DISFAVOURED. The ledger uses the band edges
there, never the point estimate alone.

WHAT THIS DOES NOT TOUCH. Every panel is read through `load_panel(reserved_from="2024-01-01")`, and
only swap P&L quarters up to 2023-Q3 are used. It computes no strategy return and no flow or
window statistic. It writes two new files: `data/ledger_fut_share_daily.csv.gz` (rows, gitignored
by suffix) and `data/ledger_fut_share_summary.json` (tracked).

    uv run python scripts/estimate_fut_share.py            # write both
    uv run python scripts/estimate_fut_share.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import gzip
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT_ROWS = REPO / "data" / "ledger_fut_share_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_fut_share_summary.json"
SWAPQ = REPO / "data" / "ledger_swap_free_quarters.json"
RESERVED_FROM = "2024-01-01"
FIRST, LAST = "2017-05-22", "2023-12-29"
LAST_ANCHOR = "2023-09-30"
L_OF = {"BOIL": 2, "KOLD": -2, "UCO": 2, "SCO": -2, "UNG": 1, "USO": 1}
ER = {"BOIL": 0.0095, "KOLD": 0.0095, "UCO": 0.0095, "SCO": 0.0095}
PL_FUNDS = ("BOIL", "UCO", "SCO")
USCF_FUNDS = ("UNG", "USO")
BAND_FUNDS = ("UCO", "SCO", "BOIL", "UNG", "USO")


class ShareError(RuntimeError):
    pass


def _gate0b() -> Any:
    spec = importlib.util.spec_from_file_location("gate_0b_ng_nav", REPO / "scripts" / "gate_0b_ng_nav.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules["gate_0b_ng_nav"] = m
    spec.loader.exec_module(m)
    return m


G = _gate0b()


def quarter_of(day: str) -> str:
    return f"{day[:4]}-Q{(int(day[5:7]) - 1) // 3 + 1}"


def anchors() -> dict[str, list[tuple[str, float, str]]]:
    """fund -> [(period_end, f, filed_date)], first publication of each quarter-end, filed before the seal."""
    h = G.load_panel("fund_holdings_quarterly", reserved_from=RESERVED_FROM).frame
    out: dict[str, list[tuple[str, float, str]]] = {}
    for fund in L_OF:
        g = h[(h["fund"] == fund) & (h["period_end"].astype(str) >= "2016-12-31")].sort_values(["period_end", "filed_date"])
        rows = []
        for pe, x in g.groupby("period_end"):
            first = x[x["source_accession"] == x["source_accession"].iloc[0]]
            n_fut = int((first["kind"] == "futures").sum())
            n_swap = int((first["kind"] == "swap").sum())
            ff = first["f_fut"].dropna()
            if len(ff):
                f = float(ff.iloc[0])
            elif n_fut > 0 and n_swap == 0:
                f = 1.0
            else:
                continue
            rows.append((str(pe), f, str(first["filed_date"].iloc[0])))
        out[fund] = rows
    return out


def pooled_h(anc: dict[str, list[tuple[str, float, str]]]) -> tuple[float, int]:
    errs = []
    for fund in BAND_FUNDS:
        v = [(pe, f) for pe, f, _ in anc[fund] if pe <= LAST_ANCHOR]
        for (_p0, a), (_p1, f), (_p2, b) in zip(v, v[1:], v[2:]):
            if min(a, f, b) < 1.0:  # a swap line at, or next to, this quarter-end
                errs.append(abs(f - (a + b) / 2))
    return float(np.quantile(errs, 0.9)), len(errs)


def swap_quarters() -> dict[str, dict[str, dict[str, Any]]]:
    d = json.loads(SWAPQ.read_text(encoding="utf-8"))["funds"]
    return {f: {q: v for q, v in d[f]["quarters"].items() if q <= "2023-Q3"} for f in d}


def calendars() -> tuple[Any, dict[str, list[str]]]:
    nav = G.load_panel("fund_nav_daily", reserved_from=RESERVED_FROM, usecols=["date", "fund", "nav", "aum"]).frame
    nav["date"] = nav["date"].astype(str)
    _nav, settles, _reads = G.load_inputs()
    ng_days = [d for d in sorted(settles) if d not in set(G.copy_days(settles))]
    cal = {f: sorted(nav[nav["fund"] == f]["date"]) for f in ("BOIL", "KOLD", "UCO", "SCO")}
    cal["UNG"] = ng_days
    cal["USO"] = ng_days  # the NYMEX calendar; CL and NG share it apart from holiday republications
    return nav, cal


def path_value(day: str, anc: list[tuple[str, float, str]]) -> tuple[float, float, float, str, str]:
    """(f, a, b, prev_pe, next_pe) by linear interpolation in calendar days; carried after LAST_ANCHOR."""
    pes = [pe for pe, _f, _fd in anc if pe <= LAST_ANCHOR]
    fs = {pe: f for pe, f, _fd in anc}
    i = bisect.bisect_left(pes, day)
    if i == 0:
        raise ShareError(f"{day} precedes the first anchor")
    p0 = pes[i - 1]
    if i == len(pes):
        return fs[p0], fs[p0], fs[p0], p0, ""
    p1 = pes[i]
    a, b = fs[p0], fs[p1]
    t0, t1, t = (dt.date.fromisoformat(x) for x in (p0, p1, day))
    w = (t - t0).days / (t1 - t0).days
    return a + w * (b - a), a, b, p0, p1


def build() -> tuple[str, dict[str, Any]]:
    anc = anchors()
    h, n_h = pooled_h(anc)
    swq = swap_quarters()
    nav, cal = calendars()
    rates = G.load_rates()

    rows: list[str] = ["fund,date,f_est,f_lo,f_hi,f_pit,method,anchor_prev,anchor_next"]
    summary: dict[str, Any] = {"h_pooled_p90": round(h, 6), "h_n": n_h, "funds": {}}
    for fund in L_OF:
        L = L_OF[fund]
        a_list = anc[fund]
        filed = sorted((fd, f) for _pe, f, fd in a_list)
        # the P&L check first: it can switch a quarter to its one-step path
        overrides: dict[str, tuple[str, float, float]] = {}  # quarter -> (tau, a, b)
        checks: list[dict[str, Any]] = []
        ratio_checks: list[dict[str, Any]] = []
        if fund in PL_FUNDS:
            g = nav[nav["fund"] == fund].sort_values("date")
            dates, navs, aums = list(g["date"]), [float(x) for x in g["nav"]], [float(x) for x in g["aum"]]
            for q, v in sorted(swq.get(fund, {}).items()):
                if v["verdict"] != "SWAPS_HELD" or q < "2017-Q2":
                    continue
                y, n = int(q[:4]), int(q[-1])
                qs = {1: f"{y - 1}-12-31", 2: f"{y}-03-31", 3: f"{y}-06-30", 4: f"{y}-09-30"}[n]
                qe = {1: f"{y}-03-31", 2: f"{y}-06-30", 3: f"{y}-09-30", 4: f"{y}-12-31"}[n]
                idx = [i for i in range(1, len(dates)) if qs < dates[i] <= qe]
                X, fprev = [], []
                for i in idx:
                    D = (dt.date.fromisoformat(dates[i]) - dt.date.fromisoformat(dates[i - 1])).days
                    yv = rates[G._month_minus(dates[i][:7], 2)]
                    R = (navs[i] / navs[i - 1] - 1 - D * (yv / 360 - ER[fund] / 365)) / L
                    X.append(L * aums[i - 1] * R)
                    fprev.append(path_value(max(dates[i - 1], qs), a_list)[0])  # f held over day i
                Xa = np.array(X)
                reported = float(v["swap_realized_usd"]) + float(v["swap_unrealized_change_usd"])
                lin = float(np.sum((1 - np.array(fprev)) * Xa))
                fsd = {pe: f for pe, f, _ in a_list}
                a, b = fsd[qs], fsd[qe]
                taus = []
                for k in range(len(idx) + 1):  # a on the first k days, b after
                    fk = np.array([a] * k + [b] * (len(idx) - k))
                    taus.append((abs(float(np.sum((1 - fk) * Xa)) - reported), k, float(np.sum((1 - fk) * Xa))))
                best = min(taus)
                gross = float(np.sum(np.abs(Xa)))
                bound = abs(reported - lin) / gross if gross else float("nan")
                c = {"quarter": q, "reported_usd": round(reported), "implied_linear_usd": round(lin),
                     "implied_all_a_usd": round(taus[-1][2]), "implied_all_b_usd": round(taus[0][2]),
                     "gross_exposure_pnl_usd": round(gross), "lower_bound_worst_share_error": round(bound, 4),
                     "financing_scale_usd_at_30bp_a_year": round(abs(1 - (a + b) / 2) * float(np.mean(np.abs(aums[idx[0] - 1: idx[-1]]))) * abs(L) * 0.003 / 4),
                     "consistent": bool(bound <= h)}
                # POST HOC (added after the first run showed the bound is weak in violent quarters):
                # the constant shift c in f that makes the linear path reproduce the reported P&L,
                # sum((1 - f - c) X) = reported. Undefined when sum(X) is small against the gap.
                net = float(np.sum(Xa))
                shift = round((lin - reported) / net, 4) if abs(net) > 1e-9 else None
                c["post_hoc_shift_to_match"] = shift
                c["post_hoc_reported_within_step_family"] = bool(
                    min(t[2] for t in taus) <= reported <= max(t[2] for t in taus))
                c["post_hoc_disfavoured"] = bool(shift is None or abs(shift) > h)
                if not c["consistent"]:
                    k = best[1]
                    c["switched_to_step"] = {"tau_first_b_day": dates[idx[k]] if k < len(idx) else None,
                                             "implied_usd": round(best[2])}
                    overrides[q] = (dates[idx[k]] if k < len(idx) else "9999-12-31", a, b)
                checks.append(c)

        proven_q = {q for q, v in swq.get(fund, {}).items() if v["verdict"] == "FUTURES_ONLY_PROVEN"}
        # USCF (post hoc, AITODO 1e): the audited futures/swap P&L split sizes the quarter's average share
        ratio_q: dict[str, float] = {}
        if fund in USCF_FUNDS:
            fsd = {pe: f for pe, f, _ in a_list}
            for q, v in sorted(swq.get(fund, {}).items()):
                if v["verdict"] != "SWAPS_HELD" or v.get("futures_pl_usd") is None or v["swap_realized_usd"] is None:
                    continue
                F = float(v["futures_pl_usd"])
                S = float(v["swap_realized_usd"]) + float(v["swap_unrealized_change_usd"])
                if F * S <= 0:  # opposite signs: the ratio is not a share
                    continue
                f_ratio = F / (F + S)
                y, n = int(q[:4]), int(q[-1])
                qs = {1: f"{y - 1}-12-31", 2: f"{y}-03-31", 3: f"{y}-06-30", 4: f"{y}-09-30"}[n]
                qe = {1: f"{y}-03-31", 2: f"{y}-06-30", 3: f"{y}-09-30", 4: f"{y}-12-31"}[n]
                fa, fb = fsd.get(qs), fsd.get(qe)
                lin_mean = None if fa is None or fb is None else (fa + fb) / 2
                c = {"quarter": q, "futures_pl_usd": F, "swap_pl_usd": S, "f_from_pl_ratio": round(f_ratio, 4),
                     "linear_mean_f": None if lin_mean is None else round(lin_mean, 4),
                     "gap": None if lin_mean is None else round(f_ratio - lin_mean, 4),
                     "within_h": None if lin_mean is None else bool(abs(f_ratio - lin_mean) <= h),
                     "intra_quarter_only": bool(fa == 1.0 and fb == 1.0)}
                ratio_checks.append(c)
                if c["intra_quarter_only"]:
                    ratio_q[q] = f_ratio
        est_days, diffs = 0, []
        for d in cal[fund]:
            if not (FIRST <= d <= LAST):
                continue
            q = quarter_of(d)
            fd_i = bisect.bisect_right([x[0] for x in filed], d) - 1
            f_pit = filed[fd_i][1] if fd_i >= 0 else float("nan")
            if q in proven_q:
                rows.append(f"{fund},{d},1.0,1.0,1.0,{f_pit!r},proven,,")
                continue
            f, a, b, p0, p1 = path_value(d, a_list)
            if q in ratio_q:
                f = ratio_q[q]
                lo, hi, method = max(0.0, f - h), 1.0, "pl_ratio_intra_quarter"
            elif not p1:
                lo, hi, method = max(0.0, f - h), min(1.0, f + h), "carried"
            elif q in overrides:
                tau, oa, ob = overrides[q]
                f_step = oa if d < tau else ob
                lo, hi = max(0.0, min(oa, ob, f) - h), min(1.0, max(oa, ob, f) + h)
                f, method = f_step, "pl_step"
            else:
                lo, hi, method = max(0.0, min(a, b) - h), min(1.0, max(a, b) + h), "interpolated"
            est_days += 1
            diffs.append(abs(f - f_pit))
            rows.append(f"{fund},{d},{f!r},{lo!r},{hi!r},{f_pit!r},{method},{p0},{p1}")
        summary["funds"][fund] = {
            "L": L, "estimated_days": est_days,
            "mean_abs_est_minus_pit": round(float(np.mean(diffs)), 6) if diffs else None,
            "pl_checks": checks,
            "pl_consistent": sum(c["consistent"] for c in checks), "pl_checked": len(checks),
            "post_hoc_disfavoured_quarters": [c["quarter"] for c in checks if c["post_hoc_disfavoured"]],
            "uscf_pl_ratio_checks": ratio_checks,
        }
    return "\n".join(rows) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text, summary = build()
    stext = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    if a.check:
        with gzip.open(OUT_ROWS, "rt", encoding="utf-8", newline="") as fh:
            if fh.read() != text:
                raise ShareError(f"{OUT_ROWS.name} does not reproduce")
        if OUT_SUM.read_text(encoding="utf-8") != stext:
            raise ShareError(f"{OUT_SUM.name} does not reproduce")
        print("[check] both outputs reproduce byte for byte")
        return 0
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(text.encode("utf-8"))
    OUT_ROWS.write_bytes(buf.getvalue())
    OUT_SUM.write_text(stext, encoding="utf-8", newline="\n")
    print(f"h (pooled leave-one-out p90) = {summary['h_pooled_p90']} over {summary['h_n']} quarter-ends")
    for fund, s in summary["funds"].items():
        print(f"{fund}: estimated days {s['estimated_days']}; mean |est - pit| {s['mean_abs_est_minus_pit']};"
              f" P&L consistent {s['pl_consistent']}/{s['pl_checked']}")
        for c in s["pl_checks"]:
            print(f"   {c['quarter']} reported {c['reported_usd']:>14,} linear {c['implied_linear_usd']:>14,}"
                  f" [all-a {c['implied_all_a_usd']:>14,} all-b {c['implied_all_b_usd']:>14,}]"
                  f" bound {c['lower_bound_worst_share_error']:.3f} {'ok' if c['consistent'] else 'STEP ' + str(c.get('switched_to_step'))}"
                  f" | post-hoc shift {c['post_hoc_shift_to_match']} {'DISFAVOURED' if c['post_hoc_disfavoured'] else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
