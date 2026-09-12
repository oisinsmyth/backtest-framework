"""D3: extract text from a PDF with pypdf; write .txt beside it; print header facts.

Usage: python D3_pdf2txt.py file.pdf [file2.pdf ...]
Prints: page count, producer, first 300 chars of page 1, output path + char count.
This is the local-extraction step the campaign's summariser rule requires.
"""
import sys, os, io
import pypdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

for p in sys.argv[1:]:
    try:
        r = pypdf.PdfReader(p)
    except Exception as e:
        print("FAIL %s: %s: %s" % (p, type(e).__name__, e))
        continue
    n = len(r.pages)
    pages = []
    for i, pg in enumerate(r.pages):
        try:
            pages.append(pg.extract_text() or "")
        except Exception as e:
            pages.append("[[PAGE %d EXTRACT FAIL %s]]" % (i + 1, e))
    txt = "\n\n=== PAGE %d ===\n\n".join([""]) if False else ""
    out_parts = []
    for i, t in enumerate(pages):
        out_parts.append("\n\n===== PAGE %d =====\n\n" % (i + 1) + t)
    txt = "".join(out_parts)
    out = os.path.splitext(p)[0] + ".txt"
    open(out, "w", encoding="utf-8").write(txt)
    meta = {}
    try:
        meta = dict(r.metadata or {})
    except Exception:
        pass
    print("%s : pages=%d chars=%d -> %s" % (p, n, len(txt), out))
    print("   meta Producer=%r Title=%r" % (str(meta.get("/Producer"))[:60], str(meta.get("/Title"))[:90]))
    print("   p1[:300]=%r" % (pages[0][:300] if pages else None,))
