import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_tools import measure, prepare, probe
from jobs import fingerprint, save_json


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "quiet.wav"
        with wave.open(str(self.source), "wb") as stream:
            stream.setparams((2, 2, 16000, 0, "NONE", "not compressed"))
            frames = [struct.pack("<hh", round(80 * math.sin(i * 0.2)), round(70 * math.sin(i * 0.3)))
                      for i in range(32000)]
            stream.writeframes(b"".join(frames))

    def tearDown(self):
        self.temp.cleanup()

    def test_gain_preserves_original_channels_rate_and_excerpt_length(self):
        original_hash = fingerprint(self.source)
        source_levels = measure(self.source, 0.5, 1)
        target, saved = prepare(self.source, self.root, start=0.5, duration=1, gain_db=12)
        result = probe(target)
        self.assertEqual(result["channels"], 2)
        self.assertEqual(result["sample_rate"], 16000)
        self.assertAlmostEqual(result["duration_seconds"], 1, places=2)
        self.assertAlmostEqual(saved["derived_levels"]["mean_volume_dbfs"] - source_levels["mean_volume_dbfs"],
                               12, delta=0.2)
        self.assertEqual(fingerprint(self.source), original_hash)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        replay, _ = prepare(self.source, self.root, start=0.5, duration=1, gain_db=12)
        self.assertEqual(target, replay)

    def test_different_gain_creates_different_audio_identity(self):
        first, _ = prepare(self.source, self.root, duration=1, gain_db=0)
        second, _ = prepare(self.source, self.root, duration=1, gain_db=6)
        self.assertNotEqual(fingerprint(first), fingerprint(second))

    def test_invalid_excerpt_and_gain_are_rejected(self):
        for kwargs in ({"start": 3}, {"duration": 3}, {"gain_db": 60}, {"gain_db": float("nan")}):
            with self.assertRaises(ValueError):
                prepare(self.source, self.root, **kwargs)

    def test_normalization_raises_quiet_audio_and_preserves_format(self):
        target, saved = prepare(self.source, self.root, normalize=True)
        self.assertEqual(probe(target)["sample_rate"], 16000)
        self.assertEqual(probe(target)["channels"], 2)
        self.assertLessEqual(saved["derived_levels"]["max_volume_dbfs"], -1)
        self.assertGreater(saved["derived_levels"]["mean_volume_dbfs"], -25)
        self.assertIsNotNone(saved["normalization_measurements"])
        with self.assertRaises(ValueError):
            prepare(self.source, self.root, normalize=True, gain_db=3)

    def test_cached_normalization_cannot_bypass_peak_check(self):
        target, saved = prepare(self.source, self.root, normalize=True)
        saved["derived_levels"]["max_volume_dbfs"] = 0
        save_json(target.with_suffix('.json'), saved)
        with self.assertRaisesRegex(ValueError, "peak-headroom"):
            prepare(self.source, self.root, normalize=True)


if __name__ == "__main__":
    unittest.main()
