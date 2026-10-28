# Naija Eval

An independent, reproducible scorecard for **N-ATLaS** — Nigeria's government-backed
multilingual model (NCAIR / NITDA, powered by Awarri) — against its base model and
hosted frontier models, on Hausa, Igbo and Yoruba. An Extrafemi Labs build.

The N-ATLaS model card publishes only self-reported human ratings. This repo publishes
numbers anyone can re-run.

## Results (first pass, 8 Oct 2026)

**Speech-to-text** — word error rate on 100 FLEURS test clips per language (lower is better):

| | N-ATLaS ASR | without tone marks | stock Whisper Small |
|---|---|---|---|
| Hausa | 38.5% | 38.5% | 92.1% |
| Igbo | 45.4% | 39.4% | — (no Igbo) |
| Yoruba | 64.7% | 33.5% | 113.8% |

**Translation** — chrF++ on 100 FLORES sentences per direction (higher is better):

| Model | en→ha | ha→en | en→ig | ig→en | en→yo | yo→en | Avg |
|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 | 51.7 | 67.2 | 40.7 | 60.4 | 32.3 | 57.1 | 51.6 |
| Gemini 3.8 Flash | 51.0 | 63.8 | 43.9 | 62.6 | 29.7 | 53.7 | 50.8 |
| GPT-6.1 Sol | 51.1 | 62.2 | 42.8 | 62.0 | 31.3 | 53.9 | 50.6 |
| Claude Haiku 5.5 | 50.0 | 57.1 | 37.8 | 44.8 | 29.6 | 46.0 | 44.2 |
| **N-ATLaS** (4-bit, local) | 47.4 | 51.2 | 37.1 | 44.2 | 24.5 | 37.6 | **40.3** |
| Llama 3.1 8B Instruct (4-bit, local) | 22.7 | 40.1 | 17.0 | 33.7 | 7.6 | 28.3 | 24.9 |

Full outputs, including example translations, are in `results/raw/`; `results/summary.json`
is what the site reads.

### Findings
- N-ATLaS's Nigerian fine-tune is real: +15.4 chrF++ over its base on average (en→yo 7.6 → 24.5).
- It writes Hausa close to frontier level (47.4 vs 51.7) but lags badly translating *into English*.
- Every model struggles with Yoruba tone marks; stripping marks lifts en→yo scores by ~10 points across the board.
- N-ATLaS is built on **Llama 3.1** 8B (rope type `llama3`, 128k positions), not Llama 3 as its card states.

### Caveats
- 100 items per language/direction — a first pass, not a leaderboard.
- Local models were quantized to 4-bit (MLX) to fit 16 GB; full precision may score slightly higher.
- FLEURS/FLORES are public: any model, N-ATLaS included, may have seen them in training.
- FLEURS is read speech of Wikipedia sentences — cleaner audio, harder vocabulary than real voice notes.

## For tools that choose between models

`python eval/scorecard.py` (and the site build) writes `public/data/scorecard.json`: these results as a
[model scorecard](https://github.com/obasaolorunfemi-ai/lodestone/blob/main/docs/scorecards.md), a small shared format
that [Lodestone](https://github.com/obasaolorunfemi-ai/lodestone) can read to try the best-measured model first for a language.
In the other direction, Lodestone can list the models a tool actually calls, and `python eval/candidates.py <list>` says which
of them are not measured yet and prints the commands to measure them. Tests: `python -m unittest discover -s eval -p 'test_*.py'`.

## Reproduce

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
hf auth login                      # read token; accept the NCAIR1 model terms first
python eval/fetch.py all           # ~22 GB: ASR models, FLEURS, N-ATLaS (16 GB), Llama 3.1 4-bit
mlx_lm.convert --hf-path models/N-ATLaS --mlx-path models/natlas-4bit -q --q-bits 4

python eval/eval_asr.py 100
python eval/eval_mt.py models/natlas-4bit natlas 100
python eval/eval_mt.py models/llama31-4bit llama31 100
# hosted models: put OPENROUTER_API_KEY=... in ~/.config/naija-eval/.env
python eval/eval_mt_api.py anthropic/claude-sonnet-5.5 sonnet55 100
python eval/summarize.py
```

Hosted run cost: $1.59 for all four models (600 translations each). Apple Silicon is
assumed for the local translation runs (MLX); the ASR eval runs anywhere PyTorch does.

## Licences and credits
- N-ATLaS models: © Awarri Technologies and the Federal Government of Nigeria, under the
  N-ATLaS licence. This repo does not redistribute weights.
- FLEURS (Google) and FLORES (Meta / OLDI): CC BY-SA 4.0.
- Evaluation code: © Extrafemi Labs.

## Site

`python eval/build_site.py` builds `public/` from `site/`: the report (`site/template.html` + `results/summary.json`), the About and method, Developers, Privacy, Terms, Legal and 404 pages (`site/pages/`), the downloadable `data/summary.json`, shared head, bar and footer (`site/partials/`), and assets. Fonts are self-hosted (`tools/fetch_fonts.py`), and `site/_headers` sets a strict CSP, so the page makes no third-party requests and sets no cookies. Check links with `python tools/check_links.py`. Deploy with `npx wrangler deploy`.
