# D439 — passive-fill capture on the 15-minute fixtures: how much of the spread a limit order recovers, net of the times it fills against you

**A MEASUREMENT** (D392's class). **Scores no strategy, proposes no rule, admits nothing (R15).
Committed before the runner exists (R8).** D400–D438 used, D407–D410 and D390–D399 reserved.
**2024-01-01 onward on every 15m fixture is RESERVED and is not read** (D383/D414's cut, asserted).

## 1. Why

Every cost number in this repo — the D411 line's neutral Corwin–Schultz, the D345 kernel's PUB/PB
half-spreads — charges a crossed spread at entry and at exit. D438 ended on that: B's information
(+34 in the wide third) is real and the round trip there is 84 bp. Whether a passive order recovers
part of that has never been measured on this data. This measures it, as a **bound**: the 15m
single-name fixtures are 40 survivor names, mostly large and liquid — not the wide-spread third
where B lives — so the answer is what passive execution recovers *on liquid names*, and the
extrapolation to illiquid ones is stated as a guess, not a number.

## 2. Data

`cohort3` (8) + `cohort4` (24) + `single_name` (8) 15m fixtures, 2018-01-02 → 2023-12-31, with
volume (the runner's own loader, cached, `[RESERVED]` asserted on every bar). For each name-day:
the session open `O` (09:30 bar's open), the first-30-minute low/high (`L30`, `H30`, bars 1–2),
the prior session close `C₋₁`, the session close `C`, the 20-session-forward close; daily volume
= the sum of the day's 15m bars; **the daily PUB half-spread `hs` for that name-day from the atlas
panel** (`P["HALF"]["PUB"]`, the number `two_c` charges), names absent from the panel reported and
dropped.

## 3. The fill models — two bounds

A **buy** limit at `O` (also at `C₋₁`), working for the first 30 minutes:
- **touch** (optimistic, front of queue): filled if `L30 ≤ limit`;
- **through-δ** (conservative, behind the queue): filled if `L30 ≤ limit·(1−δ)`, δ = 5 and 10 bp.
A **sell** limit mirrored on `H30`. Fill = at the limit price.

**Three numbers per fill rule, per name-day set:**
- **fill rate**;
- **gross capture** = `hs` when filled (crossing at the open would have paid the half-spread;
  the passive fill pays none), i.e. gross capture per order = `hs × fill rate`;
- **adverse selection** = the mean signed subsequent return (open → close, and open → 20-session
  close) on **filled** days minus **unfilled** days, signed against the order (a buy that fills
  when price is falling toward it). This is the term passive-execution claims omit.
- **Net capture** = `hs × fill − adverse selection`, and as a **fraction of `hs`**.

Reported over all name-days, by **spread tercile** (the name-day's `hs`), and on the fixtures'
**volume-shock days** (daily volume ≥ 3× the trailing-20 mean — D434's `rv_x3` on this data) —
enough for fill rates and the same-day term; the 20-session term on shock days is reported with
its n and not read as more than that.

**Null:** within each name, the filled flag rotated by a random offset (200 draws): the adverse-
selection difference under no relation between fills and subsequent returns. `[SIGN]`: a synthetic
day that gaps down through the open must register a buy fill under both rules and no sell fill,
and the adverse-selection sign convention must make a buy that fills into a falling price
*positive* (a cost); the check fires when the sign is flipped.

## 4. Predictions (MODERATE for fill rates, LOW for adverse selection)

- **X-a** buy-at-open fill rates: touch **50–60%**, through-5 **35–45%**, through-10 **25–35%**;
  at `C₋₁` a few points lower on gap-up days and higher on gap-downs, net similar.
- **X-b** `hs` on these names: median **3–12 bp/side**, the top tercile **15–40** — an order of
  magnitude below B's wide third (84 bp round trip); the study is a bound.
- **X-c** adverse selection, same day, buy fills: **+3 to +10 bp** (filled days' open-to-close
  return lower than unfilled by that much); at 20 sessions **+5 to +25**, noisier.
- **X-d** **net capture 0.15–0.35 of `hs`** under through-5 over all days; **negative on volume-
  shock days** (a limit that fills on a shock day fills because the shock is running through it).
- **X-e** net capture is largest in the widest spread tercile as a fraction of `hs` (the
  adverse-selection term does not scale with the spread), 0.3–0.5.
- **X-f** the rotation null's adverse-selection p95 is within ±2 bp of zero.

## 5. What this does and does not decide

If net capture on liquid names is ≥ 0.3 of `hs`, the repo's cost models are conservative by that
fraction *on liquid names*, and a stage-2 on B may declare a passive-fill cost with that fraction
applied to its wide third **as an assumption, labelled** — the wide third is unmeasured here.
If net capture is ≤ 0.1, passive execution does not rescue any construction in this repo and the
cost models stand. Neither outcome reads a holdout or admits anything.

## 6. Not in scope

The reserved 2024+ bars; ETFs (a reference at most); any strategy. Thirty-ninth look by object;
a measurement.
