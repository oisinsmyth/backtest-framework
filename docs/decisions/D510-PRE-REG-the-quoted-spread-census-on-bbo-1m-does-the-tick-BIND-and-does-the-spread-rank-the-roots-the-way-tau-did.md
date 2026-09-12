# D510 — the quoted-spread census on `bbo-1m`: does the tick BIND, and does the spread rank the eight roots the way τ did?

> **RENUMBERED D491 -> D510 on 2026-09-12.** This record was committed as **D491** in
> `299cb5d / 84c740b`; a concurrent session had already taken D491 for an unrelated study, and under this
> repository's convention the later writer moves. **No stub is left at D491** — that number
> belongs to the other session's record. Numbers were taken from a reserved block well clear
> of the active frontier (D496) because three sessions are racing the same counter and the
> next-free approach is what produced the collision.

**Pre-registration. Committed before the runner exists ([R8](../RULES.md#r8)).** Result in a
separate file. **NO RETURN IS READ.** Quoted bid/ask, sizes and order counts only.

**Occasioned by:** the principal's instruction to run this census, which is the
[R15](../RULES.md#r15) call [D489 §7.4](D489-RESULT-ZB-IS-large-tick-and-the-sigma-that-failed-C-d-is-the-window-not-the-contract-but-C6s-median-split-cuts-where-the-data-is-densest.md)
said was theirs to make.

## 1. Why this is worth a slice the programme had declared unread

D489 ranked eight roots on `τ_1h = tick/σ` and found ZN and ZB a factor of **3.3** clear of the
third. It could not compute the literature's ratio, whose denominator is volatility **per trade**,
and it named the reason: `ohlcv-1m` carries no trade count.

**The quoted spread is the better instrument anyway.** Large-tick is *defined* by the spread
sitting at its minimum — Gould & Bonart's large-tick result holds *"because the mean bid–ask
spread… is very close to its minimum possible value"*. **`bbo-1m` censuses that directly rather
than estimating it.** The cost is that these files cover **2025-09-11 → 2026-09-10**, a slice
[D468](D468-RESULT-none-of-24-session-windows-on-eight-roots-clears-the-component-standard-the-best-sits-at-the-78th-percentile-of-its-family-null.md)
and D489 both declared unread.

**That cost is paid for a NON-RETURN quantity only.** Nothing here reads a price change as a
signed return; no construction is scored; the 2024+ slice remains unspent for every return-bearing
line, and this record does not touch `BOOK_PROP.md` or the components ledger.

## 2. The confound this record must NOT fall into, named first

**D489 measured 2016–2023. These files are 2025–2026.** A disagreement between the two rankings
could be **horizon** (hour vs quote) or **era** (2016–23 vs 2025–26), and those are not separable
from the census alone.

> **So `τ_1h` is RECOMPUTED on the census's own window** — `data/fixtures/fut_sessions_hourly.csv.gz`
> covers 2025-09-11 → 2026-09-09 with ~257 sessions on every root — **and every comparison in this
> record is made against that same-window τ, never against D489's 2016–2023 numbers.** D489's
> figures are reported alongside purely so the era effect is visible as its own column.

## 3. The data, and the front-contract rule

**Files:** `data/raw/databento/*/glbx-mdp3-*.bbo-1m.dbn.zst`, 13 files, **7.45 GB compressed**,
2025-09-11 → 2026-09-10, `stype_in=parent`, 16,309 symbols. Fields used: `bid_px_00`, `ask_px_00`,
`bid_sz_00`, `ask_sz_00`, `bid_ct_00`, `ask_ct_00`, `ts_recv`, `instrument_id`.

**Roots:** the eight of D467/D468 — ES, NQ, YM, ZN, ZB, GC, CL, 6E. **RTY reported, outside every
bar**, as in D489.

**Outrights only.** The symbol filter is `^(ROOT)[FGHJKMNQUVXZ][0-9]{1,2}$`, which excludes
calendar spreads and combos (`ESZ6-ESH7`); a combo has its own spread and is a different object.

**Front contract per calendar day is taken from `fut_sessions_hourly`'s `contract` column**, i.e.
**D467's rule reused unchanged** (*"highest full-day volume per calendar ET day"*). It is not
re-derived here — a second front rule would be a second study.

**Window:** the 18:00 → 17:00 ET Globex session, the same clock D467/D468/D489 use.

## 4. The statistic

Per root, on front-contract minutes with a valid two-sided quote:

| | |
|---|---|
| **`spread_ticks`** | `(ask_px_00 − bid_px_00) / tick_points`, tick from `data/futures_contract_specs.json` (CME-verified; nothing hardcoded) |
| **`P1`** | **the headline: the fraction of quoted minutes at EXACTLY one tick** |
| **`P2`, `P3+`** | two ticks, three or more |
| **`mean_spread_ticks`** | the mean |
| **`queue_orders`** | median `bid_ct_00 + ask_ct_00` — depth in ORDERS at the touch |
| **`queue_lots`** | median `bid_sz_00 + ask_sz_00` — depth in CONTRACTS at the touch |
| **`crossings_per_hour`** | `ticks_per_hour ÷ mean_spread_ticks` — how many spread-widths an hour's move spans. **Declared because `P1` SATURATES and this does not** (see `S1`'s tie clause) |

**Validity mask, and it raises rather than dropping silently:** a minute enters only if
`bid_px_00 > 0`, `ask_px_00 > 0` and `ask_px_00 > bid_px_00`. **Every surviving spread must be an
integer multiple of the tick to 1e-6** — if it is not, the tick used is wrong for that root and the
runner **raises**, because a fractional "tick count" would silently rescale `P1` for exactly one
root and look plausible.

## 5. Declared conditions

- **`S1` — the AGREEMENT test.** Spearman rank correlation between the eight roots' `P1` ordering
  and their **same-window** `τ_1h` ordering. **If ρ ≥ 0.7 the two measures agree and D489's ranking
  is confirmed on an independent quantity. If ρ < 0.7, D489 §4's resolution of the lane-21/`C6`
  conflict is WITHDRAWN as horizon-specific, not merely qualified.**
  - **TIE CLAUSE, declared now:** **if five or more of the eight roots have `P1` ≥ 0.95, `S1` is
    reported UNRESOLVED regardless of ρ.** A rank correlation computed among near-ties against a
    ceiling identifies nothing — this is [D461 §4](D461-RESULT-stage-0-ABANDONED-the-hour-is-a-decay-from-the-cash-close-and-a-minute-with-no-rule-outranks-both-targets.md)'s
    defect (a condition that cannot fail on a one-rank difference) written in before it can bite.
- **`S2` — lane 21's claim, taken literally.** Lane 21 says *"ES is the canonical large-tick book:
  the spread is one tick essentially always."* **`S2` passes iff `P1(ES) ≥ 0.95`.**
- **`S3` — the adjudication `C6` and lane 21 disagree on.** **`S3` passes iff BOTH ZN and ZB have
  `P1` strictly above ES's.** This is the quote-level version of D489's `T3`.

**These three do not gate each other.** Each is reported on its own; there is no conjunction and
nothing is abandoned on this record.

## 6. THE FORK, written down before the numbers, because both branches are informative

> **Branch A — everything saturates** (most roots at `P1` ≈ 0.97–0.99). Then **the tick BINDS on
> all eight**, the spread cannot discriminate between them, and **`τ = tick/σ` is therefore the
> correct large-tick discriminator after all: D489 is STRENGTHENED, not contradicted.** Lane 21's
> ES claim is **true but non-identifying** — true of eight roots, so it never distinguished ES.
>
> **Branch B — the roots differ materially in `P1`.** Then the spread is the discriminator, `τ` was
> a proxy, and **D489's ranking is a proxy's ranking.** §7 of D489 would need its point 1 requalified.

**I am writing this fork down so that neither outcome can be narrated afterwards as the one I
expected.** Branch A is the outcome that makes my previous record look better and it is the one I
predict below; that is exactly why it is stated as a fork and not as a prediction alone.

## 7. Predictions

- **`P-a` — `S2` PASSES: `P1(ES) ≥ 0.97`.** ES is the deepest equity-index book on the exchange and
  its $12.50 tick is large against a minute's move.
- **`P-b` — `S3` FAILS.** I expect **ZN ≈ ES ≈ 0.97–0.99 and ZB BELOW both, around 0.85–0.95**: ZB
  is materially thinner than ZN and its 1/32 tick is the coarsest in the set, so its spread should
  widen more often. **If so, the census and `τ_1h` DISAGREE on ZB, and the disagreement is against
  the record I wrote one hour ago.**
- **`P-c` — `S1` is UNRESOLVED on the tie clause**, because I expect ES, ZN, GC, CL and 6E all
  above 0.95. **The tie clause is predicted to fire; if it does not, ρ decides and I expect it
  POSITIVE but below 0.7.**
- **`P-d` — NQ is the LOWEST `P1` of the eight**, around 0.55–0.80. D489 put NQ at 123 ticks an
  hour on a $5 tick, so its spread has the most room to widen. **NQ is the root where τ and the
  spread should agree most strongly.**
- **`P-e` — `crossings_per_hour` reproduces D489's ordering almost exactly** (ZN and ZB lowest),
  **because if Branch A holds, `mean_spread_ticks` ≈ 1 for most roots and the quantity collapses to
  `ticks_per_hour`.** This is a prediction that a derived statistic is nearly circular, stated so
  it is not later presented as independent confirmation.
- **`P-f` — ZB's `P1` is materially LOWER overnight than in the 08:00–10:00 ET window.** D489's
  `R1b` put ZB's variance in 07:00–10:00; a thin overnight book should widen the quote even where
  volatility is low. **If ZB's spread is instead WIDEST where its volatility is highest, the two
  effects are confounded and the hourly breakdown cannot separate liquidity from volatility** —
  which would be worth saying.
- **`P-g` — wall time under 8 minutes.** One 209 MB file decoded in **1.5 s** to 12.2 M rows; 7.45
  GB is ~36× that, so decode is ~1 min and the filtering dominates. Files are processed one at a
  time (≈1.2 GB resident each), not concatenated.

## 8. Not in scope

**No return, no signal, no strategy, no cost model, no component line, no book.** Quotes only.
**Nothing here admits, opens or closes anything** — under R15 that is the principal's call.
**The 2024+ slice remains unspent for every return-bearing construction**; what is spent here is a
quote census, and this record says so explicitly so that a later study cannot claim the slice was
already gone.
