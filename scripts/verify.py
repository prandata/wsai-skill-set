#!/usr/bin/env python3
"""Re-check every trick's check_url and update tricks.yaml in place.

  python3 scripts/verify.py            # check all, write results
  python3 scripts/verify.py --dry      # print only

A 2xx/3xx response refreshes `checked`. A failure sets `last_fail`; two failed runs in a row
mark the trick `broken`, and the newsletter build drops it. A page loading does not prove the
trick works (single-page apps serve a shell), so shoot-day checks still happen in a browser."""
import sys, datetime, subprocess, yaml
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "tricks.yaml"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

def code(url):
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-m", "15", "-A", UA, "-w", "%{http_code}", url], capture_output=True, text=True)
    return int(r.stdout or 0)

def main(dry):
    d = yaml.safe_load(P.read_text()); today = datetime.date.today().isoformat(); bad = []
    for t in d["tricks"]:
        u = t.get("check_url")
        if not u: continue
        c = code(u); ok = 200 <= c < 400 or (c == 0 and "parrot.live" in u)  # parrot.live streams forever
        print(f"{t['id']} {c:>3} {'ok' if ok else 'FAIL'} {u}")
        if dry: continue
        if ok:
            t["checked"] = today; t.pop("last_fail", None)
            if t["status"] == "broken": t["status"] = "verified"
        else:
            if t.get("last_fail"): t["status"] = "broken"
            t["last_fail"] = f"{today} HTTP {c}"; bad.append(t["id"])
    if not dry:
        d["updated"] = today; P.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=200))
    print("failed:", bad or "none")

if __name__ == "__main__":
    main("--dry" in sys.argv)
