"""Unit tests for the Instrument abstraction (D12, D16), per VERIFICATION_SCHEME.md Step 3."""

from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.option_stub import OptionStub


def test_equity_notional_is_quantity_times_price():
    equity = Equity(symbol="AAPL")
    assert equity.notional(quantity=100, price=150.0) == 15_000.0


def test_equity_tradeable_quantity_whole_shares_rounds_to_int():
    equity = Equity(symbol="AAPL")  # quantity_precision=None -> whole shares only
    assert equity.tradeable_quantity(99.6) == 100.0
    assert equity.tradeable_quantity(99.4) == 99.0


def test_equity_tradeable_quantity_fractional_shares_rounds_to_precision():
    equity = Equity(symbol="AAPL", quantity_precision=4)
    assert equity.tradeable_quantity(12.345678) == 12.3457


def test_equity_tradeable_quantity_eight_decimal_crypto_precision_stub():
    # Proves the rounding mechanism generalizes to crypto-like precision; this is not a
    # real crypto instrument (no funding carry component, no 365-day calendar override —
    # that's D14/Step 10's job).
    equity = Equity(symbol="BTC-STUB", quantity_precision=8)
    assert equity.tradeable_quantity(0.123456789) == 0.12345679


def test_equity_carry_components_lists_only_components_a_filter_can_match():
    equity = Equity(symbol="AAPL")
    assert equity.carry_components() == ("borrow", "dividend")


def test_no_instrument_declares_a_carry_component_no_brick_models():
    """The D48 defect this pins: Equity declared "margin_interest", and
    `costs/stack.py:_applies` — the only consumer of these names — could never match
    it, because MarginInterest is a PORTFOLIO brick reached through
    portfolio_carry_cost, which applies no filter. A name here that no brick declares
    is decoration. Written against the brick classes rather than a literal list so it
    still fires when a future instrument invents a component and forgets the brick."""
    from backtest_framework.costs import equity_bricks

    declared_by_bricks = {
        getattr(obj, "component")
        for obj in vars(equity_bricks).values()
        if isinstance(obj, type) and getattr(obj, "component", None) is not None
    }
    assert declared_by_bricks, "no brick declares a component — this test can no longer fire"

    for instrument in (Equity(symbol="AAPL"), _sample_option()):
        unmatched = set(instrument.carry_components()) - declared_by_bricks
        assert not unmatched, (
            f"{type(instrument).__name__}.carry_components() declares {sorted(unmatched)}, "
            "which no cost brick models — D48 false affordance"
        )


def test_margin_requirement_is_gone_from_the_instrument_interface():
    """D48: the member had zero call sites in src/ and Equity answered it with full
    notional, not a Reg T 50% requirement — a wrong number nothing could notice. It was
    deleted rather than wired; the buying-power lock stays deferred on D107 §1's terms.
    If it comes back, it comes back with a RiskLimits rule that reads it, and this test
    is the reminder to delete this test rather than to quietly re-add the method."""
    from backtest_framework.instruments.base import Instrument

    assert not hasattr(Equity(symbol="AAPL"), "margin_requirement")
    assert not hasattr(_sample_option(), "margin_requirement")
    assert "margin_requirement" not in Instrument.__protocol_attrs__  # type: ignore[attr-defined]


# --- Option stub (D16, D48) -------------------------------------------------------


def _sample_option() -> OptionStub:
    return OptionStub(underlying_symbol="AAPL", strike=150.0, expiry="2026-09-18", option_type="call")


def test_option_stub_notional_multiplier_math_correct():
    option = _sample_option()
    # 2 contracts, $3.50 premium/share, 100 shares/contract -> 2 * 3.50 * 100
    assert option.notional(quantity=2, price=3.50) == 700.0


def test_option_stub_tradeable_quantity_whole_contracts_only():
    option = _sample_option()
    assert option.tradeable_quantity(2.6) == 3.0


def test_option_stub_carry_components_is_correctly_empty_not_unimplemented():
    option = _sample_option()
    assert option.carry_components() == ()


def test_options_extension_doc_is_the_real_scoping_decision_not_a_stub():
    # Step 11's deliverable is the written scoping rationale (D16, D84). Same
    # doc-rot discipline as the D38/D82 label test: docs decay unless a test greps.
    from pathlib import Path

    doc = (Path(__file__).resolve().parent.parent.parent / "docs" / "options_extension.md").read_text(
        encoding="utf-8"
    )
    assert "Status: stub" not in doc  # the placeholder banner is gone
    for required_section in (
        "deliberately deferred",
        "What exists today",
        "six hard problems",
        "Trigger conditions",
        "What \"done\" would mean",
    ):
        assert required_section in doc, f"options_extension.md lost its '{required_section}' section"


def test_whole_share_rounding_convention_is_pinned_round_half_even():
    # D106 (audit F15): tradeable_quantity uses Python round() — banker's rounding
    # to the NEAREST whole share. This is a stated convention: changing it (e.g. to
    # floor-toward-zero) would silently move every fill in every committed artifact,
    # so any change must arrive as a deliberate study-version bump, not a refactor.
    equity = Equity(symbol="TEST")
    assert equity.tradeable_quantity(1252.96) == 1253.0  # rounds UP past the target
    assert equity.tradeable_quantity(0.5) == 0.0  # half-to-even
    assert equity.tradeable_quantity(1.5) == 2.0
    assert equity.tradeable_quantity(2.5) == 2.0
    assert equity.tradeable_quantity(-1252.96) == -1253.0  # symmetric for shorts
