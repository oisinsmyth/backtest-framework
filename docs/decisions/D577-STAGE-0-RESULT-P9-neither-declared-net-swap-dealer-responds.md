# D577 STAGE 0 RESULT — P9 on the declared statistic: **NEITHER CATEGORY RESPONDS** — the gross short of swap dealers (+18k contracts a log-point, t 1.2, rank 0.939) and of producer/merchant (t 0.8) both sit inside the shift null over four weeks, and the response is **two orders of magnitude below the derivation's prior** (+477 contracts per $1 against 18–37k). The two statistics declared "beside" say something the declared one cannot license: **the swap-dealer NET short responds (t 2.7 at four weeks, 3.7 at eight) and the producer/merchant net short moves the other way (t −2.0, −3.6)**; the swap-dealer gross short clears its null at eight weeks (t 2.1, rank 0.982); and the yearly swap-dealer net-short levels match the derivation's three natural experiments. The mapping as written fails; the mapping the data suggests is a post-hoc choice on seen data.

*2026-09-20. Design committed in D577 (`a42d19a`) before this ran. Diagnostic on 708 weekly CL
disaggregated reports 2010-06-08 → 2023-12-26 with the settlement strip at each report date;
no return computed; nothing from 2024-01-01 on read. Runner
`scripts/stage0_d577_cl_hedging_flow_p9.py`, output `data/stage0_d577_cl_p9.json`, 18 s. Audits:
the 12–24-month tenor by a second strip path on 706 reports (raises on a shift); the OLS by
statsmodels HAC and a hand-rolled Newey–West (raises on a negated regressor); the synthetic-flow
check recovered +976 from a fabricated multiple of 1,000 and −976 from its negation, so "short
rises on rallies" is the sign convention the βs below carry; the shift null's zero offset
reproduces the observed β; 685 offsets enumerated.*

---

## 1. The declared tests

Outcome: change in the category's **gross short**, in contracts, over *h* reports; regressor:
the change in the mean log settlement of delivery months 12–24 over the same *h*. β in
contracts per log-point (a log-point is a 100 % move; divide by the $67 mean strip for
contracts per $1).

| | PM gross short | SD gross short | PM+SD | SD share |
|---|---:|---:|---:|---:|
| **T1, h = 4 (primary)**: β · NW t · shift-null rank | +13.7k · 0.77 · 0.761 | **+18.2k · 1.22 · 0.939** (p95 +18.9k) | +32.0k · 1.60 · 0.945 | **0.57** (bar 0.6) |
| non-overlapping, every 4th report | +7.7k · 0.27 | +23.8k · 1.22 | +31.5k · 1.11 | |
| h = 2 | +17.1k · 1.13 · 0.917 | +13.7k · 1.46 · 0.969 | +30.8k · 1.93 · 0.981 | |
| h = 8 | −6.2k · −0.29 · 0.388 | **+37.0k · 2.13 · 0.982** | +30.9k · 1.19 · 0.846 | |
| on the nearby F₁ instead of the strip, h = 4 | −4.8k · −0.49 | +3.5k · 0.24 | −1.3k · −0.07 | |
| **T2, h = 4**: β on rallies / on declines | **+78.5k (rank 0.98) / −42.7k (0.09)** — asymmetric, the ratchet's shape | **−71.0k (0.00) / +41.6k (0.99)** — the opposite shape | +7.4k / −1.1k | |
| **T3**: Δshort a week, Feb–Mar and Aug–Sep vs other; rotated-mask rank | +1,214 vs −360 (diff +1,574, rank 0.80) | −197 vs +120 (−317, 0.29) | +1,017 vs −240 (0.73) | |
| **T4**: contracts per $1 over four reports | +205 | +272 | **+477** vs prior **18,000–37,000** | |
| **T5**: managed money | net long share of OI +0.021, positive on 75 % of reports; corr(ΔMM net long, Δ hedger short) **+0.19** | | | |

**Decision rule, as declared:** SD does not clear its null at h = 4, its share is below 0.6, its
split betas have the wrong shape → **NEITHER CATEGORY RESPONDS.** The deposit's own order (§12)
says: stop and fix the mapping.

## 2. The statistics declared "beside", which cannot decide but do speak

**The NET short by category.** Δ(short − long) on the strip change:

| h | PM net short | SD net short |
|---|---:|---:|
| 2 | −16.6k · t −1.10 | +28.0k · **t +2.46** |
| 4 | −39.5k · **t −2.02** | +44.1k · **t +2.69** |
| 8 | −74.1k · **t −3.58** | +70.9k · **t +3.71** |

The two categories' net positions move **against each other** on strip rallies, with the
swap-dealer side selling and the producer/merchant side buying, and the effect grows with the
horizon. The gross shorts do not show it because the gross longs move too: swap dealers' longs
are their index and consumer clients, producer/merchant's longs are refiners and consumers, and
on a rally both books rebalance on both sides. **The derivation's measured footprint —
`PM_short + SD_short` — nets to nothing across the two categories on the gross line (PM+SD net
β +4.5k, t 0.27) and only the swap-dealer NET line carries the sign the mechanism predicts.**

**The response builds over eight weeks, not four.** SD gross short is inside its null at two
and four weeks and above it at eight (t 2.13, rank 0.982); SD net short's t rises 2.5 → 2.7 →
3.7. The design declared four weeks from the derivation's "2–4 week" response and reported the
others; the flow the data shows is slower than the design assumed.

**The levels, by year** (SD net short / PM net short, thousands of contracts / mean strip $):
2010 −24/+56/85 · 2011 +9/+30/97 · 2012 +44/−28/95 · **2013 +160/−104/91** · 2014 +128/−71/85 ·
**2015 +43/−17/56 · 2016 +35/−35/49** · 2017 +55/−29/52 · 2018 +143/−78/60 · 2019 +163/−25/55 ·
**2020 +144/−28/43** · 2021 +110/−81/60 · **2022 +61/−46/78 · 2023 +22/+3/72**. Read against the
derivation's natural experiments (§11): the 2015–16 collapse of hedging to floor levels (SD net
short 128k → 43k → 35k as the strip fell from $85 to $49); hedges held through the 2020 crash
(144k at a $43 strip, the ratchet); reduced hedging in 2022–23 with the strip above the new-well
breakeven (61k → 22k). Producer/merchant is **net long** in eleven of fourteen years: the
category is the refiner and consumer book with the producers inside it, exactly the netting
the derivation's §1.7 warned of, seen from the other side.

**Scale.** The measured response of the combined gross short is +477 contracts per $1 of strip
over four reports. The derivation's prior, from the surveyed population's hedge-ratio slope, is
18–37k contracts per $1 "spread over days to weeks". Even the swap-dealer net response at eight
weeks (+71k a log-point ≈ +1,060 per $1) is a factor of twenty below the prior's floor. Either
the flow does not reach the futures at the 12–24-month tenors in the size the survey population
implies — OTC swaps warehoused, hedged at the front, or laid off across the whole curve rather
than the covenant window — or the prior is wrong by that factor. The record cannot tell which.

## 3. What this settles

- **On the declared statistic, P9 fails**: gross shorts do not carry the flow at four weeks in
  either category, and the deposit's own rule is to stop and fix the mapping before P1–P3.
- **The mapping the data points to** is the **swap-dealer net short** (or net short by category,
  with producer/merchant on the other side), at an **eight-week** horizon. That is a corrected
  mapping chosen after reading 708 reports; a test of it on the same reports would be reading
  the same data twice. **Its clean sample is the 2024+ reports** — about 90 weekly, 22
  non-overlapping four-week windows, 11 eight-week — which this record has not touched, and
  which is a real out-of-sample test for a flow regression in a way two harvest windows never
  were.
- **The scale gap is the larger finding.** Whatever responds, responds at a fortieth of what the
  derivation's population arithmetic says a $1 rally should produce at these tenors. Before P1–P3
  are worth running on any mapping, the derivation's §3.2 needs to say where the other 97 % of
  the hedge goes.
- **T2's shape is on the wrong category.** Producer/merchant gross short shows the ratchet's
  asymmetry (rallies +78k at rank 0.98, declines −43k at 0.09); swap dealers show its mirror.
  On the net line it is swap dealers that carry the sign. The categories are entangled and a
  design that treats them as two clean books is not describing the report.
- **T5's framing was wrong, not the data:** managed money's net long change is positively
  correlated with hedger short change because both react to price in the same direction; that
  is speculators absorbing the hedge on rallies, which is the premise, stated badly in the
  design and recorded here as such.

**What follows, for the principal.** The derivation's next steps in its own order are P7 (the
survey anchor, needs the Dallas Fed series) and P1–P3, and both assume a mapping that has now
failed as written. The honest next record is a **pre-registration of the corrected mapping —
swap-dealer net short against the 12–24-month strip at eight weeks, with the ratchet and the
calendar as declared clauses — tested once on the 2024-01 → 2026-08 reports**, with the scale
gap stated as the thing it must also explain. That spends no return slice and answers the
derivation's first question on data it has not seen.

**Lesson, recorded:** a category's gross position is two books netted; a mechanism about one
side of one book has to be measured on the net line of the category that holds it, and the
horizon a flow builds over is a prediction to be made, not a range to be reported beside.
