# D715 STAGE 0 DESIGN — the absorbed morning move (proposal B): follow the first hour's ES direction from 10:30 to the close, one MES, only when that move came with less aggressive flow than a move its size normally carries and at least two of NQ, RTY and YM agree

*2026-09-30. Committed before its runner (`scripts/stage0_d715_absorbed_morning.py`) exists (R8).*
- **The principal:** "Pre-reg, build and run a test for B please".
- **What it is:** in-sample, 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later is read. No programme slot, no
  slice spent.
- **Scored at one MES, $4.42 a round trip,** the only size the account trades.

## 1. Where it came from, and the mechanism

**Origin.** Proposal B of the five-agent round (2026-09-30), the "confirmation by design" lane. It generalises D704's
no-aggressive-push gate (the principal's "MACD plus a volume gate"): off the MACD, off short-gamma days, and onto the
first hour, every session.

**The mechanism.** A first-hour move is one of two kinds, with opposite forward signs:
- **Pushed:** made by aggressive (taker) flow. Its impact is transient, and it reverts:
  - D697: bursts fade;
  - D695: aggressively bought hours continue less (Spearman −0.03);
  - D499: moves on low volume revert less on 7 of 8 roots.
- **Absorbed:** the price moves while the aggressor flow is balanced or against it. That is the footprint of a patient
  institutional order being worked passively. The order is unfinished, so the move continues.
- **Why the plain morning direction does not carry** (D670 −0.59 bp; D673 +0.05 bp): the two kinds cancel.

**What it predicts that a random walk does not:**
1. The 10:30 → close outcome rises with the absorption score.
2. Absorbed moves continue; pushed ones do not, or reverse.
3. ES-idiosyncratic moves (other index roots disagreeing) carry less.

## 2. Data and seals

| input | file | columns used |
|---|---|---|
| ES one-minute bars | `data/fixtures/fut_ES_rth_1m.csv.gz` | day, hhmm (bar start, ET), contract, open, close |
| ES aggressor flow | `data/fixtures/fut_ES_signed_1m.csv.gz` (D695; Sierra, validated against Databento: volume ρ 0.9997, signed share 1.000) | day, hhmm, contract, volume, buy, sell |
| breadth | `fut_NQ_rth_1m`, `fut_RTY_rth_1m` (RTY from 2017-07-10), `fut_YM_rth_1m` | day, hhmm, contract, open, close |
| sessions | `fut_index_sessions.csv.gz` | root, day, bars |

- Every read is cut at day < 2024-01-01 and asserted.
- The flow's minute label equals the bars' (D462: the minute the trade falls in).

## 3. The construction (fixed now)

**Candidate sessions:**
- ES sessions with ≥ 380 one-minute bars, 2016-01-04 → 2023-12-29.
- Not a roll session (the 09:30 bar's contract differs from the previous candidate's), and one contract for every bar
  used.
- The bars 09:30, 10:29, 10:30 and 15:59 are present.
- At least 55 of the 60 first-hour minutes have signed-flow rows for the same contract.

**Inputs, all known by the close of the 10:29 bar:**

| quantity | definition |
|---|---|
| P09:30, P10:30 | the open of the 09:30 bar; the close of the 10:29 bar |
| m | ln(P10:30 / P09:30) |
| σ60 | the sd of m over the previous 20 candidate sessions (≥ 15), prior-only |
| z | m / σ60. **z = 0 is no trade** |
| I | (Σ buy − Σ sell) / Σ volume over the signed minutes 09:30–10:29 |
| Î(z) | a + b·z, OLS on the previous **250** candidate sessions' (z, I), strictly prior. There is no trade until 250 exist (the burn-in, most of 2016) |
| **R** | sign(z) · (I − Î(z)). Negative means less aggressive flow in the move's direction than its size predicts: **absorbed** |
| absorbed | R < the median of the previous 250 sessions' R (strictly prior) |
| breadth | each of NQ, RTY and YM with its own 09:30 open and 10:29 close (one contract) gives a sign. Breadth holds when **at least two available roots agree with sign(z), and at least two are available**. Before RTY, NQ and YM must both agree |

**The trade:**
- side s = sign(z);
- entry at the open of the 10:30 bar, exit at the close of the 15:59 bar;
- gross = s × (exit − entry) × $5, net = gross − $4.42;
- no stop, no target.

**The books:**

| book | takes |
|---|---|
| **B, the primary** | absorbed AND breadth |
| A | absorbed |
| Pu | pushed (not absorbed) |
| Br | breadth |
| E0 (the control) | every candidate after the burn-in: the plain first-hour direction |

## 4. The gates (fixed now)

| gate | what | passes when |
|---|---|---|
| **G1 mechanism** | Spearman ρ between the absorption score A = −R and the gross outcome, over every post-burn-in candidate | ρ > 0 and above the p95 of the **enumerated rotation** of A across candidate sessions (offsets 20 … n − 20; a rank statistic, so it does not reward size selection, per D711-A1) |
| **G2 edge** | book B | mean net > 0 with NW(5) t ≥ 2.0, AND its efficiency Σg / Σ\|g\| above the p95 of the enumerated rotation of B's take mask across candidates (count-matched and size-invariant, D711-A1's form) |
| **G3 ingredients** | point estimates | A's mean gross > Pu's, AND B's mean gross > A's |
| **G4 not one episode** | book B | net > 0 without 2020 and without 2022; no calendar year > 50% of the dollar net (D705's gate); net > 0 in at least half the years with ≥ 10 trades |
| **G5 beyond the drift** | book B | the timing term T = mean of s × (move − that year's mean 10:30 → close move over all candidates) > 0 |

**Readings:**

| reading | when |
|---|---|
| **PASS** | G1–G5 |
| **MECHANISM ONLY** | G1 and G3 hold and B's gross is > 0 at NW t ≥ 2, but G2 (the net) or G4 fails |
| **NEITHER** | G1 fails. The absorption score does not rank the outcome, so B is not the mechanism, whatever B's book shows |
| **FAIL** | otherwise |

**Reported, never gating:**
- **Does the breadth filter add anything beyond deleting trades?** D714 found a cross-root agreement filter on F2 that
  looked good and sat at rank 0.856 against count-matched random deletion. So here, B's Σnet / Σ|net| is ranked against
  20,000 random deletions of A's trades down to B's count.
- **The F2 overlap:** the share of B's gross earned between 15:30 and 16:00 (F2's clock), and ρ of B's daily net with
  F2's;
- the absorption-quintile table (the gradient's shape);
- each book's four groups;
- the unsigned secondary: "quiet" = the first-hour volume below the median of its previous 20 sessions', with quiet
  AND breadth as a book (a volume-only version of absorption);
- long against short;
- by year and by price tercile.

## 5. Size the prize and the in-sample power (stated honestly)

- **B's own guess:** about 3 bp excess a trade for the absorbed half (D704, D695, D499).
- **At the in-sample mean ES of about 3,000,** 1 bp is about $1.50 at MES. That is **about $4.50 gross against $4.42**:
  net near zero.
- **Noise:** the per-trade sd for 10:30 → 15:59 is about 79 bp (D670), or about $120.
- **Trades:** about 7 post-burn-in years × about 250 × ½ (absorbed) × about 0.85 (breadth) ≈ 750 trades.
- **Power at the guessed effect:**
  - expected gross t ≈ 0.04 × √750 ≈ 1.0;
  - G2's net gate (t ≥ 2) has almost no power at it.
  - The test detects a net edge only if the absorbed half carries about 7 bp or more.
- **G1's gradient** uses every candidate (about 1,750). It has more power: an expected ρ of about 0.05 is t ≈ 2.1.
- **So:** a NEITHER or FAIL is informative about the mechanism (G1). A PASS would need an effect more than twice B's
  own guess.

## 6. Correlation and clocks

- **Component line:** at one MES, the daily net Sharpe and Sortino, hit rate, skew, and gross beside net. ρ with #2 (the
  MACD arm, `load_arm()`, as D708 and D709) and with #4 (F2, through D707's `frame()` with its fixture paths pointed at
  the data root, as D709).
- **Clocks:** the hold (10:30 → 16:00) contains F2's 15:30 → 16:00 and D708's closed hourly clocks. The record states
  the overlap; ρ with F2 is computed.

## 7. The runner (assertions each proved to raise in `--selftest`)

1. **Lag audit, a second implementation:** for 40 sampled sessions, a plain loop over the raw fixture rows re-derives
   P09:30, P10:30, I, σ60, the walk-forward (a, b) and the absorbed flag, never calling the vectorised builder. **Break:**
   an Î fitted with the current session included must raise.
2. **Sign audit in money:** a favourable move pays the long and the short positively; net = gross − $4.42.
3. **Right quantity:**
   - the entry (10:30 open) is not the decision price (10:29 close);
   - the absorbed share is about 0.5 after the burn-in;
   - the rotation's offset 0 equals the observed statistic.
4. **The seal:** a 2024-dated row injected into any input raises.
5. **Synthetic:** a planted absorption effect passes G1 and G2; pure noise fails G1 about 95% of the time.

**Speed:** the rotations are single axis-wise calls over at most about 1,700 offsets. The projected wall time is under
2 minutes.

**Output:** `data/stage0_d715_absorbed_morning.json`.
