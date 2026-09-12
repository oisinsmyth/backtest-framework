# CLOSE — the daily channel line, D399 to D483: the principal's decision, 2026-09-12

*The principal instructed that the line be closed in writing after D482's level read and its
control, either way ("Action on your recommendation"; "Lets follow your recomendations"). The
control (D483) came in as predicted. This is the closing record. Only the principal reopens.*

## What the line was

A daily support-and-resistance channel, built causally from confirmed pivots (D399) and then
rebuilt three ways — the oracle's algorithm made causal (D478), with hysteresis and trend-side
breaks (D479), and re-dialled against the principal's own 140 hand-drawn lines (D480) — and
traded under three rules: a target and trail (D476), hold-while-a-trend (D477–D479, D481), and
the close's position in the channel (D482). Nine decisions, no holdout read.

## What it found

| reading | cells | result |
|---|---|---|
| the channel's **direction** as an entry | D476, D477 (causal arm), D478, D479, D481 | long within a few bp of zero gross, short negative, **every cell below a within-name rotation of its own trades**, worse as the gradient floor rises; the hand cell that draws the principal's lines (sign 92 / 87%) trades the same (+12 bp gross, null p50 +46) |
| the **oracle** (hindsight lines, boundaries hidden) | D477 | +780 to +1,272 bp per trade — a tautology: a channel that exists at t was chosen by what follows t |
| the channel's **level** | D482 | long **+44 bp gross over 5 bars**, median +58, 41 SE above its null, on both constructions; net −34 at 5 bars, +37 at 20 |
| the level without the channel | D483 | **a close 4% below the 30-bar low earns +47 with no lines**; inside a live channel +45; the channel adds nothing beyond the first day |

## The decision

**The daily channel line is closed.** Its direction carries no forward information on this panel
by any reading, and its level's one positive cell is a short-horizon reversal after a sharp
break of a trading range — real on this panel, both directions, net negative to ~15 bars, not
new, and not the channel's.

## What is kept, and where

- `data/d478_hand_drawn_lines.json` — 140 lines drawn step by step with the future hidden, with
  draw and end bars; `scripts/d478_score_hand_lines.py` scores any construction against them.
  The only written-down statement of what the principal's eye draws.
- `scripts/d480_hand_cell.py` — the construction that reproduces those lines (recall 69 / 71%,
  sign 92 / 87%, gradient within 27 / 40%/yr); `break_keep` in `recalc_pair`.
- The pages: "Draw the Lines" (1ed889fb, db-backed), "Step by Step" (c3cfdd07), "Grow Right"
  (6670af44), "Perfect Hindsight" (3216fed4), "The hand cell against the hand lines" (c7186ee1).
- `scripts/run_d478_grow_trades.py` — one runner, three rules, two sources, the vectorised
  extractor with its equality audit, the within-name rotation of a state series.

## The holdout ledger

**No holdout was read by this line.** Both daily holdouts stand as master's ledger records them:
#1 spent 2026-09-07 by D371, #2 spent 2026-09-10 by the second-zone line (D412–D433). Holdout
multiplicity is per line; this line read neither, and it is closed without a read.

*Numbering note.* This line was researched on the `worktree-signal-hunt-part2` branch while
master advanced independently, and its records were renumbered at the merge on 2026-09-12:
D434 → D476, D450 → D477, D451 → D478, D452 → D479, D460 → D480, D461 → D481, D462 → D482,
D463 → D483 (scripts, data files and artifact pages renamed to match). D398 and D399 kept their
numbers. Master's own D434 and D450–D463 are unrelated records.

## What the reversal effect is owed, if anyone picks it up

It belongs to a different line, and it is not on this branch's list: a 4% break below the
30-bar low, held 15–20 bars, +5–9 bp gross a bar, both directions. Before it is anything: the
book at the cost-clearing hold with a null there (D483 ran only the per-trade null at 20), a
volatility-matched control (the names it selects are wide-spread — net −80 at 5 bars), and the
literature, since one-month reversal is a published effect and this is likely a sample of it.
