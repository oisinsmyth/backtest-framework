# D454 RESULT — 17,270 insider purchase filings on 76% of the fixture including 71% of the dead, filed within two business days, contrarian, small and cheap: no abandon condition fires

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D454-RESULT-17k-insider-purchases-on-76-percent-of-the-fixture-including-71-percent-of-the-dead-filed-in-two-days-contrarian-small-and-cheap-no-abandon-condition-fires.md`. The H1 above is the full title.*

**A MEASUREMENT (R15): admits nothing. NO forward return was read.** Spec `4ce4b86` predates the
fetcher and the runner (R8). Pull 6.4 min (81 quarterly archives, 910 MB, git-ignored); parse
0.8 min (72 quarters through 2023q4; 2024q1–2026q1 cached and unread); tables 0.2 min.

```
[L] every transaction precedes its filing (46 mis-dated transactions dropped and counted); no filing after 2023-12-29 enters any table
value guard: 43 transactions above $2B dropped (a $4 x 10^14 "purchase" of PKY in 2012 is a mis-scaled field)
issuer -> name by CIK inside D331's windows: 671,335 Form 4 submissions mapped; ticker-only issuers 2010-2023: 17,709 (2.6%), all reported, none used
selftest: title rule, aggregation, business-day lag, roles, routine flags, availability strictly after the filing
```

---

## 1. Coverage — A1 does not fire

```
                          n     >= 1 purchase filing while live, 2010-2023     >= 1 sale filing
cohort  alive          1011          78.4%                                          78.8%
cohort  DEAD            562          70.8%                                          74.6%
all                    1573          75.7%                                          77.3%
by CIK confidence: high 78.7%   low (full-text) 75.3%   unresolved (43) 0%
dead by delisting year: 2011 43% (7)  2012 43%  2013 75%  2014 70%  2015 70%  2016 70%  2017 68%  2018 62%  2019 63%  2020 63%  2021 82%  2022 70%  2023 68%
live name-years with at least one purchase filing: 37%  (32-42% every year)
```

The Form 4 obligation binds every listed issuer, and the SEC's bulk data serves the delisted
ones: 398 of the 562 dead names carry at least one insider purchase while live. The gap to 100%
is names where no insider ever bought in the open market (a third of live name-years have no
purchase at all — X-a's 45–60% was too high; insiders buy less often than they sell by six to one).

---

## 2. Shape

```
purchase filings 2010-2023: 17,270 on 1,279 names;  sale filings 109,381;  sales : purchases 6.3 (2020 5.2, 2022 4.0)
value per filing: p10 $10,035   p50 $106,467   p90 $3,019,919
owners per filing: median 1, >= 2 on 25%;  distinct owners buying the same name within +-5 bars >= 2 on 47% of filings
roles (any owner on the filing): Director 74%  Officer 41%  10% owner 18%  Other 4%;  direct ownership 71% of value
by year, purchases: 987 (2010) .. 1,510 (2015) .. 1,474 (2020) .. 1,501 (2022) .. 1,296 (2023) -- no collapse, no spike
```

**The median purchase is $106k, not the $25–60k predicted:** this is a $100–500-price mid-cap
universe with a price floor, and its insiders write bigger cheques. **Clusters are common, not
rare:** a second distinct insider buys the same name within a week on 47% of filings. Directors
outnumber officers among buyers (74% vs 41%), the reverse of sellers, as the literature says.

---

## 3. Timeliness — the event is an event

```
business days, earliest transaction -> filing:  p50 2   p90 3   > 2 days on 10.0%;   median 1-2 every year 2010-2023
```

Nine filings in ten are inside the statutory two business days. **A purchase is public, on
average, two trading days after it happens** — the shape the issuance line lacked.

---

## 4. Routine vs opportunistic

```
same owner, same name, same calendar month in each of the two prior years:  4.6% of purchase filings (all owners on the filing routine: 3.7%);  directors 6%, officers 6%
```

Below the 8–20% predicted: with a two-year look-back on a thirteen-year window and a universe
that turns over, few buyers qualify. **95% of purchases are non-routine by the strictest
definition**, which means the routine/opportunistic split will not be the discriminator it is in
the literature's 25-year samples; it is reported, not gated on.

---

## 5. What the buys sit in

```
share in lo / mid / hi tercile at the availability bar (base 33/33/33):
  purchases   price 46/30/24   volatility 24/30/46   12-1 momentum 46/31/23   20-day return 47/26/28   dollar volume 60/21/19     issuance decile: top 14%, bottom 10% (base 10/10)
  sales       price 22/32/46   volatility 31/33/36   12-1 momentum 22/33/45   20-day return 26/30/44   dollar volume 38/25/37     issuance decile: top 10%, bottom  9%
```

**Insiders buy what has fallen, what is cheap, what is thin, and what is volatile; they sell the
mirror.** 47% of purchases follow a bottom-tercile 20-day return and 46% a bottom-tercile year of
momentum; 60% are in the thinnest third by dollar volume. Every one of X-e's directions held.
Two things this says for stage 1: the state-matched control (same price × volatility × momentum
cell) is not optional — a random name in the same cell is a beaten-down small name too, and the
D446 line showed such cells have their own hedged drift — and **the buys sit where the cost model
is most nearly a quote** (thin, volatile, cheap), so the crossed line will be the honest one.
The issuance cross is mild and the *wrong* way for the "insiders buy where the firm buys back"
story: 14% of purchases are in the top issuance decile (issuers), 10% in the bottom.

---

## 6. The tails, named

- **Largest purchases by value** (after the $2B guard): FMI 2018-08-02 $2.2B and FMI 2015-04-09
  $780M (Roche, a 10% owner, building its Foundation Medicine stake — a strategic holder, not an
  insider signal); RWAY 2022-02-09 $1.9B; DCP 2017-01-04 $1.0B; NLSN 2022-04 $870M and $631M
  (the Elliott/Brookfield take-private); BAC 2020-07-22 $813M (Berkshire). **Nine of the ten are
  10% owners** (X-f ✓). A stage 1 must decide what to do with 10% owners *before* it runs: they
  are 18% of filings and most of the dollars, and their buying is a different mechanism.
- **Largest clusters:** every one is HY (Hyster-Yale) in 2018–2019 with 60–66 distinct reporting
  owners — the Rankin family trusts, each a Section 16 filer, buying through a dividend
  reinvestment arrangement. That is one name filing as sixty; the cluster measure needs a
  family-trust guard (owners with the same address, or a cap) at stage 1.

---

## 7. Predictions — three of six, and the misses point the same way

| | prediction | outcome |
|---|---|---|
| X-a | alive ≥ 85%, dead ≥ 60%, all ≥ 75%; name-years 45–60%; ticker-only < 5% | alive **78%**, dead 71% ✓, all 76% ✓; name-years **37%**; ticker-only 2.6% ✓ |
| X-b | 12,000–35,000; p50 $25–60k, p90 $0.5–1.5M; clusters 12–25%; officer+director ≥ 85%; S:P 3–6 | 17,270 ✓; **$106k / $3.0M**; **47%**; 91% ✓; **6.3** |
| X-c | lag p50 1–2, > 2 on 10–20% | 2 ✓, 10% ✓ |
| X-d | routine 8–20%, officers > directors | **4.6%**; equal |
| X-e | ret20 bottom ≥ 45%, mom bottom ≥ 40%, small/cheap ≥ 40%; issuance top 8–15 / bottom 12–20 | 47% ✓, 46% ✓, 46%/60% ✓; top 14% ✓, bottom **10%** |
| X-f | largest by value are 10% owners; largest clusters 2008–09 / 2020-03 | 9/10 ✓; **HY 2018–19, one family** |

The misses share a cause: this universe's insiders are richer, buy bigger, cluster more and
repeat less than the all-CRSP samples the predictions were drawn from.

---

## 8. What this leaves — the principal's call

**None of the three abandon conditions fires**, and the data has the shape a kernel event study
needs: 17,270 dated events on a dead-inclusive universe, public in two days, in names where the
cost model is closest to honest. Under §4 of the spec a **stage 1 is the next record**, and stage 0
has already fixed four of its design choices: (i) exclude or separate **10% owners** (a different
mechanism, most of the dollars); (ii) a **family-trust guard** on the cluster measure; (iii) the
**state-matched control by price × volatility × momentum cell** is required, not optional; (iv)
a **value floor** (the p10 is $10k — a $10k director purchase is a token) declared before any
return, with the value axis reported across the whole range. The hold and the bar are the spec's
to declare.

**Disposition is the principal's.**

---

## 9. R13

Forty-sixth look by object; look #1 on insider demand; no forward return, no holdout. Files:
`scripts/fetch_sec_form345.py`, `scripts/run_d454_insider_stage0.py`, `data/d454_insider_events.csv.gz`
(133,466 purchase and sale filings), `data/d454_insider_owner_rows.csv.gz`, `data/d454_build_info.json`,
`data/d454_stage0.json`.
