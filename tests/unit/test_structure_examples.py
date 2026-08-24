"""The trade-example report's numbers, pinned against the artifact they came from.

`docs/results/structure_trade_examples.html` is hand-written prose around machine-extracted
numbers. That is the same arrangement `final_report.html` has, and it carries the same risk:
prose and artifact drift apart, which this project has recorded three times (D176, D183,
D186) as its most repeated defect.

So every figure the report quotes is regenerated here from
`data/structure_examples_summary.json` and asserted to appear in the page, in the exact
format the page uses. Re-running the extraction with different data fails this file rather
than silently publishing stale numbers.

The cross-study figures — hit rates, required hit rates, final equity — are pinned against
their own summaries for the same reason.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "docs" / "results" / "structure_trade_examples.html"
EXAMPLES = REPO / "data" / "structure_examples_summary.json"
MARGINAL = REPO / "data" / "structure_marginal_summary.json"
CENSUS = REPO / "data" / "structure_census_summary.json"
PNL = REPO / "data" / "structure_pnl_summary.json"

GOLDEN_RATIO = 0.618
STACKED = "C1+C2+C3+C4"
PRIMARY_CELL = "k2|touch0.5"
NBSP = "\u00a0"
"""Written as an escape rather than the character: an invisible byte in source is a
readability hazard, and this file exists to be read."""


@pytest.fixture(scope="module")
def page() -> str:
    """The report with HTML entities resolved.

    The page writes `&percnt;` and `&nbsp;` for typographic reasons, so a naive substring
    search for "67%" would fail on a page that says exactly that. Unescaping here keeps the
    assertions written in the units a reader sees rather than in markup."""
    raw = REPORT.read_text(encoding="utf-8")
    return html.unescape(raw).replace(NBSP, " ")


@pytest.fixture(scope="module")
def examples() -> dict:
    return json.loads(EXAMPLES.read_text(encoding="utf-8"))


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the page"


# ------------------------------------------------------------------ the seven trades

def test_every_trade_row_matches_the_artifact(page, examples):
    """The summary table, cell by cell."""
    trades = [
        examples["per_symbol"]["BTCUSDT"][k] for k in ("best", "median", "worst")
    ] + [
        examples["per_symbol"]["ETHUSDT"][k] for k in ("best", "median", "worst")
    ] + [examples["lowest_cost"]]

    for trade in trades:
        o, r, en = trade["outcome"], trade["risk"], trade["entry"]
        label = f"{trade['symbol']} {en['timestamp'][:10]}"
        present(page, f"{en['retracement']:.3f}", f"{label} retracement")
        present(page, f"{r['distance_atr']:.2f}", f"{label} stop in ATR")
        present(page, f"{r['distance_pct']:.3%}", f"{label} stop as % of price")
        present(page, f"{o['gross_r']:+.2f}", f"{label} gross R")
        present(page, f"{o['cost_r']:.2f}", f"{label} cost R")
        present(page, f"{o['net_r']:+.2f}", f"{label} net R")
        present(page, en["timestamp"][:10], f"{label} date")


def test_the_two_untradeable_stops_are_quoted_exactly(page, examples):
    """The report's central claim, and the one a reader will check first."""
    for symbol in ("BTCUSDT", "ETHUSDT"):
        worst = examples["per_symbol"][symbol]["worst"]
        present(page, f"{worst['outcome']['cost_r']:.3f}R", f"{symbol} worst cost in R")
        present(page, f"{worst['risk']['distance_pct']:.3%}", f"{symbol} worst stop pct")
    btc = examples["per_symbol"]["BTCUSDT"]["worst"]
    present(page, f"{btc['risk']['distance']:,.2f}", "BTC worst stop distance in dollars")
    present(page, f"{btc['risk']['distance_pct'] * 10000:.1f}", "BTC worst stop in bp")


def test_the_golden_ratio_band_arithmetic_is_the_artifacts(page, examples):
    """The report claims the 0.618 touch band spans a large fraction of the leg. That is
    computed from `entry.atr` and `leg.span`, both in the artifact, and is the load-bearing
    claim of finding 2 — so it is regenerated rather than trusted."""
    best = examples["per_symbol"]["BTCUSDT"]["best"]
    frac = 0.5 * best["entry"]["atr"] / abs(best["leg"]["span"])
    present(page, f"{frac:.1%} of the entire move", "BTC best band as fraction of leg")
    present(page, f"{GOLDEN_RATIO - frac:.0%}", "BTC best band lower bound")
    present(page, f"{GOLDEN_RATIO + frac:.0%}", "BTC best band upper bound")
    present(page, f"{best['levels']['fib_618']:,.2f}", "BTC best 0.618 price")
    gap = abs(best["entry"]["price"] - best["levels"]["fib_618"])
    present(page, f"{gap:,.2f}", "distance from the entry to the 0.618 level")


def test_the_best_trades_are_shown_as_full_five_r_winners(page, examples):
    """The report says both best trades reached a clean 5R. If that ever stops being true
    the sentence has to change, so it is asserted rather than described."""
    for symbol in ("BTCUSDT", "ETHUSDT"):
        best = examples["per_symbol"][symbol]["best"]
        assert best["outcome"]["gross_r"] == pytest.approx(5.0, abs=1e-9)
        assert best["exit"]["reason"] == "target"
        present(page, f"{best['outcome']['net_r']:+.3f}R", f"{symbol} best net R")


def test_the_highest_cost_trade_is_btcs_worst(page, examples):
    """The report builds a paragraph on these being the same event. If the extraction ever
    separates them, that paragraph is wrong."""
    assert (
        examples["highest_cost"]["entry"]["timestamp"]
        == examples["per_symbol"]["BTCUSDT"]["worst"]["entry"]["timestamp"]
    )
    present(page, "yields seven trades", "the seven-not-eight explanation")


def test_the_cheapest_trade_is_quoted_with_its_pool(page, examples):
    low = examples["lowest_cost"]
    present(page, f"{low['outcome']['cost_r']:.3f}R", "cheapest trade cost in R")
    present(page, f"{low['outcome']['net_r']:+.3f}R", "cheapest trade net R")
    present(page, f"{examples['pooled_n']} stacked trades", "the pooled trade count")
    target_pct = low["risk"]["target_price"] / low["entry"]["price"] - 1.0
    present(page, f"{target_pct:.1%}", "how far away the 5R target was")


# ------------------------------------------------- figures borrowed from other studies

def test_the_hit_rates_come_from_the_marginal_study(page):
    marginal = json.loads(MARGINAL.read_text(encoding="utf-8"))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    for symbol in ("BTCUSDT", "ETHUSDT"):
        achieved = marginal["runs"][symbol]["lattice"][STACKED]["costed"]["hit_rate"]
        needed = census["runs"][symbol]["cells"][PRIMARY_CELL]["entries_stacked"][
            "required_hit_rate_at_5r"
        ]
        present(page, f"{achieved:.1%}", f"{symbol} achieved hit rate")
        present(page, f"{needed:.1%}", f"{symbol} required hit rate at 5R")


def test_the_untradeable_shares_come_from_the_marginal_study(page):
    marginal = json.loads(MARGINAL.read_text(encoding="utf-8"))
    for symbol in ("BTCUSDT", "ETHUSDT"):
        share = marginal["runs"][symbol]["lattice"][STACKED]["costed"]["share_untradeable"]
        present(page, f"{share:.0%}", f"{symbol} untradeable share")


def test_the_final_equity_figures_come_from_the_pnl_study(page):
    pnl = json.loads(PNL.read_text(encoding="utf-8"))
    capital = pnl["start_capital"]
    for symbol in ("BTCUSDT", "ETHUSDT"):
        arm = pnl["runs"][symbol]["arms"][STACKED]["tiers"]["40 bps/side"]
        hold = pnl["runs"][symbol]["buy_and_hold"]
        present(page, f"{capital * (1 + arm['total_return']):,.0f}", f"{symbol} arm equity")
        present(page, f"{capital * (1 + hold['total_return']):,.0f}", f"{symbol} b&h equity")


def test_the_trade_counts_match_the_arm(page, examples):
    for symbol, expected in (("BTCUSDT", 118), ("ETHUSDT", 104)):
        assert examples["per_symbol"][symbol]["n_trades"] == expected
        present(page, str(expected), f"{symbol} stacked trade count")


# ------------------------------------------------------------------ report integrity

def test_the_report_reuses_the_final_reports_stylesheet(page):
    """The user asked for the terrain report's treatment, so the stylesheet is lifted from
    it verbatim rather than reimplemented. If the two ever diverge this fails and the
    builder has to be re-run."""
    original = (REPO / "docs" / "results" / "final_report.html").read_text(encoding="utf-8")
    inherited = original[original.index("<style>") : original.index("</style>")]
    assert inherited in page, "the inherited stylesheet is no longer byte-identical"

    # The chart rules are the only addition, and they come after everything inherited.
    raw = REPORT.read_text(encoding="utf-8")
    assert raw.index("/* ------") < raw.index(".chart {"), "chart rules must be appended"
    assert raw.count("<style>") == 1 and raw.count("</style>") == 1


def test_the_report_states_its_own_selection_rule(page):
    """An examples page whose selection rule is not on it is a slideshow."""
    for phrase in ("best", "median", "worst", "before the outcomes were read"):
        assert phrase in page


def test_the_report_states_what_it_does_not_show(page):
    for phrase in (
        "cannot carry a verdict",
        "flatter the strategy on purpose",
        "not the thing being taught",
    ):
        assert phrase in page


# ---------------------------------------------------------------------- the charts

@pytest.fixture(scope="module")
def raw() -> str:
    """The page as written, entities intact — the SVG assertions need exact markup."""
    return REPORT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def charts(raw: str) -> list[tuple[float, float, str]]:
    return [
        (float(m.group(1)), float(m.group(2)), m.group(3))
        for m in re.finditer(r'<svg viewBox="0 0 ([\d.]+) ([\d.]+)"(.*?)</svg>', raw, re.S)
    ]


def test_there_is_one_chart_per_trade(charts):
    assert len(charts) == 7


def test_every_chart_draws_one_candle_per_bar_in_its_window(charts, examples):
    """The chart window is stored in the artifact, so the candle count is checkable rather
    than eyeballed. A truncated window would otherwise look like a perfectly good chart."""
    order = [
        examples["per_symbol"]["BTCUSDT"][k] for k in ("best", "median", "worst")
    ] + [
        examples["per_symbol"]["ETHUSDT"][k] for k in ("best", "median", "worst")
    ] + [examples["lowest_cost"]]

    for (_, _, inner), trade in zip(charts, order):
        expected = len(trade["chart"]["bars"])
        wicks = len(re.findall(r'stroke="var\(--muted\)"', inner))
        assert wicks == expected, "one wick per bar"
        bodies = len(re.findall(r'stroke="var\(--ink\)" stroke-width="1"/>', inner))
        assert bodies == expected, "one body per bar"


def test_nothing_is_drawn_outside_its_own_frame(charts):
    """A stop or a gap band can fall off the bottom if the price scale is built from the
    candles alone. The generator widens the scale to include every overlay; this is what
    says it actually did."""
    for width, height, inner in charts:
        for x, y, w, h in re.findall(
            r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"', inner
        ):
            assert -1 <= float(x) and float(x) + float(w) <= width + 1
            assert -1 <= float(y) and float(y) + float(h) <= height + 1
        for cx, cy in re.findall(r'<circle cx="([\d.-]+)" cy="([\d.-]+)"', inner):
            assert 0 <= float(cx) <= width and 0 <= float(cy) <= height


def test_every_chart_marks_the_structure_it_is_illustrating(charts):
    """A chart missing its overlays is still a chart, and would pass every other check."""
    for _, _, inner in charts:
        assert "CHoCH" in inner
        assert ">entry<" in inner
        assert ">exit<" in inner
        assert "61.8%" in inner or "61.8" in inner
        assert 'stroke-dasharray="4 3"' in inner, "the stop line"


def test_the_charts_theme_with_the_page(charts):
    """Every colour is a custom property from the inherited palette, so the charts follow
    the viewer's theme. A literal hex here would render one theme's ink on the other
    theme's ground."""
    for _, _, inner in charts:
        for literal in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,8})"', inner):
            raise AssertionError(f"hard-coded colour {literal} in a chart")
        assert 'fill="var(--brass)"' in inner


def test_the_charts_are_horizontally_scrollable(raw):
    """The widest chart is 772px and the measure is 34rem. Without its own scroll container
    the page body would scroll sideways on a phone."""
    assert raw.count('<div class="scroll">') >= 7


def test_the_legend_names_every_mark_the_charts_use(raw):
    page = html.unescape(raw)
    for phrase in ("closed up", "closed down", "impulse leg", "fair value gap"):
        assert phrase in page
