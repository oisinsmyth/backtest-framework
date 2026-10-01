"""The volatility-unit year-concentration report — D729. INFORMATIONAL: it binds nothing.

D705's gate (d) asks whether one calendar year carries more than half a line's net, in dollars. D722 showed that this
conflates a line that was more often RIGHT in one year with a line that was equally right while that year's moves
were BIGGER: heating oil's 2022 was 62 % of its dollars and 30 % per unit of volatility. This report states both.

`year_concentration(sessions, gross, scale=None)` takes per-trade P&L in any unit and, optionally, a per-trade
volatility in the SAME unit known before the trade. It returns per-year counts, sums and shares of the total for the
gross and, when a scale is given, for u = gross / scale; the largest year and its share both ways; the number of
positive years; and a fixed label:

- UNDEFINED      either total is <= 0 (a share of a non-positive total means nothing);
- BOTH           the largest year's share is > CAP in both units;
- SCALE-CARRIED  > CAP in dollars and <= CAP in volatility units (the year's moves were bigger, not its calls better);
- VOL-ONLY       <= CAP in dollars and > CAP in volatility units;
- NEITHER        otherwise.
Without a scale the label is computed on the gross alone ("CONCENTRATED" / "NOT CONCENTRATED" / "UNDEFINED").

WHAT THIS MODULE IS NOT. It reads no fixture, chooses no scale and gates nothing: no frozen line, vault criterion or
existing gate changes because of it. A pre-registration that wants it as a gate must declare that in its own words.
House style follows `validation/power.py`: stdlib plus numpy, guards raise rather than return a sentinel.
"""
from __future__ import annotations

import re

import numpy as np

__all__ = ["CAP", "LABELS", "year_concentration"]

CAP = 0.5
LABELS = ("UNDEFINED", "BOTH", "SCALE-CARRIED", "VOL-ONLY", "NEITHER")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _by_year(years: np.ndarray, x: np.ndarray) -> dict:
    total = float(x.sum())
    out = {}
    for y in sorted(set(years.tolist())):
        m = years == y
        s = float(x[m].sum())
        out[y] = {"n": int(m.sum()), "sum": s, "share": (s / total) if total > 0 else None}
    return out


def _summary(per: dict, total: float) -> dict:
    if total <= 0:
        return {"total": total, "max_year": None, "max_share": None,
                "years_positive": sum(1 for v in per.values() if v["sum"] > 0), "n_years": len(per)}
    y = max(per, key=lambda k: (per[k]["sum"], k))
    return {"total": total, "max_year": y, "max_share": per[y]["share"],
            "years_positive": sum(1 for v in per.values() if v["sum"] > 0), "n_years": len(per)}


def year_concentration(sessions, gross, scale=None, *, cap: float = CAP) -> dict:
    """Per-year shares of a line's P&L in its own unit and, with `scale`, in units of its pre-trade volatility.

    sessions: ISO dates ("YYYY-MM-DD"), one per trade. gross: per-trade P&L. scale: per-trade volatility in gross's
    unit, finite and > 0, known before the trade. Informational only (D729)."""
    s = np.asarray(sessions, dtype=str)
    g = np.asarray(gross, dtype=float)
    if s.ndim != 1 or g.shape != s.shape or len(s) == 0:
        raise ValueError(f"sessions and gross must be 1-D and the same non-zero length, got {s.shape} and {g.shape}")
    bad = [x for x in s if not _ISO.match(x)]
    if bad:
        raise ValueError(f"not an ISO session: {bad[0]!r}")
    if not np.isfinite(g).all():
        raise ValueError("gross holds a non-finite value")
    if not 0 < cap < 1:
        raise ValueError(f"cap must lie in (0, 1), got {cap}")
    years = np.array([x[:4] for x in s])
    per_g = _by_year(years, g)
    out = {"cap": cap, "informational": True, "n": int(len(g)),
           "gross": {"by_year": per_g, **_summary(per_g, float(g.sum()))}}
    if scale is None:
        sg = out["gross"]
        out["label"] = ("UNDEFINED" if sg["max_share"] is None
                        else "CONCENTRATED" if sg["max_share"] > cap else "NOT CONCENTRATED")
        return out
    sc = np.asarray(scale, dtype=float)
    if sc.shape != g.shape:
        raise ValueError(f"scale must match gross's shape {g.shape}, got {sc.shape}")
    if not (np.isfinite(sc).all() and (sc > 0).all()):
        raise ValueError("scale must be finite and > 0 on every trade")
    u = g / sc
    per_u = _by_year(years, u)
    out["vol_units"] = {"by_year": per_u, **_summary(per_u, float(u.sum()))}
    a, b = out["gross"]["max_share"], out["vol_units"]["max_share"]
    if a is None or b is None:
        lab = "UNDEFINED"
    elif a > cap and b > cap:
        lab = "BOTH"
    elif a > cap:
        lab = "SCALE-CARRIED"
    elif b > cap:
        lab = "VOL-ONLY"
    else:
        lab = "NEITHER"
    out["label"] = lab
    return out
