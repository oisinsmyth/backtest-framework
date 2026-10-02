# Conservative notes (Opus pair)

## Audit checklist (applied to every lead, mine and the creative's)

A1 SIZE: gross $/trade at ONE micro >= micro RT (MES 4.42, MNQ 4.07, MYM 3.80, M2K 3.76, MGC 5.93, SIL 8.00,
   MHG 4.25, MCL 5.03, MNG 4.00 [one-tick convention; real MNG spread likely wider], M6E 4.38, MBT 4.31).
   Cost in bp of notional: MNQ ~1.2, MES ~1.8, MGC ~3, SIL ~3, MCL ~6, MNG ~13 -> energy micros need big moves.
   Passive entry recovers only ~2/3 of crossing (D770). Gross must clear ~1.3x RT to be a lead.
A2 MOMENTUM IN DISGUISE: does the fade's sign survive if the predictor is replaced by the move itself?
   Report the unconditional follow vs fade at the same clock.
A3 ERA: year split; mean ex-2020 and ex-2022; no single year > 40% of P&L.
A4 LOOK-AHEAD: predictor dated strictly before entry; bar stamps are bar START (Databento ohlcv on ts_recv);
   entry at the close of the trigger bar or later; event calendars are schedules (no unannounced delays).
A5 NULL: same-clock placebo on non-event days; rotation where the trigger is a series; mean beside median.
A6 DECAY: first half vs second half of in-sample (2016-19 vs 2020-23); flows that deepen markets fade (D685).
A7 RARE/LUMPY: >= ~25 events/yr per instrument; top trade and top-5 share of P&L.
A8 MULTIPLE TESTING: count the cells I looked at; report every cell, not the best one.
A9 BRACKET: win rate vs mean; median > 0 with mean < 0 is the D752 tell.
A10 CLOSED-RECORD: nearest D-number and the stated, testable difference.

## Candidate list (Phase 1)

(see below, updated as tests run)

### K1 (mine, POSITIVE premise): fade the CPI/NFP 08:30 impulse on the index micros, exit 11:00
- scripts/cons_macro830_fade.py, cons_macro830_robust.py, cons_macro830_fade_ymrty.py; out/cons_macro830_*.
- Data: fut_opening_globex_1m (ES/NQ, YM/RTY), sessions 2016-2023; events.csv CPI+EMPSIT at 08:30 (192 events).
- Pre = close 08:29 bar; impulse = close(08:34) - pre; enter 08:34 close; exit 11:00 close; fade.
- NQ: n186 mean +$34.88/MNQ med +12.75 t 2.73 win .56; trim +33.87; exTop 27.57; 16-19 +8.20, 20-23 +61.56;
  ex2022 +34.73; CPI +33.6 NFP +36.2; 7/8 yrs >0.
- ES: +$16.69/MES t 2.18 med 6.25; YM +$10.07/MYM t 1.73 (7/8 yrs); RTY +$8.36/M2K t 1.15.
- Placebo (non-CPI/NFP weekdays, same clock): NQ -3.32, ES -0.93; top-third impulses on placebo days:
  NQ -8.63, ES -7.03 (big non-tier-1 08:30 moves CONTINUE).
- Cells: 15 per root x 6 roots. K=1 fails everywhere. Reversion mostly 09:30-11:00 (NQ 08:34->09:29 only +5.33).
- Concerns: 24 events/yr (borderline rare); $ size grows 2020-23 (price x vol); does not generalise to ISM 10:00.
- NULLS (cons_macro830_null.py): random non-event weekdays (4000 draws): NQ p50 -3.26 p95 13.41 (SE .35) score 34.88
  rank 1.000; ES p50 -0.83 p95 8.82 score 16.69 rank .9985. Matched-|impulse|-decile null: NQ p50 -11.79 p95 11.65
  rank .9995; ES p50 -6.31 p95 9.13 rank .996. Decisive on both.
- FOMC 14:00 (cons_fomc_fade.py): same sign, t<1.7, 2022-carried; rare. Not standalone.

### K6 (mine): gold weekend reopen fade (cons_reopen_gap.py, cons_gc_offhours.py)
- Only GC's reopen window (prev 16:59 -> 18:59) reverts; other GC off-hours windows do not (22:59->01:59 continues).
- Monday all to 10:59: n390 +$15.93/MGC med 8 t 2.31 8/8 yrs; ex22 17.23; 16-19 8.01. Monday q80 +$35.15 t 2.59.
- SIL does not confirm. Index Monday reopens: nothing. CL Monday q80 +30.80 t 1.56.

### Lead-2 placebo (cons_index_overnight_windows.py): other cash-shut windows (18:05-19:59, 19:59-21:59, 21:59-02:59,
02:59-03:59, 03:59-08:29) faded to 10:59 at q80, ex CPI/NFP days: no clean reversion (t -1.0..+1.95; 21:59-02:59
weakly positive on all four). The 16:00-17:00 window is special.

### Lead-5 hunt (after the main session's instruction)
- P1 pre-open non-release fade (cons_preopen_fade.py): dead (ranks 0.16-0.92).
- P2 index weekend reopen -> Europe open (cons_index_weekend.py): NQ 2.5x RT rank .961; ES 1.5x; RTY/YM nil;
  unconfirmable (NQ/ES overnight 2024+ spent). Not proposed.
- P3 grains overnight gap fade (cons_grain_gap.py): dead; big overnight grain moves continue.
- P4 vol-target close pressure (cons_voltarget.py): ES trigger +$19.40 but ex-2020 +$1.19; NQ ex-2020 -0.89. Dead (2020).

### K2 (mine, NEGATIVE): EIA 10:30 release fade, CL/NG. scripts/cons_eia_fade.py
- 45 cells per root. CL best: K=2 exit 12:30 +$9.29 t 2.07 (best of 45). NG storage CONTINUES. Not a lead.

### K3 (mine, NEGATIVE): ISM 10:00 (BD1 mfg, BD3 svc) fade NQ/ES. scripts/cons_ism1000_fade.py. Mixed signs.

### K4 (mine, UNPROBED): CME velocity-logic / pause events (status schema) -> post-pause reversion.
- status 2019 = 34M records, 6 min decode; action 8 (Halt) 590k, reason 3 (market event) 444k, mostly options.
  Prior low: front-month pauses are rare/lumpy and inside a 1-min bar.
