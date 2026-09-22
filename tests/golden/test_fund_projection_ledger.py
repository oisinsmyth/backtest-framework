"""Golden master for D620: the filings parse and the projected panel, against hand-read numbers.

**The hand file is `test_fund_projection_ledger.hand.txt`, and it was written BEFORE the parser.**
One quarter-end per fund, typed by eye out of three recorded documents — every contract month,
every signed contract count, every notional, every swap counterparty, the share count, the net
assets and the NAV per share, with the accession on each block. This file reads that file and
requires the built fixture to reproduce it.

WHY A GOLDEN, WHEN `tests/unit/test_fund_holdings_quarterly.py` ALREADY EXERCISES EVERY GATE
----------------------------------------------------------------------------------------------
The unit tests run on hand-typed FRAGMENTS and synthetic frames. They prove the guards fire; they
cannot prove the builder read 231 real documents correctly, because they never open one. Two
defects found while building this record were invisible to every gate and visible only against
hand-read numbers:

  * `\\s*#?` in the USCF share-count pattern ate the separator before the comparative column, so
    every USCF filing returned the current period's share count and a NULL for the prior year.
    The frame was well formed, every gate passed, and half the anchors were missing.
  * The ProShares dash is an EN DASH in the 2009-2010 filings and a hyphen elsewhere.

**Both inputs are gitignored cache**, so these tests SKIP rather than fail on a fresh clone:
`data/fixtures/*.csv.gz` is excluded by suffix and `data/raw/` is the raw cache. A skip is not a
pass — the fixture metas carry their own sha256 and the builders rebuild them in one command
each. Neither fixture is in `data/data_manifest.json` yet (the D620 record drafts the catalogue
rows for the integrator), which is why the skip is written here rather than taken from
`requires_panel`.

No return is computed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
HOLDINGS = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
HOLDINGS_META = REPO / "data" / "fixtures" / "fund_holdings_quarterly.meta.json"
PROJECTED = REPO / "data" / "fixtures" / "fund_panel_projected.csv.gz"
PROJECTED_META = REPO / "data" / "fixtures" / "fund_panel_projected.meta.json"
HAND = Path(__file__).with_suffix("").with_name("test_fund_projection_ledger.hand.txt")

_SKIP = (
    "{0} is gitignored cache and is not on this checkout. Rebuild it: "
    "`uv run python scripts/fetch_fund_filings.py --documents` then "
    "`uv run python scripts/build_fund_holdings_quarterly.py --build` then "
    "`uv run python scripts/project_fund_panel.py --build --method step`."
)


def _need(path: Path) -> None:
    if not path.exists():
        pytest.skip(_SKIP.format(path.relative_to(REPO)))


# ------------------------------------------------------------------------- the hand file parse
def parse_hand(text: str) -> dict[str, dict[str, object]]:
    """The hand file -> {fund: block}. Deliberately dumb: whitespace-split lines, no schema.

    A clever reader would be a second implementation of the thing under test. This one only
    knows that a `## TICKER` line opens a block, a bare `key value` line is a scalar, and
    `futures`/`swap` lines are lists."""
    blocks: dict[str, dict[str, object]] = {}
    fund: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip() if not raw.startswith("##") else raw.strip()
        if raw.startswith("##"):
            fund = raw[2:].strip().split()[0]
            blocks[fund] = {"futures": [], "swap": []}
            continue
        if fund is None or not line:
            continue
        parts = line.split()
        if parts[0] == "futures":
            blocks[fund]["futures"].append(  # type: ignore[union-attr]
                {"contract_month": parts[1], "contracts": float(parts[3]), "notional_usd": float(parts[5])}
            )
        elif parts[0] == "swap":
            m = re.match(r"^swap\s+(?P<cp>.+?)\s+notional_usd\s+(?P<n>[-\d\.]+)$", line)
            assert m is not None, line
            blocks[fund]["swap"].append(  # type: ignore[union-attr]
                {"counterparty": m.group("cp").strip(), "notional_usd": float(m.group("n"))}
            )
        elif len(parts) == 2:
            key, value = parts
            blocks[fund][key] = float(value) if re.fullmatch(r"-?\d+(\.\d+)?", value) else value
    return blocks


@pytest.fixture(scope="module")
def hand() -> dict[str, dict[str, object]]:
    return parse_hand(HAND.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def holdings() -> pd.DataFrame:
    _need(HOLDINGS)
    frame = pd.read_csv(
        HOLDINGS, encoding="utf-8",
        dtype={"period_end": str, "fund": str, "filed_date": str, "kind": str,
               "contract_month": str, "source_accession": str},
    )
    return frame.fillna({"contract_month": "", "counterparty": "", "description": "", "reason": ""})


def _block(holdings: pd.DataFrame, fund: str, hand_block: dict[str, object]) -> pd.DataFrame:
    got = holdings[
        (holdings["fund"] == fund)
        & (holdings["period_end"] == hand_block["period_end"])
        & (holdings["source_accession"] == hand_block["accession"])
    ]
    assert len(got), f"{fund}: no rows for {hand_block['period_end']} from {hand_block['accession']}"
    return got


def test_the_hand_file_covers_all_six_funds(hand: dict[str, dict[str, object]]) -> None:
    assert sorted(hand) == ["BOIL", "KOLD", "SCO", "UCO", "UNG", "USO"]


@pytest.mark.parametrize("fund", ["BOIL", "KOLD", "SCO", "UCO", "UNG", "USO"])
def test_the_parser_reproduces_every_hand_read_futures_line(
    holdings: pd.DataFrame, hand: dict[str, dict[str, object]], fund: str
) -> None:
    block = hand[fund]
    got = _block(holdings, fund, block)
    fut = got[got["kind"] == "futures"].sort_values("contract_month")
    want = sorted(block["futures"], key=lambda r: r["contract_month"])  # type: ignore[union-attr,index]
    assert list(fut["contract_month"]) == [r["contract_month"] for r in want]
    assert list(fut["contracts"].astype(float)) == [r["contracts"] for r in want]
    # MAGNITUDE against the hand file, which types the notional as the document prints it —
    # unsigned, even in a "Futures Contracts Sold" block — and SIGN against the contract count,
    # which is the fixture's own stated convention. See the hand file's addendum.
    got_notional = fut["notional_usd"].astype(float).to_numpy()
    assert list(np.abs(got_notional)) == [abs(r["notional_usd"]) for r in want]
    assert list(np.sign(got_notional)) == list(np.sign(fut["contracts"].astype(float).to_numpy()))


@pytest.mark.parametrize("fund", ["UCO", "USO", "UNG"])
def test_the_parser_reproduces_every_hand_read_swap_line(
    holdings: pd.DataFrame, hand: dict[str, dict[str, object]], fund: str
) -> None:
    block = hand[fund]
    got = _block(holdings, fund, block)
    swaps = got[got["kind"] == "swap"]
    want = block["swap"]  # type: ignore[index]
    assert sorted(swaps["notional_usd"].astype(float)) == sorted(r["notional_usd"] for r in want)
    # The counterparty is matched by prefix: the hand file types the name as the document prints
    # it and the parser truncates at 80 characters.
    for r in want:
        assert any(str(c).startswith(str(r["counterparty"])[:18]) for c in swaps["counterparty"]), (
            f"{fund}: no swap line whose counterparty starts like {r['counterparty']!r}; "
            f"parsed {list(swaps['counterparty'])}"
        )


@pytest.mark.parametrize("fund", ["BOIL", "KOLD", "SCO", "UCO", "UNG", "USO"])
def test_the_parser_reproduces_the_hand_read_anchors_and_derived_quantities(
    holdings: pd.DataFrame, hand: dict[str, dict[str, object]], fund: str
) -> None:
    block = hand[fund]
    got = _block(holdings, fund, block)
    row = got.iloc[0]
    assert float(row["shares_out"]) == block["shares_out"]
    assert float(row["net_assets"]) == block["net_assets"]
    assert float(row["nav_per_share"]) == block["nav_per_share"]
    assert int(row["n_fut_lines"]) == int(block["n_fut_lines"])  # type: ignore[arg-type]
    assert int(row["n_swap_lines"]) == int(block["n_swap_lines"])  # type: ignore[arg-type]
    assert int(row["n_months_held"]) == int(block["n_months_held"])  # type: ignore[arg-type]
    assert float(row["f_fut"]) == pytest.approx(float(block["f_fut"]), abs=5e-7)  # type: ignore[arg-type]
    assert row["form"] == block["form"]
    assert row["filed_date"] == block["filed"]
    if "futures_notional_total" in block:
        assert float(row["futures_notional_total"]) == block["futures_notional_total"]
    if "swap_notional_total" in block:
        assert float(row["swap_notional_total"]) == block["swap_notional_total"]


def test_the_month_weights_of_a_multi_month_fund_sum_to_one(
    holdings: pd.DataFrame, hand: dict[str, dict[str, object]]
) -> None:
    got = _block(holdings, "USO", hand["USO"])
    fut = got[got["kind"] == "futures"]
    assert len(fut) == 7
    assert float(fut["month_weight"].astype(float).sum()) == pytest.approx(1.0, abs=1e-12)


def test_ung_is_restated_by_exactly_the_split_ratio_and_the_fixture_keeps_both(
    holdings: pd.DataFrame,
) -> None:
    """The hand file's footnote, pinned on the period where both publications exist.

    UNG's 2022-12-31 share count is published FOUR times as 30,184,588 and then a fifth time,
    in the FY2023 10-K filed after the 1-for-4 reverse split of 2024-01-23, as 7,546,147 —
    exactly a quarter. A panel built from the latest filing would carry that factor across the
    whole of 2022 and 2023 with no discontinuity to notice.

    And the discontinuity a POINT-IN-TIME panel correctly shows is pinned beside it: UNG's own
    filings read 169,784,588 shares at 2023-09-30 and 47,821,147 at 2023-12-31, a 3.55x fall in
    one quarter that is the split and not a redemption."""
    g = holdings[holdings["fund"] == "UNG"]
    by_filing = (
        g[g["period_end"] == "2022-12-31"].groupby("source_accession")["shares_out"].first().dropna()
    )
    post = float(by_filing.loc["0001410578-24-000105"])
    pre = by_filing[by_filing.index != "0001410578-24-000105"]
    assert len(pre) >= 3, "the pre-split publications of UNG's 2022-12-31 period are missing"
    assert set(pre.round(6)) == {30184588.0}
    assert post == 7546147.0
    assert float(pre.iloc[0]) / post == pytest.approx(4.0, rel=1e-9)
    q3 = g[g["period_end"] == "2023-09-30"]["shares_out"].dropna()
    q4 = g[g["period_end"] == "2023-12-31"]["shares_out"].dropna()
    assert float(q3.iloc[0]) / float(q4.iloc[0]) == pytest.approx(3.55, abs=0.01)


# ------------------------------------------------------------------------- the built artefacts
def test_the_holdings_meta_pins_the_fixture_it_describes() -> None:
    _need(HOLDINGS)
    _need(HOLDINGS_META)
    import hashlib

    meta = json.loads(HOLDINGS_META.read_text(encoding="utf-8"))
    assert hashlib.sha256(HOLDINGS.read_bytes()).hexdigest() == meta["sha256"]
    assert meta["record"] == "D620"
    # The cut is the AVAILABILITY column, not the as-of column: every 2023-12-31 holdings row in
    # this fixture was published in 2024, so a cut on `period_end` would let post-seal
    # publications through.
    assert meta["date_col"] == "filed_date"
    assert meta["wrong_cuts"] == ["period_end"]
    assert (
        holdings_frame_dates := pd.read_csv(
            HOLDINGS, encoding="utf-8", usecols=["period_end", "filed_date"], dtype=str
        )
    ) is not None
    assert (holdings_frame_dates["period_end"] < holdings_frame_dates["filed_date"]).all()
    # Every unparsed row is counted and every reason is a sentence, not an empty string.
    assert meta["unparsed"]["rows"] == sum(meta["unparsed"]["reasons"].values())
    assert all(str(r).strip() for r in meta["unparsed"]["reasons"])


def test_every_projected_row_is_flagged_as_an_estimate_and_never_a_truth() -> None:
    _need(PROJECTED)
    panel = pd.read_csv(PROJECTED, encoding="utf-8", dtype={"date": str, "fund": str})
    assert set(panel["fund"]) == {"UNG", "USO"}
    assert set(panel["est_flag"]) == {1}
    assert set(panel["clock"]) == {"filed"}
    # The point-in-time rule, on every row: the anchor was PUBLISHED before the date it is used.
    assert (panel["anchor_filed_date"].astype(str) <= panel["date"].astype(str)).all()
    # ...and the period it describes closed before it was published.
    assert (panel["anchor_period_end"].astype(str) < panel["anchor_filed_date"].astype(str)).all()
    assert np.isfinite(panel["shares_out_est"].to_numpy(dtype=float)).all()


def test_the_projected_meta_carries_the_measured_error_as_its_stated_uncertainty() -> None:
    _need(PROJECTED_META)
    meta = json.loads(PROJECTED_META.read_text(encoding="utf-8"))
    assert meta["record"] == "D620"
    assert meta["clock"] == "filed"
    assert meta["method"] not in ("linear",)
    unc = meta["measured_uncertainty"]["per_fund"]
    assert sorted(unc) == ["BOIL", "KOLD", "SCO", "UCO"]
    for fund, cell in unc.items():
        assert cell["shares_out"]["n"] > 1000, fund
        assert 0.0 < cell["shares_out"]["median_rel"] < 2.0, fund
        assert 0.0 < cell["aum"]["median_rel"] < 2.0, fund
        # The answer to the principal's question, pinned as a number rather than as a sentence:
        # the day-to-day creation flow a projection yields is uncorrelated with the truth.
        assert abs(cell["creation_flow_delta_shares"]["corr"]) < 0.20, fund
    assert meta["measured_uncertainty"]["premium_close_vs_nav_bp"]
    assert meta["measured_uncertainty"]["restatements_found"]
