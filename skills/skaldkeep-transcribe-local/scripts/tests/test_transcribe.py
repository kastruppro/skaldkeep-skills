import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jobs
import transcribe

ID = "12345678-1234-4234-8234-123456789abc"
CAMPAIGN = {"speakers_expected": 5, "speaker_names": ["DM", "Brannoc", "Ysolde", "Tamsin", "Oskar"],
            "speaker_aliases": {"Riley": "Brannoc"}, "prompt": "Legacy instructions.",
            "context_prompt": "A fantasy game.", "custom_spelling": [{"from": ["Wrong"], "to": "Correct"}],
            "keyterms_prompt": ["Correct", "A Fantasy Place"]}


def response(payload, status=200):
    result = Mock(status_code=status, headers={})
    result.json.return_value = payload
    return result


class ConfigurationTests(unittest.TestCase):
    def test_absent_alias_excludes_participant_and_keeps_config_intact(self):
        cfg = transcribe.session_campaign(CAMPAIGN, ["RILEY", "Brannoc"])
        self.assertEqual(cfg["speakers_expected"], 4)
        self.assertNotIn("Brannoc", cfg["speaker_names"])
        self.assertIn("Brannoc", CAMPAIGN["speaker_names"])

    def test_unknown_absence_fails_instead_of_subtracting_random_speaker(self):
        with self.assertRaises(ValueError):
            transcribe.session_campaign(CAMPAIGN, ["Typo"])

    def test_updated_has_no_guessed_names_or_destructive_spelling_default(self):
        cfg = transcribe.build_config(CAMPAIGN)
        self.assertNotIn("speech_understanding", cfg)
        self.assertNotIn("custom_spelling", cfg)
        self.assertEqual(cfg["keyterms_prompt"], ["Correct", "A Fantasy Place"])
        self.assertEqual(cfg["temperature"], 0)
        self.assertNotIn("include_speaker_confidence", str(cfg))

    def test_legacy_reproduces_existing_recipe(self):
        cfg = transcribe.build_config(CAMPAIGN, "legacy")
        self.assertEqual(cfg["prompt"], "Legacy instructions.")
        self.assertEqual(cfg["custom_spelling"], CAMPAIGN["custom_spelling"])
        self.assertIn("known_values", cfg["speech_understanding"]["request"]["speaker_identification"])
        self.assertEqual(cfg["speech_models"], ["universal-3-5-pro"])

    def test_mixed_language_uses_native_detection(self):
        cfg = transcribe.build_config(CAMPAIGN, language="auto")
        self.assertTrue(cfg["language_detection"])
        self.assertNotIn("language_code", cfg)
        self.assertNotIn("language_detection_options", cfg)

    def test_updated_identification_only_uses_present_participants(self):
        cfg = transcribe.session_campaign(CAMPAIGN, ["Brannoc"])
        payload = transcribe.build_config(cfg, identify=True)
        names = payload["speech_understanding"]["request"]["speaker_identification"]["speakers"]
        self.assertEqual(len(names), 4)
        self.assertNotIn({"name": "Brannoc"}, names)

    def test_configuration_changes_have_distinct_cache_entries(self):
        old = transcribe.build_config(CAMPAIGN, "legacy")
        new = transcribe.build_config(CAMPAIGN, "updated")
        self.assertNotEqual(jobs.cache_key("audio", old), jobs.cache_key("audio", new))
        fewer = transcribe.build_config(transcribe.session_campaign(CAMPAIGN, ["Brannoc"]))
        self.assertNotEqual(jobs.cache_key("audio", new), jobs.cache_key("audio", fewer))
        self.assertEqual(jobs.cache_key("audio", new), jobs.cache_key("audio", dict(reversed(list(new.items())))))

    def test_nan_and_invalid_keyterms_rejected(self):
        with self.assertRaises(ValueError):
            transcribe.build_config(CAMPAIGN, temperature=float("nan"))
        with self.assertRaises(ValueError):
            transcribe.build_config({**CAMPAIGN, "keyterms_prompt": ["one two three four five six seven"]})


class ProfileLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_profile_file_path_is_accepted(self):
        profile = self.root / "my-table.yaml"
        profile.write_text("speakers_expected: 2\nspeaker_names: [GM, Player1]\n")
        self.assertEqual(transcribe.load_campaign(str(profile))["speakers_expected"], 2)

    def test_user_profile_dir_wins_and_bundled_example_is_the_fallback(self):
        user_dir = self.root / "profiles"
        user_dir.mkdir()
        (user_dir / "home-game.yaml").write_text("speakers_expected: 3\n")
        with patch.dict("os.environ", {"SKALDKEEP_TRANSCRIBE_CAMPAIGNS": str(user_dir)}):
            self.assertEqual(transcribe.load_campaign("home-game")["speakers_expected"], 3)
            self.assertEqual(transcribe.load_campaign("example")["name"], "Example Campaign")
            with self.assertRaisesRegex(ValueError, "not found"):
                transcribe.load_campaign("missing")

    def test_unsafe_profile_names_are_rejected(self):
        with self.assertRaises(ValueError):
            transcribe.load_campaign("../secrets")

    def test_default_output_is_outside_the_skill(self):
        with patch.dict("os.environ", {"SKALDKEEP_TRANSCRIBE_OUTPUT": "", "XDG_DATA_HOME": str(self.root)}):
            self.assertEqual(transcribe.default_output_dir(), self.root / "skaldkeep" / "transcribe")
        self.assertNotIn(str(transcribe.SCRIPT_DIR), str(transcribe.default_output_dir()))


class DurableJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)
        self.config = transcribe.build_config(CAMPAIGN)
        self.directory = self.output / "jobs" / jobs.cache_key("audio", self.config)
        self.client = Mock()

    def tearDown(self):
        self.temp.cleanup()

    def run_job(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return jobs.run_job("https://example.invalid/audio", "audio", self.config,
                                self.output, client=self.client, **kwargs)

    def test_submit_id_saved_before_poll_and_empty_result_is_reusable(self):
        self.client.post.return_value = response({"id": ID})

        def get(*args, **kwargs):
            self.assertEqual(jobs.read_json(self.directory / "state.json")["transcript_id"], ID)
            return response({"id": ID, "status": "completed", "text": "", "utterances": []})

        self.client.get.side_effect = get
        self.run_job()
        self.run_job()
        self.assertEqual(self.client.post.call_count, 1)
        self.assertEqual(self.client.get.call_count, 1)
        self.assertEqual((self.directory / "result.json").stat().st_mode & 0o777, 0o600)

    def test_submit_timeout_is_not_retried_even_after_restart(self):
        import requests
        self.client.post.side_effect = requests.Timeout("private URL")
        with self.assertRaises(RuntimeError):
            self.run_job()
        with self.assertRaisesRegex(RuntimeError, "uncertain"):
            self.run_job()
        self.assertEqual(self.client.post.call_count, 1)

    def test_success_status_with_missing_id_is_uncertain(self):
        self.client.post.return_value = response({})
        with self.assertRaises(RuntimeError):
            self.run_job()
        with self.assertRaisesRegex(RuntimeError, "uncertain"):
            self.run_job()
        self.assertEqual(self.client.post.call_count, 1)

    def test_crash_after_id_is_resumed_without_submission(self):
        jobs.save_json(self.directory / "state.json", {
            "state": "processing", "config": self.config, "source_id": "audio", "transcript_id": ID,
        })
        self.client.get.return_value = response({"id": ID, "status": "completed", "text": "Words"})
        self.run_job()
        self.client.post.assert_not_called()

    def test_server_error_does_not_trigger_second_post(self):
        self.client.post.return_value = response({"error": "Server failed"}, 500)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                self.run_job()
        self.assertEqual(self.client.post.call_count, 1)

    def test_poll_deadline_preserves_job_for_next_run(self):
        self.client.post.return_value = response({"id": ID})
        with self.assertRaisesRegex(RuntimeError, "deadline"):
            self.run_job(poll_timeout=0)
        self.client.get.return_value = response({"id": ID, "status": "completed"})
        self.run_job()
        self.assertEqual(self.client.post.call_count, 1)

    def test_rejected_job_does_not_spend_again(self):
        self.client.post.return_value = response({"error": "Bad config"}, 400)
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                self.run_job()
        self.assertEqual(self.client.post.call_count, 1)

    def test_rate_limit_and_auth_failures_allow_the_same_command_again(self):
        for status in (429, 401, 403):
            with self.subTest(status=status):
                self.client.reset_mock()
                self.client.post.side_effect = [response({"error": "Later"}, status), response({"id": ID})]
                self.client.get.return_value = response({"id": ID, "status": "completed"})
                with self.assertRaisesRegex(RuntimeError, f"HTTP {status}; state=new"):
                    self.run_job()
                result, _ = self.run_job()
                self.assertEqual(result["id"], ID)
                self.assertEqual(self.client.post.call_count, 2)
                (self.directory / "state.json").unlink()
                (self.directory / "result.json").unlink()

    def test_submit_status_is_reported_not_masked(self):
        self.client.post.return_value = response({"error": "Bad config"}, 422)
        with self.assertRaisesRegex(RuntimeError, "HTTP 422; state=rejected"):
            self.run_job()

    def local_source(self, data=b"recording"):
        source = self.output / "session.mp3"
        source.write_bytes(data)
        return str(source), jobs.fingerprint(source)

    def test_rejected_local_job_discards_cached_upload(self):
        source, source_id = self.local_source()
        self.client.post.side_effect = [response({"upload_url": "https://cdn.invalid/1"}),
                                        response({"error": "Bad audio"}, 400)]
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            jobs.run_job(source, source_id, self.config, self.output, client=self.client)
        self.assertFalse((self.output / "uploads" / f"{source_id}.json").exists())

    def test_upload_of_changed_source_is_not_cached(self):
        source, source_id = self.local_source()
        Path(source).write_bytes(b"replaced while queued")
        self.client.post.return_value = response({"upload_url": "https://cdn.invalid/1"})
        with self.assertRaisesRegex(RuntimeError, "changed during upload"):
            jobs.uploaded_url(source, source_id, self.output, self.client)
        self.assertFalse((self.output / "uploads" / f"{source_id}.json").exists())

    def test_timestamped_output_retains_source_offset_and_legacy_format(self):
        jobs.write_outputs({"utterances": [{"speaker": "A", "text": "A clue", "start": 1230, "end": 2500}]},
                           self.output, offset_seconds=120)
        self.assertEqual((self.output / "transcript_utterances.txt").read_text(), "[Speaker:A] A clue")
        self.assertIn("00:02:01.230 - 00:02:02.500", (self.output / "transcript_timed.txt").read_text())

    def test_dry_run_and_cost_limit_never_submit(self):
        arguments = ["https://example.invalid/audio", "--url-version", "v1", "--source-duration", "300",
                     "--compare-methods", "--dry-run"]
        with patch.object(transcribe, "load_campaign", return_value=CAMPAIGN), \
                patch.object(transcribe, "run_job") as submit, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(transcribe.main(arguments), 0)
            with self.assertRaisesRegex(ValueError, "exceeds"):
                transcribe.main(arguments + ["--max-cost-usd", "0.001"])
            submit.assert_not_called()

    def test_identical_audio_at_different_offsets_preserves_both_timelines(self):
        source = self.output / 'source.mp4'
        source.touch()
        result = {'utterances': [{'speaker': 'A', 'text': 'A clue', 'start': 1230, 'end': 2500}]}
        arguments = [str(source), '--duration', '60', '--output-dir', str(self.output)]
        with patch.object(transcribe, 'load_campaign', return_value=CAMPAIGN), \
                patch.object(transcribe, 'fingerprint', return_value='identical-audio'), \
                patch.object(transcribe, 'run_job', return_value=(result, self.directory)), \
                patch('audio_tools.probe', return_value={'duration_seconds': 600}), \
                patch('audio_tools.prepare', return_value=(source, {})), \
                contextlib.redirect_stdout(io.StringIO()):
            transcribe.main(arguments + ['--start', '120'])
            transcribe.main(arguments + ['--start', '150'])
        texts = sorted(p.read_text() for p in self.directory.glob('views/*/transcript_timed.txt'))
        self.assertEqual(len(texts), 2)
        self.assertIn('00:02:01.230', texts[0])
        self.assertIn('00:02:31.230', texts[1])


if __name__ == "__main__":
    unittest.main()
