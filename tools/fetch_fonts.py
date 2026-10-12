"""Self-host the page fonts (no requests to Google from visitors' browsers).

Downloads Cardo and Lora woff2 files from Google Fonts into site/fonts/ and writes
site/fonts/fonts.css with local URLs. Keeps only latin, latin-ext and vietnamese
(vietnamese holds ẹ ọ ị ụ). Run once; the files are committed. Both fonts: SIL OFL 1.1.
Usage (repo root): python tools/fetch_fonts.py
"""
import re, subprocess

URL = ("https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400"
       "&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
KEEP = {"latin", "latin-ext", "vietnamese"}

get = lambda u: subprocess.run(["curl", "-sfL", "-A", UA, u], check=True, capture_output=True).stdout
css = get(URL).decode()
out, n = [], 0
for subset, block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S):
    if subset not in KEEP:
        continue
    fam = re.search(r"font-family: '([^']+)'", block).group(1)
    style = re.search(r"font-style: (\w+)", block).group(1)
    weight = re.search(r"font-weight: (\d+)", block).group(1)
    src = re.search(r"url\((https://[^)]+)\)", block).group(1)
    name = f"{fam.lower()}-{weight}{'i' if style == 'italic' else ''}-{subset}.woff2"
    open(f"site/fonts/{name}", "wb").write(get(src)); n += 1
    out.append(f"/* {subset} */\n" + block.replace(src, f"/fonts/{name}"))
# Cardo has the glyphs for ẹ ọ ị ụ (U+1EA0-1EF9) and combining marks, but Google ships no
# vietnamese subset for it; ask for exactly those characters with the text= API.
from urllib.parse import quote
chars = "".join(map(chr, range(0x1EA0, 0x1EFA))) + "".join(map(chr, range(0x0300, 0x0370)))
for axis, weight, style in (("0,400", "400", "normal"), ("0,700", "700", "normal"), ("1,400", "400", "italic")):
    css2 = get(f"https://fonts.googleapis.com/css2?family=Cardo:ital,wght@{axis}&text={quote(chars)}").decode()
    src = re.search(r"url\((https://[^)]+)\)", css2).group(1)
    name = f"cardo-{weight}{'i' if style == 'italic' else ''}-dots.woff2"
    open(f"site/fonts/{name}", "wb").write(get(src)); n += 1
    out.append(f"/* dot-below vowels and combining marks */\n@font-face {{\n  font-family: 'Cardo';\n  font-style: {style};\n  font-weight: {weight};\n  font-display: swap;\n  src: url({name}) format('woff2');\n  unicode-range: U+0300-036F, U+1EA0-1EF9;\n}}")
open("site/fonts/fonts.css", "w").write("/* Cardo (David Perry) and Lora (Cyreal), SIL Open Font License 1.1. Self-hosted. */\n" + "\n".join(out) + "\n")
print(n, "files")
