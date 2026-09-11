"""THE ORACLE PAGE: perfect-knowledge channels, every parameter adjustable, twelve names.

    uv run python scripts/d439_emit_live_bars.py     (or reuse temp/d399_live_bars.json)
    uv run python scripts/d439_splice_oracle_page.py

A PORT, NOT A CALL, exactly as the causal page is: `envelope_fit` and the greedy maximal-channel
search of `run_d439_oracle_ceiling.oracle_channels` are re-implemented in the page's JavaScript,
function for function. The page ships bars only.

THE ORACLE NEEDS NO HISTORY. The causal construction runs from each name's first bar because its
state accumulates; a perfect channel is a local object, so the page searches only the window plus
`max len` bars either side. That is why this page redraws in a fraction of the causal one's time.

WHAT IT DRAWS. Every maximal channel: a support line no low pierces by more than the tolerance,
a resistance line no high pierces, at least `touches` a side, at least `min width` wide, extended
as far as it survives, then the search restarts past it. Channels are disjoint and the gaps
between them are bars no channel covers -- which is what the trading rule will read as "no lines".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_live_bars.json"
OUT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "temp" / "d439_oracle_page.html")

HTML = r"""<title>Perfect Hindsight</title>
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
.dials input[type=number]{font:inherit;font-size:12.5px;width:5.2em;padding:3px 5px;
  border:1px solid var(--rule);border-radius:4px;background:var(--chip);color:var(--ink);
  font-variant-numeric:tabular-nums}
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
  <div class="eyebrow">D439 &middot; D440 &middot; perfect-knowledge channels, and the same algorithm made causal</div>
  <h1>Perfect hindsight</h1>
  <p class="lede">The best channel that could ever have been drawn, on the same twelve draws.
    Each one is fitted <b>knowing the whole window</b>: a support line no low pierces, a resistance
    line no high pierces, extended as far forward as it survives, then the search restarts past it.
    No pivots, no confirmation lag, no invalidation rules &mdash; this is what the lines look like
    when the estimator is removed entirely.</p>
  <p class="lede"><b>Grow right (CAUSAL)</b> is the left-to-right oracle with its two hindsight
    leaks removed: the window grows one bar at a time, the line at each bar is the fit on the
    window <b>up to that bar</b>, and nothing is drawn until the window is <em>min length</em>
    long. The solid stepped line is what a trader had; the faint dashed line behind it is the
    window's final fit &mdash; the channel the oracle would have shown. The gap between them is the
    hindsight. This is D440's candidate to replace D399's pivot construction.</p>

  <div class="dials" id="dials">
    <span class="grp">
      <label>split by <select id="split"><option value="causal" selected>grow right (CAUSAL)</option><option value="sliding">sliding (CAUSAL)</option><option value="greedy">left to right (oracle)</option><option value="seed">seed &amp; grow (oracle)</option><option value="pivot">pivot anchored (oracle)</option></select></label>
      <label>grow <select id="grow" title="grow right only. parallel: every candidate window grows at once and the longest survivor is shown -- the line at a bar depends only on the bars inside its window. chain: the oracle's rule, one window at a time, the next search starting where the last broke -- path-dependent"><option value="parallel" selected>parallel (longest live)</option><option value="chain">chain (oracle restart)</option></select></label>
      <label>restart back <input type="number" id="back" value="0" min="0" max="200" step="1" title="chain only: how many bars BEFORE the break bar the next window may begin. 0 = the oracle's rule (min length - 1 bars pass before anything is drawn again); min length - 1 = a fresh window may be tried at the break bar itself"> bars</label>
      <label>at max length <select id="atmax" title="grow right only: when the window reaches max length -- end it (the oracle's rule) or drop the oldest bar each bar"><option value="end" selected>end</option><option value="slide">slide</option></select></label>
      <label>window <input type="number" id="win" value="40" min="5" max="500" step="5" title="sliding only: the trailing bars fitted at each bar; nothing after the bar is used"> bars</label>
      <label>seed length <input type="number" id="seed" value="25" min="5" step="1"> bars</label>
      <label>start slack <input type="number" id="slack" value="0" min="0" max="120" step="1" title="left-to-right only: how far a channel's start may slide from the last one's end. 0 = the old behaviour"> bars</label>
      <label>pivot k <input type="number" id="pk" value="3" min="1" step="1"></label>
    </span>
    <span class="grp">
      <label>pierce tol <input type="number" id="tol" value="1.75" min="0" step="0.25">%</label>
      <label>touches a side <input type="number" id="mt" value="3" min="2" step="1"></label>
      <label>contain <select id="basis"><option value="wick" selected>wicks</option><option value="body">bodies</option></select></label>
    </span>
    <span class="grp">
      <label>min length <input type="number" id="minlen" value="20" min="3" step="1"> bars</label>
      <label>max length <input type="number" id="maxlen" value="1000" min="10" max="1000" step="10"> bars</label>
      <label>min width <input type="number" id="mw" value="0" min="0" step="0.5">%</label>
      <label>max width <input type="number" id="maxw" value="24" min="-1" step="1" title="-1 = off">%</label>
    </span>
    <span class="grp">
      <label>max offset <input type="number" id="maxoff" value="-1" min="-1" step="0.5" title="mean distance from price to the NEARER line, in % of price. -1 = off">%</label>
      <label>min touched <input type="number" id="mintd" value="35" min="-1" max="100" step="1" title="share of bars within the pierce tolerance of either line. -1 = off">%</label>
      <label>max gradient gap <input type="number" id="tau" value="0.4" min="-1" step="0.05" title="-1 = do not require the sides to be parallel"></label>
      <label><input type="checkbox" id="shade" checked> shade the channel</label>
    </span>
    <span class="tot" id="tot">&mdash;</span>
    <span class="grp" style="border-right:none;flex-basis:100%;gap:8px">
      <button id="copy" type="button">copy settings</button>
      <input id="settings" type="text" spellcheck="false" style="flex:1;min-width:280px;font:12px 'IBM Plex Mono',monospace;padding:4px 7px;border:1px solid var(--rule);border-radius:4px;background:var(--chip);color:var(--ink)">
      <button id="apply" type="button">apply</button>
      <span id="copied" style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--faint)"></span>
    </span>
  </div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support (no low below it)</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance (no high above it)</span>
    <span>gaps = no channel covers those bars</span>
    <span id="timing" style="margin-left:auto;font-family:IBM Plex Mono,monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>

  <div class="grid" id="grid"></div>

  <p class="note"><b>Three ways to split the series, and the first one was bad.</b>
    <em>Left to right</em> starts each channel where the last one ended and extends it as far as
    it will go &mdash; so every boundary is an artifact of the previous boundary, the first
    channel eats the next one's territory, and shifting the data by a bar changes the answer.
    <em>Seed &amp; grow</em> scores every short window, takes the strongest unclaimed one and
    grows it <b>both ways</b> until it fails: the channel grows out of its own best evidence and
    neither end is inherited from a neighbour. <em>Pivot anchored</em> only ever starts and ends
    a channel <b>at a swing point</b>, takes the strongest non-overlapping set, and is the
    closest to how a line actually gets drawn. Seed &amp; grow is the default.
    <em>Sliding (CAUSAL)</em> is the odd one out: the same fitter and filters on the
    <b>trailing</b> <em>window</em> bars only, read at the right edge, nothing after the bar
    consulted. It is not an oracle at all &mdash; it is the oracle's algorithm made causal, a
    candidate to replace D399's pivot construction in the study's causal arm. Each bar's level is
    its own window's line, so the drawn line steps rather than running straight.</p>
  <p class="note"><b>Grow right, causally: two growth rules.</b> <em>Chain</em> is the oracle's
    restart made online: one window at a time, and when it breaks at bar t the next search starts
    at t, so nothing can be drawn again before t + <em>min length</em> &minus; 1 (<em>restart
    back</em> lets the next window start earlier). With <em>restart back</em> 0 and <em>at max
    length</em> end, the windows it finds are bar for bar the oracle's greedy channels grown one
    bar at a time &mdash; the Python side asserts it. But every boundary is then an artifact of
    the previous one, and a change in <em>min length</em> re-times the whole series: <b>that is
    why the window swung</b>. <em>Parallel</em>, the default, removes the chain: every candidate
    window grows at once, each bar spawns a seed from the last <em>min length</em> bars if they
    pass, a window is dropped the bar it fails, and the <b>longest survivor</b> is drawn. The line
    at a bar then depends only on the bars inside its own window &mdash; starting the walk a
    thousand bars later gives the same lines (asserted) &mdash; and <em>min length</em> only decides
    which seeds qualify. <em>At max length</em> = slide keeps a window at <em>max length</em> by
    dropping its oldest bar instead of ending it.</p>
  <p class="note"><b>The oracle needs no history.</b> The causal construction runs from each name's
    first bar because its state accumulates; a perfect channel is a local object, so the search
    here covers the window plus <em>max length</em> bars either side (capped at 500). The grow-right
    walk starts at that margin too; with the parallel rule this is exact once <em>max length</em>
    bars have passed, with the chain rule the phase can differ from a run from the name's first
    bar. The study runs from bar 0.</p>
  <p class="note"><b>Max gradient gap</b> is off by default (&minus;1). Requiring the two sides to
    be parallel here would make the trading rule's own similarity gate vacuous when the study
    runs, so parallelism is left to the rule and this dial exists only to look at what it costs.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);

  // ---------------------------------------------------------------- the envelope, ported
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
  // most touches within tol, then longest span, then first -- envelope_fit's tie-break exactly
  function envFit(x, y, lower, tol){
    var n = x.length;
    if (n < 2) return null;
    var edges = hullEdges(x, y, lower), best = null, q;
    for (q = 0; q < edges.length; q++){
      var i = edges[q][0], j = edges[q][1], dx = x[j] - x[i];
      if (!(dx > 0)) continue;
      var g = (y[j] - y[i]) / dx, c = y[i] - g * x[i], touches = 0, bad = false, k;
      for (k = 0; k < n; k++){
        var r = y[k] - (g * x[k] + c);
        if (lower ? (r < -tol) : (r > tol)){ bad = true; break; }
        if (Math.abs(r) <= tol) touches++;
      }
      if (bad) continue;
      if (!best || touches > best[2] || (touches === best[2] && dx > best[3])) best = [g, c, touches, dx];
    }
    return best;
  }

  // ---------------------------------------------------------------- one window, fitted
  // A WORK BUDGET, because a dial can ask for more than a browser can do. Every fit charges its
  // own length; past the cap the search stops and the page says so, rather than hanging. A max
  // length of 5,000 did exactly that: the growth loop re-fitted the whole window at every step,
  // which is O(L^2), and the search span widened to each name's entire history.
  var BUDGET = {n: 0, cap: 30e6, hit: false};
  function fitWindow(lo, hi, a, b, P){
    var m = b - a + 1, x = new Array(m), yl = new Array(m), yh = new Array(m), k;
    if (m < 2) return null;
    BUDGET.n += m;
    if (BUDGET.n > BUDGET.cap){ BUDGET.hit = true; return null; }
    for (k = 0; k < m; k++){ x[k] = a + k; yl[k] = lo[a + k]; yh[k] = hi[a + k]; }
    var S = envFit(x, yl, true, P.tol), R = envFit(x, yh, false, P.tol);
    if (!S || !R || S[2] < P.mt || R[2] < P.mt) return null;
    var w0 = (R[0] * x[0] + R[1]) - (S[0] * x[0] + S[1]);
    var w1 = (R[0] * x[m - 1] + R[1]) - (S[0] * x[m - 1] + S[1]);
    if (Math.min(w0, w1) < P.mw) return null;
    if (P.maxw >= 0 && Math.max(w0, w1) > P.maxw) return null;
    if (P.tau >= 0 && Math.abs(S[0] - R[0]) > P.tau * Math.max(Math.abs(S[0]), Math.abs(R[0]))) return null;
    // HOW FAR PRICE SITS FROM THE NEARER LINE. Width alone does not say whether a channel is
    // real: price can ping-pong between the edges of a wide one (good) or sit in the middle of
    // it (the lines are then decoration). Per bar, the low's distance above support and the
    // high's distance below resistance; the smaller of the two is the distance to the nearer
    // edge. Its mean is the channel's offset, and a bar within `tol` of either line is a touch.
    var offSum = 0, nTouch = 0;
    for (k = 0; k < m; k++){
      var ds = yl[k] - (S[0] * x[k] + S[1]);
      var dr = (R[0] * x[k] + R[1]) - yh[k];
      var d = ds < dr ? ds : dr;
      if (d > 0) offSum += d;
      if (d <= P.tol) nTouch++;
    }
    var off = offSum / m, td = nTouch / m;
    if (P.maxoff >= 0 && off > P.maxoff) return null;
    if (P.mintd >= 0 && td < P.mintd) return null;
    return {a: a, b: b, gs: S[0], cs: S[1], gr: R[0], cr: R[1], ts: S[2], tr: R[2],
            w: (w0 + w1) / 2, off: off, td: td, score: S[2] + R[2]};
  }

  // ---------------------------------------------------------------- three ways to split
  // LEFT TO RIGHT (the first version): start where the last channel ended and extend maximally.
  // Every boundary is an artifact of the previous boundary, and the first channel eats the next
  // one's territory. Kept only so the others can be compared against it.
  // GROWTH BY STRIDE, not one bar at a time. Extending a window re-fits it, so growing to L bars
  // one at a time costs O(L^2). Here the step starts at an eighth of the current length and
  // halves on failure down to 1, so the far end is still found to the exact bar but in O(L log L).
  function growTo(lo, hi, A, B, limit, P, dir){
    var cur = null, stride = Math.max(1, (B - A + 1) >> 3);
    while (stride >= 1){
      var nA = A, nB = B;
      if (dir > 0) nB = Math.min(limit, B + stride); else nA = Math.max(limit, A - stride);
      if ((dir > 0 && nB <= B) || (dir < 0 && nA >= A)){ if (stride === 1) break; stride >>= 1; continue; }
      if (nB - nA + 1 > P.maxlen){ if (stride === 1) break; stride >>= 1; continue; }
      var f = fitWindow(lo, hi, nA, nB, P);
      if (f){ cur = f; A = nA; B = nB; stride = Math.max(1, (B - A + 1) >> 3); }
      else { if (stride === 1) break; stride >>= 1; }
      if (BUDGET.hit) break;
    }
    return {A: A, B: B, f: cur};
  }

  // LEFT TO RIGHT, WITH THE START ALLOWED TO SLIDE. Nailing each channel's left edge to wherever
  // the last one ended is why the first version could never grow: an arbitrary bar is not a
  // channel's start, a minimum-length window there fits by construction, and two more bars break
  // it -- so every channel came out at the floor. Here the start may slide up to `slack` bars to
  // find one that grows, and the longest result wins. slack = 0 is the old behaviour exactly.
  function splitGreedy(lo, hi, a0, a1, P){
    var out = [], a = a0;
    while (a + P.minlen <= a1 && !BUDGET.hit){
      var best = null, s;
      for (s = a; s <= a + P.slack && s + P.minlen <= a1; s++){
        var seed = fitWindow(lo, hi, s, s + P.minlen - 1, P);
        if (!seed) continue;
        var g = growTo(lo, hi, s, s + P.minlen - 1, a1 - 1, P, +1);
        var cand = g.f || seed;
        if (!best || (cand.b - cand.a) > (best.b - best.a)
            || ((cand.b - cand.a) === (best.b - best.a) && cand.score > best.score)) best = cand;
        if (BUDGET.hit) break;
      }
      if (!best){ a += 1; continue; }
      out.push(best); a = best.b + 1;
    }
    return out;
  }

  // SEED AND GROW, BEST FIRST: score every short window, take the strongest unclaimed seed, grow
  // it BOTH ways while it stays valid, claim its bars, repeat. The channel grows out of its own
  // strongest evidence, so neither end is an artifact of where a neighbour happened to stop.
  function splitSeed(lo, hi, a0, a1, P){
    var seeds = [], a;
    for (a = a0; a + P.seed <= a1; a++){
      var f = fitWindow(lo, hi, a, a + P.seed - 1, P);
      if (f) seeds.push(f);
    }
    seeds.sort(function(p, q){ return (q.score - p.score) || (p.w - q.w) || (p.a - q.a); });
    var claimed = new Uint8Array(a1 + 1), out = [], i, j;
    for (i = 0; i < seeds.length; i++){
      var s = seeds[i], free = true;
      for (j = s.a; j <= s.b; j++) if (claimed[j]){ free = false; break; }
      if (!free) continue;
      // the free run either side: growth may not cross a bar another channel already owns
      var rl = s.b, ll = s.a;
      while (rl + 1 < a1 && !claimed[rl + 1]) rl++;
      while (ll - 1 >= a0 && !claimed[ll - 1]) ll--;
      var A = s.a, B = s.b, cur = s, grew = true;
      while (grew && !BUDGET.hit){
        grew = false;
        var gr = growTo(lo, hi, A, B, rl, P, +1);
        if (gr.B > B){ A = gr.A; B = gr.B; cur = gr.f || cur; grew = true; }
        var gl = growTo(lo, hi, A, B, ll, P, -1);
        if (gl.A < A){ A = gl.A; B = gl.B; cur = gl.f || cur; grew = true; }
      }
      if (B - A + 1 < P.minlen || BUDGET.hit) continue;
      for (j = A; j <= B; j++) claimed[j] = 1;
      out.push(cur);
    }
    out.sort(function(p, q){ return p.a - q.a; });
    return out;
  }

  // PIVOT ANCHORED, BEST FIRST: candidates run from one swing point to another -- where a
  // chartist actually starts and ends a line -- and the strongest non-overlapping set is taken.
  function pivotIdx(lo, hi, a0, a1, k){
    var out = [], i, j;
    for (i = a0 + k; i < a1 - k; i++){
      var isHi = true, isLo = true;
      for (j = i - k; j <= i + k; j++){
        if (hi[j] > hi[i]) isHi = false;
        if (lo[j] < lo[i]) isLo = false;
        if (!isHi && !isLo) break;
      }
      if (isHi || isLo) out.push(i);
    }
    return out;
  }
  function splitPivot(lo, hi, a0, a1, P){
    var pv = pivotIdx(lo, hi, a0, a1, P.pk), cand = [], i, j;
    for (i = 0; i < pv.length && !BUDGET.hit; i++){
      for (j = i + 1; j < pv.length; j++){
        var L = pv[j] - pv[i] + 1;
        if (L < P.minlen) continue;
        if (L > P.maxlen) break;
        var f = fitWindow(lo, hi, pv[i], pv[j], P);
        if (f) cand.push(f);
        if (BUDGET.hit) break;
      }
    }
    cand.sort(function(p, q){ return (q.score - p.score) || ((q.b - q.a) - (p.b - p.a)) || (p.a - q.a); });
    var claimed = new Uint8Array(a1 + 1), out = [], k2;
    for (i = 0; i < cand.length; i++){
      var c = cand[i], free = true;
      for (k2 = c.a; k2 <= c.b; k2++) if (claimed[k2]){ free = false; break; }
      if (!free) continue;
      for (k2 = c.a; k2 <= c.b; k2++) claimed[k2] = 1;
      out.push(c);
    }
    out.sort(function(p, q){ return p.a - q.a; });
    return out;
  }

  // SLIDING, CAUSAL: the same fitter and the same filters, on the TRAILING `win` bars only, read
  // at the window's right edge. At bar t the lines are those of the channel fitted on
  // [t-win+1, t]; nothing after t is consulted. This is the oracle's algorithm made causal --
  // the principal's "sliding forward window" -- and it is what the study's CAUSAL arm can use
  // in place of D399's pivot construction. Consecutive bars with a valid window are drawn as
  // one run; each bar's level is its OWN window's line, so the drawn line can step bar to bar.
  function splitSliding(lo, hi, a0, a1, P){
    var out = [], t, run = null;
    for (t = a0 + P.win - 1; t < a1; t++){
      var f = fitWindow(lo, hi, t - P.win + 1, t, P);
      if (BUDGET.hit) break;
      if (!f){ if (run){ out.push(run); run = null; } continue; }
      // one run per stretch of valid bars; the lines are per bar (step), kept as arrays
      if (!run) run = {a: t, b: t, gs: [], cs: [], gr: [], cr: [], ts: f.ts, tr: f.tr, w: 0, off: 0, td: 0, n: 0, sliding: true};
      run.b = t; run.gs.push(f.gs); run.cs.push(f.cs); run.gr.push(f.gr); run.cr.push(f.cr);
      run.w += f.w; run.off += f.off; run.td += f.td; run.n++;
    }
    if (run) out.push(run);
    out.forEach(function(r){ r.w /= r.n; r.off /= r.n; r.td /= r.n; });
    return out;
  }

  // GROW RIGHT, CAUSALLY (D440): the left-to-right oracle with its two hindsight leaks removed.
  // The oracle seeds a min-length window, grows it while it passes every filter, stops at the
  // first bar that fails and restarts there. Every one of those decisions reads only bars up to
  // the current one. What sees the future is (1) drawing the FINAL fit at every interior bar and
  // (2) drawing the first min-length-1 bars at all, since a window that never reaches the
  // minimum is never drawn. Here the window grows ONE BAR AT A TIME, the line at bar t is the
  // fit on [A, t], and a bar is drawn only once its window is min length long. `back` lets the
  // next window start before the break bar; `atmax` says what happens at max length.
  function splitCausal(lo, hi, a0, a1, P){
    var out = [], run = null, A = -1, bound = a0, t = a0;
    function push(r, f){
      r.b = f.b; r.gs.push(f.gs); r.cs.push(f.cs); r.gr.push(f.gr); r.cr.push(f.cr);
      r.w += f.w; r.off += f.off; r.td += f.td; r.n++; r.last = f;
    }
    while (t < a1 && !BUDGET.hit){
      var f = null;
      if (A >= 0){
        var L = t - A + 1;
        if (L <= P.maxlen) f = fitWindow(lo, hi, A, t, P);
        else if (P.atmax === 'slide'){ A = t - P.maxlen + 1; f = fitWindow(lo, hi, A, t, P); }
        if (f){ push(run, f); t++; continue; }
        out.push(run); run = null; A = -1; bound = t - P.back;   // t is the break bar
      }
      var s = t - P.minlen + 1;
      if (s >= bound && s >= a0){
        f = fitWindow(lo, hi, s, t, P);
        if (f){
          A = s;
          run = {a: t, b: t, A: A, gs: [], cs: [], gr: [], cr: [], ts: f.ts, tr: f.tr, w: 0, off: 0, td: 0, n: 0, sliding: true, causal: true};
          push(run, f);
        }
      }
      t++;
    }
    if (run) out.push(run);
    out.forEach(function(r){ r.w /= r.n; r.off /= r.n; r.td /= r.n; });
    return out;
  }
  // PARALLEL GROWTH: the chain's path dependence removed. The chain shows one window at a time
  // and starts the next search where the last one broke, so every boundary is an artifact of the
  // previous one and a change in min length re-times the whole series -- what the principal saw
  // as "the window swings". Here EVERY candidate grows at once: each bar spawns a seed from the
  // last min-length bars if they pass, every live window is extended by one bar and dropped when
  // it fails, and the LONGEST survivor is drawn. The line at bar t depends only on the bars
  // inside its own window. Still one pass, still nothing after the bar. `back` has no meaning
  // here (there is no restart); `atmax` does.
  function splitParallel(lo, hi, a0, a1, P){
    var out = [], run = null, live = [], t, k;
    function push(r, f, A){
      r.b = f.b; r.A = A; r.As.push(A); r.gs.push(f.gs); r.cs.push(f.cs); r.gr.push(f.gr); r.cr.push(f.cr);
      r.w += f.w; r.off += f.off; r.td += f.td; r.n++; r.last = f;
    }
    for (t = a0; t < a1 && !BUDGET.hit; t++){
      var keep = [], best = null, f;
      for (k = 0; k < live.length; k++){                  // oldest first: first survivor is longest
        var A = live[k];
        if (t - A + 1 > P.maxlen){ if (P.atmax !== 'slide') continue; A = t - P.maxlen + 1; }
        if (keep.length && keep[keep.length - 1] === A) continue;
        f = fitWindow(lo, hi, A, t, P);
        if (!f) continue;
        keep.push(A);
        if (!best) best = [A, f];
      }
      var s = t - P.minlen + 1;
      if (s >= a0 && !(keep.length && keep[keep.length - 1] === s)){
        f = fitWindow(lo, hi, s, t, P);
        if (f){ keep.push(s); if (!best) best = [s, f]; }
      }
      live = keep;
      if (!best){ if (run){ out.push(run); run = null; } continue; }
      if (!run) run = {a: t, b: t, A: best[0], As: [], gs: [], cs: [], gr: [], cr: [], ts: best[1].ts, tr: best[1].tr, w: 0, off: 0, td: 0, n: 0, sliding: true, causal: true};
      push(run, best[1], best[0]);
    }
    if (run) out.push(run);
    out.forEach(function(r){ r.w /= r.n; r.off /= r.n; r.td /= r.n; });
    return out;
  }
  function causalWalk(lo, hi, a0, a1, P){
    return P.grow === 'chain' ? splitCausal(lo, hi, a0, a1, P) : splitParallel(lo, hi, a0, a1, P);
  }
  window.__d440 = {splitCausal: splitCausal, splitParallel: splitParallel, causalWalk: causalWalk, fitWindow: fitWindow, BUDGET: BUDGET};
  // PARITY HOOK: open the page with #parity and the grow-right walk's digest per name (run
  // count, first windows, sums of the four line parameters) is written into <pre id="parity">,
  // for a headless browser to dump and Python to compare against its own walk.
  function parityDigest(P){
    var out = [];
    D.names.forEach(function(nm){
      var st0 = nm.start, n = nm.n, marg = Math.min(P.maxlen, 500), lo0 = Math.max(0, st0 - marg), hi1 = Math.min(nm.m, st0 + n + marg);
      var LL = new Float64Array(nm.m), HHx = new Float64Array(nm.m), i;
      for (i = lo0; i < hi1; i++){ LL[i] = Math.log(nm.l[i]); HHx[i] = Math.log(nm.h[i]); }
      BUDGET.n = 0; BUDGET.hit = false;
      var runs = causalWalk(LL, HHx, lo0, hi1, P), sg = 0, sc = 0, sr = 0, scr = 0;
      runs.forEach(function(r){ r.gs.forEach(function(x){ sg += x; }); r.cs.forEach(function(x){ sc += x; }); r.gr.forEach(function(x){ sr += x; }); r.cr.forEach(function(x){ scr += x; }); });
      out.push([nm.symbol, runs.length, runs.slice(0, 4).map(function(r){ return [r.a, r.b, r.A]; }), sg, sc, sr, scr, BUDGET.hit]);
    });
    return out;
  }

  function oracleChannels(lo, hi, a0, a1, P){
    if (P.split === 'causal') return causalWalk(lo, hi, a0, a1, P);
    if (P.split === 'seed') return splitSeed(lo, hi, a0, a1, P);
    if (P.split === 'pivot') return splitPivot(lo, hi, a0, a1, P);
    if (P.split === 'sliding') return splitSliding(lo, hi, a0, a1, P);
    return splitGreedy(lo, hi, a0, a1, P);
  }

  // ---------------------------------------------------------------- drawing
  var W = 1200, HH = 250, PL = 8, PR = 62, PT = 12, PB = 22, iw = W - PL - PR, ih = HH - PT - PB;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }

  function panel(nm, P){
    var st0 = nm.start, n = nm.n, i, mn = Infinity, mx = -Infinity;
    for (i = 0; i < n; i++){ if (nm.l[st0 + i] < mn) mn = nm.l[st0 + i]; if (nm.h[st0 + i] > mx) mx = nm.h[st0 + i]; }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.07 || 0.05; a -= pad; b += pad;
    function X(q){ return PL + q * (iw / n) + (iw / n) / 2; }
    function Y(p){ return PT + ih - (Math.log(p) - a) / (b - a) * ih; }

    // the search covers the window plus a margin: a perfect channel is local, and the margin is
    // capped so that a large `max length` cannot widen the search to a name's entire history
    var marg = Math.min(P.maxlen, 500);
    var lo0 = Math.max(0, st0 - marg), hi1 = Math.min(nm.m, st0 + n + marg);
    var LL = new Float64Array(nm.m), HHx = new Float64Array(nm.m);
    for (i = lo0; i < hi1; i++){
      if (P.basis === 'body'){
        LL[i] = Math.log(Math.min(nm.o[i], nm.c[i])); HHx[i] = Math.log(Math.max(nm.o[i], nm.c[i]));
      } else { LL[i] = Math.log(nm.l[i]); HHx[i] = Math.log(nm.h[i]); }
    }
    var chans = oracleChannels(LL, HHx, lo0, hi1, P);

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

    var shown = 0, covered = 0, lens = [], wid = [], offs = [], tds = [];
    var body = '', shade = '';
    chans.forEach(function(ch){
      var i0 = Math.max(ch.a, st0), i1 = Math.min(ch.b, st0 + n - 1);
      // STATS OVER THE CHANNELS ACTUALLY DRAWN. `lens` used to be pushed before this test, so
      // the median length was taken over every channel found in the +-500-bar search margin --
      // mostly short ones that are never drawn -- while the count and the coverage were over the
      // drawn ones. The header read "7 channels, 95% covered, median 22 bars", which cannot all
      // be true of the same set.
      if (i1 < i0) return;
      lens.push(ch.b - ch.a + 1);
      shown++; covered += i1 - i0 + 1;
      var u0 = i0 - st0, u1 = i1 - st0;
      if (ch.sliding){
        // per-bar levels: each bar's own trailing window's line, joined into a stepping path
        var ps = '', pr = '', q;
        for (q = i0; q <= i1; q++){
          var k2 = q - ch.a, sv = Math.exp(ch.gs[k2] * q + ch.cs[k2]), rv = Math.exp(ch.gr[k2] * q + ch.cr[k2]);
          ps += (q === i0 ? 'M' : 'L') + X(q - st0).toFixed(1) + ',' + Y(sv).toFixed(1);
          pr += (q === i0 ? 'M' : 'L') + X(q - st0).toFixed(1) + ',' + Y(rv).toFixed(1);
        }
        var kk = i1 - ch.a;
        wid.push(100 * (Math.exp(ch.gr[kk] * i1 + ch.cr[kk]) / Math.exp(ch.gs[kk] * i1 + ch.cs[kk]) - 1));
        offs.push(100 * Math.expm1(ch.off)); tds.push(100 * ch.td);
        if (ch.causal && P.shade && ch.last){
          // THE WINDOW'S SHADOW: the last fit, drawn faintly over the whole window [A, b]. This is
          // the channel the oracle would have shown; the solid stepped line is what a trader
          // actually had at each bar. The gap between them is the hindsight.
          var f0 = ch.last, wa = Math.max(ch.A, st0) - st0, wb = i1 - st0;
          body += '<path d="M' + X(wa).toFixed(1) + ',' + Y(Math.exp(f0.gs * (wa + st0) + f0.cs)).toFixed(1) + 'L' + X(wb).toFixed(1) + ',' + Y(Math.exp(f0.gs * (wb + st0) + f0.cs)).toFixed(1) + '" fill="none" stroke="var(--sup)" stroke-width="1" stroke-dasharray="3 4" opacity=".45"/>';
          body += '<path d="M' + X(wa).toFixed(1) + ',' + Y(Math.exp(f0.gr * (wa + st0) + f0.cr)).toFixed(1) + 'L' + X(wb).toFixed(1) + ',' + Y(Math.exp(f0.gr * (wb + st0) + f0.cr)).toFixed(1) + '" fill="none" stroke="var(--res)" stroke-width="1" stroke-dasharray="3 4" opacity=".45"/>';
        }
        body += '<path d="' + ps + '" fill="none" stroke="var(--sup)" stroke-width="2" stroke-linejoin="round"/>';
        body += '<path d="' + pr + '" fill="none" stroke="var(--res)" stroke-width="2" stroke-linejoin="round"/>';
        return;
      }
      function sup(q){ return Math.exp(ch.gs * (q + st0) + ch.cs); }
      function res(q){ return Math.exp(ch.gr * (q + st0) + ch.cr); }
      wid.push(100 * (Math.exp(ch.gr * i1 + ch.cr) / Math.exp(ch.gs * i1 + ch.cs) - 1));
      offs.push(100 * Math.expm1(ch.off)); tds.push(100 * ch.td);
      if (P.shade){
        shade += '<path d="M' + X(u0).toFixed(1) + ',' + Y(res(u0)).toFixed(1) +
          'L' + X(u1).toFixed(1) + ',' + Y(res(u1)).toFixed(1) +
          'L' + X(u1).toFixed(1) + ',' + Y(sup(u1)).toFixed(1) +
          'L' + X(u0).toFixed(1) + ',' + Y(sup(u0)).toFixed(1) + 'Z" fill="var(--muted)" opacity=".07"/>';
      }
      body += '<path d="M' + X(u0).toFixed(1) + ',' + Y(sup(u0)).toFixed(1) + 'L' + X(u1).toFixed(1) + ',' + Y(sup(u1)).toFixed(1) + '" fill="none" stroke="var(--sup)" stroke-width="2" stroke-linecap="round"/>';
      body += '<path d="M' + X(u0).toFixed(1) + ',' + Y(res(u0)).toFixed(1) + 'L' + X(u1).toFixed(1) + ',' + Y(res(u1)).toFixed(1) + '" fill="none" stroke="var(--res)" stroke-width="2" stroke-linecap="round"/>';
    });
    s += '<g clip-path="url(#c' + nm.symbol + st0 + ')">' + shade + body + '</g>';
    s = '<defs><clipPath id="c' + nm.symbol + st0 + '"><rect x="0" y="' + PT + '" width="' + W + '" height="' + ih + '"/></clipPath></defs>' + s;
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (HH - 6) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
    }
    lens.sort(function(p, q){ return p - q; });
    var med = lens.length ? lens[Math.floor(lens.length / 2)] : 0;
    var lmin = lens.length ? lens[0] : 0, lmax = lens.length ? lens[lens.length - 1] : 0;
    function avg(z){ return z.length ? z.reduce(function(p, q){ return p + q; }, 0) / z.length : 0; }
    var mwid = avg(wid), moff = avg(offs), mtd = avg(tds);
    return {html: '<div class="panel"><div class="ph"><h2>' + esc(nm.symbol) + '</h2>' +
      '<span class="dt">' + esc(nm.dates[0]) + ' &rarr; ' + esc(nm.dates[n - 1]) + '</span>' +
      '<span class="st">' + shown + ' channels &middot; ' + Math.round(100 * covered / n) + '% covered &middot; length ' +
      lmin + '/' + med + '/' + lmax + ' &middot; width ' + mwid.toFixed(0) + '% &middot; <b>offset ' +
      moff.toFixed(1) + '%</b> &middot; touched ' + mtd.toFixed(0) + '%</span></div>' +
      '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + HH + '">' + s + '</svg></div></div>',
      n: shown, cov: covered, bars: n, off: offs, td: tds};
  }

  // ---------------------------------------------------------------- the dials
  function params(){
    document.querySelectorAll('#dials input[type=number]').forEach(function(el){
      var x = parseFloat(el.value);
      if (!isFinite(x)) el.value = el.defaultValue;
      else if (el.min !== '' && x < parseFloat(el.min)) el.value = el.min;
      else if (el.max !== '' && x > parseFloat(el.max)) el.value = el.max;   // a typo cannot hang it
    });
    var v = function(id){ return document.getElementById(id).value; };
    return {
      tol: Math.log(1 + parseFloat(v('tol')) / 100), mt: parseInt(v('mt'), 10),
      basis: v('basis'), minlen: parseInt(v('minlen'), 10), maxlen: parseInt(v('maxlen'), 10),
      mw: Math.log(1 + parseFloat(v('mw')) / 100), tau: parseFloat(v('tau')),
      maxw: parseFloat(v('maxw')) >= 0 ? Math.log(1 + parseFloat(v('maxw')) / 100) : -1,
      maxoff: parseFloat(v('maxoff')) >= 0 ? Math.log(1 + parseFloat(v('maxoff')) / 100) : -1,
      mintd: parseFloat(v('mintd')) >= 0 ? parseFloat(v('mintd')) / 100 : -1,
      split: v('split'), seed: parseInt(v('seed'), 10), pk: parseInt(v('pk'), 10),
      slack: parseInt(v('slack'), 10), win: parseInt(v('win'), 10),
      back: parseInt(v('back'), 10), atmax: v('atmax'), grow: v('grow'),
      shade: document.getElementById('shade').checked
    };
  }
  var CTRL = Array.prototype.slice.call(document.querySelectorAll('#dials select, #dials input[type=checkbox], #dials input[type=number]'));
  function line(){ return CTRL.map(function(el){ return el.id + '=' + (el.type === 'checkbox' ? (el.checked ? 'on' : 'off') : el.value); }).join(' '); }
  function show(){ document.getElementById('settings').value = line(); }
  var timer = null;
  function redraw(){
    var P = params(), t0 = performance.now(), html = '', tot = 0, cov = 0, bars = 0;
    BUDGET.n = 0; BUDGET.hit = false;
    D.names.forEach(function(nm){
      var R = panel(nm, P);
      html += R.html; tot += R.n; cov += R.cov; bars += R.bars;
    });
    document.getElementById('grid').innerHTML = html;
    document.getElementById('tot').textContent = tot + ' channels · ' + Math.round(100 * cov / bars) +
      '% of bars covered' + (BUDGET.hit ? ' · ⚠ SEARCH TRUNCATED — lower max length' : '');
    document.getElementById('tot').style.color = BUDGET.hit ? 'var(--down)' : 'var(--ink)';
    document.getElementById('timing').textContent = 'fitted ' + D.names.length + ' names in ' + Math.round(performance.now() - t0) + ' ms';
    show();
  }
  function queue(){ if (timer) clearTimeout(timer); timer = setTimeout(redraw, 60); }
  document.getElementById('copy').addEventListener('click', function(){
    var s = line(), inp = document.getElementById('settings'), note = document.getElementById('copied');
    inp.value = s; inp.select();
    var done = function(ok){ note.textContent = ok ? 'copied' : 'select the line and copy it'; setTimeout(function(){ note.textContent = ''; }, 2500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(function(){ done(true); }, function(){ done(false); });
    else done(false);
  });
  document.getElementById('apply').addEventListener('click', function(){
    document.getElementById('settings').value.split(/\s+/).forEach(function(tok){
      var m = tok.match(/^([a-z]+)=(.+)$/); if (!m) return;
      var el = document.getElementById(m[1]); if (!el || CTRL.indexOf(el) < 0) return;
      if (el.type === 'checkbox') el.checked = (m[2] === 'on'); else el.value = m[2];
    });
    queue();
  });
  document.querySelectorAll('#dials select').forEach(function(el){ var o = el.querySelector('option[selected]'); if (o) el.value = o.value; });
  document.querySelectorAll('#dials input[type=checkbox]').forEach(function(el){ el.checked = el.defaultChecked; });
  document.querySelectorAll('#dials input[type=number]').forEach(function(el){ el.value = el.defaultValue; });
  CTRL.forEach(function(el){
    el.addEventListener('change', queue);
    if (el.type === 'number') el.addEventListener('keydown', function(ev){ if (ev.key === 'Enter'){ ev.preventDefault(); el.blur(); } });
  });
  redraw();
  if (location.hash === '#parity'){
    var pre = document.createElement('pre'); pre.id = 'parity';
    pre.textContent = JSON.stringify(parityDigest(params()));
    document.body.appendChild(pre);
  }
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
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out) / 1e6:.2f} MB, {len(d['names'])} names)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
