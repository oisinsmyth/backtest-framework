"""Golden master for the D619 fund panel and holdings parse.

**The hand arithmetic is in `test_fund_panel_ledger.hand.txt`, and it was written BEFORE this
file.** Every number asserted below appears there with its working: the AUM identity on BOIL's
2026-09-18 row, the boundary row where half a rounding unit is nearly the whole share count, the
82-row seed exclusion, and the contract month and `f_fut` of the live BOIL holdings table.

WHY A GOLDEN AT ALL, WHEN `tests/unit/test_fund_panel.py` ALREADY EXERCISES THE GATES
--------------------------------------------------------------------------------------
The unit tests run on synthetic frames and prove the gates FIRE. They cannot prove the builder
read the real file correctly, because they never touch it. This file pins the builder's output
against numbers computed by hand from the recorded bytes, so a change to the parse — a unit
conversion, a column, a seed rule, a rounding — moves a number here rather than silently
producing a different panel that still passes every gate.

BOTH INPUTS ARE GITIGNORED CACHE, so these tests SKIP rather than fail on a fresh clone:
`data/fixtures/*.csv.gz` is excluded by suffix and `data/raw/` is the raw cache. A skip here is
not a pass — `data/fixtures/fund_nav_daily.meta.json` carries the fixture's sha256, and
`scripts/fetch_fund_nav.py` re-fetches the source in one command.

No return is computed. The panel is NAV, shares and AUM.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "fund_nav_daily.csv.gz"
META = REPO / "data" / "fixtures" / "fund_nav_daily.meta.json"
HAND = Path(__file__).with_suffix("").with_name("test_fund_panel_ledger.hand.txt")
RECORDER = REPO / "data" / "raw" / "recorder"

#: The recorded live page the section-4 hand arithmetic was read off. Named exactly, because the
#: recorder never overwrites and a later fetch is a DIFFERENT file with different holdings.
BOIL_PAGE = RECORDER / "proshares_holdings" / "BOIL__20260921T231715Z.html"


def _script(name: str) -> Any:
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def panel(requires_panel) -> pd.DataFrame:
    requires_panel(FIXTURE)
    return pd.read_csv(FIXTURE, encoding="utf-8", dtype={"date": str, "fund": str})


@pytest.fixture(scope="module")
def meta() -> dict[str, Any]:
    if not META.exists():  # pragma: no cover - built by --build
        pytest.skip("fund_nav_daily.meta.json not built")
    return json.loads(META.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def holdings_mod() -> Any:
    return _script("fetch_fund_holdings")


def test_the_hand_file_exists_and_names_its_sources() -> None:
    """A golden whose hand file has gone missing is a golden asserting its own output."""
    text = HAND.read_text(encoding="utf-8")
    assert "BOIL__20260921T231414Z.csv" in text
    assert "BOIL__20260921T231715Z.html" in text
    assert "393,459,696.5651088" in text, "the hand product must still be the one asserted here"


# ============================================================ hand section 1: the AUM identity
def test_hand_aum_identity_on_boils_last_row(panel: pd.DataFrame) -> None:
    """`hand.txt` §1. nav x shares_out = 393,459,696.5651088 against an AUM of
    393,459,777.22870848 — a residual of 80.6636, which is four shares at that NAV and inside
    the five-share half of the published rounding unit."""
    row = panel[(panel["fund"] == "BOIL") & (panel["date"] == "2026-09-18")]
    assert len(row) == 1
    nav = float(row["nav"].iloc[0])
    shares = float(row["shares_out"].iloc[0])
    aum = float(row["aum"].iloc[0])

    assert nav == pytest.approx(20.16589992, abs=0, rel=1e-15)
    assert shares == 19_511_140.0, "the source publishes thousands; the panel stores SHARES"
    assert aum == pytest.approx(393_459_777.22870848, abs=1e-6)

    product = nav * shares
    assert product == pytest.approx(393_459_696.5651088, abs=1e-6)
    residual = abs(product - aum)
    assert residual == pytest.approx(80.6636, abs=1e-3)
    assert residual <= nav * 5.001 == pytest.approx(100.84966549992, abs=1e-6)

    implied = aum / nav
    assert implied == pytest.approx(19_511_144.0, abs=1e-3)
    assert abs(implied - shares) / 1.0 == pytest.approx(4.0, abs=1e-3), "four shares, under five"


def test_hand_boundary_row_uses_almost_all_the_tolerance(panel: pd.DataFrame, meta: dict[str, Any]) -> None:
    """`hand.txt` §2. BOIL 2012-02-01: five shares held, ten published. The identity passes on
    0.99979 of its tolerance, and that number is in the meta so the gate's strength is visible
    rather than hidden behind a 100% pass rate."""
    row = panel[(panel["fund"] == "BOIL") & (panel["date"] == "2012-02-01")]
    assert len(row) == 1
    nav, shares, aum = (float(row[c].iloc[0]) for c in ("nav", "shares_out", "aum"))
    assert (nav, shares) == (2_439_840.0, 10.0)
    assert aum == pytest.approx(12_199_321.992, abs=1e-6)
    assert aum / nav == pytest.approx(5.00005, abs=1e-6), "the fund held five shares"

    residual = abs(nav * shares - aum)
    tolerance = nav * 5.001
    assert residual / tolerance == pytest.approx(0.99979, abs=1e-5)

    g1 = meta["gates"]["G1_aum_identity"]
    assert g1["BOIL"]["worst_tolerance_use"] == pytest.approx(0.99979, abs=1e-5)
    assert g1["BOIL"]["share_within_rounding"] == 1.0
    assert g1["BOIL"]["share_within_1bp"] == pytest.approx(0.29872, abs=1e-5)


# ========================================================== hand section 3: the seed exclusion
def test_hand_seed_row_exclusion(panel: pd.DataFrame, meta: dict[str, Any]) -> None:
    """`hand.txt` §3. 82 rows, BOIL only, 2011-10-04 to 2012-01-31, and nothing is rescaled."""
    seed = meta["seed_row_rule"]
    assert seed["rule"] == "shares_out == 0"
    assert seed["excluded"] == {"BOIL": 82, "KOLD": 0, "SCO": 0, "UCO": 0}
    assert seed["dates"]["BOIL"] == ["2011-10-04", "2012-01-31"]
    assert seed["dates"]["KOLD"] == []

    boil = panel[panel["fund"] == "BOIL"]
    assert boil["date"].min() == "2012-02-01", "the first row after the excluded block"
    assert (panel["shares_out"] > 0).all(), "no seed row survives into the fixture"
    assert float(boil["nav"].max()) > 1e4, (
        "the rejected `nav > 1e4` rule would have dropped rows this fixture keeps"
    )


def test_hand_row_totals(panel: pd.DataFrame, meta: dict[str, Any]) -> None:
    """`hand.txt` §5. 16,484 source rows minus the 82 seed rows is 16,402."""
    assert len(panel) == 16_402
    per = meta["gates"]["G5_spans"]
    assert {f: per[f]["rows"] for f in per} == {"BOIL": 3679, "KOLD": 3761, "SCO": 4481, "UCO": 4481}
    assert sum(meta["per_fund"][f]["rows_in_source"] for f in ("BOIL", "KOLD", "SCO", "UCO")) == 16_484
    assert 16_484 - 82 == len(panel)
    assert list(panel.columns) == list(meta["columns"])
    assert meta["date_col"] == "date"


def test_the_deposit_columns_this_source_lacks_are_absent_not_null(panel: pd.DataFrame, meta: dict[str, Any]) -> None:
    """Deposit §3.1 line 67 asks for nine columns and this source carries six of them. The other
    three must not appear at all: a column of nulls reads as data missing on those days."""
    absent = meta["deposit_columns_absent"]["columns"]
    assert absent == ["futures_notional_by_contract_month", "swap_notional", "published_at"]
    for col in absent:
        assert col not in panel.columns


def test_no_split_was_found_and_the_carry_chain_says_why(meta: dict[str, Any]) -> None:
    """[] is a result here, not an omission. The carry deviations are what make it falsifiable:
    the largest is 1.5e-2 on SCO, four orders of magnitude below any split ratio."""
    splits = meta["splits"]
    assert splits["found"] == {"BOIL": [], "KOLD": [], "SCO": [], "UCO": []}
    carry = {f: splits["carry_check"][f]["max_carry_dev"] for f in ("BOIL", "KOLD", "SCO", "UCO")}
    assert carry["BOIL"] == pytest.approx(3.216e-5, rel=1e-2)
    assert carry["SCO"] == pytest.approx(1.510e-2, rel=1e-2)
    assert max(carry.values()) < 0.15, "below the detector's own threshold, so [] is consistent"
    for f in ("BOIL", "KOLD", "SCO", "UCO"):
        assert splits["carry_check"][f]["max_pct_dev"] < 2e-4, (
            "NAV[t]/PriorNAV[t] equals the stated NAV Change (%) on every row"
        )
    assert "alphavantage" in splits["no_independent_source"]


def test_the_meta_carries_the_holdout_note(meta: dict[str, Any]) -> None:
    """In the words of `fut_book_depth_1m.meta.json#holdout` (D604): the span runs through the
    deposit's sealed vault window and past this repository's 2024-01-01 seal, and the two are
    not reconciled. Nothing here may score anything until that reconciliation is in writing."""
    h = meta["holdout"]
    assert "2025-03-01..2026-09-18" in h
    assert "2024-01-01" in h
    assert "no return, no signal, no trade" in h
    assert "reconciliation is in writing" in h


# =================================================== hand section 4: the live holdings parse
def test_hand_live_boil_holdings_row(holdings_mod: Any) -> None:
    """`hand.txt` §4, against the recorded page itself: `NOV26 -> 2026-11`, three rows, and
    f_fut = 0.5958734028535384 on a denominator of 1,320,462,544.95."""
    if not BOIL_PAGE.exists():  # pragma: no cover - data/raw/ is the gitignored cache
        pytest.skip(f"{BOIL_PAGE.name} is not on this machine; re-fetch with fetch_fund_holdings.py")
    rows = holdings_mod.parse_holdings(BOIL_PAGE.read_bytes(), "BOIL")

    assert [r.kind for r in rows] == ["futures", "mmf", "cash"]
    assert rows[0].holdings_as_of == "2026-09-18"
    assert rows[0].description == "NATURAL GAS FUTR NOV26"
    assert rows[0].contract_month == "2026-11"
    assert rows[0].contracts == 25_857.0
    assert rows[0].notional_usd == 786_828_510.0
    assert rows[2].market_value_usd == pytest.approx(393_480_034.95, abs=1e-6)

    total = sum(holdings_mod.row_exposure(r) for r in rows)
    assert total == pytest.approx(1_320_462_544.95, abs=1e-6)
    assert holdings_mod.f_fut(rows) == pytest.approx(0.5958734028535384, abs=1e-15)
    assert holdings_mod.f_fut_derivatives(rows) == 1.0, "BOIL held no swap line on 2026-09-18"


def test_hand_uco_is_the_fund_whose_split_is_not_degenerate(holdings_mod: Any) -> None:
    """The §3.2 fact that matters most, pinned: on the same day BOIL is 100% futures, UCO is
    24.9% futures and 75.1% swap across four counterparty lines, and it holds DEC26, JUN27 and
    DEC27 rather than the front month. A flow model that maps UCO's rebalance onto CME futures
    one-for-one is wrong by a factor of four on this date."""
    page = RECORDER / "proshares_holdings" / "UCO__20260921T231719Z.html"
    if not page.exists():  # pragma: no cover
        pytest.skip(f"{page.name} is not on this machine")
    rows = holdings_mod.parse_holdings(page.read_bytes(), "UCO")

    swaps = [r for r in rows if r.kind == "swap"]
    futures = [r for r in rows if r.kind == "futures"]
    assert len(swaps) == 4 and len(futures) == 3
    assert sorted(r.contract_month for r in futures) == ["2026-12", "2027-06", "2027-12"]
    assert all(r.contract_month is None for r in swaps), "the swap lines name no month"
    assert holdings_mod.f_fut_derivatives(rows) == pytest.approx(0.249021394106897, abs=1e-12)
