# RESULT D434 — the final channel, traded long and short: the long side is zero, the short side is negative, and the book is worse than randomly re-timing its own trades

*The runner is `scripts/run_d434_channel_trades.py`; the record it answers is
[D434](D434-trading-the-final-channel-long-and-short-both-lenses.md), committed before it existed.
Numbers: `data/d434_channel_trades.json`. Nothing is admitted and nothing is closed — only the
principal closes an avenue (R15, D360).*

## The answer in one line

Across 1,573 names and 44,872 trades, the long side's gross mean per trade is **+7.6 ± 6.5 bp
(t = 1.2)** — indistinguishable from zero — the short side's is **−73.1 ± 8.7 bp (t = −8.4)**, and
on the book lens **both sides return LESS than the median of a null that re-times their own
trades at random inside the same names**. The rule's entry timing is not merely uninformative;
on the book it is worse than no timing at all.

## 1. Performance, gross and net, both lenses

**Per trade** (headline cell: INDEPENDENT, τ = 0.50, target 2 ATR):

| side | n | gross | ±SE | median | trim 1% both | ex-top 1% | net | breakeven | win | hold |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 26,071 | **+7.6 bp** | 6.5 | −165.6 | −15.6 | −41.7 | −63.0 | 7.6 bp | 35% | 11 |
| short | 18,801 | **−73.1 bp** | 8.7 | −282.5 | −106.5 | −132.0 | −152.6 | — | 27% | 11 |

Cost is measured, not assumed: the Corwin-Schultz round-trip spread of the names actually held,
**70.6 bp long / 79.5 bp short**. The long side's breakeven is 7.6 bp against a 70.6 bp spread —
it needs to be nine times better before it pays for its own execution.

**The book** (equal weight over live names, `rf` 4%, `borrow` 3%, 252 bars/yr, close-only exits):

| side | total | Sharpe | exposure | maxDD | entries | null p50 | null p95 (SE) |
|---|---|---|---|---|---|---|---|
| long | +21.6% | 0.28 | 0.125 | −7.2% | 26,390 | **+34.2%** | +37.8% (0.3) |
| short | −25.7% | −0.69 | 0.079 | −27.9% | 19,247 | **−13.5%** | −11.5% (0.1) |
| both | −9.3% | −0.40 | 0.204 | −16.0% | 45,637 | **+16.5%** | +21.5% (0.3) |

## 2. The null, and what it destroys

Within-name time rotation of each name's own position series (`fast_null.rotation_null`, 300
sims, seed 0), on the same `keep_v2` mask as the observed book. It **preserves** the names, the
trade count, the holding lengths and the turnover; it **destroys** only the alignment between a
trade and the channel that produced it.

Every side is **below the null's p50**, so no margin-versus-p95 test is needed and none is
reported: the observed book loses to the middle of the null, not to its tail. The comparison is
if anything conservative *against* the null — a rotated position landing on an ineligible bar is
zeroed by the mask, so the null carries no more exposure than the observed book and still wins.

Per D434 §4's falsification clause, stated before the run: *"a side whose gross mean per trade is
at or below the null's p50 has no timing content in this rule and this record says so."* Both
sides are. Both fail, on both lenses.

## 3. Trade distribution — the long side's positive mean is six names

- 1,351 names traded long; **6 names carry half the P&L**; the top name is 11% and the **top ten
  are 85%**. Trim 1% from both tails and the mean goes from +7.6 to **−15.6 bp**; remove only the
  top 1% and it is −41.7 bp. Payoff 1.90, skew +1.8, win rate 35%.
- **9 of 17 years positive**, and the year means run from **+205 bp (2020) to −301 bp (2022)** —
  the sign of the whole result is a handful of years and a handful of names.
- Short side: 1,356 names, total P&L negative, so the "names to half the P&L" statistic is
  undefined and the JSON's `0` for the top-name shares is a degenerate readout of a negative
  total, not a real concentration figure.
- Top trade: **SWN, 2015-07-22, short, +13,194 bp**, exited on GONE (bars 1396→1497).
- 1,698 trades rejected by the split guard (|log return| > 0.40 on a held bar).

## 4. The predictions, checked before the result was read as evidence

| | prediction | outcome |
|---|---|---|
| P1 | long:short > 2:1 | **missed** — 1.39:1 |
| P2 | median hold 5–20 bars | held — 11 |
| P3 | stop is modal (>50%), target < 20% | **held, at the extreme** — stop **81%**, target **4.6%** |
| P4 | held-name spread 20–60 bp | **missed on the band** — 70.6 / 79.5 bp round trip, which is D285's 33.8 bp/side doubled; the band was too tight, the measurement stands |
| P5 | GME under 5% of trades | held — 0.1% long, 0.2% short |
| P6 | short side gross negative | held — −73.1 bp, t = −8.4 |

**P3 is the design finding.** 81% of exits are the trailing stop and 4.6% the target, so this is a
trailing-stop rule and the target multiple is close to decorative — as D434 §5 said it would be
read if P3 came in at the extreme. Consistent with that, the *tightest* target wins on every
cell (1 ATR beats 2 beats 3 on all 18 rows): there is no continuation to wait for.

## 5. The declared grid, and two things it says (R13: 3 τ × 3 targets × 2 variants = 18 cells)

- **The similarity gate does not earn its place.** Loosening τ from 0.25 → 0.50 → 1.00 *raises*
  the long gross (+7.3 → +11.8 → +14.8 bp at target 1 ATR) and adds trades. A gate whose loosest
  setting is its best setting is filtering out trades no worse than the ones it keeps.
- **"Keep going with only one" changes the exits, not the outcome.** INDEPENDENT +7.6 vs PAIRED
  +8.1 bp at the headline. The variant changes the exit mix substantially (PAIRED exits on GONE
  far more often, because its sides die together) and the per-trade result almost not at all.

## 6. What this does and does not say

It says: **this rule**, on **this construction**, does not pay, and its entry timing is worse
than random re-timing of the same trades. It does not say the construction has no information in
it — the lines were never scored against anything here, only traded by one rule; and it does not
close the D399 avenue, which is the principal's call.

The honest next question, if there is one, is not another exit overlay on the same entry: the
book being *below the null's median* on both sides means the entry condition itself is pointing
the wrong way in time, and no stop or target repairs that.

## 7. Audits carried

`[L]` seven entry decisions re-derived from inputs truncated at the entry bar, pivots recomputed
on the truncation — the rule cannot read the future. `[S]` the largest up-bar inside a long trade
(+1,417 bp on AA) contributes positively, and the inverted-direction mirror is asserted to fail.
`[N]` 26,071 long and 18,801 short trades, both far above the 100-trade non-vacuity floor.
`assert_matches_scorer` on the real book before any null — **it fired on the first run** (the
null's context was masked and the scored position was not) and refused to score a different book;
the second run passes it. The construction's own `[R]` no-line-through-a-body and `[C]`
no-inverted-channel assertions ran on every name's whole history.
