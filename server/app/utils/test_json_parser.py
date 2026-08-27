"""Unit tests for JsonStreamParser. Run from server/: python -m unittest app.utils.test_json_parser"""

from __future__ import annotations

import unittest

from app.gemini.prompts import LiveTick, SessionSummary
from app.utils.json_parser import JsonStreamParser, parse_tool_call

LIVE = (
    '{"type":"live","posture":"slouching","severity":2,"body_region":"spine",'
    '"alert":true,"spoken_cue":"Sit up — shoulders back.",'
    '"tip":"Unround your upper back."}'
)
SUMMARY = (
    '{"type":"summary","overall_score":72,"posture_score":68,'
    '"alignment_score":74,"time_good_pct":61,"slouch_events":7,'
    '"worst_habit":"forward_head","strengths":["Kept hips square"],'
    '"improvements":["Round upper back when focusing"],'
    '"exercises":[{"name":"Chin tucks","reps":"10 x 5s","why":"Counters forward head"}]}'
)


class JsonStreamParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = JsonStreamParser()

    def test_plain_live_object(self) -> None:
        events = self.parser.feed(LIVE)
        self.assertEqual(len(events), 1)
        tick = events[0]
        self.assertIsInstance(tick, LiveTick)
        self.assertEqual(tick.posture.value, "slouching")
        self.assertEqual(tick.severity, 2)
        self.assertTrue(tick.alert)
        self.assertIn("Sit up", tick.spoken_cue)

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
        self.assertEqual(events[1].overall_score, 72)
        self.assertEqual(len(events[1].exercises), 1)

    def test_garbage_then_json(self) -> None:
        events = self.parser.feed("Sure, here you go:\n" + LIVE)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], LiveTick)

    def test_invalid_object_is_dropped(self) -> None:
        bad = (
            '{"type":"live","posture":"upright","severity":2,'
            '"body_region":"spine","alert":false}'
        )
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
            '{"type":"live","posture":"slouching","severity":2,'
            f'"body_region":"spine","alert":true,"spoken_cue":"Sit up.",'
            f'"tip":"{long_tip}"}}'
        )
        events = self.parser.feed(raw)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].tip.split()), 12)

    def test_spoken_cue_truncated_to_ten_words(self) -> None:
        long_cue = " ".join(["fix"] * 15)
        raw = (
            '{"type":"live","posture":"leaning","severity":3,'
            f'"body_region":"hips","alert":true,"spoken_cue":"{long_cue}",'
            '"tip":""}'
        )
        events = self.parser.feed(raw)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].spoken_cue.split()), 10)

    def test_reset_clears_partial(self) -> None:
        self.parser.feed(LIVE[:10])
        self.parser.reset()
        events = self.parser.feed(LIVE)
        self.assertEqual(len(events), 1)

    def test_parse_tool_call_live(self) -> None:
        event = parse_tool_call(
            "emit_live",
            {
                "posture": "good",
                "severity": 0,
                "body_region": "overall",
                "alert": False,
                "spoken_cue": "",
                "tip": "Nice tall spine.",
            },
        )
        self.assertIsInstance(event, LiveTick)
        self.assertEqual(event.severity, 0)
        self.assertFalse(event.alert)

    def test_parse_tool_call_summary(self) -> None:
        event = parse_tool_call(
            "emit_summary",
            {
                "overall_score": 80,
                "posture_score": 78,
                "alignment_score": 82,
                "time_good_pct": 70,
                "slouch_events": 3,
                "worst_habit": "slouching",
                "strengths": ["Steady shoulders"],
                "improvements": ["Watch mid-session slump"],
                "exercises": [
                    {
                        "name": "Wall angels",
                        "reps": "2 x 8",
                        "why": "Opens shoulders",
                    }
                ],
            },
        )
        self.assertIsInstance(event, SessionSummary)
        self.assertEqual(event.overall_score, 80)
        self.assertEqual(event.exercises[0].name, "Wall angels")

    def test_parse_tool_call_unknown(self) -> None:
        self.assertIsNone(parse_tool_call("chat", {"text": "hi"}))
        self.assertIsNone(parse_tool_call("emit_live", None))


if __name__ == "__main__":
    unittest.main()
