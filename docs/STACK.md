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
universe      FLOOR, declared: as-traded close     removes 31% of live name-bars; the
              >= $5 at t-1 AND dv28 pass WITH its  tail it removes was not edge, and the
              21 observations, the name REPLACED   re-listing hole cost money    (D339, D343)
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
CANDIDATE.** Its out-of-sample design is written and not run. **D343 closed the
floor's re-listing hole** — the dollar-volume clause now requires its 21
observations (`keep_v2`, the universe from here; 30.9% of live name-bars fail)
— and `rsi` under it is **+3.10 PUB, +2.90 after borrow, Sharpe 0.16**, above
all 24 rotations on gross by 1.3 bp/bar (v1's margin was 0.09), drawdown down
a fifth, seven of fourteen years positive, the short leg positive per trade for
the first time. The 35 trades the hole had admitted across three books lost 134
bp a trade on net. **D344 then found the hold is a cost lever: at k=40 the same
cell is +5.14 PUB, +4.93 after borrow, Sharpe 0.27, drawdown down a quarter,
nine of fourteen years positive, above all 24 rotations on every statistic** —
the only cell in the programme to manage that; k=10 is −5.89 and inside its
null. **The candidate is now `rsi` at k=40**, a choice made after seeing three
cells and written into the out-of-sample design as such; k=40 is quoted beside
k=20 (+3.10) and never alone. Under a target exit k is a cap, so turnover follows
the realised hold and not 1/k. D342's recommendation against spending the read
stands until the null has more than 24 values. Book: still empty.

**D345 tried the construction the principal asked for — flat by default, enter
on a signal, exit on a condition — and it failed as calibrated.** Setting the
`rsi` threshold to match the slot book's exposure sent it to 11 / 89, where the
signal fires nine times a year; the book ran net short with an unhedged capital
series; and D303's target exit, built for a book that refills, cut the winners
at the first move (−2 net a trade against +182 under the invalidation exit).
Axis C closes again, for those three reasons and not for a fourth. What
survives: an event kernel proven bit-identical to the slot simulator's uncapped
lens, **the first positive invariant lens in the programme** (+12.9 net on
every signal, p = 0.055 against a 200-value null), and the amendment that
**exits were inert only because the slot refilled behind them**. A retry —
threshold on trade count, hedged series, invalidation exit — is a new
pre-registration and is not run.

**D346 re-ran all 46 legs under the floor and the open fill.** Two long legs
pay their cost uncapped at k=20 (`hist_L` +30.9, `rev_21` +5.9) and three at
k=40; none of `rsi`, `retrace_leg`, `rev_5` does. The corrections *compressed*
the table: 29 of 46 long legs improved, the best fell hardest, the long-leg p95
went from +42 to −6. And at k=40 **`hist_L` symmetric — the incumbent's own
primary — is +12.42 bp/bar with a Sharpe of 0.40**, two and a half times the
candidate's, with `id_mean` +9.61 and `dollar_vol` +8.47 also above `rsi`. One
cell of 92, unnulled, no top trade named: it gets the next candidate record
before anything is built on it, and `rsi` stays the declared candidate until it
does.

**D347 asked whether any long signal is real against controls that carry the
drift, and none is.** `hist_L`, `rev_21` and two `rsi` references as events,
every event taken, hedged against the floored market: each earns +16 to +60 bp
a trade, and **each earns less than its own names held at random times**
(per-name time rotation, medians +45 to +71). The excess is *which names*, a
cohort that pays whenever it is held; the signals' timing is worth −10 to −29
against it. Neither the floored hedge nor a rolling beta removes cohort drift.
**And the pairing design is reversed on its own terms**: `hist_L` on names in
the bottom 2% by `rsi` earns +1 bp, on neutral names +103 — the extreme of the
ranking is where the long signals do worst. **The per-name time rotation has
never been applied to the slot books' cells** — their nulls rotate names within
the gate on the same day, which these signals beat — so every per-trade
positive in D335, D344 and D346 is unmeasured against it. It goes there next.

**D348 put that time rotation on the slot books, and they survive it.** Each
name's *score* rolled within its own finite bars, re-ranked, re-simulated, 200
draws: `rsi` k=40 (+5.14 PUB), `hist_L` k=40 (+12.42) and `retrace_leg` k=20
(+2.68) are above **every** draw on gross, net, both Sharpes and both legs.
**The slot book's long leg is timing, not cohort drift**: the same kind of
names selected at random times lose 10–13 bp a trade against observed +39 and
+141. D347's cohort finding was a property of the decile-entry event it tested
— any of ~1,500 names entering the bottom decile — not of the depth-2 book.
**And on a slot book the time rotation is the *easier* null**: its p95 is
below the rank rotation's on all three cells, because the rank rotation keeps
the day. Both are carried; the rank rotation stays binding. The `hist_L` k=40
candidate record is now owed. `hist_L`'s short leg is a cohort premium (A
centred +17, observed at the 70th percentile); its book is its long leg.

**D349 asked the same three controls of the short signals, and none is
real.** `on_share`, `skew_63`, `close_in_range` and two `rsi` references as
top-decile events: every one beats its own names shorted at random times by
26–67 bp — the timing is real — and every one still loses in mean before cost,
because those names *rise* 56–70 bp at random times. None beats the
random-direction control; the long of every short event pays. The cost is not
what loses it: borrow is 8 bp a trade and HTB is structurally rare. The
extreme of the `rsi` ranking is where a signal does worst on the short side
too (`on_share` −46 in the top 2%, +52 in the middle). **The pair book has no
trigger on either side under the current conventions.** Erratum to D347: its
top-bucket base rate of −31 was names with no `rsi` rank digitised into bucket
9; the top 2% earns +11 long.

**D351 withdrew D347's headline and the two paragraphs above it are amended
by it.** D347's and D349's control A rolled each name's events within *every
priced bar*, so 8–13% of the rotated events landed on the name's own sub-$5
and illiquid spells — bars the floor forbids — worth **+226 to +318 bp** per
forty bars. The null was trading the excluded tail. Reproduced to 0.0 from the
studies' seeds, then rotated within the floor: control A for `hist_L` is **+24,
not +71**, and `hist_L`, `rev_21` and the `rsi` decile are **above it, above B
and above C**. Three of D347's four long signals are real against
drift-matched controls; the cohort premium is +7 to +24, not +45 to +71.
D349's verdict stands (every short negative in mean, none above C) with its
timing values cut to +0 to +33; D348's numbers stand and its "disagreement"
with D347 was the broken null, not the construction. **What D347 called
cohort drift was the tail D339 removed, seen through a null that did not
respect the removal.**

**D350 screened 138 long events and, under the corrected control, named three
triggers.** 43 of 138 members beat their own names at random eligible times
against 7–9 from false discovery; BH rejects 34; every reversal-type score has
timing. Under the kernel, **`rev_5`/E1** (+43 a trade, t 4.8 on 27,316 trades,
mean equal to median, ten of fourteen years, its top trade 1.3%),
`gap_reversal`/E1 (+47, three top trades GME in January 2021, +95 below the
median price and −1 above) and `cs_spread`/E2 (+72, the floor's own illiquid
edge) are above A′, B and C. **None nets positive after the published spread**
(−19 to −35 a trade; +17 to +28 under PB). The long side's problem is cost,
as it has been since D285. And on the fourth table to show it, **the bottom of
the `rsi` ranking is where every long signal does worst**: the pair book must
not select its long trigger there.

**D352 screened 139 short events down to the top 2% of every score and found no
short trigger.** 23 beat their own names at random eligible times, four passed
the gate, and under the kernel none is above random direction: the means are
−11.5 to +25.6 a trade. The short side's timing is real and worth less than the
names' own rise. `on_share` and `skew_63` pass at no shape — **the slot book's
short leg at depth 2 is not an event on the same score.** The pair book has one
side.

**D353 gave `rev_5` entering the bottom decile the full record: real at 200
draws on every control** (+43.4 a trade, above A′ +28.6, B +35.8, C +15.2; mean
equal to median, ten of fourteen years, top trade 1.3%), **−18.6 net under PUB,
+17.9 under PB**, and the invalidation exit three times as productive per bar
held. The slot-capped event book on it at two slots loses, because a two-slot
cap on 72,677 events admits 161 entries in sixteen years, most extreme first —
the crashes that do not bounce; at four slots it nets +3.5 PUB on 322 entries,
one cell of four, recorded not built on. The kernel's capital series is now
hedged as its ledger is, additive and proven to 0.0.

**D354 built the pair book the principal designed and it fails on its long
arm.** `rev_5`'s trigger hedged with a short basket of the three highest-`rsi`
names: at two pairs −4.9 PUB, negative under both cost lines, inside both nulls;
**the basket leg loses 181 bp per pair** and the pair is more volatile than a
market hedge (285 vs 232 bp/bar). At four pairs +5.9, above the trigger's time
rotation and **inside the random-partner null**: any name from the top gate
hedges as well as the three most extreme, so the ranking chooses no hedge. The
short arm had no trigger to run. **The pair book is closed on this
construction; what survives of it is the trigger.**

**D355 put the invalidation exit on the two candidate books and the target
stays.** Zero of seven: exiting on the signal's median crossing takes `rsi`
k=40 from +5.14 to +0.54 and `hist_L` k=40 from +12.42 to +10.34, because on a
refilled slot book the target already fires first (15 bars against 27) and the
invalidation exit holds through what the target would have banked; exiting on
either cuts `hist_L` to −7.75 on churn. The event lens's exit finding (D345,
D353) does not transfer, for a stated mechanism: **the target is the exit that
matches the refill.** The slot simulator now has a signal exit, additive and
proven identical to the event kernel's.

**D356 blended the two books and the blend is the best thing in the record:
+8.78 bp/bar net under PUB at a Sharpe of 0.442** against 0.268 and 0.401, on a
correlation of 0.21, above 100 of 100 paired time rotations and 24 of 24 paired
rank rotations. The two books hold the same name on the same side on 46% of
bars and their worst 1% of bars overlap on two dates; the drawdown sits between
the parents'. A linear blend's Sharpe is arithmetic, so the only prediction
worth making about a blend is the correlation. **The blend is the construction
D357's one holdout read is spent on**, with both parents reported beside.

**D358 built the flat-by-default sleeve the principal's multi-strategy book
wants — a real trigger, a market hedge, no slot cap, scored on the capital it
asks for — and it is never flat.** A fresh entry into the bottom 2% of ~1,000
names fires five times a bar; a 40-bar hold stacks 120 open positions and every
cell, both scores, three rarities, is deployed on 100% of bars. Flatness cannot
come from a cross-sectional trigger at any rarity worth trading; it has to
come from a time-series gate, which is the allocator's job. What the sleeve
earns while on: **+1.1 to +2.9 bp/bar of hedged alpha on the deployed base**,
at or below the held names' own round trip on five cells of six, and about 30%
of what the same names earn unhedged. `rev_5` at 2% is −1.93 net PUB, above
all 100 time rotations and inside the same-day same-bucket name's p95 on net
alone — the trigger selects wide names (36 bp a side PUB) and a random name in
its bucket is cheaper. `rev_5` 10% and `hist_L` 2% clear both nulls and net
negative under PUB (`hist_L` 2% is +0.70 PB); both wait on D336. Twelve per-bar
series are in `data/` for an allocator to condition on era: per trade the
trigger is −26 in era 1 and +127 in era 2.

**D359 reasoned a short signal from why the others failed — short a rally
inside a pool that drifts down, the bottom decile of 12-month momentum — and
measured the pool before timing anything in it. The pool is not there.** On
the floored universe the loser decile drifts **up**, +0.64 bp/bar hedged over
the span, down only in era 1 (−2.4) and the down-years (−2.9): the $5 / dv28
floor removes the names whose fall a short needs, and what remains of the
loser decile bounces. The spike inside it is +8.9 a trade on 8,085, inside
every control including a random same-day name from the same cohort, three
names half its P&L, on names 45 bp a side wide. It earned only where the
cohort fell: era 1 +27, down-years +45 a trade — a regime fact, not a signal.
**Every short signal since D335 has been timing inside a pool that rises**, and
that is now a statement about the universe, not about any signal. Beside it,
unpre-registered and without nulls: the mirror — a fresh dip in a 12-month
winner, long — is **+68.6 a trade at cap 10 and +160 at cap 40, +83 net PUB**,
the best per-trade long number in the record, and it is the next
pre-registration, not a result.

**D360 tried the last kind of short the tape can express — an event in an
ordinary name, a gap in the bottom 2% of the day on top-decile volume, the
drift after bad news — and there is no drift: the gapped name bounces.** Zero
of nine. The primary cell is −0.4 a trade on 20,059; its own names at random
times earn the short +6.3, so the day after a volume gap down is a *better*
day to be long the name than a random day, by 6 bp at ten bars and 33 at
twenty, and by 17 to 38 in the down-years. The gap up on volume reverses too
(the mirror, long, −15 a trade on every cell). The names are ordinary — $35,
31 bp a side, general collateral — and it does not matter. **The short side
has no tape signal on the floored universe**: levels select the wide names
whose drift is smaller than their cost (D352), loser rallies sit inside a pool
that rises (D359), news gaps reverse (D360). *Amended the same day at the
principal's ruling: that is what was tested, not a closure — the avenue is
the principal's to close, and the criterion for a signal is a positive
GROSS mean per trade above the nulls, cost tuned afterwards.* Untested and
queued as D361: a regime gate on the triggers the record has — the only
place any short paid before cost is where the loser cohort falls — and the
gap-up fade under its own controls.

**D361 made the regime the signal and found the regime points the other
way.** With the floored market's 63-day return negative, the loser cohort
rises +96 bp over the next 20 bars (−16 otherwise) and the market +188
(+80), block correlation −0.23 against a shuffled p95 of 0.16: **a negative
trailing market return is a rebound forecast**, and D359's era-1 and
down-year splits were averages over both halves of a drawdown, not states
one can be in at the time. The gated loser rally is −4.5 a trade inside
every control; gate off it is +22.5. **But one cell of four is above every
control**: the gap-up fade — D360's mirror entered short, a gap in the top 2%
of the day on top-decile volume — with the market **below its 200-day mean**,
**+42.3 gross a trade on 3,977** (t 2.5), above the 200-draw gate rotation
(p95 +36.0), its own names at random gate-on times (+25.8), the same-day
name (+37.7) and random direction (+25.2); +3.3 net PB, −47 PUB, breakeven
18 bp a side; era 2 +55, down-years +50. It is the first short in the
record to clear all its nulls, on a non-primary cell with margins of 5 to 6
bp at the p95s, and it is not yet its own record. The gated arms are the
first flat-by-default constructions in the record (28 to 42% exposure).
Status: the principal's decision (R15).

**D362 took every trade of that cell into a file, screened forty entry-time
features for the losing edges, and put the five that survived back through
the kernel with their own nulls.** Removing events that hit either of the
first two — a name trading below most of its own volume history, or a calm
market — gives **+61.7 gross a trade on 3,079** (t 3.2) against +42.3, above
200 random removals of the same size (p95 +55.7) and 200 rotations of each
name's own flags in time (+54.3); both eras improve, the 1% trim rises from
+35 to +57, eleven names to half, **+20 net under PB, −30 under PUB**.
Removing all five is +83.6 on 1,868 and inside the flag rotation: the three
extra sinks are names, not timing. Halving size per hit keeps every trade at
+66 per unit of capital and t 3.9. **And with the calm-market sink on, the
200-day gate is inside its own rotation's p95** — the filter took over part of
what the gate did; which of the two is the state variable is the next cell,
listed and not run. Within-sample with nulls: the five came from this
sample's own trades; the holdout was not read. The principal decides.

**D363 asked where the two-sink fade's 89 bp round trip could move, and
the answer is: not in the estimator, and not in the sizing — in the
execution.** The Corwin–Schultz spread on the three bars around the entry
is a fifth narrower than the trailing month at the median (34.6 against
42.9 a side) and no narrower at the mean (52.4 against 51.7): the wide
tail, where the gross lives, does not compress on volume days, and the
round trip moves 3 bp. **Charging each trade its own spread rather than
the ledger's median** — the per-trade convention from here, the median
printed beside — gives 108 bp under PUB (D362: 89) and 125 under PB (39),
because PB's single pair is zero on 43% of bars with a fat right tail; the
net is **−49 / −66**, not −30 / +20. Full crossing −46 to −66 a trade, one
side crossing about zero, neither side +55; **what the opening and closing
auctions cost is the number the programme does not have**, and daily bars
cannot supply it. Only the widest quintile pays at full crossing (+6 PUB,
+36 on the entry-window line, names at $20 with a 94 bp half-spread).
Inverse-cost sizing halves the gross; the U shape is above its permutation
null by 1.7 bp and still negative. D336 on hold at the principal's
instruction; nothing here pre-empts it.

**D364 measured the denominator that last claim rested on, and it was the
wrong one.** One-minute bars with extended hours on a stratified sample of
the fade's own trades: the **09:30 minute is a median 1.44% of the whole
day** and the **16:00 minute 7.85%**, so the honest denominator is 69×
smaller at the open and 13× at the close. The same $25k order is **2.5% of
the opening minute**; two thirds of entries are above 1% of it and a third
above 5%; and the widest PUB quintile, which carries the entire edge, is
the **thinnest at 4.2%**. Both minute bars are upper bounds on the auction
itself, so true participation is larger. This measures no impact and claims
none — it withdraws the reason for believing the +55 was reachable. The
three bounds stand as arithmetic. The sentence that stood here, *"at $25k a
position the trade is 0.04% of the day's dollar volume, so liquidity is not
the constraint"*, is **withdrawn**; FINDINGS §43 carries the same amendment
and §44 the measurement.

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

### Axis C — which CONSTRUCTION? **D300/D306's, not D310's — and not, as calibrated, an event book (D345).**

D310 turned over 1.73× more and its width result flipped sign under the correct
basis (D317). D311–D316's *relative* results survive; their absolute nets do not.
**Reopened once at the principal's decision (D345)** for a flat-by-default,
enter-on-signal, exit-on-condition book, and closed again: the exposure
calibration put the threshold where the signal barely fires, the capital series
were unhedged, and the target exit was the slot book's. The kernel is kept and
trusted; a retry is a new pre-registration.

## 2. The exit work — amended by D345

Target +4.95 bp/bar, p = 0.0050 (D295); trailing overlay p = 0.0150 at N=19 and
**negative at every threshold at N=2** (D319). Costed correctly the target is
worth **+0.69 bp/bar at N=2**, reproduced three ways (D305, D307, D318). Stops,
displacement, idle conditions, the ladder: dead **in the slot book**, because
`sel = rank < N_SLOTS` refills behind any exit and makes a price exit beside a
signal exit arithmetically inert. **D345 showed that is a property of the
construction, not of exits**: in a book with no refill, D303's target cuts
winners at the first move (−2 net a trade) and a signal-invalidation exit is
worth +185 bp a trade over it.

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

10. **The re-listing clause — DONE (D343).** `keep_v2` is the universe; `rsi`
    +3.10 under it, above all 24 rotations by 1.3; the hole's 35 trades lost
    134 bp each on net. `retrace_leg` bit-identical; the incumbent +0.12.

11. **The hold-length check — DONE (D344).** k=40 nets +5.14 PUB, Sharpe 0.27,
    above all 24 rotations on every statistic; k=10 negative and inside its
    null. The candidate cell is k=40, multiplicity three, quoted beside k=20.

12. **The event-driven book — DONE (D345), failed as calibrated.** Axis C
    closed again; the kernel kept; the exit amendment made; the first positive
    invariant lens recorded at p = 0.055.

13. **The 46 legs under the floor and the open fill — DONE (D346).** Two long
    legs pay uncapped; the table compressed; `hist_L` at k=40 is the best book
    (+12.42, Sharpe 0.40), one cell of 92.

14. **The long-signal controls — DONE (D347).** Zero of eight; no long signal
    beats its own names at random times; the extreme `rsi` rank is where long
    signals do worst. The pair book waits.

15. **Control A on the slot books — DONE (D348).** Four of seven, the
    load-bearing one held: all three candidate cells above 200 of 200 time
    rotations on every statistic. The slot book's long leg is timing; the
    rank rotation is the harder null on a slot book. The prep is cached and
    the load chain memoised (164–460 s and 5–7.5 GB a process → 0.2 s, 1 GB).
16. **The short-signal controls — DONE (D349).** Three of eight; no short
    signal is real: timing +26 to +67 against its own names, cohort rise
    56–70, mean negative before cost, mirrors positive. D347's top-bucket base
    rate corrected.

17. **The long-timing screen — DONE (D350).** One of eight as pre-registered,
    every failure the one D351 predicts; under the corrected control `rev_5`/E1,
    `gap_reversal`/E1 and `cs_spread`/E2 beat A′, B and C; none pays PUB.
18. **The erratum study — DONE (D351).** D347's and D349's control A was
    trading the excluded tail; D347's headline withdrawn, D349's verdict kept,
    D348's mechanism withdrawn. Every null now asserts its events are eligible.

19. **The short-timing screen — DONE (D352).** Two of eight; no short event at
    any extreme is above random direction; the slot book's short leg is not an
    event. The pair book has one side.
20. **`rev_5`'s full record — DONE (D353).** Seven of nine; real at 200 draws on
    every control, −18.6 PUB / +17.9 PB; a two-slot cap on it is a sample of its
    worst events; the kernel's capital series is hedged now.
21. **The pair book — DONE (D354), closed on this construction.** Two of seven;
    the basket of the opposite extreme costs the pair what the trigger earns
    and a random gate name hedges as well.

22. **The exit swap — DONE (D355).** Zero of seven; the target fires first on a
    refilled slot book and the invalidation exit gives back gross on both
    cells. The target stays.
23. **The two-book blend — DONE (D356).** Four of six; Sharpe 0.442 above both
    parents and both paired nulls on a correlation of 0.21; the blend is the
    construction the holdout read is spent on.
24. **The flat-by-default sleeve — DONE (D358), and it is never flat.** Four
    of eight; every cell deployed on 100% of bars; the hedged alpha +1.1 to
    +2.9 bp/bar against the names' round trip of 1.6 to 2.0; `rev_5` 10% and
    `hist_L` 2% above both nulls and negative under PUB. The series are written.
25. **The loser-cohort rally short — DONE (D359), the premise failed.** Two of
    nine; the bottom momentum decile drifts up on the floored universe; the
    spike inside it is inside every control; the short side has no drifting
    pool here. The mirror (winners' dip, long) is +68.6 / +160 a trade beside,
    without nulls.
26. **The news-gap short — DONE (D360), zero of nine.** A volume gap down
    reverses (the name beats its own random days by 6 to 33 bp), the volume
    gap up reverses too, the names are ordinary and there is nothing to earn.
    The short side closes on tape signals: a regime gate or outside data.
    *(Amended: not a closure — R15.)*
27. **The regime-gated short — DONE (D361), two of eight.** The 63-day gate
    forecasts a rebound (+96 bp per 20 bars in the loser cohort), the gated
    loser rally fails every control, and the gap-up fade below the 200-day
    mean is +42.3 gross a trade above all four controls on one cell of four.
    Its own record, the neighbours (100/150-bar means, the 5% gap), the
    loser cohort as a post-drawdown LONG, and a volatility gate are listed
    untested; the principal decides.
28. **The sink filter — DONE (D362), eight of ten.** Two sinks (below the
    volume history; calm market) lift the gated fade to +61.7 a trade above
    a random and a name-matched removal; five sinks to +83.6 but inside the
    flag rotation; sizing per hit t 3.9. With the calm-market sink on, the
    gate is inside its own rotation. Next cell listed: the calm-market
    condition alone, no 200-day gate, against the same rotation.
29. **The cost lines — DONE (D363), two of eight.** The entry-day spread
    moves the round trip 3 bp; the per-trade convention raises it a fifth
    over the ledger median; the fade is a 100 bp question of order placement
    (crossing −48, one side +3, auction +55) that daily bars cannot answer.
    What can: D336's quoted spreads (on hold) for the level; fills or
    intraday quotes on names like these for the auction. Sizing does not
    rescue the net.
30. **The execution measurements and instruments — DONE (D336 addendum,
    D364).** D336 re-verified offline and handed over, still unrun, still
    the principal's one command. D364 measured auction participation: the
    order is 2.5% of the opening minute, not 0.04% of the day, and the
    widest quintile is the thinnest. A daily watchlist reproduces the
    ledger on eight dates and prices what the live eligibility rule cannot
    know (one A2 event in twenty). A fill log and a slippage tool wait on
    the principal's own orders. Databento for equities is a $199/mo
    subscription question, not a data purchase: its free tier reaches 6 of
    3,028 trades.

**Next, in this order:**

0. **The winners'-dip long, pre-registered** — the bottom decile of `rev_5` is
   D353's trigger; D359's mirror restricts a fresh dip to the top decile of
   12-month momentum and it is +160 a trade at cap 40, +83 net PUB, on 3,932
   trades, with no null run. One pre-registration: the four cells' mirrors,
   A′, B, the cohort-matched B_c and C, both exits, the four groups with the
   top trade named, the deployed base. This is the three-layer design's long
   entry with momentum as the ranking, and it is the first per-trade number in
   the record that clears the published round trip by more than its own size.

1. **D357 — the out-of-sample read**, pre-registered, runner built and proven
   on the mining fixture to 0.0, the holdout's caches built by a dry stage that
   reads no return, the EDGAR pull for its 803 names' filings running. The
   construction is frozen in the addendum: the 50/50 blend of `rsi` k=40 and
   `hist_L` k=40 on the target exit, hurdles gating the blend, parents beside.
   **It runs once, on the principal's word, after the pull lands.** Whichever
   way it goes, it is the programme's first holdout read.
2. **`hist_L` k=40's candidate record** — owed regardless of the read: four
   groups, the top trade with liquidity, both nulls (run), multiplicity 92; its
   short leg is a cohort premium and the book is its long leg.
3. **D336's quoted spreads** — the principal's pull; the cost line every net
   number in this document is measured on.
4. **The time-gated sleeve** — D358 says a cross-sectional trigger is always
   on, so a flat-by-default sleeve is the trigger behind a *time-series* gate.
   The gate is the principal's era detector; the record's part is the series
   D358 wrote and one pre-registration that names a gate the allocator would
   actually use (the floored market's trailing return, or its vol) and
   predicts the deployed net conditional on it, with the gate's own null
   (rotate the gate in time, keep the trigger). Not the trigger's rarity
   again, at any p.
5. **The hedge priced as itself.** D345's cost convention charges the market
   hedge at the single name's spread (four crossings); the names' own round
   trip halves the cost line and moves `hist_L` 2% to +0.90 PUB. One line in
   the costing, stated per record, once D336 fixes the names' spread.
4. **The `rsi` + `retrace_leg` blend** as a portfolio of two books (not a
   composite): their left tails share two names of twelve; one cell, one
   prediction on the blend's Sharpe against each parent's. Lower priority
   after D346: `retrace_leg` is −1.18 at k=40.
5. **Re-base the two stale references** — `d300_width.json` and D331's cells —
   under the bounded panel, old files kept beside (D337 §9–10).
6. **Opportunity cost, measured** (FINDINGS §10). Its sign is now visible on
   both candidates: `rsi` is +3.52 a bar on the variant lens and **−4.8 a trade
   on the invariant one, both legs negative** — the book IS the slot cap.
   Pre-register: hold the slot count fixed and vary the refill pool, or the
   reverse.
7. **The mixed convention** — rebalanced long, constant-shares short — only if
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
16. **"Stops, displacement, idle conditions, the ladder: dead."** *(§2, every
    version since D295)* Dead in a book that refills behind every exit. D345's
    event book, with no refill, found the target exit costing 185 bp a trade
    against a signal-invalidation exit. **A closure is a fact about the
    construction it was measured on**, the same lesson as D344's 1/k.
17. **D345 calibrated a threshold entry to the slot book's exposure and
    scored an unbalanced book on an unhedged series.** Both were design
    choices made in the pre-registration without asking what the construction
    would do with them; both were wrong in ways the first run showed. A
    pre-registration protects against reading; it does not protect against a
    design that answers the wrong question.
18. **Every per-trade "long leg pays" in this document was measured against
    the wrong null.** The slot books' rotation null rotates *names within the
    gate on the same day*; D347's control B is that null and the long signals
    beat it. The per-name *time* rotation — the same names, random dates — is
    the control that carries cohort drift, and no slot cell has faced it. D290
    had it (its "rotation" null) and the programme dropped it when it moved to
    the gate-rotation family at D300. **A null that rotates names is not a null
    that rotates time, and cohort drift only shows against the second.**
19. **Item 18 was too wide, and D347 §10's "it may take them" was a
    prediction dressed as a scope claim.** D348 ran the time rotation on the
    slot books and every cell is above every draw; the slot book's long leg
    is timing, and the time rotation turned out to be the *easier* null on a
    slot book because the rank rotation keeps the day. Cohort drift was a
    property of the event definition D347 tested — a decile entry on any of
    ~1,500 names — not of a depth-2 selection. **A control's finding belongs
    to the construction it was measured on, exactly as a closure does (item
    16).** The rule in item 18 stands — both nulls are carried — but the
    binding one on a slot book is the rank rotation.
20. **D347's `bucket_of` digitised an undefined `rsi` percentile into the top
    bucket**, so its top-bucket base rate (−31 bp) was names with no rank —
    961,819 name-bars, nearly all off the warm base — and its control-B pool
    for that bucket drew from them. The top 2% by `rsi` earns +11 long. D347's
    events sat in the bottom buckets, so its verdict stands; the sentence
    "high-`rsi` names lose it" holds for the 90th–98th percentiles only. **A
    `digitize` on a grid with NaNs needs the NaNs masked first**; D349 asserts
    it.
21. **The load chain was the memory.** D347 §8 read six concurrent processes
    taking 50 minutes to load as "memory, not GIL" and left it there. The
    cause was 190 identical `_load` calls with no memoisation: every process
    re-executed `d285_spread_estimate.py` 151 times and held 5–7.5 GB before
    building anything. Five such processes paged the machine to a standstill
    twice on D348's first launch. `memo_load.py` executes each script once
    (0.2 s, ~1 GB) and was verified bit-identical on every cached array and on
    D348's identity check. **Profile the import before blaming the data.**
22. **Items 18 and 19 were both written on a broken null.** D347's control A
    rotated events within every priced bar while the observed events lived on
    the floored universe; 8–13% of rotated events landed on the names' sub-$5
    and illiquid spells at +226 to +318 bp per forty bars, and "cohort drift"
    was that. Item 19's explanation of why D348 disagreed with D347 — "a
    control's finding belongs to its construction" — was true as a rule and
    wrong as applied: the constructions did not disagree; one null did not
    respect the universe. **A null centred at +45 to +71 over a base rate of
    +1.7 was the thing to explain first, and the check took one line on the
    cached grid.** This document wrote a mechanism, a scope claim and a memory
    rule on it across three records before anyone ran that line.
23. **Every null must live in the universe the strategy trades.** Rotation,
    permutation, replacement: assert `null_events ⊆ elig` with the same mask
    the observed events satisfy, and report the share that would not have been.
    D347's [A] checked counts and the hedge; it never checked eligibility. From
    D351 every event-lens runner asserts it, and D350 prints both controls in
    every table so the letter of a pre-registered Q1 cannot close a real signal
    on a defective control.
24. **A self-test that cannot fail is worse than none, again.** D354's runner
    first drew its random-direction null as antithetic sign pairs so that the
    control's mean was zero by construction and the [C] check always passed.
    Reverted to iid before any stage ran; the check now can fail by seed and
    the negative control (it must fail on the unflipped ledger) is kept. The
    rule is in CLAUDE.md and an agent still wrote around it; the review caught
    it, not the assertion.
25. **A slot cap small against the event count is a sample of the signal's
    most extreme events, not the signal.** D353's two-slot book on 72,677
    events admitted 161 entries in sixteen years, most extreme first, and lost
    while the invariant signal cleared every control. Any capped book on an
    event signal must be read against its skipped share, and the K grid must
    be declared before the run.
26. **Two pre-registered predictions were identities.** D355's Q4 ("gross
    rises by more than cost rises") restates Q1 because cost is gross minus
    net; D356's Q6 ("the blend beats the arithmetic") cannot hold because a
    linear blend's Sharpe *is* the arithmetic with the measured correlation.
    Both were written by the same hand on the same day as the constructions
    they describe. **A prediction must be checkable against something the
    construction does not define**; write each one out in the quantities the
    runner computes before committing it.
27. **The event lens's exit finding was carried to the slot book on
    mechanism alone.** D345 and D353 showed the invalidation exit beating the
    cap on an event book; STACK §6 then listed the swap as "the cheapest thing
    in the queue that could move a net number by more than the spread". On a
    refilled slot book the target already fires first, and the swap cost both
    cells. Item 16's rule again: a closure or an opening is a fact about the
    construction it was measured on.
28. **An exposure prediction was written without dividing the event count by
    the bar count.** D358's Q4 said the 2% cells would be deployed on fewer
    than half the bars; D350's own file held 16,509 events on 3,185 bars — five
    a bar — and a 40-bar hold makes that 120 open positions, every bar. The
    division took ten seconds and was not done. Item 26's rule extends: before
    committing a prediction, compute it from what the record already holds;
    if the record fixes it, it is not a prediction. And the same day a [C]
    check was pre-registered at 2 SE on an iid null, which fails one cell in
    twenty on the seed — weakened to 3 SE in the runner and recorded (item 24).
29. **A pool reasoned from the literature was not a pool on this universe.**
    D359 argued that 12-month losers drift down and shorted their rallies; the
    floored universe's loser decile drifts up, because the floor removes the
    names whose fall the literature measures. The premise was pre-registered
    as its own stage and it caught this before the timing result was read,
    which is the process working — but the argument in §0 of that record
    could have been checked against D339's census (the tail the floor removed
    was where every short's top trade lived) before it was written. A pool
    must be measured under the programme's own floor; the literature's pools
    are unfloored.
30. **An exception to the record's own finding was argued from the
    literature, and the finding held.** D347, D350 and D358 say a sharp fall
    in a name that is not beaten down bounces. D360 argued that a *gap* on
    volume is informational and would continue instead, and pre-registered
    nine predictions on it; all nine failed, and the bounce after a volume gap
    is larger than after a drift. Two records in a row (item 29, this) reasoned
    a short from outside the record and were answered by what the record
    already said. **When a proposed signal contradicts a finding the record
    holds at 200 draws, the pre-registration must say why this case is
    exempt in the record's own quantities, and the premise stage must test
    that exemption first.** Also from D360: the same-day same-bucket control
    keeps 21% of clustered events for want of a pool; on event signals that
    cluster in time, B's p95 is a weak bar and A′ and C carry the verdict.
31. **An era split was read as a forecastable state.** D359 reported the
    loser cohort falling in era 1 and the down-years and the rally short
    paying there, and D361 built a gate on it. A year's average contains the
    fall and the rebound; the gate that fires on the fall is also on for the
    rebound, and on this universe the rebound is larger (+96 bp per 20 bars
    in the cohort, market +188 against +80). **A split by era or by year is
    a description of the past; a gate is a forecast, and its premise is the
    correlation of its level with the target over the next horizon, on
    non-overlapping blocks.** D361 pre-registered that number as Q0 and it
    came out with the opposite sign, which is the process working; the
    reasoning in D361 §0 that motivated the study should have asked for the
    number before the design was written.
32. **A pre-registration quoted screen numbers from one threshold set and
    fixed another.** D362 §0 gave +77 on 2,641 and +87 on 1,654 for the
    row-drop arms, from the export screen's full-sample quintiles, and then
    fixed the era-1 thresholds in §1, under which the same arms are +61 on
    3,028 and +86 on 1,832. No prediction depended on the §0 figures and the
    §4 check reproduced, but a reader comparing §0 to the result would find a
    16 bp gap with no explanation. **Every number a pre-registration quotes
    must be computed under the parameters the record fixes**, or labelled as
    coming from elsewhere.
33. **Every per-trade net since D285 charged the ledger's MEDIAN
    half-spread to every trade.** That is fine on a book whose spread is
    symmetric around its median and wrong on one whose gross sits in its
    widest names: on D362's fade the per-trade charge is 108 bp a round trip
    under PUB against the median's 89, and 125 under PB against 39 — PB's
    single-pair estimate is zero on 43% of bars and has a fat right tail, so
    it was never a per-trade charge and the median hid that. D363 carries
    both conventions; **a per-trade net must charge each trade its own
    spread at its own bars, and print the ledger median beside it for
    comparability.** Earlier per-trade nets (D285 onward) are median-based
    and read as upper bounds on any spread-concentrated ledger.

The common thread has not changed: reading a non-result as a null result,
ranking cells off a published table instead of measuring the difference, and
filing a mechanism before checking the statistic orders the outcome.
