# The stack, signal to present

**What each layer contributes, what it is worth once costed honestly, and where
the next study goes.** Rewritten 2026-09-05 after D322–D330; §0, §3, §6 and
§7 brought to D337 the same day. The previous version stopped at D321.

Companion to [FINDINGS.md](FINDINGS.md) (substantive results) and
[decisions/](decisions/README.md) (one call each).
**[PICKUP.md](../PICKUP.md) is stale** — last updated 2026-09-02.

**§7 records what earlier versions of this document got wrong.** It has grown.

---

## 0. The stack, and what it earns — now stated as BOUNDS

```
signal        hist_L primary, D293 confluence      the LONG leg is real PER TRADE and zero
                                                   as a book (D335); the SHORT leg loses
                                                   under either sizing convention (D337)
construction  factor-neutral spread                removes -mu - sigma^2                  (D285)
width         N_eff = 2, FIXED                     +21 bp over N=19, basis-immune       (D300)
exit          the target, or nothing               +0.69 bp/bar, and only at N <= 3
overlay       CLOSED at this width                 negative at all 12 thresholds        (D319)
tilt          CLOSED, one variant carried          dv28, p = 0.0100, unconfirmed        (D320/D321)
universe      FLOOR, declared: as-traded close     removes 29% of live name-bars; the
              >= $5 at t-1 AND dv28 pass, the      tail it removes was not edge          (D339)
              name REPLACED
fill          NEXT OPEN, declared for new studies  the same-close fill was 13.8 of the
                                                   best book's 18.9 bp/bar               (D340)
```

**The incumbent book, under BOTH spread conventions** (D332). `PB` is the
per-bar median the programme has used since D318; `PUB` is the estimator as
its authors specify it, a trailing 21-bar mean. IBKR per-share commission in
both. **PUB is the default until quoted spreads decide** (D332 §4).

| N=2 / target, k=5 | net bp/bar | net Sharpe | held ½-spread |
|---|--:|--:|--:|
| PB, as reported D318–D332 | +14.57 | +0.334 | 18.3 |
| **PB, post-D333** | **+7.15** | **+0.187** | 18.3 |
| PUB, as reported D332 | −5.16 | −0.118 | 38.8 |
| **PUB, post-D333** | **−12.68** | **−0.332** | 38.8 |

**D333 found thirty fabricated return days in the fixture** — corporate
actions booked as cash dividends with the price left flat, applied by the
panel without a bound (PNK +356% on a +0.9% day) — and **the incumbent's
headline was half of them.** Under the published spread convention it loses
money at either level. What survives is every *relative* finding at a lower
level — concentration (**+23 bp** N2−N19, down from 30), the leg-wise
construction, the D323 order — and one absolute one: **`retrace_leg` at k=20,
+18.78 bp/bar PB and +13.76 PUB (Sharpe +0.568 / +0.416), is the best
symmetric book in the programme under either convention and the only one
above +10 under the published one.** The runner-up on both conventions is
now `price_log`, the known-bad control.

**Under the F0 deal filter, the same book is +18.93 bp/bar PUB, Sharpe
+0.546** (D335) — the filter removes the pinned names `retrace_leg` was
shorting at a fictitious spread. **And D338 gave it the four-group report it
never had: five names of 673 are half the P&L, the top trade is VSA at 15.9%
of the ledger — a real +330% day in a stock trading at about $0.18 on 2,738
shares, bought at the close and sold at the next — and four of the five
largest trades are sub-$2 names in the bottom 7% of the universe by dollar
volume, all below dv28's cut.** It beats every one of 200 rotations on every
statistic (+32.4 gross against a null max of +15.2), the symmetric trim clears
cost by 1.85×, and the ex-top-1% mean equals the round trip. **Not declared a
candidate.**

**Then D339 and D340, the same day, took the 18.93 apart.** A census of all 47
books found 25 take more than half their P&L below a $5 / dv28 floor and 35 have
a top trade that fails it — nine names supply the top trade of 30 books — so the
floor is a **universe definition** from here. Under it, `retrace_leg` is **+3.14
bp/bar PUB** (Sharpe 0.16, −24.5 a trade on the invariant lens, both legs
negative); it still orders the liquid gate — above its rotation null's maximum
on gross — and the floor *improves* `rsi` (−2.55 → +4.05) and `hist_L` (−26.8 →
−11.6) while leaving the incumbent's net unchanged and replacing its top trade.
And the **same-close fill** every D300-family book is scored under — signal at
the close, filled at that close, credited the overnight gap — was worth **13.8
bp/bar** of the 18.93: under a next-open fill `retrace_leg` is **+5.14** PUB,
inside its null on Sharpe, negative per trade; both its legs were flattered
(+44.8 bp per long entry, +27.2 per short — larger than the published
half-spread); the incumbent loses 3.2 bp/bar and D318's re-costing is
re-opened. **Honestly scored — floor and open fill together (D341) — the best
book in the programme is +2.68 bp/bar PUB, +2.46 after borrow, Sharpe 0.14.**
This document predicted "at or below zero" and was wrong: the two corrections
overlapped by 13 bp/bar, because the gap the fill credited lived in the names
the floor removed. The ordering is real — above all 24 rotations of the liquid
gate on gross — and the book is −27 bp a trade on both legs, nine names to half
its P&L, a tenth of it one bankruptcy, 44% in names that later died. By D339's
letter it is the first cell that survives every convention the programme owns
and its out-of-sample design is live; **D341 recommends against spending the
read on it.** `rsi` under the same two conventions is **+3.52**, Sharpe 0.18,
fourteen names to half, no gap dependence — the first book to *gain* from honest
scoring. **D342 gave it the candidate record and it passed: above all 24
rotations of its gate on gross and on PUB net Sharpe, +3.32 after borrow, a
5.5% top trade that is a real eighteen-bar decline in a liquid name. `rsi` under
the deal filter, the floor and the open fill is the personal track's DECLARED
CANDIDATE.** Its out-of-sample design is written and not run; D342 recommends
against spending the read until the null has more than 24 values and the
floor's re-listing hole (NBIS, 4.4% of the book, no dollar-volume estimate at
entry) is closed. Every one of its trades loses money uncapped — the book is the
slot cap — and eight of fourteen years are positive. Book: still empty.

**Every net number in this document is an UPPER BOUND even under PUB.** §3
lists what remains — the spread convention, undecided until quoted spreads
land; opportunity cost, unmeasured. Borrow and rebalancing are now
*measured* (D337) and neither moves a verdict.

### The best construction the programme has, and its bound

**Leg-wise: `hist_L` picks the longs, `skew_63` picks the shorts** (D329). No
composite before it let two signals own one leg each. It composes exactly —
its long ledger *is* `hist_L`'s and its short ledger *is* `skew_63`'s,
bit-identically in both lenses — so what it adds is the pairing, not a new
signal.

| k=20 | net per trade, PB | **net per trade, PUB** | net Sharpe, PB | net bp/bar, PUB |
|---|--:|--:|--:|--:|
| `hist_L` symmetric | −0.89 | −59.39 | −0.082 | −18.58 |
| `skew_63` symmetric | +44.83 | +8.14 | +0.421 | +4.97 |
| **leg-wise** | **+51 to +63** | **+17 to +36** | +0.22 to +0.43 | −4.0 to +5.6 |

*The range on each leg-wise cell is the D330 filter bound (over-filtered to
deal-contaminated). Under PUB the leg-wise book is a +36 per-trade edge and a
roughly break-even bp/bar book; it still beats both parents in both.*

**The bound existed because a fifth of `skew_63`'s short trades were takeover
targets pinned at the deal price** (D329 §10, D330). **D331 removed them by SEC
filing and `skew_63` is RETIRED as a short.** Target-specific forms find 84% of
the pinned trades in resolved names with a month's lead and exclude 2.4% of
the universe; with them gone the short leg nets **−24 to −30 / −61 to −65 per
trade** (PB / PUB, across the two EDGAR passes), the symmetric book is
−9 to −11 bp/bar, and the `hist_L`/`skew_63` book is **−11 bp/bar** under the
published convention. Every number that made
`skew_63` look special — +16.6, 7.7 bp, first of 44, D326's 4.53× coverage —
was the deals. It remains the best takeover-target *detector* in the 51.
**The enumeration was re-run under the deal filter and PUB (D335), and the
short side of the programme failed as a whole.** Of 46 short legs, **one**
nets above zero — `close_in_range`, +4.9 bp per trade against a p95 of −13.3
and a p50 of −132.9. Under the old per-bar median six of the top ten were
positive: PUB alone turned the short side from a signal question into a cost
question. Every top-3 × top-3 pairing beats `retrace_leg` symmetric **per
trade** and none beats it **per bar** (+14.80 best against +18.93): the
pairings hold 19–22 names against 14, and FINDINGS §10's opportunity cost —
still unmeasured — eats the per-trade edge. `hist_L`'s long leg is third-best
per trade under F0 + PUB (+44.8) and **≈ 0 bp/bar as a book**, at 69 bp a
name in $11 stocks; `rsi`'s is first per trade (+63.9) and its book is −2.55.

**D337 then tested the sizing fix and a borrow charge.** Constant shares on
the name is worth **exactly +45.85 bp** a trade on `hist_L`'s short leg — the
premium D329 measured, reproduced to 2e-14 — and the leg still nets **−53 PB /
−135 PUB**. Under compound accumulation the `hist_L`/`skew_63`-F0 book falls
*further* (−7.7 → −11.6 PUB per trade; −13.0 after GC+HTB borrow), because the
long leg gives back its +25 bp harvest. Borrow at declared stress rates is
0.25 bp/bar on the incumbent, 1.19 at the house 300.

**Status: the leg-wise construction is a per-trade result without a book,
three studies running (D331, D335, D337).** Nothing clears R8. Book: empty.

### The one declared VARIANT, carried and not promoted

```
+ dv28   exclude the bottom 28% of the live cross-section by trailing
         dollar volume, per bar, on a lagged 63-day mean          (D321)
```

| | gross | cost | **NET** | **netSHRP** | held ½s | held price |
|---|--:|--:|--:|--:|--:|--:|
| base (`N=2/target`, D321's costing) | +32.89 | 18.33 | +14.57 | +0.334 | 18.31 | $71 |
| **base + dv28** | **+32.93** | **14.56** | **+18.37** | **+0.507** | 14.54 | $73 |

**Status: CARRIED, NOT PROMOTED. p = 0.0100 against its rotation null**, clears
BH at every plausible effective count, misses at the nominal 19, unconfirmed on
a separate construction. **Any study using dv28 reports the cell with AND
without it.** It does not enter [BOOK.md](BOOK.md).

## 1. Three axes — unchanged, and still closed

### Axis A — should width VARY over time? **No. Five studies, all closed.**

D299, D308, D311, D312, D313. **D314 explains all five at once**: with
ρ = 0.0020, `Sharpe = √N·net/σ`, net is monotone down in width, so the optimum
is a **corner**, and a rule that varies N can only move away from one.

### Axis B — which FIXED width? **N_eff = 2, basis-immune — and a quarter of its premium was fabricated data.**

In D300/D306's construction turnover is `1/k` at every depth, so the cost basis
cancels: concentration wins whatever round trip is charged, and D332 confirmed
that under the published spread convention too. **But D333 cut the premium
from +29.6 to +22.9 bp/bar**: a +356% fabricated day is +178% on the bar in a
two-name book and +19% in a nineteen-name one, so the thirty bad days
flattered concentration most. **Concentration still wins, by 23.** The "+21"
this document has quoted since D300 was measured on the unbounded panel and
is not to be quoted again without the D333 tag.

### Axis C — which CONSTRUCTION? **D300/D306's, not D310's.**

D310 turned over 1.73× more and its width result flipped sign under the correct
basis (D317). D311–D316's *relative* results survive; their absolute nets do not.

## 2. The exit work — unchanged

Target +4.95 bp/bar, p = 0.0050 (D295); trailing overlay p = 0.0150 at N=19 and
**negative at every threshold at N=2** (D319). Costed correctly the target is
worth **+0.69 bp/bar at N=2**, reproduced three ways (D305, D307, D318). Stops,
displacement, idle conditions, the ladder: dead. `sel = rank < N_SLOTS` pins the
family: a price exit beside a signal exit is arithmetically inert.

## 3. Cost — wrong twice, fixed twice, and the fill convention was the largest hole of all

**Fixed (D317, D318):** the spread basis — per-cell across widths, common
within a width — and commission, which was never charged before D318.

**What the cost model charges today:** `4 × held median Corwin–Schultz
half-spread` per paired round trip, plus IBKR's official per-share commission
`$0.005 / price` per crossing. **The commission is IBKR's published schedule
and is not in question** — except that the schedule's **$1.00 per-order
minimum and 1% of trade value maximum are not applied**; the minimum depends on
position size and is the PM's to add, the maximum binds only below ~$0.50.

**Open, each with a mechanism:**

| hole | mechanism | size | status |
|---|---|---|---|
| **The spread CONVENTION** | The per-bar Corwin–Schultz estimate is clamped to zero on **43%** of live name-bars, uniformly, uncorrelated bar to bar; PB takes the median of that coin flip at entry, so a leg above 50% zeros is charged nothing. The authors average daily estimates over a month (`cs_spread`), which reads **2.03×** PB at the median across legs | incumbent +14.57 → **−5.16** bp/bar; every net level falls 8–20 bp/bar; relative findings unchanged | **D332. PUB is the default; which is TRUE needs quoted spreads.** D336 built the test — 100 live names, 5×5 price × dollar-volume strata, PB vs PUB vs Abdi–Ranaldo by lowest median absolute log error — and **the pull waits on the principal's IBKR session** |
| **Borrow** | Announced deal targets are the most crowded short in the market; any post-jump or sub-$5 name may be hard to borrow. PUB does not touch this | **MEASURED as a stress (D337):** GC 50 bp/yr, HTB 500 on F0-window or sub-$5 names → **0.25 bp/bar** on the incumbent (3% of its short bars HTB), 1.19 at the house 300. `hist_L` k=20 is 39% HTB and pays 10 bp a short trade | charged under new keys; does not decide any book |
| **Daily rebalancing** | The book is equal-weight, rebalanced daily, and earns the *sum* of one-bar returns; a rebalanced short pays a variance premium | **MEASURED (D337):** constant shares is worth **+45.85 bp** a trade on `hist_L`'s short leg and the leg still loses 53–135. **The premium is what the target exit SELECTS, not how long the book holds** — the fixed 20-bar hold's is −33.8 against the target's −45.8 | `simulate(accumulate="compound")` exists; the trades that realise the rebalance are still free (the cost side of this hole is open) |
| **The FILL convention** | Signal at close t−1, position opened at bar t **earning close[t−1] → close[t]**: a fill at the signal's own close, the overnight gap credited to a position that could not have existed before the open. Every D300-family book, since D300 | **`retrace_leg` +18.93 → +5.14 PUB bp/bar; the incumbent −12.68 → −15.90**; +44.8 bp per long entry and +27.2 per short on `retrace_leg` — larger than the published half-spread; only 378 of 1,256 trades recur across fills | **MEASURED (D340).** `simulate(fill="open")` exists; default stays `"close"` so every identity reproduces; **every net number in this document is a same-close-fill number** and carries an open-fill companion where next quoted; D318's re-costing re-opened |
| **Liquidity** | No price or volume floor on a dead-inclusive universe; cost in bp scales with 1/price but *fillability* scales with dollar volume, which no cost model charges | 25 of 47 books take more than half their P&L below $5 / dv28; `retrace_leg` +18.93 → +3.14 under the floor; the floor improves `rsi` and `hist_L` | **DECLARED UNIVERSE (D339)**: as-traded close ≥ $5 at t−1 and the dv28 pass, the name replaced; a study on the unfloored universe says so and reports both |
| **Opportunity cost** | `sel = rank < N_SLOTS`: the refill pool is the slot count, so a per-trade edge spread over more slots earns less per bar | **its sign is now visible**: the floored `retrace_leg` is +3.14 bp/bar on the variant lens and **−24.5 a trade** on the invariant one; the two lenses disagree in sign (D339) | **open, unmeasured** (FINDINGS §10) |

*The "floor at zero" hole the previous version listed was a symptom of the
convention, not a hole of its own: under PUB the half-tick floor moves nothing
by more than 1 bp (D332 Q7).*

**And one that was not a cost at all — CLOSED (D333):**

| hole | mechanism | size | status |
|---|---|---|---|
| **Corporate actions booked as dividends** | The panel applied every event-file dividend as `log1p(amount / close)` with no bound; thirty spin-offs, mergers and splits are recorded as cash dividends with the price left flat, and became +9% to +356% return days | incumbent −7.4 bp/bar (half its book); concentration premium −6.7; every reversal-type signal −5 | **fixed in `load_ragged`**: a dividend ≥ 10% of price is applied only if the price fell ≥ half the implied move. Score cache rebuilt (D334): 48 of 51 bit-identical; `beta_63` had moved on **30%** of all cells through the market return, `ivol_21` on 12.7%, `signed_vol` on 86 — and the three books by under 0.5 bp/bar |

**Two references are still on the unbounded panel:** `data/d331_deal_filter.json`
(`S_F0` is ~7 bp a trade optimistic there; D337 §9) and `data/d300_width.json`
(`run_d306`'s own [10] now fails by 7.5 bp against it; D337 §10). Both are
quoted evidence and are re-based beside, not over, the old file — owed.

**The rebalancing premium is no longer a hole; it is a measured quantity that
did not decide a leg.** D328 §11 named it, D329 measured it (+25.2 to `hist_L`'s
long, −45.8 to its short), and D337 tested the fix: constant shares recovers
the 45.8 exactly and the short leg is still −53 PB / −135 PUB. The previous
version of this paragraph called the short leg's loss "a sizing artefact with
a concrete fix, not a signal failure." **It is a cost failure** — D335's
finding across all 46 signals — and the sizing fix was worth a third of it.

## 4. What is decisive, and what is merely not-rejected

**Decisive against a null:** the spread construction; concentration
(p = 0.0050 at every depth); **leg ownership on the short side** —
`skew_63` first of 44 real partners, above the control's p95, on both lenses
(D329).

**Real but small, confirmed three ways:** the target, ~+0.7 bp/bar.

**Real, and now with a mechanism:** `hist_L`'s long leg (+97 net per trade,
t ≈ 3, **decays by k=40** as a real signal should); the two-leg asymmetry.

**Not resolvable on this fixture:** any per-bar paired test at N_eff = 2 — MDE
11–18 bp/bar against a book netting ~11 (D316). Any per-trade `t` on a leg
that lives in its tails — `skew_63`'s short leg is +0.9, with its top 1% of
trades at 159% of P&L and its bottom 1% at −203%.

## 5. What happened between D322 and D330, in one paragraph each

**D322 — the four-group report.** 57% of the incumbent's P&L sits in the
cheapest price tercile at 8× the commission. Cost scales as 1/price; the book
is a cheap-name book.

**D323 / D324 — the shortlist at the operating point.** D290's 51 re-read at
N=2. `retrace_leg` (+20.91 bp/bar, netSHRP +0.625 at k=20) and `rsi` (+22.66,
+0.585 at k=10) lead the incumbent's +11.36. **The ranking inverts with width**
and the incumbent is the least fragile of the four. A defect in the short leg's
rank order — it shorted the *least* extreme names — was caught by a later
assertion and voided the first run.

**D325 / D326 — composites, both lenses.** D325's +0.370 composite premium and
a −0.644 pair effect. **D326 split them: the premium was the slot cap
re-ordering which two names survive; the pair effect is a signal effect and
survives the cap removed.** Neither beats `retrace_leg` alone. The mechanism
D327 offered for the pair effect was withdrawn (below).

**D327 / D328 — the rank profile, at two resolutions.** No signal is monotone;
the edge is a tail effect with a noisy middle. **`macd_hist` is computed in
dollars and its extreme ranks are a price sort** — $2,706 at one end, $3,020 at
the other, $22 in the middle — with a compounded spread of +18 bp carrying
146 bp of cost. Three of D290's 51 carry dollars by accident. D328 was
corrected three times in one day: a summed-vs-compounded *convention* mistaken
for an error, a persistence hypothesis filed unmeasured, and a price-deviation
"result" that was both errors stacked. What survived is the rebalancing
premium and the tilt mechanism: **return cancels between the legs, cost adds
across them.**

**D329 — the leg-wise composite.** §0 above. Six of seven predictions failed
as written (every-k forms, a +0.10 margin); the substance at the operating
point held; the enumeration was the finding.

**D330 — the pinned names, mapped, and the tape's limit.** Short side: median
1.5% pinned, `skew_63` 21%, `hist_L` 1.2%. Long side: **every volatility score
24–35%**, surviving names at half-spread 0.0 — axis E's long side was never a
book. A causal filter caught 71% of pinned trades and removed 39% of survivors:
**a jump followed by quiet is a deal and a reversal candidate alike.** A
deal-event source is required; an EDGAR pull is in progress (D331).

## 6. Next, in order, and why the order

**D334–D340 are done, bar one pull.** What they returned: borrow and rebalancing
are measured and small; the short side fails on cost under every signal; the
leg-wise book is per-trade only; the fixture's illiquid tail was every book's
top trade and none of their edge, so the universe now has a floor; and **the fill
convention was worth more than any cost term the programme argued about** —
every number quoted before D340 is a same-close-fill number.

1. **Score cache — DONE (D334).** Rebuilt under the dividend bound; 48 of 51
   bit-identical; `beta_63` had been stale on a third of its cells.
2. **The legs under the deal filter and PUB — DONE (D335).** One short leg in
   46 pays its cost; no pairing beats `retrace_leg` symmetric per bar.
3. **Quoted spreads — BUILT, PULL PENDING (D336).** `--pull` needs the
   principal's TWS/Gateway session (~35 min under IBKR's pacing); `--compare`
   then decides PB vs PUB vs Abdi–Ranaldo by the rule D332 declared. **Until
   it runs, every net number here is a PB / PUB pair.** Note before reading it:
   Abdi–Ranaldo clamps to zero on 28 of the 100 sample names, so Q2 may be
   decided by the 1 bp floor (D336 §8a).
4. **Constant shares and borrow — DONE (D337).** Worth 46 bp on the short leg,
   not enough; borrow 0.25 bp/bar; the leg-wise book negative at every scheme.

5. **`retrace_leg` under F0 — DONE (D338), not declared.** Five names, a $0.18
   top trade at 15.9%, four of five top trades below the dollar-volume cut.
6. **The census and the universe floor — DONE (D339).** The floor is the
   declared universe; `retrace_leg` +3.14 under it, a formal candidate by the
   record's letter with its own recommendation against an OOS read.
7. **The execution lag — DONE (D340).** The next-open fill exists as a flag;
   `retrace_leg` +5.14 under it; the incumbent −15.90.

8. **The stack under floor AND open fill — DONE (D341).** `retrace_leg` +2.68
   PUB (+2.46 after borrow), the incumbent −13.41, `rsi` **+3.52**, `hist_L`
   −10.28. The prediction "at or below zero" was falsified: the two corrections
   overlapped by 13 bp/bar. Seventy published numbers reproduced to 0.0.

9. **`rsi` candidate record — DONE (D342). Declared.** Six of eight; above all
   24 rotations on gross and PUB net Sharpe; the OOS design written, not run.

**Next, in this order:**

1. **Close the floor's re-listing hole** — a pre-registered amendment to the
   universe definition: a name passes the dollar-volume clause only with its
   21 observations (D320's missing-estimate rule stays for the *spread*, not
   for a *liquidity* floor). Re-run D342's cell under it as an identity study;
   NBIS leaves and 4.4% of the book with it.
2. **The rotation null's resolution.** 24 distinct values is the ceiling every
   D300-family p has been quoted against; `rsi` clears it by 0.09 bp/bar on
   gross. A finer null — rotation by name and by time, or a bootstrap over the
   gate — pre-registered on the `rsi` cell, before any read.
3. **Re-base the two stale references** — `d300_width.json` and D331's cells —
   under the bounded panel, old files kept beside (D337 §9–10).
4. **Opportunity cost, measured** (FINDINGS §10). Its sign is now visible on
   both candidates: `rsi` is +3.52 a bar on the variant lens and **−4.8 a trade
   on the invariant one, both legs negative** — the book IS the slot cap.
   Pre-register: hold the slot count fixed and vary the refill pool, or the
   reverse.
5. **The mixed convention** — rebalanced long, constant-shares short — only if
   anyone wants the leg-wise book back (D337 §5, post-hoc).

**Then, signal-side, each with a mechanism behind it:** `macd_hist` normalised
and D325 re-run; collapse capture in the high-vol short legs — 0–4% of trades
at +1,300 to +3,500 each — which needs a tail-aware framework, not a mean per
trade.

**Owed, still:** sub-2 widths on D300/D306's construction (D315a tested them on
D310's); D318's re-costing detaches D300/D306's null p-values from their exit
cells; dv28 on a separate construction at a threshold fixed at 28; a guard on
`log1p` in `simulate` before any fixture with a zero close (D337 §10).

## 7. What earlier versions of this document got wrong

Kept legible rather than quietly fixed.

1. **"Nothing after D300 was an improvement."** Wrong — D303, D305 arm S, D306.
2. **Calling the target and the exits "decoration" on a paired t of +0.17.**
   Wrong bar and wrong inference: the programme's standard is beating your own
   matched null, and the paired test was blind (MDE 18 against a book netting 11).
3. **Quoting D310's `none/exp2` at +4.37 as "the best cell".** Wrong
   construction and the universe's cost basis.
4. **"Cost, which was wrong twice and is now right."** *(the previous
   version's §3 heading)* It was wrong in three further places, each large
   enough to move a verdict, and the sentence was written the day before the
   first of them was found. **A cost model is never "now right"; it is "not yet
   found wrong in these places."**
5. **The composite mechanism** — "a signal can carry information at depths its
   own book never trades." Filed after the effect it explained, on a signal
   that turned out to rank price. Withdrawn.
6. **Three corrections on one study (D328).** A convention called an error; a
   hypothesis filed before it was measured; a perfect Spearman on five points
   with a measure chosen after seeing them. All caught before promotion, two by
   the principal's questions and one by a read-only audit agent.
7. **The best cost coverage in the programme (`skew_63`, 4.5×) was
   "unexplained" for three studies.** It was takeover targets read as free.
   **Measure the price and the spread of what each leg HOLDS** — FINDINGS §14
   — would have found it in D326.
8. **D322 reported "six names of 718 make half the P&L" and "top-1% of trades
   = 96.3% of P&L", and nobody asked which six.** PNK was one of them, and its
   bar was a $38.86 dividend on an $11 stock with the price flat. Reporting
   rule 3 was followed and stopped one question short. **A concentration
   report is not finished until the top trade is named and its bar is looked
   at** (FINDINGS §18). Fifteen studies were run on the unbounded panel.
9. **"The short leg is the worst leg measured for a SIZING reason."** *(this
   document's §0, previous version)* The sizing effect was real and exactly
   measured, and it was a third of the loss. The leg fails on cost, like 45
   of the other 46 short legs (D335, D337). **A mechanism's size is not its
   sign** — the premium was named, measured and tested, and never decided a leg.
10. **The rebalancing premium as a duration effect** — "longer holds pay more
    of it." Longer holds pay *less*; the target exit selects the paths that
    moved, and those are the paths a rebalanced short pays on (D337 §3). Two
    pre-registered predictions were wrong in the same direction for the same
    reason.
11. **"`retrace_leg` is the best book in the programme"** — said for three
    studies (D333, D335, D337) off cells in other studies' tables, without a
    four-group report. D338 gave it one: five names, a $0.18 top trade at
    15.9%, four of five top trades below the dollar-volume cut the programme
    already has. **A cell in a table is not a book until the top trade is
    named and its liquidity printed** — FINDINGS §18's rule, extended.
12. **Every net number in this document before D340 was a same-close-fill
    number, and no record questioned the fill.** Forty studies scored a
    position from the close its signal was computed at. The convention was
    inherited from D295 and D303's "mark with r1[:, t]" and never named as a
    choice. It was worth 13.8 of the best book's 18.9 bp/bar and 3.2 of the
    incumbent's. **A simulator's timing convention is part of the cost model
    and is declared like one.**
13. **"p = 0.0050" on a null with 24 distinct values.** The rotation null draws
    a shift from 1 to 24; 200 draws are 24 books. Every D300-family p below
    0.04 means "above all 24", nothing finer. Not wrong, but quoted with a
    precision it never had.
14. **"Honestly scored, the best book is at or below zero."** *(this document's
    §6, the version before D341)* It is +2.68. I summed two corrections that
    share a cause — the overnight gap the fill removed was in the names the
    floor removed — and the sum overstated the damage by 13 bp/bar.
    **Corrections with a common mechanism do not add; predict the interaction,
    or predict nothing.** The `hist_L` square adds a second warning: with a
    target exit, a fill change makes a different book, and its effect can have
    the opposite sign to the per-entry premium.
15. **D341's floor-share assertion compared a number to itself for one
    commit.** Its fallback `.get(key, share)` defaulted to the value under
    test when the key was absent, and the key was absent. The printed value was
    right; the check was vacuous; it was found only because D342 wrote the same
    check without the fallback and tripped. **A fallback in an assertion is a
    way of making it unable to fail** — raise on a missing key.

The common thread has not changed: reading a non-result as a null result,
ranking cells off a published table instead of measuring the difference, and
filing a mechanism before checking the statistic orders the outcome.
