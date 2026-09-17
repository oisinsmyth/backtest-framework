# D499 RESULT — stage 0, CLOSE: the hour after a large move reverts in the US off-hours on the index roots, and the reversal is worth less than a tick; no cell of 16 clears the family bar or the fee, on any of eight roots

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D499-RESULT-stage-0-CLOSE-the-hour-after-a-large-move-reverts-in-the-US-off-hours-on-the-index-roots-and-is-worth-less-than-a-tick-no-cell-of-16-clears-the-family-bar-or-the-fee.md`. The H1 above is the full title.*

**Result of D499** (spec `467500f`). Runner `scripts/run_d499_hourly_reversal_stage0.py --run`
(`--selftest` passes; 0.6 min), artefact `data/d499_hourly_reversal_stage0.json`, trade files
`data/d499_trades_<root>.csv.gz`. Eight roots, 1,979–2,040 same-front sessions each,
**2016-01-04 → 2023-12-29; 2024+ unread.** RTY held back (D467 G2).

**One correction to the spec.** h18 … h14 is **21** entry hours, not 22; *thin* is the 11
lowest-volume entry hours and *thick* the other 10. The thin set is h18–h02 plus h05, h06 on six
roots (GC swaps h02 for h14; 6E swaps h05, h06 for h13, h14). The London hours h03, h04, h07, h08
are *thick* by volume on every root — the US-clock "off-hours" and the volume-thin hours are
different sets, and the two splits give different answers below.

**Two disclosures.** The family bar uses the plain-SE z on both sides (the null's z per offset is
mean / (sd / √n), and the observed z is the same statistic); the month-block-bootstrap SE the spec
named is reported beside it (`se_boot`) and does not change any ordering. At k = 2, 3 a session
can hold two overlapping trades from adjacent hours; those cells are per-trade lenses, not books.

## 0. The primary cells (k = 1, one micro; ZN/ZB at full size, $6)

| root, cell | N (/yr) | gross $ | bp | ticks | net A (fee) | net B (fee + tick) | hit | z | N1 p95 (share ≥ obs) | halves $ | net Sharpe (SE) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| ES thin | 2,127 (266) | +1.03 | +0.6 | +0.83 | −1.97 | −3.22 | 51.2% | +0.99 | +1.68 (15.7%) | +0.34 / +1.62 | −0.57 (0.32) |
| ES thick | 1,992 (249) | +0.76 | +0.8 | +0.61 | −2.24 | −3.49 | 49.0% | +0.40 | +1.70 (36.7%) | −0.83 / +1.93 | −0.48 (0.47) |
| NQ thin | 2,176 (272) | +1.38 | +0.5 | +2.76 | −1.62 | −2.12 | 51.9% | +1.01 | +1.57 (14.2%) | +0.06 / +2.52 | −0.39 (0.28) |
| NQ thick | 1,981 (248) | +2.46 | +1.5 | +4.93 | −0.54 | −1.04 | 49.6% | +0.91 | +1.69 (19.7%) | −1.17 / +5.31 | −0.04 (0.49) |
| YM thin | 2,101 (263) | +0.86 | +0.5 | +1.71 | −2.14 | −2.64 | 52.9% | +1.01 | +1.64 (14.2%) | +0.44 / +1.22 | −0.80 (0.31) |
| YM thick | 1,918 (240) | +0.40 | +0.3 | +0.80 | −2.60 | −3.10 | 49.7% | +0.27 | +1.68 (41.0%) | −2.08 / +2.29 | −0.68 (0.40) |
| ZN thin | 2,376 (297) | +1.27 | +0.1 | +0.08 | −4.73 | −20.36 | 46.5% | +0.58 | +1.69 (29.0%) | −0.26 / +2.32 | −0.72 (0.32) |
| ZN thick | 2,109 (264) | −2.89 | −0.3 | −0.18 | −8.89 | −24.51 | 47.6% | −0.93 | +1.64 (84.3%) | +1.77 / −6.13 | −1.17 (0.39) |
| ZB thin | 2,207 (276) | +5.17 | +0.3 | +0.17 | −0.83 | −32.08 | 47.4% | +0.90 | +1.59 (18.4%) | +2.48 / +7.09 | +0.02 (0.29) |
| ZB thick | 1,963 (245) | +0.29 | −0.1 | +0.01 | −5.71 | −36.96 | 49.7% | +0.03 | +1.61 (49.6%) | −0.80 / +1.01 | −0.27 (0.35) |
| GC thin | 2,011 (251) | +0.06 | +0.1 | +0.06 | −2.94 | −3.94 | 52.3% | +0.06 | +1.65 (48.2%) | +0.75 / −0.45 | −1.29 (0.34) |
| GC thick | 1,852 (232) | −1.01 | −0.7 | −1.01 | −4.01 | −5.01 | 50.8% | −0.82 | +1.71 (80.0%) | −0.07 / −1.74 | −1.26 (0.36) |
| **CL thin** | 2,040 (291) | +1.65 | +0.7 | +1.65 | −1.35 | −2.35 | 53.1% | **+1.84** | **+1.69 (3.9%)** | +0.51 / +2.44 | −0.55 (0.63) |
| CL thick | 1,838 (263) | −1.20 | −1.0 | −1.20 | −4.20 | −5.20 | 49.3% | −0.82 | +1.65 (80.1%) | −0.39 / −1.74 | −1.03 (0.27) |
| 6E thin | 2,119 (265) | +0.35 | +0.3 | +0.28 | −2.65 | −3.90 | 52.5% | +0.96 | +1.69 (16.9%) | −0.19 / +0.66 | −2.46 (0.40) |
| 6E thick | 1,921 (240) | −0.44 | −0.3 | −0.35 | −3.44 | −4.69 | 49.3% | −0.94 | +1.72 (83.4%) | −0.33 / −0.50 | −2.71 (0.32) |

**Family maximum of z over the 16 cells, 1,978 common offsets (exact):** p50 +1.76, **p95 +2.70**,
p99 +3.12. **Observed maximum +1.84 (CL thin); 42.9% of offsets reach it.** One cell clears its
own N1 (CL thin, 3.9% of offsets) and it is net −$2.35 a trade after fee and tick, so it is not
a PICK under the rule. Fifteen of sixteen component lines are negative; the sixteenth (ZB thin)
is +0.02. **Verdict by the pre-registered rule: CLOSE.**

## 1. What the measurement found, in three parts

**(a) The reversal exists, on the US clock, on the index roots — and it is a statistic, not a
trade.** The pooled β of next-hour on last-hour return, over the US off-hours h18 … h08, is
outside its exact rotation band on ES (−0.043, band ±0.014), NQ (−0.028, ±0.015) and YM (−0.037,
±0.014); inside it in the day session on all three (+0.004 to +0.012). The conditional fade in
those hours (the secondary `us_off` cell) clears its own N1 on ES (z +2.10 vs p95 +1.68, 1.7% of
offsets) and NQ (+1.82 vs +1.56, 2.9%), with gross **+$2.12 and +$2.44 a trade** — 1.7 and 4.9
ticks, +1.3 and +1.1 bp — and both are **net negative after the $3 fee** (−$0.88, −$0.56) and
further after the tick. A 100 bp hour is followed by 3–4 bp back; a top-decile off-hours hour is
20–30 bp; the trade is worth a tick and a half. This is D487's last-half-hour finding again at a
different clock: real in sign, worth a tick in size.

**(b) The volume-thin hours are not where it lives.** Partitioned by volume — the spec's primary
split — the pooled β is inside its band on seven of eight roots (ZN thin −0.023 is the one
outside, and ZN's tick makes it untradeable). The London hours h03, h04, h07, h08 carry the
volume that makes them *thick* and the mechanism's "thin book → transitory impact" story would
exclude them; the US-clock split includes them and shows the effect, the volume split excludes
them and does not. On CL the off-hours pooled β is **positive** and outside its band (+0.030):
crude *continues* overnight, in the hours after the Asian and European opens.

**(c) The relative-volume split runs backwards.** The mechanism predicts a large move on *low*
relative volume reverts more. It reverts *less*, on seven of eight roots (YM thin −$6.19, z −2.1;
the others within 2 SE; 6E thick is the one positive at z +2.6 — two of sixteen splits beyond 2 SE
is what sixteen draws give). A move that arrives on little volume in these markets is more often
the start of something than an inventory shock. Whatever the off-hours reversal is, it is not the
transitory-impact mechanism the spec named.

## 2. The yardstick (M3): the hourly clock cannot carry $3

Fee A as a share of the expected next-hour move, averaged over the thin / thick hours: **NQ 14.5% /
7.1%**, ES 21.0% / 10.8%, CL 23.5% / 12.3%, GC 20.3% / 13.6%, YM 26.4% / 13.6%, 6E 44.7% / 26.3%.
The break-even accuracy in NQ's thin hours is **57.2%** (thick 53.5%), on ES 60.5% / 55.4%; the
observed conditional hit rates across the sixteen cells are 46.5–53.1%. Against FINDINGS §69's
day-session line (2.4% of the move, break-even 51.2%), an hourly hold on the Nasdaq micro pays six
times the fee per unit of move in the thin hours and three times in the thick. On ZN and ZB the
crossed tick is $15.63 / $31.25 against an expected hourly move of 2.8–4.5 and 3.3–5.6 ticks: fee
B is 19–80% (ZN) and 14–58% (ZB) of the move in every hour.
**No hourly-horizon construction on these roots at micro cost can clear C-a on accuracy alone;
it would need a per-trade move several times the hourly σ, which is a different clock.**

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | thin β on index roots −0.02 … −0.08, thick ±0.02; \|β\| < 0.03 ZN/ZB/6E; thin outside on ≥ 2 roots | thin β +0.001 … −0.011 (inside); thick −0.010 … −0.021; ZN thin −0.023 outside (the only one); **the US-clock off-hours β is outside on ES/NQ/YM** | wrong on the volume split; the sign is there on the clock split |
| X-b | NQ thin +4 … +10 bp, hit 52–55%, 200–260/yr; ES thin +2 … +6; thick ±3 | NQ thin **+0.5 bp**, 51.9%, 272/yr; ES thin +0.6; thick +1.5 / +0.8 | wrong: an order of magnitude smaller |
| X-c | family p95 +2.4 … +2.9; nothing clears; CLOSE | p95 +2.70; max +1.84; CLOSE | right |
| X-d | fee A 4–9% thin, 2–4% thick; ZN fee B > 30% every hour; thin break-even > 52% | 14–24% thin, 7–14% thick; ZN fee B min 19%; NQ thin break-even 57.2% | the direction right, the size wrong by 2–3× (worse than predicted); ZN better than predicted |
| X-e | low-relvol reverts more on ≥ 5 of 8 | on 1 of 8; backwards on 7 | wrong |

## 4. What stands

- **CLOSE recommended for the hourly-reversal line as a prop component**, on every root and both
  partitions; the principal closes. Fifteen of sixteen component lines are negative in-sample at
  one micro; the best gross cell is +$2.46 a trade against $3.
- **What is real and goes to FINDINGS as a measurement:** next-hour reversal of the last hour's
  move in the US off-hours on ES/NQ/YM (β −0.03 to −0.04, outside exact rotation bands), worth
  1.7–4.9 ticks a trade after a top-decile hour; crude continues in the same hours (+0.03). Not
  a trade at micro cost; a monitor, or a personal-book question at full size.
- **The hourly clock is closed by arithmetic before any signal**: the fee is 7–24% of the
  expected hourly move on the micros and 19–60% on ZN/ZB. A 24-hour-market component for the
  prop book must hold for a session, not an hour, and must be a *state* on a non-index root —
  the daily-state family (D495/D498's clock) on CL, GC, 6E, ZN is unscored and stays outside the
  overnight closure, which names only the index leg.
- **Spent:** nothing. 2024+ is unread on every root under this record.

## 5. Files

Runner · eight trade files · the artefact · this record · the ledger rows · PICKUP.
