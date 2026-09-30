# D708 STAGE 0 DESIGN — does the hourly continuation on ES-book short-gamma days choose its side, or only ride the drift?

*2026-09-30. Committed before the runner exists (R8). The runner will be
`scripts/stage0_d708_short_gamma_timing.py`, committed separately before its one run.*
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, on D688's panel. Nothing dated 2024-01-01 or later is read. No
  slice is spent.
- **What it decides:** whether proposal E goes to a pre-registration for the joint vault run, with the timing term as
  its primary statistic.

## Why

A round of five independent research agents (2026-09-30) proposed signals. Proposal E revived D689's hourly
continuation, gated on the ES options book alone. It rests on two points:
- **Trade count:** D706 priced the short-gamma line on once-a-day constructions over G_SUM days. The ES book is short
  on 187 vault days and 101 clean-slice days (D706's output), and the grid trades about five times a day.
- **Cost:** the $4.42 MES round trip is fixed in dollars, so in basis points it has roughly halved at 2025–26 price
  levels.

The principal's objection:

> "the problem with E is that it is always on, it not really a signal?"

The records support the objection in part:
- D689 §5 found that about half the per-trade profit is drift.
- D692 found the short-gamma long side at +$5.55 a MES trade gross (t 3.26) and the short side at +$1.83 (t 0.97).

**The principal's ruling (2026-09-30):** "Timing term as the gate". E passes only if choosing the side adds money
beyond the drift. That means the short trades beat always-short, and the long trades beat always-long, on the same
minutes. If it fails, E is recorded as a drift or size effect, not a signal.

## What the published numbers already imply (arithmetic, not a new read)

Write the next hour's move after an up hour as μ + c₊, and after a down hour as μ − c₋, where μ is the hour's drift
and c the continuation. D692's G_SUM-short cells give:
- long side: μ + c₊ = +$5.55;
- short side: −(μ − c₋) = +$1.83.

With c₊ ≈ c₋ that is **μ ≈ +$1.86 a MES hour and c ≈ +$3.69**. So on the G_SUM population, about two-thirds of the
gross is side choice and one-third drift. Two cautions:
- that split assumes the continuation is symmetric;
- D692's counts differ slightly by side (198 against 181 trades a year).

**The prediction this record declares:** the timing term on ES-book short days is positive, of order +$3 a MES trade
gross. The drift share is under half.

## The population

- **P_ES (primary):** sessions whose ES options book is net short gamma at the prior settlement: G_ES < 0. This is
  D688's construction (D581's Black-76 at the prior settlement, open interest keyed before 10:00), on D688's panel of
  1,989 sessions, 2016-01-05 → 2023-12-29. D706's output counts 858 such sessions in-sample.
- **Its two parts, reported separately:**
  - **P_ES∩SUM:** G_ES < 0 and G_SUM < 0, i.e. every G_SUM-short day (603; D706 found no G_SUM-short day with the ES
    book long).
  - **P_ES\SUM:** G_ES < 0 and G_SUM ≥ 0, about 255 days on which SPX GEX outweighs the ES book.
    - **No record has measured the continuation on these days alone** (the verification pass of 2026-09-30; D689 §5
      caveat 2). D692's "SPX ≥ 0, ES book < 0" cell mixes them with G_SUM-short days.
    - **They matter for the unseen test:** 67 of the vault's 187 ES-book-short days are of this kind (D706: 187 G_ES
      against 120 G_SUM).
- **The contrast population:** G_ES ≥ 0 (long gamma on the ES book), the same clocks.

## The object (D689's declared primary, unchanged)

- **When:** at t = 10:30, 11:30, 12:30, 13:30 and 14:30, on D689's 5-minute grid (the 09:30 open, then each 5-minute
  close).
- **The signal:** m = log P(t) − log P(t−60) in bp. The side is s = sign(m), and rows with m = 0 are dropped (k = 0).
- **The hold:** 60 minutes. The outcome is f = log P(t+60) − log P(t) in bp. In dollars, the gross is
  s·(P(t+60) − P(t)) × $5 at MES and × $50 at full ES.
- **The last exit is 15:30.** The grid never holds 15:30 → 16:00, the clock D707's F2 trades (FINDINGS §100). The two
  are adjacent, never overlapping, and share the instrument. Their correlation is reported (§ the component line).

## The timing term (the primary statistic)

For each decision i on day d at clock t:
- **The time-matched drift:** μ̂(y, t) is the mean of f over every P_ES decision at clock t in the same calendar year y.
  It counts both sides and every row with a finite f, including m = 0. It is the always-long control on the same
  minutes and days, estimated within the year.
  - **Why per year:** a pooled μ̂ would credit a short signal in a falling year (2022) with that year's drift. The
    per-year control removes year-level alignment, which a daily trend filter would capture anyway.
  - **Declared secondary:** the pooled μ̂(t).
- **The timing residual:** τ_i = s_i · (f_i − μ̂(y, t)), converted to dollars at MES with the decision-time price.
- **T:** the mean of τ over the population's trades, with a day-clustered t.
- **The legs:** the long leg's excess is the mean of (f − μ̂) over s = +1 trades (longs over always-long). The short
  leg's excess is the mean of −(f − μ̂) over s = −1 trades (shorts over always-short).

## The gates (all fixed now)

| | gate | passes when |
|---|---|---|
| G1 | **timing** | T on P_ES > 0, day-clustered t ≥ 2.0, and above the p95 of the enumerated day-rotation null N1 |
| G2 | **both legs** | the long leg's excess > 0 AND the short leg's excess > 0 on P_ES (point estimates) |
| G3 | **the mechanism contrast** | within deciles of the same-day realised variance to t (D689's V1 strata), the weighted difference of τ between short-gamma (G_ES < 0) and long-gamma rows is > 0 and above the p95 of the enumerated G_ES-label rotation N2 |
| G4 | **not one episode** | T > 0 without 2020-02-20 → 04-30, and T > 0 without 2022, and T > 0 in at least half the years with ≥ 20 trades |
| G5 | **the unmeasured part** | T > 0 on P_ES\SUM (point estimate; its t reported) |

- In G3, each population's τ uses its own μ̂(y, t). The rotation permutes the day-level label while τ stays fixed. That
  is an approximation, because the drift is not re-estimated under each rotation, and the record states it as one.
- **The gates are on gross.** Cost is judged separately, in the component line.

## Nulls (enumerated; the p95's SE is exactly 0)

- **N1, timing:** day d's schedule of sides is applied to day d+k's outcomes and μ̂. The offsets are k = 10 … n−10,
  cyclic, over the P_ES days in date order (`rot_ks`). It keeps each day's outcomes and the share of long signals, and
  breaks the alignment of side and outcome.
- **N2, gamma label:** D689's V1 enumeration: the day-level G_ES label rotated over all 1,989 sessions, statistic on τ.
- Both are reported with p50 and p95, and the percentile.
- **Reported, not gating:** T under the pooled μ̂; and raw mean(s·f) (E as proposed) beside T. Their difference is the
  drift share.

## The component line and the four groups

- **The book:** the tradable book is E as proposed: sign(m) held for 60 minutes on P_ES, scored at 1 MES ($4.42) and
  1 full ES ($19.24). The costs come from D685's `cost_spec`, as in D689.
- **The four groups (CLAUDE.md):**
  - performance, net and gross, Sharpe and Sortino;
  - the trade distribution with symmetric 1% trims;
  - dependencies: by year, long against short, and top-trade shares;
  - nulls.
- **The price question E rests on:** by year, the gross per MES trade in dollars AND in bp, the round trip in bp at
  that year's mean price, and the fee as a share of gross. This measures the claim that the fee in bp has halved; it
  does not assume it.
- **The always-long control book on the same windows**, with the same groups.
- **Correlation:** ρ of the daily net with the admitted MACD arm (`load_arm`, as D689). Also ρ with D707's F2 on the
  same in-sample days, if its runner exposes a daily series without reading 2024+. If it does not, the record says so.

## Power for the joint run (computed by the runner, declared now)

- **The per-trade signal-to-noise:** T / sd(τ) on P_ES, with the crash window excluded from the sd, as D689 did.
- **The count:** the unseen ES-book-short sessions from D706's output (187 vault + 101 clean = 288), times the
  in-sample trades per P_ES day.
- **The expected day-clustered t,** at 100% and 50% of the in-sample T. The clustering is shrunk by the in-sample ratio
  of the clustered to the naive t.
- **The one-sided 5% pass probability.** No new count of unseen days is made; D706's count is reused.

## Declared readings

| reading | when |
|---|---|
| **SIGNAL: GO for a joint-vault pre-registration** | G1–G5 all pass |
| **DRIFT CARRIER** | raw mean(s·f) on P_ES > 0 at t ≥ 2, but G1 or G2 fails. E is a long bias on short-gamma days, recorded as a drift or size effect, not a signal (the principal's objection upheld) |
| **NOT GAMMA** | G1 and G2 pass, G3 fails. The timing is generic intraday continuation, present on long-gamma days too |
| **EPISODIC** | G1–G3 pass, G4 fails |
| **POPULATION MISMATCH** | G1–G4 pass, G5 fails. The unseen test would have to be restricted to G_SUM-short days, and D706's power applies |
| **NEITHER** | otherwise |

The in-sample result is not independent evidence. The grid was profiled by D684, D689, D690, D692 and D693. The timing
statistic is new, but the population is not, and the record says so.

## Runner specification

`scripts/stage0_d708_short_gamma_timing.py`:
- **Reuse:** it imports D688's runner (as D689 does) for the panel, G_SPX and G_ES. It rebuilds D689's 5-minute grid in
  the same code shape, and never calls D689's premise count (no 2024+ read).
- **Reproduction guards (raise on mismatch):**
  - D688's β_G exactly;
  - D689's primary: G_SUM-short, +$3.77 gross a MES trade, t 2.93, n 2,988, to the cent and the count;
  - D692's "SPX ≥ 0, ES book < 0" cell: +$3.68, t 4.00.
- **The lag audit:** for 40 sampled decisions, a second implementation re-derives m, s and f from the raw 1-minute
  closes (a loop reading `bars` directly, never the grid), and asserts equality. The self-test shifts the side by one
  hour and asserts the audit raises.
- **The sign audit, in money:** a synthetic up-move pays a long positively and a short negatively. τ of a trade whose
  outcome equals the drift is 0.
- **Right-quantity:**
  - assert T ≠ raw mean(s·f), so the drift subtraction is applied;
  - assert per-year μ̂ ≠ pooled μ̂;
  - assert N1's k = 0 column equals the observed T.
- **Seals:** the panel guard asserts max date < 2024-01-01.
- **Speed:** D689's run took 268 s, mostly the panel.
  - N1 is a sparse day-level computation: per-day sums of s·f, s and the μ̂ terms, rotated with `bincount`.
  - N2 reuses D689's `stratified_diff` block structure.
  - Projected about 5 minutes, run once, so it launches as it stands.
- **The self-test (`--selftest`)** runs on a synthetic panel:
  - a planted timing effect must pass G1;
  - a pure drift must fail G1 and pass the raw mean;
  - the broken-lag book must raise.
- **Output:** `data/d708_short_gamma_timing.json`, statistics only and no per-date GEX (the SqueezeMetrics permission
  of 2026-09-28).

## Decisions made here that the principal's ruling did not fix

1. The drift control is per (year, clock) and not pooled. The pooled version is reported.
2. The population is the ES book alone (G_ES < 0), the population the unseen slices hold. Its G_SUM and non-G_SUM parts
   are reported separately.
3. D689's primary cell is kept unchanged (h = 60, k = 0, five clocks). No clock is dropped, even though D692 found
   10:30 weakest, because dropping it now would be selection on a profiled table.
4. G2 (both legs) is a point-estimate gate. With about 190 trades a year a side, a significance gate on each leg would
   be underpowered.
