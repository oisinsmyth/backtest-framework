"""D334 -- assert the rebuilt score cache changed exactly what D333 should change.

    uv run python scripts/d334_cache_diff.py

Compares `temp/d290_scores_pre_d333.npz` (the cache as built before D333's
dividend bound) against `temp/d290_scores.npz` (rebuilt under it) and asserts,
per docs/decisions/D334-score-cache-rebuild-under-the-dividend-bound.md section 2:

  [K]  the new key equals `d290_build_cache.cache_key(FIXTURE)` (which now hashes
       `ragged_panel.py`)
  [W]  `warm` is bit-identical old -> new
  [U]  every score EXCEPT beta_63, ivol_21, signed_vol is array_equal(equal_nan)
       old -> new -- 48 of 51
  [D]  each of those three DOES differ; the fraction of finite cells changed and
       the max |delta| are reported per score
  [V]  the key check a key-verifying runner performs (run_stage1_rerun.py, the
       three lines after `np.load(BC.CACHE, ...)`) passes on the new npz

The printed report is saved to data/d334_cache_diff.txt. Nothing is deleted.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

OLD = REPO / "temp" / "d290_scores_pre_d333.npz"
NEW = REPO / "temp" / "d290_scores.npz"
OUT = REPO / "data" / "d334_cache_diff.txt"
CHANGED = ("beta_63", "ivol_21", "signed_vol")


def _load(name, filename):
    """Same loader as d290_direction_nulls.py -- scripts/ is not a package."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
B = M.B

lines: list[str] = []


def say(s: str = "") -> None:
    print(s, flush=True)
    lines.append(s)


def main() -> int:
    failures: list[str] = []
    say(f"D334 cache diff  old={OLD.relative_to(REPO)} ({OLD.stat().st_size:,} B)")
    say(f"                 new={NEW.relative_to(REPO)} ({NEW.stat().st_size:,} B)")
    old = np.load(OLD, allow_pickle=False)
    new = np.load(NEW, allow_pickle=False)

    # [K] key -----------------------------------------------------------------
    want = BC.cache_key(B.FIXTURE)
    k_new, k_old = str(new["key"]), str(old["key"])
    ok = k_new == want
    say(f"\n[K] new key == cache_key(FIXTURE): {'PASS' if ok else 'FAIL'}")
    say(f"    'ragged_panel.py' in key: {'ragged_panel.py' in k_new}")
    say(f"    old key had ragged_panel.py: {'ragged_panel.py' in k_old}")
    if not ok:
        failures.append("K")
        say("    --- new key ---\n" + k_new + "\n    --- expected ---\n" + want)

    # [W] warm -----------------------------------------------------------------
    ok = np.array_equal(old["warm"], new["warm"])
    say(f"\n[W] warm bit-identical: {'PASS' if ok else 'FAIL'}  "
        f"shape={new['warm'].shape} dtype={new['warm'].dtype}")
    if not ok:
        failures.append("W")

    # [U] unchanged scores ----------------------------------------------------
    cands = list(BC.CANDIDATES)
    say(f"\n[U] {len(cands)} candidates in CANDIDATES; "
        f"{len(cands) - len(CHANGED)} must be unchanged")
    n_pass, bad = 0, []
    for k in cands:
        if k in CHANGED:
            continue
        a, b = old[k], new[k]
        if a.shape == b.shape and a.dtype == b.dtype and \
                np.array_equal(a, b, equal_nan=(a.dtype.kind == "f")):
            n_pass += 1
        else:
            bad.append(k)
    say(f"    unchanged: {n_pass} of {len(cands) - len(CHANGED)}"
        + (f"   DIFFER: {bad}" if bad else ""))
    if n_pass != 48 or bad:
        failures.append("U")
        say("    FAIL")
    else:
        say("    PASS")

    # [D] the three that must differ -------------------------------------------
    say("\n[D] the three scores that read total_log_returns")
    say(f"    {'score':<12} {'finite_old':>11} {'finite_new':>11} {'nan_pat_diff':>13} "
        f"{'both_finite':>12} {'changed':>9} {'frac':>8} {'max|d|':>12} {'rows':>6}")
    for k in CHANGED:
        a, b = old[k].astype(float), new[k].astype(float)
        fa, fb = np.isfinite(a), np.isfinite(b)
        both = fa & fb
        d = np.abs(a - b)
        chg = both & (a != b)
        nan_pat = int((fa != fb).sum())
        n_chg = int(chg.sum())
        differs = (nan_pat > 0) or (n_chg > 0)
        frac = n_chg / max(int(both.sum()), 1)
        mx = float(d[chg].max()) if n_chg else 0.0
        rows = int((chg | (fa != fb)).any(axis=1).sum())
        say(f"    {k:<12} {int(fa.sum()):>11,} {int(fb.sum()):>11,} {nan_pat:>13,} "
            f"{int(both.sum()):>12,} {n_chg:>9,} {frac:>8.2%} {mx:>12.4g} {rows:>6}"
            f"   {'differs' if differs else 'IDENTICAL -- FAIL'}")
        if not differs:
            failures.append(f"D:{k}")

    # [V] a key-verifying runner's check ---------------------------------------
    # run_stage1_rerun.py main(): the three lines after the existence check.
    say("\n[V] run_stage1_rerun.py key check on BC.CACHE")
    say(f"    BC.CACHE = {Path(BC.CACHE).relative_to(REPO)}  "
        f"(same file as new: {Path(BC.CACHE).resolve() == NEW.resolve()})")
    try:
        z = np.load(BC.CACHE, allow_pickle=False)
        assert str(z["key"]) == BC.cache_key(M.B.FIXTURE), (
            "CACHE IS STALE -- the fixture or an estimator module changed since it "
            "was built. Rebuild rather than scoring numbers that belong to code "
            "that no longer exists.")
        say("    PASS  (no raise)")
    except AssertionError as e:
        failures.append("V")
        say(f"    FAIL  {e}")

    say("\nRESULT: " + ("ALL ASSERTIONS PASS" if not failures
                         else f"FAILED: {failures}"))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nsaved {OUT.relative_to(REPO)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
