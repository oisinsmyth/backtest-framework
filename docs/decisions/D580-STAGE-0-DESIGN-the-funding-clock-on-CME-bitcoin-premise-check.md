# D580 STAGE 0 DESIGN — **the funding-cycle premise on CME bitcoin: does the perpetual funding clock show in CME bitcoin activity at 00, 08 and 16 UTC, and does the published funding sign order the move after it?** A premise check against the construction's own placement null, on 2017-12 → 2023-12, with the level path of the conditioner declared; no reserved session read

**Stage 0 design, committed before the runner and before the one-minute bitcoin fixture exist.
Diagnostic on 2017-12-18 → 2023-12-29; no CME bar from 2024-01-01 on is read; no quote, no cost,
no book.** Nothing admitted (R15).

*2026-09-20. `FUNDING_CYCLE_BASIS.md` derives a scheduled, price-insensitive cash flow — the
perpetual-swap funding payment at 00:00, 08:00 and 16:00 UTC — and a behavioural response to it
(the paying side reduces before the settlement and re-establishes after), transmitted to CME's
dated bitcoin futures by arbitrage with a lag. Its §4 says the study has an edge only if the
reversion is concentrated around the funding timestamps and signed by the funding rate, and its
§9 makes "no funding-time concentration" terminal. That is a premise, and this repo's rule is to
measure a premise before building on it ([[stage-0-premise-check]]). The D578 post-mortem adds
the second rule this design carries from the start: a pooled statistic taken forward is the
average of its regimes, so the era split and the level path of the conditioner — funding
magnitude and perp open interest by year, the deposit's own open question 1 — are declared
here, with a bar the last in-sample year must clear on its own.*

**What is on disk.** The funding fixture [D579](D579-FIXTURE-perpetual-funding-rates-and-open-interest-three-venues.md):
Binance USDT-margined BTC and ETH from 2019-09-10 / 2019-11-27, Bybit inverse BTC from
2018-11-15 (the deepest), Bybit linear from 2020-03-25, OKX three months deep; Bybit daily open
interest from 2020-08-04; a third to a half of every series sits at the venues' +0.01 % default. CME bitcoin (BTC, 5 BTC, tick $25) one-minute bars from 2017-12-18 and Micro Bitcoin
(MBT, 0.1 BTC, tick $5) from 2021-05-03, both inside the raw `ohlcv-1m` archive (every instrument,
2010-06 → 2026-09-10), not yet a fixture. The breadth hourly fixture carries BTC by session but at
an hour it cannot see a thirty-minute window, so this design names a one-minute fixture first.

---

## 0. The fixture this design needs, built and gated before the runner reads it

`scripts/build_fut_btc_1m.py` → `data/fixtures/fut_btc_1m.csv.gz` (gitignored by pattern, carried
in the manifest by hash; meta tracked). BTC and MBT outright bars at one minute, **every session,
keyed in UTC** (the funding clock is UTC; ET only for the CME halt), front month per (root, CME
trade date) by measured daily volume exactly as D462's chunk function does it (`ids_of` windows,
never a flat id map — D520), no stitching, no adjustment. Columns: root, contract, ts_utc (bar
start), open, high, low, close, volume, trade count. Gates in its meta: (G1) the front contract
per session equals the breadth fixture's `contract` for BTC on every common session; (G2) no bar
with a zero or `UNDEF` price (D526's two sentinels); (G3) bars per session within the CME crypto
hours (23 h less the daily halt) with the count profile by weekday reported; (G4) the MBT front
settle within 0.1 % of BTC's at every common minute-close with both present (the micro quotes the
parent's price); (G5) the first and last session, and the sessions absent, listed. **The builder
writes the whole archive; the runner filters `ts_utc < 2024-01-01` and asserts the first bar it
reads.** Decode on the system interpreter (databento lives there, D448/D462), one pass over the
26 files cached per file; projected 10–20 minutes on six workers, stated before launch.

## 1. The quantities

- **The clock.** Settlements *S* at 00:00, 08:00 and 16:00 UTC, seven days a week. **The CME set**
  is the settlements that fall inside CME crypto trading hours (Sunday 22:00/23:00 UTC open to
  Friday 21:00/22:00 UTC close by DST, with the daily hour's halt): Monday–Friday at all three
  times, so 15 a week less exchange holidays, ~4,700 events over the six years. A settlement is
  in the set only if the minute bars exist on at least 50 of the 60 minutes in [S−30, S+30);
  the count dropped is reported (audit (a)).
- **The minute profile.** For each event, per-minute volume *v*, trade count *n* and squared
  one-minute log return *r²* from S−120 to S+120, on **BTC** (the deep series; MBT from 2021-05
  reported beside, the same profiles). Each event's profile is normalised by its own **cycle
  mean** — the mean of the same quantity over the 480 minutes of the funding period ending at S —
  so a volume regime does not weight the years.
- **The move.** `r_pre = log P(S) − log P(S−30)` and `r_post(h) = log P(S+h) − log P(S)` for
  h = 15, **30 (primary)**, 60 minutes, where `P(t)` is the close of the minute bar that ENDS at
  *t* (D462: ts_event is the bar start, so the bar starting at S−1 min closes at S; the runner
  asserts this on a known-answer event, audit (d)).
- **F1, the funding rate.** The rate settled at *S* on **Binance BTCUSDT** (primary, 2019-09 →),
  the Bybit inverse BTCUSD rate for the 2018-11 → 2019-09 extension, and the cross-venue mean
  where both exist, reported beside. The rate settled at *S* is the time-average of the premium
  over the period ending at *S*, so it is known to within the last minutes' contribution before
  the event, not published in advance as the deposit says; **the strictly-known-in-advance
  variant, the rate settled at S−8h, is reported beside and must agree in sign on ≥ 80 % of
  events (its autocorrelation is the premise's own persistence, [[stage-0-premise-check]]).**
  **The default rate:** venues clamp the rate to exactly +0.0001 when the premium is near zero;
  the share of events at the default is reported by year and **T2–T3 are run with defaults
  excluded** (a default carries no sign information; the sign of the default is always positive
  and would bias a signed mean).
- **The signed move.** `y_pre = −sign(F1) · r_pre` and `y_post(h) = sign(F1) · r_post(h)`, both in
  basis points, both predicted **positive** by the derivation (§2: positive funding → selling
  before, reversion after). Sign convention proven on a synthetic path before any real number
  (audit (b)).
- **F5.** Bybit linear BTCUSDT open interest on the UTC day of *S* times |F1|, 2020-08 → 2023-12
  only, in terciles.

## 2. The tests, with predictions

| # | test | statistic | predicted | falsifier |
|---|---|---|---|---|
| **T1 — concentration** (the deposit's §4, kill 2) | the mean normalised volume, trade count and *r²* inside [S−30, S+30) over the CME set, against **the construction's own placement null**: the same 60-minute window placed at every 5-minute offset through the 480-minute funding cycle, **96 placements, enumerated (SE 0)**, offset 0 being the funding clock | **rank ≥ 0.95 for volume AND for *r²*** (top 5 of 96); the peak of the ±120-minute profile within ±5 minutes of *S*; and, within the null, the funding placement beats the **seven other top-of-hour placements** (k = 60 … 420), which is the top-of-the-hour effect controlled by construction | rank < 0.95 on either, or the peak elsewhere → **the clock is not on CME at this resolution. TERMINAL** by the deposit's own kill 2 |
| **T2 — the sign orders the move** ([[test-the-statistic-not-just-the-story]]) | mean `y_post(30)` in bp over the CME set with defaults excluded, with the block-bootstrap SE by week; against two nulls: (i) the **same placement null** (the sign of F1 attached to the window at each of the 95 other offsets — a sign attached to a non-funding window should order nothing) and (ii) the **event-shift null**, F1's sign series shifted by k events, k ∈ [8, N−8], enumerated | **`y_post(30)` > 0, ≥ 2 bp (the MBT tick is ~1–2 bp on a $30–60k price), rank ≥ 0.95 in both nulls; `y_pre` > 0 beside**; h = 15 and 60 of the same sign | `y_post(30)` ≤ 0 or inside both nulls → the clock is visible but the funding sign is not its direction (the deposit's kill 3: "sign-inconsistent with F1") |
| **T3 — magnitude orders it** | `y_post(30)` by |F1| tercile (defaults excluded); Spearman of |F1| with `y_post(30)`; the same by F5 tercile on 2020-08 → 2023-12 | monotone in |F1|, Spearman > 0; the top tercile ≥ 2× the bottom | flat in |F1| → the flow does not scale with the payment; diagnostic, no gate |
| **T4 — the level path and the era split** (the D578 lesson; the deposit's open question 1 and kill 4) | by year 2018 … 2023: mean |F1|, share at the default, share negative, Bybit OI (from 2020-08), BTC volume in the window, and **T1's rank and T2's mean with its SE computed within the year** | **T1 holds (rank ≥ 0.95) in ≥ 4 of 6 years, and T2 holds in 2023 on its own at rank ≥ 0.90** (the last in-sample year is the one the forward slice continues) | T2 holds only in 2021–2022 → decayed with deleveraging (kill 4): **NOT SUPPORTED for any forward test**, whatever the pooled number says |
| **T5 — which settlement** | T1 and T2 per settlement time (00, 08, 16 UTC) | all three show the clock; **the 08:00 UTC cell is flagged as confounded from late October to late March, when it coincides with the London cash open (08:00 GMT)**, and the record reads 00:00 and 16:00 UTC as the clean cells | 08:00 UTC alone holds → the London open, not funding |

**Decision rule, declared.**
- **SUPPORTED** — T1 holds pooled and in ≥ 4 of 6 years; T2 holds pooled and in 2023 on its own;
  at least one clean settlement time (00:00 or 16:00 UTC) holds both. Next, in separate records
  and in this order: the cost gate **per settlement time** at the funding timestamps on the
  `tbbo` quotes (2025-09-11 → 2026-09-11 — a quote read inside the reserved period, no return;
  **put to the principal before it is read**); then the spread-basis fixture (Binance perp mark
  and spot one-minute klines, a free fetch) for the deposit's F3; then the pre-registration of the
  fade on MBT.
- **PARTIAL** — T1 holds, T2 fails. The clock reaches CME but the funding sign is not the
  direction. No construction follows; the record says what the clock does carry (the unsigned
  activity and variance profile) and stops, the deposit's kill 3.
- **NOT SUPPORTED** — T1 fails, or T4's 2023 bar fails. Terminal, the deposit's kill 2 or kill 4.

**Chance.** T1's null is exact and its bar is one-sided at the 5 % of 96 placements; T2 has two
nulls, both enumerated; T4's yearly bars are declared before the run. The joint claim is a
concentration, a sign and a persistence, on three statistics.

## 3. Reported beside, diagnostic, unpromotable

The full ±120-minute profiles (volume, trade count, *r²*, and the signed cumulative move) as
arrays in the artifact, per settlement time and per year; MBT's profiles from 2021-05 beside
BTC's; ETH/MET from 2021-12 as a count-limited analogue with no gate; the cross-venue mean F1 and
the S−8h rate in place of the Binance rate, sign agreement reported; the default-rate share by
year; the trimmed means of `y_post` (1 % both tails) beside the mean and median
([[tail-carried-per-trade-edge-does-not-book]]); the weekday profile (Monday's 00:00 UTC follows
the Sunday reopen and is flagged).

**Audits, each proven to RAISE on a break that hits what the assertion reads:** (a) the CME set
by a second path — the bar-presence rule recomputed with pandas resampling, never the runner's
index arithmetic; break = one settlement moved into the Saturday gap; (b) the sign in money — a
synthetic price path with an injected post-settlement move in the funding-sign direction must
give `y_post` > 0 and its negation < 0; (c) the F1 attachment by `merge_asof` against the
runner's dictionary lookup; break = the rate series shifted one settlement; (d) the bar-end
convention on a known-answer event — the bar whose close the runner calls `P(S)` starts at
S−1 minute; (e) right quantity — the volume profile and the *r²* profile are different arrays,
and the placement null's zero offset reproduces the observed T1 and T2 exactly. `REQUIRED_OUTPUTS`
guard in the runner, checked before any number prints ([[declared-outputs-need-a-guard-not-prose]]).

## 4. What is read, and what is not

The one-minute BTC bars 2017-12-18 → 2023-12-29 and MBT bars 2021-05-03 → 2023-12-29, from the
fixture in §0; the funding fixture's settlements to 2023-12-31 23:59 UTC (the fixture holds to
2026-09-20; the runner filters and asserts its last settlement read); Bybit open interest to
2023-12-31. **Not read: any CME bar, quote or settlement from 2024-01-01 on; no cost; no book; no
P&L.** `y_post` is a 30-minute return of the underlying signed by a public series — the premise's
own statistic, with the placement null as its control (the same window elsewhere in the cycle:
[[stage-0-carries-the-always-on-control-per-positioned-day]]) — not a construction. **Seen-ness
declared:** D562's trend forward read saw BTC's daily closes 2024-01 → 2026-09; that slice is
unread by this line at any resolution, and the reserved slice for the funding line is 2024-01-01
→ 2026-09-10 at one minute ([[holdout-multiplicity-is-per-line]]).

## 5. What this record does not do

It does not build the spread F3 (needs the perp mark and spot at one minute; a free fetch,
named above as the step after SUPPORTED), F4 (aggressor flow needs `tbbo`, 2025-09 on only), or
the cost gate (quotes inside the reserved period; the principal's word). It does not test ETH as
a gate (the count is a third of BTC's). It does not size anything, does not read a prop firm's
crypto rule (the deposit's §10 says verify per firm), and does not decide between the pre-move
and the post-move as the construction — that is the pre-registration's choice, made on the
window this design reports, per [[choose-the-object-on-the-pre-registrations-own-window]].

**Runtime.** ~4,700 events × 241 minutes × three quantities is a small array; 96 placements and
an event-shift null of ~4,700 offsets over a vector of means are seconds. The cost is the fixture
decode in §0, stated there.
