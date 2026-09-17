# D400 RESULT — D163's cost arithmetic is wrong by ~400×, and the sub-hourly closure survives anyway, on signal

**Status:** Committed
**Date:** 2026-09-08
**Category:** Validation & research integrity
**Pre-registration:** [`D400-PREREG`](D400-PREREG-the-D163-recost.md), committed before the runner existed
**Runner:** `scripts/run_d400_recost.py` · **Artifact:** `data/d400_recost_summary.json`
**Discharges:** [R11](../RULES.md#r11)'s standing corollary for the Donchian breakout ladder
**D163 is NOT edited.** Under [R8](../RULES.md#r8) a result is a separate record.

> **RENUMBERED TWICE: D389 → D390 → D400, 2026-09-09.** Pre-registered and committed as **D389** at
> 2026-09-08 23:17 (`7d04812`); a concurrent session independently used D389 for the correlation
> floor at 00:24 (`5bd7d97`). This study had the number first by commit time, but the other had
> already propagated `D389 = correlation floor` into `PICKUP.md` — **so this one moved, because that
> was the smaller correction, not because it was second.**
>
> **The move went to D390, which was already reserved, and that is the instructive half.** The
> `worktree-signal-hunt-part2` branch had reserved **D390–D399** at 2026-09-08 12:27 (`fb2af62`)
> after master took D380, D381 and D382 out from under it twice. **The reservation exists only as a
> commit message on another branch** — invisible to `ls docs/decisions/`, and invisible to `git log`
> run on master alone. This record therefore moved again, clear of the block, to **D400**. Runner and
> artifact were renamed each time; the measurements are untouched.
>
> **The hazard, stated for the next session: checking that a number is unused is not the same as
> checking that it is unclaimed.** Search `git log --all` for the number *and* for `RESERVE`, and
> list the branches to see who is live. **D390–D399 belongs to that branch; master takes D400 up.**

---

## THE HEADLINE, IN THE ORDER R15 REQUIRES

**1. GROSS FIRST.** At **15m**, Design B — the shortened-horizon rule, which is what "run it
intraday" actually means — earns a gross mean of **−1.4 bp per trade on BTC (2,628 trades)** and
**+1.9 bp on ETH (2,604 trades)** over 7.54 years, against rotation nulls centred at **+4.3** and
**+4.5** bp. BTC sits at the **2.4th percentile** of its own null; ETH at the **22.0th**. Neither
comes near p95. Trim 1% from **both** tails and both go negative: **−7.8 bp** and **−5.2 bp**. The
compounded gross book returns **−56.1%** and **−10.9%**.

> **There is no gross edge at 15m to cost.** ETH's +1.9 bp arithmetic mean is smaller than its own
> trade-level variance drag of **σ²/2 = 2.49 bp**, which is exactly why a positive mean per trade
> compounds to a loss. **Under [R15](../RULES.md#r15) this construction fails the signal criterion at
> 15m before any cost line is drawn.**

**2. THEN THE COST ARITHMETIC — and D163's number is wrong by a factor of ~400.** The closure rests
on *"pays roughly 300% of capital a year in fees at the taker tier"*. That tier is **crypto spot,
40 bp/side**. At [D258](D258-the-prop-track-candidates.md)'s futures figure of ~0.1 bp/side the same
786×/yr turnover costs **0.79%/yr**. Recomputed straight off D163's own committed registry and
summary — arithmetic, no re-run:

| | BTC 15m | ETH 15m | max cost drag anywhere on D163's ladder |
|---|---:|---:|---:|
| **D163 as written, 40 bp/side** | **314.5%/yr** | **298.3%/yr** | **4.11 Sharpe units** (B/1h, D163's own published figure) |
| **futures, 0.1 bp/side** | **0.786%/yr** | **0.746%/yr** | **0.0115 Sharpe units** (B/1h) |

*The futures column is computed off each cell's `maker_0bp` turnover and volatility, because at
0.1 bp/side the cost perturbs neither materially; D163's own column used its `taker_40bp` cells,
where 75%/yr of fees genuinely moves the position path.*

**Under the futures convention the cost curve never comes within 100× of the trend edge on any rung
of D163's ladder, either design, either symbol.** Every cell reads *"edge survives"*.

**3. SO THE EXCLUSION DOES NOT SURVIVE ON THE ARITHMETIC IT WAS WRITTEN ON.** D163's decisive
sentence — *"there is no fee tier in this study, maker or taker, at which a rule paying a
triple-digit percentage of capital per year in fees can be run"* — is true of the crypto taker tier
and **false at futures commission**, where the same rule pays 0.79%. **The exclusion survives on a
different ground than the one recorded: the signal, measured over 7.54 years and ~2,600 trades per
symbol, is not there at 15m.**

**This does not close or reopen anything.** Only the principal does that ([R15](../RULES.md#r15)).

---

## THIS IS A FEASIBILITY BOUND, NOT A FUTURES BACKTEST

**The data is BTC/ETH spot crypto.** The question answered is *"does this construction survive at
futures-level cost?"* — never *"is this a futures strategy?"* This is
[D260](D260-the-vol-targeted-overnight-hold.md)'s category: an instrument-proxy result that bounds
feasibility and licenses nothing. Crypto's 365-day calendar, its volatility and its sessionless
structure are not ES's, and **this programme holds no futures data at all**
([R11](../RULES.md#r11)'s amendment says so in terms).

---

## What was run, and why it is not D163 re-run

D163 named its own blocker and declined it: *"Exchange APIs — Binance and Kraken both serve complete
1m history free — would give the years of sub-hourly data a real walk-forward needs. … It is out of
scope here."* **That blocker was discharged by a later study and the fixture has been sitting
committed since 2026-08-22.**

| | D163 | **D400** |
|---|---|---|
| fixture | `crypto_intraday_1h/30m/15m_raw` (yfinance) | **`crypto_binance_15m_raw`** (Binance 1m archives → 15m, D161) |
| sub-hourly span | **60 days**, turnover only, **no return claim possible** | **3,066 complete UTC days**, 294,336 bars/symbol |
| scored span | 441 OOS days (1h ladder) | **2018-12-29 → 2026-07-31, 2,751 days, 7.54 years**, identical at every rung |
| ladder | 1h–1d walk-forward; 15m/30m turnover-only | **15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d — returns at every rung** |
| sizing | inverse-vol, 40% target, capped 1.0 | **unit weight (declared deviation, pre-registered)** |

Everything else is D163/D109 unchanged: `close(t) > max(high)` over `t−N…t−1` to enter,
`close(t) < min(low)` to exit, long or flat, `next_open` fill (D103), Design A = 40 **days**/10 days,
Design B = 40 **bars**/10 bars, `TRAIN+TEST = 315` days dropped from the front at every rung so
frequency is the only variable. **Nothing is fitted; 0 parameters tuned, 0 filters added, 0
configurations selected on performance.**

**Levels here are NOT comparable to levels in `docs/results/breakout_intraday.md`** — different
fixture, different era, different sizing. Only the *ladder* is comparable, and only within itself.

### The apparatus validates against D163 where they overlap

Under D163's own convention (crypto 40 bp/side), reading (1) net Sharpe ≤ 0 and reading (2)
costs ≥ 100% of gross both fire at **2h for Design B on both symbols independently** — which is
D163's headline verdict, reproduced on an independent 8.4-year fixture with different sizing.
The spliced reading (3) fires one rung finer here, at 1h. That agreement is what licenses the rest.

---

## THE RE-COST OF D163 ITSELF — arithmetic on committed artifacts, no re-run

Before any new fixture: D163's `data/breakout_intraday_summary.json` and
`data/breakout_intraday_registry.sqlite` already hold every turnover and volatility the re-cost
needs. `fee_drag_annual = annual turnover × rate per side` is the identity D163's own integration
suite checks, so both columns below are that one line evaluated twice.

**The 15m/30m turnover measurement rows — the section the closure is written on.** These carry a
`gross_pnl` field D163 never printed, and it is worth reading:

| symbol | rung | closed trades | turnover/yr | **fees @ 40 bp/side** | **fees @ 0.1 bp/side** | gross P&L, 59 days |
|---|---|---:|---:|---:|---:|---:|
| BTC-USD | `15m` | 65 | 786.3× | **314.5%** | **0.786%** | −4.56% |
| BTC-USD | `30m` | 29 | 352.9× | 141.1% | 0.353% | −4.28% |
| BTC-USD | `1h` | 15 | 182.7× | 73.1% | 0.183% | −0.94% |
| ETH-USD | `15m` | 65 | 745.9× | **298.3%** | **0.746%** | −4.66% |
| ETH-USD | `30m` | 27 | 325.6× | 130.2% | 0.326% | +8.11% |
| ETH-USD | `1h` | 15 | 182.0× | 72.8% | 0.182% | −0.68% |

**The walk-forward ladder, re-costed.** Cost drag in Sharpe units at each convention, against D163's
imported reference edge (BTC 1.27 / ETH 0.84):

| symbol | design | | `1d` | `12h` | `6h` | `4h` | `2h` | `1h` |
|---|---|---|---:|---:|---:|---:|---:|---:|
| BTC | B | **drag @ 40 bp** | 0.21 | 0.38 | 0.82 | 0.96 | **1.93** | **4.59** |
| BTC | B | **drag @ 0.1 bp** | 0.0005 | 0.0010 | 0.0021 | 0.0024 | 0.0048 | **0.0115** |
| ETH | B | **drag @ 40 bp** | 0.13 | 0.18 | 0.34 | 0.45 | **1.01** | **2.10** |
| ETH | B | **drag @ 0.1 bp** | 0.0003 | 0.0005 | 0.0009 | 0.0011 | 0.0025 | **0.0052** |
| BTC | A | **drag @ 40 bp** | 0.21 | 0.22 | 0.27 | 0.27 | 0.26 | 0.26 |
| BTC | A | **drag @ 0.1 bp** | 0.0005 | 0.0005 | 0.0007 | 0.0007 | 0.0006 | 0.0006 |
| ETH | A | **drag @ 40 bp** | 0.13 | 0.15 | 0.16 | 0.17 | 0.18 | 0.19 |
| ETH | A | **drag @ 0.1 bp** | 0.0003 | 0.0004 | 0.0004 | 0.0004 | 0.0005 | 0.0005 |

**Bold = "costs win" under D165's reading (3).** At 40 bp/side, four cells win — the same
Design-B 2h/1h band D163 reported. **At 0.1 bp/side, none do, and none is close: the largest drag on
the whole ladder is 0.0115 against an edge of 1.27.** *(These are recomputed from the `maker_0bp`
cells; D163's published table used its `taker_40bp` cells, which is why its BTC B 1h figure reads
4.11 where this one reads 4.59. Both are correct on their own basis and neither changes any verdict.)*

**That is the entire cost half of the re-cost, and it took no new data.** What needed new data is the
next section: whether there is any gross edge down there to protect.

---

## GROUP 1 — performance, GROSS AND NET SIDE BY SIDE, at both conventions

*Gross first. `bp/side` breakeven = gross mean per trade ÷ 2. `drag` = annual fee drag ÷ annual vol
(D165's conversion). Sharpe is on **daily NAV** at every rung, so rungs are comparable (D164's units
argument); annual vol likewise.*

### BTCUSDT — Design B (constant 40-bar / 10-bar horizon) — the design the closure is about

| rung | entry | trades | **gross mean/trade** | **breakeven bp/side** | gross tot ret | gross Sh | vol | maxDD | expo | turn/yr | **fee@40bp** | net@40bp | net Sh | **fee@0.1bp** | **net@0.1bp** | **net Sh** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `15m` | 0.42 d | 2,628 | **−1.4 bp** | **−0.70** | −56.1% | −0.26 | 34.4% | 77.6% | 25.9% | 697.4× | 278.9% | **−100.0%** | −7.63 | **0.697%** | **−58.3%** | **−0.28** |
| `30m` | 0.83 d | 1,301 | +8.3 bp | +4.17 | +89.9% | +0.30 | 34.6% | 64.7% | 27.7% | 345.2× | 138.1% | **−100.0%** | −3.46 | 0.345% | **+85.0%** | **+0.29** |
| `1h` | 1.67 d | 639 | +26.8 bp | +13.42 | +266.7% | +0.56 | 33.4% | 44.0% | 28.2% | 169.6× | 67.8% | −97.8% | −1.39 | 0.170% | **+262.1%** | **+0.55** |
| `2h` | 3.33 d | 313 | +74.9 bp | +37.45 | +545.8% | +0.78 | 34.0% | 45.4% | 30.3% | 83.1× | 33.2% | −47.5% | −0.18 | 0.083% | **+541.7%** | **+0.78** |
| `4h` | 6.67 d | 151 | +246.6 bp | +123.32 | +1715.0% | +1.19 | 33.7% | 28.5% | 31.3% | 40.1× | 16.0% | +441.0% | +0.71 | 0.040% | +1709.5% | +1.19 |
| `6h` | 10.0 d | 107 | +344.4 bp | +172.20 | +1839.6% | +1.21 | 33.8% | 34.0% | 32.0% | 28.4× | 11.4% | +722.6% | +0.87 | 0.028% | +1835.4% | +1.21 |
| `12h` | 20.0 d | 56 | +560.0 bp | +279.98 | +878.8% | +0.92 | 35.3% | 49.8% | 32.1% | 14.9× | 5.9% | +524.8% | +0.75 | 0.015% | +877.7% | +0.92 |
| `1d` | 40.0 d | 27 | +1854.6 bp | +927.30 | +1176.8% | +0.96 | 38.5% | 50.3% | 39.2% | 7.2× | 2.9% | +928.3% | +0.89 | 0.007% | +1176.1% | +0.96 |

### ETHUSDT — Design B

| rung | trades | **gross mean/trade** | **breakeven bp/side** | gross tot ret | gross Sh | vol | maxDD | expo | turn/yr | **fee@40bp** | net@40bp | net Sh | **fee@0.1bp** | **net@0.1bp** | **net Sh** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `15m` | 2,604 | **+1.9 bp** | **+0.97** | −10.9% | +0.09 | 41.2% | 49.4% | 26.0% | 691.0× | 276.4% | **−100.0%** | −6.20 | **0.691%** | **−15.4%** | **+0.07** |
| `30m` | 1,280 | +17.6 bp | +8.82 | +416.8% | +0.65 | 42.6% | 63.1% | 26.9% | 339.7× | 135.9% | **−100.0%** | −2.42 | 0.340% | **+403.7%** | **+0.64** |
| `1h` | 639 | +51.1 bp | +25.53 | +1236.0% | +0.94 | 42.9% | 38.5% | 28.4% | 169.6× | 67.8% | −92.0% | −0.60 | 0.170% | **+1219.0%** | **+0.94** |
| `2h` | 326 | +70.5 bp | +35.24 | +340.6% | +0.59 | 44.5% | 56.8% | 30.0% | 86.5× | 34.6% | −67.7% | −0.18 | 0.087% | **+337.7%** | **+0.59** |
| `4h` | 157 | +235.6 bp | +117.81 | +1408.3% | +0.95 | 43.6% | 40.5% | 30.2% | 41.7× | 16.7% | +328.5% | +0.56 | 0.042% | +1403.5% | +0.95 |
| `6h` | 109 | +354.4 bp | +177.22 | +1721.9% | +0.99 | 44.8% | 39.3% | 30.6% | 28.9× | 11.6% | +660.4% | +0.73 | 0.029% | +1717.9% | +0.99 |
| `12h` | 51 | +720.6 bp | +360.30 | +1523.9% | +0.93 | 48.0% | 42.0% | 33.1% | 13.7× | 5.5% | +974.7% | +0.82 | 0.014% | +1522.2% | +0.93 |
| `1d` | 29 | +1485.4 bp | +742.69 | +844.4% | +0.78 | 47.9% | 45.2% | 34.3% | 7.8× | 3.1% | +645.5% | +0.71 | 0.008% | +843.8% | +0.78 |

**Design A (constant 40-day/10-day calendar horizon) is frequency-invariant, and cost never binds
under either convention.** 27–37 trades, 7.2–9.8× turnover and 32–39% exposure at *every* rung on
both symbols; fee drag runs **2.87–3.93%/yr at 40 bp/side** and **0.007–0.010%/yr at 0.1 bp/side**;
cost drag peaks at **0.11 Sharpe units** (40 bp) and **0.0003** (0.1 bp) against reference edges of
1.27/0.84. **Design A's exclusion never rested on cost in the first place** — D163 said so and this
fixture agrees. Its problem is elsewhere (groups 3 and 4 below).

### The spread of the instrument HELD, measured off its own OHLC — and why the estimate cannot be trusted

CLAUDE.md requires estimating the held names' spread rather than trusting a fee assumption.
Corwin-Schultz, run on the scored span at every rung:

| rung | `15m` | `30m` | `1h` | `2h` | `4h` | `6h` | `12h` | `1d` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **BTCUSDT** bp/side | **2.55** | 4.04 | 6.14 | 8.99 | 13.35 | 16.31 | 22.88 | 33.72 |
| **ETHUSDT** bp/side | **3.33** | 5.21 | 7.91 | 11.68 | 16.95 | 21.29 | 30.91 | 46.33 |

**A true spread cannot depend on the bar size, and this one scales as ~√duration** (13.2× across a
96× duration ratio; √96 = 9.8). **So Corwin-Schultz here is measuring volatility, not spread**, and
every reading is an upper bound that degrades as the bar coarsens. The tightest and least
contaminated reading — **2.55 / 3.33 bp/side at 15m** — is what the data itself will support.

**Two things follow, and they point opposite ways.** D163's 40 bp/side is a **fee schedule for a
retail spot venue**, not a measured spread, and it is **~16× the tightest (least contaminated)
half-spread these instruments' own bars support** — 2.55 bp/side at 15m. And separately, this is
exactly why quoting the daily-bar reading (33.7 / 46.3 bp/side) as "the cost" would be a mistake in
the other direction: on a 35–48%-vol instrument Corwin-Schultz is not a spread estimator at all.

---

## GROUP 2 — trade distribution, with the 1% two-tail trim and all three means

### The 15m rung, both symbols, Design B — where the closure lives

| | BTCUSDT | ETHUSDT |
|---|---:|---:|
| trades | 2,628 | 2,604 |
| **mean** | **−1.4 bp** | **+1.9 bp** |
| **median** | **−34.1 bp** | **−41.6 bp** |
| win rate | 33.5% | 36.0% |
| payoff | 1.93 | 1.83 |
| median / mean hold | 0.21 d / 0.21 d | 0.22 d / 0.22 d |
| skew / kurtosis | +3.40 / 31.1 | +3.10 / 26.0 |
| sd per trade | 189.9 bp | 223.1 bp |
| **σ²/2 (variance drag)** | **1.80 bp** | **2.49 bp** |
| **mean ex-top 1% (26 trades)** | **−12.3 bp** | **−10.5 bp** |
| **mean ex-bottom 1%** | **+3.1 bp** | **+7.4 bp** |
| **mean, symmetrically trimmed** | **−7.8 bp** | **−5.2 bp** |

**The mean sits ABOVE the median at every Design B rung**, which is the trend-follower shape and the
opposite of D285's tell — the **right** tail is doing the work, not a hidden left tail. That is not a
defence here: **the symmetric trim is negative on both symbols**, and the winning tail is larger than
the losing one (ex-bottom +3.1/+7.4 against ex-top −12.3/−10.5). **Stripping 1% from each end of a
2,600-trade book leaves a loss.** The whole of the 15m arithmetic mean is 26 extreme trades per
symbol.

### Design B up the ladder — the shape is the evidence

Per [R14](../RULES.md#r14)'s 2026-09-08 addition, the sweep's shape is read as evidence rather than
one cell:

| rung | `15m` | `30m` | `1h` | `2h` | `4h` | `6h` | `12h` | `1d` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **BTC mean bp/trade** | −1.4 | +8.3 | +26.8 | +74.9 | +246.6 | +344.4 | +560.0 | +1854.6 |
| **BTC symmetric trim** | **−7.8** | **−0.9** | +15.5 | +57.1 | +174.4 | +289.5 | +439.0 | +711.0 |
| **ETH mean bp/trade** | +1.9 | +17.6 | +51.1 | +70.5 | +235.6 | +354.4 | +720.6 | +1485.4 |
| **ETH symmetric trim** | **−5.2** | +7.5 | +33.3 | +40.8 | +182.4 | +321.6 | +652.3 | +536.9 |

**Monotone in bar size on both symbols, and it crosses zero between 15m and 30m on the trimmed
statistic.** A monotone shape says the effect is mechanical — the rule is being sampled into noise as
the horizon shortens — rather than a badly chosen threshold. **Per-bar edge density does not rise as
the bar shrinks; it collapses.** Trades rise **97.3×** from 1d to 15m (27 → 2,628 on BTC) while the
mean per trade falls from **+1854.6 bp to −1.4 bp** on BTC and from **+1485.4 bp to +1.9 bp** on ETH
— a fall far steeper than the rise in trade count, which is the whole reason more trading buys less
money here.

---

## GROUP 3 — what the winners depend on

**Concentration is extreme for Design A and moderate for fast Design B.**

| cell | trades to half the P&L | top-1 share | top-5 | top-10 | profitable years | **top trade, dated** |
|---|---:|---:|---:|---:|---:|---|
| BTC A `1d` | **1** | **68.9%** | 105.1% | 118.9% | 4/8 | +34,508 bp, entered **2020-10-20** |
| BTC A `15m` | 3 | 26.3% | 89.4% | 125.4% | 5/8 | +7,398 bp, entered **2019-04-02** |
| ETH A `1d` | **1** | **71.1%** | 105.2% | 126.7% | 5/8 | +30,614 bp, entered **2020-10-23** |
| ETH A `15m` | **1** | **60.7%** | 95.4% | 118.4% | 5/8 | +31,695 bp, entered **2020-10-21** |
| BTC B `1h` | 5 | 12.8% | 59.8% | 106.3% | 4/8 | +2,197 bp, entered **2020-12-12** |
| BTC B `15m` | n/a (P&L < 0) | — | — | — | 4/9 | +2,701 bp, entered **2019-10-25** |
| ETH B `15m` | 1 | 51.1% | 205.4% | 337.0% | 4/9 | +2,588 bp, entered **2025-05-08** |

**Design A is one trade.** On both symbols, at nearly every rung, a single position opened in the
third week of October 2020 supplies 60–71% of the entire 7.5-year P&L. That is not a frequency
result; it is the 2020–21 bull run being caught once. Its top-5 share exceeding 100% means the other
~30 trades are net negative.

**Era decay is severe and universal.** Mean bp/trade, pre-2022 against 2022-onward:

| cell | pre-2022 | 2022+ | ratio |
|---|---:|---:|---:|
| BTC A `15m` | +1,175.6 | +441.3 | 2.7× |
| BTC A `1d` | +4,501.3 | +297.7 | **15.1×** |
| BTC B `1h` | +62.1 | +4.6 | **13.5×** |
| BTC B `15m` | +0.0 | **−2.2** | — |
| ETH A `15m` | +3,263.9 | +327.4 | **10.0×** |
| ETH B `1h` | +95.5 | +21.3 | 4.5× |
| ETH B `15m` | +4.5 | +0.3 | **15.0×** |

**Every cell is 2.7–15× weaker in the second era, and the fast Design B cells are ~zero or negative
in it.** Profitable years run 4–7 of 8–9 everywhere. The **price** cut CLAUDE.md asks for does not
apply — a two-instrument fixture has no cross-sectional price axis — and the **dead-vs-alive** cut
does not apply either: neither instrument died.

---

## GROUP 4 — the nulls, as a DISTRIBUTION

**The control.** A **circular rotation of the position vector** against the price series, 500 draws,
seeded per cell with a stable CRC (never Python's salted `hash`). Rotation preserves exposure, trade
count, the holding-run distribution and turnover **exactly**, and destroys only the alignment between
the rule's timing and the market — matched on the nuisance, not merely on the count.

**It is a hard control here, and that is the point.** Both instruments rose enormously over the
scored span, so a rotated long-or-flat book at 26–39% exposure earns a great deal by construction —
the null's median per-trade P&L runs **+360 to +665 bp** for Design A. Anything that does not clearly
beat that is buying beta on a schedule.

| cell | observed mean/trade | **null p50** | **null p95** | percentile | clears p95? |
|---|---:|---:|---:|---:|:--:|
| **BTC B `15m`** | **−1.4** | **+4.3** | **+8.8** | **2.4** | **NO** |
| **ETH B `15m`** | **+1.9** | **+4.5** | **+10.9** | **22.0** | **NO** |
| BTC B `30m` | +8.3 | +8.4 | +18.8 | 49.6 | NO |
| ETH B `30m` | +17.6 | +10.4 | +22.3 | 84.6 | NO |
| BTC B `1h` | +26.8 | +17.6 | +36.9 | 79.8 | NO |
| ETH B `1h` | +51.1 | +22.1 | +48.1 | 96.4 | yes |
| BTC B `2h` | +74.9 | +42.1 | +83.0 | 91.4 | NO |
| ETH B `2h` | +70.5 | +48.1 | +96.1 | 78.0 | NO |
| BTC B `4h` | +246.6 | +84.2 | +169.8 | **99.6** | yes |
| ETH B `4h` | +235.6 | +98.8 | +217.4 | **97.6** | yes |
| BTC B `6h` | +344.4 | +127.1 | +263.6 | **99.0** | yes |
| ETH B `6h` | +354.4 | +144.4 | +283.0 | **98.0** | yes |
| BTC B `1d` | +1854.6 | +639.1 | +1574.6 | 96.6 | yes |
| ETH B `1d` | +1485.4 | +621.7 | +1502.7 | 94.6 | NO |

**The null is decisive at 15m and it is decisive in the wrong direction for BTC.** BTC's observed
−1.4 bp sits *below* the null's own 5th percentile (−0.5 bp): a rotation of the same book, keeping
every structural property except when it trades, **beats the rule 97.6% of the time**. The same
result holds on total return (2.2nd percentile, null p50 +120.5% against an observed −56.1%).

**Design A never clears convincingly.** BTC A clears p95 at exactly one of eight rungs (`1d`, 96.8);
ETH A clears at six of eight but with a pattern that scrambles across rungs (99.4, 98.0, 95.6, 96.2,
96.2, 92.8, 93.6, 95.2) on **27–37 trades** — a sample too small, and too dominated by one October
2020 position, to read as anything but suggestive.

**The signal crossover, which is a different quantity from the cost crossover.** Reading Design B
slow→fast, the coarsest rung at which the rule stops clearing its own rotation null is **2h on BTC**
(4h clears at 99.6, 2h fails at 91.4) and **2h on ETH** (1h clears at 96.4, 2h fails at 78.0, 30m at
84.6, 15m at 22.0). **Below roughly 1h–2h the rule is statistically indistinguishable from a rotated
copy of itself, at any cost.**

---

## THE CROSSOVER, RE-READ UNDER BOTH CONVENTIONS

Coarsest rung at which each reading fires, read slow→fast (D165's rule, unchanged):

| symbol | design | convention | (3) drag ≥ ref edge | (3b) drag ≥ own gross Sharpe | (2) cost ≥ 100% gross | (1) net Sharpe ≤ 0 |
|---|---|---|---|---|---|---|
| BTC | A | crypto 40 bp | `no rung` | `no rung` | `no rung` | `no rung` |
| BTC | A | **futures 0.1 bp** | `no rung` | `no rung` | `no rung` | `no rung` |
| BTC | B | crypto 40 bp | **`1h`** | **`2h`** | **`2h`** | **`2h`** |
| BTC | B | **futures 0.1 bp** | **`no rung`** | **`no rung`** | **`no rung`** | `15m` † |
| ETH | A | crypto 40 bp | `no rung` | `no rung` | `no rung` | `no rung` |
| ETH | A | **futures 0.1 bp** | `no rung` | `no rung` | `no rung` | `no rung` |
| ETH | B | crypto 40 bp | **`1h`** | **`2h`** | **`2h`** | **`2h`** |
| ETH | B | **futures 0.1 bp** | **`no rung`** | **`no rung`** | **`no rung`** | **`no rung`** |

† **`15m` here is not a cost crossover.** BTC's Design B book at 15m has a **gross** Sharpe of −0.26;
0.697%/yr of fees turns −0.26 into −0.28. D165's own caveat applies verbatim: reading (1) cannot
separate *"costs killed the edge"* from *"there was no edge to kill"*, and here it is unambiguously
the second.

**Maximum cost drag anywhere on the whole ladder, both designs, both symbols:**

| convention | this fixture | D163's own committed cells |
|---|---:|---:|
| crypto 40 bp/side | **8.11 Sharpe units** (BTC B 15m) | **4.59** (BTC B 1h) |
| **futures 0.1 bp/side** | **0.020 Sharpe units** | **0.0115** |
| reference gross edge | 1.27 (BTC) / 0.84 (ETH) | same |

**At futures commission the cost curve never rises above 1/60th of the reference edge anywhere on
the ladder, and on D163's own cells never above 1/110th. There is no cost–frequency frontier left to
find on this rule.**

---

## RUNNER ASSERTIONS — all three, and each PROVED able to fail

| | what it checks | how it was broken, and it raised |
|---|---|---|
| **1a lag audit** | the position vector re-derived by a **monotonic-deque rolling extremum + explicit state machine**, sharing no code path with the pandas rolling implementation, must be **bit-identical** | flipped one bar of the second implementation → *"the two implementations first disagree at bar 45 (0 vs 1)"* |
| **1b look-ahead** | perturb **every** bar strictly after `t` by a random 5–50% and require `pos[:t+2]` unchanged — `pos[k]` is worked at `open[k]` off `close[k−1]` | removed the `next_open` shift → *"perturbing bars after 1500 changed the position at or before 1501"* |
| **2 sign, in money** | a long book on a monotonically rising synthetic must **earn**, on its mirror must **lose**, and 40 bp/side must cost strictly more than 0.1 bp/side | reversed the price series inside the scorer → *"long book on a rising series returned −69.8715%, expected positive"* |
| **3 right-quantity** | Designs A and B must be **identical at 1d** (40 bars = 40 days there) and **different at every other rung** | fed a grid where A and B disagree at 1d → raised |

Assertions 1a and 1b were run on the live fixture at the `15m` and `1d` rungs of both designs on both
symbols; assertion 3 across the whole 32-cell grid; assertion 2 on synthetics. `--selftest` runs the
four break-tests alone.

---

## Limitations, stated rather than buried

1. **Crypto spot, not futures.** A feasibility bound. See the box above.
2. **Sizing deviates from D163** — unit weight rather than inverse-vol at a 40% target capped at 1.0.
   Turnover therefore differs (697× vs D163's 786× at BTC 15m, ~11% lower, mostly window and
   sizing). Declared in the pre-registration before the run.
3. **Two instruments, and their daily log returns correlate at 0.83 over the scored span** (measured,
   not assumed). "Both symbols say so independently" is much weaker on BTC and ETH than the phrase
   suggests; [R10](../RULES.md#r10)'s concurrency argument applies. Nothing here is a
   cross-sectional result, and the effective sample is closer to one instrument than two.
4. **Design A rests on 27–37 trades**, one of which is 60–71% of the P&L. No verdict on Design A
   should be read off this sample.
5. **One era does most of the work.** Every cell is 2.7–15× weaker after 2021; the fast cells are
   flat-to-negative there. A rule whose edge halves each era is not obviously a rule.
6. **Nothing about hurdle P was computed.** No P1 sizing, no P3/P4/P5 — all three of which
   [D375](D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is.md) §5
   records as never having been computed on anything.
7. **Fees only, plus a measured-but-unreliable spread estimate.** No slippage, no impact, no funding,
   no borrow. The 0.1 bp/side figure is a **commission**, and a real 15m book paying 697 sides a year
   would pay a spread on each of them.
8. **`--selftest` proves the audits bite; it does not prove the scorer is D163's engine.** The
   apparatus was validated against D163's 2h Design-B crossover, not reconciled bar-for-bar.

## Multiplicity

32 cells (8 frequencies × 2 designs × 2 symbols), each read at two cost conventions — a cost overlay
on one book, not a second search. **0 parameters tuned, 0 filters added, 0 configurations selected on
performance.** Under [R13](../RULES.md#r13) this inherits D160–D165's looks (same rule, same
hypothesis, candidate list chosen because of that work) and inherits nothing from the ETF or terrain
programmes. **No holdout was read** ([R14](../RULES.md#r14)'s amendment: the ledger counts holdout
reads).

## Cost of the run

**29 seconds. Peak working set 0.19 GB**, against a 1.5 GB budget, on the full 8.4-year 15m base with
500 nulls per cell. One rung is resampled, scored and released before the next is built.

---

## WHAT THIS MEANS FOR D163'S EXCLUSION

**The exclusion survives. The reason recorded for it does not.**

1. **D163's cost number is wrong by ~400× for anything but crypto spot.** *"Roughly 300% of capital a
   year in fees"* is **0.79%** at 0.1 bp/side, and *"no fee tier at which this can be run"* is false
   at futures commission. Under [R11](../RULES.md#r11) that sentence cannot stand as the ground of an
   exclusion, and this record retires it as such.
2. **Under the futures convention there is no cost–frequency crossover anywhere on the ladder** —
   maximum drag 0.020 Sharpe units against a 0.84–1.27 edge. The cost half of the frontier ceases to
   be the binding constraint at any bar size down to 15m.
3. **And it does not matter, because the gross edge is absent exactly where the closure applies.** At
   15m, on 7.54 years and ~2,600 trades per symbol, the rule earns −1.4 / +1.9 bp per trade against
   nulls centred at +4.3 / +4.5, sits at the 2.4th and 22.0th percentiles of its own rotation, and
   goes negative on both symbols under a symmetric 1% trim. **Under [R15](../RULES.md#r15) that is a
   failure at the signal criterion, and cost is not consulted.**
4. **The cost re-work does change three specific things**, and they are worth recording because they
   are the difference between "excluded on arithmetic" and "excluded on evidence":
   - **ETH Design B at 15m flips from ruinous to marginal**: −100.0% at 40 bp/side, **−15.4% at
     0.1 bp/side** on a gross of −10.9%. Its breakeven of **+0.97 bp/side** genuinely clears a
     0.1 bp/side commission ~10×. It still fails the null at the 22nd percentile, so it is not a
     signal — but it is no longer *arithmetically impossible*, which is what D163 claimed.
   - **The whole 30m–2h band flips sign**: BTC B 1h goes −97.8% → **+262.1%**, ETH B 1h −92.0% →
     **+1219.0%**. **Three rungs per symbol — 30m, 1h and 2h — move from decisively net-negative to
     strongly net-positive on cost alone**, and 15m stays negative on both because its gross is.
   - **Design A was never a cost story at all** and the re-cost confirms it: 0.007–0.010%/yr.
5. **The frontier's binding constraint moves from cost to signal, and it moves one rung.** Under
   crypto fees the cost curve crossed the edge at **2h**. Under futures commission the cost curve
   crosses nothing, and what fails instead is the null: the rule stops beating a rotation of itself
   at **2h on BTC and 2h on ETH**. **The same bar, for a completely different reason** — which is the
   most useful single sentence in this record, because it means D163's headline was numerically right
   and mechanistically wrong.

**This record closes nothing and reopens nothing.** It reports that R11's corollary has been
discharged for this construction, that the arithmetic ground of D163's sub-hourly exclusion is
retired, and that the exclusion stands on the signal instead. **What to do with the 30m–2h band —
where the cost re-cost moves four rungs per symbol from ruin to profit and the nulls are mixed
(ETH B 1h clears at 96.4; BTC B 1h fails at 79.8; both fail at 2h) — is the principal's call, not
this record's.**
