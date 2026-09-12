# CLOSE — the daily channel line, D399 to D463: the principal's decision, 2026-09-12

*The principal instructed that the line be closed in writing after D462's level read and its
control, either way ("Action on your recommendation"; "Lets follow your recomendations"). The
control (D463) came in as predicted. This is the closing record. Only the principal reopens.*

## What the line was

A daily support-and-resistance channel, built causally from confirmed pivots (D399) and then
rebuilt three ways — the oracle's algorithm made causal (D451), with hysteresis and trend-side
breaks (D452), and re-dialled against the principal's own 140 hand-drawn lines (D460) — and
traded under three rules: a target and trail (D434), hold-while-a-trend (D450–D452, D461), and
the close's position in the channel (D462). Nine decisions, no holdout read.

## What it found

| reading | cells | result |
|---|---|---|
| the channel's **direction** as an entry | D434, D450 (causal arm), D451, D452, D461 | long within a few bp of zero gross, short negative, **every cell below a within-name rotation of its own trades**, worse as the gradient floor rises; the hand cell that draws the principal's lines (sign 92 / 87%) trades the same (+12 bp gross, null p50 +46) |
| the **oracle** (hindsight lines, boundaries hidden) | D450 | +780 to +1,272 bp per trade — a tautology: a channel that exists at t was chosen by what follows t |
| the channel's **level** | D462 | long **+44 bp gross over 5 bars**, median +58, 41 SE above its null, on both constructions; net −34 at 5 bars, +37 at 20 |
| the level without the channel | D463 | **a close 4% below the 30-bar low earns +47 with no lines**; inside a live channel +45; the channel adds nothing beyond the first day |

## The decision

**The daily channel line is closed.** Its direction carries no forward information on this panel
by any reading, and its level's one positive cell is a short-horizon reversal after a sharp
break of a trading range — real on this panel, both directions, net negative to ~15 bars, not
new, and not the channel's.

## What is kept, and where

- `data/d451_hand_drawn_lines.json` — 140 lines drawn step by step with the future hidden, with
  draw and end bars; `scripts/d451_score_hand_lines.py` scores any construction against them.
  The only written-down statement of what the principal's eye draws.
- `scripts/d460_hand_cell.py` — the construction that reproduces those lines (recall 69 / 71%,
  sign 92 / 87%, gradient within 27 / 40%/yr); `break_keep` in `recalc_pair`.
- The pages: "Draw the Lines" (1ed889fb, db-backed), "Step by Step" (c3cfdd07), "Grow Right"
  (6670af44), "Perfect Hindsight" (3216fed4), "The hand cell against the hand lines" (c7186ee1).
- `scripts/run_d451_grow_trades.py` — one runner, three rules, two sources, the vectorised
  extractor with its equality audit, the within-name rotation of a state series.

## The holdout ledger

**No holdout was read by this line.** Both daily holdouts remain as the second-zone line left
them (#1 spent 2026-09-07 by D371; #2 built, unspent). Holdout multiplicity is per line; this
line spent none.

## What the reversal effect is owed, if anyone picks it up

It belongs to a different line, and it is not on this branch's list: a 4% break below the
30-bar low, held 15–20 bars, +5–9 bp gross a bar, both directions. Before it is anything: the
book at the cost-clearing hold with a null there (D463 ran only the per-trade null at 20), a
volatility-matched control (the names it selects are wide-spread — net −80 at 5 bars), and the
literature, since one-month reversal is a published effect and this is likely a sample of it.
