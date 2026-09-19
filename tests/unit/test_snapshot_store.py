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
    name, expected, tmp_path, requires_panel
):
    from backtest_framework.data.corporate_actions import load_events_json
    from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes

    fixtures = Path(__file__).resolve().parents[2] / "data" / "fixtures"
    requires_panel(fixtures / f"{name}.csv.gz")
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


# A snapshot id frozen from a payload built in code. It owes nothing to any data file, so it
# survives a fixture being removed for a licence reason -- which matters because
# `crypto_universe_2015_2025_raw` is the ONLY entry in `_FIXTURE_SNAPSHOT_IDS` that a clone
# receives; the other two are manifested out and skip. Until this existed, the absolute value of
# a snapshot id was verified on CI by exactly one file, and that file's presence is a standing
# decision that could be revisited (D553).
SYNTHETIC_SNAPSHOT_ID = "e77fe8e910a5521a5f63fa74f90209dfe7c660b2c89b08da3709ed58e9360a71"


def test_a_snapshot_id_built_from_code_is_frozen(tmp_path):
    """The identity, pinned without a fixture.

    Every other test in this file checks a RELATIONSHIP -- idempotence, uniqueness after a
    restatement, refusal after tampering -- and each of those would pass unchanged if the id
    algorithm were replaced wholesale. D551 is the proof: the writer's newline handling made the
    same payload freeze to two different ids depending on the operating system, and nothing here
    caught it except the fixture pin.

    This payload exercises what carried the risk: dividends and splits, which go through the
    `events.json` writer D551 fixed, volumes, and two symbols so ordering matters.
    """
    bars = {
        "AAA": [
            TimestampedBar(datetime(2021, 1, 4), Bar(10.0, 11.5, 9.75, 11.0)),
            TimestampedBar(datetime(2021, 1, 5), Bar(11.0, 12.25, 10.5, 12.0)),
        ],
        "BBB": [
            TimestampedBar(datetime(2021, 1, 4), Bar(100.0, 101.0, 99.0, 100.5)),
            TimestampedBar(datetime(2021, 1, 5), Bar(100.5, 103.0, 100.0, 102.75)),
        ],
    }
    volumes = {"AAA": [1500.0, 2250.0], "BBB": [88000.0, 91500.0]}
    actions = CorporateActions(
        dividends_by_symbol={"BBB": [(datetime(2021, 1, 5), 0.375)]},
        splits_by_symbol={"AAA": [(datetime(2021, 1, 5), 0.5)]},
    )

    store = SnapshotStore(tmp_path / "snapshots")
    assert store.create(bars, actions, volumes_by_symbol=volumes) == SYNTHETIC_SNAPSHOT_ID, (
        "the snapshot id of a fixed payload has moved. Every id this project has logged with a "
        "trial or printed in a results document was computed by the old rule. Find what changed "
        "in save_fixture_csv or save_events_json before touching this constant."
    )

