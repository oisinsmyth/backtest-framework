"""Fetch UNG's and USO's monthly account statements (CFTC Rule 4.22, furnished as 8-K Exhibit 99.1) from USCF's public library.

AITODO 1e. USCF's ETP Document Library (https://www.uscfinvestments.com/resources/{ung,uso}) links
each monthly statement as a public PDF under
    https://secure.alpsinc.com/MarketingAPI/api/v1/Content/uscfinvestments/<fund-slug>-8-kms-<YYYYMMDD>.pdf
The date in the name is the filing date, not the month. The list below was read off the library
pages on 2026-09-24 and cut to files dated on or before 2024-01-31, whose statements cover months
up to December 2023. Each statement gives the month-end NAV, the NAV per share, the shares
outstanding, and the shares added and withdrawn in the month.

Plain GETs of public documents, one every half second, into `data/raw/uscf/monthly_statements/`
(gitignored cache). Files already on disk are not fetched again.

    uv run python scripts/fetch_uscf_monthly_statements.py
"""
from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "raw" / "uscf" / "monthly_statements"
BASE = "https://secure.alpsinc.com/MarketingAPI/api/v1/Content/uscfinvestments/"
SLUG = {"UNG": "united-states-natural-gas-fund", "USO": "united-states-oil-fund"}
DATES = {
    "UNG": "20170131,20170228,20170330,20170331,20170531,20170630,20170829,20170831,20170930,20171031,20171130,"
           "20171231,20180228,20180331,20180430,20180531,20180630,20180731,20180927,20180930,20181031,20181130,"
           "20181231,20190131,20190228,20190331,20190430,20190531,20190630,20190731,20190831,20190930,20191031,"
           "20191130,20191231,20200131,20200229,20200331,20200430,20200531,20200630,20200731,20200831,20200930,"
           "20201031,20201130,20201231,20210131,20210228,20210331,20210430,20210531,20210729,20210827,20210831,"
           "20211028,20211031,20211130,20211231,20220131,20220228,20220331,20220430,20220531,20220630,20220731,"
           "20220831,20220930,20221031,20221228,20221231,20230131,20230228,20230331,20230430,20230531,20230630,"
           "20230731,20230831,20230930,20231031,20231130,20231231,20240131",
    "USO": "20170131,20170228,20170330,20170331,20170531,20170630,20170829,20170831,20170930,20171031,20171130,"
           "20171231,20180131,20180228,20180331,20180430,20180531,20180630,20180731,20180927,20180930,20181031,"
           "20181130,20181231,20190131,20190228,20190331,20190430,20190531,20190630,20190731,20190831,20190930,"
           "20191031,20191130,20191231,20200131,20200229,20200331,20200430,20200531,20200630,20200731,20200831,"
           "20200930,20201031,20201130,20201231,20210131,20210228,20210331,20210430,20210531,20210727,20210831,"
           "20211028,20211031,20211130,20211231,20220131,20220228,20220331,20220430,20220531,20220630,20220731,"
           "20220831,20220930,20221031,20221228,20221231,20230131,20230228,20230331,20230430,20230531,20230630,"
           "20230731,20230831,20230930,20231031,20231130,20231231,20240131",
}


#: statements the library files as plain 8-Ks (found 2026-09-24 by listing every document on the
#: library pages; the missing months UNG 2017-04 / 2018-01 and USO 2017-04 / 2021-06)
EXTRA = ["united-states-natural-gas-fund-8-k-20170525.pdf", "united-states-natural-gas-fund-8-k-20180131.pdf",
         "united-states-oil-fund-8-k-20170525.pdf", "united-states-oil-fund-8-k-20210729.pdf"]


#: USO's other 8-Ks, 2019-2023, from its library page (2026-09-24): the 2020 portfolio changes live here
USO_8K = ("20190329,20190401,20200320,20200324,20200330,20200416,20200420,20200421-1,20200421,20200422,"
          "20200424,20200427,20200428,20200430,20200529,20200609,20200612,20200623,20200819,20200821,20200902,"
          "20201203,20210323,20210325,20210729,20211108,20211130,20220324,20220325,20220615,20221003,20230322,"
          "20230324,20230401,20230808,20230829,20231114")
USO_8K_DIR = REPO / "data" / "raw" / "uscf" / "uso_8k"


def main() -> int:
    if "--uso-8k" in sys.argv:
        return fetch([f"united-states-oil-fund-8-k-{d}.pdf" for d in USO_8K.split(",")], USO_8K_DIR)
    names = [f"{SLUG[fund]}-8-kms-{d}.pdf" for fund, dates in DATES.items() for d in dates.split(",")] + EXTRA
    return fetch(names, OUT)


def fetch(names: list[str], out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    got = skipped = 0
    for name in names:
        path = out / name
        if path.exists() and path.stat().st_size > 0:
            skipped += 1
            continue
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        if not body.startswith(b"%PDF"):
            raise SystemExit(f"{name}: not a PDF ({body[:40]!r})")
        path.write_bytes(body)
        got += 1
        time.sleep(0.5)
    print(f"fetched {got}, already on disk {skipped}, into {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
