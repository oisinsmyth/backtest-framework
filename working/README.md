# working/

**Files in active use that are not yet part of the repo's record.**

The distinction from [`temp/`](../temp/) is *time*, not importance: losing
something here would cost real work **right now**, whereas `temp/` is safe to
empty at any moment. **When a file here stops being needed, it moves to `temp/`
— it does not linger.**

Contents are **tracked**, precisely because losing in-flight work is expensive.

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
