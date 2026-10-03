# D790 EXPLORE (scope note, written before the run): the anatomy of gold's China open. Why it moves, whether continuations and reversals have different shapes, and where it sits against its trend

*2026-10-03. The principal: "I can't believe that the wining trades aren't knowable before the trade, I need you to
come up with some viable ideas. First we should identify why gold goes up in price at the Chinese open. Then figure
out if continueations have a particular shape vs reversals have a big spike in a small time frame? Or the relation to
its 200 day SMA etc".*

- **What it is:** a disclosed IN-SAMPLE exploration on 2016–2023. That slice has already been read for this fade, and
  under RULES.md's correction to R14 (lines 751–772) it is free for selection and expensive as evidence.
  - It nominates candidates for a separately pre-registered 2024+ read; it admits nothing.
  - Every feature tried is listed here before the run, and every one is reported.
- **Nothing on or after 2024-01-01 is read.** Sessions, books and costs are D786's build (D765's MGC cell; taker
  \$5.93; D770's passive book, about \$3.03).

## Part 1: why the open moves (no outcome of the fade is used)

1. **The clock's drift:** the mean GC move in every Beijing half-hour across the CME day (2016–2023), with t and the
   share positive. Does gold rise at 09:00–09:30 Beijing more than at other half-hours? Split by year and by US
   clock.
2. **What predicts the open's direction (x), Spearman, from information dated before 09:00 Beijing:**
   - the CME overnight move g, and g_US;
   - the SGE premium: its level, and its 20-day dislocation (D786's build);
   - the day's change in the CNY fix (published 09:15, so inside x: reported as contemporaneous);
   - the AUD's move in the same window (contemporaneous).

## Part 2: the shape of the open's half-hour, and what follows

**The outcome classes (descriptive):**
- **continuation:** sign(y) = sign(x);
- **reversal:** the opposite;
- **big reversal:** the top quartile of the fade's gross.

**The shape features,** from GC's one-minute closes P(09:00) … P(09:30) (isolated prints skipped) and the bar
volumes, all oriented along x:

| feature | definition |
|---|---|
| S1 spike | the largest one-minute \|move\| / Σ\|one-minute moves\| |
| S2 burst | the largest 3-minute move along x / \|x\| |
| S3 time of extreme | the minute of the extreme along x / 30 |
| S4 retrace | (extreme − P(09:30)) / (extreme − P(09:00)), along x |
| S5 efficiency | \|x\| / Σ\|one-minute moves\| |
| S6 first minute | the 09:00 → 09:01 move along x / \|x\| (the auction-like jump) |
| S7 first five | 09:00 → 09:05 along x / \|x\| |
| S8 last ten | 09:20 → 09:30 along x / \|x\| (momentum into the close of the window) |
| S9 volume concentration | the top three minutes' share of the window's volume |
| S10 late volume | the last ten minutes' share of the window's volume |
| S11 relative size | \|x\| / its prior-60-candidate median |

## Part 3: where the open sits against the trend

**Daily closes** are P(15:00 Beijing) on prior sessions only (front contract, not roll-adjusted; the carry step is
about 0.3–0.5% a roll, disclosed).

| feature | definition |
|---|---|
| T1 / T2 / T3 | (P(09:00) − SMA200 / SMA50 / SMA20) / SMA, in percent: unsigned (the regime) and along x (the open stretching away from the average when positive) |
| T4 | P(09:00) / the prior 250 sessions' highest close − 1 |
| T5 | the daily RSI(14) − 50, along x |
| T6 | the prior 20-session return, along x |

## Statistics and the bar for a lead

- **For every feature:** Spearman ρ(feature, gross), on the taker book (every candidate) and on the passive book
  (filled), in:
  - 2016–2019 (discovery);
  - 2020–2023 (replication);
  - the whole.
- **The terciles:** the fade's mean gross and net in each tercile of every feature, both books.
- **Medians of every feature** in the continuation, reversal and big-reversal classes.
- **The null:**
  - the exact rotation of each feature over the candidate sequence (all offsets; two-sided |ρ|);
  - a family-max null: the same offset applied to every feature at once; the largest |ρ| across the features forms
    the family's distribution.
- **A lead (stated now):** on the passive book (the principal's ruling),
  - |ρ| above its own rotation p97.5,
  - the same sign in both halves, with |ρ| ≥ 0.03 in each,
  - and the result states where it sits against the family-max null.
- **A lead is triage only.** It earns a pre-registration with one frozen definition and a 2024+ read, split at the
  SHFE auction change. Nothing is admitted.

## Output

- `scripts/explore_d790_china_open_anatomy.py`;
- `data/explore_d790_china_open_anatomy.json`;
- the findings, in a separate record.
