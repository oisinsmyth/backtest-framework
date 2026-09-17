# D444 RESULT — EDGAR serves 77% of the dead names; first-filed share counts are point-in-time at 38 days; issuance is a persistent, non-proxy state on the dead-inclusive fixture. No abandon condition fires.

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D444-RESULT-EDGAR-serves-77-percent-of-the-dead-names-and-issuance-holds-on-the-dead-inclusive-fixture-no-abandon-condition-fires.md`. The H1 above is the full title.*

**A DATA ACQUISITION plus D443's stage-0 tables (R15 for the acquisition): admits nothing; NO forward
return was read.** Spec `f0d97af` predates the fetcher and the runner (R8). Pull 7.3 min (1,519
CIKs, 1,503 documents, 16 404s, 226 MB gz-cached, git-ignored); panel 1.5 min; tables 0.1 min.

```
[L] every value's period end <= its filing date (44 filer-misdated rows dropped and counted); availability = the first bar STRICTLY AFTER `filed`
[S] 0.57% flagged;  splits: 796 visible / 87 judged restated (90%);  tag: cover-page count on 1,284 names, balance-sheet instant on 88
selftest: first-filed wins over restatements, S-1 rows dropped, tag choice, annual-flow filter, t_av after filed, split branches, NIY
```

---

## 1. Coverage — A1 does not fire

```
                       n    any report   usable NS          D443 (vendor)
cohort  alive       1011     88.3%        80.8%              93.9%
cohort  DEAD         562     80.1%        77.0%               0.0%
all                 1573     85.4%        79.5%              60.3%
by CIK confidence:  high (1,138) 81%   low / full-text match (392) 83%   unresolved (43) 0%
dead by delisting year:  2011 0% (7)  2012 71%  2013 82%  2014 89%  2015 86%  2016 77%  2017 55%  2018 72%  2019 67%  2020 71%  2021 90%  2022 76%  2023 78%
live name-years with a fresh NS at year end: 68%
```

**The dead are served.** 433 of the 562 delisted names carry a usable point-in-time share series,
against zero from the vendor. The gaps are what §5 said they would be: the 43 unresolved CIKs; the
seven names delisted in 2011, before XBRL was universal; and — the one the spec did not name — **168
names (111 alive, 57 dead) with a CIK document and no share count in it.** These are the
**multi-class filers** (ABNB, AMH, AMCX …) and some foreign filers (AMX, AFYA on 20-F): the SEC's
companyfacts API omits every dimensioned fact, and a filer with Class A and Class B reports the
cover count per class with a dimension. That is 11% of the fixture, invisible to this endpoint by
construction; the fix is the frames API or the per-filing XBRL, both a separate acquisition.

The 392 names whose CIK came from D331's full-text ticker match are served at the same rate as the
map-resolved ones (83% vs 81%): the low-confidence resolutions are real.

---

## 2. Point in time — the two numbers EDGAR has and the vendor did not

```
filing lag, period end -> filed (35,591 balance-sheet instants):  p10 29   p50 38   p90 62 days;   > 90 days 4.6%
   by form: 10-Q 36   10-K 57   20-F 110;   by year: 47 in 2010, 38-39 every year since;   cover date -> filed: 6 days
restatement: 1.9% of first-filed share counts are filed again later; 0.1% change by more than 0.1% (7% of those refiled)
```

**D443's 90-day lag was conservative on 95% of values and wrong by seven weeks on the median.** A
10-Q's count is public 36 days after the quarter; the cover-page count is dated six days before
filing, so the series is available within a week of its own date. Restatement is negligible on
share counts: one value in a thousand changes after first filing. The point-in-time construction
therefore costs nothing here and is kept because it costs nothing.

---

## 3. D443's tables on the dead-inclusive panel

```
NS = ln(SO_q / SO_{q-1y}), 35,521 usable name-quarters 2010-2023 on 1,250 names
  p5 -7.7  p10 -4.8  p25 -1.5  p50 +0.3  p75 +1.9  p90 +10.0  p95 +20.1 %/yr;  NS > 0 on 59%;  net repurchase 50% of name-quarters (D443 survivors: 62%)
persistence:  one year +0.536 +- 0.005 (D443 0.441)   one quarter +0.876   top decile stays top-3: 59%;   NIY one year +0.657
proxy check (52 quarter ends, 517 names):  mom12 +0.042   ret20 -0.000   log price -0.159   log mcap -0.181   vol60 +0.197   log DV -0.164   rank R2 0.103 +- 0.005
by atlas state:  vol_hi +3.9   mom_hi +2.2   price_lo +1.6 ... price_hi +1.0   mom_lo +0.7   vol_lo -0.3
```

**A2 and A3 do not fire, and with the dead in the object is stronger, not weaker.** Persistence
rises from 0.44 to 0.54 a year out; the six tested axes still explain 10% of issuance's rank
variance; momentum is +0.04. The buyback share falls from 62% to 50% as the issuers come back —
the direction §5 predicted — though not as far as predicted: the median stays near zero, because
the marginal dead name is a small issuer with a short history, not a serial diluter with a long one.

---

## 4. Three things the tails show, disclosed

1. **Scale errors in filer XBRL.** The ten largest and ten smallest NS are ±1,382% — ln(10⁶) —
   where a filer tagged the count in the wrong scale for one or more quarters (AEP at 4.8 × 10¹⁴,
   CLX, BTI; SWY at 1 share). 98 rows (0.20%) on 53 names sit more than 50× from their own name's
   median; the [S] flag catches those where the jump is within a quarter and misses those that
   persist a year. **They do not move any table** (NS median +0.287 with them, +0.286 without) and
   a stage 1 must carry the guard explicitly: drop a count more than 50× from the name's median.
2. **The vendor disagrees with the first filing.** On 24,163 name-quarters where both carry a
   balance-sheet count at the same period end, the median gap is 1.2% and only 45% agree within 1%
   (84% within 10%) — X-f predicted 85% within 1%. The vendor's number is not the first-filed one:
   it is restated, rescaled, or a different class basis. Which is "right" for a trader is the one
   they could have read on the day, and that is this one.
3. **Split judgement:** the first-filed series shows 90% of split events (D443's vendor series:
   55%), as X-f predicted — the check of the point-in-time extraction passes.

---

## 5. Predictions — four of six, and the misses are informative

| | prediction | outcome |
|---|---|---|
| X-a | alive ≥ 92%, dead 65–85%, all ≥ 85%; A1 off | alive **81%**, dead 77% ✓, all 79% — the 168 multi-class names were not in the prediction; A1 off ✓ |
| X-b | lag p50 38–48, p90 ~80, > 90 d < 5% | 38 ✓, **62**, 4.6% ✓ |
| X-c | restated 5–15% | **0.1%** — share counts are essentially never restated |
| X-d | NS median +0.5..+1.5, > 0 on 60–68%, repurchase 45–55% | +0.3, 59%, 50% ✓ — the direction held, the size did not |
| X-e | persistence 0.35–0.50; R² 0.08–0.20; max ρ < 0.30; mom < 0.10 | **0.54** (above), 0.103 ✓, 0.197 ✓, 0.042 ✓ |
| X-f | vendor within 1% on ≥ 85%; splits visible ≥ 90% | **45%**; 90% ✓ |

---

## 6. What this leaves — the principal's call

**The acquisition did what it was for.** The fixture's dead cohort is now visible through the
share count, point-in-time, filing-dated, from the primary source, at no vendor cost; the object
that D443 found on survivors reproduces and strengthens on the dead-inclusive panel; none of the
three abandon conditions fires. Under §4 of the spec, **a stage 1 is the next record**: forward
returns on issuance as a *state* (persistent, so a slot book, not an event study), the
state-matched random control, the enumerated time rotation, the persistent-selector control,
all declared before any return is read; equal-weight, both sides (net issuers short, net
repurchasers long), the kernel's cost lines both printed. The panel and the tables are committed;
the raw cache is not (exchange-licensed rule applied to the SEC's data as well, by habit — it is
public, and could be committed if the principal prefers).

**Two gaps to carry into that record, not fix silently:** the 168 multi-class and foreign
filers (11%) are absent and must be listed as such in any universe count; and the 50× scale guard
must be in the stage-1 panel.

**Disposition is the principal's.**

---

## 7. R13

Forty-third look by object; look #1 on share supply from a primary source; no forward return, no
holdout. Files: `scripts/fetch_edgar_companyfacts.py`, `scripts/run_d444_edgar_issuance.py`,
`data/d444_issuance_panel.csv.gz` (49,421 rows, 1,343 names), `data/d444_bs_instants.csv.gz`,
`data/d444_issuance_panel_info.json`, `data/d444_stage0.json`.
