"""D620 — the principal's question, answered by measurement: can the fund panel be projected
backwards and BETWEEN the filings from current AUM and shares?

    uv run python scripts/project_fund_panel.py --premium    # |close - NAV| on the four funds
    uv run python scripts/project_fund_panel.py --validate   # the three methods against daily truth
    uv run python scripts/project_fund_panel.py --build      # UNG and USO -> the projected fixture
    uv run python scripts/project_fund_panel.py --selftest   # every guard proved to RAISE

**No strategy return is computed and nothing is scored.** The validation reads
`fund_nav_daily` through `load_panel(..., reserved_from="2024-01-01")` (D609), so **every error
number in this record is measured on rows dated 2023-12-29 or earlier.** The projected panel
itself runs to the present as a data artefact and carries D604's holdout sentence.

THE QUESTION, AND WHY IT IS ANSWERABLE AT ALL
----------------------------------------------
> *"Can we project this backwards / in between the filings based on current AUM and shares?"*

The 10-Q/10-K Schedule of Investments is quarterly, so a fund panel built from filings has four
observations a year. Four of the six funds — BOIL, KOLD, UCO and SCO — ALSO have a daily truth
series (`fund_nav_daily`, D619, from ProShares' own historical-NAV CSVs). So the question can be
answered rather than argued: build the between-filing series for those four **from their filings
alone**, compare it to the daily series, and carry the measured error over to UNG and USO, which
have filings and no daily truth.

THE THREE CANDIDATES, AND WHICH OF THEM A REAL-TIME USER COULD HAVE RUN
------------------------------------------------------------------------
| method | shares between anchors | AUM | usable in real time |
|---|---|---|---|
| `step` | the last anchor's share count, held flat | shares x the anchor's NAV per share | **yes** |
| `price_implied` | the last anchor's share count, held flat | shares x **today's market close** | **yes** |
| `linear` | linear interpolation between the two BRACKETING anchors | shares x today's close | **NO** |

`linear` needs the NEXT filing, which is published 40-90 days after the period it closes and up
to seven months after the days it is interpolating. It is reported as a **hindsight bound** — the
best any between-filing interpolation could do — and never as a method. Saying so is the whole
point: a projected panel that quietly interpolates is a look-ahead of one quarter, and it would
be invisible in every downstream number.

TWO CLOCKS, AND THE COST OF THE REPORTING LAG IS MEASURED SEPARATELY
---------------------------------------------------------------------
`--validate` runs every method twice:

* **`filed`** — the anchor in force on date `t` is the newest one whose `filed_date <= t`. This
  is deposit section 3.1 line 70 (*"Never back-fill today's composition across history"*) and it
  is what a point-in-time user has.
* **`period`** — the anchor in force is the newest whose `period_end <= t`, as if the filing
  arrived the day the quarter closed. Unusable, and reported because the DIFFERENCE between the
  two is exactly what the 40-90 day filing lag costs.

AND THE ANCHORS ARE TAKEN AS FIRST PUBLISHED, NEVER AS LATEST RESTATED. UNG's FY2023 10-K
restates every 2023 share count for a 1-for-4 reverse split of 2024-01-23. Anchoring on the
latest filing would carry a 4x error across the whole of 2023 and show no discontinuity at all.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.panels import load_panel  # noqa: E402
from backtest_framework.data.recorder import Recorder  # noqa: E402
from backtest_framework.validation import frozen  # noqa: E402

FIX = REPO / "data" / "fixtures"
HOLDINGS = FIX / "fund_holdings_quarterly.csv.gz"
OUT = FIX / "fund_panel_projected.csv.gz"
META = FIX / "fund_panel_projected.meta.json"
ROOT = REPO / "data" / "raw" / "recorder"
AV_DISK = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted_etf"
PRICE_JOB = "fund_market_prices"

#: The four with a daily truth series. The validation set.
TRUTH_FUNDS = ("BOIL", "KOLD", "SCO", "UCO")
#: The two with filings and no daily truth. The projection's target.
TARGET_FUNDS = ("UNG", "USO")
#: This repository's seal. Every validation number is measured at or before it (D609).
RESERVED_FROM = "2024-01-01"

METHODS = ("step", "price_implied", "linear")
CLOCKS = ("filed", "period")
#: `linear` needs a filing that did not exist yet. Named here so it cannot be used by accident.
HINDSIGHT_METHODS = ("linear",)

COLUMNS = (
    "date", "fund", "shares_out_est", "aum_est", "nav_proxy", "method", "clock",
    "anchor_period_end", "anchor_filed_date", "est_flag",
)

HOLDOUT = (
    "ESTIMATED SHARES AND AUM ONLY -- no return, no signal, no trade, and every row carries "
    "est_flag = 1. The span runs through the deposit's sealed vault window "
    "(2025-03-01..2026-09-18) and past this repository's 2024-01-01 holdout, neither of which "
    "the principal has reconciled with the other. Nothing here may score anything until that "
    "reconciliation is in writing (D604, D619, D620). The ERRORS quoted in this meta were "
    "measured on rows dated 2023-12-29 or earlier, read through load_panel(reserved_from="
    "'2024-01-01')."
)


class ProjectionError(RuntimeError):
    """A guard refused. Always loud."""


def P(*a: object) -> None:
    print(*a, flush=True)


# ------------------------------------------------------------------------------------- anchors
def anchors(frame: pd.DataFrame) -> pd.DataFrame:
    """`(fund, period_end)` -> the values AS FIRST PUBLISHED, with that publication's date.

    One period is reported by several filings — a 10-K repeats the prior year, a 10-Q repeats the
    prior year end — and they do not always agree. UNG's 2023 share counts are restated by a
    factor of four in the FY2023 10-K for a reverse split executed in January 2024. The FIRST
    filing to publish a period is the only one a reader on that date could have had, so each
    field takes the value from the earliest `filed_date` that carries it non-null, and the
    `filed_date` recorded is that field's own publication."""
    need = ("fund", "period_end", "filed_date", "shares_out", "net_assets", "nav_per_share")
    missing = [c for c in need if c not in frame.columns]
    if missing:
        raise ProjectionError(f"the holdings frame is missing {missing}")
    rows: list[dict[str, object]] = []
    work = frame.sort_values(["fund", "period_end", "filed_date"])
    for (fund, period), g in work.groupby(["fund", "period_end"], sort=True):
        row: dict[str, object] = {"fund": fund, "period_end": period}
        for field in ("shares_out", "net_assets", "nav_per_share"):
            vals = pd.to_numeric(g[field], errors="coerce")
            ok = g.loc[vals.notna()]
            row[field] = float(vals[vals.notna()].iloc[0]) if len(ok) else np.nan
            row[f"{field}_filed"] = str(ok["filed_date"].iloc[0]) if len(ok) else ""
            row[f"{field}_latest"] = float(pd.to_numeric(ok[field], errors="coerce").iloc[-1]) if len(ok) else np.nan
        filed = [str(row[f"{f}_filed"]) for f in ("shares_out", "net_assets", "nav_per_share") if row[f"{f}_filed"]]
        row["filed_date"] = min(filed) if filed else ""
        rows.append(row)
    out = pd.DataFrame(rows)
    out = out[out["filed_date"].astype(str) != ""].reset_index(drop=True)
    if out.empty:
        raise ProjectionError("no anchor carries a publication date; the holdings fixture is unusable")
    return out.sort_values(["fund", "period_end"]).reset_index(drop=True)


def restatements(anchor_table: pd.DataFrame, *, tol: float = 1e-6) -> pd.DataFrame:
    """Every `(fund, period_end)` whose first publication and latest restatement disagree."""
    rows = []
    for r in anchor_table.itertuples():
        for field in ("shares_out", "net_assets", "nav_per_share"):
            first = getattr(r, field)
            latest = getattr(r, f"{field}_latest")
            if not (np.isfinite(first) and np.isfinite(latest)) or first == 0:
                continue
            if abs(latest / first - 1.0) > tol:
                rows.append(
                    {"fund": r.fund, "period_end": r.period_end, "field": field,
                     "first_published": first, "latest": latest, "ratio": latest / first}
                )
    return pd.DataFrame(rows, columns=["fund", "period_end", "field", "first_published", "latest", "ratio"])


# -------------------------------------------------------------------------------------- prices
def _series_from(doc: Mapping[str, object]) -> Mapping[str, Mapping[str, str]]:
    ts = doc.get("Time Series (Daily)", doc)
    if not isinstance(ts, Mapping) or not ts:
        raise ProjectionError("the price document carries no non-empty daily series")
    return ts  # type: ignore[return-value]


def price_table(ticker: str, root: Path = ROOT) -> pd.DataFrame:
    """Raw daily close and split coefficient for one ticker, oldest first, indexed by ISO date.

    RAW close (`4. close`) and not `5. adjusted close`: the share counts and NAVs this projection
    multiplies are the numbers as published on the day, so the price beside them has to be the
    price as printed on the day. An adjusted close would silently undo UNG's and USO's reverse
    splits on one side of the product and not the other.

    Two sources, because the repository already holds two of the six: the recorder's job
    `fund_market_prices` (D620, the four ProShares tickers) and
    `data/raw/alphavantage/daily_adjusted_etf/` (D382's cache, UNG and USO)."""
    disk = AV_DISK / f"{ticker}.json.gz"
    if disk.exists():
        with gzip.open(disk, "rt", encoding="utf-8") as fh:
            ts = _series_from(json.load(fh))
    else:
        rec = Recorder(root)
        got = [r for r in rec.records(PRICE_JOB, verify=False) if r.key == ticker]
        if not got:
            raise ProjectionError(
                f"no daily closes for {ticker}: not in {AV_DISK} and no `{PRICE_JOB}` record. "
                f"Run `scripts/fetch_fund_filings.py --prices`."
            )
        ts = _series_from(json.loads((rec.job_dir(PRICE_JOB) / got[-1].path).read_text(encoding="utf-8")))
    frame = pd.DataFrame(
        {
            "close": {str(d): float(v["4. close"]) for d, v in ts.items()},
            "split_coefficient": {str(d): float(v["8. split coefficient"]) for d, v in ts.items()},
        }
    )
    return frame.sort_index()


def closes(ticker: str, root: Path = ROOT) -> pd.Series:
    """Just the raw closes. See `price_table`."""
    return price_table(ticker, root)["close"]


def split_factor(dates: Sequence[str], splits: pd.Series) -> np.ndarray:
    """`k(t) = product of every split coefficient effective STRICTLY AFTER t`.

    **This is what puts `fund_nav_daily` and a filing on the same basis, and without it none of
    the share or NAV numbers below mean anything.** D619 measured that the ProShares NAV series
    is *fully back-adjusted for reverse splits* — BOIL's earliest rows read `NAV 8,000,000`
    against `0.50005` implied shares — while a filing states the count and the NAV **as published
    on the day**, and the market close is likewise as printed. So

        nav_published(t)    = nav_backadjusted(t) * k(t)
        shares_published(t) = shares_backadjusted(t) / k(t)
        aum(t)              = unchanged, because k cancels

    and on BOIL's first row k = 5.0e-6 across seven splits, turning `NAV 8,000,000` into **$40.00
    a share** and `0.50005 shares` into **100,010 shares**, which is what a 2x natural-gas fund
    looks like at launch. D619 recorded that *"No split source other than the series itself was
    available"*; there is one — Alpha Vantage's `8. split coefficient` — and it is used here.

    **k(t) for a date before the seal uses split ratios from after it**, and that is correct
    rather than a leak: those splits are already inside every pre-seal row of `fund_nav_daily`,
    which is what "fully back-adjusted" means, and a split ratio is a corporate action rather
    than a price or a return."""
    eff = splits[splits != 1.0].sort_index()
    if eff.empty:
        return np.ones(len(dates), dtype=float)
    days = np.array([str(d) for d in dates])
    keys = np.array([str(d) for d in eff.index])
    vals = eff.to_numpy(dtype=float)
    # cumulative product of every split at index >= i, i.e. of all splits strictly after a date
    suffix = np.concatenate([np.cumprod(vals[::-1])[::-1], [1.0]])
    pos = np.searchsorted(keys, days, side="right")
    return suffix[pos]


def as_published(truth: pd.DataFrame, prices: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """`fund_nav_daily` (back-adjusted) -> the numbers as they were published on the day.

    Adds `nav_pub`, `shares_pub` and `k_split`. `aum` is untouched and is asserted to still equal
    `nav_pub * shares_pub` to the same rounding tolerance D619's G1 uses, because the whole
    conversion is a multiplication by `k` on one factor and a division on the other: if the
    identity moves, the conversion is wrong and not merely imprecise."""
    out = []
    for fund in sorted(truth["fund"].unique()):
        g = truth[truth["fund"] == fund].sort_values("date").copy()
        k = split_factor([str(d) for d in g["date"]], prices[fund]["split_coefficient"])
        g["k_split"] = k
        g["nav_pub"] = g["nav"].to_numpy(dtype=float) * k
        g["shares_pub"] = g["shares_out"].to_numpy(dtype=float) / k
        resid = np.abs(g["nav_pub"].to_numpy() * g["shares_pub"].to_numpy() - g["aum"].to_numpy(dtype=float))
        tol = np.abs(g["nav"].to_numpy(dtype=float)) * (10.0 / 2.0 + 1e-3)
        if not np.all(resid <= tol * 1.000001):
            worst = int(np.argmax(resid - tol))
            raise ProjectionError(
                f"{fund}: the split conversion broke D619's AUM identity at "
                f"{g['date'].iloc[worst]} -- |nav_pub*shares_pub - aum| = {resid[worst]:,.2f} "
                f"against a tolerance of {tol[worst]:,.2f}. k cancels in the product, so a "
                f"failure here is the conversion and not the rounding."
            )
        out.append(g)
    return pd.concat(out, ignore_index=True)


def anchor_nav_check(truth_pub: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """The known-answer check on the split reconstruction: does the converted daily NAV agree
    with the NAV PER SHARE the filing printed for that same period end?

    Two entirely separate sources — ProShares' historical-NAV CSV run through the Alpha Vantage
    split coefficients, and the Statements of Financial Condition inside a 10-Q — and if the
    conversion is right they are the same number."""
    rows = []
    for fund in sorted(truth_pub["fund"].unique()):
        g = truth_pub[truth_pub["fund"] == fund]
        by_date = dict(zip((str(d) for d in g["date"]), g["nav_pub"].to_numpy(dtype=float), strict=True))
        fa = table[table["fund"] == fund]
        rel = []
        for r in fa.itertuples():
            filed_nav = float(getattr(r, "nav_per_share"))
            got = by_date.get(str(r.period_end))
            if got is None or not np.isfinite(filed_nav) or filed_nav == 0:
                continue
            rel.append(abs(got / filed_nav - 1.0))
        if rel:
            rows.append(
                {"fund": fund, "periods_compared": len(rel),
                 "median_rel": float(np.median(rel)), "p95_rel": float(np.percentile(rel, 95)),
                 "max_rel": float(max(rel))}
            )
    return pd.DataFrame(rows)


def creation_vs_price(truth: pd.DataFrame) -> pd.DataFrame:
    """Do creations lean WITH the NAV or AGAINST it? Measured, not asserted.

    This is here because the validation turns up something counter-intuitive: carrying the last
    filing's share count forward and multiplying by TODAY's close (`price_implied`) gives a WORSE
    AUM estimate than repeating the last filing's net assets (`step`), even though the second
    number is three months stale. The mechanism that would explain it is contrarian creation —
    shares grow when NAV falls — because then a stale share count and a stale NAV err in opposite
    directions and partly cancel, while a stale share count times a current price errs twice in
    the same direction. The claim is only worth making if the correlation is actually negative,
    so it is computed."""
    rows = []
    for fund in sorted(truth["fund"].unique()):
        g = truth[truth["fund"] == fund].sort_values("date")
        sh = g["shares_pub"].to_numpy(dtype=float)
        nav = g["nav_pub"].to_numpy(dtype=float)
        ok = (sh[:-1] > 0) & (sh[1:] > 0) & (nav[:-1] > 0) & (nav[1:] > 0)
        d_sh = np.log(sh[1:][ok] / sh[:-1][ok])
        d_nav = np.log(nav[1:][ok] / nav[:-1][ok])
        if d_sh.size < 30 or np.std(d_sh) == 0 or np.std(d_nav) == 0:
            continue
        rank = pd.Series(d_sh).rank().to_numpy(), pd.Series(d_nav).rank().to_numpy()
        rows.append(
            {
                "fund": fund, "days": int(d_sh.size),
                "pearson_dlog_shares_vs_dlog_nav": float(np.corrcoef(d_sh, d_nav)[0, 1]),
                "spearman": float(np.corrcoef(rank[0], rank[1])[0, 1]),
            }
        )
    return pd.DataFrame(rows)


def premium(truth: pd.DataFrame, price: Mapping[str, pd.Series]) -> pd.DataFrame:
    """`|close - NAV| / NAV` per fund, in basis points, on the days both exist.

    This is the size of the error `price_implied` inherits by using the market close where the
    fund's own NAV belongs, and it is measurable on exactly the four funds where NAV is known."""
    rows = []
    for fund in sorted(truth["fund"].unique()):
        g = truth[truth["fund"] == fund]
        if "nav_pub" not in g.columns:
            raise ProjectionError(
                "premium needs the AS-PUBLISHED NAV (`nav_pub`). The panel's own `nav` column is "
                "back-adjusted for reverse splits and the market close is not, so comparing them "
                "measures the split factor, not the premium. Run `as_published` first."
            )
        nav = pd.Series(g["nav_pub"].to_numpy(dtype=float), index=[str(d) for d in g["date"]])
        px = price[fund]
        both = nav.index.intersection(px.index)
        if len(both) == 0:
            raise ProjectionError(f"{fund}: NAV and closes share no dates")
        rel = (px.loc[both] - nav.loc[both]).abs() / nav.loc[both].abs()
        signed = (px.loc[both] - nav.loc[both]) / nav.loc[both].abs()
        rows.append(
            {
                "fund": fund, "days": int(len(both)),
                "median_bp": float(np.median(rel) * 1e4),
                "p95_bp": float(np.percentile(rel, 95) * 1e4),
                "max_bp": float(rel.max() * 1e4),
                "median_signed_bp": float(np.median(signed) * 1e4),
                "first": str(min(both)), "last": str(max(both)),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------- projection
def project(
    fund_anchors: pd.DataFrame,
    dates: Sequence[str],
    price: pd.Series,
    *,
    method: str,
    clock: str,
) -> pd.DataFrame:
    """One fund's daily estimate between its quarterly anchors.

    `clock="filed"` keys the anchor on its publication date and is the only point-in-time
    reading; `clock="period"` keys it on the period end and is the no-lag counterfactual.
    Dates before the first usable anchor produce no row at all — an estimate with nothing behind
    it is not an estimate."""
    if method not in METHODS:
        raise ProjectionError(f"method {method!r} is not one of {METHODS}")
    if clock not in CLOCKS:
        raise ProjectionError(f"clock {clock!r} is not one of {CLOCKS}")
    key = "filed_date" if clock == "filed" else "period_end"
    a = fund_anchors.dropna(subset=["shares_out"]).sort_values(key).reset_index(drop=True)
    if a.empty:
        raise ProjectionError("this fund has no anchor with a share count")
    keys = a[key].astype(str).to_numpy()
    if not np.all(keys[1:] >= keys[:-1]):  # pragma: no cover - sorted above
        raise ProjectionError(f"anchors are not ordered on {key}")
    shares = a["shares_out"].to_numpy(dtype=float)
    navps = pd.to_numeric(a["nav_per_share"], errors="coerce").to_numpy(dtype=float)

    day = np.array([str(d) for d in dates])
    idx = np.searchsorted(keys, day, side="right") - 1
    live = idx >= 0
    out_idx = np.clip(idx, 0, len(keys) - 1)

    est_shares = shares[out_idx].astype(float)
    if method == "linear":
        # HINDSIGHT. The weight uses the NEXT anchor, which is published after every day it
        # touches. Kept so the record can quote what perfect quarterly interpolation would buy.
        nxt = np.minimum(out_idx + 1, len(keys) - 1)
        has_next = out_idx + 1 <= len(keys) - 1
        d0 = np.array([_ordinal(k) for k in keys[out_idx]], dtype=float)
        d1 = np.array([_ordinal(k) for k in keys[nxt]], dtype=float)
        dt_days = np.array([_ordinal(k) for k in day], dtype=float)
        span = np.where(d1 > d0, d1 - d0, np.nan)
        w = np.clip((dt_days - d0) / span, 0.0, 1.0)
        w = np.where(np.isfinite(w) & has_next, w, 0.0)
        est_shares = shares[out_idx] * (1.0 - w) + shares[nxt] * w

    close = price.reindex(day).to_numpy(dtype=float)
    close = pd.Series(close).ffill().to_numpy()
    nav_proxy = close if method in ("price_implied", "linear") else navps[out_idx]
    aum = est_shares * nav_proxy

    frame = pd.DataFrame(
        {
            "date": day,
            "shares_out_est": est_shares,
            "aum_est": aum,
            "nav_proxy": nav_proxy,
            "method": method,
            "clock": clock,
            "anchor_period_end": a["period_end"].astype(str).to_numpy()[out_idx],
            "anchor_filed_date": a["filed_date"].astype(str).to_numpy()[out_idx],
            "est_flag": 1,
        }
    )
    return frame.loc[live].reset_index(drop=True)


def _ordinal(iso: str) -> int:
    return dt.date.fromisoformat(str(iso)).toordinal()


# ---------------------------------------------------------------------------------- validation
def _rel_errors(est: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    ok = np.isfinite(est) & np.isfinite(truth) & (np.abs(truth) > 0)
    if not ok.any():
        return {"n": 0, "median_rel": float("nan"), "p95_rel": float("nan"), "max_rel": float("nan")}
    rel = np.abs(est[ok] - truth[ok]) / np.abs(truth[ok])
    return {
        "n": int(ok.sum()),
        "median_rel": float(np.median(rel)),
        "p95_rel": float(np.percentile(rel, 95)),
        "max_rel": float(rel.max()),
    }


def _flow_errors(est: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """What the projection does to the quantity the ledger's P3 actually uses: DAILY CREATIONS.

    `shares_out` is a level and a stale level is still roughly right; `delta shares` is the
    difference of a level, and differencing a piecewise-constant estimate gives zero on almost
    every day and the whole quarter's creation on one. So the level's error and the flow's error
    are different questions, and only the second one is the deposit's."""
    d_est = np.diff(est)
    d_tru = np.diff(truth)
    ok = np.isfinite(d_est) & np.isfinite(d_tru)
    d_est, d_tru = d_est[ok], d_tru[ok]
    if d_est.size < 3:
        return {"n": int(d_est.size)}
    nonzero_truth = np.abs(d_tru) > 0
    scale = float(np.median(np.abs(d_tru[nonzero_truth]))) if nonzero_truth.any() else float("nan")
    both_move = nonzero_truth & (np.abs(d_est) > 0)
    corr = float(np.corrcoef(d_est, d_tru)[0, 1]) if np.std(d_est) > 0 and np.std(d_tru) > 0 else float("nan")
    return {
        "n": int(d_est.size),
        "corr": corr,
        "days_truth_moves": int(nonzero_truth.sum()),
        "days_est_moves": int((np.abs(d_est) > 0).sum()),
        "days_both_move": int(both_move.sum()),
        "sign_agreement_when_both_move": (
            float(np.mean(np.sign(d_est[both_move]) == np.sign(d_tru[both_move]))) if both_move.any() else float("nan")
        ),
        "median_abs_error_over_median_abs_truth_move": (
            float(np.median(np.abs(d_est - d_tru)) / scale) if np.isfinite(scale) and scale > 0 else float("nan")
        ),
    }


def validate(*, reserved_from: str = RESERVED_FROM) -> dict[str, object]:
    holdings = read_holdings()
    table = anchors(holdings)
    loaded = load_panel("fund_nav_daily", reserved_from=reserved_from)
    truth = loaded.frame.copy()
    truth["date"] = truth["date"].astype(str)
    if truth["date"].max() >= reserved_from:
        raise ProjectionError(
            f"the truth frame reaches {truth['date'].max()}, at or past the reserved cut "
            f"{reserved_from}. load_panel's guard should have made this impossible."
        )
    prices = {f: price_table(f) for f in TRUTH_FUNDS}
    price = {f: prices[f]["close"] for f in TRUTH_FUNDS}
    truth = as_published(truth, prices)
    report: dict[str, object] = {
        "reserved_from": reserved_from,
        "truth_last_date": str(truth["date"].max()),
        "truth_rows": int(len(truth)),
        "panel_sha256": loaded.sha256,
        "splits_used": {
            f: {str(d): float(c) for d, c in prices[f]["split_coefficient"].items() if c != 1.0}
            for f in TRUTH_FUNDS
        },
        "anchor_nav_vs_converted_daily_nav": anchor_nav_check(truth, table).to_dict("records"),
        "premium_close_vs_nav_bp": premium(truth, price).to_dict("records"),
        "creation_vs_price": creation_vs_price(truth).to_dict("records"),
        "restatements": restatements(table).to_dict("records"),
        "methods": {},
    }
    per: dict[str, object] = {}
    for method in METHODS:
        for clock in CLOCKS:
            cell: dict[str, object] = {}
            for fund in TRUTH_FUNDS:
                fa = table[table["fund"] == fund]
                g = truth[truth["fund"] == fund].sort_values("date")
                dates = [str(d) for d in g["date"]]
                est = project(fa, dates, price[fund], method=method, clock=clock)
                joined = g.merge(est, on="date", how="inner")
                if joined.empty:
                    raise ProjectionError(f"{fund}/{method}/{clock}: the estimate covers no truth day")
                cell[fund] = {
                    "days": int(len(joined)),
                    "first": str(joined["date"].min()),
                    "last": str(joined["date"].max()),
                    # `shares_pub` and NOT `shares_out`: the panel's column is back-adjusted for
                    # reverse splits and a filing's count is as published, so comparing them
                    # would measure BOIL's seven splits rather than the method.
                    "shares_out": _rel_errors(
                        joined["shares_out_est"].to_numpy(dtype=float),
                        joined["shares_pub"].to_numpy(dtype=float),
                    ),
                    "aum": _rel_errors(
                        joined["aum_est"].to_numpy(dtype=float),
                        joined["aum"].to_numpy(dtype=float),
                    ),
                    "creation_flow_delta_shares": _flow_errors(
                        joined["shares_out_est"].to_numpy(dtype=float),
                        joined["shares_pub"].to_numpy(dtype=float),
                    ),
                }
            per[f"{method}/{clock}"] = cell
    report["methods"] = per
    report["hindsight_methods"] = list(HINDSIGHT_METHODS)
    return report


def read_holdings() -> pd.DataFrame:
    if not HOLDINGS.exists():
        raise ProjectionError(
            f"{HOLDINGS} does not exist; run scripts/build_fund_holdings_quarterly.py --build"
        )
    frame = pd.read_csv(
        HOLDINGS, encoding="utf-8",
        dtype={"period_end": str, "fund": str, "filed_date": str, "kind": str},
    )
    return frame


# --------------------------------------------------------------------------------------- build
def build(method: str, clock: str = "filed") -> tuple[pd.DataFrame, dict[str, object]]:
    if method in HINDSIGHT_METHODS:
        raise ProjectionError(
            f"method {method!r} interpolates towards an anchor that is published 40-90 days after "
            f"the period it closes, so a panel built with it is a one-quarter look-ahead on every "
            f"row. It is measured in --validate as a bound and it is not written to disk."
        )
    if clock != "filed":
        raise ProjectionError(
            f"clock {clock!r}: the written panel uses the `filed` clock only. Deposit section 3.1 "
            f"line 70 -- 'Never back-fill today's composition across history.'"
        )
    table = anchors(read_holdings())
    frames = []
    prov: dict[str, object] = {}
    for fund in TARGET_FUNDS:
        fa = table[table["fund"] == fund]
        if fa.empty:
            raise ProjectionError(f"no anchors for {fund}")
        px = closes(fund)
        first = fa["filed_date"].astype(str).min()
        dates = [d for d in px.index if d >= first]
        est = project(fa, dates, px, method=method, clock=clock)
        est.insert(1, "fund", fund)
        frames.append(est[list(COLUMNS)])
        prov[fund] = {
            "anchors": int(len(fa)),
            "first_anchor_period_end": str(fa["period_end"].min()),
            "first_anchor_filed": str(first),
            "rows": int(len(est)),
            "span": [str(est["date"].min()), str(est["date"].max())],
            "price_source": str((AV_DISK / f"{fund}.json.gz").relative_to(REPO)),
        }
    panel = pd.concat(frames, ignore_index=True).sort_values(["fund", "date"]).reset_index(drop=True)
    return panel, prov


REQUIRED_META_KEYS = (
    "spec", "record", "builder", "built_utc", "columns", "method", "clock", "rows", "funds",
    "per_fund", "measured_uncertainty", "sha256", "date_col", "holdout", "what_this_is_not",
)


def write_outputs(panel: pd.DataFrame, prov: Mapping[str, object], report: Mapping[str, object],
                  method: str) -> dict[str, object]:
    FIX.mkdir(parents=True, exist_ok=True)
    raw = panel.to_csv(index=False, encoding="utf-8", lineterminator="\n").encode("utf-8")
    with open(OUT, "wb") as fb, gzip.GzipFile(filename="", mode="wb", fileobj=fb, mtime=0, compresslevel=9) as gz:
        gz.write(raw)
    cell = report["methods"][f"{method}/filed"]  # type: ignore[index]
    meta: dict[str, object] = {
        "spec": "D620; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.1 lines 56-70 (the fund universe "
                "and the point-in-time rule). Answers the principal's question of 2026-09-22: "
                "'Can we project this backwards / in between the filings based on current AUM and "
                "shares?'",
        "record": "D620",
        "builder": "scripts/project_fund_panel.py",
        "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "columns": list(COLUMNS),
        "method": method,
        "clock": "filed",
        "method_definition": {
            "step": "shares = the last anchor published on or before the date, held flat; "
                    "aum = shares x that anchor's NAV per share",
            "price_implied": "shares = the last anchor published on or before the date, held "
                             "flat; aum = shares x the day's raw market close",
            "linear": "HINDSIGHT, never written: shares interpolated towards the NEXT anchor, "
                      "which is published 40-90 days after the period it closes",
        },
        "rows": int(len(panel)),
        "funds": list(TARGET_FUNDS),
        "per_fund": prov,
        "measured_uncertainty": {
            "how": "Every number here is the error of THIS method on the four funds that have a "
                   "daily truth series (BOIL, KOLD, UCO, SCO; fund_nav_daily, D619), measured "
                   "on rows dated 2023-12-29 or earlier through "
                   "load_panel(reserved_from='2024-01-01'). It is carried to UNG and USO as the "
                   "stated uncertainty because those two have no daily truth to measure against.",
            "per_fund": cell,
            "premium_close_vs_nav_bp": report["premium_close_vs_nav_bp"],
            "restatements_found": report["restatements"],
        },
        "what_this_is_not": [
            "NOT a truth series. Every row carries est_flag = 1 and nothing here is written back "
            "into fund_nav_daily.",
            "NOT a creation-flow series. Differencing a piecewise-constant share estimate gives "
            "zero on almost every day and a whole quarter's creations on one; the measured flow "
            "errors are in `measured_uncertainty.per_fund.*.creation_flow_delta_shares` and they "
            "are the reason this panel must not be differenced for P3.",
            "NOT NAV. `nav_proxy` is the raw market CLOSE for price_implied and the last "
            "anchor's published NAV per share for step. The close-versus-NAV premium measured on "
            "the four funds that have both is in `measured_uncertainty.premium_close_vs_nav_bp`.",
        ],
        "sha256": frozen.sha256_file(OUT, text_normalise=False),
        "sha256_uncompressed_csv": hashlib.sha256(raw).hexdigest(),
        "bytes": OUT.stat().st_size,
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename)",
        "date_col": "date",
        "wrong_cuts": ["anchor_filed_date", "anchor_period_end"],
        "holdout": HOLDOUT,
    }
    absent = [k for k in REQUIRED_META_KEYS if k not in meta]
    if absent:
        raise ProjectionError(f"meta is missing declared keys {absent}")
    META.write_text(json.dumps(meta, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    return meta


# ------------------------------------------------------------------------------------ selftest
_SYNTHETIC_DAYS = 200
_SYNTHETIC_LAST_ANCHOR = 180


def _synthetic(kind: str) -> tuple[pd.DataFrame, list[str], pd.Series, np.ndarray]:
    """A fund whose truth is known by construction.

    `flat`   shares never move between anchors  -> `step` is EXACT
    `linear` shares move by a constant per day  -> `linear` is EXACT and `step` is not
    """
    days = [str(dt.date(2020, 1, 1) + dt.timedelta(days=i)) for i in range(0, 200)]
    anchor_days = [days[0], days[90], days[180]]
    if kind == "flat":
        truth = np.where(np.arange(200) < 90, 1000.0, np.where(np.arange(200) < 180, 2000.0, 3000.0))
    else:
        truth = 1000.0 + 10.0 * np.arange(200, dtype=float)
    vals = [truth[0], truth[90], truth[180]]
    table = pd.DataFrame(
        {
            "fund": "TEST", "period_end": anchor_days, "filed_date": anchor_days,
            "shares_out": vals, "net_assets": [v * 10.0 for v in vals], "nav_per_share": 10.0,
        }
    )
    price = pd.Series(10.0, index=days)
    return table, days, price, truth


def selftest() -> int:
    # Only the days INSIDE the anchored span are compared: past the last anchor every method
    # extrapolates flat, and an exactness claim that included those days would be false for a
    # reason that has nothing to do with the method.
    inside = _SYNTHETIC_LAST_ANCHOR + 1
    for kind, method in (("flat", "step"), ("linear", "linear")):
        table, days, price, truth = _synthetic(kind)
        est = project(table, days, price, method=method, clock="filed")
        got = est["shares_out_est"].to_numpy(dtype=float)[:inside]
        worst = float(np.max(np.abs(got - truth[:inside])))
        P(f"  OK   synthetic {kind:<6} + {method:<13} max |est - truth| = {worst:.12g} over {len(got)} "
          f"days inside the anchored span")
        if worst > 1e-9:
            P(f"  FAILED: {method} is not exact on the {kind} fund")
            return 1
    table, days, price, truth = _synthetic("linear")
    est = project(table, days, price, method="step", clock="filed")
    worst = float(np.max(np.abs(est["shares_out_est"].to_numpy(dtype=float)[:inside] - truth[:inside])))
    P(f"  OK   synthetic linear + step          max |est - truth| = {worst:,.0f} (step is NOT exact here, "
      f"which is the point)")
    if worst < 1.0:
        P("  FAILED: step reproduced a moving series exactly; the case cannot discriminate")
        return 1

    breaks: list[tuple[str, object]] = []

    def _unknown_method() -> object:
        t, d, p, _ = _synthetic("flat")
        return project(t, d, p, method="spline", clock="filed")

    def _unknown_clock() -> object:
        t, d, p, _ = _synthetic("flat")
        return project(t, d, p, method="step", clock="realtime")

    def _no_anchor_with_shares() -> object:
        t, d, p, _ = _synthetic("flat")
        t["shares_out"] = np.nan
        return project(t, d, p, method="step", clock="filed")

    def _build_with_hindsight() -> object:
        return build("linear")

    def _build_on_the_period_clock() -> object:
        return build("step", clock="period")

    def _anchors_missing_column() -> object:
        return anchors(pd.DataFrame({"fund": ["X"], "period_end": ["2020-01-01"]}))

    def _anchors_with_no_publication_date() -> object:
        return anchors(
            pd.DataFrame(
                {"fund": ["X"], "period_end": ["2020-01-01"], "filed_date": ["2020-03-01"],
                 "shares_out": [np.nan], "net_assets": [np.nan], "nav_per_share": [np.nan]}
            )
        )

    def _premium_with_no_shared_dates() -> object:
        # `nav_pub` present, so the break lands on the OVERLAP and not on the basis guard.
        truth = pd.DataFrame(
            {"fund": ["BOIL"], "date": ["2020-01-01"], "nav": [10.0], "nav_pub": [10.0]}
        )
        return premium(truth, {"BOIL": pd.Series({"2021-01-01": 10.0})})

    def _premium_on_the_back_adjusted_nav() -> object:
        truth = pd.DataFrame({"fund": ["BOIL"], "date": ["2020-01-01"], "nav": [10.0]})
        return premium(truth, {"BOIL": pd.Series({"2020-01-01": 10.0})})

    def _split_conversion_breaks_the_identity() -> object:
        days = ["2012-05-10", "2012-05-11"]
        nav = np.array([100.0, 20.0])
        shares = np.array([200.0, 1000.0])
        truth = pd.DataFrame(
            {"date": days, "fund": "BOIL", "nav": nav, "shares_out": shares, "aum": nav * shares}
        )
        truth.loc[0, "aum"] = float(truth.loc[0, "aum"]) * 1.5
        prices = {
            "BOIL": pd.DataFrame({"close": [20.0, 20.0], "split_coefficient": [1.0, 0.2]}, index=days)
        }
        return as_published(truth, prices)

    def _empty_price_document() -> object:
        return _series_from({})

    breaks += [
        ("unknown method", _unknown_method),
        ("unknown clock", _unknown_clock),
        ("no anchor carries a share count", _no_anchor_with_shares),
        ("build with the hindsight method", _build_with_hindsight),
        ("build on the period clock", _build_on_the_period_clock),
        ("anchors: missing column", _anchors_missing_column),
        ("anchors: no publication date", _anchors_with_no_publication_date),
        ("premium: no shared dates", _premium_with_no_shared_dates),
        ("premium: given the back-adjusted NAV", _premium_on_the_back_adjusted_nav),
        ("as_published: the AUM identity broken", _split_conversion_breaks_the_identity),
        ("prices: empty document", _empty_price_document),
    ]

    silent = 0
    for name, fn in breaks:
        try:
            fn()  # type: ignore[operator]
        except ProjectionError as exc:
            P(f"  RAISED {name}: {str(exc)[:88]}")
        else:
            silent += 1
            P(f"  DID NOT RAISE {name}  <-- a guard that cannot fire")
    P(f"  selftest: {len(breaks)} breaks, {len(breaks) - silent} fired, {silent} silent")
    return 1 if silent else 0


# ---------------------------------------------------------------------------------------- main
def _rows_of(report: Mapping[str, object], key: str) -> list[dict[str, Any]]:
    got = report[key]
    assert isinstance(got, list)
    return got


def _summary(report: Mapping[str, object]) -> None:
    P(f"  premium |close - NAV| / NAV, bp (rows <= {report['truth_last_date']}):")
    for row in _rows_of(report, "premium_close_vs_nav_bp"):
        P(f"    {row['fund']:<5} n={row['days']:>5}  median {row['median_bp']:>7.1f}  "
          f"p95 {row['p95_bp']:>8.1f}  max {row['max_bp']:>9.1f}")
    P("  creations vs NAV, daily d-log correlation (negative = contrarian):")
    for row in _rows_of(report, "creation_vs_price"):
        P(f"    {row['fund']:<5} n={row['days']:>5}  pearson {row['pearson_dlog_shares_vs_dlog_nav']:>+8.4f}  "
          f"spearman {row['spearman']:>+8.4f}")
    P("  filing NAV/share vs the converted daily NAV (the split reconstruction's known answer):")
    for row in _rows_of(report, "anchor_nav_vs_converted_daily_nav"):
        P(f"    {row['fund']:<5} {row['periods_compared']:>3} period ends  median rel "
          f"{row['median_rel']:.2e}  p95 {row['p95_rel']:.2e}  max {row['max_rel']:.2e}")
    P("  relative error, median / p95, per fund")
    P(f"    {'method/clock':<22} {'fund':<5} {'shares median':>13} {'shares p95':>11} "
      f"{'aum median':>11} {'aum p95':>9} {'flow corr':>10} {'flow |e|/scale':>15}")
    methods = report["methods"]
    assert isinstance(methods, dict)
    for cellname, cell in methods.items():
        for fund, c in cell.items():
            fl = c["creation_flow_delta_shares"]
            P(f"    {cellname:<22} {fund:<5} {c['shares_out']['median_rel']:>13.5f} "
              f"{c['shares_out']['p95_rel']:>11.5f} {c['aum']['median_rel']:>11.5f} "
              f"{c['aum']['p95_rel']:>9.5f} {fl.get('corr', float('nan')):>10.4f} "
              f"{fl.get('median_abs_error_over_median_abs_truth_move', float('nan')):>15.3f}")
    restated = _rows_of(report, "restatements")
    if restated:
        P(f"  restatements (first publication != latest): {len(restated)}")
        for r in restated[:8]:
            P(f"    {r['fund']:<5} {r['period_end']}  {r['field']:<14} "
              f"{r['first_published']:>16,.2f} -> {r['latest']:>16,.2f}  x{r['ratio']:.4f}")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--premium", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--method", default="price_implied", choices=[m for m in METHODS if m not in HINDSIGHT_METHODS])
    ap.add_argument("--json", action="store_true", help="print the whole validation report")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.selftest:
        return selftest()
    if args.premium:
        loaded = load_panel("fund_nav_daily", reserved_from=RESERVED_FROM)
        truth = loaded.frame.copy()
        truth["date"] = truth["date"].astype(str)
        prices = {f: price_table(f) for f in TRUTH_FUNDS}
        truth = as_published(truth, prices)
        P(anchor_nav_check(truth, anchors(read_holdings())).to_string(index=False))
        P(premium(truth, {f: prices[f]["close"] for f in TRUTH_FUNDS}).to_string(index=False))
        return 0
    if args.validate or args.build:
        report = validate()
        if args.json:
            P(json.dumps(report, indent=1, default=str))
        else:
            _summary(report)
    if args.build:
        panel, prov = build(args.method)
        meta = write_outputs(panel, prov, report, args.method)
        P(f"  {len(panel):,} rows -> {OUT.relative_to(REPO)} (method {args.method}, clock filed)")
        for fund, p in prov.items():
            assert isinstance(p, dict)
            P(f"  {fund:<5} {p['rows']:>5} rows {p['span'][0]}..{p['span'][1]}  "
              f"{p['anchors']} anchors from {p['first_anchor_filed']}")
        P(f"  sha256 {meta['sha256']}  bytes {meta['bytes']:,}")
        return 0
    if not args.validate:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
