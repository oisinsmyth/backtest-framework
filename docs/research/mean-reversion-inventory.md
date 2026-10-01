# Mean reversion in this repo, D1 → D752: an inventory

*Compiled 2026-10-01/02, on the principal's word: "send out 5 sonnet agent to look for all mean reversion studies done
since inception" and "save it in the repo".*

**How it was made:**
- Five read-only Sonnet 5.5 readers each took one slice: D1–D190, D191–D380, D381–D560, D561–D752, and everything
  outside the decision records.
- Opus spot-checked three load-bearing claims: X3's literature score; D357's holdout status; D648's CL reversal leg.
- **Figures are as the records quote them.** Units vary by record (bp/trade, bp/bar, \$/trade, %/yr). **Verify
  against the cited record before reusing any number.**
- It is an inventory, not a reopening: nothing here changes a record's status.

**What "mean reversion" covers here.** Any construction or finding that bets on, or measures, a price, spread,
return, stretch or extreme reverting:
- fades and reversals (short-term, overnight, intraday, at the open);
- dip, oversold, RSI and z-score entries; gap fades;
- range, channel and level reversion; VWAP targets;
- pairs, spread and basis convergence;
- cross-sectional short-term reversal;
- variance ratios and reversion oracles.

Descriptive findings are marked **(desc.)**.

## 0. The one-paragraph answer

**About 150 studies over roughly 280 decision numbers.**
- **Reversion is almost always real in gross, and almost never survives its cost.**
- **The only family with positive net at its stated cost** is daily single-name equity reversal in slot books (rsi,
  hist_L, rev_5, retrace; D342–D357). It is in-sample, sensitive to the cost convention, and has no clean holdout
  left. It belongs to the personal book.
- **Everything intraday on the index micros is closed for the prop book** (D746, D747, D752). BOOK_PROP states the
  reason: "The reversion this universe shows at DAILY horizons does not exist at INTRADAY horizons."
- **Pressure-driven reversals are real,** at settlement windows, fixes, month-end and auctions. But the tradeable leg
  is the move *into* the window. The fades sit under the fee or have no null.

## 1. Pairs and spreads (D1–D190, D261)

| D | object | gross → net at 1× cost | null / result | status |
|---|---|---|---|---|
| D69, D76 | XLE/XOP z-score pair (60-bar z, enter \|z\| > 2, exit < 0.5) | +13.21 % → −22.70 % (v1); +21.74 % → −18.56 % (v2) | none; set a priori | "the naive famous-pair edge does not survive real costs" |
| D85–D90 | 57-ETF Gatev pairs, walk-forward (35 windows) | +3.45 % → −13.01 % | bootstrap p50 −12.68 %; DSR 0.0000 | no demonstrated edge |
| D92, D93 | cointegration-filtered selection (v2) | +19.03 % → −6.43 % (+5.70 % at 0.5×) | DSR 0.0000 | "edge exists but doesn't clear retail frictions" |
| D94 | β-hedged v3 | +6.12 % → −16.53 % | DSR 0.0000 | the 1:1 hedge wins; Kalman cut (D97) |
| D95, D96 | capacity; gross-exposure sweep | best net +0.12 %/yr (lw 0.5 @ \$300k) | Sharpe −1.61 against rf 4 % | "can pay for its implementation, not for the capital" |
| D105 | fill and calibration conventions | next-open fill −2.2 pp of gross | DSR 0.0000 | same-bar close fill "optimistic for mean reversion" |
| D122–D127 | BTC/ETH z-score pair | −88.7 % at zero cost; −98.04 % at 40 bp | DSR < 0.01 | "no edge here for costs to eat" |
| D125 (desc.) | BTC/ETH cointegration | spread stationary in 6 of 43 windows | | "the spread does not mean-revert" |
| D23, D87 (method) | synthetic zero-edge pair null | | | an OU null would be the wrong null |
| D189 (desc.) | reversal at high-volume levels, BTC/ETH | | 41st / 26th percentile against random levels | terrain programme closed |
| D261 | six index-ETF spread pairs (prop track) | −1.82 % to +3.01 %/yr | none beats its rotation null on both legs; 2020 broke every pair | spread category closed for prop |

## 2. Crypto levels, fades and structure (D191–D216)

| D | object | result | status |
|---|---|---|---|
| D196 | S5 supply/demand level bounce | Sharpe −0.78 to −0.25; 0 of 20 cells clear both hurdles | closed |
| D197–D203 | S6 fade every 40-bar breakout into inventory | 0 of 16 cells; D202 loses 11 of 11 years at zero cost | closed ("permanent stop") |
| D204–D211 | Fibonacci pullback entries, RSI control | RSI (matched) the only survivor; programme closed after 86 looks | closed |
| D215 (desc.) | generic reversion after a large 15-minute move | real, decaying; edge 0.24× / 0.32× cost | not pursued |
| D216 | the reversion tail at the maker/taker tiers | clears only at untradeable maker in/out | no follow-up |

## 3. ETFs and single-name equities, daily (D234–D433)

| D | object | result (as quoted) | status |
|---|---|---|---|
| D234–D244 | **S1 recovery rule**: back above the volatility channel; long/flat, about 15 bars | excess Sharpe +0.746 mined, +0.779 withheld; −0.123 on 2013–18; −0.291 crypto | **live in the personal book, not promoted**; era-specific |
| D238, D253 | short mirror M1; the dip premium on crypto | skill above the rotation null, money −11.90 %; the dip premium flips sign ETF → crypto | closed |
| D249, D254 | inverse wedge (long the down-break) | a market timer; holdout 7–16th percentile | closed |
| D250 | overnight gap → intraday (pre-screen) | +0.29 %/yr best; sign inverts without 2020 | closed |
| D251 | cross-sectional RS21/RS63 (reversal side) | all 16 books lose | closed |
| D258 (C2) | buy intraday declines, SPY/QQQ/IWM/DIA, 15 m | 19 of 20 cells negative | closed |
| D263 | COT contrarian | non-monotone; wrong-signed | closed (prop) |
| D267, D268 (desc.) | RSI calibration at 15 m | 0 of 27 cells | closed |
| D279–D284 | hist_L short; overnight long of fallen names | overnight long net Sharpe +0.96 / +0.71 / +0.26, but breakeven half-spread below the 15 bp floor (bid–ask bounce in cheap names) | closed |
| D285, D286 | factor-neutral hist_L long–short | net Sharpe +0.221 (N = 10); fails breakeven against a held half-spread of 33.8 bp | closed |
| D288–D293 | stage-1 screens of 31/51 scores and the confluence | +52.5 to +61.9 bp gross at 0.2× cost; 50 of 51 long books were drift | "nothing closed, nothing promoted" |
| D295–D335 | hist_L × MACD × RSI "triple" slot book (exits, width, costing) | early net +11 to +15 bp/bar overturned by D332/D333 (30 fabricated dividend days) | nothing promoted |
| D338–D341 | retrace_leg | +2.68 PUB bp/bar after the floor and open fill | not a candidate |
| **D342–D344, D346, D348, D355–D357** | **rsi and hist_L slot books, k = 40** | **PUB net +5.14 (rsi) / +12.42 (hist_L) bp/bar; 50/50 blend +8.78 (Sharpe 0.44)**; above 200/200 time and 24/24 rank rotations | **open, personal book.** D357's holdout read lost its fixture when D371 spent holdout #1 (PICKUP:2704) |
| D345 | RSI threshold event book | −5.87 bp/bar | closed |
| D347, D349–D354, D358 | rev_5, gap_reversal and cs_spread event lens; pair book; sleeve | rev_5 +43.4 bp/trade gross, PUB −18.6 / PB +17.9; K = 4 PUB +3.47 bp/bar on 322 entries; no short beats a random direction | rev_5 "closed on this construction"; 5-day reversal waits on the D336 quote pull (AITODO) |
| D359, D360 | short loser spikes; short news gap-downs | inside controls; both gap directions bounce | closed |
| D361–D364 | gap-up fade below the 200-day mean | +42.3 → +61.7 bp gross above every control; PUB −47 / −30; auction-fill bound +54.7 (impact not modelled) | open on execution |
| D373–D381, D401 | winners' dip (rev_5 dip in the momentum top decile) | +160.55 bp/trade gross; PUB −0.06 bp/bar; 73 % of gross is cohort exposure | closed by the principal (D401) |
| D384–D388 | level reversion where rare events cluster | gross to +88.1; net −54 to −148 | "no signal" |
| D391 | undercut and reclaim | wrong sign | stopped |
| D393–D396 | long a sustained down-run (up_run_21) | +22.06 gross against p95 +21.15; net −39.13 | closed (D396) |
| D398, D399 | ratcheted structural line, support-retest bounce (the channel line's construction) | results withheld here: the principal is redesigning the channel construction blind to them (2026-10-02); see the records | see the records |
| D402 (desc.) | gap → intraday, stale-open test | contaminated bars drive the correlation | measurement |
| D403 | wick-stack supply/demand map at 15 m | "the object was real, the barrier reading was not" | closed |
| D412–D433 | departure-zone touch (t + 5), its books, exits, layers, holdouts | touch +9.8 / +10.1 / +13.0 gross, durable; books failed out of sample (D430 −3.23, D433 −0.78 bp/bar) | "file as a base rate" |
| **D476–D483** | **the daily channel line** (the principal's hand-drawn lines) | results withheld here, as for D398/D399; see the records and `docs/FINDINGS.md` | **closed** (D483-CLOSE) |

## 4. Index futures (D470–D752)

| D | object | result | status |
|---|---|---|---|
| D470–D473 | K7: the overnight leg after a negative overnight leg (ES/NQ) | NQ net Sharpe +0.62 in-sample; forward z −1.30 | REMOVED |
| D490, D492 | the principal's range-reversion rule (1 m); hourly RSI variant | gross −\$3.48 ES / −\$4.96 NQ | closed |
| D495–D503 | K8: the NQ day session after a down day | +\$17.87/trade in-sample; forward −\$4.46 | gone |
| D499 | hourly fade after a large move, 8 roots | real, but worth less than a tick | closed |
| D523–D526 (desc.) | path persistence | index roots persist; the rates complex reverts (ZB) | measurement |
| D528 (+16 addenda) | the mean-reversion oracle, 35 roots, 1 m mid | real, forecastable, 4–8× below cost | open; the axis is the principal's |
| D581, D614, D618 (desc.) | gamma and close; expiry pinning | pinning reads as repulsion; not tradeable | closed |
| D622 | ES last-hour decline: does it revert overnight? | UNRESOLVED (5 COVID days) | — |
| D641–D643 | shock-classifier LIQ fades (NQ/ES/CL/GC) | the label placebo fails on all four | closed |
| D644–D660 | opening agent-state FADE; v2 gap fade to the prior close | policy +0.40 bp/session (t 0.78), 2022-carried | closed |
| D670 | YM 10:00 follow (the fade a post hoc note) | fade "disclosed and unclaimed" | closed |
| D683–D688 | ES long-gamma intraday fade | real at 5 minutes (t 5.5), \$0.22 against an \$8.84 bar | closed |
| D696–D700 | NQ busy/low-IV reversal; burst fades; channel onsets | unstable or NEITHER | closed / no closure stated |
| D715, D717 | fade absorbed first-hour moves | NEITHER | closed |
| D720, D721 (desc.) | do bigger moves revert more in high volatility? | "Nothing reverts." | closed |
| D724, D725 | NQ reversion to VWAP, the open, the midpoints; yesterday's levels | "respects no intraday mean"; levels are sticky | closed |
| D727, D728 (desc.) | YM's morning reversal | weak (11:00 β −0.047, rank 0.07) | description |
| D733 | NQ pullback entry in a trend | DRIFT ONLY | closed |
| D744, D747 | NQ/ES night-break (fade) | NOT SUPPORTED | closed |
| D746 | ES/YM stretch fade to the VWAP; gap fade | NO ROOM | closed |
| **D752** | **YM 11:00 open-reversal fade; the high-win-rate bracket** | B2 won 59.5 %, median +\$9.58, **mean −\$5.47**, skew −0.99 | closed |

## 5. Flows, settlements, spreads (D580–D751)

| D | object | result | status |
|---|---|---|---|
| D580, D582 | CME BTC funding-clock reversion | NOT SUPPORTED | closed |
| D630, D648, D709 | the settlement window's post-window reversion (NG, CL, SI) | NG +\$29 (t 3.98), CL +\$22.34 (t 3.18) on full-size contracts; no null on the reversion legs; the tradeable leg is the follow | NG frozen for the vault (the follow); the CL fade is below its \$31 cost |
| D636 | index-reweight January reversal (R2) | pre-registration only | — |
| D640 | LETF close flow | killed by its 11:00 placebo | closed |
| D653, D655–D657 | crack, roll, crush, margin hikes | the crush genuinely reverts (half-life about 8 weeks) but moves less than its cost | closed |
| D685–D687 | month-end rebalancing (ES) | gross at the 99.4th percentile; net Sharpe 0.26; faded after 2018 | MECHANISM ONLY |
| D710 | Treasury auction intraday V | gross +\$17.48 against p95 +\$3.85; net −\$1.18 | closed |
| D749, D751 | the M6E month-end fix fade; the MGC fix fade | +\$4.78 (post hoc, under the fee); −\$0.00 | NOTHING |

## 6. Outside the decision records

**Untested literature leads:**
- **X3, industry-relative short-term reversal in liquid names with a low-volatility screen:** +0.31 %/mo, t 2.73, net
  in Novy-Marx–Velikov's framework. Scored 17/21, "the strongest of the eleven"
  (`docs/research/the-negative-space-scan.md` §9b.2). D285 is its nearest tested relative.
- **Robintrack herding** (`working/DRAFT-robintrack-stage-0.md`).
- **"The gap that does not fill"** (`docs/research/the-signal-hunt-part2.md`).
- **Published effects rejected on paper** (`docs/research/shorts/`, `Prop-Firm-080926/`): end-of-day reversal,
  Berkman's open-gap reversal, ETF-NAV reversion, the overnight/intraday STR split, and a practitioner's MNQ gap-fill
  and liquidity-grab fades.

**Parked for the personal book** (AITODO; "Prop book only personal book when we have some real capital"):
- the multi-day index dip, and its volatility-spike gate;
- Treasury multi-day reversion (ZN and ZB variance ratios 0.885 / 0.922);
- the rsi/hist_L blend;
- the 5-day reversal (waiting on quotes);
- the gap-up fade's execution;
- a reversal-after-range-break book;
- gamma-gated reversion on a slower bar;
- S1 (live).

**Prop book:** no open mean-reversion item.

**Cross-cutting conclusions the repo states:**
- "The reversion this universe shows at DAILY horizons does not exist at INTRADAY horizons" (BOOK_PROP).
- "Do not propose: intraday mean reversion" (BOOK_PROP; `Prop-Firm-080926/00-SYNTHESIS.md`).
- "A reversal edge is compensation for supplying liquidity, so its gross is denominated in the spread"
  (`docs/future-strategies.md`).
- Mean reversion fails the prop floor structurally: negative skew, marked on open equity
  (`Prop-Firm-080926/14-practitioner-tier-screened.md`).
- A high win rate is bought by the bracket (D528 addendum 4; D417; D752).

**A documentation gap.** D724–D752 are recorded in AITODO and memory, but `docs/FINDINGS.md` ends at D732, and
neither BOOK_PROP nor COMPONENTS_PROP cite the later intraday closures.
