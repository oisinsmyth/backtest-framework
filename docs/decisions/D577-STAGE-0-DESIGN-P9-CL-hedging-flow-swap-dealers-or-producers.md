# D577 STAGE 0 DESIGN — **P9 of the CL hedging-flow derivation: does producer hedging flow show in the Swap Dealer category or in Producer/Merchant?** The measurement-mapping test the deposit orders first, on positioning data alone, with the strip as the regressor and no return read

**Stage 0 design, committed before the runner exists. Diagnostic on 2010-06 → 2023-12; no session,
report or release from 2024-01-01 on is read; no return outcome is scored anywhere in it.**
Nothing admitted (R15).

*2026-09-20. `HEDGING_FLOW_DERIVATION.md` derives a producer's hedge ratio from covenant
floors, lender ceilings, the lifting restriction and survey breakevens, and lists nine
pre-registerable predictions; its §12 orders the work: "P9 first — confirm the flow appears in
Swap Dealers. If not, stop and fix the mapping." The claim (§1.7): producers hedge OTC with
their lending banks, the banks lay off in NYMEX futures, so bank-intermediated producer
hedges appear in the COT **Swap Dealer short**, direct hedges in **Producer/Merchant**, and a
test that reads only the Producer/Merchant line misses most of the flow. D573 tested the
cross-sectional level of hedging pressure and found a static tilt that lost; it said nothing
about the derivation's claims, which are about the **response** of hedging flow to price, its
asymmetry and its calendar. P9 decides which category those claims can be tested on. It is a
data-layer question and it reads no return.*

**What is on disk.** The CFTC disaggregated futures-only report for CL, 753 weekly reports
2009-07-28 → 2023-12-26, categories producer_merchant, swap_dealer, managed_money,
other_reportable, nonreportable, with long, short and spread per category and open interest;
the CL settlement strip, every listed month per session from 2010-06-04 (71 months listed in
2010, 133 by 2023). Means over the sample, in contracts: producer_merchant **long 202k / short
173k** (the category nets producers against refiners and consumers); swap_dealer **long 29k /
short 103k**; managed_money long 34k / short 22k. The derivation's population — 30–40
independents, ~5 mb/d — would hedge 380k–950k contracts of a twelve-month window at 21–52 %
coverage (§3.2).

---

## 1. The quantities

- **Prices, from the strip, at each report date** (the Tuesday the positions are surveyed; the
  last session on or before it). With *m* the report month's delivery index, `F_k` is the
  settlement of delivery month *m*+*k*. **The hedge-tenor price is `logF_strip = mean of log F_k,
  k = 12 … 24`** — the 12–24-month window the covenants and the derivation put the flow in
  (§1.2, §3.2). `logF_1` (the nearby) is reported beside as the contrast.
- **The regressor:** `ΔF(h) = logF_strip(t) − logF_strip(t−h)` over *h* reports, **h = 4
  primary** (the derivation's 2–4-week response), h = 2 and 8 reported.
- **The outcomes, per category c ∈ {PM, SD, PM+SD}:** `Δshort_c(h)` in contracts over the same
  *h* reports (hedging is selling; a rise in short is more hedging); `Δnet_short_c(h)` =
  Δ(short − long) beside it. Managed money's `Δnet_long` is the counterparty diagnostic.
- No return is computed, forward or contemporaneous. The strip enters as the thing hedgers
  react to, never as the thing predicted.

## 2. The tests, with predictions

Each is per category, so that the categories can be compared on the same statistic.

| # | test | predicted | falsifier |
|---|---|---|---|
| **T1 — response** (P1) | OLS `Δshort_c(4) = a + β_c · ΔF(4)`, Newey–West lag 4, on overlapping weekly changes; the non-overlapping version (every fourth report) beside | **β_SD > 0**, NW t ≥ 2, above the shift null's p95; **the SD share of the hedger response, β_SD / (β_SD + β_PM), ≥ 0.6** (share = 1 if β_PM ≤ 0) | β_SD ≤ 0, or β_PM carries ≥ 60 % → the mapping in §1.7 is wrong |
| **T2 — asymmetry** (P2) | β_c split by the sign of ΔF: β⁺ on rallies, β⁻ on declines | in SD, **β⁺_SD > β⁻_SD** and β⁻_SD within its own null's p05–p95 (no buying on declines: the ratchet) | symmetric response → the ratchet is not in the data |
| **T3 — calendar** (P6) | mean `Δshort_c(1)` on reports dated February–March and August–September (4–8 weeks before the April–May and October–November redeterminations) against all other reports; placement null by rotating the two-month mask through the year | **positive in SD and larger than PM** | no calendar bump in either → compliance flow is not visible weekly |
| **T4 — scale** | β_SD+PM converted to contracts per $1 at the mean strip price, over the 4-report window; the SD and PM short levels against the surveyed hedged volumes | within a factor of three of the derivation's prior, **18–37k contracts per $1** (§7); SD short of the order of the surveyed hedged volume, not an order of magnitude below it | a response two orders of magnitude off the prior → the response is not producer flow |
| **T5 — the other side** (premise 3) | managed money net long share of OI on average; correlation of `Δnet_long_MM(4)` with `Δshort_SD+PM(4)` | positive net long; **negative** correlation (speculators absorb the hedge) | diagnostic; no gate |

**Null for T1 and T2.** The circular-shift null: `ΔF` shifted against `Δshort_c` by every offset
k ∈ [8, N−8] reports, β recomputed at each, enumerated (SE 0); it destroys the alignment and
keeps both series' autocorrelation. The observed β's rank in it is the test. **Null for T3.**
The two-month calendar mask rotated through the 52 weeks, enumerated.

**Decision rule, declared.**
- **P9 SUPPORTED** — T1 holds in SD (positive, above p95, share ≥ 0.6) and T2's asymmetry holds
  in SD. The derivation's P1–P3 are then run on `SD_short + PM_short` as the measured hedger
  footprint, in a separate record; P7 (the survey anchor) follows.
- **PRODUCER/MERCHANT-DOMINANT** — T1 holds in PM and not SD. The mapping in §1.7 is corrected in
  writing and P1–P3 run on PM.
- **NEITHER** — no category responds to the strip. The measurement chain is broken at the first
  link and P1–P3 cannot be run on the COT as designed; the derivation's flow model has no
  weekly instrument, and the record says so. The deposit's own order says stop here.

**Chance.** T1's null is exact; a share ≥ 0.6 given two positive βs is a one-sided cut declared
in advance; T2 and T3 are declared directions. The joint claim is the SD footprint on three
independent statistics.

## 3. Reported beside, diagnostic

Per category and for the nearby `F_1` in place of the strip: β at h = 2, 4, 8 with NW t and the
shift-null rank; the levels of long, short and net by category over time (yearly means); the
three natural experiments inside the sample the derivation names (§11): the 2015–16 collapse
(hedging to floor levels), entering 2020 (hedges held through the crash, no unwind until
distress), 2022–23 (reduced hedging with the strip above the new-well breakeven) — each read
off the category series as a yearly table, qualitative as the derivation says. Audits: the
tenor pick by a second pandas path on the strip pivot; the OLS by two implementations
(statsmodels HAC and numpy normal equations with a hand-rolled Newey–West), proven to raise on a
negated regressor; the shift null's zero offset reproducing the observed β exactly; a
**synthetic-flow check** — a fabricated short series equal to a known multiple of ΔF plus noise
must recover that multiple with the right sign, and its negation the opposite sign — proving
the sign convention "short rises on rallies" before any real β is read.

## 4. What is read, and what is not

The COT fixture, family disaggregated, CL, reports 2009-07-28 → 2023-12-26 (positions only,
keyed on the report date because nothing here is a trading signal — the question is what the
positions did, not when they were known); the CL settlement strip 2010-06-04 → 2023-12-29 at
the report dates. **Not read: any report, release or session from 2024-01-01 on; the June 2025
and March 2026 episodes the derivation cites are in the reserved slice and are not used.** No
return is computed.

## 5. What this record does not do

It does not test P1–P3 (that is the next record if P9 holds), P7 (needs the Dallas Fed series,
not on disk), or P8 (the only prediction that touches a return; its slice stays unread). It
does not estimate λ or the impact coefficient. It does not read the natural-gas report (the
derivation's §10.6 warns the same banks hedge gas producers there).
