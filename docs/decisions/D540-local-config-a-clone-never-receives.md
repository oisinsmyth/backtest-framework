# D540 — three times now, the repository has worked because of config a clone never receives

**Status:** Committed
**Date:** 2026-09-17
**Category:** Verification
**Source:** Two independent reviews of `471dcb6`. The third instance was found the way the first two
were — by cloning the repository and running it somewhere else.

## The class

`git clone` copies commits. **It does not copy `.git/config`.** Anything set per-repository here is
absent from every clone, and a property that silently depends on one of those settings is a property
that holds for the author and nobody else.

This has now happened three times, and each time it was recorded as a one-off:

| setting | found | cost |
|---|---|---|
| `core.autocrlf` | round five | three tests compared bytes they had written as CRLF against pages checked out LF. Fixed by reading rather than writing; the rule went into `.gitattributes`. |
| `user.name` | round nine | four tests red on every clone: `build_public_cut.py --build` cannot author a commit in a repository with no identity. They are honest skips now, naming the missing key. |
| `core.longpaths` | **this record** | a default `git clone` onto Windows **aborts the checkout, reports exit code 0**, and leaves 2,865 of 3,028 files with an empty index. |

Three instances, one mechanism, and the class was never written down — so the third was found by a
reviewer rather than by this repository, which is the part worth recording.

## What the third one actually is

```
$ git clone --quiet <this repo> clone
fatal: unable to checkout working tree
warning: Clone succeeded, but checkout failed.
EXIT=0

$ cd clone && git ls-files | wc -l
0                               # the index was never written
$ git status --porcelain | wc -l
3053                            # so every path reports as deleted
```

The cause is Windows MAX_PATH (260) against a longest tracked path of **209 characters**. It has
never been seen here because:

```
$ git config --show-origin core.longpaths
file:.git/config        true
$ git config --global core.longpaths   -> (empty)
$ git config --system core.longpaths   -> (empty)
```

The author's clone root is 45 characters against a budget of 49. **Four characters of headroom, held
by a setting no cloner is given.** `C:\Users\<name>\Documents\GitHub\quant-backtesting-framework` is
61 and fails. CI runs on `ubuntu-latest`, where MAX_PATH does not exist, so no gate here could have
seen it.

**It fails quietly**, which is the worst property of the three: exit code 0, a populated-looking tree,
and 163 decision records missing. Every index-based tool in the repository then reports zero against
that empty index — `check_doc_links.py` printed `0 documents checked, 0 unresolved link(s)` and
exited 0, a vacuous green produced by doing the thing the README most recommends.

## The diagnostic has the same trap

The review that found this first reported `core.longpaths` as unset globally *and* locally. It was
running `git config` **from inside the broken clone**, where it is genuinely unset — the reading was
correct and the conclusion was inverted. Asking `git config <key>` from inside the repository merges
local, global and system and answers *yes* here, which is exactly the answer that hides the problem.

**`git config --show-origin` is the only form that answers the question being asked.** Recorded
because the class is invisible to the obvious diagnostic.

## Decision

1. **A property that depends on repository-local config must be gated by something a clone runs.**
   Prose in `CONTRIBUTING.md` is not that; a test is.
2. **Path length is now gated**, in `tests/unit/test_public_cut.py`, which already asserts what the
   public cut contains. The bound is 85 characters, which is what D1–D299 already observe — their
   longest path is 82. It was never a rule, only a habit, and the habit lapsed at D400 (median slug
   6 words before, 18 after). The gate makes the habit checkable.
3. **The 142 records over 120 characters are shortened** to that bound, each carrying a dated line
   recording its former name. The H1 inside every record already holds the full title, so nothing is
   lost but the path.
4. `check_doc_links.py` **refuses an empty document set** rather than reporting zero unresolved
   links, and resolves against the index instead of the disk — which also removes a second
   clone-shaped defect, `Path.resolve()` canonicalising case on Windows so that a mis-cased link
   passes here and 404s on Linux.
5. The README's clone instruction carries `-c core.longpaths=true` **and the reason**, which remains
   useful for anyone on an older git regardless of path lengths.

## What this does not fix

The bound is enforced on the *cut* and on the index; it is not enforced on a working tree someone
creates by other means. And the class is only closed for the three instances known. The general
form — *what else here is true only because of `.git/config`?* — has no gate, and the honest answer
is that it took three findings to notice the pattern at all.
