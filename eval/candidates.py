"""Which of the models a tool actually uses has Naija Eval not measured yet?

Lodestone (@extrafemi-ai/lodestone) can list the models it may call (ai.candidates(), schema
model-candidates/1). This reads that list, compares it with Naija Eval's scorecard, and prints
the exact commands to measure what is missing, so the benchmark covers what is in use and not a guess.

Usage (from repo root):
  python eval/candidates.py <candidates.json | https://...> [scorecard.json | https://...] [--task translate]

With no scorecard given, the current results/summary.json is used.
"""
import json, re, sys, urllib.request

ROUTER = "openrouter/free"  # a router, not a model: there is nothing to measure


def load(src):
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src, timeout=15) as r:
            return json.load(r)
    return json.load(open(src))


def base(model_id):
    """anthropic/claude-x:free is the same model as anthropic/claude-x."""
    return model_id.split(":")[0].lower()


def label(model_id):
    """A short file-safe name for results/raw/mt_<label>.json."""
    return re.sub(r"[^a-z0-9]", "", base(model_id).split("/")[-1])


def unmeasured(candidates, scorecard, task="translate"):
    """The routable candidates with no score for `task`, each with the roles it plays. One entry per model."""
    measured = {base(s["model"]) for s in scorecard["scores"] if s["task"] == task}
    seen, out = set(), []
    for c in candidates["models"]:
        b = base(c["id"])
        if c["id"] == ROUTER or c["id"].startswith("local/") or b in measured or b in seen:
            continue
        seen.add(b)
        out.append(c)
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    task = argv[argv.index("--task") + 1] if "--task" in argv else "translate"
    args = [a for a in args if a != task]
    if not args:
        sys.exit(__doc__)
    candidates = load(args[0])
    if candidates.get("schema") != "model-candidates/1":
        sys.exit(f"{args[0]} is not a model-candidates/1 file (schema: {candidates.get('schema')!r})")
    if len(args) > 1:
        card = load(args[1])
    else:
        sys.path.insert(0, "eval")
        import scorecard
        card = scorecard.build(json.load(open("results/summary.json")))

    todo = unmeasured(candidates, card, task)
    total = len({base(c["id"]) for c in candidates["models"] if c["id"] != ROUTER})
    print(f"{total - len(todo)} of {total} candidate models already have a '{task}' score.")
    if not todo:
        return
    print(f"\nNot measured yet ({len(todo)}):")
    for c in todo:
        print(f"  {c['id']:<48} used for: {', '.join(c['roles'])}")
    print("\nTo measure them (each takes a few minutes; hosted models cost a few cents, free ones nothing):")
    for c in todo:
        print(f"  python eval/eval_mt_api.py {c['id']} {label(c['id'])} 100")
    print("\nThen add each label to MODELS in eval/summarize.py, and run:")
    print("  python eval/summarize.py && python eval/build_site.py")


if __name__ == "__main__":
    main(sys.argv[1:])
