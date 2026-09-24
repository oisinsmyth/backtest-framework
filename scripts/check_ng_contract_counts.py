"""Check that BOIL's and KOLD's daily contract COUNT follows from their daily NAV, shares and the settlement.

SPEC -- written 2026-09-24 before any count was compared, and frozen from then on.

WHY. AITODO item 1a. The held months are proven (`data/ledger_ng_held_months_check.json`), and so are
the roll days (`data/ledger_gate_0b_ng.json`). The ledger also needs how MANY contracts each fund
holds on every day, and the only daily inputs are NAV and shares (`fund_nav_daily`) and the NG
settlement (`fut_settle_strip`). The claim to prove: on a futures-only day,
    contracts_t = L * NAV_t * shares_t / (settle_t[held month] * 10,000)
where 10,000 MMBtu is the NYMEX NG multiplier.

EVIDENCE. Each BOIL and KOLD quarter-end in D620's `fund_holdings_quarterly`, whose futures lines
give the audited contract count. Only the first publication of each period is used. The panel is
read through `load_panel(reserved_from="2024-01-01")`, which cuts on `filed_date`, so the
2023-12-31 schedule, filed in 2024, is not read. The quarter-end's NAV and shares come from the last
NAV date on or before period_end, and its settlement from the same day's strip.

TWO READINGS, both declared here, because a creation on day q settles the next day and it is not
known which count the day-q position reflects:
  A (primary): shares on the quarter-end's NAV date.
  B: shares on the next NAV date.
Whichever reading matches on every futures-only quarter-end is the one the ledger uses. If
neither does, the misses are reported and the count is not proven.

TOLERANCE. |reported - derived| <= max(1 contract, 0.5% of derived). The fund rounds to whole
contracts, and 0.5% is the pre-declared allowance for everything else.

ALSO REPORTED (cross-checks, not verdicts):
  * the filing's implied price, notional / contracts / 10,000, against the strip's settlement on
    that day;
  * the filing's net assets against NAV x shares from `fund_nav_daily`, under both readings;
  * BOIL's swap quarter-ends (2023-Q1..Q3): (futures + swap notional) / (2 x net assets), which
    should be 1.0 even though the split is unknown.

CONTROL THAT MUST FIRE: with L of the wrong magnitude (1 in place of 2), no quarter-end may pass.

DEVIATION (after the first run, which raised): a quarter-end with no NG settlement on disk
(2020-06-30, the archive hole in AITODO 1b) is listed as `unverifiable` instead of raising. It
counts as neither a pass nor a miss.

READING C (POST HOC, added after the first complete run): L x AUM_t / (settle x 10,000), using
the AUM ProShares publishes, not NAV x shares. In that run KOLD passed reading A on all 25
quarter-ends, and BOIL missed 3 of 22 (2017-09-30, 2018-03-31, 2019-03-31) by 0.59-0.78%. Each
miss equals, to within 0.03 pp, the gap between the filing's net assets and NAV x shares. BOIL's
shares are back-adjusted by a 10,000x split factor from a figure published in thousands of
shares, so before 2020 its adjusted count is rounded to +/-1.5% (2017-09-29: 580 shares). The
error is in the share count, not in the leverage rule. Reading C is reported beside A and B and
is labelled post hoc.

WHAT THIS DOES NOT TOUCH. It reads only data before 2024-01-01, computes no return, and writes one
new file, `data/ledger_ng_contract_counts_check.json`.

    uv run python scripts/check_ng_contract_counts.py            # write the JSON
    uv run python scripts/check_ng_contract_counts.py --check    # rebuild and compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from pathlib import Path
from typing import Any

from backtest_framework.data.panels import load_panel

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_ng_contract_counts_check.json"
RESERVED_FROM = "2024-01-01"
FIRST = "2017-05-22"
FUNDS = {"BOIL": 2, "KOLD": -2}
MULT = 10_000
REL_TOL = 0.005
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
RE_C = re.compile(r"^NG([FGHJKMNQUVXZ])(\d{1,2})$")


class CountsError(RuntimeError):
    pass


def _ym(contract: str, session: str) -> str | None:
    """D526's rule, as in build_fut_settle_strip.ym, returned as YYYY-MM."""
    m = RE_C.match(contract)
    if not m:
        return None
    mon, y = MONTH[m.group(1)], m.group(2)
    sy, sm = int(session[:4]), int(session[5:7])
    if len(y) == 2:
        return f"{2000 + int(y):04d}-{mon:02d}"
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and (cand * 12 + mon) >= (sy * 12 + sm) - 1:
            return f"{cand:04d}-{mon:02d}"
    return None


def within(rep: float, der: float) -> bool:
    return abs(rep - der) <= max(1.0, REL_TOL * abs(der))


def build() -> dict[str, Any]:
    hq = load_panel("fund_holdings_quarterly", reserved_from=RESERVED_FROM).frame
    nav = load_panel("fund_nav_daily", reserved_from=RESERVED_FROM, usecols=["date", "fund", "nav", "shares_out", "aum"]).frame
    st = load_panel("fut_settle_strip", reserved_from=RESERVED_FROM, usecols=["root", "contract", "ref", "settle"]).frame
    st = st[st["root"] == "NG"]
    settle: dict[tuple[str, str], float] = {}
    for c, ref, px in zip(st["contract"].astype(str), st["ref"].astype(str), st["settle"].astype(float)):
        ym = _ym(c, ref)
        if ym is not None:
            settle[(ref, ym)] = px

    doc: dict[str, Any] = {
        "spec": "settlement-ledger AITODO item 1a: BOIL/KOLD daily contract count = L*NAV*shares/(settle*10000); see docstring",
        "tolerance": f"|reported - derived| <= max(1 contract, {REL_TOL:.1%} of derived)",
        "reserved_from": RESERVED_FROM, "funds": {},
    }
    for fund, L in FUNDS.items():
        g = nav[nav["fund"] == fund].sort_values("date")
        dates = [str(d) for d in g["date"]]
        navs = [float(v) for v in g["nav"]]
        shares = [float(v) for v in g["shares_out"]]
        aums = [float(v) for v in g["aum"]]
        h = hq[(hq["fund"] == fund) & (hq["period_end"].astype(str) >= FIRST[:7])]
        h = h.sort_values(["period_end", "filed_date"])
        first_pub = h.groupby("period_end")["source_accession"].first()
        rows: list[dict[str, Any]] = []
        unverifiable: list[dict[str, Any]] = []
        for pe, acc in first_pub.items():
            x = h[(h["period_end"] == pe) & (h["source_accession"] == acc)]
            fut = x[x["kind"] == "futures"]
            if fut.empty:
                continue
            months = sorted(set(fut["contract_month"].astype(str)))
            if len(months) != 1:
                raise CountsError(f"{fund} {pe}: {len(months)} months held; this check assumes one")
            i = bisect.bisect_right(dates, str(pe)) - 1
            if i < 0 or i + 1 >= len(dates):
                raise CountsError(f"{fund} {pe}: no NAV date around the quarter-end")
            day = dates[i]
            c_rep = float(fut["contracts"].astype(float).sum())
            notional = float(fut["notional_usd"].astype(float).sum())
            px = settle.get((day, months[0]))
            if px is None:
                unverifiable.append({"period_end": str(pe), "nav_date": day, "month": months[0],
                                     "reason": "no NG settlement on disk that day (archive hole, AITODO 1b)"})
                continue
            swap_total = float(x["swap_notional_total"].astype(float).iloc[0])
            net_assets = float(x["net_assets"].astype(float).iloc[0])
            aum_a = navs[i] * shares[i]
            aum_b = navs[i] * shares[i + 1]
            der_a = L * aum_a / (px * MULT)
            der_b = L * aum_b / (px * MULT)
            der_c = L * aums[i] / (px * MULT)
            wrong_l = (L // abs(L)) * aums[i] / (px * MULT)
            r: dict[str, Any] = {
                "period_end": str(pe), "nav_date": day, "next_nav_date": dates[i + 1], "month": months[0],
                "accession": str(acc), "reported_contracts": c_rep,
                "derived_A": round(der_a, 2), "derived_B": round(der_b, 2),
                "rel_err_A": round((c_rep - der_a) / der_a, 6), "rel_err_B": round((c_rep - der_b) / der_b, 6),
                "pass_A": within(c_rep, der_a), "pass_B": within(c_rep, der_b),
                "derived_C": round(der_c, 2), "rel_err_C": round((c_rep - der_c) / der_c, 6), "pass_C": within(c_rep, der_c),
                "net_assets_vs_C": round(net_assets / aums[i] - 1, 6),
                "control_wrong_L_pass": within(c_rep, wrong_l),
                "filing_price_vs_strip": round(notional / c_rep / MULT - px, 6),
                "net_assets_vs_A": round(net_assets / aum_a - 1, 6), "net_assets_vs_B": round(net_assets / aum_b - 1, 6),
                "swap_notional_total": swap_total,
            }
            if swap_total > 0:
                r["total_exposure_over_L_net_assets"] = round((abs(notional) + swap_total) / (abs(L) * net_assets), 6)
            rows.append(r)
        free = [r for r in rows if r["swap_notional_total"] == 0]
        if any(r["control_wrong_L_pass"] for r in free):
            raise CountsError(f"control failed for {fund}: L of the wrong magnitude passed a quarter-end")
        doc["funds"][fund] = {
            "L": L,
            "futures_only_quarter_ends": len(free),
            "unverifiable": unverifiable,
            "pass_A": sum(r["pass_A"] for r in free), "pass_B": sum(r["pass_B"] for r in free),
            "pass_C_post_hoc": sum(r["pass_C"] for r in free),
            "max_abs_rel_err_A": max(abs(r["rel_err_A"]) for r in free),
            "max_abs_rel_err_B": max(abs(r["rel_err_B"]) for r in free),
            "max_abs_rel_err_C_post_hoc": max(abs(r["rel_err_C"]) for r in free),
            "max_abs_filing_price_vs_strip": max(abs(r["filing_price_vs_strip"]) for r in free),
            "swap_quarter_ends": [{k: r[k] for k in ("period_end", "total_exposure_over_L_net_assets", "rel_err_A")}
                                  for r in rows if r["swap_notional_total"] > 0],
            "rows": rows,
        }
        f = doc["funds"][fund]
        f["proven_reading"] = ("A" if f["pass_A"] == len(free) else "B" if f["pass_B"] == len(free) else None)
        f["proven_reading_post_hoc"] = "C" if f["pass_C_post_hoc"] == len(free) else None
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise CountsError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for fund, f in doc["funds"].items():
        print(f"{fund}: futures-only quarter-ends {f['futures_only_quarter_ends']}; pass A {f['pass_A']}, B {f['pass_B']};"
              f" max |rel err| A {f['max_abs_rel_err_A']:.4%} B {f['max_abs_rel_err_B']:.4%};"
              f" filing price vs strip max {f['max_abs_filing_price_vs_strip']}; proven reading {f['proven_reading']};"
              f" post-hoc C pass {f['pass_C_post_hoc']} (max {f['max_abs_rel_err_C_post_hoc']:.4%}); unverifiable {len(f['unverifiable'])}")
        for r in f["rows"]:
            print(f"   {r['period_end']} {r['month']} rep {r['reported_contracts']:>9.0f}  A {r['derived_A']:>11.2f} ({r['rel_err_A']:+.4%})"
                  f"  B {r['derived_B']:>11.2f} ({r['rel_err_B']:+.4%})  NA-vs-A {r['net_assets_vs_A']:+.4%}"
                  + (f"  SWAPS exp/L*NA {r.get('total_exposure_over_L_net_assets')}" if r["swap_notional_total"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
