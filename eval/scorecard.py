"""Naija Eval's results as a model scorecard (schema model-scorecard/1).

One small JSON file that tools can read to put the models that did best on a language
first. Lodestone (@extrafemi-ai/lodestone) is the first reader; the format is documented
at https://github.com/obasaolorunfemi-ai/lodestone/blob/main/docs/scorecards.md and
anyone can use it. A scorecard says what was measured, how, on how many items and on which
day; it never says which model to use.

Usage (from repo root): python eval/scorecard.py [out.json]     (default: public/data/scorecard.json)
build_site.py calls build() too, so the live site always serves the current one.
"""
import datetime, json, os, sys

SCHEMA = "model-scorecard/1"


def _day(path):
    """The day the results file was written, which is when the run finished."""
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def _local(name):
    """The same name for a local model in every task: the speech results call it n-atlas, the translation ones natlas."""
    return "local/" + name.replace("-", "")


def _lang(pair):
    """en->yo and yo->en are both about Yoruba."""
    src, tgt = pair.split("->")
    return tgt if src == "en" else src


def build(summary, raw_dir="results/raw", now=None):
    """summary: the parsed results/summary.json. Returns a model-scorecard/1 dict.

    A hosted model is named by its OpenRouter id (read from its raw results file), which is
    what Lodestone routes by. A model run locally has no OpenRouter id and is named
    local/<label>; readers ignore those, but they stay in the file so the numbers are public."""
    scores = []

    def add(model, task, metric, value, higher, n, day, language, slice_=None):
        row = {"model": model, "task": task, "metric": metric, "value": value, "higherIsBetter": higher, "n": n, "measuredAt": day, "language": language}
        if slice_:
            row["slice"] = slice_
        scores.append(row)

    for m in summary["mt"]:
        raw_path = f"{raw_dir}/mt_{m['label']}.json"
        raw = json.load(open(raw_path)) if os.path.exists(raw_path) else {}
        model = raw.get("openrouter_id") or _local(m["label"])
        day = _day(raw_path) if os.path.exists(raw_path) else (now or datetime.date.today()).isoformat()[:10]
        for metric, per_pair in (("chrf++", m["scores"]), ("chrf++_nomarks", m["scores_nomarks"])):
            by_lang = {}
            for pair, value in per_pair.items():
                add(model, "translate", metric, value, True, m["n"], day, _lang(pair), pair)
                by_lang.setdefault(_lang(pair), []).append(value)
            for lang, values in by_lang.items():  # both directions together: what "good at Yoruba" usually means
                add(model, "translate", metric, round(sum(values) / len(values), 1), True, m["n"], day, lang, "avg")

    asr_path = f"{raw_dir}/asr.json"
    asr_day = _day(asr_path) if os.path.exists(asr_path) else (now or datetime.date.today()).isoformat()[:10]
    for lang_key, entry in summary["asr"].items():
        for name, r in entry.items():
            if not isinstance(r, dict):
                continue  # "n"
            for metric in ("wer", "wer_nomarks", "cer", "cer_nomarks"):
                if metric in r:
                    add(_local(name), "transcribe", metric, r[metric], False, entry["n"], asr_day, lang_key[:2])

    stamp = (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"schema": SCHEMA, "source": "naija-eval", "generatedAt": stamp, "scores": scores}


def problems(card):
    """What is wrong with a scorecard, in plain words. Empty if it is valid. The same checks
    as Lodestone's parseScorecard, so a file this passes will be accepted there."""
    out = []
    if card.get("schema") != SCHEMA:
        out.append(f"schema is {card.get('schema')!r}, expected {SCHEMA}")
    if not card.get("source"):
        out.append("source is missing")
    if not isinstance(card.get("scores"), list):
        return out + ["scores is not a list"]
    for i, s in enumerate(card["scores"]):
        for f in ("model", "task", "metric"):
            if not isinstance(s.get(f), str) or not s[f]:
                out.append(f"scores[{i}].{f} is missing")
        if isinstance(s.get("value"), bool) or not isinstance(s.get("value"), (int, float)):
            out.append(f"scores[{i}].value is not a number")
        if not isinstance(s.get("higherIsBetter"), bool):
            out.append(f"scores[{i}].higherIsBetter is not true or false")
        if isinstance(s.get("n"), bool) or not isinstance(s.get("n"), int) or s["n"] < 0:
            out.append(f"scores[{i}].n is not a count")
        if not isinstance(s.get("measuredAt"), str) or len(s["measuredAt"]) < 10:
            out.append(f"scores[{i}].measuredAt is not a date")
    return out


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "public/data/scorecard.json"
    card = build(json.load(open("results/summary.json")))
    bad = problems(card)
    if bad:
        sys.exit("not writing an invalid scorecard:\n  " + "\n  ".join(bad))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(card, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {out}: {len(card['scores'])} scores")
