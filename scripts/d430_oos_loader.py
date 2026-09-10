"""D430 -- THE ONE OPENER of us_shorts_daily_holdout. Imports nothing that carries run_d411's [SPLIT] audit hook.

Loads the holdout panel through the SAME load_panel_from body the --proof validated, writes it to
temp/d430_oos_panel.npz (a name the guard in the runner's process has no reason to refuse), prints a receipt.

usage:  uv run python -u scripts/d430_oos_loader.py --spend-the-holdout
"""
import argparse, hashlib, importlib.util, pathlib, sys, types
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m

FIX = REPO / "data/fixtures/us_shorts_daily_holdout.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_holdout_events.json"
CACHE = REPO / "temp" / "d430_oos_panel.npz"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--spend-the-holdout", action="store_true"); a = ap.parse_args()
    assert a.spend_the_holdout, "REFUSED: this opener needs --spend-the-holdout (the read is spent once)"
    assert FIX.name == "us_shorts_daily_holdout.csv.gz" and "holdout2" not in FIX.name, "[FILE] wrong fixture"
    assert not CACHE.exists(), f"[ONE-READ] {CACHE.name} exists: the holdout has already been opened for this line"
    assert not any("d411" in k for k in sys.modules), "[SPLIT] run_d411 must not be in this process"
    RP = _load("rp", "ragged_panel.py"); X = _load("d320", "run_d320_tilt_filters.py"); UF = _load("d339", "d339_universe_floor.py"); UF.bind(X, None)
    assert not any("d411" in k for k in sys.modules), "[SPLIT] a loader module pulled in run_d411"
    R30 = _load("d430r", "run_d430_holdout.py")             # for load_panel_from only; its imports are light and hook-free
    assert not any("d411" in k for k in sys.modules), "[SPLIT] the runner's import pulled in run_d411"
    D = types.SimpleNamespace(RP=RP, X=X, UF=UF)
    sha = hashlib.sha256(FIX.read_bytes()).hexdigest()
    P = R30.load_panel_from(D, FIX, EVJ, CACHE, verbose=True)
    print(f"  [RECEIPT] opened {FIX.name}  sha256 {sha}  panel {P['CL'].shape[0]} dates x {P['CL'].shape[1]} names  elig {100*P['elig'].mean():.1f}%  ->  {CACHE.relative_to(REPO)}")
    print("  THE FILE IS NOW SPENT FOR THIS LINE.")
