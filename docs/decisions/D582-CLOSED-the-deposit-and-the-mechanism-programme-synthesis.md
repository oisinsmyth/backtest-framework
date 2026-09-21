# D582 — **The deposit's list is CLOSED by the principal**, and the synthesis of the mechanism programme D577–D581: every one of the fourteen deposit files has now been run or killed, none reached its own declared bar, and each failure named a specific error — a pooled beta that averaged a dead era with a live one, a presence rule that was a liquidity filter, a window sized ten times wider than the effect, a parent symbol that covered a sixth of a product — while what the data did say is parked with its numbers

*2026-09-21. Closure under R15: the principal, asked "where do we go next?", was recommended a
written closure of the deposit's list and a decision between a purchase and a new deposit, and
replied "Ok lets do your recomendations". Part A is the closure. Part B is the synthesis of
D577–D581 in the form D576 set for the curve — the question, the steps with their data points,
the table, the cost — because this is a portfolio piece as much as a record. Nothing is admitted;
nothing reserved is read. Companion: [D576](D576-CLOSED-the-seasonal-line-and-the-futures-curve-synthesis.md).*

---

# Part A — the closure

## 1. What is closed

The list in `docs/internal/User-Doc-Deposit/` — fourteen files deposited 2026-09-18/19 — is
closed as a source of pre-registrations on the fixtures now on disk. Nothing on it is to be
pre-registered again in any variant without a new deposit or a new fixture that the record
names. Specifically closed by this record (the curve's lines were closed by D563 and D576):

- **the CL hedging-flow derivation** (`HEDGING_FLOW_DERIVATION.md`, D577/D578): P9 failed on the
  declared statistic, the corrected mapping did not transfer, and the flow model has no weekly
  instrument in the disaggregated COT; P1–P8 are not runnable on it;
- **the funding-cycle basis** (`FUNDING_CYCLE_BASIS.md`, D580): terminal by its own kill 2 at the
  declared window and kill 4 on decay;
- **the gamma-conditioned close** (`GAMMA_CONDITIONED_CLOSE.md`, D581): terminal by its own kill 2;
  the strong version's data (signed intraday option flow) is the purchase the deposit said to
  make only if the cheap version showed anything, and it showed nothing;
- **hedging pressure** (`ALPHA_PROGRAMME.md` §4, D573): a static tilt that lost;
- **the micro-flow signal** (`MICRO_FLOW_SIGNAL.md`, D485): the micro crowd is half distinct and
  leaves no fingerprint that clears a family bar;
- **the overnight imbalance** (`OVERNIGHT_IMBALANCE.md`, D468/D470): covered by the overnight
  line the principal closed for the prop book on 2026-09-12;
- **the prop liquidation cascades** (`PROP_LIQUIDATION_CASCADES.md`): killed at premise by the
  deposit itself on 2026-09-18 — prop orders do not reach the exchange;
- **the session-handoff liquidity study** (`SESSION_HANDOFF_LIQUIDITY.md`): never designed here —
  two-sided passive quoting, not prop-compliant, and a simulated fill engine flatters it, all by
  the deposit's own §4.

## 2. The evidence, in one table

| deposit file | study | records | the declared bar | the number | outcome |
|---|---|---|---|---|---|
| `PUBLISHED_STRATEGIES.md` §1 | time-series momentum, 36 roots | D555, D562, D563 | gross > 0 above the purged rotation p95 | +0.30 / +0.43 in sample (78th pct); +0.51 / +0.71 forward (inside) | closed D563 |
| §2 | carry timing, 36 roots | D556, D562, D563 | same | −0.20 in sample; −0.56 forward | closed D563 |
| §4 | cross-sectional term structure, 17 commodities | D557 | same | −0.21 (14th pct) | does not pass |
| §5 | cross-sectional 12-1 momentum | D558 | same | −0.26 | does not pass |
| §6 | momentum × term-structure double sort | D559 | same | −0.11 | does not pass |
| `BASIS_MOMENTUM.md` | Boons–Prado on 17 commodities | D564, D574 | same; forward outside the null | +0.42 as pre-registered (rank 0.80); +0.69 amended; **+0.48 forward, inside, composition inverted** | spent |
| `ALPHA_PROGRAMME.md` §4 | hedging pressure, 16 roots | D573 | same | −0.20 / −0.28; the sort IS the tilt predicted before the run | does not pass |
| `HEDGING_FLOW_DERIVATION.md` | P9: which COT category carries producer flow | D577, D578 | β_SD > 0, t ≥ 2, above p95, share ≥ 0.6 | gross short +18k (t 1.2); the **beside** net short +71k (t 3.7) → **forward −32k (t −1.1, rank 0.11)** | no weekly instrument |
| `MICRO_FLOW_SIGNAL.md` | is the micro crowd a retail identifier | D485 | family bar on the excess flow | half distinct, no flatten fingerprint, no family bar | closed |
| `OVERNIGHT_IMBALANCE.md` | the cash-open window on ES/NQ/RTY | D468, D470 | component standard | none of 24 windows on eight roots; the drift follows DOWN nights | line closed 2026-09-12 |
| `PROP_LIQUIDATION_CASCADES.md` | forced exits under shared rules | — | premise | prop orders do not reach the exchange | killed 2026-09-18 |
| `SESSION_HANDOFF_LIQUIDITY.md` | staffing-gap liquidity | — | prop compliance | two-sided passive quoting | never designed |
| `FUNDING_CYCLE_BASIS.md` | the funding clock on CME bitcoin | D579, D580 | 60-min window rank ≥ 0.95 both quantities, 4 of 6 years; signed post-move ≥ 2 bp above both nulls | **volume 1.9× at the settlement minute for five minutes**, gone 2022–23; window rank 0.937 / 0.874, 0 of 6 years; post-move −1.0 bp | NOT SUPPORTED |
| `GAMMA_CONDITIONED_CLOSE.md` | carried dealer gamma and the close | D581 | interaction c < 0, t ≥ 2, below the day-shift p05 | c −0.023 (t −0.66, rank 0.32); the close continues its hour in every regime (b +0.10, t 2.9) | NOT SUPPORTED |
| seasonal avatars | NG, grains, oil, meal, livestock | D565–D571, D575 | control, own placement null, prediction, forward | every one failed one | closed D576 |
| `DATA_EXPANSION_PLAN.md` | Phase 0 free sources | D572, D579, D581 | — | COT to 34 symbols; funding on three venues; ES option OI 2016–2026 | done, £0 |
| | Phase 1 Norgate, USD 270 | — | — | serves lines now closed | not bought |
| `EVENT_PORTFOLIO.md` | the stack | — | base case: 3 of 4 survive at 0.6 → 0.95 | **0 of 4 survived** | — |

`FEATURE_RESEARCH.md` and `READING_LIST.md` are method, not studies, and stay in force.

## 3. What this record does not close

The one admitted arm (the MACD day session on NQ, `BOOK_PROP.md`), the components ledger and its
standard, the fixtures (all of them stay, gated, in the manifest), and three parked observations
with their numbers: the ES close continues its prior hour by a tenth of the move in every gamma
regime (D581, b +0.10 at t 2.9 — D463's effect, cost-bound at K3); the perpetual funding
settlement minute carries a five-minute burst of about double the cycle's volume and variance on
CME bitcoin, unsigned, strongest 2018–2021 (D580); producer/merchant longs in crude buy rallies
in both the 2010–2023 and 2024–2026 samples (D578 post-mortem, +68k and +241k contracts a
log-point). None is a component; each is a fact a future deposit may build on, and a construction
built on one of them must be designed on a window that has not read it.

## 4. What survives as instruments

`fetch_perp_funding.py` and the funding fixture (46,892 settlements, three venues);
`build_fut_btc_1m.py` and the one-minute bitcoin fixture (every session, UTC); `quote_es_options_pull.py`,
`fetch_es_options.py`, `build_fut_es_options_eod.py` and the ES option end-of-day fixture (19.2M
rows, 25 families, six gates); the placement-null and event-shift machinery of D580; the Black-76
gamma sum with its two-implementation audit and the windowed definition labelling of D581; the
post-mortem decomposition of D578 (`diag_d578_postmortem.py`: era, rolling β, leverage, leg,
level path, power), which is now the guard any pooled β must pass before it goes forward.

---

# Part B — the synthesis of the mechanism programme, D577–D581

## 5. The question, and why it was asked this way

The prop book needs a second component: net Sharpe 0.4–0.6 at the account's size, correlation
under 0.3 with the MACD arm, confirmed on a slice no component has seen. D576 closed the
commodity curve and said the search moves off it, to mechanisms with a clock and a sample in
sessions. The deposit held three such mechanisms with data on disk or free: a derivation of
producer hedging flow (a weekly clock in the COT), the perpetual funding cycle (three settlements
a day), and dealer gamma at the close (every session). Each was designed as a Stage 0 premise
check — measure the conditioner before building on it — with the kill criteria the deposit itself
wrote, and each was run once.

## 6. How the reasoning moved, step by step

1. **The deposit's order was followed literally.** `HEDGING_FLOW_DERIVATION.md` §12 says "P9
   first — confirm the flow appears in Swap Dealers. If not, stop and fix the mapping." D577
   tested P9 on positioning alone: the swap-dealer gross short against the 12–24-month strip over
   four weeks, 708 weekly reports 2010–2023. **Neither category responded** on the declared
   statistic: swap dealers +18k contracts a log-point at t 1.2 (rank 0.939), producer/merchant
   t 0.8, and the response two orders of magnitude below the derivation's prior of 18–37k
   contracts per dollar.
2. **A "beside" statistic looked like the answer.** The net short — gross short less gross long
   — responded at +44k (t 2.7) over four weeks and +71k (t 3.7) over eight, with producer/merchant
   moving the other way. D577 said in writing that testing it on the same reports would be
   reading the data twice, and that its clean sample was the 139 reports of 2024–2026. That was
   the right refusal and the wrong next step, because
3. **the forward read failed, and not on power.** D578 pre-registered the net short at eight
   weeks with nine predictions and a harness that rebuilt the in-sample betas to 1e-6 before any
   forward report was opened. Forward: **−32k at t −1.1, rank 0.11** in the exact shift null;
   −110k on seventeen non-overlapping changes; the two episodes the derivation named gave +677
   and +5,302 contracts. The forward point estimate rejected the in-sample beta at z −3.7.
4. **The post-mortem found the reason inside the in-sample window.** The +71k was robust to every
   outlier cut (Theil–Sen +65k, Huber +76k, eight non-overlapping phases all positive) but it was
   a 2014–2019 phenomenon: the rolling three-year beta was +115k to +161k through 2019, +64k in
   2020, +31k, +34k, and **−0k at end-2023**; the last five in-sample years alone sat inside their
   own shift null at rank 0.78. The instrument that carried it, the swap-dealer gross short, fell
   from 184k contracts in 2019 to **32k in 2023**. The pooled t of 3.7 averaged a live era with a
   dead one, and the D577 design had reported neither the era split nor the level path — the guard
   this repo already kept for pooled averages, not yet for a regression β taken forward.
5. **The funding clock was designed with that guard in it** — the level path of funding magnitude
   and open interest by year, a bar 2023 had to clear alone — and with the construction's own
   placement null (96 five-minute offsets through the eight-hour cycle). Its fixture needed the
   venues' funding rates (D579: 46,892 settlements, three venues, a third to a half of them at the
   +0.01 % default) and one-minute CME bitcoin bars (built in three minutes on six workers).
6. **The presence rule was a liquidity filter.** Full-size bitcoin prints a bar on 59 % of open
   minutes, so "bars present on 50 of 60 minutes" kept 1,215 of 6,611 settlements and discarded
   the thin 00:00 UTC hour. Presence was redefined as the session, an untraded open minute as
   volume 0, before any statistic was read: 4,673 settlements, the count the design expected.
7. **The clock is on CME, five minutes wide.** Volume at the settlement minute is **1.92× the
   cycle mean**, the next two minutes 1.7–1.8×, the minutes before 0.9–1.0×; variance the same
   shape; the profile peaks at minute 0 and beats every other top of the hour. Spread over the
   declared sixty-minute window it is a 10 % effect ranking **0.937 / 0.874** against a bar of
   0.95, and its own overlapping neighbours rank above it. Non-overlapping rank 1.00 for volume.
8. **And it is unsigned and decaying.** The funding sign orders nothing at 15, 30 or 60 minutes:
   −1.0 bp with SE 1.5, median zero, ranks 0.38 and 0.08 in the two nulls, +4.8 bp in 2021 and
   −9.6 bp in 2022. The burst held 2018–2021 and vanished in 2022–2023 as median funding fell from
   2–3 bp a period to 0.7 bp. Terminal at the declared window by the deposit's kill 2, and kill 4.
9. **The gamma close needed data the archive half held.** Every ES-family option's one-minute
   bars were already on disk (35,690 instruments in 2025 alone), which made the 0DTE volume
   build the deposit thought unaffordable a free diagnostic; open interest and strikes were not,
   and were quoted at 47.7 GB, USD 0.00 under the subscription.
10. **The parent symbol covered a sixth of the product.** `ES.OPT` returned the quarterly family
    alone — 54,250 options, no weekly — after the pull, the build and the gates had all run. The
    24 weekly and daily families are their own parents: 336 GB billable, USD 0.00, four more jobs,
    an overnight download. Three more traps followed and are recorded: single-digit year codes
    recycle (`ESZ6` is 2016 and 2026), an expired option's final open interest is usable the next
    session (1.49M contracts of expired ESM2 in one gate check), and the quarterly expires at 09:30.
11. **The fixture passed six gates; the premise did not pass one.** On 1,990 sessions the
    interaction of the last half-hour's return with the hour before it and the carried-gamma sign
    is **−0.023 at t −0.66, rank 0.32** in the enumerated day-shift null; +0.0005 in 2016–2021,
    −0.076 (rank 0.08) in 2022–2023, −0.003 in 2023 alone; the little there is sits on the sessions
    **without** a same-day expiry. Carried open interest sees at most 8.5 % of same-day gamma, as
    the deposit's own correction of 18 September said. The close continues its prior hour in every
    regime — b +0.10 at t 2.9, D463's effect — and the regime moves it by a fifth of a standard error.
12. **Three runner crashes were subsets, not statistics.** A flip-level subset with one regime
    sign, a first-session predictor that was NaN, a collinear interaction: each was found on the
    real data after the decisive tests had printed, guarded, and rerun; none changed a number.

## 7. What the mechanism programme said, in one table

| mechanism | the conditioner's persistence | the declared statistic | in sample | forward or era | what killed it |
|---|---|---|---|---|---|
| producer hedging flow in the COT | yearly levels match the derivation's story | swap-dealer gross short vs the strip, 4 weeks | +18k, t 1.2 | net short: +71k → −32k forward | the instrument shrank 184k → 32k; the pooled β averaged two eras |
| the funding clock | 43 % default prints; |F1| fell 70 % after 2021 | 60-min window vs 96 placements; signed 30-min post-move | 1.10× (rank 0.94 / 0.87); −1.0 bp | burst 2018–21 only; sign +4.8 → −9.6 bp | a five-minute effect in an hour-wide window; no direction |
| carried dealer gamma | regimes last a week; 0DTE share ≤ 8.5 % | interaction of close with prior hour × regime sign | c −0.023, rank 0.32 | 2022–23 −0.076 (rank 0.08); 2023 nothing | the carried book is not the 0DTE book; the close continues regardless |

## 8. What it cost, and what it bought

**Cost.** Five decision numbers (D577–D581) and two days of the principal's machine, of which the
options download was an overnight; three fixtures of 67 GB, 200 MB and 60 MB; and four errors
of mine, each recorded: taking a beside statistic forward without its era split and level path
(D577 → D578; the memory rule is now general to any pooled β); writing a bar-count presence rule
on a contract that prints when it trades (D580); sizing an event window before seeing the
profile, with a placement null whose neighbours shared the window (D580); and quoting a parent
symbol without probing what it resolved to (D581). One process fault repeated: each runner's
subset diagnostics crashed on real data after the decisive tests printed, because a clean-case
selftest cannot exercise a degenerate subset — the guard is now a check on each subset's regime
count and finiteness before the fit.

**Bought.** Four fixtures that outlast their studies (COT on 34 symbols; funding on three venues;
one-minute bitcoin; ES option open interest by strike, 2016–2026, with the 0DTE volume); seven
method memories; the post-mortem decomposition as a reusable guard; and three parked facts with
their numbers (§3). And the answer to the deposit's question in the form the deposit itself
predicted in `EVENT_PORTFOLIO.md` §3 — its pessimistic case was two survivors at 0.5; the
realised case is none.

## 9. Where the ledger stands, and where the search goes

The prop book is one arm. The components ledger holds the MACD arm admitted, K8 closed, the NG
spread removed. Every line the deposit named is closed, spent or killed, and the slices spent by
line are recorded in D576 §9 with, from this programme, the CL disaggregated 2024+ reports for the
hedging-flow line; nothing reserved was read by D580 or D581.

The search for a second component cannot continue from this deposit. What would continue it is
one of two things the principal decides: a purchase that opens a line not on this list (Norgate
extends only closed lines; signed option flow serves a mechanism the cheap test just failed), or
a new deposit of mechanisms outside the ones tried. Until one arrives, the standing work is the
book as it is: the one arm, its slice spent, and the standards that kept a populated ledger from
being a borrowed one.
