"""Build the static site: inline results/summary.json into site/template.html -> public/index.html.

Usage (from repo root): python eval/build_site.py
Deploy (Cloudflare Workers static assets): npx wrangler deploy
"""
import json, os

data = json.load(open("results/summary.json"))
# drop "examples" from the ASR block; the page only needs scores there
for lang in data["asr"].values():
    for m in lang.values():
        if isinstance(m, dict):
            m.pop("examples", None)
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
tpl = open("site/template.html", encoding="utf-8").read()
assert "/*__DATA__*/" in tpl

page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + tpl.replace("/*__DATA__*/", blob).replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
        + "\n</body>\n</html>\n")
os.makedirs("public", exist_ok=True)
open("public/index.html", "w", encoding="utf-8").write(page)
# the artifact preview takes the bare template body (its host adds the skeleton)
open("site/artifact.html", "w", encoding="utf-8").write(tpl.replace("/*__DATA__*/", blob))
print(f"public/index.html  {len(page)/1024:.0f} KB")
