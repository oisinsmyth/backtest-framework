"""D24 U-gates: same snapshot ID -> byte-identical data (checksum verified on load);
identical content -> same ID (idempotent); different content -> new ID; tampering ->
refused; quarantined -> unreachable by any default path (D26, D72).
"""

from datetime import datetime

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
