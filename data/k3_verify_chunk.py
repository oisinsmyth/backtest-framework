"""K3 control: chunk == whole.

Re-harvests the ENTIRE zip in ONE process and asserts the resulting row
multiset is identical to the union of the 12 striped worker outputs.
Guards against a silently dropped or truncated worker (worker stderr was lost
to an append race, so the coverage claim needs an independent check).
"""
import glob
import hashlib
import json
import os
import sys
import zipfile

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from K3_harvest import rows_from  # noqa: E402

ZIP = os.path.join(SP, "K3_submissions.zip")


def whole():
    zf = zipfile.ZipFile(ZIP)
    out = []
    nm_count = 0
    for nm in zf.namelist():
        if not nm.endswith(".json"):
            continue
        nm_count += 1
        base = os.path.basename(nm)
        cik = base[3:13] if base.startswith("CIK") else "?"
        obj = json.loads(zf.read(nm))
        for acc, fd, form, items in rows_from(obj):
            out.append("%s\t%s\t%s\t%s\t%s" % (acc.replace("-", ""), fd, form,
                                               items, cik))
    return out, nm_count


def chunks():
    out = []
    for fp in sorted(glob.glob(os.path.join(SP, "K3_rows_*.tsv"))):
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                out.append(line.rstrip("\n"))
    return out


print("re-harvesting whole zip in one process ...")
w, nmc = whole()
c = chunks()
print("members read (single process): %d" % nmc)
print("rows whole  : %d" % len(w))
print("rows chunked: %d" % len(c))
ws, cs = sorted(w), sorted(c)
hw = hashlib.sha256("\n".join(ws).encode()).hexdigest()
hc = hashlib.sha256("\n".join(cs).encode()).hexdigest()
print("sha256 whole  : %s" % hw)
print("sha256 chunked: %s" % hc)
if ws == cs:
    print("RESULT: chunk == whole, BIT-IDENTICAL over %d rows" % len(ws))
else:
    only_w = set(ws) - set(cs)
    only_c = set(cs) - set(ws)
    print("RESULT: MISMATCH. only-in-whole=%d only-in-chunked=%d"
          % (len(only_w), len(only_c)))
    for x in list(only_w)[:5]:
        print("  only whole  :", x)
    for x in list(only_c)[:5]:
        print("  only chunked:", x)
    sys.exit(1)

# Deliberate-break self-test: the check must FAIL on a corrupted chunk set.
print()
print("SELF-TEST (the check must raise on a deliberately broken chunk set):")
broken = cs[:-1]
assert sorted(broken) != ws, "SELF-TEST FAILED: check cannot detect a dropped row"
print("  dropping one row -> detected. OK")
broken2 = list(cs)
broken2[0] = broken2[0].replace("\t8-K\t", "\t8-K/A\t", 1)
assert sorted(broken2) != ws, "SELF-TEST FAILED: check cannot detect a mutated row"
print("  mutating one row -> detected. OK")
