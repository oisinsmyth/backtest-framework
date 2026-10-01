# D753 STAGE 0 RESULT — SIGNAL, NOT THE LINES: the channel level rule on daily futures clears its timing null narrowly (p 0.039), carried by two events (the SNB unpeg, HO's 2022 spike); the lines do not beat the plain-range control on the declared paired test; it does not earn by the principal's standard

*2026-10-02.*
- *Pre-registration: [D753](D753-STAGE-0-PRE-REG-the-channel-level-rule-on-daily-futures.md) (e9748192), with A1
  (b01254fb).*
- *Runner: `scripts/stage0_d753_futures_channel.py`. Committed before its run (a219260b), with two plumbing fixes
  committed after attempts that stopped before any trade or statistic was computed:*
  - *df0b3ffe: the equity bar's timestamp is a string;*
  - *837ac8c3: the stitch canary skipped a roll whose ratio is exactly 1.*
- *Output: `data/stage0_d753_futures_channel.json`. Wall 64 s.*
- *Personal book (parked until real capital). In-sample only. The vault and the held slice were not read.*

## 0. What held before any number

- **c_eq = 2.842 %:** the median ATR20/close over 2,295,839 equity keep_v2 bars, 2010–2023.
- **The known answer was exact.** The copied line module equals the principal's hand cell (`d480_hand_cell`) at
  r = 1 on all **24** of D399's sampled equity windows, levels and gradients bit for bit.
- **A1.1's diagnostic** (ZN 2018, r 0.122): the power transform and an explicit ×r on every threshold draw the same
  lines (drawn-state agreement 1.0; max level difference 2.7e-15). No hidden constant escapes the conversion.
- **The stitching:**
  - 2,626 rolls, 36 on the fallback ratio (the new contract's 18:00 open over the prior close);
  - 0 sessions dropped;
  - the stitch check and its canary held on every root.
- **The rest:**
  - the truncation lag audit and its canary held;
  - the jump-pointer selection equals the loop on every root;
  - the rotation's vector form equals its loop on 50 offsets;
  - chunk == whole on ZN.

## 1. The reading

| | criterion | result | |
|---|---|---|---|
| **C1** | mean gross y above the shared-offset rotation (3,501 offsets, exact) | **y 0.1756 (t 2.64); p_high 0.0386** (p50 −0.0007, p95 0.1604) | **holds**, narrowly |
| E1 | net mean > 0 at t ≥ 2 | +\$90.29, **t 1.07** | fails |
| E2 | median net ≥ 0 | **−\$86.00** | fails |
| E3 | skew ≥ −0.5 | +13.46 | holds |
| E4 | G1–G3 | G1 ✓ (ex-2 +\$3,446); **G2 ✗ (6 of 12 years)**; G3 ✓ (\$345 a year) | fails |
| **X** | channel − control, paired, > 2 SE | **+0.180 y (SE 0.145), n 90** | **fails** |

**SIGNAL, NOT THE LINES,** by the declared rule.

**What the declared X test could not see.** The arms rarely trade the same session: only 90 of the channel's 1,005
trades pair with a control trade. On the **unpaired** difference (reported, not in the rule) the channel beats the
plain-range control by **+0.249 y (SE 0.072, 3.5 SE)**. The control itself *loses*: y −0.073 (t −2.67) over 7,125
trades at L = 63. The declared test is the paired one, so the reading stands. The disagreement is disclosed, and
§3 says what it would take to resolve.

## 2. Two events carry it (POST HOC inspection: `temp/idle/d753_top_trades.py`, the runner's own functions)

| | trade | |
|---|---|---|
| **largest \$** | **HO short, 2022-03-09 → 03-15** (the post-invasion heating-oil spike faded at the channel top; full contract, \$42,000 a point) | **+\$63,952 = 70 % of all net.** Without it, the mean is **+\$26.69** a trade |
| **largest y** | **6S long, 2015-01-12 → 01-16** (bought at the channel bottom three days before the SNB removed the EUR/CHF floor) | **+30.4 σ**, one trade |
| largest losses | PA long, 2021-06-15 (−\$26,956); then four more PA/RB break exits | PA is full-size palladium |

**The tails:**
- **y without the top 1 % of trades: 0.062** (from 0.176); without the bottom 1 %, 0.225; the median y is −0.280.
- **In dollars,** the 1 % trims are ex-top −\$64.01, ex-bottom +\$171.78, both +\$16.66.
- **Shares:** the top root, HO, is 71 % of net; the top year, 2022, is 63 %.

**C1's margin over its null is about the size of one SNB trade.** That trade alone adds 0.030 to mean y; the margin
over p95 is 0.015. The rotation keeps such events in its distribution, which is why p is 0.039 and not smaller. But
the reading rests on the event, not on a steady edge.

## 3. Reported, never chosen from

**By sector (y mean; net mean \$):**

| sector | y | net |
|---|---|---|
| equity index | **+0.469** | +\$84.72 |
| energy | +0.328 | +\$854.99 (HO's trade) |
| metals | +0.259 | −\$23.11 |
| livestock | +0.246 | +\$61.64 |
| FX | +0.180 | +\$100.73 (6S) |
| grains/oilseeds | +0.022 | −\$47.67 |
| **rates** | **−0.086** | −\$103.96 |
| BTC | −0.122 | −\$38.35 (13 trades) |

**Excluding energy:** 905 trades, y 0.159, net +\$5.80 a trade.

**The rest:**
- **Long vs short:** y 0.182 against 0.170; net +\$6.4 against +\$176.0 (HO's short).
- **Hold:** y rises with the hold (H 1 / 3 / 5 / 10 / 20: 0.083 / 0.099 / 0.176 / 0.153 / 0.225), but net per trade
  falls past H = 5 (+\$47 / +\$49 / +\$90 / −\$13 / −\$61), and the median is negative from H = 3 on.
- **The expected-profit gate never bound:** without it, the same 1,005 trades. At the daily scale the distance to
  the channel's middle always exceeds 3× a round trip.
- **Exits:** 71.6 % of trades ended on a line break.
- **The book** (one contract a root, net booked at exit): Sharpe 0.29, Sortino 0.64, max drawdown \$29,588; the
  breakeven cost is \$112 a trade.
- **Correlation** of daily net with the components: C1 +0.008, D737 +0.078, F2 +0.013.

## 4. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | C1 holds (P 0.5) | **held**, narrowly and event-carried |
| P2 | X fails (P 0.65; the place my prior knowledge leaked) | **held on the declared paired test.** The unpaired difference (3.5 SE) would not have |
| P3 | E1 fails | **held** (t 1.07) |
| P4 | rates and equity index carry most, energy and metals least | **mixed:** equity index highest in y; **rates negative**; energy and metals positive |
| | P(GO) ≈ 0.07 | no GO |

## 5. What follows

**By the pre-registration, nothing is admitted.** The reading is SIGNAL, NOT THE LINES.

**What the record supports:**
- **Daily futures do show a reversion signal at the channel extremes in volatility units,** but it is thin
  (0.06σ a trade without the top 1 %) and event-carried.
- **It does not earn when it trades by the principal's standard:** the median is negative and only 6 of 12 years
  are positive.

**On the lines themselves, the evidence is split** and is not resolved here:
- the declared paired test fails at n 90;
- the unpaired difference favours the lines (3.5 SE).

**Resolving it** needs a new record with a powered comparison, e.g. both arms on the same entry sessions by
construction. It would be read only on data this record has not touched: the held 2024-01 → 2025-02 slice, on the
principal's word.

**Personal book, parked until real capital.** Nothing changes in BOOK.md.
