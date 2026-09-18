# D544 RESULT — the citation gate flagged its own docstring, and its coverage is a quarter of what the audit implied

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1
above is the full title.*

*2026-09-18. Spec committed in `5a9db40` BEFORE any document was edited (R8). Nothing admitted to
either book. No holdout read.*

**Nineteen document items closed, three gates added, and the largest single lesson is about the
gate I built rather than the defects it found.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | The scope-resolving gate **passes** `ARCHITECTURE.md:201` / `:51` and **fails** `ARCHITECTURE.md:71` | **HALF FALSIFIED** |
| **P2** | Coverage is higher than the ±3 rule's 28% | **FALSIFIED** — it is lower, and honestly so |
| **P3** | No published number moves; only the two `cost-waterfall` SVGs change | **HOLDS** |
| **P4** | Every new gate demonstrated to fail on a deliberate break; every new scan carries a floor | **HOLDS** |

### P1 — the failing half confirmed, the passing half was never checked at all

`ARCHITECTURE.md:71` cites `instruments/base.py:16` for `@runtime_checkable`. Restored to `:16`,
the gate reports *"which is in no def/class (module level)"* and fails. **Exactly as predicted**,
and it is the real defect: line 16 is module-docstring prose about `Equity.margin_requirement`.

The other half is wrong, and the distinction matters. `ARCHITECTURE.md:201` cites
`engine/risk.py:61` in the form `` `evaluate(...) -> RiskViolation | None` (`engine/risk.py:61`) ``.
That backticked text is **not a bare identifier**, so the symbol pattern does not match it and the
citation is **not checked at all**. P1 said it "passes". It is skipped — which looks identical
from a green run and is a different statement entirely.

**I found this by deliberately breaking that exact citation and watching nothing happen.** A gate
that silently skips what you believe it is checking is the defect this programme keeps finding in
other people's work; it took one deliberate break to find it in mine.

### P2 — falsified, and the honest number is a quarter of the audit's

The audit measured 187 citations, of which 53 (28%) carry an adjacent backticked symbol, and
described the gate as closing the class "for ~20 lines". Built and measured:

| | |
|---|---|
| citations in maintained prose | **48** |
| of those, carrying a checkable symbol | **12** |

The corpus falls from 187 to 48 because **decision records are excluded**, and the second reason
for that was found by building the gate rather than by planning it: **a record routinely quotes a
wrong anchor in order to correct it.** D542 cites `fast_null.py:224` precisely to say the drop is
at `:243`. A gate cannot tell a quoted error from a made one, and reddening a correction is worse
than the drift it prevents.

**Then the gate flagged its own docstring**, for exactly the same reason — it cites
`engine/backtest.py:490-492` and `instruments/base.py:16` as the wrong anchors it exists to catch.
A file whose subject is bad citations cannot be checked by a gate that cannot read intent.

So the instrument covers the surface that actually changes — `ARCHITECTURE.md`, `VERIFICATION.md`,
the README, `CONTRIBUTING.md`, `TUTORIAL.md`, `src/`, `tests/` — which is also where drift does the
most damage, because those documents are edited and their anchors move underneath them. **12 is a
small number and it is stated in the gate's own docstring rather than left to be inferred.**

### The rule the audit proposed would have been worse than useless

Measured before building: the ±3-line proximity rule **fires on correct citations**.
`ARCHITECTURE.md:201`'s anchor points at the return annotation — a correct and useful anchor — but
`def evaluate(` is six lines above. The first draft of the scope-only rule was no better: it
produced **seventeen false positives**, because the common citation names a *local* at the anchor
(`impulse_nodz` at `macd.py:484`) rather than the function containing it.

The rule that works is the **union**: enclosing scope **or** within ±3 lines. Strictly more
permissive than either alone, and it still fails every anchor D544 set out to catch.

---

## Seven wrong anchors, and one of them was two hours old

| citation | said | is |
|---|---|---|
| `ARCHITECTURE.md:71` | `instruments/base.py:16` | `:33` |
| `ARCHITECTURE.md:202` | `backtest.py:490-492` | `:359-361` |
| `test_cited_decisions_exist.py:3` and `:144` | `check_doc_links.py:8` | `:12` |
| `test_the_golden_master.hand.json:3` | `test_the_golden_master.py:66-71` | `:12-13` |
| `cross_engine_residuals.json:19` | `test_cross_engine.py:27` | `:29` |
| **`D542:14`** | `analytics/metrics.py:74` | `:207` |

The last was written in this session, two hours before the gate that caught it. **The anchor was
wrong the moment it was typed**, because the line it named moved during the same commit that
named it.

---

## The review was loose on more than half of this lane

| item | review | measured |
|---|---|---|
| **A12** | "10 of 12 **README** examples" | The claim is about `TUTORIAL.md`. README has 3 fences, none Python. |
| **A16** | "fails **only** the DSR floor" is false | Defensible — README says "on Sharpe", the reading D217 says counts. **The header table** was the indefensible one. |
| **A20** | 37 missing, 14 explained, 22 never allocated | **14+22 = 36 ≠ 37.** Unexplained block is **23**; **15** carry reasons; exactly **one** (D390) was ever committed, taken three times. |
| **A23** | docstrings at `:270`/`:285`, truth 274/2/272/45 | Lines **304**/**319** plus comments at `:98`/`:101`; truth **290 / 2 / 288 / 47 of 85** — wrong on three of four. |
| **A24** | 745 records, 46/11 modules, 502 numbers | Only **745** stale. **46/11 correct.** **"502" appears nowhere in the repository.** 1 of 3. |
| **A5** | README silent on the never-run CI | `README.md:219` **does** disclose it, 179 lines below the caption. |
| **B17** | a verification runner *reads* from `temp/`; "the only such site in 585 runners" | **Wrong.** `:35` is a definition; the script **writes that file itself** at `:50-54` and consumes it in the same invocation, which is what `temp/` is for — its own docstring says so. **33** runners genuinely read from `temp/`, and no measurement yields **585**. **No fix was needed.** |
| **A18** | `.claude/hooks/test_*.py` break pytest | Real but **latent**: `testpaths = ["tests"]` and pytest skips dot-directories, so the configured run never reaches them. A trap, not a broken suite. Renamed anyway — it costs nothing. |

## Five findings neither review had

1. **`README.md:113` said "six generated SVGs". There are twelve** — six figures, light and dark.
2. **`VERIFICATION.md` contradicted itself about the same number**: `:143` said `scripts/` is 603
   runners, `:173` said 592.
3. **The index gate and its own generator were on different regex universes**, which the gate's
   rationale explicitly denied. `D315a-RESULT-…` was **rendered into the index** and **invisible
   to the test** — harmless only because a plain `D315-` sibling existed. The pattern is imported
   now, not restated, and a test asserts both classify every tracked basename identically.
4. **The runtimes were inverted, not merely divergent.** README said 3m31s here and 5m45s on a
   clone; CONTRIBUTING said 6–7.5 min here and 2m56s on a clone. Both cannot be true about which
   is faster. **Eight runs measured today span 3m48s to 5m52s** and contradict both.
5. **A count pattern that matched a bare comma.** `([\d,]+)` in a new gate fed `int(',')` and died
   with a `ValueError` instead of a verdict. Every pattern in that file shares the loose form and
   has been lucky; the new ones are `(\d[\d,]*)`.

---

## What changed, and what deliberately did not

**The front page carries its records' qualifications.** "Regenerated and checked in CI" is gone —
it was a hard-coded literal inside a block captioned *"Generated … rather than typed"*, and the
same file excluded `scripts/figures/` from the one-shot count **because "CI re-runs them on every
push"**, a rationale resting on something that has never happened.

**`BOOK_PROP.md` is amended, not edited.** It said "Admitted arms: ONE" four lines above "It is
empty". The paragraph stays: deleting it would remove the only evidence the book was ever empty,
which is the point the paragraph was making.

**The dividend stopped being called a friction** in the repository's thesis picture, against
`costs/bricks.py` — *"flows are economic transfers, not frictions"*. Two words, two SVGs, and
**817.3463 is byte-identical**.

**An author-absolute path in a committed artifact is disclosed, not rewritten.**
`a1_er_stage0.json` records a fixture inside a deleted git worktree and `d520_fixture_diff.json`
one inside `temp/`. Both are unresolvable by anyone, including their author — and **that is the
record**. Rewriting them to something plausible would destroy the only evidence that the
provenance is gone. The generators now write repo-relative paths so the next run adds no more.

**Nothing is renumbered.** D507's amendment already ruled that a decision number is an identity.

## What this record does not settle

The 64 citations in the frozen `docs/internal/AUDIT_REPORT.md`, and the drifted anchors inside
older decision records. Both are excluded by design, and a frozen document is not edited to
satisfy a gate written after it.

Whether the other 36 citations in maintained prose are correct. They carry no backticked symbol,
so this instrument cannot see them, and **that is stated in its docstring rather than implied by a
green run.**
