# RESULT D482 — the level read is the first channel cell above its null: +44 bp gross over five bars with a positive median, on both constructions, and it does not clear cost at that hold

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D482-RESULT-the-level-read-is-the-first-channel-cell-above-its-null-plus-44-bp-gross-over-five-bars-with-a-positive-median-and-it-does-not-clear-cost.md`. The H1 above is the full title.*

*Runner `scripts/run_d478_grow_trades.py --source hand --rule level`; numbers
`data/d482_hand_level.json` (the hand cell is keyed "GROW" in the file and the null/book lines);
log `temp/d482_full.log`; spec [D482](D482-the-level-read-on-the-hand-cell-in-sample.md).
In-sample, the mining panel, 1,573 names. Nothing is admitted; the closing record the principal
asked for is NOT written, because the pre-registered condition for not closing was met.*

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 HAND long, hold 5 | 0 to +25 bp gross; net negative | **+43.6 ± 5.6** gross, net −33.7 — **missed upward** on gross, held on net |
| P1 short | −20 to +10 | +11.4 ± 6.0 — held |
| P2 neither side above its null p95 by 2 SE | | long **41 SE above** (score +43.6, p95 +27.1, SE 0.4); short above too — **missed** |
| P3 per-bar gross does not grow with the hold | H20 below 4 × H5 | +112.8 vs 4 × 43.6 = 174 — held |
| P4 CAUSAL within 10 bp at H = 5 | | +45.4 vs +43.6 — held |
| P5 long median below the mean | | median **+58.1** above the mean +43.6 — **missed**: the centre carries it, not the tail |

## 1. Per trade, gross bp — HAND (D480's cell) and CAUSAL (D399's), the same rule

| hold | side | HAND n | gross | ±SE | median | trim | net | win | | CAUSAL n | gross | ±SE | median | net | win |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | long | 16,933 | +6.2 | 3.3 | +12 | +8 | −72 | 51% | | 31,496 | +15.0 | 2.9 | +41 | −63 | 52% |
| 3 | long | 16,201 | +26.5 | 4.6 | +35 | +30 | −51 | 53% | | 27,703 | +31.3 | 4.2 | +48 | −48 | 53% |
| **5** | **long** | 15,603 | **+43.6** | 5.6 | **+58** | +48 | **−34** | 55% | | 25,877 | **+45.4** | 5.2 | +66 | −34 | 54% |
| 10 | long | 14,643 | +56.4 | 7.8 | +94 | +66 | −20 | 56% | | 22,609 | +56.2 | 7.3 | +112 | −23 | 55% |
| 20 | long | 13,764 | +112.8 | 10.7 | +166 | +125 | **+37** | 57% | | 19,505 | +110.6 | 10.1 | +205 | +32 | 57% |
| 5 | short | 13,730 | +11.4 | 6.0 | −13 | +9 | −65 | 49% | | 23,798 | +1.5 | 5.1 | −33 | −74 | 48% |
| 20 | short | 12,263 | +7.4 | 11.7 | −51 | +3 | −69 | 48% | | 17,984 | −24.1 | 10.1 | −49 | −99 | 48% |

Per bar of hold, the long gross is roughly flat: 6.2 / 8.8 / 8.7 / 5.6 / 5.6 bp at holds
1 / 3 / 5 / 10 / 20. Spread of the names held ~77 bp round trip, so the long side clears cost
from a hold of about 15 bars; at 20 bars net +37 (HAND) / +32 (CAUSAL). No null was run at
holds other than 5.

**Nulls, hold 5** (within-name time rotation of the state series, 200 draws): HAND long score
+43.6 against p50 +17.8, p95 +27.1 (SE 0.4) — above by 41 SE; CAUSAL long +45.4 against p50
+25.7, p95 +32.7 — above by 21 SE; both shorts above their (negative) p95 as well.

**Books, hold 5** (D476's rotation null, 300 draws): HAND long +11.7% at Sharpe 0.67, exposure
**0.025**, maxDD −1.8%, against a null p50 +5.7% / p95 +7.0% and a null Sharpe p95 of 0.66 —
above on return, level on Sharpe; HAND both +9.4% at 0.42 against p95 +2.8% / Sharpe p95 0.10.
CAUSAL long +23.5% at 0.59, exposure 0.057, against p95 +15.5% / Sharpe p95 0.64.

**Concentration, HAND long, hold 5**: 1,333 names, **52 names to half the P&L**, top name 1%,
top ten 13%, **13 of 17 years profitable**. Top trade XPEV, long 2020-10-28, bars 43→49,
+6,339 bp. Split-guard rejections 627.

## 2. Reading it

- **This is the first channel cell that is a signal by the programme's criterion**: a positive
  gross mean per trade above its rotation null, with a positive median and a diffuse tail. The
  five direction cells (D476, D477, D478, D479, D481) had none of those three.
- **It is not the hand cell's doing.** D399's lines give the same number (+45.4). The ingredient
  is the *reading* — the close at or below the bottom tenth of a causal pivot channel whose
  support level sits 4% under the pivot lows — not the construction.
- **It is the touch effect of D412–D433, deeper and larger.** That effect was +10 bp gross on a
  touch of a second-zone line; this is +44 at a close below the channel's floor. The per-bar
  edge is about 8 bp for ten bars and 5–6 out to twenty, so it is a slow mean reversion, not a
  one-day bounce.
- **It does not clear cost at the pre-registered hold.** Net −34 at 5 bars. The hold at which it
  does (≥ 15 bars) was not the headline and has no null yet; and the book lens is only level
  with its null on Sharpe because the rule is in the market 2.5% of the time.
- **The obvious confound is the dip itself.** A close 4%+ below a channel's floor is a sharp fall;
  short-horizon reversal after sharp falls is a known effect, and the within-name rotation null
  does not control for it (it re-times the same events to bars that are not dips). Whether the
  channel adds anything to "buy the dip" is untested — a control must break the claimed
  ingredient (memory), and that control is the same rule keyed on the close's distance below its
  own trailing low, with no lines at all.

## 3. What follows, in order

1. **The dip control, in-sample, cheap**: the same hold-5 rule on bars where the close is ≥ X%
   below the trailing N-bar low (X, N matched to the depth and span the channel rule selects),
   with no channel. If it earns +44 too, the channel is not the ingredient and the line closes
   with that said. If it earns materially less, the channel's floor is doing work.
2. **A null at the cost-clearing hold** (20 bars), and the book at that hold.
3. Only then, and only on the principal's word: a held-out test on unseen names. The daily
   holdouts were spent for the second-zone line; holdout multiplicity is per line and this line
   has not spent one.

The closing record waits on step 1.

## 4. Audits carried

[V] extractor equality on 79,097 real trades within 1.9e-12 bp; [XV] rejects a one-bar shift;
[F] nine states on AA unchanged with future levels deleted, under the level rule's own audit;
[S] the largest up-bar inside a long trade (+3,768 bp) contributes with the right sign; [M]
`assert_matches_scorer` on every book; [N] 15,603 / 13,730 at the headline; [SPEED] hand cell
208 s at 3.0× on 12 workers (tail-heavy, as D481); whole run 779 s.
