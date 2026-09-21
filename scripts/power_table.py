"""D588 — render a POWER.md / TRACK_MAP power table, or self-test the power module.

    uv run python scripts/power_table.py --spec spec.json --out results/x/POWER.md
    uv run python scripts/power_table.py --selftest

The spec is a JSON LIST of objects, one per row, with the keys of
`backtest_framework.validation.power.power_row`:

    [
      {"stage": "A: P1 rebalance", "test": "Flow (all days, NG+CL)", "track": "1",
       "n": 5000, "m": 1.0, "rho": 0.0, "plausible_effect": 0.05,
       "note": "ledger 9A.1 planning row"},
      {"stage": "A: P1 rebalance", "test": "Price (trade days)", "track": "1",
       "n": 1500, "m": 1.0, "rho": 0.0, "sigma": 1.0, "plausible_effect": 0.06,
       "note": "sigma units; plausible effect = round-trip cost"}
    ]

`sigma` absent or null selects correlation units; a positive `sigma` selects price
units and the SE/MDE columns come back in multiples of sigma. An unknown key is a
hard error rather than a silent drop — a misspelled `plausible_efect` would
otherwise produce an unclassified row that `validate_track_map` then refuses for a
reason the writer never intended.

This script computes no strategy return and reads no market fixture.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402

from backtest_framework.validation.power import (  # noqa: E402
    PowerRow,
    design_effect,
    forward_evaluation_days,
    icc_from_clusters,
    mde,
    mde_80,
    n_eff,
    n_eff_cross_series,
    n_eff_from_clusters,
    power_class,
    power_row,
    se_correlation,
    se_mean,
    track3_route,
    validate_track_map,
    write_power_md,
)

SPEC = "D588"

# Checked against the RENDERED document before a single byte is written (the pattern
# in scripts/stage0_d581_gamma_close.py:36). A table missing its provenance header or
# any of its declared columns is not a power table, and writing it would leave a file
# on disk that looks authoritative and is not.
REQUIRED_OUTPUTS = (
    "**Generated:**",
    "recomputed on real data before each",
    "| Stage |",
    "n_eff",
    "MDE (t = 2)",
    "MDE (80%)",
    "Plausible effect",
    "Power class",
    "Adoption by significance",
)

ALLOWED_KEYS = frozenset(inspect.signature(power_row).parameters)


def expect_raise(fn, what, exc=ValueError, log=print):
    """The house self-test idiom (scripts/stage0_d581_gamma_close.py:39): a guard that
    cannot fire is worse than no guard, so every guard is shown failing."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:78]}")
        return True
    raise AssertionError(f"guard did not raise on {what}")


def guard_outputs(text: str) -> None:
    missing = [token for token in REQUIRED_OUTPUTS if token not in text]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing from the rendered table: {missing}")


# ----------------------------------------------------------------------------- render


def rows_from_spec(spec: list[dict]) -> list[PowerRow]:
    if not isinstance(spec, list):
        raise ValueError(f"spec must be a JSON list of row objects, got {type(spec).__name__}")
    rows = []
    for index, item in enumerate(spec):
        if not isinstance(item, dict):
            raise ValueError(f"spec row {index} is not an object: {item!r}")
        unknown = sorted(set(item) - ALLOWED_KEYS)
        if unknown:
            raise ValueError(
                f"spec row {index} has unknown key(s) {unknown}; allowed: {sorted(ALLOWED_KEYS)}"
            )
        rows.append(power_row(**item))
    return rows


def render(spec_path: Path, out_path: Path, date: str | None = None) -> Path:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    rows = rows_from_spec(spec)
    validate_track_map(rows)
    # Render once into a scratch file, guard the TEXT, then write the real one. The
    # guard has to read what the writer actually produced, not what it was asked for.
    scratch = out_path.parent / (out_path.name + ".guard.tmp")
    write_power_md(rows, scratch, date=date)
    text = scratch.read_text(encoding="utf-8")
    guard_outputs(text)
    scratch.unlink()
    written = write_power_md(rows, out_path, date=date)
    print(f"[{SPEC}] wrote {written} ({len(rows)} rows)")
    return written


# ----------------------------------------------------------------------------- selftest


def _close(a: float, b: float, tol: float = 1e-12) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tol)


def _check(name: str, condition: bool, detail: str, log=print) -> None:
    if not condition:
        raise AssertionError(f"{name} FAILED: {detail}")
    log(f"  [ok] {name}: {detail}")


def selftest(log=print) -> None:  # noqa: C901
    log(f"[{SPEC}] power module self-test -- the deposit docs' named unit tests, and the guards\n")

    # -- ledger unit test 51 ------------------------------------------------------
    deff = design_effect(10.0, 0.1)
    _check("test 51 design effect", _close(deff, 1.9), f"m=10, rho=0.1 -> deff={deff}", log)
    _check(
        "test 51 n_eff",
        _close(n_eff(1900, 10.0, 0.1), 1000.0),
        f"n=1,900 -> n_eff={n_eff(1900, 10.0, 0.1)} = 1,900/1.9",
        log,
    )

    # -- ledger unit test 52 ------------------------------------------------------
    se = se_correlation(2500.0)
    _check("test 52 SE", _close(se, 0.02), f"n_eff=2,500 -> SE={se}", log)
    _check("test 52 MDE_t2", _close(mde(se), 0.04), f"MDE_t2={mde(se)}", log)
    _check("test 52 MDE_80", _close(mde_80(se), 0.056), f"MDE_80={mde_80(se)}", log)

    # -- ledger unit test 53 ------------------------------------------------------
    under = power_row(
        stage="G: P9 non-US ETPs",
        test="Marginal flow",
        n=240,
        m=1.0,
        rho=0.0,
        track="2",
        plausible_effect=0.05,
        note="ledger 9A.1: MDE ~0.13 against a 0.05 plausible effect",
    )
    _check(
        "test 53 class",
        under.power_class == "underpowered",
        f"MDE_t2={under.mde_t2:.4f} > plausible 0.05 -> {under.power_class}",
        log,
    )
    _check(
        "test 53 adoption blocked",
        under.adoption_by_significance_blocked is True,
        "adoption_by_significance_blocked is True",
        log,
    )
    ok = power_row(
        stage="A: P1 rebalance",
        test="Flow (all days)",
        n=5000,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=0.05,
    )
    _check(
        "test 53 converse",
        ok.power_class == "individually_testable"
        and ok.adoption_by_significance_blocked is False,
        f"MDE_t2={ok.mde_t2:.4f} <= 0.05 -> {ok.power_class}, adoption permitted",
        log,
    )

    # -- ledger unit test 59 ------------------------------------------------------
    plan_a = forward_evaluation_days(0.1, 2)
    _check(
        "test 59 forward route",
        _close(plan_a.n_needed, 400.0)
        and plan_a.evaluation_days is not None
        and _close(plan_a.evaluation_days, 200.0)
        and plan_a.route == "forward",
        f"plausible 0.1, 2 instruments -> {plan_a}",
        log,
    )
    plan_b = forward_evaluation_days(0.05, 2)
    _check(
        "test 59 cap route",
        _close(plan_b.n_needed, 1600.0)
        and plan_b.evaluation_days is None
        and plan_b.route == "9B",
        f"plausible 0.05, 2 instruments -> {plan_b} (800 days > 500 cap)",
        log,
    )

    # -- ledger unit test 62 ------------------------------------------------------
    low, high = track3_route(0.08), track3_route(0.15)
    _check(
        "test 62 SE and MDE",
        _close(low.se, 1.0 / math.sqrt(300.0)) and _close(low.mde, 2.0 / math.sqrt(300.0)),
        f"N=300 -> SE={low.se:.6f} sigma, MDE={low.mde:.6f} sigma",
        log,
    )
    _check(
        "test 62 below",
        low.route == "combined_evidence",
        f"edge 0.08 sigma < {low.mde:.4f} -> {low.route}",
        log,
    )
    _check(
        "test 62 at or above",
        high.route == "efficacy_n300",
        f"edge 0.15 sigma >= {high.mde:.4f} -> {high.route}",
        log,
    )

    # -- ledger unit test 63 ------------------------------------------------------
    no_statement = power_row(
        stage="E: P2 netting",
        test="Weekly swap-dealer fit",
        n=520,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=None,
    )
    _check(
        "test 63 clean table passes",
        validate_track_map([ok, under]) is None,
        "a complete two-row table validates",
        log,
    )
    expect_raise(
        lambda: validate_track_map([ok, no_statement]),
        "test 63: a row with no plausible-effect statement",
        log=log,
    )

    # -- ICC and the clustered route ---------------------------------------------
    rng = np.random.default_rng(588)
    k_clusters, per_cluster, true_icc = 300, 20, 0.5
    effects = rng.normal(0.0, 1.0, k_clusters)
    values = np.repeat(effects, per_cluster) + rng.normal(0.0, 1.0, k_clusters * per_cluster)
    ids = np.repeat(np.arange(k_clusters), per_cluster)
    icc = icc_from_clusters(values, ids)
    _check(
        "ICC recovery",
        abs(icc - true_icc) < 0.05,
        f"{k_clusters} clusters x {per_cluster}: ICC={icc:.4f} vs true {true_icc}",
        log,
    )
    clustered = n_eff_from_clusters(values, ids)
    _check(
        "n_eff from clusters",
        _close(clustered, (k_clusters * per_cluster) / (1.0 + (per_cluster - 1) * icc), 1e-9),
        f"N={k_clusters * per_cluster} -> n_eff={clustered:.1f} at m={per_cluster}",
        log,
    )

    # -- cross-series, against the script it was ported from ----------------------
    panel, start = _synthetic_panel(seed=588)
    ported = n_eff_cross_series(panel, start, min_overlap=50)
    original = _script_effective_instruments(panel, start, min_overlap=50)
    _check(
        "cross-series parity",
        _close(ported, original, 1e-12),
        f"power.n_eff_cross_series={ported!r} == ragged_panel.effective_instruments={original!r}",
        log,
    )

    # -- every guard, shown raising ----------------------------------------------
    log("\n  guards (each must RAISE):")
    expect_raise(lambda: design_effect(0.5, 0.1), "m < 1", log=log)
    expect_raise(lambda: design_effect(10.0, 1.5), "rho > 1", log=log)
    expect_raise(lambda: design_effect(10.0, -0.5), "rho below -1/(m-1)", log=log)
    expect_raise(lambda: n_eff(0, 2.0, 0.1), "n < 1", log=log)
    expect_raise(lambda: se_correlation(1.5), "n_eff < 2 (correlation)", log=log)
    expect_raise(lambda: se_mean(0.01, 1.0), "n_eff < 2 (price)", log=log)
    expect_raise(lambda: se_mean(0.0, 100.0), "sigma <= 0", log=log)
    expect_raise(lambda: mde(0.0), "se <= 0", log=log)
    expect_raise(lambda: mde_80(-1.0), "se < 0", log=log)
    expect_raise(lambda: power_class(0.04, 0.0), "plausible effect <= 0", log=log)
    expect_raise(lambda: forward_evaluation_days(0.0, 2), "plausible effect 0", log=log)
    expect_raise(lambda: forward_evaluation_days(0.1, 0), "zero instruments", log=log)
    expect_raise(lambda: track3_route(0.0), "edge <= 0", log=log)
    expect_raise(lambda: icc_from_clusters([1.0, 2.0], [0, 0]), "fewer than 2 clusters", log=log)
    expect_raise(
        lambda: icc_from_clusters([1.0, 2.0], [0, 1]), "no within-cluster degrees of freedom",
        log=log,
    )
    expect_raise(
        lambda: icc_from_clusters([[1.0, 2.0], [], [5.0, 6.0]]),
        "an empty cluster (grouped form)",
        log=log,
    )
    expect_raise(lambda: n_eff(1000, 5.0, -0.25), "a zero design effect", log=log)
    expect_raise(
        lambda: icc_from_clusters([1.0, 1.0, 1.0, 1.0], [0, 0, 1, 1]), "zero total variance",
        log=log,
    )
    expect_raise(lambda: icc_from_clusters([1.0, 2.0, 3.0], [0, 1]), "length mismatch", log=log)
    expect_raise(lambda: validate_track_map([]), "an empty TRACK_MAP", log=log)
    expect_raise(
        lambda: rows_from_spec([{"stage": "A", "test": "t", "track": "1", "n": 10, "m": 1.0,
                                 "rho": 0.0, "plausible_efect": 0.05}]),
        "a misspelled spec key",
        log=log,
    )

    # -- the REQUIRED_OUTPUTS guard itself, shown raising -------------------------
    expect_raise(
        lambda: guard_outputs("# POWER\n\nnothing here\n"),
        "REQUIRED_OUTPUTS on a stripped document",
        exc=AssertionError,
        log=log,
    )
    good = _render_to_string([ok, under])
    guard_outputs(good)
    _check(
        "REQUIRED_OUTPUTS passes a real table",
        True,
        f"{len(REQUIRED_OUTPUTS)} tokens present in {len(good)} rendered characters",
        log,
    )

    log(f"\n[{SPEC}] self-test PASSED — 6 named ledger tests, ICC recovery, cross-series "
        f"parity, and 22 guards each shown raising.")


# ----------------------------------------------------------------------------- helpers


def _render_to_string(rows: list[PowerRow]) -> str:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = write_power_md(rows, Path(tmp) / "POWER.md", date="2026-09-21")
        return path.read_text(encoding="utf-8")


def _load_script(name: str, filename: str):
    """House pattern for reaching a research script (scripts/a1_er_stage0.py:99)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _synthetic_panel(seed: int = 588, n: int = 6, T: int = 400):
    """A ragged panel with correlated series and staggered live windows, built with the
    real `RaggedPanel` so the parity check compares the two functions and not two
    different objects."""
    rp = _load_script("ragged_panel_d588", "ragged_panel.py")
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0, 0.01, T)
    log_returns = np.array([0.6 * common + 0.8 * rng.normal(0.0, 0.01, T) for _ in range(n)])
    live = np.ones((n, T), dtype=bool)
    for i in range(n):
        live[i, : i * 30] = False  # staggered starts: pairwise overlap varies
    log_returns[~live] = 0.0
    closes = np.where(live, 100.0 * np.exp(np.cumsum(log_returns, axis=1)), np.nan)
    symbols = [f"S{i}" for i in range(n)]
    dates = [f"d{t:04d}" for t in range(T)]
    panel = rp.RaggedPanel(
        symbols=symbols,
        dates=dates,
        closes=closes,
        log_returns=log_returns,
        total_log_returns=log_returns.copy(),
        cost_fraction=np.zeros((n, T)),
        live=live,
        index_of={s: i for i, s in enumerate(symbols)},
    )
    return panel, 0


def _script_effective_instruments(panel, start: int, min_overlap: int) -> float:
    rp = _load_script("ragged_panel_d588", "ragged_panel.py")
    return rp.effective_instruments(panel, start, min_overlap=min_overlap)


# ----------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", type=Path, help="JSON list of power_row inputs")
    parser.add_argument("--out", type=Path, help="path to write the rendered table to")
    parser.add_argument("--date", type=str, default=None, help="pin the header date (ISO)")
    parser.add_argument("--selftest", action="store_true", help="run the named checks and guards")
    args = parser.parse_args(argv)

    if args.selftest:
        selftest()
        return 0
    if args.spec is None or args.out is None:
        parser.error("--spec and --out are both required unless --selftest is given")
    render(args.spec, args.out, date=args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
