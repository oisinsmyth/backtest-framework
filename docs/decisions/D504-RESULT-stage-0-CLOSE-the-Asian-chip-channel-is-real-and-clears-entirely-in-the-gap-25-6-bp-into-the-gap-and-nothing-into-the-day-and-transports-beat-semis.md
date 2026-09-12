# D504 RESULT — stage 0, CLOSE: the Asian chip channel is real and clears **entirely in the gap**. It pays +25.6 bp into the semis' opening gap and nothing measurable into the day session, and a control sector with no mechanism beats semis on the traded cell

**Result of D504** (spec `7578140`, amended `0cf06db` before the run). Runner
`scripts/run_d504_asian_chip_stage0.py --run` (`--selftest` passes, eight checks; 0.1 min),
artefact `data/d504_asian_chip_stage0.json`, signal and returns
`data/d504_signal_and_returns.csv.gz`. **1,324 sessions on which all sixteen declared symbols have
26 bars, 2018-01-02 → 2023-12-29; 1,073 after the residual's warm-up; 2024+ RESERVED on the
15-minute fixtures and not read.**

## 0. The answer in one line

**The channel exists and the gap is where it clears.** Regressing the relative day session
(SMH − QQQ, 09:45 → 16:00) on the causal-standardised Asian chip signal and on the semis' own
relative gap, with Newey–West(5) errors, n = 1,073:

| | coefficient, bp per unit z | t |
|---|---:|---:|
| **the relative GAP on z(A_rel)** — for scale, a different regression | **+25.65** | **+4.25** |
| the relative DAY SESSION on z(A_rel) | **−1.65** | −0.64 |
| the relative day session on z(G), the semis' own gap | +5.64 | +2.28 |

A one-sigma move in Taiwan-and-Korea-relative-to-the-market is worth **+25.6 bp in the semis'
opening gap and −1.7 ± 2.6 bp afterwards.** The market prices the Asian chip session by 09:45 and
leaves nothing behind. Everything below is the trade-level confirmation of that one fact.

## 1. The cells (bp per trade of one leg, cash, both legs costed)

| cell | pair | N (/yr) | gross | median | ex-top 1% | ex-bottom 1% | cost X / big | net X / big / passive | hit | skew | kurt | z | N1 p95 (share ≥) | by year |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| **P1** the incremental residual | SMH/QQQ | 82 (20) | **+8.01** | +5.22 | +5.30 | +10.06 | 11.71 / 9.14 | **−3.71 / −1.13 / −1.13** | 53.7% | +0.15 | +0.30 | **+0.96** | +1.63 (16.7%) | +5.4 / −27.3 / +38.7 / −4.8 |
| P1_z the pre-registered z-difference | SMH/QQQ | 89 (22) | −11.64 | −18.54 | −13.56 | −9.68 | 11.71 / 9.14 | −23.36 / −20.78 | 40.4% | +0.04 | −0.09 | −1.54 | +1.75 (94.0%) | +15.9 / −30.4 / −4.0 / −31.7 |
| P2 raw continuation | SMH/QQQ | 73 (18) | +13.47 | +22.25 | +10.51 | +15.71 | 11.71 / 9.14 | +1.76 / +4.34 / +4.34 | 58.9% | +0.26 | +0.59 | +1.59 | +1.62 (5.9%) | −1.9 / −17.0 / +28.5 / +14.3 |
| **P3_IYT transports** (a control) | IYT/QQQ | 82 (20) | **+27.97** | +23.91 | +24.68 | +32.91 | 7.51 / 5.81 | +20.46 / +22.16 | 61.0% | −0.24 | +1.40 | **+2.26** | +1.64 (0.8%) | +58.8 / +23.0 / +34.0 / −14.0 |
| P3_KRE banks | KRE/QQQ | 82 | +14.89 | +26.82 | +8.33 | +21.87 | 11.89 / 10.01 | +3.00 / +4.88 | 58.5% | −0.57 | +3.98 | +0.90 | +1.66 (18.3%) | |
| P3_ITB homebuilders | ITB/QQQ | 82 | +13.47 | +19.85 | | | 10.92 | +2.55 / +4.34 | 54.9% | +0.31 | | +0.93 | +1.64 (17.2%) | |
| P3_IYR REITs | IYR/QQQ | 82 | +6.92 | +21.85 | | | 10.27 | −3.35 / −0.92 | 56.1% | −0.58 | | +0.51 | +1.64 (29.3%) | |
| P3_IBB biotech | IBB/QQQ | 82 | −3.92 | +7.26 | | | 9.48 | −13.40 | 53.7% | −0.34 | | −0.36 | +1.68 (64.1%) | |
| P3_OIH oil services | OIH/QQQ | 82 | −3.90 | −11.33 | | | 9.17 | −13.07 | 45.1% | −0.46 | | −0.18 | +1.64 (56.8%) | |
| P4_EU Europe | SMH/QQQ | 84 | −3.79 | −1.70 | | | 11.71 | −15.50 | 46.4% | −0.06 | | −0.43 | +1.63 (66.7%) | |
| P4_EWZ Brazil | SMH/QQQ | 78 | −6.09 | −5.57 | | | 11.71 | −17.81 | 46.2% | +0.04 | | −0.71 | +1.68 (76.6%) | |
| P4_EEM emerging | SMH/QQQ | 85 | −11.47 | −14.05 | | | 11.71 | −23.18 | 41.2% | +0.08 | | −1.36 | +1.63 (91.8%) | |
| N4_late wrong window | SMH/QQQ | 73 | −17.33 | −14.15 | | | 11.71 | −29.04 | 38.4% | −0.11 | | −1.96 | +1.65 (97.2%) | |

**N2 family maximum, eleven cells, 1,323 exact common offsets:** p50 +1.44, **p95 +2.56**, p99
+3.15. **Observed maximum +2.26 (P3_IYT, a control); 10.2% of offsets reach it. Nothing clears the
family bar.**

**Cost lines.** Corwin–Schultz half-spread from each symbol's own 15-minute OHLC: SMH 2.1 bp, QQQ
1.8, IYT 0.0 (the estimator floors at zero and so flatters IYT's net by ~4 bp). Commission is IBKR
Fixed and the **$1 order minimum binds on a $10k leg**, so commission is a flat 1.0 bp per leg
there and 0.2–0.5 bp at $50k. The passive line charges commission only. **The verdict does not turn
on the cost model:** P1 is negative on all three lines and no cell clears its own rotation null.

## 2. What the result says, in four parts

**(a) The primary is noise and its own by-year figures say so.** P1 earns +8.01 bp on 82 trades
with an SE of 8.37, so it is one standard error from zero, and its yearly means alternate sign
every year: +5.4, −27.3, +38.7, −4.8. Its z of +0.96 sits at the 17th percentile of its own exact
rotation. Break-even against the crossed line needs a 59.9% hit rate and it gets 53.7%. **The
effective trading window is 2020–2023, four years, because the residual's 250-session fit and the
threshold's 250-session quantile together consume the first two years of a fixture that starts in
2018.** That is the sample cost of an honest causal construction and it is the main limitation of
this record.

**(b) The amendment was not cosmetic and it did not manufacture the answer.** The pre-registered
z-difference, retained as `P1_z`, comes out at **−11.64 bp with z −1.54 and a 40% hit rate** on
real data, the same wrong sign the synthetic predicted. Had it been run as written, the record
would have reported a spurious *negative* cell and invited a short-semis story. The known-answer
check is what caught it, before any real outcome was read.

**(c) A control sector with no mechanism wins, which is what a family of twelve does.** The largest
cell in the study is **transports against the Nasdaq at +27.97 bp, hit 61%, clearing its own null
at the 0.8th percentile** — on a signal built from Taiwanese and Korean semiconductor gaps. Banks
and homebuilders also beat semis. There is no chip channel into IYT; this is the family maximum
doing its job, and it is why the family bar exists. Three of six control sectors exceed SMH in
absolute size, as predicted. **The one cell that would have been called a find under single-cell
scoring is a control.**

**(d) Every control behaves.** The wrong-conditioner cells are all negative and inside their nulls
(Europe −3.8, Brazil −6.1, emerging −11.5), the wrong-window cell is −17.3 and does not predict
positively, and the partner-randomised control puts SMH-against-QQQ's +8.0 bp in the middle of a
±20 bp spread over fifteen partners (IBB +11.9, OIH +11.9, EWY +8.5, **QQQ +8.0**, SPY +3.6, down
to IYT −20.0). The +8 bp is unremarkable among partners.

## 3. The prop arm, and the vehicle question it answers by accident

**P5, MNQ vs MES on P1's signal: 82 trades, gross −$13.76 (SE 22.50), net −$19.76 against a $6
round trip, hit 40.2%, net Sharpe −0.38, worst day −$670, ρ with K8 −0.15.** Dead, and the prop
accounts are futures-only, so this line produces no prop component. The dollar beta of NQ on ES is
**1.72**, so one MNQ against one MES is *not* market-neutral: it carries residual long-index
exposure of about 0.7 MES-equivalents.

**One measurement here outlives the signal, and it speaks to what D503 found binding.** D503
established that at 2026 prices a single MNQ has a daily σ near $340 against a $50k account's
$2,000 trailing floor, so the micro itself no longer fits the floor and the prop constraint is now
a vehicle question. On the unconditional day session over this window:

| | daily σ | 2023 only | days beyond −$1,000 per year |
|---|---:|---:|---:|
| one MNQ, 09:45 → 15:59 | $282 | $273 | 0.2 |
| the MNQ/MES pair, same window | **$128** | **$135** | **0.0** |

**A market-neutral micro pair is the one futures construction whose dollar σ falls below a single
micro's rather than rising** — less than half, and stable across the price-level change that
doubled the single micro's σ. That does not rescue anything here, because the pair needs an edge
and this signal has none. It is recorded because the vehicle question now gates the prop book, and
a hedged pair is the only sub-micro exposure CME offers. Sizing it properly is its own record: the
beta of 1.72 means the integer choices are 1:1, which under-hedges, or 1:2, which over-hedges and
costs $9.

## 4. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | M1's incremental coefficient on z(A_rel) in [−6, 0] bp, \|t\| < 2 | **−1.65 bp, t −0.64** | right |
| X-b | P1 140–160 trades, gross in [−8, +8] bp, does not clear the family bar; \|P2\| < \|P1\| | 82 trades, +8.01 bp, family not cleared; **\|P2\| 13.5 > \|P1\| 8.0** | trade count wrong (the double warm-up), gross at the edge of the range, family right, P2 ordering wrong |
| X-c | P3 sectors scatter ±10 bp, ≥ 2 of 6 exceed SMH | spread −3.9 to +28.0, **3 of 6** exceed | right on the count, the spread is wider than predicted |
| X-d | the three P4 cells inside N1; EEM closer to P1 than Europe | all three inside; \|EEM − P1\| 19.5 vs \|EU − P1\| 11.8 | first half right, second half **wrong** |
| X-e | P5 gross under $6; ρ(P5, K8) in [0.1, 0.4] | gross −$13.76; **ρ −0.15** | cost right, correlation wrong in sign |
| X-f | the verdict is CLOSE | CLOSE | right |

## 5. What stands

- **CLOSE recommended for the Asian-chip-into-US-semis line**; the principal closes. The mechanism
  is real, it is semis-specific, and it is **fully priced in the opening gap**: +25.6 bp into the
  gap at t +4.25, −1.7 ± 2.6 bp into the day. There is no residual for a 09:45 entry to collect.
- **This is the fourth independent route to the same ceiling.** The last half-hour (D487), eighteen
  cross-instrument and sentiment cells (D494), the hourly clock on eight roots (D499) and now the
  cross-sectional Asian channel all end at one tick or less of collectable edge on the US day
  session. The routes share no data, no clock and no instrument.
- **For the goal that started this line — a second prop component — nothing is added.** The cash
  pair is personal-book-only by venue, and it has no edge; the futures expression has no edge and
  the wrong exposure. K8 did not transfer (D503), so the prop ledger has no live entry.
- **Kept as measurements** (to FINDINGS): the gap-versus-day decomposition of the Asian channel;
  that the volume-thin partition and the US-clock partition are different objects (D499) and
  likewise that the Asian *level* and Asian *relative* signals are different objects, since both NQ
  and ES load ≈ 0.5 on the Asian session; and the micro-pair σ measurement above.
- **Spent:** nothing. 2024+ on the 15-minute fixtures is unread and this line has never touched it.
  Note that the futures 2024+ day session is spent by D503, so **P5 could never be given a forward
  read even if it had worked.**

## 6. Files

Runner · this record · the artefact · `data/d504_signal_and_returns.csv.gz` · the ledger row ·
PICKUP · FINDINGS.
