"""Naija Eval — ASR pass. Scores N-ATLaS ASR models vs stock Whisper-small on FLEURS test clips.

Usage (from repo root): python eval/eval_asr.py [N_PER_LANG]
"""
import io, json, re, sys, time, unicodedata
import numpy as np, pandas as pd, soundfile as sf, librosa, torch, jiwer
from transformers import WhisperProcessor, WhisperForConditionalGeneration

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
DEV = "mps" if torch.backends.mps.is_available() else "cpu"

LANGS = {  # fleurs code -> (N-ATLaS model dir, whisper language name or None if unsupported)
    "ha_ng": ("Hausa-ASR", "hausa"),
    "ig_ng": ("Igbo-ASR", None),  # stock Whisper has no Igbo
    "yo_ng": ("Yoruba-ASR", "yoruba"),
}


def norm(s, strip_marks=False):
    s = unicodedata.normalize("NFC", s.lower())
    if strip_marks:
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^\w\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_clips(code):
    df = pd.read_parquet(f"data/parquet-data/{code}/test-00000-of-00001.parquet")
    df = df.drop_duplicates("id").head(N)
    clips = []
    for _, r in df.iterrows():
        a = r["audio"]
        wav, sr = sf.read(io.BytesIO(a["bytes"])) if a.get("bytes") else sf.read(a["path"])
        if wav.ndim > 1:
            wav = wav.mean(1)
        if sr != 16000:
            wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
        clips.append((wav.astype(np.float32), r["raw_transcription"]))
    return clips


def run(model_dir, clips, lang):
    proc = WhisperProcessor.from_pretrained(model_dir)
    model = WhisperForConditionalGeneration.from_pretrained(model_dir).to(DEV).eval()
    gen = {"task": "transcribe", "max_new_tokens": 200}
    if lang:
        gen["language"] = lang
    hyps, audio_s, t0 = [], 0.0, time.time()
    for i in range(0, len(clips), 8):
        batch = clips[i : i + 8]
        feats = proc([w for w, _ in batch], sampling_rate=16000, return_tensors="pt").input_features.to(DEV)
        with torch.no_grad():
            ids = model.generate(feats, **gen)
        hyps += proc.batch_decode(ids, skip_special_tokens=True)
        audio_s += sum(len(w) / 16000 for w, _ in batch)
    secs = time.time() - t0
    refs = [r for _, r in clips]
    out = {"rtf": round(secs / audio_s, 3), "examples": list(zip(refs[:3], hyps[:3]))}
    for tag, strip in (("", False), ("_nomarks", True)):
        R = [norm(r, strip) for r in refs]
        H = [norm(h, strip) or "∅" for h in hyps]
        out["wer" + tag] = round(jiwer.wer(R, H) * 100, 1)
        out["cer" + tag] = round(jiwer.cer(R, H) * 100, 1)
    del model
    return out


results = {}
for code, (natlas_dir, wlang) in LANGS.items():
    clips = load_clips(code)
    print(f"\n== {code}: {len(clips)} clips", flush=True)
    results[code] = {"n": len(clips)}
    results[code]["n-atlas"] = r = run(f"models/{natlas_dir}", clips, None)
    print("  N-ATLaS ", {k: v for k, v in r.items() if k != "examples"}, flush=True)
    if wlang:
        results[code]["whisper-small"] = r = run("models/whisper-small", clips, wlang)
        print("  Whisper ", {k: v for k, v in r.items() if k != "examples"}, flush=True)

json.dump(results, open("results/raw/asr.json", "w"), ensure_ascii=False, indent=1)
print("\nsaved results/raw/asr.json")
