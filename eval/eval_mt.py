"""Naija Eval — translation pass. chrF++ on FLEURS/FLORES-aligned sentences, en <-> ha/ig/yo.

Usage (from repo root): python eval/eval_mt.py <model_dir> <label> [N]
"""
import json, sys, time, unicodedata
import sacrebleu
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

model_dir, label = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
NAMES = {"en_us": "English", "ha_ng": "Hausa", "ig_ng": "Igbo", "yo_ng": "Yoruba"}
rows = json.load(open("data/parallel.json"))[:N]

model, tok = load(model_dir)
greedy = make_sampler(temp=0.0)


def translate(text, src, tgt):
    msgs = [
        {"role": "system", "content": "You are a professional translator."},
        {"role": "user", "content": f"Translate the following {NAMES[src]} text into {NAMES[tgt]}. "
                                    f"Output only the {NAMES[tgt]} translation, nothing else.\n\n{text}"},
    ]
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True)
    out = generate(model, tok, prompt=prompt, max_tokens=256, sampler=greedy)
    return out.strip().split("\n")[0].strip()


def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


results, t0 = {"model": label, "n": len(rows), "pairs": {}}, time.time()
for lang in ("ha_ng", "ig_ng", "yo_ng"):
    for src, tgt in (("en_us", lang), (lang, "en_us")):
        hyps = [translate(r[src], src, tgt) for r in rows]
        refs = [r[tgt] for r in rows]
        chrf = sacrebleu.corpus_chrf(hyps, [refs], word_order=2).score
        res = {"chrf++": round(chrf, 1),
               "chrf++_nomarks": round(sacrebleu.corpus_chrf([strip_marks(h) for h in hyps],
                                                             [[strip_marks(r) for r in refs]], word_order=2).score, 1),
               "examples": [{"src": r[src], "ref": r[tgt], "hyp": h} for r, h in list(zip(rows, hyps))[:3]]}
        results["pairs"][f"{src[:2]}->{tgt[:2]}"] = res
        print(f"{label:10s} {src[:2]}->{tgt[:2]}  chrF++ {res['chrf++']:5.1f}  (no marks {res['chrf++_nomarks']:5.1f})"
              f"  [{time.time()-t0:.0f}s]", flush=True)

json.dump(results, open(f"results/raw/mt_{label}.json", "w"), ensure_ascii=False, indent=1)
print("saved", f"results/raw/mt_{label}.json")
