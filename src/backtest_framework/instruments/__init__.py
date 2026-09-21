"""Instrument implementations of the `Instrument` protocol in `base.py` (D12).

This file was empty, as every other sub-package `__init__.py` here is: the house
convention is to import from the module path (`instruments.equity import Equity`), and
the packages carry no re-export surface at all.

`Future` is exported here because the record that added it asked for it, and the asymmetry
is stated rather than hidden: `Equity` and `OptionStub` are NOT re-exported, and adding
them was outside that record's touch list. Either import style resolves for `Future`; only
the module path resolves for the other two.

The record's number is deliberately not written here. This file is TRACKED while the
record is not yet staged, and `tests/unit/test_cited_decisions_exist.py` resolves
citations against `git ls-files` — so a number in this docstring would redden that gate
until the record is committed. `future.py` carries the citation, and it lands in the same
commit as the record.
"""

from backtest_framework.instruments.future import Future

__all__ = ["Future"]
