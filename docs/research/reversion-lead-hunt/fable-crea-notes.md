# Creative notes (Fable pair)

All tests: in-sample <= 2023-12-29 (asserted in every script), dollars per ONE micro, bar-close fills.
Scripts: `scripts/crea_*.py`; outputs `out/`.

## Candidate list (>= 10)

| # | effect | status |
|---|---|---|
| A | CME Stop Logic / Velocity Logic reserved-state pauses (status schema) -> fade the cascade on the PARENT | DEAD: front-contract events rare (ES 18, NQ 35, YM 18 in 8 yrs) [crea_04, crea_06] |
| A' | the MICRO's own stop-logic pauses: micro displaced from parent, arb pulls back | running [crea_09] |
| B | cross-index residual reversion ES/NQ/YM/RTY (common factor removed) | DEAD unhedged: ES +$1.86 (2020/22), hedged residual real (t 6.3) [crea_03] |
| C | TAS-offset-signed settlement fade MCL/MNG (TAS premium -> buying into 14:28-14:30 -> fade) | to run [crea_07 decoded TAS; crea_10] |
| D | Tokyo 09:55 fix on 6J/MJY (Ito-Yamada) | partner C7 dead at hourly; 6J 1-min decoded, not run |
| E | SHFE 15:00 Beijing close forced flattening -> COMEX GC/SI/HG | DEAD: GC +$1.20 (bounce), placebo clock same rho; SI/HG wrong sign [crea_05] |
| F | micro/parent volume share as retail-crowding conditioner (MES/ES, MNQ/NQ) | running [crea_08] |
| G | European cash close 11:30 ET hedge unwind on ES/NQ | untested; likely D762's generic noon reversion |
| H | macro-release first-minute overshoot (CPI/NFP 08:30, FOMC 14:00) | untested; partner's C6 (EIA) dead |
| I | WM/R 16:00 London fix daily on 6E | partner C5 dead (rho -0.10, $1.35) |
| J | BTC futures vs spot basis (MBT) | partner C2: real, break-even at the tail |
| K | LME ring clocks on HG | partner C3: generic London-morning reversion |

## Results log

- crea_03 (B): ES n=5136, rho(z, own fwd) -0.026, gross +$1.86 t 3.4, median 0, net -$2.56; 2020 $4.62, 2022 $3.70, other years < $1.4. NQ -$0.90. YM +$0.51. RTY -$0.09. Hedged residual ES +0.50 bp t 6.3. => spread effect, not micro.
- crea_05 (E): GC 07:00 UTC rho -0.096 (t -4.2) gross +$1.20 median $1.00; 05:00 UTC placebo rho -0.110. SI +0.051, HG +0.043 (wrong sign). CN-holiday control n=126 gross +$2.82 (no vanish). DEAD.
- crea_04/06 (A): census 27,179 pause events 2016-23; front-contract events ES 18, NQ 35, YM 18. NQ H15 +$16 t 0.8 n=34. Frequency fails.
- crea_07: TAS 1-s bars decoded; price = offset in ticks (0: 89%, +/-1: 8%); CLT 770k bars, NGT 572k; TAS volume peaks 14:00-14:30 ET.
- crea_08 (F, micro share): ES/NQ nothing; NQ RTH z_top H15 $2.19 (t 1.7) vs z_bottom $0.15, H30 $3.48 vs -$2.51 but 2020-carried ($9.72), dose not monotone. DEAD.
- crea_09/09b/13 (A', micro pause): MNQ 117 front events (25/yr, 62 in 2020); 1-min 'basis trade' +$21 t 1.9 top trade 31%; on 1-s bars the basis at resume+2s has median 18.5 ticks and the pre-event control 'reverts' at t 4-5 => contract mismatch / stale prints. WITHDRAWN.
- crea_10/10b (C, TAS CL/NG): sign chain's first link falsified (rho(W_late, window move) -0.08 CL / -0.21 NG; W tracks the 14:00-14:30 move +0.24). Fade -sign(W) top tercile: CL y $2.86 (t 2.7, rot p95 $1.65), y2 $3.74 (t 2.7); all non-zero days $1.54 (t 3.0); dose monotone; eras 2017-19 -1.25 / 2020-21 +3.90 / 2022-23 +3.29; uncond window fade $0.09. NG 2022-23 only ($5.49). Post hoc: discount quintile long y2 $6.24 (t 3.5, 37/yr, 2020 38%); Fridays flat (LO weekly expiry), Mon-Thu y2 ~$5.0. 0.74x cost => NOT a lead under the agreed bar; the best-evidenced outside-information signer found.
- crea_12b: the ohlcv-1m archive is ALL_SYMBOLS: TAS for GC/SI/HG/PL (GCT/SIT/HGT/PLT), BTIC EST/NQT/YMT, TACO ESQ/NQQ, ZBT, BZT/HOT/RBT exist 2016-2023. Decoded by crea_14 -> out/crea_tasbtic_1m.parquet. CL/NG 1-s 14:20-15:00 decoded by crea_15.
- Partner handed back with AGREED.md = 0 accepted (harness-forced) before N1-N3 ran.
- crea_17 (N1 BTIC close): ES rho(dB, y10) -0.016, fade $0.51; NQ 0; YM $1.78 (t 2.3) vs $3.80; TACO thin. DEAD. BTIC volume predicts |y10| size only.
- crea_16 (N2 metals TAS): GC $3.31 (t 2.8) vs $5.93; HG wrong sign; SI top tercile y30 $9.75 (t 3.7), y60 $12.35 (t 3.3), delayed-entry $8.82 (t 2.6), but 2020 = 53% of total, 2022-23 -$4.30, top-10 = 58%, and the raw window-move fade earns the same on the same days ($12.76). Agreement cell $20.13 (t 4.0, n 265) post hoc. NOT a lead.
- crea_18 (N3 1-s overshoot vs settlement VWAP): rho ~0, fade -$0.3..-$0.5. DEAD. TAS fade at 14:30:01: CL $2.83 (t 2.6), NG $3.68 (t 2.6).
- Resumed on the main session's instruction (must reach 5, no padding):
- crea_19/23/25/28 (R1 flow-sized MNG post-settlement fade, D630's |I|): dose monotone, pooled top tercile y60 $7.94 (t 4.2), walk-forward $6.05 (t 4.0) but ex-2022 $2.55; vol-gated (sd20 >= $30) $13.16 gross, NET 74-85% 2022, 9/10 top trades 2022. FAILS year concentration. Effect = 0.1-0.3 sd/trade.
- crea_21 (L1 Mon-Thu): MCL 1529 hold $5.05 (t 3.0) 1.0x but top-10 61%, 2020 41%. FAILS. SIL agreement cell inherits 2022-23 decay.
- crea_24/27 (LETF post-close reversal, fade the day's direction 16:00->16:05): NQ WF top tercile $5.10 (t 3.3) 2022 = 64%; ES $3.41 (t 4.0) every year positive, 0.77x cost. Clock-specific (15:00 control negative). FAILS.
- crea_22/26 (CL front vs second month): rho ~0. DEAD.
- crea_20: quotes — XNAS.ITCH imbalance top-25 names 2018-05..2023 $25.97; ALL_SYMBOLS $10,742; GLBX ES trades 2016-23 $850.
- Partner: SIL vol-gated fade retracted (2021 = 69% of net, Reddit squeeze); GLD premium proxy (T9) nothing; G1 withdrawn.
- FINAL: 0 leads meet the agreed bar after ~60 primary cells. Structural: relative-size reversions (0.1-0.3 sd) vs fixed-dollar cost pay only at 2-3x normal sigma; ex-ante gates select 2020-22. TAS/BTIC/TACO tapes are the repo's first outside-information signers (t 2.6-3.7, sub-cost).
