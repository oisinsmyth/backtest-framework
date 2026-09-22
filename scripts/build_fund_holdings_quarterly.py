"""D620 — the quarterly Schedule of Investments of all six funds, parsed out of the filings.

    uv run python scripts/build_fund_holdings_quarterly.py --build     # 231 filings -> fixture + meta
    uv run python scripts/build_fund_holdings_quarterly.py --gates     # G1..G6 on the committed fixture
    uv run python scripts/build_fund_holdings_quarterly.py --one ACC   # parse one accession, print the rows
    uv run python scripts/build_fund_holdings_quarterly.py --selftest  # every guard proved to RAISE

Data layer only: **no return is computed and nothing is scored.**

WHAT THIS IS FOR. [D619] established that the six funds file **zero N-PORT** and that the only
free historical holdings route is the **Schedule of Investments inside the quarterly 10-Q and the
annual 10-K**, at a 40-90 day lag. [D620]'s `fetch_fund_filings.py` recorded all 231 of them. This
turns them into rows.

A PERIOD THAT CANNOT BE PARSED IS WRITTEN DOWN, NEVER SKIPPED
-------------------------------------------------------------
Eighteen years of HTML across two filing agents and three index-sponsor renames is not one table
shape, and a parser that quietly returns fewer rows on the eras it does not understand produces a
fixture whose coverage is a fact about the parser rather than about the funds. So every
`(accession, fund, period_end)` the index says should exist and that yields no derivative lines
is written as a row with `kind="unparsed"` and a `reason`, the meta counts them per fund and per
era, and `f_fut` on such a row is null rather than zero. **The failure is in the data, not in the
silence.**

THE THREE THINGS THE DOCUMENTS SAY THAT A SUMMARY WOULD HAVE LOST
------------------------------------------------------------------
1. **UNG's share count is RESTATED backwards through a reverse split.** The FY2023 10-K footnotes
   *"On January 23, 2024 there was a 1-for-4 reverse share split ... adjusted ... on a retroactive
   basis"* against a 2023-12-31 count of 47,821,147. The count a reader had ON 2023-12-31 was four
   times it. Every row therefore carries `source_accession` and `filed_date`, all restatements are
   kept, and `project_fund_panel.py` anchors on the FIRST publication of a period, never the
   latest. Deposit §3.1 line 70: *"Never back-fill today's composition across history."*
2. **The early USCF Condensed Schedule of Investments has no notional column at all** — 2008 reads
   `Crude Oil Futures contracts, expires May 2008  7,122  $ (13,349,470)  (1.84)`, which is
   contracts, unrealized gain, and percent of partners' capital. `notional_usd` is null there and
   `f_fut` is therefore null too, rather than being silently computed off the unrealized column.
3. **The month a line names is not the same word in the two families.** USCF writes
   `NG August 2026 contracts, expiring July 2026` — delivery month and expiry month, separately.
   ProShares writes only `expires March 2025`, and the evidence that this is the DELIVERY month
   rather than the expiry is the June/December pattern of the Bloomberg Commodity Balanced index:
   UCO's three legs read March, June and December 2025, and a balanced index's deferred legs are
   the June and December CONTRACTS (which expire in May and November). Every row carries
   `month_basis` saying which of the two readings its `contract_month` came from, so a study that
   cares can filter on it instead of inheriting a guess.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import gzip
import hashlib
import html
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import Recorder  # noqa: E402
from backtest_framework.validation import frozen  # noqa: E402

JOB = "sec_fund_filings"
HOLDINGS_JOB = "proshares_holdings"
ROOT = REPO / "data" / "raw" / "recorder"
FIX = REPO / "data" / "fixtures"
OUT = FIX / "fund_holdings_quarterly.csv.gz"
META = FIX / "fund_holdings_quarterly.meta.json"

FUNDS = ("BOIL", "KOLD", "SCO", "UCO", "UNG", "USO")
ISSUER_FUNDS: dict[str, tuple[str, ...]] = {
    "proshares_trust_ii": ("BOIL", "KOLD", "SCO", "UCO"),
    "ung": ("UNG",),
    "uso": ("USO",),
}
#: Deposit §3.1 lines 58-63. Used ONLY to sign a futures line whose own table header does not say
#: long or short; the row then carries `sign_basis="fund_leverage_sign"` and says so.
LEVERAGE = {"BOIL": 2, "KOLD": -2, "UCO": 2, "SCO": -2, "UNG": 1, "USO": 1}

#: The four ProShares series have been renamed twice with the index sponsor (Dow Jones-AIG ->
#: DJ-UBS -> Bloomberg), so each is matched by an alias pattern rather than by a name.
#:
#: THE PATTERNS ARE MATCHED AGAINST THE NAME WITH EVERY SPACE REMOVED, and that is not
#: tidiness. One filing's heading reads `PROSHARES ULTR ASHORT BLOOMBERG CRUDE OIL` — the space
#: is in the wrong place inside ULTRASHORT — and a space-sensitive pattern drops that period of
#: SCO silently. It was found by the unmapped-series audit, not by inspection.
#:
#: Matching is `fullmatch`, which is what keeps ULTRA off ULTRASHORT and ULTRAPRO: after
#: `PROSHARESULTRA` the only things allowed are an optional sponsor and the commodity, so
#: `PROSHARESULTRAPRO3XCRUDEOIL` (OILU) and `PROSHARESULTRASHORTBLOOMBERGCRUDEOIL` (SCO) both
#: fail UCO's pattern.
PROSHARES_ALIASES: dict[str, str] = {
    "BOIL": r"PROSHARESULTRA(?:DJ-AIG|DJ-UBS|BLOOMBERG)?NATURALGAS",
    "KOLD": r"PROSHARESULTRASHORT(?:DJ-AIG|DJ-UBS|BLOOMBERG)?NATURALGAS",
    "UCO": r"PROSHARESULTRA(?:DJ-AIG|DJ-UBS|BLOOMBERG)?CRUDEOIL",
    "SCO": r"PROSHARESULTRASHORT(?:DJ-AIG|DJ-UBS|BLOOMBERG)?CRUDEOIL",
}

COLUMNS = (
    "period_end", "fund", "kind", "contract_month", "month_basis", "contracts", "notional_usd",
    "month_weight", "description", "counterparty", "shares_out", "net_assets", "nav_per_share",
    "f_fut", "n_fut_lines", "n_swap_lines", "n_months_held", "futures_notional_total",
    "swap_notional_total", "source_accession", "filed_date", "form", "issuer", "sign_basis",
    "reason",
)
KINDS = ("futures", "swap", "cash", "other", "unparsed")

HOLDOUT = (
    "HOLDINGS, SHARES AND NET ASSETS ONLY -- no return, no signal, no trade. Periods run "
    "2006-03-31..2026-06-30, which runs through the deposit's sealed vault window "
    "(2025-03-01..2026-09-18) and past this repository's 2024-01-01 holdout, neither of which "
    "the principal has reconciled with the other. Nothing here may score anything until that "
    "reconciliation is in writing (D604, D619, D620)."
)

MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ("january", "february", "march", "april", "may", "june", "july", "august",
         "september", "october", "november", "december")
    )
}

#: Whitespace the SEC's two filing agents use that `\s` does not match.
_INVISIBLE = "​    ⁠﻿"


class HoldingsError(RuntimeError):
    """A parse or a gate refused. Always loud."""


def P(*a: object) -> None:
    print(*a, flush=True)


# ----------------------------------------------------------------------------------- primitives
def flatten(body: bytes | str) -> str:
    """Filing HTML -> one line of text: tags out, entities resolved, whitespace collapsed.

    Entities ARE resolved here, unlike `fetch_fund_facts.text_of` which leaves them alone: that
    function exists for a human to `--grep`, and this one feeds regexes that have to see
    `Shareholders’ equity` as one token rather than `Shareholders&#8217; equity`."""
    text = body.decode("utf-8", errors="replace") if isinstance(body, (bytes, bytearray)) else body
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    for ch in _INVISIBLE:
        text = text.replace(ch, " ")
    return re.sub(r"\s+", " ", text)


def money(text: str | None, *, negative: bool = False) -> float | None:
    """`$ 431,110,215` -> 431110215.0; `( 29,339,198 )` -> -29339198.0; `—` and `-` -> None."""
    if text is None:
        return None
    s = str(text).strip().strip("$").strip()
    if s in {"", "—", "-", "–", "--"}:
        return None
    neg = negative or (s.startswith("(") and s.endswith(")"))
    s = s.strip("()").replace(",", "").replace("$", "").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    return -float(s) if neg else float(s)


def _num(value: object) -> float:
    """A parsed row's numeric field as a float. The row dicts are `dict[str, object]` because
    they also carry strings, and `float(object)` is not something a type checker will take."""
    return float(str(value))


def month_key(mon: str, year: str) -> str:
    """`March`, `2025` -> `2025-03`. RAISES on a month name this parser does not know, because a
    silently dropped contract month is a holdings row that says the fund held nothing."""
    m = MONTHS.get(mon.strip().lower())
    if m is None:
        raise HoldingsError(f"unknown month name {mon!r}")
    return f"{int(year):04d}-{m:02d}"


def cme_code_month(code: str, period_end: str) -> str:
    """`CLX2` held at `2012-09-30` -> `2012-11`.

    The CME code carries one year DIGIT, so the decade comes from the period the contract is held
    at: the candidate year is the period's decade plus that digit, pushed forward ten years if it
    would put the contract before the period. A futures fund does not hold a contract that has
    already expired, and the alternative — reading the last-trading-date field beside the code —
    is the fund's own field and not the delivery month."""
    m = re.fullmatch(r"(?P<root>[A-Z]{1,3})(?P<mon>[FGHJKMNQUVXZ])(?P<yr>\d{1,2})", code)
    if m is None:
        raise HoldingsError(f"{code!r} is not a CME outright code")
    month = _MONTH_CODES.index(m.group("mon")) + 1
    digits = m.group("yr")
    py, pm = int(period_end[:4]), int(period_end[5:7])
    if len(digits) == 2:
        year = 2000 + int(digits)
    else:
        year = py - (py % 10) + int(digits)
        if (year, month) < (py, pm):
            year += 10
    return f"{year:04d}-{month:02d}"


def iso_date(mon: str, day: str, year: str) -> str:
    m = MONTHS.get(mon.strip().lower())
    if m is None:
        raise HoldingsError(f"unknown month name {mon!r}")
    return dt.date(int(year), m, int(day)).isoformat()


# ---------------------------------------------------------------------- the ProShares filing shape
_PS_BOUNDARY = re.compile(
    r"PROSHARES [A-Z0-9&,\.'\-/ ]{3,70}?"
    r"(?:SCHEDULE OF INVESTMENTS|STATEMENTS? OF |FINANCIAL HIGHLIGHTS|NOTES TO )"
)
_PS_SOI = re.compile(
    r"(?P<name>PROSHARES [A-Z0-9&,\.'\-/ ]{3,70}?) SCHEDULE OF INVESTMENTS "
    r"(?P<mon>[A-Z]+) (?P<day>\d{1,2}), (?P<yr>\d{4})"
)
_PS_SFC = re.compile(
    r"(?P<name>PROSHARES [A-Z0-9&,\.'\-/ ]{3,70}?) STATEMENTS? OF FINANCIAL CONDITION"
)
_PS_FUT_BLOCK = re.compile(r"Futures Contracts (?P<side>Purchased|Sold)")
_PS_FUT_ROW = re.compile(
    # The dash between the commodity and the exchange is a hyphen in most years and an EN DASH
    # in the 2009-2010 filings ("Crude Oil – NYMEX"). Both, plus the em dash, or the block's
    # zero-row guard fires on a document that is perfectly well formed.
    # The comma after the exchange is optional too: 2017 reads `Natural Gas—NYMEX September 2017`.
    r"(?P<desc>[A-Za-z][A-Za-z0-9&\.'/ ]{1,60}?)\s*[-–—]\s*(?P<exch>[A-Za-z][A-Za-z ]{1,24}?),?\s*"
    # `expires` is optional: the 2015-2017 filings write `Natural Gas - NYMEX, May 2016` with no
    # verb at all, and which of the two wordings was used is carried into `month_basis`.
    r"(?P<verb>expires\s+)?(?P<mon>[A-Z][a-z]+)\s+(?P<yr>\d{4})\s+(?P<c>[\d,]+)\s+\$?\s*(?P<n>[\d,]+)"
)
#: The 2011-2013 filings name the contract by its CME code instead of a month word:
#: `WTI Crude Future 11/15/2012 (CLX2) 899 $ 82,878,810`. The code is the exact delivery month
#: and is preferred to the date beside it, which is the fund's own last-trading-date field.
_PS_FUT_ROW_CODE = re.compile(
    # The date tolerates internal spaces: the 2012 natural-gas rows read `11/15/ 2012`, which is
    # a tag boundary inside the cell showing through the flattening.
    r"(?P<desc>[A-Za-z][A-Za-z0-9&\.'/ ]{1,60}?)\s+\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{2,4}\s*"
    r"\((?P<code>[A-Z]{1,3}[FGHJKMNQUVXZ]\d{1,2})\)\s+(?P<c>[\d,]+)\s+\$?\s*(?P<n>[\d,]+)"
)
#: Two swap wordings, one pattern. 2014-: `Swap agreement with Citibank, N.A. based on ... 01/08/24
#: $ 184,008,385`. 2009-2013: `DJ-UBS WTI Crude Oil Subindex Swap—Goldman Sachs International
#: 10/08/12 $ (60,694,381 )`, where the parentheses are a SHORT swap and are captured as the sign.
_PS_SWAP_ROW = re.compile(
    r"(?:Swap agreements? (?:with|linked to) |Swap\s*[—–\-]\s*)(?P<cp>[A-Za-z][^$]{2,160}?)\s"
    r"(?P<exp>\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{2,4})\s\$?\s*(?P<neg>\()?\s*(?P<n>[\d,]+)"
)
_MONTH_CODES = "FGHJKMNQUVXZ"
_PS_CASH = re.compile(
    r"Total short-term U\.S\. government (?:and )?agency obligations(?: \(cost \$ [\d,]+ \))?\s*\$\s*(?P<v>[\d,]+)"
)
_PS_SHARES = re.compile(r"Shares outstanding(?: \(Note \d\))?\s+(?P<a>[\d,]+)(?:\s+(?P<b>[\d,]+))?")
_PS_NAV = re.compile(
    r"Net asset value per share(?: \(Note \d\))?\s+\$\s*(?P<a>[\d,\.]+)(?:\s+\$?\s*(?P<b>[\d,\.]+))?"
)
_PS_EQUITY = re.compile(
    r"(?:Total s|S)hareholders['’] equity\s+\$?\s*(?P<a>[\d,]+)(?:\s+\$?\s*(?P<b>[\d,]+))?"
)
_DATE_IN_HEADER = re.compile(r"(?P<mon>[A-Z][a-z]+) (?P<day>\d{1,2}), (?P<yr>\d{4})")
#: The flattened text runs the column header straight into the first row, so the first futures
#: line of a ProShares block reads `... (Depreciation)/Value Natural Gas - NYMEX, expires ...` and
#: the description regex, which scans left to right, starts on the header's last word. Stripped
#: here rather than by tightening the row pattern, because the header wording has changed twice
#: and a pattern that encodes it would break on the next change instead of on this list.
_PS_DESC_LEAD = re.compile(r"^(?:Value|Contracts|Amount at Value|Depreciation\)/Value)\s+")


def _sections(text: str, header: re.Pattern[str], boundary: re.Pattern[str]) -> list[tuple[re.Match[str], str]]:
    """Every `header` match paired with the text from its end to the next boundary."""
    cuts = sorted({m.start() for m in boundary.finditer(text)} | {len(text)})
    out = []
    for m in header.finditer(text):
        end = next((c for c in cuts if c > m.end()), len(text))
        out.append((m, text[m.end() : end]))
    return out


def _proshares_fund(name: str) -> str | None:
    """A series name -> its ticker, or None for one of the trust's other twelve series."""
    flat = re.sub(r"\s+", "", name)
    hits = [f for f, pat in PROSHARES_ALIASES.items() if re.fullmatch(pat, flat)]
    if len(hits) > 1:  # pragma: no cover - the aliases are mutually exclusive by construction
        raise HoldingsError(f"series name {name!r} matches more than one fund: {hits}")
    return hits[0] if hits else None


def _merge_anchor(
    anchors: dict[tuple[str, str], dict[str, float]],
    key: tuple[str, str],
    **values: float | None,
) -> None:
    """Keep the FIRST non-null value each field gets inside one filing, never the last.

    Both filing families repeat the phrase "Statements of Financial Condition" in the index at
    the front and again in the notes, and a section-walk therefore finds three matches where one
    carries the table. Replacing on every match let a later partial match — the notes, which
    restate total partners' capital and nothing else — blank out the share count that the real
    table had already supplied. Measured on USO's 2022-06-30 10-Q: the comparative 2021-12-31
    column came out with `net_assets` and a null `shares_out`, which is exactly the shape a
    projection anchor must never have."""
    slot = anchors.setdefault(key, {})
    for name, value in values.items():
        if value is not None:
            slot.setdefault(name, value)
    if not slot:
        anchors.pop(key, None)


def _two_dates(text: str, limit: int = 200) -> list[str]:
    """The (up to two) period dates a Statements-of-Financial-Condition header carries."""
    seen: list[str] = []
    for m in _DATE_IN_HEADER.finditer(text[:limit]):
        d = iso_date(m.group("mon"), m.group("day"), m.group("yr"))
        if d not in seen:
            seen.append(d)
    return seen[:2]


def parse_proshares(text: str) -> tuple[dict[tuple[str, str], list[dict[str, object]]], dict[tuple[str, str], dict[str, float]], set[str]]:
    """One ProShares Trust II filing -> (lines, anchors, series names seen).

    The third return value is the audit that makes a rename impossible to miss: every
    `PROSHARES ... SCHEDULE OF INVESTMENTS` header in the document is returned whether or not it
    maps to one of the four funds, so a future `PROSHARES ULTRA <NEWSPONSOR> NATURAL GAS` shows up
    as an unmapped series rather than as BOIL quietly losing a quarter."""
    lines: dict[tuple[str, str], list[dict[str, object]]] = {}
    anchors: dict[tuple[str, str], dict[str, float]] = {}
    seen: set[str] = set()

    for m, body in _sections(text, _PS_SOI, _PS_BOUNDARY):
        seen.add(m.group("name").strip())
        fund = _proshares_fund(m.group("name"))
        if fund is None:
            continue
        period = iso_date(m.group("mon"), m.group("day"), m.group("yr"))
        rows: list[dict[str, object]] = []
        blocks = list(_PS_FUT_BLOCK.finditer(body))
        for i, blk in enumerate(blocks):
            stop = blocks[i + 1].start() if i + 1 < len(blocks) else len(body)
            chunk = body[blk.end() : stop]
            sign = 1 if blk.group("side") == "Purchased" else -1
            found = 0
            for r in _PS_FUT_ROW.finditer(chunk):
                rows.append(
                    {
                        "kind": "futures",
                        "contract_month": month_key(r.group("mon"), r.group("yr")),
                        "month_basis": "expires_label" if r.group("verb") else "stated_contract",
                        "contracts": sign * float(r.group("c").replace(",", "")),
                        "notional_usd": sign * float(r.group("n").replace(",", "")),
                        "description": f"{_PS_DESC_LEAD.sub('', r.group('desc').strip())} - "
                                       f"{r.group('exch').strip()}",
                        "counterparty": "",
                        "sign_basis": "block_header",
                    }
                )
                found += 1
            if found == 0:
                for r in _PS_FUT_ROW_CODE.finditer(chunk):
                    rows.append(
                        {
                            "kind": "futures",
                            "contract_month": cme_code_month(r.group("code"), period),
                            "month_basis": "cme_code",
                            "contracts": sign * float(r.group("c").replace(",", "")),
                            "notional_usd": sign * float(r.group("n").replace(",", "")),
                            "description": _PS_DESC_LEAD.sub("", r.group("desc").strip()),
                            "counterparty": "",
                            "sign_basis": "block_header",
                        }
                    )
                    found += 1
            if found == 0:
                raise HoldingsError(
                    f"a 'Futures Contracts {blk.group('side')}' block yielded ZERO rows in "
                    f"{len(chunk):,} characters. The row shape has moved and dropping the block "
                    f"silently would read as a fund holding no futures: {chunk[:200]!r}"
                )
        for r in _PS_SWAP_ROW.finditer(body):
            value = float(r.group("n").replace(",", ""))
            rows.append(
                {
                    "kind": "swap",
                    "contract_month": "",
                    "month_basis": "",
                    "contracts": np.nan,
                    "notional_usd": -value if r.group("neg") else value,
                    "description": "total return swap",
                    "counterparty": re.sub(r"\s+based on.*$", "", r.group("cp")).strip()[:80],
                    "sign_basis": "printed_sign",
                }
            )
        cash = _PS_CASH.search(body)
        if cash is not None:
            rows.append(
                {
                    "kind": "cash",
                    "contract_month": "",
                    "month_basis": "",
                    "contracts": np.nan,
                    "notional_usd": float(cash.group("v").replace(",", "")),
                    "description": "short-term U.S. government and agency obligations",
                    "counterparty": "",
                    "sign_basis": "printed_sign",
                }
            )
        if rows:
            lines.setdefault((fund, period), [])
            if len(rows) > len(lines[(fund, period)]):
                lines[(fund, period)] = rows

    for m, body in _sections(text, _PS_SFC, _PS_BOUNDARY):
        fund = _proshares_fund(m.group("name"))
        if fund is None:
            continue
        dates = _two_dates(body)
        sh, nav, eq = _PS_SHARES.search(body), _PS_NAV.search(body), _PS_EQUITY.search(body)
        for i, period in enumerate(dates):
            g = "a" if i == 0 else "b"
            _merge_anchor(
                anchors, (fund, period),
                shares_out=money(sh.group(g)) if sh else None,
                nav_per_share=money(nav.group(g)) if nav else None,
                net_assets=money(eq.group(g)) if eq else None,
            )
    return lines, anchors, seen


# --------------------------------------------------------------------------- the USCF filing shape
_US_BOUNDARY = re.compile(
    r"(?:Condensed )?(?:Schedules? of Investments?|Statements? of Financial Condition|"
    r"Statements? of Operations|Statements? of Changes|Statements? of Cash Flows|"
    r"Notes to (?:Condensed )?Financial Statements)"
)
_US_SOI = re.compile(
    r"(?:Condensed )?Schedules? of Investments?(?: \(Unaudited\))? [Aa]t "
    r"(?P<mon>[A-Z][a-z]+) (?P<day>\d{1,2}), (?P<yr>\d{4})"
)
_US_SFC = re.compile(r"(?:Condensed )?Statements? of Financial Condition(?: \(Unaudited\))? [Aa]t ")
_US_LONG_SHORT = re.compile(r"Open (?:Commodity )?Futures Contracts(?:\s*[-–—]\s*(?P<side>Long|Short))?")
#: THE USCF SCHEDULE HAS FOUR ROW SHAPES AND THE COLUMN ORDER IS NOT THE SAME IN ALL OF THEM.
#: Whether a notional column exists at all is a property of the ERA, not of the row, so it is read
#: once per section from the table's own header and then the matching pattern is used:
#:
#:   2016-2026, notional present, DELIVERY MONTH NAMED
#:     `NYMEX WTI Crude Oil Futures CL August 2022 contracts, expiring July 2022 $ 431,110,215 4,366`
#:   2013-2015, NO notional, delivery month named
#:     `NYMEX WTI Crude Oil Futures CL May 2014 contracts, expiring April 2014* 5,407 $ 6,379,700`
#:   2008-2012, NO notional, only the expiry month
#:     `Crude Oil Futures contracts, expires May 2008  7,122  $ (13,349,470 ) (1.84 )`
#:
#: In the two no-notional eras the second money column is the UNREALIZED GAIN, and it is dropped
#: rather than written into `notional_usd`: a gain in a notional column would make `f_fut` a
#: number computed from two different quantities and it would look perfectly reasonable.
_US_FUT_NOTIONAL = re.compile(
    r"(?P<desc>[A-Za-z][A-Za-z0-9 \.\-]{2,60}?) (?P<mon>[A-Z][a-z]+) (?P<yr>\d{4}) contracts?, "
    r"expir\w+ [A-Z][a-z]+ \d{4}\s*\*?\s*\$?\s*(?P<n>[\d,]+)\s+(?P<c>[\d,]+)"
)
_US_FUT_MONTH_ONLY = re.compile(
    r"(?P<desc>[A-Za-z][A-Za-z0-9 \.\-]{2,60}?) (?P<mon>[A-Z][a-z]+) (?P<yr>\d{4}) contracts?, "
    r"expir\w+ [A-Z][a-z]+ \d{4}\s*\*?\s+(?P<c>[\d,]+)\s+\$?\s*\(?\s*[\d,]+"
)
_US_FUT_OLD = re.compile(
    # `expire`, `expires` and `expiring` all occur.
    r"(?P<desc>[A-Za-z][A-Za-z0-9 \.\-]{2,60}?) contracts?, expir\w* (?P<mon>[A-Z][a-z]+) "
    r"(?P<yr>\d{4})\s*\*?\s+(?P<c>[\d,]+)\s+\$?\s*\(?\s*[\d,]+"
)
_US_SWAP_ROW = re.compile(
    r"(?P<cp>[A-Za-z][A-Za-z\.,&' ]{2,60}?) (?:Monthly|monthly|Quarterly|quarterly|Daily|daily|"
    r"Weekly|weekly) (?P<exp>\d{2}/\d{2}/\d{4})\s+\$?\s*(?P<neg>\()?\s*(?P<n>[\d,]+)"
)
_US_CASH = re.compile(
    r"Total (?:United States Money Market Funds|Money Market Funds|Cash Equivalents|"
    r"Cash and Cash Equivalents)\s+\$?\s*(?P<v>[\d,]+)"
)
#: `(?:\s*#)?` and NOT `\s*#?`. The footnote marker is optional and the space before the SECOND
#: column is not: written `\s*#?`, the `\s*` eats the separator whether or not a `#` follows, the
#: optional second group can then never match its own leading `\s+`, and the comparative column
#: comes back None on every USCF filing. Caught by the hand file, which types both columns out.
_US_SHARES = re.compile(
    r"Limited Partners['’] (?:units|shares) outstanding\s+(?P<a>[\d,]+)(?:\s*#)?(?:\s+(?P<b>[\d,]+))?"
)
_US_NAV = re.compile(
    r"Net asset value per (?:unit|share)\s+\$\s*(?P<a>[\d,\.]+)(?:\s*#)?(?:\s+\$?\s*(?P<b>[\d,\.]+))?"
)
_US_CAPITAL = re.compile(
    r"Total Partners['’] [Cc]apital\s+\$?\s*(?P<a>[\d,]+)(?:\s+\$?\s*(?P<b>[\d,]+))?"
)


def parse_uscf(text: str, fund: str) -> tuple[dict[tuple[str, str], list[dict[str, object]]], dict[tuple[str, str], dict[str, float]]]:
    """One USO or UNG filing -> (lines, anchors). Single-series registrants, so no name walk."""
    lines: dict[tuple[str, str], list[dict[str, object]]] = {}
    anchors: dict[tuple[str, str], dict[str, float]] = {}
    default_sign = 1 if LEVERAGE[fund] > 0 else -1

    for m, body in _sections(text, _US_SOI, _US_BOUNDARY):
        period = iso_date(m.group("mon"), m.group("day"), m.group("yr"))
        rows: list[dict[str, object]] = []
        blocks = list(_US_LONG_SHORT.finditer(body))
        for i, blk in enumerate(blocks):
            stop = blocks[i + 1].start() if i + 1 < len(blocks) else len(body)
            chunk = body[blk.end() : stop]
            side = blk.group("side")
            sign = default_sign if side is None else (1 if side == "Long" else -1)
            basis = "fund_leverage_sign" if side is None else "block_header"
            has_notional = "Notional" in body[: blk.end()]
            shapes: tuple[tuple[re.Pattern[str], str, bool], ...]
            if has_notional:
                shapes = ((_US_FUT_NOTIONAL, "stated_contract", True),)
            else:
                shapes = ((_US_FUT_MONTH_ONLY, "stated_contract", False),
                          (_US_FUT_OLD, "expires_label", False))
            for pattern, month_basis, with_notional in shapes:
                found = 0
                for r in pattern.finditer(chunk):
                    rows.append(
                        {
                            "kind": "futures",
                            "contract_month": month_key(r.group("mon"), r.group("yr")),
                            "month_basis": month_basis,
                            "contracts": sign * float(r.group("c").replace(",", "")),
                            "notional_usd": (
                                sign * float(r.group("n").replace(",", "")) if with_notional else np.nan
                            ),
                            "description": r.group("desc").strip(),
                            "counterparty": "",
                            "sign_basis": basis,
                        }
                    )
                    found += 1
                if found:
                    break
        swap_at = body.find("Open OTC Commodity Swap Contracts")
        if swap_at >= 0:
            for r in _US_SWAP_ROW.finditer(body[swap_at:]):
                value = float(r.group("n").replace(",", ""))
                rows.append(
                    {
                        "kind": "swap",
                        "contract_month": "",
                        "month_basis": "",
                        "contracts": np.nan,
                        "notional_usd": -value if r.group("neg") else value,
                        "description": "OTC commodity swap",
                        "counterparty": r.group("cp").strip()[:80],
                        "sign_basis": "printed_sign",
                    }
                )
        cash = _US_CASH.search(body)
        if cash is not None:
            rows.append(
                {
                    "kind": "cash",
                    "contract_month": "",
                    "month_basis": "",
                    "contracts": np.nan,
                    "notional_usd": float(cash.group("v").replace(",", "")),
                    "description": "United States money market funds",
                    "counterparty": "",
                    "sign_basis": "printed_sign",
                }
            )
        if rows:
            lines.setdefault((fund, period), [])
            if len(rows) > len(lines[(fund, period)]):
                lines[(fund, period)] = rows

    for m, body in _sections(text, _US_SFC, _US_BOUNDARY):
        dates = _two_dates(body)
        sh, nav, cap = _US_SHARES.search(body), _US_NAV.search(body), _US_CAPITAL.search(body)
        for i, period in enumerate(dates):
            g = "a" if i == 0 else "b"
            _merge_anchor(
                anchors, (fund, period),
                shares_out=money(sh.group(g)) if sh else None,
                nav_per_share=money(nav.group(g)) if nav else None,
                net_assets=money(cap.group(g)) if cap else None,
            )
    return lines, anchors


# ------------------------------------------------------------------------------ one filing -> rows
def rows_for_filing(
    text: str,
    *,
    issuer: str,
    accession: str,
    filed: str,
    form: str,
    report_date: str,
) -> tuple[list[dict[str, object]], set[str]]:
    """Every row one filing contributes, including the `unparsed` ones."""
    if issuer == "proshares_trust_ii":
        lines, anchors, seen = parse_proshares(text)
    elif issuer in ("uso", "ung"):
        fund = ISSUER_FUNDS[issuer][0]
        lines, anchors = parse_uscf(text, fund)
        seen = set()
    else:  # pragma: no cover - ISSUER_FUNDS is the whole universe
        raise HoldingsError(f"no filing shape for issuer {issuer!r}")

    base = {
        "source_accession": accession,
        "filed_date": filed,
        "form": form,
        "issuer": issuer,
    }
    out: list[dict[str, object]] = []
    keys = sorted(set(lines) | set(anchors))
    for fund, period in keys:
        group = lines.get((fund, period), [])
        anchor = anchors.get((fund, period), {})
        fut = [r for r in group if r["kind"] == "futures"]
        swp = [r for r in group if r["kind"] == "swap"]
        fut_n = [abs(_num(r["notional_usd"])) for r in fut if pd.notna(r["notional_usd"])]
        swp_n = [abs(_num(r["notional_usd"])) for r in swp if pd.notna(r["notional_usd"])]
        fut_total = float(sum(fut_n)) if len(fut_n) == len(fut) and fut else np.nan
        swp_total = float(sum(swp_n)) if len(swp_n) == len(swp) else np.nan
        if np.isfinite(fut_total) and np.isfinite(swp_total) and (fut_total + swp_total) > 0:
            f_fut = fut_total / (fut_total + swp_total)
        else:
            f_fut = np.nan
        months = sorted({str(r["contract_month"]) for r in fut if r["contract_month"]})
        derived = {
            "shares_out": anchor.get("shares_out", np.nan),
            "net_assets": anchor.get("net_assets", np.nan),
            "nav_per_share": anchor.get("nav_per_share", np.nan),
            "f_fut": f_fut,
            "n_fut_lines": len(fut),
            "n_swap_lines": len(swp),
            "n_months_held": len(months),
            "futures_notional_total": fut_total,
            "swap_notional_total": swp_total,
        }
        if not group:
            out.append(
                {
                    "period_end": period, "fund": fund, "kind": "unparsed", "contract_month": "",
                    "month_basis": "", "contracts": np.nan, "notional_usd": np.nan,
                    "month_weight": np.nan, "description": "", "counterparty": "",
                    "reason": "anchors only: this filing's Statements of Financial Condition "
                              "carries this period (it is the comparative column, or the notes) "
                              "and no Schedule of Investments section for it",
                    **derived, **base,
                }
            )
            continue
        for r in group:
            weight = np.nan
            if r["kind"] == "futures" and np.isfinite(fut_total) and fut_total > 0 and pd.notna(r["notional_usd"]):
                weight = abs(_num(r["notional_usd"])) / fut_total
            backward = (
                r["kind"] == "futures"
                and str(r["contract_month"])
                and str(r["contract_month"]) < period[:7]
            )
            out.append({
                **r, "period_end": period, "fund": fund, "month_weight": weight,
                "reason": (
                    "the filing states a contract month before its own period end; transcribed "
                    "as filed, not corrected"
                ) if backward else "",
                **derived, **base,
            })

    expected = ISSUER_FUNDS[issuer]
    present = {f for f, _ in keys}
    for fund in expected:
        if fund in present:
            continue
        out.append(
            {
                "period_end": report_date or "", "fund": fund, "kind": "unparsed",
                "contract_month": "", "month_basis": "", "contracts": np.nan,
                "notional_usd": np.nan, "month_weight": np.nan, "description": "",
                "counterparty": "", "shares_out": np.nan, "net_assets": np.nan,
                "nav_per_share": np.nan, "f_fut": np.nan, "n_fut_lines": 0, "n_swap_lines": 0,
                "n_months_held": 0, "futures_notional_total": np.nan,
                "swap_notional_total": np.nan, "sign_basis": "",
                "reason": f"no section for {fund} anywhere in this filing "
                          f"({len(text):,} characters of text)",
                **base,
            }
        )
    return out, seen


# ------------------------------------------------------------------------------------- the build
def _index(rec: Recorder) -> list[dict[str, str]]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("fetch_fund_filings", REPO / "scripts" / "fetch_fund_filings.py")
    if spec is None or spec.loader is None:  # pragma: no cover
        raise HoldingsError("cannot load scripts/fetch_fund_filings.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fetch_fund_filings"] = mod
    spec.loader.exec_module(mod)
    return mod.plan(rec)  # type: ignore[no-any-return]


def build(root: Path = ROOT) -> tuple[pd.DataFrame, dict[str, object]]:
    rec = Recorder(root)
    index = _index(rec)
    have = {r.key: r for r in rec.records(JOB, verify=False)}
    jdir = rec.job_dir(JOB)
    rows: list[dict[str, object]] = []
    seen_series: set[str] = set()
    missing: list[str] = []
    for f in index:
        got = have.get(f["accession"])
        if got is None:
            missing.append(f["accession"])
            continue
        text = flatten((jdir / got.path).read_bytes())
        got_rows, seen = rows_for_filing(
            text, issuer=f["issuer"], accession=f["accession"], filed=f["filed"],
            form=f["form"], report_date=f["period_end"],
        )
        rows.extend(got_rows)
        seen_series |= seen
    if missing:
        raise HoldingsError(
            f"{len(missing)} filings in the index are not recorded, e.g. {missing[:3]}. "
            f"Run `scripts/fetch_fund_filings.py --documents` first; this builder never fetches."
        )
    frame = pd.DataFrame(rows, columns=list(COLUMNS))
    frame = frame.sort_values(["fund", "period_end", "source_accession", "kind", "contract_month", "counterparty"])
    frame = frame.reset_index(drop=True)
    prov = {
        "filings_read": len(index),
        "series_names_seen": sorted(seen_series),
        "unmapped_series": sorted(s for s in seen_series if _proshares_fund(s) is None),
    }
    return frame, prov


# ------------------------------------------------------------------------------------- the gates
def gate_kinds(frame: pd.DataFrame) -> dict[str, object]:
    """G0. Every `kind` is one of the five declared, and every `unparsed` row states a reason."""
    bad = sorted(set(frame["kind"]) - set(KINDS))
    if bad:
        raise HoldingsError(f"G0: kinds {bad} are not in {KINDS}")
    un = frame[frame["kind"] == "unparsed"]
    silent = un[un["reason"].astype(str).str.strip() == ""]
    if len(silent):
        raise HoldingsError(
            f"G0: {len(silent)} unparsed rows carry no reason, e.g. "
            f"{silent[['fund', 'period_end', 'source_accession']].head(3).to_dict('records')}"
        )
    return {k: int((frame["kind"] == k).sum()) for k in KINDS}


def gate_f_fut(frame: pd.DataFrame) -> dict[str, object]:
    """G1. `f_fut` is in [0, 1] wherever it is not null."""
    v = pd.to_numeric(frame["f_fut"], errors="coerce")
    bad = frame[v.notna() & ((v < 0.0) | (v > 1.0))]
    if len(bad):
        raise HoldingsError(f"G1: {len(bad)} rows have f_fut outside [0,1], e.g. {bad['f_fut'].head(3).tolist()}")
    fin = v[v.notna()]
    return {
        "rows_with_f_fut": int(fin.size),
        "min": float(fin.min()) if fin.size else None,
        "max": float(fin.max()) if fin.size else None,
        "rows_null": int(v.isna().sum()),
    }


#: G2's allowance. A backward contract month is either a SOURCE typo, of which there is exactly
#: one in eighteen years, or a column/pattern error in this parser, which would produce them in
#: bulk. The gate therefore prices the second and reports the first rather than refusing to build
#: over one bad sentence in one 10-Q.
BACKWARD_MONTH_MAX_SHARE = 0.01


def gate_months_forward(frame: pd.DataFrame) -> dict[str, object]:
    """G2. A held contract month is essentially never before the period it is held at.

    USO's 2013-09-30 10-Q (`0001144204-13-060424`) states *"NYMEX WTI Crude Oil Futures CL August
    2013 contracts, expiring July 2013"* in the September schedule — a contract that had already
    expired. That is the document, not the parse, and the row is transcribed as filed with a
    `reason` on it. What this gate is actually for is the systematic version: a column read in
    the wrong order, or the expiry month taken for the delivery month, would put a large SHARE of
    rows backwards, and that raises."""
    m = frame[(frame["kind"] == "futures") & (frame["contract_month"].astype(str) != "")]
    bad = m[m["contract_month"].astype(str) < m["period_end"].astype(str).str.slice(0, 7)]
    share = len(bad) / max(len(m), 1)
    if share > BACKWARD_MONTH_MAX_SHARE:
        raise HoldingsError(
            f"G2: {len(bad)} of {len(m)} futures rows ({share:.2%}, bar "
            f"{BACKWARD_MONTH_MAX_SHARE:.0%}) name a contract month before their period end. At "
            f"this share it is the parse and not the filings: "
            f"{bad[['fund', 'period_end', 'contract_month']].head(5).to_dict('records')}"
        )
    return {
        "futures_rows_checked": int(len(m)),
        "backward_rows": int(len(bad)),
        "backward_share": round(share, 6),
        "backward": bad[["fund", "period_end", "contract_month", "source_accession"]].to_dict("records"),
    }


def gate_no_duplicates(frame: pd.DataFrame) -> dict[str, object]:
    """G3. One line per (accession, fund, period, kind, month, counterparty, description)."""
    keys = ["source_accession", "fund", "period_end", "kind", "contract_month", "counterparty", "description"]
    dup = frame.duplicated(keys, keep=False)
    if dup.any():
        raise HoldingsError(
            f"G3: {int(dup.sum())} duplicate lines, e.g. {frame.loc[dup, keys].head(3).to_dict('records')}"
        )
    return {"duplicate_rows": 0}


def gate_year_coverage(frame: pd.DataFrame) -> dict[str, object]:
    """G4. Every fund has at least one PARSED row in every calendar year of its filing life.

    The life is read from the fund's own rows, not assumed: first parsed period to last. A year
    inside that span with no parsed row is an era this parser does not understand and the gate
    says which year, rather than the fixture being quietly short."""
    out: dict[str, object] = {}
    for fund in sorted(frame["fund"].unique()):
        g = frame[(frame["fund"] == fund) & (frame["kind"] != "unparsed")]
        if g.empty:
            raise HoldingsError(f"G4: {fund} has no parsed row at all")
        years = {int(str(p)[:4]) for p in g["period_end"]}
        span = range(min(years), max(years) + 1)
        gaps = sorted(y for y in span if y not in years)
        if gaps:
            raise HoldingsError(
                f"G4: {fund} has no parsed holdings row in {gaps} inside its own span "
                f"{min(years)}..{max(years)}"
            )
        out[fund] = {"first_year": min(years), "last_year": max(years), "years": len(years),
                     "parsed_rows": int(len(g))}
    return out


def gate_known_answer(frame: pd.DataFrame, root: Path = ROOT) -> dict[str, object]:
    """G5. The latest 10-Q's split agrees IN KIND with the live holdings page D619 recorded.

    D619 measured UCO at `f_fut_derivatives` 0.249 and SCO at 1.000 on 2026-09-18 off the
    issuer's own page — a completely different document, fetched from a different host, parsed by
    different code. If this filing parser says UCO is all futures, or SCO holds swaps, one of the
    two is wrong and the disagreement is the finding. The check is on the KIND split rather than
    on the number: the filing is 2026-06-30 and the page is 2026-09-18, and a fund's swap share
    moves between them."""
    out: dict[str, object] = {}
    for fund, expect_swap in (("UCO", True), ("SCO", False)):
        g = frame[(frame["fund"] == fund) & (frame["kind"] != "unparsed")]
        if g.empty:
            raise HoldingsError(f"G5: no parsed row for {fund}")
        last = max(g["period_end"])
        q = g[g["period_end"] == last]
        n_swap = int((q["kind"] == "swap").sum())
        f_fut = pd.to_numeric(q["f_fut"], errors="coerce").dropna()
        got_swap = n_swap > 0
        if got_swap != expect_swap:
            raise HoldingsError(
                f"G5: {fund} at {last} parsed {n_swap} swap lines; D619's live page of 2026-09-18 "
                f"has {'swaps' if expect_swap else 'no swaps'} for this fund. One of the two "
                f"parsers is wrong and this fixture will not be written until it is known which."
            )
        out[fund] = {
            "period_end": last,
            "swap_lines": n_swap,
            "futures_lines": int((q["kind"] == "futures").sum()),
            "f_fut": float(f_fut.iloc[0]) if len(f_fut) else None,
            "months": sorted({str(x) for x in q.loc[q["kind"] == "futures", "contract_month"]}),
        }
    return out


GATES = (
    ("G0_kinds_and_reasons", gate_kinds),
    ("G1_f_fut_in_unit_interval", gate_f_fut),
    ("G2_contract_months_forward", gate_months_forward),
    ("G3_no_duplicate_lines", gate_no_duplicates),
    ("G4_year_coverage", gate_year_coverage),
    ("G5_known_answer_live_page", gate_known_answer),
)


def run_gates(frame: pd.DataFrame) -> dict[str, object]:
    return {name: fn(frame) for name, fn in GATES}


# ------------------------------------------------------------------------------------- selftest
def _good_frame() -> pd.DataFrame:
    rows = []
    for fund in FUNDS:
        for year in (2022, 2023):
            rows.append(
                {
                    "period_end": f"{year}-12-31", "fund": fund, "kind": "futures",
                    "contract_month": f"{year + 1}-03", "month_basis": "expires_label",
                    "contracts": 100.0, "notional_usd": 75.0, "month_weight": 1.0,
                    "description": "Natural Gas - NYMEX", "counterparty": "",
                    "shares_out": 1000.0, "net_assets": 20000.0, "nav_per_share": 20.0,
                    "f_fut": 0.75, "n_fut_lines": 1, "n_swap_lines": 1, "n_months_held": 1,
                    "futures_notional_total": 75.0, "swap_notional_total": 25.0,
                    "source_accession": f"0001-{year}-1", "filed_date": f"{year + 1}-02-28",
                    "form": "10-K", "issuer": "x", "sign_basis": "block_header", "reason": "",
                }
            )
            rows.append({**rows[-1], "kind": "swap", "contract_month": "", "notional_usd": 25.0,
                         "month_weight": np.nan, "counterparty": "Citibank", "description": "total return swap"})
    frame = pd.DataFrame(rows, columns=list(COLUMNS))
    frame.loc[frame["fund"] == "SCO", "n_swap_lines"] = 0
    frame = frame[~((frame["fund"] == "SCO") & (frame["kind"] == "swap"))].reset_index(drop=True)
    frame.loc[frame["fund"] == "SCO", "f_fut"] = 1.0
    return frame


def selftest() -> int:
    good = _good_frame()
    report = run_gates(good)
    f_fut_report = report["G1_f_fut_in_unit_interval"]
    assert isinstance(f_fut_report, dict)
    P(f"  OK   good frame: kinds {report['G0_kinds_and_reasons']}, "
      f"f_fut {f_fut_report['min']}..{f_fut_report['max']}")

    breaks: list[tuple[str, object]] = []

    def _bad_kind() -> object:
        bad = good.copy()
        bad.loc[0, "kind"] = "derivative"
        return gate_kinds(bad)

    def _unparsed_without_reason() -> object:
        bad = good.copy()
        bad.loc[0, "kind"] = "unparsed"
        return gate_kinds(bad)

    def _f_fut_above_one() -> object:
        bad = good.copy()
        bad.loc[0, "f_fut"] = 1.0000001
        return gate_f_fut(bad)

    def _month_behind_period() -> object:
        bad = good.copy()
        bad.loc[0, "contract_month"] = "2021-01"
        return gate_months_forward(bad)

    def _duplicate_line() -> object:
        bad = pd.concat([good, good.iloc[[0]]], ignore_index=True)
        return gate_no_duplicates(bad)

    def _year_gap() -> object:
        bad = good.copy()
        bad.loc[bad["fund"] == "BOIL", "period_end"] = bad.loc[bad["fund"] == "BOIL", "period_end"].replace(
            {"2022-12-31": "2019-12-31"}
        )
        return gate_year_coverage(bad)

    def _uco_without_swaps() -> object:
        bad = good[~((good["fund"] == "UCO") & (good["kind"] == "swap"))].reset_index(drop=True)
        return gate_known_answer(bad)

    def _sco_with_swaps() -> object:
        extra = good[good["fund"] == "UCO"].copy()
        extra["fund"] = "SCO"
        extra["source_accession"] = "0002-2023-1"
        return gate_known_answer(pd.concat([good, extra], ignore_index=True))

    def _unknown_month() -> object:
        return month_key("Smarch", "2025")

    def _futures_block_with_no_rows() -> object:
        return parse_proshares(
            "PROSHARES ULTRA BLOOMBERG NATURAL GAS SCHEDULE OF INVESTMENTS DECEMBER 31, 2023 "
            "Futures Contracts Purchased Number of Contracts Notional Amount at Value "
            "Natural Gas NYMEX expiring March 2024 62,768 1,460,611,360 "
            "PROSHARES ULTRA BLOOMBERG NATURAL GAS STATEMENTS OF OPERATIONS"
        )

    breaks += [
        ("G0 unknown kind", _bad_kind),
        ("G0 unparsed with no reason", _unparsed_without_reason),
        ("G1 f_fut above 1", _f_fut_above_one),
        ("G2 contract month before the period", _month_behind_period),
        ("G3 duplicate line", _duplicate_line),
        ("G4 a year with no parsed row", _year_gap),
        ("G5 UCO with no swap lines", _uco_without_swaps),
        ("G5 SCO carrying swap lines", _sco_with_swaps),
        ("parse: unknown month name", _unknown_month),
        ("parse: futures block yields no rows", _futures_block_with_no_rows),
    ]

    silent = 0
    for name, fn in breaks:
        try:
            fn()  # type: ignore[operator]
        except HoldingsError as exc:
            P(f"  RAISED {name}: {str(exc)[:88]}")
        else:
            silent += 1
            P(f"  DID NOT RAISE {name}  <-- a gate that cannot fire")
    P(f"  selftest: {len(breaks)} breaks, {len(breaks) - silent} fired, {silent} silent")
    return 1 if silent else 0


# ------------------------------------------------------------------------------------------ meta
REQUIRED_META_KEYS = (
    "spec", "record", "builder", "built_utc", "columns", "kinds", "rows", "funds", "gates",
    "coverage", "unparsed", "sha256", "date_col", "holdout", "conventions",
)


def coverage(frame: pd.DataFrame) -> dict[str, object]:
    out: dict[str, object] = {}
    for fund in sorted(frame["fund"].unique()):
        g = frame[frame["fund"] == fund]
        parsed = g[g["kind"] != "unparsed"]
        periods = sorted({str(p) for p in parsed["period_end"]})
        un = g[g["kind"] == "unparsed"]
        anchored = g[pd.to_numeric(g["shares_out"], errors="coerce").notna()]
        out[fund] = {
            "rows": int(len(g)),
            "parsed_rows": int(len(parsed)),
            "unparsed_rows": int(len(un)),
            "periods_with_holdings": len(periods),
            "first_period": periods[0] if periods else None,
            "last_period": periods[-1] if periods else None,
            "periods_with_an_anchor": len(sorted({str(p) for p in anchored["period_end"]})),
            # Periods whose FUTURES lines carry a notional. Not "any row with a number": a cash
            # line always has one, and the question this answers is whether `f_fut` and the
            # month weights exist for that period at all.
            "periods_with_futures_notional": len(
                {
                    str(p)
                    for p, k, n in zip(parsed["period_end"], parsed["kind"],
                                       pd.to_numeric(parsed["notional_usd"], errors="coerce"), strict=True)
                    if k == "futures" and pd.notna(n)
                }
            ),
        }
    return out


def write_outputs(frame: pd.DataFrame, prov: Mapping[str, object], gates: Mapping[str, object]) -> dict[str, object]:
    FIX.mkdir(parents=True, exist_ok=True)
    raw = frame.to_csv(index=False, encoding="utf-8", lineterminator="\n").encode("utf-8")
    with open(OUT, "wb") as fb, gzip.GzipFile(filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9) as gz:
        gz.write(raw)
    un = frame[frame["kind"] == "unparsed"]
    meta: dict[str, object] = {
        "spec": "D620; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.1 lines 56-70 (the fund universe, "
                "the panel schema and the point-in-time rule) and section 3.2 (the futures/swap split)",
        "record": "D620",
        "builder": "scripts/build_fund_holdings_quarterly.py",
        "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "columns": list(COLUMNS),
        "kinds": list(KINDS),
        "column_units": {
            "contracts": "SIGNED contract count: positive long, negative short",
            "notional_usd": "the document's own notional column, signed the same way; NULL in the "
                            "pre-notional USCF era, which published contracts and unrealized gain "
                            "and no notional at all",
            "month_weight": "|notional| / total futures |notional| for the (accession, fund, period)",
            "shares_out": "shares as the filing states them AT THAT FILING -- a later filing may "
                          "restate them through a reverse split, and both are kept",
            "net_assets": "USD; shareholders' equity (ProShares) or total partners' capital (USCF)",
            "f_fut": "futures notional / (futures + swap notional); NULL when any line's notional is",
            "filed_date": "THE KNOWN-AT DATE. Deposit section 3.1 line 70 forbids back-filling "
                          "today's composition across history, so a point-in-time read of this "
                          "fixture filters on filed_date <= t and never on period_end alone.",
            "period_end": "the as-of date of the holdings, 40-90 days before filed_date",
        },
        "conventions": {
            "month_basis": {
                "stated_contract": "the line named the delivery month explicitly ('NG August 2026 "
                                   "contracts, expiring July 2026'), so contract_month is exact",
                "expires_label": "the line said only 'expires March 2025'. Read as the DELIVERY "
                                 "month: UCO's three legs read March, June and December, and the "
                                 "Bloomberg Commodity Balanced index's deferred legs are the June "
                                 "and December CONTRACTS, which expire in May and November. The "
                                 "reading is an inference from that pattern and is flagged so a "
                                 "study can filter on it.",
            },
            "sign_basis": {
                "block_header": "'Futures Contracts Purchased/Sold' or 'Open Commodity Futures "
                                "Contracts - Long/Short' stated the side",
                "fund_leverage_sign": "the table gave no side and the sign is the fund's leverage "
                                      "sign from deposit section 3.1 (UNG and USO are +1)",
                "printed_sign": "the value's own sign as printed (parentheses are negative)",
            },
            "restatements": "All publications of a period are kept, one row set per accession. "
                            "UNG's FY2023 10-K restates 2023 share counts for a 1-for-4 reverse "
                            "split of 2024-01-23; the point-in-time anchor is the FIRST filing to "
                            "publish a period, which scripts/project_fund_panel.py takes.",
        },
        "rows": int(len(frame)),
        "funds": list(FUNDS),
        "filings_read": prov["filings_read"],
        "series_names_seen": prov["series_names_seen"],
        "unmapped_series": prov["unmapped_series"],
        "coverage": coverage(frame),
        "unparsed": {
            "rows": int(len(un)),
            "per_fund": {f: int((un["fund"] == f).sum()) for f in FUNDS},
            "reasons": {
                str(r): int(n)
                for r, n in un["reason"]
                .astype(str)
                .str.replace(r"\(\d[\d,]* characters of text\)", "(...)", regex=True)
                .value_counts()
                .items()
            },
            "periods": sorted({f"{r.fund} {r.period_end}" for r in un.itertuples()})[:80],
        },
        "gates": gates,
        "gate_definitions": {
            "G0_kinds_and_reasons": f"every kind in {KINDS}; every unparsed row states a reason",
            "G1_f_fut_in_unit_interval": "f_fut in [0,1] wherever non-null",
            "G2_contract_months_forward": "a held contract month is never before its period end",
            "G3_no_duplicate_lines": "one line per (accession, fund, period, kind, month, counterparty, description)",
            "G4_year_coverage": "every fund has a parsed row in every calendar year of its own span",
            "G5_known_answer_live_page": "the latest 10-Q's kind split agrees with D619's live "
                                         "2026-09-18 holdings page: UCO holds swaps, SCO does not",
        },
        "sha256": frozen.sha256_file(OUT, text_normalise=False),
        "sha256_uncompressed_csv": hashlib.sha256(raw).hexdigest(),
        "bytes": OUT.stat().st_size,
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename)",
        # THE CUT COLUMN IS `filed_date`, NOT `period_end`, and the choice is deliberate.
        # `period_end` is the row's as-of; `filed_date` is when the row EXISTED. They differ by
        # 40-90 days, so a reserved-slice cut on `period_end` lets through rows whose only
        # publication is after the seal -- the 2023-12-31 holdings of every fund were published
        # in February 2024. Cutting on `filed_date` reserves strictly more and is the same
        # quantity deposit section 3.1 line 70 means by point-in-time. `period_end` is listed as
        # a wrong cut, which does not stop it being READ (panels.py) -- only being the cut.
        "date_col": "filed_date",
        "wrong_cuts": ["period_end"],
        "holdout": HOLDOUT,
    }
    absent = [k for k in REQUIRED_META_KEYS if k not in meta]
    if absent:
        raise HoldingsError(f"meta is missing declared keys {absent}")
    META.write_text(json.dumps(meta, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    return meta


def _one(rec: Recorder, accession: str) -> list[dict[str, object]]:
    index = {f["accession"]: f for f in _index(rec)}
    if accession not in index:
        raise HoldingsError(f"{accession} is not a 10-Q or 10-K in the recorded index")
    f = index[accession]
    paths = sorted(glob.glob(str(rec.job_dir(JOB) / f"{accession}*.htm")))
    if not paths:
        raise HoldingsError(f"{accession} is not recorded on disk")
    text = flatten(Path(paths[-1]).read_bytes())
    rows, _ = rows_for_filing(
        text, issuer=f["issuer"], accession=accession, filed=f["filed"], form=f["form"],
        report_date=f["period_end"],
    )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--one", help="parse a single accession and print its rows")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.selftest:
        return selftest()
    if args.one:
        for r in _one(Recorder(Path(args.root)), args.one):
            P(json.dumps({k: (None if isinstance(v, float) and not np.isfinite(v) else v)
                          for k, v in r.items()}, default=str))
        return 0
    if args.build:
        frame, prov = build(Path(args.root))
        gates = run_gates(frame)
        meta = write_outputs(frame, prov, gates)
        P(f"  {len(frame):,} rows from {prov['filings_read']} filings -> {OUT.relative_to(REPO)}")
        for fund, c in meta["coverage"].items():  # type: ignore[attr-defined]
            P(f"  {fund:<5} {c['periods_with_holdings']:>3} periods "
              f"{c['first_period']}..{c['last_period']}  parsed {c['parsed_rows']:>4}  "
              f"unparsed {c['unparsed_rows']:>3}  anchors {c['periods_with_an_anchor']:>3}")
        P(f"  unmapped ProShares series: {prov['unmapped_series']}")
        P(f"  sha256 {meta['sha256']}  bytes {meta['bytes']:,}")
        return 0
    if args.gates:
        if not OUT.exists():
            raise HoldingsError(f"{OUT} does not exist; run --build first")
        frame = pd.read_csv(OUT, encoding="utf-8", dtype={"period_end": str, "fund": str,
                                                          "contract_month": str, "kind": str})
        frame = frame.fillna({"contract_month": "", "counterparty": "", "description": "", "reason": ""})
        P(json.dumps(run_gates(frame), indent=1, default=str))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
