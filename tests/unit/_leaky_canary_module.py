"""THE LEAK CANARY. A deliberately leaky feature module, and its honest twin (D593).

`SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8 control 6: *"the test harness includes a
deliberately leaky feature (using a future bar). The pipeline's static checks must reject
it. If it isn't caught, all results are invalid until the check is fixed."* Ledger unit test
71 and `OPENING_AGENT_STATE_PREREG.md` unit test 25 say the same thing.

**This file is not a test and pytest never imports it.** `pyproject.toml` sets
`python_files = ["test_*.py"]` (D546), so a `_leaky_*.py` under `tests/` is not collectable;
`tests/unit/test_nothing_outside_tests_is_collectable.py` scans only paths OUTSIDE `tests/`,
so nothing here forbids it either. It is read as TEXT by `tests/unit/test_lookahead.py`, and
kept as a real file rather than a string constant so that the scan runs on something a linter,
a type checker and a human reader all see as code — a canary written as a string is a canary
nobody would ever notice had stopped being leaky.

Nothing here is imported, called or executed by anything. The functions take plain arrays and
frames and compute nothing that is used.

THE FOUR LEAKS, one per shape `forward_index_sites` claims to catch, and THREE HONEST
FUNCTIONS that it must leave alone. The honest half is the load-bearing half: a scan that
flagged `close[:t + 1]` or `.shift(1)` would have been switched off within a day.
"""


def momentum_leaky(close, t):
    """LEAK: reads the bar after the decision bar. `forward_index` at `close[t + 1]`."""
    return close[t + 1] / close[t] - 1.0


def cross_section_leaky(score, t):
    """LEAK: the same read through a tuple subscript on a (n_symbols, T) grid."""
    return score[:, t + 1]


def next_return_leaky(df):
    """LEAK: `.shift(-1)` moves tomorrow's close onto today's row."""
    return df["close"].shift(-1) / df["close"] - 1.0


def tail_mean_leaky(close, t):
    """LEAK: a slice whose LOWER bound starts after the decision bar."""
    return close[t + 1:].mean()


def momentum_honest(close, t):
    """Backward. `close[t - 1]` is a subtraction, not an addition, and is never flagged."""
    return close[t] / close[t - 1] - 1.0


def window_honest(close, t):
    """`close[:t + 1]` is the ordinary bar-INCLUSIVE window: the upper bound is not a leak."""
    return close[: t + 1].mean()


def lagged_honest(df):
    """`.shift(1)` is the lag every runner here applies; `np.roll` with a positive shift too."""
    return df["close"].shift(1)
