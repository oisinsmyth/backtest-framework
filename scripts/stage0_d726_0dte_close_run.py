"""D726 Stage 0: did daily 0DTE options end the last-half-hour continuation? Three premise checks on D722's K2
(take-everything 15:30 -> 16:00 on the sign of 14:30 -> 15:30), in-sample 2018-05-14 -> 2023-12-29, as pre-registered in
docs/decisions/D726-STAGE-0-PRE-REG-did-daily-0dte-end-the-close-run.md (e75ac90f).

    uv run python scripts/stage0_d726_0dte_close_run.py --selftest
    uv run python scripts/stage0_d726_0dte_close_run.py --run        # run-once: refuses if the output exists

S1  the era: e after 2022-05-16 against e over 2018-05-14 -> 2021-12-31 (week-block bootstrap, 10,000, seed 726).
S2  the weekday natural experiment: DiD = [e(no same-day PM expiry) - e(expiry)] before the date
    - [e(Tue, Thu) - e(Mon, Wed, Fri)] after it.
S3  the day's 0DTE dose after the date: Z = ln(V0 / F) less its median over the prior 20 defined sessions;
    Spearman(Z, u) against an exact circular-shift null.
e = sum(g) / sum(|g|) on gross dollars (D711-A1); u = D722's volatility-normalised gross. ES is read; NQ is beside.
Writes data/stage0_d726_0dte_close_run.json (aggregates only).
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import diag_d722_conditioners as DC  # noqa: E402
import diag_d722_lines as DL  # noqa: E402
from diag_d722_part_b import outcome_u  # noqa: E402

SEAL = "2024-01-01"
DATE = "2022-05-16"
START = "2018-05-14"
PRE_EX_END = "2021-12-31"
OPTIONS = REPO / "data" / "fixtures" / "fut_es_options_eod.csv.gz"
RTH_ES = REPO / "data" / "fixtures" / "fut_ES_rth_1m.csv.gz"
OUT = REPO / "data" / "stage0_d726_0dte_close_run.json"
SEED = 726
DRAWS = 10_000
CHUNK = 2_000
Z_WINDOW = 20
PLACEBO_MIN = 250
SE_FLOOR = 1e-9          # a bootstrap SE below this is degenerate (np.std of identical floats can be ~1e-17, not 0)
# the pre-registration's s.0 table: sessions with a same-day PM-settled ES option expiry, by era and weekday (Mon..Fri)
CAL_KNOWN = {"pre": [225, 36, 288, 24, 290], "post": [69, 84, 85, 83, 79]}


class D726Error(AssertionError):
    pass


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise D726Error(msg)


def seal(dates, what: str) -> None:
    d = pd.Series(np.asarray(dates, dtype=str))
    need(not (d >= SEAL).any(), f"[SEAL] {what}: a row dated >= {SEAL}")


# ------------------------------------------------------------------------------------------------ inputs
def read_options(path: Path = OPTIONS, plant: bool = False) -> pd.DataFrame:
    """Same-day-expiry rows only (expiry_date == session), filtered below the seal chunk by chunk."""
    parts = []
    for ch in pd.read_csv(path, usecols=["session", "expiry_date", "expiry_hhmm", "vol_to_1530"], dtype=str,
                          chunksize=2_000_000, encoding="utf-8"):
        ch = ch[ch["session"] < SEAL]
        parts.append(ch[ch["expiry_date"] == ch["session"]])
    x = pd.concat(parts, ignore_index=True)
    if plant:
        x = pd.concat([x, x.iloc[[0]].assign(session="2024-01-03", expiry_date="2024-01-03")], ignore_index=True)
    seal(x["session"], "options")
    x["pm"] = x["expiry_hhmm"] >= "15:30"
    x["v"] = pd.to_numeric(x["vol_to_1530"], errors="coerce").fillna(0.0)
    return x


def expiry_calendar(x: pd.DataFrame, include_am: bool = False) -> pd.DataFrame:
    """Per session: has a same-day PM expiry, and V0 = the PM same-day options' volume to 15:29."""
    use = x if include_am else x[x["pm"]]
    s = use.groupby("session")["v"].sum().rename("V0").to_frame()
    s["has_pm"] = True
    return s


def calendar_counts(cal: pd.DataFrame) -> dict[str, list[int]]:
    idx = pd.to_datetime(cal.index)
    out = {}
    for era, m in (("pre", idx < DATE), ("post", idx >= DATE)):
        wd = idx[m].dayofweek
        out[era] = [int((wd == k).sum()) for k in range(5)]
    return out


def read_futures_volume(path: Path = RTH_ES, plant: bool = False) -> pd.Series:
    """ES futures volume 09:30-15:29 per day (fut_ES_rth_1m), filtered below the seal chunk by chunk."""
    parts = []
    for ch in pd.read_csv(path, usecols=["day", "hhmm", "volume"], dtype={"day": str, "hhmm": str}, chunksize=2_000_000,
                          encoding="utf-8"):
        ch = ch[ch["day"] < SEAL]
        hh = ch["hhmm"].str.replace(":", "", regex=False).astype(int)
        parts.append(ch.loc[(hh >= 930) & (hh <= 1529), ["day", "volume"]])
    f = pd.concat(parts, ignore_index=True)
    if plant:
        f = pd.concat([f, pd.DataFrame({"day": ["2024-01-03"], "volume": [1.0]})], ignore_index=True)
    seal(f["day"], "ES futures volume")
    return f.groupby("day")["volume"].sum().astype(float)


def dose(V0: pd.Series, F: pd.Series, leak: bool = False) -> pd.Series:
    """Z = ln(V0/F) less the median of the prior Z_WINDOW defined values (strictly before the session)."""
    lr = np.log(V0 / F.reindex(V0.index)).replace([np.inf, -np.inf], np.nan).dropna().sort_index()
    base = lr.shift(-1) if leak else lr
    med = base.rolling(Z_WINDOW, min_periods=Z_WINDOW).median().shift(1)
    return (lr - med).dropna()


def dose_loop(V0: pd.Series, F: pd.Series) -> pd.Series:
    """Second implementation of `dose` by plain loop, never calling it."""
    vals = []
    for s in sorted(V0.index):
        f = F.get(s, np.nan)
        v = V0[s]
        if not (v > 0 and f > 0):
            continue
        vals.append((s, math.log(v / f)))
    out = {}
    for i, (s, x) in enumerate(vals):
        if i >= Z_WINDOW:
            out[s] = x - float(np.median([y for _, y in vals[i - Z_WINDOW:i]]))
    return pd.Series(out, dtype=float)


def k2_frame(root: str) -> pd.DataFrame:
    df = DL.load_lines()
    k = df[df["line"] == f"K2_{root}"].copy()
    seal(k["session"], f"K2_{root}")
    pan = DC.load_conditioners().reset_index()
    pan = pan[pan["root"] == root].set_index("session")
    k["sig20"] = pan["sig20"].reindex(k["session"]).to_numpy()
    need(np.isfinite(k["sig20"]).all(), f"[INPUT] K2_{root}: a session without sig20")
    k["u"] = outcome_u(k["gross_usd"], k["usd_pp"], k["entry_price"], k["sig20"], k["hold_min"])
    need((np.sign(k["u"]) == np.sign(k["gross_usd"])).all(), "[INPUT] u's sign differs from gross")
    k["dt"] = pd.to_datetime(k["session"])
    iso = k["dt"].dt.isocalendar()
    k["week"] = (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()
    k["wd"] = k["dt"].dt.dayofweek
    return k.reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ statistics
def eff(g: np.ndarray) -> float:
    a = np.abs(g).sum()
    return float(g.sum() / a) if a > 0 else float("nan")


def week_sums(g: np.ndarray, week: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, inv = np.unique(week, return_inverse=True)
    return np.bincount(inv, weights=g), np.bincount(inv, weights=np.abs(g))


def boot_eff(groups: list[tuple[np.ndarray, np.ndarray]], rng: np.random.Generator, draws: int = DRAWS,
             chunk: int = CHUNK) -> np.ndarray:
    """For each group (g, week): resample its weeks with replacement; returns draws x len(groups) efficiencies.
    The index matrices are drawn once per group (draw order fixed), and the gather-and-sum is chunked."""
    out = np.empty((draws, len(groups)))
    idx = []
    sums = []
    for g, w in groups:
        S, A = week_sums(g, w)
        sums.append((S, A))
        idx.append(rng.integers(0, len(S), size=(draws, len(S))))
    for j, (S, A) in enumerate(sums):
        I = idx[j]
        for lo in range(0, draws, chunk):
            b = I[lo:lo + chunk]
            out[lo:lo + chunk, j] = S[b].sum(axis=1) / A[b].sum(axis=1)
    return out


def s1(k: pd.DataFrame, rng: np.random.Generator) -> dict:
    s = k["session"]
    after = (s >= DATE).to_numpy()
    before_ex = ((s >= START) & (s <= PRE_EX_END)).to_numpy()
    before_in = ((s >= START) & (s < DATE)).to_numpy()
    g, w = k["gross_usd"].to_numpy(), k["week"].to_numpy()
    B = boot_eff([(g[after], w[after]), (g[before_ex], w[before_ex]), (g[before_in], w[before_in])], rng)
    de, de_in = eff(g[after]) - eff(g[before_ex]), eff(g[after]) - eff(g[before_in])
    se, se_in = float(np.std(B[:, 0] - B[:, 1], ddof=1)), float(np.std(B[:, 0] - B[:, 2], ddof=1))
    need(se > SE_FLOOR and se_in > SE_FLOOR, "[S1] a degenerate bootstrap SE")
    u = k["u"].to_numpy()
    # the placebo-date profile (reported only)
    order = np.argsort(s.to_numpy(), kind="mergesort")
    gs = g[order]
    ss = s.to_numpy()[order]
    cs, ca = np.cumsum(gs), np.cumsum(np.abs(gs))
    prof = []
    for i in range(PLACEBO_MIN, len(gs) - PLACEBO_MIN + 1):
        eb = cs[i - 1] / ca[i - 1]
        ea = (cs[-1] - cs[i - 1]) / (ca[-1] - ca[i - 1])
        prof.append((ss[i], ea - eb))
    pv = np.array([p[1] for p in prof])
    decl = [p for p in prof if p[0] >= DATE][0]
    return {"n_after": int(after.sum()), "n_before_ex2022": int(before_ex.sum()), "n_before_incl": int(before_in.sum()),
            "e_after": eff(g[after]), "e_before_ex2022": eff(g[before_ex]), "e_before_incl": eff(g[before_in]),
            "mean_u_after": float(u[after].mean()), "mean_u_before_ex2022": float(u[before_ex].mean()),
            "net_mean_after": float(k["net_usd"].to_numpy()[after].mean()),
            "net_mean_before_ex2022": float(k["net_usd"].to_numpy()[before_ex].mean()),
            "delta_e": de, "se": se, "z": de / se, "delta_e_incl_bulge_beside": de_in, "se_incl": se_in, "z_incl": de_in / se_in,
            "supports": bool(de < 0 and de / se <= -2.0),
            "placebo_profile_reported_only": {"n_dates": len(pv), "declared_split_first_session": decl[0],
                                              "declared_delta_e": float(decl[1]),
                                              "rank_of_declared_low_is_1": float((pv <= decl[1]).mean()),
                                              "min": float(pv.min()), "p05": float(np.percentile(pv, 5)),
                                              "p50": float(np.percentile(pv, 50))}}


def s2(k: pd.DataFrame, has_pm: set, rng: np.random.Generator) -> dict:
    s = k["session"]
    pre = ((s >= START) & (s < DATE)).to_numpy()
    post = (s >= DATE).to_numpy()
    ex = s.isin(has_pm).to_numpy()
    tt = k["wd"].isin([1, 3]).to_numpy()
    g, w = k["gross_usd"].to_numpy(), k["week"].to_numpy()
    cells = {"pre_noexp": pre & ~ex, "pre_exp": pre & ex, "post_tt": post & tt, "post_mwf": post & ~tt}
    need(all(m.sum() > 0 for m in cells.values()), "[S2] an empty cell")
    E = {c: eff(g[m]) for c, m in cells.items()}
    d_pre, d_post = E["pre_noexp"] - E["pre_exp"], E["post_tt"] - E["post_mwf"]
    did = d_pre - d_post
    need(abs(did - ((E["pre_noexp"] - E["pre_exp"]) - (E["post_tt"] - E["post_mwf"]))) < 1e-15, "[S2] the DiD identity")
    B = boot_eff([(g[m], w[m]) for m in cells.values()], rng)
    bd_pre, bd_post = B[:, 0] - B[:, 1], B[:, 2] - B[:, 3]
    se_did, se_pre, se_post = (float(np.std(v, ddof=1)) for v in (bd_pre - bd_post, bd_pre, bd_post))
    need(se_did > SE_FLOOR, "[S2] a degenerate bootstrap SE")
    u = k["u"].to_numpy()
    return {"n": {c: int(m.sum()) for c, m in cells.items()}, "e": E,
            "mean_u": {c: float(u[m].mean()) for c, m in cells.items()},
            "net_mean": {c: float(k["net_usd"].to_numpy()[m].mean()) for c, m in cells.items()},
            "delta_pre": d_pre, "se_pre": se_pre, "delta_post": d_post, "se_post": se_post,
            "did": did, "se_did": se_did, "z": did / se_did, "supports": bool(did / se_did >= 2.0)}


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def rotation(x: np.ndarray, y: np.ndarray) -> dict:
    """Exact circular-shift null: x shifted against y by every lag 1..N-1."""
    n = len(x)
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    obs = float(np.corrcoef(rx, ry)[0, 1])
    rho0 = float(np.corrcoef(np.roll(rx, 0), ry)[0, 1])
    need(abs(rho0 - obs) < 1e-12, "[S3] shift 0 differs from the observed rho")
    null = np.array([np.corrcoef(np.roll(rx, k), ry)[0, 1] for k in range(1, n)])
    return {"n": n, "rho": obs, "n_shifts": int(len(null)), "rank_low": float((null <= obs).mean()),
            "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95))}


def s3(k: pd.DataFrame, Z: pd.Series) -> dict:
    zk = Z.reindex(k["session"]).to_numpy()
    s = k["session"]
    post = (s >= DATE).to_numpy() & np.isfinite(zk)
    pre = ((s >= START) & (s < DATE)).to_numpy() & np.isfinite(zk)
    u = k["u"].to_numpy()
    r_post = rotation(zk[post], u[post])
    r_pre = rotation(zk[pre], u[pre])
    return {"after_date": r_post, "supports": bool(r_post["rho"] <= r_post["p05"]),
            "before_date_expiry_sessions_beside": r_pre,
            "n_post_sessions_without_dose": int(((s >= DATE).to_numpy() & ~np.isfinite(zk)).sum())}


def reading(sup1: bool, sup2: bool, sup3: bool) -> str:
    if sup2 and (sup1 or sup3):
        return "SUPPORTED"
    if sup1 or sup2 or sup3:
        return "PARTIAL"
    return "NOT SUPPORTED"


# ------------------------------------------------------------------------------------------------ run
def study() -> dict:
    t0 = time.time()
    x = read_options()
    cal = expiry_calendar(x)
    cc = calendar_counts(cal)
    need(cc == CAL_KNOWN, f"[CALENDAR] the expiry counts {cc} != the pre-registration's {CAL_KNOWN}")
    need(calendar_counts(expiry_calendar(x, include_am=True)) != CAL_KNOWN, "[CALENDAR] AM expiries change nothing")
    F = read_futures_volume()
    Z = dose(cal["V0"], F)
    Zl = dose_loop(cal["V0"], F)
    need(set(Z.index) == set(Zl.index) and np.allclose(Z.sort_index(), Zl.sort_index(), rtol=0, atol=1e-12),
         "[DOSE] the loop implementation disagrees")
    has_pm = set(cal.index)
    out = {"spec": "docs/decisions/D726-STAGE-0-PRE-REG-did-daily-0dte-end-the-close-run.md (e75ac90f)",
           "calendar_counts": cc, "dose_sessions": int(len(Z)), "roots": {}}
    for i, root in enumerate(("ES", "NQ")):
        k = k2_frame(root)
        rng = np.random.default_rng([SEED, i])
        r1, r2, r3 = s1(k, rng), s2(k, has_pm, rng), s3(k, Z)
        out["roots"][root] = {"n": int(len(k)), "S1": r1, "S2": r2, "S3": r3,
                              "reading": reading(r1["supports"], r2["supports"], r3["supports"]),
                              "read": root == "ES"}
    out["reading_ES"] = out["roots"]["ES"]["reading"]
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run() -> int:
    need(not OUT.exists(), f"[RUN] {OUT.name} exists: --run is run-once")
    res = study()
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(jsonable(res), fh, indent=1)
        fh.write("\n")
    for root, r in res["roots"].items():
        a, b, c = r["S1"], r["S2"], r["S3"]["after_date"]
        print(f"{root} ({'read' if r['read'] else 'beside'}): {r['reading']}")
        print(f"  S1 e after {a['e_after']:+.4f} vs before ex-2022 {a['e_before_ex2022']:+.4f}: delta {a['delta_e']:+.4f} "
              f"(SE {a['se']:.4f}, z {a['z']:+.2f}) supports {a['supports']}; incl. the bulge z {a['z_incl']:+.2f}")
        print(f"  S2 pre no-exp {b['e']['pre_noexp']:+.4f} vs exp {b['e']['pre_exp']:+.4f} (d {b['delta_pre']:+.4f}); "
              f"post Tu/Th {b['e']['post_tt']:+.4f} vs MWF {b['e']['post_mwf']:+.4f} (d {b['delta_post']:+.4f}); "
              f"DiD {b['did']:+.4f} SE {b['se_did']:.4f} z {b['z']:+.2f} supports {b['supports']}")
        print(f"  S3 rho {c['rho']:+.4f} (n {c['n']}), rotation rank {c['rank_low']:.3f}, p05 {c['p05']:+.4f} "
              f"supports {r['S3']['supports']}")
    print(f"wrote {OUT.relative_to(REPO)} in {res['wall_s']} s")
    return 0


# ------------------------------------------------------------------------------------------------ selftest
def expect_raise(fn, what: str, fired: list) -> None:
    try:
        fn()
    except D726Error as e:
        print(f"  RAISES  {what}: {str(e)[:140]}")
        fired.append(what)
        return
    raise SystemExit(f"SELFTEST FAILED: the canary did not raise: {what}")


def selftest() -> int:
    t0 = time.time()
    fired: list = []
    print("[clean] real inputs (no statistic printed)")
    x = read_options()
    cal = expiry_calendar(x)
    need(calendar_counts(cal) == CAL_KNOWN, "[CALENDAR] counts differ")
    F = read_futures_volume()
    Z, Zl = dose(cal["V0"], F), dose_loop(cal["V0"], F)
    need(np.allclose(Z.sort_index(), Zl.sort_index(), rtol=0, atol=1e-12), "[DOSE] loop disagrees")
    for root in ("ES", "NQ"):
        k = k2_frame(root)
        need(len(k) == {"ES": 1360, "NQ": 1389}[root], f"[INPUT] K2_{root} count")
    print(f"  calendar counts reproduce s.0; dose defined on {len(Z)} sessions; loop == vectorised; K2 counts ok")

    print("[canaries]")
    expect_raise(lambda: read_options(plant=True), "seal: a planted 2024 option row", fired)
    expect_raise(lambda: read_futures_volume(plant=True), "seal: a planted 2024 futures-volume row", fired)
    expect_raise(lambda: need(calendar_counts(expiry_calendar(x, include_am=True)) == CAL_KNOWN,
                              "[CALENDAR] AM-settled expiries included: the counts move"),
                 "right-quantity: AM expiries included", fired)

    def leak():
        Zk = dose(cal["V0"], F, leak=True)
        common = Zk.index.intersection(Zl.index)
        need(np.allclose(Zk.reindex(common), Zl.reindex(common), rtol=0, atol=1e-12), "[DOSE] a leaking dose disagrees with the loop")
    expect_raise(leak, "lag: the dose's median built from the next session", fired)

    rng = np.random.default_rng(0)
    g = rng.standard_t(3, 3000)
    w = np.repeat(np.arange(600), 5)
    a = boot_eff([(g, w)], np.random.default_rng(1), draws=777, chunk=777)
    b = boot_eff([(g, w)], np.random.default_rng(1), draws=777, chunk=100)
    need(np.array_equal(a, b), "[BOOT] chunk != whole")
    print("  PASS    bootstrap chunk == whole (bit-identical)")
    expect_raise(lambda: need(np.array_equal(a, boot_eff([(g, w)], np.random.default_rng(2), draws=777)), "[BOOT] seed change"),
                 "bootstrap: a different stream is caught", fired)
    expect_raise(lambda: need(float(np.std(boot_eff([(g[:5], np.zeros(5, int))], rng, draws=50)[:, 0])) > SE_FLOOR,
                              "[BOOT] a single-week group gives a degenerate SE"), "bootstrap: degenerate SE", fired)

    z = rng.standard_normal(400)
    planted = -0.4 * z + rng.standard_normal(400)
    rp = rotation(z, planted)
    need(rp["rho"] <= rp["p05"], "[S3] a planted negative dose is not detected")
    rn = rotation(z, rng.standard_normal(400))
    print(f"  PASS    rotation: planted dose detected (rank {rp['rank_low']:.3f}); noise rank {rn['rank_low']:.3f}")
    expect_raise(lambda: need(rotation(z, -planted)["rho"] <= rotation(z, -planted)["p05"], "[S3] the opposite sign is read as support"),
                 "rotation: a positive dose is not support", fired)

    cases = [((True, True, False), "SUPPORTED"), ((False, True, True), "SUPPORTED"), ((False, True, False), "PARTIAL"),
             ((True, False, True), "PARTIAL"), ((True, False, False), "PARTIAL"), ((False, False, False), "NOT SUPPORTED")]
    for args, want in cases:
        need(reading(*args) == want, f"[READING] {args} -> {reading(*args)} != {want}")
    print(f"  PASS    reading logic on {len(cases)} cases")
    expect_raise(lambda: need(reading(True, False, True) == "SUPPORTED", "[READING] S1+S3 without S2 is not SUPPORTED"),
                 "reading: S2 is required for SUPPORTED", fired)

    kk = k2_frame("ES")
    expect_raise(lambda: seal(pd.concat([kk["session"], pd.Series(["2024-02-01"])]), "K2_ES"), "seal: a planted 2024 K2 session", fired)
    print(f"SELFTEST PASS: {len(fired)} canaries raised; {time.time() - t0:.1f} s")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
