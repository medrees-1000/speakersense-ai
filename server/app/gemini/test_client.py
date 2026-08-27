"""Client factory tests. Run from server/: python -m unittest app.gemini.test_client"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.gemini.client import (
    AUDIO_SAMPLE_RATE,
    DEFAULT_MODEL,
    JPEG_QUALITY,
    MAX_FRAME_WIDTH,
    TARGET_FPS,
    audio_blob,
    build_live_config,
    get_client,
    video_blob,
)


class GetClientTests(unittest.TestCase):
    @patch("app.gemini.client._load_env", lambda: None)
    def test_missing_key_raises(self) -> None:
        env = {key: value for key, value in os.environ.items() if key != "GEMINI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_client()
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    @patch("app.gemini.client._load_env", lambda: None)
    def test_client_constructs_with_key(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-not-real"}):
            client = get_client()
        self.assertIsNotNone(client)


class LiveConfigTests(unittest.TestCase):
    def test_audio_modality(self) -> None:
        config = build_live_config()
        modalities = config.response_modalities or []
        names = [getattr(item, "name", str(item)) for item in modalities]
        self.assertTrue(any("AUDIO" in name.upper() for name in names))

    def test_default_model_is_current_live(self) -> None:
        self.assertEqual(DEFAULT_MODEL, "gemini-3.1-flash-live-preview")

    def test_coaching_tools_present(self) -> None:
        config = build_live_config()
        self.assertTrue(config.tools)
        names = [
            decl.name
            for tool in config.tools
            for decl in (tool.function_declarations or [])
        ]
        self.assertIn("emit_live", names)
        self.assertIn("emit_summary", names)

    def test_system_instruction_present(self) -> None:
        config = build_live_config()
        self.assertIsNotNone(config.system_instruction)

    def test_blob_helpers(self) -> None:
        pcm = b"\x00\x00"
        jpeg = b"\xff\xd8"
        audio = audio_blob(pcm)
        video = video_blob(jpeg)
        self.assertEqual(audio.data, pcm)
        self.assertIn("16000", audio.mime_type or "")
        self.assertEqual(video.data, jpeg)
        self.assertEqual(video.mime_type, "image/jpeg")

    def test_token_knobs(self) -> None:
        self.assertEqual(TARGET_FPS, 1)
        self.assertEqual(MAX_FRAME_WIDTH, 640)
        self.assertGreaterEqual(JPEG_QUALITY, 50)
        self.assertLessEqual(JPEG_QUALITY, 60)
        self.assertEqual(AUDIO_SAMPLE_RATE, 16_000)


if __name__ == "__main__":
    unittest.main()
