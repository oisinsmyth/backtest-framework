"""Splice the comparison payload into the side-by-side page. Same sanitiser discipline."""
import json
import math
from pathlib import Path

SCRATCH = Path(r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\f1781fb2-b9e5-432b-b1f3-adbecad8511c\scratchpad")
REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\signal-hunt-part2")

d = json.loads((REPO / "temp" / "d399_compare_data.json").read_text())


def clean(x, p=5):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


payload = json.dumps(clean(d), separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload

tpl = (SCRATCH / "compare.html").read_text(encoding="utf-8")
assert "__DATA__" in tpl
out = tpl.replace("__DATA__", payload)


def _bare(t):
    raise ValueError(f"bare {t} in the payload -- the page would render blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(SCRATCH / "compare_final.html").write_text(out, encoding="utf-8")
print(f"wrote compare_final.html  {len(out)/1024:.0f} KB")
for s in ("support", "resistance"):
    r = d["ribbon"][s]
    print(f"  {s:>10s}: drawn {r['human_bars']:>3d}  fitted {r['machine_bars']:>3d}  "
          f"both {r['both']:>3d}  recall {100*r['both']/r['human_bars']:.0f}%  "
          f"precision {100*r['both']/r['machine_bars']:.0f}%")
