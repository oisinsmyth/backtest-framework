# Creative notes (Opus pair)

All tests in-sample 2016-2023 (or narrower), seal asserted in each script. $ per ONE micro, gross. Scripts in
`scripts/crea_*`, outputs in `out/crea_*`.

## Candidates and status

| # | candidate | mechanism | status | key numbers |
|---|---|---|---|---|
| C1 | Micro (retail) share of volume as a noise detector | retail flow = noise -> reverts; mini flow = info -> continues | DROPPED | 30/30 gradient right-signed on ES/NQ/YM/GC (beta +0.02..+0.04 low-z, -0.015..-0.024 high-z) but fade top-z big moves -$2.5 ES, -$2.1 NQ, +$1.5 MGC; does not survive B=15 or 60 |
| C2 | SHFE night-session close, DST natural experiment (MGC/MHG/SIL) | Chinese intraday unwind at 02:30/01:00 Beijing | NOT RUN | China cluster D765-D771 mined; low novelty |
| C3 | 18:00 reopen auction overshoot | thin reopen book | NOT RUN | D499 (off-hours big hours revert, worth a tick) covers it |
| C4 | CME velocity-logic pauses (status schema) -> post-pause reversion | stop cascades halted by VL | DROPPED: RARE | distinct VL minutes 2016-23: NQ 254, ES 131, RTY 88, YM 54, GC 12, SI 38, HG 7; clustered at 08:30 and 18:00 and in 2020/2022 |
| C5 | Post-cash-close mega-cap earnings overshoot (NQ/ES), fade from 18:05 to 10:00 next day | AH book thin, index arb absent, single-stock earnings move index futures; cash open auction reprices | OPEN, weak-moderate | see below |
| C6 | VIX settlement (SOQ) Wednesday open | VIX hedgers trade SPX options at the open | NOT RUN | 12/yr: rare |
| C7 | CL/NG option-expiry pinning (LO/ON OI on disk) | dealer gamma at max-OI strike | NOT RUN | ES pinning read as repulsion (D614/D618) |
| C8 | Daily WM/R 4pm London fix (11:00 ET) on M6E | fix flow then reversal (Evans 2018) | NOT RUN | month-end version D749 +$4.78 post hoc; daily is smaller |
| C9 | Cross-asset residual (lone mover) reversion: SI|GC, GC|6E+ZN, YM|ES | idiosyncratic flow reverts, common info does not | TO RUN | D767 is the China-open version |
| C10 | IV/RV ratio as a reversion conditioner | options market says a move is transient | NOT RUN | |
| C11 | Second-tier releases (ISM 10:00) | low-information headlines overshoot | partner ran (K3): noise |
| C12 | 08:30 releases fade (CPI, EMPSIT, claims Thursday) on ES/NQ/GC | headline overshoot in the thin pre-open | MIXED | NQ K1->09:29: CPI -$29.41 (n92), EMPSIT +$12.50; K3->10:00: CPI +$7.82, EMPSIT +$30.79; THU claims ~0; GC: CPI reverts, EMPSIT continues. CPI sign depends on K and exit |
| C13 | CME BTC vs Binance spot basis (spot leads futures) | lead-lag plumbing | DROPPED: SUB-COST | t 3-8 but +$0.3-1.5/MBT; top 0.1% basis dev (160 bp) +$2.7-4.6 |
| C14 | CTA trend-signal flip pressure -> reversal (enter 18:00, exit by 16:10 next day) | predictable CTA execution after a signal flip | TO RUN | |
| C15 | Treasury post-auction recovery next day on micro yields | dealer inventory (Lou-Yan-Zhang 2013) | DROPPED | D710 covered it; post leg 0.85-2.99 price bp |

## Later tests (all dead unless noted)
- C5 reframed as post-cash-close transience -> ACCEPTED as Lead 2 (crea_postclose_vs_day.py, crea_postclose_legB.py; leg A ranks 0.98-1.00 on 4 roots).
  Mechanism probes: commodity post-settlement CONTINUES (crea_postsettle.py); post-London FX nil (crea_fx_postlondon.py);
  non-expiry nights carry it (crea_postclose_expiry.py/_weekday.py); reverting sub-window moved with the 2020-10-26 settlement
  shift and the 2021-06-25 end of the 16:15 halt (crea_postclose_subwin.py/_regimes.py, crea_es_halt_dates.py).
- MOC window 15:50->16:00 faded overnight -> ACCEPTED as Lead 4 on M2K (crea_moc_standalone.py).
- K6 gold weekend reopen attacked (crea_k6_attack.py, crea_k6_spread.py) -> ACCEPTED as Lead 3 with reservations.
- Dead: C14 CTA flips, C9 lone mover, LME copper official/close (crea_lme_copper.py), Treasury tier-1 (continues;
  crea_rates_tier1.py), opening-auction mirror (crea_open_auction.py), ECB decision fade (continues; crea_ecb_fade.py).
- No 5th lead met the bar; agreed with the conservative to stop at 4 rather than pad.

## C5 detail (scripts/crea_ah_shock.py, crea_postclose_fade.py, crea_postclose_season.py)

Fade the 16:00->17:00 (or 16:00->16:15) move of session S, entering at the 18:05 price of session S+1, exit at
10:00 (or 09:30). Size gate: |move| >= trailing 250-session q80 (pre-entry).
- post 16-17, q80, exit 10:00: NQ +$23.80 (n 415, med +8.50, t 2.33); ES +$12.40 (t 1.87); YM +$8.68 (t 1.38); RTY +$11.07 (t 1.98).
- q90: NQ +$44.16 (n 203, med +15.50, t 2.92); ES +$24.65 (t 2.32).
- Placebo hours (same entry/exit): 13-14 NQ +$16.58 (q90 +$42.10, t 2.70); 14-15 NQ -$8.74; 15-16 NQ +$17.98. => the
  overnight hold carries a general "big afternoon hour gives back by the next morning" component.
- Year split NQ q80: 2016 +4.6, 2017 -4.0, 2018 +11.5, 2019 +18.8, 2020 +0.5, 2021 +38.6, 2022 +86.8, 2023 +34.6;
  ex-2022 +$12.95; trimmed +$23.43.
- MECHANISM SPLIT (16:00-16:15 window, q80, exit 10:00), earnings season vs off-season:
  NQ +$32.59 (t 2.04) vs +$3.44; ES +$21.20 (t 1.92) vs -$0.92; YM +$10.27 vs -$0.66; RTY +$1.79 vs +$1.12.
  Dose-response matches mega-cap weight (NQ > ES > YM > RTY).
