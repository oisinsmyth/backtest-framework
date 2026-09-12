"""The frozen cell drawn on twelve names and dates it has never seen.

    uv run python scripts/d399_new_sample.py
    uv run python scripts/d399_splice_sample_page.py

No score on the page: both hand-drawn ground truths are GME's alone, and the principal adjusts
from what he sees. What the page carries instead is the sample's own provenance -- the draw was
seeded and the selection rule declared before any chart existed -- and the two invariants, which
hold without any ground truth at all.

GENERIC SANITISER, as every page here: a bare NaN token makes JSON.parse throw and the page
renders blank with no visible error.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
       else REPO / "temp" / "d399_new_sample_chart.json")
OUT = (Path(sys.argv[2]).resolve() if len(sys.argv) > 2
       else REPO / "temp" / "d399_sample_page.html")


def clean(x, p=6):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


HTML = r"""<title>Twelve Names It Has Never Seen</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#faf9f7; --panel:#fff; --ink:#15181d; --muted:#6a7078; --faint:#9aa1a9;
  --rule:#e3e0da; --rule-soft:#efece7; --chip:#f1eee9;
  --up:#1c6b52; --down:#a93d2c; --res:#c2410c; --sup:#1d4ed8; --cut:#7c3aed; --warn:#8a6d1f;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
    --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
    --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --cut:#b596f6; --warn:#d6b45f;
  }
}
:root[data-theme="dark"]{
  --ground:#101317; --panel:#161a1f; --ink:#e7e9ec; --muted:#9aa2ab; --faint:#6c757e;
  --rule:#272c33; --rule-soft:#1e232a; --chip:#1c2128;
  --up:#4cae87; --down:#e0705c; --res:#f0955a; --sup:#7aa2f7; --cut:#b596f6; --warn:#d6b45f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;font-size:15px;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1220px;margin:0 auto;padding:34px 22px 64px;display:flex;flex-direction:column;gap:20px}
h1{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:34px;margin:0;letter-spacing:-.01em}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
.lede{max-width:68ch;color:var(--muted);margin:0}
.lede b{color:var(--ink);font-weight:600}
.cfg{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
.grid{display:flex;flex-direction:column;gap:16px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.ph{display:flex;align-items:baseline;gap:12px;padding:11px 16px 3px;flex-wrap:wrap}
.ph h2{font-family:"Newsreader",Georgia,serif;font-size:19px;font-weight:600;margin:0}
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
  <div class="eyebrow">D399 &middot; a new name and date sample</div>
  <h1 id="h1">Twelve names it has never seen</h1>
  <p class="lede" id="lede1">Everything up to now was <b>one name over one 260-bar window</b> &mdash; GME,
    picked over and re-picked by eye across several hundred variants. These twelve are the first
    data the construction has met that it was not shaped on.</p>
  <p class="lede">The draw was <b>seeded and the rule written down before any chart existed</b>:
    every bar must clear D343's price and dollar-volume floor, any window containing a single-bar
    move over 40% in logs is rejected as an unadjusted split, GME is excluded, and twelve
    (name, start) pairs are taken uniformly from the 366,158 that qualify. BA came up twice because
    the draw is over <em>pairs</em>, not names.</p>
  <div class="cfg" id="cfg"></div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance</span>
    <span><i class="sw" style="border-color:var(--muted);border-top-style:dashed"></i> back to the segment's first pivot</span>
    <span>gaps = no trend on that side</span>
  </div>

  <div class="grid" id="grid"></div>

  <p class="note"><b>No score here.</b> Both hand-drawn ground truths &mdash; the 25 lines and the
    53 pivots &mdash; are GME's alone, so there is nothing on these names to resemble. What still
    holds without one is asserted rather than hoped: <b>no line runs through a candle body and no
    channel is inverted, on all twelve</b>.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var W = 1180, H = 250, PL = 8, PR = 62, PT = 12, PB = 22;
  var iw = W - PL - PR, ih = H - PT - PB;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }

  if (D.page){
    if (D.page.title) document.getElementById('h1').innerHTML = D.page.title;
    if (D.page.lede1) document.getElementById('lede1').innerHTML = D.page.lede1;
    if (D.page.lede2) document.getElementById('lede1').innerHTML += ' ' + D.page.lede2;
  }
  var c = D.cell;
  document.getElementById('cfg').textContent =
    'k=' + c.k + ' tie-tolerant  ·  height deadband ' + c.dh + '%  ·  gradient deadband off  ·  ' +
    'body break on  ·  min_piv ' + c.min_piv + '  ·  break bar = provisional pivot  ·  ' +
    'intercept from body clearance  ·  age decay ' + c.decay_end + '  ·  seed ' + D.seed;

  document.getElementById('grid').innerHTML = D.charts.map(function(ch){
    var n = ch.n, i, mn = Infinity, mx = -Infinity;
    for (i = 0; i < n; i++){
      if (ch.low[i] < mn) mn = ch.low[i];
      if (ch.high[i] > mx) mx = ch.high[i];
    }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.07 || 0.05;
    a -= pad; b += pad;
    function X(q){ return PL + q * (iw / n) + (iw / n) / 2; }
    function Y(p){ return PT + ih - (Math.log(p) - a) / (b - a) * ih; }
    var s = '', k;
    for (k = 0; k <= 4; k++){
      var lv = a + (b - a) * k / 4, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' +
           y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) +
           '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' +
           Math.exp(lv).toFixed(Math.exp(lv) < 10 ? 2 : 0) + '</text>';
    }
    var bw = iw / n, cw = Math.max(1.3, bw * 0.6);
    for (i = 0; i < n; i++){
      var o = ch.open[i], cl = ch.close[i], up = cl >= o;
      var col = up ? 'var(--up)' : 'var(--down)', x = X(i), yo = Y(o), yc = Y(cl);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + Y(ch.high[i]).toFixed(1) +
           '" y2="' + Y(ch.low[i]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity=".8"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) +
           '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) +
           '" fill="' + col + '" opacity=".8"/>';
    }
    // off-panel segments are MARKED: a triangle at the edge, at the x where the line is
    // furthest out, in the segment's colour (the review found one drawn entirely above its panel)
    var offCount = 0;
    function segLine(segs, col){
      var out = '', marks = '';
      (segs || []).forEach(function(g){
        function at(q){ return Math.exp(g.g * (q + ch.start_bar) + g.c); }
        var q0 = g.anchored_before ? g.s0 : g.t0;
        var ys = [[q0, Y(at(q0))], [g.t0, Y(at(g.t0))], [g.t1, Y(at(g.t1))]];
        var top = ys.reduce(function(a, p){ return p[1] < a[1] ? p : a; });
        var bot = ys.reduce(function(a, p){ return p[1] > a[1] ? p : a; });
        if (top[1] < PT){ marks += '<path d="M' + (X(Math.max(0, Math.min(n - 1, top[0]))) - 5).toFixed(1) +
          ',' + (PT + 9) + ' l5,-8 l5,8 z" fill="' + col + '" opacity=".9"/>'; offCount++; }
        if (bot[1] > PT + ih){ marks += '<path d="M' + (X(Math.max(0, Math.min(n - 1, bot[0]))) - 5).toFixed(1) +
          ',' + (PT + ih - 9) + ' l5,8 l5,-8 z" fill="' + col + '" opacity=".9"/>'; offCount++; }
        if (g.anchored_before){
          out += '<path d="M' + X(g.s0).toFixed(1) + ',' + Y(at(g.s0)).toFixed(1) + 'L' +
                 X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + '" fill="none" stroke="' +
                 col + '" stroke-width="1.2" stroke-dasharray="3 3" opacity=".5"/>';
          out += '<circle cx="' + X(g.s0).toFixed(1) + '" cy="' + Y(at(g.s0)).toFixed(1) +
                 '" r="2.3" fill="' + col + '" opacity=".8"/>';
        }
        out += '<path d="M' + X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + 'L' +
               X(g.t1).toFixed(1) + ',' + Y(at(g.t1)).toFixed(1) + '" fill="none" stroke="' + col +
               '" stroke-width="2" stroke-linecap="round"/>';
      });
      return '<g clip-path="url(#clip' + esc(ch.symbol) + ch.start_bar + ')">' + out + '</g>' + marks;
    }
    s = '<defs><clipPath id="clip' + esc(ch.symbol) + ch.start_bar + '"><rect x="0" y="' + PT +
        '" width="' + W + '" height="' + ih + '"/></clipPath></defs>' + s;
    s += segLine(ch.segments.support, 'var(--sup)') +
         segLine(ch.segments.resistance, 'var(--res)');
    // THE PRINCIPAL'S HAND LINES, if the chart carries them: each drawn between its anchors,
    // thin and dashed, in the side's colour, with a dotted continuation to the bar it was ended
    if (ch.hand){
      var hh = '';
      ch.hand.forEach(function(L){
        var col = L.kind === 'support' ? 'var(--sup)' : 'var(--res)';
        var x1 = L.x1 - ch.start_bar, x2 = L.x2 - ch.start_bar, g = (Math.log(L.p2) - Math.log(L.p1)) / (L.x2 - L.x1);
        function at(q){ return Math.exp(Math.log(L.p1) + g * (q - x1)); }
        var xe = Math.min(n - 1, (L.until != null ? L.until : ch.start_bar + n - 1) - ch.start_bar);
        hh += '<path d="M' + X(x1).toFixed(1) + ',' + Y(at(x1)).toFixed(1) + 'L' + X(x2).toFixed(1) + ',' + Y(at(x2)).toFixed(1) +
              '" fill="none" stroke="' + col + '" stroke-width="1.4" stroke-dasharray="6 4" opacity=".85"/>';
        if (xe > x2) hh += '<path d="M' + X(x2).toFixed(1) + ',' + Y(at(x2)).toFixed(1) + 'L' + X(xe).toFixed(1) + ',' + Y(at(xe)).toFixed(1) +
              '" fill="none" stroke="' + col + '" stroke-width="1" stroke-dasharray="1 4" opacity=".6"/>';
      });
      s += '<g clip-path="url(#clip' + esc(ch.symbol) + ch.start_bar + ')">' + hh + '</g>';
    }
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" ' +
           'font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' +
           esc(ch.dates[i]) + '</text>';
    }
    var ns = (ch.segments.support || []).length + (ch.segments.resistance || []).length;
    return '<div class="panel"><div class="ph"><h2>' + esc(ch.symbol) + '</h2>' +
      '<span class="dt">' + esc(ch.dates[0]) + ' &rarr; ' + esc(ch.dates[n - 1]) + '</span>' +
      '<span class="st">' + ns + ' segments' + (offCount ? ' &middot; <b>' + offCount +
      ' off panel &#9650;&#9660;</b>' : '') + (ch.stats ? ' &middot; ' + esc(ch.stats) : '') +
      '</span></div>' +
      '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' +
      esc(ch.symbol) + '">' + s + '</svg></div></div>';
  }).join('');
})();
</script>
"""


def main() -> int:
    d = clean(json.loads(SRC.read_text()))
    payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived clean()"
    out = HTML.replace("__DATA__", payload)

    def _bare(t):
        raise ValueError(f"bare {t} -- JSON.parse would throw and the page would render blank")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)
    OUT.write_text(out, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out):,} bytes, {len(d['charts'])} charts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
