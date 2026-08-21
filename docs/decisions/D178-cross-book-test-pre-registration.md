# D178 — The cross-book test: `swing_k2` on the long book, E1 on the short book

**Status:** PRE-REGISTERED — implementation committed, **studies not yet run**
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** Both rules have only ever been judged on the book they were developed on

> Written and committed **before** either study runs, as D173 was. The predictions below
> are falsifiable and dated by git. A result section will be appended and nothing above it
> edited.

## The question

Two rules survived their own books, and neither has met the other's:

- **`SwingStructureStop(k)`** was developed and judged entirely on the **short** book. It
  beat `trail_10` on both symbols (D173) and on 69% of 62 universe coins (D174).
- **`FailedBreakoutExit(k)` (E1)** was developed and judged entirely on the **long** book,
  where it is the only recommendation in `BREAKOUT_REVERSAL_FEATURES.md` to survive (D177).

An effect that belongs to the RULE should transfer. An effect that belongs to the BOOK — a
particular exit cadence, a particular trade-length distribution — should not. That is what
this asks.

Both `k ∈ {2, 3}` are tested on both sides. Testing only the k that won would repeat
D173's actual error, which was generalising from one member of a swept set.

## What is built

- Long book: `exit_swing_k2`, `exit_swing_k3` — baseline plus the swing stop, nothing else.
- Short book: `exit_e1_k2`, `exit_e1_k3` — baseline plus E1. **E1 is not a stop** (it bounds
  duration inside a window, not loss), so on a short it rides alongside the incumbent
  `channel_stop`, which the baseline also carries. The delta therefore prices E1 alone.

## The predictions

Scored by the every-symbol rule at `SHARPE_EPS = 0.01`, against each book's own baseline.

**H1 — `swing_k2` will NOT clear the bar on the long book.**

The mechanism is a difference in what the two rules bound in TIME. E1 acts only within k
bars of entry and then leaves the trade alone; a swing stop is live for the entire life of
the position, including deep inside a winning trend, where the last confirmed swing low
sits close behind price and will cut it. The long book's returns are concentrated in a
handful of long trends — that is the finding its own report leads with — and every device
this project has tested that shortens those trends has cost more than it saved.

Against this: the long book's baseline exit is a 10-bar low, which is looser than the swing
stop would be, and on the short book "tighter and adaptive" was exactly what worked.

**H2 — E1 will NOT clear the bar on the short book.**

E1's benefit on the long book came substantially from RE-ENTRY: the trade count rose
38 → 44 on BTC while returns improved. Re-entry is only a gift on a book with positive
expectancy. The short book's entry rule sits at the 51st percentile of its own null on BTC
and it pays borrow at 10%/yr — so cutting a bad trade early helps, and re-entering into
another bad trade costs, and the second effect scales with how bad the entries are.

**Confidence, stated honestly:** lower on H1 than on H2. D173's H1 was falsified by exactly
this kind of mechanism-first reasoning, where the mechanism was sound and applied to the
wrong parameter. If H1 fails again it will most likely fail the same way — on one k and not
the other.

**What would falsify either:** a Δ Sharpe above +0.01 on BOTH symbols of that book.

## Multiplicity, paid up front

Long book 28 → 30 configurations; short book 25 → 27. Every one registered and in the DSR
pool for its cell. Both books' deflated Sharpe will move as a result, and neither has an
edge to lose: the long book sits near 1.0 only because its plateau is flat, and the short
book is at 0.04–0.54.

---

# RESULT — appended 2026-08-21, after both runs. Nothing above this line was edited.

**Status: H1 confirmed as literally stated but misleading if left there. H2 FALSIFIED.**

## H1 — `swing_k2` on the long book

| | Δ Sharpe BTC | Δ Sharpe ETH | Every-symbol rule |
|---|---|---|---|
| `exit_swing_k2` | +0.100 | **−0.075** | fails |
| `exit_swing_k3` | +0.015 | +0.148 | **clears it** |

The literal prediction — *`swing_k2` will not clear the bar on the long book* — **holds**.
It fails on ETH, decisively.

**But the family transfers; only the parameter does not.** `swing_k3` clears the bar on
both symbols. Reporting H1 as "confirmed" and stopping there would be true and misleading,
which is exactly the failure this record exists to prevent.

**And the k FLIPS between books.** On the short book `swing_k2` won and `k3` did not
(D173); on the long book `k3` wins and `k2` does not. That is the sharpest structural
finding here: **the pivot lookback that works is a property of the book, while the rule
family is a property of the rule.** A book's swing-stop parameter is fitted to its own
trade cadence, and carrying the number across is precisely what does not survive.

The pre-registration flagged this exact failure mode in advance — *"if H1 fails again it
will most likely fail the same way, on one k and not the other"* — which is some evidence
the mechanism-first reasoning is sound even where its conclusions are not.

## H2 — E1 on the short book: FALSIFIED

| | Δ Sharpe BTC | Δ Sharpe ETH | Every-symbol rule |
|---|---|---|---|
| `exit_e1_k2` | +0.020 | +0.059 | **clears it** |
| `exit_e1_k3` | +0.061 | +0.101 | **clears it** |

E1 clears the bar on the short book at **both** k. The prediction that it would not is
wrong.

**Why the reasoning failed, and it is the same class of error as D173's.** H2 rested on
attributing E1's long-book benefit chiefly to RE-ENTRY, and then arguing that re-entry is a
liability on a negative-expectancy book. The trade counts say that attribution was wrong:
E1 raises the short book's trades only 35 → 39 on BTC and 27 → 28 on ETH, and it improves
returns anyway. **E1's benefit is not re-entry — it is not sitting in a failed trade.** I
identified a real secondary mechanism on the long book and mistook it for the primary one.

## What this means, taken together

**E1 is the strongest rule this project has found.** It now clears the every-symbol bar on
BOTH books at BOTH k — four independent passes — and its mechanism is direction-agnostic by
construction. Nothing else tested here has that profile: the entry filters failed
everywhere, the stops split by symbol, and the swing stop transfers only as a family.

**The swing stop is weaker than D173/D174 suggested.** It survives cross-book only if you
are permitted to re-pick k per book, and re-picking per book is a search, not a transfer.
D174's 69% universe win rate was `swing_k2` against `trail_10` on the SHORT book; nothing
here contradicts it, and nothing here extends it to the long side at that k.

**Neither is adopted.** Long book now 30 configurations, short book 27, and both DSRs moved
to pay for it: long BTC ~1.0 / ETH 0.975–0.986 (the long book's DSR sits near 1.0 because
its plateau is flat, which its own report is explicit is *not* vindication), short 0.038–0.538.
A rule passing four independent every-symbol tests is a reason to keep testing it, not a
reason to believe it.

## The honest next test for E1

Not another sweep on these two symbols. The D140 universe, exactly as D174 did for the
swing stop: E1 versus no-E1, one configuration each, on 62 coins including the ones that
died. That is the test that would distinguish a real effect from four correlated passes on
two instruments.
