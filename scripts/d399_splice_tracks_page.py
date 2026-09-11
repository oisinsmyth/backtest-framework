"""The segmenting function taken apart: GRADIENT and OFFSET on the same time axis as the price.

    uv run python scripts/d399_recalc_segment.py --k 1 --dh 30 --chart-one
    uv run python scripts/d399_splice_tracks_page.py

WHAT THIS IS FOR. Every chart so far showed the LINE. The line is two quantities multiplied
together and it hides which of them moved: a jump can be the gradient re-fitting, the offset
re-anchoring, or both. Three aligned tracks separate them --

    1. price, with the fitted support and resistance
    2. GRADIENT, per side, in annualised per cent
    3. OFFSET, per side: how far the line sits from that bar's own low (support) or high
       (resistance), in per cent

-- and the segment boundaries are ticked on all three, so whether the two quantities move
together or independently is a thing you can see rather than a thing you have to be told.

THE ANSWER IS VISIBLE IMMEDIATELY AND IT IS THE POINT: in this construction they are not
generated separately at all. Gradient and offset are the slope and intercept of ONE OLS fit,
frozen together when the segment opens, so every change in one is simultaneous with a change in
the other. The earlier ratchet design was the opposite -- the gradient held while the offset slid.
Nothing here can do that.

GENERIC SANITISER, same as every page in this thread: `json.dumps` writes a bare `NaN` for a
non-finite float, `JSON.parse` rejects it, and the page renders BLANK with no visible error.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
       else REPO / "temp" / "d399_recalc_chart.json")
OUT = (Path(sys.argv[2]).resolve() if len(sys.argv) > 2
       else REPO / "temp" / "d399_tracks_page.html")


def clean(x, p=6):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


HTML = r"""<title>Gradient and Offset</title>
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
.lede{max-width:66ch;color:var(--muted);margin:0}
.lede b{color:var(--ink);font-weight:600}
.cfg{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}
.stack{background:var(--panel);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.tk{border-top:1px solid var(--rule-soft)}
.tk:first-child{border-top:none}
.tkh{display:flex;align-items:baseline;gap:12px;padding:9px 16px 2px}
.tkh h2{font-family:"Newsreader",Georgia,serif;font-size:17px;font-weight:600;margin:0}
.tkh .sub{font-size:12.5px;color:var(--faint)}
.tkb{overflow-x:auto}
.tkb svg{display:block;width:100%;min-width:900px;height:auto}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:20px;border-top-width:2.5px;border-top-style:solid;display:inline-block}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);
  max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">D399 &middot; the segmenting function, taken apart</div>
  <h1>Gradient and offset</h1>
  <p class="lede">The line you have been judging is two quantities at once, and a chart of the line
    cannot say which of them moved. These three tracks share one time axis: the price with the
    fitted lines, then the <b>gradient</b> each line carries, then the <b>offset</b> &mdash; how far
    that line sits from the bar's own low or high. Segment boundaries are ticked on all three.</p>
  <p class="lede"><b>They move together, always.</b> Gradient and offset are the slope and intercept
    of one OLS fit, frozen when the segment opens, so neither can change without the other. The
    ratchet design did the opposite: the gradient held while the offset slid. Nothing in this
    construction can do that.</p>
  <div class="cfg" id="cfg"></div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance</span>
    <span><i class="sw" style="border-color:var(--cut);border-top-style:dashed"></i> segment boundary</span>
    <span>gaps = no trend on that side</span>
  </div>

  <div id="stack"></div>

  <p class="note"><b>Each trend line now starts at the first pivot it was fitted to</b>, marked
    with a dot. The dashed stretch is where that fit already existed but the construction was not
    yet allowed to call it a trend &mdash; it was still short of <code>min_piv</code>. Only the
    solid stretch is scored: the scored arrays are unchanged, the drawing gained the rest.</p>

  <p class="note"><b>Offset sign convention.</b> Support is drawn as its distance <i>below</i> the
    bar's low and resistance as its distance <i>above</i> the bar's high, so on both tracks
    <b>zero means touching and larger means further away</b>. A support line that crosses above the
    low, or a resistance that drops below the high, goes negative &mdash; that is the line running
    through the candle.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var c = D.cells[D.cells.length - 1];
  var n = D.n, W = 1200, PL = 8, PR = 66;
  var iw = W - PL - PR;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }
  function X(i){ return PL + i * (iw / n) + (iw / n) / 2; }

  document.getElementById('cfg').textContent =
    esc(D.symbol) + '  bars ' + D.start_bar + '–' + (D.start_bar + n - 1) + '   ·   ' +
    esc(c.label) + '   ·   score ' + c.SCORE.toFixed(4);

  var cuts = {};
  c.cuts_support.forEach(function(i){ cuts[i] = (cuts[i] || 0) | 1; });
  c.cuts_resistance.forEach(function(i){ cuts[i] = (cuts[i] || 0) | 2; });
  var cutBars = Object.keys(cuts).map(Number).sort(function(a, b){ return a - b; });

  function cutTicks(PT, ih){
    return cutBars.map(function(i){
      return '<line x1="' + X(i).toFixed(1) + '" x2="' + X(i).toFixed(1) + '" y1="' + PT +
             '" y2="' + (PT + ih) + '" stroke="var(--cut)" stroke-width="1" ' +
             'stroke-dasharray="2 4" opacity=".55"/>';
    }).join('');
  }

  // ---------- track 1: price
  function priceTrack(){
    var H = 300, PT = 12, PB = 22, ih = H - PT - PB, s = '', i;
    var mn = Infinity, mx = -Infinity;
    for (i = 0; i < n; i++){
      if (D.low[i] < mn) mn = D.low[i];
      if (D.high[i] > mx) mx = D.high[i];
    }
    var a = Math.log(mn), b = Math.log(mx), pad = (b - a) * 0.06;
    a -= pad; b += pad;
    function Y(p){ return PT + ih - (Math.log(p) - a) / (b - a) * ih; }
    for (i = 0; i <= 4; i++){
      var lv = a + (b - a) * i / 4, y = Y(Math.exp(lv));
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' +
           y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) +
           '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">$' +
           Math.exp(lv).toFixed(2) + '</text>';
    }
    s += cutTicks(PT, ih);
    var bw = iw / n, cw = Math.max(1.4, bw * 0.6);
    for (i = 0; i < n; i++){
      var o = D.open[i], cl = D.close[i], up = cl >= o, col = up ? 'var(--up)' : 'var(--down)';
      var x = X(i), yo = Y(o), yc = Y(cl);
      s += '<line x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + Y(D.high[i]).toFixed(1) +
           '" y2="' + Y(D.low[i]).toFixed(1) + '" stroke="' + col + '" stroke-width="1" opacity=".8"/>';
      s += '<rect x="' + (x - cw / 2).toFixed(1) + '" y="' + Math.min(yo, yc).toFixed(1) +
           '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, Math.abs(yc - yo)).toFixed(1) +
           '" fill="' + col + '" opacity=".8"/>';
    }
    s += segLine(c.segments.support, Y, 'var(--sup)') +
         segLine(c.segments.resistance, Y, 'var(--res)');
    for (i = 0; i < n; i += 40){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" ' +
           'font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' +
           esc(D.dates[i]) + '</text>';
    }
    return svg(W, H, s);
  }

  // Each segment drawn as ONE straight line from the first pivot it was fitted to (s0) through
  // its last live bar (t1). The stretch before emission began (s0 -> t0) is dashed: the line
  // exists there as a fit but the construction was not yet allowed to call it a trend.
  function segLine(segs, Y, col){
    var s = '';
    (segs || []).forEach(function(g){
      function at(q){ return Math.exp(g.g * (q + D.start_bar) + g.c); }
      if (g.anchored_before){
        s += '<path d="M' + X(g.s0).toFixed(1) + ',' + Y(at(g.s0)).toFixed(1) + 'L' +
             X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + '" fill="none" stroke="' + col +
             '" stroke-width="1.4" stroke-dasharray="3 3" opacity=".55"/>';
        s += '<circle cx="' + X(g.s0).toFixed(1) + '" cy="' + Y(at(g.s0)).toFixed(1) +
             '" r="2.6" fill="' + col + '" opacity=".8"/>';
      }
      s += '<path d="M' + X(g.t0).toFixed(1) + ',' + Y(at(g.t0)).toFixed(1) + 'L' +
           X(g.t1).toFixed(1) + ',' + Y(at(g.t1)).toFixed(1) + '" fill="none" stroke="' + col +
           '" stroke-width="2" stroke-linecap="round"/>';
    });
    return s;
  }

  function line(arr, Y, col){
    var s = '', run = [];
    function flush(){
      if (run.length > 1) s += '<path d="M' + run.join('L') + '" fill="none" stroke="' + col +
        '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
      run = [];
    }
    for (var i = 0; i < n; i++){
      var v = arr[i];
      if (v === null || !isFinite(v)){ flush(); continue; }
      run.push(X(i).toFixed(1) + ',' + Y(v).toFixed(1));
    }
    flush();
    return s;
  }

  // ---------- generic value track (stepped, gaps preserved)
  function valTrack(series, fmt, zero){
    var H = 150, PT = 12, PB = 20, ih = H - PT - PB, s = '', i, k;
    var mn = Infinity, mx = -Infinity;
    series.forEach(function(sr){
      for (i = 0; i < n; i++){
        var v = sr.v[i];
        if (v === null || !isFinite(v)) continue;
        if (v < mn) mn = v;
        if (v > mx) mx = v;
      }
    });
    if (!isFinite(mn)){ mn = -1; mx = 1; }
    if (zero){ mn = Math.min(mn, 0); mx = Math.max(mx, 0); }
    var pad = (mx - mn) * 0.12 || 1;
    mn -= pad; mx += pad;
    function Y(v){ return PT + ih - (v - mn) / (mx - mn) * ih; }
    for (k = 0; k <= 3; k++){
      var lv = mn + (mx - mn) * k / 3, y = Y(lv);
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + y.toFixed(1) + '" y2="' +
           y.toFixed(1) + '" stroke="var(--rule-soft)"/>';
      s += '<text x="' + (PL + iw + 8) + '" y="' + (y + 3.5).toFixed(1) +
           '" font-family="IBM Plex Mono,monospace" font-size="10" fill="var(--faint)">' +
           fmt(lv) + '</text>';
    }
    if (zero && mn < 0 && mx > 0){
      s += '<line x1="' + PL + '" x2="' + (PL + iw) + '" y1="' + Y(0).toFixed(1) + '" y2="' +
           Y(0).toFixed(1) + '" stroke="var(--faint)" stroke-width="1"/>';
    }
    s += cutTicks(PT, ih);
    series.forEach(function(sr){
      var run = [];
      function flush(){
        if (run.length > 1) s += '<path d="M' + run.join('L') + '" fill="none" stroke="' +
          sr.col + '" stroke-width="1.8" stroke-linejoin="round"/>';
        run = [];
      }
      for (i = 0; i < n; i++){
        var v = sr.v[i];
        if (v === null || !isFinite(v)){ flush(); continue; }
        // stepped: hold the value across the bar so a re-fit reads as a jump, not a ramp
        if (run.length) run.push(X(i).toFixed(1) + ',' + Y(prev).toFixed(1));
        run.push(X(i).toFixed(1) + ',' + Y(v).toFixed(1));
        var prev = v;
      }
      flush();
    });
    return svg(W, H, s);
  }

  function svg(w, h, body){
    return '<svg viewBox="0 0 ' + w + ' ' + h + '">' + body + '</svg>';
  }

  // gradient: per-bar log slope -> annualised per cent
  function ann(v){ return v === null || !isFinite(v) ? null : (Math.exp(v * 252) - 1) * 100; }
  var gS = c.g_support.map(ann), gR = c.g_resistance.map(ann);

  // offset: distance from the bar's own extreme, signed so zero = touching, larger = further
  var oS = [], oR = [];
  for (var i = 0; i < n; i++){
    var v = c.support[i];
    oS.push(v === null || !isFinite(v) ? null : (D.low[i] / v - 1) * 100);
    var w = c.resistance[i];
    oR.push(w === null || !isFinite(w) ? null : (w / D.high[i] - 1) * 100);
  }

  function panel(title, sub, body){
    return '<div class="tk"><div class="tkh"><h2>' + title + '</h2><span class="sub">' + sub +
           '</span></div><div class="tkb">' + body + '</div></div>';
  }
  document.getElementById('stack').innerHTML = '<div class="stack">' +
    panel('Price and the fitted lines', esc(D.symbol) + ', log scale', priceTrack()) +
    panel('Gradient', 'annualised per cent per year, held across the segment',
          valTrack([{v: gS, col: 'var(--sup)'}, {v: gR, col: 'var(--res)'}],
                   function(v){ return v.toFixed(0) + '%'; }, true)) +
    panel('Offset', 'distance from the bar’s own low / high; 0 = touching, negative = through it',
          valTrack([{v: oS, col: 'var(--sup)'}, {v: oR, col: 'var(--res)'}],
                   function(v){ return v.toFixed(0) + '%'; }, true)) +
    '</div>';
})();
</script>
"""


def main() -> int:
    d = clean(json.loads(SRC.read_text()))
    keep = {k: d[k] for k in ("symbol", "start_bar", "n", "dates",
                              "open", "high", "low", "close")}
    keep["cells"] = [d["cells"][-1]]
    payload = json.dumps(keep, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived clean()"
    out = HTML.replace("__DATA__", payload)

    def _bare(t):
        raise ValueError(f"bare {t} -- JSON.parse would throw and the page would render blank")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)
    OUT.write_text(out, encoding="utf-8")
    c = keep["cells"][0]
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out):,} bytes)")
    print(f"  cell {c['label']}  score {c['SCORE']}  cuts {c['n_cuts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
