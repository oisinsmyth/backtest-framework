"""THE DRAWING PAGE, STEP BY STEP: the principal draws the trendlines by hand, one bar at a time,
on the twelve names; the drawings are the labelled set every causal construction is scored against.

    uv run python scripts/d451_splice_draw_page.py           (reuses temp/d399_live_bars.json)

WHY. Every construction so far -- D399's pivots, D451's grow-right, D452's hysteresis -- was
dialled in "by eye", and the eye was never written down where an algorithm could be scored
against it. The first version of this page showed the whole window, which the principal rightly
called pointless for a causal construction: a line drawn knowing the future is not the line the
trader had. So the future is hidden. Each name has its own cursor; the principal steps forward,
draws a line when one is there to draw, and ends it when it breaks.

WHAT IS RECORDED. Per name an EVENT LOG of lines: {kind, x1, p1, x2, p2, at, until} -- kind
"support" or "resistance", x the bar index in the name's full series, p the price at each
anchor (straight in log price, the constructions' own kind of line), `at` the bar the line was
drawn at (both anchors are at or before it) and `until` the bar it was ended at (absent while it
lives). The set of lines the principal had at any bar t is exactly {at <= t < until}, so the
record is a per-step labelling without storing every step. Kept in the artifact's database (this
session reads it back with read_db) and exportable as JSON text as a fallback.

HOW A CONSTRUCTION IS SCORED AGAINST IT, later: at each bar of each name, the construction's
shown lines against the principal's live lines -- present or absent, gradient, level at the
bar, and how many bars earlier or later each one appeared and ended.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "d399_live_bars.json"
OUT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "temp" / "d451_draw_page.html")

HTML = r"""<title>Draw the Lines</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#fff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7; --chip:#f1eee9;
  --up:#1c6b52; --down:#a93d2c; --res:#c2410c; --sup:#1d4ed8; --warn:#8a6d1f; --sel:#b45309;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
    --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f; --sel:#fbbf24;
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
  --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --warn:#d6b45f; --sel:#fbbf24;
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
.bar{position:sticky;top:0;z-index:5;background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:12px 16px;
  display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}
.bar label,.ph label{display:inline-flex;align-items:center;gap:7px;font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;color:var(--muted);white-space:nowrap}
button{font:inherit;font-size:12.5px;padding:4px 12px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink);cursor:pointer}
button:hover{border-color:var(--muted)}
button.kind-sup.on{border-color:var(--sup);color:var(--sup);font-weight:600}
button.kind-res.on{border-color:var(--res);color:var(--res);font-weight:600}
.bar input[type=checkbox]{width:15px;height:15px}
.bar .st{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted)}
.grid{display:flex;flex-direction:column;gap:14px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.panel.active{border-color:var(--sup)}
.ph{display:flex;align-items:center;gap:12px;padding:10px 16px 4px;flex-wrap:wrap}
.ph h2{font-family:"Newsreader",Georgia,serif;font-size:18px;font-weight:600;margin:0}
.ph .dt{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
.ph .step{display:inline-flex;gap:6px;align-items:center;margin-left:auto}
.ph .step button{min-width:2.3em;padding:3px 8px}
.ph input[type=range]{width:220px;accent-color:var(--sup)}
.ph .where{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink);min-width:15em;text-align:right;font-variant-numeric:tabular-nums}
.ph .cnt{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted)}
.pb{overflow-x:auto}
.pb svg{display:block;width:100%;min-width:880px;height:auto;cursor:crosshair;touch-action:none}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:20px;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.sw.dot{border-top-style:dotted;border-top-width:2px}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
textarea{width:100%;min-height:90px;font:12px "IBM Plex Mono",monospace;padding:8px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink)}
</style>

<div class="wrap">
  <div class="eyebrow">the labelled set &middot; what the eye draws at each bar, written down</div>
  <h1>Draw the lines</h1>
  <p class="lede">Twelve names, <b>the future hidden</b>. Each name has its own cursor: step
    forward a bar at a time; when a line is there to draw, pick a kind and click its two anchors
    (click the first and then the second, or press on the first and drag to the second; each
    anchor snaps to that bar's wick, the low for support, the high for resistance, and a plain
    press always places an anchor even on top of a line, so an old pivot can be re-used); when a
    line breaks, <b>Shift+click</b> it and <b>end it here</b>. Every line remembers the bar it was drawn at and
    the bar it was ended at, so the set of lines you had at any bar can be replayed exactly. That
    is what each construction will be scored against, bar by bar.</p>

  <div class="bar" id="ctl">
    <label>drawing</label>
    <button id="ksup" class="kind-sup on" type="button">support (S)</button>
    <button id="kres" class="kind-res" type="button">resistance (R)</button>
    <label><input type="checkbox" id="snap" checked> snap to wick</label>
    <label><input type="checkbox" id="ext" checked> project to the right</label>
    <label><input type="checkbox" id="ghost"> show ended lines faintly</label>
    <button id="del" type="button" title="end the selected line at this bar (Delete)">end selected line here</button>
    <button id="undo" type="button" title="undo the last change (Ctrl+Z)">undo</button>
    <span class="st" id="status">&hellip;</span>
  </div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support, live</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance, live</span>
    <span><i class="sw dot" style="border-color:var(--muted)"></i> projection beyond the last anchor</span>
    <span><i class="sw" style="border-color:var(--sel)"></i> selected</span>
    <span><b>Shift+click</b> selects a line &middot; keys on the active panel: &larr; &rarr; step &middot; S / R kind &middot; Delete ends &middot; Ctrl+Z &middot; Esc cancels</span>
  </div>

  <div class="grid" id="grid"></div>

  <div class="bar" style="position:static">
    <button id="copy" type="button">copy all as JSON</button>
    <button id="show" type="button">show JSON</button>
    <span id="copied" style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>
  <textarea id="json" spellcheck="false" hidden></textarea>

  <p class="note"><b>What is recorded.</b> A line is two anchors, each a bar and a price,
    straight in log price &mdash; the same object as a construction's line &mdash; plus the bar it
    was drawn at and the bar it was ended at. Both anchors must be at or before the cursor: a
    click on a hidden bar does nothing. Ending a line does not erase it; it closes it at this
    bar, so the record says both "a line was here" and "it stopped being here". If a line needs a
    new gradient, end it and draw the new one: that records the update as an update. Undo is
    the only thing that erases.</p>
  <p class="note"><b>Draw the line you would trade from</b>, not every line you could justify;
    a name with no clean trend at a bar can be left with nothing drawn, and that is information
    too. Everything is saved as you go and can be read back by the research session.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var W = 1200, HH = 260, PL = 8, PR = 62, PT = 12, PB = 22, iw = W - PL - PR, ih = HH - PT - PB;
  var kind = 'support', pending = null, sel = null, hist = [], db = null, saveTimers = {}, active = 0;
  var STATE = {};                 // key -> {symbol, start, n, cursor, lines: [{kind,x1,p1,x2,p2,at,until?}]}
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }
  function key(nm){ return nm.symbol + '-' + nm.start; }
  function alive(L, q){ return L.at <= q && (L.until == null || L.until > q); }

  // ---------------------------------------------------------------- persistence
  function status(t){ document.getElementById('status').textContent = t; }
  function body(k){ var st = STATE[k]; return {symbol: st.symbol, start: st.start, n: st.n, cursor: st.cursor, lines: st.lines, updated: new Date().toISOString()}; }
  function save(k){
    var b = body(k);
    try { localStorage.setItem('draw2:' + k, JSON.stringify(b)); } catch (e) {}
    if (!db){ status('saved in this browser only (database unavailable) -- use copy all as JSON'); return; }
    if (saveTimers[k]) clearTimeout(saveTimers[k]);
    saveTimers[k] = setTimeout(function(){
      db.doc('lines/' + k).set(b).then(function(){ status('saved ' + k + ' at ' + b.updated.slice(11, 19)); },
        function(err){ status('save failed (' + (err && err.code) + ') -- copy all as JSON'); });
    }, 400);
  }
  function load(){
    D.names.forEach(function(nm){
      var k = key(nm), local = null;
      try { local = JSON.parse(localStorage.getItem('draw2:' + k) || 'null'); } catch (e) {}
      // a fresh name opens 30 bars in: nothing can be drawn on one bar, and a chartist looks first
      STATE[k] = {symbol: nm.symbol, start: nm.start, n: nm.n, cursor: (local && local.cursor != null) ? local.cursor : 30, lines: (local && local.lines) || []};
    });
    render();
    if (!window.claude || !window.claude.use){ status('database unavailable in this view -- saved in this browser only'); return; }
    window.claude.use('db').then(function(ns){
      db = ns;
      if (!db){ status('database unavailable in this view -- saved in this browser only'); return; }
      var pend = D.names.length;
      D.names.forEach(function(nm){
        var k = key(nm);
        db.doc('lines/' + k).get().then(function(snap){
          if (snap.exists){ var b = snap.data(); if (b && b.lines){ STATE[k].lines = b.lines; STATE[k].cursor = (b.cursor != null) ? b.cursor : 30; } }
          if (--pend === 0){ render(); status('loaded ' + total() + ' lines from the database'); }
        }, function(){ if (--pend === 0){ render(); status('database read failed -- showing this browser\'s copy'); } });
      });
    }, function(){ status('database unavailable -- saved in this browser only'); });
  }
  function total(){ var t = 0; Object.keys(STATE).forEach(function(k){ t += STATE[k].lines.length; }); return t; }
  function snapshot(){ var s = {}; Object.keys(STATE).forEach(function(k){ s[k] = JSON.parse(JSON.stringify(STATE[k].lines)); }); return s; }
  function push(){ hist.push(snapshot()); if (hist.length > 200) hist.shift(); }
  function undo(){
    if (!hist.length) return;
    var s = hist.pop();
    Object.keys(s).forEach(function(k){ if (JSON.stringify(STATE[k].lines) !== JSON.stringify(s[k])){ STATE[k].lines = s[k]; save(k); } });
    sel = null; pending = null; render();
  }

  // ---------------------------------------------------------------- geometry
  function scales(nm){
    var st0 = nm.start, n = nm.n, i, mn = Infinity, mx = -Infinity;
    for (i = 0; i < n; i++){ if (nm.l[st0 + i] < mn) mn = nm.l[st0 + i]; if (nm.h[st0 + i] > mx) mx = nm.h[st0 + i]; }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.08 || 0.05; a -= pad; b += pad;
    return {a: a, b: b, n: n, st0: st0,
      X: function(q){ return PL + q * (iw / n) + (iw / n) / 2; },
      Y: function(p){ return PT + ih - (Math.log(p) - a) / (b - a) * ih; },
      bar: function(x){ return Math.max(0, Math.min(n - 1, Math.floor((x - PL) / (iw / n)))); },
      price: function(y){ return Math.exp(a + (PT + ih - y) / ih * (b - a)); }};
  }
  function svgPoint(svg, ev){
    var r = svg.getBoundingClientRect();
    return {x: (ev.clientX - r.left) * W / r.width, y: (ev.clientY - r.top) * HH / r.height};
  }

  // ---------------------------------------------------------------- drawing
  function panelSVG(nm, idx){
    var k = key(nm), st = STATE[k], S = scales(nm), n = nm.n, st0 = nm.start, c = st.cursor, q = st0 + c, s = '', i, kq;
    for (kq = 0; kq <= 4; kq++){
      var lv = S.a + (S.b - S.a) * kq / 4, y = S.Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) + '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' + Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 0) + '</text>';
    }
    var bw = iw / n, cw = Math.max(1.3, bw * 0.6);
    for (i = 0; i <= c; i++){
      var qq = st0 + i, o = nm.o[qq], cl = nm.c[qq], up = cl >= o, col = up ? 'var(--up)' : 'var(--down)';
      var x = S.X(i), yo = S.Y(o), yc = S.Y(cl);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + S.Y(nm.h[qq]).toFixed(1) + '" y2="' + S.Y(nm.l[qq]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity=".85"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) + '" fill="' + col + '" opacity=".85"/>';
    }
    var ext = document.getElementById('ext').checked, ghost = document.getElementById('ghost').checked;
    st.lines.forEach(function(L, j){
      var isAlive = alive(L, q);
      if (!isAlive && !(ghost && L.at <= q)) return;
      var x1 = S.X(L.x1 - st0), y1 = S.Y(L.p1), x2 = S.X(L.x2 - st0), y2 = S.Y(L.p2);
      var isSel = sel && sel.k === k && sel.j === j;
      var col2 = isSel ? 'var(--sel)' : (L.kind === 'support' ? 'var(--sup)' : 'var(--res)');
      var op = isAlive ? '1' : '.25';
      if (ext && L.x2 > L.x1 && isAlive){
        var g = (Math.log(L.p2) - Math.log(L.p1)) / (L.x2 - L.x1), xe = st0 + n - 1;
        var pe = Math.exp(Math.log(L.p2) + g * (xe - L.x2));
        s += '<line x1="' + x2.toFixed(1) + '" y1="' + y2.toFixed(1) + '" x2="' + S.X(xe - st0).toFixed(1) + '" y2="' + S.Y(pe).toFixed(1) + '" stroke="' + col2 + '" stroke-width="1.2" stroke-dasharray="2 5" opacity=".55"/>';
      }
      s += '<line class="ln" data-k="' + esc(k) + '" data-j="' + j + '" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="' + col2 + '" stroke-width="' + (isSel ? 3.2 : 2.2) + '" opacity="' + op + '" stroke-linecap="round"' + (isAlive ? '' : ' pointer-events="none"') + '/>';
      if (isAlive) s += '<line class="ln-hit" data-k="' + esc(k) + '" data-j="' + j + '" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="transparent" stroke-width="12"/>';
      s += '<circle cx="' + x1.toFixed(1) + '" cy="' + y1.toFixed(1) + '" r="3" fill="' + col2 + '" opacity="' + op + '" pointer-events="none"/><circle cx="' + x2.toFixed(1) + '" cy="' + y2.toFixed(1) + '" r="3" fill="' + col2 + '" opacity="' + op + '" pointer-events="none"/>';
    });
    var first = (down && down.k === k) ? down : (pending && pending.k === k) ? pending : null;
    if (first){
      s += '<circle cx="' + S.X(first.q - st0).toFixed(1) + '" cy="' + S.Y(first.p).toFixed(1) + '" r="4.5" fill="none" stroke="var(--sel)" stroke-width="2"/>';
      if (rubber && down && down.k === k){
        s += '<line x1="' + S.X(first.q - st0).toFixed(1) + '" y1="' + S.Y(first.p).toFixed(1) + '" x2="' + S.X(rubber.q - st0).toFixed(1) + '" y2="' + S.Y(rubber.p).toFixed(1) + '" stroke="var(--sel)" stroke-width="2" stroke-dasharray="4 4" opacity=".8"/>';
      }
    }
    s += '<line x1="' + S.X(c).toFixed(1) + '" x2="' + S.X(c).toFixed(1) + '" y1="' + PT + '" y2="' + (PT + ih) + '" stroke="var(--ink)" opacity=".35"/>';
    for (i = 0; i < n; i += 45){
      s += '<text x="' + S.X(i).toFixed(1) + '" y="' + (HH - 6) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
    }
    return s;
  }
  function render(){
    var html = '';
    D.names.forEach(function(nm, idx){
      var k = key(nm), st = STATE[k], q = nm.start + st.cursor;
      var na = st.lines.filter(function(L){ return alive(L, q); }).length;
      html += '<div class="panel' + (idx === active ? ' active' : '') + '" data-idx="' + idx + '"><div class="ph"><h2>' + esc(nm.symbol) + '</h2>' +
        '<span class="dt">' + esc(nm.dates[0]) + ' &rarr; ' + esc(nm.dates[nm.n - 1]) + '</span>' +
        '<span class="cnt">' + na + ' live &middot; ' + st.lines.length + ' recorded</span>' +
        '<span class="step"><button type="button" data-act="first" data-idx="' + idx + '" title="first bar">&#9198;</button>' +
        '<button type="button" data-act="back" data-idx="' + idx + '" title="one bar back">&#9664;</button>' +
        '<button type="button" data-act="fwd" data-idx="' + idx + '" title="one bar forward">&#9654;</button>' +
        '<button type="button" data-act="fwd5" data-idx="' + idx + '" title="five bars forward">&#9654;&#9654;</button>' +
        '<input type="range" data-idx="' + idx + '" min="0" max="' + (nm.n - 1) + '" value="' + st.cursor + '" step="1">' +
        '<span class="where">' + esc(nm.dates[st.cursor]) + '  bar ' + (st.cursor + 1) + ' / ' + nm.n + '</span></span></div>' +
        '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + HH + '" data-idx="' + idx + '">' + panelSVG(nm, idx) + '</svg></div></div>';
    });
    document.getElementById('grid').innerHTML = html;
    document.getElementById('json').value = exportJSON();
  }
  function redrawPanel(idx){
    var nm = D.names[idx], k = key(nm), st = STATE[k], q = nm.start + st.cursor;
    var panel = document.querySelector('.panel[data-idx="' + idx + '"]');
    if (!panel){ render(); return; }
    panel.querySelector('svg').innerHTML = panelSVG(nm, idx);
    panel.querySelector('input[type=range]').value = st.cursor;
    panel.querySelector('.where').textContent = nm.dates[st.cursor] + '  bar ' + (st.cursor + 1) + ' / ' + nm.n;
    var na = st.lines.filter(function(L){ return alive(L, q); }).length;
    panel.querySelector('.cnt').innerHTML = na + ' live &middot; ' + st.lines.length + ' recorded';
    document.querySelectorAll('.panel').forEach(function(p){ p.classList.toggle('active', parseInt(p.getAttribute('data-idx'), 10) === active); });
  }
  function exportJSON(){
    var out = {};
    Object.keys(STATE).forEach(function(k){ out[k] = {symbol: STATE[k].symbol, start: STATE[k].start, n: STATE[k].n, cursor: STATE[k].cursor, lines: STATE[k].lines}; });
    return JSON.stringify(out);
  }
  function setCursor(idx, c){
    var nm = D.names[idx], k = key(nm);
    STATE[k].cursor = Math.max(0, Math.min(nm.n - 1, c));
    // a first anchor survives stepping: press it, step until the second pivot shows, click it
    if (sel && sel.k === k) sel = null;
    active = idx; save(k); redrawPanel(idx);
  }

  // ---------------------------------------------------------------- interaction
  var grid = document.getElementById('grid'), down = null, rubber = null;
  grid.addEventListener('click', function(ev){
    var t = ev.target, b = t.closest ? t.closest('button[data-act]') : null;
    if (!b) return;
    var i2 = parseInt(b.getAttribute('data-idx'), 10), st2 = STATE[key(D.names[i2])], act = b.getAttribute('data-act');
    setCursor(i2, act === 'first' ? 0 : act === 'back' ? st2.cursor - 1 : act === 'fwd' ? st2.cursor + 1 : st2.cursor + 5);
  });
  // ANCHORS BY POINTER, NOT BY CLICK. A click only fires when the pointer goes down and up on
  // the same element; a drag from one candle to another, or a slight move on a one-pixel wick,
  // fires nothing -- which is why two anchors could not be placed. Pointer events carry both
  // ways of drawing: press on the first anchor and release on the second (a drag, with a
  // rubber band), or press-and-release on the first and again on the second (two clicks).
  function anchorAt(svg, ev){
    var idx = parseInt(svg.getAttribute('data-idx'), 10), nm = D.names[idx], k = key(nm), S = scales(nm), st = STATE[k];
    var pt = svgPoint(svg, ev), i = S.bar(pt.x), q = nm.start + i, p = S.price(pt.y);
    if (pt.y < PT || pt.y > PT + ih) return null;
    if (document.getElementById('snap').checked) p = kind === 'support' ? nm.l[q] : nm.h[q];
    return {idx: idx, k: k, i: i, q: q, p: p, future: i > st.cursor, st: st, nm: nm};
  }
  function finish(a1, a2){
    var st = a1.st, nm = a1.nm;
    push();
    var x1 = a1.q, p1 = a1.p, x2 = a2.q, p2 = a2.p;
    if (x2 < x1){ var tx = x1, tp = p1; x1 = x2; p1 = p2; x2 = tx; p2 = tp; }
    st.lines.push({kind: kind, x1: x1, p1: p1, x2: x2, p2: p2, at: nm.start + st.cursor});
    pending = null; save(a1.k); redrawPanel(a1.idx);
  }
  grid.addEventListener('pointerdown', function(ev){
    var t = ev.target;
    if (ev.button !== 0 || (t.closest && t.closest('button, input'))) return;
    // SELECTING TAKES SHIFT. A plain press always places an anchor, even on top of a line --
    // the line anchored on an old pivot used to eat the press meant to re-use it.
    if (ev.shiftKey && t.classList && (t.classList.contains('ln') || t.classList.contains('ln-hit'))){
      active = parseInt(t.closest('svg').getAttribute('data-idx'), 10);
      sel = {k: t.getAttribute('data-k'), j: parseInt(t.getAttribute('data-j'), 10)}; pending = null; redrawPanel(active);
      ev.preventDefault(); return;
    }
    var svg = t.closest ? t.closest('svg') : null;
    if (!svg) return;
    var a = anchorAt(svg, ev);
    if (!a) return;
    ev.preventDefault();
    active = a.idx; sel = null;
    if (a.future){ status('that bar is in the future -- step forward first'); redrawPanel(a.idx); return; }
    if (pending && pending.k === a.k && a.q !== pending.q){ finish(pending, a); return; }   // second click
    down = a; rubber = null;
    try { svg.setPointerCapture(ev.pointerId); } catch (e) {}
    redrawPanel(a.idx);
  });
  grid.addEventListener('pointermove', function(ev){
    if (!down) return;
    var svg = ev.target.closest ? ev.target.closest('svg') : null;
    if (!svg) svg = document.querySelector('svg[data-idx="' + down.idx + '"]');
    var a = anchorAt(svg, ev);
    if (!a || a.future) return;
    if (a.q === down.q){ if (rubber){ rubber = null; redrawPanel(down.idx); } return; }
    rubber = a; redrawPanel(down.idx);
  });
  grid.addEventListener('pointerup', function(ev){
    if (!down) return;
    var svg = document.querySelector('svg[data-idx="' + down.idx + '"]');
    try { svg.releasePointerCapture(ev.pointerId); } catch (e) {}
    var a = anchorAt(svg, ev), d = down; down = null; rubber = null;
    if (a && !a.future && a.q !== d.q){ finish(d, a); return; }          // a drag: done
    pending = (pending && pending.k === d.k && pending.q === d.q) ? null : d;   // a click: first anchor (again cancels)
    redrawPanel(d.idx);
  });
  grid.addEventListener('pointercancel', function(){ down = null; rubber = null; });
  grid.addEventListener('input', function(ev){
    var t = ev.target;
    if (t.type === 'range') setCursor(parseInt(t.getAttribute('data-idx'), 10), parseInt(t.value, 10));
  });
  function setKind(kk){
    kind = kk;
    document.getElementById('ksup').classList.toggle('on', kk === 'support');
    document.getElementById('kres').classList.toggle('on', kk === 'resistance');
  }
  document.getElementById('ksup').addEventListener('click', function(){ setKind('support'); });
  document.getElementById('kres').addEventListener('click', function(){ setKind('resistance'); });
  function endSel(){
    if (!sel) return;
    var st = STATE[sel.k], L = st.lines[sel.j], q = st.start + st.cursor;
    push();
    if (L.at >= q) st.lines.splice(sel.j, 1);      // drawn and ended at the same bar: never existed
    else L.until = q;
    var k = sel.k; sel = null; save(k);
    var idx = D.names.findIndex(function(nm){ return key(nm) === k; });
    redrawPanel(idx);
  }
  document.getElementById('del').addEventListener('click', endSel);
  document.getElementById('undo').addEventListener('click', undo);
  ['snap', 'ext', 'ghost'].forEach(function(id){ document.getElementById(id).addEventListener('change', render); });
  document.addEventListener('keydown', function(ev){
    if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'TEXTAREA') return;
    var st = STATE[key(D.names[active])];
    if (ev.key === 'ArrowRight'){ setCursor(active, st.cursor + (ev.shiftKey ? 5 : 1)); ev.preventDefault(); }
    else if (ev.key === 'ArrowLeft'){ setCursor(active, st.cursor - (ev.shiftKey ? 5 : 1)); ev.preventDefault(); }
    else if (ev.key === 's' || ev.key === 'S') setKind('support');
    else if (ev.key === 'r' || ev.key === 'R') setKind('resistance');
    else if (ev.key === 'Delete' || ev.key === 'Backspace'){ endSel(); ev.preventDefault(); }
    else if (ev.key === 'Escape'){ pending = null; down = null; rubber = null; sel = null; redrawPanel(active); }
    else if ((ev.ctrlKey || ev.metaKey) && (ev.key === 'z' || ev.key === 'Z')){ undo(); ev.preventDefault(); }
  });
  document.getElementById('copy').addEventListener('click', function(){
    var s = exportJSON(), note = document.getElementById('copied');
    var done = function(ok){ note.textContent = ok ? 'copied ' + total() + ' lines' : 'use show JSON and copy it'; setTimeout(function(){ note.textContent = ''; }, 3000); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(s).then(function(){ done(true); }, function(){ done(false); });
    else done(false);
  });
  document.getElementById('show').addEventListener('click', function(){
    var ta = document.getElementById('json'); ta.hidden = !ta.hidden; if (!ta.hidden){ ta.value = exportJSON(); ta.select(); }
  });
  load();
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
