"""D707: F2 for the joint vault run -- the ES last-hour continuation at one MES, taken when the walk-forward composite
of the prior hour's relative size and today's realised volatility ranks in the top fifth. Spec:
docs/decisions/D707-PRE-REG-f2-last-hour-filter-for-the-joint-vault.md (b6b42cd4); the principal: "The F2 construction
is now a candidate, add it to the big vault run."

    uv run python scripts/vault_d707_last_hour_f2.py --selftest
    uv run python scripts/vault_d707_last_hour_f2.py --known-answer     # in-sample: D618, D705's F2, the path equality
    uv run python scripts/vault_d707_last_hour_f2.py --power            # the test's size and the window power (s.5)
    uv run python scripts/vault_d707_last_hour_f2.py --freeze           # once
    uv run python scripts/vault_d707_last_hour_f2.py --vault --principals-word "..."   # the joint run only

THE CONSTRUCTION (s.1): D618's ES frame (>= 380 one-minute RTH bars; the price at hh:mm is the close of the bar starting
a minute earlier). F5 = 1e4 ln(P15:30 / P14:30); candidates are non-roll sessions with finite prices and F5 != 0; trade
sign(F5) 15:30 -> 16:00, gross = sign x (P16:00 - P15:30) x $5, net = gross - $4.42. a = |F5| / sigma_F5 (the previous
252 sessions of the frame, >= 60, shifted one); b = ln sqrt(sum of 5-minute r^2, bp) 09:30 -> 15:30 (D702's rv_today).
TAKE when tiers((tiers(a) + tiers(b)) / 2) >= 0.8 (D671's tiers: the share of the previous 250 finite values strictly
below, in candidate order). No parameter is fitted. THE TEST (D705 s.3): >= 30 trades on 2024-01-01 -> 2026-09-18, mean
net > 0 and one-sided NW(5) t >= 1.2816; promotion at t >= 2.576 (slot 7).
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage1_d703_last_hour_ep_filter as E  # noqa: E402

M702, D, C = E.Z, E.D, E.C
SPEC = REPO / "docs" / "decisions" / "D707-PRE-REG-f2-last-hour-filter-for-the-joint-vault.md"
FROZEN = REPO / "data" / "FROZEN_vault_d707_last_hour_f2.json"
POWER_OUT = REPO / "data" / "vault_d707_power.json"
VAULT_OUT = REPO / "data" / "vault_d707_last_hour_f2_result.json"
HASHED = ("stage0_d618_sharpened_ladder.py", "diag_d702_last_hour_oracle_mes.py", "stage1_d703_last_hour_ep_filter.py",
          "stage0_d671_break_construction.py", "stage0_d691_iv_size.py")
IN_END, UNSEEN_FROM, VAULT_FROM, VAULT_END = "2023-12-29", "2024-01-01", "2025-03-01", "2026-09-18"
COST, MES_USD, Q = 4.42, 5.0, 0.8
T_PASS, T_PROMO, MIN_TRADES = 1.2816, 2.576, 30
N_UNSEEN_TRADES, WIN_CANDIDATES = 120, 640
KNOWN_D618 = {"n": 1960, "mean_pts": 0.6795, "hit": 0.4929}
KNOWN_D705_F2 = {"trades": 252, "mean_net": 13.208968253968253}


class D707Error(RuntimeError):
    pass


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ================================================================================ the build (s.1)
@contextlib.contextmanager
def raised_cut(m618: Any, end: str) -> Iterator[None]:
    """Move D618's module cut to `end` for one call, and put it back whatever happens."""
    old = (m618.IN_TO, m618.RESERVED_FROM)
    nxt = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    m618.IN_TO, m618.RESERVED_FROM = end, nxt
    try:
        yield
    finally:
        m618.IN_TO, m618.RESERVED_FROM = old


def frame(end: str = IN_END, vault_open: bool = False) -> pd.DataFrame:
    """Every candidate from 2016-01-04 through `end`, with gross, side, a, b. Nothing past 2023-12-29 unless the vault
    path opened it."""
    if end > IN_END and not vault_open:
        raise D707Error(f"seal: a build through {end} was asked for outside --vault")
    m618 = _load("m618", "stage0_d618_sharpened_ladder.py")
    with raised_cut(m618, end):
        S, _ = m618.load_es()
    if len(S) and S.index.max() > end:
        raise D707Error("seal: D618's frame holds a session past the cut")
    if not vault_open and (S.index >= UNSEEN_FROM).any():
        raise D707Error("seal: a session on or after 2024-01-01 reached the build")
    d = np.sign(S["F5"].to_numpy(float))
    pts = d * (S["P1600"] - S["P1530"]).to_numpy(float)
    ka = np.isfinite(pts) & ~S["roll"].to_numpy(bool)
    pre = (S.index <= IN_END)
    got = {"n": int((ka & pre).sum()), "mean_pts": float(pts[ka & pre].mean()), "hit": float((pts[ka & pre] > 0).mean())}
    if got["n"] != KNOWN_D618["n"] or abs(got["mean_pts"] - KNOWN_D618["mean_pts"]) > 5e-5 or abs(got["hit"] - KNOWN_D618["hit"]) > 5e-5:
        raise D707Error(f"known answer: {got} against D618 s.3c's {KNOWN_D618}")
    cand = ka & (d != 0)
    sig = E.sigma_f5(S["F5"])
    X = S[cand].copy()
    X["gross"] = d[cand] * (X["P1600"] - X["P1530"]).to_numpy(float) * MES_USD
    X["side"] = d[cand]
    X["a"] = (S["F5"].abs() / sig).reindex(X.index)
    b = pd.read_csv(m618.ES_1M, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= m618.IN_FROM) & (b["day"] <= end)]
    if not vault_open and (b["day"] >= UNSEEN_FROM).any():
        raise D707Error("seal: a bar on or after 2024-01-01 was read")
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(X.index)
    open_ = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(X.index)
    X["b"] = M702.rv_today(close, open_)
    step = max(1, len(X) // 25)
    sample = list(X.index[::step])
    M702.rv_audit(close, open_, X["b"], sample)
    E.sigma_audit(S["F5"], sig, sample)
    X.attrs["sessions_in_frame"] = int(len(S))
    X.attrs["d618_known"] = got
    return X


def f2(X: pd.DataFrame, q: float = Q) -> dict[str, np.ndarray]:
    a, b = X["a"].to_numpy(float), X["b"].to_numpy(float)
    ta, tb = C.tiers(a), C.tiers(b)
    tc = C.tiers((ta + tb) / 2)
    with np.errstate(invalid="ignore"):
        take = tc >= q
    return {"ta": ta, "tb": tb, "tc": tc, "take": take, "window": np.isfinite(ta) & np.isfinite(tc)}


def audit_tiers(X: pd.DataFrame, F: dict[str, np.ndarray]) -> None:
    idx = list(range(0, len(X), max(1, len(X) // 12)))
    C.tier_audit(F["ta"], X["a"].to_numpy(float), idx)
    C.tier_audit(F["tb"], X["b"].to_numpy(float), idx)
    C.tier_audit(F["tc"], (F["ta"] + F["tb"]) / 2, idx)


def take_hash(days: np.ndarray) -> str:
    return hashlib.sha256("\n".join(map(str, days)).encode("utf-8")).hexdigest()


def in_sample_answer(X: pd.DataFrame, F: dict[str, np.ndarray]) -> dict[str, Any]:
    """F2 on its own window through 2023-12-29: the numbers --vault re-proves on the extended build."""
    sess = X.index.to_numpy(str)
    k = F["take"] & F["window"] & (sess <= IN_END)
    net = X["gross"].to_numpy(float)[k] - COST
    return {"trades": int(k.sum()), "mean_net": float(net.mean()), "sum_net": float(net.sum()),
            "first_window_session": str(sess[F["window"]][0]), "take_sessions_sha256": take_hash(sess[k])}


# ================================================================================ the test (s.3)
def score(net: np.ndarray) -> dict[str, Any]:
    n = len(net)
    if n < MIN_TRADES:
        return {"trades": n, "verdict": "UNRESOLVED (fewer than 30 trades)"}
    t, se = D.nw_t(net)
    m = float(np.mean(net))
    return {"trades": n, "mean_net": m, "t_net_hac": t, "se": se,
            "verdict": "PASS" if (m > 0 and t >= T_PASS) else "FAIL",
            "programme_promotion": bool(m > 0 and t >= T_PROMO)}


def nw_t_rows(x: np.ndarray, lags: int = 5) -> np.ndarray:
    """D691's nw_t on every row of a 2-D array at once (the power's draws); equality with the loop is asserted."""
    n = x.shape[1]
    e = x - x.mean(axis=1, keepdims=True)
    v = np.einsum("ij,ij->i", e, e) / n
    for L in range(1, lags + 1):
        v = v + 2 * (1 - L / (lags + 1)) * np.einsum("ij,ij->i", e[:, L:], e[:, :-L]) / n
    return x.mean(axis=1) / np.sqrt(v / n)


# ================================================================================ reporting
def monthly_block_sharpe_se(daily: pd.Series, B: int = 2000, seed: int = 707) -> float:
    rng = np.random.default_rng(seed)
    months = daily.groupby(lambda s: s[:7])
    blocks = [g.to_numpy(float) for _, g in months]
    out = []
    for _ in range(B):
        x = np.concatenate([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        sd = x.std(ddof=1)
        if sd > 0:
            out.append(x.mean() / sd * math.sqrt(252))
    return float(np.std(out, ddof=1))


def report(X: pd.DataFrame, F: dict[str, np.ndarray], lo: str, hi: str, arm: pd.Series | None) -> dict[str, Any]:
    sess = X.index.to_numpy(str)
    span = F["window"] & (sess >= lo) & (sess <= hi)
    g = X["gross"].to_numpy(float)
    wd = sess[span]
    years = (pd.Timestamp(str(wd[-1])) - pd.Timestamp(str(wd[0]))).days / 365.25
    take = F["take"] & span
    side = X["side"].to_numpy(float)
    bk = E.book(g, take, sess, side, years, arm)
    bk_all = E.book(g, span, sess, side, years, arm)
    daily = pd.Series(np.where(take, g - COST, 0.0)[span], index=wd)
    nt = g[take] - COST
    ys = pd.Series(nt, index=sess[take]).groupby(lambda s: s[:4]).sum()
    yrs = sorted({d[:4] for d in wd})
    tot = float(nt.sum())
    return {"span": [str(wd[0]), str(wd[-1])], "candidates": int(span.sum()), "years": years,
            "F2": bk, "take_everything": bk_all,
            "daily_sharpe_monthly_block_se": monthly_block_sharpe_se(daily) if take.sum() > 10 else None,
            "d705_d_reported": {"max_year_share": float(ys.max() / tot) if tot > 0 else None,
                                "max_year": str(ys.idxmax()) if len(ys) else None,
                                "positive_years": f"{int(sum(ys.get(y, 0.0) > 0 for y in yrs))} of {len(yrs)}"},
            "mean_gross_vs_2c": [float(g[take].mean()) if take.any() else None, 2 * COST]}


# ================================================================================ modes
def known_answer() -> dict[str, Any]:
    t0 = time.time()
    E.sign_audit()
    X = frame(IN_END)
    F = f2(X)
    audit_tiers(X, F)
    # D705's path: D702's build, then D705's family; the take flags and the gross must agree session by session
    F705 = _load("f705", "stage1_d705_relative_size_filters.py")
    Y = E.inputs()["X"]
    if not (Y.index.equals(X.index)):
        raise D707Error("the runner's candidates differ from D702's")
    if not np.array_equal(Y["gross"].to_numpy(float), X["gross"].to_numpy(float)):
        raise D707Error("the runner's gross differs from D702's")
    A = np.column_stack([Y["f5z"].to_numpy(float), Y["rv_today"].to_numpy(float), Y["G_SUM"].to_numpy(float)])
    fam = F705.family(A)
    for nm, mine, theirs in (("a", X["a"], Y["f5z"]), ("b", X["b"], Y["rv_today"])):
        if not np.array_equal(mine.to_numpy(float), theirs.to_numpy(float), equal_nan=True):
            raise D707Error(f"input {nm} differs from D702's")
    if not np.array_equal(fam["take"]["F2"], F["take"]):
        raise D707Error("the runner's F2 take flags differ from D705's")
    W705 = F705.window(fam, A[:, 2])
    k = F["take"] & W705
    got = {"trades": int(k.sum()), "mean_net": float((X["gross"].to_numpy(float)[k] - COST).mean())}
    if got["trades"] != KNOWN_D705_F2["trades"] or abs(got["mean_net"] - KNOWN_D705_F2["mean_net"]) > 1e-9:
        raise D707Error(f"D705's F2: {got} against {KNOWN_D705_F2}")
    own = in_sample_answer(X, F)
    arm = E.P694.arm_daily()
    arm = arm[arm.index <= IN_END]
    rep = report(X, F, "2016-01-01", IN_END, arm)
    return {"d618_known_answer": X.attrs["d618_known"], "d705_F2_on_d705_window": got,
            "path_equality": "candidates, gross, a, b and the F2 take flags equal D702's build + D705's family exactly",
            "in_sample_own_window": own, "in_sample_report": rep, "runtime_min": round((time.time() - t0) / 60, 2)}


def power(ka: dict[str, Any] | None = None) -> dict[str, Any]:
    X = frame(IN_END)
    F = f2(X)
    sess = X.index.to_numpy(str)
    g = X["gross"].to_numpy(float)
    W = F["window"]
    net_all = g - COST
    take = F["take"] & W
    M = float(net_all[take].mean())
    # (1) the test's size: F2's in-sample net demeaned, resampled
    rng = np.random.default_rng(7071)
    pool = net_all[take] - M
    draws = pool[rng.integers(0, len(pool), (20000, N_UNSEEN_TRADES))]
    t = nw_t_rows(draws)
    for i in (0, 1, 777, 19999):
        if not math.isclose(t[i], D.nw_t(draws[i])[0], rel_tol=1e-12, abs_tol=1e-12):
            raise D707Error("the vectorised NW t differs from D691's nw_t")
    m = draws.mean(axis=1)
    size = float(((m > 0) & (t >= T_PASS)).mean())
    promo0 = float(((m > 0) & (t >= T_PROMO)).mean())
    # (2) contiguous windows of the unseen span's size
    wi = np.flatnonzero(W)
    starts = list(range(0, len(wi) - WIN_CANDIDATES + 1, 5))
    lines = {}
    for s_ in (1.0, 0.5, 0.25, 0.0):
        res = []
        for st in starts:
            idx = wi[st:st + WIN_CANDIDATES]
            kk = idx[F["take"][idx]]
            x = net_all[kk] - (1 - s_) * M
            res.append(score(x))
        n_ = np.array([r["trades"] for r in res])
        lines[f"{int(s_ * 100)}pct"] = {"pass": float(np.mean([r["verdict"] == "PASS" for r in res])),
                                        "promotion": float(np.mean([bool(r.get("programme_promotion")) for r in res])),
                                        "unresolved": float(np.mean([r["verdict"].startswith("UNRESOLVED") for r in res])),
                                        "trades_median": float(np.median(n_)), "trades_p10_p90": [float(np.quantile(n_, 0.1)), float(np.quantile(n_, 0.9))]}
    first = [str(sess[wi[s]]) for s in (starts[0], starts[-1])]
    return {"effect_in_sample_mean_net": M, "in_sample_trades_own_window": int(take.sum()),
            "size_check": {"draws": 20000, "trades_a_draw": N_UNSEEN_TRADES, "pass_rate_at_zero": size,
                           "promotion_rate_at_zero": promo0, "bar": 0.12, "ok": bool(size <= 0.12)},
            "windows": {"candidates_a_window": WIN_CANDIDATES, "step": 5, "count": len(starts),
                        "independent_approx": round(len(wi) / WIN_CANDIDATES, 2), "first_and_last_start": first, "lines": lines},
            "note": "the windows overlap and 2022 sits in many of them, so the 0% line shows time concentration, not the test's size (s.5)"}


def vault(word: str | None) -> int:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10; D707 s.6)")
        return 2
    if not FROZEN.exists():
        raise D707Error("the D707 freeze is missing")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    if fz.get("runner_sha256") != sha(Path(__file__).resolve()) or fz.get("prereg_sha256") != sha(SPEC):
        raise D707Error("this runner or D707 has moved since the freeze")
    for p, h in fz["imported_unchanged"].items():
        if sha(REPO / "scripts" / p) != h:
            raise D707Error(f"{p} has moved since the freeze")
    if VAULT_OUT.exists():
        raise D707Error("F2's unseen span has already been scored; a second opening is refused")
    E.sign_audit()
    X = frame(VAULT_END, vault_open=True)
    F = f2(X)
    audit_tiers(X, F)
    # proof first: the extended build's in-sample part reproduces the frozen known answer (prefix stability)
    ka = in_sample_answer(X, F)
    want = fz["known_answer_in_sample_own_window"]
    if ka["trades"] != want["trades"] or ka["take_sessions_sha256"] != want["take_sessions_sha256"] or abs(ka["mean_net"] - want["mean_net"]) > 1e-9:
        raise D707Error(f"prefix stability: the extended build's in-sample part {ka} differs from the frozen {want}")
    sess = X.index.to_numpy(str)
    span = F["window"] & (sess >= UNSEEN_FROM) & (sess <= VAULT_END)
    k = F["take"] & span
    net = X["gross"].to_numpy(float)[k] - COST
    arm = E.P694.arm_daily()
    out = {"principals_word": word, "known_answer_reproduced": ka, "verdict": score(net),
           "parts": {nm: score(X["gross"].to_numpy(float)[F["take"] & F["window"] & (sess >= lo) & (sess <= hi)] - COST)
                     for nm, lo, hi in (("held_slice", UNSEEN_FROM, "2025-02-28"), ("vault", VAULT_FROM, VAULT_END))},
           "report": report(X, F, UNSEEN_FROM, VAULT_END, arm if len(arm) else None),
           "last_session_in_fixture": str(sess[-1])}
    VAULT_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k_: out[k_] for k_ in ("verdict", "parts", "last_session_in_fixture")}, indent=1, default=float))
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise D707Error(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
    pw = json.loads(POWER_OUT.read_text(encoding="utf-8"))
    if not pw["power"]["size_check"]["ok"]:
        raise D707Error("the size check failed (s.5): nothing is frozen; the principal is told")
    doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/vault_d707_last_hour_f2.py",
           "runner_sha256": sha(Path(__file__).resolve()),
           "imported_unchanged": {p: sha(REPO / "scripts" / p) for p in HASHED},
           "fixture_for_information": {"path": "data/fixtures/fut_ES_rth_1m.csv.gz",
                                       "sha256_at_freeze": hashlib.sha256((REPO / "data" / "fixtures" / "fut_ES_rth_1m.csv.gz").read_bytes()).hexdigest(),
                                       "note": "not verified at the vault run (it may be extended to 2026-09-18); the in-sample known answer is re-proved instead"},
           "params": {"q": Q, "tier_n": 250, "sigma_sessions": 252, "sigma_min": 60, "rv_grid": "5-minute, 09:30 -> 15:30",
                      "cost_usd_round_trip": COST, "size": "one MES", "t_pass": T_PASS, "t_promotion": T_PROMO,
                      "min_trades": MIN_TRADES, "nw_lags": 5},
           "known_answer_in_sample_own_window": pw["known_answer"]["in_sample_own_window"],
           "known_answer_d705_window": pw["known_answer"]["d705_F2_on_d705_window"],
           "power": pw["power"], "unseen": [UNSEEN_FROM, VAULT_END], "programme_slot": 7, "frozen_date": "2026-09-30",
           "instruction": "the principal, 2026-09-30: \"The F2 construction is now a candidate, add it to the big vault run.\""}
    FROZEN.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("prereg_sha256", "runner_sha256", "imported_unchanged", "known_answer_in_sample_own_window")}, indent=1))
    return 0


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: tuple = (D707Error,)) -> None:
        try:
            fn()
        except exc:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    E.sign_audit()
    rng = np.random.default_rng(707)
    g = rng.normal(15.0, 60.0, 120)
    if score(g)["verdict"] != "PASS":
        raise SystemExit("selftest: an injected edge did not PASS")
    noise = rng.normal(0.0, 90.0, (2000, 120))
    tt = nw_t_rows(noise)
    for i in (0, 5, 1999):
        if not math.isclose(tt[i], D.nw_t(noise[i])[0], rel_tol=1e-12, abs_tol=1e-12):
            raise SystemExit("selftest: nw_t_rows differs from nw_t")
    rate = float(((noise.mean(axis=1) > 0) & (tt >= T_PASS)).mean())
    if not 0.06 <= rate <= 0.14:
        raise SystemExit(f"selftest: noise PASSed {rate:.3f} of the time (about 0.10 expected)")
    if not score(g[:29])["verdict"].startswith("UNRESOLVED"):
        raise SystemExit("selftest: fewer than 30 trades did not read UNRESOLVED")
    if score(g - 1e3)["verdict"] != "FAIL":
        raise SystemExit("selftest: a negative net did not FAIL")
    if main(["--vault"]) != 2:
        raise SystemExit("selftest: --vault ran without the principal's word")
    must_raise("a build past 2023-12-29 outside --vault", lambda: frame(VAULT_END))
    v = rng.normal(size=600)
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(v, leak=True), v, [300, 450, 599]), (C.D671Error,))
    f5 = pd.Series(rng.normal(size=400), index=[f"d{i:04d}" for i in range(400)])
    E.sigma_audit(f5, E.sigma_f5(f5), list(f5.index[100::50]))
    must_raise("a sigma_F5 that includes today", lambda: E.sigma_audit(f5, E.sigma_f5(f5, leak=True), list(f5.index[100::50])), (E.D703Error,))
    days = [f"2019-01-{i:02d}" for i in range(1, 11)]
    cols = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in range(60) if (h, m) >= (9, 30)]
    close = pd.DataFrame(100 + np.cumsum(rng.normal(0, 0.05, (10, len(cols))), axis=1), index=days, columns=cols)
    open_ = pd.Series(100.0, index=days)
    close.loc[:, "15:34"] = close["15:34"] + 5.0
    M702.rv_audit(close, open_, M702.rv_today(close, open_), days)
    must_raise("a realised volatility that reads the bar starting 15:30",
               lambda: M702.rv_audit(close, open_, M702.rv_today(close, open_, include_1530_bar=True), days), (M702.D702Error,))
    # prefix stability of the rule on synthetic inputs: appending later candidates changes nothing earlier
    Xs = pd.DataFrame({"a": np.abs(rng.normal(size=900)), "b": rng.normal(size=900)}, index=[f"s{i:04d}" for i in range(900)])
    full, part = f2(Xs), f2(Xs.iloc[:700])
    for key in ("ta", "tb", "tc", "take"):
        if not np.array_equal(full[key][:700], part[key], equal_nan=True):
            raise SystemExit(f"selftest: {key} is not prefix-stable")
    # raised_cut moves the cut for one call and restores it even when the call raises
    fake = type(sys)("_fake618")
    fake.IN_TO, fake.RESERVED_FROM = IN_END, UNSEEN_FROM
    with contextlib.suppress(ValueError):
        with raised_cut(fake, VAULT_END):
            if (fake.IN_TO, fake.RESERVED_FROM) != (VAULT_END, "2026-09-19"):
                raise SystemExit("selftest: raised_cut did not move the cut")
            raise ValueError
    if (fake.IN_TO, fake.RESERVED_FROM) != (IN_END, UNSEEN_FROM):
        raise SystemExit("selftest: raised_cut did not restore the cut")
    print(f"selftest OK: {len(fired)} canaries fired: {fired}; PASS on an edge; noise PASSed {rate:.3f}; UNRESOLVED below 30; "
          "FAIL on a negative net; --vault refused without the word; nw_t_rows == nw_t; the rule is prefix-stable. "
          "D618's, D702's and D705's known answers need the fixtures and run in --known-answer.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault:
        return vault(a.principals_word)
    if a.freeze:
        return freeze()
    if a.known_answer or a.power:
        t0 = time.time()
        ka = known_answer()
        if a.known_answer:
            print(json.dumps({k: ka[k] for k in ("d618_known_answer", "d705_F2_on_d705_window", "in_sample_own_window")}, indent=1, default=float))
            return 0
        res = {"known_answer": ka, "power": power(ka), "runtime_min": round((time.time() - t0) / 60, 2)}
        POWER_OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"known": {k: ka[k] for k in ("d705_F2_on_d705_window", "in_sample_own_window")},
                          "size_check": res["power"]["size_check"], "windows": res["power"]["windows"]}, indent=1, default=float))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
