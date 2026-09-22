"""Does the change in Robinhood holders track creations? — D621's validation measurement.

    uv run python scripts/retail_attention_report.py --selftest
    uv run python scripts/retail_attention_report.py --run
    uv run python scripts/retail_attention_report.py --check

WHAT THIS MEASURES, AND WHAT IT IS NOT
--------------------------------------
D621 replaces the deposit's hourly-Wikipedia attention row with CREATIONS as the retail-demand
measure. A replacement that is only argued is not a replacement, so the claim is measured against
the one series on disk that counts RETAIL ACCOUNTS: the Robintrack Robinhood holder-count
archive, 2018-05-02 to 2020-08-13.

**THIS IS A DATA-QUALITY MEASUREMENT AND NOT A SIGNAL TEST.** No return is computed, no price bar
is read, no null is run, nothing is scored, and no verdict about tradeability is available from
anything below. The question is narrow and factual: over the overlap window, does the daily
change in Robinhood holders move with the daily change in shares outstanding? If it does not,
creations are not a retail measure and D621's amendment is wrong on its own terms.

FOUR CONVENTIONS ARE DECLARED, BECAUSE EACH CHANGES THE NUMBER
---------------------------------------------------------------
1. **The interval.** A fund's share count exists on trading days only, so a creation is
   `shares_out[d] - shares_out[prev(d)]` where `prev(d)` is the previous day IN THE SOURCE
   (`retail_attention.creations`). The holder change is differenced over THE SAME INTERVAL,
   `holders(d) - holders(prev(d))`, not over `d - 1 day`. Two series differenced over different
   windows are not two readings of one week.
2. **The daily cut for holders** is the LAST poll of the UTC day
   (`retail_attention.daily_holders`, which states why). Inside a site outage there is no poll
   and the day is `None`, never 0.
3. **Lead and lag are in SERIES STEPS, not calendar days.** `lag = +k` pairs the creation at
   index `i` with the holder change at index `i + k`: positive `k` asks whether holders move
   AFTER creations. Over a trading-day series a step is one trading day.
4. **A "creation day"** is a day whose `|creation|` exceeds the 90th percentile of `|creation|`
   over that fund's own overlap window, by linear interpolation between order statistics
   (`retail_attention.quantile_linear`, numpy's default), compared STRICTLY.

BOTH STATISTICS, ALWAYS TOGETHER. Spearman and Pearson are reported side by side for every cell.
The holder series has a meme-era right tail — USO runs from 5,103 holders to 220,905 inside the
window — and a Pearson on a series with one spike in it is a statistic about the spike. The
golden's Case 1 is that disagreement written out on ten synthetic rows: 0.9394 against 0.4777.

THE OUTPUT IS A PURE FUNCTION OF ITS INPUTS. `data/retail_attention_validation.json` carries no
build timestamp — it carries the sha256 of every file it read instead — so `--check` can
recompute it and compare byte for byte. A number that cannot be reproduced from the committed
fixtures is a number nobody can check.

READING THE PANEL. `fund_nav_daily` is read through `panels.load_panel(..., reserved_from=
"2024-01-01")`, D609's chokepoint, so the reserved slice is filtered, asserted absent and
recorded. The Robintrack archive ends 2020-08-13 and cannot reach the cut at all.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.data.panels import load_panel  # noqa: E402
from backtest_framework.data.retail_attention import (  # noqa: E402
    MAX_GAP_DAYS,
    OUTAGES,
    ROBINTRACK_SPAN,
    CreationSeries,
    HolderObs,
    RetailAttentionError,
    creations,
    daily_holders,
    pearson,
    quantile_linear,
    read_holder_fixture,
    spearman,
)
from backtest_framework.validation.frozen import sha256_file  # noqa: E402

OUT = REPO / "data" / "retail_attention_validation.json"
REQUIRED_OUTPUTS = (OUT,)

NAV_PANEL = "fund_nav_daily"
NAV_PATH = REPO / "data" / "fixtures" / "fund_nav_daily.csv.gz"
RT_PATH = REPO / "data" / "fixtures" / "robintrack_energy_funds.csv.gz"
GDELT_PATH = REPO / "data" / "fixtures" / "gdelt_hourly_sample.csv.gz"
GDELT_META = REPO / "data" / "fixtures" / "gdelt_hourly_sample.meta.json"

RESERVED_FROM = "2024-01-01"

#: The four with a share-count truth on disk, and the two without (D619: USCF publishes no free
#: NAV history, so UNG and USO carry a holder series and nothing to correlate it against).
WITH_TRUTH = ("BOIL", "KOLD", "UCO", "SCO")
HOLDERS_ONLY = ("UNG", "USO")

LAGS = (-1, 0, 1)
CREATION_DAY_P = 0.90

#: A step whose share count moves by more than this fraction is FLAGGED, not dropped. The
#: ProShares NAV series is fully back-adjusted for reverse splits (D619), so a split should leave
#: no discontinuity at all and a day above this line is either a real, enormous creation or an
#: adjustment that did not take. Either way it belongs in the record rather than in a footnote.
SPLIT_FLAG = 0.5

#: Spot-check depth. The report indexes 115,290 holder rows into a dict for speed and then proves
#: the index against the library's own `daily_holders` on this many (ticker, day) pairs, spread
#: evenly through each ticker's series. "Prove chunk == whole before you trust the fast path."
SPOTS = 25


def P(*a: object) -> None:
    print(*a, flush=True)


def expect_raise(fn, exc_type, what: str) -> None:
    try:
        fn()
    except exc_type as exc:
        P(f"    RAISES on {what}: {type(exc).__name__}: {str(exc)[:110]}")
        return
    raise AssertionError(f"guard did not raise {exc_type.__name__} on {what}")


# ------------------------------------------------------------------------------------- inputs
def load_shares(reserved_from: str = RESERVED_FROM) -> tuple[dict[str, dict[dt.date, float]], dict]:
    """`{fund: {day: shares_out}}` through D609's chokepoint, plus that read's window record."""
    loaded = load_panel(NAV_PANEL, reserved_from=reserved_from,
                        usecols=["date", "fund", "shares_out"])
    frame = loaded.frame
    out: dict[str, dict[dt.date, float]] = {}
    for day_text, fund, shares in zip(
        frame["date"].tolist(), frame["fund"].tolist(), frame["shares_out"].tolist(), strict=True
    ):
        day = dt.date.fromisoformat(str(day_text))
        value = float(shares)
        if value <= 0.0:
            raise RetailAttentionError(
                f"{fund} on {day}: shares_out is {value}. D619 excluded the seed rows whose "
                f"published count rounds to zero; a non-positive count here means the panel has "
                f"changed and the creation arithmetic below would be dividing by nothing."
            )
        out.setdefault(str(fund), {})[day] = value
    return out, dict(loaded.record) | {"sha256": loaded.sha256}


def holder_index(series: list[HolderObs]) -> dict[tuple[str, dt.date], int]:
    """`{(ticker, UTC day): the day's LAST poll}` — the fast path for `daily_holders`.

    Proved against the library function itself in `_prove_index`, on `SPOTS` days per ticker.
    The rule it implements is `daily_holders`'s rule and nothing else: the last poll whose UTC
    instant falls inside the day.
    """
    best: dict[tuple[str, dt.date], HolderObs] = {}
    for obs in series:
        key = (obs.ticker, obs.ts_utc.date())
        prev = best.get(key)
        if prev is None or obs.ts_utc >= prev.ts_utc:
            best[key] = obs
    return {k: v.holders for k, v in best.items()}


def _prove_index(series: list[HolderObs], index: dict[tuple[str, dt.date], int]) -> dict[str, int]:
    """The index agrees with `retail_attention.daily_holders` on a spread of days per ticker,
    INCLUDING days with no poll (which must be `None` on both sides)."""
    by_ticker: dict[str, list[HolderObs]] = {}
    for obs in series:
        by_ticker.setdefault(obs.ticker, []).append(obs)
    checked: dict[str, int] = {}
    for ticker, rows in by_ticker.items():
        first, last = rows[0].ts_utc.date(), rows[-1].ts_utc.date()
        span = (last - first).days
        probes = [first + dt.timedelta(days=round(span * k / (SPOTS - 1))) for k in range(SPOTS)]
        # plus one day inside each declared outage, where both sides must answer None
        probes += [a.date() + dt.timedelta(days=2) for a, _b in OUTAGES]
        for day in probes:
            want = daily_holders(rows, ticker, day)
            got = index.get((ticker, day))
            if want != got:
                raise AssertionError(
                    f"{ticker} {day}: the index says {got!r} and daily_holders says {want!r}. "
                    f"The fast path and the reference disagree, so the fast path is not the "
                    f"reference and nothing below it may be trusted."
                )
        checked[ticker] = len(probes)
    return checked


# ------------------------------------------------------------------------------------ pairing
def pair(series: CreationSeries, index: dict[tuple[str, dt.date], int],
         ticker: str, lo: dt.date, hi: dt.date) -> list[tuple[dt.date, float, float]]:
    """`(day, Δshares, Δholders)` over the SAME interval, for days inside `[lo, hi]`.

    A step whose either end has no holder poll is DROPPED and counted, never zero-filled; the
    two ~10-day site outages are where that bites, and a zero there would be the largest
    fictional flow in the sample.
    """
    out: list[tuple[dt.date, float, float]] = []
    for day, dshares in series.deltas:
        if not lo <= day <= hi:
            continue
        prev = series.prev_day(day)
        a = index.get((ticker, prev))
        b = index.get((ticker, day))
        if a is None or b is None:
            continue
        out.append((day, dshares, float(b - a)))
    return out


def correlations(rows: list[tuple[dt.date, float, float]]) -> dict[str, dict[str, object]]:
    """Spearman AND Pearson at every lag in `LAGS`, each with its own n.

    `lag = +k` pairs `Δshares[i]` with `Δholders[i + k]`: a positive lag asks whether holders
    move AFTER creations. Both statistics are reported at every lag and neither is ever quoted
    without the other.
    """
    out: dict[str, dict[str, object]] = {}
    for lag in LAGS:
        xs: list[float] = []
        ys: list[float] = []
        for i, (_d, dshares, _dh) in enumerate(rows):
            j = i + lag
            if 0 <= j < len(rows):
                xs.append(dshares)
                ys.append(rows[j][2])
        name = f"lag_{lag:+d}".replace("+0", "0").replace("lag_0", "lag_0")
        cell: dict[str, object] = {"n": len(xs)}
        if len(xs) >= 3 and len(set(xs)) > 1 and len(set(ys)) > 1:
            cell["spearman"] = spearman(xs, ys)
            cell["pearson"] = pearson(xs, ys)
        else:
            cell["spearman"] = None
            cell["pearson"] = None
            cell["why_none"] = (
                "fewer than three pairs, or one side is constant; a correlation with no "
                "denominator is not reported as 0.0"
            )
        out[name] = cell
    return out


def describe(values: list[float]) -> dict[str, object]:
    """n, mean, median, sd, min, max, and the counts of zero / positive — the distribution, never
    the mean alone. `CLAUDE.md`: a mean below its median is the tell that the tail is doing the
    work, and it can only be seen when both are printed."""
    if not values:
        return {"n": 0}
    n = len(values)
    return {
        "n": n,
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "sd": statistics.stdev(values) if n > 1 else None,
        "min": min(values),
        "max": max(values),
        "n_zero": sum(1 for v in values if v == 0.0),
        "n_positive": sum(1 for v in values if v > 0.0),
        "share_positive": sum(1 for v in values if v > 0.0) / n,
    }


def creation_day_cell(rows: list[tuple[dt.date, float, float]]) -> dict[str, object]:
    """The headline cell: on the fund's biggest creation days, does the holder count rise?"""
    if len(rows) < 3:
        return {"n_rows": len(rows), "p90_abs_creation": None, "n_creation_days": 0}
    magnitudes = [abs(d) for _day, d, _h in rows]
    threshold = quantile_linear(magnitudes, CREATION_DAY_P)
    picked = [(day, d, h) for day, d, h in rows if abs(d) > threshold]
    pos = sum(1 for _day, _d, h in picked if h > 0.0)
    return {
        "n_rows": len(rows),
        "p90_abs_creation": threshold,
        "n_creation_days": len(picked),
        "n_dholders_positive": pos,
        "share_dholders_positive": (pos / len(picked)) if picked else None,
        "rule": (
            f"|creation| STRICTLY above the {CREATION_DAY_P:.0%} quantile of |creation| over "
            f"this fund's own overlap rows, linear interpolation between order statistics"
        ),
        "biggest": [
            {"day": day.isoformat(), "d_shares": d, "d_holders": h}
            for day, d, h in sorted(picked, key=lambda r: -abs(r[1]))[:5]
        ],
    }


def split_flags(shares: dict[dt.date, float], series: CreationSeries,
                lo: dt.date, hi: dt.date) -> dict[str, object]:
    """Steps whose share count moved by more than `SPLIT_FLAG` of its own level, FLAGGED not
    dropped, **inside the overlap window and over the whole in-sample series separately.**

    The ProShares series is fully back-adjusted for reverse splits (D619), so a split should
    leave no discontinuity at all and anything here is either a genuinely enormous creation or an
    adjustment that did not take. The whole-series count is reported beside the in-window list
    because the two answer different questions: the window's flags could corrupt this
    measurement, the older ones cannot and are a fact about the panel.
    """
    inside: list[dict[str, object]] = []
    whole = 0
    for day, delta in series.deltas:
        prev = series.prev_day(day)
        base = shares[prev]
        if base <= 0 or abs(delta) / base <= SPLIT_FLAG:
            continue
        whole += 1
        if lo <= day <= hi:
            inside.append({
                "day": day.isoformat(),
                "prev_day": prev.isoformat(),
                "shares_prev": base,
                "d_shares": delta,
                "relative": delta / base,
            })
    return {
        "rule": f"|d_shares| / shares_out[prev] > {SPLIT_FLAG}",
        "in_overlap": inside,
        "n_in_overlap": len(inside),
        "n_whole_series": whole,
        "note": (
            "The series is back-adjusted for reverse splits, so a split leaves no discontinuity "
            "here. Most whole-series flags sit in each fund's earliest, smallest-share era, "
            "where the back-adjusted count is a handful of shares and a single creation doubles "
            "it. They are reported, not dropped."
        ),
    }


# ------------------------------------------------------------------------------------ compute
def compute() -> dict[str, object]:
    """The whole measurement, as a plain dict. A pure function of the three committed files."""
    shares_by_fund, window = load_shares()
    holders = read_holder_fixture(RT_PATH)
    index = holder_index(holders)
    proved = _prove_index(holders, index)

    lo, hi = ROBINTRACK_SPAN
    per_fund: dict[str, object] = {}
    for fund in WITH_TRUTH:
        shares = shares_by_fund.get(fund)
        if not shares:
            raise RetailAttentionError(f"{NAV_PANEL} holds no rows for {fund}")
        series = creations(shares, fund=fund)
        rows = pair(series, index, fund, lo, hi)
        in_window = [(d, v) for d, v in series.deltas if lo <= d <= hi]
        holder_days = [
            day for day in (d for d, _v in in_window)
            if (fund, day) in index and (fund, series.prev_day(day)) in index
        ]
        per_fund[fund] = {
            "n_share_days_in_overlap": sum(1 for d in shares if lo <= d <= hi),
            "n_creation_steps_in_overlap": len(in_window),
            "n_paired": len(rows),
            "n_dropped_for_missing_holder_poll": len(in_window) - len(holder_days),
            "n_steps_skipped_long_gap": len(
                [d for d, _g in series.skipped if lo <= d <= hi]
            ),
            "holder_span_utc": _ticker_span(holders, fund),
            "d_shares": describe([d for _day, d, _h in rows]),
            "d_holders": describe([h for _day, _d, h in rows]),
            "correlations": correlations(rows),
            "correlations_nonzero_creation": {
                "why": (
                    "A share count that did not move is not a creation, and on these funds most "
                    "days it did not: the zero mass runs from 36% of steps (UCO) to 77% (BOIL). "
                    "A rank correlation over that mass is mostly a correlation between one tied "
                    "block and the holder series. This cell keeps only the steps where a "
                    "creation actually happened, and its n is the honest sample size."
                ),
                **correlations([r for r in rows if r[1] != 0.0]),
            },
            "creation_days": creation_day_cell(rows),
            "split_like_steps": split_flags(shares, series, lo, hi),
        }

    # THE TRADING-DAY CALENDAR FOR THE TWO FUNDS WITH NO SHARE COUNT. UNG and USO are NYSE Arca
    # listings, the same venue as the four ProShares funds, so the days the ProShares panel holds
    # ARE their trading days. Taken as the intersection of the four (a day all four price is a
    # day the venue was open) rather than the union, so a single fund's missing row cannot invent
    # a session. Without this the holder series is differenced over CALENDAR days and every
    # weekend contributes an exact zero -- 257 of UNG's 815 steps on the first build, which is a
    # third of the sample saying nothing.
    calendars = [set(shares_by_fund[f]) for f in WITH_TRUTH if f in shares_by_fund]
    trading_days = sorted(d for d in set.intersection(*calendars) if lo <= d <= hi)

    holders_only: dict[str, object] = {}
    for ticker in HOLDERS_ONLY:
        days = [d for d in trading_days if (ticker, d) in index]
        deltas: list[float] = []
        dropped = 0
        for i in range(1, len(days)):
            gap = (days[i] - days[i - 1]).days
            if gap > MAX_GAP_DAYS:
                dropped += 1
                continue
            deltas.append(float(index[(ticker, days[i])] - index[(ticker, days[i - 1])]))
        magnitudes = [abs(v) for v in deltas]
        threshold = quantile_linear(magnitudes, CREATION_DAY_P) if len(deltas) >= 3 else None
        holders_only[ticker] = {
            "why_no_truth": (
                "USCF publishes no free NAV or share-count history (D619: the fund's page is "
                "JS-gated and no free holdings history exists), so there is no creation series "
                "to correlate against. The holder series alone is reported."
            ),
            "calendar": (
                "the intersection of the four ProShares funds' trading days inside the overlap "
                "window -- UNG and USO are NYSE Arca listings like the other four, and "
                "differencing over calendar days would make every weekend an exact zero"
            ),
            "n_trading_days_in_calendar": len(trading_days),
            "n_days": len(days),
            "n_steps": len(deltas),
            "n_steps_dropped_long_gap": dropped,
            "holder_span_utc": _ticker_span(holders, ticker),
            "d_holders": describe(deltas),
            "p90_abs_d_holders": threshold,
            "n_top_decile_days": (
                sum(1 for v in deltas if abs(v) > threshold) if threshold is not None else 0
            ),
            "n_top_decile_positive": (
                sum(1 for v in deltas if abs(v) > threshold and v > 0)
                if threshold is not None else 0
            ),
        }

    return {
        "spec": "D621; SETTLEMENT_FLOW_LEDGER_PREREG.md section 3.3c line 112 and P3.7, as amended",
        "record": "D621",
        "builder": "scripts/retail_attention_report.py --run",
        "what_this_is": (
            "A DATA-QUALITY MEASUREMENT AND NOT A SIGNAL TEST. No return is computed, no price "
            "bar is read, no null is run, nothing is scored, and no verdict about tradeability "
            "follows from anything here. The question is whether the daily change in Robinhood "
            "holders moves with the daily change in shares outstanding."
        ),
        "inputs": {
            "fund_nav_daily": {
                "path": "data/fixtures/fund_nav_daily.csv.gz",
                "sha256": sha256_file(NAV_PATH, text_normalise=False),
                "read_through": "backtest_framework.data.panels.load_panel (D609)",
                "reserved_from": RESERVED_FROM,
                "window_record": window,
            },
            "robintrack_energy_funds": {
                "path": "data/fixtures/robintrack_energy_funds.csv.gz",
                "sha256": sha256_file(RT_PATH, text_normalise=False),
                "rows": len(holders),
            },
        },
        "conventions": {
            "interval": (
                "A creation is shares_out[d] - shares_out[prev(d)] where prev(d) is the previous "
                "day PRESENT IN THE SOURCE, and the holder change is differenced over the SAME "
                f"interval. A step longer than {MAX_GAP_DAYS} calendar days is skipped and named."
            ),
            "daily_holder_cut": (
                "the LAST Robintrack poll of the UTC day. The archive polls around the clock at "
                "a ~1 h cadence (the hour-of-day histogram is flat on all six funds), so the "
                "last poll of a UTC day is three to four hours after the US close."
            ),
            "lag": (
                "lag = +k pairs the creation at index i with the holder change at index i+k, in "
                "SERIES STEPS (trading days), so a positive lag asks whether holders move AFTER "
                "creations."
            ),
            "creation_day": (
                f"|creation| strictly above the {CREATION_DAY_P:.0%} quantile of |creation| over "
                "the fund's own overlap rows, by linear interpolation between order statistics."
            ),
            "missing_holder_poll": (
                "DROPPED AND COUNTED, never zero-filled. The two site outages are 152.5 h ending "
                "2019-01-30 and 238.0 h ending 2020-01-16."
            ),
            "independence": (
                "FOUR FUNDS ARE NOT FOUR EXPERIMENTS. BOIL and KOLD are the long and short "
                "leveraged natural-gas funds of one issuer on one underlying; UCO and SCO are "
                "the same pair on crude. There are TWO underlyings and one issuer, so the "
                "effective number of independent cells here is about two, and the per-fund rows "
                "below must not be read as four confirmations."
            ),
            "both_statistics": (
                "Spearman AND Pearson at every lag, always together and never one alone. The "
                "holder series has a meme-era right tail and a Pearson over a spike is a "
                "statistic about the spike."
            ),
        },
        "overlap_window": [lo.isoformat(), hi.isoformat()],
        "index_proved_against_daily_holders": proved,
        "per_fund": per_fund,
        "holders_only": holders_only,
        "gdelt_hourly": _gdelt_cell(),
        "holdout": (
            "No return, no signal, no trade. fund_nav_daily is read through load_panel with "
            f"reserved_from={RESERVED_FROM!r}; the Robintrack archive ends 2020-08-13 and cannot "
            "reach the cut. Every measurement above is on rows dated 2020-08-13 or earlier."
        ),
    }


def _ticker_span(holders: list[HolderObs], ticker: str) -> list[str]:
    rows = [o for o in holders if o.ticker == ticker]
    if not rows:
        raise RetailAttentionError(f"the Robintrack fixture holds no rows for {ticker}")
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return [rows[0].ts_utc.strftime(fmt), rows[-1].ts_utc.strftime(fmt)]


def _gdelt_cell() -> dict[str, object]:
    """The news side: what the file-derived hourly series holds, and what is DEFERRED."""
    meta = json.loads(GDELT_META.read_text(encoding="utf-8"))
    import gzip

    counts: dict[str, list[float]] = {}
    with gzip.open(GDELT_PATH, "rt", encoding="utf-8", newline="") as fh:
        fh.readline()
        for line in fh:
            source, qid, _hour, _avail, n, _tone = line.rstrip("\n").split(",")
            counts.setdefault(f"{source}:{qid}", []).append(float(n))
    return {
        "fixture": {
            "path": "data/fixtures/gdelt_hourly_sample.csv.gz",
            "sha256": sha256_file(GDELT_PATH, text_normalise=False),
            "rows": meta["rows"],
            "rows_by_source": meta["rows_by_source"],
        },
        "hourly_counts_by_key": {
            key: {"n_hours": len(v), "total": sum(v), "max": max(v), "n_zero_hours":
                  sum(1 for x in v if x == 0.0)}
            for key, v in sorted(counts.items())
        },
        "api_state": meta["api_state"],
        "comparison_deferred": (
            "The pre-registered comparison -- the DOC API's hourly count against D612's "
            "file-derived 15-minute counts summed to the hour -- is NOT RUN, because the API "
            "answered HTTP 429 and then dropped the connection on 2026-09-22 (see api_state). "
            "When it answers, the comparison is between two DIFFERENT CORPORA: timelinevolraw "
            "counts documents in GDELT's DOC index matching a DOC-query grammar, while the "
            "15-minute route counts GKG rows matching QUERIES.md section 2b's title/url/theme "
            "rules. THEY ARE NOT EXPECTED TO BE EQUAL. What is worth measuring is the rank "
            "correlation of the two hourly series and the ratio of their totals, and this "
            "sentence is written BEFORE either is seen so that whatever comes back cannot be "
            "read as confirming a prediction nobody made."
        ),
    }


def render(payload: dict[str, object]) -> str:
    """The committed bytes: sorted keys, two-space indent, one trailing newline, ASCII."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def run() -> int:
    for parent in {p.parent for p in REQUIRED_OUTPUTS}:
        if not parent.is_dir():
            raise AssertionError(f"declared outputs cannot be written: {parent} does not exist")
    payload = compute()
    text = render(payload)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    for p in REQUIRED_OUTPUTS:
        if not p.is_file():
            raise AssertionError(f"declared output {p} was not written")

    P(f"[out] {OUT}  {len(text):,} bytes")
    per_fund = payload["per_fund"]
    assert isinstance(per_fund, dict)
    for fund, cell in per_fund.items():
        corr = cell["correlations"]["lag_0"]
        days = cell["creation_days"]
        P(f"  {fund:4s} n={cell['n_paired']:>4}  lag 0: spearman "
          f"{_fmt(corr['spearman'])} pearson {_fmt(corr['pearson'])}  |  "
          f"top-decile creation days {days['n_creation_days']}, "
          f"holders up on {_fmt(days['share_dholders_positive'])}")
    ho = payload["holders_only"]
    assert isinstance(ho, dict)
    for ticker, cell in ho.items():
        d = cell["d_holders"]
        P(f"  {ticker:4s} holders only: n={d['n']}, mean {_fmt(d['mean'])}, median "
          f"{_fmt(d['median'])}, share positive {_fmt(d['share_positive'])}")
    return 0


def _fmt(value: object) -> str:
    return "n/a" if value is None else f"{float(value):+.4f}"


def check() -> int:
    """Recompute and compare BYTE FOR BYTE against the committed file."""
    if not OUT.is_file():
        raise AssertionError(f"{OUT} has not been built; run --run")
    want = OUT.read_text(encoding="utf-8")
    got = render(compute())
    if got != want:
        for i, (a, b) in enumerate(zip(want.split("\n"), got.split("\n"), strict=False)):
            if a != b:
                raise AssertionError(
                    f"{OUT.name} line {i + 1} differs.\n  committed: {a[:160]}\n  recomputed: "
                    f"{b[:160]}"
                )
        raise AssertionError(f"{OUT.name} differs in length: {len(want)} against {len(got)}")
    P(f"[check] {OUT.name} reproduces byte for byte from the committed fixtures "
      f"({len(want):,} bytes)")
    return 0


# ------------------------------------------------------------------------------------ selftest
def selftest() -> int:
    """The GOOD case first -- a known-answer pairing worked by hand -- then every guard proved to
    fire. No fixture and no panel is read."""
    P("[selftest] 1. the GOOD case: three steps, paired over the SAME interval")
    shares = {
        dt.date(2019, 11, 1): 100.0,
        dt.date(2019, 11, 4): 110.0,   # Friday -> Monday, a 3-day step and ONE creation
        dt.date(2019, 11, 5): 105.0,
        dt.date(2019, 11, 6): 105.0,
    }
    series = creations(shares, fund="TEST")
    assert series.deltas == (
        (dt.date(2019, 11, 4), 10.0), (dt.date(2019, 11, 5), -5.0), (dt.date(2019, 11, 6), 0.0)
    ), series.deltas
    assert series.prev_day(dt.date(2019, 11, 4)) == dt.date(2019, 11, 1)
    index = {
        ("TEST", dt.date(2019, 11, 1)): 50,
        ("TEST", dt.date(2019, 11, 4)): 60,
        ("TEST", dt.date(2019, 11, 5)): 58,
        ("TEST", dt.date(2019, 11, 6)): 58,
    }
    rows = pair(series, index, "TEST", dt.date(2019, 1, 1), dt.date(2020, 12, 31))
    assert rows == [
        (dt.date(2019, 11, 4), 10.0, 10.0),
        (dt.date(2019, 11, 5), -5.0, -2.0),
        (dt.date(2019, 11, 6), 0.0, 0.0),
    ], rows
    P(f"    3 steps: {[(d.isoformat(), a, b) for d, a, b in rows]}")
    P("    the Friday->Monday step is ONE creation differenced over ITS OWN 3-day interval, "
      "and the holder change uses the same two dates")

    P("[selftest] 2. a missing holder poll DROPS the step; it is never zero-filled")
    holed = {k: v for k, v in index.items() if k[1] != dt.date(2019, 11, 5)}
    dropped = pair(series, holed, "TEST", dt.date(2019, 1, 1), dt.date(2020, 12, 31))
    assert [d for d, _a, _b in dropped] == [dt.date(2019, 11, 4)], dropped
    P(f"    removing one poll removes TWO steps (the one ending on it and the one starting "
      f"from it): {len(rows)} -> {len(dropped)}")

    P("[selftest] 3. a long gap is SKIPPED and NAMED, not differenced")
    gapped = creations({dt.date(2019, 11, 1): 100.0, dt.date(2019, 12, 1): 900.0}, fund="TEST")
    assert gapped.deltas == () and gapped.skipped == ((dt.date(2019, 12, 1), 30),), gapped
    P(f"    a 30-day gap: {gapped.skipped}")

    P("[selftest] 4. the hand ledger's correlation case (golden Case 1)")
    x = [float(v) for v in range(1, 11)]
    y = [2.0, 1, 4, 3, 6, 5, 8, 7, 100, 9]
    sp, pe = spearman(x, y), pearson(x, y)
    assert sp == 0.93939393939393945, repr(sp)
    assert pe == 0.47771588185465091, repr(pe)
    assert quantile_linear([abs(v) for v in x], CREATION_DAY_P) == 9.1
    P(f"    spearman {sp!r}, pearson {pe!r}, p90 9.1 -- Spearman reads 0.94 where Pearson "
      f"reads 0.48 on the SAME ten rows, because one value is an outlier")

    P("[selftest] 5. the lag convention: +1 pairs a creation with the NEXT step's holders")
    toy = [
        (dt.date(2019, 11, 1), 1.0, 10.0),
        (dt.date(2019, 11, 4), 2.0, 20.0),
        (dt.date(2019, 11, 5), 3.0, 30.0),
        (dt.date(2019, 11, 6), 4.0, 40.0),
    ]
    cells = correlations(toy)
    assert cells["lag_0"]["n"] == 4 and cells["lag_+1"]["n"] == 3 and cells["lag_-1"]["n"] == 3
    assert cells["lag_0"]["spearman"] == 1.0, cells["lag_0"]
    P(f"    n by lag: {{-1: {cells['lag_-1']['n']}, 0: {cells['lag_0']['n']}, "
      f"+1: {cells['lag_+1']['n']}}}; a perfectly monotone pair reads 1.0 at lag 0")

    P("[selftest] 6. a constant side is reported as None, never as 0.0")
    flat = [(dt.date(2019, 11, 1) + dt.timedelta(days=k), 1.0, float(k)) for k in range(5)]
    cell = correlations(flat)["lag_0"]
    assert cell["spearman"] is None and "why_none" in cell, cell
    P(f"    {cell['why_none']}")

    P("[selftest] 7. a non-positive share count RAISES rather than being differenced")
    expect_raise(lambda: creations({dt.date(2019, 11, 1): 1.0}, fund="T").value(dt.date(2019, 11, 1)),
                 RetailAttentionError, "asking for a creation on a series' first day")
    expect_raise(lambda: quantile_linear([], 0.9), Exception, "a quantile of nothing")
    expect_raise(lambda: pearson([1.0, 2.0], [1.0, 2.0]), Exception, "a correlation of two points")

    P("[selftest] 8. describe() prints the MEDIAN beside the mean")
    d = describe([1.0, 1.0, 1.0, 1.0, 100.0])
    assert d["median"] == 1.0 and d["mean"] == 20.8, d
    P(f"    mean {d['mean']}, median {d['median']} -- the tell that a tail is doing the work")

    P("[selftest] PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--run", action="store_true", help="compute and write the validation JSON")
    ap.add_argument("--check", action="store_true", help="recompute and compare byte for byte")
    ap.add_argument("--selftest", action="store_true", help="prove every guard fires; reads nothing")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.run:
        return run()
    if args.check:
        return check()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
