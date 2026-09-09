"""The census behind `docs/research/the-negative-space-scan.md`'s [MEASURED HERE] tags.

    uv run python scripts/probe_negative_space_census.py

NOTHING HERE SCORES A CELL. No book is built, no rule is proposed, no forward return is
touched, no null is drawn. It reads two committed fixtures and counts. It exists because
the scan record quotes six fixture facts, and a file a record quotes is evidence: the
reader must be able to reproduce the numbers rather than take them.

WHAT IT ESTABLISHES, AND WHY EACH ONE IS LOAD-BEARING IN THE RECORD

  1. The two fixtures' spans.  The scan's R1 lead claims a cross-asset series can be
     attached to the equity book WITH NO FETCH.  That claim is false unless the ETF
     fixture and the single-name fixture cover the same bars.  They do, and this prints
     both spans so the claim can be checked rather than believed.

  2. How many ETF symbols span the WHOLE window.  A gate built from a series that starts
     in 2015 cannot gate a book that starts in 2010, and a ragged panel hides that.

  3. Presence AND ABSENCE of the cross-asset series by name.  The absences are the more
     important half: the record states up front that implied volatility (VXX, VIXY) and
     the dollar (UUP, UDN) are OUT OF REACH without a pull.  An absence asserted in prose
     is worth nothing; this prints the list.

  4. The dead-name counts on the equity fixture.  N1's Stage 0 turns on them -- a
     short-interest source that serves only live tickers would reintroduce exactly the
     survivorship the fixture was built to remove, and the size of that risk is the
     delisted + collapsed share.

THE ONE ASSERTION THAT CAN FAIL, and it is the claim the R1 lead rests on.  The two
fixtures must share their first and last bar; if a future refetch moves either, the
"no fetch needed" claim silently stops being true and this raises instead of printing a
join that does not exist.  Proved able to fail by flipping the comparison in a scratch
edit -- it raised.

CAUTION: THE CEF OBSERVATION IS NOT DECIDED HERE.  The record notes that several symbols
in the ETF fixture look like closed-end funds and makes a census the Stage 0 gate for
that lead.  This probe deliberately does NOT classify them -- there is no instrument-type
field in the fixture, and guessing from the ticker is exactly the kind of unmeasured
assumption the record is written to avoid.  It prints the head of the symbol list and
leaves the classification to a study that fetches the type.
"""

from __future__ import annotations

import collections
import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"
EQUITY = FIX / "us_shorts_daily_raw.csv.gz"
ETFS = FIX / "etf_wide_daily_raw.csv.gz"
OUT = ROOT / "data" / "negative_space_census.json"

# The cross-asset series the R1 lead names, by role. Absences matter as much as presences.
ROLES = {
    "curve": ["TLT", "IEF", "SHY"],
    "credit": ["HYG", "JNK", "LQD"],
    "metals": ["GLD", "SLV"],
    "fx": ["FXE", "FXY"],
    "size": ["SPY", "QQQ", "IWM", "IJR"],
    "sector": ["XLF", "XLK", "XLE", "XLU", "XLP", "XLY"],
    "geography": ["EEM", "EFA"],
    "industry": ["SMH", "KRE"],
    "cash": ["BIL"],
    "OUT_OF_REACH_vol": ["VXX", "VIXY"],
    "OUT_OF_REACH_dollar": ["UUP", "UDN"],
    "OUT_OF_REACH_factor": ["MTUM", "USMV"],
}


def census(path: Path) -> dict:
    """First bar, last bar and bar count per symbol. One pass, no panel build."""
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    bars: collections.Counter = collections.Counter()
    rows = 0
    with gzip.open(path, "rt") as fh:
        for row in csv.DictReader(fh):
            sym, ts = row["symbol"], row["timestamp"][:10]
            if sym not in first:
                first[sym] = ts
            last[sym] = ts
            bars[sym] += 1
            rows += 1
    return {"first": first, "last": last, "bars": dict(bars), "rows": rows}


def main() -> None:
    eq = census(EQUITY)
    etf = census(ETFS)

    eq_span = (min(eq["first"].values()), max(eq["last"].values()))
    etf_span = (min(etf["first"].values()), max(etf["last"].values()))

    # [ASSERT] The R1 lead's "no fetch needed" claim IS this equality. If a refetch moves
    # either fixture, the claim stops being true and the record must be amended.
    if eq_span != etf_span:
        raise AssertionError(
            f"THE JOIN THE SCAN RECORD DEPENDS ON DOES NOT HOLD: equity spans {eq_span}, "
            f"ETFs span {etf_span}. R1's 'no fetch, no new provider' claim is void until "
            "docs/research/the-negative-space-scan.md is amended."
        )

    full = sorted(
        s for s in etf["first"]
        if etf["first"][s] <= etf_span[0] and etf["last"][s] >= etf_span[1]
    )

    roles = {}
    for role, syms in ROLES.items():
        roles[role] = {
            s: (
                {"first": etf["first"][s], "last": etf["last"][s], "bars": etf["bars"][s]}
                if s in etf["first"] else None
            )
            for s in syms
        }

    eq_meta = json.loads((FIX / "us_shorts_daily_raw.meta.json").read_text())
    status = eq_meta.get("status_counts", {})
    dead = status.get("delisted", 0) + status.get("collapsed", 0)
    n_eq = eq_meta.get("n_symbols", len(eq["first"]))

    art = {
        "record": "docs/research/the-negative-space-scan.md",
        "claims": "the six [MEASURED HERE] facts in sections 1a and 6.2",
        "equity": {
            "fixture": EQUITY.name,
            "n_symbols": n_eq,
            "rows": eq["rows"],
            "span": {"start": eq_span[0], "end": eq_span[1]},
            "status_counts": status,
            "dead": dead,
            "dead_share": round(dead / n_eq, 4) if n_eq else None,
        },
        "etfs": {
            "fixture": ETFS.name,
            "n_symbols": len(etf["first"]),
            "rows": etf["rows"],
            "span": {"start": etf_span[0], "end": etf_span[1]},
            "n_spanning_whole_window": len(full),
            "roles": roles,
            "symbols_head_40": sorted(etf["first"])[:40],
        },
        "join_asserted": True,
    }
    OUT.write_text(json.dumps(art, indent=2))

    print(f"equity  {EQUITY.name}: {n_eq} names, {eq['rows']:,} rows, "
          f"{eq_span[0]} -> {eq_span[1]}, dead {dead} ({dead / n_eq:.1%})")
    print(f"etfs    {ETFS.name}: {len(etf['first'])} symbols, {etf['rows']:,} rows, "
          f"{etf_span[0]} -> {etf_span[1]}")
    print(f"[ASSERT] both fixtures share first and last bar -- the join R1 needs HOLDS")
    print(f"spanning the whole window: {len(full)} of {len(etf['first'])}\n")
    for role, got in roles.items():
        have = [s for s, v in got.items() if v]
        miss = [s for s, v in got.items() if not v]
        print(f"  {role:22} present {have}" + (f"  ABSENT {miss}" if miss else ""))
    print(f"\nhead of the ETF symbol list (the CEF observation, NOT classified here):")
    print("  " + " ".join(sorted(etf["first"])[:40]))
    print(f"\nwritten {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
