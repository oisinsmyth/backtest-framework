# D451 SCORECARD — the constructions against the principal's hand-drawn lines: pivots get the gradient, windows get the coverage, nothing gets both

*Scorer `scripts/d451_score_hand_lines.py`; numbers `data/d451_hand_scorecard.json`; the target
`data/d451_hand_drawn_lines.json`, drawn on the page "Draw the Lines" (artifact 1ed889fb) one bar
at a time with the future hidden. Not a trade; a scorecard for the drawing.*

## 1. The target, written down for the first time

140 lines on the twelve page names (69 support, 71 resistance), 117 of them ended before the
last bar. Anchor span median 24 bars (18–38). **Draw lag after the second anchor: median 1 bar**
(0–6). **Life from draw to end: median 26 bars** (18–44). Gradient median 73%/yr in magnitude,
59% rising. A line of some kind on 78% of bars, both kinds on 74%. Six explicit updates (the
same first anchor redrawn the bar the old line ended). Only 17% of anchors sit exactly on a
wick: the principal draws by eye, not by extreme.

## 2. The score, bar by bar over the panels

| | kind | recall | precision | sign | \|Δgrad\| | \|Δlevel\| | lag | matched | overstay |
|---|---|---|---|---|---|---|---|---|---|
| PIVOT (D399) | support | 30% | 75% | **88%** | **30%** | **3.2%** | 6 | 54% | **25%** |
| | resistance | 30% | 76% | **92%** | **43%** | 6.0% | 4 | 56% | **20%** |
| GROW (D451) | support | 61% | 74% | 80% | 49% | 5.5% | −3 | 93% | 40% |
| | resistance | 62% | 76% | 79% | 70% | 5.8% | −2 | 89% | 39% |
| HYST (D452) | support | 53% | 75% | 73% | 54% | 5.5% | 2 | 83% | 26% |
| | resistance | 52% | 74% | 79% | 48% | 5.2% | 1 | 85% | 27% |
| HYST-WIDE | support | **96%** | 76% | 68% | 65% | 6.3% | −5 | 77% | 72% |
| | resistance | **96%** | 77% | 72% | 55% | 6.0% | −5 | 82% | 68% |

Recall: of the bars the principal had a line, the share the construction showed one.
Precision: the converse — and it is ~76% for every construction because the principal has a line
on 78% of bars, so an always-on construction scores 76%; precision is the base rate here and says
nothing. Sign, |Δgrad| (%/yr) and |Δlevel| (%) are over bars where both had a line. Lag is bars
from the principal's draw to the construction's first same-kind, same-sign line (negative =
earlier). Overstay: the share of the principal's ended lines the construction was still showing
five bars after the end.

## 3. Reading it

- **The pivot construction draws the principal's line, when it draws at all.** Sign agreement
  88–92%, gradient within 30–43%/yr against the principal's own 73%/yr median, level within 3%
  on support, and it ends when the principal ends (overstay 20–25%, the lowest). It draws on only
  30% of the bars the principal has a line, and 4–6 bars late.
- **The window constructions draw more and draw worse.** Grow-right reaches 61% recall and is
  *earlier* than the principal (it has a same-sign line three bars before the draw), but agrees on
  sign only 80% of the time and its gradients are off by 49–70%/yr. Hysteresis is closer in
  timing (lag 1–2) and ending (overstay 26%) but agrees less on sign (73–79%). The wide candidate
  is on for 96% of the principal's bars and is simply always on: sign 68–72%, and it is still
  showing a line 70% of the time five bars after the principal has ended one.
- **What the eye does that neither does.** It anchors on pivots — which is why the pivot
  construction's gradients match — but it draws the bar the second pivot forms (lag 1), keeps the
  line through pullbacks (life 26), ends it on a break, and re-anchors across the break, six
  times explicitly. The pivot construction has the anchors and none of the survival; the window
  constructions have the survival and the wrong anchors (hull edges chosen by touch count).

## 4. What follows

The hybrid the principal described is now specified by the scorecard rather than by taste:
pivot anchors (the D399 detector, confirmation as short as the eye's one bar allows), a line
drawn as soon as two same-kind pivots exist, survival under containment with a trend-side break
as the only end, restart that may reach back to the last pivots before the break. Each change
can be scored on this card before any trade is run, and the target numbers are the principal's
own: recall toward 78%, sign toward 90%, gradient within ~40%/yr, lag near 1, overstay near 20%.
