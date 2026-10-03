"""D781: base L4 (D778's base book, the M2K closing-auction fade) for the joint vault run, programme slot 10. Spec:
docs/decisions/D781-PRE-REG-the-m2k-closing-auction-fade-for-the-joint-vault.md, committed before this file existed.

    uv run --no-sync python scripts/vault_d781_l4_auction_fade.py --selftest        # synthetic only
    uv run --no-sync python scripts/vault_d781_l4_auction_fade.py --rehearse        # in-sample (2016-2023), once
    uv run --no-sync python scripts/vault_d781_l4_auction_fade.py --power           # in-sample, once
    uv run --no-sync python scripts/vault_d781_l4_auction_fade.py --freeze          # once, after both; slot 10
    python scripts/vault_d781_l4_auction_fade.py --build-vault-fixture --principals-word "..." [--accept-hole D]
                                         # SYSTEM python (databento); the joint run ONLY, after the D462 rebuild
                                         # through 2026-09-18 and the 10-09 top-up
    uv run --no-sync python scripts/vault_d781_l4_auction_fade.py --vault --principals-word "..." [--accept-end D]
                                         # the joint run ONLY, after --build-vault-fixture

The construction is D778's base book, imported unchanged (stage0_d778_auction_fade_trend_filter.frame over D777's panel;
D777's rotation; D775's trade_stats). In every mode but --vault the bars come through D778's loader, which keeps sessions
before 2024-01-01 and raises on a later one. --build-vault-fixture runs D644's builder functions (build_fut_opening_1m:
load_front, process_chunk; D462's ids_of) unchanged for YM and RTY, with slot 9's per-record cut and hole check, into
data/joint_run/d781/ (main checkout); it never writes the committed fixture. --vault refuses unless that file's RTY rows
through 2025-02-28 equal the committed fixture's, row for row, and reads nothing after 2026-09-18.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as D775  # noqa: E402
import stage0_d777_post_close_fade as D7  # noqa: E402
import stage0_d778_auction_fade_trend_filter as D8  # noqa: E402

RUNNER_REL = "scripts/vault_d781_l4_auction_fade.py"
SPEC_REL = "docs/decisions/D781-PRE-REG-the-m2k-closing-auction-fade-for-the-joint-vault.md"
D778_PRE_REL = "docs/decisions/D778-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-trend-filter.md"
D778_RES_REL = "docs/decisions/D778-STAGE-0-RESULT-the-trend-filter-removes-the-best-trades.md"
D644_REL = "scripts/build_fut_opening_1m.py"
D778_JSON = REPO / "data" / "stage0_d778_auction_fade_trend_filter.json"
REHEARSAL = REPO / "data" / "rehearsal_vault_d781.json"
POWER = REPO / "data" / "vault_d781_power.json"
FROZEN = REPO / "data" / "FROZEN_vault_d781_l4_auction_fade.json"
OUT = REPO / "data" / "vault_d781_l4_auction_fade.json"
JOINT = D7.MAIN / "data" / "joint_run" / "d781"
FIX_NAME = "fut_opening_globex_1m_ym_rty.csv.gz"
JOINT_FIX = JOINT / FIX_NAME
STAGE = JOINT / "stage"
BUILD_META = JOINT / "d781_fixture_build.json"

ROOT = "RTY"
BUILD_ROOTS = ("YM", "RTY")
_, MULT, COST = D7.ROOTS[ROOT]
IN_LO, IN_HI = "2016-01-01", "2023-12-31"
VAULT_FROM, VAULT_END = "2024-01-01", "2026-09-18"
SPLIT_FROM, IDENTITY_TO = "2025-03-01", "2025-02-28"
KNOWN_TRADES, KNOWN_MEAN_2DP = 280, 15.84
MIN_TRADES, T_GATE = 40, 1.2816
POWER_N, POWER_DRAWS, POWER_FRACS, WIN_STEP = 133, 4000, (1.0, 0.75, 0.5, 0.25, 0.0), 16
SEED = 781
SLOT = 10
PROGRAMME_FAMILY = "closing-auction fade (M2K, base L4)"
REGISTERED = "2026-10-03"
PAGE_DATE = "2026-09-21"                                     # the page's pinned render date (as D776)
INSTRUCTION = 'the principal, 2026-10-03: "Pre-reg L4\'s freeze for slot 10"; "build it"'
NOTE = ("Vault line: D778's base book (D772 L4), the M2K 15:50 -> 16:00 closing-auction move in its trailing top fifth, "
        "faded from the next 18:05 reopen to 10:00, one M2K, $3.76, sessions 2024-01-01 -> 2026-09-18; PASS with >= 40 "
        "trades, mean net > 0 and one-sided t >= 1.2816, and mean gross above the vault-window exact rotation p95; FAIL if "
        "mean net <= 0; else UNRESOLVED")
REFUSED = 2
ET = "US/Eastern"
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")


class VaultError(RuntimeError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


# ================================================================================ loading and the trades
def in_sample_bars() -> pd.DataFrame:
    b = D8._load_file((FIX_NAME, (ROOT,)))                   # D778's loader: sessions < 2024-01-01, asserted
    if (b["session"] > IN_HI).any():
        raise VaultError("seal: an in-sample load holds a session after 2023-12-31")
    return b


def read_vault(path: Path, lo: str, hi: str) -> pd.DataFrame:
    """D778's loader's filters (root, sessions, bars, a 0-4 day stamp lag), on any file, over [lo, hi]."""
    parts = []
    for ch in pd.read_csv(path, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == ROOT) & (ch["session"] >= lo) & (ch["session"] <= hi) & ch["hhmm"].isin(D8.BARS)]
        lag = (pd.to_datetime(ch["session"]) - pd.to_datetime(ch["et"].str[:10])).dt.days
        parts.append(ch[(lag >= 0) & (lag <= D7.MAX_GAP)])
    return window_rows(pd.concat(parts, ignore_index=True), hi)


def window_rows(b: pd.DataFrame, hi: str) -> pd.DataFrame:
    if len(b) and b["session"].max() > hi:
        raise VaultError(f"seal: a row after {hi} survived the filter")
    return b


def frame(b: pd.DataFrame) -> pd.DataFrame:
    """D778's frame, unchanged, plus S's 16:00 price (for the reported give-back share)."""
    D = D8.frame(b, ROOT)
    p = b[b["root"] == ROOT].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    D["p16"] = p["15:59"].reindex(D.index)
    return D


def known(D: pd.DataFrame, hi: str = IN_HI) -> dict[str, Any]:
    B = D[D["base"] & (D["s1"] <= hi)]
    return {"trades": int(len(B)), "mean_gross": float(B["gross"].mean())}


def check_known(got: dict[str, Any], ref: dict[str, Any]) -> None:
    if got["trades"] != ref["trades"] or not math.isclose(got["mean_gross"], ref["mean_gross"], rel_tol=0, abs_tol=1e-9):
        raise VaultError(f"the in-sample known answer is not reproduced: {got} against {ref}")


# ================================================================================ the gate
def gate(n: int, mean_net: float, t: float, mean_gross: float, p95: float) -> dict[str, Any]:
    g0, g1, g2 = n >= MIN_TRADES, (mean_net > 0 and t >= T_GATE), mean_gross > p95
    verdict = "PASS" if (g0 and g1 and g2) else "FAIL" if mean_net <= 0 else "UNRESOLVED"
    return {"G0": bool(g0), "G1": bool(g1), "G2": bool(g2), "verdict": verdict}


def tstat(x: pd.Series) -> float:
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def score(D: pd.DataFrame, lo: str, hi: str, workers: int = 4, full: bool = True) -> dict[str, Any]:
    """Sessions S >= lo whose exit day S+1 <= hi, valid by D778's rule; the trades are its base book's."""
    W = D[D["cvalid"] & (D.index >= lo) & (D["s1"] <= hi)].copy()
    R = W[W["base"]]
    n = len(R)
    if n < 3:
        return {"trades": n, "gate": gate(n, float("nan"), float("nan"), float("nan"), float("nan"))}
    net = R["gross"] - COST
    t = tstat(net)
    s = (W["side"] * W["base"]).to_numpy(dtype=float)
    rot = D7.rotation(s, W["y"].to_numpy(dtype=float), workers)
    if abs(rot[0] - R["gross"].mean()) > 1e-9:
        raise VaultError("right quantity: rotation offset 0 must equal the observed")
    p95 = float(np.percentile(rot[1:], 95))
    out: dict[str, Any] = {"window": [lo, hi], "trades": n, "mean_gross": float(R["gross"].mean()),
                           "mean_net": float(net.mean()), "t_net": t, "rotation_p50": float(np.percentile(rot[1:], 50)),
                           "rotation_p95": p95, "rotation_rank": float((rot[1:] < rot[0]).mean()),
                           "gate": gate(n, float(net.mean()), t, float(R["gross"].mean()), p95)}
    if full:
        out["stats"] = D775.trade_stats(R["gross"], COST)
        out["book"] = D8.book_of(W, "base", COST)[0]
        drift = float(W["y"].mean())
        sides = {k: {"n": int(len(g)), "mean_gross": round(float(g["gross"].mean()), 2),
                     "mean_net": round(float(g["gross"].mean()) - COST, 2), "win": round(float((g["gross"] > 0).mean()), 3)}
                 for k, g in R.groupby(np.where(R["fall"], "fall (long)", "rise (short)"))}
        out["sides"] = sides
        out["drift_adjusted"] = {"drift": round(drift, 2),
                                 "fall": round(float(R.loc[R["fall"], "gross"].mean()) - drift, 2) if R["fall"].any() else None,
                                 "rise": round(float(R.loc[~R["fall"], "gross"].mean()) + drift, 2) if (~R["fall"]).any() else None}
        out["by_year"] = {k: [int(len(g)), round(float(g["gross"].mean()), 2), round(float((g["gross"] > 0).mean()), 3)]
                          for k, g in R.groupby("year")}
        out["abs_c_terciles"] = {str(k): round(float(g["gross"].mean()), 2) for k, g in
                                 R.groupby(pd.qcut(R["c"].abs().rank(method="first"), 3, labels=["low", "mid", "high"]),
                                           observed=True)}
        out["va_mean"] = round(float(R["va"].mean()), 3)
        give = R["side"] * (R["ex"] - R["p16"]) * MULT
        out["giveback_share_16_to_10"] = round(float(give.mean() / (R["c"].abs() * MULT).mean()), 3)
        R2 = R[R.index >= SPLIT_FROM]
        out["split_from_2025_03"] = ({"trades": int(len(R2)), "mean_net": round(float(R2["gross"].mean()) - COST, 2),
                                      "t_net": round(tstat(R2["gross"] - COST), 2)} if len(R2) > 2 else None)
        out["top5"] = [[d, round(v, 2)] for d, v in net.nlargest(5).items()]
        out["bottom5"] = [[d, round(v, 2)] for d, v in net.nsmallest(5).items()]
    return out


# ================================================================================ power
def power(D: pd.DataFrame) -> dict[str, Any]:
    R = D[D["base"] & (D["s1"] <= IN_HI)]
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"n_vault": POWER_N, "draws": POWER_DRAWS, "g0_g1": {}}
    for base, sel in (("all", R["year"] != ""), ("2018-19", R["year"] <= "2019"), ("2020-23", R["year"] >= "2020")):
        g = R.loc[sel, "gross"].to_numpy()
        mu = g.mean()
        row = {}
        for f in POWER_FRACS:
            gg = g - (1 - f) * mu
            hits = 0
            for _ in range(POWER_DRAWS):
                x = rng.choice(gg, POWER_N, replace=True) - COST
                sd = x.std(ddof=1)
                hits += int(x.mean() > 0 and sd > 0 and x.mean() / sd * math.sqrt(POWER_N) >= T_GATE)
            row[f"{int(f * 100)}%"] = round(hits / POWER_DRAWS, 3)
        out["g0_g1"][base] = {"trades": int(len(g)), "mean_gross": round(float(mu), 2), "pass": row}
    idx, s1 = list(R.index), list(R["s1"])
    wins = []
    for i in range(0, len(idx) - POWER_N + 1, WIN_STEP):
        lo, hi = idx[i], s1[i + POWER_N - 1]
        s = score(D, lo, hi, workers=1, full=False)
        wins.append({"from": lo, "to": hi, "trades": s["trades"], "mean_net": round(s["mean_net"], 2),
                     "t_net": round(s["t_net"], 2), "rotation_p95": round(s["rotation_p95"], 2), **s["gate"]})
    out["full_gate_windows"] = wins
    out["full_gate_summary"] = {v: sum(w["verdict"] == v for w in wins) for v in ("PASS", "UNRESOLVED", "FAIL")}
    out["independent_windows"] = round(len(idx) / POWER_N, 2)
    return out


# ================================================================================ freeze
_TOP = re.compile(r"^(?:import|from)[ \t]+([A-Za-z_]\w*)", re.M)
_BF = re.compile(r"^[ \t]*(?:from[ \t]+(backtest_framework[\w.]*)[ \t]+import|import[ \t]+(backtest_framework[\w.]*))", re.M)
_SPEC_LOAD = re.compile(r"spec_from_file_location\(\s*\"[\w.]+\"\s*,\s*REPO\s*/\s*\"scripts\"\s*/\s*\"([\w.]+\.py)\"")


def sha_text(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def discover(root: Path, starts: tuple[str, ...]) -> list[str]:
    """Repo modules imported at module level, recursively (static; never executed). Also follows a module-level
    `spec_from_file_location(..., REPO / "scripts" / "x.py")` load (D644 loads D462 that way)."""
    seen: set[str] = set()
    stack = list(starts)
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        text = (root / rel).read_text(encoding="utf-8")
        found = [f"scripts/{n}.py" for n in _TOP.findall(text)] + [f"scripts/{n}" for n in _SPEC_LOAD.findall(text)]
        for a, b in _BF.findall(text):
            parts = (a or b).split(".")
            for k in range(1, len(parts) + 1):
                base = root / "src" / Path(*parts[:k])
                for p in (base.with_suffix(".py"), base / "__init__.py"):
                    if p.exists():
                        found.append(p.relative_to(root).as_posix())
        stack += [f for f in found if (root / f).exists() and f not in seen]
    return sorted(seen - {starts[0]})


def params() -> dict[str, Any]:
    return {"root": ROOT, "fixture": FIX_NAME, "mult": MULT, "cost": COST, "bars": D8.BARS,
            "q": D8.Q, "win": D8.WIN, "win_min": D8.WIN_MIN, "ma_n": D8.MA_N, "max_gap": D7.MAX_GAP,
            "in_sample": [IN_LO, IN_HI], "vault": [VAULT_FROM, VAULT_END], "split_from": SPLIT_FROM,
            "joint_fixture": "data/joint_run/d781/" + FIX_NAME, "build_roots": list(BUILD_ROOTS), "identity_to": IDENTITY_TO,
            "known_trades": KNOWN_TRADES,
            "gate": {"G0": f">= {MIN_TRADES} trades", "G1": f"mean net > 0 and one-sided t >= {T_GATE}",
                     "G2": "mean gross > the vault-window exact rotation p95", "FAIL": "mean net <= 0", "else": "UNRESOLVED"},
            "seed": SEED, "programme_family": PROGRAMME_FAMILY, "slot": SLOT}


def manifest(root: Path) -> dict[str, Any]:
    """The runner's module-level imports AND the vault-fixture builder's (D644, which loads D462), all hashed."""
    imported = sorted(set(discover(root, (RUNNER_REL,))) | set(discover(root, (D644_REL,))) | {D644_REL})
    return {"runner": {"path": RUNNER_REL, "sha256": sha_text(root / RUNNER_REL)},
            "records": {p: sha_text(root / p) for p in (SPEC_REL, D778_PRE_REL, D778_RES_REL)},
            "imported_unchanged": {p: sha_text(root / p) for p in imported},
            "files": {p.relative_to(REPO).as_posix(): sha_text(root / p.relative_to(REPO))
                      for p in (D778_JSON, REHEARSAL, POWER)},
            "params": params()}


def check_freeze(doc: dict[str, Any], root: Path = REPO) -> None:
    now = manifest(root)
    bad = [k for k in ("runner", "records", "files", "params") if now[k] != doc.get(k)]
    fi, ni = doc.get("imported_unchanged", {}), now["imported_unchanged"]
    if set(fi) != set(ni):
        bad.append(f"the import set (added {sorted(set(ni) - set(fi))}, dropped {sorted(set(fi) - set(ni))})")
    bad += [f"imported {p}" for p in sorted(set(fi) & set(ni)) if fi[p] != ni[p]]
    if bad:
        raise VaultError(f"moved since the freeze: {bad}")


def write_once(path: Path, doc: dict[str, Any]) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, default=str)
        fh.write("\n")


# ================================================================================ the vault fixture (joint run only)
def restrict_csv(src: Path, field: int, keep: Callable[[str], bool]) -> tuple[bytes, dict[str, Any]]:
    """Slot 9's text filter (joint_d680_vault.restrict_csv), copied: lines whose comma field `field` (a date) passes
    `keep`; no dropped line's values are parsed. Raises on a data line whose field is not a date."""
    opener = gzip.open if src.suffix == ".gz" else open
    out = io.StringIO()
    kept = dropped = 0
    last = ""
    with opener(src, "rt", encoding="utf-8", newline="") as f:
        out.write(f.readline())
        for line in f:
            parts = line.split(",", field + 1)
            d = parts[field] if len(parts) > field else ""
            if not DATE.match(d):
                raise VaultError(f"{src.name}: field {field} is not a date on a data line; nothing is filtered")
            if keep(d):
                out.write(line)
                kept += 1
                last = max(last, d)
            else:
                dropped += 1
    return out.getvalue().encode("utf-8"), {"kept": kept, "dropped": dropped, "last_kept": last}


def write_gz(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as z:
        z.write(data)


def ts_cut_ns(through: str) -> int:
    """18:00 ET on the last session day: every bar before it belongs to a session <= through (D644's session rule)."""
    return int(pd.Timestamp(f"{through} 18:00", tz=ET).tz_convert("UTC").value)


def restrict_chunk(arr: np.ndarray, cut_ns: int) -> tuple[np.ndarray, int]:
    keep = arr["ts_event"] < np.uint64(cut_ns)
    n_past = int((~keep).sum())
    return (arr if n_past == 0 else arr[keep]), n_past


def holes(spans: list[tuple[int, int]], lo: int, hi: int) -> list[tuple[int, int]]:
    """The parts of [lo, hi) that no [start, end) span covers."""
    out, at = [], lo
    for s, e in sorted(spans):
        if e <= at:
            continue
        if s > at:
            out.append((at, min(s, hi)))
        at = max(at, e)
        if at >= hi:
            break
    if at < hi:
        out.append((at, hi))
    return [(a, b) for a, b in out if a < b]


def iso(ns: int) -> str:
    return pd.Timestamp(ns, tz="UTC").strftime("%Y-%m-%dT%H:%MZ")


def _load_d644() -> Any:
    import build_fut_opening_1m as D644                       # system python: it loads D462, which reads databento files
    return D644


def _fixture_worker(task: tuple[str, int, np.ndarray, pd.DataFrame]) -> dict[str, Any]:
    """D644's `worker` for YM/RTY with the per-record cut; `process_chunk` and `ids_of` are D644's/D462's, unchanged."""
    import databento as db
    D644 = _load_d644()
    path, cut_ns, sessions, front = task
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = D644.D462.ids_of(store)
    parts, n_read, n_past = [], 0, 0
    for arr in store.to_ndarray(count=D644.CHUNK):
        n_read += len(arr)
        arr, k = restrict_chunk(arr, cut_ns)
        n_past += k
        b = D644.process_chunk(arr, w, sessions, front, BUILD_ROOTS)
        if b is not None:
            parts.append(b)
    bars = pd.concat(parts, ignore_index=True) if parts else None
    return {"file": Path(path).name, "rows_read": n_read, "rows_past_cut_dropped": n_past,
            "rows_kept": 0 if bars is None else len(bars), "secs": round(time.time() - t0, 1), "bars": bars}


def build_vault_fixture(word: str | None, data_root: Path, workers: int, accept_holes: tuple[str, ...]) -> int:
    if refuse(word):
        P("[D781] REFUSED: --build-vault-fixture needs --principals-word")
        return REFUSED
    if JOINT_FIX.exists():
        raise VaultError(f"{JOINT_FIX} exists; the vault fixture is built once")
    import databento as db
    D644 = _load_d644()
    t0 = time.time()
    txt, info = restrict_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", 1, lambda d: d <= VAULT_END)
    if info["last_kept"] < VAULT_END:
        raise VaultError(f"fut_index_sessions ends {info['last_kept']}: rebuild D462 through {VAULT_END} first")
    write_gz(STAGE / "fixtures" / "fut_index_sessions.csv.gz", txt)
    sessions, front = D644.load_front(STAGE, VAULT_END, BUILD_ROOTS)
    if len(sessions) == 0 or sessions[-1] > VAULT_END:
        raise VaultError("the staged session table is empty or runs past the cut")
    cut_ns = ts_cut_ns(VAULT_END)
    hdr = []
    for p in sorted((data_root / "raw" / "databento").glob("*/*.ohlcv-1m.dbn.zst"), key=lambda q: q.name):
        m = db.DBNStore.from_file(str(p)).metadata
        hdr.append({"path": str(p), "file": p.name, "bytes": p.stat().st_size, "start": int(m.start), "end": int(m.end)})
    lo = int(pd.Timestamp(f"{D644.START} 00:00", tz=ET).tz_convert("UTC").value) - 86_400 * 10**9
    gaps = holes([(h["start"], h["end"]) for h in hdr], lo, cut_ns)
    ok = {pd.Timestamp(d).strftime("%Y-%m-%d") for d in accept_holes}
    bad = [(a, b) for a, b in gaps if not all(x.strftime("%Y-%m-%d") in ok for x in
                                              pd.date_range(pd.Timestamp(a, tz="UTC").floor("D"),
                                                            pd.Timestamp(b - 1, tz="UTC").floor("D"), freq="D"))]
    if bad:
        raise VaultError("the ohlcv-1m archive has a hole before the cut: " + ", ".join(f"[{iso(a)}, {iso(b)})" for a, b in bad)
                         + " (fill it, or name each whole UTC day with --accept-hole on the principal's word)")
    files = [h for h in hdr if h["start"] < cut_ns]
    order = {h["file"]: i for i, h in enumerate(files)}
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(_fixture_worker, [(h["path"], cut_ns, sessions, front) for h in sorted(files, key=lambda h: -h["bytes"])],
                       chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec, wall = sum(r["secs"] for r in res), time.time() - t0
    P(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {workers} workers ({100 * sec / wall / workers:.0f}%)")
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    n0 = len(bars)
    bars = bars.sort_values(["root", "session", "et"], kind="stable").drop_duplicates(["root", "session", "et"])
    if (bars["session"] > VAULT_END).any():
        raise VaultError("a session past the cut reached the fixture")
    JOINT.mkdir(parents=True, exist_ok=True)
    bars.to_csv(JOINT_FIX, index=False, compression={"method": "gzip", "mtime": 0}, float_format="%.2f", encoding="utf-8",
                lineterminator="\n")
    meta = {"principals_word": word, "builder": RUNNER_REL + " (D644's functions, unchanged; slot 9's per-record cut)",
            "roots": list(BUILD_ROOTS), "sessions": [D644.START, VAULT_END], "ts_cut_utc": iso(cut_ns), "rows": int(len(bars)),
            "duplicates_dropped": int(n0 - len(bars)), "staged_sessions": info, "accepted_holes": sorted(ok),
            "holes_before_cut": [[iso(a), iso(b)] for a, b in gaps],
            "files": [{k: v for k, v in r.items() if k != "bars"} for r in res], "wall_s": round(wall, 1)}
    BUILD_META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    P(json.dumps({k: v for k, v in meta.items() if k != "files"}, indent=1))
    return 0


def identity(new: Path, old: Path, to: str) -> dict[str, Any]:
    """RTY's rows through `to`, as text, row for row; raises unless equal."""
    def rows(p: Path) -> pd.DataFrame:
        parts = [ch[(ch["root"] == ROOT) & (ch["session"] <= to)]
                 for ch in pd.read_csv(p, encoding="utf-8", dtype=str, chunksize=2_000_000)]
        return pd.concat(parts, ignore_index=True).sort_values(["session", "et"], kind="stable").reset_index(drop=True)
    a, b = rows(new), rows(old)
    if list(a.columns) != list(b.columns) or not a.equals(b):
        raise VaultError(f"identity: the rebuilt fixture's RTY rows through {to} differ from the committed fixture's "
                         f"({len(a)} against {len(b)} rows)")
    return {"rows": int(len(a)), "through": to, "equal": True}


# ================================================================================ modes
def rehearse() -> int:
    if REHEARSAL.exists():
        raise VaultError(f"{REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    D = frame(in_sample_bars())
    ka = known(D)
    ref = json.loads(D778_JSON.read_text(encoding="utf-8"))[ROOT]["base_book"]["stats"]
    if ka["trades"] != KNOWN_TRADES or round(ka["mean_gross"], 2) != KNOWN_MEAN_2DP or \
            (ka["trades"], round(ka["mean_gross"], 2)) != (ref["n"], ref["mean_gross"]):
        raise VaultError(f"D778's base book is not reproduced: {ka} against {ref}")
    # the vault reader's path on the committed fixture's in-sample rows: the same trades, exactly
    kv = known(frame(read_vault(D7.FIX / FIX_NAME, D7.START, IN_HI)))
    check_known(kv, ka)
    res = score(D, IN_LO, IN_HI)
    doc = {"mode": "IN-SAMPLE REHEARSAL (2016-01-01 -> 2023-12-31): the vault scorer on the in-sample window",
           "spec": SPEC_REL, "known_answer": ka, "known_answer_d778_json_2dp": ref["mean_gross"],
           "vault_reader_reproduces": kv, "score": res, "wall_s": round(time.time() - t0, 1)}
    write_once(REHEARSAL, doc)
    P(f"[D781] rehearsal: {ka}; vault reader {kv}; in-sample gate {res['gate']}; t {res['t_net']:.2f}; "
      f"rotation p95 {res['rotation_p95']:.2f} (rank {res['rotation_rank']:.3f})")
    return 0


def do_power() -> int:
    if POWER.exists():
        raise VaultError(f"{POWER.name} exists: the power run is run-once")
    if not REHEARSAL.exists():
        raise VaultError("run --rehearse first")
    t0 = time.time()
    D = frame(in_sample_bars())
    check_known(known(D), json.loads(REHEARSAL.read_text(encoding="utf-8"))["known_answer"])
    pw = power(D)
    pw["wall_s"] = round(time.time() - t0, 1)
    write_once(POWER, pw)
    P(f"[D781] power: {pw['g0_g1']}; full-gate windows {pw['full_gate_summary']} (~{pw['independent_windows']} independent)")
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise VaultError(f"{FROZEN.name} exists: the freeze is written once")
    for p in (REHEARSAL, POWER):
        if not p.exists():
            raise VaultError(f"{p.name} is missing: run --rehearse and --power first")
    from backtest_framework.validation.programme import Registry
    reg = Registry()
    if reg.free_slots() != (SLOT,):
        raise VaultError(f"the registry's free slots are {reg.free_slots()}, not ({SLOT},)")
    fam = reg.register(PROGRAMME_FAMILY, Path(SPEC_REL).name, registered_utc=REGISTERED, note=NOTE)
    if fam.slot != SLOT:
        raise VaultError(f"registered in slot {fam.slot}, not {SLOT}")
    reg.render_md(date=PAGE_DATE)
    ka = json.loads(REHEARSAL.read_text(encoding="utf-8"))["known_answer"]
    doc = {"name": "FROZEN_vault_d781_l4_auction_fade", "record": SPEC_REL, "instruction": INSTRUCTION,
           "programme_slot": fam.slot, "programme_family": fam.name, "alpha": fam.alpha, **manifest(REPO),
           "known_answer": ka}
    write_once(FROZEN, doc)
    P(f"[D781] FROZEN; programme slot {fam.slot} ({fam.name}); {len(doc['imported_unchanged'])} imported files hashed")
    return 0


def refuse(word: str | None) -> bool:
    return not (word and word.strip())


def vault(word: str | None, accept_end: str | None, fixture: Path = JOINT_FIX) -> int:
    if refuse(word):
        P("[D781] REFUSED: --vault needs --principals-word")
        return REFUSED
    if not FROZEN.exists():
        raise VaultError("no freeze: --vault runs only on a frozen line")
    doc = json.loads(FROZEN.read_text(encoding="utf-8"))
    check_freeze(doc)
    if OUT.exists():
        raise VaultError(f"{OUT.name} exists: the vault is opened once")
    if not fixture.exists():
        raise VaultError(f"{fixture} is missing: run --build-vault-fixture first (system python)")
    t0 = time.time()
    end = accept_end or VAULT_END
    if end > VAULT_END:
        raise VaultError(f"seal: the vault load may not pass {VAULT_END}")
    ident = identity(fixture, D7.FIX / FIX_NAME, IDENTITY_TO)
    ref = doc["known_answer"]
    check_known(known(frame(in_sample_bars())), ref)                               # the committed in-sample path
    bv = read_vault(fixture, D7.START, end)
    last = bv["session"].max()
    if last < end:
        raise VaultError(f"the vault fixture ends {last}, before {end}: pass --accept-end (the principal's call)")
    Dv = frame(bv)
    check_known(known(Dv, IN_HI), ref)                                              # the vault file's own 2016-2023 rows
    res = score(Dv, VAULT_FROM, end)
    out = {"mode": "VAULT", "spec": SPEC_REL, "principals_word": word, "accept_end": accept_end, "end": end,
           "identity": ident, "known_answer_reproduced_on_both_inputs": ref, "score": res,
           "verdict": res["gate"]["verdict"], "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, out)
    P(f"[D781] VAULT: {res['gate']}; trades {res['trades']}; mean net {res['mean_net']:.2f}; t {res['t_net']:.2f}")
    return 0


# ================================================================================ self-test (synthetic only)
def _synthetic(sessions: list[str], eff: float, rng: np.random.Generator, root: str = ROOT) -> pd.DataFrame:
    """Random-walk sessions; each session's closing move c is followed by -eff x c from the next 18:04 to its 09:59
    (eff > 0 reverts, so the fade pays)."""
    rows, prev_c, level = [], None, 2000.0
    for d in sessions:
        level *= math.exp(rng.normal(0.0002, 0.01))
        bars = {}
        p = level + rng.normal(0, 2)
        for h in D8.BARS:
            p += rng.normal(0, 0.8)
            bars[h] = p
        bars["15:59"] = level
        bars["15:49"] = level - rng.normal(0, 3)
        if prev_c is not None:
            bars["09:59"] = bars["18:04"] - eff * prev_c + rng.normal(0, 0.5)
        prev_c = bars["15:59"] - bars["15:49"]
        for h in D8.BARS:
            day = d if h < "18:00" else (pd.Timestamp(d) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            rows.append({"root": root, "session": d, "et": f"{day} {h}", "hhmm": h, "contract": "RTYZ9",
                         "close": round(bars[h], 1)})
    return pd.DataFrame(rows)


def selftest() -> int:
    fails: list[str] = []

    def expect(fn: Callable[[], Any], what: str, exc: type = VaultError) -> None:
        try:
            fn()
        except exc:
            return
        fails.append(f"did not raise: {what}")

    # 1) the gate's three readings
    if gate(133, 10.0, 2.0, 14.0, 9.0)["verdict"] != "PASS":
        fails.append("gate: a clear pass")
    if gate(133, -1.0, -0.5, 3.0, 9.0)["verdict"] != "FAIL":
        fails.append("gate: a loss must FAIL")
    if gate(133, 2.0, 0.6, 6.0, 9.0)["verdict"] != "UNRESOLVED":
        fails.append("gate: a weak gain is UNRESOLVED")
    if gate(30, 10.0, 2.0, 14.0, 9.0)["verdict"] != "UNRESOLVED":
        fails.append("gate: too few trades is UNRESOLVED")
    # 2) the window filter refuses a row past the end
    expect(lambda: window_rows(pd.DataFrame({"session": ["2026-09-17", "2026-09-21"]}), VAULT_END), "a row after the end")
    # 3) --vault and --build-vault-fixture are refused without a word
    if vault(None, None) != REFUSED or vault("  ", None) != REFUSED:
        fails.append("--vault ran without the principal's word")
    if build_vault_fixture(None, REPO / "data", 1, ()) != REFUSED:
        fails.append("--build-vault-fixture ran without the principal's word")
    # 4) a planted reversal passes, a planted continuation fails (sessions from mid-2022 give the warm-ups history)
    rng = np.random.default_rng(SEED)
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2022-06-01", VAULT_END)]
    for eff, want in ((0.9, "PASS"), (-0.9, "FAIL")):
        D = frame(_synthetic(days, eff, rng))
        got = score(D, VAULT_FROM, VAULT_END, workers=1, full=True)
        if got["gate"]["verdict"] != want:
            fails.append(f"planted effect {eff}: {got['gate']}, expected {want}")
    # 5) the known-answer check raises on a moved answer
    D = frame(_synthetic(days, 0.9, rng))
    k = known(D, VAULT_END)
    expect(lambda: check_known({**k, "mean_gross": k["mean_gross"] + 1e-6}, k), "a known answer moved by 1e-6")
    # 6) the reader filters by root and window; the identity check passes equal files and refuses a moved row
    with tempfile.TemporaryDirectory() as td:
        f1, f2 = Path(td) / "a.csv.gz", Path(td) / "b.csv.gz"
        syn = _synthetic(days[:60], 0.0, rng)
        syn = pd.concat([syn, _synthetic(days[:60], 0.0, rng, root="YM")], ignore_index=True)
        syn.to_csv(f1, index=False, compression="gzip", encoding="utf-8")
        got = read_vault(f1, days[5], days[30])
        if set(got["root"]) != {ROOT} or got["session"].min() < days[5] or got["session"].max() > days[30]:
            fails.append("read_vault: root or window filter")
        syn.to_csv(f2, index=False, compression="gzip", encoding="utf-8")
        if not identity(f1, f2, days[40])["equal"]:
            fails.append("identity: equal files")
        moved = syn.copy()
        i = moved.index[(moved["root"] == ROOT) & (moved["session"] == days[20])][0]
        moved.loc[i, "close"] = moved.loc[i, "close"] + 0.1
        moved.to_csv(f2, index=False, compression="gzip", encoding="utf-8")
        expect(lambda: identity(f1, f2, days[40]), "the identity check on a moved row")
        if not identity(f1, f2, days[19])["equal"]:
            fails.append("identity: a moved row after the cut must not count")
    # 7) the hole finder
    if holes([(0, 5), (6, 10)], 0, 12) != [(5, 6), (10, 12)]:
        fails.append("holes()")
    # 8) the freeze detects drift (once the rehearsal and power files exist); the builder's imports are hashed
    if REHEARSAL.exists() and POWER.exists():
        doc = manifest(REPO)
        check_freeze(doc)
        if D644_REL not in doc["imported_unchanged"] or "scripts/build_fut_index_1m.py" not in doc["imported_unchanged"]:
            fails.append("the builder (D644) and D462 are not hashed")
        doc2 = json.loads(json.dumps(doc))
        doc2["params"]["cost"] = 9.99
        expect(lambda: check_freeze(doc2), "a moved parameter")
        doc3 = json.loads(json.dumps(doc))
        k3 = next(iter(doc3["imported_unchanged"]))
        doc3["imported_unchanged"][k3] = "0" * 64
        expect(lambda: check_freeze(doc3), "a moved imported file")
    if fails:
        raise VaultError("; ".join(fails))
    P("[D781] selftest OK: the gate's readings, the window seal, the refusals without a word, a planted reversal passes "
      "and a continuation fails, the known-answer check, the reader's filters, the identity check (equal, moved, past the "
      "cut), the hole finder"
      + ("; the freeze check fires on a moved parameter and a moved import, and the builder's modules are hashed"
         if REHEARSAL.exists() and POWER.exists() else " (the freeze-drift check runs once the rehearsal and power exist)"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for m in ("selftest", "rehearse", "power", "freeze", "build-vault-fixture", "vault"):
        g.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--principals-word")
    ap.add_argument("--accept-end")
    ap.add_argument("--accept-hole", action="append", default=[])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--data-root", type=Path, default=D7.MAIN / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.power:
        return do_power()
    if a.freeze:
        return freeze()
    if a.build_vault_fixture:
        return build_vault_fixture(a.principals_word, a.data_root, a.workers, tuple(a.accept_hole))
    return vault(a.principals_word, a.accept_end)


if __name__ == "__main__":
    sys.exit(main())
