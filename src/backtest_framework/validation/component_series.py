"""A component's daily P&L series, on disk, with its provenance — D590.

`docs/COMPONENTS_PROP.md` scores a component on its *daily* P&L in dollars at the
instrument's minimum tradable size. Three rows of that ledger say **"ρ not computable —
the arm's daily P&L is not on disk"** (entry #3, D555, D558). `scripts/run_d466_components.py`
is the reason: it rebuilds every series from its own fixtures, scores it, and writes
**summaries only**. C-b is a pairwise statistic, so a summary can never satisfy it; the
next record to score a construction against an earlier one has nothing to correlate with.

This module is the missing artefact. `DailyPnL` is the series plus the five things a
reader needs to know whether two series are comparable at all — the size it was traded
at, the cost line that size pays, the window, the record that produced it, and the
sha256 of the input it was derived from. `write` puts it under `data/components/` as a
CSV a human can read and a sidecar `.meta.json`; `read` returns an object equal to the
one written.

**Nothing here computes a strategy return.** It stores one that a runner already
computed, and scores it against the ledger's bars with the *same* estimator
`run_d466_components.py` used — `tests/unit/test_component_series.py` asserts that
equality by importing that script, because a component line computed by a second
estimator is the error D466 was written to prevent (CLAUDE.md, "a component number
computed outside the runner").

UNITS. Every P&L number in this module is **US dollars per session at the stated size**,
never a fraction, never basis points, never points. `account` is dollars. The one
dimensionless output is `sigma_pct_account`.

R17. Every Sharpe here carries a Sortino beside it; `component_line` refuses to return
one without the other.

Conventions, all declared so the golden test can be hand-computed:

  sharpe(x)   = mean(x) / std(x, ddof=1) * sqrt(252)          — d466's, over ALL days
  sortino(x)  = mean(x) / sqrt(sum(min(x,0)^2) / (n-1)) * sqrt(252)
                (ddof=1 denominator, so the two share a divisor and are comparable)
  skew(x)     = pandas' adjusted Fisher-Pearson sample skew    — d466's C-c statistic
  sharpe_boot = monthly block bootstrap, 1,000 draws, seed 7   — d466's, verbatim
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = [
    "Bars",
    "DailyPnL",
    "LEDGER_BARS",
    "align",
    "component_line",
    "correlation_matrix",
    "default_dir",
    "read",
    "sha256_of",
    "sharpe",
    "sharpe_boot",
    "sortino",
]

TRADING_DAYS = 252
ACCOUNT_DEFAULT = 50_000.0

_DATE_LEN = 10
_REPO = Path(__file__).resolve().parents[3]


def default_dir() -> Path:
    """`<repo>/data/components` — the convention this module establishes."""
    return _REPO / "data" / "components"


# --------------------------------------------------------------------------- the bars


@dataclass(frozen=True)
class Bars:
    """`docs/COMPONENTS_PROP.md`'s admission standard, as numbers.

    Defaults are D466's committed values (`BAR_SHARPE`, `BAR_RHO`, `BAR_SKEW`,
    `BAR_SIGMA = 0.01 * ACCOUNT`). C-e (provenance) is not a number: it is discharged by
    `DailyPnL`'s `spec`, `window`, `cost_line_usd_rt` and `source_sha256` being present.
    """

    sharpe: float = 0.5
    rho: float = 0.3
    skew: float = -0.5
    sigma: float = 500.0


LEDGER_BARS = Bars()


# --------------------------------------------------------------------------- estimators


def sharpe(x: Sequence[float] | np.ndarray) -> float:
    """Annualised Sharpe over ALL calendar days. Identical to `run_d466_components.sharpe`."""
    a = np.asarray(x, dtype=float)
    s = a.std(ddof=1)
    return float(a.mean() / s * math.sqrt(TRADING_DAYS)) if s > 0 else float("nan")


def sortino(x: Sequence[float] | np.ndarray) -> float:
    """Annualised Sortino at MAR = 0, ddof=1 downside deviation (R17).

    `downside = sqrt(sum(min(x, 0)^2) / (n - 1))`. The ddof=1 divisor is deliberate: it
    is the one `sharpe` uses, so the pair differ only in which deviations are counted.
    """
    a = np.asarray(x, dtype=float)
    if a.size < 2:
        raise ValueError(f"sortino needs at least 2 sessions, got {a.size}")
    neg = np.minimum(a, 0.0)
    down = math.sqrt(float((neg * neg).sum()) / (a.size - 1))
    return float(a.mean() / down * math.sqrt(TRADING_DAYS)) if down > 0 else float("nan")


def sharpe_boot(x: Sequence[float] | np.ndarray, dates: Sequence[str],
                n_boot: int = 1000, seed: int = 7) -> float:
    """Monthly block-bootstrap SE of `sharpe`. Verbatim `run_d466_components.sharpe_boot`."""
    a = np.asarray(x, dtype=float)
    if len(dates) != a.size:
        raise ValueError(f"{len(dates)} dates against {a.size} sessions")
    mon = np.array([str(d)[:7] for d in dates])
    keys, inv = np.unique(mon, return_inverse=True)
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    groups = [a[inv == k] for k in range(keys.size)]
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size)
        out[b] = sharpe(np.concatenate([groups[k] for k in pick]))
    return float(np.nanstd(out, ddof=1))


def sha256_of(path: str | Path) -> str:
    """sha256 of a file's BYTES, for `DailyPnL.source_sha256`."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- the artefact


@dataclass(frozen=True)
class DailyPnL:
    """One component's daily P&L in dollars, with everything C-e asks for.

    name              file-safe identifier, also the column name in `align`
    dates             ISO `YYYY-MM-DD`, strictly increasing
    usd               dollars that session at `size_label`; 0.0 on a flat day
    size_label        the traded size, e.g. "1 MNQ" — a series without one is unscoreable
    cost_line_usd_rt  the round-trip cost in dollars that size pays (e.g. 3.0)
    window            (first, last) the SERIES claims to cover; must contain every date
    spec              the record that produced it, e.g. "D498"
    source_sha256     sha256 of the file the P&L was derived from

    Frozen and validated on construction: a malformed series raises here rather than
    producing a plausible wrong number three functions later (D48).
    """

    name: str
    dates: tuple[str, ...]
    usd: tuple[float, ...]
    size_label: str
    cost_line_usd_rt: float
    window: tuple[str, str]
    spec: str
    source_sha256: str

    def __post_init__(self) -> None:
        if not self.name or any(c in self.name for c in ' /\\:*?"<>|'):
            raise ValueError(f"name {self.name!r} is empty or not file-safe")
        if len(self.dates) != len(self.usd):
            raise ValueError(f"{len(self.dates)} dates against {len(self.usd)} values")
        if len(self.dates) < 2:
            raise ValueError(f"a component series needs at least 2 sessions, got {len(self.dates)}")
        for d in self.dates:
            if len(d) != _DATE_LEN or d[4] != "-" or d[7] != "-":
                raise ValueError(f"date {d!r} is not ISO YYYY-MM-DD")
        if any(b <= a for a, b in zip(self.dates, self.dates[1:])):
            raise ValueError("dates must be strictly increasing (a duplicated session "
                             "double-counts its P&L in every statistic below)")
        arr = np.asarray(self.usd, dtype=float)
        if not np.isfinite(arr).all():
            bad = int(np.flatnonzero(~np.isfinite(arr))[0])
            raise ValueError(f"usd[{bad}] = {self.usd[bad]!r} is not finite")
        if not (self.cost_line_usd_rt >= 0.0) or not math.isfinite(self.cost_line_usd_rt):
            raise ValueError(f"cost_line_usd_rt {self.cost_line_usd_rt!r} must be >= 0 and finite")
        if len(self.window) != 2 or self.window[0] > self.window[1]:
            raise ValueError(f"window {self.window!r} is not (first, last)")
        if self.dates[0] < self.window[0] or self.dates[-1] > self.window[1]:
            raise ValueError(f"dates {self.dates[0]}..{self.dates[-1]} fall outside "
                             f"window {self.window[0]}..{self.window[1]}")
        if not self.spec:
            raise ValueError("spec is empty; C-e requires the record that produced the series")
        if len(self.source_sha256) != 64 or any(c not in "0123456789abcdef"
                                                for c in self.source_sha256):
            raise ValueError(f"source_sha256 {self.source_sha256!r} is not 64 lowercase hex")

    # -- derived views ------------------------------------------------------------------

    @property
    def values(self) -> np.ndarray:
        """The dollars as a float array (a copy; the object stays frozen)."""
        return np.asarray(self.usd, dtype=float)

    @property
    def series(self) -> pd.Series:
        """The dollars indexed by ISO date string."""
        return pd.Series(self.values, index=pd.Index(self.dates, name="date"), name=self.name)

    # -- disk ---------------------------------------------------------------------------

    def csv_path(self, directory: str | Path | None = None) -> Path:
        return Path(directory or default_dir()) / f"{self.name}_daily_usd.csv"

    def meta_path(self, directory: str | Path | None = None) -> Path:
        return Path(directory or default_dir()) / f"{self.name}_daily_usd.meta.json"

    def write(self, directory: str | Path | None = None) -> Path:
        """Write `<name>_daily_usd.csv` and its `.meta.json`; return the CSV path.

        The newline is pinned to "\\n" on every platform (D550: the author's OS is not
        the runner's, and a sha256 over CRLF bytes does not match one over LF bytes).
        Values are written with `repr`, which is the shortest string that reads back to
        the same float — so `read(write(x)) == x` exactly, not approximately.
        """
        out = Path(directory or default_dir())
        out.mkdir(parents=True, exist_ok=True)
        csv = self.csv_path(out)
        lines = ["date,usd"]
        # `float(v)` first: under numpy >= 2, `repr(np.float64(1.0))` is
        # "np.float64(1.0)", which `read` cannot parse. Found on integration
        # (2026-09-21) by writing an ndarray-backed series; the tests had only
        # ever passed tuples of Python floats.
        lines += [f"{d},{float(v)!r}" for d, v in zip(self.dates, self.usd)]
        with open(csv, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        meta = {
            "schema": "D590 component daily P&L, dollars per session at size_label",
            "name": self.name,
            "size_label": self.size_label,
            "cost_line_usd_rt": self.cost_line_usd_rt,
            "window": list(self.window),
            "spec": self.spec,
            "source_sha256": self.source_sha256,
            "n_sessions": len(self.dates),
            "first_date": self.dates[0],
            "last_date": self.dates[-1],
            "csv": csv.name,
            "csv_sha256": sha256_of(csv),
        }
        with open(self.meta_path(out), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(meta, indent=1) + "\n")
        return csv

    def to_dict(self) -> dict:
        return asdict(self)


def read(path: str | Path) -> DailyPnL:
    """Read a series written by `DailyPnL.write`. Accepts the CSV path or the meta path.

    Raises when the CSV's bytes no longer hash to what the meta recorded: a silently
    edited series is the one failure this artefact exists to make impossible.
    """
    p = Path(path)
    if p.name.endswith(".meta.json"):
        meta_p = p
        csv_p = p.with_name(p.name[: -len(".meta.json")] + ".csv")
    else:
        csv_p = p
        meta_p = p.with_name(p.name[: -len(".csv")] + ".meta.json")
    if not csv_p.exists():
        raise FileNotFoundError(f"no series CSV at {csv_p}")
    if not meta_p.exists():
        raise FileNotFoundError(f"no sidecar metadata at {meta_p}; the CSV alone cannot "
                                f"satisfy C-e (size, cost line, window, record, provenance)")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    got = sha256_of(csv_p)
    if got != meta["csv_sha256"]:
        raise ValueError(f"{csv_p.name} hashes to {got}, meta records {meta['csv_sha256']}: "
                         f"the series changed after it was written")
    raw = csv_p.read_text(encoding="utf-8").splitlines()
    if not raw or raw[0] != "date,usd":
        raise ValueError(f"{csv_p.name}: expected header 'date,usd', got {raw[:1]!r}")
    dates: list[str] = []
    vals: list[float] = []
    for i, line in enumerate(raw[1:], start=2):
        if not line:
            continue
        d, _, v = line.partition(",")
        if not _:
            raise ValueError(f"{csv_p.name}:{i}: no comma in {line!r}")
        dates.append(d)
        vals.append(float(v))
    if len(dates) != meta["n_sessions"]:
        raise ValueError(f"{csv_p.name} has {len(dates)} rows, meta records "
                         f"{meta['n_sessions']}")
    return DailyPnL(
        name=meta["name"], dates=tuple(dates), usd=tuple(vals),
        size_label=meta["size_label"], cost_line_usd_rt=float(meta["cost_line_usd_rt"]),
        window=(meta["window"][0], meta["window"][1]), spec=meta["spec"],
        source_sha256=meta["source_sha256"],
    )


# --------------------------------------------------------------------------- alignment


def align(*series: DailyPnL, calendar: Iterable[str] | None = None,
          strict: bool = True) -> pd.DataFrame:
    """One column a component, zero on a flat or absent day, on a shared calendar.

    Identical to `run_d466_components.series_on` per column: the frame is zero, and the
    series' own values are written into the rows the calendar carries. `calendar=None`
    takes the sorted union of every series' dates — which is what "the book trades on
    the union of its arms' sessions" means.

    `strict=True` (the default) RAISES when a series holds a session the calendar does
    not, because `series_on` drops those silently and a dropped session is P&L that
    vanishes from the book without appearing anywhere (D48). `strict=False` reproduces
    the drop, for the identity test against `series_on`.
    """
    if not series:
        raise ValueError("align needs at least one series")
    names = [s.name for s in series]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate component names {dupes}: a frame cannot carry two")
    cal = (pd.Index(sorted(set().union(*(set(s.dates) for s in series))), name="date")
           if calendar is None else pd.Index(list(calendar), name="date"))
    if cal.has_duplicates:
        raise ValueError("calendar has duplicate dates")
    if not cal.is_monotonic_increasing:
        raise ValueError("calendar is not sorted ascending")
    cols = {}
    for s in series:
        missing = [d for d in s.dates if d not in set(cal)]
        if missing and strict:
            raise ValueError(f"{s.name}: {len(missing)} session(s) outside the calendar, "
                             f"first {missing[0]} — their P&L would be dropped silently")
        col = pd.Series(0.0, index=cal)
        v = pd.Series(s.values, index=pd.Index(s.dates))
        v = v[v.index.isin(cal)]
        col.loc[v.index] = v.values
        cols[s.name] = col
    return pd.DataFrame(cols, index=cal)


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """C-b's statistic: Pearson ρ of the daily dollars over ALL calendar days (d466's)."""
    if df.shape[1] < 1:
        raise ValueError("correlation_matrix needs at least one column")
    return df.corr()


# --------------------------------------------------------------------------- the line


def component_line(series: DailyPnL, account: float = ACCOUNT_DEFAULT,
                   bars: Bars = LEDGER_BARS, *, n_boot: int = 1000,
                   seed: int = 7) -> dict:
    """C-a..C-d for one series, in the ledger's own estimators. Dollars throughout.

    Returns net AND gross, Sharpe AND Sortino (R17), the three pass flags and the
    numbers behind them. C-b is NOT here: it needs the other components, and
    `correlation_matrix(align(...))` is where it lives.

    `gross_*` assume **one round trip per active day** at `cost_line_usd_rt`. That is a
    convention, not a measurement — a series with two trips a day has a higher gross
    than this reports — and the key names say so.
    """
    if account <= 0:
        raise ValueError(f"account must be a positive dollar amount, got {account!r}")
    x = series.values
    n = x.size
    active = x != 0.0
    n_active = int(active.sum())
    sd = float(x.std(ddof=1))
    net_sharpe = sharpe(x)
    gross = x + np.where(active, series.cost_line_usd_rt, 0.0)
    return {
        "name": series.name,
        "spec": series.spec,
        "window": list(series.window),
        "size_label": series.size_label,
        "cost_line_usd_rt": series.cost_line_usd_rt,
        "account_usd": float(account),
        "n_sessions": int(n),
        "active_days": n_active,
        "exposure": float(active.mean()),
        "net_sharpe": net_sharpe,
        "net_sharpe_se": sharpe_boot(x, series.dates, n_boot=n_boot, seed=seed),
        "net_sortino": sortino(x),
        "gross_sharpe_one_rt_per_active_day": sharpe(gross),
        "gross_sortino_one_rt_per_active_day": sortino(gross),
        "mean_usd": float(x.mean()),
        "median_usd": float(np.median(x)),
        "sd_usd": sd,
        "ann_usd": float(x.mean() * TRADING_DAYS),
        "hit_active": float((x[active] > 0).mean()) if n_active else float("nan"),
        "skew": float(pd.Series(x).skew()),
        "worst_day_usd": float(x.min()),
        "best_day_usd": float(x.max()),
        "sigma_pct_account": sd / float(account) * 100.0,
        "cost_usd_total_one_rt_per_active_day": float(series.cost_line_usd_rt * n_active),
        "bar_sharpe": bars.sharpe,
        "bar_skew": bars.skew,
        "bar_sigma_usd": bars.sigma,
        "bar_rho": bars.rho,
        "C_a_pass": bool(net_sharpe > bars.sharpe),
        "C_c_pass": bool(float(pd.Series(x).skew()) >= bars.skew),
        "C_d_pass": bool(sd <= bars.sigma),
        "C_b_note": "not computable from one series; use correlation_matrix(align(...))",
        "C_e_provenance": f"{series.spec}; {series.window[0]}..{series.window[1]}; "
                          f"{series.size_label}; ${series.cost_line_usd_rt:.2f} RT; "
                          f"source sha256 {series.source_sha256[:12]}",
    }
