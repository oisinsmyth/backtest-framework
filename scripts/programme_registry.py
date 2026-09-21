"""The programme α registry and trial counter, on the command line (D592).

    uv run python scripts/programme_registry.py --render     # seed + write JSON and the page
    uv run python scripts/programme_registry.py --count      # the programme trial count
    uv run python scripts/programme_registry.py --selftest   # every raise, proven to fire

WHAT THIS IS. The deposit's programme-level false-positive controls
(`SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8, `OPENING_AGENT_STATE_PREREG.md` §12A) put one
α registry, one trial counter and one haircut across every document in the programme.
`src/backtest_framework/validation/programme.py` is the library; this is its entry point.

`--render` is IDEMPOTENT and additive: it registers only the families that are missing, so
re-running it can never move a slot that is already allocated. It writes
`data/programme_registry.json` and `docs/results/PROGRAMME_REGISTRY.md` — the deposit's
`results/PROGRAMME_REGISTRY.md`, which has no home in this repository because there is no
root `results/` (D592).

`--selftest` is the part worth reading. CLAUDE.md: *"a self-test that cannot fail is worse
than none"*, so every guard below is proven to RAISE on the input it exists to refuse —
the eleventh slot without an amendment, a duplicate `trial_id`, an annualised Sharpe fed
to the per-period DSR, a programme count below the doc count, and unsorted dates. The
`expect_raise` idiom is `scripts/stage0_d581_gamma_close.py:39`.

No market data is read. No strategy return is computed. Nothing here is a result.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.episodes import (  # noqa: E402
    drop_best_days,
    drop_best_year,
    episode_checks,
    sessions_to_half_pnl,
    shared_period,
    symmetric_trim,
)
from backtest_framework.validation.programme import (  # noqa: E402
    DEFAULT_PAGE_PATH,
    DEFAULT_REGISTRY_PATH,
    N_SLOTS,
    SEALED_DATE,
    SLOT_ALPHA,
    Registry,
    TrialsCsv,
    haircut,
    programme_dsr,
    programme_trial_count,
    seed_registry,
)


def expect_raise(fn, what, exc=(ValueError, AssertionError, KeyError), log=print):
    """Run `fn` and require it to raise. The idiom of stage0_d581_gamma_close.py:39."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {str(e)[:96]}")
        return True
    raise AssertionError(f"guard did not raise on {what}")


# ----------------------------------------------------------------------------- --render


def render(registry_path: Path = DEFAULT_REGISTRY_PATH, page_path: Path = DEFAULT_PAGE_PATH):
    registry = seed_registry(registry_path)
    registry.save()
    page = registry.render_md(page_path, date=SEALED_DATE)
    print(f"programme registry: {len(registry)} of {N_SLOTS} slots allocated at "
          f"alpha = {SLOT_ALPHA} each, sealed {SEALED_DATE}")
    for family in registry:
        print(f"  slot {family.slot:>2}  {family.name:<22}  {family.doc}")
    free = registry.free_slots()
    print(f"  reserved: {list(free) if free else 'none'}")
    print(f"\nwrote {registry.path.relative_to(REPO)}")
    print(f"wrote {page.relative_to(REPO)}")
    return registry


# ------------------------------------------------------------------------------ --count


def count():
    result = programme_trial_count()
    print("PROGRAMME TRIAL COUNT")
    print(f"  ETF-fixture sqlite pool, distinct configs de-duplicated : "
          f"{result['etf_pool_distinct_configs']:>8,}")
    print(f"  other LIVE sqlite registries (breakout/crypto line)     : "
          f"{result['other_registries']:>8,}")
    print(f"  trials.csv rows (the deposit's own counter)             : "
          f"{result['trials_csv_rows']:>8,}")
    print(f"  TOTAL                                                   : {result['total']:>8,}")
    print("\nRULE\n  " + result["rule"].replace("; ", ";\n  "))
    return result


# --------------------------------------------------------------------------- --selftest


def selftest():  # noqa: C901
    print("D592 SELFTEST -- every guard proven to fire\n")
    ok = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # -- 1. the eleventh slot ------------------------------------------------------
        print("  [1] Registry: ten slots, then the eleventh")
        registry = Registry(path=tmp_path / "registry.json")
        for i in range(N_SLOTS):
            registry.register(f"family {i + 1}", "DOC.md")
        assert len(registry) == N_SLOTS, len(registry)
        assert registry.free_slots() == (), registry.free_slots()
        ok += expect_raise(
            lambda: registry.register("family 11", "DOC.md"), "an eleventh slot with no amendment"
        )
        eleventh = registry.register("family 11", "DOC.md", amendment="DOC.md v2.0 re-allocates")
        assert eleventh.slot == 11, eleventh.slot
        assert eleventh.amendment is not None
        ok += 1
        ok += expect_raise(
            lambda: registry.register("family 1", "DOC.md", amendment="x"),
            "re-registering an existing family",
        )
        # test 66: the promotion check uses alpha = 0.005
        assert registry.promotion_check("family 1", 0.004) is True
        assert registry.promotion_check("family 1", SLOT_ALPHA) is True
        assert registry.promotion_check("family 1", 0.006) is False
        ok += 1
        ok += expect_raise(
            lambda: registry.promotion_check("family 1", 2.8), "a t-statistic passed as a p-value"
        )
        ok += expect_raise(lambda: registry.promotion_check("nope", 0.001), "an unknown family")
        # an amendment offered while a slot is still free
        spare = Registry(path=tmp_path / "spare.json")
        spare.register("only", "DOC.md")
        ok += expect_raise(
            lambda: spare.register("second", "DOC.md", amendment="unnecessary"),
            "an amendment while slots remain free",
        )

        # -- 2. the trials.csv ---------------------------------------------------------
        print("\n  [2] TrialsCsv: append-only")
        log = TrialsCsv(tmp_path / "trials.csv")
        assert log.count() == 0
        log.append({"trial_id": "t1", "doc": "LETF", "family": "H1", "mean_net": 0.01})
        log.append({"trial_id": "t2", "doc": "LETF", "family": "H1", "cost_mult": 2.0})
        assert log.count() == 2, log.count()
        ok += 1
        ok += expect_raise(
            lambda: log.append({"trial_id": "t1", "doc": "LETF", "family": "H1"}),
            "a duplicate trial_id",
        )
        ok += expect_raise(
            lambda: log.append({"trial_id": "t3", "doc": "LETF", "family": "H1", "bogus": 1}),
            "an unknown column",
        )
        ok += expect_raise(
            lambda: log.append({"trial_id": "t3", "doc": "LETF"}), "a missing family"
        )
        assert log.count() == 2, "a refused append must not have written"
        ok += 1

        # -- 3. the DSR ----------------------------------------------------------------
        print("\n  [3] programme_dsr: units and pool ordering")
        both = programme_dsr(
            0.05, 2000, 0.0, 3.0, n_doc=100, n_programme=45_346, var_trials=0.0004
        )
        assert both["dsr_programme"] <= both["dsr_doc"], both
        print(f"    dsr_doc {both['dsr_doc']:.6f}  >=  dsr_programme "
              f"{both['dsr_programme']:.6f}   (SR0 rises with N)")
        ok += 1
        ok += expect_raise(
            lambda: programme_dsr(
                1.2699, 2000, 0.0, 3.0, n_doc=100, n_programme=100, var_trials=0.0004
            ),
            "an ANNUALISED sr (1.2699 = 0.08 x sqrt(252)) fed to the per-period DSR",
        )
        ok += expect_raise(
            lambda: programme_dsr(
                0.05, 2000, 0.0, 3.0, n_doc=1000, n_programme=100, var_trials=0.0004
            ),
            "n_programme below n_doc",
        )

        # -- 4. the haircut (test 68) --------------------------------------------------
        print("\n  [4] haircut")
        assert haircut(0.10) == 0.05
        assert haircut(0.10, vault_estimate=0.03) == 0.03, "vault lower -> vault wins"
        assert haircut(0.10, vault_estimate=0.08) == 0.05, "vault higher -> haircut wins"
        ok += 1
        print("    0.10 -> 0.05; vault 0.03 -> 0.03; vault 0.08 -> 0.05")
        ok += expect_raise(lambda: haircut(0.10, frac=0.0), "frac = 0")

        # -- 5. episodes ---------------------------------------------------------------
        print("\n  [5] episodes: dates and guards")
        usd = [1.0] * 30 + [50.0] + [2.0] * 30
        dates = [f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(61)]
        ok += expect_raise(
            lambda: drop_best_year(usd, list(reversed(dates))), "unsorted dates"
        )
        ok += expect_raise(
            lambda: drop_best_year(usd, dates), "a single calendar year"
        )
        two_years = [f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(31)] + [
            f"2021-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(30)
        ]
        year = drop_best_year(usd, two_years)
        print(f"    drop_best_year -> {year['year_dropped']}, "
              f"${year['total_before']:.0f} -> ${year['total_after']:.0f}")
        ok += 1
        days = drop_best_days(usd, frac=0.01)
        assert days["n_dropped"] == 1, days
        assert days["total_after"] == days["total_before"] - 50.0
        ok += 1
        trim = symmetric_trim(usd)
        assert trim["n_trimmed_each_side"] == 1, trim
        assert sessions_to_half_pnl(usd) >= 1
        checks = episode_checks(usd, two_years)
        assert checks["edge_positive_after_both"] is True
        ok += 1
        print(f"    episode_checks -> edge_positive_after_both="
              f"{checks['edge_positive_after_both']}, "
              f"trim share {trim['share_ex_both_1pct']:.4f}")
        ok += expect_raise(lambda: symmetric_trim([1.0] * 5), "fewer than 21 sessions")
        ok += expect_raise(
            lambda: sessions_to_half_pnl([-1.0] * 30), "a negative total P&L"
        )
        ok += expect_raise(
            lambda: shared_period(usd, usd[:10], two_years), "misaligned series lengths"
        )
        ok += expect_raise(lambda: episode_checks([1.0, float("nan")], ["2020-01-01", "2020-01-02"]),
                           "a non-finite P&L value")
        sp = shared_period(usd, [v * 2 for v in usd], two_years)
        assert sp["rho"] > 0.99 and sp["top10_overlap"] == 10, sp
        ok += 1
        print(f"    shared_period(x, 2x) -> rho {sp['rho']:.4f}, overlap "
              f"{sp['top10_overlap']}, flag {sp['flag']}")

        # -- 6. the counter ------------------------------------------------------------
        print("\n  [6] programme_trial_count")
        result = programme_trial_count()
        assert result["total"] == (
            result["etf_pool_distinct_configs"]
            + result["other_registries"]
            + result["trials_csv_rows"]
        )
        ok += 1
        print(f"    {result['etf_pool_distinct_configs']:,} + "
              f"{result['other_registries']:,} + {result['trials_csv_rows']:,} = "
              f"{result['total']:,}")
        ok += expect_raise(
            lambda: programme_trial_count(census=tmp_path / "missing.json"),
            "a missing registry census",
            exc=(FileNotFoundError,),
        )

        # -- 7. the D504 anchor --------------------------------------------------------
        print("\n  [7] D504 anchor (data/d504_arm_full_history.json)")
        published = json.loads(
            (REPO / "data" / "d504_arm_full_history.json").read_text(encoding="utf-8")
        )
        conc, overall = published["concentration_usable"], published["overall_usable"]
        assert conc["share_ex_both_1pct"] == conc["pnl_ex_both_1pct_usd"] / overall["total_usd"]
        assert conc["top1"] == overall["best_day_usd"] / overall["total_usd"]
        assert conc["n_trimmed_each_side"] == max(1, overall["n_sessions"] // 100)
        ok += 1
        print(f"    share_ex_both_1pct {conc['share_ex_both_1pct']!r} reproduced "
              "bit-identically from the published total")

    print(f"\n  {ok} checks passed; every guard above raised on the input it refuses.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="seed the registry and write the page")
    parser.add_argument("--count", action="store_true", help="print the programme trial count")
    parser.add_argument("--selftest", action="store_true", help="prove every guard raises")
    args = parser.parse_args()
    if not (args.render or args.count or args.selftest):
        parser.print_help()
        return 2
    if args.render:
        render()
    if args.count:
        count()
    if args.selftest:
        selftest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
