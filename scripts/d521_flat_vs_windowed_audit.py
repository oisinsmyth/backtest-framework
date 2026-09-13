"""D521 -- every number in the record, recomputed from the repository and the archive.

The three remaining flat-id builders (`build_fut_open_interest`, `build_fut_micro_flow`,
`build_fut_index_1m`) were ported to the windowed mapping and their fixtures rebuilt. This script is
the evidence: it compares the committed (flat-map) fixtures and metas against what is on disk now.

    python scripts/d521_flat_vs_windowed_audit.py                    # the cheap parts, -> data/d521_flat_vs_windowed_audit.json
    python scripts/d521_flat_vs_windowed_audit.py --precheck         # + the 20-min archive metadata scan (needs databento: SYSTEM python)
    python scripts/d521_flat_vs_windowed_audit.py --baseline REV     # compare against a revision other than the one named below

The flat-map side is read from git, not from `temp/`, so this reproduces after `temp/` is deleted.
BASELINE is the last commit whose fixtures were built by the flat map; once D521 is committed, that
is D521's own parent and `--baseline` is how a later reader points at it.
"""
from __future__ import annotations
import argparse, io, json, re, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d521_flat_vs_windowed_audit.json"
BASELINE = "HEAD"
FIX = "data/fixtures"
OI = f"{FIX}/fut_open_interest_daily.csv.gz"
OI_META = f"{FIX}/fut_open_interest_daily.meta.json"
IX_META = f"{FIX}/fut_index_1m.meta.json"
MF = f"{FIX}/fut_micro_flow_5m.csv.gz"
INDEX_FIXTURES = [f"{FIX}/fut_{r}_rth_1m.csv.gz" for r in ("ES", "NQ", "YM", "RTY")] + \
                 [f"{FIX}/fut_index_sessions.csv.gz", f"{FIX}/fut_index_rolls.csv.gz"]


def from_git(rev, path):
    """The committed bytes of `path` at `rev`, or None if that revision has no such file."""
    p = subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{path}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def read_csv_gz(blob, **kw):
    return pd.read_csv(io.BytesIO(blob), compression="gzip", **kw)


# ---------------------------------------------------------------------------------- 1. the open-interest fixture
def oi_diff(rev):
    old_b = from_git(rev, OI)
    if old_b is None:
        return dict(error=f"{OI} absent at {rev}")
    o = read_csv_gz(old_b, dtype={"root": str, "session": str})
    n = pd.read_csv(REPO / OI, dtype={"root": str, "session": str})
    key = ["root", "session"]
    mg = o.merge(n, on=key, how="outer", suffixes=("_old", "_new"), indicator=True)
    both = mg[mg._merge == "both"]
    cols, changed = {}, None
    for c in o.columns:
        if c in key:
            continue
        x, y = both[f"{c}_old"], both[f"{c}_new"]
        if x.dtype.kind in "if" and y.dtype.kind in "if":
            xf, yf = x.to_numpy(float), y.to_numpy(float)
            fin = np.isfinite(xf) & np.isfinite(yf)
            d = np.where(fin, np.abs(xf - yf), np.where(np.isfinite(xf) != np.isfinite(yf), np.inf, 0.0))
            nd = int((d > 0).sum())
            cols[c] = dict(differing=nd, max_abs=float(np.max(d[np.isfinite(d)])) if np.isfinite(d).any() else 0.0)
            if nd and changed is None:
                changed = both[d > 0]
        else:
            cols[c] = dict(differing=int(((x.astype(str) != y.astype(str)) & ~(x.isna() & y.isna())).sum()))
    rows = []
    if changed is not None:
        for r in changed.itertuples():
            rows.append(dict(root=r.root, session=r.session, oi_n_contracts_old=int(r.oi_n_contracts_old),
                             oi_n_contracts_new=int(r.oi_n_contracts_new), oi_total_old=int(r.oi_total_old),
                             oi_total_new=int(r.oi_total_new), oi_total_excess=int(r.oi_total_old - r.oi_total_new),
                             excess_pct_of_total=round(100 * (r.oi_total_old - r.oi_total_new) / r.oi_total_new, 4),
                             oi_front_changed=bool(r.oi_front_old != r.oi_front_new)))
    return dict(rows_old=len(o), rows_new=len(n),
                keys_both=int((mg._merge == "both").sum()), keys_only_old=int((mg._merge == "left_only").sum()),
                keys_only_new=int((mg._merge == "right_only").sum()),
                columns=cols, changed_rows=rows,
                front_changed_anywhere=any(r["oi_front_changed"] for r in rows))


# ---------------------------------------------------------------------------------- 2. fixtures that did not move
def unchanged(rev, paths):
    """Decompressed sha256 of each fixture, committed vs on disk -- the claim that content is identical."""
    import gzip, hashlib
    out = {}
    for p in paths:
        b = from_git(rev, p)
        cur = (REPO / p)
        if b is None or not cur.exists():
            out[p] = dict(error="absent")
            continue
        a = hashlib.sha256(gzip.decompress(b)).hexdigest()
        c = hashlib.sha256(gzip.decompress(cur.read_bytes())).hexdigest()
        out[p] = dict(sha256_committed=a[:16], sha256_ondisk=c[:16], identical=bool(a == c))
    return out


# ---------------------------------------------------------------------------------- 3. what each map INGESTED
def ingest_diff(rev, meta_path, kept_field):
    """Per-file rows the flat map accepted vs the windowed map, from the two metas' own provenance."""
    b = from_git(rev, meta_path)
    if b is None:
        return dict(error=f"{meta_path} absent at {rev}")
    fa = {x["file"]: x for x in json.loads(b)["files"]}
    fb = {x["file"]: x for x in json.loads((REPO / meta_path).read_text())["files"]}
    per, tot_o, tot_n = [], 0, 0
    for k in sorted(fa):
        if k not in fb:
            continue
        o, n = fa[k], fb[k]
        assert o["rows_in"] == n["rows_in"], f"{k}: the two builds did not read the same rows"
        tot_o += o[kept_field]; tot_n += n[kept_field]
        if o[kept_field] != n[kept_field]:
            per.append(dict(file=k, kept_flat=o[kept_field], kept_windowed=n[kept_field],
                            foreign=o[kept_field] - n[kept_field],
                            foreign_pct=round(100 * (o[kept_field] - n[kept_field]) / o[kept_field], 4)))
    return dict(rows_in=sum(x["rows_in"] for x in fa.values()), kept_flat=tot_o, kept_windowed=tot_n,
                foreign=tot_o - tot_n, foreign_pct=round(100 * (tot_o - tot_n) / max(tot_o, 1), 4),
                files_affected=len(per), files_total=len(fa),
                per_file=sorted(per, key=lambda x: -x["foreign"]))


# ---------------------------------------------------------------------------------- 4. gate scalars
def gates_diff(rev, meta_path):
    b = from_git(rev, meta_path)
    if b is None:
        return dict(error=f"{meta_path} absent at {rev}")
    def flat(d, p=""):
        out = {}
        if isinstance(d, dict):
            for k, v in d.items():
                out.update(flat(v, f"{p}.{k}" if p else str(k)))
        elif isinstance(d, list):
            out[p] = str(d)
        else:
            out[p] = d
        return out
    ga = flat(json.loads(b).get("gates") or {})
    gb = flat(json.loads((REPO / meta_path).read_text()).get("gates") or {})
    keys = sorted(set(ga) | set(gb))
    diff = {}
    for k in keys:
        x, y = ga.get(k, "<absent>"), gb.get(k, "<absent>")
        if not ((x == y) or (isinstance(x, float) and isinstance(y, float) and abs(x - y) < 1e-12)):
            diff[k] = [x, y]
    return dict(scalars=len(keys), identical=len(keys) - len(diff), changed=diff)


# ---------------------------------------------------------------------------------- 5. the archive itself
def phantom(root_re=r"^(ES|NQ|CL|GC)([FGHJKMNQUVXZ])(\d{1,2})$"):
    """Name every id whose flat label belongs to our roots while an EARLIER window of the same id does not.

    This is the defect in its pure form: the flat dict's surviving label is the last one written, so
    any earlier window of that id had its rows ingested under a symbol they never carried.
    """
    import databento as db
    OUTR = re.compile(root_re)
    files = sorted((REPO / "data" / "raw" / "databento").glob("*/*.statistics.dbn.zst"), key=lambda p: p.name)
    found = []
    for f in files:
        store = db.DBNStore.from_file(f)
        flat, windows = {}, {}
        for sym, ivs in store.metadata.mappings.items():
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if not sid:
                    continue
                s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
                e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                windows.setdefault(int(sid), []).append((str(sym), str(s), str(e)))
                if OUTR.match(str(sym)):
                    flat[int(sid)] = str(sym)
        for iid, label in flat.items():
            ws = sorted(windows[iid], key=lambda t: t[1])
            wrong = [w for w in ws if w[0] != label]
            if wrong:
                found.append(dict(file=f.name, iid=iid, flat_label=label,
                                  windows=[dict(contract=c, start=s, end=e) for c, s, e in ws],
                                  foreign_windows=len(wrong)))
    return found


def index_precheck():
    """Windows the flat map would mislabel in the ohlcv-1m archive, for the four index roots."""
    import databento as db
    sys.path.insert(0, str(REPO / "scripts"))
    import build_fut_index_1m as ix
    files = sorted((REPO / "data" / "raw" / "databento").glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    per = []
    for f in files:
        store = db.DBNStore.from_file(f)
        w = ix.ids_of(store)
        flat = {}
        for sym, ivs in store.metadata.mappings.items():
            if not ix.OUTRIGHT.match(str(sym)):
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid:
                    flat[int(sid)] = str(sym)
        mis = 0 if w is None else int((w["contract"] != [flat[i] for i in w["iid"]]).sum())
        foreign = 0
        for sym, ivs in store.metadata.mappings.items():
            if ix.OUTRIGHT.match(str(sym)):
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid and int(sid) in flat:
                    foreign += 1
        per.append(dict(file=f.name, ids=0 if w is None else int(w["iid"].nunique()),
                        windows=0 if w is None else int(len(w)), mislabelled_index_windows=mis,
                        foreign_windows_ingested_as_index=foreign))
        print(f"  {f.name[:44]:<44} mislabelled {mis:>3}  foreign {foreign:>4}", flush=True)
    return dict(files=len(per), mislabelled_index_windows=sum(p["mislabelled_index_windows"] for p in per),
                foreign_windows=sum(p["foreign_windows_ingested_as_index"] for p in per),
                files_with_foreign=sum(1 for p in per if p["foreign_windows_ingested_as_index"]), per_file=per)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=BASELINE, help="revision whose fixtures were built by the FLAT map")
    ap.add_argument("--precheck", action="store_true", help="also scan the ohlcv-1m archive metadata (~20 min)")
    ap.add_argument("--phantom", action="store_true", help="also name the reused ids in the statistics archive")
    a = ap.parse_args()
    t0 = time.time()
    r = dict(baseline=a.baseline, run_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    print("== open interest: the only fixture whose content moved")
    r["open_interest"] = oi_diff(a.baseline)
    d = r["open_interest"]
    if "error" not in d:
        print(f"  rows {d['rows_old']:,} -> {d['rows_new']:,}; keys both {d['keys_both']:,}, lost {d['keys_only_old']}, gained {d['keys_only_new']}")
        print(f"  changed rows {len(d['changed_rows'])}; front month changed anywhere: {d['front_changed_anywhere']}")
        for row in d["changed_rows"][:3]:
            print(f"    {row['root']} {row['session']}  contracts {row['oi_n_contracts_old']}->{row['oi_n_contracts_new']}  "
                  f"oi_total excess {row['oi_total_excess']:,} ({row['excess_pct_of_total']}%)")

    print("== fixtures whose content did NOT move")
    r["unchanged"] = unchanged(a.baseline, INDEX_FIXTURES + [MF, f"{FIX}/fut_micro_flow_rolls.csv.gz"])
    for p, v in r["unchanged"].items():
        print(f"  {Path(p).name:<30} {'identical' if v.get('identical') else v}")

    print("== rows each map INGESTED, from the two metas' own provenance")
    for name, path, field, unit in (("index_1m", IX_META, "rth_rows_kept", "RTH bars"),
                                    ("open_interest", OI_META, "rows_kept", "statistics records")):
        d = ingest_diff(a.baseline, path, field)
        r.setdefault("ingest", {})[name] = d
        if "error" in d:
            print(f"  {name}: {d['error']}")
            continue
        print(f"  {name:<14} archive rows {d['rows_in']:>15,}; {unit} kept flat {d['kept_flat']:>10,} vs windowed {d['kept_windowed']:>10,}")
        print(f"  {'':<14} foreign the flat map accepted: {d['foreign']:,} ({d['foreign_pct']}%) in {d['files_affected']} of {d['files_total']} files")
    r["index_ingest"] = r["ingest"]["index_1m"]

    print("== gate scalars")
    for name, path in (("open_interest", OI_META), ("index_1m", IX_META)):
        g = gates_diff(a.baseline, path)
        r.setdefault("gates", {})[name] = g
        print(f"  {name:<16} {g.get('identical')} of {g.get('scalars')} identical, {len(g.get('changed', {}))} changed")

    if a.phantom:
        print("== reused ids in the statistics archive")
        r["phantom"] = phantom()
        for p in r["phantom"]:
            print(f"  {p['file'][10:18]}  iid {p['iid']} flat-labelled {p['flat_label']}: " +
                  ", ".join(f"{w['contract']} {w['start']}..{w['end']}" for w in p["windows"]))
    if a.precheck:
        print("== ohlcv-1m mapping precheck")
        r["index_precheck"] = index_precheck()
        d = r["index_precheck"]
        print(f"  mislabelled index windows {d['mislabelled_index_windows']}; foreign windows {d['foreign_windows']} in {d['files_with_foreign']} of {d['files']} files")

    OUT.write_text(json.dumps(r, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
