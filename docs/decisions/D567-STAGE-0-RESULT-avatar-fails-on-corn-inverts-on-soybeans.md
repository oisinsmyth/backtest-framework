# D567 STAGE 0 RESULT — the merchant-at-harvest avatar **fails on corn and inverts on soybeans**: the corn harvest spread narrows (front gains in 9 of 13), the soybean harvest spread widens as designed (11 of 13, t −2.3) but **most when stocks are tight**, not full; what survives is the **post-harvest carry narrowing on corn** (9 of 12, monotone in stocks-to-use) and the **corn weather-premium decay** (9 of 13, −8.7 % in non-drought years, +29 % in the two drought years)

*2026-09-20. Design committed in D567 before this ran (`d557e52`, amended `7f9b3ac`). Diagnostic:
outcomes read on 2011 → 2023 only, thirteen harvests a root; no pre-registration produced; no
2024+ session read on any source. Runner `scripts/stage0_d567_grains_harvest.py`, output
`data/stage0_d567_grains.json`, 11 minutes (permutation tests). The derived state-variable
fixture `data/fixtures/wasde_grains_su.csv` — 978 (report, commodity, marketing-year) rows over
163 WASDE releases 2010-04-09 → 2023-12-08, stocks-to-use point-in-time by release date — is
committed (public domain).*

**Two corrections to the design, made before any outcome was read and recorded here.** (1) Some
monthly WASDE files carry the release date as month/day/year; the builder normalises it and
asserts the release sits in its report month. (2) The design's stated pairs for soybeans (X/F
over September → November) and wheat (N/U over June → August) cannot survive a three-month
window — the front expires mid-delivery-month — so the pair is chosen to survive it: the first
delivery strictly after the window's last month, T2 the next listed. That gives corn Z/H,
soybeans F/H and wheat U/Z over their harvest windows; the design's soybean pair is kept as a
declared two-month window ending before X expires; the weather window names the new-crop
contract explicitly (Z, X). **One control is vacuous here and the record says so:** the
leave-one-year-out residual, which decided NG's Stage 0, only subtracts a per-year constant when
each window yields one observation a year, so raw and residual correlations are the same. The
seasonal question in this design is carried by the per-year tables and, for anything built on
them, by a placement null in the runner.

---

## 1. The seven tests, per root and window

Spread = front return minus second return over the window (short the spread pays when negative).
S/U = stocks-to-use from the last WASDE released before formation, the new-crop `Proj.` year.
ρ is Spearman over the thirteen harvests, p by permutation.

| root · window · pair | **T1 calendar** spread mean · short pays · t | front mean · negative · t | **T2** S/U → spread ρ (p) | S/U terciles low / mid / high, spread | **T3** at full carry at formation | **T4** COT net short → spread ρ (p) |
|---|---|---|---|---|---|---|
| **ZC harvest**, Sep–Nov, Z/H | **+0.27 %** · **4 of 13** · +1.29 | −1.53 % · 7 of 13 · −0.57 | −0.09 (0.76) | +0.39 / +0.03 / +0.36 | 1 of 13 | +0.21 (0.49) |
| ZC weather, Jun–Aug, Z/H | −0.39 % · 10 of 13 · −1.26 | **−2.80 % · 9 of 13** · −0.51 | −0.32 (0.27) | −0.32 / −0.19 / −0.68 | 0 of 13 | −0.11 (0.72) |
| **ZC post-harvest**, Dec–Feb, H/K | **+0.74 % · front gains 9 of 12 · +2.57** | +4.61 % · 6 of 12 · +1.38 | **−0.43 (0.16)** | **+1.11 / +0.87 / +0.24** | 0 of 12 | +0.45 (0.15) |
| **ZS harvest**, Sep–Nov, F/H | **−0.50 % · 11 of 13 · −2.28** | −1.02 % · 8 of 13 · −0.33 | **+0.65 (0.02)** | **−1.05 / −0.22 / −0.10** | 2 of 13 | **−0.61 (0.03)** |
| ZS harvest, Sep–Oct, X/F (the design's pair) | −0.06 % · 8 of 13 · −0.41 | −1.49 % · 8 of 13 · −0.71 | +0.46 (0.12); S/U → front **+0.73 (0.005)** | −0.46 / +0.15 / +0.23 | 3 of 13 | −0.06 (0.85) |
| ZS weather, Jun–Aug, X/F | −0.09 % · 9 of 13 · −0.76 | +1.53 % · 7 of 13 · +0.36 | −0.14 (0.67) | +0.03 / −0.23 / −0.11 | 1 of 13 | +0.07 (0.82) |
| ZS post-harvest, Dec–Feb, H/K | +0.18 % · 7 of 12 · +0.75 | **+6.60 % · 8 of 12 · +2.04**; S/U → front **−0.68 (0.02)** | +0.08 (0.82) | −0.14 / +0.44 / +0.23 | 2 of 12 | −0.34 (0.28) |
| **ZW harvest**, Jun–Aug, U/Z | −0.30 % · 7 of 13 · −0.75 | **−5.58 % · 9 of 13** · −1.38 | −0.34 (0.27) | +0.14 / −0.19 / **−0.96** | **8 of 13** | +0.04 (0.90) |
| ZW post-harvest, Sep–Nov, Z/H | +0.46 % · 7 of 13 · +0.94 | −2.12 % · 8 of 13 · −0.77 | +0.13 (0.68) | +0.62 / −0.06 / +0.77 | 7 of 13 | +0.14 (0.64) |

**T5, the weather premium (corn):** the new-crop December contract fell in 9 of 13 Junes-to-Augusts,
**−8.65 % on average in the eleven non-drought years** and **+29.4 % in the two drought years**
(2012: the July WASDE cut production 12 %, the front rose 53 %; 2020: −6 %, +5.6 %). Soybeans: no
decay (7 of 13, mean +1.5 %, tails 2012 +38 %, 2023 +19 %).

**T6, the post-harvest carry:** the front gains against the deferred in 9 of 12 on corn (t +2.57),
7 of 12 on soybeans, 7 of 13 on wheat — predicted ≥ 7 of 13 on all three, and corn is the one
with a margin.

**T7, the reverse state (lowest stocks tercile):** corn harvest +0.39 % (flat-to-positive, as
predicted, but the high tercile is also positive); **soybeans −1.05 %, the most negative tercile,
the opposite of the prediction**; wheat +0.14 % as predicted.

## 2. What the tests say about the avatar

**Corn does not clear by price at harvest against the deferred.** The Z/H spread narrows over
September → November in 9 of 13 years; the carry that the merchant's full bins were supposed to
widen is already what it is at the end of August, and the curve is at full carry at formation in
one year of thirteen. The merchant's constraint is priced before the window opens, which is what
NG's storage state taught, seen from the other end of the season. Stocks-to-use has nothing to
say about it (ρ −0.09).

**Soybeans clear by price at harvest — and the state that drives it is the opposite of the
design's.** The F/H spread widens in 11 of 13 (t −2.3), but it widens most when stocks-to-use is
**lowest** (−1.05 % in the tight tercile against −0.10 % in the full one, ρ +0.65, p 0.02), and
the outright front falls most when stocks are tight (S/U → front +0.73 on the X/F pair). That is
not bins filling. It is a **pre-harvest inverse collapsing**: with old-crop stocks tight, the
crusher and exporter bid the nearby up against the deferred through the summer, and the new crop
arriving releases it. The constrained party is the short-bought buyer before harvest, not the
merchant after it — a different avatar, seen in the data, and therefore to be written as seen.
The COT commercial net short at formation predicts the spread with the design's sign (ρ −0.61,
p 0.03), so the merchant's selling is in the price; it is the buyer's earlier bid that sets the
size.

**Wheat is the only root at full carry at harvest formation** (8 of 13) and its harvest spread
widens further only in the full-stocks tercile (−0.96 %, n 4); the outright falls 5.6 % on
average, 9 of 13, with 2012's +32 % as the tail. The design predicted wheat the weakest; on the
spread it is, on the outright it is the largest.

**What survives, with thirteen observations each:**

1. **Corn post-harvest carry narrowing**, December → February, long the front against the
   deferred: 9 of 12, t +2.6, and monotone in stocks-to-use in the mechanism's direction — tight
   stocks, the front gains most (+1.11 %); full stocks, least (+0.24 %). ρ −0.43 is not
   significant at n 12; the monotone terciles are the reason to carry it forward.
2. **Corn weather-premium decay**, June → August, short the new-crop December contract: 9 of 13,
   −8.7 % in non-drought years, with a +29 % tail in the two drought years the July WASDE
   production cut identifies after the fact. An outright with a known fat tail on the wrong
   side, for a root whose one-contract σ is $376 a day: not a prop candidate, a personal-book
   question of tail sizing.
3. **Soybean harvest spread widening**, September → November, short F against H: 11 of 13,
   t −2.3, strongest when stocks-to-use is tight — an avatar re-derived from the data.

## 3. What follows, and what this record does not license

A pre-registration on (1) is the honest next step: the constraint (paid storage narrowing the
carry as bins empty) was in the design, the direction and window were declared, and the
stocks-to-use gate was declared as a state variable with a predicted sign that the terciles
match. Its confirmation is ZC's unread 2024+ slice. (3) is stronger on the number and weaker on
provenance — its mechanism was re-derived after the read — and would be pre-registered as seen,
with ZS's 2024+ slice as the only clean test. (2) is recorded and not built for the prop book.

**Not licensed:** any window not in the design; any gate threshold read from these tables (the
terciles are the only cut and were declared); any netting of the harvest and post-harvest
windows. **The spent-slice ledger is unchanged:** nothing past 2023 was read for ZC, ZS or ZW.
