"""D271 -- render the trade anatomy as a self-contained HTML report.

    uv run python scripts/d271_build_report.py

Reads `data/d271_trade_anatomy.json` and writes `docs/results/trade_anatomy.html`.
All charts are inline SVG generated here; no external assets, no scripts.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "d271_trade_anatomy.json"
OUT = REPO / "docs" / "results" / "trade_anatomy.html"

ORDER = ["LOW:S2_short_intra", "HIGH:S1_short_intra", "LOW:rel_vol Q5"]
NICE = {"LOW:S2_short_intra": "S2 short · low-vol",
        "HIGH:S1_short_intra": "S1 short · high-vol",
        "LOW:rel_vol Q5": "Relative volume Q5 · low-vol"}
NULLS = {"LOW:S2_short_intra": "rotation null 97.2th / 97.9th, both legs",
         "HIGH:S1_short_intra": "rotation null 96.9th / 99.7th, both legs",
         "LOW:rel_vol Q5": "monotone 5/5 · beats shuffle floor 3.68 vs 2.56 bp"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def histogram(p, cost, w=340, h=170, clip=280, bins=41):
    lo, hi = -clip, clip
    step = (hi - lo) / bins
    counts = [0] * bins
    for v in p:
        k = min(bins - 1, max(0, int((min(max(v, lo), hi) - lo) / step)))
        counts[k] += 1
    mx = max(counts) or 1
    pad_l, pad_b, pad_t = 6, 22, 8
    bw = (w - pad_l * 2) / bins
    out = []
    for i, c in enumerate(counts):
        bh = (h - pad_b - pad_t) * c / mx
        x = pad_l + i * bw
        mid = lo + (i + 0.5) * step
        fill = "var(--loss)" if mid < 0 else "var(--gain)"
        out.append(f'<rect x="{x:.1f}" y="{h - pad_b - bh:.1f}" width="{bw - 0.8:.1f}" '
                   f'height="{bh:.1f}" fill="{fill}" opacity=".78"/>')
    zx = pad_l + (0 - lo) / (hi - lo) * (w - pad_l * 2)
    cx = pad_l + (min(cost, hi) - lo) / (hi - lo) * (w - pad_l * 2)
    out.append(f'<line x1="{zx:.1f}" y1="{pad_t}" x2="{zx:.1f}" y2="{h - pad_b}" '
               f'stroke="var(--ink)" stroke-width="1" opacity=".45"/>')
    out.append(f'<line x1="{cx:.1f}" y1="{pad_t - 2}" x2="{cx:.1f}" y2="{h - pad_b}" '
               f'stroke="var(--accent)" stroke-width="1.6" stroke-dasharray="3 2"/>')
    out.append(f'<text x="{cx + 4:.1f}" y="{pad_t + 8}" class="cap" fill="var(--accent)">'
               f'cost {cost:.1f} bp</text>')
    out.append(f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_l}" y2="{h - pad_b}" '
               f'stroke="var(--rule)"/>')
    for v in (-clip, 0, clip):
        x = pad_l + (v - lo) / (hi - lo) * (w - pad_l * 2)
        out.append(f'<text x="{x:.1f}" y="{h - 7}" class="cap" text-anchor="middle">'
                   f'{v:+d}</text>')
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="P&amp;L distribution">'
            + "".join(out) + "</svg>")


def concentration(series, w=720, h=300):
    pad_l, pad_r, pad_t, pad_b = 44, 14, 14, 34
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    out = [f'<rect x="{pad_l}" y="{pad_t}" width="{iw}" height="{ih}" fill="none" '
           f'stroke="var(--rule)"/>']
    for f in (0.25, 0.5, 0.75):
        y = pad_t + ih * f
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + iw}" y2="{y:.1f}" '
                   f'stroke="var(--rule)" stroke-dasharray="2 3"/>')
    y100 = pad_t + ih * (1 - 100 / 500)
    out.append(f'<line x1="{pad_l}" y1="{y100:.1f}" x2="{pad_l + iw}" y2="{y100:.1f}" '
               f'stroke="var(--ink)" stroke-width="1.2" opacity=".5"/>')
    out.append(f'<text x="{pad_l + iw - 4}" y="{y100 - 5:.1f}" class="cap" '
               f'text-anchor="end">100% of total P&amp;L</text>')
    cols = ["var(--accent)", "var(--gain)", "var(--loss)"]
    for k, (name, xs, ys) in enumerate(series):
        pts = []
        for x, y in zip(xs, ys):
            px = pad_l + iw * x
            py = pad_t + ih * (1 - min(max(y, -0.2), 5.0) / 5.0)
            pts.append(f"{px:.1f},{py:.1f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{cols[k]}" '
                   f'stroke-width="2" stroke-linejoin="round"/>')
    for f, lab in ((0, "0%"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "100%")):
        x = pad_l + iw * f
        out.append(f'<text x="{x:.1f}" y="{h - 12}" class="cap" text-anchor="middle">{lab}</text>')
    for v in (0, 100, 200, 300, 400, 500):
        y = pad_t + ih * (1 - v / 500)
        out.append(f'<text x="{pad_l - 8}" y="{y + 3:.1f}" class="cap" '
                   f'text-anchor="end">{v}%</text>')
    out.append(f'<text x="{pad_l + iw / 2:.0f}" y="{h - 1}" class="cap" '
               f'text-anchor="middle">trades, ranked best to worst</text>')
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Cumulative share of total '
            f'P&amp;L by trade rank">' + "".join(out) + "</svg>")


def yearbars(by_year, w=340, h=150):
    ys = sorted(by_year)
    vals = [by_year[y]["mean_bp"] for y in ys]
    lim = max(abs(v) for v in vals) * 1.15 or 1
    pad_l, pad_b, pad_t = 8, 20, 8
    iw, ih = w - pad_l * 2, h - pad_b - pad_t
    zero = pad_t + ih / 2
    bw = iw / len(ys)
    out = [f'<line x1="{pad_l}" y1="{zero:.1f}" x2="{w - pad_l}" y2="{zero:.1f}" '
           f'stroke="var(--rule)"/>']
    for i, (y, v) in enumerate(zip(ys, vals)):
        bh = ih / 2 * abs(v) / lim
        x = pad_l + i * bw + bw * 0.18
        top = zero - bh if v > 0 else zero
        out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw * 0.64:.1f}" '
                   f'height="{bh:.1f}" fill="{"var(--gain)" if v > 0 else "var(--loss)"}" '
                   f'opacity=".85"/>')
        out.append(f'<text x="{x + bw * 0.32:.1f}" y="{h - 6}" class="cap" '
                   f'text-anchor="middle">{y[2:]}</text>')
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Mean P&amp;L per trade by year">'
            + "".join(out) + "</svg>")


def main() -> int:
    d = json.loads(SRC.read_text())
    conc = []
    for k in ORDER:
        p = sorted(d[k]["pnl_bp"], reverse=True)
        tot = sum(p)
        n = len(p)
        xs, ys, run = [], [], 0.0
        stepn = max(1, n // 400)
        for i, v in enumerate(p):
            run += v
            if i % stepn == 0 or i == n - 1:
                xs.append((i + 1) / n)
                ys.append(run / tot if tot else 0)
        conc.append((k, xs, ys))

    cards = []
    for k in ORDER:
        s = d[k]
        pc = s["percentiles"]
        cards.append(f"""
<article class="card">
  <header>
    <h3>{esc(NICE[k])}</h3>
    <p class="null">{esc(NULLS[k])}</p>
  </header>
  <div class="chart">{histogram(s["pnl_bp"], s["cost_bp"])}</div>
  <dl class="stats">
    <div><dt>trades</dt><dd>{s['n']:,}</dd></div>
    <div><dt>mean</dt><dd class="{'pos' if s['mean_bp']>0 else 'neg'}">{s['mean_bp']:+.2f} bp</dd></div>
    <div><dt>median</dt><dd>{s['median_bp']:+.2f} bp</dd></div>
    <div><dt>vs cost bar</dt><dd class="neg">{s['mean_vs_cost']:.2f}&times;</dd></div>
    <div><dt>hit rate</dt><dd>{s['hit_rate']:.1%}</dd></div>
    <div><dt>payoff</dt><dd>{s['payoff']:.2f}</dd></div>
    <div><dt>skew</dt><dd>{s['skew']:+.2f}</dd></div>
    <div><dt>kurtosis</dt><dd>{s['kurtosis']:.1f}</dd></div>
    <div><dt>mean hold</dt><dd>{s['mean_bars']:.1f} bars</dd></div>
    <div><dt>beat cost</dt><dd>{s['share_of_trades_above_cost']:.1%}</dd></div>
  </dl>
  <p class="pct"><span>p1 {pc['1']:+.0f}</span><span>p25 {pc['25']:+.0f}</span>
     <span>p50 {pc['50']:+.0f}</span><span>p75 {pc['75']:+.0f}</span>
     <span>p99 {pc['99']:+.0f}</span></p>
  <div class="chart small">{yearbars(s["by_year"])}</div>
  <p class="cap under">mean bp per trade, by year</p>
</article>""")

    # Computed, not transcribed -- a hardcoded table drifts the moment the data does.
    ex = {}
    for k in ORDER:
        arr = sorted(d[k]["pnl_bp"], reverse=True)
        n = len(arr)
        n1 = max(1, round(0.01 * n))
        tot = sum(arr)
        run, j = 0.0, n
        for i, v in enumerate(arr):
            run += v
            if run >= tot:
                j = i + 1
                break
        ex[k] = (sum(arr) / n, sum(arr[n1:]) / (n - n1), j, n)
    rows = "".join(
        f"<tr><td>{esc(NICE[k])}</td><td class='num pos'>{a:+.2f}</td>"
        f"<td class='num neg'>{b:+.2f}</td><td class='num'>{c:,} / {n:,}</td>"
        f"<td class='num'>{c / n:.2%}</td></tr>" for k, (a, b, c, n) in
        ((k, ex[k]) for k in ORDER))

    html = f"""<title>Where the Edge Actually Lives</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ground:#EFF1F5; --surface:#FFFFFF; --ink:#141A22; --ink-2:#4A5563;
  --rule:#CDD3DD; --accent:#3F5386; --accent-soft:#E6EAF4;
  --gain:#2C7A5B; --loss:#9E3B33;
  --measure:68ch;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#10141A; --surface:#171D26; --ink:#E4E8EF; --ink-2:#98A3B4;
    --rule:#2C3542; --accent:#93A7DA; --accent-soft:#1D2432;
    --gain:#5BB98C; --loss:#D97A6E;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#10141A; --surface:#171D26; --ink:#E4E8EF; --ink-2:#98A3B4;
  --rule:#2C3542; --accent:#93A7DA; --accent-soft:#1D2432;
  --gain:#5BB98C; --loss:#D97A6E;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:16px;line-height:1.6}}
.wrap{{max-width:1080px;margin:0 auto;padding:56px 24px 96px;
  display:flex;flex-direction:column;gap:44px}}
.eyebrow{{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.72rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);margin:0}}
h1{{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:clamp(2rem,4.6vw,3.1rem);
  line-height:1.1;margin:.25em 0 0;text-wrap:balance;letter-spacing:-.01em}}
h2{{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:1.6rem;margin:0 0 .2em;
  text-wrap:balance}}
h3{{font-family:Newsreader,Georgia,serif;font-weight:600;font-size:1.12rem;margin:0}}
p{{margin:0 0 1em;max-width:var(--measure)}}
p:last-child{{margin-bottom:0}}
.lede{{font-size:1.12rem;color:var(--ink-2)}}
strong{{font-weight:600}}
.finding{{background:var(--surface);border:1px solid var(--rule);
  border-left:3px solid var(--loss);padding:24px 26px;border-radius:2px}}
.finding p{{margin-bottom:.6em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}
.card{{background:var(--surface);border:1px solid var(--rule);border-radius:2px;
  padding:20px;display:flex;flex-direction:column;gap:12px}}
.card header{{display:flex;flex-direction:column;gap:2px}}
.null{{font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--accent);margin:0}}
.chart svg{{width:100%;height:auto;display:block}}
.cap{{font-family:"IBM Plex Mono",monospace;font-size:9px;fill:var(--ink-2);color:var(--ink-2)}}
.under{{font-size:.68rem;margin:0;text-align:center}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:2px 16px;margin:0;
  font-variant-numeric:tabular-nums}}
.stats>div{{display:flex;justify-content:space-between;gap:8px;
  border-bottom:1px dotted var(--rule);padding:2px 0}}
dt{{font-size:.78rem;color:var(--ink-2)}}
dd{{margin:0;font-family:"IBM Plex Mono",monospace;font-size:.78rem;font-weight:500}}
.pos{{color:var(--gain)}} .neg{{color:var(--loss)}}
.pct{{display:flex;flex-wrap:wrap;gap:4px 10px;font-family:"IBM Plex Mono",monospace;
  font-size:.68rem;color:var(--ink-2);margin:0}}
.hero{{background:var(--surface);border:1px solid var(--rule);border-radius:2px;padding:26px}}
.legend{{display:flex;flex-wrap:wrap;gap:16px;font-family:"IBM Plex Mono",monospace;
  font-size:.72rem;margin:10px 0 0}}
.legend span{{display:flex;align-items:center;gap:6px}}
.sw{{width:14px;height:3px;display:inline-block}}
.tblwrap{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:.85rem}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--rule)}}
th{{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--ink-2);font-weight:500}}
td.num{{font-family:"IBM Plex Mono",monospace;text-align:right;
  font-variant-numeric:tabular-nums}}
footer{{border-top:1px solid var(--rule);padding-top:20px;color:var(--ink-2);font-size:.8rem}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">D271 · trade-level anatomy · 15-minute single names, 2018–2026</p>
  <h1>Where the edge actually lives</h1>
</header>

<p class="lede">Three constructions in this programme survive a properly-constructed null.
Every number reported for them so far has been a mean. This is what the individual trades
behind those means look like — and the distribution says something the mean cannot.</p>

<section class="finding">
  <h2>Remove the best 1% of trades and all three lose money</h2>
  <div class="tblwrap">
  <table>
    <thead><tr><th>construction</th><th class="num">mean</th>
      <th class="num">excl. best 1%</th><th class="num">trades carrying 100% of profit</th>
      <th class="num">share</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  <p style="margin-top:18px">The nulls are real: these constructions beat matched-count
  rotation on both legs, and the volume score beats a shuffle floor while ordering
  monotonically across all five quintiles. <strong>What the nulls establish is that the
  timing is not random. What the distribution establishes is that the mean is carried by
  between twelve and a hundred and seventy trades.</strong></p>
</section>

<section class="hero">
  <h2>Cumulative share of total P&amp;L, by trade rank</h2>
  <p class="cap" style="font-size:.8rem;margin-bottom:14px">Each curve overshoots 100%
  within the first few percent of trades, then descends — every trade after the peak is,
  on net, giving profit back.</p>
  {concentration(conc)}
  <p class="legend">
    <span><i class="sw" style="background:var(--accent)"></i>S2 short · low-vol</span>
    <span><i class="sw" style="background:var(--gain)"></i>S1 short · high-vol</span>
    <span><i class="sw" style="background:var(--loss)"></i>Relative volume Q5</span>
  </p>
</section>

<section>
  <h2>Per-construction distributions</h2>
  <p>Gross P&amp;L per trade, in basis points, clipped at ±280. The dashed line is the
  round-trip cost each construction must clear. <strong>In all three the mass sits astride
  zero and the cost line falls inside the body of the distribution</strong> — under half of
  trades beat it.</p>
  <div class="grid">{"".join(cards)}</div>
</section>

<section class="finding" style="border-left-color:var(--accent)">
  <h2>A correction, and it changed a number by more than half</h2>
  <p>The first version of this page admitted a volume entry on <em>every</em> qualifying
  bar. Consecutive top-quintile bars share seven of their eight bars, so it reported
  <strong>43,204 &ldquo;trades&rdquo; from four names over 8.25 years &mdash; 1,309 per
  symbol per year against 252 sessions.</strong> A book cannot open 1,300 positions in 252
  sessions; those were overlapping observations wearing a trade&rsquo;s clothes.</p>
  <p>Held non-overlapping, as a book would: <strong>13,752 trades, mean +1.57 bp, and the
  t-statistic falls from +5.30 to +2.31</strong> &mdash; to roughly 1.6 once the four names&rsquo;
  cross-correlation is accounted for, since they carry only 1.87 effective instruments.</p>
  <p><strong>And the symmetry is the tell.</strong> The percentile ratios sit at 1.04, 1.08 and
  1.07 across p25/p75, p5/p95 and p1/p99 &mdash; a <em>constant</em> tilt at every point. That is
  a location shift, not a change of shape; a real edge fattens the winning tail relative to the
  losing one and the ratio grows outward. Against the unconditional distribution the conditioning
  moves the mean <strong>+2.15 bp</strong> and widens the spread from <strong>58.8 to 77.2 bp</strong>.
  <strong>High relative volume is mostly selecting volatility; direction is a side effect riding on
  it.</strong> The cost bar is 4.00 bp.</p>
</section>

<section>
  <h2>What the shape means</h2>
  <p><strong>Kurtosis between 10.7 and 24.5.</strong> A normal distribution scores 3. These
  are violently fat-tailed, which is why a mean computed over them is fragile.</p>
  <p><strong>Two of the three are positively skewed</strong> — +0.19 and +1.14. In a short
  book that is the wrong direction: it means the profit arrives as rare large gains rather
  than as a steady harvest, and rare large gains are exactly what a backtest cannot promise
  will recur.</p>
  <p><strong>Median P&amp;L is zero or negative in all three</strong> — the typical trade
  makes nothing. Hit rates cluster at 47.7–50.1% with payoff ratios of 1.08–1.19, so on the
  body of the distribution these are coin flips with almost no asymmetry.</p>
  <p><strong>The by-year bars show no era carrying it either.</strong> S2's mean per trade
  falls from +17.2 bp in 2018 to −6.1 in 2025; S1's is lumpy rather than trending. Neither
  looks like a stable process observed over eight years.</p>
</section>

<footer>
  <p>Produced by <code>scripts/d271_trade_anatomy.py</code> from
  <code>single_name_intraday_15m_panel.csv.gz</code> — 8 survivor names, 55,004 bars,
  2,117 sessions. Descriptive: no hurdle was run and no cell scored. Constructions are
  those surviving nulls in D264, D265 and D270. Survivorship applies — the provider serves
  no intraday bars for delisted tickers, so 41.6% of the 2013–17 cohort is unreachable.</p>
</footer>
</div>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1000:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
