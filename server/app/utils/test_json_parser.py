"""Unit tests for JsonStreamParser. Run from server/: python -m unittest app.utils.test_json_parser"""

from __future__ import annotations

import unittest

from app.gemini.prompts import LiveTick, SessionSummary
from app.utils.json_parser import JsonStreamParser

LIVE = (
    '{"type":"live","posture":"good","eye_contact":"engaged",'
    '"wpm":142,"filler_count":4,"tip":"Lift your chin toward the camera."}'
)
SUMMARY = (
    '{"type":"summary","overall_score":78,"posture_score":80,'
    '"eye_contact_score":72,"pace_score":85,"filler_score":64,'
    '"avg_wpm":145,"total_fillers":12,"strengths":["Steady pace"],'
    '"improvements":["Watch filler like"]}'
)


class JsonStreamParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = JsonStreamParser()

    def test_plain_live_object(self) -> None:
        events = self.parser.feed(LIVE)
        self.assertEqual(len(events), 1)
        tick = events[0]
        self.assertIsInstance(tick, LiveTick)
        self.assertEqual(tick.posture.value, "good")
        self.assertEqual(tick.wpm, 142)
        self.assertEqual(tick.filler_count, 4)

    def test_strips_markdown_fences(self) -> None:
        fenced = f"```json\n{LIVE}\n```"
        events = self.parser.feed(fenced)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_partial_chunks(self) -> None:
        mid = len(LIVE) // 2
        self.assertEqual(self.parser.feed(LIVE[:mid]), [])
        events = self.parser.feed(LIVE[mid:])
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_two_objects_in_one_chunk(self) -> None:
        events = self.parser.feed(LIVE + SUMMARY)
        self.assertEqual(len(events), 2)
        self.assertIsInstance(events[0], LiveTick)
        self.assertIsInstance(events[1], SessionSummary)
        self.assertEqual(events[1].overall_score, 78)

    def test_garbage_then_json(self) -> None:
        events = self.parser.feed("Sure, here you go:\n" + LIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_invalid_object_is_dropped(self) -> None:
        bad = '{"type":"live","posture":"upright","eye_contact":"engaged","wpm":10,"filler_count":0}'
        events = self.parser.feed(bad + LIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_unknown_type_dropped(self) -> None:
        events = self.parser.feed('{"type":"chat","text":"hello"}' + LIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_empty_and_none_chunks(self) -> None:
        self.assertEqual(self.parser.feed(""), [])
        self.assertEqual(self.parser.feed(None), [])

    def test_tip_truncated_to_twelve_words(self) -> None:
        long_tip = " ".join(["word"] * 20)
        raw = (
            '{"type":"live","posture":"slouching","eye_contact":"looking_away",'
            f'"wpm":90,"filler_count":2,"tip":"{long_tip}"}}'
        )
        events = self.parser.feed(raw)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].tip.split()), 12)

    def test_reset_clears_partial(self) -> None:
        self.parser.feed(LIVE[:10])
        self.parser.reset()
        events = self.parser.feed(LIVE)
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
