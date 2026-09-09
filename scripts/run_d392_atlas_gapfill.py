"""D392 ADDENDUM 2 -- the last three atlas floor gaps: cap 5 both sides, cap 1 short.

    uv run python scripts/run_d392_atlas_gapfill.py --selftest
    uv run python scripts/run_d392_atlas_gapfill.py --verify     [K][G][SHARD], ~1 min, spends nothing
    uv run python scripts/run_d392_atlas_gapfill.py --run        6 processes, ~5 min, then merges
    uv run python scripts/run_d392_atlas_gapfill.py --merge      merge shards only
    uv run python scripts/run_d392_atlas_gapfill.py --cell I     one cell (what --run spawns)

Spec: docs/decisions/D392-ADDENDUM-2-the-last-three-floor-gaps.md, committed BEFORE this file (R8).

WHAT IT IS. Six more cells on D392's grid, nothing else. A MEASUREMENT (D280's class): it scores no
strategy, proposes no rule, admits nothing (R15), and spends no holdout read.

WHY. D391 RESULT: "Three cells have no floor -- cap 5 either side, and cap 1 short at 167,179
trades -- because the grid's trade axis does not reach there at those caps. Named rather than
interpolated past." Those three counts are 94,198 / 106,888 / 167,179 and `lookup` RAISES on all
three today. Six cells at n in {100,000, 150,000} x cap 5 and n = 200,000 x cap 1 bracket them.

NOTHING IS REIMPLEMENTED. draw_mask, score_once, summarise, eligible_index, cell_key, cell_seed and
lookup are imported from run_d392_base_rate_atlas.py. This file is a PLAN, a SHARDER and a MERGE.

THE TWO THINGS THIS FILE DOES DIFFERENTLY, both proved rather than assumed (addendum section 3):
  * prep(need_grids=False) -- F is only read by tercile_pools and every cell here is pool="ALL".
    [G] asserts a probe ledger is bit-identical to need_grids=True.
  * six processes, one per cell -- the kernel is simulate_event's pure-Python double loop, so it is
    GIL-bound and threads are the wrong tool (CLAUDE.md). [SHARD] asserts a cheap plan computed as
    subprocesses equals the same plan computed as one serial loop, cell for cell, to 0.0.

ASSERTIONS [SELFTEST][K][G][SHARD][P][M][B] -- addendum section 5.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


ATLAS = REPO / "data" / "d392_atlas.json"
SHARDS = REPO / "temp" / "d392_gapfill"

# ------------------------------------------------------------------ the plan, frozen (section 2)
GAPS = (
    dict(n=100_000, cap=5, side="long"),
    dict(n=100_000, cap=5, side="short"),
    dict(n=150_000, cap=5, side="long"),
    dict(n=150_000, cap=5, side="short"),
    dict(n=200_000, cap=1, side="long"),
    dict(n=200_000, cap=1, side="short"),
)
DRAWS = 500                      # DRAWS_UNCOND, unchanged: the principal's ruling of 2026-09-08

# the cheap plan [SHARD] is proved on. Two cells so the proof covers the side axis of the seed.
TINY = (dict(n=2_000, cap=5, side="long"), dict(n=2_000, cap=5, side="short"))
TINY_DRAWS = 20

# the three counts this record exists to floor (data/d391_fill_and_decay.json, `decay`)
TARGETS = ((94_198, 5, "long", 4.9686), (106_888, 5, "short", 2.8858), (167_179, 1, "short", 1.0607))

PLANS = {"gaps": (GAPS, DRAWS), "tiny": (TINY, TINY_DRAWS)}


def plan_of(name):
    cells, draws = PLANS[name]
    return [dict(kind="uncond", pool="ALL", conc=1.0, draws=draws, **c) for c in cells]


def shard_path(name, i):
    return SHARDS / f"{name}_{i}.json"


def working_set_gb():
    """Peak and current working set, or None -- reported honestly rather than as a fake 0.00."""
    try:
        import ctypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        fn = getattr(ctypes.windll.kernel32, "K32GetProcessMemoryInfo", None)
        if fn is None:
            fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), ctypes.c_uint32]
        fn.restype = ctypes.c_int
        cur = ctypes.windll.kernel32.GetCurrentProcess
        cur.restype = ctypes.c_void_p
        ok = fn(cur(), ctypes.byref(c), c.cb)
        if not ok or c.PeakWorkingSetSize == 0:
            return None
        return c.PeakWorkingSetSize / 2 ** 30, c.WorkingSetSize / 2 ** 30
    except Exception:
        return None


# ------------------------------------------------------------------ the one cell body
def build(AT, need_grids):
    PREP = _load("d348p", "d348_prep.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=need_grids, verbose=False)
    T, N = P["T"], P["n"]
    elig = np.asarray(P["elig"])
    return dict(AT=AT, V59=V59, P=P, T=T, N=N, elig=elig,
                idx=AT.eligible_index(elig), sc=np.full((T, N), 50.0))


def run_cell(B, c):
    """One atlas cell, through the parent's own functions. Returns the cell dict."""
    AT, V59, P, T, N, elig, idx, sc = (B["AT"], B["V59"], B["P"], B["T"], B["N"],
                                       B["elig"], B["idx"], B["sc"])
    rng = AT.cell_seed(c["n"], c["cap"], c["side"], c["pool"], c["conc"])
    vals, trades, t1, skipped = [], [], time.time(), 0
    for _d in range(c["draws"]):
        m = AT.draw_mask(rng, idx, (T, N), c["n"])
        if m is None:
            skipped += 1
            continue
        assert not (m & ~elig).any(), "[E] a drawn event landed off the eligible mask"
        mu, ntr = AT.score_once(V59, P, m, c["cap"], c["side"], sc)
        if mu is not None:
            vals.append(mu)
            trades.append(ntr)
    assert vals, "empty cell -- the uniform pool cannot be too small at these sizes"
    # the bootstrap stream is keyed on the CELL, not on its position in a plan, so a cell computed
    # alone and the same cell computed inside a loop get the same stream. [SHARD] tests exactly this.
    boot = np.random.default_rng([AT.SEED, 7, c["n"], c["cap"], AT.SIDE_CODE[c["side"]]])
    cell = AT.summarise(vals, trades, boot)
    cell.update(kind=c["kind"], n=c["n"], cap=c["cap"], side=c["side"], pool=c["pool"],
                conc=c["conc"], seconds=time.time() - t1, skipped=skipped)
    return cell


# ------------------------------------------------------------------ [K][G][SHARD]
def verify(AT) -> int:
    print("D392 GAPFILL VERIFY -- [K] the kernel, [G] need_grids, [SHARD] the process split\n")
    AT.selftest()                                        # [SELFTEST] [N][E][SE][X], not reimplemented

    t0 = time.time()
    B = build(AT, need_grids=False)
    print(f"  prep(need_grids=False) in {time.time() - t0:.0f}s | {B['N']} names x {B['T']} bars | "
          f"{B['idx'].size:,} eligible cells | F is None = {B['P']['F'] is None}", flush=True)

    # ---- [K] score_once is run_d359's own path ----------------------------
    V59, P, sc = B["V59"], B["P"], B["sc"]
    mk = AT.draw_mask(np.random.default_rng(AT.SEED), B["idx"], (B["T"], B["N"]), 2_000)
    r1 = V59.run_mirror(P, mk, sc, "cap", 20)
    r2 = V59.run_mirror(P, mk, np.full((B["T"], B["N"]), 17.0), "cap", 20)
    m1, c1 = AT.score_once(V59, P, mk, 20, "long", sc)
    assert len(r1["trades"]) == len(r2["trades"]), "[K] the score changed a cap-exit ledger"
    assert m1 == float(V59.V47.pnl_bp(r1).mean()) and c1 == len(r1["trades"]), \
        "[K] score_once differs from run_d359's path"
    print(f"    [K] score_once == run_d359's own path to 0.0 ({c1:,} trades, {m1:+.6f} bp); "
          f"the cap exit ignores the score", flush=True)

    # ---- [G] need_grids=False changes nothing -----------------------------
    Bg = build(AT, need_grids=True)
    assert Bg["P"]["F"] is not None, "[G] need_grids=True did not load F -- the test is vacuous"
    for cap, side in ((20, "long"), (5, "short"), (1, "short")):
        a = AT.score_once(V59, P, mk, cap, side, sc)
        b = AT.score_once(Bg["V59"], Bg["P"], mk, cap, side, Bg["sc"])
        assert a == b, f"[G] need_grids changed the ledger at cap {cap} {side}: {a} vs {b}"
    print("    [G] need_grids=False is BIT-IDENTICAL to need_grids=True at cap 20 long, "
          "5 short and 1 short on the same 2,000-event probe", flush=True)
    del Bg

    # ---- [SHARD] the process split is the cell boundary --------------------
    serial = {}
    ts = time.time()
    for i, c in enumerate(plan_of("tiny")):
        serial[i] = run_cell(B, c)
    print(f"    tiny plan serially in {time.time() - ts:.0f}s", flush=True)

    SHARDS.mkdir(parents=True, exist_ok=True)
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                               "--cell", str(i), "--plan", "tiny"],
                              cwd=str(REPO), stdout=subprocess.DEVNULL)
             for i in range(len(serial))]
    for p in procs:
        assert p.wait() == 0, "[SHARD] a tiny-plan subprocess failed"

    for i, sc_cell in serial.items():
        got = json.loads(shard_path("tiny", i).read_text())
        drop = ("seconds",)                       # wall time is the one field that cannot match
        a = {k: v for k, v in sc_cell.items() if k not in drop}
        b = {k: v for k, v in got.items() if k not in drop}
        assert a == b, f"[SHARD] cell {i} differs serial vs subprocess:\n  {a}\n  {b}"
    print(f"    [SHARD] {len(serial)} cells computed as SUBPROCESSES == the same cells computed "
          f"in ONE SERIAL LOOP, to 0.0, every field but wall time", flush=True)

    # [X] the shard comparison must be able to fail
    raised = False
    try:
        bad = dict(serial[0])
        bad["p95"] += 1e-12
        assert {k: v for k, v in bad.items() if k != "seconds"} == \
               {k: v for k, v in serial[0].items() if k != "seconds"}, "[SHARD] mismatch"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SHARD COMPARISON CANNOT FAIL -- a perturbed p95 passed"
    print("    [X] a p95 perturbed by 1e-12 IS CAUGHT by the shard comparison")

    ws = working_set_gb()
    print(f"\n    memory: {'peak WS %.2f GB, now %.2f GB' % ws if ws else 'NOT MEASURED'}")
    print("\nVERIFY PASSED -- nothing was spent.\n")
    return 0


# ------------------------------------------------------------------ merge and check
def merge(AT, plan_name="gaps") -> int:
    # the tiny plan is a PROOF, not a measurement: n=2,000 at 20 draws would land on the same
    # lookup curve as the real cells and drag it. It never touches data/.
    assert plan_name == "gaps", \
        f"[M] REFUSING to merge plan {plan_name!r} into the atlas -- only 'gaps' is a measurement"
    atlas = json.loads(ATLAS.read_text())
    before = dict(atlas["cells"])
    cells = plan_of(plan_name)
    added = []
    for i, c in enumerate(cells):
        p = shard_path(plan_name, i)
        assert p.exists(), f"shard missing: {p.relative_to(REPO)} -- run --cell {i} first"
        cell = json.loads(p.read_text())
        key = AT.cell_key(c["kind"], c["n"], c["cap"], c["side"], c["pool"], c["conc"])
        assert key not in before, f"[M] {key} already in the atlas -- this record adds cells only"
        assert (cell["n"], cell["cap"], cell["side"]) == (c["n"], c["cap"], c["side"]), \
            f"[M] shard {i} is not the cell the plan asked for"
        atlas["cells"][key] = cell
        added.append((key, cell))

    # [M] nothing pre-existing may move
    for k, v in before.items():
        assert atlas["cells"][k] == v, f"[M] the merge changed a pre-existing cell: {k}"
    assert len(atlas["cells"]) == len(before) + len(added), "[M] cell count is not before + added"

    # [P] persist BEFORE rendering
    ATLAS.write_text(json.dumps(atlas, indent=1))
    print(f"\n  [P] {ATLAS.relative_to(REPO)} written: {len(before)} -> {len(atlas['cells'])} cells; "
          f"[M] all {len(before)} pre-existing cells byte-identical\n")

    print(f"  {'n':>8s} {'cap':>4s} {'side':>6s} {'trades':>9s} {'p50':>8s} {'p95':>8s} "
          f"{'se':>6s} {'p05':>9s} {'max':>9s}")
    for key, c in added:
        print(f"  {c['n']:>8,} {c['cap']:>4d} {c['side']:>6s} {c['trades_mean']:>9,.0f} "
              f"{c['p50']:>+8.2f} {c['p95']:>+8.2f} {c['se_p95']:>6.2f} {c['p05']:>+9.2f} "
              f"{c['max']:>+9.2f}")

    # [B] the three gaps now resolve where they raised, and the grid still raises outside itself
    print(f"\n  [B] THE THREE GAPS -- lookup(trades, cap, side) where it RAISED before\n")
    print(f"  {'observed (D391)':>22s} {'trades':>9s} {'floor p95':>10s} {'+/-':>6s} "
          f"{'p50':>8s} {'ratio':>7s} {'between':>21s}")
    for trades, cap, side, obs in TARGETS:
        f = AT.lookup(atlas, trades, cap, side)
        lo, hi = f["between"]
        print(f"  cap {cap:<2d} {side:<5s} {obs:>+7.2f} {trades:>9,} {f['p95']:>+10.2f} "
              f"{f['se_p95']:>6.2f} {f['p50']:>+8.2f} {obs / f['p95']:>6.2f}x "
              f"{lo:>10,.0f}-{hi:<10,.0f}")

    raised = False
    try:
        AT.lookup(atlas, 400_000, 5, "long")
    except ValueError:
        raised = True
    assert raised, "[X] THE LOOKUP NO LONGER RAISES OUTSIDE THE GRID -- it must never extrapolate"
    print("\n    [X] lookup(400,000, cap 5, long) still RAISES -- the atlas states what it measured")

    print("\nThis is a MEASUREMENT. It admits nothing (R15) and it does not revive D391.")
    return 0


# ------------------------------------------------------------------ reporting only
def d391_table(AT) -> int:
    """Added AFTER the run, and it measures NOTHING -- it reads data/d392_atlas.json and
    data/d391_fill_and_decay.json and prints whether every cell D391 reported now has a floor.
    D391 is the only record in the programme that ever hit a missing one (grep "no floor")."""
    atlas = json.loads(ATLAS.read_text())
    decay = json.loads((REPO / "data" / "d391_fill_and_decay.json").read_text())["decay"]
    print("\n  D391's CORRECTED LEDGER against the atlas, every cell -- the completeness check\n")
    print(f"  {'cap':>4s} {'side':>6s} {'trades':>9s} {'observed':>9s} {'floor p95':>10s} "
          f"{'+/-':>5s} {'ratio':>7s} {'null p05..max':>18s}  status")
    missing = []
    for side in ("long", "short"):
        for row in decay[side]:
            cap, tr, obs = row["cap"], row["trades"], row["mean_bp"]
            try:
                f = AT.lookup(atlas, tr, cap, side)
            except (ValueError, KeyError) as e:
                missing.append((cap, side, tr, str(e)))
                print(f"  {cap:>4d} {side:>6s} {tr:>9,} {obs:>+9.2f} {'NO FLOOR':>10s}")
                continue
            lo, hi = f["between"]
            ends = [c for c in atlas["cells"].values()
                    if c.get("cap") == cap and c.get("side") == side and c.get("pool") == "ALL"
                    and c.get("conc", 1.0) == 1.0 and c.get("status") != "EMPTY"
                    and (abs(c["trades_mean"] - lo) < 1.0 or abs(c["trades_mean"] - hi) < 1.0)]
            assert ends, f"[B] could not re-find the bracketing cells for cap {cap} {side}"
            p05 = min(c["p05"] for c in ends)
            mx = max(c["max"] for c in ends)
            inside = obs <= mx
            print(f"  {cap:>4d} {side:>6s} {tr:>9,} {obs:>+9.2f} {f['p95']:>+10.2f} "
                  f"{f['se_p95']:>5.2f} {obs / f['p95']:>6.2f}x  {p05:>+7.2f}..{mx:<+7.2f}  "
                  + ("INSIDE the null's observed range" if inside else "above every one of 500 draws"))
    assert not missing, f"[B] cells still without a floor: {missing}"
    print("\n  [B] EVERY cell D391 reported now has an in-grid floor. Nothing is interpolated past.")
    print("\n  The `ratio` column is gross-vs-uniform-draw and it is NOT a verdict: D391 died on")
    print("  B_r, its SAME-POOL control, which a uniform draw does not share (D291).")
    return 0


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--d391table", action="store_true")
    ap.add_argument("--cell", type=int)
    ap.add_argument("--plan", default="gaps", choices=sorted(PLANS))
    a = ap.parse_args()

    AT = _load("d392a", "run_d392_base_rate_atlas.py")

    if a.selftest:
        return AT.selftest()
    if a.verify:
        return verify(AT)
    if a.d391table:
        return d391_table(AT)

    if a.cell is not None:
        c = plan_of(a.plan)[a.cell]
        B = build(AT, need_grids=False)
        cell = run_cell(B, c)
        SHARDS.mkdir(parents=True, exist_ok=True)
        # [P] persist before anything is rendered
        shard_path(a.plan, a.cell).write_text(json.dumps(cell, indent=1))
        ws = working_set_gb()
        print(f"  cell {a.cell}: n={c['n']:,} cap={c['cap']} {c['side']} -> "
              f"p50 {cell['p50']:+.2f} p95 {cell['p95']:+.2f} +/- {cell['se_p95']:.2f} "
              f"({cell['trades_mean']:,.0f} trades, {cell['seconds']:.0f}s"
              + (f", peak WS {ws[0]:.2f} GB)" if ws else ")"))
        return 0

    if a.merge:
        return merge(AT, a.plan)

    if not a.run:
        ap.error("pass --selftest, --verify, --run, --merge, --d391table or --cell I")

    cells = plan_of(a.plan)
    SHARDS.mkdir(parents=True, exist_ok=True)
    todo = [i for i in range(len(cells)) if not shard_path(a.plan, i).exists()]
    print(f"\n  {len(cells)} cells, {len(cells) - len(todo)} shards already present -- "
          f"launching {len(todo)} processes (the kernel is GIL-bound; threads are the wrong tool)\n",
          flush=True)
    t0 = time.time()
    procs = {i: subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                  "--cell", str(i), "--plan", a.plan], cwd=str(REPO))
             for i in todo}
    for i, p in procs.items():
        assert p.wait() == 0, f"cell {i} failed"
    wall = time.time() - t0

    work = sum(json.loads(shard_path(a.plan, i).read_text())["seconds"] for i in range(len(cells)))
    eff = work / (wall * max(len(todo), 1)) if wall else 0.0
    print(f"\n  [SPEED] sum(cell time) {work / 60:.1f} min / wall {wall / 60:.1f} min = "
          f"{work / wall:.2f}x on {len(todo)} processes ({eff:.0%} efficiency)"
          + ("" if eff >= 0.70 else "   <-- BELOW THE 70% FLOOR"), flush=True)

    return merge(AT, a.plan)


if __name__ == "__main__":
    raise SystemExit(main())
