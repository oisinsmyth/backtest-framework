# FINAL — Fable pair, CONSERVATIVE (hand-back forced before 5 leads were agreed)

Scripts: `scratchpad/leads/fable_pair/scripts/cons_*.py` (conservative) and `crea_*.py` (creative); outputs in
`out/`. Every test in-sample <= 2023-12-29, dollars per ONE micro, bar-close fills (optimistic by a half-spread; the
cost line carries the crossing). Nothing dated 2024+ was read; no repo writes; no downloads.

## 0. Where the debate stood

**0 of 5 leads accepted.** The two agents had agreed the acceptance bar (gross >= 1.0x cost with an explicit
"cost-fragile" reservation and still >= 0 net at cost + one tick; >= 1.5x without reservation; >= 50 events/yr; no
year > 50% of net; trimmed mean positive; top-10 trades < 30% of net). Alive when the harness stopped me:

| rank | lead | owner | state | my prior |
|---|---|---|---|---|
| 1 | **L1 TAS-signed CL settlement fade (MCL).** Predictor outside the price path: the volume-weighted Trade-at-Settlement offset and TAS volume to 14:00 ET (CLT 1-s bars 2017-05..2023, free pull on disk) sign and size the 14:28–14:30 pressure whose 30-min reversal D648 measured at $22 full / $2.23 MCL (78% of the move). New vs D630/D648 (signed by estimated ETF flow). Mechanism documented (CFTC "banging the close" cases; the 2020 negative-oil TAS paper). My open attacks: the sign of the chain is an empirical question (a premium-paying TAS buyer's hedger BUYS into the window; a predatory TAS buyer SELLS into it) — both directions must be reported or the sign set walk-forward; the offset is 0 on 89% of prints; needs the top tercile >= $5.03 with the bottom near zero; NG is frozen (D723) so MCL only. | creative | computing | 25% |
| 2 | **L2 micro/parent volume-share as participant identity (MNQ).** A top-quintile 5-min move carried by an abnormally high MNQ share of NQ volume (retail-chased) reverts; the same move at a low share does not. New: the micro's own volume never used here. On ES it carries nothing (z-top +$0.74 vs z-bottom +$0.02, non-monotone dose, 2019/2023 negative); survives only if NQ shows a monotone dose with the top cell >= $4.07. Index intraday MR is CLOSED for the prop book, so this stands only as a new conditioner with a stated mechanism. | creative | NQ computing | 15% |
| 3 | **G1 ETF-flow-signed gold fix (MGC; SIL mirror with SLV).** D751 closed the price-only proxy and wrote that the AP creation flow "would need fund-flow data, which is not on disk". GLD's daily tonnes/shares (SPDR) and IAU/SLV shares (iShares) are public and free; creations settle at the London PM auction, flows are autocorrelated, so T-1's flow signs T's window pressure and the fade after it. Untested; needs the principal's permission for two free spreadsheets. Bad prior from D751 (no directional structure at the fix with a price proxy). | conservative | data-required | 12% |

Everything else on both lists is dead (below).

## 1. What I killed (my own candidates), with numbers

- **C1 cross-market residual reversion** (SI~GC, HG~GC, HG~SI, CL~BZ, GC~SI, NG~CL; 30-min residual off a trailing
  60-session beta; ~11–14k windows each): rho(resid, y) −0.00..−0.04, no better than the raw move; top-third fades
  −$1.25..+$0.80 vs $4–8. The partner adds nothing. [cons_t1]
- **C2 CME bitcoin futures vs Binance SPOT basis (MBT).** At 15 min: rho −0.076 every year, rotation p05 −0.004,
  spot does not follow; top 5% of |db| $3.35–3.75 vs $4.31. At 1 min: top 1% +$4.72/5 min (t 18.6, 6/6 yrs).
  **Killed by the creative's attack (d):** with the fill one bar later the top-1% fade falls to $0.87 / $0.37 / $0.86
  (5/15/30 min) and the walk-forward non-overlapping book to $0.17 / −$0.02 / $0.23 on ~1,000 trades/yr; a resting
  limit at fair ± X is adverse-selected (−$2 gross, 0/6 years). The reversion lives inside the next minute.
  [cons_t2, t2b, t2c, t2d]
- **C3 COMEX copper at the LME clocks (MHG).** The ring-2 dip is real and documented (Fideres "Dirty Copper"):
  short 12:05→12:35 London +$1.74 (t 5.1, 8/8 yrs), long 12:35→14:05 +$3.34 (t 3.6, 7/8) vs $4.25; the V is ~$5
  over two round trips ($8.50). The 11:00-London placebo reverses MORE (fade +$3.00/60m, t 3.2, 7/8 yrs) and is
  DEAD in the fresh era 2010–15 (rho −0.03, fade −$1.32). Sub-cost, era-specific. [cons_t3, t3b, t7]
- **C4 index-roll days (BD5–10) post-settlement reversion** on CL/NG/HG/GC/SI: nothing roll-specific; CL's front is
  sold −$3.20 (t −2.2) on roll days with no recovery. [cons_t4 D3]
- **C5 6E daily WM/R fix fade**: rho −0.099 every year (decisive vs rotation) but $1.35 gross vs $4.38. [t4 D1]
- **C6 EIA first-two-minute overshoot**: NG rho +0.035, fade −$1.62; CL +$3.53 (t 1.3) vs $5.03. [t4 D2]
- **C7 Tokyo fix on 6J (hourly)**: post-fix hour +$0.90/MJY (t 2.9), gotobi = non-gotobi. [t4 D4]
- **T6 open-interest reversal** (a day's move on falling front OI): runs BACKWARDS — continuation on 8/10 roots. 
- **SI/GC London auctions** (12:00 silver, 10:30 gold AM): silver falls into its auction (−$4.05/SIL, t −3.8) with
  no recovery; fades $1–4 vs $8. GC AM auction: nothing. The SI 13:00-London cell (+$14.83/60m, t 2.7, 2016–23) did
  NOT reproduce in 2010–15 (t 0.9); post hoc, dropped. [t3b, t7]

## 2. What the creative killed (its own), accepted by me

- K1 cross-index residual (ES/NQ/YM/RTY): the hedged residual reverts but the unhedged micro grosses $1.86 (ES,
  2020+2022 = 85%), −$0.90 NQ. K2 SHFE 15:00-Beijing close: GC rho −0.096 but fade $1.20 (= one tick), placebo clock
  reverses as much. K3 parent-contract stop-logic pauses: 18–35 events on the front in 8 years. L3 micro stop-logic:
  117 MNQ events in 5 years (62 in 2020), top trade 31% of the book — rare and lumpy.

## 3. Structural conclusion (the principal's question)

Every price-path-only reversion in the micros lands at $1–6 gross against $4–8 of cost, in both eras and across
metals, energy, FX and crypto: the repo's structural result holds. The effects are real (rho −0.05..−0.11, decisive
against rotation nulls, stable year to year) and too small by 2–4x. **A lead that can clear the micro round trip must
bring information from OUTSIDE the instrument's own price path** — a flow with known sign and size (TAS prints, ETF
creations), or a participant-identity signal (the micro's own volume share) — and should live in the highest
dollar-sigma micros (SIL sd(30m) $68, MNQ, MBT). The three candidates above are exactly of that kind; none is yet
shown to pay.

## 3b. Addendum — the creative's L1/L2/L3 numbers arrived after the hand-back (crea_10, crea_10b, crea_13)

- **L1 TAS-offset-signed post-settlement reversal on MCL: REAL, 0.74x COST, MECHANISM OPEN — not a lead under the
  agreed bar.** rho(W_late, y 14:30->14:59) = -0.119 CL (-0.163 for y2 to 15:29); fade = -sign(W), top tercile |W|:
  y $2.86 (t 2.7, n 410, median $3, win .556), y2 $3.74 (t 2.7) vs $5.03; beats its rotation (p95 $1.65); dose
  monotone; the unconditional fade is $0.09 here so the sign is doing the work (not momentum in disguise). Eras:
  2017-19 -$1.25 (n 60), 2020-21 +$3.90 (t 3.3), 2022-23 +$3.29. **The dealer-hedging chain is FALSIFIED**: a TAS
  premium goes with a window move DOWN (rho -0.076 CL, -0.213 NG) and W tracks the afternoon's direction (+0.24).
  TAS volume carries nothing. Two POST HOC cells, not claimed: discount-side-only long on y2 $6.24 (t 3.5, n 246 =
  37/yr, 2020 = 38%; 1.24x, +$0.21 at +1 tick; fails n >= 50/yr); Mon-Thu only y2 ~$5.0 on ~50/yr (Fridays -$1.1:
  the CL weekly options expire at the Friday settlement). NG transfer: 2022-23 only. My verdict: the best-evidenced
  OUTSIDE-information signer found by the pair; it fails 1.0x on the pre-registrable cell; worth a pre-registration
  ONLY if the principal accepts the Friday exclusion as a mechanism-motivated primary cell (then ~1.0x, cost-fragile).
- **L2 micro share: DEAD** (NQ z_top +$2.19 vs z_bottom +$0.15, 2020-carried, dose not monotone; ES nothing).
- **L3 micro stop-logic: WITHDRAWN** (1-second check: the "basis" is a contract-mismatch/stale-print artefact).
- **The creative found unread instruments in the ALL_SYMBOLS 1-m archive**: COMEX TAS (GCT/SIT/HGT/PLT), BTIC on
  ES/NQ/YM (basis trades to the 16:00 cash close), TACO (09:30 cash open), ZBT/BZT/HOT/RBT. Its next constructions
  (not yet run): N1 BTIC-signed 16:00->16:10 fade on MES/MNQ/MYM (signs D762's unsigned null result from the BTIC
  tape); N2 TAS-signed post-settlement fade on MGC/SIL/MHG (L1's transfer to roots never tested); N3 the CL 1-second
  last-30-second overshoot vs the settlement VWAP, which also gives L1 a 14:30:01 entry. These are the right next
  tests: outside-information signers on forced legs, and the only line in this debate with a positive gradient.
- **G1 extended** (creative's addition): the same free SLV file signs the SILVER auction, a mechanism for the SI
  13:00-London cell; quote G1 as one data-required lead with a gold and a silver leg.

## 3c. Addendum 2 — N1/N2/N3 results (creative, crea_14..18; JSON out/crea_16_metals_tas.json, crea_17_btic_close.json, crea_18_settle_1s.json)

- **N1 BTIC-signed cash-close fade: DEAD.** ES rho(dB, 16:00->16:10) -0.016, the first link (dB -> 15:50->16:00)
  absent (+0.047); top-tercile fade $0.51. NQ nothing. YM rho -0.076, fade $1.78 (t 2.3) vs $3.80. TACO too thin.
  BTIC volume predicts SIZE only (|16:00->16:10| by tercile ES $10.3/11.7/13.7, NQ $18.9/24.2/27.3).
- **N2 COMEX TAS-signed post-settlement fade:** GC 0.56x cost, DEAD; HG wrong sign, DEAD. **SIL: real but not a
  lead** — top tercile |W| y30 $9.75 (t 3.7, n 428 = 54/yr, median $5, rotation p95 $4.49), y60 $12.35 (t 3.3),
  monotone dose, survives a 5-min delayed entry ($8.82); BUT 2020 = 53% of y60, 2022-23 = -$4.30 (n 100), top-10
  trades = 58% of net, and the raw window-move fade on the same days earns the same ($12.76, t 3.5) with W
  uncorrelated to it — TAS is a second signer of SI's known generic post-13:25 reversal (my C4 / D709), not a new
  effect. The agreement cell (TAS sign = window sign) $20.13 (t 4.0, n 265) is POST HOC.
- **N3 1-second settlement overshoot (CL/NG):** DEAD (rho ~0, fade negative; the last-30-second push reverts within
  1-5 min at ~$1.4). The TAS-signed fade entered at the executable 14:30:01 reproduces the 1-min L1 result: CL y29
  $2.83 (t 2.6); NG y15 $3.37 (t 2.9) — NG transfer only (frozen line).
- **Pair tally: 0 of 5 leads meet the agreed bar.** Both agents concur. The one construction either of us would still
  pre-register as a Stage 0, knowing it is ~0.74x: **L1 on MCL, TAS-offset-signed post-settlement fade, with the
  Friday (LO weekly-expiry) exclusion as the pre-registered secondary cell.** The structural finding worth recording:
  the ohlcv-1m archive is ALL_SYMBOLS and carries TAS/BTIC/TACO tapes for every root — outside-information prints
  the repo has never read — and on CL/NG/SI the TAS offset signs the post-settlement reversal at t 2.6-3.7 while the
  window move itself does not on CL (rho -0.05). That is a new TYPE of predictor; it is not yet a new SIZE.

## 3d. Addendum 3 — the debate resumed on the main session's instruction (keep the bar, do not pad, reach 5)

- **SIL post-settlement fade (cons_t8, t8b):** x = 12:55->13:25 ET window move, fade y60, walk-forward top third:
  **$13.10 gross (t 3.4, 68/yr, median $10, trimmed $11.85, ex-top-1% $8.31), net +$5.10 at $8, +$0.10 at $13**;
  rho(x,y60) -0.133 (rotation p05 -0.038), the 11:55 clock placebo flat, GC weak: clock- and silver-specific, 1.6x the
  line. **DEAD by regime decay, not scale:** rho by year -0.20/-0.22/-0.27/-0.17/-0.22/-0.10 (2016-21) then
  +0.02/+0.03 (2022-23) at the same volatility; 2022-23 n 163 mean -$1.60, median 0, win 0.485. The pair's largest
  in-sample number; the same shape as D709's into-window move and D685. Not a lead.
- **T9 — G1's premise via the on-disk proxy: DEAD, and G1 is withdrawn.** GLD's and IAU's close premium to the
  GC-implied NAV (de-trended, autocorrelation 0.86 — a persistent AP trigger) at T-1 carries NOTHING for the next
  day's London PM window: rho(prem, into-fix) +0.001 / +0.009, rho(prem, after-fix) -0.003 / -0.007, rotation p 0.6-0.9,
  3,282 days 2010-23; the signed into-fix trade is 2020-21-carried ($7-13 vs $-2..+2 elsewhere). If the APs' own
  creation trigger does not sign the fix window, the free flow files are unlikely to; G1 drops to "not a lead".
- **R1 (creative; crea_19, crea_23) — MNG post-settlement fade sized by the leveraged-fund flow |I| (D630's own
  predictor), the best-evidenced reversal of the debate, WITHDRAWN as a solid lead.** Pooled in-sample top tercile:
  y60 $7.94 (t 4.2, 78/yr, median $6, trimmed $8.02), dose monotone by |I| quintile ($0.8/0.6/1.6/2.9/10.7), rotation
  p95 $2.61, TAS-agreement cell $11.33 (t 4.9). But WALK-FORWARD (trailing-250 tercile): y60 $6.05 (t 4.0, median
  $2.5, top-10 34%), **ex-2022 $2.55 (t 2.2)**; by year y60 2018 $3.29, 2019 $0.93, 2020 $1.79, 2021 $3.51, **2022
  $16.27 (69% of net)**, in vol units 0.09-0.28 sd a trade every year. The effect exists every year and clears the
  fixed dollar cost only when NG's sd(y60) is ~$60 (2022): the principal's closure reason (one-year edge) and the
  repo's structural result (a relative-size reversion against a fixed-dollar cost is a vol-regime gate). CL does not
  transfer (the funds are swaps). **One reframing requested before closing:** R1 with a pre-registered EX-ANTE vol
  gate (trailing-20-session sd of the 14:29->15:29 MNG move >= $30 / $40, thresholds from the breakeven arithmetic, not
  the data) — the principal's own abstention principle; acceptable only as a lead with the reservation "vol-gated by
  construction; trades concentrate in high-volatility years".
- **L1 MCL Mon-Thu cell (crea_21):** hold to 15:29 $5.05 (t 3.0, 46/yr, median $4) = 1.0x, net −$0.98 at +1 tick,
  top-10 share 61%, 2020 = 41%; the TAS sign carries it (the unsigned control $1.05). FAILS the bar; the Friday
  exclusion does not rescue it. MNG Mon-Thu 1-s entry to 15:59 $6.75 (t 3.0) but 2022 = 77%.
- **SIL TAS agreement cell (crea_21):** inherits T8's decay (2020 = 49%, 2022-23 −$6.60, top-10 58%). DEAD.
- **R2 (creative, data-required):** Nasdaq TotalView NOII imbalance for the 25 largest NDX names 2018-05..2023,
  Databento quote **$25.97** (ALL_SYMBOLS $10,742); signer for a 16:00->16:10 MNQ fade of the closing-auction
  pressure; D762's sd(y10) $42/MNQ needs rho >= 0.1 for 1.0x; closing-pressure reversal in the literature is
  overnight, not intra-10-minutes. **Prior <= 10%**, recorded as data-required, not solid.
- **T10/T10b — the vol-gate reframing, GATE ALONE (window-move sign), four settlement roots.** Gate = trailing-20-
  session sd of the post-window y60 (pre-entry), thresholds from the breakeven arithmetic (cost/0.15 at 1.0x and
  1.5x). NG: fails ($1.94 at >= $30; the flow signer is essential on NG). CL, GC: nothing. **SIL at gate >= $80 (19%
  of days, 47/yr): fade60 $15.51 gross (t 2.7, median $10, trimmed $14.29, ex-top-1% $9.95, win .563), net +$7.51 at
  $8 / +$2.51 at $13 (+1 SIL tick) / −$2.49 at $18; 6 of 7 years positive (2016 +18.3 n33, 2017 +8.3 n3, 2018 +25.8
  n19, 2020 +8.2 n114, 2021 +27.7 n98, 2022 +13.5 n84, 2023 −5.2 n22); Mon-Thu 7/7 years ($14.78).** Robustness:
  threshold plateau $70-$100 ($12.5-15.5, 1.6-1.9x), not a knife-edge; 5/10-min delayed entry $11.5-11.6 (t 2.1-2.6)
  — not bounce; exact rotation within the gated set rank 0.989 (p95 $10.1, p99 $14.9); |x| size adds nothing (halves
  $15.8 / $15.3); the 11:55 clock placebo under its own gate −$3.88; the ungated book $4.2 (t 2.9). Weaknesses:
  top-10 share 69% (symmetric trim still 1.8x), 2020-22 = 83% of net because 80% of gated days are 2020-22 (the gate
  IS a vol-regime selector), 2023's 22 trades −$5 (SE ~$15), SIL crossing unmeasured (one-tick convention). D709
  closed SI's INTO-window LETF line; this is the post-window fade under an ex-ante gate — a stated difference, and
  the principal's own abstention principle. **Proposed to the creative as LEAD 1 — then RETRACTED by my own top-trade
  check (cons_t10c):** NET by year at $8 = 2016 +341, 2017 +1, 2018 +338, 2019 0, **2020 +23 (114 trades, gross =
  cost), 2021 +1,931 (69% of the $2,801 net)**, 2022 +458, 2023 −291; at $13 only 2021 is positive of size (2020
  −547, 2023 −401). Top month 2021-01 = 30% of gross, top 3 months 51%; four of the top-10 trades are 2021-01-28 ..
  2021-02-02, **the Reddit silver squeeze**. Daily net Sharpe 0.47 at $8, 0.16 at $13. "6 of 7 years positive" was
  gross; at the account's cost it is a one-year edge on one episode. NOT a lead.
- **The creative's last three (crea_24/25/26), read from their JSON at hand-back:**
  - **Index LETF post-close reversal (fade the DAY's direction 16:00->16:05/16:10, top tercile |r_day|):** NQ y5
    $5.47 (t 3.5, net +$1.40 at $4.07; y10 $3.47, net −$0.60), years y10 2020 −0.5 / 2021 −9.4 / 2022 +9.5 / 2023
    +8.5; ES y5 $4.06 (t 5.0, net −$0.36), y10 $3.52; YM/RTY $1.4-2.6. D762's unsigned fade on the same days ~$0.1-
    0.9, so the day-sign carries it — a real signed closing-pressure reversal at ~1.0-1.3x on a 5-minute hold, cost-
    fragile, with 2021 strongly negative on NQ. Not a lead under the bar.
  - **R1 vol-gated (MNG, flow-signed, gate = trailing-20 sd of y60 >= $20/$30/$40):** gated top tercile y60 $11.4 /
    $13.2 / $17.6 (t 4.0-4.5, median 9.5-16), net +$7.4 / +$9.2 at $4; in vol units 0.21-0.25 gated vs 0.065 ungated
    (high-vol days revert MORE, not merely larger) — but the gate is open on 100% of 2022 and 2-38% of other years,
    2022 is 154 of 302 trades and ~73% of the net, and 2023 has 2 trades. The best-evidenced construction of the
    debate and, at the account's cost, a 2022 book. Not a lead under the principal's rule.
  - **CL front-vs-second-month residual:** DEAD (rho(dspread, y) −0.003 to −0.013; every cell negative).

## 3e. The pair's close

**0 of 5 leads meet the agreed bar after ~60 primary cells across both agents** (every price-path reversion;
cross-venue basis; the TAS/BTIC/TACO tapes; fund-flow sizing; vol gates; ETF premia; open interest; LME/LBMA/Tokyo/
WM-R clocks; EIA; rolls; stop-logic pauses). Three constructions are real in gross at t 3-4.5 and would be the
Stage-0 candidates if the principal relaxes the one-year rule for an explicitly vol-gated (abstention) book:
1. **R1 — MNG post-settlement fade sized by the leveraged-fund flow, vol-gated** ($11-18 gross, net 2-4x the line
   on gated days; 2022 = 73% of net because the gate is open all of 2022).
2. **SIL post-settlement fade, vol-gated at sd >= $80** ($15.5 gross; at cost 2021 = 69% of net, the silver squeeze).
3. **L1 — TAS-offset-signed MCL post-settlement fade** ($3.74-5.05 gross, ~0.74-1.0x; mechanism open; 2020 41%).
Each is the same object: a 0.1-0.3 sd-per-trade reversion of settlement-window pressure that clears a fixed-dollar
micro cost only in the high-volatility year. The structural findings for the record: (i) that equation — a
relative-size reversion against a fixed-dollar cost is a vol-regime gate — holds in every market tested; (ii) the
ALL_SYMBOLS archive carries TAS/BTIC/TACO prints for every root, unread until now, and the TAS offset is an
outside-information signer of the post-settlement reversal on CL/NG/SI (t 2.6-3.7) while the window move itself is
not on CL; (iii) the metals' settlement reversions died as a regime in 2022-23 (SI rho −0.2 -> +0.02 at unchanged
volatility); (iv) nothing in the index micros survives an outside signer either (BTIC, micro share, stop-logic).
Data-required, low prior (<= 10%): R2, the Nasdaq closing-auction imbalance signer for MNQ ($25.97 quote).

**The creative's final numbers (crea_25/27/28), both agents concurring on the close:**
- R1 vol-gated at X=$30: gross $13.16 (t 4.1, n 259, median $14), ungated top tercile $0.72 (the gate explains it),
  gated bottom-two terciles $1.80 (the flow size matters), 0.25 sd gated vs 0.056 ungated. **Net by year at $4: 2018
  +297 (13%), 2019 −67, 2020 −21, 2021 +339 (14%), 2022 +1,761 (74%), 2023 +63 (2 trades)**; at X=$40 2022 = 85%,
  9 of the top-10 trades are 2022. Daily net Sharpe 1.38, max DD $434 — and it is a 2022 book. Withdrawn.
- LETF-signed post-close reversal, walk-forward top |r_day| tercile, 16:00->16:05: **MNQ $5.10 (t 3.3, 76/yr, median
  $2, top-10 62%) = 1.25x, 2022 = 64% of gross; MES $3.41 (t 4.0) = 0.77x and EVERY year positive (0.48..5.68)** —
  the one stable thing in the debate, sub-cost. Clock-specific: the same rule at 15:00 is −$8.7/−$3.7 (continuation),
  ~0 at 12:00; D762's unsigned fade on the same days $0.1-0.2. Fails the bar (MNQ year concentration; MES size).
- CL front vs second month: dead (rho −0.003/−0.011; every cell negative). The TAS CL fade under a vol gate: the gate
  opens only in 2020/2022 (54 days); nothing.

**Ranked by prior, none "solid" under the BRIEF's bar; the reservations are the kill reasons above, verbatim:**
1. MNG post-settlement fade sized by the leveraged-fund flow, vol-gated (prior 20% as a vol-regime abstention book
   the principal would have to accept as such; <5% under the one-year rule).
2. LETF-signed post-close reversal on MES/MNQ, 16:00->16:05 (prior 15%: stable every year on MES at 0.77x; the only
   path is a lower cost line or a larger-sigma micro, and MNQ's is 2022).
3. SIL post-window fade under an ex-ante sigma gate (prior 10%: 2021/the silver squeeze at cost).
4. MCL TAS-offset-signed post-settlement fade (prior 10%: 0.74-1.0x, mechanism open, tail-heavy).
5. R2 MOC-imbalance-signed MNQ close fade, data-required at $26 (prior <= 10%).

## 4. Dissent / reservations

- The creative agent proposed the 1.0x-with-reservation bar; I accepted it with the "+1 tick still >= 0" clause.
- I would not carry L2 if NQ is not monotone, and I would not carry G1 without the principal's data permission.
- The hand-back was forced by the harness before L1/L2 numbers arrived; the creative agent (aecb5655d6e764fe5)
  holds them in `out/crea_07*`, `out/crea_08_micro_share.json`.
