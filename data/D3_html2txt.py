"""D3: strip HTML to text, write .txt beside it, print to stdout as UTF-8."""
import sys, re, html, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

for p in sys.argv[1:]:
    s = open(p, "rb").read().decode("latin-1")
    t = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = t.replace("\x92", "'").replace("\x93", '"').replace("\x94", '"').replace("\x96", "-").replace("\xa0", " ")
    t = re.sub(r"[ \t\r]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    out = os.path.splitext(p)[0] + ".txt"
    open(out, "w", encoding="utf-8").write(t)
    print("=== %s -> %s (%d chars) ===" % (p, out, len(t)))
    print(t)
