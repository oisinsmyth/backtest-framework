# D473 RESULT (forward) — K7 is REMOVED: the gated nights paid and so did the others; the reversal is absent on the futures and reversed on cash in 2024–2026. The 2024+ slice is spent for the overnight leg on NQ, ES, SPY and IWM.

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D473-RESULT-forward-K7-is-REMOVED-the-gated-nights-paid-and-so-did-the-others-the-reversal-is-absent-on-the-futures-and-reversed-on-cash-2024-2026-the-slice-is-spent-for-the-overnight-leg.md`. The H1 above is the full title.*

**Forward result of the component record D473, run on the principal's word** (`--forward
--principals-word`, 0.7 min), artefact `data/d473_downleg_forward.json`. Slices read for the first
time: NQ and ES futures **2024-01-02 → 2026-09-09** (677 sessions, 290 / 285 gated nights) and SPY
and IWM cash **2024-01-02 → 2026-08-26**. The rule was declared in D473 §3 before any of it was
read. **Verdict under that rule: REMOVED** (pooled z −1.30, below the 0.5 floor).

## 0. What happened, in one table

| 2024-01 → 2026-09 | gated nights | after a down leg | after an up leg | difference (SE) | in bp: gated / other |
|---|---:|---:|---:|---:|---|
| **NQ K7, exit 09:00, one MNQ** | 290 of 677 (43%) | **+$30.76** (σ 374) | **+$21.29** | +9.47 (26.7) = **+0.4 SE** | +5.15 / +6.17, diff **−1.02 bp** (5.8) |
| ES K7, one MES | 285 of 675 | +$11.37 | +$10.20 | +1.17 (12.9) = +0.1 SE | +2.84 / +4.01, diff −1.17 |
| SPY cash gap after a down gap | 260 (39%) | +0.71 bp | **+9.22 bp** | −8.51 (5.3) = **−1.6 SE** | |
| IWM cash gap after a down gap | 289 | −0.21 bp | +11.10 bp | −11.32 (7.4) = **−1.5 SE** | |
| pooled (NQ bp + SPY bp) | | | | **z −1.30** | |

**The gated component made money: NQ K7's forward net Sharpe at one MNQ is +0.76 (SE 0.64),
gross +0.84, annual net +$2,923, cost 10% of the gross mean.** And it made it for the wrong
reason: the nights it did *not* trade paid almost as much in dollars and **more in basis
points**. The overnight drift on the index futures in 2024–2026 was the strongest in the whole
record (≈ +5.6 bp a night on NQ against ≈ +3.5 in 2016–2023), on both sides of the gate. **The
concentration that defined K7 — down leg then up leg, the other side at zero — is not there.
On the futures the two sides are equal to the SE; on cash the sign is reversed on both symbols.**

By year the reversal was present in 2024 on neither side's favour (NQ +17.6 vs +30.6), **absent
in 2025** (−23.6 vs +51.9: the April 2025 selloff, where buying after a down leg bought
continuation), and present in 2026 (+117.5 vs −40.0, 82 nights). Three years, three answers,
and the declared pooled test says no.

## 1. Predictions (X-e, written in D473 before the read)

| predicted | observed | |
|---|---|---|
| NQ gated +$6 to +$16, other −$6 to +$6 | **+$30.76, +$21.29** | both above the range: the drift, not the gate |
| futures-only z 0.8–2.0 | **+0.35** | wrong |
| SPY gap after a down gap +3 to +8 bp | **+0.71** (other side +9.22) | wrong, sign of the difference reversed |
| pooled z 1.3–2.5 | **−1.30** | wrong |
| dose–response monotone in ≥ 3 of 4 bins | NQ 17 / 9 / 47 / 77 (not monotone; SEs 30–80); ES flat | not supported |
| worst night −$400 to −$900 | **−$1,710** on NQ (σ 374, twice the in-sample 172) | wrong: the 2024–2026 NQ is a bigger contract in dollar terms and a more volatile one |
| "PROVISIONAL more likely than not" | REMOVED | wrong |

Every substantive forward prediction was wrong in the same direction: I predicted the
in-sample structure would persist and it did not. The three independent signs (futures
2016–2023, SPY and IWM cash 2010–2015) were real in their periods and did not carry.

## 2. What is and is not spent

- **Spent, for the overnight-leg family:** the 2024+ futures slice on NQ and ES for the 18:00 →
  09:00 leg (both sides of the gate were read, so the *ungated* NQ/ES overnight leg is read
  too), and the cash 2024+ reserve on SPY and IWM for the 16:00 → 09:30 gap and the
  close-to-close (all four cash cells were printed). **No record may re-read these for an
  overnight-leg construction on these instruments.**
- **Not read:** 2024+ on the full-session hold (W1) and the day leg (W3) beyond what the
  "other side" implies for the leg; every other root (YM, ZN, ZB, GC, CL, 6E, RTY); the 15m
  single-name and cohort reserves; every last-30-minute construction.
- **The 09:30 secondary exit** was read alongside and is worse forward as it was in-sample
  (NQ +$18.44 gated, other +$28.97).

## 3. What stands after this record

- **K7 is REMOVED from the ledger's candidates** under its own rule, with its in-sample line,
  its replication and its forward failure all on the row. Not a pick any more; a closed
  construction on these instruments for the overnight leg.
- **The unconditional overnight drift on NQ and ES was strong in 2024–2026** — this record
  read it as the "other side" and reports it because it was printed, not because it was
  tested: NQ ≈ +$25 a night on both sides at one MNQ, ≈ +5.6 bp. **It is not a candidate
  finding**; it is a fact now known about a spent slice, and any later use of it is
  selection on read data. D468's verdict on the ungated leg (K-family, +0.26 in-sample at
  micro cost) stands as the in-sample number.
- **The structural claim in D472 §5 is withdrawn**: "the drift is almost entirely the nights
  after a down night" held for 2010–2023 on the data read and did not hold in 2024–2026. The
  drift persisted; its conditional structure did not.
- **The process held.** The pick was carried to a forward test with a rule written first, the
  rule fired, and nothing was sharpened in between. Eight years of in-sample multiplicity
  plus a 2-SE replication on an earlier period was not enough; the family null that refused
  this cell in-sample (D470, D472) was right to.

## 4. Files

Runner (unchanged) · `data/d473_downleg_forward.json` · this record · the ledger row · PICKUP.
