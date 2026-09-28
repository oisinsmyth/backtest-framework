# working/

**Files in active use that are not yet part of the repo's record.**

The distinction from [`temp/`](../temp/) is *time*, not importance: losing
something here would cost real work **right now**, whereas `temp/` is safe to
empty at any moment. **When a file here stops being needed, it moves to `temp/`
— it does not linger.**

**Contents are NOT tracked, as of 2026-09-28.** They were, "precisely because losing in-flight
work is expensive" — and 137 tracked files showed that the rule above was not being followed, so a
clone received 87 one-off diagnostics, drafts, CSVs, logs and PNGs it could not interpret.

What is still tracked is what the record depends on: the `leads*/` research corpus that
[`docs/research/`](../docs/research/README.md) is built on, and the handful of files that tracked
decision records cite. `.gitignore` lists them by name, so adding a file here leaves it untracked
unless someone says otherwise in writing.

**Nothing was deleted and the history keeps every version committed up to that date.** What changed
is that a *future* edit in here is no longer backed up by a push — which makes the rule above load
bearing rather than advisory. **When a file stops being needed, move it to `temp/`; when it becomes
part of the record, promote it out of here.**

## What belongs here

A runner being iterated on before its pre-registration is committed, a fixture
mid-build, a diagnostic still being read, an analysis feeding a record that is
not yet written.

## What does NOT

Anything finished. A runner whose study has run belongs in `scripts/`; the
numbers it produced belong in `data/` and the reasoning in
`docs/decisions/`. **A file that has been in here across several sessions is
telling you it is either finished or abandoned** — promote it or drop it in
`temp/`.
