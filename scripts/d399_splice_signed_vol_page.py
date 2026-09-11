"""Draw the two fixes on GME candles, next to the principal's own lines.

    uv run python scripts/d399_signed_vol_segment.py --chart      # writes the data
    uv run python scripts/d399_splice_signed_vol_page.py          # writes the page

GENERIC SANITISER, for the reason `d399_splice_charts.py` records: `json.dumps` writes a bare
`NaN` token for a non-finite float, Python's `json.load` accepts it and `JSON.parse` REJECTS it, so
one unsanitised field renders a BLANK PAGE with no visible error. Every float is made finite or
None, and the payload is re-parsed with `parse_constant` raising before the file is written.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
       else REPO / "temp" / "d399_signed_vol_chart.json")
OUT = (Path(sys.argv[2]).resolve() if len(sys.argv) > 2
       else REPO / "temp" / "d399_signed_vol_page.html")


def clean(x, p=6):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


HTML = r"""<title>Cutting the Trend</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#ffffff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7;
  --up:#1c6b52; --down:#a93d2c; --sup:#1d4ed8; --res:#c2410c; --human:#7c3aed;
  --warn:#8a6d1f; --chip:#f1eee9;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a;
    --up:#4cae87; --down:#e0705c; --sup:#7aa2f7; --res:#f0955a; --human:#b596f6;
    --warn:#d6b45f; --chip:#1c2128;
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a;
  --up:#4cae87; --down:#e0705c; --sup:#7aa2f7; --res:#f0955a; --human:#b596f6;
  --warn:#d6b45f; --chip:#1c2128;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 72px;display:flex;flex-direction:column;gap:34px}
header{display:flex;flex-direction:column;gap:12px;border-bottom:1px solid var(--rule);padding-bottom:24px}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
h1{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:38px;line-height:1.12;
  margin:0;text-wrap:balance;letter-spacing:-.01em}
.lede{max-width:65ch;color:var(--muted);font-size:16px;margin:0}
.lede strong{color:var(--ink);font-weight:600}

table.sum{border-collapse:collapse;width:100%;font-size:14px;
  font-variant-numeric:tabular-nums}
table.sum th{text-align:right;font-weight:500;color:var(--muted);font-size:11px;
  font-family:"IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;
  padding:0 10px 8px;border-bottom:1px solid var(--rule)}
table.sum th:first-child,table.sum td:first-child{text-align:left}
table.sum td{padding:9px 10px;border-bottom:1px solid var(--rule-soft)}
table.sum td.num{text-align:right;font-family:"IBM Plex Mono",monospace}
table.sum tr.ctl td{background:var(--chip)}
.tag{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;
  padding:2px 6px;border:1px solid var(--rule);border-radius:3px;color:var(--muted);white-space:nowrap}
.worse{color:var(--down);font-weight:500}
.same{color:var(--muted)}

.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.phead{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  padding:14px 18px;border-bottom:1px solid var(--rule-soft)}
.phead h2{font-family:"Newsreader",Georgia,serif;font-size:20px;font-weight:600;margin:0;
  letter-spacing:-.005em}
.phead .cfg{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint)}
.phead .sc{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:13px;
  font-variant-numeric:tabular-nums;color:var(--muted)}
.phead .sc b{color:var(--ink);font-weight:500}
.pbody{overflow-x:auto}
.pbody svg{display:block;width:100%;min-width:900px;height:auto}
.pnote{padding:10px 18px 14px;font-size:13px;color:var(--muted);border-top:1px solid var(--rule-soft)}

.sub{font-family:"Newsreader",Georgia,serif;font-size:23px;font-weight:600;margin:0 0 8px;
  letter-spacing:-.005em}
.sublede{margin:0 0 16px;max-width:68ch;color:var(--muted);font-size:14.5px}
.sublede b,.sublede em{color:var(--ink)}
.sublede b{font-weight:600}
table.sum tr.human td{background:color-mix(in srgb,var(--human) 10%,transparent);
  border-bottom:1px solid var(--rule)}
table.sum tr.human td:first-child{font-weight:600}
table.sum td.far{color:var(--down);font-weight:500}
section{display:block}
.legend{display:flex;flex-wrap:wrap;gap:18px;align-items:center;font-size:13px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:22px;height:0;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.swb{width:9px;height:14px;display:inline-block;border-radius:1px}

.note{border-left:3px solid var(--warn);padding:2px 0 2px 16px;color:var(--muted);
  max-width:70ch;font-size:14.5px}
.note b{color:var(--ink);font-weight:600}
footer{color:var(--faint);font-size:12.5px;font-family:"IBM Plex Mono",monospace;
  border-top:1px solid var(--rule);padding-top:16px;line-height:1.7}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">D399 &middot; pivot classifier &middot; GME, the causal replay window</div>
    <h1 id="h1">Cutting the trend</h1>
    <p class="lede" id="lede1">The segmenter ends a trend when a new pivot lands more than &tau; off the line:
      <strong>|r| &gt; &tau;</strong>. Until now support and resistance were built in complete
      isolation &mdash; separate pivot series, separate buffers, separate cuts. These panels join
      them, two different ways, on the same 260 GME bars with the principal's own hand-drawn lines
      underneath. Shading marks the bars where both edges are live, which is the only place a
      <em>channel</em> exists at all.</p>
    <p class="lede" id="lede2"><strong>Sharing the cut makes it worse; sharing the yardstick makes it
      better.</strong> Measuring a pivot's distance against the channel's own width is the one
      change so far that clears the always-on floor by a real margin.</p>
  </header>

  <div id="sum"></div>

  <section>
    <h3 class="sub">Where the line actually sits</h3>
    <p class="sublede" id="placelede">The score has only ever read the <em>slope</em>. This is the level &mdash;
      how far each drawn line sits from the bar's own high (resistance) or low (support), in per
      cent of that bar's price. The principal's own 25 lines get the identical statistic over the
      bars he held them, and they are the benchmark: <b>a support line about 10% under the low is
      what he draws.</b></p>
    <div id="place"></div>
  </section>

  <div class="legend">
    <span><i class="swb" style="background:var(--up)"></i><i class="swb" style="background:var(--down)"></i> GME daily</span>
    <span><i class="sw" style="border-color:var(--sup)"></i> support, ratcheted under the bodies</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance, ratcheted over the bodies</span>
    <span><i class="sw" style="border-color:var(--faint);border-top-style:dotted"></i> the raw OLS fit it replaced</span>
    <span><i class="sw" style="border-color:var(--human);border-top-style:dashed"></i> drawn live by the principal, over the bars he held it</span>
    <span>&#9660; a cut &mdash; where the line is thrown away and re-fitted</span>
  </div>

  <div id="charts"></div>

  <p class="note"><b>Read the vertical axis as log price.</b> A straight line here is a constant
    percentage growth rate, which is what the construction actually fits &mdash; on a linear axis
    every one of these lines would be a curve. Bars left of the shaded edge were never scored: the
    principal had not drawn anything yet.</p>

  <p class="note"><b>Why the lines look stepped rather than straight.</b> The fit is re-run at
    every confirmed pivot, not only at a cut &mdash; so between cuts the line still shifts as each
    new pivot joins the buffer. A cut (&#9660;) throws the buffer away; a step is the same line
    being re-estimated. Both are the construction, not the drawing: five live pieces were re-fitted
    by hand from the raw pivots and every level matched to 1e&#8209;9.</p>

  <p class="note"><b>An OLS fit is not a trendline, so the intercept is thrown away.</b> A
    regression puts its line through the middle of its pivots and crosses candle bodies by
    construction &mdash; it did so on 12&ndash;30% of the bars it was live. The solid lines here
    keep the OLS <em>gradient</em> and replace the intercept with the only one that satisfies the
    constraint everywhere in the piece: the line is pushed away from price until every body in the
    segment is respected. Because the whole line shifts by a constant, respecting the newest bar
    can never break an older one &mdash; so this is asserted, not measured. The dotted line is the
    raw fit it replaced.</p>

  <p class="note"><b>The ratchet cannot move the score.</b> Everything scored here is the
    <em>gradient</em>, and the ratchet changes only the level. The scores in the table are
    identical before and after. What it changes is whether the line is usable &mdash; a stop has
    to sit somewhere, and it cannot sit on a line that runs through the candles.</p>

  <footer id="foot"></footer>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var n = D.n, W = 1120, H = 300, PL = 8, PR = 62, PT = 14, PB = 26;
  var iw = W - PL - PR, ih = H - PT - PB;
  var bw = iw / n, cw = Math.max(1.4, bw * 0.62);

  // one price scale for every panel, so the panels are comparable to each other
  var lo = Infinity, hi = -Infinity, i;
  for (i = 0; i < n; i++){ if (D.low[i] < lo) lo = D.low[i]; if (D.high[i] > hi) hi = D.high[i]; }
  var lmin = Math.log(lo), lmax = Math.log(hi), pad = (lmax - lmin) * 0.06;
  lmin -= pad; lmax += pad;
  function Y(p){ return PT + ih - (Math.log(p) - lmin) / (lmax - lmin) * ih; }
  function X(i){ return PL + i * bw + bw / 2; }

  function esc(s){ return String(s).replace(/[&<>]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]; }); }

  // ---- the page's own words, when the payload carries them
  if (D.page){
    if (D.page.title){ document.getElementById('h1').innerHTML = D.page.title; }
    if (D.page.lede1){ document.getElementById('lede1').innerHTML = D.page.lede1; }
    if (D.page.lede2){ document.getElementById('lede2').innerHTML = D.page.lede2; }
    if (D.page.placelede){ document.getElementById('placelede').innerHTML = D.page.placelede; }
  }

  // ---- summary table
  var rows = D.cells.map(function(c){
    var d = c.delta_vs_control;
    var cls = d === 0 ? 'same' : (d < 0 ? 'worse' : '');
    var sgn = d > 0 ? '+' : '';
    return '<tr class="' + (c.key === 'fixed' ? 'ctl' : '') + '">' +
      '<td>' + esc(c.blurb) + (c.key === 'fixed' ? ' <span class="tag">incumbent</span>' : '') + '</td>' +
      '<td class="num">' + c.SCORE.toFixed(4) + '</td>' +
      '<td class="num ' + cls + '">' + (c.key === 'fixed' ? '&mdash;' : sgn + d.toFixed(4)) + '</td>' +
      '<td class="num">' + c.n_cuts + '</td>' +
      '<td class="num">' + (c.parts.support.FP + c.parts.resistance.FP) + '</td>' +
      '<td class="num">' + (c.parts.support.FN + c.parts.resistance.FN) + '</td>' +
      '<td class="num">' + (((c.parts.support.quality||0) + (c.parts.resistance.quality||0)) / 2).toFixed(3) + '</td>' +
      '</tr>';
  }).join('');
  document.getElementById('sum').innerHTML =
    '<table class="sum"><thead><tr><th>cell</th><th>score</th><th>vs control</th>' +
    '<th>cuts</th><th>false pos</th><th>false neg</th><th>slope quality</th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table>';

  // ---- where the line sits, with the principal's own lines as the benchmark row
  function pc(v){ return (v > 0 ? '+' : '') + v.toFixed(1) + '%'; }
  function placeRows(){
    var s = '', kinds = ['support', 'resistance'];
    kinds.forEach(function(kd){
      var ref = kd === 'support' ? 'low' : 'high';
      var hm = D.human_placement[kd];
      s += '<tr class="human"><td>your ' + kd + ' lines &mdash; vs the bar\'s own ' + ref +
           '</td><td class="num">' + pc(hm.median) + '</td><td class="num">' + pc(hm.p10) +
           '</td><td class="num">' + pc(hm.p90) + '</td><td class="num">&mdash;</td></tr>';
      D.cells.forEach(function(c){
        var p = c.placement[kd];
        if (!p) return;
        // "far" = the median sits more than twice as far out as the principal's own
        var far = Math.abs(p.median) > 2 * Math.abs(hm.median);
        s += '<tr><td style="padding-left:22px;color:var(--muted)">' + esc(c.key) + '</td>' +
          '<td class="num' + (far ? ' far' : '') + '">' + pc(p.median) + '</td>' +
          '<td class="num">' + pc(p.p10) + '</td><td class="num">' + pc(p.p90) + '</td>' +
          '<td class="num">' + (c.reach_bars[kd] === null ? '&mdash;' : c.reach_bars[kd]) +
          '</td></tr>';
      });
    });
    return s;
  }
  document.getElementById('place').innerHTML =
    '<table class="sum"><thead><tr><th>line</th><th>median offset</th><th>p10</th><th>p90</th>' +
    '<th>fit reaches back</th></tr></thead><tbody>' + placeRows() + '</tbody></table>';

  // ---- one panel per cell
  function candles(){
    var s = '';
    for (var i = 0; i < n; i++){
      var o = D.open[i], c = D.close[i], h = D.high[i], l = D.low[i];
      var up = c >= o, col = up ? 'var(--up)' : 'var(--down)';
      var x = X(i), yo = Y(o), yc = Y(c);
      var top = Math.min(yo, yc), hgt = Math.max(1, Math.abs(yc - yo));
      s += '<line x1="' + x.toFixed(2) + '" x2="' + x.toFixed(2) + '" y1="' + Y(h).toFixed(2) +
           '" y2="' + Y(l).toFixed(2) + '" stroke="' + col + '" stroke-width="1" opacity=".85"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(2) + '" y="' + top.toFixed(2) + '" width="' +
           cw.toFixed(2) + '" height="' + hgt.toFixed(2) + '" fill="' + col + '" opacity=".85"/>';
    }
    return s;
  }

  function channel(c){
    // shade only where BOTH lines are live -- that shading IS the pair, and where it is absent the
    // construction is holding one edge with nothing opposite it
    var s = '', run = [];
    function flush(){
      if (run.length > 1){
        var top = run.map(function(p){ return p[0] + ',' + p[1]; }).join('L');
        var bot = run.slice().reverse().map(function(p){ return p[0] + ',' + p[2]; }).join('L');
        s += '<path d="M' + top + 'L' + bot + 'Z" fill="var(--ink)" opacity=".055"/>';
      }
      run = [];
    }
    for (var i = 0; i < n; i++){
      var a = c.anchored.resistance[i], b = c.anchored.support[i];
      if (a === null || b === null || !isFinite(a) || !isFinite(b) || a <= 0 || b <= 0){
        flush(); continue;
      }
      run.push([X(i).toFixed(2), Y(a).toFixed(2), Y(b).toFixed(2)]);
    }
    flush();
    return s;
  }

  // Each segment as ONE straight line from the first pivot it was fitted to. The stretch before
  // emission began is dashed: the fit existed there but the construction was not yet allowed to
  // call it a trend. Only the solid stretch is scored.
  function segLine(segs, col){
    var s = '';
    (segs || []).forEach(function(g){
      function at(q){ return Math.exp(g.g * (q + D.start_bar) + g.c); }
      if (g.anchored_before){
        s += '<path d="M' + X(g.s0).toFixed(2) + ',' + Y(at(g.s0)).toFixed(2) + 'L' +
             X(g.t0).toFixed(2) + ',' + Y(at(g.t0)).toFixed(2) + '" fill="none" stroke="' + col +
             '" stroke-width="1.2" stroke-dasharray="3 3" opacity=".5"/>';
        s += '<circle cx="' + X(g.s0).toFixed(2) + '" cy="' + Y(at(g.s0)).toFixed(2) +
             '" r="2.3" fill="' + col + '" opacity=".8"/>';
      }
      s += '<path d="M' + X(g.t0).toFixed(2) + ',' + Y(at(g.t0)).toFixed(2) + 'L' +
           X(g.t1).toFixed(2) + ',' + Y(at(g.t1)).toFixed(2) + '" fill="none" stroke="' + col +
           '" stroke-width="2.1" stroke-linecap="round"/>';
    });
    return s;
  }

  function polyline(arr, colour, w, dash){
    // break the path wherever the construction goes silent -- a gap IS the answer "no trend"
    var s = '', run = [];
    var extra = dash ? ' stroke-dasharray="2 3" opacity=".5"' : '';
    function flush(){
      if (run.length > 1) s += '<path d="M' + run.join('L') + '" fill="none" stroke="' + colour +
        '" stroke-width="' + (w || 2.1) + '" stroke-linecap="round" stroke-linejoin="round"' +
        extra + '/>';
      else if (run.length === 1 && !dash) s += '<circle cx="' + run[0].split(',')[0] + '" cy="' +
        run[0].split(',')[1] + '" r="1.6" fill="' + colour + '"/>';
      run = [];
    }
    for (var i = 0; i < n; i++){
      var v = arr[i];
      if (v === null || !isFinite(v) || v <= 0){ flush(); continue; }
      run.push(X(i).toFixed(2) + ',' + Y(v).toFixed(2));
    }
    flush();
    return s;
  }

  function humanLines(){
    var s = '';
    for (var j = 0; j < D.drawn.length; j++){
      var L = D.drawn[j];
      var a = L.drawn_at, b = L.ended_at;          // only the stretch he HELD it
      if (b < a) b = a;
      var lp0 = Math.log(L.p0) + L.g_per_bar * (a - L.i0);
      var lp1 = Math.log(L.p0) + L.g_per_bar * (b - L.i0);
      s += '<line x1="' + X(a).toFixed(2) + '" y1="' + Y(Math.exp(lp0)).toFixed(2) +
           '" x2="' + X(b).toFixed(2) + '" y2="' + Y(Math.exp(lp1)).toFixed(2) +
           '" stroke="var(--human)" stroke-width="1.7" stroke-dasharray="4 3" opacity=".78"/>';
    }
    return s;
  }

  function cuts(list, colour, y){
    return list.map(function(i){
      var x = X(i);
      return '<path d="M' + (x - 3.4).toFixed(2) + ' ' + y + 'L' + (x + 3.4).toFixed(2) + ' ' + y +
             'L' + x.toFixed(2) + ' ' + (y + 5.4) + 'Z" fill="' + colour + '" opacity=".9"/>';
    }).join('');
  }

  function axis(){
    var s = '', ticks = 5, k;
    for (k = 0; k <= ticks; k++){
      var lv = lmin + (lmax - lmin) * k / ticks, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(2) + '" y2="' +
           y.toFixed(2) + '" stroke="var(--rule-soft)" stroke-width="1"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.6).toFixed(2) +
           '" font-family="IBM Plex Mono, monospace" font-size="10.5" fill="var(--faint)">$' +
           Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 1) + '</text>';
    }
    // the unscored head of the window
    s += '<rect x="' + PL + '" y="' + PT + '" width="' + (X(D.first_seen) - PL).toFixed(2) +
         '" height="' + ih + '" fill="var(--ink)" opacity=".045"/>';
    // date ticks
    for (k = 0; k < n; k += 40){
      s += '<text x="' + X(k).toFixed(2) + '" y="' + (H - 8) +
           '" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="10" ' +
           'fill="var(--faint)">' + esc(D.dates[k]) + '</text>';
    }
    return s;
  }

  var html = D.cells.map(function(c){
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' +
      esc(c.blurb) + '">' + axis() + channel(c) + humanLines() + candles() +
      (c.segments
        ? segLine(c.segments.support, 'var(--sup)') + segLine(c.segments.resistance, 'var(--res)')
        : polyline(c.anchored.support, 'var(--sup)', 2.1, false) +
          polyline(c.anchored.resistance, 'var(--res)', 2.1, false)) +
      cuts(c.cuts_support, 'var(--sup)', PT + ih + 4) +
      cuts(c.cuts_resistance, 'var(--res)', PT + ih + 12) + '</svg>';
    var d = c.delta_vs_control;
    return '<div class="panel"><div class="phead"><h2>' + esc(c.blurb) + '</h2>' +
      '<span class="cfg">' + esc(c.label) + '</span>' +
      '<span class="sc">score <b>' + c.SCORE.toFixed(4) + '</b>' +
      (c.key === 'fixed' ? '' : ' &nbsp;(' + (d > 0 ? '+' : '') + d.toFixed(4) + ')') +
      ' &nbsp;&middot;&nbsp; ' + c.n_cuts + ' cuts</span></div>' +
      '<div class="pbody">' + svg + '</div>' +
      '<div class="pnote">' + esc(c.note) + '</div></div>';
  }).join('');
  document.getElementById('charts').innerHTML = html;
  document.getElementById('charts').style.display = 'flex';
  document.getElementById('charts').style.flexDirection = 'column';
  document.getElementById('charts').style.gap = '26px';

  document.getElementById('foot').innerHTML =
    esc(D.symbol) + ' bars ' + D.start_bar + '&ndash;' + (D.start_bar + D.n - 1) +
    ' &middot; scored on bars ' + D.first_seen + '&ndash;' + D.seen_through +
    ' &middot; ground truth: data/d399_live_ground_truth.json, ' + D.drawn.length +
    ' lines drawn forward-only<br>carry=3, min_piv=5, delta gate on &mdash; held at the incumbent, ' +
    'so only the cut test varies &middot; scores from scripts/d399_signed_vol_segment.py';
})();
</script>
"""


def main() -> int:
    d = clean(json.loads(SRC.read_text()))
    notes = {
        "alwayson": ("THE FLOOR, not a candidate: the incumbent's own fit with the gate removed, "
                     "so it claims a trend on all 221 bars and never once says N/A. It scores "
                     "0.3122. Every number on this page has to be read against that -- the "
                     "incumbent beats it by 0.005."),
        "fixed": ("Two lines fitted and cut in complete isolation; nothing connects a support "
                  "line to the resistance above it. 13 cuts, and 0.005 clear of the always-on "
                  "floor."),
        "chan_shared": ("The sides now share ONE piece: a break on either edge ends both. This is "
                        "the direct reading of 'combine them', and it does not work -- 0.3237 "
                        "against 0.3657 for keeping the cuts separate. Ending a good line because "
                        "the other edge broke costs more than the pairing is worth."),
        "chan_solo": ("The sides share the YARDSTICK but not the cut: a pivot has to be more than "
                      "20% of the current channel's own width off its line. That number does not "
                      "exist until the two edges are joined. 0.3657 -- and resistance precision "
                      "0.772 against a 0.507 base rate, on 18 false positives. Its support line "
                      "sits 9.4% under the low, where the principal's sits 9.3% under."),
        "trail100": ("For reference, the best of the adaptive scales estimated from the pivot "
                     "residuals themselves: pooled over 100 pivots it converges back to the "
                     "constant it was meant to improve on."),
    }
    for c in d["cells"]:
        c["note"] = c.get("note") or notes.get(c["key"], "")
    payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived clean()"

    assert "__DATA__" in HTML, "marker missing"
    out = HTML.replace("__DATA__", payload)

    def _bare(c):
        raise ValueError(f"bare {c} in the payload -- JSON.parse would throw and the page "
                         f"would render NOTHING")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  ({len(out):,} bytes, {len(d['cells'])} panels, "
          f"{d['n']} bars, {len(d['drawn'])} drawn lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
