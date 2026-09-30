# D717 STAGE 0 RESULT — NEITHER on NQ: the reversed flow rule does not transfer. NQ's flow residual ranks nothing (Spearman −0.007, 37th percentile), and its two-sided book nets −$5.37 a MNQ trade; the principal's prediction (NQ better than ES) is missed; ES's +$4.31 is D715's own selection restated

*2026-09-30. One run of `scripts/stage0_d717_reversed_flow.py` (14 s).*
- **The order:** the [design record](D717-STAGE-0-DESIGN-the-reversed-flow-rule.md) (`f979337d`) and the principal's
  prediction were committed before the builder and runner. The builder and runner were committed before the run.
- **The new fixture** `fut_NQ_signed_1m` (2,062 sessions) passed D695's validation before any outcome was read: volume
  ratio 1.00, volume ρ 0.99996, signed share 1.000, last trade = bar close on 98.0% of minutes.
- **Checks:**
  - 40 candidates per root re-derived from the raw rows: equal;
  - ES reproduced D715 exactly (1,961 candidates, ρ −0.060754);
  - NQ F2's in-sample book reproduced (274 trades, +$20.67) before its correlation.
- **What it is:** in-sample, 2016–2023, one micro per root. Nothing dated 2024-01-01 or later was read.
- **Output:** `data/stage0_d717_reversed_flow.json`.

## The answer in one line

**NQ, the declared primary, reads NEITHER.**
- The flow residual carries no information about NQ's 10:30 → close move, in either direction.
- The reversal found on ES in D715 is **not a mechanism that transfers across index roots**. It is ES's in-sample
  result, and on the evidence it is most likely noise.

## 1. NQ (the primary; one MNQ, $4.07)

| gate | result | passes |
|---|---|---|
| G1 mechanism | Spearman ρ(R, the follow outcome) **−0.007**; rotation p50 +0.001, p95 +0.040, **the 37th percentile** | no |
| G2 edge | the two-sided book nets −$5.37 (NW t −0.92); efficiency at the 42nd percentile | no |
| G3 both halves | pushed-follow +$9.95, **absorbed-fade −$11.89** | no |
| G4 episodes | −$6,573 in 2022; positive in 1 of 6 years | no |
| G5 drift | T −$2.11 | no |

**NQ's R quintiles** (the follow outcome, gross per MNQ trade, 0 = most absorbed): +$18.44, +$16.32, −$15.40,
+$16.94, +$12.33. There is no gradient.

| NQ book | trades | gross (t) | net (t) | median net | win | bp | daily net Sharpe (Sortino) | max DD | ρ arm |
|---|---:|---|---|---:|---:|---:|---|---:|---:|
| **two-sided reversed** | 1,444 | −$1.30 (−0.22) | **−$5.37 (−0.92)** | −$2.57 | 49.2% | −0.59 | −0.32 (−0.44) | $11,510 | −0.10 |
| pushed, followed | 700 | +$9.95 (1.30) | +$5.89 (0.77) | +$12.68 | 53.3% | +3.55 | +0.26 (+0.37) | $4,566 | +0.08 |
| absorbed, faded | 744 | −$11.89 (−1.42) | −$15.95 (−1.90) | −$16.57 | 45.4% | −4.48 | −0.64 (−0.88) | $13,933 | −0.20 |

- **Absorbed moves on NQ continue too.** Fading them loses. That is B's original prediction on one half, and the
  reversed prediction on the other. So the residual separates nothing on NQ.
- **The trade distribution** (the two-sided book, net): skew +0.01, kurtosis 6.1; trims 1%: ex-top −$13.52,
  ex-bottom +$2.75, both −$5.40.
- **By year:** 2018 −$1,683, 2019 −$91, 2020 −$1,082, 2021 +$2,697, 2022 −$6,573, 2023 −$1,014.
- **Long −$2.17, short −$8.64.** −24% of the gross falls in 15:30 → 16:00.
- **ρ with NQ F2** (slot 7), daily: +0.09.

## 2. ES (reported; selected by D715, not evidence)

- **The reversed rule on ES:** 1,425 trades, gross +$8.73 (t 2.23), net +$4.31 (t 1.10), daily Sharpe +0.41 (Sortino
  +0.59). G1 ρ +0.061 (99.3rd percentile), which is D715's result with the sign flipped.
- **Gates:** G3 and G5 pass. G4 fails: 2022 holds +$4,553 of the +$6,148 net, and 2019 is −$1,889.
- **Its reading on these gates would be MECHANISM ONLY,** but it was chosen by D715, so it carries no evidential
  weight.

## 3. The principal's prediction

**P-principal (NQ's reversed book beats ES's on gross AND net a trade): MISSED.**

| | gross | net | bp |
|---|---:|---:|---:|
| NQ | −$1.30 | −$5.37 | −0.59 |
| ES | +$8.73 | +$4.31 | +4.62 |

It is missed in dollars and in bp alike. Pooled daily, the two roots net −$1.10 a session (Sharpe −0.06).

## 4. What it says

1. **ES's inverted absorption gradient does not replicate on NQ,** on the same rule, years, clock and flow source (NQ's
   fixture validates as well as ES's). The honest reading is that D715's inversion was an ES sample result, not a
   mechanism.
2. **The aggressor-flow residual has now failed as a direction signal four times on the index day session:**
   - D695 found nothing;
   - D704 was about 1 SE the "no push" way on V1's trades;
   - D715 ran the other way on ES;
   - D717 found nothing on NQ.
3. **Under R15, this closes the reversed construction.** Whether to close the avenue (first-hour aggressor flow as a
   direction conditioner on index futures) is the principal's call. The new NQ flow fixture stays as data.

## CLOSED, 2026-09-30, on the principal's word

The principal: "Close B and its reversal under R15."
- **Closed under R15:** proposal B (the absorbed morning move, D715) and its reversal (follow pushed and fade absorbed
  first-hour moves, D717), on ES and NQ, including any filter or cut of either.
- **Not closed:** the wider avenue, first-hour aggressor flow as a direction conditioner on index futures, was not
  ruled on.
- **Kept as data:** `fut_NQ_signed_1m`, beside D695's ES file.
