# Conservative agent — working notes (Fable pair)

Seal: nothing dated >= 2024-01-01 is read. No repo writes. Scripts in `scripts/cons_*.py`, outputs in `out/`.

## Audit checklist (the repo's failure modes, applied to every lead)

1. **Sub-cost size.** Gross per micro vs the cost line (`data/futures_costs.json`: $3 + measured crossing; MES 4.42,
   MNQ 4.07, MGC 5.93, MCL 5.03, MBT 4.31, M6E 4.38, MHG ~5.5 (one tick, unmeasured), SIL ~8 (one tick, unmeasured),
   MNG 4.0). A $-fade at rho -0.1 on a $20-sd response grosses ~$2: structurally short. Ask for sd(y)/cost >= 5 or
   rho >= 0.2 before believing a fade clears. Prefer high-$-sigma micros (SIL, MNQ, MHG, MBT).
2. **Momentum in disguise.** A "reversion" of a residual/relative move may be the market factor continuing. Demand the
   control: the same fade on the raw move, and the residual fade on rows where the raw move is NOT extreme.
3. **2020-2022 concentration.** Year split; mean ex-best-year; the volatility-unit concentration (D729).
4. **Look-ahead.** Predictor strictly from bars ending at or before the entry; walk-forward thresholds; the fix clocks via
   zoneinfo (DST mismatch weeks are a free placebo, D749/D751).
5. **Rotation-null equivalence.** Time rotation of the response; for a label (roll day, event day) an enumerated label
   rotation; p50/p95 beside the score, SE of the p95.
6. **Decay as markets deepen.** Era split (pre/post 2019; 2015 fix reform; MBT era 2021+). Flows that are published get
   front-run and absorbed (D685, D709, D764).
7. **Rare and lumpy.** Events/year >= ~50 and no single trade > 10% of the total; trim 1% both tails.
8. **Multiple testing in my own search.** I ran 6 pairs x 2 signals (T1), 7 clocks (T3), 4 clock tests (T4), 1 basis
   test (T2): ~25 primary cells. One nominal p < 0.05 in 25 is expected. Family-wise read before believing anything.
9. **Bid-ask bounce as reversion** (D530): a close measured in a thin tail bounces on the spread; use each root's own
   liquid hours; a tick-sized "reversal" is bounce.
10. **A high win rate bought by a bracket** (D752): report mean beside median; no stops in premise tests.
11. **Closed-record re-runs:** index-micro intraday MR (D746/D747/D752), gold/FX fixes (D749/D751), China open
    (D765-D771), settlement fades (D630/D648/D709), cash close (D762), expiry (D763/D764), funding (D580/D766),
    round numbers (D761), levels (D724/D725), gamma direction, aggressor flow (D695/D715/D717/D770).

## Candidate list (conservative: documented forced flow / cross-market structure first)

C1. **Cross-market residual reversion, metals/energy (SIL vs MGC, MHG vs MGC/SIL, MCL vs BZ).** Mechanism: a liquidity
    shock in one leg of a cointegrated pair moves that leg off its partner; arbitrageurs/market makers restore the
    relation; the idiosyncratic component reverts while the common component does not (pairs/lead-lag literature;
    Campbell-Grossman-Wang liquidity-demand reversal applied to the idiosyncratic leg). Traded on ONE leg (no hedge).
    New: D261 pairs were daily ETF spreads; D735/D737 is the INDEX complex and trades the spread's continuation (NQ
    leads). Metals/energy intraday residuals untested. Test: T1.
C2. **CME bitcoin futures vs spot basis change (MBT).** Mechanism: CME-only flows (institutions, CTAs, no spot
    arbitrage inside the CME book) push the futures off spot; cash-and-carry arbs restore the basis; the futures' excess
    move over spot reverts. New: D580/D766 (funding), D764 (expiry), D758 (weekend gap) never used the spot leg. Risk:
    CME leads price discovery (Kapar-Olmo 2019; Alexander et al.) so the spot catches up instead. Test: T2.
C3. **COMEX copper at the LME benchmark clocks (MHG).** Mechanism: the LME official price (Ring 2, 12:30-12:35 London)
    is the physical pricing benchmark; producers/consumers/banks hedge fixing exposure into the ring; the pressure into a
    benchmark reverts after it (fix literature: Evans 2018; Melvin-Prins 2015). New: the repo's own AITODO names it as
    "the one untried idea" (D758 entry); D749/D751 were FX and gold fixes. Risk: D749/D751 found no price-only direction
    at the FX/gold fixes. Test: T3 (ring 2, official, LME close, placebos).
C4. **Index-roll-day post-settlement reversion (MCL/MNG/MHG/MGC/SIL).** Mechanism: GSCI/BCOM roll BD5-9/6-10 sells the
    front into the settlement (TAS); liquidity providers absorb it and the pressure reverts (Bessembinder et al. 2016 JFE
    on the Goldman roll; Mou 2011). New vs D630/D648/D709 (fund flows), D635 (flow INTO the window, unread): the sign is
    known a priori and the flow is concentrated on five known days. Risk: faded (Mou's effect decayed; D709 shape). Test: T4-D3.
C5. **6E daily WM/R fix fade (M6E).** Daily, two-sided, not month-end-signed (D749 was month-end signed by equities).
    Risk: size (M6E $ sigma small). Test: T4-D1. Expected to die on size.
C6. **EIA storage/petroleum first-minute overshoot (MNG/MCL).** 52/yr each; rare-ish. Test: T4-D2.
C7. **Tokyo fix 09:55 JST reversal on 6J/MJY, gotobi days** (Ito-Yamada). Repo already sized the into-fix leg as under the
    micro bar; the post-fix reversal is the untested leg. MJY liquidity is a reservation. Test: T4-D4 (hourly, crude).

## Results log (all $ per one micro, in-sample <= 2023)

- **T1 residual reversion (cons_t1_resid_reversion.py):** DEAD. rho(resid, y) -0.00..-0.04 on all six pairs, no
  better than the raw move; top-third fades -$1.25..+$0.80 gross vs $4-8. The partner adds nothing.
- **T2/T2b BTC basis (cons_t2_btc_basis.py, cons_t2b_btc_basis_dose.py):** REAL, STABLE, SUB-COST. rho(db, yf15)
  -0.076 every year 2018-23; rotation p05 -0.004; spot does not follow (+0.02). Dose monotone: top decile $2.3-2.6,
  top 5% (|db| > $64) $3.35/30m, $3.75/60m (t 5), net -$0.96/-$0.56, 2018-20 negative 2021-23 positive; top 2%
  $3.8-4.1 (net ~ -$0.2..-$0.5). EVE session (21-24 UTC) strongest. Level deviation carries nothing. Median at top 5%
  = $3 (6 ticks), not bounce. Verdict: lead with reservation (break-even at the tail), prior ~15%.
- **T3/T3b HG at LME clocks (cons_t3_lme_copper.py, cons_t3b_metals_london.py):** the ring-2 dip is real and
  documented (Fideres "Dirty Copper"): short 12:05->12:35 London +$1.74 (t 5.1, 8/8 years), long 12:35->14:05 +$3.34
  (t 3.6, 7/8) vs $4.25; the V is ~$5 over two round trips ($8.50). rho at 12:35 -0.058 (p 0.014) but the 11:00
  placebo reverses MORE (rho -0.073, fade +$3.00/60m, t 3.2, 7/8 yrs): generic London-morning reversion, not the
  clock. Dose at 11:00 not monotone (top quintile $3.25/60m). SUB-COST everywhere.
- **T3b SI LBMA silver 12:00 London:** silver also falls into its auction (-$4.05/SIL, t -3.8) with no recovery
  (+$0.23). rho -0.051 (p 0.02) but the 11:00 placebo rho -0.093; fades $1-4 vs $8. DEAD. GC AM auction: see json.
- **T4-D1 6E daily fix:** rho -0.099 every year (decisive vs rotation) but $1.35 gross vs $4.38. DEAD on size.
- **T4-D2 EIA:** NG nothing (rho +0.035, fade -$1.62). CL events fade +$3.53 (t 1.3, 6/8 yrs) vs $5.03: underpowered,
  sub-cost. DEAD.
- **T4-D3 roll days:** nothing roll-specific on CL/NG/HG/GC/SI. CL front sold -$3.20 (t -2.2) on roll days, no
  recovery. SI post-13:25 fade on all days +$5.87/60m (t 3.4, 7/8) vs $8 -- D709 territory (closed), thin tape.
- **T4-D4 6J Tokyo fix (hourly):** post-fix hour +$0.90/MJY (t 2.9), gotobi no different. DEAD.
- **T2c BTC basis at ONE minute (cons_t2c_btc_basis_1m.py; Binance 1m raw klines + fut_btc_1m, 1.51M minutes
  2018-23):** rho(db5, yf5) -0.109, every year -0.063..-0.068 at 15 min. Dose monotone. Top 1% in-sample (|db5| >
  $106, ~1,800/yr): +$4.72/5 min (t 18.6, 6/6 years, median $4, trimmed $4.52, ex-top1 $3.47) -> net +$0.41 at
  $4.31; 30 min +$4.59 (net +$0.28); EVE 21-24 UTC $5.35, US $2.65. Walk-forward top 5%: $1.5-1.7. The RESTING-LIMIT
  book at fair +/- X is NEGATIVE at every X (-$1.9 to -$2.3 gross, 0/6 years): adverse selection, as D770 found.
  Verdict: real, documented, stable; break-even at the tail with a taker entry; no passive rescue.
- **T3b SI 13:00-London placebo cell:** fade/60m +$14.83 (t 2.7, 7/8 yrs, net +$6.83 at $8) but rho -0.02 (p 0.34):
  1 of ~25 cells, money in the tail, no linear relation -> POST HOC, not a lead unless re-found on a fresh design.
- **T6 open-interest reversal (cons_t6_oi_reversal.py; fut_oi_expiry_cycles + breadth hourly, 10 roots):** the
  folklore runs backwards -- a day's move on FALLING front OI CONTINUES next session (rho(ret, next | OI fall) +0.05
  to +0.07 on CL, HG, 6E, 6B, ZN); the fade loses on 8 of 10 roots. SI fade +$27.88 (t 1.96) is 2020-carried ($109)
  with 4/7 years. DEAD as a reversion predictor.
- **T2d BTC basis robustness:** ONE-BAR DELAY (fill at the close of t+1) collapses the top-1% fade from $4.73 to
  $0.87 (5m), $4.03 -> $0.37 (15m), $4.55 -> $0.86 (30m); the walk-forward non-overlapping delayed book is $0.17 /
  -$0.02 / $0.23 on 830-1,270 trades/yr. The reversion lives inside the next minute: not enterable on 1-min bars, and
  the resting-limit version is adverse-selected. C2 WITHDRAWN.
- **Sources for the debate:** Fideres "Dirty Copper" (pre-official-price decline in copper 2005-15, matches my HG V);
  Bessembinder-Carrion-Tuttle-Venkataraman 2016 JFE (roll trades: liquidity provision, temporary impact reversed);
  CFTC "banging the close" TAS cases (Optiver 2008, Shak 2013) and the 2020 negative-oil TAS paper (AEA 2023): a TAS
  BUYER who wants a low settle sells outrights into the window (down into the window, up after) while a TAS SELLER
  hedging a premium-paying buyer BUYS outrights into the window (up, then down) -- the sign of L1's chain is an
  empirical question, not a theorem; both directions must be reported, or the sign set walk-forward.
- **T7 fresh era 2010-06..2015-08 (cons_t7_fresh_era_london.py; 3.19M SI/HG front minutes decoded from the raw
  archive, never read before):** the SI 12:30->13:00 London cell faded to 14:00: walk-forward top third +$10.03 (t
  0.91, n 289), in-sample-threshold top third +$1.96 (t 0.2), all days +$6.33 (t 1.36) -- NOT CONFIRMED (sd_y was
  $169 then, cost $8). The 12:00 silver-fix cell reverses in THIS era (all days +$9.47, t 2.75, rho -0.09) but was flat
  in 2016-23: the clock moves between eras, so there is no pre-registrable construction. HG 11:00 London: DEAD in the
  fresh era (rho -0.03, top-third fade -$1.32). Both London-morning cells are dropped.
- **T8/T8b SIL post-settlement fade:** 1.6x in-sample (top third y60 $13.10, t 3.4) but rho flips to +0.02 in 2022-23 at
  the same volatility -> regime death; not a lead. **T9 GLD/IAU premium -> fix:** rho 0.00; G1 withdrawn.
- **DRAFT (pending the partner's walk-forward numbers) — R1 entry for AGREED.md:**
  LEAD: MNG post-settlement fade sized by the leveraged-fund flow. Mechanism: BOIL/KOLD's daily rebalance is executed
  into the 14:28-14:30 NG settlement (D627-D630, H2 PASS t 5.0); the price impact is temporary and reverts after the
  window (D630 reported $29 full unconditional; D648's CL T3 78% reversal). New because: D630/D648 traded the FOLLOW
  into the window and reported the fade unconditionally at $2.90/MNG; this sizes the fade by the predicted flow |I|
  and trades against the funds. Construction: MNG, enter at the 14:30 close (or 14:30:01), exit 15:29, side =
  -sign(predicted fund direction), on the top third of |I| (walk-forward). Predictor: the ledger's 13:50 predicted-flow
  row (AUM x return), pre-entry. Premise (crea_19): pooled top tercile y60 $7.94 (t 4.2, n 546, median $6, trimmed
  $8.02), net +$3.94 at $4 / +$2.94 at $5 / +$1.94 at $6; dose monotone by |I| quintile ($0.8/0.6/1.6/2.9/10.7);
  rotation p95 $2.61; TAS-agreement cell $11.33 (t 4.9, 36/yr). Frequency 78/yr. Stability: 2022 = 69% of net; 2021
  and 2023 below cost on y30 (pending y60 and walk-forward). Kill: walk-forward top-third y60 < $5.00 in two of
  2021/2022/2023, or the +1-tick net < 0. Reservations: 2021-23 effective sample; MNG crossing unmeasured at this
  clock; D723 vault entanglement; CL does not transfer (swaps).
- **Pattern:** every price-path-only reversion lands at $1-6 gross vs $4-8 cost. A surviving lead must bring
  information from outside the instrument's own price path, or live in the highest $-sigma micros at rho >= 0.15.
