"""THE LIVE PAGE: every parameter of the construction adjustable, all twelve names redrawn on
each change.

    uv run python scripts/d399_emit_live_bars.py
    uv run python scripts/d399_splice_live_page.py

A PORT, NOT A CALL. `recalc_pair` from scripts/d399_recalc_segment.py is re-implemented in the
page's JavaScript, function for function and in the same order -- pivot detection, the weighted
fit, the clearance intercept, the back-projection check, the three invalidators, the pair test,
the provisional pivot, the walk, the emission guards. It runs from each name's bar 0 exactly as the
Python does. It is a faithful port and it is NOT bit-identical: JavaScript sums floats in the
order written here and numpy does not, so a threshold comparison can in principle land on the
other side of a boundary at the last ULP. The Python is the record; this is the instrument.

The page ships bars only -- no lines, no pivots, no chosen cell -- so nothing on it was computed
anywhere but in front of the principal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_live_bars.json"
OUT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "temp" / "d399_live_page.html")

HTML = r"""<title>Turn the Dials</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#fff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7; --chip:#f1eee9;
  --up:#1c6b52; --down:#a93d2c; --res:#c2410c; --sup:#1d4ed8; --warn:#8a6d1f;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
    --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f;
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
  --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;font-size:15px;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:30px 22px 64px;display:flex;flex-direction:column;gap:18px}
h1{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:33px;margin:0;letter-spacing:-.01em}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
.lede{max-width:70ch;color:var(--muted);margin:0}
.lede b{color:var(--ink);font-weight:600}
.dials{position:sticky;top:0;z-index:5;background:var(--panel);border:1px solid var(--rule);
  border-radius:6px;padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center}
.dials label{display:inline-flex;align-items:center;gap:7px;font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;color:var(--muted);white-space:nowrap}
.dials select{font:inherit;font-size:12.5px;padding:3px 6px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink)}
.dials input[type=checkbox]{width:15px;height:15px}
.dials input[type=number]{font:inherit;font-size:12.5px;width:5.2em;padding:3px 5px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink);font-variant-numeric:tabular-nums}
.dials input[type=number]:invalid{border-color:var(--down)}
.dials .grp{display:inline-flex;gap:14px;align-items:center;padding-right:16px;
  border-right:1px solid var(--rule-soft)}
.dials .grp:last-child{border-right:none}
.dials .tot{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12.5px;
  color:var(--ink);font-variant-numeric:tabular-nums}
.dials button{font:inherit;font-size:12.5px;padding:4px 10px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink);cursor:pointer}
.dials button:hover{border-color:var(--muted)}
.grid{display:flex;flex-direction:column;gap:14px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.ph{display:flex;align-items:baseline;gap:12px;padding:10px 16px 2px;flex-wrap:wrap}
.ph h2{font-family:"Newsreader",Georgia,serif;font-size:18px;font-weight:600;margin:0}
.ph .dt{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
.ph .st{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted);
  font-variant-numeric:tabular-nums}
.pb{overflow-x:auto}
.pb svg{display:block;width:100%;min-width:880px;height:auto}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:20px;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);
  max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">D399 &middot; the construction, live</div>
  <h1>Turn the dials</h1>
  <p class="lede">Every parameter of the construction, on the same twelve draws. Change one and all
    twelve redraw. Nothing on this page was computed anywhere else: the page carries bars only and
    runs the construction itself, from each name's first bar, exactly as the Python does. <b>The
    page opens on the final construction as chosen on 2026-09-10</b>; the settings line below the
    dials is its record, and <em>apply</em> restores any line pasted into it.</p>

  <div class="dials" id="dials">
    <span class="grp">
      <label>k <input type="number" id="k" value="2" min="1" max="10" step="1"></label>
      <label>min pivots <input type="number" id="mp" value="2" min="2" step="1"></label>
      <label>max pivots <input type="number" id="maxp" value="0" min="0" step="1" title="0 = off"></label>
      <label>carry <input type="number" id="carry" value="7" min="0" step="1"></label>
    </span>
    <span class="grp">
      <label>height Δ <input type="number" id="dh" value="20" min="0" step="1" title="0 = off">%</label>
      <label>gradient Δ <input type="number" id="dg" value="0" min="0" step="1" title="0 = off">%/yr</label>
      <label>min width <input type="number" id="mw" value="10" min="0" step="0.5">%</label>
    </span>
    <span class="grp">
      <label><input type="checkbox" id="body" checked> body break</label>
      <label>needs more than <input type="number" id="bdepth" value="2" min="0" step="0.5">% through</label>
      <label>for <input type="number" id="bbars" value="2" min="1" step="1"> bars</label>
      <label><input type="checkbox" id="syn" checked> break bar = pivot</label>
      <label>height from <select id="anchor"><option value="latest">newest pivot</option><option value="pivot">outermost pivot</option><option value="quantile" selected>weighted quantile q</option><option value="clear">clear all bodies</option><option value="raw">raw fit</option></select></label>
      <label>q <input type="number" id="aq" value="0.2" min="0" max="1" step="0.05" title="0 = outermost, 0.5 = weighted median"></label>
    </span>
    <span class="grp">
      <label>age law <select id="dmode"><option value="span">span: oldest at</option><option value="linear">linear: oldest at</option><option value="halflife">half-life, bars</option><option value="rank" selected>rank: per pivot</option><option value="respect">respect (no number)</option></select></label>
      <label><input type="number" id="decay" value="0.76" min="0.01" step="0.05" title="span/linear: weight at the oldest pivot (1 = none). half-life: bars. rank: ratio per pivot."></label>
      <label>height test vs <select id="height"><option value="raw">raw fit</option><option value="anchored" selected>drawn line</option></select></label>
      <label><input type="checkbox" id="ttl" checked> drop falsified break pivot</label>
    </span>
    <span class="grp">
      <label><input type="checkbox" id="walk" checked> keep what fits</label>
      <label>walk tol <input type="number" id="btol" value="-1" min="-1" step="1" title="-1 = height Δ">%</label>
      <label>hand on walked points <select id="chain"><option value="body_only" selected>across body breaks</option><option value="native_only">never</option><option value="unbounded">always</option></select></label>
      <label>max reach <input type="number" id="reach" value="130" min="0" step="5" title="0 = off"> bars</label>
    </span>
    <span class="grp">
      <label>stale after <input type="number" id="stalew" value="35" min="0" step="1" title="0 = off"> bars</label>
      <label>of price more than <input type="number" id="staled" value="18" min="0" step="0.5">% off, by <select id="stalestat"><option value="mean" selected>mean</option><option value="min">closest</option></select></label>
      <label>birth fit tol <input type="number" id="fittol" value="16" min="0" step="0.5" title="0 = off">%</label>
    </span>
    <span class="grp">
      <label><input type="checkbox" id="pairbreak" checked> channel: break together</label>
      <label><input type="checkbox" id="pairdraw" checked> channel: draw together</label>
    </span>
    <span class="grp">
      <label>fit <select id="fit"><option value="ols" selected>regression</option><option value="env">envelope</option></select></label>
      <label>touch tol <input type="number" id="ttol" value="0.37" min="0" step="0.005"> log</label>
      <label>touches <input type="number" id="mt" value="1" min="1" step="1"></label>
    </span>
    <span class="tot" id="tot">—</span>
    <span class="grp" style="border-right:none;flex-basis:100%;gap:8px">
      <button id="copy" type="button">copy settings</button>
      <input id="settings" type="text" spellcheck="false" style="flex:1;min-width:280px;font:12px 'IBM Plex Mono',monospace;padding:4px 7px;border:1px solid var(--rule);border-radius:4px;background:var(--chip);color:var(--ink)">
      <button id="apply" type="button">apply</button>
      <span id="copied" style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--faint)"></span>
    </span>
  </div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance</span>
    <span><i class="sw" style="border-color:var(--muted);border-top-style:dashed"></i> back to the segment's first pivot</span>
    <span id="timing" style="margin-left:auto;font-family:IBM Plex Mono,monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>

  <div class="grid" id="grid"></div>

  <p class="note"><b>A port, not a call.</b> The construction here is re-implemented in the page's
    own script, function for function in the same order as <code>recalc_pair</code>. It is
    faithful and it is not bit-identical &mdash; JavaScript and numpy sum floats in different
    orders, so a threshold test can in principle land a ULP the other way. The independent review
    measured this: with Python's sums put in the page's order the two agree exactly, and in
    numpy's order the segment count on a name can differ by up to four &mdash; a statement about
    how sensitive the construction is to a last-bit change, not about the port. The Python is the
    record; this is the instrument. Both invariants are still checked on every redraw: the count
    of bars where a line runs through a body, and of inverted channels, is in the header of each
    panel and should read 0 / 0. A triangle at a panel's top or bottom edge marks a segment that
    runs off it.</p>
  <p class="note"><b>After the review (2026-09-10).</b> The fit's points are now merged in bar
    order (the age weight was mis-applied in about half the fits before); the walk can no longer
    resurrect a provisional pivot; a body close is tested even on a bar whose candidate fit
    cannot be computed. Four dials came out of the review's suspicions: <b>height test vs</b>
    (compare the candidate to the raw frozen fit, or to the drawn, clearance-anchored line);
    <b>drop falsified break pivot</b> (once the detector has ruled on that bar); <b>hand on
    walked points</b> (across body breaks only, never, or always &mdash; the last is what chained
    an origin 663 bars back); <b>max reach</b>, the one new number. The walk's proximity test now
    reads the line before the point joins it.</p>
  <p class="note"><b>Age on the envelope.</b> The envelope is chosen, not fitted, so the age
    weight cannot enter as it does in the regression. It enters at the one decision the envelope
    makes: which valid edge wins. Each touching pivot supports an edge by 1 at the newest pivot
    down to the <b>age decay</b> value at the oldest, the largest sum wins, longest span on a
    tie. The candidates (hull edges), validity (every pivot still clears the line) and
    qualification (<b>touches</b> is still a plain count) are untouched. At decay 1 it is the
    unweighted choice exactly. The <b>age decay</b> dial therefore applies to both fits; the
    <b>clearance intercept</b> applies to the regression only and is greyed out under the
    envelope.</p>
  <p class="note"><b>Is price still respecting the line?</b> Every earlier invalidator asked
    whether the <em>fit</em> had moved; none asked whether price was still near the line, which
    is how a support sat 30% under six months of candles. The offset of each bar's extreme from
    the line (the low for support, the high for resistance; 0 is a touch) now serves two tests.
    <b>Stale</b>: the line dies when the offset over the last W bars &mdash; its mean, or the
    closest approach &mdash; exceeds the tolerance; the side goes dormant and re-forms from the
    recent pivots at the next confirmed one. <b>Birth fit tol</b>: a line is drawn only if its
    own pivots sit on it, mean |residual| within the tolerance &mdash; "too strict" caught
    before it exists. Each stale death is split in the header: <em>respected then left</em>
    (some bar after it was drawn came within the tolerance) or <em>never confirmed</em>.</p>
  <p class="note"><b>The segment is a channel.</b> <em>Break together</em>: any invalidation of one
    side resets the other too, the way a crossing always has; the broken side keeps its own
    reason and its provisional pivot, the partner goes dormant until its next confirmed pivot.
    <em>Draw together</em>: a bar shows both lines or neither. Each half is its own box so its
    cost in coverage can be seen alone.</p>
  <p class="note"><b>The height from one pivot.</b> The gradient is the weighted regression
    through the pivots; the height used to come from clearing <em>every</em> body back to the
    origin, so one deep candle set the level of the whole line. <em>Height from: one pivot</em>
    puts the line through the founding pivot that sits outermost against that slope &mdash;
    lowest for support, highest for resistance &mdash; with every other pivot on or inside it,
    and consults no body in placing it; the forward body-break rule polices it from the bar it is
    drawn. <em>Newest pivot</em> puts it through the most recent founding pivot instead:
    with the age decay the slope hugs the newest points and leaves the oldest pivot sticking out,
    so <em>outermost</em> tends to hang the line on its origin; <em>newest</em> makes the height
    what price is respecting now, and older pivots may sit either side. <em>Weighted quantile</em>
    is the age-aware rule: each founding pivot's offset from the slope, weighted by the age law,
    and the line set at the q-th quantile from the outside &mdash; q = 0 is the outermost pivot,
    0.5 the weighted median, a small q sits on the recent lows and steps over an old outlier
    whose age weight is a small share of the mass. <em>Clear all bodies</em> is the earlier rule;
    <em>raw fit</em> is the regression as fitted.</p>
  <p class="note"><b>Five age laws.</b> The number beside the law changes meaning with it.
    <em>Span</em> (the original): the oldest pivot weighs the number, the newest 1, whatever the
    segment's length. <em>Linear</em>: the same endpoints on a straight ramp. <em>Half-life</em>:
    a pivot's weight halves every that-many bars from <em>today</em>, so a short segment is barely
    discounted and a long one forgets its origin &mdash; which span-normalisation cannot say.
    <em>Rank</em>: the k-th newest pivot weighs the number to the k, blind to bar distance
    &mdash; age in swings. <em>Respect</em>: no number; a pivot weighs 1 plus the count of later
    bars whose extreme came within the touch tolerance of the line of the unweighted slope through
    it &mdash; evidence rather than age, taken in one step so it is not circular. Under the
    envelope the same weights are the edge's touch support.</p>
  <p class="note"><b>Max pivots.</b> The fit is the newest N confirmed pivots and no more: older
    ones are forgotten as newer ones arrive, so the slope is the last N swings and the origin
    drops out of the regression entirely once N newer pivots exist &mdash; where the age decay
    only down-weights it. The drawn origin moves forward with the buffer, and the walk stops
    adding old points once the buffer is full.</p>
  <p class="note"><b>A break needs depth and persistence.</b> The lines sat on the micro trends
    and broke on every pullback, because a break was one close through the line. Now a body
    counts as through only when it closes more than the <em>depth</em> beyond the line, and the
    break fires only after that many <em>consecutive</em> closes. The same tolerance applies to
    the drawing guard (or the line would vanish during the pullback it is meant to survive) and to
    the through-body count in each header, which reads "more than the depth through". 0% for 1
    bar is the earlier rule exactly; <em>pullbacks tolerated</em> counts the closes that touched or
    poked the line without breaking it.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var DELTA = D.delta, INF = Infinity;

  // ---------------------------------------------------------------- the fit
  function ols(x, y){
    var n = x.length, i;
    if (n < 2) return [NaN, NaN];
    var xm = 0, ym = 0;
    for (i = 0; i < n; i++){ xm += x[i]; ym += y[i]; }
    xm /= n; ym /= n;
    var num = 0, den = 0;
    for (i = 0; i < n; i++){ var dx = x[i] - xm; num += dx * (y[i] - ym); den += dx * dx; }
    if (den <= 0) return [NaN, NaN];
    var b = num / den;
    return [b, ym - b * xm];
  }
  function wls(x, y, decay){
    var n = x.length, i;
    if (n < 2) return [NaN, NaN];
    if (decay === 1) return ols(x, y);
    var span = x[n - 1] - x[0];
    if (!(span > 0)) throw new Error('[S] wls: points not in bar order (span ' + span + ')');
    var w = new Array(n);
    for (i = 0; i < n; i++) w[i] = Math.pow(decay, (x[n - 1] - x[i]) / span);
    return wols(x, y, w);
  }
  // weighted least squares with explicit weights: the arithmetic wls always did, same order
  function wols(x, y, w){
    var n = x.length, i, sw = 0;
    for (i = 0; i < n; i++) sw += w[i];
    if (sw <= 0) return [NaN, NaN];
    var xm = 0, ym = 0;
    for (i = 0; i < n; i++){ xm += w[i] * x[i]; ym += w[i] * y[i]; }
    xm /= sw; ym /= sw;
    var num = 0, den = 0;
    for (i = 0; i < n; i++){ var dx = x[i] - xm; num += w[i] * dx * (y[i] - ym); den += w[i] * dx * dx; }
    if (den <= 0) return [NaN, NaN];
    var b = num / den;
    return [b, ym - b * xm];
  }
  // FIVE ANSWERS TO "WHAT IS AGE?" -- one weight per pivot, newest last; null = all ones.
  // span: p at the oldest pivot, 1 at the newest, whatever the span. linear: same endpoints,
  // straight. halflife: 0.5^(bars from today / p). rank: p^k for the k-th newest. respect:
  // 1 + bars since the pivot whose extreme came within tol of the unweighted-slope line through it.
  function ageWeights(mode, x, y, t, p, ext, kd, tol){
    var n = x.length, i, w = new Array(n);
    if (n < 2) return null;
    if (mode === 'span' || mode === 'linear'){
      if (p === 1) return null;
      var span = x[n - 1] - x[0];
      if (!(span > 0)) throw new Error('[S] ageWeights: points not in bar order');
      for (i = 0; i < n; i++) w[i] = mode === 'span' ? Math.pow(p, (x[n - 1] - x[i]) / span) : 1 - (1 - p) * (x[n - 1] - x[i]) / span;
      return w;
    }
    if (mode === 'halflife'){ for (i = 0; i < n; i++) w[i] = Math.pow(0.5, (t - x[i]) / p); return w; }
    if (mode === 'rank'){ if (p === 1) return null; for (i = 0; i < n; i++) w[i] = Math.pow(p, n - 1 - i); return w; }
    if (mode === 'respect'){
      var g0 = ols(x, y)[0]; if (!isFinite(g0)) return null;
      for (i = 0; i < n; i++){
        w[i] = 1;
        for (var q = x[i] + 1; q <= t; q++){ var e = ext[q]; if (!isFinite(e)) continue; if (Math.abs(e - (y[i] + g0 * (q - x[i]))) <= tol) w[i]++; }
      }
      return w;
    }
    throw new Error('unknown decay mode ' + mode);
  }

  // ---------------------------------------------------------------- the envelope, ported
  // Monotone chain over x-sorted points; collinear middles dropped with the same 1e-9 epsilon
  // as the Python, so a straight run of lows is one edge with the middle as a touch.
  function hullEdges(x, y, lower){
    var n = x.length, h = [], EPS = 1e-9, p;
    if (n < 2) return [];
    for (p = 0; p < n; p++){
      while (h.length >= 2){
        var a = h[h.length - 2], b = h[h.length - 1];
        var cr = (x[b] - x[a]) * (y[p] - y[a]) - (y[b] - y[a]) * (x[p] - x[a]);
        if (lower ? (cr <= EPS) : (cr >= -EPS)) h.pop(); else break;
      }
      h.push(p);
    }
    var e = [];
    for (p = 0; p + 1 < h.length; p++) e.push([h[p], h[p + 1]]);
    return e;
  }
  // The most-respected edge: the largest SUPPORT within tol, then longest span, then first in
  // order. Support is the touch count at decay 1, and the age-weighted sum of touches otherwise
  // (1 at the newest pivot, decay at the oldest -- the same law as wls). The returned touch
  // count stays a plain count, so `touches` qualification is unchanged.
  function envFit(x, y, kd, tol, decay, wIn){
    var n = x.length;
    if (n < 2) return [NaN, NaN, 0];
    var w = new Array(n), k;
    if (wIn){ w = wIn; }
    else if (decay === 1){ for (k = 0; k < n; k++) w[k] = 1; }
    else {
      var span = x[n - 1] - x[0];
      if (!(span > 0)) throw new Error('[S] envFit: points not in bar order (span ' + span + ')');
      for (k = 0; k < n; k++) w[k] = Math.pow(decay, (x[n - 1] - x[k]) / span);
    }
    var edges = hullEdges(x, y, kd === 'sup'), best = null, q;
    for (q = 0; q < edges.length; q++){
      var i = edges[q][0], j = edges[q][1], dx = x[j] - x[i];
      if (!(dx > 0)) continue;
      var g = (y[j] - y[i]) / dx, c = y[i] - g * x[i], touches = 0, sup = 0, bad = false;
      for (k = 0; k < n; k++){
        var r = y[k] - (g * x[k] + c);
        if (kd === 'sup' ? (r < -tol) : (r > tol)){ bad = true; break; }
        if (Math.abs(r) <= tol){ touches++; sup += w[k]; }
      }
      if (bad) continue;
      if (!best || sup > best[4] || (sup === best[4] && dx > best[3])) best = [g, c, touches, dx, sup];
    }
    return best ? [best[0], best[1], best[2]] : [NaN, NaN, 0];
  }

  // ---------------------------------------------------------------- pivots, tie-tolerant
  function pivots(H, Lw, k){
    var m = H.length, out = {sup: [], res: []}, i, j;
    for (i = k; i < m - k; i++){
      var mx = -Infinity, mn = Infinity;
      for (j = i - k; j <= i + k; j++){ if (H[j] > mx) mx = H[j]; if (Lw[j] < mn) mn = Lw[j]; }
      if (H[i] === mx) out.res.push([i, Math.log(H[i])]);
      if (Lw[i] === mn) out.sup.push([i, Math.log(Lw[i])]);
    }
    return out;
  }

  // ---------------------------------------------------------------- recalc_pair, ported
  function recalc(nm, P){
    var O = nm.o, H = nm.h, Lw = nm.l, C = nm.c, m = nm.m, k = P.k;
    var body = {sup: new Float64Array(m), res: new Float64Array(m)};
    var ext = {sup: new Float64Array(m), res: new Float64Array(m)};
    var t;
    for (t = 0; t < m; t++){
      body.sup[t] = Math.log(Math.min(O[t], C[t])); body.res[t] = Math.log(Math.max(O[t], C[t]));
      ext.sup[t] = Math.log(Lw[t]); ext.res[t] = Math.log(H[t]);
    }
    var pv = pivots(H, Lw, k);
    var G = {sup: new Float64Array(m).fill(NaN), res: new Float64Array(m).fill(NaN)};
    var L = {sup: new Float64Array(m).fill(NaN), res: new Float64Array(m).fill(NaN)};
    var S = {sup: new Int32Array(m).fill(-1), res: new Int32Array(m).fill(-1)};
    var why = {gradient: 0, height: 0, body: 0, inverted: 0, backproj: 0, extended: 0, extended_pts: 0,
               nan_fit: 0, max_reach_hit: 0, syn: 0, rat: 0, dropped: 0, superseded: 0,
               stale: 0, stale_abandoned: 0, stale_unconfirmed: 0, unfit: 0, pair: 0, pair_hidden: 0, body_poke: 0};
    var st = {};
    ['sup', 'res'].forEach(function(kd){
      st[kd] = {list: pv[kd], p: 0, bx: [], by: [], walked: {}, g: NaN, c: NaN, craw: NaN, s0: -1,
                dormant: false, syn: null, old: [], pending: false, reached: 0,
                touch: 0, ver: 0, fitVer: -1, fitNow: [NaN, NaN, 0], born: -1, touched: false, thru: 0};
    });
    // a body more than the break depth through the line (the tolerance is the same everywhere)
    function deep(b, lv, kd){ return isFinite(b) && (kd === 'sup' ? (b < lv - P.bdepth) : (b > lv + P.bdepth)); }
    // the bar's extreme against the line, signed so 0 is a touch and positive is price off the line
    function offset(g, c, t, kd){ var lv = g * t + c; return kd === 'sup' ? ext.sup[t] - lv : lv - ext.res[t]; }
    // BIRTH: the line must be a fair description of its own pivots (mean |residual| <= fit tol)
    function fitsPivots(g, c, fx, fy){
      if (P.fittol < 0 || !isFinite(g) || !isFinite(c) || !fx.length) return true;
      var s = 0; for (var i = 0; i < fx.length; i++) s += Math.abs(fy[i] - (g * fx[i] + c));
      return s / fx.length <= P.fittol;
    }
    // first index whose value is >= x, in a sorted array: where a bar belongs (D1)
    function lowerBound(arr, x){
      var lo = 0, hi = arr.length;
      while (lo < hi){ var mid = (lo + hi) >> 1; if (arr[mid] < x) lo = mid + 1; else hi = mid; }
      return lo;
    }
    // the confirmed buffer with the provisional MERGED IN BAR ORDER, never appended (D1)
    function fitpts(d){
      var fx = d.bx.slice(), fy = d.by.slice();
      if (d.syn){ var p = lowerBound(fx, d.syn[0]); fx.splice(p, 0, d.syn[0]); fy.splice(p, 0, d.syn[1]); }
      return [fx, fy];
    }
    function np(d){ return d.bx.length + (d.syn ? 1 : 0); }
    function need(d){ return d.syn ? 1 : 0; }
    // the drawn intercept for a fitted gradient: through the outermost founding pivot, clear of
    // every body back to the origin, or the raw fit
    function place(g, craw, s0, t, kd, fx, fy){
      if (P.fit === 'env' || !isFinite(g) || P.anchor === 'raw') return craw;
      if (P.anchor === 'pivot'){
        var best = NaN;
        for (var i = 0; i < fx.length; i++){ var v = fy[i] - g * fx[i]; if (isNaN(best)) best = v; else best = kd === 'sup' ? Math.min(best, v) : Math.max(best, v); }
        return best;
      }
      if (P.anchor === 'latest') return fx.length ? fy[fx.length - 1] - g * fx[fx.length - 1] : NaN;   // fx is in bar order
      if (P.anchor === 'quantile'){
        // the age-weighted q-th quantile of the pivots' offsets from the slope, lowest first for
        // support, highest first for resistance: q = 0 is the outermost pivot
        var n = fx.length; if (!n) return NaN;
        var w = ageWeights(P.dmode, fx, fy, t, P.decay, ext[kd], kd, P.ttol), i;
        if (!w){ w = new Array(n); for (i = 0; i < n; i++) w[i] = 1; }
        var idx = [], sw = 0; for (i = 0; i < n; i++){ idx.push(i); sw += w[i]; }
        idx.sort(function(a, b){ var ra = fy[a] - g * fx[a], rb = fy[b] - g * fx[b]; return kd === 'sup' ? (ra - rb || a - b) : (rb - ra || a - b); });
        var cum = 0;
        for (i = 0; i < n; i++){ cum += w[idx[i]]; if (cum / sw >= P.aq) return fy[idx[i]] - g * fx[idx[i]]; }
        return fy[idx[n - 1]] - g * fx[idx[n - 1]];
      }
      return clear(g, s0, t, kd);
    }
    function spans(g, c, s0, t, kd){
      if (!(P.body && P.back) || P.anchor === 'pivot' || P.anchor === 'latest' || P.anchor === 'quantile') return true;
      if (!isFinite(g) || !isFinite(c)) return true;
      var a = Math.max(0, s0), b = Math.min(m - 1, t);
      if (b < a) return true;
      for (var q = a; q <= b; q++){
        if (deep(body[kd][q], g * q + c, kd)) return false;
      }
      return true;
    }
    function clear(g, s0, t, kd){
      var a = Math.max(0, s0), b = Math.min(m - 1, t);
      if (b < a) return NaN;
      var best = NaN;
      for (var q = a; q <= b; q++){
        var bo = body[kd][q]; if (!isFinite(bo)) continue;
        var v = bo - g * q;
        if (isNaN(best)) best = v;
        else best = kd === 'sup' ? Math.min(best, v) : Math.max(best, v);
      }
      return best;
    }
    function fit(fx, fy, kd, t){
      for (var i = 1; i < fx.length; i++) if (!(fx[i] > fx[i - 1])) throw new Error('[S] fit input not in bar order: ' + fx.join(','));
      if (P.dmode === 'span'){
        if (P.fit === 'env') return envFit(fx, fy, kd, P.ttol, P.decay);
        var r = wls(fx, fy, P.decay); return [r[0], r[1], fx.length];
      }
      var w = ageWeights(P.dmode, fx, fy, t, P.decay, ext[kd], kd, P.ttol);
      if (P.fit === 'env') return envFit(fx, fy, kd, P.ttol, 1, w);
      var r2 = w ? wols(fx, fy, w) : ols(fx, fy); return [r2[0], r2[1], fx.length];
    }
    // freeze a fit as the side's line; the RAW intercept is kept beside the drawn one (S1)
    function freeze(d, g, craw, tn, s0, t, kd, fx, fy){
      d.s0 = s0; d.g = g; d.craw = craw; d.touch = tn; d.born = -1; d.touched = false; d.thru = 0;
      var c = place(g, craw, s0, t, kd, fx || [], fy || []);
      d.c = c;
      if (!spans(g, c, s0, t, kd)){ why.backproj++; d.g = NaN; d.c = NaN; d.craw = NaN; d.dormant = true; return false; }
      if (!fitsPivots(g, c, fx || [], fy || [])){
        why.unfit++; d.g = NaN; d.c = NaN; d.craw = NaN; d.dormant = true;
        // and the buffer slides to the newest `carry` points: the old ones are what do not fit
        if (P.carry > 0 && d.bx.length > P.carry){ d.bx = d.bx.slice(-P.carry); d.by = d.by.slice(-P.carry); d.walked = {}; d.ver++; }
        return false;
      }
      return true;
    }
    function refit(d, t, kd){
      var f = fitpts(d), fx = f[0], fy = f[1];
      var s0 = fx.length ? fx[0] : t;
      var r = fx.length >= 2 ? fit(fx, fy, kd, t) : [NaN, NaN, 0];
      freeze(d, r[0], r[1], r[2], s0, t, kd, fx, fy);
    }
    function sleep(d){ d.g = NaN; d.c = NaN; d.craw = NaN; d.dormant = true; d.born = -1; d.touched = false; d.thru = 0; }
    function reset(d, t, kd, bad, ns){
      // `old` from the CONFIRMED buffer only (D2), and only the points this segment may hand
      // on: walked-in points travel only across a BODY break under 'body_only' (S3)
      var all = P.chain === 'unbounded' || (P.chain === 'body_only' && bad === 'body');
      d.old = [];
      for (var i = 0; i < d.bx.length; i++){ if (all || !d.walked[d.bx[i]]) d.old.push([d.bx[i], d.by[i]]); }
      d.pending = true; d.reached = 0;
      d.bx = P.carry > 0 ? d.bx.slice(-P.carry) : []; d.by = P.carry > 0 ? d.by.slice(-P.carry) : [];
      d.walked = {}; d.ver++;
      if (ns){
        if (d.syn) why.superseded++;
        why.syn++;
        if (d.bx.indexOf(ns[0]) >= 0){ d.syn = null; why.rat++; }   // already confirmed (k=0)
        else d.syn = ns;
        d.dormant = false; refit(d, t, kd);
      } else sleep(d);
    }
    function walk(d, t, kd){
      var tol = P.btol < 0 ? P.dh : P.btol;
      d.pending = false;
      if (!d.old.length || !isFinite(d.g)) return;
      var have = {}; d.bx.forEach(function(x){ have[x] = 1; }); if (d.syn) have[d.syn[0]] = 1;
      for (var i = d.old.length - 1; i >= 0; i--){
        var x = d.old[i][0], y = d.old[i][1];
        if (have[x]) continue;
        if (P.maxp > 0 && d.bx.length >= P.maxp) break;     // the buffer is full
        if (P.reach > 0 && t - x > P.reach){ why.max_reach_hit++; break; }
        if (P.fit === 'env'){
          // three outcomes: wrong side = a break, stop; touching = evidence, accept;
          // right side but not touching = neither, skip without adding
          var r0 = y - (d.g * x + d.c);
          if (kd === 'sup' ? (r0 < -P.ttol) : (r0 > P.ttol)) break;
          if (Math.abs(r0) > P.ttol) continue;
        } else if (Math.abs(y - (d.g * x + d.c)) > tol) break;   // against the line BEFORE adding (S2)
        var f = fitpts(d), fx = f[0], fy = f[1], p = lowerBound(fx, x);
        fx.splice(p, 0, x); fy.splice(p, 0, y);                    // the trial in bar order (D1)
        var r = fit(fx, fy, kd, t), g = r[0], craw = r[1], tn = r[2];
        if (!isFinite(g)) break;
        var s0 = fx[0], c = place(g, craw, s0, t, kd, fx, fy);
        if (!isFinite(c)) break;
        if (!spans(g, c, s0, t, kd)) break;
        if (!fitsPivots(g, c, fx, fy)) break;
        var q = lowerBound(d.bx, x); d.bx.splice(q, 0, x); d.by.splice(q, 0, y); d.walked[x] = 1;
        d.g = g; d.c = c; d.craw = craw; d.s0 = s0; d.touch = tn; d.ver++; d.reached++; have[x] = 1;
      }
      if (d.reached){ why.extended++; why.extended_pts += d.reached; }
    }
    for (t = 0; t < m; t++){
      var broke = {sup: null, res: null};
      ['sup', 'res'].forEach(function(kd){
        var d = st[kd], fresh = false;
        while (d.p < d.list.length && d.list[d.p][0] <= t - k){
          var bar = d.list[d.p][0];
          if (d.syn && d.syn[0] === bar){ d.syn = null; why.rat++; }
          d.bx.push(bar); d.by.push(d.list[d.p][1]); d.p++; d.ver++; fresh = true;
        }
        // forget the oldest beyond max pivots: the fit is the newest N and no more
        if (P.maxp > 0 && d.bx.length > P.maxp){
          var nd = d.bx.length - P.maxp;
          for (var gi = 0; gi < nd; gi++) delete d.walked[d.bx[gi]];
          d.bx = d.bx.slice(nd); d.by = d.by.slice(nd); d.ver++;
        }
        // falsified: the detector has ruled on the provisional's bar and did not confirm it (S4)
        if (P.ttl && d.syn && d.syn[0] <= t - k){ d.syn = null; d.ver++; why.dropped++; sleep(d); }
        if (fresh && d.dormant){ d.dormant = false; refit(d, t, kd); }
        if (d.dormant || np(d) < 2) return;
        // halflife and respect depend on today, not only on the buffer: no cache under them
        if (d.fitVer !== d.ver || P.dmode === 'halflife' || P.dmode === 'respect'){ var f = fitpts(d); d.fitNow = fit(f[0], f[1], kd, t); d.fitVer = d.ver; }
        var gn = d.fitNow[0], an = d.fitNow[1];
        if (!isFinite(gn)) why.nan_fit++;
        if (!isFinite(d.g)){ if (isFinite(gn)) refit(d, t, kd); return; }
        var lvl = d.g * t + d.c, ref = P.height === 'anchored' ? lvl : d.g * t + d.craw, bad = null;
        // gradient and height need the candidate fit; the body test needs only the frozen line (D3)
        if (isFinite(gn)){
          if (Math.abs(gn - d.g) > P.dg) bad = 'gradient';
          else if (Math.abs((gn * t + an) - ref) > P.dh) bad = 'height';
        }
        if (!bad && P.body && isFinite(lvl)){
          var b = body[kd][t], through = deep(b, lvl, kd);
          // depth AND persistence: beyond the tolerance, on `bbars` consecutive bars
          d.thru = through ? d.thru + 1 : 0;
          if (through && d.thru >= P.bbars) bad = 'body';
          else if (through || (isFinite(b) && (kd === 'sup' ? (b < lvl) : (b > lvl)))) why.body_poke++;
        }
        if (!bad && P.stalew > 0 && isFinite(lvl)){
          // is price still respecting the line? the offset of the last W bars' extremes
          var a0 = Math.max(0, t - P.stalew + 1), sum = 0, mn = Infinity, cnt = 0, q;
          for (q = a0; q <= t; q++){ var o = offset(d.g, d.c, q, kd); if (!isFinite(o)) continue; sum += o; if (o < mn) mn = o; cnt++; }
          if (cnt && (P.stalestat === 'mean' ? sum / cnt : mn) > P.staled){
            bad = 'stale'; if (d.touched) why.stale_abandoned++; else why.stale_unconfirmed++;
          }
        }
        if (bad){
          why[bad]++; broke[kd] = bad;
          var ns = null;
          if (bad === 'body' && P.syn){ var e = ext[kd][t]; if (isFinite(e)) ns = [t, e]; }
          reset(d, t, kd, bad, ns);
        }
      });
      // one broken, both broken: the partner of an invalidated side is reset too
      if (P.pairbreak){
        [['sup', 'res'], ['res', 'sup']].forEach(function(pr){
          if (broke[pr[0]] && !broke[pr[1]]){ why.pair++; reset(st[pr[1]], t, pr[1], 'pair', null); broke[pr[1]] = 'pair'; }
        });
      }
      var ds = st.sup, dr = st.res;
      if (isFinite(ds.g) && isFinite(ds.c) && isFinite(dr.g) && isFinite(dr.c)){
        if ((dr.g * t + dr.c) - (ds.g * t + ds.c) < P.mw){
          why.inverted++; reset(ds, t, 'sup', 'inverted', null); reset(dr, t, 'res', 'inverted', null);
        }
      }
      var ok = {};
      ['sup', 'res'].forEach(function(kd){
        var d = st[kd];
        if (P.walk && d.pending && !d.dormant && isFinite(d.g) && np(d) >= P.mp + need(d) && (!P.ttl || !d.syn)) walk(d, t, kd);
        ok[kd] = !d.dormant && isFinite(d.g) && isFinite(d.c) && np(d) >= P.mp + need(d)
                 && !(Math.abs(d.g) <= DELTA) && (P.fit !== 'env' || d.touch >= P.mt);
        if (ok[kd] && P.body && deep(body[kd][t], d.g * t + d.c, kd)) ok[kd] = false;
      });
      if (ok.sup && ok.res){
        if ((st.res.g * t + st.res.c) - (st.sup.g * t + st.sup.c) < P.mw){ ok.sup = false; ok.res = false; }
      }
      // the channel or nothing
      if (P.pairdraw && ok.sup !== ok.res){ why.pair_hidden++; ok.sup = false; ok.res = false; }
      ['sup', 'res'].forEach(function(kd){
        if (!ok[kd]) return;
        var d = st[kd];
        G[kd][t] = d.g; L[kd][t] = d.g * t + d.c; S[kd][t] = d.s0;
        // the line's biography: first drawn here; respected once a LATER bar comes within staled
        if (d.born < 0) d.born = t;
        else if (!d.touched){ var o2 = offset(d.g, d.c, t, kd); if (isFinite(o2) && Math.abs(o2) <= P.staled) d.touched = true; }
      });
    }
    // the invariants, checked on the window
    var st0 = nm.start, n = nm.n, thru = 0, inv = 0;
    for (t = st0; t < st0 + n; t++){
      if (isFinite(L.sup[t]) && body.sup[t] < L.sup[t] - P.bdepth) thru++;
      if (isFinite(L.res[t]) && body.res[t] > L.res[t] + P.bdepth) thru++;
      if (isFinite(L.sup[t]) && isFinite(L.res[t]) && L.res[t] - L.sup[t] < P.mw) inv++;
    }
    // segments, each from its first pivot
    var segs = {sup: [], res: []}, cov = 0;
    ['sup', 'res'].forEach(function(kd){
      var i = 0;
      while (i < n){
        var q = st0 + i;
        if (!(isFinite(L[kd][q]) && S[kd][q] >= 0)){ i++; continue; }
        var j = i;
        while (j + 1 < n && S[kd][st0 + j + 1] === S[kd][q] && isFinite(L[kd][st0 + j + 1])) j++;
        var g = G[kd][q], c = L[kd][q] - g * q, a = S[kd][q] - st0;
        segs[kd].push({s0: a, t0: i, t1: j, g: g, c: c, before: a < i});
        cov += j - i + 1;
        i = j + 1;
      }
    });
    return {segs: segs, cov: cov, thru: thru, inv: inv, why: why};
  }

  // ---------------------------------------------------------------- drawing
  var W = 1200, HH = 250, PL = 8, PR = 62, PT = 12, PB = 22, iw = W - PL - PR, ih = HH - PT - PB;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }
  function panel(nm, R){
    var st0 = nm.start, n = nm.n, i, mn = Infinity, mx = -Infinity;
    for (i = 0; i < n; i++){ if (nm.l[st0 + i] < mn) mn = nm.l[st0 + i]; if (nm.h[st0 + i] > mx) mx = nm.h[st0 + i]; }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.07 || 0.05; a -= pad; b += pad;
    function X(q){ return PL + q * (iw / n) + (iw / n) / 2; }
    function Y(p){ return PT + ih - (Math.log(p) - a) / (b - a) * ih; }
    var s = '', kq;
    for (kq = 0; kq <= 4; kq++){
      var lv = a + (b - a) * kq / 4, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) + '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' + Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 0) + '</text>';
    }
    var bw = iw / n, cw = Math.max(1.3, bw * 0.6);
    for (i = 0; i < n; i++){
      var q = st0 + i, o = nm.o[q], c = nm.c[q], up = c >= o, col = up ? 'var(--up)' : 'var(--down)';
      var x = X(i), yo = Y(o), yc = Y(c);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + Y(nm.h[q]).toFixed(1) + '" y2="' + Y(nm.l[q]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity=".8"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) + '" fill="' + col + '" opacity=".8"/>';
    }
    // OFF-PANEL SEGMENTS ARE MARKED, NOT LOST. The review found a resistance line drawn for 254
    // bars entirely above its panel (SVG y from -5 to -190): invisible, and the header still
    // counted it. Any part of a segment outside the price range now gets a triangle at the
    // panel edge, at the x where it is furthest out, in the segment's colour.
    var offCount = 0;
    function seg(list, col){
      var out = '', marks = '';
      list.forEach(function(g){
        function at(qq){ return Math.exp(g.g * (qq + st0) + g.c); }
        var q0 = g.before ? g.s0 : g.t0, ys = [[q0, Y(at(q0))], [g.t0, Y(at(g.t0))], [g.t1, Y(at(g.t1))]];
        var top = ys.reduce(function(a, p){ return p[1] < a[1] ? p : a; }), bot = ys.reduce(function(a, p){ return p[1] > a[1] ? p : a; });
        if (top[1] < PT){ marks += '<path d="M' + (X(Math.max(0, Math.min(n - 1, top[0]))) - 5).toFixed(1) + ',' + (PT + 9) + ' l5,-8 l5,8 z" fill="' + col + '" opacity=".9"/>'; offCount++; }
        if (bot[1] > PT + ih){ marks += '<path d="M' + (X(Math.max(0, Math.min(n - 1, bot[0]))) - 5).toFixed(1) + ',' + (PT + ih - 9) + ' l5,8 l5,-8 z" fill="' + col + '" opacity=".9"/>'; offCount++; }
        if (g.before){
          out += '<path d="M' + X(g.s0).toFixed(1) + ',' + Y(at(g.s0)).toFixed(1) + 'L' + X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + '" fill="none" stroke="' + col + '" stroke-width="1.2" stroke-dasharray="3 3" opacity=".5"/>';
          out += '<circle cx="' + X(g.s0).toFixed(1) + '" cy="' + Y(at(g.s0)).toFixed(1) + '" r="2.3" fill="' + col + '" opacity=".8"/>';
        }
        out += '<path d="M' + X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + 'L' + X(g.t1).toFixed(1) + ',' + Y(at(g.t1)).toFixed(1) + '" fill="none" stroke="' + col + '" stroke-width="2" stroke-linecap="round"/>';
      });
      return '<g clip-path="url(#clip' + nm.symbol + st0 + ')">' + out + '</g>' + marks;
    }
    s = '<defs><clipPath id="clip' + nm.symbol + st0 + '"><rect x="0" y="' + PT + '" width="' + W + '" height="' + ih + '"/></clipPath></defs>' + s;
    s += seg(R.segs.sup, 'var(--sup)') + seg(R.segs.res, 'var(--res)');
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (HH - 6) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
    }
    var ns = R.segs.sup.length + R.segs.res.length;
    return '<div class="panel"><div class="ph"><h2>' + esc(nm.symbol) + '</h2>' +
      '<span class="dt">' + esc(nm.dates[0]) + ' &rarr; ' + esc(nm.dates[n - 1]) + '</span>' +
      '<span class="st">' + ns + ' segments &middot; ' + Math.round(100 * R.cov / (2 * n)) + '% on &middot; through body ' +
      R.thru + ' / inverted ' + R.inv + (offCount ? ' &middot; <b>' + offCount + ' off panel &#9650;&#9660;</b>' : '') +
      ' &middot; over its whole history: walks ' + R.why.extended + ' (' + R.why.extended_pts + ' pts, cap ' + R.why.max_reach_hit + ')' +
      ', break pivots ' + R.why.syn + ' / ' + R.why.rat + ' ratified / ' + R.why.dropped + ' dropped' +
      ', stale deaths ' + R.why.stale + ' (' + R.why.stale_abandoned + ' respected then left, ' + R.why.stale_unconfirmed + ' never confirmed), unfit at birth ' + R.why.unfit +
      ', partner resets ' + R.why.pair + ', bars hidden for want of a partner ' + R.why.pair_hidden + ', pullbacks tolerated ' + R.why.body_poke + '</span></div>' +
      '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + HH + '">' + s + '</svg></div></div>';
  }

  // ---------------------------------------------------------------- the dials
  function params(){
    // EXACT NUMBERS, TYPED. A number box that is empty or below its floor is snapped back to
    // the floor (or its default) before it is read, so a half-typed value never runs.
    document.querySelectorAll('#dials input[type=number]').forEach(function(el){
      var x = parseFloat(el.value);
      if (!isFinite(x)) el.value = el.defaultValue;
      else if (el.min !== '' && x < parseFloat(el.min)) el.value = el.min;
      else if (el.max !== '' && x > parseFloat(el.max)) el.value = el.max;
    });
    var v = function(id){ return document.getElementById(id).value; };
    var chk = function(id){ return document.getElementById(id).checked; };
    var dh = parseFloat(v('dh')), dg = parseFloat(v('dg')), btol = parseFloat(v('btol'));
    return {
      k: parseInt(v('k'), 10), mp: parseInt(v('mp'), 10), carry: parseInt(v('carry'), 10),
      maxp: parseInt(v('maxp'), 10),
      dh: dh > 0 ? Math.log(1 + dh / 100) : INF,
      dg: dg > 0 ? Math.log(1 + dg / 100) / 252 : INF,
      mw: Math.log(1 + parseFloat(v('mw')) / 100),
      body: chk('body'), syn: chk('syn'), anchor: v('anchor'), aq: parseFloat(v('aq')), back: true,
      bdepth: Math.log(1 + parseFloat(v('bdepth')) / 100), bbars: parseInt(v('bbars'), 10),
      decay: parseFloat(v('decay')), dmode: v('dmode'), walk: chk('walk'),
      btol: btol < 0 ? -1 : Math.log(1 + btol / 100),
      height: v('height'), ttl: chk('ttl'), chain: v('chain'), reach: parseInt(v('reach'), 10),
      stalew: parseInt(v('stalew'), 10), staled: Math.log(1 + parseFloat(v('staled')) / 100), stalestat: v('stalestat'),
      fittol: parseFloat(v('fittol')) > 0 ? Math.log(1 + parseFloat(v('fittol')) / 100) : -1,
      pairbreak: chk('pairbreak'), pairdraw: chk('pairdraw'),
      // the touch tolerance is a LOG distance used raw, as the Python uses it -- the earlier
      // page converted it from a percentage and sat 1.2% narrow (review)
      fit: v('fit'), ttol: parseFloat(v('ttol')), mt: parseInt(v('mt'), 10)
    };
  }
  var timer = null;
  function redraw(){
    var P = params(), t0 = performance.now(), html = '', segs = 0, on = 0, thru = 0, inv = 0;
    D.names.forEach(function(nm){
      var R = recalc(nm, P);
      html += panel(nm, R);
      segs += R.segs.sup.length + R.segs.res.length; on += R.cov; thru += R.thru; inv += R.inv;
    });
    document.getElementById('grid').innerHTML = html;
    var side = 2 * D.window * D.names.length;
    document.getElementById('tot').textContent =
      segs + ' segments · ' + Math.round(100 * on / side) + '% on · through body ' + thru + ' · inverted ' + inv;
    document.getElementById('timing').textContent =
      'recomputed ' + D.names.length + ' names from bar 0 in ' + Math.round(performance.now() - t0) + ' ms';
  }
  function queue(){ if (timer) clearTimeout(timer); timer = setTimeout(redraw, 60); }
  // the clearance intercept is the regression's repair and does nothing to an envelope edge,
  // which clears every pivot by construction: greyed out rather than silently ignored
  function gate(){
    var env = document.getElementById('fit').value === 'env';
    var a = document.getElementById('anchor'); a.disabled = env; a.parentNode.style.opacity = env ? '.4' : '1';
    a.parentNode.title = env ? 'an envelope edge has no separate height: switch fit to regression' : '';
    // the number beside the age law means something different per law; when the law changes,
    // the number jumps to that law's sensible starting point (and is greyed where it has none)
    var dm = document.getElementById('dmode'), dv = document.getElementById('decay');
    if (dm.value !== dm.dataset.last){
      var start = {span: '0.8', linear: '0.8', halflife: '60', rank: '0.7', respect: '1'}[dm.value];
      if (dm.dataset.last !== undefined) dv.value = start;
      dm.dataset.last = dm.value;
    }
    dv.disabled = dm.value === 'respect'; dv.style.opacity = dv.disabled ? '.4' : '1';
    var aq = document.getElementById('aq'); aq.disabled = a.value !== 'quantile' || env; aq.parentNode.style.opacity = aq.disabled ? '.4' : '1';
  }
  // EVERY DIAL STARTS AT ITS DECLARED DEFAULT. Browsers restore form controls to their last
  // state on a reload, so an envelope tried yesterday came back today with the height dial
  // greyed out and nothing on the page saying why. The defaults are the `selected` and
  // `checked` attributes in the markup, and they win over whatever the browser remembered.
  document.querySelectorAll('#dials select').forEach(function(el){
    var o = el.querySelector('option[selected]'); if (o) el.value = o.value;
  });
  document.querySelectorAll('#dials input[type=checkbox]').forEach(function(el){ el.checked = el.defaultChecked; });
  document.querySelectorAll('#dials input[type=number]').forEach(function(el){ el.value = el.defaultValue; });
  // THE SETTINGS AS ONE LINE: every dial as id=value, so a setting can be copied out of the
  // page and pasted back in (or handed over) exactly. Booleans are on/off.
  var CTRL = Array.prototype.slice.call(document.querySelectorAll('#dials select, #dials input[type=checkbox], #dials input[type=number]'));
  function settingsLine(){
    return CTRL.map(function(el){ return el.id + '=' + (el.type === 'checkbox' ? (el.checked ? 'on' : 'off') : el.value); }).join(' ');
  }
  function applyLine(s){
    var n = 0;
    s.split(/\s+/).forEach(function(tok){
      var m = tok.match(/^([a-z]+)=(.+)$/); if (!m) return;
      var el = document.getElementById(m[1]); if (!el || CTRL.indexOf(el) < 0) return;
      if (el.type === 'checkbox') el.checked = (m[2] === 'on');
      else if (el.type === 'number'){ if (!isFinite(parseFloat(m[2]))) return; el.value = m[2]; }
      else { el.value = m[2]; if (el.value !== m[2]) return; }
      n++;
    });
    return n;
  }
  function showSettings(){ document.getElementById('settings').value = settingsLine(); }
  document.getElementById('copy').addEventListener('click', function(){
    var s = settingsLine(), inp = document.getElementById('settings'), note = document.getElementById('copied');
    inp.value = s; inp.select();
    var done = function(ok){ note.textContent = ok ? 'copied' : 'select the line and copy it'; setTimeout(function(){ note.textContent = ''; }, 2500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(function(){ done(true); }, function(){ done(false); });
    else done(false);
  });
  document.getElementById('apply').addEventListener('click', function(){
    var n = applyLine(document.getElementById('settings').value), note = document.getElementById('copied');
    note.textContent = n + ' settings applied'; setTimeout(function(){ note.textContent = ''; }, 2500);
    // an applied line carries its own number for the age law: do not let gate() overwrite it
    var dm = document.getElementById('dmode'); dm.dataset.last = dm.value;
    gate(); queue();
  });
  CTRL.forEach(function(el){
    el.addEventListener('change', function(){ gate(); showSettings(); queue(); });
    if (el.type === 'number') el.addEventListener('keydown', function(ev){ if (ev.key === 'Enter'){ ev.preventDefault(); el.blur(); } });
  });
  gate(); showSettings(); redraw();
})();
</script>
"""


def main() -> int:
    d = json.loads(SRC.read_text())
    payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value in the bars"
    out = HTML.replace("__DATA__", payload)

    def _bare(t):
        raise ValueError(f"bare {t} -- JSON.parse would throw and the page would render blank")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)
    OUT.write_text(out, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out) / 1e6:.2f} MB, "
          f"{len(d['names'])} names, {sum(x['m'] for x in d['names']):,} bars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
