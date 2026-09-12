# D504 — stage 0: the Asian chip session into the US semiconductor day. Does Taiwan and Korea carry information the US semis' own gap has not already priced?

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
In-sample **2018-01-02 → 2023-12-29** on `etf_intraday_15m_raw` (26 bars, 09:30–16:00, regular
hours, split-adjusted, gates i1–i3 pass) and the D462 one-minute regular-hours futures fixtures;
**2024-01 onward is RESERVED on the 15-minute fixtures and is not read here.**

## 0. Why, and what has already been measured

The principal's direction of 2026-09-13, after the index-level version of this question was
answered at one tick (D494) and the hourly clock was closed (D499): make it **cross-sectional**.
Asian tech trades while US semiconductor stocks are shut, so unlike the S&P future the individual
US names cannot have priced it continuously. The literature's asymmetry (Rapach–Strauss–Zhou:
lagged non-US returns barely predict the US) is an index-level statement; the mechanism that
survives it is **slow diffusion into a sector whose market was closed**, which is the ADR
lead-lag mechanism applied to a sector rather than a single cross-listing.

**What a predictor-side measurement already establishes** (run before this record, outcome never
touched; 1,980 sessions 2016–2023, daily ETF fixture):

| | ρ with the EWT gap | ρ with the EWY gap | ρ with the EWJ gap |
|---|---:|---:|---:|
| NQ Tokyo-hours return, 19:00 → 01:00 ET | +0.52 | +0.57 | +0.50 |
| NQ − ES Tokyo-hours tilt | +0.30 | +0.25 | +0.20 |
| NQ − ES European-hours tilt, 03:00 → 08:00 | +0.05 | +0.05 | +0.02 |
| **SMH − QQQ overnight gap** | **+0.45** | +0.40 | +0.37 |

Three things follow and they shape the design. **(i)** The Asian session reaches US prices mostly
as a *market-wide* move: both NQ and ES load on it at ≈ 0.5, and the tech-versus-market tilt only
at 0.2–0.3, so a futures-only expression is a weak proxy for the chip complex. **(ii)** There is
nevertheless a genuinely **semis-specific** channel: the SMH-minus-QQQ gap loads +0.45 on Taiwan.
**(iii)** That channel is visible **in the gap**, which is exactly where it should be if the market
is efficient. So the only question worth asking is the incremental one: after the US semis have
gapped, does the day session still complete the move? This record asks that and nothing else.

**Timing is why the 15-minute fixture is used rather than the daily one.** On the daily fixture the
conditioner (an Asian ETF's opening print) and the entry (SMH's opening print) are the same instant,
which is an assumption no fixture can discharge. Here the conditioner is measured to the **close of
bar 0 (09:30–09:45)** and entry is at the **open of bar 1 (09:45)**, strictly after it.

## 1. Definitions

- Session calendar: the 1,497 sessions on which all sixteen declared symbols have 26 bars.
- **Gap of symbol s** = `close(s, bar 0, day d) / close(s, bar 25, day d−1) − 1`, in bp. Bar 25's
  close is the 16:00 print.
- **The Asian chip complex** `A_d` = the equal-weighted mean of the EWT and EWY gaps. EWT is roughly
  half TSMC; EWY carries Samsung and SK Hynix. Declared equal-weight, not fitted.
- **The US semis' relative gap** `G_d` = gap(SMH) − gap(QQQ).
- **Causal standardisation**: `z(x)_d = (x_d − mean)/sd` over the trailing 250 sessions **ending at
  d−1**. The first 250 sessions are warm-up and are not traded.
- **Disagreement** `D_d = z(A)_d − z(G)_d`: the Asian chip session moved and the US semis did not
  follow it, or the reverse.
- **The traded window** is bar 1's open → bar 25's close (09:45 → 16:00), the same window for every
  leg and every arm.
- **The cash pair**: equal dollar notional long one ETF and short the other, returns in bp of one
  leg's notional; costs charged on **both** legs, on a crossed line **and** a passive line. The
  crossed line uses the **Corwin–Schultz spread estimated from each held symbol's own 15-minute
  OHLC** over the trailing 250 sessions, never an assumed figure, with a one-cent-per-share line
  reported beside it.
- **The futures pair**: 1 MNQ against 1 MES, entry at the 09:45 bar's open and exit at the 15:59
  close on the D462 one-minute fixtures, $3 a leg, $6 the pair. The residual market exposure of a
  one-for-one micro pair is reported, and a notional-neutral variant is reported beside it.

## 2. The declared cells

One primary (R14), everything else secondary or control.

- **P1, THE PRIMARY.** Cash SMH vs QQQ, traded when `|D_d|` is in the **top decile of its own
  trailing 250-session distribution** (causal), in the direction `sign(D_d)`. About 150 trades
  in-sample. The hypothesis is underreaction: the day session completes what the gap left undone.
- **P2.** The same pair on the raw Asian signal: top decile of `|z(A)_d|`, direction `sign(A_d)` —
  the pure continuation cell, which makes no claim about what the gap has priced.
- **P3, THE SEMIS-SPECIFICITY CONTROL (six cells).** P1's rule with SMH replaced by **KRE, ITB,
  IYR, IYT, IBB, OIH**. The Asian chip complex has no mechanism into banks, homebuilders, REITs,
  transports, biotech or oil services. If these carry the same sign as SMH, the effect is Asia into
  *any* US sector and is not the chip channel.
- **P4, THE WRONG-CONDITIONER CONTROL (three cells).** P1 with `A_d` replaced by the EWG+EWU mean
  (Europe, whose session overlaps the US pre-open, so its information should already be in the gap),
  by the EWZ gap (Brazil, wrong region), and by the EEM gap (broad emerging markets, which contains
  Taiwan and Korea but dilutes them).
- **P5, THE PROP ARM.** P1's signal traded as MNQ vs MES. The prop accounts are futures-only, so
  **P1 can only ever be a personal-book component; P5 is the only prop-eligible expression**, and
  the predictor-side table above predicts it will be weaker.
- **M1, the measurement beside the trade.** OLS of the relative day-session return on `z(A)` and
  `z(G)` jointly, full sample: the incremental coefficient on `z(A)`, its Newey–West t, and the
  share of the Asian signal's total transmission that lands in the gap rather than the day.

## 3. Nulls

- **N1, exact enumerated common rotation.** Each signal is a single market-level daily series, so
  the rotation group is finite: rotate the signal by `k = 1 … T−1` sessions against the outcome
  matrix, enumerated, ≈ 1,246 offsets after warm-up. The p95's sampling error is then exactly zero
  (CLAUDE.md's rule for a one-series rotation). Reported per cell: p50, p95, and the share of
  offsets at or above the observed statistic.
- **N2, family maximum.** All twelve declared cells share each offset `k`; the family bar is the
  p95 of the per-offset maximum of the cell statistic. P1 must clear this, not only N1.
- **N3, the partner-randomised control.** The rule is kept and the *partner* leg is redrawn: SMH
  against each of the other fifteen symbols in turn. This follows the repo's rule that a random
  subset is never a control for a persistent selector — randomise the partner, not the membership.
- **N4, the wrong-window control.** The conditioner is replaced by the **same-day 14:00 → 15:45
  Asian-ETF return**, which cannot contain the overnight Asian session. It must not predict.

## 4. Decision rule (pre-registered)

- **PROCEED** to a declared stage 1 if P1's gross mean per trade is at least 1.5× its crossed
  round-trip cost, its statistic clears N1 and the N2 family p95, the hit rate exceeds 50%, the
  sign is the same in both halves (2018–2020, 2021–2023), **and** the six P3 control sectors do not
  show the same sign at the same size. A stage 1 would score the component line on both books.
- **PICK** if P1 clears N1 and its cost line but not the family bar, or if it clears everything and
  P3 shows the effect is not semis-specific. Recorded, not pursued without a mechanism test.
- **CLOSE** otherwise. Only the principal closes the avenue; the runner's verdict is a
  recommendation.
- **The forward slice is not read here.** If this line ever reads 2024+, it is read in the single
  pass already agreed for K8's promotion and the assembled book, because it reads the same sessions.

## 5. Predictions (checkable in the runner's quantities)

- **X-a** M1's incremental coefficient on `z(A)`, controlling for `z(G)`, is **small and negative**:
  between −6 and 0 bp per unit z with |t| < 2. Reason: the +0.45 gap loading says the channel exists
  and the gap is where it clears, and three prior routes here have all ended at one tick.
- **X-b** P1 trades 140–160 times, gross between −8 and +8 bp a trade, and **does not clear the N2
  family bar**. P2 is smaller in absolute size than P1.
- **X-c** The P3 sector controls scatter around zero with a spread of ±10 bp and **at least two of
  the six exceed SMH's own figure**, because twelve cells produce a best-of-twelve.
- **X-d** The wrong-conditioner cells are inside N1 on all three, and the EEM version is closer to
  SMH's result than the European one, because EEM contains Taiwan and Korea.
- **X-e** P5, the futures pair, is smaller than P1 in units of its own cost: its gross mean is under
  $6 a round trip, so the prop-eligible expression fails on cost even if P1 does not. The
  one-for-one micro pair carries residual long-NQ exposure, so its correlation with **K8** is
  between 0.1 and 0.4 rather than ≈ 0.
- **X-f** The verdict is **CLOSE**.

## 6. Files

This record · `scripts/run_d504_asian_chip_stage0.py` (`--run`, `--selftest`) ·
`data/d504_asian_chip_stage0.json` · trade files per cell · RESULT (separate). Projected runtime
under two minutes: 1,497 sessions, sixteen symbols, twelve cells, ≈ 1,246 enumerated offsets,
vectorised over offsets.

---

## AMENDMENT, 2026-09-13 — the primary is a causal RESIDUAL, not a z-difference. Found in the selftest, before any real outcome was read

**What was wrong.** §1 defined the primary conditioner as `D = z(A) − z(G)` and §0/§2 describe its
intent as the **incremental** quantity: the Asian move the US semis' own gap has not already priced.
A z-difference is not that quantity. On a synthetic panel built to the record's own hypothesis (the
Asian factor enters EWT and EWY in full, enters SMH's gap only partly, and the remainder is
delivered in SMH's 09:45 → 16:00 window) the z-difference **failed to detect a planted effect and
came out with the wrong sign**, at −24.7 bp on a plant of +3σ.

**Why.** `A` carries a large market-wide component — the predictor-side table in §0 is explicit that
both NQ and ES load ≈ 0.5 on the Asian session — and that component inflates `sd(A)`, so `z(A)`
loads *less* on the Asian factor than `z(G)` does. Their difference then points away from the Asian
direction. The z-difference also conflates two mechanisms under one sign: Asia up with semis not
following, and Asia flat with semis gapping down hard.

**The amended definitions.** Both are faithful to §0's stated intent and neither has seen an outcome:

1. **`A_rel` = mean(gap EWT, gap EWY) − gap(QQQ)** — the Asian chip complex *relative to the US
   market benchmark*, which removes the market-wide component the predictor-side table identified.
2. **`resid_d` = `A_rel_d` − (a + b·`G_d`)**, with `a`, `b` from an OLS fitted on the trailing 250
   sessions **ending at d−1**, so the fit never sees day d. This is "the Asian move not explained by
   the US semis' own relative gap", which is what §0 (iii) says the only question worth asking is.

**P1 is now**: trade when `|resid|` is in the top decile of its own trailing 250-session
distribution, in the direction `sign(resid)`. **The original z-difference is retained as a declared
secondary cell `P1_z`**, so the record shows both and nothing is hidden. Every control, null,
decision rule and prediction in §2–§5 is unchanged and now applies to the amended `P1`; the P4
wrong-conditioner cells use the same residual construction with their own region in place of Asia.

**Prediction X-a is restated in the amended quantities** (it referred to `z(A)`): the incremental
coefficient on `z(A_rel)` in M1, controlling for `z(G)`, is between −6 and 0 bp per unit z with
|t| < 2. X-b to X-f stand as written.

**How it was caught.** The known-answer check `[F]` in `--selftest` requires the planted cell to
clear its own null while the unplanted and wrong-sector cells do not. It failed on the z-difference.
CLAUDE.md: *a self-test that cannot fail is worse than none* — this is the case it was there for.
