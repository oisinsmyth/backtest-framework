# temp/

**Everything in here is disposable. If this directory were deleted between two
commands, nothing of value would be lost.**

That is the whole contract, and it is a promise made to the *reader*: anyone can
empty this folder at any moment without asking, without reading the contents,
and without checking what depends on them. **If deleting a file would cost
something, it does not belong here.**

Contents are **git-ignored**. Only this README is tracked.

## What belongs here

Run logs already summarised into a record, one-off probe scripts, intermediate
dumps, scratch notebooks, anything downloaded that can be downloaded again,
and **anything promoted out of [`working/`](../working/) once it is finished
with**.

## What does NOT

Fixtures, committed data artefacts a decision record cites, runners, decision
records, anything a test imports. **If a `docs/decisions/*.md` file quotes a
number from it, it is evidence and belongs in `data/`.**
