# `docs/prop firm leads/` — leads toward an initial prop book

**What this folder is.** Working leads for the prop track: things that could become a candidate, a
measurement or a pre-registration. **Nothing here is a result, a decision or a book entry.**

**What it is not.**

> **No record in this folder closes anything, admits anything, or elevates anything.** Under
> [R8](../RULES.md#r8) every item needs a pre-registration committed **before** its runner exists;
> under [R15](../RULES.md#r15) **only the principal opens or closes an avenue.** Where a lead cites
> [`docs/research/`](../research/README.md) it cites it as **`[EXT]` evidence about the outside
> world**, never as a measurement on any fixture here — the standing ruling of 2026-09-09 is
> untouched.

**Where the authority actually lives:** [`BOOK_PROP.md`](../BOOK_PROP.md) (admitted arms: **none**) ·
[hurdle P, R11](../RULES.md#r11) · [`docs/decisions/`](../decisions/) · [`FINDINGS.md`](../FINDINGS.md).

---

## Contents

| | |
|---|---|
| **[01 · six leads, and one is unblocked today](01-prop-lead.md)** | recorded 2026-09-10 |
| **[02 · the data-acquisition prompt](02-data-acquisition-prompt.md)** | ready to paste. Covers `01` §6.1 — **we hold no futures data** |

## `01` in one screen

**The track's state.** [D258](../decisions/D258-the-prop-track-candidates.md)'s four candidates are
**all resolved** — C2 and C3 closed, C3 on **shape** rather than return; **C1 closed then reopened
and it clears P4** under vol-targeted sizing (0.48× average, **6.40-year expected life**, +4.41%/yr,
**28.20% expected profit before breach**). A fifth candidate needs **a new mechanism, not a new
parameter**.

| § | lead | status |
|---|---|---|
| ~~**1**~~ | ~~`D379 §4` is computable today — the MFF ladder terms are in the research folder~~ | **WITHDRAWN 2026-09-11 — D386 had already done it, on 2026-09-08** |
| ~~**2**~~ | ~~`P(pass)` is computable now~~ | **WITHDRAWN — it was COMPUTED**, `scripts/d386_pass_rate.py` |
| **3** | **C1's value-maximising size was never searched** — the sweep stopped at 0.48× where P4 cleared, and profit-before-breach falls monotonically **28.20% → 1.75%** across it | **absorbed into [D440](../decisions/D440-the-measured-path-through-the-lifecycle-model.md)** as an argmax of `V` |
| **4** | **The hold-length interior optimum.** The research's *"the scissors close on LONG windows"* and D259's MAE failure are **the same 4% bound moving in opposite directions with hold length. Nobody has drawn the curve** | a specification, not a candidate |
| **5** | **The T+0/T+1 settlement question** — C1's edge is measured on equity and would be traded as a future | **a kill-check on D440's input** |
| **6** | **Two constraints on all of it** — **we hold no futures data** (`$30` inside a `$125` credit), and every candidate should be screened on the **12-symbol complex at breadth 3.00**, not four equity indices at **1.17** | standing |

## WHAT HAS RUN SINCE, 2026-09-11

| | outcome |
|---|---|
| **[D440](../decisions/D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it-is-clustering-not-kurtosis.md)** — the measured-path join | **`T1` unresolved, `T2` FAIL, `T3` unresolved — not a candidate.** The Gaussian was carrying **88%** of the account's value, and **82–86% of the damage is CLUSTERING, not kurtosis** |
| **[R11 RULING](../RULES.md#r11)** — P4 means the **account's life** | **C1 does not clear P4.** D259's 6.40 years is a per-hold statistic; the account's is **0.14**. [`BOOK_PROP.md`](../BOOK_PROP.md) amended |
| **[D442](../decisions/D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the-rotation-null-and-the-mask-breaks-the-inactivity-rule.md)** — `O1`, the abstention rule | **`G1` PASS, `G2` FAIL on all four symbols, `G3` pass.** An exposure cut with a story — **the ledger's own sentence.** Plus an independent kill: **88 consecutive flat sessions against a 7-day inactivity rule** |
| **[D442 ADDENDUM](../decisions/D442-ADDENDUM-the-two-apparent-wins-were-selection-across-four-risk-fractions.md)** | two apparent wins were **selection across four risk fractions**; the premium the null was denied (**~+245**) was **larger than the effects it hid** |

**The prop candidate ledger is now empty of unscreened entries.** `O1` was the last one.

**Two rules earned that outlive both candidates:** a null must be scored on the **same statistic** as
the treatment — *count the choices the treatment was allowed and give the null every one* — and
**any gate that can go flat must report its maximum run beside its returns.**

## The one line to carry out of `01`

> ~~**What is newly actionable is the VALUATION half — and it was blocked on a number sitting in
> `docs/research/` the whole time.**~~ **AMENDED 2026-09-11.**
>
> **The valuation framework was already built — D386 models five MFFU plans under every published
> rule and names Rapid EOD as the vehicle at a break-even Sharpe of ~0.00. What is actionable is
> its INPUT: `d386_full_lifecycle` draws `rng.normal(...)`, so it values a GAUSSIAN trader, while
> D259 measured a real path whose p99 MAE sits exactly on the 4% floor. Nobody has run one through
> the other.**

## Order of work — reissued twice on 2026-09-11, current version in `01` §8

**~~the measured-path join~~ and ~~`O1`~~ have RUN.** What remains:

**the floor-lock check** → **the settlement check** → **re-run D440 on ES** → **a run-length-capped
gate** → **the hold-length curve.** Each needs its own pre-registration. **Only the ES re-run and
the hold-length curve wait on the futures data.**

## Related

| | |
|---|---|
| the consolidated research view | [`research/consolidated/venues/`](../research/consolidated/venues/00-index.md) |
| the prop firm campaign, 24 lanes | [`research/Prop-Firm-080926/`](../research/Prop-Firm-080926/00-SYNTHESIS.md) |
| the account as a down-and-out call | [D379](../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md) |
| the account is worth its buffer | [D386](../decisions/D386-the-prop-account-is-worth-its-buffer.md) |
| the hurdle audit — **P3, P4, P5 never computed** | [D375](../decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md) |
| C1's path measurement | [D259](../decisions/D259-the-extended-session-and-the-overnight-interior.md) |
