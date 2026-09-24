"""Recover the NG and CL settlements missing from `fut_settle_strip` on 2020-02-27 and 2020-06-30 (AITODO 1b).

WHY. The settlement strip, and the 2020 statistics file it was built from
(`data/raw/databento/GLBX-20260911-SDNLQ6M99S/glbx-mdp3-20200101-20201231.statistics.dbn.zst`), holds
no NG or CL settlement for either trade date. Gate 0b showed each hole as a pair of equal and
opposite failing days (356-931 bp).

DATABENTO DOES NOT HAVE THEM EITHER (checked 2026-09-24). A $0 refetch of the statistics schema for
NG.FUT and CL.FUT over 2020-02-27 → 02-29 and 2020-06-30 → 07-02 is kept under
`data/raw/databento/holes_2020/`. It carries settlements referenced to the 2020-02-26 and
2020-02-28 sessions and to 2020-07-01, and none for the two hole dates. Databento marks
2020-06-30 and 2020-07-01 "degraded".

THE SOURCE USED: the EIA's daily NYMEX futures settlements, already on disk in the EIA bulk files
`data/raw/eia/NG.zip` (series NG.RNGC1.D-RNGC4.D, "Natural Gas Futures Contract 1-4, Daily") and
`data/raw/eia/PET.zip` (PET.RCLC1.D-RCLC4.D, crude oil). EIA's contract k is the k-th nearest
delivery month still trading. Nothing is downloaded.

VALIDATION, all of which must hold or it raises:
  (1) THE MAPPING, a known-answer check. (The first run found CL at 90.2%. D526's one-digit year
      rule dates a CL code ten years out as a month behind the session, so CLK9 on 2019-06-10
      read as May 2019, an expired contract. Codes whose rule-based last trading day has passed are
      now dropped from the ranking. That was a fix to the check, made after that run, and NG was
      unaffected.) On every strip day from 2017-05-22 to 2023-12-29, EIA
      contract k (k = 1..4) must equal the strip's k-th nearest settlement that day, to 0.0005.
      This must hold on at least 99% of root-day-k cells, and every mismatch is listed.
  (2) THE HOLE DAY'S CONTRACT LIST. The contracts trading on a hole day are those that settle on
      the next strip day, plus any that settle on the previous strip day and whose last trading
      day, under the exchange's own rule, is on or after the hole day. NG's rule: three business
      days before the first calendar day of the delivery month. CL's rule: three business days
      before the 25th calendar day of the month before delivery, or four if the 25th is not a
      business day. A contract that falls between the two lists without the rule placing it
      raises.
  (3) GATE 0b. With the recovered NG settlements added, BOIL's and KOLD's rebuilt NAV on each
      hole date and on the day after must be within 5 bp of the official NAV, using Gate 0b's own
      functions (`scripts/gate_0b_ng_nav.py`, imported, not copied).

WHAT THIS DOES NOT TOUCH. `fut_settle_strip.csv.gz` and every existing artefact are unchanged. The
recovered rows are written to `data/ledger_settle_holes_2020.csv` (root, contract, ref, settle,
source) for the ledger build to read beside the strip. Everything read is dated before
2024-01-01.

    uv run python scripts/fill_settle_holes_2020.py            # build + validate
    uv run python scripts/fill_settle_holes_2020.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import csv
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
EIA = {"NG": (REPO / "data" / "raw" / "eia" / "NG.zip", "NG.RNGC{k}.D"),
       "CL": (REPO / "data" / "raw" / "eia" / "PET.zip", "PET.RCLC{k}.D")}
OUT = REPO / "data" / "ledger_settle_holes_2020.csv"
HOLES = ("2020-02-27", "2020-06-30")
FIRST, LAST = "2017-05-22", "2023-12-29"
TOL = 0.0005
MIN_MATCH = 0.99
LETTER = "FGHJKMNQUVXZ"


class HoleError(RuntimeError):
    pass


def _gate0b() -> Any:
    spec = importlib.util.spec_from_file_location("gate_0b_ng_nav", REPO / "scripts" / "gate_0b_ng_nav.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules["gate_0b_ng_nav"] = m
    spec.loader.exec_module(m)
    return m


def eia_series(root: str) -> dict[int, dict[str, float]]:
    """k -> {YYYY-MM-DD: price} for the four nearest contracts, window-cut before 2024."""
    path, pat = EIA[root]
    want = {pat.format(k=k): k for k in range(1, 5)}
    out: dict[int, dict[str, float]] = {}
    with zipfile.ZipFile(path) as z, zipfile.Path(z, at=z.namelist()[0]).open(mode="rb") as fh:
        for raw in fh:
            if b'"series_id"' not in raw[:200]:
                continue
            d = json.loads(raw)
            k = want.get(d.get("series_id", ""))
            if k is None:
                continue
            out[k] = {f"{s[:4]}-{s[4:6]}-{s[6:8]}": float(v) for s, v in d["data"]
                      if v is not None and f"{s[:4]}-{s[4:6]}-{s[6:8]}" < "2024-01-01"}
    if sorted(out) != [1, 2, 3, 4]:
        raise HoleError(f"{root}: EIA series found {sorted(out)}, want 1-4")
    return out


def code(ym: tuple[int, int]) -> str:
    return f"{LETTER[ym[1] - 1]}{ym[0] % 10}"


def last_trade(root: str, ym: tuple[int, int], bdays: list[str]) -> str:
    """The exchange's last trading day for delivery month ym, on the business calendar `bdays`."""
    y, m = ym
    if f"{y:04d}-{m:02d}-01" > bdays[-1]:
        return "9999-12-31"  # beyond the calendar on hand: certainly still trading within it
    if root == "NG":
        anchor = f"{y:04d}-{m:02d}-01"
        i = bisect.bisect_left(bdays, anchor)
        return bdays[i - 3]
    py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
    d25 = f"{py:04d}-{pm:02d}-25"
    i = bisect.bisect_left(bdays, d25)
    return bdays[i - 3] if (i < len(bdays) and bdays[i] == d25) else bdays[i - 4]


def build() -> tuple[list[list[str]], dict[str, Any]]:
    g = _gate0b()
    strip = g.load_panel("fut_settle_strip", reserved_from=g.RESERVED_FROM, usecols=["root", "contract", "ref", "settle"]).frame
    by_day: dict[str, dict[str, dict[tuple[int, int], float]]] = {"NG": {}, "CL": {}}
    for r, c, d, px in zip(strip["root"].astype(str), strip["contract"].astype(str), strip["ref"].astype(str),
                           strip["settle"].astype(float)):
        if r not in by_day:
            continue
        ym = g._ym("NG" + c[2:], d)  # gate_0b's D526 code rule; the month code and year digits are root-free
        if ym is None:
            raise HoleError(f"unparsed {c}")
        by_day[r].setdefault(d, {})[ym] = px
    # copies of the previous day (holiday republications, Gate 0b's finding) are not trading days
    for r in by_day:
        days = sorted(by_day[r])
        copies = [d for p, d in zip(days, days[1:]) if by_day[r][d] == by_day[r][p]]
        for d in copies:
            del by_day[r][d]

    report: dict[str, Any] = {"mapping": {}, "holes": {}}
    out_rows: list[list[str]] = []
    for root in ("NG", "CL"):
        eia = eia_series(root)
        days = sorted(by_day[root])
        bdays = sorted(set(days) | set(HOLES))
        # (1) the mapping. A code whose rule-based last trading day is already past is the contract
        # ten years out that D526's one-digit rule dated a month behind the session (CLK9 on
        # 2019-06-10 is May 2029): it is not a near contract and is dropped from the ranking.
        n_cells, n_ok, bad = 0, 0, []
        n_dropped = 0
        for d in days:
            if not (FIRST <= d <= LAST):
                continue
            live_items = [(ym, px) for ym, px in sorted(by_day[root][d].items()) if last_trade(root, ym, bdays) >= d]
            n_dropped += len(by_day[root][d]) - len(live_items)
            near_px = live_items[:4]
            for k in range(1, 5):
                e = eia[k].get(d)
                if e is None or len(near_px) < k:
                    continue
                n_cells += 1
                if abs(e - near_px[k - 1][1]) <= TOL:
                    n_ok += 1
                else:
                    bad.append({"day": d, "k": k, "eia": e, "strip": near_px[k - 1][1], "strip_month": list(near_px[k - 1][0])})
        share = n_ok / n_cells
        report["mapping"][root] = {"cells": n_cells, "matched": n_ok, "share": round(share, 6), "mismatches": bad,
                                   "ten_year_codes_dropped": n_dropped}
        if share < MIN_MATCH:
            raise HoleError(f"{root}: EIA contract k matches the strip's k-th nearest on only {share:.4f}; "
                            f"first mismatches {bad[:12]}")
        # (2) the hole day's contract list, then (fill)
        for hole in HOLES:
            i = bisect.bisect_left(days, hole)
            prev, nxt = days[i - 1], days[i]
            live = {ym for ym in by_day[root][nxt] if last_trade(root, ym, bdays) >= nxt}
            for ym in {ym for ym in by_day[root][prev] if last_trade(root, ym, bdays) >= prev} - live:
                lt = last_trade(root, ym, bdays)
                if lt >= hole:
                    live.add(ym)
                elif lt != prev:
                    raise HoleError(f"{root} {hole}: {ym} settles on {prev}, not on {nxt}, and its rule date is {lt}")
            near: list[tuple[int, int]] = sorted(live)[:4]
            got = {}
            for k in range(1, 5):
                e = eia[k].get(hole)
                if e is None:
                    raise HoleError(f"{root} {hole}: EIA has no contract-{k} price")
                got[k] = e
                out_rows.append([root, root + code(near[k - 1]), hole, repr(e), f"EIA {EIA[root][1].format(k=k)}"])
            report["holes"][f"{root} {hole}"] = {"prev": prev, "next": nxt,
                                                 "contracts": [f"{y:04d}-{m:02d}" for y, m in near], "eia": got}
    # (3) Gate 0b with the NG fill
    nav, settles, _reads = g.load_inputs()
    filled = {d: dict(v) for d, v in settles.items()}
    for root, c, d, px, _src in out_rows:
        if root == "NG":
            ym = g._ym(c, d)
            filled.setdefault(d, {})[ym] = float(px)
    filled = {d: v for d, v in filled.items() if d not in set(g.copy_days(filled))}
    bdl, bd = g.business_days(filled)
    R = g.index_returns(bdl, bd, filled, g.s0)
    rates = g.load_rates()
    check = {"2020-02-27", "2020-02-28", "2020-06-30", "2020-07-01"}
    report["gate0b_with_fill"] = {}
    for fund, L in g.FUNDS.items():
        errs = {str(x["date"]): (None if x["err_bp"] is None else round(float(x["err_bp"]), 3))
                for x in g.replicate(nav, fund, L, bdl, bd, R, rates) if x["date"] in check}
        report["gate0b_with_fill"][fund] = errs
        if len(errs) != 4 or any(e is None or abs(e) > g.BP_TOL for e in errs.values()):
            raise HoleError(f"Gate 0b on the hole days for {fund} with the fill: {errs}")
    return out_rows, report


def render(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["root", "contract", "ref", "settle", "source"])
    w.writerows(sorted(rows))
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    rows, rep = build()
    text = render(rows)
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise HoleError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.name}: {len(rows)} settlements")
    for root, m in rep["mapping"].items():
        print(f"  mapping {root}: {m['matched']}/{m['cells']} = {m['share']:.4%}; mismatches {len(m['mismatches'])}")
        for b in m["mismatches"][:8]:
            print("     ", b)
    for k, v in rep["holes"].items():
        print(f"  {k}: contracts {v['contracts']} eia {v['eia']}")
    for fund, errs in rep["gate0b_with_fill"].items():
        print(f"  Gate 0b {fund} with the fill: {errs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
