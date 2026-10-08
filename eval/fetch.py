"""Download everything the evals need into models/ and data/ (both git-ignored).

Usage (from repo root): python eval/fetch.py [asr|mt|all]

The NCAIR1 repos are gated: accept the terms on each model page on Hugging Face,
then run `hf auth login` with a read token before fetching.
"""
import csv, json, sys
from huggingface_hub import snapshot_download, hf_hub_download

what = sys.argv[1] if len(sys.argv) > 1 else "all"
FLEURS = ["ha_ng", "ig_ng", "yo_ng"]

if what in ("asr", "all"):
    for m in ["Hausa-ASR", "Igbo-ASR", "Yoruba-ASR"]:
        # the repos also ship ~1.9 GB of leftover training state; skip it
        snapshot_download(f"NCAIR1/{m}", local_dir=f"models/{m}",
                          ignore_patterns=["optimizer.pt", "rng_state*", "scheduler.pt", "training_args.bin"])
    snapshot_download("openai/whisper-small", local_dir="models/whisper-small",
                      allow_patterns=["*.json", "*.txt", "model.safetensors"])
    for l in FLEURS:
        hf_hub_download("google/fleurs", f"parquet-data/{l}/test-00000-of-00001.parquet",
                        repo_type="dataset", local_dir="data")

if what in ("mt", "all"):
    # FLEURS test sentences are FLORES sentences; its per-language TSVs align by id,
    # which gives a parallel en/ha/ig/yo set without the gated FLORES+ repo.
    csv.field_size_limit(10**9)
    T = {}
    for l in ["en_us"] + FLEURS:
        p = hf_hub_download("google/fleurs", f"data/{l}/test.tsv", repo_type="dataset", local_dir="data")
        d = {}
        for row in csv.reader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            d.setdefault(row[0], row[2])
        T[l] = d
    common = sorted(set.intersection(*(set(d) for d in T.values())), key=int)
    json.dump([{l: T[l][i] for l in T} | {"id": i} for i in common],
              open("data/parallel.json", "w"), ensure_ascii=False, indent=0)
    print(f"data/parallel.json: {len(common)} aligned sentences")
    snapshot_download("NCAIR1/N-ATLaS", local_dir="models/N-ATLaS")
    snapshot_download("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit", local_dir="models/llama31-4bit")
    print("now quantize N-ATLaS:  mlx_lm.convert --hf-path models/N-ATLaS --mlx-path models/natlas-4bit -q --q-bits 4")
