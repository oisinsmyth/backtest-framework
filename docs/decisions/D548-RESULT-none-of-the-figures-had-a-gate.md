# D548 RESULT — the page moved, and measuring it found that none of the figures on it had a gate

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

*2026-09-19. Spec committed in `6675ab2` BEFORE the move (R8). Nothing admitted to either book. No
holdout read. No runner touched.*

**The 42 lines are off the front page. Two of four predictions were wrong, and the one that was
most wrong is the useful one: the sentence I wrote into the new page was false, and the check
written to confirm it is what proved it.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | No published number changes | **HOLDS** |
| **P2** | `check_doc_links` reports one more document and **0 unresolved** | **FALSIFIED on the first run** — one more document, **2 unresolved**, for a reason worth keeping |
| **P3** | Perturbing a figure in `docs/RUNNING.md` reddens the counts sweep, naming the new page | **FALSIFIED** — it reddens nothing, and neither do six others |
| **P4** | The front page's longest run of lines with no framework content falls below 20 | **HOLDS** — 42 → **13** |

---

## P3 — the finding, and it is bigger than the prediction

**Seven figures from the moved text were perturbed one at a time, each against the whole unit
tier. The suite stayed green on all seven.**

| figure | caught? |
|---|---|
| the clone's `2,017 passed` | no |
| the clone's `53 skipped` | no |
| `85 characters or shorter` | no |
| `49 of the 53` skips name a file | no |
| the manifest's `118` panels | no |
| the `115` panels carrying a blob id | no |
| D536's `844 MB` | no |

`tests/unit/test_quoted_counts_are_current.py` sweeps quantities it can **compute from the git
index** — decision records, decision numbers, test counts per tier, scripts, modules, `raise`
statements, guard files. **None of these seven is one of those**, so the sweep never looked at
them. I had assumed "living document ⇒ swept" and that is not what the gate does.

**So the sentence D548 told me to write was false.** The amended rule, as first drafted into
`docs/RUNNING.md`, said pass and skip counts *"are gated, so they may appear wherever they are
useful and cannot drift apart."* They are not gated. `docs/VERIFICATION.md:188-190` carries the
same clone figures and **nothing stops the two drifting apart** — which is the exact failure D544
was written about, still live, in the sentence claiming it was solved.

The page now says that, with the measurement.

### And D544's stated reason was too generous

D544's rule is that runtimes live in one place *"because they are the only numbers in this
repository that no gate can hold."* The premise is wrong: **they are not the only ones, they are
just the only ones anybody noticed.** Every figure in the 42 lines was in the same position.

## What was built in response

`tests/unit/test_running_page_figures.py` — six tests. It pins the **three of seven that are
computable**, each as a literal beside a callable that recomputes it:

| anchor | source |
|---|---|
| `118` panels | `len(data/data_manifest.json["files"])` |
| `115` with a blob id | the count with a non-null `git_blob` |
| `85` characters | `max(len(p) for p in git ls-files)` — and it is exactly 85 |

Plus the stronger half the counts could not give: **the three panels with no blob id are checked
as a set, not as a number.** `115` would still pass if one panel lost its blob and another gained
one, and the page's three filenames would then be wrong while its count was right.

The other four are genuinely ungateable — a property of a machine, of a clone, or of history — and
the test's docstring lists them by name rather than letting the page look better covered than it
is.

---

## P2 — falsified by a gate doing its job

The first `check_doc_links` run after writing the page reported **2 unresolved**:

```
README.md:87:  docs/RUNNING.md -> on disk but NOT in git; a reader gets nothing
README.md:207: docs/RUNNING.md -> on disk but NOT in git; a reader gets nothing
```

The page existed. It was not staged. **The link checker measures from the index, not the
worktree**, and refuses a target a reader would not receive — the same distinction that produced
D540, the manifest work, and the clone-measured skip counts. Both resolved on `git add`.

I predicted 0 unresolved because I was thinking about whether the *path* was right. The gate was
thinking about whether a reader gets the file.

---

## P4 — 42 → 13, and the category it is scored on

The front page's longest run of consecutive lines with no framework content is now **13**
(lines 76–88): the two commands, *"That runs on a bare clone"*, and the three-line pointer. The
next longest are 5 and 4.

**Scored on D545's categories, and that is worth stating.** Under a stricter reading — counting any
line that does not describe the framework itself — there is a 38-line run at 16–53: the figure's
caption, the header table, the generated counts block. D545 classified those as *measured claims
about the repository* (51 of 109 lines) and treated them as the page's intended shape, because the
evidence is what the front page is for. The 42-line run was singled out for being about the
**development environment**. P4 holds on that category; on the stricter one it does not arise,
because that material was never the complaint.

---

## What moved, exactly

`docs/RUNNING.md` carries all three blocks. **The prose is verbatim.** The only edits:

- **Link targets rebased** one directory down — `](docs/decisions/…)` → `](decisions/…)`,
  `](CONTRIBUTING.md)` → `](../CONTRIBUTING.md)`, and the manifest link likewise.
- **The rule sentence rewritten**, as D548 said it would be, and then rewritten again when P3
  falsified the first rewrite.

`README.md`'s `## Five minutes` goes from 52 lines to 12. `CONTRIBUTING.md:138` points at the new
home; the Doc suite gains a **Live** entry.

### The rule was already broken in three places, and the move is what found it

**`0.58s` — the golden suite's wall-clock time — was on the front page, in `CONTRIBUTING.md:137`,
and in `docs/TUTORIAL.md:21`.** The third was spelled `~0.6s`: an *approximate* copy of an exact
figure, which is how the D544 inversion began. All three now carry the command without a timing,
and the figure lives once, on the page whose subject it is.

Nothing was renumbered. Removing a duplicate is not moving a number.

---

## What this record does not settle

**Whether the clone figures should be gated at all.** They cannot be, from inside the working copy;
gating them means a CI job that clones and runs, which this repository does not have and which its
own README says has never run. Until then `docs/RUNNING.md` and `docs/VERIFICATION.md` carry the
same two numbers on trust, and both now say so.

**Whether `test_quoted_counts_are_current`'s scope should widen.** It sweeps what it can compute.
Everything it cannot compute is, by construction, invisible to it — and the census above is the
first time anyone asked how much that was. Seven figures on one page is not an estimate of the
whole tree.

**Whether the front page's 16–53 block is too long.** It is the page's evidence and it is
generated or gated throughout, so it is not the same problem. It is a different question and it
stays the principal's.
