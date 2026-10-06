"""Instrument implementations of the `Instrument` protocol in `base.py`.

The package convention is to import from the module path
(`instruments.equity import Equity`). `Future` is also re-exported here; `Equity` and
`OptionStub` are not, so for those two only the module path resolves.
"""

from backtest_framework.instruments.future import Future

__all__ = ["Future"]
