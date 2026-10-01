# AI TODO

> **The live task list, kept current from 2026-09-24 on the principal's instruction.** Update it
> at the end of every working session; an entry that is done or dropped is removed, not left to go
> stale. The build-phase list this file held until 2026-09-01 is in git history at `f78786e`
> (`git show f78786e:docs/internal/AITODO.md`).

## Decision numbers across branches (2026-09-29)

- Main holds D676–D682 from `wt/after-d643`, which merged first.
- **`wt/after-d674` merged second (2026-09-29) and RENUMBERED its clashing records:**
  - month-end: D677 → **D685**, D678 → **D686**, D680 → **D687**;
  - the dealer-gamma close: D681 → **D688**.
  D683 (gamma DIAG) and D684 (the long-gamma fade sizing) kept their numbers. Each renumbered record carries a head
  note; commit messages and recorded outputs in `data/` keep the old numbers.
- **Next free number: 749.**
  - **D748 (2026-10-01): PRE-REGISTERED, Stage 0.** The activity keeper: one placeholder trade at 13:30–14:00 ET on
    the cash-settled financial micro with the smallest forecast σ\$ (the principal's "vol\*tick size, smallest root";
    "Financial micros only"). It fires only when a firm's inactivity window would otherwise lapse.
    - **The standard:** it may break even, and it must never threaten the account.
    - **Readings:** K1 worst trade ≥ −\$50; K2 worst 30 days ≥ −\$150; K3 ≤ \$300 a year; K4 zero breaches.
    - **Next:** the runner, `scripts/stage0_d748_activity_keeper.py`, runs on the system interpreter (`fut_day5m`
      needs pyarrow).
  - **D747 (2026-10-01): NOT SUPPORTED, and NO ROOM on ES** (the principal: "Close D746 and pre-reg C as D747"). The
    night-break fade (resting limits at yesterday's range ± 0.25 ATR20, 03:00–08:29, 1:1 bracket, flat 09:29),
    decided on data D744 never scored.
    - **ES 2016–2023, b 0.25:** +$1.45 gross (t 0.56), inside its timing null (p 0.30); net −$3.67; 2 of 8 years.
    - **NQ 2016-01 → 2018-01-08:** −$0.50 gross, 0 of 3 years.
    - **On D744's read slice (NQ 2018–2023, post hoc):** +$9.09 gross, but 2022 alone exceeds the whole book's total.
    - The reversal belonged to the slice, not the market. With D746, the prop book has no intraday mean-reversion line
      on the index micros. Closing it is the principal's call.
  - **D746 (2026-10-01): NO ROOM on all four primary cells; CLOSED by the principal** ("Close D746 and pre-reg C as
    D747"). The prop-book mean-reversion oracle on ES and YM at one micro, in-sample 2016–2023.
    - **A, the stretch fade** (|z| ≥ 2.5 from the open, faded to the VWAP with a 1:1 bracket): gross −$5.76 (ES) and
      −$1.56 (YM) a trade.
    - **B, the gap fade** (to yesterday's close): gross −$5.27 (ES) and −$0.55 (YM).
    - Every cell sits at its timing null's median (Holm 1.00), and gross is at or below zero in 11 of 12 cells.
    - **The size is there (the median target is 4–10× the fee); the direction is not.** Stretches carry on to the
      stop more often than they return, and gaps extend as often as they fill.
    - A filter would need ρ 0.075–0.20 to break even; at the realistic 0.05, every kept half loses.
    - The dealer-gamma split runs the wrong way: the fade does best on short-gamma days (n ≈ 60, not significant).
    - Post hoc and not significant: holding YM's fades to the close grosses +$4–8 (t ≤ 1.6), D727's weak YM reversal.
    - Closing it is the principal's call. The remaining prop reversion candidate is C, NQ's night-break fade, on the
      principal's word.
  - **D743 (2026-10-01): NOT SUPPORTED, all six; CLOSED by the principal** ("Ok close that and look at idea 2").
    It tested skipping busy two-way nights and CPI / jobs days on D735's legs (YM k1.0 = D737's twin, EQ k1.5); idea 1
    of the C1 mechanism comparison.
    - The skips do not select; on EQ the skipped trades earn more (\$29–42 against \$11–16).
    - D737 is unchanged.
    - Next: idea 2, the consolidation break at the European open, is D744.
  - **D744 (2026-10-01): NOT SUPPORTED; CLOSED by the principal** ("Close D743 and D744 Only"). It tested NQ's fresh break of yesterday's range between 03:00 and 08:29 ET,
    gated by C1's tier rebuilt for 03:00, flat at 09:29.
    - **The gated book:** 96 trades, gross −0.30 bp (t −0.09).
    - **The ungated night break reverses:** −4.48 bp, t −2.08. This is an observation; a fade is not pursued without
      the principal's word.
    - **C1's edge is a cash-session effect.**
    - **Only D743 and D744 are closed;** the C1 comparison line stays open (idea 3, FOMC 14:00, underpowered; anything
      further on the principal's word).
  - **D745 (2026-10-01): WITHDRAWN before its freeze by the principal** ("Withdraw D745"). It was the abstention
    principle (shock recency) on the joint vault.
    - **The rehearsal is NOT CONFIRMED in-sample:** C1 is best with NONE, F2 with FRESH.
    - **No candidate state sorts both continuation books** (`data/d745_candidate_states.json`). Compression sorts C1
      only (p 0.022, its own gate's quantity); F2 has p 0.38.
    - **The vault is not spent,** and there is no JOINT_RUN_CHECKLIST step.
    - **Any new principle needs a new record,** whose declared statistic reproduces its in-sample pattern first.
  - **D736, D738, D740, D741, D742: the NQ follow's selectivity line (2026-10-01), CLOSED.**
    - **The records:**
      - D736 is the earn-when-trading screen;
      - D738 tests expected-profit filters on D727's follow (NOT SUPPORTED);
      - D740 keeps a fixed volatility floor σ\$ ≥ \$150, in-sample and post hoc; the 20-day SMA agreement adds nothing;
      - D741's MACD agreement for drawdown is NOT SUPPORTED;
      - D742 keeps the 1.0 σ_rem stop as a worst-day risk rule, not a drawdown fix.
    - **Closed by the principal** ("close the follow plus stop and leave D737 as is"): the line is 94 % D737's days and
      still a follow. D737 stays frozen.
    - **Monitor, not a test:** split D737's forward trades (`data/forward/d737_forward.csv`) by floor on and off at the
      open. Post hoc in-sample, D737 nets +\$2.66 a trade below the floor and 92 % of its total above it (D742,
      addendum 2). The ledger's `sigma_oc_usd` column (NQ's prior-20-session σ_oc × \$2, known at the open) carries the
      split. It is readable once forward trades accumulate, from about 2026-11-09.
  - **D739 is this session's transfer test of D735's mechanism** (the principal: "Lets do 3. D735's mechanism on other
    roots"). The rule is D737's, unchanged, on 25 roots (metals, energy, rates, FX, grains; PA dropped by A1's coverage
    gate).
  - **No root reads MECHANISM:** δ < 0 on 12 of 25, which is chance; the only p_low < 0.05 is RB's 0.027, at Holm
    0.67.
  - **None TRANSFERS, none reaches GO.** All five micros (GC, SI, HG, CL, 6E) net negative.
  - **The drift from the open in these markets is too weak to pay its cost** (gross −$7 to +$13 a contract, positive on 20 of 25; the C2a medians are negative only net of cost — corrected the same day; not a reversion).
  - **CLOSED under R15** (the principal, 2026-10-01: "Close this, move on"). D737 is unaffected.
  - D736 is the other session's screen.
  - **D737 is this session's vault pre-registration of D735's YM k1.0 1σ_rem, FROZEN, programme slot 1** (the
    principal: "Yes write it into slot 110 and freeze"; the registry gave the lowest free slot). See the programme
    section.
  - **D733 CLOSED** (the principal: "Close D733").
  - **D735** is this session's NQ entry construction after D733. The principal: "That is so bad, have a fable 5.1
    agent analyse the results and come up with a better construction"; "Pre-reg D735, build and run it. Go for the
    widest construction". It is a merged design with a Fable 5.1 agent: NQ breaks from the market. The first minute
    from 10:00 to 14:30 with |z| of NQ's move minus the leg's ≥ k, traded in the spread's direction; 20 cells over
    ES / YM / RTY / EQ / TICK × k × stop.
  - **The reading is DRIFT ONLY by the declared rule (no GO).** Every cell fails the per-|x| bin leg. **But unlike
    D733 it beats its timing null:**
    - the equity legs rank 0.94–1.00, and 8 cells clear the family p95 of $14.41;
    - matched-row gains are +$9–14 a trade, and counter trades win.
  - **MECHANISM reads on YM only** (Holm 0.050). TICK is not it.
  - **The best cells, chosen after the fact:**
    - EQ k1.5 1σ: +$18.11 a MNQ, Sharpe 0.97, trimmed +$14, ex-2022 +$14, ρ +0.05 with NQ F2;
    - YM k1.0 1σ: Sharpe 1.11, 7/8 years.
  - In practice it is a 10:00 trade (93–97% of entries).
  - **Open, on the principal's word only:** a slot-10 vault pre-registration of ONE named cell. It would overlap D716's
    NQ 2024+ window.
- D733 is this session's NQ pullback entry (the principal: "I would like an entry signal?"; a merged design with a Fable 5.1 agent; "Ok pre-reg, build and run the merged study"): DRIFT ONLY, GO false. **CLOSED under R15 (the principal, 2026-10-01: "Close D733"), with a correction note on C1, O1 and O2 (s.7).** The primary cell (r 0.25, 5-minute turn) nets +$3.90 a MNQ inside its timing null (rank 0.74; matched-row gain +$0.02); it gives up $31.84 a day to the same-day follow (a later, higher entry); the turn costs $16.53 against the resting limit; 70% stopped; a 28%-win lottery (trimmed mean −$0.12); O1 ceiling +$86.62 (room exists, but nothing finds the holding pullbacks). Closing it is the principal's call. D734 (the other session's) is the F2 + compression book pre-registration; D732 (the other session's) is the ES/NQ micro book premise. The MACD arm was RETIRED by the principal (aa894c80). D731 is this session's flatness check (the principal: "I would like a proper flatness check, where the high the lower part of the U relative to the morning peaks the better"): NOTHING on NQ, YM, RTY; the dose runs the other way on NQ (continuation by flatness tercile +0.073 / +0.054 / +0.035; gamma −0.065, rank 0.13); the flat filter on the 13:30 entry costs $6.50 a trade (rank 0.24). With D730: NQ continues most on LOW relative participation (a quiet open, a deep lunch). The volume-profile detector (D730/D731) is CLOSED under R15 (the principal: "Close the volume-profile detector"); the principal declined D727's plain follow as a strategy ("I don't want a dumb follow type strategy. I would like an entry signal?"). D730 is this session's step 3 of the trend line (the principal: "we get direction from, delta from open, we get trend detection from the volume and size from the dettector?"): the volume profile does NOT detect continuation (NOTHING on NQ, YM, RTY; a heavy open comes with WEAKER continuation, by early-volume tercile +0.071 / +0.054 / +0.037; steadiness Q alone nothing); the detected book nets less than D727's unfiltered one (filter gain −$4.61, rank 0.32); SIZE HELPS false (sizing by the evening-before forecast: Δ net Sharpe −0.004). Volume finds big days, not continuing ones. **The principal's follow-up (2026-10-01): "a more flat/flatened U shape volume profile?"** D730's Q (recent vs early relative volume) is one form of flatness and read nothing; a cumulative flatness measure is a candidate D731 on the principal's go. D729 is the other session's volatility-unit year-concentration METHOD. D728 is this session's step 2 of the trend line (the principal: "Lets look at (B)"): cross-asset agreement does NOT sharpen NQ's continuation (G_eq, G_rates, G_usd all NOTHING; NQ continues MORE when ES/YM/RTY disagree, Δβ rank 0.043, not after Holm); the dollar-agreement book split (+$23.80 vs +$0.99 at k 1.0, rank 0.945) is an unsupported lead; NQ LEADS the index complex intraday (its move since the open predicts YM's and RTY's rest of day, ranks 0.986 / 0.991, while YM gives back its own move). **QUEUED, the principal's step 3 ("high volume early then constant volume predicts trending?"):** the intraday volume profile as a trend-day predictor on NQ (volume is on fut_NQ_rth_1m and fut_day1m); pre-reg on the principal's go. D727 is this session's trend detection curve (the principal: "Trend detection my old foe"; "Ok pre-reg build and run please"): NQ's move since the open continues into the rest of the day at every clock (beta +0.13 at 10:00, ranks 0.71–1.00), RECOGNISABLE FROM 14:30 by the declared rule; DOES NOT TRANSFER (YM reverses in the morning, RTY echoes only the morning); the practical NQ book (first |z| >= 1.5, hold to the close, one MNQ) nets +$15.22 a trade, Sharpe +0.83, rho 0.24 with the MACD arm (post hoc); GO false on transfer. Next is the principal's: a slot-10 vault pre-registration (needs their explicit word), step 2 (cross-asset agreement), or close. D726 is the other session's 0DTE close-run check. D725 is this session's Stage 0 on crossing yesterday's levels (the principal: "I love #1, look into it please, do a pre-reg for the premise checks"): NO-GO. Yesterday's close, VWAP and overnight midpoint do not continue when crossed (g_60 −$4.85 / −$1.88 / −$1.90 a MNQ; at or below the mirror level, rotation ranks 0.068 / 0.299 / 0.041), and the price falls back behind them more often than behind random levels (holding 52–53% vs 56–57%): sticky zones, not launch points. Only yesterday's high continues (D668's spent break). The evening-before size forecast again misses the oracle's trend-day ceiling. CLOSED under R15 on the principal's word ("Yeah Close it"). D724 is this session's Stage 0 on the principal's mean-reversion questions ("Which mean will the price respect ... how far in advance do you know about the size ... Does it affect the mean?"): NQ respects NO intraday mean (kappa negative for every anchor, below the rotation's p05 for VWAP, open, running and overnight mid; strongest in the afternoon); size is known EARLY (prior-close forecast 0.475 vs open 0.495 on the day range; the morning forecast predicts every later hour at 0.19–0.24 and adds beyond the last 30 minutes' vol all day); size does not change the mean; only yesterday's levels (close, overnight mid, VWAP) are touched beyond the mirror control, without reversion; CLOSED under R15 on the principal's word ("Close it"). D723 is this session's NG Stage A vault pre-registration with A1, FROZEN 2026-10-01 (programme slot 3; see the programme section). D722 is the other session's "Why 2022" diagnostic. D721 is this session's check of D720's quiet-day F2 pattern on ES, YM and RTY (the principal: "Close the quiet-day pattern on F2 after check for similar patterners in other roots"): NQ only (G1 rank 0.011; ES 0.11, YM 0.27, RTY 0.13, all NOT SIMILAR though same-signed); the volatility hypothesis does not fit (RTY most volatile, weakest; big moves on big days continue more); CLOSED under R15. D720 CLOSED for the arm and NQ F2 only (the principal: "Close the sizing overlay on those specific applications, I think will work on another type"). D720 is this session's size overlay (the principal: "Let try your idea, and push it to its edge"): the MACD arm and NQ F2 sized 0/1/2/3 MNQ by D691's day-size forecast; the arm CEILING ONLY (R1 −0.13 net Sharpe, rotation rank 0.24), NQ F2 NO CEILING (R1 −0.31, rank 0.016); the forecast knows the day's range (Spearman 0.51) but not the trade's, and its big days are the lines' weakest; closing it is the principal's call (R15). D719 is F2 at the commodity settlement windows (this session; NONE transfers; HO signal at an unviable size; HO CLOSED by the principal 2026-09-30). D718 is this session's premise check of proposal A, vol-control flow at the close (the principal: "Ok do the cheap check please"): ABSENT (beta +1.35 bp/sd, t 1.35; yesterday's flow as strong; the sign trade grosses $0.50 a MES trade); CLOSED under R15 (the principal: "Close A"). D717 is this session's reversed flow rule, tested fresh on NQ in-sample (the principal: "pre-reg, build and run a reversed rule test"; "insampel"): NEITHER on NQ (rho -0.007), P-principal missed; CLOSED with B under R15 (the principal: "Close B and its reversal under R15"). D716 is NQ F2 for the joint vault run (the other session; ES F2 withdrawn; slot 7). D715 is this session's in-sample test of proposal B, the absorbed morning move (the principal: "Pre-reg, build and run a test for B please"): NEITHER, the absorption gradient inverted (rho -0.061, 0.7th percentile); CLOSED under R15. D714 is NQ F2 only when ES F2 agrees (this session; NO INCREMENT). D713 is this session's MES oracle profile of E (the principal: "go get me the oracle first"; result: no single cut clears the fee). D712 is this session's joint-vault pre-registration of D708's rule, WITHDRAWN before any look (slot 10 free again). D711 is the other session's F2 placebo clocks and other index roots. D708, D709 and D710 are this session's three Stage 0 studies from the five-agent signal round (the principal: "I would like E, D and C all looked at"): D708 the short-gamma hourly continuation's timing term over the drift, D709 silver leveraged-ETF flow into the COMEX settlement, D710 the Treasury auction-day intraday V (D499 reopened for this use). D707 is F2's vault pre-registration (this session; the principal: "The F2 construction is now a candidate, add it to the big vault run"). D706 is the short-gamma day count on the unseen slices (this session; the principal: "Count short-gamma days"). D705 is the other session's relative-size filters on the last hour. D704 is the no-aggressive-push volume gate on V1 (this session). D702 and D703 are the other session's last-hour line. D701 is the channel–V1 overlap diagnostic (this session). D700 is the channel clock profile (this session; the premise check for the principal's trend detector). D698 is the other session's pre-reg for D696's cell. D699 is the gamma-gated 15-minute log
  MACD long (this session; the principal reopened the MACD for it, D675 §11). D697 is the move-triggered short-gamma
  long.
- **D699 RESULT (2026-09-30): V1, the histogram with a ±0.5 band, is a LEAD, but it fails the declared reading on (b).**
  - **Results:** +$10.47 a MES trade, net Sharpe +0.63, every year positive. Timing null 98.5th, gamma-label null 99.6th.
  - **Gate (b):** its gross beats the time-matched drift at NW t 1.64, not 2.
  - **Concentration:** 2022 is 75% of the net.
  - **V2 (ROC) and V3 (OR)** are inside their nulls.
  - **CLOSED by the principal, 2026-10-01 ("Close D699"),** after D722: V1 is positive in volatility units only in 2022 (ex-2022 +$3.55 net, Sharpe 0.25). The options were:
    a vault pre-reg (count the vault's short-gamma days first); or the 2022 diagnosis. **The 2022 diagnosis is done (D722):** V1 is positive in volatility units only in 2022 (ex-2022 +$3.55 net, Sharpe 0.25); no pre-trade variable identifies the 2022 state.
  - **D722 (2026-10-01, the "Why 2022" diagnostic):** no pre-trade variable explains 2022 on any line (all UNEXPLAINED); HO and the MACD arm are SCALE, NQ F2 REGIME, ES F2 MIXED, D699 V1 positive in vol units only in 2022; the index lines' 2022 is January to mid-May (the base lost after 2022-05-16); SEPARATE day to day, but the ES F2 + NQ F2 + D699 book earns 77 % of its net in 2022 ([result](../decisions/D722-DIAG-RESULT-no-variable-explains-2022.md)).
  - **D726 (2026-10-01): did daily 0DTE end the last-half-hour continuation? NOT SUPPORTED** on ES and NQ; **CLOSED by the principal ("Close, Move on"); reopen only with SPX 0DTE volume, on their word.** Every sign points the 0DTE way (era delta e -0.07, z -0.80; the Tue/Thu DiD +0.17, z +0.95), but nothing clears 2 SE, and the day's 0DTE dose carries nothing (rho +0.03). A larger test would need SPX 0DTE volume, which is not on disk ([result](../decisions/D726-STAGE-0-RESULT-0dte-not-supported-direction-only.md)).
  - **D729 (2026-10-01): the volatility-unit concentration report** (the principal: "construct a non-binding informational gate on the volatility unit"). Applied to the queued vault lines in-sample: NQ F2 BOTH (2022 60 % of gross $, 55 % in vol units), D649 MNG BOTH (75 % / 61 %), NG Stage A SCALE-CARRIED (62 % / 44 %), D680 NEITHER. Informational only ([record](../decisions/D729-METHOD-the-volatility-unit-year-concentration-report.md)).
  - **D732 (2026-10-01): a book that does not rest on one year, at one micro, ES and NQ: GO by the declared rule** (the arm + NQ F2 + NQ compression C1, one MNQ each: net Sharpe 1.22, Sortino 1.97, max DD $4,920; no year over half; 0.95 without 2022). POST HOC: 2020 + 2022 are 86 % of the net; without both the book is 0.34, carried by the compression break (0.98; the arm 0.01). ES adds nothing at micro. Next, on the principal's word: a declared-book pre-registration for the joint run ([result](../decisions/D732-STAGE-0-RESULT-go-but-the-book-is-two-years-and-compression.md)).
  - **THE MACD ARM RETIRED by the principal, 2026-10-01** ("That MACD arm is useless ... using capital to trade when you don't make money, even if you don't lose money is shit"). It is in the market on 83 % of sessions and makes 0.01 net Sharpe without 2020 and 2022. The prop book is empty until an assembled book passes the joint run; the candidate is NQ F2 + the compression break. Written in BOOK_PROP and COMPONENTS_PROP (entry #2 retired).
  - [x] **D734 FROZEN (2026-10-01; the principal: "Ok finish this off and freeze"): the assembled book NQ F2 + the compression break, one MNQ each, for the joint run** ([record](../decisions/D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md), A1 P3b censored, A2 the calendar and the vault mechanics). `data/FROZEN_vault_d734_nq_book.json` (runner 983f5c64…; hashes D716/D680/the joint wrapper/hurdle_p/prop_venues). Known answer in-sample: ADMITTED, $10,582.76, Sharpe 1.40, Sortino 2.69, max DD $1,360. Dry-checked: the freezes verify, and the vault path stops at the order check. **Joint-run step, after D716 --vault and D680 joint-wrapper --run-vault:** `uv run python scripts/vault_d734_nq_book.py --vault --principals-word "..."`.
- **D700 RESULT (2026-09-30): the channel trend detector (D480's hand cell on rescaled ES bars) reads NEITHER on every
  clock.**
  - **No clock fades,** against my prediction.
  - **5m and 15m on short-gamma days:** +$4.41 and +$6.76 a MES event at +60 min, above the timing null's p95
    (97.1st and 96.7th), with clustered t 1.96 and 1.86.
  - **1m:** nothing.
  - **The strict "held 10 closes" reading** removes what there is.
  - **Waiting on the principal:** stop; overlap with V1 first; or the channel as V1's exit.
- **D701 DIAG RESULT (2026-09-30): the overlap between the channel and V1.**
  - **5m: SAME INFORMATION as V1.** 93% of its up onsets come while V1 is long (base 53%), and all of the
    continuation is there. D700's 5m t 1.96 is not a second confirmation.
  - **15m: uncorrelated with V1** (φ 0.00), and it continues whether V1 is flat or long. The INDEPENDENT and
    CONDITIONER flags rest on 41 onsets and 29 trades, and the conditioner is 0.35 SE.
  - **Channels arrive after V1's entries** (up held at 5–9% of them).
  - **Waiting on the principal.**
- **D704 DIAG RESULT (2026-09-30): the no-aggressive-push volume gate on V1 reads NO INFORMATION.**
  - **Direction right:** Spearman +0.044, the upper half +$18.72 against the lower +$2.23, 6 of 8 years positive,
    +0.084 without 2022, and nothing on long-gamma days.
  - **Inside its null:** 84.6th percentile, about 1 SE.
  - **No pre-2016 sample exists** (the options book starts 2016, and Sierra has no ES contract before ESZ15).
  - **Waiting on the principal.**
- **D706 PREMISE COUNT (2026-09-30): the unseen slices cannot confirm the short-gamma direction line.**
  - **The count:** the vault holds 120 short-gamma days (to 2026-09-09) and the clean slice 66. 85–98% of them are
    short by the ES book alone.
  - **The power:** best case (V1 + the 15m channel, all 186 days, full in-sample effect), a pass probability of 0.39.
    At 50% of the effect it is 0.17.
  - **Waiting on the principal:** park or close the line (R15), or hold it for a longer unseen sample.
  - **Superseded in part by D708:** D706's power covered once-a-day constructions on G_SUM days only. The hourly grid
    on ES-book-short days (288 unseen sessions) has more power.
- **D708 STAGE 0 (2026-09-30): SIGNAL, GO for a joint-vault pre-registration.** This is proposal E from the five-agent
  round, on the principal's ruling "Timing term as the gate".
  - **The result:** on ES-book short-gamma days (858), the hourly continuation's side choice earns +$3.09 a MES trade
    over the per-year clock-matched drift (t 3.17, the 99.9th percentile of its timing null). Both legs are positive
    (+$2.98 / +$3.22), long-gamma days are −$0.18, the gamma contrast is at the 99.8th percentile, and 7 of 8 years
    are positive.
  - **The drift is only 2% of the profit,** because the book is balanced long and short.
  - **Net at MES:** −0.45 in-sample; at full ES +0.45. The unseen-price projection at MES is a thin positive.
  - **The power:** 0.63 at the full effect, 0.26 at half.
  - **D712 (its vault pre-registration) was WITHDRAWN before any look,** on the principal's word. The account trades
    MES only, and at MES the rule loses in-sample.
  - **CLOSED 2026-09-30 (the principal: "Close E - If even the oracle's best is 0.93 dollars 106 times a year we stand no chance"), under R15.** D713: the oracle's best bucket nets about +$0.92 a MES trade, 106 a year.
- **D709 STAGE 0 (2026-09-30): FAIL (not the funds).** Silver moves into its 13:24–13:25 settlement window with the
  day's sign after AGQ/ZSL switched to the settlement benchmark: +$5.63 a SIL gross (t 3.14, above every rotation).
  - **Specific:** the midday placebo is flat, and so is gold.
  - **Why it fails:** the pre-era carried the effect too (t 4.03), though only in the pit era: 2015-07 → 2019-01 is
    flat. That split is reported, post hoc.
  - **Net and trend:** net −$2.37 at $8. It fades to nothing in 2022–2023.
  - **CLOSED 2026-09-30 (the principal: "close the silver"), under R15.**
- **D710 STAGE 0 (2026-09-30): PRESENT, then MECHANISM ONLY.**
  - **The premise:** the dealers' auction-day V (FRBNY SR 1188) is in the Treasury futures. Pooled z +0.26 (t 4.98),
    above every enumerated placebo schedule, with an achieved share of 0.68 overall and 0.69 in 2015–23. The 11:00 and
    ±1-week placebos are flat, and all seven of the paper's predictions hold, the dealer-share dose included (t 2.06).
  - **The trade:**
    - the unfiltered legs gross +$17.48 (t 2.89) and net −$1.18 at full size;
    - the paper-sized filter (mostly the 30-year pre-auction short) nets +$43.85 a trade at t 1.45, about 12 trades a
      year. Component net Sharpe +0.48, ρ under 0.1.
  - **CLOSED 2026-09-30 (the principal: "Close it, not on the size problem, but on the rarity and spikiness of the strategy"), under R15.** The tradeable part is a pre-auction short on ZF and UB, about 18 days a year and lumpy by year. The mechanism stands as evidence.
  - **New data:** `data/calendar/treasury_auctions.csv` (Fiscal Data, 2009–2026) and `fomc_2010_2015.csv`.
- D695 is the short-gamma continuation's directional inputs; D696 is D694's busy / low-IV/RV cell (below).
  - D689 is the short-gamma continuation stage 0.
  - D690 is the oracle filter and accuracy assessment, and D692 the oracle profile at MES (the other session).
  - D691 is the implied-vs-realised volatility premise check (RESULT: SIZE INFORMATION CONFIRMED on ES and NQ).
  - D693 is the short-gamma filter at MES (the other session).
  - D694 is D691's Stage 1 (below).
- **D694 (D691's Stage 1) is NOT SUPPORTED on ES and NQ, and the implied-volatility line is CLOSED for the break.**
  - Coiled days are bigger, but IV's own information picks no better breaks: ES rank 0.77, NQ 0.30 against the
    count-matched ingredient null.
  - **D696's busy-realised / low-IV/RV cell is CLOSED as unstable (the principal, 2026-09-30; recorded on D698).**
    - It survived in-sample (D696), but its effect lives in 2019-07 → 2022-08. The most recent window shows nothing.
    - D698 was never frozen or scored. Slot 10 was never registered and stays free.
    - Do not re-test it in-sample with a new split.
  - **EXPECTED-PROFIT FILTER LEADS (the principal, 2026-09-30).** A 7-agent scan of D1–D700 looked for trades whose
    mechanism works before costs but fails after them. The figures below were checked by an independent verification
    pass. D1–D200 held no usable candidate.
    - **1. ES last-hour continuation (D618 §3c): REOPENED by the principal ("that is the whole point of this study"),
      and IN PROGRESS.**
      - **The trade:** the sign of 14:30 → 15:30, held 15:30 → 16:00.
      - **Numbers:** gross +$3.40 per MES trade (rank 0.999 against an enumerated rotation), fee 1.25× gross, hit
        0.493 with median 0. 2016–17 was negative.
      - **Prior evidence:** D688's gamma filter at 2× cost failed on the close (t 0.30).
      - **D702 (oracle, MES): the edge IS big-move-shaped.**
        - The size-only oracle's top 20 % nets +$12.78.
        - The top 20 % by the prior hour's |F5| (known at 15:30) nets +$8.87, Sharpe 0.74 (hindsight threshold).
      - **D703 (the principal's filter: |F5|/σ, gamma and ln IV, the expected-profit template): DEVELOPMENT FAIL,
        and the line closes again.**
        - +$11.02 net on 211 trades at t 1.51, but 167 of them in 2022.
        - The dollar bar made it an IV-regime gate; |F5| alone cleared it 4 times.
        - The slice is unspent.
      - **D705 (the declared second look; F1 / F2 / F3 relative-size filters at the top 20 %): NONE PASSES, and the
        line closes again.**
        - **F2 (the prior hour's size plus today's vol)** passes the edge (+$13.21, t 2.48, Holm p 0.02), the
          best-of-three null (rank 0.996) and ex-COVID.
        - **It fails only the one-year gate:** 2022 holds 59.9 % of its net, against 50 %.
        - It keeps +$7.17 without 2022 and +$7.06 after 2022-05-16.
      - **DECIDED 2026-09-30 (the principal: "The F2 construction is now a candidate, add it to the big vault run"):**
        - F2 is registered as D707 (`b6b42cd4`), frozen, and holds programme slot 7;
        - one look at 2024-01-01 → 2026-09-18 happens in the joint run;
        - COMPONENTS_PROP entry #4, PROVISIONAL. See the programme-rule section below.
        - **SUPERSEDED the same day by D716:**
          - ES F2 is withdrawn before any look;
          - NQ F2 (with the agreement-book takeover) holds slot 7 instead.
      - **D711 (2026-09-30; mechanism tests of F2, in-sample, the vault unspent):**
        - **A1, the placebo clocks on ES, is UNRESOLVED.** 13:30 → 14:00 z +0.27 is nearly F2's +0.30; 11:30, 12:30 and
          14:30 are nothing.
        - **A2 is MIXED.** NQ transfers (+$20.67 a MNQ trade, ρ 0.87 with ES F2: the same trade). YM misses its
          rotation (0.936). RTY has no edge.
        - **The corrected (efficiency) null ranks ES F2 at 0.991.**
        - **Open, the principal's call:**
          - NQ F2 as a sizing choice beside ES F2 (it would need its own vault pre-registration; programme slot 10 is
            free again, after D712's withdrawal).
        - **The D711 addenda (post hoc):**
          - with 10 % trimmed from each tail, ES F2 keeps +$9.79 (t 3.14) and NQ +$18.94 (t 4.00);
          - ES's 13:30 island is five trades and does not replicate on NQ, so it is DROPPED as a lead;
          - ES and NQ F2 share 217 days, agree on direction on 216, and take 96–104 % of their profit there.
        - **D714 (in-sample): NQ traded only when ES F2 agrees is NO INCREMENT.**
          - +$25.58 against +$20.77 a MNQ trade;
          - but random deletion of 55 trades matches it (efficiency rank 0.856);
          - not carried.
      - **D719 (2026-09-30, in-sample 2018 → 2023): F2 at the commodity settlement windows, twelve roots — NONE
        transfers.**
        - **HO carries the signal:** +$119 gross / +$109 net a full contract, t 2.74, Holm 0.037, efficiency rank 0.991.
        - **But it is NOT VIABLE at the $50k account:** q99 $1,117, no micro, and a $4,304 drawdown at one contract.
        - **HO CLOSED by the principal, 2026-09-30** ("Ok close, Heating Oil"), with RB. None of the three routes is
          taken. MHO exists, but it printed zero volume on 32 of 32 sessions (`data/d719_ho_micro_volume_check.json`).
          HO's 2024-01 → 2025-02 slice and its vault stay unread for this line.
        - **KE is deferred** until its one-minute bars are built.
    - **2. CL settlement flow (D648): OPEN**; the form choice (x_GM vs x_SR) is with the principal.
      - **The trade** runs with the funds into the window: +$28.46 gross, t 2.230 against a bar of 2.241, net −$3.00
        at $31.46. The fade after the window (T3) is +$22.34, t 3.18, not cost-tested.
      - **The x_GM-filtered form is already read in-sample** (+$14.91 over 70 MCL trades), so a confirmation needs
        unread CL data. CL is sealed until 2026-10-10, and CL's vault holds no look.
    - **3. CL hourly log-MACD (D484/D495): CLOSED** under R15 (D675). Gross Sharpe +1.09 against net +0.11. It needs
      the principal's word, and CL's in-sample slices are spent.
    - **4. 5-day reversal in US single names (D350/D353): OPEN, unpromoted, personal book.**
      - **Numbers:** gross +43.4 bp (t 4.8), hit 51.5 %; net −18.6 on the published spread, +17.9 on the per-bar
        convention.
      - Tradeability waits on D336's quoted-spread pull. No expected-profit filter tried.
  - **DEFERRED to a future study (the principal, 2026-09-30): implied volatility as a trade.**
    - **The design, drafted but not registered or numbered:** sell the ATM ES Friday-PM weekly straddle at Friday's
      settlement and hold it to the next Friday's 16:00 expiry. That is one non-overlapping trade a week, about 460
      in-sample weeks, 2016-01 → 2025-02; NQ secondary.
    - **Tests:**
      - (A) the premium: gross, with Sharpe and Sortino, the tail and ex-Feb–Apr 2020;
      - (B) whether the entry-day IV/RV (D691's ivrv) predicts the week's P&L, against a rotation null over weeks;
      - (C) selling only when IV/RV is high against always selling;
      - costs as the breakeven in points and net at a declared band.
    - **Facts already gathered:**
      - no prior repo study of the VRP or short vol;
      - EW1–EW4 Friday weeklies from 2016 (EW3 only from 2016-07-15);
      - the fixture has no expiry-day option settle, so the payoff comes from `fut_settle_strip`'s expiry-date
        settlement (D618's convention). Check coverage on every expiry, including Good Friday weeks;
      - there is no options cost line, and no quotes before 2025-09, so the spread is unmeasurable in-sample;
      - options are eligible for the personal book only.
  - D691 §8's "ES has no unread index slice" was unsupported. ES's vault window is sealed and unread for break
    constructions (D694 §0).
  **Check every branch, and the commit messages, before claiming a number.**

## Programme rule: ONE joint vault run (the principal, 2026-09-26; amendment A10)

- **JOINT-RUN PREP, 2026-09-30 → 10-01 (the principal: "go with your full recommendation"; "1-3 I approve"; "I take both your recomenations"). The run order and every input's status is `docs/internal/JOINT_RUN_CHECKLIST.md`.**
  - **Independent verification pass, 2026-10-01 (2b1a6c93): §0 is 11/11 and every freeze verifies.** Read the
    checklist's V-table first. The principal said "Yes to all 3" on 2026-10-01:
    - `--accept-hole 2026-09-12` (the daily-split top-up has no Saturday file);
    - the NG panels step's `temp/` reference file is handled by procedure, with no D723 re-freeze;
    - the D462 rebuild, and so the joint run, comes **after** D626's 10-10 read.
  - **Slot 9, D680:**
    - `scripts/joint_d680_vault.py` builds the NQ vault inputs and holds D663's cut at 2026-09-19 for the frozen
      runner's call. This is a joint-run wrapper, not an amendment.
    - Proved in-sample: D644's fixture byte for byte to 2023-12-29, and D672's per-year C1 exactly.
    - SPY is refreshed to 2026-09-30 in `data/raw/alphavantage/daily_refresh/SPY_20260930.json.gz` (`--spy`).
  - **Slots 3 and 8, NG:**
    - The input path is `scripts/build_ledger_vault_inputs.py`. It reproduces all six frozen inputs, D630 (1,028 /
      $66.0214) and D649 (270).
    - The vault strip is `scripts/build_strip_vault.py`, cut at 2026-09-19T00:00Z. It reproduces the committed strip.
    - The principal's anchors are the defaults: LAST_ANCHOR 2026-06-30 and SWAP_Q_LAST 2026-Q2.
    - The swap-free quarters are extended to 2026-Q2; BOIL's Q2 reads "swaps held" under the frozen rule.
  - **Slot 3, NG Stage A: D723 PRE-REG + A1, FROZEN 2026-10-01** (`data/ledger_frozen_vault_h2_ng.json`; the
    principal: "Do the write up and freeze").
    - The gate is D630 §8's rule with the t as NW(5).
    - `--accept-a6-tail-moves` is permitted.
    - The run takes the full `d630_trade_table.csv`.
  - **CLOSED 2026-10-01 (the principal: "close that last 10-09 thing"): the 2026-09-10 ohlcv-1m hole.**
    - `scripts/fetch_prelapse_topup.py` starts the ohlcv-1m job at 2026-09-10 (`JOB_START`); the other jobs start at
      09-11, and the re-quote still refuses anything not USD 0.00.
    - After the 10-09 download, check that the job record carries `"start": "2026-09-10"`.

- No model opens the vault (2025-03-01 → 2026-09-18) by itself.
- Every model that has passed its in-sample gates and is frozen (`scripts/freeze.py`) is scored in one joint run,
  called by the principal: when the planned set is ready, or earlier on their word.
- Each model is scored on its own pre-registered vault criteria, and the assembled book is scored on the same
  period.
- α stays in fixed slots of 0.005 per family, so a joint run changes no bar.
- **FROZEN 2026-10-01 (the principal: "I choose YM 1.0, it look really good"; "Yes write it into slot 110 and
  freeze"): D737, NQ leads the Dow (D735's YM k1.0 1σ_rem, one MNQ). Programme slot 1.**
  - **Why slot 1, not 10:** the principal said slot 10, but `Registry.register` takes the lowest free slot, and 1 has
    been free since 09-30. The α is the same 0.005; free slots are now 2 and 10, with 0.040 allocated.
  - **The files:** the freeze is `data/FROZEN_vault_d737_nq_leads_the_dow.json`, hashing the runner, D737, D735's
    records and JSON, the rehearsal, the power file and 29 imported files. The runner is
    `scripts/vault_d737_nq_leads_the_dow.py`.
  - **Known answer:** 1,699 trades, +$14.869654. The Nov–Dec 2023 overlap (36 trades) reproduces through the vault
    loader.
  - **The gate:**
    - PASS: ≥ 100 trades, mean net > 0 with one-sided NW(5) t ≥ 1.645, and mean net above the vault-window timing
      null's p95;
    - FAIL: mean net ≤ 0;
    - else UNRESOLVED.
  - **Power** (`data/vault_d737_power.json`, about 595 expected trades):
    - G1: 0.63–0.68 / 0.37–0.42 / 0.16–0.19 / 0.05–0.07 / 0.013–0.015 at 100 / 75 / 50 / 25 / 0 %;
    - the full gate on 64 in-sample windows the vault's length: PASS 0.61, UNRESOLVED 0.39, FAIL 0.
  - **Promotion is a separate, higher bar.** The registry page requires an adjusted p ≤ 0.005 (one-sided t ≈ 2.58)
    plus the programme DSR. A vault PASS at t 1.645–2.58 confirms the line but does not promote it on the programme's
    α; the same holds for D716 and D680.
  - **When it runs:** after the D462 rebuild, in JOINT_RUN_CHECKLIST §3. It shares NQ's 2024+ sessions with D716.
  - **Ledger:** entry #6, PROVISIONAL.
- [x] **The forward recorder is RUNNING (2026-10-01; the principal: "start with the recorder").**
  - **What it is:** `scripts/record_forward_nq_lines.py`, run by the daily scheduled task `forward-nq-recorder`.
    - It decodes Sierra's NQ / YM / ES tick files from 2026-09-21 only, into one-minute bars
      (`data/raw/forward/`, irreplaceable after about five months).
    - It computes D737's line on them with D737's own functions (`data/forward/d737_forward.csv`, one row a session;
      revisions are logged, never silent).
  - **Validated in-sample** against Databento: closes equal on 99.6–99.9% of minutes, and D737's 118 trades identical.
  - **Burn-in:** σ needs about 35 forward sessions, so the first scoreable session is around 2026-11-09.
  - **Watch:** the March 2027 files (NQH27, YMH27, ESH27) must exist before the December roll (about 2026-12-10). The
    recorder prints MISSING until they do, and `--refresh` queues them.
  - **NQ F2 and C1 ADDED as inputs (2026-10-01; the principal: "yes add F2 and C1 to the recorder").**
    - The recorder now also keeps each session's full Globex minutes, on the day session's front
      (`data/raw/forward/fut_{NQ,YM,ES}_fwd_globex_1m.csv.gz`, fut_opening_globex_1m's layout; from 09-22, because
      09-21's Globex opened on 09-20, before the seal).
    - With the day-session bars, that is everything F2 (D716, slot 7) and C1 (D680, slot 9) read.
    - **Validated in-sample** (2023-04 → 12, against D644's fixture): C1's overnight high and low are equal on all 192
      NQ and ES sessions; minutes ≥ 99.85%.
    - **Their ledgers are NOT computed yet, and cannot be before the joint run.** Both rank each day among the
      previous 250 days, three times over (D671's `tiers`), so their first forward tier reads the vault window.
    - **The forward-log step is BUILT and PROVED (2026-10-01; the principal: "yes start on the F2 and C1 forward-log
      step"):** `scripts/forward_f2_c1_ledgers.py`.
      - The splice is each line's frozen functions over Databento history + Sierra bars, with Sierra contract
        names mapped to Databento codes so the join never reads as a roll.
      - **The proof, in-sample** (`data/forward/f2_c1_splice_proof.json`): Databento to 2023-06 + Sierra 2023-07 → 12
        against all-Databento, every Databento file restricted as text before 2024.
        - F2: 129/129 sessions agree, and all 32 trades match on side, entry and tier; net $29.35 against $30.85
          (7 exits differ by ≤ 1.25 points).
        - C1: 129/129 sessions agree, and all 27 trades match on side and tier; net $11.20 against $11.89.
      - C1's forward half days come from ES's own bars (the day session ending before 15:30). The CME calendar
        (ends 2026-09-09) is built from the Databento archive and cannot be extended after the lapse. The rule
        equals the calendar on every NYSE day of 2016–2023, and the usable sessions equal G0's (124/124 on 2023-H2).
    - **Owed AFTER the joint run (one command, in the main checkout):**
      `uv run python scripts/forward_f2_c1_ledgers.py --ledgers --spy <a SPY daily file reaching the last forward
      session>`. It writes `data/forward/f2_forward.csv` and `c1_forward.csv`, and refuses until both
      vault results exist. History: the rebuilt `fut_{NQ,ES}_rth_1m` and `data/joint_run/d680/`, through
      2026-09-18.
- [ ] **Pre-lapse gap pulls (2026-10-01; the principal approved A, B, C and D).**
  - **The record:** `scripts/fetch_prelapse_gaps.py`; jobs in `data/prelapse_gap_jobs.json`; quotes in
    `data/prelapse_gap_quote.json`, all USD 0.00.
  - **The pulls:**
    - **A:** ohlcv-1s for NQ/ES/YM/RTY + MNQ/MES/MYM/M2K, 2010 →;
    - **B:** statistics + definition for MGC/MCL/SIL/MHG/M6E;
    - **C:** status / bbo-1m on the 41 roots and NQ + CL/NG options statistics/definition, from each archive's end;
    - **D:** MBO for MNQ/MES/MYM/M2K, 2026-09-01 →.
  - **Done 2026-10-01:** all ten submitted; A, B and C downloading.
  - **Owed 2026-10-10 (task `prelapse-gaps-final`, 14:00):**
    - C2 (C again, 10-01 → the lapse);
    - downloading C2 and D after the 10-09 top-up, whose 90 GB free-space check D would otherwise threaten.
  - **The principal's own action:** a backup of `data/raw/databento` (about 250 GB; no copy exists; after the lapse
    the base pull alone re-costs about $7,719).
- [ ] **PARKED for the personal book, until there is real capital** (the principal, 2026-10-01: "Prop book only
  personal book when we have some real capital"). These are mean-reversion ideas from the same day; all hold for
  several days, so the prop book's 16:10 flat rule excludes them.
  - **The multi-day index dip:** ES, NQ, YM or RTY closes well below its recent range; hold 2–5 sessions, with a time
    stop counted in bars.
    - Basis: the daily variance ratio is below 1 on 7 of 8 roots; D483's dip earned +47 bp over 5 bars on the stock
      panel; D528 found reversion decays over about 5 bars.
    - It needs an always-long control with matched exposure.
  - **Its volatility-spike gate:** volatility-targeting funds re-lever as realised volatility falls after a spike.
  - **Treasury multi-day reversion:** ZN and ZB variance ratios are 0.89 and 0.92; micro yield futures exist.
- [ ] **AFTER THE JOINT RUN: state-based allocation** (the principal, 2026-10-01: "Add that to the AITODO for after the
  vault run if we still have components then (We will)").
  - **The source:** the principal's deposit `User-Doc-Deposit/STATE_BASED_ALLOCATION.md` and its review
    `docs/internal/STATE_BASED_ALLOCATION_REVIEW.md`. Follow the review's §5.
  - **Step 0, the binding-constraint check** (in-sample, no model):
    - put the surviving components' daily P&L on one calendar;
    - count the overlaps;
    - run hurdle P on the one-MNQ-each book (P2, P3a, P3b at $50k);
    - verify each venue's contract limit.
    - **If P3b holds, there is nothing to allocate.**
  - **Step 1, per-component gates** (with the principal, oracle first):
    - the realised-volatility percentile + trend-strength baseline before any HMM;
    - HMM: filtered probabilities only, 2–3 states, refit stability checked;
    - the label is expected net or day-risk, not P(win);
    - nulls by Σg/Σ|g| (D711-A1).
  - **Step 2, a book risk rule against the fixed "all on, one MNQ each" rule** on P(pass) / P3b, only if step 0 says
    the barrier binds.
  - **Step 3, confirmation on forward sessions only** (after 2026-09-18), because the 2024+ NQ slice is spent by D716
    and D737.
  - **Dropped from the deposit's plan:** RL, exit modulation as the first step, and P(win) as the label.
- **Frozen and waiting:** the settlement ledger's NG Stage A (`data/FROZEN_ledger_stage_a_ng.json`), and **D649's
  NG projected-profit line** (`data/FROZEN_ledger_vault_pp_ng.json`, programme slot 8): one MNG when the projected
  move clears 2 × $5, scored on D630's vault trade table (`scripts/ledger_vault_pp_ng.py --vault`, on the principal's
  word). D649 needs D630's vault inputs built first (D630 §8).
- **FROZEN 2026-09-29 (the principal: "happy for the NQ compression to stay in queue for the big vault run"; "Freeze
  the ones that where queued today"): D680, the NQ compression break, programme slot 9.**
  `data/FROZEN_vault_d680_nq_compression.json`; runner `scripts/vault_d680_nq_compression.py` (known answer reproduced:
  387 C1 trades, +6.93 / +7.56 bp net). PASS: >= 30 C1 trades, gross one-sided HAC t >= 1.2816, net > 0. Power
  (`data/vault_d680_power.json`): PASS 0.66 / 0.30 / 0.18 / 0.10 at 100 / 50 / 25 / 0% of the in-sample edge, ~85
  trades. D668's plain break is NOT queued (C1 is its subset); B0 is reported beside.
  **Prerequisite before the joint run (not built): the NQ vault-input path** -- D644's `fut_opening_globex_1m` built
  through 2026-09-18 into a separate file and G0's loader (`usable_sessions`, `load_bars`) with the cut moved, written
  out as `--vault-bars` / `--vault-use`; `--vault` re-proves the known answer on its in-sample part before scoring.
  **OPEN, the principal's decision (found 2026-09-30 while building D698): D680's frozen `--vault` would score ZERO
  vault trades.**
  - Its `book()` builds the frame with D663's `root_frame`, which keeps only sessions before the module constant
    `RESERVED_FROM` = 2025-03-01 (`scripts/stage0_d663_per_root_gamma_break.py:141`).
  - Fed vault bars, it would drop every vault session, write UNRESOLVED, and then refuse a second opening.
  - The frozen files are not edited. The options are an amendment record, or a joint-run wrapper that raises
    `T.RESERVED_FROM` before calling it.
  - D698's `raised_cut` and its rehearsal prove that mechanism works both ways.
- **WITHDRAWN 2026-09-30, before any look (the principal: "Remove ES F2 from the vault run and keep NQ F2 and NQ F2 only
  when ES F2 agrees"): D707, the ES last-hour F2.**
  - Slot 7 was released with a recorded reason (`Registry.release`).
  - D707's record, runner and freeze are kept as committed, and still verify. **Its `--vault` mode must never be run.**
  - ES's 2024+ last-hour data is read as D716's input, so ES F2 has no clean look left.
- **FROZEN 2026-09-30 (the principal: "Ok I agree with your recommendations, write it up please"): D716, NQ F2, with a
  fixed-sequence takeover by "NQ F2 only when ES F2 agrees". Programme slot 7.**
  - The freeze is `data/FROZEN_vault_d716_nq_f2.json`; the runner `scripts/vault_d716_nq_f2.py`.
  - **Known answers held:** D711's NQ book (274, +$20.670105), D714's B (271) and A (216, +$25.578712), and D707's
    ES F2.
  - **Step 1:** NQ F2 PASS with ≥ 30 trades on 2024-01-01 → 2026-09-18, net > 0 and NW(5) t ≥ 1.2816.
  - **Step 2, only if step 1 passes:** the agreement book takes over iff its net t ≥ 2.576 and it beats count-matched
    random deletion on efficiency (D714's rule, seed 716).
  - **Power** (`data/vault_d716_power.json`, 147 contiguous 640-candidate windows, about two independent):
    - the size is 0.101;
    - PASS is 0.69 / 0.61 / 0.52 / 0.13 at 100 / 50 / 25 / 0 % of the in-sample edge;
    - takeover is 0.06 / 0.11 / 0.09 / 0.00;
    - medians are 129 B and 102 A trades.
  - **Data:** both fixtures run to 2026-09-09. No vault-input build is needed; `--vault` re-proves every known answer on
    the extended build first.
  - **Ledger:** entry #5, PROVISIONAL. Entry #4 (ES F2) is PARKED.
- **WITHDRAWN 2026-09-30, before any look (the principal: "Did I tell you to add E to the 10th slot? We can't afford to
  trade on ES so it doesn't matter if its profitable there"): D712.**
  - Slot 10 is unregistered and free again, and D712's freeze file is removed (see its WITHDRAWN section).
  - The rule loses at one MES in-sample (−0.45). Its runner and power output are kept as evidence.
  - **Free programme slots (2026-09-30, after the principal released slots 1 and 2, "Release 1 and 2"): 1, 2 and 10; 0.035 allocated.**
- **CLOSED 2026-09-29 (the principal: "Ok close both of those"):** opening v2 (D652/D659) without spending its vault
  look (no freeze, no slot); D668's NQ plain break as a separate vault line (reported beside D680 as B0). Slot 10
  stays free. **The NQ vault-input path is deferred ("start on the NQ Vault period data later").**
- **CLOSED 2026-09-29 (the principal: "close opening model v1"; slot 7: "Release it"):** the opening agent-state
  model's H-O2 (D658), without its vault look. **Programme slot 7 RELEASED** (`Registry.release`; the family is kept in
  `released` in `data/programme_registry.json`): the principal's override of the never-retroactively default, for
  this family only. (Superseded: slot 7 now holds NQ F2, D716; slots 1 and 2 were released 2026-09-30; free: 1, 2 and 10.)
- **PARKED (the principal, 2026-09-28): D630 §8's vault-input path.** The plan, inventoried 2026-09-28 from metadata only:
  - a wrapper (`scripts/build_ledger_vault_inputs.py`, not yet written) loads each frozen builder unchanged and moves
    only its cut and output paths;
  - proved first with the cut left at 2025-03-01 by reproducing the frozen in-sample inputs byte for byte;
  - switched to the vault only at the joint run.

  On disk for 2025-03 → 2026-09:
  - the NG/CL one-second files (to 2026-09-19) and `fund_nav_daily` (to 2026-09-18);
  - the fund filings in `fund_holdings_quarterly`.

  **Short:** the settlement strip ends 2026-09-10, six sessions early; the 10-09 top-up plus a strip rebuild covers it.
  The event calendar is to be checked. Build it before the principal calls the joint run.

## Index reweight flow — opened 2026-09-27 (the principal: "start the index-reweight pre-registration")

- The spec is `docs/internal/User-Doc-Deposit/INDEX_REWEIGHT_FLOW_PREREG.md` v1.3 (read-only).
  The facts are in `data/index_reweight/`:
  - `SOURCES.md`, `methodology_facts.json`, `weights/2016–2026.csv` (BCOM);
  - `SOURCES_GSCI_CFTC.md` (GSCI, CIT, COT);
  - `DATA_INVENTORY.md` (what's on disk; free Databento quotes).
  - The GSCI methodology PDF (Aug 2026) is cached at `data/raw/index_reweight/`.
  - None of this is committed yet.
- **The deadline.** The model freezes before BCOM's 2027 announcement. BCOM announced between 10-20 and 11-09 in
  2015–2025 (2025: 10-30); GSCI in early November.
  - **Freeze by Fri 2026-10-16.**
  - Until then, read no 2027 weight, pro-forma or advisory publication from either index. GSCI's advisory pro-forma
    comes about a month before its announcement.
- **The split (programme rule A10):**
  - in-sample: the January events 2016–2025 (10) and the monthly rolls to 2025-02;
  - vault: January 2026 and the rolls 2025-03 → 2026-09;
  - forward: January 2027.
- **Facts established (all sourced, no fabrication):**
  - **Trading days.** BCOM's replicating book trades the closes of **business days 5–9**, 20% a day: the "Hedge Roll
    Period". The index roll period is BD6–10, so the spec's "6th–10th" is the index window, not the trading days.
    GSCI also rolls on BD5–9. The two indices therefore trade on the SAME days, and a combined κ (R-D4) is near
    certain.
  - **January rebalance** runs inside the January roll. Most CME components have no contract roll in January, so
    their January flow is the reweight alone.
  - **The multiplier (CIM) date** is BD4 of January, at that day's settlements. Three printed dates are to be
    checked against data: 2016-01-06, 2018 (Jan 5 or 6) and 2022-01-07.
  - **BCOM weights** 2016–2026: each year sums to 100%, and each year's printed prior weights chain exactly to the
    previous year's targets.
  - **Tracking AUM** is stated for 2019 (~85), 2022 (>100), 2023 (>110), 2024 (105.5), 2025 (102) and 2026
    (108.8), in $bn. It is **not stated for 2016–2018, 2020 or 2021.**
  - **GSCI** publishes quantity weights for 2015–2026 but no AUM (its "Investment Support Level" is not AUM), so κ_G
    must absorb the scale. GSCI holds no ZL, ZM or COMEX copper.
  - **Roll counts.** Grains, softs and precious metals roll 4–5 times a year and livestock 6–8, not the ~12 in the
    spec's §5.
- **Gaps (IR-G):**

| # | information | gate / test | status | route |
|---|---|---|---|---|
| IR-G1 | non-CME component prices (31.5% of BCOM) | R0 | MISSING | the BCOM aggregate ER index level nearly replaces them. The drifted weight is CIM_i·P_i(t)/Σ_j CIM_j·P_j(t); the CME numerators are exact, and the denominator follows the ER level up to the non-CME roll gaps, which can be bounded (a band, not exact). Needs the principal's ruling and a source. Otherwise ICE via Databento from 2018-12 only ($24, closes) and no LME |
| IR-G2 | published BCOM single-commodity sub-index levels | R0's 5 bp test | to source | public pages; terms to check |
| IR-G3 | KE settlements | R0, C0 | MISSING, **$0 until ~10-11** | Databento statistics + definition, 2.2 GB. Needs approval |
| IR-G4 | aggressor-signed window flow, 13 roots, 2016 → 2025-02 | **C0**, R1 | MISSING (CL/NG only, via Sierra) | Databento `trades` in windows ≈ $243 (exact windows) / $471 (padded), exchange flag. Or Sierra: free, ~725 files, sign r ≈ 0.88 (HO/RB), pre-2020 coverage unverified |
| IR-G5 | settlement windows with effective dates, 11 roots before 2026-09-21 | C0, R1 | MISSING | CME settlement procedure notices (to source) |
| IR-G6 | BCOM tracking AUM, 5 years | ΔN scale | MISSING | an estimate with a band (A2's standard) |
| IR-G7 | CIT supplement | 5A.2 | not on disk; tracker line 158 wrong | free CFTC yearly zips |
| IR-G8 | designated-contract 1-minute panel | R1, C0 | raw bars on disk; builder not written | build |

**This table is the 2026-09-27 opening state, and it is SUPERSEDED.** The rulings and the "Next" list below closed it,
and the model is FROZEN (IR-A15/A16). **Checked 2026-09-30:**
- `freeze_index_reweight_2027.py --verify` passes: nothing has moved.
- The Track 2 recorder's daily task has succeeded every day (settlements 2026-09-21 → 09-29).
- The two sign-check tasks (10-05, 10-11) and the Databento pre-lapse top-up (10-09) are scheduled.
- **Nothing in this line waits on the Databento lapse.**
- **One loose end:** D636 §1 lists FC, CC (before 2026) and LME copper for the GSCI reference-day weights as inputs
  "pending the principal's approval", with a declared fallback. No amendment records a ruling, so the frozen code's
  behaviour governs. Confirm which applies before R1 runs.

- **Rulings taken, 2026-09-27.** They are recorded in
  [`INDEX_REWEIGHT_FLOW_AMENDMENTS.md`](INDEX_REWEIGHT_FLOW_AMENDMENTS.md), IR-A1–IR-A12.
  - IR-G1 → ICE from Sierra Chart and LME from Westmetall (IR-A4). The LME prices are on disk:
    `data/index_reweight/lme_westmetall_daily.csv.gz`.
  - IR-G3 → the KE jobs were ordered at $0.00 (IR-A8).
  - IR-G4 → Sierra Chart, validated per root at r ≥ 0.8 (IR-A7).
  - The freeze contingency → freeze the code and rules (IR-A10).
- **Downloads (2026-09-27):**
  - **Sierra CME: all 775 on disk (76.3 GB).** 686 cover roll-in minus 30 business days through roll-out, per
    `data/index_reweight/sierra_download_record.json`. Of the rest:
    - HG, KE, SI, ZC and ZW are 1–3 days short of the 30-day pad. That is harmless for a 20-day norm.
    - **GC and ZS, 9 each, have only ~6 days of pad before roll-in**, so the norm there needs a rule.
    - **ZL and ZM, 9 each (the Dec contract, which leads Jul–Nov), miss their roll-in period entirely**, because
      Sierra's intraday history is capped near 5 months. **C0's pre-registration must say how those rolls are
      treated:** the old-contract side only, or Databento `trades` for those windows (paid, small, needs
      approval).
  - **ICE: the Sierra daily settlements cover all 237 (IR-A13).** The intraday files are on disk too.
  - **KE:** settlements are on disk (17 files); the definitions job is still processing.
  - **ProShares NAVs:** UGL, GLL, AGQ, ZSL, UCD and CMD are recorded. Their benchmark spans are in D634 §8.
- **Gate R0 (D634) ran 2026-09-27: UNRESOLVED (proxy).** See
  [D634-RESULT](../decisions/D634-RESULT-gate-r0-unresolved-proxy-the-rebuild-is-right.md).
  - The rebuilt subindices match the published ones: 0.2–1.0 bp a month, and 99.4–100% of roll days.
  - The misses: the fund proxy's accrual (−4 to −6 bp a month); two 2020 strip holes (02-27, 06-30); and the LME
    stand-in in the 2016 aggregate.
  - **Rulings taken (IR-A14), and the logged re-run gave RESOLVED** (D634-RESULT §6). The 2020 holes were filled
    from Sierra. The rebuild meets 5 bp a month in 97–100% of months, and ΔN was unchanged. **The re-run's tracker
    (`drift_tracker_daily_rerun.csv.gz`) is the one to freeze.**
- **Next:**
  - **Settlement windows DONE (`3764e43`):** the 11 roots are MEASURED over 2015-12 → 2025-02. The documented
    window reproduces the settlement on 95–100% of days in every year (KE from 2017, ZM from 2016).
  - **C0 is PRE-REGISTERED: D635 (`e001171`).**
  - **C0 POWER DONE (`b0e992a`):** size 3.25%, power 100% from κ = 0.02; corr(Q_B, Q_G) = 0.47 (separable).
    `docs/internal/INDEX_REWEIGHT_POWER.md`.
  - **Sign-check inputs on disk:**
    - Databento `trades` for the 15 roots, 2026-09-19 → 09-25 ($0; 5 sessions);
    - Sierra files for the 24 current contracts.
  - **The C0 runner and the sign check are committed (`bef2903`).** Both steps below are SCHEDULED. Each task
    reports; neither commits or runs C0.
  1. **Scheduled for Mon 2026-10-05 08:00, task `c0-signcheck-nonenergy`:** top up the $0 trades and the Sierra
     files, then run `check_c0_sierra_sign.py --group nonenergy`.
  2. **Scheduled for Sun 2026-10-11 09:00, task `c0-signcheck-energy`:** it first checks that D626's read
     (2026-10-10) happened, then runs `--group energy`, and reports whether all 15 roots have a verdict.
  3. **The principal calls C0's one run:** `uv run python -W error::RuntimeWarning scripts/run_gate_c0.py --run`.
  - **R1–R3 are pre-registered (D636), POWER-checked and their runners committed** (`c019f34`). Each runs once
    after C0, **followed each time by `uv run python scripts/log_index_reweight_trials.py`** (IR-A16: the trials log
    and the DSR's count).
  - **FROZEN on 2026-09-27** on the principal's word (IR-A15), and re-frozen the same day after a logged path fix
    (IR-A16; only the wrapper's hash changed): `data/index_reweight/FROZEN_2027.json`, 27 code
    files, 30 inputs, 24 parameters. `uv run python scripts/freeze_index_reweight_2027.py --verify` before every run.
    C0 has not run, so κ is what the frozen `run_gate_c0.py` returns on the in-sample data (IR-A10). A code change
    from here is a logged bug fix under a NEW frozen file.
  - **The Track 2 recorder:** `scripts/record_index_reweight_2027.py`.
    - `--settlements` works: 125 post-vault settlements for 21 components, 2026-09-21 → 25. Scheduled daily.
    - CL, NG, HO and RB are skipped until 2026-10-11 (D626's sample).
    - `--cim2026` DONE (IR-A15): the 21 expired Sierra daily files were downloaded on the principal's approval
      (1.58 MB) and `track2/cim_2026.json` written from the 2026-01-07 settlements, once, on the frozen code.
    - `--forecast` REFUSES until the 2027 targets are transcribed after the announcement.

## The MACD arm's mechanism (D669, 2026-09-29)

- [x] **The MACD arm RESIZED and AMENDED (D674, 2026-09-29, the principal: "resize it, then amend", "MFFU Rapid
  150k").** One MNQ unchanged; account MFFU Rapid 150k (P3a 1.90 -> 0/yr); expectation Sharpe 0.24. BOOK_PROP and
  COMPONENTS_PROP amended. D669's second proposal was withdrawn by D670.
- [x] **The reshaping line CLOSED (D670, D673; the principal, 2026-09-29: "Close and merge then remove the
  worktree").** No plain form of the arm's behaviour carries on YM, RTY or ES. The 15:00 last-hour cut stays a
  candidate exit. **Done at the merge (2026-09-29):** `wt/after-d643` merged second and renumbered its D667 → D681
  (the diagnostic of D666) and its D673 → D682 (the compression break on YM/RTY).

## The log MACD's mechanism, mechanism first (D675, 2026-09-29)

The principal: "we now require a deterministic explanation of the underlying mechanism ... we design a signal that
fires on a mechanism of the market we can make money off." Three stages: locate (Stage 1), design on the mechanism's
own observable (Stage 2), confirm on an unread slice after a seal inventory and a power check (Stage 3).

- [x] **Stage 1 DONE: D675 RESULT.** No declared mechanism fits any root. The MACD is a clock-blind blend of known
  effects: recent moves revert overnight (D499's, under a tick); they continue into the US afternoon, strongest on NQ
  (US_CLOSE at the 100th percentile, mechanism unidentified); and on NQ, yesterday's move reverts (D495/K8). Per root
  the traded signal clears its own null only on NQ (0.976) and CL (0.997); 6E loses (0.024); on ES, YM and CL most of
  it is 2020.
- [x] **Seal inventory and power DONE (D675 §9).** No clock cell can be confirmed: 0 of 105 reach t 1.5 on the one
  clean slice (ZN/ZB/6E 2024-01 → 2025-02) even at full effect. The best is ZN's overnight reversal (t 1.37), which
  is D499's effect and has no money in it. NQ has no unread slice. CL and GC 2024-01 → 2025-02 are about to be read by
  the other session's root-aware break (D676, since run: NOT SUPPORTED). The next free number is now **685** (see the
  numbering note at the top).
- [x] **The log MACD line CLOSED (D675 §10; the principal, 2026-09-29: "Ok close it").** It includes any MACD variant
  and any Stage 2 on a §3 clock cell; no slice was spent. The clock map stays as market structure.
- [x] **DONE 2026-09-30 (the principal: "Do the house keeping"):** FINDINGS §98 and the D484 mention in its micro table now say D484's pooled pass rests on NQ and CL (D675 §2, §8.3).

## Month-end rebalancing flow (D685, 2026-09-29; the principal: "Write, build then run it please")

- [x] **D685 RESULT: MECHANISM ONLY.**
  - **Gate 1 passes:** −14.06 bp per 1-SD, NW t −3.22; the sign book is at the 99.4th percentile of its month-rotation
    null and beats the mid-month placebo (97.5th).
  - **Gate 2 fails:** the filtered MES book nets $4.06 per active day at t 1.04. That is noise and fade, not cost
    ($4.42 a round trip against a $93 average move).
  - **Against the mechanism:** the sign book lost money in each of 2019–2022; ZN's β is −0.01 (no bond leg); the next
    10 days continue (−49, t −1.97) rather than revert.
  - **Component line:** unfiltered MES net Sharpe 0.26, Sortino 0.39, ρ −0.04 with the MACD arm.
- [x] **D686 RESULT (development): no variant rescues it.** 13 projections, overlays and lags.
  - **None reaches NW t 2.** The best, O2 (the macro-day stand-aside), has a Sharpe of 0.331 at the 75.5th percentile
    of the best-of-13 null.
  - **Nothing is confirmable:** the expected t is at most 0.64 even with the vault.
  - **The fade is not liquidity:** the square-root impact factor doubled from 2013–15 to 2020–23 while the edge turned
    negative (Spearman −0.25). The flow was anticipated or offset, not diluted.
  - **Number note:** the other session committed its own D677 in the same minute (13:40). This branch merged second,
    so this record became D685 (see the numbering note at the top).
- [x] **D687 DIAG: why the mechanism fails.** The flow did not shrink, move earlier or get offset.
  - **Its price response per unit collapsed after 2018:** −15.8 / −19.7 → −5.9 bp per 0.01 of drift. This happened
    while |drift| grew and the square-root law predicted more impact.
  - **The timing part of the sign book went from +13/+16 to +0.2.**
  - **The bond leg was real in duration and faded with it:** ZB +8.6 (t 2.09) in 2010–15; ES−ZB pooled −18.0
    (t −3.27).
  - **The residual in 2019–23 sits at quarter-ends:** −14.1, t −1.54.
  - **The reading:** predictable flow is now absorbed without a price concession.
- [x] **The month-end line CLOSED** (the principal, 2026-09-29: "Ok close no need for 2024+ data").
  - D685, D686 and D687 carry closure sections; no slice was spent.
  - SCORED, NOT ENTERED in COMPONENTS_PROP.
  - Neither the anticipation line nor the forward-only quarter-end book is taken up.
- [x] **Superseded by the closure above:** the principal's calls (D685 §7):
  - record MECHANISM ONLY and do not spend 2024-01 → 2025-02 (expected t ≈ 1.1 at the measured effect; 1.65 with
    the vault);
  - enter it in COMPONENTS_PROP as SCORED, NOT ENTERED;
  - any successor explains the flat bond leg and the continuation first.

## The dealer-gamma close (D688, 2026-09-29; reopens D581's line under D582's new-fixture clause)

- [x] **D688 (formerly D681) RESULT: NOT SUPPORTED. CLOSED by the principal, 2026-09-29, with D683 and D684.**
  [Record](../decisions/D688-RESULT-not-supported-the-close-sees-a-quarter-of-the-flow.md).
  - **The run:** one run, 118 s; D581 reproduced exactly.
  - **Gate 1 fails:** β_G is +0.12 (t 1.23, the 91st percentile of the rotation null), about a quarter of the
    square-root law's size, with Y ≥ 0.5 rejected at 3.8 SE.
  - **Regimes:** short gamma +0.55 (t 1.3); long gamma 0.00.
  - **Gate 2 fails:** 235 trades, net t 0.30; one day (2020-03-13) is 134% of the net.
  - **The confirmation is not triggered,** because the unread slices are long gamma. No 2024+ data was read.
  - **D683 DIAG** ([record](../decisions/D683-DIAG-the-hedging-happens-along-the-path-not-at-the-close.md)): it was not
    too little impact.
    - The flow is 8.6% of ES's closing half-hour volume at the median, and the expected NW t at Y = 0.5 was 5.0.
    - The hedging lands along the path: long gamma deepens 5-minute mean reversion (below every rotation) and halves
      realised variance (t 12.8).
    - The close slope is the Feb–Apr 2020 crash (+0.04 without it).
    - Both books carry real information.
    - **Open idea, the principal's call:** gamma-gated intraday mean reversion on a slower bar (check the volatility
      confound first).
  - **D684 SIZING: NO-GO**
    ([record](../decisions/D684-SIZING-no-go-the-long-gamma-fade-is-far-below-cost.md)).
    - The long-gamma fade makes $0.2–0.3 gross a trade against an $8.84 bar, at 5–60 minutes.
    - D683's 5-minute gradient disappears under a same-day volatility control (addendum on D683).
    - Gamma's role now: the size term of the expected-profit filter.
  - [ ] **D689 STAGE 0: UNCONFIRMABLE ON THE CLEAN SLICE; the principal's call**
    ([record](../decisions/D689-STAGE-0-short-gamma-continuation-is-real-but-unconfirmable.md)).
    - **Survives, in-sample:**
      - the volatility control: short − long +1.48 bp within same-day RV deciles, the 98.5th percentile of the
        enumerated rotation null;
      - the crash: +$4.06 a MES trade without it (t 3.24);
      - 8 of 8 years with positive gross.
    - **The books:** full ES net Sharpe +0.51 (Sortino +0.75), ρ −0.05; MES −0.18. The |m|-scaled expected-profit
      filter fails.
    - **The premise:** 66 short-gamma sessions in 2024-01 → 2025-02 (SPX 1, ES book 101), so the expected t is 1.12,
      under 1.5.
    - **Open checks (§5):**
      - an always-long control (about half the per-trade profit looks like up-drift);
      - the effect on ES-book-only short days (the confirmation population).
    - **Then:** a joint-vault pre-registration (power about 1.7, estimated) or park it.
  - [x] **D690: the oracle filter and the accuracy assessment**
    ([design](../decisions/D690-DESIGN-the-oracle-filter-and-the-accuracy-assessment.md),
    [DIAG](../decisions/D690-DIAG-accuracy-needed-is-small-and-the-regime-gate-is-best.md)).
    - **The library:** `validation/filter_oracle.py` (tested), covering the oracle, partial oracles, confusion, AUC,
      capture and calibration.
    - **On this trade:** a Spearman of about 0.01 breaks even at full ES and about 0.03 reaches Sharpe 0.5; real
      filters reach 0.04–0.06.
    - **The regime gate is still the best** (+0.54; no model filter beats it). A size-only oracle is worth almost
      nothing, and D689's π·|m| was anti-calibrated (slope −1.7).
    - **Proposed house practice:** no filter is traded without a positive calibration slope. The next gain needs a new
      directional input.
- [x] **D688 PRE-REG committed** (`de4a4f7e`); runner `7be544a3`. The formation decisions F1–F10 were settled with
  the principal:
  - **Gamma:** SPX GEX plus the ES book (re-evaluated at the prior close), with SPX-only and ES-only beside it.
  - **Construction:** continuous; hedge flow Q = −G·r from the prior settlement to 15:30, in square-root form; the
    outcome 15:30 → 16:00.
  - **Controls and placebo:** the day's move, the LETF flow and σ; the placebo at 11:00 → 11:30 plus a clock profile.
  - **Gates:** Gate 1 (NW t ≥ 2 and above an enumerated day-rotation null; beats the placebo); Gate 2 (an
    expected-profit-filtered MES book with regime-split pass-through).
  - **Scope and evidence:** ES only; 2016–23 is a test.
  - **Step 0:** the white paper confirms the convention; the units are inferred as $ per 1%.

## Pre-lapse data sweep (2026-09-27; the Databento CME Standard subscription lapses ~2026-10-11)

- Quoted by `scripts/quote_prelapse_sweep.py` → `data/prelapse_sweep_quote.json` (`8dac850`), metadata only,
  **all USD 0.00 now, billed after the lapse.** Billable sizes (disk is smaller by the ratios in data-available.md):
  - **NQ options** (opening model S-H, O-Q2): definition 27.2 GB + statistics 247.0 GB, 2016 → 2026-09-27. Families
    resolved and counted first: NQ.OPT, QN1–QN4, QNE from 2016; the Mon–Thu dailies Q{1-4}{A-D} exist only in 2026.
    ≈ 48 GB on disk.
  - **CL/NG options** (the ledger's options OI; D619's parents): definition 60.7 GB + statistics 118.7 GB. ≈ 25 GB.
  - **Forward top-ups** from the archives' end (2026-09-11): ohlcv-1m all symbols 0.3 GB, tbbo all symbols 5.0 GB,
    statistics + definition 41 roots 0.6 GB, ES options 2.4 GB, **mbo 8 roots 81.3 GB** (≈ 28 GB, and growing ~5 GB
    a session). Best pulled as late as possible (~10-09/10-10) so they reach the lapse.
  - Free disk 201 GB.
- **The principal approved all four (2026-09-27).**
  - NQ and CL/NG options: SUBMITTED 2026-09-27 by `scripts/fetch_prelapse_options.py` (7 batch jobs, each re-quoted
    at USD 0.00 just before submission; records `data/prelapse_options_pull_jobs_{nq,energy}.json`); downloading.
  - Top-ups including MBO: SCHEDULED for Fri 2026-10-09 07:30, task `prelapse-databento-topup`
    (`scripts/fetch_prelapse_topup.py`; checks ≥ 90 GB free first, refuses any job no longer at USD 0.00).
- **Session-handoff pre-vault pull: RULED NONE** (the principal, 2026-09-28, on D651's recommendation). The
  session-handoff line is closed (D651 §6); nothing is pulled for its kill 2.

## LETF close-flow — opened 2026-09-27 (the principal: "then open LETF close-flow")

- The spec is `docs/internal/User-Doc-Deposit/LETF_CLOSE_FLOW_PREREG.md` v1.2 (read-only).
- **PRIOR READS OF THIS MECHANISM (must be ruled on before a pre-registration):**
  - **D530** (2026-09-14, closed by the principal as "avenue 3"): the LETF reset flow `L(L−1)·A·r` on ES/NQ/YM/RTY,
    2016-01-04 → 2023-12-29. Its dose-response prediction (continuation rising with |return-of-day|) FAILED:
    quintile 1 → 5 reads 47.2% → 50.6%, Q5 z ≈ 0.49; equity index hit 50.03%, z = +0.1. The closing-hour volume hump
    is real (1.10–1.48×); the direction is not.
  - **D463**: the last-30-minute intraday momentum (15:30 → 16:00, sign of return-of-day) on 2010–2023: NQ −0.01, ES
    −0.29 net Sharpe (components K2–K4).
  - **D487**: ES/NQ intraday continuation, 2016–2023: a 2018/2022 property, not a stress one.
  - **All three left 2024-01-02 onward UNREAD.** So for this line the unread slices are 2024-01-02 → 2025-02-28
    (~290 sessions), the vault (joint run) and the forward.
  - What the deposit adds beyond D530: real AUM weights, the volume normalisation and impact gate, entries at
    14:30/15:00, H3 (AUM scaling) and H4 (the 11:00 placebo). H2's |q| quintiles are close to D530's |r| quintiles
    within a year.
- **Gate 0 AUM (`data/letf/SOURCES.md`):** the eight ProShares tickers are ON DISK (the principal's all-funds file,
  2006/2009/2010 → 2025-02-28, longest gap 5 calendar days, no zero-share rows). **Direxion SPXL/SPXS: no free
  history found** (issuer page current-day only; N-PORT monthly is the candidate).
- **Already built:** ES/NQ 1-minute bars (`fut_{ES,NQ}_rth_1m`, `fut_index_sessions`), the session calendar with
  early closes and FOMC/CPI/quad-witching/quarter-end flags (D589, D585), the power module (D588). To build: the
  NQ-equivalent volume series (NQ + MNQ/10), the AUM panel and Gate 0.
- **Rulings taken 2026-09-27** (`docs/internal/LETF_CLOSE_FLOW_AMENDMENTS.md`): LETF-A1 run the deposit as
  written, D530/D463/D487 disclosed in every result; LETF-A2 in-sample 2016-01 → 2025-02-28 (A10); LETF-A3 Direxion
  from N-PORT (2019-Q3 on: quarter-end net assets plus monthly flows and returns, CIK 1424958), band measured on the
  ProShares funds, else the principal sources it; LETF-A4 Q1/Q2 defaults (proposed, never ruled; **moot**: Gate 1
  killed the line before Phase 6, and D639 §11 had already fixed Q2).
- **Phase 1 / Gate 0 DONE (D637, 2026-09-27):** `scripts/build_letf_aum.py` → `data/letf/letf_aum_daily.csv.gz`,
  `gate0.json`. **NQ set PASSES** (four ProShares funds, 2016-01 → 2025-02, 22 N-PORT spot checks each within
  0.011%). **ES set:** ProShares four PASS; Direxion (39% of the S&P flow) estimated from N-PORT 2019-10 → 2025-02
  with a measured band (impact I moved by 2.1% at p95), failing the proposed 1% bar that the method also fails on
  known-good funds; **Direxion absent 2016-01 → 2019-10.** Stop-and-report for ES.
- **Ruled 2026-09-27 (LETF-A5, A6):** Direxion's 2019-10+ estimate accepted; the pre-2019 filings transcribed
  (`scripts/fetch_direxion_pre2019.py` → `data/letf/direxion_pre2019_filings.csv`, 398 cited rows, all re-verified).
  **Gate 0 PASSES for all ten funds on every row, 2016-01 → 2025-02; ES is complete from 2016-01** (D637 addendum).
  Caveat: Direxion 2017-11 → 2019-07 has only quarterly anchors (wider band, p95 16% at the fund).
- **NQ Phase 2 DONE (D638):** 2,285 usable sessions, every bar the model reads present, t−1 priced in one contract
  on every day (36 rolls via `fut_index_anchor_bars`), MNQ volume built (`fut_micro_day_volume`). CME's settlement
  is NOT the 16:00 price (equal on 2.4% of days).
- **ES Phase 2 DONE** (`data/letf/phase2_ES_qa.json`): 2,285 usable sessions, every model bar present, 36 rolls
  priced in one contract; MES 1–7% of the ES-equivalent volume.
- **Phase 3 DONE:** `src/backtest_framework/letf/model.py` (section 4's algebra) and `tests/unit/test_letf_model.py`
  (the deposit's nine tests, all claimed: crosswalk 88 of 146).
- **D639 PRE-REG committed alone** (`e95c0a9`).
- **POWER DONE** (`scripts/power_letf.py` → `data/letf/power.json`, `docs/results/LETF_CLOSE_FLOW_POWER.md`):
  - **Every primary cell is UNDERPOWERED by D639's default** (MDE vs the mean cost).
  - **NQ:** about 950 active days per cell, MDE (t = 2) 3.1–4.7 bp against a 1.6 bp cost. But against the model's
    own predicted impact (about 10 bp) it is powered even at Holm 80% (5.4–8.3 bp).
  - **ES:** 60–69 active days per cell and **none in 2024+**. MDE 27–38 bp, above even its own 15 bp prediction.
  - **Open for the principal before the runner:** whether to add the model's-own-prediction comparison as a
    pre-registered reading (LETF-A7).
- **LETF-A7** (the model's-own-prediction reading) and **LETF-A8** (H3's slope corrected) committed before the runner.
- **RUN ONCE 2026-09-27 → KILLED AT GATE 1 (D640; `docs/results/LETF_CLOSE_FLOW_REPORT.md`).**
  - NQ 14:30 and 15:00 pass H1, but the 11:00 placebo is significant on NQ (t 2.08).
  - The unread 2024+ slice is flat in every NQ cell. There is no AUM scaling. ES never passes.
  - Component lines are entered in `COMPONENTS_PROP.md` as scored, not entered. NQ 15:30 is K2 (ρ 0.83).
  - **The LETF line stops here.** Phases 6–7 do not run; the deposit's v2 overlays have no v1 effect to build on.
- The runner (committed before its run): `scripts/run_letf_close_flow.py`.
  - `--selftest` shows 7 checks firing (on synthetic prices).
  - `--dry-run` substitutes synthetic prices and reads only the bars' calendar. Every path ran (6 cells, 71 trials,
    5.2 min).
  - **It ran once on 2026-09-27 (D640, above)** and wrote `data/letf/letf_close_flow_signal.json` and
    `data/letf/trials.csv`. Phases 6–7 did not run.

## Shock classifier — opened 2026-09-27 (the principal: "open the shock classifier")

- **Spec:** `docs/internal/User-Doc-Deposit/SHOCK_CLASSIFIER_PREREG.md` v1.2 (read-only).
- **Amendments:** `docs/internal/SHOCK_CLASSIFIER_AMENDMENTS.md`: SC-A1 (the A10 split; D592 paths), plus the opening
  facts.
- **Prior reads, disclosed:** D528 (1-minute spikes, reversion 4–8× too small), D499, D526.
- **Data:**
  - bars ✓ (`fut_day1m`, 100% on usable sessions);
  - calendar ✓ (D585, all five events 2016 → 2026);
  - **GC window 08:25: pre-09:00 bars to build** from the on-disk archive (GC, SI, 6E, ZN);
  - **no in-sample aggressor trades** (Q3).
- **Ruled (SC-A2..A6):**
  - run as written, with the prior reads disclosed and the unconditional baseline beside each class;
  - bars-only v1;
  - the GC-complex pre-09:00 bars;
  - the MCL cost line throughout; Q1/Q2 as for LETF;
  - Gate 0 read on usable sessions.
- **Phase 1 / GATE 0 PASSED** (`scripts/shock_gate0.py` → `data/shock/gate0.json`):
  - 2,282 usable sessions, 2016-01 → 2025-02;
  - traded markets 99.99–100%; peers priced within 5 minutes on ≥ 99.99% of minutes (BZ literal 96.3%, reported);
  - calendar complete; roll days listed;
  - outage days 2020-02-27, 2020-02-28 and 2020-06-30 excluded.
- **Phase 2 DONE (D641):**
  - built: `src/backtest_framework/shock/model.py` and the 13 deposit tests (all pass; crosswalk shock 13/13);
  - counts: `scripts/build_shock_phase2.py` → `data/shock/phase2_shocks.csv.gz` and `phase2_counts.json` (4.4 min);
  - **almost every z = 4 shock is INFO** (C median ≈ 1). **LIQ: NQ 85, ES 51, CL 40, GC 304 over nine years**,
    against ~1,800 planned. 317–387 shocks a year per market (planned ~150).
  - SC-A7 (NGSR diagnostic; unscheduled FOMC counts) and SC-A8 (a zero σ_tod cannot detect) are PROPOSED.
- **POWER DONE** (`scripts/power_shock.py` → `data/shock/power.json`, `docs/results/SHOCK_CLASSIFIER_POWER.md`), H1's
  INFO-vs-LIQ divergence at the 30-minute exit against the micro round-trip cost:
  - **NQ, ES and CL are UNDERPOWERED** (MDE at t = 2: 8.9 / 9.0 / 25.4 bp against costs of 2.4 / 3.3 / 10.7 bp; LIQ n
    85 / 51 / 40). An H1 null there is inconclusive (§7A).
  - **GC is powered at t = 2** (MDE 2.9 bp against a 4.5 bp cost; LIQ n 304), but not quite at Holm 80% (4.9 bp).
  - Pooled MDE 0.094σ against the plan's 0.06σ.
- SC-A7 and SC-A8 RULED (`31e2af6`). **D642 PRE-REG** (`0768da5`), runner `scripts/run_shock_signal.py` (`906c501`,
  audit fix `8c2a67f`).
- **CLOSED at GATE 1, 2026-09-28 (D643):** H1 passes nowhere.
  - GC (powered) is a clean null: Δ +0.28 bp, t 0.21, 95% interval −2.4 to +3.0 against a 4.5 bp cost.
  - NQ/ES/CL are inconclusive as POWER said, and their LIQ class is a 2016–2020 label carried by the 2020 crash.
  - Neither class differs from the unconditional shock; H3 and H4 fail everywhere.
  - Component lines are all negative or empty (COMPONENTS_PROP.md). 96 trials in `data/shock/trials.csv`.
  - Report: `docs/results/SHOCK_CLASSIFIER_REPORT.md`.
- Not answered: a flow-signed classifier (aggressor data never in-sample, SC-A3). Nothing here argues for buying it.

## Opening agent-state model — opened 2026-09-28 (the principal: "Open it")

- **Spec:** `docs/internal/User-Doc-Deposit/OPENING_AGENT_STATE_PREREG.md` v1.1 (read-only; untracked in the main
  checkout).
- **Amendments:** `docs/internal/OPENING_AGENT_STATE_AMENDMENTS.md`:
  - OA-A1: the A10 split and D592's paths; H-O2 already holds registry slot 7.
  - The opening facts.
  - **OA-A2–A5 ruled 2026-09-28:**
    - prior reads run as written, disclosed;
    - A7 from Sierra Chart tick data, one contract at a time;
    - A6 from Alpha Vantage 1-minute SPY/QQQ;
    - costs: D508 + one tick, checked forward.
- **CLOSED 2026-09-29 by the principal.** What ran:
  - Gate O0 passed (D644);
  - stage S-A (D646) passed H-O1 by the letter and failed H-O2;
  - Phases 4–5 (D658) retained no agent, and Gate O1 failed;
  - v2 (D652/D659) passed its own kill, but its vault power was 5–6.5 %.
  - **v2 was closed without its vault look ("Ok close both of those"). v1 was closed with programme slot 7 released
    ("close opening model v1"; "Release it").** The line has no vault look left.
  - Diagnostics: D647, D660, D661. Findings: FINDINGS §87 and §92. Component lines: COMPONENTS_PROP (scored, not
    entered).
- The branch `wt/after-d643` was merged to main and pushed (`6506cc26`), and the worktree was removed. Its
  gitignored fixtures, `fut_opening_globex_1m*.csv.gz`, are in the main checkout.

## Settlement flow ledger — the full study, one problem at a time (opened 2026-09-24)

**The standard, the principal's, 2026-09-24:**
- The starting position: *"I dont want a partial test, I dont want any reason to handwave the
  results or doubt them."* So no Stage A-lite, no partial Gate 0, and no forward-only stand-in for a
  backtest stage.
- Relaxed the same day for inputs that cannot be observed for free: an estimate is acceptable if it
  is *"directionally correct"*. It must carry a measured band, smaller size and larger error bars.
  The binding form is the amendments A1–A5 in
  [`SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md`](SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md), which sit beside
  the read-only deposit.
- The document is `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`. The
  infrastructure already built is in [`DEPOSIT_INFRASTRUCTURE_TRACKER.md`](DEPOSIT_INFRASTRUCTURE_TRACKER.md).

**Measured 2026-09-24, from free Databento metadata calls; nothing spent:**
- CME market-by-order history begins **2017-05-21**, so Stage H cannot start earlier from any source.
- Databento's consolidated equity NBBO begins in **2023**. The listing venue, NYSE Arca, where all six
  ETFs list, begins **2018-05-01**. A true NBBO from 2016 needs NYSE TAQ from another vendor.
- Aggressor-signed CL/NG trades are on disk only for 2025-09 → 2026-09, which is inside the vault.

**DATA GAPS REGISTER (2026-09-24; the principal can't buy more data, and will source some items).**
"Weakened" means a free substitute exists, as an estimate or a proxy. "Missing" means there is no free
source.

| # | information | stage / test | status | free substitute or note |
|---|---|---|---|---|
| G1 | aggressor side of CL/NG trades, 2017-05 → 2025-09-24 | **A (the kill test)**, B, I, H5 | **MISSING: the estimate FAILED (D624 RESULT, 2026-09-25)** | One-second bars cannot sign settlement-window flow (sibling r −0.22 to −0.03 against the 0.8 bar). **The principal will source it.** The cheapest real route is window-only `trades` (14:28–14:30 plus 11:50–12:20 ET): ~$108 in-sample, ~$7.50 vault |
| G2 | aggressor side of TAS trades | D | **SOLVED from 2020-02-10 (Sierra Chart, the principal's choice, 2026-09-26)** | 41 held NG TAS months on disk, in-sample and vault (`sierra_tas_download.py` → `data/sierra_tas_download_record.json`). **Sierra's TAS sides ARE the exchange flag:** on the HO/RB sibling TAS, r 0.9998–0.9999, sign agreement 99.8–100%, volume ratio 1.00 (`check_sierra_tas_aggressor.py` → `data/sierra_tas_aggressor_check.json`); under 0.3% of TAS volume has no aggressor. **Sierra has no NG TAS before 2020-02-10** ("historical data file not available": NGTN17 → NGTF20, 16 months). The gap 2017-05-21 → 2020-02-10 is quoted at $0.29 (11.2 MB) as Databento NGT trades with the exchange flag, and is the principal's to approve. The one-second estimate FAILED (D625) |
| G3 | ETF bid/ask (NBBO) quotes before 2023-03-28 | C2 premium | WEAKENED | see the ETF-premium options in the reply of 2026-09-24; the principal is choosing |
| G4 | ETF trades with aggressor side | C1 features, C3 H11a | WEAKENED | estimated from Alpha Vantage 1-minute bars; thin funds have sparse minutes |
| G5 | CL/NG order book (depth) history | **H** | MISSING | only the last month is free. **Principal will source it** |
| G6 | daily futures/swap split and months held | A (f_fut), E, F | WEAKENED | estimated with a band (item 1). Proven where it can be |
| G7 | UNG/USO daily shares outstanding | C1 creations | WEAKENED | exact month-ends and monthly creation totals; daily figures interpolated |
| G8 | USO's weights by contract month, 2020-04 → 2023 | F rolls, P1 held month | WEAKENED | documented allocations and the ladder estimate (±2.7 pp) |
| G9 | each fund's execution time of day (settlement, TAS or earlier) | A (where the flow lands), D | MISSING | the filings are silent (item 9). Not for sale |
| G10 | whether the funds use TAS (Q2, D4) | D, F (P6 split) | MISSING | the filings are silent |
| G11 | 10 other fund facts (D619) | several | MISSING / to source | item 9 |
| G12 | social-media archives (Q12) | C3 social part | MISSING | **kept OPEN: the principal will source it** |
| G13 | hourly Wikipedia views | C3 | FREE but ~2.5 TB | daily views under D621's amendment, or the full download |
| G14 | swap dissemination history (DTCC) | E netting, H15 | **FREE, partial (checked 2026-09-25)** | DTCC's public daily cumulative commodity files, no files downloaded yet. See the note below the table |
| G15 | non-US products (BetaPro, WisdomTree): NAV, units, leverage, restrikes | G | **PARTIAL (checked 2026-09-25)** | See the note below the table |
| G16 | official intraday NAV (IIV) history | validation only | MISSING | not needed: the rebuilt iNAV passes Gate 0b |
| G17 | vault trades with aggressor side, 2025-03-01 → 2025-09-24 | the vault look | WEAKENED | the same one-second estimate, which keeps the method consistent |
| G18 | CL 2020-04-01 → 09-16 | all CL stages | EXCLUDED | A1 |
| G19 | USO roll days 2017 → 2020-04 | F | **PROVEN 2026-09-25** | `check_uso_monthly_rolls.py`: exact NAV÷shares 0.81 bp against 3.11, sign test 33–5 (p 2e-6), both controls fire; UNG's known answer re-identified |
| G20 | the item-1 estimates run only to 2023-12 | A–F | **Stage A's part DONE 2026-09-25** | See the note below the table. UNG/USO month-ends, AUM and USO weights past 2023 are still to extend; Stage A doesn't need them |

**G14, the detail.** DTCC's public daily cumulative commodity files are free.
- `…/slices/CUMULATIVE_COMMODITIES_YYYY_MM_DD.zip` returns 200 from 2013-06 to 2020-11; `…/cftc/eod/…` from
  2020-11 onward.
- The whole 2017 → 2026 span is ~0.3–0.5 GB.
- It covers DTCC-reported swaps only. ICE Trade Vault needs its terms accepted, and CME's SDR blocks scripts.

**G15, the detail.**
- BetaPro (betapro.ca) has free daily NAV back to 2008, embedded in each product page. Units outstanding and
  leverage are current values only. The leverage changes are dated from press releases: HOU/HOD went to 1x on
  2020-04-22, to 1.5x on 2020-11-10 and back to 2x on 2021-01-20; HNU/HND changed index on 2020-08-27.
- WisdomTree's NAV history is behind an investor-type and terms dialog. Its restrike history is public only
  from 2024-08 (GlobeNewswire), with earlier events likely in LSE RNS. The ISINs changed, so series need
  chaining.
- FX is free: the Bank of Canada Valet API, the ECB data API and the Bank of England database.

**G20, the detail.** Both extensions run under `--seal a6` (`reserved_from="2025-03-01"`), and both original
outputs stay byte-identical.
- **f_fut, to 2025-02-28** (`estimate_fut_share.py --seal a6`):
  - BOIL, KOLD and SCO are proven through 2024; UCO is interpolated through 2024.
  - January–February 2025 are carried from 2024-12-31, which was filed 2025-02-28.
  - h is now 0.162 (70 quarter-ends; it was 0.151).
  - UCO's 2024-Q2 is newly flagged DISFAVOURED.
- **NG contract counts** (`check_ng_contract_counts.py --seal a6`): reading C matches 57 of 57 futures-only
  quarter-ends, a maximum error of 0.13%.
| G21 | live feeds for Tracks 2 and 3 | forward | COSTS | CME $199/month; ETF live quotes not checked |

**Taken one at a time, in this order.** `[>]` means in progress. Each item names who owns it.

- **1 and 2 are CLOSED (2026-09-24).** Their records are in PICKUP.md, "SETTLEMENT LEDGER, ITEMS 1
  AND 2". The amendments A1–A6 are in `SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md`.
  - **The seal is the deposit's vault (A6).** In-sample runs to 2025-02-28, and every read uses
    `reserved_from="2025-03-01"`.
  - Gate 0b passes on 2024-01 → 2025-02 for all four ProShares funds (1f).
  - **Carried forward to item 11:** extend `estimate_fut_share.py` and the USCF estimates from
    2023-12 to 2025-02 under the new cut. The 2023-12-31 schedules are now readable.
  - Carried forward to item 9: the execution time of day.
- **3. The sample start. CLOSED 2026-09-24 (amendment A7, the principal's "choice one").**
  - The in-sample is 2017-05-22 → 2025-02-28: NG 1,955 business days, CL 1,839.
  - C2 and C3's ETF-volume test run on a declared 2018-05-01 sub-sample, on Arca's best bid and
    offer.
  - Before C2 runs, Arca is checked against the NBBO on 2023-03 → 2025-02.
- [ ] **4. ETF quote history for the premium in Stage C2** (Claude to price, principal to approve;
      deposit Q8). A true NBBO means NYSE TAQ, not yet priced. The Arca-only option (bbo-1m plus
      trades, 2018-05 → 2023) costs **$11.10**, but a listing venue's quote is not the NBBO the
      document specifies.
- [ ] **5. UNG and USO daily shares for creations** (Claude; Stage C1).
      - **Now in hand (item 1):**
        - exact month-end NAV and shares, 2017–2023, from the monthly statements;
        - a daily AUM estimate with shares linear between month-ends, band −12% to +18%.
      - **Still missing:** a DAILY shares count, which C1's creation flow differences. The
        interpolated series must not be differenced for flow.
      - **What C1 can use:**
        - the monthly shares_added and shares_withdrawn (exact, but month totals);
        - or a free daily source, not yet found. USCF's history endpoint needs its site API key,
          which is not used.
      - This does not affect P1: at L = +1, P1 is zero.
- [>] **4 + 6. RE-QUOTED 2026-09-24 under A6 and A7** by `scripts/quote_ledger_pulls.py`
      (`data/ledger_pull_quote.json`). Metadata calls only; nothing was submitted.
      - **In-sample:**
        - ETF Arca best bid/offer (1-minute) plus trades, 2018-05 → 2025-02: $14.38;
        - consolidated best bid/offer for the Arca check, 2023-03-28 → 2025-02: $0.54;
        - TAS trades: $2.67;
        - CL/NG trades, whole days $1,024.23, or WINDOWED (13:30–14:45 plus 10:30–12:30 ET)
          about $397;
        - CL/NG order book, whole days $7,232.23, or WINDOWED (13:30–14:35 ET) about $916.
      - **Vault, bought only for the one look:** Arca $9.01, consolidated $0.47, trades windowed
        about $28, TAS $0.23, order book windowed about $231.
      - **Why the subscription doesn't cover it** (Databento's pricing page, checked 2026-09-24, and
        confirmed by quotes):
        - CME Standard ($199/month) includes the full history for OHLCV, definitions, statistics
          and status.
        - It includes only the **last 12 months** for trades, TBBO and BBO: $0 from 2025-09-25,
          and billed before that.
        - It includes only the **last month** for MBO and MBP-10: $0 from 2026-08-25, and $110
          for July 2026.
        - Full trade history needs Plus ($1,750/month, annual contract). Full MBO history needs
          Unlimited ($4,500/month, annual).
        - NYSE Arca is equities and isn't in the CME plan at all.
        - The vault's trades from 2025-09-11 are already on disk: `tbbo`, every instrument.
      - **THE PRINCIPAL CANNOT BUY MORE DATA (2026-09-24). Free route approved ("go for the free
        data pulls"):**
        - Databento `ohlcv-1s` for CL, NG, CLT and NGT, 2017-05-21 → 2026-09-19, $0 under the
          subscription. Signed flow will be ESTIMATED from these bars.
        - Databento `trades` after the vault, 2026-09-19 →, free (last 12 months). This is the
          ground truth for validating the estimate, outside both the in-sample and the vault.
          **Top it up before the subscription lapses (~2026-10-11).**
        - Alpha Vantage 1-minute bars for the six ETFs, 2017-05 → 2026-09, on the principal's paid
          key. They stand in for the NBBO quotes and signed ETF trades.
        - Script: `scripts/fetch_ledger_free.py`. Job record: `data/ledger_free_pull_jobs.json`.
        - **ON DISK 2026-09-24, every job billed $0.00:**
          - `ohlcv-1s` CL, 2.20 GB, and NG, 1.09 GB, compressed;
          - `ohlcv-1s` TAS, 0.02 GB;
          - post-vault `trades` 2026-09-19 → 09-23, 0.03 GB;
          - all under `data/raw/databento/<job id>/`.
          - Alpha Vantage: 678 slices, no failures, under `data/raw/alphavantage/1min/`. Regular-hours
            minutes with a bar: USO 99%, UNG 95%, UCO 94%, SCO 91%, BOIL 77%, KOLD 67%.
      - **DECIDED 2026-09-24 (principal):**
        - **The Stage A bar:** Stage A's kill test may run on the one-second estimate of signed flow
          only if, per root, the day-level correlation between estimated and true signed flow in
          the settlement window is **≥ 0.8**.
          - It is measured on the post-vault true trades, topped up before ~2026-10-11.
          - Below 0.8, the principal sources the real data.
          - This bar is fixed before any validation number is computed.
        - **The ETF premium:** Alpha Vantage 1-minute bars, time-averaged, anchored on the exact
          daily closing premium. **IEX's free historical quotes** measure the trade-price bias on a
          sample of days. The principal accepts IEX's terms for this use. The file names and sizes
          are stated before downloading.
          - **DONE 2026-09-25.** IEX TOPS on 10 days, 2018-06-13 → 2024-07-17: 24.3 GB streamed = listed on every
            day, and every packet's message count checked. Filtered to the six ETFs under `data/raw/iex/`. Record:
            `data/ledger_iex_sample_pull.json`.
          - Bias check (`scripts/check_etf_premium_bias.py` → `data/ledger_etf_premium_bias_check.json`):
            - Alpha Vantage bars are stamped at the minute's START (exact matches 25.7% against 10.3%).
            - The close's mean bias against the mid is below 1.3 bp for every ETF, and below 0.5 bp wherever
              the sample gives an SE under 1 bp (USO +0.06 ± 0.11; UNG +0.04 ± 0.16). Per-minute noise has an sd of
              3–10 bp.
            - The primary measure uses one-tick IEX minutes only, where IEX's quote is the national best. That
              covers USO 23%, UNG 15%, SCO 13%, BOIL 6%, and KOLD and UCO under 1%, which rest on the ≤ 3-tick
              sample.
            - **So the close stands in for the mid in a time-averaged premium.**
      - **D624 RESULT (2026-09-25): the siblings do NOT agree.**
        - E2 was chosen at a first-half mean r of 0.33. On the second half it scored r −0.03 (HO) and
          −0.22 (RB).
        - **So neither CL nor NG runs Stage A on the estimate.**
        - The NG/CL gate phase is moot for the decision. The free top-up is SCHEDULED for Sat 2026-10-10 08:00 (task `d624-ng-cl-free-topup`; it also reads D625), as
          a record only, and it is the principal's call.
        - Record: `docs/decisions/D624-RESULT-one-second-bars-cannot-carry-settlement-window-flow.md`.
      - **The Stage A validation, as planned** (pre-registration committed `6e1bfa4`, 2026-09-24).
        Runner `scripts/validate_flow_estimate.py`, which passes its selftest.
        - **Sibling phase (HO/RB):** runs when the free sibling pull lands
          (`data/ledger_sibling_pull_jobs.json`).
        - **NG/CL gate:** read ONCE, after the top-up. **Top-up scheduled Sat 2026-10-10 08:00 (15 sessions incl. Fri 10-09):** free `trades` and
          `ohlcv-1s` for CL/NG/CLT/NGT from 2026-09-19. Its job record must be
          `data/ledger_topup_pull_jobs.json`, with labels `topup-trades` and `topup-ohlcv1s`.
        - **Outcomes:** PASS ≥ 0.8; UNRESOLVED near miss 0.70–0.80; FAIL < 0.70; UNRESOLVED below 15
          sessions. The siblings must agree.
      - **A8 WRITTEN 2026-09-25** (it replaces the held draft):
        - **Stage A's H1 becomes H1a:** does the predicted flow's SIZE explain abnormal window volume
          (free one-second bars, exact), with controls for |return|, activity and calendar flags?
          - It must beat an 11:50–12:20 placebo and a day shuffle.
          - τ is the earliest-pass time. TAS volume is reported beside it.
        - **Direction rests on H2.**
        - C2 runs on Alpha Vantage bars.
        - Stage H is forward-only.
        - Stage B, Stage I, H8a and H9 are blocked until real signed flow exists.
        - **Option 2, done 2026-09-25:** D625 did not pass, because its control fired on a base-rate
          effect. Post hoc, the TAS level reads backwards (κ +0.33 to +0.49, reversed sign).
          - **D626** (committed `9ee8142`) tests the reversed sign on data no one has read: pooled κ ≥ 0.2
            over CL, NG, HO and RB, with CL and NG each > 0.
          - Runner `scripts/validate_tas_sign.py`, uncommitted until its result.
          - **Read once by the scheduled task on Sat 2026-10-10.** A pass writes H1b, after its own
            pre-registration.
        - **H1a's inputs, BUILT 2026-09-25 (uncommitted), in-sample 2017-05-22 → 2025-02-28 under A6:**
          - Step 1: f_fut and the NG contract counts to 2025-02 (`estimate_fut_share.py --seal a6`,
            `check_ng_contract_counts.py --seal a6`).
          - Step 2: calendar flags, `scripts/build_ledger_calendar.py` → `data/ledger_calendar_flags.csv`
            (1,957 days per root). Window-volume panel, `scripts/build_window_volume_panel.py` →
            `data/ledger_window_volume_daily.csv.gz` + summary; `--check` reproduces byte for byte.
            - Known answer: window volume = the 1-minute fixture's 14:28 and 14:29 bars on all 1,966 front
              days per root, exactly (CL 12,661,012; NG 7,487,344 contracts).
            - The window is a median 3.4% (CL) and 5.9% (NG) of the 09:30–14:30 volume, against 0.67% if
              spread evenly.
            - The panel also has 51 CME holiday sessions per root, with no settlement; H1a joins on the
              calendar, so they drop out. 2020-02-28 is a Databento gap (NYMEX at about 4% of a normal
              day's volume in both bar fixtures; ES complete). It is the same event as the EIA-filled
              settlement hole, so it drops from H1a.
          - Step 3: P1 at 11:30/13:50/14:00/14:10/14:28, `scripts/build_predicted_flow_panel.py` →
            `data/ledger_predicted_flow_{daily,contracts}.csv.gz` + summary. `--check` reproduces byte for
            byte.
            - Holdings are Gate 0b's, imported, not re-derived. The ratio at the settlement equals Gate 0b's
              `index_returns` bit for bit on 3,708 days per root.
            - Q equals `ledger.flows.q1_rebalance` on every single-component row. It uses f_pit[t−1] and
              AUM[t−1], and carries q_lo/q_hi at f_lo/f_hi.
            - The sign audit raises.
            - Median |Q| was 2–3% of the traded contract's window volume in 2017–19, then 14–74% from 2020,
              and about 100% for NG in 2023. That is AUM growth, which the within-year shuffle controls.
            - **CL era B has no single traded contract:** the three Balanced WTI components each carry
              about ⅓ (the largest has a median of 34.4%).
          - **DECIDED 2026-09-25 (principal):** (1) H1a's dependent is the window volume SUMMED over the held
            contracts, for every root and era, with the largest-share contract reported beside it. (2) τ's
            §7.2 gate uses FULL-SIZE CL and NG on the repo's default cost line: CL $21.46 (D508 effective), NG
            $16.00 (the one-tick convention). The micro-size τ is reported beside it.
          - **Correction:** A4's primary f reading is f_est, not f_pit. The panel now stores Q at f = 1 per fund
            plus f_est, f_pit, f_lo, f_hi and σ_q (h = 0.162; DISFAVOURED quarters at h), so the runner forms any
            reading, or A4's draws, exactly.
          - **The §7.2 gate and τ\*, BUILT:**
            - V_d uses the new `vol_ses` (whole-session screen volume, added to the window panel; the old columns
              are unchanged). Screen volume is 64–76% of cleared on the front month and 19–39% on the held months:
              spread legs, TAS and blocks make up the rest.
            - Evaluable on 1,936 days per root. It signals on CL 798 and NG 1,028 days, mostly first at 13:50.
            - **The binding criterion is |I| ≥ 3 × cost, and it tracks AUM:** CL passes 7–12% of days in
              2017–19 and 91% in 2022; NG 8–13% in 2017–19 and 89–98% from 2022. SNR ≥ 1.5 passes 73–79%.
            - **Note for the pre-registration:** D5 treats BOIL's and KOLD's (and UCO's and SCO's) errors as
              independent. They are perfectly correlated through r, so SNR is inflated by a factor from 1 to √2
              (measured: the maximum departure is exactly √2 − 1).
        - **POWER, BUILT 2026-09-25** (`scripts/ledger_power_h1a.py` → `docs/internal/SETTLEMENT_FLOW_LEDGER_POWER.md` +
          `data/ledger_power_h1a.json`; `--check` reproduces).
          - Noise comes from the PRE-SAMPLE (the principal): front-month window volume 2015-06-29 → 2017-05-19, 465 days
            (the 1-minute fixture's day session is absent 2011–14). No in-sample vol_win is read, and a guard raises
            if it is.
          - n = 1,819 (CL, A1 transition excluded) and 1,936 (NG). At the plausible β = 0.25 (a quarter of predicted
            P1 lands in the window), power is CL 0.92 HC1 / 0.85 Newey-West and NG 1.00. NG detects β = 0.1 at 98%.
            Recovery within ±0.15: CL 94%, NG 100%. CL is an upper bound: A4's imputation is not simulated.
          - **FINDING: A8's day shuffle is anti-conservative.** The null's p95 of t is 1.90–2.04. The within-year shuffle
            gives 0.94–1.43, because permuting days destroys the autocorrelation of |Q| (AUM) and of the noise
            (AC(1) 0.2). 13–19% of null datasets beat it. HC1's size is 4.4–5.5% against a nominal 2.3%; Newey-West's
            is 1.4–2.8%. So t ≥ 2 binds, and the shuffle adds nothing.
          - **RESOLVED by A9 (the principal, 2026-09-25):** residualise |Q| on the controls, then rotate it within
            instrument-year (offsets ≥ 20 days). Calibrated: 4–7% of null datasets beat their own p95, and the
            combined gate rejects 0–2%. Power at β = 0.25 (kept): CL 0.87, NG 1.00. A9 also records the summed
            dependent, the full-size cost line and the Newey-West report.
        - **D627: pre-registration `505d83b`, runner `46e317d`, RESULT `17c6867` → FAIL on BOTH roots, with NEGATIVE slopes** (CL β −0.74, t −4.12; NG β −0.10, t −3.07). **The premise is KILLED under A8's kill row.** POST HOC: the dependent drifts (A_t > 0 on 74–77% of days), and NG's TAS volume rises with |Q| (t 3.9 with year FE).
        - **OPTION D (the principal, 2026-09-25): diagnose first, then decide.** `scripts/explore_h1a_lifecycle.py` is EXPLORATORY: it compares each contract with the previous 6 months' contracts at the same days-to-expiry, then refits the window and TAS lines. **The vault rule, committed before the run:** a line qualifies if β > 0 and its vault power ≥ 0.80 at HALF its exploratory effect (it needs t ≈ 12.7 with year FE, over 390 vault days). If no line qualifies → STOP → write-up, and the vault stays unread.
        - **D628 (2026-09-25): NO LINE QUALIFIES → the settlement flow ledger STOPS, and the vault stays unread.** The life-cycle correction leaves CL's window slope negative (t −3.97, and the placebo too) and NG's window flat. NG's TAS line is the strongest (t 6.9 with year FE) but only ties the rotation p95 (6.93), and its vault power at half effect is 0.34. The lead carried forward: NG TAS volume against predicted rebalance, testable only on forward-recorded data. **Next:** the programme write-up.
        - **SIGNED FLOW, A POSSIBLE REOPEN (2026-09-26): Sierra Chart's historical tick data carries the exchange's aggressor side.** The principal installed Sierra Chart (trial to 2026-10-17, then **Package 3, Base Standard, paid for 12 months on 2026-09-26: usage runs to 2027-10-24**). It is driven from here by `scripts/sierra_ui.py` (Win32 window messages; refuses anything trade-related) and its UDP port 22903 (opens charts). Its DTC API excludes CME.
          - **Known answer on the sibling year** (`scripts/check_sierra_aggressor.py` → `data/sierra_aggressor_check_{ho,rb}.json`): window total volume equals Databento's exactly. Net flow r = 0.877 (HO, 686 sessions) and 0.875 (RB, 694); sign agreement 80%. B/A match the exchange flag exactly; the error is the ~29% of window volume with NO aggressor (spread legs), which Sierra Chart signs by its own rule and marks with no field (tested). **Both siblings clear the principal's r ≥ 0.8 bar (2026-09-24).** It fails the stricter "is it the exchange flag" test (r ≥ 0.99).
          - **Still to check:** CL/NG against true trades, only AFTER D626's one read on 2026-10-10 (the post-vault CL/NG trades are its sample).
          - **Bulk download DONE (2026-09-26):** all 125 held contracts (77 CL, 48 NG; 19.5 + 4.3 GB) through `scripts/sierra_bulk_download.py`. `data/sierra_ledger_download_record.json` holds each file's first/last timestamp only; every file ends on its contract's last trading day (the `cut_short` check). Sierra Chart serves about 5 months before expiry whatever the depth setting, so **NG is fully covered, and so are CL's 837 era-A days. Every CL day from late 2020 on (1,119 days) lacks at least one held June/Dec contract**: CLM21–CLM25 and CLZ21–CLZ25, 1,828 of 4,327 CL held contract-days. Two network faults forced re-queues. The drops are logged as "complete", so `cut_short` must pass before any read.
          - **The principal (2026-09-26): score only the covered contracts.** The inputs are built:
            - `scripts/build_signed_window_panel.py` → `data/ledger_signed_window_daily.csv.gz`. Sierra's window volume agrees with Databento's within 1% on 99.2% (CL) and 98.5% (NG) of covered contract-days. The vault is never decoded.
            - POWER (`scripts/ledger_power_signed_h1.py`, `SETTLEMENT_FLOW_LEDGER_POWER_SIGNED.md`, pre-sample 2015-07 → 2017-05): NG power 1.00 at β 0.25; CL 0.29, underpowered.
          - **D629 (2026-09-26): NG PASSES (provisional), CL is INCONCLUSIVE.**
            - NG: β 0.061 ± 0.015, t 4.21, placebo −1.41, rotation p95 1.84 ± 0.07.
            - CL: Rubin t 1.79; β above 0.76 is excluded.
            - POST HOC: NG's pass exists only with the return control. Without it, window flow runs against the funds (t −7.98). In the top fund-size tercile β is 0.008 ± 0.02, so the pass does not look like a proportional footprint.
          - **Next:**
            1. **BUILT 2026-09-29, runs after D626's read (D629 §6):** `check_sierra_aggressor.py --root NG --run` and `--root CL --run`, **after** the 10-11 `c0-signcheck-energy` task has refreshed the Sierra files (they end at the 09-29 download). It refuses before 2026-10-11, before D626's marker (`data/ledger_tas_sign_validation.json`) and before the `topup-trades` job is downloaded; it reads D626's own truth files and only CLX26/CLF27/NGX26/NGF27 inside 2026-09-21 → 2026-10-09. The principal's rulings: UNRESOLVED below 10 sessions, else KEEP at r(ts_recv) ≥ 0.8, VOID below; the four contracts on disk. A VOID follows D629's VOID row and D630/D631's own. **Do not re-run the legacy HO/RB path before 10-10:** its `read_scid` decodes whole files, and the HO/RB files now reach D626's sealed sessions.
            2. **D630 RESULT (2026-09-26): H2 on NG PASSES.** $66 a trade gross, $40 net, t 5.01; placebo −0.42; rotation p95 1.47. Gate 1 is met on NG, with H1 provisional.
               - The move reverts after the settlement (+$29, t 3.98).
               - POST HOC partner control: traded beats untraded at the same move, +$65 (t 4.76).
               - Caveats: the stress fill nets −$9; the result is concentrated in 2022 (without it, net +$5); DSR 0.87 < 0.95; the MNG net Sharpe is 0.44 (misses C-a); fund size acts as a threshold.
               - **NG's Stage A is FROZEN (2026-09-26, A10):** `data/FROZEN_ledger_stage_a_ng.json`. `scripts/verify_ledger_stage_a_ng.py` must pass before the joint vault run and before any work that edits the files it hashes.
               - **The vault waits for the JOINT RUN (A10).** No model opens it alone.
            3. Sierra Chart is paid to 2027-10-24 (Package 3, set 2026-09-26), so no deadline binds. Every in-sample file is on disk, and so are **the vault's NG contracts (DONE 2026-09-26)**: NGK25 … NGX26, 10 files, none cut short (`scripts/sierra_vault_download.py` → `data/sierra_vault_download_record.json`). They are read only in the joint vault run (A10).
            4. **D631 (2026-09-26): Stage B is NOT RETAINED; the ledger stays at Stage A on NG.**
               - The principal chose to run it after POWER showed a 2.5% ceiling against the 10% bar.
               - Out of sample, the flow clause PASSED (ρ 0.137 → 0.170, ×1.24) and the price clause FAILED (H2 t 5.08 → 3.90; $68 → $51 a trade).
               - The midday placebo gains as much (−0.036 → +0.140), so the flow gain is order-flow persistence, not the funds. p swings from 0 to 0.9 across windows.
               - **Lesson for later stages:** a flow gain counts only in excess of the same update's gain at midday. Stage I must gate on that placebo.
            5. **D632 (2026-09-26): Stage C1 is NOT RETAINED; the ledger stays at Stage A on NG.**
               - The forecast creations LOWER the flow correlation (0.137 → 0.094), and a better same-day forecast lowers it further (→ −0.02). The creations' futures are not window aggressive flow; they are likely blocks, EFPs or TAS at the settlement.
               - Price: C1 trades 404 days at $119 (t 4.47) against A's 1,010 at $68 (t 5.08). POST HOC: A's own top-404 |I| days give $141 (t 4.90), so C1's trade edge is only a stricter filter.
               - **Before C2:** the question to put is whether a hedging split h can make a term that lowers the flow fit at every forecast quality useful. C2's premium mostly forecasts same-day creations.
               - **D633 (2026-09-26): Stage D is NOT RETAINED (individually testable, so this is evidence against).**
                 - The TAS imbalance is unrelated to window aggressive flow: partial correlation −0.03 to τ and −0.05 to 14:30; signs agree on 50.1% of days; nil in both source eras.
                 - Adding it dilutes P1: flow 0.136 → 0.043; H2 t 5.01 → 1.23 ($17 gross).
                 - B, C1 and D have now all failed the same way. **The ledger stays at Stage A on NG.**
               - Stage D's pre-registration record:
                 - The NG TAS gap was bought ($0.29, job GLBX-20260926-ACYTFRDQDD). `build_tas_imbalance_panel.py` stitches Databento (≤ 2020-02-10) and Sierra (≥ 2020-02-11), which agree exactly on 2020-02-10.
                 - POWER: size 3.5%; 0.97 at γ = 0.061. The ratio rule breaks at γ = 0.25.
               - Background from the pre-registration (D632), kept as facts:
                 - The funds' creation flow (published AUM; the alignment is proven by the contract counts; `lag_c` = 0) is LARGER than P1 and runs AGAINST it on the same day (SD 2,162 vs 1,814; corr −0.68).
                 - It did NOT explain D629's unconditional negative sign: the slope is still −0.054, t −7.89, with C1.
                 - UNG is absent (G7).
        - Signed flow estimated from one-second bars, carried with a measured band.
        - C2 on Alpha Vantage trade bars, full in-sample; this replaces A7's Arca clause.
        - Stage H forward-only.
      - The quote superseded by this is kept below for the record.
- [ ] **6 (superseded quote). Databento purchases** (principal to approve; quoted 2026-09-24):
      - CL/NG trades 2016–2023: **$1,029.90**, plus **$147.29** to 2025-03, which now applies since
        the vault's seal was chosen (A6); the order-book quote below also ends at 2023 and needs
        re-quoting to 2025-02;
      - TAS trades: **$3.17**;
      - CL/NG order book 2017-05 → 2023: **$6,126.34** (3.65 TB).
      CL/NG options open interest is already on disk from the free pull of 2026-09-22.
- [ ] **7. The non-US products for Stage G** (Claude; deposit Q14–Q16): BetaPro and WisdomTree NAV,
      units, leverage history and restrike terms, plus FX from free central-bank series.
- [ ] **8. Swap dissemination history** (Claude; deposit Q21, §8A.3, H15): DTCC public data;
      coverage not yet verified.
- [ ] **9. The remaining fund facts** (Claude; deposit Q4, Q9–Q11, Q19, Q20).
      - 10 of the 40 facts are unknown (D619). This includes the **time of day of each fund's
        trade**: settlement, TAS or earlier. That decides whether the flow lands in the 14:28–14:30
        window.
      - Item 1 proved the roll DAYS, not the clock time.
      - The T-bill yield for iNAV comes from FRED.
- [ ] **10. The principal's other decisions:**
      - Q7, the NG execution contract;
      - Q5, the prop constraints;
      - Q18, the Track 3 mode;
      - Q17, the recorder host;
      - the attention design: accept D621's amendment as a document edit, or run the full hourly
        backfills (about 2.5 TB of Wikipedia dumps and 1.64 TB of GDELT, free, weeks to download);
      - Q13, the query list, and Q12, social data. **Q12 stays OPEN: the principal is sourcing
        social data (2026-09-24). Do not close or disable it;**
      - Q2 and decision D4, TAS usage, on which the filings are silent;
      - Q24, the COT report choice;
      - the budget.
- [ ] **11. Build** (Claude, once the data has landed):
      - calendar flags for EIA report days and index roll days. Roll days are known:
        - NG: BCOM closes of BD5–9;
        - CL: BD2–3 from 2020-09-17, BCOM's rule before that;
        - UNG: D0..D0+3;
        - USO: D0..D0+3, then BD1–10 from May 2020.
      - the business-day calendar drops holiday republications and fills the 2020 holes from
        `data/ledger_settle_holes_2020.csv`;
      - the §9B validation toolkit, with unit tests 54–58, which D588 declined, and 61;
      - panels for held months, prices and settlements, signed window flow, TAS, depth, the ETF
        premium, creations, the non-US products, swap timing and attention;
      - Stage A–I runners, reading through `load_panel`, with REQUIRED_OUTPUTS and the canonical
        Sortino, and A4's multiple imputation and A5's var_Q1 term wherever f_fut is estimated;
      - the documents that come before any runner: POWER.md with parameter recovery, TRACK_MAP.md
        with every stage on Track 1, the PROGRAMME_REGISTRY entry, and the pre-registration record
        committed before its runner;
      - Gate 0 and Gate 0b, fully passed.
- [ ] **12. Phase 0:** the recorder runs for five clean days on the chosen host. This waits on item 10.
