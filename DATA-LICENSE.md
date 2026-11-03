# Data licences

Naija Eval's results are published under two Creative Commons licences, because some of the files embed other people's text. Which licence applies to a file depends on what is inside it.

## CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

| File | What it is |
|---|---|
| `public/data/scorecard.json` | The scores as a `model-scorecard/1`: model, task, metric, value, `n`, date. Numbers only. |
| `results/raw/asr.json` | Word error rates, with short example transcripts from FLEURS (Google, CC BY 4.0) and each model's transcription of them. |

You may share and adapt these for any purpose, including commercial, if you give credit, link to the licence and say whether you changed anything. Credit: **"Naija Eval, Extrafemi Labs, https://naija-eval.extrafemi.com"**. For `asr.json`, also credit FLEURS (Google).

## CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/

| File | Why |
|---|---|
| `results/raw/mt_*.json` | Each holds example sentences from FLORES (Meta and OLDI, CC BY-SA 4.0) and each model's translation of them. |
| `results/summary.json` and `public/data/summary.json` | The same examples, collected with the scores. |

The FLORES sentences and the model translations of them are CC BY-SA 4.0. If you reuse or adapt them, credit FLORES and Naija Eval, and share what you make under CC BY-SA 4.0 (or a licence it names as compatible). The numbers in these files are also in `public/data/scorecard.json` under CC BY 4.0, which is the file to use if you only want the scores.

## Not covered here

- **Code** (`eval/`, `tools/`, the site's build and templates): Apache-2.0, see `LICENSE`.
- **The written text of the report and its pages** is covered by the site's [Terms of use](https://naija-eval.extrafemi.com/terms/).
- **Test data and models that this repository does not contain** keep their own licences: see `NOTICE`. Running the evaluation downloads them from their owners and means accepting those licences, including the N-ATLaS licence.
- **Hosted models' outputs** appear only as test results, under those providers' terms.
