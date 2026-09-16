"""Gates on the D224 assembled strategy.

The one that matters most is `test_the_stop_bar_is_a_held_bar_not_an_escape`. The
first version of this runner zeroed the position on the bar the stop triggered, so
the book escaped the entire adverse move that caused the stop — look-ahead, which
inflated C_stop's gross Sharpe to +4.197. It was caught by the magnitude being
implausible, not by a test. This is that test.

The second is `test_var_trials_comes_from_the_null_and_not_from_the_cells`. D219's
amendment established that estimating var_trials from a sweep containing real
effects inflates the floor; here C_stop's -3.17 pushes it to +4.944 annualised,
which is not a noise floor for anything.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "assembled_strategy_summary.json"
PAGE = REPO / "docs" / "results" / "ASSEMBLED_RESULTS.md"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


A = _load("run_assembled_strategy", "run_assembled_strategy.py")


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_assembled_strategy.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return PAGE.read_text(encoding="utf-8").replace("−", "-").replace("×", "x")


# --------------------------------------------------------------------------
# 1. The look-ahead defect this runner had
# --------------------------------------------------------------------------


def _synthetic(n=6000, seed=1):
    """A drifting series long enough to clear the 4,049-bar warm-up, with periodic
    sharp intrabar spikes down so the trailing stop is actually exercised.

    The first version of this helper was 400 bars — below the warm-up — so no
    position ever existed and the look-ahead test passed vacuously. A test that
    cannot fail is worse than no test."""
    from datetime import datetime, timedelta

    from backtest_framework.data.bars import TimestampedBar
    from backtest_framework.simulator.fills import Bar

    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0008, 0.004, n)))
    bars = []
    t0 = datetime(2020, 1, 1)
    for i, c in enumerate(close):
        prev = close[i - 1] if i else c
        lo = min(prev, c) * (0.94 if (i > 4200 and i % 137 == 0) else 0.998)
        hi = max(prev, c) * 1.002
        bars.append(
            TimestampedBar(
                timestamp=t0 + timedelta(minutes=15 * i),
                bar=Bar(open=prev, high=hi, low=lo, close=c),
            )
        )
    return bars


def test_the_stop_bar_is_a_held_bar_not_an_escape():
    """THE DEFECT. On the bar the stop triggers the book must still be long and must
    take the loss down to the fill. Zeroing the position there lets it escape the
    whole adverse move, which is look-ahead and inflated gross Sharpe to +4.2."""
    bars = _synthetic()
    volumes = np.ones(len(bars))
    pos, meta = A.build_positions(bars, volumes, gated=False, stopped=True)
    assert meta["stop_exits"] > 0, "the synthetic series must trigger the stop"
    for idx, value in meta["ret_override"].items():
        assert pos[idx] != 0.0, "the stop bar must still be a HELD bar"
        assert value < 0.0, "a stop-out bar must carry a loss, not zero"


def test_the_stop_fill_uses_the_repos_own_d10_rule_and_not_a_restatement():
    """A bar that gaps through the stop fills at the OPEN, not the stop price.
    That rule already exists as `simulator.fills.stop_fill_price` (D10); this
    runner calls it rather than restating it, which is what D212 is about."""
    assert "stop_fill_price" in dir(A)
    bars = _synthetic()
    volumes = np.ones(len(bars))
    close = np.asarray([b.bar.close for b in bars])
    open_ = np.asarray([b.bar.open for b in bars])
    _pos, meta = A.build_positions(bars, volumes, gated=False, stopped=True)
    for idx, value in meta["ret_override"].items():
        implied_fill = close[idx - 1] * math.exp(value)
        assert implied_fill <= open_[idx] + 1e-9, "fill better than the open"


def test_the_gate_reads_the_decision_bar_and_not_the_fill_bar():
    """Perturb volume from bar t onward; the gate decision for a position that first
    exists at t must not move."""
    bars = _synthetic()
    rng = np.random.default_rng(5)
    vol = rng.lognormal(8.0, 0.5, len(bars))
    base, _ = A.build_positions(bars, vol, gated=True, stopped=False)
    t = 5200
    tampered = vol.copy()
    tampered[t:] *= 100.0
    after, _ = A.build_positions(bars, tampered, gated=True, stopped=False)
    assert np.array_equal(base[: t + 1], after[: t + 1])


def test_the_gate_only_removes_exposure_it_never_adds():
    bars = _synthetic()
    rng = np.random.default_rng(6)
    vol = rng.lognormal(8.0, 0.5, len(bars))
    parent, _ = A.build_positions(bars, vol, gated=False, stopped=False)
    gated, _ = A.build_positions(bars, vol, gated=True, stopped=False)
    assert np.all((gated == 0) | (gated == parent))


# --------------------------------------------------------------------------
# 2. The floor
# --------------------------------------------------------------------------


def test_var_trials_comes_from_the_null_and_not_from_the_cells(payload):
    """D219's amendment, applied. Estimating var_trials from the eight cells puts
    the floor at ~+4.9 annualised because C_stop's -3.17 is a REAL effect. The
    simulated null IS the null distribution and its variance is the right estimate."""
    from backtest_framework.validation.dsr import expected_max_sharpe

    ppy = 365.0 * 96
    cells = [r["net_sharpe"] / math.sqrt(ppy) for r in payload["rows"]]
    from_cells = expected_max_sharpe(
        A.VERDICT_COUNT, float(np.var(cells, ddof=1))
    ) * math.sqrt(ppy)
    published = [
        r["floor_verdict"] for r in payload["rows"] if r["floor_verdict"] == r["floor_verdict"]
    ]
    assert from_cells > 4.0, "the cell-based floor is meant to be absurd"
    assert max(published) < 1.5, "the published floor should come from the null"


def test_the_gate_clears_selectivity_and_fails_the_verdict_floor(payload):
    """The finding, in both halves. If either stops being true the write-up is wrong."""
    gates = [r for r in payload["rows"] if r["cell"] == "B_gate"]
    assert len(gates) == 2
    for r in gates:
        assert r["H_selectivity"] is True, r["symbol"]
        assert r["P_beats_parent"] is True, r["symbol"]
        assert r["G_clears_verdict_floor"] is False, r["symbol"]
    eth = next(r for r in gates if r["symbol"] == "ETHUSDT")
    assert eth["G_clears_fresh_floor"] is True, "ETH clears the fresh floor — D214's pattern"


def test_there_are_no_survivors_but_the_near_miss_is_recorded(payload):
    v = payload["verdict"]
    assert v["survivors"] == []
    assert set(v["clear_H_and_P_but_not_G"]) == {"B_gate/BTCUSDT", "B_gate/ETHUSDT"}


# --------------------------------------------------------------------------
# 3. The factorial and the interaction
# --------------------------------------------------------------------------


def test_the_interaction_is_negative_on_both_symbols(payload):
    """D223's census predicted it: the gate selects into loud markets, loud markets
    revert, and a trailing stop in a reverting market is a whipsaw generator."""
    assert payload["verdict"]["interaction_negative_on_both"] is True
    for sym, x in payload["verdict"]["interactions"].items():
        assert x < -1.0, sym


def test_the_stop_exits_almost_every_trade(payload):
    for r in payload["rows"]:
        if not r["stopped"]:
            continue
        assert r["stop_exits"] / r["n_trades"] > 0.90, r["cell"]
        assert r["median_hold_bars"] < 10


def test_the_factorial_is_the_four_declared_cells(payload):
    assert [c[0] for c in A.CELLS] == [
        "A_parent",
        "B_gate",
        "C_stop",
        "D_gate_and_stop",
    ]
    assert len(payload["rows"]) == 8  # 4 cells x 2 symbols


def test_the_declared_parameters_are_the_ones_used(payload):
    c = payload["config"]
    assert (c["length"], c["signal"]) == (136, 36)
    assert c["atr_window"] == 56 and c["atr_multiple"] == 2.0
    assert c["vol_window"] == 200
    assert c["mde_sharpe"] == 0.18


# --------------------------------------------------------------------------
# 4. The page
# --------------------------------------------------------------------------


def test_the_published_table_is_the_artifact(payload, page):
    for r in payload["rows"]:
        assert f"{r['net_sharpe']:+.3f}" in page, f"{r['symbol']}/{r['cell']}"


def test_the_page_records_the_floor_provenance(page):
    assert "simulated null" in page
    assert "+4.9" in page


def test_report_only_reproduces_the_page_exactly(payload):
    """`--report-only` re-renders the committed page, character for character.

    NOT byte for byte, and the difference is the point. `.gitattributes` (09855a0) pins tracked
    text to LF, so a clone checks this page out with LF while the author's worktree — which
    predates that file — still holds CRLF. `read_text` normalises both to `\\n`, which is what
    `render` emits, so the assertion tests the RENDERER and not the checkout. Measured on a real
    clone on 2026-09-16: the previous byte comparison, which wrote the page out and restored it,
    failed here on all three of these pages for that reason alone.

    Reading instead of writing also means an interrupted run can no longer leave a tracked
    document rewritten on disk.
    """
    assert A.render(payload) == PAGE.read_text(encoding="utf-8")
