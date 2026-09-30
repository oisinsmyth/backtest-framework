"""D723: NG Stage A (D630's H2) for the joint vault run, programme slot 3. D723 registers it (the principal,
2026-09-30: "Do the write up and freeze"); this file scores it. D630 s.8 names the freeze this file writes.

    uv run python scripts/vault_d723_ng_stage_a.py --selftest          # synthetic only, reads no market data
    uv run python scripts/vault_d723_ng_stage_a.py --known-answer      # in-sample only (< 2025-03-01)
    uv run python scripts/vault_d723_ng_stage_a.py --freeze            # ONCE, after the NG input path is final
    uv run python scripts/vault_d723_ng_stage_a.py --vault --trade-table data/joint_run/ng/d630_trade_table.csv \\
        --principals-word "..."                                          # the joint run ONLY

THE CONSTRUCTION is D630's, frozen in data/FROZEN_ledger_stage_a_ng.json and unchanged: side sign(Q_rem) at t0, fill
at the close of bar t0+1, exit at the close of 14:29, one full-size NG at $26 a trade ($16 + one $10 tick).

THE KNOWN ANSWER (n 1,028, mean g $66.0214007782101, both EXACT) comes from D630's OWN PATH:
`run_h2_ng_stage_a.build(read_returns=True)` + `signed`, on the frozen in-sample fixtures, each checked byte for byte
against the Stage A freeze before it is read, and turned into the trade table exactly as
`build_ledger_vault_inputs.build_panels` writes it (day, traded & finite g, absI_usd, g with 0 where not finite). It
is the cheapest EXACT route that does not depend on `temp/` (the `--prove panels` table lives in a deletable scratch
dir): one pass over the in-sample bars, about 20 seconds. Where the gitignored fixtures are absent (a worktree) they
are read from the main checkout's data/ (the explore_d630_exits_micro convention).

THE PASS RULE (D723 s.2 = D630 s.8 = deposit line 902), on the vault's traded days 2025-03-01 -> 2026-09-18:
  1. mean g > 0 (the in-sample sign);
  2. one-sided t >= 1.2816, t = Newey-West with 5 lags over the trade sequence: D630's `nw_t` (statsmodels OLS on a
     constant, HAC, maxlags 5), imported from the frozen runner and never re-implemented;
  3. mean net at 1x cost ($26 a trade) > 0.
  Fewer than 15 vault traded days: UNRESOLVED. A failure is "FAIL (not promoted)", no re-tuning.
  NOTE for the principal: D630's REGISTERED gate t was the ordinary SE t (5.01 in-sample); the NW(5) t (4.55) was
  reported beside it. D723 s.2 names Newey-West, so NW(5) gates here (GATE_T); the ordinary t is reported beside.

REPORTED BESIDE, NEVER GATING (D723 s.3): the MNG line (one MNG; the cost from data/futures_costs.json
roots.NG.micro: commission_rt $3 + the default crossing line d556_one_tick x $1 + one $1 tick of entry slippage
(D630 s.7) = $5, asserted equal to D630's MNG_COST and D649's); full-size net and gross Sharpe and Sortino (D630's
`performance`: daily over the vault table's calendar, 0 on untraded days, sqrt 252); the trade distribution with
symmetric 1% trims; by year (2025 against 2026); the 11:30 placebo and the rotation p50/p95 (+- SE) on the vault days,
both D630's own functions run on D630's own frame rebuilt from the vault panels beside the trade table (the table
carries only day, traded, absI_usd, g, so the placebo and rotation need the panels); rho with D649's vault book (D649's
own `select` on the same table, checked against its output file when that exists).

THE IN-SAMPLE RE-PROOF in --vault: D630's path on the frozen in-sample fixtures reproduces the known answer exactly;
then the trade table's own in-sample rows must be identical to it, row for row, through 2024-12-31 (A6's last
in-sample anchor). The rows 2025-01-01 -> 2025-02-28 CAN move under the vault's later fut-share anchors (the builder
says so and permits it); if they do, the table's in-sample n / mean no longer reproduce 1,028 / $66.0214007782101 and
--vault REFUSES unless --accept-a6-tail-moves is passed, which the principal decides (it is recorded in the output).

FREEZE (data/ledger_frozen_vault_h2_ng.json, written once): the LF-pinned sha256 of this runner, of D723, of D630's
pre-registration and result, of scripts/build_ledger_vault_inputs.py and of every repo module it and this runner
import (discovered statically, recursively, from their `_load("...")`, `spec_from_file_location("...")` and
backtest_framework imports; the modules actually imported are checked to be a subset), the Stage A freeze's own
bytes sha256, the parameters, the retained stage A, the known answer, programme slot 3 and the principal's word.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

RUNNER_REL = "scripts/vault_d723_ng_stage_a.py"
SPEC_REL = "docs/decisions/D723-PRE-REG-ng-stage-a-for-the-joint-vault.md"
D630_PRE_REL = "docs/decisions/D630-PRE-REG-h2-ng-the-settlement-move-in-the-funds-direction.md"
D630_RES_REL = "docs/decisions/D630-RESULT-h2-ng-passes-and-the-move-reverts-after-the-settlement.md"
BUILDER_REL = "scripts/build_ledger_vault_inputs.py"
STAGE_A_REL = "data/FROZEN_ledger_stage_a_ng.json"
FROZEN = REPO / "data" / "ledger_frozen_vault_h2_ng.json"
OUT = REPO / "data" / "vault_d723_ng_stage_a.json"
D649_OUT = REPO / "data" / "ledger_vault_pp_ng_vault.json"
PUBLISHED = REPO / "data" / "ledger_h2_ng_stage_a.json"
COSTS = REPO / "data" / "futures_costs.json"
VERIFY_A = REPO / "scripts" / "verify_ledger_stage_a_ng.py"

CUT_IN, A6_ANCHOR_IN = "2025-03-01", "2024-12-31"
VAULT_FROM, VAULT_END, SEAL = "2025-03-01", "2026-09-18", "2026-09-19"
KNOWN = {"n": 1028, "gate_mean": 66.0214007782101}
COST_FULL, T_ONE_SIDED, NW_LAGS, MIN_DAYS, GATE_T = 26.0, 1.2816, 5, 15, "nw5"
ROT_SEED, ROT_DRAWS = 630, 1000
PROGRAMME_SLOT, RETAINED_STAGE = 3, "A"
INSTRUCTION = 'the principal, 2026-09-30: "Do the write up and freeze"'
TABLE_COLS = ["day", "traded", "absI_usd", "g"]
# the frozen in-sample inputs D630's build reads, by the attribute that holds each path
IN_FILES = {("R", "FLOW"): "ledger_predicted_flow_daily.csv.gz", ("R", "BARS"): "ng_minute_bars.csv.gz",
            ("R", "PANEL"): "ledger_window_volume_daily.csv.gz", ("R", "CAL"): "ledger_calendar_flags.csv",
            ("H", "FLOW"): "ledger_predicted_flow_daily.csv.gz", ("H", "PANEL"): "ledger_window_volume_daily.csv.gz",
            ("H", "FSHARE"): "ledger_fut_share_daily_a6.csv.gz", ("H", "CAL"): "ledger_calendar_flags.csv"}
REFUSED = 2


class VaultError(RuntimeError):
    pass


class SealError(VaultError):
    pass


# ================================================================================ modules, hashing, discovery
def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    import importlib.util
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def _R() -> Any:
    return _load("run_h2_ng_stage_a")


def _H() -> Any:
    _R()
    return sys.modules["run_h1a_stage_a"]


def _P649() -> Any:
    return _load("ledger_vault_pp_ng")


@contextlib.contextmanager
def held(pairs: list[tuple[Any, str, Any]]) -> Iterator[None]:
    """Hold module globals for the body; every old value is put back whatever happens."""
    old = [(m, n, getattr(m, n)) for m, n, _ in pairs]
    try:
        for m, n, v in pairs:
            setattr(m, n, v)
        yield
    finally:
        for m, n, v in reversed(old):
            setattr(m, n, v)


def sha_text(p: Path) -> str:
    """LF-pinned (as the Stage A freeze and D649/D680), so a checkout's line endings cannot fake a drift."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha_bytes(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


_LOADS = (re.compile(r'_load(?:_mod)?\(\s*"([A-Za-z0-9_]+)"'),
          re.compile(r'spec_from_file_location\(\s*"([A-Za-z0-9_]+)"'))
_NAMES = r"(\([\w\s,]+\)|[\w ,]+)"  # one line, or a parenthesised list that may span lines
_BF = re.compile(r"^[ \t]*(?:from[ \t]+(backtest_framework[\w.]*)[ \t]+import[ \t]+" + _NAMES +
                 r"|import[ \t]+(backtest_framework[\w.]*))", re.M)
_REL = re.compile(r"^[ \t]*from[ \t]+(\.+)([\w.]*)[ \t]+import[ \t]+" + _NAMES, re.M)
_TOP = re.compile(r"^(?:import|from)[ \t]+([A-Za-z_]\w*)", re.M)


def _names(s: str) -> list[str]:
    return [x.strip().split(" as ")[0].strip() for x in s.replace("(", " ").replace(")", " ").split(",") if x.strip()]


def _src_file(root: Path, dotted: str) -> str | None:
    base = root / "src" / Path(*dotted.split("."))
    for p in (base.with_suffix(".py"), base / "__init__.py"):
        if p.exists():
            return p.relative_to(root).as_posix()
    return None


def discover(root: Path, starts: tuple[str, ...]) -> list[str]:
    """Every repo module the start files import, recursively (static: text patterns, never executed), with the
    package __init__ files a src import runs. The start files themselves are not listed."""
    seen: set[str] = set()
    stack = list(starts)
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        text = (root / rel).read_text(encoding="utf-8")
        found: list[str] = []
        for pat in _LOADS:
            found += [f"scripts/{n}.py" for n in pat.findall(text)]
        found += [f"scripts/{n}.py" for n in _TOP.findall(text)]
        mods: list[str] = []
        for frm, names, imp in _BF.findall(text):
            if imp:
                mods.append(imp)
            else:
                mods.append(frm)
                mods += [f"{frm}.{x}" for x in _names(names)]
        if rel.startswith("src/"):
            pkg = Path(rel).parent.relative_to("src").as_posix().replace("/", ".")
            for dots, sub, names in _REL.findall(text):
                base = ".".join(pkg.split(".")[: len(pkg.split(".")) - (len(dots) - 1)])
                frm = f"{base}.{sub}" if sub else base
                mods.append(frm)
                mods += [f"{frm}.{x}" for x in _names(names)]
        for m in mods:
            parts = m.split(".")
            for k in range(1, len(parts) + 1):
                f = _src_file(root, ".".join(parts[:k]))
                if f:
                    found.append(f)
        stack += [f for f in found if (root / f).exists() and f not in seen]
    return sorted(seen - set(starts))


def imported_repo_files(root: Path) -> set[str]:
    """The repo files this process has actually imported (the dynamic side of the discovery check)."""
    out = set()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        try:
            rel = Path(f).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        if rel.startswith(("scripts/", "src/")) and rel.endswith(".py"):
            out.add(rel)
    return out


def import_builder_chain() -> None:
    """Import the NG input path the way its own selftest does (no data is read) so the dynamic check sees it."""
    B = _load("build_ledger_vault_inputs")
    B.modules()
    for n in ("build_window_volume_panel", "build_ng_minute_bars", "ledger_vault_pp_ng"):
        _load(n)


def params() -> dict[str, Any]:
    return {"vault": [VAULT_FROM, VAULT_END], "seal_from": SEAL, "in_sample_cut": CUT_IN,
            "a6_last_in_sample_anchor": A6_ANCHOR_IN, "cost_full_usd": COST_FULL,
            "pass_rule": {"1": "vault mean g > 0 (the in-sample sign)",
                          "2": f"one-sided t >= {T_ONE_SIDED}, t = Newey-West, {NW_LAGS} lags (D630 nw_t)",
                          "3": f"vault mean net at ${COST_FULL:g} a trade > 0",
                          "floor": f"fewer than {MIN_DAYS} vault traded days -> UNRESOLVED"},
            "t_one_sided": T_ONE_SIDED, "nw_lags": NW_LAGS, "gate_t": GATE_T, "min_vault_traded_days": MIN_DAYS,
            "rotation": {"seed": ROT_SEED, "draws": ROT_DRAWS, "form": "D630 C2 on the vault days (reported)"},
            "placebo": "D630 C1: the 11:30 ledger, 11:31 fill to the 12:19 close, on the vault days (reported)",
            "mng_cost": "futures_costs.json NG.micro: commission_rt + default crossing x tick + 1 tick slippage",
            "vault_a6_anchors_accepted": {"LAST_ANCHOR": "2026-06-30", "SWAP_Q_LAST": "2026-Q2"}}


def manifest(root: Path, known: dict[str, Any] | None) -> dict[str, Any]:
    imported = discover(root, (BUILDER_REL, RUNNER_REL))
    return {"name": "ledger_frozen_vault_h2_ng", "record": SPEC_REL, "programme_slot": PROGRAMME_SLOT,
            "retained_stage": RETAINED_STAGE, "instruction": INSTRUCTION,
            "runner": {"path": RUNNER_REL, "sha256": sha_text(root / RUNNER_REL)},
            "records": {p: sha_text(root / p) for p in (SPEC_REL, D630_PRE_REL, D630_RES_REL)},
            "builder": {"path": BUILDER_REL, "sha256": sha_text(root / BUILDER_REL)},
            "imported_unchanged": {p: sha_text(root / p) for p in imported},
            "stage_a_freeze": {"path": STAGE_A_REL, "sha256_bytes": sha_bytes(root / STAGE_A_REL)},
            "params": params(), "known_answer": known}


def check_freeze(doc: dict[str, Any], root: Path) -> None:
    """Every hash the freeze holds, recomputed; the import set re-discovered. Raises on any drift."""
    now = manifest(root, doc.get("known_answer"))
    bad = []
    for k in ("runner", "builder"):
        if now[k] != doc.get(k):
            bad.append(f"{k} {now[k]['path']}")
    for p, h in doc.get("records", {}).items():
        if now["records"].get(p) != h:
            bad.append(f"record {p}")
    if set(now["records"]) != set(doc.get("records", {})):
        bad.append("the record set")
    fi, ni = doc.get("imported_unchanged", {}), now["imported_unchanged"]
    if set(fi) != set(ni):
        bad.append(f"the import set (added {sorted(set(ni) - set(fi))}, dropped {sorted(set(fi) - set(ni))})")
    bad += [f"imported {p}" for p in sorted(set(fi) & set(ni)) if fi[p] != ni[p]]
    if now["stage_a_freeze"] != doc.get("stage_a_freeze"):
        bad.append("the Stage A freeze file")
    if now["params"] != doc.get("params"):
        bad.append("the parameters")
    if bad:
        raise VaultError(f"moved since the freeze: {bad}")


# ================================================================================ money, the pass rule
def mng_cost_line() -> dict[str, Any]:
    """One MNG round trip from the repo cost table, plus D630 s.7's one tick of entry slippage."""
    j = json.loads(COSTS.read_text(encoding="utf-8"))
    m, f = j["roots"]["NG"]["micro"], j["roots"]["NG"]["full"]
    line = m["default_line"]
    comm = float(m["commission_rt_usd"]["value"])
    cross = float(m["crossing_ticks_rt"][line]["value"]) * float(m["tick_usd"])
    slip = float(m["tick_usd"])
    ratio = float(m["usd_per_point"]) / float(f["usd_per_point"])
    R = _R()
    if not (math.isclose(comm + cross + slip, R.MNG_COST) and math.isclose(comm + cross + slip, _P649().MNG_COST)
            and math.isclose(ratio, R.MNG_MULT / R.MULT)):
        raise VaultError(f"the cost table's MNG line (${comm + cross + slip}, ratio {ratio}) is not D630's / D649's")
    return {"symbol": m["symbol"], "source": "data/futures_costs.json roots.NG.micro", "commission_rt_usd": comm,
            "crossing_line": line, "crossing_usd": cross, "entry_slippage_usd": slip, "cost_usd": comm + cross + slip,
            "mng_over_ng": ratio}


def audit_money(net: Callable[[float], float], mng_net: Callable[[float], float]) -> None:
    """A $0.010 rise after a buy is +$100 gross at full size (D630's money), +$74 net; +$10 gross and +$5 net at
    one MNG; the same rise after a sell is -$100."""
    R = _R()
    g_buy, g_sell = R.money(1, 2.0, 2.01), R.money(-1, 2.0, 2.01)
    if not (math.isclose(g_buy, 100.0) and math.isclose(g_sell, -100.0) and math.isclose(net(g_buy), 74.0)
            and math.isclose(mng_net(g_buy), 5.0)):
        raise VaultError("sign audit: the money does not pay the traded way")


def full_net(g: Any) -> Any:
    return g - COST_FULL


def mng_gross(g: Any) -> Any:
    return g * _R().MNG_MULT / _R().MULT  # D630's own order of operations (bit-exact with its component line)


def pass_rule(g: np.ndarray, nw: Callable[[np.ndarray, int], float] | None = None) -> dict[str, Any]:
    """D723 s.2 on the vault's traded days (one trade per day), g in gross dollars per full contract."""
    g = np.asarray(g, float)
    if not np.isfinite(g).all():
        raise VaultError("a traded vault day has no finite g")
    nw = nw or _R().nw_t
    n = len(g)
    out: dict[str, Any] = {"n_traded_days": n}
    if n >= 2:
        sd = float(g.std(ddof=1))
        se = sd / math.sqrt(n)
        mean = float(g.mean())
        if sd > 0:
            t_plain, t_nw = mean / se, float(nw(g, NW_LAGS))
        else:
            t_plain = t_nw = 0.0 if mean == 0 else math.copysign(math.inf, mean)
        from scipy import stats
        out.update({"mean_g": mean, "se": se, "t_ordinary": t_plain, "t_nw5": t_nw,
                    "t_gate": t_nw if GATE_T == "nw5" else t_plain, "p_one_sided_nw5": float(stats.norm.sf(t_nw)),
                    "mean_net": mean - COST_FULL})
    if n < MIN_DAYS:
        out["verdict"] = "UNRESOLVED"
        out["why"] = f"{n} vault traded days, fewer than {MIN_DAYS} (D723 s.2 floor)"
        return out
    parts = {"1_mean_g_positive": bool(out["mean_g"] > 0),
             "2_one_sided_t_nw5_ge_1.2816": bool(out["t_gate"] >= T_ONE_SIDED),
             "3_mean_net_at_26_positive": bool(out["mean_net"] > 0)}
    out["parts"] = parts
    out["verdict"] = "PASS" if all(parts.values()) else "FAIL (not promoted)"
    return out


# ================================================================================ tables
def to_table(d: pd.DataFrame) -> pd.DataFrame:
    """D630's frame -> the trade table, exactly as build_ledger_vault_inputs.build_panels writes it."""
    g = _R().signed(d)
    return pd.DataFrame({"day": d["day"].to_numpy(), "traded": d["traded"].to_numpy() & np.isfinite(g),
                         "absI_usd": d["absI_usd"].to_numpy(float), "g": np.where(np.isfinite(g), g, 0.0)})


def check_days(days: Any, lo: str | None = None, hi: str = VAULT_END) -> None:
    for x in days:
        if len(x) != 10 or x[4] != "-" or x[7] != "-":
            raise VaultError(f"not an ISO day: {x!r}")
        if x >= SEAL:
            raise SealError(f"a session dated {x} (D626's seal: nothing for NG dated {SEAL} or later)")
        if x > hi or (lo is not None and x < lo):
            raise VaultError(f"a session dated {x} outside {lo} -> {hi}")


def read_table(path: Path) -> pd.DataFrame:
    """The trade table, read as text first: every day field is checked against the seal before any value is
    converted, so no row dated 2026-09-19 or later is ever parsed."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0] != TABLE_COLS:
        raise VaultError(f"{path.name}: header {rows[:1]}, not {TABLE_COLS}")
    check_days([r[0] for r in rows[1:]])
    bad = [r for r in rows[1:] if len(r) != 4 or r[1] not in ("True", "False")]
    if bad:
        raise VaultError(f"{path.name}: malformed rows, first {bad[0]}")
    t = pd.DataFrame({"day": [r[0] for r in rows[1:]], "traded": [r[1] == "True" for r in rows[1:]],
                      "absI_usd": [float(r[2]) for r in rows[1:]], "g": [float(r[3]) for r in rows[1:]]})
    if not t["day"].is_monotonic_increasing or t["day"].duplicated().any():
        raise VaultError(f"{path.name}: days are not unique and increasing")
    return t


def answer(tab: pd.DataFrame, upto: str | None = None) -> dict[str, Any]:
    t = tab if upto is None else tab[tab["day"] <= upto]
    g = t.loc[t["traded"], "g"].to_numpy(float)
    return {"n": int(len(g)), "gate_mean": float(g.mean()) if len(g) else float("nan"),
            "sum_g": float(g.sum()), "first": str(t["day"].min()), "last": str(t["day"].max())}


def check_known(got: dict[str, Any]) -> None:
    if got["n"] != KNOWN["n"] or got["gate_mean"] != KNOWN["gate_mean"]:
        raise VaultError(f"known answer: n {got['n']}, mean g {got['gate_mean']!r}; D630/D723 say {KNOWN}")


def same_rows(a: pd.DataFrame, b: pd.DataFrame) -> list[str]:
    """Days whose (traded, absI_usd, g) differ, or that only one side has. Exact equality."""
    j = a.merge(b, on="day", how="outer", suffixes=("", "_b"), indicator=True)
    diff = ((j["_merge"] != "both") | (j["traded"] != j["traded_b"]) | (j["absI_usd"] != j["absI_usd_b"])
            | (j["g"] != j["g_b"]))
    return sorted(j.loc[diff, "day"].astype(str))


def data_path(name: str, root: Path | None) -> Path:
    if root is not None:
        return root / name
    p = REPO / "data" / name
    if p.exists():
        return p
    q = REPO
    while q.parent != q:  # a worktree reads the gitignored fixtures from the main checkout
        if q.name == "worktrees" and q.parent.name == ".claude":
            return q.parent.parent / "data" / name
        q = q.parent
    return p


def in_sample(root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """D630's own path on the frozen in-sample fixtures, each checked against the Stage A freeze first."""
    R, H = _R(), _H()
    frozen = {Path(f["path"]).name: f["sha256"]
              for f in json.loads((REPO / STAGE_A_REL).read_text(encoding="utf-8"))["fixtures"]}
    paths = {k: data_path(v, root) for k, v in IN_FILES.items()}
    for p in sorted(set(paths.values())):
        if sha_bytes(p) != frozen[p.name]:
            raise VaultError(f"{p}: not the Stage A freeze's {p.name}")
    if (R.CUT, H.CUT) != (CUT_IN, CUT_IN):
        raise VaultError(f"D630's cut is {R.CUT} / {H.CUT}, not {CUT_IN}")
    mods = {"R": R, "H": H}
    with held([(mods[m], a, p) for (m, a), p in paths.items()]):
        d = R.build(read_returns=True)["d"]
    if (d["day"] >= CUT_IN).any():
        raise VaultError("an in-sample frame holds a day on or after the cut")
    return to_table(d), d


def mng_line(traded: np.ndarray, g: np.ndarray, cost: float) -> dict[str, Any]:
    """D630's component block (run_h2_ng_stage_a.analyse), on a table: daily series over every row, 0 untraded."""
    from backtest_framework.validation import component_series as C
    ok = np.asarray(traded, bool)
    g = np.asarray(g, float)
    gm = mng_gross(g[ok])
    dm = np.where(ok, mng_gross(g) - cost, 0.0)
    dg = np.where(ok, mng_gross(g), 0.0)
    return {"contract": "MNG, 1,000 MMBtu", "cost_usd": cost, "trades": int(ok.sum()), "days": int(len(ok)),
            "mean_gross": float(gm.mean()), "mean_net": float(gm.mean() - cost), "sharpe_net": C.sharpe(dm),
            "sortino_net": C.sortino(dm), "sharpe_gross": C.sharpe(dg), "sortino_gross": C.sortino(dg),
            "hit_rate_net": float((gm - cost > 0).mean()), "skew_daily_net": float(pd.Series(dm).skew()),
            "_daily_net": dm}


def rehearse(tab: pd.DataFrame, d: pd.DataFrame, cost_mng: float) -> dict[str, Any]:
    """The --vault reporting code (`beside`, `audit_frame`) run on the IN-SAMPLE table and frame: its placebo, rotation,
    performance and distribution must equal D630's published ones exactly (same functions, seed and draw order)."""
    audit_frame(tab, d)
    reh = beside(tab, d, None, cost_mng, None)
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))["NG"]
    pairs = {"placebo": (reh["placebo_1130"], pub["placebo"], ("mean", "n", "se", "t")),
             "rotation": (reh["rotation"], pub["rotation"], ("p50", "p95", "p95_se")),
             "performance": (reh["performance_full_size"], pub["performance"], tuple(pub["performance"])),
             "distribution_gross": (reh["distribution"]["gross"], pub["distribution"]["gross"],
                                    tuple(pub["distribution"]["gross"])),
             "mng_line": (reh["mng_line"], pub["component_mng"], ("mean_net", "sharpe_net", "sortino_net"))}
    res: dict[str, Any] = {}
    for name, (got, want, keys) in pairs.items():
        diff = {k: float(got[k]) - float(want[k]) for k in keys}
        res[name] = {"exact": all(v == 0 for v in diff.values()), "max_abs_diff": max(abs(v) for v in diff.values())}
        if not all(math.isclose(float(got[k]), float(want[k]), rel_tol=1e-12, abs_tol=1e-12) for k in keys):
            raise VaultError(f"rehearsal: {name} does not reproduce D630's published values: {diff}")
    res["rotation_observed_t"] = reh["rotation"]["t_observed_ordinary"]
    return res


def known_answer(root: Path | None = None) -> dict[str, Any]:
    t0 = time.time()
    tab, _d = in_sample(root)
    got = answer(tab)
    check_known(got)
    cl = mng_cost_line()
    mng = mng_line(tab["traded"].to_numpy(), tab["g"].to_numpy(), cl["cost_usd"])
    mng.pop("_daily_net")
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))["NG"]["component_mng"]
    keys = ("mean_gross", "mean_net", "sharpe_net", "sortino_net", "sharpe_gross", "sortino_gross", "hit_rate_net",
            "skew_daily_net")
    diffs = {k: mng[k] - pub[k] for k in keys}
    if any(not math.isclose(mng[k], pub[k], rel_tol=1e-12, abs_tol=1e-12) for k in keys):
        raise VaultError(f"the in-sample MNG line does not reproduce D630's component_mng: {diffs}")
    rule = pass_rule(tab.loc[tab["traded"], "g"].to_numpy(float))
    reh = rehearse(tab, _d, cl["cost_usd"])
    return {"source": "run_h2_ng_stage_a.build + signed on the Stage A freeze's in-sample fixtures",
            "rehearsal_of_the_beside_lines_on_the_in_sample": reh,
            "n": got["n"], "gate_mean": got["gate_mean"], "gate_mean_repr": repr(got["gate_mean"]),
            "exact": {"n": got["n"] == KNOWN["n"], "gate_mean": got["gate_mean"] == KNOWN["gate_mean"]},
            "in_sample_days": [got["first"], got["last"]], "table_rows": int(len(tab)),
            "prefix_through_a6_anchor": answer(tab, A6_ANCHOR_IN),
            "in_sample_statistics": {k: rule[k] for k in ("mean_g", "se", "t_ordinary", "t_nw5", "mean_net")},
            "in_sample_mng_line": mng, "mng_cost_line": cl,
            "mng_line_reproduces_d630_component_mng": {"max_abs_diff": max(abs(v) for v in diffs.values()),
                                                       "exact": all(v == 0 for v in diffs.values())},
            "runtime_s": round(time.time() - t0, 1)}


# ================================================================================ the vault's reported-beside lines
def vault_frame(joint: Path) -> pd.DataFrame:
    """D630's frame rebuilt from the vault panels the input path wrote beside the table, the cut held at the seal
    (D630's own check then raises on any bar dated 2026-09-19 or later)."""
    R, H = _R(), _H()
    f = {"FLOW": joint / "ledger_predicted_flow_daily.csv.gz", "BARS": joint / "ng_minute_bars.csv.gz",
         "PANEL": joint / "ledger_window_volume_daily.csv.gz", "CAL": joint / "ledger_calendar_flags.csv",
         "FSHARE": joint / "ledger_fut_share_daily_a6.csv.gz"}
    pairs = [(R, "CUT", SEAL), (H, "CUT", SEAL)] + [(R, k, f[k]) for k in ("FLOW", "BARS", "PANEL", "CAL")] + \
        [(H, k, f[k]) for k in ("FLOW", "PANEL", "FSHARE", "CAL")]
    with held(pairs):
        d = R.build(read_returns=True)["d"]
    check_days(d["day"])
    return d


def audit_frame(v: pd.DataFrame, dv: pd.DataFrame) -> None:
    """Second implementation of the traded set: D630's frame (signal_day, its own signed g) against the table."""
    t = to_table(dv)
    bad = same_rows(v.reset_index(drop=True), t)
    if bad:
        raise VaultError(f"the trade table is not D630's frame on {len(bad)} vault days (first {bad[0]})")


def welch(a: np.ndarray, b: np.ndarray) -> float:
    return float((a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))


def beside(v: pd.DataFrame, dv: pd.DataFrame | None, ins: pd.DataFrame | None, cost_mng: float,
           d649_out: Path | None) -> dict[str, Any]:
    R, H = _R(), _H()
    tr, g = v["traded"].to_numpy(bool), v["g"].to_numpy(float)
    gt, days = g[tr], v["day"].to_numpy()
    out: dict[str, Any] = {}
    perf = R.performance(pd.DataFrame({"traded": tr}), g, COST_FULL)
    daily_full_net = perf.pop("_daily_net")
    out["performance_full_size"] = {**perf, "calendar_days": int(len(v))}
    mng = mng_line(tr, g, cost_mng)
    daily_mng = mng.pop("_daily_net")
    out["mng_line"] = mng
    if len(gt) >= 3:
        out["distribution"] = {"gross": R.distribution(gt), "net": R.distribution(full_net(gt))}
    years = np.array([x[:4] for x in days])
    out["by_year"] = {y: R.mean_t(g[tr & (years == y)]) for y in sorted(set(years[tr]))
                      if (tr & (years == y)).sum() >= 2}
    a, b = g[tr & (years == "2025")], g[tr & (years == "2026")]
    if len(a) >= 2 and len(b) >= 2:
        out["2025_vs_2026"] = {"diff_mean_g": float(a.mean() - b.mean()), "welch_t": welch(a, b)}
    if len(gt):
        srt = np.sort(gt)[::-1]
        k1 = max(1, int(math.ceil(0.01 * len(gt))))
        top = int(np.argmax(np.where(tr, g, -np.inf)))
        out["depends"] = {
            "trades_for_half_the_gross": int(np.searchsorted(np.cumsum(srt), srt.sum() / 2) + 1) if srt.sum() > 0
            else None,
            "top10_share_of_gross": float(srt[:10].sum() / srt.sum()) if srt.sum() != 0 else None,
            "without_best_1pct_days": R.mean_t(srt[k1:]) if len(srt) - k1 >= 2 else None,
            "top_trade": {"day": str(days[top]), "g": float(g[top])}}
    if dv is not None:
        dv = dv.reset_index(drop=True)
        pm = dv["plc_traded"].to_numpy(bool) & dv["plc_clean"].to_numpy(bool)
        pg = (dv["plc_dir"] * dv["m_plc"]).to_numpy(float)
        out["placebo_1130"] = R.mean_t(pg[pm & np.isfinite(pg)]) if (pm & np.isfinite(pg)).sum() >= 2 else None
        rr = np.random.default_rng(ROT_SEED)
        ts = R.rotation(dv, rr, ROT_DRAWS)
        p50, p95, p95_se = H.p95_with_se(ts, rr)
        sg = R.signed(dv)
        ok = dv["traded"].to_numpy(bool) & np.isfinite(sg)
        t_obs = R.mean_t(sg[ok])["t"]
        if not math.isclose(t_obs, R.mean_t(gt)["t"], rel_tol=0, abs_tol=0):
            raise VaultError("right-quantity: the rotation's observed t is not the table's")
        out["rotation"] = {"p50": p50, "p95": p95, "p95_se": p95_se, "t_observed_ordinary": t_obs,
                           "margin": t_obs - p95, "beats_p95_by_2se": bool(t_obs - p95 > 2 * p95_se),
                           "draws": int(len(ts)), "seed": ROT_SEED, "statistic": "D630 C2: the ordinary t"}
        un = ~dv["traded"].to_numpy(bool) & np.isfinite(sg)
        if un.sum() >= 2:
            out["untraded_days_same_rule"] = R.mean_t(sg[un])
    else:
        out["placebo_1130"] = out["rotation"] = "not computed: no vault frame"
    if ins is None:
        out["rho_with_d649"] = "not computed (the in-sample rehearsal)"
        return out
    P = _P649()
    itr = ins["traded"].to_numpy(bool)
    take = P.select(ins["g"].to_numpy(float)[itr], ins["absI_usd"].to_numpy(float)[itr], tr,
                    v["absI_usd"].to_numpy(float), g)
    d649 = np.where(take, g * P.MNG_RATIO - P.MNG_COST, 0.0)
    rho: dict[str, Any] = {"d649_trades": int(take.sum()), "d649_subset_of_d723": bool((take <= tr).all())}
    if take.sum() >= 2 and daily_mng.std() > 0 and d649.std() > 0:
        rho["rho_daily_mng_net"] = float(np.corrcoef(daily_mng, d649)[0, 1])
        rho["rho_d723_full_net_vs_d649_mng_net"] = float(np.corrcoef(daily_full_net, d649)[0, 1])
    if d649_out is not None and d649_out.exists():
        o = json.loads(d649_out.read_text(encoding="utf-8"))
        rho["d649_output"] = {"trades": o.get("trades"), "mng_net_per_trade": o.get("mng_net_per_trade"),
                              "agrees": o.get("trades") == int(take.sum())}
    else:
        rho["d649_output"] = "absent: D649's vault not yet scored; its book is recomputed with D649's own select"
    out["rho_with_d649"] = rho
    return out


# ================================================================================ freeze and vault
def git_head() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, encoding="utf-8",
                       check=False)
    return r.stdout.strip()


def freeze(root: Path | None) -> int:
    if FROZEN.exists():
        raise VaultError(f"{FROZEN.name} exists; the freeze is written once (a change needs a new record)")
    import_builder_chain()
    ka = known_answer(root)
    doc = manifest(REPO, ka)
    extra = imported_repo_files(REPO) - set(doc["imported_unchanged"]) - {RUNNER_REL, BUILDER_REL}
    if extra:
        raise VaultError(f"imported but not discovered (the discovery is incomplete): {sorted(extra)}")
    doc.update({"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git_head": git_head()})
    with open(FROZEN, "x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1, default=float) + "\n")
    print(json.dumps(doc, indent=1, default=float))
    return 0


def refuse(word: str | None) -> bool:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10; D630 s.8; D723 s.4)")
        return True
    return False


def check_manifests(joint: Path) -> dict[str, str]:
    """The input path's own sha256 of every file read here (dbn_manifest.json, panels_manifest.json)."""
    want: dict[str, str] = {}
    for m in ("dbn_manifest.json", "panels_manifest.json"):
        want.update(json.loads((joint / m).read_text(encoding="utf-8"))["sha256"])
    for name, h in want.items():
        if sha_bytes(joint / name) != h:
            raise VaultError(f"{name}: not the input path's manifest sha256")
    return want


def vault(table: Path, word: str | None, accept_tail: bool, root: Path | None) -> int:
    if refuse(word):
        return REFUSED
    if not FROZEN.exists():
        raise VaultError(f"{FROZEN.name} is missing: the vault is scored only after the freeze (D723 s.4)")
    if OUT.exists():
        raise VaultError(f"{OUT.name} exists: the vault was opened once; a second opening is refused (D630 s.8)")
    doc = json.loads(FROZEN.read_text(encoding="utf-8"))
    check_freeze(doc, REPO)
    if subprocess.run([sys.executable, str(VERIFY_A)], cwd=REPO, check=False).returncode != 0:
        raise VaultError("verify_ledger_stage_a_ng.py: the Stage A freeze has moved")
    joint = table.resolve().parent
    shas = check_manifests(joint)
    if shas.get(table.name) != sha_bytes(table):
        raise VaultError(f"{table.name} is not the table the input path's manifest names (pass the FULL table, "
                         "d630_trade_table.csv; its vault rows are checked against d630_vault_trade_table.csv)")
    tab = read_table(table)
    # the re-proof: D630's path on the frozen in-sample fixtures, then the table's own in-sample rows against it
    ins, _ = in_sample(root)
    check_known(answer(ins))
    t_in = tab[tab["day"] < CUT_IN].reset_index(drop=True)
    if not len(t_in):
        raise VaultError("the table holds no in-sample rows: pass the FULL table (d630_trade_table.csv)")
    pre = same_rows(t_in[t_in["day"] <= A6_ANCHOR_IN], ins[ins["day"] <= A6_ANCHOR_IN].reset_index(drop=True))
    if pre:
        raise VaultError(f"the table's in-sample rows through {A6_ANCHOR_IN} differ from D630's on {len(pre)} days")
    tail = same_rows(t_in, ins.reset_index(drop=True))
    full = answer(t_in)
    reproof: dict[str, Any] = {"d630_path": answer(ins), "prefix_identical_through": A6_ANCHOR_IN,
                               "table_in_sample": full, "a6_tail_days_moved": tail}
    try:
        check_known(full)
        reproof["table_in_sample_reproduces_known_answer"] = True
    except VaultError:
        reproof["table_in_sample_reproduces_known_answer"] = False
        if not accept_tail:
            raise VaultError(f"the table's in-sample rows give {full} after A6's anchor moved {len(tail)} days in "
                             f"2025-01..02; the principal decides (--accept-a6-tail-moves)") from None
    reproof["accept_a6_tail_moves"] = bool(accept_tail)
    v = tab[tab["day"] >= VAULT_FROM].reset_index(drop=True)
    check_days(v["day"], VAULT_FROM, VAULT_END)
    vo = joint / "d630_vault_trade_table.csv"
    if vo.exists() and same_rows(read_table(vo), v):
        raise VaultError(f"{vo.name} is not the full table's vault rows")
    dv = vault_frame(joint)
    dv = dv[(dv["day"] >= VAULT_FROM) & (dv["day"] <= VAULT_END)].reset_index(drop=True)
    audit_frame(v, dv)
    cl = mng_cost_line()
    audit_money(full_net, lambda x: mng_gross(x) - cl["cost_usd"])
    res = {"record": SPEC_REL, "programme_slot": PROGRAMME_SLOT, "principals_word": word,
           "opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git_head": git_head(),
           "freeze_sha256": sha_bytes(FROZEN), "table": {"path": str(table), "sha256": sha_bytes(table)},
           "known_answer_reproof": reproof, "vault_days": [str(v["day"].min()), str(v["day"].max())],
           "vault_calendar_days": int(len(v)),
           "gate": pass_rule(v.loc[v["traded"], "g"].to_numpy(float)),
           "beside_never_gating": beside(v, dv, ins, cl["cost_usd"], D649_OUT), "mng_cost_line": cl,
           "deviations": []}
    extra = imported_repo_files(REPO) - set(doc["imported_unchanged"]) - {RUNNER_REL, BUILDER_REL}
    if extra:
        raise VaultError(f"a module outside the freeze was imported: {sorted(extra)}")
    with open(OUT, "x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps(res, indent=1, default=float))
    return 0


# ================================================================================ selftest (synthetic only)
def expect_raise(fn: Callable[[], Any], what: str, fired: list[str], exc: type = VaultError) -> None:
    try:
        fn()
    except exc as e:
        fired.append(what)
        print(f"  fires: {what} ({type(e).__name__})")
        return
    raise AssertionError(f"the check did not fire: {what}")


def synthetic_frame(n: int, rng: np.random.Generator, first: str = VAULT_FROM, edge: float = 60.0) -> pd.DataFrame:
    days = [str(x.date()) for x in pd.bdate_range(first, periods=n)]
    tau_i = rng.integers(0, 3, n)
    dr = np.where(rng.random(n) < 0.5, 1.0, -1.0)
    tr = rng.random(n) < 0.55
    d = pd.DataFrame({"day": days, "year": [x[:4] for x in days], "traded": tr, "dir": dr, "t0_idx": tau_i,
                      "tau": np.array(["13:50", "14:00", "14:10"])[tau_i], "absI_usd": rng.lognormal(5, 0.6, n),
                      "plc_traded": rng.random(n) < 0.35, "plc_clean": True, "plc_dir": dr[::-1].copy(),
                      "m_plc": rng.normal(0, 300, n), "p_held": 3.0})
    for i, t in enumerate(("13:50", "14:00", "14:10")):
        d[f"m_{t}"] = rng.normal(0, 300, n) + np.where(tr & (tau_i == i), edge * dr, 0.0)
    return d


def selftest() -> int:
    fired: list[str] = []
    rng = np.random.default_rng(723)
    R = _R()
    # --- the pass rule: clean, then each part broken on its own
    g = rng.normal(90.0, 250.0, 300)
    ok = pass_rule(g)
    assert ok["verdict"] == "PASS", ok
    assert ok["t_gate"] == R.nw_t(g, NW_LAGS) and ok["t_gate"] == ok["t_nw5"], ok
    cases = {"1 (mean g <= 0)": (g - g.mean() - 5.0, "1_mean_g_positive"),
             "2 (t < 1.2816, net > 0)": (np.r_[np.full(20, 900.0), np.full(20, -830.0)],
                                         "2_one_sided_t_nw5_ge_1.2816"),
             "3 (net <= 0, t large)": (rng.normal(20.0, 20.0, 300), "3_mean_net_at_26_positive")}
    for what, (x, part) in cases.items():
        r = pass_rule(x)
        if r["verdict"] == "PASS" or r["parts"][part]:
            raise AssertionError(f"pass-rule part {what} did not fail: {r}")
        if what != "1 (mean g <= 0)" and sum(not v for v in r["parts"].values()) != 1:
            raise AssertionError(f"breaking part {what} broke another part: {r['parts']}")
        fired.append(f"pass rule part {what}")
        print(f"  fires: pass rule part {what} -> {r['verdict']} ({r['parts']})")
    # NW gates, not the ordinary t: a strongly autocorrelated book the ordinary t would pass
    base = rng.normal(0.0, 1.0, 20)
    ar = np.repeat(36.0 + 200.0 * (base - base.mean()) / base.std(ddof=1), 8)  # runs of 8: ordinary t ~2.3, NW ~1.1
    r = pass_rule(ar)
    if not (r["t_ordinary"] >= T_ONE_SIDED > r["t_nw5"] and r["verdict"] != "PASS"
            and r["parts"]["1_mean_g_positive"] and r["parts"]["3_mean_net_at_26_positive"]):
        raise AssertionError(f"the gate did not read the NW t: {r}")
    fired.append("gate reads NW(5): ordinary t passes, NW fails -> not PASS")
    print(f"  fires: the gate reads NW(5) (ordinary t {r['t_ordinary']:.2f}, NW {r['t_nw5']:.2f} -> {r['verdict']})")
    u = pass_rule(g[:MIN_DAYS - 1])
    assert u["verdict"] == "UNRESOLVED" and pass_rule(g[:MIN_DAYS])["verdict"] != "UNRESOLVED", u
    fired.append(f"floor: {MIN_DAYS - 1} traded days -> UNRESOLVED ({MIN_DAYS} -> scored)")
    print(f"  fires: the floor ({MIN_DAYS - 1} days -> UNRESOLVED; {MIN_DAYS} -> scored)")
    expect_raise(lambda: pass_rule(np.r_[g, np.nan]), "a traded day without a finite g", fired)
    # --- money
    cl = mng_cost_line()
    audit_money(full_net, lambda x: mng_gross(x) - cl["cost_usd"])
    expect_raise(lambda: audit_money(lambda x: x + COST_FULL, lambda x: mng_gross(x) - cl["cost_usd"]),
                 "sign audit: net = gross + cost", fired)
    expect_raise(lambda: audit_money(full_net, lambda x: -mng_gross(x) - cl["cost_usd"]),
                 "sign audit: a flipped MNG book", fired)
    # --- the seal and the window
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        good = "day,traded,absI_usd,g\n2025-03-03,True,120.5,40.25\n2026-09-18,False,10,0\n"
        (t / "ok.csv").write_text(good, encoding="utf-8", newline="\n")
        tab = read_table(t / "ok.csv")
        assert tab["traded"].tolist() == [True, False] and tab["g"].tolist() == [40.25, 0.0], tab
        (t / "seal.csv").write_text(good + "2026-09-19,True,99,NOT-A-NUMBER\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: read_table(t / "seal.csv"), "a 2026-09-19 session in the table (before parsing)",
                     fired, SealError)
        expect_raise(lambda: check_days(["2026-09-22"]), "a session after the seal", fired, SealError)
        expect_raise(lambda: check_days(["2025-02-28"], VAULT_FROM, VAULT_END), "an in-sample day scored", fired)
        (t / "hdr.csv").write_text("day,traded,g\n2025-03-03,True,1\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: read_table(t / "hdr.csv"), "a table without D630's columns", fired)
    # --- the known answer and the in-sample re-proof
    check_known(dict(KNOWN))
    expect_raise(lambda: check_known({**KNOWN, "n": 1027}), "known answer: n - 1", fired)
    expect_raise(lambda: check_known({**KNOWN, "gate_mean": KNOWN["gate_mean"] + 1e-12}), "known answer: mean + 1e-12",
                 fired)
    a = pd.DataFrame({"day": ["2024-12-30", "2024-12-31", "2025-01-02"], "traded": [True, False, True],
                      "absI_usd": [1.0, 2.0, 3.0], "g": [5.0, 0.0, -1.0]})
    b = a.copy()
    assert same_rows(a, b) == []
    b.loc[2, "g"] = np.nextafter(-1.0, 0.0)
    assert same_rows(a, b) == ["2025-01-02"] and same_rows(a[a["day"] <= A6_ANCHOR_IN], b[b["day"] <= A6_ANCHOR_IN]) == []
    fired.append("row audit: one ULP on a 2025-01 day is seen (and is outside the hard prefix)")
    print("  fires: row audit sees one ULP; the hard prefix ends at A6's anchor")
    # --- the reported-beside lines end to end on synthetic frames, and the frame audit
    dv = synthetic_frame(390, rng)
    v = to_table(dv)
    audit_frame(v, dv)
    ins = to_table(synthetic_frame(600, np.random.default_rng(1), first="2022-01-03", edge=150.0))
    ins["absI_usd"] = 100.0  # D649's pass-through b ~ mean g / 100, so most synthetic vault days clear its $100 bar
    res = beside(v, dv, ins, cl["cost_usd"], None)
    need = ("performance_full_size", "mng_line", "distribution", "by_year", "2025_vs_2026", "depends", "placebo_1130",
            "rotation", "rho_with_d649")
    miss = [k for k in need if k not in res or res[k] is None]
    if miss:
        raise AssertionError(f"beside() is missing {miss}")
    if not math.isclose(res["mng_line"]["mean_gross"] * 10, v.loc[v["traded"], "g"].mean(), rel_tol=1e-12):
        raise AssertionError("the MNG line is not a tenth of the full contract")
    print(f"  beside() end to end (synthetic): rotation p50 {res['rotation']['p50']:.2f} p95 {res['rotation']['p95']:.2f}"
          f" +- {res['rotation']['p95_se']:.3f}; placebo t {res['placebo_1130']['t']:.2f}; D649 trades "
          f"{res['rho_with_d649']['d649_trades']}; rho {res['rho_with_d649'].get('rho_daily_mng_net', float('nan')):.2f}")
    v2 = v.copy()
    k = int(np.flatnonzero(v2["traded"].to_numpy())[5])
    v2.loc[k, "g"] = np.nextafter(v2.loc[k, "g"], np.inf)
    expect_raise(lambda: audit_frame(v2, dv), "frame audit: one ULP on one traded day", fired)
    v3 = v.copy()
    j = int(np.flatnonzero(~v3["traded"].to_numpy())[0])
    v3.loc[j, "traded"] = True
    expect_raise(lambda: audit_frame(v3, dv), "frame audit: an untraded day marked traded", fired)
    # --- the freeze: hashes, discovery, and every refusal of the vault mode
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        files = {RUNNER_REL: '"""runner"""\nH = _load("helper_a")\n', SPEC_REL: "# D723\n", D630_PRE_REL: "# pre\n",
                 D630_RES_REL: "# res\n", BUILDER_REL: 'R = _load("helper_b")\nfrom backtest_framework.x import y\n',
                 "scripts/helper_a.py": "A = 1\n", "scripts/helper_b.py": 'G = _load_mod("helper_c", "x")\n',
                 "scripts/helper_c.py": "C = 1\n", "src/backtest_framework/__init__.py": "",
                 "src/backtest_framework/x/__init__.py": "", "src/backtest_framework/x/y.py": "from .z import w\n",
                 "src/backtest_framework/x/z.py": "w = 1\n", STAGE_A_REL: "{}\n"}
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8", newline="\n")
        doc = manifest(root, {"n": 1})
        want = {"scripts/helper_a.py", "scripts/helper_b.py", "scripts/helper_c.py",
                "src/backtest_framework/__init__.py", "src/backtest_framework/x/__init__.py",
                "src/backtest_framework/x/y.py", "src/backtest_framework/x/z.py"}
        if set(doc["imported_unchanged"]) != want:
            raise AssertionError(f"discovery found {sorted(doc['imported_unchanged'])}, not {sorted(want)}")
        check_freeze(doc, root)
        crlf = root / SPEC_REL
        crlf.write_bytes(b"# D723\r\n")
        check_freeze(doc, root)  # LF-pinned: a CRLF checkout is not a drift
        for rel, what in ((RUNNER_REL, "a tampered runner"), (SPEC_REL, "a tampered D723 record"),
                          (D630_RES_REL, "a tampered D630 result"), (BUILDER_REL, "a tampered builder"),
                          ("src/backtest_framework/x/z.py", "a tampered imported module"),
                          (STAGE_A_REL, "a tampered Stage A freeze")):
            p = root / rel
            old = p.read_bytes()
            p.write_bytes(old + b" ")
            expect_raise(lambda: check_freeze(doc, root), f"hash check: {what}", fired)
            p.write_bytes(old)
        check_freeze(doc, root)
        p = root / "scripts" / "helper_a.py"
        p.write_text('A = 1\nB = _load("helper_d")\n', encoding="utf-8", newline="\n")
        (root / "scripts" / "helper_d.py").write_text("D = 1\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: check_freeze(doc, root), "hash check: a new import added to an imported module", fired)
        p.write_text("A = 1\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: check_freeze({**doc, "params": {**doc["params"], "cost_full_usd": 16.0}}, root),
                     "hash check: a parameter changed", fired)
        # the vault mode's refusals, on paths held inside the temp dir (the real freeze and output are never touched)
        fz, out = root / "frozen.json", root / "out.json"
        g_mod = sys.modules[__name__]
        with held([(g_mod, "FROZEN", fz), (g_mod, "OUT", out)]):
            assert FROZEN == fz and OUT == out
            for argv in (["--vault", "--trade-table", "x.csv"], ["--vault", "--trade-table", "x.csv",
                                                                 "--principals-word", "  "]):
                if main(argv) != REFUSED:
                    raise AssertionError(f"{argv} ran without the principal's word")
            fired.append("vault refused without the principal's word (absent, blank)")
            print("  fires: --vault refused without the principal's word (absent, blank) -> exit 2")
            expect_raise(lambda: main(["--vault", "--trade-table", "x.csv", "--principals-word", "go"]),
                         "vault refused without the freeze", fired)
            fz.write_text("{}\n", encoding="utf-8")
            out.write_text("{}\n", encoding="utf-8")
            expect_raise(lambda: main(["--vault", "--trade-table", "x.csv", "--principals-word", "go"]),
                         "vault refused on a second opening (the output exists)", fired)
            expect_raise(lambda: main(["--freeze"]), "freeze refused when the freeze exists", fired)
        assert FROZEN == REPO / "data" / "ledger_frozen_vault_h2_ng.json" and OUT == REPO / "data" / "vault_d723_ng_stage_a.json"
    # the real repo: the static discovery covers every module the NG input path actually imports (code, no data)
    import_builder_chain()
    disc = set(discover(REPO, (BUILDER_REL, RUNNER_REL)))
    extra = imported_repo_files(REPO) - disc - {RUNNER_REL, BUILDER_REL}
    if extra:
        raise AssertionError(f"imported but not discovered: {sorted(extra)}")
    print(f"  the real discovery: {len(disc)} repo modules would be hashed; every module the input path and this "
          "runner import is among them")
    print(f"selftest OK: {len(fired)} checks fired on their breaks; the clean cases pass")
    return 0


# ================================================================================ entry point
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--known-answer", action="store_true")
    g.add_argument("--freeze", action="store_true", help="write the D723 freeze ONCE (after the NG input path is final)")
    g.add_argument("--vault", action="store_true", help="the joint run ONLY")
    ap.add_argument("--trade-table", type=Path, default=None, help="the FULL table: data/joint_run/ng/d630_trade_table.csv")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--accept-a6-tail-moves", action="store_true",
                    help="the principal's: accept in-sample rows 2025-01..02 moved by the vault's fut-share anchors")
    ap.add_argument("--data-root", type=Path, default=None, help="where the frozen in-sample fixtures are")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault:
        if refuse(a.principals_word):
            return REFUSED
        if a.trade_table is None:
            raise VaultError("--vault needs --trade-table")
        return vault(a.trade_table, a.principals_word, a.accept_a6_tail_moves, a.data_root)
    if a.freeze:
        return freeze(a.data_root)
    print(json.dumps(known_answer(a.data_root), indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
