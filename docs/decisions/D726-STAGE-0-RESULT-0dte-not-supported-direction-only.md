# D726 STAGE 0 RESULT — NOT SUPPORTED on ES and NQ: every sign points the way the 0DTE story says, but none clears 2 SE, and the day's 0DTE dose carries nothing

*2026-10-01. Pre-registered in [D726](D726-STAGE-0-PRE-REG-did-daily-0dte-end-the-close-run.md) (`e75ac90f`).*
- *The runner is `scripts/stage0_d726_0dte_close_run.py` (`--selftest`: 9 canaries raise), run once. Output:
  `data/stage0_d726_0dte_close_run.json`.*
- *In-sample 2018-05-14 → 2023-12-29. No vault, no 2024+ value, no slot.*
- *The principal: "OK I like #1, pre-reg the cheap premise checks, build and run please".*

## 1. The checks (ES is read; NQ is beside)

**The outcome.** The unfiltered last half-hour, K2: the sign of 14:30 → 15:30, held 15:30 → 16:00, every session.
Efficiency e = Σg/Σ\|g\| on gross dollars.

| check | ES | NQ (beside) |
|---|---|---|
| **S1** era: e after 2022-05-16 vs 2018-05 → 2021 | +0.031 vs +0.103: Δ −0.072, SE 0.090, **z −0.80** | +0.038 vs +0.071: Δ −0.033, SE 0.078, z −0.43 |
| S1 with the Jan → May 2022 bulge included (beside) | z −1.28 | z −1.35 |
| **S2** weekday DiD | +0.172, SE 0.180, **z +0.95** | +0.124, SE 0.164, z +0.76 |
| **S3** dose after the date: Spearman(Z, u), n 389 / 392 | **ρ +0.031**, rotation rank 0.73 (p05 −0.090) | ρ +0.034, rank 0.76 |
| **reading** | **NOT SUPPORTED** | NOT SUPPORTED |

**The DiD in the cells** (e, with net dollars a MES trade):
- **Before the date:**
  - sessions without a same-day expiry: +0.194 (+$2.34), 383 sessions;
  - sessions with one: +0.116 (+$0.10), 582.
  - Δ_pre +0.079 (SE 0.106).
- **After the date:**
  - Tuesday and Thursday, now 0DTE days: −0.028 (**−$5.37**), 165;
  - Monday, Wednesday and Friday: +0.066 (−$1.75), 230.
  - Δ_post −0.093 (SE 0.147).
- **So:**
  - Tuesday and Thursday lost about 0.22 of efficiency once they gained daily expiries.
  - Monday, Wednesday and Friday, which already had them, lost about 0.05.
  - **That is the shape the hypothesis predicts. The sampling error is as large as the effect.**

**On NQ:**
- Δ_pre is +0.013, so before the date the no-expiry days barely differed.
- In volatility units, NQ's mean u is unchanged across the date: +0.019 before, +0.020 after.

**Reported only:**
- **The placebo-date profile.** The declared split ranks in the bottom 4 % (ES) and 8 % (NQ) of all 861 and 890 split
  dates. As §2 said, the January → May 2022 bulge sitting just before the date makes this self-fulfilling.
- **The dose before the date,** on expiry sessions: ρ +0.006 (ES) and +0.012 (NQ), both at the null's centre.

## 2. Predictions (§4)

| # | prediction | outcome |
|---|---|---|
| 1 | S1 does not support (Δ negative, z > −2) | **held** (z −0.80) |
| 2 | S2 does not support | **held** (z +0.95) |
| 3 | S3 does not support | **held** (ρ +0.03, the wrong sign) |
| 4 | NOT SUPPORTED | **held** |
| 5 | NQ the same | **held** |

## 3. Meaning (per §2)

- **On these measures, the post-May-2022 loss of the last-half-hour continuation is not shown to be daily 0DTE.** D722's
  reading stands: UNEXPLAINED.
- **The weekday experiment points the right way, but at about 1 SE.**
  - §4's power note applies: these checks could find a large effect, and they did not find one.
  - **This is weak evidence against 0DTE, not a refutation.**
- **The day's 0DTE intensity, relative to its recent norm, carries nothing.** A heavier-0DTE afternoon does not continue
  less. If 0DTE matters, it would be as a regime that set in, not as a dose that varies by day.
- **D716 (NQ F2's vault look) is unchanged.** Nothing here says the vault era is hostile to it beyond what D722 already
  recorded.
- **Not pursued unless the principal asks:** a larger test would need SPX's own 0DTE volume, which is not on disk.

## CLOSED by the principal, 2026-10-01

**The principal:** "Close, Move on".

**Why:**
- The tradeable form (the day's 0DTE dose) carries nothing: ρ +0.03, the wrong sign.
- The weekday hint (about 1 SE) cannot be sharpened in-sample. Its post-date sample is fixed at about 400 sessions, and
  the only extra data is the held 2024 slice and the vault, which a diagnostic does not spend.

**What follows:**
- No 0DTE-conditioned design is registered, and D716 is unchanged.
- **Reopening needs SPX's own 0DTE volume** (not on disk, a paid pull) **and the principal's word.**

