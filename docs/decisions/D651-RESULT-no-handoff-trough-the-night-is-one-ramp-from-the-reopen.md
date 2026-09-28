# D651 RESULT — there is no handoff trough: the night is one ramp, thinnest at the 18:00 reopen and deepest into the cash close; kill 1 does not fire; no pre-vault pull is recommended

*Pre-registered in [D651](D651-PRE-REG-the-time-of-day-liquidity-map-and-the-handoff-kill-1.md) (`3bbf879`),
committed alone before the builder existed (R8). Builder and report: `scripts/build_fut_liquidity_map.py`;
fixture `data/fixtures/fut_liquidity_15m.csv.gz` (gitignored, in the manifest by hash) and its meta; numbers
[`data/d651_liquidity_map.json`](../../data/d651_liquidity_map.json); page
[`docs/results/LIQUIDITY_MAP.md`](../results/LIQUIDITY_MAP.md). **No return was computed.** Every byte read is inside
the programme vault, and only as quoted spread in ticks and touch sizes.*

## The answer in one line

**The staffing-gap mechanism does not show in the quotes.** Of 105 scored (root, window) cells, **one** is a trough
(6J at W3, and it is H0 MARGINAL), three are UNRESOLVED and **101 are NOT A TROUGH**. Each window is deeper than its
thinner neighbour, not shallower. Kill 1 does not fire (61 cells PASS, 29 MARGINAL, 15 FAIL, and the 15 are the five
micros). The candidate set is empty, so the decision is **branch (c)**: no affordable trough, **recommend no
pull**, the principal decides.

## 1. The build, and the check that it is right

13 `bbo-1m` files (7.45 GiB), 6 processes over `files[i::6]`, **0.8 minutes at 94 % of the pool**; 2,424,214 rows,
41 roots, 327 session days, **13,526,478 quoted front-contract minutes**. The largest file was profiled alone first
(16.4 s, 39.4 M rows → 1.17 M front minutes, which is 41 roots × ~22 sessions × ~1,380 minutes).

**Known answer:** [D507](D507-the-spread-census-on-all-41-roots-micros-quote-tighter-than.md)'s fixture reads the
same files with the same front rule into hourly cells. Summed to (root, day, ET hour, spread), the two agree on
**all 888,238 cells** on minutes, touch lots and order counts, with zero difference. `--selftest`: 17 checks, each
guard shown to raise when it is broken (a price column, a sealed session, a wrong tick, the INT64_MAX sentinel,
the 18:00 roll, both DST weeks, strided chunks against the whole, the trough verdict on a halved, doubled and flat
synthetic W3, and the H0 arithmetic).

**One build defect, found and fixed before any statistic was read:** the tick gate first ran on every contract
month and fired on a 0.6-tick spread in October 2025, a deferred month quoting on a coarser tick than the root's
front increment. It now runs on the front contract only, which is D507's placement. The equality above is
measured after the fix.

## 2. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | kill 1 does not fire; ES PASS, MES FAIL | **HELD**: ES W3 R 2.43, MES 0.48 |
| 2 | W3 a TROUGH on ES NQ ZN CL | **FAILED**: all four NOT A TROUGH (x +0.71, +0.30, +0.79, +0.14) |
| 3 | W2 a TROUGH on ZN ZB ES | **FAILED**: all NOT A TROUGH (x +0.08, +0.10, +0.07) |
| 4 | W1 a TROUGH on 6E 6B, not on the index roots | **FAILED** on its first half (6E +0.05, 6B +0.04); the index half held |
| 5 | windows < 0.5 of core depth on the index roots | **FAILED**: ES W1 0.36 and W2 0.44 hold, but W3 0.64, NQ 0.63–0.86, YM 0.80–0.85 |

`x` is the median across sessions of ln(window depth / the thinner neighbour's depth). All intervals are 5-session
moving-block bootstraps, 2,000 draws, seed 651; every interval quoted in §3 is on the page.

## 3. What the profile says instead

Depth at the touch is **one ramp**. It is lowest at the Globex reopen, builds through Asia and Europe with no dip
at either handoff, steps up at the US cash open, and peaks into the 15:00–16:00 close:

| root | thinnest bucket (halt excluded) | 02:00 | 07:30 | 12:00 | deepest |
|---|---|---:|---:|---:|---|
| ES | **18:00**, 12.8 lots, 1.40 ticks | 19.7 | 25.3 | 57.2 | 15:45, 86.3 |
| ZN | **18:00**, 1,043 lots | 3,187 | 4,542 | 6,800 | 14:45, 13,289 |
| CL | **18:00**, 6.3 lots, 2.76 ticks | 7.4 | 8.4 | 10.3 | 14:15, 14.8 |
| 6E | **18:00**, 26.2 lots | 64.5 | 81.9 | 85.1 | 15:00, 108.7 |
| 6J | **18:00**, 38.8 lots | 106.1 | 128.3 | 138.4 | 14:45, 165.1 |

(median touch depth, contracts; ES and CL's spread in ticks at the minimum.) The **spread** agrees: the median
window spread is below the wider neighbour's on ES, NQ, CL and GC in every window (`y` < 0; ZN is pinned at 1.00
tick in every bucket, and 6E and 6J are slightly wider at W3 only), so the night is **wider but not dipping**. Relative to the core, ES quotes
1.09–1.12×, NQ 1.41–1.54×, CL 1.07–1.44×.

**Why W3 read NOT A TROUGH on the roots whose true minimum is at 18:00:** the deposit's W3 averages the deep
post-close hour (16:00–17:00: ES 83 → 47 lots) with the thin reopen (18:00–19:00: 13 → 17 lots), and its after
neighbour (19:00–20:00, ~18 lots) is thinner than that average. The reopen is the day's thinnest two-sided period,
**but it is a session boundary, not a staffing handoff**, and a reopen-only window was not pre-registered. It is
recorded here as a post-hoc observation. Any use of it is a new pre-registration.

**One disclosed specification choice.** The pre-registration says "the hour before / the hour after" on the ET
clock, but W3's 18:00–19:00 half belongs to the next CME session day. The report pairs every window with its
neighbours by **ET calendar date** (the session day less one for buckets at or after 18:00). A Friday close has no
same-evening reopen and drops out, which is why W3 counts ~198 evenings to W1's 257. The selftest proves the
pairing on a synthetic series (150 evenings paired across the halt).

## 4. Kill 1, root by root

`R` = (mean quoted spread × tick value / 2) ÷ (declared commission per side: $3.00 full, $1.50 micro).

- **PASS in every window it trades:** ES NQ CL NG RB HO BZ GC SI HG PL PA ZN ZB UB TN NKD BTC, and ZC ZS ZW in W1
  (their only session window). The metals and BTC reach R 5–44 because their quoted spreads are several ticks wide.
- **MARGINAL:** ZF and ZT (a one-tick book on a small tick: R ≈ 1.3), SR3 (1.9), ZL and ZM (W1), five of the six FX
  roots (R 1.0–1.4; 6S reaches 2.0–2.3 in W1 and W3), RTY in W2 and YM in W1.
- **FAIL everywhere:** MES MNQ M2K MYM MBT (R 0.29–0.75). This is the deposit's §7 foreseen: the commission kills
  it on the micro, not on the parent.

R is a **ceiling**. It is the spread a quoter would keep if the mid never moved against the fill, and adverse
selection, queue position and fill rate are all outside it. That H0 passes on the full-size contracts says only
that the study was not dead on commission. Its kill 2 was always the test that would decide it.

## 5. What this decides, and what it does not

- **The pre-lapse pull (branch (c)).** No root has a window that is both a trough and affordable, so there is no
  window in which the deposit's mechanism would be worth measuring on pre-vault `tbbo`. **Recommended: no pull.**
  The principal decides; nothing was quoted, since branch (c) does not call for a quote.
- **`SESSION_HANDOFF_LIQUIDITY.md`** is not closed by this record (R15: closure is the principal's). Its own
  kill 1 did not fire. Its mechanism, liquidity thinning *at* the handoffs, is not visible in touch depth or quoted
  spread on any of the 39 roots in session for at least one window (LE and HE trade in none of them); the one
  trough, 6J at W3, is MARGINAL on cost.
- **The map stays as cost infrastructure.** Every root's 96-bucket profile (median depth, mean quoted spread,
  dates quoted) is in the JSON for any study that needs time-of-day cost. The obvious reader is
  [D507](D507-the-spread-census-on-all-41-roots-micros-quote-tighter-than.md)'s successors: the night on the index
  roots quotes about 10 % wider on ES and 50 % wider on NQ than the core.

**Limits, stated.** Level-1 depth only: the deposit's F1 wanted five levels, which `bbo-1m` does not carry, and on a
one-tick-pinned book the queue at the touch grows as volatility falls, so touch depth mixes calm with liquidity.
One year, all of it inside the vault window. Quoted spread is a floor on what an aggressor pays. Commission is
declared, never measured (D591).

## 6. The principal's ruling, 2026-09-28

"No pull for the handoff." Branch (c) is taken as recommended: no pre-vault `tbbo` or `bbo-1m` pull is quoted or
submitted for the session-handoff study, so its kill 2 (realised spread against normal hours) stays unscored and
`SESSION_HANDOFF_LIQUIDITY.md` ends here on its measured premise. The map stays as cost infrastructure.
