# The Components Ledger — prop book

**Append-only.** A component is entered here on the standard below; it is amended or retired in
writing, never quietly edited. **Nothing in this ledger is admitted to the prop book**: only the
assembled book is tested against hurdle P (R11) and only the assembled book can enter
[`BOOK_PROP.md`](BOOK_PROP.md). The ledger exists because the book-level Sharpe the account
needs (~1.5–2) is reached by layering low-correlation components, never by one construction
(CLAUDE.md, *Two altitudes*).

## The standard (pre-registered in D466, 2026-09-12)

A construction is a **component** when, on the in-sample window (the D462 usable window,
2016-01-04 to 2023-12-29, for the futures fixtures) at the instrument's **minimum tradable size**
(the micro where one exists, one contract otherwise), net of the declared futures cost:

| | bar |
|---|---|
| **C-a** net annualised Sharpe of its daily P&L | **> 0.5** |
| **C-b** correlation of its daily P&L with **every** component already in the ledger | **< 0.3** — **no longer a rejection; it ROUTES to the vault. See the amendment of 2026-09-12 at the foot of this page.** |
| **C-c** skew of its daily P&L | **≥ −0.5** (P1 punishes negative skew; positive is fine) |
| **C-d** expressible | daily σ at minimum size ≤ 1% of a $50k account, so the assembled book can be sized |
| **C-e** provenance | a pre-registered record; the window; the cost line; the nulls it was scored against |

**C-a is a bar on the point estimate, and a component's Sharpe carries its SE** (block
bootstrap, monthly); the ledger records both. **Order of entry is recorded** because components
are chosen after their Sharpes are seen: the assembled book is confirmed only on the unread slice
(2024-01 onward on the futures fixtures), and the order fixes what "already in the ledger" meant
when C-b was applied.

**A gated subset of a component is not a new component** (it shares the clock and the signal).
**Two windows on one instrument that do not overlap in time are two components** (ρ ≈ 0.1).

**PROVISIONAL entries (added by D468, 2026-09-12).** When a record scores a *family* of declared
constructions, it reports the sign-randomisation null of the **best net Sharpe across the family**
(one sign vector per session, common to all members, so the family's correlation is preserved).
A construction that clears C-a but sits below that null's p95 is entered as **PROVISIONAL**: it
counts for C-b against later entries, it goes into the assembled book, and only the unread slice
(2024-01 onward, read under the principal's word) promotes it to a full entry or removes it. With
~2,000 days the SE of a Sharpe is ≈ 0.35 and the best of 24 draws under no edge sits near +0.6;
C-a on the point estimate is under that ceiling, and the ledger says so in the row.

## The ledger

| # | component | instrument, window, rule | record | window | net Sharpe (SE) | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|---|---|
| — | *no entry* | | D466 | 2016–2023 | | | | | *the standard admitted nothing on 2026-09-12* |
| **1** | **K8** — long the NQ day session after a down day | NQ, 09:30 open + tick → 15:59 close, one MNQ, $3; fires when yesterday's day session closed below its open (≈ 44% of sessions) | D498 (from D495's other side; selection stated) | 2016–2023 | **+0.61 (0.32)**; gross +$17.87 / +11.6 bp (SE 4.0) a trade; other side −3.1 bp, z +2.89 vs family p95 +2.41 | 56.9% | −0.02 | first entry; ρ with the ungated NQ day session 0.70 | **PROVISIONAL, 2026-09-12** — promotion by the declared forward read (D498 §3) on 2024-01-02 → 2026-09-09, on the principal's word |
| **3** | **NG winter-premium calendar spread, flat by default** — short the first-nearby, long the second, through the EIA withdrawal season (numbered #3: #1 K8 is CLOSED and #2 the MACD arm is ADMITTED, both 2026-09-13, see the sections below; the row was first written as #2 in error) | NG, one MNG a leg; T1 = delivery ≥ m+3, T2 the next listed, formed at the last session before each of Nov–Mar and held to the month's last session; flat Apr–Oct; $3 RT + one tick a leg, four sides a month | D565 (Stage 0 disclosed: five windows read before the season was declared from the EIA definition) | 2016–2023 | **+0.62 (0.28)**; gross +0.69 / Sortino +1.03; 40 positioned months, hit 0.75, median +0.34 %, worst −3.5 %; **$1,261 total at one pair, σ $24 a day positioned** — twenty pairs fit inside C-d | 20.5 % (all sessions) | **+1.98** | **not computable** — K8's daily P&L is not on disk; expected near zero by instrument and clock (NG monthly spread vs NQ day session), an expectation, not a number | **PROVISIONAL, 2026-09-20** — below its placement null's p95 by 0.007 (rank 0.942; family N2 rank 0.918); the obligated-buyer avatar is **unsupported** in the COT (7 of 13 years); promotion or removal by the unread NG 2024+ slice (thirteen positioned months), read with hurdle P on the assembled book of #2 (the admitted MACD arm, whose own slice is spent) plus this spread, on the principal's word — D566 |

**Entry #1 PARKED, 2026-09-12 (the principal).** K8 stays PROVISIONAL and its forward read is
**held**. Reason: the 2024+ day session is the one unseen slice this line has, and rule 3 above
confirms the *assembled book* on the same slice, so a K8-only read would make the book's
confirmation a re-read for K8. The read runs once, together with the second component's promotion
and hurdle P on the assembled book, when a second entry exists. K8 is not sharpened, filtered or
re-scored in-sample while parked. ES K8 (+0.18, inside its null, ρ ≈ 0.85) is the same construction
on another root and is not a second entry. Noted in `BOOK_PROP.md` (last section).

**Entry #3 REMOVED, 2026-09-20 (D566, the forward read on the principal's word).** The NG
winter-premium spread did not transfer: **−1.07 gross / −1.22 net** over the thirteen forward
positioned months (5 of 13 positive, mean −1.76 %, worst −9.72 %, −$878 at one pair), at the
**27.7th percentile** of its placement null; the pre-registered rule (REMOVED if net < −0.3 or the
positioned-month mean < 0) fires on both clauses. The two forward seasons were formed with the
front **8 and 13 % below** the second, the opposite curve state to the in-sample seasons, and the
short lost into two cold snaps. The assembled book with the admitted MACD arm (#2) read **+0.650**
at one pair against +0.712 for the arm alone on the same calendar, and −0.325 at twenty pairs;
ρ +0.01; hurdle P fails on P2 structurally (the spread is held across every permitted venue's
flatten time) and on P3a (1.09 a year at one pair, 6.16 at twenty). **The prop book is unchanged.**
The row above stays as scored; NG's 2024+ slice is spent for this construction.

## Scored and NOT entered

| construction | record | net Sharpe | why not |
|---|---|---|---|
| K1 C1: ES hold 18:00→16:00 every same-contract night, 1 MES, $3 | D466 (D449, D465) | **+0.37 (SE 0.32)**; gross +0.63 | C-a. $3 is 41% of the $7.29 gross mean per night; clears C-a only below $1.48 a round trip |
| **D555 (2026-09-19): 12-month time-series momentum as published (MOP 2012), 34 roots at minimum size, monthly holds, $3/$6 RT + one tick, rolls charged** | D555 | **+0.06 (SE 0.30)**; gross +0.08; the C-d-eligible 17-root sub-book +0.24 | **C-a, C-c (skew −0.61), C-d (σ $8,762 a day; $1,712 on the sub-book)**; inside its purged rotation null (rank 0.76). ρ with entry #2 not computed — the arm's daily P&L is not on disk |
| the 3m / 1m / 3+12 / 1+3+12 dollar cells of the same family | D555 | +0.14 / +0.27 / +0.12 / +0.18 | C-a on all; family best +0.34 (3+12 published) sits at its N2 null's **median** |
| **D556 (2026-09-19): carry timing as published (KMPV 2018), sign of the front-next annualised basis, 34 roots at minimum size, monthly holds, $3/$6 RT + one tick, rolls charged** | D556 | **+0.20 (SE 0.31)**; gross +0.23; the C-d-eligible 17-root sub-book +0.03 | **C-c (skew −0.78), C-d (σ $7,341 a day)**; and the +0.20 is **one contract of palladium** (+$276k of a +$216k total) — the equal-risk published book is **−0.20**, below its null's median |
| carry demeaned (B) and trend + carry (C) dollar cells | D556 | +0.25 / +0.21 | same palladium dependence; C-c, C-d; family best +0.25 at its N2 null's median |
| **D557 (2026-09-19): cross-sectional term-structure sort as published (Erb & Harvey 2006; FMR 2010), 17 commodities ranked by the annualised front-next basis, long top 6 / short bottom 6, 16 roots at minimum size, monthly holds, $3/$6 RT + one tick, rolls charged** | D557 | **+0.28 (SE 0.31)**; gross +0.29; the C-d-eligible 6-root sub-book +0.00 | **C-a, C-c (skew −1.03), C-d (σ $4,924 a day)**; and the +0.28 is **one contract of palladium** (+$200k of a +$176k total) — the equal-weight published book is **−0.21**, at the 14th percentile of a null whose median is +0.16 |
| the vol-scaled published cell of the same family | D557 | +0.02 gross (no dollar form: its sign is the membership, the same object as the row above) | flat; family best +0.28 (sort/dollar) at its N2 null's 60th percentile |
| **D558 (2026-09-19): cross-sectional 12-1 momentum as published (Miffre–Rallis 2007, AMP 2013), 17 commodities ranked, top/bottom third long/short, 16 roots at minimum size, monthly holds, $3/$6 RT + one tick, rolls charged** | D558 | **+0.05 (SE 0.28)**; gross +0.07; the C-d-eligible 6-root sub-book +0.06 (σ $529, fails C-d together) | **C-a, C-c (skew −0.51), C-d (σ $5,236 a day)**; the +0.05 is **palladium** (+$133k of a +$35k total) against RB (−$84k) — the equal-weight published book is **−0.26**, below its null's median (rank 0.35); ρ with entry #2 not computed — the arm's daily P&L is not on disk |
| vol-scaled published cell of the same family | D558 | −0.03 gross | not a dollar cell; family best +0.05 at its N2 null's median |
| **D559 (2026-09-19): momentum × term-structure double sort as published (FMR 2010), 17 commodity roots ranked / 16 traded at minimum size, two names a side, monthly holds, $3/$6 RT + one tick, rolls charged** | D559 | **+0.16 (SE 0.29)**; gross +0.17; the C-d-eligible 6-root sub-book −0.22 | **C-c (skew −1.07), C-d (σ $3,768 a day)**; and the +0.16 is **one contract of palladium again** (+$85k of an +$82k total) — the equal-weight published book is **−0.11**, below its null's median; it is the two single sorts (ρ 0.72 / 0.80), both negative |
| the vol-scaled published cell of the same family | D559 | gross +0.11 (not a dollar cell; the vol-scaled dollar cell is the same object as the row above) | not dollar-neutral (net notional 21% of gross); family best +0.16 at its N2 null's median |
| **D561 (2026-09-19): D555's 12m trend book with a per-root leverage cap (CAP 1 / 5 / 10 / 20 on 0.40/σ), same signs, same 34-root minimum-size dollar book** | D561 | **+0.06 (SE 0.30)** — D555's dollar line re-emitted and asserted equal: a cap on return-space weights does not alter a one-contract-per-root book | **C-a, C-c (skew −0.61), C-d (σ $8,762)**, as D555. The cap is monotone in Sharpe (published gross +0.07 / +0.20 / +0.25 / +0.27 against +0.30 uncapped) and the worst day is the same macro session (2021-11-26) at every cap. **Role, not component:** on ES's worst 5% of days trend earns +0.26 σ at the 94th percentile of its rotation null (bar 95); on carry A's worst 5% of days it **loses 0.56 σ, below every one of 1,562 rotations** at ρ 0.18 — C-b is a body statistic, and any pair entered should carry the worst-day c5 with its null beside it |
| **D562 (2026-09-19): THE FORWARD READ — D555's 12m trend book on the reserved slice 2024-01-02 → 2026-09-09 (696 sessions), same 34-root minimum-size dollar book, $3/$6 RT + one tick, rolls charged. The 2024+ slice is now SPENT for trend, for carry timing, and for any assembled book containing either** | D562 | **+0.71 (SE 0.5)**; gross +0.73; Sortino +0.96; the C-d-eligible 19-root sub-book **−0.08** | **C-c (skew −1.52), C-d (σ $10,920 a day)**; and the +0.71 is **three full-size contracts** (NKD +$125k, HO +$112k, RB +$79k of a +$339k total). The published book earned **+0.51 gross / +0.50 net** forward (Sortino +0.71), inside its rotation null (p50 +0.18, p95 +1.30, rank 0.69), harness ρ 0.73 with AQR out of sample; the whole P&L is 2026. **Role, forward:** on ES's worst 5% of days trend **lost 1.29 σ, at the 5th percentile** of random sign books, ρ with ES +0.31 (in sample −0.13) — the "crisis alpha" reading failed out of sample with the sign inverted. Disposition B: return-component candidate for the personal book only, **not a hedge**; nothing for prop |
| **D564 (2026-09-20): basis-momentum as published (Boons–Prado 2019), twelve-month momentum of the first-nearby minus the second-nearby from the settlement strip, High4 long / Low4 short on 17 commodity roots, 16 traded at minimum size, monthly holds, $3/$6 RT + one tick, rolls charged** | D564 | **+0.36 (SE 0.32)**; gross +0.38; Sortino +0.51; the C-d-eligible 6-root sub-book (CL GC HG NG SI ZC) **+0.49 at σ $340** | **C-a (+0.36 < 0.5), C-d (σ $3,803; HO is 37% of the total)**; C-c passes (skew +0.01). The published book: **as pre-registered +0.42 gross, rank 0.80, DOES NOT PASS; under a formation-rule amendment repairing two calendar defects (2020-06-30 truncated, 2021-05-31 Memorial Day) +0.69 / Sortino +0.99, rank 0.972 / 0.971 / 0.975 in N1 / N2 / name-randomised N3, PASS** — the first of the deposit series; the amendment restored the 2021–2022 months that carry it. Two roots reach half the P&L (NG short 81 of 83 months, ZL); the nine non-seasonal roots read −0.09. Shares carry A's worst days at the 0.5th percentile (c5 −0.29 σ). 2024+ unread. The sub-book is a subset, not a construction; its own pre-registration is the next read |
| **D568 (2026-09-20): the corn post-harvest carry narrowing, flat by default — long H / short K by the grains delivery rule (T1 delivery ≥ m+2, asserted to survive the window), one ZC a leg (no micro), positioned December → February, flat otherwise, $6 RT + one tick a leg, four sides a window** | D568 (Stage 0 disclosed: the twelve per-window returns and their correlations were seen in D567) | **+0.43 (SE 0.29)**; gross +0.59 / Sortino +1.00 in dollars (return space +0.60 / +1.00); 24 positioned months, hit 0.58, median +0.14 %, worst −0.61 %; **+$760 total at one pair, σ $28 a day positioned**, cost $314 (29 % of gross) | **C-a (+0.43 < 0.5)**; C-c passes (skew +2.10), C-d passes with room. **DOES NOT PASS** its placement null (rank 0.848, p95 +0.706, exact) and **the always-on control earns more per positioned day (1.11 vs 0.90 bp)**: the corn front gains on its deferred all year, in April and June most and July least — the window samples a drift, and December itself loses 10 of 13. The merchant avatar fails in the COT (commercial net short falls through the window in 5 of 12). **Not entered.** ZC 2024+ unread |
| the same spread gated on the November stocks-to-use (≤ the median of prior Novembers) | D568 | +0.41 net; gross +0.51 / +0.90 on 12 positioned months | a declared, non-promotable secondary; opens 4 of 10 decidable windows including both losers (hit 0.50 vs 0.70 ungated); rank 0.897 of its own placement null; family best +0.60 at its N2 null's 82nd percentile |
| **D570 (2026-09-20, written as seen): the soybean harvest spread on the F/H pair, flat by default — short January / long March (first delivery strictly after November, next listed), formed at August's last session, held September → November, one ZS a leg (no micro), $6 RT + one tick a leg, four sides a window** | D570 (D567 Stage 0 and the D569 addendum read this object's per-year, per-month, gate, control and COT figures before it) | **+0.41 (SE 0.30)**; gross +0.49 / Sortino +0.69 in dollars (return space +0.40 / +0.54); 24 positioned months, hit 0.62, median +0.07 %, worst −0.64 %; **+$1,542 at one pair, σ $57 a day positioned**, cost 16 % of gross, max DD −$1,325 | **C-a (+0.41 < 0.5), C-c (skew −1.31)**; C-d passes. **DOES NOT PASS**: the schedule is real (the always-on short loses −0.80 bp a day; the rolled cousin under the mask is at the 99.3rd percentile of its exact placement null) but **the construction's own twelve-placement null puts Sep–Nov third — July → September on X/F earns +1.24 / Sortino +1.97** — and the rolled cousin beats the F/H pair per positioned day in sample (+0.67 vs +0.53 bp), which the seen table already showed on 2016–2023. **Not entered.** ZS 2024+ unread; the July placement is a null cell, seen, Stage 0 material |
| the same F/H spread gated on the August stocks-to-use (≤ the median of prior Augusts; seen in D569) | D570 | **+0.61 net**; gross +0.68 / +1.06; skew +0.54; 12 positioned months, hit 0.67, worst −0.16 % | the one cell clearing C-a; a declared non-promotable secondary on four windows (2016, 2021, 2022, 2023, all paid); below the July placement; not carried |
| the rule-rolled cousin under the same mask (X/F then F/H, one roll inside the window; D569's object) | D570 | +0.54 net; gross +0.80 / +1.24 | diagnostic; N1 rank 0.993; beats the primary per positioned day; eight sides a window |
| **D571 (2026-09-20, Stage 0 with the placement predicted from soybeans): the same short-spread construction, one declared placement a root — ZC Jul–Sep Z/H, ZW Apr–Jun N/U, ZL Jul–Sep V/Z, ZM Jul–Sep V/Z — one contract a leg, four sides a window, the twelve placements as the enumerated null** | D571 | ZC **+0.21** (gross $ +0.41; return space +0.35 / +0.54); ZW **+0.22** (−0.01 / −0.01); ZL **−1.15** (−1.13 / −1.42, −$3,390); **ZM +0.29** (gross +0.35; return space +0.42 / +0.77; skew +6.95, σ $68, +$1,304) | all four fail **C-a**; ZL fails C-c. Meal is the one candidate by the design's rule (best of twelve on both windows, above its control) and its return is September alone. The cross-root prediction held on corn and meal and was falsified on wheat and oil: **not supported, chance level**. Corn's real structure is a different pair (old-crop U against new-crop Z, Jun–Aug, 13 of 13, +0.75 / +1.04), a null cell, seen. **No entry** |
| **D573 (2026-09-20): hedging pressure as published (Basu–Miffre 2013), 16 commodity roots ranked on the 13-report mean of commercial long / (long + short) from the CFTC legacy report keyed on the release date, long the lowest 6 / short the highest 6, monthly holds, 16 traded at minimum size, $3/$6 RT + one tick, rolls charged** | D573 | **−0.065 (SE 0.29)**; gross −0.05; Sortino −0.09; **−$46,439 over 2016–2023**, σ $5,504 a day; the C-d-eligible 6-root sub-book **−0.06 at σ $573** (fails all three bars together); the EW published book −0.20 gross / −0.28 Sortino, net −0.21 | **C-a, C-d** (sub-book also C-c, skew −0.50). **DOES NOT PASS**: below its time-rotation median (rank 0.076, p50 +0.085) and at the 26th percentile of the name-randomised null (p50 +0.01); the sort is the predicted static tilt (metals long 71–97 % of month-ends, NG and ZW short 92–98 %) and the tilt lost — short the energies through 2021–22 (HO −$138k, CL the largest loser in book units), long palladium the one winner (+$207k). The de-meaned cell is worse (−0.23). ρ with the term-structure sort on the same 16 roots +0.18. **Not entered.** The deposit's list is scored end to end; skewness and value remain parked |
| the vol-scaled and de-meaned published cells of the same family | D573 | −0.38 / −0.24 net (gross −0.37 / −0.23) | every cell negative; family best −0.065 (the dollar cell) at its N2 null's 22nd percentile |
| **D574 (2026-09-20): THE FORWARD READ of basis-momentum (D564) on 2024-01-02 → 2026-09-09, on the principal's word — the same 16-contract minimum-size dollar book and its six-root C-d sub-book, scored on the unread slice. The 2024+ slice is now SPENT for basis-momentum in every form on the 17 commodity roots** | D574 | dollar **+0.99 net / +1.54 Sortino forward** (in sample +0.36), **+$251,187**, σ **$5,791**, max DD −$94,522, **HO +$154k = 61 %**; sub-book (CL GC HG NG SI ZC) **+0.04 net**, +$428, σ $253; the EW published primary +0.48 gross / +0.69 Sortino forward (in sample +0.69), rank 0.73 / 0.80 in the full-span rotation and name-randomised nulls (p95 ≈ +1.0 on 33 months) — **INSIDE** | **Nothing enters**, as the pre-registration declared before the number: the dollar book failed C-a and C-d in sample and its forward number is one heating-oil contract in the spring-2026 energy move (March 2026 +13 % of the published book; 2025 −0.35); the sub-book was a declared subset under the bar and is flat forward. **The composition inverted**: the seasonal roots that carried the in-sample result read −0.47 forward and NG was never short; the nine non-seasonal roots read +0.84. The amendment is inert forward (as-pre-registered identical). Slice spent; no clean test remains on this line |
| **D575 (2026-09-20, Stage 0 with the placement predicted from each root's supply calendar): D570's short-spread construction, one declared placement a root — HE Aug–Oct Z/G, LE Apr–Jun Q/V — one contract a leg, four sides a window, the twelve placements as the enumerated null** | D575 | HE **−0.15** (gross −0.10; return space −0.28 / −0.38; 2020 window −17.2 %; σ $187, −$1,786); LE **−0.08** (return space −0.08 / −0.11; σ $130, −$666) | both fail **C-a**; neither best of its twelve (ranks 3 and 2 of 11 others). The hog prediction was **falsified** (the predicted placements are the three most negative); cattle's best placement (Feb–Apr M/Q, +0.63 / +0.84) was named by neither avatar and is a null cell. **No entry.** The seasonal-spread line on the commodity curve has no open construction |
| K2 last-30-min momentum NQ, 1 MNQ, $3 | D466 (D463) | −0.01 (0.40); gross +0.66 | C-a. cost 102% of the gross mean |
| K3 last-30-min momentum ES, 1 MES, $3 | D466 (D463) | −0.29 (0.41); gross +0.62 | C-a; ρ(K2,K3) = 0.73 — one construction across roots |
| K4 last-30-min momentum YM, 1 MYM, $3 | D466 (D463) | −1.12 (0.48); gross +0.08 | C-a; no gross edge |
| K5 C1 on S1 nights (SPY gate), 1 MES | D466 (D464) | +0.36 (0.40) | C-a; a gated subset of K1 (ρ 0.35) |
| K6 C1 on S2-exposure nights (SPY gate), 1 MES | D466 (D464) | +0.39 (0.29) | C-a; C-c skew −1.21; a gated subset of K1 (ρ 0.26) |

| **D468 (2026-09-12): 24 session windows on eight roots**, W1 18:00→16:00, W2 18:00→09:00, W3 09:00→16:00, long only, minimum size, $3 ($6 on ZN/ZB) | D468 (D467) | family-max null p50 +0.55, p95 +0.95; observed best +0.39 (78th pct of the null) | **C-a on all 24**; nothing provisional |
| ES-W1 (1 MES) / NQ-W1 (1 MNQ) / YM-W1 (1 MYM) | D468 | +0.39 (0.32) / +0.38 (0.32) / +0.15 (0.33); gross +0.64 / +0.54 / +0.47 | C-a; ρ 0.91–0.92 among them (one construction); YM also C-c |
| ES-W2 / NQ-W2 / YM-W2 (the overnight leg) | D468 | +0.19 / +0.26 / +0.04; gross +0.63 / +0.56 / +0.60 | C-a; cost 54–93% of the gross mean — the edge is here and the micro cost is too |
| ES-W3 / NQ-W3 / YM-W3 (the day leg) | D468 | +0.04 / +0.10 / −0.25; gross +0.35 / +0.29 / +0.14 | C-a |
| ZN-W1/W2/W3 (1 ZN, $6) | D468 | −0.20 / −0.29 / −0.35; gross ≈ 0 | C-a; no micro; σ $290–400 a day |
| ZB-W1/W2/W3 (1 ZB, $6) | D468 | +0.01 / −0.08 / −0.08; gross ≈ 0 | C-a; **C-d** σ $682–939 (> 1% of the account); no micro |
| GC-W1/W2/W3 (1 MGC) | D468 | −0.23 / −0.19 / −0.63; gross +0.09 / +0.25 / −0.17 | C-a |
| CL-W1/W2/W3 (1 MCL) | D468 | −0.39 / −0.31 / −0.69; gross −0.09 / +0.14 / −0.30 | C-a; C-c |
| 6E-W1/W2/W3 (1 M6E) | D468 | −0.72 / −1.17 / −0.85; gross +0.01 / −0.21 / +0.24 | C-a |

| **D470 stage 0 (2026-09-12): four declared gates on ES/NQ W1 and W2** (continuation, prior overnight leg, 200-average, vol tercile), 32 cells | D470 (D467) | best gated component: ES-W2 after a DOWN overnight leg +0.70 (0.26), NQ-W2 +0.62 (0.25); clears N1/N2, **not the family-max p95** | stage 0 — a PICK, not a component: the reversal sign is on 8 of 8 cells but its size is 2020–2022; continuation is the wrong sign everywhere; 200-average clears every null on ES (+0.44) and reverses on NQ; only the unread 2024+ slice can promote it. **D472:** fails the family bar on the z and Sharpe scales too (2.78 vs p95 3.13; +0.70 vs +0.79 — the null is centred on the drift, and eight years cannot beat the best of eight); **replicates on SPY and IWM cash 2010–2015** (gap after a down gap +5.5 / +7.7 bp vs ≈ 0, 1.9 / 2.0 SE, both single nulls cleared, 11 of 12 symbol-years); the step-3 criterion is not met on one of four conditions; the prior-session variant does not replicate; RTY held back on G2 |

| **K7 (candidate, D473): long the NQ overnight leg 18:00→09:00 on nights after a negative overnight leg, 1 MNQ, $3** (ES 1 MES the check root; 09:30 exit the declared secondary) | D473 (D470, D472) | **+0.62 (0.25)**; gross +0.80; 887 of 2,009 nights; diff vs other side +$14.89 (2.1 SE); N1/N2 cleared; ES +0.70 (0.26), 2.5 SE; 09:30 exit +0.45 (worse) | **C-a passes on the point estimate; NOT entered: the D470/D472 family bar failed (z 2.78 vs p95 3.13) and the cell was selected in-sample.** Replicates on SPY/IWM cash 2010–2015. 71% of the gated P&L follows falls > 1% (16% of nights). ρ(K1) 0.39. Worst night −$794 at one micro, none below −2%. **Forward read run 2026-09-12 on the principal's word: REMOVED** — 2024-01→2026-09: NQ gated +$30.76 vs other +$21.29 (+0.4 SE; in bp −1.02), SPY cash gap after a down gap +0.71 vs +9.22 bp (−1.6 SE), IWM −1.5 SE, pooled z −1.30; the gated nights paid (forward net Sharpe +0.76) and so did the others; the reversal structure did not carry. **The 2024+ slice is spent for the overnight leg on NQ/ES and the cash gap on SPY/IWM.** |

| **D490 (2026-09-12): the principal's range-reversion rule** — bottom 5% of yesterday's range on a 2× volume spike, target the top 5%, trail from the last swing past the midpoint; short symmetric; 1 MES / 1 MNQ, $3 + fills; development 2016-02→2020 | D490 | ES pooled **−1.14 (0.38)**, gross −$3.48/trade; NQ −1.03, −$4.96; long −0.60 / short −1.03 | C-a by a wide margin on both roots; below the wrong-range control (≈ $0); 60% of longs are breakdowns below yesterday's low; target reached on 5% of trades; not taken to validation |

| **D492 (2026-09-12): D490's rule with an hourly RSI(14) confirmation** (long ≤ 30 / short ≥ 70; cell A with the spike, cell B in place of it); development 2016-02→2020 | D492 | ES A **−0.30 (0.38)**, gross −$0.88 on 287 trades; ES B −0.40; NQ A −0.11 (+$1.57); NQ B +0.12 (+$4.49) | C-a on every cell; below the wrong-range control on both roots (NQ N1 p50 +$5.4–5.9); the target reached on 0–3% of trades; 92 long trades on ES (SE ≈ $16); no validation read |

| **D495 stage 0 (2026-09-12): the day session after a daily state, intraday** — cell A fades the next session after a top-decile day (causal), cell B trades it after a daily RSI(2) extreme; 09:30 open + tick → 15:59 close; 1 MES / 1 MNQ, $3; 2016–2023 | D495 | **NQ A long +0.47 (0.25)**, +$42.61 gross on 110 trades, +21.9 bp vs +10.2 on the other side (z +0.78); NQ A short +0.21; ES A +0.08 / +0.09; B long +0.09 / +0.00; B short −0.28 / −0.38 | **NQ A long a PICK** (own null and 0.3 cleared; family-max z p95 +2.45 not cleared: most of it is the day session's drift after any down day, +10.2 bp on 761 days — post hoc, not scored); all other cells closed; 2024+ day session unread |

| **D498 (2026-09-12): the second-clock cells** — E1 turn-of-month long day sessions, E2 FOMC decision days long 09:30→14:00, E3 the first-30 fade at 15:30; NQ and ES; one micro, $3 | D498 | NQ +0.22 / +0.18 / −0.53; ES +0.15 / +0.02 / −0.94 | C-a on all; E1 +6.9 bp vs +3.7 other side (z +0.46), E2 +2.8 bp (z +0.06), E3 +0.4 bp; none clears its rotation null; ES K8 +0.18 (the check root, below C-a) |
| **D499 stage 0 (2026-09-13): fade the next hour after a top-decile hourly move**, causal per hour-of-day, thin vs thick hours by volume (11 / 10 of the 21 entry hours), k = 1 primary (k = 2, 3 and the US-clock split secondary); eight roots; one micro, $3 ($6 ZN/ZB); exits by 15:59; 2016–2023 | D499 (D467) | 16 primary cells: **15 negative**, ZB thin +0.02 (0.29); best gross +$2.46 a trade (NQ thick) against $3; family-max z p95 +2.70, observed +1.84 (CL thin; 43% of offsets) | **C-a on all 16; CLOSE recommended.** The reversal is real on the US-clock off-hours of ES/NQ/YM (pooled β −0.03 to −0.04 outside exact rotation bands; the `us_off` fade clears N1 on ES and NQ) at 1.7–4.9 ticks a trade, net negative after the fee; the fee is 7–24% of the expected hourly move on the micros, so the hourly clock fails the yardstick before any signal; low-relative-volume moves revert *less*; 2024+ unread on every root |

**Line closed by the principal, 2026-09-12:** the index overnight leg at micro cost (any gate,
window or size) is closed for the prop book after D466–D473; open for the personal book at full
size. See BOOK_PROP's closure section.

**Correction recorded 2026-09-12 (D466 RESULT):** the figures that motivated this ledger (C1 0.62,
NQ last-30 0.42, equal-risk book 0.91) were computed at full-size cost in basis points (1.1 bp a
round trip); at the standard's minimum size and $3 they are 0.37 and −0.01 and there is no book.
The gross edges (0.63, 0.66 at micro size) are real; the cost per round trip at micro notional
(~2 bp) eats them. Every component line from here on is computed by the runner under this
standard, never in a shell line.

---

## AMENDMENT, 2026-09-12 — **C-b no longer rejects. It ROUTES. And a second book gets a second account.**

*Directed by the principal.*

> *"On the ρ < 0.3, I understand where we are going here but they should still be permitted into
> a secondary strategy 'vault' where we can build a second prop book that can run on a different
> account."*

### The change

**C-b was the only criterion that failed a construction for something it does not control.** A
component with a real, independent edge could be discarded purely because something already in
the ledger moves with it — which says nothing about the construction and everything about the
order things were tested in.

**C-b is therefore no longer a rejection. It is a routing rule:**

| a construction that… | goes to |
|---|---|
| clears **C-a, C-c, C-d, C-e** and has **ρ < 0.3** against every component in **Book 1** | **Book 1's ledger** |
| clears **C-a, C-c, C-d, C-e** but **ρ ≥ 0.3** against something in Book 1 | **THE VAULT** |
| fails **C-a, C-c, C-d or C-e** | not a component; recorded in *Scored and NOT entered* as before |

**C-a, C-c, C-d and C-e are unchanged and still reject.** Only C-b's consequence changed.

### Why this is more than a consolation prize — and it is the reason it works

**Each prop account carries its own independent 4% trailing drawdown floor.** Two correlated
books on ONE account share a floor, and correlation is then fatal: both arms draw down together
against a single barrier. **Two correlated books on TWO accounts do not share a floor** — a
breach on account 2 does not touch account 1.

So the vault is not "the leftovers". It is **the set of constructions whose edge is real and
whose only defect is that it duplicates a risk already taken — which stops being a defect the
moment it is taken on a separate drawdown budget.**

**What this costs, stated plainly:** a second account is a second fee, and under the amended
[P4](RULES.md#r11) that fee enters the arithmetic directly. Two accounts must clear **two**
cost bars, not one. A vault component is worth running only if it clears P4's profit-before-breach
test **against its own account's fee**.

### The vault's own rules

1. **The vault has its own C-b, applied WITHIN the vault.** Book 2 is built from vault components
   and needs the same internal decorrelation Book 1 does: a vault entry needs **ρ < 0.3 against
   every component already in the VAULT**. A construction correlated with Book 1 *and* with the
   vault goes to a third holding area, and the same logic recurses.
2. **Order of entry is recorded**, in the vault as in the ledger, because ρ is measured against
   whatever was already there.
3. **Cross-book correlation is REPORTED, never screened.** ρ(Book 1, Book 2) at the book level is
   carried in both books' records. It does not gate anything — the separate floors are the point —
   but a reader must be able to see how much of the two accounts' risk is the same risk.
4. **Hurdle P is tested per account, on that account's assembled book.** There is no combined
   hurdle-P test across accounts, because there is no combined drawdown floor.
5. **The vault admits nothing to any book by itself.** A vault entry is a component awaiting a
   second book, exactly as a ledger entry is a component awaiting the first one. Only an
   assembled book enters `BOOK_PROP.md`, and only on hurdle P.

### The vault

| # | component | instrument, window, rule | record | net Sharpe (SE) | ρ with Book 1 | ρ with prior vault | entered |
|---|---|---|---|---|---|---|---|
| — | *no entry* | | | | | | *the vault was created empty on 2026-09-12; nothing has yet cleared C-a to be routed* |

**Note on what this does NOT retroactively admit.** Every construction in *Scored and NOT
entered* above failed **C-a**, not C-b — with one exception, **K7**, which passed C-a on its point
estimate and was held back for the family-bar failure and in-sample selection, then **removed on
its forward read**. So the vault starts empty and no prior verdict is reversed by this amendment.
The routing rule takes effect for constructions scored from here.

| **D504 stage 0 (2026-09-13): the Asian chip session into the US semiconductor day** — the EWT+EWY overnight gap relative to QQQ, residualised causally on the semis' own relative gap, traded 09:45 → 16:00; twelve declared cells on the 15-minute ETF fixture plus the prop arm MNQ/MES at $6; 2018–2023 | D504 | **P5 (the only prop-eligible expression) gross −$13.76 a trade, net −$19.76 against $6, net Sharpe −0.38, hit 40%, ρ with K8 −0.15**; the cash primary +8.0 ± 8.4 bp against 11.7 bp crossed | **C-a; and by venue the cash pair is personal-book-only (the prop accounts are futures-only).** The channel is real but clears in the GAP (+25.6 bp at t +4.25) and leaves −1.7 ± 2.6 bp for the day; a control sector with no mechanism (transports) was the family maximum; nothing clears the eleven-cell family p95 of +2.56. Vehicle measurement kept: the unconditional MNQ/MES pair's daily σ is $128 against one MNQ's $282 |

**Line closed by the principal, 2026-09-13:** the **hourly clock** (any hourly-horizon construction
on the eight gated roots at micro cost) is closed for the prop book after D499. The reversal it
measured is real on the US off-hours clock and worth a tick; the fee is 7–24% of an hourly move on
the micros. See BOOK_PROP's closure section and FINDINGS §70. Nothing spent; 2024+ unread.

---

## THE ONE-PASS FORWARD READ IS SPENT — D503, 2026-09-13

**On the principal's word.** The read [BOOK_PROP](BOOK_PROP.md) parked K8 for, taken once on
**2024-01-02 → 2026-09-09**, 652 union sessions, for K8, the MACD component **and** the assembled
book together. **The slice is now SPENT for all three. Nothing may be re-read, re-scored or
sharpened on it.**

| | in-sample | forward | verdict |
|---|---:|---:|---|
| **#1 K8** — long 1 MNQ, 09:30+tick → 15:59, after a down day | net Sharpe **+0.595**, gross **+$17.87**/trade, hit 57%, z +2.89 | net Sharpe **−0.160**, gross **−$4.46**/trade, hit 50.6%, z **+0.02**, total **−$2,297** | **PROVISIONAL** by D498 §3's own rule (REMOVED needs Sharpe < −0.3 *or* a negative difference; it reads −0.16 and +0.2 bp). **The rule says PROVISIONAL; a negative GROSS mean says the edge is gone.** Its own N1 null: p95 +7.7 bp against +0.9 bp observed — does not clear |
| **#2 the MACD component** — 1 MNQ, NQ day session, both log MACDs agree, min hold 5 h, flat 16:00 | net Sharpe **+0.723**, σ $180, skew −0.05, best day 6.7% of total | net Sharpe **+0.736**, σ **$340**, skew **+0.68**, kurtosis **12.1**, best day **84.9%** of total | **FULL** by D503 §3's rule (Sharpe > 0.5, gross > 0) — **and not to be trusted on it**: it does **not** clear its own rotation null (obs +0.736 against p95 +0.758, −0.8 SE, UNRESOLVED), 3 of 632 sessions carry half the P&L, and the **mean per trade ex-top-1% is −$0.59** |
| **ρ(#1, #2)** | **+0.190** | **+0.197** | C-b cleared on both windows — the most stable number in the read, and it did not help |

**The assembled book is NOT admitted.** Un-netted, 1 MNQ each, summed: net Sharpe **+0.364** —
**worse than its best arm alone (+0.736)**, because layering only helps when the arms' Sharpes
are comparable and a −0.16 arm subtracts whatever ρ does. Hurdle P: **P3a 6.96 breaches/yr
against a bar of 1.0, FAIL**; **C-d σ $534 against $500, FAIL**; worst day **−$2,724 = 136% of
the account's entire $2,000 loss budget**; **empirical trailing-4% life 31 sessions, 20 deaths**
in the slice. Book-level alignment null: observed +0.364 against a p50 of **+0.398** — the arms'
real alignment is worse than random, at −87.5 SE.

**And the load-bearing finding is about the CONTRACT, not either signal.** Daily σ nearly doubled
on an unchanged strategy ($180 → $340) because **MNQ pays $2 an index point and NQ's level
roughly doubled** between the windows. At 2026 price levels **one MNQ is too large for a $50k
account with a $2,000 trailing floor**: the single-arm worst day is 88% of the whole loss budget
and the book's is 136%, and there is nothing smaller than one micro. D493 found the full contract
too big; the micro is now too big as well. Every C-d, P3 and P4 figure quoted in this ledger from
a 2016–2023 window is a **price-level artefact** and must be recomputed per year.

**What is NOT closed:** the constructions. Gross is +$19.68 a trade forward against a $3.50 cost,
so the signal pays — the barrier no longer fits the contract. Closing an avenue is the
principal's.

**ENTRY #1 (K8) CLOSED BY THE PRINCIPAL, 2026-09-13.** Tested forward in D503 and it did not
transfer (gross −$4.46 a trade, net Sharpe −0.160, difference z +0.02). D498 §3's rule returned
PROVISIONAL; the principal closed it on the negative gross mean, which the rule did not name.
**The ledger holds no live entry.** See BOOK_PROP's closure section of 2026-09-13.

| **D506 stage 1 (2026-09-13): the in-play filter on the day session** — the causal overnight range-and-volume score, top decile against the rest, on two signals the repo already owns (the day drift; D484's log MACD at d−1) across eight roots, one micro, $3 ($6 ZN/ZB); 2016–2023 | D506 | primary YM-MACD **in play −$10.61 gross a trade, net Sharpe −1.32**, against +$2.10 on the rest; Δ of (2p−1) − fee/E\|M\| = **−0.0504**, 73% of its exact offsets above it; 16-cell family p95 +0.2192 against an observed max of +0.0620 | **C-a; CLOSE.** The fee lever is real (+0.85 points, positive 16 of 16) and accuracy falls by **−2.09 points** (negative 11 of 16). The untradeable bound — conditioning on the day's REALISED range — is −0.0018, so there is no prize even with perfect foreknowledge of the day's size. **Kept:** the same filter cuts P3a three to five fold (ZB 14.00 → 2.71 a year), so selectivity is a drawdown instrument, not a selector (FINDINGS §72) |

**Line closed by the principal, 2026-09-13:** the **in-play construction** — conditioning a day-session signal on how active the
overnight session was, as a way of choosing *when* to trade (D506). The fee lever is real (+0.85 points, positive 16 of 16) and
accuracy falls by −2.09 points; the untradeable bound, conditioning on the day's REALISED range, is −0.0018, so the whole family
goes, not just its causal version. **The premise is KEPT as a survival-layer instrument**: `scripts/activity_filter.py`, which cuts
P3a three to five fold and must never be used to choose direction. See R11's P3 amendment and BOOK_PROP's closure section.

**Line closed by the principal, 2026-09-13:** **cross-market-into-the-open** — any construction that
reads a foreign market before the US open and enters at or after it (D494 at index level, D504
cross-sectionally). The Asian chip channel is real and clears in the gap (+25.65 bp at t +4.25 into
the gap, −1.65 ± 2.6 bp into the day); a control sector with no mechanism was the family maximum.
Kept as measurements in FINDINGS §71. Nothing spent on the 15-minute fixtures.

---

## ENTRY #1 RETIRED — K8 is CLOSED, 2026-09-13, on the principal's word

> *"Retire K8 as closed and admit the MACD into the book."*

**K8 is retired as CLOSED**, not parked and not provisional. Its forward read (D503, from K8's own
guarded command) on 2024-01-02 → 2026-09-09, 308 trades:

    gross -$4.46 a trade (in-sample +$17.87)   hit 50.6% (was 56.9%)   net Sharpe -0.16 (was +0.61)
    after-down minus after-up  +0.2 bp at z +0.02   (in-sample z +2.89)
    total -$2,297   by year 2024 -$3,506 / 2025 +$4,658 / 2026 -$3,449
    its own N1 null: p95 +7.7 bp against +0.9 bp observed -- does NOT clear

**D498 §3's rule returned PROVISIONAL** (REMOVED needed net Sharpe < −0.3 *or* a negative
difference, and it read −0.16 with +0.2 bp). **The principal has closed it anyway, and the reason
is sound: a negative GROSS mean is not a cost failure, it is the signal having stopped paying.**
The rule's letter is recorded above; the principal's judgement overrides it and the record says
both.

**What K8 leaves behind.** Its provenance was selection (seen as D495's control before D498
declared it), and the forward read is exactly what that provenance predicted. **ES K8 — dismissed
in-sample as "the same sign at half the size" — was the arm that worked forward** (+4.4 bp, net
Sharpe +0.22). That is what noise looks like, and it is the cleanest illustration this ledger has
of why an in-sample pick needs a forward read. **The 2024+ slice is spent for K8 and may never be
re-read for it.**

## ENTRY #2 — the MACD day-session arm, ADMITTED, 2026-09-13

**The ledger's first non-provisional entry.** Order of entry: second, after K8, and with K8 now
retired it is the **only live entry**, so C-b is trivially satisfied for it.

| | |
|---|---|
| **instrument, size** | NQ front month by volume, traded as **one MNQ** |
| **window** | day session only: decide at the close of each hour from **h09**, execute at the next hour's open |
| **signal** | the **log Impulse MACD (34/9)** and the **plain log MACD histogram (12/26/9)** must **agree in sign**; `md == 0` is a no-trade state |
| **exit** | when the signal turns, after a **minimum hold of 5 hours**; **forced flat at the close of h15 (16:00 ET)** |
| **cost** | **$3 commission + 1.009 ticks** crossing = **$3.50** a round trip |
| **published defaults, never tuned** | both MACDs at their canonical / LazyBear parameters |

### Scored on 2016-01-04 → 2026-09-09, 2,508 sessions, 2,543 trades ([D504](decisions/D504-the-MACD-arm-across-every-year-the-fixture-holds.md))

| | | |
|---|---:|---|
| **C-a** net Sharpe > 0.5 | **+0.698** (SE 0.353) | **PASS** |
| **C-b** ρ < 0.3 | ledger has no other live entry; ρ with the retired K8 was +0.190 | **PASS** |
| **C-c** skew ≥ −0.5 | **+0.555** | **PASS** |
| **C-d** daily σ ≤ $500 | **$233** | **PASS** — but **$386 in 2026 alone** |
| **C-e** provenance | D484 signal · D491 machine · D495 pre-reg · **D503 forward read** · D504 full history | **PASS** |

gross Sharpe +0.941 · mean +$10.25/session · total **+$25,697** · maxDD $7,814 · hit 50.5% ·
payoff 1.13 · **gross $13.61 a trade = 3.88× the $3.50 cost** · trips 1.01/session ·
**rotation null: observed +0.698 against p95 +0.272 → +35.3 SE, CLEARS**

**Forward-read provenance, which is what makes this a full entry rather than provisional:** the
2024-01-02 → 2026-09-09 slice was read once, on the principal's word, under a rule declared before
the read (D503 §3: FULL if net Sharpe > +0.5 and gross > 0). It returned **net Sharpe +0.736,
gross +$19.68 a trade → FULL.** **That slice is now spent and may never be re-read.**

### The three qualifications that travel with this entry

1. **It is a REGIME construction.** 2020 + 2022 + 2025 + 2026 carry **96%** of the total; 2016,
   2017, 2019, 2023 and 2024 are flat to negative (−0.04% to −1.51% of the account each). Quote
   this wherever the entry is quoted.
2. **P3a passes pooled and fails in the recent years individually** — 0.50/yr pooled against a bar
   of 1.0, but **2.14 in 2022, 2.17 in 2025, 1.53 in 2026.** A rate bar calibrated on a pooled
   window does not survive a price level that doubles.
3. **C-d passes at $233 pooled and reads $386 in 2026**, against a $500 cap. One MNQ is now
   **1.10× the account's notional** (0.18× in 2016) — see D504 §4. The margin is thinning, and it
   is a property of the price level, not of the construction.

---

## AMENDMENT to ENTRY #2, 2026-09-14 — **the crossing assumption is optimistic by 2.4×, because the arm fills at the worst minute of the day. The entry stands.**

*[D527](decisions/D527-the-arm-fills-at-the-worst-minute-of-the-day-and-its-crossing.md).
Nothing about the construction changes and no code was touched; this corrects the COST LINE the row
is scored under. Raised by the micro-spread census of 2026-09-13, which found MNQ's quoted spread
has a median of 1.00 tick and a **mean of 1.55**, with only 56.8 % of trades seeing a one-tick market.*

**The arm does not fill at an average moment.** `d491_conditional_hold` fills at the OPEN of an hourly
segment and is forced flat at the CLOSE of h15, so every fill lands at `hh:00` ET or at 15:59. Traced
over the in-sample window with a copy of `simulate` asserted **bit-identical** to the committed one
(1,876 sessions, 1,908 round trips):

| | share of entries | measured spread |
|---|---:|---:|
| **10:00** | **66.6 %** | **3.66 ticks** — one-tick only **19.5 %** of the time |
| 11:00 | 9.2 % | 1.79 |
| 12:00 | 6.8 % | 1.49 |
| 13:00 | 3.8 % | 1.52 |
| 14:00 | 1.9 % | 3.35 |
| 15:00 | 11.7 % | 1.46 |
| day-session baseline | — | 1.61 |
| the forced flat at 15:59 (**75 % of exits**) | — | **1.44** — the day's *best* moment |

**Two-thirds of entries land on the single worst spread minute of the session, and that is
structural, not luck**: the arm decides at h09's close and fills at h10's open, and two-thirds of the
time the signal already agrees at 09:59 so it enters immediately. 10:00 and 14:00 are the two
scheduled-announcement hours — a plausible mechanism, observed rather than tested.

### The corrected cost line

| | ledger | measured |
|---|---:|---:|
| round-trip crossing | 1.009 ticks | **2.411 ticks** |
| round trip | **$3.50** | **$4.21** (+20.3 %) |
| net per trade | $10.11 | $9.40 (−7.0 %) |
| in-sample net Sharpe (2016-2023) | **+0.724** | **+0.661** |
| in-sample total | $15,423 | $14,086 |

**C-a's bar is 0.5 and the entry clears at the corrected cost**, which is why this is an amendment and
not a retirement. The Sharpes above are the **in-sample window alone** and are therefore not the row's
headline **+0.698**, which is scored 2016-2026 and includes the spent forward slice; that slice was
**not re-read** here and the row's headline figure is **not restated**. A full re-score at the
corrected cost would have to read it, and must wait for a reason better than this.

### What the correction does NOT establish, and the bias runs in the arm's favour

**tbbo spans 2025-09-11 → 2026-09-11; there is no quote data at the arm's historical entries.** This
prices the arm **today**; it does not reprice the backtest. And the error is one-sided: NQ was ~4,000
in 2016 and is ~27,000 now against a **fixed $0.50 tick**, so the tick was relatively **~7× coarser**
then, and a coarser tick locks a market at one tick more often. **The historical spread in ticks was
probably tighter than measured**, so $4.21 is closer to an upper bound on the in-sample cost than an
estimate of it. It is the right number for **deployment**, which is the decision it bears on — the
same mechanism as [one micro has grown into the prop barrier], where the contract's relative
coarseness moved underneath a fixed assumption.

**An obvious mitigation is NOT taken here:** entering a few minutes after the hour, or skipping h10,
would avoid the worst quote. That is a **different construction**, and this entry is admitted and
frozen — it would need its own pre-registration, not a quiet edit to a component already in the
ledger.

## AMENDMENT to ENTRY #2, 2026-09-29 — **expectation cut to Sharpe 0.24; account moved to MFFU Rapid 150k. The entry stands, spec unchanged**

**On the principal's word, after D669, D670 and D673:**
- the arm's in-sample 0.72 is the top of a 486-cell neighbourhood whose median is **0.24 net**;
- its deflated Sharpe fails;
- no plain statement of its behaviour carries to YM, RTY or ES, or clears its null on NQ.

**What changes on this ledger:**
- The entry's **expected net Sharpe for any assembled book is 0.24.**
- **C-a is not re-scored:** it was passed on the measured +0.698, and the ledger does not rewrite a score.
- **C-d's 2026 reading ($386) now sits against a 150k account** ([D674](decisions/D674-the-macd-arm-resized-to-the-150k-account.md)).
- The account change is recorded in `BOOK_PROP.md`'s amendment of the same date.

---

## SCORED, NOT ENTERED — the LETF close-flow cells, 2026-09-27 ([D640](decisions/D640-RESULT-letf-close-flow-killed-by-its-own-11am-placebo.md))

Component lines as D639 §10 requires, whatever the verdict: 1 micro, D639's cost (MNQ $4.07, MES $4.42 a round trip),
daily net Sharpe over all calendar days, **2016-01-04 → 2025-02-28** (a longer window than this ledger's 2016–2023
standard; the 2024+ part is the line's own unread slice, not another line's). Correlations are with D466's committed
series over 2016–2023.

| construction | record | net Sharpe (all days) | why not |
|---|---|---|---|
| LETF flow, NQ, enter 14:30 → exit 16:00 on active days (I ≥ 3× cost), 1 MNQ | D640 | +0.49; per-trade Sharpe 0.49 net / 0.74 gross; 944 trades | **killed at Gate 1**: its 11:00 placebo is significant (t 2.08); 2024+ −0.2 bp (t −0.07); ρ K2 +0.52 |
| the same at 15:00 | D640 | +0.73; per-trade 0.73 net / 1.04 gross; 961 trades | killed at Gate 1 as above; 2024+ +0.9 bp (t 0.33); **ρ K2 +0.59, K3 +0.53**: largely the last-hour momentum K2 already scores |
| the same at 15:30 | D640 | −0.08 | **ρ K2 +0.83: the same construction as K2** (D639 §10's 0.7 bar), not a new component; below the model's own claim (LETF-A7) |
| LETF flow, ES, 14:30 / 15:00 / 15:30, 1 MES | D640 | +0.50 / +0.52 / +0.23 on 60 / 69 / 68 trades | H1 fails in all three; no activation after 2023; overnight give-back −35 to −51 bp (H5) |

## SCORED, NOT ENTERED — the shock classifier's classes, 2026-09-28 ([D643](decisions/D643-RESULT-shock-classifier-fails-gate-1-on-all-four.md))

Component lines as CLAUDE.md requires, whatever the verdict (`scripts/shock_component_line.py` →
`data/shock/phase3_component_lines.json`; descriptive, not a D642 test). Each z = 4 shock is traded exactly as D642's
runner scored it: the t0+1 fill, a 30-minute time exit, 1 micro, and s.5.1's cost in dollars (MNQ $4.57, MES $5.67,
MCL $6.03, MGC $6.93 a round trip). Every trade is kept (path-invariant; the slot-limited book was Phase 5's, which
Gate 1 stopped). Daily net Sharpe over every usable session on the ledger's 2016–2023 window (√252). Correlations are
with D466's committed series over 2016–2023.

| construction | record | net Sharpe 2016–23 (Sortino); gross | why not |
|---|---|---|---|
| shock INFO (follow), NQ / ES / CL / GC, 1 micro | D643 | −1.24 (−1.60) / −2.28 (−2.75) / −2.91 (−3.44) / −2.42 (−3.06); gross −0.19 / −0.25 / −0.04 / +0.27 | Gate 1 failed; gross $0.14–$0.74 a trade against a $4.57–$6.93 round trip; 225–378 trades a year; \|ρ\| with K1–K6 ≤ 0.13 |
| shock LIQ (fade), NQ / ES / CL / GC, 1 micro | D643 | −0.02 (−0.04) / −0.59 (−0.64) / +0.04 (+0.06) / −1.16 (−1.34); gross +0.09 / −0.47 / +0.46 / −0.09 | Gate 1 failed; NQ/ES/CL on 9 / 6 / 4 trades a year, carried by the 2020 crash (CL −0.03 ex-2020); GC's 34 a year are a clean null; \|ρ\| ≤ 0.14 |

## SCORED, NOT ENTERED — month-end rebalancing flow, 2026-09-29 ([D685](decisions/D685-RESULT-mechanism-only-the-month-end-flow-replicates-and-fades.md), [D686](decisions/D686-RESULT-no-variant-rescues-it-and-the-fade-is-not-liquidity.md), [D687](decisions/D687-DIAG-the-month-end-flow-stopped-moving-prices.md))

Component lines as CLAUDE.md requires, taken from the runners' own output (`data/d685_month_end_rebalancing.json`,
`data/d686_month_end_variants.json`).
- **The construction:** the lagged 60/40 drift, traded on ES over the last five trading days of each month.
- **Size and cost:** 1 MES, at the house cost of $4.42 a round trip.
- **The score:** daily net Sharpe over every trading day of **2010-07 → 2023-12** (√252). That is wider than the
  ledger's 2016–2023, because D685 scored that window.
- **Correlations** are with the admitted MACD arm's daily net, 2016–2023.

**Closed by the principal, 2026-09-29** ("Ok close no need for 2024+ data"). No unread slice was spent.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| month-end drift, unfiltered, 1 MES | D685 | +0.26 (+0.39); gross +0.32 | Gate 2 failed: net t 1.04, on noise and fade, not cost ($4.42 a round trip against a $93 mean move). Lost money in each of 2019–2022. ρ with the arm −0.035 |
| month-end drift, expected-profit filtered, 1 MES | D685 | +0.24 (+0.36); gross +0.28 | the filter adds nothing; ρ +0.007 |
| O2: stand aside on FOMC/CPI/NFP days, 1 MES | D686 | +0.33 (+0.50) | best of 13 variants, but only at the 75.5th percentile of the best-of-13 null; NW t 1.42; ρ −0.032 |

**Why the line is closed (D687).** The price response per unit of flow collapsed after 2018: −15.8 and −19.7 fell to
−5.9 bp per 0.01 of drift. That happened in both legs (the long bond had responded, ZB t 2.09, in 2010–15), while the
flows grew and the square-root law predicted more impact. The effect was not front-run earlier into the month. The
residual sits at quarter-ends only.

## SCORED, NOT ENTERED — the dealer-gamma close, 2026-09-29 ([D688](decisions/D688-RESULT-not-supported-the-close-sees-a-quarter-of-the-flow.md))

Component lines as CLAUDE.md requires, from the runner's own output (`data/d688_gamma_close.json`).
- **The construction:** SPX GEX plus the ES options book at the prior settlement, and the hedge flow −G·r in
  square-root form; ES traded 15:30 → 16:00 in the sign of the push.
- **Size and cost:** 1 MES at $4.42 a round trip, unless noted.
- **The score:** daily net Sharpe over every session of 2016–2023 (√252).
- **Correlations** are with the admitted MACD arm's daily net, 2016–2023.

**Status: NOT SUPPORTED, awaiting the principal's ruling.** No unread slice was spent.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| gamma push, expected-profit filtered (regime-split π), 1 MES | D688 | +0.10 (+0.15); gross +0.33 (+0.53) | Gate 1 failed (β +0.12, t 1.23, 91st percentile); 30 trades a year, all short-gamma days; net t 0.30; mean $1.91 against a median of −$1.92; 2020-03-13 is 134% of the net; ρ +0.156 |
| gamma push, unfiltered sign(Z), 1 MES | D688 | −1.16 (−1.65); gross +0.20 (+0.31) | $0.66 gross a trade against a $4.42 round trip; lost money in every year; ρ +0.058 |
| gamma push, filtered, 1 full ES ($19.24) | D688 | +0.14 (+0.21); gross +0.30 (+0.46) | 50 a year; net t 0.45; the same single-day dependence; ρ +0.133 |

## SCORED, NOT ENTERED — the opening model, the opening-break line and the MACD arm's reshaping tests, 2026-09-29

**Why this section exists.** Component lines as CLAUDE.md requires, whatever the verdict. These constructions were
scored but never entered here. The principal's ruling (2026-09-29): enter them as recorded, with the departures from
this ledger's standard disclosed. Nothing below is recomputed here; every figure is from the record named. Two sets
come from post-hoc scripts rather than the runners:
- the single-count restatements (`diag_d677_single_count_index.py`);
- D659's correlations (`diag_opening_v2_component_corr.py`, on per-session bp, not dollars).

**Departures from the standard, per row:**
- **Window:** most run 2016-01-04 → 2025-02-28 rather than 2016–2023. D671 and D672 run from 2018-01-09; D682 from
  2018-01 (YM) and 2019-08 (RTY); D679 from about 2017-10.
- **Cost:**
  - **"double":** the D666/D668/D671/D672/D676/D682 stack counts friction twice, filling each stop a tick through and then
    charging the crossing plus another tick (D668-A2). The single-count restatements are per trade only:
    - D668: NQ +2.48 bp (t 2.06), ES −0.03, YM −1.02, RTY −3.60;
    - D672 C1: NQ +7.56 (t 2.62), ES +2.78.
  - D671 and D682 are the same runner stack, but no single-count restatement exists for them.
  - **"once":** D678 and D679 count it once; so do D670 and D673 (`d508_exec`, $3 + crossing, no stop fills).
  - D658 and D659 use OA-A5's line (crossing + $3 + one adverse tick). Whether their fills also carry a tick is
    not stated, so they are unclassified.
- **Size:** micro, except D678 and D679, which are one full contract. That is the minimum size only for HO, RB, BZ and
  PL, since HG, CL, NG, GC and SI have micros.
- **Correlation:** ρ with #2 (the MACD arm) was not rebuilt, except by D670 and D673.
- **No rows** for D669 or D675. D669's component table is the arm itself and free-running variants on spent data.
  D675 is a Stage 1 decomposition, "not a trade", with a gross-only line.
- **Three cells clear C-a on the point estimate:** D672 NQ C1, D659 V2-C and D668 NQ. Each row says why it is not
  entered.

| construction | record | daily $ net Sharpe (Sortino); gross | window · cost · size | why not |
|---|---|---|---|---|
| opening agent-state model v1, H-O2 policy, ES+NQ | D658 | no daily line (the runner wrote no per-session series); policy −0.135 / −0.051 bp a day net at 09:45 / 10:00 | 2016 → 2025-02 · OA-A5 · micro | Gate O1 failed; **CLOSED 2026-09-29, slot 7 released** |
| opening v2, V2-F (fade 09:45 to the prior close) | D659 | +0.22 (0.29); gross +0.64; hit 57 %; 842 trades | 2016-04 → 2025-02 · OA-A5 · micro | 2022-carried; policy −0.22 bp a session at 2× cost; vault power 6.5 %; **CLOSED 2026-09-29** without its vault look; \|ρ\| K1–K6 ≤ 0.06 (bp series) |
| opening v2, V2-C (hold from 10:30 to the close) | D659 | **+0.62 (0.94)**; gross +0.87; hit 55 %; 1,259 trades | 2016-04 → 2025-02 · OA-A5 · micro | clears C-a on the point estimate, but "the component is the always-on hold, not v2's model" (diff +0.06, t 0.05); vault power 5.0 %; **CLOSED**; \|ρ\| K1–K6 ≤ 0.101 (bp series) |
| re-break of yesterday's range, ES / NQ, E1–E4 | D666 | no daily line (correlations omitted, every cell net-negative); per-trade Sharpe net −1.15 to −0.23 | 2016 → 2025-02 · **double** · micro | NOT SUPPORTED at Gate 1; worse than the plain break in every cell |
| plain break, E4 unfiltered: ES / NQ / YM / RTY | D668 | −0.64 / **+0.60** / −0.68 / −1.32; gross +0.46 / +1.11 / +0.43 / −0.06 | 2016 → 2025-02 (RTY 2017-07) · **double** · micro | YM/RTY NOT SUPPORTED; ES/NQ development; NQ clears C-a on the point estimate but is in-sample, double-counted, and **CLOSED as a separate vault line** (its subset D680 is frozen); ρ K8 −0.05 / −0.11 / −0.04 / −0.05 |
| size-forecast break B3: NQ / ES | D671 | −0.03 (−0.05) / −0.05 (−0.09); gross +0.35 / +0.57 | 2018-01 → 2025-02 · **double** · micro | development; on NQ worse than the plain break (placebo rank 0.003); on ES only the short-side veto helps; ρ K8 −0.08 / +0.05 |
| compression break C1: NQ / ES | D672 | **+0.97 (2.14)** / +0.14 (0.25); gross +1.21 / +0.66; $1,025 / $83 a year | 2018-01 → 2025-02 · **double** · micro | development, "close to circular" on NQ; **frozen for the joint vault as D680 (slot 9)**, whose PASS is the confirmation; not entered before it; ρ K8 −0.05 / −0.02 |
| compression break C1: YM / RTY | D682 | −0.45 (−0.76) / −1.33 (−1.98); gross +0.11 / −0.65 | YM 2018-01, RTY 2019-08 → 2025-02 · **double** · micro | NOT SUPPORTED (RTY's compressed third is its worst); ρ K8 +0.04 / −0.07 |
| root-aware break: CL / NG / GC / SI | D676 | −1.12 (−1.90) / −1.22 (−1.75) / −1.19 (−1.92) / −1.41 (−2.26); gross −0.05 / −0.24 / +0.13 / −0.29 | 2016 → 2025-02 · **double** · micro (MCL $6.03, MNG $5.00, MGC $6.93, SIL $13.00) | NOT SUPPORTED on all four; ρ K8 ≤ 0.05 |
| overnight gap at the open: HO / RB / BZ / HG / PL | D678 | −0.44 (−0.72) / −0.21 (−0.38) / −0.60 (−1.01) / −1.14 (−1.83) / −0.69 (−1.15); gross +0.23 / +0.15 / −0.02 / −0.37 / +0.67 | 2016 → 2025-02 · once · **full** ($57 / $37 / $35 / $34 / $50) | NO MECHANISM: a random side earns the same on the same days; ρ K8 ≤ 0.05 |
| compression tier C1, nine roots: HO / RB / BZ / HG / PL / CL / NG / GC / SI | D679 | +0.21 / +0.05 / +0.03 / −0.92 / −1.18 / −0.01 / +0.15 / −0.16 / −0.87; gross +0.73 / +0.44 / +0.51 / −0.28 / +0.18 / +0.22 / +0.40 / +0.42 / +0.42 | 2017-10 → 2025-02 · once · **full** | NO MECHANISM by the declared bar; net at most +0.21; \|ρ\| K8 ≤ 0.04 |
| 10:00 direction held to the close: YM / RTY / ES / NQ | D670 | −1.64 (−2.08) / −0.76 (−1.00) / −0.73 (−0.95) / −0.11 (−0.16); gross −1.07 / −0.13 / −0.24 / +0.16 | 2016 (RTY 2017-07) → 2025-02 · `d508_exec` · micro | fails on every root; **ρ with the arm 0.19 / 0.24 / 0.35 / 0.37**; line CLOSED (R15) |
| join the formed move: YM / RTY / ES / NQ | D673 | −1.07 (−1.39) / −0.82 (−1.04) / −0.60 (−0.78) / +0.04 (+0.06); gross −0.43 / −0.08 / −0.05 / +0.36 | 2016 (RTY 2017-07) → 2025-02 · `d508_exec` · micro | NOT SUPPORTED; **ρ with the arm 0.21 / 0.17 / 0.26 / 0.35**; line CLOSED (R15) |

## SCORED, NOT ENTERED — short-gamma continuation on ES, 2026-09-29 ([D689](decisions/D689-STAGE-0-short-gamma-continuation-is-real-but-unconfirmable.md))

Component lines from the runner's own output (`data/d689_short_gamma_continuation.json`).
- **The construction:** on days with G_SUM < 0, follow the last hour for the next hour, at 10:30–14:30.
- **The score:** daily net Sharpe over every session of 2016–2023 (√252).
- **Correlations** are with the admitted MACD arm's daily net.

**Status: in-sample development (a stage 0), UNCONFIRMABLE ON THE CLEAN SLICE.** Not a candidate until a
pre-registered test on unseen data.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| short-gamma 60-min continuation, unfiltered, 1 full ES ($19.24) | D689 | +0.51 (+0.75); gross +1.04 (+1.59) | in-sample only; 379 trades a year, mean ≈ median +$18; 2022–23 are 81% of the net; about half is up-drift on short-gamma days; max drawdown $15.4k per contract; ρ −0.046 |
| the same, 1 MES ($4.42) | D689 | −0.18 (−0.25); gross +1.04 (+1.59) | $3.77 gross against a $4.42 round trip; ρ −0.048 |
| the same, expected-profit filtered (π·\|m\|), full ES | D689 | −0.39 (−0.49) | the \|m\|-scaled projection selects moves that do not continue; 10 a year |

## SCORED, NOT ENTERED — the break on "coiled" days, ES and NQ, 2026-09-29 ([D694](decisions/D694-STAGE-1-RESULT-not-supported-iv-adds-nothing-to-the-break.md))

Component lines come from the runner's own output (`data/stage1_d694_coiled_break.json`).
- **The construction:** D668's E4 plain break on D672's C1 days whose walk-forward IV/RV20 percentile is ≥ 1/2.
- **Size and cost:** one micro, at the level, friction once.
- **The score:** daily net Sharpe over every session of 2018-01-09 → 2025-02-28 (√252).
- **Correlations** are with the admitted MACD arm's daily net, truncated below 2025-03-01.

**Status: NOT SUPPORTED on both roots** (the IV ingredient fails its null). The line is closed.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| COILED, ES, 1 MES ($4.42) | D694 | +0.69 (+1.54); gross +0.94 (+2.33) | its lift over the quiet C1 trades is matched by a count-matched label with IV's own information scrambled (rank 0.765); 120 trades in 7 years; top 5 trades are 53% of gross; ρ +0.02 |
| COILED, NQ, 1 MNQ ($4.07) | D694 | +0.55 (+1.19); gross +0.70 (+1.59) | earns less than the quiet C1 trades (−3.1 bp); rank 0.298; a subset of D680's C1 (ρ +0.46) that is worse than C1 itself (1.03); ρ +0.04 |
| COILED, expected-profit filtered, ES / NQ | D694 | +0.20 (+0.38) / +0.54 (+1.15) | Gate 2 fails: 36 / 87 trades, net t 0.74 / 1.30 |

## SCORED, NOT ENTERED — the gamma-gated 15-minute log MACD long on ES, 2026-09-30 ([D699](decisions/D699-STAGE-0-RESULT-hist-clears-the-timing-null-not-the-drift.md))

Component lines come from the runner's own output (`data/d699_gamma_macd_long.json`).
- **The construction:** on days with G_SUM < 0, a 12/26/9 log MACD on 15-minute bars of the gap-spliced day session,
  normalised to unit sd under a random walk; long with hysteresis; flat at 16:00.
- **The score:** daily net Sharpe over every session of 2016–2023 (√252).
- **Correlations** are with the admitted MACD arm's daily net.

**Status: in-sample development (a stage 0).** V1 fails the declared reading on one gate of three (its lead over the
time-matched drift is NW t 1.64, not 2). UNCONFIRMABLE on 2024-01 → 2025-02 (expected t about 0.6). Not a candidate.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| V1 HIST (z_H band ±0.5), 1 MES ($4.42) | D699 | +0.63 (+1.06); gross +0.90 (+1.56) | 72 trades a year, hit 50.5%, skew +1.09, median +$0.58 against a mean +$10.47; 2022 is 75% of the net; beats the drift at t 1.64 only; timing null 98.5th, gamma-label null 99.6th; ρ +0.154 |
| V2 ROC (z_R band ±1.0), 1 MES | D699 | +0.19 (+0.28); gross +0.57 (+0.89) | inside its timing null (83rd; 40th in the family); +$0.35 a trade without Feb–Apr 2020; ρ +0.056 |
| V3 OR, 1 MES | D699 | +0.27 (+0.41); gross +0.59 (+0.91) | inside its timing null (82nd; 62nd in the family); median −$15.67; ρ +0.106 |

## SCORED, NOT ENTERED — the hourly continuation on ES-book short-gamma days, 2026-09-30 ([D708](decisions/D708-STAGE-0-RESULT-the-side-choice-is-the-signal-not-the-drift.md))

Component lines come from the runner's own output (`data/d708_short_gamma_timing.json`).
- **The construction:** on days with G_ES < 0 (the ES options book short gamma at the prior settlement), at 10:30,
  11:30, 12:30, 13:30 and 14:30, hold the sign of the last 60 minutes' move for 60 minutes. D689's primary grid.
- **The score:** daily net Sharpe over every session of 2016–2023 (√252).
- **Correlations** are with the admitted MACD arm's daily net.

**Status: in-sample development (a stage 0).**
- **The signal:** SIGNAL on the timing term: +$3.09 a MES trade over the drift, t 3.17, both legs positive.
- **As a component:** not a candidate at MES in-sample. A joint-vault pre-registration awaits the principal.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| E, 1 MES ($4.42) | D708 | −0.45 (−0.62); gross +1.14 (+1.73) | 537 trades a year, hit 48.0%, skew −0.03; gross +$3.16 a trade against a $4.42 round trip. The fee is 1.32–3.37 × the gross in 2016–2022 (33× in 2017) and 0.69× in 2023. Net is positive only in 2023. ρ −0.042 |
| E, 1 full ES ($19.24) | D708 | +0.45 (+0.65); gross +1.14 (+1.73) | max drawdown $18,972, annual vol $14,830 a contract (the prop account's size problem). 2023 is 54% of the net, and the top 10 trades 67%. ρ −0.039 |

## ENTRY #4, PROVISIONAL, 2026-09-30 — F2, the ES last-hour continuation on a relative-size filter ([D705](decisions/D705-RESULT-none-passes-f2-fails-only-on-2022-concentration.md), [D707](decisions/D707-PRE-REG-f2-last-hour-filter-for-the-joint-vault.md))

*The principal: "The F2 construction is now a candidate, add it to the big vault run."*

The component line comes from the runner's own output (`data/vault_d707_power.json`, which reproduces D705's F2
exactly: 252 trades, +$13.208968 net).
- **The construction:**
  - at 15:30, trade the sign of the 14:30 → 15:30 ES move, held to 16:00, one MES, $4.42 a round trip;
  - only when tiers((tiers(|F5| / σ_F5) + tiers(today's 5-minute realised volatility to 15:30)) / 2) ≥ 0.8;
  - D707 §1 is the full specification.
- **The score:** daily net Sharpe over every candidate session of 2018-05-14 → 2023-12-29 (√252).

| # | component | window | net Sharpe (SE); Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **4** | **F2** (D707 §1), ES 15:30 → 16:00, 1 MES, $4.42, about 45 trades a year | 2018-05 → 2023-12 (the walk-forward burn-in) | **+0.80 (0.36)**; Sortino +1.37; per trade +$13.21 net / +$17.63 gross (HAC t 2.48); max drawdown $707 | 53.6 % | +0.81 (per trade) | +0.02 with #2 (the MACD arm) | **PROVISIONAL, on the principal's ruling.** D705's development verdict was FAIL on its one-year gate (2022 = 59.9 % of the net, bar 50 %); +$7.17 a trade without 2022, +$7.06 after 2022-05-16. Promotion or removal by D707's one look at 2024-01-01 → 2026-09-18 in the joint run (programme slot 7) |

**How it meets the standard:**
- **C-a:** +0.80 > 0.5 on the point estimate, SE 0.36 (a monthly block bootstrap). **C-b:** ρ +0.02 with #2.
- **C-c:** positive skew. **C-d:** daily σ about $40 at one MES. **C-e:** D705 and D707.
- **It sits above its family null:** D705's best-of-three count-matched rotation had p95 +$7.94 a trade, and F2's rank
  was 0.996.

**Disclosures:**
- **The window** is 2018-05 onward, not the standard's 2016-01, because the composite tier needs two 250-value
  burn-ins.
- **Selection:** three steps chose F2 on this window (D702's hindsight profile, D703's failure, D705's best of three),
  and only the last is priced by a null. The in-sample figure is an upper estimate.
- **The unseen span includes this ledger's own confirmation slice** (2024-01 onward). It is unread for this
  trade, and D707 reads it once, in the joint run, together with the vault.

**Entry #4, a note of 2026-09-30 ([D711](decisions/D711-RESULT-placebo-unresolved-nq-transfers.md)):**
- **D705's null was anti-conservative.** It compared mean net under an input rotation, and F2 picks bigger days than
  a rotated selection does (D711-A1: 17 % false passes on synthetic worlds with no direction).
- **Under the correctly sized statistic** (direction efficiency Σg / Σ|g|), F2 still ranks **0.991** (p95 0.235
  against its 0.279). The row stands.
- **D711's A1 read UNRESOLVED:** 13:30 → 14:00 carries almost F2's information per trade, and 11:30, 12:30 and 14:30
  carry none. So the flow-into-the-close mechanism is neither confirmed nor refuted.

## SCORED, NOT ENTERED — F2 unchanged on NQ, YM and RTY, 2026-09-30 ([D711](decisions/D711-RESULT-placebo-unresolved-nq-transfers.md))

Component lines come from the runner's own output (`data/stage1_d711_f2_mechanism.json`).
- **The construction:** D707 §1 at 15:30, one micro, each root's single cost line.
- **The score:** daily net Sharpe over the candidate sessions of each root's window (√252).

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| F2 on NQ, 1 MNQ ($4.07), 2018-04 → 2023-12 | D711 | +0.92 (+1.56); +$24.74 gross / +$20.67 net a trade, t 3.53, efficiency rank 0.984 | **ρ 0.87 with entry #4**: the same trade on a bigger-moving contract, so it fails C-b. 2022 is 67 % of the net. At most a sizing choice beside #4, on the principal's word |
| F2 on YM, 1 MYM ($3.80) | D711 | +0.54 (+0.85); +$9.94 / +$6.15 | fails its efficiency rotation (rank 0.936); ρ 0.86 with #4 |
| F2 on RTY, 1 M2K ($3.76), 2019-11 → 2023-12 | D711 | +0.07 (+0.11); +$4.39 / +$0.64 | no edge (t 1.53, Holm 0.063; rank 0.839) |
| NQ F2 only when ES F2 agrees (same day, same side), 1 MNQ, 2018-05 → 2023-12 | [D714](decisions/D714-RESULT-no-increment-es-agreement-is-inside-chance.md) | +0.98 (+1.71); +$29.65 / +$25.58, 216 trades | NO INCREMENT: random deletion of 55 NQ trades matches it (efficiency rank 0.856); ρ 0.96 with entry #4; found by looking |

## SCORED, NOT ENTERED — silver into its settlement window, 2026-09-30 ([D709](decisions/D709-STAGE-0-RESULT-silver-moves-into-settlement-not-the-funds.md))

Component line from the runner's own output (`data/d709_silver_settlement_flow.json`).
- **The construction:** on SI, from 12:55 ET, hold the sign of the move since the prior settlement to the 13:24 close,
  one SIL at $8. Post-era, 2019-01-07 → 2023-12-29.
- **Status:** FAIL (not the funds). Not a candidate.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| SI 12:55 → 13:24, 1 SIL ($8) | D709 | −0.58 (−0.92), SE 0.52; gross +1.39 (+2.47) | gross +$5.63 a trade (t 3.14) below the $8 round trip. The pre-era carried it too (t 4.03), so the funds are not shown as its cause. It fades: 2022 +$0.87, 2023 −$3.87. Hit 45.9%, daily skew +2.28; ρ +0.05 with #2, +0.03 with #4 |

## SCORED, NOT ENTERED — the Treasury auction-day V, ZT/ZF/ZN/UB, 2026-09-30 ([D710](decisions/D710-STAGE-0-RESULT-the-auction-v-is-in-the-futures-mechanism-only.md))

Component lines from the runner's own output (`data/stage0_d710_auction_v.json`), 2016-01-04 → 2023-12-29, full
contracts at the d556 round trip.
- **The construction:** on 13:00 coupon-auction days, short the mapped future from 10:01 to 12:59, and long it from
  13:06 to 16:00 (the 30-year pre-leg only). U takes every leg. F takes a leg only when the paper-sized projection is at
  least 2 × its round trip.
- **Status:** the premise is PRESENT (t 4.98). The trade is MECHANISM ONLY. Not a candidate.
- **All ten programme slots are allocated,** so a vault line would need an α re-allocation.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| Book U, every leg | D710 | +0.04 (+0.06), SE 0.34; gross +0.77 | gross +$17.48 a leg (t 2.89) against $14–37 round trips; net −$1.18. ρ +0.07 with #2, +0.01 with #4 |
| Book F, paper-sized filter | D710 | +0.48 (+0.76), SE 0.35; gross +0.64 | about 12 trades a year; net +$43.85 a trade at t 1.45 (the gate is 2), median +$9.63; the top 10 trades are 117% of the net; mostly the 30-year pre-auction short. ρ +0.08 with #2, +0.02 with #4: a diversifier on the point estimate, not established |

## ENTRY #4 PARKED and ENTRY #5, PROVISIONAL, 2026-09-30 — NQ F2 replaces ES F2 in the joint vault run ([D716](decisions/D716-PRE-REG-nq-f2-for-the-joint-vault.md))

*The principal: "Remove ES F2 from the vault run and keep NQ F2 and NQ F2 only when ES F2 agrees".*

**Entry #4 (ES F2) is PARKED.**
- Its promotion path (D707's vault look) is withdrawn before any look.
- The row stands as scored. After D716's run it has no unread sample left: ES's last-hour data is read there as
  an input.

**Entry #5 is NQ F2,** from `data/vault_d716_power.json` (D711's book reproduced).

| # | component | window | net Sharpe (SE); Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **5** | **NQ F2** (D716 §1): NQ 15:30 → 16:00, 1 MNQ, $4.07, about 48 trades a year | 2018-04 → 2023-12 | **+0.92**; Sortino +1.56; per trade +$20.67 net / +$24.74 gross (HAC t 2.95); max drawdown $990 | 55.5 % | +0.57 (per trade) | +0.02 with #2; **0.87 with #4** (the same signal, and #4 is parked) | **PROVISIONAL, on the principal's ruling.** The joint run's D716 look (slot 7) promotes or removes it. If the agreement book takes over in the fixed sequence, the entry becomes that book |

**Disclosures:**
- The rule came from ES's in-sample search.
- NQ was chosen over ES after both were seen, so the in-sample figures are upper estimates.
- 2022 holds 67 % of the net.

## SCORED, NOT ENTERED — the absorbed morning move (proposal B), ES, 2026-09-30 ([D715](decisions/D715-STAGE-0-RESULT-absorption-ranks-backwards.md))

Component lines from the runner's own output (`data/stage0_d715_absorbed_morning.json`), one MES at $4.42, 2018-02 →
2023-12.
- **The construction:** from the 10:30 open to the 15:59 close, trade in the first hour's direction when its aggressor
  flow was below what its size predicts (absorbed) and at least two of NQ, RTY and YM agree.
- **Status:** NEITHER. The absorption gradient is inverted (Spearman −0.061, 0.7th percentile). Not a candidate.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| B, absorbed + breadth | D715 | −0.66 (−0.87); −0.41 | −$11.64 a trade net (t −1.77); 626 trades; the mechanism runs the other way. ρ +0.19 with #2, −0.09 with F2 |

## SCORED, NOT ENTERED — the reversed flow rule, NQ (primary) and ES, 2026-09-30 ([D717](decisions/D717-STAGE-0-RESULT-the-reversal-does-not-transfer-to-nq.md))

Component lines from the runner's own output (`data/stage0_d717_reversed_flow.json`), 2018-02 → 2023-12.
- **The construction:** from the 10:30 open to the 15:59 close, follow a first-hour move whose aggressor flow exceeded
  what its size predicts, and fade one whose flow fell short.
- **Status:** NEITHER on NQ (the flow residual ranks nothing). ES is D715's selection restated. Not a candidate.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| reversed, NQ, 1 MNQ ($4.07) | D717 | −0.32 (−0.44) | −$5.37 a trade net (t −0.92), 1,444 trades; G1 ρ −0.007 (37th percentile); positive in 1 of 6 years. ρ −0.10 with #2, +0.09 with NQ F2 |
| reversed, ES, 1 MES ($4.42) | D717 | +0.41 (+0.59) | selected by D715 (not evidence); +$4.31 net (t 1.10); 2022 is 74% of the net |

## SCORED, NOT ENTERED — F2 at the commodity settlement windows, 2026-09-30 ([D719](decisions/D719-RESULT-none-transfers-ho-signal-at-unviable-size.md))

Component lines come from the runner's own output (`data/stage1_d719_commodity_settlement_f2.json`).
- **The construction:** D707's F2 held for the final 30 minutes into each root's settlement window.
- **Size:** the biggest viable for a $50k prop account, set from the burn-in.
- **The score:** daily net Sharpe on the root's candidate sessions, 2018 → 2023.

**Family: NONE.**

| construction | record | net Sharpe (Sortino); per contract | why not |
|---|---|---|---|
| **HO, 1 full ($10.20)** | D719 | **+0.92 (+1.72)**; +$119.41 gross / +$109.21 net, t 2.74, efficiency rank 0.991 | **NOT VIABLE on size:** a q99 hold loss of $1,117 > $1,000 and no micro; one contract draws down $4,304 with 9 days below −$1,000. 2022 is about two-thirds of the net. At the quoted 12-tick crossing the net is about +$62. ρ −0.02 with NQ F2 |
| RB, 1 full ($10.20) | D719 | +0.54 (+0.84); +$76.69 / +$66.49, t 1.85 | fails Holm (0.35); NOT VIABLE on size |
| CL, 1 full ($21.46) | D719 | +0.27 (+0.43); +$49.79 / +$28.33, t 1.35 | fails Holm and the rotation (0.910) |
| SI, 1 full ($31.00) | D719 | +0.20 (+0.37); +$45.60 / +$14.60, t 1.78 | fails Holm; negative after 2022-05-16; D709's window |
| NG, HG, GC, ZC, ZS, ZW, ZL, ZM | D719 | −0.90 to −0.38 | no gross edge (t −1.15 to +0.54) |

**HO and RB CLOSED by the principal, 2026-09-30** ("Ok close, Heating Oil")
([D719 closure](decisions/D719-RESULT-none-transfers-ho-signal-at-unviable-size.md#closed-by-the-principal-2026-09-30-heating-oil)).
- A correction to the HO row: a micro exists (MHO, 4,200 gallons).
- It does not trade: zero volume on 32 of 32 sessions (2026-08-14 → 09-29), with 2 contracts open.
- The NOT VIABLE reading stands. Neither line is entered.

## SCORED, NOT ENTERED — the MACD arm and NQ F2 sized by the day-size forecast, 2026-09-30 ([D720](decisions/D720-STAGE-0-RESULT-forecast-big-days-are-where-direction-fails.md))

Component lines come from the runner's own output (`data/stage0_d720_size.json`), 2018-02 → 2023-12.
- **The construction:** each line's own trades, at 2 MNQ when D691's walk-forward forecast of the day's range is in
  its top third (R1), otherwise 1.
- **Status:** a sizing overlay on existing components, not a new one. It lowers both. Not a candidate.

| construction | record | net Sharpe (Sortino); gross | why not |
|---|---|---|---|
| the MACD arm, R1 | D720 | +0.70 (+1.02); +0.94 | −0.13 against the unsized arm (rotation rank 0.24); P3a at $50k 1.93 a year; the forecast's big days carry the arm's weakest efficiency (0.077 against 0.150) |
| NQ F2, R1 | D720 | +0.48 (+0.70); +0.68 | −0.31 against unsized F2 (rotation rank 0.016); F2 nets −$0.61 a trade on the forecast's big days |
| the unsized arm + NQ F2, one MNQ each (reported) | D720 | +1.01 (+1.54) | not a new component: the sum of two existing lines, in-sample, with ρ −0.01 between them |

## SCORED, NOT ENTERED — F2 on forecast-quiet days, four index roots, 2026-09-30 ([D721](decisions/D721-DIAG-RESULT-the-quiet-day-pattern-is-nq-only.md))

Component lines come from the runner's own output (`data/diag_d721_quiet_day_f2.json`), 2018-01 → 2023-12.
- **The construction:** F2 taken only when D671's size-forecast tier τ is below 1/3.
- **Status:** CLOSED on the principal's word. The pattern is significant on NQ only.

| construction | record | net Sharpe (Sortino); net $ a year | why not |
|---|---|---|---|
| NQ, 1 MNQ | D721 | +1.09 (+1.87); $380 | the root the pattern was found on (G1 rank 0.011); 59 trades |
| ES, 1 MES | D721 | +0.98 (+2.16); $168 | G1 rank 0.11, NOT SIMILAR; 48 trades; 3 of 6 years positive |
| YM, 1 MYM | D721 | +0.94 (+2.36); $142 | G1 rank 0.27, NOT SIMILAR; 59 trades |
| RTY, 1 M2K | D721 | +0.15 (+0.20); $22 | G1 rank 0.13; F2 itself barely pays on RTY |

## NOTE — the 2022 dependence of the lines, 2026-10-01 ([D722](decisions/D722-DIAG-RESULT-no-variable-explains-2022.md))

No construction is scored or entered here. This is a reading note on entries #5 (NQ F2, PROVISIONAL) and the scored
lines D699, D707/D705 and D719.
- **No pre-trade variable explains 2022 on any line** (all UNEXPLAINED).
- **The ex-2022 figures** (net a trade; net Sharpe and Sortino):

  | line | ex-2022 |
  |---|---|
  | NQ F2 | +$9.01; 0.50 (0.79) |
  | ES F2 | +$7.17; 0.54 (0.88) |
  | D699 V1 | +$3.55; 0.25 (0.39) |
  | HO F2 (closed) | +$50.08; 0.78 (1.21) |

- **ρ is honest day to day, but not over years.** The daily correlations in this ledger are body statistics that hold
  up in 2022 (F2–D699 0.15, lower than elsewhere). But the equal-weight ES F2 + NQ F2 + D699 book earns **77 % of its
  net in 2022**, so assembling these components does not diversify the year.

**D699 CLOSED by the principal, 2026-10-01** ("Close D699";
[closure](decisions/D699-STAGE-0-RESULT-hist-clears-the-timing-null-not-the-drift.md#closed-by-the-principal-2026-10-01)).
V1 is positive in volatility units only in 2022 (D722). Not entered.

## SCORED — the assembled ES/NQ micro book, 2026-10-01 ([D732](decisions/D732-STAGE-0-RESULT-go-but-the-book-is-two-years-and-compression.md))

**Not an admission.** Only the assembled book goes to BOOK_PROP, and only after a pre-registered test on unseen data.
This is the in-sample premise check.

| book | window | net Sharpe (Sortino) | max DD | largest year ($ / vol) | without 2022 | without 2020 and 2022 (post hoc) |
|---|---|---|---:|---|---:|---:|
| #2 the arm + #5 NQ F2 + D680 C1, one MNQ each | 2018-05 → 2023-12 | **1.22 (1.97)** | $4,920 | 2022 45 % / 2020 49 % | 0.95 | **0.34** |

- **Pairwise ρ** is below 0.25 in every year.
- **Outside 2020 and 2022,** the compression break carries the book: C1 0.98, NQ F2 0.33, the arm 0.01.
- **ES offers no eligible micro component;** ES F2 is NQ F2's trade (ρ 0.87).

## ENTRY #2 RETIRED — the MACD arm, 2026-10-01, on the principal's word

> *"That MACD arm is useless ... using capital to trade when you don't make money, even if you don't lose money is
> shit."* — the principal ([BOOK_PROP](BOOK_PROP.md#the-macd-arm-retired-by-the-principal-2026-10-01--the-prop-book-is-empty-again))

**Entry #2 is retired.** It is not a component of any assembled book.

**The reason, D732's numbers:**
- in the market on 83 % of sessions;
- net Sharpe 0.01 without 2020 and 2022;
- 99 % of its volatility-unit net in 2020;
- it brings the in-sample book's drawdown from $1,360 to $4,920.

**The ledger's live entries:**
- **#5 NQ F2:** PROVISIONAL, programme slot 7.
- **#6 NQ leads the Dow:** PROVISIONAL, programme slot 1 (below).
- **The NQ compression break (D680):** frozen for the joint run in slot 9. It is not a ledger entry; it is scored as a
  component line in D732.

## ENTRY #6, PROVISIONAL, 2026-10-01 — NQ leads the Dow ([D735](decisions/D735-STAGE-0-RESULT-nq-breaking-from-the-market-beats-its-null.md), [D737](decisions/D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md))

*The principal: "I choose YM 1.0, it look really good"; "Yes write it into slot 110 and freeze".*

| # | component | window | net Sharpe; Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **6** | **NQ leads the Dow** (D735's YM k1.0 1σ_rem): at the first minute 10:00–14:30 where NQ's move since the open minus YM's (own-σ units) reaches \|z\| 1.0, one MNQ in the spread's direction, held to the close under a 1σ_rem stop; $4.07; about 210 trades a year | 2016-01 → 2023-12 | **+1.11**; Sortino +1.85; gross Sharpe +1.41 (Sortino +2.40); per trade +$14.87 net / +$18.94 gross (NW t 3.15); max drawdown $2,690 | 50 % | +0.94 (per trade) | **+0.05 with #5** (NQ F2) | **PROVISIONAL.** The joint run's D737 look (slot 1) confirms or removes it |

**Disclosures:**
- **This cell was chosen after the fact from D735's 20.** D735's declared reading was DRIFT ONLY: every cell failed the per-\|x\| bin leg.
- Largest year: 51 % in dollars, 35 % in volatility units. Without 2022 it nets +$8.52 a trade.
- About 96 % of entries fall in the 10:00 hour.
- The drawdown exceeds a $50k account's $2,000 trailing barrier at one MNQ.

## ENTRY #7, PROVISIONAL, 2026-10-02 — the CPI/jobs-report fade on MNQ ([D775](decisions/D775-STAGE-0-RESULT-the-cpi-and-jobs-report-fade-passes-in-sample.md), [D776](decisions/D776-PRE-REG-the-cpi-and-jobs-report-fade-for-the-joint-vault.md))

*The principal: "Pre-reg the CPI/NFP fade as D775"; "Put D775 in the next slot and freeze it".*

| # | component | window | net Sharpe; Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **7** | **The CPI/jobs-report fade** (D775): on each 08:30 CPI and Employment Situation release, one MNQ against the 08:29 → 08:34 bar-close impulse, entered at the 08:34 close and held to the 11:00 close; \$4.07; about 24 trades a year | 2016-01 → 2023-12 | **+0.84**; Sortino +1.50; gross Sharpe +0.95; per trade +\$30.81 net / +\$34.88 gross (t 2.73; net t 2.41); max drawdown \$1,036 | 55.9 % | +0.48 (per trade) | **−0.042 with #5** (NQ F2), **−0.010 with #6** (D737's twin), −0.016 with C1 | **PROVISIONAL.** The joint run's D776 look (slot 2) confirms or removes it |

**Disclosures:**
- **The in-sample was read before D775 was registered** (D772's lead hunt found it in a search). D775 fixed the
  construction and passed its exact rotation null (rank 0.9995) and the principal's year test, the latter only on the
  win-rate branch at its boundary.
- **Largest year:** 2023, 48 % of the net in dollars. 2016–19 is +0.09σ against +0.33σ in 2020–23, volatility-adjusted.
  The five worst trades are all 2022.
- **It lives in large and downward impulses,** and after the 09:30 cash open (+\$29.55 of the +\$34.88).
- **Vault power at 64 release days:** 0.57 at the in-sample edge, 0.77 at 2020–23's, 0.16 at 2016–19's.

**The ledger's live entries now:**
- #5 NQ F2 (slot 7);
- #6 NQ leads the Dow (slot 1);
- #7 the CPI/jobs-report fade (slot 2).
- The NQ compression break (D680, slot 9) is scored as a component line, not an entry.

## ENTRY #8, PROVISIONAL, 2026-10-03 — base L4, the M2K closing-auction fade ([D778](decisions/D778-STAGE-0-RESULT-the-trend-filter-removes-the-best-trades.md), [D781](decisions/D781-PRE-REG-the-m2k-closing-auction-fade-for-the-joint-vault.md))

*The principal: "Pre-reg L4's freeze for slot 10"; "build it"; "Freeze it".*

| # | component | window | net Sharpe; Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **8** | **Base L4** (D772's Lead 4, D778's base book): when M2K's 15:50 → 16:00 move is in its trailing top fifth, one M2K against it, entered at the next 18:05 reopen and held to 10:00; \$3.76; about 47 trades a year | 2018-01 → 2023-12 | **+0.81**; Sortino +1.25; gross Sharpe +1.05; per trade +\$12.08 net / +\$15.84 gross (t 2.47; net t 1.88); max drawdown \$1,167 | 55.7 % | +0.04 (per trade) | **+0.032 with #7** (D775), **+0.006 with #5** (NQ F2), **+0.002 with #6** (D737's twin), +0.054 with C1 | **PROVISIONAL.** The joint run's D781 look (slot 10) confirms or removes it |

**Disclosures:**
- **The in-sample was read before the line was registered** (D772's lead hunt found it in a search, and D777–D780
  read it again). It fails the G2 bar D775 cleared: net t 1.88, and −\$15 in total without 2020–21.
- **2022 lost** (−\$13.06 net a trade). Neither a trend filter (D778) nor a rates filter (D779) separates it; the
  closing move gave back 2.5% of its size by 10:00 that year, against 52–72% in every other period.
- **The edge is in buying closing-auction falls** (+\$19 to +\$41 net a trade in every period but 2022). Fading rises
  earns about nothing.
- **The ρ above is the base book's**, computed for this entry (in-sample, scratch, read-only). D781's record quotes
  "−0.06 to +0.03" from D778's filtered book. That record is hashed in the freeze and is not edited.
- **Vault power at about 133 trades** (`data/vault_d781_power.json`): 0.52 at the in-sample edge, 0.27 at 2018–19's,
  0.04 at zero. The three latest in-sample 133-trade windows, all holding 2022, were UNRESOLVED.

**The ledger's live entries now:**
- #5 NQ F2 (slot 7);
- #6 NQ leads the Dow (slot 1);
- #7 the CPI/jobs-report fade (slot 2);
- #8 base L4 (slot 10).
- The NQ compression break (D680, slot 9) is scored as a component line, not an entry.

## DECLARED — the assembled prop book for the joint run, 2026-10-04 ([D792](decisions/D792-PRE-REG-the-assembled-prop-book-for-the-joint-vault.md))

*The principal: "Pre-reg the assembled book"; "Build it"; "Freeze it".*

**Not an admission.** The assembly rule is fixed before any member's vault is read.

**The members:** the five live components above (#5, #6, #7, #8 and C1), one micro each. **Only the members that PASS
their own vault lines enter.**

**The window:** 2024-01-01 → 2026-09-18, with C1 counted from 2025-03-01.

**The gates:** at least two members PASS; the book's net is > 0; its net is > 0 in each half; and hurdle P holds.

**The confirmation:** a forward read of the same members on 2026-09-21 → 2027-09-30.

**The in-sample rehearsal** (all five, 2018-05 → 2023; machinery, not evidence):

| book | net Sharpe (Sortino) | gross Sharpe (Sortino) | net | max DD | largest year | share of net |
|---|---|---|---:|---:|---|---|
| F2 + D737 + D776 + C1 + L4, one micro each | **2.03 (3.75)** | 2.42 (4.60) | \$45,757 | \$2,817 | 2022, 41 % | D737 57 %, D776 13 %, F2 12 %, C1 11 %, L4 7 % |

- **The account dies 4 times:** the max drawdown passes the \$2,000 trailing barrier, and P1's multiplier is 0.71.
- **Hurdle P passes anyway:** no 2 % days, and \$4,689 expected profit before a breach against a \$209 fee.
- **Daily ρ** between members is −0.04 to +0.06.
- **D734's NQ pair** stays frozen and is read beside. When both books read ADMITTED, D792's is the candidate.

## ENTRY #9, PROVISIONAL, 2026-10-04 — D791's gold China-open model, programme slot 11 by amendment ([D791](decisions/D791-EXPLORE-RESULT-a-walk-forward-model-picks-the-winners.md), [D793](decisions/D793-PRE-REG-gold-china-open-model-for-the-joint-vault.md))

*The principal: "Add it to the vault"; "Put it in slot 11".*

| # | component | window | net Sharpe; Sortino; gross | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|
| **9** | **D791's model** on D765's MGC China-open fade: the 36-feature no-calendar ridge (α 100) scores each session from information known by 09:30 Beijing; take the top third and fade the open passively (D770's rule, \$3.03); about 80 trades a year | 2018-01 → 2023-12 (walk-forward: each year scored by a model fitted on the years before) | **+0.82**; Sortino +1.28; gross Sharpe +1.34; per trade +\$4.80 net / +\$7.83 gross (net t 2.00); max drawdown \$787 | 53.4 % | +0.32 (per trade) | **+0.016 with #7** (D775), +0.027 with D777's MNQ book; with #5, #6 and #8 not computed | **PROVISIONAL.** The joint run's D793 look (slot 11) confirms or removes it |

**Disclosures:**
- **Pseudo out-of-sample.** The walk-forward protected the fit, not the 36 features, which were assembled after D786,
  D787 and D790 read 2016–2023 (D791 §4.1).
- **About two-thirds overfit in training** (ρ 0.16–0.23 against 0.059 out of sample). A rolling 3-year window has no
  edge. α 100 is the best of 10 / 100 / 1000. 2020, 2021 and 2023 carry it; 2018, 2019 and 2022 are flat or negative
  (D791's addendum).
- **The passive book is modelled** (GC's queue, D770's fill rule). The 8% of best sessions that never fill are
  already lost in it.
- **It is outside D792 by construction.** D792's assembled book names five members; including this line needs a new
  record.
- **Vault power at about 216 trades** (`data/vault_d793_power.json`): 0.53 at the out-of-sample edge, 0.27 at half,
  0.10 at zero. It is 0.84 if the edge is 2020–23's, and 0.01 if it is 2018–19's.
- **The vault read needs inputs not yet built** (`JOINT_RUN_CHECKLIST` D793). Among them is about USD 23 of GC quote
  data for 2024-01 → 2025-09, bought only on the principal's word.

**The ledger's live entries now:** #5 NQ F2 (slot 7), #6 NQ leads the Dow (slot 1), #7 the CPI/jobs-report fade
(slot 2), #8 base L4 (slot 10), #9 D791's gold China-open model (slot 11, by amendment).
