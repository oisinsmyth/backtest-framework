"""D619 — the daily fund NAV panel for BOIL, KOLD, UCO and SCO, and the point-in-time OI join.

    uv run python scripts/build_fund_panel.py --build      # recorded CSVs -> the fixture + meta
    uv run python scripts/build_fund_panel.py --gates       # G1..G5 on the committed fixture
    uv run python scripts/build_fund_panel.py --selftest    # every gate proved to RAISE

Data layer only: **no return is computed, nothing is scored, no bar from 2024-01-01 on is read
for any return.** The panel is NAV, shares and AUM, and the gates are arithmetic on those three.

WHAT THE DEPOSIT ASKS FOR AND WHAT THIS SOURCE CARRIES
------------------------------------------------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.1 line 67, verbatim:

    For each fund, per day, store in Parquet: `date, fund, nav, shares_out, aum,
    futures_notional_by_contract_month, swap_notional, source, published_at`.

ProShares' historical NAV CSV carries `date, fund, nav, shares_out, aum` and **nothing else**.
`futures_notional_by_contract_month`, `swap_notional` and `published_at` are therefore **ABSENT
COLUMNS, not null-filled ones**, and the meta names them as columns the deposit asks for that
this source lacks. A column of nulls reads like data that happened to be missing on those days;
an absent column says the source never had it. (Parquet: this checkout has no engine — D608
records the same disagreement for the recorder's parsed copies — so the fixture is gzipped CSV,
which is what every other fixture here is.)

THE SERIES IS FULLY BACK-ADJUSTED FOR REVERSE SPLITS, AND THAT IS WHY THE EARLY ROWS LOOK WRONG
-----------------------------------------------------------------------------------------------
BOIL's first row reads `NAV 8,000,000`, `Shares Outstanding (000) 0`, `AUM 4,000,400`. That is
not a scale error and nothing here rescales it. `AUM / NAV` on that row is **0.50005 shares** —
no fund has ever held half a share — so both the NAV and the share count have been divided and
multiplied by the cumulative reverse-split factor while AUM, which is in dollars, has not. The
evidence that this is the whole story and there is no unadjusted discontinuity anywhere:

  * `NAV[t] / PriorNAV[t] == 1 + NAV Change (%) / 100` on **every one of the 16,484 rows**, to
    within 2e-4;
  * `max |NAV[t-1] / PriorNAV[t] - 1|` is 3.2e-5 (BOIL), 7.5e-5 (KOLD), 5.9e-3 (UCO), 1.5e-2
    (SCO) — four orders of magnitude below any split ratio;
  * so a split search over this series finds **nothing**, which is reported as nothing found
    rather than as no splits having happened. **No split source other than the series itself was
    available**: `data/raw/alphavantage/daily_adjusted_etf/` holds UNG and USO only, neither of
    which is one of these four.

WHY THE AUM IDENTITY IS NOT GATED AT ONE BASIS POINT
-----------------------------------------------------
The brief's gate was `aum ~= nav * shares_out * 1000` within 1 bp on >= 99% of rows. **The data
refuses it, for a reason that is about the source and not about the parse**: `Shares Outstanding
(000)` is published rounded to two decimals, which is **ten shares**. When BOIL held five shares
in February 2012 the rounding is the whole number, and the naive 1 bp test passes on 29.87% of
BOIL's rows, 71.42% of KOLD's, 99.20% of SCO's and 99.89% of UCO's. Gating on that would be
asserting a property of the DATA, not of the code (the standing rule: *assert code, not data;
find the invariant*). The invariant that IS about the parse is the rounding-aware one —

    |nav * shares_out - aum| <= |nav| * (ROUNDING_UNIT / 2 + eps),   ROUNDING_UNIT = 10 shares

— which holds on **100.000% of all 16,484 rows of all four funds**, and which still collapses the
moment a column is mis-assigned, because it is the same identity. The naive 1 bp share is
reported beside it, per fund, with its worst row, so the weaker statistic is visible rather than
replaced.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import gzip
import hashlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.recorder import Recorder  # noqa: E402
from backtest_framework.validation import frozen  # noqa: E402

FUNDS = ("BOIL", "KOLD", "SCO", "UCO")
JOB = "proshares_nav"
ROOT = REPO / "data" / "raw" / "recorder"
FIX = REPO / "data" / "fixtures"
OUT = FIX / "fund_nav_daily.csv.gz"
META = FIX / "fund_nav_daily.meta.json"

PANEL_COLUMNS = ("date", "fund", "nav", "shares_out", "aum", "source", "fetched_at")
#: Deposit §3.1 line 67 asks for these three as well. This source has none of them, so they are
#: ABSENT from the panel. Named here and in the meta so the omission is a statement, not a gap.
DEPOSIT_COLUMNS_THIS_SOURCE_LACKS = (
    "futures_notional_by_contract_month",
    "swap_notional",
    "published_at",
)

#: The source column `Shares Outstanding (000)` is published to two decimals of THOUSANDS.
SHARES_ROUNDING_UNIT = 10.0          # shares
AUM_IDENTITY_MIN_SHARE = 0.99        # G1's bar
NAIVE_IDENTITY_BP = 1e-4             # the brief's 1 bp, reported and NOT gated. See the docstring.

#: The holdout note, in the words of `data/fixtures/fut_book_depth_1m.meta.json#holdout` (D604),
#: with only the span and the builder changed. The sentence is the principal's, not this record's.
HOLDOUT = (
    "NAV, SHARES AND AUM ONLY -- no return, no signal, no trade. The series spans "
    "2008-11-24..2026-09-18, which runs through the deposit's sealed vault window "
    "(2025-03-01..2026-09-18) and past this repository's 2024-01-01 holdout, neither of which "
    "the principal has reconciled with the other. Nothing here may score anything until that "
    "reconciliation is in writing (D604, D619)."
)


class PanelError(RuntimeError):
    """A gate failed, or the parse produced something this builder will not write. Always loud."""


def P(*a: object) -> None:
    print(*a, flush=True)


# ------------------------------------------------------------------------------------- parsing
SOURCE_COLUMNS = (
    "Date", "ProShares Name", "Ticker", "NAV", "Prior NAV", "NAV Change (%)",
    "NAV Change ($)", "Shares Outstanding (000)", "Assets Under Management",
)


def read_nav_csv(path: Path, fund: str) -> pd.DataFrame:
    """One recorded ProShares CSV -> a tidy frame, oldest row first.

    The header is asserted against `SOURCE_COLUMNS` before anything is read out of it: a column
    inserted or renamed upstream would otherwise shift `Shares Outstanding (000)` into
    `Assets Under Management` and the AUM identity is the only thing that would notice.
    `utf-8-sig` because the file carries a BOM."""
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    got = tuple(c.strip() for c in raw.columns)
    if got != SOURCE_COLUMNS:
        raise PanelError(f"{path.name}: header is {got}, want {SOURCE_COLUMNS}")
    raw.columns = list(got)
    tickers = set(raw["Ticker"].str.strip().unique())
    if tickers != {fund}:
        raise PanelError(f"{path.name}: Ticker column holds {sorted(tickers)}, want {{{fund!r}}}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(raw["Date"], format="%m/%d/%Y"),
            "fund": fund,
            "nav": raw["NAV"].astype(float),
            "shares_out": raw["Shares Outstanding (000)"].astype(float) * 1000.0,
            "aum": raw["Assets Under Management"].astype(float),
            "prior_nav": raw["Prior NAV"].astype(float),
            "nav_change_pct": raw["NAV Change (%)"].astype(float),
        }
    )
    return out.sort_values("date").reset_index(drop=True)


def seed_rows(frame: pd.DataFrame) -> pd.Series:
    """**The seed-row rule: `shares_out == 0`.** True for the rows this builder drops.

    Chosen against the data and not assumed. The alternative on the table was `nav > 1e4`, and
    the data refuses it: 2,327 of BOIL's rows and 7 of SCO's carry a NAV above 10,000 and are
    ordinary rows of a back-adjusted series (see the module docstring), so that rule would drop
    62% of BOIL. `shares_out == 0` selects **82 rows, all of them BOIL's, all contiguous at the
    start of the series, 2011-10-04 to 2012-01-31**, and selects nothing at all in KOLD, UCO or
    SCO. What makes them unusable is not their scale: it is that a published share count of zero
    beside an AUM of four million dollars cannot carry per-share arithmetic, and differencing it
    for creation flow would read a flat zero across the fund's whole seed period.

    Nothing is rescaled. The rows are dropped and counted, and the meta names their dates."""
    return frame["shares_out"] == 0.0


def split_candidates(frame: pd.DataFrame, *, ratio_tol: float = 0.15) -> list[dict[str, object]]:
    """Reverse-split candidates: a NAV discontinuity with a matching inverse jump in shares.

    The detector is the series' own `Prior NAV` column, which is the previous session's NAV as
    the publisher carries it forward. Under a 1-for-k reverse split restated into the history,
    `PriorNAV[t] = k * NAV[t-1]` and `shares[t] = shares[t-1] / k`, so

        nav_ratio    = PriorNAV[t] / NAV[t-1]      = k
        shares_ratio = shares[t]   / shares[t-1]   = 1/k
        inverse_match  <=>  nav_ratio * shares_ratio == 1

    which is the "matching INVERSE jump" in one number. `ratio_tol = 0.15` on `|log nav_ratio|`
    is far below the smallest reverse split any of these funds has done (1-for-4) and far above
    the observed carry noise. Returns [] when there is none, and [] is reported as [] — see the
    module docstring on why this series has no discontinuity to find."""
    nav = frame["nav"].to_numpy(dtype=float)
    prior = frame["prior_nav"].to_numpy(dtype=float)
    shares = frame["shares_out"].to_numpy(dtype=float)
    if len(frame) < 2:
        return []
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = prior[1:] / nav[:-1]
    out: list[dict[str, object]] = []
    for i in np.where(np.abs(np.log(np.where(ratio > 0, ratio, np.nan))) > ratio_tol)[0]:
        share_ratio = float(shares[i + 1] / shares[i]) if shares[i] else float("nan")
        out.append(
            {
                "fund": str(frame["fund"].iloc[i + 1]),
                "date": str(frame["date"].iloc[i + 1].date()),
                "nav_ratio": float(ratio[i]),
                "shares_ratio": share_ratio,
                "inverse_match": bool(np.isfinite(share_ratio) and abs(ratio[i] * share_ratio - 1.0) < 0.05),
            }
        )
    return out


def carry_check(frame: pd.DataFrame) -> dict[str, float]:
    """The two numbers the split search rests on, so the [] above is falsifiable.

    `max_carry_dev` is `max |NAV[t-1]/PriorNAV[t] - 1|` and `max_pct_dev` is
    `max |NAV[t]/PriorNAV[t] - (1 + pct/100)|`. Both near zero means the publisher's own
    day-to-day chain is intact and carries no restatement."""
    nav = frame["nav"].to_numpy(dtype=float)
    prior = frame["prior_nav"].to_numpy(dtype=float)
    pct = frame["nav_change_pct"].to_numpy(dtype=float)
    return {
        "max_carry_dev": float(np.max(np.abs(nav[:-1] / prior[1:] - 1.0))),
        "max_pct_dev": float(np.max(np.abs(nav[1:] / prior[1:] - (1.0 + pct[1:] / 100.0)))),
    }


# --------------------------------------------------------------------------------------- build
def build(root: Path = ROOT) -> tuple[pd.DataFrame, dict[str, object]]:
    """The recorded CSVs -> the panel and its provenance. No network."""
    rec = Recorder(root)
    per_fund: dict[str, pd.DataFrame] = {}
    prov: dict[str, object] = {}
    frames = []
    for fund in FUNDS:
        recs = [r for r in rec.records(JOB) if r.key == fund]
        if not recs:
            raise PanelError(f"no {JOB} record for {fund}; run scripts/fetch_fund_nav.py first")
        r = recs[-1]
        raw = read_nav_csv(rec.job_dir(JOB) / r.path, fund)
        per_fund[fund] = raw
        drop = seed_rows(raw)
        kept = raw.loc[~drop].copy()
        kept["source"] = r.source_url
        kept["fetched_at"] = r.fetched_at
        frames.append(kept[list(PANEL_COLUMNS)])
        prov[fund] = {
            "record_path": r.path,
            "sha256": r.sha256,
            "bytes": r.bytes,
            "source_url": r.source_url,
            "fetched_at": r.fetched_at,
            "rows_in_source": int(len(raw)),
            "rows_kept": int(len(kept)),
            "seed_rows_excluded": int(drop.sum()),
            "seed_row_dates": (
                [str(raw.loc[drop, "date"].min().date()), str(raw.loc[drop, "date"].max().date())]
                if drop.any() else []
            ),
            "span": [str(kept["date"].min().date()), str(kept["date"].max().date())],
            "splits_found": split_candidates(raw),
            "carry_check": carry_check(raw),
        }
    panel = pd.concat(frames, ignore_index=True).sort_values(["fund", "date"]).reset_index(drop=True)
    panel["date"] = panel["date"].dt.strftime("%Y-%m-%d")
    return panel, prov


# --------------------------------------------------------------------------------------- gates
def gate_four_funds(panel: pd.DataFrame) -> dict[str, object]:
    """G4. Exactly the four funds, each non-empty."""
    got = tuple(sorted(panel["fund"].unique()))
    if got != FUNDS:
        raise PanelError(f"G4: funds are {got}, want {FUNDS}")
    counts = {f: int((panel["fund"] == f).sum()) for f in FUNDS}
    empty = [f for f, n in counts.items() if n == 0]
    if empty:
        raise PanelError(f"G4: {empty} present with zero rows")
    return {"funds": list(got), "rows": counts}


def gate_no_duplicates(panel: pd.DataFrame) -> dict[str, object]:
    """G3. No `(date, fund)` appears twice."""
    dupes = panel.duplicated(["date", "fund"], keep=False)
    if dupes.any():
        sample = panel.loc[dupes, ["fund", "date"]].head(5).to_dict("records")
        raise PanelError(f"G3: {int(dupes.sum())} duplicate (date, fund) rows, e.g. {sample}")
    return {"duplicate_rows": 0}


def gate_dates_increasing(panel: pd.DataFrame) -> dict[str, object]:
    """G2. Dates strictly increase within each fund, in the order the fixture is written."""
    for fund in sorted(panel["fund"].unique()):
        d = panel.loc[panel["fund"] == fund, "date"].to_numpy()
        bad = np.where(d[1:] <= d[:-1])[0]
        if bad.size:
            i = int(bad[0])
            raise PanelError(f"G2: {fund} is not strictly increasing at row {i}: {d[i]} -> {d[i + 1]}")
    return {"strictly_increasing": True}


def gate_aum_identity(panel: pd.DataFrame) -> dict[str, object]:
    """G1. `aum == nav * shares_out` to within half the published share-rounding unit.

    A known-answer check on the parse: the three numbers come from three different columns of
    the source and only a correct assignment satisfies the identity. The naive 1 bp share is
    computed and REPORTED per fund — with the worst row — and is deliberately not the bar; the
    module docstring says why."""
    per: dict[str, object] = {}
    for fund in sorted(panel["fund"].unique()):
        g = panel[panel["fund"] == fund]
        nav = g["nav"].to_numpy(dtype=float)
        shares = g["shares_out"].to_numpy(dtype=float)
        aum = g["aum"].to_numpy(dtype=float)
        resid = np.abs(nav * shares - aum)
        tol = np.abs(nav) * (SHARES_ROUNDING_UNIT / 2.0 + 1e-3)
        ok = resid <= tol
        rel = resid / np.maximum(np.abs(aum), 1e-9)
        use = resid / tol
        worst = int(np.argmax(rel))
        per[fund] = {
            "n": int(len(g)),
            "share_within_rounding": float(ok.mean()),
            "share_within_1bp": float((rel <= NAIVE_IDENTITY_BP).mean()),
            # HOW MUCH OF THE TOLERANCE THE WORST ROW USES. A 100% pass rate says nothing about
            # how close the bar was, and on this source it can be very close: when a fund holds
            # five shares, half a rounding unit is the whole quantity and the test is nearly
            # vacuous on that row. Reported so the gate's strength is visible, not just its
            # verdict.
            "worst_tolerance_use": float(use.max()),
            "median_tolerance_use": float(np.median(use)),
            "rows_using_over_half_the_tolerance": int((use > 0.5).sum()),
            "worst_relative_bp": float(rel[worst] * 1e4),
            "worst_row": {
                "date": str(g["date"].iloc[worst]),
                "nav": float(nav[worst]),
                "shares_out": float(shares[worst]),
                "aum": float(aum[worst]),
                "implied_shares": float(aum[worst] / nav[worst]),
            },
        }
        if ok.mean() < AUM_IDENTITY_MIN_SHARE:
            raise PanelError(
                f"G1: {fund} satisfies |nav*shares - aum| <= |nav|*{SHARES_ROUNDING_UNIT / 2} on "
                f"{ok.mean():.6f} of rows, bar {AUM_IDENTITY_MIN_SHARE}. Worst row {per[fund]['worst_row']}"
            )
    return per


def gate_spans(panel: pd.DataFrame) -> dict[str, object]:
    """G5. Every fund's span, reported. Raises only on an empty or reversed span."""
    out: dict[str, object] = {}
    for fund in sorted(panel["fund"].unique()):
        d = panel.loc[panel["fund"] == fund, "date"]
        first, last = str(d.min()), str(d.max())
        if not first or first > last:
            raise PanelError(f"G5: {fund} span {first}..{last} is empty or reversed")
        out[fund] = {"first": first, "last": last, "rows": int(len(d))}
    return out


GATES: tuple[tuple[str, Callable[[pd.DataFrame], dict[str, object]]], ...] = (
    ("G1_aum_identity", gate_aum_identity),
    ("G2_dates_increasing", gate_dates_increasing),
    ("G3_no_duplicates", gate_no_duplicates),
    ("G4_four_funds", gate_four_funds),
    ("G5_spans", gate_spans),
)


def run_gates(panel: pd.DataFrame) -> dict[str, object]:
    return {name: fn(panel) for name, fn in GATES}


# ------------------------------------------------------------------- deposit test 50: the OI join
def _oi_rule() -> tuple[Callable[..., object], int]:
    """`usable_session` and `ENTRY_MIN` out of `scripts/build_fut_open_interest.py`, by AST.

    ONE definition of D497's causality rule in this repository. Not `import`: that module's body
    inserts `scripts/` on `sys.path` and imports a second runner, and D606 recorded what running
    a runner's module body costs (`run_d365`'s audit hook poisoned the collectability gate for a
    whole process). Only the constant and the function are compiled, into a namespace holding
    numpy and pandas. Source is read as bytes with CRLF normalised first (D550)."""
    path = REPO / "scripts" / "build_fut_open_interest.py"
    tree = ast.parse(path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8"), filename=str(path))
    wanted: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "ENTRY_MIN" for t in node.targets
        ):
            wanted.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "usable_session":
            wanted.append(node)
    if len(wanted) != 2:
        raise PanelError(
            f"{path}: expected exactly one `ENTRY_MIN =` and one `def usable_session`, found "
            f"{len(wanted)} of the two. D497's rule has moved and this join must not guess at it."
        )
    ns: dict[str, object] = {"np": np, "pd": pd}
    exec(compile(ast.fix_missing_locations(ast.Module(body=wanted, type_ignores=[])), str(path), "exec"), ns)  # noqa: S102
    return ns["usable_session"], int(ns["ENTRY_MIN"])  # type: ignore[return-value,arg-type]


OI_COLUMNS = ("ts_event", "strike", "oi")


def usable_oi(
    oi_table: pd.DataFrame,
    session: str,
    *,
    calendar: Sequence[str] | None = None,
) -> pd.DataFrame:
    """**Deposit unit test 50**: options open interest by strike, joined point-in-time — *"the
    prior day's published values only"* (§12 item 50, line 756).

    Two rules compose here and they are not the same rule, so both are named:

      * **D497's causality rule**, imported from `scripts/build_fut_open_interest.py` and not
        restated: a publication is first usable in the earliest calendar session whose 10:00 ET
        entry is strictly after `ts_event`. A figure published at 09:00 ET is usable that
        session; one published at 11:00 ET is not.
      * **The deposit's extra conservatism**: test 50 says the PRIOR day's published values only.
        That is a condition on the PUBLICATION DAY, not on the usable day, so it is a second
        clause and not a shift of the first: a figure published at 09:00 ET on `session` itself
        is excluded here even though D497 would allow it. The two disagree, the deposit is
        stricter, and a settlement-window study fills at 14:28-14:30 ET where a 09:00
        publication would genuinely be available — **this function takes the stricter rule and
        says so, rather than silently taking either.**

    A row survives both clauses:

        first_usable_session(ts) <= session        (D497: it has become usable)
        publication ET date       <  session        (the deposit: it is a PRIOR day's value)

    Returns the freshest surviving publication per strike, `ts_event`-ascending. RAISES on a
    missing column, a non-integer `ts_event`, or a `session` absent from the calendar; an empty
    frame is a legitimate answer (nothing had been published yet) and is returned, not raised.

    `calendar` defaults to the ET dates the publications fall on, plus `session`. Pass the real
    session calendar whenever one exists: a default built from the data cannot know about a
    holiday on which nothing was published.
    """
    missing = [c for c in OI_COLUMNS if c not in oi_table.columns]
    if missing:
        raise PanelError(f"usable_oi: oi_table is missing {missing}; want {list(OI_COLUMNS)}")
    ts = oi_table["ts_event"].to_numpy()
    if not np.issubdtype(ts.dtype, np.integer):
        raise PanelError(f"usable_oi: ts_event is {ts.dtype}, want int64 nanoseconds UTC")
    try:
        dt.date.fromisoformat(session)
    except ValueError as exc:
        raise PanelError(f"usable_oi: session {session!r} is not an ISO date") from exc

    pub_days = pd.to_datetime(ts, utc=True).tz_convert("US/Eastern").strftime("%Y-%m-%d").to_numpy()
    if calendar is None:
        calendar = sorted(set(pub_days.tolist()) | {session})
    cal = np.array(sorted(set(calendar)), dtype=object)
    if session not in set(cal.tolist()):
        raise PanelError(f"usable_oi: session {session!r} is not in the calendar of {len(cal)} sessions")

    usable_session, _entry_min = _oi_rule()
    first_usable = usable_session(ts, cal)
    keep = np.array(
        [u is not None and u <= session and p < session for u, p in zip(first_usable, pub_days, strict=True)],
        dtype=bool,
    )
    out = oi_table.loc[keep].copy()
    out["first_usable_session"] = [u for u, k in zip(first_usable, keep, strict=True) if k]
    out = out.sort_values("ts_event")
    return out.groupby("strike", as_index=False).last().sort_values("strike").reset_index(drop=True)


# ------------------------------------------------------------------------------------ selftest
def _synthetic_panel() -> pd.DataFrame:
    """A four-fund, three-row-each panel that passes every gate. The base case for the breaks."""
    rows = []
    for fund in FUNDS:
        for i, day in enumerate(("2026-09-16", "2026-09-17", "2026-09-18")):
            nav, shares = 20.0 + i, 19_511_140.0
            rows.append(
                {"date": day, "fund": fund, "nav": nav, "shares_out": shares,
                 "aum": nav * shares, "source": "https://example.invalid/x.csv",
                 "fetched_at": "2026-09-21T23:14:14Z"}
            )
    return pd.DataFrame(rows, columns=list(PANEL_COLUMNS))


def selftest() -> int:
    """Every gate shown to ACCEPT the good panel first and then to RAISE on a broken one.
    A self-test that cannot fail is worse than none, so each break is aimed at the scalar the
    gate compares, not merely at the frame."""
    good = _synthetic_panel()
    report = run_gates(good)
    P(f"  OK   good panel: {report['G4_four_funds']['rows']}, "
      f"identity {report['G1_aum_identity']['BOIL']['share_within_rounding']:.6f}")

    breaks: list[tuple[str, Callable[[], object]]] = []

    def _shift_aum() -> object:
        bad = good.copy()
        # 1% off: far outside half a rounding unit (10 shares on ~19.5 M is 5e-7 of the AUM)
        bad.loc[0, "aum"] = float(bad.loc[0, "aum"]) * 1.01
        return gate_aum_identity(bad)

    def _swap_columns() -> object:
        bad = good.copy()
        bad["shares_out"], bad["aum"] = bad["aum"].copy(), bad["shares_out"].copy()
        return gate_aum_identity(bad)

    def _unsorted() -> object:
        bad = good.copy()
        bad.loc[0, "date"], bad.loc[1, "date"] = bad.loc[1, "date"], bad.loc[0, "date"]
        return gate_dates_increasing(bad)

    def _duplicate() -> object:
        bad = good.copy()
        bad.loc[1, "date"] = bad.loc[0, "date"]
        return gate_no_duplicates(bad)

    def _three_funds() -> object:
        return gate_four_funds(good[good["fund"] != "SCO"].reset_index(drop=True))

    def _empty_span() -> object:
        return gate_spans(good.assign(date=""))

    def _bad_header() -> object:
        p = REPO / "temp" / "d613_bad_header.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Date,Ticker,NAV\n09/18/2026,BOIL,20.0\n", encoding="utf-8", newline="\n")
        try:
            return read_nav_csv(p, "BOIL")
        finally:
            p.unlink(missing_ok=True)

    def _oi_missing_column() -> object:
        return usable_oi(pd.DataFrame({"ts_event": np.array([0], dtype="int64"), "oi": [1]}), "2026-09-18")

    def _oi_float_ts() -> object:
        return usable_oi(
            pd.DataFrame({"ts_event": np.array([0.0]), "strike": [1.0], "oi": [1]}), "2026-09-18"
        )

    def _oi_session_off_calendar() -> object:
        ts = np.array([pd.Timestamp("2026-09-17 18:00", tz="US/Eastern").value], dtype="int64")
        return usable_oi(pd.DataFrame({"ts_event": ts, "strike": [3.0], "oi": [10]}),
                         "2026-09-18", calendar=["2026-09-17"])

    breaks += [
        ("G1 aum shifted 1%", _shift_aum),
        ("G1 shares/aum swapped", _swap_columns),
        ("G2 dates out of order", _unsorted),
        ("G3 duplicate (date, fund)", _duplicate),
        ("G4 one fund missing", _three_funds),
        ("G5 empty span", _empty_span),
        ("parse: wrong header", _bad_header),
        ("test 50: missing column", _oi_missing_column),
        ("test 50: float ts_event", _oi_float_ts),
        ("test 50: session off calendar", _oi_session_off_calendar),
    ]

    silent = 0
    for name, fn in breaks:
        try:
            fn()
        except PanelError as exc:
            P(f"  RAISED {name}: {str(exc)[:90]}")
        else:
            silent += 1
            P(f"  DID NOT RAISE {name}  <-- a gate that cannot fire")
    P(f"  selftest: {len(breaks)} breaks, {len(breaks) - silent} fired, {silent} silent")
    return 1 if silent else 0


# ---------------------------------------------------------------------------------------- meta
REQUIRED_META_KEYS = (
    "spec", "record", "builder", "built_utc", "columns", "deposit_columns_absent", "sources",
    "per_fund", "seed_row_rule", "splits", "gates", "rows", "sha256", "date_col", "holdout",
)


def write_outputs(panel: pd.DataFrame, prov: Mapping[str, object], gates: Mapping[str, object]) -> dict[str, object]:
    FIX.mkdir(parents=True, exist_ok=True)
    # A DETERMINISTIC gzip stream, the pattern of `scripts/build_fut_book_depth.py:589`: the
    # default header carries the source file name and the WALL CLOCK, so two identical panels
    # hash differently and the meta's sha256 would check nothing but "this is the file I just
    # wrote". `mtime=0` and an empty `filename` make the bytes a pure function of the rows, and
    # LF is pinned at both layers (D550). Measured before this line existed: three consecutive
    # builds of the same 16,402 rows gave three different digests.
    raw = panel.to_csv(index=False, encoding="utf-8", lineterminator="\n").encode("utf-8")
    with open(OUT, "wb") as fb, gzip.GzipFile(
        filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9
    ) as gz:
        gz.write(raw)
    meta: dict[str, object] = {
        "spec": "D619; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.1 line 67 (the panel schema)",
        "record": "D619",
        "builder": "scripts/build_fund_panel.py",
        "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "columns": list(PANEL_COLUMNS),
        "column_units": {
            "nav": "USD per share, as published (the series is back-adjusted for reverse splits)",
            "shares_out": "SHARES. The source column is 'Shares Outstanding (000)', published to "
                          "two decimals of thousands; multiplied by 1000 here, so every value is "
                          "an exact multiple of 10 shares and that 10 is the rounding unit.",
            "aum": "USD, as published, NOT split-adjusted",
            "source": "the URL the row's CSV was fetched from",
            "fetched_at": "the recorder's fetched_at for that CSV -- the availability time "
                          "(deposit decision D23); this source states no published_at",
        },
        "deposit_columns_absent": {
            "columns": list(DEPOSIT_COLUMNS_THIS_SOURCE_LACKS),
            "why": "ProShares' historical NAV CSV carries none of them. They are ABSENT rather "
                   "than null-filled: a column of nulls reads as data missing on those days, an "
                   "absent column says the source never had it. Holdings (the futures/swap split "
                   "by contract month) are FORWARD ONLY from this issuer -- see D619 and "
                   "scripts/fetch_fund_holdings.py; the free historical route is the Schedule of "
                   "Investments in the quarterly 10-Q and annual 10-K, at a 40-90 day lag.",
        },
        "sources": {f: prov[f]["source_url"] for f in FUNDS},  # type: ignore[index]
        "per_fund": prov,
        "seed_row_rule": {
            "rule": "shares_out == 0",
            "why": "the published share count rounds to zero beside a multi-million-dollar AUM, "
                   "so no per-share or creation-flow arithmetic is possible on those rows. "
                   "NOTHING IS RESCALED; the rows are dropped and named.",
            "rejected_alternative": "nav > 1e4 -- refused by the data: 2,327 of BOIL's rows and 7 "
                                    "of SCO's carry NAV above 10,000 and are ordinary rows of a "
                                    "back-adjusted series.",
            "excluded": {f: prov[f]["seed_rows_excluded"] for f in FUNDS},  # type: ignore[index]
            "dates": {f: prov[f]["seed_row_dates"] for f in FUNDS},  # type: ignore[index]
        },
        "splits": {
            "found": {f: prov[f]["splits_found"] for f in FUNDS},  # type: ignore[index]
            "detector": "a NAV discontinuity of more than 15% against the series' own Prior NAV "
                        "column, with the shares_out jump beside it",
            "why_empty": "the published series is FULLY BACK-ADJUSTED for reverse splits, so it "
                         "carries no discontinuity to find: NAV[t]/PriorNAV[t] equals 1 + the "
                         "stated NAV Change (%) on every row, and the carry deviation is at most "
                         "1.5e-2. BOIL's first row implies 0.50005 shares outstanding, which is "
                         "the adjustment showing itself.",
            "no_independent_source": "No split source other than the series itself was available. "
                                     "data/raw/alphavantage/daily_adjusted_etf/ holds UNG and USO "
                                     "only -- neither is one of these four -- and carries prices, "
                                     "not corporate actions.",
            "carry_check": {f: prov[f]["carry_check"] for f in FUNDS},  # type: ignore[index]
        },
        "gates": gates,
        "gate_definitions": {
            "G1_aum_identity": f"|nav*shares_out - aum| <= |nav|*({SHARES_ROUNDING_UNIT}/2 + 1e-3) "
                               f"on >= {AUM_IDENTITY_MIN_SHARE} of rows per fund. The naive 1 bp "
                               f"share is REPORTED beside it and is not the bar: the source "
                               f"rounds shares to 10, which the early low-share era cannot carry.",
            "G2_dates_increasing": "dates strictly increase within each fund",
            "G3_no_duplicates": "no (date, fund) twice",
            "G4_four_funds": "exactly BOIL, KOLD, SCO, UCO, each non-empty",
            "G5_spans": "each fund's first and last date, reported",
        },
        "rows": int(len(panel)),
        "sha256": frozen.sha256_file(OUT, text_normalise=False),
        "sha256_uncompressed_csv": hashlib.sha256(raw).hexdigest(),
        "bytes": OUT.stat().st_size,
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename), so the digest is a fact about the rows and not about when the build ran",
        "date_col": "date",
        "holdout": HOLDOUT,
    }
    absent = [k for k in REQUIRED_META_KEYS if k not in meta]
    if absent:
        raise PanelError(f"meta is missing declared keys {absent}")
    META.write_text(json.dumps(meta, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.build:
        panel, prov = build(Path(args.root))
        gates = run_gates(panel)
        meta = write_outputs(panel, prov, gates)
        P(f"  {len(panel):,} rows, {len(FUNDS)} funds -> {OUT.relative_to(REPO)}")
        for f in FUNDS:
            g = gates["G1_aum_identity"][f]  # type: ignore[index]
            s = meta["per_fund"][f]  # type: ignore[index]
            P(f"  {f:<5} {s['span'][0]}..{s['span'][1]}  {g['n']:>5} rows  "
              f"identity {g['share_within_rounding']:.6f}  1bp {g['share_within_1bp']:.4f}  "
              f"seed dropped {s['seed_rows_excluded']}  splits {len(s['splits_found'])}")
        P(f"  sha256 {meta['sha256']}  bytes {meta['bytes']:,}")
        return 0

    if args.gates:
        if not OUT.exists():
            raise PanelError(f"{OUT} does not exist; run --build first")
        panel = pd.read_csv(OUT, encoding="utf-8", dtype={"date": str, "fund": str})
        P(json.dumps(run_gates(panel), indent=1, default=str))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
