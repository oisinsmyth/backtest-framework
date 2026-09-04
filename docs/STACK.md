# The stack, signal to present

**What each layer contributes, what it is worth once costed honestly, and where
the next study goes.** Rewritten 2026-09-04 after D317 and D318.

Companion to [FINDINGS.md](FINDINGS.md) (substantive results) and
[decisions/](decisions/README.md) (one call each).
**[PICKUP.md](../PICKUP.md) is stale** — last updated 2026-09-02, before the whole
D285→D318 spread programme.

**§7 records what earlier versions of this document got wrong.** Two of the three
errors were caught by the principal, not by me.

---

## 0. The stack, and what it earns

```
signal        the D293 confluence          min z +2.58 across three nulls
construction  factor-neutral spread        removes -mu - sigma^2          (D285)
width         N_eff = 2, FIXED             +21 bp over N=19, basis-immune (D300)
exit          the target, or nothing       +0.69 bp/bar, and only at N <= 3
overlay       OUT at this width            -3.37 bp/bar at N=2 -- but see D319
```

**Charged its own held-name spread and IBKR per-share commission (D318):**

| | net bp/bar | net Sharpe | gross Sharpe |
|---|--:|--:|--:|
| **N=2 / target** | **+11.36** | +0.261 | +0.754 |
| **N=2 / none** | **+10.67** | **+0.288** | +0.770 |

**These two are not distinguishable from each other** — D316 put the minimum
detectable effect at ~18 bp/bar for a paired per-bar test at this concentration.

## 1. Three axes, which earlier versions of this document ran together

### Axis A — should width VARY over time? **No. Five studies, all closed.**

D299 (ladder), D308 (discrete), D311 (continuous λ), D312 (vol-targeted), D313
(universe-conditioned). Every one lost to a fixed width. **D314 explains all five
at once**: with ρ = 0.0020, `Sharpe = √N·net/σ`, net is monotone down in width, so
the optimum is a **corner** — and a rule that varies N can only move away from a
corner.

### Axis B — which FIXED width? **N_eff = 2, and it is immune to the cost basis.**

In D300/D306's construction **turnover is invariant to N** — 0.2002–0.2003 at
every depth, because it is just `1/k`. So the cost basis cancels out of the
comparison:

```
N=2 minus N=19, common rt  56.98 : +21.03      per-cell held rt : +25.02
                common rt  86.70 : +21.03
                common rt 105.24 : +21.03
```

**Concentration wins by ~21 bp whatever round trip you charge**, and N=2 stays
net-positive at the harshest basis *plus* commission.

### Axis C — which CONSTRUCTION? **D300/D306's, not D310's.**

| | D300/D306 | D310+ |
|---|---|---|
| build | top-N per leg, hold `k`=5 | rank-weight the whole 25-name gate |
| turnover at N=2 | **0.2003** | **0.3465** (1.73×) |
| turnover vs N | **invariant** (`1/k`) | **falls** with width |
| net at N=2 | **+11.36** | +4.37 published, **−1.54** corrected |
| width result | **basis-immune** | **basis-fragile — flips sign** |

**D310 was meant as a refinement and correctly costed it is the worse book.**
D311–D316 all sit on it. Their *relative* results survive (every arm shares one
`rt`); their absolute nets do not. See [D317](decisions/D317-CORRECTION-the-D310-family-was-charged-the-wrong-spread.md).

## 2. The exit work

**Cleared their own matched nulls:**

| exit | study | effect | null |
|---|---|---|---|
| **profit target** | D295 | +4.95 bp/bar, t +2.58 | p50 +1.49, p95 +3.11, **p = 0.0050** |
| **trailing overlay** | D297 | gross Sharpe **+0.512 → +0.728**, maxDD **−62%** | **p = 0.0150** |
| reversion | D295 | +1.78 | clears |

**Died:** stops (p 0.98, 0.995) · displacement (D286 did not reproduce) · idle
conditions (null p95 −0.40, R7's pathology) · the ladder (D299) · reversion *as an
addition* · and "six survivors", which D295's correction reduced to **three
distinct books, two non-pathological**.

**The pinning governs the family.** `sel = rank < N_SLOTS`, so an exit on a
still-selected name re-enters it the same bar — **0.00% of held bars differ**.
Adding a price exit alongside a signal exit is arithmetically inert.

**What each exit is worth, costed correctly (D318):**

| N | **target − none** | **overlay on none** |
|--:|--:|--:|
| **2** | **+0.69** | **−3.37** |
| 3 | +3.48 | +3.27 |
| 7 | −4.41 | +5.98 |
| 19 | −1.27 | +6.53 |

**Mutually exclusive in sign.** The target pays only at N ≤ 3; the overlay only at
N ≥ 3. And +0.69 independently reproduces D307's +0.80 and D305's +0.79 — three
routes to one number.

## 3. Cost, which was wrong twice and is now right

1. **Spread basis.** D310+ charged the *universe's* median half-spread (rt 56.98)
   to a book holding names at 18.51–25.05 bp. **The two axes need opposite
   treatment** — per-cell across widths (the spread difference is *caused* by the
   width choice), common within a width across exits (D307). D318 applies both.
2. **Commission was never charged at all.** IBKR per-share on the held median
   price: **0.66 bp/side at N=2 ($75.95), 2.11 at N=19 ($23.72)**. It works in
   concentration's favour and changes no verdict.
3. **Published `sharpe` columns in D306 and D310 are GROSS Sharpes** — verified,
   not assumed. D306 §3's "net and Sharpe point at different books, 3× volatility
   apart" was that mismatch; on net Sharpe **both objectives point at N_eff = 2.**

## 4. What is decisive, and what is merely not-rejected

**Decisive against a null:** the spread construction, the confluence ranking
(min z +2.58), concentration (p = 0.0050 at every depth).

**Real but small, and confirmed three ways:** the target, ~+0.7 to +0.8 bp/bar.

**Not resolvable on this fixture:** everything else. D316 measured the minimum
detectable effect at **11–18 bp/bar** at N_eff = 2 against a book netting ~11.
**No component that could exist would register on a paired per-bar test here.** A
non-significant result at this concentration is a statement about resolution, not
about the component.

## 5. Next

**D319 — the overlay at concentration, pre-registered and running first.** The
overlay is the largest Sharpe effect this programme has produced and it is ruled
out at the operating point by **a single cell at a single threshold**. Its trigger
is `drawdown >= X × trailing_vol(book)`, and D312 measured that denominator as
**noise at N_eff = 2 (ρ = −0.016) and usable at N=19 (+0.347)** — a named
mechanism for why it fails there, and D313 has already measured a replacement.

**Then B — the tilt filters.** D304's unrun study. Held names cost **26.31 bp**
half-spread against the universe's **13.20**; concentration alone already moved
held price **$23.72 → $75.95**. Mandatory: a price-matched control (D284 died of
discovering the price level) and a persistence-matched random exclusion (a per-bar
random exclusion churns where the treatment persists — the defect that voided
D291's veto arm).

**Then the entry signal**, frozen since D293 and still the only untested surface
of any size.

## 6. Owed

- **`[S]` SPREAD BASIS assertion** for every runner: the round trip must come from
  the names held, be reported per-cell *and* common, and **FAIL against the
  universe median**. `[C]` checked cost's dimensions and never its basis.
- **Sub-2 widths have never been run on D300/D306's construction** — D315a tested
  them on D310's.
- **D318's re-costing reorders cells, so D300/D306's null p-values no longer
  attach** to the cells they were computed for on the exit axis.

## 7. What earlier versions of this document got wrong

Kept legible rather than quietly fixed.

1. **"Nothing after D300 was an improvement."** Wrong — D303 (correctness), D305
   arm S (+1.35 bp/bar, book kept full), D306 (the target composes with
   concentration, and width/exits are separable).
2. **Calling the target and the exits "decoration" on a paired t of +0.17.**
   Wrong bar and wrong inference: the programme's standard is beating your own
   matched null, which the target cleared at **p = 0.0050**, and the paired test
   was blind anyway (MDE 18.3 against a book netting 11).
3. **Quoting D310's `none/exp2` at +4.37 as "the best cell".** Wrong on both
   counts — wrong construction, and +4.37 was the universe's cost basis.

**The principal caught 1 and 2 and prompted 3.** The common thread is reading a
non-result as a null result, and ranking cells off a published table instead of
measuring the difference between them.
