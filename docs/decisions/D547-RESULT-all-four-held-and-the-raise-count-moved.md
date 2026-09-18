# D547 RESULT — all four predictions held, and deleting a research module moved a number in the verification document

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

*2026-09-18. Spec committed in `d204284` BEFORE anything was deleted (R8). Nothing admitted to
either book. No holdout read.*

**987 lines of S5b and two saved 429 bodies are gone. Four of four predictions held — the first
clean sweep in this programme — and the only surprise came from a count nobody was looking at.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | Deleting the JSON without emptying `ALLOWED` reddens exactly one test, naming both paths; emptying it turns the file green | **HOLDS**, both halves run |
| **P2** | The collected total falls by **exactly 48**, 2,221 → 2,173, nothing outside S5b's own test fails | **HOLDS exactly** |
| **P3** | No documentation gate reddens | **HOLDS** |
| **P4** | `terrain_swing.py` and its five dependents import cleanly; ruff and mypy stay green | **HOLDS** |

### P1 — the gate asked to be edited, in those words

`git rm` on the two files with `ALLOWED` still populated: **1 failed, 3 passed**, and the failure is
`test_the_allow_list_is_still_earned`, naming both paths as *"no longer present, so remove it from
ALLOWED"*. Emptying the list: **4 passed**.

That is the re-derivation doing exactly the job it was written for, in the direction it was least
likely to be exercised. It was built expecting a *refetch*; what actually happened was a deletion,
and it caught that too because it checks existence and parseability separately.

### P2 — exactly 48

**2,221 → 2,173.** Eight tests failed on the way, and all eight were counts gates
(`test_quoted_counts_are_current` ×7, `test_readme_counts_are_current` ×1) reporting numbers that
the deletion had made stale. **Nothing failed because something depended on S5b.**

That was the prediction worth being wrong about: a fall of more than 48 would have meant a
dependency invisible to a name search. The name search was right, and `terrain_swing.py` — the
parent, which three `src/` modules and two runners import — is untouched.

### P4 — and the number that confirmed it in passing

`mypy` reports **84 source files** where it reported 85. S5, `structure.py`, `terrain_field.py`,
`terrain_strategies.py`, `ragged_structure_scores.py` and `run_d403_wick_potential.py` all import
cleanly.

---

## The thing nobody predicted, and the gate that caught it

`docs/VERIFICATION.md:96-97` says, about proving guards fire:

> `src/` carries **288 `raise` statements**, spread across **47 of its 85** tracked `.py` files

**S5b carried 8 of those raises.** So deleting a research module that no runner used moved a
headline number in the document about *how this repository verifies itself* — to **280 across 46 of
84**.

Nobody would have thought to check that. `test_the_quoted_raise_count_is_the_non_bare_one` and
`test_the_quoted_guard_file_split_is_current` did, and they are in the suite because Lane 8 put
every quoted number under a sweep. **A gate written for stale documentation caught a consequence of
a deletion three lanes later, in a file the deletion had no obvious relationship to.** That is the
argument for sweeping counts rather than pinning the ones you remember.

Nine prose lines carrying ten numbers were bumped across five documents: `PHILOSOPHY.md`,
`README.md` (×3), `docs/TUTORIAL.md`, `docs/VERIFICATION.md` (×4).

---

## What S5b was, kept so that the hypothesis outlives its apparatus

Retiring an instrument is not a verdict on its question, so the question is recorded rather than
deleted with the code:

> *a level that has been probed and rejected is not the same object as a level that has never been
> touched from the wrong side, even though S5 scores them identically.*

The mechanism was `strength_multiplier = (1 - decay) ** pierces` at `DECAY_PER_PIERCE = (0.1,
0.25)`, cumulative over the formation→index walk that already counted tests.

**And the sharp negative it had already established**, which is the reason retiring it costs less
than 987 lines suggests: S5b emitted the **same level set as S5 at every index, always**. S5's kill
test reads `close` alone, so a wick that closed back was already survivable under S5. The entire
difference was the *score* on identical levels — a re-weighting test, not a survival test — and
**the re-weighting was never measured against anything**. The apparatus was built, gated by 48
tests, and the comparison it existed to make was never run.

`terrain_swing.py` and this record are enough to rebuild it, and git holds the original at
`d204284~1`.

---

## What the JSON gate looks like now

`ALLOWED` is **kept and empty**, typed `dict[str, str]`, with a comment saying that adding an entry
is a decision rather than a fix: name the file, why it cannot parse, and whose call its removal is.
The re-derivation stays, because an empty list that is still checked is the state the gate should
rest in.

Its docstring now records **what it still cannot see**: an error body that happens to be valid
JSON. The two that prompted it were HTML and could not parse; a 200-byte `{"error": "rate limited"}`
would sail through. The mechanism that produced both — `data/D3_fetch.py:31`, which writes the
response body under the requested filename whatever the status was, reporting the code afterwards
rather than checking it — is still there and is the principal's to change.

---

## What this record does not settle

**`data/D3_fetch.py`.** One status check would have prevented both files. It is evidence, the gate
catches the outcome, and it is noted rather than patched.

**Whether any tracked artifact is a saved error body that parses.** Nothing here looks for that,
and the two this programme found were only findable because they did not parse.

**Whether `docs/VERIFICATION.md`'s guard-coverage numbers should be generated rather than prose.**
They are the third set of hand-written counts in that document to go stale in this round, and they
went stale because of a change with no connection to them. The sweep catches it every time, which
is an argument for the sweep and also an argument that these particular numbers want a generated
block.
