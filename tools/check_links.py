"""Check every internal link and #anchor in public/ resolves. Usage: python tools/check_links.py"""
import os, re, sys
P = "public"
pages = {f: open(f"{P}/{f}", encoding="utf-8").read() for f in os.listdir(P) if f.endswith(".html")}
ids = {f: set(re.findall(r'\bid="([^"]+)"', s)) for f, s in pages.items()}
# ids that app.js creates at runtime on the report page
ids["index.html"] |= {"mt", "asr", "ex", "find"}
bad, n = [], 0
for f, s in pages.items():
    for href in re.findall(r'href="([^"]+)"', s):
        if href.startswith(("http", "mailto:")):
            continue
        n += 1
        path, _, frag = href.partition("#")
        path = path.split("?")[0]
        if path == "":
            target = f
        elif path == "/":
            target = "index.html"
        else:
            p = path.lstrip("/")
            target = p if os.path.exists(f"{P}/{p}") and not os.path.isdir(f"{P}/{p}") else p + ".html"
        if not os.path.exists(f"{P}/{target}"):
            bad.append(f"{f}: {href} -> missing {target}")
        elif frag and target.endswith(".html") and frag not in ids.get(target, set()):
            bad.append(f"{f}: {href} -> no #{frag} in {target}")
print(f"{n} internal links checked")
print("\n".join(bad) or "all resolve")
sys.exit(1 if bad else 0)
