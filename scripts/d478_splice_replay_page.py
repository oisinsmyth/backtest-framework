"""THE REPLAY PAGE: what the grow-right algorithm draws at each time step, one name, one bar at a
time -- the demonstration the principal asked for.

    uv run python scripts/d478_splice_replay_page.py          (reuses temp/d399_live_bars.json)

At bar t the page shows only bars <= t, the window the trader is shown (the longest live one:
its support and resistance fitted on [A, t], projected a few bars forward as a trader would),
every other live candidate window faintly, the trail of levels the trader was shown on earlier
bars (so the line's movement over time is visible), and the trading rule's state -- in a long,
in a short, or flat -- with the running P&L of the open trade. Scrub, step or play.

The engine is the D478 page's JavaScript, function for function (`envFit`, `fitWindow`,
`broken`, the parallel and chain walks); the walk here only records what each bar saw. Opened
with `#parity` it writes, for every name, the count of shown bars inside the panel and the sums
of the four line parameters over them, which a headless dump hands to Python for comparison
with `d478_causal_grow.causal_channels` on the same bars and line.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_live_bars.json"
OUT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "temp" / "d478_replay_page.html")

HTML = r"""<title>Step by Step</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#fff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7; --chip:#f1eee9;
  --up:#1c6b52; --down:#a93d2c; --res:#c2410c; --sup:#1d4ed8; --warn:#8a6d1f;
  --long:rgba(28,107,82,.10); --short:rgba(169,61,44,.10);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
    --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f;
    --long:rgba(76,174,135,.14); --short:rgba(224,112,92,.14);
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
  --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f;
  --long:rgba(76,174,135,.14); --short:rgba(224,112,92,.14);
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
.bar{background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 16px;
  display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}
.bar label{display:inline-flex;align-items:center;gap:7px;font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;color:var(--muted);white-space:nowrap}
.bar select,.bar input[type=number],.bar input[type=text]{font:inherit;font-size:12.5px;padding:3px 6px;
  border:1px solid var(--rule);border-radius:4px;background:var(--chip);color:var(--ink)}
.bar input[type=number]{width:5.2em;font-variant-numeric:tabular-nums}
.bar button{font:inherit;font-size:12.5px;padding:4px 10px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink);cursor:pointer;min-width:2.4em}
.bar button:hover{border-color:var(--muted)}
.bar button.on{border-color:var(--sup);color:var(--sup)}
.bar input[type=range]{flex:1;min-width:260px;accent-color:var(--sup)}
.stage{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.stage svg{display:block;width:100%;height:auto}
.read{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px 18px;
  padding:10px 16px 12px;border-top:1px solid var(--rule-soft);font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.read b{display:block;color:var(--ink);font-weight:500;font-size:14px}
.read .st-long b{color:var(--up)} .read .st-short b{color:var(--down)}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:20px;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.sw.thin{border-top-width:1px;opacity:.6}
.sw.dot{border-top-style:dotted}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
#parity{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint)}
</style>

<div class="wrap">
  <div class="eyebrow">D478 &middot; what the trader saw, bar by bar</div>
  <h1>Step by step</h1>
  <p class="lede">The grow-right construction replayed one bar at a time. At each step the page
    shows <b>only the bars up to that step</b>, the window the trader is shown &mdash; the longest
    live one, its two lines fitted on the bars inside it and projected a few bars forward &mdash;
    every other live candidate faintly, the trail of levels shown on earlier bars, and the
    trading rule's state. Nothing after the current bar is consulted; the future bars can be
    ghosted in to see what the line did not know.</p>

  <div class="bar" id="ctl">
    <label>name <select id="name"></select></label>
    <label>min gradient <input type="number" id="gmin" value="25" min="0" step="5" title="the trading rule's floor, % per year: a trend needs both lines steeper than this, same sign">%/yr</label>
    <label><input type="checkbox" id="cands" checked> candidates</label>
    <label><input type="checkbox" id="trail" checked> trail</label>
    <label><input type="checkbox" id="ghost"> ghost the future</label>
  </div>
  <div class="bar" id="dials">
    <label>grow <select id="grow" title="parallel: every candidate window grows at once and the longest survivor is shown. chain: the oracle's rule, one window at a time"><option value="parallel" selected>parallel</option><option value="chain">chain</option></select></label>
    <label>restart back <input type="number" id="back" value="9" min="0" max="200" step="1" title="after a break, only windows that started within this many bars before the break bar survive (parallel), or the next window may begin this many bars before it (chain)"></label>
    <label>at max <select id="atmax"><option value="end" selected>end</option><option value="slide">slide</option></select></label>
    <label>pierce tol <input type="number" id="tol" value="2" min="0" step="0.25">%</label>
    <label>touches <input type="number" id="mt" value="2" min="2" step="1"></label>
    <label>contain <select id="basis"><option value="wick" selected>wicks</option><option value="body">bodies</option></select></label>
    <label>min length <input type="number" id="minlen" value="30" min="3" step="1"></label>
    <label>max length <input type="number" id="maxlen" value="1000" min="10" max="1000" step="10"></label>
    <label>min width <input type="number" id="mw" value="5.5" min="0" step="0.5">%</label>
    <label>max width <input type="number" id="maxw" value="55" min="-1" step="1" title="-1 = off">%</label>
    <label>max offset <input type="number" id="maxoff" value="6.5" min="-1" step="0.5" title="mean distance from price to the nearer line. -1 = off">%</label>
    <label>min touched <input type="number" id="mintd" value="10" min="-1" max="100" step="1" title="share of bars within the pierce tolerance of either line. -1 = off">%</label>
    <label>gradient gap <input type="number" id="tau" value="1" min="-1" step="0.05" title="the two gradients may differ by at most this fraction of the steeper one. -1 = off"></label>
    <label>break depth <input type="number" id="brk" value="-1" min="-1" step="0.25" title="a close (or wick) beyond the line the trader had by more than this kills the window and every window older than restart back. -1 = off">%</label>
    <label>break bars <input type="number" id="bbars" value="1" min="1" max="10" step="1"></label>
    <label>break on <select id="bon"><option value="close" selected>close</option><option value="wick">wick</option></select></label>
    <label>break side <select id="bside" title="either: a close beyond either line ends the window. trend: only the trend-side line can -- support in an uptrend, resistance in a downtrend; a breakout in the trend's own direction is continuation"><option value="both">either line</option><option value="trend" selected>trend side only</option></select></label>
    <label>survive <select id="surv" title="strict: a live window must keep passing every birth filter. loose: born under the full set, it survives under containment alone and ends only on a break, the survive width cap, or max length"><option value="strict">strict</option><option value="loose" selected>loose</option></select></label>
    <label>survive tol <input type="number" id="stol" value="4" min="0" step="0.5" title="loose only: the pierce tolerance a live window is re-fitted with; it decides which hull edge wins, by touches">%</label>
    <label>survive max width <input type="number" id="smaxw" value="40" min="-1" step="1" title="loose only: a width cap that still ends a live window. -1 = off">%</label>
  </div>
  <div class="bar">
    <button id="copy" type="button">copy settings</button>
    <input id="settings" type="text" spellcheck="false" style="flex:1;min-width:280px;font:12px 'IBM Plex Mono',monospace;padding:4px 7px;border:1px solid var(--rule);border-radius:4px;background:var(--chip);color:var(--ink)">
    <button id="apply" type="button">apply</button>
    <span id="copied" style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>
  <div class="bar">
    <button id="first" type="button" title="first bar">&#9198;</button>
    <button id="back" type="button" title="one bar back">&#9664;</button>
    <button id="play" type="button" title="play / pause">&#9654;</button>
    <button id="fwd" type="button" title="one bar forward">&#9654;&#9654;</button>
    <label>speed <select id="speed"><option value="400">slow</option><option value="150" selected>medium</option><option value="50">fast</option></select></label>
    <input type="range" id="pos" min="0" max="10" value="0" step="1">
    <span id="where" style="font-family:'IBM Plex Mono',monospace;font-size:12.5px;color:var(--ink);min-width:16em;text-align:right"></span>
  </div>

  <div class="stage">
    <svg id="svg" viewBox="0 0 1200 420"></svg>
    <div class="read" id="read"></div>
  </div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support, shown</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance, shown</span>
    <span><i class="sw dot" style="border-color:var(--muted)"></i> projected forward (not yet fitted)</span>
    <span><i class="sw thin" style="border-color:var(--sup)"></i> other live candidates</span>
    <span><i class="sw thin" style="border-color:var(--faint)"></i> trail of shown levels</span>
    <span id="parity" style="margin-left:auto"></span>
  </div>

  <p class="note"><b>Strict to be born, loose to survive.</b> Under the trading line, 58% of
    shown-window deaths were the two hull lines pinching under the minimum width, 21% exceeding
    the maximum, 19% the gradient gap &mdash; not one was a bar through a line &mdash; and half were
    followed within five bars by a same-direction window overlapping the dead one: a gradient
    update dressed as an end. With <em>survive</em> = loose a window is born under the full filter
    set and then survives under containment alone; it ends only on a break of the line the trader
    had, the survive width cap, or max length. The gradient still updates every bar. With the
    break rule off nothing ends before max length, and the footer says so.</p>
  <p class="note"><b>How to read it.</b> A window is a stretch of bars whose lows all sit above
    one line and whose highs all sit below another, passing the filters in the settings line. The
    walk keeps every such window alive and grows each by one bar per step; a window dies the bar
    it fails, and the longest survivor is the one drawn. Its lines are re-fitted every bar on the
    bars inside it, which is why they step. The dotted continuation is the projection a trader
    would draw from the current fit &mdash; it is not part of the construction and nothing is
    fitted on it. Candidates are the shorter live windows waiting to take over. The trail is the
    level the trader was shown on each earlier bar, so a jump in the trail is a jump the trader
    saw.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var DEFAULT_LINE = 'split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000 mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=2 bbars=1 bon=close bside=trend surv=loose stol=4 smaxw=40';

  // ---------------------------------------------------------------- the engine (the D478 page's, verbatim)
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
  var BUDGET = {n: 0, cap: 60e6, hit: false};
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

  // ---------------------------------------------------------------- the walks, recording what each bar saw
  // rec[t] = {shown: fit|null, A: start|-1, live: [{A, f}...]}  for t in [a0, a1)
  function walkParallel(lo, hi, cl, a0, a1, P){
    var rec = new Array(a1), live = [], shown = null, shownNb = 0, bound = a0, t, k, PS = survivalParams(P);
    for (t = a0; t < a1 && !BUDGET.hit; t++){
      shownNb = broken(lo, hi, cl, t, shown, P) ? shownNb + 1 : 0;
      var purged = false;
      if (P.brk >= 0 && shownNb >= P.bbars){ bound = t - P.back; live = live.filter(function(w){ return w.A >= bound; }); shownNb = 0; purged = true; }
      var keep = [], best = null, f;
      for (k = 0; k < live.length; k++){
        var A = live[k].A, nb = broken(lo, hi, cl, t, live[k].f, P) ? live[k].nb + 1 : 0;
        if (P.brk >= 0 && nb >= P.bbars) continue;
        if (t - A + 1 > P.maxlen){ if (P.atmax !== 'slide') continue; A = t - P.maxlen + 1; }
        if (keep.length && keep[keep.length - 1].A === A) continue;
        f = fitWindow(lo, hi, A, t, PS);            // a LIVE window: the survival set
        if (!f) continue;
        keep.push({A: A, f: f, nb: nb});
        if (!best) best = keep[keep.length - 1];
      }
      var s = t - P.minlen + 1;
      if (s >= bound && !(keep.length && keep[keep.length - 1].A === s)){
        f = fitWindow(lo, hi, s, t, P);
        if (f){ keep.push({A: s, f: f, nb: 0}); if (!best) best = keep[keep.length - 1]; }
      }
      live = keep;
      shown = best ? best.f : null;
      rec[t] = {shown: shown, A: best ? best.A : -1, live: keep.map(function(w){ return {A: w.A, f: w.f}; }), purged: purged};
    }
    return rec;
  }
  function walkChain(lo, hi, cl, a0, a1, P){
    var rec = new Array(a1), A = -1, bound = a0, t = a0, fprev = null, nb = 0, PS = survivalParams(P);
    while (t < a1 && !BUDGET.hit){
      var f = null, purged = false;
      if (A >= 0){
        nb = broken(lo, hi, cl, t, fprev, P) ? nb + 1 : 0;
        var dead = P.brk >= 0 && nb >= P.bbars, L = t - A + 1;
        if (dead){ purged = true; }
        else if (L <= P.maxlen) f = fitWindow(lo, hi, A, t, PS);
        else if (P.atmax === 'slide'){ A = t - P.maxlen + 1; f = fitWindow(lo, hi, A, t, PS); }
        if (f){ rec[t] = {shown: f, A: A, live: [{A: A, f: f}], purged: false}; fprev = f; t++; continue; }
        A = -1; bound = t - P.back; fprev = null; nb = 0;
      }
      var s = t - P.minlen + 1;
      if (s >= bound && s >= a0){
        f = fitWindow(lo, hi, s, t, P);
        if (f){ A = s; fprev = f; nb = 0; }
      }
      rec[t] = f ? {shown: f, A: A, live: [{A: A, f: f}], purged: purged} : {shown: null, A: -1, live: [], purged: purged};
      t++;
    }
    return rec;
  }

  // ---------------------------------------------------------------- settings
  function parseLine(line){
    var P = {tol: Math.log(1.02), mt: 2, basis: 'wick', minlen: 30, maxlen: 1000, mw: 0, maxw: Math.log(1.55),
             maxoff: -1, mintd: -1, tau: 1.05, grow: 'parallel', back: 9, atmax: 'end', brk: -1, bbars: 1, bon: 'close',
             surv: 'strict', stol: Math.log(1.04), smaxw: -1, bside: 'both'};
    line.split(/\s+/).forEach(function(tok){
      var m = tok.match(/^([a-z]+)=(.+)$/); if (!m) return;
      var k = m[1], v = m[2], x = parseFloat(v);
      if (k === 'tol' || k === 'mw' || k === 'stol') P[k] = Math.log(1 + x / 100);
      else if (k === 'maxw' || k === 'maxoff' || k === 'brk' || k === 'smaxw') P[k] = x >= 0 ? Math.log(1 + x / 100) : -1;
      else if (k === 'mintd') P[k] = x >= 0 ? x / 100 : -1;
      else if (k === 'mt' || k === 'minlen' || k === 'maxlen' || k === 'back' || k === 'bbars') P[k] = parseInt(v, 10);
      else if (k === 'tau') P[k] = x;
      else if (k === 'basis' || k === 'atmax' || k === 'grow' || k === 'bon' || k === 'surv' || k === 'bside') P[k] = v;
    });
    P.maxlen = Math.min(P.maxlen, 1000);
    return P;
  }

  // ---------------------------------------------------------------- state
  var W = 1200, HH = 420, PL = 8, PR = 62, PT = 14, PB = 24, iw = W - PL - PR, ih = HH - PT - PB, PROJ = 8;
  var nm = null, P = null, REC = null, lo0 = 0, st0 = 0, n = 0, t = 0, timer = null, ya = 0, yb = 1;
  var LL, HHx, CL, STATE, TRADES;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }
  function X(q){ return PL + q * (iw / n) + (iw / n) / 2; }
  function Y(p){ return PT + ih - (Math.log(p) - ya) / (yb - ya) * ih; }
  function gpct(g){ return 100 * Math.expm1(g * 252); }

  // ---------------------------------------------------------------- dials <-> settings line
  var CTRL = Array.prototype.slice.call(document.querySelectorAll('#dials select, #dials input[type=number]'));
  function params(){
    document.querySelectorAll('#dials input[type=number]').forEach(function(el){
      var x = parseFloat(el.value);
      if (!isFinite(x)) el.value = el.defaultValue;
      else if (el.min !== '' && x < parseFloat(el.min)) el.value = el.min;
      else if (el.max !== '' && x > parseFloat(el.max)) el.value = el.max;
    });
    return parseLine(line());
  }
  function line(){ return 'split=causal ' + CTRL.map(function(el){ return el.id + '=' + el.value; }).join(' '); }
  function applyLine(s){
    s.split(/\s+/).forEach(function(tok){
      var m = tok.match(/^([a-z]+)=(.+)$/); if (!m) return;
      var el = document.getElementById(m[1]); if (!el || CTRL.indexOf(el) < 0) return;
      el.value = m[2];
    });
  }
  document.getElementById('copy').addEventListener('click', function(){
    var s = line(), inp = document.getElementById('settings'), note = document.getElementById('copied');
    inp.value = s; inp.select();
    var done = function(ok){ note.textContent = ok ? 'copied' : 'select the line and copy it'; setTimeout(function(){ note.textContent = ''; }, 2500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(function(){ done(true); }, function(){ done(false); });
    else done(false);
  });

  function build(){
    var sel = document.getElementById('name');
    nm = D.names[parseInt(sel.value, 10)];
    P = params();
    document.getElementById('settings').value = line();
    st0 = nm.start; n = nm.n;
    var marg = Math.min(P.maxlen, 500);
    lo0 = Math.max(0, st0 - marg);
    var hi1 = st0 + n;                      // the walk never reads past the panel: causal by construction
    LL = new Float64Array(nm.m); HHx = new Float64Array(nm.m); CL = new Float64Array(nm.m);
    var i, mn = Infinity, mx = -Infinity;
    for (i = lo0; i < hi1; i++){
      if (P.basis === 'body'){ LL[i] = Math.log(Math.min(nm.o[i], nm.c[i])); HHx[i] = Math.log(Math.max(nm.o[i], nm.c[i])); }
      else { LL[i] = Math.log(nm.l[i]); HHx[i] = Math.log(nm.h[i]); }
      CL[i] = Math.log(nm.c[i]);
    }
    for (i = 0; i < n; i++){ if (nm.l[st0 + i] < mn) mn = nm.l[st0 + i]; if (nm.h[st0 + i] > mx) mx = nm.h[st0 + i]; }
    ya = Math.log(mn); yb = Math.log(mx); var pad = (yb - ya) * 0.10 || 0.05; ya -= pad; yb += pad;
    BUDGET.n = 0; BUDGET.hit = false;
    var t0 = performance.now();
    REC = P.grow === 'chain' ? walkChain(LL, HHx, CL, lo0, hi1, P) : walkParallel(LL, HHx, CL, lo0, hi1, P);
    // the trading rule's state at each bar, and the trades it makes inside the panel
    var g = Math.log(1 + parseFloat(document.getElementById('gmin').value) / 100) / 252;
    STATE = new Int8Array(nm.m);
    for (i = st0; i < hi1; i++){
      var r = REC[i];
      if (!r || !r.shown) continue;
      if (r.shown.gs > g && r.shown.gr > g) STATE[i] = 1;
      else if (r.shown.gs < -g && r.shown.gr < -g) STATE[i] = -1;
    }
    TRADES = [];
    var q = st0;
    while (q < hi1){
      var d = STATE[q];
      if (d === 0){ q++; continue; }
      var u = q + 1;
      while (u < hi1 && STATE[u] === d) u++;
      var x = Math.min(u, hi1 - 1);
      if (x > q) TRADES.push({e: q, x: x, d: d, gross: d * (CL[x] - CL[q])});
      q = u;
    }
    document.getElementById('pos').max = n - 1;
    var ms = Math.round(performance.now() - t0);
    document.getElementById('parity').textContent = 'walked ' + n + ' bars (+' + (st0 - lo0) + ' of run-in) in ' + ms + ' ms' + (BUDGET.hit ? ' -- SEARCH TRUNCATED, lower max length' : '') +
      (P.surv === 'loose' && P.brk < 0 && P.smaxw < 0 ? ' -- LOOSE SURVIVAL WITH THE BREAK RULE OFF: windows end only at max length' : '');
    if (t > n - 1) t = n - 1;
    draw();
  }

  function draw(){
    var q = st0 + t, s = '', i, kq;
    var ghost = document.getElementById('ghost').checked, cands = document.getElementById('cands').checked, trail = document.getElementById('trail').checked;
    // trade shading: every completed trade up to now, and the open one
    TRADES.forEach(function(tr){
      if (tr.e > q) return;
      var x1 = Math.min(tr.x, q);
      s += '<rect x="' + (X(tr.e - st0) - iw / n / 2).toFixed(1) + '" y="' + PT + '" width="' + ((x1 - tr.e + 1) * iw / n).toFixed(1) + '" height="' + ih + '" fill="var(--' + (tr.d > 0 ? 'long' : 'short') + ')"/>';
    });
    for (kq = 0; kq <= 4; kq++){
      var lv = ya + (yb - ya) * kq / 4, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) + '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' + Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 0) + '</text>';
    }
    var bw = iw / n, cw = Math.max(1.3, bw * 0.6);
    for (i = 0; i < n; i++){
      var qq = st0 + i, o = nm.o[qq], c = nm.c[qq], up = c >= o, col = up ? 'var(--up)' : 'var(--down)';
      var fut = i > t;
      if (fut && !ghost) continue;
      var op = fut ? '.18' : '.85', x = X(i), yo = Y(o), yc = Y(c);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + Y(nm.h[qq]).toFixed(1) + '" y2="' + Y(nm.l[qq]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity="' + op + '"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) + '" fill="' + col + '" opacity="' + op + '"/>';
    }
    // the trail: the level the trader was shown at each earlier bar
    if (trail){
      var ps = '', pr = '', open = false;
      for (i = 0; i < t; i++){
        var r0 = REC[st0 + i];
        if (!r0 || !r0.shown){ open = false; continue; }
        var u = st0 + i, sv = Math.exp(r0.shown.gs * u + r0.shown.cs), rv = Math.exp(r0.shown.gr * u + r0.shown.cr);
        ps += (open ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(sv).toFixed(1);
        pr += (open ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(rv).toFixed(1);
        open = true;
      }
      s += '<path d="' + ps + '" fill="none" stroke="var(--sup)" stroke-width="1" opacity=".35" stroke-linejoin="round"/>';
      s += '<path d="' + pr + '" fill="none" stroke="var(--res)" stroke-width="1" opacity=".35" stroke-linejoin="round"/>';
    }
    var r = REC[q];
    function seg(f, A, b, cls, w, op, dash, kind){
      var g = kind === 's' ? f.gs : f.gr, c = kind === 's' ? f.cs : f.cr;
      var x0 = Math.max(A, st0) - st0, x1 = b - st0;
      return '<path d="M' + X(x0).toFixed(1) + ',' + Y(Math.exp(g * (x0 + st0) + c)).toFixed(1) + 'L' + X(x1).toFixed(1) + ',' + Y(Math.exp(g * (x1 + st0) + c)).toFixed(1) + '" fill="none" stroke="var(--' + cls + ')" stroke-width="' + w + '" opacity="' + op + '"' + (dash ? ' stroke-dasharray="2 4"' : '') + ' stroke-linecap="round"/>';
    }
    if (r){
      if (cands) r.live.forEach(function(w){
        if (r.shown && w.A === r.A) return;
        s += seg(w.f, w.A, q, 'sup', 1, .28, false, 's') + seg(w.f, w.A, q, 'res', 1, .28, false, 'r');
      });
      if (r.shown){
        var pe = Math.min(q + PROJ, st0 + n - 1);
        s += seg(r.shown, r.A, q, 'sup', 2.4, 1, false, 's') + seg(r.shown, r.A, q, 'res', 2.4, 1, false, 'r');
        if (pe > q){ s += seg(r.shown, q, pe, 'sup', 1.4, .7, true, 's') + seg(r.shown, q, pe, 'res', 1.4, .7, true, 'r'); }
        if (r.A >= st0) s += '<line x1="' + X(r.A - st0).toFixed(1) + '" x2="' + X(r.A - st0).toFixed(1) + '" y1="' + PT + '" y2="' + (PT + ih) + '" stroke="var(--faint)" stroke-dasharray="3 5" opacity=".6"/>';
      }
    }
    // the cursor
    s += '<line x1="' + X(t).toFixed(1) + '" x2="' + X(t).toFixed(1) + '" y1="' + PT + '" y2="' + (PT + ih) + '" stroke="var(--ink)" opacity=".35"/>';
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (HH - 8) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
    }
    document.getElementById('svg').innerHTML = s;
    document.getElementById('pos').value = t;
    document.getElementById('where').textContent = esc(nm.dates[t]) + '  bar ' + (t + 1) + ' / ' + n;
    // the readout
    var sh = r && r.shown, cl = nm.c[q], html = '';
    html += '<div><b>' + esc(nm.symbol) + '</b>' + esc(nm.dates[t]) + '</div>';
    html += '<div><b>' + (r ? r.live.length : 0) + '</b>live windows</div>';
    html += '<div><b>' + (sh ? (q - r.A + 1) + ' bars' : '&mdash;') + '</b>shown window' + (sh && r.A >= st0 ? ', from ' + esc(nm.dates[r.A - st0]) : sh ? ', from before the panel' : '') + '</div>';
    html += '<div><b>' + (sh ? gpct(sh.gs).toFixed(0) + '% / ' + gpct(sh.gr).toFixed(0) + '%' : '&mdash;') + '</b>support / resistance, %/yr</div>';
    html += '<div><b>' + (sh ? (100 * (Math.exp(sh.gr * q + sh.cr) / Math.exp(sh.gs * q + sh.cs) - 1)).toFixed(1) + '%' : '&mdash;') + '</b>width at this bar</div>';
    html += '<div><b>' + (sh ? (100 * (cl / Math.exp(sh.gs * q + sh.cs) - 1)).toFixed(1) + '% above support' : '&mdash;') + '</b>close vs the lines</div>';
    var stt = STATE[q], open = null, k;
    for (k = 0; k < TRADES.length; k++){ if (TRADES[k].e <= q && q <= TRADES[k].x) { open = TRADES[k]; break; } }
    var stTxt = stt > 0 ? 'LONG' : stt < 0 ? 'SHORT' : 'flat';
    var pnl = open ? (open.d * (CL[q] - CL[open.e])) : 0;
    html += '<div class="' + (stt > 0 ? 'st-long' : stt < 0 ? 'st-short' : '') + '"><b>' + stTxt + '</b>trend state at min gradient</div>';
    html += '<div><b>' + (open && open.e < q ? (1e4 * pnl).toFixed(0) + ' bp' : '&mdash;') + '</b>open trade, from ' + (open ? esc(nm.dates[open.e - st0]) : '&mdash;') + '</div>';
    var done = TRADES.filter(function(tr){ return tr.x <= q; }), sum = 0;
    done.forEach(function(tr){ sum += tr.gross; });
    html += '<div><b>' + done.length + ' closed, ' + (1e4 * sum).toFixed(0) + ' bp</b>trades so far, gross</div>';
    if (r && r.purged) html += '<div><b style="color:var(--down)">break</b>the shown line was broken this bar</div>';
    document.getElementById('read').innerHTML = html;
  }

  // ---------------------------------------------------------------- controls
  function stop(){ if (timer){ clearInterval(timer); timer = null; } document.getElementById('play').classList.remove('on'); document.getElementById('play').innerHTML = '&#9654;'; }
  function playPause(){
    if (timer){ stop(); return; }
    if (t >= n - 1) t = 0;
    document.getElementById('play').classList.add('on'); document.getElementById('play').innerHTML = '&#10074;&#10074;';
    timer = setInterval(function(){ if (t >= n - 1){ stop(); return; } t++; draw(); }, parseInt(document.getElementById('speed').value, 10));
  }
  document.getElementById('play').addEventListener('click', playPause);
  document.getElementById('first').addEventListener('click', function(){ stop(); t = 0; draw(); });
  document.getElementById('back').addEventListener('click', function(){ stop(); if (t > 0) t--; draw(); });
  document.getElementById('fwd').addEventListener('click', function(){ stop(); if (t < n - 1) t++; draw(); });
  document.getElementById('pos').addEventListener('input', function(){ stop(); t = parseInt(this.value, 10); draw(); });
  document.getElementById('speed').addEventListener('change', function(){ if (timer){ stop(); playPause(); } });
  ['cands', 'trail', 'ghost'].forEach(function(id){ document.getElementById(id).addEventListener('change', draw); });
  document.getElementById('apply').addEventListener('click', function(){ stop(); applyLine(document.getElementById('settings').value); build(); });
  document.getElementById('gmin').addEventListener('change', function(){ stop(); build(); });
  document.getElementById('name').addEventListener('change', function(){ stop(); t = 0; build(); });
  document.getElementById('settings').addEventListener('keydown', function(ev){ if (ev.key === 'Enter'){ ev.preventDefault(); stop(); applyLine(this.value); build(); } });
  CTRL.forEach(function(el){
    el.addEventListener('change', function(){ stop(); build(); });
    if (el.type === 'number') el.addEventListener('keydown', function(ev){ if (ev.key === 'Enter'){ ev.preventDefault(); el.blur(); } });
  });
  document.querySelectorAll('#dials select').forEach(function(el){ var o = el.querySelector('option[selected]'); if (o) el.value = o.value; });
  document.querySelectorAll('#dials input[type=number]').forEach(function(el){ el.value = el.defaultValue; });
  document.addEventListener('keydown', function(ev){
    if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'SELECT') return;
    if (ev.key === 'ArrowRight'){ stop(); if (t < n - 1) t++; draw(); ev.preventDefault(); }
    else if (ev.key === 'ArrowLeft'){ stop(); if (t > 0) t--; draw(); ev.preventDefault(); }
    else if (ev.key === ' '){ playPause(); ev.preventDefault(); }
  });

  var sel = document.getElementById('name');
  D.names.forEach(function(x, i){ var o = document.createElement('option'); o.value = i; o.textContent = x.symbol + '  ' + x.dates[0] + ' → ' + x.dates[x.n - 1]; sel.appendChild(o); });
  sel.value = 0;
  applyLine(DEFAULT_LINE);
  document.getElementById('gmin').value = 25;
  t = 60;                                   // open mid-panel so the first frame shows the lines
  build();
  if (location.hash.indexOf('#parity') === 0){
    // PARITY HOOK: per name, shown bars inside the panel and the sums of the four line
    // parameters over them, under the default line -- compared with Python by a headless dump
    var out = [], Pp = parseLine(DEFAULT_LINE);
    D.names.forEach(function(x){
      var s0 = x.start, nn = x.n, l0 = Math.max(0, s0 - Math.min(Pp.maxlen, 500)), h1 = s0 + nn, i;
      var L2 = new Float64Array(x.m), H2 = new Float64Array(x.m), C2 = new Float64Array(x.m);
      for (i = l0; i < h1; i++){ L2[i] = Math.log(x.l[i]); H2[i] = Math.log(x.h[i]); C2[i] = Math.log(x.c[i]); }
      BUDGET.n = 0; BUDGET.hit = false;
      var R2 = Pp.grow === 'chain' ? walkChain(L2, H2, C2, l0, h1, Pp) : walkParallel(L2, H2, C2, l0, h1, Pp);
      var cnt = 0, sg = 0, sc = 0, sr = 0, scr = 0;
      for (i = s0; i < h1; i++){ var rr = R2[i]; if (rr && rr.shown){ cnt++; sg += rr.shown.gs; sc += rr.shown.cs; sr += rr.shown.gr; scr += rr.shown.cr; } }
      out.push([x.symbol, cnt, sg, sc, sr, scr, BUDGET.hit]);
    });
    var pre = document.createElement('pre'); pre.id = 'parity-out';
    pre.textContent = JSON.stringify(out);
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
