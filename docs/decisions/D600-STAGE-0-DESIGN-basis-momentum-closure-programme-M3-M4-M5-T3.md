# D600 STAGE 0 DESIGN — **the basis-momentum closure programme on the 17 commodity roots: every remaining test in `BASIS_MOMENTUM.md` that is worth running and needs no purchase** — the maturity-specific and curvature cells (M3, §6.3, item 6), the de-seasonalised signal (§6.4, item 4), the computable half of the feature evaluation (T3), the He–Kelly–Manela loading (M4), the inventory negative control on ten roots (M5), and the second-nearby capacity table (item 7); every prediction and bar declared, every conditioner measured before the sessions it conditions, no reserved session read, **no closure rule declared — the principal rules on the document once the results are in**

**Stage 0 design, committed before the runner and before the fixtures it needs. Diagnostic on
2011-07 → 2023-12-29; no session, settlement, release or observation from 2024-01-01 on is read;
no cost beyond D564's component line, which stands; nothing admitted (R15).** The line's forward
slice is spent on these roots (D574), so nothing here can be promoted whatever it shows: the
record buys the knowledge the principal asked for on 2026-09-21 — "fully close out the momentum
basis document, run every test worth running" — and the closure, if any, is the principal's
ruling afterwards, written as a separate record.

*2026-09-21. After D564/D574 (the book and its forward read), D583 (M7) and D584 (M1, M2, the
COT negative control), the document's remaining items sort into: what the settlement strip
already supports (the third nearby is on disk for every root — all 17 have at least four
eligible deferred contracts at every month-end); what needs a keyless fetch (the He–Kelly–Manela
factors; the EIA weekly stocks); what needs a key the principal registers (the USDA NASS stocks);
what is a construction for financials with its own trial and its own unread slice (T2 on FX —
**a separate pre-registration to follow, not this record**); and what is not run. The D578, D580,
D583 and D584 lessons are carried: era and years, the profile beside the window, overlapping
placements named, the count of years holding a state declared as a bar, and **the sign declared
on every bar whose falsifier has one**.*

**Not run, and why.** T1 (correlation with the published factor series): the JF Internet
Appendix is behind Wiley's gate and no free copy exists; D564's internal harness stands in its
place. T2 on equity index: the deposit's own open question 2 (dividend-residualised curves) has
no keyless data; excluded. §6.5 (a vol multiplier), §6.9 (position buffering) and the
ranking-period variants: enhancements and sweeps on a line with no unread commodity slice — the
document itself says never to report the best of several. §4.1 (the implied financing rate, the
cross-currency basis) and §4.3 (calendar-spread liquidity): instrumentation builds; M4 measures
the constraint directly with the canonical series.

---

## 1. The book, the harness, the fixtures

**The book.** D564's primary cell, EW High4/Low4 under `FFILL_FORMATION = 5`, rebuilt by
D583's `build_book`; positioned sessions 2011-07-01 → 2023-12-29. **Harness before any
statistic:** its PRIMARY-window gross Sharpe equals D564's artifact to 1e-9 (+0.692157), and the
High4−Low4 **spreading** cell (D564 P-7) equals the artifact's +0.163294 to 1e-9 — the second
harness because block A scores that very object. The nine-root non-seasonal diagnostic (−0.092)
is the third harness, for block B.

**Fixtures this design needs and does not yet have (a separate fixture record to follow):** the
He–Kelly–Manela factors (monthly and quarterly, zhiguohe.net's 2025-06-27 file, keyless); the
EIA weekly stocks (the keyless bulk archives, four series, a release-date column by the WPSR and
WNGSR calendars); the USDA NASS stocks (Quick Stats, keyed by the principal's `NASS_API_KEY`;
release dates from the ESMIS archive). Each with gates, a meta sidecar, a manifest entry and a
`data-available.md` paragraph before the runner reads it. **If the NASS key is absent at run
time, block E runs on the five energy roots and says so; it does not prompt and does not fail.**

## 2. The blocks, with predictions

### A. The maturity-specific component and curvature (M3, §6.3, item 6)

`choose_nearby` extended to return a **third nearby T3**, the next listed delivery after T2 with
a settlement at formation, and `nearby_series` to carry `R3` (the monthly same-contract return
of T3) and `r3d`. Three cells, each EW High4/Low4 on ≤ 17 roots with D564's eligibility
(twelve finite returns of every series the signal uses, nothing stale), each scored on the
**nearby return `r1d`** as the primary is, each against D564's exactness-guarded N1 rotation
null (every offset within the PRIMARY window, purge 252 both ends) and the N3 name-randomised
null (2,000 draws), and the family maximum as N2:

| cell | signal at formation | predicted | falsifier |
|---|---|---|---|
| **BM(2,3)** | Π(1+R2) − Π(1+R3) | gross Sharpe > 0, above N1 p95 — the paper's "maturity-specific component that varies across the curve" measured one pair out | inside → the effect lives at the front pair only |
| **curvature** | [Π(1+R1) − Π(1+R2)] − [Π(1+R2) − Π(1+R3)] | gross > 0, above N1 p95 — the document's item 6 | inside → curvature adds nothing the pair does not have |
| **the primary scored on `r2d` and on `r1d − r2d`** | D564's own membership | the spread cell reproduces P-7 (+0.163) to 1e-9; the `r2d` cell's Sharpe and its share of the primary's daily P&L reported | — |

Beside: Spearman of each new signal with BM(1,2) at the month-end (declared: BM(2,3) between
0.3 and 0.7; curvature with BM positive), the per-root sign count, the eras, and the trimmed
(1 % both tails) root-month means. **The three signals must be pairwise distinct** (right
quantity).

### B. De-seasonalisation (§6.4, item 4) — one method, chosen here

Per root, the monthly curve increment `d_m = R1_m − R2_m`. The seasonal component
`s(root, calendar month)` is the **expanding-window mean of `d` for that calendar month over
month-ends strictly before formation, requiring at least three prior observations** (else the
root is ineligible that month; NG and the grains lose their first three years of that month).
`BM_ds = Σ_{12} (d_m − s_m)`, the additive form. Cell: EW High4/Low4 on `BM_ds`, D564's nulls
as in A.

| | predicted | falsifier |
|---|---|---|
| **BM_ds** | gross > 0, above N1 p95: "demonstrate the signal survives" | inside → the in-sample pass was the calendar, which D574's inverted composition already said |
| ρ(BM_ds, BM) at the month-end | > 0.8 on the nine non-seasonal roots; lower on NG and the five grains | — |
| the nine-root non-seasonal High3/Low3 | reproduces D564's −0.092 to 1e-9 (harness) | — |

The alternative the document lists — same-delivery-month contracts year over year — is not run;
one method, declared.

### C. T3 — the computable half of the feature evaluation

On the month-end signal grid (17 roots, ~150 month-ends), against `FEATURE_RESEARCH.md` §11's
bars as a checklist, no admission at stake:

| statistic | predicted | §11 bar |
|---|---|---|
| cross-sectional Spearman IC of BM with the forward nearby return at horizons 1, 3, 6, 12 months; Newey–West t with lag h−1 | **IC(1) > 0, t ≥ 2** (the paper's cross-sectional claim on 21 names); IC decays by 6 months | t ≥ 3.0 |
| bucket spread, High4 − Low4 and High3 − Low3, monthly mean return; interior buckets (the middle 9) | monotone from Low4 through the middle to High4 without an interior sign reversal | no interior reversal |
| per-year IC and bucket spread, 2012–2023 | positive spread in ≥ 60 % of years | ≥ 60 % |
| turnover | D564's 4.2 weight-units a year, restated | breakeven ≥ 3× cost (D564: reported) |

Not built and not claimed: CPCV path distributions, PBO, incremental IC against a library that
does not exist here. The IC by a second path (`pandas.DataFrame.corr(method="spearman")` per
month-end against the runner's rank arrays) to 1e-12.

### D. M4 — dealer balance-sheet stress (He–Kelly–Manela)

Monthly, 2011-07 → 2023-12: 150 calendar-month gross book returns, non-overlapping, so SE(ρ) ≈
0.08 and |ρ| ≈ 0.165 is the two-SE line. **One confirmatory test; two signed diagnostics; the
family is one.**

| # | statistic | predicted | falsifier |
|---|---|---|---|
| **D1 — the loading (confirmatory)** | OLS of the book's calendar-month return in month *m* on `intermediary_capital_risk_factor` dated *m*; HAC(3) t; year-block bootstrap SE beside | **β > 0, t ≥ 2.0**; point prior ρ 0.10–0.25 (the strategy loses when intermediary capital falls, §2.7) | β ≤ 0 or t < 1 → NOT SUPPORTED; 1 ≤ t < 2 with β > 0 → "consistent, unresolved" |
| D2 — lagged conditioning (§4.5) | `intermediary_capital_ratio` dated *m−1* (the paper's end-of-previous-period usage; *m−3* beside, the quarter certainly filed) in its **bottom tercile of the trailing 120 months** against the top tercile → the month-*m* book return; null = the tercile state shifted by every offset within the span, enumerated; non-overlapping rank beside; the years holding both states counted | bottom > top | reported; no gate |
| D3 — dispersion | Spearman of the cross-sectional IQR of BM at formation with the ratio dated *m−1*; 12-month block-bootstrap 90 % interval; the non-overlapping annual version beside | negative (disturbances persist when capacity is scarce, §2.4) | declared unresolvable at conventional levels — BM is a twelve-month overlapping sum and the ratio is AR(1) ≈ 0.94 quarterly, effective n ≈ 12–15, the two-SE line ≈ 0.5 — so a sign, never a verdict |

Verdict on M4 from D1 alone: SUPPORTED, UNRESOLVED, NOT SUPPORTED. Beside: D1 on
`intermediary_leverage_ratio_squared` (the paper's alternative), the eras 2011–2015 and
2016–2023, the same on the as-pre-registered (`ffill = 1`) book. Sign in money: a synthetic book
equal to +x × the factor plus noise gives β > 0 at t ≫ 2 and its negation β < 0. **Declared
about the series:** one vintage (2025-06-27); the monthly capital ratio interpolates quarterly
balance-sheet data with market equity monthly; used contemporaneously only as a risk factor and
lagged for conditioning; accounting restatements are not point-in-time.

### E. M5 — the inventory negative control

Coverage, declared: **ten of the seventeen roots** — CL and BZ (crude ex-SPR, `WCESTUS1`), HO
(distillate, `WDISTUS1`), RB (total gasoline, `WGTSTUS1`), NG (Lower-48 working gas,
`NW2_EPG0_SWO_R48_BCFW`), weekly from EIA; ZC, ZS, ZW (quarterly Grain Stocks), LE (monthly
Cattle on Feed), HE (quarterly Hogs and Pigs) from NASS. GC, SI, HG, PL, PA (no free
machine-readable warehouse history) and ZL, ZM (no NASS stocks series) are excluded — a limit
of the control, not a finding about the mechanism.

**Known-at rules, audited on every used row (RAISE on a one-week shift):** an EIA week ending
Friday *w* is known at month-end session *t* iff *w* + 7 calendar days ≤ *t* (covers the
Wednesday and Thursday 10:30 ET releases, holiday shifts and the June-2022 two-week outage
conservatively); a NASS report is known iff its release timestamp, from the ESMIS archive, is
≤ 16:00 ET on session *t* — never the Quick Stats `load_time`, which is an insertion stamp.

**The conditioner:** the latest known observation's level and its 12-month log change,
de-seasonalised against the trailing five same-period observations (same week of year; same
quarter; same month) — so the series is the surprise in storage, not the calendar.

| statistic | bar (with the sign) |
|---|---|
| mean cross-sectional Spearman over month-ends of BM with the inventory change over the covered roots (≥ 5 roots present), year-block SE; the pooled version; the per-root time-series Spearman for every covered root, quarterly roots on their own grid | **holds** if every \|ρ\| < 0.3 and each sits more than two SE inside; **fails** if any \|ρ\| ≥ 0.5 in either sign (the effect would then be a storage sort); UNRESOLVED between |
| the same with the inventory **level** | reported |

Right quantity: the change and the level are distinct series. The control's sign is not
predicted (a storage effect could go either way); the bar is on magnitude, both tails named.

### F. Capacity at the second nearby (item 7)

From the `statistics` archive's per-contract cleared volume (`stat_type == 6`, the worker of
`build_fut_open_interest.py` before its aggregation, windowed ids as D521), a table per root:
median and 10th-percentile daily cleared volume of the **held T2 contract** over 2016–2023 and
the D564 dollar book's one-contract T2 position as a share of it; the same for T1. No
prediction: a table for the personal-capital path. If the decode exceeds five minutes, one year
per era is sampled and the table says so.

## 3. Nulls, chance, verdicts

**Nulls.** A and B use D564's N1 (every rotation offset within the PRIMARY window, purge 252,
an exactness guard on 20 offsets against `book_return_loop`) and N3 (name-randomised, 2,000
draws); N2 is the family maximum over A's three new cells and B's one. D2's null is the
enumerated shift of the state; the T3 t-statistics carry their own overlap correction. Every
zero offset must reproduce its observed statistic.

**Chance.** A declares two directional cells; B one; C one confirmatory IC; D one confirmatory
loading; E a two-sided magnitude bar. Six declared bars, each with a direction or a magnitude
written here first; nothing is selected on and nothing is varied except as the reported
diagnostics say.

**Verdicts, one per block, never combined:** A (M3): SUPPORTED if either new cell clears N1 p95
with gross > 0 and the family clears N2 p95; NOT SUPPORTED otherwise. B: SURVIVES / DOES NOT
SURVIVE on BM_ds against N1 p95. C: the §11 checklist, each row holds or fails. D: as in §2.D.
E: HOLDS / FAILS / UNRESOLVED. **No closure rule is declared.** The RESULT reports the six
verdicts and, for anything that passes, what a follow-up would need — a fixture this line has
not read — so that the principal's ruling on the document is informed.

## 4. Audits, each proven to RAISE on a break that hits what the assertion reads

(a) the three harnesses — the primary, the spreading cell and the nine-root diagnostic against
D564's artifact to 1e-9; break = the series rolled one session; (b) the third nearby and `R3`
by a pandas second path in `bm_pandas`'s style on 300 seeded cells to 1e-10; break = the
delivery threshold shifted one month; (c) `BM_ds` by a second path — pandas groupby on the
calendar month with an expanding mean shifted one observation, never the numpy loop; break =
the seasonal mean not shifted (look-ahead); (d) the IC by `DataFrame.corr` per month-end;
break = the forward return unlagged; (e) sign in money on every directional statistic —
synthetic grids with +x on the predicted side give rank 1.0 and their negation raises; (f) the
known-at keying of EIA and NASS — every used observation's release date ≤ the month-end it
conditions; break = the release column shifted one week earlier; (g) the zero offset of every
enumerated null reproduces the observed; (h) right quantity — A's three signals pairwise
distinct, `BM_ds ≠ BM`, E's change ≠ level; (i) `REQUIRED_OUTPUTS` first; `encoding="utf-8"`
on every text IO call.

## 5. What is read, and what is not

The settlement strip and the breadth fixture to 2023-12-29 for the 17 roots; D564's artifact;
the fixture record's four fixtures with every row filtered on its observation and release dates `< 2024-01-01`;
the `statistics` archive's cleared-volume rows to 2023-12-29. **Not read:** any session,
settlement, release or observation from 2024-01-01 on; the COT, funding and option fixtures.
**Seen-ness declared:** the book's returns on 2011–2023 have been read by D564, D574, D583 and
D584; this record reads them again under conditioners the document named in advance (M3, M4,
M5) and under two construction variants the document asked for (curvature, de-seasonalisation)
that can inform no trade on these roots.

**Runtime.** The book 8 s; four new cells under N1 (≈ 1,760 offsets after purge) and N3 (2,000
draws) — D564's family of four took a few minutes, so a few minutes here; the enumerated shift
null and the correlations seconds; the capacity decode about three minutes in the pool. Under
fifteen minutes; the first cell is timed before the family is launched.
