# D705 PRE-REGISTRATION — a declared SECOND LOOK: three relative-size filters on the ES last-hour continuation at MES (the prior hour's relative size; plus today's volatility; on short-gamma days), scored against a best-of-three, count-matched rotation null

*2026-09-30.*
- *The principal, after [D703](D703-RESULT-development-fail-the-template-became-an-iv-regime-gate.md) failed:*
  - *"Can we come up with a better filter then?"*
  - *chose F2 and F3 at the top 20 % and $4.42;*
  - *then: "Ok add F1 back in. Run the tests on all them."*
- *Numbered D705: D704 is the highest on every branch and in every commit subject, and the other session was told.*
- ***Committed alone, before its runner exists.***

**This is the SECOND look at 2016-01 → 2023-12 for a filter on this trade.**
- D703 was the first. D702's hindsight profile informed both.
- **The choice among three filters is priced by a best-of-three null.** The choice of this family after D702 and
  D703 is not priced, so it is disclosed here.
- **Nothing in-sample can confirm it.** The 2024-01 → 2025-02 slice stays held.

## 0. What D702 and D703 taught, and how this design uses it

| lesson | where it came from | how D705 uses it |
|---|---|---|
| **The edge is big-move-shaped, and the signal is RELATIVE** | D702: the prior hour's size against a normal hour, top third +$9.48 gross (t 3.44) | every filter is on relative inputs |
| **A dollar bar turns a relative signal into a volatility-regime gate** | D703: 167 of 211 trades in 2022 | walk-forward **percentile** thresholds instead |
| **A rotation null of a per-trade mean needs matched counts** | D703: 1,397 of 1,813 offsets were empty books | a percentile rule takes about the same share of days under any rotation, so the null is count-matched by construction |
| **Concentration in one year is the failure signature** | D703 | declared as a gate (§2 (d)) |

## 1. The objects

**The candidates** (D702's, unchanged):
- the 1,917 non-roll ES sessions with F5 ≠ 0, 2016-01-04 → 2023-12-29;
- sign(F5) held 15:30 → 16:00 at 1 MES;
- net = gross − $4.42.

**The inputs**, each known at 15:30 and each built by D702's audited code:
- a = |F5| / σ_F5: the prior hour's size against its trailing 252-session σ;
- b = today's realised volatility 09:30 → 15:30, as ln √(Σ 5-minute r²);
- G_SUM: dealer gamma, SPX GEX plus the ES book, from D688's panel.

**The walk-forward percentile** is D671's `tiers`: a value's share of the previous 250 finite values in candidate
order, strictly earlier; NaN until 250 exist.

**The family, all at the top 20 %:**

| | filter | take the trade when |
|---|---|---|
| **F1** | the prior hour's relative size | tiers(a) ≥ 0.8 |
| **F2** | size and today's volatility | tiers((tiers(a) + tiers(b)) / 2) ≥ 0.8 (D672's composite construction) |
| **F3** | F1 on short-gamma days | G_SUM < 0 and tiers(a) ≥ 0.8 |

**The window:** the candidates on which every member's inputs are defined (tiers(a), the composite's tier and G_SUM
all finite). It starts about 2018 because the composite needs two 250-value burn-ins. It is one window, common to all
three members.

## 2. The development gates, per member

**A member PASSES DEVELOPMENT if all of these hold:**

| # | condition |
|---|---|
| (a) | **edge:** filtered mean net > 0 at MES with one-sided HAC t; Holm across the three members at p < 0.05 |
| (b) | **the best-of-three null:** the member's filtered mean net exceeds the **exact p95 of the best-of-three rotation** |
| (c) | **not one episode:** filtered mean net > 0 without Feb–Apr 2020 |
| (d) | **not one year:** no calendar year holds more than 50 % of the member's total filtered net, **and** at least half of the window's calendar years are net positive |

**How (b) is built.**
- Rotate the three raw inputs (a, b, G_SUM) **jointly**, by every offset from 21 to n − 21, against the candidates'
  fixed outcomes.
- Re-run the walk-forward tiers and all three rules at each offset.
- Take the **maximum** filtered mean net over the three members.
- The joint rotation keeps the inputs' own joint distribution, so every member's count stays near its actual count.
  The runner reports the counts' range across offsets as a check.

**Otherwise:**
- **UNRESOLVED** if the member has fewer than 60 filtered trades in the window;
- **DEVELOPMENT FAIL** otherwise.

**The family's verdict** is the list of passing members. **If none passes, the line closes again,** and a third look
would need the principal's word and would say so.

**Reported, never gating, per member:**
- **The four groups at MES,** net and gross side by side:
  - Sharpe with Sortino, per trade (annualised by the member's own count) and daily;
  - max drawdown; trades a year; hit, median and payoff; skew; the 1 % trimmed means;
  - by year; before and after 2022-05-16; long against short.
- **The component line:** net Sharpe at one MES, $ cost, hit, skew, gross beside net, and ρ with the MACD arm.
- **D690's assessment** of the member's score against the oracle label: AUC and capture. The score is tiers(a) for
  F1 and F3 and the composite's tier for F2.
- **The same members at the top 33 %** (reported only; not in the null).
- **Take everything** on the window.

## 3. The confirmation rule (frozen now; the slice stays held)

**Only a member that passes development is carried to confirmation.**
- **The data:** 2024-01-01 → 2025-02-28, never read for this trade, plus forward data from 2026-09-19 if the principal
  adds it.
- **The rule, unchanged:** walk-forward tiers continue through the slice from earlier sessions only.

| verdict | condition |
|---|---|
| **CONFIRM** | filtered mean net > 0 at one-sided HAC t ≥ 1.2816 |
| **FAIL** | otherwise |
| **UNRESOLVED** | fewer than 30 filtered trades |

**Power, stated before anything is spent** (D702's per-trade sd, about $85):

| member | filtered trades a year | slice trades | expected t at full effect | trades needed for t 1.2816 |
|---|---:|---:|---:|---:|
| F1, F2 | about 48 | about 56 | about 0.8 | about 150 |
| F3 | about 15–20 | about 18–23 | about 0.5 | — |

- **The slice is held until the principal releases it,** once forward data brings the count within reach.
- **The confirmation mode refuses to run without the principal's word.**

## 4. The runner's assertions (each shown to raise in `--selftest`)

- **Known answers:** D702's candidates and lines (take everything; the top 20 % by |F5|, both reproduced), D618 §3c,
  D691's d̄ and D688's β_G, all through D702's build.
- **Lag:**
  - `tier_audit` on tiers(a), tiers(b) and the composite;
  - D702's realised-volatility lag audit and canary;
  - a canary that lets a tier include its own value must raise.
- **Sign, in money:** favourable continuations pay on both sides.
- **The null:**
  - offset 0 reproduces every member's book exactly;
  - chunk == whole across processes;
  - on synthetic data, an injected relative-size effect is found, and a label with no effect passes (b) about 5 % of
    the time.
- **The seal:** no session ≥ 2024-01-01 is read.

## 5. Speed

- Each offset is three tier passes and three rules, with no refit. About 1,850 offsets fan out over processes.
- **Projected:** a few minutes, measured on a few offsets and stated before launch.

## 6. Predictions

1. **F1 passes (a)** at a t near 2 and clears (b), (c) and (d).
2. **F2 lands at or slightly below F1** on mean net. The volatility half adds size, not direction (D702: Spearman
   with gross 0.039 against 0.066).
3. **F3 has the highest mean net but the fewest trades,** and fails (d) or reads UNRESOLVED, because short-gamma days
   cluster in 2020 and 2022.
4. **Every member is weaker after 2022-05-16.**
5. **The best-of-three null's p95 sits near +$3–5 a trade.**
