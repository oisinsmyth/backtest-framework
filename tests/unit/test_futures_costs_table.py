"""Gates on `data/futures_costs.json` and on the `futures_round_trip` config seam (D591).

TWO THINGS ARE GATED HERE AND THEY ARE DIFFERENT.

1. THE TABLE IS WHAT ITS BUILDER PRODUCES. `scripts/futures_cost_table.py` copies every
   value out of a committed artefact or a named runner literal; the file in `data/` is
   worthless as evidence unless rebuilding it from today's inputs gives back the same bytes.
   That is a one-line check and it is the whole reason the builder carries no timestamp.

2. THE CONFIG SEAM STILL VALIDATES EVERY CONFIG IT VALIDATED BEFORE. `config/cost_stack.py`
   says a key missing from `BRICK_KEYS` "turns a working config into a raise", and that
   176,592 stored trial configs must keep validating. Adding a ninth brick type is exactly
   the edit that could break the other eight, and four of those rows are exercised by nothing
   else in the repository.

`tests/golden/test_futures_costs_ledger.py` holds the money arithmetic and the pre-edit
`BRICK_KEYS` snapshot; this file holds the structure and the seam.
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from backtest_framework.config.cost_stack import (
    BRICK_KEYS,
    StackDataContext,
    _brick_registry,
    build_cost_stack,
    validate_stack_config,
)
from backtest_framework.config.errors import ConfigError
from backtest_framework.costs.futures_bricks import (
    FuturesCommission,
    FuturesRoundTrip,
    TickCrossing,
    load_cost_table,
)
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.instruments.future import Future

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "data" / "futures_costs.json"

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)


def _builder():
    """Exec the builder by explicit path — `scripts/` is not a package (D546)."""
    spec = importlib.util.spec_from_file_location(
        "futures_cost_table", REPO / "scripts" / "futures_cost_table.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["futures_cost_table"] = module
    spec.loader.exec_module(module)
    return module


def _context() -> StackDataContext:
    return StackDataContext(
        bars_by_symbol={}, volumes_by_symbol={}, actions=CorporateActions({}, {})
    )


# ------------------------------------------------------------------ 1. the table is its build


def test_the_committed_table_is_byte_for_byte_what_the_builder_produces():
    """Rebuild from today's artefacts and compare the bytes. If this fails, either an input
    moved (and the table is stale) or someone edited the JSON by hand (and it is not
    evidence any more). Both are worth stopping for."""
    builder = _builder()
    rebuilt = builder._render(builder.build(builder.Sources()))
    assert hashlib.sha256(rebuilt.encode("utf-8")).hexdigest() == hashlib.sha256(
        TABLE.read_bytes()
    ).hexdigest()


def test_the_builders_selftest_passes():
    builder = _builder()
    src = builder.Sources()
    assert builder.selftest(src, builder.build(src)) == 0


def test_the_builder_refuses_a_value_it_cannot_find():
    """The refusals are the point: a builder that falls back writes a plausible number."""
    builder = _builder()
    src = builder.Sources()
    with pytest.raises(builder.BuildError, match="no key"):
        src.at("d508", "per_root.NOPE.execution_hours.effective_mean_ticks")
    with pytest.raises(builder.BuildError, match="no module-level assignment"):
        src.literal("d555", "NOT_A_LITERAL")
    with pytest.raises(builder.BuildError, match="not a number"):
        src.cite("d508", "purpose", "D508")
    with pytest.raises(builder.BuildError, match="no contract specification"):
        builder.spec_for(src, "NOPE")


def test_the_cross_check_between_the_two_records_of_minimum_size_can_fail():
    """A guard that cannot fire is worse than none: break what the assertion reads.

    d556's `min_size` map and run_d555's `MICRO_OF` literal are two records of one fact. The
    builder raises when they disagree — this perturbs the SCALAR the check compares, not its
    label, and asserts the build goes red.
    """
    builder = _builder()
    src = builder.Sources()
    src.json["d556"]["dollar_book"]["min_size"]["ES"] = "ES"  # the micro, un-named
    with pytest.raises(builder.BuildError, match=r"\[XCHK\] ES"):
        builder.build(src)


def test_the_builder_reads_runner_literals_rather_than_carrying_copies():
    """`COST_USD = 4.21` and `COMMISSION_RT` come out of the runners through `ast`."""
    builder = _builder()
    src = builder.Sources()
    assert src.literal("d531", "COST_USD") == 4.21
    assert src.literal("d555", "COMMISSION_RT") == {"micro": 3.0, "full": 6.0}
    assert src.literal("d533", "COST") == {
        "CL": 4.00, "GC": 5.00, "SI": 8.00, "NG": 5.00, "ES": 4.25, "NQ": 4.21
    }
    # run_d535's COST is `dict(D533.COST, HG=5.0, ...)` — composed, not a literal.
    d535 = src.literal("d535", "COST")
    assert d535["CL"] == 4.00 and d535["HG"] == 5.0 and d535["6E"] == 5.0 and d535["ZC"] == 10.0


# ------------------------------------------------------------------ the table's shape


def test_every_value_in_the_table_carries_a_provenance():
    """No bare number anywhere: artefact + key, or source + literal, or a derivation."""
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    seen = 0

    def walk(node, path):
        nonlocal seen
        if isinstance(node, dict):
            if "value" in node and "provenance" in node:
                seen += 1
                prov = node["provenance"]
                assert "decision" in prov, path
                assert (
                    ("artefact" in prov and "key" in prov)
                    or ("source" in prov and "literal" in prov)
                    or ("derivation" in prov and "inputs" in prov)
                ), f"{path}: provenance names no source"
                assert isinstance(node["value"], float), path
                assert "measured" in node, path
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(table["roots"], "roots")
    # 289 cited values across the 47 size entries at the build of 2026-09-21. A floor rather
    # than a pin: the bytes are gated exactly by the rebuild check above, and this one exists
    # to catch a walk that silently stops descending.
    assert seen >= 289, f"only {seen} cited values; the table lost most of its content"


def test_every_measured_crossing_line_carries_its_window():
    """A census measured on 2025-2026 and applied to 2016 is an extrapolation; the window
    is how a caller can see that it is making one (D507/D508 say so themselves)."""
    table = load_cost_table()
    for root, entry in table["roots"].items():
        for size in ("micro", "full"):
            if size not in entry:
                continue
            for name, line in entry[size]["crossing_ticks_rt"].items():
                if line["measured"]:
                    assert line.get("window"), f"{root}.{size}.{name} has no window"
                    assert len(line["window"]) == 2
                else:
                    assert name == "d556_one_tick"
                    assert "window" not in line, "a convention measured nothing"


def test_the_default_line_is_never_a_quoted_spread():
    """d507/d510 are FLOORS. The default serves effective crossing or the convention."""
    table = load_cost_table()
    quoted = {n for n, meta in table["lines"].items() if meta["kind"] == "quoted"}
    for root, entry in table["roots"].items():
        for size in ("micro", "full"):
            if size in entry:
                assert entry[size]["default_line"] not in quoted, f"{root}.{size}"


def test_the_default_is_d508_exec_exactly_where_d508_measured_the_contract():
    table = load_cost_table()
    for root, entry in table["roots"].items():
        for size in ("micro", "full"):
            if size not in entry:
                continue
            e = entry[size]
            want = "d508_exec" if "d508_exec" in e["crossing_ticks_rt"] else "d556_one_tick"
            assert e["default_line"] == want, f"{root}.{size}"


def test_tick_usd_agrees_with_the_instrument_the_specs_file_builds():
    """The table's geometry and `Future.from_specs` must not fork (R16's shape).

    **This is the test that made D609 a two-sided change.** Until D609 both sides read the
    definition snapshot's `tick_usd`, so they agreed on 1250.0 for ZC and this passed while
    both were 100x wrong; and correcting either side alone would have turned it red. Both were
    moved onto `tick_usd_full_contract` in the same record, which is why it is still green and
    why green now means something it did not mean before.
    """
    table = load_cost_table()
    for root, entry in table["roots"].items():
        for size in ("micro", "full"):
            if size not in entry:
                continue
            e = entry[size]
            spec = Future.from_specs(e["symbol"])
            assert spec.tick_usd == e["tick_usd"], f"{root}.{size}"
            assert spec.tick_points == e["tick_points"], f"{root}.{size}"
            assert spec.usd_per_point == pytest.approx(e["usd_per_point"], rel=1e-12)


def test_the_seven_corrected_roots_carry_the_dollar_value_and_not_the_raw_formula():
    """The agreement above would also hold at 1250.0, so the values are pinned outright."""
    table = load_cost_table()
    for symbol, dollars, raw in [("ZC", 12.5, 1250.0), ("ZS", 12.5, 1250.0),
                                 ("ZW", 12.5, 1250.0), ("LE", 10.0, 1000.0),
                                 ("HE", 10.0, 1000.0), ("ZL", 6.000000000000001,
                                                        600.0000000000001),
                                 ("SR3", 6.25, 6.25)]:
        e = table["roots"][symbol]["full"]
        assert e["tick_usd"] == dollars, symbol
        assert e["tick_usd_raw_formula"] == raw, symbol
        assert Future.from_specs(symbol).tick_usd == dollars, symbol
    assert table["roots"]["ZC"]["full"]["specs_provenance"]["key"].endswith(
        "(tick_price_units, tick_usd_full_contract)"
    )


def test_the_runtime_path_charges_the_corrected_tick():
    """`futures_bricks.py:253` builds a `Future` out of this table, so `FuturesRoundTrip` is
    what a study would actually be charged. It was 1250.0 for ZC until D609."""
    from backtest_framework.costs.futures_bricks import FuturesRoundTrip

    assert FuturesRoundTrip.from_table("ZC").instrument.tick_usd == 12.5
    assert FuturesRoundTrip.from_table("ZC").instrument.usd_per_point == 50.0
    assert FuturesRoundTrip.from_table("SR3").instrument.tick_usd == 6.25
    assert FuturesRoundTrip.from_table("SR3").instrument.usd_per_point == 2500.0


def test_d555s_committed_dollar_book_already_held_the_corrected_multipliers():
    """The claim that no published number moved, made checkable.

    `run_d555` read the BREADTH meta for `usd_per_point`, not the definition file, so its
    dollar book was right while the spec file was wrong. Its bytes are asserted unchanged by
    D609 — if the correction had moved a published result, this is where it would show.
    """
    import json
    from pathlib import Path

    from backtest_framework.validation.frozen import sha256_file

    path = Path(__file__).resolve().parents[2] / "data" / "d555_tsmom_replication.json"
    upp = json.loads(path.read_text(encoding="utf-8"))["dollar_book"]["usd_per_point"]
    for root, want in [("ZC", 50.0), ("ZS", 50.0), ("ZW", 50.0), ("ZL", 600.0000000000001),
                       ("LE", 400.0), ("HE", 400.0), ("SR3", 2500.0)]:
        assert upp[root] == want, root
        assert Future.from_specs(root).usd_per_point == want, root
    # LF-pinned before hashing (D550/D551): this is a tracked TEXT artefact and `.gitattributes`
    # pins `eol=lf` in the index while the author's worktree carries CRLF, so the raw digest is
    # a fact about the checkout rather than about the file.
    assert sha256_file(path, text_normalise=True) == (
        "7811e322bc6e6cb15d3903e2b3c38721a76b265f448710eb014b47e81906fc61"
    )


def test_every_traded_symbol_is_indexed_exactly_once():
    table = load_cost_table()
    symbols = [
        table["roots"][r][s]["symbol"]
        for r in table["roots"]
        for s in ("micro", "full")
        if s in table["roots"][r]
    ]
    assert len(symbols) == len(set(symbols)) == len(table["by_symbol"]) == 47
    for symbol, (root, size) in table["by_symbol"].items():
        assert table["roots"][root][size]["symbol"] == symbol


def test_the_eleven_roots_with_a_micro_are_the_ones_the_runners_size_at_a_micro():
    table = load_cost_table()
    micro_roots = {r for r, e in table["roots"].items() if "micro" in e}
    assert micro_roots == {"ES", "NQ", "RTY", "YM", "CL", "GC", "6E", "BTC", "SI", "NG", "HG"}
    for root, entry in table["roots"].items():
        assert entry["min_size"] == ("micro" if root in micro_roots else "full")
        if root not in micro_roots:
            assert "no_micro_because" in entry


def test_the_table_records_the_disagreements_it_found():
    disagreements = load_cost_table()["disagreements"]
    whats = [d["what"] for d in disagreements]
    assert any("full-size commission" in w for w in whats)
    assert any("GC" in w for w in whats) and any("NG" in w for w in whats)
    assert any("D527" in w for w in whats) and any("D465" in w for w in whats)
    for d in disagreements:
        assert len(d["values"]) == 2 and d["resolution"]


# ------------------------------------------------------------------ 2. the config seam


FUTURES_CONFIG = {
    "trade_bricks": [{"type": "futures_round_trip", "root": "MES"}],
    "carry_bricks": [],
    "portfolio_carry_bricks": [],
    "event_flow_bricks": [],
}


def test_the_key_table_still_covers_every_registered_type():
    registered = set(_brick_registry(_context())._factories)
    assert registered == set(BRICK_KEYS)
    assert "futures_round_trip" in registered


@pytest.mark.parametrize(
    "brick",
    [
        # Every shape the eight pre-D591 factories accept. If adding a ninth row broke one of
        # these, a stored, published trial config would now raise.
        {"type": "percent_spread", "bps": 1.0},
        {"type": "borrow_fee", "annual_rate": 0.02},
        {"type": "margin_interest", "annual_rate": 0.06},
        {"type": "flat_commission", "amount": 1.0},
        {"type": "flat_rate_carry", "annual_rate": 0.01},
        {"type": "ibkr_commission"},
        {"type": "ibkr_commission", "per_share": 0.005, "min_per_order": 1.0,
         "max_pct_of_trade_value": 0.01},
        {"type": "sqrt_impact", "calibration": "full_sample", "coefficient": 1.0},
        {"type": "sqrt_impact", "coefficient": 1.0},  # pre-D187 shape, 2,170 trials
        {"type": "sqrt_impact", "coefficient": 1.0, "volume_units": "shares"},
        {"type": "dividend_flow", "source": "snapshot_declared"},
    ],
)
def test_every_legacy_brick_config_still_validates(brick):
    slot = "event_flow_bricks" if brick["type"] == "dividend_flow" else "trade_bricks"
    validate_stack_config({**FUTURES_CONFIG, slot: [brick]})


@pytest.mark.parametrize(
    "brick",
    [
        {"type": "futures_round_trip", "root": "MES"},
        {"type": "futures_round_trip", "root": "ES", "line": "d465"},
        {"type": "futures_round_trip", "commission_rt_usd": 3.0, "crossing_ticks_rt": 1.0},
    ],
)
def test_every_futures_shape_the_factory_accepts_survives_the_key_check(brick):
    validate_stack_config({**FUTURES_CONFIG, "trade_bricks": [brick]})


def test_a_config_built_futures_stack_matches_the_hand_built_one():
    """D102: the dict a study LOGS is the dict its stack is BUILT from."""
    built = build_cost_stack(FUTURES_CONFIG, _context())
    hand = FuturesRoundTrip.from_table("MES")
    assert built.trade_cost(MES, 1.0, 5000.0) == hand.cost(MES, 1.0, 5000.0)
    assert built.trade_cost(MES, 1.0, 5000.0) > 0.0

    explicit = build_cost_stack(
        {
            **FUTURES_CONFIG,
            "trade_bricks": [
                {"type": "futures_round_trip", "commission_rt_usd": 3.0, "crossing_ticks_rt": 1.0}
            ],
        },
        _context(),
    )
    pair = (FuturesCommission(3.0), TickCrossing(1.0))
    assert explicit.trade_cost(MES, 2.0, 5000.0) == sum(b.cost(MES, 2.0, 5000.0) for b in pair)


def test_the_config_records_which_line_it_charged():
    brick = build_cost_stack(FUTURES_CONFIG, _context()).trade_bricks[0]
    assert isinstance(brick, FuturesRoundTrip)
    assert brick.root == "ES" and brick.size == "micro" and brick.line == "d508_exec"
    assert brick.window == ("2025-09-11", "2026-09-11")


@pytest.mark.parametrize(
    ("brick", "match"),
    [
        ({"type": "futures_round_trip", "root": "MES", "commission_rt_usd": 3.0}, "both"),
        ({"type": "futures_round_trip", "commission_rt_usd": 3.0}, "crossing_ticks_rt"),
        ({"type": "futures_round_trip", "crossing_ticks_rt": 1.0}, "commission_rt_usd"),
        ({"type": "futures_round_trip"}, "commission_rt_usd"),
        ({"type": "futures_round_trip", "line": "d465"}, "meaningless without 'root'"),
        ({"type": "futures_round_trip", "root": "NOPE"}, "no futures cost line"),
        ({"type": "futures_round_trip", "root": "ZN", "line": "d465"}, "no crossing line"),
        ({"type": "futures_round_trip", "root": 7}, "must be a string"),
        ({"type": "futures_round_trip", "root": "MES", "line": 7}, "must be a string"),
        ({"type": "futures_round_trip", "commission_rt_usd": "free",
          "crossing_ticks_rt": 1.0}, "numeric"),
        # The silent surface D102 closed: a typo on a key must raise, not build a default.
        ({"type": "futures_round_trip", "root": "MES", "lien": "d465"}, "unknown key"),
        ({"type": "futures_round_trip", "commission_rt_usd": 3.0, "crossing_tikcs_rt": 1.0},
         "unknown key"),
    ],
)
def test_an_invalid_futures_config_fails_loudly_naming_the_problem(brick, match):
    with pytest.raises(ConfigError, match=match):
        build_cost_stack({**FUTURES_CONFIG, "trade_bricks": [brick]}, _context())


def test_a_negative_declared_cost_reaches_the_bricks_own_guard():
    with pytest.raises(ValueError, match="negative"):
        build_cost_stack(
            {
                **FUTURES_CONFIG,
                "trade_bricks": [
                    {"type": "futures_round_trip", "commission_rt_usd": -1.0,
                     "crossing_ticks_rt": 1.0}
                ],
            },
            _context(),
        )
