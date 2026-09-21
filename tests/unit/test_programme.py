"""Unit tests for `validation/programme.py` (D592).

The ledger of record is `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8 / §12A of
`OPENING_AGENT_STATE_PREREG.md`, and the three unit tests it names:

    66. Programme registry: a family's promotion check uses α = 0.005; registering an
        eighth to tenth family uses a reserved slot; an eleventh is refused without a doc
        amendment.
    67. Programme DSR: the trial count equals the total rows across all docs' trials.csv.
    68. Haircut: 50% of the walk-forward edge, or the vault estimate if lower.

Each of the three has its own section below, named for its number. No sqlite file is
opened by any test here: the counter reads the committed census
`data/trial_registries.json`, never a registry (`TrialRegistry.__init__` opens read-write
and runs CREATE TABLE).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from backtest_framework.validation.dsr import deflated_sharpe_ratio
from backtest_framework.validation.programme import (
    DEFAULT_CENSUS_PATH,
    DEFAULT_PAGE_PATH,
    DEFAULT_REGISTRY_PATH,
    DSR_PROMOTION_BAR,
    HAIRCUT_FRACTION,
    N_SLOTS,
    PER_PERIOD_SR_CEILING,
    PROGRAMME_ALPHA,
    SEALED_DATE,
    SEED_FAMILIES,
    SLOT_ALPHA,
    TRIALS_COLUMNS,
    Family,
    Registry,
    TrialsCsv,
    haircut,
    programme_dsr,
    programme_trial_count,
    seed_registry,
)

REPO = Path(__file__).resolve().parents[2]


# ==================================================================== ledger test 66


def test_66_the_alpha_split_is_the_docs_arithmetic():
    assert PROGRAMME_ALPHA == 0.05
    assert N_SLOTS == 10
    assert SLOT_ALPHA == 0.005
    assert PROGRAMME_ALPHA / N_SLOTS == SLOT_ALPHA


def test_66_promotion_check_uses_alpha_0_005(tmp_path):
    registry = Registry(path=tmp_path / "r.json")
    registry.register("F", "DOC.md")
    assert registry.promotion_check("F", 0.0049) is True
    assert registry.promotion_check("F", 0.005) is True, "the bar is <=, per the doc"
    assert registry.promotion_check("F", 0.0051) is False
    assert registry.promotion_check("F", 0.05) is False, "programme alpha is not the family's"


def test_66_the_eighth_ninth_and_tenth_use_the_reserved_slots(tmp_path):
    registry = Registry(path=tmp_path / "r.json")
    for i in range(7):
        registry.register(f"seed {i}", "DOC.md")
    assert registry.free_slots() == (8, 9, 10)
    for i, expected in enumerate((8, 9, 10)):
        assert registry.register(f"later {i}", "NEW.md").slot == expected
    assert registry.free_slots() == ()


def test_66_the_eleventh_is_refused_without_an_amendment(tmp_path):
    registry = Registry(path=tmp_path / "r.json")
    for i in range(N_SLOTS):
        registry.register(f"f{i}", "DOC.md")
    with pytest.raises(ValueError, match="requires a doc amendment"):
        registry.register("eleventh", "DOC.md")
    with pytest.raises(ValueError, match="requires a doc amendment"):
        registry.register("eleventh", "DOC.md", amendment="   ")
    eleventh = registry.register("eleventh", "DOC.md", amendment="DOC.md v2.0 re-allocates α")
    assert eleventh.slot == 11
    assert eleventh.amendment == "DOC.md v2.0 re-allocates α"


def test_66_an_amendment_is_refused_while_a_slot_is_free(tmp_path):
    """The door is for the eleventh family, not a way to skip the reserved slots."""
    registry = Registry(path=tmp_path / "r.json")
    registry.register("first", "DOC.md")
    with pytest.raises(ValueError, match="is still free"):
        registry.register("second", "DOC.md", amendment="unnecessary")


def test_66_alpha_is_never_re_allocated_for_a_registered_family(tmp_path):
    registry = Registry(path=tmp_path / "r.json")
    registry.register("F", "DOC.md")
    with pytest.raises(ValueError, match="already registered in slot 1"):
        registry.register("F", "OTHER.md")
    assert len(registry) == 1


def test_66_promotion_check_refuses_a_t_statistic_and_an_unknown_family(tmp_path):
    registry = Registry(path=tmp_path / "r.json")
    registry.register("F", "DOC.md")
    with pytest.raises(ValueError, match="probability in"):
        registry.promotion_check("F", 2.8)
    with pytest.raises(ValueError, match="probability in"):
        registry.promotion_check("F", -0.001)
    with pytest.raises(KeyError, match="no family named"):
        registry.promotion_check("missing", 0.001)


def test_66_the_registry_round_trips_through_its_json(tmp_path):
    path = tmp_path / "r.json"
    first = Registry(path=path)
    first.register("F", "DOC.md", note="a statistic")
    reloaded = Registry(path=path)
    assert [f.to_json() for f in reloaded] == [f.to_json() for f in first]
    assert reloaded.get("F").alpha == SLOT_ALPHA
    assert json.loads(path.read_text(encoding="utf-8"))["slot_alpha"] == SLOT_ALPHA


def test_66_a_family_beyond_slot_ten_cannot_exist_without_an_amendment():
    with pytest.raises(ValueError, match="without naming a doc amendment"):
        Family(name="F", doc="D.md", registered_utc=SEALED_DATE, slot=11)
    ok = Family(name="F", doc="D.md", registered_utc=SEALED_DATE, slot=11, amendment="v2")
    assert ok.slot == 11


def test_66_family_guards():
    with pytest.raises(ValueError, match="needs a name"):
        Family(name="  ", doc="D.md", registered_utc=SEALED_DATE, slot=1)
    with pytest.raises(ValueError, match="needs the doc"):
        Family(name="F", doc="", registered_utc=SEALED_DATE, slot=1)
    with pytest.raises(ValueError, match="slots are 1-based"):
        Family(name="F", doc="D.md", registered_utc=SEALED_DATE, slot=0)
    with pytest.raises(ValueError, match="must lie in"):
        Family(name="F", doc="D.md", registered_utc=SEALED_DATE, slot=1, alpha=0.5)


# --------------------------------------------------------- the seven committed families


def test_the_committed_registry_holds_the_seven_families_the_docs_name():
    """`data/programme_registry.json` as rendered, against the two docs' own list:
    LETF close flow H1; shock classifier H1; ledger H2; index H-R1, H-R2, H-R3(b);
    opening H-O2. Seven slots used, three reserved."""
    registry = Registry(path=DEFAULT_REGISTRY_PATH)
    assert [f.name for f in registry] == [name for name, _, _ in SEED_FAMILIES]
    assert [f.slot for f in registry] == [1, 2, 3, 4, 5, 6, 7]
    assert registry.free_slots() == (8, 9, 10)
    assert all(f.registered_utc == SEALED_DATE for f in registry)
    assert all(f.alpha == SLOT_ALPHA for f in registry)
    assert registry.alpha_total() == pytest.approx(0.035)
    docs = {f.doc for f in registry}
    assert docs == {
        "LETF_CLOSE_FLOW_PREREG.md",
        "SHOCK_CLASSIFIER_PREREG.md",
        "SETTLEMENT_FLOW_LEDGER_PREREG.md",
        "INDEX_REWEIGHT_FLOW_PREREG.md",
        "OPENING_AGENT_STATE_PREREG.md",
    }
    for doc in docs:
        assert (REPO / "docs" / "internal" / "User-Doc-Deposit" / doc).exists()


def test_seed_registry_is_idempotent(tmp_path):
    path = tmp_path / "r.json"
    first = seed_registry(path)
    again = seed_registry(path)
    assert [f.to_json() for f in first] == [f.to_json() for f in again]
    assert len(again) == len(SEED_FAMILIES) == 7


def test_the_rendered_page_exists_and_says_where_the_deposits_path_maps_to():
    page = DEFAULT_PAGE_PATH.read_text(encoding="utf-8")
    assert "# PROGRAMME REGISTRY" in page
    assert "no root `results/`" in page
    assert "data/programme_registry.json" in page
    for name, _, _ in SEED_FAMILIES:
        assert f"`{name}`" in page
    assert page.count("*(reserved)*") == 3
    assert not (REPO / "results").exists(), "the mapping exists because this path does not"


def test_render_md_is_deterministic_for_a_pinned_date(tmp_path):
    registry = seed_registry(tmp_path / "r.json")
    a = registry.render_md(tmp_path / "a.md", date=SEALED_DATE).read_text(encoding="utf-8")
    b = registry.render_md(tmp_path / "b.md", date=SEALED_DATE).read_text(encoding="utf-8")
    assert a == b
    assert a == DEFAULT_PAGE_PATH.read_text(encoding="utf-8")


# ==================================================================== ledger test 67


def test_67_the_union_schema_covers_all_four_documents():
    """Every column of every doc's `trials.csv` line, plus `doc` and `family`."""
    letf = "trial_id timestamp tau instrument k hold cost_mult event_filter n_trades " \
           "mean_gross mean_net t_hac sharpe_net notes".split()
    shock = "trial_id timestamp instrument class z w c_hi c_lo s f exit_type fill_model " \
            "cost_mult event_filter n_trades mean_gross mean_net t_clustered sharpe_net " \
            "notes".split()
    index = "trial_id timestamp stage construction year_set t0_offset hold fill_model " \
            "cost_mult gsci_stack k n_obs mean_gross mean_net p_boot notes".split()
    ledger = "trial_id timestamp instrument stage timing_rule t0 fill_model cost_mult " \
             "flag_filter sizing n_trades flow_corr_oos mean_gross mean_net t_clustered " \
             "sharpe_net notes".split()
    union = set(letf) | set(shock) | set(index) | set(ledger)
    assert union | {"doc", "family"} == set(TRIALS_COLUMNS)
    assert len(TRIALS_COLUMNS) == len(set(TRIALS_COLUMNS)) == len(union) + 2
    assert TRIALS_COLUMNS[:3] == ("trial_id", "doc", "family")
    assert TRIALS_COLUMNS[-1] == "notes"


def test_67_trials_csv_is_append_only(tmp_path):
    log = TrialsCsv(tmp_path / "trials.csv")
    assert log.count() == 0 and log.rows() == [] and not log.exists()
    log.append({"trial_id": "t1", "doc": "LETF", "family": "H1", "cost_mult": 1.0})
    log.append({"trial_id": "t2", "doc": "LETF", "family": "H1", "cost_mult": 2.0})
    assert log.count() == 2
    with pytest.raises(ValueError, match="already logged"):
        log.append({"trial_id": "t1", "doc": "LETF", "family": "H1"})
    assert log.count() == 2, "a refused append must leave the file untouched"


def test_67_trials_csv_rejects_an_unknown_column_and_a_missing_provenance(tmp_path):
    log = TrialsCsv(tmp_path / "trials.csv")
    with pytest.raises(ValueError, match="unknown trials.csv column"):
        log.append({"trial_id": "t1", "doc": "L", "family": "H1", "sharpe_annualised": 1.0})
    for missing in ("trial_id", "doc", "family"):
        row = {"trial_id": "t1", "doc": "L", "family": "H1"}
        row[missing] = ""
        with pytest.raises(ValueError, match=f"non-empty '{missing}'"):
            log.append(row)
    assert log.count() == 0


def test_67_trials_csv_pins_the_newline_and_the_encoding(tmp_path):
    """D550: the author's OS is not the runner's. A row logged here must be the same
    bytes anywhere."""
    path = tmp_path / "trials.csv"
    log = TrialsCsv(path)
    log.append({"trial_id": "t1", "doc": "LETF", "family": "H1", "notes": "café"})
    raw = path.read_bytes()
    assert b"\r\n" not in raw
    assert raw.decode("utf-8").splitlines()[0] == ",".join(TRIALS_COLUMNS)
    assert log.rows()[0]["notes"] == "café"


def test_67_a_drifted_header_is_refused_rather_than_pooled(tmp_path):
    path = tmp_path / "trials.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["trial_id", "doc"])
        writer.writerow(["t1", "LETF"])
    with pytest.raises(ValueError, match="not the D592 union schema"):
        TrialsCsv(path).count()


def test_67_the_counter_totals_its_three_terms():
    got = programme_trial_count()
    assert set(got) == {
        "etf_pool_distinct_configs", "other_registries", "trials_csv_rows", "total", "rule",
    }
    assert got["total"] == (
        got["etf_pool_distinct_configs"] + got["other_registries"] + got["trials_csv_rows"]
    )


def test_67_the_counter_reads_the_census_and_not_a_registry():
    """The ETF pool is the `prior_etf_trials` predicate's number, not the raw row count."""
    census = json.loads(DEFAULT_CENSUS_PATH.read_text(encoding="utf-8"))
    got = programme_trial_count()
    assert got["etf_pool_distinct_configs"] == census["etf_pool"]["distinct_configs_deduplicated"]
    assert got["etf_pool_distinct_configs"] == 45_346
    assert got["etf_pool_distinct_configs"] < census["etf_pool"]["raw_rows"]
    assert got["etf_pool_distinct_configs"] < census["etf_pool"][
        "sum_of_per_registry_distinct_configs"
    ]
    # the non-pool term: live only, so the superseded copy and the 10-row demo are out
    expected = sum(
        row["distinct_config_json"]
        for row in census["registries"]
        if not row["in_etf_pool"] and row["status"] == "live"
    )
    assert got["other_registries"] == expected == 37_728
    assert all(
        row["status"] != "live" or row["in_etf_pool"] or row["registry"] != "trial"
        for row in census["registries"]
    )


def test_67_no_trials_csv_exists_in_the_repository_yet():
    """The deposit's own counter is rows of `trials.csv`, and there are none — recorded
    as a fact of today's tree, not assumed. If one appears, this test says so."""
    assert list(REPO.glob("data/**/trials.csv")) == []
    assert programme_trial_count()["trials_csv_rows"] == 0


def test_67_the_rule_names_both_counting_conventions():
    rule = programme_trial_count()["rule"]
    assert "prior_etf_trials" in rule and "D98" in rule
    assert "DISTINCT DE-DUPLICATED CONFIG PAYLOAD" in rule
    assert "ROWS" in rule
    assert "upper bound" in rule


def test_67_a_missing_census_raises_rather_than_counting_zero(tmp_path):
    with pytest.raises(FileNotFoundError, match="committed census"):
        programme_trial_count(census=tmp_path / "nope.json")


def test_67_trials_csv_rows_are_counted_when_they_exist(tmp_path):
    (tmp_path / "data" / "letf").mkdir(parents=True)
    log = TrialsCsv(tmp_path / "data" / "letf" / "trials.csv")
    for i in range(5):
        log.append({"trial_id": f"t{i}", "doc": "LETF", "family": "H1"})
    got = programme_trial_count(repo=tmp_path)
    assert got["trials_csv_rows"] == 5
    assert got["total"] == got["etf_pool_distinct_configs"] + got["other_registries"] + 5


# ================================================================= the programme DSR


def test_programme_dsr_returns_both_and_the_programme_one_is_never_larger():
    got = programme_dsr(0.05, 2000, 0.0, 3.0, n_doc=100, n_programme=83_074, var_trials=4e-4)
    assert set(got) == {"dsr_doc", "dsr_programme"}
    assert 0.0 <= got["dsr_programme"] <= got["dsr_doc"] <= 1.0
    assert got["dsr_doc"] == deflated_sharpe_ratio(0.05, 2000, 0.0, 3.0, 100, 4e-4)
    assert got["dsr_programme"] == deflated_sharpe_ratio(0.05, 2000, 0.0, 3.0, 83_074, 4e-4)


def test_programme_dsr_refuses_an_annualised_sharpe_citing_d98():
    """D98's red finding: an annualised sr against a per-period var_trials inflates SR0 by
    sqrt(ppy) and forces the DSR to 0 for any strategy."""
    daily = 0.08
    annualised = daily * math.sqrt(252)
    assert annualised > PER_PERIOD_SR_CEILING
    with pytest.raises(ValueError, match="D98"):
        programme_dsr(annualised, 2000, 0.0, 3.0, n_doc=10, n_programme=10, var_trials=4e-4)
    with pytest.raises(ValueError, match="D98"):
        programme_dsr(-annualised, 2000, 0.0, 3.0, n_doc=10, n_programme=10, var_trials=4e-4)
    assert programme_dsr(daily, 2000, 0.0, 3.0, n_doc=10, n_programme=10, var_trials=4e-4)


def test_programme_dsr_refuses_a_programme_count_below_the_doc_count():
    with pytest.raises(ValueError, match="is below n_doc"):
        programme_dsr(0.05, 2000, 0.0, 3.0, n_doc=500, n_programme=100, var_trials=4e-4)
    with pytest.raises(ValueError, match="at least 2 trials"):
        programme_dsr(0.05, 2000, 0.0, 3.0, n_doc=1, n_programme=100, var_trials=4e-4)
    # equality is allowed: a doc whose trials ARE the whole programme
    assert programme_dsr(0.05, 2000, 0.0, 3.0, n_doc=50, n_programme=50, var_trials=4e-4)


def test_the_programme_count_is_what_costs_the_promotion():
    """With this repository's real pool, a Sharpe that clears 0.95 on a doc's own 100
    trials does not clear it on the programme's 83,074 — which is the entire point of
    control 3."""
    got = programme_dsr(0.09, 2000, 0.0, 3.0, n_doc=100, n_programme=83_074, var_trials=4e-4)
    assert got["dsr_doc"] == pytest.approx(0.960583, abs=1e-6)
    assert got["dsr_doc"] >= DSR_PROMOTION_BAR
    assert got["dsr_programme"] == pytest.approx(0.553130, abs=1e-6)
    assert got["dsr_programme"] < DSR_PROMOTION_BAR


# ==================================================================== ledger test 68


def test_68_haircut_is_half_the_edge():
    assert HAIRCUT_FRACTION == 0.5
    assert haircut(0.10) == 0.05
    assert haircut(120.0) == 60.0
    assert haircut(0.10, frac=0.25) == 0.025


def test_68_the_vault_estimate_wins_when_it_is_lower():
    assert haircut(0.10, vault_estimate=0.03) == 0.03
    assert haircut(0.10, vault_estimate=0.05) == 0.05
    assert haircut(0.10, vault_estimate=0.08) == 0.05
    assert haircut(0.10, vault_estimate=-0.02) == -0.02, "a vault miss is not floored at 0"


def test_68_haircut_guards():
    with pytest.raises(ValueError, match=r"frac must lie in \(0, 1\]"):
        haircut(0.1, frac=0.0)
    with pytest.raises(ValueError, match=r"frac must lie in \(0, 1\]"):
        haircut(0.1, frac=1.5)
    assert haircut(0.1, frac=1.0) == 0.1
