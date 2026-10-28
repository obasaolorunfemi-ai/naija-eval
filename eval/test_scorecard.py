"""Run from the repo root: python -m unittest discover -s eval -p 'test_*.py'"""
import json, os, sys, tempfile, unittest, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorecard, candidates

SUMMARY = {
    "mt": [
        {"label": "sonnet55", "name": "Claude Sonnet 5.5", "run": "hosted", "n": 100,
         "scores": {"en->yo": 30.0, "yo->en": 60.0}, "scores_nomarks": {"en->yo": 40.0, "yo->en": 60.0}},
        {"label": "natlas", "name": "N-ATLaS", "run": "local · 4-bit", "n": 100,
         "scores": {"en->yo": 20.0, "yo->en": 40.0}, "scores_nomarks": {"en->yo": 25.0, "yo->en": 40.0}},
    ],
    "asr": {"yo_ng": {"n": 50, "n-atlas": {"wer": 64.7, "cer": 24.6, "wer_nomarks": 33.5, "cer_nomarks": 10.2, "rtf": 0.03}}},
}
NOW = datetime.datetime(2026, 10, 28, 9, 0, tzinfo=datetime.timezone.utc)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        json.dump({"model": "sonnet55", "openrouter_id": "anthropic/claude-sonnet-5.5", "n": 100}, open(f"{self.dir.name}/mt_sonnet55.json", "w"))
        json.dump({"model": "natlas", "n": 100}, open(f"{self.dir.name}/mt_natlas.json", "w"))
        json.dump({}, open(f"{self.dir.name}/asr.json", "w"))
        self.card = scorecard.build(SUMMARY, raw_dir=self.dir.name, now=NOW)

    def find(self, **want):
        return [s for s in self.card["scores"] if all(s.get(k) == v for k, v in want.items())]


class BuildTests(Fixture):
    def test_is_a_valid_scorecard(self):
        self.assertEqual(self.card["schema"], "model-scorecard/1")
        self.assertEqual(self.card["generatedAt"], "2026-10-28T09:00:00Z")
        self.assertEqual(scorecard.problems(self.card), [])

    def test_hosted_models_are_named_by_openrouter_id_and_local_ones_are_marked(self):
        models = {s["model"] for s in self.card["scores"]}
        self.assertEqual(models, {"anthropic/claude-sonnet-5.5", "local/natlas"})

    def test_n_atlas_has_one_name_across_translation_and_speech(self):
        self.assertTrue(self.find(model="local/natlas", task="transcribe"))
        self.assertTrue(self.find(model="local/natlas", task="translate"))

    def test_each_direction_and_the_average_of_both_are_published(self):
        (a,) = self.find(model="anthropic/claude-sonnet-5.5", metric="chrf++", language="yo", slice="avg")
        self.assertEqual(a["value"], 45.0)
        self.assertEqual(a["n"], 100)
        self.assertEqual(self.find(model="anthropic/claude-sonnet-5.5", metric="chrf++", slice="yo->en")[0]["language"], "yo")
        self.assertEqual(self.find(model="anthropic/claude-sonnet-5.5", metric="chrf++", slice="en->yo")[0]["language"], "yo")

    def test_scores_without_tone_marks_are_kept_apart_from_scores_with_them(self):
        (a,) = self.find(model="anthropic/claude-sonnet-5.5", metric="chrf++_nomarks", slice="en->yo")
        self.assertEqual(a["value"], 40.0)

    def test_speech_errors_say_that_lower_is_better_and_translation_that_higher_is(self):
        self.assertFalse(self.find(task="transcribe", metric="wer")[0]["higherIsBetter"])
        self.assertTrue(self.find(task="translate", metric="chrf++")[0]["higherIsBetter"])

    def test_speech_scores_carry_the_language_and_item_count(self):
        (w,) = self.find(task="transcribe", metric="wer")
        self.assertEqual((w["language"], w["n"], w["value"]), ("yo", 50, 64.7))
        self.assertEqual(self.find(task="transcribe", metric="rtf"), [])  # speed of a local run is not a quality score

    def test_the_measured_day_is_when_the_results_file_was_written(self):
        day = datetime.date.fromtimestamp(os.path.getmtime(f"{self.dir.name}/mt_sonnet55.json")).isoformat()
        self.assertEqual(self.find(model="anthropic/claude-sonnet-5.5")[0]["measuredAt"], day)


class ProblemsTests(unittest.TestCase):
    def test_reports_each_thing_that_is_wrong(self):
        bad = {"schema": "nope", "source": "", "scores": [{"model": "a", "task": "t", "metric": "m", "value": "x", "higherIsBetter": "yes", "n": -1, "measuredAt": "soon"}]}
        found = "\n".join(scorecard.problems(bad))
        for needle in ("schema", "source", "value", "higherIsBetter", ".n ", "measuredAt"):
            self.assertIn(needle, found)

    def test_a_missing_list_of_scores_is_reported(self):
        self.assertIn("scores is not a list", scorecard.problems({"schema": scorecard.SCHEMA, "source": "x"}))


class CandidatesTests(Fixture):
    def cands(self, *ids):
        return {"schema": "model-candidates/1", "source": "lodestone", "models": [{"id": i, "provider": "openrouter", "roles": ["free:fast"]} for i in ids]}

    def test_lists_only_models_with_no_translation_score(self):
        todo = candidates.unmeasured(self.cands("anthropic/claude-sonnet-5.5", "google/gemma-4-31b-it:free"), self.card)
        self.assertEqual([c["id"] for c in todo], ["google/gemma-4-31b-it:free"])

    def test_a_free_variant_counts_as_its_measured_base_model(self):
        self.assertEqual(candidates.unmeasured(self.cands("anthropic/claude-sonnet-5.5:free"), self.card), [])

    def test_ignores_the_router_and_local_models_and_lists_each_model_once(self):
        todo = candidates.unmeasured(self.cands("openrouter/free", "local/x", "a/new:free", "a/new"), self.card)
        self.assertEqual([c["id"] for c in todo], ["a/new:free"])

    def test_a_model_measured_for_speech_only_is_still_unmeasured_for_translation(self):
        self.card["scores"].append({"model": "a/new", "task": "transcribe", "metric": "wer", "value": 1, "higherIsBetter": False, "n": 50, "measuredAt": "2026-10-08", "language": "ha"})
        self.assertEqual(len(candidates.unmeasured(self.cands("a/new"), self.card, "translate")), 1)
        self.assertEqual(len(candidates.unmeasured(self.cands("a/new"), self.card, "transcribe")), 0)

    def test_labels_are_short_and_file_safe(self):
        self.assertEqual(candidates.label("google/gemma-4-31b-it:free"), "gemma431bit")
        self.assertEqual(candidates.label("qwen/qwen3.7-flash"), "qwen37flash")


if __name__ == "__main__":
    unittest.main()
