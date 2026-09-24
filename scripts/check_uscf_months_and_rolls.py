"""UNG and USO: held months at every quarter-end, and the roll days, against the funds' own documented rule (AITODO 1e).

SPEC -- written 2026-09-24 before any held month or return was compared, and frozen from then on.

THE RULE, quoted from UNG's and USO's 10-Ks (UNG every year; USO through its 2019 10-K): the
Benchmark Futures Contract is "the near month contract to expire, except when the near month
contract is within two weeks of expiration, in which case it will be measured by the futures
contract that is the next month contract to expire". It "is changed from the near month contract
to the next month contract over a four-day period ... starting at the end of the day on the date
two weeks prior to expiration of the near month contract ... day 1 consists of 75% of the then
near month contract's price plus 25% of the price of the next month contract, divided by 75% of
the near month contract's prior day's price plus 25% of the next month contract's prior day's
price", then 50/50 and 25/75, and on day 4 the next month contract. USO changed this in May 2020 to
a ten-day roll of a multi-month portfolio whose weights appear only on its website. USO is
therefore tested only through 2020-03-31, and later quarter-ends are reported, not scored.

Made precise, before looking:
  * E, the near contract's last trading day. NG: three business days before the first calendar
    day of the delivery month. CL: three business days before the 25th calendar day of the month
    before delivery, or four if the 25th is not a business day.
  * D0 = E - 14 calendar days, or the last business day on or before that. Days 1-4 are the four
    business days after D0. The return on day k (k = 1, 2, 3) uses weights (1 - k/4, k/4) on
    (near, next) for both today's and yesterday's settlements. From day 4 the return is the next
    contract's.
  * Business days: settlement days of the root, minus holiday republications (Gate 0b's rule),
    plus `data/ledger_settle_holes_2020.csv`.

PART 1, HELD MONTHS: at every quarter-end (after the roll), the fund holds exactly the benchmark
contract. For UNG that is 2017-03-31 → 2023-09-30; for USO, 2017-03-31 → 2020-03-31. Evidence:
D620's `fund_holdings_quarterly`, first publication. Control: the rule shifted to the contract one
month later must fail.

PART 2, ROLL DAYS. There is no UNG or USO NAV on disk (AITODO item 5). The test is therefore made
on MARKET closes (the Alpha Vantage daily-adjusted cache,
`data/raw/alphavantage/daily_adjusted_etf/{UNG,USO}.json.gz`, cut to dates before 2024-01-01 at
load). The market close is at 4:00 p.m. while the settlement is at 2:30 p.m., and a premium
exists, so this cannot be a 5 bp gate. It is a schedule identification: err_t = r_etf,t -
r_bench,t with L = +1.
  * Declared schedules: the documented one; its 4-day window shifted by s in {-3, -2, -1, +1, +2,
    +3} business days; and single-day rolls at the close of day j in {0, 1, 2, 3} relative to D0.
  * Scored on roll-window days: the business days from D0-3 to D0+8, where some declared schedule
    differs from another.
  * IDENTIFIED if the documented schedule has the lowest mean |err| on roll-window days AND, month
    by month, beats the best alternative in more roll months than it loses (a one-sided sign
    test, p < 0.05).
  * Window: UNG 2017-05-22 → 2023-12-29; USO 2017-05-22 → 2020-03-31.
  * Control that must fire: the documented schedule applied to the WRONG pair (next → the month
    after) must score a higher mean |err| than the documented pair.

PART 3, THE OFFICIAL ROLL CALENDAR. Added 2026-09-24, after Part 2 returned "not identified" and
BEFORE any date below was compared. USCF publishes each year's roll dates as a CSV
(`https://secure.alpsinc.com/MarketingAPI/api/v1/Content/uscfinvestments/uscf-rolldates-commodities-{YYYY}.csv`,
2020-2026, cached under `data/raw/uscf/`, gitignored). Each row gives a fund's "Roll Begin" and
"Roll End" trade dates. The prediction, for every month of 2020-2023:
  * UNG, and USO through April 2020: Roll Begin = D0 and Roll End = the third business day after
    D0. Those are the four closes at which 25% moves, whose returns are days 1-4 of Part 2's rule.
  * USO from May 2020 (its 2023 10-K: "over a ten-day period beginning on the first business day
    of each month"): Roll Begin = business day 1 and Roll End = business day 10, on the CL
    calendar.
PROVEN if every month matches exactly. Every mismatch is listed with both dates.

WHAT THIS DOES NOT TOUCH: it reads holdings, NG/CL settlements and UNG/USO market closes, all dated
before 2024-01-01. It computes no strategy return and no settlement-window statistic, and writes
`data/ledger_uscf_months_rolls_check.json`.

    uv run python scripts/check_uscf_months_and_rolls.py            # write the JSON
    uv run python scripts/check_uscf_months_and_rolls.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import gzip
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_uscf_months_rolls_check.json"
AV = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted_etf"
HOLES = REPO / "data" / "ledger_settle_holes_2020.csv"
RESERVED_FROM = "2024-01-01"
ROOT_OF = {"UNG": "NG", "USO": "CL"}
WINDOW = {"UNG": ("2017-05-22", "2023-12-29"), "USO": ("2017-05-22", "2020-03-31")}
QE_LAST = {"UNG": "2023-09-30", "USO": "2020-03-31"}
Key = tuple[int, int]


class UscfError(RuntimeError):
    pass


def _load_mod(name: str, rel: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G = _load_mod("gate_0b_ng_nav", "scripts/gate_0b_ng_nav.py")
GCL = _load_mod("gate_0b_cl_nav", "scripts/gate_0b_cl_nav.py")


def settlements(root: str) -> dict[str, dict[Key, float]]:
    if root == "NG":
        _nav, st, _r = G.load_inputs()
        with HOLES.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["root"] == "NG":
                    ym = G._ym(r["contract"], r["ref"])
                    st.setdefault(r["ref"], {})[ym] = float(r["settle"])
    else:
        _nav, st, _r = GCL.load()
    copies = set(G.copy_days(st))
    return {d: v for d, v in st.items() if d not in copies}


def _add(y: int, m: int) -> Key:
    return (y + (m - 1) // 12, (m - 1) % 12 + 1)


def last_trade(root: str, ym: Key, bdays: list[str]) -> str:
    y, m = ym
    if root == "NG":
        i = bisect.bisect_left(bdays, f"{y:04d}-{m:02d}-01")
        return bdays[i - 3]
    py, pm = _add(y, m - 1)
    d25 = f"{py:04d}-{pm:02d}-25"
    i = bisect.bisect_left(bdays, d25)
    return bdays[i - 3] if (i < len(bdays) and bdays[i] == d25) else bdays[i - 4]


def roll_calendar(root: str, bdays: list[str]) -> list[dict[str, Any]]:
    """One entry per near contract: (near, next, E, D0 index in bdays)."""
    out = []
    first, last = bdays[0], bdays[-1]
    y, m = int(first[:4]), int(first[5:7])
    while True:
        near = _add(y, m + 1)
        # E is computable while the delivery month starts within a week of the calendar's end
        # (deviation, 2026-09-24: the first run stopped one contract early and missed Dec 2023's roll)
        start = dt.date(near[0], near[1], 1)
        E = last_trade(root, near, bdays) if start <= dt.date.fromisoformat(last) + dt.timedelta(days=7) else None
        if E is None or E > last:
            break
        d0_cal = (dt.date.fromisoformat(E) - dt.timedelta(days=14)).isoformat()
        i0 = bisect.bisect_right(bdays, d0_cal) - 1
        out.append({"near": near, "next": _add(near[0], near[1] + 1), "E": E, "D0": bdays[i0], "i0": i0})
        y, m = _add(y, m + 1)
    return out


def near_on(day: str, rolls: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
    """The roll entry whose near contract is the benchmark's near contract on `day`, and day's offset from D0."""
    for r in rolls:
        if day <= r["E"]:
            return r, 0
    raise UscfError(f"no roll entry covers {day}")


def weight_fn(kind: str, param: int) -> Any:
    """Next-contract weight for the return on business day offset o = index(day) - i0."""
    if kind == "doc":
        return lambda o: min(max((o - param) / 4.0, 0.0), 1.0)  # param = shift; o=1 -> 0.25 ... o=4 -> 1
    return lambda o: 1.0 if o >= param + 1 else 0.0  # single-day roll at the close of day `param`


SCHEDULES = {"documented": ("doc", 0)}
for _s in (-3, -2, -1, 1, 2, 3):
    SCHEDULES[f"documented shifted {_s:+d}"] = ("doc", _s)
for _j in (0, 1, 2, 3):
    SCHEDULES[f"single day at close of D0+{_j}"] = ("one", _j)


def bench_returns(bdays: list[str], st: dict[str, dict[Key, float]], rolls: list[dict[str, Any]],
                  w: Any, *, wrong_pair: bool = False) -> dict[str, float | None]:
    """Benchmark return per business day: during a roll month's window the (near, next) mix, else the near."""
    out: dict[str, float | None] = {}
    ri = 0
    for i in range(1, len(bdays)):
        d, p = bdays[i], bdays[i - 1]
        while ri < len(rolls) and rolls[ri]["E"] < d:
            ri += 1  # roll entry whose near contract has not expired by d
        if ri >= len(rolls):
            break
        r = rolls[ri]
        near, nxt = r["near"], r["next"]
        if wrong_pair:
            near, nxt = nxt, _add(nxt[0], nxt[1] + 1)
        b = w(i - r["i0"])
        # after day 4 the benchmark is the next contract until this near contract expires
        try:
            num = (1 - b) * st[d][near] + b * st[d][nxt] if b < 1 else st[d][nxt]
            den = (1 - b) * st[p][near] + b * st[p][nxt] if b < 1 else st[p][nxt]
            if b == 0:
                num, den = st[d][near], st[p][near]
            out[d] = num / den
        except KeyError:
            out[d] = None
    return out


def etf_closes(fund: str) -> dict[str, float]:
    with gzip.open(AV / f"{fund}.json.gz", "rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    out = {d: float(v["5. adjusted close"]) for d, v in raw.items() if d < RESERVED_FROM}
    if any(d >= RESERVED_FROM for d in out):
        raise UscfError("a market close on or after the seal is in memory")
    return out


def held_months(fund: str, rolls: list[dict[str, Any]]) -> dict[str, Any]:
    h = G.load_panel("fund_holdings_quarterly", reserved_from=RESERVED_FROM).frame
    g = h[(h["fund"] == fund) & (h["period_end"].astype(str) >= "2017-03-31")].sort_values(["period_end", "filed_date"])
    rows = []
    for pe, x in g.groupby("period_end"):
        first = x[x["source_accession"] == x["source_accession"].iloc[0]]
        fut = first[first["kind"] == "futures"]
        months = sorted(set(fut["contract_month"].dropna().astype(str)))
        r, _ = near_on(str(pe), rolls)
        # the position after the close of day 3 is all next contract
        pred = r["next"] if str(pe) >= _nth_after(r, 3) else r["near"]  # fully rolled from the close of day 3
        pred_s = f"{pred[0]:04d}-{pred[1]:02d}"
        wrong = _add(pred[0], pred[1] + 1)
        rows.append({"period_end": str(pe), "held": months, "predicted": [pred_s],
                     "scored": str(pe) <= QE_LAST[fund], "match": months == [pred_s],
                     "control_match": months == [f"{wrong[0]:04d}-{wrong[1]:02d}"]})
    scored = [r for r in rows if r["scored"]]
    if any(r["control_match"] for r in scored) and all(r["control_match"] for r in scored):
        raise UscfError(f"{fund}: the one-month-later control matches every quarter-end")
    return {"scored": len(scored), "matched": sum(r["match"] for r in scored),
            "mismatched": [r for r in scored if not r["match"]],
            "control_matches": sum(r["control_match"] for r in scored),
            "unscored_after_rule_change": [r for r in rows if not r["scored"]]}


_BDAYS: list[str] = []


def _nth_after(r: dict[str, Any], n: int) -> str:
    return _BDAYS[min(r["i0"] + n, len(_BDAYS) - 1)]


def roll_days(fund: str, bdays: list[str], st: dict[str, dict[Key, float]], rolls: list[dict[str, Any]]) -> dict[str, Any]:
    lo, hi = WINDOW[fund]
    px = etf_closes(fund)
    dates = sorted(d for d in px if lo <= d <= hi)
    all_dates = sorted(px)
    pos = {d: i for i, d in enumerate(all_dates)}
    in_roll: dict[str, str] = {}  # business day -> roll-month label, for days in [D0-3, D0+8]
    for r in rolls:
        for k in range(-3, 9):
            j = r["i0"] + k
            if 0 <= j < len(bdays):
                in_roll[bdays[j]] = r["E"]
    res: dict[str, Any] = {}
    per_month: dict[str, dict[str, list[float]]] = {}
    for name, (kind, param) in SCHEDULES.items():
        R = bench_returns(bdays, st, rolls, weight_fn(kind, param))
        errs: list[float] = []
        month_err: dict[str, list[float]] = {}
        for d in dates:
            pd_ = all_dates[pos[d] - 1]
            ks = bdays[bisect.bisect_right(bdays, pd_): bisect.bisect_right(bdays, d)]
            if not ks or not any(k in in_roll for k in ks):
                continue
            rb = 1.0
            for kd in ks:
                v = R.get(kd)
                if v is None:
                    rb = math.nan
                    break
                rb *= v
            if math.isnan(rb):
                continue
            e = (px[d] / px[pd_] - 1 - (rb - 1)) * 1e4
            errs.append(abs(e))
            month_err.setdefault(in_roll[ks[-1]] if ks[-1] in in_roll else in_roll[ks[0]], []).append(abs(e))
        res[name] = {"roll_window_days": len(errs), "mean_abs_err_bp": round(float(np.mean(errs)), 4),
                     "median_abs_err_bp": round(float(np.median(errs)), 4)}
        per_month[name] = month_err
    best = min(res, key=lambda n: res[n]["mean_abs_err_bp"])
    alts = [n for n in res if n != "documented"]
    best_alt = min(alts, key=lambda n: res[n]["mean_abs_err_bp"])
    wins = losses = 0
    for mlab, errs in per_month["documented"].items():
        other = per_month[best_alt].get(mlab)
        if not other:
            continue
        a, b = float(np.mean(errs)), float(np.mean(other))
        wins += a < b
        losses += a > b
    n = wins + losses
    p = sum(math.comb(n, k) for k in range(wins, n + 1)) / 2 ** n if n else 1.0
    Rw = bench_returns(bdays, st, rolls, weight_fn("doc", 0), wrong_pair=True)
    werr = []
    for d in dates:
        pd_ = all_dates[pos[d] - 1]
        ks = bdays[bisect.bisect_right(bdays, pd_): bisect.bisect_right(bdays, d)]
        if not ks or not any(k in in_roll for k in ks):
            continue
        vals = [Rw.get(k) for k in ks]
        if any(v is None for v in vals):
            continue
        werr.append(abs((px[d] / px[pd_] - 1 - (math.prod(vals) - 1)) * 1e4))  # type: ignore[arg-type]
    wrong_pair = round(float(np.mean(werr)), 4)
    if wrong_pair <= res["documented"]["mean_abs_err_bp"]:
        raise UscfError(f"{fund}: control failed, the wrong contract pair fits as well as the documented one")
    return {"window": [lo, hi], "schedules": res, "best": best, "best_alternative": best_alt,
            "documented_is_best": best == "documented",
            "sign_test_vs_best_alternative": {"months_won": wins, "months_lost": losses, "p_one_sided": round(p, 6)},
            "identified": bool(best == "documented" and p < 0.05),
            "control_wrong_pair_mean_abs_err_bp": wrong_pair}


ROLLCAL = REPO / "data" / "raw" / "uscf"
MON3 = {m: i + 1 for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}


def _d(s: str) -> str:
    dd, mm, yy = s.strip().split("-")
    return f"20{yy}-{MON3[mm]:02d}-{int(dd):02d}"


def official_calendar(fund: str, bdays: list[str], rolls: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for y in range(2020, 2024):
        with (ROLLCAL / f"uscf-rolldates-commodities-{y}.csv").open(encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) >= 3 and r[0] == fund:
                    rows.append((_d(r[1]), _d(r[2])))
    out = []
    for begin, end in sorted(rows):
        month = begin[:7]
        if fund == "USO" and month >= "2020-05":
            mb = [d for d in bdays if d[:7] == month]
            pred_b, pred_e, rule = mb[0], mb[9], "BD1-BD10"
        else:
            hit = [x for x in rolls if x["D0"][:7] == month]
            if not hit:
                out.append({"month": month, "rule": "D0..D0+3", "official": [begin, end], "predicted": None,
                            "match": False, "note": "no computed D0 in this month"})
                continue
            pred_b, pred_e, rule = hit[0]["D0"], bdays[hit[0]["i0"] + 3], "D0..D0+3"
        out.append({"month": month, "rule": rule, "official": [begin, end], "predicted": [pred_b, pred_e],
                    "match": [begin, end] == [pred_b, pred_e]})
    return {"months": len(out), "matched": sum(o["match"] for o in out), "proven": all(o["match"] for o in out),
            "mismatches": [o for o in out if not o["match"]]}


def build() -> dict[str, Any]:
    doc: dict[str, Any] = {"spec": "settlement-ledger AITODO 1e: UNG/USO held months and roll days vs the funds' "
                                   "documented four-day rule; see the script docstring",
                           "reserved_from": RESERVED_FROM, "funds": {}}
    global _BDAYS
    for fund, root in ROOT_OF.items():
        st = settlements(root)
        bdays = sorted(st)
        _BDAYS = bdays
        rolls = roll_calendar(root, bdays)
        doc["funds"][fund] = {"root": root, "held_months": held_months(fund, rolls),
                              "roll_days": roll_days(fund, bdays, st, rolls),
                              "official_roll_calendar": official_calendar(fund, bdays, rolls)}
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise UscfError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for fund, f in doc["funds"].items():
        hm, rd = f["held_months"], f["roll_days"]
        print(f"{fund}: held months {hm['matched']}/{hm['scored']} (control {hm['control_matches']}); mismatches "
              f"{[(m['period_end'], m['held'], m['predicted']) for m in hm['mismatched']]}")
        for n, s in sorted(rd["schedules"].items(), key=lambda kv: kv[1]["mean_abs_err_bp"]):
            print(f"   {n:32s} mean|err| {s['mean_abs_err_bp']:8.3f} bp  median {s['median_abs_err_bp']:7.3f}  days {s['roll_window_days']}")
        print(f"   identified {rd['identified']}; sign test {rd['sign_test_vs_best_alternative']};"
              f" wrong-pair control {rd['control_wrong_pair_mean_abs_err_bp']}")
        oc = f["official_roll_calendar"]
        print(f"   OFFICIAL CALENDAR: {oc['matched']}/{oc['months']} months match -> {'PROVEN' if oc['proven'] else 'NOT PROVEN'}")
        for m in oc["mismatches"]:
            print("      MISMATCH", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
