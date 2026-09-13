# D515 — is the MACD signal real on the failing roots but **slower** than a seven-hour window?

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**2016-01-04 → 2023-12-29 on the eight gated roots. No 2024+ slice is read.**

## 0. The question, and why it is not idle

The principal's hypothesis, after D513 and D514: the MACD signal may be **real on every root**, and the
roots where the arm loses may simply be ones where **price takes longer to move**, so a seven-hour
day-session window truncates the trade before the edge arrives.

**Three things on the record make it worth testing rather than dismissing.**

1. **D514's ladder points that way.** Gross rises monotonically with holding length on three roots of
   four, and on NQ it is **still rising at M = 5**, which `max_hold_available` shows is the ceiling
   the window allows. The construction sits at a corner imposed by the flatten, not at an optimum.
2. **D484 never looked past five bars.** Its declared grid was `holds = (1, 2, 3, 5)`. Everything
   beyond that is unmeasured, and the arm's window is about seven hourly segments.
3. **D484's own best cell was CL at H = 5** (edge 0.0337 in σ units) — and CL is one of the three
   roots where the arm's gross is *negative*. A root can carry a measurable signal at one horizon and
   lose money at the arm's horizon, which is precisely the principal's point.

**And two things argue against it, which this record must be able to detect.**

4. **The daily variance ratio is below 1 on seven of eight roots** (D502; NQ above 1 in 0.4% of
   sessions). At the daily horizon these markets are mildly mean-reverting, so an edge that needs
   more than a session is swimming upstream.
5. **The overnight reverses.** FINDINGS §70 measured next-hour reversal on the US off-hours clock at
   β −0.03 to −0.04 on the index roots. Any horizon past about six bars crosses that.

**So the coherent alternative to the principal's hypothesis is:** within-session momentum builds to
roughly the window's length and the overnight then gives it back, in which case the window is
truncating at about the right place rather than too early. **This record separates the two.**

## 1. What is measured

**No trading machinery, no cost, no flatten, no day-session constraint.** This is a signal
measurement, so that "is the signal real" is answered separately from "can this book trade it" —
the mistake D513 made by conditioning a construction that was already losing.

- **The signal** is the frozen AGREE state — the log Impulse MACD (34/9) and the plain log MACD
  histogram (12/26/9) agreeing in sign, zero otherwise — evaluated at **every hourly segment** of the
  continuous 23-segment series, exactly as `d506_macd_breadth.build_root` produces it.
- **The forward return** at horizon `H` is the log return from the **open of segment t+1** to the
  **open of segment t+1+H**, so it respects the decide-at-close, fill-at-next-open convention and
  never reads the bar the signal was computed on.
- **The statistic is D484's `edge_sigma`** = `mean(signal × forward) / sd(forward)`: dimensionless,
  scale-free, and therefore comparable across roots whose ticks differ by 60×. Imported, not
  re-implemented.
- **Horizons** `H ∈ {1, 2, 3, 5, 8, 13, 21, 34}` hourly segments. The arm's window is ~7, one session
  is 23, so the ladder spans well inside the window to well beyond a full day.
- **Roots**: all eight gated roots.

## 2. The primary statistic, one (R14)

**The pooled `edge_sigma` over the three signal-dead roots — YM, CL and 6E — at H = 13**, a horizon
pre-specified as roughly twice the arm's window and safely beyond it.

**The full 8 × 8 ladder is reported**, along with, per root: the horizon at which `edge_sigma` peaks,
and the number of effectively independent observations `n_eff ≈ n / H`, because overlapping forward
windows inflate a naive count and every figure must be read against it.

## 3. Nulls

- **N1, exact enumerated rotation of the signal** along the **session** axis, per root and horizon,
  re-computing `edge_sigma` at every offset. Rolling whole sessions preserves each session's intraday
  signal shape and the signal's autocorrelation — a smoothed signal is rotated, never shuffled.
- **N2, family maximum** over the **64 cells** (8 roots × 8 horizons) under common offsets. Any cell
  claimed must clear this, not only its own null.

## 4. Decision rule (pre-registered)

- **SLOW-BUT-REAL** if the primary is positive and clears N1 **and** the N2 family p95, **and** the
  three signal-dead roots peak at a horizon longer than the arm's window. The principal's reading
  would then be confirmed and the right follow-up is a personal-book construction, since the prop
  flatten forbids the hold.
- **TRUNCATED AT ABOUT THE RIGHT PLACE** if `edge_sigma` peaks at or below ~6 segments on most roots
  and decays or turns negative beyond it. The window is then not the problem and the overnight is
  giving the move back.
- **NO SIGNAL AT ANY HORIZON** if the three roots are inside their nulls at every H.

## 5. Predictions (checkable in the runner's quantities)

- **X-a** Pooled `edge_sigma` on the three signal-dead roots at H = 13 is **between −0.01 and +0.01**
  and does **not** clear N1. The signal does not arrive late on them.
- **X-b** `edge_sigma` **peaks at H ≤ 8 on at least six of the eight roots**, consistent with
  within-session momentum that the overnight then gives back.
- **X-c** NQ is positive at **every** horizon, largest between H = 3 and H = 8, and **declines** by
  H = 34 without turning negative.
- **X-d** At H = 21 and H = 34, which straddle a full session, the pooled edge across all eight roots
  is **below its value at H = 5**, because the crossed overnight reverses (FINDINGS §70) and the daily
  variance ratio is below 1 (D502).
- **X-e** The 64-cell family p95 lands between **+0.02 and +0.05** in σ units, and **at most two cells
  clear it** — one of which is on NQ.
- **X-f** The verdict is **TRUNCATED AT ABOUT THE RIGHT PLACE**.

## 6. Files

This record · `scripts/run_d515_horizon_ladder.py` (`--run`, `--selftest`, importing the frozen
signal from `d506_macd_breadth` and `edge_sigma` from `d484_offdiagonal_and_macd`) ·
`data/d515_horizon_ladder.json` · RESULT (separate). Runtime under five minutes.
