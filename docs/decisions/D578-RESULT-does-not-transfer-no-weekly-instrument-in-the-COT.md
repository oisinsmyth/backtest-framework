# D578 RESULT — **DOES NOT TRANSFER**: on the 139 unread reports of 2024-01 → 2026-08 the swap-dealer net short's eight-week response to the 12–24-month strip is **−32k contracts a log-point (t −1.1, rank 0.112 in the exact shift null)**, against +71k in sample; the four-week response −8.6k; the gross short −8.5k; the two forward episodes the derivation names produced +677 and +5,302 contracts of net selling, neither in the top quartile. **The corrected mapping was the in-sample data, and the derivation's flow model has no weekly instrument in the COT as the report is built.** The line stops at the measurement, as the deposit's own order says; the CL disaggregated 2024+ reports are spent for it and the CL deferred curve's forward path is seen.

*2026-09-20. Spec committed in `5f0cfcd` BEFORE the runner (R8), on the principal's word. The
runner refused without `--principals-word` and ran under it. **Harness before any forward
number:** the in-sample swap-dealer net-short betas rebuilt by the same code equalled D577's
artifact, +70,910 at eight weeks and +44,057 at four, to 1e-6. Forward: 139 weekly disaggregated
CL reports 2024-01-02 → 2026-08-25, the strip at every one, mean strip $66. Audits on the
forward objects: the tenor by a second strip path (raises on a shift); the OLS by two
implementations (raises on a negated regressor); the synthetic-flow check recovered the sign
convention on the forward regressor; the shift null's zero offset reproduces the observed β.
No return was computed. Runner `scripts/run_d578_sd_net_short_forward.py`, output
`data/d578_sd_net_short_forward.json`, 12 s.*

---

## 1. The declared verdicts

| # | prediction | forward | in sample (seen) | |
|---|---|---:|---:|---|
| **C-1** (primary) | SD net short, h = 8: β > 0, t ≥ 2, above p95; point 30k–110k | **−32,189** · t −1.06 · rank **0.112** (p05 −50k, p50 −5k, p95 +55k); non-overlapping (17 obs) −110k | +70,910 · t 3.71 | **fails** |
| C-2 | SD net short, h = 4: β > 0 | −8,582 · t −0.29 · rank 0.325 | +44,057 | fails |
| C-3 | PM net short, h = 8: β < 0 | **−275,131** · t −1.93 · rank 0.000 | −74,074 | holds by sign; see §2 |
| C-4 | the ratchet on the net line: rallies' β > declines', declines inside null | rallies +74k (rank 0.83, n 60) vs declines +20k (0.51, n 71, inside) | unseen | holds by the letter; the means say the opposite: **ΔNS on rallies −1,228, on declines +7,189** |
| C-5 | calendar: Feb–Mar / Aug–Sep ΔNS > 0 and > other | +680 vs +190 a week (rank 0.78) | unseen | holds by sign, inside its null |
| C-6 | scale within 3× of +1,060 per $1; prior ≥ 10× above | **−487 per $1** | +1,060 | fails |
| C-7 | gross SD short β(8) > 0 and < net | −8,544 · t −0.27 | +37,030 | fails |
| C-8 | June 2025 and March 2026: ΔNS(8) positive and top quartile | **+677** (strip −7.3 % over the eight reports: the rally reversed) · **+5,302** (strip +13.3 %) — positive, neither top quartile | qualitative | fails |
| **verdict** | | | | **DOES NOT TRANSFER** |

## 2. What the forward reports say

**The instrument that responded in sample does not respond forward.** On 2010–2023 the
swap-dealer net short rose about 71k contracts for each log-point the 12–24-month strip
rallied over eight weeks, at t 3.7. On the 139 reports since, it fell 32k, at t −1.1, inside
its shift null at the 11th percentile; over four weeks −8.6k; the non-overlapping eight-week
changes, seventeen of them, give −110k. The gross short is flat (−8.5k). The mean eight-week
change in the swap-dealer net short was **negative on rallies and positive on declines** —
the sign the derivation forbids — even though the split-sample slopes happen to order the
way C-4 asked. C-3's producer/merchant net short falls violently on rallies (−275k a
log-point, rank 0.000): forward, that is the whole two-category picture, one side moving and
the other not, which is not the netting D577 described.

**The two episodes the derivation names as its cleanest forward cases** both show net
swap-dealer selling in the eight reports that follow — +677 contracts after the June 2025
rally, whose strip gain reversed within the window, and +5,302 after the March 2026 spike, on a
+13 % strip — but 5,302 contracts is a fortieth of the derivation's arithmetic for a $9 rally and
sits below the sample's own 75th percentile of eight-week changes. The yearly level did rise —
swap-dealer net short 29k in 2024, 57k in 2025, 87k in 2026 to August, with producer/merchant
net short −17k → −37k → −80k — which is the derivation's story told at the resolution of years,
as D577's natural experiments were. At the resolution of weeks, where the flow model makes its
predictions, there is nothing.

## 3. What this settles

- **The mapping chosen from the in-sample statistics was the in-sample statistics.** D577
  declared the net-short and eight-week results "beside" and said a test of them on the same
  reports would be reading the data twice; this record tested them once on unread reports and
  they did not survive. That is what the beside numbers were worth.
- **The derivation's flow model has no weekly instrument in the disaggregated report as it is
  built.** The categories net producers against refiners and consumers, the swap-dealer line
  nets bank-intermediated hedges against index and consumer clients, and whatever producer flow
  reaches the 12–24-month tenors is either smaller than the population arithmetic by a factor
  of forty or not in these lines at all. P1–P3 cannot be run on it; P7 and P8 are moot until a
  measurement exists.
- **What would be a measurement:** the CFTC's supplemental (index-trader) report to strip the
  index clients out of the swap-dealer line; the disclosed hedge ratios themselves (10-K, 10-Q,
  the surveys the derivation cites) as a quarterly series against the strip, which is the
  derivation's P7 and the level story the years support; or the OTC swap data the banks report
  under Dodd–Frank, which is the flow's actual venue. None is on disk; each is a fetch and a
  record before any regression.
- **Spent:** the CL disaggregated 2024+ reports for the hedging-flow line. **Seen:** the CL
  12–24-month settlement path 2024-01 → 2026-09, read as a regressor; any later CL curve study
  on those tenors must treat it as seen.

**Lesson, recorded:** a statistic reported "beside" a failed primary is not a finding, it is a
hypothesis, and the forward test of it here was the first time the programme had a clean
out-of-sample sample larger than two windows for anything — 139 weekly reports — and the
hypothesis did not survive it. The level of a position tells the derivation's story at the
resolution of years; the flow model's weekly predictions are where it must be tested, and
there the report does not carry them.

---

## 4. Post-mortem (2026-09-20, on the principal's question: why did a clean in-sample fail forward?)

*Script `scripts/diag_d578_postmortem.py`, output `data/d578_postmortem.json`, 9 s. It reads
only what D577 and D578 already read, computes no return and tests nothing new; its harness
rebuilds the in-sample +70,910 and matches D578's to 1e-6.*

**The in-sample number was not an artefact.** On the 696 overlapping eight-week windows of
2010-06 → 2023-12 the response survives every cut that catches an outlier: Newey–West t 4.2, 3.7
and 3.7 at lags 4, 8 and 16; rank 1.000 in its own exact shift null (p95 +31k, which D577 never
ran on the net line); Theil–Sen +65k and Huber +76k; all eight non-overlapping phases positive,
+55k to +95k; +51k with the top 5 % of |Δstrip| removed; +57k (t 1.7) on the windows where
|Δstrip| ≤ 0.10, so it was not a crisis-only relation either.

**It was a 2014–2019 phenomenon pooled with four dead years.** The rolling three-year β at
each year-end:

| 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| +39k | +115k | +161k | +126k | +132k | +135k | +111k | +64k | +31k | +34k | **−0k** |

By era: 2010–14 +97k (t 2.1, Spearman 0.20); 2015–19 **+118k (t 5.5, ρ 0.46)**; 2020–23
**+23k (t 0.8, ρ 0.07)**. The last five in-sample years on their own, 2019–2023, give +18k at
t 0.55, rank 0.78 in their own shift null: inside. The years 2014–2018 carry 82 % of the
covariance; 2019, 2021, 2022 and 2023 contribute nothing or less than nothing; 2020's 14 % is
the April 2020 collapse (five of the eight largest contributing windows). Pooled 2017–2026,
+37k at t 1.5. The forward slice did not break a relation; it continued a regime that had
already reached zero inside the in-sample window, and the pooled t of 3.7 averaged a live
era with a dead one.

**The instrument that carried it shrank to a sixth.** Net short = gross short − gross long, and
the two legs did different work. In sample the swap-dealer gross short responded +37k (t 2.1)
and the gross long −34k (t −4.2): the more significant leg was the long clients cutting on
rallies. By era the short leg went +49k (2010–14), **+79k (2015–19), −0k (2020–23)**; the long
leg −48k, −39k, −24k. The level says why: the swap-dealer gross short was 184k contracts in
2019, then 162k, 113k, 67k, **32k in 2023 (−83 %)**, and the gross long had fallen from 76k
in 2010 to 13k by 2013 and 3–10k in 2021–23. A line a sixth of its former size carries a
sixth of the flow, and the producer-side leg's β was zero before 2024 began. Forward the gross
short rebuilt to 43k / 75k / 94k with β −9k, and the gross long's sign flipped (+24k, t 2.2).
What is stable across both samples is the other category's long side: producer/merchant gross
long +68k (t 2.3) in sample and +241k (t 2.9) forward, consumers and refiners buying rallies,
which is the leg behind D577's "PM net short moves the other way". Why bank-intermediated
producer hedging in this line fell by five-sixths over 2020–2023 is outside the data on disk
(the industry account is reduced shale hedging after the 2021 hedge losses and the
consolidation into producers that hedge little); it is stated here as context, not a finding.

**Neither multiplicity nor power explains it.** D577 reported 27 betas (three categories, three
horizons, gross, net and on F1); six had |t| ≥ 2 and the one taken forward was the maximum, so
the pick was a selection — but at rank 1.000 against a p95 of +31k it would have survived any
family correction, and that is not where the failure came from. The pre-registered bar (t ≥ 2)
was above what an unchanged effect would have produced on 131 reports (expected t ≈ 1.8), a
design fault to record; but the forward point estimate rejects the in-sample β on its own,
90 % interval −78k to +13k against +71k, z −3.7. The difference is real.

**What this corrects in §3.** "No weekly instrument in the COT" is half the truth. There was one,
in the swap-dealer line, from 2014 to 2019, and it faded with the level of the line that carried
it; by 2020 it was gone. **The process fault is D577's:** the era split and the rolling β of a
pooled regression statistic, the guard this repo already keeps for pooled averages, were not
reported before the statistic was pre-registered forward, and neither was the level path of the
instrument. Either would have shown β ≈ 0 at the in-sample window's end, and the forward
prediction "30k–110k" would not have been written. A regression β taken forward is the average
of its regimes; report its time path and its instrument's level beside it, or the forward test
is a test of the average of the dead and the living.
