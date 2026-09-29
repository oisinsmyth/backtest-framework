# D663 STAGE 0 RESULT — NOT SUPPORTED on either root: measured on the SPX options book, ES breaks do not carry further when dealers are short gamma (D662's post hoc hint does not replicate), NQ's do not either on its own book or on SPX's, and the cash market's flow into the break is not multiplied by gamma. All five written predictions held

*2026-09-29.*
- *One run of `scripts/stage0_d663_per_root_gamma_break.py` (`0f6f9e4`) under D663's design (`b4d0d3d`), 0.6 min.*
- *In-sample 2016-01-04 → 2025-02-28 through the sealed loader. The Sierra files were read only before 2025-03-01
  (asserted), and SqueezeMetrics GEX only from the row dated before each session (asserted by a second path).*
- *Output: `data/stage0_d663_per_root_gamma_break.json`, plus a post hoc correction (§4),
  `data/stage0_d663_correction.json`.*
- ***Dealer gamma (GEX): SqueezeMetrics**, used under the principal's written permission
  ([licence note](../research/licences/squeezemetrics-dix-gex.md)). No per-date series is in either file (guarded).*

**Audits.** The selftest's nine audits fired on broken inputs. In the run:
- the break equalled `b3_trade`'s on every session of both roots;
- F differs from F measured from 10:00;
- every OLS equalled statsmodels';
- the signed b₃ differs from the unsigned b₃;
- the GEX lag audit and the vault-cut assertion held.

## 1. Before the run proper

**The first `--run` (07:07) crashed** inside the process pool, on an empty secondary-shock column. Nothing was
written, and no statistic was returned or seen. The cause was Gate F, read on inputs only:
- **UVOL/DVOL are not cumulative within the session:** 0% of sessions are monotone.
- They are the volume of stocks currently advancing or declining, which moves as stocks cross unchanged. They are a
  breadth *state*, not a flow.
- The design (§2) drops such a shock before any outcome is read. The runner had scheduled its job anyway. `0f6f9e4`
  skips it, and the run proper followed.

**The secondary shock is therefore dropped** for both roots. The primary TICK-SP / TICK-NQ pass Gate F: median
coverage 100%, with 4 of 2,344 sessions under 90%. The shock is defined on 2,135 of 2,138 ES breaks and 2,114 of 2,118
NQ breaks.

## 2. Results (primary family H1, secondary family H2; Holm within each, one-sided)

| cell | coefficient (HAC t) | rotation rank; null p50, p95 | Holm p | midday placebo (t) | vault power | verdict |
|---|---|---|---:|---|---:|---|
| **H1-ES** (break × SPX short gamma) | **b₁ +0.22 (0.55)** | 0.73; −0.02, +0.64 | 0.58 | +0.23 (0.66) | 4% | **NOT SUPPORTED** |
| **H1-NQ** (break × NQ own-book short gamma) | **b₁ −1.54 (−0.90)** | 0.22*; +0.02, +3.20 | 0.82 | +1.37 (1.03) | 1% | **NOT SUPPORTED** |
| H2-ES (TICK-SP flow × SPX gamma) | b₃ −0.09 (−0.25) | 0.38; −0.00, +0.56 | 0.60 | +0.31 (0.92) | 2% | NOT SUPPORTED |
| H2-NQ (TICK-NQ flow × own gamma) | b₃ +1.90 (1.13) | 0.81*; +0.09, +3.33 | 0.26 | +0.56 (0.44) | 7% | NOT SUPPORTED |
| *control:* H1-NQ on SPX gamma | b₁ −0.08 (−0.59) | 0.32* | — | +0.12 (1.28) | — | — |
| *control:* H2-NQ on SPX gamma | b₃ +0.08 (0.62) | 0.71* | — | +0.12 (1.59) | — | — |

\* From the post hoc correction (§4).

**ES, read in full:**
- **The re-measurement does not replicate D662's post hoc hint.** On the carried ES book, D662's break × gamma slope
  had t 2.30. On the SPX book, the book that actually carries dealer gamma, it has t 0.55.
- The midday placebo's slope (+0.23) equals the morning's (+0.22). There is nothing specific to the opening break.
- It is +0.33 without February–April 2020.
- **8 of 10 years are positive, against its own null's p50 of 5 and p95 of 8:** at the edge, not beyond it.
- By era: +0.07 before 2022-05-16 and +1.16 after, an era hint on a null slope.
- **The size claim:** β 0.09, 90% CI (−0.31, 0.48), wholly below 0.5. That is a **powered null against the
  square-root law's push** (mean predicted push 5.2 bp), with the GEX unit caveat (D663 §2).
- MDE b₁ 1.15.

**NQ:**
- The own-book slope has the wrong sign (−1.54), and on SPX gamma it is flat (−0.08).
- NQ's own-book MDEs are 4–5× ES's, because the book is thin (D663 §2's weak link).
- H2-NQ's +1.90 is inside its null.

**F** (the 60-minute follow-through, bp):

| root | n | mean | median | sd | trimmed | ex-top 1% | ex-bottom 1% |
|---|---:|---:|---:|---:|---:|---:|---:|
| ES | 2,138 | +0.31 | +0.91 | 33.4 | +0.34 | −0.97 | +1.62 |
| NQ | 2,118 | −0.66 | +0.58 | 44.6 | −0.29 | −2.03 | +1.09 |

## 3. Predictions (D663 §8): all five held

1. H1-ES had the right sign and was NOT SUPPORTED.
2. H1-NQ was NOT SUPPORTED.
3. H2 was NOT SUPPORTED for both roots.
4. The placebos were inside noise.
5. There was no pass, so no vault power to exceed. Every cell's vault power is 1–7%.

## 4. Post hoc correction (`scripts/diag_d663_correction.py`; no verdict changes)

1. **NQ's rotation nulls were empty.** NQ's own-book g is missing on 58 sessions. The runner rotated g over the full
   calendar, so every rotated slope was NaN: the run's ranks read 0.000, with NaN p50/p95. Recomputed on the finite-g
   calendar: H1-NQ rank 0.22, H2-NQ 0.81, the midday ranks 0.82 and 0.63. ES has no missing GEX, so its nulls are
   unaffected.
2. **The pre-registered control "H1-NQ with SPX GEX" did not run.** `0f6f9e4`'s Gate F skip wrapped it by mistake. It
   was run here: b₁ −0.08 (t −0.59), rank 0.32; H2 on SPX gamma +0.08 (t 0.62).
3. **Neither defect touches a verdict.** Every cell fails at the Holm step, before the rank is consulted.

## Routing (D663 §6)

**Nothing is SUPPORTED:**
- The break × gamma line closes for both roots: the gamma mechanism's fifth null here (D581, H-O6, S-H, D662, D663).
- **D662's post hoc ES hint was measurement- and selection-specific.** It does not survive the SPX book.
- **With it, the opening line's closure is recommended:**
  - D658 H-O2 (slot 7);
  - D652 v2 without its vault look (slot 9 never taken).
- **What stays on file:**
  - the Sierra market-statistics fixtures: TICK-SP and TICK-NQ are clean to 2014. UVOL/DVOL are advancing/declining
    state, not flow, and are noted for any later reader;
  - the SqueezeMetrics GEX series under its licence;
  - D661's prize-sizing method.
