# D544 — The front page is the least honest document in the repository, and the proposed citation gate would have fired on correct citations

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Documentation integrity
**Source:** Lane 8 of the two-reviewer audit (`working/REVIEW_REMEDIATION_PLAN.md` §9, nineteen
items). Committed before any document is edited (R8).

## The pattern, which is worth more than any single item

Verifying these nineteen produced one finding that none of them is: **in every case where the
README and a subordinate document disagree, the subordinate document is the honest one.**

| the front page says | the record says |
|---|---|
| "clears six of seven hurdles" (`README.md:16`, no metric) | D217: under a total-return reading of hurdle D, **"0 of 12 cells clear D"** |
| "penny-exact" (`:25`, no scope) | `VERIFICATION.md:88` states the scope **and** pre-empts this reading: *"true of that scope"* |
| "regenerated and checked in CI" (`:40`) | `VERIFICATION.md:215`: *"**It has never run on a machine that is not this one.**"* |
| "every example executed verbatim" (`:192`) | `test_tutorial.py` runs **10 of 12**; the 11th is a `SyntaxError` |

`VERIFICATION.md`, `CONTRIBUTING.md`, `.gitattributes` and D217 each carry the qualification the
front page drops. **This is a summarisation problem, not a record-keeping one** — and the front
page is the page a reviewer reads.

## The review was loose on more than half of this lane

Every item was re-measured rather than taken. What the review got wrong:

| item | review | measured |
|---|---|---|
| **A12** | "10 of 12 **README** examples run" | The claim is about `docs/TUTORIAL.md`. README has **3** fences, none Python. Substance survives; the scoping was wrong. |
| **A16** | "fails **only** the DSR floor" is false | README says "buy-and-hold **on Sharpe**" — the reading D217 says *counts*. The line is defensible; **the header table is not**. |
| **A20** | 37 missing, 14 explained, 22 never allocated | 37 ✓, but **14 + 22 = 36 ≠ 37**. Unexplained block is **23**; **15** carry a reason; exactly **one** (D390) was ever committed. |
| **A23** | docstrings at `:270`/`:285`, truth 274/2/272/45 | Lines are **304/319** (+ comments at `:98`/`:101`); truth today is **290 / 2 / 288 / 47 of 85** — wrong on three of four. |
| **A24** | three stale counts: 745 records, 46/11 modules, 502 numbers | Only **745** is stale. **46/11 is correct today.** **"502" appears nowhere in the repository.** 1 of 3. |
| **A5** | the README is silent on the never-run CI | `README.md:219` **does** disclose it — 179 lines below the caption, never connected to it. |
| **B17** | a verification runner *reads* a panel from `temp/`; "the only such site in 585 runners" | **Wrong.** `:35` is a *definition*; the script **writes** that file itself at `:50-54` and consumes it in the same invocation — which is what `temp/` is for. **33** tracked runners genuinely read from `temp/`, and no measurement in the repo yields **585**. |

## Three findings neither review had

1. **`README.md:113` says "six generated SVGs". There are twelve** — six figures, light and dark.
   `VERIFICATION.md:135` says twelve and is right; `docs/figures/README.md` says "Six pictures" and
   is also right. Only the map line is false.
2. **`VERIFICATION.md` contradicts itself about the same number**: `:143` says `scripts/` is **603
   runners**, `:173` says **592 one-shot runners**. Both are ungated. (603 is all tracked
   `scripts/*.py`; 595 excludes `scripts/figures/`; 592 is stale.)
3. **The decision-index gate and its own generator are on different universes, which the gate's
   rationale explicitly denies.** `test_decision_index_is_complete.py:32` uses `^D0*(\d+)[-.]`;
   `build_decision_register.py:132` uses an unanchored `D\d+`. So `D315a-RESULT-…` is **rendered
   into the index** (`docs/decisions/README.md:377`) and **invisible to the test**. It is harmless
   only because a plain `D315-` sibling exists; a `D<n>a-` record without one would be generated
   and then flagged as a phantom by the gate's own sibling test.

## The citation gate: the prescription would have fired on correct citations

The review proposed requiring a backticked symbol beside each `path:line` anchor and asserting it
appears **within ±3 lines**, describing it as closing the class "for ~20 lines". Measured across
**187** citations in tracked `.md` and `src/`/`tests/` docstrings (plus 10 in committed artifacts):

- **53 of 187 (28%)** carry a backticked symbol within 45 characters on the same line. **134 (72%)
  carry none** and are uncoverable by that rule.
- Widening to "the line before" reaches 66% but makes each row of `AUDIT_REPORT.md`'s citation
  table inherit its neighbour's symbols — ~20 spurious flags.
- **It has a false-positive mode on correct citations.** `ARCHITECTURE.md:201` cites
  `engine/risk.py:61` for `evaluate(...) -> RiskViolation | None`. Line 61 **is** that return
  annotation — a correct anchor — but `def evaluate(` is at `:55`, six lines above, so a ±3 check
  reddens it. Same shape at `ARCHITECTURE.md:51`.

At 28% coverage it would catch **3 of the 7** known-wrong anchors while flagging correct ones.

**So the convention stands and the proximity rule is replaced by scope resolution.** The gate
resolves the cited line to its **enclosing `def`/`class` via AST** and asserts the backticked
symbol names that scope or something in it. `risk.py:61` resolves to `evaluate` and passes;
`base.py:16` resolves to the module docstring and fails, which is the defect. Where no symbol is
adjacent, the citation is counted and reported rather than silently skipped, and the covered
subset carries a floor so it cannot empty.

## Decision

1. **The front page carries its records' qualifications** — metric on the hurdle count, scope on
   "penny-exact", the CI clause dropped at its source in `render()`, and the tutorial claim
   corrected to 10 of 12 with the 11th block made parseable.
2. **The index discloses; nothing is renumbered.** Nine numbers name two studies each (D440, D472,
   D473, D495, D497, D498, D504, D506, D508) — D507's amendment already rules that reassigning a
   number is the principal's call. The 23 never-allocated numbers and the tracked `DRAFT-` record
   each get a line, and the two regex universes are reconciled.
3. **Citations are fixed and gated by enclosing scope, not by line proximity.**
4. **Self-counts that `counts()` already computes are gated**; the ones it does not are corrected
   and the contradiction between `VERIFICATION.md:143` and `:173` is resolved.
5. **An author-absolute path in a committed artifact is disclosed, not rewritten.**
   `a1_er_stage0.json:4` records a fixture inside a deleted git worktree and
   `d520_fixture_diff.json:2` records one inside `temp/`; both are **unresolvable by anyone**, and
   silently rewriting them to something plausible would destroy the only evidence of that. The
   generators are fixed; the artifacts are noted.

## Predictions

**No count is predicted.** Three attempts in this programme, three misses — B26 (272 → 284,
predicted 278), D542's P6 (+4, predicted +1), D543's P5 (+0 where +1 and +1/+2 were predicted) —
and the last two shared a cause: naming a guard in a tree the counting gate does not read. D543's
RESULT recorded the usable rule, *do not predict a count until the artifact that moves it exists*,
and this record follows it by predicting **behaviour** instead.

| # | Prediction | Confidence |
|---|---|---|
| **P1** | The citation gate, resolving by enclosing scope, **passes `ARCHITECTURE.md:201` and `:51`** (the ±3 rule's false positives) and **fails `ARCHITECTURE.md:71`** (whose cited line is module-docstring prose). | High |
| **P2** | Its coverage is **higher than 28%**, because a symbol naming an enclosing `def` need not sit within 45 characters of the anchor. The figure is reported, not guessed. | Medium |
| **P3** | **No published number moves.** A19 is a caption, A16 and A21 are qualifications, A12 repairs a block that never ran. The only artifacts that change are the two `cost-waterfall` SVGs, and their arithmetic (817.3463) is byte-identical. | High |
| **P4** | Every new gate is demonstrated to **fail on a deliberate break before it is trusted**, and every new scan carries a **floor**. | High |

P1 is the falsifiable one: it names two citations that must pass and one that must fail, before the
gate exists.

## What this record does not settle

Whether the 64 citations concentrated in the frozen `docs/internal/AUDIT_REPORT.md` are correct.
21 of 187 were hand-verified and 7 were wrong; the rest are gated going forward but not audited
backwards, and a frozen document is not edited to satisfy a gate written after it.

Whether `D508` should be renumbered. D507's amendment is explicit that this is the principal's
call, and this record does not take it.
