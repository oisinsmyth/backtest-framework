# D545 RESULT — the page exists, and three of the numbers it was built to quote turned out to have no artifact

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

*2026-09-18. Spec committed in `6c8e340` BEFORE the page existed (R8). Nothing admitted to either
book. No holdout read.*

**`docs/results/D190-D544.md` is written, linked and gated. Twenty figures, each pinned to a
`data/*.json` key. Three findings were cut and one prediction of mine was wrong before the record
was even committed.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | No published number moves | **HOLDS** |
| **P2** | The anchor gate fails on a single perturbed digit, naming the anchor | **HOLDS** |
| **P3** | With the floor added, emptying `test_writeup.py`'s `ANCHORS` fails | **HOLDS** |
| **P4** | At least one candidate finding is cut for being untraceable or open | **HOLDS — three were** |
| **P5** | The README sample executes; `trade_cost(100 @ $50) == 1.00` exactly | **HOLDS** |

### P2 and P3 — both gates proved, not assumed

Changing `+41.81` to `+41.82` on the page: **1 failed, 24 passed, exit 1**, and the failure names
`test_every_quoted_number_matches_its_artifact[c2b G2:T2 exact p95]`. The message says which
artifact disagrees and by how much.

`test_writeup.py` before the floor: emptying `ANCHORS` gave **29 passed → "3 passed, 1 skipped",
exit 0** — twenty-six checks gone, nothing red, in the gate whose job is keeping a document honest.
After: **1 failed, exit 1**. Sixth instance of the empty-scan defect this programme has closed, and
it was sitting in a file written to prevent exactly this class of rot.

### P5 — and the probe that lied to me first

`IBKRCommission()` on 100 shares at $50: per-share is $0.50, the minimum is $1.00, and
`trade_cost` returns **exactly 1.00**. A false assertion in the sample fails the suite; removing the
`# runnable` marker fails **two** tests — the block-presence check and the `SOURCES` floor.

**The first probe reported the marker case as passing, and the probe was wrong, not the gate.** It
keyed on `b"```python\n# runnable\n"` and `README.md` is CRLF, so the replacement matched nothing
and the suite passed for a reason that had nothing to do with what was being tested. *Breaking what
the assertion reads means breaking the bytes that are actually there* — and a probe that cannot
break the thing is indistinguishable from a gate that cannot catch it.

---

## What was cut, and why — P4

**D333 (thirty fabricated dividend days) and D388 (the density line)** were both verified,
artifact-backed and strong. They were cut for length: the page is six findings and both duplicate a
lesson already carried — D333's *"name the top trade"* is D340's second rule, and D388's *"beating a
shuffled path is not beating a rotated density"* is the same shape as the cohort-null kill in D373.
They stay in `docs/FINDINGS.md`, where they belong.

**Three genuinely could not be used:**

| candidate | why it was cut |
|---|---|
| the **sign-fitting floor** — a composite of sixteen pure-noise signals clears a best-of-16 selection floor by +1.28 | **No decision number.** It is a method probe with no fixture, and the correction it forces on D280 is a withdrawn *inference*, not a withdrawn number. |
| **`etf_wide_daily_raw` is not an ETF fixture** — 27.2% carry a closed-end-fund distribution signature, terminal wealth understated 5.37× over 16 years | **Resolves to "the principal's call".** No record is withdrawn and no metadata is edited, so it is an open item, not a finding. |
| **the half-spread is a range estimator** (D439) — the kernel charges a median 28 bp a side on names whose quoted half-spread is 1–2 bp | **The fix is explicitly unrun.** D336's quote pull needs a TWS session that has not happened. The repository's own highest-value unrun measurement is not a result. |

---

## What the survey corrected in this record's own pre-registration

**The centre-bias theorem is C2b's, not D373's.** This record's first draft credited D373 with *"a
sample p95 is biased toward the centre"*. D373's pre-registered rule is the **2-SE UNRESOLVED
band**; C2b's is the theorem, and C2b names D373 as a precedent that *"is simply not universal"*.
Caught before the page was written and pinned by a test, because the distinction is load-bearing:
one is a fact about sampling, the other a reporting standard.

**Three of the numbers this lane set out to quote have no artifact — and it kept them, as
withdrawn.** D466's **0.62 / 0.42** at ρ 0.09 and the **0.91** book were computed outside the
runner, in basis points at full-size cost. `CLAUDE.md`, the working notes and D466 §0 were all
written on them. Only the corrected **+0.369 (SE 0.322)** and **−0.011** exist in
`data/d466_components.json`, with `entered = []`.

Under this record's own gating rule those three fail, so the page quotes them **as withdrawn,
beside the pair that replaced them**, and says why: *a number that never passed through a runner
cannot be sourced, cannot be gated, and gets believed anyway.* That is the page's sharpest
paragraph and it exists because the gate refused the figures.

---

## The directory's own description of itself was false

**Every `.md` in `docs/results/` is a script's output** — including the ones its index called
*"hand-written analysis pages. A human decided what to say."* A human did, and said it **in the
runner**: `scripts/run_vol_estimator_gate.py:111` writes the H1 of `vol_estimator_gate.md`.

This matters beyond tidiness. `tests/unit/test_quoted_counts_are_current.py:53` exempts the whole
directory from its number sweep with the reason *"study ledgers emitted by a runner; regenerating
the study rewrites them"*. **A hand-written page dropped there inherits a no-gate exemption written
for files a runner owns** — no sweep, and no regeneration either.

The page still goes there, because `final_report.html` is the one other genuinely hand-written
document in the directory and is the narrative of phase one; this is its successor and belongs
beside it. It brings its own gate, and the index now states the exception instead of denying it.

---

## A28 — the README has its first line of Python

Three fenced blocks before this, two `bash` and a directory tree. `CostStack` appeared nowhere in
`README.md` — not in a fence, not in prose — and the first pointer to a usable example was an
outbound link on line 203. There is now a stack assembled from three bricks at their three scopes
at **line 56**, with one hand-checkable assertion.

**It is extracted, not pasted.** `tests/integration/test_tutorial.py` now takes a list of sources,
because copying the tutorial's code into the front page would create precisely the failure
`README.md` itself names: *"two copies of the same prose drift apart — the most repeated defect in
this project's own history."* Extending the extractor gates both copies; copying would gate
neither.

**The front-loading half is reported, not acted on.** The claim was ~70 of the first 130 lines are
commentary on past errors. Classified over 109 content lines: **38 what the framework is or does,
51 measured claims, 20 past-error commentary** — strict self-correction is **18%**, not 70 lines.
The sharper fact: **lines 61–102 are 42 consecutive lines with no framework content at all**.
Restructuring the front page on a reviewer's taste is the principal's call, not a documentation
lane's.

---

## What this record does not settle

Whether `docs/FINDINGS.md` would have been the better home. It is not FROZEN in the counts gate, so
numbers there are swept and kept current — an advantage given up in exchange for sitting beside
`final_report.html`, which is where the README's own spine sends a reader. The dedicated gate closes
that gap for twenty figures and is a narrower instrument than the sweep.

Whether the other three cut findings should ever get a page. Two are complete and were cut only for
length; one is open.

**And the page will go stale.** It is dated on its face for that reason, as `final_report.html` is.
Twenty numbers are pinned; the prose around them is not, and no test can tell you that a finding
has been superseded by a study run after it.
