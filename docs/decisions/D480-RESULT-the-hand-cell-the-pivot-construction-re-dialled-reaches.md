# RESULT D480 — the construction rebuilt against the hand-drawn lines: the swing envelope loses, and the pivot construction re-dialled reaches the eye on gradient and most of the way on coverage

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D480-RESULT-the-hand-cell-the-pivot-construction-re-dialled-reaches-the-eye-on-gradient-and-the-swing-envelope-loses.md`. The H1 above is the full title.*

*Generators `scripts/d480_swing_envelope.py` (the swing envelope, with its dial sweep) and
`scripts/d480_hand_cell.py` (the winning cell); scorer `scripts/d478_score_hand_lines.py`; cards
`data/d480_swing_scorecard.json`, `data/d480_hand_scorecard.json`, `data/d478_hand_scorecard.json`
(the four earlier constructions, re-scored); target `data/d478_hand_drawn_lines.json`; page
"The hand cell against the hand lines". No trade was run, by the principal's instruction.*

## 1. What the hand lines obey (three more facts than the scorecard had)

Measured on the 140 lines: anchors sit a median **4.4% outside the wicks** (2–8%); the wicks
never pierce a line between its anchors; while a line is kept the deepest wick pierce is 0 at the
median, 3.5% at the third quartile, 7% at the ninth decile. The first anchor is a **major** swing
(the extreme of ±7 bars, 13% reversed off by the draw bar), the second a **minor** one (±3 bars,
5% reversed), drawn a median 1 bar after it. Ends: **45% breaks** (the close a median 4.4%
through the line), **40% replacements** (a same-kind line drawn the same bar), **15% drift**
(price 26% from the line, no touch for ~22 bars).

## 2. The swing envelope, built to those rules, loses

A zigzag-anchored envelope (major and minor reversal thresholds, a 4% margin, fixed lines,
break / replace / drift ends, `d480_swing_envelope.py`) was swept over 90 then 96 dial lines
against the card. Its best: recall 63–66%, **sign 73–76%**, gradient error 21–42%/yr, overstay
37–39%; the two-scale version reached 79–88% recall with sign falling to 55–75%. Two-point lines
through minor swings carry the swing's noise into the gradient. The construction whose
gradients matched the principal's was D399's envelope over several confirmed pivots (sign
88–92%), so that estimator was kept and the rules around it re-dialled, each change scored.

## 3. The card, corrected, and the cell

One correction to the scorer first: overstay had counted the 40% of the principal's ends that
were replacements, where a construction still showing a line five bars later agrees with the
principal; it now counts only breaks and drifts (35 ends). The base cell reproduced the earlier
PIVOT row exactly before the change, so the harness is consistent.

| | kind | recall | sign | \|Δgrad\| %/yr | \|Δlevel\| | lag | matched | overstay |
|---|---|---|---|---|---|---|---|---|
| PIVOT (D399 CELL_FINAL) | S / R | 30 / 30 | 88 / 92 | 30 / 43 | 3.2 / 6.0 | +6 / +4 | 54 / 56 | 37 / 38 |
| GROW (D478) | S / R | 61 / 62 | 80 / 79 | 49 / 70 | 5.5 / 5.8 | −3 / −2 | 93 / 89 | 53 / 50 |
| HYST (D479) | S / R | 53 / 52 | 73 / 79 | 54 / 48 | 5.5 / 5.2 | +2 / +1 | 83 / 85 | **16 / 19** |
| HYST-WIDE | S / R | **96 / 96** | 68 / 72 | 65 / 55 | 6.3 / 6.0 | −5 / −5 | 77 / 82 | 84 / 81 |
| **HAND CELL (D480)** | S / R | **69 / 71** | **92 / 87** | **27 / 40** | **3.2 / 4.3** | −5 / −5 | 86 / 86 | 42 / 31 |

The hand cell, as a settings line for the live page:

    k=1 mp=2 maxp=0 carry=7 dh=20 dg=0 mw=0 body=on bdepth=3 bbars=1 bkeep=1 syn=on anchor=quantile
    aq=0.2 dmode=rank decay=0.76 height=anchored ttl=on walk=on btol=-1 chain=body_only reach=130
    stalew=25 staled=12 stalestat=mean fittol=16 pairbreak=off pairdraw=off fit=ols ttol=0.37 mt=1 margin=4

What each change bought, on the card (support / resistance):

| change, cumulative | recall | sign | \|Δgrad\| | lag | overstay |
|---|---|---|---|---|---|
| CELL_FINAL | 30 / 30 | 88 / 92 | 30 / 43 | +6 / +4 | 37 / 38 |
| pair rules off | 54 / 59 | 85 / 87 | 30 / 41 | −1 / 0 | 47 / 38 |
| + k = 1 | 58 / 63 | 90 / 87 | 29 / 69 | −2 / −4 | 47 / 50 |
| + stale 25/12 | 57 / 61 | 93 / 87 | 34 / 50 | −2 / −4 | 42 / 38 |
| + break 4/1, keep 0 on a break | 50 / 50 | 89 / 87 | 33 / 35 | −1 / −1 | 26 / 31 |
| + keep 1, min width 0 | 72 / 74 | 90 / 88 | 32 / 35 | −4 / −5 | 47 / 38 |
| + break 3/1 (the hand cell) | 69 / 71 | 92 / 87 | 27 / 40 | −5 / −5 | 42 / 31 |

`bkeep` is a new switch in `recalc_pair` (`break_keep`): on a break the buffer keeps that many
pivots across it instead of `carry`. The margin is applied to the drawn level, not the fit.

## 4. Reading it

- **On the line itself the cell is the eye's.** Sign 92 / 87%, gradient within 27 / 40%/yr
  against the principal's own 73%/yr median slope, level within 3.2 / 4.3% with the margin. It
  is the only construction above 85% on sign with recall above 60%.
- **Coverage went from 30% to 69–71%** against the principal's 78%; the missing bars are mostly
  the ten bars after a construction end (55% of misses), the rebirth wait.
- **It draws earlier than the principal**, five bars on the median — the one-bar pivot and the
  carried pivot put a line up before the eye commits. Whether that is a fault is the principal's
  call; the lag metric is symmetric and the composite penalises it.
- **Overstay is the open item**: 42 / 31% against the principal's 20%, on 35 ends. Nine of the
  fifteen overstays are the principal's drift ends, where the construction's line lived a
  median eight more bars; the staleness dial did not move it without costing recall, and on 35
  ends each is three points, so it was left rather than fitted.
- The swing envelope is kept as evidence of what does not work: the eye's anchors read as two
  points, but its gradient reads as an envelope over several.

## 5. What is not done

No trade. The principal said not to. The next step, when wanted, is the D477 rule and the D476
rule on this cell — with the prediction already on record from D478/D479 that a better drawing
does not change what the direction is worth — and, separately, a rule that reads the channel's
level, which the hand lines' 4% margin now makes a defined quantity.
