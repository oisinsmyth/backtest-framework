# D701 DIAG DESIGN — do D700's 5- and 15-minute channel onsets and D699's V1 carry the same information on short-gamma days?

*2026-09-30. Committed before the runner exists. The runner will be `scripts/diag_d701_channel_v1_overlap.py`,
committed separately before its one run.*
- **What it is:** a diagnostic on the in-sample window both studies already read (2016-01-05 → 2023-12-29,
  short-gamma days). Nothing dated 2024-01-01 or later is read.
- **What it is not:** it trades nothing new, fits nothing, and admits nothing.

## Why

D699's V1 (the 15-minute log MACD histogram, long above +0.5, out below −0.5) and D700's channel onsets (D480's hand
cell spanning 10 bars at a slope of at least 0.1σ a bar, on 5- and 15-minute bars) each carry a small continuation on
short-gamma days. Each sits just short of its declared bar:
- V1 beats the drift at t 1.64;
- the channel beats it at t 1.96 (5-minute) and 1.86 (15-minute).

Both are trend reads on a 15-minute-to-hours scale on the same days, so they may be one signal counted twice. The
principal: "Measure the overlap between the 5- and 15-minute channels and V1's entries first."

## The objects (reproduced, not rebuilt)

- **V1:** D699's functions, unchanged, on D699's tradable short-gamma days. The guard: 572 trades and a mean net of
  +$10.47477440436403, exactly.
- **The channel onsets:** D700's functions, unchanged, at f = 0.1 on the 5- and 15-minute clocks, with D700's
  truncation lag audit re-run. The guard: +60-minute mean excess on short-gamma days of +$4.408950821115721 (5-minute)
  and +$6.764175105858219 (15-minute), exactly.
- **The universe:** the short-gamma days both studies trade. The runner asserts that the two day sets are equal.

## Declared measurements

**A. Coincidence**, each against a time-matched base rate.
1. **V1 at a channel onset:** at each up onset's fill minute, is V1 holding? The base rate is V1's holding share at
   those same minutes, averaged over all short-gamma days. The same is done for down onsets.
2. **The channel at a V1 entry:** at V1's deciding close (a 15-minute close), does an up channel hold on the 5- and on
   the 15-minute clock? The base rate is the up channel's share at those same minutes over all short-gamma days.
3. **The φ correlation** between V1's state and the up channel's state at every 15-minute close from 09:45 to 15:45.

**B. The channel's information without V1.** D700's up and down onsets on short-gamma days, split by V1's state at the
fill (long or flat). For each: the +60-minute signed gross, the time-matched drift control, the excess, its t
clustered by day, and the hit rate. The measure is D700's exactly.

**C. V1's information without the channel.** V1's trades split by whether an up channel holds at V1's deciding close:
once for the 5-minute clock and once for the 15-minute. For each: count, mean net and gross, median, hit, the
time-matched drift excess (D699's control) with its day-clustered t.

## Declared reading (descriptive; power is thin and it is said)

**On each clock, from B and C:**
- **SAME INFORMATION:** the channel's up-onset excess with V1 flat is under a third of its pooled value, with
  |t| < 1, and V1's trades without a channel keep at least two-thirds of V1's mean gross. The channel adds nothing to
  V1.
- **INDEPENDENT:** the channel's up-onset excess with V1 flat keeps at least two-thirds of its pooled value.
- **A CONDITIONER CANDIDATE:** V1's trades with the channel's agreement earn at least one MES round trip ($4.42) more
  a trade than those without. That would be a filter for V1, designed with the principal against V1's oracle (D699
  §1).
- **MIXED:** anything else.

**The limits:**
- Every split halves samples that were already short of t 2, so no split here is evidence of an edge by itself.
- The reading is about which object to carry forward, not about whether it pays.
- No split, clock or threshold is tuned after the run.
