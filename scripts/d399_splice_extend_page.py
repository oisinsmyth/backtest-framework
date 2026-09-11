"""Before / after: the frozen cell against extend-back, on the name the walk changed most.

    uv run python scripts/d399_new_sample.py --compare
    uv run python scripts/d399_splice_extend_page.py

Two panels of the same bars, same cell, same pivots; the only difference is what happens to the
invalidated segment's points when the next segment forms. Above, `carry=3` takes three of them
unconditionally. Below, the walk keeps every one that still fits, newest first, and stops at the
first that does not. Same sanitiser discipline as every page here.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
       else REPO / "temp" / "d399_extend_chart.json")
OUT = (Path(sys.argv[2]).resolve() if len(sys.argv) > 2
       else REPO / "temp" / "d399_extend_page.html")
PICK = sys.argv[3] if len(sys.argv) > 3 else None


def clean(x, p=6):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


HTML = r"""<title>Keeping What Still Fits</title>
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
table.sum{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
table.sum th{text-align:right;font-weight:500;color:var(--muted);font-size:11px;
  font-family:"IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;
  padding:0 10px 8px;border-bottom:1px solid var(--rule)}
table.sum th:first-child,table.sum td:first-child{text-align:left}
table.sum td{padding:7px 10px;border-bottom:1px solid var(--rule-soft)}
table.sum td.num{text-align:right;font-family:"IBM Plex Mono",monospace}
table.sum tr.pick td{background:var(--chip)}
.note{border-left:3px solid var(--warn);padding:2px 0 2px 15px;color:var(--muted);
  max-width:72ch;font-size:14px}
.note b{color:var(--ink);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">D399 &middot; what the next segment keeps of the last</div>
  <h1>Keeping what still fits</h1>
  <p class="lede">Same bars, same cell, same pivots. The only difference is what happens to the
    invalidated segment's points when the next one forms. <b>Above:</b> <code>carry=3</code> takes
    three of them, unconditionally. <b>Below:</b> the walk keeps every one that still fits &mdash;
    within the height deadband of the new line, with a back-projection that clears every body
    &mdash; newest first, stopping at the first that does not.</p>
  <p class="lede" id="picknote"></p>
  <div class="cfg" id="cfg"></div>

  <div class="legend">
    <span><i class="sw" style="border-color:var(--sup)"></i> support</span>
    <span><i class="sw" style="border-color:var(--res)"></i> resistance</span>
    <span><i class="sw" style="border-color:var(--muted);border-top-style:dashed"></i> back to the segment's first pivot</span>
  </div>

  <div class="grid" id="grid"></div>

  <div id="tbl"></div>

  <p class="note"><b>Coverage did not fall.</b> A first version set <code>carry=0</code> on the
    theory that the walk made it redundant, and coverage collapsed from 69% to 38% &mdash; the
    whole drop was the carry change, not the walk. They answer different invalidations: after a
    gradient or height drift there is no new information and the side needs carried points to
    re-qualify at all; after a break there is, and the walk decides how far back the new trend
    reaches. Kept together, coverage goes <em>up</em>.</p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('payload').textContent);
  var W = 1180, H = 290, PL = 8, PR = 62, PT = 12, PB = 22;
  var iw = W - PL - PR, ih = H - PT - PB;
  function esc(s){ return String(s).replace(/[&<>]/g, function(q){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[q]; }); }

  var c = D.cell;
  document.getElementById('cfg').textContent =
    'k=' + c.k + ' tie-tolerant  ·  height deadband ' + c.dh + '%  ·  body break on  ·  min_piv ' +
    c.min_piv + '  ·  provisional break pivot  ·  intercept from body clearance  ·  age decay ' +
    c.decay_end + '  ·  seed ' + D.seed;

  var pick = D.pick;
  document.getElementById('picknote').innerHTML =
    '<b>' + esc(pick) + '</b> is shown because it is the name the walk changed most: the median ' +
    'distance from a segment\'s first pivot to where it is first drawn moved furthest back.';

  function panel(ch, title){
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
    function segLine(segs, col){
      var out = '';
      (segs || []).forEach(function(g){
        function at(q){ return Math.exp(g.g * (q + ch.start_bar) + g.c); }
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
      return out;
    }
    s += segLine(ch.segments.support, 'var(--sup)') +
         segLine(ch.segments.resistance, 'var(--res)');
    for (i = 0; i < n; i += 45){
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" ' +
           'font-family="IBM Plex Mono,monospace" font-size="9.5" fill="var(--faint)">' +
           esc(ch.dates[i]) + '</text>';
    }
    var ns = (ch.segments.support || []).length + (ch.segments.resistance || []).length;
    return '<div class="panel"><div class="ph"><h2>' + esc(title) + '</h2>' +
      '<span class="dt">' + esc(ch.symbol) + ' &middot; ' + esc(ch.dates[0]) + ' &rarr; ' +
      esc(ch.dates[n - 1]) + '</span><span class="st">' + ns + ' segments</span></div>' +
      '<div class="pb"><svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' +
      esc(title) + '">' + s + '</svg></div></div>';
  }

  var html = '';
  D.variants.forEach(function(v){
    var ch = null;
    v.charts.forEach(function(x){ if (x.symbol === pick && !ch) ch = x; });
    if (ch) html += panel(ch, v.label);
  });
  document.getElementById('grid').innerHTML = html;

  // every name, both ways
  var rows = '';
  var F = D.variants[0].charts, E = D.variants[1].charts;
  for (var i = 0; i < F.length; i++){
    function cnt(x){ return (x.segments.support || []).length + (x.segments.resistance || []).length; }
    function reach(x){
      var r = [];
      ['support', 'resistance'].forEach(function(kd){
        (x.segments[kd] || []).forEach(function(g){ r.push(g.t0 - g.s0); });
      });
      r.sort(function(a, b){ return a - b; });
      return r.length ? r[Math.floor(r.length / 2)] : 0;
    }
    rows += '<tr' + (F[i].symbol === pick ? ' class="pick"' : '') + '><td>' + esc(F[i].symbol) +
      ' <span style="color:var(--faint);font-family:IBM Plex Mono,monospace;font-size:11px">' +
      esc(F[i].dates[0]) + '</span></td>' +
      '<td class="num">' + cnt(F[i]) + '</td><td class="num">' + cnt(E[i]) + '</td>' +
      '<td class="num">' + reach(F[i]) + '</td><td class="num">' + reach(E[i]) + '</td></tr>';
  }
  document.getElementById('tbl').innerHTML =
    '<table class="sum"><thead><tr><th>name</th><th>segments, carry=3</th>' +
    '<th>segments, walk</th><th>reach, carry=3</th><th>reach, walk</th></tr></thead><tbody>' +
    rows + '</tbody></table>';
})();
</script>
"""


def main() -> int:
    d = clean(json.loads(SRC.read_text()))
    if PICK:
        d["pick"] = PICK
    payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
    assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived clean()"
    out = HTML.replace("__DATA__", payload)

    def _bare(t):
        raise ValueError(f"bare {t} -- JSON.parse would throw and the page would render blank")

    block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
    json.loads(block, parse_constant=_bare)
    OUT.write_text(out, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)} ({len(out):,} bytes), showing {d['pick']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
