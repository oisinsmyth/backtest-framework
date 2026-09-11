"""THE DRAWING PAGE: the principal draws the trendlines by hand on the twelve names; the drawings
are the labelled set every construction will be scored against.

    uv run python scripts/d451_splice_draw_page.py           (reuses temp/d399_live_bars.json)

WHY. Every construction so far -- D399's pivots, D451's grow-right, D452's hysteresis -- was
dialled in "by eye", and the eye was never written down where an algorithm could be scored
against it. This page records it. Support and resistance segments, two clicks each, snapped to
the wick they anchor on; kept per name in the artifact's database (so this session can read
them back with the Artifact tool's read_db) and exportable as JSON text as a fallback.

WHAT IS RECORDED. Per name: a list of {kind, x1, p1, x2, p2} -- kind "support" or "resistance",
x the bar index in the name's full series, p the price at each end. A line is straight in log
price, exactly as the constructions' lines are, so a drawn line and a fitted line are the same
kind of object and can be compared on gradient (log per bar), level and extent.

THE CURSOR. All bars are visible by default: the target is the line a chartist draws knowing
the window, which is what a construction's FINAL line is scored against. The cursor ghosts the
bars after it, for drawing what one would have drawn at that time; the record notes the cursor
position a line was drawn at (`at`), so causal and hindsight drawings can be told apart later.
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
.bar label{display:inline-flex;align-items:center;gap:7px;font-family:"IBM Plex Mono",monospace;
  font-size:12.5px;color:var(--muted);white-space:nowrap}
.bar button{font:inherit;font-size:12.5px;padding:4px 12px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink);cursor:pointer}
.bar button:hover{border-color:var(--muted)}
.bar button.kind-sup.on{border-color:var(--sup);color:var(--sup);font-weight:600}
.bar button.kind-res.on{border-color:var(--res);color:var(--res);font-weight:600}
.bar input[type=range]{width:220px;accent-color:var(--sup)}
.bar input[type=checkbox]{width:15px;height:15px}
.bar .st{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted)}
.grid{display:flex;flex-direction:column;gap:14px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.ph{display:flex;align-items:baseline;gap:12px;padding:10px 16px 2px;flex-wrap:wrap}
.ph h2{font-family:"Newsreader",Georgia,serif;font-size:18px;font-weight:600;margin:0}
.ph .dt{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
.ph .cnt{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted)}
.pb{overflow-x:auto}
.pb svg{display:block;width:100%;min-width:880px;height:auto;cursor:crosshair;touch-action:none}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:20px;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
textarea{width:100%;min-height:90px;font:12px "IBM Plex Mono",monospace;padding:8px;border:1px solid var(--rule);
  border-radius:4px;background:var(--chip);color:var(--ink)}
</style>

<div class="wrap">
  <div class="eyebrow">the labelled set &middot; what the eye draws, written down</div>
  <h1>Draw the lines</h1>
  <p class="lede">Twelve names. Draw the support and resistance lines you would draw: pick a kind,
    click where the line starts, click where it ends. Each click snaps to the wick of the bar under
    it &mdash; the low for support, the high for resistance &mdash; so a line anchors where a
    chartist anchors it. Click a line to select it, then delete. <b>Everything is saved as you
    go</b> and can be read back by the research session, so these drawings become the target
    every construction is scored against on gradient, level and where it starts and ends.</p>

  <div class="bar" id="ctl">
    <label>drawing</label>
    <button id="ksup" class="kind-sup on" type="button">support (S)</button>
    <button id="kres" class="kind-res" type="button">resistance (R)</button>
    <label><input type="checkbox" id="snap" checked> snap to wick</label>
    <label><input type="checkbox" id="ext" checked> extend to the right</label>
    <button id="del" type="button" title="delete the selected line (Delete)">delete selected</button>
    <button id="undo" type="button" title="undo the last change (Ctrl+Z)">undo</button>
    <label>cursor <input type="range" id="cur" min="0" max="100" value="100" step="1" title="ghost the bars after the cursor, to draw what one would have drawn at that time"> <span id="curtxt">all bars</span></label>
    <span class="st" id="status">&hellip;</span>
  </div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support, drawn</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance, drawn</span>
    <span><i class="sw" style="border-color:var(--sel)"></i> selected</span>
    <span>keys: S / R kind &middot; Delete &middot; Ctrl+Z &middot; Esc cancels a half-drawn line</span>
  </div>

  <div class="grid" id="grid"></div>

  <div class="bar" style="position:static">
    <button id="copy" type="button">copy all as JSON</button>
    <button id="show" type="button">show JSON</button>
    <span id="copied" style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--faint)"></span>
  </div>
  <textarea id="json" spellcheck="false" hidden></textarea>

  <p class="note"><b>What a drawn line is.</b> Two anchors, each a bar and a price, straight in
    log price &mdash; the same object as a construction's line, so the two can be compared
    directly: gradient in per cent a year, level at any bar, and the bars the line covers. Draw
    the line you would trade from, not every line you could justify; a name with no clean
    trend can be left empty and that is information too.</p>
  <p class="note"><b>Hindsight is fine here.</b> The whole window is visible because the target
    is the line a chartist draws knowing the window &mdash; what a construction's <em>final</em>
    line on a window should match. To record what you would have drawn at a moment, move the
    cursor first; each line remembers the cursor position it was drawn at.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var W = 1200, HH = 260, PL = 8, PR = 62, PT = 12, PB = 22, iw = W - PL - PR, ih = HH - PT - PB;
  var kind = 'support', pending = null, sel = null, hist = [], db = null, saveTimers = {};
  var STATE = {};                 // key -> {symbol, start, n, lines: [...]}
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }
  function key(nm){ return nm.symbol + '-' + nm.start; }

  // ---------------------------------------------------------------- persistence
  function status(t){ document.getElementById('status').textContent = t; }
  function save(k){
    var st = STATE[k], body = {symbol: st.symbol, start: st.start, n: st.n, lines: st.lines, updated: new Date().toISOString()};
    try { localStorage.setItem('draw:' + k, JSON.stringify(body)); } catch (e) {}
    if (!db){ status('saved in this browser only (database unavailable) -- use copy all as JSON'); return; }
    if (saveTimers[k]) clearTimeout(saveTimers[k]);
    saveTimers[k] = setTimeout(function(){
      db.doc('lines/' + k).set(body).then(function(){ status('saved ' + k + ' at ' + body.updated.slice(11, 19)); },
        function(err){ status('save failed (' + (err && err.code) + ') -- copy all as JSON'); });
    }, 400);
  }
  function load(){
    D.names.forEach(function(nm){
      var k = key(nm), local = null;
      try { local = JSON.parse(localStorage.getItem('draw:' + k) || 'null'); } catch (e) {}
      STATE[k] = {symbol: nm.symbol, start: nm.start, n: nm.n, lines: (local && local.lines) || []};
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
          if (snap.exists){ var b = snap.data(); if (b && b.lines) STATE[k].lines = b.lines; }
          if (--pend === 0){ render(); status('loaded ' + total() + ' lines from the database'); }
        }, function(){ if (--pend === 0){ render(); status('database read failed -- showing this browser\'s copy'); } });
      });
    }, function(){ status('database unavailable -- saved in this browser only'); });
  }
  function total(){ var t = 0; Object.keys(STATE).forEach(function(k){ t += STATE[k].lines.length; }); return t; }
  function snapshot(){ var s = {}; Object.keys(STATE).forEach(function(k){ s[k] = JSON.parse(JSON.stringify(STATE[k].lines)); }); return s; }
  function push(){ hist.push(snapshot()); if (hist.length > 100) hist.shift(); }
  function undo(){
    if (!hist.length) return;
    var s = hist.pop();
    Object.keys(s).forEach(function(k){ STATE[k].lines = s[k]; save(k); });
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
  function cursorBar(nm){ return Math.round(parseInt(document.getElementById('cur').value, 10) / 100 * (nm.n - 1)); }

  // ---------------------------------------------------------------- drawing
  function render(){
    var html = '';
    D.names.forEach(function(nm, idx){
      var k = key(nm), S = scales(nm), n = nm.n, st0 = nm.start, s = '', i, kq, cur = cursorBar(nm);
      for (kq = 0; kq <= 4; kq++){
        var lv = S.a + (S.b - S.a) * kq / 4, y = S.Y(Math.exp(lv));
        s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
        s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) + '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' + Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 0) + '</text>';
      }
      var bw = iw / n, cw = Math.max(1.3, bw * 0.6);
      for (i = 0; i < n; i++){
        var q = st0 + i, o = nm.o[q], c = nm.c[q], up = c >= o, col = up ? 'var(--up)' : 'var(--down)', op = i > cur ? '.15' : '.85';
        var x = S.X(i), yo = S.Y(o), yc = S.Y(c);
        s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + S.Y(nm.h[q]).toFixed(1) + '" y2="' + S.Y(nm.l[q]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity="' + op + '"/>';
        s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) + '" fill="' + col + '" opacity="' + op + '"/>';
      }
      var ext = document.getElementById('ext').checked;
      STATE[k].lines.forEach(function(L, j){
        var x1 = S.X(L.x1 - st0), y1 = S.Y(L.p1), x2 = S.X(L.x2 - st0), y2 = S.Y(L.p2);
        var isSel = sel && sel.k === k && sel.j === j, col2 = isSel ? 'var(--sel)' : (L.kind === 'support' ? 'var(--sup)' : 'var(--res)');
        if (ext && L.x2 > L.x1){
          var g = (Math.log(L.p2) - Math.log(L.p1)) / (L.x2 - L.x1), xe = st0 + n - 1;
          var pe = Math.exp(Math.log(L.p2) + g * (xe - L.x2));
          s += '<line x1="' + x2.toFixed(1) + '" y1="' + y2.toFixed(1) + '" x2="' + S.X(xe - st0).toFixed(1) + '" y2="' + S.Y(pe).toFixed(1) + '" stroke="' + col2 + '" stroke-width="1" stroke-dasharray="3 5" opacity=".5"/>';
        }
        s += '<line class="ln" data-k="' + esc(k) + '" data-j="' + j + '" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="' + col2 + '" stroke-width="' + (isSel ? 3.2 : 2.2) + '" stroke-linecap="round" style="cursor:pointer"/>';
        s += '<line class="ln-hit" data-k="' + esc(k) + '" data-j="' + j + '" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="transparent" stroke-width="12" style="cursor:pointer"/>';
        s += '<circle cx="' + x1.toFixed(1) + '" cy="' + y1.toFixed(1) + '" r="3" fill="' + col2 + '"/><circle cx="' + x2.toFixed(1) + '" cy="' + y2.toFixed(1) + '" r="3" fill="' + col2 + '"/>';
      });
      if (pending && pending.k === k){
        s += '<circle cx="' + S.X(pending.x1 - st0).toFixed(1) + '" cy="' + S.Y(pending.p1).toFixed(1) + '" r="4.5" fill="none" stroke="var(--sel)" stroke-width="2"/>';
      }
      if (cur < n - 1) s += '<line x1="' + S.X(cur).toFixed(1) + '" x2="' + S.X(cur).toFixed(1) + '" y1="' + PT + '" y2="' + (PT + ih) + '" stroke="var(--ink)" opacity=".3"/>';
      for (i = 0; i < n; i += 45){
        s += '<text x="' + S.X(i).toFixed(1) + '" y="' + (HH - 6) + '" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' + esc(nm.dates[i]) + '</text>';
      }
      var ns = STATE[k].lines.filter(function(L){ return L.kind === 'support'; }).length, nr = STATE[k].lines.length - ns;
      html += '<div class="panel"><div class="ph"><h2>' + esc(nm.symbol) + '</h2><span class="dt">' + esc(nm.dates[0]) + ' &rarr; ' + esc(nm.dates[n - 1]) + '</span>' +
        '<span class="cnt">' + ns + ' support &middot; ' + nr + ' resistance</span></div>' +
        '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + HH + '" data-idx="' + idx + '">' + s + '</svg></div></div>';
    });
    document.getElementById('grid').innerHTML = html;
    document.getElementById('json').value = exportJSON();
  }

  function exportJSON(){
    var out = {};
    Object.keys(STATE).forEach(function(k){ out[k] = {symbol: STATE[k].symbol, start: STATE[k].start, n: STATE[k].n, lines: STATE[k].lines}; });
    return JSON.stringify(out);
  }

  // ---------------------------------------------------------------- interaction
  document.getElementById('grid').addEventListener('click', function(ev){
    var t = ev.target;
    if (t.classList && (t.classList.contains('ln') || t.classList.contains('ln-hit'))){
      sel = {k: t.getAttribute('data-k'), j: parseInt(t.getAttribute('data-j'), 10)}; pending = null; render(); return;
    }
    var svg = t.closest ? t.closest('svg') : null;
    if (!svg) return;
    var nm = D.names[parseInt(svg.getAttribute('data-idx'), 10)], k = key(nm), S = scales(nm);
    var pt = svgPoint(svg, ev), i = S.bar(pt.x), q = nm.start + i, p = S.price(pt.y);
    if (pt.y < PT || pt.y > PT + ih) return;
    if (document.getElementById('snap').checked) p = kind === 'support' ? nm.l[q] : nm.h[q];
    sel = null;
    if (!pending || pending.k !== k){ pending = {k: k, x1: q, p1: p}; render(); return; }
    if (q === pending.x1){ pending = null; render(); return; }
    push();
    var x1 = pending.x1, p1 = pending.p1, x2 = q, p2 = p;
    if (x2 < x1){ var tx = x1, tp = p1; x1 = x2; p1 = p2; x2 = tx; p2 = tp; }
    STATE[k].lines.push({kind: kind, x1: x1, p1: p1, x2: x2, p2: p2, at: nm.start + cursorBar(nm)});
    pending = null; save(k); render();
  });
  function setKind(kk){
    kind = kk;
    document.getElementById('ksup').classList.toggle('on', kk === 'support');
    document.getElementById('kres').classList.toggle('on', kk === 'resistance');
  }
  document.getElementById('ksup').addEventListener('click', function(){ setKind('support'); });
  document.getElementById('kres').addEventListener('click', function(){ setKind('resistance'); });
  function delSel(){
    if (!sel) return;
    push();
    STATE[sel.k].lines.splice(sel.j, 1); var k = sel.k; sel = null; save(k); render();
  }
  document.getElementById('del').addEventListener('click', delSel);
  document.getElementById('undo').addEventListener('click', undo);
  ['snap', 'ext'].forEach(function(id){ document.getElementById(id).addEventListener('change', render); });
  document.getElementById('cur').addEventListener('input', function(){
    var v = parseInt(this.value, 10);
    document.getElementById('curtxt').textContent = v >= 100 ? 'all bars' : v + '% of the window';
    render();
  });
  document.addEventListener('keydown', function(ev){
    if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'TEXTAREA') return;
    if (ev.key === 's' || ev.key === 'S') setKind('support');
    else if (ev.key === 'r' || ev.key === 'R') setKind('resistance');
    else if (ev.key === 'Delete' || ev.key === 'Backspace'){ delSel(); ev.preventDefault(); }
    else if (ev.key === 'Escape'){ pending = null; sel = null; render(); }
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
