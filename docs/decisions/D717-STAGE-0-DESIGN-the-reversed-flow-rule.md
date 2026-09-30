# D717 STAGE 0 DESIGN — the reversed flow rule: follow first-hour moves that came with more aggressive flow than their size predicts, fade those that came with less; tested fresh on NQ, with ES reported beside it

*2026-09-30. Committed before its builder and runner exist (R8).*
- **The principal:** "Ok lets go with your recommendation, pre-reg, build and run a reversed rule test". Asked about a
  slot and unseen data, the principal answered "Test in sample, as a full test" and "No" (to scoring unseen data), then
  "insampel".
- **What it is:** in-sample, 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later is read. No programme slot, no
  unseen data.

## 1. Why, and what makes an in-sample test worth anything here

- **What D715 found:** proposal B's absorption score ranked ES's 10:30 → close outcome **backwards** (Spearman −0.061,
  the 0.7th percentile of its rotation). Absorbed moves reversed, and pushed moves continued.
- **The reversed rule on ES was chosen by that result,** so ES cannot test it. Its ES numbers are reported, **not
  counted as evidence**.
- **The fresh test is NQ.** NQ's aggressor flow has never been read in this repo. Sierra holds NQ tick files from NQZ15,
  and no record has built or studied NQ signed flow. The same rule, unchanged, applied to NQ 2016–2023, is a genuine
  out-of-root test within the in-sample years.

**The mechanism now stated** (the literature's usual direction, the reverse of B):
- **Order-flow imbalance** that exceeds what the move's size explains is informed trading crossing the spread. It
  continues.
- **A move made on less aggressive flow than its size predicts** is liquidity-driven, and it reverts.
- This is stated after D715 and is held accountable only on NQ.

## 2. Data and the new fixture

| input | file |
|---|---|
| NQ bars | `data/fixtures/fut_NQ_rth_1m.csv.gz` |
| **NQ aggressor flow (new)** | `data/fixtures/fut_NQ_signed_1m.csv.gz`, built by `scripts/build_fut_nq_signed_1m.py` from `C:\SierraChart\Data\NQ{H,M,U,Z}{16..24}-CME.scid` |
| ES bars and flow (reported) | `fut_ES_rth_1m`, `fut_ES_signed_1m` (D695) |
| sessions | `fut_index_sessions.csv.gz` (root NQ; root ES) |

**The builder** reuses D695's ES builder unchanged: the same record layout, session slicing, minute convention and
seal. Only the root changes (NQ's front contract from `fut_index_sessions`).

**Its validation is declared now** (D695's four checks against `fut_NQ_rth_1m`):
- V1: the median volume ratio in [0.98, 1.02];
- V2: the per-minute volume correlation ≥ 0.98;
- V3: the signed share ≥ 0.99;
- V4: the last trade equals the bar close on ≥ 95% of minutes.

**If it fails,** the study stops and reports why. No outcome is read before the builder passes.

## 3. The construction (D715's, unchanged, except for the side and for breadth)

Per root:
- **Candidate sessions:** ≥ 380 bars, not a roll session, one contract over the bars used, and ≥ 55 of 60 first-hour
  minutes with signed flow.
- **The walk-forward inputs:** m, σ60, z, I, the fit Î = a + b z on the prior 250 candidates, R = sign(z)(I − Î), and
  the median of the prior 250 R. These are D715's `walk_forward`, imported and unchanged.
- **The side:**

| state | side | name |
|---|---|---|
| R ≥ the median | **+sign(z)** | pushed: follow |
| R < the median | **−sign(z)** | absorbed: fade |

- **Breadth is not used.** D715 found it added nothing (rank 0.70 against random deletion).
- **Entry and exit:** entry at the 10:30 bar's open, exit at the 15:59 bar's close.
- **Size and cost:** NQ at **one MNQ** ($2 a point, cost from D685's `cost_spec("NQ", "micro")`, about $4.07). ES at one
  MES ($4.42).

## 4. The gates (on NQ; fixed now)

| gate | what | passes when |
|---|---|---|
| **G1 mechanism** | Spearman ρ(R, the follow outcome sign(z) × move) over every candidate with R | ρ > 0 and above the p95 of the enumerated rotation of R (offsets 20 … n − 20) |
| **G2 edge** | the two-sided book | mean net > 0 with NW(5) t ≥ 2.0, and its efficiency Σg / Σ\|g\| above the p95 of the enumerated rotation of the follow/fade choice across candidates (outcomes fixed) |
| **G3 both halves** | point estimates | pushed-follow mean gross > 0 AND absorbed-fade mean gross > 0 |
| **G4 not one episode** | the two-sided book | net > 0 without 2020 and without 2022; no year > 50% of the dollar net; positive in at least half the years with ≥ 10 trades |
| **G5 beyond the drift** | the two-sided book | the timing term (side × (move − that year's mean move)) > 0 |

**Readings:**

| reading | when |
|---|---|
| **PASS** | G1–G5 on NQ |
| **MECHANISM ONLY** | G1 and G3 pass and the book's gross is > 0 at NW t ≥ 2, but the net or G4 fails |
| **NEITHER** | G1 fails on NQ. The reversal is ES's alone, and D715's inversion is not a mechanism |
| **FAIL** | otherwise |

**Reported, never gating:**
- **ES:** every statistic above, marked "selected by D715: not evidence". Also the two-root pooled book, with NQ and ES
  daily nets summed, beside it.
- **The four groups at MNQ and MES,** the R quintiles, long against short, by year and by price.
- **The component line:** ρ with the MACD arm (#2, NQ, so the overlap matters) and with F2.
- **The clock overlap:** the share of the gross earned 15:30 → 16:00.

## 5. Size the prize and the power (honest)

- **ES's selected reversed book:** about +$8.7 gross a MES trade (D715's halves), about 5.8 bp at ES ~3,000.
- **If NQ carried half of that in bp** (~2.9 bp), at NQ ~11,000 one MNQ bp is ~$2.20: **about +$6.4 gross against
  $4.07**. The per-trade sd is roughly 90 bp, about $200.
- **Trades:** about 1,425 (every post-burn-in candidate).
- **Expected gross t ≈ 0.032 × √1,425 ≈ 1.2** at half ES's effect, and about 2.4 at the full effect. So the gross
  mechanism is testable, and the net gate needs close to the full effect.
- **G1 uses all ~1,675 candidates.** At ρ ~ 0.06 (ES's magnitude) the expected t is about 2.5.

## 6. The runner (`scripts/stage0_d717_reversed_flow.py`)

- **Reuse:** D715's `walk_forward`, `spearman_rotation`, `mask_rotation` and `eff`, imported unchanged. D715's loader
  logic is generalised to a root parameter. The Sierra contract-code normalisation is kept.
- **Assertions:**
  - **the lag audit:** a plain loop over raw rows re-derives m, I, z and R for 40 NQ candidates;
  - **the sign audit:** a follow on a favourable move pays, and a fade on an unfavourable move pays;
  - **right quantity:** the pushed/absorbed split is about 50/50, the side flips exactly on the absorbed half, and the
    rotation's offset 0 equals the observed statistic;
  - **the seal:** a 2024 row raises;
  - **ES reproduction:** the ES path reproduces D715's candidate count (1,961) and G1 ρ (−0.0608) exactly before the
    reversed ES numbers are written.
- **The self-test:** a planted reversed effect passes G1 and G2; noise fails G1 about 95% of the time.
- **Output:** `data/stage0_d717_reversed_flow.json`.
