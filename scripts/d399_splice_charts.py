"""Splice the chart data into the template.

GENERIC SANITISER, and it exists because a targeted one silently broke the page. `json.dumps`
writes bare `NaN` for a non-finite float; Python's `json.load` accepts that token, but
`JSON.parse` in the browser REJECTS it -- so one unsanitised field threw inside the page's script
and rendered NOTHING AT ALL, with no visible error. The previous version listed the fields to
round by name, and fields added later (`g_lo`, `g_hi`) were not on the list.

So: walk the whole structure, convert every non-finite float to None, and ASSERT that no NaN or
Infinity token survives into the HTML. A blank page must not be a possible outcome again.
"""
import json
import math
from pathlib import Path

SCRATCH = Path(r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\f1781fb2-b9e5-432b-b1f3-adbecad8511c\scratchpad")
REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\signal-hunt-part2")

d = json.loads((REPO / "temp" / "d399_chart_data.json").read_text())


def clean(x, p=5):
    """Every float finite or None; everything else passed through untouched."""
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


d = clean(d)
for c in d["charts"]:
    c["dates"] = [str(x)[:10] for x in c["dates"]]

payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived the clean"

tpl = (SCRATCH / "ratchet_charts.html").read_text(encoding="utf-8")
assert "__DATA__" in tpl, "marker missing"
out = tpl.replace("__DATA__", payload)


def _bare(c):
    raise ValueError(f"bare {c} in the payload -- JSON.parse would throw and the page would be blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(SCRATCH / "ratchet_charts_final.html").write_text(out, encoding="utf-8")
print(f"wrote ratchet_charts_final.html  {len(out) / 1024:.0f} KB  ({len(d['charts'])} charts)")
print(f"  {'sym':>5s} {'support':>12s} {'resistance':>12s} {'state on':>12s}")
for c in d["charts"]:
    n = c["n"]
    a = sum(1 for v in c["line_lo"] if v is not None)
    b = sum(1 for v in c["line_hi"] if v is not None)
    st = sum(1 for v in c["state"] if v != 0)
    print(f"  {c['symbol']:>5s} {a:>8d}/{n} {b:>8d}/{n} {st:>8d}/{n}")
