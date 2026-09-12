# D413 ADDENDUM 3 — cell 2's edge decays monotonically; its level gap does the opposite

**EXPLORATORY, on data D413 has already spent. Clears nothing, admits nothing.** Requested by the
principal: a holding-period sweep on cell 2, `deep · clean · hi`, to see whether the edge decays
monotonically.

**The cell is fixed exactly as [ADDENDUM 2](D413-ADDENDUM-2-the-cost-estimate-was-wrong-and-path-efficiency-splits-the-effect.md)
reported it and is not re-tuned here:** `REV ≤ −2.47%`, `EFF > 0.2367`, `DV > $44.4M`.

---

## 1. The sweep

```
   h       n    gross    +-     SE   median   win%  bp/bar      LVL      gap    +-   cost    cov     net
   1  26,052    +6.31  1.71   +3.7    +6.86  51.45   +6.31    +3.51    +2.79  1.74   22.8   0.28  -16.52
   2  26,047   +15.73  2.45   +6.4   +15.50  52.38   +7.87    +7.72    +8.01  2.49   21.4   0.74   -5.64
   3  26,041   +22.63  2.98   +7.6   +19.11  52.35   +7.54   +13.72    +8.91  3.03   21.5   1.05   +1.08
   4  26,037   +28.74  3.41   +8.4   +22.20  52.38   +7.19   +17.54   +11.20  3.47   21.6   1.33   +7.15
   5  26,024   +30.26  3.74   +8.1   +21.65  52.16   +6.05   +15.11   +15.15  3.80   21.6   1.40   +8.66
   6  26,015   +27.71  4.08   +6.8   +23.32  51.93   +4.62   +10.54   +17.17  4.15   21.7   1.28   +5.99
   7  26,011   +21.40  4.46   +4.8   +20.42  51.62   +3.06    +1.95   +19.45  4.54   21.8   0.98   -0.40
   8  26,002   +19.77  4.73   +4.2   +20.89  51.49   +2.47    +0.66   +19.12  4.81   21.8   0.91   -1.99
   9  25,995   +11.09  5.12   +2.2   +15.71  51.00   +1.23    -8.00   +19.10  5.22   21.9   0.51  -10.76
  10  25,988    +7.29  5.37   +1.4    +8.40  50.48   +0.73   -12.00   +19.29  5.47   21.9   0.33  -14.58
  12  25,961    -7.32  5.91   -1.2    +7.42  50.44   -0.61   -21.17   +13.85  6.01   22.1  -0.33  -29.40
  15  25,936   -11.32  6.71   -1.7    +9.31  50.43   -0.75   -23.77   +12.45  6.83   22.1  -0.51  -33.45
  18  25,898   -10.52  7.15   -1.5    +7.65  50.31   -0.58   -17.15    +6.63  7.27   22.3  -0.47  -32.78
  21  25,859    -6.98  7.53   -0.9    +2.54  50.06   -0.33    -8.26    +1.28  7.66   22.5  -0.31  -29.44
  25  25,801    -9.08  8.16   -1.1    +5.65  50.20   -0.36   -10.53    +1.44  8.30   22.7  -0.40  -31.75
  30  25,736    -2.30  8.83   -0.3    +0.00  49.97   -0.08    -0.37    -1.93  8.97   22.8  -0.10  -25.08
```

---

## 2. IT DOES DECAY MONOTONICALLY — twice

```
per-bar edge   h=2 -> h=15   TEN consecutive non-increasing steps   +7.87 -> -0.75
win rate       h=4 -> h=21   TEN consecutive non-increasing steps   52.38% -> 50.06%
```

**The per-bar edge falls smoothly from +7.87 bp/bar and crosses zero at about h = 11.** Past h = 15
it oscillates between −0.75 and −0.08, which is entirely inside one standard error at those
horizons — a dead signal wobbling around zero, not a broken profile.

**The win rate decays over the same span**, 52.38% → 50.06%, reaching the coin-flip level at exactly
the horizon where the per-bar edge reaches zero. **Two independently-computed statistics agreeing on
where the signal ends is the strongest internal-consistency check in this line.**

**`h = 1` is the one exception and it is informative:** per-bar +6.31, *below* h = 2's +7.87. The
first bar after entry underperforms, which is what an entry taken mid-move looks like — the touch
bar's close is not the bottom of the move.

**A note on my own instrument.** The first version of this check asked "is the profile monotone from
h = 1?" and answered **no** for all three curves, because a single upward wobble of a tenth of a
basis point at h = 18 — far inside its 7.15 bp standard error — fails a strict test. That question
was the wrong one. It now reports the longest monotone run, which is what "does it decay" actually
means.

---

## 3. THE LEVEL'S OWN GAP DOES THE OPPOSITE, AND THE REASON MATTERS

```
gap  +2.79  +8.01  +8.91 +11.20 +15.15 +17.17 +19.45 +19.12 +19.10 +19.29 +13.85 ...
```

**It RISES to h = 7, plateaus at ~+19 bp through h = 10, and only then decays.** Its longest monotone
run is four steps, from h = 10.

**And the cause is the control collapsing, not the treatment improving:**

```
real  +30.26 (h=5)   +11.09 (h=9)    +7.29 (h=10)   -11.32 (h=15)
LVL   +15.11         -8.00          -12.00         -23.77
```

**The gap widens because `LVL` falls faster than the real cell does.** That is a statement about the
level carrying information over a longer horizon than the tradeable edge survives — **and it is not
tradeable, because you cannot trade the gap.** At h = 10 the gap is +19.29 bp while the cell itself
makes +7.29 gross against a 21.9 bp cost.

**So the two curves answer two different questions, and they disagree about the right horizon:**
the *information* in the level peaks around h = 7–10; the *money* peaks at h = 5.

---

## 4. The tradeable window

**Net is positive only for `h = 3` to `h = 6`**, peaking at **h = 5: coverage 1.40×, net +8.66 bp**.
`h = 7` is already −0.40.

**`h = 5` was the horizon declared in advance in `6374e5c`**, before any of this was measured. It
being the peak is mildly reassuring rather than a post-hoc choice — **though the cell it is measured
in was selected post-hoc**, which is the multiplicity that still stands.

---

## 5. What this does not change

Every caveat from ADDENDUM 2 stands: eight cells examined and one quoted; splits at medians computed
from the same spent data; coverage above 1.0× on the **neutral** spread only (0.80× on the event-bar
estimate at h = 5); no execution model; no out-of-sample test; no time rotation; and the effect
concentrated in 2010–2013 in a pooled table.

**One further caveat specific to this file: the horizons are not 16 independent tests.** The cell
membership is fixed at the touch bar, so every row reuses the same ~26,000 events and the errors are
heavily correlated across `h`. **A monotone profile here is one population behaving smoothly, not
ten confirmations.**

**Disposition is the principal's.**

---

**Evidence:** `data/d413_cell2_hold.json`. Runner `scripts/run_d413_cell2_hold.py`.
