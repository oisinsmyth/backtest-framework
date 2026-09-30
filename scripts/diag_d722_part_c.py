"""D722 Part C: event windows. How much of each line's 2022 NET sits in the macro-event days, the 2022 FOMC days, the war's
first ten weeks, either side of the 2022-05-16 0DTE era split, and (HO) the backwardation squeezes, against the same number of
2022 trades drawn at random. Spec: docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md s.4 (f25e4726), with
Amendment D722-A1 (7880c5a0); assertions s.7.

    uv run python scripts/diag_d722_part_c.py --selftest   # clean case on the real inputs, synthetic null checks, every canary RAISES
    uv run python scripts/diag_d722_part_c.py --run        # run-once: refuses if data/diag_d722_part_c.json exists

INPUTS (imported, never edited): diag_d722_lines.load_lines() (the per-trade tables, known answers validated on every load) and
diag_d722_conditioners.load_conditioners() (the (root, session) panel; X8 on HO includes EIA_WPSR). data/calendar/events.csv is read
a second time, independently, by the join audit only (rows dated >= 2024-01-01 dropped as they are read).

THE WINDOWS (over a line's 2022 trades; the line's own root's panel row for the trade's session):
  C1_X8       X8 == 1 (FOMC, FOMC_UNSCHEDULED, CPI or EMPSIT that session; on HO also EIA_WPSR)
  C1_FOMC     fomc == 1 (FOMC or FOMC_UNSCHEDULED; 2022 has eight, all scheduled, asserted on every root's panel)
  C2_war      war == 1 (2022-02-24 -> 2022-04-29)
  C3_pre      session <  2022-05-16;  C3_post  session >= 2022-05-16 (the era's first session is "after"). Both tested.
  C4_X12p90   L4 only: X12 >= the 90th percentile (numpy's default linear interpolation) of X12 over HO's panel sessions
              2016-01-01 .. 2021-12-31 (X12 is the prior session's (front - next) / front; high = backwardation).
  beside, reported and NOT read: C1_X8_macro_only on L4 (X8 without EIA_WPSR).
  Reference: C1_X8 and C1_FOMC in every other year each line trades, with the same test.
  BESIDE (the orchestrator's ruling 4; the declared test stays primary): C2_war, C3_pre and C3_post also carry `rotation_null`, the
  exact enumerated rotation: the line's 2022 trading sessions in order (M of them), the window as a block of k consecutive ones,
  every one of the M circular shifts (wrapping at year end; shift 0 is the window itself), each block's exact net and share of 2022
  net. rotation_rank = P(shift <= window), strict and mid beside; null p50 and p95; SE 0 (enumerated).

THE TEST (per window): N = the line's trades in the year, n = the window's. 10,000 draws; draw k takes the n trades with the n
smallest keys of rng.random(N), rng = default_rng(722) created once per (line, year) and drawn row by row: a uniform random n-subset
without replacement. The draws of one (line, year) are shared by its windows (common random numbers; each window's null is exact
marginally). Sums are EXACT: net is held as int64 nano-dollars (quantisation error <= 5e-10 $ a trade, asserted), so the whole-year
window ties every draw exactly and ties are counted honestly.
  rank       P(null sum <= window sum) (the declared rank: a whole-year window gives 1). rank_lt (strict) and rank_mid beside it;
             `tie_sensitive` where rank_lt < 0.95 <= rank.
  share      window net / the year's net, only where the year's net > 0; null p50, p95 of the drawn shares; the p95's bootstrap SE
             (400 resamples of the 10,000 draws, default_rng([722, 95])).
  verdict    (the record) CONCENTRATED iff rank >= 0.95 AND share >= 0.25; else NOT_CONCENTRATED. EMPTY for n = 0.
             UNDEFINED where the year's net <= 0 (no share; the rank on the dollar sum is still reported).
  verdict_se (CLAUDE.md's nulls rule, D373) = UNRESOLVED where share >= 0.25 and |share - p95| <= 2 SE; else the record's verdict.
  flags      denominator_unstable where the year's net > 0 but its t = sum / (sd sqrt N) < 2 (the share's denominator has a
             relative SE above one half); degenerate where n = N.

SPEED. One (B x N) key matrix, one argsort and one int64 cumsum per (line, year) serve every window of that line-year: ~50
line-years, N <= 246, a few seconds each at most. Nothing fans out, so there is no chunk to prove; the self-test proves the one
vectorised draw equals the row-by-row draw bit for bit instead.

SEALS. No value dated 2024-01-01 or later enters: every trade, panel row and calendar row used is asserted < 2024-01-01; the vault is
never read; no fixture is opened here (the two Phase 0 caches and events.csv only).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import diag_d722_conditioners as DC  # noqa: E402  (defines only; main-guarded)
import diag_d722_lines as DL  # noqa: E402  (defines only; main-guarded)

OUT = REPO / "data" / "diag_d722_part_c.json"
EVENTS = REPO / "data" / "calendar" / "events.csv"
SPEC = "docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md s.4, s.7 (f25e4726; D722-A1 7880c5a0)"
SEAL = "2024-01-01"
YEAR = "2022"
SEED = 722
B = 10_000
N_BOOT = 400
BOOT_SEED = (722, 95)
ERA = "2022-05-16"
WAR = ("2022-02-24", "2022-04-29")
REF_LO, REF_HI = "2016-01-01", "2021-12-31"
RANK_BAR, SHARE_BAR, T_STABLE = 0.95, 0.25, 2.0
QSCALE = 1e9            # nano-dollars
Q_TOL = 1e-9            # $: the quantisation error bound (0.5 / QSCALE plus the float spacing at |net| < 1e5)
FOMC_2022_N = 8
LINES = DL.LINES
ROOT_OF = DL.ROOT_OF
FLAGS = ["X8", "fomc", "fomc_unscheduled", "cpi", "empsit", "eia_wpsr", "war", "X12"]
N_SYN_REPS = 200
ROTATION_WINDOWS = ("C2_war", "C3_pre", "C3_post")   # the orchestrator's ruling 4: contiguous windows also get the rotation null


class PartCError(AssertionError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


# ================================================================================ seal
def assert_seal(dates: Any, what: str) -> None:
    d = np.asarray(pd.Series(list(dates), dtype=object).astype(str).str[:10])
    bad = int((d >= SEAL).sum())
    if bad:
        raise PartCError(f"[SEAL] {what}: {bad} row(s) dated >= {SEAL}")


# ================================================================================ the join (vectorised) and its audit
def join_flags(tr: pd.DataFrame, panel: pd.DataFrame, shift: int = 0) -> pd.DataFrame:
    """Each trade's calendar flags and X12 from its OWN root's panel row for its session. `shift` exists only for the canary (a
    join that reads the neighbouring session)."""
    parts = []
    for root, sub in tr.groupby("root", sort=False):
        p = panel.loc[root].sort_index()
        pos = p.index.get_indexer(sub["session"].to_numpy())
        if (pos < 0).any():
            raise PartCError(f"[JOIN] {int((pos < 0).sum())} {root} trade session(s) have no panel row")
        pos = np.clip(pos + shift, 0, len(p) - 1)
        f = p.iloc[pos][FLAGS].copy()
        f.index = sub.index
        parts.append(f)
    return pd.concat(parts).loc[tr.index]


def read_events(cut: str = SEAL) -> dict[str, set[str]]:
    """events.csv read independently of the panel's builder: {ET date: {event}}; rows dated >= cut dropped as they are read."""
    ev: dict[str, set[str]] = {}
    with open(EVENTS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            d = row["datetime_et"][:10]
            if d >= cut:
                continue
            ev.setdefault(d, set()).add(row["event"])
    assert_seal(ev.keys(), "events.csv (as read)")
    return ev


def join_audit(tr: pd.DataFrame, fl: pd.DataFrame, ev: dict[str, set[str]], panel: pd.DataFrame) -> int:
    """A second implementation, plain loops: every calendar flag re-derived from events.csv and the war dates for the trade's own
    session, and HO's X12 looked up by session key in a dict. Must equal the vectorised join on every trade."""
    assert_seal(ev.keys(), "events dict")
    ho = panel.loc["HO"]
    x12 = dict(zip(ho.index.tolist(), ho["X12"].tolist()))
    bad: list[str] = []
    for i, (root, s) in enumerate(zip(tr["root"].tolist(), tr["session"].tolist())):
        e = ev.get(s, set())
        want = {"fomc": int(bool(e & {"FOMC", "FOMC_UNSCHEDULED"})), "fomc_unscheduled": int("FOMC_UNSCHEDULED" in e),
                "cpi": int("CPI" in e), "empsit": int("EMPSIT" in e), "eia_wpsr": int("EIA_WPSR" in e),
                "war": int(WAR[0] <= s <= WAR[1])}
        want["X8"] = int(bool(want["fomc"] or want["cpi"] or want["empsit"] or (root == "HO" and want["eia_wpsr"])))
        for k, v in want.items():
            if int(fl[k].iat[i]) != v:
                bad.append(f"{root} trade {i} {k}")
        if root == "HO":
            a, b = x12[s], float(fl["X12"].iat[i])
            if not (a == b or (math.isnan(a) and math.isnan(b))):
                bad.append(f"HO trade {i} X12")
    if bad:
        raise PartCError(f"[JOIN] the vectorised join disagrees with the loop re-derivation on {len(bad)} cell(s), e.g. {bad[:3]}")
    return len(tr)


def assert_fomc_2022(panel: pd.DataFrame) -> dict[str, Any]:
    out = {}
    for root in ("ES", "NQ", "HO"):
        p = panel.loc[root]
        s = p.index[(p.index.str[:4] == YEAR) & (p["fomc"] == 1)].tolist()
        uns = int(p.loc[p.index.str[:4] == YEAR, "fomc_unscheduled"].sum())
        if len(s) != FOMC_2022_N:
            raise PartCError(f"[FOMC] {root}: {len(s)} FOMC sessions in 2022, expected {FOMC_2022_N}")
        if not ((p["fomc"] == 1) <= (p["X8"] == 1)).all():
            raise PartCError(f"[FOMC] {root}: an FOMC session is not an X8 session")
        out[root] = {"n": len(s), "unscheduled": uns, "sessions": s}
    if len({tuple(v["sessions"]) for v in out.values()}) != 1:
        raise PartCError("[FOMC] the 2022 FOMC sessions differ across roots")
    return out


# ================================================================================ exact sums
def quantize(x: np.ndarray, scale: float = QSCALE) -> np.ndarray:
    x = np.asarray(x, float)
    q = np.rint(x * scale).astype(np.int64)
    err = float(np.max(np.abs(q / scale - x))) if len(x) else 0.0
    if err > Q_TOL:
        raise PartCError(f"[QUANT] quantisation error {err:.3g} $ > {Q_TOL}")
    return q


def assert_right_quantity(q: np.ndarray, tr: pd.DataFrame) -> None:
    """The scored vector is NET (not gross): equal to quantize(net), and different from quantize(gross)."""
    if not np.array_equal(q, quantize(tr["net_usd"].to_numpy())):
        raise PartCError("[RIGHT-QUANTITY] the scored vector is not the net")
    if np.array_equal(q, quantize(tr["gross_usd"].to_numpy())):
        raise PartCError("[RIGHT-QUANTITY] the scored vector equals the gross")


# ================================================================================ the null
def draw_order(N: int, seed: Any = SEED, b: int = B, replace: bool = False, fill: str = "C") -> np.ndarray:
    """(b x N): row k is draw k's permutation (the first n entries = a uniform n-subset). `replace` and `fill` exist only for the
    canaries (with-replacement draws; a column-major fill of the keys)."""
    rng = np.random.default_rng(seed)
    if replace:
        return rng.integers(0, N, size=(b, N))
    U = rng.random((b, N)) if fill == "C" else rng.random((N, b)).T
    return np.argsort(U, axis=1, kind="stable")


def draw_order_loop(N: int, seed: Any = SEED, b: int = B) -> np.ndarray:
    """The documented per-draw semantics, one draw at a time: the reference the vectorised draw must equal bit for bit."""
    rng = np.random.default_rng(seed)
    return np.stack([np.argsort(rng.random(N), kind="stable") for _ in range(b)])


def assert_draw_equal(N: int, fill: str = "C", b: int = 500) -> None:
    if not np.array_equal(draw_order(N, b=b, fill=fill), draw_order_loop(N, b=b)):
        raise PartCError(f"[DRAW] vectorised draw != row-by-row draw at N {N}")


class YearNull:
    def __init__(self, q: np.ndarray, seed: Any = SEED, b: int = B, replace: bool = False):
        self.N = len(q)
        self.total = int(q.sum())
        self.q_hash = hashlib.sha256(q.tobytes()).hexdigest()
        self.cs = np.cumsum(q[draw_order(self.N, seed, b, replace)], axis=1) if self.N else np.zeros((b, 0), np.int64)

    def sums(self, n: int) -> np.ndarray:
        return self.cs[:, n - 1] if n > 0 else np.zeros(self.cs.shape[0], np.int64)


_BOOT: dict[int, np.ndarray] = {}


def boot_idx(b: int) -> np.ndarray:
    if b not in _BOOT:
        _BOOT[b] = np.random.default_rng(list(BOOT_SEED)).integers(0, b, size=(N_BOOT, b))
    return _BOOT[b]


def p95_se(x: np.ndarray) -> float:
    qs = np.quantile(x[boot_idx(len(x))], 0.95, axis=1)
    return float(np.std(qs, ddof=1))


def ranks(obs: int, null: np.ndarray) -> tuple[float, float, float]:
    le, lt = float(np.mean(null <= obs)), float(np.mean(null < obs))
    return le, lt, (le + lt) / 2


def year_stats(net: np.ndarray, q: np.ndarray) -> dict[str, Any]:
    N = len(net)
    tot = int(q.sum()) / QSCALE
    sd = float(np.std(net, ddof=1)) if N > 1 else float("nan")
    t = tot / (sd * math.sqrt(N)) if N > 1 and sd > 0 else float("nan")
    return {"n_trades": N, "net_usd": tot, "mean_net": tot / N if N else float("nan"), "sd_net": sd, "t_total": t,
            "net_positive": bool(tot > 0), "denominator_unstable": bool(tot > 0 and not (t >= T_STABLE))}


def test_window(q: np.ndarray, mask: np.ndarray, yn: YearNull) -> dict[str, Any]:
    if yn.N != len(q) or yn.total != int(q.sum()) or yn.q_hash != hashlib.sha256(q.tobytes()).hexdigest():
        raise PartCError("[NULL] the null's pool is not this year's trades")
    N, n = len(q), int(mask.sum())
    obs, tot = int(q[mask].sum()), yn.total
    r: dict[str, Any] = {"n_trades": n, "share_trades": n / N if N else float("nan"), "net_usd": obs / QSCALE,
                         "net_outside_usd": (tot - obs) / QSCALE,
                         "mean_net_in": obs / QSCALE / n if n else float("nan"),
                         "mean_net_out": (tot - obs) / QSCALE / (N - n) if N - n else float("nan"),
                         "degenerate": bool(n == N)}
    if n == 0:
        r.update(verdict="EMPTY", verdict_se="EMPTY", share_net=None)
        return r
    null = yn.sums(n)
    le, lt, mid = ranks(obs, null)
    nd = null / QSCALE
    se_d = p95_se(nd)
    r.update(rank=le, rank_lt=lt, rank_mid=mid, tie_sensitive=bool(lt < RANK_BAR <= le),
             null_p50_usd=float(np.median(nd)), null_p95_usd=float(np.quantile(nd, 0.95)), null_p95_se_usd=se_d)
    if tot <= 0:
        r.update(share_net=None, verdict="UNDEFINED", verdict_se="UNDEFINED",
                 note="the year's net <= 0: shares undefined; the rank is on the dollar sum")
        return r
    share = obs / tot
    ns = null / tot
    p95 = float(np.quantile(ns, 0.95))
    se = p95_se(ns)
    v = "CONCENTRATED" if (le >= RANK_BAR and share >= SHARE_BAR) else "NOT_CONCENTRATED"
    within = bool(abs(share - p95) <= 2 * se)
    r.update(share_net=share, null_p50_share=float(np.median(ns)), null_p95_share=p95, null_p95_se_share=se,
             p95_margin_share=share - p95, margin_within_2se=within, verdict=v,
             verdict_se="UNRESOLVED" if (share >= SHARE_BAR and within) else v)
    return r


def session_sums(sessions: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The line's trading sessions of the year (sorted), each session's exact int64 net, and each trade's session index."""
    S, inv = np.unique(np.asarray(sessions).astype(str), return_inverse=True)
    sn = np.zeros(len(S), np.int64)
    np.add.at(sn, inv, q)
    return S, sn, inv


def rotation_sums(sn: np.ndarray, i0: int, k: int, wrap: bool = True) -> np.ndarray:
    """Every circular shift of a block of k consecutive trading sessions: element s is the exact net of sessions
    i0+s .. i0+s+k-1 (mod M), s = 0..M-1, so element 0 is the window itself. `wrap=False` exists only for the canary (a block
    that runs off the year's end is truncated instead of wrapping)."""
    M = len(sn)
    if not 0 < k <= M + 1:
        raise PartCError(f"[ROTATION] block length {k} outside 1..{M + 1}")
    if wrap:
        base = np.roll(sn, -i0)                                   # element 0 = the window's first session
        ext = np.concatenate([base, base])
    else:
        ext = np.concatenate([sn[i0:], np.zeros(M + i0, np.int64)])
    cs = np.concatenate([np.zeros(1, np.int64), np.cumsum(ext)])
    return cs[k:k + M] - cs[:M]


def rotation_test(sessions: np.ndarray, q: np.ndarray, mask: np.ndarray, length_delta: int = 0, wrap: bool = True
                  ) -> dict[str, Any] | None:
    """The orchestrator's ruling 4 (beside the declared test, for the contiguous windows C2 and C3): the exact enumerated rotation
    null over the line's trading sessions of the year. `length_delta` and `wrap` exist only for the canaries."""
    if not mask.any():
        return None
    S, sn, inv = session_sums(sessions, q)
    idx = np.unique(inv[mask])
    if not np.array_equal(idx, np.arange(idx[0], idx[0] + len(idx))):
        raise PartCError("[ROTATION] the window is not a contiguous block of the line's trading sessions")
    if mask.sum() != np.isin(inv, idx).sum():
        raise PartCError("[ROTATION] the window holds only part of a session's trades")
    k = len(idx) + length_delta
    null = rotation_sums(sn, int(idx[0]), k, wrap=wrap)
    obs = int(q[mask].sum())
    if int(null[0]) != obs:
        raise PartCError(f"[ROTATION] the unshifted block's net != the window's (block length {k}, window {len(idx)} sessions)")
    tot = int(q.sum())
    le, lt, mid = ranks(obs, null)
    r = {"n_shifts": int(len(S)), "block_sessions": int(k), "rotation_rank": le, "rotation_rank_lt": lt, "rotation_rank_mid": mid,
         "null_p50_usd": float(np.median(null / QSCALE)), "null_p95_usd": float(np.quantile(null / QSCALE, 0.95)),
         "null_p95_se": 0.0, "exact": "every circular shift enumerated; SE 0"}
    if tot > 0:
        ns = null / tot
        r.update(null_p50_share=float(np.median(ns)), null_p95_share=float(np.quantile(ns, 0.95)))
    return r


def assert_rotation_whole_year(sessions: np.ndarray, q: np.ndarray, length_delta: int = 0, wrap: bool = True) -> None:
    """The whole-year block: every shift must carry the whole year's net exactly (identical shares)."""
    S, sn, _ = session_sums(sessions, q)
    null = rotation_sums(sn, 0, len(S) + length_delta, wrap=wrap)
    if not (null == int(q.sum())).all():
        raise PartCError(f"[ROTATION] the whole-year block's shifts differ ({len(np.unique(null))} distinct sums)")


def assert_share_guard(r: dict[str, Any], year_net: float) -> None:
    if year_net <= 0 and r.get("share_net") is not None:
        raise PartCError("[SHARE] a share was reported over a year whose net is <= 0")
    if year_net <= 0 and r.get("verdict") not in ("UNDEFINED", "EMPTY"):
        raise PartCError("[SHARE] a verdict was read over a year whose net is <= 0")


def assert_whole_year(q: np.ndarray, yn: YearNull, what: str) -> None:
    r = test_window(q, np.ones(len(q), bool), yn)
    if r["rank"] != 1.0:
        raise PartCError(f"[NULL] {what}: the whole-year window ranks {r['rank']}, not 1")
    if yn.total > 0 and r["share_net"] != 1.0:
        raise PartCError(f"[NULL] {what}: the whole-year window's share is {r['share_net']}, not 1")


# ================================================================================ the study
def windows_2022(line: str, tr: pd.DataFrame, fl: pd.DataFrame, thr: float) -> dict[str, tuple[np.ndarray, bool]]:
    s = tr["session"].to_numpy().astype(str)
    w = {"C1_X8": ((fl["X8"] == 1).to_numpy(), True), "C1_FOMC": ((fl["fomc"] == 1).to_numpy(), True),
         "C2_war": ((fl["war"] == 1).to_numpy(), True), "C3_pre": (s < ERA, True), "C3_post": (s >= ERA, True)}
    if line == "L4":
        w["C4_X12p90"] = ((fl["X12"] >= thr).fillna(False).to_numpy(bool), True)
        w["C1_X8_macro_only"] = (((fl["fomc"] == 1) | (fl["cpi"] == 1) | (fl["empsit"] == 1)).to_numpy(), False)
    return w


def assert_c3_partition(tr: pd.DataFrame, pre: np.ndarray, post: np.ndarray) -> None:
    if (pre & post).any() or not (pre | post).all():
        raise PartCError("[C3] the two halves do not partition the year's trades")


def x12_reference(panel: pd.DataFrame) -> dict[str, Any]:
    ho = panel.loc["HO"]
    ref = ho.loc[(ho.index >= REF_LO) & (ho.index <= REF_HI), "X12"]
    n_nan = int(ref.isna().sum())
    ref = ref.dropna().to_numpy(float)
    edges = np.quantile(ref, np.arange(1, 10) / 10)
    return {"p90": float(np.quantile(ref, 0.90)), "deciles_edges": edges.tolist(), "n_sessions": int(len(ref)),
            "n_nan_dropped": n_nan, "span": [REF_LO, REF_HI], "method": "numpy quantile, linear interpolation"}


def x12_decile(x: float, edges: list[float]) -> int | None:
    return None if (x is None or math.isnan(x)) else int(1 + np.searchsorted(np.asarray(edges), x, side="right"))


def prepare(panel_shift: int = 0) -> dict[str, Any]:
    df = DL.load_lines()                      # validates the seal, the rows and every s.1 known answer
    panel = DC.load_conditioners()
    assert_seal(df["session"], "line table")
    assert_seal(panel.index.get_level_values("session"), "conditioner panel")
    ev = read_events()
    fl = join_flags(df, panel, shift=panel_shift)
    n_audit = join_audit(df, fl, ev, panel)
    fomc = assert_fomc_2022(panel)
    return {"df": df, "panel": panel, "flags": fl, "events": ev, "n_join_audited": n_audit, "fomc_2022": fomc}


def study(prep: dict[str, Any], log: Callable[..., None] = P, b: int = B) -> dict[str, Any]:
    df, fl, panel = prep["df"], prep["flags"], prep["panel"]
    xr = x12_reference(panel)
    thr = xr["p90"]
    out: dict[str, Any] = {}
    for line in LINES:
        t0 = time.time()
        L = df[df["line"] == line]
        F = fl.loc[L.index]
        yr = L["session"].str[:4]
        res: dict[str, Any] = {"root": ROOT_OF[line], "years": {}}
        for y in sorted(yr.unique()):
            m = (yr == y).to_numpy()
            T, FT = L[m], F[m]
            q = quantize(T["net_usd"].to_numpy())
            assert_right_quantity(q, T)
            ys = year_stats(T["net_usd"].to_numpy(float), q)
            ys["gross_usd"] = float(T["gross_usd"].sum())
            yn = YearNull(q, b=b)
            assert_whole_year(q, yn, f"{line} {y}")
            if y == YEAR:
                W = windows_2022(line, T, FT, thr)
                assert_c3_partition(T, W["C3_pre"][0], W["C3_post"][0])
            else:
                W = {"C1_X8": ((FT["X8"] == 1).to_numpy(), True), "C1_FOMC": ((FT["fomc"] == 1).to_numpy(), True)}
            wr = {}
            for k, (mask, read) in W.items():
                r = test_window(q, mask, yn)
                assert_share_guard(r, ys["net_usd"])
                r["read"] = read
                if y == YEAR and k in ROTATION_WINDOWS:
                    r["rotation_null"] = rotation_test(T["session"].to_numpy(), q, mask)
                if ys["denominator_unstable"] and r.get("share_net") is not None:
                    r["flag"] = "denominator_unstable: the year's net t < 2, the share is unstable"
                wr[k] = r
            if y == YEAR:
                ys["fomc_sessions_traded"] = sorted(set(T.loc[(FT["fomc"] == 1).to_numpy(), "session"]))
                if line == "L4":
                    ys["x12_nan_trades"] = int(FT["X12"].isna().sum())
            res["years"][y] = {"year": ys, "windows": wr}
        # 2022's ten largest trades by net (stable: ties keep session order)
        m22 = (yr == YEAR).to_numpy()
        T, FT = L[m22], F[m22]
        order = np.argsort(-T["net_usd"].to_numpy(float), kind="stable")[:10]
        top = []
        for j, i in enumerate(order, 1):
            row = {"rank": j, "session": T["session"].iat[i], "side": int(T["side"].iat[i]),
                   "net_usd": float(T["net_usd"].iat[i]), "gross_usd": float(T["gross_usd"].iat[i]),
                   "era": "post" if T["session"].iat[i] >= ERA else "pre"}
            for k in ("X8", "fomc", "cpi", "empsit", "eia_wpsr", "war"):
                row[k] = int(FT[k].iat[i])
            if line == "L4":
                row["X12_decile_vs_2016_2021"] = x12_decile(float(FT["X12"].iat[i]), xr["deciles_edges"])
            top.append(row)
        res["top10_2022"] = top
        res["top10_share_of_2022_net"] = (float(T["net_usd"].to_numpy(float)[order].sum()) / res["years"][YEAR]["year"]["net_usd"]
                                          if res["years"][YEAR]["year"]["net_usd"] > 0 else None)
        out[line] = res
        log(f"  {line}: {len(res['years'])} years tested, {time.time() - t0:.1f} s")
    return {"lines": out, "x12_reference": xr}


# ================================================================================ output
def clean(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def provenance() -> dict[str, Any]:
    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    return {"runner_sha256": sha(Path(__file__).resolve()),
            "lines_cache_sha256": json.loads(DL.META.read_text(encoding="utf-8")).get("table_csv_sha256"),
            "conditioners_cache_sha256": json.loads(DC.CACHE_META.read_text(encoding="utf-8")).get("sha256"),
            "events_csv": {"size": EVENTS.stat().st_size, "mtime_ns": EVENTS.stat().st_mtime_ns}}


def print_summary(res: dict[str, Any]) -> None:
    P(f"\nX12 90th percentile (HO, {REF_LO}..{REF_HI}, n {res['x12_reference']['n_sessions']}): {res['x12_reference']['p90']:.6g}")
    for line, r in res["lines"].items():
        y = r["years"][YEAR]["year"]
        P(f"\n{line} ({r['root']}) 2022: n {y['n_trades']}, net ${y['net_usd']:,.2f}, t {y['t_total']:.2f}"
          f"{'  [DENOMINATOR UNSTABLE]' if y['denominator_unstable'] else ''}{'' if y['net_positive'] else '  [NET <= 0]'}")
        for k, w in r["years"][YEAR]["windows"].items():
            if w["verdict"] == "EMPTY":
                P(f"   {k:17s} n 0: EMPTY")
                continue
            sh = "   n/a" if w.get("share_net") is None else f"{w['share_net']:6.1%}"
            P(f"   {k:17s} n {w['n_trades']:3d} ({w['share_trades']:5.1%})  net {w['net_usd']:10,.2f}  share {sh}  rank "
              f"{w['rank']:.4f}  p50 {w.get('null_p50_share', float('nan')):.3f} p95 {w.get('null_p95_share', float('nan')):.3f}"
              f" (se {w.get('null_p95_se_share', float('nan')):.3f})  {w['verdict']}"
              f"{'' if w['verdict_se'] == w['verdict'] else ' / ' + w['verdict_se']}{'' if w['read'] else '  (beside)'}")
            ro = w.get("rotation_null")
            if ro:
                P(f"   {'':17s} rotation ({ro['n_shifts']} shifts of {ro['block_sessions']} sessions): rank {ro['rotation_rank']:.4f}"
                  f"  p50 {ro.get('null_p50_share', float('nan')):.3f} p95 {ro.get('null_p95_share', float('nan')):.3f} (exact)")


def run() -> int:
    if OUT.exists():
        P(f"REFUSED: {OUT.relative_to(REPO)} exists (run-once)")
        return 2
    t0 = time.time()
    P("[run] the self-test first")
    if selftest() != 0:
        P("REFUSED: the self-test failed")
        return 3
    t1 = time.time()
    prep = prepare()
    res = study(prep)
    doc = {"what": "D722 Part C: event windows (2022 net split over C1-C4, random-draw null)", "spec": SPEC,
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "config": {"year": YEAR, "draws": B, "seed": SEED, "boot_resamples_p95_se": N_BOOT, "boot_seed": list(BOOT_SEED),
                      "rank": "P(null sum <= window sum)", "concentrated": f"rank >= {RANK_BAR} and share >= {SHARE_BAR}",
                      "unresolved": "share >= 0.25 and |share - null p95| <= 2 SE (CLAUDE.md nulls rule)",
                      "denominator_unstable": f"year net > 0 and t = sum/(sd sqrt N) < {T_STABLE}",
                      "era_split": f"pre < {ERA} <= post", "war": list(WAR), "sums": "exact int64 nano-dollars"},
           "fomc_2022": prep["fomc_2022"], "join_audited_trades": prep["n_join_audited"],
           "x12_reference": res["x12_reference"], "lines": res["lines"], "provenance": provenance(),
           "wall_s": {"selftest": round(t1 - t0, 1), "study": round(time.time() - t1, 1)},
           "notes": ["No GEX value is carried. L3's top-10 dates are short-gamma sessions by construction (D699's gate); dates "
                     "only, as D699's committed top-5.",
                     "The null draws TRADES, not sessions: L3 carries several trades on some sessions, and C2/C3 are contiguous "
                     "blocks, so a window's trades may be more alike than a random draw (anti-conservative there)."]}
    OUT.write_text(json.dumps(clean(doc), indent=1), encoding="utf-8")
    print_summary(res)
    P(f"\nwrote {OUT.relative_to(REPO)}; wall {time.time() - t0:.1f} s")
    return 0


# ================================================================================ selftest
def selftest() -> int:
    t0 = time.time()
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except PartCError as e:
            fired.append(name)
            P(f"  RAISED  {name}: {str(e)[:150]}")
            return
        raise SystemExit(f"CANARY FAILED TO RAISE: {name}")

    P("[clean] real inputs")
    prep = prepare()
    df, panel, fl, ev = prep["df"], prep["panel"], prep["flags"], prep["events"]
    P(f"  seal ok; join audit ok on {prep['n_join_audited']} trades; 2022 FOMC sessions per root: "
      f"{ {r: v['n'] for r, v in prep['fomc_2022'].items()} } (unscheduled {prep['fomc_2022']['ES']['unscheduled']})")
    xr = x12_reference(panel)
    P(f"  X12 p90 over HO {REF_LO}..{REF_HI} ({xr['n_sessions']} sessions, {xr['n_nan_dropped']} NaN dropped): {xr['p90']:.6g}")
    for line in LINES:
        T = df[(df["line"] == line) & (df["session"].str[:4] == YEAR)]
        q = quantize(T["net_usd"].to_numpy())
        assert_right_quantity(q, T)
        yn = YearNull(q)
        assert_whole_year(q, yn, line)
        W = windows_2022(line, T, fl.loc[T.index], xr["p90"])
        assert_c3_partition(T, W["C3_pre"][0], W["C3_post"][0])
        assert_rotation_whole_year(T["session"].to_numpy(), q)
    P("  every line's 2022: net quantised exactly, net != gross, whole-year window rank 1 share 1, C3 halves partition, "
      "whole-year rotation block identical on every shift")

    # the vectorised draw == the row-by-row draw, bit for bit (the chunk == whole analogue; nothing fans out)
    for N in (1, 66, 246):
        assert_draw_equal(N)
    a1 = np.cumsum(np.arange(246, dtype=np.int64)[draw_order(246, b=3000)], axis=1)
    a2 = np.concatenate([np.cumsum(np.arange(246, dtype=np.int64)[o], axis=1)
                         for o in np.array_split(draw_order_loop(246, b=3000), 7)])
    if not np.array_equal(a1, a2):
        raise PartCError("[DRAW] chunked cumsum != whole")
    P("  draws: vectorised == row-by-row bit-identical (N 1, 66, 246); chunked cumsum == whole")

    P("[synthetic] the null")
    rs = np.random.default_rng([722, 7])
    # (1) a random-subset window: ranks ~ uniform over 200 replications (KS p > 0.01, mean rank_mid in 0.5 +- 0.06)
    t1 = time.time()

    def uniform_ranks(pool_shift: float) -> np.ndarray:
        out = []
        for r in range(N_SYN_REPS):
            g = np.random.default_rng([722, 1, r])
            x = g.standard_t(3, 250) * 40.0 + 5.0
            win = np.zeros(250, bool)
            win[g.choice(250, 40, replace=False)] = True
            q = quantize(x)
            pool = q if pool_shift == 0 else quantize(x + pool_shift * 40.0)   # canary: the null drawn from another year's pool
            yn = YearNull(pool, seed=[722, 2, r])
            out.append(ranks(int(q[win].sum()), yn.sums(40))[2])
        return np.asarray(out)

    def check_uniform(rk: np.ndarray) -> float:
        p = float(stats.kstest(rk, "uniform").pvalue)
        if p <= 0.01 or abs(rk.mean() - 0.5) > 0.06:
            raise PartCError(f"[NULL] random-window ranks are not uniform: KS p {p:.3g}, mean {rk.mean():.3f}")
        return p

    rk = uniform_ranks(0.0)
    p_ks = check_uniform(rk)
    dec = np.histogram(rk, bins=10, range=(0, 1))[0].tolist()
    P(f"  random window (N 250 t3 trades, n 40, {N_SYN_REPS} reps x {B} draws): KS p {p_ks:.3f}, mean rank {rk.mean():.3f}, "
      f"deciles {dec}, share of reps rank >= 0.95: {np.mean(rk >= 0.95):.3f}  [{time.time() - t1:.1f} s]")
    # (2) a biased window (planted extra P&L) is detected
    x = rs.standard_t(3, 250) * 40.0 + 20.0          # a clearly positive year (t ~ 4), so the -$60 canary keeps net > 0
    win = np.zeros(250, bool)
    win[rs.choice(250, 40, replace=False)] = True

    def detected(xx: np.ndarray) -> dict[str, Any]:
        q = quantize(xx)
        r = test_window(q, win, YearNull(q))
        if not (r["verdict"] == "CONCENTRATED" and r["verdict_se"] == "CONCENTRATED"):
            raise PartCError(f"[NULL] the planted window is not detected: rank {r['rank']:.4f}, share {r.get('share_net')}")
        return r

    xb = x.copy()
    xb[win] += 60.0
    rb = detected(xb)
    P(f"  planted +$60 a trade on 40 of 250: rank {rb['rank']:.4f}, share {rb['share_net']:.3f} (p95 {rb['null_p95_share']:.3f}) "
      f"-> {rb['verdict']}")
    qx = quantize(x)
    ru = test_window(qx, win, YearNull(qx))
    P(f"  the same window unplanted (information only; a random window is CONCENTRATED at ~5 % x P(share >= 25 %)): rank "
      f"{ru['rank']:.4f}, share {ru['share_net']:.3f}, year t {year_stats(x, qx)['t_total']:.2f} -> {ru['verdict']}")
    # (3) a year whose net <= 0: no share, verdict UNDEFINED, rank on the dollar sum still reported
    xn = x - 45.0
    qn = quantize(xn)
    rn = test_window(qn, win, YearNull(qn))
    assert_share_guard(rn, int(qn.sum()) / QSCALE)
    if rn["verdict"] != "UNDEFINED" or rn["share_net"] is not None or not (0 <= rn["rank"] <= 1):
        raise PartCError("[SHARE] a net <= 0 year was not handled")
    P(f"  a year with net ${int(qn.sum()) / QSCALE:,.0f}: verdict {rn['verdict']}, share None, dollar rank {rn['rank']:.3f}")
    def check_denominator(xx: np.ndarray, want: bool) -> dict[str, Any]:
        ys_ = year_stats(xx, quantize(xx))
        if not ys_["net_positive"] or ys_["denominator_unstable"] != want:
            raise PartCError(f"[SHARE] denominator flag wrong: net {ys_['net_usd']:.2f}, t {ys_['t_total']:.2f}, "
                             f"unstable {ys_['denominator_unstable']}, wanted {want}")
        return ys_

    xz = x - x.mean() + 0.2          # a positive but thin year: t ~ 0.08
    xs = x - x.mean() + 20.0         # a clear year: t ~ 8
    a_, b_ = check_denominator(xz, True), check_denominator(xs, False)
    P(f"  denominator flag: thin year t {a_['t_total']:.2f} -> unstable; clear year t {b_['t_total']:.2f} -> stable")

    P("[canaries] each must RAISE")
    plant = df.iloc[[0]].copy()
    plant["session"] = "2024-01-02"
    must_raise("seal: a planted 2024 trade", lambda: assert_seal(pd.concat([df, plant])["session"], "line table"))
    pp = panel.iloc[[0]].copy()
    pp.index = pd.MultiIndex.from_tuples([("ES", "2024-01-02")], names=panel.index.names)
    must_raise("seal: a planted 2024 panel row", lambda: assert_seal(pd.concat([panel, pp]).index.get_level_values("session"), "panel"))
    ev2 = dict(ev)
    ev2["2024-01-31"] = {"FOMC"}
    must_raise("seal: a planted 2024 calendar row", lambda: join_audit(df, fl, ev2, panel))
    for sh in (1, -1):
        must_raise(f"join: every trade joined to the session {sh:+d}",
                   lambda sh=sh: join_audit(df, join_flags(df, panel, shift=sh), ev, panel))
    fl_x = fl.copy()
    i_ho = np.flatnonzero((df["root"] == "HO").to_numpy())[5]
    fl_x.iloc[i_ho, fl_x.columns.get_loc("X12")] = fl_x["X12"].iat[i_ho + 1]
    must_raise("join: one HO trade's X12 from its neighbour", lambda: join_audit(df, fl_x, ev, panel))
    q22 = quantize(df.loc[(df["line"] == "L1") & (df["session"].str[:4] == YEAR), "net_usd"].to_numpy())
    must_raise("null: whole-year window under with-replacement draws",
               lambda: assert_whole_year(q22, YearNull(q22, replace=True), "L1 with replacement"))
    must_raise("null: random-window ranks with the null drawn from a shifted (wrong-year) pool",
               lambda: check_uniform(uniform_ranks(0.3)))
    must_raise("null: the pool guard (another year's trades)",
               lambda: test_window(q22, np.ones(len(q22), bool), YearNull(q22[:-1])))
    xneg = x.copy()
    xneg[win] -= 60.0
    must_raise("null: a window planted with -$60 a trade is not 'detected'", lambda: detected(xneg))
    must_raise("draw: a column-major key fill checked against row-by-row", lambda: assert_draw_equal(66, fill="F"))
    must_raise("share: a thin year not flagged unstable", lambda: check_denominator(xz, False))
    must_raise("quantise: a cent grid breaks the exact-sum bound", lambda: quantize(df["net_usd"].to_numpy(), scale=1e2))
    T1 = df[(df["line"] == "L1") & (df["session"].str[:4] == YEAR)]
    must_raise("right-quantity: the gross scored as the net",
               lambda: assert_right_quantity(quantize(T1["gross_usd"].to_numpy()), T1))
    pf = panel.copy()
    k = pf.index[(pf.index.get_level_values("session") == prep["fomc_2022"]["NQ"]["sessions"][3])
                 & (pf.index.get_level_values("root") == "NQ")]
    pf.loc[k, "fomc"] = 0
    must_raise("FOMC: one 2022 FOMC session dropped on NQ", lambda: assert_fomc_2022(pf))
    must_raise("share: a share reported over a net <= 0 year", lambda: assert_share_guard({**rn, "share_net": -0.4}, -1.0))
    must_raise("share: a verdict read over a net <= 0 year",
               lambda: assert_share_guard({**rn, "verdict": "CONCENTRATED"}, -1.0))
    Tb = T1.copy()
    Tb.iloc[0, Tb.columns.get_loc("session")] = ERA
    sb = Tb["session"].to_numpy().astype(str)
    must_raise("C3: the era's first session counted in both halves",
               lambda: assert_c3_partition(Tb, sb <= ERA, sb >= ERA))
    s1 = T1["session"].to_numpy()
    q1 = quantize(T1["net_usd"].to_numpy())
    must_raise("rotation: a block that does not wrap at year end (whole-year block)",
               lambda: assert_rotation_whole_year(s1, q1, wrap=False))
    must_raise("rotation: a whole-year block one session short", lambda: assert_rotation_whole_year(s1, q1, length_delta=-1))
    # synthetic sessions (two trades on some, as L3 has), so no real window value is computed or printed
    gs = np.random.default_rng([722, 11])
    ss = np.array(sorted([f"2022-{m:02d}-{d:02d}" for m in range(1, 13) for d in (3, 10, 17, 24)] * 2))[::3]
    qs_ = quantize(gs.standard_t(3, len(ss)) * 40.0 + 20.0)
    blk = (ss >= "2022-03-01") & (ss <= "2022-04-30")
    rotation_test(ss, qs_, blk)                                   # the clean case passes
    must_raise("rotation: a block one session too long", lambda: rotation_test(ss, qs_, blk, length_delta=1))
    must_raise("rotation: a block one session short", lambda: rotation_test(ss, qs_, blk, length_delta=-1))
    must_raise("rotation: a non-contiguous window", lambda: rotation_test(ss, qs_, blk | (ss >= "2022-11-01")))

    # the whole study, end to end, on SYNTHETIC P&L over the real trade rows (sessions, roots, flags real; net replaced by noise,
    # K2_ES's 2022 pushed below zero to exercise the UNDEFINED path): proves --run's code path and its JSON, computes no real result
    P("[synthetic study] every code path of --run on noise P&L (1,000 draws)")
    t2 = time.time()
    g = np.random.default_rng([722, 9])
    dfs = df.copy()
    dfs["net_usd"] = g.standard_t(3, len(dfs)) * 30.0 + 3.0
    neg = ((dfs["line"] == "K2_ES") & (dfs["session"].str[:4] == YEAR)).to_numpy()
    dfs.loc[neg, "net_usd"] -= 40.0
    dfs["gross_usd"] = dfs["net_usd"] + dfs["cost_usd"]
    res = study({**prep, "df": dfs}, log=lambda *a: None, b=1000)
    vc: dict[str, int] = {}
    for line, r in res["lines"].items():
        Tn = dfs[(dfs["line"] == line) & (dfs["session"].str[:4] == YEAR)]
        yw = r["years"][YEAR]
        w = yw["windows"]
        if w["C3_pre"]["n_trades"] + w["C3_post"]["n_trades"] != len(Tn) or \
                abs(w["C3_pre"]["net_usd"] + w["C3_post"]["net_usd"] - yw["year"]["net_usd"]) > 1e-6 or \
                abs(yw["year"]["net_usd"] - float(Tn["net_usd"].sum())) > 1e-6 or \
                w["C1_FOMC"]["n_trades"] > w["C1_X8"]["n_trades"] or len(r["top10_2022"]) != min(10, len(Tn)):
            raise PartCError(f"[STUDY] {line}: an internal identity fails on the synthetic study")
        ro = {k: w[k].get("rotation_null") for k in ROTATION_WINDOWS}
        M = Tn["session"].nunique()
        if any(w[k]["n_trades"] and (ro[k] is None or ro[k]["n_shifts"] != M or not 0 < ro[k]["rotation_rank"] <= 1)
               for k in ROTATION_WINDOWS) or \
                sum((ro[k] or {}).get("block_sessions", 0) for k in ("C3_pre", "C3_post")) != M:
            raise PartCError(f"[STUDY] {line}: the rotation nulls are missing or inconsistent")
        if line == "L4" and not ("C4_X12p90" in w and "C1_X8_macro_only" in w and w["C1_X8_macro_only"]["read"] is False):
            raise PartCError("[STUDY] L4's C4 or its beside line is missing")
        for yy in r["years"].values():
            for ww in yy["windows"].values():
                vc[ww["verdict"]] = vc.get(ww["verdict"], 0) + 1
    if res["lines"]["K2_ES"]["years"][YEAR]["windows"]["C1_X8"]["verdict"] != "UNDEFINED":
        raise PartCError("[STUDY] a net <= 0 year did not read UNDEFINED")
    json.dumps(clean(res), allow_nan=False)
    P(f"  ran {sum(vc.values())} window tests over {len(res['lines'])} lines; verdicts on noise {dict(sorted(vc.items()))}; "
      f"C3 halves sum to the year, FOMC within X8, top-10 lists full, JSON has no NaN  [{time.time() - t2:.1f} s]")
    P(f"\nSELFTEST PASS: clean case passes; {len(fired)} canaries raised; wall {time.time() - t0:.1f} s")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
