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

**Entry #1 PARKED, 2026-09-12 (the principal).** K8 stays PROVISIONAL and its forward read is
**held**. Reason: the 2024+ day session is the one unseen slice this line has, and rule 3 above
confirms the *assembled book* on the same slice, so a K8-only read would make the book's
confirmation a re-read for K8. The read runs once, together with the second component's promotion
and hurdle P on the assembled book, when a second entry exists. K8 is not sharpened, filtered or
re-scored in-sample while parked. ES K8 (+0.18, inside its null, ρ ≈ 0.85) is the same construction
on another root and is not a second entry. Noted in `BOOK_PROP.md` (last section).

## Scored and NOT entered

| construction | record | net Sharpe | why not |
|---|---|---|---|
| K1 C1: ES hold 18:00→16:00 every same-contract night, 1 MES, $3 | D466 (D449, D465) | **+0.37 (SE 0.32)**; gross +0.63 | C-a. $3 is 41% of the $7.29 gross mean per night; clears C-a only below $1.48 a round trip |
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
