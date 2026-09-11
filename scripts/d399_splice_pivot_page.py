"""The forward-only PIVOT replay: the principal marks swing highs and lows bar by bar.

    uv run python scripts/d399_splice_pivot_page.py

WHY A SECOND REPLAY. The first one asked him to draw LINES, so a disagreement between his lines
and a construction's could be a disagreement about pivots, about fitting, or about when a trend
ends -- three questions in one number. This asks only for the pivots. Whatever the detector gets
wrong here is a pivot problem; whatever survives is a fitting problem. The two stop contaminating
each other.

THE ALGORITHM'S PIVOTS ARE NOT SHOWN AND ARE NOT IN THE PAYLOAD. If the page displayed them, the
comparison would measure how closely he agreed with a suggestion, which is not the quantity
anyone wants. The k=3 detector's output is compared afterwards, in a separate script.

RECORDING, and the two defects from last time it is built to avoid:

  * THE EVENT LOG IS THE RECORD. Every action writes its OWN document immediately -- place,
    remove, step -- so nothing depends on rewriting an array. Last time a per-bar `snapshots`
    array stopped at bar 48 while he stepped to 259, and the per-bar state had to be
    reconstructed from the events afterwards. Here there is no derived array to break.
  * REMOVE IS LOGGED. Last time `undo` popped a line and wrote nothing, so three lines were
    unrecoverable and the bar at which they were dropped was lost outright.

GENERIC SANITISER, same as every other page here: `json.dumps` emits a bare `NaN` for a
non-finite float, `JSON.parse` rejects it, and the page renders BLANK with no visible error. Every
float is made finite or None and the payload is re-parsed strictly before the file is written.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_recalc_chart.json"
OUT = REPO / "temp" / "d399_pivot_page.html"

WARMUP = 30          # bars visible before the cursor starts, so the first pivot has context
VIEW = 100           # trailing bars drawn, wide enough that a bar is comfortably clickable


def clean(x, p=6):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


HTML = r"""<title>Mark the Pivots</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#fff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7; --chip:#f1eee9;
  --up:#1c6b52; --down:#a93d2c; --hi:#c2410c; --lo:#1d4ed8; --ok:#1c6b52; --warn:#8a6d1f;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
    --up:#4cae87; --down:#e0705c; --hi:#f0955a; --lo:#7aa2f7; --ok:#4cae87; --warn:#d6b45f;
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
  --up:#4cae87; --down:#e0705c; --hi:#f0955a; --lo:#7aa2f7; --ok:#4cae87; --warn:#d6b45f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;font-size:15px;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1220px;margin:0 auto;padding:28px 22px 60px;display:flex;flex-direction:column;gap:18px}
h1{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:31px;margin:0;letter-spacing:-.01em}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
.lede{max-width:66ch;color:var(--muted);margin:0}
.lede b{color:var(--ink);font-weight:600}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;
  background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:11px 14px}
button{font:inherit;font-size:14px;padding:7px 15px;border-radius:5px;cursor:pointer;
  border:1px solid var(--rule);background:var(--chip);color:var(--ink)}
button:hover{border-color:var(--muted)}
button:disabled{opacity:.4;cursor:not-allowed}
button.primary{background:var(--ink);color:var(--ground);border-color:var(--ink);font-weight:500}
.stat{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--muted);
  font-variant-numeric:tabular-nums}
.stat b{color:var(--ink);font-weight:500}
.spacer{flex:1}
#chart{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
#chart svg{display:block;width:100%;height:auto;touch-action:manipulation}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:6px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);
  max-width:70ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
#saved{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
</style>

<div class="wrap">
  <div class="eyebrow">D399 &middot; pivot ground truth &middot; GME, forward-only</div>
  <h1>Mark the pivots</h1>
  <p class="lede">Step forward one bar at a time and mark the swing highs and lows where you think
    they are. <b>Click the upper half of a bar for a swing high, the lower half for a swing low.</b>
    Click a marker again to remove it. There is no way back &mdash; what you can see is all you
    would have seen at the time.</p>
  <p class="lede">The detector's own pivots are <b>not shown and not in this page's data</b>. If
    they were, this would measure how far you agreed with a suggestion instead of what you
    actually think. The <b>trend lines are fitted to your pivots</b> and redraw as you go &mdash;
    those are derived from your own clicks, not from a detector, and the construction supplies its
    own break pivots (hollow rings) without you placing any.</p>

  <div class="bar">
    <button id="step" class="primary">Step forward &rarr;</button>
    <button id="step5">+5 bars</button>
    <span class="stat">bar <b id="cur">—</b> of <b id="tot">—</b> &nbsp;·&nbsp; <b id="dt">—</b></span>
    <span class="spacer"></span>
    <span class="stat">highs <b id="nhi">0</b> &nbsp;·&nbsp; lows <b id="nlo">0</b></span>
    <span id="saved">—</span>
  </div>

  <div class="bar">
    <label class="stat">height deadband
      <select id="dh"><option value="5">5%</option><option value="10" selected>10%</option>
        <option value="20">20%</option><option value="0">off</option></select></label>
    <label class="stat">min pivots
      <select id="mp"><option>3</option><option selected>4</option><option>5</option></select></label>
    <label class="stat"><input type="checkbox" id="showline" checked> draw the lines</label>
    <span class="spacer"></span>
    <span class="stat">on <b id="cov">0</b> bars &nbsp;·&nbsp; <b id="nseg">0</b> segments
      &nbsp;·&nbsp; <b id="nsyn">0</b> break pivots</span>
  </div>

  <div class="legend">
    <span><i class="dot" style="background:var(--hi)"></i> swing high (yours)</span>
    <span><i class="dot" style="background:var(--lo)"></i> swing low (yours)</span>
    <span><i class="sw" style="border-top:2.5px solid var(--hi);width:20px;display:inline-block"></i> resistance</span>
    <span><i class="sw" style="border-top:2.5px solid var(--lo);width:20px;display:inline-block"></i> support</span>
    <span><i class="dot" style="background:var(--faint);width:7px;height:7px"></i> the construction's own break pivot</span>
    <span>right edge = now; nothing beyond it exists yet</span>
  </div>

  <div id="chart"></div>

  <p class="note"><b>Log price.</b> Same vertical scale as every other chart in this thread, so a
    straight line is a constant growth rate. Every click and every step is written to its own
    record as it happens &mdash; there is no array to rewrite, and removals are logged too.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var n = D.n, WARM = D.warmup, VIEW = D.view;
  var cur = WARM;                       // newest visible bar
  var piv = {};                         // "bar:sign" -> {bar, sign, price}
  var seq = 0, db = null;

  var W = 1200, H = 460, PL = 8, PR = 64, PT = 16, PB = 28;
  var iw = W - PL - PR, ih = H - PT - PB;

  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  function view(){ var hi = cur, lo = Math.max(0, hi - VIEW + 1); return [lo, hi]; }

  function scales(){
    var v = view(), lo = v[0], hi = v[1], mn = Infinity, mx = -Infinity;
    for (var i = lo; i <= hi; i++){
      if (D.low[i] < mn) mn = D.low[i];
      if (D.high[i] > mx) mx = D.high[i];
    }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.08 || 0.05;
    return {lo: lo, hi: hi, a: a - pad, b: b + pad, m: hi - lo + 1};
  }
  var S = null;
  function X(i){ return PL + (i - S.lo) * (iw / S.m) + (iw / S.m) / 2; }
  function Y(p){ return PT + ih - (Math.log(p) - S.a) / (S.b - S.a) * ih; }
  function barAt(px){
    var i = Math.floor((px - PL) / (iw / S.m)) + S.lo;
    return (i < S.lo || i > S.hi) ? null : i;
  }

  // ---- THE CONSTRUCTION, fed by HIS pivots instead of the k=3 detector's.
  // A port of recalc_pair from scripts/d399_recalc_segment.py: the line is the OLS fit, gradient
  // and intercept frozen when the segment opens, thrown away when the fit's LEVEL drifts past the
  // deadband or a candle body closes through it. A break makes that bar a provisional pivot of the
  // construction's own -- he places none of those. Both sides walk together so a crossed channel
  // invalidates both. D173's lag applies to his pivots exactly as it does to the detector's: a
  // pivot he marks at bar i does not reach the fit until bar i+3.
  var K = 3, CARRY = 3, DELTA = 1e-3;

  function ols(x, y){
    var nn = x.length, i, sx = 0, sy = 0;
    if (nn < 2) return [NaN, NaN];
    for (i = 0; i < nn; i++){ sx += x[i]; sy += y[i]; }
    var mx = sx / nn, my = sy / nn, num = 0, den = 0;
    for (i = 0; i < nn; i++){ num += (x[i] - mx) * (y[i] - my); den += (x[i] - mx) * (x[i] - mx); }
    if (den <= 0) return [NaN, NaN];
    var b = num / den;
    return [b, my - b * mx];
  }

  function recalc(upto){
    var dh = parseFloat(document.getElementById('dh').value);
    var maxdh = dh > 0 ? Math.log(1 + dh / 100) : Infinity;
    var minp = parseInt(document.getElementById('mp').value, 10);
    var out = {res: new Array(n).fill(null), sup: new Array(n).fill(null)},
        syn = [], segs = {res: 0, sup: 0};
    var side = {};
    ['res', 'sup'].forEach(function(kd){
      var sg = kd === 'res' ? 1 : -1, list = [];
      Object.keys(piv).forEach(function(kk){
        if (piv[kk].sign === sg) list.push([piv[kk].bar, Math.log(piv[kk].price)]);
      });
      list.sort(function(a, b){ return a[0] - b[0]; });
      side[kd] = {list: list, p: 0, bx: [], by: [], g: NaN, c: NaN, syn: null, dormant: false};
    });
    function fitpts(d){
      var x = d.bx.slice(), y = d.by.slice();
      if (d.syn){ x.push(d.syn[0]); y.push(d.syn[1]); }
      return [x, y];
    }
    function np(d){ return d.bx.length + (d.syn ? 1 : 0); }
    function refit(d){
      var f = fitpts(d), r = ols(f[0], f[1]);
      d.g = r[0]; d.c = r[1];
    }
    for (var t = 0; t <= upto; t++){
      ['res', 'sup'].forEach(function(kd){
        var d = side[kd], fresh = false;
        while (d.p < d.list.length && d.list[d.p][0] <= t - K){
          if (d.syn && d.syn[0] === d.list[d.p][0]) d.syn = null;   // ratified, never doubled
          d.bx.push(d.list[d.p][0]); d.by.push(d.list[d.p][1]); d.p++; fresh = true;
        }
        if (fresh && d.dormant){ d.dormant = false; refit(d); }
        if (d.dormant || np(d) < 2) return;
        var f = fitpts(d), r = ols(f[0], f[1]);
        if (!isFinite(r[0])) return;
        if (!isFinite(d.g)){ refit(d); return; }
        var lvl = d.g * t + d.c, bad = null;
        if (Math.abs((r[0] * t + r[1]) - lvl) > maxdh) bad = 'h';
        else {
          var b = kd === 'sup' ? Math.log(Math.min(D.open[t], D.close[t]))
                               : Math.log(Math.max(D.open[t], D.close[t]));
          if (kd === 'sup' ? (b < lvl) : (b > lvl)) bad = 'b';
        }
        if (bad){
          d.bx = d.bx.slice(-CARRY); d.by = d.by.slice(-CARRY);
          if (bad === 'b'){
            d.syn = [t, Math.log(kd === 'sup' ? D.low[t] : D.high[t])];
            syn.push({bar: t, sign: kd === 'res' ? 1 : -1,
                      price: kd === 'sup' ? D.low[t] : D.high[t]});
            d.dormant = false; refit(d); segs[kd]++;
          } else { d.g = NaN; d.c = NaN; d.dormant = true; segs[kd]++; }
        }
      });
      var ds = side.sup, dr = side.res, ok = {};
      if (isFinite(ds.g) && isFinite(ds.c) && isFinite(dr.g) && isFinite(dr.c)
          && (dr.g * t + dr.c) - (ds.g * t + ds.c) < 0){
        [ds, dr].forEach(function(d){
          d.bx = d.bx.slice(-CARRY); d.by = d.by.slice(-CARRY);
          d.g = NaN; d.c = NaN; d.dormant = true;
        });
      }
      ['res', 'sup'].forEach(function(kd){
        var d = side[kd];
        ok[kd] = !d.dormant && isFinite(d.g) && isFinite(d.c)
                 && np(d) >= minp + (d.syn ? 1 : 0) && Math.abs(d.g) > DELTA;
        if (ok[kd]){
          var lv = d.g * t + d.c;
          var b = kd === 'sup' ? Math.log(Math.min(D.open[t], D.close[t]))
                               : Math.log(Math.max(D.open[t], D.close[t]));
          if (kd === 'sup' ? (b < lv) : (b > lv)) ok[kd] = false;
        }
      });
      if (ok.res && ok.sup){
        var l1 = side.sup.g * t + side.sup.c, l2 = side.res.g * t + side.res.c;
        if (l2 - l1 < 0){ ok.res = false; ok.sup = false; }
      }
      ['res', 'sup'].forEach(function(kd){
        if (ok[kd]) out[kd][t] = Math.exp(side[kd].g * t + side[kd].c);
      });
    }
    return {lines: out, syn: syn, segs: segs.res + segs.sup};
  }

  function poly(arr, colour){
    var s = '', run = [];
    function flush(){
      if (run.length > 1) s += '<path d="M' + run.join('L') + '" fill="none" stroke="' + colour +
        '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>';
      run = [];
    }
    for (var i = S.lo; i <= S.hi; i++){
      var v = arr[i];
      if (v === null || !isFinite(v)){ flush(); continue; }
      run.push(X(i).toFixed(1) + ',' + Y(v).toFixed(1));
    }
    flush();
    return s;
  }

  function draw(){
    S = scales();
    var bw = iw / S.m, cw = Math.max(2, bw * 0.62), s = '', i;
    for (i = 0; i <= 5; i++){
      var lv = S.a + (S.b - S.a) * i / 5, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' +
           y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) +
           '" font-family="IBM Plex Mono,monospace" font-size="10.5" fill="var(--faint)">$' +
           Math.exp(lv).toFixed(2) + '</text>';
    }
    for (i = S.lo; i <= S.hi; i++){
      var o = D.open[i], c = D.close[i], up = c >= o, col = up ? 'var(--up)' : 'var(--down)';
      var x = X(i), yo = Y(o), yc = Y(c), top = Math.min(yo, yc);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + Y(D.high[i]).toFixed(1) +
           '" y2="' + Y(D.low[i]).toFixed(1) + '" stroke="' + col + '" stroke-width="1"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + top.toFixed(1) + '" width="' +
           cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) +
           '" fill="' + col + '"/>';
    }
    var R = null;
    if (document.getElementById('showline').checked){
      R = recalc(cur);
      s += poly(R.lines.sup, 'var(--lo)') + poly(R.lines.res, 'var(--hi)');
      R.syn.forEach(function(p){
        if (p.bar < S.lo || p.bar > S.hi) return;
        s += '<circle cx="' + X(p.bar).toFixed(1) + '" cy="' + Y(p.price).toFixed(1) +
             '" r="3" fill="none" stroke="var(--faint)" stroke-width="1.4"/>';
      });
    }
    Object.keys(piv).forEach(function(kk){
      var p = piv[kk];
      if (p.bar < S.lo || p.bar > S.hi) return;
      var x = X(p.bar), y = Y(p.price), dy = p.sign > 0 ? -9 : 9;
      s += '<circle cx="' + x.toFixed(1) + '" cy="' + (y + dy).toFixed(1) + '" r="4.5" fill="' +
           (p.sign > 0 ? 'var(--hi)' : 'var(--lo)') + '"/>';
    });
    var cv = 0;
    if (R){
      for (var q = 0; q <= cur; q++){
        if (R.lines.sup[q] !== null) cv++;
        if (R.lines.res[q] !== null) cv++;
      }
    }
    document.getElementById('cov').textContent = cv;
    document.getElementById('nseg').textContent = R ? R.segs : 0;
    document.getElementById('nsyn').textContent = R ? R.syn.length : 0;
    s += '<line x1="' + (PL + iw).toFixed(1) + '" x2="' + (PL + iw).toFixed(1) + '" y1="' + PT +
         '" y2="' + (PT + ih) + '" stroke="var(--faint)" stroke-dasharray="3 3"/>';
    for (i = S.lo; i <= S.hi; i += 20){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" ' +
           'font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">' +
           esc(D.dates[i]) + '</text>';
    }
    document.getElementById('chart').innerHTML =
      '<svg id="svg" viewBox="0 0 ' + W + ' ' + H + '">' + s + '</svg>';
    document.getElementById('svg').addEventListener('click', onClick);
    document.getElementById('cur').textContent = cur;
    document.getElementById('tot').textContent = n - 1;
    document.getElementById('dt').textContent = D.dates[cur];
    var nh = 0, nl = 0;
    Object.keys(piv).forEach(function(kk){ if (piv[kk].sign > 0) nh++; else nl++; });
    document.getElementById('nhi').textContent = nh;
    document.getElementById('nlo').textContent = nl;
    document.getElementById('step').disabled = cur >= n - 1;
    document.getElementById('step5').disabled = cur >= n - 1;
  }

  function log(action, extra){
    seq += 1;
    var rec = Object.assign({action: action, at_bar: cur, seq: seq,
                             t: new Date().toISOString()}, extra || {});
    if (!db){ return; }
    var id = ('000000' + seq).slice(-6);
    db.doc('events/' + id).set(rec).then(function(){
      document.getElementById('saved').textContent = 'saved ' + seq + ' events';
    }).catch(function(){
      document.getElementById('saved').textContent = 'SAVE FAILED at event ' + seq;
    });
    db.doc('meta/state').set({cursor: cur, seq: seq, n_pivots: Object.keys(piv).length,
                              updated: new Date().toISOString()}).catch(function(){});
  }

  function onClick(ev){
    var sv = document.getElementById('svg'), r = sv.getBoundingClientRect();
    var px = (ev.clientX - r.left) * (W / r.width);
    var py = (ev.clientY - r.top) * (H / r.height);
    var i = barAt(px);
    if (i === null || i > cur) return;
    // above the bar's own midpoint = a swing HIGH, below = a swing LOW
    var mid = (Y(D.high[i]) + Y(D.low[i])) / 2;
    var sign = py < mid ? 1 : -1;
    var key = i + ':' + sign;
    if (piv[key]){
      delete piv[key];
      log('remove', {bar: i, sign: sign});
    } else {
      var price = sign > 0 ? D.high[i] : D.low[i];
      piv[key] = {bar: i, sign: sign, price: price};
      log('place', {bar: i, sign: sign, price: price});
    }
    draw();
  }

  function step(k){
    var was = cur;
    cur = Math.min(n - 1, cur + k);
    if (cur !== was){ log('step', {from: was, to: cur}); draw(); }
  }
  document.getElementById('step').onclick = function(){ step(1); };
  document.getElementById('step5').onclick = function(){ step(5); };
  ['dh', 'mp', 'showline'].forEach(function(id){
    document.getElementById(id).addEventListener('change', function(){
      // the setting is part of what he saw when he placed the next pivot, so it is logged
      log('setting', {which: id, value: String(document.getElementById(id).type === 'checkbox'
                      ? document.getElementById(id).checked
                      : document.getElementById(id).value)});
      draw();
    });
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'ArrowRight'){ e.preventDefault(); step(1); }
  });

  draw();
  if (window.claude && claude.use){
    claude.use('db').then(function(x){
      db = x;
      document.getElementById('saved').textContent = db ? 'recording' : 'NOT SAVING';
      if (db){ log('open', {n: n, warmup: WARM, view: VIEW, symbol: D.symbol,
                            start_bar: D.start_bar}); }
    }).catch(function(){
      document.getElementById('saved').textContent = 'NOT SAVING';
    });
  } else {
    document.getElementById('saved').textContent = 'NOT SAVING';
  }
})();
</script>
"""


def main() -> int:
    src = json.loads(SRC.read_text())
    d = clean({k: src[k] for k in ("symbol", "start_bar", "n", "dates",
                                   "open", "high", "low", "close")})
    d["warmup"] = WARMUP
    d["view"] = VIEW
    for kk in ("cells", "drawn", "human_placement"):
        assert kk not in d, f"{kk} leaked into the pivot payload"
    payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived clean()"
    assert "cells" not in payload and "g_per_bar" not in payload, (
        "a fitted construction leaked into the page -- it must show his bars and nothing else")
    out = HTML.replace("__DATA__", payload)

    def _bare(c):
        raise ValueError(f"bare {c} -- JSON.parse would throw and the page would render blank")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out):,} bytes)")
    print(f"  {d['symbol']} bars {d['start_bar']}-{d['start_bar'] + d['n'] - 1}, n={d['n']}, "
          f"{d['dates'][0]} -> {d['dates'][-1]}")
    print(f"  cursor starts at bar {WARMUP}, trailing view {VIEW} bars")
    print("  NO detector pivots in the payload (asserted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
