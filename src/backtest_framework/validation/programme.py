"""Programme-level false-positive controls: the α registry, the trial log, the
programme-wide DSR and the winner's-curse haircut (D592).

The ledger of record is written identically in two deposit documents —
`docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8 and
`OPENING_AGENT_STATE_PREREG.md` §12A — and the four controls this module implements are
its items 2, 3 and 4, with the ledger's unit tests 66, 67 and 68 as the acceptance bar:

    66. Programme registry: a family's promotion check uses α = 0.005; registering an
        eighth to tenth family uses a reserved slot; an eleventh is refused without a
        doc amendment.
    67. Programme DSR: the trial count equals the total rows across all docs' trials.csv
        files.
    68. Haircut: sizing and the Track 3 power check use 50% of the walk-forward edge, or
        the vault estimate if lower.

(Item 5, the episode and shared-period checks, is `validation/episodes.py`; items 1, 6
and 7 — the sealed vault, the one-bar-delay rerun and the leak canary — are not in scope
here, because each of them is a property of a runner that does not exist yet.)

WHERE `results/PROGRAMME_REGISTRY.md` LIVES IN THIS REPOSITORY. The deposit names a path,
`results/PROGRAMME_REGISTRY.md`, that has no counterpart here: **there is no root
`results/` directory**, and `validation/power.py:write_power_md` already declined to
invent one. The mapping used by this module, and recorded in D592:

    deposit `results/PROGRAMME_REGISTRY.md`  ->  `docs/results/PROGRAMME_REGISTRY.md`  (the
                                                 rendered page; `docs/results/` is this
                                                 repository's prose-results home, 30-odd
                                                 `*_RESULTS.md` pages)
                                             +   `data/programme_registry.json`  (the
                                                 machine-readable state; `data/` is the
                                                 artefact home)

The page is RENDERED from the JSON and is never the source of truth. A markdown table
cannot refuse an eleventh slot.

THE DSR UNITS CONTRACT IS LOAD-BEARING HERE (D98). Every Sharpe crossing `programme_dsr`
is per-period and non-annualised, in the same frequency as `t`. Feeding an annualised
Sharpe against a per-period trial variance inflates SR0 by sqrt(periods per year) — about
15.9x on daily data — and drives the DSR to zero for any strategy at all; that is the
audit's one red finding, reproduced in D98. `programme_dsr` therefore refuses a `sr`
above 1.0 per period rather than returning the number an annualised input would produce.

THE TRIAL POOL (D90/D98, and `run_macd_ladder.prior_etf_trials`). Two kinds of evidence
are counted here and they are NOT counted the same way, which is the whole content of
`programme_trial_count`'s `rule` string: a sqlite registry is counted by DISTINCT
DE-DUPLICATED CONFIG PAYLOAD, because the same window re-run at a scaled cost multiplier
is a sensitivity point and not an independent trial; a `trials.csv` is counted by ROWS,
because that is what the deposit says and because a csv row IS a configuration there.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dsr import deflated_sharpe_ratio

_REPO = Path(__file__).resolve().parents[3]

#: `data/programme_registry.json` — the machine-readable registry state.
DEFAULT_REGISTRY_PATH = _REPO / "data" / "programme_registry.json"
#: `docs/results/PROGRAMME_REGISTRY.md` — the rendered page (the deposit's
#: `results/PROGRAMME_REGISTRY.md`).
DEFAULT_PAGE_PATH = _REPO / "docs" / "results" / "PROGRAMME_REGISTRY.md"
#: `data/trial_registries.json` — D589's census of the 19 sqlite trial registries.
DEFAULT_CENSUS_PATH = _REPO / "data" / "trial_registries.json"

#: Programme-wide α, split into 10 equal slots (ledger §13A.8(2), opening §12A(2)).
PROGRAMME_ALPHA = 0.05
N_SLOTS = 10
SLOT_ALPHA = PROGRAMME_ALPHA / N_SLOTS  # 0.005

#: The programme-level DSR bar for promotion (ledger §13A.8(3)).
DSR_PROMOTION_BAR = 0.95

#: The winner's-curse haircut (ledger §13A.8(4)).
HAIRCUT_FRACTION = 0.5

#: The date the deposit's programme controls were sealed, and the registration date of
#: the seven families the two docs name.
SEALED_DATE = "2026-09-21"

#: The seven families named in ledger §13A.8(2) and opening §12A(2), in the docs' order.
#: Three slots stay reserved for future models.
SEED_FAMILIES: tuple[tuple[str, str, str], ...] = (
    (
        "LETF close flow H1",
        "LETF_CLOSE_FLOW_PREREG.md",
        "Primary effect: on active days the mean signed return tau -> close is positive "
        "(§4 H1; Holm across the 6 primary cells)",
    ),
    (
        "shock classifier H1",
        "SHOCK_CLASSIFIER_PREREG.md",
        "Class divergence: INFO and LIQ returns differ in the shock direction "
        "(§6 H1; Holm across the 4 instruments)",
    ),
    (
        "ledger H2",
        "SETTLEMENT_FLOW_LEDGER_PREREG.md",
        "Price effect: signed return from the t0+1 fill to the W_end close on traded days "
        "(§9 H2; Holm across the 2 instruments)",
    ),
    (
        "index H-R1",
        "INDEX_REWEIGHT_FLOW_PREREG.md",
        "Execution-day effect: signed entry -> W_end close return pooled across "
        "commodities, days and years (§6 H-R1; Holm across constructions A and B)",
    ),
    (
        "index H-R2",
        "INDEX_REWEIGHT_FLOW_PREREG.md",
        "Reversal: signed return in the reversal direction over 1/3/5 days "
        "(§6 H-R2; Holm across 3 holds x 2 constructions)",
    ),
    (
        "index H-R3(b)",
        "INDEX_REWEIGHT_FLOW_PREREG.md",
        "Pre-positioning, TRADING arm only: the December entry -> pre-execution exit "
        "return in the forecast direction (§6 H-R3(b); H-R3(a) is descriptive and is not "
        "a decision family)",
    ),
    (
        "opening H-O2",
        "OPENING_AGENT_STATE_PREREG.md",
        "Decision value: the state-conditioned policy's net daily return minus the best "
        "of B1-B3, paired by day (§7 H-O2; Holm across t0 in {09:45, 10:00})",
    ),
)


# --------------------------------------------------------------------------- the registry


@dataclass(frozen=True)
class Family:
    """One registered primary decision family and the α slot it holds.

    `slot` is 1-based. Slots 1..10 are the pre-registered allocation; a slot above
    `N_SLOTS` exists only where `amendment` names the doc amendment that re-allocated α,
    which is the only door §13A.8(2) leaves open.
    """

    name: str
    doc: str
    registered_utc: str
    slot: int
    alpha: float = SLOT_ALPHA
    amendment: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a family needs a name")
        if not self.doc.strip():
            raise ValueError(f"family {self.name!r} needs the doc that registers it")
        if self.slot < 1:
            raise ValueError(f"family {self.name!r} has slot {self.slot}; slots are 1-based")
        if not 0.0 < self.alpha <= PROGRAMME_ALPHA:
            raise ValueError(
                f"family {self.name!r} has alpha {self.alpha}; it must lie in "
                f"(0, {PROGRAMME_ALPHA}]"
            )
        if self.slot > N_SLOTS and not (self.amendment or "").strip():
            raise ValueError(
                f"family {self.name!r} holds slot {self.slot} beyond the {N_SLOTS} "
                "pre-registered slots without naming a doc amendment"
            )

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "doc": self.doc,
            "registered_utc": self.registered_utc,
            "slot": self.slot,
            "alpha": self.alpha,
            "amendment": self.amendment,
            "note": self.note,
        }

    @staticmethod
    def from_json(row: Mapping[str, Any]) -> Family:
        return Family(
            name=str(row["name"]),
            doc=str(row["doc"]),
            registered_utc=str(row["registered_utc"]),
            slot=int(row["slot"]),
            alpha=float(row.get("alpha", SLOT_ALPHA)),
            amendment=(None if row.get("amendment") in (None, "") else str(row["amendment"])),
            note=str(row.get("note", "")),
        )


@dataclass
class Registry:
    """The programme α registry: `data/programme_registry.json` plus its rendered page.

    `Registry(path)` loads the file if it exists and starts empty otherwise; nothing is
    written until `register` or `save` is called. The registry is NOT append-only in the
    `docs/BOOK*.md` sense — it is a state file — but `register` refuses to re-register or
    to silently move a family, which is the property the append-only books protect.
    """

    path: Path = DEFAULT_REGISTRY_PATH
    families: list[Family] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.families = [Family.from_json(row) for row in payload["families"]]
            self._check_slots()

    # -- state -------------------------------------------------------------------------

    def _check_slots(self) -> None:
        slots = [f.slot for f in self.families]
        if len(set(slots)) != len(slots):
            raise ValueError(f"the registry holds a duplicated slot: {sorted(slots)}")
        names = [f.name for f in self.families]
        if len(set(names)) != len(names):
            raise ValueError(f"the registry holds a duplicated family name: {sorted(names)}")

    def __len__(self) -> int:
        return len(self.families)

    def __iter__(self) -> Iterator[Family]:
        return iter(sorted(self.families, key=lambda f: f.slot))

    def get(self, name: str) -> Family:
        for family in self.families:
            if family.name == name:
                return family
        raise KeyError(
            f"no family named {name!r} is registered; the registry holds "
            f"{[f.name for f in self.families]}"
        )

    def free_slots(self) -> tuple[int, ...]:
        """The pre-registered slots 1..10 that are still unallocated."""
        taken = {f.slot for f in self.families}
        return tuple(slot for slot in range(1, N_SLOTS + 1) if slot not in taken)

    def alpha_total(self) -> float:
        """The α actually allocated. Above `PROGRAMME_ALPHA` only after an amendment."""
        return float(sum(f.alpha for f in self.families))

    # -- registration ------------------------------------------------------------------

    def register(
        self,
        name: str,
        doc: str,
        *,
        amendment: str | None = None,
        registered_utc: str = SEALED_DATE,
        note: str = "",
    ) -> Family:
        """Allocate one α slot to a new primary decision family (ledger unit test 66).

        The lowest free slot of 1..10 is taken, so registrations are ordered and the
        eighth, ninth and tenth families land in the three reserved slots without any
        special case. **An eleventh is refused** unless `amendment` names the doc
        amendment that re-allocates α — §13A.8(2)'s only door, and it is a string that
        goes into the record, not a boolean flag.

        Re-registering an existing name raises: §13A.8(2) forbids re-allocating α
        retroactively for families already evaluated, and a silent overwrite is exactly
        that.
        """
        if not name.strip():
            raise ValueError("a family needs a name")
        if any(f.name == name for f in self.families):
            raise ValueError(
                f"family {name!r} is already registered in slot {self.get(name).slot}; "
                "alpha is never re-allocated for a family already registered "
                "(ledger 13A.8(2))"
            )
        free = self.free_slots()
        if free:
            slot = free[0]
            if amendment is not None and amendment.strip():
                raise ValueError(
                    f"family {name!r} names an amendment but slot {slot} of {N_SLOTS} is "
                    "still free; an amendment is for the ELEVENTH family, not a spare one"
                )
            amendment = None
        else:
            if not (amendment or "").strip():
                raise ValueError(
                    f"all {N_SLOTS} programme alpha slots are allocated "
                    f"({[f.name for f in self]}); registering {name!r} requires a doc "
                    "amendment that re-allocates alpha (ledger 13A.8(2)) — pass it as "
                    "`amendment=`"
                )
            slot = max(f.slot for f in self.families) + 1
        family = Family(
            name=name,
            doc=doc,
            registered_utc=registered_utc,
            slot=slot,
            alpha=SLOT_ALPHA,
            amendment=amendment,
            note=note,
        )
        self.families.append(family)
        self._check_slots()
        self.save()
        return family

    def save(self) -> Path:
        """Write `data/programme_registry.json`. Returns the path written."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "spec": "D592",
            "source": (
                "SETTLEMENT_FLOW_LEDGER_PREREG.md 13A.8(2) and "
                "OPENING_AGENT_STATE_PREREG.md 12A(2)"
            ),
            "programme_alpha": PROGRAMME_ALPHA,
            "n_slots": N_SLOTS,
            "slot_alpha": SLOT_ALPHA,
            "sealed": SEALED_DATE,
            "families": [f.to_json() for f in self],
        }
        self.path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        return self.path

    # -- the decision ------------------------------------------------------------------

    def promotion_check(self, name: str, adjusted_p: float) -> bool:
        """True iff the family's WITHIN-DOC ADJUSTED p clears its slot's α (= 0.005).

        Ledger §13A.8(2): *"Promotion requires the family's within-doc adjusted p-value
        <= 0.005 (roughly t >= 2.8), in addition to every within-doc criterion."* The
        "in addition" is the point: a True here is one necessary condition, never a
        promotion. `adjusted_p` must already carry the doc's own Holm correction.
        """
        family = self.get(name)
        if not 0.0 <= adjusted_p <= 1.0:
            raise ValueError(
                f"adjusted_p must be a probability in [0, 1], got {adjusted_p} - "
                "pass the within-doc Holm-adjusted p-value, not a t-statistic"
            )
        return bool(adjusted_p <= family.alpha)

    # -- the page ----------------------------------------------------------------------

    def render_md(self, path: Path | str = DEFAULT_PAGE_PATH, date: str | None = None) -> Path:
        """Render `docs/results/PROGRAMME_REGISTRY.md` from the JSON. Returns the path.

        The deposit calls this page `results/PROGRAMME_REGISTRY.md`; this repository has
        no root `results/`, and the mapping to `docs/results/` + `data/` is recorded in
        D592 and restated on the page itself.
        """
        path = Path(path)
        stamp = date if date is not None else _dt.datetime.now(_dt.timezone.utc).date().isoformat()
        used = len(self.families)
        over = [f for f in self if f.slot > N_SLOTS]
        lines = [
            "# PROGRAMME REGISTRY",
            "",
            f"**Generated:** {stamp} · `backtest_framework.validation.programme` (D592) · "
            f"rendered from [`data/programme_registry.json`](../../data/programme_registry.json)",
            "",
            "The deposit's programme-level false-positive controls name this page "
            "`results/PROGRAMME_REGISTRY.md` "
            "([`SETTLEMENT_FLOW_LEDGER_PREREG.md`](../internal/User-Doc-Deposit/"
            "SETTLEMENT_FLOW_LEDGER_PREREG.md) §13A.8(2), "
            "[`OPENING_AGENT_STATE_PREREG.md`](../internal/User-Doc-Deposit/"
            "OPENING_AGENT_STATE_PREREG.md) §12A(2)). **This repository has no root "
            "`results/`**: the rendered page lives here in `docs/results/` with the other "
            "prose-results pages, and the state it is rendered from lives in `data/` with "
            "the other artefacts (D592).",
            "",
            f"**Programme-wide α = {PROGRAMME_ALPHA}, split into {N_SLOTS} equal slots of "
            f"{SLOT_ALPHA}.** Sealed {SEALED_DATE}. "
            f"**{used} of {N_SLOTS} slots allocated; {N_SLOTS - min(used, N_SLOTS)} reserved "
            "for future models.**",
            "",
            "A family may only be registered into a free slot. When all ten are used, an "
            "eleventh requires a doc amendment that re-allocates α — never retroactively "
            "for families already evaluated. **Promotion requires the family's within-doc "
            f"adjusted p-value ≤ {SLOT_ALPHA} (roughly t ≥ 2.8), in addition to every "
            "within-doc criterion, and a programme-level DSR ≥ "
            f"{DSR_PROMOTION_BAR}.** A row below is a registration, not a result.",
            "",
            "| Slot | Family | α | Doc | Registered | Statistic |",
            "|---|---|---|---|---|---|",
        ]
        for family in self:
            note = family.note or "—"
            if family.amendment:
                note = f"{note} · **amendment:** {family.amendment}"
            lines.append(
                f"| {family.slot} | `{family.name}` | {family.alpha} | "
                f"`{family.doc}` | {family.registered_utc} | {note} |"
            )
        for slot in self.free_slots():
            lines.append(f"| {slot} | *(reserved)* | {SLOT_ALPHA} | — | — | — |")
        lines += [
            "",
            f"**α allocated: {self.alpha_total():.3f} of {PROGRAMME_ALPHA}.**",
        ]
        if over:
            lines.append(
                f"**{len(over)} family(ies) sit beyond slot {N_SLOTS} under a doc "
                "amendment, so the allocation above exceeds the pre-registered α. The "
                "amendment text is in the table; families registered before it keep "
                f"their {SLOT_ALPHA}.**"
            )
        lines += [
            "",
            "---",
            "",
            "## The other programme controls",
            "",
            "This page is control 2 of seven. The rest, as the two docs write them:",
            "",
            "| # | Control | Where it is implemented |",
            "|---|---|---|",
            "| 1 | Sealed vault, 2025-03-01 → 2026-09-18, one look per model | not implemented "
            "— it is a property of a loader that does not exist yet |",
            "| 2 | Cross-document α allocation (this page) | "
            "`validation/programme.py:Registry` |",
            "| 3 | Programme-level Deflated Sharpe, two counts per Sharpe | "
            "`validation/programme.py:programme_dsr`, `programme_trial_count` |",
            "| 4 | 50% winner's-curse haircut, or the vault estimate if lower | "
            "`validation/programme.py:haircut` |",
            "| 5 | Episode concentration and shared-period dependence | "
            "`validation/episodes.py` |",
            "| 6 | One-bar-delay robustness and the leak canary | not implemented — both are "
            "properties of a runner that does not exist yet |",
            "| 7 | The forward consistency route also requires a vault pass | a rule, not code |",
            "",
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


def seed_registry(path: Path | str = DEFAULT_REGISTRY_PATH) -> Registry:
    """A `Registry` holding the seven families the deposit names, registered `SEALED_DATE`.

    Idempotent: families already present are left exactly as they are, and only the
    missing ones are registered, so calling this on a live registry cannot move a slot.
    """
    registry = Registry(path=Path(path))
    have = {f.name for f in registry.families}
    for name, doc, note in SEED_FAMILIES:
        if name not in have:
            registry.register(name, doc, registered_utc=SEALED_DATE, note=note)
    return registry


# --------------------------------------------------------------------------- the trial log


#: The union of the four documents' `trials.csv` column sets, plus `doc` and `family`.
#:
#: Taken in document order and de-duplicated, keeping each column's first appearance:
#: LETF §7, shock §8, index §9, ledger §11. `doc` and `family` are D592's additions and
#: are what makes `programme_trial_count` able to sum across documents at all — the
#: deposit's four schemas share only `trial_id`, `timestamp`, `cost_mult`, `mean_gross`,
#: `mean_net` and `notes`, so a pooled file with no provenance column could not be split
#: back into its documents.
TRIALS_COLUMNS: tuple[str, ...] = (
    # D592's provenance columns
    "trial_id",
    "doc",
    "family",
    # LETF_CLOSE_FLOW_PREREG.md §7
    "timestamp",
    "tau",
    "instrument",
    "k",
    "hold",
    "cost_mult",
    "event_filter",
    "n_trades",
    "mean_gross",
    "mean_net",
    "t_hac",
    "sharpe_net",
    # SHOCK_CLASSIFIER_PREREG.md §8
    "class",
    "z",
    "w",
    "c_hi",
    "c_lo",
    "s",
    "f",
    "exit_type",
    "fill_model",
    "t_clustered",
    # INDEX_REWEIGHT_FLOW_PREREG.md §9
    "stage",
    "construction",
    "year_set",
    "t0_offset",
    "gsci_stack",
    "n_obs",
    "p_boot",
    # SETTLEMENT_FLOW_LEDGER_PREREG.md §11
    "timing_rule",
    "t0",
    "flag_filter",
    "sizing",
    "flow_corr_oos",
    # last in every one of the four schemas
    "notes",
)

_REQUIRED_TRIAL_FIELDS = ("trial_id", "doc", "family")


class TrialsCsv:
    """An append-only `trials.csv` over the union of the four documents' schemas.

    Append-only in the sense the deposit needs: `append` refuses a `trial_id` the file
    already holds, and there is no update, no delete and no rewrite. *"Log every
    configuration evaluated, including failed and exploratory ones"* (LETF §0.4) only
    means anything if a row cannot be taken back out.

    The newline is pinned to `\\n` and the encoding to UTF-8 on both the read and the
    write, so a row logged on Windows and a row logged on Linux hash the same (D550).
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.columns = TRIALS_COLUMNS

    # -- read --------------------------------------------------------------------------

    def exists(self) -> bool:
        return self.path.exists()

    def rows(self) -> list[dict[str, str]]:
        """Every logged row, in file order. An empty list when the file does not exist."""
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            header = tuple(reader.fieldnames or ())
            if header != self.columns:
                raise ValueError(
                    f"{self.path} has header {header!r}, which is not the D592 union "
                    "schema; a trials.csv whose columns have drifted cannot be pooled"
                )
            return [dict(row) for row in reader]

    def count(self) -> int:
        """Rows logged. This is the number the programme trial counter sums (test 67)."""
        return len(self.rows())

    def trial_ids(self) -> set[str]:
        return {row["trial_id"] for row in self.rows()}

    # -- write -------------------------------------------------------------------------

    def append(self, row: Mapping[str, Any]) -> dict[str, str]:
        """Append one trial. Returns the row as written (every column, blanks filled).

        Raises on an unknown column, on a missing `trial_id` / `doc` / `family`, and on a
        `trial_id` already in the file.
        """
        unknown = sorted(set(row) - set(self.columns))
        if unknown:
            raise ValueError(
                f"unknown trials.csv column(s) {unknown}; the union schema is "
                f"{list(self.columns)}"
            )
        for key in _REQUIRED_TRIAL_FIELDS:
            if not str(row.get(key, "")).strip():
                raise ValueError(f"a trial row needs a non-empty {key!r}")
        trial_id = str(row["trial_id"])
        existing = self.trial_ids()
        if trial_id in existing:
            raise ValueError(
                f"trial_id {trial_id!r} is already logged in {self.path.name}; "
                "trials.csv is append-only and a trial is never re-logged or overwritten"
            )
        out = {column: ("" if row.get(column) is None else str(row.get(column, "")))
               for column in self.columns}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not self.path.exists()
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.columns), lineterminator="\n")
            if fresh:
                writer.writeheader()
            writer.writerow(out)
        return out


# --------------------------------------------------------------------- the trial counter


def programme_trial_count(
    census: Path | str = DEFAULT_CENSUS_PATH,
    trials_csv_glob: str = "data/**/trials.csv",
    repo: Path | str = _REPO,
) -> dict[str, Any]:
    """The programme-wide trial count, with the rule that produced it (test 67).

    Returns `etf_pool_distinct_configs`, `other_registries`, `trials_csv_rows`, `total`
    and `rule`. All four counts are dimensionless counts of TRIALS.

    The deposit's own definition (§13A.8(3), §12A(3)) is *"a programme trial counter sums
    the rows of every doc's trials.csv"* — that is `trials_csv_rows`, and today it is
    **zero, because no `trials.csv` exists anywhere in this repository and no futures
    runner logs a trial to any registry**. The other two terms are this repository's
    prior multiplicity, which the deposit's counter does not see and which a DSR computed
    on a shared fixture ought to: D90's whole argument is that a trial count cannot be
    reconstructed retroactively, so the counts that WERE captured live are carried.

    The two kinds of evidence are counted differently, and that is the `rule`:

      * **sqlite registries → distinct, de-duplicated config payloads.** The predicate is
        `scripts/run_macd_ladder.py:729-745 prior_etf_trials()`: *distinct logged config
        payload, de-duplicated across registries*. Re-running one window at a scaled cost
        multiplier is a sensitivity point, not an independent trial (D98). For the twelve
        ETF-fixture registries the de-duplicated pool is 45,346 against 129,286 raw rows;
        summing the per-registry column instead gives 97,966, about 2.2x the pool.
      * **`trials.csv` → rows.** A row there IS a configuration; the deposit says rows.

    `other_registries` covers the LIVE registries outside the ETF pool — the
    breakout/crypto line, a separate body of work — counted at their own distinct-config
    counts, which happen to equal their row counts. The superseded `breakout_study` copy
    and the 10-row demo registry are excluded. No cross-registry de-duplication was ever
    measured for these five, so this term is an upper bound on their pool and is reported
    separately rather than folded into the ETF number.
    """
    census_path = Path(census)
    if not census_path.exists():
        raise FileNotFoundError(
            f"{census_path} is missing; it is the committed census of the sqlite trial "
            "registries (scripts/build_trial_registries.py --build). The registries "
            "themselves are gitignored, so the count cannot be re-derived without it."
        )
    payload = json.loads(census_path.read_text(encoding="utf-8"))
    etf_pool = int(payload["etf_pool"]["distinct_configs_deduplicated"])
    predicate = str(payload["etf_pool"]["predicate"])

    others = [
        row
        for row in payload["registries"]
        if not row["in_etf_pool"] and row["status"] == "live"
    ]
    other_total = int(sum(int(row["distinct_config_json"]) for row in others))

    repo_path = Path(repo)
    csv_paths = sorted(repo_path.glob(trials_csv_glob))
    csv_rows = int(sum(TrialsCsv(path).count() for path in csv_paths))

    rule = (
        "sqlite registries are counted by DISTINCT DE-DUPLICATED CONFIG PAYLOAD, the "
        f"predicate of run_macd_ladder.py:729-745 prior_etf_trials() ({predicate}), "
        "because one window re-run at a scaled cost multiplier is a cost-sensitivity "
        "point and not an independent trial (D98); trials.csv logs are counted by ROWS, "
        "because a row there is a configuration and because the deposit's counter "
        "(SETTLEMENT_FLOW_LEDGER_PREREG.md 13A.8(3), OPENING_AGENT_STATE_PREREG.md "
        "12A(3)) says rows. etf_pool_distinct_configs is the 12-registry ETF-fixture "
        "pool de-duplicated ACROSS registries; other_registries is the live "
        "breakout/crypto line at its per-registry distinct-config counts, with no "
        "cross-registry de-duplication measured, so it is an upper bound; the superseded "
        "registry copy and the 10-row demo registry are excluded. trials_csv_rows is the "
        f"deposit's own literal count and covers {len(csv_paths)} file(s) matching "
        f"{trials_csv_glob!r}."
    )
    return {
        "etf_pool_distinct_configs": etf_pool,
        "other_registries": other_total,
        "trials_csv_rows": csv_rows,
        "total": etf_pool + other_total + csv_rows,
        "rule": rule,
    }


# ------------------------------------------------------------------------------- the DSR


#: A per-period Sharpe above this is almost certainly an annualised one (D98).
PER_PERIOD_SR_CEILING = 1.0


def programme_dsr(
    sr: float,
    t: int,
    skew: float,
    kurt: float,
    *,
    n_doc: int,
    n_programme: int,
    var_trials: float,
) -> dict[str, float]:
    """The two DSR values every reported Sharpe carries (ledger §13A.8(3)).

    *"Any reported Sharpe carries two DSR values: one with the doc's own trial count and
    one with the programme trial count. Promotion requires the programme-level DSR
    probability >= 0.95."*

    Returns `{"dsr_doc": ..., "dsr_programme": ...}`, both probabilities in [0, 1].
    `dsr_programme <= dsr_doc` always, because SR0 rises with the trial count.

    UNITS (D98). `sr` and `var_trials` are PER-PERIOD, non-annualised, in the same
    frequency as `t`, and `kurt` is RAW (3.0 for a normal). An annualised `sr` against a
    per-period `var_trials` inflates SR0 by sqrt(periods per year) and drives the DSR to
    zero for any strategy at all — the audit's one red finding. A `sr` above
    `PER_PERIOD_SR_CEILING` is therefore REFUSED rather than scored: a per-period Sharpe
    of 1.0 is 15.9 annualised on daily data, which nothing here has ever produced.
    """
    if n_doc < 2:
        raise ValueError(f"n_doc must be at least 2 trials, got {n_doc}")
    if n_programme < n_doc:
        raise ValueError(
            f"n_programme ({n_programme}) is below n_doc ({n_doc}); the programme pool "
            "contains the doc's own trials by construction, so a smaller programme count "
            "means the two were counted under different rules "
            "(see programme_trial_count's `rule`)"
        )
    if abs(sr) > PER_PERIOD_SR_CEILING:
        raise ValueError(
            f"sr = {sr} is not a plausible PER-PERIOD Sharpe (|sr| > "
            f"{PER_PERIOD_SR_CEILING}); the DSR units contract of D98 requires sr, "
            "var_trials and t in one non-annualised frequency. An annualised sr here "
            "inflates SR0 by sqrt(periods per year), about 15.9x on daily data, and "
            "forces the DSR toward 0 regardless of the strategy. Divide by "
            "sqrt(periods per year)."
        )
    return {
        "dsr_doc": deflated_sharpe_ratio(sr, t, skew, kurt, n_doc, var_trials),
        "dsr_programme": deflated_sharpe_ratio(sr, t, skew, kurt, n_programme, var_trials),
    }


# --------------------------------------------------------------------------- the haircut


def haircut(edge: float, frac: float = HAIRCUT_FRACTION, vault_estimate: float | None = None) -> float:
    """The winner's-curse haircut (ledger §13A.8(4), unit test 68).

    *"All sizing, drawdown planning and the Track 3 power check use 50% of the in-sample
    walk-forward edge estimate. If the vault estimate is lower than the haircut estimate,
    the vault estimate is used instead."*

    So: `frac * edge`, and `min(frac * edge, vault_estimate)` when a vault estimate is
    given. The units are whatever `edge` is in — sigma per trade, dollars per day, basis
    points — and `vault_estimate` must be in the SAME units, which this function cannot
    check and the caller must.
    """
    if not 0.0 < frac <= 1.0:
        raise ValueError(f"frac must lie in (0, 1], got {frac}")
    haircut_estimate = frac * edge
    if vault_estimate is None:
        return float(haircut_estimate)
    return float(min(haircut_estimate, vault_estimate))


__all__ = [
    "DSR_PROMOTION_BAR",
    "DEFAULT_CENSUS_PATH",
    "DEFAULT_PAGE_PATH",
    "DEFAULT_REGISTRY_PATH",
    "Family",
    "HAIRCUT_FRACTION",
    "N_SLOTS",
    "PER_PERIOD_SR_CEILING",
    "PROGRAMME_ALPHA",
    "Registry",
    "SEALED_DATE",
    "SEED_FAMILIES",
    "SLOT_ALPHA",
    "TRIALS_COLUMNS",
    "TrialsCsv",
    "haircut",
    "programme_dsr",
    "programme_trial_count",
    "seed_registry",
]
