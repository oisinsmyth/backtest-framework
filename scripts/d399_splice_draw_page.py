"""Splice GME's bars alone into the blank drawing page.

Same sanitiser discipline as scripts/d399_splice_charts.py: a bare NaN token makes JSON.parse
throw and renders the page blank with no visible error, so every float is finite or None and the
emitted block is re-parsed strictly before the file is written.
"""
import json
import math
from pathlib import Path

SCRATCH = Path(r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\f1781fb2-b9e5-432b-b1f3-adbecad8511c\scratchpad")
REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\signal-hunt-part2")

src = json.loads((REPO / "temp" / "d399_chart_data.json").read_text())
gme = [c for c in src["charts"] if c["symbol"] == "GME"]
assert len(gme) == 1, f"expected one GME chart, got {len(gme)}"
c = gme[0]

keep = {k: c[k] for k in ("symbol", "start", "n", "dates", "open", "high", "low", "close")}


def clean(x, p=5):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


keep = clean(keep)
keep["dates"] = [str(x)[:10] for x in keep["dates"]]
d = {"note": "BLANK. The principal draws the lines; nothing is fitted here.", "charts": [keep]}

payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload

tpl = (SCRATCH / "gme_draw.html").read_text(encoding="utf-8")
assert "__DATA__" in tpl
out = tpl.replace("__DATA__", payload)


def _bare(t):
    raise ValueError(f"bare {t} in the payload -- the page would render blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(SCRATCH / "gme_draw_final.html").write_text(out, encoding="utf-8")
print(f"wrote gme_draw_final.html  {len(out)/1024:.0f} KB")
print(f"  GME bars {keep['start']}-{keep['start']+keep['n']}  "
      f"{keep['dates'][0]} -> {keep['dates'][-1]}  n={keep['n']}")
