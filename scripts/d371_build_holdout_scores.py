"""D371 -- add family G (the anomaly scores) to the HOLDOUT score cache, so the momentum book can be read.

    uv run python scripts/d371_build_holdout_scores.py --verify     # in-process == the 8-worker fan, on MINING
    uv run python scripts/d371_build_holdout_scores.py --build      # extend the holdout npz with family G

WHY THIS EXISTS. D357 built the holdout score cache as a deliberate SUBSET -- families A, B, E and F, in-process
-- because its short candidates needed nothing else. The momentum book's own score, `mom_252_21`, lives in
family G, and so does `rev_21`, which d348_prep's LAG_SIGS requires. Neither is in the holdout npz, so the read
could not run: the strategy's signal had never been computed on that universe.

WHY NOT THE 8-PROCESS FAN. `d290_build_worker.py` fans C, D, G and H across processes because C (~309s) and
D (~700s) are expensive. G alone is ~110s of per-symbol trailing windows on the 1,573-name mining panel, so on
803 holdout names it is a minute -- cheap enough to run in ONE process on the WHOLE panel. That also sidesteps
the workers' two hazards entirely: they take no --fixture argument (they would rebuild the mining panel however
the parent is re-pointed), and chunking is where the market-return estimator can silently change.

THE VERIFICATION THAT MAKES THIS TRUSTWORTHY. `--verify` computes family G in-process on the MINING fixture and
compares it, member by member, to the mining cache that the 8-worker fan produced -- values AND the NaN pattern.
If the in-process path reproduces the fanned path bit-identically there, it is the same estimator on the holdout.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import run_d365_momentum_buffer as V65        # noqa: E402  -- installs the holdout audit hook
V65.allow_holdout("D371 score-cache build: computes SCORES on the holdout universe; no book, no null, no hurdle")

import run_d357_holdout_read as V57           # noqa: E402  -- repoint(), FIXTURES
import ragged_anomaly_scores as AN            # noqa: E402  -- family G

BC, M, R = V57.BC, V57.M, V57.R
NEEDED = ("mom_252_21", "rev_21")


def family_G(tag):
    """Family G on the WHOLE panel, one process. Returns (scores, warm, n_names, n_bars)."""
    t0 = time.time()
    V57.repoint(tag)
    panel, cleaned = BC.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = BC.P1.build_grids(panel, cleaned)
    vol, vpx = BC.RF.volume_grids(panel, cleaned, live=live)
    mkt = AN.market_return(panel.total_log_returns, live)      # from the FULL cross-section, never a subset
    sc = AN.anomaly_scores(g, panel, live, vol=vol, mkt=mkt)
    print(f"    family G on {tag}: {len(sc)} scores over {live.shape[0]} names x {live.shape[1]} bars "
          f"({time.time() - t0:.0f}s)")
    return sc, panel, live


def stage_verify():
    """In-process family G vs the MINING cache the 8-worker fan built. Bit-identical, or this is not trusted."""
    sc, panel, live = family_G("mining")
    z = np.load(R.BC.CACHE, allow_pickle=False)
    common = [k for k in AN.ANOMALY_SCORES if k in z.files]
    assert common, "the mining cache has no family-G members to compare against"
    print(f"\n  comparing {len(common)} family-G members against the fanned build in {Path(R.BC.CACHE).name}")
    bad = 0
    for k in common:
        a, b = np.asarray(z[k], float), np.asarray(sc[k], float)
        assert a.shape == b.shape, f"{k}: shape {a.shape} vs {b.shape}"
        fa, fb = np.isfinite(a), np.isfinite(b)
        if not np.array_equal(fa, fb):
            print(f"    {k:16s} NaN PATTERN MOVED on {int((fa ^ fb).sum()):,} cells")
            bad += 1
        elif not np.array_equal(a[fa], b[fb]):
            d = np.abs(a[fa] - b[fb])
            print(f"    {k:16s} {int((d > 0).sum()):,} cells CHANGED, max {d.max():.3e}")
            bad += 1
        else:
            print(f"    {k:16s} bit-identical, {int(fa.sum()):,} finite cells")
    assert bad == 0, f"[G] {bad} member(s) differ from the fanned build -- the in-process path is NOT the same"
    print(f"\nOK  in-process family G == the 8-worker fan on every member, bit-identically.")


def stage_build(force=False):
    """Extend the HOLDOUT npz with family G, leaving every existing array untouched."""
    t0 = time.time()
    V57.repoint("holdout")
    cache = Path(R.BC.CACHE)
    assert "holdout" in str(cache).lower(), f"refusing to write {cache}: not the holdout cache"
    z = np.load(cache, allow_pickle=False)
    before = {k: np.asarray(z[k]) for k in z.files}          # materialise every array...
    z.close()                                                # ...then CLOSE: an NpzFile is lazy and holds the
    #                                                          handle open, and Windows refuses to replace a file
    #                                                          that is still open.
    have = [k for k in NEEDED if k in before]
    if have == list(NEEDED) and not force:
        print(f"  HIT: {cache.name} already carries {NEEDED}")
        return
    print(f"  {cache.name} currently holds {len(before) - 2} members; {NEEDED} missing -> building family G")

    sc, panel, live = family_G("holdout")
    for k in NEEDED:
        assert k in sc, f"[G] {k} not produced"
        fin = int(np.isfinite(sc[k]).sum())
        assert fin > 0, f"[G] {k} is entirely NaN"
        print(f"    {k}: {fin:,} finite cells of {sc[k].size:,}")

    merged = dict(before)
    added = []
    for k in AN.ANOMALY_SCORES:
        if k in sc:
            merged[k] = sc[k]
            added.append(k)
    fams = sorted(set(list(np.atleast_1d(before["families"]).astype(str)) + ["G"]))
    built = sorted(set(list(np.atleast_1d(before["built"]).astype(str)) + added))
    merged["families"] = np.array(fams)
    merged["built"] = np.array(built)
    merged["key"] = before["key"]                              # the key is the FIXTURE's, unchanged by adding members

    # np.savez APPENDS '.npz' unless the name already ends in it, so a '.npz.tmp' name silently becomes
    # '.npz.tmp.npz' and the rename then fails on a file that was never written.
    tmp = cache.with_name(cache.stem + "__tmp.npz")
    np.savez(tmp, **merged)
    assert tmp.exists(), f"savez did not write {tmp}"
    tmp.replace(cache)

    # every pre-existing array must survive untouched
    z2 = np.load(cache, allow_pickle=False)
    for k, v in before.items():
        if k in ("families", "built"):
            continue
        a, b = np.asarray(v), np.asarray(z2[k])
        same = (np.array_equal(a, b) if a.dtype.kind not in "fc"
                else (np.array_equal(np.isfinite(a), np.isfinite(b))
                      and np.array_equal(a[np.isfinite(a)], b[np.isfinite(b)])))
        assert same, f"[G] rewriting the cache changed the pre-existing array {k}"
    for k in NEEDED:
        assert k in z2.files, f"[G] {k} did not survive the write"
    print(f"  BUILT {cache.name}: {len(before) - 2} -> {len(built)} members, families {','.join(fams)} "
          f"({cache.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.0f}s); every pre-existing array unchanged")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.verify:
        stage_verify()
    elif a.build:
        stage_build(a.force)
    else:
        ap.error("one of --verify, --build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
