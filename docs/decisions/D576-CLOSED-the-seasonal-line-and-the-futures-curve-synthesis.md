# D576 — the **seasonal calendar-spread line** on the commodity curve is CLOSED by the principal, 2026-09-20; and the synthesis of the futures-curve programme, D555 → D575: how the reasoning moved, what each number said, and what it cost to learn

*Closed on the principal's word after D575 ("Close the seasonal line and write the synthesis
record"). Nothing admitted (R15). Part A states what is closed, on what evidence, what it does
not close and what survives as instruments, in D563's form. Part B is the synthesis the
programme owes itself after twenty-one decision numbers in two days: the thought process at
each fork, the data point that turned it, and the errors made and corrected in writing. It is
written to be read by someone who was not here.*

---

# Part A — the closure

## 1. What is closed

**The seasonal calendar-spread line**: every flat-by-default construction that holds a nearby
commodity spread through a calendar window named by a storage, harvest, supply or hedging
mechanism — the NG withdrawal-season spread (D565, D566), the corn post-harvest carry narrowing
(D568), the soybean harvest spread on the F/H pair (D570), the placement-profile constructions
on corn, wheat, soybean oil, soybean meal (D571), live cattle and lean hogs (D575), and their
gated, rolled and de-meaned variants — on these fixtures, on any window. With it the avatar
programme that produced them (the per-root plan of D564 §3: NG, the grains, livestock, then
heating oil and crude), including the two roots not yet designed, whose constructions would be
the same object on the same strip.

Operationally: no new pre-registration of a seasonal spread on the settlement strip; the
`COMPONENTS_PROP.md` rows stand as scored; the five seen cells in §3 are parked and not built.
The NG 2024+ slice is spent (D566); the other roots' 2024+ slices are unspent for this line and
stay so, because nothing on the line can be confirmed with two windows.

## 2. The evidence, in one table

| construction | in sample 2016–2023 | its own null | the control | what decided it |
|---|---:|---|---|---|
| **NG spread**, Nov → Mar, short T1 / long T2 (D565) | +0.69 / +1.03 | placement rank 0.942, p95 +0.70 | beat the always-on 3 : 1 per day | **forward −1.07** on 13 months (D566): REMOVED |
| **corn post-harvest**, Dec → Feb, long H / short K (D568) | +0.60 / +1.00 | rank 0.848 | **always-on earned more per day** (1.11 vs 0.90 bp); December lost 10 of 13 | the window sampled a year-round drift |
| **soybeans F/H**, Sep → Nov, short F / long H (D570) | +0.40 / +0.54 | **third of its own twelve placements** (Jul → Sep on X/F +1.24) | beat the always-on (−1.15 bp) | the declared window was two months late; the object was chosen on the wrong window of a seen table |
| **cross-root placements** from the soybean profile (D571) | corn m6 +0.75, meal m7 +0.26; wheat flat; oil m7 −0.69 | prediction held 2 of 4, chance level | controls ≤ 0 on all four | profiles are root-specific |
| **livestock placements** from the supply calendar (D575) | hogs' predicted set all negative; cattle best m2 +0.63 outside both avatars' sets | neither declared construction best of twelve | hogs −2.7 bp a day, cattle flat | falsified on hogs; two avatars refuted on cattle |

**The reading.** Every window that looked real at Stage 0 failed one of four tests once it was
pre-registered: the always-on control per positioned day (corn), the construction's own
placement null (soybeans), a mechanism prediction made before the read (cross-root, livestock),
or the forward slice (NG). None failed for lack of a number; each in-sample figure was positive
and several cleared a rotation null. What every agricultural root shares is a sign, not a
schedule: **the always-on short nearby spread loses** — corn −0.70, soybeans −1.15, oil −0.80,
meal −1.61, hogs −2.72 bp a day; cattle flat — because the nearby strengthens against the
deferred on average. That is carry, and the carry line is closed (D563).

## 3. What this record does not close

- **The five seen cells** — corn U/Z June → August (13 of 13, +0.75 / +1.04), soybeans X/F July →
  September (+1.24), meal V/Z September (hit 0.85), hogs J/K December → February (+0.46), cattle
  M/Q February → April (+0.63 / +0.84). Each was found by a null or a control, none was
  predicted, each is seen for every placement of its construction, and each has two forward
  windows as its only test. They are parked as the one-shots they are; a joint forward read of
  all five as one pre-registered family is the only honest use of them, and it is not asked for.
- **The fixtures and the machinery**: the settlement strip, the WASDE stocks-to-use fixture
  (D567), the extended COT fixture (D572), the survival-pair series, the placement-profile
  runner, the always-on control and the placement null — all stay, and any later study of a
  commodity curve reads them first.

## 4. What survives as instruments

1. **A Stage 0 window carries the same construction held always-on, scored per positioned day**
   (D568). A window that does not beat it per day is a drift sampled, not a schedule.
2. **The construction's own placement null decides, not a schedule null on a cousin** (D570):
   the schedule can sit at the 99th percentile while the construction is third of twelve.
3. **Predict the placement and its sign from the mechanism before reading, and name the
   competing avatar with a disjoint prediction** (D571, D575). A profile's best cell that no
   avatar named is a null result, not a lead.
4. **With one observation a year, the leave-one-year-out residual is a constant** (D567); the
   per-year table and the placement null carry the seasonal question.
5. **The pair must survive the window** (D567): T1 is the first delivery strictly after the
   window's last month; a rule-rolled pair diverges from it exactly on the roll month.
6. **Choose between seen objects on the primary window** (D570).
7. **Two forward windows refute a large claim and confirm nothing** (D566, D569 §3).

---

# Part B — the synthesis of the futures-curve programme, D555 → D575

## 5. The question, and why it was asked this way

The prop account's geometry needs a book-level Sharpe near 1.5–2, and no single construction
here has come within half of that; the ledger's design is five components at net 0.4–0.6 with
pairwise correlation under 0.3. On 2026-09-19 the ledger held one admitted arm (the MACD day
session on NQ) with its 2024+ slice already spent, so the search for a second component had to
be on instruments and clocks the arm does not share. The deposit folder offered the obvious
place to look: five published futures strategies with decades of literature, on 36 CME roots
whose hourly, curve and settlement fixtures had just been built and gated. The deposit's own
framing was explicit — "five expressions of two robust mechanisms, trend and carry, is what
actually exists" — and it parked hedging pressure, basis-momentum, skewness and value as
second-pass. The programme took the deposit at its word, scored the five, then the parked
ones, then followed the one that passed into a per-root design. Every step below was a
decision taken because of the number before it.

## 6. How the reasoning moved, step by step

**Step 1 — calibrate the harness before believing anything (D555).** Time-series momentum was
scored first because it has a published monthly factor to reproduce. The harness reproduced
AQR's series at ρ 0.815 in sample and 0.733 forward, which is what made every later number on
these fixtures trustworthy. The result itself was small: **+0.30 gross / +0.43 Sortino on
2016–2023, at the 78th percentile** of its rotation null (p95 +0.95), ten cells with the family
best +0.34 at the family null's median. Two things learned here shaped everything after. First,
the rotation null of a slow signal must **purge a lookback at both ends** — offsets within 252
sessions of a cycle end are look-ahead on one side and a stale copy of the signal on the other;
D555 stored the offset profile so the purge could be seen. Second, **the null's median is not
zero**: a persistent-sign book rotated through time keeps its tilt, and the median came out
+0.11 (+0.18 forward). That observation is the reason the name-randomised null exists in every
later runner.

**Step 2 — carry timing, and the strip fixture (D556).** The sign of the front–next basis on the
same 36 roots read **−0.20 / −0.28**. The study's lasting product was the settlement-strip
fixture (every listed month, every session, gated against the curve table), and one lesson
that recurred five times afterwards: a **one-contract dollar book across roots is a bet on the
largest dollar σ** — carry's +0.20 dollar Sharpe was one contract of palladium.

**Step 3 — the sharpening question before the forward read (D561).** The principal asked whether
trend's mechanism could be sharpened rather than accepted at +0.30. Three levers were
pre-registered: power (does a 13-year window narrow the null?), sizing (does a leverage cap
help?), role (is it a hedge for equities or for carry?). Each answered no with a number. The
13-year null's sd was **0.51 against a predicted 0.43** — width comes from regimes, not sessions,
so a longer window does not buy power on a persistent book. Every cap lowered the Sharpe
(+0.07 / +0.20 / +0.25 / +0.27 against +0.30) and the worst day was the same macro session at
every cap. And the role test introduced the instrument that decided the most later: **ρ is a
body statistic**; scored on the base's worst 5 % of days, trend gave +0.26 σ to ES (rank 0.94,
bar 0.95) and **−0.56 σ to carry, below all 1,562 rotations**, at a body ρ of 0.18. Trend is
carry's tail, not its hedge.

**Step 4 — spend the slice, then close (D562, D563).** With sharpening exhausted the principal
settled the forward read: trend **+0.51 / +0.71, rank 0.69**, the whole P&L in 2026; on ES's
worst forward days **−1.29 σ, rank 0.05** — the in-sample hedge inverted. Carry forward
**−0.56**. The principal closed both lines. The reasoning recorded: a real, small, rare effect
with no vehicle at the account's size and a role that flips is not a component.

**Step 5 — the three sorts in parallel (D557–D559).** Term structure, 12-1 momentum and the
double sort share inputs and are independent of each other, so they ran as three agents with a
pinned construction. All three were negative in equal weight (**−0.21, −0.26, −0.11**) and all
three had a positive dollar number that was **one palladium contract** (D557: +$200k of a +$176k
total). The count floor on a short window turned out to be a calendar filter (D558/D559), and
the C-d sub-books read −0.22 to +0.06. Reasoning at this point: the deposit's five were done
and two lines closed; the parked premia were next in the deposit's own order of confidence.

**Step 6 — basis-momentum passes, and only under an amendment (D564).** Boons–Prado's
first-nearby-minus-second-nearby momentum, High4/Low4 on 17 commodities. As pre-registered it
read **+0.42 at rank 0.80** with 24 flat month-ends. Inspection found two calendar defects —
2020-06-30 is a truncated archive day (237 of ~900 settlements) and 2021-05-31 is Memorial Day
sitting in the session calendar — each of which voided twelve month-ends of a twelve-month
signal for every root. The amendment (read the last finite settlement within five sessions of
the month-end, D556's own rule) was recorded as an amendment with the as-pre-registered result
kept beside it: **+0.69 / +0.99, ranks 0.972 / 0.971 / 0.975** in the time rotation, the family
maximum and the name-randomised null. The first pass in the programme. But the decomposition,
demanded by D556's lesson, said what carried it: two roots reached half the P&L, **natural gas
was in the short leg 81 of 83 months**, and the nine non-seasonal roots read −0.09 standalone.
The reasoning that followed was the principal's: if the premium sits in seasonal roots, then
the constrained party on each root is seasonal and specific, and a construction built to that
party, flat by default, should do better than a sort that happens to catch it. That is the
avatar programme, and it was designed to avoid overfitting by having a different mechanism and
a different constrained party per root.

**Step 7 — natural gas: the schedule is real and the forward slice refuses it (D565, D566).** NG's
Stage 0 found the storage state the deposit named — working gas against its five-year band —
predicts nothing about the next month of the curve once the calendar is removed (residual
Spearman −0.02, year-block p 0.7). The calendar itself is where the curve moves, so the avatar
became the obligated winter buyer and the construction a short T1 / long T2 spread through the
EIA withdrawal season, one micro a leg. In sample: **+0.69 / +1.03 at the 94.2nd percentile of
its placement null — 0.007 below the p95** — beating the always-on control three to one per
day, **net +0.62 at σ $24 a day, skew +1.98**, every ledger bar cleared. It entered as
PROVISIONAL under D468's rule, and it entered as #2 in error: K8 had been closed and the MACD
arm admitted as #2 a week earlier, which a reading of the ledger to its foot would have shown.
Corrected the same day to #3. The avatar test failed on the way in (commercial long share rose
into the formation months in 7 of 13 years). The joint forward read on the principal's word:
**−1.07 gross on thirteen positioned months, 5 of 13 positive, worst −9.72 %**, and the two
forward seasons were formed with the front **8 % and 13 % below the second** — the opposite
curve state to every in-sample season. Removed. The assembled book with the MACD arm was the
arm minus 0.06 at one pair and −0.33 at twenty, and hurdle P failed structurally on P2 (a spread
held through the month crosses every permitted venue's flatten time). Two lessons: a formation-
basis premise belongs in the next Stage 0 as a test, and an overnight-held spread cannot be a
prop component whatever its Sharpe.

**Step 8 — the grains, designed before reading (D567).** The merchant-at-harvest avatar for corn,
soybeans and wheat, with WASDE stocks-to-use as the state variable, was written with its
predictions and falsifiers before any outcome was read; the WASDE fixture was built from raw
monthly files, a 2010–2015 archive and a 2016–2020 gap closed in a browser session after the
provider's zip failed a virus scan. Two design corrections were made before reading: some
monthly files write the release date month/day/year, and the design's three-month pairs expire
inside the window, so the survival rule was written (T1 strictly after the window's last
month). One control was recognised as vacuous — with one observation a year, the leave-one-
year-out residual subtracts a constant — and the record said so. What the read found: **corn's
harvest carry is priced by August** (the Z/H spread narrows in 9 of 13; the curve is at full
carry at formation in 1 year of 13; stocks-to-use ρ −0.09); **soybeans clear by price but the
state sign is inverted** (the F/H spread widens most when stocks are *tight*, ρ +0.65, p 0.02 —
a pre-harvest inverse collapsing, the short-bought crusher the constrained party, re-derived
from the data); wheat at full carry at harvest in 8 of 13. What survived: the corn post-harvest
narrowing, 9 of 12, t +2.6, monotone in stocks-to-use, with its window and direction declared
in the design.

**Step 9 — the corn window is a drift (D568).** Pre-registered on the design's own terms: **+0.60
/ +1.00, rank 0.848**, net +0.43 at one contract. The unseen parts decided it. **The always-on
long spread earned more per positioned day than the window (1.11 vs 0.90 bp)**: the corn front
gains on its deferred all year, **April +6.4 and June +7.0 bp a day**, July −5.8; **December,
where the mechanism put the merchant's selling, loses 10 of 13**; the window's return is
February. The real-time stocks-to-use gate opened four windows including both losers. The
merchant avatar had now failed on corn in both halves of its year. The lesson written into
memory that day: a Stage 0 window carries the same construction held always-on, per positioned
day, or it cannot tell a schedule from a drift.

**Step 10 — soybeans, addendum first, then the pre-registration (D569, D570).** Because of step
9, the soybean thread was not pre-registered from its Stage 0 table; an addendum was designed
to put the missing tests on it. The schedule held where corn's failed: **+0.42 bp a positioned
day against −1.15 always-on** (the short loses every month but September and November, most
in June–August), **placement rank 0.972 exact**, and the one declared real-time stocks-to-use
cut selected — **four open windows, all four paid, +0.71 % against +0.16 %**. Against it: the
curve was inverted at formation in two years only, the commercial net short *fell* through
harvest in 8 of 13 with the spread widening most when it fell least (ρ +0.57, the predicted
sign reversed), and **2012 was half the thirteen-year total**. Under the addendum's own rule
the schedule could be pre-registered as seen, on the F/H pair, and the principal took it. The
pre-registration ran its own twelve-placement null, and that null decided it: **the F/H
harvest window was third of twelve; the same construction formed at the end of June on X/F
earned +1.24 / +1.97 against +0.40 / +0.54**. And the rolled cousin beat the F/H pair per day in
sample — which the seen thirteen-year table had already shown on the 2016–2023 subset; the
pair's lead was 2012 and 2013, outside the primary window. I had chosen the object on the
wrong window of a table in front of me. Recorded as the lesson, with the pre-harvest widening
recognised as starting in July: corn's D568 shape with the season reversed.

**Step 11 — does the profile transfer? (D571).** The honest test of "a pre-harvest short spread
pays into harvest" was on roots whose profiles were unseen, with the placement predicted from
the soybean profile before reading. Corn's best placement landed in its set (m6) and meal's
(m7); **wheat's profile is flat and oil's July placement is the worst of its twelve**, the same
crop with the opposite sign. Two of four is what one-in-six and one-in-four chances deliver;
the profile correlations with soybeans were +0.27, −0.39, −0.14, +0.01. Not supported. What
corn's profile actually held was a different pair — **the old-crop September against the
new-crop December, June → August, 13 of 13 at +2.3 % a window** — D567's weather-premium decay
seen from the spread side, unpredicted, a null cell. The one prediction that held on all four
roots was the sign of the always-on control. A December-label erratum in the shared helper was
found and fixed here (labels only; every number asserted unchanged).

**Step 12 — hedging pressure, the deposit's last premium (D572, D573).** The COT fixture lacked
six of the seventeen roots; the fetcher resolved them on the live API and refused two patterns
that matched only spread contracts (heating oil's outright is `NY HARBOR ULSD`; gasoline's
`GASOLINE RBOB`, among ten matches). A positioning-only probe before the pre-registration found
the thing that shaped it: **53 % of the cross-sectional variance of hedgers' hedging pressure is
the root's own long-run level** — the metals permanently low, natural gas and wheat permanently
high — so the published sort would be a static tilt. The pre-registration therefore declared a
de-meaned cell, a name-randomised null, and a TILT verdict. The tilt prediction held at
71–98 %; **the tilt lost: −0.20 / −0.28, below its rotation median (rank 0.076) and at the 26th
percentile of the name randomisation**, short the energies through 2021–22 (heating oil −$138k),
long palladium the one winner (+$207k of a −$46k dollar total). The de-meaned cell was worse.
The release-date audit found 141 of 300 checked cells change under report-date keying — the
look-ahead the design existed to prevent.

**Step 13 — the one pass, forward (D574).** With the deposit's list scored end to end, the only
construction with an in-sample pass and an unread slice was basis-momentum, and the
pre-registration was written to predict the composition before the total. Harness first: the
in-sample book rebuilt on the full calendar equalled D564's artifact to 1e-9. Forward, 696
sessions: **+0.48 / +0.69, rank 0.73 and 0.80** in nulls whose 95th percentiles sit near +1.0
on a 33-month window — INSIDE. The amendment was inert (identical to every digit). And the
composition inverted: **the seasonal roots that made the in-sample result read −0.47 forward,
natural gas was long 59 % of the time and short never, the non-seasonal nine read +0.84,
heating oil was 86 % of the profit, March 2026 alone 13 %.** A transferred total with reversed
carriers is a rule that picks something every month and was lucky in sample about what.
Nothing entered, as declared before the number.

**Step 14 — the closing test (D575).** Livestock was the last unseen avatar. Each root's best
placement was predicted from its own supply calendar, cattle's feedlot placement-hedge avatar
named as a disjoint alternative, one construction declared a root. **Hogs falsified** — the
three predicted placements were the three most negative of twelve, the declared construction
−0.28 with a −17.2 % window in 2020. **Cattle outside both sets** — best February → April on M/Q,
+0.63 / +0.84, named by nothing. Neither declared construction best of twelve. The closing
clause the design carried fired: the seasonal line had no open construction, and the principal
closed it.

## 7. What the curve said, in one table

| line | what was scored | in sample | forward | disposition |
|---|---|---:|---:|---|
| time-series trend (D555, D561, D562) | MOP 12m sign, 36 roots | +0.30 / +0.43, rank 0.78 | +0.51 / +0.71, rank 0.69 | CLOSED (D563) |
| carry timing (D556, D562) | KMPV sign of basis | −0.20 / −0.28 | −0.56 / −0.82 | CLOSED (D563) |
| cross-sectional term structure (D557) | 17 roots, 6/5/6 | EW −0.21 | unread | not a candidate |
| cross-sectional 12-1 momentum (D558) | 17 roots | EW −0.26 | unread | not a candidate |
| double sort (D559) | 17 roots, 2 a side | EW −0.11 | unread | not a candidate |
| **basis-momentum (D564, D574)** | Boons–Prado H4/L4, 17 roots | as pre-registered +0.42 rank 0.80; **amended +0.69 / +0.99, rank 0.972 / 0.975** | **+0.48 / +0.69, INSIDE; composition inverted; HO 86 %** | spent; no entry |
| hedging pressure (D572, D573) | Basu–Miffre, 16 roots, COT legacy | −0.20 / −0.28, below the rotation median; **the tilt held 71–98 %** | unread | not a candidate |
| NG winter spread (D565, D566) | short T1 / long T2, Nov–Mar | +0.69 / +1.03, rank 0.942, PROVISIONAL #3 | **−1.07 / −1.29**, REMOVED | CLOSED (this record) |
| grains and livestock seasonal (D567–D571, D575) | seven roots, five Stage 0s, two pre-registrations | Part A §2 | unread | CLOSED (this record) |

**Three things the table says together.**

1. **No published commodity premium is a component here.** Five cross-sectional sorts on this
   universe are negative or inside their nulls, and in four of five the minimum-size dollar book's
   largest single line was one palladium contract. The one in-sample pass needed an amendment
   made after the read, was carried by two seasonal roots, and transferred a positive number with
   its carriers reversed. Trend is real, small, rare and has no vehicle at the account's size;
   carry timing is negative on both windows.
2. **Seasonal schedules on the curve are drifts, cousins of carry, or luck** — Part A.
3. **The instrument the account can hold is the problem as much as the signal.** The ledger's
   C-d bar (σ ≤ $500 a day at minimum size) removes eleven of the seventeen commodity roots from
   any one-contract book; every sub-book that clears it read −0.06 to +0.49 net; the two
   constructions that cleared C-a in sample (the NG spread at $24 a day, the gated soybean cell
   at four windows) were one micro and four observations. Nothing on the commodity curve has
   both a signal and a size.

## 8. What it cost, and what it bought

Two days, twenty-one decision numbers, nineteen studies, 1,858 unit tests green at every
commit that mattered. Two errors of judgement went into records and were corrected in writing:
the NG spread entered the ledger as #2 when #2 was the admitted MACD arm (D565, corrected the
same day; the lesson was to read a ledger to its foot), and the soybean object was chosen on the
long window of a seen table whose primary-window subset said otherwise (D570). Two process
faults: a result commit went out red on the Windows path-length gate because a chained command
committed regardless (D568; fixed in the next commit and never chained again), and the WASDE
fixture's span was misstated in D567 (the file held 195 releases to 2026-09, not 163 to 2023-12;
corrected in D568, with the runner filtering first). One erratum in shared code: December
delivery months were labelled a year late in the pair tables of D565's and D567's artifacts —
labels only, fixed in D571 and asserted inert by re-running.

What it bought is in Part A §4 and in the methods that now sit in every runner and were each
proven to raise on a deliberate break: the purged enumerated rotation with its offset profile
stored (D555); the name-randomised null with the p95's bootstrap SE, separating tilt from
timing (D564, D573); the worst-days overlay statistic beside every ρ (D561); the always-on
control per positioned day (D568); the construction's own placement null over every calendar
month (D570); the mechanism-derived placement prediction with a named competing avatar (D571,
D575); the survival rule for a windowed pair (D567); the release-date keying audit on
positioning (D573); the per-root dollar decomposition before any component line (D556); and the
composition prediction before any forward read (D574). And two committed public-domain fixtures
— WASDE stocks-to-use, point in time by release date, and the 34-symbol COT panel — that no
later study on these roots has to build.

## 9. Where the ledger stands, and where the search goes

The prop book is one arm, the MACD day-session arm on NQ (admitted 2026-09-13, its slice spent
in D503). The components ledger has three entries: K8 closed, the MACD arm admitted, the NG
spread removed. Nothing from the futures curve is entered, provisional or otherwise.

The search for a second component moves off the commodity curve. Two directions are open and
unscoped, and each comes to the principal before a slice is read: the day-session mechanism on
the index roots other than NQ, whose 2024+ slices that line has not read; and the positioning
fixture's financial families (dealer, asset manager, leveraged money) on the index and rates
futures, which D572 extended the commodity side of and no study has touched. Both are sessions,
not years, which is the sample the curve never gave.

**Spent slices, by line, at this record:** trend and carry (all 36 roots, D562); the NG spread
(D566); basis-momentum on the 17 commodity roots (D574); the NQ day session for the MACD arm
(D503); the overnight leg (K7). **Unspent:** every other line on every other root.
