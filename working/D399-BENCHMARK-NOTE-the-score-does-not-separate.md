# D399 BENCHMARK NOTE — four constructions beat the incumbent, none clears its own null, and the metric is why

**Status:** A NOTE, in `working/` because it is a live methodological problem the principal owns.
**Nothing here is admitted (R15). No holdout read. Nothing retired.**
**Date:** 2026-09-09 · Four parallel agents, each on a different construction family.

---

## 1. The raw scoreboard, and it looks like progress

Ground truth: `data/d399_drawn_ground_truth.json`, seven lines the principal drew on GME bars
2429–2689. Score: `AGREEMENT × RECALL^0.25` (`scripts/d399_score_against_drawn.py`).

| construction | defensible cell | best of sweep | cells searched |
|---|--:|--:|--:|
| **branch E** — dynamic windows (incumbent) | **0.236** | — | — |
| warm-started windows | 0.28 | 0.51 | 128 |
| chartist two-pivot line | 0.324 | 0.404 | 195 |
| piecewise segmentation | — | 0.478 | 672 |
| **convex hull envelope** | — | **0.513** | 66 |

**Every family beat the incumbent, and the hull more than doubled it.**

---

## 2. And then two of them ran the null, independently, and it holds none of them

An **exact time rotation of the fitted gradient series** — all 259 offsets enumerated, so the p95's
standard error is exactly 0 (CLAUDE.md's enumeration escape, and D361's `ROT`).

| construction | observed | rotation p50 | **rotation p95** | verdict |
|---|--:|--:|--:|---|
| branch E | 0.2363 | — | 0.3015 | **inside**, 70th pct |
| segmentation, best of 672 | 0.4775 | 0.141 | **0.5384** | **inside**, 86th pct |
| its top ten cells | — | — | — | **all inside**, 82–88th |
| convex hull, best of 66 | 0.5133 | 0.294 | **0.534** | **inside**, margin −0.021 |
| hull, other top cells | — | — | — | inside by −0.078 to −0.227 |

**Two agents, two different construction families, two independently written nulls, and the p95
lands at 0.534 and 0.5384. Nothing tested clears it.**

Excluding near-identity offsets (|offset| ≥ 21) does not rescue the hull: p95 0.535.

---

## 3. The metric is the problem, and one number says it

> **The hull's rotation p50 is 0.294. The incumbent construction's actual score is 0.236.**
>
> **A randomly time-shifted copy of the hull's own gradients beats the real branch E, at the
> median, half the time.**

That is not a statement about the constructions. It is a statement about the score:
**`AGREEMENT × RECALL^0.25` is mostly satisfied by getting the DISTRIBUTION of slopes right, not
by getting a slope right AT THE RIGHT BAR.** Rotating destroys all placement information and keeps
the marginal — and the marginal is worth ~0.29 of a possible ~0.53.

**The effective sample is SEVEN DRAWN LINES, not 260 bars.** Per-bar averaging makes 260
correlated observations look like 260 independent ones, which is what lets a rotation score so
well and what makes every margin here fragile.

---

## 4. What the constructions did establish, which is not nothing

**These survive the metric's failure, because they are mechanisms rather than scores.**

- **The warm start's mechanism is real and monotone.** Carrying pivots into a new window collapses
  the blind head **35.5 → 4.5 bars** and lifts mean recall **0.227 → 0.713**, with agreement
  *rising* (0.305 → 0.347), monotonically across all 32 cells per level. `carry=0` reproduces
  branch E bit-identically and that guard fires on `carry=2`.
- **The non-piercing chartist line wins only as a LIVE REDRAW.** Refreshed on each new confirmed
  pivot it beats the naive most-recent pair **9 of 9** matched cells; *frozen until broken* it is
  the worst object in its grid (0.099–0.116 against 0.188–0.214). A long unpierced line, once
  latched, is stale.
- **The literal "hull edge at the most recent vertex" is the WORST hull rule** (0.086), because
  bar `t` is always its own hull vertex, so that edge re-pivots every bar. What works is the
  **matured** edge, confirmed ≥5 bars ago — and it wins at every window and every gate, so it is a
  family rather than a lucky cell.
- **Segment length is nearly decoupled from score.** Segmentation's best cell runs 16-bar segments
  against the human's 46; the one cell near 46 scores lower.
- **Where the fits fail is consistent across families:** the steep, long, pivot-rich legs are
  fitted well (agreement 0.76–0.88), and the shallow −0.0011 support line scores **0.000**, the
  11-bar line is never seen, and resistance 87–138 comes out the **wrong sign**.

---

## 5. What is owed before any of this is ranked again

1. **The score must be placement-sensitive, or scored against its own null.** The programme's own
   habit everywhere else is to report the excess over a null rather than the raw statistic; this
   benchmark should do the same — `(observed − p50) / (p95 − p50)`, or a per-LINE score over the
   seven, not a per-bar mean over 260.
2. **One window on one symbol is not a benchmark.** Seven lines is the sample. More drawn windows,
   on more names, is the only thing that makes any of these margins readable.
3. **Every number in §1 is a best-of-N** — 66, 128, 195, 672 cells — and none has a best-of-N
   floor. Even with a fixed metric they would need one.

**No construction is retired and none is admitted. The ranking in §1 is not currently
interpretable, and that is the finding.**
