"""Instrument implementations of the `Instrument` protocol in `base.py`.

Import from the module path (`instruments.equity import Equity`). Only `Future` is also
re-exported here; `Equity` and `OptionStub` are available only from their modules.
"""

from backtest_framework.instruments.future import Future

__all__ = ["Future"]
