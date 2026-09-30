# D725 STAGE 0 PRE-REG — when NQ crosses yesterday's levels, does it keep going, and does the crossing pay one MNQ?

*2026-10-01. The principal: "I love #1, look into it please, do a pre-reg for the premise checks."*
- **The source:** D724's one structural finding. Price reaches yesterday's close, the overnight midpoint and
  yesterday's VWAP more often than an equidistant mirror level (t 4.7 / 3.1 / 2.8), and passes through them rather
  than reverting.
- **Since the day session trends,** the premise is that a crossing of one of these levels continues.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run. The
  result is a separate record.
- **What it is:** a premise check, oracle first. It chooses no rule; a rule is designed with the principal
  afterwards.

## 0. Scope and seal

- **Data:** NQ day session, 2016-01-04 → 2023-12-29, from `fut_NQ_rth_1m`, with the overnight bars from
  `fut_opening_globex_1m`.
- **The seal:** nothing dated 2024-01-01 or later is read. NQ's 2024+ last hour is D716's joint-vault look.
- **Conventions are D724's:**
  - the price at t is the close of the bar starting t−1, as-of;
  - σ_d is the mean day range of the prior 20 sessions;
  - one MNQ at D711's NQ cost line ($4.07 a round trip).
- **Excluded:** roll days, where the prior session's levels belong to another contract.

## 1. The levels (all known by 09:30)

| | level | status |
|---|---|---|
| **L1** | the prior session's 15:59 close | primary |
| **L2** | the prior session's full VWAP | primary |
| **L3** | today's overnight midpoint: (high + low)/2 of the Globex bars 18:00 → 09:29 | primary |
| L4 / L5 | the prior session's high / low | **reported only.** Their break is D668's object, whose in-sample is spent; here they are a reference |

## 2. The crossing event

- **The side:** the open's side of a level is sign(O − L), where O is the 09:30 open. Days that open within one tick
  of L have no side and no event.
- **The crossing:** the first one-minute bar, starting 09:31 → 14:59, whose close is on the other side of L. The
  crossing is known at the next minute's start.
- **The trade:** the direction is s = sign(close − L), the way the price crossed. Entry is that close.
- **One event per level per day:** the first crossing. Later crossings are reported separately, never pooled into the
  primary.

## 3. What is measured

**P1, continuation (primary).**
- **The statistic:** the forward move in the crossing's direction, g_h = s·(P(entry + h) − P(entry)), in σ_d units
  and in MNQ dollars, for h ∈ {15, 30, 60, to 15:59}.
- **The primary horizon is h = 60.** To the close is co-primary for the money line; the other two are reported.
- **Mean and median, and the t clustered by day.** There is one event per level per day, so the clustering is by the
  calendar week.

**The controls, each sharing the treatment's nuisance:**
- **C-mirror, the same distance and clock:** the crossing of the mirror level M = 2·O − L, the same distance from the
  open on the other side, with the same event rule. The statistic is g_h(L) − g_h(M) on days where both events
  exist, plus each one alone.
- **C-rotation, the level's information:** the enumerated rotation of the level's offset from the open, (L − O),
  across sessions (offsets 20 … n − 20; the SE of the p95 is 0).
  - Each day keeps its own prices and open.
  - The level becomes O + (another day's L − O), which keeps the distance distribution and breaks the link to
    yesterday.
  - p50, p95 and rank of the mean g_60 are reported.
- **C-drift:** the mean s·(the same-clock move) across all days, subtracted per event clock. This checks that the
  continuation is not the day's drift in the crossing's direction.

**P2, holding.** The share of events still beyond L at entry + 60, against the mirror's share.

**P3, the money (the oracle first):**
- **As measured:** the mean and median gross per MNQ at h = 60 and to the close, against $4.07 and against 2 × $4.07.
- **The size-only oracle:** the same trades split by terciles of the day's realised range (unknowable in advance).
  It shows whether the continuation's dollars grow with the day's size.
- **Size known the evening before (D724):** the same split by the walk-forward tercile of F_close, D691's M1 without
  the open-time features, built exactly as D724 built it.
  - This is the "another type" of sizing the principal expects to work: a construction whose dollars may grow with
    a size known in advance.
  - F_close is finite from 2018-02, so this split covers 2018-02 → 2023-12 only.
- **By clock:** events crossing 09:31–11:59, 12:00–13:59 and 14:00–14:59.
- **By year, with the largest year's share.**

**All four groups for the h = 60 and to-the-close trades per level:**
- net and gross Sharpe and Sortino (daily over all sessions);
- trades, mean, median, win rate, payoff, skew, kurtosis, and the symmetric 1% trims;
- profitable years;
- the nulls above, with p50 and p95.

## 4. Readings (per primary level; Holm across L1–L3 on the clustered t at h = 60)

| reading | condition |
|---|---|
| **CONTINUES** | mean g_60 > 0 at a Holm-adjusted clustered p < 0.05, **and** above the rotation's p95, **and** above the mirror crossing's g_60 (the paired difference > 0 at t ≥ 2), **and** positive after C-drift |
| **NOT DISTINCT** | g_60 > 0 but it fails the rotation or the mirror. The move is any crossing's, not yesterday's level's |
| **REVERTS** | mean g_60 < 0 at a Holm-adjusted p < 0.05 |
| **NOTHING** | otherwise |

**The go/no-go for a Stage 1 rule design with the principal:**
- **GO:** at least one level reads CONTINUES **and** its mean gross per MNQ at h = 60 or to the close is ≥ 2 × $4.07,
  either overall or in a declared F_close tercile.
- **Otherwise, NO-GO:** the result is written up. Closing the line is the principal's call.

## 5. Runner assertions

- **Lag:**
  - each level and each crossing is re-derived at a sample of days by a second implementation that reads only bars
    starting before the entry minute;
  - a canary that reads the crossing bar's successor must fire;
  - no index may wrap to the day's last bar (D724's 10:00 lesson), and the self-test must show the audit firing on
    such a wrap;
  - F_close uses D671's `forecast_audit` and `tier_audit` with their leak canaries.
- **Sign, in money:** a long crossing up that rises pays +$2 a point at MNQ, and a short crossing down that falls pays
  the same.
- **Right quantity:** the forward move runs from the entry, not from the level. σ_d uses the prior 20 sessions only.
  The mirror sits at exactly the level's distance from the open.
- **The self-test** shows every audit firing on a deliberately broken input, and the rotation's offset 0 equal to the
  observed statistic.
