# D675 STAGE 1 RESULT — the log MACD has no mechanism of its own: it is a clock-blind blend of effects the record already holds, and per root only NQ and CL clear their own null

*2026-09-29. One run of `scripts/d675_macd_kernel_decomposition.py` (`6c8a0300`) under
[D675's design](D675-STAGE-1-DESIGN-the-log-macd-edge-decomposed-exactly.md) (`4ba8b359`), 79 s. Output
`data/d675_macd_kernel_decomposition.json`. It is a diagnostic on D484's already-read 2016-01-04 → 2023-12-29, so it
gives no verdict and admits nothing.*

## The answer in one line

**No declared mechanism fits any root.** Decomposed exactly, D484's edge is three things the record already holds,
summed by a kernel that cannot tell the clock:
- **Recent moves revert in the overnight hours** on six of eight roots. This is D499's effect, worth under a tick.
- **Recent moves continue into the US afternoon,** most strongly on NQ. It is the family of D463's intraday
  momentum; D581 found dealer gamma does not sort the close's continuation.
- **On NQ, the move 14–39 hours ago reverts.** This is the daily fade of D495 and K8.

Per root, D484's traded signal clears its own exact null only on NQ (97.6th percentile) and CL (99.7th). On 6E it
loses beyond chance (2.4th). On ES, YM and CL, most of it is 2020.

## 1. The mechanics held

- **G0:** all 32 B2 cells and P1 pooled (+0.007203157478334437) reproduce D484 bit for bit.
- **The identity:** the kernel sum equals `macd_hist` to 1.4e-13 to 6.4e-12 of its standard deviation on every
  chain, and every partition of every root and hold closed to 1e-10.
- **The audits:** all six fire on their deliberately broken inputs. The lag audit and the second path also passed on
  every real chain.
- **The null:** exact, 1,970–2,031 session offsets per root, so the p95's SE is zero.
- **Forward windows that cross a roll** (§7): 30–37 bars per hold on seven roots and 96 on CL, at H=1, rising in
  proportion to H. They are kept, as D484 kept them.

## 2. The edge per root (mean over the four holds, σ units)

| root | E_S (traded) | S pct in null | E_L1 | ρ(S, L1) | L1 represents S? | CONT | REV | S from 2020 |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| ES | +0.00804 | 0.889 | −0.00325 | 0.56 | **NO** (sign) | −0.00578 | +0.00252 | 84% |
| **NQ** | **+0.01413** | **0.976** | +0.00983 | 0.92 | yes | +0.00311 (0.65) | **+0.00672 (0.989)** | 38% |
| YM | +0.00811 | 0.875 | −0.00172 | 0.73 | **NO** (sign) | −0.00288 | +0.00116 | 110% |
| ZN | +0.00267 | 0.663 | −0.00686 | 0.84 | **NO** (sign) | −0.01004 (0.06) | +0.00318 | −58% |
| ZB | +0.00597 | 0.800 | −0.00757 | 0.71 | **NO** (sign) | −0.00945 (0.07) | +0.00188 | 36% |
| GC | +0.00910 | 0.911 | +0.00371 | 0.68 | yes | +0.00371 | +0.00000 | 5% |
| **CL** | **+0.02339** | **0.997** | +0.01138 | 0.85 | yes | +0.00761 (0.86) | +0.00376 (0.81) | **72%** |
| 6E | **−0.01379** | **0.024** | −0.01160 | 0.84 | yes | −0.01016 (0.06) | −0.00145 | 31% |

Percentiles are in parentheses where they matter. The null's p95 for S is +0.0110 to +0.0134 per root.

**What this corrects.** D484's pooled pass (+0.0072 against a pooled p95 of +0.0043) was read as "a real signal on
eight roots". Per root it is two: NQ and CL. The other five positive roots sit inside their own nulls, and 6E runs
the other way. **The TAIL** (lags ≥ 79, beyond the purity window) is under 10% of E_L1 everywhere, so the roll gaps in
the kernel's memory do not matter.

**On four roots the linear version has the opposite sign to the traded one** (ES, YM, ZN, ZB). There, L1 weights
bars by the size of the histogram, and the large divergences revert. `sign()` caps those extremes. The traded
signal's small positive edge on those roots is therefore not the linear content, and it is inside its null anyway.
The design marks their lag split NOT REPRESENTATIVE, and it is read here only through the clock split below, which
S and L1 share.

## 3. What the decomposition shows: the sign of "recent" depends on the clock

**CONT** (the last 0–13 bars, the part that bets on continuation), split by the clock of the entry bar. Each cell
gives the value and its percentile in the null:

| root | ASIA h18–h02 | EUROPE h03–h08 | US_OPEN h09–h10 | US_MID h11–h13 | US_CLOSE h14–h16 |
|---|---|---|---|---|---|
| ES | **−0.00713 (0.01)** | **−0.00320 (0.04)** | −0.00007 (0.47) | +0.00119 (0.68) | +0.00343 (0.88) |
| NQ | **−0.00421 (0.04)** | **−0.00487 (0.00)** | −0.00081 (0.30) | +0.00417 (0.94) | **+0.00883 (1.00)** |
| YM | −0.00218 (0.18) | −0.00077 (0.32) | −0.00020 (0.46) | −0.00189 (0.23) | +0.00216 (0.76) |
| ZN | **−0.00856 (0.00)** | −0.00282 (0.16) | −0.00071 (0.37) | +0.00164 (0.75) | +0.00041 (0.58) |
| ZB | **−0.00487 (0.02)** | −0.00007 (0.49) | −0.00093 (0.33) | −0.00105 (0.33) | −0.00253 (0.13) |
| GC | **−0.00527 (0.02)** | +0.00497 (0.95) | −0.00046 (0.41) | +0.00132 (0.72) | **+0.00315 (0.96)** |
| CL | −0.00205 (0.21) | +0.00340 (0.90) | **+0.00363 (0.96)** | −0.00103 (0.36) | +0.00365 (0.88) |
| 6E | **−0.00628 (0.00)** | −0.00180 (0.30) | −0.00254 (0.13) | +0.00258 (0.88) | −0.00213 (0.11) |

- **Overnight, recent moves revert.** The Asian-hours cell is at or below the null's 4th percentile on six of eight
  roots. This is D499's finding, from the other side: the hour after a large move reverts in the thin off-hours, and
  D499 found that reversal worth less than a tick.
- **In the US afternoon, recent moves continue,** strongest on NQ: US_CLOSE is at the 100th percentile, 22 times
  CONT's average per bar. It belongs to the family of D463's intraday momentum into the close, but it is broader: any
  of the last ~13 hours, into the whole afternoon block. D463's narrower published form (the first half-hour
  predicting the last) was a third of its published size on ES. D581 found dealer gamma does not decide the close's
  continuation, and D640 found the LETF close-flow version no stronger than its 11:00 placebo.
- **The MACD adds the two with one kernel.** Its continuation weights are paid in the overnight hours and collected in
  the afternoon, so the net CONT is small everywhere. On NQ it is +0.00311, at the 65th percentile.

**NQ's larger piece is REV,** the reversal of the move 14–39 bars ago. It is at the 98.9th percentile and positive at
every target clock (98th percentile in Asian hours, 96th in US_MID, 98th in US_CLOSE). That is roughly "yesterday
reverts", the daily fade D495 and K8 already measured on NQ.

**CL is continuation across its active hours** (Europe 0.90, US open 0.96, US close 0.88). 72% of its traded edge is
2020.

## 4. The fingerprints (§4, as declared)

| | F1 liquidity reversal | F2 metaorders | F3 vol-target feedback | F4 overnight → day | F5 gamma (ES) | F6 settlement / fix |
|---|---|---|---|---|---|---|
| holds on | none | none | none | none | no | **NQ, GC, CL** |

- **F1** fails on (a) everywhere except NQ: REV is under half of E_L1 or inside its null. On NQ it fails (d), which
  §5 shows cannot be read.
- **F2** fails (a) everywhere: CONT is never above its null's p95.
- **F3** fails (a) everywhere.
- **F4** fails everywhere: no root's continuation comes from abroad into the US day. The overnight hours carry
  reversal, not information.
- **F6** holds on NQ, GC and CL, but its fingerprint (an intensity of at least 2 in the root's window) cannot separate
  a settlement flow from §3's afternoon continuation, whose window it shares on NQ. It is read as §3's pattern, not
  as a mechanism.

## 5. Two flaws in my own fingerprints, disclosed

1. **The UP/DOWN split (F1 d, F3 c) is dominated by the forward drift.** With a positive mean forward return m, the
   UP bucket's term `w_k · r⁺ · f` has expectation `w_k · E[r⁺] · m` even when nothing predicts anything. The sign of
   w flips it, and the DOWN bucket gets the mirror term. So the two come out as a large ± pair that nearly cancels.
   On NQ: UP −0.01159, DOWN +0.01831, net +0.00672. Neither fingerprint can be read on a root with drift. A
   demeaned forward return would have removed this, and I did not declare one.
2. **An intensity is a ratio to its region's total,** and GC's REV is +0.00000, so its bucket intensities (559,
   −177) are meaningless.

Neither changes §3, which uses no sign split and no ratio.

## 6. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | G0 bit for bit | **HELD** |
| 2 | identity to 1e-10 | **HELD** |
| 3 | L1 represents S on ≥ 7 roots | **BROKEN**: 4 of 8 |
| 4 | REV is the majority on ≥ 5 roots | **BROKEN**: only NQ |
| 5 | TAIL under 10% everywhere | **HELD** |
| 6 | F1 fits ≥ 3, F4 fits ≤ 2 | **BROKEN**: F1 fits 0 |

I expected a reversal signal in disguise. It is a reversal signal only on NQ, and only at the daily scale. At the
hourly scale it is two effects of opposite sign divided by the clock.

## 7. Component line

Stage 1 is not a trade, so there is no net line. The gross ticks per trade of the traded signal, by D484 §2's
conversion (σ in ticks from the median price and the tick size):

| root | H=1 | H=2 | H=3 | H=5 |
|---|---:|---:|---:|---:|
| NQ | +0.85 | +1.88 | +2.65 | +3.81 |
| CL | +0.45 | +1.04 | +1.70 | +2.78 |
| ES | +0.09 | +0.27 | +0.43 | +0.84 |
| 6E | −0.15 | −0.40 | −0.67 | −0.96 |

NQ's H=5 reproduces D484's +3.849 to rounding (D484 took the best cell; here it is the mean over the four holds of
the S edge at each hold).

## 8. What this decides

**The log MACD is not a mechanism, and a better MACD will not become one.** Every piece it holds has a clock and an
owner:

| piece | clock | the record's measurement |
|---|---|---|
| recent moves revert | overnight, thin hours | D499: under a tick, closed |
| recent moves continue | US afternoon into the close | D463: the published form is a third of its size on ES; D581: gamma does not sort it; D640: the LETF version fails its placebo; **mechanism unidentified** |
| yesterday reverts | daily, NQ | D495 and K8 (the fade after a big day; long the NQ day after a down day) |

**The mechanism-first reading.** The MACD made money on NQ because NQ's afternoon continuation and daily fade happen
to point the same way as its kernel, and its overnight losses are smaller there. That is why it did not transplant
(D506) and why the arm has no portable mechanism (D669–D673).

**Proposals, each the principal's (R15):**
1. **Close the log MACD as a signal line.** A clock-blind filter cannot be repaired into a mechanism. Any successor is
   a clock-specific design built on one of the three pieces above.
2. **For Stage 2, the one piece that carries money is NQ's US-afternoon continuation, and its mechanism is
   unidentified.** Three candidates are already measured:
   - dealer gamma does not sort the close's continuation (D581, ES);
   - the LETF close flow fails its 11:00 placebo (D640);
   - the published relation of Gao, Han, Li and Zhou (2018), the first half-hour predicting the last, is a third of its
     published size on ES and indistinguishable from zero (D463).

   What D675 sees is broader: the last ~13 hours continue into the whole US_MID and US_CLOSE block, and it is
   significant on NQ, not ES. D669 found the admitted arm's gross in the same place (entries after 10:00, held to the
   close). A Stage 2 needs a candidate mechanism the record has not yet measured. It also overlaps the other session's
   break studies (the same roots, the same afternoon), so it is to be coordinated before anything is designed.
3. **Name the correction to D484 in the record:** its pooled pass rests on NQ and CL, not eight roots. That belongs
   in FINDINGS beside D484 when the principal agrees.

## 9. Seal inventory and holdout power (added the same day)

The principal: "We have since learnt that time of day is part of market structure. I have no problem with a time of
day based filter or strategy." Then: "Run steps 1 and 2": the seal inventory, then the power of every clock cell,
before any clock-specific design is written. No return was read for this section.

### 9.1 Where a clock rule chosen from §3 could still be confirmed

| roots | 2024-01 → 2025-02 | the vault, 2025-03-01 → 2026-09-18 | after the vault |
|---|---|---|---|
| **NQ** | spent (D503, the day session to 2026-09) | spent (D503) | — |
| **ES, YM** (and RTY) | read for this very idea: "join the formed move after 10:00" (D673, 2016 → 2025-02), and the break studies on the other branch | joint run only (A10) | index mids 2025-09 → 2026-09 read by D526 |
| **CL, GC** | read by the shock classifier's event windows (D643, to 2025-02); **about to be read by the other session's pre-registration 676**, a root-aware break (day-session continuation) on CL, NG, GC and SI to 2025-02 | joint run only | CL: D626's sample, sealed until its read on 2026-10-10 |
| **ZN, ZB, 6E** | **unread** for any intraday price path. D513–D535 and D622 declared it unread, and pre-registration 676 defers treasuries. | joint run only | — |

Number 676 is the other session's, claimed on `wt/after-d643`. The next free number on every branch is **677**.

### 9.2 Power

`scripts/d675_power.py` → `data/d675_power.json`. For each of the 105 cells (root × {S, CONT, REV} × target clock on
GC, CL, ZN, ZB, 6E, ES and YM):
- `z_in` is the cell's distance from its null median in null standard deviations. The SD is `(p95 − p50)/1.645`, a
  normal approximation of the exact null.
- The expected holdout t, **if the effect is entirely real**, is `|z_in| · √(months in the slice / 96)`.
- The power rule's floor is t = 1.5.

| | |
|---|---|
| cells with \|z_in\| ≥ 1.645 | **19 of 105** (10.5 expected by chance at two-sided 10%) |
| the strongest cell | ZN CONT at Asian targets, z −3.59 (the overnight reversal) |
| its expected t on 2024-01 → 2025-02 | **1.37** at full effect, 0.69 at half |
| on 2024-01 → 2025-02 plus the vault | 2.09 at full effect, 1.04 at half |
| cells reaching t ≥ 1.5 on the one clean slice | **0** |
| the best continuation cells (CL S at Asian targets, CL CONT at US_OPEN, GC CONT at US_CLOSE) | t 0.95, 0.66, 0.68 on slice A; 1.45, 1.00, 1.04 with the vault |

**No clock cell can be confirmed.**
- **Every cell is under the floor even if its whole in-sample effect is real,** and in-sample effects picked as the
  largest of 105 are inflated.
- **The only cells that approach the floor are the overnight reversal,** and those are D499's effect: under a tick,
  with no money even if confirmed.
- **The cells that would carry money are weakest:** NQ's afternoon has no unread slice, and CL and GC continuation
  sit at t ≤ 1.45 with the vault.
- **Reading a slice now would return a number near zero whichever world is true, and spend it.**

**What would change this is a construction that fires more often,** not a longer wait. For example, pooling one
clock effect across the roots that share it: six roots show the overnight reversal. But the pooled effect with money
in it does not exist: the reversal is under a tick, and the continuation is NQ's alone.

**Proposal (R15, the principal's):** close the log MACD line, and do not spend any slice on a clock cell from §3.
Keep the clock map (§3) as a fact of market structure. A future construction may condition on it, provided it is
designed on a window that has not read it.

## 10. CLOSED by the principal, 2026-09-29

"Ok close it." **The log MACD line is closed under R15.** Closed with it:
- D484's signal as a line;
- any MACD variant or re-parameterisation;
- a Stage 2 built on any §3 clock cell.

No unread slice was spent.

**What stays open:**
- **The clock map of §3,** kept as a fact of market structure: recent moves revert in the thin overnight hours and
  continue into the US afternoon. A new construction may condition on it only if it is designed on a window that has
  not read it.
- **The admitted arm** in `BOOK_PROP.md`, as D674 left it.
- **The FINDINGS correction** (§8, proposal 3: D484's pooled pass rests on NQ and CL). It waits for the principal's
  word.

## 11. REOPENED by the principal for one use, 2026-09-30

"Reopen it." The principal reopened the MACD for a **gamma-gated** use only: the 15-minute log MACD on ES on
short-gamma days, in three variants. See
[D699](D699-STAGE-0-DESIGN-the-gamma-gated-15-minute-log-macd-long.md).
- **Why it is new:** the dealer-gamma gate, which D675 never conditioned on. The overnight gap is also spliced out,
  which removes §3's overnight reversal.
- **Still closed:** D484's signal as a line, and any Stage 2 on a §3 clock cell.
