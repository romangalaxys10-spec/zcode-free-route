#!/usr/bin/env python3
"""Probe OpenAI-compatible endpoints for latency and keep an EWMA history."""
import argparse, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

CFG = os.path.expanduser("~/.config/zcode-free-route/config.json")
HIST = os.path.expanduser("~/.local/share/zcode-free-route/history.jsonl")
ALPHA = 0.3

def load_cfg():
    try:
        cfg = json.load(open(CFG, encoding="utf-8"))
    except FileNotFoundError:
        print("no config at %s; create it first (endpoints: name, base_url, "
              "optional model, optional auth_header_env)" % CFG, file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print("bad config JSON: %s" % e, file=sys.stderr)
        sys.exit(2)
    eps = cfg.get("endpoints", [])
    if not eps:
        print("config has no endpoints", file=sys.stderr)
        sys.exit(2)
    return eps

def load_ewma():
    ew = {}
    try:
        with open(HIST, encoding="utf-8") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                    ew[o["name"]] = o["ewma_total"]
                except (json.JSONDecodeError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return ew

def probe(ep):
    name = ep.get("name", ep.get("base_url", "?"))
    url = ep["base_url"].rstrip("/") + ("/models" if not ep.get("model") else "/chat/completions")
    req = urllib.request.Request(url)
    env_name = ep.get("auth_header_env")
    if env_name:
        val = os.environ.get(env_name)
        if not val:
            return {"name": name, "error": "env %s not set" % env_name}
        req.add_header("Authorization", "Bearer " + val)
    body = None
    if ep.get("model"):
        body = json.dumps({"model": ep["model"], "max_tokens": 1,
                           "messages": [{"role": "user", "content": "ping"}]}).encode()
        req.add_header("Content-Type", "application/json")
        req.get_method = lambda: "POST"
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, body, timeout=20) as r:
            r.read()
        total = (time.time() - t0) * 1000
        return {"name": name, "ttfb": round(total, 1), "total": round(total, 1)}
    except urllib.error.HTTPError as e:
        total = (time.time() - t0) * 1000
        return {"name": name, "error": "HTTP %d" % e.code, "total": round(total, 1)}
    except Exception as e:
        return {"name": name, "error": str(e)[:80]}

def main():
    ap = argparse.ArgumentParser(description="probe model endpoints, rank by latency")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    eps = load_cfg()
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(probe, eps))
    ew = load_ewma()
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "a", encoding="utf-8") as fh:
        for r in results:
            if "total" in r:
                prev = ew.get(r["name"])
                r["ewma_total"] = round(r["total"] if prev is None else ALPHA * r["total"] + (1 - ALPHA) * prev, 1)
                ew[r["name"]] = r["ewma_total"]
                fh.write(json.dumps({"name": r["name"], "ewma_total": r["ewma_total"],
                                     "ts": round(time.time())}) + "\n")
    rows = []
    for r in results:
        e = ew.get(r["name"])
        degraded = bool(e and "total" in r and e and r["total"] > 2 * e)
        rows.append({"name": r["name"], "total": r.get("total"),
                     "ewma": e, "error": r.get("error"), "degraded": degraded})
    rows.sort(key=lambda r: (r["error"] is not None, r["total"] if r["total"] is not None else 9e9))
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        print("# Endpoint latency (fastest first)\n")
        for r in rows:
            if r["error"]:
                print("- %s: ERROR %s" % (r["name"], r["error"]))
            else:
                flag = "  DEGRADED (>2x own EWMA)" if r["degraded"] else ""
                print("- %s: %sms total (ewma %s)%s" % (r["name"], r["total"], r["ewma"], flag))
        best = next((r for r in rows if not r["error"]), None)
        if best:
            print("\nRecommendation: %s (failover: %s)" % (
                best["name"], next((r["name"] for r in rows if not r["error"] and r is not best), "none")))
    return 0

if __name__ == "__main__":
    sys.exit(main())
