"""Naija Eval — translation pass for hosted models via OpenRouter. Same prompt/data/metric as eval_mt.py.

Usage (from repo root): python eval/eval_mt_api.py <openrouter_model_id> <label> [N]
Reads OPENROUTER_API_KEY from ~/.config/naija-eval/.env
"""
import json, os, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
import requests, sacrebleu

for line in open(os.path.expanduser("~/.config/naija-eval/.env")):
    k, _, v = line.strip().partition("=")
    os.environ.setdefault(k, v)
KEY = os.environ["OPENROUTER_API_KEY"]

model_id, label = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
NAMES = {"en_us": "English", "ha_ng": "Hausa", "ig_ng": "Igbo", "yo_ng": "Yoruba"}
rows = json.load(open("data/parallel.json"))[:N]
cost = 0.0


def translate(args):
    global cost
    text, src, tgt = args
    body = {
        "model": model_id,
        "temperature": 0,
        "max_tokens": 400,
        "reasoning": {"effort": "low", "exclude": True},
        "usage": {"include": True},
        "messages": [
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": f"Translate the following {NAMES[src]} text into {NAMES[tgt]}. "
                                        f"Output only the {NAMES[tgt]} translation, nothing else.\n\n{text}"},
        ],
    }
    for attempt in range(5):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120,
                              headers={"Authorization": f"Bearer {KEY}", "X-Title": "Naija Eval"})
            d = r.json()
            if "choices" in d:
                cost += (d.get("usage") or {}).get("cost", 0) or 0
                return (d["choices"][0]["message"]["content"] or "").strip().split("\n")[0].strip()
            err = d.get("error", d)
        except Exception as e:
            err = e
        time.sleep(2 ** attempt)
    print("  FAILED:", str(err)[:200], flush=True)
    return ""


def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


results, t0 = {"model": label, "openrouter_id": model_id, "n": len(rows), "pairs": {}}, time.time()
with ThreadPoolExecutor(8) as pool:
    for lang in ("ha_ng", "ig_ng", "yo_ng"):
        for src, tgt in (("en_us", lang), (lang, "en_us")):
            hyps = list(pool.map(translate, [(r[src], src, tgt) for r in rows]))
            refs = [r[tgt] for r in rows]
            res = {"chrf++": round(sacrebleu.corpus_chrf(hyps, [refs], word_order=2).score, 1),
                   "chrf++_nomarks": round(sacrebleu.corpus_chrf([strip_marks(h) for h in hyps],
                                                                 [[strip_marks(r) for r in refs]], word_order=2).score, 1),
                   "empty": sum(1 for h in hyps if not h),
                   "examples": [{"src": r[src], "ref": r[tgt], "hyp": h} for r, h in list(zip(rows, hyps))[:3]]}
            results["pairs"][f"{src[:2]}->{tgt[:2]}"] = res
            print(f"{label:14s} {src[:2]}->{tgt[:2]}  chrF++ {res['chrf++']:5.1f}  (no marks {res['chrf++_nomarks']:5.1f})"
                  f"  empty={res['empty']}  [{time.time()-t0:.0f}s, ${cost:.3f}]", flush=True)

results["cost_usd"] = round(cost, 4)
json.dump(results, open(f"results/raw/mt_{label}.json", "w"), ensure_ascii=False, indent=1)
print("saved", f"results/raw/mt_{label}.json", f"cost ${cost:.3f}")
