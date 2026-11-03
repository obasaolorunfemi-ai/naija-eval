# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static site: `eval/build_site.py` builds `public/` (report + Privacy, Terms, Legal, 404) from `site/` and `results/summary.json`, served as Cloudflare Workers static assets (`wrangler.jsonc`). No cookies, no analytics, no third-party requests (self-hosted fonts, strict CSP in `site/_headers`). Live at https://naija-eval.extrafemi.com.

## What it is

Naija Eval is an Extrafemi Labs independent, reproducible scorecard for N-ATLaS, Nigeria's multilingual model (Llama 3.1 8B fine-tune + Whisper Small ASR models), on Hausa, Igbo and Yoruba speech-to-text and translation. It compares N-ATLaS with its Llama 3.1 base, stock Whisper Small, and four hosted models.

## Readers

All of these, equally:

- Nigerian builders deciding whether to self-host N-ATLaS or pay for a hosted model.
- Policy makers and press (NCAIR, NITDA, journalists) wanting an independent read.
- AI researchers checking method, sample sizes and reproducibility.
- Curious members of the public asking whether "our own AI" is any good.

## Commitments

- Every sentence, number, finding and caveat on the page is fixed copy; redesigns restyle and restructure, never rewrite or add claims.
- Numbers come only from `results/summary.json`.
- Licence attribution in the footer stays (N-ATLaS © Awarri Technologies and the Federal Government of Nigeria; FLEURS © Google (CC BY 4.0), FLORES © Meta and OLDI (CC BY-SA 4.0)). No model weights redistributed.
- Hausa, Igbo and Yoruba text must render with correct letters and tone marks (ɓ ɗ ƙ ẹ ọ ṣ ị ụ ṅ + combining accents) in one face, never a mid-word fallback.
- Visual family: Extrafemi Dashboards (dashboards.extrafemi.com) data-story system, with the SANU Report (reports.sanucoin.com) cover-then-report structure as the sample. No monospace fonts anywhere.
