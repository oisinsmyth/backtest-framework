"""D793: D791's gold China-open model for the joint vault run (programme slot 11, by amendment).
Spec: docs/decisions/D793-PRE-REG-gold-china-open-model-for-the-joint-vault.md.

    python scripts/vault_d793_gold_china_open_model.py --selftest             # SYSTEM interpreter (databento, pyarrow)
    python scripts/vault_d793_gold_china_open_model.py --rehearse             # in-sample, once
    uv run --no-sync python scripts/vault_d793_gold_china_open_model.py --crosscheck-sklearn   # numpy ridge == sklearn
    python scripts/vault_d793_gold_china_open_model.py --power                # in-sample, once
    python scripts/vault_d793_gold_china_open_model.py --dry-vault            # the vault path on 2023 (in-sample) inputs
    python scripts/vault_d793_gold_china_open_model.py --freeze               # once; registers slot 11
    python scripts/vault_d793_gold_china_open_model.py --vault --principals-word "..."   # the joint run only

The model: D791's 36 features (the 40 less month sine/cosine, weekday and the US clock), each scaled by its empirical
CDF among the 1,697 in-sample sessions (minus 0.5; missing -> 0), a ridge (alpha 100, intercept) on the percentile
rank of the taker gross, fitted ONCE on 2016-2023 and frozen; take a session when its score exceeds the 2/3 quantile
of the in-sample scores. The ridge is solved in closed form in numpy (sklearn's centred Cholesky solution), proven
equal to sklearn in --crosscheck-sklearn, so the vault needs no sklearn. The vault mode points D765/D769/D770/D786/
D790/D791's own functions at data/joint_run/d793/ and lifts their seal to the vault end, in this process and in every
worker process; it re-derives the in-sample features from the vault inputs and refuses unless they equal D791's
cache row for row.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")
SPEC = REPO / "docs" / "decisions" / "D793-PRE-REG-gold-china-open-model-for-the-joint-vault.md"
REHEARSAL = REPO / "data" / "vault_d793_rehearsal.json"
POWER = REPO / "data" / "vault_d793_power.json"
CROSS = REPO / "data" / "vault_d793_sklearn_crosscheck.json"
FROZEN = REPO / "data" / "FROZEN_vault_d793_gold_china_open_model.json"
RESULT = REPO / "data" / "vault_d793_result.json"
DRY = REPO / "data" / "vault_d793_dry_run.json"
JR = MAIN / "data" / "joint_run" / "d793"
ALPHA_RIDGE = 100.0
CALENDAR = ("month_sin", "month_cos", "weekday", "est_clock")
SEAL = "2024-01-01"
VAULT_START, VAULT_END = "2024-01-02", "2026-09-18"
TAKER_COST = 5.93
G0_MIN, T_G1 = 60, 1.2816
TEST_YEARS = ("2018", "2019", "2020", "2021", "2022", "2023")
KNOWN = {"intercept_round4": -0.0041, "threshold_round4": 0.0117, "wf_oos_rho": 0.0590, "wf_passive_n": 479,
         "wf_passive_net_round2": 4.80, "n_candidates": 1697}
FAMILY = "gold China-open model (MGC, D791 ridge)"
AMENDMENT = 'D793 §0: an eleventh family by amendment (the principal: "Put it in slot 11")'
SEED, N_BOOT = 793, 5000


class D793Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D793Error(msg)


# ================================================================================ the model (numpy, frozen form)
def scale_fit(train: np.ndarray) -> list[np.ndarray]:
    """The 36 sorted training vectors (finite values only): the frozen scaler."""
    return [np.sort(train[np.isfinite(train[:, j]), j]) for j in range(train.shape[1])]


def scale_apply(X: np.ndarray, srt: list[np.ndarray]) -> np.ndarray:
    """D791's rank_scale with the training CDF: searchsorted(right) / n - 0.5; missing -> 0."""
    out = np.zeros(X.shape)
    for j, s in enumerate(srt):
        ok = np.isfinite(X[:, j])
        if len(s) >= 20:
            out[ok, j] = np.searchsorted(s, X[ok, j], side="right") / len(s) - 0.5
    return out


def target(g: np.ndarray) -> np.ndarray:
    return pd.Series(g).rank().to_numpy() / len(g) - 0.5


def ridge_fit(A: np.ndarray, y: np.ndarray, alpha: float = ALPHA_RIDGE) -> tuple[np.ndarray, float]:
    """sklearn Ridge(alpha, fit_intercept=True) in closed form: centre, solve (Ac'Ac + alpha I) b = Ac'yc."""
    xm, ym = A.mean(axis=0), y.mean()
    Ac, yc = A - xm, y - ym
    b = np.linalg.solve(Ac.T @ Ac + alpha * np.eye(A.shape[1]), Ac.T @ yc)
    return b, float(ym - xm @ b)


def features_of(X: pd.DataFrame) -> list[str]:
    import explore_d791_oracle_patterns as M
    fs = [c for c in X.columns if c not in M.NON_FEATURES and c not in CALENDAR]
    need(len(fs) == 36, f"the model has 36 features, not {len(fs)}")
    return fs


def fit_full(X: pd.DataFrame) -> dict[str, Any]:
    fs = features_of(X)
    A = X[fs].to_numpy(float)
    srt = scale_fit(A)
    a = scale_apply(A, srt)
    b, c0 = ridge_fit(a, target(X["gross"].to_numpy(float)))
    pred = a @ b + c0
    return {"features": fs, "sorted": srt, "coef": b, "intercept": c0, "threshold": float(np.quantile(pred, 2 / 3)),
            "pred": pred}


def score(X: pd.DataFrame, model: dict[str, Any]) -> np.ndarray:
    a = scale_apply(X[model["features"]].to_numpy(float), model["sorted"])
    return a @ np.asarray(model["coef"], float) + float(model["intercept"])


def walk_forward_numpy(X: pd.DataFrame) -> dict[str, Any]:
    """D791's walk-forward (expanding, 2018-2023) in numpy, for the known answer (rho +0.0590; 479 at +$4.80)."""
    fs = features_of(X)
    yr = X["year"].to_numpy()
    A = X[fs].to_numpy(float)
    g = X["gross"].to_numpy(float)
    pred = np.full(len(X), np.nan)
    take = np.zeros(len(X), bool)
    for ty in TEST_YEARS:
        tr, te = yr < ty, yr == ty
        srt = scale_fit(A[tr])
        a_tr, a_te = scale_apply(A[tr], srt), scale_apply(A[te], srt)
        b, c0 = ridge_fit(a_tr, target(g[tr]))
        ptr = a_tr @ b + c0
        pred[te] = a_te @ b + c0
        take[te] = pred[te] > np.quantile(ptr, 2 / 3)
    return {"pred": pred, "take": take}


# ================================================================================ statistics and gates
def spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    ra, rb = pd.Series(a[m]).rank().to_numpy(), pd.Series(b[m]).rank().to_numpy()
    ra, rb = ra - ra.mean(), rb - rb.mean()
    return float(ra @ rb / math.sqrt((ra @ ra) * (rb @ rb)))


def tstat(v: np.ndarray) -> float:
    v = v[np.isfinite(v)]
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std(ddof=1) > 0 else float("nan")


def gates(take: np.ndarray, gross: np.ndarray, valid: np.ndarray, cost: float) -> dict[str, Any]:
    """G0 count, G1 mean net > 0 and t >= 1.2816, G2 mean gross above the exact rotation p95 of the take flag over the
    valid sessions. PASS / FAIL (mean net <= 0) / UNRESOLVED."""
    v = np.flatnonzero(valid)
    f, g = take[v], gross[v]
    k = f.astype(bool)
    n = int(k.sum())
    out: dict[str, Any] = {"n": n, "valid_sessions": int(len(v))}
    if n < 3:
        out.update({"reading": "UNRESOLVED", "why": "fewer than 3 trades"})
        return out
    net = g[k] - cost
    obs = float(g[k].mean())
    rot = np.array([g[np.roll(k, s)].mean() for s in range(1, len(v))]) if len(v) > 1 else np.array([obs])
    p95 = float(np.quantile(rot, 0.95))
    t = tstat(net)
    g0, g1, g2 = n >= G0_MIN, bool(net.mean() > 0 and t >= T_G1), bool(obs > p95)
    reading = "FAIL" if net.mean() <= 0 else ("PASS" if (g0 and g1 and g2) else "UNRESOLVED")
    out.update({"mean_gross": obs, "mean_net": float(net.mean()), "t_net": t, "rotation_p50": float(np.quantile(rot, 0.5)),
                "rotation_p95": p95, "rotation_rank": float((rot < obs).mean()), "G0": g0, "G1": g1, "G2": g2,
                "reading": reading})
    return out


# ================================================================================ the vault switch (in every process)
_VAULT_CFG: dict[str, Any] | None = None


def _load_shau_vault(path: Path | None = None) -> pd.DataFrame:
    """D786's load_shau with the path taken at CALL time and units widened for 2024-26 gold (CNY 200-1,500 a gram;
    D786's 200-600 rejects post-2024 prices). The parsing, the seal and the ordering checks are D786's."""
    import stage0_d786_china_open_five_filters as D86
    s = pd.read_csv(path or D86.SHAU, dtype={"date_beijing": str}, encoding="utf-8")
    D86.seal_days(s["date_beijing"], "SHAU benchmark")
    need(bool(s["shau_pm_cny_per_g"].between(200, 1500).all()), "units: a SHAU PM outside 200-1,500 CNY/g")
    need(bool(s["date_beijing"].is_monotonic_increasing), "SHAU: dates not ordered")
    return s


def _load_fix_vault() -> pd.DataFrame:
    """D769's load_fix with the units bound widened to 5.5-8.0 for 2024-26 (D769's 6.0-7.4 is in-sample)."""
    import stage0_d769_yuan_fix_residual as V
    f = pd.read_csv(V.FIX, usecols=["date", "usdcny_fix"], dtype={"date": str}, encoding="utf-8")
    need(bool((f["date"] < V.SEAL).all()), "seal: a fix past the vault seal")
    need(bool(f["usdcny_fix"].between(5.5, 8.0).all()), "units: a fix outside [5.5, 8.0]")
    return f


def apply_vault_patches(cfg: dict[str, Any]) -> None:
    """Point the lineage's own modules at the vault inputs and lift their seal to cfg['end'] (exclusive bound end+1).
    Called in the main process and, through the pool initializer, in every worker."""
    import stage0_d765_china_open as C
    import stage0_d769_yuan_fix_residual as V
    import stage0_d770_china_open_flow_passive as D7
    import stage0_d786_china_open_five_filters as D86
    import explore_d790_china_open_anatomy as A
    import explore_d791_oracle_patterns as M
    global _VAULT_CFG
    _VAULT_CFG = cfg
    seal = cfg["seal"]
    seal_ns = int(pd.Timestamp(seal, tz="UTC").value)
    for mod in (C, V, D86, A, M):
        mod.SEAL = seal
        if hasattr(mod, "SEAL_NS"):
            mod.SEAL_NS = seal_ns
    D7.SEAL_NS = seal_ns
    C.TMP = Path(cfg["bars_dir"])
    C.CAL = Path(cfg["holidays"])
    C.HI = cfg["end"]
    V.FIX = Path(cfg["fix"])
    D86.SHAU = Path(cfg["shau"])
    D86.load_shau = _load_shau_vault                        # its default path was bound at definition time
    V.load_fix = _load_fix_vault
    D7.PAID = Path(cfg["paid_dir"])
    M.CACHE = Path(cfg["cache_dir"])
    M.FEAT = M.CACHE / "features.csv.gz"
    M.META = M.CACHE / "meta.json"
    D86.WORKERS = cfg.get("workers", 6)
    D86._install_seal()                                     # D770's reader wrapped with the moved seal
    D86.ProcessPoolExecutor = _PatchedPool                  # every pool re-applies these patches in its workers


def _worker_init(cfg: dict[str, Any]) -> None:
    apply_vault_patches(cfg)


class _PatchedPool(cf.ProcessPoolExecutor):
    def __init__(self, max_workers: int | None = None, *args: Any, **kw: Any) -> None:
        need(_VAULT_CFG is not None, "the patched pool is used only after the vault patches")
        super().__init__(max_workers, initializer=_worker_init, initargs=(_VAULT_CFG,))


def build_features(cfg: dict[str, Any] | None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """D791's --build, either in-sample (cfg None: its own cache dir) or through the vault patches."""
    import stage0_d786_china_open_five_filters as D86
    import explore_d791_oracle_patterns as M
    if cfg is not None:
        apply_vault_patches(cfg)
        orig = D86.reproduce

        def reproduce_insample(B: dict[str, Any]) -> dict[str, Any]:
            """The vault build reproduces D767 / D770 on its own pre-2024 rows (identity), not on the whole."""
            e = B["e"]
            sess = B["sess"]
            Bi = dict(B)
            Bi["e"] = e[e.index < SEAL]
            Bi["sess"] = {k: s[s.index < SEAL] for k, s in sess.items()}
            return orig(Bi)
        D86.reproduce = reproduce_insample
        Path(cfg["cache_dir"]).mkdir(parents=True, exist_ok=True)
    rc = M.build()
    need(rc == 0, "D791's build failed")
    X = pd.read_csv(M.FEAT, dtype={"day": str, "year": str}, encoding="utf-8")
    with open(M.META, encoding="utf-8") as fh:
        meta = json.load(fh)
    return X, meta


def identity_check(X: pd.DataFrame, ref: pd.DataFrame) -> dict[str, Any]:
    """The rebuilt features on the in-sample sessions must equal D791's committed-cache rows exactly."""
    a = X[X["day"] < SEAL].reset_index(drop=True)
    need(len(a) == len(ref), f"identity: {len(a)} in-sample rows against the cache's {len(ref)}")
    need(bool((a["day"].to_numpy() == ref["day"].to_numpy()).all()), "identity: the in-sample days differ")
    bad = []
    for c in ref.columns:
        if c in ("day", "year"):
            continue
        x, y = a[c].to_numpy(float), ref[c].to_numpy(float)
        if not np.array_equal(np.isnan(x), np.isnan(y)) or not np.allclose(x[~np.isnan(x)], y[~np.isnan(y)], rtol=0, atol=1e-9):
            bad.append(c)
    need(not bad, f"identity: the rebuilt in-sample features differ from D791's cache in {bad}")
    return {"rows": len(a), "columns": len(ref.columns) - 2, "equal": True}


# ================================================================================ modes
def load_cache() -> pd.DataFrame:
    import explore_d791_oracle_patterns as M
    X = pd.read_csv(M.FEAT, dtype={"day": str, "year": str}, encoding="utf-8")
    need(len(X) == KNOWN["n_candidates"] and round(float(X["gross"].mean()), 2) == 3.14, "the cache is not D767's pool")
    need(bool((X["day"] < SEAL).all()), "seal: the in-sample cache reaches 2024")
    return X


def rehearse() -> int:
    need(not REHEARSAL.exists(), f"{REHEARSAL.name} exists: the rehearsal is run once")
    t0 = time.time()
    ref = load_cache()
    with tempfile_dir() as td:
        cfg = insample_cfg(Path(td))
        X, meta = build_features(cfg)
    ident = identity_check(X, ref)
    m = fit_full(ref)
    need(round(m["intercept"], 4) == KNOWN["intercept_round4"] and round(m["threshold"], 4) == KNOWN["threshold_round4"],
         f"the full fit does not reproduce the descriptive fit ({m['intercept']}, {m['threshold']})")
    wf = walk_forward_numpy(ref)
    oos = np.isin(ref["year"].to_numpy(), TEST_YEARS)
    rho = spearman(wf["pred"][oos], ref["gross"].to_numpy(float)[oos])
    cost_p = float(meta["cost_p"])
    gp = ref["gross_p"].to_numpy(float)
    k = wf["take"] & oos & ref["filled"].to_numpy(bool)
    need(round(rho, 4) == KNOWN["wf_oos_rho"] and int(k.sum()) == KNOWN["wf_passive_n"]
         and round(float((gp[k] - cost_p).mean()), 2) == KNOWN["wf_passive_net_round2"],
         f"the walk-forward does not reproduce D791 (rho {rho}, n {k.sum()})")
    take = m["pred"] > m["threshold"]
    filled = ref["filled"].to_numpy(bool)
    out = {"spec": SPEC.name, "mode": "rehearse (in-sample, once)", "identity_vs_d791_cache": ident,
           "cost_passive": cost_p, "features": m["features"],
           "full_fit": {"intercept": m["intercept"], "threshold": m["threshold"], "coef": dict(zip(m["features"], map(float, m["coef"]))),
                        "take_share": float(take.mean()),
                        "in_sample_passive_gates": gates(take, gp, filled, cost_p),
                        "in_sample_taker_gates": gates(take, ref["gross"].to_numpy(float), np.ones(len(ref), bool), TAKER_COST),
                        "note": "in-sample (the model was fitted on these sessions): a check of the scorer, not evidence"},
           "walk_forward": {"oos_rho": rho, "passive_n": int(k.sum()), "passive_net": float((gp[k] - cost_p).mean()),
                            "passive_t": tstat(gp[k] - cost_p)},
           "wall_s": round(time.time() - t0, 1)}
    with open(REHEARSAL, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("rehearsal:", {k2: out["walk_forward"][k2] for k2 in out["walk_forward"]}, "| identity", ident, f"| {out['wall_s']}s")
    return 0


def crosscheck_sklearn() -> int:
    from sklearn.linear_model import Ridge
    ref = load_cache()
    fs = features_of(ref)
    A = ref[fs].to_numpy(float)
    a = scale_apply(A, scale_fit(A))
    y = target(ref["gross"].to_numpy(float))
    b, c0 = ridge_fit(a, y)
    sk = Ridge(alpha=ALPHA_RIDGE).fit(a, y)
    dmax = float(max(np.abs(sk.coef_ - b).max(), abs(sk.intercept_ - c0)))
    need(dmax < 1e-9, f"numpy ridge differs from sklearn by {dmax}")
    import explore_d791_oracle_patterns as M
    ra, _ = M.rank_scale(A, A[:1])
    need(np.array_equal(ra, a), "the frozen scaler differs from D791's rank_scale on the training data")
    out = {"max_abs_difference_coef_intercept": dmax, "rank_scale_equal": True, "sklearn": __import__("sklearn").__version__}
    with open(CROSS, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("crosscheck:", out)
    return 0


def power() -> int:
    need(not POWER.exists(), f"{POWER.name} exists: the power run is run once")
    ref = load_cache()
    with open(REHEARSAL, encoding="utf-8") as fh:
        reh = json.load(fh)
    cost_p = float(reh["cost_passive"])
    wf = walk_forward_numpy(ref)
    yr = ref["year"].to_numpy()
    gp = ref["gross_p"].to_numpy(float)
    filled = ref["filled"].to_numpy(bool)
    per_year = (wf["take"] & np.isin(yr, TEST_YEARS) & filled).sum() / len(TEST_YEARS)
    years_in_window = (pd.Timestamp(VAULT_END) - pd.Timestamp(VAULT_START)).days / 365.25
    n_win = int(round(per_year * years_in_window))
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"n_window_expected": n_win, "per_year": float(per_year), "years": years_in_window, "bases": {}}
    for nm, ys in (("2018_2023", TEST_YEARS), ("2020_2023", ("2020", "2021", "2022", "2023")), ("2018_2019", ("2018", "2019"))):
        k = wf["take"] & np.isin(yr, ys) & filled
        net = gp[k] - cost_p
        mu = float(net.mean())
        res = {"base_n": int(k.sum()), "base_mean_net": mu}
        for frac in (1.0, 0.75, 0.5, 0.25, 0.0):
            shifted = net - (1 - frac) * mu
            draws = rng.choice(shifted, size=(N_BOOT, n_win), replace=True)
            m = draws.mean(axis=1)
            t = m / (draws.std(axis=1, ddof=1) / math.sqrt(n_win))
            res[f"P_G0_G1_at_{int(frac * 100)}pct"] = float(((m > 0) & (t >= T_G1)).mean()) if n_win >= G0_MIN else 0.0
        out["bases"][nm] = res
    sd = float(np.std(gp[wf["take"] & np.isin(yr, TEST_YEARS) & filled] - cost_p, ddof=1))
    out["analytic"] = {f"{int(f * 100)}pct": float(0.5 * math.erfc((T_G1 - f * 4.80 / (sd / math.sqrt(n_win))) / math.sqrt(2)))
                       for f in (1.0, 0.5, 0.0)}
    out["analytic_sd"] = sd
    with open(POWER, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("power:", json.dumps(out, indent=1))
    return 0


class tempfile_dir:
    def __enter__(self) -> str:
        import tempfile
        self._d = tempfile.mkdtemp(prefix="d793_")
        return self._d

    def __exit__(self, *a: Any) -> None:
        import shutil
        shutil.rmtree(self._d, ignore_errors=True)


def insample_cfg(cache_dir: Path, end: str = "2023-12-29", seal: str = SEAL) -> dict[str, Any]:
    """The vault path pointed at the IN-SAMPLE inputs (the rehearsal's identity build and the dry run)."""
    return {"seal": seal, "end": end, "bars_dir": str(REPO / "temp" / "d765"),
            "holidays": str(REPO / "data" / "calendar" / "china_exchange_holidays.csv"),
            "fix": str(REPO / "data" / "fixtures" / "cny_central_parity.csv"),
            "shau": str(REPO / "data" / "fixtures" / "sge_shau_benchmark_2016_2023.csv"),
            "paid_dir": str(MAIN / "data" / "raw" / "databento" / "china_window_2016_2023"),
            "cache_dir": str(cache_dir), "workers": 6}


def vault_cfg() -> dict[str, Any]:
    return {"seal": (pd.Timestamp(VAULT_END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), "end": VAULT_END,
            "bars_dir": str(JR / "d765_cache"), "holidays": str(JR / "china_exchange_holidays.csv"),
            "fix": str(JR / "cny_central_parity.csv"), "shau": str(JR / "sge_shau_benchmark.csv"),
            "paid_dir": str(JR / "paid"), "cache_dir": str(JR / "features"), "workers": 6}


def frozen_files() -> list[Path]:
    s = REPO / "scripts"
    d = REPO / "docs" / "decisions"
    return [Path(__file__).resolve(), SPEC,
            d / "D791-EXPLORE-patterns-in-the-oracle-s-china-open-trades-scope.md",
            d / "D791-EXPLORE-RESULT-a-walk-forward-model-picks-the-winners.md",
            REPO / "data" / "explore_d791_oracle_patterns.json", REPO / "data" / "explore_d791_followup_calendar.json",
            REPO / "data" / "explore_d791_followup_overfit.json", REHEARSAL, POWER, CROSS,
            s / "stage0_d765_china_open.py", s / "stage0_d767_china_open_fade_filter.py",
            s / "stage0_d769_yuan_fix_residual.py", s / "stage0_d770_china_open_flow_passive.py",
            s / "stage0_d786_china_open_five_filters.py", s / "explore_d790_china_open_anatomy.py",
            s / "explore_d791_oracle_patterns.py"]


def lf_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_freeze() -> int:
    need(not FROZEN.exists(), f"{FROZEN.name} exists: the freeze is written once")
    for p in (REHEARSAL, POWER, CROSS):
        need(p.exists(), f"{p.name} missing: rehearse, cross-check and power before the freeze")
    ref = load_cache()
    m = fit_full(ref)
    with open(REHEARSAL, encoding="utf-8") as fh:
        reh = json.load(fh)
    need(abs(m["intercept"] - reh["full_fit"]["intercept"]) < 1e-12, "the freeze's fit differs from the rehearsal's")
    out = {"spec": SPEC.name, "family": FAMILY, "slot": 11, "amendment": AMENDMENT,
           "frozen_utc": pd.Timestamp.now(tz="UTC").isoformat(), "vault": [VAULT_START, VAULT_END],
           "features": m["features"], "coef": [float(v) for v in m["coef"]], "intercept": m["intercept"],
           "threshold": m["threshold"], "sorted_training": [[float(v) for v in s] for s in m["sorted"]],
           "cost_passive": float(reh["cost_passive"]), "cost_taker": TAKER_COST, "gates": {"G0_min": G0_MIN, "T_G1": T_G1},
           "known": KNOWN, "hashes": {str(p.relative_to(REPO)).replace("\\", "/"): lf_sha(p) for p in frozen_files()}}
    with open(FROZEN, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("frozen:", FROZEN.relative_to(REPO), "| features", len(out["features"]), "| threshold", round(out["threshold"], 6))
    return 0


def verify_freeze(path: Path = FROZEN, check_fit: bool = True) -> dict[str, Any]:
    need(path.exists(), "no freeze: the vault scorer refuses")
    with open(path, encoding="utf-8") as fh:
        fz = json.load(fh)
    drift = [k for k, h in fz["hashes"].items() if lf_sha(REPO / k) != h]
    need(not drift, f"freeze drift: {drift}")
    if not check_fit:
        return fz
    ref = load_cache()
    m = fit_full(ref)
    need(np.allclose(m["coef"], fz["coef"], rtol=0, atol=1e-12) and abs(m["intercept"] - fz["intercept"]) < 1e-12,
         "freeze drift: the refit coefficients differ from the frozen ones")
    return fz


def score_window(X: pd.DataFrame, fz: dict[str, Any], lo: str, hi: str) -> dict[str, Any]:
    model = {"features": fz["features"], "sorted": [np.asarray(s) for s in fz["sorted_training"]], "coef": fz["coef"],
             "intercept": fz["intercept"]}
    w = X[(X["day"] >= lo) & (X["day"] <= hi)].reset_index(drop=True)
    need(len(w) > 0, "no session in the window")
    need(bool((w["day"] <= hi).all()), "a row past the window's end")
    s = score(w, model)
    take = s > float(fz["threshold"])
    gp, g = w["gross_p"].to_numpy(float), w["gross"].to_numpy(float)
    filled = w["filled"].to_numpy(bool)
    yrs = w["day"].str[:4].to_numpy()
    out = {"window": [lo, hi], "sessions": int(len(w)), "take_share": float(take.mean()),
           "passive_PRIMARY": gates(take, gp, filled, float(fz["cost_passive"])),
           "taker_reported": gates(take, g, np.ones(len(w), bool), TAKER_COST),
           "rho_score_gross": spearman(s, g),
           "rho_rotation_p95": float(np.quantile([spearman(np.roll(s, k), g) for k in range(1, len(w))], 0.95)) if len(w) > 20 else None,
           "years_passive_net": {y: (float((gp[take & filled & (yrs == y)] - fz["cost_passive"]).mean())
                                     if (take & filled & (yrs == y)).any() else None) for y in sorted(set(yrs))},
           "long_short_passive_net": {nm: float((gp[take & filled & m] - fz["cost_passive"]).mean()) if (take & filled & m).any() else None
                                      for nm, m in (("long_fades", w["side_long_fade"].to_numpy(float) == 1),
                                                    ("short_fades", w["side_long_fade"].to_numpy(float) == 0))}}
    return out


def dry_vault() -> int:
    """The whole vault path on IN-SAMPLE inputs, scored on 2023 (already read): proves the code, carries no evidence."""
    fz = verify_freeze() if FROZEN.exists() else None
    ref = load_cache()
    with tempfile_dir() as td:
        X, _ = build_features(insample_cfg(Path(td)))
    ident = identity_check(X, ref)
    if fz is None:
        m = fit_full(ref)
        fz = {"features": m["features"], "sorted_training": m["sorted"], "coef": m["coef"], "intercept": m["intercept"],
              "threshold": m["threshold"], "cost_passive": json.load(open(REHEARSAL, encoding="utf-8"))["cost_passive"]}
    out = {"DRY_RUN": "in-sample inputs, 2023 scored as a pseudo-window; NOT evidence", "identity": ident,
           "scored": score_window(X, fz, "2023-01-03", "2023-12-29")}
    with open(DRY, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("dry vault:", json.dumps(out["scored"]["passive_PRIMARY"], default=str))
    return 0


def vault(word: str | None) -> int:
    need(bool(word and word.strip()), "--vault needs --principals-word (the joint run, on the principal's word)")
    need(not RESULT.exists(), f"{RESULT.name} exists: the vault is read once")
    fz = verify_freeze()
    for k in ("d765_cache", "china_exchange_holidays.csv", "cny_central_parity.csv", "sge_shau_benchmark.csv", "paid"):
        need((JR / k).exists(), f"vault input missing: {JR / k} (JOINT_RUN_CHECKLIST D793 steps)")
    ref = load_cache()
    X, meta = build_features(vault_cfg())
    ident = identity_check(X, ref)
    need(abs(float(meta["cost_p"]) - float(fz["cost_passive"])) < 1e-12, "the vault build's passive cost differs from the frozen one")
    need(bool((X["day"] <= VAULT_END).all()), "a vault row past 2026-09-18")
    out = {"spec": SPEC.name, "principals_word": word, "identity": ident, "scored": score_window(X, fz, VAULT_START, VAULT_END),
           "split_from_2025_03_01": score_window(X, fz, "2025-03-01", VAULT_END)}
    with open(RESULT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("VAULT D793:", out["scored"]["passive_PRIMARY"]["reading"], json.dumps(out["scored"]["passive_PRIMARY"], default=str))
    return 0


def selftest() -> int:
    t0 = time.time()
    rng = np.random.default_rng(1)
    # the scaler: the training CDF, missing -> 0
    tr = rng.normal(size=(500, 3))
    srt = scale_fit(tr)
    a = scale_apply(tr, srt)
    need(a.min() > -0.5 and a.max() <= 0.5, "scaler range")
    te = np.array([[np.nan, 1e9, -1e9]])
    need(np.allclose(scale_apply(te, srt), [[0.0, 0.5, -0.5]]), "scaler: missing / extremes")
    # the ridge in closed form recovers a planted linear relation
    A = rng.normal(size=(2000, 5))
    y = A @ np.array([0.3, -0.2, 0, 0, 0.1]) + rng.normal(scale=0.5, size=2000)
    b, c0 = ridge_fit(A, y, 1.0)
    need(np.allclose(b, [0.3, -0.2, 0, 0, 0.1], atol=0.05), f"ridge: planted coefficients {b}")
    # the gates: a planted edge passes, a shuffled one does not, a loser fails
    n = 600
    gross = rng.standard_t(3, n) * 30
    take = (gross + rng.normal(scale=40, size=n)) > 10
    gp = gates(take, gross, np.ones(n, bool), 3.0)
    need(gp["reading"] == "PASS", f"gates: a planted edge read {gp['reading']}")
    gs = gates(rng.permutation(take), gross - 8.0, np.ones(n, bool), 3.0)
    need(gs["reading"] == "FAIL", f"gates: a losing book read {gs['reading']}")
    # the vault refuses without a word
    try:
        vault(None)
    except D793Error:
        pass
    else:
        raise D793Error("--vault ran without the principal's word")
    # the freeze check fires on a moved file (a synthetic freeze hashing a file under temp/)
    d = REPO / "temp" / "d793_selftest"
    d.mkdir(parents=True, exist_ok=True)
    f, fzp = d / "hashed.txt", d / "freeze.json"
    f.write_text("coef 0.1\n", encoding="utf-8")
    fzp.write_text(json.dumps({"hashes": {"temp/d793_selftest/hashed.txt": lf_sha(f)}}), encoding="utf-8")
    verify_freeze(fzp, check_fit=False)
    f.write_text("coef 0.1000001\n", encoding="utf-8")
    try:
        verify_freeze(fzp, check_fit=False)
    except D793Error:
        pass
    else:
        raise D793Error("freeze: a moved hashed file was not caught")
    # the vault loaders read their path at call time and accept 2024-26 units; the in-sample loader would refuse them
    g = d / "shau.csv"
    pd.DataFrame({"date_beijing": ["2025-06-02"], "shau_am_cny_per_g": [770.0], "shau_pm_cny_per_g": [771.0]}).to_csv(
        g, index=False, encoding="utf-8")
    import stage0_d786_china_open_five_filters as D86
    saved = D86.SEAL
    try:
        D86.SEAL = "2026-09-19"
        need(len(_load_shau_vault(g)) == 1, "the vault SHAU loader refused a 2025 price")
        try:
            D86.load_shau(g)
        except D86.D786Error:
            pass
        else:
            raise D793Error("D786's in-sample SHAU loader accepted 771 CNY/g (its units bound moved?)")
    finally:
        D86.SEAL = saved
    # the window filter refuses a row past the end
    X = pd.DataFrame({"day": ["2026-09-17", "2026-09-18"]})
    need(bool((X[(X["day"] >= VAULT_START) & (X["day"] <= VAULT_END)]["day"] <= VAULT_END).all()), "window filter")
    # the in-sample cache is D767's pool and the full fit reproduces the descriptive fit
    ref = load_cache()
    m = fit_full(ref)
    need(round(m["intercept"], 4) == KNOWN["intercept_round4"] and round(m["threshold"], 4) == KNOWN["threshold_round4"],
         "the full fit does not reproduce the descriptive fit")
    print(f"selftest OK ({time.time() - t0:.0f}s)", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    for f in ("selftest", "rehearse", "crosscheck-sklearn", "power", "dry-vault", "freeze", "vault"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.crosscheck_sklearn:
        return crosscheck_sklearn()
    if a.power:
        return power()
    if a.dry_vault:
        return dry_vault()
    if a.freeze:
        return write_freeze()
    if a.vault:
        return vault(a.principals_word)
    ap.print_help()
    return 1


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())
