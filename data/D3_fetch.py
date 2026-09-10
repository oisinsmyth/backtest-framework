"""D3 lane fetcher. Pace 0.4s. Writes bytes to disk, reports status/size/content-type/sha1.

Usage: python D3_fetch.py URL[::name] ...
"""
import sys, os, time, urllib.request, urllib.error, hashlib

UA = "D3-research/1.0 (research@backtest-framework.org)"
OUT = os.path.dirname(os.path.abspath(__file__))


def get(url, name=None, pace=0.4, headers=None):
    name = name or ("D3_" + url.rsplit("/", 1)[-1].split("?")[0])
    path = os.path.join(OUT, name)
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
            ct = r.headers.get("Content-Type")
            code = r.status
            final = r.geturl()
    except urllib.error.HTTPError as e:
        body = e.read()
        ct = e.headers.get("Content-Type") if e.headers else None
        code = e.code
        final = url
    except Exception as e:
        print("ERR  %s -> %s: %s" % (url, type(e).__name__, e))
        time.sleep(pace)
        return None
    with open(path, "wb") as f:
        f.write(body)
    print("%s %10d %s sha1=%s %.1fs -> %s" % (code, len(body), ct, hashlib.sha1(body).hexdigest()[:12], time.time() - t0, name))
    if final != url:
        print("     final=%s" % final)
    print("     first120=%r" % (body[:120],))
    time.sleep(pace)
    return path


if __name__ == "__main__":
    for a in sys.argv[1:]:
        if "::" in a:
            url, nm = a.split("::", 1)
            get(url, nm)
        else:
            get(a)
