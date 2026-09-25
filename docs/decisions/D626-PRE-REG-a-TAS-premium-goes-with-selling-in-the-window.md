# D626 PRE-REGISTRATION — a TAS premium goes with net SELLING in the settlement window: a confirmation on data no one has read

*Drafted 2026-09-25. It is committed alone, before its runner exists (R8). The bar (κ ≥ 0.2) is the principal's.
The pooling rule in §4 is this record's, and it is shown to the principal before commit.*

## 0. Where this comes from, stated plainly

[D625](D625-PRE-REG-the-TAS-premium-as-a-signed-stand-in-for-window-flow.md) fixed the sign as **+** (a TAS
premium goes with window BUYING) and did not pass. Its control C1 fired on a base-rate effect, and its chosen
measures were at chance. See [D625-RESULT](D625-RESULT-the-TAS-premium-reads-backwards.md).

The post-hoc diagnostic in D625's runner found the **opposite** sign on every sibling sample. The volume-weighted
TAS differential T1, with its sign reversed, agreed with the true window-flow sign beyond chance on HO and RB, in
both halves of 2025-09-25 → 2026-09-18. Cohen's κ was about 0.33–0.49.

**This record is the test of that post-hoc hypothesis, and it therefore reads only data D625 never read:**
- CL and NG post-vault sessions;
- HO and RB sessions after 2026-09-18.

The sibling year is SEEN, and nothing here may reuse it.

A mechanism that fits, stated after the fact: when the market expects selling into the settlement, buying at the
settlement price is attractive, so TAS trades at a premium. The premium would then signal the selling rather than
cause buying. It is a story and not a test. This record tests the sign only.

## 1. The measure and the truth, fixed now

- **The measure, M.** It is the **negative** of D625's T1: the volume-weighted mean TAS differential over the
  session (18:00 ET the evening before → 14:30:00 ET), from the one-second bars of the TAS month matching the
  traded contract. There is one measure, so there is no selection.
- **The truth.** It is the sign of aggressor-signed outright volume in the traded contract, 14:28:00–14:30:00 ET,
  from Databento `trades`. It is bucketed on `ts_recv` and `size` is cast to int64 (D624's deviations).
- **The traded contract** is D624's: for CL and NG, the index month with the largest weight; for HO and RB, the
  most active outright in the window on the one-second bars.
- **Session floor:** 20 true trades in the window. A session with no matching TAS bar is excluded and listed.

## 2. The statistic

**Cohen's κ** of sign(M) against sign(truth). It is agreement beyond what the two series' sign frequencies give
by themselves, so the base-rate effect that fired D625's C1 cannot pass. The conventions:
- sessions whose truth is exactly 0 are dropped and counted;
- a measure of exactly 0 is its own category, so it can never agree.

## 3. Data, all free and none of it read

| roots | sessions | source |
|---|---|---|
| CL, NG | 2026-09-21 → 2026-10-09 (15 NYMEX sessions) | D624's post-vault `trades` plus the scheduled top-up |
| HO, RB | 2026-09-21 → 2026-10-09 (15) | the top-up's `topup-sib-*` jobs: `trades` and `ohlcv-1s` for HO, RB, HOT and RBT from 2026-09-19. They quote at $0.00, and the scheduled top-up takes them |

No CL or NG data dated 2025-03-01 → 2026-09-18 (A6's vault) is read. None of the HO/RB sibling year is read.

## 4. The gate (the principal: "κ ≥ 0.2")

Read ONCE, after the top-up. Power was computed before the run by simulation, with equal base rates and 20,000
draws. A measure with **no** information clears κ ≥ 0.2 by chance **21%** of the time on 15 sessions, **12%** on
30 and **5%** on 60. A per-root bar on 15 sessions is therefore close to a coin flip, so:

- **PASS** if the **pooled κ over all four roots is ≥ 0.2**, about 60 sessions, **and** CL and NG each have κ > 0.
- **UNRESOLVED (near miss)** if the pooled κ is in [0.10, 0.20), or if the pooled κ passes but CL or NG has κ ≤ 0.
- **FAIL** if the pooled κ < 0.10.
- **UNRESOLVED** if fewer than 45 usable sessions are pooled.

The pass probability of the pooled gate at a true κ of 0 / 0.2 / 0.3 / 0.4 / 0.5 is about **0.05 / 0.48 / 0.78
/ 0.94 / 0.99**. Per-root κ is reported beside and never gates alone.

**What a pass buys:** amendment **H1b**, written only after a pass. It is a signed partner to A8's H1a: over the
in-sample, does the sign of Q_rem agree, beyond chance, with the sign of M? M is free for every session from 2017
in the TAS one-second bars. H1b's own pre-registration would come first.

## 5. Checks and controls (each raises)

- **K1, TAS and outright:** bar volume equals summed trade size on `ts_recv`, on ≥ 99.9% of seconds, on every
  root.
- **C1, day shift:** the pooled κ of M_t against truth_{t+1} must satisfy |κ| < 0.2.
- **C2, random signs** (seed 626): the pooled κ must satisfy |κ| < 0.2.
- The runner runs with `-W error::RuntimeWarning`.

## 6. Reported beside, never gating

- Per-root κ, raw agreement, chance agreement, and sign base rates.
- The Pearson r of M against the truth's size.
- κ with the pre-registered D625 sign (+), for completeness. It is the mirror image by construction.
- D625's T2 reversed, as a second look.

## 7. Files, and what this does not touch

- **Runner:** `scripts/validate_tas_sign.py` (`--gate`, `--check`, `--selftest`). It reuses D624's and D625's
  loaders.
- **Output:** `data/ledger_tas_sign_validation.json`.
- **Not read:** no fund data and no price move. No vault data. No sibling-year data.
- **Deviations** are listed in the output and never replace a verdict.
