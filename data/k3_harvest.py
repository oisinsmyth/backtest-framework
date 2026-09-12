"""K3: harvest every 8-K submission's item codes from SEC bulk submissions.zip.

Route: https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
  (SEC primary doc: "contains the public EDGAR filing history for all filers
   from the Submissions API", recompiled nightly.)

Output: one TSV per worker, columns
  accno_int  filing_year  filing_date  form  items
De-duplication on accession number happens in the REDUCE step (K3_reduce.py),
because a single accession appears in the submissions file of EVERY
co-registrant CIK on that filing.

Year bucket = year of `filingDate` (a DATE). This deliberately avoids
`acceptanceDateTime`, which the programme has found to be timezone-inconsistent.
"""
import json
import os
import sys
import zipfile

if len(sys.argv) > 4:          # importable for the chunk==whole verifier
    ZIP = sys.argv[1]
    OUT_DIR = sys.argv[2]
    WORKER = int(sys.argv[3])
    NWORKERS = int(sys.argv[4])

FORMS = ("8-K",)  # prefix match; captures 8-K, 8-K/A, 8-K12B, 8-K12G3, 8-K15D5


def rows_from(obj):
    """Yield (accno, filingDate, form, items) from a submissions JSON object.

    Handles both the top-level CIK##########.json (arrays under
    filings.recent) and the overflow CIK##########-submissions-00N.json
    (arrays at top level)."""
    if "filings" in obj:
        blocks = [obj["filings"].get("recent") or {}]
    else:
        blocks = [obj]
    for b in blocks:
        forms = b.get("form")
        if not forms:
            continue
        acc = b["accessionNumber"]
        fd = b["filingDate"]
        it = b.get("items") or [""] * len(forms)
        for i, f in enumerate(forms):
            if f.startswith(FORMS):
                yield acc[i], fd[i], f, it[i]


def main():
    zf = zipfile.ZipFile(ZIP)
    names = zf.namelist()
    mine = names[WORKER::NWORKERS]
    out = open(os.path.join(OUT_DIR, "K3_rows_%02d.tsv" % WORKER), "w",
               encoding="utf-8", newline="\n")
    n_members = 0
    n_rows = 0
    n_bad = 0
    for nm in mine:
        if not nm.endswith(".json"):
            continue
        n_members += 1
        try:
            obj = json.loads(zf.read(nm))
        except Exception:
            n_bad += 1
            continue
        # CIK of the submissions file this record came from. Member names are
        # CIK##########.json or CIK##########-submissions-00N.json.
        base = os.path.basename(nm)
        cik = base[3:13] if base.startswith("CIK") else "?"
        try:
            for acc, fd, form, items in rows_from(obj):
                ai = acc.replace("-", "")
                out.write("%s\t%s\t%s\t%s\t%s\n" % (ai, fd, form, items, cik))
                n_rows += 1
        except Exception:
            n_bad += 1
    out.close()
    sys.stderr.write("worker %d: members=%d rows=%d bad=%d\n"
                     % (WORKER, n_members, n_rows, n_bad))


if __name__ == "__main__":
    main()
