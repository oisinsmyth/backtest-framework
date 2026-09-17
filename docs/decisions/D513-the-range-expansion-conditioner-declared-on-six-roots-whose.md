# D513 — the range-expansion conditioner, declared in advance on six roots whose 2024+ slice is unread

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D513-the-range-expansion-conditioner-declared-on-six-roots-whose-2024-slice-is-unread.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**In-sample 2016-01-04 → 2023-12-29. The 2024+ slice of these six roots is UNREAD and stays unread
under this record** — that is the entire point of moving the question here.

## 0. Why this record exists

On the principal's word, after the conditioner line on the admitted arm was closed
(BOOK_PROP, 2026-09-13). D508, D509 and D512 all carried the same structural defect, stated in each
of their §0: **the admitted arm has no unread slice on NQ** (D503), so nothing found on it could
ever be confirmed. D512's range-expansion conditioner was nevertheless the most interesting result
of the three — it does not reverse within year, and its bottom quintile loses *gross* — and it was
refused by a family bar at 6.0% rather than dismissed.

**This record moves that conditioner to ground where a confirmation is possible**, declares it in
advance, and stops. It reads only 2016–2023. **The forward read is a separate command on the
principal's word**, exactly as K8's was.

## 1. The construction, restated and frozen

**The conditioner**, one value per session, every window ending at d−1 so it is known before the
session it labels:

```
range_d = log(high_d / low_d)          over segments h09 .. h15, the day session
V_d     = log( EMA50(range) / SMA200(range) )
```

**One window, declared: the day session.** D512's addendum showed the day, night and 23-hour
versions correlate at **+0.99** and are one conditioner measured three ways, with the apparent gap
between them worth nine sessions. Choosing among them after the fact is what that addendum warns
against, so this record declares the day-session window — D512's own primary — and scores nothing
else. **The log range is used, not the point range**: D512 measured the price-level contamination at
+0.01 to +0.02 and found the choice immaterial, so this is a tie broken on principle, not on data.

**The construction conditioned** is the frozen MACD arm, transplanted per root by the other
session's own generalised builder (`d506_macd_breadth.build_root`), which applies D484's `present`
and `same_front` filters before flattening. Nothing about the arm is re-implemented or re-tuned.

## 2. The roots, and what is known about them

**Six roots whose 2024+ is unread: YM, ZN, ZB, GC, CL, 6E.** NQ and ES are excluded — NQ's slice is
spent for this arm (D503) and ES's overnight leg is spent (D473).

**What is already known and must frame the reading:** the other session's D506 found that **the arm
does not transplant** — one root of thirty-five clears its own null and it is the one the arm was
found on. So on these six the arm is expected to be flat or negative unconditionally. **That does
not make the question empty; it sharpens it.** The claim under test is not "the arm works here" but
**"a compressed range is where a trend construction bleeds"**. If V separates a flat series into a
positive top and a negative bottom on roots where the arm has no overall edge, the conditioner is a
property of trend constructions. If it separates nothing, D512's result was a property of NQ's
history.

**The unconditional per-root arm figures are reported beside every cell**, so no reader can mistake
a conditional split for an edge.

## 3. The primary statistic, one (R14)

**Δ/σ on YM**: the top-minus-bottom quintile difference of net P&L per session, divided by that
root's own daily net P&L standard deviation.

**Why standardised rather than dollars.** D509 and D512 used dollars, which is right for one
instrument and wrong across six: a ZB session and a 6E session are not comparable in dollars, and a
family maximum over unstandardised cells would simply select the largest contract. **Δ in dollars
and in ticks is reported beside it** so the economic size is never hidden.

**Why YM.** It is the index root closest to the one the arm was built on, its 2024+ is unread, and
it was the declared primary of D506 for reasons already on the record (the best cost-to-move
improvement of any root with a σ that fits the account's floor). Declared before the run.

## 4. Nulls and controls

- **N1, exact enumerated rotation** of V against the arm's P&L for each root, re-forming quintiles at
  every offset. Per D509's proof, this subsumes a run-length-matched persistent gate.
- **N2, family maximum** over the six roots under common offsets. The primary must clear this.
- **N3, within-year.** Δ/σ inside each calendar year, per root. D512's range conditioner passed this
  on NQ where the stretch failed it; the question is whether it passes on unspent ground.
- **N4, the direction check.** The sign of Δ must be **positive** — the conditioner's claim is that a
  compressed range is bad for a trend construction. A negative Δ that clears a two-sided null is not
  a confirmation of D512; it is a contradiction of it, and the record will say so.

## 5. Decision rule (pre-registered)

- **PROCEED to a forward read** — a separate record, on the principal's explicit word, reading
  2024-01-02 → 2026-09-09 on the declared root only — if the primary clears N1, clears the N2 family
  p95, is positive, and holds its sign within year on a majority of years.
- **PICK** if it clears N1 and N4 but fails N2 or N3: recorded, no forward read.
- **CLOSE** otherwise. The principal closes.

**The forward slice is not read here under any outcome.**

## 6. Predictions (checkable in the runner's quantities)

- **X-a** The arm is unconditionally **flat or negative on at least four of the six roots**, net
  Sharpe between −0.3 and +0.3, consistent with D506's finding that it does not transplant.
- **X-b** The primary Δ/σ on YM is **positive but small, between +0.05 and +0.30**, and **does not
  clear its own N1 p95**, which lands between +0.30 and +0.55.
- **X-c** The N2 family p95 over six roots is **1.2× to 1.6×** the single-cell p95.
- **X-d** Δ is **positive on at least four of the six roots** — the direction survives even if the
  size does not, because a compressed-range regime is thin for any trend construction.
- **X-e** The within-year mean keeps the pooled sign on **at least four roots**, unlike the 200-day
  stretch which reversed on NQ.
- **X-f** The verdict is **PICK or CLOSE**, not PROCEED.

## 7. Files

This record · `scripts/run_d513_conditioner_unspent_roots.py` (`--run`, `--selftest`, importing the
frozen arm from `d506_macd_breadth` and the statistic from `run_d509_quintile_primary`) ·
`data/d513_conditioner_unspent_roots.json` · RESULT (separate). Runtime under two minutes.
