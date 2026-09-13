"""D524 -- verify the committed `fut_day5m.parquet`, and measure what a FLAT id dict would have done to it.

`build_fut_day5m.py` already imports the WINDOWED `ids_of` from the breadth builder, so there was
nothing to port. What was never done is the check D520/D521 applied to every other futures builder:
rebuild, and diff. Two things make that non-trivial here and they are why this script has four modes:

  * **`--build` reads a CACHED decode** (`temp/day5m_decode/*.5m.parquet`) and the id mapping is
    applied during `--decode`, which costs 88 minutes. So a rebuild-from-cache proves the build is
    reproducible and says NOTHING about the mapping.
  * The mapping question is therefore answered two other ways: by folding the 5-minute bars into
    hours and comparing them against `fut_breadth_hourly`, a SEPARATE decode pass over the same
    archive; and by reading the archive's mapping tables to count what a flat dict would have got
    wrong.

    python scripts/d524_day5m_verification.py --rebuild-diff     # ~1 min, writes to temp/, never touches the fixture
    python scripts/d524_day5m_verification.py --aggregate        # ~1 min, day5m folded to hours vs the breadth fixture
    python scripts/d524_day5m_verification.py --precheck         # ~21 min, SYSTEM python (databento): the flat-map counterfactual
    python scripts/d524_day5m_verification.py --name 2019 2020   # ~1 min a file, SYSTEM python: resolve mislabels to contracts
    python scripts/d524_day5m_verification.py --all              # everything, ~25 min

Results merge into data/d524_day5m_verification.json, so the cheap modes can be re-run without
losing the expensive one.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d524_day5m_verification.json"
FIX = REPO / "data" / "fixtures"
HOURS = [f"h{h:02d}" for h in range(9, 16)]
TMP = REPO / "temp" / "fut_day5m_D524_REBUILD.parquet"


def merge_out(key, value):
    r = json.loads(OUT.read_text()) if OUT.exists() else {}
    r[key] = value
    r["run_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    OUT.write_text(json.dumps(r, indent=1, default=float))


# ------------------------------------------------------------------ 1. the build is reproducible
def rebuild_diff():
    """Re-run do_build() into temp/ and diff row for row. The committed parquet is never written."""
    import build_fut_day5m as d5
    committed = d5.OUT
    d5.OUT = TMP
    d5.META = REPO / "temp" / "fut_day5m_D524_REBUILD.meta.json"
    print(f"committed (untouched) {committed}\nrebuilding to         {TMP}")
    t0 = time.time()
    rc = d5.do_build()
    wall = time.time() - t0
    o, n = pd.read_parquet(committed), pd.read_parquet(TMP)
    assert list(o.columns) == list(n.columns) and len(o) == len(n), f"shape moved: {o.shape} vs {n.shape}"
    per = {}
    for c in o.columns:
        a, b = o[c], n[c]
        if a.dtype.kind in "if":
            af, bf = a.to_numpy(float), b.to_numpy(float)
            fin = np.isfinite(af) & np.isfinite(bf)
            d = np.where(fin, np.abs(af - bf), np.where(np.isfinite(af) != np.isfinite(bf), np.inf, 0.0))
            per[c] = int((d > 0).sum())
        else:
            per[c] = int((a.astype(str) != b.astype(str)).sum())
    h_o = hashlib.sha256(Path(committed).read_bytes()).hexdigest()
    h_n = hashlib.sha256(TMP.read_bytes()).hexdigest()
    res = dict(rc=int(rc), wall_min=round(wall / 60, 2), rows=int(len(o)), columns=list(o.columns),
               differing_by_column=per, total_differing=int(sum(per.values())),
               sha256_committed=h_o[:16], sha256_rebuilt=h_n[:16], file_identical=bool(h_o == h_n))
    print(f"  {len(o):,} rows, {sum(per.values())} differing values, file identical: {res['file_identical']} "
          f"({h_o[:16]}), {wall/60:.1f} min")
    merge_out("rebuild_diff", res)
    return res


# ------------------------------------------------------------------ 2. the decode agrees with a separate decode
def aggregate_check():
    """Fold the 5-minute bars into hours and compare against the breadth fixture, field by field."""
    G = pd.read_parquet(FIX / "fut_day5m.parquet")
    G["hour"] = 9 + (G["bar"].to_numpy() // 12)
    G = G[G["hour"].between(9, 15)]
    agg = G.sort_values(["root", "day", "bar"], kind="stable").groupby(["root", "day", "hour"], as_index=False).agg(
        o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"),
        v=("volume", "sum"), n=("n", "sum"))
    cols = ["root", "day"] + [f"{p}_{s}" for p in HOURS for s in ("o", "h", "l", "c", "v", "n")]
    B = pd.read_csv(FIX / "fut_breadth_hourly.csv.gz", usecols=cols, dtype={"root": str, "day": str})
    long = []
    for hh in HOURS:
        x = B[["root", "day"] + [f"{hh}_{s}" for s in ("o", "h", "l", "c", "v", "n")]].copy()
        x.columns = ["root", "day", "o", "h", "l", "c", "v", "n"]
        x["hour"] = int(hh[1:])
        long.append(x)
    Bl = pd.concat(long, ignore_index=True).dropna(subset=["o", "c"])
    j = agg.merge(Bl, on=["root", "day", "hour"], how="inner", suffixes=("_5m", "_hr"))
    per = {}
    for s in ("o", "h", "l", "c", "v", "n"):
        a, b = j[f"{s}_5m"].to_numpy(float), j[f"{s}_hr"].to_numpy(float)
        fin = np.isfinite(a) & np.isfinite(b)
        per[s] = dict(differing=int((np.abs(a[fin] - b[fin]) > 1e-9).sum()),
                      max_abs=float(np.abs(a[fin] - b[fin]).max()) if fin.any() else 0.0)
    res = dict(hours_compared=int(len(j)), hours_only_day5m=int(len(agg) - len(j)), hours_only_breadth=int(len(Bl) - len(j)),
               per_field=per, total_differing=int(sum(v["differing"] for v in per.values())))
    print(f"  {len(j):,} root-session-hours; only-day5m {res['hours_only_day5m']}, only-breadth {res['hours_only_breadth']}; "
          f"{res['total_differing']} differing values across o/h/l/c/v/n")
    merge_out("aggregation_vs_breadth", res)
    return res


# ------------------------------------------------------------------ 3. what a FLAT dict would have done
def _flat_and_windows(store, B):
    w = B.ids_of(store)
    flat = {}
    for sym, ivs in store.metadata.mappings.items():
        m = B.OUTRIGHT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                flat[int(sid)] = str(sym)
    return w, flat


def precheck():
    import databento as db
    import build_fut_breadth_hourly as B
    files = B.ohlcv_files()
    print(f"  {len(files)} files, {len(B.ROOTS)} roots")
    t0 = time.time()
    rows = []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        w, flat = _flat_and_windows(store, B)
        mis = 0 if w is None else int((w["contract"].to_numpy() != [flat[x] for x in w["iid"]]).sum())
        foreign = 0
        for sym, ivs in store.metadata.mappings.items():
            if B.OUTRIGHT.match(str(sym)):
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid and int(sid) in flat:
                    foreign += 1
        rows.append(dict(file=f.name, ids=int(w["iid"].nunique()), windows=int(len(w)), mislabelled=mis, foreign=foreign))
        print(f"  [{i:2d}/{len(files)}] {f.name[10:18]}  windows {len(w):>5}  mislabelled {mis:>3}  foreign {foreign:>5}  "
              f"({(time.time()-t0)/60:.1f} min)", flush=True)
    d = pd.DataFrame(rows)
    res = dict(files=len(d), windows=int(d.windows.sum()), mislabelled=int(d.mislabelled.sum()),
               foreign=int(d.foreign.sum()), files_with_mislabels=int((d.mislabelled > 0).sum()),
               files_with_foreign=int((d.foreign > 0).sum()), per_file=rows, wall_min=round((time.time() - t0) / 60, 1))
    print(f"  TOTAL mislabelled {res['mislabelled']} of {res['windows']:,} windows; foreign windows {res['foreign']:,}")
    merge_out("flat_map_counterfactual", res)
    return res


def name_mislabels(years):
    """Resolve mislabelled windows to the contract each one really is. A count is not an object."""
    import databento as db
    import build_fut_breadth_hourly as B
    files = [f for f in B.ohlcv_files() if any(f.name[10:14] == y for y in years)]
    out = []
    for f in files:
        store = db.DBNStore.from_file(f)
        w, flat = _flat_and_windows(store, B)
        w = w.copy()
        w["flat_label"] = [flat[x] for x in w["iid"]]
        bad = w[w["contract"] != w["flat_label"]]
        print(f"  {f.name[10:18]}: {len(bad)} of {len(w):,} windows")
        for r in bad.itertuples():
            rec = dict(file=f.name, iid=int(r.iid), root=r.root, really=r.contract, flat_would_say=r.flat_label,
                       valid_from=str(pd.Timestamp(int(r.w0), unit="ns", tz="UTC").date()),
                       valid_to=str(pd.Timestamp(int(r.w1), unit="ns", tz="UTC").date()),
                       cross_root=bool(r.contract[:2] != r.flat_label[:2]))
            out.append(rec)
            print(f"     iid {rec['iid']:>9}  REALLY {rec['really']:<8} {rec['valid_from']} .. {rec['valid_to']}"
                  f"   flat dict would say {rec['flat_would_say']}{'   <-- DIFFERENT ROOT' if rec['cross_root'] else ''}")
    res = dict(years=list(years), n=len(out), cross_root=int(sum(x["cross_root"] for x in out)),
               by_root=pd.DataFrame(out).groupby("root").size().to_dict() if out else {}, windows=out)
    merge_out("named_mislabels", res)
    return res


CHILD = r"""
import sys, json
sys.path.insert(0, r"{scripts}")
import databento as db
import build_fut_breadth_hourly as B
f = [x for x in B.ohlcv_files() if x.name[10:14] == "{year}"][0]
store = db.DBNStore.from_file(f)
w = B.ids_of(store)
flat, order = {{}}, []
for sym, ivs in store.metadata.mappings.items():
    if not B.OUTRIGHT.match(str(sym)):
        continue
    for iv in (ivs if isinstance(ivs, list) else [ivs]):
        sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
        if sid:
            flat[int(sid)] = str(sym)
            order.append(str(sym))
m = w.groupby("iid")["contract"].nunique()
print(json.dumps(dict(surviving={{str(i): flat[i] for i in m[m > 1].index.tolist()}},
                      first_ten=order[:10], n=len(order))))
"""


def determinism(year="2019", seeds=(0, 1, 2, 3, 4, 5)):
    """Is the flat dict's SURVIVING label even the same twice? One process per hash seed.

    Two runs of the naming code disagreed about which of iid 436191's windows a flat dict mislabels.
    Only one explanation fits: `store.metadata.mappings` iterates in an order that varies between
    processes, so "the last write wins" picks a different winner each time.

    READ THE COUNT RIGHT. An id carrying k labels is unstable IN PRINCIPLE; a finite probe only
    catches it when two draws happen to differ. With k = 2 and n draws, an unstable id LOOKS stable
    with probability 2^-(n-1) -- 25% at n = 3 -- so a three-seed probe is expected to miss about two
    of eight, and to miss a DIFFERENT two next time. `expected_false_stable` reports that, because
    "5 of 8" and "6 of 8" are the same finding and reporting either as the rate would be wrong.
    """
    import subprocess, os
    src = CHILD.format(scripts=str(REPO / "scripts"), year=year)
    runs = []
    for s in seeds:
        env = dict(os.environ); env["PYTHONHASHSEED"] = str(s)
        p = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, env=env)
        if p.returncode != 0:
            raise RuntimeError(f"child failed (seed {s}): {p.stderr[-1500:]}")
        runs.append(json.loads(p.stdout.strip().splitlines()[-1]))
        print(f"  seed {s}: {runs[-1]['n']:,} outright symbol-windows; first five {runs[-1]['first_ten'][:5]}")
    ids = sorted(set().union(*(set(r["surviving"]) for r in runs)))
    per, unstable = {}, []
    for i in ids:
        vals = [r["surviving"].get(i) for r in runs]
        per[i] = vals
        if len(set(vals)) > 1:
            unstable.append(i)
        print(f"  iid {i:>9}  surviving flat label per run: {vals}{'   <-- VARIES' if len(set(vals)) > 1 else ''}")
    n = len(seeds)
    expected_false_stable = round(len(ids) * 2.0 ** (-(n - 1)), 2)
    res = dict(year=year, seeds=list(seeds), multi_label_ids=len(ids), unstable_ids=len(unstable),
               observed_stable=len(ids) - len(unstable), expected_false_stable=expected_false_stable,
               iteration_order_stable=bool(len({tuple(r["first_ten"]) for r in runs}) == 1), per_id=per)
    print(f"  {len(unstable)} of {len(ids)} ids OBSERVED to flip in {n} draws; {len(ids)-len(unstable)} looked stable "
          f"against {expected_false_stable} expected to look stable BY CHANCE if all of them are unstable")
    print(f"  symbol iteration order stable across processes: {res['iteration_order_stable']}")
    merge_out("flat_label_determinism", res)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--determinism", action="store_true", help="is the flat dict's surviving label reproducible?")
    ap.add_argument("--rebuild-diff", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--name", nargs="*", metavar="YEAR")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if not any([a.rebuild_diff, a.aggregate, a.precheck, a.determinism, a.name is not None, a.all]):
        ap.error("pick a mode")
    if a.all or a.rebuild_diff:
        print("== 1. the build is reproducible from its cache")
        rebuild_diff()
    if a.all or a.aggregate:
        print("== 2. the decode agrees with the breadth fixture's separate decode")
        aggregate_check()
    if a.all or a.precheck:
        print("== 3. what a FLAT id dict would have done to these 36 roots")
        precheck()
    if a.all or a.determinism:
        print("== 5. is the flat dict's surviving label even reproducible?")
        determinism()
    if a.all or a.name is not None:
        print("== 4. the mislabelled windows, resolved to contracts")
        name_mislabels(a.name or ["2019", "2020"])
    print(f"\n-> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
