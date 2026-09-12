import json, statistics

c = json.load(open("A4_census.json"))
for k, yr in c.items():
    tot = sum(v[0] for v in yr.values() if isinstance(v[0], int))
    print(f"{k:18s} sum over 2010..2026 per-year slices = {tot:,}")

feed = json.load(open("A4_feed_sizes.json"))
vals = [v for _, v in feed]
# per-year mean x ~247 trading days, summed (2026 partial: ~163 days to Aug 26)
byyear = {}
for d, v in feed: byyear.setdefault(d[:4], []).append(v)
total = 0
for y, vs in sorted(byyear.items()):
    days = 163 if y == "2026" else 251
    total += statistics.mean(vs) * days
print(f"\nFEED: per-year-mean x trading days, 2010..2026-08 = {total/1e12:.2f} TB compressed")
print(f"FEED: flat mean x 4187 days = {statistics.mean(vals)*4187/1e12:.2f} TB")
print(f"FEED requests = ~4,187 (one per trading day); largest single member {max(vals)/1e9:.2f} GB")

d = json.load(open("A4_docsize.json"))
print(f"\nDOC mean={statistics.mean(d['doc']):,.0f}B  SUB mean={statistics.mean(d['sub']):,.0f}B")

N_8K = 1_185_352
print(f"\n--- ROUTE COSTS for the 8-K universe (n={N_8K:,}) ---")
print(f" hdr.sgml only (items+acceptance), 921 B mean : {N_8K*921/1e9:.2f} GB, {N_8K:,} requests")
print(f" full submission .txt, 216,743 B mean         : {N_8K*216743/1e12:.2f} TB, {N_8K:,} requests")
print(f" at 10 req/s sustained: {N_8K/10/3600:.1f} h of requests; at 5 req/s: {N_8K/5/3600:.1f} h")

# targeted FTS route
div = sum(v[0] for v in c["A_div_quarterly"].values()) + sum(v[0] for v in c["B_div_cash"].values())
print(f"\n--- TARGETED FTS ROUTE (dividend phrases A+B) ---")
print(f" FTS hits = {div:,} documents; at 0.844 unique-accession ratio = ~{int(div*0.844):,} filings")
print(f" FTS result pages at 100/page = {div//100+1:,} requests")
print(f" + exhibit fetch at 13,547 B mean = {div*13547/1e9:.2f} GB, {div:,} requests")
print(f" + hdr.sgml for item codes = {int(div*0.844)*921/1e6:.0f} MB, {int(div*0.844):,} requests")
tot_req = div//100+1 + div + int(div*0.844)
print(f" TOTAL ~{tot_req:,} requests, ~{(div*13547 + int(div*0.844)*921)/1e9:.2f} GB; at 5 req/s = {tot_req/5/3600:.2f} h")
