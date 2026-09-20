# D580 STAGE 0 RESULT — **NOT SUPPORTED.** The funding clock is on CME bitcoin, but as a **five-minute unsigned burst**, not the hour the deposit sized: volume at the settlement minute is 1.9× the cycle mean and variance 1.8×, the profile peaks at minute 0 and beats every other top of the hour, yet the declared 60-minute window ranks 0.937 (volume) and 0.874 (r²) in its 96-placement null against a bar of 0.95, clears the bar in **none of six years**, and was strongest 2018–2021 and gone by 2022–2023 as funding magnitudes fell 70 %. **The funding sign orders nothing:** the 30-minute post-move is −1.0 bp (SE 1.5), median zero, rank 0.38 and 0.08 in its two nulls, +4.8 bp in 2021 and −9.6 bp in 2022. Terminal by the deposit's own kill 2 at the declared window and kill 4; no construction follows.

*2026-09-20. Design committed in `382ef54` before the fixture builder and the runner (R8). Fixture
`data/fixtures/fut_btc_1m.csv.gz` built by `scripts/build_fut_btc_1m.py` (3.0 min on six workers
at 89 %; the pool proven bit-identical to the serial decode; five gates green, meta tracked, panel
in the manifest by hash). Runner `scripts/stage0_d580_funding_clock.py`, output
`data/stage0_d580_funding_clock.json`, 25 s. Every audit passed its clean case and raised on its
break inside the run: the CME set by a second path on all 6,611 settlements; the F1 attachment by
`merge_asof` on 3,337; the sign in money (+102 bp injected, −98 negated); the bar-end convention
on a known answer; the volume and r² matrices distinct; the declared-outputs guard. **Read:** BTC
one-minute bars 2017-12-17 23:00 → 2023-12-29 21:59 UTC (1,257,985 bars), MBT from 2021-05-02,
the funding fixture to 2023-12-31, Bybit open interest to 2023-12-31. **Not read:** any bar,
quote or settlement from 2024-01-01; no cost, no book.*

---

## 1. Five amendments to the design, made before any test statistic was read

1. **Presence is the session, not the bar.** Full-size BTC prints a one-minute bar only when it
   trades — 59 % of open minutes (MBT 53 %). The design's literal rule, "bars exist on 50 of the
   60 minutes", would have kept **1,215 of 6,611 settlements** and been a liquidity filter that
   discards the thin 00:00 UTC hour. The runner marks a minute *open* when it lies between a
   trade date's first and last bar, treats an untraded open minute as volume 0 with the close
   carried (r = 0), and requires 50 open minutes: **4,673 settlements**, the ~4,700 the design
   expected. The literal count is in the artifact beside it.
2. **The daily halt sits inside every 00:00 UTC cycle.** The centred 480-minute cycle of the
   00:00 event always contains the 21:00–22:00 (or 22:00–23:00) UTC halt, 60 of 480 minutes, so
   the design's 90 % full-cycle rule would have dropped that hour wholesale; the bar is 80 %.
   Monday 00:00 UTC still falls (the weekend gap) and is excluded from T1, as the design flagged.
3. **The `ohlcv-1m` schema carries no trade count.** T1 runs on volume and r² only.
4. **Eleven of the 95 other placements overlap the window** (offsets within 55 minutes share the
   funding minutes), so a true clock's declared rank is decided against them by noise alone; the
   rank among the **73 non-overlapping placements** (offsets 60 … 420) is reported beside,
   unpromotable, and the declared rank decides.
5. The 08:00 UTC season split uses the actual Europe/London offset at each settlement.

## 2. T1 — the clock is on CME, at the minute

| BTC, 4,294 full-cycle events | window mean ÷ cycle mean | rank in 96 placements (bar 0.95) | p50 / p95 of the null | rank among 73 non-overlapping | beats the 7 other tops of the hour | profile peak |
|---|---:|---:|---:|---:|---|---:|
| volume | 1.097 | **0.937** | 0.992 / 1.106 | **1.000** | yes | **minute 0** |
| r² | 1.097 | **0.874** | 1.014 / 1.121 | 0.918 | yes | minute +2 |

**The minute profile, normalised, minutes −5 … +5:** volume 0.98 0.96 0.96 0.90 0.99 │ **1.92
1.71 1.76 1.49 1.30 1.39**; r² 0.88 0.89 0.94 0.96 0.97 │ **1.77 1.70 1.85 1.65 1.45 1.47**. The
settlement minute and the four after it carry roughly double the cycle's volume and variance;
the minutes before are at or below the mean. That is a five-minute event. Spread over the
declared sixty-minute window it is a 10 % effect, and the placements that beat it are its own
neighbours at offsets 10–30 (which keep the burst and add the minutes after) and, for r², offset
335 after the 08:00 event, which is 13:35 UTC — the US equity open.

**By year** (declared rank volume / r², non-overlapping rank volume / r², volume peak minute):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| declared | 0.93 / 0.80 | 0.93 / 0.81 | 0.94 / 0.95 | 0.94 / 0.94 | **0.54 / 0.66** | **0.84 / 0.64** |
| non-overlapping | 1.00 / 0.85 | 1.00 / 0.86 | 1.00 / 0.99 | 1.00 / 1.00 | 0.58 / 0.70 | 0.90 / 0.71 |
| peak | +4 | +1 | 0 | +2 | −120 | −60 |

No year clears 0.95 on both at the declared window (bar: four of six). **The burst was there
2018–2021 and is not there in 2022–2023:** the profile no longer peaks at the settlement and the
non-overlapping rank falls to 0.58. By hour the 08:00 and 16:00 events peak at 0 and +2; the
00:00 event does not (peak −120; 1,210 events, declared rank 0.59). MBT alone (1,920 events from
2021-05) ranks 0.56 / 0.69.

## 3. T2 to T5 — the sign orders nothing

| | mean bp | n | SE (week blocks) | median | placement rank (bar 0.95) | event-shift rank (bar 0.95) |
|---|---:|---:|---:|---:|---:|---:|
| **y_post(30)**, primary | **−0.99** | 2,220 | 1.53 | 0.00 | **0.379** (p95 +1.49; non-overlapping 0.365) | **0.078** (p95 +2.68) |
| y_post(15) / y_post(60) | −0.70 / −1.54 | | | 0.00 / −1.94 | | |
| y_pre(30) | +1.31 | 2,220 | | | | |

Share positive 46.5 %; trimmed 1 % both tails −0.73; ex-top −3.74; ex-bottom +2.01 — no tail
carries anything. In MBT ticks (2.0 bp at the mean price) the post-move is −0.49 of a tick. The
S−8h rate agrees in sign with the settled rate on 79 % of events (bar 80 %), and with it in
place the post-move is −0.66 bp; with the cross-venue mean +0.15. **T3:** by |F1| tercile −3.3,
−2.8, **+3.1** bp (740 each), Spearman +0.04; by F5 −4.3, +0.8, −0.8. **T4 by year:** 2019 +1.7
(rank 0.80), 2020 +0.5 (0.77), **2021 +4.8 (0.96)**, **2022 −9.6 (0.00)**, 2023 +1.5 (0.67) —
the two adjacent years with the largest magnitudes have opposite signs, and 2023 fails its bar of
0.90; 2018 is 40 events. Mean |F1| by year: 1.8, 2.5, 2.0, 3.0 bp for 2018–2021, then **0.7 and
0.8 bp** for 2022–2023, the share at the default falling from 58 % to 32–40 % as the rates
themselves shrank. **T5:** 00:00 +0.7 bp (rank 0.73), 08:00 −2.0 (0.34), 16:00 −1.6 (0.28); the
08:00 cell in the GMT season, when it coincides with the London cash open, is −8.4 bp at rank
0.03 against +2.9 in the BST season — the confound the design flagged is in the data and it is
not the funding sign. The largest events are ±600 bp (2018-12-20 08:00, 2020-03-19 16:00).

## 4. Verdict, declared rule applied

T1 pooled below 0.95 on both quantities; 0 of 6 years; T2 below both nulls, below 2 bp, negative;
2023 fails its own bar; no clean hour holds both. **NOT SUPPORTED.** By the deposit's §9 this is
kill 2 (no funding-time concentration at the declared resolution) and kill 4 (what concentration
there was is confined to the early years). Nothing follows: no cost gate, no spread fixture, no
pre-registration. The reserved slice 2024-01 → 2026-09 at one minute is unread by this line.

**What the data did say, parked and unpromotable.** The perpetual funding clock reaches CME
bitcoin as a burst of trading at the settlement minute itself — about double the cycle's volume
and variance for five minutes, strongest when funding rates were large (2018–2021) and gone as
they fell — with no direction in it at 15, 30 or 60 minutes. That is an arbitrage print, not a
behavioural flow, and it is the deposit's §1.5 mechanism at a tenth of the horizon it assumed.
A five-minute window chosen now would be chosen on this profile; it is not pre-registered and
will not be on these bars.

**Lessons, recorded in memory.** A contract that prints no bar when it does not trade needs
presence defined by the session, or a bar-count rule becomes a liquidity filter; and an event
window sized before the profile is seen must be reported with the profile at its own resolution
and with the overlapping placements named, or a sharp effect is diluted into its own null.
