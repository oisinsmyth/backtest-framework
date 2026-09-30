# D643 — RESULT: the shock classifier fails Gate 1 on all four instruments. GC, the one powered cell, is a clean null, and on the other three LIQ is a 2016–2020 label with its weight in March–April 2020

*2026-09-28. The principal: "build the D642 runner and run it". One run of `scripts/run_shock_signal.py` (committed
`906c501`, with the audit fix `8c2a67f`) under D642 (`0768da5`), SC-A1..A8, D641 and POWER (`2f6a2b3`). In-sample
2016-01-04 → 2025-02-28 on SC-A6's 2,282 usable sessions; nothing on or after 2025-03-01 was read.*

*Output: `data/shock/phase3_signal.json` (every number below unless named otherwise), `data/shock/trials.csv` (96
configurations), `data/shock/phase3_event_study.svg` (the event-study figure, `scripts/plot_shock_event_study.py`),
`data/shock/phase3_component_lines.json` (`scripts/shock_component_line.py`, descriptive). `--check` rebuilds it byte
for byte. The deposit's write-up is `docs/results/SHOCK_CLASSIFIER_REPORT.md`.*

*Before this run, a first `--run` stopped in its own lag audit, inside the loader and before any outcome was computed;
nothing was written. Re-detection reproduced D641's counts, but the check read D641's CSV back with a float parser
that is not round-trip. The check now compares the rebuild byte for byte and passed. No forward return was read before
the fix (`8c2a67f`).*

## Verdict (D642 §4; deposit §10)

**GATE 1 FAILED → STOP → write-up.**
- **H1 passes on no instrument.** NQ, ES and CL are **INCONCLUSIVE**: they were UNDERPOWERED before the run (§7A), so
  their nulls are not failures.
- **GC, the informative cell, FAILS** with a divergence of +0.28 bp (t 0.21). Its 95% interval, [−2.4, +3.0] bp, excludes
  the divergence that would pay GC's 4.5 bp cost.
- **H3 (Gate 2) fails on all four** (none needed it: Gate 1 did not pass). **H4 fails** per instrument and pooled.
- Phases 5 and 6 do not run. The deposit's §12 kill applies to the line as registered.

## H1: INFO − LIQ in the 30-minute move from the t0+1 fill, shock direction, CR1 by day

| | Δ bp | SE | t | Holm p | mean x INFO (n) | mean x LIQ (n) | predicted signs | LIQ 2024+ | POWER | verdict |
|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| NQ | −0.80 | 8.99 | −0.09 | 1.00 | −0.08 (3,048) | +0.72 (85) | no | 6 | underpowered | INCONCLUSIVE |
| ES | −16.47 | 11.17 | −1.47 | 1.00 | −0.21 (3,425) | **+16.26** (51) | no: LIQ **continues** | 1 | underpowered | INCONCLUSIVE |
| CL | +19.35 | 21.28 | +0.91 | 0.73 | +0.84 (3,163) | −18.51 (40) | yes | 0 | underpowered | INCONCLUSIVE |
| GC | +0.28 | 1.36 | +0.21 | 1.00 | +0.30 (2,035) | +0.02 (304) | no | 55 | powered at t = 2 | **FAIL** |

**SC-A2: neither class differs from the unconditional baseline** (all z = 4 shocks), on any instrument. INFO − baseline
is between −0.99 and +0.08 bp (|t| ≤ 1.09), and LIQ − baseline has |t| ≤ 1.48. The classification adds nothing to what
D528/D499 already measured on these one-minute moves.

**The calibration recorded before the run** (`906c501`): on synthetic random-walk prices H1's clustered t has sd 1.21,
not 1, because CR1 is mildly anti-conservative where one class is small. Every t here is below 1.5 in absolute value,
so the note does not bind in either direction.

## What the LIQ class is on NQ, ES and CL (the top trades, named)

- **CL: 23 of the 40 LIQ shocks fall between 2020-02-21 and 2020-05-01** (22 of them from 2020-03-13 on, with fills of
  $12–$32), and their moves reach ±550 bp:
  - the largest is 2020-04-21 11:11, a LIQ fade that lost 550 bp from a $14.55 fill;
  - the mean cost at those fills is 21 bp against CL's usual 9–10;
  - **ex-2020: n 17, mean +9.3 bp, median +1.7 bp**, against the cost of ~9 bp;
  - no LIQ shock after 2020.
- **ES: LIQ continues rather than reverts**, and not only in the crash:
  - the fade loses −16.3 bp on the mean and −7.5 on the median;
  - 19 of 51 are in 2020 (18 in March–April), the largest being 2020-03-12 12:39 at −456 bp;
  - **ex-2020 the fade still loses: mean −6.0, median −3.2 bp** (n 32).
- **NQ: LIQ is flat** (fade +0.72 bp; median +1.45).
- **LIQ after 2023 is almost empty on the three:** NQ 6, ES 1, CL 0. On them the label marks the 2016–2020 regime of
  low peer correlation, not a recurring event. GC's 304 LIQ shocks spread over every year, with 55 in 2024+.

## H2 (timing): not reached, reported

H2 passes for ES INFO, GC INFO and GC LIQ, whose curves peak after minute 5. The peaks are 0.24, 0.58 and 1.19 bp, at
most 27% of the cost. It cannot open Gate 1 without H1.

The curves (figure) say the same:
- **INFO's mean curve is within ±1.2 bp of zero for 60 minutes on every instrument;**
- LIQ's curves are wide and carried by 2020. CL's LIQ fade reaches +28 bp at k = 10 (band +10 to +49), then gives most
  of it back by k = 60 (+5.8). That is the 22 crash-period shocks, and in H1's x, measured from the t0+1 fill, H3
  cannot tell what is left from a random relabelling.

## H3 (label placebo, within instrument × year, 1,000 permutations)

| | observed Δ | p50 | p95 | SE(p95) | margin | rank | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| NQ | −0.80 | +1.01 | 8.06 | 0.32 | −8.87 | 0.33 | FAIL |
| ES | −16.47 | +0.25 | 8.49 | 0.34 | −24.96 | 0.00 | FAIL |
| CL | +19.35 | +1.91 | 27.48 | 0.86 | −8.13 | 0.86 | FAIL |
| GC | +0.28 | +0.19 | 2.71 | 0.12 | −2.43 | 0.53 | FAIL |

CL's +19.35 bp is at the 86th percentile of its own label placebo. With 40 LIQ shocks, 23 of them in one crash, a
Δ that large is what a random relabelling gives.

## H4 (dose-response): none

Spearman ρ(C, x):
- within INFO: −0.02 to +0.03 on the four (every CI spans 0);
- within LIQ: −0.05 to +0.09;
- pooled: INFO −0.00 [−0.02, +0.01], LIQ −0.01 [−0.11, +0.09].

## The four groups (CLAUDE.md), per class, trade direction, t0+1 fill, 30-minute exit

**1. Performance, net and gross** (bp; $ at one micro; cost = s.5.1: D508 + $3 + one tick; the mean round trip is
MNQ $4.57, MES $5.67, MCL $6.03, MGC $6.93):

| | gross bp | net bp | net 2× | gross $ | net $ | **breakeven round trip** |
|---|---:|---:|---:|---:|---:|---:|
| NQ INFO | −0.08 | −2.47 | −4.87 | +0.18 | −4.39 | $0.18 |
| NQ LIQ | −0.72 | −3.83 | −6.94 | +3.33 | −1.24 | $3.33 |
| ES INFO | −0.21 | −3.50 | −6.79 | +0.19 | −5.48 | $0.19 |
| ES LIQ | −16.26 | −20.74 | −25.21 | −18.31 | −23.98 | none |
| CL INFO | +0.84 | −9.72 | −20.29 | +0.14 | −5.89 | $0.14 |
| CL LIQ | +18.51 | −2.57 | −23.64 | +6.55 | +0.52 | $6.55 |
| GC INFO | +0.30 | −4.27 | −8.84 | +0.74 | −6.19 | $0.74 |
| GC LIQ | −0.02 | −4.38 | −8.74 | +0.27 | −6.67 | $0.27 |

(Gross bp and gross $ differ in sign on NQ LIQ and CL INFO because a bp mean weights every trade equally and a dollar
mean weights by price level. CL's 2020 fills were $12–$29.)

**Component lines** (`phase3_component_lines.json`; path-invariant daily $ series, every trade kept, √252, over every
usable session):

| | trades / yr | net Sharpe 2016–23 | net Sortino 2016–23 | gross Sharpe 2016–23 | net Sharpe full | ex-2020 | hit (net) | skew/trade | max \|ρ\| with K1–K6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NQ INFO | 337 | −1.24 | −1.60 | −0.19 | −0.97 | −0.69 | 0.454 | +0.11 | 0.13 (K4) |
| NQ LIQ | 9 | −0.02 | −0.04 | +0.09 | −0.03 | +0.09 | 0.482 | −0.25 | 0.04 |
| ES INFO | 378 | −2.28 | −2.75 | −0.25 | −1.96 | −1.88 | 0.435 | −0.18 | 0.07 |
| ES LIQ | 6 | −0.59 | −0.64 | −0.47 | −0.52 | −0.47 | 0.373 | −3.29 | 0.14 (K1) |
| CL INFO | 349 | −2.91 | −3.44 | −0.04 | −2.78 | −2.73 | 0.395 | +0.03 | 0.05 |
| CL LIQ | 4 | +0.04 | +0.06 | +0.46 | +0.03 | −0.03 | 0.475 | +0.50 | 0.06 |
| GC INFO | 225 | −2.42 | −3.06 | +0.27 | −2.18 | −2.20 | 0.370 | +0.55 | 0.05 |
| GC LIQ | 34 | −1.16 | −1.34 | −0.09 | −0.91 | −0.90 | 0.395 | +0.01 | 0.07 |

**No line is a component.** The one non-negative line, CL LIQ, has net Sharpe +0.04 on 4.4 trades a year (−0.03
ex-2020). Every line is uncorrelated with the ledger (|ρ| ≤ 0.14), so none would have been redundant, only empty.

**2. Trade distribution** (bp, trade direction):

| | n | mean | median | win | skew | kurt | ex-top 1% | ex-bottom 1% | both trimmed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NQ INFO | 3,048 | −0.08 | −0.49 | 0.492 | −0.21 | 5.8 | −1.49 | +1.52 | +0.11 |
| NQ LIQ | 85 | −0.72 | +1.45 | 0.529 | 0.00 | 15.5 | −5.20 | +3.87 | −0.60 |
| ES INFO | 3,425 | −0.21 | 0.00 | 0.492 | −0.25 | 6.8 | −1.41 | +1.09 | −0.11 |
| ES LIQ | 51 | −16.26 | −7.50 | 0.431 | −3.50 | 19.5 | −19.63 | −7.46 | −10.72 |
| CL INFO | 3,163 | +0.84 | −1.55 | 0.478 | +2.57 | 54.8 | −2.26 | +3.54 | +0.43 |
| CL LIQ | 40 | +18.51 | +4.92 | 0.525 | −0.40 | 1.9 | +7.80 | +33.08 | +22.47 |
| GC INFO | 2,035 | +0.30 | −0.77 | 0.475 | +0.37 | 5.1 | −0.71 | +1.22 | +0.21 |
| GC LIQ | 304 | −0.02 | −0.73 | 0.474 | −0.38 | 2.7 | −0.84 | +0.99 | +0.16 |

CL INFO's mean is above its median, carried by the right tail (the top trade is 2020-04-02 10:29, +1,386 bp from a
$22.80 fill). Its symmetric trim is +0.43 bp against a 10.6 bp cost.

**3. What the winners depend on:**
- **Era:** every LIQ result on NQ/ES/CL is a 2016–2020 result, and CL's and ES's are March–April 2020 results.
- **Price:** CL's cost in bp doubled at its 2020 fills (21 bp against 9–10).
- **2016–2023 vs 2024+:** INFO's gross mean is −0.34 → +1.47 (NQ), −0.57 → +1.81 (ES), +0.59 → +3.08 (CL) and
  +0.28 → +0.55 bp (GC). It is under every cost in both periods.
- **Robustness** (s.5; reported, never re-selected):
  - of the 76 H1 sensitivity rows, **three** have t ≥ 2;
  - **two carry the predicted signs:** CL's (0.7, 0.1) C pair (Δ +65.5 bp, t 2.55, **LIQ n 26**) and NQ's 2021
    (t 2.14, LIQ n 10);
  - the third, CL's high-liquidity tercile (t 2.45), has INFO negative and **LIQ n 4**;
  - over 76 rows and a t whose null sd is 1.21, that is what chance gives. The stress fill moves Δ strongly negative
  on every instrument (GC t −7.36), as it must: the worst of five closes is taken against each class's own trade
  direction.
- Event shocks: at most 178 per instrument, and LIQ there is structurally empty (§4.6's override makes an event shock
  INFO at C ≥ 0.3). Without events, nothing changes. CL's NGSR diagnostic changes nothing.
- The flow-profile feature is not computable in v1 (bars only, SC-A3).

**4. Nulls:** H3 above (p50, p95 and SE for all four); its verdicts do not depend on the SE (every margin is more than
2 SE below p95).

## What was learned

1. **On one-minute bars, a peer-confirmation ratio does not separate a shock that continues from one that reverts.**
   On GC, where there were 304 LIQ shocks and the test had power, the two classes' 30-minute moves are the same to
   within ±3 bp. Neither differs from the unconditional shock.
2. **The LIQ label is rare exactly where the deposit needed it common.** It fired on 1.2–2.3% of index and energy
   shocks (GC: 9.6%), those shocks clustered in the 2020 crash and all but vanished after 2021. The classifier's premise is that
   uncorrelated shocks are liquidity events, and on these markets it mostly picks out a market in crisis, whose moves
   continue (ES) or swing both ways (CL).
3. **INFO continuation is not a trade at the latency the bars allow.** The INFO curve is flat at ±1 bp for an hour
   from t0, with 225–378 trades a year and gross $0.14–$0.74 against a $4.57–$6.93 round trip.

The bars-only v1 (SC-A3) is what failed. The deposit's aggressor-flow feature was never available in-sample. Whether
a flow-signed classifier would separate the classes is not answered here.

## Programme slot 2 RELEASED by the principal, 2026-09-30

*The principal: "Release 1 and 2".*

- **Slot 2** ("shock classifier H1") is moved to `released` in `data/programme_registry.json` with its reason
  (`Registry.release`).
- **Why it is free:** the classifier failed Gate 1 on all four instruments in-sample (above) and never reached the
  vault, so no vault look is being given up.
- **This is the principal's override** of the deposit's never-retroactively default, as for H-O2 (D658). It
  applies to this family only, and the family can never be registered again.
