# D603 — **`BASIS_MOMENTUM.md` is CLOSED by the principal**, and the synthesis of the basis-momentum programme D564–D602: ten free tests in four Stage 0 records, the in-sample replication and the forward read, and not one mechanism prediction supported — the calendar orders nothing, the illiquid roots earn the *wrong* way, the curve moves together across maturities, the dealer factor reads zero, storage is *in* the signal, and the FX extension is void on its own harness

*2026-09-21. Closure under R15: the principal, shown the full verdict table of D583, D584, D600
and D602 and told that closure waited on their ruling, replied "Close all this I don't think its
worth running the rest? What do you think?" and was answered that the three remaining items (the
NASS extension of M5, a re-specified FX construction on forward or OIS rates, T1) could change no
verdict and promote nothing. Part A is the closure. Part B is the synthesis in the form D576 and
D582 set — the question, the steps with their data points, the table, the cost. Nothing is
admitted; nothing reserved is read; the FX 2024+ slice stays unread. Companions:
[D576](D576-CLOSED-the-seasonal-line-and-the-futures-curve-synthesis.md),
[D582](D582-CLOSED-the-deposit-and-the-mechanism-programme-synthesis.md).*

---

# Part A — the closure

## 1. What is closed

`docs/internal/User-Doc-Deposit/BASIS_MOMENTUM.md` is closed as a source of pre-registrations
on the fixtures now on disk, in every variant the document names or implies: the published
construction and its formation amendment (D564), the second-nearby, curvature and
de-seasonalised forms (D600), the time-series form (D564, D602), the covered-parity FX form
(D602), and every conditioning of the book on liquidity, volatility, the calendar, dealer
capital or inventories (D583, D584, D600). The commodity 2024+ slice was spent by D574; the FX
2024+ slice is reserved and unread, and stays so — a construction that could read it would need
a rates fixture this repository does not hold (§3).

Specifically **not run, on the ruling**, with the reason each time:

- **M5 on the NASS roots** (ZC ZS ZW LE HE): the control already fails on its meaning on all
  five energy roots and the commodity slice is spent, so five more roots can only make a failed
  control more precise. The fetcher's `--fetch nass` path stays, unrun, for a future deposit.
- **A re-specified FX construction**: it needs 3-to-6-month forward rates or an OIS curve per
  currency, daily and point-in-time — not on disk, not keyless — to test a signal whose raw form
  is −0.04 in sample and whose only positive cell the harness showed to be rate momentum.
- **T1** (correlation with the published factor series): the Internet Appendix is behind a
  403 and no free copy was found; not runnable.
- **§6.5 volatility scaling, §6.9 buffering, the ranking-period variants, §4.1 financing-rate
  and §4.3 spread-liquidity instrumentation**: enhancements and instrumentation on a line with
  nothing to enhance; the document itself says not to sweep.

`FEATURE_RESEARCH.md` and `READING_LIST.md` are method, not studies, and stay in force.

## 2. The evidence, in one table

| item in the document | record | the declared bar | the number | outcome |
|---|---|---|---|---|
| the replication, 17 commodities, High4/Low4 | [D564](D564-RESULT-passes-only-under-the-formation-amendment.md) | gross > 0 above the purged rotation p95 | +0.42 as pre-registered (rank 0.80); **+0.69 under the formation amendment** (rank 0.97) | passes only amended |
| the forward read, 2024-01 on | [D574](D574-RESULT-inside-the-total-transfers-the-composition-inverts.md) | forward outside the null | **+0.48, inside; the seasonal roots that carried it in sample lost forward** | slice spent |
| M7 · the reporting calendar | [D583](D583-STAGE-0-RESULT-not-supported-quarter-ends-order-nothing.md) | the ten sessions into a quarter-end above the placement p95; quarter-ends above the other month-ends | −0.37 bp/day, rank 0.47 of 63 placements; the quarter-ends 2.7 bp/day *below* the rest, rank 0.23 of 495 subsets | NOT SUPPORTED |
| M1 · stronger in the less liquid roots | [D584](D584-STAGE-0-RESULT-M1-M2-not-supported-the-control-unresolved.md) | the 8 least liquid above the 9 most liquid, above the split p95, Spearman < 0 | +5.46 bp/root-day the predicted way but rank 0.85 of 24,310 splits, Spearman **+0.02**, 5 of 12 years, all of it on PL and GC | NOT SUPPORTED |
| M2 · stronger after a volatility spike | D584 | the 21 post-spike sessions above the rest, above the shift p95 | −0.57 bp/day (SE 2.26), rank 0.44 of 3,224 shifts, 5 of 10 years | NOT SUPPORTED |
| negative control · uncorrelated with hedging pressure | D584 | \|ρ\| < 0.3 holds, ≥ 0.5 fails | −0.15 and −0.11 with HP and its change; the same-week signed commercial flow **−0.35**, the commercials-against-price relation every root shows | UNRESOLVED on its letter, holds on its meaning |
| M3 · maturity-specific component, curvature | [D600](D600-STAGE-0-RESULT-M3-M4-not-supported-M5-unresolved-on-storage.md) | BM(2,3) and curvature above N1 p95 | BM(2,3) +0.37 at rank 0.90; curvature −0.08 at 0.42; **the primary scored on the second nearby +0.70, 94 % of its P&L** | NOT SUPPORTED |
| §6.4 · the de-seasonalised signal survives | D600 | above N1 p95 | +0.51 at rank 0.958 in N1, 0.93 in N3, 0.94 as the family's best; **ρ 0.89–0.93 with the raw signal** | survives as arithmetic: a 12-month sum of a fixed calendar effect is a per-root constant |
| T3 · the feature evaluation | D600 | `FEATURE_RESEARCH` §11: t ≥ 3, no interior reversal, positive spread ≥ 60 % of years | IC(1) **+0.048, t 2.17**, rising to +0.11 at twelve months; buckets −51 / +31 / +71 bp monotone; 9 of 12 years | the paper's bar, not the protocol's; CPCV and PBO not built |
| M4 · loads on dealer balance-sheet stress | D600 | β > 0 on the He–Kelly–Manela capital risk factor, HAC t ≥ 2 | **β +0.0061, t 0.13, ρ 0.01**; after the lowest capital tercile the book earns **81 bp/month less**, rank 0.047 | NOT SUPPORTED |
| M5 · uncorrelated with inventories | D600 | \|ρ\| < 0.3 holds, ≥ 0.5 fails | −0.13 to −0.48 with the de-seasonalised inventory surprise, **negative on all five energy roots**, −0.43 cross-sectionally in 2011–2015 | UNRESOLVED on its letter, against the paper on its meaning: storage is in the signal |
| item 7 · capacity at the second nearby | D600 | a table | PL 25, SI 444, HG 836, GC 3,742 lots/day: the COMEX metals' held contracts are the inactive months | no candidate to size |
| T2 · financials, FX in covered-parity space | [D602](D602-RESULT-VOID-the-parity-correction-over-shoots-on-monthly-rates.md) | harness: raw < −0.5 with Δ12 rate differential, corrected inside 0.3; then primary above N1 p95 | raw **−0.514** holds; corrected **+0.598** fails; for the record the primary +0.06 (rank 0.88), the raw form −0.04, the time-series form +0.48 at rank 0.996 on a signal 0.6-correlated with rate momentum | VOID on its own harness |
| T2 · equity index | D600 design | — | dividend-residualised curves, no data | excluded |
| T1 · the published factor series | D600 design | — | Internet Appendix behind a 403 | not runnable |

Every book above is gross on the nearby return, the rotation null purged 252 sessions at both
ends and exactness-guarded, the family maximum and the name-randomised null beside; every runner
reproduced D564's primary (+0.692157) to 1e-9 before scoring anything; every audit raised on its
break inside the run.

## 3. What this record does not close

The fixtures and the instruments (§4), the components ledger, the one admitted arm. Two facts are
parked with their numbers, not as components: **the cross-sectional IC of basis momentum on the
17 commodity roots rises with horizon** (+0.048 at one month to +0.112 at twelve, 9 of 12 years),
which D574 already read forward as a book and found inside its null — the persistence is real,
the premium it orders is not; and **the FX curve's calendar spread, corrected by a single 3-month
tenor, is more rate-momentum than the raw spread** (+0.60 against −0.51), which is a statement
about the correction, not about basis momentum in FX. A construction that read the FX 2024+
slice would need the forward or OIS rates named in §1 and a pre-registration on a window that has
not read D602; nothing here is tuned toward one.

## 4. What survives as instruments

`fetch_macro_series.py` (HKM, EIA bulk, OECD SDMX, ESMIS release lists, NASS behind the
principal's key; every fixture gated, the gates proven to raise) and the fixtures it built
([D601](D601-FIXTURE-macro-series-for-the-basis-momentum-closure-programme.md): the He–Kelly–Manela
factors, gitignored under the authors' terms and manifest-hashed; EIA weekly stocks with the
known-at rule week-ending + 7 days; the OECD 3-month interbank rates for seven currencies with
the one filled cell flagged); `build_fut_cleared_volume_cm.py` and the per-contract cleared
volume of the 17 commodity roots from 2015-11-19; the third-nearby extension of the strip and
the de-seasonalised signal with their pandas second paths (`stage0_d600_bm_closure.py`); the
covered-parity correction, its exactness test on synthetic parity settlements and the void-not-
failed harness form (`run_d602_bm_fx.py`); the enumerated placement, split and shift nulls of
D583 and D584; and the harness pattern — rebuild the prior record's primary to 1e-9 before any
new statistic — that every runner in this programme opened with.

---

# Part B — the synthesis of the basis-momentum programme, D564–D602

## 5. The question, and why it was asked this way

The deposit selected basis momentum as the candidate second mechanism "for orthogonality to
hedging pressure rather than for standalone strength", with a mechanism section (§2) naming seven
predictions that would distinguish a curve-imbalance premium from a re-labelled carry or momentum
effect, and a test section (§6) naming the harness. D564 replicated the construction and D574
read it forward; both were on the book's Sharpe. The principal then asked, on 2026-09-21, for the
mechanism itself to be tested — first the calendar (D583), then liquidity, volatility and the
control (D584), then, in the words "fully close out the momentum basis document, run every test
worth running", everything the document names that needs no purchase (D600, D601, D602). Every
one was a Stage 0 premise check with the bar declared before the run and the closure rule left to
the principal.

## 6. How the reasoning moved, step by step

1. **The replication passed only amended.** D564's pre-registered construction earned +0.42 at
   rank 0.80; a formation-rule amendment repairing two calendar defects (a month-end with no
   settlement voids a year of a twelve-month signal), made *after* the pre-registered percentile
   was read and recorded as such, took it to +0.69 at rank 0.972. The pass was recorded as
   conditional, carried by the seasonal roots and the two years the amendment restored.
2. **The forward read was inside, and the composition inverted.** D574: +0.48 on 2024-01 onward,
   inside its null; the seasonal roots that carried the in-sample book lost forward. The commodity
   slice was spent there, so nothing on commodities could be promoted whatever the mechanism tests
   showed — those were run for the ruling, not for admission.
3. **The calendar orders nothing.** D583 asked whether the ten sessions into a quarter-end carry
   the book (the reporting-date rebalancing story): −0.37 bp/day against the rest, rank 0.47 in
   the 63 enumerated placements; the quarter-ends 2.7 bp/day *below* the other eight month-ends;
   December the worst quarter. Four declared parts, four failures.
4. **The illiquid roots earn the wrong way.** D584: the eight least liquid roots earn more than
   the nine most liquid (+5.46 bp/root-day) but at rank 0.85 among 24,310 splits, with a Spearman
   of +0.02 where the mechanism needs a negative, and the whole difference on the two roots the
   book holds least (PL on 107 days, GC on 61). The post-spike sessions earn less, not more.
5. **The control held on its meaning and not its letter.** The signal's correlation with
   commercial positioning is −0.15; the same-week signed commercial flow is −0.35, above the bar —
   but that is the commercials-against-price relation every root shows (−0.47 mean, negative on
   16 of 16), not the book riding the flow. The record said a directional falsifier needs a
   directional bar and returned UNRESOLVED as written.
6. **The principal asked for everything, and the design left closure to them.** D600 designed the
   six remaining free blocks with every bar and audit, and stated no closure rule. The principal's
   answers fixed the two open choices: FX for T2 with a rates fetch; energy plus grains and
   livestock for M5, on a NASS key the principal would register.
7. **The fixtures came from wherever was keyless.** FRED resets every connection from this
   machine, so the rates came from the OECD SDMX endpoint FRED republishes, five FRED-published
   values reproduced to 0.01 as a gate. EIA's bulk archives are keyless. The He–Kelly–Manela file
   carried two mislabelled 2025 rows, dropped and recorded. The statistics archive publishes
   cleared volume only from 2015-11-19, found when the first draft's density assert fired on
   every root — a data assert, replaced by a density over each root's own span (D601).
8. **The curve moves together.** BM(2,3) — the same construction one contract further out — earns
   +0.37 at rank 0.90, curvature −0.08. The decisive number was not a new cell but the old one
   re-scored: the primary's membership on the *second* nearby's return earns +0.70, as much as on
   the front, and 94 % of the primary's P&L. There is no maturity-specific component at this
   resolution; whatever the signal orders, it orders the whole curve.
9. **De-seasonalisation is a per-root constant.** The subtracted seasonal component summed over
   a twelve-month lookback is the same twelve calendar months every time, so BM_ds differs from BM
   by a slowly moving per-root offset — ρ 0.89–0.93 — and its survival of N1 (0.958) is the
   primary's own. Recorded as arithmetic, not evidence, and as a memory: a twelve-month sum
   cannot carry a calendar. The self-test's first draft used K = 40 months, too short for the
   expanding seasonal mean to have three prior observations; K = 72.
10. **The paper's persistence is real and rises with horizon.** IC(1) +0.048 at t 2.17, +0.112 at
    twelve months, buckets monotone, 9 of 12 years — the paper's cross-sectional claim on 21
    names reproduced on 17. And still not a component: D574 had read the book it orders forward.
11. **The dealer factor reads zero.** β +0.0061 on the capital risk factor, t 0.13, ρ 0.01, in
    neither era, on neither factor, on neither book; the conditioning diagnostic runs the wrong
    way (81 bp/month *less* after the lowest capital tercile, rank 0.047). The mechanism's
    "limited intermediary capital" premium is not in this book's returns.
12. **Storage is in the signal.** On the five energy roots the correlation of the signal with the
    de-seasonalised inventory surprise is negative on every root (−0.13 to −0.48), −0.43
    cross-sectionally in 2011–2015. The paper says the premium is inconsistent with a storage
    story; the signal on the roots where storage is measurable is a storage signal. The letter
    (|ρ| between 0.3 and 0.5) says UNRESOLVED; the reading is against the paper. The COMEX metals,
    where no free inventory history exists, turned out to be held on their inactive months
    (PL 25 lots a day at the second nearby) — the listed delivery is not the traded one.
13. **FX made the deposit's objection exact, and the correction over-shot.** In logs, basis
    momentum is minus the cumulated change of the log calendar spread; covered parity says that
    spread's fair value is the tenor-weighted rate differential, spot cancelling. So on raw
    settlements FX basis momentum is minus a quarter of the twelve-month change in the 3-month
    rate differential — rate momentum, which is why the raw form could not be the primary. The
    harness confirmed the derivation (−0.514 against a bar of −0.5) and failed the correction
    (+0.598 against 0.3): a single 3-month tenor carries the level and not the expected policy
    path the curve prices, and in a hiking cycle the 3-to-6-month slope is of the order of the
    level difference. Void, not failed; the one cell that cleared a null is rate momentum wearing
    the signal's name, and it is recorded so nobody reads it as a pass.
14. **The ruling.** Shown the table, the principal asked whether the rest was worth running and
    was told no: the NASS extension could only sharpen a failed control on a spent slice, the FX
    re-specification needs paid data for a signal with no support anywhere else, T1 is
    unrunnable. "Close all this."

## 7. What the programme said, in one table

| mechanism prediction (the document's §2) | test | the number | verdict |
|---|---|---|---|
| a premium for curve imbalance that a maturity-specific component or curvature would reveal | M3, D600 | BM(2,3) rank 0.90; curvature −0.08; the second nearby earns 94 % of the primary | NOT SUPPORTED |
| stronger where arbitrage capital is scarce: illiquid roots, post-spike sessions | M1, M2, D584 | Spearman +0.02 where negative was predicted; post-spike −0.57 bp/day | NOT SUPPORTED |
| priced by dealer balance-sheet stress | M4, D600 | β +0.006, t 0.13; conditioning the wrong way | NOT SUPPORTED |
| not a storage effect | M5, D600 | negative with the inventory surprise on every energy root | against the paper |
| not commercial hedging pressure | the control, D584 | −0.15 with HP; the same-week flow −0.35 is price-against-commercials | holds on its meaning |
| ordered by the reporting calendar | M7, D583 | rank 0.47; quarter-ends below the rest | NOT SUPPORTED |
| survives de-seasonalisation | §6.4, D600 | ρ 0.9 with the raw signal; a per-root constant | arithmetic |
| present in currencies once parity is removed | T2, D602 | the correction over-shoots (+0.60); raw −0.04 | VOID |
| persistent as a feature | T3, D600 | IC +0.048 rising to +0.112 at twelve months | real, and already read forward inside (D574) |

## 8. What it cost, and what it bought

**Cost.** Six decision numbers (D583, D584, D600, D601, D602, this record) in one day; four
fixtures under 5 MB tracked and two gitignored; no purchase; no reserved slice read. Errors of
mine, each recorded where it happened: a self-test whose de-seasonalisation window could never
reach three prior observations (D600, caught by the self-test's own guard before the run); a
density assert that encoded a data expectation and fired legitimately on every root (D601); a
first fetcher draft that cited records not yet written and opened a zip member through a text
opener the encoding scanner counts (D601); the FX correction built on the one tenor available,
which the pre-registration named as its limitation and its harness caught (D602). Two process
faults: a shell chain whose failed link let the trailing commit through on an earlier index
(8d9a7a0, repaired by a3a3ff0), and a shared worktree whose index carried a concurrent session's
forty staged files — resolved by moving this line to its own worktree and merging back (d673e43),
with the drawdown-sign lint's census (`git ls-files`, so an artifact must be staged before it can
be labelled) costing two suite runs on the way.

**Bought.** The four fixtures and the fetcher (§4), which outlast the line; the third-nearby
strip and the covered-parity construction as tested code; three method memories (a twelve-month
sum cannot carry a calendar; the listed delivery is not the traded one on COMEX; label after
staging); and the answer to the deposit's own selection criterion — basis momentum was chosen for
orthogonality to hedging pressure, and on the seen book it is orthogonal to hedging pressure,
correlated with storage, and carries no premium the nulls cannot produce.

## 9. Where the ledger stands, and where the search goes

Unchanged from D582 §9: the prop book is one arm; the components ledger holds the MACD arm
admitted, K8 closed, the NG spread removed; every line the deposit named is now closed, spent or
killed, this one included. The search for a second component cannot continue from this deposit.
What would continue it is one of two things the principal decides: a purchase that opens a line
not on the list, or a new deposit of mechanisms outside the ones tried. Until one arrives, the
standing work is the book as it is.
