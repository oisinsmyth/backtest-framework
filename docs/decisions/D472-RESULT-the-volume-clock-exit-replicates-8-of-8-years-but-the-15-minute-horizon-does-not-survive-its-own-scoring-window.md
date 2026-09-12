# D472 — RESULT: the volume-clock exit replicates 8 of 8 years, but the 15-minute horizon does not survive its own scoring window

**2026-09-12.** Runner [`scripts/d472_volume_clock_exit_insample.py`](../../scripts/d472_volume_clock_exit_insample.py) ·
artifact [`data/d472_volume_clock_exit_insample.json`](../../data/d472_volume_clock_exit_insample.json)

**A MEASUREMENT OF A SAMPLING RULE, NOT A STUDY.** No entry signal, no directional forecast, no
Sharpe of any construction. Nothing opened, closed or admitted ([R15](../RULES.md#r15)).
Scoring an actual rule needs a pre-registration ([R8](../RULES.md#r8)); this is not that.

[D471 AMENDMENT 2](D471-RESULT-the-spread-barely-widens-where-the-moves-are-and-path-efficiency-is-exactly-the-random-walk-value-in-every-bucket.md)
found a volume-clock exit worth ~1 pp of breakeven accuracy on **one recent year** of ticks, and
said in writing that the component window is 2016–2023 and that no rule had been scored on it.
This is that window: **2016-01-04 → 2023-12-29**, 792,644 ES RTH 1-minute bars over 2,062
sessions, from `data/fixtures/fut_ES_rth_1m.csv.gz` (**ES passes G1–G5**; only RTY fails G4).
2024+ is the confirmation slice and a hard gate refuses any row past 2023.

---

## 1. The volume-clock exit replicates, and cleanly

| year | price | ann. RTH vol | E\|M\| time | E\|M\| volume | **move lift** | p_be time | p_be volume | **advantage** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 2,103 | 7.8% | 6.49 | 7.16 | +10.4% | 76.26% | 73.79% | **+2.47 pp** |
| 2017 | 2,446 | 4.9% | 4.69 | 5.24 | +11.8% | 86.38% | 82.52% | **+3.85 pp** |
| 2018 | 2,750 | 11.0% | 11.88 | 12.79 | +7.7% | 64.35% | 63.33% | **+1.02 pp** |
| 2019 | 2,912 | 7.8% | 8.90 | 10.12 | +13.6% | 69.14% | 66.85% | **+2.29 pp** |
| 2020 | 3,212 | 15.6% | 19.77 | 21.29 | +7.7% | 58.62% | 58.01% | **+0.62 pp** |
| 2021 | 4,266 | 8.6% | 14.48 | 16.03 | +10.7% | 61.77% | 60.63% | **+1.14 pp** |
| 2022 | 4,101 | 16.1% | 26.06 | 28.56 | +9.6% | 56.54% | 55.97% | **+0.57 pp** |
| 2023 | 4,306 | 9.3% | 15.87 | 17.56 | +10.6% | 60.74% | 59.71% | **+1.03 pp** |
| **pooled** | | | **13.59** | **15.01** | **+10.4%** | **62.54%** | **61.36%** | **+1.18 pp** |

**Positive in 8 of 8 years**, pooled **+1.18 pp** against D471's +1.00 pp on the recent year, at
matched bar count (25.6 against 25.7 a session) and matched mean holding time (15.0 min both).
The move lift is +7.7% to +13.6% here against D471's +15% — **lower, exactly as the runner
predicted before it ran**, because this clock is minute-resolution and a blunted volume clock
should show a smaller advantage. The figure here is a floor.

**The advantage is largest where the level is worst** (+3.85 pp in 2017, +0.57 pp in 2022):
when the move is small relative to cost, capturing 12% more of it moves the accuracy
requirement further. That is arithmetic, not a regime effect.

## 2. And the finding that matters more — the horizon does not survive its own window

D469 and D471 measured the 15-minute bar at **54.8–57.5%** breakeven. **That was 2025-09 →
2026-09.** On the window a component is actually scored on:

    pooled 2016-2023, volume clock     61.4%
    2017                               82.5%      <- impossible
    2016                               73.8%
    2019                               66.9%
    2018                               63.3%
    2021                               60.6%
    2023                               59.7%
    2020                               58.0%
    2022                               56.0%      <- the only year near the recent one

**The mechanism is visible in the table and it is not subtle.** Cost in *ticks* is fixed —
$3 of commission is 2.40 MES ticks and the spread is one tick, at any price. The *move* in
ticks is price × volatility. ES traded at **2,446 with 4.9% vol in 2017** and at **~6,900 with
healthy vol in the year D469 measured**. So the same 15-minute horizon offered **5.24 ticks**
then and **27 ticks** now, against an unchanged 3.41-tick cost.

This is CLAUDE.md's standing lesson in its futures form: *"cost in bp scales inversely with
price; killed D284."* Here it is cost in **ticks** against price, and it did not kill D284's
descendant — it says the 15-minute horizon is **viable only in a high price × high volatility
regime**, and the scoring window contains regimes where it is arithmetically impossible.

**A rule whose breakeven bar swings from 56% to 86% across the in-sample window is a hurdle-P
problem before it is an edge problem** — P5 is consistency, and C-a is a single Sharpe over
2016–2023 that would be dragged down by years in which no accuracy could pay.

## 3. The independent check that made me believe the extreme years

A 4.69-tick 15-minute move is a strange enough number to want verifying outside this file, so
the runner derives the **implied annualised RTH volatility** from it (σ = E|M|/√(2/π), scaled
by √26 bars and √252 days). The column reads **4.9% in 2017**, 15.6% in 2020, 16.1% in 2022,
7.8% in 2016 and 2019. That ordering and those levels match the known history — 2017 was the
famously quiet year, 2020 and 2022 the violent ones — and RTH-only intraday vol sitting below
close-to-close vol is expected, since it excludes overnight gaps. **The extreme early years are
real, not a fixture artefact.**

## 4. And D471 §5's constant reconciles once measured the same way

D471 §5 reported `adverse/|move| ≈ 0.48`. The first run here read **1.35** and that looked like
a contradiction. It was two different statistics: D471 took a **ratio of means**, this took a
**mean of ratios**, which is inflated by bars whose net move is near zero. Computed as a ratio
of means, this window gives **0.49–0.54 by year, 0.50 pooled** — D471's 0.48 replicates over
eight years. Both forms are now reported rather than one being chosen.

So the stop guidance from D471 §5 stands on the in-sample window too, and the volume clock does
**not** worsen it: 0.50 against the time clock's 0.52.

---

## 5. Limitations, all recorded in the artifact

1. **The volume clock is minute-resolution.** No tick data exists before 2025-09, so a boundary
   lands on a minute edge — a ~13-minute bar carries ~8% granularity. This **blunts** the
   volume clock, so §1's advantage is a floor.
2. **V is causal, and that costs exact matching.** It is the trailing 20 sessions' mean RTH
   volume / 26 — never the period's own and never the session's own, which would be look-ahead
   within the day. The consequence is that bars/session is not exactly 26 on the volume clock
   (25.0 to 26.9 by year); busy days produce more bars and pay more total cost. Both clocks'
   frequencies are reported, and no year has the volume clock worse on both frequency and
   per-trade economics.
3. **MES did not exist before 2019-05-06.** Breakeven is quoted at MES cost throughout for
   comparability, but for 2016 to mid-2019 the minimum size was one full ES contract, which
   C-d forbids in a $50k account (D469 §1: one ES contract runs ~$4,070 of daily σ against a
   $500 cap). **The pre-2019 rows are an instrument measurement, not a tradable proposition.**
4. **The 1.009-tick crossing is assumed, not measured, for this era.** `tbbo` does not reach
   back before 2025-09. The one-tick spread is highly likely on ES in RTH throughout, but it is
   an assumption and it is the one that would move every p_be here if wrong.
5. **E|M| in ticks is not comparable across years** — that is the point of §2, and it is why
   the exit comparison is read *within* each year and never across them.

## 6. Checks

`--self-test` carries 14 checks: bar grouping (inclusive ends, tiling with no gap or overlap,
the single-bar case), the volume clock on hand-computed volumes, that it uses volume *before*
each minute so it starts at bar 0, that **a huge minute skips bar ids** — the minute-resolution
limit made visible rather than described — that skipped ids still yield contiguous bars, that a
busy session yields more bars at fixed V, the cost arithmetic, and **that D471's +1 pp
reproduces from its own two E|M| values** (0.96 pp). Adverse excursion is checked on a winning
long and a winning short.

Runtime gates: the fixture's own ES gate results are **read and required to pass** rather than
assumed, `usable_start` is required to precede the window start, and a hard stop raises if any
row past 2023 reaches the measurement.

## 7. What this does not do

- **It scores no rule.** There is no entry, so there is no edge and no Sharpe. A volume-clock
  exit is now measured on 10 years of data across two clocks; **it has never been traded in a
  backtest**, and doing so needs a pre-registration under R8.
- **It does not close the 15-minute horizon** — R15, and §2 is a statement about regimes, not a
  verdict. What it does is move the bar: any 15-minute construction must now clear **~61%
  in-sample**, not the 55–57% the recent year suggested, and must survive years where the bar
  exceeds 70%.
- **Nothing is elevated** into `FINDINGS.md`, `RULES.md` or either book, and nothing is entered
  in `COMPONENTS_PROP.md`.
