"""Build the static site into public/.

- index.html  = site/partials + site/template.html, with results/summary.json inlined
- legal pages = site/partials + site/pages/*.html (front matter: title, description)
- assets      = style.css, app.js, site.js, theme.js, fonts/, favicon, robots, _headers
- sitemap.xml, and site/artifact.html (a self-contained preview for a Claude artifact)

Usage (from repo root): python eval/build_site.py
Deploy (Cloudflare Workers static assets): npx wrangler deploy
"""
import hashlib, json, os, re, shutil, sys

S, P = "site", "public"
read = lambda p: open(p, encoding="utf-8").read()
write = lambda p, s: open(p, "w", encoding="utf-8").write(s)

data = json.load(open("results/summary.json"))
# drop "examples" from the ASR block; the page only needs scores there
for lang in data["asr"].values():
    for m in lang.values():
        if isinstance(m, dict):
            m.pop("examples", None)
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

if os.path.isdir(P):
    shutil.rmtree(P)
os.makedirs(P)
shutil.copytree(f"{S}/fonts", f"{P}/fonts")
for f in ("style.css", "app.js", "site.js", "theme.js", "favicon.svg", "robots.txt", "_headers"):
    shutil.copy(f"{S}/{f}", f"{P}/{f}")

# one cache-busting version for every asset
h = hashlib.sha256()
for f in sorted(os.listdir(P)) + sorted(os.listdir(f"{P}/fonts")):
    p = f"{P}/{f}" if os.path.isfile(f"{P}/{f}") else f"{P}/fonts/{f}"
    if os.path.isfile(p):
        h.update(open(p, "rb").read())
v = h.hexdigest()[:10]

HEAD, BAR, FOOT = read(f"{S}/partials/head.html"), read(f"{S}/partials/sitebar.html"), read(f"{S}/partials/footer.html")
# The same links on every page. On the report they scroll to the section; from any other page they go to the report's section.
SECTIONS = [("mt", "Translation"), ("asr", "Speech to text"), ("ex", "Outputs"), ("find", "Findings")]
PAGE_LINKS = [("/about", "About and method"), ("/developers", "Developers")]
REPORT_NAV = [(f"#{i}", l) for i, l in SECTIONS] + PAGE_LINKS
DOC_NAV = [("/", "The report")] + [(f"/#{i}", l) for i, l in SECTIONS] + PAGE_LINKS


def page(path, title, desc, body, nav, nav_label, extra_head=""):
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == path else ""}>{label}</a>' for href, label in nav)
    head = (HEAD.replace("{{title}}", title).replace("{{description}}", desc)
            .replace("{{path}}", path).replace("{{v}}", v).replace("{{extra_head}}", extra_head))
    bar = BAR.replace("{{nav}}", links).replace("{{nav_label}}", nav_label)
    if "{{SITEBAR}}" in body:
        body = body.replace("{{SITEBAR}}", bar)
    else:
        body = bar + f'<main id="main" tabindex="-1">\n{body}</main>\n'
    return head + body + FOOT


# report
tpl = read(f"{S}/template.html")
data_tag = f'<script id="data" type="application/json">{blob}</script>'
index = page("/", "Naija Eval: N-ATLaS tested on Hausa, Igbo and Yoruba",
             "An independent, reproducible scorecard for N-ATLaS, Nigeria's multilingual model, on Hausa, Igbo and Yoruba.",
             tpl, REPORT_NAV, "Report sections",
             extra_head=f'<script src="/app.js?v={v}" defer></script>')
index = index.replace("</body>", data_tag + "\n</body>", 1)
write(f"{P}/index.html", index)

# the results file, for developers
os.makedirs(f"{P}/data")
write(f"{P}/data/summary.json", json.dumps(data, ensure_ascii=False, indent=1))

# the same results as a model scorecard (model-scorecard/1), for tools that route between models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorecard
card = scorecard.build(json.load(open("results/summary.json")))  # the unstripped file: summary.json above had its examples removed
bad = scorecard.problems(card)
if bad:
    raise SystemExit("scorecard is invalid:\n  " + "\n  ".join(bad))
write(f"{P}/data/scorecard.json", json.dumps(card, ensure_ascii=False, indent=1))
FILL = {"{{models}}": str(len(data["mt"])), "{{asr_langs}}": str(len(data["asr"])),
        "{{size}}": f'{os.path.getsize(f"{P}/data/summary.json") / 1024:.0f} KB'}

# other pages and 404
urls = ["/"]
for f in sorted(os.listdir(f"{S}/pages")):
    src = read(f"{S}/pages/{f}")
    meta = dict(re.findall(r"^(\w+): (.+)$", re.match(r"<!--(.*?)-->", src, re.S).group(1), re.M))
    body = src[src.index("-->") + 3:].lstrip("\n")
    for k, val in FILL.items():
        body = body.replace(k, val)
    name = f[:-5]
    path = "/" + name
    write(f"{P}/{f}", page(path, meta["title"], meta["description"], body, DOC_NAV, "Site"))
    if name != "404":
        urls.append(path)

write(f"{P}/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"  <url><loc>https://naija-eval.extrafemi.com{u}</loc></url>\n" for u in urls) + "</urlset>\n")

# the artifact preview takes one self-contained body (its host adds the skeleton; Google Fonts allowed there)
css = read(f"{S}/style.css")
artifact = (f'<title>Naija Eval</title>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap">\n'
            f"<style>\n{css}</style>\n<script>{read(f'{S}/theme.js')}</script>\n"
            + tpl.replace("{{SITEBAR}}", BAR.replace("{{nav}}", "".join(f'<a href="{h}">{l}</a>' for h, l in REPORT_NAV)).replace("{{nav_label}}", "Report sections"))
            + FOOT.replace("</body>\n</html>\n", "") + data_tag
            + f"\n<script>{read(f'{S}/site.js')}</script>\n<script>{read(f'{S}/app.js')}</script>\n")
write(f"{S}/artifact.html", artifact)

total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(P) for f in fs)
print(f"public/  {len(os.listdir(P))} entries, {total / 1024:.0f} KB  (v={v})")
