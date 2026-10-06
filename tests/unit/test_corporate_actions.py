"""Unit tests for corporate-action frame conversions.

Notional and dividend cash must be the same whether computed in the split-adjusted or the
as-traded frame. yfinance's auto_adjust=False data is in the split-adjusted frame (checked
on XOP's 2020-03-30 reverse split); as_traded_from_adjusted and as_declared_dividends
reconstruct the as-traded frame.
"""

from datetime import datetime

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import (
    CorporateActions,
    as_declared_dividends,
    as_traded_from_adjusted,
    load_events_json,
    save_events_json,
    split_adjusted,
)
from backtest_framework.simulator.fills import Bar


def _tb(day: int, price: float) -> TimestampedBar:
    return TimestampedBar(datetime(2020, 3, day), Bar(open=price, high=price, low=price, close=price))


REVERSE_SPLIT = [(datetime(2020, 3, 30), 0.25)]  # 1-for-4: shares x0.25, price x4


def test_as_traded_reconstruction_reverse_split():
    # Adjusted frame is continuous (~32 both sides); true pre-split price was ~8.
    adjusted = [_tb(27, 32.12), _tb(30, 32.01)]
    true = as_traded_from_adjusted(adjusted, REVERSE_SPLIT)
    assert true[0].bar.close == pytest.approx(32.12 * 0.25)  # 8.03, the as-traded 2020-03-27 price
    assert true[1].bar.close == 32.01  # on/after ex-date: unchanged


def test_split_adjusted_is_the_inverse_direction():
    # True frame jumps 4x at the split; adjusting makes it continuous again.
    true = [_tb(27, 8.03), _tb(30, 32.01)]
    adjusted = split_adjusted(true, REVERSE_SPLIT)
    assert adjusted[0].bar.close == pytest.approx(8.03 / 0.25)  # 32.12
    assert adjusted[1].bar.close == 32.01


def test_forward_split_convention():
    # 4-for-1 forward (ratio 4.0): shares x4, price /4. True frame: 400 -> 100.
    forward = [(datetime(2020, 3, 30), 4.0)]
    true = [_tb(27, 400.0), _tb(30, 100.0)]
    adjusted = split_adjusted(true, forward)
    assert adjusted[0].bar.close == pytest.approx(100.0)  # continuous
    back = as_traded_from_adjusted(adjusted, forward)
    assert back[0].bar.close == pytest.approx(400.0)  # roundtrip


def test_as_declared_dividends_cash_invariance():
    # Adjusted-frame 0.38/share pre-split -> declared 0.095/share on 4x the shares:
    # identical cash either way.
    adjusted_divs = [(datetime(2020, 3, 23), 0.38), (datetime(2020, 6, 22), 0.311)]
    declared = as_declared_dividends(adjusted_divs, REVERSE_SPLIT)

    assert declared[0][1] == pytest.approx(0.38 * 0.25)  # pre-split: converted
    assert declared[1][1] == pytest.approx(0.311)  # post-split: unchanged

    # Invariance: adj_qty x adj_div == true_qty x declared_div for the same capital.
    capital, adj_price = 32_000.0, 32.0
    adj_qty = capital / adj_price  # 1,000 adjusted shares
    true_qty = adj_qty / 0.25  # 4,000 real shares held pre-split
    assert adj_qty * 0.38 == pytest.approx(true_qty * declared[0][1])


def test_no_splits_is_identity():
    bars = [_tb(27, 50.0)]
    assert as_traded_from_adjusted(bars, []) == bars
    assert split_adjusted(bars, []) == bars
    assert as_declared_dividends([(datetime(2020, 3, 23), 0.5)], []) == [(datetime(2020, 3, 23), 0.5)]


def test_events_json_roundtrip(tmp_path):
    actions = CorporateActions(
        dividends_by_symbol={"XLE": [(datetime(2015, 3, 20), 0.2575)]},
        splits_by_symbol={"XOP": [(datetime(2020, 3, 30), 0.25)]},
    )
    path = tmp_path / "events.json"
    save_events_json(path, actions)
    loaded = load_events_json(path)

    assert loaded.dividends_by_symbol == {"XLE": [(datetime(2015, 3, 20), 0.2575)]}
    assert loaded.splits_by_symbol == {"XOP": [(datetime(2020, 3, 30), 0.25)]}


def test_the_events_file_is_byte_identical_on_every_platform(tmp_path):
    """`save_events_json` writes CRLF line endings on every platform.

    `SnapshotStore.create` hashes this file into the snapshot id, which is logged with every
    trial. Text-mode newline translation (as in `Path.write_text`) would give the same fixture
    different snapshot ids on Windows and Linux. Existing ids were computed over CRLF bytes,
    so switching to LF would change all of them.

    On Windows text mode already writes CRLF, so this test can only fail on Linux, e.g. in CI.
    """
    actions = CorporateActions(
        dividends_by_symbol={"XLE": [(datetime(2015, 3, 20), 0.2575)]},
        splits_by_symbol={"XOP": [(datetime(2020, 3, 30), 0.25)]},
    )
    path = tmp_path / "events.json"
    save_events_json(path, actions)
    raw = path.read_bytes()

    assert b"\r\n" in raw, "the events payload must be CRLF; a snapshot id is a hash of it"
    assert raw.count(b"\n") == raw.count(b"\r\n"), (
        f"{raw.count(b'\n') - raw.count(b'\r\n')} bare LF byte(s) in the events payload. On a "
        f"platform where these come out as LF, existing snapshot ids stop reproducing."
    )
    # The file still loads back correctly.
    assert load_events_json(path).splits_by_symbol == {"XOP": [(datetime(2020, 3, 30), 0.25)]}

