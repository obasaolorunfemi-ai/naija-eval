"""Fold results/raw/*.json into results/summary.json, the one file the site reads.

Usage (from repo root): python eval/summarize.py
"""
import glob, json, os

MODELS = {  # label -> display name, how it ran
    "sonnet55": ("Claude Sonnet 5.5", "hosted"),
    "gemini38flash": ("Gemini 3.8 Flash", "hosted"),
    "gpt61sol": ("GPT-6.1 Sol", "hosted"),
    "haiku55": ("Claude Haiku 5.5", "hosted"),
    "natlas": ("N-ATLaS", "local · 4-bit"),
    "llama31": ("Llama 3.1 8B Instruct", "local · 4-bit"),
}
PAIRS = ["en->ha", "ha->en", "en->ig", "ig->en", "en->yo", "yo->en"]

mt = []
for label, (name, run) in MODELS.items():
    p = f"results/raw/mt_{label}.json"
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    scores = {k: d["pairs"][k]["chrf++"] for k in PAIRS}
    mt.append({
        "label": label, "name": name, "run": run, "n": d["n"],
        "scores": scores,
        "scores_nomarks": {k: d["pairs"][k]["chrf++_nomarks"] for k in PAIRS},
        "avg": round(sum(scores.values()) / len(scores), 1),
        "cost_usd": d.get("cost_usd"),
        "examples": {k: d["pairs"][k]["examples"] for k in PAIRS},
    })
mt.sort(key=lambda m: -m["avg"])

a = json.load(open("results/raw/asr.json"))
asr = {lang: {"n": v["n"], **{m: {k: x for k, x in r.items()} for m, r in v.items() if m != "n"}}
       for lang, v in a.items()}

json.dump({"mt": mt, "asr": asr, "pairs": PAIRS}, open("results/summary.json", "w"), ensure_ascii=False, indent=1)
print("wrote results/summary.json:", ", ".join(f"{m['name']} {m['avg']}" for m in mt))
