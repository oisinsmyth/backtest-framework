"""D619 — the ProShares holdings table for BOIL, KOLD, UCO and SCO, recorded and parsed.

    uv run python scripts/fetch_fund_holdings.py             # one live GET per fund, recorded
    uv run python scripts/fetch_fund_holdings.py --parse     # parse the LATEST record of each
    uv run python scripts/fetch_fund_holdings.py --selftest  # no network: the parser's guards

FORWARD ONLY, AND THAT IS THE WHOLE POINT OF RECORDING IT
---------------------------------------------------------
The deposit asks for `futures_notional_by_contract_month` and `swap_notional` per fund per day
(§3.1 line 67) and insists on point-in-time composition: *"Use holdings as published for each
date. Never back-fill today's composition across history."* (§3.1 line 70). **ProShares publishes
ONE day of holdings — today's — and no historical archive** (six plausible archive URL patterns
were tried and all 404). So this page can never produce history; it can only start one, which is
exactly what the forward recorder is for (§13A.3). The free historical route for these four funds
is the Schedule of Investments inside the quarterly 10-Q and annual 10-K, at a 40-90 day lag, and
`data/fund_facts/SOURCES.md` records that.

WHY THE `Accept` HEADER IS NOT THE RECORDER'S
---------------------------------------------
`backtest_framework.data.recorder.UA` sends `Accept: text/html,application/json`, and
`www.proshares.com` CONTENT-NEGOTIATES on it: with that header the fund URL returns 7.8 KB of
Optimizely CMS JSON (page metadata and document links, no holdings), and with `Accept: text/html`
it returns the 270 KB page whose holdings table is server-rendered. Both are recorded under the
job `proshares_holdings` — the JSON records of 2026-09-21T23:14Z are the first four, and they are
kept rather than deleted, because they carry the prospectus, SAI and annual-report URLs this
repository otherwise had no link to. `fetch` is the caller's by the recorder's own contract
("the network is the caller's"), so the HTML request is built here and `recorder.http_get`'s
retry ladder — `ATTEMPTS` tries, backoff doubling from `BACKOFF_SECONDS`, **404 never retried** —
is reproduced rather than reached into, because `http_get` takes no headers argument.

THE PARSE RAISES ON A SHAPE CHANGE. A page with no `as of` date, or with no futures row, is not
an empty holdings table: it is a page this code no longer understands, and it stops the run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import (  # noqa: E402
    ATTEMPTS,
    BACKOFF_SECONDS,
    TIMEOUT,
    UA,
    RateLimiter,
    Record,
    Recorder,
)

PROSHARES_FUNDS = ("BOIL", "KOLD", "UCO", "SCO")
PAGE_URL = "https://www.proshares.com/our-etfs/leveraged-and-inverse/{slug}"
JOB = "proshares_holdings"
ROOT = REPO / "data" / "raw" / "recorder"
MIN_INTERVAL = 2.0

#: The recorder's own user agent, with an HTML-only Accept. See the module docstring.
HTML_HEADERS = {"User-Agent": UA["User-Agent"], "Accept": "text/html,application/xhtml+xml"}

KINDS = ("futures", "swap", "cash", "mmf", "other")

MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
#: `NATURAL GAS FUTR NOV26` -> ("NOV", "26"). Anchored on a word boundary at both ends so
#: `NOVA26` and `NOV260` do not match.
_MONTH_RE = re.compile(r"\b(" + "|".join(MONTHS) + r")(\d{2})\b")
#: The holdings block: everything from the table wrapper to the end of the table.
_BLOCK_RE = re.compile(r'<div class="fund-detail-table-holdings".*?</table>', re.S)
#: `<p class="text-util-md section-header-subtitle ...">as of 9/18/2026</p>`
_ASOF_RE = re.compile(r"as of\s+(\d{1,2})/(\d{1,2})/(\d{4})", re.I)
_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")


class HoldingsParseError(RuntimeError):
    """The page no longer has the shape this parser was written against. Always loud."""


@dataclass(frozen=True)
class HoldingRow:
    """One row of the fund's holdings table.

    `notional_usd`      the "Exposure Value (Notional + GL)" cell, SIGNED (KOLD's futures row is
                        negative), or None when the page prints `--`.
    `market_value_usd`  the "Market Value" cell, or None when the page prints `--`.
    `contracts`         the "Shares/Contracts" cell, signed, or None.
    `contract_month`    `2026-11` for `NOV26`, or None for a row with no month in its description.
    `kind`              futures | swap | cash | mmf | other — classified from the DESCRIPTION,
                        which is the only thing the page states.
    """

    holdings_as_of: str
    fund: str
    description: str
    contract_month: str | None
    contracts: float | None
    notional_usd: float | None
    market_value_usd: float | None
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise HoldingsParseError(f"kind {self.kind!r} not in {KINDS}")


# ------------------------------------------------------------------------------------ parsing
def _text(cell: str) -> str:
    return html.unescape(_TAG_RE.sub("", cell)).replace(" ", " ").strip()


def _number(text: str) -> float | None:
    """`786,828,510` -> 786828510.0, `$393,480,034.95` -> 393480034.95, `--` -> None.

    `(1,234)` is read as -1234.0 because an accounting negative is a real spelling on these
    pages; anything else that is not a number RAISES rather than becoming None, so a changed
    cell format is loud instead of silently emptying a column."""
    t = text.strip()
    if t in ("", "--", "-", "—", "N/A", "n/a"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace("$", "").replace(",", "").replace("%", "").strip()
    if t.startswith("+"):
        t = t[1:]
    try:
        v = float(t)
    except ValueError as exc:
        raise HoldingsParseError(f"cell {text!r} is neither a number nor an empty marker") from exc
    return -v if neg else v


def contract_month(description: str) -> str | None:
    """`NATURAL GAS FUTR NOV26` -> `2026-11`. None when the description names no month.

    Two-digit years are read as 2000+YY. That is right for every month these funds can hold
    (CME lists energy futures out to roughly ten years) and wrong only for a 1900s month, which
    no live holdings page can print."""
    m = _MONTH_RE.search(description.upper())
    if m is None:
        return None
    return f"{2000 + int(m.group(2)):04d}-{MONTHS[m.group(1)]:02d}"


def classify(description: str) -> str:
    """The row's `kind`, from the description alone — the only thing the page states.

    Order matters: `SWAP` is checked before `FUTR`, because a description naming both is a swap
    ON a future and its notional is swap notional for §3.2's purpose."""
    d = description.upper()
    if "SWAP" in d:
        return "swap"
    if "FUTR" in d or "FUTURE" in d:
        return "futures"
    if "MNY MKT" in d or "MONEY MARKET" in d or "MONEY MKT" in d:
        return "mmf"
    if "CASH" in d or "TREASURY BILL" in d or "T-BILL" in d:
        return "cash"
    return "other"


def parse_holdings(body: bytes | str, fund: str) -> list[HoldingRow]:
    """The fund page's holdings table.

    RAISES when the block is absent, when there is no `as of` date, when the table has no rows,
    or when no row classifies as `futures`. A commodity pool with no futures line is not an
    empty table, it is a page whose shape has moved, and a silent empty list would flow straight
    into `f_fut` as a division by zero or a false zero."""
    text = body.decode("utf-8", errors="replace") if isinstance(body, (bytes, bytearray)) else body
    block = _BLOCK_RE.search(text)
    if block is None:
        raise HoldingsParseError(
            f"{fund}: no `fund-detail-table-holdings` block in {len(text):,} characters. "
            f"The page shape has changed, or the response is the CMS JSON (see the module "
            f"docstring on the Accept header)."
        )
    chunk = block.group(0)
    asof = _ASOF_RE.search(chunk)
    if asof is None:
        raise HoldingsParseError(f"{fund}: the holdings block states no `as of M/D/YYYY` date")
    mm, dd, yyyy = int(asof.group(1)), int(asof.group(2)), int(asof.group(3))
    as_of = dt.date(yyyy, mm, dd).isoformat()

    rows: list[HoldingRow] = []
    for tr in _ROW_RE.finditer(chunk):
        cells = [_text(c) for c in _CELL_RE.findall(tr.group(1))]
        if not cells:
            continue  # the <thead> row, whose cells are <th>
        if len(cells) != 7:
            raise HoldingsParseError(
                f"{fund}: a holdings row has {len(cells)} cells, not the 7 this parser was "
                f"written against (Exposure Weight, Ticker, Description, Exposure Value, "
                f"Market Value, Shares/Contracts, SEDOL): {cells}"
            )
        description = cells[2]
        rows.append(
            HoldingRow(
                holdings_as_of=as_of,
                fund=fund,
                description=description,
                contract_month=contract_month(description),
                contracts=_number(cells[5]),
                notional_usd=_number(cells[3]),
                market_value_usd=_number(cells[4]),
                kind=classify(description),
            )
        )
    if not rows:
        raise HoldingsParseError(f"{fund}: the holdings table has no <td> rows")
    if not any(r.kind == "futures" for r in rows):
        raise HoldingsParseError(
            f"{fund}: no row classifies as futures. Descriptions found: "
            f"{[r.description for r in rows]}"
        )
    return rows


def row_exposure(row: HoldingRow) -> float:
    """|exposure value| where the page states one, else |market value|, else 0.

    The page prints `--` in Exposure Value for the cash line and `--` in Market Value for the
    derivative lines, so neither column alone is a complete exposure measure."""
    if row.notional_usd is not None:
        return abs(row.notional_usd)
    if row.market_value_usd is not None:
        return abs(row.market_value_usd)
    return 0.0


def f_fut(rows: list[HoldingRow]) -> float:
    """Futures exposure as a share of TOTAL exposure, all rows, absolute values.

    This is a whole-balance-sheet number: the denominator includes the money-market fund and the
    cash line, which are collateral rather than exposure. `f_fut_derivatives` is the §3.2 fact —
    the split of the DERIVATIVE book between futures and swaps — and the two answer different
    questions. Raises on an empty book rather than returning 0/0."""
    total = sum(row_exposure(r) for r in rows)
    if total <= 0.0:
        raise HoldingsParseError("total exposure is zero; f_fut is undefined")
    return sum(row_exposure(r) for r in rows if r.kind == "futures") / total


def f_fut_derivatives(rows: list[HoldingRow]) -> float | None:
    """**Deposit §3.2 line 89: "Split of exposure between futures and swaps, over time."**

    futures / (futures + swap), over the derivative rows only. None when the fund holds no
    derivative row at all — which is not a split of zero, it is no split."""
    fut = sum(row_exposure(r) for r in rows if r.kind == "futures")
    swp = sum(row_exposure(r) for r in rows if r.kind == "swap")
    if fut + swp <= 0.0:
        return None
    return fut / (fut + swp)


# ------------------------------------------------------------------------------------ fetching
def html_fetch(url: str, limiter: RateLimiter | None = None,
               opener: Callable[..., object] | None = None,
               sleep: Callable[[float], None] | None = None) -> Callable[[], tuple[bytes, Mapping[str, str]]]:
    """`recorder.fetcher(url)` with an HTML-only `Accept`. Same retry ladder, 404 never retried."""

    def _fetch() -> tuple[bytes, Mapping[str, str]]:
        _open = opener or urllib.request.urlopen
        _sleep = sleep or time.sleep
        req = urllib.request.Request(url, headers=HTML_HEADERS)
        delay = BACKOFF_SECONDS
        for attempt in range(ATTEMPTS):
            if limiter is not None:
                limiter.wait()
            try:
                with _open(req, timeout=TIMEOUT) as r:  # type: ignore[union-attr]
                    return bytes(r.read()), {str(k).lower(): str(v) for k, v in dict(r.headers).items()}
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                    raise
                if attempt == ATTEMPTS - 1:
                    raise RuntimeError(
                        f"GET {url} failed after {ATTEMPTS} attempts (urllib.request.urlopen): "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                _sleep(delay)
                delay *= 2
        raise RuntimeError(f"GET {url}: attempts={ATTEMPTS} exhausted without a result")

    return _fetch


def page_url(ticker: str) -> str:
    if ticker not in PROSHARES_FUNDS:
        raise ValueError(f"{ticker!r} is not one of {PROSHARES_FUNDS}")
    return PAGE_URL.format(slug=ticker.lower())


def fetch_one(rec: Recorder, ticker: str, limiter: RateLimiter | None = None) -> Record:
    """One fund page, recorded raw. No `parse=` is passed: `Recorder.record` writes the raw file
    BEFORE calling a parser, so a parser that raises would leave a file the manifest never names.
    The parse is a separate step over the recorded bytes (`--parse`), which also means a page
    fetched today can be re-parsed years later without another request."""
    url = page_url(ticker)
    return rec.record(JOB, ticker, html_fetch(url, limiter), ext="html", source_url=url)


def latest(rec: Recorder, ticker: str) -> Record:
    recs = [r for r in rec.records(JOB) if r.key == ticker]
    if not recs:
        raise HoldingsParseError(f"no {JOB} record for {ticker}")
    return recs[-1]


# ------------------------------------------------------------------------------------ selftest
_GOOD_PAGE = """
<div class="fund-detail-table-holdings"><div class="container">
<h2 class="section-header-title">Holdings</h2>
<p class="section-header-subtitle">as of 9/18/2026</p>
<table id="holdings"><thead><tr><th>Exposure Weight</th><th>Ticker</th><th>Description</th>
<th>Exposure Value</th><th>Market Value</th><th>Shares/Contracts</th><th>SEDOL Number</th></tr></thead>
<tbody>
<tr><td>199.97%</td><td>--</td><td>NATURAL GAS FUTR NOV26</td><td>786,828,510</td><td>--</td><td>25,857</td><td>--</td></tr>
<tr><td>--</td><td>--</td><td>NAT GAS SWAP NOV26</td><td>100,000,000</td><td>--</td><td>--</td><td>--</td></tr>
<tr><td>--</td><td>--</td><td>NET OTHER ASSETS / CASH</td><td>--</td><td>$393,480,034.95</td><td>393,480,035</td><td>--</td></tr>
</tbody></table></div></div>
"""


def selftest() -> int:
    """Every guard shown to ACCEPT the good case first and then to RAISE on a broken one."""
    checks: list[tuple[str, Callable[[], None]]] = []

    rows = parse_holdings(_GOOD_PAGE, "SYN")
    assert [r.kind for r in rows] == ["futures", "swap", "cash"], [r.kind for r in rows]
    assert rows[0].contract_month == "2026-11", rows[0].contract_month
    assert rows[1].kind == "swap", "a synthetic SWAP row must surface as kind == 'swap'"
    assert abs(f_fut_derivatives(rows) - 786828510 / 886828510) < 1e-15
    print(f"  OK   good page: 3 rows, month {rows[0].contract_month}, "
          f"f_fut {f_fut(rows):.6f}, derivative split {f_fut_derivatives(rows):.6f}")

    checks.append(("no holdings block", lambda: parse_holdings("<html>nothing</html>", "SYN")))
    checks.append(("no as-of date", lambda: parse_holdings(
        _GOOD_PAGE.replace("as of 9/18/2026", "as at some point"), "SYN")))
    checks.append(("no futures row", lambda: parse_holdings(
        _GOOD_PAGE.replace("NATURAL GAS FUTR NOV26", "NET OTHER ASSETS / CASH")
                  .replace("NAT GAS SWAP NOV26", "NET OTHER ASSETS / CASH"), "SYN")))
    checks.append(("wrong cell count", lambda: parse_holdings(
        _GOOD_PAGE.replace("<td>25,857</td><td>--</td></tr>", "<td>25,857</td></tr>"), "SYN")))
    checks.append(("unparseable cell", lambda: parse_holdings(
        _GOOD_PAGE.replace("786,828,510", "about a lot"), "SYN")))
    checks.append(("empty book", lambda: f_fut([])))
    checks.append(("bad kind", lambda: HoldingRow("2026-09-18", "SYN", "X", None, None, None, None, "nope")))

    bad = 0
    for name, fn in checks:
        try:
            fn()
        except HoldingsParseError as exc:
            print(f"  RAISED {name}: {type(exc).__name__}: {str(exc)[:70]}")
        else:
            bad += 1
            print(f"  DID NOT RAISE {name}  <-- a guard that cannot fire")
    print(f"  selftest: {len(checks)} guards, {len(checks) - bad} fired, {bad} silent")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fund", action="append", choices=list(PROSHARES_FUNDS))
    ap.add_argument("--parse", action="store_true", help="parse the latest record; no network")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    funds = tuple(args.fund) if args.fund else PROSHARES_FUNDS
    rec = Recorder(Path(args.root))
    if not args.parse:
        limiter = RateLimiter(MIN_INTERVAL)
        for t in funds:
            r = fetch_one(rec, t, limiter)
            print(f"  {t:<5} {r.bytes:>9,} bytes  sha {r.sha256[:12]}  {r.path}", flush=True)

    for t in funds:
        r = latest(rec, t)
        rows = parse_holdings((Path(args.root) / JOB / r.path).read_bytes(), t)
        print(f"  {t:<5} as of {rows[0].holdings_as_of}  f_fut {f_fut(rows):.4f}  "
              f"derivative split {f_fut_derivatives(rows)}", flush=True)
        for row in rows:
            print(f"        {row.kind:<8} {row.description:<32} month={row.contract_month} "
                  f"contracts={row.contracts} notional={row.notional_usd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
