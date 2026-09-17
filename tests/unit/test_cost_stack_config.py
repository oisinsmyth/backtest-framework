"""Declarative cost-stack config (D102, audit F2): the dict a study logs is the
dict its stack is built from — behaviourally identical to hand construction, and
invalid configs fail loudly at factory time naming the bad key.
"""

from datetime import datetime, timedelta

import pytest

from backtest_framework.config.cost_stack import (
    BRICK_KEYS,
    StackDataContext,
    _brick_registry,
    build_cost_stack,
    validate_stack_config,
)
from backtest_framework.config.errors import ConfigError
from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest, SqrtImpact
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import CorporateActions, as_declared_dividends
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

START = datetime(2026, 1, 5, 16)
XLE = Equity(symbol="XLE")


def _context() -> StackDataContext:
    prices = [50.0, 51.0, 50.5, 52.0, 51.5, 53.0]
    bars = [
        TimestampedBar(START + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
        for i, p in enumerate(prices)
    ]
    actions = CorporateActions(
        dividends_by_symbol={"XLE": ((START + timedelta(days=3), 0.5),)},
        splits_by_symbol={"XLE": ((START + timedelta(days=2), 2.0),)},
    )
    return StackDataContext(
        bars_by_symbol={"XLE": bars}, volumes_by_symbol={"XLE": [1e6] * len(prices)}, actions=actions
    )


STACK_CONFIG = {
    "trade_bricks": [
        {"type": "ibkr_commission"},
        {"type": "sqrt_impact", "coefficient": 1.0, "calibration": "full_sample"},
        {"type": "percent_spread", "bps": 1.0},
    ],
    "carry_bricks": [{"type": "borrow_fee", "annual_rate": 0.0025}],
    "portfolio_carry_bricks": [{"type": "margin_interest", "annual_rate": 0.06}],
    "event_flow_bricks": [{"type": "dividend_flow", "source": "snapshot_declared"}],
}


def test_config_built_stack_matches_hand_built_behaviourally():
    context = _context()
    built = build_cost_stack(STACK_CONFIG, context)

    declared = {
        symbol: tuple(as_declared_dividends(divs, context.actions.splits_by_symbol.get(symbol, ())))
        for symbol, divs in context.actions.dividends_by_symbol.items()
    }
    hand = CostStack(
        trade_bricks=(
            IBKRCommission(),
            SqrtImpact(params_by_symbol=calibrate_impact_params(context.bars_by_symbol, context.volumes_by_symbol)),
            PercentOfNotionalSpread(bps=1.0),
        ),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol=declared),),
    )

    prev, curr = START + timedelta(days=2), START + timedelta(days=5)
    assert built.trade_cost(XLE, 500, 52.0) == hand.trade_cost(XLE, 500, 52.0)
    assert built.carry_cost(-25_000.0, prev, curr) == hand.carry_cost(-25_000.0, prev, curr)
    assert built.portfolio_carry_cost(10_000.0, prev, curr) == hand.portfolio_carry_cost(10_000.0, prev, curr)
    assert built.event_flow(XLE, 100.0, prev, curr) == hand.event_flow(XLE, 100.0, prev, curr)
    assert built.event_flow(XLE, 100.0, prev, curr) != 0.0  # dividend really flowed


@pytest.mark.parametrize(
    ("config", "match"),
    [
        ({**STACK_CONFIG, "extra_slot": []}, "unknown key"),
        ({k: v for k, v in STACK_CONFIG.items() if k != "carry_bricks"}, "missing required slot"),
        ({**STACK_CONFIG, "trade_bricks": [{"type": "no_such_brick"}]}, "unknown type"),
        ({**STACK_CONFIG, "trade_bricks": [{"type": "percent_spread"}]}, "bps"),
        ({**STACK_CONFIG, "trade_bricks": [{"type": "sqrt_impact", "calibration": "psychic"}]}, "calibration"),
        ({**STACK_CONFIG, "event_flow_bricks": [{"type": "dividend_flow", "source": "vibes"}]}, "source"),
        ({**STACK_CONFIG, "carry_bricks": [{"type": "borrow_fee", "annual_rate": "high"}]}, "numeric"),
        # A typo on an OPTIONAL parameter, which is the whole silent surface: a typo on a
        # required key already raised through `_required_numeric`, so only the optional ones
        # could be quietly dropped and replaced by a default.
        (
            {**STACK_CONFIG, "trade_bricks": [{"type": "sqrt_impact", "coeficient": 3.0}]},
            "unknown key",
        ),
        (
            {**STACK_CONFIG, "trade_bricks": [{"type": "ibkr_commission", "per_shre": 0.1}]},
            "unknown key",
        ),
        (
            {**STACK_CONFIG, "event_flow_bricks": [{"type": "dividend_flow", "sources": "x"}]},
            "unknown key",
        ),
    ],
)
def test_invalid_stack_configs_fail_loudly_naming_the_problem(config, match):
    with pytest.raises(ConfigError, match=match):
        build_cost_stack(config, _context())


@pytest.mark.parametrize(
    "brick",
    [
        {"type": "percent_spread", "bps": 1.0},
        {"type": "borrow_fee", "annual_rate": 0.02},
        {"type": "margin_interest", "annual_rate": 0.06},
        {"type": "flat_commission", "amount": 1.0},
        {"type": "flat_rate_carry", "annual_rate": 0.01},
        {"type": "ibkr_commission"},
        {"type": "ibkr_commission", "per_share": 0.005, "min_per_order": 1.0, "max_pct_of_trade_value": 0.01},
        {"type": "sqrt_impact", "calibration": "full_sample", "coefficient": 1.0},
        # Pre-D187 shape, WITHOUT volume_units. 2,170 trials are stored carrying it, so
        # rejecting it would retroactively invalidate part of a published multiplicity pool.
        {"type": "sqrt_impact", "coefficient": 1.0},
        {"type": "dividend_flow", "source": "snapshot_declared"},
    ],
)
def test_every_shape_a_factory_accepts_survives_the_key_check(brick):
    """The other half of an allowed-key table: it must not reject anything real.

    A key missing from `BRICK_KEYS` turns a working config into a raise, and four of those
    keys are exercised by nothing — `flat_commission` and `flat_rate_carry` appear in no
    source literal and in none of the 240,766 brick configs stored across the trial
    registries, and `ibkr_commission` is stored 4,393 times always as the bare
    `{"type": "ibkr_commission"}`. Without this test a typo in those rows would be caught by
    nothing at all.
    """
    slot = "event_flow_bricks" if brick["type"] == "dividend_flow" else "trade_bricks"
    validate_stack_config({**STACK_CONFIG, slot: [brick]})


def test_the_key_table_covers_every_registered_brick_type():
    """A new brick type without a row here would be unvalidated and silently lenient."""
    registered = set(_brick_registry(_context())._factories)
    assert registered == set(BRICK_KEYS), (
        f"registered but not in BRICK_KEYS: {sorted(registered - set(BRICK_KEYS))}; "
        f"in BRICK_KEYS but not registered: {sorted(set(BRICK_KEYS) - registered)}"
    )
    for type_name, keys in BRICK_KEYS.items():
        assert "type" in keys, f"{type_name} must allow its own 'type' key"
