"""Metrics tearsheet renderer (D36, D37, D49).

The surface where the honesty rules become visible: the risk-free rate is stated in
the Sharpe row itself (never implicit), realised beta carries the D37 "expected ≈ 0
for a market-neutral book" note when a benchmark is present, and VaR/CVaR print the
literal insufficient-data message instead of a number the sample can't support.
"""

from __future__ import annotations

from typing import Sequence

from .metrics import max_drawdown, realised_beta, sharpe, sortino
from .monte_carlo import block_bootstrap_percentiles
from .tail_risk import var_cvar


def render_metrics_table(
    returns: Sequence[float],
    rf_annual: float,
    periods_per_year: float,
    equity_curve: Sequence[tuple[object, float]] | None = None,
    benchmark_returns: Sequence[float] | None = None,
    mc_seed: int | None = None,
) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    lines.append(f"| Sharpe (rf={rf_annual:.2%}/yr, {periods_per_year:g} periods/yr) | {sharpe(returns, rf_annual, periods_per_year):.3f} |")
    lines.append(f"| Sortino (rf={rf_annual:.2%}/yr) | {sortino(returns, rf_annual, periods_per_year):.3f} |")
    if equity_curve is not None:
        lines.append(f"| Max drawdown | {max_drawdown(equity_curve):.2%} |")
    if benchmark_returns is not None:
        beta = realised_beta(returns, benchmark_returns)
        lines.append(f"| Realised beta vs benchmark | {beta:+.4f} (market-neutral expectation: ≈ 0, D37) |")

    tail = var_cvar(returns)
    if tail.sufficient:
        lines.append(f"| VaR {tail.confidence:.0%} (daily) | {tail.var:.2%} |")
        lines.append(f"| CVaR {tail.confidence:.0%} (daily) | {tail.cvar:.2%} |")
    else:
        lines.append(f"| VaR/CVaR {tail.confidence:.0%} | {tail.insufficient_reason} |")

    if mc_seed is not None:
        mc = block_bootstrap_percentiles(returns, seed=mc_seed)
        percentiles = sorted(mc.terminal_return)
        header = " | ".join(f"p{p}" for p in percentiles)
        terminal = " | ".join(f"{mc.terminal_return[p]:+.2%}" for p in percentiles)
        drawdown = " | ".join(f"{mc.max_drawdown[p]:.2%}" for p in percentiles)
        lines.append("")
        lines.append(f"Block bootstrap (n={mc.n_sims:,}, block={mc.block_size}, seed={mc.seed} — D34/D36):")
        lines.append(f"| | {header} |")
        lines.append("|---|" + "---|" * len(percentiles))
        lines.append(f"| Terminal return | {terminal} |")
        lines.append(f"| Max drawdown | {drawdown} |")

    return "\n".join(lines)
