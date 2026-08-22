"""D24 U-gates: same snapshot ID -> byte-identical data (checksum verified on load);
identical content -> same ID (idempotent); different content -> new ID; tampering ->
refused; quarantined -> unreachable by any default path (D26, D72).
"""

from datetime import datetime
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.data.snapshot_store import (
    QuarantinedSnapshotError,
    SnapshotIntegrityError,
    SnapshotStore,
)
from backtest_framework.data.validator import ValidationResult, Violation
from backtest_framework.simulator.fills import Bar


def _bars(close: float = 100.0):
    return {"A": [TimestampedBar(datetime(2026, 1, 1), Bar(open=close, high=close, low=close, close=close))]}


ACTIONS = CorporateActions(dividends_by_symbol={"A": [(datetime(2026, 1, 2), 0.5)]})


def test_create_load_roundtrip_and_id_stability(tmp_path):
    store = SnapshotStore(tmp_path)
    snapshot_id = store.create(_bars(), ACTIONS)

    loaded = store.load(snapshot_id)

    assert loaded.snapshot_id == snapshot_id
    assert loaded.bars_by_symbol == _bars()
    assert loaded.actions == ACTIONS


def test_identical_content_is_idempotent_same_id(tmp_path):
    store = SnapshotStore(tmp_path)
    first = store.create(_bars(), ACTIONS)
    second = store.create(_bars(), ACTIONS)
    assert first == second  # content-addressed: re-freezing identical data dedupes


def test_restated_history_gets_a_new_id(tmp_path):
    store = SnapshotStore(tmp_path)
    original = store.create(_bars(100.0), ACTIONS)
    restated = store.create(_bars(100.01), ACTIONS)  # yfinance restates a close
    assert original != restated


def test_tampered_payload_refuses_to_load(tmp_path):
    store = SnapshotStore(tmp_path)
    snapshot_id = store.create(_bars(), ACTIONS)

    bars_file = tmp_path / snapshot_id / "bars.csv"
    bars_file.write_text(bars_file.read_text(encoding="utf-8").replace("100.0", "999.0"), encoding="utf-8")

    with pytest.raises(SnapshotIntegrityError):
        store.load(snapshot_id)


def test_quarantined_snapshot_is_unreachable_by_default(tmp_path):
    store = SnapshotStore(tmp_path)
    failed_validation = ValidationResult(
        violations=(
            Violation("A", datetime(2026, 1, 1), "ohlc_inconsistent", "low>high", hard=True),
        )
    )
    snapshot_id = store.create(_bars(), ACTIONS, validation=failed_validation)

    with pytest.raises(QuarantinedSnapshotError):
        store.load(snapshot_id)

    inspected = store.load(snapshot_id, allow_quarantined=True)  # inspection-only path
    assert inspected.meta["quarantined"] is True


def test_passing_validation_is_loadable_and_meta_carries_reports(tmp_path):
    store = SnapshotStore(tmp_path)
    snapshot_id = store.create(_bars(), ACTIONS, validation=ValidationResult())

    loaded = store.load(snapshot_id)
    assert loaded.meta["quarantined"] is False
    assert loaded.meta["validation"]["passed"] is True


# ------------------------------------------------- the schema extension is inert (D190)

_FIXTURE_SNAPSHOT_IDS = {
    # Pinned BEFORE `save_fixture_csv` grew its `extra_columns` parameter. A snapshot id
    # is logged with every trial and printed in results docs, so a writer change that
    # moved these would silently invalidate the provenance of every study in the repo.
    "crypto_intraday_1h_raw": "88b3e08d666006f7b47f08ba42eaa3bcae5ec484d9a8d3811d1c7240e177a281",
    "crypto_universe_2015_2025_raw": "51756f0d66b037982a8fb7d08db68d843fb84e81bf62f51e97688798da90776d",
    "universe_daily_2015_2024_raw": "b1e9424d04ca988264a3421ad337c6dd8e69d96c2e4aa985402821a9110eb1ad",
}


@pytest.mark.parametrize("name,expected", sorted(_FIXTURE_SNAPSHOT_IDS.items()))
def test_committed_fixtures_still_freeze_to_their_original_snapshot_id(
    name, expected, tmp_path
):
    from backtest_framework.data.corporate_actions import load_events_json
    from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes

    fixtures = Path(__file__).resolve().parents[2] / "data" / "fixtures"
    bars, volumes = load_fixture_csv_with_volumes(fixtures / f"{name}.csv.gz")
    actions = load_events_json(fixtures / f"{name}_events.json")

    store = SnapshotStore(tmp_path / "snapshots")
    assert store.create(bars, actions, volumes_by_symbol=volumes) == expected


def test_extra_columns_change_the_snapshot_id_and_survive_the_roundtrip(tmp_path):
    """The other half: opting IN must change the payload, or the columns are not stored."""
    bars = {"X": [TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 1.0, 1.0, 1.0))]}
    store = SnapshotStore(tmp_path / "snapshots")
    plain = store.create(bars, CorporateActions(), volumes_by_symbol={"X": [7.0]})
    with_extras = store.create(
        bars,
        CorporateActions(),
        volumes_by_symbol={"X": [7.0]},
        extra_columns={"base_volume": {"X": [3.0]}},
    )
    assert plain != with_extras
    assert store.load(plain).extras == {}
    assert store.load(with_extras).extras == {"base_volume": {"X": [3.0]}}
