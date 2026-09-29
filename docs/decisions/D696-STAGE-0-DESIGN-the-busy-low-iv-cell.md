# D696 — STAGE 0 DESIGN: is D694's worst cell (busy realised range, low implied-to-realised) real, or the worst of six by chance? A search-adjusted null, a mechanism read, and a prediction on a break the grid never saw (ES and NQ)

*2026-09-29.*
- *The principal asked why the lead could not be investigated in-sample, then: "Yes write the pre-reg and run it".*
- *Numbered D696: D695 is the highest number on every branch and in every commit subject, and the other session was
  told before writing.*
- ***Committed alone, before its runner exists.***
- *In-sample, 2018-01-09 → 2025-02-28. The vault is not read. Dealer gamma (GEX) is SqueezeMetrics', read to
  < 2025-03-01, and credited.*

## 0. Where this comes from

**The lead.** [D694](D694-STAGE-1-RESULT-not-supported-iv-adds-nothing-to-the-break.md)'s grid split D668's E4 plain
break by D672's compression tier (terciles) and D691's walk-forward IV/RV percentile (halves). The worst cell on both
roots was **X = ctier ≥ 2/3 and p_iv < 1/2**: busy recent realised range that the options market does not price
forward.
- ES: −7.37 bp gross (85 trades);
- NQ: −14.71 bp (99).
- Its neighbour **Y = ctier ≥ 2/3 and p_iv ≥ 1/2** earned +0.59 (280) and +6.61 (270).

**Why it cannot be read as it stands.**
- X was noticed after the run, as the worst of six cells a root. The worst of six noisy means is always bad by some
  margin.
- ES and NQ are highly correlated day to day, so "worst on both" is closer to one observation than two.
- The in-sample window can no longer *confirm* this cell. **It can still investigate it:** measure how unusual the
  search result is, find the mechanism, and test the cell on a trade the grid never saw.

**A correction this record makes to D694.** D694 §4, FINDINGS §99 and AITODO said the in-sample window is "spent for
any IV split of the break". The accurate statement is **spent for confirming one, still open for investigating one.**
The RESULT appends that correction to D694.

## 1. Objects (unchanged from D694; nothing new is fitted)

- **Labels, per session:**
  - `ctier`: D672's walk-forward compression tier;
  - `p_iv`: the walk-forward percentile of D691's ivrv = ln(IV/RV20).
  - Both are exactly D694's, read from the same cached bundle. That bundle is keyed on the D694 runner, every
    imported module and every fixture.
- **The six cells:** ctier terciles (< 1/3, 1/3–2/3, ≥ 2/3) × p_iv halves (< 1/2, ≥ 1/2). **X** = tercile 3 with low
  p_iv; **Y** = tercile 3 with high p_iv.
- **Trade 1, the one the grid was read on:** D694's E4 plain break, one micro, gross at the level, in bp.
- **Trade 2, never split by either label:** D663's opening-range break.
  - The range is the 09:30–09:59 high and low.
  - The break is the first one-minute close beyond it, 10:00–11:29.
  - Entry is at the close of the next bar.
  - **F** = D·ln(close 60 minutes after the entry bar / entry)·1e4 bp, with no stop (D662/D663's `find_break` and
    `follow`).
  - D665 reported it at ES +0.31 and NQ −0.66 bp gross on 2016–2025-02. No record has split it by ctier or IV.
  - Its days overlap trade 1's, so it is not an independent sample. It has a different clock, entry and exit.
- **The window:** D694's (sessions with finite ctier, p_iv, D671's forecast tier and M1 forecast; 2018-01-09 →
  2025-02-28).

## 2. The tests

### A. Is X more than the worst of six? (trade 1)

**The statistic.**
- For each root r and cell c: z_r(c) = mean gross in c / (sd_r / √n_c). sd_r is the SD of root r's window B0 gross,
  fixed from the actual trades so the scale does not move under rotation.
- **S = min over the six cells of (z_ES(c) + z_NQ(c)) / √2**, the jointly worst cell.
- The observed S is taken at the actual labels. The runner asserts that its argmin is X.

**A1, the search-adjusted null (the whole label).**
- Rotate each root's finite ivrv series by k positions, the **same k on both roots**, for every k from 21 to
  min(n_ES, n_NQ) − 21.
- Re-tier p_iv, rebuild both grids, and recompute S. ctier and the trades are held.
- **Pass: the observed S lies below the exact 5th percentile of the enumerated S_k.** The group is finite, so the
  percentile's SE is 0.

**A2, the same statistic under D694's ingredient rotation.** Only the part of ln IV not explained by ln RV20, rv5,
on_range and ln(ATR/price) is rotated, with the rest held. It is also enumerated, with the same k on both roots.
- **Passing A2 would mean the cell is IV information. Failing it (after passing A1) means the cell is the label's
  realised part.**
- A2 labels the verdict. It does not gate it.

### B. The mechanism (trade 1, descriptive, with readings declared now)

For X, Y and the rest of B0, per root:
- the exit reason shares (trailing or initial stop, against the 15:59 close);
- **MFE and MAE** from the bar after entry to 15:59, in bp in the trade's direction;
- **the hold-to-close move** (entry → 15:59 close, direction-signed, no stop);
- **the share of the day's RTH range already made before entry:** (high − low up to and including the entry bar) /
  (the day's high − low);
- the entry minute;
- the day's ln(range/ATR20).

**Readings (per root):**

| reading | condition |
|---|---|
| **REVERSAL** | X's mean hold-to-close move < 0, with one-sided HAC t ≤ −2 |
| **SPENT RANGE** | not REVERSAL, and X's mean MFE is below Y's (Welch t ≤ −2) |
| **NEITHER** | otherwise |

### C. The prediction on trade 2 (the cell is fixed in advance, so there is no search)

- **C-i (literal):** X is the jointly worst of the six cells for D663's F, by the same summed z.
- **C-ii (gating):** X's joint z for F, (z_ES(X) + z_NQ(X))/√2 with sd_r from each root's window F, lies **below the
  exact 5th percentile** of the same statistic for the fixed cell X under A1's whole-label rotation. The offsets are
  the same.

### Verdict

| verdict | condition |
|---|---|
| **SEARCH ARTEFACT** | A1 fails. The lead is dropped. |
| **LEAD SURVIVES** | A1 and C-ii pass. The cell has earned a pre-registration on unseen data (the vault or forward recording), on the principal's word, and A2 says whether it is IV information or realised. |
| **CONSTRUCTION-SPECIFIC** | A1 passes and C-ii fails. The cell is a property of E4's trailing stop, not of the day. Not taken forward. |

B's reading is reported with every verdict.

## 3. Runner assertions (each shown to raise in `--selftest`)

- **Known answers:**
  - D694's grid is reproduced cell by cell from the bundle (n and mean gross to 1e-9);
  - D663's morning F is reproduced on D663's own frame: ES 2,138 breaks, mean +0.30905 bp; NQ 2,118, −0.65576 (to
    1e-9);
  - trade 1's at-level gross, re-derived bar by bar for the mechanism read, equals the bundle's.
- **Lag:** the labels come from D694's audited bundle. MFE, MAE and hold-to-close read only bars after the entry bar,
  and a canary that includes the entry bar must raise. The pre-entry range share reads only bars up to the entry bar,
  and a canary that reads one bar past it must raise.
- **Sign:** a favourable synthetic path gives a positive MFE and hold-to-close for a long, and the same for its
  mirrored short.
- **Right quantity:** F is measured from the entry, not from 10:00 (D663's own check). A2's rotation acts on the
  residual, not on ln IV.
- **The null:**
  - offset 0 reproduces the observed S and C's statistic exactly;
  - chunk == whole across processes, bit for bit;
  - on synthetic data, rotating an injected label destroys it.

## 4. Speed

- The bundle, bars and frames are cached (D694's).
- Each offset is two re-tiers and three grids. The rotations fan out over processes on `items[i::N]`.
- **Projected under 10 minutes** (D694's rotations took 71 s a root). Measured and stated before launch.

## 5. Power, roughly (stated before the run)

- **A1:** if the six joint z's were independent standard normals, the 5th percentile of their minimum would be about
  −2.6.
  - The observed cells suggest z ≈ −1.9 (ES) and −3.0 (NQ), so a joint S ≈ −3.5.
  - The rotation keeps the labels' persistence and the cells' correlation, so its spread may be wider than that
    approximation. That is the point of enumerating it.
- **C:** X holds about 7–8 % of breaks, so about 130 of D663's roughly 1,700 window breaks a root.
  - With F's SD of 33 (ES) and 45 bp (NQ), each root's cell mean has an SE of about 3–4 bp.
  - A cell as bad as trade 1's would clear C-ii. One a third as bad would not.

## 6. Predictions

1. **A1 passes:** X is beyond the worst-of-six by chance.
2. **A2 fails:** the cell is the label's realised part, as D694's coiled cell was.
3. **B reads SPENT RANGE on both roots,** not REVERSAL.
4. **C-ii fails:** the cell belongs to E4's trailing stop through the afternoon, and a 60-minute morning hold does not
   see it.

## 7. Routing

- **SEARCH ARTEFACT:** D694's lead is struck in FINDINGS §99 and AITODO.
- **LEAD SURVIVES:** a separate pre-registration for unseen data, on the principal's word. It states the vault's
  expected count first: X is about 7.6 % of E4 breaks, so about 18 a root in 2025-03 → 2026-09-18. It also states whether
  forward recording is the only route with power.
- **CONSTRUCTION-SPECIFIC:** recorded, and not taken forward.
