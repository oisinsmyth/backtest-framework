"""THE GROW-RIGHT PAGE: D440's causal construction alone, every one of ITS dials, twelve names.

    uv run python scripts/d440_splice_causal_page.py            (reuses temp/d399_live_bars.json)

The oracle page (D439, `d439_splice_oracle_page.py`) carries four hindsight splitters and the
causal walk side by side; the principal asked for a page with the causal walk only, its dials
only, and the baseline he chose as the defaults. The JavaScript here is the same port, function
for function, minus the splitters: `envFit`/`fitWindow` (the envelope and the filters),
`splitParallel` (every candidate window grows at once, the longest survivor is drawn) and
`splitChain` (the oracle's restart made online, kept for comparison). `scripts/d440_causal_grow.py`
is the Python side; the two are held to parity by the `#parity` hook and `--dump`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_live_bars.json"
OUT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "temp" / "d440_causal_page.html")

HTML = r"""<title>Grow Right</title>
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
.sw.dash{border-top-style:dashed;border-top-width:1.5px;opacity:.7}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);
  max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">D440 &middot; the causal construction rebuilt from the oracle</div>
  <h1>Grow right</h1>
  <p class="lede">The oracle's left-to-right search with its two hindsight leaks removed. A window
    is a stretch of bars with a support line no low pierces and a resistance line no high pierces,
    passing every filter below. It is grown <b>one bar at a time</b>; the line drawn at each bar is
    the fit on the window <b>up to that bar</b>; nothing is drawn until the window is
    <em>min length</em> long. Every candidate window grows at once and the <b>longest survivor</b>
    is drawn, so the line at a bar depends only on the bars inside its own window.</p>
  <p class="lede">The solid stepped line is what a trader had. The faint dashed line behind it is
    the window's final fit &mdash; the channel the oracle would have drawn. The gap between them is
    the hindsight.</p>

  <div class="dials" id="dials">
    <span class="grp">
      <label>grow <select id="grow" title="parallel: every candidate window grows at once and the longest survivor is shown -- the line at a bar depends only on the bars inside its window. chain: the oracle's rule, one window at a time, the next search starting where the last broke -- path-dependent"><option value="parallel" selected>parallel (longest live)</option><option value="chain">chain (oracle restart)</option></select></label>
      <label>restart back <input type="number" id="back" value="9" min="0" max="200" step="1" title="after a break, only windows that started within this many bars before the break bar survive (parallel), or the next window may begin this many bars before it (chain). 0 = the oracle's rule; min length - 1 = a fresh window may show at the break bar itself"> bars</label>
      <label>at max length <select id="atmax" title="when the window reaches max length: end it, or drop the oldest bar each bar"><option value="end" selected>end</option><option value="slide">slide</option></select></label>
    </span>
    <span class="grp">
      <label>pierce tol <input type="number" id="tol" value="2" min="0" step="0.25" title="a wick may pierce a line by this much; a bar within it counts as a touch">%</label>
      <label>touches a side <input type="number" id="mt" value="2" min="2" step="1"></label>
      <label>contain <select id="basis"><option value="wick" selected>wicks</option><option value="body">bodies</option></select></label>
    </span>
    <span class="grp">
      <label>min length <input type="number" id="minlen" value="30" min="3" step="1" title="a window is drawn only once it is this long; also the seed length"> bars</label>
      <label>max length <input type="number" id="maxlen" value="1000" min="10" max="1000" step="10"> bars</label>
      <label>min width <input type="number" id="mw" value="0" min="0" step="0.5">%</label>
      <label>max width <input type="number" id="maxw" value="55" min="-1" step="1" title="-1 = off">%</label>
    </span>
    <span class="grp">
      <label>max offset <input type="number" id="maxoff" value="-1" min="-1" step="0.5" title="mean distance from price to the NEARER line, in % of price. -1 = off">%</label>
      <label>min touched <input type="number" id="mintd" value="-1" min="-1" max="100" step="1" title="share of bars within the pierce tolerance of either line. -1 = off">%</label>
      <label>max gradient gap <input type="number" id="tau" value="1.05" min="-1" step="0.05" title="the two gradients may differ by at most this fraction of the steeper one. Relative, so flat channels fail small values. -1 = off"></label>
    </span>
    <span class="grp">
      <label>break depth <input type="number" id="brk" value="-1" min="-1" step="0.25" title="a bar beyond the line the trader HAD (the previous bar's line, projected one bar) by more than this kills the window. -1 = off: the envelope re-tilts around every bar and nothing ever breaks">%</label>
      <label>break bars <input type="number" id="bbars" value="1" min="1" max="10" step="1" title="consecutive breaking bars needed"></label>
      <label>break on <select id="bon" title="which price must be beyond the line"><option value="close" selected>close</option><option value="wick">wick</option></select></label>
      <label>break side <select id="bside" title="either: a close beyond either line ends the window. trend: only the trend-side line can -- support in an uptrend, resistance in a downtrend; a breakout in the trend's own direction is continuation"><option value="both" selected>either line</option><option value="trend">trend side only</option></select></label>
    </span>
    <span class="grp">
      <label>survive <select id="surv" title="strict: a live window must keep passing every birth filter. loose: born under the full set, it survives under containment alone and ends only on a break, the survive width cap, or max length"><option value="strict" selected>strict</option><option value="loose">loose</option></select></label>
      <label>survive tol <input type="number" id="stol" value="4" min="0" step="0.5" title="loose only: the pierce tolerance a live window is re-fitted with; it decides which hull edge wins, by touches">%</label>
      <label>survive max width <input type="number" id="smaxw" value="-1" min="-1" step="1" title="loose only: a width cap that still ends a live window. -1 = off">%</label>
      <label><input type="checkbox" id="shade" checked> window's final fit</label>
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
    <span><i class="sw" style="border-color:var(--sup)"></i> support, as the trader had it</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance, as the trader had it</span>
    <span><i class="sw dash" style="border-color:var(--muted)"></i> the window's final fit (hindsight)</span>
    <span>gaps = no window of min length is alive</span>
    <span id="timing" style="margin-left:auto;font-family:IBM Plex Mono,monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>

  <div class="grid" id="grid"></div>

  <p class="note"><b>What kills a window.</b> The lines always contain every wick by construction,
    so containment never fails as a window grows. What fails is the shape of the two hulls: under
    the oracle's filters, <em>max gradient gap</em> ended 65% of windows and <em>max width</em>
    28%, and the same two blocked 96% of failed seeds; pierce tolerance never bound. The gap test
    is relative &mdash; the two gradients may differ by at most that fraction of the steeper one
    &mdash; so a flat channel with gradients of plus and minus a fraction of a percent fails small
    values even when the lines look parallel. Above 1 it admits opposite signs of similar size.</p>
  <p class="note"><b>A bar that breaks the line kills the window.</b> Off by default (break
    depth &minus;1), and then the envelope re-tilts around every bar: a window can live for
    hundreds of bars while the line it shows is redrawn under the trader's feet. With a depth
    set, each bar is compared with the line the trader <em>had</em> &mdash; the previous bar's
    fit projected one bar &mdash; and a close (or wick) beyond it by more than the depth is a
    break; <em>break bars</em> in a row kill the window. It is checked before the refit, so a
    broken window is never re-fitted into validity. <b>And a break kills the siblings too:</b>
    every live window that started more than <em>restart back</em> bars before the break bar
    dies with the shown one. Without that, the next-longest survivor &mdash; seeded a few bars
    later on mostly the same bars &mdash; was drawn in its place, and the line jumped instead of
    disappearing. So after a break nothing can be drawn for <em>min length</em> &minus;
    <em>restart back</em> &minus; 1 bars; raise <em>restart back</em> to shorten that gap. The
    Python side asserts that no shown line survives its own break, and that the assertion
    rejects a walk with the rule off.</p>
  <p class="note"><b>Strict to be born, loose to survive.</b> Under the trading line, 58% of
    shown-window deaths were the two hull lines pinching under the minimum width, 21% exceeding
    the maximum, 19% the gradient gap &mdash; not one was a bar through a line &mdash; and half were
    followed within five bars by a same-direction window overlapping the dead one: a gradient
    update dressed as an end. With <em>survive</em> = loose a window is born under the full filter
    set and then survives under containment alone; it ends only on a break of the line the trader
    had, the <em>survive max width</em> cap, or max length. The Python side asserts it.</p>
  <p class="note"><b>A line can still move without a break.</b> The support line is the edge of
    the lows' hull with the most touches. A new bar can hand that title to a different edge
    &mdash; often an older, lower one &mdash; and the line steps to it although no bar went
    through it. That is the fit choosing another valid line inside the same window, not a break,
    and the break rule cannot stop it; it is what the <em>max width</em> and <em>max gradient
    gap</em> dials bound.</p>
  <p class="note"><b>Two growth rules.</b> <em>Chain</em> is the oracle's restart made online: one
    window at a time, and when it breaks at bar t the next search starts at t (or <em>restart
    back</em> bars earlier). With restart back 0 and at max length end, the windows it finds are
    bar for bar the oracle's greedy channels grown one bar at a time &mdash; the Python side
    asserts it. But every boundary is then an artifact of the previous one and a change in
    <em>min length</em> re-times the whole series. <em>Parallel</em>, the default, has no chain:
    starting the walk a thousand bars later gives the same lines (asserted), and <em>min
    length</em> only decides which seeds qualify.</p>
  <p class="note"><b>The search starts 500 bars before each panel.</b> With the parallel rule that
    is exact once <em>max length</em> bars have passed; with the chain rule the phase can differ
    from a run from the name's first bar. The study runs from bar 0.</p>
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
  // A WORK BUDGET: every fit charges its own length; past the cap the search stops and the page
  // says so, rather than hanging.
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

  // ---------------------------------------------------------------- the two growth rules
  function newRun(t, f, A){
    return {a: t, b: t, A: A, As: [], gs: [], cs: [], gr: [], cr: [], ts: f.ts, tr: f.tr, w: 0, off: 0, td: 0, n: 0, last: null};
  }
  function push(r, f, A){
    r.b = f.b; r.A = A; r.As.push(A); r.gs.push(f.gs); r.cs.push(f.cs); r.gr.push(f.gr); r.cr.push(f.cr);
    r.w += f.w; r.off += f.off; r.td += f.td; r.n++; r.last = f;
  }
  function finish(out){ out.forEach(function(r){ r.w /= r.n; r.off /= r.n; r.td /= r.n; }); return out; }

  // THE BREAK RULE. The envelope contains every wick by construction, so a bar through the line
  // never fails the fit -- the hull re-tilts around it and the line is redrawn under the
  // trader's feet. Here the bar is compared with the line the trader HAD: the previous bar's
  // fit projected one bar. Beyond it by more than `brk` is a break; `bbars` in a row kill the
  // window. Checked BEFORE the refit, so a broken window is never re-fitted into validity.
  function broken(lo, hi, cl, t, f, P){
    if (P.brk < 0 || !f) return false;
    var sl = f.gs * t + f.cs, rl = f.gr * t + f.cr, sb, rb;
    if (P.bon === 'close'){ sb = cl[t] < sl - P.brk; rb = cl[t] > rl + P.brk; }
    else { sb = lo[t] < sl - P.brk; rb = hi[t] > rl + P.brk; }
    if (P.bside === 'trend'){            // only the trend-side line can end the window
      var g = f.gs + f.gr;
      if (g > 0) return sb;
      if (g < 0) return rb;
    }
    return sb || rb;
  }

  // HYSTERESIS: the filter set a LIVE window is re-fitted under. Strict = the birth set. Loose =
  // containment only: `stol` as the tolerance (it decides which hull edge wins, by touches), the
  // width, gap, offset and touch tests off, only the looser width cap `smaxw` kept. A hull edge
  // contains every point by construction, so under loose survival a window never dies of
  // containment -- the break rule IS the death.
  function survivalParams(P){
    if (P.surv !== 'loose') return P;
    var Q = {}, k; for (k in P) Q[k] = P[k];
    Q.tol = P.stol; Q.mt = 2; Q.mw = 0; Q.maxw = P.smaxw; Q.maxoff = -1; Q.mintd = -1; Q.tau = -1;
    return Q;
  }

  // PARALLEL: every candidate grows at once; the longest survivor is drawn.
  function splitParallel(lo, hi, cl, a0, a1, P){
    var out = [], run = null, live = [], t, k, PS = survivalParams(P);   // live: {A, f, nb}, oldest first
    var shown = null, shownNb = 0;                  // the line the trader SAW at the previous bar
    var bound = a0;                                 // no window may start before this (set by a break)
    for (t = a0; t < a1 && !BUDGET.hit; t++){
      // A BREAK OF THE SHOWN LINE KILLS EVERY WINDOW OLDER THAN `back`. Each window dying on
      // its own break was not enough: the next-longest sibling, sharing most of its bars, was
      // drawn in its place and the line jumped instead of disappearing.
      shownNb = broken(lo, hi, cl, t, shown, P) ? shownNb + 1 : 0;
      if (P.brk >= 0 && shownNb >= P.bbars){
        bound = t - P.back;                          // and the seeds that follow respect it too
        live = live.filter(function(w){ return w.A >= bound; });
        shownNb = 0;
      }
      var keep = [], best = null, f;
      for (k = 0; k < live.length; k++){              // oldest first: first survivor is longest
        var A = live[k].A, nb = broken(lo, hi, cl, t, live[k].f, P) ? live[k].nb + 1 : 0;
        if (P.brk >= 0 && nb >= P.bbars) continue;    // the bar broke the line the trader had
        if (t - A + 1 > P.maxlen){ if (P.atmax !== 'slide') continue; A = t - P.maxlen + 1; }
        if (keep.length && keep[keep.length - 1].A === A) continue;
        f = fitWindow(lo, hi, A, t, PS);            // a LIVE window: the survival set
        if (!f) continue;
        keep.push({A: A, f: f, nb: nb});
        if (!best) best = [A, f];
      }
      var s = t - P.minlen + 1;
      if (s >= bound && !(keep.length && keep[keep.length - 1].A === s)){
        f = fitWindow(lo, hi, s, t, P);
        if (f){ keep.push({A: s, f: f, nb: 0}); if (!best) best = [s, f]; }
      }
      live = keep;
      if (!best){ shown = null; if (run){ out.push(run); run = null; } continue; }
      shown = best[1];
      if (!run) run = newRun(t, best[1], best[0]);
      push(run, best[1], best[0]);
    }
    if (run) out.push(run);
    return finish(out);
  }

  // CHAIN: the oracle's restart made online. One window at a time; when it breaks at t the next
  // search starts at t - back.
  function splitChain(lo, hi, cl, a0, a1, P){
    var out = [], run = null, A = -1, bound = a0, t = a0, fprev = null, nb = 0, PS = survivalParams(P);
    while (t < a1 && !BUDGET.hit){
      var f = null;
      if (A >= 0){
        nb = broken(lo, hi, cl, t, fprev, P) ? nb + 1 : 0;
        var dead = P.brk >= 0 && nb >= P.bbars, L = t - A + 1;
        if (dead){ }
        else if (L <= P.maxlen) f = fitWindow(lo, hi, A, t, PS);
        else if (P.atmax === 'slide'){ A = t - P.maxlen + 1; f = fitWindow(lo, hi, A, t, PS); }
        if (f){ push(run, f, A); fprev = f; t++; continue; }
        out.push(run); run = null; A = -1; bound = t - P.back; fprev = null; nb = 0;
      }
      var s = t - P.minlen + 1;
      if (s >= bound && s >= a0){
        f = fitWindow(lo, hi, s, t, P);
        if (f){ A = s; run = newRun(t, f, A); push(run, f, A); fprev = f; nb = 0; }
      }
      t++;
    }
    if (run) out.push(run);
    return finish(out);
  }
  function causalWalk(lo, hi, cl, a0, a1, P){
    return P.grow === 'chain' ? splitChain(lo, hi, cl, a0, a1, P) : splitParallel(lo, hi, cl, a0, a1, P);
  }
  window.__d440 = {splitChain: splitChain, splitParallel: splitParallel, causalWalk: causalWalk, fitWindow: fitWindow, BUDGET: BUDGET};

  // PARITY HOOK: open with #parity and a digest per name is written into <pre id="parity">.
  function parityDigest(P){
    var out = [];
    D.names.forEach(function(nm){
      var st0 = nm.start, n = nm.n, marg = Math.min(P.maxlen, 500), lo0 = Math.max(0, st0 - marg), hi1 = Math.min(nm.m, st0 + n + marg);
      var LL = new Float64Array(nm.m), HHx = new Float64Array(nm.m), CL = new Float64Array(nm.m), i;
      for (i = lo0; i < hi1; i++){ LL[i] = Math.log(nm.l[i]); HHx[i] = Math.log(nm.h[i]); CL[i] = Math.log(nm.c[i]); }
      BUDGET.n = 0; BUDGET.hit = false;
      var runs = causalWalk(LL, HHx, CL, lo0, hi1, P), sg = 0, sc = 0, sr = 0, scr = 0;
      runs.forEach(function(r){ r.gs.forEach(function(x){ sg += x; }); r.cs.forEach(function(x){ sc += x; }); r.gr.forEach(function(x){ sr += x; }); r.cr.forEach(function(x){ scr += x; }); });
      out.push([nm.symbol, runs.length, runs.slice(0, 4).map(function(r){ return [r.a, r.b, r.A]; }), sg, sc, sr, scr, BUDGET.hit]);
    });
    return out;
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

    var marg = Math.min(P.maxlen, 500);
    var lo0 = Math.max(0, st0 - marg), hi1 = Math.min(nm.m, st0 + n + marg);
    var LL = new Float64Array(nm.m), HHx = new Float64Array(nm.m), CL = new Float64Array(nm.m);
    for (i = lo0; i < hi1; i++){
      if (P.basis === 'body'){
        LL[i] = Math.log(Math.min(nm.o[i], nm.c[i])); HHx[i] = Math.log(Math.max(nm.o[i], nm.c[i]));
      } else { LL[i] = Math.log(nm.l[i]); HHx[i] = Math.log(nm.h[i]); }
      CL[i] = Math.log(nm.c[i]);
    }
    var chans = causalWalk(LL, HHx, CL, lo0, hi1, P);

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

    var shown = 0, covered = 0, lens = [], wins = [], wid = [], offs = [], tds = [], body = '';
    chans.forEach(function(ch){
      var i0 = Math.max(ch.a, st0), i1 = Math.min(ch.b, st0 + n - 1);
      if (i1 < i0) return;
      lens.push(ch.b - ch.a + 1); wins.push(ch.b - ch.A + 1);
      shown++; covered += i1 - i0 + 1;
      var ps = '', pr = '', qq;
      for (qq = i0; qq <= i1; qq++){
        var k2 = qq - ch.a, sv = Math.exp(ch.gs[k2] * qq + ch.cs[k2]), rv = Math.exp(ch.gr[k2] * qq + ch.cr[k2]);
        ps += (qq === i0 ? 'M' : 'L') + X(qq - st0).toFixed(1) + ',' + Y(sv).toFixed(1);
        pr += (qq === i0 ? 'M' : 'L') + X(qq - st0).toFixed(1) + ',' + Y(rv).toFixed(1);
      }
      var kk = i1 - ch.a;
      wid.push(100 * (Math.exp(ch.gr[kk] * i1 + ch.cr[kk]) / Math.exp(ch.gs[kk] * i1 + ch.cs[kk]) - 1));
      offs.push(100 * Math.expm1(ch.off)); tds.push(100 * ch.td);
      if (P.shade && ch.last){
        var f0 = ch.last, wa = Math.max(ch.A, st0) - st0, wb = i1 - st0;
        body += '<path d="M' + X(wa).toFixed(1) + ',' + Y(Math.exp(f0.gs * (wa + st0) + f0.cs)).toFixed(1) + 'L' + X(wb).toFixed(1) + ',' + Y(Math.exp(f0.gs * (wb + st0) + f0.cs)).toFixed(1) + '" fill="none" stroke="var(--sup)" stroke-width="1" stroke-dasharray="3 4" opacity=".45"/>';
        body += '<path d="M' + X(wa).toFixed(1) + ',' + Y(Math.exp(f0.gr * (wa + st0) + f0.cr)).toFixed(1) + 'L' + X(wb).toFixed(1) + ',' + Y(Math.exp(f0.gr * (wb + st0) + f0.cr)).toFixed(1) + '" fill="none" stroke="var(--res)" stroke-width="1" stroke-dasharray="3 4" opacity=".45"/>';
      }
      body += '<path d="' + ps + '" fill="none" stroke="var(--sup)" stroke-width="2" stroke-linejoin="round"/>';
      body += '<path d="' + pr + '" fill="none" stroke="var(--res)" stroke-width="2" stroke-linejoin="round"/>';
    });
    s += '<g clip-path="url(#c' + nm.symbol + st0 + ')">' + body + '</g>';
    s = '<defs><clipPath id="c' + nm.symbol + st0 + '"><rect x="0" y="' + PT + '" width="' + W + '" height="' + ih + '"/></clipPath></defs>' + s;
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (HH - 6) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
    }
    function med(z){ z = z.slice().sort(function(p, q){ return p - q; }); return z.length ? z[Math.floor(z.length / 2)] : 0; }
    function avg(z){ return z.length ? z.reduce(function(p, q){ return p + q; }, 0) / z.length : 0; }
    var lsort = lens.slice().sort(function(p, q){ return p - q; });
    var lmin = lsort.length ? lsort[0] : 0, lmax = lsort.length ? lsort[lsort.length - 1] : 0;
    return {html: '<div class="panel"><div class="ph"><h2>' + esc(nm.symbol) + '</h2>' +
      '<span class="dt">' + esc(nm.dates[0]) + ' &rarr; ' + esc(nm.dates[n - 1]) + '</span>' +
      '<span class="st">' + shown + ' runs &middot; ' + Math.round(100 * covered / n) + '% covered &middot; drawn ' +
      lmin + '/' + med(lens) + '/' + lmax + ' &middot; window med ' + med(wins) + ' &middot; width ' + avg(wid).toFixed(0) +
      '% &middot; offset ' + avg(offs).toFixed(1) + '% &middot; touched ' + avg(tds).toFixed(0) + '%</span></div>' +
      '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + HH + '">' + s + '</svg></div></div>',
      n: shown, cov: covered, bars: n};
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
      grow: v('grow'), back: parseInt(v('back'), 10), atmax: v('atmax'),
      brk: parseFloat(v('brk')) >= 0 ? Math.log(1 + parseFloat(v('brk')) / 100) : -1,
      bbars: parseInt(v('bbars'), 10), bon: v('bon'), bside: v('bside'),
      surv: v('surv'), stol: Math.log(1 + parseFloat(v('stol')) / 100),
      smaxw: parseFloat(v('smaxw')) >= 0 ? Math.log(1 + parseFloat(v('smaxw')) / 100) : -1,
      shade: document.getElementById('shade').checked
    };
  }
  var CTRL = Array.prototype.slice.call(document.querySelectorAll('#dials select, #dials input[type=checkbox], #dials input[type=number]'));
  function line(){ return 'split=causal ' + CTRL.map(function(el){ return el.id + '=' + (el.type === 'checkbox' ? (el.checked ? 'on' : 'off') : el.value); }).join(' '); }
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
    document.getElementById('tot').textContent = tot + ' runs · ' + Math.round(100 * cov / bars) +
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
      var el = document.getElementById(m[1]); if (!el || CTRL.indexOf(el) < 0) return;   // foreign keys ignored
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
  if (location.hash.indexOf('#parity') === 0){
    // "#parity" digests the defaults; "#parity=<settings line>" applies that line first
    var ln = decodeURIComponent(location.hash.slice(8));
    if (ln){ document.getElementById('settings').value = ln; document.getElementById('apply').click(); }
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
