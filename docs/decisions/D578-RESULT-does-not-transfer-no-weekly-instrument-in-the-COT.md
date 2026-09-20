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
