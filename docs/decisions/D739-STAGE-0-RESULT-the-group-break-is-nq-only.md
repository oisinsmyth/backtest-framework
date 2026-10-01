# D739 STAGE 0 RESULT — D735's mechanism does not transfer: no root in metals, energy, rates, FX or grains reads MECHANISM (δ < 0 on 12 of 25, chance), none TRANSFERS, none reaches GO. The group break is NQ's alone. The cross-group line is proposed for closure

*2026-10-01. One run of `scripts/stage0_d739_group_breaks.py` (0.9 min) under D739-A1, via `uv run --with pyarrow`
with `--data-root` set to the main checkout.*
- **The order:**
  - the [pre-registration](D739-STAGE-0-PRE-REG-does-breaking-from-the-group-transfer.md) (`fcf63dea` claims D739);
  - the runner (`8a43559b`);
  - a first launch built the panels, printed each root's day count and stopped inside scoring, with no statistic
    computed;
  - D739-A1 (`30053a23`, the coverage gate) and the runner under it (`1a8b8f47`) were committed;
  - then this run.
- **The audits all passed:**
  - per root, a second implementation re-derived σ_s and the trigger from raw parquet rows on 40 trades, and its
    one-bar-lead canary fired;
  - every member join passed, and its shifted canary fired;
  - C2b's offset 0 reproduced every root's trades;
  - the FW null's offset 0 equals δ̂.
  - The self-test showed the window-length functions equal D735's at L = 390.
- **The data:** fut_day1m, 2016-01-04 → 2023-12-29. **PA was dropped by A1** (205 valid days of about 1,950), so 25
  roots were scored. Nothing dated 2024-01-01 or later was read.
- **The output:** `data/stage0_d739_group_breaks.json`.

## 1. The mechanism (S1): absent everywhere

| group | roots | δ < 0 | the smallest p_low (root) | MECHANISM |
|---|---|---:|---|---|
| METALS | GC, SI, HG, PL | 2 of 4 | 0.195 (PL) | none |
| ENERGY | CL, BZ, HO, RB | 3 of 4 | **0.027 (RB;** clustered t −1.68, Holm 0.67) | none |
| RATES | ZT, ZF, ZN, TN, ZB, UB | 1 of 6 | 0.320 (TN) | none |
| FX | 6A, 6B, 6C, 6E, 6J, 6S | 2 of 6 | 0.397 (6J) | none |
| GRAINS | ZC, ZW, ZS, ZM, ZL | 4 of 5 | 0.068 (ZM) | none |

- **12 of 25 slopes have the declared sign.** That is what chance gives.
- **The only p_low under 0.05 is RB's** (0.027), with a clustered t of −1.68 and Holm 0.67.
- **In rates, five of six slopes are positive** (ZF +0.116, ZN +0.089). In rates, the part of a contract's move the
  curve shares continues *more*, not less. That is the opposite of NQ.
- **NQ's δ against YM was −0.044** (D735); none of these comes close at that significance.

## 2. The trades: no root TRANSFERS; the room is absent almost everywhere

**Per root**, net per contract at its smallest listed size (the round trip from `futures_costs.json`'s rule):

| root (contract) | trades | net (NW t) | gross | C2a p50 / p95; rank | matched-row gain ± SE | O1 room | reading |
|---|---:|---|---:|---|---|---:|---|
| GC (MGC, $5.93) | 1,482 | −$4.46 (−2.37) | +$1.47 | −4.82 / −2.75; 0.61 | +0.21 ± 1.69 | +0.27 | NO ROOM; NOTHING |
| SI (SIL, $8.00) | 1,453 | −$11.25 (−2.65) | −$3.25 | −7.91 / −2.72; 0.15 | −5.90 ± 4.14 | +3.17 | NO ROOM; NOTHING |
| HG (MHG, $4.25) | 1,513 | −$3.71 (−2.94) | +$0.54 | −3.73 / −2.23; 0.51 | +0.86 ± 1.13 | +0.40 | NO ROOM; NOTHING |
| CL (MCL, $5.03) | 1,074 | −$2.57 (−0.94) | +$2.46 | −3.27 / +0.47; 0.61 | +0.88 ± 2.87 | −0.47 | NO ROOM; NOTHING |
| 6E (M6E, $4.38) | 1,317 | −$5.62 (−6.19) | −$1.23 | −4.64 / −3.48; 0.09 | −1.07 ± 0.83 | −1.11 | NO ROOM; NOTHING |
| PL | 1,535 | −$6.44 | +$4.56 | rank 0.54 | −0.29 ± 8.99 | +4.92 | NO ROOM; NOTHING |
| BZ | 1,254 | +$44.17 (+1.78) | +$60.17 | +12.57 / +42.70; 0.957 | +33.67 ± 29.62 | **−60.73** | NO ROOM; DRIFT ONLY |
| **HO** | 1,085 | **+$63.29 (+1.42)** | +$73.49 | −17.04 / +36.52; **0.997** | +72.40 ± 43.20 | +51.81 | DRIFT ONLY |
| RB | 1,074 | +$9.35 (+0.25) | +$19.55 | +29.99 / +77.42; 0.25 | −8.85 ± 37.87 | +47.79 | DRIFT ONLY |
| ZT, ZF, ZN, TN, ZB, UB | 903–1,095 each | −$12.87 to −$61.44 | −$24 to +$1 | ranks 0.01–0.33 | all ≤ 0 | ≤ +$4.17 | NO ROOM; NOTHING (all six) |
| 6A, 6J | 1,355 / 1,282 | +$0.63 / +$2.72 | +$11.63 / +$14.97 | ranks 0.70 / 0.88 | +4.42 / +5.70 (t < 1) | +8.45 / +17.34 | NO ROOM; DRIFT ONLY |
| 6B, 6C, 6S | 1,286–1,502 | −$7.88 to −$24.97 | | ranks 0.02–0.35 | ≤ +1.15 | | NO ROOM; NOTHING |
| ZM, ZL | 1,416 / 1,492 | +$2.92 / +$3.04 | +$18.92 / +$15.04 | ranks **1.000** / 0.979 | +15.50 ± 8.09 / +6.43 ± 6.54 | +10.10 / +8.88 | NO ROOM; DRIFT ONLY |
| ZC, ZW, ZS | 1,431–1,497 | −$11.28 to −$20.41 | | ranks 0.08–0.35 | ≤ −0.53 | | NO ROOM; NOTHING |

- **The family p95** (the maximum over 25 roots) is **+$76.93**. It is set by the full-size energy contracts' dollar
  scale. No root clears it.
- **Holm over the 25 C2a p_high:** nothing ≤ 0.05.
- **The five micro-tradable roots** (GC, SI, HG, CL, 6E) all net negative. Their gross is −$3.25 to +$2.46 against
  round trips of $4.25–8.00.
- **The timing nulls themselves are informative:**
  - on metals, rates, FX and three grains, C2a's p50 is negative (−$1.77 to −$44.66);
  - that is, entering at those minutes in the direction the root has already moved since the window opened LOSES on
    average;
  - these markets mean-revert intraday where NQ trends, so there is no drift for an own-part signal to sit on.
- **The DRIFT ONLY cells with high timing-null ranks** (HO 0.997, ZM 1.000, ZL 0.979, BZ 0.957) are post hoc,
  without MECHANISM, and at full size only:
  - HO's +$63 a full contract has a max drawdown of $47,291, and HO is CLOSED (the principal, 2026-09-30; D719);
  - ZM's and ZL's means are under their round trips (NO ROOM), and their trimmed means are negative;
  - BZ's O1 is −$60.73.
  - None is a lead.

## 3. Readings

- **MECHANISM:** none of 25.
- **TRANSFERS:** none.
- **GO:** none.
- **D739 §5's closing condition holds:** no root in any group reads MECHANISM.

## 4. What it says

1. **D735's effect is NQ's,** consistent with the explanation given then. The part of NQ's move the Dow does not share
   is concentrated mega-cap flow, worked through the day. None of these groups has that structure.
   - Their common factors (the dollar, the rate level, the oil price, the metals complex, the grain complex) do not
     leave an own part that continues.
2. **Most of these markets revert intraday from their window open.** The negative timing-null medians across metals,
   rates, FX and grains say that a move since the open is, on average, given back. That is the opposite of NQ (D727).
   It is the same sign D724 found for NQ's means and D490 for ranges, measured here on the trades' own entry minutes.
3. **Rates point the other way on the mechanism too:** the shared part continues more. The curve moves together, and
   a single contract's own part fades.
4. **Proposed, not decided:**
   - **(a) close the cross-group extension of D735 under R15,** on the principal's word. This study's rule, the group
     legs and the 2016–2023 slice are spent. 2024+ stays unread for these roots.
   - **(b) D737 is unaffected:** it is NQ against YM, frozen in slot 1.
   - **(c) the intraday reversion seen in the timing-null medians is recorded as structure,** not a lead. It is a
     different object (fading the move since the open) and would need its own premise check.
