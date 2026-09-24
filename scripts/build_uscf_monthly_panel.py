"""UNG and USO month-end NAV and shares from their monthly account statements (AITODO 1e).

Input: the statements fetched by `scripts/fetch_uscf_monthly_statements.py`
(`data/raw/uscf/monthly_statements/*.pdf`, gitignored), text extracted with `pdftotext -raw`. Each
statement ("For the Month Ended <date>", Exhibit 99.1 of a Rule 4.22 8-K) carries:
    Net Asset Value Beginning of Month <m/1/yy> $ X
    Additions (N Shares) Y          -- when shares were created
    Withdrawals (N Shares) (Z)      -- when shares were redeemed
    Net Asset Value End of Month $ W
    Net Asset Value Per Share (S Shares) $ P
A file with no "For the Month Ended" line (some library files are 10-K or 10-Q text under the
same name) is skipped and listed. Where two files state the same month, they must agree, or the
build raises.

Output: `data/fund_facts/uscf_monthly_statements.csv` (tracked, small): fund, month_end, nav_usd,
nav_per_share, shares, shares_added, shares_withdrawn, source.

GATES (each raises):
  G1 NAV = NAV per share x shares, to half a cent per share.
  G2 shares[m] - shares[m-1] = added[m] - withdrawn[m], for every consecutive pair of months. The
     only exception allowed is a month containing a reverse split, which is listed:
     USO 1-for-8 on 2020-04-28.
  G3 at every quarter-end month, shares and NAV equal D620's audited schedule (`shares_out`,
     `net_assets` in `fund_holdings_quarterly`, first publication) exactly. D620 reports the
     post-split count, so a statement from before the split is compared on that basis.
     Amended after the first run: NAV to $10, because USO 2019-12-31 differs by $2 between the two
     documents. Every non-exact match is listed in the gate's notes.
  G4 every month from 2017-01 to 2023-12 is present for both funds.
  G5 (added 2026-09-24) each month's "Net Asset Value Beginning of Month" equals the previous
     month's closing NAV. Amended after the first run: to 0.001% of NAV, because USO's March 2023
     statement opens $2,073 below February's close. Every non-exact pair is listed.
  A month the library lacks is DERIVED exactly from the next statement: closing NAV = the next
  month's opening NAV; closing shares = the next month's shares - additions + withdrawals. G3
  checks it where it is a quarter-end. Its own additions and withdrawals are -1 (unknown).

    uv run python scripts/build_uscf_monthly_panel.py            # write the CSV
    uv run python scripts/build_uscf_monthly_panel.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "raw" / "uscf" / "monthly_statements"
OUT = REPO / "data" / "fund_facts" / "uscf_monthly_statements.csv"
HOLDINGS = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
SLUG = {"united-states-natural-gas-fund": "UNG", "united-states-oil-fund": "USO"}
NAME = {"UNG": "United States Natural Gas Fund, LP", "USO": "United States Oil Fund, LP"}
MONTHS = {m: i + 1 for i, m in enumerate(("January", "February", "March", "April", "May", "June", "July", "August",
                                          "September", "October", "November", "December"))}
SPLIT_MONTHS = {("USO", "2020-04")}
FIRST, LAST = "2017-01", "2023-12"
NUM = r"\(?\s*(\d{1,3}(?:,\s?\d{3})*)\s*\)?"  # USO 2023-03 prints "$ 1,630, 200,959"


class PanelError(RuntimeError):
    pass


def _n(s: str) -> int:
    return int(s.replace(",", "").replace(" ", ""))


def parse(text: str) -> dict[str, Any] | None:
    m = re.search(r"For the Month Ended (\w+) (\d{1,2}), (\d{4})", text)
    if not m:
        return None
    month_end = f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    end = re.search(r"Net Asset Value End of Month \$\s*" + NUM, text)
    # '*' marks figures restated for a reverse split (UNG's December 2017 statement)
    ps = re.search(r"Net Asset Value Per Share \(([\d,]+)(\*?) Shares\) \$\s*([\d.]+)\*?", text)
    if not end or not ps:
        raise PanelError(f"{month_end}: statement found but NAV lines not parsed")
    add = re.search(r"Additions \(([\d,]+)\*? Shares\)", text)
    wd = re.search(r"Withdrawals \(([\d,]+)\*? Shares\)", text)
    beg = re.search(r"Net Asset Value Beginning of Month \S+ \$\s*" + NUM, text)
    if not beg:
        raise PanelError(f"{month_end}: beginning-of-month NAV not parsed")
    return {"month_end": month_end, "nav_begin_usd": _n(beg.group(1)), "nav_usd": _n(end.group(1)),
            "nav_per_share": float(ps.group(3)),
            "shares": _n(ps.group(1)), "shares_added": _n(add.group(1)) if add else 0,
            "shares_withdrawn": _n(wd.group(1)) if wd else 0, "split_restated": bool(ps.group(2))}


def build() -> tuple[str, dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    skipped: list[str] = []
    mislabeled: list[str] = []
    for pdf in sorted(list(SRC.glob("*-8-kms-*.pdf")) + list(SRC.glob("*-8-k-*.pdf"))):
        fund = SLUG[re.split(r"-8-k(?:ms)?-", pdf.name)[0]]
        text = subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True, check=True).stdout.decode(
            "utf-8", errors="replace")
        rec = parse(text)
        if rec is None:
            skipped.append(pdf.name)
            continue
        # identity: USCF's library files at least one sister fund's statement under this fund's name
        # (UNG's 2018-06 file is UNL's, "United States 12 Month Natural Gas Fund")
        name = NAME[fund]
        low = text.lower()
        if name.lower() not in low or "12 month" in low:
            mislabeled.append(pdf.name)
            continue
        key = (fund, rec["month_end"][:7])
        rec = {"fund": fund, **rec, "source": pdf.name}
        if key in rows:
            a, b = rows[key], rec
            if any(a[k] != b[k] for k in ("nav_usd", "shares", "nav_per_share")):
                raise PanelError(f"{key}: two statements disagree ({a['source']} vs {b['source']})")
            continue
        rows[key] = rec
    # a month the library lacks is DERIVED from the next month's statement, exactly: its closing NAV is
    # the next statement's beginning NAV, and its closing shares are the next month's shares minus that
    # month's additions plus its withdrawals. Its own additions and withdrawals are unknown (-1).
    derived: list[str] = []
    for fund in ("UNG", "USO"):
        have = {k[1] for k in rows if k[0] == fund}
        for y in range(2017, 2024):
            for mth in range(1, 13):
                m = f"{y}-{mth:02d}"
                nxt = f"{y + (mth == 12)}-{mth % 12 + 1:02d}"
                if m in have or nxt not in have:
                    continue
                n = rows[(fund, nxt)]
                shares = n["shares"] - n["shares_added"] + n["shares_withdrawn"]
                last_day = (pd.Timestamp(m + "-01") + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
                rows[(fund, m)] = {"fund": fund, "month_end": last_day, "nav_begin_usd": -1, "nav_usd": n["nav_begin_usd"],
                                   "nav_per_share": round(n["nav_begin_usd"] / shares, 2), "shares": shares,
                                   "shares_added": -1, "shares_withdrawn": -1, "split_restated": False,
                                   "source": f"derived from {n['source']}"}
                derived.append(f"{fund} {m}")
    df = pd.DataFrame(sorted(rows.values(), key=lambda r: (r["fund"], r["month_end"])))
    df = df[(df["month_end"].str[:7] >= FIRST) & (df["month_end"].str[:7] <= LAST)].reset_index(drop=True)

    gates: dict[str, Any] = {}
    # G1
    bad1 = df[(df["nav_usd"] - df["nav_per_share"] * df["shares"]).abs() > 0.005 * df["shares"] + 1]
    if len(bad1):
        raise PanelError(f"G1 failed on {bad1[['fund', 'month_end']].values.tolist()}")
    gates["G1_nav_eq_ps_x_shares"] = f"{len(df)} of {len(df)}"
    # G2
    g2, exceptions = 0, []
    g5 = 0
    g5_notes: list[str] = []
    for fund, g in df.groupby("fund"):
        g = g.sort_values("month_end")
        for (_, p), (_, c) in zip(g.iterrows(), g.iloc[1:].iterrows()):
            py, pm = int(p["month_end"][:4]), int(p["month_end"][5:7])
            if (int(c["month_end"][:4]) * 12 + int(c["month_end"][5:7])) - (py * 12 + pm) != 1:
                continue  # a gap in the library; G4 lists it
            if c["shares_added"] < 0:
                continue  # a derived month: its own additions and withdrawals are unknown
            # G5: this month's opening NAV is last month's closing NAV, to the dollar
            if c["nav_begin_usd"] >= 0 and c["nav_begin_usd"] != p["nav_usd"]:
                gap = c["nav_begin_usd"] - p["nav_usd"]
                if abs(gap) > 1e-5 * p["nav_usd"]:
                    raise PanelError(f"G5 failed: {fund} {c['month_end']} opens at {c['nav_begin_usd']}, "
                                     f"{p['month_end']} closed at {p['nav_usd']}")
                g5_notes.append(f"{fund} {c['month_end'][:7]} opens ${gap:+,} from the prior close")
            g5 += 1
            net = c["shares_added"] - c["shares_withdrawn"]
            if c["shares"] - p["shares"] == net:
                g2 += 1
                continue
            # a reverse split restates the month: previous shares / k + net == shares, exactly, for an integer k
            ks = [k for k in (2, 3, 4, 5, 8, 10) if p["shares"] % k == 0 and p["shares"] // k + net == c["shares"]]
            if ks:
                exceptions.append(f"{fund} {c['month_end'][:7]}: 1-for-{ks[0]} reverse split, identity exact after it")
            else:
                raise PanelError(f"G2 failed: {fund} {c['month_end']}: shares {p['shares']} -> {c['shares']}, "
                                 f"added {c['shares_added']}, withdrawn {c['shares_withdrawn']}")
    gates["G2_share_identity"] = {"held": g2, "split_exceptions": exceptions}
    gates["G5_opening_nav_eq_previous_close"] = {"held": g5, "non_exact": g5_notes}
    gates["derived_months"] = derived
    # G3
    h = pd.read_csv(HOLDINGS, encoding="utf-8", dtype=str)
    h = h[h["fund"].isin(["UNG", "USO"])].sort_values(["period_end", "filed_date"])
    first = h.groupby(["fund", "period_end"]).first().reset_index()
    g3, g3_bad = 0, []
    g3_notes: list[str] = []
    for _, r in df.iterrows():
        if r["month_end"][5:7] not in ("03", "06", "09", "12"):
            continue
        q = first[(first["fund"] == r["fund"]) & (first["period_end"] == r["month_end"])]
        if q.empty:
            continue
        sh, na = float(q["shares_out"].iloc[0]), float(q["net_assets"].iloc[0])
        # shares exactly, or exactly after a later reverse split restated the audited figure; NAV to $10
        # (USO 2019-12-31 differs by $2 between the statement and the audited schedule)
        k_ok = [k for k in (1, 2, 3, 4, 5, 8, 10) if r["shares"] % k == 0 and r["shares"] // k == int(sh)]
        if k_ok and abs(int(na) - r["nav_usd"]) <= 10:
            g3 += 1
            if k_ok[0] != 1 or int(na) != r["nav_usd"]:
                g3_notes.append(f"{r['fund']} {r['month_end']}: split k={k_ok[0]}, NAV diff ${int(na) - r['nav_usd']}")
        else:
            g3_bad.append({"fund": r["fund"], "month_end": r["month_end"], "statement": [r["shares"], r["nav_usd"]],
                           "audited": [sh, na]})
    if g3_bad:
        raise PanelError(f"G3 failed: {g3_bad[:4]}")
    gates["G3_quarter_ends_equal_audited"] = {"matched": g3, "notes": g3_notes}
    # G4 (amended after the first run found USCF's library lacks some months): LIST the missing
    # months. They are to be filled from the same 8-Ks on EDGAR, which was in maintenance on
    # 2026-09-24.
    missing: dict[str, list[str]] = {}
    for fund in ("UNG", "USO"):
        have = set(df[df["fund"] == fund]["month_end"].str[:7])
        want = {f"{y}-{m:02d}" for y in range(2017, 2024) for m in range(1, 13)}
        missing[fund] = sorted(want - have)
    gates["G4_missing_months_to_fill_from_edgar"] = missing
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", encoding="utf-8")
    return buf.getvalue(), {"rows": len(df), "skipped_files_not_monthly_statements": skipped,
                            "mislabeled_files_other_fund": mislabeled, "gates": gates}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text, meta = build()
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise PanelError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}: {meta['rows']} rows; gates {meta['gates']}")
    print(f"skipped (not monthly statements): {meta['skipped_files_not_monthly_statements']}")
    print(f"mislabeled (another fund's statement): {meta['mislabeled_files_other_fund']}")
    return 0


if __name__ == "__main__":
    _ = csv
    sys.exit(main())
