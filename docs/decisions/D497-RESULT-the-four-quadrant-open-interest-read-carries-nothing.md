# D497 — RESULT: the four-quadrant open-interest read carries nothing, the open-interest term flips sign between index and commodity roots, and the textbook reading is backwards on gold

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D497-RESULT-the-four-quadrant-open-interest-read-carries-nothing-the-open-interest-term-flips-sign-between-index-and-commodity-roots-and-the-textbook-reading-is-backwards-on-gold.md`. The H1 above is the full title.*

**2026-09-12.** Spec [D497 PRE-REG](D497-PRE-REG-open-interest-against-price-does-the-four-quadrant.md)
(`ab8b5df`, before the fixture and the runner). Fixture `scripts/build_fut_open_interest.py` →
`data/fixtures/fut_open_interest_daily.csv.gz` (13,843 rows, four roots, 2010-06 → 2026-09, gates
in its meta). Runner `scripts/run_d497_open_interest.py`; numbers `data/d497_open_interest.json`.
**In-sample 2016-01-04 → 2023-12-29; 2024 onward sealed; no holdout of any line touched; nothing
admitted.** Build 1.8 min, study 3 s.

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| 1 data layer: staleness 1 session on ≥ 80%, ≤ 2 on ≥ 97%, coverage ≥ 98%, roll gate holds | | staleness **p80 = 1, max = 2**; coverage **100.000%** on all four roots — held. **The roll gate [O4] could not fire as written** and was amended (§3) |
| 2 inside the rotation null on all four; ES and NQ nearest zero (\|mean\| < $3); CL largest in magnitude | | inside on all four; **ES −1.60, NQ −2.34** both under $3; **CL −7.74** the largest, GC −7.47 — held, precisely |
| 3 the largest single quadrant is price-down-with-OI-down on CL, still inside noise | | **CL price-down-OI-down −$11.1, the largest quadrant anywhere**, inside noise — held |
| 4 the cleared-volume control reproduces the OI result within ±40% on ≥ 3 of 4 roots | | **missed on all four.** The two differ by 2.9× (ES), flip sign (NQ), and differ by 3× (CL): **the change in open interest is not merely an activity measure** |
| 5 the price-only baseline is negative on NQ | | **−$8.72 net, −$5.21 gross** — held |

## 1. The four declared cells, and the two controls

Dollars per session at one micro, 2016–2023, one round trip, net of $3.00 + 1.009 ticks.

| | traded | gross | net | SE | hit | median | N1 exact p50 / p95 |
|---|---|---|---|---|---|---|---|
| **ES** signal | 1,889 | +2.66 | **−1.60** | 3.22 | 47.6% | −3.01 | −4.10 / +0.90 |
| **NQ** signal | 1,889 | +1.17 | **−2.34** | 4.60 | 48.7% | −2.50 | −3.46 / +4.66 |
| **CL** signal | 1,721 | −3.73 | **−7.74** | 2.75 | 46.4% | −6.01 | −4.26 / −0.17 |
| **GC** signal | 1,871 | −3.46 | **−7.47** | 1.77 | 44.7% | −7.01 | −3.89 / −0.88 |
| C1 cleared volume | | −0.43 / +5.46 / +1.52 / −0.43 | −4.69 / +1.96 / −2.49 / −4.44 | | | | |
| C2 price only | | −0.87 / −5.21 / +2.14 / +1.92 | −5.13 / −8.72 / −1.87 / −2.08 | | | | |

Family maximum over the four roots (1,726 common offsets): p50 −0.99, **p95 +4.66**. **Picks:
none.** No cell is positive, none is above its own exact rotation p95, and none is above the family
bar. Worst sessions are real event days: NQ 2022-02-24 (−$1,254), ES 2020-03-17 (−$844),
CL 2022-03-09 (−$791), GC 2020-03-13 (−$520).

**The rotation null validates itself**: its median is −$3.5 to −$4.3 a session on every root, which
is the cost of a signal with no gross edge. That is what a correctly built null of this rule must
produce, and it does.

## 2. What the open-interest term actually contributes

Gross dollars a session, the same rule with the open-interest term replaced:

| | with ΔOI | price only | **ΔOI contributes** | with Δcleared volume |
|---|---|---|---|---|
| ES | +2.66 | −0.87 | **+3.53** | −0.43 |
| NQ | +1.17 | −5.21 | **+6.38** | +5.46 |
| CL | −3.73 | +2.14 | **−5.87** | +1.52 |
| GC | −3.46 | +1.92 | **−5.38** | −0.43 |

**The term helps on the two index roots and hurts on the two commodity roots, by similar
magnitudes and with no consistent ordering against the volume version** — on NQ the cleared-volume
version (+5.46) beats the open-interest version (+1.17), on ES it is the reverse. Four roots
produce four different orderings of three constructions, and every difference is inside one
standard error of the net means ($1.8 to $5.5). That is the signature of noise, not of a
mechanism that happens to be asset-class-specific.

## 3. The quadrants, where the textbook claim is actually tested

Mean day-session move in dollars at one micro, by the state of the previous session:

| | price up, OI up | price up, OI down | price down, OI up | price down, OI down |
|---|---|---|---|---|
| textbook | new longs, continue | short covering, fade | new shorts, continue | liquidation, fade |
| ES | +5.4 (653) | −6.5 (384) | +3.8 (485) | +2.3 (367) |
| NQ | +0.3 (610) | −7.0 (441) | **+8.6 (464)** | **+7.9 (374)** |
| CL | −4.2 (546) | +2.7 (370) | −2.1 (440) | **−11.1 (365)** |
| GC | −2.0 (650) | **+10.7 (334)** | +0.5 (328) | −2.6 (559) |

- **On NQ the two down-price quadrants are both strongly positive and close to each other**
  (+8.6 and +7.9). The day session rises after a down day *whether open interest rose or fell*.
  That is the daily reversal D487 and D495 measured, and **the open-interest split does not
  separate it** — which is why the price-only baseline and the interacted signal both end up
  losing after cost in different ways.
- **On gold the most positive quadrant is price-up-with-open-interest-down (+$10.7)**, the
  "short covering, therefore exhaustion" cell the textbook says to fade. The classic reading is
  backwards there, on 334 sessions.
- No quadrant on any root is far enough from the others to survive its own null.

## 4. The fixture, and one gate that could not fire

The premise probe settled the causality question that decides whether this rule is legal at all:
**open interest for trade date T is first published around 21:00 ET on T itself**, so a 10:00 ET
entry on T+1 legitimately knows it. `ts_ref` is the session start, the evening before the trade
date, and is used only to label the reference session; causality rests on `ts_event` and is
asserted by gate [O1] (0 of 7,992 rows published at or after the entry).

**[O4] as pre-registered could not fire, and I am recording that rather than reporting a pass.**
It asked for a one-day fall of more than 40% in `oi_front` at each quarterly roll. Two things make
that impossible: the roll is spread across days, and `oi_front` in this fixture is the *largest-OI
month*, which is smooth through a roll by construction. The substantive claim — that the root
total is roll-immune — was re-tested on the expiring contract instead: **over the 20 sessions
before a month dies its own open interest falls 72–99%, while the root total moves 4–18%.** The
amendment is in the fixture meta and named there as an amendment.

Other audits: [M] vectorised P&L equals the loop on every root; [S] sign in money; [X] flipping
the open-interest sign negates the statistic exactly; [D] no session after 2023-12-29 reached the
measurement; sessions where either difference is zero are no-trade and are not charged cost
(12 to 9 per root); stale repeats, where the figure did not update, are dropped and counted
(24 to 29 per root). Build speed was 1.43× on 8 workers (18%), which is poor, but the job is
1.8 minutes and most of it is the serial assembly; not optimised, and said so.

## 5. What this settles

- **The four-quadrant open-interest read does not carry a day-session edge on ES, NQ, CL or GC.**
  Nothing is positive net, nothing clears its own rotation null, and the term's contribution
  changes sign across asset classes with no mechanism that would predict it.
- **Open interest is distinguishable from volume** (prediction 4 missed in the useful direction):
  the two give materially different answers, so a future construction cannot be dismissed as "just
  activity" without testing it. Neither carries here.
- **The one real structure in these tables is the price term on NQ**, the reversal after a down
  day, which is already the other session's D495 and is not this record's to claim.
- The open-interest fixture is built, gated and committed, and the same object is now available for
  any later construction at the cost of a read.

## 6. What it does not do

Nothing enters `COMPONENTS_PROP.md` or either book. No avenue is opened or closed (R15); closing
the open-interest question is the principal's call, and my reading is that the daily four-quadrant
form of it is answered while the object itself is now cheap to reuse. The sealed slice stays
sealed. The remaining volume-character constructions from the same slate are a separate record.
