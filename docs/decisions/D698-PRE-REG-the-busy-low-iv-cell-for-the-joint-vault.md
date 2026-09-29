# D698 — PRE-REGISTRATION: the busy / low-IV/RV cell on unseen data. A pooled four-slice test for the joint vault run (ES and NQ; the plain break and the opening-range break)

*2026-09-30.*
- *The principal: "Write the pre-reg for the busy/low-IV cell", after
  [D696](D696-STAGE-0-RESULT-lead-survives-the-busy-low-iv-cell.md) found that the lead survives in-sample.*
- *Numbered D698: D697 is the highest number on every branch and in every commit subject, and the other session was
  told before writing.*
- ***Committed alone, before its runner exists.***

**What this record does and does not do.**
- It registers one family for the **joint vault run** (AITODO's programme rule, A10). The vault is 2025-03-01 →
  2026-09-18.
- The runner is built next. It reproduces D696's in-sample numbers, estimates the correlation of the four slices, and
  computes the vault's power. The rule is frozen only after that (`scripts/freeze.py`, as D680).
- **The vault is opened only in the joint run, on the principal's word.** Nothing in this record reads it.

## 0. The claim being confirmed

**On a day with busy recent realised range and low implied-to-realised volatility, a break of the day's reference
level does worse than the root's other breaks.** Busy means D672's compression tercile 3. Low means D691's walk-forward
IV/RV percentile < 1/2. The options market is not pricing more movement on such a day.

**In-sample** (2018-01-09 → 2025-02-28; D696, all gross bp):

| slice | X trades | X mean | the rest | difference | per-trade SD |
|---|---:|---:|---:|---:|---:|
| ES, E4 plain break | 85 | −7.37 | ≈ +3.3 | ≈ −10.6 | 38.3 |
| NQ, E4 plain break | 99 | −14.71 | ≈ +6.4 | ≈ −21.1 | 49.4 |
| ES, D663 opening-range break (60-min F) | 143 | −4.18 | ≈ +0.7 | ≈ −4.9 | 35.7 |
| NQ, D663 opening-range break | 161 | −4.95 | ≈ −0.2 | ≈ −4.7 | 47.2 |

*"The rest" figures are approximate:*
- *for E4 they are derived from D694's B0 means less the X cells;*
- *for D663 they are taken from D663's 2016–2025 all-break means (+0.31, −0.66).*
- *The runner states all of them exactly on the window, as its known answer.*

**The E4 slices were chosen for being the worst cell of a grid**, so their in-sample effect is biased upward (the
winner's curse). The D663 slices were named before the trade was split, so they are much less biased.

## 1. The objects (all known before each session's first bar)

- **The label, per session:**
  - `ctier`: D672's walk-forward compression tier, from rv5 and the overnight range;
  - `p_iv`: the walk-forward percentile of ivrv = ln(IV/RV20). IV is D691's prior-close ATM implied volatility.
  - **X = ctier ≥ 2/3 and p_iv < 1/2.** This is D696's declared cell, including ctier = 1.0.
  - The walk-forward windows run across the in-sample and vault boundary. Every lookback uses only sessions before T.
- **Slice 1 and 2, the E4 plain break** (D668 / D694 / D696, unchanged):
  - a stop at the prior RTH high + 0.25·ATR20 or low − 0.25·ATR20, from 09:30, first fill, no entry after 15:29;
  - an initial stop at the level, trailing 0.25·ATR20, flat at the 15:59 close;
  - gross at the level, one micro.
- **Slice 3 and 4, D663's opening-range break:**
  - the first one-minute close beyond the 09:30–09:59 range, 10:00–11:29;
  - entry at the next bar's close;
  - F = D·ln(close 60 minutes after the entry bar / entry)·1e4.
- **The costs,** for the veto book only (§3): friction once. $4.418 a round trip for MES, $4.067 for MNQ (D668-A2).

## 2. The test (one family, one pooled statistic)

**Per slice s:**
- d_s = mean gross of X breaks − mean gross of the slice's other breaks;
- z_s = d_s / its Welch SE.

**The pooled statistic:** Z = Σ z_s / √(1ᵀ R 1).
- R is the 4 × 4 correlation matrix of the z_s under the null.
- **R is estimated in-sample and frozen before the vault:** a session-block bootstrap (blocks of 20 sessions,
  B = 2,000) resamples sessions jointly across the four slices, so the dependence between roots and breaks on the same
  days is kept.
- Equal weights are declared here. Nothing is re-weighted after the vault.

**The verdict:**

| verdict | condition |
|---|---|
| **PASS** | **Z ≤ −1.2816** (one-sided 10 %, D680's convention for a joint-run look), **and at least 3 of the 4 d_s < 0** |
| **FAIL** | otherwise |
| **UNRESOLVED** | fewer than 40 X breaks across the four slices, or fewer than 8 in either E4 slice |

- **Programme promotion** is flagged separately: p ≤ 0.005 (Z ≤ −2.576), the family's α slot.
- **The slot:** 10, one of the two free ones. It is registered in the programme registry at freeze time.

**The window:**
- the vault sessions whose label is computable;
- **ES's options fixture ends 2026-09-09 and the settle strip 2026-09-10,** so ES loses its last few vault sessions.
  NQ needs an options fixture built past 2025-02-28 (§5).
- The runner counts every excluded session.

## 3. Reported beside the verdict, never gating

- **Each slice's** d_s, z_s, X count and X mean.
- **The veto book,** the tradeable form: the E4 plain break with X days skipped, net at one micro, per root. It is
  reported against the unvetoed break:
  - all four reporting groups, net and gross side by side, Sharpe with Sortino;
  - the component line: ρ with the MACD arm, and, on NQ, ρ with D680's C1.
  - **C1 and X are disjoint:** C1 is compression tercile 1 and X tercile 3, so this family shares no trade with D680.
- **The NQ reversal (D696 §B):** X's hold-to-close move on the E4 break. In-sample it was −23.4 bp.
- **The mechanism,** from D696: MFE, MAE and the pre-entry range share for X against the rest.
- **The by-root and by-break signs,** so a pass carried by one slice is visible.

## 4. Power (a rough estimate now; the runner computes it exactly before the freeze)

**Expected X breaks in the vault** (about 385 sessions, at in-sample rates):

| slice | expected X | SE of d_s |
|---|---:|---:|
| ES E4 | ~18 | ~9.3 bp |
| NQ E4 | ~18 | ~12.0 bp |
| ES D663 | ~33 | ~6.5 bp |
| NQ D663 | ~33 | ~8.6 bp |

**At the full in-sample effect,** the slices' expected z are about −1.1, −1.8, −0.8 and −0.6 (sum −4.2). With the
slices' pairwise correlation between 0.3 and 0.5, **the expected Z is about −1.3 to −1.5.**

| effect kept | PASS probability | promotion probability |
|---|---:|---:|
| 100 % | **~0.5–0.6** | ~0.1 |
| 50 % (a plausible allowance for the E4 slices' winner's curse) | ~0.25 | — |

**The runner's `--power` mode states the exact figures** before the freeze. It simulates the vault from the in-sample
trades (session blocks, the vault's expected counts, the effect scaled to 100 / 50 / 25 / 0 %), using the frozen R.

**The rule written now:**
- **if the PASS probability at 100 % of the in-sample effect is below 0.5, the rule is still frozen, and the record
  goes to the principal** before slot 10 is spent;
- the principal then decides between spending the vault look now, and holding the family for a longer unseen sample
  (§6).

## 5. Prerequisites for the vault look (not built; none reads the vault until the joint run)

1. **The vault-input bar path for ES and NQ,** shared with D680:
   - D644's one-minute fixture built through 2026-09-18 into a separate file;
   - the loader's cut moved, exposed as `--vault-bars` / `--vault-use`;
   - the known answer re-proved on the bars' in-sample part before any vault session is scored.
2. **An NQ options end-of-day fixture past 2025-02-28,** built from the approved raw pull on disk (2026-09-27; about
   48 GB), through D691's gates G1–G5.
3. **ES's IV label past 2026-09-09:** none exists. Those sessions are excluded and counted.
4. **The freeze:**
   - the pre-registration's, the runner's and every imported module's sha256;
   - the in-sample known answers (D696's four cells);
   - the frozen R;
   - the power table;
   - slot 10 registered.
5. **The principal's word** for the joint run.

## 6. The longer route, stated now so it is not chosen after the vault

**A forward sample from 2026-09-19 (Track 2)** would add about 11 E4 and 21 D663 X breaks a root a year.
- **It needs a post-lapse source for ES and NQ option settlements.** The Databento subscription lapses around
  2026-10-11, and the record has no other source yet.
- **Without one, the vault is the only unseen sample.**
- If the principal holds the family back (§4), the forward sample is scored with this same rule when it reaches twice
  the vault's expected counts.

## 7. The runner's assertions (each shown to raise in `--selftest`)

- **Known answers:** on the in-sample window, D696's four X cells are reproduced exactly (counts and means). D663's
  morning F and D694's E4 gross are reproduced through their own checks.
- **Lag:**
  - D691's IV lag audit and canary;
  - `tier_audit` on ctier and p_iv across the in-sample / vault boundary;
  - a canary that lets the label read session T's own settle must raise.
- **The seal:** in every mode except `--vault`, no session ≥ 2025-03-01 reaches the scoring code. `--vault` refuses
  to run without:
  - the frozen file's hashes;
  - the vault-input files;
  - the principal's word given on the command line (D680's pattern).
- **The statistic:**
  - the pooled Z equals a second implementation (explicit sum over slices, R inverted separately);
  - on synthetic data, an injected X effect gives Z < −3, and noise gives |Z| < 2 in about 95 % of draws;
  - chunk == whole for the bootstrap and the power simulation.

## 8. Predictions (about the vault, to be checked only in the joint run)

1. **All four d_s are negative.**
2. **The E4 slices' differences are smaller than in-sample** (the winner's curse); **the D663 slices' are about the
   same.**
3. **NQ's X hold-to-close on the E4 break is negative** (the reversal holds).
4. **The veto lifts the E4 plain break's net on both roots.**
